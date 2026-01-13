mod json_contract;

use serde::Serialize;
use serde_json::{json, Value};
use std::ffi::OsString;
use std::path::{Component, Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::{SystemTime, UNIX_EPOCH};

const PW_RUNNER_SERVICE_DIR: &str = "PWRunner";

const DEFAULT_TIMEOUT_MS: u64 = 240_000;
const DEFAULT_LOG_LAST: &str = "10s";

const MAX_CAPTURE_BYTES: usize = 1024 * 1024;

fn print_usage() {
    eprintln!(
        "\
usage:
  policy-witness run <request.json> [--timeout-ms <n>] [--log-last <dur>]

notes:
  - runs the embedded PWRunner XPC service once and prints a single JSON result to stdout
  - request.json is passed through to the runner client (it must match the runner request schema)"
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

#[derive(Serialize)]
struct SandboxLogCapture {
    capture_status: String,
    tool_exit_code: i32,
    stdout_parse_error: Option<String>,
    stdout_truncated: bool,
    stdout_raw: Option<String>,
    stderr: String,
    stderr_truncated: bool,
    observer: Option<Value>,
    observed_deny: Option<bool>,
}

#[derive(Serialize)]
struct RunData {
    request_path: String,
    runner_service_bundle_id: String,
    runner_service_executable: String,
    timeout_ms: u64,
    log_last: String,
    runner_client: RunnerClientRun,
    runner_result: Option<Value>,
    sandbox_log_capture: Option<SandboxLogCapture>,
}

fn run_pw_runner_client(
    service_bundle_id: &str,
    request_path: &Path,
    timeout_ms: u64,
) -> Result<(RunnerClientRun, Option<Value>), String> {
    let tool = resolve_contents_macos_tool("pw-runner-client")?;
    let argv = vec![
        tool.into_os_string(),
        OsString::from("run"),
        OsString::from("--timeout-ms"),
        OsString::from(format!("{timeout_ms}")),
        OsString::from(service_bundle_id),
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

    Ok((runner_client, parsed))
}

fn observed_deny_from_observer_envelope(obj: &Value) -> Option<bool> {
    obj.get("data")
        .and_then(|v| v.get("observed_deny"))
        .and_then(|v| v.as_bool())
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
    let capture_status = if out.status.success() {
        "captured".to_string()
    } else {
        "requested_unavailable".to_string()
    };

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

    Ok(SandboxLogCapture {
        capture_status,
        tool_exit_code: exit_code,
        stdout_parse_error: parse_error.clone(),
        stdout_truncated,
        stdout_raw: if parse_error.is_some() { Some(stdout) } else { None },
        stderr,
        stderr_truncated,
        observer: parsed,
        observed_deny,
    })
}

fn cmd_run(args: &[OsString]) -> Result<i32, String> {
    let mut request_path: Option<PathBuf> = None;
    let mut timeout_ms = DEFAULT_TIMEOUT_MS;
    let mut log_last = DEFAULT_LOG_LAST.to_string();

    let mut idx = 0usize;
    while idx < args.len() {
        let arg = args[idx].to_string_lossy();
        if arg == "--" {
            idx += 1;
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
            _ => return Err(format!("unknown argument: {arg}")),
        }
    }

    let request_path = request_path.ok_or_else(|| "missing <request.json>".to_string())?;
    if !request_path.exists() {
        return Err(format!("request.json not found: {}", request_path.display()));
    }

    let app_root = app_root_from_current_exe()?;
    let runner_info = resolve_pw_runner_bundle_info(&app_root)?;

    let (runner_client, runner_result) =
        run_pw_runner_client(&runner_info.bundle_id, &request_path, timeout_ms)?;

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

    let sandbox_log_capture = runner_pid.map(|pid| {
        capture_sandbox_logs_last(pid, &runner_info.executable, &log_last).unwrap_or_else(|err| {
            SandboxLogCapture {
                capture_status: "requested_unavailable".to_string(),
                tool_exit_code: 1,
                stdout_parse_error: None,
                stdout_truncated: false,
                stdout_raw: None,
                stderr: err,
                stderr_truncated: false,
                observer: None,
                observed_deny: None,
            }
        })
    });

    let data = RunData {
        request_path: request_path.to_string_lossy().to_string(),
        runner_service_bundle_id: runner_info.bundle_id,
        runner_service_executable: runner_info.executable,
        timeout_ms,
        log_last,
        runner_client,
        runner_result,
        sandbox_log_capture,
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

    if sub != "run" {
        print_usage();
        std::process::exit(2);
    }

    match cmd_run(rest) {
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
            let data = json!({"error": "policy-witness run failed before producing a runner result"});
            let _ = json_contract::print_envelope("run", result, &data);
            std::process::exit(2);
        }
    }
}
