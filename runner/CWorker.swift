import Darwin
import Foundation

/*
 * CWorker — Swift driver for pw-probe-runner. Per RUNNER-RESHAPE-PLAN
 * Step 6.2 (R9 part 1). Owns the host side of the shared-memory ABI
 * defined in controller/tools/pw_probe_runner/pw_probe_runner_abi.h
 * and mirrored as offset constants below.
 *
 * This module is intentionally self-contained: it does not depend on
 * PWRunnerService, WorkerProcess, or any of the legacy Swift-worker
 * machinery. The integration into PWRunnerService is Step 6.3.
 *
 * Flow (mirrors tests/suites/runner_c_worker_harness/harness.c):
 *   1. shm_open + ftruncate + mmap a PWShmLayout.regionBytes region;
 *      clear FD_CLOEXEC so the child inherits the FD.
 *   2. Memset the header to zero, populate abi_version, step_count,
 *      param_count; populate slot inputs from the request; populate
 *      param keys/values from policy.params.
 *   3. Pre-touch every page so the worker's post-apply writes never
 *      depend on lazy allocation (R8).
 *   4. Release-store `prepared = 1`.
 *   5. Create ready + policy pipes. Mark parent-side ends FD_CLOEXEC.
 *   6. posix_spawn pw-probe-runner with FDs dup'd to 0/3/4.
 *   7. Write the policy text to the policy pipe and close.
 *   8. Read the pre-apply ready byte (deadline).
 *   9. Acquire-poll `applied`, then `done`, with bounded timeouts.
 *  10. Release-store `exit_requested = 1`; waitpid with grace timer;
 *      SIGKILL fallback if the worker hangs.
 *  11. Reconstruct CWorkerStepResult per slot by reading the shm
 *      output fields once `completed == 1`.
 *
 * Errors are surfaced via CWorkerRunError; the caller (Step 6.3 code
 * in PWRunnerService) maps them to the runner's normalized_outcome
 * vocabulary. Nothing in this module reaches into PWRunnerAPI's
 * existing types.
 */

// MARK: - ABI mirror

/// Wire-stable layout of the shm region. Mirrors pw_probe_runner_abi.h.
/// A future ABI bump in the C header MUST update these constants;
/// source_drift (Step 6.5 extension) will enforce.
public enum PWShmLayout {
    public static let abiVersion: UInt32   = 2

    public static let headerBytes: Int     = 64
    public static let slotBytes: Int       = 2048
    public static let maxSteps: Int        = 256
    public static let paramBytes: Int      = 512
    public static let maxParams: Int       = 16

    public static let regionBytes: Int =
        headerBytes + maxSteps * slotBytes + maxParams * paramBytes

    // Header field offsets (in bytes from region base).
    public static let abiVersionOffset: Int    = 0
    public static let stepCountOffset: Int     = 4
    public static let preparedOffset: Int      = 8
    public static let appliedOffset: Int       = 12
    public static let doneOffset: Int          = 16
    public static let exitRequestedOffset: Int = 20
    public static let applyRcOffset: Int       = 24
    public static let paramCountOffset: Int    = 28

    public static let slotsOffset: Int    = headerBytes
    public static let paramsOffset: Int   = headerBytes + maxSteps * slotBytes

    // Slot field offsets (from the slot's base).
    public static let stepIdMax: Int           = 64
    public static let targetMax: Int           = 512
    public static let observedPathMax: Int     = 1024
    public static let errorMax: Int            = 256

    public static let slotStepIdOffset: Int       = 0
    public static let slotAttemptKindOffset: Int  = 64
    public static let slotTargetOffset: Int       = 68
    public static let slotRcOffset: Int           = 580
    public static let slotErrnoOffset: Int        = 584
    public static let slotObservedPathOffset: Int = 588
    public static let slotErrorOffset: Int        = 1612
    public static let slotCompletedOffset: Int    = 1868

    // Param field offsets (from the param's base).
    public static let paramKeyMax: Int    = 128
    public static let paramValueMax: Int  = 384
    public static let paramKeyOffset: Int   = 0
    public static let paramValueOffset: Int = 128
}

/// Mirrors pw_attempt_kind_t in the C ABI. Wire-stable: NEVER renumber.
public enum PWAttemptKind: UInt32 {
    case none           = 0
    case fileOpenRead   = 1
    case fileOpenWrite  = 2
    case fileCreate     = 3
    case fileUnlink     = 4
    case fileAccess     = 5
    case machLookup     = 6
}

