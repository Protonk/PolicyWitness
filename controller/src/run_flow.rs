//! Orchestrates a single run and builds the JSON envelope.
//!
//! The controller reads the request, selects a runner, invokes the Swift client,
//! and attaches best-effort evidence (sandbox logs, cross-check results).
//!
//! Published legacy preparation/application failures are runner_failed: the
//! existing worker payload cannot distinguish the failed native operation.
//! Fallback sbpl-check reports only its own compilation, not missing worker
//! progress or the cause of a lost reply. Unified-log capture is optional.

use serde::Serialize;
use serde_json::Value;
use serde_json::json;
use std::ffi::OsString;
use std::path::Path;

use crate::app_layout::app_root_from_current_exe;
use crate::augments::{AugmentResolution, PolicyAugmentation, resolve_augments};
use crate::cli;
use crate::evidence;
use crate::json_contract;
use crate::log_capture::LogTimeout;
use crate::policy_check::{PolicyCheckCapture, run_policy_check};
use crate::request_patch::{read_json_file, write_temp_request};
use crate::runner_client::{RunnerClientRun, run_pw_runner_client};
use crate::runner_manager::RunnerKind;
use crate::runner_select::{
    RunnerProvenance, parse_runner_selector_value, resolve_runner_target,
    runner_provenance_from_target,
};
use crate::sandbox_log::{
    SandboxLogCapture, SandboxLogWindow, bounded_step_denies, capture_sandbox_logs_with_timeout,
    worker_pid,
};
use crate::utils::now_unix_ms;

pub const DEFAULT_TIMEOUT_MS: u64 = 240_000;

#[derive(Serialize)]
pub struct AppProvenance {
    pub app_bundle_id: Option<String>,
    pub app_binary_rel_path: Option<String>,
    pub app_entitlements: Option<Value>,
    pub evidence_manifest_path: String,
    pub evidence_notes: Option<Vec<String>>,
    pub evidence_verify: Option<evidence::VerifyReport>,
}

#[derive(Serialize)]
struct ExecutionData {
    pub request_path: String,
    pub runner_service_bundle_id: String,
    pub runner_service_executable: String,
    pub runner_service_name: String,
    pub runner_registry_id: Option<String>,
    pub runner_provenance: RunnerProvenance,
    pub app_provenance: Option<AppProvenance>,
    pub policy_augmentation: Option<PolicyAugmentation>,
    pub policy_check: Option<PolicyCheckCapture>,
    pub timeout_ms: u64,
    pub runner_client: RunnerClientRun,
    pub runner_result: Option<Value>,
    pub runner_startup_diagnostics: Option<RunnerStartupDiagnostics>,
}

#[derive(Serialize)]
struct RunData {
    #[serde(flatten)]
    execution: ExecutionData,
    sandbox_log_capture: Option<SandboxLogCapture>,
    runner_sandbox_diagnostics: Option<RunnerSandboxDiagnostics>,
}

// Completed before any optional collector runs. Log processing only borrows
// runner evidence and returns LogEvidence; it cannot rewrite this value.
struct CompletedExecution {
    data: ExecutionData,
    diagnostics: RunnerExecutionDiagnostics,
    result: json_contract::JsonResult,
    exit_code: i32,
}

struct LogEvidence {
    capture: Option<SandboxLogCapture>,
    diagnostics: RunnerLogDiagnostics,
}

#[derive(Serialize)]
struct RunnerSandboxDiagnostics {
    #[serde(flatten)]
    execution: RunnerExecutionDiagnostics,
    #[serde(flatten)]
    logs: RunnerLogDiagnostics,
}

#[derive(Serialize)]
struct RunnerExecutionDiagnostics {
    pub worker_pid: Option<i32>,
    pub process_disposition: &'static str,
    pub termination_cause: Option<&'static str>,
    /// Projection of the worker disposition record's stop reason; null for a
    /// legacy reply or an unresolved question.
    pub stop_reason: Option<String>,
    /// `valid`, `invalid` (claims withheld) or `not_reported` (legacy reply).
    pub disposition_integrity: Option<&'static str>,
    /// Integrity issues plus the record's own reported conflicts; empty when none.
    pub disposition_issues: Vec<Value>,
}

#[derive(Serialize)]
struct RunnerLogDiagnostics {
    pub capture_status: String,
    pub correlation_status: &'static str,
    /// First PID match in the capture array, not the first event in time or a
    /// cause of termination. Reference keeps the event in observer evidence.
    pub first_deny: Option<DenyEventReference>,
    /// Step IDs whose attempt the runner itself classified as a permission-shaped
    /// failure and that no captured event names as a candidate. Beside
    /// `no_match` a non-empty list means the log holds no record of denials the
    /// attempts reported, not that nothing was denied; it never says why. Null
    /// when correlation was not possible or the reply carries no per-step
    /// comparison.
    pub permission_failures_without_record: Option<Vec<String>>,
}

#[derive(Serialize)]
pub struct DenyEventReference {
    pub event_index: usize,
}

#[derive(Serialize)]
pub struct RunnerStartupDiagnostics {
    pub status: String,
    pub note: String,
    pub xpc_error: Option<String>,
    pub policy_check_status: Option<String>,
}

fn load_app_provenance(app_root: &Path) -> Result<AppProvenance, String> {
    let manifest_path = evidence::manifest_path_from_app_root(app_root);
    let manifest = evidence::load_manifest(&manifest_path)
        .map_err(|e| format!("failed to read evidence manifest: {e}"))?;
    let verify = match std::env::var("PW_VERIFY_EVIDENCE").ok().as_deref() {
        Some("1") => Some(evidence::verify_manifest(
            &manifest,
            app_root,
            &manifest_path,
        )),
        _ => None,
    };
    Ok(AppProvenance {
        app_bundle_id: manifest.app_bundle_id,
        app_binary_rel_path: manifest.app_binary_rel_path,
        app_entitlements: manifest.app_entitlements,
        evidence_manifest_path: manifest_path.display().to_string(),
        evidence_notes: manifest.notes,
        evidence_verify: verify,
    })
}

fn fallback_policy_note(check: &PolicyCheckCapture) -> String {
    let detail = if check.status == "policy_too_large" {
        "sbpl-check admission refused: policy_too_large"
    } else {
        match check.compiled {
            Some(true) => "sbpl-check compiled ok",
            Some(false) => "sbpl-check compilation failed",
            None => "sbpl-check compilation unavailable",
        }
    };
    format!(
        "runner did not reply; worker progress and cause unavailable; sbpl-check describes only the fallback helper ({detail})"
    )
}

fn synthetic_runner_client(note: &str) -> RunnerClientRun {
    let now = now_unix_ms();
    RunnerClientRun {
        argv: vec!["(runner not invoked)".to_string()],
        started_at_unix_ms: now,
        ended_at_unix_ms: now,
        exit_code: 2,
        output: crate::utils::JsonOutputCapture::unavailable(
            note.to_string(),
            crate::utils::RUNNER_CAPTURE_BYTES,
        ),
    }
}

