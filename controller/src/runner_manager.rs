//! External runner registry and launchd wiring.
//!
//! The registry is a small JSON file under the user's Library directory. We
//! also generate launchd plists so Mach services can be registered in a user or
//! system domain.

use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use std::io::{Read, Write};
use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

pub const RUNNER_REGISTRY_SCHEMA_VERSION: u32 = 1;
pub const RUNNER_PROTOCOL_VERSION: u32 = 1;
/// After `launchctl bootout` returns, launchd can still list the job for a
/// moment. `runner remove` re-reads the service every poll interval until it
/// is absent or this nominal allowance is spent, then judges completion from
/// the last observation (docs/limits.json: `runner_remove_teardown_wait`).
const TEARDOWN_WAIT_MS: u64 = 1_000;
const TEARDOWN_POLL_INTERVAL_MS: u64 = 50;
/// `ThrottleInterval` written into every generated launchd plist. The host
/// exits after each specimen and launchd respawns the job at most once per
/// interval; its default of ten seconds made every consecutive request to
/// one installed runner wait for the remainder. Chosen by measurement
/// (docs/limits.json: `byoxpc_throttle_interval`).
const BYOXPC_THROTTLE_INTERVAL_SECONDS: u64 = 1;

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum RunnerKind {
    Standard,
    // The aliases accept legacy on-disk registry entries carrying
    // `kind: "machme"` or `kind: "debuggable"` and coerce them to
    // Byoxpc on load so upgraded integrators don't have a stranded
    // registry. New input that uses either string is rejected by
    // RunnerKind::parse.
    #[serde(alias = "machme", alias = "debuggable")]
    Byoxpc,
}

