//! Orchestrates a single run and builds the JSON envelope.
//!
//! The controller reads the request, selects a runner, invokes the Swift client,
//! and attaches best-effort evidence (sandbox logs, cross-check results).

use serde::Serialize;
use serde_json::Value;
use std::ffi::OsString;
use std::path::Path;

use crate::app_layout::app_root_from_current_exe;
use crate::cli;
use crate::evidence;
use crate::json_contract;
use crate::policy_preflight::{run_policy_preflight, PolicyPreflightCapture};
use crate::request_patch::{load_instrumentation_value, read_json_file, write_temp_request};
use crate::runner_client::{
    run_pw_runner_client, run_pw_runner_client_with_cross_check, RunnerClientRun,
};
use crate::runner_manager::RunnerKind;
use crate::runner_select::{
    parse_runner_selector_value, resolve_runner_target, runner_provenance_from_target,
    RunnerProvenance,
};
use crate::sandbox_log::{capture_sandbox_logs_last, match_step_denies, SandboxLogCapture};
use crate::sonoma_cross_check::{
    apply_sonoma_cross_check_runner_results, extract_sonoma_cross_check_specs,
    inject_sonoma_cross_check_instrumentation, sonoma_cross_check_skipped,
    sonoma_cross_check_unavailable, sonoma_cross_check_wait_ms,
    SonomaCrossCheckPlan, SonomaCrossCheckReport,
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
    pub policy_preflight: Option<PolicyPreflightCapture>,
    pub timeout_ms: u64,
    pub log_last: String,
    pub runner_client: RunnerClientRun,
    pub runner_result: Option<Value>,
    pub sandbox_log_capture: Option<SandboxLogCapture>,
    pub sonoma_cross_check: Option<SonomaCrossCheckReport>,
    pub runner_startup_diagnostics: Option<RunnerStartupDiagnostics>,
    pub runner_sandbox_diagnostics: Option<RunnerSandboxDiagnostics>,
}

#[derive(Serialize)]
pub struct RunnerSandboxDiagnostics {
    pub first_deny: Option<DenyEventSummary>,
}

#[derive(Serialize)]
pub struct DenyEventSummary {
    pub operation: Option<String>,
    pub path: Option<String>,
    pub raw_line: Option<String>,
}

