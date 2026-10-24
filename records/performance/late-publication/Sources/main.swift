// One late-publication observation: the shipped C worker compiles and applies
// a real policy, is released at once, and performs one file open-read attempt
// whose target this process owns. On a FIFO the worker's open() and one-byte
// read() block until this process opens the write end, writes and closes; that
// release can be scheduled after the driver's phase release or after the host
// enters exit grace. On a regular file the attempt returns at once, and the
// worker's post-apply hang can delay `done` instead.
//
// The driver is unchanged. Its process calls are the production waitpid,
// kill and sleep functions wrapped only to timestamp each call; the clock is
// not wrapped. Every *_ns time is CLOCK_MONOTONIC_RAW in nanoseconds.

import Darwin
import Foundation
@testable import PWRunnerCore

@inline(__always) func mono() -> UInt64 { clock_gettime_nsec_np(CLOCK_MONOTONIC_RAW) }

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(2)
}

struct Options {
    var worker = ""
    var workDir = ""
    var out = ""
    var label = ""
    var target = "fifo"
    var sentinelMs = 400
    var graceMs = 1_000
    var hangMs = 0
    var unblockAfterReleaseMs: Int? = nil
    var unblockAfterGraceEntryMs: Int? = nil
    var sampleIntervalMs: UInt32 = 20
    var holdMs = 0
}

func parseOptions() -> Options {
    var options = Options()
    var args = Array(CommandLine.arguments.dropFirst())[...]
    while let flag = args.popFirst() {
        guard let value = args.popFirst() else { fail("missing value for \(flag)") }
        switch flag {
        case "--worker": options.worker = value
        case "--work-dir": options.workDir = value
        case "--out": options.out = value
        case "--label": options.label = value
        case "--target": options.target = value
        case "--sentinel-ms": options.sentinelMs = Int(value) ?? -1
        case "--grace-ms": options.graceMs = Int(value) ?? -1
        case "--hang-ms": options.hangMs = Int(value) ?? -1
        case "--unblock-after-release-ms": options.unblockAfterReleaseMs = Int(value)
        case "--unblock-after-grace-entry-ms": options.unblockAfterGraceEntryMs = Int(value)
        case "--sample-interval-ms": options.sampleIntervalMs = UInt32(value) ?? 0
        case "--hold-ms": options.holdMs = Int(value) ?? -1
        default: fail("unknown argument \(flag)")
        }
    }
    guard !options.worker.isEmpty, !options.workDir.isEmpty, !options.out.isEmpty, !options.label.isEmpty,
          ["fifo", "file"].contains(options.target), options.sentinelMs > 0, options.graceMs > 0,
          options.hangMs >= 0, options.sampleIntervalMs > 0, options.holdMs >= 0,
          options.target == "fifo" || (options.unblockAfterReleaseMs == nil && options.unblockAfterGraceEntryMs == nil),
          options.unblockAfterReleaseMs == nil || options.unblockAfterGraceEntryMs == nil else {
        fail("usage: --worker PATH --work-dir DIR --out PATH --label NAME [--target fifo|file] [--sentinel-ms N] "
             + "[--grace-ms N] [--hang-ms N] [--unblock-after-release-ms N | --unblock-after-grace-entry-ms N]")
    }
    return options
}

func clockReadings() -> [String: Any] {
    let wallBefore = clock_gettime_nsec_np(CLOCK_REALTIME)
    let absolute = mach_absolute_time()
    let continuous = mach_continuous_time()
    let monotonic = mono()
    let wallAfter = clock_gettime_nsec_np(CLOCK_REALTIME)
    return ["wall_before_ns": wallBefore, "mach_absolute": absolute, "mach_continuous": continuous,
            "mono_ns": monotonic, "wall_after_ns": wallAfter]
}

