//! Wrapper for invoking the Swift pw-runner-client helper.
//!
//! The Rust controller shells out to the Swift client to perform NSXPC wiring;
//! the JSON output is captured and embedded in the controller envelope. Every
//! controller invocation, a run and `runner verify` alike, delivers the held
//! request string on the client's stdin (`--request -`); the client's
//! positional file form remains for direct use.

use serde::Serialize;
use serde_json::Value;
use std::ffi::OsString;
use std::process::Command;

use crate::app_layout::resolve_contents_macos_tool;
use crate::runner_select::RunnerConnectionKind;
#[cfg(test)]
use crate::utils::RUNNER_CAPTURE_BYTES;
use crate::utils::{
    JsonOutputCapture, RequestDelivery, capture_json_output, now_unix_ms, run_with_stdin,
};

#[derive(Serialize)]
pub struct RunnerClientRun {
    pub argv: Vec<String>,
    pub started_at_unix_ms: u64,
    pub ended_at_unix_ms: u64,
    pub exit_code: i32,
    /// The stdin delivery observation: bytes the pipe accepted and the first
    /// write error. Null only in constructed fixtures.
    pub request_delivery: Option<RequestDelivery>,
    #[serde(flatten)]
    pub output: JsonOutputCapture,
}

fn parse_runner_client_output(
    argv: &[OsString],
    started: u64,
    ended: u64,
    out: &std::process::Output,
    request_delivery: Option<RequestDelivery>,
) -> (RunnerClientRun, Option<Value>) {
    let (output, parsed) = capture_json_output(out, "runner", crate::utils::RUNNER_CAPTURE_BYTES);

    let runner_client = RunnerClientRun {
        argv: argv
            .iter()
            .map(|s| s.to_string_lossy().to_string())
            .collect(),
        started_at_unix_ms: started,
        ended_at_unix_ms: ended,
        exit_code: out.status.code().unwrap_or(1),
        request_delivery,
        output,
    };

    (runner_client, parsed)
}

fn client_argv(
    timeout_ms: u64,
    connection: &RunnerConnectionKind,
) -> Result<Vec<OsString>, String> {
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
    Ok(argv)
}

/// Deliver `request` on the client's stdin and capture its reply. A delivery
/// error is returned inside the capture, never as an `Err`: the caller decides
/// its precedence over the captured reply.
pub fn run_pw_runner_client(
    service_name: &str,
    request: &str,
    timeout_ms: u64,
    connection: &RunnerConnectionKind,
) -> Result<(RunnerClientRun, Option<Value>), String> {
    let mut argv = client_argv(timeout_ms, connection)?;
    argv.push(OsString::from("--request"));
    argv.push(OsString::from("-"));
    argv.push(OsString::from(service_name));
    run_client_stdin(&argv, request.as_bytes().to_vec())
}

/// The recorded span brackets the child's whole lifetime: `started` is taken
/// before the spawn and `ended` after the exit is collected. Deny-log capture
/// requests this wall-clock span and rejects reversed endpoints. Two readings
/// do not establish clock continuity throughout execution.
fn run_client_stdin(
    argv: &[OsString],
    request: Vec<u8>,
) -> Result<(RunnerClientRun, Option<Value>), String> {
    run_client_stdin_with_clock(argv, request, now_unix_ms)
}