// MARK: - C atomic shim binding

@_silgen_name("pw_cworker_load_acquire_u32")
private func pw_cworker_load_acquire_u32(_ p: UnsafePointer<UInt32>) -> UInt32

@_silgen_name("pw_cworker_store_release_u32")
private func pw_cworker_store_release_u32(_ p: UnsafeMutablePointer<UInt32>, _ value: UInt32)

@_silgen_name("pw_cworker_shm_open_create")
private func pw_cworker_shm_open_create(_ name: UnsafePointer<CChar>, _ mode: mode_t) -> Int32

// MARK: - Public input/output types

public struct CWorkerSlotInput {
    public var stepId: String
    public var attemptKind: PWAttemptKind
    public var target: String

    public init(stepId: String, attemptKind: PWAttemptKind, target: String) {
        self.stepId = stepId
        self.attemptKind = attemptKind
        self.target = target
    }
}

public struct CWorkerParam {
    public var key: String
    public var value: String

    public init(key: String, value: String) {
        self.key = key
        self.value = value
    }
}

public struct CWorkerInput {
    public var workerExecutablePath: String
    public var policy: String
    public var params: [CWorkerParam]
    public var slots: [CWorkerSlotInput]
    public var readyByteTimeoutMs: Int
    public var sentinelTimeoutMs: Int
    public var exitGraceMs: Int
    /// Optional test-seam routed to pw-probe-runner as
    /// `--post-apply-hang-ms <N>`. When > 0, the worker sleeps for
    /// N ms after every slot is durable but before flipping `done`;
    /// drives the host's `runner_timeout` outcome from a real
    /// specimen. Production callers pass nil. Step 6.6 / R12b.
    public var postApplyHangMs: Int?

    public init(workerExecutablePath: String,
                policy: String,
                params: [CWorkerParam] = [],
                slots: [CWorkerSlotInput],
                readyByteTimeoutMs: Int = 1_000,
                sentinelTimeoutMs: Int = 60_000,
                exitGraceMs: Int = 1_000,
                postApplyHangMs: Int? = nil) {
        self.workerExecutablePath = workerExecutablePath
        self.policy = policy
        self.params = params
        self.slots = slots
        self.readyByteTimeoutMs = readyByteTimeoutMs
        self.sentinelTimeoutMs = sentinelTimeoutMs
        self.exitGraceMs = exitGraceMs
        self.postApplyHangMs = postApplyHangMs
    }
}

public struct CWorkerSlotResult {
    public var stepId: String
    public var rc: Int32
    public var errnoVal: Int32
    public var observedPath: String?
    public var error: String?
    public var completed: Bool
}

public struct CWorkerOutput {
    public var workerPid: pid_t
    public var readyByteReceived: Bool
    public var applied: Bool
    public var applyRC: Int32
    public var done: Bool
    public var sentSigkill: Bool
    public var exitCode: Int32?     // nil if signaled
    public var termSignal: Int32?   // nil if clean exit
    public var slots: [CWorkerSlotResult]
}

public enum CWorkerRunError: Error, CustomStringConvertible {
    case slotCountExceeded(Int)
    case paramCountExceeded(Int)
    case slotInputTooLong(field: String, stepId: String, max: Int)
    case paramInputTooLong(field: String, key: String, max: Int)
    case shmSetupFailed(String)
    case pipeFailed(String)
    case spawnFailed(String)
    case policyWriteFailed(String)

    public var description: String {
        switch self {
        case .slotCountExceeded(let n):
            return "request has \(n) probe steps; pw-probe-runner ABI caps at \(PWShmLayout.maxSteps)"
        case .paramCountExceeded(let n):
            return "request has \(n) policy params; pw-probe-runner ABI caps at \(PWShmLayout.maxParams)"
        case .slotInputTooLong(let field, let stepId, let max):
            return "slot \(stepId) \(field) exceeds ABI max (\(max) bytes including NUL)"
        case .paramInputTooLong(let field, let key, let max):
            return "param \(key) \(field) exceeds ABI max (\(max) bytes including NUL)"
        case .shmSetupFailed(let why): return "shm setup: \(why)"
        case .pipeFailed(let why):     return "pipe: \(why)"
        case .spawnFailed(let why):    return "posix_spawn: \(why)"
        case .policyWriteFailed(let why): return "write(policy_pipe): \(why)"
        }
    }
}

public enum CWorkerRunResult {
    case success(CWorkerOutput)
    case failure(CWorkerRunError)
}