/// One kernel accounting read of the worker, bracketed by this process's clock.
func rusageSample(_ pid: pid_t) -> [String: Any] {
    var info = rusage_info_v6()
    let before = mono()
    let rc = withUnsafeMutablePointer(to: &info) { pointer in
        pointer.withMemoryRebound(to: rusage_info_t?.self, capacity: 1) {
            proc_pid_rusage(pid, RUSAGE_INFO_V6, $0)
        }
    }
    let err = rc == 0 ? 0 : errno
    var sample: [String: Any] = ["before_ns": before, "after_ns": mono(), "rc": rc, "errno": err]
    if rc == 0 {
        sample.merge(["user_time": info.ri_user_time, "system_time": info.ri_system_time,
                      "proc_start_abstime": info.ri_proc_start_abstime,
                      "proc_exit_abstime": info.ri_proc_exit_abstime]) { $1 }
    }
    return sample
}

/// Scheduler state of each worker thread (TH_STATE_RUNNING 1, WAITING 3, ...).
func threadStates(_ pid: pid_t) -> [[String: Any]] {
    var handles = [UInt64](repeating: 0, count: 16)
    let bytes = proc_pidinfo(pid, PROC_PIDLISTTHREADS, 0, &handles, Int32(handles.count * 8))
    guard bytes > 0 else { return [["list_errno": Int(errno)]] }
    return handles.prefix(Int(bytes) / 8).map { handle in
        var info = proc_threadinfo()
        let count = proc_pidinfo(pid, PROC_PIDTHREADINFO, handle, &info, Int32(MemoryLayout<proc_threadinfo>.size))
        guard count > 0 else { return ["handle": handle, "errno": Int(errno)] }
        return ["handle": handle, "run_state": Int(info.pth_run_state), "flags": Int(info.pth_flags),
                "user_time": info.pth_user_time, "system_time": info.pth_system_time]
    }
}

/// PROC_PIDUNIQIDENTIFIERINFO (17) and its layout are private in the SDK; the
/// same 56-byte layout is read by records/performance/host-lifetime/observe.py.
struct UniqIdentifierInfo {
    var uuid: (UInt64, UInt64) = (0, 0)
    var uniqueid: UInt64 = 0
    var puniqueid: UInt64 = 0
    var idversion: Int32 = 0
    var reserve2: UInt32 = 0
    var reserve3: UInt64 = 0
    var reserve4: UInt64 = 0
}

func identity(_ pid: pid_t) -> [String: Any] {
    var bsd = proc_bsdinfo()
    let bsdCount = proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &bsd, Int32(MemoryLayout<proc_bsdinfo>.size))
    var uniq = UniqIdentifierInfo()
    let uniqCount = proc_pidinfo(pid, 17, 0, &uniq, Int32(MemoryLayout<UniqIdentifierInfo>.size))
    var path = [CChar](repeating: 0, count: 4096)
    let pathCount = proc_pidpath(pid, &path, 4096)
    return [
        "pid": pid,
        "ppid": bsdCount > 0 ? Int(bsd.pbi_ppid) : NSNull(),
        "start_wall_us": bsdCount > 0 ? bsd.pbi_start_tvsec * 1_000_000 + bsd.pbi_start_tvusec : NSNull(),
        "uniqueid": uniqCount > 0 ? uniq.uniqueid : NSNull(),
        "parent_uniqueid": uniqCount > 0 ? uniq.puniqueid : NSNull(),
        "path": pathCount > 0 ? String(cString: path) : NSNull(),
    ]
}

