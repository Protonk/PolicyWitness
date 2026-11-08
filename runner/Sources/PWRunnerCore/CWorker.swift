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
 *  10. Release-store `exit_requested = 1`; waitpid samples under the grace
 *      allowance, waiting between them for the ready pipe's hangup at the
 *      worker's exit; SIGKILL fallback if the worker hangs.
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
    static let abiIdentityHex = "564477bc0b94cbaf0d99ae4f3cd82f2cd2ec20298c60218e4542c551b68298ee"
    static let abiIdentity: [UInt8] = [0x56, 0x44, 0x77, 0xbc, 0x0b, 0x94, 0xcb, 0xaf, 0x0d, 0x99, 0xae, 0x4f, 0x3c, 0xd8, 0x2f, 0x2c, 0xd2, 0xec, 0x20, 0x29, 0x8c, 0x60, 0x21, 0x8e, 0x45, 0x42, 0xc5, 0x51, 0xb6, 0x82, 0x98, 0xee]
    // END GENERATED WORKER IDENTITY

    static let abiMagic: UInt32 = 0x50574944
    static let abiIdentityBytes: Int = 32

    static let headerBytes: Int     = 768
    static let maxPhases: Int = 16
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
    static let authoritySetupBytes: Int = 832

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
        headerBytes + maxSteps * slotBytes + maxParams * paramBytes + captureHeaderBytes + captureBytes + evidenceHeaderBytes + diagnosticBytes + authoritySetupBytes

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

    // Policy delivery acknowledgement: the host's expected byte count (input) and
    // the worker's EOF receipt (count plus its publication flag).
    static let policyBytesExpectedOffset: Int = 136
    static let policyBytesReceivedOffset: Int = 140
    static let policyReadPublishedOffset: Int = 144
    // Actor-form inputs and publications carved from the reserved bytes and
    // the header tail.
    static let actorModeOffset: Int = 148
    static let actorIndexOffset: Int = 152
    static let actorSetupOffset: Int = 156
    static let activationOffset: Int = 160
    static let activationObservedOffset: Int = 164
    static let lifetimeCutoffTicksOffset: Int = 168
    static let policyHashPublishedOffset: Int = 176
    static let authorityStatusOffset: Int = 180
    static let authorityDetailOffset: Int = 184
    static let nativeSymbolsOffset: Int = 188
    static let policyReceivedSha256Offset: Int = 704
    static let phaseCountOffset: Int = 96
    static let phaseRecordsOffset: Int = 192
    static let phaseFirstSlotOffset: Int = 0
    static let phaseEndSlotOffset: Int = 4
    static let phaseArrivedOffset: Int = 8
    static let phaseAcknowledgedOffset: Int = 12
    static let phaseCompletedOffset: Int = 16
    static let phaseGlobalPhaseOffset: Int = 20

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
    static let authoritySetupOffset: Int = evidenceOffset + evidenceHeaderBytes + diagnosticBytes
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
    // Actor-form extension operands and publications.
    static let extTargetBytes: Int = 1024
    static let slotExtFamilyOffset: Int = 6480
    static let slotExtAuthorityOffset: Int = 6484
    static let slotExtTokenIndexOffset: Int = 6488
    static let slotExtDeliveryIndexOffset: Int = 6492
    static let slotExtHandleIndexOffset: Int = 6496
    static let slotExtRecipientIndexOffset: Int = 6500
    static let slotExtLastUseOffset: Int = 6504
    static let slotExtTokenLengthOffset: Int = 6508
    static let slotExtCustodyStatusOffset: Int = 6512
    static let slotExtTransferStatusOffset: Int = 6516
    static let slotExtTargetOffset: Int = 6524
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
/// `mapAttemptKindOrNil` in CWorkerRequestPlanning.swift. See docs/PolicyWitness.md →
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
    case extensionIssue = 14
    case extensionTransfer = 15
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
    /// Actor-form extension operands: the normalized plan's global indexes and
    /// the exact submitted issue path. Nil for every other attempt.
    var extensionOperands: CWorkerExtensionOperands? = nil

    init(stepId: String, attemptKind: PWAttemptKind, target: String, args: [String] = [],
         extensionOperands: CWorkerExtensionOperands? = nil) {
        self.stepId = stepId
        self.attemptKind = attemptKind
        self.target = target
        self.args = args
        self.extensionOperands = extensionOperands
    }
}

