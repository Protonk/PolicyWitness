//! Helpers for reading and patching request JSON.
//!
//! We never mutate user-provided request files. Any injected fields (runner
//! mode) are written to a temp copy and used for the single run.

use serde_json::Value;
use std::path::{Path, PathBuf};

use crate::utils::now_unix_ms;

pub fn read_json_file(path: &Path, label: &str) -> Result<Value, String> {
    let text = std::fs::read_to_string(path)
        .map_err(|e| format!("failed to read {label}: {e}"))?;
    serde_json::from_str(&text).map_err(|e| format!("failed to parse {label}: {e}"))
}

pub fn write_temp_request(value: &Value) -> Result<PathBuf, String> {
    let temp_dir = std::env::temp_dir().join("policy-witness");
    std::fs::create_dir_all(&temp_dir)
        .map_err(|e| format!("failed to create temp dir: {e}"))?;
    let pid = std::process::id();
    let encoded = serde_json::to_string_pretty(value)
        .map_err(|e| format!("failed to encode request JSON: {e}"))?;
    for attempt in 0..100u32 {
        let candidate = temp_dir.join(format!("request-{pid}-{}-{attempt}.json", now_unix_ms()));
        if candidate.exists() {
            continue;
        }
        std::fs::write(&candidate, &encoded)
            .map_err(|e| format!("failed to write temp request: {e}"))?;
        return Ok(candidate);
    }
    Err("failed to create temp request file".to_string())
}
