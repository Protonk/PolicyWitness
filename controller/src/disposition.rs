//! Worker disposition record validation and projection for
//! `data.runner_sandbox_diagnostics`, grounded in native execution observations.

#[path = "actor_evidence.rs"]
mod actor_evidence;

use serde::Serialize;
use serde_json::{Value, json};

/// Only spawned-worker metadata identifies the worker; a host/client PID is
/// never a substitute for a missing worker observation.
fn worker_pid(result: Option<&Value>) -> Option<i32> {
    let pid = result?.get("runner_subprocess")?.get("pid")?.as_i64()?;
    i32::try_from(pid).ok().filter(|pid| *pid > 0)
}

#[derive(Serialize)]
pub(crate) struct RunnerExecutionDiagnostics {
    pub process_disposition: &'static str,
    pub termination_cause: Option<&'static str>,
    /// Projection of the worker disposition record's stop reason; null for an
    /// unresolved question.
    pub stop_reason: Option<String>,
    /// `valid` or `invalid` (claims withheld); null without a worker.
    pub disposition_integrity: Option<&'static str>,
    /// Integrity issues plus the record's own reported conflicts; empty when none.
    pub disposition_issues: Vec<Value>,
    /// The actor form: one projection per actor, in actor order. The singular
    /// fields above then read `per_actor`, with integrity valid only when every
    /// launched actor's record is valid.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub actors: Option<Vec<ActorExecutionDiagnostics>>,
}

#[derive(Serialize)]
pub(crate) struct ActorExecutionDiagnostics {
    pub actor_id: Option<String>,
    pub process_disposition: &'static str,
    pub termination_cause: Option<&'static str>,
    pub stop_reason: Option<String>,
    pub disposition_integrity: Option<&'static str>,
    pub disposition_issues: Vec<Value>,
}

// Worker disposition record projection (tests/FAILURE-PROPAGATION-CONTRACT.md,
// "Worker disposition record"). The controller validates the carried record
// against the raw facts it cites and projects from it; it never derives a
// competing lifecycle answer from raw fields or prose. Spellings are shared
// with tests/lib/lifecycle_contract.py.
const DISPOSITION_CLAIM_STATES: &[&str] =
    &["supported", "unresolved", "conflicting", "inapplicable"];
const DISPOSITION_RUN_QUESTIONS: &[&str] = &[
    "final_status",
    "stop_reason",
    "cleanup_trigger",
    "grace_end",
    "kill_request_and_result",
    "collection_basis",
    "progress_association",
];
const DISPOSITION_STEP_QUESTIONS: &[&str] = &[
    "step_boundary_reached",
    "step_result_published",
    "step_requested_operation_applicability",
];
const DISPOSITION_RUN_REFERENCES: &[&str] = &[
    "reaped",
    "exit_code",
    "term_signal",
    "poll_stop_reason",
    "exit_requested",
    "termination_request",
    "wait_errors",
    "cleanup_trigger",
    "grace_end",
    "collection_basis",
    "done_observed",
    "progress",
    "worker_failure",
    "plan",
];
const DISPOSITION_STEP_REFERENCES: &[&str] = &["slot", "attempt_support"];
const CAUSE_FOR_TRIGGER: &[(&str, &str)] = &[
    ("deadline_expiry", "host_sentinel_deadline"),
    ("completion", "host_exit_grace_exhausted"),
    ("poll_wait_error", "host_cleanup_after_wait_error"),
    ("policy_transfer_error", "host_cleanup_after_transfer_error"),
    (
        "policy_transfer_timeout",
        "host_cleanup_after_transfer_timeout",
    ),
];

struct DispositionProjection {
    disposition: &'static str,
    cause: Option<&'static str>,
    stop_reason: Option<String>,
    integrity: Option<&'static str>,
    issues: Vec<Value>,
}

pub(crate) fn integrity_issue(kind: &str, detail: String) -> Value {
    json!({"kind": kind, "detail": detail})
}

fn reference_resolves(token: &str, sub: &Value, step: Option<&Value>) -> bool {
    let present = |key: &str| sub.get(key).map_or(false, |v| !v.is_null());
    match token {
        "slot" | "attempt_support" => {
            step.map_or(false, |s| s.get(token).map_or(false, |v| !v.is_null()))
        }
        // Step count/order are retained by record.steps and checked against the reply.
        "plan" => true,
        "worker_failure" => sub
            .get("worker_evidence")
            .and_then(|e| e.get("failure"))
            .map_or(false, |v| v.is_object()),
        "progress" => sub
            .get("worker_evidence")
            .and_then(|e| e.get("progress"))
            .map_or(false, |v| !v.is_null()),
        // The host records an explicit non-request as an absent object once it has
        // recorded the cleanup stage, so the token resolves beside exit_requested.
        "termination_request" => present("termination_request") || present("exit_requested"),
        other => present(other),
    }
}

fn same_termination_request(a: &Value, b: &Value) -> bool {
    a.is_object()
        && b.is_object()
        && ["signal", "rc"]
            .iter()
            .all(|k| a[*k].as_i64().is_some() && a[*k] == b[*k])
        && a["errno"] == b["errno"]
}

// Necessary witness sets. Extra references must still resolve; an unrelated
// existing field cannot substitute for the observations that support an answer.
fn sufficient_disposition_basis(name: &str, claim: &Value) -> bool {
    let has = |tokens: &[&str]| {
        tokens.iter().all(|t| {
            claim["basis"]
                .as_array()
                .map_or(false, |b| b.iter().any(|v| v.as_str() == Some(t)))
        })
    };
    match (name, claim["answer"].as_str()) {
        ("final_status", Some("signal")) => has(&["reaped", "term_signal"]),
        ("final_status", Some("exit_code")) => has(&["reaped", "exit_code"]),
        ("stop_reason", _) => has(&["poll_stop_reason"]),
        ("cleanup_trigger" | "grace_end", _) => has(&[name, "exit_requested"]),
        ("collection_basis", _) => has(&["collection_basis"]),
        ("kill_request_and_result", Some("requested")) => has(&["termination_request"]),
        ("kill_request_and_result", Some("none")) => {
            has(&["termination_request", "exit_requested"])
        }
        ("progress_association", Some("step_index" | "invalid")) => has(&["progress", "plan"]),
        ("progress_association", Some("none" | "parameter_index")) => has(&["progress"]),
        ("step_requested_operation_applicability", _) => has(&["attempt_support"]),
        ("step_boundary_reached", Some("reached")) => {
            has(&["progress"]) || has(&["slot", "attempt_support"])
        }
        ("step_boundary_reached", Some("not_reached")) => {
            has(&["progress", "slot", "collection_basis"])
        }
        ("step_result_published", Some("published")) => has(&["slot", "attempt_support"]),
        ("step_result_published", Some("unpublished")) => has(&["slot", "collection_basis"]),
        _ => true, // Preserve future answers without inventing semantics for them.
    }
}

type DispositionPosition = (usize, u64, u64);

/// Temporal order of worker operations (pw_probe_runner_abi.h): clock setup (12)
/// follows header validation (1), proceed (11) precedes the indexed attempts (9).
// The actor form's parked activation wait (13) follows application and
// precedes each visit's release wait (11).
const PROTOCOL_ORDER: [u64; 13] = [1, 12, 2, 3, 4, 5, 6, 7, 8, 13, 11, 9, 10];

/// The protocol position of the indexed attempt operation.
fn attempt_position() -> usize {
    PROTOCOL_ORDER.iter().position(|v| *v == 9).unwrap()
}

fn disposition_progress(
    sub: &Value,
    count: usize,
) -> (Option<&str>, Option<i64>, Option<DispositionPosition>) {
    let progress = &sub["worker_evidence"]["progress"];
    let op = progress["operation"].as_u64();
    let stage = progress["stage"].as_u64();
    let order = PROTOCOL_ORDER.iter().position(|v| Some(*v) == op);
    let (Some(op), Some(stage @ (1 | 2)), Some(order)) = (op, stage, order) else {
        return (None, None, None);
    };
    let index = progress["index"].as_u64();
    let phase_wait = matches!(op, 11 | 13) && index.is_some();
    let indexed = op == 9 || op == 4 || phase_wait;
    if (indexed && index.is_none())
        || (!indexed && !progress["index"].is_null())
        || index.map_or(false, |i| {
            i >= 0xfffff || (op == 9 && i >= count as u64) || (phase_wait && i > count as u64)
        })
        || progress["raw"].as_u64() != Some((op << 24) | (stage << 20) | index.map_or(0, |i| i + 1))
    {
        return (Some("invalid"), None, None);
    }
    if phase_wait {
        return (
            Some("none"),
            None,
            Some((attempt_position(), index.unwrap(), 0)),
        );
    }
    (
        Some(if op == 9 {
            "step_index"
        } else if op == 4 {
            "parameter_index"
        } else {
            "none"
        }),
        index.map(|i| i as i64),
        Some((order, index.unwrap_or(0), stage)),
    )
}

fn disposition_summary(step: &Value) -> &'static str {
    let q = &step["questions"];
    let supported =
        |name: &str, answer: &str| q[name]["state"] == "supported" && q[name]["answer"] == answer;
    if step["attempt_support"] == "unsupported" {
        "unsupported"
    } else if supported("step_result_published", "published") {
        "completed"
    } else if q["step_boundary_reached"]["state"] == "conflicting"
        || q["step_result_published"]["state"] == "conflicting"
    {
        "conflicting"
    } else if supported("step_result_published", "unpublished")
        && supported("step_boundary_reached", "reached")
    {
        "started_without_result"
    } else if supported("step_result_published", "unpublished")
        && supported("step_boundary_reached", "not_reached")
    {
        "not_reached"
    } else {
        "unresolved"
    }
}

