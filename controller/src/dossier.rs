//! The specimen dossier: controller-collected facts about what the controller
//! submitted and what ran it, gathered before invocation and retained on every
//! `kind: "run"` envelope.
//!
//! Nothing here embeds source or parameter values, proves worker compilation,
//! or changes whether a request is admitted or the runner invoked. Collection
//! failures are recorded in the record they concern.

use serde::Serialize;
use serde_json::Value;
use std::path::{Path, PathBuf};

use crate::app_layout::{SHIPPED_SERVICE, SHIPPED_VALIDATOR, SHIPPED_WORKER, ShippedBinary};
use crate::augments::PolicyAugmentation;
use crate::evidence::{self, EvidenceManifest};
use crate::host_facts;
use crate::runner_select::{RunnerProvenance, RunnerTarget};
use crate::sbpl_imports::{self, ImportRecord, MAX_SBPL_SOURCE_BYTES};

/// `data.specimen`.
#[derive(Serialize, Clone)]
pub struct Specimen {
    pub request_path: Option<String>,
    pub policy: PolicyDossier,
    pub host: HostFacts,
    pub runner_provenance: Option<RunnerProvenance>,
    pub app_provenance: Option<AppProvenance>,
    pub binaries: Binaries,
}

#[derive(Serialize, Clone)]
pub struct PolicyDossier {
    pub augmentation: Augmentation,
    pub imports: Imports,
}

#[derive(Serialize, Clone)]
pub struct AppProvenance {
    pub evidence_manifest_path: String,
    pub evidence_verify: Option<evidence::VerifyReport>,
}

/// The augmentation record. Hashes identify string source bytes that existed:
/// `original_sha256` the pre-augmentation string, `applied_sha256` the string
/// selected for invocation (the unchanged source when nothing was applied).
#[derive(Serialize, Clone)]
pub struct Augmentation {
    pub status: String,
    pub applied: Vec<String>,
    pub original_sha256: Option<String>,
    pub applied_sha256: Option<String>,
    pub error: Option<String>,
}

impl Augmentation {
    pub fn not_requested(source: Option<&str>) -> Self {
        let hash = source.map(sbpl_imports::sha256_hex);
        Augmentation {
            status: "not_requested".into(),
            applied: Vec::new(),
            original_sha256: hash.clone(),
            applied_sha256: hash,
            error: None,
        }
    }
    pub fn applied(record: &PolicyAugmentation, original_existed: bool) -> Self {
        Augmentation {
            status: "applied".into(),
            applied: record.applied.clone(),
            original_sha256: original_existed.then(|| record.original_sha256.clone()),
            applied_sha256: Some(record.applied_sha256.clone()),
            error: None,
        }
    }
    pub fn failed(original: Option<&str>, error: String) -> Self {
        Augmentation {
            status: "failed".into(),
            applied: Vec::new(),
            original_sha256: original.map(sbpl_imports::sha256_hex),
            applied_sha256: None,
            error: Some(error),
        }
    }
    pub fn not_applicable() -> Self {
        Augmentation {
            status: "not_applicable".into(),
            applied: Vec::new(),
            original_sha256: None,
            applied_sha256: None,
            error: None,
        }
    }
}

/// The import inventory of the source selected for invocation, under the
/// helper's search paths and bounds. `complete` means the literal import
/// closure was exhausted with nothing unresolved, no cycle, no nonliteral form,
/// no decoding error and no bound hit; it does not mean compiler-complete.
#[derive(Serialize, Clone)]
pub struct Imports {
    pub status: String,
    pub closure_sha256: Option<String>,
    pub records: Vec<ImportRecord>,
    pub cycle: Option<Vec<String>>,
    pub exceeded: Option<String>,
    pub failure: Option<String>,
}

impl Imports {
    pub fn not_applicable(failure: Option<String>) -> Self {
        Imports {
            status: "not_applicable".into(),
            closure_sha256: None,
            records: Vec::new(),
            cycle: None,
            exceeded: None,
            failure,
        }
    }
    pub fn failed(failure: String) -> Self {
        Imports {
            status: "failed".into(),
            closure_sha256: None,
            records: Vec::new(),
            cycle: None,
            exceeded: None,
            failure: Some(failure),
        }
    }
    /// Scan the selected source synchronously. The scan shares the helper's
    /// depth, count and source bounds and its closure hash algorithm.
    pub fn scan(source: &str) -> Self {
        if source.len() > MAX_SBPL_SOURCE_BYTES {
            return Imports::failed(format!(
                "source is {} bytes; the import scan reads at most {} bytes",
                source.len(),
                MAX_SBPL_SOURCE_BYTES
            ));
        }
        let resolved = sbpl_imports::resolve_imports(source);
        let incomplete = resolved.exceeded.is_some()
            || resolved.cycle.is_some()
            || resolved.nonliteral_imports
            || resolved.records.iter().any(|r| r.error.is_some());
        let closure = sbpl_imports::compute_closure_hash(source, &resolved.records);
        Imports {
            status: if incomplete { "incomplete" } else { "complete" }.into(),
            closure_sha256: Some(closure),
            records: resolved.records,
            cycle: resolved.cycle,
            exceeded: resolved.exceeded,
            failure: if resolved.nonliteral_imports {
                Some("a nonliteral (import ...) form could not be followed".into())
            } else {
                None
            },
        }
    }
}

/// Host facts read through `sysctlbyname` (`kern.osproductversion`,
/// `kern.osversion`, `kern.osrelease`, `hw.machine`); null when a read fails.
/// Environment context only: nothing here identifies the worker's or the
/// validator's sandbox libraries.
#[derive(Serialize, Clone, Debug)]
pub struct HostFacts {
    pub macos_version: Option<String>,
    pub macos_build: Option<String>,
    pub kernel_release: Option<String>,
    pub arch: Option<String>,
}

