//! JSON envelope helpers for controller output.
//!
//! The controller emits a single JSON object per run. Keys are sorted so
//! envelopes are stable for diffing and hashing.

use serde::Serialize;
use serde_json::{Map, Value};
use std::time::{SystemTime, UNIX_EPOCH};

// BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py)
pub const SCHEMA_VERSION: u32 = 4;
// END GENERATED CONTRACT VERSIONS

#[derive(Serialize, Clone)]
pub struct JsonResult {
    pub ok: bool,
    pub rc: Option<i64>,
    pub exit_code: Option<i32>,
    pub normalized_outcome: Option<String>,
    pub errno: Option<i64>,
    pub error: Option<String>,
    pub stderr: Option<String>,
    pub stdout: Option<String>,
}

/// The build stamp says which code produced an envelope. build.sh derives it
/// from git (nearest `v*` tag, commit count, `git describe --dirty`, commit
/// hash) and passes it to cargo; a plain `cargo build` reads "unknown". It is a
/// coordinate, not a contract: the contract numbers say how to read the JSON.
pub fn build_stamp() -> Value {
    serde_json::json!({
        "version": option_env!("PW_BUILD_VERSION").unwrap_or("unknown"),
        "number": option_env!("PW_BUILD_NUMBER").unwrap_or("unknown"),
        "describe": option_env!("PW_BUILD_DESCRIBE").unwrap_or("unknown"),
        "commit": option_env!("PW_BUILD_COMMIT").unwrap_or("unknown"),
    })
}

/// The wire contract versions this build was made with, embedded from
/// docs/contract.json at compile time for `policy-witness --version`.
pub fn contract_versions() -> Value {
    let manifest: Value =
        serde_json::from_str(include_str!("../../docs/contract.json")).unwrap_or(Value::Null);
    manifest.get("versions").cloned().unwrap_or(Value::Null)
}

fn now_unix_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

fn sort_value(value: &mut Value) {
    match value {
        Value::Array(items) => {
            for item in items {
                sort_value(item);
            }
        }
        Value::Object(map) => {
            // Sort object keys to keep output deterministic across runs.
            let mut entries: Vec<(String, Value)> =
                map.iter().map(|(k, v)| (k.clone(), v.clone())).collect();
            entries.sort_by(|a, b| a.0.cmp(&b.0));
            let mut sorted = Map::new();
            for (key, mut val) in entries {
                sort_value(&mut val);
                sorted.insert(key, val);
            }
            *map = sorted;
        }
        _ => {}
    }
}

fn envelope_value<T: Serialize>(kind: &str, result: JsonResult, data: &T) -> Result<Value, String> {
    let mut value = serde_json::json!({
        "schema_version": SCHEMA_VERSION,
        "kind": kind,
        "generated_at_unix_ms": now_unix_ms(),
        "build": build_stamp(),
        "result": result,
        "data": data,
    });
    sort_value(&mut value);
    Ok(value)
}

pub fn render_envelope<T: Serialize>(
    kind: &str,
    result: JsonResult,
    data: &T,
) -> Result<String, String> {
    let value = envelope_value(kind, result, data)?;
    serde_json::to_string_pretty(&value).map_err(|e| format!("failed to encode JSON: {e}"))
}

#[allow(dead_code)]
pub fn render_envelope_compact<T: Serialize>(
    kind: &str,
    result: JsonResult,
    data: &T,
) -> Result<String, String> {
    let value = envelope_value(kind, result, data)?;
    serde_json::to_string(&value).map_err(|e| format!("failed to encode JSON: {e}"))
}

/// Bounded serialization for the optional observer report. Existing runner and
/// helper rendering keeps its own contract. The caller also bounds its strings,
/// arrays and metadata before constructing the envelope Value.
#[allow(dead_code)]
pub fn render_envelope_limited<T: Serialize>(
    kind: &str,
    result: JsonResult,
    data: &T,
    pretty: bool,
    limit: usize,
) -> Result<String, String> {
    struct LimitedOutput {
        bytes: Vec<u8>,
        limit: usize,
    }
    impl std::io::Write for LimitedOutput {
        fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
            if bytes.len() > self.limit.saturating_sub(self.bytes.len()) {
                return Err(std::io::Error::other(format!(
                    "observer serialization_overflow: limit={}, retained={}, attempted={}",
                    self.limit,
                    self.bytes.len(),
                    self.bytes.len().saturating_add(bytes.len())
                )));
            }
            self.bytes.extend_from_slice(bytes);
            Ok(bytes.len())
        }
        fn flush(&mut self) -> std::io::Result<()> {
            Ok(())
        }
    }
    let value = envelope_value(kind, result, data)?;
    let mut output = LimitedOutput {
        bytes: Vec::new(),
        limit,
    };
    let serialized = if pretty {
        serde_json::to_writer_pretty(&mut output, &value)
    } else {
        serde_json::to_writer(&mut output, &value)
    };
    serialized.map_err(|e| format!("failed to encode bounded JSON: {e}"))?;
    String::from_utf8(output.bytes).map_err(|e| format!("JSON encoder returned invalid UTF-8: {e}"))
}

