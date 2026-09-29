//! Unified-log capture helpers for sandbox denials.
//!
//! The controller shells out to the embedded sandbox-log-observer tool and
//! attaches its JSON report to the run envelope as best-effort evidence.

use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;
use std::ffi::OsString;
use std::process::Command;

use crate::app_layout::resolve_contents_macos_tool;
use crate::log_capture::{
    self, Boundary, CollectionBudget, Cutoff, LogTimeout, ProcessCapture, Supervision,
};
use crate::utils::{JsonOutputCapture, capture_json_output};

#[derive(Serialize, Deserialize, Clone)]
pub struct SandboxDenyEvent {
    pub pid: Option<i32>,
    pub process: Option<String>,
    pub operation: Option<String>,
    pub path: Option<String>,
    pub raw_line: Option<String>,
}

/// References into capture.deny_events, not copies or uniquely identified
/// occurrences. Even a single candidate has no exact run/ordering guarantee.
#[derive(Serialize)]
pub struct SandboxLogStepDeny {
    pub event_index: usize,
    pub candidate_step_ids: Vec<String>,
    pub association: String,
    pub matching_evidence: Vec<SandboxLogMatchEvidence>,
}

/// The actual inputs that admitted a candidate. This is association evidence,
/// not a claim that the request operation executed or caused termination.
#[derive(Serialize)]
pub struct SandboxLogMatchEvidence {
    pub step_id: String,
    pub operation: String,
    pub operation_source: &'static str,
    pub requested_kind: String,
    pub requested_action: String,
    pub path: String,
    pub path_sources: Vec<String>,
}

pub const LOG_WINDOW_PAD_SECONDS: u64 = 2;

/// The interval requested from the observer. It is the runner client's own
/// wall-clock span, rounded outward to whole seconds and padded by two seconds
/// at each end to allow for client/archive clock differences. `log show` accepts
/// `YYYY-MM-DD HH:MM:SS+0000` and nothing finer. Reversed clock readings retain
/// their raw values but have no scan bounds. Ordered endpoints do not establish
/// clock continuity or complete log delivery. Events have no structured
/// timestamps here, and a PID can be reused inside the interval.
#[derive(Serialize, Clone, PartialEq, Debug)]
pub struct SandboxLogWindow {
    pub kind: &'static str,
    pub started_at_unix_ms: u64,
    pub ended_at_unix_ms: u64,
    pub pad_seconds: u64,
    pub start: Option<String>,
    pub end: Option<String>,
    pub event_timestamps_available: bool,
    pub exact_run_membership: bool,
    pub step_ordering: bool,
    pub pid_reuse_protection: bool,
}

impl SandboxLogWindow {
    /// Round outward, then pad both ends; even equal timestamps yield a scan.
    /// A clock rollback cannot be repaired by padding: withhold both bounds.
    pub fn runner_client_span(started_at_unix_ms: u64, ended_at_unix_ms: u64) -> Self {
        // Dividing u64 milliseconds first fits i64 seconds, including the pad.
        // Signed seconds preserve the exact lower bound near the Unix epoch.
        let start_s = (started_at_unix_ms / 1000) as i64 - LOG_WINDOW_PAD_SECONDS as i64;
        let end_s = ended_at_unix_ms.div_ceil(1000) as i64 + LOG_WINDOW_PAD_SECONDS as i64;
        Self {
            kind: "runner_client_span",
            started_at_unix_ms,
            ended_at_unix_ms,
            pad_seconds: LOG_WINDOW_PAD_SECONDS,
            start: (ended_at_unix_ms >= started_at_unix_ms).then(|| log_show_timestamp(start_s)),
            end: (ended_at_unix_ms >= started_at_unix_ms).then(|| log_show_timestamp(end_s)),
            event_timestamps_available: false,
            exact_run_membership: false,
            step_ordering: false,
            pid_reuse_protection: false,
        }
    }
}

/// Render a Unix second as the `%Y-%m-%d %H:%M:%S%z` form `log show` parses,
/// always in UTC with an explicit offset so local time and DST never move the
/// window. Fractional seconds are rejected by the tool, so none are emitted.
pub fn log_show_timestamp(unix_seconds: i64) -> String {
    let days = unix_seconds.div_euclid(86_400);
    let rem = unix_seconds.rem_euclid(86_400);
    let (hour, minute, second) = (rem / 3_600, (rem % 3_600) / 60, rem % 60);
    // Proleptic Gregorian civil date from days since 1970-01-01 (H. Hinnant).
    let z = days + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z.rem_euclid(146_097);
    let yoe = (doe - doe / 1_460 + doe / 36_524 - doe / 146_096) / 365;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let day = doy - (153 * mp + 2) / 5 + 1;
    let month = if mp < 10 { mp + 3 } else { mp - 9 };
    let year = yoe + era * 400 + i64::from(month <= 2);
    format!("{year:04}-{month:02}-{day:02} {hour:02}:{minute:02}:{second:02}+0000")
}

#[derive(Serialize)]
pub struct SandboxLogCapture {
    pub window: SandboxLogWindow,
    pub capture_status: String,
    pub tool_exit_code: i32,
    pub blocked_reason: Option<String>,
    #[serde(flatten)]
    pub output: JsonOutputCapture,
    pub observer: Option<Value>,
    pub observed_deny: Option<bool>,
    pub deny_events: Option<Vec<SandboxDenyEvent>>,
    pub step_denies: Option<Vec<SandboxLogStepDeny>>,
    pub supervision: Option<Supervision>,
    pub processing_cutoff: Option<Cutoff>,
}

fn observed_deny_from_observer_envelope(obj: &Value) -> Option<bool> {
    obj.get("data")
        .and_then(|v| v.get("observed_deny"))
        .and_then(|v| v.as_bool())
}

fn observer_log_error(obj: &Value) -> Option<String> {
    obj.get("data")
        .and_then(|v| v.get("log_error"))
        .and_then(|v| v.as_str())
        .map(|s| s.to_string())
}

fn observer_blocked_reason(obj: &Value) -> Option<String> {
    if let Some(reason) = obj
        .get("data")
        .and_then(|v| v.get("blocked_reason"))
        .and_then(|v| v.as_str())
    {
        return Some(reason.to_string());
    }
    let err = observer_log_error(obj)?;
    if err
        .to_ascii_lowercase()
        .contains("cannot run while sandboxed")
    {
        return Some(err);
    }
    None
}

fn observer_deny_events(obj: &Value) -> Option<Vec<SandboxDenyEvent>> {
    let value = obj.get("data")?.get("deny_events")?.clone();
    serde_json::from_value::<Vec<SandboxDenyEvent>>(value).ok()
}

/// Only authoritative spawned-worker metadata can identify a worker. Stored
/// replies remain readable without falling back to a host/client top-level PID.
pub fn worker_pid(result: Option<&Value>) -> Option<i32> {
    let pid = result?.get("runner_subprocess")?.get("pid")?.as_i64()?;
    i32::try_from(pid).ok().filter(|pid| *pid > 0)
}

