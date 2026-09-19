//! Small shared utilities for the controller.
//!
//! These helpers keep run-time metadata consistent across modules.

use std::time::{SystemTime, UNIX_EPOCH};

// Bound captured output to keep envelopes predictable when tools are noisy.
pub const MAX_CAPTURE_BYTES: usize = 1024 * 1024;

pub fn now_unix_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

pub fn truncate_output(bytes: &[u8]) -> (String, bool) {
    if bytes.len() <= MAX_CAPTURE_BYTES {
        return (String::from_utf8_lossy(bytes).to_string(), false);
    }
    (
        String::from_utf8_lossy(&bytes[..MAX_CAPTURE_BYTES]).to_string(),
        true,
    )
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
    pub fn unavailable(note: String) -> Self {
        Self {
            stdout_parse_error: None,
            stdout_truncated: false,
            stdout_capture_error: None,
            stdout_bytes_received: None,
            stdout_bytes_retained: None,
            stderr_bytes_received: None,
            stderr_bytes_retained: None,
            capture_limit_bytes: MAX_CAPTURE_BYTES,
            stdout_raw: None,
            stderr: note,
            stderr_truncated: false,
        }
    }
}

pub fn capture_json_output(
    out: &std::process::Output,
    producer: &str,
) -> (JsonOutputCapture, Option<serde_json::Value>) {
    let (stdout, stdout_truncated) = truncate_output(&out.stdout);
    let (stderr, stderr_truncated) = truncate_output(&out.stderr);
    // Command::output collected all bytes: this is a retention cap, not a
    // streaming memory limit. A truncated prefix is never parsed as evidence.
    let stdout_capture_error =
        stdout_truncated.then(|| {
            format!(
        "controller truncated {producer} stdout: received {} bytes, retained {} bytes (cap {})",
        out.stdout.len(), out.stdout.len().min(MAX_CAPTURE_BYTES), MAX_CAPTURE_BYTES)
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
            stdout_bytes_retained: Some(out.stdout.len().min(MAX_CAPTURE_BYTES)),
            stderr_bytes_received: Some(out.stderr.len()),
            stderr_bytes_retained: Some(out.stderr.len().min(MAX_CAPTURE_BYTES)),
            capture_limit_bytes: MAX_CAPTURE_BYTES,
            stdout_raw,
            stderr,
            stderr_truncated,
        },
        parsed,
    )
}

#[cfg(test)]
pub fn receiver_fixture(valid: &str, mode: &str) -> std::process::Output {
    // Independent child emits original bytes, including invalid bytes that
    // cannot be produced by a normal serde String envelope.
    let script = r#"import sys
p = sys.argv[1].encode()
m = sys.argv[2]
if m == 'oversized': p = p[:-1] + b',"detail":"' + b'x'*1048576 + b'"}'
if m == 'utf8': p = p[:-1] + b',"detail":"' + bytes([255]) + b'"}'
if m == 'malformed': p = b'{'
if m == 'empty': p = b''
if m == 'missing': p = b'{"data":{"diagnostic":"future diagnostic","code":97319}}'
sys.stdout.buffer.write(p)
sys.stderr.buffer.write(bytes([0xe2,0x82,0xac])*349526)
"#;
    let output = std::process::Command::new("/usr/bin/python3")
        .args(["-c", script, valid, mode])
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
