//! Host-side `sbpl-check` helper wiring.
//!
//! On an `xpc_error` the controller records an independent helper compilation.
//! That result does not establish the worker's progress or explain a missing reply.

use serde::Serialize;
use serde_json::Value;
use std::ffi::OsString;
use std::path::Path;
use std::process::{Command, Stdio};

use crate::app_layout::resolve_contents_macos_tool;
use crate::utils::{capture_json_output, JsonOutputCapture};

#[derive(Serialize)]
pub struct PolicyCheckCapture {
    pub status: String,
    pub tool_exit_code: i32,
    #[serde(flatten)]
    pub output: JsonOutputCapture,
    pub envelope: Option<Value>,
    pub policy_format: Option<String>,
    pub policy_sha256: Option<String>,
    pub compiled: Option<bool>,
    pub compile_error: Option<String>,
    pub normalized_outcome: Option<String>,
}

impl PolicyCheckCapture {
    pub fn unavailable(error: String) -> Self {
        PolicyCheckCapture {
            status: "unavailable".to_string(),
            tool_exit_code: 1,
            output: JsonOutputCapture::unavailable(error),
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

pub fn run_policy_check(request_path: &Path) -> Result<PolicyCheckCapture, String> {
    let tool = resolve_contents_macos_tool("sbpl-check")?;
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
        .map_err(|e| format!("failed to run sbpl-check: {e}"))?;

    Ok(parse_policy_check_output(&out))
}

fn parse_policy_check_output(out: &std::process::Output) -> PolicyCheckCapture {
    let exit_code = out.status.code().unwrap_or(1);
    let (output, parsed) = capture_json_output(out, "sbpl-check");

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

    let status = if output.stdout_capture_error.is_some() {
        "capture_error".to_string()
    } else if output.stdout_parse_error.is_some() {
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
        "invalid_reply".to_string()
    } else {
        "tool_error".to_string()
    };

    PolicyCheckCapture {
        status,
        tool_exit_code: exit_code,
        output,
        envelope: parsed,
        policy_format,
        policy_sha256,
        compiled,
        compile_error,
        normalized_outcome,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::utils::{receiver_fixture, MAX_CAPTURE_BYTES};
    #[test]
    fn unfamiliar_diagnostics_survive_helper_capture() {
        let records = crate::utils::transport_diagnostics();
        let original = serde_json::json!({"data": {"diagnostics": records,
            "compiled": false, "compile_error": "independent helper diagnostic"},
            "result": {"normalized_outcome": "compile_error"}});
        for mode in ["valid", "oversized"] {
            let output = crate::utils::receiver_fixture(&original.to_string(), mode);
            let capture = parse_policy_check_output(&output);
            let wire = serde_json::to_value(&capture).unwrap();
            if mode == "valid" {
                assert_eq!(wire["envelope"], original);
                assert_eq!(wire["compiled"], false);
                assert_eq!(capture.status, "compile_error");
                assert_eq!(
                    capture.compile_error.as_deref(),
                    Some("independent helper diagnostic")
                );
            } else {
                assert!(serde_json::from_slice::<Value>(&output.stdout).is_ok());
                assert!(capture.envelope.is_none());
                assert!(capture.compiled.is_none());
                assert_eq!(capture.status, "capture_error");
                assert!(capture.output.stdout_parse_error.is_none());
            }
        }
    }

    #[test]
    fn helper_receiver_preserves_loss_and_never_invents_compilation() {
        for (mode, expected) in [
            ("valid", "compiled"),
            ("oversized", "capture_error"),
            ("utf8", "parse_error"),
            ("malformed", "parse_error"),
            ("empty", "tool_error"),
            ("missing", "invalid_reply"),
        ] {
            let original = receiver_fixture(r#"{"data":{"compiled":true}}"#, mode);
            let capture = parse_policy_check_output(&original);
            let wire = serde_json::to_value(&capture).unwrap();
            assert_eq!(capture.status, expected, "{mode}");
            assert_eq!(wire["stdout_bytes_received"], original.stdout.len());
            assert_eq!(
                wire["stdout_bytes_retained"],
                original.stdout.len().min(MAX_CAPTURE_BYTES)
            );
            assert_eq!(wire["stderr_bytes_received"], 1048578);
            assert_eq!(wire["stderr_bytes_retained"], MAX_CAPTURE_BYTES);
            assert_eq!(wire["capture_limit_bytes"], MAX_CAPTURE_BYTES);
            assert_eq!(
                capture.compiled,
                if mode == "valid" { Some(true) } else { None }
            );
            if mode == "oversized" {
                assert!(serde_json::from_slice::<Value>(&original.stdout).is_ok());
                assert!(capture.output.stdout_capture_error.is_some());
                assert!(capture.output.stdout_parse_error.is_none());
                assert!(capture.envelope.is_none());
            }
            if mode == "missing" {
                assert_eq!(capture.envelope.unwrap()["data"]["code"], 97319);
                assert!(capture.compile_error.is_none());
            }
        }
    }
}
