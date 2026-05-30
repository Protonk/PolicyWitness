//! Wrapper for invoking the Swift pw-runner-client helper.
//!
//! The Rust controller shells out to the Swift client to perform NSXPC wiring;
//! the JSON output is captured and embedded in the controller envelope.

use serde::Serialize;
use serde_json::Value;
use std::ffi::OsString;
use std::process::{Command, Stdio};

use crate::app_layout::resolve_contents_macos_tool;
use crate::runner_select::RunnerConnectionKind;
use crate::utils::{now_unix_ms, truncate_output};

#[derive(Serialize)]
pub struct RunnerClientRun {
    pub argv: Vec<String>,
    pub started_at_unix_ms: u64,
    pub ended_at_unix_ms: u64,
    pub exit_code: i32,
    pub stdout_parse_error: Option<String>,
    pub stdout_truncated: bool,
    pub stdout_raw: Option<String>,
    pub stderr: String,
    pub stderr_truncated: bool,
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
        // pw-runner-client prints a JSON envelope on stdout when successful.
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

pub fn run_pw_runner_client(
    service_name: &str,
    request_path: &std::path::Path,
    timeout_ms: u64,
    connection: &RunnerConnectionKind,
) -> Result<(RunnerClientRun, Option<Value>), String> {
    let tool = resolve_contents_macos_tool("pw-runner-client")?;
    let mut argv = vec![
        tool.into_os_string(),
        OsString::from("run"),
        OsString::from("--timeout-ms"),
        OsString::from(format!("{timeout_ms}")),
    ];
    match connection {
        RunnerConnectionKind::XpcService => {}
        RunnerConnectionKind::MachService { privileged } => {
            argv.push(OsString::from("--mach-service"));
            if *privileged {
                argv.push(OsString::from("--privileged"));
            }
        }
    }
    argv.push(OsString::from(service_name));
    argv.push(request_path.as_os_str().to_os_string());

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