/// A generic, lossless-enough projection of driver values for retention.
func jsonValue(_ value: Any) -> Any {
    switch value {
    case let v as Bool: return v
    case let v as String: return v
    case let v as Int: return v
    case let v as Int32: return Int(v)
    case let v as Int64: return v
    case let v as UInt32: return Int(v)
    case let v as UInt64: return v <= UInt64(Int64.max) ? NSNumber(value: v) : String(v)
    case let v as Double: return v.isFinite ? v : String(v)
    default: break
    }
    let mirror = Mirror(reflecting: value)
    switch mirror.displayStyle {
    case .optional:
        return mirror.children.first.map { jsonValue($0.value) } ?? NSNull()
    case .collection, .set, .tuple:
        return mirror.children.map { jsonValue($0.value) }
    case .dictionary:
        var out: [String: Any] = [:]
        for child in mirror.children {
            let pair = Mirror(reflecting: child.value).children.map { $0.value }
            if pair.count == 2 { out[String(describing: pair[0])] = jsonValue(pair[1]) }
        }
        return out
    case .enum:
        if let child = mirror.children.first {
            return [child.label ?? "case": jsonValue(child.value)]
        }
        return String(describing: value)
    case .struct, .class:
        var out: [String: Any] = [:]
        for child in mirror.children {
            if let label = child.label { out[label] = jsonValue(child.value) }
        }
        return out
    default:
        return String(describing: value)
    }
}

final class Recorder: @unchecked Sendable {
    let lock = NSLock()
    var calls: [[String: Any]] = []
    var events: [[String: Any]] = []
    var samples: [[String: Any]] = []
    var stop = false
    var graceSignalled = false
    func add(call: [String: Any]) { lock.lock(); calls.append(call); lock.unlock() }
    func add(event: [String: Any]) { lock.lock(); events.append(event); lock.unlock() }
    var stopped: Bool { lock.lock(); defer { lock.unlock() }; return stop }
}

let options = parseOptions()
var timebase = mach_timebase_info_data_t()
mach_timebase_info(&timebase)
let target = (options.workDir as NSString).appendingPathComponent(options.target == "fifo" ? "attempt.fifo" : "attempt.file")
if options.target == "fifo" {
    guard mkfifo(target, 0o600) == 0 else { fail("mkfifo failed: \(errno)") }
} else {
    guard FileManager.default.createFile(atPath: target, contents: Data("late-publication".utf8)) else {
        fail("cannot create \(target)")
    }
}
let recorder = Recorder()
let unblockTrigger = DispatchSemaphore(value: 0)
var triggerAtNs: UInt64 = 0
let unblockDelayMs = options.unblockAfterReleaseMs ?? options.unblockAfterGraceEntryMs

// Release control: open the write end without blocking (it succeeds only while
// a reader is present), write one byte and close, so the worker's open() and
// read() return. Never runs when no unblock is scheduled.
let controlDone = DispatchSemaphore(value: 0)
if let delay = unblockDelayMs {
    Thread.detachNewThread {
        defer { controlDone.signal() }
        guard unblockTrigger.wait(timeout: .now() + 30) == .success else {
            recorder.add(event: ["kind": "unblock_not_triggered", "at_ns": mono()]); return
        }
        let due = triggerAtNs + UInt64(delay) * 1_000_000
        while mono() < due {
            let remaining = due - mono()
            var request = timespec(tv_sec: Int(remaining / 1_000_000_000), tv_nsec: Int(remaining % 1_000_000_000))
            nanosleep(&request, nil)
        }
        let openStart = mono()
        let fd = open(target, O_WRONLY | O_NONBLOCK)
        let openErrno = fd < 0 ? errno : 0
        let openEnd = mono()
        var event: [String: Any] = ["kind": "unblock", "due_ns": due, "open_start_ns": openStart,
                                    "open_end_ns": openEnd, "open_fd_valid": fd >= 0, "open_errno": openErrno]
        if fd >= 0 {
            var byte: UInt8 = 0x78
            let written = write(fd, &byte, 1)
            event["write_rc"] = written
            event["write_end_ns"] = mono()
            close(fd)
            event["close_end_ns"] = mono()
        }
        recorder.add(event: event)
    }
}

