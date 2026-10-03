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
    pub expected_schema: Option<u32>,
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
                expected_schema: (path == ["schema_version"])
                    .then_some(crate::json_contract::REQUEST_SCHEMA_VERSION),
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

/// The marker identifies the accepted input language, not a build revision.
/// Check it before interpreting controller-owned options or named augments.
pub fn validate_request_version(value: &Value) -> Result<(), RequestError> {
    let expected = crate::json_contract::REQUEST_SCHEMA_VERSION;
    match value.get("schema_version") {
        Some(Value::Number(version)) if version.as_f64().is_some_and(|v| v.fract() == 0.0) => {
            if version.as_f64() == Some(f64::from(expected)) {
                Ok(())
            } else {
                Err(RequestError::new(
                    "unsupported_schema",
                    &["schema_version"],
                    format!("unsupported request schema {version} (expected {expected})"),
                ))
            }
        }
        other => Err(RequestError::new(
            match other {
                None => "missing_field",
                Some(Value::Null) => "missing_value",
                _ => "type_mismatch",
            },
            &["schema_version"],
            format!("schema_version must be an integer (expected {expected})"),
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
            assert!(error.message.contains("unsupported request schema"));
            assert!(error.message.contains(&format!("expected {current}")));
        }
        for version in [json!(null), json!(true), json!("3"), json!(3.5), json!([])] {
            assert!(validate_request_version(&json!({"schema_version": version})).is_err());
        }
        assert!(validate_request_version(&json!({})).is_err());
    }
}