/// Structural and claim/basis validation of a carried record. Returns integrity
/// issues; `unrecognized_value` issues do not invalidate the record.
fn validate_disposition(
    record: &Value,
    sub: &Value,
    reply_steps: &[Value],
    reporting_failed: bool,
) -> Vec<Value> {
    let mut issues = Vec::new();
    let Some(questions) = record.get("questions").and_then(Value::as_object) else {
        return vec![integrity_issue(
            "malformed_record",
            "questions is not an object".into(),
        )];
    };
    let record_issues = record
        .get("issues")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    if record.get("issues").map_or(true, |v| !v.is_array()) {
        issues.push(integrity_issue(
            "malformed_record",
            "issues is not an array".into(),
        ));
    }
    let raw_str = |key: &str| sub.get(key).and_then(Value::as_str);
    let check_claim =
        |name: &str, claim: &Value, step: Option<(usize, &Value)>, issues: &mut Vec<Value>| {
            let where_ = match step {
                Some((i, _)) => format!("step {i} {name}"),
                None => name.to_string(),
            };
            let Some(state) = claim.get("state").and_then(Value::as_str) else {
                issues.push(integrity_issue(
                    "malformed_record",
                    format!("{where_}: claim without a state"),
                ));
                return;
            };
            if !DISPOSITION_CLAIM_STATES.contains(&state) {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("{where_}: unknown claim state {state}"),
                ));
                return;
            }
            match state {
                "supported" => {
                    if claim.get("answer").and_then(Value::as_str).is_none() {
                        issues.push(integrity_issue(
                            "invalid_claim",
                            format!("{where_}: supported claim without an answer"),
                        ));
                    }
                    match claim.get("basis").and_then(Value::as_array) {
                        Some(basis) if !basis.is_empty() => {
                            for value in basis {
                                let Some(token) = value.as_str() else {
                                    issues.push(integrity_issue(
                                        "invalid_claim",
                                        format!("{where_}: reference is not a string"),
                                    ));
                                    continue;
                                };
                                let known = DISPOSITION_RUN_REFERENCES.contains(&token)
                                    || (step.is_some()
                                        && DISPOSITION_STEP_REFERENCES.contains(&token));
                                if !known {
                                    issues.push(integrity_issue(
                                        "unresolved_reference",
                                        format!("{where_}: unknown reference {token}"),
                                    ));
                                } else if !reference_resolves(token, sub, step.map(|(_, s)| s)) {
                                    issues.push(integrity_issue(
                                        "unresolved_reference",
                                        format!("{where_}: {token} does not resolve"),
                                    ));
                                }
                            }
                        }
                        _ => issues.push(integrity_issue(
                            "invalid_claim",
                            format!("{where_}: supported claim without basis"),
                        )),
                    }
                    if !sufficient_disposition_basis(name, claim) {
                        issues.push(integrity_issue(
                            "invalid_claim",
                            format!("{where_}: insufficient witness references"),
                        ));
                    }
                }
                "conflicting" => {
                    let matches = claim
                        .get("issue")
                        .and_then(Value::as_u64)
                        .and_then(|i| record_issues.get(i as usize))
                        .map_or(false, |issue| {
                            issue.get("question").and_then(Value::as_str) == Some(name)
                                && issue.get("step_index").and_then(Value::as_u64)
                                    == step.map(|(i, _)| i as u64)
                                && issue["kind"] == "conflict"
                                && issue["rule"] == if name == "final_status" { "D1" } else { "D5" }
                                && [
                                    "final_status",
                                    "step_boundary_reached",
                                    "step_result_published",
                                ]
                                .contains(&name)
                                && issue["observations"].as_array().map_or(false, |obs| {
                                    let required: &[&str] = if name == "final_status" {
                                        &["exit_code", "term_signal"]
                                    } else {
                                        &["progress", "slot", "collection_basis"]
                                    };
                                    required
                                        .iter()
                                        .all(|t| obs.iter().any(|v| v.as_str() == Some(t)))
                                        && obs.iter().all(|v| {
                                            v.as_str().map_or(false, |t| {
                                                reference_resolves(t, sub, step.map(|(_, s)| s))
                                            })
                                        })
                                })
                        });
                    if !matches {
                        issues.push(integrity_issue(
                            "invalid_claim",
                            format!("{where_}: conflicting claim without a matching issue"),
                        ));
                    }
                }
                _ => {
                    if claim.get("reason").and_then(Value::as_str).is_none() {
                        issues.push(integrity_issue(
                            "invalid_claim",
                            format!("{where_}: {state} claim without a reason"),
                        ));
                    }
                }
            }
        };
    for name in DISPOSITION_RUN_QUESTIONS {
        match questions.get(*name) {
            Some(claim) => check_claim(name, claim, None, &mut issues),
            None => issues.push(integrity_issue(
                "malformed_record",
                format!("questions lacks {name}"),
            )),
        }
    }
    let reaped = sub.get("reaped").and_then(Value::as_bool) == Some(true);
    if raw_str("collection_basis") == Some("after_confirmed_reap") && !reaped {
        issues.push(integrity_issue(
            "invalid_claim",
            "collection_basis: terminal collection without a confirmed reap".into(),
        ));
    }
    for name in ["cleanup_trigger", "grace_end", "kill_request_and_result"] {
        if questions
            .get(name)
            .map_or(false, |q| q["state"] == "supported")
            && sub["exit_requested"] == false
        {
            issues.push(integrity_issue(
                "invalid_claim",
                format!("{name}: cleanup claim when exit was not requested"),
            ));
        }
    }
    let signal = sub.get("term_signal").and_then(Value::as_i64);
    let exit = sub.get("exit_code").and_then(Value::as_i64);
    if let Some(final_status) = questions.get("final_status") {
        let state = final_status.get("state").and_then(Value::as_str);
        let answer = final_status.get("answer").and_then(Value::as_str);
        let value = final_status.get("value").and_then(Value::as_i64);
        let contradiction = match (state, answer) {
            (Some("supported"), Some("signal")) => {
                !reaped || signal.is_none() || exit.is_some() || value != signal
            }
            (Some("supported"), Some("exit_code")) => {
                !reaped || exit.is_none() || signal.is_some() || value != exit
            }
            (Some("conflicting"), _) => !reaped || exit.is_none() || signal.is_none(),
            _ => false,
        };
        if contradiction {
            issues.push(integrity_issue(
                "invalid_claim",
                "final_status: claim contradicts reaped status".into(),
            ));
        }
    }
    for (name, key) in [
        ("stop_reason", "poll_stop_reason"),
        ("cleanup_trigger", "cleanup_trigger"),
        ("grace_end", "grace_end"),
        ("collection_basis", "collection_basis"),
    ] {
        if let Some(claim) = questions.get(name) {
            if claim.get("state").and_then(Value::as_str) == Some("supported")
                && claim.get("answer").and_then(Value::as_str) != raw_str(key)
            {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("{name}: claim contradicts the recorded host fact"),
                ));
            }
        }
    }
    if let Some(kill) = questions.get("kill_request_and_result") {
        if kill.get("state").and_then(Value::as_str) == Some("supported") {
            let request = sub
                .get("termination_request")
                .map_or(false, |v| v.is_object());
            match kill.get("answer").and_then(Value::as_str) {
                Some("requested")
                    if !request
                        || !same_termination_request(
                            &kill["value"],
                            &sub["termination_request"],
                        ) =>
                {
                    issues.push(integrity_issue(
                        "invalid_claim",
                        "kill_request_and_result: value differs from termination_request".into(),
                    ))
                }
                Some("none") if request => issues.push(integrity_issue(
                    "invalid_claim",
                    "kill_request_and_result: no-request claim beside a termination_request".into(),
                )),
                _ => {}
            }
        }
    }
    let Some(steps) = record.get("steps").and_then(Value::as_array) else {
        issues.push(integrity_issue(
            "malformed_record",
            "steps is not an array".into(),
        ));
        return issues;
    };
    if steps.len() != reply_steps.len() {
        issues.push(integrity_issue(
            "invalid_claim",
            format!(
                "disposition steps ({}) disagree with reply steps ({})",
                steps.len(),
                reply_steps.len()
            ),
        ));
    }
    let terminal = raw_str("collection_basis") == Some("after_confirmed_reap") && reaped;
    let (association, index, position) = disposition_progress(sub, steps.len());
    if let Some(claim) = questions.get("progress_association") {
        if claim["state"] == "supported"
            && matches!(
                claim["answer"].as_str(),
                Some("none" | "invalid" | "step_index" | "parameter_index")
            )
            && (claim["answer"].as_str() != association || claim["value"].as_i64() != index)
        {
            issues.push(integrity_issue(
                "invalid_claim",
                "progress_association: claim disagrees with progress identity".into(),
            ));
        }
    }
    if sub["partial_steps"].as_bool() != Some(steps.iter().any(|s| s["slot"] != "completed")) {
        issues.push(integrity_issue(
            "invalid_claim",
            "partial_steps disagrees with record slots".into(),
        ));
    }
    for (i, step) in steps.iter().enumerate() {
        if step.get("index").and_then(Value::as_u64) != Some(i as u64) {
            issues.push(integrity_issue(
                "malformed_record",
                format!("step {i} carries the wrong index"),
            ));
        }
        if let Some(reply_step) = reply_steps.get(i) {
            if step.get("step_id") != reply_step.get("step_id") {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i}: step_id disagrees with the reply"),
                ));
            }
        }
        let slot = step.get("slot").and_then(Value::as_str);
        let supported = step["attempt_support"] == "supported";
        let reached = position.map_or(false, |p| p >= (attempt_position(), i as u64, 1));
        let returned = position.map_or(false, |p| p >= (attempt_position(), i as u64, 2));
        let boundary_conflict =
            terminal && position.is_some() && !reached && slot == Some("completed");
        let result_conflict = terminal && returned && slot == Some("incomplete") && supported;
        if !matches!(slot, Some("completed" | "incomplete" | "absent")) {
            issues.push(integrity_issue(
                "malformed_record",
                format!("step {i}: unknown slot state"),
            ));
        }
        if !matches!(
            step.get("attempt_support").and_then(Value::as_str),
            Some("supported" | "unsupported")
        ) {
            issues.push(integrity_issue(
                "malformed_record",
                format!("step {i}: unknown attempt support"),
            ));
        }
        let Some(claims) = step.get("questions").and_then(Value::as_object) else {
            issues.push(integrity_issue(
                "malformed_record",
                format!("step {i}: questions is not an object"),
            ));
            continue;
        };
        for name in DISPOSITION_STEP_QUESTIONS {
            match claims.get(*name) {
                Some(claim) => check_claim(name, claim, Some((i, step)), &mut issues),
                None => issues.push(integrity_issue(
                    "malformed_record",
                    format!("step {i} lacks question {name}"),
                )),
            }
        }
        if let Some(applicability) = claims.get("step_requested_operation_applicability") {
            if applicability["state"] == "supported"
                && matches!(
                    applicability["answer"].as_str(),
                    Some("supported" | "unsupported")
                )
                && applicability["answer"] != step["attempt_support"]
            {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i}: applicability disagrees with attempt support"),
                ));
            }
        }
        if let Some(result) = claims.get("step_result_published") {
            if result.get("state").and_then(Value::as_str) == Some("supported") {
                match result.get("answer").and_then(Value::as_str) {
                    Some("published") if slot != Some("completed") || !supported => issues.push(integrity_issue("invalid_claim",
                        format!("step {i}: published claim on a slot that is not completed"))),
                    Some("unpublished") if slot != Some("incomplete") || !terminal || !supported || result_conflict => issues.push(integrity_issue(
                        "invalid_claim", format!("step {i}: unpublished claim needs an incomplete slot under terminal collection"))),
                    _ => {}
                }
            }
        }
        if let Some(boundary) = claims.get("step_boundary_reached") {
            let cites = |token: &str| {
                boundary["basis"].as_array().map_or(false, |basis| {
                    basis.iter().any(|v| v.as_str() == Some(token))
                })
            };
            let progress_witness = reached && cites("progress");
            let slot_witness =
                slot == Some("completed") && supported && cites("slot") && cites("attempt_support");
            if boundary.get("state").and_then(Value::as_str) == Some("supported")
                && boundary.get("answer").and_then(Value::as_str) == Some("not_reached")
                && (!terminal || slot == Some("completed") || position.is_none() || reached)
            {
                issues.push(integrity_issue("invalid_claim",
                    format!("step {i}: not_reached claim needs terminal collection and no completed slot")));
            }
            if boundary["state"] == "supported"
                && boundary["answer"] == "reached"
                && (boundary_conflict || !(progress_witness || slot_witness))
            {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i}: reached claim lacks an unopposed boundary witness"),
                ));
            }
        }
        for (name, conflict) in [
            ("step_boundary_reached", boundary_conflict),
            ("step_result_published", result_conflict),
        ] {
            if claims
                .get(name)
                .map_or(false, |q| q["state"] == "conflicting")
                && !conflict
            {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i} {name}: conflict without incompatible observations"),
                ));
            }
        }
        if let Some(reply) = reply_steps.get(i) {
            let is_event = reply.get("operation").is_some();
            let attempt = &reply["attempt"];
            let completed = supported && slot == Some("completed");
            let reason = if completed {
                None
            } else if !supported {
                Some("attempt_not_supported")
            } else if slot == Some("absent") {
                Some("slot_absent")
            } else {
                Some("slot_incomplete")
            };
            if (is_event && reply["result_published"].as_bool() != Some(completed))
                || (!is_event
                    && (attempt["result_source"] != if completed { "worker" } else { "synthetic" }
                        || attempt["missing_reason"].as_str() != reason))
            {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i}: compatibility projections disagree with record"),
                ));
            }
            let lifecycle = if is_event {
                &reply["lifecycle"]
            } else {
                &attempt["lifecycle"]
            };
            if is_event {
                let native = reply.get("native_result").and_then(Value::as_i64);
                let valid = if reply["operation"] == "transfer" {
                    reply["call_boundary_observed"] == false
                        && native.is_none()
                        && reply["errno"].is_null()
                        && reply["unavailable_reason"].is_null()
                        && if completed {
                            actor_transfer_status(reply["status"].as_str().unwrap_or(""))
                        } else {
                            reply["status"] == "unresolved"
                        }
                } else {
                    match reply["status"].as_str() {
                        Some("returned") => {
                            completed
                                && reply["call_boundary_observed"] == true
                                && native.is_some()
                                && reply["errno"].as_i64().is_some()
                                && reply["unavailable_reason"].is_null()
                        }
                        Some("unavailable") => {
                            completed
                                && reply["call_boundary_observed"] == false
                                && native.is_none()
                                && reply["errno"].is_null()
                                && reply["unavailable_reason"].is_string()
                        }
                        Some("unresolved") => {
                            !completed
                                && native.is_none()
                                && reply["errno"].is_null()
                                && reply["unavailable_reason"].is_null()
                        }
                        _ => false,
                    }
                };
                if !valid {
                    issues.push(integrity_issue(
                        "invalid_claim",
                        format!("step {i}: native lifecycle publication is inconsistent"),
                    ));
                }
            }
            if lifecycle["boundary"] != step["questions"]["step_boundary_reached"]
                || lifecycle["result"] != step["questions"]["step_result_published"]
            {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i}: lifecycle copies disagree with record"),
                ));
            }
            let summary = disposition_summary(step);
            match lifecycle["summary"].as_str() {
                Some(
                    s @ ("completed"
                    | "started_without_result"
                    | "not_reached"
                    | "unsupported"
                    | "unresolved"
                    | "conflicting"),
                ) if s != summary => issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i}: lifecycle summary disagrees with record"),
                )),
                None => issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i}: missing lifecycle summary"),
                )),
                _ => {}
            }
            let expected = match summary {
                "completed" => None,
                "unresolved" => Some("attempt:lifecycle_unresolved"),
                "conflicting" => Some("attempt:lifecycle_conflicting"),
                "unsupported" => Some("attempt:unsupported"),
                "not_reached" => Some("attempt:not_reached"),
                _ => Some("attempt:started_without_result"),
            };
            let limits: Vec<_> = reply["comparison"]["limitations"]
                .as_array()
                .into_iter()
                .flatten()
                .filter_map(Value::as_str)
                .filter(|l| {
                    [
                        "attempt:lifecycle_unresolved",
                        "attempt:lifecycle_conflicting",
                        "attempt:unsupported",
                        "attempt:not_reached",
                        "attempt:started_without_result",
                    ]
                    .contains(l)
                })
                .collect();
            if !is_event
                && !(reporting_failed && reply["comparison"].is_null())
                && limits != expected.into_iter().collect::<Vec<_>>()
            {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i}: lifecycle limitations disagree with record"),
                ));
            }
        }
    }
    for (index, _) in record_issues.iter().enumerate() {
        let referenced = questions
            .values()
            .chain(
                steps
                    .iter()
                    .filter_map(|s| s["questions"].as_object())
                    .flat_map(|q| q.values()),
            )
            .any(|c| c["state"] == "conflicting" && c["issue"].as_u64() == Some(index as u64));
        if !referenced {
            issues.push(integrity_issue(
                "invalid_claim",
                format!("issue {index} is unreferenced"),
            ));
        }
    }
    issues
}