// Candidate operation names from submitted intent, never the independently
// routed sandbox_check. No wildcard/prefix aliases. create can open an existing
// file for writing or create a new file. Unlisted operations remain unmatched.
fn attempt_operations(attempt: &Value) -> &'static [&'static str] {
    match (
        attempt.get("kind").and_then(Value::as_str),
        attempt.get("action").and_then(Value::as_str),
    ) {
        (Some("file"), Some("open_read" | "access")) => &["file-read-data"],
        (Some("file"), Some("open_write")) => &["file-write-data"],
        (Some("file"), Some("create")) => &["file-write-create", "file-write-data"],
        (Some("file"), Some("unlink")) => &["file-write-unlink"],
        (Some("mach_lookup"), Some("bootstrap_look_up")) => &["mach-lookup"],
        (Some("sysctl"), Some("read")) => &["sysctl-read"],
        (Some("exec"), Some("spawn")) => &["process-exec"],
        _ => &[],
    }
}

fn step_id(value: &Value) -> Option<&str> {
    value.get("step_id").and_then(Value::as_str)
}

#[cfg(test)]
pub fn match_step_denies(
    steps: &[Value],
    submitted_plan: &[Value],
    deny_events: &[SandboxDenyEvent],
    pid: Option<i32>,
) -> Vec<SandboxLogStepDeny> {
    bounded_step_denies(steps, submitted_plan, deny_events, pid, None).unwrap()
}

pub fn bounded_step_denies(
    steps: &[Value],
    submitted_plan: &[Value],
    deny_events: &[SandboxDenyEvent],
    pid: Option<i32>,
    budget: Option<CollectionBudget>,
) -> Result<Vec<SandboxLogStepDeny>, Cutoff> {
    let Some(pid) = pid.filter(|p| *p > 0) else {
        return Ok(Vec::new());
    };
    for (name, count, limit) in [
        (
            "reply_steps",
            steps.len(),
            log_capture::MAX_CORRELATION_STEPS,
        ),
        (
            "submitted_steps",
            submitted_plan.len(),
            log_capture::MAX_CORRELATION_STEPS,
        ),
        (
            "deny_events",
            deny_events.len(),
            log_capture::MAX_DENY_EVENTS,
        ),
    ] {
        if count > limit {
            return Err(Cutoff::limit("correlation_overflow", name, limit, count));
        }
    }
    // A duplicate ID on either side makes the provenance join unusable. Resolve
    // the join once, in reply order; each event then costs one pass over the
    // joined steps instead of a rescan of both arrays per step.
    let mut reply_ids: HashMap<&str, usize> = HashMap::new();
    for id in steps.iter().filter_map(step_id) {
        *reply_ids.entry(id).or_insert(0) += 1;
    }
    let mut requests: HashMap<&str, Option<&Value>> = HashMap::new();
    for request in submitted_plan {
        if let Some(id) = step_id(request) {
            requests
                .entry(id)
                .and_modify(|unique| *unique = None)
                .or_insert(Some(request));
        }
    }
    let joined: Vec<(&str, &Value, &Value)> = steps
        .iter()
        .filter_map(|step| {
            let id = step_id(step)?;
            if reply_ids.get(id) != Some(&1) {
                return None;
            }
            let request = (*requests.get(id)?)?;
            Some((id, step, request.get("attempt")?))
        })
        .collect();
    let mut out = Vec::new();
    let mut total_matches = 0;
    let mut total_bytes = 0usize;
    for (event_index, event) in deny_events.iter().enumerate() {
        if budget.is_some_and(CollectionBudget::expired) {
            return Err(Cutoff::reason(
                "deadline",
                Some("candidate association exceeded the collection deadline".into()),
            ));
        }
        if event.pid != Some(pid) {
            continue;
        }
        let (Some(operation), Some(path)) = (event.operation.as_deref(), event.path.as_deref())
        else {
            continue;
        };
        let mut candidates = Vec::new();
        let mut matching_evidence = Vec::new();
        for &(id, step, attempt) in &joined {
            if !attempt_operations(attempt).contains(&operation) {
                continue;
            }
            let mut path_sources = Vec::new();
            if attempt.get("target").and_then(Value::as_str) == Some(path) {
                path_sources.push("submitted_attempt.target".to_string());
            }
            for key in ["observed_path", "requested_path"] {
                if step
                    .get("attempt")
                    .and_then(|a| a.get(key))
                    .and_then(Value::as_str)
                    == Some(path)
                {
                    path_sources.push(format!("attempt.{key}"));
                }
            }
            // Host-resolved forms of the attempt target count only with their
            // observer/phase provenance. The block is always compact: a form
            // listed in same_as_input equals the input, a string is the derived
            // form, null derived nothing. A malformed block supplies no identity.
            if let Some(forms) = step.get("attempt").and_then(|a| a.get("path_diagnostics")) {
                let label = |key: &str| {
                    forms
                        .get(key)
                        .and_then(Value::as_str)
                        .filter(|text| !text.is_empty())
                };
                if let (Some(observer), Some(phase), Some(input), Some(listed)) = (
                    label("observer"),
                    label("phase"),
                    forms.get("input").and_then(Value::as_str),
                    forms.get("same_as_input").and_then(Value::as_array),
                ) {
                    for name in ["realpath_resolved", "parent_realpath_resolved"] {
                        let is_listed = listed.iter().any(|n| n.as_str() == Some(name));
                        let value = match (is_listed, forms.get(name)) {
                            (true, None) => Some(input),
                            (false, Some(form)) => form.as_str(),
                            _ => None,
                        };
                        if value == Some(path) {
                            path_sources.push(format!("{observer}.{phase}.{name}"));
                        }
                    }
                }
            }
            if !path_sources.is_empty() {
                total_matches += 1;
                if total_matches > log_capture::MAX_ASSOCIATIONS {
                    return Err(Cutoff::limit(
                        "correlation_overflow",
                        "matching_evidence",
                        log_capture::MAX_ASSOCIATIONS,
                        total_matches,
                    ));
                }
                // Conservative encoded/allocation allowance: duplicate step ID,
                // path, operation, kind/action, six-byte escaping and fixed keys,
                // path-source labels and per-event/reference overhead.
                let bytes = (2 * id.len()
                    + path.len()
                    + operation.len()
                    + attempt["kind"].as_str().unwrap_or("").len()
                    + attempt["action"].as_str().unwrap_or("").len())
                    * 6
                    + 1024;
                total_bytes = total_bytes.saturating_add(bytes);
                if total_bytes > log_capture::MAX_ASSOCIATION_BYTES {
                    return Err(Cutoff::limit(
                        "correlation_overflow",
                        "association_bytes",
                        log_capture::MAX_ASSOCIATION_BYTES,
                        total_bytes,
                    ));
                }
                candidates.push(id.to_string());
                matching_evidence.push(SandboxLogMatchEvidence {
                    step_id: id.to_string(),
                    operation: operation.to_string(),
                    operation_source: "submitted_attempt",
                    path: path.to_string(),
                    requested_kind: attempt["kind"].as_str().unwrap_or("").to_string(),
                    requested_action: attempt["action"].as_str().unwrap_or("").to_string(),
                    path_sources,
                });
            }
        }
        if !candidates.is_empty() {
            out.push(SandboxLogStepDeny {
                event_index,
                association: if candidates.len() > 1 {
                    "ambiguous"
                } else {
                    "candidate"
                }
                .to_string(),
                candidate_step_ids: candidates,
                matching_evidence,
            });
        }
    }
    if budget.is_some_and(CollectionBudget::expired) {
        return Err(Cutoff::reason(
            "deadline",
            Some("candidate association exceeded the collection deadline".into()),
        ));
    }
    Ok(out)
}

