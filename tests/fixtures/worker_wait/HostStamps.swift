import Darwin
import Foundation

// Test-only host timeline recorder for the worker-wait pilot. Only disposable
// hosts built by host_stamps.py compile it; that builder prepends the literal
// PWW_STAMP_DIR, PWW_STAMP_SWIFT_FLAGS and PWW_STAMP_INSPECTION declarations.
//
// Every stamp is mach_continuous_time(), the worker's tick domain. All storage
// is allocated and written once when the service starts, so the record path
// neither allocates nor faults a fresh page. Records come from the request
// thread only; the export runs once, immediately before the reply is sent,
// because launchd removes the service as soon as the client disconnects and
// the delayed exit closure may never run. The closure's flush is then a no-op.
// After the stamps file is renamed into place, a <stem>.exported marker gives
// the export's span: from event 171's raw to a read after that rename.
//
// Phase field by event: request-scoped events (100, 160, 161, 171) carry
// UInt32.max; session-scoped events (101-103, 144-148, 157, 170) carry the
// actor index (0 in the ordinary form); validator events (122-136) carry the
// phase of the latest PLANNING_START; sleep and wait events (180-182) carry the
// wait key; the rest carry the global phase index. Register keys use the same
// phase, except 156, which is keyed by delivery index.
//
// The worker exit grace is bracketed by program points 148 (WORKER_GRACE_BEGIN)
// and 157 (WORKER_GRACE_FINISHED), aux 0 exhausted, 1 reaped, 2 wait_error.
// A bounded exit wait records its pair like a sleep and then 182
// (WAIT_OUTCOME): phase = key, aux 0 timed out, 1 notified, 2 unusable, raw =
// the pair's post read.

struct HostStamp {
    var event: UInt32
    var phase: UInt32
    var aux: UInt64
    var raw: UInt64
}

final class HostStamps {
    static let shared = HostStamps()

    static let eventCapacity = 4096
    static let registerEvents: [UInt32] = [103, 110, 142, 143, 144, 156]
    static let registerPhases = 64
    static let registerWords = 3      // last_negative, first_positive, negatives
    static let sleepKeys = 8          // 0 unkeyed, 1...7 as the contract numbers them
    static let sleepWords = 8         // count, last_pre, last_post, last_requested_ns, sum, max, min, requested_sum_ns
    static let custodyPhases = 64
    static let custodyWords = 6       // passes, sum, max, last_start, last_end, work_passes
    static let pageActors = 8         // PWActorLimits.actors
    static let pageWords = 6          // copied, pid, event_count_read, reaped, capture_requested, copied_raw
    // The worker stamp page as tests/fixtures/worker_wait/pww_stamp_page.h lays it out.
    static let pageOffset = 3_293_184
    static let pageBytes = 32_768
    static let pageEventCountOffset = 32
    static let stampCostRecords = 16

    let numer: UInt32
    let denom: UInt32
    let pageWithinCapture: Bool
    private(set) var currentPhase = UInt32.max

    private let events = UnsafeMutablePointer<HostStamp>.allocate(capacity: HostStamps.eventCapacity)
    private var eventCount = 0
    private let registers = UnsafeMutablePointer<UInt64>.allocate(
        capacity: HostStamps.registerEvents.count * HostStamps.registerPhases * HostStamps.registerWords)
    private let sleeps = UnsafeMutablePointer<UInt64>.allocate(capacity: HostStamps.sleepKeys * HostStamps.sleepWords)
    private let custody = UnsafeMutablePointer<UInt64>.allocate(capacity: HostStamps.custodyPhases * HostStamps.custodyWords)
    private let pages = UnsafeMutableRawPointer.allocate(byteCount: HostStamps.pageActors * HostStamps.pageBytes, alignment: 16)
    private let pageMeta = UnsafeMutablePointer<UInt64>.allocate(capacity: HostStamps.pageActors * HostStamps.pageWords)
    private let costRaws = UnsafeMutablePointer<UInt64>.allocate(capacity: HostStamps.stampCostRecords)
    private var costCount = 0
    private var droppedEvents: UInt64 = 0
    private var droppedRegisterSamples: UInt64 = 0
    private var droppedSleeps: UInt64 = 0
    private var droppedCustodyPasses: UInt64 = 0
    private var droppedPages: UInt64 = 0