fn project_disposition(
    sub: &Value,
    reply_steps: &[Value],
    reporting_failed: bool,
) -> DispositionProjection {
    let Some(record) = sub.get("disposition").filter(|r| !r.is_null()) else {
        // A worker subprocess without the record is invalid; its claims are withheld.
        return DispositionProjection {
            disposition: "withheld",
            cause: Some("unknown"),
            stop_reason: None,
            integrity: Some("invalid"),
            issues: vec![integrity_issue(
                "missing_record",
                "a worker subprocess requires a disposition record".into(),
            )],
        };
    };
    let mut issues = validate_disposition(record, sub, reply_steps, reporting_failed);
    let invalid = issues
        .iter()
        .any(|i| i.get("kind").and_then(Value::as_str) != Some("unrecognized_value"));
    if invalid {
        return DispositionProjection {
            disposition: "withheld",
            cause: Some("unknown"),
            stop_reason: None,
            integrity: Some("invalid"),
            issues,
        };
    }
    let questions = &record["questions"];
    let claim = |name: &str| &questions[name];
    let state = |name: &str| claim(name).get("state").and_then(Value::as_str);
    let answer = |name: &str| claim(name).get("answer").and_then(Value::as_str);
    let final_state = state("final_status");
    let final_answer = answer("final_status");
    let final_value = claim("final_status").get("value").and_then(Value::as_i64);
    let disposition = match (final_state, final_answer) {
        (Some("supported"), Some("signal")) => "signaled",
        (Some("supported"), Some("exit_code")) => {
            if final_value == Some(0) {
                "clean_exit"
            } else {
                "nonzero_exit"
            }
        }
        (Some("supported"), Some(other)) => {
            issues.push(integrity_issue(
                "unrecognized_value",
                format!("final_status: unrecognized answer {other}"),
            ));
            "unrecognized"
        }
        (Some("conflicting"), _) => "conflicting",
        (Some("unresolved"), _) | (Some("inapplicable"), _) => "unconfirmed",
        _ => "unrecognized",
    };
    let mut cause = if disposition == "clean_exit" {
        None
    } else {
        Some("unknown")
    };
    if disposition == "signaled" {
        let requested_signal = claim("kill_request_and_result")
            .get("value")
            .and_then(|v| v.get("signal"))
            .and_then(Value::as_i64);
        let requested_rc = claim("kill_request_and_result")
            .get("value")
            .and_then(|v| v.get("rc"))
            .and_then(Value::as_i64);
        if state("cleanup_trigger") == Some("supported")
            && state("grace_end") == Some("supported")
            && answer("grace_end") == Some("exhausted")
            && state("kill_request_and_result") == Some("supported")
            && answer("kill_request_and_result") == Some("requested")
            && requested_rc == Some(0)
            && requested_signal == final_value
        {
            if let Some((_, label)) = CAUSE_FOR_TRIGGER
                .iter()
                .find(|(trigger, _)| Some(*trigger) == answer("cleanup_trigger"))
            {
                cause = Some(label);
            }
        }
    }
    let stop_reason = if state("stop_reason") == Some("supported") {
        answer("stop_reason")
            .filter(|s| {
                [
                    "sentinel_deadline",
                    "done",
                    "child_reaped",
                    "wait_error",
                    "policy_write_error",
                    "policy_transfer_deadline",
                ]
                .contains(s)
            })
            .map(str::to_string)
    } else {
        None
    };
    if let Some(conflicts) = record.get("issues").and_then(Value::as_array) {
        issues.extend(conflicts.iter().cloned());
    }
    DispositionProjection {
        disposition,
        cause,
        stop_reason,
        integrity: Some("valid"),
        issues,
    }
}

// Native actions exist only in the actor model. Removed declaration keys are
// rejected even when explicitly null; no historical semantic reader survives.
fn extension_account_issues(runner: &Value) -> Vec<Value> {
    let mut issues: Vec<Value> = actor_evidence::validate(runner)
        .into_iter()
        .map(|detail| integrity_issue("actor_evidence", detail))
        .collect();
    if runner["execution_form"] == "actors" {
        issues.extend(actor_extension_issues(runner));
    }
    issues
}

// Optional bounded exec evidence. Absence carries no negative cleanup fact.
/// The actor form's extension evidence rules, shared with the Swift encoder
/// and the Python reader: every event names a live actor and one of its
/// phases, references resolve in the resource tables to their owners,
/// transfers carry no native result, and each status is published only by the
/// shape it claims.
fn actor_transfer_status(status: &str) -> bool {
    matches!(
        status,
        "none"
            | "delivered"
            | "custody_unavailable"
            | "recipient_rejected"
            | "recipient_timeout"
            | "recipient_unavailable"
            | "request_invalid"
            | "host_timeout"
            | "clock_fault"
            | "copy_mismatch"
    )
}

