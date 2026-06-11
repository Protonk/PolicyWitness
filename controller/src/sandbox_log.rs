//! Unified-log capture helpers for sandbox denials.
//!
//! The controller shells out to the embedded sandbox-log-observer tool and
//! attaches its JSON report to the run envelope as best-effort evidence.

use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::ffi::OsString;
use std::process::{Command, Stdio};

use crate::app_layout::resolve_contents_macos_tool;
use crate::utils::truncate_output;

#[derive(Serialize, Deserialize, Clone)]
pub struct SandboxDenyEvent {
    pub pid: Option<i32>,
    pub process: Option<String>,
    pub operation: Option<String>,
    pub path: Option<String>,
    pub raw_line: Option<String>,
}

#[derive(Serialize)]
pub struct SandboxLogStepDeny {
    pub step_id: String,
    pub deny_events: Vec<SandboxDenyEvent>,
}

#[derive(Serialize)]
pub struct SandboxLogCapture {
    pub capture_status: String,
    pub tool_exit_code: i32,
    pub blocked_reason: Option<String>,
    pub stdout_parse_error: Option<String>,
    pub stdout_truncated: bool,
    pub stdout_raw: Option<String>,
    pub stderr: String,
    pub stderr_truncated: bool,
    pub observer: Option<Value>,
    pub observed_deny: Option<bool>,
    pub deny_events: Option<Vec<SandboxDenyEvent>>,
    pub step_denies: Option<Vec<SandboxLogStepDeny>>,
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
    if err.to_ascii_lowercase().contains("cannot run while sandboxed") {
        return Some(err);
    }
    None
}

fn observer_deny_events(obj: &Value) -> Option<Vec<SandboxDenyEvent>> {
    let value = obj.get("data")?.get("deny_events")?.clone();
    serde_json::from_value::<Vec<SandboxDenyEvent>>(value).ok()
}

fn step_attempt_paths(step: &Value) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    let attempt = match step.get("attempt") {
        Some(v) => v,
        None => return out,
    };
    for key in ["observed_path", "normalized_path", "requested_path"] {
        if let Some(val) = attempt.get(key).and_then(|v| v.as_str()) {
            out.push(val.to_string());
        }
    }
    out.sort();
    out.dedup();
    out
}

pub fn match_step_denies(
    steps: &[Value],
    deny_events: &[SandboxDenyEvent],
    pid: Option<i64>,
) -> Vec<SandboxLogStepDeny> {
    let pid = pid.and_then(|v| i32::try_from(v).ok());
    let mut out: Vec<SandboxLogStepDeny> = Vec::new();
    for step in steps {
        let step_id = match step.get("step_id").and_then(|v| v.as_str()) {
            Some(v) => v.to_string(),
            None => continue,
        };
        let paths = step_attempt_paths(step);
        if paths.is_empty() {
            continue;
        }
        // Match log lines to step paths to avoid over-attributing denials.
        let mut matched: Vec<SandboxDenyEvent> = Vec::new();
        for event in deny_events {
            if let (Some(event_pid), Some(pid)) = (event.pid, pid) {
                if event_pid != pid {
                    continue;
                }
            }
            if let Some(path) = event.path.as_ref() {
                if paths.iter().any(|p| p == path) {
                    matched.push(event.clone());
                }
            }
        }
        if !matched.is_empty() {
            out.push(SandboxLogStepDeny {
                step_id,
                deny_events: matched,
            });
        }
    }
    out
}