    private var specimenID: String? = nil
    private var requestStartRaw: UInt64 = 0
    private var requestPair: (UInt64, UInt64?, UInt64)? = nil
    private var startedStatus = "not_attempted"
    private var startedErrno: Int32? = nil
    private var startedBeginRaw: UInt64 = 0
    private var startedEndRaw: UInt64 = 0
    private let lock = UnsafeMutablePointer<os_unfair_lock>.allocate(capacity: 1)
    private var flushed = false

    init() {
        var info = mach_timebase_info_data_t()
        mach_timebase_info(&info)
        numer = info.numer
        denom = info.denom
        let captureStart = PWShmLayout.captureOffset + PWShmLayout.captureHeaderBytes
        pageWithinCapture = HostStamps.pageOffset >= captureStart
            && HostStamps.pageOffset + HostStamps.pageBytes <= captureStart + PWShmLayout.captureBytes
        events.initialize(repeating: HostStamp(event: 0, phase: 0, aux: 0, raw: 0), count: HostStamps.eventCapacity)
        registers.initialize(repeating: 0, count: HostStamps.registerEvents.count * HostStamps.registerPhases * HostStamps.registerWords)
        sleeps.initialize(repeating: 0, count: HostStamps.sleepKeys * HostStamps.sleepWords)
        custody.initialize(repeating: 0, count: HostStamps.custodyPhases * HostStamps.custodyWords)
        pages.initializeMemory(as: UInt8.self, repeating: 0, count: HostStamps.pageActors * HostStamps.pageBytes)
        pageMeta.initialize(repeating: 0, count: HostStamps.pageActors * HostStamps.pageWords)
        costRaws.initialize(repeating: 0, count: HostStamps.stampCostRecords)
        lock.initialize(to: os_unfair_lock())
    }

    // MARK: - Record path (no allocation)

    private func append(_ event: UInt32, _ phase: UInt32, _ aux: UInt64, _ raw: UInt64) {
        if eventCount < HostStamps.eventCapacity {
            events[eventCount] = HostStamp(event: event, phase: phase, aux: aux, raw: raw)
            eventCount += 1
        } else {
            droppedEvents += 1
        }
    }

    func record(_ event: UInt32, _ phase: UInt32, _ aux: UInt64 = 0) {
        append(event, phase, aux, mach_continuous_time())
    }

    /// A stamp whose clock value the caller already read.
    func record(_ event: UInt32, _ phase: UInt32, _ aux: UInt64, raw: UInt64) {
        append(event, phase, aux, raw)
    }

    /// Validator-path events carry the phase of the latest planning start.
    func phaseEvent(_ event: UInt32, _ aux: UInt64 = 0) {
        append(event, currentPhase, aux, mach_continuous_time())
    }

    func planningStart(_ phase: Int) {
        let raw = mach_continuous_time()
        currentPhase = UInt32(truncatingIfNeeded: phase)
        append(120, currentPhase, 0, raw)
    }

    private static func registerSlot(_ event: UInt32) -> Int {
        switch event {
        case 103: return 0
        case 110: return 1
        case 142: return 2
        case 143: return 3
        case 144: return 4
        case 156: return 5
        default: return -1
        }
    }

    /// One sample of a polled publication. A false sample overwrites
    /// last_negative; the first true sample sets first_positive and, unless
    /// `append` is false, appends the event with aux = preceding false samples.
    /// Later true samples read no clock.
    @discardableResult
    func sample(_ event: UInt32, _ phase: UInt32, _ value: Bool, append appendEvent: Bool = true) -> Bool {
        let slot = HostStamps.registerSlot(event)
        guard slot >= 0, phase < UInt32(HostStamps.registerPhases) else {
            droppedRegisterSamples += 1
            return value
        }
        let r = registers + (slot * HostStamps.registerPhases + Int(phase)) * HostStamps.registerWords
        if value {
            if r[1] == 0 {
                let raw = mach_continuous_time()
                r[1] = raw
                if appendEvent { append(event, phase, r[2], raw) }
            }
        } else {
            r[0] = mach_continuous_time()
            r[2] += 1
        }
        return value
    }

