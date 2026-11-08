import Darwin
import Foundation
@testable import PWRunnerCore

// Constructed observations mirror the independently authored reader corpus.
private func execFixture0() -> PWRunnerAttemptResult {
    let value1 = PWExecStreamObservation(eof: true)
    let value2 = PWExecStreamObservation(eof: true)
    let value3 = PWExecCollectionObservation(stop_reason: "leader_exit_and_eof", leader_exit_observed: true, stdout: value1, stderr: value2)
    let value4 = PWExecCleanupObservation(state: "not_requested")
    let value5 = PWExecWaitObservation(rc: 4242, status: 0)
    let value6 = PWExecReapObservation(stop_reason: "reaped", last_wait: value5)
    let value7 = PWExecObservation(collection: value3, cleanup: value4, reap: value6)
    let value8 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value9 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value10 = PWAttemptLifecycle(summary: "completed", boundary: value8, result: value9)
    var value11 = PWRunnerAttemptResult(rc: 0, outcome: "ok", child_pid: 4242, child_exit_code: 0, child_term_signal: 0, exec_observation: value7)
    value11.requested_kind = "exec"
    value11.requested_action = "spawn"
    value11.result_source = "worker"
    value11.lifecycle = value10
    return value11
}

private func execFixture1() -> PWRunnerAttemptResult {
    let value1 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value2 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value3 = PWAttemptLifecycle(summary: "completed", boundary: value1, result: value2)
    var value4 = PWRunnerAttemptResult(rc: 0, outcome: "ok", child_pid: 4242, child_exit_code: 0, child_term_signal: 0)
    value4.requested_kind = "exec"
    value4.requested_action = "spawn"
    value4.result_source = "worker"
    value4.lifecycle = value3
    return value4
}

private func execFixture2() -> PWRunnerAttemptResult {
    let value1 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value2 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value3 = PWAttemptLifecycle(summary: "completed", boundary: value1, result: value2)
    var value4 = PWRunnerAttemptResult(rc: 0, outcome: "ok", child_pid: 4242, child_exit_code: 0, child_term_signal: 0, exec_observation: nil)
    value4.requested_kind = "exec"
    value4.requested_action = "spawn"
    value4.result_source = "worker"
    value4.lifecycle = value3
    return value4
}

private func execFixture3() -> PWRunnerAttemptResult {
    let value1 = PWExecStreamObservation(eof: true)
    let value2 = PWExecStreamObservation(eof: false)
    let value3 = PWExecCollectionObservation(stop_reason: "deadline", leader_exit_observed: false, stdout: value1, stderr: value2, deadline_kind: "child")
    let value4 = PWExecSignalRequest(target: -4242, signal: 9, rc: 0)
    let value5 = PWExecCleanupObservation(state: "requested", group_request: value4)
    let value6 = PWExecWaitObservation(rc: 4242, status: 9)
    let value7 = PWExecReapObservation(stop_reason: "reaped", last_wait: value6)
    let value8 = PWExecObservation(collection: value3, cleanup: value5, reap: value7)
    let value9 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value10 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value11 = PWAttemptLifecycle(summary: "completed", boundary: value9, result: value10)
    var value12 = PWRunnerAttemptResult(rc: -1, outcome: "exec_failed", child_pid: 4242, child_exit_code: -1, child_term_signal: 9, exec_observation: value8)
    value12.requested_kind = "exec"
    value12.requested_action = "spawn"
    value12.result_source = "worker"
    value12.lifecycle = value11
    return value12
}

private func execFixture4() -> PWRunnerAttemptResult {
    let value1 = PWExecStreamObservation(eof: true)
    let value2 = PWExecStreamObservation(eof: false)
    let value3 = PWExecCollectionObservation(stop_reason: "deadline", leader_exit_observed: false, stdout: value1, stderr: value2, deadline_kind: "child")
    let value4 = PWExecSignalRequest(target: -4242, signal: 9, rc: -1, errno: 3)
    let value5 = PWExecCleanupObservation(state: "requested", group_request: value4)
    let value6 = PWExecWaitObservation(rc: 4242, status: 9)
    let value7 = PWExecReapObservation(stop_reason: "reaped", last_wait: value6)
    let value8 = PWExecObservation(collection: value3, cleanup: value5, reap: value7)
    let value9 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value10 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value11 = PWAttemptLifecycle(summary: "completed", boundary: value9, result: value10)
    var value12 = PWRunnerAttemptResult(rc: -1, outcome: "exec_failed", child_pid: 4242, child_exit_code: -1, child_term_signal: 9, exec_observation: value8)
    value12.requested_kind = "exec"
    value12.requested_action = "spawn"
    value12.result_source = "worker"
    value12.lifecycle = value11
    return value12
}