#[derive(Serialize)]
pub struct RunnerStartupDiagnostics {
    pub status: String,
    pub note: String,
    pub xpc_error: Option<String>,
    pub policy_preflight_status: Option<String>,
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

fn synthetic_runner_client(note: &str) -> RunnerClientRun {
    let now = now_unix_ms();
    RunnerClientRun {
        argv: vec!["(runner not invoked)".to_string()],
        started_at_unix_ms: now,
        ended_at_unix_ms: now,
        exit_code: 2,
        stdout_parse_error: None,
        stdout_truncated: false,
        stdout_raw: None,
        stderr: note.to_string(),
        stderr_truncated: false,
    }
}

pub fn cmd_run(args: &[OsString]) -> Result<i32, String> {
    let mut request_path: Option<std::path::PathBuf> = None;
    let mut timeout_ms = DEFAULT_TIMEOUT_MS;
    let mut log_last = DEFAULT_LOG_LAST.to_string();
    let mut instrumentation_arg: Option<String> = None;
    let mut runner_mode_arg: Option<String> = None;
    let mut sonoma_cross_check_enabled = false;

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
            "--instrumentation" => {
                let value = args
                    .get(idx + 1)
                    .and_then(|s| s.to_str())
                    .ok_or_else(|| "missing value for --instrumentation".to_string())?;
                instrumentation_arg = Some(value.to_string());
                idx += 2;
            }
            "--sonoma-cross-check" => {
                sonoma_cross_check_enabled = true;
                idx += 1;
            }
            _ => return Err(format!("unknown argument: {arg}")),
        }
    }

    let request_path = request_path.ok_or_else(|| "missing <request.json>".to_string())?;
    if !request_path.exists() {
        return Err(format!("request.json not found: {}", request_path.display()));
    }

    let app_root = app_root_from_current_exe()?;
    let app_provenance = load_app_provenance(&app_root).ok();

    // Parse request JSON early for runner selection and policy preflight.
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
            runner_obj.insert(
                "mode".to_string(),
                Value::String(kind.as_str().to_string()),
            );
            request_modified = true;
        }
    }

    let selector = parse_runner_selector_value(&request_value)?;
    let runner_target = resolve_runner_target(&app_root, &selector)?;
    let runner_provenance = runner_provenance_from_target(&runner_target);

    let mut policy_preflight = match run_policy_preflight(&request_path) {
        Ok(report) => Some(report),
        Err(err) => Some(PolicyPreflightCapture::unavailable(err)),
    };
    let preflight_failed = policy_preflight
        .as_ref()
        .and_then(|p| p.compiled)
        == Some(false);
    if preflight_failed {
        let preflight = policy_preflight.take();
        let compile_error = preflight
            .as_ref()
            .and_then(|p| p.compile_error.clone())
            .unwrap_or_else(|| "sbpl preflight failed".to_string());
        let runner_client = synthetic_runner_client(&format!(
            "runner not invoked; sbpl preflight failed: {compile_error}"
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
            policy_preflight: preflight,
            timeout_ms,
            log_last,
            runner_client,
            runner_result: None,
            sandbox_log_capture: None,
            sonoma_cross_check: None,
            runner_startup_diagnostics: None,
            runner_sandbox_diagnostics: None,
        };

        let result = json_contract::JsonResult {
            ok: false,
            rc: None,
            exit_code: Some(1),
            normalized_outcome: Some("bad_policy".to_string()),
            errno: None,
            error: Some(compile_error),
            stderr: None,
            stdout: None,
        };
        json_contract::print_envelope("run", result, &data)?;
        return Ok(1);
    }

    if let Some(arg) = instrumentation_arg.as_deref() {
        let instrumentation = load_instrumentation_value(arg)?;
        let obj = request_value
            .as_object_mut()
            .ok_or_else(|| "request.json must be a JSON object".to_string())?;
        if obj.contains_key("instrumentation") {
            return Err("request.json already includes instrumentation; remove it or omit --instrumentation".to_string());
        }
        obj.insert("instrumentation".to_string(), instrumentation);
        request_modified = true;
    }

    let mut sonoma_cross_check_report: Option<SonomaCrossCheckReport> = None;
    let mut sonoma_cross_check_plan: Option<SonomaCrossCheckPlan> = None;

    if sonoma_cross_check_enabled {
        let specs = extract_sonoma_cross_check_specs(&request_value)?;
        if specs.is_empty() {
            sonoma_cross_check_report =
                Some(sonoma_cross_check_skipped("no sandbox_check steps".to_string()));
        } else {
            match crate::app_layout::resolve_contents_macos_tool("sb_api_validator") {
                Ok(tool_path) => {
                    let wait_ms = sonoma_cross_check_wait_ms(specs.len());
                    // Inject a post-sandbox delay so the runner stays alive for cross-checking.
                    inject_sonoma_cross_check_instrumentation(&mut request_value, wait_ms)?;
                    request_modified = true;
                    sonoma_cross_check_plan = Some(SonomaCrossCheckPlan {
                        tool_path,
                        process_name: runner_target.process_name.clone(),
                        wait_ms,
                        specs,
                    });
                }
                Err(err) => {
                    sonoma_cross_check_report = Some(sonoma_cross_check_unavailable(err));
                }
            }
        }
    }

    let request_path_for_runner = if request_modified {
        write_temp_request(&request_value)?
    } else {
        request_path.clone()
    };

    let (runner_client, runner_result, sonoma_cross_check_from_run) =
        if let Some(plan) = sonoma_cross_check_plan {
            run_pw_runner_client_with_cross_check(
                &runner_target.service_name,
                &request_path_for_runner,
                timeout_ms,
                &runner_target.connection,
                plan,
            )?
        } else {
            let (runner_client, runner_result) = run_pw_runner_client(
                &runner_target.service_name,
                &request_path_for_runner,
                timeout_ms,
                &runner_target.connection,
            )?;
            (runner_client, runner_result, None)
        };

    let mut sonoma_cross_check =
        sonoma_cross_check_report.or(sonoma_cross_check_from_run);

    if let (Some(report), Some(result)) = (sonoma_cross_check.as_mut(), runner_result.as_ref()) {
        apply_sonoma_cross_check_runner_results(report, result);
    }

    let runner_pid = runner_result
        .as_ref()
        .and_then(|v| v.get("pid"))
        .and_then(|v| v.as_i64());
    let runner_outcome = runner_result
        .as_ref()
        .and_then(|v| v.get("normalized_outcome"))
        .and_then(|v| v.as_str())
        .unwrap_or("runner_output_not_json")
        .to_string();
    let ok = runner_outcome == "ok";

    let runner_startup_diagnostics = if runner_outcome == "xpc_error" {
        let mut note = "runner did not reply; process may have exited during sandbox apply or policy may block Mach/XPC reply".to_string();
        if let Some(preflight) = policy_preflight.as_ref() {
            match preflight.compiled {
                Some(true) => note.push_str(" (sbpl preflight compiled ok)"),
                Some(false) => note.push_str(" (sbpl preflight failed)"),
                None => {
                    if preflight.status == "unavailable" {
                        note.push_str(" (sbpl preflight unavailable)")
                    }
                }
            }
        }
        Some(RunnerStartupDiagnostics {
            status: "xpc_error".to_string(),
            note,
            xpc_error: runner_result
                .as_ref()
                .and_then(|v| v.get("error"))
                .and_then(|v| v.as_str())
                .map(|s| s.to_string()),
            policy_preflight_status: policy_preflight
                .as_ref()
                .map(|p| p.status.clone()),
        })
    } else {
        None
    };

    let mut sandbox_log_capture = runner_pid.map(|pid| {
        // Capture unified-log evidence only when the runner PID is known.
        capture_sandbox_logs_last(pid, &runner_target.process_name, &log_last).unwrap_or_else(|err| {
            SandboxLogCapture {
                capture_status: "requested_unavailable".to_string(),
                tool_exit_code: 1,
                blocked_reason: None,
                stdout_parse_error: None,
                stdout_truncated: false,
                stdout_raw: None,
                stderr: err,
                stderr_truncated: false,
                observer: None,
                observed_deny: None,
                deny_events: None,
                step_denies: None,
            }
        })
    });

    if let (Some(ref mut capture), Some(steps)) = (
        sandbox_log_capture.as_mut(),
        runner_result
            .as_ref()
            .and_then(|v| v.get("steps"))
            .and_then(|v| v.as_array()),
    ) {
        if let Some(deny_events) = capture.deny_events.as_ref() {
            let matches = match_step_denies(steps, deny_events, runner_pid);
            if !matches.is_empty() {
                capture.step_denies = Some(matches);
            }
        }
    }

    let runner_sandbox_diagnostics = synthesize_runner_sandbox_diagnostics(
        &runner_outcome,
        runner_pid,
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
        policy_preflight,
        timeout_ms,
        log_last,
        runner_client,
        runner_result,
        sandbox_log_capture,
        sonoma_cross_check,
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
    } else if let Some(v) = data.runner_client.stdout_parse_error.as_ref() {
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

// Surface the first kernel sandbox deny that killed the worker so
// consumers can route by cause without parsing the full deny_events
// array. PID-filtered (no process-name fallback) to avoid attribution
// to concurrent runners. Returns None unless the outcome is
// runner_sandbox_denied, log capture succeeded, and at least one
// matching event is present.
fn synthesize_runner_sandbox_diagnostics(
    normalized_outcome: &str,
    worker_pid: Option<i64>,
    capture: Option<&SandboxLogCapture>,
) -> Option<RunnerSandboxDiagnostics> {
    if normalized_outcome != "runner_sandbox_denied" {
        return None;
    }
    let capture = capture?;
    if capture.capture_status != "captured" {
        return None;
    }
    let pid = worker_pid.and_then(|v| i32::try_from(v).ok())?;
    let deny_events = capture.deny_events.as_ref()?;
    let first = deny_events.iter().find(|e| e.pid == Some(pid))?;
    Some(RunnerSandboxDiagnostics {
        first_deny: Some(DenyEventSummary {
            operation: first.operation.clone(),
            path: first.path.clone(),
            raw_line: first.raw_line.clone(),
        }),
    })
}