    /// Called after a host sleep returns; `pre` was read just before it.
    /// The first 64 sleeps of each key are also appended as event pairs 180/181
    /// (phase = key, aux = requested ns), so a worker publication can be placed
    /// in the exact host sleep that contained it; later sleeps update only the registers.
    static let sleepEventsPerKey: UInt64 = 64

    func sleep(_ key: UInt32, pre: UInt64, requestedNs: UInt64) {
        let post = mach_continuous_time()
        guard key < UInt32(HostStamps.sleepKeys) else { droppedSleeps += 1; return }
        let s = sleeps + Int(key) * HostStamps.sleepWords
        let ticks = post >= pre ? post - pre : 0
        s[0] += 1
        if s[0] <= HostStamps.sleepEventsPerKey {
            append(180, key, requestedNs, pre)
            append(181, key, requestedNs, post)
        }
        s[1] = pre
        s[2] = post
        s[3] = requestedNs
        s[4] &+= ticks
        if ticks > s[5] { s[5] = ticks }
        if s[0] == 1 || ticks < s[6] { s[6] = ticks }
        s[7] &+= requestedNs
    }

    /// Called after a bounded exit wait returns: records the pair exactly as
    /// sleep(...) does, then, while that key's pairs are still appended, event
    /// 182 with the outcome (0 timed out, 1 notified, 2 unusable) and the
    /// pair's post read. Past 64 waits of a key only the registers change.
    func wait(_ key: UInt32, pre: UInt64, requestedNs: UInt64, outcome: UInt64) {
        sleep(key, pre: pre, requestedNs: requestedNs)
        guard key < UInt32(HostStamps.sleepKeys) else { return }
        let s = sleeps + Int(key) * HostStamps.sleepWords
        if s[0] <= HostStamps.sleepEventsPerKey { append(182, key, outcome, s[2]) }
    }

    /// One custody service pass in the actor completion loop. Passes are kept
    /// as registers; a pass that changed the custody or transfer record count
    /// also appends 153/154 with those counts, which bounds the events by the
    /// admitted tokens and deliveries. `start` 0 means no custody exists.
    func custodyPass(_ phase: UInt32, start: UInt64, workBefore: Int, workAfter: Int) {
        guard start != 0 else { return }
        let end = mach_continuous_time()
        let worked = workAfter != workBefore
        if worked {
            append(153, phase, UInt64(max(0, workBefore)), start)
            append(154, phase, UInt64(max(0, workAfter)), end)
        }
        guard phase < UInt32(HostStamps.custodyPhases) else { droppedCustodyPasses += 1; return }
        let c = custody + Int(phase) * HostStamps.custodyWords
        let ticks = end >= start ? end - start : 0
        c[0] += 1
        c[1] &+= ticks
        if ticks > c[2] { c[2] = ticks }
        c[3] = start
        c[4] = end
        if worked { c[5] += 1 }
    }

    /// Copy one worker's stamp page out of the session mapping before unmap.
    /// The event count is read with acquire ordering before the bytes.
    func copyWorkerPage(_ base: UnsafeMutablePointer<UInt8>, actor: UInt32, pid: pid_t, reaped: Bool, captureRequested: Bool) {
        guard actor < UInt32(HostStamps.pageActors), pageWithinCapture else { droppedPages += 1; return }
        let page = base.advanced(by: HostStamps.pageOffset)
        let count = loadAcquire(page, offset: HostStamps.pageEventCountOffset)
        memcpy(pages + Int(actor) * HostStamps.pageBytes, page, HostStamps.pageBytes)
        let raw = mach_continuous_time()
        let m = pageMeta + Int(actor) * HostStamps.pageWords
        m[0] = 1
        m[1] = UInt64(UInt32(bitPattern: pid))
        m[2] = UInt64(count)
        m[3] = reaped ? 1 : 0
        m[4] = captureRequested ? 1 : 0
        m[5] = raw
        append(170, actor, UInt64(count), raw)
    }