// MARK: - Driver

/// Callback invoked once the worker's `applied` sentinel flips, before
/// the driver starts polling `done`. The callback receives the worker
/// PID — that's the moment the validator child (or any other observer
/// that wants to inspect the sandboxed worker) can be spawned. The
/// callback runs synchronously; the driver does NOT poll `done` while
/// it's executing, so a hook that blocks for longer than the per-attempt
/// deadline will push the overall worker wait out by the same margin.
/// The hook should complete in well under sentinelTimeoutMs.
public typealias CWorkerPostAppliedHook = (pid_t) -> Void

public func runCWorker(_ input: CWorkerInput,
                       postApplied: CWorkerPostAppliedHook? = nil) -> CWorkerRunResult {
    // ---- Validation: bound the inputs to ABI caps before we touch shm.
    if input.slots.count > PWShmLayout.maxSteps {
        return .failure(.slotCountExceeded(input.slots.count))
    }
    if input.params.count > PWShmLayout.maxParams {
        return .failure(.paramCountExceeded(input.params.count))
    }
    for slot in input.slots {
        if slot.stepId.utf8.count >= PWShmLayout.stepIdMax {
            return .failure(.slotInputTooLong(field: "step_id", stepId: slot.stepId,
                                              max: PWShmLayout.stepIdMax))
        }
        if slot.target.utf8.count >= PWShmLayout.targetMax {
            return .failure(.slotInputTooLong(field: "target", stepId: slot.stepId,
                                              max: PWShmLayout.targetMax))
        }
    }
    for p in input.params {
        if p.key.utf8.count >= PWShmLayout.paramKeyMax {
            return .failure(.paramInputTooLong(field: "key", key: p.key,
                                                max: PWShmLayout.paramKeyMax))
        }
        if p.value.utf8.count >= PWShmLayout.paramValueMax {
            return .failure(.paramInputTooLong(field: "value", key: p.key,
                                                max: PWShmLayout.paramValueMax))
        }
    }

    // ---- shm region.
    let shmName: String = {
        // shm_open names cap at 32 chars on macOS including the leading '/'.
        let base = "/pw_cw_\(getpid())"
        return String(base.prefix(31))
    }()

    let shmFD = shmName.withCString { cName -> Int32 in
        return pw_cworker_shm_open_create(cName, 0o600)
    }
    if shmFD < 0 {
        return .failure(.shmSetupFailed("shm_open: \(String(cString: strerror(errno)))"))
    }
    // Unlink immediately; the FD survives and the region is anonymous-ish.
    _ = shmName.withCString { Darwin.shm_unlink($0) }
    // Clear FD_CLOEXEC so posix_spawn's adddup2 can land on FD 3 in the child.
    _ = fcntl(shmFD, F_SETFD, 0)

    if ftruncate(shmFD, off_t(PWShmLayout.regionBytes)) != 0 {
        let why = String(cString: strerror(errno))
        close(shmFD)
        return .failure(.shmSetupFailed("ftruncate: \(why)"))
    }
    guard let base = mmap(nil, PWShmLayout.regionBytes,
                          PROT_READ | PROT_WRITE,
                          MAP_SHARED, shmFD, 0) else {
        let why = String(cString: strerror(errno))
        close(shmFD)
        return .failure(.shmSetupFailed("mmap: \(why)"))
    }
    if base == MAP_FAILED {
        let why = String(cString: strerror(errno))
        close(shmFD)
        return .failure(.shmSetupFailed("mmap: \(why)"))
    }
    defer {
        _ = munmap(base, PWShmLayout.regionBytes)
        close(shmFD)
    }

    // Zero the region. The worker checks abi_version + prepared so a
    // leftover non-zero from a recycled mapping wouldn't be confusing,
    // but zeroing is cheap and removes a class of "did I clear it?"
    // questions.
    memset(base, 0, PWShmLayout.regionBytes)

    // ---- Populate header.
    let rawBase = base.assumingMemoryBound(to: UInt8.self)
    writeU32(rawBase, offset: PWShmLayout.abiVersionOffset, PWShmLayout.abiVersion)
    writeU32(rawBase, offset: PWShmLayout.stepCountOffset, UInt32(input.slots.count))
    writeU32(rawBase, offset: PWShmLayout.paramCountOffset, UInt32(input.params.count))

    // ---- Populate slots.
    for (i, slot) in input.slots.enumerated() {
        let slotBase = rawBase.advanced(by: PWShmLayout.slotsOffset + i * PWShmLayout.slotBytes)
        writeString(slotBase, offset: PWShmLayout.slotStepIdOffset,
                    value: slot.stepId, max: PWShmLayout.stepIdMax)
        writeU32(slotBase, offset: PWShmLayout.slotAttemptKindOffset,
                 slot.attemptKind.rawValue)
        writeString(slotBase, offset: PWShmLayout.slotTargetOffset,
                    value: slot.target, max: PWShmLayout.targetMax)
    }

    // ---- Populate params.
    for (i, p) in input.params.enumerated() {
        let paramBase = rawBase.advanced(by: PWShmLayout.paramsOffset + i * PWShmLayout.paramBytes)
        writeString(paramBase, offset: PWShmLayout.paramKeyOffset,
                    value: p.key, max: PWShmLayout.paramKeyMax)
        writeString(paramBase, offset: PWShmLayout.paramValueOffset,
                    value: p.value, max: PWShmLayout.paramValueMax)
    }

    // ---- Pre-touch every page. R8 requires this so post-apply writes
    // don't fault into the kernel's lazy-allocation path.
    let pageSize: Int = {
        let v = sysconf(_SC_PAGESIZE)
        return v > 0 ? Int(v) : 4096
    }()
    var off = 0
    while off < PWShmLayout.regionBytes {
        let p = rawBase.advanced(by: off)
        p.pointee = p.pointee
        off += pageSize
    }
    let last = rawBase.advanced(by: PWShmLayout.regionBytes - 1)
    last.pointee = last.pointee

    // ---- Release-store prepared sentinel.
    storeRelease(rawBase, offset: PWShmLayout.preparedOffset, 1)

    // ---- Pipes.
    var readyPipe = [Int32](repeating: -1, count: 2)
    var policyPipe = [Int32](repeating: -1, count: 2)
    if pipe(&readyPipe) != 0 {
        return .failure(.pipeFailed("ready pipe: \(String(cString: strerror(errno)))"))
    }
    if pipe(&policyPipe) != 0 {
        close(readyPipe[0]); close(readyPipe[1])
        return .failure(.pipeFailed("policy pipe: \(String(cString: strerror(errno)))"))
    }
    // Parent-only ends close on exec; child gets the dup2'd FDs only.
    _ = fcntl(readyPipe[0], F_SETFD, FD_CLOEXEC)
    _ = fcntl(policyPipe[1], F_SETFD, FD_CLOEXEC)

    // ---- posix_spawn.
    var fa: posix_spawn_file_actions_t? = nil
    posix_spawn_file_actions_init(&fa)
    defer { posix_spawn_file_actions_destroy(&fa) }
    posix_spawn_file_actions_adddup2(&fa, policyPipe[0], 0)
    posix_spawn_file_actions_adddup2(&fa, shmFD, 3)
    posix_spawn_file_actions_adddup2(&fa, readyPipe[1], 4)

    let stepCountStr = String(input.slots.count)
    var argv: [String] = [
        "pw-probe-runner",
        "--shm-fd", "3",
        "--ready-fd", "4",
        "--step-count", stepCountStr,
    ]
    if let hangMs = input.postApplyHangMs, hangMs > 0 {
        argv.append("--post-apply-hang-ms")
        argv.append(String(hangMs))
    }
    var pid: pid_t = 0
    let spawnRC = withCStringArrayCopy(argv) { argvPtr in
        posix_spawn(&pid, input.workerExecutablePath, &fa, nil, argvPtr, nil)
    }
    if spawnRC != 0 {
        close(policyPipe[0]); close(policyPipe[1])
        close(readyPipe[0]); close(readyPipe[1])
        return .failure(.spawnFailed("\(String(cString: strerror(spawnRC)))"))
    }
    // Close parent-side ends that the child now owns.
    close(policyPipe[0])
    close(readyPipe[1])

    // ---- Write policy and close.
    let policyBytes = Array(input.policy.utf8)
    let policyWritten: Int = policyBytes.withUnsafeBufferPointer { buf in
        guard let baseAddr = buf.baseAddress else { return 0 }
        var written = 0
        while written < buf.count {
            let n = Darwin.write(policyPipe[1], baseAddr.advanced(by: written),
                                 buf.count - written)
            if n < 0 {
                if errno == EINTR { continue }
                return -1
            }
            written += n
        }
        return written
    }
    close(policyPipe[1])
    if policyWritten < 0 {
        // Reap the worker before bailing so we don't leak the process.
        _ = kill(pid, SIGKILL)
        var st: Int32 = 0
        _ = waitpid(pid, &st, 0)
        close(readyPipe[0])
        return .failure(.policyWriteFailed("write: \(String(cString: strerror(errno)))"))
    }

    // ---- Read pre-apply ready byte.
    var readyByte: UInt8 = 0
    var readyByteReceived = false
    do {
        let pollIntervalNs: UInt64 = 10_000_000   // 10 ms
        let deadlineIters = max(1, input.readyByteTimeoutMs * 1_000_000 / Int(pollIntervalNs))
        // Set the read end nonblocking so we don't pin the loop on a single read.
        let flags = fcntl(readyPipe[0], F_GETFL, 0)
        if flags >= 0 { _ = fcntl(readyPipe[0], F_SETFL, flags | O_NONBLOCK) }
        for _ in 0..<deadlineIters {
            let n = Darwin.read(readyPipe[0], &readyByte, 1)
            if n == 1 { readyByteReceived = true; break }
            if n == 0 { break }     // EOF — worker exited without writing
            if n < 0 && errno != EAGAIN && errno != EINTR { break }
            sleepNs(pollIntervalNs)
        }
    }
    close(readyPipe[0])

    // ---- Poll applied, fire postApplied hook, then poll done.
    var sawApplied = false
    var sawDone = false
    do {
        let pollIntervalNs: UInt64 = 2_000_000   // 2 ms
        let deadlineIters = max(1, input.sentinelTimeoutMs * 1_000_000 / Int(pollIntervalNs))
        var hookFired = false
        for _ in 0..<deadlineIters {
            if !sawApplied && loadAcquire(rawBase, offset: PWShmLayout.appliedOffset) != 0 {
                sawApplied = true
            }
            // Fire the post-applied hook the first iteration after we
            // observe `applied`. The worker is now under the policy;
            // anything the hook does sees the sandboxed worker_pid.
            // We fire BEFORE checking `done` so a short-running worker
            // can't finish before the hook starts.
            if sawApplied && !hookFired {
                hookFired = true
                if let hook = postApplied { hook(pid) }
            }
            if loadAcquire(rawBase, offset: PWShmLayout.doneOffset) != 0 {
                sawDone = true
                break
            }
            sleepNs(pollIntervalNs)
        }
    }

    // ---- Read apply_rc (regular load — worker writes once, before done sentinel).
    let applyRC = readI32(rawBase, offset: PWShmLayout.applyRcOffset)

    // ---- Read slot outputs (must be done before exit_requested so the
    // shm reads are paired with the worker's release-store of completed).
    var slotResults: [CWorkerSlotResult] = []
    slotResults.reserveCapacity(input.slots.count)
    for i in 0..<input.slots.count {
        let slotBase = rawBase.advanced(by: PWShmLayout.slotsOffset + i * PWShmLayout.slotBytes)
        let completed = loadAcquire(slotBase, offset: PWShmLayout.slotCompletedOffset)
        let stepId = readString(slotBase, offset: PWShmLayout.slotStepIdOffset,
                                max: PWShmLayout.stepIdMax)
        let rc = readI32(slotBase, offset: PWShmLayout.slotRcOffset)
        let errnoVal = readI32(slotBase, offset: PWShmLayout.slotErrnoOffset)
        let observedRaw = readString(slotBase, offset: PWShmLayout.slotObservedPathOffset,
                                     max: PWShmLayout.observedPathMax)
        let errorRaw = readString(slotBase, offset: PWShmLayout.slotErrorOffset,
                                  max: PWShmLayout.errorMax)
        slotResults.append(CWorkerSlotResult(
            stepId: stepId,
            rc: rc,
            errnoVal: errnoVal,
            observedPath: observedRaw.isEmpty ? nil : observedRaw,
            error: errorRaw.isEmpty ? nil : errorRaw,
            completed: completed != 0
        ))
    }

    // ---- Request worker exit.
    storeRelease(rawBase, offset: PWShmLayout.exitRequestedOffset, 1)

    // ---- Reap (grace + SIGKILL fallback).
    var status: Int32 = 0
    var reaped: pid_t = 0
    var sentSigkill = false
    let pollIntervalNs: UInt64 = 10_000_000
    let graceIters = max(1, input.exitGraceMs * 1_000_000 / Int(pollIntervalNs))
    for _ in 0..<graceIters {
        let r = waitpid(pid, &status, WNOHANG)
        if r == pid { reaped = r; break }
        sleepNs(pollIntervalNs)
    }
    if reaped != pid {
        _ = kill(pid, SIGKILL)
        sentSigkill = true
        _ = waitpid(pid, &status, 0)
    }

    let exitCode: Int32?
    let termSignal: Int32?
    let wifexited = (status & 0x7f) == 0
    let wifsignaled = !wifexited && (((status & 0x7f) + 1) >> 1 > 0)
    if wifexited {
        exitCode = (status >> 8) & 0xff
        termSignal = nil
    } else if wifsignaled {
        exitCode = nil
        termSignal = status & 0x7f
    } else {
        exitCode = nil
        termSignal = nil
    }

    return .success(CWorkerOutput(
        workerPid: pid,
        readyByteReceived: readyByteReceived,
        applied: sawApplied,
        applyRC: applyRC,
        done: sawDone,
        sentSigkill: sentSigkill,
        exitCode: exitCode,
        termSignal: termSignal,
        slots: slotResults
    ))
}

