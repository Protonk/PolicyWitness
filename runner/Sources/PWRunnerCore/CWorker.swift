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
 *   3. Touch each page in the host mapping; this does not establish
 *      worker page residency or eliminate post-apply faults.
 *   4. Release-store `prepared = 1`.
 *   5. Create ready + policy pipes. Mark parent-side ends FD_CLOEXEC.
 *   6. posix_spawn pw-probe-runner with FDs dup'd to 0/3/4.
 *   7. Write the policy text to the policy pipe and close.
 *   8. Read the pre-apply ready byte (deadline).
 *   9. Acquire applied and each phase arrival; collect, then release its ordinal;
 *      retain per-phase acknowledgement/completion with bounded sentinel polling.
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
    static let abiIdentityHex = "6f777628d0b0f233f6e26f99222e8f78cd0920bb94b842b5bf2d0c4b2e29a9a7"
    static let abiIdentity: [UInt8] = [0x6f, 0x77, 0x76, 0x28, 0xd0, 0xb0, 0xf2, 0x33, 0xf6, 0xe2, 0x6f, 0x99, 0x22, 0x2e, 0x8f, 0x78, 0xcd, 0x09, 0x20, 0xbb, 0x94, 0xb8, 0x42, 0xb5, 0xbf, 0x2d, 0x0c, 0x4b, 0x2e, 0x29, 0xa9, 0xa7]
    // END GENERATED WORKER IDENTITY

    static let abiMagic: UInt32 = 0x50574944
    static let abiIdentityBytes: Int = 32

    static let headerBytes: Int     = 448
    static let maxPhases: Int = 8
    static let phaseBytes: Int = 32
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

    static let extensionRequestedOffset: Int = 100
    static let extensionDeliveryPublishedOffset: Int = 104
    static let extensionDeliveryStatusOffset: Int = 108
    static let extensionDeliveredBytesOffset: Int = 112
    static let extensionDeliveryStageOffset: Int = 116
    static let extensionDeliveryNativeRcOffset: Int = 120
    static let extensionDeliveryErrnoOffset: Int = 124
    static let extensionDeliveryCleanupStageOffset: Int = 128
    static let extensionDeliveryCleanupErrnoOffset: Int = 132
    // Policy delivery acknowledgement: the host's expected byte count (input) and
    // the worker's EOF receipt (count plus its publication flag).
    static let policyBytesExpectedOffset: Int = 136
    static let policyBytesReceivedOffset: Int = 140
    static let policyReadPublishedOffset: Int = 144
    static let phaseCountOffset: Int = 96
    static let phaseRecordsOffset: Int = 192
    static let phaseFirstSlotOffset: Int = 0
    static let phaseEndSlotOffset: Int = 4
    static let phaseArrivedOffset: Int = 8
    static let phaseAcknowledgedOffset: Int = 12
    static let phaseCompletedOffset: Int = 16

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
    static let freshReadBytes: Int = 64
    static let slotCallBoundaryOffset: Int = 5984
    static let slotNativeResultValidOffset: Int = 5988
    static let slotNativeResultOffset: Int = 5992
    static let slotNativeErrnoOffset: Int = 6000
    static let slotUnavailableCodeOffset: Int = 6004
    static let slotAccessOpenRcOffset: Int = 6008
    static let slotAccessOpenErrnoOffset: Int = 6012
    static let slotAccessReadRcOffset: Int = 6016
    static let slotAccessReadErrnoOffset: Int = 6024
    static let slotAccessCloseRcOffset: Int = 6028
    static let slotAccessCloseErrnoOffset: Int = 6032
    static let slotAccessStatRcOffset: Int = 6036
    static let slotAccessStatErrnoOffset: Int = 6040
    static let slotAccessModeOffset: Int = 6044
    static let slotAccessDeviceOffset: Int = 6048
    static let slotAccessInodeOffset: Int = 6056
    static let slotAccessUidOffset: Int = 6064
    static let slotAccessGidOffset: Int = 6068
    static let slotAccessBytesOffset: Int = 6072
    static let slotExecValidOffset: Int = 6136
    static let slotExecCollectionStopOffset: Int = 6140
    static let slotExecLeaderExitObservedOffset: Int = 6144
    static let slotExecStdoutEofOffset: Int = 6148
    static let slotExecStderrEofOffset: Int = 6152
    static let slotExecDeadlineKindOffset: Int = 6156
    static let slotExecWaitidErrnoOffset: Int = 6160
    static let slotExecPollErrnoOffset: Int = 6164
    static let slotExecStdoutReadErrnoOffset: Int = 6168
    static let slotExecStderrReadErrnoOffset: Int = 6172
    static let slotExecStdoutPollReventsOffset: Int = 6176
    static let slotExecStderrPollReventsOffset: Int = 6180
    static let slotExecCollectionClockFaultOffset: Int = 6184
    static let slotExecCleanupStateOffset: Int = 6188
    static let slotExecGroupTargetOffset: Int = 6192
    static let slotExecGroupSignalOffset: Int = 6196
    static let slotExecGroupRcOffset: Int = 6200
    static let slotExecGroupErrnoOffset: Int = 6204
    static let slotExecFallbackPresentOffset: Int = 6208
    static let slotExecFallbackTargetOffset: Int = 6212
    static let slotExecFallbackSignalOffset: Int = 6216
    static let slotExecFallbackRcOffset: Int = 6220
    static let slotExecFallbackErrnoOffset: Int = 6224
    static let slotExecReapStopOffset: Int = 6228
    static let slotExecReapWaitRcOffset: Int = 6232
    static let slotExecReapWaitErrnoOffset: Int = 6236
    static let slotExecReapStatusOffset: Int = 6240
    static let slotExecReapClockFaultOffset: Int = 6244
    static let slotFreshWriteOffset: Int = 6248
    static let fileStatBytes: Int = 48
    static let fileStatRcOffset: Int = 0
    static let fileStatErrnoOffset: Int = 4
    static let fileStatModeOffset: Int = 8
    static let fileStatUidOffset: Int = 12
    static let fileStatGidOffset: Int = 16
    static let fileStatDeviceOffset: Int = 24
    static let fileStatInodeOffset: Int = 32
    static let fileStatSizeOffset: Int = 40
    static let freshWriteBytes: Int = 232
    static let freshWriteOpenRcOffset: Int = 0
    static let freshWriteOpenErrnoOffset: Int = 4
    static let freshWriteTruncateRcOffset: Int = 8
    static let freshWriteTruncateErrnoOffset: Int = 12
    static let freshWriteWriteRcOffset: Int = 16
    static let freshWriteWriteErrnoOffset: Int = 24
    static let freshWriteCloseRcOffset: Int = 28
    static let freshWriteCloseErrnoOffset: Int = 32
    static let freshWritePreopenStatOffset: Int = 40
    static let freshWriteOpenedStatOffset: Int = 88
    static let freshWriteTruncatedStatOffset: Int = 136
    static let freshWriteWrittenStatOffset: Int = 184

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
    case fileReadFresh = 9
    case extensionConsume = 10
    case extensionRelease = 11
    case fileWriteFresh = 12
    case fileCreateFresh = 13
}