fn actor_extension_issues(runner: &Value) -> Vec<Value> {
    let mut issues = Vec::new();
    let mut reject =
        |detail: &str| issues.push(integrity_issue("extension_evidence", detail.into()));
    let empty = Vec::new();
    let events = runner["extension_events"].as_array().unwrap_or(&empty);
    let (Some(actors), Some(resources), Some(transfers)) = (
        runner["actors"].as_array(),
        runner["resources"].as_object(),
        runner["transfers"].as_array(),
    ) else {
        reject("actor form lacks actor, resource or transfer tables");
        return issues;
    };
    if !runner["extensions"].is_null()
        || !runner["runner_subprocess"].is_null()
        || !runner["policy_sha256"].is_null()
        || !runner["sandboxed_after_apply"].is_null()
    {
        reject("actor form carries singular projections");
        return issues;
    }
    let tokens = resources["tokens"].as_array().unwrap_or(&empty);
    let deliveries = resources["deliveries"].as_array().unwrap_or(&empty);
    let handles = resources["handles"].as_array().unwrap_or(&empty);
    if actors.is_empty()
        || actors.len() > 8
        || tokens.len() > 32
        || deliveries.len() > 64
        || handles.len() > 64
        || transfers.len() > 64
        || events.len() > 32 + 128 + 64 + 64
    {
        reject("actor extension record capacity");
        return issues;
    }
    for actor in actors {
        if !matches!(actor["application_count"].as_u64(), Some(0 | 1))
            || (actor["application_count"] == 1) != (actor["applied"] == true)
            || (actor["setup_status"] == "applied" && actor["applied"] != true)
        {
            reject("application count contradicts application publication");
        }
    }
    let reference = |v: &Value| {
        v.as_str()
            .is_some_and(|s| !s.is_empty() && s.len() <= 63 && !s.contains('\0'))
    };
    let phases = runner["phases"].as_array().unwrap_or(&empty);
    let action_ids: Vec<&Value> = phases
        .iter()
        .flat_map(|p| p["action_ids"].as_array().into_iter().flatten())
        .collect();
    for (table, key) in [
        (tokens, "token_ref"),
        (deliveries, "delivery_ref"),
        (handles, "handle_ref"),
        (transfers, "delivery_ref"),
    ] {
        let mut seen = std::collections::BTreeSet::new();
        if table
            .iter()
            .any(|row| !reference(&row[key]) || !seen.insert(row[key].as_str().unwrap_or("")))
        {
            reject("resource and transfer references must be unique");
        }
    }
    let before = |first: &Value, second: &Value| {
        matches!((action_ids.iter().position(|id| **id == *first), action_ids.iter().position(|id| **id == *second)),
                 (Some(a), Some(b)) if a < b)
    };
    let transfer_statuses = [
        "none",
        "delivered",
        "custody_unavailable",
        "recipient_rejected",
        "recipient_timeout",
        "recipient_unavailable",
        "request_invalid",
        "host_timeout",
        "clock_fault",
        "copy_mismatch",
    ];
    let mut consumed: std::collections::BTreeMap<String, &Value> = Default::default();
    let mut released = std::collections::BTreeSet::new();
    for event in events {
        let actor_id = &event["actor_id"];
        let Some(actor) = actors
            .iter()
            .find(|a| actor_id.is_string() && a["actor_id"] == *actor_id)
        else {
            reject("extension event actor");
            continue;
        };
        let Some(phase) = phases.iter().find(|p| {
            p["phase_id"] == event["phase_id"]
                && p["action_ids"]
                    .as_array()
                    .is_some_and(|ids| ids.contains(&event["step_id"]))
        }) else {
            reject("extension event phase association");
            continue;
        };
        if phase["actor_id"] != *actor_id {
            reject("extension event phase association");
            continue;
        }
        if event["family"] != "file" {
            reject("extension event family");
            continue;
        }
        let status = event["status"].as_str().unwrap_or("");
        let published = event["result_published"] == true;
        let called = event["call_boundary_observed"] == true;
        match event["operation"].as_str() {
            Some("issue") => {
                let ok = reference(&event["token_ref"])
                    && tokens.iter().any(|t| {
                        t["token_ref"] == event["token_ref"]
                            && t["actor_id"] == *actor_id
                            && t["step_id"] == event["step_id"]
                    })
                    && event["handle_ref"].is_null()
                    && event["delivery_ref"].is_null();
                if !ok {
                    reject("issue reference");
                }
                if status == "returned"
                    && (!matches!(event["native_result"].as_i64(), Some(0 | 1))
                        || event["native_nonnull"].as_bool() != Some(event["native_result"] == 1))
                {
                    reject("issue nonnull disagrees with native result");
                }
            }
            Some("transfer") => {
                let ok = reference(&event["token_ref"])
                    && reference(&event["delivery_ref"])
                    && deliveries.iter().any(|d| {
                        d["delivery_ref"] == event["delivery_ref"]
                            && d["token_ref"] == event["token_ref"]
                            && d["source_actor_id"] == *actor_id
                            && d["step_id"] == event["step_id"]
                    })
                    && event["handle_ref"].is_null();
                if !ok {
                    reject("transfer reference");
                }
                if !tokens.iter().any(|t| {
                    t["token_ref"] == event["token_ref"]
                        && t["actor_id"] == *actor_id
                        && before(&t["step_id"], &event["step_id"])
                }) {
                    reject("transfer token owner/order");
                }
                if called || !event["native_result"].is_null() || !event["errno"].is_null() {
                    reject("transfer carries a native result");
                }
                let status_ok = if status == "unresolved" {
                    !published
                } else {
                    published && transfer_statuses.contains(&status)
                };
                if !status_ok {
                    reject("transfer status");
                }
            }
            Some("consume") => {
                let handle = event["handle_ref"].as_str().unwrap_or("").to_string();
                let ok = reference(&event["delivery_ref"])
                    && reference(&event["handle_ref"])
                    && handles.iter().any(|h| {
                        h["handle_ref"] == event["handle_ref"]
                            && h["delivery_ref"] == event["delivery_ref"]
                            && h["actor_id"] == *actor_id
                            && h["step_id"] == event["step_id"]
                    })
                    && event["token_ref"].is_null();
                if !ok || consumed.contains_key(&handle) {
                    reject("consume reference");
                }
                if !deliveries.iter().any(|d| {
                    d["delivery_ref"] == event["delivery_ref"]
                        && d["recipient_actor_id"] == *actor_id
                        && before(&d["step_id"], &event["step_id"])
                }) {
                    reject("consume delivery recipient/order");
                }
                consumed.insert(handle, event);
            }
            Some("release") => {
                let handle = event["handle_ref"].as_str().unwrap_or("").to_string();
                let prior = consumed.get(&handle).copied();
                let order_ok = prior.is_some_and(|p| {
                    let first = action_ids.iter().position(|id| **id == p["step_id"]);
                    let second = action_ids.iter().position(|id| **id == event["step_id"]);
                    matches!((first, second), (Some(a), Some(b)) if a < b)
                });
                let ok = reference(&event["handle_ref"])
                    && event["token_ref"].is_null()
                    && event["delivery_ref"].is_null()
                    && handles.iter().any(|h| {
                        h["handle_ref"] == event["handle_ref"]
                            && h["actor_id"] == *actor_id
                            && h["release_step_id"] == event["step_id"]
                    })
                    && !released.contains(&handle)
                    && order_ok;
                if !ok {
                    reject("release reference/order");
                }
                released.insert(handle);
                if status == "returned"
                    && prior.is_some_and(|p| {
                        p["status"] != "returned"
                            || p["native_result"].is_null()
                            || p["native_result"] == -1
                    })
                {
                    reject("release lacks an observed consume handle");
                }
            }
            _ => {
                reject("unknown extension operation");
                continue;
            }
        }
        if event["operation"] != "transfer" {
            match status {
                "returned" => {
                    if !published
                        || !called
                        || event["native_result"].is_null()
                        || !event["errno"].as_i64().is_some_and(|e| e >= 0)
                        || !event["unavailable_reason"].is_null()
                    {
                        reject("native extension result lacks publication");
                    }
                }
                "unavailable" => {
                    let reason = event["unavailable_reason"].as_str().unwrap_or("");
                    if !published
                        || called
                        || !event["native_result"].is_null()
                        || !event["errno"].is_null()
                        || ![
                            "token_unavailable",
                            "handle_unavailable",
                            "native_api_unavailable",
                            "repeated_action",
                            "authority_channel_unavailable",
                            "delivery_unavailable",
                        ]
                        .contains(&reason)
                    {
                        reject("unavailable extension action fabricates a call");
                    }
                }
                "unresolved" => {
                    if published
                        || !event["native_result"].is_null()
                        || !event["errno"].is_null()
                        || !event["unavailable_reason"].is_null()
                    {
                        reject("unpublished extension result must stay unresolved");
                    }
                }
                _ => reject("invalid extension event status"),
            }
        }
        let record = actor["subprocess"]["disposition"]["steps"]
            .as_array()
            .and_then(|steps| steps.iter().find(|s| s["step_id"] == event["step_id"]));
        match record {
            Some(step) => {
                if published != (step["slot"] == "completed")
                    || event["lifecycle"]["boundary"] != step["questions"]["step_boundary_reached"]
                    || event["lifecycle"]["result"] != step["questions"]["step_result_published"]
                {
                    reject("extension publication disagrees with disposition");
                }
            }
            None => {
                if actor["subprocess"].is_object()
                    || called
                    || published
                    || !event["lifecycle"].is_null()
                {
                    reject("extension event lacks disposition");
                }
            }
        }
        let setup = actor["setup_status"].as_str().unwrap_or("");
        if (published || called)
            && (phase["ordering"]["proceed_observed"] != true
                || !["applied", "unapplied_declared"].contains(&setup))
        {
            reject("extension publication lacks setup and phase acknowledgement");
        }
    }
    for transfer in transfers {
        let ok = deliveries.iter().any(|d| {
            d["delivery_ref"] == transfer["delivery_ref"]
                && d["token_ref"] == transfer["token_ref"]
                && d["source_actor_id"] == transfer["source_actor_id"]
                && d["recipient_actor_id"] == transfer["recipient_actor_id"]
                && d["step_id"] == transfer["step_id"]
        }) && transfer["status"]
            .as_str()
            .is_some_and(|s| transfer_statuses.contains(&s));
        if !ok {
            reject("transfer record association");
        }
        if !events.iter().any(|e| {
            e["operation"] == "transfer"
                && e["delivery_ref"] == transfer["delivery_ref"]
                && e["phase_id"] == transfer["phase_id"]
                && e["lifecycle"] == transfer["lifecycle"]
        }) {
            reject("transfer source phase/lifecycle association");
        }
    }
    for transfer in transfers {
        if transfer["status"] == "delivered"
            && (transfer["request_published"] != true
                || transfer["custody_status"] != "held"
                || transfer["copy_status"] != "copied"
                || transfer["equality"] != "equal"
                || transfer["recipient_acknowledged"] != true)
        {
            reject("delivered transfer lacks custody, copy or recipient acknowledgement");
        }
        if transfer["source_acknowledged"] == true
            && !events.iter().any(|e| {
                e["operation"] == "transfer"
                    && e["step_id"] == transfer["step_id"]
                    && e["actor_id"] == transfer["source_actor_id"]
                    && e["result_published"] == true
                    && e["status"] == transfer["status"]
            })
        {
            reject("source acknowledgement lacks matching publication");
        }
    }
    for (table, operation, reference) in [
        (tokens, "issue", "token_ref"),
        (handles, "consume", "handle_ref"),
        (deliveries, "transfer", "delivery_ref"),
    ] {
        for resource in table {
            let matches: Vec<_> = events
                .iter()
                .filter(|e| e["operation"] == operation && e[reference] == resource[reference])
                .collect();
            if matches.len() != 1 {
                reject("resource lacks unique producing event");
                continue;
            }
            let event = matches[0];
            if operation == "transfer" {
                if !actors
                    .iter()
                    .any(|a| a["actor_id"] == resource["recipient_actor_id"])
                {
                    reject("delivery recipient does not exist");
                }
                if let Some(host) = transfers
                    .iter()
                    .find(|t| t["delivery_ref"] == resource[reference])
                {
                    // The host's observation survives missing source publication.
                    if resource["status"] != host["status"]
                        || resource["equality"] != host["equality"]
                    {
                        reject("delivery projection contradicts host transfer");
                    }
                    if host["status"] == "delivered" {
                        let length = resource["delivered_length"].as_u64();
                        let token = tokens
                            .iter()
                            .find(|t| t["token_ref"] == resource["token_ref"]);
                        if !length.is_some_and(|n| (1..16384).contains(&n))
                            || token.is_some_and(|t| {
                                !t["token_length"].is_null()
                                    && t["token_length"] != resource["delivered_length"]
                            })
                        {
                            reject("delivered length contradicts custody");
                        }
                    } else if !resource["delivered_length"].is_null() {
                        reject("undelivered resource carries delivered length");
                    }
                    continue;
                }
                if !resource["equality"].is_null()
                    || !resource["delivered_length"].is_null()
                    || !["none", "host_timeout", "clock_fault", "unresolved"]
                        .contains(&event["status"].as_str().unwrap_or(""))
                {
                    reject("delivery claims host observation without transfer");
                }
                if event["result_published"] == true
                    && resource["status"]
                        != event["unavailable_reason"]
                            .as_str()
                            .unwrap_or("unrequested")
                {
                    reject("unobserved delivery status contradicts source");
                }
            }
            if event["result_published"] != true {
                let boundary = &event["lifecycle"]["boundary"];
                let status = if boundary["state"] == "supported"
                    && boundary["answer"] == "not_reached"
                    && event["call_boundary_observed"] == false
                {
                    "not_reached"
                } else {
                    "unresolved"
                };
                if resource["status"] != status {
                    reject("unpublished resource status contradicts lifecycle");
                }
            } else if operation == "issue" {
                let valid = if event["status"] == "unavailable" {
                    resource["status"] == "unavailable"
                } else if event["native_result"] == 0 {
                    resource["status"] == "null"
                } else {
                    resource["status"] == "issued" || resource["status"] == "issued_uncustodied"
                };
                if !valid {
                    reject("token status contradicts issue");
                }
            } else if operation == "consume" {
                let status = if event["status"] == "unavailable" {
                    "unavailable"
                } else if event["native_result"] == -1 {
                    "consume_failed"
                } else {
                    "produced"
                };
                if resource["status"] != status {
                    reject("handle status or value contradicts consume");
                }
            }
            if operation == "consume"
                && resource["native_handle"]
                    != if resource["status"] == "produced" {
                        event["native_result"].clone()
                    } else {
                        Value::Null
                    }
            {
                reject("handle status or value contradicts consume");
            }
            if operation == "issue"
                && (resource["family"] != "file"
                    || resource["token_length"] != event["token_length"]
                    || (resource["status"] == "issued"
                        && !resource["token_length"]
                            .as_u64()
                            .is_some_and(|n| (1..16384).contains(&n))))
            {
                reject("token metadata contradicts issue");
            }
            if operation == "consume" {
                let release = events.iter().find(|e| {
                    e["operation"] == "release" && e["handle_ref"] == resource[reference]
                });
                if &resource["release_step_id"]
                    != release.map(|e| &e["step_id"]).unwrap_or(&Value::Null)
                    || resource["release_attempted"].as_bool()
                        != Some(release.is_some_and(|e| e["call_boundary_observed"] == true))
                {
                    reject("handle release projection contradicts event");
                }
                let equal: std::collections::BTreeSet<_> = handles
                    .iter()
                    .filter(|h| {
                        h["handle_ref"] != resource[reference]
                            && h["actor_id"] == resource["actor_id"]
                            && !resource["native_handle"].is_null()
                            && h["native_handle"] == resource["native_handle"]
                    })
                    .filter_map(|h| h["handle_ref"].as_str())
                    .collect();
                let observed = resource["raw_equal_handles"].as_array();
                let unique: std::collections::BTreeSet<_> = observed
                    .into_iter()
                    .flatten()
                    .filter_map(Value::as_str)
                    .collect();
                if observed.is_none_or(|a| a.len() != unique.len()) || unique != equal {
                    reject("handle equality projection contradicts native handles");
                }
            }
        }
    }
    issues
}

