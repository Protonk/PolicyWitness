//! Typed evidence admission for the porcelain experiment. Raw records remain
//! publishable when a claim fails; diagnostics never replace their native facts.
use crate::porcelain_records::*;
#[path = "porcelain_actor.rs"]
mod actor;
#[path = "porcelain_native.rs"]
mod native;
use serde::Serialize;
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug, Serialize, PartialEq)]
pub(crate) struct IntegrityIssue {
    pub kind: String,
    pub detail: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub rule: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub question: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub step_index: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub observations: Option<Vec<String>>,
}
fn issue(out: &mut Vec<IntegrityIssue>, kind: &str, detail: impl Into<String>) {
    out.push(IntegrityIssue {
        kind: kind.into(),
        detail: detail.into(),
        rule: None,
        question: None,
        step_index: None,
        observations: None,
    });
}
#[derive(Clone, Debug, Serialize)]
pub(crate) struct RunnerExecutionDiagnostics {
    pub process_disposition: &'static str,
    pub termination_cause: Option<&'static str>,
    pub stop_reason: Option<String>,
    pub disposition_integrity: Option<&'static str>,
    pub disposition_issues: Vec<IntegrityIssue>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub actors: Option<Vec<ActorExecutionDiagnostics>>,
}
#[derive(Clone, Debug, Serialize)]
pub(crate) struct ActorExecutionDiagnostics {
    pub actor_id: Option<String>,
    pub process_disposition: &'static str,
    pub termination_cause: Option<&'static str>,
    pub stop_reason: Option<String>,
    pub disposition_integrity: Option<&'static str>,
    pub disposition_issues: Vec<IntegrityIssue>,
}

/// Question selection is a fixed field operation, never a dynamic record lookup.
#[derive(Clone, Copy, Debug, PartialEq)]
enum Question {
    FinalStatus,
    StopReason,
    CleanupTrigger,
    GraceEnd,
    Kill,
    Collection,
    Progress,
    Boundary,
    Published,
    Applicability,
}
impl Question {
    fn name(self) -> &'static str {
        match self {
            Self::FinalStatus => "final_status",
            Self::StopReason => "stop_reason",
            Self::CleanupTrigger => "cleanup_trigger",
            Self::GraceEnd => "grace_end",
            Self::Kill => "kill_request_and_result",
            Self::Collection => "collection_basis",
            Self::Progress => "progress_association",
            Self::Boundary => "step_boundary_reached",
            Self::Published => "step_result_published",
            Self::Applicability => "step_requested_operation_applicability",
        }
    }
    fn run(self, q: &PWDispositionRunQuestions) -> Option<&PWDispositionClaim> {
        match self {
            Self::FinalStatus => q.final_status.as_ref(),
            Self::StopReason => q.stop_reason.as_ref(),
            Self::CleanupTrigger => q.cleanup_trigger.as_ref(),
            Self::GraceEnd => q.grace_end.as_ref(),
            Self::Kill => q.kill_request_and_result.as_ref(),
            Self::Collection => q.collection_basis.as_ref(),
            Self::Progress => q.progress_association.as_ref(),
            _ => None,
        }
    }
    fn step(self, q: &PWDispositionStepQuestions) -> Option<&PWDispositionClaim> {
        match self {
            Self::Boundary => q.step_boundary_reached.as_ref(),
            Self::Published => q.step_result_published.as_ref(),
            Self::Applicability => q.step_requested_operation_applicability.as_ref(),
            _ => None,
        }
    }
}
const RUN_QUESTIONS: [Question; 7] = [
    Question::FinalStatus,
    Question::StopReason,
    Question::CleanupTrigger,
    Question::GraceEnd,
    Question::Kill,
    Question::Collection,
    Question::Progress,
];
const STEP_QUESTIONS: [Question; 3] = [
    Question::Boundary,
    Question::Published,
    Question::Applicability,
];
fn supported(c: Option<&PWDispositionClaim>) -> bool {
    c.is_some_and(|c| c.state == "supported")
}
fn answer(c: Option<&PWDispositionClaim>) -> Option<&str> {
    c.and_then(|c| c.answer.as_deref())
}
fn integer(c: Option<&PWDispositionClaim>) -> Option<i64> {
    match c.and_then(|c| c.value.as_ref()) {
        Some(PWDispositionValue::Integer(n)) => Some(*n),
        _ => None,
    }
}
fn cites(c: &PWDispositionClaim, token: &str) -> bool {
    c.basis
        .as_ref()
        .is_some_and(|v| v.iter().any(|v| v == token))
}
fn reference_resolves(
    token: &str,
    s: &PWRunnerSubprocess,
    step: Option<&PWDispositionStep>,
) -> bool {
    match token {
        "reaped" => s.reaped.is_some(),
        "exit_code" => s.exit_code.is_some(),
        "term_signal" => s.term_signal.is_some(),
        "poll_stop_reason" => s.poll_stop_reason.is_some(),
        "exit_requested" => s.exit_requested.is_some(),
        "termination_request" => s.termination_request.is_some() || s.exit_requested.is_some(),
        "wait_errors" => s.wait_errors.is_some(),
        "cleanup_trigger" => s.cleanup_trigger.is_some(),
        "grace_end" => s.grace_end.is_some(),
        "collection_basis" => s.collection_basis.is_some(),
        "done_observed" => s.done_observed.is_some(),
        "plan" => true,
        "progress" => s
            .worker_evidence
            .as_ref()
            .is_some_and(|e| e.progress.is_some()),
        "worker_failure" => s
            .worker_evidence
            .as_ref()
            .is_some_and(|e| e.failure.is_some()),
        "slot" | "attempt_support" => step.is_some(),
        _ => false,
    }
}
fn sufficient(q: Question, c: &PWDispositionClaim) -> bool {
    let has = |v: &[&str]| v.iter().all(|v| cites(c, v));
    match (q, c.answer.as_deref()) {
        (Question::FinalStatus, Some("exit_code")) => has(&["reaped", "exit_code"]),
        (Question::FinalStatus, Some("signal")) => has(&["reaped", "term_signal"]),
        (Question::StopReason, _) => has(&["poll_stop_reason"]),
        (Question::CleanupTrigger, _) => has(&["cleanup_trigger", "exit_requested"]),
        (Question::GraceEnd, _) => has(&["grace_end", "exit_requested"]),
        (Question::Collection, _) => has(&["collection_basis"]),
        (Question::Kill, Some("requested")) => has(&["termination_request"]),
        (Question::Kill, Some("none")) => has(&["termination_request", "exit_requested"]),
        (Question::Progress, Some("step_index" | "invalid")) => has(&["progress", "plan"]),
        (Question::Progress, Some("none" | "parameter_index")) => has(&["progress"]),
        (Question::Applicability, _) => has(&["attempt_support"]),
        (Question::Boundary, Some("reached")) => {
            has(&["progress"]) || has(&["slot", "attempt_support"])
        }
        (Question::Boundary, Some("not_reached")) => has(&["progress", "slot", "collection_basis"]),
        (Question::Published, Some("published")) => has(&["slot", "attempt_support"]),
        (Question::Published, Some("unpublished")) => has(&["slot", "collection_basis"]),
        _ => true,
    }
}
fn check_claim(
    q: Question,
    c: Option<&PWDispositionClaim>,
    record: &PWDispositionRecord,
    sub: &PWRunnerSubprocess,
    step: Option<(usize, &PWDispositionStep)>,
    out: &mut Vec<IntegrityIssue>,
) {
    let label = match step {
        Some((i, _)) => format!("step {i} {}", q.name()),
        None => q.name().into(),
    };
    let Some(c) = c else {
        issue(out, "malformed_record", format!("{label}: missing claim"));
        return;
    };
    match c.state.as_str() {
        "supported" => {
            if c.answer.is_none()
                || !c.basis.as_ref().is_some_and(|b| !b.is_empty())
                || !sufficient(q, c)
            {
                issue(
                    out,
                    "invalid_claim",
                    format!("{label}: supported claim lacks answer or sufficient basis"),
                );
            }
            if c.basis
                .iter()
                .flatten()
                .any(|token| !reference_resolves(token, sub, step.map(|(_, s)| s)))
            {
                issue(
                    out,
                    "unresolved_reference",
                    format!("{label}: basis contains an unresolved reference"),
                );
            }
        }
        "conflicting" => {
            let expected = if q == Question::FinalStatus {
                &["exit_code", "term_signal"][..]
            } else {
                &["progress", "slot", "collection_basis"][..]
            };
            let valid = c
                .issue
                .and_then(|i| usize::try_from(i).ok())
                .and_then(|i| record.issues.get(i))
                .is_some_and(|i| {
                    i.kind == "conflict"
                        && i.question == q.name()
                        && i.step_index == step.map(|(i, _)| i as i64)
                        && i.rule
                            == if q == Question::FinalStatus {
                                "D1"
                            } else {
                                "D5"
                            }
                        && matches!(
                            q,
                            Question::FinalStatus | Question::Boundary | Question::Published
                        )
                        && expected
                            .iter()
                            .all(|v| i.observations.iter().any(|o| o == v))
                        && i.observations
                            .iter()
                            .all(|v| reference_resolves(v, sub, step.map(|(_, s)| s)))
                });
            if !valid {
                issue(
                    out,
                    "invalid_claim",
                    format!("{label}: conflict lacks matching observations/issue"),
                );
            }
        }
        "unresolved" | "inapplicable" => {
            if c.reason.is_none() {
                issue(out, "invalid_claim", format!("{label}: state lacks reason"));
            }
        }
        _ => issue(
            out,
            "invalid_claim",
            format!("{label}: unknown claim state"),
        ),
    }
}
const PROTOCOL_ORDER: [u32; 13] = [1, 12, 2, 3, 4, 5, 6, 7, 8, 13, 11, 9, 10];
type Position = (usize, u64, u32);
fn attempt_position() -> usize {
    PROTOCOL_ORDER
        .iter()
        .position(|operation| *operation == 9)
        .expect("attempt operation belongs to the protocol order")
}
fn progress(
    sub: &PWRunnerSubprocess,
    count: usize,
) -> (Option<&'static str>, Option<i64>, Option<Position>) {
    let Some(p) = sub
        .worker_evidence
        .as_ref()
        .and_then(|e| e.progress.as_ref())
    else {
        return (None, None, None);
    };
    let Some(order) = PROTOCOL_ORDER.iter().position(|o| *o == p.operation) else {
        return (None, None, None);
    };
    if !matches!(p.stage, 1 | 2) {
        return (None, None, None);
    }
    let phase = matches!(p.operation, 11 | 13) && p.index.is_some();
    let indexed = matches!(p.operation, 4 | 9) || phase;
    if indexed != p.index.is_some()
        || p.index.is_some_and(|i| {
            i >= 0xfffff
                || (p.operation == 9 && i as usize >= count)
                || (phase && i as usize > count)
        })
        || p.raw != ((p.operation << 24) | (p.stage << 20) | p.index.map_or(0, |i| i + 1))
    {
        return (Some("invalid"), None, None);
    }
    if phase {
        return (
            Some("none"),
            None,
            Some((attempt_position(), u64::from(p.index.unwrap()), 0)),
        );
    }
    (
        Some(if p.operation == 9 {
            "step_index"
        } else if p.operation == 4 {
            "parameter_index"
        } else {
            "none"
        }),
        p.index.map(i64::from),
        Some((order, u64::from(p.index.unwrap_or(0)), p.stage)),
    )
}
#[derive(Clone, Copy)]
enum ActionRef<'a> {
    Step(&'a PWRunnerStepResult),
    Event(&'a PWRunnerExtensionEvent),
}
impl<'a> ActionRef<'a> {
    fn id(self) -> &'a str {
        match self {
            Self::Step(s) => &s.step_id,
            Self::Event(e) => &e.step_id,
        }
    }
    fn lifecycle(self) -> Option<&'a PWAttemptLifecycle> {
        match self {
            Self::Step(s) => s.attempt.lifecycle.as_ref(),
            Self::Event(e) => e.lifecycle.as_ref(),
        }
    }
}
fn lifecycle_summary(s: &PWDispositionStep) -> &'static str {
    let b = s.questions.step_boundary_reached.as_ref();
    let r = s.questions.step_result_published.as_ref();
    if s.attempt_support == "unsupported" {
        "unsupported"
    } else if supported(r) && answer(r) == Some("published") {
        "completed"
    } else if b.is_some_and(|c| c.state == "conflicting")
        || r.is_some_and(|c| c.state == "conflicting")
    {
        "conflicting"
    } else if supported(r)
        && answer(r) == Some("unpublished")
        && supported(b)
        && answer(b) == Some("reached")
    {
        "started_without_result"
    } else if supported(r)
        && answer(r) == Some("unpublished")
        && supported(b)
        && answer(b) == Some("not_reached")
    {
        "not_reached"
    } else {
        "unresolved"
    }
}

