//! Runner selection and provenance logic.
//!
//! The controller can target the embedded standard runner or an
//! external runner registered in the local registry. This module resolves the
//! request selector into a concrete service connection and auditable metadata.

use serde::Serialize;
use serde_json::Value;
use std::path::{Path, PathBuf};

use crate::app_layout::SHIPPED_SERVICE;
use crate::evidence::{self, EvidenceManifest};
use crate::request_patch::RequestError;
use crate::runner_manager::{
    self, RunnerEntitlements, RunnerKind, RunnerRecord, RunnerRegistry, RunnerScope,
    RunnerSignature,
};

#[derive(Default)]
pub struct RunnerSelector {
    runner_id: Option<String>,
    runner_service: Option<String>,
    required_entitlements: Vec<String>,
    mode: Option<RunnerKind>,
}

#[derive(Clone, Copy, Debug)]
pub enum RunnerConnectionKind {
    XpcService,
    MachService { privileged: bool },
}

pub struct RunnerTarget {
    pub kind: RunnerKind,
    pub connection: RunnerConnectionKind,
    pub service_name: String,
    pub bundle_id: Option<String>,
    pub bundle_path: Option<PathBuf>,
    pub executable_path: Option<PathBuf>,
    pub registry_id: Option<String>,
    pub signature: Option<RunnerSignature>,
    pub entitlements: Option<RunnerEntitlements>,
}

#[derive(Serialize, Clone)]
pub struct RunnerProvenance {
    runner_kind: String,
    runner_registry_id: Option<String>,
    runner_service_name: String,
    runner_bundle_id: Option<String>,
    runner_bundle_path: Option<String>,
    runner_executable_path: Option<String>,
    runner_signature: Option<RunnerSignature>,
    runner_entitlements: Option<RunnerEntitlements>,
}

/// Controller-owned keys are consumed before the worker request is delivered.
pub const SELECTOR_FIELDS: &[&str] = &[
    "runner",
    "runner_id",
    "runner_service",
    "required_entitlements",
    "runner_mode",
];

fn selector_string<'a>(
    object: &'a serde_json::Map<String, Value>,
    key: &str,
    path: &str,
) -> Result<Option<&'a str>, RequestError> {
    match object.get(key) {
        None | Some(Value::Null) => Ok(None),
        Some(Value::String(value)) => Ok(Some(value)),
        Some(_) => Err(selector_error(
            "type_mismatch",
            path,
            &[key],
            format!("{path}{key} must be a string or null"),
        )),
    }
}

fn selector_entitlements(
    object: &serde_json::Map<String, Value>,
    path: &str,
) -> Result<Option<Vec<String>>, RequestError> {
    match object.get("required_entitlements") {
        None | Some(Value::Null) => Ok(None),
        Some(Value::Array(items)) => items
            .iter()
            .enumerate()
            .map(|(i, item)| {
                item.as_str().map(str::to_owned).ok_or_else(|| {
                    selector_error(
                        "type_mismatch",
                        path,
                        &["required_entitlements", &i.to_string()],
                        format!("{path}required_entitlements[{i}] must be a string"),
                    )
                })
            })
            .collect::<Result<Vec<_>, _>>()
            .map(Some),
        Some(_) => Err(selector_error(
            "type_mismatch",
            path,
            &["required_entitlements"],
            format!("{path}required_entitlements must be an array of strings or null"),
        )),
    }
}

fn selector_error(code: &str, prefix: &str, suffix: &[&str], message: String) -> RequestError {
    let mut path = if prefix.is_empty() {
        vec![]
    } else {
        vec!["runner"]
    };
    path.extend_from_slice(suffix);
    RequestError::new(code, &path, message)
}

