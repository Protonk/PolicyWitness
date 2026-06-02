//! Runner selection and provenance logic.
//!
//! The controller can target the embedded standard runner or an
//! external runner registered in the local registry. This module resolves the
//! request selector into a concrete service connection and auditable metadata.

use serde::Serialize;
use serde_json::Value;
use std::path::{Path, PathBuf};

use crate::app_layout::{
    resolve_pw_runner_bundle_info, PW_RUNNER_STANDARD_SERVICE_DIR,
};
use crate::evidence;
use crate::runner_manager::{self, RunnerEntitlements, RunnerKind, RunnerRecord, RunnerRegistry, RunnerScope, RunnerSignature};

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
    pub process_name: String,
    pub bundle_id: Option<String>,
    pub bundle_path: Option<PathBuf>,
    pub executable_path: Option<PathBuf>,
    pub registry_id: Option<String>,
    pub signature: Option<RunnerSignature>,
    pub entitlements: Option<RunnerEntitlements>,
}

#[derive(Serialize)]
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

pub fn parse_runner_selector_value(value: &Value) -> Result<RunnerSelector, String> {
    let mut selector = RunnerSelector::default();

    if let Some(runner) = value.get("runner").and_then(|v| v.as_object()) {
        if let Some(v) = runner.get("id").and_then(|v| v.as_str()) {
            selector.runner_id = Some(v.to_string());
        }
        if let Some(v) = runner.get("service").and_then(|v| v.as_str()) {
            selector.runner_service = Some(v.to_string());
        }
        if let Some(list) = runner.get("required_entitlements").and_then(|v| v.as_array()) {
            selector.required_entitlements = list
                .iter()
                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                .collect();
        }
        if let Some(v) = runner.get("mode").and_then(|v| v.as_str()) {
            selector.mode = Some(parse_runner_mode(v, "runner.mode")?);
        }
    }

    if selector.runner_id.is_none() {
        // Legacy top-level fields are still accepted for backward compatibility.
        if let Some(v) = value.get("runner_id").and_then(|v| v.as_str()) {
            selector.runner_id = Some(v.to_string());
        }
    }
    if selector.runner_service.is_none() {
        if let Some(v) = value.get("runner_service").and_then(|v| v.as_str()) {
            selector.runner_service = Some(v.to_string());
        }
    }
    if selector.required_entitlements.is_empty() {
        if let Some(list) = value.get("required_entitlements").and_then(|v| v.as_array()) {
            selector.required_entitlements = list
                .iter()
                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                .collect();
        }
    }
    if selector.mode.is_none() {
        if let Some(v) = value.get("runner_mode").and_then(|v| v.as_str()) {
            selector.mode = Some(parse_runner_mode(v, "runner_mode")?);
        }
    }

    Ok(selector)
}

fn parse_runner_mode(value: &str, field: &str) -> Result<RunnerKind, String> {
    if value == "machme" {
        return Err(format!(
            "{field}=\"machme\" is not supported; use \"byoxpc\""
        ));
    }
    RunnerKind::parse(value).ok_or_else(|| format!("invalid {field} value: {value}"))
}

fn entitlements_from_manifest_value(
    value: Option<&Value>,
    error: Option<&String>,
) -> RunnerEntitlements {
    let mut entitlements = value
        .map(runner_manager::entitlements_from_json)
        .unwrap_or(RunnerEntitlements {
            raw_plist: None,
            keys: Vec::new(),
            error: None,
        });
    if entitlements.raw_plist.is_none() {
        entitlements.raw_plist = value
            .and_then(|v| serde_json::to_string_pretty(v).ok());
    }
    if let Some(err) = error {
        entitlements.error = Some(err.to_string());
    }
    entitlements
}

