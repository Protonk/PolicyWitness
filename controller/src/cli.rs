//! Command-line entrypoint for the PolicyWitness controller.
//!
//! Dispatch reads the command table in `interface::commands`: the first
//! argument is compared with each command's spelling, and the command's tail
//! rule decides what its handler receives.

use serde_json::json;
use std::ffi::OsString;
use std::io::Write;

use crate::example;
use crate::help;
use crate::interface::commands::{Command, TailRefused};
use crate::json_contract;
use crate::run_flow;
use crate::runner_commands;
use crate::test_input;

/// A refusal's reason, for a person. An unwritable stderr leaves the exit
/// status as the whole report.
pub fn diagnose(reason: &str) {
    let _ = writeln!(std::io::stderr(), "{reason}");
}

/// The refusal for an invocation that names no command: exit 2, nothing on
/// stdout.
fn refuse_command() -> i32 {
    diagnose(&format!(
        "policy-witness: no command recognized; `policy-witness {}` prints the help topics",
        Command::Help.def().spelling
    ));
    2
}

pub fn run(argv: Vec<OsString>) -> i32 {
    let Some(command) = argv.first().and_then(|first| Command::recognize(first)) else {
        return refuse_command();
    };
    match (command, command.def().tail.admit(&argv[1..])) {
        // `example` reports each of its refusals itself, a refused tail among them.
        (Command::Example, admitted) => example::cmd_example(admitted),
        (_, Err(TailRefused)) => {
            diagnose(&format!(
                "policy-witness {}: accepts no arguments",
                command.def().spelling
            ));
            2
        }
        (Command::Help, Ok(tail)) => help::cmd_help(tail),
        (Command::VersionFlag | Command::Version, Ok(_)) => {
            let result = json_contract::JsonResult::new(true, 0, None, None);
            let data = json!({"contract": json_contract::BUILD_CONTRACT});
            match json_contract::print_envelope("version", result, &data) {
                Ok(()) => 0,
                Err(error) => {
                    diagnose(&format!(
                        "policy-witness {}: {error}",
                        command.def().spelling
                    ));
                    2
                }
            }
        }
        (Command::Run, Ok(tail)) => match run_flow::cmd_run(tail) {
            Ok(code) => code,
            // Errors that escape cmd_run still use the uniform run envelope.
            Err(err) => run_flow::print_escaped_tool_error(command, err),
        },
        (Command::TestInput, Ok(tail)) => test_input::cmd_test_input(tail),
        (Command::Runner, Ok(tail)) => match runner_commands::cmd_runner(tail) {
            Ok(code) => code,
            Err(err) => {
                diagnose(&err);
                2
            }
        },
    }
}