impl HostFacts {
    pub fn collect() -> Self {
        HostFacts {
            macos_version: host_facts::sysctl_string("kern.osproductversion"),
            macos_build: host_facts::macos_build_version(),
            kernel_release: host_facts::sysctl_string("kern.osrelease"),
            arch: host_facts::sysctl_string("hw.machine"),
        }
    }
}

/// One selected binary the app manifest does not describe as selected:
/// its path, its hash, the manifest baseline for the role and the comparison.
#[derive(Serialize, Clone, Debug, PartialEq)]
pub struct BinaryRecord {
    pub path: Option<String>,
    pub actual_sha256: Option<String>,
    pub baseline_sha256: Option<String>,
    pub verification: String,
    pub reason: Option<String>,
}

#[derive(Serialize, Clone, Debug, PartialEq)]
pub struct Binaries {
    pub service: Option<BinaryRecord>,
    pub worker: Option<BinaryRecord>,
    pub validator: Option<BinaryRecord>,
}

/// The echo bound the runner applies to override paths; longer strings are
/// neither echoed nor read.
pub const OVERRIDE_PATH_ECHO_BYTES: usize = 1023;

/// Baseline hash for one role: the manifest entry at the role's fixed path with
/// the required kind, whose `sha256` is 64 hexadecimal digits.
fn baseline(
    manifest: Result<&EvidenceManifest, &String>,
    role: &ShippedBinary,
) -> Result<Option<String>, String> {
    let manifest = manifest.map_err(|e| format!("app evidence manifest unavailable: {e}"))?;
    let entry = evidence::unique_typed_entry(manifest, role.rel_path, role.kind)?;
    match entry.sha256.as_deref() {
        Some(hash) if hash.len() == 64 && hash.bytes().all(|b| b.is_ascii_hexdigit()) => {
            Ok(Some(hash.to_ascii_lowercase()))
        }
        Some(_) => Err(format!(
            "manifest entry {} carries a malformed sha256",
            role.rel_path
        )),
        None => Err(format!(
            "manifest entry {} carries no sha256",
            role.rel_path
        )),
    }
}

fn unavailable(
    path: Option<String>,
    actual: Option<String>,
    baseline: Option<String>,
    reason: String,
) -> BinaryRecord {
    BinaryRecord {
        path,
        actual_sha256: actual,
        baseline_sha256: baseline,
        verification: "unavailable".into(),
        reason: Some(reason),
    }
}

/// Hash a readable regular file; a missing, unreadable or nonregular file is a reason.
fn hash_regular_file(path: &Path) -> Result<String, String> {
    let metadata =
        std::fs::metadata(path).map_err(|e| format!("cannot stat {}: {e}", path.display()))?;
    if !metadata.is_file() {
        return Err(format!("{} is not a regular file", path.display()));
    }
    evidence::sha256_hex(path)
}

/// Compare a selected file with the role's baseline.
fn compare(
    path: &Path,
    manifest: Result<&EvidenceManifest, &String>,
    role: &ShippedBinary,
) -> BinaryRecord {
    let shown = Some(path.display().to_string());
    let (baseline_hash, baseline_reason) = match baseline(manifest, role) {
        Ok(hash) => (hash, None),
        Err(reason) => (None, Some(reason)),
    };
    let actual = match hash_regular_file(path) {
        Ok(hash) => hash,
        Err(reason) => return unavailable(shown, None, baseline_hash, reason),
    };
    match (baseline_hash, baseline_reason) {
        (Some(expected), _) if expected == actual => BinaryRecord {
            path: shown,
            actual_sha256: Some(actual),
            baseline_sha256: Some(expected),
            verification: "match".into(),
            reason: None,
        },
        (Some(expected), _) => BinaryRecord {
            path: shown,
            actual_sha256: Some(actual),
            baseline_sha256: Some(expected),
            verification: "mismatch".into(),
            reason: Some(format!(
                "selected bytes differ from the manifest baseline for {}",
                role.rel_path
            )),
        },
        (None, reason) => unavailable(
            shown,
            Some(actual),
            None,
            reason.unwrap_or_else(|| "baseline unavailable".into()),
        ),
    }
}

/// The override value for one helper role, read from the parsed request.
enum Override {
    Absent,
    Malformed(String),
    Path(String),
}

fn override_for(request: &Value, key: &str) -> Override {
    match request.get("_test_overrides") {
        None | Some(Value::Null) => Override::Absent,
        Some(Value::Object(map)) => match map.get(key) {
            None | Some(Value::Null) => Override::Absent,
            Some(Value::String(text)) => Override::Path(text.clone()),
            Some(other) => Override::Malformed(format!(
                "_test_overrides.{key} is {}, not a string",
                json_type(other)
            )),
        },
        Some(other) => Override::Malformed(format!(
            "_test_overrides is {}, not an object",
            json_type(other)
        )),
    }
}

fn json_type(value: &Value) -> &'static str {
    match value {
        Value::Null => "null",
        Value::Bool(_) => "a boolean",
        Value::Number(_) => "a number",
        Value::String(_) => "a string",
        Value::Array(_) => "an array",
        Value::Object(_) => "an object",
    }
}

