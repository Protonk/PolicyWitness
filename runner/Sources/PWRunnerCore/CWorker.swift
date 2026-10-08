import Darwin
import Foundation
import CryptoKit

/*
 * CWorker — Swift driver for pw-probe-runner. Owns the host side of
 * the shared-memory ABI defined in
 * controller/tools/pw_probe_runner/pw_probe_runner_abi.h and mirrored
 * as offset constants below.
 *
 * This module is intentionally self-contained: PWRunnerService
 * drives it through CWorkerOrchestrator and never reaches in.
 *
 * Flow (mirrors tests/suites/runner_c_worker_harness/harness.c):
 *   1. shm_open + ftruncate + mmap a PWShmLayout.regionBytes region;
 *      clear FD_CLOEXEC so the child inherits the FD.
 *   2. Memset the header to zero, populate ABI identity, step_count,
 *      param_count; populate slot inputs from the request; populate
 *      param keys/values from policy.params.
 *   3. Pre-touch every page so the worker's post-apply writes never
 *      depend on lazy allocation.
 *   4. Release-store `prepared = 1`.
 *   5. Create ready + policy pipes. Mark parent-side ends FD_CLOEXEC.
 *   6. posix_spawn pw-probe-runner with FDs dup'd to 0/3/4.
 *   7. Write the policy text to the policy pipe and close.
 *   8. Read the pre-apply ready byte (deadline).
 *   9. Acquire applied, run the synchronous collection hook, release proceed;
 *      acquire acknowledgement and done with bounded sentinel polling.
 *  10. Release-store `exit_requested = 1`; waitpid with grace timer;
 *      SIGKILL fallback if the worker hangs.
 *  11. Reconstruct CWorkerStepResult per slot by reading the shm
 *      output fields once `completed == 1`.
 *
 * Errors are surfaced via CWorkerRunError; CWorkerOrchestrator maps
 * them to the runner's normalized_outcome vocabulary. Nothing in
 * this module changes classification. Host syscall observations use the
 * authoritative Codable record types documented in PWRunnerAPI.swift.
 */

// MARK: - ABI mirror

/// Wire-stable layout of the shm region. Mirrors pw_probe_runner_abi.h.
/// Layout changes in the C header must update these constants.
/// The runner_abi_layout suite compiles a C printer against
/// pw_probe_runner_abi.h at test time and asserts that every
/// constant + offset here matches the C-side `sizeof` / `offsetof`,
/// so a drift between this enum and the header fails as a test
/// rather than a runtime shm misalignment.
enum PWShmLayout {
    // BEGIN GENERATED WORKER IDENTITY (docs/generate_worker_identity.py)
    static let abiIdentityHex = "b92ab663b143748f81d4e4bf7994a33727eb19903d054dd0aa8097eed37cb802"
    static let abiIdentity: [UInt8] = [0xb9, 0x2a, 0xb6, 0x63, 0xb1, 0x43, 0x74, 0x8f, 0x81, 0xd4, 0xe4, 0xbf, 0x79, 0x94, 0xa3, 0x37, 0x27, 0xeb, 0x19, 0x90, 0x3d, 0x05, 0x4d, 0xd0, 0xaa, 0x80, 0x97, 0xee, 0xd3, 0x7c, 0xb8, 0x02]
    // END GENERATED WORKER IDENTITY

    static let abiMagic: UInt32 = 0x50574944
    static let abiIdentityBytes: Int = 32

    static let headerBytes: Int     = 96
    static let slotBytes: Int       = 8192
    static let maxSteps: Int        = 256
    static let policyBytes: Int     = 262144
    static let paramBytes: Int      = 512
    static let maxParams: Int       = 1024
    static let captureHeaderBytes: Int = 144
    static let captureBytes: Int = 1048576
    static let captureNonceBytes: Int = 16
    static let evidenceHeaderBytes: Int = 64
    static let diagnosticBytes: Int = 4096

    // Exec-attempt input bounds. argvBytes is the per-entry
    // byte cap (including the trailing NUL); maxArgv is the number of
    // entries the slot's argv table holds. The runner host validates
    // both before shm allocation.
    static let maxArgv: Int          = 16
    static let argvBytes: Int        = 128
    // Exec-attempt output bounds. Per-stream child output
    // capture; output past the buffer is truncated and tagged.
    static let childOutputBytes: Int = 1024

    static let regionBytes: Int =
        headerBytes + maxSteps * slotBytes + maxParams * paramBytes + captureHeaderBytes + captureBytes + evidenceHeaderBytes + diagnosticBytes

    // Header field offsets (in bytes from region base).
    static let abiMagicOffset: Int      = 0
    static let abiIdentityOffset: Int   = 64
    static let stepCountOffset: Int     = 4
    static let preparedOffset: Int      = 8
    static let appliedOffset: Int       = 12
    static let doneOffset: Int          = 16
    static let exitRequestedOffset: Int = 20
    static let applyRcOffset: Int       = 24
    static let paramCountOffset: Int    = 28
    static let applyErrnoOffset: Int    = 32
    static let captureRequestedOffset: Int = 36
    static let captureNonceOffset: Int = 40
    static let proceedOffset: Int = 56
    static let proceedObservedOffset: Int = 60

    static let slotsOffset: Int    = headerBytes
    static let paramsOffset: Int   = headerBytes + maxSteps * slotBytes
    static let captureOffset: Int = headerBytes + maxSteps * slotBytes + maxParams * paramBytes
    static let captureCompletedOffset: Int = 0
    static let captureStatusOffset: Int = 4
    static let captureProfileTypeOffset: Int = 8
    static let captureBytecodeLengthOffset: Int = 12
    static let captureWorkerPidOffset: Int = 16
    static let captureSourceLengthOffset: Int = 20
    static let captureParamCountOffset: Int = 24
    static let captureSourceSha256Offset: Int = 32
    static let captureParamsSha256Offset: Int = 64
    static let captureBytecodeSha256Offset: Int = 96
    static let captureRequestNonceOffset: Int = 128

    static let evidenceOffset: Int = captureOffset + captureHeaderBytes + captureBytes
    static let evidenceProgressOffset: Int = 0
    static let evidenceFailurePublishedOffset: Int = 4
    static let evidenceOperationOffset: Int = 8
    static let evidenceCodeOffset: Int = 12
    static let evidenceNativeKindOffset: Int = 16
    static let evidenceNativeResultOffset: Int = 20
    static let evidenceErrnoValOffset: Int = 24
    static let evidenceErrnoPresentOffset: Int = 28
    static let evidenceItemIndexOffset: Int = 32
    static let evidenceDetailOffset: Int = 36
    static let evidenceReadyPublishedOffset: Int = 40
    static let evidenceReadyRcOffset: Int = 44
    static let evidenceReadyErrnoOffset: Int = 48
    static let evidenceDiagnosticStateOffset: Int = 52
    static let evidenceDiagnosticLengthOffset: Int = 56

