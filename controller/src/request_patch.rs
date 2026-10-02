//! Reading request JSON.
//!
//! The controller never mutates user-provided request files and writes no
//! temporary copy: the parsed value is resolved in memory and serialized once
//! for delivery.

use serde_json::Value;
use std::path::Path;

pub fn read_json_file(path: &Path, label: &str) -> Result<Value, String> {
    let text = std::fs::read_to_string(path).map_err(|e| format!("failed to read {label}: {e}"))?;
    serde_json::from_str(&text).map_err(|e| format!("failed to parse {label}: {e}"))
}
