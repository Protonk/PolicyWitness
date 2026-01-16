mod evidence;
mod json_contract;
mod runner_manager;

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::BTreeMap;
use std::ffi::OsString;
use std::path::{Component, Path, PathBuf};
use std::process::{Command, Stdio};
use std::thread;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use runner_manager::{RunnerEntitlements, RunnerRecord, RunnerRegistry, RunnerScope, RunnerSignature};

const PW_RUNNER_SERVICE_DIR: &str = "PWRunner";

const DEFAULT_TIMEOUT_MS: u64 = 240_000;
const DEFAULT_LOG_LAST: &str = "10s";

const MAX_CAPTURE_BYTES: usize = 1024 * 1024;
const SONOMA_CROSS_CHECK_PID_TIMEOUT_MS: u64 = 1500;
const SONOMA_CROSS_CHECK_PID_POLL_MS: u64 = 50;
const SONOMA_CROSS_CHECK_SETTLE_MS: u64 = 200;
const SONOMA_CROSS_CHECK_BASE_MS: u64 = 1000;
const SONOMA_CROSS_CHECK_PER_STEP_MS: u64 = 150;
const SONOMA_CROSS_CHECK_MIN_MS: u64 = 3000;
const SONOMA_CROSS_CHECK_MAX_MS: u64 = 15000;

fn print_usage() {
    eprintln!(
        "\
usage:
  policy-witness run <request.json> [--timeout-ms <n>] [--log-last <dur>] [--instrumentation <json|@path>] [--sonoma-cross-check]
  policy-witness runner <command> [options]

notes:
  - runs the selected PWRunner XPC service once and prints a single JSON result to stdout
  - request.json is passed through to the runner client (or copied with instrumentation injected)"
    );
}

fn now_unix_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

fn validate_tool_name(tool_name: &str) -> Result<(), String> {
    let mut components = Path::new(tool_name).components();
    match (components.next(), components.next()) {
        (Some(Component::Normal(_)), None) => Ok(()),
        _ => Err(format!(
            "invalid tool name {tool_name:?} (must be a single path component)"
        )),
    }
}

fn app_root_from_current_exe() -> Result<PathBuf, String> {
    let exe = std::env::current_exe().map_err(|e| format!("current_exe() failed: {e}"))?;
    // Expected layout: PolicyWitness.app/Contents/MacOS/policy-witness
    let contents_dir = exe
        .parent()
        .and_then(|p| p.parent())
        .ok_or_else(|| format!("unexpected executable location: {}", exe.display()))?;
    let app_root = contents_dir
        .parent()
        .ok_or_else(|| format!("unexpected executable location: {}", exe.display()))?;
    Ok(app_root.to_path_buf())
}

fn resolve_contents_macos_tool(tool_name: &str) -> Result<PathBuf, String> {
    validate_tool_name(tool_name)?;
    let exe = std::env::current_exe().map_err(|e| format!("current_exe() failed: {e}"))?;
    let contents_dir = exe
        .parent()
        .and_then(|p| p.parent())
        .ok_or_else(|| format!("unexpected executable location: {}", exe.display()))?;
    let candidate = contents_dir.join("MacOS").join(tool_name);
    if candidate.exists() {
        return Ok(candidate);
    }
    Err(format!(
        "embedded tool not found in Contents/MacOS: {tool_name:?} (expected: {})",
        candidate.display()
    ))
}

fn plist_key_string(plist_path: &Path, key: &str) -> Result<String, String> {
    let plist = plist_path
        .to_str()
        .ok_or_else(|| format!("non-utf8 plist path: {}", plist_path.display()))?;
    let cmd = "/usr/libexec/PlistBuddy";
    let out = Command::new(cmd)
        .args(["-c", &format!("Print :{key}"), plist])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run {cmd}: {e}"))?;
    if !out.status.success() {
        let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
        let stdout = String::from_utf8_lossy(&out.stdout).trim().to_string();
        let msg = if !stderr.is_empty() { stderr } else { stdout };
        return Err(format!(
            "PlistBuddy failed for {} key {}: {}",
            plist_path.display(),
            key,
            msg
        ));
    }
    Ok(String::from_utf8_lossy(&out.stdout).trim().to_string())
}

#[derive(Clone)]
struct PWRunnerBundleInfo {
    bundle_id: String,
    executable: String,
}

fn resolve_pw_runner_bundle_info(app_root: &Path) -> Result<PWRunnerBundleInfo, String> {
    let plist = app_root
        .join("Contents")
        .join("XPCServices")
        .join(format!("{PW_RUNNER_SERVICE_DIR}.xpc"))
        .join("Contents")
        .join("Info.plist");
    if !plist.exists() {
        return Err(format!("missing PWRunner Info.plist: {}", plist.display()));
    }
    let bundle_id = plist_key_string(&plist, "CFBundleIdentifier")?;
    let executable = plist_key_string(&plist, "CFBundleExecutable")?;
    Ok(PWRunnerBundleInfo {
        bundle_id,
        executable,
    })
}

#[derive(Default)]
struct RunnerSelector {
    runner_id: Option<String>,
    runner_service: Option<String>,
    required_entitlements: Vec<String>,
}

struct RunnerTarget {
    kind: String,
    service_name: String,
    process_name: String,
    bundle_id: Option<String>,
    bundle_path: Option<PathBuf>,
    executable_path: Option<PathBuf>,
    registry_id: Option<String>,
    signature: Option<RunnerSignature>,
    entitlements: Option<RunnerEntitlements>,
}

#[derive(Serialize)]
struct RunnerProvenance {
    runner_kind: String,
    runner_registry_id: Option<String>,
    runner_service_name: String,
    runner_bundle_id: Option<String>,
    runner_bundle_path: Option<String>,
    runner_executable_path: Option<String>,
    runner_signature: Option<RunnerSignature>,
    runner_entitlements: Option<RunnerEntitlements>,
}

#[derive(Serialize)]
struct AppProvenance {
    app_bundle_id: Option<String>,
    app_binary_rel_path: Option<String>,
    app_entitlements: Option<Value>,
    evidence_manifest_path: String,
    evidence_notes: Option<Vec<String>>,
    evidence_verify: Option<evidence::VerifyReport>,
}

fn parse_runner_selector(request_path: &Path) -> Result<RunnerSelector, String> {
    let text = std::fs::read_to_string(request_path)
        .map_err(|e| format!("failed to read request.json: {e}"))?;
    let value: Value = serde_json::from_str(&text)
        .map_err(|e| format!("failed to parse request.json: {e}"))?;

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
        return Ok(selector);
    }

    if let Some(v) = value.get("runner_id").and_then(|v| v.as_str()) {
        selector.runner_id = Some(v.to_string());
    }
    if let Some(v) = value.get("runner_service").and_then(|v| v.as_str()) {
        selector.runner_service = Some(v.to_string());
    }
    if let Some(list) = value.get("required_entitlements").and_then(|v| v.as_array()) {
        selector.required_entitlements = list
            .iter()
            .filter_map(|v| v.as_str().map(|s| s.to_string()))
            .collect();
    }

    Ok(selector)
}

fn read_json_file(path: &Path, label: &str) -> Result<Value, String> {
    let text = std::fs::read_to_string(path)
        .map_err(|e| format!("failed to read {label}: {e}"))?;
    serde_json::from_str(&text).map_err(|e| format!("failed to parse {label}: {e}"))
}

fn load_instrumentation_value(raw: &str) -> Result<Value, String> {
    let raw = raw.trim();
    let path = if let Some(rest) = raw.strip_prefix('@') {
        Some(PathBuf::from(rest))
    } else {
        let candidate = Path::new(raw);
        if candidate.exists() {
            Some(candidate.to_path_buf())
        } else {
            None
        }
    };

    let value = if let Some(path) = path {
        read_json_file(&path, "instrumentation").map_err(|e| format!("failed to read instrumentation: {e}"))?
    } else {
        serde_json::from_str(raw).map_err(|e| format!("failed to parse instrumentation JSON: {e}"))?
    };

    if !value.is_object() {
        return Err("instrumentation must be a JSON object".to_string());
    }
    Ok(value)
}