fn exec_observation_problem(attempt: &Value) -> Option<&'static str> {
    let value = &attempt["exec_observation"];
    if value.is_null() {
        return None;
    }
    let i32_value = |v: &Value| {
        v.as_i64()
            .filter(|n| (i32::MIN as i64..=i32::MAX as i64).contains(n))
    };
    let positive = |v: &Value| v.is_null() || i32_value(v).is_some_and(|n| n > 0);
    let pid = match i32_value(&attempt["child_pid"]) {
        Some(pid) if pid > 0 => pid,
        _ => return Some("exec observation requires positive native child PID"),
    };
    if !value.is_object()
        || attempt["requested_kind"] != "exec"
        || attempt["requested_action"] != "spawn"
        || attempt["result_source"] != "worker"
        || attempt["lifecycle"]["summary"] != "completed"
    {
        return Some("exec observation requires published worker exec");
    }
    let c = &value["collection"];
    let k = &value["cleanup"];
    let r = &value["reap"];
    let out = &c["stdout"];
    let err = &c["stderr"];
    let wait = &r["last_wait"];
    if ![c, k, r, out, err, wait].iter().all(|v| v.is_object())
        || !c["leader_exit_observed"].is_boolean()
    {
        return Some("exec observation lacks typed sections");
    }
    for stream in [out, err] {
        let read = &stream["read_errno"];
        let events = &stream["poll_revents"];
        let event_ok = events.is_null()
            || i32_value(events)
                .is_some_and(|n| n >= -32768 && n <= 32767 && n & 0x28 != 0 && n & 0x11 == 0);
        if !stream["eof"].is_boolean()
            || !positive(read)
            || matches!(read.as_i64(), Some(4 | 35))
            || !event_ok
            || (stream["eof"] == true && (!read.is_null() || !events.is_null()))
            || (!read.is_null() && !events.is_null())
        {
            return Some("invalid exec stream observation");
        }
    }
    let wi = &c["waitid_errno"];
    let po = &c["poll_errno"];
    if !positive(wi) || !positive(po) || wi == 4 || po == 4 {
        return Some("invalid exec collection errno");
    }
    for fault in [&c["clock_fault"], &r["clock_fault"]] {
        if !fault.is_null()
            && !fault
                .as_u64()
                .is_some_and(|n| n > 0 && n <= u32::MAX as u64)
        {
            return Some("invalid exec clock reason");
        }
    }
    let stream_error = [out, err]
        .iter()
        .any(|s| !s["read_errno"].is_null() || !s["poll_revents"].is_null());
    let errors = !wi.is_null() || !po.is_null() || stream_error;
    if !wi.is_null() && c["leader_exit_observed"] == true {
        return Some("waitid failure after already observed leader exit");
    }
    if (!wi.is_null() && (!po.is_null() || stream_error)) || (!po.is_null() && stream_error) {
        return Some("incompatible exec collection branches");
    }
    let collection_stop = c["stop_reason"].as_str();
    let fault = &c["clock_fault"];
    let deadline = &c["deadline_kind"];
    let collection_valid = match collection_stop {
        Some("leader_exit_and_eof") => {
            c["leader_exit_observed"] == true
                && out["eof"] == true
                && err["eof"] == true
                && !errors
                && fault.is_null()
                && deadline.is_null()
        }
        Some("deadline") => {
            matches!(deadline.as_str(), Some("child" | "plan")) && !errors && fault.is_null()
        }
        Some("observation_error") => errors && fault.is_null() && deadline.is_null(),
        Some("clock_fault") => !fault.is_null() && !errors && deadline.is_null(),
        _ => false,
    };
    if !collection_valid {
        return Some("exec collection stop contradicts observations");
    }
    let signal_valid = |request: &Value, target: i64| {
        request.is_object()
            && i32_value(&request["target"]) == Some(target)
            && i32_value(&request["signal"]) == Some(9)
            && match i32_value(&request["rc"]) {
                Some(-1) => i32_value(&request["errno"]).is_some_and(|n| n > 0),
                Some(0) => request["errno"].is_null(),
                _ => false,
            }
    };
    let group = &k["group_request"];
    let fallback = &k["leader_fallback"];
    let state = k["state"].as_str();
    let cleanup_valid = match state {
        Some("not_requested") => {
            collection_stop == Some("leader_exit_and_eof") && group.is_null() && fallback.is_null()
        }
        Some("ownership_unconfirmed") => !wi.is_null() && group.is_null() && fallback.is_null(),
        Some("requested") => {
            let expected = group["rc"] == -1 && group["errno"] != 3;
            collection_stop != Some("leader_exit_and_eof")
                && wi.is_null()
                && signal_valid(group, -pid)
                && expected == !fallback.is_null()
                && (fallback.is_null() || signal_valid(fallback, pid))
        }
        _ => false,
    };
    if !cleanup_valid {
        return Some("exec cleanup contradicts native call roles");
    }
    let rc = i32_value(&wait["rc"]);
    let errno = &wait["errno"];
    let status = &wait["status"];
    if !matches!(rc, Some(-1 | 0)) && rc != Some(pid) {
        return Some("invalid exec wait return");
    }
    if !(if rc == Some(-1) {
        i32_value(errno).is_some_and(|n| n > 0)
    } else {
        errno.is_null()
    }) || !(if rc == Some(pid) {
        i32_value(status).is_some()
    } else {
        status.is_null()
    }) {
        return Some("exec wait errno or status lacks supporting return");
    }
    let (exit_code, signal) = match i32_value(status) {
        Some(status) => {
            let bits = status & 0x7f;
            (
                if bits == 0 { (status >> 8) & 0xff } else { -1 },
                if bits != 0 && bits != 127 { bits } else { 0 },
            )
        }
        None => (-1, 0),
    };
    if i32_value(&attempt["child_exit_code"]) != Some(exit_code)
        || i32_value(&attempt["child_term_signal"]) != Some(signal)
    {
        return Some("exec legacy leader status disagrees with confirmed wait");
    }
    let failed_group = group["rc"] == -1 && group["errno"] != 3;
    let reap_valid = match r["stop_reason"].as_str() {
        Some("reaped") => rc == Some(pid),
        Some("wait_error") => rc == Some(-1) && errno != 4,
        Some(
            stop @ ("ownership_unconfirmed" | "group_request_failed" | "clock_fault" | "deadline"),
        ) => {
            (rc == Some(0) || (rc == Some(-1) && errno == 4))
                && match stop {
                    "ownership_unconfirmed" => state == Some("ownership_unconfirmed"),
                    "group_request_failed" => {
                        state != Some("ownership_unconfirmed") && failed_group
                    }
                    _ => {
                        state != Some("ownership_unconfirmed")
                            && !failed_group
                            && ((stop == "clock_fault") == !r["clock_fault"].is_null())
                    }
                }
        }
        _ => false,
    };
    if !reap_valid {
        return Some("exec reap stop contradicts final wait or branch priority");
    }
    None
}

fn exec_observation_issues(runner: &Value) -> Vec<Value> {
    if runner["reporting_failure"].is_object() {
        return vec![];
    }
    runner["steps"]
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|step| {
            exec_observation_problem(&step["attempt"])
                .map(|detail| integrity_issue("exec_observation", detail.into()))
        })
        .collect()
}

fn phase_collection_issues(runner: &Value) -> Vec<Value> {
    if runner["reporting_failure"].is_object() {
        return vec![]; // Degraded replies preserve conflicting observations.
    }
    let phases = match runner.get("phases") {
        None | Some(Value::Null) => return vec![],
        Some(Value::Array(phases)) => phases,
        Some(_) => {
            return vec![integrity_issue(
                "phase_collection",
                "phases is not an array".into(),
            )];
        }
    };
    let mut issues = Vec::new();
    for phase in phases {
        let ordering = &phase["ordering"];
        let raw_disposition = &ordering["validator_disposition"];
        let spawn = &phase["validator_spawn_failure"];
        if !phase.is_object()
            || !(ordering.is_null() || ordering.is_object())
            || !(raw_disposition.is_null() || raw_disposition.is_string())
            || !(spawn.is_null() || spawn.is_object())
        {
            issues.push(integrity_issue(
                "phase_collection",
                "phase collection evidence has an invalid type".into(),
            ));
            continue;
        }
        let disposition = raw_disposition.as_str();
        let status = phase["collection_status"].as_str();
        let allowed = match status {
            Some("not_reached") => matches!(disposition, None | Some("not_invoked")),
            Some("not_needed") => disposition == Some("not_needed"),
            Some("collected") => {
                matches!(disposition, Some("not_spawned" | "reaped" | "unconfirmed"))
            }
            Some("budget_exhausted") => disposition == Some("not_spawned"),
            Some("clock_unavailable") => matches!(disposition, Some("not_needed" | "not_spawned")),
            _ => false,
        };
        let validator = &phase["validator_subprocess"];
        let observations = if status != Some("collected") {
            validator.is_null() && spawn.is_null()
        } else if disposition == Some("not_spawned") {
            validator.is_null() // Driver setup can fail before posix_spawn.
        } else {
            validator.is_object()
                && spawn.is_null()
                && validator["reaped"].as_bool() == Some(disposition == Some("reaped"))
        };
        if !allowed || !observations {
            issues.push(integrity_issue(
                "phase_collection",
                "phase collection status contradicts validator evidence".into(),
            ));
        }
        if validator.is_object() {
            if let Some(detail) = validator_ownership_problem(runner, phase, validator) {
                issues.push(integrity_issue("phase_collection", detail.into()));
            }
        }
    }
    issues
}

