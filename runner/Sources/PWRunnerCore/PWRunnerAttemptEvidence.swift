import Foundation
import Darwin

struct PWRunnerFreshRead: Codable {
    var open_rc: Int32
    var open_errno: Int32?
    var read_rc: Int64?
    var read_errno: Int32?
    var stat_rc: Int32?
    var stat_errno: Int32?
    var identity: PWFileIdentity?
    var close_rc: Int32?
    var close_errno: Int32?
    var content_hex: String?
}
struct PWRunnerFileStat: Codable {
    var rc: Int32
    var errno: Int32?
    var identity: PWFileIdentity?
    var size: Int64?

    func evidenceProblem() -> String? {
        guard [-1, 0].contains(rc), rc == -1 ? errno != nil && errno! >= 0 : errno == nil,
              rc == 0 ? identity != nil && size != nil : identity == nil && size == nil else {
            return "file metadata lacks its native result or successful payload"
        }
        return nil
    }
}
struct PWRunnerFreshWrite: Codable {
    var open_rc: Int32
    var open_errno: Int32?
    var truncate_rc: Int32?
    var truncate_errno: Int32?
    var write_rc: Int64?
    var write_errno: Int32?
    var close_rc: Int32?
    var close_errno: Int32?
    var preopen_stat: PWRunnerFileStat?
    var opened_stat: PWRunnerFileStat?
    var truncated_stat: PWRunnerFileStat?
    var written_stat: PWRunnerFileStat?
}

/// Bounded observations from the completed exec slot. Collection is frozen before
/// termination requests; final wait facts concern only the owned leader.
struct PWExecStreamObservation: Codable {
    var eof: Bool
    var read_errno: Int32? = nil
    var poll_revents: Int32? = nil
}
struct PWExecCollectionObservation: Codable {
    var stop_reason: String
    var leader_exit_observed: Bool
    var stdout: PWExecStreamObservation
    var stderr: PWExecStreamObservation
    var deadline_kind: String? = nil
    var waitid_errno: Int32? = nil
    var poll_errno: Int32? = nil
    var clock_fault: UInt32? = nil
}
struct PWExecSignalRequest: Codable {
    var target: Int32
    var signal: Int32
    var rc: Int32
    var errno: Int32? = nil
}
struct PWExecCleanupObservation: Codable {
    var state: String
    var group_request: PWExecSignalRequest? = nil
    var leader_fallback: PWExecSignalRequest? = nil
}
struct PWExecWaitObservation: Codable {
    var rc: Int32
    var errno: Int32? = nil
    var status: Int32? = nil
}
struct PWExecReapObservation: Codable {
    var stop_reason: String
    var last_wait: PWExecWaitObservation
    var clock_fault: UInt32? = nil
}
struct PWExecObservation: Codable {
    var collection: PWExecCollectionObservation
    var cleanup: PWExecCleanupObservation
    var reap: PWExecReapObservation
}

