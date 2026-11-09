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

use crate::request_patch::RequestError;
use serde::Serialize;
use serde_json::Value;
use std::path::Path;

/// Successful augment resolution, used to construct the always-present
/// `data.specimen.policy.augmentation` record in the controller envelope.
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
    /// contract; the caller serializes this mutation into the held request
    /// delivered on stdin and reports augmentation as `not_requested`.
    StrippedNoOp,
    /// Augments resolved and spliced into the request. `request_value`
    /// has been mutated: `policy.sbpl_source` carries the spliced text
    /// and `policy.augments` has been removed.
    Applied(PolicyAugmentation),
    /// Resolution failed. The caller should emit a `bad_request` envelope
    /// with this error string and not invoke the runner.
    BadRequest(RequestError),
}

/// Augment names are the one request string the controller itself echoes into
/// an envelope diagnostic. Bound the echo like the runner's labels (127 bytes)
/// so a refusal never repeats an unbounded value; the length still identifies it.
const MAX_REPORTED_AUGMENT_NAME_BYTES: usize = 127;

fn reportable_name(name: &str) -> String {
    if name.len() <= MAX_REPORTED_AUGMENT_NAME_BYTES {
        format!("{name:?}")
    } else {
        format!("<unreported: {} bytes>", name.len())
    }
}

fn is_valid_augment_name(name: &str) -> bool {
    // Restricted to ASCII alphanumeric + underscore so the name maps
    // unambiguously to a filename component and resists traversal via
    // `..`, `/`, or shell metacharacters.
    !name.is_empty() && name.chars().all(|c| c.is_ascii_alphanumeric() || c == '_')
}

/// Resolve `request.policy.augments` against `<app_root>/Contents/Resources/Augments/`.
///
/// On `Applied`, the request value is mutated in place: `policy.sbpl_source`
/// becomes the spliced source and `policy.augments` is removed. The caller
/// must serialize this mutation into the held request delivered on stdin so
/// the runner (and `sbpl-check`, on the xpc_error path) see the spliced policy.
pub fn resolve_augments(request_value: &mut Value, app_root: &Path) -> AugmentResolution {
    let policy = match request_value
        .get_mut("policy")
        .and_then(|v| v.as_object_mut())
    {
        Some(p) => p,
        None => return AugmentResolution::NotPresent,
    };
    resolve_policy_augments(policy, &["policy"], app_root)
}

/// One apply actor's resolution in the actor form. `original_source` and
/// `selected_source` are the string sources before and after resolution, when
/// they existed; the actor's id and mode are copied for the dossier.
pub struct ActorAugmentResolution {
    pub index: usize,
    pub actor_id: Option<String>,
    pub mode: Option<String>,
    pub original_source: Option<String>,
    pub selected_source: Option<String>,
    pub resolution: AugmentResolution,
}

/// Resolve every `actors[i].sandbox.policy.augments` in place, in actor order,
/// stopping at the first refusal so no later actor is partially resolved.
/// Actors without a policy object produce a `NotPresent` entry. Only the
/// runner judges whether an actor's mode permits a policy.
pub fn resolve_actor_augments(
    request_value: &mut Value,
    app_root: &Path,
) -> Vec<ActorAugmentResolution> {
    let mut out = Vec::new();
    let Some(actors) = request_value
        .get_mut("actors")
        .and_then(Value::as_array_mut)
    else {
        return out;
    };
    for (index, actor) in actors.iter_mut().enumerate() {
        let actor_id = actor
            .get("actor_id")
            .and_then(Value::as_str)
            .map(str::to_string);
        let mode = actor
            .get("sandbox")
            .and_then(|s| s.get("mode"))
            .and_then(Value::as_str)
            .map(str::to_string);
        let index_text = index.to_string();
        let path = ["actors", index_text.as_str(), "sandbox", "policy"];
        let policy = actor
            .get_mut("sandbox")
            .and_then(|s| s.get_mut("policy"))
            .and_then(Value::as_object_mut);
        let Some(policy) = policy else {
            out.push(ActorAugmentResolution {
                index,
                actor_id,
                mode,
                original_source: None,
                selected_source: None,
                resolution: AugmentResolution::NotPresent,
            });
            continue;
        };
        let original_source = policy
            .get("sbpl_source")
            .and_then(Value::as_str)
            .map(str::to_string);
        let resolution = resolve_policy_augments(policy, &path, app_root);
        let selected_source = policy
            .get("sbpl_source")
            .and_then(Value::as_str)
            .map(str::to_string);
        let refused = matches!(resolution, AugmentResolution::BadRequest(_));
        out.push(ActorAugmentResolution {
            index,
            actor_id,
            mode,
            original_source,
            selected_source,
            resolution,
        });
        if refused {
            break;
        }
    }
    out
}

