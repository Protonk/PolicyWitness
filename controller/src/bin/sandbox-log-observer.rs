//! Unified-log observer for sandbox deny events.
//!
//! This tool runs outside the app sandbox to query the system log for deny
//! messages associated with a specific process. It emits JSON so the controller
//! can attach evidence without parsing raw log output.

#[path = "../json_contract.rs"]
#[allow(dead_code)]
mod json_contract;
#[path = "../log_capture.rs"]
#[allow(dead_code)]
mod log_capture;

#[path = "../log_show.rs"]
mod log_show;

#[cfg(test)]
use log_capture::Boundary;
use log_capture::{CollectionBudget, LogTimeout, Supervision};
#[cfg(test)]
use log_show::ShowCapture;
use log_show::{SandboxDenyEvent, capture_show, is_log_prelude_line, parse_sandbox_deny_line};
use serde::Serialize;
use std::ffi::OsString;
use std::fs::OpenOptions;
use std::io::{self, BufRead, Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

const OBSERVER_SCHEMA_VERSION: u32 = 1;
const MAX_CAPTURE_BYTES: usize = 1024 * 1024;
const ESRCH: i32 = 3;

unsafe extern "C" {
    fn kill(pid: i32, sig: i32) -> i32;
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum OutputFormat {
    Json,
    Jsonl,
}

impl OutputFormat {
    fn parse(value: &str) -> Option<Self> {
        match value {
            "json" => Some(OutputFormat::Json),
            "jsonl" => Some(OutputFormat::Jsonl),
            _ => None,
        }
    }
}

fn print_usage() {
    eprintln!(
        "\
usage:
  sandbox-log-observer --pid <pid> --process-name <name> [--start <time> --end <time> | --last <duration> | --duration <seconds> | --follow] [--until-pid-exit] [--predicate <predicate>] [--format <json|jsonl>] [--output <path>] [--plan-id <id>] [--row-id <id>] [--correlation-id <id>]

notes:
  - runs `log show` (default) or `log stream` (with --duration/--follow) with a sandbox-deny predicate (observer-only)
  - --format jsonl emits per-line events plus a final report line
  - show mode has a finite default collection deadline (10000 ms) and fixed cleanup grace (1000 ms)
  - --collection-budget <json> is the internal shared CLOCK_MONOTONIC budget passed by the controller
  - intended to run outside PolicyWitness.app (unsandboxed)"
    );
}

fn now_unix_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

fn json_result(ok: bool) -> json_contract::JsonResult {
    json_contract::JsonResult {
        ok,
        rc: None,
        exit_code: Some(if ok { 0 } else { 3 }),
        normalized_outcome: None,
        errno: None,
        error: None,
        stderr: None,
        stdout: None,
    }
}

fn is_pid_alive(pid: i32) -> bool {
    unsafe {
        // kill(pid, 0) checks existence without delivering a signal.
        if kill(pid, 0) == 0 {
            return true;
        }
        match io::Error::last_os_error().raw_os_error() {
            Some(ESRCH) => false,
            Some(_) => true,
            None => false,
        }
    }
}

fn sandbox_predicate(process_name: &str, pid: i32) -> String {
    let mut name = String::new();
    for c in process_name.chars() {
        if "\\.^$|?*+()[]{}".contains(c) {
            name.push('\\');
        }
        name.push(c);
    }
    // Select complete process/PID tokens, including supported whitespace after
    // Sandbox:. Exact parsed PID checking still precedes candidate association.
    let pattern = format!(r"(?s).*Sandbox:[ \t]+{name}\({pid}\)([ \t]+.*)?");
    format!(
        "eventMessage MATCHES[c] {}",
        serde_json::to_string(&pattern).unwrap()
    )
}

// The archive is an internal test input, never a controller flag or a fallback
// to the live store. Production and the archive control use identical flags.
fn log_show_command(
    start: Option<&str>,
    end: Option<&str>,
    last: Option<&str>,
    predicate: Option<&str>,
    archive: Option<&Path>,
) -> Command {
    let mut command = Command::new("/usr/bin/log");
    command.args(["show", "--style", "syslog", "--info", "--debug"]);
    if let Some(archive) = archive {
        command.arg("--archive").arg(archive);
    }
    if let Some(last) = last {
        command.arg("--last").arg(last);
    }
    if let Some(start) = start {
        command.arg("--start").arg(start);
    }
    if let Some(end) = end {
        command.arg("--end").arg(end);
    }
    if let Some(predicate) = predicate {
        command.arg("--predicate").arg(predicate);
    }
    command
}

fn open_output(path: &Path, append: bool) -> Result<std::fs::File, String> {
    if let Some(parent) = path.parent() {
        if !parent.as_os_str().is_empty() && parent != Path::new(".") {
            std::fs::create_dir_all(parent)
                .map_err(|e| format!("failed to create {}: {e}", parent.display()))?;
        }
    }
    let mut opts = OpenOptions::new();
    opts.create(true).write(true);
    if append {
        opts.append(true);
    } else {
        opts.truncate(true);
    }
    opts.open(path)
        .map_err(|e| format!("failed to open {}: {e}", path.display()))
}

fn write_jsonl_line(line: &str, file: Option<&mut std::fs::File>) -> Result<(), String> {
    let mut stdout = io::stdout();
    stdout
        .write_all(line.as_bytes())
        .map_err(|e| format!("failed to write stdout: {e}"))?;
    stdout
        .write_all(b"\n")
        .map_err(|e| format!("failed to write stdout: {e}"))?;
    stdout
        .flush()
        .map_err(|e| format!("failed to flush stdout: {e}"))?;
    if let Some(file) = file {
        file.write_all(line.as_bytes())
            .map_err(|e| format!("failed to write output: {e}"))?;
        file.write_all(b"\n")
            .map_err(|e| format!("failed to write output: {e}"))?;
        file.flush()
            .map_err(|e| format!("failed to flush output: {e}"))?;
    }
    Ok(())
}

fn read_to_string(mut reader: impl Read) -> String {
    let mut buf = String::new();
    let _ = reader.read_to_string(&mut buf);
    buf
}

#[derive(Serialize)]
struct ObserverLayerAttribution {
    seatbelt: String,
}

#[derive(Serialize)]
struct LogObserverData {
    observer_schema_version: u32,
    mode: String,
    duration_ms: Option<u64>,
    stop_on_pid_exit: bool,
    plan_id: Option<String>,
    row_id: Option<String>,
    correlation_id: Option<String>,
    pid: i32,
    process_name: Option<String>,
    predicate: String,
    start: Option<String>,
    end: Option<String>,
    last: Option<String>,
    log_rc: Option<i32>,
    log_stdout: String,
    log_stderr: String,
    log_error: Option<String>,
    blocked_reason: Option<String>,
    log_truncated: bool,
    observed_lines: usize,
    observed_deny: bool,
    deny_lines: Vec<String>,
    deny_events: Vec<SandboxDenyEvent>,
    layer_attribution: ObserverLayerAttribution,
    collection: Option<Supervision>,
}

#[derive(Serialize)]
struct LogObserverEventData {
    observer_schema_version: u32,
    plan_id: Option<String>,
    row_id: Option<String>,
    correlation_id: Option<String>,
    pid: i32,
    process_name: Option<String>,
    predicate: String,
    observed_at_unix_ms: u64,
    line: String,
    is_deny: bool,
}

fn main() {
    let args: Vec<OsString> = std::env::args_os().skip(1).collect();
    if args.is_empty() {
        print_usage();
        std::process::exit(2);
    }

    let mut pid: Option<i32> = None;
    let mut process_name: Option<String> = None;
    let mut predicate: Option<String> = None;
    let mut start: Option<String> = None;
    let mut end: Option<String> = None;
    let mut last: Option<String> = None;
    let mut plan_id: Option<String> = None;
    let mut row_id: Option<String> = None;
    let mut correlation_id: Option<String> = None;
    let mut collection_budget: Option<CollectionBudget> = None;
    let mut output_format = OutputFormat::Json;
    let mut output_path: Option<PathBuf> = None;
    let mut follow = false;
    let mut duration: Option<Duration> = None;
    let mut until_pid_exit = false;

    let mut idx = 0usize;
    while idx < args.len() {
        let arg = args.get(idx).and_then(|s| s.to_str()).unwrap_or_default();
        match arg {
            "--collection-budget" => {
                collection_budget = Some(
                    args.get(idx + 1)
                        .and_then(|s| s.to_str())
                        .ok_or_else(|| "missing --collection-budget".to_string())
                        .and_then(CollectionBudget::from_argument)
                        .unwrap_or_else(|err| {
                            eprintln!("{err}");
                            std::process::exit(2);
                        }),
                );
                idx += 2;
            }
            "-h" | "--help" => {
                print_usage();
                return;
            }
            "--pid" => {
                let value = args.get(idx + 1).and_then(|s| s.to_str());
                match value.and_then(|v| v.parse::<i32>().ok()) {
                    Some(v) => pid = Some(v),
                    None => {
                        eprintln!("invalid value for --pid");
                        print_usage();
                        std::process::exit(2);
                    }
                }
                idx += 2;
            }
            "--process-name" => {
                let value = args.get(idx + 1).and_then(|s| s.to_str());
                match value {
                    Some(v) => process_name = Some(v.to_string()),
                    None => {
                        eprintln!("missing value for --process-name");
                        print_usage();
                        std::process::exit(2);
                    }
                }
                idx += 2;
            }
            "--predicate" => {
                let value = args.get(idx + 1).and_then(|s| s.to_str());
                match value {
                    Some(v) => predicate = Some(v.to_string()),
                    None => {
                        eprintln!("missing value for --predicate");
                        print_usage();
                        std::process::exit(2);
                    }
                }
                idx += 2;
            }
            "--start" => {
                let value = args.get(idx + 1).and_then(|s| s.to_str());
                match value {
                    Some(v) => start = Some(v.to_string()),
                    None => {
                        eprintln!("missing value for --start");
                        print_usage();
                        std::process::exit(2);
                    }
                }
                idx += 2;
            }
            "--end" => {
                let value = args.get(idx + 1).and_then(|s| s.to_str());
                match value {
                    Some(v) => end = Some(v.to_string()),
                    None => {
                        eprintln!("missing value for --end");
                        print_usage();
                        std::process::exit(2);
                    }
                }
                idx += 2;
            }
            "--last" => {
                let value = args.get(idx + 1).and_then(|s| s.to_str());
                match value {
                    Some(v) => last = Some(v.to_string()),
                    None => {
                        eprintln!("missing value for --last");
                        print_usage();
                        std::process::exit(2);
                    }
                }
                idx += 2;
            }
            "--duration" => {
                let value = args.get(idx + 1).and_then(|s| s.to_str());
                let parsed = value.and_then(|v| v.parse::<f64>().ok());
                match parsed {
                    Some(secs) if secs > 0.0 => {
                        duration = Some(Duration::from_secs_f64(secs));
                    }
                    _ => {
                        eprintln!("invalid value for --duration (expected seconds > 0)");
                        print_usage();
                        std::process::exit(2);
                    }
                }
                idx += 2;
            }
            "--follow" => {
                follow = true;
                idx += 1;
            }
            "--until-pid-exit" => {
                until_pid_exit = true;
                idx += 1;
            }
            "--format" => {
                let value = args.get(idx + 1).and_then(|s| s.to_str());
                match value.and_then(OutputFormat::parse) {
                    Some(v) => output_format = v,
                    None => {
                        eprintln!("invalid value for --format (expected json|jsonl)");
                        print_usage();
                        std::process::exit(2);
                    }
                }
                idx += 2;
            }
            "--output" => {
                let value = args.get(idx + 1).and_then(|s| s.to_str());
                match value {
                    Some(v) => output_path = Some(PathBuf::from(v)),
                    None => {
                        eprintln!("missing value for --output");
                        print_usage();
                        std::process::exit(2);
                    }
                }
                idx += 2;
            }
            "--plan-id" => {
                let value = args.get(idx + 1).and_then(|s| s.to_str());
                match value {
                    Some(v) => plan_id = Some(v.to_string()),
                    None => {
                        eprintln!("missing value for --plan-id");
                        print_usage();
                        std::process::exit(2);
                    }
                }
                idx += 2;
            }
            "--row-id" => {
                let value = args.get(idx + 1).and_then(|s| s.to_str());
                match value {
                    Some(v) => row_id = Some(v.to_string()),
                    None => {
                        eprintln!("missing value for --row-id");
                        print_usage();
                        std::process::exit(2);
                    }
                }
                idx += 2;
            }
            "--correlation-id" => {
                let value = args.get(idx + 1).and_then(|s| s.to_str());
                match value {
                    Some(v) => correlation_id = Some(v.to_string()),
                    None => {
                        eprintln!("missing value for --correlation-id");
                        print_usage();
                        std::process::exit(2);
                    }
                }
                idx += 2;
            }
            _ => {
                eprintln!("unknown arg: {}", arg);
                print_usage();
                std::process::exit(2);
            }
        }
    }

    let pid = match pid {
        Some(v) => v,
        None => {
            eprintln!("missing --pid");
            print_usage();
            std::process::exit(2);
        }
    };

    if follow && duration.is_some() {
        eprintln!("cannot combine --follow with --duration");
        print_usage();
        std::process::exit(2);
    }

    let stream_mode = follow || duration.is_some();

    if until_pid_exit && !stream_mode {
        eprintln!("--until-pid-exit requires --follow or --duration");
        print_usage();
        std::process::exit(2);
    }

    if stream_mode && (start.is_some() || end.is_some() || last.is_some()) {
        eprintln!("--start/--end/--last cannot be combined with --duration/--follow");
        print_usage();
        std::process::exit(2);
    }

    if !stream_mode {
        if (start.is_some() || end.is_some()) && last.is_some() {
            eprintln!("cannot combine --start/--end with --last");
            print_usage();
            std::process::exit(2);
        }

        if start.is_some() ^ end.is_some() {
            eprintln!("--start and --end must be provided together");
            print_usage();
            std::process::exit(2);
        }

        if start.is_none() && end.is_none() {
            last = Some(last.unwrap_or_else(|| "5s".to_string()));
        }
    }

    let predicate = match predicate {
        Some(v) => v,
        None => match process_name.as_ref() {
            Some(name) => sandbox_predicate(name, pid),
            None => {
                eprintln!("missing --process-name (required when --predicate is not set)");
                print_usage();
                std::process::exit(2);
            }
        },
    };
    if stream_mode && collection_budget.is_some() {
        eprintln!("--collection-budget is only valid for log show");
        std::process::exit(2);
    }
    // Bound echoed query/identity metadata independently of stream output.
    for value in [
        Some(predicate.as_str()),
        process_name.as_deref(),
        start.as_deref(),
        end.as_deref(),
        last.as_deref(),
        plan_id.as_deref(),
        row_id.as_deref(),
        correlation_id.as_deref(),
    ]
    .into_iter()
    .flatten()
    {
        if value.len() > log_capture::MAX_OBSERVER_METADATA_BYTES {
            eprintln!("observer metadata exceeds 4096 UTF-8 bytes");
            std::process::exit(2);
        }
    }

    let mut output_file = if output_format == OutputFormat::Jsonl {
        output_path.as_ref().map(|path| {
            open_output(path, true).unwrap_or_else(|err| {
                eprintln!("{err}");
                std::process::exit(1);
            })
        })
    } else {
        None
    };

    let mut observed_lines = 0usize;
    let mut deny_lines: Vec<String> = Vec::new();
    let mut deny_events: Vec<SandboxDenyEvent> = Vec::new();
    let mut log_stdout = String::new();
    let mut log_stdout_bytes = 0usize;
    let mut log_truncated = false;
    let log_stderr: String;
    let log_rc: Option<i32>;
    let mut log_error: Option<String> = None;
    let mut blocked_reason: Option<String> = None;
    let mut collection: Option<Supervision> = None;

    // log stream gives live updates; log show is a point-in-time snapshot.
    let mode = if stream_mode { "stream" } else { "show" }.to_string();
    let duration_ms = duration.map(|d| d.as_millis() as u64);

    if stream_mode {
        let mut cmd = Command::new("/usr/bin/log");
        cmd.arg("stream")
            .arg("--style")
            .arg("syslog")
            .arg("--info")
            .arg("--debug")
            .arg("--predicate")
            .arg(&predicate)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        let mut child = match cmd.spawn() {
            Ok(child) => child,
            Err(err) => {
                let data = LogObserverData {
                    observer_schema_version: OBSERVER_SCHEMA_VERSION,
                    mode,
                    duration_ms,
                    stop_on_pid_exit: until_pid_exit,
                    plan_id: plan_id.clone(),
                    row_id: row_id.clone(),
                    correlation_id: correlation_id.clone(),
                    pid,
                    process_name: process_name.clone(),
                    predicate,
                    start,
                    end,
                    last,
                    log_rc: None,
                    log_stdout: String::new(),
                    log_stderr: String::new(),
                    log_error: Some(format!("failed to run log: {err}")),
                    blocked_reason: None,
                    log_truncated: false,
                    observed_lines: 0,
                    observed_deny: false,
                    deny_lines: Vec::new(),
                    deny_events: Vec::new(),
                    layer_attribution: ObserverLayerAttribution {
                        seatbelt: "observer_only".to_string(),
                    },
                    collection: None,
                };
                let result = json_result(false);
                if let Err(err) =
                    json_contract::print_envelope("sandbox_log_observer_report", result, &data)
                {
                    eprintln!("{err}");
                }
                std::process::exit(1);
            }
        };

        let stdout = match child.stdout.take() {
            Some(stdout) => stdout,
            None => {
                eprintln!("failed to capture log stdout");
                std::process::exit(1);
            }
        };
        let stderr = match child.stderr.take() {
            Some(stderr) => stderr,
            None => {
                eprintln!("failed to capture log stderr");
                std::process::exit(1);
            }
        };

        let child = Arc::new(Mutex::new(child));

        if let Some(duration) = duration {
            let child_for_timer = Arc::clone(&child);
            thread::spawn(move || {
                thread::sleep(duration);
                if let Ok(mut child) = child_for_timer.lock() {
                    let _ = child.kill();
                }
            });
        }

        if follow {
            let child_for_signal = Arc::clone(&child);
            let _ = ctrlc::set_handler(move || {
                if let Ok(mut child) = child_for_signal.lock() {
                    let _ = child.kill();
                }
            });
        }

        if until_pid_exit {
            let child_for_pid = Arc::clone(&child);
            let pid_to_watch = pid;
            thread::spawn(move || {
                while is_pid_alive(pid_to_watch) {
                    thread::sleep(Duration::from_millis(200));
                }
                if let Ok(mut child) = child_for_pid.lock() {
                    let _ = child.kill();
                }
            });
        }

        let stderr_handle = thread::spawn(move || read_to_string(stderr));

        let mut stdout_reader = io::BufReader::new(stdout);
        let mut line = String::new();
        loop {
            line.clear();
            let bytes = match stdout_reader.read_line(&mut line) {
                Ok(n) => n,
                Err(_) => break,
            };
            if bytes == 0 {
                break;
            }
            let trimmed = line.trim_end_matches(['\n', '\r']);
            if trimmed.is_empty() {
                continue;
            }
            if is_log_prelude_line(trimmed) {
                continue;
            }
            observed_lines += 1;
            let deny_event = parse_sandbox_deny_line(trimmed);
            let is_deny = deny_event.is_some();
            if let Some(event) = deny_event {
                deny_lines.push(trimmed.to_string());
                deny_events.push(event);
            }
            if !log_truncated {
                let add_bytes = trimmed.len() + 1;
                if log_stdout_bytes + add_bytes > MAX_CAPTURE_BYTES {
                    log_truncated = true;
                } else {
                    log_stdout.push_str(trimmed);
                    log_stdout.push('\n');
                    log_stdout_bytes += add_bytes;
                }
            }

            if output_format == OutputFormat::Jsonl {
                let event = LogObserverEventData {
                    observer_schema_version: OBSERVER_SCHEMA_VERSION,
                    plan_id: plan_id.clone(),
                    row_id: row_id.clone(),
                    correlation_id: correlation_id.clone(),
                    pid,
                    process_name: process_name.clone(),
                    predicate: predicate.clone(),
                    observed_at_unix_ms: now_unix_ms(),
                    line: trimmed.to_string(),
                    is_deny,
                };
                let text = match json_contract::render_envelope_compact(
                    "sandbox_log_observer_event",
                    json_result(true),
                    &event,
                ) {
                    Ok(text) => text,
                    Err(err) => {
                        eprintln!("{err}");
                        continue;
                    }
                };
                if let Err(err) = write_jsonl_line(&text, output_file.as_mut()) {
                    eprintln!("{err}");
                }
            }
        }

        let status = match child.lock() {
            Ok(mut child) => child.wait().ok(),
            Err(_) => None,
        };
        log_rc = status.and_then(|s| s.code());
        log_stderr = stderr_handle.join().unwrap_or_default();

        if let Some(status) = status {
            if !status.success() && duration.is_none() && !follow {
                log_error = Some("log stream returned non-zero".to_string());
            }
        }
    } else {
        let budget = collection_budget.unwrap_or_else(|| {
            LogTimeout::default().start().unwrap_or_else(|e| {
                eprintln!("{e}");
                std::process::exit(2);
            })
        });
        let mut command = log_show_command(
            start.as_deref(),
            end.as_deref(),
            last.as_deref(),
            Some(&predicate),
            None,
        );
        let captured = capture_show(&mut command, budget);
        log_rc = captured.report.process.exit_code;
        log_truncated = captured.report.stdout.truncated
            || captured.report.stderr.truncated
            || captured
                .report
                .cutoff
                .as_ref()
                .is_some_and(|c| c.reason == "event_overflow");
        if !captured.report.complete() {
            log_error = Some(
                captured
                    .report
                    .cutoff
                    .as_ref()
                    .map(|c| c.reason.clone())
                    .unwrap_or_else(|| "log query completion unavailable".into()),
            );
        }
        log_stdout = captured.stdout;
        log_stderr = captured.stderr;
        observed_lines = captured.observed_lines;
        deny_lines = captured.deny_lines;
        deny_events = captured.deny_events;
        collection = Some(captured.report);
    }

    let lower = format!("{log_stdout}\n{log_stderr}").to_ascii_lowercase();
    if lower.contains("cannot run while sandboxed") {
        let reason = "Cannot run while sandboxed".to_string();
        blocked_reason = Some(reason.clone());
        log_error = Some(reason);
    }

    let observed_deny = !deny_events.is_empty();

    let data = LogObserverData {
        observer_schema_version: OBSERVER_SCHEMA_VERSION,
        mode,
        duration_ms,
        stop_on_pid_exit: until_pid_exit,
        plan_id,
        row_id,
        correlation_id,
        pid,
        process_name,
        predicate,
        start,
        end,
        last,
        log_rc,
        log_stdout,
        log_stderr,
        log_error: log_error.clone(),
        blocked_reason,
        log_truncated,
        observed_lines,
        observed_deny,
        deny_lines,
        deny_events,
        layer_attribution: ObserverLayerAttribution {
            seatbelt: "observer_only".to_string(),
        },
        collection,
    };

    let result = json_result(log_error.is_none());

    match output_format {
        OutputFormat::Json => {
            let text = match json_contract::render_envelope_limited(
                "sandbox_log_observer_report",
                result,
                &data,
                true,
                log_capture::OBSERVER_STDOUT_BYTES - 1, // final newline also crosses the pipe
            ) {
                Ok(text) => text,
                Err(err) => {
                    eprintln!("{err}");
                    std::process::exit(1);
                }
            };
            if let Some(path) = output_path.as_ref() {
                match open_output(path, false) {
                    Ok(mut file) => {
                        if let Err(err) = file.write_all(format!("{text}\n").as_bytes()) {
                            eprintln!("failed to write {}: {err}", path.display());
                            std::process::exit(1);
                        }
                    }
                    Err(err) => {
                        eprintln!("{err}");
                        std::process::exit(1);
                    }
                }
            }
            println!("{text}");
        }
        OutputFormat::Jsonl => {
            let text = match json_contract::render_envelope_limited(
                "sandbox_log_observer_report",
                result,
                &data,
                false,
                log_capture::OBSERVER_STDOUT_BYTES - 1,
            ) {
                Ok(text) => text,
                Err(err) => {
                    eprintln!("{err}");
                    std::process::exit(1);
                }
            };
            if let Err(err) = write_jsonl_line(&text, output_file.as_mut()) {
                eprintln!("{err}");
                std::process::exit(1);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn documented_observer_limits() {
        let manifest: serde_json::Value =
            serde_json::from_str(include_str!("../../../docs/limits.json")).unwrap();
        let owned: std::collections::BTreeMap<&str, usize> = manifest["limits"]
            .as_array()
            .unwrap()
            .iter()
            .filter(|row| {
                row["checks"].as_array().unwrap().iter().any(|check| {
                    check["path"] == "controller/src/bin/sandbox-log-observer.rs"
                        && check["kind"] == "value"
                })
            })
            .map(|row| {
                (
                    row["id"].as_str().unwrap(),
                    row["value"].as_u64().unwrap() as usize,
                )
            })
            .collect();
        assert_eq!(
            owned,
            std::collections::BTreeMap::from([("observer_stream_text", super::MAX_CAPTURE_BYTES)])
        );
    }

    #[test]
    fn parsed_event_retains_pid_operation_and_raw_line_without_temporal_claims() {
        let line =
            "2026-09-17 12:00:00 Sandbox: pw-probe-runner(42) deny(1) file-write-data /tmp/attempt";
        let event = parse_sandbox_deny_line(line).unwrap();
        assert_eq!(event.pid, Some(42));
        assert_eq!(event.operation.as_deref(), Some("file-write-data"));
        assert_eq!(event.path.as_deref(), Some("/tmp/attempt"));
        assert_eq!(event.raw_line, line);
        let raw = serde_json::to_value(event).unwrap();
        assert!(raw.get("timestamp").is_none());
    }

    #[test]
    fn path_with_spaces_is_not_shortened_to_a_different_target() {
        let event = parse_sandbox_deny_line(
            "Sandbox: pw-probe-runner(42) deny(1) file-read-data /tmp/a  b",
        )
        .unwrap();
        assert_eq!(event.path.as_deref(), Some("/tmp/a  b"));
    }

    #[test]
    fn absent_or_malformed_pid_remains_absent_in_observer_evidence() {
        for proc in ["pw-probe-runner", "pw-probe-runner(unknown)"] {
            let line = format!("Sandbox: {proc} deny(1) file-read-data /tmp/x");
            let event = parse_sandbox_deny_line(&line).unwrap();
            assert_eq!(event.pid, None);
            assert_eq!(event.raw_line, line);
        }
    }

    #[test]
    fn predicate_escapes_quotes_and_includes_pid() {
        let pred = sandbox_predicate("service\"name.*", 123);
        let regex: String =
            serde_json::from_str(pred.strip_prefix("eventMessage MATCHES[c] ").unwrap()).unwrap();
        assert!(regex.contains(r#"service"name\.\*\(123\)"#));
        assert!(regex.contains("Sandbox:"));
        assert!(!pred.contains("CONTAINS"));
        // Syntax checks are not a substitute for the real archive query case.
    }

    fn python(script: &str) -> Command {
        let mut command = Command::new("/usr/bin/python3");
        command.args(["-c", script]);
        command
    }

    fn report_from_capture(capture: ShowCapture) -> LogObserverData {
        LogObserverData {
            observer_schema_version: OBSERVER_SCHEMA_VERSION,
            mode: "show".into(),
            duration_ms: None,
            stop_on_pid_exit: false,
            plan_id: None,
            row_id: None,
            correlation_id: None,
            pid: 42,
            process_name: Some("pw-probe-runner".into()),
            predicate: sandbox_predicate("pw-probe-runner", 42),
            start: Some("2026-01-01 00:00:00+0000".into()),
            end: Some("2026-01-01 00:00:05+0000".into()),
            last: None,
            log_rc: capture.report.process.exit_code,
            log_stdout: capture.stdout,
            log_stderr: capture.stderr,
            log_error: capture.report.cutoff.as_ref().map(|c| c.reason.clone()),
            blocked_reason: None,
            log_truncated: capture.report.stdout.truncated || capture.report.stderr.truncated,
            observed_lines: capture.observed_lines,
            observed_deny: !capture.deny_events.is_empty(),
            deny_lines: capture.deny_lines,
            deny_events: capture.deny_events,
            layer_attribution: ObserverLayerAttribution {
                seatbelt: "observer_only".into(),
            },
            collection: Some(capture.report),
        }
    }

    #[test]
    fn controlled_capacity_preserves_256_records_and_fits_the_outer_report() {
        let script = r#"import os
for n in range(256):
    os.write(1, ('Sandbox: pw-probe-runner(42) deny(1) file-write-data /capacity/%03d/' % n).encode() + b'\x01'*490 + b'\n')
"#;
        let capture = capture_show(&mut python(script), LogTimeout::default().start().unwrap());
        assert!(capture.report.complete(), "{:?}", capture.report);
        assert_eq!(capture.deny_events.len(), 256);
        assert_eq!(capture.deny_lines.len(), 256);
        for (n, event) in capture.deny_events.iter().enumerate() {
            assert_eq!(event.pid, Some(42));
            assert_eq!(
                event.path.as_deref(),
                Some(format!("/capacity/{n:03}/{}", "\u{1}".repeat(490)).as_str())
            );
        }
        let report = report_from_capture(capture);
        let text = json_contract::render_envelope_limited(
            "sandbox_log_observer_report",
            json_result(true),
            &report,
            true,
            log_capture::OBSERVER_STDOUT_BYTES - 1,
        )
        .unwrap();
        let value: serde_json::Value = serde_json::from_str(&text).unwrap();
        assert_eq!(value["data"]["deny_events"].as_array().unwrap().len(), 256);
        eprintln!(
            "capacity: 256 records, inner stdout {} bytes, observer report {} bytes",
            report.collection.as_ref().unwrap().stdout.bytes_read,
            text.len() + 1
        );
    }

    #[test]
    fn inner_byte_limit_with_maximal_json_escaping_fits_outer_serialization_limit() {
        let script = format!(
            r#"import os
prefix = b'Sandbox: pw-probe-runner(42) deny(1) file-write-data /'
os.write(1, prefix + b'\x01'*({}-len(prefix)-1) + b'\n')
os.write(2, b'\x01'*{})
"#,
            log_capture::LOG_STDOUT_BYTES,
            log_capture::LOG_STDERR_BYTES
        );
        let capture = capture_show(&mut python(&script), LogTimeout::default().start().unwrap());
        assert!(capture.report.complete(), "{:?}", capture.report);
        assert_eq!(
            capture.report.stdout.bytes_read,
            log_capture::LOG_STDOUT_BYTES
        );
        assert_eq!(
            capture.report.stderr.bytes_read,
            log_capture::LOG_STDERR_BYTES
        );
        assert_eq!(capture.deny_events.len(), 1);
        let report = report_from_capture(capture);
        let text = json_contract::render_envelope_limited(
            "sandbox_log_observer_report",
            json_result(true),
            &report,
            true,
            log_capture::OBSERVER_STDOUT_BYTES - 1,
        )
        .unwrap();
        assert!(text.len() + 1 < log_capture::OBSERVER_STDOUT_BYTES);
        assert!(
            json_contract::render_envelope_limited(
                "sandbox_log_observer_report",
                json_result(true),
                &report,
                true,
                100
            )
            .is_err()
        );
        eprintln!(
            "maximum escaping: observer report {} bytes, budget {}",
            text.len() + 1,
            log_capture::OBSERVER_STDOUT_BYTES
        );
    }

    #[test]
    fn event_limit_withholds_completion_without_discarding_retained_diagnostics() {
        for n in [
            log_capture::MAX_DENY_EVENTS,
            log_capture::MAX_DENY_EVENTS + 1,
        ] {
            let script = format!(
                "import os; os.write(1,b'Sandbox: w(42) deny(1) file-read-data /a\\n'*{n})"
            );
            let capture =
                capture_show(&mut python(&script), LogTimeout::default().start().unwrap());
            assert_eq!(capture.deny_events.len(), log_capture::MAX_DENY_EVENTS);
            assert_eq!(capture.report.complete(), n == log_capture::MAX_DENY_EVENTS);
            if n > log_capture::MAX_DENY_EVENTS {
                let cutoff = capture.report.cutoff.as_ref().unwrap();
                assert_eq!(cutoff.reason, "event_overflow");
                assert_eq!(cutoff.observed, Some(n as u64));
            }
            let report = report_from_capture(capture);
            let text = json_contract::render_envelope_limited(
                "sandbox_log_observer_report",
                json_result(n == log_capture::MAX_DENY_EVENTS),
                &report,
                true,
                log_capture::OBSERVER_STDOUT_BYTES - 1,
            )
            .unwrap();
            assert_eq!(
                serde_json::from_str::<serde_json::Value>(&text).unwrap()["data"]["deny_events"]
                    .as_array()
                    .unwrap()
                    .len(),
                log_capture::MAX_DENY_EVENTS
            );
        }
    }

    #[test]
    fn inner_timeout_preserves_available_record_and_actual_child_wait() {
        let budget = LogTimeout {
            milliseconds: 200,
            source: log_capture::TimeoutSource::Cli,
        }
        .start()
        .unwrap();
        let capture = capture_show(
            &mut python(
                "import os,time; os.write(1,b'Sandbox: w(42) deny(1) file-read-data /a\\n'); time.sleep(60)",
            ),
            budget,
        );
        assert_eq!(capture.deny_events.len(), 1);
        assert_eq!(capture.report.cutoff.as_ref().unwrap().reason, "deadline");
        assert_eq!(capture.report.process.term_signal, Some(libc::SIGKILL));
        assert!(capture.report.process.reaped);
        assert_eq!(capture.report.cleanup.outcome, "child_reaped");
        let report = report_from_capture(capture);
        let text = json_contract::render_envelope_limited(
            "sandbox_log_observer_report",
            json_result(false),
            &report,
            true,
            log_capture::OBSERVER_STDOUT_BYTES - 1,
        )
        .unwrap();
        assert_eq!(
            serde_json::from_str::<serde_json::Value>(&text).unwrap()["data"]["deny_events"]
                .as_array()
                .unwrap()
                .len(),
            1
        );
    }

    #[test]
    #[ignore = "selected explicitly by the required archive case; needs the committed archive and OS log access"]
    fn log_query_predicate_archive() {
        use serde_json::{Value, json};
        use std::collections::BTreeMap;
        let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../tests/fixtures/deny_capture");
        let archive = root.join("query_predicate.logarchive");
        assert!(
            archive.is_dir(),
            "required archive fixture missing: {}; see fixture README",
            archive.display()
        );
        let manifest: Value = serde_json::from_slice(
            &std::fs::read(root.join("query_predicate.json"))
                .expect("required independent query manifest missing"),
        )
        .unwrap();
        assert_eq!(manifest["schema_version"], 1);
        assert!(manifest["emitting_pid"].as_i64().is_some_and(|pid| pid > 0));
        let artifacts = PathBuf::from(
            std::env::var_os("PW_LOG_ARCHIVE_EVIDENCE")
                .expect("archive control requires an evidence directory"),
        );
        std::fs::create_dir_all(&artifacts).unwrap();
        let marker = manifest["message_marker"].as_str().unwrap();
        assert!(!marker.is_empty());
        let multiset = |messages: Vec<String>| {
            let mut counts = BTreeMap::new();
            for message in messages {
                *counts.entry(message).or_insert(0_usize) += 1;
            }
            counts
        };
        let strings = |value: &Value| {
            value
                .as_array()
                .unwrap()
                .iter()
                .map(|v| v.as_str().unwrap().to_string())
                .collect::<Vec<_>>()
        };
        let query = |label: &str, start: &str, end: &str, predicate: Option<&str>| {
            assert!(
                label
                    .bytes()
                    .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
            );
            let mut command =
                log_show_command(Some(start), Some(end), None, predicate, Some(&archive));
            let argv: Vec<_> = std::iter::once(command.get_program())
                .chain(command.get_args())
                .map(|s| s.to_string_lossy().into_owned())
                .collect();
            std::fs::write(
                artifacts.join(format!("{label}.argv.json")),
                serde_json::to_vec_pretty(&argv).unwrap(),
            )
            .unwrap();
            let capture = log_capture::capture_with_limits(
                &mut command,
                LogTimeout::default().start().unwrap(),
                Boundary::Observer,
                (log_capture::LOG_STDOUT_BYTES, log_capture::LOG_STDERR_BYTES),
            );
            std::fs::write(artifacts.join(format!("{label}.stdout")), &capture.stdout).unwrap();
            std::fs::write(artifacts.join(format!("{label}.stderr")), &capture.stderr).unwrap();
            std::fs::write(
                artifacts.join(format!("{label}.supervision.json")),
                serde_json::to_vec_pretty(&capture.supervision).unwrap(),
            )
            .unwrap();
            assert!(
                capture.supervision.complete(),
                "archive query {label} failed: {:?}",
                capture.supervision
            );
            String::from_utf8(capture.stdout).unwrap()
        };
        let all = query(
            "unfiltered",
            manifest["window"]["start"].as_str().unwrap(),
            manifest["window"]["end"].as_str().unwrap(),
            None,
        );
        let inventory: Vec<_> = all
            .lines()
            .filter_map(|line| line.find(marker).map(|at| line[at..].to_string()))
            .collect();
        assert_eq!(
            multiset(inventory),
            multiset(strings(&manifest["messages"])),
            "unfiltered corpus missing, duplicated or unexpected"
        );
        assert!(manifest["queries"].as_array().unwrap().len() >= 2);
        for input in manifest["queries"].as_array().unwrap() {
            let pid = i32::try_from(input["pid"].as_i64().unwrap()).unwrap();
            assert_ne!(
                Some(i64::from(pid)),
                manifest["emitting_pid"].as_i64(),
                "emitter and embedded worker identity must differ"
            );
            let expected = strings(&input["selected_messages"]);
            assert!(
                !expected.is_empty(),
                "each archive query requires a positive oracle"
            );
            let predicate = sandbox_predicate(input["process_name"].as_str().unwrap(), pid);
            let output = query(
                input["name"].as_str().unwrap(),
                input["start"].as_str().unwrap(),
                input["end"].as_str().unwrap(),
                Some(&predicate),
            );
            let mut selected = Vec::new();
            for line in output.lines() {
                if line.trim().is_empty()
                    || is_log_prelude_line(line)
                    || line.starts_with("Timestamp")
                {
                    continue;
                }
                let at = line
                    .find(marker)
                    .unwrap_or_else(|| panic!("unexpected selected non-corpus row: {line}"));
                selected.push(line[at..].to_string());
            }
            assert_eq!(
                multiset(selected),
                multiset(expected),
                "selected message multiset differs before parsing"
            );
            let parsed: Vec<_> = output.lines().filter_map(parse_sandbox_deny_line).map(|e|
                json!({"pid":e.pid, "process":e.process, "operation":e.operation, "path":e.path})).collect();
            let normalized =
                |events: Vec<Value>| multiset(events.iter().map(Value::to_string).collect());
            assert_eq!(
                normalized(parsed),
                normalized(input["deny_events"].as_array().unwrap().clone()),
                "parser discarded or changed a selected deny record"
            );
        }
    }
}