pub fn parse_runner_selector_value(value: &Value) -> Result<RunnerSelector, RequestError> {
    let root = value.as_object().ok_or_else(|| {
        RequestError::new("type_mismatch", &[], "request.json must be a JSON object")
    })?;
    // Validate every supplied spelling, including a shadowed alias. A bad
    // entitlement entry must never disappear through filter_map.
    let id = selector_string(root, "runner_id", "")?;
    let service = selector_string(root, "runner_service", "")?;
    let entitlements = selector_entitlements(root, "")?;
    let mode = selector_string(root, "runner_mode", "")?
        .map(|v| {
            parse_runner_mode(v, "runner_mode")
                .map_err(|e| RequestError::new("invalid_value", &["runner_mode"], e))
        })
        .transpose()?;
    let mut selector = RunnerSelector {
        runner_id: id.map(str::to_owned),
        runner_service: service.map(str::to_owned),
        required_entitlements: entitlements.unwrap_or_default(),
        mode,
    };
    let runner = match root.get("runner") {
        None | Some(Value::Null) => return checked_selector(selector),
        Some(Value::Object(object)) => object,
        Some(_) => {
            return Err(RequestError::new(
                "type_mismatch",
                &["runner"],
                "runner must be a JSON object or null",
            ));
        }
    };
    for key in runner.keys() {
        if !["id", "service", "required_entitlements", "mode"].contains(&key.as_str()) {
            let name = if key.len() <= 63 {
                format!("{key:?}")
            } else {
                "<unreported_key>".into()
            };
            return Err(RequestError::new(
                "unknown_field",
                &["runner", key],
                format!("unknown field in runner: {name}"),
            ));
        }
    }
    if let Some(id) = selector_string(runner, "id", "runner.")? {
        selector.runner_id = Some(id.to_owned());
    }
    if let Some(service) = selector_string(runner, "service", "runner.")? {
        selector.runner_service = Some(service.to_owned());
    }
    if let Some(entitlements) = selector_entitlements(runner, "runner.")? {
        selector.required_entitlements = entitlements;
    }
    if let Some(mode) = selector_string(runner, "mode", "runner.")? {
        selector.mode = Some(
            parse_runner_mode(mode, "runner.mode")
                .map_err(|e| RequestError::new("invalid_value", &["runner", "mode"], e))?,
        );
    }
    checked_selector(selector)
}

fn selector_problem(selector: &RunnerSelector) -> Option<&'static str> {
    let external = selector.runner_id.is_some() || selector.runner_service.is_some();
    if matches!(selector.mode, Some(RunnerKind::Standard)) && external {
        Some("runner.mode=standard cannot be combined with an external runner selection")
    } else if matches!(selector.mode, Some(RunnerKind::Byoxpc)) && !external {
        Some("runner.mode requires runner.id or runner.service for external runners")
    } else {
        None
    }
}

fn checked_selector(selector: RunnerSelector) -> Result<RunnerSelector, RequestError> {
    if let Some(problem) = selector_problem(&selector) {
        // A relationship between selector fields; the root is its location.
        return Err(RequestError::new("conflicting_selector", &[], problem));
    }
    Ok(selector)
}

pub fn strip_runner_selector(value: &mut Value) {
    if let Some(object) = value.as_object_mut() {
        for key in SELECTOR_FIELDS {
            object.remove(*key);
        }
    }
}

fn parse_runner_mode(value: &str, field: &str) -> Result<RunnerKind, String> {
    if value == "machme" {
        return Err(format!(
            "{field}=\"machme\" is not supported; use \"byoxpc\""
        ));
    }
    RunnerKind::parse(value).ok_or_else(|| {
        let shown = if value.len() <= 63 {
            format!("{value:?}")
        } else {
            "<unreported_value>".into()
        };
        format!("invalid {field} value: {shown}")
    })
}

fn entitlements_from_manifest_value(
    value: Option<&Value>,
    error: Option<&String>,
) -> RunnerEntitlements {
    let mut entitlements =
        value
            .map(runner_manager::entitlements_from_json)
            .unwrap_or(RunnerEntitlements {
                raw_plist: None,
                keys: Vec::new(),
                error: None,
            });
    if entitlements.raw_plist.is_none() {
        entitlements.raw_plist = value.and_then(|v| serde_json::to_string_pretty(v).ok());
    }
    if let Some(err) = error {
        entitlements.error = Some(err.to_string());
    }
    entitlements
}