/// The issues a record list implies for an eligible query plan, mirroring the
/// host's join: (kind, step_id, count), sorted.
fn association_issues(
    records: &[Value],
    eligible: &[&Value],
) -> Vec<(String, Option<String>, usize)> {
    let mut groups: std::collections::BTreeMap<&str, Vec<&Value>> = Default::default();
    for record in records {
        if let Some(id) = record["step_id"].as_str() {
            groups.entry(id).or_default().push(record);
        }
    }
    let wanted: Vec<&str> = eligible
        .iter()
        .filter_map(|s| s["step_id"].as_str())
        .collect();
    let mut out = Vec::new();
    for step in eligible {
        let sid = step["step_id"].as_str().unwrap_or("");
        let matches = groups.get(sid).map(Vec::as_slice).unwrap_or(&[]);
        if matches.len() == 1 {
            let record = matches[0];
            let query = &step["sandbox_check"];
            let prediction = matches!(record["outcome"].as_str(), Some("allow" | "deny"));
            let kind = query["filter_kind"].as_str().unwrap_or("");
            let filter_type = kind.to_uppercase();
            let filter_value = if kind == "none" {
                Value::Null
            } else {
                query["filter_value"].clone()
            };
            let mismatch = ((prediction || !record["operation"].is_null())
                && record["operation"] != query["operation"])
                || ((prediction || !record["filter_type"].is_null())
                    && record["filter_type"] != filter_type)
                || ((prediction || !record["filter_value"].is_null())
                    && record["filter_value"] != filter_value);
            if mismatch {
                out.push(("query_mismatch".to_string(), Some(sid.to_string()), 1));
            }
        } else {
            let kind = if matches.is_empty() {
                "missing_id"
            } else {
                "duplicate_id"
            };
            out.push((kind.to_string(), Some(sid.to_string()), matches.len()));
        }
    }
    for (sid, group) in &groups {
        if !wanted.contains(sid) {
            out.push((
                "unexpected_id".to_string(),
                Some(sid.to_string()),
                group.len(),
            ));
        }
    }
    let unassociated = records.iter().filter(|r| r["step_id"].is_null()).count();
    if unassociated > 0 {
        out.push(("unassociated".to_string(), None, unassociated));
    }
    out.sort();
    out
}

/// A phase's validator collection must name this phase, carry exactly its
/// eligible query plan and the association issues its records imply. The plan
/// is read from the retained per-step query decisions; PID uniqueness is not a
/// rule. Shared with the Swift encoder and the Python reader.
fn validator_ownership_problem(
    runner: &Value,
    phase: &Value,
    block: &Value,
) -> Option<&'static str> {
    let (Some(owner), Some(ordinal)) = (block["phase_id"].as_str(), block["ordinal"].as_i64())
    else {
        return Some("validator collection lacks phase ownership");
    };
    if Some(owner) != phase["phase_id"].as_str() || Some(ordinal) != phase["ordinal"].as_i64() {
        return Some("validator collection names another phase");
    }
    // Order is the step-order and partition checks' question; ownership asks
    // whether the plan names exactly this phase's eligible queries.
    let empty = Vec::new();
    let eligible: Vec<&Value> = runner["steps"]
        .as_array()
        .unwrap_or(&empty)
        .iter()
        .filter(|s| {
            s["phase_id"] == phase["phase_id"]
                && s["sandbox_check"]["missing_reason"] != "query_not_requested"
        })
        .collect();
    let Some(expected) = block["expected_step_ids"].as_array() else {
        return Some("validator collection lacks its expected plan");
    };
    if eligible
        .iter()
        .any(|s| !s["step_id"].is_string() || !s["sandbox_check"].is_object())
        || expected.iter().any(|v| !v.is_string())
    {
        return Some("validator query plan has an invalid type");
    }
    let mut plan: Vec<String> = eligible
        .iter()
        .map(|s| {
            s["step_id"]
                .as_str()
                .expect("validated step ID")
                .to_string()
        })
        .collect();
    plan.sort();
    let mut named: Vec<String> = expected
        .iter()
        .map(|v| v.as_str().expect("validated plan ID").to_string())
        .collect();
    named.sort();
    let unique = named.windows(2).all(|w| w[0] != w[1]);
    if !unique || named != plan {
        return Some("validator expected IDs disagree with the phase's eligible query plan");
    }
    let (Some(records), Some(issues)) = (
        block["records"].as_array(),
        block["association_issues"].as_array(),
    ) else {
        return Some("validator collection lacks records or association issues");
    };
    if records
        .iter()
        .any(|r| !r.is_object() || (!r["step_id"].is_null() && !r["step_id"].is_string()))
        || issues.iter().any(|i| {
            !i.is_object()
                || !i["kind"].is_string()
                || (!i["step_id"].is_null() && !i["step_id"].is_string())
                || !i["count"].as_i64().is_some_and(|v| v >= 0)
        })
    {
        return Some("validator association evidence has an invalid type");
    }
    let mut reported: Vec<(String, Option<String>, usize)> = issues
        .iter()
        .map(|i| {
            (
                i["kind"]
                    .as_str()
                    .expect("validated issue kind")
                    .to_string(),
                i["step_id"].as_str().map(str::to_string),
                i["count"].as_u64().expect("validated association count") as usize,
            )
        })
        .collect();
    reported.sort();
    if reported != association_issues(records, &eligible) {
        return Some("validator association issues disagree with its records");
    }
    None
}

pub(crate) fn execution_diagnostics(runner: Option<&Value>) -> RunnerExecutionDiagnostics {
    if let Some(runner) = runner.filter(|r| r["execution_form"] == "actors") {
        return actor_execution_diagnostics(runner);
    }
    let pid = worker_pid(runner);
    let sub = runner.and_then(|r| r.get("runner_subprocess"));
    // Ordinary requests carry only probe pairs. Native authority actions are
    // interpreted exclusively by actor_execution_diagnostics.
    let reply_steps: Vec<Value> = runner
        .and_then(|r| r.get("steps"))
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    let mut projection = match (pid, sub) {
        (Some(_), Some(sub)) => project_disposition(
            sub,
            &reply_steps,
            runner.map_or(false, |r| {
                r["normalized_outcome"] == "runner_reporting_failed"
                    && r["reporting_failure"].is_object()
            }),
        ),
        _ => DispositionProjection {
            disposition: "no_worker",
            cause: None,
            stop_reason: None,
            integrity: None,
            issues: vec![],
        },
    };
    if let Some(runner) = runner {
        let mut native_issues = extension_account_issues(runner);
        native_issues.extend(phase_collection_issues(runner));
        native_issues.extend(exec_observation_issues(runner));
        if !native_issues.is_empty() {
            projection.disposition = "withheld";
            projection.cause = Some("unknown");
            projection.integrity = Some("invalid");
            projection.issues.extend(native_issues);
        }
    }
    RunnerExecutionDiagnostics {
        process_disposition: projection.disposition,
        termination_cause: projection.cause,
        stop_reason: projection.stop_reason,
        disposition_integrity: projection.integrity,
        disposition_issues: projection.issues,
        actors: None,
    }
}

