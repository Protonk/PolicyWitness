use serde::{Deserialize, Serialize};
use serde_json::{json, Map, Value};
use std::ffi::{c_char, c_void, CString, OsString};
use std::path::{Component, Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::{SystemTime, UNIX_EPOCH};

const LABBOOK_VERSION: u32 = 1;

const PW_RUNNER_SERVICE_DIR: &str = "PWRunner";

const SANDBOX_FILTER_GLOBAL_NAME: i32 = 16;

const DEFAULT_TIMEOUT_MS: u64 = 240_000;
const DEFAULT_LOG_LAST: &str = "10s";

// RTLD_DEFAULT in C is ((void *) -2)
const RTLD_DEFAULT: *mut c_void = (-2isize) as *mut c_void;

type SandboxCheckNoArgFn = unsafe extern "C" fn(pid: i32, operation: *const c_char, filter: i32) -> i32;
type SandboxCheckOneArgFn =
    unsafe extern "C" fn(pid: i32, operation: *const c_char, filter: i32, arg: *const c_char) -> i32;

unsafe extern "C" {
    fn dlsym(handle: *mut c_void, symbol: *const c_char) -> *mut c_void;
}

fn print_usage() {
    eprintln!(
        "\
usage:
  policy-witness inside [--service-name <mach-service-name> ...] [--bare]
  policy-witness specimen <specimen.json> [--outdir <dir>] [--timeout-ms <n>] [--log-last <dur>] [--force]

notes:
  - `specimen` runs a canonical run plus an instrumented run (SBPL `message` marker on deny) and writes a labbook directory."
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

fn ensure_clean_dir(path: &Path, force: bool) -> Result<(), String> {
    if path.exists() {
        let mut entries = std::fs::read_dir(path)
            .map_err(|e| format!("failed to read {}: {e}", path.display()))?;
        if entries.next().is_some() {
            if !force {
                return Err(format!("output directory not empty: {}", path.display()));
            }
            std::fs::remove_dir_all(path)
                .map_err(|e| format!("failed to remove {}: {e}", path.display()))?;
        }
    }
    std::fs::create_dir_all(path)
        .map_err(|e| format!("failed to create {}: {e}", path.display()))?;
    Ok(())
}

fn write_text(path: &Path, content: &str) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        if !parent.as_os_str().is_empty() && parent != Path::new(".") {
            std::fs::create_dir_all(parent)
                .map_err(|e| format!("failed to create {}: {e}", parent.display()))?;
        }
    }
    std::fs::write(path, content).map_err(|e| format!("failed to write {}: {e}", path.display()))
}

fn write_json_pretty(path: &Path, mut value: Value) -> Result<(), String> {
    sort_json_value(&mut value);
    let text = serde_json::to_string_pretty(&value)
        .map_err(|e| format!("failed to encode JSON: {e}"))?;
    write_text(path, &(text + "\n"))
}

fn sort_json_value(value: &mut Value) {
    match value {
        Value::Array(items) => {
            for item in items {
                sort_json_value(item);
            }
        }
        Value::Object(map) => {
            let mut entries: Vec<(String, Value)> =
                map.iter().map(|(k, v)| (k.clone(), v.clone())).collect();
            entries.sort_by(|a, b| a.0.cmp(&b.0));
            let mut sorted = Map::new();
            for (key, mut val) in entries {
                sort_json_value(&mut val);
                sorted.insert(key, val);
            }
            *map = sorted;
        }
        _ => {}
    }
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

fn load_sandbox_check_symbol() -> Option<*mut c_void> {
    let sym = CString::new("sandbox_check").ok()?;
    let ptr = unsafe { dlsym(RTLD_DEFAULT, sym.as_ptr()) };
    if ptr.is_null() {
        None
    } else {
        Some(ptr)
    }
}

fn sandbox_check_mach_lookup(symbol: *mut c_void, name: &str) -> Option<bool> {
    let pid = std::process::id() as i32;
    let op = CString::new("mach-lookup").ok()?;
    let arg = CString::new(name).ok()?;
    let fn_ptr: SandboxCheckOneArgFn = unsafe { std::mem::transmute(symbol) };
    let rc = unsafe { fn_ptr(pid, op.as_ptr(), SANDBOX_FILTER_GLOBAL_NAME, arg.as_ptr()) };
    match rc {
        0 => Some(true),
        1 => Some(false),
        _ => None,
    }
}

fn sandbox_check_am_i_sandboxed(symbol: *mut c_void) -> Option<bool> {
    let pid = std::process::id() as i32;
    let fn_ptr: SandboxCheckNoArgFn = unsafe { std::mem::transmute(symbol) };
    let rc = unsafe { fn_ptr(pid, std::ptr::null(), 0) };
    match rc {
        0 => Some(false),
        1 => Some(true),
        _ => None,
    }
}

fn inside_probe(service_names: &[String]) -> Value {
    let mut checked: Vec<Value> = Vec::new();

    if let Ok(marker) = std::env::var("CODEX_SANDBOX") {
        if !marker.is_empty() {
            return json!({
                "inside": true,
                "trigger": "env:CODEX_SANDBOX",
                "checked": [
                    {"sensor": "env:CODEX_SANDBOX", "status": "triggered", "details": {"value": marker}}
                ],
                "service_names": service_names,
            });
        }
    }
    checked.push(json!({"sensor": "env:CODEX_SANDBOX", "status": "pass"}));

    let symbol = match load_sandbox_check_symbol() {
        Some(ptr) => ptr,
        None => {
            checked.push(json!({"sensor": "sandbox_check", "status": "unavailable"}));
            return json!({
                "inside": true,
                "trigger": "sandbox_check:unavailable",
                "checked": checked,
                "service_names": service_names,
            });
        }
    };

    if let Some(true) = sandbox_check_am_i_sandboxed(symbol) {
        checked.push(json!({"sensor": "sandbox_check:self", "status": "triggered"}));
        return json!({
            "inside": true,
            "trigger": "sandbox_check:self",
            "checked": checked,
            "service_names": service_names,
        });
    }
    checked.push(json!({"sensor": "sandbox_check:self", "status": "pass"}));

    // Always check logd lookup: if this is denied, unified-log collectors are often blocked.
    match sandbox_check_mach_lookup(symbol, "com.apple.logd") {
        Some(true) => checked.push(json!({"sensor": "sandbox_check:mach-lookup:com.apple.logd", "status": "pass"})),
        Some(false) => {
            checked.push(json!({"sensor": "sandbox_check:mach-lookup:com.apple.logd", "status": "triggered"}));
            return json!({
                "inside": true,
                "trigger": "sandbox_check:mach-lookup:com.apple.logd",
                "checked": checked,
                "service_names": service_names,
            });
        }
        None => {
            checked.push(json!({"sensor": "sandbox_check:mach-lookup:com.apple.logd", "status": "error"}));
            return json!({
                "inside": true,
                "trigger": "sandbox_check:error:com.apple.logd",
                "checked": checked,
                "service_names": service_names,
            });
        }
    }

    for name in service_names {
        match sandbox_check_mach_lookup(symbol, name) {
            Some(true) => checked.push(json!({"sensor": format!("sandbox_check:mach-lookup:{name}"), "status": "pass"})),
            Some(false) => {
                checked.push(json!({"sensor": format!("sandbox_check:mach-lookup:{name}"), "status": "triggered"}));
                return json!({
                    "inside": true,
                    "trigger": format!("sandbox_check:mach-lookup:{name}"),
                    "checked": checked,
                    "service_names": service_names,
                });
            }
            None => {
                checked.push(json!({"sensor": format!("sandbox_check:mach-lookup:{name}"), "status": "error"}));
                return json!({
                    "inside": true,
                    "trigger": format!("sandbox_check:error:{name}"),
                    "checked": checked,
                    "service_names": service_names,
                });
            }
        }
    }

    json!({
        "inside": false,
        "trigger": null,
        "checked": checked,
        "service_names": service_names,
    })
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SpecimenFile {
    specimen_id: Option<String>,
    policy: PWRunnerPolicySpec,
    #[serde(default)]
    instrumented_policy: Option<PWRunnerPolicySpec>,
    probe_plan: Vec<PWRunnerProbeStep>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct PWRunnerPolicySpec {
    format: String,
    #[serde(default)]
    sbpl_source: Option<String>,
    #[serde(default)]
    params: Option<Map<String, Value>>,
    #[serde(default)]
    compiled_profile_b64: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct PWRunnerSandboxFilter {
    kind: String,
    #[serde(default)]
    value: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct PWRunnerSandboxCheck {
    operation: String,
    filter: PWRunnerSandboxFilter,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct PWRunnerAttempt {
    kind: String,
    action: String,
    target: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct PWRunnerProbeStep {
    step_id: String,
    sandbox_check: PWRunnerSandboxCheck,
    attempt: PWRunnerAttempt,
}

#[derive(Serialize)]
struct PWRunnerRunRequest {
    schema_version: u32,
    specimen_id: String,
    run_kind: String,
    policy: PWRunnerPolicySpec,
    probe_plan: Vec<PWRunnerProbeStep>,
}

fn load_specimen(path: &Path) -> Result<SpecimenFile, String> {
    let text = std::fs::read_to_string(path)
        .map_err(|e| format!("failed to read specimen {}: {e}", path.display()))?;
    serde_json::from_str(&text)
        .map_err(|e| format!("failed to parse specimen JSON {}: {e}", path.display()))
}

fn escape_sbpl_string(input: &str) -> String {
    input.replace('\\', "\\\\").replace('"', "\\\"")
}

fn instrument_sbpl_message_marker(sbpl: &str, message: &str) -> String {
    // Best-effort transformation: add `(with message "...")` to each `(deny ...)` form.
    // Keep this intentionally narrow: SBPL is ASCII; refuse to reason about complex cases.
    let bytes = sbpl.as_bytes();
    let mut spans: Vec<(usize, usize)> = Vec::new();

    let mut in_string = false;
    let mut escape = false;

    fn is_sym_char(b: u8) -> bool {
        matches!(b, b'a'..=b'z' | b'A'..=b'Z' | b'0'..=b'9' | b'-' | b'_' | b'.')
    }

    let mut i = 0usize;
    while i < bytes.len() {
        let ch = bytes[i];
        if in_string {
            if escape {
                escape = false;
            } else if ch == b'\\' {
                escape = true;
            } else if ch == b'"' {
                in_string = false;
            }
            i += 1;
            continue;
        }

        if ch == b'"' {
            in_string = true;
            i += 1;
            continue;
        }

        if ch == b'(' {
            let mut j = i + 1;
            while j < bytes.len() && bytes[j].is_ascii_whitespace() {
                j += 1;
            }
            let mut k = j;
            while k < bytes.len() && is_sym_char(bytes[k]) {
                k += 1;
            }
            if j < k && &sbpl[j..k] == "deny" {
                let mut form_depth = 1i32;
                let mut m = k;
                let mut local_in_string = false;
                let mut local_escape = false;
                while m < bytes.len() {
                    let c2 = bytes[m];
                    if local_in_string {
                        if local_escape {
                            local_escape = false;
                        } else if c2 == b'\\' {
                            local_escape = true;
                        } else if c2 == b'"' {
                            local_in_string = false;
                        }
                        m += 1;
                        continue;
                    }
                    if c2 == b'"' {
                        local_in_string = true;
                        m += 1;
                        continue;
                    }
                    if c2 == b'(' {
                        form_depth += 1;
                    } else if c2 == b')' {
                        form_depth -= 1;
                        if form_depth == 0 {
                            spans.push((i, m));
                            break;
                        }
                    }
                    m += 1;
                }
            }
            i += 1;
            continue;
        }

        i += 1;
    }

    if spans.is_empty() {
        return sbpl.to_string();
    }

    let escaped = escape_sbpl_string(message);
    let suffix = format!(" (with message \"{escaped}\")");
    let mut out = sbpl.to_string();
    for (start, end) in spans.into_iter().rev() {
        if end >= out.len() || start >= out.len() || start > end {
            continue;
        }
        let segment = &out[start..=end];
        if segment.contains("with message") {
            continue;
        }
        out.insert_str(end, &suffix);
    }
    out
}

#[derive(Serialize)]
struct ClientRunArtifact {
    exit_code: i32,
    started_at_unix_ms: u64,
    ended_at_unix_ms: u64,
    parse_error: Option<String>,
    parsed: Option<Value>,
}

fn run_pw_runner_client(
    service_bundle_id: &str,
    request_path: &Path,
    out_dir: &Path,
    timeout_ms: u64,
) -> Result<ClientRunArtifact, String> {
    let tool = resolve_contents_macos_tool("pw-runner-client")?;
    ensure_clean_dir(out_dir, true)?;

    let cmd = vec![
        tool.into_os_string(),
        OsString::from("run"),
        OsString::from("--timeout-ms"),
        OsString::from(format!("{timeout_ms}")),
        OsString::from(service_bundle_id),
        request_path.as_os_str().to_os_string(),
    ];
    write_text(out_dir.join("cmd.txt").as_path(), &(format_cmd(&cmd) + "\n"))?;

    let start_ms = now_unix_ms();
    let out = Command::new(&cmd[0])
        .args(&cmd[1..])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run pw-runner-client: {e}"))?;
    let end_ms = now_unix_ms();

    write_text(out_dir.join("outputs.stdout.json").as_path(), &String::from_utf8_lossy(&out.stdout))?;
    write_text(out_dir.join("outputs.stderr.txt").as_path(), &String::from_utf8_lossy(&out.stderr))?;
    write_text(
        out_dir.join("outputs.exit_code.txt").as_path(),
        &format!("{}\n", out.status.code().unwrap_or(1)),
    )?;

    let stdout = String::from_utf8_lossy(&out.stdout);
    let mut parsed: Option<Value> = None;
    let mut parse_error: Option<String> = None;
    if !stdout.trim().is_empty() {
        match serde_json::from_str::<Value>(&stdout) {
            Ok(v) => parsed = Some(v),
            Err(e) => parse_error = Some(format!("{e}")),
        }
    }

    let run_json = json!({
        "schema_version": 1,
        "driver": "pw-runner-client",
        "started_at_unix_ms": start_ms,
        "ended_at_unix_ms": end_ms,
        "argv": cmd.iter().map(|s| s.to_string_lossy().to_string()).collect::<Vec<_>>(),
        "exit_code": out.status.code().unwrap_or(1),
        "parse_error": parse_error,
        "parsed": parsed,
    });
    write_json_pretty(out_dir.join("run.json").as_path(), run_json)?;

    Ok(ClientRunArtifact {
        exit_code: out.status.code().unwrap_or(1),
        started_at_unix_ms: start_ms,
        ended_at_unix_ms: end_ms,
        parse_error,
        parsed,
    })
}

fn format_cmd(argv: &[OsString]) -> String {
    argv.iter()
        .map(|s| shell_escape(s))
        .collect::<Vec<_>>()
        .join(" ")
}

fn shell_escape(s: &OsString) -> String {
    let text = s.to_string_lossy();
    if text.is_empty() {
        return "''".to_string();
    }
    if text.chars().all(|c| c.is_ascii_alphanumeric() || "-_./:@".contains(c)) {
        return text.to_string();
    }
    format!("'{}'", text.replace('\'', "'\\''"))
}

fn capture_sandbox_logs_last(
    pid: i64,
    process_name: &str,
    out_dir: &Path,
    last: &str,
) -> Result<Value, String> {
    let tool = resolve_contents_macos_tool("sandbox-log-observer")?;
    ensure_clean_dir(out_dir, true)?;

    let cmd = vec![
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
    write_text(out_dir.join("cmd.txt").as_path(), &(format_cmd(&cmd) + "\n"))?;

    let out = Command::new(&cmd[0])
        .args(&cmd[1..])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run sandbox-log-observer: {e}"))?;

    write_text(out_dir.join("outputs.stdout.json").as_path(), &String::from_utf8_lossy(&out.stdout))?;
    write_text(out_dir.join("outputs.stderr.txt").as_path(), &String::from_utf8_lossy(&out.stderr))?;
    write_text(
        out_dir.join("outputs.exit_code.txt").as_path(),
        &format!("{}\n", out.status.code().unwrap_or(1)),
    )?;

    let stdout = String::from_utf8_lossy(&out.stdout);
    let mut parsed: Option<Value> = None;
    let mut parse_error: Option<String> = None;
    if !stdout.trim().is_empty() {
        match serde_json::from_str::<Value>(&stdout) {
            Ok(v) => parsed = Some(v),
            Err(e) => parse_error = Some(format!("{e}")),
        }
    }

    let parse_error_clone = parse_error.clone();
    let mut out_obj = match parsed {
        Some(Value::Object(map)) => Value::Object(map),
        _ => json!({"capture_status": "requested_unavailable", "error": parse_error_clone.unwrap_or_else(|| "stdout not json".to_string())}),
    };

    if let Value::Object(map) = &mut out_obj {
        map.insert(
            "capture_status".to_string(),
            Value::String(if out.status.success() {
                "captured".to_string()
            } else {
                "requested_unavailable".to_string()
            }),
        );
        map.insert(
            "capture_parse_error".to_string(),
            parse_error.map(Value::String).unwrap_or(Value::Null),
        );
    }

    Ok(out_obj)
}

fn observed_deny_from_capture(obj: &Value) -> Option<bool> {
    if let Some(v) = obj.get("observed_deny").and_then(|v| v.as_bool()) {
        return Some(v);
    }
    obj.get("data")
        .and_then(|v| v.get("observed_deny"))
        .and_then(|v| v.as_bool())
}

fn summary_for_specimen_eval(
    specimen_id: &str,
    probe_plan: &[PWRunnerProbeStep],
    canonical: Option<&Value>,
    canonical_logs: Option<&Value>,
    instrumented_logs: Option<&Value>,
    deny_marker: &str,
    inside: &Value,
) -> Value {
    let mut plan_by_step: std::collections::HashMap<String, &PWRunnerProbeStep> = std::collections::HashMap::new();
    for entry in probe_plan {
        plan_by_step.insert(entry.step_id.clone(), entry);
    }

    let canon_steps = canonical.and_then(|v| v.get("steps")).and_then(|v| v.as_array());

    let mut marker_observed: Option<bool> = None;
    if !deny_marker.is_empty() {
        let logs_obj = instrumented_logs.or(canonical_logs);
        if let Some(logs_obj) = logs_obj {
            if let Some(log_stdout) = logs_obj
                .get("data")
                .and_then(|d| d.get("log_stdout"))
                .and_then(|v| v.as_str())
            {
                marker_observed = Some(log_stdout.contains(deny_marker));
            }
        }
    }

    let mut steps: Vec<Value> = Vec::new();
    if let Some(canon_steps) = canon_steps {
        for s in canon_steps {
            let sid = s.get("step_id").and_then(|v| v.as_str()).unwrap_or("-");
            let probe_id = plan_by_step
                .get(sid)
                .map(|entry| format!("{}:{}", entry.attempt.kind, entry.attempt.action))
                .unwrap_or_else(|| "-".to_string());

            let attempt = s.get("attempt").cloned().unwrap_or(Value::Null);
            let sb = s.get("sandbox_check").cloned().unwrap_or(Value::Null);
            let rc = attempt.get("rc").and_then(|v| v.as_i64());
            let err = attempt.get("errno").and_then(|v| v.as_i64());
            let sb_outcome = sb.get("outcome").and_then(|v| v.as_str()).unwrap_or("");

            let mut outcome = "ok".to_string();
            let mut ok = rc == Some(0);
            if rc != Some(0) && sb_outcome == "deny" {
                outcome = "failed_predicted_deny".to_string();
                ok = false;
            }
            if rc != Some(0) && sb_outcome == "allow" {
                outcome = "failed_predicted_allow".to_string();
                ok = false;
            }
            if rc == Some(0) && sb_outcome == "deny" {
                outcome = "mismatch_allow_but_predicted_deny".to_string();
                ok = false;
            }

            steps.push(json!({
                "step_id": sid,
                "probe_id": probe_id,
                "ok": ok,
                "normalized_outcome": outcome,
                "rc": rc,
                "errno": err,
                "probe_exec_overlap": null,
                "sandbox_check_outcome": sb_outcome,
                "deny_marker_observed": marker_observed,
            }));
        }
    }

    let mut observed_deny = canonical_logs.and_then(observed_deny_from_capture);
    if observed_deny != Some(true) {
        observed_deny = instrumented_logs.and_then(observed_deny_from_capture);
    }

    let mut confidence = "unknown".to_string();
    let mut reasons: Vec<String> = Vec::new();
    if observed_deny != Some(true) {
        reasons.push("sandbox_deny_not_observed".to_string());
    }
    if marker_observed != Some(true) {
        reasons.push("deny_marker_not_observed".to_string());
    }
    if observed_deny == Some(true) && marker_observed == Some(true) && !steps.is_empty() {
        confidence = "high".to_string();
    }

    let canonical_ok = canonical
        .and_then(|v| v.get("normalized_outcome"))
        .and_then(|v| v.as_str())
        == Some("ok");
    let status = if canonical_ok { "pass" } else { "fail" };

    json!({
        "labbook_version": LABBOOK_VERSION,
        "scenario_id": format!("specimen:{specimen_id}"),
        "driver": "pw_runner",
        "profile": "PWRunner",
        "variant": "default",
        "status": status,
        "exit_code": if status == "pass" { 0 } else { 1 },
        "inside": inside,
        "uncertainty": {
            "confidence": confidence,
            "reasons": reasons,
            "collector_health": {},
        },
        "steps": steps,
        "evidence": {
            "sandbox_logs": { "observed_deny": observed_deny },
            "deny_marker": { "value": deny_marker, "observed": marker_observed },
        }
    })
}

fn cmd_inside(args: &[OsString]) -> Result<i32, String> {
    let mut bare = false;
    let mut service_names: Vec<String> = Vec::new();

    let mut idx = 0usize;
    while idx < args.len() {
        let arg = args[idx].to_string_lossy();
        match arg.as_ref() {
            "-h" | "--help" => {
                print_usage();
                return Ok(0);
            }
            "--bare" => {
                bare = true;
                idx += 1;
            }
            "--service-name" => {
                let name = args
                    .get(idx + 1)
                    .and_then(|s| s.to_str())
                    .ok_or_else(|| "missing value for --service-name".to_string())?;
                service_names.push(name.to_string());
                idx += 2;
            }
            _ => return Err(format!("unknown argument: {arg}")),
        }
    }

    let result = inside_probe(&service_names);
    if bare {
        let inside = result.get("inside").and_then(|v| v.as_bool()).unwrap_or(true);
        println!("{}", if inside { "true" } else { "false" });
    } else {
        let mut v = result;
        sort_json_value(&mut v);
        println!(
            "{}",
            serde_json::to_string_pretty(&v).map_err(|e| format!("failed to encode JSON: {e}"))?
        );
    }
    Ok(0)
}

fn cmd_specimen(args: &[OsString]) -> Result<i32, String> {
    let mut specimen_path: Option<PathBuf> = None;
    let mut out_dir: Option<PathBuf> = None;
    let mut timeout_ms = DEFAULT_TIMEOUT_MS;
    let mut log_last = DEFAULT_LOG_LAST.to_string();
    let mut force = false;

    let mut idx = 0usize;
    while idx < args.len() {
        let arg = args[idx].to_string_lossy();
        if arg == "--" {
            break;
        }
        if !arg.starts_with('-') {
            specimen_path = Some(PathBuf::from(args[idx].clone()));
            idx += 1;
            continue;
        }
        match arg.as_ref() {
            "-h" | "--help" => {
                print_usage();
                return Ok(0);
            }
            "--outdir" => {
                let v = args
                    .get(idx + 1)
                    .ok_or_else(|| "missing value for --outdir".to_string())?;
                out_dir = Some(PathBuf::from(v));
                idx += 2;
            }
            "--timeout-ms" => {
                let v = args
                    .get(idx + 1)
                    .and_then(|s| s.to_str())
                    .ok_or_else(|| "missing value for --timeout-ms".to_string())?;
                timeout_ms = v
                    .parse::<u64>()
                    .map_err(|_| "invalid --timeout-ms".to_string())?
                    .max(1);
                idx += 2;
            }
            "--log-last" => {
                let v = args
                    .get(idx + 1)
                    .and_then(|s| s.to_str())
                    .ok_or_else(|| "missing value for --log-last".to_string())?;
                log_last = v.to_string();
                idx += 2;
            }
            "--force" => {
                force = true;
                idx += 1;
            }
            _ => return Err(format!("unknown argument: {arg}")),
        }
    }

    let specimen_path = specimen_path.ok_or_else(|| "missing <specimen.json>".to_string())?;

    let app_root = app_root_from_current_exe()?;
    let runner_info = resolve_pw_runner_bundle_info(&app_root)?;

    let inside = inside_probe(&[runner_info.bundle_id.clone()]);

    let allow_inside = std::env::var("PW_LAB_ALLOW_INSIDE").ok().as_deref() == Some("1");
    if inside.get("inside").and_then(|v| v.as_bool()).unwrap_or(true) && !allow_inside {
        let blocked_dir = out_dir.unwrap_or_else(|| {
            let stamp = chrono_stamp();
            PathBuf::from(".pw_lab/out").join(format!("{stamp}_specimen_blocked"))
        });
        ensure_clean_dir(&blocked_dir, force)?;
        write_json_pretty(&blocked_dir.join("inside.json"), inside.clone())?;
        let blocked_summary = json!({
            "labbook_version": LABBOOK_VERSION,
            "scenario_id": "specimen",
            "driver": "pw_runner",
            "profile": "PWRunner",
            "variant": "default",
            "status": "blocked",
            "exit_code": 3,
            "inside": inside,
            "uncertainty": {"confidence": "unknown", "reasons": ["inside"], "collector_health": {}},
            "steps": [],
            "evidence": {},
        });
        write_json_pretty(&blocked_dir.join("lab_summary.json"), blocked_summary)?;
        return Ok(3);
    }

    let spec_obj = load_specimen(&specimen_path)?;
    let specimen_id = spec_obj
        .specimen_id
        .clone()
        .unwrap_or_else(|| "specimen".to_string());

    let deny_marker = format!("PW_LAB_DENY_MARKER:{specimen_id}");

    let canonical_policy = spec_obj.policy.clone();
    let instrumented_policy = if let Some(p) = spec_obj.instrumented_policy.clone() {
        p
    } else if canonical_policy.format == "sbpl" {
        let src = canonical_policy
            .sbpl_source
            .clone()
            .ok_or_else(|| "policy.format=sbpl requires sbpl_source".to_string())?;
        let mut p = canonical_policy.clone();
        p.sbpl_source = Some(instrument_sbpl_message_marker(&src, &deny_marker));
        p
    } else {
        return Err("missing instrumented_policy (and canonical policy cannot be auto-instrumented)".to_string());
    };

    let out_dir = out_dir.unwrap_or_else(|| {
        let stamp = chrono_stamp();
        PathBuf::from(".pw_lab/out").join(format!("{stamp}_specimen_{specimen_id}"))
    });
    ensure_clean_dir(&out_dir, force)?;

    write_json_pretty(&out_dir.join("inside.json"), inside.clone())?;
    write_json_pretty(
        &out_dir.join("specimen.json"),
        serde_json::to_value(&spec_obj).map_err(|e| format!("failed to encode specimen.json: {e}"))?,
    )?;

    let canonical_req = PWRunnerRunRequest {
        schema_version: 1,
        specimen_id: specimen_id.clone(),
        run_kind: "canonical".to_string(),
        policy: canonical_policy,
        probe_plan: spec_obj.probe_plan.clone(),
    };
    let canonical_req_path = out_dir.join("canonical.request.json");
    write_json_pretty(
        &canonical_req_path,
        serde_json::to_value(canonical_req).map_err(|e| format!("failed to encode request: {e}"))?,
    )?;

    let instr_req = PWRunnerRunRequest {
        schema_version: 1,
        specimen_id: specimen_id.clone(),
        run_kind: "instrumented".to_string(),
        policy: instrumented_policy,
        probe_plan: spec_obj.probe_plan.clone(),
    };
    let instr_req_path = out_dir.join("instrumented.request.json");
    write_json_pretty(
        &instr_req_path,
        serde_json::to_value(instr_req).map_err(|e| format!("failed to encode request: {e}"))?,
    )?;

    let canonical_run = run_pw_runner_client(
        &runner_info.bundle_id,
        &canonical_req_path,
        &out_dir.join("canonical"),
        timeout_ms,
    )?;

    let instrumented_run = run_pw_runner_client(
        &runner_info.bundle_id,
        &instr_req_path,
        &out_dir.join("instrumented"),
        timeout_ms,
    )?;

    // Channel C: unified-log deny capture (best-effort but required for high confidence).
    let canonical_pid = canonical_run
        .parsed
        .as_ref()
        .and_then(|v| v.get("pid"))
        .and_then(|v| v.as_i64());
    let instr_pid = instrumented_run
        .parsed
        .as_ref()
        .and_then(|v| v.get("pid"))
        .and_then(|v| v.as_i64());

    let mut canonical_logs: Option<Value> = None;
    if let Some(pid) = canonical_pid {
        let logs = capture_sandbox_logs_last(
            pid,
            &runner_info.executable,
            &out_dir.join("canonical_sandbox_logs"),
            &log_last,
        )?;
        write_json_pretty(&out_dir.join("canonical_sandbox_logs.json"), logs.clone())?;
        canonical_logs = Some(logs);
    }

    let mut instrumented_logs: Option<Value> = None;
    if let Some(pid) = instr_pid {
        let logs = capture_sandbox_logs_last(
            pid,
            &runner_info.executable,
            &out_dir.join("instrumented_sandbox_logs"),
            &log_last,
        )?;
        write_json_pretty(
            &out_dir.join("instrumented_sandbox_logs.json"),
            logs.clone(),
        )?;
        instrumented_logs = Some(logs);
    }

    let summary = summary_for_specimen_eval(
        &specimen_id,
        &spec_obj.probe_plan,
        canonical_run.parsed.as_ref(),
        canonical_logs.as_ref(),
        instrumented_logs.as_ref(),
        &deny_marker,
        &inside,
    );
    write_json_pretty(&out_dir.join("lab_summary.json"), summary.clone())?;

    let mut out_summary = summary;
    sort_json_value(&mut out_summary);
    println!(
        "{}",
        serde_json::to_string_pretty(&out_summary).map_err(|e| format!("failed to encode JSON: {e}"))?
    );

    let exit_code = out_summary
        .get("exit_code")
        .and_then(|v| v.as_i64())
        .unwrap_or(1)
        .clamp(0, 255) as i32;
    Ok(exit_code)
}

fn chrono_stamp() -> String {
    // YYYYMMDD-HHMMSS, local time (stable enough for run dirs).
    // Avoid external dependencies: use `date` for portability.
    let out = Command::new("/bin/date")
        .arg("+%Y%m%d-%H%M%S")
        .output()
        .ok()
        .and_then(|o| String::from_utf8(o.stdout).ok())
        .unwrap_or_else(|| "00000000-000000".to_string());
    out.trim().to_string()
}

fn main() {
    let argv: Vec<OsString> = std::env::args_os().skip(1).collect();
    if argv.is_empty() {
        print_usage();
        std::process::exit(2);
    }
    let sub = argv[0].to_string_lossy().to_string();
    let rest = &argv[1..];

    let result = match sub.as_str() {
        "inside" => cmd_inside(rest),
        "specimen" => cmd_specimen(rest),
        "-h" | "--help" | "help" => {
            print_usage();
            Ok(0)
        }
        _ => Err(format!("unknown subcommand: {sub}")),
    };

    match result {
        Ok(code) => std::process::exit(code),
        Err(err) => {
            eprintln!("{err}");
            std::process::exit(2);
        }
    }
}