    // Slot field offsets (from the slot's base), checked against compiled C.
    static let stepIdMax: Int           = 64
    static let targetMax: Int           = 512
    static let observedPathMax: Int     = 1024
    static let errorMax: Int            = 256

    static let slotStepIdOffset: Int           = 0
    static let slotAttemptKindOffset: Int      = 64
    static let slotTargetOffset: Int           = 68
    static let slotArgvCountOffset: Int        = 580
    static let slotArgvOffset: Int             = 584
    static let slotRcOffset: Int               = 2632
    static let slotErrnoValOffset: Int         = 2636
    static let slotObservedPathOffset: Int     = 2640
    static let slotErrorOffset: Int            = 3664
    static let slotChildPidOffset: Int         = 3920
    static let slotChildExitCodeOffset: Int    = 3924
    static let slotChildTermSignalOffset: Int  = 3928
    static let slotChildStdoutOffset: Int      = 3932
    static let slotChildStderrOffset: Int      = 4956
    static let slotCompletedOffset: Int        = 5980

    // Param field offsets (from the param's base).
    static let paramKeyMax: Int    = 128
    static let paramValueMax: Int  = 384
    static let paramKeyOffset: Int   = 0
    static let paramValueOffset: Int = 128
}

/// Mirrors pw_attempt_kind_t in the C ABI. Wire-stable: NEVER renumber.
///
/// `execSpawn` is the C worker's `posix_spawn` attempt kind, dispatched
/// from wire requests with `kind="exec", action="spawn"` via
/// `CWorkerOrchestrator.mapAttemptKindOrNil`. See docs/PolicyWitness.md →
/// Attempt kinds for the wire contract.
enum PWAttemptKind: UInt32 {
    case none           = 0
    case fileOpenRead   = 1
    case fileOpenWrite  = 2
    case fileCreate     = 3
    case fileUnlink     = 4
    case fileAccess     = 5
    case machLookup     = 6
    case sysctlRead     = 7
    case execSpawn      = 8
}

// MARK: - C atomic shim binding

@_silgen_name("pw_cworker_load_acquire_u32")
private func pw_cworker_load_acquire_u32(_ p: UnsafePointer<UInt32>) -> UInt32

@_silgen_name("pw_cworker_store_release_u32")
private func pw_cworker_store_release_u32(_ p: UnsafeMutablePointer<UInt32>, _ value: UInt32)

@_silgen_name("pw_cworker_shm_open_create")
private func pw_cworker_shm_open_create(_ name: UnsafePointer<CChar>, _ mode: mode_t) -> Int32

// MARK: - Public input/output types

struct CWorkerSlotInput {
    var stepId: String
    var attemptKind: PWAttemptKind
    var target: String
    /// argv[1..N] for exec attempts. `target` is argv[0]; the C worker
    /// reads the full argv table (argv_count = 1 + args.count) out of
    /// the shm slot and passes it straight to `posix_spawn`. Capped
    /// per the ABI: count ≤ PWShmLayout.maxArgv - 1, per-arg UTF-8
    /// length ≤ PWShmLayout.argvBytes - 1 (room for the trailing NUL).
    /// Ignored for non-exec attempts.
    var args: [String]

    init(stepId: String, attemptKind: PWAttemptKind, target: String, args: [String] = []) {
        self.stepId = stepId
        self.attemptKind = attemptKind
        self.target = target
        self.args = args
    }
}

struct CWorkerParam {
    var key: String
    var value: String

    init(key: String, value: String) {
        self.key = key
        self.value = value
    }
}

struct CWorkerInput {
    static let defaultPolicyTransferTimeoutMs = 5_000
    // Internal test setting; never admitted from request JSON.
    var policyTransferTimeoutMs = CWorkerInput.defaultPolicyTransferTimeoutMs
    static let defaultSentinelTimeoutMs = 120_000
    var workerExecutablePath: String
    var policy: String
    var params: [CWorkerParam]
    /// Explicit opt-in: captured bytecode and input hashes are sensitive output.
    var captureAppliedProfile: Bool
    var captureNonce: String?
    var slots: [CWorkerSlotInput]
    var readyByteTimeoutMs: Int
    var sentinelTimeoutMs: Int
    var exitGraceMs: Int
    /// Optional test-seam routed to pw-probe-runner as
    /// `--post-apply-hang-ms <N>`. When > 0, the worker sleeps for
    /// N ms after every slot is durable but before flipping `done`;
    /// drives the host's `runner_timeout` outcome from a real
    /// specimen. Production callers pass nil.
    var postApplyHangMs: Int?
    /// Optional test-seam routed to pw-probe-runner as
    /// `--post-apply-kill-signal <N>`. When > 0, the worker raises signal N
    /// on itself after `applied` but before `done`, so the host observes a
    /// termination signal with done unset: runner_failed, without a policy
    /// cause. Production callers pass nil.
    var postApplyKillSignal: Int?
    /// Optional test-seam routed to pw-probe-runner as
    /// `--pre-ready-hang-ms <N>`. When > 0, the worker sleeps N ms
    /// after compilation/capture and before the ready byte. A sufficient
    /// sentinel budget lets it survive a closed ready pipe (SIGPIPE ignored);
    /// a shorter budget can expire before application. Production callers pass nil.
    var preReadyHangMs: Int?
    /// Optional test-seam routed to pw-probe-runner as
    /// `--exec-child-deadline-ms <N>`. Overrides the worker's
    /// default per-exec wall-clock cap (10s). Test cases that pin
    /// the deadline-fired behavior pass a short value (e.g. 500)
    /// against a long-running helper so the bounded-runtime path
    /// runs in seconds rather than tens of seconds. Production
    /// callers pass nil.
    var execChildDeadlineMs: Int?
    /// Internal test equipment: shorten the local exec plan budget independently
    /// of the host sentinel. Never populated from specimen JSON.
    var execAttemptBudgetMs: Int?

    init(workerExecutablePath: String,
                policy: String,
                params: [CWorkerParam] = [],
                slots: [CWorkerSlotInput],
                readyByteTimeoutMs: Int = 1_000,
                sentinelTimeoutMs: Int = CWorkerInput.defaultSentinelTimeoutMs,
                exitGraceMs: Int = 1_000,
                postApplyHangMs: Int? = nil,
                postApplyKillSignal: Int? = nil,
                preReadyHangMs: Int? = nil,
                execChildDeadlineMs: Int? = nil,
                execAttemptBudgetMs: Int? = nil,
                captureAppliedProfile: Bool = false,
                captureNonce: String? = nil) {
        self.workerExecutablePath = workerExecutablePath
        self.policy = policy
        self.params = params
        self.slots = slots
        self.readyByteTimeoutMs = readyByteTimeoutMs
        self.sentinelTimeoutMs = sentinelTimeoutMs
        self.exitGraceMs = exitGraceMs
        self.postApplyHangMs = postApplyHangMs
        self.postApplyKillSignal = postApplyKillSignal
        self.preReadyHangMs = preReadyHangMs
        self.execChildDeadlineMs = execChildDeadlineMs
        self.execAttemptBudgetMs = execAttemptBudgetMs
        self.captureAppliedProfile = captureAppliedProfile
        self.captureNonce = captureNonce
    }
}

