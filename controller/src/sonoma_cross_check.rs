//! Sonoma-era sandbox_check cross-check support.
//!
//! This module runs the sb_api_validator helper against the runner PID while
//! the runner is paused post-sandbox. It is best-effort evidence to compare
//! runner-reported outcomes with the system sandbox API.

use serde::Serialize;
use serde_json::{json, Value};
use std::collections::BTreeMap;
use std::ffi::OsString;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::thread;
use std::time::{Duration, Instant};

use crate::utils::truncate_output;

const SONOMA_CROSS_CHECK_PID_TIMEOUT_MS: u64 = 1500;
const SONOMA_CROSS_CHECK_PID_POLL_MS: u64 = 50;
const SONOMA_CROSS_CHECK_SETTLE_MS: u64 = 200;
const SONOMA_CROSS_CHECK_BASE_MS: u64 = 1000;
const SONOMA_CROSS_CHECK_PER_STEP_MS: u64 = 150;
const SONOMA_CROSS_CHECK_MIN_MS: u64 = 3000;
const SONOMA_CROSS_CHECK_MAX_MS: u64 = 15000;

#[derive(Clone)]
pub struct SonomaCrossCheckSpec {
    pub step_id: String,
    pub operation: String,
    pub filter_kind: String,
    pub filter_value: Option<String>,
}

#[derive(Clone)]
pub struct SonomaCrossCheckPlan {
    pub tool_path: PathBuf,
    pub process_name: String,
    pub wait_ms: u64,
    pub specs: Vec<SonomaCrossCheckSpec>,
}

#[derive(Serialize, Default)]
pub struct SonomaCrossCheckCounts {
    pub total: usize,
    pub checked: usize,
    pub skipped: usize,
    pub errors: usize,
    pub mismatches: usize,
}

#[derive(Serialize)]
pub struct SonomaCrossCheckStep {
    pub step_id: String,
    pub operation: String,
    pub filter_kind: String,
    pub filter_value: Option<String>,
    pub status: String,
    pub validator: Option<Value>,
    pub validator_outcome: Option<String>,
    pub expected_outcome: Option<String>,
    pub mismatch: Option<bool>,
    pub error: Option<String>,
}

#[derive(Serialize)]
pub struct SonomaCrossCheckReport {
    pub status: String,
    pub tool_path: Option<String>,
    pub runner_pid: Option<i64>,
    pub wait_ms: Option<u64>,
    pub error: Option<String>,
    pub counts: SonomaCrossCheckCounts,
    pub steps: Vec<SonomaCrossCheckStep>,
}

pub fn sonoma_cross_check_wait_ms(step_count: usize) -> u64 {
    // Wait time scales with steps but is clamped to keep runs bounded.
    let raw = SONOMA_CROSS_CHECK_BASE_MS + (SONOMA_CROSS_CHECK_PER_STEP_MS * step_count as u64);
    raw.clamp(SONOMA_CROSS_CHECK_MIN_MS, SONOMA_CROSS_CHECK_MAX_MS)
}

pub fn extract_sonoma_cross_check_specs(
    request_value: &Value,
) -> Result<Vec<SonomaCrossCheckSpec>, String> {
    let plan = request_value
        .get("probe_plan")
        .and_then(|v| v.as_array())
        .ok_or_else(|| "request.json missing probe_plan array".to_string())?;
    let mut specs = Vec::with_capacity(plan.len());
    for step in plan {
        let step_id = step
            .get("step_id")
            .and_then(|v| v.as_str())
            .ok_or_else(|| "probe_plan step missing step_id".to_string())?;
        let sandbox_check = step
            .get("sandbox_check")
            .and_then(|v| v.as_object())
            .ok_or_else(|| format!("step {step_id} missing sandbox_check"))?;
        let operation = sandbox_check
            .get("operation")
            .and_then(|v| v.as_str())
            .ok_or_else(|| format!("step {step_id} missing sandbox_check.operation"))?;
        let filter = sandbox_check
            .get("filter")
            .and_then(|v| v.as_object())
            .ok_or_else(|| format!("step {step_id} missing sandbox_check.filter"))?;
        let filter_kind = filter
            .get("kind")
            .and_then(|v| v.as_str())
            .ok_or_else(|| format!("step {step_id} missing sandbox_check.filter.kind"))?;
        let filter_value = filter
            .get("value")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string());
        specs.push(SonomaCrossCheckSpec {
            step_id: step_id.to_string(),
            operation: operation.to_string(),
            filter_kind: filter_kind.to_string(),
            filter_value,
        });
    }
    Ok(specs)
}

