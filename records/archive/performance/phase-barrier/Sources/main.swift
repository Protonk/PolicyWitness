// One phase-barrier observation: the shipped C worker compiles and applies a
// real policy, arrives at its single phase, and waits while this process holds
// the driver's phaseBoundary callback for a requested time. The hold is a
// controlled substitute for collection time; no validator runs. The attempt
// unlinks a file this process owns, so the file's existence during the hold
// witnesses that the action had not run.
//
// Clocks: every *_ns time is CLOCK_MONOTONIC_RAW in nanoseconds. Worker CPU
// comes from proc_pid_rusage(RUSAGE_INFO_V6) on the worker's PID, read by this
// process; *_abstime and rusage time fields are reported raw with the mach
// timebase so the reader converts them.

import Darwin
import Foundation
@testable import PWRunnerCore

@inline(__always) func mono() -> UInt64 { clock_gettime_nsec_np(CLOCK_MONOTONIC_RAW) }

/// Simultaneous-enough readings that place kernel stamps (wall-clock creation
/// time, mach absolute time) on the CLOCK_MONOTONIC_RAW axis.
func clockReadings() -> [String: Any] {
    let wallBefore = clock_gettime_nsec_np(CLOCK_REALTIME)
    let absolute = mach_absolute_time()
    let continuous = mach_continuous_time()
    let monotonic = mono()
    let wallAfter = clock_gettime_nsec_np(CLOCK_REALTIME)
    return ["wall_before_ns": wallBefore, "mach_absolute": absolute, "mach_continuous": continuous,
            "mono_ns": monotonic, "wall_after_ns": wallAfter]
}

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(2)
}

struct Options {
    var worker = ""
    var workDir = ""
    var out = ""
    var condition = ""
    var holdMs = 0
    var proceedWaitMs: Int? = nil
    var sampling = "boundary"
    var samplerIntervalUs: UInt32 = 1000
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
        case "--condition": options.condition = value
        case "--hold-ms": options.holdMs = Int(value) ?? -1
        case "--proceed-wait-ms": options.proceedWaitMs = Int(value)
        case "--sampling": options.sampling = value
        case "--sampler-interval-us": options.samplerIntervalUs = UInt32(value) ?? 0
        default: fail("unknown argument \(flag)")
        }
    }
    guard !options.worker.isEmpty, !options.workDir.isEmpty, !options.out.isEmpty,
          !options.condition.isEmpty, options.holdMs >= 0, options.samplerIntervalUs > 0,
          ["none", "boundary", "dense"].contains(options.sampling) else {
        fail("usage: --worker PATH --work-dir DIR --out PATH --condition NAME --hold-ms N "
             + "[--proceed-wait-ms N] [--sampling none|boundary|dense] [--sampler-interval-us N]")
    }
    return options
}