struct CWorkerSlotResult {
    var stepId: String
    var rc: Int32
    var errnoVal: Int32
    var observedPath: String?
    var error: String?
    var completed: Bool
    /// Exec output fields, populated only when the slot's attempt
    /// kind was `.execSpawn`. Non-exec slots leave these nil so the
    /// orchestrator can branch on `childPid != nil` rather than
    /// inspecting kind.
    var childPid: Int32?
    var childExitCode: Int32?
    var childTermSignal: Int32?
    var childStdout: String?
    var childStderr: String?
}

struct CWorkerOutput {
    var workerPid: pid_t
    var readyByteReceived: Bool
    var applied: Bool
    /// The status word, published by applied/done. -1 also represents parameter
    /// setup and compilation failures; without publication it is not a result.
    var applyRC: Int32
    /// Meaningful native errno only on a failed apply published by done.
    /// Zero alone distinguishes neither success nor absence of a call.
    var applyErrno: Int32
    var done: Bool
    /// Derived convenience for existing driver tests: a SIGKILL request was made, regardless
    /// of its result. Derived, not an independent authoritative observation.
    var sentSigkill: Bool { terminationRequest?.signal == SIGKILL }
    var exitCode: Int32?     // nil unless successfully reaped with exit
    var termSignal: Int32?   // nil unless successfully reaped with signal
    var slots: [CWorkerSlotResult]
    var profileCapture: AppliedProfileCapture? = nil
    /// Host-only fields, forwarded to runner_subprocess without reinterpretation.
    /// Defaults support constructed test inputs, not live observations.
    /// See PWRunnerSubprocess for JSON paths, types and absence semantics.
    var pollStopReason: String? = nil
    var exitRequested: Bool? = nil
    var terminationRequest: PWRunnerTerminationRequest? = nil
    var reaped: Bool? = nil
    var waitErrors: [PWRunnerWaitError]? = nil
    var workerEvidence: PWWorkerEvidence? = nil
    var policyTransferTimeout: PWWorkerPolicyTransferTimeout? = nil
    var policyTransferError: PWWorkerPolicyTransferError? = nil
    var hookInvoked: Bool = false
    var proceedSet: Bool = false
    var proceedObserved: Bool = false
    var proceedOwnershipEstablished: Bool = false
    var orderingProtocolViolations: [String] = []
    /// Direct host observations for the disposition record: why exit was
    /// requested (recorded at the exit-request store), how the exit-grace wait
    /// ended, and whether the final reads followed a confirmed reap. Nil only
    /// for constructed test inputs.
    var cleanupTrigger: String? = nil
    var graceEnd: String? = nil
    var collectionBasis: String? = nil
}


// Only publication words gate non-atomic payload reads. Progress itself is atomic.
// Unknown codes remain numbers; structural bounds, not recognition, gate validity.
func workerIdentityMatches(_ base: UnsafePointer<UInt8>) -> Bool {
    UInt32(bitPattern: readI32(base, offset: PWShmLayout.abiMagicOffset)) == PWShmLayout.abiMagic
        && UnsafeBufferPointer(start: base.advanced(by: PWShmLayout.abiIdentityOffset),
                               count: PWShmLayout.abiIdentityBytes).elementsEqual(PWShmLayout.abiIdentity)
}

func decodeWorkerEvidence(_ base: UnsafePointer<UInt8>) -> PWWorkerEvidence? {
    guard workerIdentityMatches(base) else { return nil }
    let e = base.advanced(by: PWShmLayout.evidenceOffset)
    func u(_ offset: Int) -> UInt32 { UInt32(bitPattern: readI32(e, offset: offset)) }
    let raw = loadAcquire(e, offset: PWShmLayout.evidenceProgressOffset)
    let item = raw & 0xfffff
    let progress = raw == 0 ? nil : PWWorkerProgress(raw: raw, operation: raw >> 24,
        phase: (raw >> 20) & 15, index: item == 0 ? nil : item - 1)
    let published = loadAcquire(e, offset: PWShmLayout.evidenceFailurePublishedOffset)
    var state = published == 0 ? "absent" : published == 2 ? "incomplete" : "invalid"
    var failure: PWWorkerFailure? = nil
    if published == 1 && u(PWShmLayout.evidenceErrnoPresentOffset) <= 1
        && (u(PWShmLayout.evidenceNativeKindOffset) != 2
            || readI32(e, offset: PWShmLayout.evidenceNativeResultOffset) == 0) {
        let kind = u(PWShmLayout.evidenceNativeKindOffset)
        let index = u(PWShmLayout.evidenceItemIndexOffset)
        state = "published"
        failure = PWWorkerFailure(operation: u(PWShmLayout.evidenceOperationOffset),
            code: u(PWShmLayout.evidenceCodeOffset), native_kind: kind,
            native_result: kind == 0 ? nil : readI32(e, offset: PWShmLayout.evidenceNativeResultOffset),
            errno: u(PWShmLayout.evidenceErrnoPresentOffset) == 1 ? readI32(e, offset: PWShmLayout.evidenceErrnoValOffset) : nil,
            index: index == UInt32.max ? nil : index, detail: u(PWShmLayout.evidenceDetailOffset))
    }
    var readiness: PWWorkerReadiness? = nil
    if loadAcquire(e, offset: PWShmLayout.evidenceReadyPublishedOffset) == 1 {
        let rc = readI32(e, offset: PWShmLayout.evidenceReadyRcOffset)
        readiness = PWWorkerReadiness(rc: rc, errno: rc == 0 ? nil : readI32(e, offset: PWShmLayout.evidenceReadyErrnoOffset))
    }
    let ds = loadAcquire(e, offset: PWShmLayout.evidenceDiagnosticStateOffset)
    var diagnostic = PWWorkerDiagnostic(state: ds,
        status: ds == 0 ? "absent" : ds == 3 ? "incomplete" : "unknown")
    if ds == 1 || ds == 2 {
        let length = u(PWShmLayout.evidenceDiagnosticLengthOffset)
        if length < PWShmLayout.diagnosticBytes
            && e[PWShmLayout.evidenceHeaderBytes + Int(length)] == 0 {
            diagnostic.status = ds == 1 ? "complete" : "truncated"
            diagnostic.length = length
            diagnostic.text = String(decoding: UnsafeBufferPointer(start:
                e.advanced(by: PWShmLayout.evidenceHeaderBytes), count: Int(length)), as: UTF8.self)
        } else { diagnostic.status = "invalid" }
    }
    return PWWorkerEvidence(abi_identity: PWShmLayout.abiIdentityHex, progress: progress,
        failure_publication: published, failure_state: state, failure: failure,
        readiness: readiness, diagnostic: diagnostic)
}