fn write_temp_request(value: &Value) -> Result<PathBuf, String> {
    let temp_dir = std::env::temp_dir().join("policy-witness");
    std::fs::create_dir_all(&temp_dir)
        .map_err(|e| format!("failed to create temp dir: {e}"))?;
    let pid = std::process::id();
    let encoded = serde_json::to_string_pretty(value)
        .map_err(|e| format!("failed to encode request JSON: {e}"))?;
    for attempt in 0..100u32 {
        let candidate = temp_dir.join(format!("request-{pid}-{}-{attempt}.json", now_unix_ms()));
        if candidate.exists() {
            continue;
        }
        std::fs::write(&candidate, &encoded)
            .map_err(|e| format!("failed to write temp request: {e}"))?;
        return Ok(candidate);
    }
    Err("failed to create temp request file".to_string())
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

fn builtin_runner_target(app_root: &Path) -> Result<RunnerTarget, String> {
    let runner_info = resolve_pw_runner_bundle_info(app_root)?;
    let bundle_path = app_root
        .join("Contents")
        .join("XPCServices")
        .join(format!("{PW_RUNNER_SERVICE_DIR}.xpc"));
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
    let entitlements = entry.map(|e| entitlements_from_manifest_value(
        e.entitlements.as_ref(),
        e.entitlements_error.as_ref(),
    ));

    Ok(RunnerTarget {
        kind: "builtin".to_string(),
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

fn resolve_runner_target(
    app_root: &Path,
    selector: &RunnerSelector,
) -> Result<RunnerTarget, String> {
    let needs_external = selector.runner_id.is_some() || selector.runner_service.is_some();
    if !needs_external {
        let target = builtin_runner_target(app_root)?;
        if !selector.required_entitlements.is_empty() {
            let ent = target
                .entitlements
                .as_ref()
                .ok_or_else(|| "built-in runner entitlements unavailable".to_string())?;
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

    if !selector.required_entitlements.is_empty()
        && !runner_manager::entitlements_superset(
            &selector.required_entitlements,
            &record.entitlements,
        )
    {
        return Err("external runner does not satisfy required entitlements".to_string());
    }

    Ok(RunnerTarget {
        kind: "external".to_string(),
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

fn runner_provenance_from_target(target: &RunnerTarget) -> RunnerProvenance {
    RunnerProvenance {
        runner_kind: target.kind.clone(),
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

fn load_app_provenance(app_root: &Path) -> Result<AppProvenance, String> {
    let manifest_path = evidence::manifest_path_from_app_root(app_root);
    let manifest = evidence::load_manifest(&manifest_path)
        .map_err(|e| format!("failed to read evidence manifest: {e}"))?;
    let verify = match std::env::var("PW_VERIFY_EVIDENCE").ok().as_deref() {
        Some("1") => Some(evidence::verify_manifest(
            &manifest,
            app_root,
            &manifest_path,
        )),
        _ => None,
    };
    Ok(AppProvenance {
        app_bundle_id: manifest.app_bundle_id,
        app_binary_rel_path: manifest.app_binary_rel_path,
        app_entitlements: manifest.app_entitlements,
        evidence_manifest_path: manifest_path.display().to_string(),
        evidence_notes: manifest.notes,
        evidence_verify: verify,
    })
}

fn truncate_output(bytes: &[u8]) -> (String, bool) {
    if bytes.len() <= MAX_CAPTURE_BYTES {
        return (String::from_utf8_lossy(bytes).to_string(), false);
    }
    (
        String::from_utf8_lossy(&bytes[..MAX_CAPTURE_BYTES]).to_string(),
        true,
    )
}

#[derive(Serialize)]
struct RunnerClientRun {
    argv: Vec<String>,
    started_at_unix_ms: u64,
    ended_at_unix_ms: u64,
    exit_code: i32,
    stdout_parse_error: Option<String>,
    stdout_truncated: bool,
    stdout_raw: Option<String>,
    stderr: String,
    stderr_truncated: bool,
}

#[derive(Serialize, Deserialize, Clone)]
struct SandboxDenyEvent {
    pid: Option<i32>,
    process: Option<String>,
    operation: Option<String>,
    path: Option<String>,
    raw_line: Option<String>,
}

#[derive(Serialize)]
struct SandboxLogStepDeny {
    step_id: String,
    deny_events: Vec<SandboxDenyEvent>,
}

#[derive(Serialize)]
struct SandboxLogCapture {
    capture_status: String,
    tool_exit_code: i32,
    blocked_reason: Option<String>,
    stdout_parse_error: Option<String>,
    stdout_truncated: bool,
    stdout_raw: Option<String>,
    stderr: String,
    stderr_truncated: bool,
    observer: Option<Value>,
    observed_deny: Option<bool>,
    deny_events: Option<Vec<SandboxDenyEvent>>,
    step_denies: Option<Vec<SandboxLogStepDeny>>,
}

#[derive(Clone)]
struct SonomaCrossCheckSpec {
    step_id: String,
    operation: String,
    filter_kind: String,
    filter_value: Option<String>,
}

#[derive(Clone)]
struct SonomaCrossCheckPlan {
    tool_path: PathBuf,
    process_name: String,
    wait_ms: u64,
    specs: Vec<SonomaCrossCheckSpec>,
}

#[derive(Serialize, Default)]
struct SonomaCrossCheckCounts {
    total: usize,
    checked: usize,
    skipped: usize,
    errors: usize,
    mismatches: usize,
}

#[derive(Serialize)]
struct SonomaCrossCheckStep {
    step_id: String,
    operation: String,
    filter_kind: String,
    filter_value: Option<String>,
    status: String,
    validator: Option<Value>,
    validator_outcome: Option<String>,
    expected_outcome: Option<String>,
    mismatch: Option<bool>,
    error: Option<String>,
}

#[derive(Serialize)]
struct SonomaCrossCheckReport {
    status: String,
    tool_path: Option<String>,
    runner_pid: Option<i64>,
    wait_ms: Option<u64>,
    error: Option<String>,
    counts: SonomaCrossCheckCounts,
    steps: Vec<SonomaCrossCheckStep>,
}

#[derive(Serialize)]
struct RunData {
    request_path: String,
    runner_service_bundle_id: String,
    runner_service_executable: String,
    runner_service_name: String,
    runner_registry_id: Option<String>,
    runner_provenance: RunnerProvenance,
    app_provenance: Option<AppProvenance>,
    timeout_ms: u64,
    log_last: String,
    runner_client: RunnerClientRun,
    runner_result: Option<Value>,
    sandbox_log_capture: Option<SandboxLogCapture>,
    sonoma_cross_check: Option<SonomaCrossCheckReport>,
}

fn parse_runner_client_output(
    argv: &[OsString],
    started: u64,
    ended: u64,
    out: &std::process::Output,
) -> (RunnerClientRun, Option<Value>) {
    let (stdout, stdout_truncated) = truncate_output(&out.stdout);
    let (stderr, stderr_truncated) = truncate_output(&out.stderr);

    let mut parsed: Option<Value> = None;
    let mut parse_error: Option<String> = None;
    if !stdout.trim().is_empty() {
        match serde_json::from_str::<Value>(&stdout) {
            Ok(v) => parsed = Some(v),
            Err(e) => parse_error = Some(format!("{e}")),
        }
    }

    let runner_client = RunnerClientRun {
        argv: argv
            .iter()
            .map(|s| s.to_string_lossy().to_string())
            .collect(),
        started_at_unix_ms: started,
        ended_at_unix_ms: ended,
        exit_code: out.status.code().unwrap_or(1),
        stdout_parse_error: parse_error.clone(),
        stdout_truncated,
        stdout_raw: if parse_error.is_some() { Some(stdout) } else { None },
        stderr,
        stderr_truncated,
    };

    (runner_client, parsed)
}

fn run_pw_runner_client(
    service_name: &str,
    request_path: &Path,
    timeout_ms: u64,
) -> Result<(RunnerClientRun, Option<Value>), String> {
    let tool = resolve_contents_macos_tool("pw-runner-client")?;
    let argv = vec![
        tool.into_os_string(),
        OsString::from("run"),
        OsString::from("--timeout-ms"),
        OsString::from(format!("{timeout_ms}")),
        OsString::from(service_name),
        request_path.as_os_str().to_os_string(),
    ];

    let started = now_unix_ms();
    let out = Command::new(&argv[0])
        .args(&argv[1..])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run pw-runner-client: {e}"))?;
    let ended = now_unix_ms();
    Ok(parse_runner_client_output(&argv, started, ended, &out))
}

fn run_pw_runner_client_with_cross_check(
    service_name: &str,
    request_path: &Path,
    timeout_ms: u64,
    plan: SonomaCrossCheckPlan,
) -> Result<(RunnerClientRun, Option<Value>, Option<SonomaCrossCheckReport>), String> {
    let tool = resolve_contents_macos_tool("pw-runner-client")?;
    let argv = vec![
        tool.into_os_string(),
        OsString::from("run"),
        OsString::from("--timeout-ms"),
        OsString::from(format!("{timeout_ms}")),
        OsString::from(service_name),
        request_path.as_os_str().to_os_string(),
    ];

    let started = now_unix_ms();
    let child = Command::new(&argv[0])
        .args(&argv[1..])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("failed to spawn pw-runner-client: {e}"))?;

    let report = run_sonoma_cross_check(&plan);

    let out = child
        .wait_with_output()
        .map_err(|e| format!("failed to wait for pw-runner-client: {e}"))?;
    let ended = now_unix_ms();
    let (runner_client, parsed) = parse_runner_client_output(&argv, started, ended, &out);
    Ok((runner_client, parsed, Some(report)))
}

fn observed_deny_from_observer_envelope(obj: &Value) -> Option<bool> {
    obj.get("data")
        .and_then(|v| v.get("observed_deny"))
        .and_then(|v| v.as_bool())
}

fn observer_log_error(obj: &Value) -> Option<String> {
    obj.get("data")
        .and_then(|v| v.get("log_error"))
        .and_then(|v| v.as_str())
        .map(|s| s.to_string())
}

fn observer_blocked_reason(obj: &Value) -> Option<String> {
    if let Some(reason) = obj
        .get("data")
        .and_then(|v| v.get("blocked_reason"))
        .and_then(|v| v.as_str())
    {
        return Some(reason.to_string());
    }
    let err = observer_log_error(obj)?;
    if err.to_ascii_lowercase().contains("cannot run while sandboxed") {
        return Some(err);
    }
    None
}

fn observer_deny_events(obj: &Value) -> Option<Vec<SandboxDenyEvent>> {
    let value = obj.get("data")?.get("deny_events")?.clone();
    serde_json::from_value::<Vec<SandboxDenyEvent>>(value).ok()
}

fn step_attempt_paths(step: &Value) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    let attempt = match step.get("attempt") {
        Some(v) => v,
        None => return out,
    };
    for key in ["observed_path", "normalized_path", "requested_path"] {
        if let Some(val) = attempt.get(key).and_then(|v| v.as_str()) {
            out.push(val.to_string());
        }
    }
    out.sort();
    out.dedup();
    out
}

fn match_step_denies(
    steps: &[Value],
    deny_events: &[SandboxDenyEvent],
    pid: Option<i64>,
) -> Vec<SandboxLogStepDeny> {
    let pid = pid.and_then(|v| i32::try_from(v).ok());
    let mut out: Vec<SandboxLogStepDeny> = Vec::new();
    for step in steps {
        let step_id = match step.get("step_id").and_then(|v| v.as_str()) {
            Some(v) => v.to_string(),
            None => continue,
        };
        let paths = step_attempt_paths(step);
        if paths.is_empty() {
            continue;
        }
        let mut matched: Vec<SandboxDenyEvent> = Vec::new();
        for event in deny_events {
            if let (Some(event_pid), Some(pid)) = (event.pid, pid) {
                if event_pid != pid {
                    continue;
                }
            }
            if let Some(path) = event.path.as_ref() {
                if paths.iter().any(|p| p == path) {
                    matched.push(event.clone());
                }
            }
        }
        if !matched.is_empty() {
            out.push(SandboxLogStepDeny {
                step_id,
                deny_events: matched,
            });
        }
    }
    out
}

fn capture_sandbox_logs_last(
    pid: i64,
    process_name: &str,
    last: &str,
) -> Result<SandboxLogCapture, String> {
    let tool = resolve_contents_macos_tool("sandbox-log-observer")?;
    let argv = vec![
        tool.into_os_string(),
        OsString::from("--pid"),
        OsString::from(format!("{pid}")),
        OsString::from("--process-name"),
        OsString::from(process_name),
        OsString::from("--last"),
        OsString::from(last),
        OsString::from("--format"),
        OsString::from("json"),
    ];

    let out = Command::new(&argv[0])
        .args(&argv[1..])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run sandbox-log-observer: {e}"))?;

    let exit_code = out.status.code().unwrap_or(1);

    let (stdout, stdout_truncated) = truncate_output(&out.stdout);
    let (stderr, stderr_truncated) = truncate_output(&out.stderr);

    let mut parsed: Option<Value> = None;
    let mut parse_error: Option<String> = None;
    if !stdout.trim().is_empty() {
        match serde_json::from_str::<Value>(&stdout) {
            Ok(v) => parsed = Some(v),
            Err(e) => parse_error = Some(format!("{e}")),
        }
    }

    let observed_deny = parsed.as_ref().and_then(observed_deny_from_observer_envelope);
    let observer_log_error = parsed.as_ref().and_then(observer_log_error);
    let blocked_reason = parsed.as_ref().and_then(observer_blocked_reason);
    let deny_events = parsed.as_ref().and_then(observer_deny_events);

    let capture_status = if parse_error.is_some() {
        "parse_error".to_string()
    } else if blocked_reason.is_some() {
        "blocked".to_string()
    } else if observer_log_error.is_some() {
        "error".to_string()
    } else if exit_code != 0 {
        "error".to_string()
    } else if parsed.is_some() {
        "captured".to_string()
    } else {
        "error".to_string()
    };

    Ok(SandboxLogCapture {
        capture_status,
        tool_exit_code: exit_code,
        blocked_reason,
        stdout_parse_error: parse_error.clone(),
        stdout_truncated,
        stdout_raw: if parse_error.is_some() { Some(stdout) } else { None },
        stderr,
        stderr_truncated,
        observer: parsed,
        observed_deny,
        deny_events,
        step_denies: None,
    })
}

fn sonoma_cross_check_wait_ms(step_count: usize) -> u64 {
    let raw = SONOMA_CROSS_CHECK_BASE_MS + (SONOMA_CROSS_CHECK_PER_STEP_MS * step_count as u64);
    raw.clamp(SONOMA_CROSS_CHECK_MIN_MS, SONOMA_CROSS_CHECK_MAX_MS)
}

fn extract_sonoma_cross_check_specs(request_value: &Value) -> Result<Vec<SonomaCrossCheckSpec>, String> {
    let plan = request_value
        .get("probe_plan")
        .and_then(|v| v.as_array())
        .ok_or_else(|| "request.json missing probe_plan array".to_string())?;
    let mut specs = Vec::with_capacity(plan.len());
    for step in plan {
        let step_id = step
            .get("step_id")
            .and_then(|v| v.as_str())
            .ok_or_else(|| "probe_plan step missing step_id".to_string())?;
        let sandbox_check = step
            .get("sandbox_check")
            .and_then(|v| v.as_object())
            .ok_or_else(|| format!("step {step_id} missing sandbox_check"))?;
        let operation = sandbox_check
            .get("operation")
            .and_then(|v| v.as_str())
            .ok_or_else(|| format!("step {step_id} missing sandbox_check.operation"))?;
        let filter = sandbox_check
            .get("filter")
            .and_then(|v| v.as_object())
            .ok_or_else(|| format!("step {step_id} missing sandbox_check.filter"))?;
        let filter_kind = filter
            .get("kind")
            .and_then(|v| v.as_str())
            .ok_or_else(|| format!("step {step_id} missing sandbox_check.filter.kind"))?;
        let filter_value = filter
            .get("value")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string());
        specs.push(SonomaCrossCheckSpec {
            step_id: step_id.to_string(),
            operation: operation.to_string(),
            filter_kind: filter_kind.to_string(),
            filter_value,
        });
    }
    Ok(specs)
}

fn inject_sonoma_cross_check_instrumentation(
    request_value: &mut Value,
    wait_ms: u64,
) -> Result<(), String> {
    let obj = request_value
        .as_object_mut()
        .ok_or_else(|| "request.json must be a JSON object".to_string())?;
    let instrumentation = obj
        .entry("instrumentation")
        .or_insert_with(|| json!({}));
    let inst_obj = instrumentation
        .as_object_mut()
        .ok_or_else(|| "instrumentation must be a JSON object".to_string())?;
    let version = inst_obj
        .get("version")
        .and_then(|v| v.as_i64())
        .unwrap_or(1);
    if version != 1 {
        return Err(format!(
            "sonoma cross-check requires instrumentation.version=1 (got {version})"
        ));
    }
    inst_obj.insert("version".to_string(), json!(1));
    let ports = inst_obj.entry("ports").or_insert_with(|| json!([]));
    let ports_arr = ports
        .as_array_mut()
        .ok_or_else(|| "instrumentation.ports must be an array".to_string())?;
    ports_arr.push(json!({
        "kind": "debug_wait",
        "sleep_ms": wait_ms,
        "phase": "post_sandbox",
        "label": "sonoma_cross_check"
    }));
    Ok(())
}

fn wait_for_runner_pid(process_name: &str, timeout_ms: u64) -> Result<i64, String> {
    let deadline = Instant::now() + Duration::from_millis(timeout_ms);
    loop {
        let out = Command::new("/usr/bin/pgrep")
            .args(["-n", "-x", process_name])
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output();
        match out {
            Ok(output) => {
                if output.status.success() {
                    let stdout = String::from_utf8_lossy(&output.stdout);
                    if let Some(first) = stdout.lines().next() {
                        let pid = first
                            .trim()
                            .parse::<i64>()
                            .map_err(|e| format!("failed to parse pgrep pid: {e}"))?;
                        return Ok(pid);
                    }
                }
            }
            Err(e) => return Err(format!("failed to run pgrep: {e}")),
        }

        if Instant::now() >= deadline {
            break;
        }
        thread::sleep(Duration::from_millis(SONOMA_CROSS_CHECK_PID_POLL_MS));
    }
    Err(format!(
        "runner pid not found (process_name={process_name})"
    ))
}

fn sb_api_validator_outcome(value: &Value) -> Option<String> {
    let rc = value.get("rc").and_then(|v| v.as_i64())?;
    let errno = value.get("errno").and_then(|v| v.as_i64()).unwrap_or(0);
    if rc == 0 {
        Some("allow".to_string())
    } else if rc == 1 && errno == 0 {
        Some("deny".to_string())
    } else {
        Some("error".to_string())
    }
}

fn run_sb_api_validator(tool_path: &Path, pid: i64, spec: &SonomaCrossCheckSpec) -> SonomaCrossCheckStep {
    let mut step = SonomaCrossCheckStep {
        step_id: spec.step_id.clone(),
        operation: spec.operation.clone(),
        filter_kind: spec.filter_kind.clone(),
        filter_value: spec.filter_value.clone(),
        status: "error".to_string(),
        validator: None,
        validator_outcome: None,
        expected_outcome: None,
        mismatch: None,
        error: None,
    };

    let filter_type = match spec.filter_kind.as_str() {
        "path" => "PATH",
        "global_name" => "GLOBAL_NAME",
        "local_name" => "LOCAL_NAME",
        "none" => {
            step.status = "skipped".to_string();
            step.error = Some("filter.kind=none not supported by sb_api_validator".to_string());
            return step;
        }
        _ => {
            step.status = "skipped".to_string();
            step.error = Some(format!(
                "unsupported filter.kind {}",
                spec.filter_kind
            ));
            return step;
        }
    };

    let filter_value = match spec.filter_value.as_deref() {
        Some(v) if !v.is_empty() => v,
        _ => {
            step.status = "skipped".to_string();
            step.error = Some("filter.value missing".to_string());
            return step;
        }
    };

    let out = Command::new(tool_path)
        .args([
            OsString::from("--json"),
            OsString::from(pid.to_string()),
            OsString::from(&spec.operation),
            OsString::from(filter_type),
            OsString::from(filter_value),
        ])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output();

    let out = match out {
        Ok(o) => o,
        Err(e) => {
            step.error = Some(format!("sb_api_validator failed to run: {e}"));
            return step;
        }
    };

    let exit_code = out.status.code().unwrap_or(1);
    let (stdout, stdout_truncated) = truncate_output(&out.stdout);
    let (stderr, stderr_truncated) = truncate_output(&out.stderr);

    if stdout.trim().is_empty() {
        step.error = Some(format!(
            "sb_api_validator produced no stdout (exit={exit_code})"
        ));
        return step;
    }

    let parsed = match serde_json::from_str::<Value>(&stdout) {
        Ok(v) => v,
        Err(e) => {
            let mut msg = format!("sb_api_validator stdout parse error: {e}");
            if stdout_truncated {
                msg.push_str(" (stdout truncated)");
            }
            if stderr_truncated {
                msg.push_str(" (stderr truncated)");
            }
            if !stderr.is_empty() {
                msg.push_str(&format!("; stderr={}", stderr.trim()));
            }
            step.error = Some(msg);
            return step;
        }
    };

    let kind = parsed.get("kind").and_then(|v| v.as_str()).unwrap_or("");
    step.validator = Some(parsed.clone());

    if kind == "sb_api_validator_error" {
        let err = parsed
            .get("error")
            .and_then(|v| v.as_str())
            .unwrap_or("unknown error");
        step.error = Some(format!("sb_api_validator error: {err}"));
        return step;
    }

    if kind != "sb_api_validator_result" {
        step.error = Some(format!("unexpected sb_api_validator kind: {kind}"));
        return step;
    }

    if let Some(outcome) = sb_api_validator_outcome(&parsed) {
        step.validator_outcome = Some(outcome.clone());
        if outcome == "allow" || outcome == "deny" {
            step.status = "ok".to_string();
        } else {
            step.status = "error".to_string();
            step.error = Some("sb_api_validator returned non-allow/deny rc".to_string());
        }
        return step;
    }

    step.error = Some("sb_api_validator missing rc/errno".to_string());
    step
}

fn update_sonoma_cross_check_counts(report: &mut SonomaCrossCheckReport) {
    if report.status == "unavailable" {
        return;
    }
    let mut blocked = report
        .error
        .as_ref()
        .map(|msg| {
            let msg = msg.to_ascii_lowercase();
            msg.contains("operation not permitted") || msg.contains("sandbox")
        })
        .unwrap_or(false);
    let mut counts = SonomaCrossCheckCounts::default();
    counts.total = report.steps.len();
    for step in &report.steps {
        match step.status.as_str() {
            "ok" => counts.checked += 1,
            "skipped" => counts.skipped += 1,
            _ => counts.errors += 1,
        }
        if step.mismatch == Some(true) {
            counts.mismatches += 1;
        }
        if let Some(err) = step.error.as_ref() {
            let msg = err.to_ascii_lowercase();
            if msg.contains("operation not permitted") || msg.contains("sandbox") {
                blocked = true;
            }
        }
    }
    report.counts = counts;
    if blocked {
        report.status = "blocked".to_string();
        return;
    }
    report.status = if report.error.is_some() {
        "error".to_string()
    } else if report.counts.mismatches > 0 {
        "mismatch".to_string()
    } else if report.counts.errors > 0 {
        "error".to_string()
    } else if report.counts.checked == 0 {
        "skipped".to_string()
    } else if report.counts.skipped > 0 {
        "partial".to_string()
    } else {
        "ok".to_string()
    };
}

fn apply_sonoma_cross_check_runner_results(
    report: &mut SonomaCrossCheckReport,
    runner_result: &Value,
) {
    if report.status == "unavailable" {
        return;
    }
    if report.runner_pid.is_none() {
        if let Some(pid) = runner_result.get("pid").and_then(|v| v.as_i64()) {
            report.runner_pid = Some(pid);
        }
    }

    let mut by_id: BTreeMap<String, String> = BTreeMap::new();
    if let Some(steps) = runner_result.get("steps").and_then(|v| v.as_array()) {
        for step in steps {
            let step_id = match step.get("step_id").and_then(|v| v.as_str()) {
                Some(v) => v,
                None => continue,
            };
            let outcome = step
                .get("sandbox_check")
                .and_then(|v| v.get("outcome"))
                .and_then(|v| v.as_str());
            if let Some(outcome) = outcome {
                by_id.insert(step_id.to_string(), outcome.to_string());
            }
        }
    }

    for step in report.steps.iter_mut() {
        if let Some(expected) = by_id.get(&step.step_id) {
            step.expected_outcome = Some(expected.clone());
            if let Some(actual) = step.validator_outcome.as_ref() {
                if (expected == "allow" || expected == "deny")
                    && (actual == "allow" || actual == "deny")
                {
                    step.mismatch = Some(actual != expected);
                }
            }
        }
    }
    update_sonoma_cross_check_counts(report);
}

fn sonoma_cross_check_unavailable(error: String) -> SonomaCrossCheckReport {
    SonomaCrossCheckReport {
        status: "unavailable".to_string(),
        tool_path: None,
        runner_pid: None,
        wait_ms: None,
        error: Some(error),
        counts: SonomaCrossCheckCounts::default(),
        steps: Vec::new(),
    }
}

fn sonoma_cross_check_skipped(reason: String) -> SonomaCrossCheckReport {
    SonomaCrossCheckReport {
        status: "skipped".to_string(),
        tool_path: None,
        runner_pid: None,
        wait_ms: None,
        error: Some(reason),
        counts: SonomaCrossCheckCounts::default(),
        steps: Vec::new(),
    }
}

fn run_sonoma_cross_check(plan: &SonomaCrossCheckPlan) -> SonomaCrossCheckReport {
    let mut report = SonomaCrossCheckReport {
        status: "error".to_string(),
        tool_path: Some(plan.tool_path.display().to_string()),
        runner_pid: None,
        wait_ms: Some(plan.wait_ms),
        error: None,
        counts: SonomaCrossCheckCounts::default(),
        steps: Vec::new(),
    };

    let pid_timeout =
        SONOMA_CROSS_CHECK_PID_TIMEOUT_MS.max(plan.wait_ms.saturating_sub(SONOMA_CROSS_CHECK_SETTLE_MS));
    let pid = match wait_for_runner_pid(&plan.process_name, pid_timeout) {
        Ok(pid) => pid,
        Err(err) => {
            report.error = Some(err);
            update_sonoma_cross_check_counts(&mut report);
            return report;
        }
    };
    report.runner_pid = Some(pid);

    thread::sleep(Duration::from_millis(SONOMA_CROSS_CHECK_SETTLE_MS));

    for spec in &plan.specs {
        report
            .steps
            .push(run_sb_api_validator(&plan.tool_path, pid, spec));
    }

    update_sonoma_cross_check_counts(&mut report);
    report
}

fn cmd_run(args: &[OsString]) -> Result<i32, String> {
    let mut request_path: Option<PathBuf> = None;
    let mut timeout_ms = DEFAULT_TIMEOUT_MS;
    let mut log_last = DEFAULT_LOG_LAST.to_string();
    let mut instrumentation_arg: Option<String> = None;
    let mut sonoma_cross_check_enabled = false;

    let mut idx = 0usize;
    while idx < args.len() {
        let arg = args[idx].to_string_lossy();
        if arg == "--" {
            break;
        }
        if !arg.starts_with('-') {
            request_path = Some(PathBuf::from(args[idx].clone()));
            idx += 1;
            continue;
        }
        match arg.as_ref() {
            "-h" | "--help" => {
                print_usage();
                return Ok(0);
            }
            "--timeout-ms" => {
                let value = args
                    .get(idx + 1)
                    .and_then(|s| s.to_string_lossy().parse::<u64>().ok())
                    .ok_or_else(|| "invalid value for --timeout-ms".to_string())?;
                timeout_ms = value.max(1);
                idx += 2;
            }
            "--log-last" => {
                let value = args
                    .get(idx + 1)
                    .and_then(|s| s.to_str())
                    .ok_or_else(|| "missing value for --log-last".to_string())?;
                log_last = value.to_string();
                idx += 2;
            }
            "--instrumentation" => {
                let value = args
                    .get(idx + 1)
                    .and_then(|s| s.to_str())
                    .ok_or_else(|| "missing value for --instrumentation".to_string())?;
                instrumentation_arg = Some(value.to_string());
                idx += 2;
            }
            "--sonoma-cross-check" => {
                sonoma_cross_check_enabled = true;
                idx += 1;
            }
            _ => return Err(format!("unknown argument: {arg}")),
        }
    }

    let request_path = request_path.ok_or_else(|| "missing <request.json>".to_string())?;
    if !request_path.exists() {
        return Err(format!("request.json not found: {}", request_path.display()));
    }

    let app_root = app_root_from_current_exe()?;
    let app_provenance = load_app_provenance(&app_root).ok();
    let selector = parse_runner_selector(&request_path)?;
    let runner_target = resolve_runner_target(&app_root, &selector)?;
    let runner_provenance = runner_provenance_from_target(&runner_target);

    let mut request_value: Option<Value> = None;
    let mut request_modified = false;

    if instrumentation_arg.is_some() || sonoma_cross_check_enabled {
        request_value = Some(read_json_file(&request_path, "request.json")?);
    }

    if let Some(arg) = instrumentation_arg.as_deref() {
        let instrumentation = load_instrumentation_value(arg)?;
        let request_value_mut = request_value
            .as_mut()
            .ok_or_else(|| "request.json unavailable".to_string())?;
        let obj = request_value_mut
            .as_object_mut()
            .ok_or_else(|| "request.json must be a JSON object".to_string())?;
        if obj.contains_key("instrumentation") {
            return Err("request.json already includes instrumentation; remove it or omit --instrumentation".to_string());
        }
        obj.insert("instrumentation".to_string(), instrumentation);
        request_modified = true;
    }

    let mut sonoma_cross_check_report: Option<SonomaCrossCheckReport> = None;
    let mut sonoma_cross_check_plan: Option<SonomaCrossCheckPlan> = None;

    if sonoma_cross_check_enabled {
        let specs = extract_sonoma_cross_check_specs(
            request_value
                .as_ref()
                .ok_or_else(|| "request.json unavailable".to_string())?,
        )?;
        if specs.is_empty() {
            sonoma_cross_check_report =
                Some(sonoma_cross_check_skipped("no sandbox_check steps".to_string()));
        } else {
            match resolve_contents_macos_tool("sb_api_validator") {
                Ok(tool_path) => {
                    let wait_ms = sonoma_cross_check_wait_ms(specs.len());
                    let request_value_mut = request_value
                        .as_mut()
                        .ok_or_else(|| "request.json unavailable".to_string())?;
                    inject_sonoma_cross_check_instrumentation(request_value_mut, wait_ms)?;
                    request_modified = true;
                    sonoma_cross_check_plan = Some(SonomaCrossCheckPlan {
                        tool_path,
                        process_name: runner_target.process_name.clone(),
                        wait_ms,
                        specs,
                    });
                }
                Err(err) => {
                    sonoma_cross_check_report = Some(sonoma_cross_check_unavailable(err));
                }
            }
        }
    }

    let request_path_for_runner = if request_modified {
        let value = request_value
            .as_ref()
            .ok_or_else(|| "request.json unavailable".to_string())?;
        write_temp_request(value)?
    } else {
        request_path.clone()
    };

    let (runner_client, runner_result, sonoma_cross_check_from_run) =
        if let Some(plan) = sonoma_cross_check_plan {
            run_pw_runner_client_with_cross_check(
                &runner_target.service_name,
                &request_path_for_runner,
                timeout_ms,
                plan,
            )?
        } else {
            let (runner_client, runner_result) =
                run_pw_runner_client(&runner_target.service_name, &request_path_for_runner, timeout_ms)?;
            (runner_client, runner_result, None)
        };

    let mut sonoma_cross_check =
        sonoma_cross_check_report.or(sonoma_cross_check_from_run);

    if let (Some(report), Some(result)) = (sonoma_cross_check.as_mut(), runner_result.as_ref()) {
        apply_sonoma_cross_check_runner_results(report, result);
    }

    let runner_pid = runner_result
        .as_ref()
        .and_then(|v| v.get("pid"))
        .and_then(|v| v.as_i64());
    let runner_outcome = runner_result
        .as_ref()
        .and_then(|v| v.get("normalized_outcome"))
        .and_then(|v| v.as_str())
        .unwrap_or("runner_output_not_json")
        .to_string();
    let ok = runner_outcome == "ok";

    let mut sandbox_log_capture = runner_pid.map(|pid| {
        capture_sandbox_logs_last(pid, &runner_target.process_name, &log_last).unwrap_or_else(|err| {
            SandboxLogCapture {
                capture_status: "requested_unavailable".to_string(),
                tool_exit_code: 1,
                blocked_reason: None,
                stdout_parse_error: None,
                stdout_truncated: false,
                stdout_raw: None,
                stderr: err,
                stderr_truncated: false,
                observer: None,
                observed_deny: None,
                deny_events: None,
                step_denies: None,
            }
        })
    });

    if let (Some(ref mut capture), Some(steps)) = (
        sandbox_log_capture.as_mut(),
        runner_result
            .as_ref()
            .and_then(|v| v.get("steps"))
            .and_then(|v| v.as_array()),
    ) {
        if let Some(deny_events) = capture.deny_events.as_ref() {
            let matches = match_step_denies(steps, deny_events, runner_pid);
            if !matches.is_empty() {
                capture.step_denies = Some(matches);
            }
        }
    }

    let data = RunData {
        request_path: request_path.to_string_lossy().to_string(),
        runner_service_bundle_id: runner_target
            .bundle_id
            .clone()
            .unwrap_or_else(|| runner_target.service_name.clone()),
        runner_service_executable: runner_target.process_name.clone(),
        runner_service_name: runner_target.service_name,
        runner_registry_id: runner_provenance.runner_registry_id.clone(),
        runner_provenance,
        app_provenance,
        timeout_ms,
        log_last,
        runner_client,
        runner_result,
        sandbox_log_capture,
        sonoma_cross_check,
    };

    let error = if ok {
        None
    } else if let Some(v) = data
        .runner_result
        .as_ref()
        .and_then(|v| v.get("error"))
        .and_then(|v| v.as_str())
    {
        Some(v.to_string())
    } else if let Some(v) = data.runner_client.stdout_parse_error.as_ref() {
        Some(format!("runner output parse error: {v}"))
    } else {
        Some("run did not complete successfully".to_string())
    };

    let result = json_contract::JsonResult {
        ok,
        rc: None,
        exit_code: Some(if ok { 0 } else { 1 }),
        normalized_outcome: Some(runner_outcome),
        errno: None,
        error,
        stderr: None,
        stdout: None,
    };

    json_contract::print_envelope("run", result, &data)?;
    Ok(if ok { 0 } else { 1 })
}

#[derive(Serialize)]
struct RunnerInstallData {
    runner: RunnerRecord,
    plist_path: String,
    bootstrapped: bool,
}

#[derive(Serialize)]
struct RunnerRemoveData {
    runner_id: String,
    service_name: String,
    plist_path: String,
    booted_out: bool,
}

#[derive(Serialize)]
struct RunnerVerifyData {
    runner_id: Option<String>,
    service_name: String,
    runner_pid: Option<i64>,
    normalized_outcome: String,
}

#[derive(Serialize)]
struct RunnerRefreshData {
    updated: usize,
    missing: usize,
}

fn runner_usage() -> String {
    "\
usage:
  policy-witness runner install --bundle <path> [--service-name <name>] [--scope user|system]
                               [--identity <codesign-id>] [--entitlements <plist>]
                               [--executable <path>] [--bundle-id <id>] [--allow-adhoc]
                               [--env KEY=VALUE]
                               [--skip-bootstrap]
  policy-witness runner list
  policy-witness runner status --id <runner-id> | --service-name <name>
  policy-witness runner verify --id <runner-id> | --service-name <name> [--timeout-ms <n>]
  policy-witness runner remove --id <runner-id> | --service-name <name> [--skip-bootout]
  policy-witness runner refresh
"
    .to_string()
}

fn read_bundle_info(bundle_path: &Path) -> Result<(String, String), String> {
    let plist = bundle_path.join("Contents").join("Info.plist");
    if !plist.exists() {
        return Err(format!("missing Info.plist at {}", plist.display()));
    }
    let bundle_id = plist_key_string(&plist, "CFBundleIdentifier")?;
    let executable = plist_key_string(&plist, "CFBundleExecutable")?;
    Ok((bundle_id, executable))
}

fn load_registry_or_default() -> Result<(PathBuf, RunnerRegistry), String> {
    let registry_path = runner_manager::runner_registry_path()?;
    let registry = runner_manager::load_registry(&registry_path)?;
    Ok((registry_path, registry))
}

fn cmd_runner_install(args: &[OsString]) -> Result<i32, String> {
    let mut bundle_path: Option<PathBuf> = None;
    let mut service_name: Option<String> = None;
    let mut scope = RunnerScope::User;
    let mut identity: Option<String> = None;
    let mut entitlements_path: Option<PathBuf> = None;
    let mut executable_override: Option<PathBuf> = None;
    let mut bundle_id_override: Option<String> = None;
    let mut allow_adhoc = false;
    let mut skip_bootstrap = false;
    let mut env: BTreeMap<String, String> = BTreeMap::new();

    let mut idx = 0;
    while idx < args.len() {
        let arg = args[idx].to_string_lossy();
        match arg.as_ref() {
            "--bundle" => {
                let path = args.get(idx + 1).ok_or_else(|| "missing value for --bundle".to_string())?;
                bundle_path = Some(PathBuf::from(path));
                idx += 2;
            }
            "--service-name" => {
                let name = args.get(idx + 1).ok_or_else(|| "missing value for --service-name".to_string())?;
                service_name = Some(name.to_string_lossy().to_string());
                idx += 2;
            }
            "--scope" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --scope".to_string())?;
                let scope_str = value.to_string_lossy();
                scope = RunnerScope::parse(scope_str.as_ref())
                    .ok_or_else(|| "invalid value for --scope".to_string())?;
                idx += 2;
            }
            "--identity" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --identity".to_string())?;
                identity = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--entitlements" => {
                let path = args.get(idx + 1).ok_or_else(|| "missing value for --entitlements".to_string())?;
                entitlements_path = Some(PathBuf::from(path));
                idx += 2;
            }
            "--executable" => {
                let path = args.get(idx + 1).ok_or_else(|| "missing value for --executable".to_string())?;
                executable_override = Some(PathBuf::from(path));
                idx += 2;
            }
            "--bundle-id" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --bundle-id".to_string())?;
                bundle_id_override = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--allow-adhoc" => {
                allow_adhoc = true;
                idx += 1;
            }
            "--env" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --env".to_string())?;
                let raw = value.to_string_lossy();
                let (key, val) = raw
                    .split_once('=')
                    .ok_or_else(|| "invalid --env (expected KEY=VALUE)".to_string())?;
                if key.is_empty() {
                    return Err("invalid --env (empty key)".to_string());
                }
                env.insert(key.to_string(), val.to_string());
                idx += 2;
            }
            "--skip-bootstrap" => {
                skip_bootstrap = true;
                idx += 1;
            }
            _ => return Err(format!("unknown argument: {arg}")),
        }
    }

    let bundle_path = bundle_path.ok_or_else(|| "missing --bundle".to_string())?;
    if !bundle_path.exists() {
        return Err(format!("bundle path not found: {}", bundle_path.display()));
    }

    let (bundle_id, executable_name) = if bundle_path.is_dir() {
        read_bundle_info(&bundle_path)?
    } else {
        (
            bundle_id_override.clone().unwrap_or_else(|| "unknown".to_string()),
            bundle_path
                .file_name()
                .and_then(|v| v.to_str())
                .ok_or_else(|| "invalid bundle path".to_string())?
                .to_string(),
        )
    };
    let executable_path = if let Some(override_path) = executable_override {
        override_path
    } else if bundle_path.is_dir() {
        bundle_path
            .join("Contents")
            .join("MacOS")
            .join(&executable_name)
    } else {
        bundle_path.clone()
    };
    if !executable_path.exists() {
        return Err(format!(
            "executable path not found: {}",
            executable_path.display()
        ));
    }

    let sign_target = if bundle_path.is_dir() {
        bundle_path.clone()
    } else {
        executable_path.clone()
    };
    if let Some(identity) = identity.as_ref() {
        runner_manager::codesign_sign(
            &sign_target,
            identity,
            entitlements_path.as_deref(),
        )?;
    }
    runner_manager::codesign_verify(&sign_target)?;
    let signature = runner_manager::codesign_metadata(&executable_path)?;
    if signature.adhoc && !allow_adhoc {
        return Err("runner is ad-hoc signed; pass --allow-adhoc to accept".to_string());
    }

    let entitlements = if let Some(entitlements_path) = entitlements_path.as_deref() {
        runner_manager::entitlements_from_plist_path(entitlements_path)
    } else {
        runner_manager::entitlements_from_codesign(&executable_path)
    };

    let runner_id = runner_manager::random_id()?;
    let service_name = service_name.unwrap_or_else(|| runner_manager::generate_service_name(&runner_id));
    let plist_path = runner_manager::launchd_plist_path(&service_name, scope)?;
    let plist_contents = runner_manager::build_launchd_plist(
        &service_name,
        &executable_path,
        if env.is_empty() { None } else { Some(&env) },
    );
    runner_manager::write_launchd_plist(&plist_path, &plist_contents)?;
    if !skip_bootstrap {
        runner_manager::launchctl_bootstrap(scope, &plist_path)?;
    }

    let record = RunnerRecord {
        id: runner_id.clone(),
        service_name: service_name.clone(),
        bundle_path: bundle_path.display().to_string(),
        executable_path: executable_path.display().to_string(),
        bundle_id: Some(bundle_id),
        scope,
        protocol_version: runner_manager::RUNNER_PROTOCOL_VERSION,
        signature,
        entitlements,
        installed_at_unix_ms: now_unix_ms(),
    };

    let (registry_path, mut registry) = load_registry_or_default()?;
    if registry
        .runners
        .iter()
        .any(|r| r.id == record.id || r.service_name == record.service_name)
    {
        return Err("runner id or service name already registered".to_string());
    }
    registry.runners.push(record.clone());
    runner_manager::save_registry(&registry_path, &registry)?;

    let data = RunnerInstallData {
        runner: record,
        plist_path: plist_path.display().to_string(),
        bootstrapped: !skip_bootstrap,
    };
    let result = json_contract::JsonResult {
        ok: true,
        rc: None,
        exit_code: Some(0),
        normalized_outcome: Some("ok".to_string()),
        errno: None,
        error: None,
        stderr: None,
        stdout: None,
    };
    json_contract::print_envelope("runner_install", result, &data)?;
    Ok(0)
}

fn cmd_runner_list() -> Result<i32, String> {
    let (_, registry) = load_registry_or_default()?;
    let result = json_contract::JsonResult {
        ok: true,
        rc: None,
        exit_code: Some(0),
        normalized_outcome: Some("ok".to_string()),
        errno: None,
        error: None,
        stderr: None,
        stdout: None,
    };
    json_contract::print_envelope("runner_registry", result, &registry)?;
    Ok(0)
}

fn cmd_runner_status(args: &[OsString]) -> Result<i32, String> {
    let mut runner_id: Option<String> = None;
    let mut service_name: Option<String> = None;

    let mut idx = 0;
    while idx < args.len() {
        let arg = args[idx].to_string_lossy();
        match arg.as_ref() {
            "--id" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --id".to_string())?;
                runner_id = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--service-name" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --service-name".to_string())?;
                service_name = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            _ => return Err(format!("unknown argument: {arg}")),
        }
    }

    let (_, registry) = load_registry_or_default()?;
    let record = if let Some(id) = runner_id.as_ref() {
        registry.runners.iter().find(|r| &r.id == id)
    } else if let Some(service) = service_name.as_ref() {
        registry.runners.iter().find(|r| &r.service_name == service)
    } else {
        None
    }
    .ok_or_else(|| "runner not found in registry".to_string())?;

    let result = json_contract::JsonResult {
        ok: true,
        rc: None,
        exit_code: Some(0),
        normalized_outcome: Some("ok".to_string()),
        errno: None,
        error: None,
        stderr: None,
        stdout: None,
    };
    json_contract::print_envelope("runner_status", result, record)?;
    Ok(0)
}

fn cmd_runner_verify(args: &[OsString]) -> Result<i32, String> {
    let mut runner_id: Option<String> = None;
    let mut service_name: Option<String> = None;
    let mut timeout_ms: u64 = DEFAULT_TIMEOUT_MS;

    let mut idx = 0;
    while idx < args.len() {
        let arg = args[idx].to_string_lossy();
        match arg.as_ref() {
            "--id" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --id".to_string())?;
                runner_id = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--service-name" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --service-name".to_string())?;
                service_name = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--timeout-ms" => {
                let value = args
                    .get(idx + 1)
                    .and_then(|s| s.to_string_lossy().parse::<u64>().ok())
                    .ok_or_else(|| "invalid value for --timeout-ms".to_string())?;
                timeout_ms = value.max(1);
                idx += 2;
            }
            _ => return Err(format!("unknown argument: {arg}")),
        }
    }

    let (_, registry) = load_registry_or_default()?;
    let record = if let Some(id) = runner_id.as_ref() {
        registry.runners.iter().find(|r| &r.id == id)
    } else if let Some(service) = service_name.as_ref() {
        registry.runners.iter().find(|r| &r.service_name == service)
    } else {
        None
    }
    .ok_or_else(|| "runner not found in registry".to_string())?;

    let temp_dir = std::env::temp_dir()
        .join("pw-runner-verify");
    std::fs::create_dir_all(&temp_dir)
        .map_err(|e| format!("failed to create temp dir: {e}"))?;
    let request_path = temp_dir.join(format!("verify-{}.json", now_unix_ms()));

    let spec = json!({
        "schema_version": 1,
        "specimen_id": "runner_verify",
        "run_kind": "runner_verify",
        "policy": {
            "format": "sbpl",
            "sbpl_source": "(version 1)\n(allow default)\n"
        },
        "probe_plan": []
    });
    std::fs::write(&request_path, serde_json::to_string_pretty(&spec).unwrap())
        .map_err(|e| format!("failed to write verify request: {e}"))?;

    let (_, runner_result) =
        run_pw_runner_client(&record.service_name, &request_path, timeout_ms)?;
    let runner_pid = runner_result
        .as_ref()
        .and_then(|v| v.get("pid"))
        .and_then(|v| v.as_i64());
    let outcome = runner_result
        .as_ref()
        .and_then(|v| v.get("normalized_outcome"))
        .and_then(|v| v.as_str())
        .unwrap_or("runner_output_not_json")
        .to_string();

    let ok = outcome == "ok";
    let data = RunnerVerifyData {
        runner_id: Some(record.id.clone()),
        service_name: record.service_name.clone(),
        runner_pid,
        normalized_outcome: outcome.clone(),
    };
    let result = json_contract::JsonResult {
        ok,
        rc: None,
        exit_code: Some(if ok { 0 } else { 1 }),
        normalized_outcome: Some(outcome),
        errno: None,
        error: None,
        stderr: None,
        stdout: None,
    };
    json_contract::print_envelope("runner_verify", result, &data)?;
    Ok(if ok { 0 } else { 1 })
}

fn cmd_runner_remove(args: &[OsString]) -> Result<i32, String> {
    let mut runner_id: Option<String> = None;
    let mut service_name: Option<String> = None;
    let mut skip_bootout = false;

    let mut idx = 0;
    while idx < args.len() {
        let arg = args[idx].to_string_lossy();
        match arg.as_ref() {
            "--id" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --id".to_string())?;
                runner_id = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--service-name" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --service-name".to_string())?;
                service_name = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--skip-bootout" => {
                skip_bootout = true;
                idx += 1;
            }
            _ => return Err(format!("unknown argument: {arg}")),
        }
    }

    let (registry_path, mut registry) = load_registry_or_default()?;
    let idx = if let Some(id) = runner_id.as_ref() {
        registry.runners.iter().position(|r| &r.id == id)
    } else if let Some(service) = service_name.as_ref() {
        registry.runners.iter().position(|r| &r.service_name == service)
    } else {
        None
    }
    .ok_or_else(|| "runner not found in registry".to_string())?;

    let record = registry.runners.remove(idx);
    let plist_path = runner_manager::launchd_plist_path(&record.service_name, record.scope)?;
    if !skip_bootout {
        runner_manager::launchctl_bootout(record.scope, &plist_path)?;
    }
    if plist_path.exists() {
        std::fs::remove_file(&plist_path)
            .map_err(|e| format!("failed to remove plist {}: {e}", plist_path.display()))?;
    }
    runner_manager::save_registry(&registry_path, &registry)?;

    let data = RunnerRemoveData {
        runner_id: record.id,
        service_name: record.service_name,
        plist_path: plist_path.display().to_string(),
        booted_out: !skip_bootout,
    };
    let result = json_contract::JsonResult {
        ok: true,
        rc: None,
        exit_code: Some(0),
        normalized_outcome: Some("ok".to_string()),
        errno: None,
        error: None,
        stderr: None,
        stdout: None,
    };
    json_contract::print_envelope("runner_remove", result, &data)?;
    Ok(0)
}