/// The built-in runner, selected from the app evidence manifest: the one
/// `xpc-service` entry at the fixed shipped path, whose `bundle_id` names the
/// XPC connection. No Info.plist is read; no `id`, `bundle_id` or service-name
/// lookup substitutes for the path.
fn builtin_runner_target(
    app_root: &Path,
    manifest: Result<&EvidenceManifest, &String>,
    kind: RunnerKind,
) -> Result<RunnerTarget, String> {
    if matches!(kind, RunnerKind::Byoxpc) {
        return Err("builtin runner target requires a built-in kind".to_string());
    }
    let manifest = manifest.map_err(|e| format!("built-in runner unavailable: {e}"))?;
    let manifest_path = evidence::manifest_path_from_app_root(app_root);
    let unavailable = |error| {
        format!(
            "built-in runner unavailable: {}: {error}",
            manifest_path.display()
        )
    };
    let entry =
        evidence::unique_typed_entry(manifest, SHIPPED_SERVICE.rel_path, SHIPPED_SERVICE.kind)
            .map_err(&unavailable)?;
    let bundle_id = match entry.bundle_id.as_deref() {
        Some(id) if !id.is_empty() && !id.contains('\0') => id.to_string(),
        Some(_) => {
            return Err(unavailable(format!(
                "evidence manifest entry at {} has an empty or NUL-containing bundle_id",
                SHIPPED_SERVICE.rel_path
            )));
        }
        None => {
            return Err(unavailable(format!(
                "evidence manifest entry at {} has no bundle_id",
                SHIPPED_SERVICE.rel_path
            )));
        }
    };
    let executable_path = app_root.join(SHIPPED_SERVICE.rel_path);
    let bundle_path = executable_path
        .parent()
        .and_then(|p| p.parent())
        .and_then(|p| p.parent())
        .map(|p| p.to_path_buf());
    let entitlements = Some(entitlements_from_manifest_value(
        entry.entitlements.as_ref(),
        entry.entitlements_error.as_ref(),
    ));

    Ok(RunnerTarget {
        kind,
        connection: RunnerConnectionKind::XpcService,
        service_name: bundle_id.clone(),
        bundle_id: Some(bundle_id),
        bundle_path,
        executable_path: Some(executable_path),
        registry_id: None,
        signature: None,
        entitlements,
    })
}

pub fn infer_record_kind(record: &RunnerRecord) -> RunnerKind {
    record.kind.unwrap_or(RunnerKind::Byoxpc)
}

/// Fail fast when a selected runner doesn't carry the entitlements the
/// caller required. Shared by the built-in and external resolution paths
/// so the enforcement (a security gate — it blocks the launch) lives in
/// one tested place. `subject` names the runner in the error so the two
/// call sites keep their distinct messages ("built-in runner ...",
/// "external runner ...").
fn enforce_required_entitlements(
    required: &[String],
    entitlements: Option<&RunnerEntitlements>,
    subject: &str,
) -> Result<(), String> {
    if required.is_empty() {
        return Ok(());
    }
    let ent = entitlements.ok_or_else(|| format!("{subject} entitlements unavailable"))?;
    if !runner_manager::entitlements_superset(required, ent) {
        return Err(format!("{subject} does not satisfy required entitlements"));
    }
    Ok(())
}

/// Resolve a selector into the runner target, with the external-registry
/// location injectable. Production passes `None` (resolve from
/// `PW_RUNNER_REGISTRY` / `$HOME` via `runner_registry_path`); tests pass
/// `Some(path)` to a fixture registry so the whole external chain —
/// `load_registry → find_external_record → resolve_external_target →
/// enforce_required_entitlements` — is exercisable at the public boundary
/// without mutating the process-global env. The override is consulted lazily:
/// the built-in branch never touches it, and the external branch never touches
/// the app manifest.
pub fn resolve_runner_target_with_registry(
    app_root: &Path,
    manifest: Result<&EvidenceManifest, &String>,
    selector: &RunnerSelector,
    registry_path_override: Option<&Path>,
) -> Result<RunnerTarget, String> {
    let needs_external = selector.runner_id.is_some() || selector.runner_service.is_some();
    if let Some(problem) = selector_problem(selector) {
        return Err(problem.into());
    }
    if !needs_external {
        let kind = selector.mode.unwrap_or(RunnerKind::Standard);
        let target = builtin_runner_target(app_root, manifest, kind)?;
        enforce_required_entitlements(
            &selector.required_entitlements,
            target.entitlements.as_ref(),
            "built-in runner",
        )?;
        return Ok(target);
    }

    let registry_path = match registry_path_override {
        Some(path) => path.to_path_buf(),
        None => runner_manager::runner_registry_path()?,
    };
    let registry = runner_manager::load_registry(&registry_path)?;
    let record = find_external_record(&registry, selector)?;
    resolve_external_target(record, selector)
}