func sha256Hex(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}

/// Same specified framing as the C worker, independently implemented. Sorting
/// fixed-size pair digests avoids depending on Swift/Python Unicode sort order.
func consumedParamsDigest(_ params: [CWorkerParam]) -> String {
    func le(_ n: Int) -> Data {
        var word = UInt32(n).littleEndian
        return withUnsafeBytes(of: &word) { Data($0) }
    }
    let pairs = params.map { p -> Data in
        let k = Data(p.key.utf8), v = Data(p.value.utf8)
        return Data(SHA256.hash(data: le(k.count) + k + le(v.count) + v))
    }.sorted { $0.lexicographicallyPrecedes($1) }
    return sha256Hex(pairs.reduce(le(params.count), +))
}

/// Called only for an opted-in run. A checksum, PID or actual-consumed-input
/// mismatch refuses publication instead of falling back to source-only identity.
func captureNonceBytes(_ nonce: String?) -> Data? {
    guard let nonce, nonce.utf8.count == 32,
        nonce.utf8.allSatisfy({ (48...57).contains($0) || (97...102).contains($0) }) else { return nil }
    let chars = Array(nonce)
    return Data(stride(from: 0, to: chars.count, by: 2).map { UInt8(String(chars[$0...($0 + 1)]), radix: 16)! })
}

func decodeProfileCapture(_ base: UnsafePointer<UInt8>, workerPid: pid_t,
    applied: Bool, applyRC: Int32, done: Bool, exitCode: Int32?, termSignal: Int32?,
    source: String, params: [CWorkerParam], nonce: String?) -> AppliedProfileCapture {
    func unavailable(_ reason: String) -> AppliedProfileCapture {
        AppliedProfileCapture(status: "unavailable", reason: reason, worker_pid: Int(workerPid))
    }
    guard applied && applyRC == 0 else { return unavailable("successful_application_unconfirmed") }
    guard done && exitCode == 0 && termSignal == nil else { return unavailable("worker_not_complete") }
    guard loadAcquire(base, offset: PWShmLayout.captureCompletedOffset) == 1 else {
        return unavailable("capture_not_complete")
    }
    func word(_ offset: Int) -> Int { Int(UInt32(bitPattern: readI32(base, offset: offset))) }
    func digest(_ offset: Int) -> String {
        Data(bytes: base.advanced(by: offset), count: 32).map { String(format: "%02x", $0) }.joined()
    }
    guard word(PWShmLayout.captureStatusOffset) == 1 else { return unavailable("worker_capture_refused") }
    guard word(PWShmLayout.captureWorkerPidOffset) == Int(workerPid) else { return unavailable("capture_worker_mismatch") }
    guard let nonceBytes = captureNonceBytes(nonce),
        Data(bytes: base.advanced(by: PWShmLayout.captureRequestNonceOffset), count: PWShmLayout.captureNonceBytes) == nonceBytes else {
        return unavailable("capture_nonce_mismatch")
    }
    let length = word(PWShmLayout.captureBytecodeLengthOffset)
    guard word(PWShmLayout.captureProfileTypeOffset) == 0 && length > 0 && length <= PWShmLayout.captureBytes else {
        return unavailable("capture_extent_or_type_invalid")
    }
    let bytes = Data(bytes: base.advanced(by: PWShmLayout.captureHeaderBytes), count: length)
    guard sha256Hex(bytes) == digest(PWShmLayout.captureBytecodeSha256Offset) else {
        return unavailable("capture_bytecode_digest_mismatch")
    }
    guard word(PWShmLayout.captureSourceLengthOffset) == source.utf8.count
        && digest(PWShmLayout.captureSourceSha256Offset) == sha256Hex(Data(source.utf8))
        && word(PWShmLayout.captureParamCountOffset) == params.count
        && digest(PWShmLayout.captureParamsSha256Offset) == consumedParamsDigest(params) else {
        return unavailable("capture_consumed_input_mismatch")
    }
    return AppliedProfileCapture(status: "captured", worker_pid: Int(workerPid), request_nonce: nonce, profile_type: 0,
        bytecode_length: length, bytecode_sha256: sha256Hex(bytes), bytecode_b64: bytes.base64EncodedString(),
        source_sha256: digest(PWShmLayout.captureSourceSha256Offset), source_length: source.utf8.count,
        params_sha256: digest(PWShmLayout.captureParamsSha256Offset), parameter_count: params.count)
}

enum CWorkerRunError: Error, CustomStringConvertible {
    case captureNonceInvalid
    case admissionFailed(PWRunnerAdmissionFailure)
    case execTargetNotAbsolute(stepId: String, target: String)
    case shmSetupFailed(String)
    case pipeFailed(String)
    case spawnFailed(String)
    case policyWriteFailed(String)
    case policyTransferTimedOut(String)

    /// Refusals decided from the request alone, before any shm, pipe or process
    /// work: nothing ran and nothing was observed, so the reply carries the
    /// refusal and no steps. Echoing the plan would repeat the strings a
    /// capacity refusal rejected, and 256 refused queries can outgrow the
    /// reply cap on their own.
    var isPreSpawnRefusal: Bool {
        switch self {
        case .captureNonceInvalid, .admissionFailed, .execTargetNotAbsolute: return true
        case .shmSetupFailed, .pipeFailed, .spawnFailed, .policyWriteFailed, .policyTransferTimedOut: return false
        }
    }

    var description: String {
        switch self {
        case .captureNonceInvalid:
            return "capture_applied_profile requires a fresh 32-character lowercase hex capture_nonce"
        case .admissionFailed(let record):
            return "\(record.field) has \(record.actual) \(record.unit); maximum \(record.maximum)"
        case .execTargetNotAbsolute(let stepId, let target):
            return "slot \(stepId) exec target must be an absolute path (got \(target.isEmpty ? "<empty>" : target))"
        case .shmSetupFailed(let why): return "shm setup: \(why)"
        case .pipeFailed(let why):     return "pipe: \(why)"
        case .spawnFailed(let why):    return "posix_spawn: \(why)"
        case .policyTransferTimedOut(let why): return "policy transfer deadline: \(why)"
        case .policyWriteFailed(let why): return "write(policy_pipe): \(why)"
        }
    }
}

