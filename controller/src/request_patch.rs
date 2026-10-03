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

/// The marker identifies the accepted input language, not a build revision.
/// Check it before interpreting controller-owned options or named augments.
pub fn validate_request_version(value: &Value) -> Result<(), String> {
    let expected = crate::json_contract::REQUEST_SCHEMA_VERSION;
    match value.get("schema_version") {
        Some(Value::Number(version)) if version.as_f64().is_some_and(|v| v.fract() == 0.0) => {
            if version.as_f64() == Some(f64::from(expected)) {
                Ok(())
            } else {
                Err(format!(
                    "unsupported request schema {version} (expected {expected})"
                ))
            }
        }
        _ => Err(format!(
            "schema_version must be an integer (expected {expected})"
        )),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn request_version_is_an_exact_value_not_an_implementation_range() {
        let current = crate::json_contract::REQUEST_SCHEMA_VERSION;
        for version in [json!(current), json!(f64::from(current))] {
            assert!(validate_request_version(&json!({"schema_version": version})).is_ok());
        }
        for version in [json!(-1), json!(0), json!(1), json!(2), json!(current + 1)] {
            let error = validate_request_version(&json!({"schema_version": version})).unwrap_err();
            assert!(error.contains("unsupported request schema"));
            assert!(error.contains(&format!("expected {current}")));
        }
        for version in [json!(null), json!(true), json!("3"), json!(3.5), json!([])] {
            assert!(validate_request_version(&json!({"schema_version": version})).is_err());
        }
        assert!(validate_request_version(&json!({})).is_err());
    }
}