private func execFixture5() -> PWRunnerAttemptResult {
    let value1 = PWExecStreamObservation(eof: true)
    let value2 = PWExecStreamObservation(eof: false)
    let value3 = PWExecCollectionObservation(stop_reason: "deadline", leader_exit_observed: false, stdout: value1, stderr: value2, deadline_kind: "child")
    let value4 = PWExecSignalRequest(target: -4242, signal: 9, rc: -1, errno: 1)
    let value5 = PWExecSignalRequest(target: 4242, signal: 9, rc: 0)
    let value6 = PWExecCleanupObservation(state: "requested", group_request: value4, leader_fallback: value5)
    let value7 = PWExecWaitObservation(rc: 4242, status: 0)
    let value8 = PWExecReapObservation(stop_reason: "reaped", last_wait: value7)
    let value9 = PWExecObservation(collection: value3, cleanup: value6, reap: value8)
    let value10 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value11 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value12 = PWAttemptLifecycle(summary: "completed", boundary: value10, result: value11)
    var value13 = PWRunnerAttemptResult(rc: -1, errno: 1, outcome: "exec_failed", child_pid: 4242, child_exit_code: 0, child_term_signal: 0, exec_observation: value9)
    value13.requested_kind = "exec"
    value13.requested_action = "spawn"
    value13.result_source = "worker"
    value13.lifecycle = value12
    return value13
}

private func execFixture6() -> PWRunnerAttemptResult {
    let value1 = PWExecStreamObservation(eof: true)
    let value2 = PWExecStreamObservation(eof: false)
    let value3 = PWExecCollectionObservation(stop_reason: "deadline", leader_exit_observed: false, stdout: value1, stderr: value2, deadline_kind: "child")
    let value4 = PWExecSignalRequest(target: -4242, signal: 9, rc: -1, errno: 1)
    let value5 = PWExecSignalRequest(target: 4242, signal: 9, rc: -1, errno: 3)
    let value6 = PWExecCleanupObservation(state: "requested", group_request: value4, leader_fallback: value5)
    let value7 = PWExecWaitObservation(rc: 4242, status: 0)
    let value8 = PWExecReapObservation(stop_reason: "reaped", last_wait: value7)
    let value9 = PWExecObservation(collection: value3, cleanup: value6, reap: value8)
    let value10 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value11 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value12 = PWAttemptLifecycle(summary: "completed", boundary: value10, result: value11)
    var value13 = PWRunnerAttemptResult(rc: -1, errno: 1, outcome: "exec_failed", child_pid: 4242, child_exit_code: 0, child_term_signal: 0, exec_observation: value9)
    value13.requested_kind = "exec"
    value13.requested_action = "spawn"
    value13.result_source = "worker"
    value13.lifecycle = value12
    return value13
}

private func execFixture7() -> PWRunnerAttemptResult {
    let value1 = PWExecStreamObservation(eof: true)
    let value2 = PWExecStreamObservation(eof: false)
    let value3 = PWExecCollectionObservation(stop_reason: "deadline", leader_exit_observed: false, stdout: value1, stderr: value2, deadline_kind: "child")
    let value4 = PWExecSignalRequest(target: -4242, signal: 9, rc: 0)
    let value5 = PWExecCleanupObservation(state: "requested", group_request: value4)
    let value6 = PWExecWaitObservation(rc: 0)
    let value7 = PWExecReapObservation(stop_reason: "deadline", last_wait: value6)
    let value8 = PWExecObservation(collection: value3, cleanup: value5, reap: value7)
    let value9 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value10 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value11 = PWAttemptLifecycle(summary: "completed", boundary: value9, result: value10)
    var value12 = PWRunnerAttemptResult(rc: -1, errno: 60, outcome: "exec_failed", child_pid: 4242, child_exit_code: -1, child_term_signal: 0, exec_observation: value8)
    value12.requested_kind = "exec"
    value12.requested_action = "spawn"
    value12.result_source = "worker"
    value12.lifecycle = value11
    return value12
}

