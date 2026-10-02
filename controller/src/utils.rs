//! Small shared utilities for the controller.
//!
//! These helpers keep run-time metadata consistent across modules.

use std::time::{SystemTime, UNIX_EPOCH};

// Per-receiver retention budgets, not peak-memory limits: Command::output
// has already collected both streams for runner and policy helper capture. The runner budget is derived, not tuned:
// three times the synthesized maximal reply (docs/limits.json
// runner_reply_maximum, computed by runner_unit from the field-complete reply
// fixture with every string at its limit), rounded up to a whole 4 MiB.
// Observer capture enforces independent streaming budgets in log_capture.
pub const RUNNER_CAPTURE_BYTES: usize = 72 * 1024 * 1024;
pub const HELPER_CAPTURE_BYTES: usize = 8 * 1024 * 1024;
pub const OBSERVER_CAPTURE_BYTES: usize = crate::log_capture::OBSERVER_STDOUT_BYTES;

/// The controller's observation of writing a request to a child's stdin: how
/// many bytes the pipe accepted and the first write error, if any. An accepted
/// write and a closed writer do not prove that the child read the bytes.
#[derive(serde::Serialize, Clone, Debug, PartialEq)]
pub struct RequestDelivery {
    pub bytes_written: usize,
    pub error: Option<String>,
}

fn write_request(writer: &mut impl std::io::Write, input: &[u8]) -> RequestDelivery {
    let mut written = 0;
    while written < input.len() {
        let remaining = &input[written..input.len().min(written + 64 * 1024)];
        let error = match writer.write(remaining) {
            Ok(0) => std::io::Error::from(std::io::ErrorKind::WriteZero),
            Ok(count) => {
                written += count;
                continue;
            }
            Err(error) if error.kind() == std::io::ErrorKind::Interrupted => continue,
            Err(error) => error,
        };
        return RequestDelivery {
            bytes_written: written,
            error: Some(format!(
                "request delivery failed after {written} bytes: {error}"
            )),
        };
    }
    RequestDelivery {
        bytes_written: written,
        error: writer
            .flush()
            .err()
            .map(|error| format!("request delivery flush failed after {written} bytes: {error}")),
    }
}

/// Run `command` with `input` delivered on its stdin by a writer thread while
/// stdout and stderr are collected concurrently. The writer closes stdin after
/// the last byte. A write failure (for example EPIPE from a child that exited
/// without reading) is recorded in the delivery record, never raised as a
/// signal: the controller ignores SIGPIPE and reads the error from `write`.
pub fn run_with_stdin(
    mut command: std::process::Command,
    input: Vec<u8>,
) -> Result<(std::process::Output, RequestDelivery), String> {
    use std::process::Stdio;
    let mut child = command
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("failed to launch {:?}: {e}", command.get_program()))?;
    let mut stdin = child
        .stdin
        .take()
        .ok_or_else(|| "child stdin was not piped".to_string())?;
    let writer = std::thread::spawn(move || {
        let delivery = write_request(&mut stdin, &input);
        drop(stdin);
        delivery
    });
    let output = child
        .wait_with_output()
        .map_err(|e| format!("failed to collect child output: {e}"))?;
    let delivery = writer
        .join()
        .map_err(|_| "request writer thread panicked".to_string())?;
    Ok((output, delivery))
}

pub fn now_unix_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

pub fn truncate_output(bytes: &[u8], limit: usize) -> (String, bool) {
    if bytes.len() <= limit {
        return (String::from_utf8_lossy(bytes).to_string(), false);
    }
    (String::from_utf8_lossy(&bytes[..limit]).to_string(), true)
}

