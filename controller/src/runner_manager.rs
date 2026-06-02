//! External runner registry and launchd wiring.
//!
//! The registry is a small JSON file under the user's Library directory. We
//! also generate launchd plists so Mach services can be registered in a user or
//! system domain.

use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

pub const RUNNER_REGISTRY_SCHEMA_VERSION: u32 = 1;
pub const RUNNER_PROTOCOL_VERSION: u32 = 1;

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
    pub keys: Vec<String>,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunnerRecord {
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
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunnerRegistry {
    pub schema_version: u32,
    pub runners: Vec<RunnerRecord>,
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
        });
    }
    let text =
        fs::read_to_string(path).map_err(|e| format!("failed to read {}: {e}", path.display()))?;
    let registry: RunnerRegistry =
        serde_json::from_str(&text).map_err(|e| format!("failed to parse {}: {e}", path.display()))?;
    if registry.schema_version != RUNNER_REGISTRY_SCHEMA_VERSION {
        return Err(format!(
            "unsupported runner registry schema_version {} (expected {})",
            registry.schema_version, RUNNER_REGISTRY_SCHEMA_VERSION
        ));
    }
    Ok(registry)
}

pub fn save_registry(path: &Path, registry: &RunnerRegistry) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|e| format!("failed to create {}: {e}", parent.display()))?;
    }
    let text = serde_json::to_string_pretty(registry)
        .map_err(|e| format!("failed to encode registry JSON: {e}"))?;
    fs::write(path, text).map_err(|e| format!("failed to write {}: {e}", path.display()))
}

pub fn random_id() -> Result<String, String> {
    let mut buf = [0u8; 16];
    let mut file = fs::File::open("/dev/urandom")
        .map_err(|e| format!("failed to open /dev/urandom: {e}"))?;
    file.read_exact(&mut buf)
        .map_err(|e| format!("failed to read /dev/urandom: {e}"))?;
    let mut out = String::from("runner-");
    for b in buf {
        out.push_str(&format!("{:02x}", b));
    }
    Ok(out)
}

pub fn entitlements_from_json(value: &Value) -> RunnerEntitlements {
    let keys = match value {
        Value::Object(map) => {
            let mut keys: Vec<String> = map.keys().cloned().collect();
            keys.sort();
            keys
        }
        _ => Vec::new(),
    };
    RunnerEntitlements {
        raw_plist: None,
        keys,
        error: None,
    }
}

pub fn entitlements_superset(required: &[String], entitlements: &RunnerEntitlements) -> bool {
    if entitlements.error.is_some() {
        return false;
    }
    let set: BTreeSet<&str> = entitlements.keys.iter().map(|s| s.as_str()).collect();
    required.iter().all(|key| set.contains(key.as_str()))
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
</dict>
</plist>
"#,
    )
}

pub fn write_launchd_plist(path: &Path, content: &str) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|e| format!("failed to create {}: {e}", parent.display()))?;
    }
    let mut file = fs::File::create(path)
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
        .args(["-d", "--entitlements", ":-", target.to_string_lossy().as_ref()])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output();
    let out = match out {
        Ok(out) => out,
        Err(err) => {
            return RunnerEntitlements {
                raw_plist: None,
                keys: Vec::new(),
                error: Some(format!("failed to run codesign: {err}")),
            };
        }
    };
    if !out.status.success() {
        let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
        return RunnerEntitlements {
            raw_plist: None,
            keys: Vec::new(),
            error: Some(format!("codesign failed: {stderr}")),
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

pub fn codesign_verify(target: &Path) -> Result<(), String> {
    let out = Command::new("/usr/bin/codesign")
        .args(["--verify", "--verbose=2", target.to_string_lossy().as_ref()])
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

fn current_uid_string() -> Result<String, String> {
    if let Ok(uid) = std::env::var("UID") {
        let trimmed = uid.trim();
        if !trimmed.is_empty() && trimmed.chars().all(|c| c.is_ascii_digit()) {
            return Ok(trimmed.to_string());
        }
    }
    // Fall back to /usr/bin/id for environments that do not export UID.
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

fn launchctl_target(scope: RunnerScope) -> Result<String, String> {
    match scope {
        // launchctl expects user services under the per-user GUI domain.
        RunnerScope::User => Ok(format!("gui/{}", current_uid_string()?)),
        RunnerScope::System => Ok("system".to_string()),
    }
}

pub fn launchctl_service_present(scope: RunnerScope, service_name: &str) -> Result<bool, String> {
    let target = launchctl_target(scope)?;
    let full = format!("{}/{}", target, service_name);
    let out = Command::new("/bin/launchctl")
        .args(["print", &full])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run launchctl: {e}"))?;
    Ok(out.status.success())
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

pub fn launchctl_bootout(scope: RunnerScope, plist_path: &Path) -> Result<(), String> {
    let target = launchctl_target(scope)?;
    let out = Command::new("/bin/launchctl")
        .args(["bootout", &target, plist_path.to_string_lossy().as_ref()])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run launchctl: {e}"))?;
    if out.status.success() {
        return Ok(());
    }
    let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
    Err(format!("launchctl bootout failed: {stderr}"))
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn entitlements_superset_matches_keys() {
        let ent = entitlements_from_json(&json!({
            "com.apple.security.app-sandbox": true,
            "com.apple.security.cs.allow-jit": true
        }));
        assert!(entitlements_superset(
            &vec![
                "com.apple.security.app-sandbox".to_string(),
                "com.apple.security.cs.allow-jit".to_string()
            ],
            &ent
        ));
        assert!(!entitlements_superset(
            &vec!["com.apple.security.files.user-selected.read-only".to_string()],
            &ent
        ));
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
        let kind: RunnerKind = serde_json::from_str("\"debuggable\"")
            .expect("legacy debuggable should deserialize");
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
}
