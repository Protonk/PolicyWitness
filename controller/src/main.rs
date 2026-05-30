//! PolicyWitness controller entry point.
//!
//! The controller binary is intentionally small; most logic lives in modules
//! that focus on runner selection, evidence capture, and JSON output.

mod app_layout;
mod bundle;
mod cli;
mod evidence;
mod json_contract;
mod policy_preflight;
mod plist;
mod request_patch;
mod run_flow;
mod runner_client;
mod runner_commands;
mod runner_manager;
mod runner_select;
mod sandbox_log;
mod utils;

use std::ffi::OsString;

fn main() {
    let argv: Vec<OsString> = std::env::args_os().skip(1).collect();
    std::process::exit(cli::run(argv));
}