private func execFixture8() -> PWRunnerAttemptResult {
    let value1 = PWExecStreamObservation(eof: true)
    let value2 = PWExecStreamObservation(eof: false)
    let value3 = PWExecCollectionObservation(stop_reason: "deadline", leader_exit_observed: false, stdout: value1, stderr: value2, deadline_kind: "child")
    let value4 = PWExecSignalRequest(target: -4242, signal: 9, rc: 0)
    let value5 = PWExecCleanupObservation(state: "requested", group_request: value4)
    let value6 = PWExecWaitObservation(rc: -1, errno: 60)
    let value7 = PWExecReapObservation(stop_reason: "wait_error", last_wait: value6)
    let value8 = PWExecObservation(collection: value3, cleanup: value5, reap: value7)
    let value9 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value10 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value11 = PWAttemptLifecycle(summary: "completed", boundary: value9, result: value10)
    var value12 = PWRunnerAttemptResult(rc: -1, errno: 60, outcome: "exec_failed", child_pid: 4242, child_exit_code: -1, child_term_signal: 0, exec_observation: value8)
    value12.requested_kind = "exec"
    value12.requested_action = "spawn"
    value12.result_source = "worker"
    value12.lifecycle = value11
    return value12
}

private func execFixture9() -> PWRunnerAttemptResult {
    let value1 = PWExecStreamObservation(eof: true)
    let value2 = PWExecStreamObservation(eof: false)
    let value3 = PWExecCollectionObservation(stop_reason: "deadline", leader_exit_observed: false, stdout: value1, stderr: value2, deadline_kind: "child")
    let value4 = PWExecSignalRequest(target: -4242, signal: 9, rc: 0)
    let value5 = PWExecCleanupObservation(state: "requested", group_request: value4)
    let value6 = PWExecWaitObservation(rc: -1, errno: 4)
    let value7 = PWExecReapObservation(stop_reason: "deadline", last_wait: value6)
    let value8 = PWExecObservation(collection: value3, cleanup: value5, reap: value7)
    let value9 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value10 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value11 = PWAttemptLifecycle(summary: "completed", boundary: value9, result: value10)
    var value12 = PWRunnerAttemptResult(rc: -1, errno: 60, outcome: "exec_failed", child_pid: 4242, child_exit_code: -1, child_term_signal: 0, exec_observation: value8)
    value12.requested_kind = "exec"
    value12.requested_action = "spawn"
    value12.result_source = "worker"
    value12.lifecycle = value11
    return value12
}

private func execFixture10() -> PWRunnerAttemptResult {
    let value1 = PWExecStreamObservation(eof: true)
    let value2 = PWExecStreamObservation(eof: true)
    let value3 = PWExecCollectionObservation(stop_reason: "leader_exit_and_eof", leader_exit_observed: true, stdout: value1, stderr: value2)
    let value4 = PWExecCleanupObservation(state: "not_requested")
    let value5 = PWExecWaitObservation(rc: 4242, status: 0)
    let value6 = PWExecReapObservation(stop_reason: "reaped", last_wait: value5, clock_fault: 4294967295)
    let value7 = PWExecObservation(collection: value3, cleanup: value4, reap: value6)
    let value8 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value9 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value10 = PWAttemptLifecycle(summary: "completed", boundary: value8, result: value9)
    var value11 = PWRunnerAttemptResult(rc: -1, outcome: "exec_failed", child_pid: 4242, child_exit_code: 0, child_term_signal: 0, exec_observation: value7)
    value11.requested_kind = "exec"
    value11.requested_action = "spawn"
    value11.result_source = "worker"
    value11.lifecycle = value10
    return value11
}