pub fn inject_sonoma_cross_check_instrumentation(
    request_value: &mut Value,
    wait_ms: u64,
) -> Result<(), String> {
    let obj = request_value
        .as_object_mut()
        .ok_or_else(|| "request.json must be a JSON object".to_string())?;
    let instrumentation = obj
        .entry("instrumentation")
        .or_insert_with(|| json!({}));
    let inst_obj = instrumentation
        .as_object_mut()
        .ok_or_else(|| "instrumentation must be a JSON object".to_string())?;
    let version = inst_obj
        .get("version")
        .and_then(|v| v.as_i64())
        .unwrap_or(1);
    if version != 1 {
        return Err(format!(
            "sonoma cross-check requires instrumentation.version=1 (got {version})"
        ));
    }
    inst_obj.insert("version".to_string(), json!(1));
    let ports = inst_obj.entry("ports").or_insert_with(|| json!([]));
    let ports_arr = ports
        .as_array_mut()
        .ok_or_else(|| "instrumentation.ports must be an array".to_string())?;
    // debug_wait keeps the runner alive long enough for sb_api_validator to query.
    ports_arr.push(json!({
        "kind": "debug_wait",
        "sleep_ms": wait_ms,
        "phase": "post_sandbox",
        "label": "sonoma_cross_check"
    }));
    Ok(())
}

fn wait_for_runner_pid(process_name: &str, timeout_ms: u64) -> Result<i64, String> {
    let deadline = Instant::now() + Duration::from_millis(timeout_ms);
    loop {
        let out = Command::new("/usr/bin/pgrep")
            .args(["-n", "-x", process_name])
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output();
        match out {
            Ok(output) => {
                if output.status.success() {
                    let stdout = String::from_utf8_lossy(&output.stdout);
                    if let Some(first) = stdout.lines().next() {
                        let pid = first
                            .trim()
                            .parse::<i64>()
                            .map_err(|e| format!("failed to parse pgrep pid: {e}"))?;
                        return Ok(pid);
                    }
                }
            }
            Err(e) => return Err(format!("failed to run pgrep: {e}")),
        }

        if Instant::now() >= deadline {
            break;
        }
        thread::sleep(Duration::from_millis(SONOMA_CROSS_CHECK_PID_POLL_MS));
    }
    Err(format!(
        "runner pid not found (process_name={process_name})"
    ))
}

fn sb_api_validator_outcome(value: &Value) -> Option<String> {
    let rc = value.get("rc").and_then(|v| v.as_i64())?;
    let errno = value.get("errno").and_then(|v| v.as_i64()).unwrap_or(0);
    if rc == 0 {
        Some("allow".to_string())
    } else if rc == 1 && errno == 0 {
        Some("deny".to_string())
    } else {
        Some("error".to_string())
    }
}