/// Capture metadata is shared by all controller JSON receivers. Counts refer to
/// original bytes, not the lossy text retained for human-readable context.
#[derive(serde::Serialize)]
pub struct JsonOutputCapture {
    pub stdout_parse_error: Option<String>,
    pub stdout_truncated: bool,
    pub stdout_capture_error: Option<String>,
    pub stdout_bytes_received: Option<usize>,
    pub stdout_bytes_retained: Option<usize>,
    pub stderr_bytes_received: Option<usize>,
    pub stderr_bytes_retained: Option<usize>,
    pub capture_limit_bytes: usize,
    pub stdout_raw: Option<String>,
    pub stderr: String,
    pub stderr_truncated: bool,
}

impl JsonOutputCapture {
    pub fn unavailable(note: String, limit: usize) -> Self {
        Self {
            stdout_parse_error: None,
            stdout_truncated: false,
            stdout_capture_error: None,
            stdout_bytes_received: None,
            stdout_bytes_retained: None,
            stderr_bytes_received: None,
            stderr_bytes_retained: None,
            capture_limit_bytes: limit,
            stdout_raw: None,
            stderr: note,
            stderr_truncated: false,
        }
    }
}

pub fn capture_json_output(
    out: &std::process::Output,
    producer: &str,
    limit: usize,
) -> (JsonOutputCapture, Option<serde_json::Value>) {
    let (stdout, stdout_truncated) = truncate_output(&out.stdout, limit);
    let (stderr, stderr_truncated) = truncate_output(&out.stderr, limit);
    // Command::output collected all bytes: this is a retention cap, not a
    // streaming memory limit. A truncated prefix is never parsed as evidence.
    let stdout_capture_error = stdout_truncated.then(|| {
        format!(
            "controller truncated {producer} stdout: received {} bytes, retained {} bytes (cap {})",
            out.stdout.len(),
            out.stdout.len().min(limit),
            limit
        )
    });
    let mut parsed = None;
    let mut stdout_parse_error = None;
    if !stdout_truncated && !out.stdout.is_empty() {
        match serde_json::from_slice(&out.stdout) {
            Ok(value) => parsed = Some(value),
            Err(error) => stdout_parse_error = Some(error.to_string()),
        }
    }
    let stdout_raw = (stdout_parse_error.is_some() || stdout_truncated).then_some(stdout);
    (
        JsonOutputCapture {
            stdout_parse_error,
            stdout_truncated,
            stdout_capture_error,
            stdout_bytes_received: Some(out.stdout.len()),
            stdout_bytes_retained: Some(out.stdout.len().min(limit)),
            stderr_bytes_received: Some(out.stderr.len()),
            stderr_bytes_retained: Some(out.stderr.len().min(limit)),
            capture_limit_bytes: limit,
            stdout_raw,
            stderr,
            stderr_truncated,
        },
        parsed,
    )
}

