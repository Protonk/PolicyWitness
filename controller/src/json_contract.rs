//! The envelope frame: the outer JSON object every controller-family binary
//! prints (`kind`, `generated_at_unix_ms`, `build`, `result`,
//! `data`). `policy-witness` uses this file as a module; `sbpl-check`
//! includes it by `#[path]`, so one frame
//! and one build contract cover the family. The frame and generated
//! record projections emit deterministic fields without a semantic JSON tree.

use serde::Serialize;

#[cfg(not(test))]
pub const BUILD_CONTRACT: &str = match option_env!("PW_BUILD_CONTRACT") {
    Some(value) => {
        if value.is_empty() {
            "unbound"
        } else {
            value
        }
    }
    None => "unbound",
};
#[cfg(test)]
pub const BUILD_CONTRACT: &str = "test:policy-witness";

#[cfg(test)]
use serde_json::Value;
use std::time::{SystemTime, UNIX_EPOCH};

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
/// hash) and passes it to cargo beside the exact build contract. A plain
/// `cargo build` has unknown provenance and an unbound contract.
#[derive(Serialize)]
struct BuildStamp {
    commit: &'static str,
    contract: &'static str,
    describe: &'static str,
    number: &'static str,
    version: &'static str,
}
fn build_stamp() -> BuildStamp {
    BuildStamp {
        contract: BUILD_CONTRACT.into(),
        commit: option_env!("PW_BUILD_COMMIT").unwrap_or("unknown"),
        describe: option_env!("PW_BUILD_DESCRIBE").unwrap_or("unknown"),
        number: option_env!("PW_BUILD_NUMBER").unwrap_or("unknown"),
        version: option_env!("PW_BUILD_VERSION").unwrap_or("unknown"),
    }
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
        assert_eq!(parsed["build"]["contract"], BUILD_CONTRACT);
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
    fn public_identity_is_in_the_build_frame() {
        let value: Value =
            serde_json::from_str(&render_envelope("version", tests_result_ok(), &()).unwrap())
                .unwrap();
        assert_eq!(value["build"]["contract"], BUILD_CONTRACT);
        assert!(value.get("schema_version").is_none());
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