pub fn print_envelope<T: Serialize>(
    kind: &str,
    result: JsonResult,
    data: &T,
) -> Result<(), String> {
    let text = render_envelope(kind, result, data)?;
    println!("{text}");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde::Serialize;
    use serde_json::json;

    #[derive(Serialize)]
    struct Dummy {
        label: String,
    }

    fn result_ok() -> JsonResult {
        JsonResult {
            ok: true,
            rc: None,
            exit_code: Some(0),
            normalized_outcome: None,
            errno: None,
            error: None,
            stderr: None,
            stdout: None,
        }
    }

    #[test]
    fn compact_envelope_is_single_line() {
        let payload = Dummy {
            label: "ok".to_string(),
        };
        let text = render_envelope_compact("dummy", result_ok(), &payload).expect("render");
        assert!(!text.contains('\n'));
        let parsed: serde_json::Value = serde_json::from_str(&text).expect("parse");
        assert_eq!(parsed["kind"], "dummy");
        assert_eq!(parsed["schema_version"], SCHEMA_VERSION);
    }

    #[test]
    fn envelope_keys_are_sorted() {
        let payload = json!({
            "z": "last",
            "m": "middle",
            "a": "first"
        });
        let text = render_envelope_compact("dummy", result_ok(), &payload).expect("render");

        let keys = [
            "\"build\"",
            "\"data\"",
            "\"generated_at_unix_ms\"",
            "\"kind\"",
            "\"result\"",
            "\"schema_version\"",
        ];
        let mut last = 0usize;
        for key in keys {
            let idx = text
                .find(key)
                .unwrap_or_else(|| panic!("missing key {key} in {text}"));
            assert!(
                idx >= last,
                "expected key order to be sorted; {key} appeared before previous key"
            );
            last = idx;
        }

        let a_idx = text.find("\"a\"").expect("missing nested key a");
        let m_idx = text.find("\"m\"").expect("missing nested key m");
        let z_idx = text.find("\"z\"").expect("missing nested key z");
        assert!(
            a_idx < m_idx && m_idx < z_idx,
            "expected nested keys to be sorted in data object"
        );

        let parsed: serde_json::Value = serde_json::from_str(&text).expect("parse");
        assert_eq!(parsed["schema_version"], SCHEMA_VERSION);
    }
}

#[cfg(test)]
mod build_stamp_tests {
    use super::*;

    #[test]
    fn every_envelope_carries_a_complete_build_stamp() {
        let text = render_envelope_compact("dummy", tests_result_ok(), &serde_json::json!({}))
            .expect("render");
        let parsed: Value = serde_json::from_str(&text).expect("parse");
        let build = parsed["build"].as_object().expect("build object");
        for key in ["version", "number", "describe", "commit"] {
            assert!(build[key].is_string(), "build.{key} must be a string");
        }
    }

    #[test]
    fn embedded_contract_versions_match_the_manifest_keys() {
        let versions = contract_versions();
        for key in [
            "request_schema",
            "response_schema",
            "worker_abi",
            "controller_envelope",
        ] {
            assert!(versions[key].is_u64(), "contract.{key} must be an integer");
        }
        assert_eq!(
            versions["controller_envelope"].as_u64(),
            Some(u64::from(SCHEMA_VERSION))
        );
    }

    fn tests_result_ok() -> JsonResult {
        JsonResult {
            ok: true,
            rc: None,
            exit_code: Some(0),
            normalized_outcome: None,
            errno: None,
            error: None,
            stderr: None,
            stdout: None,
        }
    }
}

#[cfg(test)]
mod contract_manifest {
    // docs/contract.json owns the envelope version; the generated constant
    // above is text, so compare the compiled value with the manifest.
    #[test]
    fn envelope_schema_version_matches_contract_manifest() {
        let manifest: serde_json::Value =
            serde_json::from_str(include_str!("../../docs/contract.json"))
                .expect("docs/contract.json parses");
        assert_eq!(
            manifest["versions"]["controller_envelope"].as_u64(),
            Some(u64::from(super::SCHEMA_VERSION)),
            "SCHEMA_VERSION disagrees with docs/contract.json controller_envelope"
        );
    }
}