    // MARK: - Request boundaries (pre-spawn) and export (post-reply)

    func requestStart() {
        requestStartRaw = mach_continuous_time()
        append(100, UInt32.max, 0, requestStartRaw)
        requestPair = HostStamps.clockPair()
        stampCostBurst()
    }

    /// Sixteen consecutive records through the call sites' own expression,
    /// then withdrawn from the timeline: adjacent raws give this build's
    /// per-record cost. Unrolled so that no loop step lies between them.
    private func stampCostBurst() {
        let before = eventCount
        guard before + HostStamps.stampCostRecords <= HostStamps.eventCapacity else { return }
        HostStamps.shared.record(0, UInt32.max, 0)
        HostStamps.shared.record(0, UInt32.max, 0)
        HostStamps.shared.record(0, UInt32.max, 0)
        HostStamps.shared.record(0, UInt32.max, 0)
        HostStamps.shared.record(0, UInt32.max, 0)
        HostStamps.shared.record(0, UInt32.max, 0)
        HostStamps.shared.record(0, UInt32.max, 0)
        HostStamps.shared.record(0, UInt32.max, 0)
        HostStamps.shared.record(0, UInt32.max, 0)
        HostStamps.shared.record(0, UInt32.max, 0)
        HostStamps.shared.record(0, UInt32.max, 0)
        HostStamps.shared.record(0, UInt32.max, 0)
        HostStamps.shared.record(0, UInt32.max, 0)
        HostStamps.shared.record(0, UInt32.max, 0)
        HostStamps.shared.record(0, UInt32.max, 0)
        HostStamps.shared.record(0, UInt32.max, 0)
        costCount = eventCount - before
        for i in 0..<costCount { costRaws[i] = events[before + i].raw }
        eventCount = before
    }

    /// Name the run and write the pre-spawn `.started` marker. The descriptor
    /// is close-on-exec and closed before this returns.
    func specimenStarted(_ id: String) {
        specimenID = id
        startedBeginRaw = mach_continuous_time()
        let text = "{\"host_pid\": \(getpid()), \"specimen_id\": \(HostStamps.jsonString(id)), \"raw\": \(requestStartRaw)}\n"
        let result = HostStamps.writeAtomically(HostStamps.fileStem(id) + ".started", Array(text.utf8))
        startedStatus = result.0
        startedErrno = result.1
        startedEndRaw = mach_continuous_time()
    }

    /// Runs immediately before the reply is sent; the scheduleExit closure calls
    /// it again, which writes nothing. Its cost lies inside the request latency.
    func flush() {
        os_unfair_lock_lock(lock)
        defer { os_unfair_lock_unlock(lock) }
        if flushed { return }
        flushed = true
        let beginRaw = mach_continuous_time()
        append(171, UInt32.max, 0, beginRaw)
        let flushPair = HostStamps.clockPair()
        guard let id = specimenID else { return }
        let bytes = Array(export(id, flushPair: flushPair).utf8)
        let stem = HostStamps.fileStem(id)
        guard HostStamps.writeAtomically(stem + ".stamps.json", bytes).0 == "written" else { return }
        let endRaw = mach_continuous_time()
        let marker = "{\"host_pid\":\(getpid()),\"begin_raw\":\(beginRaw),\"end_raw\":\(endRaw),\"bytes\":\(bytes.count)}\n"
        _ = HostStamps.writeAtomically(stem + ".exported", Array(marker.utf8))
    }

    private static func clockPair() -> (UInt64, UInt64?, UInt64) {
        let before = mach_continuous_time()
        let monotonic = MonotonicDeadline.now()
        let after = mach_continuous_time()
        return (before, monotonic, after)
    }