/// Host inputs for an actor-form extension action, written into the slot.
struct CWorkerExtensionOperands: Equatable {
    var family: UInt32 = 1
    /// 0 read, 1 read_write (the transient channel's authority values).
    var authority: UInt32 = 0
    var tokenIndex: UInt32 = 0
    var deliveryIndex: UInt32 = 0
    var handleIndex: UInt32 = 0
    var recipientIndex: UInt32 = 0
    /// This action is the last declared use of its delivery.
    var lastUse = false
    var target: String = ""
}

/// Worker publications of an actor-form extension action, read once completed.
struct CWorkerExtensionPublication: Equatable {
    /// Measured token length of a nonnull issue; 0 otherwise.
    var tokenLength: UInt32
    /// PW_CUSTODY_*: 0 none, 1 accepted, 2 rejected, 3 timeout, 4 not published, 5 clock fault.
    var custodyStatus: UInt32
    /// PW_TRANSFER_ACK_*: 0 none, 1 delivered, 2 custody unavailable, 3 recipient
    /// rejected, 4 recipient timeout, 5 recipient unavailable, 6 request invalid,
    /// 7 host timeout, 8 clock fault.
    var transferStatus: UInt32
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
    /// The actor form's 1-based global phase ordinal for this visit; the
    /// legacy form leaves it nil and the driver writes index + 1.
    var globalPhase: Int? = nil
    init(firstSlot: Int, endSlot: Int, globalPhase: Int? = nil) {
        self.firstSlot = firstSlot; self.endSlot = endSlot; self.globalPhase = globalPhase
    }
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
    /// Actor form: the descriptor of this actor's authority region, passed as
    /// the child's descriptor 5.
    var authorityFD: Int32? = nil
    var authorityRequired = false
    var authorityRecorder: AuthoritySetupRecorder? = nil
    /// Actor-form inputs: PW_ACTOR_MODE_* (0 legacy), the actor's index and the
    /// shared absolute continuous-clock cutoff (0 none).
    var actorMode: UInt32 = 0
    var actorIndex: UInt32 = 0
    var lifetimeCutoffTicks: UInt64 = 0
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
    var extensionPublication: CWorkerExtensionPublication? = nil
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
    /// Measured host waits; nil when the stage did not run.
    var readyWait: PWHostWait? = nil
    var sentinelWait: PWHostWait? = nil
    var graceWait: PWHostWait? = nil
    /// Actor-form publications: PW_ACTOR_SETUP_* (0 none), the latest
    /// acknowledged activation and the worker's hash of the policy bytes it read.
    var actorSetup: UInt32 = 0
    var activationObserved: UInt32 = 0
    var policyReceivedSha256: String? = nil
    /// PW_AUTHORITY_SETUP_* with its stage or reason, and the resolved native
    /// entry points (PW_NATIVE_SYMBOL_* bits); zero for legacy workers.
    var authorityStatus: UInt32 = 0
    var authorityDetail: UInt32 = 0
    var nativeSymbols: UInt32 = 0
    var authoritySetup: PWRunnerAuthorityScope? = nil
    var ownedReap: PWOwnedReapObservation? = nil
}

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
    /// The monotonic clock, the bounded sleep and the bounded readability wait
    /// host waits use. Tests may drive them; production reads CLOCK_MONOTONIC,
    /// nanosleeps and polls.
    var clock: () -> UInt64? = MonotonicDeadline.now
    var sleep: (UInt64) -> Void = sleepNs
    var waitReadable: (Int32, UInt64) -> Void = waitReadableNs
    /// The bounded exit wait host grace uses; tests may drive it.
    var waitExit: (ExitWatch, UInt64) -> ExitWatchOutcome = waitExitNs
}

/// How one bounded wait for a child's exit ended.
enum ExitWatchOutcome { case notified, timedOut, unusable }

/// The host's handle for waiting on one child's exit without a timer sleep.
/// `fd` is the host's read end of the worker's readiness pipe, whose only
/// write end the worker holds until it exits (its exec children spawn with
/// close-on-exec default), so hangup marks the worker's exit by any cause;
/// -1 when the session holds none. `usable` false means the primitive cannot
/// inform this wait and the grace falls back to the sleeping poll. `notified`
/// records that the hangup was seen; it never substitutes for a reap.
struct ExitWatch {
    let fd: Int32
    var usable: Bool
    var notified = false