/// The observer is asked for exactly the window; `--last` never appears.
pub fn observer_argv(
    tool: OsString,
    pid: i64,
    process_name: &str,
    window: &SandboxLogWindow,
) -> Result<Vec<OsString>, String> {
    let (Some(start), Some(end)) = (&window.start, &window.end) else {
        return Err(
            "runner client wall clock moved backwards; deny-log interval unavailable".into(),
        );
    };
    Ok(vec![
        tool,
        OsString::from("--pid"),
        OsString::from(format!("{pid}")),
        OsString::from("--process-name"),
        OsString::from(process_name),
        OsString::from("--start"),
        OsString::from(start),
        OsString::from("--end"),
        OsString::from(end),
        OsString::from("--format"),
        OsString::from("json"),
    ])
}

#[cfg(test)]
pub fn capture_sandbox_logs(
    pid: i64,
    process_name: &str,
    window: SandboxLogWindow,
) -> Result<SandboxLogCapture, String> {
    capture_sandbox_logs_with_timeout(pid, process_name, window, LogTimeout::default())
}

pub fn capture_sandbox_logs_with_timeout(
    pid: i64,
    process_name: &str,
    window: SandboxLogWindow,
    timeout: LogTimeout,
) -> Result<SandboxLogCapture, String> {
    // Check before resolving or executing a helper. The raw clock readings
    // remain available even though no interval can be submitted to log show.
    if window.start.is_none() || window.end.is_none() {
        return Ok(SandboxLogCapture {
            window,
            capture_status: "invalid_window".into(),
            tool_exit_code: 1,
            blocked_reason: None,
            output: JsonOutputCapture::unavailable(
                "runner client wall clock moved backwards; deny-log scan not attempted".into(),
                crate::utils::OBSERVER_CAPTURE_BYTES,
            ),
            observer: None,
            observed_deny: None,
            deny_events: None,
            step_denies: None,
            supervision: None,
            processing_cutoff: None,
        });
    }
    let tool = resolve_contents_macos_tool("sandbox-log-observer")?;
    let argv = observer_argv(tool.into_os_string(), pid, process_name, &window)?;

    let budget = timeout.start()?;
    let mut command = Command::new(&argv[0]);
    command
        .args(&argv[1..])
        .arg("--collection-budget")
        .arg(budget.argument());
    Ok(parse_supervised_observer(
        log_capture::capture(&mut command, budget, Boundary::Observer),
        window,
        pid,
        process_name,
    ))
}

fn cutoff_status(report: &Supervision) -> &'static str {
    match report.cutoff.as_ref().map(|c| c.reason.as_str()) {
        Some("deadline") => "timeout",
        Some("output_overflow" | "event_overflow" | "serialization_overflow") => "overflow",
        Some("launch_error") => "requested_unavailable",
        Some("process_exit") => "error",
        _ => "capture_error",
    }
}

pub(crate) fn parse_supervised_observer(
    raw: ProcessCapture,
    window: SandboxLogWindow,
    pid: i64,
    process_name: &str,
) -> SandboxLogCapture {
    use std::os::unix::process::ExitStatusExt;
    let status =
        std::process::ExitStatus::from_raw(raw.supervision.process.exit_code.unwrap_or(1) << 8);
    let out = std::process::Output {
        status,
        stdout: raw.stdout,
        stderr: raw.stderr,
    };
    let mut capture = parse_observer_output(&out, window);
    let report = raw.supervision;
    capture.output.stdout_bytes_received = Some(report.stdout.bytes_read);
    capture.output.stderr_bytes_received = Some(report.stderr.bytes_read);
    capture.output.stdout_bytes_retained = Some(report.stdout.bytes_retained);
    capture.output.stderr_bytes_retained = Some(report.stderr.bytes_retained);
    capture.output.stderr_truncated = report.stderr.truncated;
    if report.stdout.truncated {
        capture.output.stdout_truncated = true;
        capture.output.stdout_capture_error =
            Some("observer stdout exceeded its streaming limit".into());
        capture.output.stdout_raw = Some(String::from_utf8_lossy(&out.stdout).into_owned());
        capture.observer = None;
        capture.observed_deny = None;
        capture.deny_events = None;
    }
    // Shape-valid, intact replies remain diagnostic evidence even after a failed
    // wait, interrupted pipe or inner query. No extraction from JSON fragments.
    let data = capture.observer.as_ref().and_then(|o| o.get("data"));
    let inner = data
        .and_then(|d| d.get("collection"))
        .and_then(|v| serde_json::from_value::<Supervision>(v.clone()).ok());
    let shape_valid = data.is_some_and(|d| {
        d["observer_schema_version"] == 1
            && d["mode"] == "show"
            && d["pid"].as_i64() == Some(pid)
            && d["process_name"].as_str() == Some(process_name)
            && d["log_truncated"].is_boolean()
            && d["log_stdout"].is_string()
            && d["log_stderr"].is_string()
            && capture
                .deny_events
                .as_ref()
                .is_some_and(|events| d["observed_deny"].as_bool() == Some(!events.is_empty()))
            && [
                "process_name",
                "predicate",
                "start",
                "end",
                "last",
                "plan_id",
                "row_id",
                "correlation_id",
            ]
            .iter()
            .all(|key| {
                d.get(key).is_none_or(|v| {
                    v.is_null()
                        || v.as_str()
                            .is_some_and(|s| s.len() <= log_capture::MAX_OBSERVER_METADATA_BYTES)
                })
            })
            && inner
                .as_ref()
                .is_some_and(|r| d["log_rc"].as_i64() == r.process.exit_code.map(i64::from))
    }) && inner.as_ref().is_some_and(|inner| {
        inner.boundary == Boundary::LogShow
            && inner.reserve_ms == log_capture::LOG_REPORT_RESERVE_MS
            && inner.budget.deadline_monotonic_ns == report.budget.deadline_monotonic_ns
            && inner.budget.started_monotonic_ns == report.budget.started_monotonic_ns
            && inner.budget.timeout_ms == report.budget.timeout_ms
            && inner.budget.timeout_source == report.budget.timeout_source
            && inner.stdout.limit_bytes == log_capture::LOG_STDOUT_BYTES
            && inner.stderr.limit_bytes == log_capture::LOG_STDERR_BYTES
    });
    if !report.complete() {
        capture.capture_status = cutoff_status(&report).into();
    } else if capture.processing_cutoff.is_some() {
        capture.capture_status = "overflow".into();
    } else if !shape_valid {
        if capture.observer.is_some() {
            capture.capture_status = "invalid_reply".into();
        }
    } else if let Some(inner) = inner {
        if !inner.complete() {
            capture.capture_status = if capture.blocked_reason.is_some() {
                "blocked"
            } else {
                cutoff_status(&inner)
            }
            .into();
        } else if data.is_some_and(|d| d["log_truncated"] == true) {
            capture.capture_status = "capture_error".into();
        }
    }
    if capture.capture_status == "captured" && report.budget.expired() {
        capture.capture_status = "timeout".into();
        capture.processing_cutoff = Some(Cutoff::reason(
            "deadline",
            Some("observer reply parsing exceeded the collection deadline".into()),
        ));
    }
    capture.supervision = Some(report);
    capture
}