/// The record for a helper role under the override rules.
fn helper_record(
    request: &Value,
    key: &str,
    bundle_helper: Option<&Path>,
    manifest_selected_path: Option<&Path>,
    manifest: Result<&EvidenceManifest, &String>,
    role: &ShippedBinary,
) -> Option<BinaryRecord> {
    match override_for(request, key) {
        Override::Malformed(reason) => Some(unavailable(
            None,
            None,
            baseline(manifest, role).ok().flatten(),
            reason,
        )),
        Override::Absent => match bundle_helper {
            Some(path) if Some(path) == manifest_selected_path => None,
            Some(path) => Some(compare(path, manifest, role)),
            None => Some(unavailable(
                None,
                None,
                baseline(manifest, role).ok().flatten(),
                "no runner bundle was selected".into(),
            )),
        },
        Override::Path(text) => {
            if text.contains('\0') {
                return Some(unavailable(
                    None,
                    None,
                    baseline(manifest, role).ok().flatten(),
                    format!("_test_overrides.{key} contains a NUL byte"),
                ));
            }
            if text.len() > OVERRIDE_PATH_ECHO_BYTES {
                return Some(unavailable(
                    None,
                    None,
                    baseline(manifest, role).ok().flatten(),
                    format!(
                        "_test_overrides.{key} is {} bytes, beyond the {OVERRIDE_PATH_ECHO_BYTES}-byte echo bound",
                        text.len()
                    ),
                ));
            }
            if text.is_empty() {
                return Some(unavailable(
                    Some(text),
                    None,
                    baseline(manifest, role).ok().flatten(),
                    format!("_test_overrides.{key} is empty"),
                ));
            }
            if !text.starts_with('/') {
                return Some(unavailable(
                    Some(text),
                    None,
                    baseline(manifest, role).ok().flatten(),
                    format!(
                        "_test_overrides.{key} is relative; the runner's working directory is unknown to the controller"
                    ),
                ));
            }
            let path = PathBuf::from(&text);
            if Some(path.as_path()) == manifest_selected_path {
                return None;
            }
            Some(compare(&path, manifest, role))
        }
    }
}

impl Binaries {
    /// Every role unavailable with one diagnostic: no runner was selected.
    pub fn unselected(reason: &str) -> Self {
        let record = || unavailable(None, None, None, reason.to_string());
        Binaries {
            service: Some(record()),
            worker: Some(record()),
            validator: Some(record()),
        }
    }

    /// Observe the selected service and helper binaries against the manifest.
    pub fn observe(
        app_root: &Path,
        target: &RunnerTarget,
        request: &Value,
        manifest: Result<&EvidenceManifest, &String>,
    ) -> Self {
        let service_selected = target.executable_path.as_deref();
        let bundle_macos = target
            .bundle_path
            .as_ref()
            .map(|b| b.join("Contents").join("MacOS"));
        let shipped = |role: &ShippedBinary| app_root.join(role.rel_path);
        // A built-in selection whose path is the manifest's uniquely selected,
        // correctly typed entry needs no hash.
        let manifest_entry = |role: &ShippedBinary| -> Option<PathBuf> {
            let manifest = manifest.ok()?;
            evidence::unique_typed_entry(manifest, role.rel_path, role.kind).ok()?;
            Some(shipped(role))
        };
        let service = match service_selected {
            None => Some(unavailable(
                None,
                None,
                baseline(manifest, &SHIPPED_SERVICE).ok().flatten(),
                "no service executable was selected".into(),
            )),
            Some(path) if Some(path.to_path_buf()) == manifest_entry(&SHIPPED_SERVICE) => None,
            Some(path) => Some(compare(path, manifest, &SHIPPED_SERVICE)),
        };
        let worker_selected = manifest_entry(&SHIPPED_WORKER);
        let validator_selected = manifest_entry(&SHIPPED_VALIDATOR);
        let worker_bundle = bundle_macos.as_ref().map(|m| m.join("pw-probe-runner"));
        let validator_bundle = bundle_macos.as_ref().map(|m| m.join("sb_api_validator"));
        Binaries {
            service,
            worker: helper_record(
                request,
                "worker_executable_path",
                worker_bundle.as_deref(),
                worker_selected.as_deref(),
                manifest,
                &SHIPPED_WORKER,
            ),
            validator: helper_record(
                request,
                "validator_executable_path",
                validator_bundle.as_deref(),
                validator_selected.as_deref(),
                manifest,
                &SHIPPED_VALIDATOR,
            ),
        }
    }
}