pub fn capture_sandbox_logs_last(
    pid: i64,
    process_name: &str,
    last: &str,
) -> Result<SandboxLogCapture, String> {
    let tool = resolve_contents_macos_tool("sandbox-log-observer")?;
    let argv = vec![
        tool.into_os_string(),
        OsString::from("--pid"),
        OsString::from(format!("{pid}")),
        OsString::from("--process-name"),
        OsString::from(process_name),
        OsString::from("--last"),
        OsString::from(last),
        OsString::from("--format"),
        OsString::from("json"),
    ];

    let out = Command::new(&argv[0])
        .args(&argv[1..])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run sandbox-log-observer: {e}"))?;

    let exit_code = out.status.code().unwrap_or(1);

    let (stdout, stdout_truncated) = truncate_output(&out.stdout);
    let (stderr, stderr_truncated) = truncate_output(&out.stderr);

    let mut parsed: Option<Value> = None;
    let mut parse_error: Option<String> = None;
    if !stdout.trim().is_empty() {
        match serde_json::from_str::<Value>(&stdout) {
            Ok(v) => parsed = Some(v),
            Err(e) => parse_error = Some(format!("{e}")),
        }
    }

    let observed_deny = parsed.as_ref().and_then(observed_deny_from_observer_envelope);
    let observer_log_error = parsed.as_ref().and_then(observer_log_error);
    let blocked_reason = parsed.as_ref().and_then(observer_blocked_reason);
    let deny_events = parsed.as_ref().and_then(observer_deny_events);

    let capture_status = if parse_error.is_some() {
        "parse_error".to_string()
    } else if blocked_reason.is_some() {
        "blocked".to_string()
    } else if observer_log_error.is_some() {
        "error".to_string()
    } else if exit_code != 0 {
        "error".to_string()
    } else if parsed.is_some() {
        "captured".to_string()
    } else {
        "error".to_string()
    };

    Ok(SandboxLogCapture {
        capture_status,
        tool_exit_code: exit_code,
        blocked_reason,
        stdout_parse_error: parse_error.clone(),
        stdout_truncated,
        stdout_raw: if parse_error.is_some() { Some(stdout) } else { None },
        stderr,
        stderr_truncated,
        observer: parsed,
        observed_deny,
        deny_events,
        step_denies: None,
    })
}

#[cfg(test)]
mod tests {
    // Deterministic coverage of step↔deny correlation. Pairs with the
    // first_deny synthesis tests in run_flow.rs; both pin the populated-deny
    // path that the e2e (runner_sandbox_diagnostics_on_denied) can't produce —
    // its seam-killed worker logs no kernel deny (COVERAGE.md).
    use super::*;
    use serde_json::json;

    fn deny(pid: i32, op: &str, path: &str) -> SandboxDenyEvent {
        SandboxDenyEvent {
            pid: Some(pid),
            process: Some("PWRunner".to_string()),
            operation: Some(op.to_string()),
            path: Some(path.to_string()),
            raw_line: Some(format!("Sandbox: PWRunner({pid}) deny(1) {op} {path}")),
        }
    }

    #[test]
    fn matches_deny_to_step_by_path_and_pid() {
        let steps = vec![json!({
            "step_id": "p1",
            "attempt": { "requested_path": "/tmp/x", "observed_path": "/tmp/x" }
        })];
        let events = vec![deny(1234, "file-read-data", "/tmp/x")];
        let out = match_step_denies(&steps, &events, Some(1234));
        assert_eq!(out.len(), 1);
        assert_eq!(out[0].step_id, "p1");
        assert_eq!(out[0].deny_events.len(), 1);
        assert_eq!(out[0].deny_events[0].path.as_deref(), Some("/tmp/x"));
    }

    #[test]
    fn rejects_deny_with_mismatched_pid() {
        // When both PIDs are known and differ, the deny is not the worker's.
        let steps = vec![json!({"step_id": "p1", "attempt": {"requested_path": "/tmp/x"}})];
        let events = vec![deny(9999, "file-read-data", "/tmp/x")];
        assert!(match_step_denies(&steps, &events, Some(1234)).is_empty());
    }

    #[test]
    fn rejects_deny_with_unrelated_path() {
        // A deny whose path matches no attempt path of the step is not pinned
        // to it (avoids over-attribution).
        let steps = vec![json!({"step_id": "p1", "attempt": {"requested_path": "/tmp/x"}})];
        let events = vec![deny(1234, "file-read-data", "/etc/passwd")];
        assert!(match_step_denies(&steps, &events, Some(1234)).is_empty());
    }

    #[test]
    fn step_without_attempt_paths_is_skipped() {
        let steps = vec![json!({"step_id": "p1", "attempt": {}})];
        let events = vec![deny(1234, "file-read-data", "/tmp/x")];
        assert!(match_step_denies(&steps, &events, Some(1234)).is_empty());
    }
}
