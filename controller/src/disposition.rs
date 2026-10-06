//! Worker disposition record validation and projection: the execution half of
//! `data.runner_sandbox_diagnostics`. Log correlation is a separate observation
//! and stays with the envelope assembly in run_flow.rs.

use serde::Serialize;
use serde_json::{Value, json};

use crate::sandbox_log::worker_pid;

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
        // recorded the cleanup phase, so the token resolves beside exit_requested.
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

fn disposition_progress(
    sub: &Value,
    count: usize,
) -> (Option<&str>, Option<i64>, Option<DispositionPosition>) {
    let progress = &sub["worker_evidence"]["progress"];
    let op = progress["operation"].as_u64();
    let phase = progress["phase"].as_u64();
    let order = [1, 2, 3, 4, 5, 6, 7, 8, 11, 9, 10]
        .iter()
        .position(|v| Some(*v) == op);
    let (Some(op), Some(phase @ (1 | 2)), Some(order)) = (op, phase, order) else {
        return (None, None, None);
    };
    let index = progress["index"].as_u64();
    let indexed = op == 9 || op == 4;
    if (indexed && index.is_none())
        || (!indexed && !progress["index"].is_null())
        || index.map_or(false, |i| i >= 0xfffff || (op == 9 && i >= count as u64))
        || progress["raw"].as_u64() != Some((op << 24) | (phase << 20) | index.map_or(0, |i| i + 1))
    {
        return (Some("invalid"), None, None);
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
        Some((order, index.unwrap_or(0), phase)),
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
        let reached = position.map_or(false, |p| p >= (9, i as u64, 1));
        let returned = position.map_or(false, |p| p >= (9, i as u64, 2));
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
            if attempt["result_source"] != if completed { "worker" } else { "synthetic" }
                || attempt["missing_reason"].as_str() != reason
            {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i}: compatibility projections disagree with record"),
                ));
            }
            let lifecycle = &attempt["lifecycle"];
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
            if !(reporting_failed && reply["comparison"].is_null())
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

pub(crate) fn execution_diagnostics(runner: Option<&Value>) -> RunnerExecutionDiagnostics {
    let pid = worker_pid(runner);
    let sub = runner.and_then(|r| r.get("runner_subprocess"));
    let reply_steps: Vec<Value> = runner
        .and_then(|r| r.get("steps"))
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    let projection = match (pid, sub) {
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
    RunnerExecutionDiagnostics {
        process_disposition: projection.disposition,
        termination_cause: projection.cause,
        stop_reason: projection.stop_reason,
        disposition_integrity: projection.integrity,
        disposition_issues: projection.issues,
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
    fn disposition_checks_step_proofs_issues_and_projection_copies() {
        let envelope: Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/disposition/response14/a1_expected.json"
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