private func execFixture11() -> PWRunnerAttemptResult {
    let value1 = PWExecStreamObservation(eof: false, read_errno: 5)
    let value2 = PWExecStreamObservation(eof: false, read_errno: 9)
    let value3 = PWExecCollectionObservation(stop_reason: "observation_error", leader_exit_observed: true, stdout: value1, stderr: value2)
    let value4 = PWExecSignalRequest(target: -4242, signal: 9, rc: -1, errno: 1)
    let value5 = PWExecSignalRequest(target: 4242, signal: 9, rc: 0)
    let value6 = PWExecCleanupObservation(state: "requested", group_request: value4, leader_fallback: value5)
    let value7 = PWExecWaitObservation(rc: 4242, status: 0)
    let value8 = PWExecReapObservation(stop_reason: "reaped", last_wait: value7)
    let value9 = PWExecObservation(collection: value3, cleanup: value6, reap: value8)
    let value10 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value11 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value12 = PWAttemptLifecycle(summary: "completed", boundary: value10, result: value11)
    var value13 = PWRunnerAttemptResult(rc: -1, errno: 9, outcome: "exec_failed", child_pid: 4242, child_exit_code: 0, child_term_signal: 0, exec_observation: value9)
    value13.requested_kind = "exec"
    value13.requested_action = "spawn"
    value13.result_source = "worker"
    value13.lifecycle = value12
    return value13
}

private func execFixture12() -> PWRunnerAttemptResult {
    let value1 = PWExecStreamObservation(eof: false, poll_revents: 8)
    let value2 = PWExecStreamObservation(eof: false, poll_revents: 32)
    let value3 = PWExecCollectionObservation(stop_reason: "observation_error", leader_exit_observed: true, stdout: value1, stderr: value2)
    let value4 = PWExecSignalRequest(target: -4242, signal: 9, rc: -1, errno: 1)
    let value5 = PWExecSignalRequest(target: 4242, signal: 9, rc: 0)
    let value6 = PWExecCleanupObservation(state: "requested", group_request: value4, leader_fallback: value5)
    let value7 = PWExecWaitObservation(rc: 4242, status: 0)
    let value8 = PWExecReapObservation(stop_reason: "reaped", last_wait: value7)
    let value9 = PWExecObservation(collection: value3, cleanup: value6, reap: value8)
    let value10 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value11 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value12 = PWAttemptLifecycle(summary: "completed", boundary: value10, result: value11)
    var value13 = PWRunnerAttemptResult(rc: -1, errno: 5, outcome: "exec_failed", child_pid: 4242, child_exit_code: 0, child_term_signal: 0, exec_observation: value9)
    value13.requested_kind = "exec"
    value13.requested_action = "spawn"
    value13.result_source = "worker"
    value13.lifecycle = value12
    return value13
}

private func execFixture13() -> PWRunnerAttemptResult {
    let value1 = PWExecStreamObservation(eof: false)
    let value2 = PWExecStreamObservation(eof: false)
    let value3 = PWExecCollectionObservation(stop_reason: "observation_error", leader_exit_observed: false, stdout: value1, stderr: value2, poll_errno: 5)
    let value4 = PWExecSignalRequest(target: -4242, signal: 9, rc: -1, errno: 1)
    let value5 = PWExecSignalRequest(target: 4242, signal: 9, rc: 0)
    let value6 = PWExecCleanupObservation(state: "requested", group_request: value4, leader_fallback: value5)
    let value7 = PWExecWaitObservation(rc: 4242, status: 0)
    let value8 = PWExecReapObservation(stop_reason: "reaped", last_wait: value7)
    let value9 = PWExecObservation(collection: value3, cleanup: value6, reap: value8)
    let value10 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value11 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value12 = PWAttemptLifecycle(summary: "completed", boundary: value10, result: value11)
    var value13 = PWRunnerAttemptResult(rc: -1, errno: 5, outcome: "exec_failed", child_pid: 4242, child_exit_code: 0, child_term_signal: 0, exec_observation: value9)
    value13.requested_kind = "exec"
    value13.requested_action = "spawn"
    value13.result_source = "worker"
    value13.lifecycle = value12
    return value13
}