/// Resolve one policy object's `augments`; `path` locates that object in the
/// request for refusal diagnostics.
pub fn resolve_policy_augments(
    policy: &mut serde_json::Map<String, Value>,
    path: &[&str],
    app_root: &Path,
) -> AugmentResolution {
    let at = |suffix: &[&str]| -> Vec<String> {
        path.iter()
            .map(|s| (*s).to_string())
            .chain(suffix.iter().map(|s| (*s).to_string()))
            .collect()
    };
    let refuse = |code: &str, suffix: &[&str], message: String| -> AugmentResolution {
        let owned = at(suffix);
        let parts: Vec<&str> = owned.iter().map(String::as_str).collect();
        AugmentResolution::BadRequest(RequestError::new(code, &parts, message))
    };
    let location = path.join(".");

    let augments_field = match policy.remove("augments") {
        Some(v) => v,
        None => return AugmentResolution::NotPresent,
    };
    // From here on the request is mutated (the augments key is stripped).
    // The caller serializes the resolved value once and delivers that string
    // to every reader, so the runner sees the augment-free shape.

    let names: Vec<String> = match augments_field {
        Value::Null => return AugmentResolution::StrippedNoOp,
        Value::Array(items) => {
            let mut collected = Vec::with_capacity(items.len());
            for (idx, item) in items.iter().enumerate() {
                match item.as_str() {
                    Some(s) => collected.push(s.to_string()),
                    None => {
                        return refuse(
                            "type_mismatch",
                            &["augments", &idx.to_string()],
                            format!("{location}.augments[{idx}] must be a string"),
                        );
                    }
                }
            }
            collected
        }
        _ => {
            return refuse(
                "type_mismatch",
                &["augments"],
                format!("{location}.augments must be an array of strings"),
            );
        }
    };

    if names.is_empty() {
        return AugmentResolution::StrippedNoOp;
    }

    // Never replace a missing or mistyped source with just the augment text.
    let Some(original_source) = policy.get("sbpl_source").and_then(Value::as_str) else {
        let code = if policy.get("sbpl_source").is_none_or(Value::is_null) {
            "missing_policy_source"
        } else {
            "type_mismatch"
        };
        return refuse(
            code,
            &["sbpl_source"],
            format!("{location}.sbpl_source must be a string when {location}.augments is nonempty"),
        );
    };
    let original_source = original_source.to_owned();

    // Validate every name BEFORE touching the filesystem so a typo in
    // the last entry can't leak partial-resolution state.
    for (index, name) in names.iter().enumerate() {
        if !is_valid_augment_name(name) {
            return refuse(
                "invalid_value",
                &["augments", &index.to_string()],
                format!(
                    "invalid augment name {} (must be ASCII alphanumeric or underscore)",
                    reportable_name(name)
                ),
            );
        }
    }

    let augments_dir = app_root.join("Contents").join("Resources").join("Augments");

    let mut appended = String::new();
    for (index, name) in names.iter().enumerate() {
        let path = augments_dir.join(format!("{name}.sb"));
        let contents = match std::fs::read_to_string(&path) {
            Ok(s) => s,
            Err(_) => {
                return refuse(
                    "augment_unavailable",
                    &["augments", &index.to_string()],
                    format!("unknown augment {}", reportable_name(name)),
                );
            }
        };
        // Always splice with a leading newline so we never accidentally
        // concatenate the last token of the caller's source with the
        // first token of the augment (e.g. `(allow default)` followed
        // by `(allow process-exec*)` must remain two top-level forms).
        appended.push('\n');
        appended.push_str(&contents);
    }

    let original_sha256 = crate::digest::sha256_hex(&original_source);

    let mut applied_source = original_source.clone();
    applied_source.push_str(&appended);
    let applied_sha256 = crate::digest::sha256_hex(&applied_source);

    policy.insert("sbpl_source".to_string(), Value::String(applied_source));

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
        // Request must remain untouched.
        assert_eq!(req["policy"]["sbpl_source"].as_str(), Some("(version 1)\n"));
    }

    #[test]
    fn stripped_noop_when_empty_array() {
        let app = tempdir("empty");
        let mut req = json!({
            "policy": { "format": "sbpl", "sbpl_source": "(version 1)\n", "augments": [] }
        });
        let resolution = resolve_augments(&mut req, &app);
        assert!(matches!(resolution, AugmentResolution::StrippedNoOp));
        // The stripped value is what the caller serializes for the runner.
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
        match &resolution {
            AugmentResolution::Applied(aug) => {
                assert_eq!(aug.applied, vec!["exec_baseline".to_string()]);
                assert_ne!(aug.original_sha256, aug.applied_sha256);
                assert_eq!(aug.original_sha256, crate::digest::sha256_hex(original));
                let expected_applied = format!("{original}\n; comment-only\n");
                assert_eq!(
                    aug.applied_sha256,
                    crate::digest::sha256_hex(&expected_applied)
                );
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
                assert!(msg.message.contains("does_not_exist"), "msg={msg}");
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
        for bad in [
            "",
            "../etc/passwd",
            "has space",
            "with/slash",
            "dotted.name",
        ] {
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

    #[test]
    fn augments_cannot_replace_missing_or_malformed_policy_source() {
        let app = tempdir("malformed-source");
        write_augment(&app, "exec_baseline", "(allow default)");
        for source in [
            None,
            Some(serde_json::json!(null)),
            Some(serde_json::json!(42)),
        ] {
            let mut req = json!({"policy": {"format": "sbpl", "augments": ["exec_baseline"]}});
            if let Some(value) = source {
                req["policy"]["sbpl_source"] = value;
            }
            let before = req["policy"].get("sbpl_source").cloned();
            match resolve_augments(&mut req, &app) {
                AugmentResolution::BadRequest(error) => {
                    assert!(error.message.contains("policy.sbpl_source"))
                }
                _ => panic!("malformed source was replaced by augment text"),
            }
            assert_eq!(req["policy"].get("sbpl_source").cloned(), before);
        }
        fs::remove_dir_all(app).unwrap();
    }

    fn outcome_name(r: &AugmentResolution) -> &'static str {
        match r {
            AugmentResolution::NotPresent => "NotPresent",
            AugmentResolution::StrippedNoOp => "StrippedNoOp",
            AugmentResolution::Applied(_) => "Applied",
            AugmentResolution::BadRequest(_) => "BadRequest",
        }
    }

    #[test]
    fn actor_policies_resolve_at_their_own_paths_and_stop_at_the_first_refusal() {
        let app = tempdir("actors");
        write_augment(&app, "exec_baseline", "; fragment\n");
        let mut req = json!({
            "specimen_id": "a",
            "actors": [
                {"actor_id": "A", "sandbox": {"mode": "unapplied"}},
                {"actor_id": "B", "sandbox": {"mode": "apply", "policy": {"format": "sbpl", "sbpl_source": "(version 1)", "augments": ["exec_baseline"]}}},
                {"actor_id": "C", "sandbox": {"mode": "apply", "policy": {"format": "sbpl", "sbpl_source": "(version 1)", "augments": ["nope"]}}},
                {"actor_id": "D", "sandbox": {"mode": "apply", "policy": {"format": "sbpl", "sbpl_source": "(version 1)", "augments": ["exec_baseline"]}}}
            ],
            "phases": []
        });
        let resolved = resolve_actor_augments(&mut req, &app);
        assert_eq!(
            resolved.len(),
            3,
            "resolution stops after the refused actor"
        );
        assert!(matches!(
            resolved[0].resolution,
            AugmentResolution::NotPresent
        ));
        assert_eq!(resolved[0].actor_id.as_deref(), Some("A"));
        assert_eq!(resolved[0].mode.as_deref(), Some("unapplied"));
        assert!(resolved[0].original_source.is_none() && resolved[0].selected_source.is_none());
        match &resolved[1].resolution {
            AugmentResolution::Applied(record) => {
                assert_eq!(record.applied, vec!["exec_baseline".to_string()])
            }
            _ => panic!("B not applied"),
        }
        assert_eq!(resolved[1].original_source.as_deref(), Some("(version 1)"));
        assert_eq!(
            resolved[1].selected_source.as_deref(),
            Some("(version 1)\n; fragment\n")
        );
        assert_eq!(
            req["actors"][1]["sandbox"]["policy"]["sbpl_source"],
            "(version 1)\n; fragment\n"
        );
        assert!(
            req["actors"][1]["sandbox"]["policy"]
                .get("augments")
                .is_none()
        );
        match &resolved[2].resolution {
            AugmentResolution::BadRequest(error) => {
                assert_eq!(error.failure.code, "augment_unavailable");
                assert_eq!(
                    error.failure.path.as_deref(),
                    Some(
                        &[
                            "actors".to_string(),
                            "2".to_string(),
                            "sandbox".to_string(),
                            "policy".to_string(),
                            "augments".to_string(),
                            "0".to_string()
                        ][..]
                    )
                );
            }
            _ => panic!("C not refused"),
        }
        // D was never touched: its augments remain in the request.
        assert_eq!(
            req["actors"][3]["sandbox"]["policy"]["augments"],
            json!(["exec_baseline"])
        );
        assert_eq!(
            req["actors"][3]["sandbox"]["policy"]["sbpl_source"],
            "(version 1)"
        );
    }

    #[test]
    fn legacy_refusal_paths_are_unchanged_by_the_shared_resolver() {
        let app = tempdir("legacy-paths");
        let mut req =
            json!({"policy": {"format": "sbpl", "sbpl_source": "(version 1)", "augments": [7]}});
        match resolve_augments(&mut req, &app) {
            AugmentResolution::BadRequest(error) => {
                assert_eq!(
                    error.failure.path.as_deref(),
                    Some(
                        &[
                            "policy".to_string(),
                            "augments".to_string(),
                            "0".to_string()
                        ][..]
                    )
                );
                assert!(
                    error
                        .message
                        .contains("policy.augments[0] must be a string")
                );
            }
            _ => panic!("expected refusal"),
        }
        let mut req = json!({"actors": [{"actor_id": "B", "sandbox": {"mode": "apply", "policy": {"format": "sbpl", "augments": ["exec_baseline"]}}}]});
        let resolved = resolve_actor_augments(&mut req, &app);
        match &resolved[0].resolution {
            AugmentResolution::BadRequest(error) => {
                assert_eq!(error.failure.code, "missing_policy_source");
                assert!(
                    error
                        .message
                        .contains("actors.0.sandbox.policy.sbpl_source")
                );
            }
            _ => panic!("expected refusal"),
        }
    }
}
