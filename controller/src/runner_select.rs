//! Runner selection and provenance logic.
//!
//! The controller can target the embedded standard/debuggable runner or an
//! external runner registered in the local registry. This module resolves the
//! request selector into a concrete service connection and auditable metadata.

use serde::Serialize;
use serde_json::Value;
use std::path::{Path, PathBuf};

use crate::app_layout::{
    resolve_pw_runner_bundle_info, PW_RUNNER_DEBUG_SERVICE_DIR, PW_RUNNER_STANDARD_SERVICE_DIR,
};
use crate::bundle::read_bundle_info;
use crate::evidence;
use crate::runner_manager::{self, RunnerEntitlements, RunnerKind, RunnerRecord, RunnerScope, RunnerSignature};

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
            selector.mode = Some(
                RunnerKind::parse(v)
                    .ok_or_else(|| format!("invalid runner.mode value: {v}"))?,
            );
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
            selector.mode = Some(
                RunnerKind::parse(v)
                    .ok_or_else(|| format!("invalid runner_mode value: {v}"))?,
            );
        }
    }

    Ok(selector)
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
        RunnerKind::Debuggable => PW_RUNNER_DEBUG_SERVICE_DIR,
        RunnerKind::Byoxpc | RunnerKind::Machme => {
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
    if let Some(kind) = record.kind {
        return kind;
    }
    let bundle_path = Path::new(&record.bundle_path);
    if bundle_path.is_dir() {
        if let Ok(info) = read_bundle_info(bundle_path) {
            if info.package_type.as_deref() == Some("XPC!") {
                return RunnerKind::Byoxpc;
            }
        }
    }
    RunnerKind::Machme
}

pub fn resolve_runner_target(
    app_root: &Path,
    selector: &RunnerSelector,
) -> Result<RunnerTarget, String> {
    let needs_external = selector.runner_id.is_some() || selector.runner_service.is_some();
    if matches!(selector.mode, Some(RunnerKind::Debuggable | RunnerKind::Standard)) && needs_external {
        return Err(
            "runner.mode=standard or runner.mode=debuggable cannot be combined with an external runner selection"
                .to_string(),
        );
    }
    if matches!(selector.mode, Some(RunnerKind::Byoxpc | RunnerKind::Machme)) && !needs_external {
        return Err("runner.mode requires runner.id or runner.service for external runners".to_string());
    }
    if !needs_external {
        let kind = selector.mode.unwrap_or(RunnerKind::Standard);
        if matches!(kind, RunnerKind::Byoxpc | RunnerKind::Machme) {
            return Err("runner.mode requires runner.id or runner.service for external runners".to_string());
        }
        let target = builtin_runner_target(app_root, kind)?;
        if !selector.required_entitlements.is_empty() {
            let ent = target
                .entitlements
                .as_ref()
                .ok_or_else(|| "built-in runner entitlements unavailable".to_string())?;
            // Enforce entitlements before launching so mismatches fail fast.
            if !runner_manager::entitlements_superset(&selector.required_entitlements, ent) {
                return Err("built-in runner does not satisfy required entitlements".to_string());
            }
        }
        return Ok(target);
    }

    let registry_path = runner_manager::runner_registry_path()?;
    let registry = runner_manager::load_registry(&registry_path)?;

    let record = if let Some(id) = selector.runner_id.as_ref() {
        registry.runners.iter().find(|r| &r.id == id)
    } else if let Some(service) = selector.runner_service.as_ref() {
        registry.runners.iter().find(|r| &r.service_name == service)
    } else {
        None
    }
    .ok_or_else(|| "external runner not found in registry".to_string())?;

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

    if !selector.required_entitlements.is_empty()
        && !runner_manager::entitlements_superset(
            &selector.required_entitlements,
            &record.entitlements,
        )
    {
        return Err("external runner does not satisfy required entitlements".to_string());
    }

    let connection = match record_kind {
        RunnerKind::Byoxpc | RunnerKind::Machme => RunnerConnectionKind::MachService {
            privileged: matches!(record.scope, RunnerScope::System),
        },
        RunnerKind::Debuggable | RunnerKind::Standard => {
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
                "mode": "machme"
            }
        });
        fs::write(&path, serde_json::to_string(&payload).unwrap()).unwrap();
        let text = fs::read_to_string(&path).expect("read request");
        let value: Value = serde_json::from_str(&text).expect("parse request");
        let selector = parse_runner_selector_value(&value).expect("parse selector");
        assert_eq!(selector.runner_id.as_deref(), Some("runner-abc"));
        assert_eq!(selector.runner_service.as_deref(), Some("com.example.runner"));
        assert_eq!(selector.required_entitlements.len(), 1);
        assert_eq!(selector.mode, Some(RunnerKind::Machme));
        let _ = fs::remove_file(&path);
    }
}
