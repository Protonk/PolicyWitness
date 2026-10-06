//! Current-schema reply builders shared by the controller's unit tests. Every
//! step carries the lifecycle copies and validator record the controller and
//! the independent consumer check; the disposition record is derived from the
//! same subprocess facts the reply states.

use serde_json::{Value, json};

use crate::json_contract;

pub(crate) fn operation(action: &str) -> &'static str {
    match action {
        "open_read" | "access" => "file-read-data",
        "open_write" => "file-write-data",
        "unlink" => "file-write-unlink",
        other => panic!("unmapped action {other}"),
    }
}

pub(crate) fn failed_outcome(action: &str) -> &'static str {
    match action {
        "unlink" => "unlink_failed",
        "access" => "access_failed",
        _ => "open_failed",
    }
}

pub(crate) fn query(action: &str, path: &str) -> Value {
    json!({"outcome": "allow", "rc": 0, "native_rc": 0, "errno": 0, "error": null, "pid": 42,
        "result_source": "validator", "operation": operation(action), "filter_kind": "path",
        "filter_type_id": 1, "filter_value": path,
        "path_diagnostics": {"input": path, "observer": "runner_host", "phase": "after_orchestration",
            "same_as_input": ["realpath_resolved", "firmlink_resolved"]}})
}

pub(crate) fn attempt_paths(path: &str) -> Value {
    json!({"input": path, "observer": "runner_host", "phase": "after_orchestration",
        "same_as_input": ["realpath_resolved", "parent_realpath_resolved"]})
}

/// A completed, supported file step whose attempt reports `observation`.
pub(crate) fn step(id: &str, action: &str, path: &str, observation: &str) -> Value {
    let (outcome, rc, errno, basis) = match observation {
        "succeeded" => ("ok", 0, Value::Null, "completed_worker_status"),
        "permission_failure" => (failed_outcome(action), -1, json!(1), "permission_errno"),
        "other_failure" => (
            failed_outcome(action),
            -1,
            json!(2),
            "completed_worker_status",
        ),
        other => panic!("unmapped observation {other}"),
    };
    let boundary =
        json!({"state": "supported", "answer": "reached", "basis": ["slot", "attempt_support"]});
    let result =
        json!({"state": "supported", "answer": "published", "basis": ["slot", "attempt_support"]});
    json!({"step_id": id, "sandbox_check": query(action, path),
        "attempt": {"requested_kind": "file", "requested_action": action, "requested_path": path,
            "outcome": outcome, "rc": rc, "errno": errno, "error": null, "observed_path": null,
            "result_source": "worker", "path_diagnostics": attempt_paths(path),
            "lifecycle": {"boundary": boundary, "result": result, "summary": "completed"}},
        "comparison": {"observation": observation, "observation_basis": basis,
            "operation_relation": "matched", "target_relation": "same_submitted",
            "order": "query_first", "limitations": []}})
}

/// A step whose attempt never published: an incomplete slot under terminal
/// collection, with the boundary question unresolved.
pub(crate) fn incomplete_step(id: &str, action: &str, path: &str) -> Value {
    let boundary = json!({"state": "unresolved", "reason": "no_progress_word"});
    let result = json!({"state": "supported", "answer": "unpublished",
        "basis": ["slot", "collection_basis"]});
    json!({"step_id": id, "sandbox_check": query(action, path),
        "attempt": {"requested_kind": "file", "requested_action": action, "requested_path": path,
            "outcome": "not_run_worker_died", "rc": -1, "errno": null,
            "error": "no completed attempt result: slot publication incomplete",
            "observed_path": null, "result_source": "synthetic", "missing_reason": "slot_incomplete",
            "path_diagnostics": attempt_paths(path),
            "lifecycle": {"boundary": boundary, "result": result, "summary": "unresolved"}},
        "comparison": {"observation": "unavailable", "observation_basis": "no_completed_worker_result",
            "operation_relation": "matched", "target_relation": "same_submitted",
            "order": "query_first", "limitations": ["attempt:lifecycle_unresolved"]}})
}