enum CWorkerRunResult {
    case success(CWorkerOutput)
    case failure(CWorkerRunError, CWorkerOutput? = nil)
}

/// One string's admission and safe echo policy. Host-only metadata may contain
/// NUL; native C strings must reject it rather than silently use a prefix.
struct AdmissionStringRule {
    let field: String
    let maximum: Int
    var requiresCString: Bool = false

    func failure(_ value: String?) -> PWRunnerAdmissionFailure? {
        guard let value else { return nil }
        if value.utf8.count > maximum {
            return PWRunnerAdmissionFailure(field: field, actual: value.utf8.count,
                maximum: maximum, unit: "utf8_bytes")
        }
        if requiresCString {
            let nuls = value.utf8.filter { $0 == 0 }.count
            if nuls > 0 {
                return PWRunnerAdmissionFailure(field: field, actual: nuls, maximum: 0, unit: "nul_bytes")
            }
        }
        return nil
    }

    func safeEcho(_ value: String?) -> String? {
        failure(value) == nil ? value : nil
    }
}

let stepIdAdmission = AdmissionStringRule(field: "step_id", maximum: PWShmLayout.stepIdMax - 1, requiresCString: true)
let parameterKeyAdmission = AdmissionStringRule(field: "key", maximum: PWShmLayout.paramKeyMax - 1, requiresCString: true)

/// Checks local to the ABI writer. The C reader retains its defensive guard.
func workerAdmissionFailure(_ input: CWorkerInput) -> PWRunnerAdmissionFailure? {
    func check(_ field: String, _ actual: Int, _ maximum: Int, _ unit: String,
               step: String? = nil, position: Int? = nil, key: String? = nil, index: Int? = nil) -> PWRunnerAdmissionFailure? {
        guard actual > maximum else { return nil }
        return PWRunnerAdmissionFailure(field: field, actual: actual, maximum: maximum,
            unit: unit, step_id: step, step_index: position, parameter_key: key, index: index)
    }
    func string(_ field: String, _ value: String, _ maximum: Int,
                step: String? = nil, position: Int? = nil, key: String? = nil, index: Int? = nil) -> PWRunnerAdmissionFailure? {
        guard var r = AdmissionStringRule(field: field, maximum: maximum, requiresCString: true).failure(value) else { return nil }
        r.step_id = stepIdAdmission.safeEcho(step)
        r.step_index = position
        r.parameter_key = parameterKeyAdmission.safeEcho(key)
        r.index = index
        return r
    }
    if let r = string("policy.sbpl_source", input.policy, PWShmLayout.policyBytes - 1) { return r }
    if let r = check("probe_plan", input.slots.count, PWShmLayout.maxSteps, "items") { return r }
    if let r = check("policy.params", input.params.count, PWShmLayout.maxParams, "items") { return r }
    for (position, slot) in input.slots.enumerated() {
        // A refused step ID or parameter key is identified by position or by
        // field and byte count, never echoed: the record must stay small.
        if let r = string("step_id", slot.stepId, stepIdAdmission.maximum, position: position) { return r }
        if let r = string("target", slot.target, PWShmLayout.targetMax - 1, step: slot.stepId, position: position) { return r }
        if slot.attemptKind == .execSpawn {
            if let r = check("args", slot.args.count, PWShmLayout.maxArgv - 1, "items", step: slot.stepId, position: position) { return r }
            for (i, arg) in slot.args.enumerated() {
                if let r = string("args", arg, PWShmLayout.argvBytes - 1, step: slot.stepId, position: position, index: i) { return r }
            }
        }
    }
    for p in input.params {
        if let r = string("key", p.key, parameterKeyAdmission.maximum) { return r }
        if let r = string("value", p.value, PWShmLayout.paramValueMax - 1, key: p.key) { return r }
    }
    return nil
}

// MARK: - Driver

/// Callback invoked once the worker's `applied` sentinel flips, before
/// the driver starts polling `done`. The callback receives the worker
/// PID — that's the moment the validator child (or any other observer
/// that wants to inspect the sandboxed worker) can be spawned. The
/// callback runs synchronously; the driver does NOT poll `done` while
/// it's executing. Hook time is outside the host sentinel budget, but the
/// worker's monotonic proceed budget continues independently. Returning closes
/// collection and releases attempts, including after validator failure.
typealias CWorkerPostAppliedHook = (pid_t) -> Void

func runCWorker(_ input: CWorkerInput,
                       postApplied: CWorkerPostAppliedHook? = nil) -> CWorkerRunResult {
    runCWorker(input, processCalls: ChildProcessCalls(), postApplied: postApplied)
}

/// Internal OS-call boundary for driver tests, never selected by request JSON.
/// Production always uses Darwin. Tests can fail one real boundary without
/// manufacturing CWorkerOutput or a normalized outcome.
struct ChildProcessCalls {
    var wait: (pid_t, UnsafeMutablePointer<Int32>, Int32) -> pid_t = {
        Darwin.waitpid($0, $1, $2)
    }
    var kill: (pid_t, Int32) -> Int32 = { Darwin.kill($0, $1) }
}

enum ChildWaitObservation { case pending, reaped, failed }

/// One child's host observations. Status is assigned only by a successful reap.
/// Across polling/grace/final reap, allow two EINTR retries total. A terminal
/// wait error ends that phase; ECHILD ends all waits/kills because ownership is
/// lost. At most five failed calls can be recorded (two recovered interruptions
/// plus one terminal error in each of three phases). No errors are dropped.
/// Grace retains its existing budget. A failed kill permits only a nonblocking
/// final wait. After successful kill the existing blocking wait remains: retry
/// limits bound failed calls, not kernel exit latency or the whole lifecycle.
/// Unconfirmed disposition may leave a live child or zombie; no global reaper
/// or new lifecycle timeout is introduced here.
struct ChildProcessState {
    let pid: pid_t
    let calls: ChildProcessCalls
    var status: Int32? = nil
    var terminationRequest: PWRunnerTerminationRequest? = nil
    var waitErrors: [PWRunnerWaitError] = []
    var childUnavailable = false
    private var interruptRetries = 2

    init(pid: pid_t, calls: ChildProcessCalls) {
        self.pid = pid
        self.calls = calls
    }

    mutating func wait(options: Int32, phase: String) -> ChildWaitObservation {
        while true {
            var candidate: Int32 = 0
            let rc = calls.wait(pid, &candidate, options)
            let savedErrno = rc == -1 ? errno : nil
            if rc == pid {
                status = candidate
                return .reaped
            }
            if rc == 0 { return .pending }
            if let error = savedErrno {
                waitErrors.append(PWRunnerWaitError(phase: phase, rc: rc, errno: error))
                if error == ECHILD { childUnavailable = true }
                if error == EINTR && interruptRetries > 0 {
                    interruptRetries -= 1
                    continue
                }
            }
            return .failed
        }
    }

