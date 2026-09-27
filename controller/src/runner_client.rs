//! Wrapper for invoking the Swift pw-runner-client helper.
//!
//! The Rust controller shells out to the Swift client to perform NSXPC wiring;
//! the JSON output is captured and embedded in the controller envelope.

use serde::Serialize;
use serde_json::Value;
use std::ffi::OsString;
use std::process::{Command, Stdio};

use crate::app_layout::resolve_contents_macos_tool;
use crate::runner_select::RunnerConnectionKind;
#[cfg(test)]
use crate::utils::MAX_CAPTURE_BYTES;
use crate::utils::{JsonOutputCapture, capture_json_output, now_unix_ms};

#[derive(Serialize)]
pub struct RunnerClientRun {
    pub argv: Vec<String>,
    pub started_at_unix_ms: u64,
    pub ended_at_unix_ms: u64,
    pub exit_code: i32,
    #[serde(flatten)]
    pub output: JsonOutputCapture,
}

fn parse_runner_client_output(
    argv: &[OsString],
    started: u64,
    ended: u64,
    out: &std::process::Output,
) -> (RunnerClientRun, Option<Value>) {
    let (output, parsed) = capture_json_output(out, "runner");

    let runner_client = RunnerClientRun {
        argv: argv
            .iter()
            .map(|s| s.to_string_lossy().to_string())
            .collect(),
        started_at_unix_ms: started,
        ended_at_unix_ms: ended,
        exit_code: out.status.code().unwrap_or(1),
        output,
    };

    (runner_client, parsed)
}

pub fn run_pw_runner_client(
    service_name: &str,
    request_path: &std::path::Path,
    timeout_ms: u64,
    connection: &RunnerConnectionKind,
) -> Result<(RunnerClientRun, Option<Value>), String> {
    let tool = resolve_contents_macos_tool("pw-runner-client")?;
    let mut argv = vec![
        tool.into_os_string(),
        OsString::from("run"),
        OsString::from("--timeout-ms"),
        OsString::from(format!("{timeout_ms}")),
    ];
    match connection {
        RunnerConnectionKind::XpcService => {}
        RunnerConnectionKind::MachService { privileged } => {
            argv.push(OsString::from("--mach-service"));
            if *privileged {
                argv.push(OsString::from("--privileged"));
            }
        }
    }
    argv.push(OsString::from(service_name));
    argv.push(request_path.as_os_str().to_os_string());
    run_client_argv(&argv)
}

/// The recorded span brackets the child's whole lifetime: `started` is taken
/// before the spawn and `ended` after the exit is collected. Deny-log capture
/// requests this wall-clock span and rejects reversed endpoints. Two readings
/// do not establish clock continuity throughout execution.
fn run_client_argv(argv: &[OsString]) -> Result<(RunnerClientRun, Option<Value>), String> {
    run_client_argv_with_clock(argv, now_unix_ms)
}