extension PWRunnerAttemptResult {
    func execObservationEvidenceProblem() -> String? {
        if let execObservationDecodeProblem { return execObservationDecodeProblem }
        guard let value = exec_observation else { return nil } // absence remains unknown
        guard requested_kind == "exec", requested_action == "spawn", result_source == "worker",
              let pid = child_pid, pid > 0, pid <= Int(Int32.max),
              lifecycle?.summary == "completed" else { return "exec observation requires a published worker exec and positive child PID" }
        let c = value.collection, k = value.cleanup, r = value.reap, w = value.reap.last_wait
        func positive(_ n: Int32?) -> Bool { n == nil || n! > 0 }
        func streamValid(_ stream: PWExecStreamObservation) -> Bool {
            positive(stream.read_errno) && stream.read_errno != EINTR && stream.read_errno != EAGAIN
                && (stream.poll_revents == nil || (stream.poll_revents! >= Int32(Int16.min) && stream.poll_revents! <= Int32(Int16.max)
                    && (stream.poll_revents! & 0x28) != 0 && (stream.poll_revents! & 0x11) == 0))
                && !(stream.eof && (stream.read_errno != nil || stream.poll_revents != nil))
                && !(stream.read_errno != nil && stream.poll_revents != nil)
        }
        guard positive(c.waitid_errno), positive(c.poll_errno), c.waitid_errno != EINTR, c.poll_errno != EINTR,
              streamValid(c.stdout), streamValid(c.stderr), c.clock_fault != 0, r.clock_fault != 0 else {
            return "invalid exec collection scalar or stream observation"
        }
        let errors = c.waitid_errno != nil || c.poll_errno != nil || c.stdout.read_errno != nil
            || c.stderr.read_errno != nil || c.stdout.poll_revents != nil || c.stderr.poll_revents != nil
        if c.waitid_errno != nil && c.leader_exit_observed { return "waitid failure after previously observed leader exit" }
        if c.waitid_errno != nil && (c.poll_errno != nil || c.stdout.read_errno != nil || c.stderr.read_errno != nil
            || c.stdout.poll_revents != nil || c.stderr.poll_revents != nil) { return "waitid failure cannot share a later poll observation" }
        if c.poll_errno != nil && (c.stdout.read_errno != nil || c.stderr.read_errno != nil
            || c.stdout.poll_revents != nil || c.stderr.poll_revents != nil) { return "poll failure cannot share stream observations" }
        switch c.stop_reason {
        case "leader_exit_and_eof":
            guard c.leader_exit_observed, c.stdout.eof, c.stderr.eof, !errors, c.clock_fault == nil, c.deadline_kind == nil else { return "ordinary collection lacks leader exit and EOF" }
        case "deadline":
            guard ["child", "plan"].contains(c.deadline_kind ?? ""), !errors, c.clock_fault == nil else { return "invalid exec deadline observation" }
        case "observation_error":
            guard errors, c.clock_fault == nil, c.deadline_kind == nil else { return "exec observation error lacks a native observation" }
        case "clock_fault":
            guard c.clock_fault != nil, !errors, c.deadline_kind == nil else { return "exec clock stop lacks its local fault" }
        default: return "unknown exec collection stop"
        }
        func signalValid(_ request: PWExecSignalRequest, target: Int32) -> Bool {
            request.target == target && request.signal == SIGKILL && [-1, 0].contains(request.rc)
                && (request.rc == -1 ? request.errno != nil && request.errno! > 0 : request.errno == nil)
        }
        switch k.state {
        case "not_requested":
            guard c.stop_reason == "leader_exit_and_eof", k.group_request == nil, k.leader_fallback == nil else { return "no cleanup request contradicts collection stop" }
        case "ownership_unconfirmed":
            guard c.waitid_errno != nil, k.group_request == nil, k.leader_fallback == nil else { return "withheld cleanup lacks ownership failure" }
        case "requested":
            guard c.stop_reason != "leader_exit_and_eof", c.waitid_errno == nil,
                  let g = k.group_request, signalValid(g, target: -Int32(pid)) else { return "invalid exec group request" }
            let fallbackExpected = g.rc == -1 && g.errno != ESRCH
            guard fallbackExpected == (k.leader_fallback != nil) else { return "exec fallback disagrees with group result" }
            if let f = k.leader_fallback, !signalValid(f, target: Int32(pid)) { return "invalid exec leader fallback" }
        default: return "unknown exec cleanup state"
        }
        guard w.rc == -1 || w.rc == 0 || w.rc == Int32(pid),
              (w.rc == -1 ? w.errno != nil && w.errno! > 0 : w.errno == nil),
              (w.rc == Int32(pid)) == (w.status != nil) else { return "invalid exec last wait observation" }
        if let status = w.status {
            let bits = status & 0x7f
            let exit = bits == 0 ? Int((status >> 8) & 0xff) : -1
            let signal = bits != 0 && bits != 0x7f ? Int(bits) : 0
            guard child_exit_code == exit, child_term_signal == signal else { return "exec wait status disagrees with leader fields" }
        } else if child_exit_code != -1 || child_term_signal != 0 { return "exec leader status lacks confirmed wait" }
        let failedGroup = k.group_request.map { $0.rc == -1 && $0.errno != ESRCH } ?? false
        switch r.stop_reason {
        case "reaped":
            guard w.rc == Int32(pid) else { return "exec reap lacks leader return" }
        case "wait_error":
            guard w.rc == -1, w.errno != EINTR else { return "exec wait error lacks terminal errno" }
        case "ownership_unconfirmed", "group_request_failed", "clock_fault", "deadline":
            guard w.rc == 0 || (w.rc == -1 && w.errno == EINTR) else { return "local reap stop cannot replace native wait result" }
            if r.stop_reason == "ownership_unconfirmed" {
                guard k.state == "ownership_unconfirmed" else { return "reap ownership stop lacks ownership failure" }
            } else if r.stop_reason == "group_request_failed" {
                guard k.state != "ownership_unconfirmed", failedGroup else { return "reap group stop lacks failed request" }
            } else {
                guard k.state != "ownership_unconfirmed", !failedGroup else { return "reap stop changes ownership/group branch priority" }
                guard (r.stop_reason == "clock_fault") == (r.clock_fault != nil) else { return "reap local fault disagrees with stop" }
            }
        default: return "unknown exec reap stop"
        }
        return nil
    }
}