#[cfg(test)]
pub fn receiver_fixture(valid: &str, mode: &str, limit: usize) -> std::process::Output {
    // Independent child emits original bytes, including invalid bytes that
    // cannot be produced by a normal serde String envelope.
    // argv[3] is the cap: the oversized stdout exceeds it by construction and
    // the multibyte stderr exceeds it by one to three bytes.
    let script = r#"import sys
p = sys.argv[1].encode()
m = sys.argv[2]
cap = int(sys.argv[3])
if m == 'oversized': p = p[:-1] + b',"detail":"' + b'x'*cap + b'"}'
if m == 'utf8': p = p[:-1] + b',"detail":"' + bytes([255]) + b'"}'
if m == 'malformed': p = b'{'
if m == 'empty': p = b''
if m == 'missing': p = b'{"data":{"diagnostic":"future diagnostic","code":97319}}'
sys.stdout.buffer.write(p)
sys.stderr.buffer.write(bytes([0xe2,0x82,0xac])*(cap//3+1))
"#;
    let cap = limit.to_string();
    let output = std::process::Command::new("/usr/bin/python3")
        .args(["-c", script, valid, mode, &cap])
        .output()
        .unwrap();
    assert!(output.status.success());
    output
}

#[cfg(test)]
pub fn transport_diagnostics() -> serde_json::Value {
    let inputs: serde_json::Value = serde_json::from_str(include_str!(
        "../../tests/fixtures/diagnostic_transport/cases.json"
    ))
    .unwrap();
    inputs["diagnostics"].clone()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::os::unix::process::ExitStatusExt;

    #[test]
    fn delivery_counts_short_writes_before_a_failure() {
        use std::io::{self, Write};
        struct PartialWriter {
            calls: usize,
            accepted: Vec<u8>,
        }
        impl Write for PartialWriter {
            fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
                self.calls += 1;
                match self.calls {
                    1 | 3 => {
                        self.accepted.extend_from_slice(&bytes[..7]);
                        Ok(7)
                    }
                    2 => Err(io::ErrorKind::Interrupted.into()),
                    _ => Err(io::ErrorKind::BrokenPipe.into()),
                }
            }
            fn flush(&mut self) -> io::Result<()> {
                panic!("a failed delivery must not flush")
            }
        }
        let input = b"abcdefghijklmnopqrstuvwxyz";
        let mut writer = PartialWriter {
            calls: 0,
            accepted: Vec::new(),
        };
        let delivery = write_request(&mut writer, input);
        assert_eq!(writer.accepted, input[..14]);
        assert_eq!(delivery.bytes_written, writer.accepted.len());
        assert!(delivery.error.unwrap().contains("after 14 bytes"));
    }

    #[test]
    fn arbitrary_budgets_preserve_counts_at_every_unicode_cut() {
        for scalar in ["é", "€", "😀"] {
            let bytes = format!("\"{scalar}\"").into_bytes();
            let out = std::process::Output {
                status: std::process::ExitStatus::from_raw(0),
                stdout: bytes.clone(),
                stderr: scalar.as_bytes().to_vec(),
            };
            for limit in 0..=bytes.len() + 1 {
                let (capture, parsed) = capture_json_output(&out, "fixture", limit);
                assert_eq!(capture.capture_limit_bytes, limit);
                assert_eq!(capture.stdout_bytes_received, Some(bytes.len()));
                assert_eq!(capture.stdout_bytes_retained, Some(bytes.len().min(limit)));
                assert_eq!(capture.stderr_bytes_received, Some(scalar.len()));
                assert_eq!(capture.stderr_bytes_retained, Some(scalar.len().min(limit)));
                assert_eq!(
                    capture.stderr,
                    String::from_utf8_lossy(&scalar.as_bytes()[..scalar.len().min(limit)])
                );
                assert!(capture.stdout_parse_error.is_none());
                assert_eq!(capture.stdout_capture_error.is_some(), limit < bytes.len());
                if limit < bytes.len() {
                    assert!(parsed.is_none());
                    assert_eq!(
                        capture.stdout_raw.as_deref(),
                        Some(String::from_utf8_lossy(&bytes[..limit]).as_ref())
                    );
                } else {
                    assert_eq!(parsed, Some(serde_json::json!(scalar)));
                    assert!(capture.stdout_raw.is_none());
                }
            }
        }
    }

    #[test]
    fn producer_and_receiver_budgets_are_independent() {
        for limit in [15, 16, 17] {
            let raw = receiver_fixture("{}", "valid", limit);
            assert_eq!(raw.stderr.len(), 3 * (limit / 3 + 1));
            let (capture, parsed) = capture_json_output(&raw, "fixture", limit);
            assert_eq!(parsed, Some(serde_json::json!({})));
            assert_eq!(capture.stderr_bytes_retained, Some(limit));
            assert!(capture.stderr_truncated);
            let (complete, _) = capture_json_output(&raw, "fixture", raw.stderr.len());
            assert!(!complete.stderr_truncated);
            assert_eq!(
                JsonOutputCapture::unavailable("unavailable".into(), limit).capture_limit_bytes,
                limit
            );
        }
    }
}
