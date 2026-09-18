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

/// References into capture.deny_events, not copies or uniquely identified
/// occurrences. Even a single candidate has no exact run/ordering guarantee.
#[derive(Serialize)]
pub struct SandboxLogStepDeny {
    pub event_index: usize,
    pub candidate_step_ids: Vec<String>,
    pub association: String,
}

#[derive(Serialize)]
pub struct SandboxLogWindow {
    pub kind: &'static str,
    pub last: String,
    pub event_timestamps_available: bool,
    pub exact_run_membership: bool,
    pub step_ordering: bool,
    pub pid_reuse_protection: bool,
}

impl SandboxLogWindow {
    pub fn trailing(last: &str) -> Self {
        Self {
            kind: "trailing",
            last: last.to_string(),
            event_timestamps_available: false,
            exact_run_membership: false,
            step_ordering: false,
            pid_reuse_protection: false,
        }
    }
}

#[derive(Serialize)]
pub struct SandboxLogCapture {
    pub window: SandboxLogWindow,
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

/// Only authoritative spawned-worker metadata can identify a worker. Stored
/// replies remain readable without falling back to a host/client top-level PID.
pub fn worker_pid(result: Option<&Value>) -> Option<i32> {
    let pid = result?.get("runner_subprocess")?.get("pid")?.as_i64()?;
    i32::try_from(pid).ok().filter(|pid| *pid > 0)
}

// Exact operation names from the attempted syscall, never the independently
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

pub fn match_step_denies(
    steps: &[Value],
    submitted_plan: &[Value],
    deny_events: &[SandboxDenyEvent],
    pid: Option<i32>,
) -> Vec<SandboxLogStepDeny> {
    let Some(pid) = pid.filter(|p| *p > 0) else {
        return Vec::new();
    };
    let mut out = Vec::new();
    for (event_index, event) in deny_events.iter().enumerate() {
        if event.pid != Some(pid) {
            continue;
        }
        let (Some(operation), Some(path)) = (event.operation.as_deref(), event.path.as_deref())
        else {
            continue;
        };
        let mut candidates = Vec::new();
        for step in steps {
            let Some(id) = step.get("step_id").and_then(Value::as_str) else {
                continue;
            };
            // A duplicate ID on either side makes the provenance join unusable.
            if steps
                .iter()
                .filter(|s| s.get("step_id").and_then(Value::as_str) == Some(id))
                .count()
                != 1
            {
                continue;
            }
            let mut submitted = submitted_plan
                .iter()
                .filter(|s| s.get("step_id").and_then(Value::as_str) == Some(id));
            let Some(request) = submitted.next() else {
                continue;
            };
            if submitted.next().is_some() {
                continue;
            }
            let Some(attempt) = request.get("attempt") else {
                continue;
            };
            if !attempt_operations(attempt).contains(&operation) {
                continue;
            }
            let mut paths = step_attempt_paths(step);
            if let Some(target) = attempt.get("target").and_then(Value::as_str) {
                paths.push(target.to_string());
            }
            if paths.iter().any(|p| p == path) {
                candidates.push(id.to_string());
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

    let observed_deny = parsed
        .as_ref()
        .and_then(observed_deny_from_observer_envelope);
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
        window: SandboxLogWindow::trailing(last),
        capture_status,
        tool_exit_code: exit_code,
        blocked_reason,
        stdout_parse_error: parse_error.clone(),
        stdout_truncated,
        stdout_raw: if parse_error.is_some() {
            Some(stdout)
        } else {
            None
        },
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
    use super::*;
    use serde_json::json;

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
            assert!(match_step_denies(
                &steps,
                &plan,
                &[deny(pid, "file-read-data", "/attempt")],
                Some(42)
            )
            .is_empty());
        }
        for pid in [None, Some(0), Some(-1)] {
            assert!(match_step_denies(
                &steps,
                &plan,
                &[deny(Some(42), "file-read-data", "/attempt")],
                pid
            )
            .is_empty());
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
    }
    #[test]
    fn unknown_or_duplicate_step_provenance_is_not_correlated() {
        let event = [deny(Some(42), "file-read-data", "/attempt")];
        assert!(match_step_denies(&[reply("s")], &[], &event, Some(42)).is_empty());
        assert!(match_step_denies(
            &[reply("s")],
            &[request("other", "open_read", "/attempt")],
            &event,
            Some(42)
        )
        .is_empty());
        let plan = [request("s", "open_read", "/attempt")];
        assert!(match_step_denies(&[reply("s"), reply("s")], &plan, &event, Some(42)).is_empty());
        assert!(match_step_denies(
            &[reply("s")],
            &[plan[0].clone(), plan[0].clone()],
            &event,
            Some(42)
        )
        .is_empty());
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
        assert!(match_step_denies(
            &steps,
            &plan,
            &[deny(Some(42), "file-write-unlink", "/attempt")],
            Some(42)
        )
        .is_empty());
    }
    #[test]
    fn trailing_window_reports_missing_temporal_evidence() {
        let v = serde_json::to_value(SandboxLogWindow::trailing("10s")).unwrap();
        assert_eq!(v["last"], "10s");
        assert_eq!(v["kind"], "trailing");
        for field in [
            "event_timestamps_available",
            "exact_run_membership",
            "step_ordering",
            "pid_reuse_protection",
        ] {
            assert_eq!(v[field], false);
        }
    }
}