struct PWRunnerAttemptResult: Codable {
    /// Submitted intent, not proof that the named native operation ran. See
    /// the "Worker evidence contract" in tests/FAILURE-PROPAGATION-CONTRACT.md
    /// for PW status versus missing reasons.
    var requested_kind: String? = nil
    var requested_action: String? = nil
    var result_source: String? = nil
    var missing_reason: String? = nil
    /// Projection of this step's disposition claims. It is the evidence for
    /// whether a `no_completed_result`/`slot_incomplete` step started.
    var lifecycle: PWAttemptLifecycle? = nil
    /// PW's attempt status, not a raw syscall return.
    var fresh_read: PWRunnerFreshRead? = nil
    var fresh_write: PWRunnerFreshWrite? = nil
    var exec_observation: PWExecObservation? = nil
    // Host-local corruption diagnostic, checked by ordinary-reply encoding.
    var execObservationDecodeProblem: String? = nil
    var rc: Int
    var errno: Int?
    var outcome: String
    var error: String?
    var requested_path: String?
    /// Host-resolved forms of the attempt target; absent for non-path attempts.
    var path_diagnostics: PWRunnerAttemptPathDiagnostics?
    var observed_path: String?

    /// Exec-attempt outputs. All five are nil for non-exec attempts and
    /// are emitted as explicit JSON null (when populated) or omitted
    /// entirely (when nil) so a sysctl/file/mach result envelope does
    /// not grow five new null fields it has no use for.
    ///
    /// `child_pid > 0` means `posix_spawn` produced a child; it does not
    /// establish reaping. Unconfirmed status keeps exit -1 / signal 0.
    /// Attempt rc may fail independently of a natural leader exit.
    /// `child_pid == 0` means
    /// spawn/setup did not produce a child; this alone does not identify
    /// the cause. `errno` carries the applicable native error in
    /// that case. comparisonEvidence reads `child_pid` to distinguish
    /// spawn failure from a child non-zero exit. EPERM/EACCES without
    /// a child remain ambiguous: execute permissions can also prevent
    /// spawning.
    var child_pid: Int?
    var child_exit_code: Int?
    var child_term_signal: Int?
    var stdout: String?
    var stderr: String?

    init(
        rc: Int,
        errno: Int? = nil,
        outcome: String,
        error: String? = nil,
        requested_path: String? = nil,
        path_diagnostics: PWRunnerAttemptPathDiagnostics? = nil,
        observed_path: String? = nil,
        child_pid: Int? = nil,
        child_exit_code: Int? = nil,
        child_term_signal: Int? = nil,
        stdout: String? = nil,
        stderr: String? = nil,
        exec_observation: PWExecObservation? = nil
    ) {
        self.rc = rc
        self.errno = errno
        self.outcome = outcome
        self.error = error
        self.requested_path = requested_path
        self.path_diagnostics = path_diagnostics
        self.observed_path = observed_path
        self.child_pid = child_pid
        self.child_exit_code = child_exit_code
        self.child_term_signal = child_term_signal
        self.stdout = stdout
        self.stderr = stderr
        self.exec_observation = exec_observation
    }

