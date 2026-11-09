//! Reading request JSON.
//!
//! The controller never mutates user-provided request files and writes no
//! temporary copy: the parsed value is resolved in memory and serialized once
//! for delivery.

use serde::Serialize;
use serde_json::Value;

/// Shared wire shape with PWRunnerRequestFailure. A null path withholds a
/// location that cannot be reported in full within the diagnostic bounds.
#[derive(Debug, Clone, Serialize)]
pub struct RequestFailure {
    pub code: String,
    pub path: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub expected_contract: Option<String>,
}

#[derive(Debug, Clone)]
pub struct RequestError {
    pub failure: RequestFailure,
    pub message: String,
}

impl RequestError {
    pub fn new(code: &str, path: &[&str], message: impl Into<String>) -> Self {
        Self {
            failure: RequestFailure {
                code: code.into(),
                path: (path.len() <= 8 && path.iter().all(|part| part.len() <= 63))
                    .then(|| path.iter().map(|part| (*part).into()).collect()),
                expected_contract: (path == ["contract"])
                    .then(|| crate::json_contract::BUILD_CONTRACT.into()),
            },
            message: message.into(),
        }
    }
}

impl std::fmt::Display for RequestError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.message)
    }
}

pub fn parse_request(text: &str) -> Result<Value, RequestError> {
    let value: Value = serde_json::from_str(text).map_err(|e| {
        RequestError::new(
            "invalid_json",
            &[],
            format!("failed to parse request.json: {e}"),
        )
    })?;
    if !value.is_object() {
        return Err(RequestError::new(
            if value.is_null() {
                "missing_value"
            } else {
                "type_mismatch"
            },
            &[],
            "request.json must be a JSON object",
        ));
    }
    Ok(value)
}

/// The assertion binds the request to the exact public build contract.
/// Check it before interpreting controller-owned options or named augments.
pub fn validate_request_contract(value: &Value) -> Result<(), RequestError> {
    validate_contract(value, crate::json_contract::BUILD_CONTRACT)
}

pub fn validate_contract(value: &Value, expected: &str) -> Result<(), RequestError> {
    let failure = |code, message: String| {
        let mut error = RequestError::new(code, &["contract"], message);
        error.failure.expected_contract = Some(expected.into());
        error
    };
    match value.get("contract") {
        Some(Value::String(contract))
            if !expected.is_empty() && expected != "unbound" && contract == expected =>
        {
            Ok(())
        }
        Some(Value::String(_)) => Err(failure(
            "unsupported_contract",
            format!("unsupported request contract (expected {expected})"),
        )),
        other => Err(failure(
            match other {
                None => "missing_field",
                Some(Value::Null) => "missing_value",
                _ => "type_mismatch",
            },
            format!("contract must be a string (expected {expected})"),
        )),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn documented_request_failure_path_limits_match_retained_paths() {
        let depth = (0..=128)
            .filter(|&count| {
                RequestError::new("type_mismatch", &vec!["key"; count], "invalid value")
                    .failure
                    .path
                    .is_some()
            })
            .max()
            .unwrap();
        let component_bytes = (0..=256)
            .filter(|&count| {
                RequestError::new("type_mismatch", &[&"x".repeat(count)], "invalid value")
                    .failure
                    .path
                    .is_some()
            })
            .max()
            .unwrap();
        // These scan ceilings are independent of the inventory. Reaching one
        // means the production maximum has not been observed.
        assert!(depth < 128);
        assert!(component_bytes < 256);
        let manifest: Value = serde_json::from_str(include_str!("../../docs/limits.json")).unwrap();
        let owned: std::collections::BTreeMap<&str, (u64, &str)> = manifest["limits"]
            .as_array()
            .unwrap()
            .iter()
            .filter(|row| {
                row["checks"].as_array().unwrap().iter().any(|check| {
                    check["path"] == "controller/src/request_patch.rs" && check["kind"] == "value"
                })
            })
            .map(|row| {
                (
                    row["id"].as_str().unwrap(),
                    (
                        row["value"].as_u64().unwrap(),
                        row["unit"].as_str().unwrap(),
                    ),
                )
            })
            .collect();
        assert_eq!(
            owned,
            std::collections::BTreeMap::from([
                ("request_failure_path_components", (depth as u64, "items")),
                (
                    "request_failure_path_component",
                    (component_bytes as u64, "UTF-8 bytes")
                ),
            ])
        );
    }

    #[test]
    fn request_failure_path_depth_retains_eight_and_withholds_nine() {
        let path = [
            "actors", "0", "phases", "1", "steps", "2", "attempt", "target",
        ];
        let retained = RequestError::new("type_mismatch", &path, "invalid value");
        assert_eq!(retained.failure.path, Some(path.map(String::from).to_vec()));
        assert_eq!(
            serde_json::to_value(&retained.failure).unwrap(),
            json!({"code": "type_mismatch", "path": path})
        );
        let mut too_deep = path.to_vec();
        too_deep.push("leaf");
        let withheld = RequestError::new("type_mismatch", &too_deep, "invalid value");
        assert_eq!(withheld.failure.path, None);
        assert_eq!(
            serde_json::to_value(&withheld.failure).unwrap(),
            json!({"code": "type_mismatch", "path": null})
        );
        assert_eq!(withheld.message, "invalid value");
    }

    #[test]
    fn request_failure_path_components_use_utf8_bytes_and_withhold_the_whole_path() {
        for component in ["a".repeat(63), format!("{}a", "é".repeat(31))] {
            assert_eq!(component.len(), 63);
            let path = [
                "actors",
                "0",
                "policy",
                "params",
                component.as_str(),
                "value",
            ];
            let retained = RequestError::new("type_mismatch", &path, "invalid value");
            assert_eq!(retained.failure.path, Some(path.map(String::from).to_vec()));
            assert_eq!(
                serde_json::to_value(&retained.failure).unwrap(),
                json!({"code": "type_mismatch", "path": path})
            );
        }
        // The oversized component is in the middle: neither a prefix nor a
        // subset of otherwise valid components may stand in for the location.
        for component in ["a".repeat(64), "é".repeat(32)] {
            assert_eq!(component.len(), 64);
            let path = [
                "actors",
                "0",
                "policy",
                "params",
                component.as_str(),
                "value",
            ];
            let withheld = RequestError::new("type_mismatch", &path, "invalid value");
            assert_eq!(withheld.failure.path, None);
            assert_eq!(
                serde_json::to_value(&withheld.failure).unwrap(),
                json!({"code": "type_mismatch", "path": null})
            );
            assert_eq!(withheld.message, "invalid value");
        }
    }

    #[test]
    fn request_contract_is_exact_and_required() {
        let current = "test:current";
        assert!(validate_contract(&json!({"contract":current}), current).is_ok());
        for (value, code) in [
            (json!({}), "missing_field"),
            (json!({"schema_version":6}), "missing_field"),
            (json!({"contract":null}), "missing_value"),
            (json!({"contract":6}), "type_mismatch"),
            (json!({"contract":"test:foreign"}), "unsupported_contract"),
        ] {
            let error = validate_contract(&value, current).unwrap_err();
            assert_eq!(error.failure.code, code);
            assert_eq!(error.failure.expected_contract.as_deref(), Some(current));
        }
        assert!(validate_contract(&json!({"contract":"unbound"}), "unbound").is_err());
    }
}
