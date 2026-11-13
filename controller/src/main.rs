//! PolicyWitness controller entry point.
//!
//! The controller binary is intentionally small; most logic lives in modules
//! that focus on runner selection, evidence capture, and JSON output.

mod app_layout;
mod augments;
mod bundle;
mod cli;
mod digest;
mod dossier;
mod evidence;
mod example;
// Shared with the sbpl-check helper through #[path] includes.
mod host_facts;
mod json_contract;
mod plist;
mod policy_check;
mod porcelain;
#[rustfmt::skip]
mod porcelain_records;
mod porcelain_admission;
#[cfg(test)]
mod reply_fixtures;
mod request_patch;
mod run_flow;
mod runner_client;
mod runner_commands;
mod runner_manager;
mod runner_select;
mod sbpl_imports;
mod sbpl_lex;
#[cfg(test)]
mod shape;
mod utils;

use std::ffi::OsString;

fn main() {
    let argv: Vec<OsString> = std::env::args_os().skip(1).collect();
    std::process::exit(cli::run(argv));
}