impl Specimen {
    /// The dossier skeleton before anything was collected: every key present,
    /// every fact unavailable.
    pub fn unavailable(request_path: Option<String>, host: HostFacts, reason: &str) -> Self {
        Specimen {
            request_path,
            policy: PolicyDossier {
                augmentation: Augmentation::not_applicable(),
                imports: Imports::not_applicable(None),
            },
            host,
            runner_provenance: None,
            app_provenance: None,
            binaries: Binaries::unselected(reason),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::evidence::{EVIDENCE_SCHEMA_VERSION, EvidenceEntry};
    use crate::runner_manager::RunnerKind;
    use crate::runner_select::{
        RunnerConnectionKind, parse_runner_selector_value, resolve_runner_target,
        runner_provenance_from_target,
    };
    use serde_json::json;
    use std::fs;
    use std::os::unix::fs::PermissionsExt;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn temp_root(tag: &str) -> PathBuf {
        let stamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        std::env::temp_dir().join(format!("pw-dossier-{tag}-{}-{stamp}", std::process::id()))
    }

    fn write(path: &Path, bytes: &[u8]) {
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(path, bytes).unwrap();
    }

    const ROLES: [&ShippedBinary; 3] = [&SHIPPED_SERVICE, &SHIPPED_WORKER, &SHIPPED_VALIDATOR];

    /// A synthetic app root: the three shipped binaries as small distinct
    /// files, an app-level validator decoy, and no Info.plist anywhere.
    fn synthetic_app(tag: &str) -> PathBuf {
        let root = temp_root(tag);
        for role in ROLES {
            write(
                &root.join(role.rel_path),
                format!("binary at {}", role.rel_path).as_bytes(),
            );
        }
        write(
            &root.join("Contents/MacOS/sb_api_validator"),
            b"app-level diagnostic validator copy",
        );
        root
    }

    fn entry(
        id: &str,
        kind: &str,
        bundle_id: Option<&str>,
        rel_path: &str,
        sha256: Option<String>,
    ) -> EvidenceEntry {
        EvidenceEntry {
            id: id.to_string(),
            kind: kind.to_string(),
            bundle_id: bundle_id.map(str::to_string),
            rel_path: rel_path.to_string(),
            sha256,
            lc_uuid: Some("00000000-0000-0000-0000-000000000000".into()),
            entitlements: Some(json!({"com.apple.security.app-sandbox": true})),
            entitlements_error: None,
        }
    }

    fn hash_of(root: &Path, role: &ShippedBinary) -> String {
        evidence::sha256_hex(&root.join(role.rel_path)).unwrap()
    }

    /// The shipped manifest plus decoys: the app-level validator, and entries
    /// whose id and bundle_id equal the service's at other paths.
    fn manifest_for(root: &Path) -> EvidenceManifest {
        EvidenceManifest {
            schema_version: EVIDENCE_SCHEMA_VERSION,
            entries: vec![
                entry(
                    "com.example.pw.PWRunner",
                    "xpc-service",
                    Some("com.example.pw.PWRunner"),
                    "Contents/MacOS/PWRunner-decoy",
                    Some("f".repeat(64)),
                ),
                entry(
                    "com.example.pw.PWRunner",
                    "xpc-service",
                    Some("com.example.pw.PWRunner"),
                    SHIPPED_SERVICE.rel_path,
                    Some(hash_of(root, &SHIPPED_SERVICE)),
                ),
                entry(
                    "pw-probe-runner",
                    "xpc-embedded-helper",
                    None,
                    SHIPPED_WORKER.rel_path,
                    Some(hash_of(root, &SHIPPED_WORKER)),
                ),
                entry(
                    "sb_api_validator",
                    "xpc-embedded-helper",
                    None,
                    SHIPPED_VALIDATOR.rel_path,
                    Some(hash_of(root, &SHIPPED_VALIDATOR)),
                ),
                entry(
                    "sb_api_validator",
                    "helper",
                    None,
                    "Contents/MacOS/sb_api_validator",
                    Some(
                        evidence::sha256_hex(&root.join("Contents/MacOS/sb_api_validator"))
                            .unwrap(),
                    ),
                ),
            ],
            notes: None,
        }
    }

    fn builtin(root: &Path, manifest: &EvidenceManifest) -> RunnerTarget {
        let selector = parse_runner_selector_value(&json!({})).unwrap();
        match resolve_runner_target(root, Ok(manifest), &selector) {
            Ok(target) => target,
            Err(error) => panic!("built-in selection failed: {error}"),
        }
    }

    fn selection_error(root: &Path, manifest: Result<&EvidenceManifest, &String>) -> String {
        let selector = parse_runner_selector_value(&json!({})).unwrap();
        match resolve_runner_target(root, manifest, &selector) {
            Ok(_) => panic!("selection succeeded"),
            Err(error) => error,
        }
    }

    /// An external runner bundle laid out like a BYOXPC copy.
    fn byoxpc(
        tag: &str,
        service: &[u8],
        worker: Option<&[u8]>,
        validator: Option<&[u8]>,
    ) -> (PathBuf, RunnerTarget) {
        let bundle = temp_root(tag).join("Runner.xpc");
        let macos = bundle.join("Contents").join("MacOS");
        write(&macos.join("PWRunner"), service);
        if let Some(bytes) = worker {
            write(&macos.join("pw-probe-runner"), bytes);
        }
        if let Some(bytes) = validator {
            write(&macos.join("sb_api_validator"), bytes);
        }
        let target = RunnerTarget {
            kind: RunnerKind::Byoxpc,
            connection: RunnerConnectionKind::MachService { privileged: false },
            service_name: "com.example.runner".into(),
            bundle_id: Some("com.example.runner".into()),
            bundle_path: Some(bundle.clone()),
            executable_path: Some(macos.join("PWRunner")),
            registry_id: Some("runner-ext".into()),
            signature: None,
            entitlements: None,
        };
        (bundle, target)
    }

    fn record(binaries: &Binaries, role: &str) -> BinaryRecord {
        match role {
            "service" => binaries.service.clone(),
            "worker" => binaries.worker.clone(),
            _ => binaries.validator.clone(),
        }
        .unwrap_or_else(|| panic!("{role}: expected a record"))
    }

    fn running_as_root() -> bool {
        unsafe { libc::geteuid() == 0 }
    }

    #[test]
    fn builtin_run_hashes_nothing_and_reports_null_records() {
        let root = synthetic_app("builtin");
        let manifest = manifest_for(&root);
        let target = builtin(&root, &manifest);
        // Unreadable binaries would surface as records if anything hashed them.
        if !running_as_root() {
            for role in ROLES {
                fs::set_permissions(root.join(role.rel_path), fs::Permissions::from_mode(0o000))
                    .unwrap();
            }
        }
        let request =
            json!({"policy": {"format": "sbpl", "sbpl_source": "(version 1)\n"}, "probe_plan": []});
        let before = request.clone();
        let binaries = Binaries::observe(&root, &target, &request, Ok(&manifest));
        assert_eq!(
            binaries,
            Binaries {
                service: None,
                worker: None,
                validator: None
            }
        );
        assert_eq!(request, before);
        for role in ROLES {
            fs::set_permissions(root.join(role.rel_path), fs::Permissions::from_mode(0o644))
                .unwrap();
        }
        fs::remove_dir_all(&root).unwrap();
    }

    #[test]
    fn builtin_selection_reads_the_manifest_entry_and_no_info_plist() {
        let root = synthetic_app("select");
        let manifest = manifest_for(&root);
        let target = builtin(&root, &manifest);
        assert_eq!(target.service_name, "com.example.pw.PWRunner");
        assert_eq!(target.bundle_id.as_deref(), Some("com.example.pw.PWRunner"));
        assert_eq!(
            target.executable_path,
            Some(root.join(SHIPPED_SERVICE.rel_path))
        );
        assert_eq!(
            target.bundle_path,
            Some(root.join("Contents/XPCServices/PWRunner.xpc"))
        );
        assert!(matches!(
            target.connection,
            RunnerConnectionKind::XpcService
        ));
        assert!(target.entitlements.is_some());
        let provenance = serde_json::to_value(runner_provenance_from_target(&target)).unwrap();
        assert_eq!(provenance["runner_kind"], "standard");
        assert_eq!(provenance["runner_service_name"], "com.example.pw.PWRunner");
        assert_eq!(
            provenance["runner_executable_path"],
            root.join(SHIPPED_SERVICE.rel_path).display().to_string()
        );
        assert!(provenance["runner_registry_id"].is_null());
        // Neither hash availability nor helper-entry failures gate selection.
        let mut relaxed = manifest_for(&root);
        relaxed
            .entries
            .retain(|e| e.rel_path != SHIPPED_WORKER.rel_path);
        relaxed.entries.iter_mut().for_each(|e| e.sha256 = None);
        builtin(&root, &relaxed);
        fs::remove_dir_all(&root).unwrap();
    }

    #[test]
    fn builtin_selection_failures_name_the_manifest_or_the_entry() {
        let root = synthetic_app("refuse");
        let missing = format!(
            "failed to read manifest {}: No such file or directory (os error 2)",
            evidence::manifest_path_from_app_root(&root).display()
        );
        let error = selection_error(&root, Err(&missing));
        assert!(
            error.contains("built-in runner unavailable") && error.contains("manifest.json"),
            "{error}"
        );
        // Decoys at other paths never substitute for the fixed service path.
        let mut decoys = manifest_for(&root);
        decoys
            .entries
            .retain(|e| e.rel_path != SHIPPED_SERVICE.rel_path);
        let error = selection_error(&root, Ok(&decoys));
        assert!(
            error.contains("no entry at") && error.contains(SHIPPED_SERVICE.rel_path),
            "{error}"
        );
        let mut duplicate = manifest_for(&root);
        duplicate.entries.push(entry(
            "dup",
            "xpc-service",
            Some("dup"),
            SHIPPED_SERVICE.rel_path,
            None,
        ));
        let error = selection_error(&root, Ok(&duplicate));
        assert!(error.contains("more than one entry"), "{error}");
        let mut wrong_kind = manifest_for(&root);
        wrong_kind
            .entries
            .iter_mut()
            .filter(|e| e.rel_path == SHIPPED_SERVICE.rel_path)
            .for_each(|e| e.kind = "helper".into());
        let error = selection_error(&root, Ok(&wrong_kind));
        assert!(error.contains("has kind"), "{error}");
        for (label, bundle_id) in [
            ("missing", None),
            ("empty", Some("")),
            ("nul", Some("com.example\0pw")),
        ] {
            let mut manifest = manifest_for(&root);
            manifest
                .entries
                .iter_mut()
                .filter(|e| e.rel_path == SHIPPED_SERVICE.rel_path)
                .for_each(|e| e.bundle_id = bundle_id.map(str::to_string));
            let error = selection_error(&root, Ok(&manifest));
            assert!(error.contains("bundle_id"), "{label}: {error}");
        }
        fs::remove_dir_all(&root).unwrap();
    }

    #[test]
    fn helper_entry_failures_affect_only_their_baseline() {
        let root = synthetic_app("helpers");
        let request = json!({});
        let worker_hash = hash_of(&root, &SHIPPED_WORKER);
        let validator_hash = hash_of(&root, &SHIPPED_VALIDATOR);
        let cases: Vec<(&str, Box<dyn Fn(&mut EvidenceManifest)>, &str, &str)> = vec![
            (
                "missing worker entry",
                Box::new(|m| m.entries.retain(|e| e.rel_path != SHIPPED_WORKER.rel_path)),
                "worker",
                "no entry at",
            ),
            (
                "duplicate validator entry",
                Box::new(|m| {
                    m.entries.push(entry(
                        "dup",
                        "xpc-embedded-helper",
                        None,
                        SHIPPED_VALIDATOR.rel_path,
                        None,
                    ))
                }),
                "validator",
                "more than one entry",
            ),
            (
                "wrong worker kind",
                Box::new(|m| {
                    m.entries
                        .iter_mut()
                        .filter(|e| e.rel_path == SHIPPED_WORKER.rel_path)
                        .for_each(|e| e.kind = "xpc-service".into())
                }),
                "worker",
                "has kind",
            ),
        ];
        for (label, mutate, role, reason) in cases {
            let mut manifest = manifest_for(&root);
            mutate(&mut manifest);
            let target = builtin(&root, &manifest);
            let binaries = Binaries::observe(&root, &target, &request, Ok(&manifest));
            assert!(binaries.service.is_none(), "{label}");
            let (affected, other) = if role == "worker" {
                (binaries.worker.clone(), binaries.validator.clone())
            } else {
                (binaries.validator.clone(), binaries.worker.clone())
            };
            assert!(
                other.is_none(),
                "{label}: the other helper keeps its null record"
            );
            let affected = affected.unwrap_or_else(|| panic!("{label}: {role} needs a record"));
            let shipped = if role == "worker" {
                &SHIPPED_WORKER
            } else {
                &SHIPPED_VALIDATOR
            };
            let actual = if role == "worker" {
                &worker_hash
            } else {
                &validator_hash
            };
            assert_eq!(
                affected.path.as_deref(),
                Some(root.join(shipped.rel_path).to_str().unwrap()),
                "{label}"
            );
            assert_eq!(
                affected.actual_sha256.as_deref(),
                Some(actual.as_str()),
                "{label}"
            );
            assert!(affected.baseline_sha256.is_none(), "{label}");
            assert_eq!(affected.verification, "unavailable", "{label}");
            assert!(
                affected.reason.as_deref().unwrap_or("").contains(reason),
                "{label}: {:?}",
                affected.reason
            );
        }
        fs::remove_dir_all(&root).unwrap();
    }

    #[test]
    fn byoxpc_copies_are_compared_with_the_shipped_baselines() {
        let root = synthetic_app("byoxpc");
        let manifest = manifest_for(&root);
        let service_bytes = fs::read(root.join(SHIPPED_SERVICE.rel_path)).unwrap();
        let (bundle, target) = byoxpc("byoxpc", &service_bytes, Some(b"a different worker"), None);
        let request = json!({});
        let binaries = Binaries::observe(&root, &target, &request, Ok(&manifest));
        let service = record(&binaries, "service");
        assert_eq!(service.verification, "match");
        assert!(service.reason.is_none());
        assert_eq!(
            service.path.as_deref(),
            bundle.join("Contents/MacOS/PWRunner").to_str()
        );
        assert_eq!(service.actual_sha256, service.baseline_sha256);
        assert_eq!(
            service.baseline_sha256.as_deref(),
            Some(hash_of(&root, &SHIPPED_SERVICE).as_str())
        );
        let worker = record(&binaries, "worker");
        assert_eq!(worker.verification, "mismatch");
        assert!(
            worker
                .reason
                .as_deref()
                .unwrap()
                .contains("differ from the manifest baseline")
        );
        assert_eq!(
            worker.baseline_sha256.as_deref(),
            Some(hash_of(&root, &SHIPPED_WORKER).as_str())
        );
        assert_ne!(worker.actual_sha256, worker.baseline_sha256);
        let validator = record(&binaries, "validator");
        assert_eq!(validator.verification, "unavailable");
        assert!(validator.actual_sha256.is_none());
        assert_eq!(
            validator.baseline_sha256.as_deref(),
            Some(hash_of(&root, &SHIPPED_VALIDATOR).as_str())
        );
        assert!(validator.reason.as_deref().unwrap().contains("cannot stat"));
        // A malformed or absent manifest hash makes the comparison unavailable,
        // with the selected file's hash retained.
        for (label, sha) in [("malformed", Some("not-hex".to_string())), ("absent", None)] {
            let mut damaged = manifest_for(&root);
            damaged
                .entries
                .iter_mut()
                .filter(|e| e.rel_path == SHIPPED_SERVICE.rel_path)
                .for_each(|e| e.sha256 = sha.clone());
            let binaries = Binaries::observe(&root, &target, &request, Ok(&damaged));
            let service = record(&binaries, "service");
            assert_eq!(service.verification, "unavailable", "{label}");
            assert!(service.actual_sha256.is_some(), "{label}");
            assert!(service.baseline_sha256.is_none(), "{label}");
            assert!(
                service.reason.as_deref().unwrap().contains("sha256"),
                "{label}: {:?}",
                service.reason
            );
        }
        fs::remove_dir_all(&root).unwrap();
        fs::remove_dir_all(bundle.parent().unwrap()).unwrap();
    }

    #[test]
    fn unavailable_manifest_keeps_paths_and_hashes_without_baselines() {
        let root = synthetic_app("nomanifest");
        let (bundle, target) = byoxpc(
            "nomanifest",
            b"service",
            Some(b"worker"),
            Some(b"validator"),
        );
        let missing = "failed to read manifest /x/manifest.json: No such file".to_string();
        let binaries = Binaries::observe(&root, &target, &json!({}), Err(&missing));
        for role in ["service", "worker", "validator"] {
            let record = record(&binaries, role);
            assert_eq!(record.verification, "unavailable", "{role}");
            assert!(
                record
                    .path
                    .as_deref()
                    .unwrap()
                    .starts_with(bundle.to_str().unwrap()),
                "{role}"
            );
            assert!(record.actual_sha256.is_some(), "{role}");
            assert!(record.baseline_sha256.is_none(), "{role}");
            assert!(
                record
                    .reason
                    .as_deref()
                    .unwrap()
                    .contains("app evidence manifest unavailable"),
                "{role}"
            );
        }
        fs::remove_dir_all(&root).unwrap();
        fs::remove_dir_all(bundle.parent().unwrap()).unwrap();
    }

    #[test]
    fn override_observations_follow_the_table_without_changing_the_request() {
        let root = synthetic_app("overrides");
        let manifest = manifest_for(&root);
        let target = builtin(&root, &manifest);
        let worker_baseline = hash_of(&root, &SHIPPED_WORKER);
        let scratch = temp_root("override-files");
        let same = scratch.join("same-worker");
        write(
            &same,
            &fs::read(root.join(SHIPPED_WORKER.rel_path)).unwrap(),
        );
        let different = scratch.join("other-worker");
        write(&different, b"not the shipped worker");
        let directory = scratch.join("a-directory");
        fs::create_dir_all(&directory).unwrap();
        let unreadable = scratch.join("unreadable");
        write(&unreadable, b"secret");
        fs::set_permissions(&unreadable, fs::Permissions::from_mode(0o000)).unwrap();
        let shipped_worker = root.join(SHIPPED_WORKER.rel_path).display().to_string();
        let overlong = format!("/{}", "x".repeat(OVERRIDE_PATH_ECHO_BYTES));
        let longest = format!("/{}", "x".repeat(OVERRIDE_PATH_ECHO_BYTES - 1));
        assert_eq!(overlong.len(), OVERRIDE_PATH_ECHO_BYTES + 1);

        struct Case {
            label: &'static str,
            value: Value,
            path: Option<String>,
            hashed: bool,
            verification: &'static str,
            reason: &'static str,
        }
        let cases = vec![
            Case {
                label: "number",
                value: json!(7),
                path: None,
                hashed: false,
                verification: "unavailable",
                reason: "not a string",
            },
            Case {
                label: "array",
                value: json!(["/x"]),
                path: None,
                hashed: false,
                verification: "unavailable",
                reason: "not a string",
            },
            Case {
                label: "nul",
                value: json!("/tmp/w\u{0}x"),
                path: None,
                hashed: false,
                verification: "unavailable",
                reason: "NUL byte",
            },
            Case {
                label: "overlong",
                value: json!(overlong),
                path: None,
                hashed: false,
                verification: "unavailable",
                reason: "echo bound",
            },
            Case {
                label: "empty",
                value: json!(""),
                path: Some(String::new()),
                hashed: false,
                verification: "unavailable",
                reason: "is empty",
            },
            Case {
                label: "relative",
                value: json!("relative/worker"),
                path: Some("relative/worker".into()),
                hashed: false,
                verification: "unavailable",
                reason: "relative",
            },
            Case {
                label: "missing",
                value: json!("/nonexistent/pw-worker"),
                path: Some("/nonexistent/pw-worker".into()),
                hashed: false,
                verification: "unavailable",
                reason: "cannot stat",
            },
            Case {
                label: "longest",
                value: json!(longest.clone()),
                path: Some(longest.clone()),
                hashed: false,
                verification: "unavailable",
                reason: "cannot stat",
            },
            Case {
                label: "directory",
                value: json!(directory.to_str().unwrap()),
                path: Some(directory.display().to_string()),
                hashed: false,
                verification: "unavailable",
                reason: "not a regular file",
            },
            Case {
                label: "same bytes",
                value: json!(same.to_str().unwrap()),
                path: Some(same.display().to_string()),
                hashed: true,
                verification: "match",
                reason: "",
            },
            Case {
                label: "different bytes",
                value: json!(different.to_str().unwrap()),
                path: Some(different.display().to_string()),
                hashed: true,
                verification: "mismatch",
                reason: "differ from the manifest baseline",
            },
        ];
        for case in cases {
            let request =
                json!({"policy": {}, "_test_overrides": {"worker_executable_path": case.value}});
            let before = request.clone();
            let binaries = Binaries::observe(&root, &target, &request, Ok(&manifest));
            assert_eq!(request, before, "{}", case.label);
            assert!(
                binaries.service.is_none() && binaries.validator.is_none(),
                "{}",
                case.label
            );
            let worker = record(&binaries, "worker");
            assert_eq!(worker.path, case.path, "{}", case.label);
            assert_eq!(
                worker.actual_sha256.is_some(),
                case.hashed,
                "{}",
                case.label
            );
            assert_eq!(worker.verification, case.verification, "{}", case.label);
            assert_eq!(
                worker.baseline_sha256.as_deref(),
                Some(worker_baseline.as_str()),
                "{}",
                case.label
            );
            match case.reason {
                "" => assert!(worker.reason.is_none(), "{}", case.label),
                text => assert!(
                    worker.reason.as_deref().unwrap_or("").contains(text),
                    "{}: {:?}",
                    case.label,
                    worker.reason
                ),
            }
        }
        if !running_as_root() {
            let request = json!({"_test_overrides": {"validator_executable_path": unreadable.to_str().unwrap()}});
            let binaries = Binaries::observe(&root, &target, &request, Ok(&manifest));
            let validator = record(&binaries, "validator");
            assert!(binaries.worker.is_none());
            assert_eq!(validator.path.as_deref(), unreadable.to_str());
            assert!(validator.actual_sha256.is_none());
            assert_eq!(validator.verification, "unavailable");
            assert!(
                validator
                    .reason
                    .as_deref()
                    .unwrap()
                    .contains("failed to open"),
                "{:?}",
                validator.reason
            );
        }
        // The manifest's own path for the role needs no comparison.
        let request = json!({"_test_overrides": {"worker_executable_path": shipped_worker, "validator_executable_path": null}});
        let binaries = Binaries::observe(&root, &target, &request, Ok(&manifest));
        assert_eq!(
            binaries,
            Binaries {
                service: None,
                worker: None,
                validator: None
            }
        );
        // A malformed container affects both helper roles; the service is untouched.
        for container in [json!(5), json!("x"), json!([])] {
            let request = json!({"_test_overrides": container});
            let binaries = Binaries::observe(&root, &target, &request, Ok(&manifest));
            assert!(binaries.service.is_none());
            for role in ["worker", "validator"] {
                let record = record(&binaries, role);
                assert!(record.path.is_none() && record.actual_sha256.is_none());
                assert_eq!(record.verification, "unavailable");
                assert!(record.reason.as_deref().unwrap().contains("not an object"));
                assert!(
                    record.baseline_sha256.is_some(),
                    "{role}: the baseline is retained"
                );
            }
        }
        // An override under an unavailable manifest still hashes the selected file.
        let missing = "failed to read manifest /x/manifest.json: No such file".to_string();
        let request =
            json!({"_test_overrides": {"worker_executable_path": different.to_str().unwrap()}});
        let binaries = Binaries::observe(&root, &target, &request, Err(&missing));
        let worker = record(&binaries, "worker");
        assert!(worker.actual_sha256.is_some() && worker.baseline_sha256.is_none());
        assert_eq!(worker.verification, "unavailable");
        assert!(
            worker
                .reason
                .as_deref()
                .unwrap()
                .contains("manifest unavailable")
        );
        fs::set_permissions(&unreadable, fs::Permissions::from_mode(0o644)).unwrap();
        fs::remove_dir_all(&root).unwrap();
        fs::remove_dir_all(&scratch).unwrap();
    }

    #[test]
    fn specimen_skeleton_serializes_every_documented_key() {
        let specimen = Specimen::unavailable(None, HostFacts::collect(), "controlled");
        let wire = serde_json::to_value(&specimen).unwrap();
        let keys = |v: &Value| v.as_object().unwrap().keys().cloned().collect::<Vec<_>>();
        assert_eq!(
            keys(&wire),
            [
                "app_provenance",
                "binaries",
                "host",
                "policy",
                "request_path",
                "runner_provenance"
            ]
        );
        assert_eq!(keys(&wire["policy"]), ["augmentation", "imports"]);
        assert_eq!(
            keys(&wire["host"]),
            ["arch", "kernel_release", "macos_build", "macos_version"]
        );
        assert_eq!(keys(&wire["binaries"]), ["service", "validator", "worker"]);
        assert_eq!(
            keys(&wire["binaries"]["worker"]),
            [
                "actual_sha256",
                "baseline_sha256",
                "path",
                "reason",
                "verification"
            ]
        );
        assert!(
            wire["request_path"].is_null()
                && wire["runner_provenance"].is_null()
                && wire["app_provenance"].is_null()
        );
        let provenance = AppProvenance {
            evidence_manifest_path: "/m.json".into(),
            evidence_verify: None,
        };
        assert_eq!(
            keys(&serde_json::to_value(&provenance).unwrap()),
            ["evidence_manifest_path", "evidence_verify"]
        );
    }

    #[test]
    fn host_facts_are_the_four_sysctl_strings() {
        let host = HostFacts::collect();
        assert_eq!(
            host.macos_version,
            host_facts::sysctl_string("kern.osproductversion")
        );
        assert_eq!(
            host.macos_build,
            host_facts::sysctl_string("kern.osversion")
        );
        assert_eq!(
            host.kernel_release,
            host_facts::sysctl_string("kern.osrelease")
        );
        assert_eq!(host.arch, host_facts::sysctl_string("hw.machine"));
        for value in [
            &host.macos_version,
            &host.macos_build,
            &host.kernel_release,
            &host.arch,
        ] {
            assert!(
                value.as_deref().map_or(false, |v| !v.is_empty()),
                "{host:?}"
            );
        }
    }

    #[test]
    fn augmentation_records_hash_only_bytes_that_existed() {
        let source = "(version 1)\n";
        let hash = sbpl_imports::sha256_hex(source);
        let plain = Augmentation::not_requested(Some(source));
        assert_eq!(
            (
                plain.status.as_str(),
                plain.original_sha256.as_deref(),
                plain.applied_sha256.as_deref()
            ),
            ("not_requested", Some(hash.as_str()), Some(hash.as_str()))
        );
        assert!(plain.applied.is_empty() && plain.error.is_none());
        let record = PolicyAugmentation {
            applied: vec!["a".into()],
            original_sha256: hash.clone(),
            applied_sha256: "b".repeat(64),
        };
        let applied = Augmentation::applied(&record, false);
        assert_eq!(applied.status, "applied");
        assert!(applied.original_sha256.is_none());
        assert_eq!(
            applied.applied_sha256.as_deref(),
            Some("b".repeat(64).as_str())
        );
        assert_eq!(
            Augmentation::applied(&record, true)
                .original_sha256
                .as_deref(),
            Some(hash.as_str())
        );
        let failed = Augmentation::failed(Some(source), "refused".into());
        assert_eq!(
            (
                failed.status.as_str(),
                failed.original_sha256.as_deref(),
                failed.applied_sha256,
                failed.error.as_deref()
            ),
            ("failed", Some(hash.as_str()), None, Some("refused"))
        );
        assert!(failed.applied.is_empty());
        let none = Augmentation::not_applicable();
        assert_eq!(none.status, "not_applicable");
        assert!(
            none.original_sha256.is_none() && none.applied_sha256.is_none() && none.error.is_none()
        );
    }

    #[test]
    fn import_scan_statuses_never_report_an_unscanned_closure_as_complete() {
        let complete = Imports::scan("(version 1)\n(allow default)\n");
        assert_eq!(complete.status, "complete");
        assert!(complete.closure_sha256.is_some() && complete.records.is_empty());
        assert!(
            complete.cycle.is_none() && complete.exceeded.is_none() && complete.failure.is_none()
        );
        let nonliteral = Imports::scan("(define (m x) (import x))\n(m \"system.sb\")\n");
        assert_eq!(nonliteral.status, "incomplete");
        assert!(nonliteral.closure_sha256.is_some());
        assert!(
            nonliteral
                .failure
                .as_deref()
                .unwrap()
                .contains("nonliteral")
        );
        let unresolved = Imports::scan("(import \"pw-no-such-profile-0000.sb\")\n");
        assert_eq!(unresolved.status, "incomplete");
        assert_eq!(unresolved.records.len(), 1);
        assert!(unresolved.records[0].error.is_some());
        assert!(unresolved.closure_sha256.is_some());
        let oversized = Imports::scan(&"x".repeat(MAX_SBPL_SOURCE_BYTES + 1));
        assert_eq!(oversized.status, "failed");
        assert!(oversized.closure_sha256.is_none() && oversized.records.is_empty());
        assert!(oversized.failure.as_deref().unwrap().contains("at most"));
        let skipped = Imports::not_applicable(Some("augmentation_failed".into()));
        assert_eq!(skipped.status, "not_applicable");
        assert_eq!(skipped.failure.as_deref(), Some("augmentation_failed"));
        assert!(skipped.closure_sha256.is_none());
    }
}