fn run_client_argv_with_clock(
    argv: &[OsString],
    mut clock: impl FnMut() -> u64,
) -> Result<(RunnerClientRun, Option<Value>), String> {
    let started = clock();
    let out = Command::new(&argv[0])
        .args(&argv[1..])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run pw-runner-client: {e}"))?;
    let ended = clock();
    Ok(parse_runner_client_output(argv, started, ended, &out))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn path_wire_fixtures_survive_capture_serialization_and_independent_consumer() {
        use std::io::Write;
        let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("..");
        let fixture = root.join("tests/fixtures/contract/path_diagnostics.json");
        let original: Value = serde_json::from_slice(&std::fs::read(&fixture).unwrap()).unwrap();
        let output = Command::new("/usr/bin/python3")
            .args([
                "-B",
                "-c",
                "import sys; sys.stdout.buffer.write(open(sys.argv[1], 'rb').read())",
            ])
            .arg(&fixture)
            .output()
            .unwrap();
        assert!(output.status.success());
        let (capture, parsed) = parse_runner_client_output(&[], 0, 1, &output);
        assert!(capture.output.stdout_capture_error.is_none());
        assert_eq!(parsed.as_ref(), Some(&original));
        // Forward valid and malformed representations unchanged. The independent
        // consumer owns interpretation; the controller must not normalize them.
        let mut consumer = Command::new("/usr/bin/python3")
            .arg("-B")
            .arg(root.join("tests/lib/path_diagnostics_contract.py"))
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .unwrap();
        consumer
            .stdin
            .take()
            .unwrap()
            .write_all(&serde_json::to_vec(&parsed.unwrap()).unwrap())
            .unwrap();
        let answer = consumer.wait_with_output().unwrap();
        assert!(
            answer.status.success(),
            "{}",
            String::from_utf8_lossy(&answer.stderr)
        );
    }

    // Real subprocess producers exercise full capture before prefix selection.
    fn producer(program: &str) -> (RunnerClientRun, Option<Value>, Vec<u8>) {
        let argv = vec![
            OsString::from("/usr/bin/python3"),
            OsString::from("-c"),
            OsString::from(program),
        ];
        let output = Command::new(&argv[0]).args(&argv[1..]).output().unwrap();
        assert!(output.status.success());
        let (capture, parsed) = parse_runner_client_output(&argv, 0, 1, &output);
        (capture, parsed, output.stdout)
    }

    #[test]
    fn consumer_distinctions_and_legacy_absences_survive_receiver_transport() {
        for version in 4..=8 {
            let mut original = serde_json::json!({"schema_version": version, "steps": [{
                "step_id": "spawn", "drift": false,
                "sandbox_check": {"outcome": "allow", "native_rc": 0},
                "attempt": {"outcome": "exec_failed", "rc": 37, "child_pid": 123,
                            "child_exit_code": 37, "stdout": "controlled marker"}
            }]});
            if version >= 7 {
                original["steps"][0]["comparison"] = serde_json::json!({
                    "scope": "submitted_operation_and_target", "prediction": "allow",
                    "observation": "succeeded", "observation_basis": "spawned_child",
                    "operation_relation": "matched", "target_relation": "same_submitted",
                    "conclusion": "agreement", "limitations": [
                        "query_attempt_order_unestablished", "state_stability_unestablished",
                        "exec_result_failed_after_spawn", "sandbox_attribution_unestablished",
                        "future_evidence_limit"]});
                original["steps"][0]["attempt"]["requested_kind"] = serde_json::json!("exec");
                original["steps"][0]["attempt"]["requested_action"] = serde_json::json!("spawn");
                original["steps"][0]["sandbox_check"]["path_diagnostics"] = serde_json::json!({
                    "input": "/submitted", "observer": "runner_host", "phase": "after_orchestration"});
            }
            if version == 8 {
                original["steps"][0]["comparison"]["order"] = serde_json::json!("future_order");
                original["runner_subprocess"] = serde_json::json!({"ordering": {
                    "collection_closed_before_proceed": true, "proceed_set": true,
                    "proceed_observed": true, "validator_disposition": "unconfirmed",
                    "worker_lifetime_established": true, "protocol_violations": []}});
                original["validator_spawn_failure"] = serde_json::json!({
                    "origin": "runner_host", "operation": "posix_spawn",
                    "executable_path": "/unknown/validator-\"é\"", "return_code": 2147483647,
                    "diagnostic": "unfamiliar native launch diagnostic"});
            }
            let output = crate::utils::receiver_fixture(&original.to_string(), "valid");
            let (capture, received) = parse_runner_client_output(&[], 0, 1, &output);
            assert!(capture.output.stdout_capture_error.is_none());
            assert_eq!(received, Some(original));
        }
    }

    #[test]
    fn unfamiliar_diagnostics_survive_runner_capture() {
        let records = crate::utils::transport_diagnostics();
        let original = serde_json::json!({"data": {"diagnostics": records},
            "result": {"ok": false, "normalized_outcome": "runner_failed", "rc": 1}});
        for mode in ["valid", "oversized"] {
            let output = crate::utils::receiver_fixture(&original.to_string(), mode);
            let (capture, received) = parse_runner_client_output(&[], 0, 1, &output);
            if mode == "valid" {
                assert_eq!(received, Some(original.clone()));
                assert!(capture.output.stdout_capture_error.is_none());
            } else {
                assert!(serde_json::from_slice::<Value>(&output.stdout).is_ok());
                assert!(received.is_none());
                assert!(capture.output.stdout_capture_error.is_some());
                assert!(capture.output.stdout_parse_error.is_none());
            }
        }
    }

    #[test]
    fn recorded_span_brackets_the_child_process() {
        // The child reports its own clock twice, around a sleep; both readings
        // must fall inside the span the controller records for it.
        let argv = vec![
            OsString::from("/usr/bin/python3"),
            OsString::from("-c"),
            OsString::from(
                "import json, time; a = int(time.time() * 1000); time.sleep(0.3); \
                 b = int(time.time() * 1000); print(json.dumps({'a': a, 'b': b}))",
            ),
        ];
        let (run, parsed) = run_client_argv(&argv).unwrap();
        let reply = parsed.expect("child reply is JSON");
        let (a, b) = (reply["a"].as_u64().unwrap(), reply["b"].as_u64().unwrap());
        assert!(
            run.started_at_unix_ms <= a,
            "{} <= {a}",
            run.started_at_unix_ms
        );
        assert!(b <= run.ended_at_unix_ms, "{b} <= {}", run.ended_at_unix_ms);
        assert!(run.ended_at_unix_ms - run.started_at_unix_ms >= 300);
        assert_eq!(run.exit_code, 0);
    }

    #[test]
    fn backwards_clock_readings_are_retained_without_a_log_scan() {
        use crate::sandbox_log::{SandboxLogWindow, capture_sandbox_logs, observer_argv};
        let argv = vec![OsString::from("/usr/bin/true")];
        for (started, ended) in [(5_000, 4_000), (5_999, 5_001)] {
            let mut readings = [started, ended].into_iter();
            let (run, _) = run_client_argv_with_clock(&argv, || readings.next().unwrap()).unwrap();
            assert!(readings.next().is_none());
            assert_eq!(
                (run.started_at_unix_ms, run.ended_at_unix_ms),
                (started, ended)
            );
            assert_eq!(run.exit_code, 0);
            let window =
                SandboxLogWindow::runner_client_span(run.started_at_unix_ms, run.ended_at_unix_ms);
            assert!(window.start.is_none() && window.end.is_none());
            assert!(observer_argv("observer".into(), 42, "pw-probe-runner", &window).is_err());
            // A unit-test binary has no bundle helper to resolve. This must
            // return without even resolving, let alone spawning, the observer.
            let capture = capture_sandbox_logs(42, "pw-probe-runner", window).unwrap();
            assert_eq!(capture.capture_status, "invalid_window");
            assert!(capture.observer.is_none());
            assert!(capture.deny_events.is_none() && capture.observed_deny.is_none());
            assert!(capture.output.stdout_bytes_received.is_none());
            assert!(capture.output.stderr.contains("wall clock moved backwards"));
        }
    }

    #[test]
    fn valid_oversized_producer_is_receiver_loss_not_malformed_json() {
        let (capture, parsed, full) =
            producer("import sys; sys.stdout.write('{\"value\":\"' + 'x'*8388608 + '\"}')");
        assert!(
            serde_json::from_slice::<Value>(&full).is_ok(),
            "producer emitted valid complete JSON"
        );
        assert!(parsed.is_none());
        let wire = serde_json::to_value(&capture).unwrap();
        assert_eq!(wire["stdout_bytes_received"], MAX_CAPTURE_BYTES + 12);
        assert_eq!(wire["stdout_bytes_retained"], MAX_CAPTURE_BYTES);
        assert!(
            wire["stdout_capture_error"]
                .as_str()
                .unwrap()
                .contains("controller truncated")
        );
        assert_eq!(
            capture.output.stdout_bytes_received,
            Some(MAX_CAPTURE_BYTES + 12)
        );
        assert_eq!(
            capture.output.stdout_bytes_retained,
            Some(MAX_CAPTURE_BYTES)
        );
        assert_eq!(capture.output.capture_limit_bytes, 8388608);
        assert!(capture.output.stdout_truncated);
        assert!(capture.output.stdout_parse_error.is_none());
        assert!(
            capture
                .output
                .stdout_capture_error
                .unwrap()
                .contains("controller truncated")
        );
    }

    #[test]
    fn malformed_within_cap_is_a_parse_error() {
        let (capture, parsed, full) = producer("import sys; sys.stdout.write('invalid-json')");
        assert!(serde_json::from_slice::<Value>(&full).is_err());
        assert!(parsed.is_none());
        assert_eq!(capture.output.stdout_bytes_received, Some(12));
        assert_eq!(capture.output.stdout_bytes_retained, Some(12));
        assert!(!capture.output.stdout_truncated);
        assert!(capture.output.stdout_capture_error.is_none());
        assert!(capture.output.stdout_parse_error.is_some());
    }

    #[test]
    fn invalid_utf8_is_not_repaired_into_accepted_json() {
        let (capture, parsed, full) =
            producer("import sys; sys.stdout.buffer.write(b'{\"v\":\"' + bytes([255]) + b'\"}')");
        assert!(serde_json::from_slice::<Value>(&full).is_err());
        assert!(parsed.is_none());
        assert!(!capture.output.stdout_truncated);
        assert!(capture.output.stdout_capture_error.is_none());
        assert!(capture.output.stdout_parse_error.is_some());
        assert_eq!(capture.output.stdout_bytes_received, Some(9));
    }

    #[test]
    fn multibyte_cut_counts_bytes_before_lossy_conversion() {
        let (capture, parsed, full) = producer(
            "import sys; sys.stdout.buffer.write(b'{\"v\":\"' + b'x'*(8388608-7) + bytes([0xe2,0x82,0xac]) + b'\"}'); sys.stderr.buffer.write(bytes([0xe2,0x82,0xac])*2796203)",
        );
        assert!(serde_json::from_slice::<Value>(&full).is_ok());
        assert!(parsed.is_none());
        assert_eq!(
            capture.output.stdout_bytes_received,
            Some(MAX_CAPTURE_BYTES + 4)
        );
        assert_eq!(
            capture.output.stdout_bytes_retained,
            Some(MAX_CAPTURE_BYTES)
        );
        assert_eq!(capture.output.stderr_bytes_received, Some(8388609));
        assert_eq!(
            capture.output.stderr_bytes_retained,
            Some(MAX_CAPTURE_BYTES)
        );
        let text = capture.output.stdout_raw.unwrap();
        assert!(text.ends_with('\u{fffd}'));
        assert_eq!(text.len(), MAX_CAPTURE_BYTES + 2);
        assert!(capture.output.stdout_capture_error.is_some());
        assert!(capture.output.stdout_parse_error.is_none());
    }
}
