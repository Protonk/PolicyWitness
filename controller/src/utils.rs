//! Small shared utilities for the controller.
//!
//! These helpers keep run-time metadata consistent across modules.

use std::time::{SystemTime, UNIX_EPOCH};

// Bound captured output to keep envelopes predictable when tools are noisy.
const MAX_CAPTURE_BYTES: usize = 1024 * 1024;

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
