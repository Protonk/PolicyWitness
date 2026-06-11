//! Orchestrates a single run and builds the JSON envelope.
//!
//! The controller reads the request, selects a runner, invokes the Swift client,
//! and attaches best-effort evidence (sandbox logs, cross-check results).
//!
//! The host-side `sbpl-check` compile is not on the happy path. A non-compiling
//! policy is caught by the C worker — compile failure and apply failure both
//! surface as `sandbox_apply_failed` (the worker does not distinguish them) —
//! so the host runs `sbpl-check` only to disambiguate an `xpc_error`
//! (compiled-but-reply-blocked vs. never-compiled). This retires the
//! controller's old `bad_policy`
//! short-circuit for compile errors; `bad_policy` in a run now comes only from
//! the runner host's structural check (missing `sbpl_source` / wrong format).
//! Unified-log capture is best-effort and can be turned off per run with
//! `--no-log-capture`.

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
use crate::sandbox_log::{capture_sandbox_logs_last, match_step_denies, SandboxLogCapture};
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
        return Err(format!("request.json not found: {}", request_path.display()));
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

    // No host-side sbpl-check compile on the happy path. A non-compiling policy
    // is caught by the C worker: compile failure and apply failure both write
    // apply_rc=-1, which the host classifies as `sandbox_apply_failed`, so we
    // don't need a separate host compile to reject bad input (this retires the
    // controller's old `bad_policy` short-circuit for compile errors — that
    // outcome now comes only from the runner host's structural check). The one
    // non-redundant job left for sbpl-check is disambiguating an `xpc_error`
    // ("did the policy never compile, or did it compile and then block the XPC
    // reply?"), so it is run lazily in that branch alone (below). That removes
    // a full `sandbox_compile_string` from every run the runner can answer,
    // including the large-profile tail where the duplicate compile costs
    // seconds.
    let (runner_client, runner_result) = run_pw_runner_client(
        &runner_target.service_name,
        &request_path_for_run,
        timeout_ms,
        &runner_target.connection,
    )?;

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

    // The sbpl-check compile runs only here, to disambiguate a no-reply: the
    // runner could not answer, so we compile host-side to tell "never compiled"
    // (check fails) from "compiled but blocked the reply" (check ok). On every
    // other outcome `policy_check` stays None — the worker's own compile
    // is authoritative and a second host-side compile would be pure overhead.
    let mut policy_check: Option<PolicyCheckCapture> = None;
    let runner_startup_diagnostics = if runner_outcome == "xpc_error" {
        let check = match run_policy_check(&request_path_for_run) {
            Ok(report) => report,
            Err(err) => PolicyCheckCapture::unavailable(err),
        };
        let mut note = "runner did not reply; process may have exited during sandbox apply or policy may block Mach/XPC reply".to_string();
        match check.compiled {
            Some(true) => note.push_str(" (sbpl-check compiled ok)"),
            Some(false) => note.push_str(" (sbpl-check failed)"),
            None => {
                if check.status == "unavailable" {
                    note.push_str(" (sbpl-check unavailable)")
                }
            }
        }
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
        // `--no-log-capture`: skip the unified-log scan entirely. The scan
        // (`log show`) is archive-bound and costs seconds per run regardless
        // of the `--log-last` window, so callers that don't consume the deny
        // evidence opt out to reclaim it. `sandbox_log_capture` is then null
        // (the field stays present), and any outcome-gated diagnostics that
        // would have drawn on it (e.g. `first_deny`) degrade to null exactly
        // as they do when the observer is blocked/unavailable.
        None
    } else {
        runner_pid.map(|pid| {
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
// to concurrent runners.
//
// Contract: the outer `runner_sandbox_diagnostics` object is present
// for any outcome where a sandbox deny is the suspected cause
// (currently just `runner_sandbox_denied`); within it, `first_deny`
// is populated when a matching deny event was captured and `null`
// otherwise. Consumers can branch on `first_deny != null` without
// first checking that the outer object exists. For unrelated outcomes
// the outer object is `null` because no kernel-deny narrative applies.
fn synthesize_runner_sandbox_diagnostics(
    normalized_outcome: &str,
    worker_pid: Option<i64>,
    capture: Option<&SandboxLogCapture>,
) -> Option<RunnerSandboxDiagnostics> {
    if normalized_outcome != "runner_sandbox_denied" {
        return None;
    }
    let first_deny = capture
        .filter(|c| c.capture_status == "captured")
        .and_then(|c| {
            let pid = worker_pid.and_then(|v| i32::try_from(v).ok())?;
            let events = c.deny_events.as_ref()?;
            events.iter().find(|e| e.pid == Some(pid)).map(|e| DenyEventSummary {
                operation: e.operation.clone(),
                path: e.path.clone(),
                raw_line: e.raw_line.clone(),
            })
        });
    Some(RunnerSandboxDiagnostics { first_deny })
}

#[cfg(test)]
mod tests {
    // Deterministic coverage of the `first_deny` synthesis. The e2e
    // (tests/suites/witness_contract/runner_sandbox_diagnostics_on_denied.sh)
    // drives `runner_sandbox_denied` via the `worker_post_apply_kill_signal`
    // seam, but that only exercises the object-present / `first_deny: null`
    // shape — the seam-killed worker logs no kernel deny. The *populated*
    // first_deny path needs a real fatal-on-deny kernel event (unforgeable),
    // so these tests feed the synthesizer synthetic captures to pin the
    // matching branch logic that no e2e can reach.
    use super::*;
    use crate::sandbox_log::{SandboxDenyEvent, SandboxLogCapture};

    fn deny_event(pid: i32, op: &str, path: &str) -> SandboxDenyEvent {
        SandboxDenyEvent {
            pid: Some(pid),
            process: Some("PWRunner".to_string()),
            operation: Some(op.to_string()),
            path: Some(path.to_string()),
            raw_line: Some(format!("Sandbox: PWRunner({pid}) deny(1) {op} {path}")),
        }
    }

    fn capture_with(status: &str, events: Vec<SandboxDenyEvent>) -> SandboxLogCapture {
        SandboxLogCapture {
            capture_status: status.to_string(),
            tool_exit_code: 0,
            blocked_reason: None,
            stdout_parse_error: None,
            stdout_truncated: false,
            stdout_raw: None,
            stderr: String::new(),
            stderr_truncated: false,
            observer: None,
            observed_deny: Some(!events.is_empty()),
            deny_events: Some(events),
            step_denies: None,
        }
    }

    #[test]
    fn non_denied_outcome_yields_no_diagnostics() {
        // The outer object is reserved for the sandbox-deny narrative: any
        // other outcome must be None so consumers can read its mere presence
        // as "a kernel deny is the suspected cause".
        let cap = capture_with("captured", vec![deny_event(1234, "file-read-data", "/tmp/x")]);
        assert!(synthesize_runner_sandbox_diagnostics("ok", Some(1234), Some(&cap)).is_none());
        assert!(synthesize_runner_sandbox_diagnostics("runner_timeout", Some(1234), Some(&cap)).is_none());
    }

    #[test]
    fn denied_with_matching_pid_populates_first_deny() {
        let cap = capture_with(
            "captured",
            vec![
                deny_event(9999, "mach-lookup", "/other"), // wrong pid — must be ignored
                deny_event(1234, "file-read-data", "/tmp/x"), // the worker's deny
            ],
        );
        let diag = synthesize_runner_sandbox_diagnostics("runner_sandbox_denied", Some(1234), Some(&cap))
            .expect("runner_sandbox_denied must produce the outer diagnostics object");
        let first = diag
            .first_deny
            .expect("a deny event matching the worker pid must populate first_deny");
        assert_eq!(first.operation.as_deref(), Some("file-read-data"));
        assert_eq!(first.path.as_deref(), Some("/tmp/x"));
        assert!(first.raw_line.as_deref().unwrap_or_default().contains("deny(1)"));
    }

    #[test]
    fn denied_without_capture_is_present_object_with_null_first_deny() {
        // Contract: outer object present for runner_sandbox_denied; first_deny
        // null when there is no capture (e.g. --no-log-capture, or blocked).
        let diag = synthesize_runner_sandbox_diagnostics("runner_sandbox_denied", Some(1234), None)
            .expect("outer object present even when no capture is available");
        assert!(diag.first_deny.is_none());
    }

    #[test]
    fn denied_with_pid_mismatch_yields_null_first_deny() {
        // PID-filtered with no process-name fallback: a deny attributed to a
        // different PID must not be pinned on the worker.
        let cap = capture_with("captured", vec![deny_event(9999, "file-read-data", "/tmp/x")]);
        let diag = synthesize_runner_sandbox_diagnostics("runner_sandbox_denied", Some(1234), Some(&cap)).unwrap();
        assert!(diag.first_deny.is_none());
    }

    #[test]
    fn denied_with_uncaptured_status_yields_null_first_deny() {
        // Events from a non-`captured` observer run (blocked/error) are not
        // trustworthy evidence and must be ignored.
        let cap = capture_with("blocked", vec![deny_event(1234, "file-read-data", "/tmp/x")]);
        let diag = synthesize_runner_sandbox_diagnostics("runner_sandbox_denied", Some(1234), Some(&cap)).unwrap();
        assert!(diag.first_deny.is_none());
    }
}
