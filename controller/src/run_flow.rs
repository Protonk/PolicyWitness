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
use std::ffi::OsString;
use std::path::Path;

use crate::app_layout::app_root_from_current_exe;
use crate::augments::{resolve_augments, AugmentResolution, PolicyAugmentation};
use crate::cli;
use crate::evidence;
use crate::json_contract;
use crate::policy_check::{run_policy_check, PolicyCheckCapture};
use crate::request_patch::{read_json_file, write_temp_request};
use crate::runner_client::{run_pw_runner_client, RunnerClientRun};
use crate::runner_manager::RunnerKind;
use crate::runner_select::{
    parse_runner_selector_value, resolve_runner_target, runner_provenance_from_target,
    RunnerProvenance,
};
use crate::sandbox_log::{
    capture_sandbox_logs_last, match_step_denies, worker_pid, SandboxLogCapture, SandboxLogWindow,
};
use crate::utils::now_unix_ms;

pub const DEFAULT_TIMEOUT_MS: u64 = 240_000;
const DEFAULT_LOG_LAST: &str = "10s";

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
pub struct RunData {
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
    pub log_last: String,
    pub runner_client: RunnerClientRun,
    pub runner_result: Option<Value>,
    pub sandbox_log_capture: Option<SandboxLogCapture>,
    pub runner_startup_diagnostics: Option<RunnerStartupDiagnostics>,
    pub runner_sandbox_diagnostics: Option<RunnerSandboxDiagnostics>,
}

#[derive(Serialize)]
pub struct RunnerSandboxDiagnostics {
    pub worker_pid: Option<i32>,
    pub process_disposition: &'static str,
    pub capture_status: String,
    pub correlation_status: &'static str,
    pub termination_cause: Option<&'static str>,
    /// First PID match in the capture array, not the first event in time or a
    /// cause of termination. Reference keeps the event in observer evidence.
    pub first_deny: Option<DenyEventReference>,
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
    format!("runner did not reply; worker progress and cause unavailable; sbpl-check describes only the fallback helper ({detail})")
}

fn synthetic_runner_client(note: &str) -> RunnerClientRun {
    let now = now_unix_ms();
    RunnerClientRun {
        argv: vec!["(runner not invoked)".to_string()],
        started_at_unix_ms: now,
        ended_at_unix_ms: now,
        exit_code: 2,
        output: crate::utils::JsonOutputCapture::unavailable(note.to_string()),
    }
}