impl RunnerKind {
    pub fn parse(value: &str) -> Option<Self> {
        match value {
            "standard" => Some(RunnerKind::Standard),
            "byoxpc" => Some(RunnerKind::Byoxpc),
            _ => None,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            RunnerKind::Standard => "standard",
            RunnerKind::Byoxpc => "byoxpc",
        }
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum RunnerScope {
    User,
    System,
}

impl RunnerScope {
    pub fn parse(value: &str) -> Option<Self> {
        match value {
            "user" => Some(RunnerScope::User),
            "system" => Some(RunnerScope::System),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunnerSignature {
    pub team_id: Option<String>,
    pub identity: Option<String>,
    pub cdhash: Option<String>,
    pub valid: bool,
    pub adhoc: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunnerEntitlements {
    pub raw_plist: Option<String>,
    /// Every key the plist names, whatever its value.
    pub keys: Vec<String>,
    /// The keys whose value is the boolean `true`: the entitlements the kernel
    /// treats as held. A key present with any other value is not granted.
    #[serde(default)]
    pub granted: Vec<String>,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Copy, Default, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RunnerState {
    Pending,
    #[default]
    Installed,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunnerOwnership {
    pub plist_path: String,
    pub launchd_domain: String,
    pub owner_uid: u32,
    pub plist_sha256: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PendingCleanup {
    #[serde(flatten)]
    pub runner: RunnerRecord,
    pub cleanup_started_at_unix_ms: u64,
    #[serde(default)]
    pub observations: Vec<Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunnerRecord {
    #[serde(default)]
    pub state: RunnerState,
    #[serde(default)]
    pub ownership: Option<RunnerOwnership>,
    pub id: String,
    pub service_name: String,
    pub bundle_path: String,
    pub executable_path: String,
    pub bundle_id: Option<String>,
    pub scope: RunnerScope,
    pub protocol_version: u32,
    pub signature: RunnerSignature,
    pub entitlements: RunnerEntitlements,
    pub installed_at_unix_ms: u64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub kind: Option<RunnerKind>,
    /// The embedded worker's and validator's signatures and entitlements, read
    /// back after installation. Absent in records written before the
    /// installer signed and read back the helpers.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub worker_signature: Option<RunnerSignature>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub worker_entitlements: Option<RunnerEntitlements>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub validator_signature: Option<RunnerSignature>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub validator_entitlements: Option<RunnerEntitlements>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunnerRegistry {
    pub schema_version: u32,
    pub runners: Vec<RunnerRecord>,
    #[serde(default)]
    pub pending_cleanup: Vec<PendingCleanup>,
}

pub fn runner_registry_path() -> Result<PathBuf, String> {
    // Ops/test seam: point PW at an alternate registry without touching
    // $HOME. Mirrors the PW_VERIFY_EVIDENCE override in run_flow.rs. The
    // resolve path also accepts an explicit override argument (see
    // runner_select::resolve_runner_target_with_registry) so unit tests
    // need not mutate this process-global env var.
    if let Ok(path) = std::env::var("PW_RUNNER_REGISTRY") {
        if !path.is_empty() {
            return Ok(PathBuf::from(path));
        }
    }
    let home = std::env::var("HOME")
        .map_err(|_| "HOME is not set; cannot locate runner registry".to_string())?;
    Ok(Path::new(&home)
        .join("Library")
        .join("Application Support")
        .join("PolicyWitness")
        .join("runners.json"))
}

pub fn launchd_plist_path(service_name: &str, scope: RunnerScope) -> Result<PathBuf, String> {
    let base = match scope {
        RunnerScope::User => {
            let home = std::env::var("HOME")
                .map_err(|_| "HOME is not set; cannot locate LaunchAgents".to_string())?;
            Path::new(&home).join("Library").join("LaunchAgents")
        }
        RunnerScope::System => Path::new("/Library/LaunchDaemons").to_path_buf(),
    };
    Ok(base.join(format!("{service_name}.plist")))
}

pub fn load_registry(path: &Path) -> Result<RunnerRegistry, String> {
    if !path.exists() {
        return Ok(RunnerRegistry {
            schema_version: RUNNER_REGISTRY_SCHEMA_VERSION,
            runners: Vec::new(),
            pending_cleanup: Vec::new(),
        });
    }
    let text =
        fs::read_to_string(path).map_err(|e| format!("failed to read {}: {e}", path.display()))?;
    let registry: RunnerRegistry = serde_json::from_str(&text)
        .map_err(|e| format!("failed to parse {}: {e}", path.display()))?;
    if registry.schema_version != RUNNER_REGISTRY_SCHEMA_VERSION {
        return Err(format!(
            "unsupported runner registry schema_version {} (expected {})",
            registry.schema_version, RUNNER_REGISTRY_SCHEMA_VERSION
        ));
    }
    Ok(registry)
}

/// The lock inode lives beside the registry and is never renamed or unlinked.
/// Atomic replacement of the JSON file must not replace the held lock itself.
pub fn lock_registry(path: &Path) -> Result<fs::File, String> {
    if let Some(parent) = path.parent().filter(|p| !p.as_os_str().is_empty()) {
        fs::create_dir_all(parent).map_err(|e| format!("create registry directory: {e}"))?;
    }
    let lock_path = path.with_file_name(format!(
        "{}.lock",
        path.file_name()
            .ok_or("registry has no filename")?
            .to_string_lossy()
    ));
    if fs::symlink_metadata(&lock_path).is_ok_and(|m| !m.is_file()) {
        return Err("registry lock is not a regular file".to_string());
    }
    let file = fs::OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(false)
        .mode(0o600)
        .open(&lock_path)
        .map_err(|e| format!("open registry lock {}: {e}", lock_path.display()))?;
    file.try_lock()
        .map_err(|e| format!("runner registry busy or lock unavailable: {e}"))?;
    Ok(file)
}

pub fn save_registry(path: &Path, registry: &RunnerRegistry) -> Result<(), String> {
    if let Some(parent) = path.parent().filter(|p| !p.as_os_str().is_empty()) {
        fs::create_dir_all(parent)
            .map_err(|e| format!("failed to create {}: {e}", parent.display()))?;
    }
    let text = serde_json::to_vec_pretty(registry)
        .map_err(|e| format!("failed to encode registry JSON: {e}"))?;
    let temporary = path.with_file_name(format!(
        ".{}.{}.tmp",
        path.file_name()
            .ok_or("registry has no filename")?
            .to_string_lossy(),
        random_id()?
    ));
    let result = (|| -> std::io::Result<()> {
        let mut file = fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .mode(0o600)
            .open(&temporary)?;
        file.write_all(&text)?;
        file.sync_all()?;
        fs::rename(&temporary, path)
    })();
    if result.is_err() {
        let _ = fs::remove_file(&temporary);
    }
    result.map_err(|e| format!("failed to atomically save {}: {e}", path.display()))
}

/// Persist recovery identity before the caller performs installation actions.
/// Tests supply observed action boundaries; the CLI closure uses real tools.
pub fn install_record(
    path: &Path,
    registry: &mut RunnerRegistry,
    mut record: RunnerRecord,
    install: impl FnOnce() -> Result<(), String>,
) -> Result<RunnerRecord, String> {
    record.state = RunnerState::Pending;
    registry.runners.push(record.clone());
    save_registry(path, registry)?;
    let completed = (|| -> Result<(), String> {
        install()?;
        record.state = RunnerState::Installed;
        *registry.runners.last_mut().expect("pending record") = record.clone();
        save_registry(path, registry)
    })();
    completed.map_err(|error| {
        format!(
            "{error}; pending runner {} ({}) retained in {}; retry runner remove --service-name {}",
            record.id,
            record.service_name,
            path.display(),
            record.service_name
        )
    })?;
    Ok(record)
}

pub fn conflicting_record<'a>(
    registry: &'a RunnerRegistry,
    service: &str,
    bundle: &str,
    executable: &str,
) -> Option<&'a RunnerRecord> {
    registry
        .runners
        .iter()
        .chain(registry.pending_cleanup.iter().map(|c| &c.runner))
        .find(|r| {
            r.service_name == service || r.bundle_path == bundle || r.executable_path == executable
        })
}

pub fn content_hash(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

pub fn random_id() -> Result<String, String> {
    let mut buf = [0u8; 16];
    let mut file =
        fs::File::open("/dev/urandom").map_err(|e| format!("failed to open /dev/urandom: {e}"))?;
    file.read_exact(&mut buf)
        .map_err(|e| format!("failed to read /dev/urandom: {e}"))?;
    let mut out = String::from("runner-");
    for b in buf {
        out.push_str(&format!("{:02x}", b));
    }
    Ok(out)
}

pub fn entitlements_from_json(value: &Value) -> RunnerEntitlements {
    let (keys, granted) = match value {
        Value::Object(map) => {
            let mut keys: Vec<String> = map.keys().cloned().collect();
            keys.sort();
            let mut granted: Vec<String> = map
                .iter()
                .filter(|(_, value)| matches!(value, Value::Bool(true)))
                .map(|(key, _)| key.clone())
                .collect();
            granted.sort();
            (keys, granted)
        }
        _ => (Vec::new(), Vec::new()),
    };
    RunnerEntitlements {
        raw_plist: None,
        keys,
        granted,
        error: None,
    }
}

fn plist_escape(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
}

pub fn build_launchd_plist(
    service_name: &str,
    executable_path: &Path,
    env: Option<&BTreeMap<String, String>>,
    kind: RunnerKind,
) -> String {
    let mut env_block = String::new();
    if let Some(env) = env {
        if !env.is_empty() {
            env_block.push_str("  <key>EnvironmentVariables</key>\n  <dict>\n");
            for (key, value) in env {
                env_block.push_str(&format!(
                    "    <key>{}</key>\n    <string>{}</string>\n",
                    plist_escape(key),
                    plist_escape(value)
                ));
            }
            env_block.push_str("  </dict>\n");
        }
    }
    let mut args = vec![executable_path.display().to_string()];
    if matches!(kind, RunnerKind::Byoxpc) {
        // External runners use a Mach service name for NSXPC connections.
        args.push("--mach-service".to_string());
        args.push(service_name.to_string());
    }
    let args_block: String = args
        .iter()
        .map(|arg| format!("    <string>{}</string>\n", plist_escape(arg)))
        .collect();
    format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{service_name}</string>
  <key>ProgramArguments</key>
  <array>
{args_block}  </array>
  <key>MachServices</key>
  <dict>
    <key>{service_name}</key>
    <true/>
  </dict>
{env_block}  <key>RunAtLoad</key>
  <true/>
  <key>ThrottleInterval</key>
  <integer>{throttle}</integer>
</dict>
</plist>
"#,
        throttle = BYOXPC_THROTTLE_INTERVAL_SECONDS,
    )
}

pub fn write_launchd_plist(path: &Path, content: &str) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|e| format!("failed to create {}: {e}", parent.display()))?;
    }
    let mut file = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o644)
        .open(path)
        .map_err(|e| format!("failed to create {}: {e}", path.display()))?;
    file.write_all(content.as_bytes())
        .map_err(|e| format!("failed to write {}: {e}", path.display()))
}

fn plutil_json_from_bytes(bytes: &[u8]) -> Result<Value, String> {
    let mut child = Command::new("/usr/bin/plutil")
        .args(["-convert", "json", "-o", "-", "-"])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("failed to run plutil: {e}"))?;
    if let Some(mut stdin) = child.stdin.take() {
        stdin
            .write_all(bytes)
            .map_err(|e| format!("failed to write plutil stdin: {e}"))?;
    }
    let out = child
        .wait_with_output()
        .map_err(|e| format!("failed to read plutil output: {e}"))?;
    if !out.status.success() {
        let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
        return Err(format!("plutil failed: {stderr}"));
    }
    serde_json::from_slice(&out.stdout).map_err(|e| format!("plutil JSON parse failed: {e}"))
}

pub fn entitlements_from_codesign(target: &Path) -> RunnerEntitlements {
    let out = Command::new("/usr/bin/codesign")
        .args([
            "-d",
            "--entitlements",
            ":-",
            target.to_string_lossy().as_ref(),
        ])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output();
    let out = match out {
        Ok(out) => out,
        Err(err) => {
            return RunnerEntitlements {
                raw_plist: None,
                keys: Vec::new(),
                granted: Vec::new(),
                error: Some(format!("failed to run codesign: {err}")),
            };
        }
    };
    if !out.status.success() {
        let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
        return RunnerEntitlements {
            raw_plist: None,
            keys: Vec::new(),
            granted: Vec::new(),
            error: Some(format!("codesign failed: {stderr}")),
        };
    }
    // codesign writes nothing for a signature that carries no entitlements.
    if out.stdout.iter().all(u8::is_ascii_whitespace) {
        return RunnerEntitlements {
            raw_plist: None,
            keys: Vec::new(),
            granted: Vec::new(),
            error: None,
        };
    }
    match plutil_json_from_bytes(&out.stdout) {
        Ok(value) => {
            let mut ent = entitlements_from_json(&value);
            ent.raw_plist = String::from_utf8(out.stdout).ok();
            ent
        }
        Err(err) => RunnerEntitlements {
            raw_plist: String::from_utf8(out.stdout).ok(),
            keys: Vec::new(),
            granted: Vec::new(),
            error: Some(err),
        },
    }
}

pub fn codesign_metadata(target: &Path) -> Result<RunnerSignature, String> {
    let out = Command::new("/usr/bin/codesign")
        .args(["-dv", "--verbose=4", target.to_string_lossy().as_ref()])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run codesign: {e}"))?;
    let stderr = String::from_utf8_lossy(&out.stderr);
    if !out.status.success() {
        return Err(format!("codesign metadata failed: {}", stderr.trim()));
    }
    let mut team_id = None;
    let mut identity = None;
    let mut cdhash = None;
    let mut adhoc = false;
    for line in stderr.lines() {
        if let Some(rest) = line.strip_prefix("Authority=") {
            if identity.is_none() {
                identity = Some(rest.trim().to_string());
            }
        } else if let Some(rest) = line.strip_prefix("TeamIdentifier=") {
            team_id = Some(rest.trim().to_string());
        } else if let Some(rest) = line.strip_prefix("CDHash=") {
            cdhash = Some(rest.trim().to_string());
        } else if line.contains("Signature=adhoc") {
            adhoc = true;
        }
    }
    Ok(RunnerSignature {
        team_id,
        identity,
        cdhash,
        valid: true,
        adhoc,
    })
}

/// Recursive, strict verification: nested code is checked as well as the
/// enclosing seal, so a changed embedded worker fails here even when the
/// bundle's own seal still verifies. Used at installation and by validate.
pub fn codesign_verify(target: &Path) -> Result<(), String> {
    let out = Command::new("/usr/bin/codesign")
        .args([
            "--verify",
            "--deep",
            "--strict",
            "--verbose=2",
            target.to_string_lossy().as_ref(),
        ])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run codesign: {e}"))?;
    if out.status.success() {
        return Ok(());
    }
    let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
    Err(format!("codesign verify failed: {stderr}"))
}

/// Sign an XPC bundle for installation: the embedded worker with the identity
/// and the supplied entitlements, the embedded validator with the identity
/// alone, then the enclosing bundle with the identity and the entitlements.
/// Nested code is signed before the enclosing seal records its hashes; the
/// order is part of the contract and `sign` is injectable so a test pins it
/// without an identity.
pub fn sign_install_tree(
    bundle: &Path,
    identity: &str,
    entitlements: Option<&Path>,
    sign: &mut dyn FnMut(&Path, &str, Option<&Path>) -> Result<(), String>,
) -> Result<(), String> {
    let worker = bundle.join(crate::app_layout::BUNDLE_WORKER_REL);
    let validator = bundle.join(crate::app_layout::BUNDLE_VALIDATOR_REL);
    for (role, path) in [("worker", &worker), ("validator", &validator)] {
        if !path.is_file() {
            return Err(format!(
                "bundle has no embedded {role} at {}; external runners must carry the complete copy",
                path.display()
            ));
        }
    }
    sign(&worker, identity, entitlements)?;
    sign(&validator, identity, None)?;
    sign(bundle, identity, entitlements)
}

/// One validation failure: the record it concerns and the binary that failed
/// (`bundle` for the recursive check of the enclosing seal, otherwise `host`,
/// `worker` or `validator` for that binary's own verification or read-back).
#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct ValidateFailure {
    pub runner_id: String,
    pub service_name: String,
    pub binary: String,
    pub error: String,
}

fn unreadable_signature() -> RunnerSignature {
    RunnerSignature {
        team_id: None,
        identity: None,
        cdhash: None,
        valid: false,
        adhoc: false,
    }
}

/// Re-check one registry record against disk: the bundle recursively
/// (`verify_bundle`), then each of the host, the worker and the validator
/// on its own (`verify_binary`), re-reading every signature and
/// entitlement set. The record's host `signature.valid` reports the
/// bundle's recursive check; each helper's `valid` reports its own. The
/// three operations are injectable so the classification is pinned
/// without codesign.
pub fn validate_record(
    record: &mut RunnerRecord,
    verify_bundle: &dyn Fn(&Path) -> Result<(), String>,
    verify_binary: &dyn Fn(&Path) -> Result<(), String>,
    read: &dyn Fn(&Path) -> Result<(RunnerSignature, RunnerEntitlements), String>,
) -> Vec<ValidateFailure> {
    let mut failures = Vec::new();
    let mut fail = |binary: &str, error: String| {
        failures.push(ValidateFailure {
            runner_id: record.id.clone(),
            service_name: record.service_name.clone(),
            binary: binary.to_string(),
            error,
        });
    };
    let bundle = PathBuf::from(&record.bundle_path);
    let bundle_ok = match verify_bundle(&bundle) {
        Ok(()) => true,
        Err(error) => {
            fail("bundle", error);
            false
        }
    };
    let host = PathBuf::from(&record.executable_path);
    let worker = bundle.join(crate::app_layout::BUNDLE_WORKER_REL);
    let validator = bundle.join(crate::app_layout::BUNDLE_VALIDATOR_REL);
    let mut observe = |role: &str, path: &Path| -> (RunnerSignature, RunnerEntitlements) {
        let own = verify_binary(path);
        let (mut signature, entitlements) = match read(path) {
            Ok(read) => read,
            Err(error) => {
                fail(role, error);
                return (
                    unreadable_signature(),
                    RunnerEntitlements {
                        raw_plist: None,
                        keys: Vec::new(),
                        granted: Vec::new(),
                        error: Some(format!("{role} read-back failed")),
                    },
                );
            }
        };
        if let Err(error) = own {
            fail(role, error);
            signature.valid = false;
        }
        (signature, entitlements)
    };
    let (mut host_signature, host_entitlements) = observe("host", &host);
    host_signature.valid = host_signature.valid && bundle_ok;
    let (worker_signature, worker_entitlements) = observe("worker", &worker);
    let (validator_signature, validator_entitlements) = observe("validator", &validator);
    record.signature = host_signature;
    record.entitlements = host_entitlements;
    record.worker_signature = Some(worker_signature);
    record.worker_entitlements = Some(worker_entitlements);
    record.validator_signature = Some(validator_signature);
    record.validator_entitlements = Some(validator_entitlements);
    failures
}

/// A binary's signature metadata and entitlements as codesign reads them
/// back. The metadata read is required; an entitlement read failure is
/// recorded inside the entitlements.
pub fn read_back(target: &Path) -> Result<(RunnerSignature, RunnerEntitlements), String> {
    let signature = codesign_metadata(target)
        .map_err(|e| format!("read-back of {} failed: {e}", target.display()))?;
    Ok((signature, entitlements_from_codesign(target)))
}

/// Non-recursive strict verification of one binary's own code. A bundle's
/// main executable resolves to its bundle's seal, so this reports the
/// seal without repeating the recursive verdict over the nested helpers.
pub fn codesign_verify_binary(target: &Path) -> Result<(), String> {
    let out = Command::new("/usr/bin/codesign")
        .args([
            "--verify",
            "--strict",
            "--verbose=2",
            target.to_string_lossy().as_ref(),
        ])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run codesign: {e}"))?;
    if out.status.success() {
        return Ok(());
    }
    let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
    Err(format!("codesign verify failed: {stderr}"))
}

pub fn codesign_sign(
    target: &Path,
    identity: &str,
    entitlements: Option<&Path>,
) -> Result<(), String> {
    let mut cmd = Command::new("/usr/bin/codesign");
    cmd.args(["--force", "--options", "runtime", "-s", identity]);
    // Apple's RFC 3161 timestamp service rejects ad-hoc signatures; only request
    // a trusted timestamp when the caller actually has a signing identity.
    if identity != "-" {
        cmd.arg("--timestamp");
    }
    if let Some(entitlements) = entitlements {
        cmd.args(["--entitlements", entitlements.to_string_lossy().as_ref()]);
    }
    let out = cmd
        .arg(target.to_string_lossy().as_ref())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run codesign: {e}"))?;
    if out.status.success() {
        return Ok(());
    }
    let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
    Err(format!("codesign sign failed: {stderr}"))
}

pub fn current_uid_string() -> Result<String, String> {
    let out = Command::new("/usr/bin/id")
        .args(["-u"])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run id -u: {e}"))?;
    if !out.status.success() {
        let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
        return Err(format!("id -u failed: {stderr}"));
    }
    let uid = String::from_utf8_lossy(&out.stdout).trim().to_string();
    if uid.is_empty() || !uid.chars().all(|c| c.is_ascii_digit()) {
        return Err("id -u returned a non-numeric uid".to_string());
    }
    Ok(uid)
}

pub fn launchctl_target(scope: RunnerScope) -> Result<String, String> {
    match scope {
        // launchctl expects user services under the per-user GUI domain.
        RunnerScope::User => Ok(format!("gui/{}", current_uid_string()?)),
        RunnerScope::System => Ok("system".to_string()),
    }
}

pub fn launchctl_bootstrap(scope: RunnerScope, plist_path: &Path) -> Result<(), String> {
    let target = launchctl_target(scope)?;
    let out = Command::new("/bin/launchctl")
        .args(["bootstrap", &target, plist_path.to_string_lossy().as_ref()])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run launchctl: {e}"))?;
    if out.status.success() {
        return Ok(());
    }
    let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
    Err(format!("launchctl bootstrap failed: {stderr}"))
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Presence {
    Present,
    Absent,
    Unknown,
}

#[derive(Debug, Clone, Copy, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Ownership {
    Owned,
    Unowned,
    Ambiguous,
    Unknown,
}

#[derive(Debug, Clone, Serialize)]
pub struct ServiceObservation {
    pub presence: Presence,
    pub executable_path: Option<String>,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct PlistObservation {
    pub presence: Presence,
    pub config: Option<Value>,
    pub sha256: Option<String>,
    pub owner_uid: Option<u32>,
    pub regular: bool,
    pub error: Option<String>,
}

fn classify_service_output(
    success: bool,
    stdout: &str,
    stderr: &str,
    service: &str,
) -> ServiceObservation {
    if success {
        let programs: Vec<_> = stdout
            .lines()
            .filter_map(|line| line.trim().strip_prefix("program = "))
            .collect();
        return ServiceObservation {
            presence: Presence::Present,
            executable_path: (programs.len() == 1).then(|| programs[0].to_string()),
            error: None,
        };
    }
    let absent = stderr.contains(&format!("Could not find service \"{service}\""));
    ServiceObservation {
        presence: if absent {
            Presence::Absent
        } else {
            Presence::Unknown
        },
        executable_path: None,
        error: (!absent).then(|| format!("launchctl print: {}", stderr.trim())),
    }
}

pub fn inspect_service(domain: &str, service: &str) -> ServiceObservation {
    match Command::new("/bin/launchctl")
        .args(["print", &format!("{domain}/{service}")])
        .output()
    {
        Ok(out) => classify_service_output(
            out.status.success(),
            &String::from_utf8_lossy(&out.stdout),
            &String::from_utf8_lossy(&out.stderr),
            service,
        ),
        Err(error) => ServiceObservation {
            presence: Presence::Unknown,
            executable_path: None,
            error: Some(error.to_string()),
        },
    }
}

pub fn inspect_plist(path: &Path) -> PlistObservation {
    let mut result = PlistObservation {
        presence: Presence::Unknown,
        config: None,
        sha256: None,
        owner_uid: None,
        regular: false,
        error: None,
    };
    match fs::symlink_metadata(path) {
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            result.presence = Presence::Absent;
            return result;
        }
        Err(error) => {
            result.error = Some(error.to_string());
            return result;
        }
        Ok(meta) => {
            result.presence = Presence::Present;
            result.owner_uid = Some(meta.uid());
            result.regular = meta.is_file();
        }
    }
    if !result.regular {
        result.error = Some("plist is not a regular file".into());
        return result;
    }
    match fs::read(path) {
        Ok(bytes) => {
            result.sha256 = Some(content_hash(&bytes));
            match plutil_json_from_bytes(&bytes) {
                Ok(value) => result.config = Some(value),
                Err(error) => result.error = Some(error),
            }
        }
        Err(error) => {
            result.presence = Presence::Unknown;
            result.error = Some(error.to_string());
        }
    }
    result
}

pub fn record_location(record: &RunnerRecord) -> Result<(PathBuf, String), String> {
    if record.service_name.is_empty()
        || !record
            .service_name
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || "._-".contains(c))
    {
        return Err("invalid recorded service name".into());
    }
    let domain = launchctl_target(record.scope)?;
    if let Some(ownership) = &record.ownership {
        let plist = PathBuf::from(&ownership.plist_path);
        let uid: u32 = current_uid_string()?.parse().map_err(|_| "invalid uid")?;
        let expected_parent = match record.scope {
            RunnerScope::User => "LaunchAgents",
            RunnerScope::System => "LaunchDaemons",
        };
        if ownership.owner_uid != uid
            || ownership.launchd_domain != domain
            || !plist.is_absolute()
            || plist
                .components()
                .any(|p| matches!(p, std::path::Component::ParentDir))
            || plist.file_name().and_then(|n| n.to_str())
                != Some(&format!("{}.plist", record.service_name))
            || plist
                .parent()
                .and_then(|p| p.file_name())
                .and_then(|n| n.to_str())
                != Some(expected_parent)
            || Path::new(&record.executable_path).parent()
                != Some(&Path::new(&record.bundle_path).join("Contents/MacOS"))
        {
            return Err(
                "recorded cleanup ownership is inconsistent with this user, scope or paths".into(),
            );
        }
        // Refuse redirected parents even if the final plist happens to be absent.
        for parent in plist.ancestors().skip(1) {
            match fs::symlink_metadata(parent) {
                Ok(meta) if meta.file_type().is_symlink() => {
                    return Err("recorded plist parent is a symlink".into());
                }
                Err(error) if error.kind() != std::io::ErrorKind::NotFound => {
                    return Err(error.to_string());
                }
                _ => (),
            }
        }
        Ok((plist, domain))
    } else {
        Ok((
            launchd_plist_path(&record.service_name, record.scope)?,
            domain,
        ))
    }
}

pub fn plist_ownership(record: &RunnerRecord, observation: &PlistObservation) -> Ownership {
    if observation.presence == Presence::Unknown {
        return Ownership::Unknown;
    }
    if observation.presence == Presence::Absent {
        return Ownership::Ambiguous;
    }
    if !observation.regular {
        return Ownership::Unowned;
    }
    let Some(config) = &observation.config else {
        return Ownership::Unknown;
    };
    let expected_args = serde_json::json!([
        record.executable_path,
        "--mach-service",
        record.service_name
    ]);
    let expected_services = serde_json::json!({ &record.service_name: true });
    if config.get("Label").and_then(Value::as_str) != Some(&record.service_name)
        || config.get("ProgramArguments") != Some(&expected_args)
        || config.get("MachServices") != Some(&expected_services)
        || config
            .pointer("/EnvironmentVariables/XPC_SERVICE_PATH")
            .and_then(Value::as_str)
            != Some(&record.bundle_path)
    {
        return Ownership::Unowned;
    }
    if let Some(owned) = &record.ownership {
        if observation.owner_uid != Some(owned.owner_uid)
            || observation.sha256.as_ref() != Some(&owned.plist_sha256)
        {
            return Ownership::Unowned;
        }
    }
    Ownership::Owned
}

pub fn service_ownership(record: &RunnerRecord, observation: &ServiceObservation) -> Ownership {
    match observation.presence {
        Presence::Unknown => Ownership::Unknown,
        Presence::Absent => Ownership::Ambiguous,
        Presence::Present => match observation.executable_path.as_deref() {
            Some(path) if path == record.executable_path => Ownership::Owned,
            Some(_) => Ownership::Unowned,
            None => Ownership::Ambiguous,
        },
    }
}

fn cleanup_complete(service: &ServiceObservation, plist: &PlistObservation) -> bool {
    service.presence == Presence::Absent && plist.presence == Presence::Absent
}

fn bootout_service(domain: &str, service: &str) -> Result<(), String> {
    let out = Command::new("/bin/launchctl")
        .args(["bootout", &format!("{domain}/{service}")])
        .output()
        .map_err(|e| format!("launchctl bootout: {e}"))?;
    if out.status.success() {
        Ok(())
    } else {
        Err(format!(
            "launchctl bootout: {}",
            String::from_utf8_lossy(&out.stderr).trim()
        ))
    }
}

#[derive(Serialize)]
pub struct CleanupReport {
    runner_id: String,
    service_name: String,
    plist_path: String,
    booted_out: bool,
    plist_removed: bool,
    cleanup_retained: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    retained_record: Option<PendingCleanup>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    warnings: Vec<String>,
}

/// Narrow system observations/actions for the removal transaction. Production
/// always supplies NativeCleanup; unit controls supply independent observations.
pub trait CleanupSystem {
    fn location(&mut self, record: &RunnerRecord) -> Result<(PathBuf, String), String>;
    fn service(&mut self, domain: &str, name: &str) -> ServiceObservation;
    fn plist(&mut self, path: &Path) -> PlistObservation;
    fn bootout(&mut self, domain: &str, name: &str) -> Result<(), String>;
    fn remove_plist(&mut self, path: &Path) -> std::io::Result<()>;
    /// Pause between service re-reads while launchd tears a job down.
    fn wait(&mut self, interval: std::time::Duration);
}

pub struct NativeCleanup;
impl CleanupSystem for NativeCleanup {
    fn location(&mut self, record: &RunnerRecord) -> Result<(PathBuf, String), String> {
        record_location(record)
    }
    fn service(&mut self, domain: &str, name: &str) -> ServiceObservation {
        inspect_service(domain, name)
    }
    fn plist(&mut self, path: &Path) -> PlistObservation {
        inspect_plist(path)
    }
    fn bootout(&mut self, domain: &str, name: &str) -> Result<(), String> {
        bootout_service(domain, name)
    }
    fn remove_plist(&mut self, path: &Path) -> std::io::Result<()> {
        fs::remove_file(path)
    }
    fn wait(&mut self, interval: std::time::Duration) {
        std::thread::sleep(interval)
    }
}

/// Read the service after this call's bootout, waiting out launchd's
/// asynchronous teardown: while the job is still listed, re-read every
/// `TEARDOWN_POLL_INTERVAL_MS` until `TEARDOWN_WAIT_MS` of nominal waiting is
/// spent. Without a bootout here there is nothing to wait for. The record
/// says how many reads were made and how long was waited; the last
/// observation is the one judged.
fn service_after_bootout(
    system: &mut impl CleanupSystem,
    domain: &str,
    name: &str,
    booted_out: bool,
) -> (ServiceObservation, Value) {
    let mut observation = system.service(domain, name);
    let mut reads = 1u64;
    let mut waited_ms = 0u64;
    while booted_out && observation.presence == Presence::Present && waited_ms < TEARDOWN_WAIT_MS {
        system.wait(std::time::Duration::from_millis(TEARDOWN_POLL_INTERVAL_MS));
        waited_ms += TEARDOWN_POLL_INTERVAL_MS;
        observation = system.service(domain, name);
        reads += 1;
    }
    let record = json!({
        "reads": reads, "waited_ms": waited_ms,
        "poll_interval_ms": TEARDOWN_POLL_INTERVAL_MS, "budget_ms": TEARDOWN_WAIT_MS,
    });
    (observation, record)
}

pub fn remove_record(
    registry_path: &Path,
    registry: &mut RunnerRegistry,
    runner_id: Option<&str>,
    service_name: Option<&str>,
    skip_bootout: bool,
    system: &mut impl CleanupSystem,
) -> Result<Option<CleanupReport>, String> {
    let matches = |record: &RunnerRecord| {
        runner_id.map_or_else(
            || service_name == Some(record.service_name.as_str()),
            |id| id == record.id,
        )
    };
    if let Some(index) = registry.runners.iter().position(&matches) {
        let record = registry.runners.remove(index);
        registry.pending_cleanup.push(PendingCleanup {
            runner: record,
            cleanup_started_at_unix_ms: crate::utils::now_unix_ms(),
            observations: Vec::new(),
        });
        // This must succeed before any launchd or plist action.
        save_registry(registry_path, registry)?;
    }
    let Some(index) = registry
        .pending_cleanup
        .iter()
        .position(|c| matches(&c.runner))
    else {
        return Ok(None);
    };
    let mut cleanup = registry.pending_cleanup[index].clone();
    let record = &cleanup.runner;
    let mut warnings = Vec::new();
    let mut booted_out = false;
    let mut plist_removed = false;
    let mut complete = false;
    let mut plist_path_text = record
        .ownership
        .as_ref()
        .map(|o| o.plist_path.clone())
        .unwrap_or_default();
    match system.location(record) {
        Err(error) => warnings.push(error),
        Ok((plist_path, domain)) => {
            plist_path_text = plist_path.display().to_string();
            let service = system.service(&domain, &record.service_name);
            let plist = system.plist(&plist_path);
            let service_owner = service_ownership(record, &service);
            let plist_owner = plist_ownership(record, &plist);
            cleanup
                .observations
                .push(json!({"phase":"before", "service":service, "plist":plist,
                "service_ownership":service_owner, "plist_ownership":plist_owner}));
            if service.presence != Presence::Absent && !skip_bootout {
                if service_owner == Ownership::Owned {
                    match system.bootout(&domain, &record.service_name) {
                        Ok(()) => booted_out = true,
                        Err(error) => warnings.push(error),
                    }
                } else {
                    warnings.push(format!(
                        "service ownership is {service_owner:?}; bootout refused"
                    ));
                }
            }
            if plist.presence != Presence::Absent {
                if plist_owner == Ownership::Owned {
                    // Reinspect immediately before unlinking; stale observations are not authority.
                    let current = system.plist(&plist_path);
                    if plist_ownership(record, &current) == Ownership::Owned {
                        match system.remove_plist(&plist_path) {
                            Ok(()) => plist_removed = true,
                            Err(error) => warnings.push(format!(
                                "failed to remove plist {}: {error}",
                                plist_path.display()
                            )),
                        }
                    } else {
                        warnings.push("plist ownership changed; removal refused".into());
                    }
                } else {
                    warnings.push(format!(
                        "plist ownership is {plist_owner:?}; removal refused"
                    ));
                }
            }
            let (service_after, teardown) =
                service_after_bootout(system, &domain, &record.service_name, booted_out);
            let plist_after = system.plist(&plist_path);
            complete = cleanup_complete(&service_after, &plist_after) && warnings.is_empty();
            cleanup.observations.push(json!({
                "phase":"after", "service":service_after, "plist":plist_after,
                "teardown_wait":teardown,
            }));
            if !complete {
                warnings
                    .push("service/plist absence is not confirmed; cleanup record retained".into());
            }
        }
    }
    registry.pending_cleanup[index] = cleanup.clone();
    if complete {
        registry.pending_cleanup.remove(index);
    }
    if let Err(error) = save_registry(registry_path, registry) {
        complete = false;
        warnings.push(format!(
            "cleanup persistence failed; prior recovery record retained: {error}"
        ));
    }
    let data = CleanupReport {
        runner_id: cleanup.runner.id.clone(),
        service_name: cleanup.runner.service_name.clone(),
        plist_path: plist_path_text,
        booted_out,
        plist_removed,
        cleanup_retained: !complete,
        retained_record: (!complete).then_some(cleanup),
        warnings,
    };
    Ok(Some(data))
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn false_valued_key_does_not_satisfy_a_requirement() {
        // The kernel grants a boolean entitlement only when its value is true.
        // A plist that names the key with `false` denies it: the read-back
        // records the key but does not grant it, and the selection gate
        // (`enforce_required_entitlements` in runner_select) consults `granted`.
        let key = "com.apple.security.cs.allow-jit".to_string();
        let ent = entitlements_from_json(&json!({"com.apple.security.cs.allow-jit": false}));
        assert_eq!(ent.keys, vec![key.clone()]);
        assert!(
            ent.granted.is_empty(),
            "a required key present with value false must be refused"
        );
        // Only the boolean true grants; strings and numbers do not.
        for value in [json!("true"), json!(1), json!([true]), json!(null)] {
            let ent = entitlements_from_json(&json!({"com.apple.security.cs.allow-jit": value}));
            assert!(ent.granted.is_empty(), "{value}");
        }
        let ent = entitlements_from_json(&json!({"com.apple.security.cs.allow-jit": true}));
        assert_eq!(ent.granted, vec![key.clone()]);
        // A record written before values were recorded grants nothing until
        // it is re-read: `granted` defaults to empty.
        let old: RunnerEntitlements =
            serde_json::from_value(json!({"raw_plist": null, "keys": [key], "error": null}))
                .unwrap();
        assert!(old.granted.is_empty());
    }

    #[test]
    fn install_signing_signs_helpers_before_the_bundle() {
        // The worker takes the entitlements, the validator the identity
        // alone, and the enclosing bundle is sealed last so it records the
        // helpers' new hashes. Pinned with a recording signer; no codesign.
        let root = std::env::temp_dir().join(format!(
            "pw-sign-order-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let bundle = root.join("Runner.xpc");
        let macos = bundle.join("Contents/MacOS");
        fs::create_dir_all(&macos).unwrap();
        for name in ["PWRunner", "pw-probe-runner", "sb_api_validator"] {
            fs::write(macos.join(name), name).unwrap();
        }
        let plist = root.join("entitlements.plist");
        fs::write(&plist, "<plist/>").unwrap();
        let mut calls: Vec<(PathBuf, String, Option<PathBuf>)> = Vec::new();
        sign_install_tree(
            &bundle,
            "Developer ID",
            Some(&plist),
            &mut |target, identity, ent| {
                calls.push((
                    target.to_path_buf(),
                    identity.to_string(),
                    ent.map(Path::to_path_buf),
                ));
                Ok(())
            },
        )
        .unwrap();
        assert_eq!(
            calls,
            vec![
                (
                    macos.join("pw-probe-runner"),
                    "Developer ID".to_string(),
                    Some(plist.clone())
                ),
                (
                    macos.join("sb_api_validator"),
                    "Developer ID".to_string(),
                    None
                ),
                (
                    bundle.clone(),
                    "Developer ID".to_string(),
                    Some(plist.clone())
                ),
            ]
        );
        // A failing helper signature stops before the bundle is sealed.
        let mut sealed = Vec::new();
        let err = sign_install_tree(&bundle, "-", None, &mut |target, _, _| {
            sealed.push(target.to_path_buf());
            if target.ends_with("sb_api_validator") {
                Err("controlled".into())
            } else {
                Ok(())
            }
        })
        .unwrap_err();
        assert_eq!(err, "controlled");
        assert_eq!(
            sealed,
            vec![
                macos.join("pw-probe-runner"),
                macos.join("sb_api_validator")
            ]
        );
        // An incomplete copy is refused before any signing.
        fs::remove_file(macos.join("sb_api_validator")).unwrap();
        let mut touched = 0;
        let err = sign_install_tree(&bundle, "-", None, &mut |_, _, _| {
            touched += 1;
            Ok(())
        })
        .unwrap_err();
        assert!(err.contains("no embedded validator"), "{err}");
        assert_eq!(touched, 0);
        fs::remove_dir_all(&root).unwrap();
    }

    #[test]
    fn validation_reports_the_bundle_and_each_binary_that_fails() {
        let mut record: RunnerRecord = serde_json::from_value(json!({
            "id": "runner-v", "service_name": "com.example.v", "bundle_path": "/v/Runner.xpc",
            "executable_path": "/v/Runner.xpc/Contents/MacOS/PWRunner", "bundle_id": "com.example.v",
            "scope": "user", "protocol_version": RUNNER_PROTOCOL_VERSION,
            "signature": {"team_id": null, "identity": null, "cdhash": null, "valid": true, "adhoc": true},
            "entitlements": {"raw_plist": null, "keys": [], "error": null},
            "installed_at_unix_ms": 0, "kind": "byoxpc"
        }))
        .unwrap();
        let good = |path: &Path| {
            Ok((
                RunnerSignature {
                    team_id: Some("TEAM".into()),
                    identity: Some(path.display().to_string()),
                    cdhash: None,
                    valid: true,
                    adhoc: false,
                },
                entitlements_from_json(&json!({"k": path.ends_with("pw-probe-runner")})),
            ))
        };
        // Intact: nothing fails and every binary's read-back lands on the record.
        let failures = validate_record(&mut record, &|_| Ok(()), &|_| Ok(()), &good);
        assert!(failures.is_empty(), "{failures:?}");
        assert!(record.signature.valid);
        let worker = record.worker_entitlements.as_ref().unwrap();
        assert_eq!(worker.keys, vec!["k".to_string()]);
        assert!(record.validator_signature.as_ref().unwrap().valid);
        // A changed worker: the recursive bundle check and the worker's own
        // check fail; the host and validator still verify individually, the
        // host's recorded validity follows the bundle.
        let changed = |path: &Path| {
            if path.ends_with("Runner.xpc") || path.ends_with("pw-probe-runner") {
                Err(format!("codesign verify failed: {}", path.display()))
            } else {
                Ok(())
            }
        };
        let failures = validate_record(&mut record, &changed, &changed, &good);
        let names: Vec<(&str, &str)> = failures
            .iter()
            .map(|f| (f.binary.as_str(), f.service_name.as_str()))
            .collect();
        assert_eq!(
            names,
            vec![("bundle", "com.example.v"), ("worker", "com.example.v")]
        );
        assert!(failures.iter().all(|f| f.runner_id == "runner-v"));
        assert!(!record.signature.valid, "host validity follows the bundle");
        assert!(!record.worker_signature.as_ref().unwrap().valid);
        assert!(record.validator_signature.as_ref().unwrap().valid);
        // An unreadable helper is its own failure with an unreadable signature.
        let unreadable = |path: &Path| {
            if path.ends_with("sb_api_validator") {
                Err("read-back of validator failed".to_string())
            } else {
                good(path)
            }
        };
        let failures = validate_record(&mut record, &|_| Ok(()), &|_| Ok(()), &unreadable);
        assert_eq!(failures.len(), 1);
        assert_eq!(failures[0].binary, "validator");
        let validator = record.validator_signature.as_ref().unwrap();
        assert!(!validator.valid && validator.team_id.is_none());
        assert_eq!(
            record
                .validator_entitlements
                .as_ref()
                .unwrap()
                .error
                .as_deref(),
            Some("validator read-back failed")
        );
        assert!(record.signature.valid && record.worker_signature.as_ref().unwrap().valid);
    }

    #[test]
    fn registry_records_without_helper_read_backs_still_load() {
        // Records written before the installer read the helpers back carry no
        // worker or validator fields; the additive loader keeps them, and a
        // record that carries them round-trips unchanged.
        let text = serde_json::to_string(&json!({
            "schema_version": RUNNER_REGISTRY_SCHEMA_VERSION,
            "runners": [{
                "id": "runner-old", "service_name": "com.example.old", "bundle_path": "/old/Runner.xpc",
                "executable_path": "/old/Runner.xpc/Contents/MacOS/PWRunner", "bundle_id": "com.example.old",
                "scope": "user", "protocol_version": RUNNER_PROTOCOL_VERSION,
                "signature": {"team_id": null, "identity": null, "cdhash": null, "valid": true, "adhoc": true},
                "entitlements": {"raw_plist": null, "keys": [], "error": null},
                "installed_at_unix_ms": 0, "kind": "byoxpc"
            }]
        }))
        .unwrap();
        let registry: RunnerRegistry = serde_json::from_str(&text).unwrap();
        let record = &registry.runners[0];
        assert!(record.worker_signature.is_none() && record.worker_entitlements.is_none());
        assert!(record.validator_signature.is_none() && record.validator_entitlements.is_none());
        let wire = serde_json::to_value(record).unwrap();
        assert!(
            wire.get("worker_entitlements").is_none(),
            "absent fields stay absent: {wire}"
        );
        let mut carried = record.clone();
        carried.worker_entitlements = Some(entitlements_from_json(&json!({"a": true})));
        let wire = serde_json::to_value(&carried).unwrap();
        assert_eq!(wire["worker_entitlements"]["keys"], json!(["a"]));
        let again: RunnerRecord = serde_json::from_value(wire).unwrap();
        assert_eq!(
            again.worker_entitlements.unwrap().keys,
            vec!["a".to_string()]
        );
    }

    #[test]
    fn legacy_machme_kind_deserializes_as_byoxpc() {
        // Registry entries written by older builds may carry `"kind": "machme"`.
        // The serde alias on RunnerKind::Byoxpc must absorb them silently so
        // upgraded integrators don't have a stranded registry. Re-serializing
        // produces "byoxpc" — that's the documented one-shot migration.
        let kind: RunnerKind =
            serde_json::from_str("\"machme\"").expect("legacy machme should deserialize");
        assert_eq!(kind, RunnerKind::Byoxpc);
        let round_trip = serde_json::to_string(&kind).unwrap();
        assert_eq!(round_trip, "\"byoxpc\"");
    }

    #[test]
    fn legacy_debuggable_kind_deserializes_as_byoxpc() {
        // Registries written by older builds may carry
        // `"kind": "debuggable"`. The serde alias coerces them to
        // Byoxpc so upgraded integrators don't have a stranded
        // registry. Re-serializing produces "byoxpc" — same one-shot
        // migration shape as the machme alias.
        let kind: RunnerKind =
            serde_json::from_str("\"debuggable\"").expect("legacy debuggable should deserialize");
        assert_eq!(kind, RunnerKind::Byoxpc);
        let round_trip = serde_json::to_string(&kind).unwrap();
        assert_eq!(round_trip, "\"byoxpc\"");
    }

    #[test]
    fn caller_facing_parse_rejects_legacy_aliases() {
        // RunnerKind::parse is for CLI / specimen input where we want a
        // clean error pointing at byoxpc, not silent migration.
        assert_eq!(RunnerKind::parse("machme"), None);
        assert_eq!(RunnerKind::parse("debuggable"), None);
        assert_eq!(RunnerKind::parse("byoxpc"), Some(RunnerKind::Byoxpc));
        assert_eq!(RunnerKind::parse("standard"), Some(RunnerKind::Standard));
    }

    #[test]
    fn byoxpc_plist_wires_mach_service_and_machservices() {
        // The BYOXPC LaunchAgent launches the executable directly as a
        // mach-service, so the plist must pass `--mach-service <service>`
        // and register a MachServices entry. The runner host binds
        // NSXPCListener(machServiceName:) off that argument (see
        // PWRunnerListener.pwListenerConfig); this pins the install half so
        // the two can't silently drift apart again.
        let plist = build_launchd_plist(
            "com.x.PWRunner",
            Path::new("/tmp/PWRunner.xpc/Contents/MacOS/PWRunner"),
            None,
            RunnerKind::Byoxpc,
        );
        assert!(
            plist.contains("<string>--mach-service</string>"),
            "byoxpc plist must pass --mach-service; got:\n{plist}"
        );
        assert!(
            plist.contains("<string>com.x.PWRunner</string>"),
            "byoxpc plist must pass the service name as the --mach-service value"
        );
        assert!(
            plist.contains("<key>MachServices</key>"),
            "byoxpc plist must register a MachServices entry"
        );
    }

    #[test]
    fn byoxpc_plist_sets_the_respawn_throttle() {
        // Every generated plist bounds launchd's respawn wait; without the
        // key launchd applies its ten-second default between launches.
        let plist = build_launchd_plist(
            "com.x.PWRunner",
            Path::new("/tmp/PWRunner.xpc/Contents/MacOS/PWRunner"),
            None,
            RunnerKind::Byoxpc,
        );
        let expected = format!(
            "  <key>ThrottleInterval</key>\n  <integer>{BYOXPC_THROTTLE_INTERVAL_SECONDS}</integer>\n"
        );
        assert!(
            plist.contains(&expected),
            "plist must set ThrottleInterval; got:\n{plist}"
        );
        assert_eq!(plist.matches("ThrottleInterval").count(), 1);
    }

    #[test]
    fn documented_throttle_interval() {
        let manifest: serde_json::Value =
            serde_json::from_str(include_str!("../../docs/limits.json")).unwrap();
        let row = manifest["limits"]
            .as_array()
            .unwrap()
            .iter()
            .find(|r| r["id"] == "byoxpc_throttle_interval")
            .expect("limits.json documents the generated plist's ThrottleInterval");
        assert_eq!(
            row["value"].as_u64(),
            Some(BYOXPC_THROTTLE_INTERVAL_SECONDS)
        );
        assert_eq!(row["unit"], "seconds");
    }

    #[test]
    fn standard_plist_has_no_mach_service_arg() {
        // The built-in Standard runner is launched as the embedded `.xpc`
        // bundle (NSXPCListener.service()), so it must NOT receive
        // `--mach-service` — that argument is what routes the host onto the
        // mach-service listener.
        let plist = build_launchd_plist(
            "com.x.PWRunner",
            Path::new("/tmp/PWRunner"),
            None,
            RunnerKind::Standard,
        );
        assert!(
            !plist.contains("--mach-service"),
            "standard plist must not pass --mach-service; got:\n{plist}"
        );
    }
    fn recovery_record() -> RunnerRecord {
        serde_json::from_value(json!({"id":"runner-owned", "service_name":"com.policywitness.test.recovery",
            "bundle_path":"/private/tmp/owned/PWRunner.xpc", "executable_path":"/private/tmp/owned/PWRunner.xpc/Contents/MacOS/PWRunner",
            "bundle_id":"com.policywitness.test.recovery", "scope":"user", "protocol_version":1,
            "signature":{"valid":true,"adhoc":true}, "entitlements":{"keys":[]}, "installed_at_unix_ms":1,
            "kind":"byoxpc"})).unwrap()
    }

    struct RegistryFixture(PathBuf);
    impl RegistryFixture {
        fn new() -> Self {
            let dir = std::env::temp_dir().join(format!("pw-registry-{}", random_id().unwrap()));
            fs::create_dir(&dir).unwrap();
            Self(dir)
        }
        fn path(&self) -> PathBuf {
            self.0.join("runners.json")
        }
        fn writable(&self, writable: bool) {
            use std::os::unix::fs::PermissionsExt;
            fs::set_permissions(
                &self.0,
                fs::Permissions::from_mode(if writable { 0o700 } else { 0o500 }),
            )
            .unwrap();
        }
    }
    impl Drop for RegistryFixture {
        fn drop(&mut self) {
            self.writable(true);
            let _ = fs::remove_dir_all(&self.0);
        }
    }

    #[test]
    fn registry_additive_defaults_preserve_schema_one() {
        let record = recovery_record();
        assert_eq!(record.state, RunnerState::Installed);
        assert!(record.ownership.is_none());
        let registry: RunnerRegistry = serde_json::from_value(
            json!({"schema_version":1,"runners":[record],"future_field":42}),
        )
        .unwrap();
        assert!(registry.pending_cleanup.is_empty());
        assert_eq!(registry.schema_version, 1);
    }

    #[test]
    fn atomic_registry_replace_preserves_old_open_readers_and_failed_write() {
        let fixture = RegistryFixture::new();
        let path = fixture.path();
        let mut registry = load_registry(&path).unwrap();
        save_registry(&path, &registry).unwrap();
        let before = fs::read(&path).unwrap();
        let mut reader = fs::File::open(&path).unwrap();
        registry.runners.push(recovery_record());
        save_registry(&path, &registry).unwrap();
        let mut old = Vec::new();
        reader.read_to_end(&mut old).unwrap();
        assert_eq!(old, before);
        assert_eq!(load_registry(&path).unwrap().runners.len(), 1);
        let current = fs::read(&path).unwrap();
        fixture.writable(false);
        assert!(save_registry(&path, &registry).is_err());
        assert_eq!(fs::read(&path).unwrap(), current);
    }

    #[test]
    fn registry_lock_serializes_writers_and_keeps_its_inode() {
        let fixture = RegistryFixture::new();
        let first = lock_registry(&fixture.path()).unwrap();
        let inode = first.metadata().unwrap().ino();
        assert!(lock_registry(&fixture.path()).is_err());
        assert!(load_registry(&fixture.path()).unwrap().runners.is_empty());
        drop(first);
        let second = lock_registry(&fixture.path()).unwrap();
        assert_eq!(second.metadata().unwrap().ino(), inode);
        // Exercise the blocking standard-library primitive on an uncontended handle.
        second.unlock().unwrap();
        second.lock().unwrap();
    }

    #[test]
    fn pending_cleanup_conflicts_with_service_bundle_and_executable() {
        let mut registry = RunnerRegistry {
            schema_version: 1,
            runners: vec![],
            pending_cleanup: vec![],
        };
        let record = recovery_record();
        registry.pending_cleanup.push(PendingCleanup {
            runner: record.clone(),
            cleanup_started_at_unix_ms: 1,
            observations: vec![],
        });
        assert!(conflicting_record(&registry, &record.service_name, "other", "other").is_some());
        assert!(conflicting_record(&registry, "other", &record.bundle_path, "other").is_some());
        assert!(conflicting_record(&registry, "other", "other", &record.executable_path).is_some());
        assert!(conflicting_record(&registry, "other", "other", "other").is_none());
    }

    #[test]
    fn install_failure_boundaries_preserve_observed_pending_state() {
        use std::cell::Cell;
        for boundary in [
            "initial_save",
            "plist",
            "bootstrap",
            "installed_save",
            "success",
        ] {
            let fixture = RegistryFixture::new();
            let path = fixture.path();
            let plist = fixture.0.join("owned.plist");
            let called = Cell::new(false);
            let bootstrap_observed = Cell::new(false);
            let mut registry = load_registry(&path).unwrap();
            if boundary == "initial_save" {
                fixture.writable(false);
            }
            let result = install_record(&path, &mut registry, recovery_record(), || {
                called.set(true);
                let pending = load_registry(&path)?;
                assert_eq!(pending.runners[0].state, RunnerState::Pending);
                if boundary == "plist" {
                    return Err("controlled plist creation failure".into());
                }
                fs::write(&plist, "owned plist").unwrap();
                if boundary == "bootstrap" {
                    return Err("controlled bootstrap failure after plist creation".into());
                }
                bootstrap_observed.set(true);
                if boundary == "installed_save" {
                    fixture.writable(false);
                }
                Ok(())
            });
            fixture.writable(true);
            assert_eq!(result.is_ok(), boundary == "success", "{boundary}");
            assert_eq!(called.get(), boundary != "initial_save", "{boundary}");
            assert_eq!(
                plist.exists(),
                matches!(boundary, "bootstrap" | "installed_save" | "success")
            );
            assert_eq!(
                bootstrap_observed.get(),
                matches!(boundary, "installed_save" | "success")
            );
            let disk = load_registry(&path).unwrap();
            if boundary == "initial_save" {
                assert!(disk.runners.is_empty());
            } else {
                assert_eq!(
                    disk.runners[0].state,
                    if boundary == "success" {
                        RunnerState::Installed
                    } else {
                        RunnerState::Pending
                    }
                );
                if let Err(error) = result {
                    assert!(error.contains("pending runner") && error.contains("runner remove"));
                }
            }
        }
    }

    #[test]
    fn service_absence_requires_specific_observation_not_any_nonzero_exit() {
        let unknown = classify_service_output(false, "", "Sandbox restriction", "owned");
        assert_eq!(unknown.presence, Presence::Unknown);
        assert_eq!(
            classify_service_output(false, "", "Could not find service \"another\"", "owned")
                .presence,
            Presence::Unknown
        );
        assert_eq!(
            classify_service_output(
                false,
                "",
                "Could not find service \"owned\" in domain",
                "owned"
            )
            .presence,
            Presence::Absent
        );
        let record = recovery_record();
        let own = classify_service_output(
            true,
            &format!("  program = {}\n", record.executable_path),
            "",
            &record.service_name,
        );
        assert_eq!(service_ownership(&record, &own), Ownership::Owned);
        let foreign =
            classify_service_output(true, "program = /unrelated\n", "", &record.service_name);
        assert_eq!(service_ownership(&record, &foreign), Ownership::Unowned);
        assert_eq!(
            service_ownership(
                &record,
                &classify_service_output(true, "", "", &record.service_name)
            ),
            Ownership::Ambiguous
        );
    }

    #[test]
    fn plist_and_service_evidence_independently_gate_cleanup_retirement() {
        let mut record = recovery_record();
        let mut plist = PlistObservation {
            presence: Presence::Present,
            regular: true,
            owner_uid: Some(501),
            sha256: Some("sealed".into()),
            error: None,
            config: Some(
                json!({"Label":record.service_name, "ProgramArguments":[record.executable_path,"--mach-service",record.service_name],
                              "MachServices":{&record.service_name:true},"EnvironmentVariables":{"XPC_SERVICE_PATH":record.bundle_path}}),
            ),
        };
        record.ownership = Some(RunnerOwnership {
            plist_path: "/owned.plist".into(),
            launchd_domain: "gui/501".into(),
            owner_uid: 501,
            plist_sha256: "sealed".into(),
        });
        assert_eq!(plist_ownership(&record, &plist), Ownership::Owned);
        plist.sha256 = Some("changed".into());
        assert_eq!(plist_ownership(&record, &plist), Ownership::Unowned);
        plist.presence = Presence::Absent;
        let mut service = ServiceObservation {
            presence: Presence::Present,
            executable_path: Some(record.executable_path.clone()),
            error: None,
        };
        assert!(
            !cleanup_complete(&service, &plist),
            "failed bootout plus successful plist removal must retain recovery"
        );
        service.presence = Presence::Unknown;
        assert!(!cleanup_complete(&service, &plist));
        service.presence = Presence::Absent;
        assert!(cleanup_complete(&service, &plist));
        plist.presence = Presence::Unknown;
        assert!(!cleanup_complete(&service, &plist));
    }
    struct SuppliedCleanup {
        registry: PathBuf,
        loaded: Presence,
        plist_exists: bool,
        owned: bool,
        fail_bootout: bool,
        fail_unlink: bool,
        fail_retirement: bool,
        crash_after_bootout: bool,
        actions: Vec<&'static str>,
        /// Service reads after a bootout that still list the job before it clears.
        teardown_reads: usize,
        pending_teardown: usize,
    }
    impl CleanupSystem for SuppliedCleanup {
        fn location(&mut self, _: &RunnerRecord) -> Result<(PathBuf, String), String> {
            let disk = load_registry(&self.registry)?;
            assert!(
                disk.runners.is_empty(),
                "active record must be retired before machine inspection"
            );
            assert_eq!(disk.pending_cleanup.len(), 1);
            Ok((
                self.registry.with_file_name("owned.plist"),
                "gui/fixture".into(),
            ))
        }
        fn service(&mut self, _: &str, _: &str) -> ServiceObservation {
            let presence = if self.pending_teardown > 0 {
                self.pending_teardown = self.pending_teardown.saturating_sub(1);
                Presence::Present
            } else {
                self.loaded
            };
            ServiceObservation {
                presence,
                error: None,
                executable_path: Some(if self.owned {
                    recovery_record().executable_path
                } else {
                    "/unrelated".into()
                }),
            }
        }
        fn plist(&mut self, _: &Path) -> PlistObservation {
            use std::os::unix::fs::PermissionsExt;
            if self.fail_retirement && !self.plist_exists && self.loaded == Presence::Absent {
                fs::set_permissions(
                    self.registry.parent().unwrap(),
                    fs::Permissions::from_mode(0o500),
                )
                .unwrap();
            }
            let record = recovery_record();
            PlistObservation {
                presence: if self.plist_exists {
                    Presence::Present
                } else {
                    Presence::Absent
                },
                regular: true,
                sha256: None,
                owner_uid: None,
                error: None,
                config: Some(json!({
                    "Label":if self.owned {record.service_name.clone()} else {"unrelated".into()},
                    "ProgramArguments":[record.executable_path,"--mach-service",record.service_name],
                    "MachServices":{&record.service_name:true},"EnvironmentVariables":{"XPC_SERVICE_PATH":record.bundle_path}})),
            }
        }
        fn bootout(&mut self, _: &str, _: &str) -> Result<(), String> {
            self.actions.push("bootout");
            if self.fail_bootout {
                return Err("controlled bootout failure".into());
            }
            self.loaded = Presence::Absent;
            self.pending_teardown = self.teardown_reads;
            assert!(
                !self.crash_after_bootout,
                "controlled process loss after bootout"
            );
            Ok(())
        }
        fn wait(&mut self, interval: std::time::Duration) {
            assert_eq!(interval.as_millis() as u64, TEARDOWN_POLL_INTERVAL_MS);
            self.actions.push("wait");
        }
        fn remove_plist(&mut self, _: &Path) -> std::io::Result<()> {
            self.actions.push("unlink");
            if self.fail_unlink {
                return Err(std::io::Error::from(std::io::ErrorKind::PermissionDenied));
            }
            self.plist_exists = false;
            Ok(())
        }
    }

    #[test]
    fn removal_preserves_recovery_across_faults_and_repeated_cleanup() {
        for mode in [
            "initial_save",
            "bootout",
            "unlink",
            "unknown",
            "unowned",
            "skip_bootout",
            "crash",
            "retirement",
            "success",
        ] {
            let fixture = RegistryFixture::new();
            let path = fixture.path();
            let mut registry = load_registry(&path).unwrap();
            registry.runners.push(recovery_record());
            save_registry(&path, &registry).unwrap();
            let mut system = SuppliedCleanup {
                registry: path.clone(),
                loaded: if mode == "unknown" {
                    Presence::Unknown
                } else {
                    Presence::Present
                },
                plist_exists: true,
                owned: mode != "unowned",
                fail_bootout: mode == "bootout",
                fail_unlink: mode == "unlink",
                fail_retirement: mode == "retirement",
                crash_after_bootout: mode == "crash",
                actions: vec![],
                teardown_reads: 0,
                pending_teardown: 0,
            };
            if mode == "initial_save" {
                fixture.writable(false);
            }
            let first = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                remove_record(
                    &path,
                    &mut registry,
                    Some("runner-owned"),
                    None,
                    mode == "skip_bootout",
                    &mut system,
                )
            }));
            fixture.writable(true);
            if mode == "initial_save" {
                assert!(first.unwrap().is_err());
                assert!(system.actions.is_empty());
                assert_eq!(load_registry(&path).unwrap().runners.len(), 1);
                continue;
            }
            let disk = load_registry(&path).unwrap();
            assert!(disk.runners.is_empty());
            assert_eq!(disk.pending_cleanup.is_empty(), mode == "success", "{mode}");
            if mode == "crash" {
                assert!(first.is_err());
            } else {
                let report = first.unwrap().unwrap().unwrap();
                assert_eq!(report.cleanup_retained, mode != "success", "{mode}");
                if mode != "success" {
                    assert!(!report.warnings.is_empty());
                }
            }
            if mode == "bootout" {
                assert!(!system.plist_exists && system.loaded == Presence::Present);
                assert_eq!(
                    disk.pending_cleanup[0].runner.executable_path,
                    recovery_record().executable_path
                );
                assert_eq!(
                    disk.pending_cleanup[0].observations.last().unwrap()["service"]["presence"],
                    "present"
                );
            }
            if mode == "unowned" {
                assert!(system.actions.is_empty());
            }
            system.fail_bootout = false;
            system.fail_unlink = false;
            system.owned = true;
            system.fail_retirement = false;
            system.crash_after_bootout = false;
            if system.loaded == Presence::Unknown {
                system.loaded = Presence::Present;
            }
            let mut disk = load_registry(&path).unwrap();
            let retry = remove_record(
                &path,
                &mut disk,
                None,
                Some(&recovery_record().service_name),
                false,
                &mut system,
            )
            .unwrap();
            if mode == "success" {
                assert!(retry.is_none());
            } else {
                assert!(!retry.unwrap().cleanup_retained, "{mode}");
            }
            assert!(load_registry(&path).unwrap().pending_cleanup.is_empty());
            assert!(!system.plist_exists && system.loaded == Presence::Absent);
        }
    }