    enum CodingKeys: String, CodingKey {
        case requested_kind, requested_action
        case result_source, missing_reason, lifecycle
        case rc, fresh_read, fresh_write, exec_observation
        case errno
        case outcome
        case error
        case requested_path
        case path_diagnostics
        case observed_path
        case child_pid
        case child_exit_code
        case child_term_signal
        case stdout
        case stderr
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encodeIfPresent(requested_kind, forKey: .requested_kind)
        try container.encodeIfPresent(requested_action, forKey: .requested_action)
        try container.encodeIfPresent(result_source, forKey: .result_source)
        try container.encodeIfPresent(missing_reason, forKey: .missing_reason)
        try container.encodeIfPresent(lifecycle, forKey: .lifecycle)
        try container.encodeIfPresent(fresh_read, forKey: .fresh_read)
        try container.encodeIfPresent(fresh_write, forKey: .fresh_write)
        try container.encodeIfPresent(exec_observation, forKey: .exec_observation)
        try container.encode(rc, forKey: .rc)
        if let errno {
            try container.encode(errno, forKey: .errno)
        } else {
            try container.encodeNil(forKey: .errno)
        }
        try container.encode(outcome, forKey: .outcome)
        try container.encodeIfPresent(error, forKey: .error)
        if let requested_path {
            try container.encode(requested_path, forKey: .requested_path)
        } else {
            try container.encodeNil(forKey: .requested_path)
        }
        try container.encodeIfPresent(path_diagnostics, forKey: .path_diagnostics)
        if let observed_path {
            try container.encode(observed_path, forKey: .observed_path)
        } else {
            try container.encodeNil(forKey: .observed_path)
        }
        // Exec output fields: emit when non-nil, omit the key when nil.
        // A completed exec slot supplies the three child fields, including
        // child_pid == 0 / child_exit_code == -1 / child_term_signal == 0
        // when spawn failed. stdout/stderr are included only when that
        // stream produced bytes. Non-exec attempts omit all five fields.
        try container.encodeIfPresent(child_pid, forKey: .child_pid)
        try container.encodeIfPresent(child_exit_code, forKey: .child_exit_code)
        try container.encodeIfPresent(child_term_signal, forKey: .child_term_signal)
        try container.encodeIfPresent(stdout, forKey: .stdout)
        try container.encodeIfPresent(stderr, forKey: .stderr)
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        requested_kind = try container.decodeIfPresent(String.self, forKey: .requested_kind)
        requested_action = try container.decodeIfPresent(String.self, forKey: .requested_action)
        result_source = try container.decodeIfPresent(String.self, forKey: .result_source)
        missing_reason = try container.decodeIfPresent(String.self, forKey: .missing_reason)
        lifecycle = try container.decodeIfPresent(PWAttemptLifecycle.self, forKey: .lifecycle)
        fresh_read = try container.decodeIfPresent(PWRunnerFreshRead.self, forKey: .fresh_read)
        fresh_write = try container.decodeIfPresent(PWRunnerFreshWrite.self, forKey: .fresh_write)
        exec_observation = try container.decodeIfPresent(PWExecObservation.self, forKey: .exec_observation)
        rc = try container.decode(Int.self, forKey: .rc)
        errno = try container.decodeIfPresent(Int.self, forKey: .errno)
        outcome = try container.decode(String.self, forKey: .outcome)
        error = try container.decodeIfPresent(String.self, forKey: .error)
        requested_path = try container.decodeIfPresent(String.self, forKey: .requested_path)
        path_diagnostics = try container.decodeIfPresent(PWRunnerAttemptPathDiagnostics.self, forKey: .path_diagnostics)
        observed_path = try container.decodeIfPresent(String.self, forKey: .observed_path)
        child_pid = try container.decodeIfPresent(Int.self, forKey: .child_pid)
        child_exit_code = try container.decodeIfPresent(Int.self, forKey: .child_exit_code)
        child_term_signal = try container.decodeIfPresent(Int.self, forKey: .child_term_signal)
        stdout = try container.decodeIfPresent(String.self, forKey: .stdout)
        stderr = try container.decodeIfPresent(String.self, forKey: .stderr)
    }
}