/// Find the registry record a selector points at, by id (preferred) or
/// service name. Pure over the loaded registry so the by-id / by-service /
/// not-found branches are unit-testable without reading `$HOME`. The id and
/// service branches are mutually exclusive: when an id is set, a matching
/// service is NOT consulted as a fallback.
fn find_external_record<'a>(
    registry: &'a RunnerRegistry,
    selector: &RunnerSelector,
) -> Result<&'a RunnerRecord, String> {
    let record = if let Some(id) = selector.runner_id.as_ref() {
        registry.runners.iter().find(|r| &r.id == id)
    } else if let Some(service) = selector.runner_service.as_ref() {
        registry.runners.iter().find(|r| &r.service_name == service)
    } else {
        None
    }
    .ok_or_else(|| "external runner not found in registry".to_string())?;
    if record.state == runner_manager::RunnerState::Pending {
        return Err("external runner is pending installation".into());
    }
    Ok(record)
}

/// Resolve a registry record + selector into a concrete external target.
/// Split out of `resolve_runner_target_with_registry` so its guard ladder (mode-vs-kind
/// agreement, the entitlement gate, and the built-in-kind rejection) is
/// unit-testable from a hand-built `RunnerRecord` — the registry lookup
/// that precedes it needs `$HOME`, this doesn't.
fn resolve_external_target(
    record: &RunnerRecord,
    selector: &RunnerSelector,
) -> Result<RunnerTarget, String> {
    let record_kind = infer_record_kind(record);
    if let Some(mode) = selector.mode {
        if mode != record_kind {
            return Err(format!(
                "runner.mode mismatch (requested {}, registry has {})",
                mode.as_str(),
                record_kind.as_str()
            ));
        }
    }

    enforce_required_entitlements(
        &selector.required_entitlements,
        Some(&record.entitlements),
        "external runner",
    )?;

    let connection = match record_kind {
        RunnerKind::Byoxpc => RunnerConnectionKind::MachService {
            privileged: matches!(record.scope, RunnerScope::System),
        },
        RunnerKind::Standard => {
            return Err("external runners cannot be built-in kinds".to_string());
        }
    };

    Ok(RunnerTarget {
        kind: record_kind,
        connection,
        service_name: record.service_name.clone(),
        bundle_id: record.bundle_id.clone(),
        bundle_path: Some(PathBuf::from(&record.bundle_path)),
        executable_path: Some(PathBuf::from(&record.executable_path)),
        registry_id: Some(record.id.clone()),
        signature: Some(record.signature.clone()),
        entitlements: Some(record.entitlements.clone()),
    })
}