    #[test]
    fn documented_removal_limits() {
        let manifest: serde_json::Value =
            serde_json::from_str(include_str!("../../docs/limits.json")).unwrap();
        let row = manifest["limits"]
            .as_array()
            .unwrap()
            .iter()
            .find(|r| r["id"] == "runner_remove_teardown_wait")
            .expect("limits.json documents the removal teardown wait");
        assert_eq!(row["value"].as_u64(), Some(TEARDOWN_WAIT_MS));
        assert_eq!(row["unit"], "milliseconds");
    }

    #[test]
    fn bootout_waits_out_launchd_teardown_within_the_budget() {
        let polls = TEARDOWN_WAIT_MS / TEARDOWN_POLL_INTERVAL_MS;
        for (label, reads, skip, complete, waits) in [
            ("clears_after_two_reads", 2usize, false, true, 2u64),
            ("never_clears", usize::MAX, false, false, polls),
            ("skipped_bootout_awaits_nothing", usize::MAX, true, false, 0),
        ] {
            let fixture = RegistryFixture::new();
            let path = fixture.path();
            let mut registry = load_registry(&path).unwrap();
            registry.runners.push(recovery_record());
            save_registry(&path, &registry).unwrap();
            let mut system = SuppliedCleanup {
                registry: path.clone(),
                loaded: Presence::Present,
                plist_exists: true,
                owned: true,
                fail_bootout: false,
                fail_unlink: false,
                fail_retirement: false,
                crash_after_bootout: false,
                actions: vec![],
                teardown_reads: reads,
                pending_teardown: 0,
            };
            let report = remove_record(
                &path,
                &mut registry,
                Some("runner-owned"),
                None,
                skip,
                &mut system,
            )
            .unwrap()
            .unwrap();
            let waited = system.actions.iter().filter(|a| **a == "wait").count() as u64;
            assert_eq!(waited, waits, "{label}");
            assert_eq!(report.cleanup_retained, !complete, "{label}");
            let disk = load_registry(&path).unwrap();
            if complete {
                assert!(disk.pending_cleanup.is_empty(), "{label}");
                continue;
            }
            let after = disk.pending_cleanup[0].observations.last().unwrap().clone();
            assert_eq!(after["phase"], "after", "{label}");
            assert_eq!(after["service"]["presence"], "present", "{label}");
            assert_eq!(after["teardown_wait"]["reads"], waits + 1, "{label}");
            assert_eq!(
                after["teardown_wait"]["waited_ms"],
                waits * TEARDOWN_POLL_INTERVAL_MS,
                "{label}"
            );
            assert!(
                report
                    .warnings
                    .iter()
                    .any(|w| w.contains("absence is not confirmed")),
                "{label}: {:?}",
                report.warnings
            );
        }
    }
}