pub fn cmd_run(args: &[OsString]) -> Result<i32, String> {
    let mut request_path: Option<std::path::PathBuf> = None;
    let mut timeout_ms = DEFAULT_TIMEOUT_MS;
    let mut log_last = DEFAULT_LOG_LAST.to_string();
    let mut runner_mode_arg: Option<String> = None;
    let mut no_log_capture = false;

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
            "--log-last" => {
                let value = args
                    .get(idx + 1)
                    .and_then(|s| s.to_str())
                    .ok_or_else(|| "missing value for --log-last".to_string())?;
                log_last = value.to_string();
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
            let data = RunData {
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
                log_last,
                runner_client,
                runner_result: None,
                sandbox_log_capture: None,
                runner_startup_diagnostics: None,
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

    let runner_pid = worker_pid(runner_result.as_ref());
    let runner_outcome = runner_result
        .as_ref()
        .and_then(|v| v.get("normalized_outcome"))
        .and_then(|v| v.as_str())
        .unwrap_or("runner_output_not_json")
        .to_string();
    let ok = runner_outcome == "ok";

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

    let mut sandbox_log_capture = if no_log_capture {
        // Explicitly disabled; diagnostics distinguish this from unavailable capture.
        None
    } else {
        runner_pid.map(|pid| {
            // Capture unified-log evidence only when the runner PID is known.
            capture_sandbox_logs_last(i64::from(pid), "pw-probe-runner", &log_last).unwrap_or_else(
                |err| SandboxLogCapture {
                    window: SandboxLogWindow::trailing(&log_last),
                    capture_status: "requested_unavailable".to_string(),
                    tool_exit_code: 1,
                    blocked_reason: None,
                    output: crate::utils::JsonOutputCapture::unavailable(err),
                    observer: None,
                    observed_deny: None,
                    deny_events: None,
                    step_denies: None,
                },
            )
        })
    };

    if let (Some(ref mut capture), Some(steps)) = (
        sandbox_log_capture.as_mut(),
        runner_result
            .as_ref()
            .and_then(|v| v.get("steps"))
            .and_then(|v| v.as_array()),
    ) {
        if let Some(deny_events) = capture.deny_events.as_ref() {
            if capture.capture_status == "captured" {
                let plan = request_value.get("probe_plan").and_then(Value::as_array);
                capture.step_denies = Some(match_step_denies(
                    steps,
                    plan.map(Vec::as_slice).unwrap_or(&[]),
                    deny_events,
                    runner_pid,
                ));
            }
        }
    }

    let runner_sandbox_diagnostics = synthesize_runner_sandbox_diagnostics(
        runner_result.as_ref(),
        no_log_capture,
        sandbox_log_capture.as_ref(),
    );

    let data = RunData {
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
        log_last,
        runner_client,
        runner_result,
        sandbox_log_capture,
        runner_startup_diagnostics,
        runner_sandbox_diagnostics,
    };

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
        exit_code: Some(if ok { 0 } else { 1 }),
        normalized_outcome: Some(runner_outcome),
        errno: None,
        error,
        stderr: None,
        stdout: None,
    };

    json_contract::print_envelope("run", result, &data)?;
    Ok(if ok { 0 } else { 1 })
}

// Execution disposition and optional log correlation are separate observations.
// No outcome gate, host/client PID fallback, or causal interpretation of a match.
fn synthesize_runner_sandbox_diagnostics(
    runner: Option<&Value>,
    disabled: bool,
    capture: Option<&SandboxLogCapture>,
) -> Option<RunnerSandboxDiagnostics> {
    let pid = worker_pid(runner);
    let sub = runner.and_then(|r| r.get("runner_subprocess"));
    let reaped = sub.and_then(|s| s.get("reaped")).and_then(Value::as_bool) == Some(true);
    let signal = sub
        .and_then(|s| s.get("term_signal"))
        .and_then(Value::as_i64);
    let exit = sub.and_then(|s| s.get("exit_code")).and_then(Value::as_i64);
    let disposition = if pid.is_none() {
        "no_worker"
    } else if !reaped {
        "unconfirmed"
    } else if signal.is_some() {
        "signaled"
    } else if exit == Some(0) {
        "clean_exit"
    } else if exit.is_some() {
        "nonzero_exit"
    } else {
        "unconfirmed"
    };
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
    Some(RunnerSandboxDiagnostics {
        worker_pid: pid,
        process_disposition: disposition,
        capture_status: capture_status.to_string(),
        correlation_status,
        termination_cause: if matches!(disposition, "signaled" | "nonzero_exit" | "unconfirmed") {
            Some("unknown")
        } else {
            None
        },
        first_deny,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sandbox_log::SandboxDenyEvent;
    use serde_json::json;

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
            ("controller_output", crate::utils::MAX_CAPTURE_BYTES as u64),
        ]);
        assert_eq!(owned, actual);
        // The behavioral oracle is independent of the documented value.
        for len in [1_048_575, 1_048_576, 1_048_577] {
            let bytes = vec![b'x'; len];
            let (text, truncated) = crate::utils::truncate_output(&bytes);
            assert_eq!(text.len(), len.min(1_048_576));
            assert_eq!(truncated, len > 1_048_576);
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
            window: SandboxLogWindow::trailing("10s"),
            capture_status: status.into(),
            tool_exit_code: 0,
            blocked_reason: None,
            output: crate::utils::JsonOutputCapture::unavailable(String::new()),
            observer: None,
            observed_deny: Some(!events.is_empty()),
            deny_events: Some(events),
            step_denies: None,
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
        let diag = synthesize_runner_sandbox_diagnostics(Some(&runner), false, Some(&cap)).unwrap();
        let envelope = json!({"data":{"runner_result":runner,
            "sandbox_log_capture":cap, "runner_sandbox_diagnostics":diag}});
        let data = &envelope["data"];
        assert_eq!(data["runner_result"], original);
        assert!(data["runner_result"]["steps"][0]
            .get("comparison")
            .is_none());
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
        let diag = synthesize_runner_sandbox_diagnostics(Some(&runner), false, Some(&cap)).unwrap();
        assert_eq!(diag.termination_cause, Some("unknown"));
        assert_eq!(diag.first_deny.unwrap().event_index, 0);
        assert_eq!(runner, before);
        assert_eq!(cap.deny_events.as_ref().unwrap().len(), 1);
    }

    #[test]
    fn ordinary_denial_and_unrelated_signal_remain_separate_observations() {
        let runner = worker("runner_failed", Some(9));
        let original = runner.clone();
        let cap = capture_with("captured", vec![event(Some(99)), event(Some(42))]);
        let diag = synthesize_runner_sandbox_diagnostics(Some(&runner), false, Some(&cap)).unwrap();
        assert_eq!(diag.worker_pid, Some(42));
        assert_eq!(diag.process_disposition, "signaled");
        assert_eq!(diag.first_deny.unwrap().event_index, 1);
        assert_eq!(diag.termination_cause, Some("unknown"));
        assert_eq!(diag.correlation_status, "pid_match");
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
            let diag =
                synthesize_runner_sandbox_diagnostics(Some(&runner), disabled, Some(&cap)).unwrap();
            assert_eq!(diag.capture_status, expected_capture);
            assert_eq!(diag.correlation_status, expected_correlation);
            assert_eq!(diag.process_disposition, "signaled");
            assert_eq!(diag.termination_cause, Some("unknown"));
            assert!(diag.first_deny.is_none());
            assert_eq!(runner, original);
        }
    }
    #[test]
    fn successful_run_keeps_correlations_without_a_termination_cause() {
        let runner = worker("ok", None);
        let cap = capture_with("captured", vec![event(Some(42))]);
        let diag = synthesize_runner_sandbox_diagnostics(Some(&runner), false, Some(&cap)).unwrap();
        assert_eq!(diag.process_disposition, "clean_exit");
        assert_eq!(diag.capture_status, "captured");
        assert_eq!(diag.first_deny.unwrap().event_index, 0);
        assert_eq!(diag.termination_cause, None);
        assert_eq!(runner["normalized_outcome"], "ok");
    }
    #[test]
    fn no_worker_never_uses_host_or_client_pid() {
        for outcome in ["bad_request", "xpc_error", "runner_sandbox_denied"] {
            let runner =
                json!({"pid": 42, "normalized_outcome": outcome, "runner_subprocess": null});
            let cap = capture_with("captured", vec![event(Some(42))]);
            let diag =
                synthesize_runner_sandbox_diagnostics(Some(&runner), false, Some(&cap)).unwrap();
            assert_eq!(diag.worker_pid, None);
            assert_eq!(diag.capture_status, "no_worker");
            assert_eq!(diag.process_disposition, "no_worker");
            assert_eq!(diag.correlation_status, "not_attempted");
            assert!(diag.first_deny.is_none());
        }
    }
    #[test]
    fn missing_mismatched_pid_and_unavailable_events_never_supply_first_deny() {
        let runner = worker("runner_failed", Some(9));
        for status in ["captured", "blocked", "parse_error"] {
            let cap = capture_with(status, vec![event(None), event(Some(99))]);
            let diag =
                synthesize_runner_sandbox_diagnostics(Some(&runner), false, Some(&cap)).unwrap();
            assert!(diag.first_deny.is_none());
        }
        let mut cap = capture_with("captured", vec![]);
        cap.deny_events = None;
        let diag = synthesize_runner_sandbox_diagnostics(Some(&runner), false, Some(&cap)).unwrap();
        assert_eq!(diag.correlation_status, "unavailable");
        let diag = synthesize_runner_sandbox_diagnostics(Some(&runner), false, None).unwrap();
        assert_eq!(diag.capture_status, "requested_unavailable");
    }
    #[test]
    fn unconfirmed_reap_does_not_manufacture_clean_disposition_from_status_storage() {
        let mut runner = worker("runner_failed", None);
        runner["runner_subprocess"]["reaped"] = json!(false);
        let diag = synthesize_runner_sandbox_diagnostics(Some(&runner), true, None).unwrap();
        assert_eq!(diag.process_disposition, "unconfirmed");
        assert_eq!(diag.termination_cause, Some("unknown"));
    }
}