// The production process calls, timestamped. The readiness wait and the grace
// loop sleep 10 ms per pass and the sentinel loop at most 2 ms, so the first
// 10 ms sleep request after a sentinel sleep marks grace entry, after the
// exit-request store and the first grace wait.
let production = ChildProcessCalls()
var calls = ChildProcessCalls()
calls.wait = { pid, status, waitOptions in
    let start = mono()
    let rc = production.wait(pid, status, waitOptions)
    let err = rc < 0 ? errno : 0
    recorder.add(call: ["call": "wait", "options": Int(waitOptions), "rc": Int(rc), "errno": Int(err),
                        "status": rc == pid ? Int(status.pointee) : NSNull(), "start_ns": start, "end_ns": mono()])
    return rc
}
calls.kill = { pid, signal in
    let start = mono()
    let rc = production.kill(pid, signal)
    let err = rc < 0 ? errno : 0
    recorder.add(call: ["call": "kill", "signal": Int(signal), "rc": Int(rc), "errno": Int(err),
                        "start_ns": start, "end_ns": mono()])
    return rc
}
var sawSentinelSleep = false
calls.sleep = { ns in
    let start = mono()
    if ns <= 2_000_000 { sawSentinelSleep = true }
    if ns == 10_000_000 && sawSentinelSleep {
        recorder.lock.lock()
        let first = !recorder.graceSignalled
        recorder.graceSignalled = true
        recorder.lock.unlock()
        if first {
            recorder.add(event: ["kind": "grace_entry_detected", "at_ns": start])
            if options.unblockAfterGraceEntryMs != nil { triggerAtNs = start; unblockTrigger.signal() }
        }
    }
    production.sleep(ns)
    recorder.add(call: ["call": "sleep", "requested_ns": ns, "start_ns": start, "end_ns": mono()])
}

// Worker exit by kqueue NOTE_EXIT on this process's clock; it never reaps.
let kq = kqueue()
guard kq >= 0 else { fail("kqueue failed: \(errno)") }
let watcherDone = DispatchSemaphore(value: 0)
Thread.detachNewThread {
    var events: [kevent] = Array(repeating: kevent(ident: 0, filter: 0, flags: 0, fflags: 0, data: 0, udata: nil),
                                 count: 4)
    var timeout = timespec(tv_sec: 0, tv_nsec: 20_000_000)
    while !recorder.stopped {
        let count = kevent(kq, nil, 0, &events, 4, &timeout)
        let at = mono()
        if count > 0 {
            for event in events[0..<Int(count)] {
                recorder.add(event: ["kind": "worker_exit_kevent", "at_ns": at, "ident": Int(event.ident),
                                     "fflags": Int(event.fflags)])
            }
        }
    }
    watcherDone.signal()
}

var hook: [String: Any] = [:]
var releaseCalls: [[String: Any]] = []
let samplerDone = DispatchSemaphore(value: 0)
var samplerStarted = false

let phaseHook: CWorkerPhaseHook = { pid, index in
    hook["entry_ns"] = mono()
    hook["index"] = index
    hook["clocks_entry"] = clockReadings()
    hook["worker_identity_entry"] = identity(pid)
    var exitChange = kevent(ident: UInt(pid), filter: Int16(EVFILT_PROC), flags: UInt16(EV_ADD | EV_ONESHOT),
                            fflags: NOTE_EXIT, data: 0, udata: nil)
    hook["exit_registration_rc"] = kevent(kq, &exitChange, 1, nil, 0, nil)
    samplerStarted = true
    Thread.detachNewThread {
        // Scheduler state and CPU every interval until the worker exits or the run ends.
        while !recorder.stopped {
            var sample = rusageSample(pid)
            sample["threads"] = threadStates(pid)
            recorder.lock.lock(); recorder.samples.append(sample); recorder.lock.unlock()
            if (sample["rc"] as? Int32) != 0 || ((sample["proc_exit_abstime"] as? UInt64) ?? 0) != 0 { break }
            usleep(options.sampleIntervalMs * 1000)
        }
        samplerDone.signal()
    }
    // A short hold samples the spinning worker before release: a control for the
    // scheduler-state reading. The host excludes it from the sentinel allowance.
    let holdEnd = (hook["entry_ns"] as! UInt64) + UInt64(options.holdMs) * 1_000_000
    while mono() < holdEnd {
        let remaining = holdEnd - mono()
        var request = timespec(tv_sec: Int(remaining / 1_000_000_000), tv_nsec: Int(remaining % 1_000_000_000))
        nanosleep(&request, nil)
    }
    hook["exit_ns"] = mono()
}