pub fn cmd_run(args: &[OsString]) -> Result<i32, String> {
    let mut request_path: Option<std::path::PathBuf> = None;
    let mut timeout_ms = DEFAULT_TIMEOUT_MS;
    let mut runner_mode_arg: Option<String> = None;
    let mut no_log_capture = false;
    let mut log_timeout = LogTimeout::default();

    let mut idx = 0usize;
    while idx < args.len() {
        let arg = args[idx].to_string_lossy();
        if arg == "--" {
            break;
        }
        if !arg.starts_with('-') {
            request_path = Some(std::path::PathBuf::from(args[idx].clone()));
            idx += 1;
            continue;
        }
        match arg.as_ref() {
            "-h" | "--help" => {
                cli::print_usage();
                return Ok(0);
            }
            "--timeout-ms" => {
                let value = args
                    .get(idx + 1)
                    .and_then(|s| s.to_string_lossy().parse::<u64>().ok())
                    .ok_or_else(|| "invalid value for --timeout-ms".to_string())?;
                timeout_ms = value.max(1);
                idx += 2;
            }
            "--log-timeout-ms" => {
                let value = args
                    .get(idx + 1)
                    .and_then(|s| s.to_str())
                    .ok_or_else(|| "missing value for --log-timeout-ms".to_string())?;
                log_timeout = LogTimeout::parse(value)?;
                idx += 2;
            }
            "--runner-mode" => {
                let value = args
                    .get(idx + 1)
                    .and_then(|s| s.to_str())
                    .ok_or_else(|| "missing value for --runner-mode".to_string())?;
                runner_mode_arg = Some(value.to_string());
                idx += 2;
            }
            "--no-log-capture" => {
                no_log_capture = true;
                idx += 1;
            }
            _ => return Err(format!("unknown argument: {arg}")),
        }
    }

    let request_path = request_path.ok_or_else(|| "missing <request.json>".to_string())?;
    if !request_path.exists() {
        return Err(format!(
            "request.json not found: {}",
            request_path.display()
        ));
    }

    let app_root = app_root_from_current_exe()?;
    let app_provenance = load_app_provenance(&app_root).ok();

    // Parse request JSON early for runner selection and the sbpl-check compile.
    let mut request_value = read_json_file(&request_path, "request.json")?;
    let mut request_modified = false;

    if let Some(mode) = runner_mode_arg.as_deref() {
        if mode == "machme" {
            return Err(
                "--runner-mode machme is not supported; use --runner-mode byoxpc".to_string(),
            );
        }
        let kind = RunnerKind::parse(mode)
            .ok_or_else(|| format!("invalid value for --runner-mode: {mode}"))?;
        let obj = request_value
            .as_object_mut()
            .ok_or_else(|| "request.json must be a JSON object".to_string())?;
        let runner_entry = obj
            .entry("runner")
            .or_insert_with(|| Value::Object(serde_json::Map::new()));
        let runner_obj = runner_entry
            .as_object_mut()
            .ok_or_else(|| "runner must be a JSON object".to_string())?;
        if let Some(existing) = runner_obj.get("mode").and_then(|v| v.as_str()) {
            if existing != kind.as_str() {
                return Err(
                    "request.json already includes runner.mode; remove it or omit --runner-mode"
                        .to_string(),
                );
            }
        } else {
            runner_obj.insert("mode".to_string(), Value::String(kind.as_str().to_string()));
            request_modified = true;
        }
    }

    let selector = parse_runner_selector_value(&request_value)?;
    let runner_target = resolve_runner_target(&app_root, &selector)?;
    let runner_provenance = runner_provenance_from_target(&runner_target);

    // Resolve named augments BEFORE the runner (and the sbpl-check compile, if
    // the xpc_error path runs it) so the bytes they see match what the runner
    // will actually compile.
    let augment_resolution = resolve_augments(&mut request_value, &app_root);
    if augment_resolution.request_was_mutated() {
        // Strip-without-apply (null or [] augments) still mutates the
        // request and MUST trigger a temp-file write — otherwise the
        // runner reads the original on-disk file with the augments
        // key still present, violating the "runner sees no
        // augment-aware shape" contract.
        request_modified = true;
    }
    let policy_augmentation = match augment_resolution {
        AugmentResolution::NotPresent | AugmentResolution::StrippedNoOp => None,
        AugmentResolution::Applied(aug) => Some(aug),
        AugmentResolution::BadRequest(err) => {
            let runner_client = synthetic_runner_client(&format!(
                "runner not invoked; augment resolution failed: {err}"
            ));
            let execution = ExecutionData {
                request_path: request_path.to_string_lossy().to_string(),
                runner_service_bundle_id: runner_target
                    .bundle_id
                    .clone()
                    .unwrap_or_else(|| runner_target.service_name.clone()),
                runner_service_executable: runner_target.process_name.clone(),
                runner_service_name: runner_target.service_name.clone(),
                runner_registry_id: runner_target.registry_id.clone(),
                runner_provenance,
                app_provenance,
                policy_augmentation: None,
                policy_check: None,
                timeout_ms,
                runner_client,
                runner_result: None,
                runner_startup_diagnostics: None,
            };
            let data = RunData {
                execution,
                sandbox_log_capture: None,
                runner_sandbox_diagnostics: None,
            };
            let result = json_contract::JsonResult {
                ok: false,
                rc: None,
                exit_code: Some(1),
                normalized_outcome: Some("bad_request".to_string()),
                errno: None,
                error: Some(err),
                stderr: None,
                stdout: None,
            };
            json_contract::print_envelope("run", result, &data)?;
            return Ok(1);
        }
    };

    // Persist any in-memory request mutations (runner mode injection or
    // augment splicing) to a temp file so the runner — and the sbpl-check
    // compile, if we run it (xpc_error branch below) — both see the same bytes.
    let request_path_for_run = if request_modified {
        write_temp_request(&request_value)?
    } else {
        request_path.clone()
    };

    // The worker owns its published failure. A fallback compilation is only
    // requested on xpc_error, and cannot explain missing worker execution.
    let (runner_client, runner_result) = run_pw_runner_client(
        &runner_target.service_name,
        &request_path_for_run,
        timeout_ms,
        &runner_target.connection,
    )?;

    let runner_outcome = runner_result
        .as_ref()
        .and_then(|v| v.get("normalized_outcome"))
        .and_then(|v| v.as_str())
        .unwrap_or("runner_output_not_json");

    // Retain the independent fallback result without assigning a worker cause.
    let mut policy_check: Option<PolicyCheckCapture> = None;
    let runner_startup_diagnostics = if runner_outcome == "xpc_error" {
        let check = match run_policy_check(&request_path_for_run) {
            Ok(report) => report,
            Err(err) => PolicyCheckCapture::unavailable(err),
        };
        let note = fallback_policy_note(&check);
        let diagnostics = RunnerStartupDiagnostics {
            status: "xpc_error".to_string(),
            note,
            xpc_error: runner_result
                .as_ref()
                .and_then(|v| v.get("error"))
                .and_then(|v| v.as_str())
                .map(|s| s.to_string()),
            policy_check_status: Some(check.status.clone()),
        };
        policy_check = Some(check);
        Some(diagnostics)
    } else {
        None
    };

    let execution = complete_execution(ExecutionData {
        request_path: request_path.to_string_lossy().to_string(),
        runner_service_bundle_id: runner_target
            .bundle_id
            .clone()
            .unwrap_or_else(|| runner_target.service_name.clone()),
        runner_service_executable: runner_target.process_name.clone(),
        runner_service_name: runner_target.service_name,
        runner_registry_id: runner_target.registry_id.clone(),
        runner_provenance,
        app_provenance,
        policy_augmentation,
        policy_check,
        timeout_ms,
        runner_client,
        runner_result,
        runner_startup_diagnostics,
    });
    let (result, data, exit_code) = attach_sandbox_logs(
        execution,
        &request_value,
        no_log_capture,
        |pid, process, window| capture_sandbox_logs_with_timeout(pid, process, window, log_timeout),
    );

    json_contract::print_envelope("run", result, &data)?;
    Ok(exit_code)
}

fn complete_execution(data: ExecutionData) -> CompletedExecution {
    let diagnostics = execution_diagnostics(data.runner_result.as_ref());
    let runner_outcome = data
        .runner_result
        .as_ref()
        .and_then(|v| v.get("normalized_outcome"))
        .and_then(Value::as_str)
        .unwrap_or("runner_output_not_json")
        .to_string();
    let ok = runner_outcome == "ok";
    let exit_code = if ok { 0 } else { 1 };

    let error = if ok {
        None
    } else if let Some(v) = data
        .runner_result
        .as_ref()
        .and_then(|v| v.get("error"))
        .and_then(|v| v.as_str())
    {
        Some(v.to_string())
    } else if let Some(v) = data.runner_client.output.stdout_capture_error.as_ref() {
        Some(v.clone())
    } else if let Some(v) = data.runner_client.output.stdout_parse_error.as_ref() {
        Some(format!("runner output parse error: {v}"))
    } else {
        Some("run did not complete successfully".to_string())
    };

    let result = json_contract::JsonResult {
        ok,
        rc: None,
        exit_code: Some(exit_code),
        normalized_outcome: Some(runner_outcome),
        errno: None,
        error,
        stderr: None,
        stdout: None,
    };

    CompletedExecution {
        data,
        diagnostics,
        result,
        exit_code,
    }
}

// This is the production assembly seam. The collector receives only its query
// inputs; log processing has read-only execution evidence and returns only
// log-owned fields. Flattening merges the two channels into the existing wire
// shape without granting either channel ownership of the other's fields.
fn attach_sandbox_logs(
    execution: CompletedExecution,
    request: &Value,
    disabled: bool,
    collect: impl FnOnce(i64, &str, SandboxLogWindow) -> Result<SandboxLogCapture, String>,
) -> (json_contract::JsonResult, RunData, i32) {
    let logs = collect_log_evidence(
        execution.data.runner_result.as_ref(),
        request,
        &execution.data.runner_client,
        disabled,
        collect,
    );
    let data = RunData {
        execution: execution.data,
        sandbox_log_capture: logs.capture,
        runner_sandbox_diagnostics: Some(RunnerSandboxDiagnostics {
            execution: execution.diagnostics,
            logs: logs.diagnostics,
        }),
    };
    (execution.result, data, execution.exit_code)
}

fn collect_log_evidence(
    runner: Option<&Value>,
    request: &Value,
    client: &RunnerClientRun,
    disabled: bool,
    collect: impl FnOnce(i64, &str, SandboxLogWindow) -> Result<SandboxLogCapture, String>,
) -> LogEvidence {
    let mut capture = if disabled {
        None
    } else {
        worker_pid(runner).map(|pid| {
            let window = SandboxLogWindow::runner_client_span(
                client.started_at_unix_ms,
                client.ended_at_unix_ms,
            );
            collect(i64::from(pid), "pw-probe-runner", window.clone()).unwrap_or_else(|err| {
                SandboxLogCapture {
                    window,
                    capture_status: "requested_unavailable".into(),
                    tool_exit_code: 1,
                    blocked_reason: None,
                    output: crate::utils::JsonOutputCapture::unavailable(
                        err,
                        crate::utils::OBSERVER_CAPTURE_BYTES,
                    ),
                    observer: None,
                    observed_deny: None,
                    deny_events: None,
                    step_denies: None,
                    supervision: None,
                    processing_cutoff: None,
                }
            })
        })
    };
    let diagnostics = finish_sandbox_log_capture(runner, request, disabled, &mut capture);
    LogEvidence {
        capture,
        diagnostics,
    }
}

// Association and log diagnostics share one availability gate; retained events
// from a failed capture or without an authoritative PID cannot gain candidates.
fn finish_sandbox_log_capture(
    runner: Option<&Value>,
    request: &Value,
    disabled: bool,
    capture: &mut Option<SandboxLogCapture>,
) -> RunnerLogDiagnostics {
    if let Some(capture) = capture.as_mut() {
        capture.step_denies = None;
        if !disabled && worker_pid(runner).is_some() && capture.capture_status == "captured" {
            if let (Some(steps), Some(events)) = (
                runner
                    .and_then(|r| r.get("steps"))
                    .and_then(Value::as_array),
                capture.deny_events.as_ref(),
            ) {
                let plan = request.get("probe_plan").and_then(Value::as_array);
                match bounded_step_denies(
                    steps,
                    plan.map(Vec::as_slice).unwrap_or(&[]),
                    events,
                    worker_pid(runner),
                    capture.supervision.as_ref().map(|r| r.budget),
                ) {
                    Ok(associations) => capture.step_denies = Some(associations),
                    Err(cutoff) => {
                        capture.capture_status = if cutoff.reason == "deadline" {
                            "timeout"
                        } else {
                            "overflow"
                        }
                        .into();
                        capture.processing_cutoff = Some(cutoff);
                    }
                }
            }
        }
    }
    log_diagnostics(runner, disabled, capture.as_ref())
}