private func execFixture14() -> PWRunnerAttemptResult {
    let value1 = PWExecStreamObservation(eof: false)
    let value2 = PWExecStreamObservation(eof: false)
    let value3 = PWExecCollectionObservation(stop_reason: "observation_error", leader_exit_observed: false, stdout: value1, stderr: value2, waitid_errno: 10)
    let value4 = PWExecCleanupObservation(state: "ownership_unconfirmed")
    let value5 = PWExecWaitObservation(rc: 0)
    let value6 = PWExecReapObservation(stop_reason: "ownership_unconfirmed", last_wait: value5, clock_fault: 5)
    let value7 = PWExecObservation(collection: value3, cleanup: value4, reap: value6)
    let value8 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value9 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value10 = PWAttemptLifecycle(summary: "completed", boundary: value8, result: value9)
    var value11 = PWRunnerAttemptResult(rc: -1, errno: 10, outcome: "exec_failed", child_pid: 4242, child_exit_code: -1, child_term_signal: 0, exec_observation: value7)
    value11.requested_kind = "exec"
    value11.requested_action = "spawn"
    value11.result_source = "worker"
    value11.lifecycle = value10
    return value11
}

private func execFixture15() -> PWRunnerAttemptResult {
    let value1 = PWExecStreamObservation(eof: false)
    let value2 = PWExecStreamObservation(eof: false)
    let value3 = PWExecCollectionObservation(stop_reason: "clock_fault", leader_exit_observed: false, stdout: value1, stderr: value2, clock_fault: 7)
    let value4 = PWExecSignalRequest(target: -4242, signal: 9, rc: 0)
    let value5 = PWExecCleanupObservation(state: "requested", group_request: value4)
    let value6 = PWExecWaitObservation(rc: 0)
    let value7 = PWExecReapObservation(stop_reason: "clock_fault", last_wait: value6, clock_fault: 9)
    let value8 = PWExecObservation(collection: value3, cleanup: value5, reap: value7)
    let value9 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value10 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value11 = PWAttemptLifecycle(summary: "completed", boundary: value9, result: value10)
    var value12 = PWRunnerAttemptResult(rc: -1, outcome: "exec_failed", child_pid: 4242, child_exit_code: -1, child_term_signal: 0, exec_observation: value8)
    value12.requested_kind = "exec"
    value12.requested_action = "spawn"
    value12.result_source = "worker"
    value12.lifecycle = value11
    return value12
}

private func execFixture16() -> PWRunnerAttemptResult {
    let value1 = PWExecStreamObservation(eof: true)
    let value2 = PWExecStreamObservation(eof: false)
    let value3 = PWExecCollectionObservation(stop_reason: "deadline", leader_exit_observed: false, stdout: value1, stderr: value2, deadline_kind: "plan")
    let value4 = PWExecSignalRequest(target: -4242, signal: 9, rc: 0)
    let value5 = PWExecCleanupObservation(state: "requested", group_request: value4)
    let value6 = PWExecWaitObservation(rc: 4242, status: 9)
    let value7 = PWExecReapObservation(stop_reason: "reaped", last_wait: value6)
    let value8 = PWExecObservation(collection: value3, cleanup: value5, reap: value7)
    let value9 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value10 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value11 = PWAttemptLifecycle(summary: "completed", boundary: value9, result: value10)
    var value12 = PWRunnerAttemptResult(rc: -1, outcome: "exec_failed", child_pid: 4242, child_exit_code: -1, child_term_signal: 9, exec_observation: value8)
    value12.requested_kind = "exec"
    value12.requested_action = "spawn"
    value12.result_source = "worker"
    value12.lifecycle = value11
    return value12
}

private func execFixture17() -> PWRunnerAttemptResult {
    let value1 = PWExecStreamObservation(eof: true)
    let value2 = PWExecStreamObservation(eof: false)
    let value3 = PWExecCollectionObservation(stop_reason: "deadline", leader_exit_observed: false, stdout: value1, stderr: value2, deadline_kind: "child")
    let value4 = PWExecSignalRequest(target: -4242, signal: 9, rc: -1, errno: 1)
    let value5 = PWExecSignalRequest(target: 4242, signal: 9, rc: 0)
    let value6 = PWExecCleanupObservation(state: "requested", group_request: value4, leader_fallback: value5)
    let value7 = PWExecWaitObservation(rc: 0)
    let value8 = PWExecReapObservation(stop_reason: "group_request_failed", last_wait: value7)
    let value9 = PWExecObservation(collection: value3, cleanup: value6, reap: value8)
    let value10 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value11 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value12 = PWAttemptLifecycle(summary: "completed", boundary: value10, result: value11)
    var value13 = PWRunnerAttemptResult(rc: -1, errno: 1, outcome: "exec_failed", child_pid: 4242, child_exit_code: -1, child_term_signal: 0, exec_observation: value9)
    value13.requested_kind = "exec"
    value13.requested_action = "spawn"
    value13.result_source = "worker"
    value13.lifecycle = value12
    return value13
}