pub fn runner_provenance_from_target(target: &RunnerTarget) -> RunnerProvenance {
    RunnerProvenance {
        runner_kind: target.kind.as_str().to_string(),
        runner_registry_id: target.registry_id.clone(),
        runner_service_name: target.service_name.clone(),
        runner_bundle_id: target.bundle_id.clone(),
        runner_bundle_path: target.bundle_path.as_ref().map(|p| p.display().to_string()),
        runner_executable_path: target
            .executable_path
            .as_ref()
            .map(|p| p.display().to_string()),
        runner_signature: target.signature.clone(),
        runner_entitlements: target.entitlements.clone(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::{Value, json};
    use std::fs;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn temp_path() -> PathBuf {
        let stamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        std::env::temp_dir().join(format!("pw-request-{}.json", stamp))
    }

    #[test]
    fn parses_runner_selector_from_nested_runner() {
        let path = temp_path();
        let payload = json!({
            "schema_version": crate::json_contract::REQUEST_SCHEMA_VERSION,
            "specimen_id": "specimen",
            "policy": {"format": "sbpl", "sbpl_source": "(version 1)\n(allow default)\n"},
            "probe_plan": [],
            "runner": {
                "id": "runner-abc",
                "service": "com.example.runner",
                "required_entitlements": ["com.apple.security.cs.allow-jit"],
                "mode": "byoxpc"
            }
        });
        fs::write(&path, serde_json::to_string(&payload).unwrap()).unwrap();
        let text = fs::read_to_string(&path).expect("read request");
        let value: Value = serde_json::from_str(&text).expect("parse request");
        let selector = parse_runner_selector_value(&value).expect("parse selector");
        assert_eq!(selector.runner_id.as_deref(), Some("runner-abc"));
        assert_eq!(
            selector.runner_service.as_deref(),
            Some("com.example.runner")
        );
        assert_eq!(selector.required_entitlements.len(), 1);
        assert_eq!(selector.mode, Some(RunnerKind::Byoxpc));
        let _ = fs::remove_file(&path);
    }

    // ---- builders -----------------------------------------------------------

    fn ent(keys: &[&str]) -> RunnerEntitlements {
        RunnerEntitlements {
            raw_plist: None,
            keys: keys.iter().map(|s| s.to_string()).collect(),
            error: None,
        }
    }

    fn external_record(
        kind: Option<RunnerKind>,
        scope: RunnerScope,
        ent_keys: &[&str],
    ) -> RunnerRecord {
        RunnerRecord {
            state: runner_manager::RunnerState::Installed,
            ownership: None,
            id: "runner-ext".to_string(),
            service_name: "com.example.runner".to_string(),
            bundle_path: "/opt/pw/Runner.app".to_string(),
            executable_path: "/opt/pw/Runner.app/Contents/MacOS/PWRunner".to_string(),
            bundle_id: Some("com.example.runner".to_string()),
            scope,
            protocol_version: runner_manager::RUNNER_PROTOCOL_VERSION,
            signature: RunnerSignature {
                team_id: None,
                identity: None,
                cdhash: None,
                valid: true,
                adhoc: true,
            },
            entitlements: ent(ent_keys),
            installed_at_unix_ms: 0,
            kind,
        }
    }

    fn selector_with(
        mode: Option<RunnerKind>,
        required: &[&str],
        external: bool,
    ) -> RunnerSelector {
        RunnerSelector {
            runner_id: external.then(|| "runner-ext".to_string()),
            required_entitlements: required.iter().map(|s| s.to_string()).collect(),
            mode,
            ..Default::default()
        }
    }

    // RunnerTarget doesn't implement Debug, so `.unwrap_err()` won't compile
    // on a Result<RunnerTarget, _>. Unwrap the error explicitly instead.
    fn err_of(result: Result<RunnerTarget, String>) -> String {
        match result {
            Ok(_) => panic!("expected an error, got Ok(RunnerTarget)"),
            Err(e) => e,
        }
    }

    fn record_named(id: &str, service: &str) -> RunnerRecord {
        let mut r = external_record(Some(RunnerKind::Byoxpc), RunnerScope::User, &[]);
        r.id = id.to_string();
        r.service_name = service.to_string();
        r
    }

    fn registry_of(records: Vec<RunnerRecord>) -> RunnerRegistry {
        RunnerRegistry {
            pending_cleanup: Vec::new(),
            schema_version: runner_manager::RUNNER_REGISTRY_SCHEMA_VERSION,
            runners: records,
        }
    }

    // ---- cheap batch: selector parsing + mode parsing + conflict guards ------

    #[test]
    fn malformed_selection_never_falls_back_or_discards_entitlements() {
        for (value, field) in [
            (json!({"runner": "standard"}), "runner"),
            (json!({"runner": {"servce": "external"}}), "servce"),
            (json!({"runner": {"id": 42}}), "runner.id"),
            (json!({"runner": {"mode": false}}), "runner.mode"),
            (
                json!({"runner": {"required_entitlements": "required"}}),
                "runner.required_entitlements",
            ),
            (
                json!({"runner": {"required_entitlements": ["required", false]}}),
                "runner.required_entitlements[1]",
            ),
            (json!({"runner_id": 42}), "runner_id"),
            (json!({"runner_service": []}), "runner_service"),
            (json!({"runner_mode": false}), "runner_mode"),
            (
                json!({"runner": {"id": "valid"}, "runner_id": 42}),
                "runner_id",
            ),
            (
                json!({"required_entitlements": ["required", 42]}),
                "required_entitlements[1]",
            ),
        ] {
            let error = parse_runner_selector_value(&value)
                .err()
                .expect("must reject malformed intent");
            assert!(error.message.contains(field), "{error}: expected {field}");
        }
    }

    #[test]
    fn optional_nulls_and_explicit_nested_empty_entitlements_have_defined_meanings() {
        let value = json!({"runner": null, "runner_id": null, "runner_mode": null,
                           "required_entitlements": null});
        let parsed = parse_runner_selector_value(&value).unwrap();
        assert!(parsed.runner_id.is_none() && parsed.mode.is_none());
        assert!(parsed.required_entitlements.is_empty());
        let parsed = parse_runner_selector_value(&json!({
            "required_entitlements": ["outer"], "runner": {"required_entitlements": []}
        }))
        .unwrap();
        assert!(
            parsed.required_entitlements.is_empty(),
            "the explicit nested value takes precedence"
        );
    }

    #[test]
    fn parses_legacy_top_level_fields() {
        // The legacy top-level shape is documented as still accepted; a
        // regression dropping it would otherwise pass silently.
        let value = json!({
            "runner_id": "legacy-id",
            "runner_service": "com.legacy.svc",
            "required_entitlements": ["com.apple.security.cs.allow-jit"],
            "runner_mode": "byoxpc"
        });
        let s = parse_runner_selector_value(&value).expect("parse");
        assert_eq!(s.runner_id.as_deref(), Some("legacy-id"));
        assert_eq!(s.runner_service.as_deref(), Some("com.legacy.svc"));
        assert_eq!(s.required_entitlements.len(), 1);
        assert_eq!(s.mode, Some(RunnerKind::Byoxpc));
    }

    #[test]
    fn nested_runner_takes_precedence_over_legacy_top_level() {
        let value = json!({
            "runner": { "id": "nested-id" },
            "runner_id": "legacy-id"
        });
        let s = parse_runner_selector_value(&value).expect("parse");
        assert_eq!(s.runner_id.as_deref(), Some("nested-id"));
    }

    #[test]
    fn parse_runner_mode_rejects_machme_with_byoxpc_hint() {
        let err = parse_runner_mode("machme", "runner.mode").unwrap_err();
        assert!(
            err.contains("byoxpc"),
            "message should steer to byoxpc: {err}"
        );
        assert!(
            err.contains("runner.mode"),
            "message should name the field: {err}"
        );
    }

    #[test]
    fn parse_runner_mode_rejects_unknown_value() {
        let err = parse_runner_mode("bogus", "runner_mode").unwrap_err();
        assert!(err.contains("invalid runner_mode value"), "got: {err}");
    }

    #[test]
    fn resolve_rejects_standard_mode_with_external_selector() {
        // Errors before any filesystem access, so the app_root is irrelevant.
        let selector = RunnerSelector {
            runner_id: Some("runner-ext".to_string()),
            mode: Some(RunnerKind::Standard),
            ..Default::default()
        };
        let err = err_of(resolve_runner_target_with_registry(
            Path::new("/nonexistent"),
            Err(&"no manifest".to_string()),
            &selector,
            None,
        ));
        assert!(
            err.contains("cannot be combined with an external runner"),
            "got: {err}"
        );
    }

    #[test]
    fn resolve_rejects_byoxpc_mode_without_external_selector() {
        let selector = RunnerSelector {
            mode: Some(RunnerKind::Byoxpc),
            ..Default::default()
        };
        let err = err_of(resolve_runner_target_with_registry(
            Path::new("/nonexistent"),
            Err(&"no manifest".to_string()),
            &selector,
            None,
        ));
        assert!(
            err.contains("requires runner.id or runner.service"),
            "got: {err}"
        );
    }

    // ---- entitlement enforcement gate (security-relevant) -------------------

    #[test]
    fn entitlement_gate_skips_when_nothing_required() {
        // Empty required short-circuits before the None check.
        assert!(enforce_required_entitlements(&[], None, "built-in runner").is_ok());
    }

    #[test]
    fn entitlement_gate_passes_on_superset() {
        let e = ent(&["A", "B"]);
        assert!(
            enforce_required_entitlements(&["A".to_string()], Some(&e), "external runner").is_ok()
        );
    }

    #[test]
    fn entitlement_gate_blocks_on_shortfall() {
        let e = ent(&["A"]);
        let err = enforce_required_entitlements(
            &["A".to_string(), "B".to_string()],
            Some(&e),
            "external runner",
        )
        .unwrap_err();
        assert_eq!(
            err,
            "external runner does not satisfy required entitlements"
        );
    }

    #[test]
    fn entitlement_gate_blocks_when_entitlements_unavailable() {
        let err =
            enforce_required_entitlements(&["A".to_string()], None, "built-in runner").unwrap_err();
        assert_eq!(err, "built-in runner entitlements unavailable");
    }

    // ---- external target resolution (mode/kind, connection, gate) -----------

    #[test]
    fn external_target_byoxpc_user_is_unprivileged_mach_service() {
        let record = external_record(Some(RunnerKind::Byoxpc), RunnerScope::User, &[]);
        let selector = selector_with(Some(RunnerKind::Byoxpc), &[], true);
        let target = resolve_external_target(&record, &selector).expect("resolve");
        assert_eq!(target.kind, RunnerKind::Byoxpc);
        assert_eq!(target.registry_id.as_deref(), Some("runner-ext"));
        assert_eq!(target.service_name, "com.example.runner");
        match target.connection {
            RunnerConnectionKind::MachService { privileged } => assert!(!privileged),
            other => panic!("expected unprivileged MachService, got {other:?}"),
        }
    }

    #[test]
    fn external_target_byoxpc_system_is_privileged_mach_service() {
        let record = external_record(Some(RunnerKind::Byoxpc), RunnerScope::System, &[]);
        let selector = selector_with(None, &[], true);
        let target = resolve_external_target(&record, &selector).expect("resolve");
        match target.connection {
            RunnerConnectionKind::MachService { privileged } => assert!(privileged),
            other => panic!("expected privileged MachService, got {other:?}"),
        }
    }

    #[test]
    fn external_target_rejects_mode_kind_mismatch() {
        // Record infers Standard (kind=Some(Standard)); requesting byoxpc mismatches.
        let record = external_record(Some(RunnerKind::Standard), RunnerScope::User, &[]);
        let selector = selector_with(Some(RunnerKind::Byoxpc), &[], true);
        let err = err_of(resolve_external_target(&record, &selector));
        assert!(err.contains("runner.mode mismatch"), "got: {err}");
        assert!(
            err.contains("requested byoxpc") && err.contains("registry has standard"),
            "got: {err}"
        );
    }

    #[test]
    fn external_target_enforces_required_entitlements() {
        let record = external_record(Some(RunnerKind::Byoxpc), RunnerScope::User, &["A"]);
        let selector = selector_with(Some(RunnerKind::Byoxpc), &["A", "B"], true);
        let err = err_of(resolve_external_target(&record, &selector));
        assert_eq!(
            err,
            "external runner does not satisfy required entitlements"
        );
    }

    #[test]
    fn external_target_rejects_builtin_kind_record() {
        // A record that infers Standard with no mode requested: the
        // connection match rejects it as a built-in kind.
        let record = external_record(Some(RunnerKind::Standard), RunnerScope::User, &[]);
        let selector = selector_with(None, &[], true);
        let err = err_of(resolve_external_target(&record, &selector));
        assert_eq!(err, "external runners cannot be built-in kinds");
    }

    // ---- registry record lookup (pure over a loaded registry) ---------------

    #[test]
    fn find_external_record_by_id() {
        let reg = registry_of(vec![record_named("a", "svc-a"), record_named("b", "svc-b")]);
        let sel = RunnerSelector {
            runner_id: Some("b".to_string()),
            ..Default::default()
        };
        let rec = find_external_record(&reg, &sel).expect("found");
        assert_eq!(rec.id, "b");
    }

    #[test]
    fn find_external_record_by_service_when_no_id() {
        let reg = registry_of(vec![record_named("a", "svc-a"), record_named("b", "svc-b")]);
        let sel = RunnerSelector {
            runner_service: Some("svc-a".to_string()),
            ..Default::default()
        };
        let rec = find_external_record(&reg, &sel).expect("found");
        assert_eq!(rec.id, "a");
    }

    #[test]
    fn find_external_record_prefers_id_over_service() {
        // When an id is present the service is ignored entirely.
        let reg = registry_of(vec![record_named("a", "svc-a"), record_named("b", "svc-b")]);
        let sel = RunnerSelector {
            runner_id: Some("a".to_string()),
            runner_service: Some("svc-b".to_string()),
            ..Default::default()
        };
        let rec = find_external_record(&reg, &sel).expect("found");
        assert_eq!(rec.id, "a");
    }

    #[test]
    fn find_external_record_id_miss_does_not_fall_back_to_service() {
        // id set but unmatched → the service branch is NOT consulted, so the
        // lookup fails even though the service would have matched.
        let reg = registry_of(vec![record_named("a", "svc-a")]);
        let sel = RunnerSelector {
            runner_id: Some("missing".to_string()),
            runner_service: Some("svc-a".to_string()),
            ..Default::default()
        };
        let err = find_external_record(&reg, &sel).unwrap_err();
        assert_eq!(err, "external runner not found in registry");
    }

    #[test]
    fn find_external_record_not_found() {
        let reg = registry_of(vec![record_named("a", "svc-a")]);
        let sel = RunnerSelector {
            runner_id: Some("zzz".to_string()),
            ..Default::default()
        };
        let err = find_external_record(&reg, &sel).unwrap_err();
        assert_eq!(err, "external runner not found in registry");
    }

    #[test]
    fn find_external_record_empty_selector_is_not_found() {
        let reg = registry_of(vec![record_named("a", "svc-a")]);
        let sel = RunnerSelector::default();
        let err = find_external_record(&reg, &sel).unwrap_err();
        assert_eq!(err, "external runner not found in registry");
    }

    // ---- public-boundary external resolution (registry injected, no $HOME) ---
    // These drive the true entry point `resolve_runner_target_with_registry`
    // against an on-disk fixture, so the whole external chain — load_registry
    // → find_external_record → resolve_external_target →
    // enforce_required_entitlements — is pinned at the boundary callers use.
    // Any of those helpers can be re-inlined and these still hold; only a
    // change in the security OUTCOME fails them. No process-global env is
    // touched, so they are parallel-safe.

    fn registry_fixture(reg: &RunnerRegistry) -> PathBuf {
        let path = temp_path();
        fs::write(
            &path,
            serde_json::to_string(reg).expect("serialize registry"),
        )
        .expect("write registry fixture");
        path
    }

    #[test]
    fn resolve_via_registry_blocks_external_runner_missing_entitlements() {
        // The registry record carries only "A"; the caller requires "A"+"B".
        // The gate must refuse the launch even though the runner exists and
        // its mode matches.
        let reg = registry_of(vec![external_record(
            Some(RunnerKind::Byoxpc),
            RunnerScope::User,
            &["A"],
        )]);
        let path = registry_fixture(&reg);
        let selector = selector_with(Some(RunnerKind::Byoxpc), &["A", "B"], true);
        let err = err_of(resolve_runner_target_with_registry(
            Path::new("/unused"),
            Err(&"no manifest".to_string()),
            &selector,
            Some(&path),
        ));
        assert_eq!(
            err,
            "external runner does not satisfy required entitlements"
        );
        let _ = fs::remove_file(&path);
    }

    #[test]
    fn resolve_via_registry_admits_external_runner_with_sufficient_entitlements() {
        // Positive companion: same record, caller requires only "A" (a
        // subset). The gate passes and the target is built from the
        // looked-up record — proving the gate is REACHED through the real
        // registry lookup, not short-circuited before it.
        let reg = registry_of(vec![external_record(
            Some(RunnerKind::Byoxpc),
            RunnerScope::User,
            &["A"],
        )]);
        let path = registry_fixture(&reg);
        let selector = selector_with(Some(RunnerKind::Byoxpc), &["A"], true);
        let target = resolve_runner_target_with_registry(
            Path::new("/unused"),
            Err(&"no manifest".to_string()),
            &selector,
            Some(&path),
        )
        .expect("resolve");
        assert_eq!(target.kind, RunnerKind::Byoxpc);
        assert_eq!(target.registry_id.as_deref(), Some("runner-ext"));
        match target.connection {
            RunnerConnectionKind::MachService { privileged } => assert!(!privileged),
            other => panic!("expected unprivileged MachService, got {other:?}"),
        }
        let _ = fs::remove_file(&path);
    }
    #[test]
    #[ignore = "docs/BYOXPC-REMEDIATION-PLAN.md Group 3: selection must refuse a required key whose recorded value is false"]
    fn selection_refuses_a_false_valued_required_key() {
        // An on-disk registry record whose read-back names the required key
        // with the value false. Built from the codesign JSON the installer
        // records, so the record carries the value, not only the key.
        let mut record = external_record(Some(RunnerKind::Byoxpc), RunnerScope::User, &[]);
        record.entitlements = runner_manager::entitlements_from_json(
            &json!({"com.apple.security.cs.allow-jit": false}),
        );
        let path = registry_fixture(&registry_of(vec![record]));
        let selector = selector_with(
            Some(RunnerKind::Byoxpc),
            &["com.apple.security.cs.allow-jit"],
            true,
        );
        let outcome = resolve_runner_target_with_registry(
            Path::new("/unused"),
            Err(&"no manifest".to_string()),
            &selector,
            Some(&path),
        );
        let _ = fs::remove_file(&path);
        match outcome {
            Ok(_) => panic!("a required key present with value false must be refused"),
            Err(e) => assert!(
                e.contains("com.apple.security.cs.allow-jit") && e.contains("worker"),
                "the refusal names the process and the key: {e}"
            ),
        }
    }

    #[test]
    fn pending_external_record_is_not_selectable() {
        let mut record = record_named("pending", "com.example.pending");
        record.state = runner_manager::RunnerState::Pending;
        let reg = registry_of(vec![record]);
        for selector in [
            RunnerSelector {
                runner_id: Some("pending".into()),
                ..Default::default()
            },
            RunnerSelector {
                runner_service: Some("com.example.pending".into()),
                ..Default::default()
            },
        ] {
            assert_eq!(
                find_external_record(&reg, &selector).unwrap_err(),
                "external runner is pending installation"
            );
        }
    }
}