var input = CWorkerInput(workerExecutablePath: options.worker,
                         policy: "(version 1)(allow default)(deny mach-lookup)",
                         slots: [CWorkerSlotInput(stepId: "r1", attemptKind: .fileOpenRead, target: target)],
                         phases: [CWorkerPhaseInput(firstSlot: 0, endSlot: 1)],
                         sentinelTimeoutMs: options.sentinelMs,
                         exitGraceMs: options.graceMs,
                         postApplyHangMs: options.hangMs > 0 ? options.hangMs : nil)
input.phaseReleaseOrdinal = { index in
    // Called by the driver immediately before its release store.
    let at = mono()
    releaseCalls.append(["index": index, "at_ns": at])
    if options.unblockAfterReleaseMs != nil { triggerAtNs = at; unblockTrigger.signal() }
    return UInt32(index + 1)
}

let clocksStart = clockReadings()
let runStart = mono()
let result = runCWorker(input, processCalls: calls, phaseBoundary: phaseHook)
let runEnd = mono()
let clocksEnd = clockReadings()

recorder.lock.lock(); recorder.stop = true; recorder.lock.unlock()
if samplerStarted { _ = samplerDone.wait(timeout: .now() + 2) }
if unblockDelayMs != nil {
    // An unblock that never triggered is released here so its thread ends.
    unblockTrigger.signal()
    _ = controlDone.wait(timeout: .now() + 5)
}
_ = watcherDone.wait(timeout: .now() + 2)
let fifoExistedAfterRun = access(target, F_OK) == 0
unlink(target)

// The orchestrator's own reading of this driver result, without a validator.
var classified: [String: Any] = [:]
if case .success(let out) = result {
    let disposition = resolveDisposition(out, plan: nil)
    let run = classify(workerResult: result, validatorResult: nil, expectedVerdictCount: 0, disposition: disposition)
    classified = ["outcome": run.outcome, "rc": run.rc, "error": run.error ?? NSNull(),
                  "disposition": jsonValue(disposition)]
}

recorder.lock.lock()
let record: [String: Any] = [
    "format": 1,
    "label": options.label,
    "options": ["target": options.target, "sentinel_ms": options.sentinelMs, "grace_ms": options.graceMs,
                "hang_ms": options.hangMs,
                "unblock_after_release_ms": options.unblockAfterReleaseMs.map { $0 as Any } ?? NSNull(),
                "unblock_after_grace_entry_ms": options.unblockAfterGraceEntryMs.map { $0 as Any } ?? NSNull(),
                "sample_interval_ms": Int(options.sampleIntervalMs), "hold_ms": options.holdMs,
                "worker": options.worker,
                "policy": input.policy, "attempt": "fileOpenRead", "attempt_target": target],
    "fixture_pid": Int(getpid()),
    "mach_timebase": [Int(timebase.numer), Int(timebase.denom)],
    "run_start_ns": runStart, "run_end_ns": runEnd,
    "clocks": ["run_start": clocksStart, "run_end": clocksEnd],
    "hook": hook,
    "release_ordinal_calls": releaseCalls,
    "process_calls": recorder.calls,
    "events": recorder.events,
    "samples": recorder.samples,
    "target_existed_after_run": fifoExistedAfterRun,
    "classified": classified,
    "driver": jsonValue(result),
]
recorder.lock.unlock()
let data = try JSONSerialization.data(withJSONObject: record, options: [.sortedKeys, .prettyPrinted])
guard FileManager.default.createFile(atPath: options.out, contents: data) else { fail("cannot write \(options.out)") }
print(options.out)