    mutating func terminate() {
        guard status == nil && !childUnavailable else { return }
        let rc = calls.kill(pid, SIGKILL)
        let savedErrno = rc == -1 ? errno : nil
        terminationRequest = PWRunnerTerminationRequest(signal: SIGKILL, rc: rc, errno: savedErrno)
        _ = wait(options: rc == 0 ? 0 : WNOHANG, phase: "after_termination")
    }
}

func runCWorker(_ input: CWorkerInput, processCalls: ChildProcessCalls,
                postApplied: CWorkerPostAppliedHook? = nil) -> CWorkerRunResult {
    if input.captureAppliedProfile && captureNonceBytes(input.captureNonce) == nil {
        return .failure(.captureNonceInvalid)
    }
    // All capacity refusals use the same host-owned record, before shm/spawn.
    if let failure = workerAdmissionFailure(input) { return .failure(.admissionFailed(failure)) }
    for slot in input.slots where slot.attemptKind == .execSpawn && !slot.target.hasPrefix("/") {
        return .failure(.execTargetNotAbsolute(stepId: slot.stepId, target: slot.target))
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

    // Zero the region. The worker checks ABI identity + prepared so a
    // leftover non-zero from a recycled mapping wouldn't be confusing,
    // but zeroing is cheap and removes a class of "did I clear it?"
    // questions.
    memset(base, 0, PWShmLayout.regionBytes)

    // ---- Populate header.
    let rawBase = base.assumingMemoryBound(to: UInt8.self)
    writeU32(rawBase, offset: PWShmLayout.abiMagicOffset, PWShmLayout.abiMagic)
    PWShmLayout.abiIdentity.withUnsafeBytes { identity in
        rawBase.advanced(by: PWShmLayout.abiIdentityOffset).update(from: identity.bindMemory(to: UInt8.self).baseAddress!,
                                                                 count: PWShmLayout.abiIdentityBytes)
    }
    writeU32(rawBase, offset: PWShmLayout.stepCountOffset, UInt32(input.slots.count))
    writeU32(rawBase, offset: PWShmLayout.paramCountOffset, UInt32(input.params.count))
    writeU32(rawBase, offset: PWShmLayout.captureRequestedOffset, input.captureAppliedProfile ? 1 : 0)
    if input.captureAppliedProfile, let nonce = captureNonceBytes(input.captureNonce) {
        nonce.copyBytes(to: rawBase.advanced(by: PWShmLayout.captureNonceOffset), count: nonce.count)
    }

    // ---- Populate slots.
    for (i, slot) in input.slots.enumerated() {
        let slotBase = rawBase.advanced(by: PWShmLayout.slotsOffset + i * PWShmLayout.slotBytes)
        writeString(slotBase, offset: PWShmLayout.slotStepIdOffset,
                    value: slot.stepId, max: PWShmLayout.stepIdMax)
        writeU32(slotBase, offset: PWShmLayout.slotAttemptKindOffset,
                 slot.attemptKind.rawValue)
        writeString(slotBase, offset: PWShmLayout.slotTargetOffset,
                    value: slot.target, max: PWShmLayout.targetMax)
        // Exec slots: argv[0] is target; args occupy argv[1..argv_count-1].
        // Other slots leave argv_count = 0 (host memset already zeroed
        // the table) so the worker's EXEC_SPAWN case sees a clean
        // argv_count == 0 → 1 fallback for kinds that aren't dispatched
        // here.
        if slot.attemptKind == .execSpawn {
            let argvCount = 1 + slot.args.count
            writeU32(slotBase, offset: PWShmLayout.slotArgvCountOffset, UInt32(argvCount))
            // Write argv[0] = target.
            let argvBase = slotBase.advanced(by: PWShmLayout.slotArgvOffset)
            writeString(argvBase, offset: 0,
                        value: slot.target, max: PWShmLayout.argvBytes)
            // Write argv[1..N] = args.
            for (j, arg) in slot.args.enumerated() {
                writeString(argvBase,
                            offset: (j + 1) * PWShmLayout.argvBytes,
                            value: arg, max: PWShmLayout.argvBytes)
            }
        }
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
    // FD-scoped SIGPIPE suppression leaves process-wide signal handling intact.
    guard fcntl(policyPipe[1], F_SETNOSIGPIPE, 1) == 0 else {
        let error = errno
        close(readyPipe[0]); close(readyPipe[1]); close(policyPipe[0]); close(policyPipe[1])
        return .failure(.pipeFailed("F_SETNOSIGPIPE: \(String(cString: strerror(error)))"))
    }
    let policyFlags = fcntl(policyPipe[1], F_GETFL, 0)
    guard policyFlags >= 0, fcntl(policyPipe[1], F_SETFL, policyFlags | O_NONBLOCK) == 0 else {
        let error = errno
        for fd in readyPipe + policyPipe { close(fd) }
        return .failure(.pipeFailed("policy O_NONBLOCK: \(String(cString: strerror(error)))"))
    }
    // Original pipe descriptors close on exec; only the explicit dup2 targets
    // survive. An extra policy read end would keep a closed stdin pipe alive.
    for fd in readyPipe + policyPipe {
        guard fcntl(fd, F_SETFD, FD_CLOEXEC) == 0 else {
            let error = errno
            for opened in readyPipe + policyPipe { close(opened) }
            return .failure(.pipeFailed("FD_CLOEXEC: \(String(cString: strerror(error)))"))
        }
    }

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
    if let killSig = input.postApplyKillSignal, killSig > 0 {
        argv.append("--post-apply-kill-signal")
        argv.append(String(killSig))
    }
    if let preReadyMs = input.preReadyHangMs, preReadyMs > 0 {
        argv.append("--pre-ready-hang-ms")
        argv.append(String(preReadyMs))
    }
    if let deadlineMs = input.execChildDeadlineMs, deadlineMs > 0 {
        argv.append("--exec-child-deadline-ms")
        argv.append(String(deadlineMs))
    }
    if let budgetMs = input.execAttemptBudgetMs {
        argv.append("--exec-attempt-budget-ms")
        argv.append(String(budgetMs))
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
    let transferDeadline = MonotonicDeadline(milliseconds: input.policyTransferTimeoutMs)
    // Close parent-side ends that the child now owns.
    close(policyPipe[0])
    close(readyPipe[1])
    var process = ChildProcessState(pid: pid, calls: processCalls)

    // ---- Deliver under one deadline established immediately after spawn.
    let policyBytes = Array(input.policy.utf8)
    let transfer = writePolicy(policyBytes, fd: policyPipe[1], deadline: transferDeadline)
    close(policyPipe[1])
    var transferError: PWWorkerPolicyTransferError? = nil
    var transferTimeout: PWWorkerPolicyTransferTimeout? = nil
    var transferFailure: CWorkerRunError? = nil
    switch transfer.stop {
    case .complete: break
    case .timeout(let elapsed):
        transferTimeout = PWWorkerPolicyTransferTimeout(budget_ms: input.policyTransferTimeoutMs,
            elapsed_ms: elapsed, bytes_written: transfer.written, bytes_expected: policyBytes.count)
        transferFailure = .policyTransferTimedOut("exceeded \(input.policyTransferTimeoutMs) ms; wrote \(transfer.written) of \(policyBytes.count) bytes")
    case .writeError(let error):
        transferError = PWWorkerPolicyTransferError(errno: error, bytes_written: transfer.written,
            bytes_expected: policyBytes.count)
        transferFailure = .policyWriteFailed("errno=\(error) (\(String(cString: strerror(error)))); wrote \(transfer.written) of \(policyBytes.count) bytes")
    case .failed(let diagnostic):
        transferFailure = .policyWriteFailed(diagnostic + "; wrote \(transfer.written) of \(policyBytes.count) bytes")
    }

    // ---- Read pre-apply ready byte.
    var readyByte: UInt8 = 0
    var readyByteReceived = false
    if transferFailure == nil {
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

    // ---- Poll applied, fire postApplied hook, then poll done. Also
    // watch for the worker exiting WITHOUT flipping `done` (a sandbox
    // kill mid-probe, a crash, or a pre-apply death): there is nothing
    // left to wait for, so reap and stop immediately instead of spinning
    // the full sentinel deadline over a corpse.
    var sawApplied = false
    var sawDone = false
    var hookFired = false
    var proceedSet = false
    var ownershipUnbroken = true
    var acknowledgedWhileOwned = false
    var orderingFaults: [String] = []
    func observeAcknowledgement() {
        if ownershipUnbroken && loadAcquire(rawBase, offset: PWShmLayout.proceedObservedOffset) == 1 {
            acknowledgedWhileOwned = true
        }
    }
    func checkPrematurePublication() {
        let ack = loadAcquire(rawBase, offset: PWShmLayout.proceedObservedOffset)
        let progress = loadAcquire(rawBase.advanced(by: PWShmLayout.evidenceOffset),
                                   offset: PWShmLayout.evidenceProgressOffset)
        let completed = input.slots.indices.contains { i in
            loadAcquire(rawBase.advanced(by: PWShmLayout.slotsOffset + i * PWShmLayout.slotBytes),
                        offset: PWShmLayout.slotCompletedOffset) == 1
        }
        if ack != 0 { orderingFaults.append("acknowledgement_before_release") }
        if completed || progress >> 24 == 9 { orderingFaults.append("attempt_before_release") }
    }
    var pollStopReason = transferFailure == nil ? "sentinel_deadline" : (transferTimeout == nil ? "policy_write_error" : "policy_transfer_deadline")
    if transferFailure == nil {
        let pollIntervalNs: UInt64 = 2_000_000   // 2 ms
        let deadlineIters = max(1, input.sentinelTimeoutMs * 1_000_000 / Int(pollIntervalNs))
        // Probe for a dead worker only every ~50ms, not every 2ms: a
        // waitpid syscall in the hot loop measurably inflates the
        // effective sentinel deadline (syscall cost + short-sleep timer
        // coalescing), so throttle it. 50ms detection latency is
        // negligible against the seconds-scale sentinel and is far better
        // than spinning the whole deadline over a corpse.
        let exitCheckEvery = max(1, 50_000_000 / Int(pollIntervalNs))   // 25 iters
        polling: for iter in 0..<deadlineIters {
            if !sawApplied && loadAcquire(rawBase, offset: PWShmLayout.appliedOffset) == 1 {
                sawApplied = true
            }
            // Fire the post-applied hook the first iteration after we
            // observe `applied`. The worker is now under the policy;
            // anything the hook does sees the sandboxed worker_pid.
            // We fire BEFORE checking `done` so a short-running worker
            // can't finish before the hook starts.
            if sawApplied && !hookFired
                && readI32(rawBase, offset: PWShmLayout.applyRcOffset) == 0
                && workerIdentityMatches(rawBase) {
                checkPrematurePublication()
                hookFired = true
                if let hook = postApplied { hook(pid) }
                // Synchronous collection is closed. No record can enter this
                // run's predictions after the release store, including on error.
                checkPrematurePublication()
                storeRelease(rawBase, offset: PWShmLayout.proceedOffset, 1)
                proceedSet = true
            }
            observeAcknowledgement()
            if loadAcquire(rawBase, offset: PWShmLayout.doneOffset) != 0 {
                sawDone = true
                pollStopReason = "done"
                break
            }
            // Normal completion flips `done` (checked above) and then the
            // worker spins until exit_requested, so it is still alive at
            // this point. If waitpid reaps it here, it died without
            // flipping done — there is nothing more to poll for; capture
            // its status and let the classifier read the signal/exit as
            // the source of truth.
            if iter % exitCheckEvery == 0 {
                switch process.wait(options: WNOHANG, phase: "poll") {
                case .reaped:
                    pollStopReason = "child_reaped"
                    break polling
                case .failed:
                    ownershipUnbroken = false
                    pollStopReason = "wait_error"
                    break polling
                case .pending:
                    break
                }
            }
            sleepNs(pollIntervalNs)
        }
    }

    // ---- Request worker exit (a no-op if it already died on its own).
    storeRelease(rawBase, offset: PWShmLayout.exitRequestedOffset, 1)
    // The cleanup trigger is recorded here, at the store, as the reason polling
    // stopped; it is a host fact for the disposition record, not reconstructed
    // from a final exit code.
    let cleanupTrigger = PWDisposition.triggerForStop[pollStopReason] ?? pollStopReason

    // ---- Reap (grace + SIGKILL fallback), unless the poll loop already
    // reaped a worker that exited without flipping `done`. How the grace wait
    // ended is recorded directly: a reap, a wait error, or exhaustion (which
    // is followed by the termination request), never inferred later.
    var graceEnd = "not_entered"
    if process.status == nil && !process.childUnavailable {
        let pollIntervalNs: UInt64 = 10_000_000
        let graceIters = max(1, input.exitGraceMs * 1_000_000 / Int(pollIntervalNs))
        graceEnd = "exhausted"
        grace: for _ in 0..<graceIters {
            observeAcknowledgement()
            switch process.wait(options: WNOHANG, phase: "exit_grace") {
            case .reaped:
                graceEnd = "reaped_during_grace"
                break grace
            case .failed:
                graceEnd = "wait_error"
                ownershipUnbroken = false
                break grace
            case .pending:
                sleepNs(pollIntervalNs)
            }
        }
        observeAcknowledgement()
        let errorsBeforeTermination = process.waitErrors.count
        process.terminate()
        if process.waitErrors.count > errorsBeforeTermination { ownershipUnbroken = false }
    }
    // Collection basis: whether every read below follows a successful reap. A
    // reap observed later cannot upgrade it.
    let collectionBasis = process.status != nil ? "after_confirmed_reap" : "execution_may_continue"

    // Final acquire snapshot after cleanup. Publications are immutable, so this
    // also safely retains results if cleanup failed and the child is still alive.
    // Never rewrite pollStopReason or run the validator against a reaped child.
    sawApplied = loadAcquire(rawBase, offset: PWShmLayout.appliedOffset) == 1
    sawDone = loadAcquire(rawBase, offset: PWShmLayout.doneOffset) == 1
    let finalProceedObserved = loadAcquire(rawBase, offset: PWShmLayout.proceedObservedOffset) == 1
    let applyRC = (sawApplied || sawDone) ? readI32(rawBase, offset: PWShmLayout.applyRcOffset) : 0
    let applyErrno = (sawApplied || sawDone) ? readI32(rawBase, offset: PWShmLayout.applyErrnoOffset) : 0

    // Slot payloads are immutable after release publication. Read only confirmed slots.
    var slotResults: [CWorkerSlotResult] = []
    slotResults.reserveCapacity(input.slots.count)
    for i in 0..<input.slots.count {
        let slotBase = rawBase.advanced(by: PWShmLayout.slotsOffset + i * PWShmLayout.slotBytes)
        let completed = loadAcquire(slotBase, offset: PWShmLayout.slotCompletedOffset)
        if completed != 1 {
            slotResults.append(CWorkerSlotResult(stepId: input.slots[i].stepId,
                rc: 0, errnoVal: 0, completed: false))
            continue
        }
        let stepId = readString(slotBase, offset: PWShmLayout.slotStepIdOffset,
                                max: PWShmLayout.stepIdMax)
        let rc = readI32(slotBase, offset: PWShmLayout.slotRcOffset)
        let errnoVal = readI32(slotBase, offset: PWShmLayout.slotErrnoValOffset)
        let observedRaw = readString(slotBase, offset: PWShmLayout.slotObservedPathOffset,
                                     max: PWShmLayout.observedPathMax)
        let errorRaw = readString(slotBase, offset: PWShmLayout.slotErrorOffset,
                                  max: PWShmLayout.errorMax)

        // Exec output fields. Only read when the input slot was exec
        // (we trust input.slots[i].attemptKind here because the host
        // wrote the slot's attempt_kind field with that value;
        // re-reading the shm field would just round-trip the same
        // value). Non-exec slots leave these nil so the orchestrator's
        // `childPid != nil` branch works.
        let isExec = input.slots[i].attemptKind == .execSpawn
        let childPid:        Int32? = isExec ? readI32(slotBase, offset: PWShmLayout.slotChildPidOffset)        : nil
        let childExitCode:   Int32? = isExec ? readI32(slotBase, offset: PWShmLayout.slotChildExitCodeOffset)   : nil
        let childTermSignal: Int32? = isExec ? readI32(slotBase, offset: PWShmLayout.slotChildTermSignalOffset) : nil
        let childStdout: String? = isExec ? readString(slotBase, offset: PWShmLayout.slotChildStdoutOffset,
                                                       max: PWShmLayout.childOutputBytes) : nil
        let childStderr: String? = isExec ? readString(slotBase, offset: PWShmLayout.slotChildStderrOffset,
                                                       max: PWShmLayout.childOutputBytes) : nil

        slotResults.append(CWorkerSlotResult(
            stepId: stepId,
            rc: rc,
            errnoVal: errnoVal,
            observedPath: observedRaw.isEmpty ? nil : observedRaw,
            error: errorRaw.isEmpty ? nil : errorRaw,
            completed: completed != 0,
            childPid: childPid,
            childExitCode: childExitCode,
            childTermSignal: childTermSignal,
            childStdout: (childStdout?.isEmpty ?? true) ? nil : childStdout,
            childStderr: (childStderr?.isEmpty ?? true) ? nil : childStderr
        ))
    }

    let exitCode: Int32?
    let termSignal: Int32?
    if let status = process.status, (status & 0x7f) == 0 {
        exitCode = (status >> 8) & 0xff
        termSignal = nil
    } else if let status = process.status, (((status & 0x7f) + 1) >> 1 > 0) {
        exitCode = nil
        termSignal = status & 0x7f
    } else {
        exitCode = nil
        termSignal = nil
    }

    let output = CWorkerOutput(
        workerPid: pid,
        readyByteReceived: readyByteReceived,
        applied: sawApplied,
        applyRC: applyRC,
        applyErrno: applyErrno,
        done: sawDone,
        exitCode: exitCode,
        termSignal: termSignal,
        slots: slotResults,
        profileCapture: input.captureAppliedProfile ? decodeProfileCapture(
            rawBase.advanced(by: PWShmLayout.captureOffset), workerPid: pid,
            applied: sawApplied, applyRC: applyRC, done: sawDone,
            exitCode: exitCode, termSignal: termSignal, source: input.policy, params: input.params,
            nonce: input.captureNonce) : nil,
        pollStopReason: pollStopReason,
        exitRequested: true,
        terminationRequest: process.terminationRequest,
        reaped: process.status != nil,
        waitErrors: process.waitErrors,
        workerEvidence: decodeWorkerEvidence(rawBase),
        policyTransferTimeout: transferTimeout,
        policyTransferError: transferError,
        hookInvoked: hookFired,
        proceedSet: proceedSet,
        proceedObserved: finalProceedObserved,
        proceedOwnershipEstablished: finalProceedObserved && (acknowledgedWhileOwned || ownershipUnbroken),
        orderingProtocolViolations: Array(Set(orderingFaults)).sorted(),
        cleanupTrigger: cleanupTrigger,
        graceEnd: graceEnd,
        collectionBasis: collectionBasis
    )
    if let failure = transferFailure {
        return .failure(failure, output)
    }
    return .success(output)
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

// Shared with ValidatorClient.swift. Internal-scope so both
// drivers see the same helper without code duplication.
func sleepNs(_ ns: UInt64) {
    var ts = timespec(tv_sec: Int(ns / 1_000_000_000), tv_nsec: Int(ns % 1_000_000_000))
    _ = nanosleep(&ts, nil)
}

/// Convert a [String] into a NULL-terminated argv array of C strings the
/// posix_spawn family expects. Each cstring is allocated and freed in the
/// scope of the body closure.
// Shared with ValidatorClient.swift. Internal-scope.
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
