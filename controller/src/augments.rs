//! Resolves `policy.augments` by splicing named SBPL fragments into the
//! caller's `sbpl_source` before the request reaches the runner.
//!
//! Augments live under `Contents/Resources/Augments/<name>.sb` inside the
//! signed app bundle. The controller appends each named augment's contents
//! to the caller's source and forwards the spliced policy to the runner (and
//! to `sbpl-check`, if the xpc_error path runs it) so both see the same bytes.
//!
//! The `augments` field is stripped from the forwarded request — the
//! runner is augment-agnostic by design.

use serde::Serialize;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::path::Path;

/// Reported in the envelope under `data.policy_augmentation` when one or
/// more augments were applied. Absent when no augments were resolved so
/// consumers can branch on `policy_augmentation != null` rather than
/// comparing arrays.
#[derive(Serialize, Clone)]
pub struct PolicyAugmentation {
    pub applied: Vec<String>,
    pub original_sha256: String,
    pub applied_sha256: String,
}

/// Outcome of attempting to resolve `policy.augments` for a request.
pub enum AugmentResolution {
    /// No `augments` field was present on the request. `request_value`
    /// was not touched.
    NotPresent,
    /// The `augments` field was present but resolved to no-op (null or
    /// empty array). `request_value` was mutated to remove the field
    /// so the runner sees the documented "no augment-aware shape"
    /// contract; the caller must persist this mutation to the temp
    /// request file even though no `policy_augmentation` block will
    /// be emitted.
    StrippedNoOp,
    /// Augments resolved and spliced into the request. `request_value`
    /// has been mutated: `policy.sbpl_source` carries the spliced text
    /// and `policy.augments` has been removed.
    Applied(PolicyAugmentation),
    /// Resolution failed. The caller should emit a `bad_request` envelope
    /// with this error string and not invoke the runner.
    BadRequest(String),
}

impl AugmentResolution {
    /// True when `resolve_augments` mutated the request and the caller
    /// must persist the result to a temp file before forwarding to
    /// the runner. False only when the request was left
    /// untouched (`NotPresent`) or when resolution failed (`BadRequest`,
    /// in which case the caller short-circuits and doesn't forward
    /// anything).
    pub fn request_was_mutated(&self) -> bool {
        matches!(self, AugmentResolution::StrippedNoOp | AugmentResolution::Applied(_))
    }
}

fn is_valid_augment_name(name: &str) -> bool {
    // Restricted to ASCII alphanumeric + underscore so the name maps
    // unambiguously to a filename component and resists traversal via
    // `..`, `/`, or shell metacharacters.
    !name.is_empty()
        && name
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || c == '_')
}

fn sha256_hex_of(s: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(s.as_bytes());
    format!("{:x}", hasher.finalize())
}