fn validate_lifecycle(
    sub: &PWRunnerSubprocess,
    actions: &[ActionRef<'_>],
    reporting_failed: bool,
) -> Vec<IntegrityIssue> {
    let mut out = Vec::new();
    if actions.len() > 256 || lifecycle_geometry(sub).is_some() {
        issue(
            &mut out,
            "reply_capacity",
            "worker disposition exceeds native semantic capacity",
        );
        return out;
    }
    if sub.pid <= 0 || sub.pid > i64::from(i32::MAX) {
        issue(
            &mut out,
            "invalid_claim",
            "worker PID is outside native process identity range",
        );
    }
    let Some(record) = sub.disposition.as_ref() else {
        issue(
            &mut out,
            "missing_record",
            "worker subprocess requires disposition",
        );
        return out;
    };
    for q in RUN_QUESTIONS {
        check_claim(q, q.run(&record.questions), record, sub, None, &mut out);
    }
    let q = &record.questions;
    let reaped = sub.reaped == Some(true);
    if sub.collection_basis.as_deref() == Some("after_confirmed_reap") && !reaped {
        issue(
            &mut out,
            "invalid_claim",
            "terminal collection without confirmed reap",
        );
    }
    for question in [Question::CleanupTrigger, Question::GraceEnd, Question::Kill] {
        if supported(question.run(q)) && sub.exit_requested == Some(false) {
            issue(
                &mut out,
                "invalid_claim",
                "cleanup claim without exit request",
            );
        }
    }
    let final_status = q.final_status.as_ref();
    let contradiction = if supported(final_status) {
        match answer(final_status) {
            Some("signal") => {
                !reaped
                    || sub.term_signal.is_none()
                    || sub.exit_code.is_some()
                    || integer(final_status) != sub.term_signal
            }
            Some("exit_code") => {
                !reaped
                    || sub.exit_code.is_none()
                    || sub.term_signal.is_some()
                    || integer(final_status) != sub.exit_code
            }
            _ => false,
        }
    } else {
        final_status.is_some_and(|c| c.state == "conflicting")
            && (!reaped || sub.exit_code.is_none() || sub.term_signal.is_none())
    };
    if contradiction {
        issue(
            &mut out,
            "invalid_claim",
            "final_status contradicts reaped status",
        );
    }
    for (c, fact) in [
        (q.stop_reason.as_ref(), sub.poll_stop_reason.as_deref()),
        (q.cleanup_trigger.as_ref(), sub.cleanup_trigger.as_deref()),
        (q.grace_end.as_ref(), sub.grace_end.as_deref()),
        (q.collection_basis.as_ref(), sub.collection_basis.as_deref()),
    ] {
        if supported(c) && answer(c) != fact {
            issue(
                &mut out,
                "invalid_claim",
                "claim contradicts recorded host fact",
            );
        }
    }
    if let Some(c) = q
        .kill_request_and_result
        .as_ref()
        .filter(|c| c.state == "supported")
    {
        let valid = match c.answer.as_deref() {
            Some("requested") => match (&c.value, &sub.termination_request) {
                (Some(PWDispositionValue::Request(a)), Some(b)) => a == b,
                _ => false,
            },
            Some("none") => sub.termination_request.is_none(),
            _ => true,
        };
        if !valid {
            issue(
                &mut out,
                "invalid_claim",
                "kill claim contradicts termination request",
            );
        }
    }
    let (association, index, position) = progress(sub, record.steps.len());
    if supported(q.progress_association.as_ref())
        && matches!(
            answer(q.progress_association.as_ref()),
            Some("none" | "invalid" | "step_index" | "parameter_index")
        )
        && (answer(q.progress_association.as_ref()) != association
            || q.progress_association
                .as_ref()
                .and_then(|c| c.value.as_ref())
                != index.map(PWDispositionValue::Integer).as_ref())
    {
        issue(
            &mut out,
            "invalid_claim",
            "progress claim contradicts encoded progress",
        );
    }
    if record.steps.len() != actions.len() {
        issue(
            &mut out,
            "invalid_claim",
            "disposition/action count mismatch",
        );
    }
    if sub.partial_steps != record.steps.iter().any(|s| s.slot != "completed") {
        issue(
            &mut out,
            "invalid_claim",
            "partial_steps contradicts record slots",
        );
    }
    let terminal = reaped && sub.collection_basis.as_deref() == Some("after_confirmed_reap");
    for (i, s) in record.steps.iter().enumerate() {
        for question in STEP_QUESTIONS {
            check_claim(
                question,
                question.step(&s.questions),
                record,
                sub,
                Some((i, s)),
                &mut out,
            );
        }
        if s.index != i as i64
            || !matches!(s.slot.as_str(), "completed" | "incomplete" | "absent")
            || !matches!(s.attempt_support.as_str(), "supported" | "unsupported")
        {
            issue(
                &mut out,
                "malformed_record",
                format!("step {i}: identity/slot/support invalid"),
            );
        }
        let Some(action) = actions.get(i).copied() else {
            continue;
        };
        if s.step_id != action.id() {
            issue(
                &mut out,
                "invalid_claim",
                format!("step {i}: action identity mismatch"),
            );
        }
        let completed = s.slot == "completed" && s.attempt_support == "supported";
        let reached = position.is_some_and(|p| p >= (attempt_position(), i as u64, 1));
        let returned = position.is_some_and(|p| p >= (attempt_position(), i as u64, 2));
        let boundary_conflict = terminal && position.is_some() && !reached && s.slot == "completed";
        let result_conflict =
            terminal && returned && s.slot == "incomplete" && s.attempt_support == "supported";
        let b = s.questions.step_boundary_reached.as_ref();
        let r = s.questions.step_result_published.as_ref();
        let a = s.questions.step_requested_operation_applicability.as_ref();
        if supported(a)
            && matches!(answer(a), Some("supported" | "unsupported"))
            && answer(a) != Some(s.attempt_support.as_str())
        {
            issue(
                &mut out,
                "invalid_claim",
                "applicability contradicts support",
            );
        }
        if supported(r)
            && ((answer(r) == Some("published") && !completed)
                || (answer(r) == Some("unpublished")
                    && (s.slot != "incomplete"
                        || !terminal
                        || s.attempt_support != "supported"
                        || result_conflict)))
        {
            issue(
                &mut out,
                "invalid_claim",
                "result publication contradicts slot/collection",
            );
        }
        if let Some(b) = b {
            let witness = (reached && cites(b, "progress"))
                || (completed && cites(b, "slot") && cites(b, "attempt_support"));
            if b.state == "supported"
                && ((b.answer.as_deref() == Some("reached") && (boundary_conflict || !witness))
                    || (b.answer.as_deref() == Some("not_reached")
                        && (!terminal || s.slot == "completed" || position.is_none() || reached)))
            {
                issue(
                    &mut out,
                    "invalid_claim",
                    "boundary lacks unopposed witness",
                );
            }
            if b.state == "conflicting" && !boundary_conflict {
                issue(
                    &mut out,
                    "invalid_claim",
                    "boundary conflict lacks incompatible observations",
                );
            }
        }
        if r.is_some_and(|r| r.state == "conflicting") && !result_conflict {
            issue(
                &mut out,
                "invalid_claim",
                "result conflict lacks incompatible observations",
            );
        }
        let reason = if completed {
            None
        } else if s.attempt_support != "supported" {
            Some("attempt_not_supported")
        } else if s.slot == "absent" {
            Some("slot_absent")
        } else {
            Some("slot_incomplete")
        };
        match action {
            ActionRef::Step(step) => {
                if step.attempt.result_source.as_deref()
                    != Some(if completed { "worker" } else { "synthetic" })
                    || step.attempt.missing_reason.as_deref() != reason
                {
                    issue(
                        &mut out,
                        "invalid_claim",
                        "attempt compatibility projection contradicts lifecycle",
                    );
                }
                let expected = match lifecycle_summary(s) {
                    "completed" => None,
                    "unresolved" => Some("attempt:lifecycle_unresolved"),
                    "conflicting" => Some("attempt:lifecycle_conflicting"),
                    "unsupported" => Some("attempt:unsupported"),
                    "not_reached" => Some("attempt:not_reached"),
                    _ => Some("attempt:started_without_result"),
                };
                let mut actual = step
                    .comparison
                    .iter()
                    .flat_map(|c| &c.limitations)
                    .map(String::as_str)
                    .filter(|l| l.starts_with("attempt:"));
                if !(reporting_failed && step.comparison.is_none()) && !actual.by_ref().eq(expected)
                {
                    issue(
                        &mut out,
                        "invalid_claim",
                        "comparison lifecycle limitations disagree",
                    );
                }
            }
            ActionRef::Event(e) => {
                if e.result_published != completed {
                    issue(
                        &mut out,
                        "invalid_claim",
                        "event publication contradicts lifecycle",
                    );
                }
                let valid = if e.operation == "transfer" {
                    !e.call_boundary_observed
                        && e.native_result.is_none()
                        && e.errno.is_none()
                        && e.unavailable_reason.is_none()
                } else {
                    match e.status.as_str() {
                        "returned" => {
                            completed
                                && e.call_boundary_observed
                                && e.native_result.is_some()
                                && e.errno.is_some()
                                && e.unavailable_reason.is_none()
                        }
                        "unavailable" => {
                            completed
                                && !e.call_boundary_observed
                                && e.native_result.is_none()
                                && e.errno.is_none()
                                && e.unavailable_reason.is_some()
                        }
                        "unresolved" => {
                            !completed
                                && e.native_result.is_none()
                                && e.errno.is_none()
                                && e.unavailable_reason.is_none()
                        }
                        _ => false,
                    }
                };
                if !valid {
                    issue(
                        &mut out,
                        "invalid_claim",
                        "event native publication is inconsistent",
                    );
                }
            }
        }
        if let Some(l) = action.lifecycle() {
            if Some(&l.boundary) != b
                || Some(&l.result) != r
                || (matches!(
                    l.summary.as_str(),
                    "completed"
                        | "started_without_result"
                        | "not_reached"
                        | "unsupported"
                        | "unresolved"
                        | "conflicting"
                ) && l.summary != lifecycle_summary(s))
            {
                issue(
                    &mut out,
                    "invalid_claim",
                    "lifecycle projection disagrees with canonical record",
                );
            }
        } else {
            issue(
                &mut out,
                "invalid_claim",
                "action lacks lifecycle projection",
            );
        }
    }
    for (i, _) in record.issues.iter().enumerate() {
        let used = RUN_QUESTIONS
            .iter()
            .filter_map(|q| q.run(&record.questions))
            .chain(
                record
                    .steps
                    .iter()
                    .flat_map(|s| STEP_QUESTIONS.iter().filter_map(|q| q.step(&s.questions))),
            )
            .any(|c| c.state == "conflicting" && c.issue == Some(i as i64));
        if !used {
            issue(
                &mut out,
                "invalid_claim",
                format!("issue {i} is unreferenced"),
            );
        }
    }
    out
}

fn filter_type(kind: &str) -> &str {
    match kind {
        "none" => "NONE",
        "path" => "PATH",
        "global_name" => "GLOBAL_NAME",
        "local_name" => "LOCAL_NAME",
        "iokit_registry_entry_class" => "IOKIT_REGISTRY_ENTRY_CLASS",
        "iokit_user_client_class" => "IOKIT_USER_CLIENT_CLASS",
        "sysctl_name" => "SYSCTL_NAME",
        other => other,
    }
}
fn query_matches(record: &ValidatorVerdict, step: &PWRunnerStepResult) -> bool {
    let q = &step.sandbox_check;
    record.operation.as_deref() == Some(q.operation.as_str())
        && record.filter_type.as_deref() == Some(filter_type(&q.filter_kind))
        && record.filter_value.as_deref()
            == if q.filter_kind == "none" {
                None
            } else {
                q.filter_value.as_deref()
            }
}
fn phase_issues(reply: &PWRunnerRunResult, out: &mut Vec<IntegrityIssue>) {
    let actor_form = reply.execution_form.as_deref() == Some("actors");
    let launched = reply.runner_subprocess.is_some()
        || reply
            .actors
            .iter()
            .flatten()
            .any(|a| a.subprocess.is_some());
    if launched && reply.phases.is_empty() {
        issue(
            out,
            "phase_collection",
            "worker subprocess requires phase evidence",
        );
    }
    let mut phase_ids = BTreeSet::new();
    let mut action_ids = BTreeSet::new();
    let events = reply.extension_events.as_deref().unwrap_or(&[]);
    let phase_cap = if reply.execution_form.as_deref() == Some("actors") {
        16
    } else {
        8
    };
    if reply.phases.len() > phase_cap || reply.steps.len() + events.len() > 256 {
        issue(out, "phase_collection", "phase/action capacity exceeded");
    }
    let mut all = BTreeSet::new();
    for id in reply
        .steps
        .iter()
        .map(|s| &s.step_id)
        .chain(events.iter().map(|e| &e.step_id))
    {
        if !all.insert(id) {
            issue(out, "phase_collection", "duplicate action identity");
        }
    }
    for (i, p) in reply.phases.iter().enumerate() {
        if p.ordinal != i as i64 + 1
            || !phase_ids.insert(&p.phase_id)
            || p.action_ids.iter().any(|id| !action_ids.insert(id))
        {
            issue(
                out,
                "phase_collection",
                "phase ordinal/partition identity conflict",
            );
        }
        let worker = if actor_form {
            reply
                .actors
                .iter()
                .flatten()
                .find(|a| Some(a.actor_id.as_str()) == p.actor_id.as_deref())
                .and_then(|a| a.subprocess.as_ref())
        } else {
            reply.runner_subprocess.as_ref()
        };
        if worker.is_some() && p.ordering.is_none() {
            issue(
                out,
                "phase_collection",
                "phase ordering is required beside a worker subprocess",
            );
        }
        if let Some(spawn) = &p.validator_spawn_failure {
            if spawn.origin != "runner_host"
                || spawn.operation != "posix_spawn"
                || spawn.executable_path.is_empty()
                || spawn.return_code == 0
                || p.validator_subprocess.is_some()
            {
                issue(
                    out,
                    "phase_collection",
                    "invalid validator spawn failure record",
                );
            }
        }
        if let Some(o) = &p.ordering {
            if o.collection_closed_before_proceed && !p.arrival_observed {
                issue(out, "ordering", "collection closure lacks phase arrival");
            }
            if worker.is_some() {
                if o.collection_closed_before_proceed != (o.validator_disposition != "not_invoked")
                {
                    issue(
                        out,
                        "ordering",
                        "collection decision disagrees with validator disposition",
                    );
                }
                let established = if actor_form {
                    reply
                        .actors
                        .iter()
                        .flatten()
                        .find(|a| a.actor_id.as_str() == p.actor_id.as_deref().unwrap_or(""))
                        .is_some_and(|a| {
                            matches!(a.setup_status.as_str(), "applied" | "unapplied_declared")
                        })
                } else {
                    reply.sandboxed_after_apply == Some(true)
                };
                let after_proceed_failure = worker
                    .and_then(|s| s.worker_evidence.as_ref())
                    .and_then(|e| e.failure.as_ref())
                    .is_some_and(|f| {
                        f.operation == 11 && f.index.map(i64::from) == Some(p.ordinal - 1)
                    })
                    && (o.proceed_observed
                        || reply.steps.iter().any(|s| {
                            s.phase_id == p.phase_id
                                && s.attempt.result_source.as_deref() == Some("worker")
                        }));
                for (present, name) in [
                    (
                        o.proceed_set && !o.collection_closed_before_proceed,
                        "release_without_collection_closure",
                    ),
                    (
                        o.proceed_observed && !o.proceed_set,
                        "acknowledgement_without_release",
                    ),
                    (
                        (o.proceed_set || o.proceed_observed) && !established,
                        "release_without_successful_application",
                    ),
                    (
                        after_proceed_failure,
                        "attempt_or_acknowledgement_after_proceed_failure",
                    ),
                ] {
                    if present && !o.protocol_violations.iter().any(|s| s == name) {
                        issue(
                            out,
                            "ordering",
                            format!("unmarked ordering protocol violation: {name}"),
                        );
                    }
                }
            }
        }
        let disposition = p
            .ordering
            .as_ref()
            .map(|o| o.validator_disposition.as_str());
        let valid = match p.collection_status.as_str() {
            "not_reached" => matches!(disposition, None | Some("not_invoked")),
            "not_needed" => disposition == Some("not_needed"),
            "collected" => matches!(disposition, Some("not_spawned" | "reaped" | "unconfirmed")),
            "budget_exhausted" => disposition == Some("not_spawned"),
            "clock_unavailable" => matches!(disposition, Some("not_needed" | "not_spawned")),
            _ => false,
        };
        let observations = if p.collection_status != "collected" {
            p.validator_subprocess.is_none() && p.validator_spawn_failure.is_none()
        } else if disposition == Some("not_spawned") {
            p.validator_subprocess.is_none()
        } else {
            p.validator_spawn_failure.is_none()
                && p.validator_subprocess
                    .as_ref()
                    .is_some_and(|v| v.reaped == Some(disposition == Some("reaped")))
        };
        if !valid || !observations {
            issue(
                out,
                "phase_collection",
                "collection status contradicts validator evidence",
            );
        }
        if p.completion_observed
            && (!p.arrival_observed || !p.ordering.as_ref().is_some_and(|o| o.proceed_observed))
        {
            issue(
                out,
                "phase_collection",
                "completion lacks arrival and observed proceed",
            );
        }
        if p.arrival_observed
            && i != 0
            && !reply.phases[i - 1].completion_observed
            && !(reply.execution_form.as_deref() == Some("actors")
                && reply.phases[i - 1].actor_id != p.actor_id)
        {
            issue(
                out,
                "phase_collection",
                "arrival follows incomplete previous visit of the same process",
            );
        }
        let Some(v) = p.validator_subprocess.as_ref() else {
            continue;
        };
        let eligible: Vec<_> = reply
            .steps
            .iter()
            .filter(|s| {
                s.phase_id == p.phase_id
                    && s.sandbox_check.missing_reason.as_deref() != Some("query_not_requested")
            })
            .collect();
        let expected: BTreeSet<_> = eligible.iter().map(|s| &s.step_id).collect();
        let declared = v.expected_step_ids.as_ref();
        if v.phase_id.as_deref() != Some(p.phase_id.as_str())
            || v.ordinal != Some(p.ordinal)
            || declared.is_none_or(|d| {
                d.len() != expected.len() || d.iter().collect::<BTreeSet<_>>() != expected
            })
        {
            issue(
                out,
                "phase_collection",
                "validator owner or expected query plan mismatch",
            );
        }
        let (Some(records), Some(observed)) = (&v.records, &v.association_issues) else {
            issue(
                out,
                "phase_collection",
                "validator collection lacks records or association issues",
            );
            continue;
        };
        let mut implied: Vec<(String, Option<String>, i64)> = Vec::new();
        let mut groups: BTreeMap<&str, Vec<&ValidatorVerdict>> = BTreeMap::new();
        for r in records {
            if let Some(id) = r.step_id.as_deref() {
                groups.entry(id).or_default().push(r);
            }
        }
        for s in &eligible {
            let matches = groups
                .get(s.step_id.as_str())
                .map(Vec::as_slice)
                .unwrap_or(&[]);
            if matches.len() != 1 {
                implied.push((
                    if matches.is_empty() {
                        "missing_id"
                    } else {
                        "duplicate_id"
                    }
                    .into(),
                    Some(s.step_id.clone()),
                    matches.len() as i64,
                ));
            } else {
                let r = matches[0];
                let prediction = matches!(r.outcome.as_str(), "allow" | "deny");
                let q = &s.sandbox_check;
                let mismatch = ((prediction || r.operation.is_some())
                    && r.operation.as_deref() != Some(q.operation.as_str()))
                    || ((prediction || r.filter_type.is_some())
                        && r.filter_type.as_deref() != Some(filter_type(&q.filter_kind)))
                    || ((prediction || r.filter_value.is_some())
                        && r.filter_value.as_deref()
                            != if q.filter_kind == "none" {
                                None
                            } else {
                                q.filter_value.as_deref()
                            });
                if mismatch {
                    implied.push(("query_mismatch".into(), Some(s.step_id.clone()), 1));
                }
            }
        }
        for (id, rows) in groups {
            if !expected.iter().any(|s| s.as_str() == id) {
                implied.push(("unexpected_id".into(), Some(id.into()), rows.len() as i64));
            }
        }
        let unassociated = records.iter().filter(|r| r.step_id.is_none()).count();
        if unassociated != 0 {
            implied.push(("unassociated".into(), None, unassociated as i64));
        }
        implied.sort();
        let mut observed: Vec<_> = observed
            .iter()
            .map(|i| (i.kind.clone(), i.step_id.clone(), i.count))
            .collect();
        observed.sort();
        if observed != implied {
            issue(
                out,
                "phase_collection",
                "validator association issues disagree with records",
            );
        }
    }
    if reply.preparation_failure.is_none() && all != action_ids {
        issue(
            out,
            "phase_collection",
            "phase actions do not partition reply",
        );
    }
    let ordered: Vec<_> = reply.phases.iter().flat_map(|p| &p.action_ids).collect();
    if ordered
        .iter()
        .copied()
        .filter(|id| reply.steps.iter().any(|s| &s.step_id == *id))
        .collect::<Vec<_>>()
        != reply.steps.iter().map(|s| &s.step_id).collect::<Vec<_>>()
    {
        issue(
            out,
            "phase_collection",
            "step array order disagrees with phase plan",
        );
    }
    if ordered
        .iter()
        .copied()
        .filter(|id| events.iter().any(|e| &e.step_id == *id))
        .collect::<Vec<_>>()
        != events.iter().map(|e| &e.step_id).collect::<Vec<_>>()
    {
        issue(
            out,
            "phase_collection",
            "event array order disagrees with phase plan",
        );
    }
    for s in &reply.steps {
        let Some(p) = reply
            .phases
            .iter()
            .find(|p| p.phase_id == s.phase_id && p.action_ids.contains(&s.step_id))
        else {
            issue(out, "ordering", "step lacks its phase association");
            continue;
        };
        let actor = reply
            .actors
            .iter()
            .flatten()
            .find(|a| Some(&a.actor_id) == s.actor_id.as_ref());
        let (established, pid) = if reply.execution_form.as_deref() == Some("actors") {
            if p.actor_id != s.actor_id || actor.is_none() {
                issue(out, "ordering", "step actor differs from phase actor");
            }
            (
                actor.is_some_and(|a| {
                    matches!(a.setup_status.as_str(), "applied" | "unapplied_declared")
                }),
                actor.and_then(|a| a.launch.as_ref()).map(|l| l.pid),
            )
        } else {
            (
                reply.sandboxed_after_apply == Some(true),
                reply.runner_subprocess.as_ref().map(|s| s.pid),
            )
        };
        let Some(c) = s.comparison.as_ref() else {
            issue(out, "ordering", "ordinary reply step lacks comparison");
            continue;
        };
        if !matches!(c.order.as_str(), "query_first" | "unestablished") {
            issue(out, "ordering", "unknown comparison order");
        }
        if c.limitations.iter().any(|l| {
            ![
                "query_plan:path_unresolved_at_planning",
                "query_plan:prediction_unavailable_pair",
                "query_plan:unrecognized_filter_kind",
                "attempt:started_without_result",
                "attempt:not_reached",
                "attempt:unsupported",
                "attempt:lifecycle_unresolved",
                "attempt:lifecycle_conflicting",
            ]
            .contains(&l.as_str())
        }) {
            issue(
                out,
                "ordering",
                "comparison limitation outside declared vocabulary",
            );
        }
        if c.order != "query_first" {
            continue;
        }
        let q = &s.sandbox_check;
        let chain = p.ordering.as_ref().is_some_and(|o| {
            o.collection_closed_before_proceed
                && o.proceed_set
                && o.proceed_observed
                && o.worker_lifetime_established
                && o.protocol_violations.is_empty()
        });
        let matches: Vec<_> = p
            .validator_subprocess
            .as_ref()
            .and_then(|v| v.records.as_ref())
            .into_iter()
            .flatten()
            .filter(|r| r.step_id.as_deref() == Some(s.step_id.as_str()))
            .collect();
        let native = q.result_source.as_deref() == Some("validator")
            && q.native_rc == Some(q.rc)
            && q.errno.is_some()
            && ((q.outcome == "allow" && q.rc == 0)
                || (q.outcome == "deny" && q.rc == 1 && q.errno == Some(0)));
        if !chain
            || !established
            || pid.is_none()
            || q.pid != pid
            || !native
            || matches.len() != 1
            || !matches.first().is_some_and(|r| {
                query_matches(r, s)
                    && r.rc == q.native_rc
                    && r.errno == q.errno
                    && r.outcome == q.outcome
            })
        {
            issue(
                out,
                "ordering",
                "query_first lacks eligible prediction and complete ordering chain",
            );
        }
    }
}

fn policy_read_issues(
    reply: &PWRunnerRunResult,
    sub: &PWRunnerSubprocess,
    actor: Option<&str>,
    applied: bool,
    out: &mut Vec<IntegrityIssue>,
) {
    let Some(e) = sub.worker_evidence.as_ref() else {
        return;
    };
    let Some(read) = e.policy_read.as_ref() else {
        return;
    };
    if !(0..=262_143).contains(&read.bytes_expected)
        || !(0..=262_143).contains(&read.bytes_received)
        || sub
            .policy_transfer_timeout
            .as_ref()
            .is_some_and(|t| t.bytes_expected != read.bytes_expected)
        || sub
            .policy_transfer_error
            .as_ref()
            .is_some_and(|t| t.bytes_expected != read.bytes_expected)
    {
        issue(
            out,
            "policy_read",
            "receipt exceeds source capacity or disagrees with host transfer",
        );
    }
    if e.failure.as_ref().is_some_and(|f| {
        f.operation == 2
            && f.code == 13
            && (read.bytes_received == read.bytes_expected
                || i64::from(f.detail) != read.bytes_received)
    }) {
        issue(
            out,
            "policy_read",
            "length refusal does not name unequal received count",
        );
    }
    if read.bytes_expected != read.bytes_received {
        let later = applied
            || sub.ready_byte_received == Some(true)
            || sub.done_observed == Some(true)
            || e.readiness.is_some()
            || e.progress
                .as_ref()
                .is_some_and(|p| (3..=11).contains(&p.operation))
            || e.failure
                .as_ref()
                .is_some_and(|f| (3..=11).contains(&f.operation))
            || reply
                .phases
                .iter()
                .filter(|p| p.actor_id.as_deref() == actor)
                .any(|p| {
                    p.arrival_observed
                        || p.completion_observed
                        || p.ordering.as_ref().is_some_and(|o| o.proceed_observed)
                })
            || reply
                .steps
                .iter()
                .filter(|s| s.actor_id.as_deref() == actor)
                .any(|s| s.attempt.result_source.as_deref() == Some("worker"));
        if later {
            issue(
                out,
                "policy_read",
                "unequal receipt contradicts later worker observation",
            );
        }
    }
}

pub(crate) fn admission_problem(reply: &PWRunnerRunResult) -> Option<String> {
    if reply.schema_version != i64::from(crate::json_contract::RESPONSE_SCHEMA_VERSION) {
        return Some(format!(
            "unsupported response schema {}",
            reply.schema_version
        ));
    }
    if let Some(problem) = reply_geometry(reply) {
        return Some(problem.into());
    }
    for c in reply.compiled_profile.iter().chain(
        reply
            .actors
            .iter()
            .flatten()
            .filter_map(|a| a.compiled_profile.as_ref()),
    ) {
        if c.schema_version != 2 || !matches!(c.status.as_str(), "captured" | "unavailable") {
            return Some("unsupported or malformed compiled_profile".into());
        }
        if (c.status == "captured"
            && (c.producer.as_deref() != Some("worker")
                || c.capture_stage.as_deref() != Some("before_apply")))
            || (c.status == "unavailable" && (c.producer.is_some() || c.capture_stage.is_some()))
        {
            return Some("compiled_profile context is inconsistent".into());
        }
    }
    None
}
fn no_worker() -> ActorExecutionDiagnostics {
    ActorExecutionDiagnostics {
        actor_id: None,
        process_disposition: "no_worker",
        termination_cause: None,
        stop_reason: None,
        disposition_integrity: None,
        disposition_issues: Vec::new(),
    }
}
fn project(
    sub: &PWRunnerSubprocess,
    actions: &[ActionRef<'_>],
    degraded: bool,
) -> ActorExecutionDiagnostics {
    let mut out = no_worker();
    out.disposition_issues = validate_lifecycle(sub, actions, degraded);
    if !out.disposition_issues.is_empty() {
        out.process_disposition = "withheld";
        out.termination_cause = Some("unknown");
        out.disposition_integrity = Some("invalid");
        return out;
    }
    let q = &sub
        .disposition
        .as_ref()
        .expect("validated record")
        .questions;
    let c = q.final_status.as_ref().expect("validated claim");
    out.process_disposition = match (c.state.as_str(), c.answer.as_deref()) {
        ("supported", Some("signal")) => "signaled",
        ("supported", Some("exit_code")) => {
            if integer(Some(c)) == Some(0) {
                "clean_exit"
            } else {
                "nonzero_exit"
            }
        }
        ("conflicting", _) => "conflicting",
        ("unresolved" | "inapplicable", _) => "unconfirmed",
        _ => "unrecognized",
    };
    out.termination_cause = if out.process_disposition == "clean_exit" {
        None
    } else {
        Some("unknown")
    };
    if out.process_disposition == "signaled"
        && supported(q.cleanup_trigger.as_ref())
        && supported(q.grace_end.as_ref())
        && answer(q.grace_end.as_ref()) == Some("exhausted")
        && supported(q.kill_request_and_result.as_ref())
        && answer(q.kill_request_and_result.as_ref()) == Some("requested")
    {
        if let Some(PWDispositionValue::Request(r)) = q
            .kill_request_and_result
            .as_ref()
            .and_then(|c| c.value.as_ref())
        {
            if r.rc == 0 && Some(i64::from(r.signal)) == integer(Some(c)) {
                out.termination_cause = match answer(q.cleanup_trigger.as_ref()) {
                    Some("deadline_expiry") => Some("host_sentinel_deadline"),
                    Some("completion") => Some("host_exit_grace_exhausted"),
                    Some("poll_wait_error") => Some("host_cleanup_after_wait_error"),
                    Some("policy_transfer_error") => Some("host_cleanup_after_transfer_error"),
                    Some("policy_transfer_timeout") => Some("host_cleanup_after_transfer_timeout"),
                    _ => Some("unknown"),
                };
            }
        }
    }
    out.stop_reason = q
        .stop_reason
        .as_ref()
        .filter(|c| c.state == "supported")
        .and_then(|c| c.answer.as_ref())
        .filter(|s| {
            [
                "sentinel_deadline",
                "done",
                "child_reaped",
                "wait_error",
                "policy_write_error",
                "policy_transfer_deadline",
            ]
            .contains(&s.as_str())
        })
        .cloned();
    out.disposition_integrity = Some("valid");
    for i in &sub.disposition.as_ref().unwrap().issues {
        out.disposition_issues.push(IntegrityIssue {
            kind: i.kind.clone(),
            detail: i.detail.clone(),
            rule: Some(i.rule.clone()),
            question: Some(i.question.clone()),
            step_index: i.step_index,
            observations: Some(i.observations.clone()),
        });
    }
    out
}

/// Validate semantic relationships without changing or dropping native records.
pub(crate) fn admit_reply(reply: &PWRunnerRunResult) -> Result<(), Vec<IntegrityIssue>> {
    let mut out = Vec::new();
    if let Some(problem) = reply_geometry(reply) {
        issue(&mut out, "reply_capacity", problem);
        return Err(out);
    }

    if let Some(problem) = admission_problem(reply) {
        issue(&mut out, "reply_admission", problem);
    }
    if let Some(f) = &reply.reporting_failure {
        if reply.normalized_outcome != "runner_reporting_failed"
            || reply.rc != 1
            || reply.error.as_ref().is_none_or(String::is_empty)
            || f.origin != "runner_host"
            || f.diagnostic.is_empty()
            || f.original_normalized_outcome.is_empty()
            || reply.steps.iter().any(|s| s.comparison.is_some())
            || (!f.evidence_retained
                && (!reply.steps.is_empty()
                    || reply.runner_subprocess.is_some()
                    || !reply.phases.is_empty()
                    || reply
                        .extension_events
                        .as_ref()
                        .is_some_and(|events| !events.is_empty())))
        {
            issue(
                &mut out,
                "reporting_failure",
                "degraded reply lacks diagnostics or retains comparison claims",
            );
        }
    } else {
        if reply.normalized_outcome == "runner_reporting_failed" {
            issue(
                &mut out,
                "reporting_failure",
                "reporting outcome lacks failure evidence",
            );
        }
        phase_issues(reply, &mut out);
        if let Some(sub) = &reply.runner_subprocess {
            policy_read_issues(
                reply,
                sub,
                None,
                reply.sandboxed_after_apply == Some(true),
                &mut out,
            );
        }
        for a in reply.actors.iter().flatten() {
            if let Some(sub) = &a.subprocess {
                policy_read_issues(
                    reply,
                    sub,
                    Some(&a.actor_id),
                    a.applied == Some(true),
                    &mut out,
                );
            }
        }
        native::validate(reply, &mut out);
        let actor_form = reply.execution_form.as_deref() == Some("actors");
        if actor_form {
            actor_associations(reply, &mut out);
        }
        actor::validate(reply, &mut out);
    }
    if out.is_empty() { Ok(()) } else { Err(out) }
}
fn actor_associations(reply: &PWRunnerRunResult, out: &mut Vec<IntegrityIssue>) {
    let actors = reply.actors.as_deref().unwrap_or(&[]);
    let events = reply.extension_events.as_deref().unwrap_or(&[]);
    let mut ids = BTreeSet::new();
    for (i, a) in actors.iter().enumerate() {
        if a.index != i as i64 || !ids.insert(a.actor_id.as_str()) {
            issue(out, "actor_evidence", "actor index or identity conflict");
        }
        if let (Some(l), Some(s)) = (&a.launch, &a.subprocess) {
            if l.pid != s.pid {
                issue(
                    out,
                    "actor_evidence",
                    "launch and subprocess identify different PIDs",
                );
            }
        }
        let visits: Vec<_> = reply
            .phases
            .iter()
            .enumerate()
            .filter(|(_, p)| p.actor_id.as_deref() == Some(a.actor_id.as_str()))
            .map(|(i, _)| i as i64 + 1)
            .collect();
        if a.visits != visits {
            issue(out, "actor_evidence", "actor visits disagree with schedule");
        }
    }
    for p in &reply.phases {
        if !p.actor_id.as_deref().is_some_and(|id| ids.contains(id)) {
            issue(out, "actor_evidence", "phase actor is absent");
        }
    }
    for e in events {
        if !e.actor_id.as_deref().is_some_and(|id| ids.contains(id))
            || !reply.phases.iter().any(|p| {
                p.phase_id == e.phase_id
                    && p.actor_id == e.actor_id
                    && p.action_ids.contains(&e.step_id)
            })
        {
            issue(
                out,
                "actor_evidence",
                "event actor/phase association conflict",
            );
        }
    }
    for t in reply.transfers.iter().flatten() {
        if !ids.contains(t.source_actor_id.as_str())
            || !ids.contains(t.recipient_actor_id.as_str())
            || !events.iter().any(|e| {
                e.step_id == t.step_id
                    && e.phase_id == t.phase_id
                    && e.operation == "transfer"
                    && e.actor_id.as_deref() == Some(t.source_actor_id.as_str())
                    && e.token_ref.as_deref() == Some(t.token_ref.as_str())
                    && e.delivery_ref.as_deref() == Some(t.delivery_ref.as_str())
            })
        {
            issue(
                out,
                "actor_evidence",
                "transfer lacks matching source event and actors",
            );
        }
    }
}

pub(crate) fn execution_diagnostics(
    reply: Option<&PWRunnerRunResult>,
) -> RunnerExecutionDiagnostics {
    let mut result = RunnerExecutionDiagnostics {
        process_disposition: "no_worker",
        termination_cause: None,
        stop_reason: None,
        disposition_integrity: None,
        disposition_issues: Vec::new(),
        actors: None,
    };
    let Some(reply) = reply else { return result };
    if let Some(problem) = reply_geometry(reply) {
        result.process_disposition = "withheld";
        result.termination_cause = Some("unknown");
        result.disposition_integrity = Some("invalid");
        issue(&mut result.disposition_issues, "reply_capacity", problem);
        return result;
    }
    let degraded = reply.reporting_failure.is_some();
    if reply.execution_form.as_deref() == Some("actors") {
        let mut actors = Vec::new();
        for actor in reply.actors.iter().flatten() {
            let actions: Vec<_> = reply
                .phases
                .iter()
                .filter(|p| p.actor_id.as_deref() == Some(actor.actor_id.as_str()))
                .flat_map(|p| &p.action_ids)
                .filter_map(|id| {
                    reply
                        .steps
                        .iter()
                        .find(|s| &s.step_id == id)
                        .map(ActionRef::Step)
                        .or_else(|| {
                            reply
                                .extension_events
                                .iter()
                                .flatten()
                                .find(|e| &e.step_id == id)
                                .map(ActionRef::Event)
                        })
                })
                .collect();
            let mut d = actor
                .subprocess
                .as_ref()
                .map(|s| project(s, &actions, degraded))
                .unwrap_or_else(no_worker);
            d.actor_id = Some(actor.actor_id.clone());
            actors.push(d);
        }
        if actors.iter().any(|a| a.process_disposition != "no_worker") {
            result.process_disposition = "per_actor";
            result.disposition_integrity = Some(
                if actors
                    .iter()
                    .all(|a| a.disposition_integrity.is_none_or(|v| v == "valid"))
                {
                    "valid"
                } else {
                    "invalid"
                },
            );
        }
        result.actors = Some(actors);
    } else if let Some(sub) = reply.runner_subprocess.as_ref() {
        let actions: Vec<_> = reply.steps.iter().map(ActionRef::Step).collect();
        let d = project(sub, &actions, degraded);
        result.process_disposition = d.process_disposition;
        result.termination_cause = d.termination_cause;
        result.stop_reason = d.stop_reason;
        result.disposition_integrity = d.disposition_integrity;
        result.disposition_issues = d.disposition_issues;
    }
    if let Err(mut issues) = admit_reply(reply) {
        result.process_disposition = "withheld";
        result.termination_cause = Some("unknown");
        result.disposition_integrity = Some("invalid");
        result.disposition_issues.append(&mut issues);
    }
    result
}

// Bounds come from native owners, before joins or per-actor projections. A
// refusal changes only certification; the caller still owns the original reply.
fn claim_geometry(c: Option<&PWDispositionClaim>, references: usize) -> bool {
    c.and_then(|c| c.basis.as_ref())
        .is_none_or(|v| v.len() <= references)
}
fn lifecycle_geometry(sub: &PWRunnerSubprocess) -> Option<&'static str> {
    let d = sub.disposition.as_ref()?;
    if d.steps.len() > 256 || d.issues.len() > 1 + 2 * 256 {
        return Some("worker disposition exceeds native semantic capacity");
    }
    // Fourteen run references plus the two step-local references. Repeated
    // aliases cannot extend the native observation vocabulary or its capacity.
    if RUN_QUESTIONS
        .iter()
        .any(|q| !claim_geometry(q.run(&d.questions), 14))
        || d.steps.iter().any(|s| {
            STEP_QUESTIONS
                .iter()
                .any(|q| !claim_geometry(q.step(&s.questions), 16))
        })
        || d.issues
            .iter()
            .any(|i| i.observations.len() > if i.step_index.is_some() { 16 } else { 14 })
    {
        return Some("disposition reference lists exceed native semantic capacity");
    }
    None
}

fn scope_geometry(s: &PWRunnerAuthorityScope, operations: usize) -> bool {
    s.operations.len() <= operations
        && s.ownership.0.len() <= 5
        && s.integrity_errors.as_ref().is_none_or(|v| v.len() <= 16)
}
fn reply_geometry(reply: &PWRunnerRunResult) -> Option<&'static str> {
    let actor_form = reply.execution_form.as_deref() == Some("actors");
    let phase_cap = if actor_form { 16 } else { 8 };
    if reply.phases.len() > phase_cap
        || reply.steps.len() > 256
        || reply
            .extension_events
            .as_ref()
            .is_some_and(|v| v.len() > 256)
        || reply.extension_events.as_ref().map_or(0, Vec::len) > 256 - reply.steps.len()
        || reply.actors.as_ref().is_some_and(|v| v.len() > 8)
        || reply.transfers.as_ref().is_some_and(|v| v.len() > 64)
    {
        return Some("reply actor/phase/action/transfer tables exceed native semantic capacity");
    }
    if let Some(r) = &reply.resources {
        if r.tokens.len() > 32
            || r.deliveries.len() > 64
            || r.handles.len() > 64
            || r.handles.iter().any(|h| h.raw_equal_handles.len() > 63)
        {
            return Some("authority resource tables exceed native semantic capacity");
        }
    }
    let mut actions = 0usize;
    for p in &reply.phases {
        if p.action_ids.len() > 256 - actions {
            return Some("phase action plan exceeds native semantic capacity");
        }
        actions += p.action_ids.len();
        if let Some(v) = &p.validator_subprocess {
            // ValidatorClient retains at most two records per admitted probe;
            // one native worker has at most 256 probes. Association can add one
            // issue for each expected ID, record ID, and unassociated group.
            let probes = reply
                .steps
                .iter()
                .filter(|s| {
                    s.phase_id == p.phase_id
                        && s.sandbox_check.missing_reason.as_deref() != Some("query_not_requested")
                })
                .count();
            let records = v.records.as_ref().map_or(0, Vec::len);
            if v.expected_step_ids.as_ref().is_some_and(|v| v.len() > 256)
                || records > probes.max(1) * 2
                || v.association_issues
                    .as_ref()
                    .is_some_and(|v| v.len() > probes + records + 1)
            {
                return Some("validator tables exceed native semantic capacity");
            }
        }
    }
    if reply
        .equipment_bindings
        .as_ref()
        .is_some_and(|v| v.len() > 4)
        || reply
            .equipment_entitlements
            .as_ref()
            .is_some_and(|v| v.len() > 12)
    {
        return Some("equipment tables exceed native semantic capacity");
    }
    if let Some(s) = &reply.authority_setup {
        if s.workers.len() > 8
            || s.host.regions.len() > 8
            || s.host.custody.len() > 32
            || !scope_geometry(&s.host.run, 4)
            || s.workers.iter().any(|s| !scope_geometry(s, 16))
            || s.host.regions.iter().any(|s| !scope_geometry(s, 16))
            || s.host.custody.iter().any(|s| !scope_geometry(s, 4))
        {
            return Some("authority setup tables exceed native semantic capacity");
        }
    }
    for lifecycle in reply
        .steps
        .iter()
        .filter_map(|s| s.attempt.lifecycle.as_ref())
        .chain(
            reply
                .extension_events
                .iter()
                .flatten()
                .filter_map(|e| e.lifecycle.as_ref()),
        )
    {
        if !claim_geometry(Some(&lifecycle.boundary), 16)
            || !claim_geometry(Some(&lifecycle.result), 16)
        {
            return Some("lifecycle copy reference lists exceed native semantic capacity");
        }
    }
    if let Some(s) = &reply.runner_subprocess {
        if let Some(p) = lifecycle_geometry(s) {
            return Some(p);
        }
    }
    for a in reply.actors.iter().flatten() {
        if a.visits.len() > 16 {
            return Some("actor visits exceed native semantic capacity");
        }
        if let Some(s) = &a.subprocess {
            if let Some(p) = lifecycle_geometry(s) {
                return Some(p);
            }
        }
        if let Some(e) = &a.equipment {
            if e.required_entitlements.len() > 64
                || e.missing_requirements
                    .as_ref()
                    .is_some_and(|v| v.len() > 64)
                || e.execution.native_observations.len() > 4
            {
                return Some("actor equipment tables exceed native semantic capacity");
            }
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    // Authored public fixtures enter Deserialize only in these controls. Runtime
    // admission receives generated binary-decoded records, never this adapter.
    pub(super) fn ordinary() -> PWRunnerRunResult {
        let mut reply: PWRunnerRunResult = serde_json::from_str(include_str!(
            "../../tests/fixtures/contract/ordinary_phase_reply.json"
        ))
        .expect("authored typed ordinary fixture");
        reply.schema_version = i64::from(crate::json_contract::RESPONSE_SCHEMA_VERSION);
        reply
    }
    pub(super) fn actors() -> PWRunnerRunResult {
        // A complete typed construction of the association slice. The older
        // actor_authority JSON fixture intentionally omits launch observations;
        // it is not a full wire record and must not drive decoder defaults.
        fn actor(id: &str, index: i64, pid: i64, visits: Vec<i64>) -> PWRunnerActorResult {
            PWRunnerActorResult {
                actor_id: id.into(),
                index,
                mode: "apply".into(),
                policy_format: Some("sbpl".into()),
                policy_sha256: None,
                policy_received_sha256: None,
                setup_status: "applied".into(),
                applied: Some(true),
                application_count: 1,
                launch: Some(PWRunnerActorLaunch {
                    pid,
                    parent_pid: 7000,
                    environment: "empty".into(),
                    standard_streams: "stdin_policy_pipe_stdout_stderr_null_device".into(),
                    inherited_descriptors: vec![0, 3, 4],
                }),
                subprocess: None,
                compiled_profile: None,
                visits,
                equipment: None,
                application: None,
                owned_reap: None,
            }
        }
        let mut reply = ordinary();
        let mut phase = reply.phases.remove(0);
        phase.phase_id = "transfer-phase".into();
        phase.ordinal = 1;
        phase.action_ids = vec!["transfer-action".into()];
        phase.actor_id = Some("issuer".into());
        phase.actor_visit = Some(1);
        phase.arrival_observed = false;
        phase.completion_observed = false;
        phase.collection_status = "not_reached".into();
        phase.ordering = None;
        phase.validator_subprocess = None;
        phase.validator_spawn_failure = None;
        phase.termination_gate = None;
        phase.activation_observation = None;
        reply.phases = vec![phase];
        reply.steps.clear();
        reply.runner_subprocess = None;
        reply.sandboxed_after_apply = None;
        reply.execution_form = Some("actors".into());
        reply.actors = Some(vec![
            actor("issuer", 0, 7001, vec![1]),
            actor("subject", 1, 7002, vec![]),
        ]);
        reply.extension_events = Some(vec![PWRunnerExtensionEvent {
            phase_id: "transfer-phase".into(),
            step_id: "transfer-action".into(),
            operation: "transfer".into(),
            token_ref: Some("token".into()),
            handle_ref: None,
            call_boundary_observed: false,
            result_published: false,
            status: "unresolved".into(),
            native_result: None,
            errno: None,
            unavailable_reason: None,
            lifecycle: None,
            actor_id: Some("issuer".into()),
            family: None,
            target: None,
            extension_class: None,
            flags: None,
            delivery_ref: Some("delivery".into()),
            native_nonnull: None,
            token_length: None,
        }]);
        reply.transfers = Some(vec![PWRunnerTransferRecord {
            phase_id: "transfer-phase".into(),
            step_id: "transfer-action".into(),
            source_actor_id: "issuer".into(),
            recipient_actor_id: "subject".into(),
            token_ref: "token".into(),
            delivery_ref: "delivery".into(),
            request_published: false,
            custody_status: "unobserved".into(),
            copy_status: "not_copied".into(),
            equality: "unobserved".into(),
            recipient_acknowledged: false,
            source_acknowledged: false,
            status: "unresolved".into(),
            lifecycle: None,
            recipient_wait: None,
        }]);
        reply
    }

    #[test]
    fn typed_query_order_requires_closure_and_unique_live_prediction() {
        let baseline = ordinary();
        let mut issues = Vec::new();
        phase_issues(&baseline, &mut issues);
        assert!(issues.is_empty(), "baseline phase checks: {issues:?}");
        let cases = [
            "closure",
            "acknowledgement",
            "lifetime",
            "pid",
            "duplicate",
            "association",
            "phase_ordinal",
            "validator_ordinal",
            "late_unassociated",
        ];
        for case in cases {
            let mut reply = baseline.clone();
            let phase = &mut reply.phases[0];
            match case {
                "closure" => {
                    phase
                        .ordering
                        .as_mut()
                        .unwrap()
                        .collection_closed_before_proceed = false
                }
                "acknowledgement" => phase.ordering.as_mut().unwrap().proceed_observed = false,
                "lifetime" => phase.ordering.as_mut().unwrap().worker_lifetime_established = false,
                "pid" => reply.steps[0].sandbox_check.pid = Some(1),
                "duplicate" => {
                    let records = phase
                        .validator_subprocess
                        .as_mut()
                        .unwrap()
                        .records
                        .as_mut()
                        .unwrap();
                    records.push(records[0].clone());
                }
                "association" => reply.steps[0].actor_id = Some("another-process".into()),
                "phase_ordinal" => phase.ordinal += 1,
                "validator_ordinal" => {
                    phase.validator_subprocess.as_mut().unwrap().ordinal = Some(phase.ordinal + 1)
                }
                "late_unassociated" => {
                    let records = phase
                        .validator_subprocess
                        .as_mut()
                        .unwrap()
                        .records
                        .as_mut()
                        .unwrap();
                    let mut additional = records[0].clone();
                    additional.step_id = None;
                    records.push(additional);
                }
                _ => unreachable!(),
            }
            // An ordinary actor_id is not interpreted as worker identity. The
            // association case instead names a phase the action never entered.
            if case == "association" {
                reply.steps[0].phase_id = "unvisited".into();
            }
            let native_rc = reply.steps[0].sandbox_check.native_rc;
            let attempt_rc = reply.steps[0].attempt.rc;
            let mut issues = Vec::new();
            phase_issues(&reply, &mut issues);
            assert!(!issues.is_empty(), "accepted {case}");
            if case == "late_unassociated" {
                assert!(
                    issues
                        .iter()
                        .any(|i| i.detail == "validator association issues disagree with records")
                );
                assert_eq!(
                    reply.phases[0]
                        .validator_subprocess
                        .as_ref()
                        .unwrap()
                        .records
                        .as_ref()
                        .unwrap()
                        .last()
                        .unwrap()
                        .step_id,
                    None
                );
            }
            assert_eq!(reply.steps[0].sandbox_check.native_rc, native_rc);
            assert_eq!(reply.steps[0].attempt.rc, attempt_rc);
        }
    }

    #[test]
    fn typed_actor_query_order_requires_the_named_actor_and_its_pid() {
        let mut baseline = ordinary();
        let mut actor = actors().actors.unwrap().remove(0);
        actor.subprocess = baseline.runner_subprocess.take();
        actor.launch.as_mut().unwrap().pid = actor.subprocess.as_ref().unwrap().pid;
        actor.visits = (1..=baseline.phases.len() as i64).collect();
        for p in &mut baseline.phases {
            p.actor_id = Some(actor.actor_id.clone());
        }
        for s in &mut baseline.steps {
            s.actor_id = Some(actor.actor_id.clone());
        }
        baseline.execution_form = Some("actors".into());
        baseline.actors = Some(vec![actor]);
        let mut baseline_issues = Vec::new();
        phase_issues(&baseline, &mut baseline_issues);
        assert!(baseline_issues.is_empty(), "{baseline_issues:?}");
        for case in ["step_actor", "phase_actor", "actor_pid", "setup"] {
            let mut reply = baseline.clone();
            match case {
                "step_actor" => reply.steps[0].actor_id = Some("another-actor".into()),
                "phase_actor" => reply.phases[0].actor_id = Some("another-actor".into()),
                "actor_pid" => {
                    reply.actors.as_mut().unwrap()[0]
                        .launch
                        .as_mut()
                        .unwrap()
                        .pid += 1
                }
                "setup" => reply.actors.as_mut().unwrap()[0].setup_status = "unobserved".into(),
                _ => unreachable!(),
            }
            let records = reply.phases[0]
                .validator_subprocess
                .as_ref()
                .unwrap()
                .records
                .clone();
            let mut issues = Vec::new();
            phase_issues(&reply, &mut issues);
            assert!(
                issues.iter().any(|i| i.kind == "ordering"),
                "accepted {case}: {issues:?}"
            );
            assert_eq!(
                reply.phases[0]
                    .validator_subprocess
                    .as_ref()
                    .unwrap()
                    .records,
                records
            );
            assert_eq!(reply.steps[0].attempt, baseline.steps[0].attempt);
        }
    }

    #[test]
    fn typed_successful_kill_does_not_supply_a_failed_reaps_status() {
        let reply = ordinary();
        let actions: Vec<_> = reply.steps.iter().map(ActionRef::Step).collect();
        let mut sub = reply.runner_subprocess.clone().unwrap();
        let request = PWRunnerTerminationRequest {
            signal: 9,
            rc: 0,
            errno: None,
        };
        sub.reaped = Some(false);
        sub.exit_code = None;
        sub.term_signal = None;
        sub.exit_requested = Some(true);
        sub.termination_request = Some(request.clone());
        sub.wait_errors = Some(vec![PWRunnerWaitError {
            stage: "after_termination".into(),
            rc: -1,
            errno: 10,
        }]);
        sub.poll_stop_reason = Some("sentinel_deadline".into());
        sub.cleanup_trigger = Some("deadline_expiry".into());
        sub.grace_end = Some("exhausted".into());
        sub.collection_basis = Some("execution_may_continue".into());
        let q = &mut sub.disposition.as_mut().unwrap().questions;
        let final_status = q.final_status.as_mut().unwrap();
        final_status.state = "unresolved".into();
        final_status.answer = None;
        final_status.value = None;
        final_status.reason = Some("no_successful_reap".into());
        final_status.basis = None;
        q.stop_reason.as_mut().unwrap().answer = Some("sentinel_deadline".into());
        q.cleanup_trigger.as_mut().unwrap().answer = Some("deadline_expiry".into());
        q.grace_end.as_mut().unwrap().answer = Some("exhausted".into());
        q.collection_basis.as_mut().unwrap().answer = Some("execution_may_continue".into());
        let kill = q.kill_request_and_result.as_mut().unwrap();
        kill.answer = Some("requested".into());
        kill.value = Some(PWDispositionValue::Request(request.clone()));
        kill.basis = Some(vec!["termination_request".into()]);
        let honest = project(&sub, &actions, false);
        assert_eq!(
            honest.process_disposition, "unconfirmed",
            "{:?}",
            honest.disposition_issues
        );
        assert_eq!(honest.disposition_integrity, Some("valid"));
        assert_eq!(honest.termination_cause, Some("unknown"));
        assert_eq!(sub.termination_request, Some(request));
        assert_eq!(sub.exit_code, None);
        assert_eq!(sub.term_signal, None);
        let native_wait = sub.wait_errors.clone();
        let unsupported = sub
            .disposition
            .as_mut()
            .unwrap()
            .questions
            .final_status
            .as_mut()
            .unwrap();
        unsupported.state = "supported".into();
        unsupported.answer = Some("signal".into());
        unsupported.value = Some(PWDispositionValue::Integer(9));
        unsupported.basis = Some(vec!["reaped".into(), "term_signal".into()]);
        unsupported.reason = None;
        let rejected = project(&sub, &actions, false);
        assert_eq!(rejected.process_disposition, "withheld");
        assert!(
            rejected
                .disposition_issues
                .iter()
                .any(|i| i.detail == "final_status contradicts reaped status")
        );
        assert_eq!(sub.wait_errors, native_wait);
        assert_eq!(sub.reaped, Some(false));
        assert_eq!(sub.term_signal, None);
    }

    #[test]
    fn typed_lifecycle_refuses_status_claim_without_owned_reap() {
        let baseline = ordinary();
        let actions: Vec<_> = baseline.steps.iter().map(ActionRef::Step).collect();
        let sub = baseline.runner_subprocess.as_ref().unwrap();
        let accepted = project(sub, &actions, false);
        assert_eq!(
            accepted.process_disposition, "clean_exit",
            "{:?}",
            accepted.disposition_issues
        );
        for case in ["reap", "pid", "claim", "request", "progress", "step"] {
            let mut sub = sub.clone();
            match case {
                "reap" => sub.reaped = Some(false),
                "pid" => sub.pid = 0,
                "claim" => sub.disposition.as_mut().unwrap().questions.final_status = None,
                "request" => {
                    let q = sub
                        .disposition
                        .as_mut()
                        .unwrap()
                        .questions
                        .kill_request_and_result
                        .as_mut()
                        .unwrap();
                    q.state = "supported".into();
                    q.answer = Some("requested".into());
                    q.value = Some(PWDispositionValue::Request(PWRunnerTerminationRequest {
                        signal: 9,
                        rc: 0,
                        errno: None,
                    }));
                    q.basis = Some(vec!["termination_request".into(), "exit_requested".into()]);
                    sub.termination_request = None;
                }
                "progress" => {
                    if let Some(e) = sub.worker_evidence.as_mut() {
                        if let Some(p) = e.progress.as_mut() {
                            p.raw ^= 1;
                        } else {
                            sub.disposition
                                .as_mut()
                                .unwrap()
                                .questions
                                .progress_association = None;
                        }
                    }
                }
                "step" => {
                    sub.disposition.as_mut().unwrap().steps[0].step_id = "other-action".into()
                }
                _ => unreachable!(),
            }
            let exit = sub.exit_code;
            let d = project(&sub, &actions, false);
            assert_eq!(d.process_disposition, "withheld", "accepted {case}");
            assert_eq!(sub.exit_code, exit, "{case} repaired raw native status");
            assert!(!d.disposition_issues.is_empty());
        }
    }

    #[test]
    fn typed_signaled_partial_worker_preserves_entered_and_unreached_boundaries() {
        // Authored regression for the observed killed-before-slot-publication
        // sequence: a completed prefix, entry to action 1 without publication,
        // and action 2 not reached. Native status and progress are separate.
        let mut reply = ordinary();
        let mut sub = reply.runner_subprocess.take().unwrap();
        sub.reaped = Some(true);
        sub.exit_code = None;
        sub.term_signal = Some(9);
        sub.partial_steps = true;
        sub.poll_stop_reason = Some("child_reaped".into());
        sub.cleanup_trigger = Some("child_reaped".into());
        sub.grace_end = Some("not_entered".into());
        sub.collection_basis = Some("after_confirmed_reap".into());
        sub.worker_evidence.as_mut().unwrap().progress = Some(PWWorkerProgress {
            raw: 152_043_522,
            operation: 9,
            stage: 1,
            index: Some(1),
        });
        let record = sub.disposition.as_mut().unwrap();
        let q = &mut record.questions;
        q.final_status.as_mut().unwrap().answer = Some("signal".into());
        q.final_status.as_mut().unwrap().value = Some(PWDispositionValue::Integer(9));
        q.final_status.as_mut().unwrap().basis = Some(vec!["reaped".into(), "term_signal".into()]);
        q.stop_reason.as_mut().unwrap().answer = Some("child_reaped".into());
        q.cleanup_trigger.as_mut().unwrap().answer = Some("child_reaped".into());
        q.grace_end.as_mut().unwrap().answer = Some("not_entered".into());
        q.progress_association.as_mut().unwrap().answer = Some("step_index".into());
        q.progress_association.as_mut().unwrap().value = Some(PWDispositionValue::Integer(1));
        q.progress_association.as_mut().unwrap().basis =
            Some(vec!["progress".into(), "plan".into()]);
        for i in [1, 2] {
            let step = &mut record.steps[i];
            step.slot = "incomplete".into();
            let boundary = step.questions.step_boundary_reached.as_mut().unwrap();
            boundary.answer = Some(if i == 1 { "reached" } else { "not_reached" }.into());
            boundary.basis = Some(if i == 1 {
                vec!["progress".into(), "slot".into(), "attempt_support".into()]
            } else {
                vec!["progress".into(), "slot".into(), "collection_basis".into()]
            });
            let publication = step.questions.step_result_published.as_mut().unwrap();
            publication.answer = Some("unpublished".into());
            publication.basis = Some(vec![
                "slot".into(),
                "collection_basis".into(),
                "progress".into(),
            ]);
            let summary = if i == 1 {
                "started_without_result"
            } else {
                "not_reached"
            };
            let attempt = &mut reply.steps[i].attempt;
            attempt.result_source = Some("synthetic".into());
            attempt.missing_reason = Some("slot_incomplete".into());
            attempt.rc = -1;
            attempt.outcome = "no_completed_result".into();
            attempt.lifecycle = Some(PWAttemptLifecycle {
                summary: summary.into(),
                boundary: step.questions.step_boundary_reached.clone().unwrap(),
                result: step.questions.step_result_published.clone().unwrap(),
            });
            reply.steps[i].comparison.as_mut().unwrap().limitations =
                vec![format!("attempt:{summary}")];
        }
        let actions: Vec<_> = reply.steps.iter().map(ActionRef::Step).collect();
        let projection = project(&sub, &actions, false);
        assert_eq!(
            projection.process_disposition, "signaled",
            "{:?}",
            projection.disposition_issues
        );
        assert_eq!(projection.disposition_integrity, Some("valid"));
        assert_eq!(projection.termination_cause, Some("unknown"));
        assert!(projection.disposition_issues.is_empty());
        assert_eq!(sub.term_signal, Some(9));
        assert_eq!(
            sub.worker_evidence
                .as_ref()
                .unwrap()
                .progress
                .as_ref()
                .unwrap()
                .raw,
            152_043_522
        );
        assert_eq!(
            reply.steps[0].attempt.lifecycle.as_ref().unwrap().summary,
            "completed"
        );
        assert_eq!(
            reply.steps[1].attempt.lifecycle.as_ref().unwrap().summary,
            "started_without_result"
        );
        assert_eq!(
            reply.steps[2].attempt.lifecycle.as_ref().unwrap().summary,
            "not_reached"
        );

        // Moving a later boundary to reached is still rejected; accepting this
        // genuine partial sequence must not weaken the progress witness rule.
        let mut false_boundary = sub.clone();
        false_boundary.disposition.as_mut().unwrap().steps[2]
            .questions
            .step_boundary_reached
            .as_mut()
            .unwrap()
            .answer = Some("reached".into());
        let rejected = project(&false_boundary, &actions, false);
        assert_eq!(rejected.process_disposition, "withheld");
        assert!(
            rejected
                .disposition_issues
                .iter()
                .any(|i| i.detail == "boundary lacks unopposed witness")
        );
    }

    #[test]
    fn typed_final_status_requires_its_native_witness_basis() {
        let reply = ordinary();
        let actions: Vec<_> = reply.steps.iter().map(ActionRef::Step).collect();
        let baseline = reply.runner_subprocess.as_ref().unwrap();
        let final_status = baseline
            .disposition
            .as_ref()
            .unwrap()
            .questions
            .final_status
            .as_ref()
            .unwrap();
        assert_eq!(final_status.state, "supported");
        assert_eq!(final_status.answer.as_deref(), Some("exit_code"));
        assert!(cites(final_status, "reaped") && cites(final_status, "exit_code"));
        assert_eq!(baseline.reaped, Some(true));
        assert_eq!(baseline.exit_code, Some(0));
        assert_eq!(
            project(baseline, &actions, false).process_disposition,
            "clean_exit"
        );

        for case in ["absent", "unrelated"] {
            let mut sub = baseline.clone();
            let claim = sub
                .disposition
                .as_mut()
                .unwrap()
                .questions
                .final_status
                .as_mut()
                .unwrap();
            claim.basis = match case {
                "absent" => None,
                // This host fact exists and resolves, but cannot witness the
                // native status. Shape and reference validity are insufficient.
                "unrelated" => Some(vec!["poll_stop_reason".into(), "exit_code".into()]),
                _ => unreachable!(),
            };
            assert!(reference_resolves("poll_stop_reason", &sub, None));
            let projection = project(&sub, &actions, false);
            assert_eq!(
                projection.process_disposition, "withheld",
                "accepted {case} basis"
            );
            assert_eq!(projection.disposition_integrity, Some("invalid"));
            assert!(
                projection.disposition_issues.iter().any(|issue| {
                    issue.kind == "invalid_claim" && issue.detail.starts_with("final_status:")
                }),
                "missing final-status basis refusal for {case}: {:?}",
                projection.disposition_issues
            );
            assert_eq!(sub.pid, baseline.pid);
            assert_eq!(sub.reaped, baseline.reaped);
            assert_eq!(sub.exit_code, baseline.exit_code);
            assert_eq!(sub.term_signal, baseline.term_signal);
            assert_eq!(sub.termination_request, baseline.termination_request);
            assert_eq!(sub.worker_evidence, baseline.worker_evidence);
            let retained = sub
                .disposition
                .as_ref()
                .unwrap()
                .questions
                .final_status
                .as_ref()
                .unwrap();
            assert_eq!(retained.answer, final_status.answer);
            assert_eq!(retained.value, final_status.value);
        }
    }

    #[test]
    fn typed_actor_references_reject_other_source_without_erasing_transfer() {
        let mut reply = actors();
        let mut issues = Vec::new();
        actor_associations(&reply, &mut issues);
        assert!(issues.is_empty(), "actor baseline: {issues:?}");
        let transfer = reply.transfers.as_mut().unwrap().first_mut().unwrap();
        transfer.source_actor_id = "unlaunched-source".into();
        let status = transfer.status.clone();
        let mut issues = Vec::new();
        actor_associations(&reply, &mut issues);
        assert!(issues.iter().any(|i| i.detail.contains("transfer")));
        assert_eq!(reply.transfers.as_ref().unwrap()[0].status, status);
        let d = execution_diagnostics(Some(&reply));
        assert_eq!(d.disposition_integrity, Some("invalid"));
        assert!(
            d.disposition_issues
                .iter()
                .any(|i| i.kind == "actor_evidence")
        );
    }

    #[test]
    fn typed_invalid_actor_account_keeps_independent_actor_endings() {
        let mut reply = ordinary();
        let mut actor = actors().actors.unwrap().remove(0);
        actor.actor_id = "constructed-fixture-actor".into();
        actor.setup_status = "applied".into();
        actor.applied = Some(true);
        actor.subprocess = reply.runner_subprocess.take();
        actor.launch.as_mut().unwrap().pid = actor.subprocess.as_ref().unwrap().pid;
        actor.visits = (1..=reply.phases.len() as i64).collect();
        for p in &mut reply.phases {
            p.actor_id = Some(actor.actor_id.clone());
        }
        for step in &mut reply.steps {
            step.actor_id = Some(actor.actor_id.clone());
        }
        reply.execution_form = Some("actors".into());
        reply.actors = Some(vec![actor]);
        let d = execution_diagnostics(Some(&reply));
        assert_eq!(d.process_disposition, "withheld");
        assert!(
            d.disposition_issues
                .iter()
                .any(|i| i.kind == "actor_evidence")
        );
        assert_eq!(d.disposition_integrity, Some("invalid"));
        let actors = d.actors.as_ref().unwrap();
        assert_eq!(actors.len(), reply.actors.as_ref().unwrap().len());
        assert!(
            actors.iter().any(|a| a.process_disposition == "clean_exit"),
            "{actors:?}"
        );
        for (projection, raw) in actors.iter().zip(reply.actors.as_ref().unwrap()) {
            assert_eq!(projection.actor_id.as_deref(), Some(raw.actor_id.as_str()));
            if raw
                .subprocess
                .as_ref()
                .is_some_and(|s| s.reaped == Some(true) && s.exit_code == Some(0))
            {
                assert_eq!(
                    projection.process_disposition, "clean_exit",
                    "{:?}",
                    projection.disposition_issues
                );
            }
        }
    }

    #[test]
    fn typed_missing_fresh_payload_is_invalid_and_exec_absence_remains_unknown() {
        for action in ["read_fresh", "write_fresh", "create_fresh"] {
            let mut reply = ordinary();
            let attempt = &mut reply.steps[0].attempt;
            attempt.requested_kind = Some("file".into());
            attempt.requested_action = Some(action.into());
            attempt.result_source = Some("worker".into());
            attempt.fresh_read = None;
            attempt.fresh_write = None;
            let native_rc = attempt.rc;
            let issues = admit_reply(&reply)
                .expect_err("published fresh attempt requires its native record");
            assert!(
                issues
                    .iter()
                    .any(|i| i.kind == "fresh_read" || i.kind == "fresh_write"),
                "{action}: {issues:?}"
            );
            assert_eq!(
                execution_diagnostics(Some(&reply)).disposition_integrity,
                Some("invalid")
            );
            assert_eq!(reply.steps[0].attempt.rc, native_rc);
        }
        let mut attempt = ordinary().steps.remove(0).attempt;
        attempt.requested_kind = Some("exec".into());
        attempt.requested_action = Some("spawn".into());
        attempt.exec_observation = None;
        assert!(
            native::exec_problem(&attempt).is_none(),
            "absence is unknown, including a spawn before child creation"
        );
    }

    #[test]
    fn typed_ordinary_reply_cannot_hide_actor_evidence_behind_its_form() {
        let actor_fixture = actors();
        let mut reply = ordinary();
        reply.actors = actor_fixture.actors.clone();
        let invalid = execution_diagnostics(Some(&reply));
        assert_eq!(invalid.disposition_integrity, Some("invalid"));
        assert!(
            invalid
                .disposition_issues
                .iter()
                .any(|i| i.kind == "actor_evidence")
        );
        let event = actor_fixture.extension_events.unwrap().remove(0);
        reply.phases[0].action_ids.push(event.step_id.clone());
        reply.extension_events = Some(vec![PWRunnerExtensionEvent {
            phase_id: reply.phases[0].phase_id.clone(),
            ..event
        }]);
        let native_exit = reply.runner_subprocess.as_ref().unwrap().exit_code;
        let d = execution_diagnostics(Some(&reply));
        assert_eq!(d.disposition_integrity, Some("invalid"));
        assert!(
            d.disposition_issues
                .iter()
                .any(|i| i.kind == "actor_evidence"
                    && i.detail == "ordinary reply carries actor authority evidence")
        );
        assert_eq!(
            reply.runner_subprocess.as_ref().unwrap().exit_code,
            native_exit
        );
    }

    #[test]
    fn typed_degradation_never_certifies_surviving_comparison() {
        let mut reply = ordinary();
        reply.normalized_outcome = "runner_reporting_failed".into();
        reply.rc = 1;
        reply.error = Some("controlled host reporting failure".into());
        reply.reporting_failure = Some(PWRunnerReportingFailure {
            origin: "runner_host".into(),
            diagnostic: "controlled rich encoder failure".into(),
            original_rc: 0,
            original_normalized_outcome: "finished".into(),
            original_error: None,
            evidence_retained: true,
        });
        assert!(
            admit_reply(&reply)
                .unwrap_err()
                .iter()
                .any(|i| i.kind == "reporting_failure")
        );
        let original_attempt = reply.steps[0].attempt.clone();
        for step in &mut reply.steps {
            step.comparison = None;
        }
        assert!(admit_reply(&reply).is_ok());
        assert_eq!(reply.steps[0].attempt, original_attempt);
    }
    #[test]
    fn typed_shared_evidence_type_corpus() {
        let baseline: serde_json::Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/contract/ordinary_phase_reply.json"
        ))
        .unwrap();
        let rows: Vec<serde_json::Value> = serde_json::from_str(include_str!(
            "../../tests/fixtures/contract/evidence_types.json"
        ))
        .unwrap();
        for row in rows {
            let mut v = baseline.clone();
            for patch in row["patches"].as_array().unwrap() {
                let (parent, key) = patch["path"].as_str().unwrap().rsplit_once('/').unwrap();
                let target = v.pointer_mut(parent).unwrap();
                if let Some(a) = target.as_array_mut() {
                    a[key.parse::<usize>().unwrap()] = patch["value"].clone();
                } else {
                    target[key] = patch["value"].clone();
                }
            }
            match serde_json::from_value::<PWRunnerRunResult>(v) {
                Ok(reply) => {
                    let before = reply.clone();
                    let d = execution_diagnostics(Some(&reply));
                    assert_eq!(
                        d.disposition_integrity == Some("valid"),
                        row["accepted"] == true,
                        "{}: {:?}",
                        row["name"],
                        d.disposition_issues
                    );
                    assert_eq!(reply, before);
                }
                Err(error) => assert_eq!(row["accepted"], false, "{}: {error}", row["name"]),
            }
        }
    }
    #[test]
    fn phase_collection_states_gate_disposition_without_requiring_success() {
        let ordinary = ordinary();
        for (status, disposition, valid) in [
            ("not_reached", "not_invoked", true),
            ("not_needed", "not_needed", true),
            ("collected", "not_spawned", true),
            ("collected", "reaped", true),
            ("collected", "unconfirmed", true),
            ("budget_exhausted", "not_spawned", true),
            ("clock_unavailable", "not_needed", true),
            ("clock_unavailable", "not_spawned", true),
            ("not_reached", "reaped", false),
            ("not_needed", "not_spawned", false),
            ("budget_exhausted", "reaped", false),
            ("clock_unavailable", "reaped", false),
            ("collected", "not_needed", false),
        ] {
            let mut reply = ordinary.clone();
            reply.phases.truncate(1);
            reply.steps.truncate(1);
            reply.steps[0].comparison.as_mut().unwrap().order = "unestablished".into();
            let phase = &mut reply.phases[0];
            phase.arrival_observed = true;
            phase.completion_observed = false;
            phase.collection_status = status.into();
            let order = phase.ordering.as_mut().unwrap();
            order.validator_disposition = disposition.into();
            order.collection_closed_before_proceed = disposition != "not_invoked";
            order.proceed_set = false;
            order.proceed_observed = false;
            if matches!(disposition, "reaped" | "unconfirmed") {
                phase.validator_subprocess.as_mut().unwrap().reaped = Some(disposition == "reaped");
            } else {
                phase.validator_subprocess = None;
            }
            let before = reply.clone();
            let mut issues = Vec::new();
            phase_issues(&reply, &mut issues);
            assert_eq!(
                issues.is_empty(),
                valid,
                "{status}/{disposition}: {issues:?}"
            );
            assert_eq!(reply, before);
        }
    }
    #[test]
    fn typed_host_cleanup_cause_requires_all_independent_observations() {
        let reply = ordinary();
        let actions: Vec<_> = reply.steps.iter().map(ActionRef::Step).collect();
        for (trigger, stop, cause) in [
            ("completion", "done", "host_exit_grace_exhausted"),
            (
                "deadline_expiry",
                "sentinel_deadline",
                "host_sentinel_deadline",
            ),
            (
                "poll_wait_error",
                "wait_error",
                "host_cleanup_after_wait_error",
            ),
            ("future_trigger", "future_stop", "unknown"),
        ] {
            let mut sub = reply.runner_subprocess.as_ref().unwrap().clone();
            sub.exit_code = None;
            sub.term_signal = Some(9);
            sub.reaped = Some(true);
            sub.exit_requested = Some(true);
            sub.grace_end = Some("exhausted".into());
            sub.cleanup_trigger = Some(trigger.into());
            sub.poll_stop_reason = Some(stop.into());
            let request = PWRunnerTerminationRequest {
                signal: 9,
                rc: 0,
                errno: None,
            };
            sub.termination_request = Some(request.clone());
            let q = &mut sub.disposition.as_mut().unwrap().questions;
            let claim = |answer: &str, basis: &[&str], value: Option<PWDispositionValue>| {
                PWDispositionClaim {
                    state: "supported".into(),
                    answer: Some(answer.into()),
                    basis: Some(basis.iter().map(|s| (*s).into()).collect()),
                    value,
                    reason: None,
                    issue: None,
                }
            };
            q.final_status = Some(claim(
                "signal",
                &["reaped", "term_signal"],
                Some(PWDispositionValue::Integer(9)),
            ));
            q.stop_reason = Some(claim(stop, &["poll_stop_reason"], None));
            q.cleanup_trigger = Some(claim(trigger, &["cleanup_trigger", "exit_requested"], None));
            q.grace_end = Some(claim("exhausted", &["grace_end", "exit_requested"], None));
            q.kill_request_and_result = Some(claim(
                "requested",
                &["termination_request"],
                Some(PWDispositionValue::Request(request)),
            ));
            let d = project(&sub, &actions, false);
            assert_eq!(
                d.process_disposition, "signaled",
                "{:?}",
                d.disposition_issues
            );
            assert_eq!(d.termination_cause, Some(cause));
            let before = sub.clone();
            sub.reaped = Some(false);
            let d = project(&sub, &actions, false);
            assert_eq!(d.process_disposition, "withheld");
            assert_eq!(d.termination_cause, Some("unknown"));
            assert_eq!(sub.termination_request, before.termination_request);
            assert_eq!(sub.term_signal, before.term_signal);
        }
    }
    #[test]
    fn typed_profile_context_gate_includes_actor_captures_and_degradation() {
        let capture = CompiledProfileCapture {
            schema_version: 2,
            status: "captured".into(),
            reason: None,
            worker_pid: 7001,
            producer: Some("worker".into()),
            capture_stage: Some("before_apply".into()),
            request_nonce: None,
            profile_type: None,
            bytecode_length: None,
            bytecode_sha256: None,
            bytecode_b64: None,
            source_sha256: None,
            source_length: None,
            params_sha256: None,
            parameter_count: None,
        };
        for degraded in [false, true] {
            let mut reply = actors();
            reply.actors.as_mut().unwrap()[0].compiled_profile = Some(capture.clone());
            if degraded {
                reply.reporting_failure = Some(PWRunnerReportingFailure {
                    origin: "runner_host".into(),
                    diagnostic: "controlled conflict".into(),
                    original_rc: 0,
                    original_normalized_outcome: "finished".into(),
                    original_error: None,
                    evidence_retained: true,
                });
            }
            assert!(admission_problem(&reply).is_none());
            for mutation in ["stage", "version", "unavailable_context"] {
                let mut changed = reply.clone();
                let c = changed.actors.as_mut().unwrap()[0]
                    .compiled_profile
                    .as_mut()
                    .unwrap();
                match mutation {
                    "stage" => c.capture_stage = None,
                    "version" => c.schema_version = 1,
                    "unavailable_context" => c.status = "unavailable".into(),
                    _ => unreachable!(),
                }
                let raw = changed.clone();
                assert!(
                    admission_problem(&changed).is_some(),
                    "{degraded}/{mutation}"
                );
                assert_eq!(changed, raw);
            }
        }
    }
    #[test]
    fn typed_minimal_reporting_failure_cannot_retain_authority_events() {
        let mut reply = ordinary();
        reply.steps.clear();
        reply.phases.clear();
        reply.runner_subprocess = None;
        reply.normalized_outcome = "runner_reporting_failed".into();
        reply.rc = 1;
        reply.error = Some("controlled reporting failure".into());
        reply.reporting_failure = Some(PWRunnerReportingFailure {
            origin: "runner_host".into(),
            diagnostic: "controlled minimal fallback".into(),
            original_rc: 0,
            original_normalized_outcome: "finished".into(),
            original_error: None,
            evidence_retained: false,
        });
        assert!(admit_reply(&reply).is_ok());
        let event = actors().extension_events.unwrap().remove(0);
        reply.extension_events = Some(vec![event.clone()]);
        assert!(
            admit_reply(&reply)
                .unwrap_err()
                .iter()
                .any(|i| i.kind == "reporting_failure")
        );
        assert_eq!(reply.extension_events.as_ref().unwrap()[0], event);
        reply.reporting_failure.as_mut().unwrap().evidence_retained = true;
        assert!(
            admit_reply(&reply).is_ok(),
            "evidence-preserving degradation retains conflicting/raw authority events"
        );
    }
    #[test]
    fn typed_worker_requires_phase_presence_and_ordering_even_before_arrival() {
        let mut reply = ordinary();
        let worker = reply.runner_subprocess.as_ref().unwrap().clone();
        reply.steps.clear();
        reply.phases.clear();
        let sub = reply.runner_subprocess.as_mut().unwrap();
        sub.partial_steps = false;
        sub.disposition.as_mut().unwrap().steps.clear();
        let d = execution_diagnostics(Some(&reply));
        assert_eq!(d.process_disposition, "withheld");
        assert_eq!(d.disposition_integrity, Some("invalid"));
        assert!(
            d.disposition_issues
                .iter()
                .any(|i| i.detail == "worker subprocess requires phase evidence")
        );
        assert_eq!(reply.runner_subprocess.as_ref().unwrap().pid, worker.pid);
        let mut reply = ordinary();
        reply.phases[0].ordering = None;
        reply.phases[0].collection_status = "not_reached".into();
        reply.phases[0].validator_subprocess = None;
        reply.phases[0].arrival_observed = false;
        reply.phases[0].completion_observed = false;
        let before = reply.clone();
        let d = execution_diagnostics(Some(&reply));
        assert_eq!(d.process_disposition, "withheld");
        assert_eq!(d.disposition_integrity, Some("invalid"));
        assert!(
            d.disposition_issues
                .iter()
                .any(|i| i.detail == "phase ordering is required beside a worker subprocess")
        );
        assert_eq!(reply, before);
    }
    #[test]
    fn typed_validator_spawn_failure_requires_its_native_call_identity() {
        let mut reply = ordinary();
        let p = &mut reply.phases[0];
        p.validator_subprocess = None;
        p.ordering.as_mut().unwrap().validator_disposition = "not_spawned".into();
        p.validator_spawn_failure = Some(PWRunnerSpawnFailure {
            origin: "runner_host".into(),
            operation: "posix_spawn".into(),
            executable_path: "/constructed/validator".into(),
            return_code: libc::EAGAIN,
            diagnostic: "constructed native spawn failure".into(),
        });
        reply.steps[0].comparison.as_mut().unwrap().order = "unestablished".into();
        let mut out = Vec::new();
        phase_issues(&reply, &mut out);
        assert!(out.is_empty(), "{out:?}");
        for mutation in ["origin", "operation", "path", "rc"] {
            let mut r = reply.clone();
            let f = r.phases[0].validator_spawn_failure.as_mut().unwrap();
            match mutation {
                "origin" => f.origin = "worker".into(),
                "operation" => f.operation = "waitpid".into(),
                "path" => f.executable_path.clear(),
                "rc" => f.return_code = 0,
                _ => unreachable!(),
            };
            let before = r.clone();
            let mut out = Vec::new();
            phase_issues(&r, &mut out);
            assert!(
                out.iter()
                    .any(|i| i.detail == "invalid validator spawn failure record"),
                "{mutation}: {out:?}"
            );
            assert_eq!(r, before);
        }
    }
    #[test]
    fn typed_ordering_contradictions_need_explicit_native_fault_markers() {
        let mut reply = ordinary();
        let p = &mut reply.phases[0];
        p.validator_subprocess = None;
        p.collection_status = "not_reached".into();
        let order = p.ordering.as_mut().unwrap();
        order.validator_disposition = "not_invoked".into();
        order.collection_closed_before_proceed = false;
        reply.steps[0].comparison.as_mut().unwrap().order = "unestablished".into();
        let mut out = Vec::new();
        phase_issues(&reply, &mut out);
        assert!(out.iter().any(|i| i.detail
            == "unmarked ordering protocol violation: release_without_collection_closure"));
        reply.phases[0]
            .ordering
            .as_mut()
            .unwrap()
            .protocol_violations
            .push("release_without_collection_closure".into());
        let before = reply.clone();
        let mut out = Vec::new();
        phase_issues(&reply, &mut out);
        assert!(out.is_empty(), "{out:?}");
        assert_eq!(
            reply, before,
            "marking a conflict must preserve its raw ordering observations"
        );
        let mut reply = ordinary();
        reply.phases[0]
            .ordering
            .as_mut()
            .unwrap()
            .collection_closed_before_proceed = false;
        let mut out = Vec::new();
        phase_issues(&reply, &mut out);
        assert!(
            out.iter()
                .any(|i| i.detail == "collection decision disagrees with validator disposition")
        );
    }
    #[test]
    fn typed_no_index_progress_cannot_hide_a_request_variant_as_absence() {
        let reply = ordinary();
        let actions: Vec<_> = reply.steps.iter().map(ActionRef::Step).collect();
        let mut sub = reply.runner_subprocess.unwrap();
        let c = sub
            .disposition
            .as_ref()
            .unwrap()
            .questions
            .progress_association
            .as_ref()
            .unwrap();
        assert_eq!(c.answer.as_deref(), Some("none"));
        assert_eq!(c.value, None);
        assert_eq!(
            project(&sub, &actions, false).process_disposition,
            "clean_exit"
        );
        let facts = sub.worker_evidence.clone();
        sub.disposition
            .as_mut()
            .unwrap()
            .questions
            .progress_association
            .as_mut()
            .unwrap()
            .value = Some(PWDispositionValue::Request(PWRunnerTerminationRequest {
            signal: 9,
            rc: 0,
            errno: None,
        }));
        let d = project(&sub, &actions, false);
        assert_eq!(d.process_disposition, "withheld");
        assert_eq!(d.disposition_integrity, Some("invalid"));
        assert!(
            d.disposition_issues
                .iter()
                .any(|i| i.detail == "progress claim contradicts encoded progress")
        );
        assert_eq!(sub.worker_evidence, facts);
    }
    #[test]
    fn typed_conflicting_status_preserves_the_native_pair_and_rule() {
        let reply = ordinary();
        let actions: Vec<_> = reply.steps.iter().map(ActionRef::Step).collect();
        let mut sub = reply.runner_subprocess.unwrap();
        sub.term_signal = Some(9);
        let d = project(&sub, &actions, false);
        assert_eq!(d.process_disposition, "withheld");
        let record = sub.disposition.as_mut().unwrap();
        record.questions.final_status = Some(PWDispositionClaim {
            state: "conflicting".into(),
            answer: None,
            value: None,
            reason: None,
            issue: Some(0),
            basis: None,
        });
        record.issues = vec![PWDispositionIssue {
            kind: "conflict".into(),
            rule: "D1".into(),
            question: "final_status".into(),
            step_index: None,
            observations: vec!["exit_code".into(), "term_signal".into()],
            detail: "constructed successful reap carries both exit and signal".into(),
        }];
        let before = sub.clone();
        let d = project(&sub, &actions, false);
        assert_eq!(
            d.process_disposition, "conflicting",
            "{:?}",
            d.disposition_issues
        );
        assert_eq!(d.disposition_integrity, Some("valid"));
        assert_eq!(d.termination_cause, Some("unknown"));
        assert!(
            d.disposition_issues
                .iter()
                .any(|i| i.rule.as_deref() == Some("D1"))
        );
        assert_eq!(sub, before);
    }
    #[test]
    fn typed_indexed_activation_wait_preserves_completed_prefix_and_clock_setup_order() {
        let mut sub = ordinary().runner_subprocess.unwrap();
        let mut set = |operation: u32, stage: u32, index: Option<u32>| {
            sub.worker_evidence.as_mut().unwrap().progress = Some(PWWorkerProgress {
                raw: (operation << 24) | (stage << 20) | index.map_or(0, |i| i + 1),
                operation,
                stage,
                index,
            });
            sub.clone()
        };
        for stage in [1, 2] {
            for first in [0, 1, 2] {
                let (answer, value, position) = progress(&set(13, stage, Some(first)), 2);
                assert_eq!((answer, value), (Some("none"), None));
                let position = position.unwrap();
                assert_eq!(position, (attempt_position(), u64::from(first), 0));
                if first > 0 {
                    assert!(position > (attempt_position(), u64::from(first - 1), 2));
                }
                assert!(position < (attempt_position(), u64::from(first), 1));
            }
        }
        assert_eq!(
            progress(&set(13, 2, Some(0)), 0),
            (Some("none"), None, Some((attempt_position(), 0, 0)))
        );
        assert_eq!(
            progress(&set(13, 1, Some(3)), 2),
            (Some("invalid"), None, None)
        );
        let mut mismatched = set(13, 1, Some(0));
        mismatched
            .worker_evidence
            .as_mut()
            .unwrap()
            .progress
            .as_mut()
            .unwrap()
            .raw = (13 << 24) | (1 << 20) | 2;
        assert_eq!(progress(&mismatched, 2), (Some("invalid"), None, None));
        let header = progress(&set(1, 2, None), 1).2.unwrap();
        let setup = progress(&set(12, 2, None), 1).2.unwrap();
        let read = progress(&set(2, 1, None), 1).2.unwrap();
        assert!(header < setup && setup < read);
        let apply = progress(&set(8, 2, None), 1).2.unwrap();
        let activation = progress(&set(13, 1, None), 1).2.unwrap();
        let proceed = progress(&set(11, 1, None), 1).2.unwrap();
        assert!(apply < activation && activation < proceed);
        assert_eq!(
            progress(&set(14, 1, None), 1),
            (None, None, None),
            "unknown native operation magnitude is not time order"
        );
    }
    #[test]
    fn typed_future_applicability_and_summary_remain_open_without_rewriting() {
        let reply = ordinary();
        let actions: Vec<_> = reply.steps.iter().map(ActionRef::Step).collect();
        let mut sub = reply.runner_subprocess.clone().unwrap();
        sub.disposition.as_mut().unwrap().steps[0]
            .questions
            .step_requested_operation_applicability
            .as_mut()
            .unwrap()
            .answer = Some("future_applicability".into());
        let before = sub.clone();
        assert!(validate_lifecycle(&sub, &actions, false).is_empty());
        assert_eq!(sub, before);
        let mut changed = reply.clone();
        changed.steps[0].attempt.lifecycle.as_mut().unwrap().summary = "future_summary".into();
        let actions: Vec<_> = changed.steps.iter().map(ActionRef::Step).collect();
        let d = project(changed.runner_subprocess.as_ref().unwrap(), &actions, false);
        assert_eq!(
            d.process_disposition, "clean_exit",
            "native final status remains independently supported: {:?}",
            d.disposition_issues
        );
        assert_eq!(
            changed.steps[0].attempt.lifecycle.as_ref().unwrap().summary,
            "future_summary"
        );
        let known = changed.steps[0].attempt.lifecycle.as_mut().unwrap();
        known.summary = "not_reached".into();
        let actions: Vec<_> = changed.steps.iter().map(ActionRef::Step).collect();
        assert!(
            !validate_lifecycle(changed.runner_subprocess.as_ref().unwrap(), &actions, false)
                .is_empty(),
            "known contradictory summary must still reject"
        );
    }
    #[test]
    fn typed_geometry_refuses_before_projection_and_retains_every_raw_record() {
        let baseline = ordinary();
        let sample_issue = PWDispositionIssue {
            kind: "conflict".into(),
            rule: "D1".into(),
            question: "final_status".into(),
            step_index: None,
            observations: vec![],
            detail: "constructed capacity cell".into(),
        };
        for mutation in [
            "steps",
            "disposition_steps",
            "issues",
            "actors",
            "phases",
            "validator_records",
            "validator_plan",
            "validator_issues",
        ] {
            let mut r = baseline.clone();
            match mutation {
                "steps" => r.steps = vec![r.steps[0].clone(); 257],
                "disposition_steps" => {
                    let d = r
                        .runner_subprocess
                        .as_mut()
                        .unwrap()
                        .disposition
                        .as_mut()
                        .unwrap();
                    d.steps = vec![d.steps[0].clone(); 257];
                }
                "issues" => {
                    r.runner_subprocess
                        .as_mut()
                        .unwrap()
                        .disposition
                        .as_mut()
                        .unwrap()
                        .issues = vec![sample_issue.clone(); 514]
                }
                "actors" => {
                    r.execution_form = Some("actors".into());
                    r.actors = Some(vec![actors().actors.unwrap().remove(0); 9]);
                }
                "phases" => r.phases = vec![r.phases[0].clone(); 9],
                "validator_records" => {
                    let v = r.phases[0].validator_subprocess.as_mut().unwrap();
                    v.records = Some(vec![v.records.as_ref().unwrap()[0].clone(); 513]);
                }
                "validator_plan" => {
                    r.phases[0]
                        .validator_subprocess
                        .as_mut()
                        .unwrap()
                        .expected_step_ids = Some(vec!["constructed".into(); 257])
                }
                "validator_issues" => {
                    r.phases[0]
                        .validator_subprocess
                        .as_mut()
                        .unwrap()
                        .association_issues = Some(vec![
                        PWValidatorAssociationIssue {
                            kind: "missing_id".into(),
                            step_id: None,
                            count: 0,
                            origin: "runner_host".into()
                        };
                        770
                    ])
                }
                _ => unreachable!(),
            }
            let before = r.clone();
            let d = execution_diagnostics(Some(&r));
            assert_eq!(d.process_disposition, "withheld", "{mutation}");
            assert_eq!(d.disposition_integrity, Some("invalid"));
            assert!(
                d.actors.is_none(),
                "overcount cannot produce per-actor claims: {mutation}"
            );
            assert_eq!(
                d.disposition_issues.len(),
                1,
                "{mutation}: {:?}",
                d.disposition_issues
            );
            assert_eq!(d.disposition_issues[0].kind, "reply_capacity");
            assert_eq!(r, before, "lost raw {mutation}");
            assert_eq!(admit_reply(&r).unwrap_err().len(), 1);
        }
        let mut boundary = baseline.clone();
        boundary.steps = vec![boundary.steps[0].clone(); 256];
        boundary.phases.clear();
        boundary
            .runner_subprocess
            .as_mut()
            .unwrap()
            .disposition
            .as_mut()
            .unwrap()
            .issues = vec![sample_issue; 513];
        assert!(
            reply_geometry(&boundary).is_none(),
            "capacity guard must not impose a smaller native geometry"
        );
        let mut sub = baseline.runner_subprocess.unwrap();
        let actions: Vec<_> = baseline.steps.iter().map(ActionRef::Step).collect();
        sub.disposition
            .as_mut()
            .unwrap()
            .questions
            .final_status
            .as_mut()
            .unwrap()
            .basis = Some(vec!["unknown_reference".into(); 1024]);
        let issues = validate_lifecycle(&sub, &actions, false);
        assert!(
            issues.len() <= 3,
            "one bad reference list must not multiply diagnostics: {issues:?}"
        );
    }
    #[test]
    fn typed_reference_geometry_is_checked_before_claims_and_admission_contexts() {
        for mutation in [
            "run_basis",
            "step_basis",
            "issue_observations",
            "lifecycle_copy",
        ] {
            let mut r = ordinary();
            match mutation {
                "run_basis" => {
                    r.runner_subprocess
                        .as_mut()
                        .unwrap()
                        .disposition
                        .as_mut()
                        .unwrap()
                        .questions
                        .final_status
                        .as_mut()
                        .unwrap()
                        .basis = Some(vec!["reaped".into(); 15])
                }
                "step_basis" => {
                    r.runner_subprocess
                        .as_mut()
                        .unwrap()
                        .disposition
                        .as_mut()
                        .unwrap()
                        .steps[0]
                        .questions
                        .step_boundary_reached
                        .as_mut()
                        .unwrap()
                        .basis = Some(vec!["slot".into(); 17])
                }
                "issue_observations" => r
                    .runner_subprocess
                    .as_mut()
                    .unwrap()
                    .disposition
                    .as_mut()
                    .unwrap()
                    .issues
                    .push(PWDispositionIssue {
                        kind: "conflict".into(),
                        rule: "D1".into(),
                        question: "final_status".into(),
                        step_index: None,
                        observations: vec!["exit_code".into(); 15],
                        detail: "constructed reference overcount".into(),
                    }),
                "lifecycle_copy" => {
                    r.steps[0]
                        .attempt
                        .lifecycle
                        .as_mut()
                        .unwrap()
                        .boundary
                        .basis = Some(vec!["slot".into(); 17])
                }
                _ => unreachable!(),
            }
            let before = r.clone();
            assert!(admission_problem(&r).is_some());
            let d = execution_diagnostics(Some(&r));
            assert_eq!(d.process_disposition, "withheld");
            assert_eq!(d.disposition_issues.len(), 1);
            assert_eq!(d.disposition_issues[0].kind, "reply_capacity");
            assert_eq!(r, before);
        }
    }
}
