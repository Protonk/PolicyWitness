//! Command-line entrypoint for the PolicyWitness controller.
//!
//! This module owns the public CLI surface and keeps the dispatch logic
//! together so the rest of the controller can focus on orchestration.

use serde_json::json;
use std::ffi::OsString;

use crate::json_contract;
use crate::run_flow;
use crate::runner_commands;

pub fn print_usage() {
    eprintln!(
        "\
usage:
  policy-witness run <request.json> [--timeout-ms <n>] [--log-timeout-ms <n>] [--no-log-capture] [--runner-mode <standard|byoxpc>]
  policy-witness runner <command> [options]
    commands: install, list, status, verify, remove, validate, reconcile
  policy-witness --version

notes:
  - runs the selected PWRunner XPC service once and prints a single JSON result to stdout
  - request.json is parsed once; the resolved request is delivered to the runner client on stdin (`--request -`), never through a temporary file
  - the unified-log (`log show`) deny scan requests the runner client's wall-clock span, rounded outward to whole seconds and padded by two seconds at each end; reversed endpoints prevent the scan
  - --log-timeout-ms sets a finite log-collection allowance (default 10000 ms), with a separate fixed 1000 ms cleanup grace
  - --no-log-capture skips that scan; use it when you don't consume the deny evidence and want the per-run cost back
  - --version prints a JSON envelope (kind=version) with the build stamp and the wire contract versions this build speaks; every envelope also carries the stamp under `build`"
    );
}

pub fn run(argv: Vec<OsString>) -> i32 {
    if argv.is_empty() {
        print_usage();
        return 2;
    }

    let sub = argv[0].to_string_lossy().to_string();
    let rest = &argv[1..];

    if sub == "-h" || sub == "--help" || sub == "help" {
        print_usage();
        return 0;
    }

    if sub == "--version" || sub == "version" {
        let result = json_contract::JsonResult::new(true, 0, None, None);
        let data = json!({"contract": json_contract::contract_versions()});
        return match json_contract::print_envelope("version", result, &data) {
            Ok(()) => 0,
            Err(_) => 2,
        };
    }

    match sub.as_str() {
        "run" => match run_flow::cmd_run(rest) {
            Ok(code) => code,
            Err(err) => {
                // Errors that escape cmd_run still use the uniform run envelope.
                let _ = run_flow::print_escaped_tool_error(err);
                2
            }
        },
        "runner" => match runner_commands::cmd_runner(rest) {
            Ok(code) => code,
            Err(err) => {
                eprintln!("{err}");
                2
            }
        },
        _ => {
            print_usage();
            2
        }
    }
}