fn cmd_runner_refresh() -> Result<i32, String> {
    let (registry_path, mut registry) = load_registry_or_default()?;
    let mut missing = 0usize;
    for record in registry.runners.iter_mut() {
        let exec_path = Path::new(&record.executable_path);
        if !exec_path.exists() {
            missing += 1;
            record.signature.valid = false;
            record.entitlements.error = Some("executable missing".to_string());
            continue;
        }
        if let Ok(sig) = runner_manager::codesign_metadata(exec_path) {
            record.signature = sig;
        }
        record.entitlements = runner_manager::entitlements_from_codesign(exec_path);
    }
    let updated = registry.runners.len();
    runner_manager::save_registry(&registry_path, &registry)?;

    let data = RunnerRefreshData { updated, missing };
    let result = json_contract::JsonResult {
        ok: true,
        rc: None,
        exit_code: Some(0),
        normalized_outcome: Some("ok".to_string()),
        errno: None,
        error: None,
        stderr: None,
        stdout: None,
    };
    json_contract::print_envelope("runner_refresh", result, &data)?;
    Ok(0)
}

fn cmd_runner(args: &[OsString]) -> Result<i32, String> {
    if args.is_empty() {
        return Err(format!("missing runner command\n\n{}", runner_usage()));
    }
    let sub = args[0].to_string_lossy().to_string();
    let rest = &args[1..];
    match sub.as_str() {
        "install" => cmd_runner_install(rest),
        "list" => cmd_runner_list(),
        "status" => cmd_runner_status(rest),
        "verify" => cmd_runner_verify(rest),
        "remove" => cmd_runner_remove(rest),
        "refresh" => cmd_runner_refresh(),
        "-h" | "--help" | "help" => {
            println!("{}", runner_usage());
            Ok(0)
        }
        _ => Err(format!("unknown runner command: {sub}\n\n{}", runner_usage())),
    }
}

