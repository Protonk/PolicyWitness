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
use crate::utils::{capture_json_output, now_unix_ms, JsonOutputCapture};

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

    let started = now_unix_ms();
    let out = Command::new(&argv[0])
        .args(&argv[1..])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run pw-runner-client: {e}"))?;
    let ended = now_unix_ms();
    Ok(parse_runner_client_output(&argv, started, ended, &out))
}

#[cfg(test)]
mod tests {
    use super::*;

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
    fn valid_oversized_producer_is_receiver_loss_not_malformed_json() {
        let (capture, parsed, full) =
            producer("import sys; sys.stdout.write('{\"value\":\"' + 'x'*1048576 + '\"}')");
        assert!(
            serde_json::from_slice::<Value>(&full).is_ok(),
            "producer emitted valid complete JSON"
        );
        assert!(parsed.is_none());
        let wire = serde_json::to_value(&capture).unwrap();
        assert_eq!(wire["stdout_bytes_received"], MAX_CAPTURE_BYTES + 12);
        assert_eq!(wire["stdout_bytes_retained"], MAX_CAPTURE_BYTES);
        assert!(wire["stdout_capture_error"]
            .as_str()
            .unwrap()
            .contains("controller truncated"));
        assert_eq!(
            capture.output.stdout_bytes_received,
            Some(MAX_CAPTURE_BYTES + 12)
        );
        assert_eq!(
            capture.output.stdout_bytes_retained,
            Some(MAX_CAPTURE_BYTES)
        );
        assert_eq!(capture.output.capture_limit_bytes, 1048576);
        assert!(capture.output.stdout_truncated);
        assert!(capture.output.stdout_parse_error.is_none());
        assert!(capture
            .output
            .stdout_capture_error
            .unwrap()
            .contains("controller truncated"));
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
        let (capture, parsed, full) = producer("import sys; sys.stdout.buffer.write(b'{\"v\":\"' + b'x'*(1048576-7) + bytes([0xe2,0x82,0xac]) + b'\"}'); sys.stderr.buffer.write(bytes([0xe2,0x82,0xac])*349526)");
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
        assert_eq!(capture.output.stderr_bytes_received, Some(1048578));
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