/// The observer mirrors the window it actually handed to `log show`. A reply
/// that scanned a different interval, or a trailing one, is not evidence for
/// this run's window, whatever else it carries.
fn observer_window_matches(obj: &Value, window: &SandboxLogWindow) -> bool {
    let Some(data) = obj.get("data") else {
        return false;
    };
    window.start.is_some()
        && window.end.is_some()
        && data.get("start").and_then(Value::as_str) == window.start.as_deref()
        && data.get("end").and_then(Value::as_str) == window.end.as_deref()
        && data.get("last").is_none_or(Value::is_null)
}

pub(crate) fn parse_observer_output(
    out: &std::process::Output,
    window: SandboxLogWindow,
) -> SandboxLogCapture {
    let exit_code = out.status.code().unwrap_or(1);

    let mut output;
    let parsed;
    let mut processing_cutoff = None;
    // Count JSON punctuation outside strings before allocating a Value tree.
    // This bounds object/array expansion even for a malformed helper response.
    let mut quoted = false;
    let mut escaped = false;
    let mut tokens = 0;
    for b in &out.stdout {
        if quoted {
            if escaped {
                escaped = false;
            } else if *b == b'\\' {
                escaped = true;
            } else if *b == b'"' {
                quoted = false;
            }
        } else if *b == b'"' {
            quoted = true;
        } else if matches!(b, b'{' | b'[' | b',' | b':') {
            tokens += 1;
            if tokens > log_capture::MAX_OBSERVER_JSON_TOKENS {
                processing_cutoff = Some(Cutoff::limit(
                    "json_structure_overflow",
                    "json_punctuation",
                    log_capture::MAX_OBSERVER_JSON_TOKENS,
                    tokens,
                ));
                break;
            }
        }
    }
    if processing_cutoff.is_some() {
        output = JsonOutputCapture::unavailable(
            "observer JSON structure limit exceeded".into(),
            crate::utils::OBSERVER_CAPTURE_BYTES,
        );
        let (prefix, truncated) =
            crate::utils::truncate_output(&out.stdout, crate::utils::OBSERVER_CAPTURE_BYTES);
        output.stdout_raw = Some(prefix);
        output.stdout_truncated = truncated;
        output.stdout_bytes_received = Some(out.stdout.len());
        output.stdout_bytes_retained =
            Some(out.stdout.len().min(crate::utils::OBSERVER_CAPTURE_BYTES));
        let (stderr, stderr_truncated) =
            crate::utils::truncate_output(&out.stderr, log_capture::OBSERVER_STDERR_BYTES);
        output.stderr = stderr;
        output.stderr_truncated = stderr_truncated;
        output.stderr_bytes_received = Some(out.stderr.len());
        output.stderr_bytes_retained =
            Some(out.stderr.len().min(log_capture::OBSERVER_STDERR_BYTES));
        parsed = None;
    } else {
        (output, parsed) = capture_json_output(
            out,
            "sandbox-log-observer",
            crate::utils::OBSERVER_CAPTURE_BYTES,
        );
    }

    let observed_deny = parsed
        .as_ref()
        .and_then(observed_deny_from_observer_envelope);
    let observer_log_error = parsed.as_ref().and_then(observer_log_error);
    let blocked_reason = parsed.as_ref().and_then(observer_blocked_reason);
    let deny_events = parsed
        .as_ref()
        .filter(|v| {
            v.pointer("/data/deny_events")
                .and_then(Value::as_array)
                .is_none_or(|events| events.len() <= log_capture::MAX_DENY_EVENTS)
        })
        .and_then(observer_deny_events);
    let window_mirrored = parsed
        .as_ref()
        .is_some_and(|obj| observer_window_matches(obj, &window));

    if parsed
        .as_ref()
        .and_then(|v| v.pointer("/data/deny_events"))
        .and_then(Value::as_array)
        .is_some_and(|events| events.len() > log_capture::MAX_DENY_EVENTS)
    {
        processing_cutoff = Some(Cutoff::limit(
            "event_overflow",
            "deny_events",
            log_capture::MAX_DENY_EVENTS,
            parsed.as_ref().unwrap()["data"]["deny_events"]
                .as_array()
                .unwrap()
                .len(),
        ));
        // Preserve the intact reply as diagnostic evidence, without allocating
        // another derived event array beyond the declared limit.
    }
    let capture_status = if processing_cutoff.is_some() {
        "overflow".to_string()
    } else if output.stdout_capture_error.is_some() {
        "capture_error".to_string()
    } else if output.stdout_parse_error.is_some() {
        "parse_error".to_string()
    } else if blocked_reason.is_some() {
        "blocked".to_string()
    } else if observer_log_error.is_some() {
        "error".to_string()
    } else if exit_code != 0 {
        "error".to_string()
    } else if observed_deny.is_some() && deny_events.is_some() {
        if window_mirrored {
            "captured".to_string()
        } else {
            "window_mismatch".to_string()
        }
    } else if parsed.is_some() {
        "invalid_reply".to_string()
    } else {
        "error".to_string()
    };

    SandboxLogCapture {
        window,
        capture_status,
        tool_exit_code: exit_code,
        blocked_reason,
        output,
        observer: parsed,
        observed_deny,
        deny_events,
        step_denies: None,
        supervision: None,
        processing_cutoff,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn supervised_receiver_retains_failed_inner_evidence_and_rejects_bad_shapes() {
        let line = "Sandbox: pw-probe-runner(42) deny(1) file-write-data /attempt";
        for scenario in [
            "complete",
            "nonzero",
            "overflow",
            "bad_pid",
            "missing_collection",
            "wrong_budget",
            "wrong_reserve",
            "bad_observed",
            "bad_exit",
            "bad_metadata",
        ] {
            let budget = LogTimeout {
                milliseconds: 3000,
                source: log_capture::TimeoutSource::Cli,
            }
            .start()
            .unwrap();
            let mut inner = Command::new("/usr/bin/python3");
            inner.args(["-c", "import os,sys; os.write(1,sys.argv[1].encode()+b'\\n'); os.write(1,b'x'*int(sys.argv[2])); sys.exit(int(sys.argv[3]))", line,
                if scenario == "overflow" { "1048577" } else { "0" }, if scenario == "nonzero" { "7" } else { "0" }]);
            let inner = log_capture::capture_reserving(
                &mut inner,
                budget,
                Boundary::LogShow,
                log_capture::LOG_REPORT_RESERVE_MS,
            );
            let window = SandboxLogWindow::runner_client_span(1000, 2500);
            let mut body = json!({"kind":"sandbox_log_observer_report", "data": {
                "observer_schema_version":1, "mode":"show", "pid":42, "process_name":"pw-probe-runner",
                "start":window.start, "end":window.end, "last":null,
                "log_rc":inner.supervision.process.exit_code, "log_error":inner.supervision.cutoff.as_ref().map(|c| &c.reason),
                "log_truncated":inner.supervision.stdout.truncated, "log_stdout":String::from_utf8_lossy(&inner.stdout), "log_stderr":"",
                "observed_deny":true, "deny_events":[{"pid":42,"process":"pw-probe-runner", "operation":"file-write-data", "path":"/attempt", "raw_line":line}],
                "collection":inner.supervision,
            }});
            match scenario {
                "bad_pid" => body["data"]["pid"] = json!(99),
                "bad_observed" => body["data"]["observed_deny"] = json!(false),
                "bad_exit" => body["data"]["log_rc"] = json!(19),
                "bad_metadata" => {
                    body["data"]["predicate"] =
                        json!("x".repeat(log_capture::MAX_OBSERVER_METADATA_BYTES + 1))
                }
                "missing_collection" => {
                    body["data"].as_object_mut().unwrap().remove("collection");
                }
                "wrong_budget" => {
                    body["data"]["collection"]["budget"]["deadline_monotonic_ns"] =
                        json!(budget.deadline_monotonic_ns + 1)
                }
                "wrong_reserve" => body["data"]["collection"]["reserve_ms"] = json!(0),
                _ => (),
            }
            // File-backed stdin avoids argv limits for the intact, bounded
            // diagnostic reply after inner overflow. The fixture stdout is the
            // only receiver transport.
            let file = std::env::temp_dir().join(format!(
                "pw-observer-reply-{}-{scenario}.json",
                std::process::id()
            ));
            std::fs::write(&file, serde_json::to_vec(&body).unwrap()).unwrap();
            let mut observer = Command::new("/bin/cat");
            observer.arg(&file);
            let raw = log_capture::capture(&mut observer, budget, Boundary::Observer);
            std::fs::remove_file(file).unwrap();
            let received = parse_supervised_observer(raw, window, 42, "pw-probe-runner");
            let expected = match scenario {
                "complete" => "captured",
                "nonzero" => "error",
                "overflow" => "overflow",
                _ => "invalid_reply",
            };
            assert_eq!(received.capture_status, expected, "{scenario}");
            assert_eq!(
                received.observer.as_ref(),
                Some(&body),
                "intact diagnostic reply must survive"
            );
            assert_eq!(received.deny_events.as_ref().unwrap().len(), 1);
            assert!(received.step_denies.is_none());
            assert!(received.supervision.as_ref().unwrap().complete());
        }
    }

    #[test]
    fn incomplete_outer_reply_remains_raw_and_has_no_recovered_events() {
        let budget = LogTimeout {
            milliseconds: 200,
            source: log_capture::TimeoutSource::Cli,
        }
        .start()
        .unwrap();
        let mut observer = Command::new("/usr/bin/python3");
        observer.args([
            "-c",
            "import os,time; os.write(1,b'{\"data\":'); time.sleep(60)",
        ]);
        let raw = log_capture::capture(&mut observer, budget, Boundary::Observer);
        let capture = parse_supervised_observer(
            raw,
            SandboxLogWindow::runner_client_span(0, 1),
            42,
            "pw-probe-runner",
        );
        assert_eq!(capture.capture_status, "timeout");
        assert_eq!(capture.output.stdout_raw.as_deref(), Some("{\"data\":"));
        assert!(
            capture.observer.is_none()
                && capture.deny_events.is_none()
                && capture.step_denies.is_none()
        );
        assert_eq!(
            capture.supervision.as_ref().unwrap().cleanup.outcome,
            "group_absent"
        );
    }

    #[test]
    fn derived_json_and_candidate_allocations_are_bounded() {
        use std::os::unix::process::ExitStatusExt;
        let stdout = format!("[{}0]", "0,".repeat(log_capture::MAX_OBSERVER_JSON_TOKENS));
        let output = std::process::Output {
            status: std::process::ExitStatus::from_raw(0),
            stdout: stdout.into_bytes(),
            stderr: vec![],
        };
        let capture = parse_observer_output(&output, SandboxLogWindow::runner_client_span(0, 1));
        assert_eq!(capture.capture_status, "overflow");
        assert!(capture.observer.is_none());
        assert_eq!(
            capture.processing_cutoff.as_ref().unwrap().reason,
            "json_structure_overflow"
        );
        let steps: Vec<_> = (0..256)
            .map(|i| json!({"step_id":format!("s{i}")}))
            .collect();
        let plan: Vec<_> = (0..256).map(|i| json!({"step_id":format!("s{i}"), "attempt":{"kind":"file","action":"open_read","target":format!("/p{i}")}})).collect();
        let events: Vec<_> = (0..256)
            .map(|i| SandboxDenyEvent {
                pid: Some(42),
                process: Some("pw-probe-runner".into()),
                operation: Some("file-read-data".into()),
                path: Some(format!("/p{i}")),
                raw_line: None,
            })
            .collect();
        let matches = bounded_step_denies(&steps, &plan, &events, Some(42), None).unwrap();
        assert_eq!(matches.len(), 256);
        for (i, matching) in matches.iter().enumerate() {
            assert_eq!(matching.candidate_step_ids, [format!("s{i}")]);
        }
        let identical_plan: Vec<_> = plan
            .iter()
            .map(|p| {
                let mut p = p.clone();
                p["attempt"]["target"] = json!("/p0");
                p
            })
            .collect();
        let repeated = vec![events[0].clone(); 256];
        let cutoff = bounded_step_denies(&steps, &identical_plan, &repeated, Some(42), None)
            .err()
            .expect("candidate expansion must be bounded");
        assert_eq!(cutoff.reason, "correlation_overflow");
        assert!(cutoff.observed.unwrap() > cutoff.limit.unwrap());
        assert_eq!(cutoff.stream.as_deref(), Some("matching_evidence"));
        let long_path = format!("/{}", "x".repeat(510));
        let long_plan: Vec<_> = plan
            .iter()
            .map(|p| {
                let mut p = p.clone();
                p["attempt"]["target"] = json!(long_path);
                p
            })
            .collect();
        let mut long_event = events[0].clone();
        long_event.path = Some(long_path);
        let cutoff =
            bounded_step_denies(&steps, &long_plan, &vec![long_event; 256], Some(42), None)
                .err()
                .expect("correlation limit must reject");
        assert_eq!(cutoff.stream.as_deref(), Some("association_bytes"));
        assert_eq!(
            cutoff.limit,
            Some(log_capture::MAX_ASSOCIATION_BYTES as u64)
        );
        let extra_steps = vec![steps[0].clone(); 257];
        assert_eq!(
            bounded_step_denies(&extra_steps, &plan, &events, Some(42), None)
                .err()
                .expect("correlation limit must reject")
                .stream
                .as_deref(),
            Some("reply_steps")
        );
        let extra_plan = vec![plan[0].clone(); 257];
        assert_eq!(
            bounded_step_denies(&steps, &extra_plan, &events, Some(42), None)
                .err()
                .expect("correlation limit must reject")
                .stream
                .as_deref(),
            Some("submitted_steps")
        );
    }

    #[test]
    fn maximum_event_volume_correlates_within_the_default_allowance() {
        // The provenance join is resolved once per capture. Rescanning both step
        // arrays for every event made 8192 worker events against 256 steps
        // exhaust the production allowance in an unoptimized build.
        let steps: Vec<_> = (0..256)
            .map(|i| json!({"step_id": format!("s{i}")}))
            .collect();
        let plan: Vec<_> = (0..256).map(|i| json!({"step_id": format!("s{i}"), "attempt": {"kind": "file", "action": "open_read", "target": format!("/p{i}")}})).collect();
        let events: Vec<_> = (0..log_capture::MAX_DENY_EVENTS)
            .map(|i| SandboxDenyEvent {
                pid: Some(42),
                process: Some("pw-probe-runner".into()),
                operation: Some("file-read-data".into()),
                path: Some(if i < 256 {
                    format!("/p{i}")
                } else {
                    format!("/unplanned/{i}")
                }),
                raw_line: None,
            })
            .collect();
        let budget = LogTimeout::default().start().unwrap();
        let matches = bounded_step_denies(&steps, &plan, &events, Some(42), Some(budget))
            .expect("maximum event volume must correlate inside the default allowance");
        assert_eq!(matches.len(), 256);
        for (i, matching) in matches.iter().enumerate() {
            assert_eq!(matching.event_index, i);
            assert_eq!(matching.candidate_step_ids, [format!("s{i}")]);
        }
    }

    #[test]
    fn empty_correlation_does_not_bypass_the_shared_deadline() {
        let budget = LogTimeout::parse("1").unwrap().start().unwrap();
        std::thread::sleep(std::time::Duration::from_millis(3));
        let cutoff = bounded_step_denies(&[], &[], &[], Some(42), Some(budget))
            .err()
            .expect("expired budget");
        assert_eq!(cutoff.reason, "deadline");
    }

    #[test]
    fn unfamiliar_diagnostics_survive_observer_capture() {
        let records = crate::utils::transport_diagnostics();
        let original = serde_json::json!({"data": {"diagnostics": records,
            "observed_deny": false, "deny_events": [], "log_error": "independent collection failure"}});
        for mode in ["valid", "oversized"] {
            let output = crate::utils::receiver_fixture(
                &original.to_string(),
                mode,
                crate::utils::OBSERVER_CAPTURE_BYTES,
            );
            let capture =
                parse_observer_output(&output, SandboxLogWindow::runner_client_span(0, 1));
            let wire = serde_json::to_value(&capture).unwrap();
            if mode == "valid" {
                assert_eq!(wire["observer"], original);
                assert_eq!(wire["observed_deny"], false);
                assert_eq!(capture.capture_status, "error");
                assert_eq!(wire["deny_events"], serde_json::json!([]));
            } else {
                assert!(serde_json::from_slice::<Value>(&output.stdout).is_ok());
                assert!(capture.observer.is_none());
                assert!(capture.observed_deny.is_none());
                assert_eq!(capture.capture_status, "capture_error");
                assert!(capture.output.stdout_parse_error.is_none());
            }
        }
    }

    #[test]
    fn observer_receiver_uses_original_bytes_and_reports_local_loss() {
        use crate::utils::{OBSERVER_CAPTURE_BYTES, receiver_fixture};
        for (mode, expected) in [
            ("valid", "captured"),
            ("oversized", "capture_error"),
            ("utf8", "parse_error"),
            ("malformed", "parse_error"),
            ("empty", "error"),
            ("missing", "invalid_reply"),
        ] {
            let original = receiver_fixture(
                r#"{"data":{"observed_deny":true,"deny_events":[],"code":97319,
                    "start":"1969-12-31 23:59:58+0000","end":"1970-01-01 00:00:03+0000","last":null}}"#,
                mode,
                crate::utils::OBSERVER_CAPTURE_BYTES,
            );
            let capture =
                parse_observer_output(&original, SandboxLogWindow::runner_client_span(0, 1));
            let wire = serde_json::to_value(&capture).unwrap();
            assert_eq!(capture.capture_status, expected, "{mode}");
            assert_eq!(wire["stdout_bytes_received"], original.stdout.len());
            assert_eq!(
                wire["stdout_bytes_retained"],
                original.stdout.len().min(OBSERVER_CAPTURE_BYTES)
            );
            assert_eq!(wire["stderr_bytes_received"], original.stderr.len());
            assert_eq!(wire["stderr_bytes_retained"], OBSERVER_CAPTURE_BYTES);
            assert_eq!(
                capture.observed_deny,
                if mode == "valid" { Some(true) } else { None }
            );
            if mode == "oversized" {
                assert!(serde_json::from_slice::<Value>(&original.stdout).is_ok());
                assert!(capture.output.stdout_capture_error.is_some());
                assert!(capture.output.stdout_parse_error.is_none());
            }
            if mode == "valid" {
                assert_eq!(capture.observer.unwrap()["data"]["code"], 97319);
            } else if mode == "missing" {
                assert_eq!(capture.observer.unwrap()["data"]["code"], 97319);
            } else {
                assert!(capture.observer.is_none());
                assert!(capture.deny_events.is_none());
            }
        }
    }

    fn deny(pid: Option<i32>, op: &str, path: &str) -> SandboxDenyEvent {
        SandboxDenyEvent {
            pid,
            process: Some("pw-probe-runner".into()),
            operation: Some(op.into()),
            path: Some(path.into()),
            raw_line: Some(format!("fixture {pid:?} {op} {path}")),
        }
    }
    fn request(id: &str, action: &str, target: &str) -> Value {
        json!({"step_id": id, "sandbox_check": {"operation": "file-read-data", "filter": {"value": "/query"}},
               "attempt": {"kind": "file", "action": action, "target": target}})
    }
    fn reply(id: &str) -> Value {
        json!({"step_id": id, "sandbox_check": {"operation": "file-read-data", "filter_value": "/query"},
               "attempt": {"requested_path": "/attempt", "observed_path": "/observed"}})
    }
    #[test]
    fn only_authoritative_positive_worker_pid_is_usable() {
        for value in [
            json!({"pid": 12}),
            json!({"pid": 12, "runner_subprocess": null}),
            json!({"runner_subprocess": {"pid": 0}}),
            json!({"runner_subprocess": {"pid": -1}}),
            json!({"runner_subprocess": {"pid": 2147483648i64}}),
        ] {
            assert_eq!(worker_pid(Some(&value)), None);
        }
        assert_eq!(
            worker_pid(Some(&json!({"pid": 12, "runner_subprocess": {"pid": 34}}))),
            Some(34)
        );
    }
    #[test]
    fn attempt_operation_and_paths_are_independent_of_query() {
        let steps = [reply("s")];
        let plan = [request("s", "open_write", "/attempt")];
        let events = [
            deny(Some(42), "file-read-data", "/attempt"),
            deny(Some(42), "file-write-data", "/query"),
            deny(Some(42), "file-write-data", "/observed"),
        ];
        let out = match_step_denies(&steps, &plan, &events, Some(42));
        assert_eq!(out.len(), 1);
        assert_eq!(out[0].event_index, 2);
        assert_eq!(out[0].candidate_step_ids, ["s"]);
        assert_eq!(out[0].association, "candidate");
    }
    #[test]
    fn missing_or_mismatched_pid_and_operation_cannot_match() {
        let steps = [reply("s")];
        let plan = [request("s", "open_read", "/attempt")];
        for pid in [None, Some(7)] {
            assert!(
                match_step_denies(
                    &steps,
                    &plan,
                    &[deny(pid, "file-read-data", "/attempt")],
                    Some(42)
                )
                .is_empty()
            );
        }
        for pid in [None, Some(0), Some(-1)] {
            assert!(
                match_step_denies(
                    &steps,
                    &plan,
                    &[deny(Some(42), "file-read-data", "/attempt")],
                    pid
                )
                .is_empty()
            );
        }
        for op in ["file-write-data", "file-read-metadata", "file-read*"] {
            assert!(
                match_step_denies(&steps, &plan, &[deny(Some(42), op, "/attempt")], Some(42))
                    .is_empty()
            );
        }
        let mut missing = deny(Some(42), "file-read-data", "/attempt");
        missing.operation = None;
        assert!(match_step_denies(&steps, &plan, &[missing], Some(42)).is_empty());
    }
    #[test]
    fn repeated_attempts_reference_one_event_with_ambiguous_candidates() {
        let steps = [reply("second"), reply("first")];
        let plan = [
            request("first", "open_write", "/attempt"),
            request("second", "open_write", "/attempt"),
        ];
        let events = [deny(Some(42), "file-write-data", "/attempt")];
        let out = match_step_denies(&steps, &plan, &events, Some(42));
        assert_eq!(out.len(), 1);
        assert_eq!(out[0].event_index, 0);
        assert_eq!(out[0].candidate_step_ids, ["second", "first"]);
        assert_eq!(out[0].association, "ambiguous");
        let raw = serde_json::to_value(out).unwrap();
        assert!(raw[0].get("deny_events").is_none());
        assert_eq!(raw[0]["matching_evidence"][0]["step_id"], "second");
        assert_eq!(
            raw[0]["matching_evidence"][0]["operation_source"],
            "submitted_attempt"
        );
        assert_eq!(
            raw[0]["matching_evidence"][0]["requested_action"],
            "open_write"
        );
        assert_eq!(
            raw[0]["matching_evidence"][0]["operation"],
            "file-write-data"
        );
        assert_eq!(raw[0]["matching_evidence"][0]["path"], "/attempt");
        assert!(
            raw[0]["matching_evidence"][0]["path_sources"]
                .as_array()
                .unwrap()
                .contains(&serde_json::json!("submitted_attempt.target"))
        );
    }
    #[test]
    fn host_resolved_attempt_forms_supply_identity_only_with_provenance() {
        let plan = [request("s", "open_read", "/link/file")];
        let event = [deny(Some(42), "file-read-data", "/real/file")];
        let block = |provenance: bool| {
            let mut forms = json!({"input": "/link/file", "same_as_input": [],
                "realpath_resolved": "/real/file", "parent_realpath_resolved": "/real/file"});
            if provenance {
                forms["observer"] = json!("runner_host");
                forms["phase"] = json!("after_orchestration");
            }
            json!({"step_id": "s", "attempt": {"requested_path": "/link/file", "path_diagnostics": forms}})
        };
        assert!(match_step_denies(&[block(false)], &plan, &event, Some(42)).is_empty());
        let matches = match_step_denies(&[block(true)], &plan, &event, Some(42));
        assert_eq!(matches.len(), 1);
        assert_eq!(
            matches[0].matching_evidence[0].path_sources,
            [
                "runner_host.after_orchestration.realpath_resolved",
                "runner_host.after_orchestration.parent_realpath_resolved"
            ]
        );
        // A form listed as equal to the input carries the input's bytes and
        // nothing else; a malformed listing (listed and present) supplies none.
        let mut listed = block(true);
        listed["attempt"]["path_diagnostics"] = json!({"input": "/link/file",
            "same_as_input": ["realpath_resolved"], "parent_realpath_resolved": null,
            "observer": "runner_host", "phase": "after_orchestration"});
        assert!(match_step_denies(&[listed.clone()], &plan, &event, Some(42)).is_empty());
        let same = [deny(Some(42), "file-read-data", "/link/file")];
        let matches = match_step_denies(&[listed.clone()], &plan, &same, Some(42));
        assert_eq!(
            matches[0].matching_evidence[0].path_sources,
            [
                "submitted_attempt.target",
                "attempt.requested_path",
                "runner_host.after_orchestration.realpath_resolved"
            ]
        );
        listed["attempt"]["path_diagnostics"]["realpath_resolved"] = json!("/link/file");
        let matches = match_step_denies(&[listed], &plan, &same, Some(42));
        assert_eq!(
            matches[0].matching_evidence[0].path_sources,
            ["submitted_attempt.target", "attempt.requested_path"]
        );
    }
    #[test]
    fn parent_form_matches_created_and_unlinked_records() {
        let step = json!({"step_id": "s", "attempt": {"requested_path": "/link/new",
            "path_diagnostics": {"input": "/link/new", "same_as_input": [],
                "realpath_resolved": null, "parent_realpath_resolved": "/real/new",
                "observer": "runner_host", "phase": "after_orchestration"}}});
        for (action, op) in [
            ("create", "file-write-create"),
            ("unlink", "file-write-unlink"),
        ] {
            let plan = [request("s", action, "/link/new")];
            let matches = match_step_denies(
                &[step.clone()],
                &plan,
                &[deny(Some(42), op, "/real/new")],
                Some(42),
            );
            assert_eq!(matches.len(), 1, "{action}");
            assert_eq!(
                matches[0].matching_evidence[0].path_sources,
                ["runner_host.after_orchestration.parent_realpath_resolved"]
            );
        }
        // Null forms derive nothing; a record under any other path stays unmatched.
        assert!(
            match_step_denies(
                &[step],
                &[request("s", "create", "/link/new")],
                &[deny(Some(42), "file-write-create", "/other/new")],
                Some(42)
            )
            .is_empty()
        );
    }
    #[test]
    fn unknown_or_duplicate_step_provenance_is_not_correlated() {
        let event = [deny(Some(42), "file-read-data", "/attempt")];
        assert!(match_step_denies(&[reply("s")], &[], &event, Some(42)).is_empty());
        assert!(
            match_step_denies(
                &[reply("s")],
                &[request("other", "open_read", "/attempt")],
                &event,
                Some(42)
            )
            .is_empty()
        );
        let plan = [request("s", "open_read", "/attempt")];
        assert!(match_step_denies(&[reply("s"), reply("s")], &plan, &event, Some(42)).is_empty());
        assert!(
            match_step_denies(
                &[reply("s")],
                &[plan[0].clone(), plan[0].clone()],
                &event,
                Some(42)
            )
            .is_empty()
        );
    }
    #[test]
    fn create_supports_only_explicit_create_and_write_operations() {
        let steps = [reply("s")];
        let plan = [request("s", "create", "/attempt")];
        for op in ["file-write-create", "file-write-data"] {
            assert_eq!(
                match_step_denies(&steps, &plan, &[deny(Some(42), op, "/attempt")], Some(42)).len(),
                1
            );
        }
        assert!(
            match_step_denies(
                &steps,
                &plan,
                &[deny(Some(42), "file-write-unlink", "/attempt")],
                Some(42)
            )
            .is_empty()
        );
    }
    #[test]
    fn log_show_timestamps_are_utc_whole_seconds_with_explicit_offset() {
        // Expected strings come from Python's datetime, not from this formatter.
        for (seconds, expected) in [
            (-2, "1969-12-31 23:59:58+0000"),
            (-1, "1969-12-31 23:59:59+0000"),
            (0, "1970-01-01 00:00:00+0000"),
            (951782400, "2000-02-29 00:00:00+0000"),
            (1767225599, "2025-12-31 23:59:59+0000"),
            (1790463530, "2026-09-26 22:58:50+0000"),
            (4107542399, "2100-02-28 23:59:59+0000"),
            (4107542400, "2100-03-01 00:00:00+0000"),
            (253402300799, "9999-12-31 23:59:59+0000"),
        ] {
            assert_eq!(log_show_timestamp(seconds), expected, "{seconds}");
        }
    }

    #[test]
    fn run_span_window_floors_start_ceils_end_and_never_collapses() {
        // Literal bounds include rounding, both pads, equal spans and epoch crossing.
        for (started, ended, start, end) in [
            (
                951_782_400_999,
                951_782_401_001,
                "2000-02-28 23:59:58+0000",
                "2000-02-29 00:00:04+0000",
            ),
            (
                1_000,
                3_000,
                "1969-12-31 23:59:59+0000",
                "1970-01-01 00:00:05+0000",
            ),
            (
                5_000,
                5_000,
                "1970-01-01 00:00:03+0000",
                "1970-01-01 00:00:07+0000",
            ),
            (
                5_500,
                5_500,
                "1970-01-01 00:00:03+0000",
                "1970-01-01 00:00:08+0000",
            ),
            (0, 0, "1969-12-31 23:59:58+0000", "1970-01-01 00:00:02+0000"),
            // No lookback cap is reintroduced for a long run.
            (
                0,
                300_000,
                "1969-12-31 23:59:58+0000",
                "1970-01-01 00:05:02+0000",
            ),
        ] {
            let window = SandboxLogWindow::runner_client_span(started, ended);
            assert_eq!(window.start.as_deref(), Some(start));
            assert_eq!(window.end.as_deref(), Some(end));
            assert_eq!(window.started_at_unix_ms, started);
            assert_eq!(window.ended_at_unix_ms, ended);
            assert_eq!(window.pad_seconds, 2);
        }
    }

    #[test]
    fn run_span_window_claims_coverage_and_nothing_stronger() {
        let v = serde_json::to_value(SandboxLogWindow::runner_client_span(1_000, 2_500)).unwrap();
        assert_eq!(v["kind"], "runner_client_span");
        assert_eq!(v["started_at_unix_ms"], 1_000);
        assert_eq!(v["ended_at_unix_ms"], 2_500);
        assert_eq!(v["pad_seconds"], 2);
        assert_eq!(v["start"], "1969-12-31 23:59:59+0000");
        assert_eq!(v["end"], "1970-01-01 00:00:05+0000");
        assert!(v.get("last").is_none());
        for field in [
            "event_timestamps_available",
            "exact_run_membership",
            "step_ordering",
            "pid_reuse_protection",
        ] {
            assert_eq!(v[field], false);
        }
    }

    #[test]
    fn observer_is_asked_for_the_window_and_never_for_a_trailing_lookback() {
        let window = SandboxLogWindow::runner_client_span(1_000, 2_500);
        let argv = observer_argv(
            OsString::from("/x/sandbox-log-observer"),
            42,
            "pw-probe-runner",
            &window,
        )
        .unwrap();
        let argv: Vec<String> = argv
            .iter()
            .map(|a| a.to_string_lossy().to_string())
            .collect();
        assert_eq!(
            argv,
            [
                "/x/sandbox-log-observer",
                "--pid",
                "42",
                "--process-name",
                "pw-probe-runner",
                "--start",
                "1969-12-31 23:59:59+0000",
                "--end",
                "1970-01-01 00:00:05+0000",
                "--format",
                "json",
            ]
        );
        assert!(!argv.iter().any(|a| a == "--last"));
    }

    #[test]
    fn observer_reply_for_another_window_is_not_captured_evidence() {
        use crate::utils::receiver_fixture;
        let window = SandboxLogWindow::runner_client_span(1_000, 2_500);
        let event = r#"{"pid":42,"operation":"file-read-data","path":"/attempt","raw_line":"x"}"#;
        for (reply, expected) in [
            (
                r#""start":"1969-12-31 23:59:59+0000","end":"1970-01-01 00:00:05+0000","last":null"#,
                "captured",
            ),
            (
                r#""start":"1969-12-31 23:59:59+0000","end":"1970-01-01 00:00:05+0000""#,
                "captured",
            ),
            (
                r#""start":"1970-01-01 00:00:02+0000","end":"1970-01-01 00:00:05+0000","last":null"#,
                "window_mismatch",
            ),
            (
                r#""start":"1969-12-31 23:59:59+0000","end":"1970-01-01 00:00:04+0000","last":null"#,
                "window_mismatch",
            ),
            (
                r#""start":"1969-12-31 23:59:59+0000","end":"1970-01-01 00:00:05+0000","last":"10s""#,
                "window_mismatch",
            ),
            // A pre-padding reply is not the query we requested.
            (
                r#""start":"1970-01-01 00:00:01+0000","end":"1970-01-01 00:00:03+0000","last":null"#,
                "window_mismatch",
            ),
            (r#""last":"10s""#, "window_mismatch"),
        ] {
            let body =
                format!(r#"{{"data":{{"observed_deny":true,"deny_events":[{event}],{reply}}}}}"#);
            let capture = parse_observer_output(
                &receiver_fixture(&body, "valid", crate::utils::OBSERVER_CAPTURE_BYTES),
                window.clone(),
            );
            assert_eq!(capture.capture_status, expected, "{reply}");
            // Raw evidence survives either way; only its standing changes.
            assert_eq!(capture.deny_events.as_ref().unwrap().len(), 1, "{reply}");
            assert_eq!(capture.observed_deny, Some(true));
            assert_eq!(capture.window, window);
        }
    }

    #[test]
    fn requested_intervals_select_independently_timed_events() {
        let fixture = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../tests/fixtures/deny_capture/observer.py");
        for (started, ended, retired, paths) in [
            (
                1_999,
                22_001,
                false,
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
                false,
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
                2_500,
                2_500,
                false,
                vec![
                    "/start-pad",
                    "/start-slack",
                    "/early",
                    "/short-tail",
                    "/short-pad",
                    "/short-bound",
                ],
            ),
            // Retired control has its own unpadded end: ceil(22001ms) = 23s.
            (13_000, 23_000, true, vec!["/late", "/end-slack"]),
            (40_000, 50_000, false, vec![]),
        ] {
            let mut window = SandboxLogWindow::runner_client_span(started, ended);
            if retired {
                window.start = Some("1970-01-01 00:00:13+0000".into());
                window.end = Some("1970-01-01 00:00:23+0000".into());
                window.pad_seconds = 0;
            }
            let argv = observer_argv("observer".into(), 42, "pw-probe-runner", &window).unwrap();
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
            let capture = parse_observer_output(&out, window);
            assert_eq!(capture.capture_status, "captured");
            let actual: Vec<_> = capture
                .deny_events
                .as_ref()
                .unwrap()
                .iter()
                .map(|event| event.path.as_deref().unwrap())
                .collect();
            assert_eq!(actual, paths, "span {started}..{ended}");
        }
    }
}
