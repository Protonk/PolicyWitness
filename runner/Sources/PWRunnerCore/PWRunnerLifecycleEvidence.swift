import Foundation
import Darwin

/// Host observation of one kill(2) request, not evidence of its delivery or cause.
/// JSON: runner_subprocess.termination_request.{signal,rc,errno}. All numbers
/// are signed 32-bit syscall values encoded as JSON integers (no units).
/// errno is captured immediately only when rc == -1; otherwise it is absent/null.
/// An absent/null request means no request. Structurally valid values are decoded
/// without a signal/errno allowlist. The client/controller forward this object.
struct PWRunnerTerminationRequest: Codable {
    let signal: Int32
    let rc: Int32
    let errno: Int32?

    init(signal: Int32, rc: Int32, errno: Int32?) {
        self.signal = signal
        self.rc = rc
        self.errno = errno
    }
}

/// One host-observed failed waitpid(2) call, including recovered interruptions.
/// JSON: runner_subprocess.wait_errors[].{stage,rc,errno}. stage is a string
/// (poll, exit_grace, after_termination); rc/errno are signed 32-bit integers.
/// Only rc == -1 produces a record, with errno captured before another call.
/// Unknown stage/errno values remain transportable. Empty array means no errors
/// observed; absent/null array means unavailable.
struct PWRunnerWaitError: Codable {
    let stage: String
    let rc: Int32
    let errno: Int32

    init(stage: String, rc: Int32, errno: Int32) {
        self.stage = stage
        self.rc = rc
        self.errno = errno
    }
}

/// Host-observed UTF-8 policy transfer failure; counts are writes, not child reads.
/// See tests/FAILURE-PROPAGATION-CONTRACT.md for field validity and JSON semantics.
/// Timer observation; byte counts are writes accepted, not child reads.
struct PWWorkerPolicyTransferTimeout: Codable {
    var budget_ms: Int
    var elapsed_ms: UInt64
    var bytes_written: Int
    var bytes_expected: Int
}
struct PWWorkerPolicyTransferError: Codable {
    var errno: Int32
    var bytes_written: Int
    var bytes_expected: Int
}
/// Worker publications. Numeric codes are open, never Codable enums.
struct PWWorkerProgress: Codable {
    var raw: UInt32
    var operation: UInt32
    var stage: UInt32
    var index: UInt32?
}
struct PWWorkerFailure: Codable {
    var operation: UInt32
    var code: UInt32
    var native_kind: UInt32
    var native_result: Int32?
    var errno: Int32?
    var index: UInt32?
    var detail: UInt32
}
struct PWWorkerReadiness: Codable {
    var rc: Int32
    var errno: Int32?
}
struct PWWorkerDiagnostic: Codable {
    var state: UInt32
    var status: String
    var length: UInt32?
    var text: String?
}
/// The worker's EOF receipt for the policy pipe: the host's expected byte count
/// (its immutable header input) beside the count the worker read at EOF. Present
/// only when the worker published it, which happens before the length comparison;
/// a header refusal, read error or overflow publishes none. Equal counts establish
/// length agreement with the submission, not content identity, compilation,
/// application or kernel effect. Absence establishes nothing about delivery.
struct PWWorkerPolicyRead: Codable, Equatable {
    var bytes_expected: Int
    var bytes_received: Int
}
/// The worker's fixed source buffer less its terminating NUL (PW_SHM_POLICY_BYTES - 1),
/// the bound on both receipt counts. Stated here because the client target compiles
/// this file without the layout mirror; `PolicyTransferTests` pins agreement with
/// `PWShmLayout.policyBytes`.
let policyReceiptCapacityBytes = 262_143
struct PWWorkerEvidence: Codable {
    /// Host-selected source identity, not proof that a child reached ABI validation.
    var abi_identity: String
    var progress: PWWorkerProgress?
    var failure_publication: UInt32
    var failure_state: String
    var failure: PWWorkerFailure?
    var readiness: PWWorkerReadiness?
    var diagnostic: PWWorkerDiagnostic
    var policy_read: PWWorkerPolicyRead? = nil
}