extension PWRunnerAttemptResult {
    func freshWriteEvidenceProblem() -> String? {
        let expected = requested_kind == "file" && ["write_fresh", "create_fresh"].contains(requested_action ?? "") && result_source == "worker"
        guard let write = fresh_write else { return expected ? "completed fresh write lacks syscall observations" : nil }
        guard expected, write.open_rc >= -1 else { return "fresh write requires a completed fresh-write attempt" }
        let creating = requested_action == "create_fresh"
        guard creating == (write.preopen_stat != nil) else { return "fresh creation requires its pre-open metadata observation" }
        for metadata in [write.preopen_stat, write.opened_stat, write.truncated_stat, write.written_stat].compactMap({ $0 }) {
            if let problem = metadata.evidenceProblem() { return problem }
        }
        func validErrno(_ result: Int64, _ error: Int32?) -> Bool {
            result == -1 ? error != nil && error! >= 0 : error == nil
        }
        guard validErrno(Int64(write.open_rc), write.open_errno) else { return "fresh write open errno disagrees with native result" }
        var firstFailure: Int32?
        var failed = false
        func observe(_ result: Int64, _ error: Int32?, short: Bool = false) {
            if !failed && (result < 0 || short) { failed = true; firstFailure = result < 0 ? error : nil }
        }
        observe(Int64(write.open_rc), write.open_errno)
        if write.open_rc == -1 {
            guard write.opened_stat == nil, write.truncate_rc == nil, write.truncate_errno == nil,
                  write.truncated_stat == nil, write.write_rc == nil, write.write_errno == nil,
                  write.written_stat == nil, write.close_rc == nil, write.close_errno == nil else {
                return "failed fresh write open cannot supply later syscall evidence"
            }
        } else {
            guard let opened = write.opened_stat, let close = write.close_rc, [-1, 0].contains(close),
                  validErrno(Int64(close), write.close_errno) else { return "fresh write lacks opened metadata or close result" }
            observe(Int64(opened.rc), opened.errno)
            if creating {
                guard write.truncate_rc == nil, write.truncate_errno == nil, write.truncated_stat == nil else {
                    return "exclusive creation must not fabricate truncation"
                }
            } else {
                guard let truncated = write.truncate_rc, [-1, 0].contains(truncated),
                      validErrno(Int64(truncated), write.truncate_errno), let metadata = write.truncated_stat else {
                    return "fresh write lacks truncation observations"
                }
                observe(Int64(truncated), write.truncate_errno)
                observe(Int64(metadata.rc), metadata.errno)
            }
            if creating || write.truncate_rc == 0 {
                guard let count = write.write_rc, (-1...1).contains(count), validErrno(count, write.write_errno),
                      let metadata = write.written_stat else { return "fresh write lacks bounded transfer observations" }
                observe(count, write.write_errno, short: count == 0)
                observe(Int64(metadata.rc), metadata.errno)
            } else if write.write_rc != nil || write.write_errno != nil || write.written_stat != nil {
                return "failed truncation cannot supply a later write"
            }
            observe(Int64(close), write.close_errno)
        }
        guard rc == (failed ? -1 : 0), errno == firstFailure.flatMap({ $0 == 0 ? nil : Int($0) }),
              outcome == (failed ? AttemptOutcome.writeFailed : AttemptOutcome.ok) else {
            return "fresh write syscalls disagree with attempt status"
        }
        return nil
    }

    func freshReadEvidenceProblem() -> String? {
        let expected = requested_kind == "file" && requested_action == "read_fresh" && result_source == "worker"
        guard let read = fresh_read else { return expected ? "completed fresh read lacks syscall observations" : nil }
        guard expected, read.open_rc >= -1 else { return "fresh read requires a completed read_fresh attempt" }
        if read.open_rc == -1 {
            guard let error = read.open_errno, error >= 0, read.read_rc == nil, read.read_errno == nil,
                  read.stat_rc == nil, read.stat_errno == nil, read.identity == nil,
                  read.close_rc == nil, read.close_errno == nil, read.content_hex == nil,
                  rc == -1, errno == (error == 0 ? nil : Int(error)), outcome == AttemptOutcome.readFailed else {
                return "failed fresh open cannot supply read/stat/close evidence"
            }
            return nil
        }
        guard read.open_errno == nil, let count = read.read_rc, count >= -1 && count <= PWExtensionLimits.freshReadBytes,
              let stat = read.stat_rc, [-1, 0].contains(stat), let close = read.close_rc, [-1, 0].contains(close) else { return "invalid fresh syscall results" }
        func validErrno(_ result: Int64, _ error: Int32?) -> Bool { result < 0 ? error != nil && error! >= 0 : error == nil }
        guard validErrno(count, read.read_errno), validErrno(Int64(stat), read.stat_errno), validErrno(Int64(close), read.close_errno),
              (stat == 0) == (read.identity != nil) else { return "fresh syscall failure evidence disagrees" }
        if count >= 0 {
            guard let content = read.content_hex, content.utf8.count == Int(count) * 2,
                  content.utf8.allSatisfy({ (48...57).contains($0) || (97...102).contains($0) }) else { return "fresh read bytes disagree with native count" }
        } else if read.content_hex != nil { return "failed fresh read cannot supply content" }
        let failed = stat < 0 || count < 0 || close < 0
        let error = stat < 0 ? read.stat_errno : count < 0 ? read.read_errno : close < 0 ? read.close_errno : nil
        guard rc == (failed ? -1 : 0), errno == error.flatMap({ $0 == 0 ? nil : Int($0) }),
              outcome == (failed ? AttemptOutcome.readFailed : AttemptOutcome.ok) else { return "fresh syscall results disagree with attempt" }
        return nil
    }
}