// MARK: - Layout helpers

private func writeU32(_ base: UnsafeMutablePointer<UInt8>, offset: Int, _ value: UInt32) {
    base.advanced(by: offset).withMemoryRebound(to: UInt32.self, capacity: 1) { p in
        p.pointee = value
    }
}

private func readI32(_ base: UnsafePointer<UInt8>, offset: Int) -> Int32 {
    return base.advanced(by: offset).withMemoryRebound(to: Int32.self, capacity: 1) { p in
        p.pointee
    }
}

private func loadAcquire(_ base: UnsafePointer<UInt8>, offset: Int) -> UInt32 {
    return base.advanced(by: offset).withMemoryRebound(to: UInt32.self, capacity: 1) { p in
        pw_cworker_load_acquire_u32(p)
    }
}

private func storeRelease(_ base: UnsafeMutablePointer<UInt8>, offset: Int, _ value: UInt32) {
    base.advanced(by: offset).withMemoryRebound(to: UInt32.self, capacity: 1) { p in
        pw_cworker_store_release_u32(p, value)
    }
}

/// Copies `value` (UTF-8) into `base[offset..offset+max-1]`, NUL-terminating
/// at `offset + n` where `n = min(value.utf8.count, max - 1)`. Validation
/// happens earlier; this is a tight memcpy.
private func writeString(_ base: UnsafeMutablePointer<UInt8>, offset: Int,
                         value: String, max: Int) {
    let bytes = Array(value.utf8)
    let n = Swift.min(bytes.count, max - 1)
    let dst = base.advanced(by: offset)
    bytes.withUnsafeBufferPointer { buf in
        if let src = buf.baseAddress, n > 0 {
            memcpy(UnsafeMutableRawPointer(dst), src, n)
        }
    }
    dst.advanced(by: n).pointee = 0
}

