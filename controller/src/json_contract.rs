//! The envelope frame: the outer JSON object every controller-family binary
//! prints (`kind`, `schema_version`, `generated_at_unix_ms`, `build`, `result`,
//! `data`). `policy-witness` uses this file as a module; `sbpl-check`
//! includes it by `#[path]`, so one frame
//! and one version (`SCHEMA_VERSION`) cover the family. The frame and generated
//! record projections emit deterministic fields without a semantic JSON tree.

use serde::Serialize;
use serde_json::Value;
use std::time::{SystemTime, UNIX_EPOCH};

// BEGIN GENERATED CONTRACT VERSIONS (docs/contract.json via docs/generate_contract.py)
pub const SCHEMA_VERSION: u32 = 13;
/// The accepted request contract, independent of implementation revisions.
pub const REQUEST_SCHEMA_VERSION: u32 = 6;
/// The one runner response schema this controller reads; any other version is refused.
pub const RESPONSE_SCHEMA_VERSION: u32 = 29;
/// Required reservation RPC and client capture protocol.
pub const RUNNER_PROTOCOL_VERSION: u32 = 4;
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

impl JsonResult {
    /// A result the controller or a helper makes itself. `rc`, `errno`,
    /// `stderr` and `stdout` are never set on this path and serialize as null.
    pub fn new(
        ok: bool,
        exit_code: i32,
        normalized_outcome: Option<&str>,
        error: Option<String>,
    ) -> Self {
        JsonResult {
            ok,
            rc: None,
            exit_code: Some(exit_code),
            normalized_outcome: normalized_outcome.map(str::to_string),
            errno: None,
            error,
            stderr: None,
            stdout: None,
        }
    }
}

/// The build stamp says which code produced an envelope. build.sh derives it
/// from git (nearest `v*` tag, commit count, `git describe --dirty`, commit
/// hash) and passes it to cargo; a plain `cargo build` reads "unknown". It is a
/// coordinate, not a contract: the contract numbers say how to read the JSON.
#[derive(Serialize)]
struct BuildStamp {
    commit: &'static str,
    describe: &'static str,
    number: &'static str,
    version: &'static str,
}
fn build_stamp() -> BuildStamp {
    BuildStamp {
        commit: option_env!("PW_BUILD_COMMIT").unwrap_or("unknown"),
        describe: option_env!("PW_BUILD_DESCRIBE").unwrap_or("unknown"),
        number: option_env!("PW_BUILD_NUMBER").unwrap_or("unknown"),
        version: option_env!("PW_BUILD_VERSION").unwrap_or("unknown"),
    }
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

/// Presentation borrows its inputs. It never builds a second semantic tree.
#[derive(Serialize)]
struct Envelope<'a, T: Serialize> {
    build: BuildStamp,
    data: &'a T,
    generated_at_unix_ms: u64,
    kind: &'a str,
    result: JsonResult,
    schema_version: u32,
}

pub fn render_envelope<T: Serialize>(
    kind: &str,
    result: JsonResult,
    data: &T,
) -> Result<String, String> {
    let envelope = Envelope {
        build: build_stamp(),
        data,
        generated_at_unix_ms: now_unix_ms(),
        kind,
        result,
        schema_version: SCHEMA_VERSION,
    };
    let text = serde_json::to_string_pretty(&envelope)
        .map_err(|e| format!("failed to encode JSON: {e}"))?;
    Ok(text)
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
    use serde_json::json;

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
    fn renderer_borrows_nonclone_typed_payload_and_serializes_it_once() {
        use std::cell::Cell;
        struct Payload<'a> {
            calls: &'a Cell<u32>,
        }
        impl Serialize for Payload<'_> {
            fn serialize<S: serde::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
                use serde::ser::SerializeStruct;
                self.calls.set(self.calls.get() + 1);
                let mut record = serializer.serialize_struct("Payload", 2)?;
                record.serialize_field("native_rc", &-1i64)?;
                record.serialize_field("published", &false)?;
                record.end()
            }
        }
        let calls = Cell::new(0);
        let payload = Payload { calls: &calls };
        let text = render_envelope("typed_fixture", result_ok(), &payload).unwrap();
        assert_eq!(calls.get(), 1);
        let public: Value = serde_json::from_str(&text).unwrap();
        assert_eq!(public["data"]["native_rc"], -1);
        assert_eq!(public["data"]["published"], false);
    }

    #[test]
    fn envelope_fields_and_map_payload_have_deterministic_order() {
        let payload = json!({
            "z": "last",
            "m": "middle",
            "a": "first"
        });
        let text = render_envelope("dummy", result_ok(), &payload).expect("render");

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
        let text =
            render_envelope("dummy", tests_result_ok(), &serde_json::json!({})).expect("render");
        let parsed: Value = serde_json::from_str(&text).expect("parse");
        let build = parsed["build"].as_object().expect("build object");
        for key in ["version", "number", "describe", "commit"] {
            assert!(build[key].is_string(), "build.{key} must be a string");
        }
    }

    #[test]
    fn embedded_contract_versions_match_the_manifest_keys() {
        let versions = contract_versions();
        for key in ["request_schema", "response_schema", "controller_envelope"] {
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