// MARK: - C atomic shim binding

@_silgen_name("pw_cworker_load_acquire_u32")
private func pw_cworker_load_acquire_u32(_ p: UnsafePointer<UInt32>) -> UInt32

@_silgen_name("pw_cworker_store_release_u32")
func pw_cworker_store_release_u32(_ p: UnsafeMutablePointer<UInt32>, _ value: UInt32)

@_silgen_name("pw_cworker_shm_open_create")
func pw_cworker_shm_open_create(_ name: UnsafePointer<CChar>, _ mode: mode_t) -> Int32

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

struct CWorkerPhaseInput {
    var firstSlot: Int
    var endSlot: Int
}
struct CWorkerPhaseOutput {
    var arrived = false
    var collectionClosed = false
    var releaseSet = false
    var acknowledged = false
    var completed = false
    var ownershipEstablished = false
    var violations: [String] = []
}

struct CWorkerInput {
    var extensionRequested = false
    var extensionFD: Int32? = nil
    static let defaultPolicyTransferTimeoutMs = 5_000
    // Internal test setting; never admitted from request JSON.
    var policyTransferTimeoutMs = CWorkerInput.defaultPolicyTransferTimeoutMs
    // Internal controls operate on the real wait and ordinal store. They are
    // never decoded from a specimen and cannot manufacture observations.
    var proceedWaitMs: Int? = nil
    var phaseReleaseOrdinal: ((Int) -> UInt32)? = nil
    static let defaultSentinelTimeoutMs = 120_000
    var workerExecutablePath: String
    var policy: String
    var params: [CWorkerParam]
    /// Explicit opt-in: captured bytecode and input hashes are sensitive output.
    var captureCompiledProfile: Bool
    var captureNonce: String?
    var slots: [CWorkerSlotInput]
    var phases: [CWorkerPhaseInput]
    var readyByteTimeoutMs: Int
    var sentinelTimeoutMs: Int
    var exitGraceMs: Int
    /// Optional test-seam routed to pw-probe-runner as
    /// `--post-apply-hang-ms <N>` when positive. If native argument admission
    /// and execution reach the post-phase seam, the worker requests an N ms
    /// sleep before `done`. A shorter host allowance can expire meanwhile;
    /// the request alone establishes neither a reached sleep nor a timeout.
    var postApplyHangMs: Int?
    /// Optional test-seam routed to pw-probe-runner as
    /// `--post-apply-kill-signal <N>` when positive. If admitted and reached,
    /// the post-phase seam requests signal N on the worker before `done`.
    /// Failed delivery or a nonfatal/ignored signal can return. A reaped fatal
    /// signal establishes disposition, not its sender or a policy cause.
    var postApplyKillSignal: Int?
    /// Optional test-seam routed to pw-probe-runner as
    /// `--pre-ready-hang-ms <N>` when positive. If admitted and reached after
    /// compilation/capture, it requests sleep before the ready byte. The
    /// sentinel allowance can expire before application; a requested duration
    /// is not an observation of the sleep's entry, return or elapsed time.
    var preReadyHangMs: Int?
    /// Optional test-seam routed to pw-probe-runner as
    /// `--kill-before-publish-slot <N>` when nonnegative. If admitted and that
    /// slot is reached, run_attempt() requests SIGKILL after dispatch returns
    /// and before publishing `completed`. Dispatch can refuse without a native
    /// attempt. Observed started progress with no immutable result does not
    /// recover an unpublished native return or identify the signal's sender.
    var killBeforePublishSlot: Int?
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
                phases: [CWorkerPhaseInput]? = nil,
                readyByteTimeoutMs: Int = 1_000,
                sentinelTimeoutMs: Int = CWorkerInput.defaultSentinelTimeoutMs,
                exitGraceMs: Int = 1_000,
                postApplyHangMs: Int? = nil,
                postApplyKillSignal: Int? = nil,
                preReadyHangMs: Int? = nil,
                killBeforePublishSlot: Int? = nil,
                execChildDeadlineMs: Int? = nil,
                execAttemptBudgetMs: Int? = nil,
                captureCompiledProfile: Bool = false,
                captureNonce: String? = nil) {
        self.workerExecutablePath = workerExecutablePath
        self.policy = policy
        self.params = params
        self.slots = slots
        self.phases = phases ?? [CWorkerPhaseInput(firstSlot: 0, endSlot: slots.count)]
        self.readyByteTimeoutMs = readyByteTimeoutMs
        self.sentinelTimeoutMs = sentinelTimeoutMs
        self.exitGraceMs = exitGraceMs
        self.postApplyHangMs = postApplyHangMs
        self.postApplyKillSignal = postApplyKillSignal
        self.preReadyHangMs = preReadyHangMs
        self.killBeforePublishSlot = killBeforePublishSlot
        self.execChildDeadlineMs = execChildDeadlineMs
        self.execAttemptBudgetMs = execAttemptBudgetMs
        self.captureCompiledProfile = captureCompiledProfile
        self.captureNonce = captureNonce
    }
}

struct CWorkerSlotResult {
    var callBoundary = false
    var nativeResult: Int64? = nil
    var nativeErrno: Int32? = nil
    var unavailableCode: UInt32? = nil
    var freshRead: PWRunnerFreshRead? = nil
    var freshWrite: PWRunnerFreshWrite? = nil
    var execObservation: PWExecObservation? = nil
    var execObservationProblem: String? = nil
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
    var profileCapture: CompiledProfileCapture? = nil
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
    var phases: [CWorkerPhaseOutput] = []
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
    /// The worker's delivery publication, read only after its release store.
    var extensionDelivery: CWorkerExtensionDelivery? = nil
    /// Measured host waits; nil when the stage did not run.
    var readyWait: PWHostWait? = nil
    var sentinelWait: PWHostWait? = nil
    var graceWait: PWHostWait? = nil
}