/// One host wait measured on CLOCK_MONOTONIC: its allowance, the elapsed time
/// when it stopped and why it stopped. `excluded_ms` is time the wait does not
/// charge (synchronous phase collection inside the sentinel wait); the
/// allowance consumed is `elapsed_ms - excluded_ms`. `clock_unavailable` means
/// the clock failed or ran backwards and the wait fell back to a bounded number
/// of fixed sleeps; `setup_failed` means the nonblocking prerequisite could not
/// be established and no wait was attempted. Elapsed time is absent when the
/// clock could not supply it, and `clock_fault` says the clock failed or ran
/// backwards during the wait. A stop names when the host moved on, not when a
/// child ended.
struct PWHostWait: Codable, Equatable {
    var budget_ms: Int
    var elapsed_ms: UInt64?
    var stop: String
    var excluded_ms: UInt64?
    var native_errno: Int32?
    var clock_fault: Bool
}

struct PWRunnerSubprocess: Codable {
    var pid: Int
    /// JSON integers, meaningful only after waitpid returned this child's PID.
    /// Both may be absent/null when status was not obtained; zero is a real exit.
    var term_signal: Int?
    var exit_code: Int?
    var partial_steps: Bool
    /// Worker publication snapshot; absent before spawn.
    var worker_evidence: PWWorkerEvidence? = nil
    /// Host transfer observation independent of any child publication.
    var policy_transfer_timeout: PWWorkerPolicyTransferTimeout? = nil
    var policy_transfer_error: PWWorkerPolicyTransferError? = nil
    /// Host read of the ready byte; false does not prove compilation failed.
    var ready_byte_received: Bool?
    /// Final acquire observation of done after cleanup, not successful application.
    /// poll_stop_reason separately retains the reason the polling stage ended.
    var done_observed: Bool?
    /// Host string: done, child_reaped, sentinel_deadline, wait_error, policy_write_error, or policy_transfer_deadline.
    /// Identifies why polling stopped; later cleanup must not rewrite it.
    /// Only sentinel_deadline establishes exhaustion of the polling budget.
    /// Unknown strings survive decoding; they do not imply a known condition.
    var poll_stop_reason: String?
    /// Host performed the release-store of exit_requested; not worker receipt.
    var exit_requested: Bool?
    var termination_request: PWRunnerTerminationRequest?
    /// True only when waitpid actually returned this PID. False is explicitly
    /// unconfirmed disposition, distinct from an absent/null observation.
    var reaped: Bool?
    var wait_errors: [PWRunnerWaitError]?
    /// Host facts recorded where the host acts (tests/FAILURE-PROPAGATION-CONTRACT.md,
    /// "Worker disposition record"): why exit was requested, how the exit-grace
    /// wait ended, and whether the final reads followed a confirmed reap.
    /// Absence is unreported, not observed false.
    var cleanup_trigger: String? = nil
    var grace_end: String? = nil
    var collection_basis: String? = nil
    /// Measured host waits: readiness hint, publication (sentinel) and exit grace.
    /// Absent when the stage did not run.
    var ready_wait: PWHostWait? = nil
    var sentinel_wait: PWHostWait? = nil
    var exit_grace_wait: PWHostWait? = nil
    /// The canonical lifecycle account, resolved once by the host. Mandatory
    /// whenever this object is present.
    var disposition: PWDispositionRecord? = nil

    init(
        pid: Int,
        term_signal: Int? = nil,
        exit_code: Int? = nil,
        partial_steps: Bool,
        ready_byte_received: Bool? = nil,
        done_observed: Bool? = nil,
        poll_stop_reason: String? = nil,
        exit_requested: Bool? = nil,
        termination_request: PWRunnerTerminationRequest? = nil,
        reaped: Bool? = nil,
        wait_errors: [PWRunnerWaitError]? = nil
    ) {
        self.pid = pid
        self.term_signal = term_signal
        self.exit_code = exit_code
        self.partial_steps = partial_steps
        self.ready_byte_received = ready_byte_received
        self.done_observed = done_observed
        self.poll_stop_reason = poll_stop_reason
        self.exit_requested = exit_requested
        self.termination_request = termination_request
        self.reaped = reaped
        self.wait_errors = wait_errors
    }
}

extension PWRunnerTerminationRequest: Equatable {}