fn builtin_runner_target(app_root: &Path, kind: RunnerKind) -> Result<RunnerTarget, String> {
    let service_dir = match kind {
        RunnerKind::Standard => PW_RUNNER_STANDARD_SERVICE_DIR,
        RunnerKind::Byoxpc => {
            return Err("builtin runner target requires a built-in kind".to_string());
        }
    };
    let runner_info = resolve_pw_runner_bundle_info(app_root, service_dir)?;
    let bundle_path = app_root
        .join("Contents")
        .join("XPCServices")
        .join(format!("{service_dir}.xpc"));
    let executable_path = bundle_path
        .join("Contents")
        .join("MacOS")
        .join(&runner_info.executable);

    let manifest_path = evidence::manifest_path_from_app_root(app_root);
    let manifest = evidence::load_manifest(&manifest_path)
        .map_err(|e| format!("failed to read evidence manifest: {e}"))?;
    let rel_path =
        evidence::rel_path_from_absolute(app_root, &executable_path).unwrap_or_default();
    let entry = evidence::find_entry_by_rel_path(&manifest, &rel_path)
        .or_else(|| evidence::find_entry_by_id(&manifest, &runner_info.bundle_id));
    let entitlements = entry.map(|e| {
        entitlements_from_manifest_value(
            e.entitlements.as_ref(),
            e.entitlements_error.as_ref(),
        )
    });

    Ok(RunnerTarget {
        kind,
        connection: RunnerConnectionKind::XpcService,
        service_name: runner_info.bundle_id.clone(),
        process_name: runner_info.executable.clone(),
        bundle_id: Some(runner_info.bundle_id),
        bundle_path: Some(bundle_path),
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

pub fn resolve_runner_target(
    app_root: &Path,
    selector: &RunnerSelector,
) -> Result<RunnerTarget, String> {
    let needs_external = selector.runner_id.is_some() || selector.runner_service.is_some();
    if matches!(selector.mode, Some(RunnerKind::Standard)) && needs_external {
        return Err(
            "runner.mode=standard cannot be combined with an external runner selection"
                .to_string(),
        );
    }
    if matches!(selector.mode, Some(RunnerKind::Byoxpc)) && !needs_external {
        return Err("runner.mode requires runner.id or runner.service for external runners".to_string());
    }
    if !needs_external {
        let kind = selector.mode.unwrap_or(RunnerKind::Standard);
        if matches!(kind, RunnerKind::Byoxpc) {
            return Err("runner.mode requires runner.id or runner.service for external runners".to_string());
        }
        let target = builtin_runner_target(app_root, kind)?;
        enforce_required_entitlements(
            &selector.required_entitlements,
            target.entitlements.as_ref(),
            "built-in runner",
        )?;
        return Ok(target);
    }

    let registry_path = runner_manager::runner_registry_path()?;
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
    if let Some(id) = selector.runner_id.as_ref() {
        registry.runners.iter().find(|r| &r.id == id)
    } else if let Some(service) = selector.runner_service.as_ref() {
        registry.runners.iter().find(|r| &r.service_name == service)
    } else {
        None
    }
    .ok_or_else(|| "external runner not found in registry".to_string())
}

/// Resolve a registry record + selector into a concrete external target.
/// Split out of `resolve_runner_target` so its guard ladder (mode-vs-kind
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
        process_name: Path::new(&record.executable_path)
            .file_name()
            .and_then(|s| s.to_str())
            .unwrap_or("PWRunner")
            .to_string(),
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
        runner_bundle_path: target
            .bundle_path
            .as_ref()
            .map(|p| p.display().to_string()),
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
    use serde_json::{json, Value};
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
            "schema_version": 1,
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
        assert_eq!(selector.runner_service.as_deref(), Some("com.example.runner"));
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

    fn selector_with(mode: Option<RunnerKind>, required: &[&str], external: bool) -> RunnerSelector {
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
            schema_version: runner_manager::RUNNER_REGISTRY_SCHEMA_VERSION,
            runners: records,
        }
    }

    // ---- cheap batch: selector parsing + mode parsing + conflict guards ------

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
        assert!(err.contains("byoxpc"), "message should steer to byoxpc: {err}");
        assert!(err.contains("runner.mode"), "message should name the field: {err}");
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
        let err = err_of(resolve_runner_target(Path::new("/nonexistent"), &selector));
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
        let err = err_of(resolve_runner_target(Path::new("/nonexistent"), &selector));
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
        assert_eq!(err, "external runner does not satisfy required entitlements");
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
        assert_eq!(err, "external runner does not satisfy required entitlements");
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
}