fn run_sb_api_validator(
    tool_path: &Path,
    pid: i64,
    spec: &SonomaCrossCheckSpec,
) -> SonomaCrossCheckStep {
    let mut step = SonomaCrossCheckStep {
        step_id: spec.step_id.clone(),
        operation: spec.operation.clone(),
        filter_kind: spec.filter_kind.clone(),
        filter_value: spec.filter_value.clone(),
        status: "error".to_string(),
        validator: None,
        validator_outcome: None,
        expected_outcome: None,
        mismatch: None,
        error: None,
    };

    // Filter kinds for which sandbox_check is known to drift from kernel
    // enforcement (see runner/ProbeRunner.swift::predictionUnavailableFilters
    // and tests/suites/witness_contract/harness/verify_filter_id.sh). The
    // cross-check skips them with a stable error string so consumers can
    // recognize "we deliberately didn't predict" apart from "the cross-check
    // hit a transient problem." Each entry here MUST be matched by the
    // same wire-name in the runner's predictionUnavailableFilters set.
    const PREDICTION_UNAVAILABLE_FILTERS: &[&str] = &[
        "iokit_registry_entry_class",
        "iokit_user_client_class",
        "sysctl_name",
    ];
    if PREDICTION_UNAVAILABLE_FILTERS.contains(&spec.filter_kind.as_str()) {
        step.status = "skipped".to_string();
        step.error = Some(
            "prediction_unavailable: sandbox_check is unreliable for this op+filter; \
             see runner_result.steps[].sandbox_check.outcome and the attempt result instead"
                .to_string(),
        );
        return step;
    }

    let filter_type = match spec.filter_kind.as_str() {
        "none" => "NONE",
        "path" => "PATH",
        "global_name" => "GLOBAL_NAME",
        "local_name" => "LOCAL_NAME",
        _ => {
            step.status = "skipped".to_string();
            step.error = Some(format!(
                "unsupported filter.kind {}",
                spec.filter_kind
            ));
            return step;
        }
    };

    // NONE takes no filter_value; everything else requires one.
    let filter_value_arg: Option<&str> = if spec.filter_kind == "none" {
        None
    } else {
        match spec.filter_value.as_deref() {
            Some(v) if !v.is_empty() => Some(v),
            _ => {
                step.status = "skipped".to_string();
                step.error = Some("filter.value missing".to_string());
                return step;
            }
        }
    };

    let mut args: Vec<OsString> = vec![
        OsString::from("--json"),
        OsString::from(pid.to_string()),
        OsString::from(&spec.operation),
        OsString::from(filter_type),
    ];
    if let Some(v) = filter_value_arg {
        args.push(OsString::from(v));
    }

    let out = Command::new(tool_path)
        .args(args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output();

    let out = match out {
        Ok(o) => o,
        Err(e) => {
            step.error = Some(format!("sb_api_validator failed to run: {e}"));
            return step;
        }
    };

    let exit_code = out.status.code().unwrap_or(1);
    let (stdout, stdout_truncated) = truncate_output(&out.stdout);
    let (stderr, stderr_truncated) = truncate_output(&out.stderr);

    if stdout.trim().is_empty() {
        step.error = Some(format!(
            "sb_api_validator produced no stdout (exit={exit_code})"
        ));
        return step;
    }

    let parsed = match serde_json::from_str::<Value>(&stdout) {
        Ok(v) => v,
        Err(e) => {
            let mut msg = format!("sb_api_validator stdout parse error: {e}");
            if stdout_truncated {
                msg.push_str(" (stdout truncated)");
            }
            if stderr_truncated {
                msg.push_str(" (stderr truncated)");
            }
            if !stderr.is_empty() {
                msg.push_str(&format!("; stderr={}", stderr.trim()));
            }
            step.error = Some(msg);
            return step;
        }
    };

    let kind = parsed.get("kind").and_then(|v| v.as_str()).unwrap_or("");
    step.validator = Some(parsed.clone());

    if kind == "sb_api_validator_error" {
        let err = parsed
            .get("error")
            .and_then(|v| v.as_str())
            .unwrap_or("unknown error");
        step.error = Some(format!("sb_api_validator error: {err}"));
        return step;
    }

    if kind != "sb_api_validator_result" {
        step.error = Some(format!("unexpected sb_api_validator kind: {kind}"));
        return step;
    }

    if let Some(outcome) = sb_api_validator_outcome(&parsed) {
        step.validator_outcome = Some(outcome.clone());
        if outcome == "allow" || outcome == "deny" {
            step.status = "ok".to_string();
        } else {
            step.status = "error".to_string();
            step.error = Some("sb_api_validator returned non-allow/deny rc".to_string());
        }
        return step;
    }

    step.error = Some("sb_api_validator missing rc/errno".to_string());
    step
}

fn update_sonoma_cross_check_counts(report: &mut SonomaCrossCheckReport) {
    if report.status == "unavailable" {
        return;
    }
    let mut blocked = report
        .error
        .as_ref()
        .map(|msg| {
            let msg = msg.to_ascii_lowercase();
            msg.contains("operation not permitted") || msg.contains("sandbox")
        })
        .unwrap_or(false);
    let mut counts = SonomaCrossCheckCounts::default();
    counts.total = report.steps.len();
    for step in &report.steps {
        match step.status.as_str() {
            "ok" => counts.checked += 1,
            "skipped" => counts.skipped += 1,
            _ => counts.errors += 1,
        }
        if step.mismatch == Some(true) {
            counts.mismatches += 1;
        }
        if let Some(err) = step.error.as_ref() {
            let msg = err.to_ascii_lowercase();
            if msg.contains("operation not permitted") || msg.contains("sandbox") {
                blocked = true;
            }
        }
    }
    report.counts = counts;
    if blocked {
        report.status = "blocked".to_string();
        return;
    }
    report.status = if report.error.is_some() {
        "error".to_string()
    } else if report.counts.mismatches > 0 {
        "mismatch".to_string()
    } else if report.counts.errors > 0 {
        "error".to_string()
    } else if report.counts.checked == 0 {
        "skipped".to_string()
    } else if report.counts.skipped > 0 {
        "partial".to_string()
    } else {
        "ok".to_string()
    };
}

pub fn apply_sonoma_cross_check_runner_results(
    report: &mut SonomaCrossCheckReport,
    runner_result: &Value,
) {
    if report.status == "unavailable" {
        return;
    }
    if report.runner_pid.is_none() {
        if let Some(pid) = runner_result.get("pid").and_then(|v| v.as_i64()) {
            report.runner_pid = Some(pid);
        }
    }

    let mut by_id: BTreeMap<String, String> = BTreeMap::new();
    if let Some(steps) = runner_result.get("steps").and_then(|v| v.as_array()) {
        for step in steps {
            let step_id = match step.get("step_id").and_then(|v| v.as_str()) {
                Some(v) => v,
                None => continue,
            };
            let outcome = step
                .get("sandbox_check")
                .and_then(|v| v.get("outcome"))
                .and_then(|v| v.as_str());
            if let Some(outcome) = outcome {
                by_id.insert(step_id.to_string(), outcome.to_string());
            }
        }
    }

    for step in report.steps.iter_mut() {
        if let Some(expected) = by_id.get(&step.step_id) {
            step.expected_outcome = Some(expected.clone());
            if let Some(actual) = step.validator_outcome.as_ref() {
                if (expected == "allow" || expected == "deny")
                    && (actual == "allow" || actual == "deny")
                {
                    step.mismatch = Some(actual != expected);
                }
            }
        }
    }
    update_sonoma_cross_check_counts(report);
}

pub fn sonoma_cross_check_unavailable(error: String) -> SonomaCrossCheckReport {
    SonomaCrossCheckReport {
        status: "unavailable".to_string(),
        tool_path: None,
        runner_pid: None,
        wait_ms: None,
        error: Some(error),
        counts: SonomaCrossCheckCounts::default(),
        steps: Vec::new(),
    }
}

pub fn sonoma_cross_check_skipped(reason: String) -> SonomaCrossCheckReport {
    SonomaCrossCheckReport {
        status: "skipped".to_string(),
        tool_path: None,
        runner_pid: None,
        wait_ms: None,
        error: Some(reason),
        counts: SonomaCrossCheckCounts::default(),
        steps: Vec::new(),
    }
}

pub fn run_sonoma_cross_check(plan: &SonomaCrossCheckPlan) -> SonomaCrossCheckReport {
    let mut report = SonomaCrossCheckReport {
        status: "error".to_string(),
        tool_path: Some(plan.tool_path.display().to_string()),
        runner_pid: None,
        wait_ms: Some(plan.wait_ms),
        error: None,
        counts: SonomaCrossCheckCounts::default(),
        steps: Vec::new(),
    };

    let pid_timeout =
        SONOMA_CROSS_CHECK_PID_TIMEOUT_MS.max(plan.wait_ms.saturating_sub(SONOMA_CROSS_CHECK_SETTLE_MS));
    let pid = match wait_for_runner_pid(&plan.process_name, pid_timeout) {
        Ok(pid) => pid,
        Err(err) => {
            report.error = Some(err);
            update_sonoma_cross_check_counts(&mut report);
            return report;
        }
    };
    report.runner_pid = Some(pid);

    thread::sleep(Duration::from_millis(SONOMA_CROSS_CHECK_SETTLE_MS));

    for spec in &plan.specs {
        report
            .steps
            .push(run_sb_api_validator(&plan.tool_path, pid, spec));
    }

    update_sonoma_cross_check_counts(&mut report);
    report
}