fn run_client_stdin_with_clock(
    argv: &[OsString],
    request: Vec<u8>,
    mut clock: impl FnMut() -> u64,
) -> Result<(RunnerClientRun, Option<Value>), String> {
    let started = clock();
    let mut command = Command::new(&argv[0]);
    command.args(&argv[1..]);
    let (out, delivery) = run_with_stdin(command, request)
        .map_err(|e| format!("failed to run pw-runner-client: {e}"))?;
    let ended = clock();
    Ok(parse_runner_client_output(
        argv,
        started,
        ended,
        &out,
        Some(delivery),
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::process::Stdio;

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
        let (capture, parsed) = parse_runner_client_output(&[], 0, 1, &output, None);
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
        let (capture, parsed) = parse_runner_client_output(&argv, 0, 1, &output, None);
        (capture, parsed, output.stdout)
    }

    #[test]
    fn transport_preserves_current_replies_with_unfamiliar_values_and_other_versions() {
        use serde_json::json;
        let current = i64::from(crate::json_contract::RESPONSE_SCHEMA_VERSION);
        // A current-version reply whose strings the controller does not
        // recognize is received unchanged: the version gate and the readers
        // decide later, never the transport.
        let mut replies = vec![
            json!({"schema_version": current, "normalized_outcome": "ok", "steps": [{
            "step_id": "spawn",
            "sandbox_check": {"outcome": "allow", "rc": 0, "native_rc": 0, "path_diagnostics": {
                "input": "/submitted", "observer": "runner_host", "phase": "after_orchestration"}},
            "attempt": {"outcome": "exec_failed", "rc": 37, "child_pid": 123, "child_exit_code": 37,
                "stdout": "controlled marker", "requested_kind": "exec", "requested_action": "spawn"},
            "comparison": {"observation": "succeeded", "observation_basis": "spawned_child",
                "operation_relation": "matched", "target_relation": "same_submitted",
                "order": "future_order", "limitations": ["future_evidence_limit"]}}],
            "runner_subprocess": {"ordering": {
                "collection_closed_before_proceed": true, "proceed_set": true,
                "proceed_observed": true, "validator_disposition": "unconfirmed",
                "worker_lifetime_established": true, "protocol_violations": ["future_fault"]}},
            "validator_spawn_failure": {
                "origin": "runner_host", "operation": "posix_spawn",
                "executable_path": "/unknown/validator-\"\u{e9}\"", "return_code": 2147483647,
                "diagnostic": "unfamiliar native launch diagnostic"}}),
        ];
        // Other and malformed versions are transported as received; nothing
        // here coerces or rejects them.
        for version in [current - 1, current + 1] {
            replies.push(
                json!({"schema_version": version, "steps": [{"step_id": "s", "drift": false}]}),
            );
        }
        replies.push(json!({"schema_version": current.to_string(), "steps": []}));
        replies.push(json!({"steps": []}));
        for original in replies {
            let output = crate::utils::receiver_fixture(
                &original.to_string(),
                "valid",
                crate::utils::RUNNER_CAPTURE_BYTES,
            );
            let (capture, received) = parse_runner_client_output(&[], 0, 1, &output, None);
            assert!(capture.output.stdout_capture_error.is_none());
            assert_eq!(received, Some(original));
        }
    }

    fn python(program: &str) -> Vec<OsString> {
        vec![
            OsString::from("/usr/bin/python3"),
            OsString::from("-c"),
            OsString::from(program),
        ]
    }

    #[test]
    fn delivery_completes_a_request_larger_than_the_pipe_buffer() {
        // The child reads only after a delay, so the writer must block on a
        // full pipe and still deliver every byte before closing stdin.
        let request = vec![b'x'; 1 << 20];
        let argv = python(
            "import sys, time, json; time.sleep(0.2); data = sys.stdin.buffer.read(); \
             print(json.dumps({'bytes': len(data), 'uniform': data == b'x' * len(data)}))",
        );
        let (run, reply) =
            run_client_stdin_with_clock(&argv, request.clone(), now_unix_ms).unwrap();
        assert_eq!(
            run.request_delivery,
            Some(RequestDelivery {
                bytes_written: request.len(),
                error: None
            })
        );
        assert_eq!(
            reply,
            Some(serde_json::json!({"bytes": request.len(), "uniform": true}))
        );
        assert_eq!(run.exit_code, 0);
        let wire = serde_json::to_value(&run).unwrap();
        assert_eq!(wire["request_delivery"]["bytes_written"], request.len());
        assert!(wire["request_delivery"]["error"].is_null());
    }

    #[test]
    fn a_child_that_exits_without_reading_breaks_the_pipe_without_terminating_the_controller() {
        let request = vec![b'x'; 1 << 20];
        let argv = python("import sys; sys.exit(3)");
        let (run, reply) =
            run_client_stdin_with_clock(&argv, request.clone(), now_unix_ms).unwrap();
        let delivery = run.request_delivery.clone().unwrap();
        let error = delivery.error.expect("the broken pipe is recorded");
        assert!(
            error.contains("request delivery failed after") && error.contains("Broken pipe"),
            "{error}"
        );
        assert!(delivery.bytes_written < request.len());
        assert!(reply.is_none());
        assert_eq!(run.exit_code, 3);
        assert!(run.output.stdout_parse_error.is_some() || run.output.stdout_raw.is_none());
    }

    #[test]
    fn a_delivery_error_is_recorded_beside_a_captured_failure_reply() {
        let request = vec![b'x'; 1 << 20];
        let argv = python(
            "import sys, json; print(json.dumps({'schema_version': 0, 'normalized_outcome': \
             'xpc_error', 'error': 'controlled failure reply'})); sys.exit(1)",
        );
        let (run, reply) = run_client_stdin_with_clock(&argv, request, now_unix_ms).unwrap();
        let delivery = run.request_delivery.clone().unwrap();
        assert!(
            delivery
                .error
                .as_deref()
                .unwrap_or("")
                .contains("Broken pipe")
        );
        let reply = reply.expect("the failure reply is captured beside the delivery error");
        assert_eq!(reply["normalized_outcome"], "xpc_error");
        assert_eq!(reply["error"], "controlled failure reply");
        assert_eq!(run.exit_code, 1);
    }

    #[test]
    fn unfamiliar_diagnostics_survive_runner_capture() {
        let records = crate::utils::transport_diagnostics();
        let original = serde_json::json!({"data": {"diagnostics": records},
            "result": {"ok": false, "normalized_outcome": "runner_failed", "rc": 1}});
        for mode in ["valid", "oversized"] {
            let output = crate::utils::receiver_fixture(
                &original.to_string(),
                mode,
                crate::utils::RUNNER_CAPTURE_BYTES,
            );
            let (capture, received) = parse_runner_client_output(&[], 0, 1, &output, None);
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
        let (run, parsed) = run_client_stdin(&argv, Vec::new()).unwrap();
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
            let (run, _) =
                run_client_stdin_with_clock(&argv, Vec::new(), || readings.next().unwrap())
                    .unwrap();
            assert!(readings.next().is_none());
            assert_eq!(
                (run.started_at_unix_ms, run.ended_at_unix_ms),
                (started, ended)
            );
            assert_eq!(run.exit_code, 0);
            let window =
                SandboxLogWindow::runner_client_span(run.started_at_unix_ms, run.ended_at_unix_ms);
            assert_eq!(window.pad_seconds, 2);
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
        let (capture, parsed, full) = producer(&format!(
            "import sys; sys.stdout.write('{{\"value\":\"' + 'x'*{} + '\"}}')",
            RUNNER_CAPTURE_BYTES
        ));
        assert!(
            serde_json::from_slice::<Value>(&full).is_ok(),
            "producer emitted valid complete JSON"
        );
        assert!(parsed.is_none());
        let wire = serde_json::to_value(&capture).unwrap();
        assert_eq!(wire["stdout_bytes_received"], RUNNER_CAPTURE_BYTES + 12);
        assert_eq!(wire["stdout_bytes_retained"], RUNNER_CAPTURE_BYTES);
        assert!(
            wire["stdout_capture_error"]
                .as_str()
                .unwrap()
                .contains("controller truncated")
        );
        assert_eq!(
            capture.output.stdout_bytes_received,
            Some(RUNNER_CAPTURE_BYTES + 12)
        );
        assert_eq!(
            capture.output.stdout_bytes_retained,
            Some(RUNNER_CAPTURE_BYTES)
        );
        assert_eq!(capture.output.capture_limit_bytes, RUNNER_CAPTURE_BYTES);
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
        // stdout: the cap falls inside a three-byte character; stderr exceeds the
        // cap with whole three-byte characters, regardless of the cap modulo three.
        let (capture, parsed, full) = producer(&format!(
            "import sys; sys.stdout.buffer.write(b'{{\"v\":\"' + b'x'*({} - 7) + bytes([0xe2,0x82,0xac]) + b'\"}}'); sys.stderr.buffer.write(bytes([0xe2,0x82,0xac])*{})",
            RUNNER_CAPTURE_BYTES,
            RUNNER_CAPTURE_BYTES / 3 + 1
        ));
        assert!(serde_json::from_slice::<Value>(&full).is_ok());
        assert!(parsed.is_none());
        assert_eq!(
            capture.output.stdout_bytes_received,
            Some(RUNNER_CAPTURE_BYTES + 4)
        );
        assert_eq!(
            capture.output.stdout_bytes_retained,
            Some(RUNNER_CAPTURE_BYTES)
        );
        assert_eq!(
            capture.output.stderr_bytes_received,
            Some(3 * (RUNNER_CAPTURE_BYTES / 3 + 1))
        );
        assert_eq!(
            capture.output.stderr_bytes_retained,
            Some(RUNNER_CAPTURE_BYTES)
        );
        let text = capture.output.stdout_raw.unwrap();
        assert!(text.ends_with('\u{fffd}'));
        assert_eq!(text.len(), RUNNER_CAPTURE_BYTES + 2);
        assert!(capture.output.stdout_capture_error.is_some());
        assert!(capture.output.stdout_parse_error.is_none());
    }
}