    /// Each UTF-8 byte outside [A-Za-z0-9._-] becomes "_", then the first 120 bytes.
    static func fileStem(_ id: String) -> String {
        var bytes: [UInt8] = []
        for byte in id.utf8.prefix(120) {
            let allowed = (byte >= 0x41 && byte <= 0x5a) || (byte >= 0x61 && byte <= 0x7a)
                || (byte >= 0x30 && byte <= 0x39) || byte == 0x2e || byte == 0x5f || byte == 0x2d
            bytes.append(allowed ? byte : 0x5f)
        }
        return String(decoding: bytes, as: UTF8.self)
    }

    private static func jsonString(_ value: String) -> String {
        var out = "\""
        for scalar in value.unicodeScalars {
            switch scalar {
            case "\"": out += "\\\""
            case "\\": out += "\\\\"
            default:
                if scalar.value < 0x20 { out += String(format: "\\u%04x", scalar.value) }
                else { out.unicodeScalars.append(scalar) }
            }
        }
        return out + "\""
    }

    /// Temporary file plus rename; nothing is written when the directory is absent.
    private static func writeAtomically(_ name: String, _ bytes: [UInt8]) -> (String, Int32?) {
        var info = stat()
        if stat(PWW_STAMP_DIR, &info) != 0 { return ("directory_missing", errno) }
        if (info.st_mode & S_IFMT) != S_IFDIR { return ("not_a_directory", nil) }
        let temp = PWW_STAMP_DIR + "/." + name + "." + String(getpid()) + ".tmp"
        let final = PWW_STAMP_DIR + "/" + name
        let fd = open(temp, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW, 0o644)
        if fd < 0 { return ("open_failed", errno) }
        var failure: Int32? = nil
        bytes.withUnsafeBytes { raw in
            var offset = 0
            while offset < raw.count {
                let n = Darwin.write(fd, raw.baseAddress! + offset, raw.count - offset)
                if n > 0 { offset += n; continue }
                if n < 0 && errno == EINTR { continue }
                failure = n < 0 ? errno : EIO
                break
            }
        }
        if close(fd) != 0 && failure == nil { failure = errno }
        if let failure { unlink(temp); return ("write_failed", failure) }
        if rename(temp, final) != 0 { let error = errno; unlink(temp); return ("rename_failed", error) }
        return ("written", nil)
    }

    private func nanoseconds(_ ticks: UInt64) -> UInt64 {
        let (high, low) = ticks.multipliedFullWidth(by: UInt64(numer))
        guard denom != 0, high < UInt64(denom) else { return UInt64.max }
        return UInt64(denom).dividingFullWidth((high, low)).quotient
    }

    private static func optional(_ value: UInt64) -> String { value == 0 ? "null" : String(value) }

    private static func pairJSON(_ stage: String, _ pair: (UInt64, UInt64?, UInt64)?) -> String {
        guard let pair else { return "{\"stage\":\"\(stage)\",\"observed\":false}" }
        return "{\"stage\":\"\(stage)\",\"observed\":true,\"continuous_before\":\(pair.0),\"monotonic_ns\":"
            + (pair.1.map { String($0) } ?? "null") + ",\"continuous_after\":\(pair.2)}"
    }