/// One kernel accounting read of a process, bracketed by this process's clock.
func rusageSample(_ pid: pid_t) -> [String: Any] {
    var info = rusage_info_v6()
    let before = mono()
    let rc = withUnsafeMutablePointer(to: &info) { pointer in
        pointer.withMemoryRebound(to: rusage_info_t?.self, capacity: 1) {
            proc_pid_rusage(pid, RUSAGE_INFO_V6, $0)
        }
    }
    let err = rc == 0 ? 0 : errno
    let after = mono()
    var sample: [String: Any] = ["before_ns": before, "after_ns": after, "rc": rc, "errno": err]
    if rc == 0 {
        sample.merge([
            "user_time": info.ri_user_time, "system_time": info.ri_system_time,
            "user_ptime": info.ri_user_ptime, "system_ptime": info.ri_system_ptime,
            "runnable_time": info.ri_runnable_time,
            "instructions": info.ri_instructions, "cycles": info.ri_cycles,
            "pinstructions": info.ri_pinstructions, "pcycles": info.ri_pcycles,
            "pkg_idle_wkups": info.ri_pkg_idle_wkups, "interrupt_wkups": info.ri_interrupt_wkups,
            "energy_nj": info.ri_energy_nj, "penergy_nj": info.ri_penergy_nj,
            "proc_start_abstime": info.ri_proc_start_abstime,
            "proc_exit_abstime": info.ri_proc_exit_abstime,
        ]) { $1 }
    }
    return sample
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
let procPidUniqIdentifierInfo: Int32 = 17
assert(MemoryLayout<UniqIdentifierInfo>.size == 56)

func identity(_ pid: pid_t) -> [String: Any] {
    var bsd = proc_bsdinfo()
    let bsdCount = proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &bsd, Int32(MemoryLayout<proc_bsdinfo>.size))
    var uniq = UniqIdentifierInfo()
    let uniqCount = proc_pidinfo(pid, procPidUniqIdentifierInfo, 0, &uniq,
                                 Int32(MemoryLayout<UniqIdentifierInfo>.size))
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

func selfUsage(_ who: Int32) -> [String: Any] {
    var usage = rusage()
    getrusage(who, &usage)
    return ["user_us": Int64(usage.ru_utime.tv_sec) * 1_000_000 + Int64(usage.ru_utime.tv_usec),
            "system_us": Int64(usage.ru_stime.tv_sec) * 1_000_000 + Int64(usage.ru_stime.tv_usec),
            "at_ns": mono()]
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
    var kevents: [[String: Any]] = []
    var dense: [[String: Any]] = []
    var stopWatcher = false
    var stopSampler = false
    func add(event: [String: Any]) { lock.lock(); kevents.append(event); lock.unlock() }
    var watcherStopped: Bool { lock.lock(); defer { lock.unlock() }; return stopWatcher }
    var samplerStopped: Bool { lock.lock(); defer { lock.unlock() }; return stopSampler }
}

let options = parseOptions()
var timebase = mach_timebase_info_data_t()
mach_timebase_info(&timebase)
let target = (options.workDir as NSString).appendingPathComponent("unlink-target")
guard FileManager.default.createFile(atPath: target, contents: Data("phase-barrier".utf8)) else {
    fail("cannot create \(target)")
}
let recorder = Recorder()

// Passive observer: the attempt's unlink and the worker's exit, by kqueue on
// this process's clock. Registering NOTE_EXIT never reaps the worker.
let kq = kqueue()
let targetFD = open(target, O_EVTONLY)
guard kq >= 0, targetFD >= 0 else { fail("kqueue or O_EVTONLY open failed: \(errno)") }
var vnodeChange = kevent(ident: UInt(targetFD), filter: Int16(EVFILT_VNODE), flags: UInt16(EV_ADD | EV_CLEAR),
                         fflags: UInt32(NOTE_DELETE), data: 0, udata: nil)
guard kevent(kq, &vnodeChange, 1, nil, 0, nil) == 0 else { fail("vnode registration failed: \(errno)") }
let watcherDone = DispatchSemaphore(value: 0)
Thread.detachNewThread {
    var events: [kevent] = Array(repeating: kevent(ident: 0, filter: 0, flags: 0, fflags: 0, data: 0, udata: nil),
                                 count: 8)
    var timeout = timespec(tv_sec: 0, tv_nsec: 20_000_000)
    while !recorder.watcherStopped {
        let count = kevent(kq, nil, 0, &events, 8, &timeout)
        let at = mono()
        if count > 0 {
            for event in events[0..<Int(count)] {
                recorder.add(event: ["at_ns": at, "ident": Int(event.ident), "fflags": Int(event.fflags),
                                     "data": Int(event.data),
                                     "kind": event.filter == Int16(EVFILT_VNODE) ? "vnode" : "proc"])
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
    let entry = mono()
    hook["entry_ns"] = entry
    hook["clocks_entry"] = clockReadings()
    hook["index"] = index
    hook["fixture_usage_entry"] = selfUsage(RUSAGE_SELF)
    hook["worker_identity_entry"] = identity(pid)
    if options.sampling != "none" { hook["sample_entry"] = rusageSample(pid) }
    hook["file_exists_at_entry"] = access(target, F_OK) == 0
    var exitChange = kevent(ident: UInt(pid), filter: Int16(EVFILT_PROC), flags: UInt16(EV_ADD | EV_ONESHOT),
                            fflags: NOTE_EXIT, data: 0, udata: nil)
    hook["exit_registration_rc"] = kevent(kq, &exitChange, 1, nil, 0, nil)
    if options.sampling == "dense" {
        samplerStarted = true
        Thread.detachNewThread {
            // Continues through release and acknowledgement until the worker's
            // exit is recorded, its accounting disappears, or the run ends.
            while !recorder.samplerStopped {
                let sample = rusageSample(pid)
                recorder.lock.lock(); recorder.dense.append(sample); recorder.lock.unlock()
                if (sample["rc"] as? Int32) != 0 || ((sample["proc_exit_abstime"] as? UInt64) ?? 0) != 0 { break }
                usleep(options.samplerIntervalUs)
            }
            samplerDone.signal()
        }
    }
    let holdEnd = entry + UInt64(options.holdMs) * 1_000_000
    var sleeps = 0
    while true {
        let now = mono()
        if now >= holdEnd { break }
        let remaining = holdEnd - now
        var request = timespec(tv_sec: Int(remaining / 1_000_000_000), tv_nsec: Int(remaining % 1_000_000_000))
        nanosleep(&request, nil)
        sleeps += 1
    }
    hook["sleep_calls"] = sleeps
    hook["file_exists_at_exit"] = access(target, F_OK) == 0
    if options.sampling != "none" { hook["sample_exit"] = rusageSample(pid) }
    hook["fixture_usage_exit"] = selfUsage(RUSAGE_SELF)
    hook["exit_ns"] = mono()
}

var input = CWorkerInput(workerExecutablePath: options.worker,
                         policy: "(version 1)(allow default)(deny mach-lookup)",
                         slots: [CWorkerSlotInput(stepId: "u1", attemptKind: .fileUnlink, target: target)],
                         phases: [CWorkerPhaseInput(firstSlot: 0, endSlot: 1)])
input.proceedWaitMs = options.proceedWaitMs
input.phaseReleaseOrdinal = { index in
    // Called by the driver immediately before its release store.
    releaseCalls.append(["index": index, "at_ns": mono()])
    return UInt32(index + 1)
}

let clocksStart = clockReadings()
let childrenBefore = selfUsage(RUSAGE_CHILDREN)
let runStart = mono()
let result = runCWorker(input, phaseBoundary: phaseHook)
let runEnd = mono()
let childrenAfter = selfUsage(RUSAGE_CHILDREN)
let clocksEnd = clockReadings()
let fileAfter = access(target, F_OK) == 0

recorder.lock.lock(); recorder.stopSampler = true; recorder.lock.unlock()
if samplerStarted { _ = samplerDone.wait(timeout: .now() + 2) }
usleep(30_000)  // let a late kqueue event arrive before the watcher stops
recorder.lock.lock(); recorder.stopWatcher = true; recorder.lock.unlock()
_ = watcherDone.wait(timeout: .now() + 2)

// Unit calibration after the run: rusage_info time fields against getrusage
// for this process's own CPU burn.
let calibrationBefore = (rusageSample(getpid()), selfUsage(RUSAGE_SELF))
let burnEnd = mono() + 30_000_000
var spin: UInt64 = 0
while mono() < burnEnd { spin &+= 1 }
let calibrationAfter = (rusageSample(getpid()), selfUsage(RUSAGE_SELF))

recorder.lock.lock()
let record: [String: Any] = [
    "format": 1,
    "condition": options.condition,
    "options": ["hold_ms": options.holdMs, "proceed_wait_ms": options.proceedWaitMs.map { $0 as Any } ?? NSNull(),
                "sampling": options.sampling, "sampler_interval_us": Int(options.samplerIntervalUs),
                "worker": options.worker, "work_dir": options.workDir, "policy": input.policy],
    "fixture_pid": Int(getpid()),
    "mach_timebase": [Int(timebase.numer), Int(timebase.denom)],
    "run_start_ns": runStart, "run_end_ns": runEnd,
    "clocks": ["run_start": clocksStart, "run_end": clocksEnd],
    "hook": hook,
    "hook_invocations": hook.isEmpty ? 0 : 1,
    "release_ordinal_calls": releaseCalls,
    "kevents": recorder.kevents,
    "dense_samples": options.sampling == "dense" ? recorder.dense : NSNull(),
    "file_exists_after_run": fileAfter,
    "children_usage": ["before": childrenBefore, "after": childrenAfter],
    "calibration": ["before": ["rusage_info": calibrationBefore.0, "getrusage": calibrationBefore.1],
                    "after": ["rusage_info": calibrationAfter.0, "getrusage": calibrationAfter.1],
                    "spin_iterations": spin],
    "driver": jsonValue(result),
]
recorder.lock.unlock()
let data = try JSONSerialization.data(withJSONObject: record, options: [.sortedKeys, .prettyPrinted])
guard FileManager.default.createFile(atPath: options.out, contents: data) else { fail("cannot write \(options.out)") }
print(options.out)
