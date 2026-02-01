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
  policy-witness run <request.json> [--timeout-ms <n>] [--log-last <dur>] [--runner-mode <standard|debuggable|byoxpc|machme>] [--instrumentation <json|@path>] [--sonoma-cross-check]
  policy-witness runner <command> [options]

notes:
  - runs the selected PWRunner XPC service once and prints a single JSON result to stdout
  - request.json is passed through to the runner client (or copied with runner mode/instrumentation injected)"
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

    match sub.as_str() {
        "run" => match run_flow::cmd_run(rest) {
            Ok(code) => code,
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
