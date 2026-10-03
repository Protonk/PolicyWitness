//! Host-side `sbpl-check` helper wiring.
//!
//! On an `xpc_error` the controller records an independent helper compilation.
//! That result does not establish the worker's progress or explain a missing reply.
//! The capture copies the helper's own verdict; it derives no second one from
//! the compile record, `result.ok` or the process exit code.

use serde::Serialize;
use serde_json::Value;
use std::process::Command;

use crate::app_layout::resolve_contents_macos_tool;
use crate::json_contract::SCHEMA_VERSION;
use crate::utils::{JsonOutputCapture, capture_json_output, run_with_stdin};

/// The helper envelope kind the capture reads.
const HELPER_KIND: &str = "sbpl_check";

#[derive(Serialize)]
pub struct PolicyCheckCapture {
    /// A transport status (`unavailable`, `capture_error`, `parse_error`,
    /// `tool_error`, `invalid_reply`) or the helper's `normalized_outcome`
    /// copied exactly from a supported envelope.
    pub status: String,
    pub tool_exit_code: i32,
    #[serde(flatten)]
    pub output: JsonOutputCapture,
    /// The parsed helper output, retained unchanged whenever untruncated
    /// stdout parsed, supported or not.
    pub envelope: Option<Value>,
}

impl PolicyCheckCapture {
    pub fn unavailable(error: String) -> Self {
        PolicyCheckCapture {
            status: "unavailable".to_string(),
            tool_exit_code: 1,
            output: JsonOutputCapture::unavailable(error, crate::utils::HELPER_CAPTURE_BYTES),
            envelope: None,
        }
    }
}

/// The outcome of a supported helper envelope: the helper kind, the current
/// integer envelope version and a nonempty string outcome. Anything else is
/// not interpreted; the version is checked before the outcome is read.
fn supported_outcome(env: &Value) -> Option<String> {
    if env.get("kind").and_then(Value::as_str) != Some(HELPER_KIND) {
        return None;
    }
    let version = env.get("schema_version")?;
    if !version.is_u64() || version.as_u64() != Some(u64::from(SCHEMA_VERSION)) {
        return None;
    }
    env.get("result")
        .and_then(|v| v.get("normalized_outcome"))
        .and_then(Value::as_str)
        .filter(|outcome| !outcome.is_empty())
        .map(str::to_string)
}

/// Deliver the held request string to `sbpl-check --request -` on stdin. A
/// launch or delivery failure is an error; the caller records the capture as
/// unavailable and keeps the original runner reply.
pub fn run_policy_check(request: &str) -> Result<PolicyCheckCapture, String> {
    let tool = resolve_contents_macos_tool("sbpl-check")?;
    let mut command = Command::new(&tool);
    command.args(["--request", "-"]);
    let (out, delivery) = run_with_stdin(command, request.as_bytes().to_vec())
        .map_err(|e| format!("failed to run sbpl-check: {e}"))?;
    if let Some(error) = delivery.error {
        return Err(format!("sbpl-check request delivery failed: {error}"));
    }
    Ok(parse_policy_check_output(&out))
}

