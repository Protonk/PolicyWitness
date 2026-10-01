//! PolicyWitness controller entry point.
//!
//! The controller binary is intentionally small; most logic lives in modules
//! that focus on runner selection, evidence capture, and JSON output.

mod app_layout;
mod augments;
mod bundle;
mod cli;
mod evidence;
// Shared with the sbpl-check helper through #[path] includes; the controller's
// specimen dossier reads them.
#[allow(dead_code)]
mod host_facts;
mod json_contract;
mod log_capture;
#[cfg(test)]
mod log_show;
mod plist;
mod policy_check;
mod request_patch;
mod run_flow;
mod runner_client;
mod runner_commands;
mod runner_manager;
mod runner_select;
mod sandbox_log;
#[allow(dead_code)]
mod sbpl_imports;
#[allow(dead_code)]
mod sbpl_lex;
mod utils;

use std::ffi::OsString;

fn main() {
    let argv: Vec<OsString> = std::env::args_os().skip(1).collect();
    std::process::exit(cli::run(argv));
}
