//! Typed evidence admission for the porcelain experiment. Raw records remain
//! publishable when a claim fails; diagnostics never replace their native facts.
use crate::porcelain_records::*;
use serde::Serialize;
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug, Serialize, PartialEq)]
pub(crate) struct IntegrityIssue {
    pub kind: String,
    pub detail: String,
}
fn issue(out: &mut Vec<IntegrityIssue>, kind: &str, detail: impl Into<String>) {
    out.push(IntegrityIssue { kind: kind.into(), detail: detail.into() });
}
#[derive(Clone, Debug, Serialize)]
pub(crate) struct TypedRunnerExecutionDiagnostics {
    pub process_disposition: &'static str,
    pub termination_cause: Option<&'static str>,
    pub stop_reason: Option<String>,
    pub disposition_integrity: Option<&'static str>,
    pub disposition_issues: Vec<IntegrityIssue>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub actors: Option<Vec<TypedActorExecutionDiagnostics>>,
}
#[derive(Clone, Debug, Serialize)]
pub(crate) struct TypedActorExecutionDiagnostics {
    pub actor_id: Option<String>,
    pub process_disposition: &'static str,
    pub termination_cause: Option<&'static str>,
    pub stop_reason: Option<String>,
    pub disposition_integrity: Option<&'static str>,
    pub disposition_issues: Vec<IntegrityIssue>,
}

/// Question selection is a fixed field operation, never a dynamic record lookup.
#[derive(Clone, Copy, Debug, PartialEq)]
enum Question { FinalStatus, StopReason, CleanupTrigger, GraceEnd, Kill, Collection, Progress,
    Boundary, Published, Applicability }
impl Question {
    fn name(self) -> &'static str { match self {
        Self::FinalStatus => "final_status", Self::StopReason => "stop_reason",
        Self::CleanupTrigger => "cleanup_trigger", Self::GraceEnd => "grace_end",
        Self::Kill => "kill_request_and_result", Self::Collection => "collection_basis",
        Self::Progress => "progress_association", Self::Boundary => "step_boundary_reached",
        Self::Published => "step_result_published", Self::Applicability => "step_requested_operation_applicability",
    }}
    fn run(self, q: &PWDispositionRunQuestions) -> Option<&PWDispositionClaim> { match self {
        Self::FinalStatus => q.final_status.as_ref(), Self::StopReason => q.stop_reason.as_ref(),
        Self::CleanupTrigger => q.cleanup_trigger.as_ref(), Self::GraceEnd => q.grace_end.as_ref(),
        Self::Kill => q.kill_request_and_result.as_ref(), Self::Collection => q.collection_basis.as_ref(),
        Self::Progress => q.progress_association.as_ref(), _ => None,
    }}
    fn step(self, q: &PWDispositionStepQuestions) -> Option<&PWDispositionClaim> { match self {
        Self::Boundary => q.step_boundary_reached.as_ref(), Self::Published => q.step_result_published.as_ref(),
        Self::Applicability => q.step_requested_operation_applicability.as_ref(), _ => None,
    }}
}
const RUN_QUESTIONS: [Question; 7] = [Question::FinalStatus, Question::StopReason,
    Question::CleanupTrigger, Question::GraceEnd, Question::Kill, Question::Collection, Question::Progress];