fn parse_policy_check_output(out: &std::process::Output) -> PolicyCheckCapture {
    let exit_code = out.status.code().unwrap_or(1);
    let (output, parsed) =
        capture_json_output(out, "sbpl-check", crate::utils::HELPER_CAPTURE_BYTES);

    // Transport loss first, then whether anything parsed, then whether what
    // parsed is a helper envelope this reader interprets.
    let status = if output.stdout_capture_error.is_some() {
        "capture_error".to_string()
    } else if output.stdout_parse_error.is_some() {
        "parse_error".to_string()
    } else {
        match parsed.as_ref() {
            None => "tool_error".to_string(),
            Some(env) => supported_outcome(env).unwrap_or_else(|| "invalid_reply".to_string()),
        }
    };

    PolicyCheckCapture {
        status,
        tool_exit_code: exit_code,
        output,
        envelope: parsed,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::utils::{HELPER_CAPTURE_BYTES, receiver_fixture};
    use serde_json::json;
    use std::os::unix::process::ExitStatusExt;

    /// The projections the capture no longer carries; readers use the nested
    /// envelope.
    const RETIRED_PROJECTIONS: [&str; 5] = [
        "compiled",
        "compile_error",
        "normalized_outcome",
        "policy_format",
        "policy_sha256",
    ];

    /// A current helper envelope in the frame the helper prints.
    fn helper_envelope(outcome: Value, exit_code: i64, compile: Value) -> Value {
        json!({
            "schema_version": SCHEMA_VERSION, "kind": HELPER_KIND, "generated_at_unix_ms": 1,
            "build": {"version": "0", "number": "0", "describe": "test", "commit": "0"},
            "result": {"ok": exit_code == 0, "rc": null, "exit_code": exit_code,
                "normalized_outcome": outcome, "errno": null, "error": null,
                "stderr": null, "stdout": null},
            "data": {"policy_format": "sbpl", "policy_sha256": "f".repeat(64),
                "macos_build_version": "23J220", "params_present": false, "params_count": 0,
                "compile": compile, "import_inventory": null},
        })
    }

    fn output_of(envelope: &Value, exit_code: i32) -> std::process::Output {
        std::process::Output {
            status: std::process::ExitStatus::from_raw(exit_code << 8),
            stdout: serde_json::to_vec(envelope).unwrap(),
            stderr: Vec::new(),
        }
    }

    fn assert_projections_absent(wire: &Value) {
        let keys = wire.as_object().unwrap();
        for key in RETIRED_PROJECTIONS {
            assert!(!keys.contains_key(key), "{key} must be absent, not null");
        }
    }

    #[test]
    fn supported_outcomes_are_copied_into_status_without_a_second_verdict() {
        for outcome in [
            "ok",
            "compile_error",
            "setup_error",
            "bad_request",
            "policy_too_large",
            "future_outcome",
        ] {
            // Contradictory process exit and compile record: the capture copies
            // the helper's outcome and preserves both as received.
            let contradictory = json!({"stage": "compile", "ok": outcome != "ok", "error": null});
            let envelope = helper_envelope(json!(outcome), 0, contradictory);
            let capture = parse_policy_check_output(&output_of(&envelope, 3));
            assert_eq!(capture.status, outcome);
            assert_eq!(capture.tool_exit_code, 3);
            assert_eq!(capture.envelope.as_ref(), Some(&envelope));
            let wire = serde_json::to_value(&capture).unwrap();
            assert_eq!(wire["status"], outcome);
            assert_eq!(wire["tool_exit_code"], 3);
            assert_eq!(wire["envelope"], envelope);
            assert_projections_absent(&wire);
        }
    }

    #[test]
    fn unsupported_or_incomplete_envelopes_are_invalid_replies_retained_unchanged() {
        let current = i64::from(SCHEMA_VERSION);
        let mut cases: Vec<(&str, Value)> = Vec::new();
        let mut wrong_kind = helper_envelope(json!("ok"), 0, json!(null));
        wrong_kind["kind"] = json!("run");
        cases.push(("wrong kind", wrong_kind));
        let mut no_kind = helper_envelope(json!("ok"), 0, json!(null));
        no_kind.as_object_mut().unwrap().remove("kind");
        cases.push(("missing kind", no_kind));
        for (label, version) in [
            ("missing version", Value::Null),
            ("string version", json!(current.to_string())),
            ("float version", json!(current as f64)),
            ("previous version", json!(current - 1)),
            ("next version", json!(current + 1)),
            ("negative version", json!(-current)),
        ] {
            let mut envelope = helper_envelope(json!("ok"), 0, json!(null));
            if version.is_null() {
                envelope.as_object_mut().unwrap().remove("schema_version");
            } else {
                envelope["schema_version"] = version;
            }
            cases.push((label, envelope));
        }
        // An old-version envelope that says it compiled earns no recovered success.
        let mut old_compiled = helper_envelope(json!("ok"), 0, json!(null));
        old_compiled["schema_version"] = json!(current - 1);
        old_compiled["data"]["compiled"] = json!(true);
        cases.push(("old version with compiled: true", old_compiled));
        for (label, outcome) in [
            ("null outcome", Value::Null),
            ("empty outcome", json!("")),
            ("numeric outcome", json!(0)),
        ] {
            cases.push((label, helper_envelope(outcome, 0, json!(null))));
        }
        let mut no_outcome = helper_envelope(json!("ok"), 0, json!(null));
        no_outcome["result"]
            .as_object_mut()
            .unwrap()
            .remove("normalized_outcome");
        cases.push(("missing outcome", no_outcome));
        let mut no_result = helper_envelope(json!("ok"), 0, json!(null));
        no_result.as_object_mut().unwrap().remove("result");
        cases.push(("missing result", no_result));

        for (label, envelope) in cases {
            let capture = parse_policy_check_output(&output_of(&envelope, 0));
            assert_eq!(capture.status, "invalid_reply", "{label}");
            assert_eq!(capture.tool_exit_code, 0, "{label}");
            assert_eq!(capture.envelope.as_ref(), Some(&envelope), "{label}");
            let wire = serde_json::to_value(&capture).unwrap();
            assert_eq!(wire["envelope"], envelope, "{label}");
            assert_projections_absent(&wire);
        }
    }

    #[test]
    fn unfamiliar_diagnostics_survive_helper_capture() {
        let records = crate::utils::transport_diagnostics();
        let mut original = helper_envelope(
            json!("compile_error"),
            1,
            json!({"stage": "compile", "ok": false, "error": "independent helper diagnostic"}),
        );
        original["data"]["diagnostics"] = records;
        for mode in ["valid", "oversized"] {
            let output = receiver_fixture(&original.to_string(), mode, HELPER_CAPTURE_BYTES);
            let capture = parse_policy_check_output(&output);
            let wire = serde_json::to_value(&capture).unwrap();
            assert_projections_absent(&wire);
            if mode == "valid" {
                assert_eq!(wire["envelope"], original);
                assert_eq!(capture.status, "compile_error");
                assert_eq!(
                    wire["envelope"]["data"]["compile"]["error"],
                    "independent helper diagnostic"
                );
            } else {
                assert!(serde_json::from_slice::<Value>(&output.stdout).is_ok());
                assert!(capture.envelope.is_none());
                assert_eq!(capture.status, "capture_error");
                assert!(capture.output.stdout_parse_error.is_none());
            }
        }
    }

    #[test]
    fn helper_receiver_preserves_loss_and_never_invents_compilation() {
        let valid = helper_envelope(
            json!("ok"),
            0,
            json!({"stage": "compile", "ok": true, "error": null}),
        );
        for (mode, expected) in [
            ("valid", "ok"),
            ("oversized", "capture_error"),
            ("utf8", "parse_error"),
            ("malformed", "parse_error"),
            ("empty", "tool_error"),
            ("missing", "invalid_reply"),
        ] {
            let original = receiver_fixture(&valid.to_string(), mode, HELPER_CAPTURE_BYTES);
            let capture = parse_policy_check_output(&original);
            let wire = serde_json::to_value(&capture).unwrap();
            assert_eq!(capture.status, expected, "{mode}");
            assert_eq!(wire["stdout_bytes_received"], original.stdout.len());
            assert_eq!(
                wire["stdout_bytes_retained"],
                original.stdout.len().min(HELPER_CAPTURE_BYTES)
            );
            assert_eq!(wire["stderr_bytes_received"], original.stderr.len());
            assert_eq!(wire["stderr_bytes_retained"], HELPER_CAPTURE_BYTES);
            assert_eq!(wire["capture_limit_bytes"], HELPER_CAPTURE_BYTES);
            assert_projections_absent(&wire);
            // Transport statuses are independent of each other and of parsing.
            assert_eq!(
                capture.output.stdout_capture_error.is_some(),
                mode == "oversized",
                "{mode}"
            );
            assert_eq!(
                capture.output.stdout_parse_error.is_some(),
                matches!(mode, "utf8" | "malformed"),
                "{mode}"
            );
            assert_eq!(
                capture.envelope.is_some(),
                matches!(mode, "valid" | "missing"),
                "{mode}"
            );
            if mode == "valid" {
                assert_eq!(wire["envelope"], valid);
            }
            if mode == "oversized" {
                assert!(serde_json::from_slice::<Value>(&original.stdout).is_ok());
            }
            if mode == "missing" {
                assert_eq!(capture.envelope.unwrap()["data"]["code"], 97319);
            }
        }
    }

    #[test]
    fn empty_stdout_is_a_tool_error_regardless_of_exit_code() {
        for exit_code in [0, 1] {
            let output = std::process::Output {
                status: std::process::ExitStatus::from_raw(exit_code << 8),
                stdout: Vec::new(),
                stderr: b"usage".to_vec(),
            };
            let capture = parse_policy_check_output(&output);
            assert_eq!(capture.status, "tool_error");
            assert_eq!(capture.tool_exit_code, exit_code);
            assert!(capture.envelope.is_none());
        }
    }
}