// Execution disposition and optional log correlation are separate observations.
// No outcome gate, host/client PID fallback, or causal interpretation of a match.

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

fn integrity_issue(kind: &str, detail: String) -> Value {
    json!({"kind": kind, "detail": detail})
}

fn status_conflict_issue() -> Value {
    json!({"kind": "conflict", "rule": "D1", "question": "final_status",
        "observations": ["exit_code", "term_signal"],
        "detail": "one successful reap represented as both an exit status and a signal"})
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
    schema: Option<u64>,
    reporting_failed: bool,
) -> DispositionProjection {
    let reaped = sub.get("reaped").and_then(Value::as_bool) == Some(true);
    let signal = sub.get("term_signal").and_then(Value::as_i64);
    let exit = sub.get("exit_code").and_then(Value::as_i64);
    let Some(record) = sub.get("disposition").filter(|r| !r.is_null()) else {
        if schema.map_or(false, |v| v >= 10) {
            return DispositionProjection {
                disposition: "withheld",
                cause: Some("unknown"),
                stop_reason: None,
                integrity: Some("invalid"),
                issues: vec![integrity_issue(
                    "missing_record",
                    "response 10 requires a disposition record".into(),
                )],
            };
        }
        // Legacy reply without the record: the raw-status compatibility projection,
        // with the one integrity rule that needs no record (D1).
        let mut issues = Vec::new();
        let disposition = if !reaped {
            "unconfirmed"
        } else if signal.is_some() && exit.is_some() {
            issues.push(status_conflict_issue());
            "conflicting"
        } else if signal.is_some() {
            "signaled"
        } else if exit == Some(0) {
            "clean_exit"
        } else if exit.is_some() {
            "nonzero_exit"
        } else {
            "unconfirmed"
        };
        let cause = if disposition == "clean_exit" {
            None
        } else {
            Some("unknown")
        };
        return DispositionProjection {
            disposition,
            cause,
            stop_reason: None,
            integrity: Some("not_reported"),
            issues,
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

fn execution_diagnostics(runner: Option<&Value>) -> RunnerExecutionDiagnostics {
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
            runner
                .and_then(|r| r.get("schema_version"))
                .and_then(Value::as_u64),
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
        worker_pid: pid,
        process_disposition: projection.disposition,
        termination_cause: projection.cause,
        stop_reason: projection.stop_reason,
        disposition_integrity: projection.integrity,
        disposition_issues: projection.issues,
    }
}

fn log_diagnostics(
    runner: Option<&Value>,
    disabled: bool,
    capture: Option<&SandboxLogCapture>,
) -> RunnerLogDiagnostics {
    let pid = worker_pid(runner);
    let capture_status = if disabled {
        "disabled"
    } else if pid.is_none() {
        "no_worker"
    } else {
        capture
            .map(|c| c.capture_status.as_str())
            .unwrap_or("requested_unavailable")
    };
    let first_deny = if capture_status == "captured" {
        capture
            .and_then(|c| c.deny_events.as_ref())
            .and_then(|events| {
                let pid = pid?;
                events
                    .iter()
                    .position(|e| e.pid == Some(pid))
                    .map(|event_index| DenyEventReference { event_index })
            })
    } else {
        None
    };
    let correlation_status = if disabled || pid.is_none() {
        "not_attempted"
    } else if capture_status != "captured" || capture.and_then(|c| c.deny_events.as_ref()).is_none()
    {
        "unavailable"
    } else if first_deny.is_some() {
        "pid_match"
    } else {
        "no_match"
    };
    let permission_failures_without_record =
        if matches!(correlation_status, "pid_match" | "no_match") {
            permission_failures_without_record(runner, capture)
        } else {
            None
        };
    RunnerLogDiagnostics {
        capture_status: capture_status.to_string(),
        correlation_status,
        first_deny,
        permission_failures_without_record,
    }
}

// The runner's own per-step classification is the only input: a step counts
// when `comparison.observation` is `permission_failure`. Candidate membership
// comes from the associations already computed for this capture. A reply whose
// steps carry no comparison cannot be classified and yields null.
fn permission_failures_without_record(
    runner: Option<&Value>,
    capture: Option<&SandboxLogCapture>,
) -> Option<Vec<String>> {
    let steps = runner?.get("steps")?.as_array()?;
    if !steps.is_empty()
        && !steps
            .iter()
            .any(|s| s.pointer("/comparison/observation").is_some())
    {
        return None;
    }
    let recorded: std::collections::HashSet<&str> = capture
        .and_then(|c| c.step_denies.as_ref())
        .map(|associations| {
            associations
                .iter()
                .flat_map(|a| a.candidate_step_ids.iter().map(String::as_str))
                .collect()
        })
        .unwrap_or_default();
    Some(
        steps
            .iter()
            .filter(|s| {
                s.pointer("/comparison/observation").and_then(Value::as_str)
                    == Some("permission_failure")
            })
            .filter_map(|s| s.get("step_id").and_then(Value::as_str))
            .filter(|id| !recorded.contains(id))
            .map(str::to_string)
            .collect(),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sandbox_log::{SandboxDenyEvent, capture_sandbox_logs, match_step_denies};
    use serde_json::json;

    fn diagnostics_with_logs(
        runner: Option<&Value>,
        disabled: bool,
        capture: Option<&SandboxLogCapture>,
    ) -> RunnerSandboxDiagnostics {
        RunnerSandboxDiagnostics {
            execution: execution_diagnostics(runner),
            logs: log_diagnostics(runner, disabled, capture),
        }
    }

    fn execution_data(runner: Option<Value>) -> ExecutionData {
        use crate::runner_select::{RunnerConnectionKind, RunnerTarget};
        let target = RunnerTarget {
            kind: RunnerKind::Standard,
            connection: RunnerConnectionKind::XpcService,
            service_name: "controlled.service".into(),
            process_name: "PWRunner".into(),
            bundle_id: None,
            bundle_path: None,
            executable_path: None,
            registry_id: None,
            signature: None,
            entitlements: None,
        };
        let stdout = serde_json::to_vec(&runner).unwrap();
        let (output, _) = crate::utils::capture_json_output(
            &std::process::Output {
                status: std::os::unix::process::ExitStatusExt::from_raw(0),
                stdout,
                stderr: b"fixed runner-client diagnostic".to_vec(),
            },
            "runner",
            crate::utils::RUNNER_CAPTURE_BYTES,
        );
        ExecutionData {
            request_path: "/controlled/request.json".into(),
            runner_service_bundle_id: target.service_name.clone(),
            runner_service_executable: target.process_name.clone(),
            runner_service_name: target.service_name.clone(),
            runner_registry_id: None,
            runner_provenance: runner_provenance_from_target(&target),
            app_provenance: None,
            policy_augmentation: None,
            policy_check: None,
            timeout_ms: DEFAULT_TIMEOUT_MS,
            runner_client: RunnerClientRun {
                argv: vec!["controlled-client".into()],
                started_at_unix_ms: 1_000,
                ended_at_unix_ms: 2_500,
                exit_code: 0,
                output,
            },
            runner_result: runner,
            runner_startup_diagnostics: None,
        }
    }

    #[test]
    fn collector_states_preserve_the_serialized_execution_half() {
        // Independent native observations with two indistinguishable candidates
        // and one permission failure that has no matching captured path.
        let request = json!({"probe_plan": [
            {"step_id": "a", "attempt": {"kind": "file", "action": "open_write", "target": "/attempt"}},
            {"step_id": "b", "attempt": {"kind": "file", "action": "open_write", "target": "/attempt"}},
            {"step_id": "silent", "attempt": {"kind": "file", "action": "open_write", "target": "/silent"}}
        ]});
        let mut runner = worker("ok", None);
        runner["schema_version"] = json!(7);
        runner["steps"] = json!(["a", "b", "silent"].map(|id| json!({
            "step_id": id, "drift": null, "deny_signal": null,
            "sandbox_check": {"outcome": "allow", "rc": 0, "pid": 42},
            "attempt": {"outcome": "open_failed", "rc": -1, "errno": 1,
                "requested_kind": "file", "requested_action": "open_write"},
            "comparison": {"observation": "permission_failure", "conclusion": "unavailable",
                "limitations": ["sandbox_attribution_unestablished"]}
        })));
        let mut failed = runner.clone();
        failed["normalized_outcome"] = json!("runner_failed");
        failed["error"] = json!("worker signal 9");
        failed["runner_subprocess"]["exit_code"] = Value::Null;
        failed["runner_subprocess"]["term_signal"] = json!(9);
        let mut no_pid = runner.clone();
        no_pid["pid"] = json!(42); // A matching host/client PID is not authoritative.
        no_pid["runner_subprocess"]
            .as_object_mut()
            .unwrap()
            .remove("pid");
        let fixture: Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/disposition/a1_expected.json"
        ))
        .unwrap();
        let mut no_comparisons = runner.clone();
        for step in no_comparisons["steps"].as_array_mut().unwrap() {
            step.as_object_mut().unwrap().remove("comparison");
        }
        let cases = [
            (Some(runner), 0, "clean_exit", Value::Null, true),
            (Some(failed), 1, "signaled", json!("unknown"), true),
            (Some(no_pid), 0, "no_worker", Value::Null, true),
            (
                Some(fixture["data"]["runner_result"].clone()),
                1,
                "signaled",
                json!("host_sentinel_deadline"),
                false,
            ),
            (Some(no_comparisons), 0, "clean_exit", Value::Null, false),
            (None, 1, "no_worker", Value::Null, false),
        ];
        for (runner, expected_exit, disposition, cause, permission_steps) in cases {
            let mut baseline = None;
            for state in [
                "events",
                "empty",
                "unrelated",
                "blocked",
                "error",
                "capture_error",
                "parse_error",
                "invalid_reply",
                "window_mismatch",
                "invalid_window",
                "requested_unavailable",
                "timeout",
                "overflow",
                "disabled",
            ] {
                let execution = complete_execution(execution_data(runner.clone()));
                let client = serde_json::to_value(&execution.data.runner_client).unwrap();
                let pid = worker_pid(runner.as_ref());
                let disabled = state == "disabled";
                let mut invoked = false;
                let (result, data, exit_code) = attach_sandbox_logs(
                    execution,
                    &request,
                    disabled,
                    |actual_pid, name, window| {
                        invoked = true;
                        assert_eq!(Some(actual_pid), pid.map(i64::from));
                        assert_eq!(name, "pw-probe-runner");
                        assert_eq!(
                            (window.started_at_unix_ms, window.ended_at_unix_ms),
                            (1_000, 2_500)
                        );
                        if state == "requested_unavailable" {
                            return Err("controlled collector launch failure".into());
                        }
                        let status = match state {
                            "events" | "empty" | "unrelated" => "captured",
                            other => other,
                        };
                        let events = match state {
                            "empty" => vec![],
                            "unrelated" => vec![event(Some(99))],
                            // Every failed capture deliberately retains a matching
                            // diagnostic event. Status, not event presence, gates it.
                            _ => vec![event(Some(99)), event(pid)],
                        };
                        let mut capture = capture_with(status, events);
                        capture.window = window;
                        capture.observer = Some(json!({"data": {"diagnostic": "retained reply"}}));
                        // Reject precomputed/stale associations supplied by a collector.
                        capture.step_denies = Some(match_step_denies(
                            runner
                                .as_ref()
                                .and_then(|r| r["steps"].as_array())
                                .map(Vec::as_slice)
                                .unwrap_or(&[]),
                            request["probe_plan"].as_array().unwrap(),
                            capture.deny_events.as_ref().unwrap(),
                            pid,
                        ));
                        Ok(capture)
                    },
                );
                assert_eq!(invoked, !disabled && pid.is_some(), "{state}");
                assert_eq!(exit_code, expected_exit, "{state}");
                let text = json_contract::render_envelope("run", result, &data).unwrap();
                let mut wire: Value = serde_json::from_str(&text).unwrap();
                assert_eq!(wire["result"]["exit_code"], expected_exit, "{state}");
                assert_eq!(wire["result"]["ok"], expected_exit == 0, "{state}");
                assert_eq!(
                    wire["data"]["runner_result"],
                    runner.clone().unwrap_or(Value::Null),
                    "{state}"
                );
                assert_eq!(wire["data"]["runner_client"], client, "{state}");
                assert_eq!(
                    wire["data"]
                        .as_object()
                        .unwrap()
                        .keys()
                        .map(String::as_str)
                        .collect::<Vec<_>>(),
                    [
                        "app_provenance",
                        "policy_augmentation",
                        "policy_check",
                        "request_path",
                        "runner_client",
                        "runner_provenance",
                        "runner_registry_id",
                        "runner_result",
                        "runner_sandbox_diagnostics",
                        "runner_service_bundle_id",
                        "runner_service_executable",
                        "runner_service_name",
                        "runner_startup_diagnostics",
                        "sandbox_log_capture",
                        "timeout_ms"
                    ],
                    "internal ownership structs must not change the data wire shape",
                );
                let diag = &wire["data"]["runner_sandbox_diagnostics"];
                assert_eq!(
                    diag.as_object()
                        .unwrap()
                        .keys()
                        .map(String::as_str)
                        .collect::<Vec<_>>(),
                    [
                        "capture_status",
                        "correlation_status",
                        "disposition_integrity",
                        "disposition_issues",
                        "first_deny",
                        "permission_failures_without_record",
                        "process_disposition",
                        "stop_reason",
                        "termination_cause",
                        "worker_pid"
                    ],
                    "internal ownership structs must not change the diagnostics wire shape",
                );
                assert_eq!(diag["process_disposition"], disposition, "{state}");
                assert_eq!(diag["termination_cause"], cause, "{state}");
                let cap = &wire["data"]["sandbox_log_capture"];
                if disabled || pid.is_none() {
                    assert!(cap.is_null());
                    assert_eq!(
                        diag["capture_status"],
                        if disabled { "disabled" } else { "no_worker" }
                    );
                    assert_eq!(diag["correlation_status"], "not_attempted");
                    assert!(diag["first_deny"].is_null());
                    assert!(diag["permission_failures_without_record"].is_null());
                } else if matches!(state, "events" | "empty" | "unrelated") {
                    assert_eq!(diag["capture_status"], "captured");
                    assert_eq!(
                        diag["correlation_status"],
                        if state == "events" {
                            "pid_match"
                        } else {
                            "no_match"
                        }
                    );
                    assert_eq!(
                        diag["first_deny"],
                        if state == "events" {
                            json!({"event_index": 1})
                        } else {
                            Value::Null
                        }
                    );
                    if permission_steps {
                        assert_eq!(
                            diag["permission_failures_without_record"],
                            if state == "events" {
                                json!(["silent"])
                            } else {
                                json!(["a", "b", "silent"])
                            }
                        );
                        if state == "events" {
                            assert_eq!(cap["step_denies"].as_array().unwrap().len(), 1);
                            assert_eq!(cap["step_denies"][0]["event_index"], 1);
                            assert_eq!(
                                cap["step_denies"][0]["candidate_step_ids"],
                                json!(["a", "b"])
                            );
                            assert_eq!(cap["step_denies"][0]["association"], "ambiguous");
                        } else {
                            assert_eq!(cap["step_denies"], json!([]));
                        }
                    }
                } else {
                    assert_eq!(cap["capture_status"], state);
                    assert_eq!(diag["capture_status"], state);
                    assert_eq!(diag["correlation_status"], "unavailable");
                    assert!(cap["step_denies"].is_null());
                    assert!(diag["first_deny"].is_null());
                    assert!(diag["permission_failures_without_record"].is_null());
                    if state != "requested_unavailable" {
                        assert_eq!(cap["deny_events"][1]["pid"], pid.unwrap());
                        assert_eq!(cap["observer"]["data"]["diagnostic"], "retained reply");
                    }
                }
                // Remove only the four log-owned diagnostic fields and the log
                // subtree. Everything else, including unknown future execution
                // fields, must be byte-identical across collector states.
                wire.as_object_mut().unwrap().remove("generated_at_unix_ms");
                wire["data"]
                    .as_object_mut()
                    .unwrap()
                    .remove("sandbox_log_capture");
                for key in [
                    "capture_status",
                    "correlation_status",
                    "first_deny",
                    "permission_failures_without_record",
                ] {
                    assert!(
                        wire["data"]["runner_sandbox_diagnostics"]
                            .as_object_mut()
                            .unwrap()
                            .remove(key)
                            .is_some()
                    );
                }
                let bytes = serde_json::to_vec(&wire).unwrap();
                if let Some(baseline) = &baseline {
                    assert_eq!(&bytes, baseline, "execution changed under {state}");
                } else {
                    baseline = Some(bytes);
                }
            }
        }
    }

    #[test]
    fn real_subprocess_failures_preserve_execution_and_withhold_associations() {
        use crate::log_capture::{self, Boundary, LogTimeout, TimeoutSource};
        let native: Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/disposition/a1_expected.json"
        ))
        .unwrap();
        let runner = native["data"]["runner_result"].clone();
        let mut baseline = None;
        for (script, expected) in [
            ("import time; time.sleep(60)", "timeout"),
            ("import os; os.write(1,b'x'*33554433)", "overflow"),
            ("import os; os.write(2,b'e'*131073)", "overflow"),
            ("import sys; sys.exit(7)", "error"),
            (
                "import os,signal; os.kill(os.getpid(),signal.SIGTERM)",
                "error",
            ),
            ("print('{broken')", "parse_error"),
        ] {
            let (result, data, code) = attach_sandbox_logs(
                complete_execution(execution_data(Some(runner.clone()))),
                &json!({"probe_plan":[]}),
                false,
                |pid, process, window| {
                    let mut command = std::process::Command::new("/usr/bin/python3");
                    command.args(["-c", script]);
                    let budget = LogTimeout {
                        milliseconds: if expected == "timeout" { 150 } else { 3000 },
                        source: TimeoutSource::Cli,
                    }
                    .start()
                    .unwrap();
                    let raw = log_capture::capture(&mut command, budget, Boundary::Observer);
                    Ok(crate::sandbox_log::parse_supervised_observer(
                        raw, window, pid, process,
                    ))
                },
            );
            assert_eq!(code, 1);
            let mut wire: Value = serde_json::from_str(
                &json_contract::render_envelope("run", result, &data).unwrap(),
            )
            .unwrap();
            assert_eq!(wire["data"]["runner_result"], runner);
            let capture = &wire["data"]["sandbox_log_capture"];
            assert_eq!(capture["capture_status"], expected);
            assert_eq!(capture["supervision"]["cleanup"]["outcome"], "group_absent");
            assert!(capture["step_denies"].is_null());
            let diag = &wire["data"]["runner_sandbox_diagnostics"];
            assert_eq!(diag["correlation_status"], "unavailable");
            assert!(
                diag["first_deny"].is_null()
                    && diag["permission_failures_without_record"].is_null()
            );
            wire.as_object_mut().unwrap().remove("generated_at_unix_ms");
            wire["data"]
                .as_object_mut()
                .unwrap()
                .remove("sandbox_log_capture");
            for key in [
                "capture_status",
                "correlation_status",
                "first_deny",
                "permission_failures_without_record",
            ] {
                wire["data"]["runner_sandbox_diagnostics"]
                    .as_object_mut()
                    .unwrap()
                    .remove(key);
            }
            let bytes = serde_json::to_vec(&wire).unwrap();
            if let Some(baseline) = &baseline {
                assert_eq!(&bytes, baseline, "{expected}");
            } else {
                baseline = Some(bytes);
            }
        }
    }

    #[test]
    fn retained_events_without_worker_identity_never_acquire_associations() {
        let request = json!({"probe_plan": [{"step_id": "s", "attempt": {
            "kind": "file", "action": "open_write", "target": "/attempt"}}]});
        for sub in [
            Value::Null,
            json!({"pid": 0}),
            json!({"pid": -1}),
            json!({"pid": 4_294_967_338_u64}),
        ] {
            let runner = json!({"pid": 42, "runner_subprocess": sub, "steps": [{"step_id": "s",
                "comparison": {"observation": "permission_failure"}}]});
            let mut capture = capture_with("captured", vec![event(Some(42))]);
            capture.step_denies = Some(match_step_denies(
                runner["steps"].as_array().unwrap(),
                request["probe_plan"].as_array().unwrap(),
                capture.deny_events.as_ref().unwrap(),
                Some(42),
            ));
            assert_eq!(capture.step_denies.as_ref().unwrap().len(), 1);
            let mut capture = Some(capture);
            let diagnostics =
                finish_sandbox_log_capture(Some(&runner), &request, false, &mut capture);
            assert!(capture.as_ref().unwrap().step_denies.is_none());
            assert_eq!(
                capture
                    .as_ref()
                    .unwrap()
                    .deny_events
                    .as_ref()
                    .unwrap()
                    .len(),
                1
            );
            assert_eq!(diagnostics.capture_status, "no_worker");
            assert_eq!(diagnostics.correlation_status, "not_attempted");
            assert!(diagnostics.first_deny.is_none());
            assert!(diagnostics.permission_failures_without_record.is_none());
        }
    }

    #[test]
    fn no_match_is_distinguished_by_unrecorded_permission_failures() {
        fn step(id: &str, observation: &str) -> Value {
            json!({"step_id": id, "drift": null, "attempt": {"requested_path": format!("/{id}")},
                "comparison": {"observation": observation}})
        }
        fn plan(ids: &[&str]) -> Value {
            json!({"probe_plan": ids.iter().map(|id| json!({"step_id": id, "attempt": {
                "kind": "file", "action": "open_write", "target": format!("/{id}")}})).collect::<Vec<_>>()})
        }
        fn denied(path: &str) -> SandboxDenyEvent {
            let mut e = event(Some(42));
            e.path = Some(path.into());
            e
        }
        let ids = ["recorded", "silent", "fine"];
        let request = plan(&ids);
        let mut runner = worker("ok", None);
        runner["steps"] = json!([
            step("recorded", "permission_failure"),
            step("silent", "permission_failure"),
            step("fine", "succeeded"),
        ]);
        // One denial recorded, one not: only the silent one is listed.
        let mut cap = Some(capture_with("captured", vec![denied("/recorded")]));
        let diag = finish_sandbox_log_capture(Some(&runner), &request, false, &mut cap);
        assert_eq!(diag.correlation_status, "pid_match");
        assert_eq!(
            diag.permission_failures_without_record,
            Some(vec!["silent".to_string()])
        );
        // No record at all: no_match now names the denials the attempts reported.
        let mut cap = Some(capture_with("captured", vec![event(Some(99))]));
        let diag = finish_sandbox_log_capture(Some(&runner), &request, false, &mut cap);
        assert_eq!(diag.correlation_status, "no_match");
        assert_eq!(
            diag.permission_failures_without_record,
            Some(vec!["recorded".to_string(), "silent".to_string()])
        );
        let wire = serde_json::to_value(&diag).unwrap();
        assert_eq!(
            wire["permission_failures_without_record"],
            json!(["recorded", "silent"])
        );
        // Nothing permission-shaped: the list is empty, not null.
        let mut clean = runner.clone();
        clean["steps"] = json!([step("fine", "succeeded"), step("other", "other_failure")]);
        let mut cap = Some(capture_with("captured", vec![]));
        let diag = finish_sandbox_log_capture(Some(&clean), &request, false, &mut cap);
        assert_eq!(diag.permission_failures_without_record, Some(vec![]));
        // Unclassifiable, uncorrelated or disabled: null, never an invented list.
        let mut legacy = runner.clone();
        legacy["steps"] = json!([{"step_id": "recorded", "drift": false,
            "attempt": {"requested_path": "/recorded", "errno": 1}}]);
        let mut cap = Some(capture_with("captured", vec![]));
        let diag = finish_sandbox_log_capture(Some(&legacy), &request, false, &mut cap);
        assert_eq!(diag.correlation_status, "no_match");
        assert_eq!(diag.permission_failures_without_record, None);
        for (status, disabled) in [
            ("error", false),
            ("window_mismatch", false),
            ("captured", true),
        ] {
            let mut cap = Some(capture_with(status, vec![]));
            let diag = finish_sandbox_log_capture(Some(&runner), &request, disabled, &mut cap);
            assert_ne!(diag.correlation_status, "no_match", "{status}");
            assert_eq!(diag.permission_failures_without_record, None, "{status}");
        }
        let diag = finish_sandbox_log_capture(Some(&runner), &request, false, &mut None);
        assert_eq!(diag.correlation_status, "unavailable");
        assert_eq!(diag.permission_failures_without_record, None);
    }

    #[test]
    fn log_timeout_is_validated_before_any_runner_or_specimen_work() {
        for value in [
            "0",
            "-1",
            "+1",
            "1.5",
            "unlimited",
            "18446744073709551615",
            "18446744073709551616",
        ] {
            for disabled in [false, true] {
                let mut args = vec!["--log-timeout-ms".into(), value.into()];
                if disabled {
                    args.push("--no-log-capture".into());
                }
                let error = cmd_run(&args).unwrap_err();
                assert!(
                    error.contains("invalid value for --log-timeout-ms"),
                    "{error}"
                );
            }
        }
        let args = vec![
            "--log-timeout-ms".into(),
            "1".into(),
            "--no-log-capture".into(),
        ];
        let error = cmd_run(&args).unwrap_err();
        assert!(
            !error.contains("log-timeout"),
            "valid finite timeout must pass option admission: {error}"
        );
        assert!(
            cmd_run(&["--log-timeout-ms".into()])
                .unwrap_err()
                .contains("missing value")
        );
    }

    #[test]
    fn documented_controller_limits() {
        let manifest: serde_json::Value =
            serde_json::from_str(include_str!("../../docs/limits.json")).unwrap();
        let owned: std::collections::BTreeMap<&str, u64> = manifest["limits"]
            .as_array()
            .unwrap()
            .iter()
            .filter(|row| {
                row["checks"].as_array().unwrap().iter().any(|check| {
                    check["path"] == "controller/src/run_flow.rs" && check["kind"] == "value"
                })
            })
            .map(|row| (row["id"].as_str().unwrap(), row["value"].as_u64().unwrap()))
            .collect();
        let actual = std::collections::BTreeMap::from([
            ("client_rpc_wait", DEFAULT_TIMEOUT_MS),
            ("log_window_pad", crate::sandbox_log::LOG_WINDOW_PAD_SECONDS),
            (
                "controller_output",
                crate::utils::RUNNER_CAPTURE_BYTES as u64,
            ),
            (
                "policy_helper_output",
                crate::utils::HELPER_CAPTURE_BYTES as u64,
            ),
            (
                "log_observer_output",
                crate::utils::OBSERVER_CAPTURE_BYTES as u64,
            ),
        ]);
        assert_eq!(owned, actual);
        // The behavioral oracle is independent of the documented value.
        let cap = crate::utils::RUNNER_CAPTURE_BYTES;
        for len in [cap - 1, cap, cap + 1] {
            let bytes = vec![b'x'; len];
            let (text, truncated) = crate::utils::truncate_output(&bytes, cap);
            assert_eq!(text.len(), len.min(cap));
            assert_eq!(truncated, len > cap);
        }
    }

    #[test]
    fn fallback_admission_and_compile_results_remain_distinct() {
        for (status, compiled, expected) in [
            (
                "policy_too_large",
                Some(false),
                "admission refused: policy_too_large",
            ),
            ("compile_error", Some(false), "compilation failed"),
            ("compiled", Some(true), "compiled ok"),
            ("unavailable", None, "compilation unavailable"),
        ] {
            let mut check = PolicyCheckCapture::unavailable("test".into());
            check.status = status.into();
            check.compiled = compiled;
            let note = fallback_policy_note(&check);
            assert!(note.contains(expected));
            assert!(note.contains("worker progress and cause unavailable"));
        }
    }

    fn capture_with(status: &str, events: Vec<SandboxDenyEvent>) -> SandboxLogCapture {
        SandboxLogCapture {
            window: SandboxLogWindow::runner_client_span(0, 1),
            capture_status: status.into(),
            tool_exit_code: 0,
            blocked_reason: None,
            output: crate::utils::JsonOutputCapture::unavailable(
                String::new(),
                crate::utils::OBSERVER_CAPTURE_BYTES,
            ),
            observer: None,
            observed_deny: Some(!events.is_empty()),
            deny_events: Some(events),
            step_denies: None,
            supervision: None,
            processing_cutoff: None,
        }
    }

    #[test]
    fn observer_windows_survive_association_serialization_and_consumer_recovery() {
        use crate::sandbox_log::parse_observer_output;
        use std::io::Write;
        use std::os::unix::process::ExitStatusExt;
        use std::process::{Command, ExitStatus, Output, Stdio};

        let window = SandboxLogWindow::runner_client_span(1_000, 2_500);
        let good = json!({"start": window.start, "end": window.end, "last": null});
        let mut replies = vec![("matching", good.clone(), "captured")];
        for (name, field, value) in [
            ("wrong_start", "start", json!("1970-01-01 00:00:02+0000")),
            ("wrong_end", "end", json!("1970-01-01 00:00:04+0000")),
            ("trailing", "last", json!("10s")),
            ("null_start", "start", Value::Null),
        ] {
            let mut reply = good.clone();
            reply[field] = value;
            replies.push((name, reply, "window_mismatch"));
        }
        for field in ["start", "end"] {
            let mut reply = good.clone();
            reply.as_object_mut().unwrap().remove(field);
            replies.push((field, reply, "window_mismatch"));
        }
        replies.push(("missing_bounds", json!({"last": "10s"}), "window_mismatch"));
        replies.push(("clock_rollback", Value::Null, "invalid_window"));

        let request = json!({"probe_plan": [{"step_id": "s", "attempt": {
            "kind": "file", "action": "open_write", "target": "/attempt"}}]});
        let events = json!([{"pid": 42, "process": "pw-probe-runner", "operation": "file-write-data",
            "path": "/attempt", "raw_line": "retained observer evidence"}]);
        let mut envelopes = Vec::new();
        for version in [5, 8] {
            for signaled in [false, true] {
                let outcome = if signaled { "runner_failed" } else { "ok" };
                let mut runner = worker(outcome, signaled.then_some(9));
                runner["schema_version"] = json!(version);
                runner["steps"] = json!([{"step_id": "s", "drift": null,
                    "attempt": {"requested_path": "/attempt"}}]);
                for (name, bounds, expected_status) in &replies {
                    let mut observer = json!({"data": bounds});
                    let mut capture = Some(if *expected_status == "invalid_window" {
                        capture_sandbox_logs(
                            42,
                            "pw-probe-runner",
                            SandboxLogWindow::runner_client_span(5_000, 4_000),
                        )
                        .unwrap()
                    } else {
                        observer["data"]["observed_deny"] = json!(true);
                        observer["data"]["deny_events"] = events.clone();
                        let out = Output {
                            status: ExitStatus::from_raw(0),
                            stdout: serde_json::to_vec(&observer).unwrap(),
                            stderr: vec![],
                        };
                        parse_observer_output(&out, window.clone())
                    });
                    let execution = complete_execution(execution_data(Some(runner.clone())));
                    let (result, data, exit_code) =
                        attach_sandbox_logs(execution, &request, false, |_, _, _| {
                            Ok(capture.take().unwrap())
                        });
                    assert_eq!(exit_code, i32::from(signaled));
                    let text = json_contract::render_envelope("run", result, &data).unwrap();
                    let wire: Value = serde_json::from_str(&text).unwrap();
                    assert!(wire["schema_version"].as_u64().unwrap() >= 2);
                    assert_eq!(wire["result"]["ok"], !signaled);
                    assert_eq!(wire["result"]["normalized_outcome"], outcome);
                    assert_eq!(wire["data"]["runner_result"], runner);
                    let cap = &wire["data"]["sandbox_log_capture"];
                    let diag = &wire["data"]["runner_sandbox_diagnostics"];
                    assert_eq!(cap["capture_status"], *expected_status, "{name}");
                    assert_eq!(diag["capture_status"], *expected_status);
                    if *expected_status == "invalid_window" {
                        assert!(cap["observer"].is_null() && cap["deny_events"].is_null());
                        assert!(cap["window"]["start"].is_null() && cap["window"]["end"].is_null());
                        assert_eq!(cap["window"]["started_at_unix_ms"], 5_000);
                        assert_eq!(cap["window"]["ended_at_unix_ms"], 4_000);
                    } else {
                        assert_eq!(cap["observer"], observer);
                        assert_eq!(cap["deny_events"], events);
                        assert_eq!(cap["observed_deny"], true);
                    }
                    if *expected_status == "captured" {
                        assert_eq!(cap["step_denies"][0]["candidate_step_ids"], json!(["s"]));
                        assert_eq!(diag["first_deny"], json!({"event_index": 0}));
                        assert_eq!(diag["correlation_status"], "pid_match");
                    } else {
                        assert!(
                            cap["step_denies"].is_null(),
                            "{name}: no candidate from unusable interval"
                        );
                        assert!(
                            diag["first_deny"].is_null(),
                            "{name}: no diagnostic match from unusable interval"
                        );
                        assert_eq!(diag["correlation_status"], "unavailable");
                    }
                    envelopes.push(wire);
                }
            }
        }
        // Exercise the real independent consumer on serialized production output,
        // including old runner replies inside the new controller envelope.
        let mut child = Command::new("/usr/bin/python3")
            .args(["-B", "-c", "import json, sys; sys.path.insert(0, sys.argv[1]); from consumer import recover_evidence; print(json.dumps([recover_evidence(e) for e in json.load(sys.stdin)]))"])
            .arg(std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../tests/lib"))
            .stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped()).spawn().unwrap();
        child
            .stdin
            .take()
            .unwrap()
            .write_all(&serde_json::to_vec(&envelopes).unwrap())
            .unwrap();
        let output = child.wait_with_output().unwrap();
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
        let answers: Vec<Value> = serde_json::from_slice(&output.stdout).unwrap();
        assert_eq!(answers.len(), envelopes.len());
        for (wire, answer) in envelopes.iter().zip(answers) {
            let cap = &wire["data"]["sandbox_log_capture"];
            let diag = &wire["data"]["runner_sandbox_diagnostics"];
            let recovered = &answer["denials"];
            assert_eq!(recovered["capture"], *cap);
            assert_eq!(recovered["window"], cap["window"]);
            assert_eq!(recovered["events"], cap["deny_events"]);
            assert_eq!(recovered["capture_status"], cap["capture_status"]);
            assert_eq!(recovered["diagnostics"], *diag);
            assert_eq!(recovered["correlation_status"], diag["correlation_status"]);
            if cap["capture_status"] == "captured" {
                assert_eq!(recovered["candidates"][0]["event"], events[0]);
                assert_eq!(
                    recovered["candidates"][0]["candidate_step_ids"],
                    json!(["s"])
                );
            } else {
                assert!(recovered["candidates"].is_null());
                assert_eq!(recovered["association_reporting"], "not_reported");
            }
        }
    }
    #[test]
    fn padded_records_survive_assembly_and_consumer_recovery() {
        use crate::sandbox_log::{observer_argv, parse_observer_output};
        use std::io::Write;
        use std::process::{Command, Stdio};

        // Native permission failures and expected event subsets are specified
        // independently of the timestamp-selection fixture and matching code.
        let paths = [
            "/before",
            "/lower-bound",
            "/start-pad",
            "/start-slack",
            "/early",
            "/short-tail",
            "/short-pad",
            "/short-bound",
            "/late",
            "/end-slack",
            "/end-pad",
            "/upper-bound",
            "/after",
        ];
        let plan: Vec<_> = paths
            .iter()
            .map(|path| {
                json!({"step_id": path,
            "attempt": {"kind":"file", "action":"open_read", "target":path}})
            })
            .collect();
        let request = json!({"probe_plan":plan});
        let mut runner = worker("ok", None);
        runner["schema_version"] = json!(7);
        runner["steps"] = json!(paths.iter().map(|path| json!({
            "step_id":path, "drift":null,
            "sandbox_check":{"outcome":"allow", "native_rc":0, "result_source":"validator"},
            "attempt":{"requested_kind":"file", "requested_action":"open_read",
                "requested_path":path, "outcome":"open_failed", "errno":1,
                "native_rc":-1, "result_source":"worker"},
            "comparison":{"scope":"submitted_operation_and_target", "prediction":"allow",
                "observation":"permission_failure", "observation_basis":"permission_errno",
                "operation_relation":"matched", "target_relation":"same_submitted",
                "conclusion":"unavailable", "limitations":["state_stability_unestablished",
                    "query_attempt_order_unestablished", "sandbox_attribution_unestablished"]}
        })).collect::<Vec<_>>());
        let fixture = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../tests/fixtures/deny_capture/observer.py");
        let mut envelopes = Vec::new();
        for (start, end, expected) in [
            (
                1_999,
                22_001,
                vec![
                    "/lower-bound",
                    "/start-pad",
                    "/start-slack",
                    "/early",
                    "/short-tail",
                    "/short-pad",
                    "/short-bound",
                    "/late",
                    "/end-slack",
                    "/end-pad",
                    "/upper-bound",
                ],
            ),
            (
                1_999,
                2_001,
                vec![
                    "/lower-bound",
                    "/start-pad",
                    "/start-slack",
                    "/early",
                    "/short-tail",
                    "/short-pad",
                    "/short-bound",
                ],
            ),
            (
                13_000,
                23_000,
                vec!["/late", "/end-slack", "/end-pad", "/upper-bound"],
            ),
            (40_000, 50_000, vec![]),
        ] {
            let mut execution = execution_data(Some(runner.clone()));
            execution.runner_client.started_at_unix_ms = start;
            execution.runner_client.ended_at_unix_ms = end;
            let (result, data, code) = attach_sandbox_logs(
                complete_execution(execution),
                &request,
                false,
                |pid, process, window| {
                    let argv = observer_argv("observer".into(), pid, process, &window).unwrap();
                    let out = Command::new("/usr/bin/python3")
                        .arg(&fixture)
                        .args(&argv[1..])
                        .output()
                        .unwrap();
                    assert!(
                        out.status.success(),
                        "{}",
                        String::from_utf8_lossy(&out.stderr)
                    );
                    Ok(parse_observer_output(&out, window))
                },
            );
            assert_eq!(code, 0);
            let wire: Value = serde_json::from_str(
                &json_contract::render_envelope("run", result, &data).unwrap(),
            )
            .unwrap();
            assert_eq!(wire["data"]["runner_result"], runner);
            let cap = &wire["data"]["sandbox_log_capture"];
            assert_eq!(cap["capture_status"], "captured");
            assert_eq!(cap["window"]["pad_seconds"], 2);
            let events = cap["deny_events"].as_array().unwrap();
            assert_eq!(
                events
                    .iter()
                    .map(|e| e["path"].as_str().unwrap())
                    .collect::<Vec<_>>(),
                expected
            );
            assert_eq!(cap["observer"]["data"]["deny_events"], cap["deny_events"]);
            let candidates = cap["step_denies"].as_array().unwrap();
            assert_eq!(candidates.len(), expected.len());
            for (index, path) in expected.iter().enumerate() {
                assert_eq!(candidates[index]["event_index"], index);
                assert_eq!(candidates[index]["candidate_step_ids"], json!([path]));
                assert_eq!(candidates[index]["association"], "candidate");
                assert_eq!(candidates[index]["matching_evidence"][0]["path"], *path);
            }
            let diag = &wire["data"]["runner_sandbox_diagnostics"];
            assert_eq!(
                diag["correlation_status"],
                if expected.is_empty() {
                    "no_match"
                } else {
                    "pid_match"
                }
            );
            assert_eq!(
                diag["first_deny"],
                if expected.is_empty() {
                    Value::Null
                } else {
                    json!({"event_index":0})
                }
            );
            assert_eq!(
                diag["permission_failures_without_record"],
                json!(
                    paths
                        .iter()
                        .filter(|p| !expected.contains(p))
                        .collect::<Vec<_>>()
                )
            );
            envelopes.push(wire);
        }
        let mut child = Command::new("/usr/bin/python3")
            .args(["-B", "-c", "import json, sys; sys.path.insert(0, sys.argv[1]); from consumer import recover_evidence, validate_evidence_shape; es=json.load(sys.stdin); assert all(not validate_evidence_shape(e) for e in es); print(json.dumps([recover_evidence(e) for e in es]))"])
            .arg(std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../tests/lib"))
            .stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped()).spawn().unwrap();
        child
            .stdin
            .take()
            .unwrap()
            .write_all(&serde_json::to_vec(&envelopes).unwrap())
            .unwrap();
        let out = child.wait_with_output().unwrap();
        assert!(
            out.status.success(),
            "{}",
            String::from_utf8_lossy(&out.stderr)
        );
        let answers: Vec<Value> = serde_json::from_slice(&out.stdout).unwrap();
        assert_eq!(answers.len(), envelopes.len());
        for (wire, answer) in envelopes.iter().zip(answers) {
            let cap = &wire["data"]["sandbox_log_capture"];
            let recovered = &answer["denials"];
            assert_eq!(recovered["capture"], *cap);
            assert_eq!(recovered["window"], cap["window"]);
            assert_eq!(recovered["events"], cap["deny_events"]);
            assert_eq!(
                recovered["diagnostics"],
                wire["data"]["runner_sandbox_diagnostics"]
            );
            let candidates = recovered["candidates"].as_array().unwrap();
            assert_eq!(
                candidates.len(),
                cap["step_denies"].as_array().unwrap().len()
            );
            for (candidate, original) in candidates
                .iter()
                .zip(cap["step_denies"].as_array().unwrap())
            {
                assert_eq!(
                    candidate["candidate_step_ids"],
                    original["candidate_step_ids"]
                );
                assert_eq!(
                    candidate["matching_evidence"],
                    original["matching_evidence"]
                );
                assert_eq!(
                    candidate["event"],
                    cap["deny_events"][original["event_index"].as_u64().unwrap() as usize]
                );
            }
        }
    }

    fn event(pid: Option<i32>) -> SandboxDenyEvent {
        SandboxDenyEvent {
            pid,
            process: Some("pw-probe-runner".into()),
            operation: Some("file-write-data".into()),
            path: Some("/attempt".into()),
            raw_line: Some("ordinary denied write before unrelated self-signal".into()),
        }
    }
    fn worker(outcome: &str, signal: Option<i32>) -> Value {
        json!({"pid": 9999, "normalized_outcome": outcome, "sandboxed_after_apply": true,
            "runner_subprocess": {"pid": 42, "reaped": true, "term_signal": signal,
                "exit_code": if signal.is_none() { Some(0) } else { None }, "termination_request": null}})
    }
    #[test]
    fn serialized_candidates_remain_inspectable_beside_a_legacy_runner_reply() {
        let mut runner = worker("runner_failed", Some(9));
        runner["schema_version"] = json!(5);
        runner["steps"] = json!([{"step_id":"s", "drift":false,
            "attempt":{"requested_path":"/attempt"}}]);
        let original = runner.clone();
        let plan = [json!({"step_id":"s", "attempt":{
            "kind":"file", "action":"open_write", "target":"/attempt"}})];
        let mut cap = capture_with("captured", vec![event(Some(99)), event(Some(42))]);
        cap.step_denies = Some(match_step_denies(
            runner["steps"].as_array().unwrap(),
            &plan,
            cap.deny_events.as_ref().unwrap(),
            Some(42),
        ));
        let diag = diagnostics_with_logs(Some(&runner), false, Some(&cap));
        let envelope = json!({"data":{"runner_result":runner,
            "sandbox_log_capture":cap, "runner_sandbox_diagnostics":diag}});
        let data = &envelope["data"];
        assert_eq!(data["runner_result"], original);
        assert!(
            data["runner_result"]["steps"][0]
                .get("comparison")
                .is_none()
        );
        let capture = &data["sandbox_log_capture"];
        assert_eq!(capture["deny_events"].as_array().unwrap().len(), 2);
        let candidate = &capture["step_denies"][0];
        let index = candidate["event_index"].as_u64().unwrap() as usize;
        assert_eq!(index, 1);
        assert_eq!(capture["deny_events"][index]["pid"], 42);
        assert_eq!(candidate["candidate_step_ids"], json!(["s"]));
        assert_eq!(candidate["association"], "candidate");
        assert_eq!(
            candidate["matching_evidence"],
            json!([{
            "step_id":"s", "operation":"file-write-data", "operation_source":"submitted_attempt",
            "requested_kind":"file", "requested_action":"open_write", "path":"/attempt",
            "path_sources":["submitted_attempt.target", "attempt.requested_path"]}])
        );
        for key in [
            "event_timestamps_available",
            "exact_run_membership",
            "step_ordering",
            "pid_reuse_protection",
        ] {
            assert_eq!(capture["window"][key], false);
        }
        assert_eq!(
            data["runner_sandbox_diagnostics"]["termination_cause"],
            "unknown"
        );
    }

    #[test]
    fn incomplete_attempt_retains_independent_prediction_and_event_without_cause() {
        let mut runner = worker("runner_failed", Some(9));
        runner["runner_subprocess"]["done_observed"] = json!(false);
        runner["steps"] = json!([{"step_id": "s",
            "sandbox_check": {"result_source": "validator", "outcome": "deny", "native_rc": 1},
            "attempt": {"result_source": "synthetic", "native_rc": null,
                "missing_reason": "slot_incomplete", "outcome": "not_run_worker_died"},
            "drift": null}]);
        let before = runner.clone();
        let plan = [json!({"step_id": "s", "attempt": {
            "kind": "file", "action": "open_write", "target": "/attempt"}})];
        let cap = capture_with("captured", vec![event(Some(42))]);
        let associations = match_step_denies(
            runner["steps"].as_array().unwrap(),
            &plan,
            cap.deny_events.as_ref().unwrap(),
            Some(42),
        );
        assert_eq!(associations.len(), 1);
        assert_eq!(associations[0].event_index, 0);
        assert_eq!(associations[0].candidate_step_ids, ["s"]);
        assert_eq!(associations[0].association, "candidate");
        let diag = diagnostics_with_logs(Some(&runner), false, Some(&cap));
        assert_eq!(diag.execution.termination_cause, Some("unknown"));
        assert_eq!(diag.logs.first_deny.unwrap().event_index, 0);
        assert_eq!(runner, before);
        assert_eq!(cap.deny_events.as_ref().unwrap().len(), 1);
    }

    #[test]
    fn ordinary_denial_and_unrelated_signal_remain_separate_observations() {
        let runner = worker("runner_failed", Some(9));
        let original = runner.clone();
        let cap = capture_with("captured", vec![event(Some(99)), event(Some(42))]);
        let diag = diagnostics_with_logs(Some(&runner), false, Some(&cap));
        assert_eq!(diag.execution.worker_pid, Some(42));
        assert_eq!(diag.execution.process_disposition, "signaled");
        assert_eq!(diag.logs.first_deny.unwrap().event_index, 1);
        assert_eq!(diag.execution.termination_cause, Some("unknown"));
        assert_eq!(diag.logs.correlation_status, "pid_match");
        assert_eq!(cap.deny_events.as_ref().unwrap().len(), 2);
        assert_eq!(runner, original);
    }
    #[test]
    fn capture_conditions_do_not_change_execution_status_or_cause() {
        let runner = worker("runner_failed", Some(9));
        let original = runner.clone();
        for (disabled, status, expected_capture, expected_correlation) in [
            (true, "captured", "disabled", "not_attempted"),
            (false, "blocked", "blocked", "unavailable"),
            (false, "error", "error", "unavailable"),
            (
                false,
                "requested_unavailable",
                "requested_unavailable",
                "unavailable",
            ),
            (false, "captured", "captured", "no_match"),
        ] {
            let cap = capture_with(status, vec![]);
            let diag = diagnostics_with_logs(Some(&runner), disabled, Some(&cap));
            assert_eq!(diag.logs.capture_status, expected_capture);
            assert_eq!(diag.logs.correlation_status, expected_correlation);
            assert_eq!(diag.execution.process_disposition, "signaled");
            assert_eq!(diag.execution.termination_cause, Some("unknown"));
            assert!(diag.logs.first_deny.is_none());
            assert_eq!(runner, original);
        }
    }
    #[test]
    fn successful_run_keeps_correlations_without_a_termination_cause() {
        let runner = worker("ok", None);
        let cap = capture_with("captured", vec![event(Some(42))]);
        let diag = diagnostics_with_logs(Some(&runner), false, Some(&cap));
        assert_eq!(diag.execution.process_disposition, "clean_exit");
        assert_eq!(diag.logs.capture_status, "captured");
        assert_eq!(diag.logs.first_deny.unwrap().event_index, 0);
        assert_eq!(diag.execution.termination_cause, None);
        assert_eq!(runner["normalized_outcome"], "ok");
    }
    #[test]
    fn no_worker_never_uses_host_or_client_pid() {
        for outcome in ["bad_request", "xpc_error", "runner_sandbox_denied"] {
            let runner =
                json!({"pid": 42, "normalized_outcome": outcome, "runner_subprocess": null});
            let cap = capture_with("captured", vec![event(Some(42))]);
            let diag = diagnostics_with_logs(Some(&runner), false, Some(&cap));
            assert_eq!(diag.execution.worker_pid, None);
            assert_eq!(diag.logs.capture_status, "no_worker");
            assert_eq!(diag.execution.process_disposition, "no_worker");
            assert_eq!(diag.logs.correlation_status, "not_attempted");
            assert!(diag.logs.first_deny.is_none());
        }
    }
    #[test]
    fn missing_mismatched_pid_and_unavailable_events_never_supply_first_deny() {
        let runner = worker("runner_failed", Some(9));
        for status in ["captured", "blocked", "parse_error"] {
            let cap = capture_with(status, vec![event(None), event(Some(99))]);
            let diag = diagnostics_with_logs(Some(&runner), false, Some(&cap));
            assert!(diag.logs.first_deny.is_none());
        }
        let mut cap = capture_with("captured", vec![]);
        cap.deny_events = None;
        let diag = diagnostics_with_logs(Some(&runner), false, Some(&cap));
        assert_eq!(diag.logs.correlation_status, "unavailable");
        let diag = diagnostics_with_logs(Some(&runner), false, None);
        assert_eq!(diag.logs.capture_status, "requested_unavailable");
    }
    #[test]
    fn unconfirmed_reap_does_not_manufacture_clean_disposition_from_status_storage() {
        let mut runner = worker("runner_failed", None);
        runner["runner_subprocess"]["reaped"] = json!(false);
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert_eq!(diag.execution.process_disposition, "unconfirmed");
        assert_eq!(diag.execution.termination_cause, Some("unknown"));
    }
    // Disposition record plan, B1 (wave 1 refusal). Red by design until the
    // controller validates status representations; wave 2 adds the structured
    // conflict issue with `termination_cause: unknown`. Run it explicitly with
    // `cargo test --bins -- --ignored conflicting_status_representation`.
    #[test]
    fn conflicting_status_representation_is_not_silently_resolved() {
        let mut runner = worker("runner_failed", Some(9));
        // One final reap represented as both a clean exit and a signal.
        runner["runner_subprocess"]["exit_code"] = json!(0);
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert!(
            !matches!(
                diag.execution.process_disposition,
                "signaled" | "clean_exit"
            ),
            "exit_code 0 beside term_signal 9 is an invalid status pair; \
             an unqualified disposition ({}) resolves it silently",
            diag.execution.process_disposition
        );
        // Unaffected: identity and capture fields do not depend on the status rule.
        assert_eq!(diag.execution.worker_pid, Some(42));
        assert_eq!(diag.logs.capture_status, "disabled");
        assert_eq!(diag.logs.correlation_status, "not_attempted");
    }
    // Disposition record plan, E1 (wave 2, behavioral red). The runner reply
    // carries the record the contract names; the controller must project the
    // witnessed host cleanup instead of ignoring the object. Constructed JSON,
    // runnable before the runner produces the record.
    fn disposition_reply(cause_trigger: &str, reaped: bool) -> Value {
        let mut runner = worker("runner_timeout", Some(9));
        runner["schema_version"] = json!(10);
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
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert_eq!(
            diag.execution.termination_cause,
            Some("host_sentinel_deadline"),
            "E1: the controller ignores the carried disposition record and reports a generic cause"
        );
        assert_eq!(diag.execution.process_disposition, "signaled");
        let wire = serde_json::to_value(&diag).unwrap();
        assert_eq!(wire["disposition_integrity"], json!("valid"));
        assert_eq!(wire["stop_reason"], json!("sentinel_deadline"));
    }
    #[test]
    fn record_contradicting_its_basis_is_withheld() {
        // A supported signal claim while the reply says the worker was never reaped.
        let runner = disposition_reply("deadline_expiry", false);
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert_eq!(
            diag.execution.process_disposition, "withheld",
            "E1: an assembled claim that contradicts its basis must be withheld, not re-derived"
        );
        assert_eq!(diag.execution.termination_cause, Some("unknown"));
        let wire = serde_json::to_value(&diag).unwrap();
        assert_eq!(wire["disposition_integrity"], json!("invalid"));
        assert!(
            wire["disposition_issues"]
                .as_array()
                .map_or(false, |v| !v.is_empty())
        );
    }
    #[test]
    fn conflicting_status_reports_the_status_rule() {
        let mut runner = worker("runner_failed", Some(9));
        runner["runner_subprocess"]["exit_code"] = json!(0);
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert_eq!(
            diag.execution.process_disposition, "conflicting",
            "B1: exit_code 0 beside term_signal 9 must be reported as a status conflict"
        );
        assert_eq!(diag.execution.termination_cause, Some("unknown"));
        let wire = serde_json::to_value(&diag).unwrap();
        let issues = wire["disposition_issues"]
            .as_array()
            .cloned()
            .unwrap_or_default();
        assert!(
            issues.iter().any(|i| i["rule"] == json!("D1")),
            "issue must name the status rule D1"
        );
    }
    // Disposition record plan, F3 (wave 1, preservation) and E1's counterexamples:
    // legacy replies without the record keep their compatibility projections, and
    // an unrecognized future trigger never projects a cause.
    #[test]
    fn legacy_reply_without_record_keeps_compatibility_projections() {
        let mut signaled = worker("runner_failed", Some(9));
        signaled["schema_version"] = json!(9);
        let diag = diagnostics_with_logs(Some(&signaled), true, None);
        assert_eq!(diag.execution.process_disposition, "signaled");
        assert_eq!(diag.execution.termination_cause, Some("unknown"));
        let wire = serde_json::to_value(&diag).unwrap();
        assert!(wire.get("stop_reason").map_or(true, Value::is_null));
        let mut clean = worker("ok", None);
        clean["schema_version"] = json!(9);
        let diag = diagnostics_with_logs(Some(&clean), true, None);
        assert_eq!(diag.execution.process_disposition, "clean_exit");
        assert_eq!(diag.execution.termination_cause, None);
    }
    #[test]
    fn unrecognized_future_trigger_never_projects_a_cause() {
        let runner = disposition_reply("host_future_trigger", true);
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert_eq!(diag.execution.termination_cause, Some("unknown"));
        assert_ne!(diag.execution.process_disposition, "clean_exit");
    }

    #[test]
    fn current_reply_missing_disposition_is_withheld() {
        let mut runner = disposition_reply("deadline_expiry", true);
        runner["runner_subprocess"]["disposition"] = Value::Null;
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert_eq!(diag.execution.process_disposition, "withheld");
        assert_eq!(diag.execution.disposition_integrity, Some("invalid"));
    }

    #[test]
    fn disposition_cannot_hide_a_second_status_representation() {
        let mut runner = disposition_reply("deadline_expiry", true);
        runner["runner_subprocess"]["exit_code"] = json!(0);
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert_eq!(diag.execution.process_disposition, "withheld");
        assert_eq!(diag.execution.termination_cause, Some("unknown"));
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
            let diag = diagnostics_with_logs(Some(&runner), true, None);
            assert_eq!(
                diag.execution.process_disposition, "withheld",
                "mismatched {field}"
            );
            assert_eq!(diag.execution.termination_cause, Some("unknown"));
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
            let diag = diagnostics_with_logs(Some(&runner), true, None);
            assert_eq!(
                diag.execution.process_disposition, "withheld",
                "basis {basis}"
            );
        }
    }

    #[test]
    fn unknown_stop_is_preserved_without_becoming_a_known_projection() {
        let mut runner = disposition_reply("deadline_expiry", true);
        runner["runner_subprocess"]["poll_stop_reason"] = json!("future_stop");
        runner["runner_subprocess"]["disposition"]["questions"]["stop_reason"]["answer"] =
            json!("future_stop");
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert_eq!(diag.execution.stop_reason, None);
        assert_eq!(diag.execution.process_disposition, "signaled");
        assert_eq!(
            runner["runner_subprocess"]["poll_stop_reason"],
            json!("future_stop")
        );
    }

    #[test]
    fn disposition_checks_step_proofs_issues_and_projection_copies() {
        let envelope: Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/disposition/a1_expected.json"
        ))
        .unwrap();
        let base = &envelope["data"]["runner_result"];
        let diag = diagnostics_with_logs(Some(base), true, None);
        assert_eq!(
            diag.execution.disposition_integrity,
            Some("valid"),
            "{:?}",
            diag.execution.disposition_issues
        );
        // The degraded-reply contract intentionally withholds comparisons while
        // retaining independently usable lifecycle observations.
        let mut degraded = base.clone();
        degraded["normalized_outcome"] = json!("runner_reporting_failed");
        degraded["reporting_failure"] = json!({"origin":"runner_host", "evidence_retained":true});
        for step in degraded["steps"].as_array_mut().unwrap() {
            step["comparison"] = Value::Null;
        }
        let diag = diagnostics_with_logs(Some(&degraded), true, None);
        assert_eq!(diag.execution.disposition_integrity, Some("valid"));
        assert_eq!(
            diag.execution.termination_cause,
            Some("host_sentinel_deadline")
        );
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
            let diag = diagnostics_with_logs(Some(&runner), true, None);
            assert_eq!(
                diag.execution.disposition_integrity,
                Some("invalid"),
                "{path}"
            );
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
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert_eq!(diag.execution.disposition_integrity, Some("invalid"));
    }

    #[test]
    fn malformed_disposition_questions_are_withheld_without_panicking() {
        for name in DISPOSITION_RUN_QUESTIONS {
            let mut runner = disposition_reply("deadline_expiry", true);
            runner["runner_subprocess"]["disposition"]["questions"]
                .as_object_mut()
                .unwrap()
                .remove(*name);
            let diag = diagnostics_with_logs(Some(&runner), true, None);
            assert_eq!(
                diag.execution.process_disposition, "withheld",
                "missing {name}"
            );
        }
        for state in [json!("future_state"), json!(17), Value::Null] {
            let mut runner = disposition_reply("deadline_expiry", true);
            runner["runner_subprocess"]["disposition"]["questions"]["stop_reason"]["state"] = state;
            let diag = diagnostics_with_logs(Some(&runner), true, None);
            assert_eq!(diag.execution.process_disposition, "withheld");
        }
    }
}