    private func export(_ id: String, flushPair: (UInt64, UInt64?, UInt64)) -> String {
        var s = String()
        s.reserveCapacity(1 << 20)
        s += "{\"version\":2,\"host_pid\":\(getpid()),\"specimen_id\":\(HostStamps.jsonString(id))"
        s += ",\"file_stem\":\(HostStamps.jsonString(HostStamps.fileStem(id)))"
        s += ",\"stamp_dir\":\(HostStamps.jsonString(PWW_STAMP_DIR))"
        s += ",\"timebase\":{\"numer\":\(numer),\"denom\":\(denom)}"
        s += ",\"resampling_measured\":\(PWW_STAMP_RESAMPLING)"
        s += ",\"flavour\":{\"swift\":\(HostStamps.jsonString(PWW_STAMP_SWIFT_FLAGS)),\"inspection\":\(PWW_STAMP_INSPECTION)}"
        s += ",\"capacity\":{\"events\":\(HostStamps.eventCapacity),\"register_phases\":\(HostStamps.registerPhases)"
        s += ",\"custody_phases\":\(HostStamps.custodyPhases),\"page_actors\":\(HostStamps.pageActors)}"
        s += ",\"dropped\":{\"events\":\(droppedEvents),\"register_samples\":\(droppedRegisterSamples)"
        s += ",\"sleeps\":\(droppedSleeps),\"custody_passes\":\(droppedCustodyPasses),\"worker_pages\":\(droppedPages)}"
        s += ",\"page_within_capture\":\(pageWithinCapture)"
        s += ",\"started_marker\":{\"status\":\"\(startedStatus)\",\"errno\":" + (startedErrno.map { String($0) } ?? "null")
        s += ",\"begin_raw\":\(HostStamps.optional(startedBeginRaw)),\"end_raw\":\(HostStamps.optional(startedEndRaw))}"
        s += ",\"clock_pairs\":[" + HostStamps.pairJSON("request_start", requestPair) + "," + HostStamps.pairJSON("flush", flushPair) + "]"
        s += ",\"stamp_cost\":{\"raws\":["
        for i in 0..<costCount { s += (i > 0 ? "," : "") + String(costRaws[i]) }
        s += "]}"
        s += ",\"events\":["
        for i in 0..<eventCount {
            let e = events[i]
            if i > 0 { s += "," }
            s += "[\(e.event),\(e.phase),\(e.aux),\(e.raw)]"
        }
        s += "],\"registers\":{"
        var first = true
        for (slot, event) in HostStamps.registerEvents.enumerated() {
            for phase in 0..<HostStamps.registerPhases {
                let r = registers + (slot * HostStamps.registerPhases + phase) * HostStamps.registerWords
                if r[1] == 0 && r[2] == 0 { continue }
                if !first { s += "," }
                first = false
                s += "\"\(event):\(phase)\":{\"last_negative\":\(HostStamps.optional(r[0])),\"first_positive\":\(HostStamps.optional(r[1])),\"negatives\":\(r[2])}"
            }
        }
        s += "},\"sleeps\":{"
        for key in 0..<HostStamps.sleepKeys {
            let w = sleeps + key * HostStamps.sleepWords
            if key > 0 { s += "," }
            let observed = w[0] > 0
            s += "\"\(key)\":{\"count\":\(w[0]),\"last_pre\":\(observed ? String(w[1]) : "null"),\"last_post\":\(observed ? String(w[2]) : "null")"
            s += ",\"last_requested_ns\":\(observed ? String(w[3]) : "null"),\"requested_sum_ns\":\(w[7])"
            s += ",\"sum_ticks\":\(w[4]),\"max_ticks\":\(observed ? String(w[5]) : "null"),\"min_ticks\":\(observed ? String(w[6]) : "null")"
            s += ",\"sum_ns\":\(nanoseconds(w[4])),\"max_ns\":\(observed ? String(nanoseconds(w[5])) : "null")}"
        }
        s += "},\"custody_passes\":{"
        first = true
        for phase in 0..<HostStamps.custodyPhases {
            let c = custody + phase * HostStamps.custodyWords
            if c[0] == 0 { continue }
            if !first { s += "," }
            first = false
            s += "\"\(phase)\":{\"passes\":\(c[0]),\"sum_ticks\":\(c[1]),\"max_ticks\":\(c[2]),\"last_start\":\(c[3]),\"last_end\":\(c[4]),\"work_passes\":\(c[5])}"
        }
        s += "},\"worker_pages\":["
        first = true
        for actor in 0..<HostStamps.pageActors {
            let m = pageMeta + actor * HostStamps.pageWords
            if m[0] == 0 { continue }
            if !first { s += "," }
            first = false
            let bytes = Data(bytes: pages + actor * HostStamps.pageBytes, count: HostStamps.pageBytes)
            s += "{\"actor\":\(actor),\"pid\":\(m[1]),\"event_count_read\":\(m[2]),\"reaped\":\(m[3] == 1)"
            s += ",\"capture_requested\":\(m[4] == 1),\"copied_raw\":\(m[5]),\"base64\":\"" + bytes.base64EncodedString() + "\"}"
        }
        s += "]}\n"
        return s
    }
}