/// Resolve `request.policy.augments` against `<app_root>/Contents/Resources/Augments/`.
///
/// On `Applied`, the request value is mutated in place: `policy.sbpl_source`
/// becomes the spliced source and `policy.augments` is removed. The caller
/// must persist this mutation (typically by writing a temp request) so
/// the runner (and `sbpl-check`, on the xpc_error path) see the spliced policy.
pub fn resolve_augments(request_value: &mut Value, app_root: &Path) -> AugmentResolution {
    let policy = match request_value
        .get_mut("policy")
        .and_then(|v| v.as_object_mut())
    {
        Some(p) => p,
        None => return AugmentResolution::NotPresent,
    };

    let augments_field = match policy.remove("augments") {
        Some(v) => v,
        None => return AugmentResolution::NotPresent,
    };
    // From here on we have mutated `request_value` (the augments key is
    // stripped). Any non-error return must be a variant whose
    // `request_was_mutated()` is true so the caller persists the
    // mutated request to a temp file and the runner sees the
    // augment-free shape.

    let names: Vec<String> = match augments_field {
        Value::Null => return AugmentResolution::StrippedNoOp,
        Value::Array(items) => {
            let mut collected = Vec::with_capacity(items.len());
            for (idx, item) in items.iter().enumerate() {
                match item.as_str() {
                    Some(s) => collected.push(s.to_string()),
                    None => {
                        return AugmentResolution::BadRequest(format!(
                            "policy.augments[{idx}] must be a string"
                        ));
                    }
                }
            }
            collected
        }
        _ => {
            return AugmentResolution::BadRequest(
                "policy.augments must be an array of strings".to_string(),
            );
        }
    };

    if names.is_empty() {
        return AugmentResolution::StrippedNoOp;
    }

    // Validate every name BEFORE touching the filesystem so a typo in
    // the last entry can't leak partial-resolution state.
    for name in &names {
        if !is_valid_augment_name(name) {
            return AugmentResolution::BadRequest(format!(
                "invalid augment name {name:?} (must be ASCII alphanumeric or underscore)"
            ));
        }
    }

    let augments_dir = app_root
        .join("Contents")
        .join("Resources")
        .join("Augments");

    let mut appended = String::new();
    for name in &names {
        let path = augments_dir.join(format!("{name}.sb"));
        let contents = match std::fs::read_to_string(&path) {
            Ok(s) => s,
            Err(_) => {
                return AugmentResolution::BadRequest(format!("unknown augment {name:?}"));
            }
        };
        // Always splice with a leading newline so we never accidentally
        // concatenate the last token of the caller's source with the
        // first token of the augment (e.g. `(allow default)` followed
        // by `(allow process-exec*)` must remain two top-level forms).
        appended.push('\n');
        appended.push_str(&contents);
    }

    let original_source = policy
        .get("sbpl_source")
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .to_string();
    let original_sha256 = sha256_hex_of(&original_source);

    let mut applied_source = original_source.clone();
    applied_source.push_str(&appended);
    let applied_sha256 = sha256_hex_of(&applied_source);

    policy.insert(
        "sbpl_source".to_string(),
        Value::String(applied_source),
    );

    AugmentResolution::Applied(PolicyAugmentation {
        applied: names,
        original_sha256,
        applied_sha256,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    use std::fs;

    fn tempdir(label: &str) -> std::path::PathBuf {
        let dir = std::env::temp_dir().join(format!(
            "pw-augments-test-{}-{}-{}",
            label,
            std::process::id(),
            crate::utils::now_unix_ms()
        ));
        fs::create_dir_all(dir.join("Contents/Resources/Augments")).expect("mkdir augments");
        dir
    }

    fn write_augment(app_root: &Path, name: &str, body: &str) {
        let path = app_root
            .join("Contents/Resources/Augments")
            .join(format!("{name}.sb"));
        fs::write(&path, body).expect("write augment");
    }

    #[test]
    fn not_present_when_field_absent() {
        let app = tempdir("absent");
        let mut req = json!({
            "policy": { "format": "sbpl", "sbpl_source": "(version 1)\n" }
        });
        let resolution = resolve_augments(&mut req, &app);
        assert!(matches!(resolution, AugmentResolution::NotPresent));
        assert!(!resolution.request_was_mutated());
        // Request must remain untouched.
        assert_eq!(
            req["policy"]["sbpl_source"].as_str(),
            Some("(version 1)\n")
        );
    }

    #[test]
    fn stripped_noop_when_empty_array() {
        let app = tempdir("empty");
        let mut req = json!({
            "policy": { "format": "sbpl", "sbpl_source": "(version 1)\n", "augments": [] }
        });
        let resolution = resolve_augments(&mut req, &app);
        assert!(matches!(resolution, AugmentResolution::StrippedNoOp));
        // The mutation marker MUST be set so the caller persists the
        // stripped request to a temp file. Without this the runner
        // would read the original on-disk file with the augments key
        // still present.
        assert!(resolution.request_was_mutated());
        assert!(req["policy"].as_object().unwrap().get("augments").is_none());
    }

    #[test]
    fn stripped_noop_when_null_field() {
        let app = tempdir("null");
        let mut req = json!({
            "policy": {
                "format": "sbpl",
                "sbpl_source": "(version 1)\n",
                "augments": serde_json::Value::Null
            }
        });
        let resolution = resolve_augments(&mut req, &app);
        assert!(matches!(resolution, AugmentResolution::StrippedNoOp));
        assert!(resolution.request_was_mutated());
        assert!(req["policy"].as_object().unwrap().get("augments").is_none());
    }

    #[test]
    fn applies_and_strips_field() {
        let app = tempdir("apply");
        write_augment(&app, "exec_baseline", "; comment-only\n");
        let original = "(version 1)\n(allow default)\n";
        let mut req = json!({
            "policy": { "format": "sbpl", "sbpl_source": original, "augments": ["exec_baseline"] }
        });
        let resolution = resolve_augments(&mut req, &app);
        assert!(resolution.request_was_mutated());
        match &resolution {
            AugmentResolution::Applied(aug) => {
                assert_eq!(aug.applied, vec!["exec_baseline".to_string()]);
                assert_ne!(aug.original_sha256, aug.applied_sha256);
                assert_eq!(aug.original_sha256, sha256_hex_of(original));
                let expected_applied = format!("{original}\n; comment-only\n");
                assert_eq!(aug.applied_sha256, sha256_hex_of(&expected_applied));
            }
            other => panic!("expected Applied, got {:?}", outcome_name(other)),
        }
        assert!(req["policy"].as_object().unwrap().get("augments").is_none());
        assert_eq!(
            req["policy"]["sbpl_source"].as_str(),
            Some(format!("{original}\n; comment-only\n").as_str())
        );
    }

    #[test]
    fn unknown_name_is_bad_request_without_partial_apply() {
        let app = tempdir("unknown");
        write_augment(&app, "exec_baseline", "; ok\n");
        let original = "(version 1)\n";
        let mut req = json!({
            "policy": {
                "format": "sbpl",
                "sbpl_source": original,
                "augments": ["exec_baseline", "does_not_exist"]
            }
        });
        let resolution = resolve_augments(&mut req, &app);
        match &resolution {
            AugmentResolution::BadRequest(msg) => {
                assert!(msg.contains("does_not_exist"), "msg={msg}");
            }
            other => panic!("expected BadRequest, got {:?}", outcome_name(other)),
        }
        // No partial-apply: the original source must be intact even
        // though the first augment in the list existed.
        assert_eq!(req["policy"]["sbpl_source"].as_str(), Some(original));
    }

    #[test]
    fn invalid_name_rejected() {
        let app = tempdir("invalid");
        for bad in ["", "../etc/passwd", "has space", "with/slash", "dotted.name"] {
            let mut req = json!({
                "policy": {
                    "format": "sbpl",
                    "sbpl_source": "(version 1)\n",
                    "augments": [bad]
                }
            });
            let resolution = resolve_augments(&mut req, &app);
            assert!(
                matches!(resolution, AugmentResolution::BadRequest(_)),
                "name {bad:?} should be rejected"
            );
        }
    }

    #[test]
    fn non_array_augments_is_bad_request() {
        let app = tempdir("nonarray");
        let mut req = json!({
            "policy": {
                "format": "sbpl",
                "sbpl_source": "(version 1)\n",
                "augments": "exec_baseline"
            }
        });
        let resolution = resolve_augments(&mut req, &app);
        assert!(matches!(resolution, AugmentResolution::BadRequest(_)));
    }

    fn outcome_name(r: &AugmentResolution) -> &'static str {
        match r {
            AugmentResolution::NotPresent => "NotPresent",
            AugmentResolution::StrippedNoOp => "StrippedNoOp",
            AugmentResolution::Applied(_) => "Applied",
            AugmentResolution::BadRequest(_) => "BadRequest",
        }
    }
}
