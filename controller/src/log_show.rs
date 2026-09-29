//! Collection and parsing for the observer's bounded `log show` path.
//! Shared with controller replay tests so supplied text crosses the real parser.

use crate::log_capture::{self, Boundary, CollectionBudget, Cutoff, Supervision};
use serde::Serialize;
use std::process::Command;

pub(crate) fn is_log_prelude_line(line: &str) -> bool {
    line.to_ascii_lowercase()
        .contains("filtering the log data using")
}

#[derive(Serialize, Clone)]
pub(crate) struct SandboxDenyEvent {
    pub(crate) pid: Option<i32>,
    pub(crate) process: Option<String>,
    pub(crate) operation: Option<String>,
    pub(crate) path: Option<String>,
    pub(crate) raw_line: String,
}

fn parse_proc_pid(token: &str) -> (Option<String>, Option<i32>) {
    let open = token.rfind('(');
    let close = token.rfind(')');
    if let (Some(open), Some(close)) = (open, close) {
        if close > open + 1 {
            let name = token[..open].to_string();
            let pid_str = &token[(open + 1)..close];
            if let Ok(pid) = pid_str.parse::<i32>() {
                return (Some(name), Some(pid));
            }
        }
    }
    (None, None)
}

pub(crate) fn parse_sandbox_deny_line(line: &str) -> Option<SandboxDenyEvent> {
    let idx = line.find("Sandbox:")?;
    let msg = line[(idx + "Sandbox:".len())..].trim_start();
    if !msg.to_ascii_lowercase().contains("deny(") {
        return None;
    }
    let mut parts = msg.split_whitespace();
    let proc_token = parts.next().unwrap_or_default();
    let deny_token = parts.next().unwrap_or_default();
    if !deny_token.to_ascii_lowercase().starts_with("deny(") {
        return None;
    }
    let operation = parts.next().map(|v| v.to_string());
    // Preserve the entire remaining target, including internal spaces. A
    // first-token path could falsely associate /tmp/a b with an attempt /tmp/a.
    // Additional unparsed suffixes stay in this value; correlation requires
    // exact equality and does not guess where such a suffix begins.
    let path = operation.as_ref().and_then(|op| {
        let after_proc = msg.strip_prefix(proc_token)?.trim_start();
        let after_deny = after_proc.strip_prefix(deny_token)?.trim_start();
        let target = after_deny.strip_prefix(op)?.trim_start();
        if target.is_empty() {
            None
        } else {
            Some(target.to_string())
        }
    });
    let (process, pid) = parse_proc_pid(proc_token);
    Some(SandboxDenyEvent {
        pid,
        process,
        operation,
        path,
        raw_line: line.to_string(),
    })
}

pub(crate) struct ShowCapture {
    pub(crate) stdout: String,
    pub(crate) stderr: String,
    pub(crate) observed_lines: usize,
    pub(crate) deny_lines: Vec<String>,
    pub(crate) deny_events: Vec<SandboxDenyEvent>,
    pub(crate) report: Supervision,
}

pub(crate) fn capture_show(
    command: &mut Command,
    budget: CollectionBudget,
    reserve_ms: u64,
) -> ShowCapture {
    let captured = log_capture::capture_reserving(command, budget, Boundary::LogShow, reserve_ms);
    let mut report = captured.supervision;
    if (std::str::from_utf8(&captured.stdout).is_err()
        || std::str::from_utf8(&captured.stderr).is_err())
        && report.cutoff.is_none()
    {
        report.cutoff = Some(Cutoff::reason(
            "decode_error",
            Some(
                "log show emitted invalid UTF-8; retained text is lossy diagnostic evidence".into(),
            ),
        ));
    }
    let stdout = String::from_utf8_lossy(&captured.stdout).into_owned();
    let stderr = String::from_utf8_lossy(&captured.stderr).into_owned();
    let mut observed_lines = 0;
    let mut deny_lines = Vec::new();
    let mut deny_events = Vec::new();
    for line in stdout.lines() {
        if line.trim().is_empty() || is_log_prelude_line(line) {
            continue;
        }
        observed_lines += 1;
        if let Some(event) = parse_sandbox_deny_line(line) {
            if deny_events.len() == log_capture::MAX_DENY_EVENTS {
                report.cutoff.get_or_insert_with(|| {
                    Cutoff::limit(
                        "event_overflow",
                        "deny_events",
                        log_capture::MAX_DENY_EVENTS,
                        deny_events.len() + 1,
                    )
                });
                break;
            }
            deny_lines.push(line.to_string());
            deny_events.push(event);
        }
    }
    if budget.expired_within(reserve_ms) && report.cutoff.is_none() {
        report.cutoff = Some(Cutoff::reason(
            "deadline",
            Some("log output parsing exceeded the collection deadline".into()),
        ));
    }
    ShowCapture {
        stdout,
        stderr,
        observed_lines,
        deny_lines,
        deny_events,
        report,
    }
}