private func execFixture18() -> PWRunnerAttemptResult {
    let value1 = PWExecStreamObservation(eof: false, poll_revents: -32760)
    let value2 = PWExecStreamObservation(eof: false, poll_revents: 32)
    let value3 = PWExecCollectionObservation(stop_reason: "observation_error", leader_exit_observed: true, stdout: value1, stderr: value2)
    let value4 = PWExecSignalRequest(target: -4242, signal: 9, rc: -1, errno: 1)
    let value5 = PWExecSignalRequest(target: 4242, signal: 9, rc: 0)
    let value6 = PWExecCleanupObservation(state: "requested", group_request: value4, leader_fallback: value5)
    let value7 = PWExecWaitObservation(rc: 4242, status: 0)
    let value8 = PWExecReapObservation(stop_reason: "reaped", last_wait: value7)
    let value9 = PWExecObservation(collection: value3, cleanup: value6, reap: value8)
    let value10 = PWDispositionClaim(state: "supported", answer: "reached", basis: ["slot", "attempt_support"])
    let value11 = PWDispositionClaim(state: "supported", answer: "published", basis: ["slot", "attempt_support"])
    let value12 = PWAttemptLifecycle(summary: "completed", boundary: value10, result: value11)
    var value13 = PWRunnerAttemptResult(rc: -1, errno: 5, outcome: "exec_failed", child_pid: 4242, child_exit_code: 0, child_term_signal: 0, exec_observation: value9)
    value13.requested_kind = "exec"
    value13.requested_action = "spawn"
    value13.result_source = "worker"
    value13.lifecycle = value12
    return value13
}

private func execNativeCases() -> [(String, PWRunnerAttemptResult)] {
    [
        ("ordinary", execFixture0()),
        ("old_producer_absent", execFixture1()),
        ("null_unknown", execFixture2()),
        ("deadline_kill_and_reap", execFixture3()),
        ("esrch_not_success", execFixture4()),
        ("clean_exit_group_failure_fallback_success", execFixture5()),
        ("separate_failed_fallback", execFixture6()),
        ("successful_signal_unconfirmed_reap", execFixture7()),
        ("native_timeout", execFixture8()),
        ("interrupted_local_deadline", execFixture9()),
        ("reaped_with_unfamiliar_clock_fault", execFixture10()),
        ("two_read_errors", execFixture11()),
        ("two_stream_revents", execFixture12()),
        ("native_poll_error", execFixture13()),
        ("ownership_lost_clock_fault", execFixture14()),
        ("local_faults", execFixture15()),
        ("plan_deadline", execFixture16()),
        ("failed_group_pending", execFixture17()),
        ("signed_short_revents", execFixture18())
    ]
}

func execObservationShapeDocuments() throws -> [PWRunnerRunResult] {
    try execNativeCases().map { _, attempt in
        var reply = try replyFixture()
        reply.steps[0].attempt = attempt
        return reply
    }
}