    init(fd: Int32) {
        self.fd = fd
        usable = fd >= 0
    }
}

/// One host wait measured as elapsed monotonic time against an allowance.
/// Progress, interrupted calls and sleep overruns never renew it; each sleep,
/// readability wait or exit wait is bounded by the remaining allowance. Excluded intervals
/// (synchronous phase collection) extend the allowance by exactly their
/// measured length. When the clock fails or runs backwards the wait spends only
/// the last remaining allowance in nominal sleeps or waits; it never restores
/// time already charged.
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
        expiredAfterSleeping(atMost: pollNs)
    }

    /// Like expiredAfterSleeping, bounded by `atMost` instead of the poll period.
    mutating func expiredAfterSleeping(atMost ns: UInt64) -> Bool {
        _ = remainingNs()
        if fallbackRemainingNs == 0 { return true }
        let sleep = min(max(1, ns), fallbackRemainingNs)
        // If the next clock read fails, this requested sleep is already charged.
        // A working clock measures the actual interval on its next reading.
        fallbackRemainingNs -= sleep
        calls.sleep(sleep)
        return false
    }

    /// Decide whether the allowance is exhausted; otherwise wait for `fd` to
    /// become readable for at most the remaining allowance (bounded by the poll
    /// period) and report that the wait continues. An early return is a pass.
    mutating func expiredAfterWaiting(readable fd: Int32) -> Bool {
        _ = remainingNs()
        if fallbackRemainingNs == 0 { return true }
        let wait = min(pollNs, fallbackRemainingNs)
        // As with a sleep: if the next clock read fails, this requested wait is already charged.
        fallbackRemainingNs -= wait
        calls.waitReadable(fd, wait)
        return false
    }

    /// Decide whether the allowance is exhausted; otherwise wait for the
    /// child's exit notification for at most the remaining allowance (bounded
    /// by the poll period) and report how the wait ended. Charged like a sleep.
    mutating func expiredAfterWaiting(exit watch: ExitWatch) -> (expired: Bool, outcome: ExitWatchOutcome?) {
        _ = remainingNs()
        if fallbackRemainingNs == 0 { return (true, nil) }
        let wait = min(pollNs, fallbackRemainingNs)
        // As with a sleep: if the next clock read fails, this requested wait is already charged.
        fallbackRemainingNs -= wait
        let outcome = calls.waitExit(watch, wait)
        return (false, outcome)
    }

    /// A short settle sleep after a notification that preceded reapability.
    static let exitSettleNs: UInt64 = 100_000
    static let exitSettleSleeps = 10

    /// The clock time one re-sampling may spend before the first sleep after a publication.
    static let resampleBudgetNs: UInt64 = 100_000

    /// Bounds the re-sampling loop's iterations when the clock stops advancing;
    /// a working clock ends the budget long before it is reached.
    static let resampleSampleCap = 16_384

    /// Before the first sleep after a publication whose answer arrives within
    /// microseconds, re-sample `answered` for at most `budgetNs` of clock time,
    /// never beyond the remaining allowance, then sleep as usual when it is
    /// still false. The re-sampling is charged like any pass; an unusable
    /// clock, an exhausted allowance or the sample cap ends it at once.
    mutating func expiredAfterResampling(_ answered: () -> Bool, budgetNs: UInt64) -> Bool {
        if let start = elapsedNs(), fallbackRemainingNs > 0 {
            let window = min(budgetNs, fallbackRemainingNs)
            var samples = 0
            while !answered() {
                samples += 1
                guard samples < HostWaitClock.resampleSampleCap, let now = elapsedNs(), now - start < window else { break }
            }
            if answered() { return false }
        }
        return expiredAfterSleeping()
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
    var ownedReap: PWOwnedReapObservation? = nil
    var departureRequested = false
    var ownershipUnbroken = true
    private var interruptRetries = 2
    private var captureOrdinal: UInt64 = 0
    /// One sequence for actual activation stores, the single owned reap, and
    /// gate snapshots. Bounded by the admitted schedule, never by poll count.
    mutating func nextCaptureOrdinal() -> UInt64 {
        captureOrdinal += 1
        return captureOrdinal
    }

    init(pid: pid_t, calls: ChildProcessCalls) {
        self.pid = pid
        self.calls = calls
    }

    mutating func wait(options: Int32, stage: String) -> ChildWaitObservation {
        if status != nil { return .reaped }
        while true {
            var candidate: Int32 = 0
            let rc = calls.wait(pid, &candidate, options)
            let savedErrno = rc == -1 ? errno : nil
            if rc == pid {
                status = candidate
                ownedReap = PWOwnedReapObservation(pid: Int(pid), native_rc: rc, raw_status: candidate,
                    stage: stage, observed_ns: calls.clock(), ownership_unbroken: ownershipUnbroken,
                    departure_requested: departureRequested, capture_ordinal: nextCaptureOrdinal())
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
            ownershipUnbroken = false
            return .failed
        }
    }

    mutating func terminate() {
        guard status == nil && !childUnavailable else { return }
        departureRequested = true
        let rc = calls.kill(pid, SIGKILL)
        let savedErrno = rc == -1 ? errno : nil
        terminationRequest = PWRunnerTerminationRequest(signal: SIGKILL, rc: rc, errno: savedErrno)
        _ = wait(options: rc == 0 ? 0 : WNOHANG, stage: "after_termination")
    }
}

func runCWorker(_ input: CWorkerInput, processCalls: ChildProcessCalls,
                transferCalls: PolicyTransferCalls = PolicyTransferCalls(),
                postApplied: CWorkerPostAppliedHook? = nil, phaseBoundary: CWorkerPhaseHook? = nil) -> CWorkerRunResult {
    // The single-worker adapter: one owned session, the legacy polling loop
    // over its primitives, then its cleanup and output. Setup refusals before
    // spawn carry no output; a transfer failure after spawn keeps the child's
    // observations.
    let session = ActorSession(input, processCalls: processCalls, transferCalls: transferCalls)
    guard session.spawned else { return .failure(session.failure!) }
    defer { session.tearDown() }
    let pid = session.pid

    // ---- Poll applied, fire postApplied hook, then poll done. Also
    // watch for the worker exiting WITHOUT flipping `done` (a sandbox
    // kill mid-probe, a crash, or a pre-apply death): there is nothing
    // left to wait for, so reap and stop immediately instead of spinning
    // the full sentinel deadline over a corpse.
    var sawApplied = false
    var nextPhase = 0
    if session.transferFailure == nil {
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
        // Set by a release store and cleared by the next wait, which re-samples
        // the next phase's arrival before its first sleep.
        var resampleArrival = false
        polling: while true {
            passes += 1
            if !sawApplied && session.appliedObserved {
                sawApplied = true
            }
            // Only the exact arrived phase may collect predictions. Planning and
            // collection occur while this worker is paused, after prior completion.
            if sawApplied && nextPhase < input.phases.count
                && session.applyRCIsZero
                && session.identityMatches
                && !session.doneObserved
                && session.arrived(nextPhase) {
                let index = nextPhase
                session.phaseOutputs[index].arrived = true
                session.checkPrematurePublication(index)
                session.observeAcknowledgement()
                if index > 0 && !session.completed(index - 1) {
                    session.phaseOutputs[index].violations.append("arrival_without_previous_completion")
                }
                if session.completed(index) {
                    session.phaseOutputs[index].violations.append("completion_before_release")
                }
                if !session.phaseOutputs[index].violations.isEmpty {
                    // Preserve the invalid boundary and stop collections. Normal
                    // done/death/deadline polling still owns terminal cleanup.
                    nextPhase = input.phases.count
                    continue
                }
                switch session.waitChild(stage: "poll") {
                case .reaped: session.pollStopReason = "child_reaped"; break polling
                case .failed: session.pollStopReason = "wait_error"; break polling
                case .pending: break
                }
                let hookStarted = clock.mark()
                if let hook = phaseBoundary { hook(pid, index) }
                else if index == 0, let hook = postApplied { hook(pid) }
                clock.excludeSince(hookStarted)
                session.phaseOutputs[index].collectionClosed = true
                session.checkPrematurePublication(index)
                // Collection may outlast the worker wait or lose the child. A
                // closed collection alone never authorizes a late release.
                switch session.waitChild(stage: "poll") {
                case .reaped: session.pollStopReason = "child_reaped"; break polling
                case .failed: session.pollStopReason = "wait_error"; break polling
                case .pending: break
                }
                if !session.doneObserved
                    && session.arrived(index)
                    && !session.acknowledged(index)
                    && !session.completed(index)
                    && (index == 0 || session.completed(index - 1))
                    && session.phaseOutputs[index].violations.isEmpty {
                    session.releaseVisit(index)
                    resampleArrival = true
                }
                nextPhase += 1
            }
            session.observeAcknowledgement()
            if session.doneObserved {
                session.pollStopReason = "done"
                break
            }
            // The worker may publish and exit between the samples above and
            // this wait. Retain this actual stop reason; final reconciliation
            // recovers immutable publications without inventing timely done.
            let elapsed = clock.elapsedNs()
            if elapsed.map({ $0 >= nextExitCheckNs }) ?? (passes % 25 == 1) {
                nextExitCheckNs = (elapsed ?? 0) + 50_000_000
                switch session.waitChild(stage: "poll") {
                case .reaped:
                    session.pollStopReason = "child_reaped"
                    break polling
                case .failed:
                    session.pollStopReason = "wait_error"
                    break polling
                case .pending:
                    break
                }
            }
            // done was read above: a publication observed as the allowance
            // runs out is done, not a deadline.
            if resampleArrival && nextPhase < input.phases.count {
                resampleArrival = false
                if clock.expiredAfterResampling({ session.arrived(nextPhase) }, budgetNs: HostWaitClock.resampleBudgetNs) { break }
                continue
            }
            resampleArrival = false
            if clock.expiredAfterSleeping() { break }
        }
        session.sentinelWait = clock.record(stop: session.pollStopReason, excluded: true)
    }

    // ---- Request worker exit (a no-op if it already died on its own), then
    // reap with grace and the SIGKILL fallback.
    session.requestExit()
    session.finishCleanup()
    let output = session.collectOutput()
    if let failure = session.transferFailure {
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

// MARK: - Misc helpers

// Shared with ValidatorClient.swift. Internal-scope so both
// drivers see the same helper without code duplication.
func sleepNs(_ ns: UInt64) {
    var ts = timespec(tv_sec: Int(ns / 1_000_000_000), tv_nsec: Int(ns % 1_000_000_000))
    _ = nanosleep(&ts, nil)
}

/// Wait at most `ns`, rounded up to whole milliseconds, for `fd` to become
/// readable. Readiness, timeout, an error and EINTR all return without retry;
/// the caller's clock charges whatever elapsed, so an early return is one more
/// pass, never progress.
func waitReadableNs(_ fd: Int32, _ ns: UInt64) {
    let ms = ns == 0 ? 0 : min((ns - 1) / 1_000_000 + 1, UInt64(Int32.max))
    var entry = pollfd(fd: fd, events: Int16(POLLIN), revents: 0)
    _ = poll(&entry, 1, Int32(ms))
}

/// Wait at most `ns`, rounded up to whole milliseconds, for the hangup of the
/// watched pipe. Hangup or readability (a byte or EOF) is a notification, an
/// invalid or failed descriptor makes the watch unusable, and a timeout or EINTR
/// is a timed-out pass the caller's clock charges. Never retried here.
func waitExitNs(_ watch: ExitWatch, _ ns: UInt64) -> ExitWatchOutcome {
    guard watch.usable && watch.fd >= 0 else { return .unusable }
    let ms = ns == 0 ? 0 : min((ns - 1) / 1_000_000 + 1, UInt64(Int32.max))
    var entry = pollfd(fd: watch.fd, events: Int16(POLLIN), revents: 0)
    let rc = poll(&entry, 1, Int32(ms))
    if rc < 0 { return errno == EINTR ? .timedOut : .unusable }
    if rc == 0 { return .timedOut }
    if entry.revents & Int16(POLLNVAL | POLLERR) != 0 { return .unusable }
    if entry.revents & Int16(POLLHUP | POLLIN) != 0 { return .notified }
    return .timedOut
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