const STEP_QUESTIONS: [Question; 3] = [Question::Boundary, Question::Published, Question::Applicability];
fn supported(c: Option<&PWDispositionClaim>) -> bool { c.is_some_and(|c| c.state == "supported") }
fn answer(c: Option<&PWDispositionClaim>) -> Option<&str> { c.and_then(|c| c.answer.as_deref()) }
fn integer(c: Option<&PWDispositionClaim>) -> Option<i64> {
    match c.and_then(|c| c.value.as_ref()) { Some(PWDispositionValue::Integer(n)) => Some(*n), _ => None }
}
fn cites(c: &PWDispositionClaim, token: &str) -> bool {
    c.basis.as_ref().is_some_and(|v| v.iter().any(|v| v == token))
}
fn reference_resolves(token: &str, s: &PWRunnerSubprocess, step: Option<&PWDispositionStep>) -> bool {
    match token {
        "reaped" => s.reaped.is_some(), "exit_code" => s.exit_code.is_some(),
        "term_signal" => s.term_signal.is_some(), "poll_stop_reason" => s.poll_stop_reason.is_some(),
        "exit_requested" => s.exit_requested.is_some(),
        "termination_request" => s.termination_request.is_some() || s.exit_requested.is_some(),
        "wait_errors" => s.wait_errors.is_some(), "cleanup_trigger" => s.cleanup_trigger.is_some(),
        "grace_end" => s.grace_end.is_some(), "collection_basis" => s.collection_basis.is_some(),
        "done_observed" => s.done_observed.is_some(), "plan" => true,
        "progress" => s.worker_evidence.as_ref().is_some_and(|e| e.progress.is_some()),
        "worker_failure" => s.worker_evidence.as_ref().is_some_and(|e| e.failure.is_some()),
        "slot" | "attempt_support" => step.is_some(), _ => false,
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
        (Question::Collection, _) => has(&["collection_basis", "reaped"]),
        (Question::Kill, _) => has(&["termination_request", "exit_requested"]),
        (Question::Progress, Some("step_index" | "invalid")) => has(&["progress", "plan"]),
        (Question::Progress, _) => has(&["progress"]),
        (Question::Applicability, _) => has(&["attempt_support"]),
        (Question::Boundary, Some("reached")) => has(&["progress"]) || has(&["slot", "attempt_support"]),
        (Question::Boundary, Some("not_reached")) => has(&["progress", "slot", "collection_basis"]),
        (Question::Published, Some("published")) => has(&["slot", "attempt_support"]),
        (Question::Published, Some("unpublished")) => has(&["slot", "collection_basis"]), _ => true,
    }
}
fn check_claim(q: Question, c: Option<&PWDispositionClaim>, record: &PWDispositionRecord,
    sub: &PWRunnerSubprocess, step: Option<(usize, &PWDispositionStep)>, out: &mut Vec<IntegrityIssue>) {
    let label = match step { Some((i, _)) => format!("step {i} {}", q.name()), None => q.name().into() };
    let Some(c) = c else { issue(out, "malformed_record", format!("{label}: missing claim")); return };
    match c.state.as_str() {
        "supported" => {
            if c.answer.is_none() || !c.basis.as_ref().is_some_and(|b| !b.is_empty()) || !sufficient(q, c) {
                issue(out, "invalid_claim", format!("{label}: supported claim lacks answer or sufficient basis"));
            }
            for token in c.basis.iter().flatten() {
                if !reference_resolves(token, sub, step.map(|(_, s)| s)) {
                    issue(out, "unresolved_reference", format!("{label}: {token} does not resolve"));
                }
            }
        }
        "conflicting" => {
            let expected = if q == Question::FinalStatus { &["exit_code", "term_signal"][..] }
                else { &["progress", "slot", "collection_basis"][..] };
            let valid = c.issue.and_then(|i| usize::try_from(i).ok()).and_then(|i| record.issues.get(i))
                .is_some_and(|i| i.kind == "conflict" && i.question == q.name()
                    && i.step_index == step.map(|(i, _)| i as i64)
                    && i.rule == if q == Question::FinalStatus { "D1" } else { "D5" }
                    && matches!(q, Question::FinalStatus | Question::Boundary | Question::Published)
                    && expected.iter().all(|v| i.observations.iter().any(|o| o == v))
                    && i.observations.iter().all(|v| reference_resolves(v, sub, step.map(|(_, s)| s))));
            if !valid { issue(out, "invalid_claim", format!("{label}: conflict lacks matching observations/issue")); }
        }
        "unresolved" | "inapplicable" => if c.reason.is_none() {
            issue(out, "invalid_claim", format!("{label}: state lacks reason"));
        },
        _ => issue(out, "invalid_claim", format!("{label}: unknown claim state")),
    }
}
const PROTOCOL_ORDER: [u32; 13] = [1, 12, 2, 3, 4, 5, 6, 7, 8, 13, 11, 9, 10];
type Position = (usize, u64, u32);
fn progress(sub: &PWRunnerSubprocess, count: usize) -> (Option<&'static str>, Option<i64>, Option<Position>) {
    let Some(p) = sub.worker_evidence.as_ref().and_then(|e| e.progress.as_ref()) else { return (None, None, None) };
    let Some(order) = PROTOCOL_ORDER.iter().position(|o| *o == p.operation) else { return (None, None, None) };
    if !matches!(p.stage, 1 | 2) { return (None, None, None); }
    let phase = matches!(p.operation, 11 | 13) && p.index.is_some();
    let indexed = matches!(p.operation, 4 | 9) || phase;
    if indexed != p.index.is_some() || p.index.is_some_and(|i| i >= 0xfffff
        || (p.operation == 9 && i as usize >= count) || (phase && i as usize > count))
        || p.raw != ((p.operation << 24) | (p.stage << 20) | p.index.map_or(0, |i| i + 1)) {
        return (Some("invalid"), None, None);
    }
    if phase { return (Some("none"), None, Some((10, u64::from(p.index.unwrap()), 0))); }
    (Some(if p.operation == 9 { "step_index" } else if p.operation == 4 { "parameter_index" } else { "none" }),
        p.index.map(i64::from), Some((order, u64::from(p.index.unwrap_or(0)), p.stage)))
}
#[derive(Clone, Copy)]
enum ActionRef<'a> { Step(&'a PWRunnerStepResult), Event(&'a PWRunnerExtensionEvent) }
impl<'a> ActionRef<'a> {
    fn id(self) -> &'a str { match self { Self::Step(s) => &s.step_id, Self::Event(e) => &e.step_id } }
    fn lifecycle(self) -> Option<&'a PWAttemptLifecycle> { match self {
        Self::Step(s) => s.attempt.lifecycle.as_ref(), Self::Event(e) => e.lifecycle.as_ref(),
    }}
}
fn lifecycle_summary(s: &PWDispositionStep) -> &'static str {
    let b = s.questions.step_boundary_reached.as_ref(); let r = s.questions.step_result_published.as_ref();
    if b.is_some_and(|c| c.state == "conflicting") || r.is_some_and(|c| c.state == "conflicting") { "conflicting" }
    else if s.attempt_support == "unsupported" { "unsupported" }
    else if supported(r) && answer(r) == Some("published") { "completed" }
    else if supported(b) && answer(b) == Some("not_reached") { "not_reached" }
    else if supported(b) && answer(b) == Some("reached") { "started_without_result" }
    else { "unresolved" }
}
fn validate_lifecycle(sub: &PWRunnerSubprocess, actions: &[ActionRef<'_>], reporting_failed: bool) -> Vec<IntegrityIssue> {
    let mut out = Vec::new();
    let Some(record) = sub.disposition.as_ref() else {
        issue(&mut out, "missing_record", "worker subprocess requires disposition"); return out;
    };
    for q in RUN_QUESTIONS { check_claim(q, q.run(&record.questions), record, sub, None, &mut out); }
    let q = &record.questions;
    let reaped = sub.reaped == Some(true);
    if sub.collection_basis.as_deref() == Some("after_confirmed_reap") && !reaped {
        issue(&mut out, "invalid_claim", "terminal collection without confirmed reap");
    }
    for question in [Question::CleanupTrigger, Question::GraceEnd, Question::Kill] {
        if supported(question.run(q)) && sub.exit_requested == Some(false) {
            issue(&mut out, "invalid_claim", "cleanup claim without exit request");
        }
    }
    let final_status = q.final_status.as_ref();
    let contradiction = if supported(final_status) { match answer(final_status) {
        Some("signal") => !reaped || sub.term_signal.is_none() || sub.exit_code.is_some() || integer(final_status) != sub.term_signal,
        Some("exit_code") => !reaped || sub.exit_code.is_none() || sub.term_signal.is_some() || integer(final_status) != sub.exit_code,
        _ => false,
    }} else { final_status.is_some_and(|c| c.state == "conflicting") && (!reaped || sub.exit_code.is_none() || sub.term_signal.is_none()) };
    if contradiction { issue(&mut out, "invalid_claim", "final_status contradicts reaped status"); }
    for (c, fact) in [(q.stop_reason.as_ref(), sub.poll_stop_reason.as_deref()),
        (q.cleanup_trigger.as_ref(), sub.cleanup_trigger.as_deref()), (q.grace_end.as_ref(), sub.grace_end.as_deref()),
        (q.collection_basis.as_ref(), sub.collection_basis.as_deref())] {
        if supported(c) && answer(c) != fact { issue(&mut out, "invalid_claim", "claim contradicts recorded host fact"); }
    }
    if let Some(c) = q.kill_request_and_result.as_ref().filter(|c| c.state == "supported") {
        let valid = match c.answer.as_deref() {
            Some("requested") => match (&c.value, &sub.termination_request) {
                (Some(PWDispositionValue::Request(a)), Some(b)) => a == b, _ => false,
            }, Some("none") => sub.termination_request.is_none(), _ => true,
        };
        if !valid { issue(&mut out, "invalid_claim", "kill claim contradicts termination request"); }
    }
    let (association, index, position) = progress(sub, record.steps.len());
    if supported(q.progress_association.as_ref()) && (answer(q.progress_association.as_ref()) != association
        || integer(q.progress_association.as_ref()) != index) {
        issue(&mut out, "invalid_claim", "progress claim contradicts encoded progress");
    }
    if record.steps.len() != actions.len() { issue(&mut out, "invalid_claim", "disposition/action count mismatch"); }
    if sub.partial_steps != record.steps.iter().any(|s| s.slot != "completed") {
        issue(&mut out, "invalid_claim", "partial_steps contradicts record slots");
    }
    let terminal = reaped && sub.collection_basis.as_deref() == Some("after_confirmed_reap");
    for (i, s) in record.steps.iter().enumerate() {
        for question in STEP_QUESTIONS { check_claim(question, question.step(&s.questions), record, sub, Some((i, s)), &mut out); }
        if s.index != i as i64 || !matches!(s.slot.as_str(), "completed" | "incomplete" | "absent")
            || !matches!(s.attempt_support.as_str(), "supported" | "unsupported") {
            issue(&mut out, "malformed_record", format!("step {i}: identity/slot/support invalid"));
        }
        let Some(action) = actions.get(i).copied() else { continue };
        if s.step_id != action.id() { issue(&mut out, "invalid_claim", format!("step {i}: action identity mismatch")); }
        let completed = s.slot == "completed" && s.attempt_support == "supported";
        let reached = position.is_some_and(|p| p >= (10, i as u64, 1));
        let returned = position.is_some_and(|p| p >= (10, i as u64, 2));
        let boundary_conflict = terminal && position.is_some() && !reached && s.slot == "completed";
        let result_conflict = terminal && returned && s.slot == "incomplete" && s.attempt_support == "supported";
        let b = s.questions.step_boundary_reached.as_ref(); let r = s.questions.step_result_published.as_ref();
        let a = s.questions.step_requested_operation_applicability.as_ref();
        if supported(a) && answer(a) != Some(s.attempt_support.as_str()) {
            issue(&mut out, "invalid_claim", "applicability contradicts support");
        }
        if supported(r) && ((answer(r) == Some("published") && !completed)
            || (answer(r) == Some("unpublished") && (s.slot != "incomplete" || !terminal || s.attempt_support != "supported" || result_conflict))) {
            issue(&mut out, "invalid_claim", "result publication contradicts slot/collection");
        }
        if let Some(b) = b {
            let witness = (reached && cites(b, "progress")) || (completed && cites(b, "slot") && cites(b, "attempt_support"));
            if b.state == "supported" && ((b.answer.as_deref() == Some("reached") && (boundary_conflict || !witness))
                || (b.answer.as_deref() == Some("not_reached") && (!terminal || s.slot == "completed" || position.is_none() || reached))) {
                issue(&mut out, "invalid_claim", "boundary lacks unopposed witness");
            }
            if b.state == "conflicting" && !boundary_conflict { issue(&mut out, "invalid_claim", "boundary conflict lacks incompatible observations"); }
        }
        if r.is_some_and(|r| r.state == "conflicting") && !result_conflict {
            issue(&mut out, "invalid_claim", "result conflict lacks incompatible observations");
        }
        let reason = if completed { None } else if s.attempt_support != "supported" { Some("attempt_not_supported") }
            else if s.slot == "absent" { Some("slot_absent") } else { Some("slot_incomplete") };
        match action {
            ActionRef::Step(step) => {
                if step.attempt.result_source.as_deref() != Some(if completed { "worker" } else { "synthetic" })
                    || step.attempt.missing_reason.as_deref() != reason {
                    issue(&mut out, "invalid_claim", "attempt compatibility projection contradicts lifecycle");
                }
                let expected = match lifecycle_summary(s) { "completed" => None, "unresolved" => Some("attempt:lifecycle_unresolved"),
                    "conflicting" => Some("attempt:lifecycle_conflicting"), "unsupported" => Some("attempt:unsupported"),
                    "not_reached" => Some("attempt:not_reached"), _ => Some("attempt:started_without_result") };
                let actual: Vec<&str> = step.comparison.iter().flat_map(|c| &c.limitations).map(String::as_str)
                    .filter(|l| l.starts_with("attempt:")).collect();
                if !(reporting_failed && step.comparison.is_none()) && actual != expected.into_iter().collect::<Vec<_>>() {
                    issue(&mut out, "invalid_claim", "comparison lifecycle limitations disagree");
                }
            }
            ActionRef::Event(e) => {
                if e.result_published != completed { issue(&mut out, "invalid_claim", "event publication contradicts lifecycle"); }
                let valid = if e.operation == "transfer" {
                    !e.call_boundary_observed && e.native_result.is_none() && e.errno.is_none() && e.unavailable_reason.is_none()
                } else { match e.status.as_str() {
                    "returned" => completed && e.call_boundary_observed && e.native_result.is_some() && e.errno.is_some() && e.unavailable_reason.is_none(),
                    "unavailable" => completed && !e.call_boundary_observed && e.native_result.is_none() && e.errno.is_none() && e.unavailable_reason.is_some(),
                    "unresolved" => !completed && e.native_result.is_none() && e.errno.is_none() && e.unavailable_reason.is_none(), _ => false,
                }};
                if !valid { issue(&mut out, "invalid_claim", "event native publication is inconsistent"); }
            }
        }
        if let Some(l) = action.lifecycle() {
            if Some(&l.boundary) != b || Some(&l.result) != r || l.summary != lifecycle_summary(s) {
                issue(&mut out, "invalid_claim", "lifecycle projection disagrees with canonical record");
            }
        } else { issue(&mut out, "invalid_claim", "action lacks lifecycle projection"); }
    }
    for (i, _) in record.issues.iter().enumerate() {
        let used = RUN_QUESTIONS.iter().filter_map(|q| q.run(&record.questions))
            .chain(record.steps.iter().flat_map(|s| STEP_QUESTIONS.iter().filter_map(|q| q.step(&s.questions))))
            .any(|c| c.state == "conflicting" && c.issue == Some(i as i64));
        if !used { issue(&mut out, "invalid_claim", format!("issue {i} is unreferenced")); }
    }
    out
}

fn filter_type(kind: &str) -> &str { match kind {
    "none" => "NONE", "path" => "PATH", "global_name" => "GLOBAL_NAME", "local_name" => "LOCAL_NAME",
    "iokit_registry_entry_class" => "IOKIT_REGISTRY_ENTRY_CLASS", "iokit_user_client_class" => "IOKIT_USER_CLIENT_CLASS",
    "sysctl_name" => "SYSCTL_NAME", other => other,
}}
fn query_matches(record: &ValidatorVerdict, step: &PWRunnerStepResult) -> bool {
    let q = &step.sandbox_check;
    record.operation.as_deref() == Some(q.operation.as_str())
        && record.filter_type.as_deref() == Some(filter_type(&q.filter_kind))
        && record.filter_value.as_deref() == if q.filter_kind == "none" { None } else { q.filter_value.as_deref() }
}
fn phase_issues(reply: &PWRunnerRunResult, out: &mut Vec<IntegrityIssue>) {
    let mut phase_ids = BTreeSet::new(); let mut action_ids = BTreeSet::new();
    let events = reply.extension_events.as_deref().unwrap_or(&[]);
    let mut all = BTreeSet::new();
    for id in reply.steps.iter().map(|s| &s.step_id).chain(events.iter().map(|e| &e.step_id)) {
        if !all.insert(id) { issue(out, "phase_collection", "duplicate action identity"); }
    }
    for (i, p) in reply.phases.iter().enumerate() {
        if p.ordinal != i as i64 + 1 || !phase_ids.insert(&p.phase_id)
            || p.action_ids.iter().any(|id| !action_ids.insert(id)) {
            issue(out, "phase_collection", "phase ordinal/partition identity conflict");
        }
        let disposition = p.ordering.as_ref().map(|o| o.validator_disposition.as_str());
        let valid = match p.collection_status.as_str() {
            "not_reached" => matches!(disposition, None | Some("not_invoked")),
            "not_needed" => disposition == Some("not_needed"),
            "collected" => matches!(disposition, Some("not_spawned" | "reaped" | "unconfirmed")),
            "budget_exhausted" => disposition == Some("not_spawned"),
            "clock_unavailable" => matches!(disposition, Some("not_needed" | "not_spawned")), _ => false,
        };
        let observations = if p.collection_status != "collected" {
            p.validator_subprocess.is_none() && p.validator_spawn_failure.is_none()
        } else if disposition == Some("not_spawned") { p.validator_subprocess.is_none() }
        else { p.validator_spawn_failure.is_none() && p.validator_subprocess.as_ref()
            .is_some_and(|v| v.reaped == Some(disposition == Some("reaped"))) };
        if !valid || !observations { issue(out, "phase_collection", "collection status contradicts validator evidence"); }
        if p.completion_observed && (!p.arrival_observed || !p.ordering.as_ref().is_some_and(|o| o.proceed_observed)) {
            issue(out, "phase_collection", "completion lacks arrival and observed proceed");
        }
        let Some(v) = p.validator_subprocess.as_ref() else { continue };
        let eligible: Vec<_> = reply.steps.iter().filter(|s| s.phase_id == p.phase_id
            && s.sandbox_check.missing_reason.as_deref() != Some("query_not_requested")).collect();
        let expected: BTreeSet<_> = eligible.iter().map(|s| &s.step_id).collect();
        let declared = v.expected_step_ids.as_ref();
        if v.phase_id.as_deref() != Some(p.phase_id.as_str()) || v.ordinal != Some(p.ordinal)
            || declared.is_none_or(|d| d.len() != expected.len() || d.iter().collect::<BTreeSet<_>>() != expected) {
            issue(out, "phase_collection", "validator owner or expected query plan mismatch");
        }
        let (Some(records), Some(observed)) = (&v.records, &v.association_issues) else {
            issue(out, "phase_collection", "validator collection lacks records or association issues"); continue;
        };
        let mut implied: Vec<(String, Option<String>, i64)> = Vec::new();
        let mut groups: BTreeMap<&str, Vec<&ValidatorVerdict>> = BTreeMap::new();
        for r in records { if let Some(id) = r.step_id.as_deref() { groups.entry(id).or_default().push(r); } }
        for s in &eligible {
            let matches = groups.get(s.step_id.as_str()).map(Vec::as_slice).unwrap_or(&[]);
            if matches.len() != 1 {
                implied.push((if matches.is_empty() { "missing_id" } else { "duplicate_id" }.into(), Some(s.step_id.clone()), matches.len() as i64));
            } else {
                let r = matches[0]; let prediction = matches!(r.outcome.as_str(), "allow" | "deny");
                let q = &s.sandbox_check;
                let mismatch = ((prediction || r.operation.is_some()) && r.operation.as_deref() != Some(q.operation.as_str()))
                    || ((prediction || r.filter_type.is_some()) && r.filter_type.as_deref() != Some(filter_type(&q.filter_kind)))
                    || ((prediction || r.filter_value.is_some()) && r.filter_value.as_deref()
                        != if q.filter_kind == "none" { None } else { q.filter_value.as_deref() });
                if mismatch { implied.push(("query_mismatch".into(), Some(s.step_id.clone()), 1)); }
            }
        }
        for (id, rows) in groups { if !expected.iter().any(|s| s.as_str() == id) {
            implied.push(("unexpected_id".into(), Some(id.into()), rows.len() as i64));
        }}
        let unassociated = records.iter().filter(|r| r.step_id.is_none()).count();
        if unassociated != 0 { implied.push(("unassociated".into(), None, unassociated as i64)); }
        implied.sort();
        let mut observed: Vec<_> = observed.iter().map(|i| (i.kind.clone(), i.step_id.clone(), i.count)).collect(); observed.sort();
        if observed != implied { issue(out, "phase_collection", "validator association issues disagree with records"); }
    }
    if reply.preparation_failure.is_none() && all != action_ids { issue(out, "phase_collection", "phase actions do not partition reply"); }
    let ordered: Vec<_> = reply.phases.iter().flat_map(|p| &p.action_ids).collect();
    if ordered.iter().copied().filter(|id| reply.steps.iter().any(|s| &s.step_id == *id)).collect::<Vec<_>>()
        != reply.steps.iter().map(|s| &s.step_id).collect::<Vec<_>>() {
        issue(out, "phase_collection", "step array order disagrees with phase plan");
    }
    for s in &reply.steps {
        let Some(p) = reply.phases.iter().find(|p| p.phase_id == s.phase_id && p.action_ids.contains(&s.step_id)) else {
            issue(out, "ordering", "step lacks its phase association"); continue;
        };
        let actor = reply.actors.iter().flatten().find(|a| Some(&a.actor_id) == s.actor_id.as_ref());
        let (established, pid) = if reply.execution_form.as_deref() == Some("actors") {
            if p.actor_id != s.actor_id || actor.is_none() { issue(out, "ordering", "step actor differs from phase actor"); }
            (actor.is_some_and(|a| matches!(a.setup_status.as_str(), "applied" | "unapplied_declared")),
                actor.and_then(|a| a.launch.as_ref()).map(|l| l.pid))
        } else { (reply.sandboxed_after_apply == Some(true), reply.runner_subprocess.as_ref().map(|s| s.pid)) };
        let Some(c) = s.comparison.as_ref() else { issue(out, "ordering", "ordinary reply step lacks comparison"); continue };
        if !matches!(c.order.as_str(), "query_first" | "unestablished") { issue(out, "ordering", "unknown comparison order"); }
        if c.order != "query_first" { continue; }
        let q = &s.sandbox_check;
        let chain = p.ordering.as_ref().is_some_and(|o| o.collection_closed_before_proceed && o.proceed_set
            && o.proceed_observed && o.worker_lifetime_established && o.protocol_violations.is_empty());
        let matches: Vec<_> = p.validator_subprocess.as_ref().and_then(|v| v.records.as_ref()).into_iter().flatten()
            .filter(|r| r.step_id.as_deref() == Some(s.step_id.as_str())).collect();
        let native = q.result_source.as_deref() == Some("validator") && q.native_rc == Some(q.rc) && q.errno.is_some()
            && ((q.outcome == "allow" && q.rc == 0) || (q.outcome == "deny" && q.rc == 1 && q.errno == Some(0)));
        if !chain || !established || pid.is_none() || q.pid != pid || !native || matches.len() != 1
            || !matches.first().is_some_and(|r| query_matches(r, s) && r.rc == q.native_rc && r.errno == q.errno && r.outcome == q.outcome) {
            issue(out, "ordering", "query_first lacks eligible prediction and complete ordering chain");
        }
    }
}

pub(crate) fn admission_problem(reply: &PWRunnerRunResult) -> Option<String> {
    if reply.schema_version != i64::from(crate::json_contract::RESPONSE_SCHEMA_VERSION) {
        return Some(format!("unsupported response schema {}", reply.schema_version));
    }
    if let Some(c) = &reply.compiled_profile {
        if c.schema_version != 2 || !matches!(c.status.as_str(), "captured" | "unavailable") {
            return Some("unsupported or malformed compiled_profile".into());
        }
        if (c.status == "captured" && (c.producer.as_deref() != Some("worker") || c.capture_stage.as_deref() != Some("before_apply")))
            || (c.status == "unavailable" && (c.producer.is_some() || c.capture_stage.is_some())) {
            return Some("compiled_profile context is inconsistent".into());
        }
    }
    None
}
fn no_worker() -> TypedActorExecutionDiagnostics {
    TypedActorExecutionDiagnostics { actor_id: None, process_disposition: "no_worker", termination_cause: None,
        stop_reason: None, disposition_integrity: None, disposition_issues: Vec::new() }
}
fn project(sub: &PWRunnerSubprocess, actions: &[ActionRef<'_>], degraded: bool) -> TypedActorExecutionDiagnostics {
    let mut out = no_worker(); out.disposition_issues = validate_lifecycle(sub, actions, degraded);
    if !out.disposition_issues.is_empty() {
        out.process_disposition = "withheld"; out.termination_cause = Some("unknown"); out.disposition_integrity = Some("invalid"); return out;
    }
    let q = &sub.disposition.as_ref().expect("validated record").questions;
    let c = q.final_status.as_ref().expect("validated claim");
    out.process_disposition = match (c.state.as_str(), c.answer.as_deref()) {
        ("supported", Some("signal")) => "signaled",
        ("supported", Some("exit_code")) => if integer(Some(c)) == Some(0) { "clean_exit" } else { "nonzero_exit" },
        ("conflicting", _) => "conflicting", ("unresolved" | "inapplicable", _) => "unconfirmed", _ => "unrecognized",
    };
    out.termination_cause = if out.process_disposition == "clean_exit" { None } else { Some("unknown") };
    if out.process_disposition == "signaled" && supported(q.cleanup_trigger.as_ref())
        && supported(q.grace_end.as_ref()) && answer(q.grace_end.as_ref()) == Some("exhausted")
        && supported(q.kill_request_and_result.as_ref()) && answer(q.kill_request_and_result.as_ref()) == Some("requested") {
        if let Some(PWDispositionValue::Request(r)) = q.kill_request_and_result.as_ref().and_then(|c| c.value.as_ref()) {
            if r.rc == 0 && Some(i64::from(r.signal)) == integer(Some(c)) {
                out.termination_cause = match answer(q.cleanup_trigger.as_ref()) {
                    Some("deadline_expiry") => Some("host_sentinel_deadline"), Some("completion") => Some("host_exit_grace_exhausted"),
                    Some("poll_wait_error") => Some("host_cleanup_after_wait_error"), Some("policy_transfer_error") => Some("host_cleanup_after_transfer_error"),
                    Some("policy_transfer_timeout") => Some("host_cleanup_after_transfer_timeout"), _ => Some("unknown"),
                };
            }
        }
    }
    out.stop_reason = q.stop_reason.as_ref().filter(|c| c.state == "supported").and_then(|c| c.answer.clone());
    out.disposition_integrity = Some("valid");
    for i in &sub.disposition.as_ref().unwrap().issues { issue(&mut out.disposition_issues, &i.kind, i.detail.clone()); }
    out
}

/// The selected slice's checks. Remaining validators are named explicitly and
/// withhold aggregate certification; their observations are still exported.
pub(crate) fn admit_reply(reply: &PWRunnerRunResult) -> Result<(), Vec<IntegrityIssue>> {
    let mut out = Vec::new();
    if let Some(problem) = admission_problem(reply) { issue(&mut out, "reply_admission", problem); }
    if let Some(f) = &reply.reporting_failure {
        if reply.normalized_outcome != "runner_reporting_failed" || reply.rc != 1 || reply.error.as_ref().is_none_or(String::is_empty)
            || f.origin != "runner_host" || f.diagnostic.is_empty() || f.original_normalized_outcome.is_empty()
            || reply.steps.iter().any(|s| s.comparison.is_some())
            || (!f.evidence_retained && (!reply.steps.is_empty() || reply.runner_subprocess.is_some() || !reply.phases.is_empty())) {
            issue(&mut out, "reporting_failure", "degraded reply lacks diagnostics or retains comparison claims");
        }
    } else {
        if reply.normalized_outcome == "runner_reporting_failed" { issue(&mut out, "reporting_failure", "reporting outcome lacks failure evidence"); }
        phase_issues(reply, &mut out);
        // These records are typed and retained, but their independent native
        // consistency rules have not been migrated by the selected experiment.
        for s in &reply.steps {
            if s.attempt.exec_observation.is_some() || s.attempt.fresh_read.is_some() || s.attempt.fresh_write.is_some() {
                issue(&mut out, "unconverted_scope", "exec/fresh-I/O semantic validation remains outside the typed slice");
            }
        }
        if reply.execution_form.as_deref() == Some("actors") {
            actor_associations(reply, &mut out);
            issue(&mut out, "unconverted_scope", "equipment/plist, authority-setup, application and full resource settlement validators remain unconverted");
        }
    }
    if out.is_empty() { Ok(()) } else { Err(out) }
}
fn actor_associations(reply: &PWRunnerRunResult, out: &mut Vec<IntegrityIssue>) {
    let actors = reply.actors.as_deref().unwrap_or(&[]); let events = reply.extension_events.as_deref().unwrap_or(&[]);
    let mut ids = BTreeSet::new();
    for (i, a) in actors.iter().enumerate() {
        if a.index != i as i64 || !ids.insert(a.actor_id.as_str()) { issue(out, "actor_evidence", "actor index or identity conflict"); }
        if let (Some(l), Some(s)) = (&a.launch, &a.subprocess) {
            if l.pid != s.pid { issue(out, "actor_evidence", "launch and subprocess identify different PIDs"); }
        }
        let visits: Vec<_> = reply.phases.iter().enumerate().filter(|(_, p)| p.actor_id.as_deref() == Some(a.actor_id.as_str()))
            .map(|(i, _)| i as i64 + 1).collect();
        if a.visits != visits { issue(out, "actor_evidence", "actor visits disagree with schedule"); }
    }
    for p in &reply.phases {
        if !p.actor_id.as_deref().is_some_and(|id| ids.contains(id)) { issue(out, "actor_evidence", "phase actor is absent"); }
    }
    for e in events {
        if !e.actor_id.as_deref().is_some_and(|id| ids.contains(id)) || !reply.phases.iter().any(|p| p.phase_id == e.phase_id && p.actor_id == e.actor_id && p.action_ids.contains(&e.step_id)) {
            issue(out, "actor_evidence", "event actor/phase association conflict");
        }
    }
    for t in reply.transfers.iter().flatten() {
        if !ids.contains(t.source_actor_id.as_str()) || !ids.contains(t.recipient_actor_id.as_str())
            || !events.iter().any(|e| e.step_id == t.step_id && e.phase_id == t.phase_id && e.operation == "transfer"
                && e.actor_id.as_deref() == Some(t.source_actor_id.as_str()) && e.token_ref.as_deref() == Some(t.token_ref.as_str())
                && e.delivery_ref.as_deref() == Some(t.delivery_ref.as_str())) {
            issue(out, "actor_evidence", "transfer lacks matching source event and actors");
        }
    }
}

pub(crate) fn execution_diagnostics(reply: Option<&PWRunnerRunResult>) -> TypedRunnerExecutionDiagnostics {
    let mut result = TypedRunnerExecutionDiagnostics { process_disposition: "no_worker", termination_cause: None,
        stop_reason: None, disposition_integrity: None, disposition_issues: Vec::new(), actors: None };
    let Some(reply) = reply else { return result };
    let degraded = reply.reporting_failure.is_some();
    if reply.execution_form.as_deref() == Some("actors") {
        let mut actors = Vec::new();
        for actor in reply.actors.iter().flatten() {
            let actions: Vec<_> = reply.phases.iter().filter(|p| p.actor_id.as_deref() == Some(actor.actor_id.as_str()))
                .flat_map(|p| &p.action_ids).filter_map(|id| {
                    reply.steps.iter().find(|s| &s.step_id == id).map(ActionRef::Step)
                        .or_else(|| reply.extension_events.iter().flatten().find(|e| &e.step_id == id).map(ActionRef::Event))
                }).collect();
            let mut d = actor.subprocess.as_ref().map(|s| project(s, &actions, degraded)).unwrap_or_else(no_worker);
            d.actor_id = Some(actor.actor_id.clone()); actors.push(d);
        }
        if actors.iter().any(|a| a.process_disposition != "no_worker") {
            result.process_disposition = "per_actor";
            result.disposition_integrity = Some(if actors.iter().all(|a| a.disposition_integrity.is_none_or(|v| v == "valid")) { "valid" } else { "invalid" });
        }
        result.actors = Some(actors);
    } else if let Some(sub) = reply.runner_subprocess.as_ref() {
        let actions: Vec<_> = reply.steps.iter().map(ActionRef::Step).collect();
        let d = project(sub, &actions, degraded);
        result.process_disposition = d.process_disposition; result.termination_cause = d.termination_cause;
        result.stop_reason = d.stop_reason; result.disposition_integrity = d.disposition_integrity;
        result.disposition_issues = d.disposition_issues;
    }
    if let Err(mut issues) = admit_reply(reply) {
        result.process_disposition = "withheld"; result.termination_cause = Some("unknown"); result.disposition_integrity = Some("invalid");
        result.disposition_issues.append(&mut issues);
    }
    result
}