/// Raw delivery publication words. Codes are interpreted by the orchestrator;
/// unknown values stay numbers here.
struct CWorkerExtensionDelivery: Equatable {
    var status: UInt32
    var deliveredBytes: UInt32
    var stage: UInt32
    var nativeRc: Int32
    var errno: Int32
    var cleanupStage: UInt32
    var cleanupErrno: Int32
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
        stage: (raw >> 20) & 15, index: item == 0 ? nil : item - 1)
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
    // The EOF receipt is gated by its own publication word in the region
    // header. Zero or any other flag exposes no count; a count outside the
    // source capacity cannot have been read into the fixed buffer, so it is
    // not exposed either. Absence establishes nothing about delivery.
    var policyRead: PWWorkerPolicyRead? = nil
    if loadAcquire(base, offset: PWShmLayout.policyReadPublishedOffset) == 1 {
        let expected = UInt32(bitPattern: readI32(base, offset: PWShmLayout.policyBytesExpectedOffset))
        let received = UInt32(bitPattern: readI32(base, offset: PWShmLayout.policyBytesReceivedOffset))
        if expected < PWShmLayout.policyBytes && received < PWShmLayout.policyBytes {
            policyRead = PWWorkerPolicyRead(bytes_expected: Int(expected), bytes_received: Int(received))
        }
    }
    return PWWorkerEvidence(abi_identity: PWShmLayout.abiIdentityHex, progress: progress,
        failure_publication: published, failure_state: state, failure: failure,
        readiness: readiness, diagnostic: diagnostic, policy_read: policyRead)
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
    source: String, params: [CWorkerParam], nonce: String?) -> CompiledProfileCapture {
    func unavailable(_ reason: String) -> CompiledProfileCapture {
        CompiledProfileCapture(status: "unavailable", reason: reason, worker_pid: Int(workerPid))
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
    return CompiledProfileCapture(status: "captured", worker_pid: Int(workerPid),
        producer: "worker", capture_stage: "before_apply", request_nonce: nonce, profile_type: 0,
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
            return "capture_compiled_profile requires a fresh 32-character lowercase hex capture_nonce"
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
    if input.phases.count > PWShmLayout.maxPhases {
        return PWRunnerAdmissionFailure(field: "phases", actual: input.phases.count, maximum: PWShmLayout.maxPhases, unit: "items")
    }
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
typealias CWorkerPhaseHook = (pid_t, Int) -> Void

func runCWorker(_ input: CWorkerInput, phaseBoundary: @escaping CWorkerPhaseHook) -> CWorkerRunResult {
    runCWorker(input, processCalls: ChildProcessCalls(), phaseBoundary: phaseBoundary)
}

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
    /// The monotonic clock and the bounded sleep every host wait uses. Tests
    /// may drive them; production reads CLOCK_MONOTONIC and nanosleeps.
    var clock: () -> UInt64? = MonotonicDeadline.now
    var sleep: (UInt64) -> Void = sleepNs
}

/// One host wait measured as elapsed monotonic time against an allowance.
/// Progress, interrupted calls and sleep overruns never renew it; each sleep is
/// bounded by the remaining allowance. Excluded intervals (synchronous phase
/// collection) extend the allowance by exactly their measured length. When the
/// clock fails or runs backwards the wait spends only the last remaining
/// allowance in nominal sleeps; it never restores time already charged.
struct HostWaitClock {
    let budgetNs: UInt64
    let pollNs: UInt64
    let calls: ChildProcessCalls
    let started: UInt64?
    private(set) var excludedNs: UInt64 = 0
    private(set) var clockFault = false
    private var lastReading: UInt64?
    private var fallbackRemainingNs: UInt64

    init(milliseconds: Int, pollNs: UInt64, calls: ChildProcessCalls) {
        budgetNs = min(UInt64(max(0, milliseconds)), UInt64.max / 1_000_000) * 1_000_000
        self.pollNs = max(1, pollNs)
        self.calls = calls
        started = calls.clock()
        lastReading = started
        clockFault = started == nil
        fallbackRemainingNs = budgetNs
    }

    /// Every reading, including exclusion boundaries, must follow the previous one.
    private mutating func readClock() -> UInt64? {
        guard !clockFault, let previous = lastReading, let now = calls.clock(), now >= previous else {
            clockFault = true
            return nil
        }
        lastReading = now
        return now
    }

    private mutating func account(_ now: UInt64) {
        guard let start = started else { return }
        let elapsed = now - start
        let allowance = budgetNs > UInt64.max - excludedNs ? UInt64.max : budgetNs + excludedNs
        fallbackRemainingNs = elapsed >= allowance ? 0 : allowance - elapsed
    }

    /// Elapsed nanoseconds since the wait started, or nil once the clock is unusable.
    mutating func elapsedNs() -> UInt64? {
        guard let now = readClock(), let start = started else { return nil }
        account(now)
        return now - start
    }

    /// The remaining allowance: budget plus excluded time minus elapsed time.
    mutating func remainingNs() -> UInt64? {
        guard elapsedNs() != nil else { return nil }
        return fallbackRemainingNs
    }

    /// Decide whether the allowance is exhausted; otherwise sleep for at most
    /// the remaining allowance and report that the wait continues.
    mutating func expiredAfterSleeping() -> Bool {
        _ = remainingNs()
        if fallbackRemainingNs == 0 { return true }
        let sleep = min(pollNs, fallbackRemainingNs)
        // If the next clock read fails, this requested sleep is already charged.
        // A working clock measures the actual interval on its next reading.
        fallbackRemainingNs -= sleep
        calls.sleep(sleep)
        return false
    }

    /// Mark the start of an interval the wait does not charge.
    mutating func mark() -> UInt64? {
        guard elapsedNs() != nil else { return nil }
        return lastReading
    }

    /// Exclude the interval since `mark()`; an unreadable interval is a clock fault.
    mutating func excludeSince(_ mark: UInt64?) {
        guard let start = mark, let end = readClock(), end >= start else { clockFault = true; return }
        let interval = end - start
        excludedNs = excludedNs > UInt64.max - interval ? UInt64.max : excludedNs + interval
        account(end)
    }

    mutating func record(stop: String, nativeErrno: Int32? = nil, excluded: Bool = false) -> PWHostWait {
        let elapsed = elapsedNs()
        return PWHostWait(budget_ms: Int(budgetNs / 1_000_000), elapsed_ms: elapsed.map { $0 / 1_000_000 },
                          stop: stop, excluded_ms: excluded ? excludedNs / 1_000_000 : nil,
                          native_errno: nativeErrno, clock_fault: clockFault)
    }
}

enum ChildWaitObservation { case pending, reaped, failed }

/// One child's host observations. Status is assigned only by a successful reap.
/// Across polling/grace/final reap, allow two EINTR retries total. A terminal
/// wait error ends that stage; ECHILD ends all waits/kills because ownership is
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

    mutating func wait(options: Int32, stage: String) -> ChildWaitObservation {
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
                waitErrors.append(PWRunnerWaitError(stage: stage, rc: rc, errno: error))
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
        _ = wait(options: rc == 0 ? 0 : WNOHANG, stage: "after_termination")
    }
}

func runCWorker(_ input: CWorkerInput, processCalls: ChildProcessCalls,
                transferCalls: PolicyTransferCalls = PolicyTransferCalls(),
                postApplied: CWorkerPostAppliedHook? = nil, phaseBoundary: CWorkerPhaseHook? = nil) -> CWorkerRunResult {
    if input.captureCompiledProfile && captureNonceBytes(input.captureNonce) == nil {
        return .failure(.captureNonceInvalid)
    }
    // All capacity refusals use the same host-owned record, before shm/spawn.
    if let failure = workerAdmissionFailure(input) { return .failure(.admissionFailed(failure)) }
    var endSlot = 0
    guard !input.phases.isEmpty, input.phases.allSatisfy({ phase in
        defer { endSlot = phase.endSlot }
        return phase.firstSlot == endSlot && phase.endSlot >= endSlot && phase.endSlot <= input.slots.count
    }), endSlot == input.slots.count else { return .failure(.shmSetupFailed("invalid phase partition")) }
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
    var ownsShmFD = true
    defer {
        _ = munmap(base, PWShmLayout.regionBytes)
        if ownsShmFD { close(shmFD) }
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
    writeU32(rawBase, offset: PWShmLayout.extensionRequestedOffset, input.extensionRequested ? 1 : 0)
    writeU32(rawBase, offset: PWShmLayout.stepCountOffset, UInt32(input.slots.count))
    writeU32(rawBase, offset: PWShmLayout.paramCountOffset, UInt32(input.params.count))
    // The submission's byte array is built once. Its count is the header's
    // expected policy length and every transfer record's bytes_expected, and
    // the same bytes are what writePolicy delivers after spawn. The worker
    // compares the count it reads at EOF against this input; admission bounds
    // it below the source capacity.
    let policyBytes = Array(input.policy.utf8)
    writeU32(rawBase, offset: PWShmLayout.policyBytesExpectedOffset, UInt32(policyBytes.count))
    writeU32(rawBase, offset: PWShmLayout.captureRequestedOffset, input.captureCompiledProfile ? 1 : 0)
    if input.captureCompiledProfile, let nonce = captureNonceBytes(input.captureNonce) {
        nonce.copyBytes(to: rawBase.advanced(by: PWShmLayout.captureNonceOffset), count: nonce.count)
    }

    writeU32(rawBase, offset: PWShmLayout.phaseCountOffset, UInt32(input.phases.count))
    for (index, phase) in input.phases.enumerated() {
        let base = rawBase.advanced(by: PWShmLayout.phaseRecordsOffset + index * PWShmLayout.phaseBytes)
        writeU32(base, offset: PWShmLayout.phaseFirstSlotOffset, UInt32(phase.firstSlot))
        writeU32(base, offset: PWShmLayout.phaseEndSlotOffset, UInt32(phase.endSlot))
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

    // ---- Touch pages in the host mapping. The worker maps independently;
    // host touching does not prove its page residency or absence of faults.
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

    // A high CLOEXEC duplicate avoids collisions with the evidence/ready dup2
    // destinations even when the session's original channel occupied FD 3/4/5.
    var tokenFD: Int32 = -1
    if let source = input.extensionFD {
        tokenFD = fcntl(source, F_DUPFD_CLOEXEC, 64)
        if tokenFD < 0 {
            for fd in readyPipe + policyPipe { close(fd) }
            return .failure(.shmSetupFailed("extension descriptor duplication failed"))
        }
    }
    defer { if tokenFD >= 0 { close(tokenFD) } }
    // ---- posix_spawn.
    var fa: posix_spawn_file_actions_t? = nil
    posix_spawn_file_actions_init(&fa)
    defer { posix_spawn_file_actions_destroy(&fa) }
    posix_spawn_file_actions_adddup2(&fa, policyPipe[0], 0)
    posix_spawn_file_actions_adddup2(&fa, shmFD, 3)
    posix_spawn_file_actions_adddup2(&fa, readyPipe[1], 4)
    if tokenFD >= 0 { posix_spawn_file_actions_adddup2(&fa, tokenFD, 5) }

    let stepCountStr = String(input.slots.count)
    var argv: [String] = [
        "pw-probe-runner",
        "--shm-fd", "3",
        "--ready-fd", "4",
        "--step-count", stepCountStr,
    ]
    if tokenFD >= 0 { argv += ["--extension-fd", "5"] }
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
    if let slot = input.killBeforePublishSlot, slot >= 0 {
        argv.append("--kill-before-publish-slot")
        argv.append(String(slot))
    }
    if let deadlineMs = input.execChildDeadlineMs, deadlineMs > 0 {
        argv.append("--exec-child-deadline-ms")
        argv.append(String(deadlineMs))
    }
    if let waitMs = input.proceedWaitMs {
        argv += ["--proceed-wait-ms", String(waitMs)]
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
    // The transfer calls (clock, write, poll) are one injection point: the
    // deadline and the writer share the supplied clock, and production keeps
    // the Darwin defaults.
    let transferDeadline = MonotonicDeadline(milliseconds: input.policyTransferTimeoutMs, clock: transferCalls.clock)
    // The child now owns its evidence endpoint. Retain only our mapping, so
    // later validators cannot inherit the host's writable descriptor. Retire
    // close ownership first: a reused number must never reach deferred close.
    ownsShmFD = false
    close(shmFD)
    // Close parent-side ends that the child now owns.
    close(policyPipe[0])
    close(readyPipe[1])
    var process = ChildProcessState(pid: pid, calls: processCalls)

    // ---- Deliver under one deadline established immediately after spawn. The
    // bytes are the array whose count the header already carries.
    let transfer = writePolicy(policyBytes, fd: policyPipe[1], deadline: transferDeadline, calls: transferCalls)
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

    // ---- Read pre-apply ready byte under its elapsed allowance. The wait
    // starts after policy transfer completed. The read end must be
    // nonblocking first: a blocking read would turn the allowance into an
    // unbounded wait, so a failed prerequisite is recorded and no wait runs.
    var readyByte: UInt8 = 0
    var readyByteReceived = false
    var readyWait: PWHostWait? = nil
    if transferFailure == nil {
        let flags = fcntl(readyPipe[0], F_GETFL, 0)
        if flags < 0 || fcntl(readyPipe[0], F_SETFL, flags | O_NONBLOCK) < 0 {
            readyWait = PWHostWait(budget_ms: input.readyByteTimeoutMs, elapsed_ms: 0, stop: "setup_failed",
                                   native_errno: errno, clock_fault: false)
        } else {
            var clock = HostWaitClock(milliseconds: input.readyByteTimeoutMs, pollNs: 10_000_000, calls: processCalls)
            var stop = "deadline"
            var readErrno: Int32? = nil
            while true {
                // The read precedes the clock: a byte that lands as the
                // allowance runs out is received, not timed out.
                let n = Darwin.read(readyPipe[0], &readyByte, 1)
                if n == 1 { readyByteReceived = true; stop = "received"; break }
                if n == 0 { stop = "eof"; break }     // EOF — worker exited without writing
                if n < 0 && errno != EAGAIN && errno != EINTR { stop = "read_error"; readErrno = errno; break }
                if clock.expiredAfterSleeping() { break }
            }
            readyWait = clock.record(stop: stop, nativeErrno: readErrno)
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
    var phaseOutputs = input.phases.map { _ in CWorkerPhaseOutput() }
    var nextPhase = 0
    var ownershipUnbroken = true
    func phaseBase(_ index: Int) -> UnsafeMutablePointer<UInt8> {
        rawBase.advanced(by: PWShmLayout.phaseRecordsOffset + index * PWShmLayout.phaseBytes)
    }
    func observeAcknowledgement() {
        for index in input.phases.indices {
            let base = phaseBase(index)
            let ack = loadAcquire(base, offset: PWShmLayout.phaseAcknowledgedOffset)
            if ownershipUnbroken && phaseOutputs[index].releaseSet && ack == 1 {
                phaseOutputs[index].ownershipEstablished = true
            }
        }
    }
    func checkPrematurePublication(_ index: Int) {
        let base = phaseBase(index)
        let ordinal = loadAcquire(rawBase, offset: PWShmLayout.proceedObservedOffset)
        let ack = loadAcquire(base, offset: PWShmLayout.phaseAcknowledgedOffset)
        let progress = loadAcquire(rawBase.advanced(by: PWShmLayout.evidenceOffset), offset: PWShmLayout.evidenceProgressOffset)
        let progressIndex = Int(progress & 0xfffff) - 1
        let completed = (input.phases[index].firstSlot..<input.slots.count).contains { i in
            loadAcquire(rawBase.advanced(by: PWShmLayout.slotsOffset + i * PWShmLayout.slotBytes),
                        offset: PWShmLayout.slotCompletedOffset) == 1
        }
        if ack != 0 || ordinal > UInt32(index) { phaseOutputs[index].violations.append("acknowledgement_before_release") }
        if completed || (progress >> 24 == 9 && progressIndex >= input.phases[index].firstSlot) {
            phaseOutputs[index].violations.append("attempt_before_release")
        }
    }
    var pollStopReason = transferFailure == nil ? "sentinel_deadline" : (transferTimeout == nil ? "policy_write_error" : "policy_transfer_deadline")
    var sentinelWait: PWHostWait? = nil
    if transferFailure == nil {
        // The sentinel allowance is elapsed monotonic time from the end of
        // the readiness wait, excluding each synchronous phase collection
        // interval measured around the hook. Each sleep is bounded by the
        // remaining allowance; syscall and scheduling costs consume it.
        var clock = HostWaitClock(milliseconds: input.sentinelTimeoutMs, pollNs: 2_000_000, calls: processCalls)
        // Probe for a dead worker only every ~50 ms of elapsed time (every
        // 25 passes once the clock is unusable): a waitpid in the hot loop
        // costs more than the detection latency saves.
        var nextExitCheckNs: UInt64 = 0
        var passes = 0
        polling: while true {
            passes += 1
            if !sawApplied && loadAcquire(rawBase, offset: PWShmLayout.appliedOffset) == 1 {
                sawApplied = true
            }
            // Only the exact arrived phase may collect predictions. Planning and
            // collection occur while this worker is paused, after prior completion.
            if sawApplied && nextPhase < input.phases.count
                && readI32(rawBase, offset: PWShmLayout.applyRcOffset) == 0
                && workerIdentityMatches(rawBase)
                && loadAcquire(rawBase, offset: PWShmLayout.doneOffset) == 0
                && loadAcquire(phaseBase(nextPhase), offset: PWShmLayout.phaseArrivedOffset) == 1 {
                let index = nextPhase
                phaseOutputs[index].arrived = true
                checkPrematurePublication(index)
                observeAcknowledgement()
                if index > 0 && loadAcquire(phaseBase(index - 1), offset: PWShmLayout.phaseCompletedOffset) != 1 {
                    phaseOutputs[index].violations.append("arrival_without_previous_completion")
                }
                if loadAcquire(phaseBase(index), offset: PWShmLayout.phaseCompletedOffset) != 0 {
                    phaseOutputs[index].violations.append("completion_before_release")
                }
                if !phaseOutputs[index].violations.isEmpty {
                    // Preserve the invalid boundary and stop collections. Normal
                    // done/death/deadline polling still owns terminal cleanup.
                    nextPhase = input.phases.count
                    continue
                }
                switch process.wait(options: WNOHANG, stage: "poll") {
                case .reaped: pollStopReason = "child_reaped"; break polling
                case .failed: ownershipUnbroken = false; pollStopReason = "wait_error"; break polling
                case .pending: break
                }
                let hookStarted = clock.mark()
                if let hook = phaseBoundary { hook(pid, index) }
                else if index == 0, let hook = postApplied { hook(pid) }
                clock.excludeSince(hookStarted)
                phaseOutputs[index].collectionClosed = true
                checkPrematurePublication(index)
                // Collection may outlast the worker wait or lose the child. A
                // closed collection alone never authorizes a late release.
                switch process.wait(options: WNOHANG, stage: "poll") {
                case .reaped: pollStopReason = "child_reaped"; break polling
                case .failed: ownershipUnbroken = false; pollStopReason = "wait_error"; break polling
                case .pending: break
                }
                if loadAcquire(rawBase, offset: PWShmLayout.doneOffset) == 0
                    && loadAcquire(phaseBase(index), offset: PWShmLayout.phaseArrivedOffset) == 1
                    && loadAcquire(phaseBase(index), offset: PWShmLayout.phaseAcknowledgedOffset) == 0
                    && loadAcquire(phaseBase(index), offset: PWShmLayout.phaseCompletedOffset) == 0
                    && (index == 0 || loadAcquire(phaseBase(index - 1), offset: PWShmLayout.phaseCompletedOffset) == 1)
                    && phaseOutputs[index].violations.isEmpty {
                    let ordinal = input.phaseReleaseOrdinal?(index) ?? UInt32(index + 1)
                    storeRelease(rawBase, offset: PWShmLayout.proceedOffset, ordinal)
                    phaseOutputs[index].releaseSet = ordinal == UInt32(index + 1)
                    if ordinal != UInt32(index + 1) { phaseOutputs[index].violations.append("wrong_release_ordinal") }
                }
                nextPhase += 1
            }
            observeAcknowledgement()
            if loadAcquire(rawBase, offset: PWShmLayout.doneOffset) != 0 {
                sawDone = true
                pollStopReason = "done"
                break
            }
            // The worker may publish and exit between the samples above and
            // this wait. Retain this actual stop reason; final reconciliation
            // recovers immutable publications without inventing timely done.
            let elapsed = clock.elapsedNs()
            if elapsed.map({ $0 >= nextExitCheckNs }) ?? (passes % 25 == 1) {
                nextExitCheckNs = (elapsed ?? 0) + 50_000_000
                switch process.wait(options: WNOHANG, stage: "poll") {
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
            // done was read above: a publication observed as the allowance
            // runs out is done, not a deadline.
            if clock.expiredAfterSleeping() { break }
        }
        sentinelWait = clock.record(stop: pollStopReason, excluded: true)
    }

    // ---- Request worker exit (a no-op if it already died on its own).
    storeRelease(rawBase, offset: PWShmLayout.exitRequestedOffset, 1)
    // The cleanup trigger is recorded here, at the store, as the reason polling
    // stopped; it is a host fact for the disposition record, not reconstructed
    // from a final exit code.
    let cleanupTrigger = PWDisposition.triggerForStop[pollStopReason] ?? pollStopReason

    // ---- Reap (grace + SIGKILL fallback), unless the poll loop already
    // reaped the worker. How the grace wait
    // ended is recorded directly: a reap, a wait error, or exhaustion (which
    // is followed by the termination request), never inferred later.
    var graceEnd = "not_entered"
    var graceWait: PWHostWait? = nil
    if process.status == nil && !process.childUnavailable {
        var clock = HostWaitClock(milliseconds: input.exitGraceMs, pollNs: 10_000_000, calls: processCalls)
        graceEnd = "exhausted"
        grace: while true {
            observeAcknowledgement()
            switch process.wait(options: WNOHANG, stage: "exit_grace") {
            case .reaped:
                graceEnd = "reaped_during_grace"
                break grace
            case .failed:
                graceEnd = "wait_error"
                ownershipUnbroken = false
                break grace
            case .pending:
                break
            }
            if clock.expiredAfterSleeping() { break }
        }
        graceWait = clock.record(stop: graceEnd)
        observeAcknowledgement()
        let errorsBeforeTermination = process.waitErrors.count
        process.terminate()
        if process.waitErrors.count > errorsBeforeTermination { ownershipUnbroken = false }
    }
    // Acknowledgement may follow the last polling/grace sample and precede
    // reap, including a fatal exit without done. Unbroken ownership through
    // that publication establishes the phase's historical lifetime; the
    // existing predicate cannot repair ownership lost before acknowledgement.
    if process.status != nil { observeAcknowledgement() }
    // Collection basis: whether every read below follows a successful reap. A
    // reap observed later cannot upgrade it.
    let collectionBasis = process.status != nil ? "after_confirmed_reap" : "execution_may_continue"

    // Final acquire snapshot after cleanup. Publications are immutable, so this
    // also safely retains results if cleanup failed and the child is still alive.
    // Never rewrite pollStopReason or run the validator against a reaped child.
    sawApplied = loadAcquire(rawBase, offset: PWShmLayout.appliedOffset) == 1
    sawDone = loadAcquire(rawBase, offset: PWShmLayout.doneOffset) == 1
    for index in input.phases.indices {
        let base = phaseBase(index)
        phaseOutputs[index].arrived = loadAcquire(base, offset: PWShmLayout.phaseArrivedOffset) == 1
        phaseOutputs[index].acknowledged = loadAcquire(base, offset: PWShmLayout.phaseAcknowledgedOffset) == 1
        phaseOutputs[index].completed = loadAcquire(base, offset: PWShmLayout.phaseCompletedOffset) == 1
    }
    let finalProceedObserved = phaseOutputs.allSatisfy { $0.acknowledged }
    let applyRC = (sawApplied || sawDone) ? readI32(rawBase, offset: PWShmLayout.applyRcOffset) : 0
    let applyErrno = (sawApplied || sawDone) ? readI32(rawBase, offset: PWShmLayout.applyErrnoOffset) : 0

    // Slot payloads are immutable after release publication. Read only confirmed slots.
    var slotResults: [CWorkerSlotResult] = []
    slotResults.reserveCapacity(input.slots.count)
    for i in 0..<input.slots.count {
        let slotBase = rawBase.advanced(by: PWShmLayout.slotsOffset + i * PWShmLayout.slotBytes)
        let completed = loadAcquire(slotBase, offset: PWShmLayout.slotCompletedOffset)
        if completed != 1 {
            slotResults.append(CWorkerSlotResult(callBoundary: loadAcquire(slotBase, offset: PWShmLayout.slotCallBoundaryOffset) == 1, stepId: input.slots[i].stepId,
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

        let execAccount = isExec ? decodeExecObservation(slotBase, childPid: childPid ?? 0) : (nil, nil)

        slotResults.append(CWorkerSlotResult(
            callBoundary: loadAcquire(slotBase, offset: PWShmLayout.slotCallBoundaryOffset) == 1,
            nativeResult: readI32(slotBase, offset: PWShmLayout.slotNativeResultValidOffset) == 1 ? readI64(slotBase, offset: PWShmLayout.slotNativeResultOffset) : nil,
            nativeErrno: readI32(slotBase, offset: PWShmLayout.slotNativeResultValidOffset) == 1 ? readI32(slotBase, offset: PWShmLayout.slotNativeErrnoOffset) : nil,
            unavailableCode: [.extensionConsume, .extensionRelease].contains(input.slots[i].attemptKind) ? UInt32(bitPattern: readI32(slotBase, offset: PWShmLayout.slotUnavailableCodeOffset)) : nil,
            freshRead: input.slots[i].attemptKind == .fileReadFresh ? decodeFreshRead(slotBase) : nil,
            freshWrite: [.fileWriteFresh, .fileCreateFresh].contains(input.slots[i].attemptKind) ? decodeFreshWrite(slotBase) : nil,
            execObservation: execAccount.0, execObservationProblem: execAccount.1,
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
        profileCapture: input.captureCompiledProfile ? decodeProfileCapture(
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
        phases: phaseOutputs,
        hookInvoked: phaseOutputs.allSatisfy { $0.collectionClosed },
        proceedSet: phaseOutputs.allSatisfy { $0.releaseSet },
        proceedObserved: finalProceedObserved,
        proceedOwnershipEstablished: phaseOutputs.allSatisfy { $0.ownershipEstablished },
        orderingProtocolViolations: Array(Set(phaseOutputs.flatMap { $0.violations })).sorted(),
        cleanupTrigger: cleanupTrigger,
        graceEnd: graceEnd,
        collectionBasis: collectionBasis,
        extensionDelivery: loadAcquire(rawBase, offset: PWShmLayout.extensionDeliveryPublishedOffset) == 1
            ? CWorkerExtensionDelivery(
                status: UInt32(bitPattern: readI32(rawBase, offset: PWShmLayout.extensionDeliveryStatusOffset)),
                deliveredBytes: UInt32(bitPattern: readI32(rawBase, offset: PWShmLayout.extensionDeliveredBytesOffset)),
                stage: UInt32(bitPattern: readI32(rawBase, offset: PWShmLayout.extensionDeliveryStageOffset)),
                nativeRc: readI32(rawBase, offset: PWShmLayout.extensionDeliveryNativeRcOffset),
                errno: readI32(rawBase, offset: PWShmLayout.extensionDeliveryErrnoOffset),
                cleanupStage: UInt32(bitPattern: readI32(rawBase, offset: PWShmLayout.extensionDeliveryCleanupStageOffset)),
                cleanupErrno: readI32(rawBase, offset: PWShmLayout.extensionDeliveryCleanupErrnoOffset))
            : nil,
        readyWait: readyWait,
        sentinelWait: sentinelWait,
        graceWait: graceWait
    )
    if let failure = transferFailure {
        return .failure(failure, output)
    }
    return .success(output)
}

// MARK: - Layout helpers

func writeU32(_ base: UnsafeMutablePointer<UInt8>, offset: Int, _ value: UInt32) {
    base.advanced(by: offset).withMemoryRebound(to: UInt32.self, capacity: 1) { p in
        p.pointee = value
    }
}

func readI32(_ base: UnsafePointer<UInt8>, offset: Int) -> Int32 {
    return base.advanced(by: offset).withMemoryRebound(to: Int32.self, capacity: 1) { p in
        p.pointee
    }
}

func loadAcquire(_ base: UnsafePointer<UInt8>, offset: Int) -> UInt32 {
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

func readI64(_ base: UnsafePointer<UInt8>, offset: Int) -> Int64 {
    UnsafeRawPointer(base.advanced(by: offset)).load(as: Int64.self)
}
/// Caller has acquired slot.completed. Do not invoke this for interrupted slots.
func decodeExecObservation(_ base: UnsafePointer<UInt8>, childPid: Int32) -> (PWExecObservation?, String?) {
    let marker = readI32(base, offset: PWShmLayout.slotExecValidOffset)
    if marker == 0 { return (nil, nil) }
    func bad(_ detail: String) -> (PWExecObservation?, String?) { (nil, "malformed completed exec payload: " + detail) }
    guard marker == 1, childPid > 0 else { return bad("valid marker or child PID") }
    func word(_ offset: Int) -> Int32 { readI32(base, offset: offset) }
    func optional(_ offset: Int) -> Int32? { let v = word(offset); return v == 0 ? nil : v }
    func fault(_ offset: Int) -> UInt32? { let v = UInt32(bitPattern: word(offset)); return v == 0 ? nil : v }
    let stop = word(PWShmLayout.slotExecCollectionStopOffset)
    let cleanup = word(PWShmLayout.slotExecCleanupStateOffset)
    let reap = word(PWShmLayout.slotExecReapStopOffset)
    let deadline = word(PWShmLayout.slotExecDeadlineKindOffset)
    let observed = word(PWShmLayout.slotExecLeaderExitObservedOffset)
    let stdout = word(PWShmLayout.slotExecStdoutEofOffset), stderr = word(PWShmLayout.slotExecStderrEofOffset)
    let fallback = word(PWShmLayout.slotExecFallbackPresentOffset)
    guard (1...4).contains(stop), (1...3).contains(cleanup), (1...6).contains(reap),
          (0...2).contains(deadline), [0, 1].contains(observed), [0, 1].contains(stdout),
          [0, 1].contains(stderr), [0, 1].contains(fallback) else { return bad("unknown enum or boolean") }
    if cleanup != 3 && [PWShmLayout.slotExecGroupTargetOffset, PWShmLayout.slotExecGroupSignalOffset,
                        PWShmLayout.slotExecGroupRcOffset, PWShmLayout.slotExecGroupErrnoOffset].contains(where: { word($0) != 0 }) {
        return bad("group fields without request")
    }
    if fallback == 0 && [PWShmLayout.slotExecFallbackTargetOffset, PWShmLayout.slotExecFallbackSignalOffset,
                        PWShmLayout.slotExecFallbackRcOffset, PWShmLayout.slotExecFallbackErrnoOffset].contains(where: { word($0) != 0 }) {
        return bad("fallback fields without call")
    }
    let waitRC = word(PWShmLayout.slotExecReapWaitRcOffset)
    if waitRC != childPid && word(PWShmLayout.slotExecReapStatusOffset) != 0 { return bad("status without child wait return") }
    if waitRC != -1 && word(PWShmLayout.slotExecReapWaitErrnoOffset) != 0 { return bad("errno without failed wait") }
    func request(_ target: Int, _ signal: Int, _ rc: Int, _ error: Int) -> PWExecSignalRequest {
        PWExecSignalRequest(target: word(target), signal: word(signal), rc: word(rc), errno: word(rc) == -1 ? word(error) : optional(error))
    }
    let collection = PWExecCollectionObservation(
        stop_reason: ["leader_exit_and_eof", "deadline", "observation_error", "clock_fault"][Int(stop - 1)],
        leader_exit_observed: observed == 1,
        stdout: PWExecStreamObservation(eof: stdout == 1, read_errno: optional(PWShmLayout.slotExecStdoutReadErrnoOffset), poll_revents: optional(PWShmLayout.slotExecStdoutPollReventsOffset)),
        stderr: PWExecStreamObservation(eof: stderr == 1, read_errno: optional(PWShmLayout.slotExecStderrReadErrnoOffset), poll_revents: optional(PWShmLayout.slotExecStderrPollReventsOffset)),
        deadline_kind: deadline == 0 ? nil : ["child", "plan"][Int(deadline - 1)],
        waitid_errno: optional(PWShmLayout.slotExecWaitidErrnoOffset), poll_errno: optional(PWShmLayout.slotExecPollErrnoOffset),
        clock_fault: fault(PWShmLayout.slotExecCollectionClockFaultOffset))
    let cleanupValue = PWExecCleanupObservation(state: ["not_requested", "ownership_unconfirmed", "requested"][Int(cleanup - 1)],
        group_request: cleanup == 3 ? request(PWShmLayout.slotExecGroupTargetOffset, PWShmLayout.slotExecGroupSignalOffset, PWShmLayout.slotExecGroupRcOffset, PWShmLayout.slotExecGroupErrnoOffset) : nil,
        leader_fallback: fallback == 1 ? request(PWShmLayout.slotExecFallbackTargetOffset, PWShmLayout.slotExecFallbackSignalOffset, PWShmLayout.slotExecFallbackRcOffset, PWShmLayout.slotExecFallbackErrnoOffset) : nil)
    let reapValue = PWExecReapObservation(stop_reason: ["reaped", "wait_error", "ownership_unconfirmed", "group_request_failed", "clock_fault", "deadline"][Int(reap - 1)],
        last_wait: PWExecWaitObservation(rc: waitRC, errno: waitRC == -1 ? word(PWShmLayout.slotExecReapWaitErrnoOffset) : nil,
            status: waitRC == childPid ? word(PWShmLayout.slotExecReapStatusOffset) : nil), clock_fault: fault(PWShmLayout.slotExecReapClockFaultOffset))
    return (PWExecObservation(collection: collection, cleanup: cleanupValue, reap: reapValue), nil)
}

func decodeFreshRead(_ base: UnsafePointer<UInt8>) -> PWRunnerFreshRead {
    func i(_ offset: Int) -> Int32 { readI32(base, offset: offset) }
    let opened = i(PWShmLayout.slotAccessOpenRcOffset)
    guard opened >= 0 else { return PWRunnerFreshRead(open_rc: opened, open_errno: i(PWShmLayout.slotAccessOpenErrnoOffset)) }
    let readRC = readI64(base, offset: PWShmLayout.slotAccessReadRcOffset)
    let statRC = i(PWShmLayout.slotAccessStatRcOffset)
    let closeRC = i(PWShmLayout.slotAccessCloseRcOffset)
    let identity: PWFileIdentity? = statRC == 0 ? PWFileIdentity(
        device: UInt64(bitPattern: readI64(base, offset: PWShmLayout.slotAccessDeviceOffset)),
        inode: UInt64(bitPattern: readI64(base, offset: PWShmLayout.slotAccessInodeOffset)),
        mode: UInt32(bitPattern: i(PWShmLayout.slotAccessModeOffset)),
        uid: UInt32(bitPattern: i(PWShmLayout.slotAccessUidOffset)), gid: UInt32(bitPattern: i(PWShmLayout.slotAccessGidOffset))) : nil
    let content: String? = readRC >= 0 && readRC <= PWShmLayout.freshReadBytes
        ? (0..<Int(readRC)).map { String(format: "%02x", base[PWShmLayout.slotAccessBytesOffset + $0]) }.joined() : nil
    return PWRunnerFreshRead(open_rc: opened, read_rc: readRC, read_errno: readRC < 0 ? i(PWShmLayout.slotAccessReadErrnoOffset) : nil,
        stat_rc: statRC, stat_errno: statRC != 0 ? i(PWShmLayout.slotAccessStatErrnoOffset) : nil, identity: identity,
        close_rc: closeRC, close_errno: closeRC != 0 ? i(PWShmLayout.slotAccessCloseErrnoOffset) : nil, content_hex: content)
}

func decodeFreshWrite(_ slot: UnsafePointer<UInt8>) -> PWRunnerFreshWrite {
    let base = slot.advanced(by: PWShmLayout.slotFreshWriteOffset)
    func i(_ offset: Int) -> Int32 { readI32(base, offset: offset) }
    func optional(_ value: Int32) -> Int32? { value == -2 ? nil : value }
    func error(_ rc: Int32, _ offset: Int) -> Int32? { rc == -1 ? i(offset) : nil }
    func metadata(_ offset: Int) -> PWRunnerFileStat? {
        let p = base.advanced(by: offset)
        let rc = readI32(p, offset: PWShmLayout.fileStatRcOffset)
        if rc == -2 { return nil }
        let identity = rc == 0 ? PWFileIdentity(
            device: UInt64(bitPattern: readI64(p, offset: PWShmLayout.fileStatDeviceOffset)),
            inode: UInt64(bitPattern: readI64(p, offset: PWShmLayout.fileStatInodeOffset)),
            mode: UInt32(bitPattern: readI32(p, offset: PWShmLayout.fileStatModeOffset)),
            uid: UInt32(bitPattern: readI32(p, offset: PWShmLayout.fileStatUidOffset)),
            gid: UInt32(bitPattern: readI32(p, offset: PWShmLayout.fileStatGidOffset))) : nil
        return PWRunnerFileStat(rc: rc,
            errno: rc == -1 ? readI32(p, offset: PWShmLayout.fileStatErrnoOffset) : nil,
            identity: identity, size: rc == 0 ? readI64(p, offset: PWShmLayout.fileStatSizeOffset) : nil)
    }
    let opened = i(PWShmLayout.freshWriteOpenRcOffset)
    let truncated = i(PWShmLayout.freshWriteTruncateRcOffset)
    let written = readI64(base, offset: PWShmLayout.freshWriteWriteRcOffset)
    let closed = i(PWShmLayout.freshWriteCloseRcOffset)
    return PWRunnerFreshWrite(open_rc: opened, open_errno: error(opened, PWShmLayout.freshWriteOpenErrnoOffset),
        truncate_rc: optional(truncated), truncate_errno: error(truncated, PWShmLayout.freshWriteTruncateErrnoOffset),
        write_rc: written == -2 ? nil : written,
        write_errno: written == -1 ? i(PWShmLayout.freshWriteWriteErrnoOffset) : nil,
        close_rc: optional(closed), close_errno: error(closed, PWShmLayout.freshWriteCloseErrnoOffset),
        preopen_stat: metadata(PWShmLayout.freshWritePreopenStatOffset),
        opened_stat: metadata(PWShmLayout.freshWriteOpenedStatOffset),
        truncated_stat: metadata(PWShmLayout.freshWriteTruncatedStatOffset),
        written_stat: metadata(PWShmLayout.freshWriteWrittenStatOffset))
}