func runExecObservationTests(_ tk: TestKit) {
    tk.group("exec observation readers and publication") {
        tk.run("independent native combinations retain cleanup separate from leader status") {
            for (name, attempt) in execNativeCases() {
                try expectNil(attempt.execObservationEvidenceProblem(), name)
                var reply = try replyFixture()
                reply.steps[0].attempt = attempt
                let comparison = computeComparison(sandboxCheck: reply.steps[0].sandbox_check, attempt: attempt)
                try expectEqual(comparison.observation, "succeeded", name)
                try expectEqual(comparison.observation_basis, "spawned_child", name)
                _ = try admittedReplyData(reply)
                let decoded = reply
                try expectEqual(decoded.steps[0].attempt.child_exit_code, attempt.child_exit_code)
                try expectEqual(decoded.steps[0].attempt.exec_observation?.cleanup.state,
                                attempt.exec_observation?.cleanup.state)
                if name == "old_producer_absent" || name == "null_unknown" {
                    try expectNil(decoded.steps[0].attempt.exec_observation, "absence cannot become not_requested")
                }
            }
        }
        tk.run("contradictory typed exec facts degrade without losing observations") {
            let changes: [(inout PWRunnerAttemptResult) -> Void] = [
                { $0.child_pid = 0 }, { $0.child_exit_code = 99 },
                { $0.exec_observation?.reap.last_wait.rc = 1 },
                { $0.result_source = "synthetic" }, { $0.requested_kind = "file" },
            ]
            for change in changes {
                var reply = try replyFixture()
                reply.steps[0].attempt = execFixture0()
                change(&reply.steps[0].attempt)
                try expectThrows { try reply.validateForReporting() }
                let degraded = try reportedReply(reply)
                try expectEqual(degraded.normalized_outcome, "runner_reporting_failed")
                try expectTrue(degraded.steps.allSatisfy { $0.comparison == nil })
                try expectEqual(try pwPorcelainEncode(degraded.steps[0].attempt), try pwPorcelainEncode(reply.steps[0].attempt))
            }
        }
        tk.run("C slot completion gates payload and malformed publication degrades") {
            guard let path = ProcessInfo.processInfo.environment["PW_LIFECYCLE_WORKER_FIXTURE"] else {
                throw TestFailure(message: "missing worker lifecycle fixture")
            }
            for mode in ["exec_payload_valid", "exec_payload_unpublished", "exec_payload_bad_marker", "exec_payload_bad_enum"] {
                let input = CWorkerInput(workerExecutablePath: path, policy: mode,
                    slots: [CWorkerSlotInput(stepId: "s", attemptKind: .execSpawn, target: "/usr/bin/true")],
                    sentinelTimeoutMs: 500, exitGraceMs: 500)
                guard case .success(let out) = runCWorker(input), let slot = out.slots.first else {
                    throw TestFailure(message: "fixture driver failed for \(mode)")
                }
                if mode == "exec_payload_unpublished" {
                    try expectFalse(slot.completed)
                    try expectNil(slot.execObservation)
                    try expectNil(slot.execObservationProblem)
                    try expectNil(slot.childPid)
                    try expectNil(slot.childStdout)
                    try expectEqual(out.termSignal, SIGKILL)
                } else {
                    try expectTrue(slot.completed)
                    let probe = PWRunnerProbeStep(step_id: "s", sandbox_check: PWRunnerSandboxCheck(operation: "process-exec",
                        filter: PWRunnerSandboxFilter(kind: "path", value: "/usr/bin/true")),
                        attempt: PWRunnerAttempt(kind: "exec", action: "spawn", target: "/usr/bin/true"))
                    let disposition = resolveDisposition(out, plan: [probe])
                    let phase = constructedPhase(out, ids: ["s"])
                    let reply = PWRunnerRunResult(specimen_id: mode, rc: 0, normalized_outcome: "finished", pid: Int(out.workerPid),
                        policy_format: "sbpl", sandboxed_after_apply: true,
                        steps: buildStepResults(probePlan: [probe], queryPlan: planValidatorQueries([probe]), workerOutput: out,
                            validatorOutput: nil, ordering: phase.ordering, disposition: disposition),
                        runner_subprocess: buildWorkerSubprocess(out, disposition: disposition), phases: [phase])
                    let decoded = try reportedReply(reply)
                    if mode == "exec_payload_valid" {
                        try expectEqual(decoded.steps[0].attempt.exec_observation?.reap.last_wait.rc, 4242)
                        try expectEqual(decoded.steps[0].attempt.exec_observation?.cleanup.state, "not_requested")
                    } else {
                        try expectEqual(decoded.normalized_outcome, "runner_reporting_failed")
                        try expectContains(decoded.reporting_failure?.diagnostic ?? "", "malformed completed exec payload")
                        try expectNil(decoded.steps[0].comparison)
                    }
                }
            }
        }
    }
}
