//! Host-side SBPL preflight helper wiring.
//!
//! The controller runs a lightweight compile check before invoking a runner so
//! SBPL syntax errors are surfaced even if the runner cannot reply over XPC.

use serde::Serialize;
use serde_json::Value;
use std::ffi::OsString;
use std::path::Path;
use std::process::{Command, Stdio};

use crate::app_layout::resolve_contents_macos_tool;
use crate::utils::truncate_output;

#[derive(Serialize)]
pub struct PolicyPreflightCapture {
    pub status: String,
    pub tool_exit_code: i32,
    pub stdout_parse_error: Option<String>,
    pub stdout_truncated: bool,
    pub stdout_raw: Option<String>,
    pub stderr: String,
    pub stderr_truncated: bool,
    pub envelope: Option<Value>,
    pub policy_format: Option<String>,
    pub policy_sha256: Option<String>,
    pub compiled: Option<bool>,
    pub compile_error: Option<String>,
    pub normalized_outcome: Option<String>,
}

impl PolicyPreflightCapture {
    pub fn unavailable(error: String) -> Self {
        PolicyPreflightCapture {
            status: "unavailable".to_string(),
            tool_exit_code: 1,
            stdout_parse_error: None,
            stdout_truncated: false,
            stdout_raw: None,
            stderr: error,
            stderr_truncated: false,
            envelope: None,
            policy_format: None,
            policy_sha256: None,
            compiled: None,
            compile_error: None,
            normalized_outcome: None,
        }
    }
}

fn envelope_field_string(env: &Value, key: &str) -> Option<String> {
    env.get("data")
        .and_then(|v| v.get(key))
        .and_then(|v| v.as_str())
        .map(|s| s.to_string())
}

fn envelope_field_bool(env: &Value, key: &str) -> Option<bool> {
    env.get("data")
        .and_then(|v| v.get(key))
        .and_then(|v| v.as_bool())
}

fn envelope_normalized_outcome(env: &Value) -> Option<String> {
    env.get("result")
        .and_then(|v| v.get("normalized_outcome"))
        .and_then(|v| v.as_str())
        .map(|s| s.to_string())
}

pub fn run_policy_preflight(request_path: &Path) -> Result<PolicyPreflightCapture, String> {
    let tool = resolve_contents_macos_tool("sbpl-preflight")?;
    let argv = vec![
        tool.into_os_string(),
        OsString::from("--request"),
        request_path.as_os_str().to_os_string(),
    ];

    let out = Command::new(&argv[0])
        .args(&argv[1..])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run sbpl-preflight: {e}"))?;

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

    let (compiled, policy_format, policy_sha256, compile_error, normalized_outcome) =
        if let Some(env) = parsed.as_ref() {
            (
                envelope_field_bool(env, "compiled"),
                envelope_field_string(env, "policy_format"),
                envelope_field_string(env, "policy_sha256"),
                envelope_field_string(env, "compile_error"),
                envelope_normalized_outcome(env),
            )
        } else {
            (None, None, None, None, None)
        };

    let status = if parse_error.is_some() {
        "parse_error".to_string()
    } else if compiled == Some(true) {
        "compiled".to_string()
    } else if compiled == Some(false) {
        normalized_outcome
            .as_deref()
            .unwrap_or("compile_error")
            .to_string()
    } else if exit_code != 0 {
        "tool_error".to_string()
    } else if parsed.is_some() {
        "ok".to_string()
    } else {
        "tool_error".to_string()
    };

    Ok(PolicyPreflightCapture {
        status,
        tool_exit_code: exit_code,
        stdout_parse_error: parse_error.clone(),
        stdout_truncated,
        stdout_raw: if parse_error.is_some() { Some(stdout) } else { None },
        stderr,
        stderr_truncated,
        envelope: parsed,
        policy_format,
        policy_sha256,
        compiled,
        compile_error,
        normalized_outcome,
    })
}