/// The disposition record the host carries for `sub` and the reply's steps.
pub(crate) fn disposition_for(sub: &Value, steps: &[Value]) -> Value {
    let supported = |answer: Value, basis: &[&str]| json!({"state": "supported", "answer": answer, "basis": basis});
    let exit_requested = sub["exit_requested"] == true;
    let final_status = if sub["term_signal"].is_i64() {
        json!({"state": "supported", "answer": "signal", "value": sub["term_signal"],
            "basis": ["reaped", "term_signal"]})
    } else {
        json!({"state": "supported", "answer": "exit_code", "value": sub["exit_code"],
            "basis": ["reaped", "exit_code"]})
    };
    let cleanup = |name: &str| {
        if exit_requested {
            supported(sub[name].clone(), &[name, "exit_requested"])
        } else {
            json!({"state": "inapplicable", "reason": "exit_not_requested"})
        }
    };
    let kill = if sub["termination_request"].is_object() {
        json!({"state": "supported", "answer": "requested", "value": sub["termination_request"],
            "basis": ["termination_request"]})
    } else {
        json!({"state": "inapplicable", "reason": "exit_not_requested"})
    };
    let records: Vec<Value> = steps
        .iter()
        .enumerate()
        .map(|(i, s)| {
            let lifecycle = &s["attempt"]["lifecycle"];
            let slot = if s["attempt"]["result_source"] == "worker" {
                "completed"
            } else {
                "incomplete"
            };
            json!({"index": i, "step_id": s["step_id"], "slot": slot, "attempt_support": "supported",
                "questions": {"step_boundary_reached": lifecycle["boundary"],
                    "step_result_published": lifecycle["result"],
                    "step_requested_operation_applicability":
                        supported(json!("supported"), &["attempt_support"])}})
        })
        .collect();
    json!({"questions": {
            "final_status": final_status,
            "stop_reason": supported(sub["poll_stop_reason"].clone(), &["poll_stop_reason"]),
            "cleanup_trigger": cleanup("cleanup_trigger"),
            "grace_end": cleanup("grace_end"),
            "kill_request_and_result": kill,
            "collection_basis": supported(sub["collection_basis"].clone(), &["collection_basis"]),
            "progress_association": {"state": "inapplicable", "reason": "no_progress_word"}},
        "steps": records, "issues": []})
}

/// A reply under the current response schema. A signal means the host's
/// sentinel deadline expired and it killed the worker during cleanup.
pub(crate) fn reply_with(outcome: &str, signal: Option<i32>, steps: Vec<Value>) -> Value {
    let partial = steps
        .iter()
        .any(|s| s["attempt"]["result_source"] != "worker");
    let mut sub = json!({"pid": 42, "reaped": true, "term_signal": signal,
        "exit_code": signal.is_none().then_some(0),
        "poll_stop_reason": if signal.is_some() { "sentinel_deadline" } else { "done" },
        "done_observed": signal.is_none(), "exit_requested": signal.is_some(),
        "termination_request": signal.map(|s| json!({"signal": s, "rc": 0})),
        "cleanup_trigger": signal.map(|_| "deadline_expiry"),
        "grace_end": signal.map(|_| "exhausted"),
        "collection_basis": "after_confirmed_reap", "partial_steps": partial,
        "wait_errors": [], "ready_byte_received": true,
        "ordering": {"collection_closed_before_proceed": true, "proceed_set": true,
            "proceed_observed": true, "validator_disposition": "reaped",
            "worker_lifetime_established": true, "protocol_violations": []}});
    sub["disposition"] = disposition_for(&sub, &steps);
    let records: Vec<Value> = steps
        .iter()
        .map(|s| {
            let q = &s["sandbox_check"];
            json!({"step_id": s["step_id"], "operation": q["operation"], "filter_type": "PATH",
                "filter_type_id": 1, "filter_value": q["filter_value"], "outcome": q["outcome"],
                "rc": q["rc"], "errno": q["errno"]})
        })
        .collect();
    let ok = outcome == "ok";
    json!({"schema_version": json_contract::RESPONSE_SCHEMA_VERSION, "specimen_id": "controlled",
        "run_kind": null, "rc": if ok { 0 } else { 1 }, "normalized_outcome": outcome,
        "error": if ok { Value::Null } else { json!("controlled worker failure") },
        "pid": 9999, "bundle_id": "controlled.service", "policy_format": "sbpl",
        "policy_sha256": "0".repeat(64), "sandboxed_after_apply": true, "test_overrides": null,
        "runner_subprocess": sub,
        "validator_subprocess": {"pid": 43, "reaped": true, "exit_code": 0, "records": records},
        "steps": steps})
}

pub(crate) fn worker(outcome: &str, signal: Option<i32>) -> Value {
    reply_with(outcome, signal, vec![])
}

/// A degraded reply: the host withheld every comparison and said so.
pub(crate) fn reporting_failed(mut runner: Value) -> Value {
    runner["normalized_outcome"] = json!("runner_reporting_failed");
    runner["rc"] = json!(1);
    runner["error"] = json!("controlled reporting failure");
    runner["reporting_failure"] = json!({"origin": "runner_host", "diagnostic": "controlled",
        "original_rc": 0, "original_normalized_outcome": "ok", "original_error": null,
        "evidence_retained": true});
    for step in runner["steps"].as_array_mut().unwrap() {
        step["comparison"] = Value::Null;
    }
    runner
}