/// Reads a NUL-bounded UTF-8 string from `base[offset..offset+max]`.
/// Stops at the first NUL or at `max`, whichever comes first.
private func readString(_ base: UnsafePointer<UInt8>, offset: Int, max: Int) -> String {
    let start = base.advanced(by: offset)
    var len = 0
    while len < max && start.advanced(by: len).pointee != 0 {
        len += 1
    }
    let data = Data(bytes: start, count: len)
    return String(data: data, encoding: .utf8) ?? ""
}

// MARK: - Misc helpers

// Shared with ValidatorClient.swift (Step 6.3b). Internal-scope so both
// drivers see the same helper without code duplication.
func sleepNs(_ ns: UInt64) {
    var ts = timespec(tv_sec: Int(ns / 1_000_000_000), tv_nsec: Int(ns % 1_000_000_000))
    _ = nanosleep(&ts, nil)
}

/// Convert a [String] into a NULL-terminated argv array of C strings the
/// posix_spawn family expects. Each cstring is allocated and freed in the
/// scope of the body closure.
// Shared with ValidatorClient.swift (Step 6.3b). Internal-scope.
func withCStringArrayCopy<R>(_ strings: [String],
                             _ body: (UnsafePointer<UnsafeMutablePointer<CChar>?>) -> R) -> R {
    let cStrings: [UnsafeMutablePointer<CChar>?] = strings.map { strdup($0) }
    defer {
        for p in cStrings { if let p { free(p) } }
    }
    var argv = cStrings
    argv.append(nil)
    return argv.withUnsafeBufferPointer { buf -> R in
        body(buf.baseAddress!)
    }
}