fn main() {
    let argv: Vec<OsString> = std::env::args_os().skip(1).collect();
    if argv.is_empty() {
        print_usage();
        std::process::exit(2);
    }

    let sub = argv[0].to_string_lossy().to_string();
    let rest = &argv[1..];

    if sub == "-h" || sub == "--help" || sub == "help" {
        print_usage();
        std::process::exit(0);
    }

    match sub.as_str() {
        "run" => match cmd_run(rest) {
            Ok(code) => std::process::exit(code),
            Err(err) => {
                let result = json_contract::JsonResult {
                    ok: false,
                    rc: None,
                    exit_code: Some(2),
                    normalized_outcome: Some("tool_error".to_string()),
                    errno: None,
                    error: Some(err),
                    stderr: None,
                    stdout: None,
                };
                let data =
                    json!({"error": "policy-witness run failed before producing a runner result"});
                let _ = json_contract::print_envelope("run", result, &data);
                std::process::exit(2);
            }
        },
        "runner" => match cmd_runner(rest) {
            Ok(code) => std::process::exit(code),
            Err(err) => {
                eprintln!("{err}");
                std::process::exit(2);
            }
        },
        _ => {
            print_usage();
            std::process::exit(2);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
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
                "required_entitlements": ["com.apple.security.cs.allow-jit"]
            }
        });
        fs::write(&path, serde_json::to_string(&payload).unwrap()).unwrap();
        let selector = parse_runner_selector(&path).expect("parse selector");
        assert_eq!(selector.runner_id.as_deref(), Some("runner-abc"));
        assert_eq!(selector.runner_service.as_deref(), Some("com.example.runner"));
        assert_eq!(selector.required_entitlements.len(), 1);
        let _ = fs::remove_file(&path);
    }
}