/// The actor form: each actor's own subprocess record is projected against
/// that actor's steps and events; native, collection and exec issues of the
/// whole reply withhold the aggregate.
fn actor_execution_diagnostics(runner: &Value) -> RunnerExecutionDiagnostics {
    let reporting_failed = runner["normalized_outcome"] == "runner_reporting_failed"
        && runner["reporting_failure"].is_object();
    let action_ids: Vec<&Value> = runner["phases"]
        .as_array()
        .into_iter()
        .flatten()
        .flat_map(|p| p["action_ids"].as_array().into_iter().flatten())
        .collect();
    let empty = Vec::new();
    let mut actors = Vec::new();
    let mut all_valid = true;
    for actor in runner["actors"].as_array().unwrap_or(&empty) {
        let actor_id = actor["actor_id"].as_str().map(str::to_string);
        let Some(sub) = actor.get("subprocess").filter(|s| s.is_object()) else {
            actors.push(ActorExecutionDiagnostics {
                actor_id,
                process_disposition: "no_worker",
                termination_cause: None,
                stop_reason: None,
                disposition_integrity: None,
                disposition_issues: vec![],
            });
            continue;
        };
        let mut reply_steps: Vec<Value> = runner["steps"]
            .as_array()
            .unwrap_or(&empty)
            .iter()
            .chain(
                runner["extension_events"]
                    .as_array()
                    .unwrap_or(&empty)
                    .iter(),
            )
            .filter(|s| s["actor_id"] == actor["actor_id"])
            .cloned()
            .collect();
        reply_steps.sort_by_key(|a| {
            action_ids
                .iter()
                .position(|id| **id == a["step_id"])
                .unwrap_or(usize::MAX)
        });
        let projection = project_disposition(sub, &reply_steps, reporting_failed);
        if projection.integrity != Some("valid") {
            all_valid = false;
        }
        actors.push(ActorExecutionDiagnostics {
            actor_id,
            process_disposition: projection.disposition,
            termination_cause: projection.cause,
            stop_reason: projection.stop_reason,
            disposition_integrity: projection.integrity,
            disposition_issues: projection.issues,
        });
    }
    let mut native_issues = extension_account_issues(runner);
    native_issues.extend(phase_collection_issues(runner));
    native_issues.extend(exec_observation_issues(runner));
    let launched = actors.iter().any(|a| a.process_disposition != "no_worker");
    let withheld = !native_issues.is_empty();
    RunnerExecutionDiagnostics {
        process_disposition: if withheld {
            "withheld"
        } else if launched {
            "per_actor"
        } else {
            "no_worker"
        },
        termination_cause: if withheld { Some("unknown") } else { None },
        stop_reason: None,
        disposition_integrity: if !launched && !withheld {
            None
        } else if withheld || !all_valid {
            Some("invalid")
        } else {
            Some("valid")
        },
        disposition_issues: native_issues,
        actors: Some(actors),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::reply_fixtures::*;

    fn diagnostics(runner: &Value) -> RunnerExecutionDiagnostics {
        execution_diagnostics(Some(runner))
    }

    #[test]
    fn exec_observations_preserve_independent_facts_and_refuse_malformed_combinations() {
        let cases: Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/contract/exec_observation.json"
        ))
        .unwrap();
        for section in ["valid", "invalid"] {
            for case in cases[section].as_array().unwrap() {
                let attempt = &case["attempt"];
                let issue = exec_observation_problem(attempt);
                assert_eq!(
                    issue.is_none(),
                    section == "valid",
                    "{}: {:?}",
                    case["name"],
                    issue
                );
                let mut runner = worker("finished", None);
                runner["steps"] = json!([{ "step_id": "exec", "attempt": attempt.clone() }]);
                let issues = exec_observation_issues(&runner);
                assert_eq!(issues.is_empty(), section == "valid", "{}", case["name"]);
                if section == "invalid" {
                    let diagnostics = execution_diagnostics(Some(&runner));
                    assert_eq!(diagnostics.disposition_integrity, Some("invalid"));
                    assert_eq!(diagnostics.process_disposition, "withheld");
                }
                // A degraded reply retains contradictory facts under its existing
                // rules; the new object cannot recover comparison claims.
                runner["reporting_failure"] = json!({"origin":"runner_host"});
                assert!(exec_observation_issues(&runner).is_empty());
            }
        }
    }

    #[test]
    fn phase_collection_states_gate_disposition_without_requiring_success() {
        let cases: Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/contract/phase_collection.json"
        ))
        .unwrap();
        for case in cases.as_array().unwrap() {
            let mut runner = worker("finished", None);
            let phase = &mut runner["phases"][0];
            phase["collection_status"] = case["status"].clone();
            phase["ordering"]["validator_disposition"] = case["disposition"].clone();
            phase["validator_subprocess"] = if case["reaped"].is_null() {
                Value::Null
            } else {
                let mut block = phase["validator_subprocess"].clone();
                block["reaped"] = case["reaped"].clone();
                block["exit_code"] = Value::Null;
                block
            };
            phase["validator_spawn_failure"] = if case["spawn_failure"] == true {
                json!({"origin": "runner_host", "operation": "posix_spawn",
                    "executable_path": "/controlled/validator", "return_code": 2,
                    "diagnostic": "controlled spawn failure"})
            } else {
                Value::Null
            };
            let diag = diagnostics(&runner);
            if case["accepted"] == true {
                assert_eq!(
                    diag.disposition_integrity,
                    Some("valid"),
                    "{}",
                    case["name"]
                );
            } else {
                assert_eq!(
                    diag.disposition_integrity,
                    Some("invalid"),
                    "{}",
                    case["name"]
                );
                assert_eq!(diag.process_disposition, "withheld", "{}", case["name"]);
                assert!(
                    diag.disposition_issues
                        .iter()
                        .any(|i| i["kind"] == "phase_collection")
                );
            }
        }
    }

    #[test]
    fn phase_collection_types_distinguish_malformed_from_optional_absence() {
        let mut baseline = worker("finished", None);
        baseline["phases"][0]["collection_status"] = json!("not_reached");
        baseline["phases"][0]["ordering"]["validator_disposition"] = json!("not_invoked");
        baseline["phases"][0]["validator_subprocess"] = Value::Null;
        baseline["phases"][0]["validator_spawn_failure"] = Value::Null;
        for (path, values) in [
            (
                "/phases",
                vec![json!(7), json!(true), json!("wrong"), json!({}), json!([7])],
            ),
            (
                "/phases/0/ordering",
                vec![json!(7), json!(true), json!("wrong"), json!([])],
            ),
            (
                "/phases/0/ordering/validator_disposition",
                vec![json!(7), json!(true), json!([]), json!({})],
            ),
            (
                "/phases/0/validator_spawn_failure",
                vec![json!(7), json!(true), json!([])],
            ),
        ] {
            for value in values {
                let mut runner = baseline.clone();
                *runner.pointer_mut(path).unwrap() = value.clone();
                let diag = diagnostics(&runner);
                assert_eq!(
                    diag.disposition_integrity,
                    Some("invalid"),
                    "{path}: {value}"
                );
                assert_eq!(diag.process_disposition, "withheld", "{path}: {value}");
                assert_eq!(diag.termination_cause, Some("unknown"));
                assert!(
                    diag.disposition_issues
                        .iter()
                        .any(|i| i["kind"] == "phase_collection")
                );
            }
        }
        // The claim reader tolerates optional absence. It is not the response
        // shape validator, and does not turn absent ordering into query_first.
        for path in [
            "/phases",
            "/phases/0/ordering",
            "/phases/0/ordering/validator_disposition",
        ] {
            for absent in [false, true] {
                let mut runner = baseline.clone();
                if absent {
                    let (parent, key) = path.rsplit_once('/').unwrap();
                    runner
                        .pointer_mut(parent)
                        .unwrap()
                        .as_object_mut()
                        .unwrap()
                        .remove(key);
                } else {
                    *runner.pointer_mut(path).unwrap() = Value::Null;
                }
                assert_eq!(
                    diagnostics(&runner).disposition_integrity,
                    Some("valid"),
                    "{path}: absent={absent}"
                );
            }
        }
        // An empty spawn object has no contradictory presence claim here.
        // The full Python consumer owns its required native-call fields.
        let phase = &mut baseline["phases"][0];
        phase["collection_status"] = json!("collected");
        phase["ordering"]["validator_disposition"] = json!("not_spawned");
        phase["validator_spawn_failure"] = json!({});
        assert_eq!(diagnostics(&baseline).disposition_integrity, Some("valid"));
    }

    #[test]
    fn validator_collection_ownership_rejects_transplants_and_ignores_pid_reuse() {
        let ordinary: Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/contract/ordinary_phase_reply.json"
        ))
        .unwrap();
        let baseline = &ordinary;
        assert_eq!(baseline["phases"].as_array().unwrap().len(), 3);
        assert_eq!(diagnostics(baseline).disposition_integrity, Some("valid"));
        let block =
            |runner: &Value, index: usize| runner["phases"][index]["validator_subprocess"].clone();
        let rejected = |runner: &Value, reason: &str| {
            let diag = diagnostics(runner);
            assert_eq!(diag.disposition_integrity, Some("invalid"), "{reason}");
            assert_eq!(diag.process_disposition, "withheld", "{reason}");
            assert!(
                diag.disposition_issues
                    .iter()
                    .any(|i| i["kind"] == "phase_collection"
                        && i["detail"].as_str().is_some_and(|d| d.contains(reason))),
                "{reason}: {:?}",
                diag.disposition_issues
            );
        };
        let mut whole = baseline.clone();
        whole["phases"][0]["validator_subprocess"] = block(baseline, 1);
        rejected(&whole, "names another phase");
        let mut identity = baseline.clone();
        identity["phases"][1]["validator_subprocess"]["phase_id"] =
            baseline["phases"][0]["phase_id"].clone();
        rejected(&identity, "names another phase");
        let mut ordinal = baseline.clone();
        ordinal["phases"][1]["validator_subprocess"]["ordinal"] = json!(1);
        rejected(&ordinal, "names another phase");
        let mut expected = baseline.clone();
        expected["phases"][1]["validator_subprocess"]["expected_step_ids"] =
            block(baseline, 0)["expected_step_ids"].clone();
        rejected(&expected, "eligible query plan");
        let mut records = baseline.clone();
        records["phases"][1]["validator_subprocess"]["records"] =
            block(baseline, 0)["records"].clone();
        rejected(&records, "association issues disagree");
        let mut missing = baseline.clone();
        missing["phases"][1]["validator_subprocess"]
            .as_object_mut()
            .unwrap()
            .remove("phase_id");
        rejected(&missing, "lacks phase ownership");
        let mut plan = baseline.clone();
        plan["phases"][1]["validator_subprocess"]
            .as_object_mut()
            .unwrap()
            .remove("expected_step_ids");
        rejected(&plan, "lacks its expected plan");
        let mut erased = baseline.clone();
        erased["phases"][1]["validator_subprocess"]["records"] = json!([]);
        rejected(&erased, "association issues disagree");
        // Sequential children may reuse a numeric PID; ownership never reads PIDs.
        let mut reused = baseline.clone();
        reused["phases"][1]["validator_subprocess"]["pid"] = block(baseline, 0)["pid"].clone();
        assert_eq!(diagnostics(&reused).disposition_integrity, Some("valid"));
    }

    #[test]
    fn shared_evidence_type_corpus() {
        let baseline: Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/contract/ordinary_phase_reply.json"
        ))
        .unwrap();
        let rows: Vec<Value> = serde_json::from_str(include_str!(
            "../../tests/fixtures/contract/evidence_types.json"
        ))
        .unwrap();
        for row in rows {
            let mut reply = baseline.clone();
            for patch in row["patches"].as_array().unwrap() {
                let (parent, key) = patch["path"].as_str().unwrap().rsplit_once('/').unwrap();
                let target = reply.pointer_mut(parent).unwrap();
                if let Some(array) = target.as_array_mut() {
                    array[key.parse::<usize>().unwrap()] = patch["value"].clone();
                } else {
                    target[key] = patch["value"].clone();
                }
            }
            let diag = diagnostics(&reply);
            assert_eq!(
                diag.disposition_integrity == Some("valid"),
                row["accepted"].as_bool().unwrap(),
                "{}: {:?}",
                row["name"],
                diag.disposition_issues
            );
            if row["accepted"] == false {
                assert_eq!(diag.process_disposition, "withheld");
            }
        }
    }

    #[test]
    fn unconfirmed_reap_does_not_manufacture_clean_disposition_from_status_storage() {
        let mut runner = worker("runner_failed", None);
        runner["runner_subprocess"]["reaped"] = json!(false);
        let diag = diagnostics(&runner);
        // The record claims an exit status its reap evidence does not support.
        assert_eq!(diag.process_disposition, "withheld");
        assert_eq!(diag.disposition_integrity, Some("invalid"));
        assert_eq!(diag.termination_cause, Some("unknown"));
    }

    #[test]
    fn conflicting_status_representation_is_not_silently_resolved() {
        let mut runner = worker("runner_failed", Some(9));
        // One final reap represented as both a clean exit and a signal.
        runner["runner_subprocess"]["exit_code"] = json!(0);
        let diag = diagnostics(&runner);
        assert!(
            !matches!(diag.process_disposition, "signaled" | "clean_exit"),
            "exit_code 0 beside term_signal 9 is an invalid status pair; \
             an unqualified disposition ({}) resolves it silently",
            diag.process_disposition
        );
        assert_eq!(diag.termination_cause, Some("unknown"));
    }

    #[test]
    fn conflicting_status_reports_the_status_rule() {
        // The host itself recorded the conflict under rule D1.
        let mut runner = worker("runner_failed", Some(9));
        runner["runner_subprocess"]["exit_code"] = json!(0);
        runner["runner_subprocess"]["disposition"]["questions"]["final_status"] =
            json!({"state": "conflicting", "issue": 0});
        runner["runner_subprocess"]["disposition"]["issues"] = json!([{
            "kind": "conflict", "rule": "D1", "question": "final_status",
            "observations": ["exit_code", "term_signal"],
            "detail": "one successful reap represented as both an exit status and a signal"}]);
        let diag = diagnostics(&runner);
        assert_eq!(diag.process_disposition, "conflicting");
        assert_eq!(diag.disposition_integrity, Some("valid"));
        assert_eq!(diag.termination_cause, Some("unknown"));
        let wire = serde_json::to_value(&diag).unwrap();
        let issues = wire["disposition_issues"].as_array().cloned().unwrap();
        assert!(
            issues.iter().any(|i| i["rule"] == json!("D1")),
            "issue must name the status rule D1"
        );
    }

    // The runner reply carries the record the contract names; the controller
    // projects the witnessed host cleanup instead of ignoring the object.
    fn disposition_reply(cause_trigger: &str, reaped: bool) -> Value {
        let mut runner = worker("runner_timeout", Some(9));
        let sub = &mut runner["runner_subprocess"];
        sub["reaped"] = json!(reaped);
        sub["poll_stop_reason"] = json!("sentinel_deadline");
        sub["exit_requested"] = json!(true);
        sub["termination_request"] = json!({"signal": 9, "rc": 0});
        sub["cleanup_trigger"] = json!(cause_trigger);
        sub["grace_end"] = json!("exhausted");
        sub["collection_basis"] = json!("after_confirmed_reap");
        sub["partial_steps"] = json!(false);
        sub["disposition"] = json!({
            "questions": {
                "final_status": {"state": "supported", "answer": "signal", "value": 9, "basis": ["reaped", "term_signal"]},
                "stop_reason": {"state": "supported", "answer": "sentinel_deadline", "basis": ["poll_stop_reason"]},
                "cleanup_trigger": {"state": "supported", "answer": cause_trigger, "basis": ["cleanup_trigger", "exit_requested"]},
                "grace_end": {"state": "supported", "answer": "exhausted", "basis": ["grace_end", "exit_requested"]},
                "kill_request_and_result": {"state": "supported", "answer": "requested",
                    "value": {"signal": 9, "rc": 0}, "basis": ["termination_request"]},
                "collection_basis": {"state": "supported", "answer": "after_confirmed_reap", "basis": ["collection_basis"]},
                "progress_association": {"state": "inapplicable", "reason": "no_progress_word"}
            },
            "steps": [], "issues": []
        });
        runner["steps"] = json!([]);
        runner
    }

    #[test]
    fn disposition_record_projects_witnessed_host_cleanup_cause() {
        let runner = disposition_reply("deadline_expiry", true);
        let diag = diagnostics(&runner);
        assert_eq!(
            diag.termination_cause,
            Some("host_sentinel_deadline"),
            "the controller ignores the carried disposition record and reports a generic cause"
        );
        assert_eq!(diag.process_disposition, "signaled");
        let wire = serde_json::to_value(&diag).unwrap();
        assert_eq!(wire["disposition_integrity"], json!("valid"));
        assert_eq!(wire["stop_reason"], json!("sentinel_deadline"));
    }

    #[test]
    fn record_contradicting_its_basis_is_withheld() {
        // A supported signal claim while the reply says the worker was never reaped.
        let runner = disposition_reply("deadline_expiry", false);
        let diag = diagnostics(&runner);
        assert_eq!(
            diag.process_disposition, "withheld",
            "an assembled claim that contradicts its basis must be withheld, not re-derived"
        );
        assert_eq!(diag.termination_cause, Some("unknown"));
        let wire = serde_json::to_value(&diag).unwrap();
        assert_eq!(wire["disposition_integrity"], json!("invalid"));
        assert!(
            wire["disposition_issues"]
                .as_array()
                .map_or(false, |v| !v.is_empty())
        );
    }

    #[test]
    fn unrecognized_future_trigger_never_projects_a_cause() {
        let runner = disposition_reply("host_future_trigger", true);
        let diag = diagnostics(&runner);
        assert_eq!(diag.termination_cause, Some("unknown"));
        assert_ne!(diag.process_disposition, "clean_exit");
    }

    #[test]
    fn reply_without_a_disposition_record_is_withheld() {
        for record in [Value::Null, json!(null)] {
            let mut runner = disposition_reply("deadline_expiry", true);
            runner["runner_subprocess"]["disposition"] = record;
            let diag = diagnostics(&runner);
            assert_eq!(diag.process_disposition, "withheld");
            assert_eq!(diag.disposition_integrity, Some("invalid"));
            assert_eq!(diag.termination_cause, Some("unknown"));
            assert_eq!(diag.stop_reason, None);
            assert_eq!(diag.disposition_issues[0]["kind"], "missing_record");
        }
        let mut runner = disposition_reply("deadline_expiry", true);
        runner["runner_subprocess"]
            .as_object_mut()
            .unwrap()
            .remove("disposition");
        let diag = diagnostics(&runner);
        assert_eq!(diag.process_disposition, "withheld");
    }

    #[test]
    fn disposition_cannot_hide_a_second_status_representation() {
        let mut runner = disposition_reply("deadline_expiry", true);
        runner["runner_subprocess"]["exit_code"] = json!(0);
        let diag = diagnostics(&runner);
        assert_eq!(diag.process_disposition, "withheld");
        assert_eq!(diag.termination_cause, Some("unknown"));
    }

    #[test]
    fn disposition_request_value_must_match_the_observed_request() {
        for (field, value) in [
            ("rc", json!(-1)),
            ("signal", json!(15)),
            ("errno", json!(1)),
        ] {
            let mut runner = disposition_reply("deadline_expiry", true);
            runner["runner_subprocess"]["termination_request"][field] = value;
            let diag = diagnostics(&runner);
            assert_eq!(diag.process_disposition, "withheld", "mismatched {field}");
            assert_eq!(diag.termination_cause, Some("unknown"));
        }
    }

    #[test]
    fn disposition_requires_typed_sufficient_resolving_basis() {
        for basis in [
            json!([17]),
            json!([null]),
            json!([{}]),
            json!(["wait_errors"]),
            json!(["exit_requested"]),
            json!(["term_signal"]),
        ] {
            let mut runner = disposition_reply("deadline_expiry", true);
            runner["runner_subprocess"]["disposition"]["questions"]["final_status"]["basis"] =
                basis.clone();
            let diag = diagnostics(&runner);
            assert_eq!(diag.process_disposition, "withheld", "basis {basis}");
        }
    }

    #[test]
    fn unknown_stop_is_preserved_without_becoming_a_known_projection() {
        let mut runner = disposition_reply("deadline_expiry", true);
        runner["runner_subprocess"]["poll_stop_reason"] = json!("future_stop");
        runner["runner_subprocess"]["disposition"]["questions"]["stop_reason"]["answer"] =
            json!("future_stop");
        let diag = diagnostics(&runner);
        assert_eq!(diag.stop_reason, None);
        assert_eq!(diag.process_disposition, "signaled");
        assert_eq!(
            runner["runner_subprocess"]["poll_stop_reason"],
            json!("future_stop")
        );
    }

    #[test]
    fn indexed_activation_wait_precedes_its_first_slot_without_discarding_the_prefix() {
        let word = |stage: u64, index: u64| {
            json!({"worker_evidence": {"progress": {"operation": 13, "stage": stage,
                "index": index, "raw": (13u64 << 24) | (stage << 20) | (index + 1)}}})
        };
        for stage in [1, 2] {
            for first in [0, 1, 2] {
                let sub = word(stage, first);
                let (answer, value, position) = disposition_progress(&sub, 2);
                assert_eq!((answer, value), (Some("none"), None));
                let position = position.unwrap();
                assert_eq!(position, (attempt_position(), first, 0));
                if first > 0 {
                    assert!(position > (attempt_position(), first - 1, 2));
                }
                assert!(position < (attempt_position(), first, 1));
            }
        }
        assert_eq!(
            disposition_progress(&word(2, 0), 0),
            (Some("none"), None, Some((attempt_position(), 0, 0)))
        );
        assert_eq!(
            disposition_progress(&word(1, 3), 2),
            (Some("invalid"), None, None)
        );
        let mut mismatch = word(1, 0);
        mismatch["worker_evidence"]["progress"]["raw"] = json!((13u64 << 24) | (1 << 20) | 2);
        assert_eq!(
            disposition_progress(&mismatch, 2),
            (Some("invalid"), None, None)
        );
    }

    #[test]
    fn clock_setup_progress_is_a_known_position_before_the_policy_read() {
        let word = |op: u64, stage: u64| {
            json!({"worker_evidence": {"progress":
                {"operation": op, "stage": stage, "raw": (op << 24) | (stage << 20)}}})
        };
        let (header, setup, read, open) = (word(1, 2), word(12, 2), word(2, 1), word(14, 1));
        let (header_answer, _, header) = disposition_progress(&header, 1);
        let (setup_answer, setup_index, setup) = disposition_progress(&setup, 1);
        let (_, _, read) = disposition_progress(&read, 1);
        assert_eq!(
            (header_answer, setup_answer, setup_index),
            (Some("none"), Some("none"), None)
        );
        assert!(header.unwrap() < setup.unwrap() && setup.unwrap() < read.unwrap());
        // The parked activation wait (13) follows application and precedes the
        // release wait; an open code acquires no temporal meaning from its magnitude.
        let (apply_word, activate_word, proceed_word) = (word(8, 2), word(13, 1), word(11, 1));
        let (_, _, apply) = disposition_progress(&apply_word, 1);
        let (activate_answer, _, activate) = disposition_progress(&activate_word, 1);
        let (_, _, proceed) = disposition_progress(&proceed_word, 1);
        assert_eq!(activate_answer, Some("none"));
        assert!(apply.unwrap() < activate.unwrap() && activate.unwrap() < proceed.unwrap());
        assert_eq!(disposition_progress(&open, 1), (None, None, None));
    }

    #[test]
    fn disposition_checks_step_proofs_issues_and_projection_copies() {
        let envelope: Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/disposition/current/constructed_deadline.json"
        ))
        .unwrap();
        let base = &envelope["data"]["runner_result"];
        let diag = diagnostics(base);
        assert_eq!(
            diag.disposition_integrity,
            Some("valid"),
            "{:?}",
            diag.disposition_issues
        );
        // The degraded-reply contract intentionally withholds comparisons while
        // retaining independently usable lifecycle observations.
        let mut degraded = base.clone();
        degraded["normalized_outcome"] = json!("runner_reporting_failed");
        degraded["reporting_failure"] = json!({"origin":"runner_host", "evidence_retained":true});
        for step in degraded["steps"].as_array_mut().unwrap() {
            step["comparison"] = Value::Null;
        }
        let diag = diagnostics(&degraded);
        assert_eq!(diag.disposition_integrity, Some("valid"));
        assert_eq!(diag.termination_cause, Some("host_sentinel_deadline"));
        let mutations = [
            (
                "/runner_subprocess/disposition/questions/progress_association/value",
                json!(1),
            ),
            ("/runner_subprocess/partial_steps", json!(false)),
            (
                "/steps/0/attempt/lifecycle/boundary/answer",
                json!("not_reached"),
            ),
            ("/steps/0/attempt/lifecycle/summary", json!("not_reached")),
            ("/steps/0/attempt/result_source", json!("worker")),
            ("/steps/0/comparison/limitations", json!([])),
            (
                "/runner_subprocess/disposition/steps/0/questions/step_boundary_reached/answer",
                json!("not_reached"),
            ),
            (
                "/runner_subprocess/disposition/steps/1/questions/step_boundary_reached/answer",
                json!("reached"),
            ),
        ];
        for (path, value) in mutations {
            let mut runner = base.clone();
            *runner.pointer_mut(path).expect(path) = value;
            let diag = diagnostics(&runner);
            assert_eq!(diag.disposition_integrity, Some("invalid"), "{path}");
        }
        let mut runner = base.clone();
        let issue = json!({"kind":"conflict", "rule":"D5", "question":"step_boundary_reached", "step_index":0,
            "observations":["progress","slot","collection_basis"], "detail":"fabricated conflict"});
        runner["runner_subprocess"]["disposition"]["issues"] = json!([issue]);
        let fake = json!({"state":"conflicting", "issue":0});
        runner["runner_subprocess"]["disposition"]["steps"][0]["questions"]["step_boundary_reached"] =
            fake.clone();
        runner["steps"][0]["attempt"]["lifecycle"]["boundary"] = fake;
        runner["steps"][0]["attempt"]["lifecycle"]["summary"] = json!("conflicting");
        runner["steps"][0]["comparison"]["limitations"] = json!(["attempt:lifecycle_conflicting"]);
        let diag = diagnostics(&runner);
        assert_eq!(diag.disposition_integrity, Some("invalid"));
    }

    #[test]
    fn malformed_disposition_questions_are_withheld_without_panicking() {
        for name in DISPOSITION_RUN_QUESTIONS {
            let mut runner = disposition_reply("deadline_expiry", true);
            runner["runner_subprocess"]["disposition"]["questions"]
                .as_object_mut()
                .unwrap()
                .remove(*name);
            let diag = diagnostics(&runner);
            assert_eq!(diag.process_disposition, "withheld", "missing {name}");
        }
        for state in [json!("future_state"), json!(17), Value::Null] {
            let mut runner = disposition_reply("deadline_expiry", true);
            runner["runner_subprocess"]["disposition"]["questions"]["stop_reason"]["state"] = state;
            let diag = diagnostics(&runner);
            assert_eq!(diag.process_disposition, "withheld");
        }
    }
}
