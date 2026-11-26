//! `policy-witness help`: prints one card the build stored.
//!
//! `build.rs` renders the cards from the definitions in `interface` and the
//! example specimen; nothing is rendered, read or collected here.

use std::ffi::OsString;
use std::io::Write;

use crate::interface::commands::Topic;

const BASE: &str = include_str!(concat!(env!("OUT_DIR"), "/help/base.txt"));
const RUN: &str = include_str!(concat!(env!("OUT_DIR"), "/help/run.txt"));
const EXAMPLE: &str = include_str!(concat!(env!("OUT_DIR"), "/help/example.txt"));
const RUNNER: &str = include_str!(concat!(env!("OUT_DIR"), "/help/runner.txt"));
const RESULT: &str = include_str!(concat!(env!("OUT_DIR"), "/help/result.txt"));

pub fn card(topic: Option<Topic>) -> &'static str {
    match topic {
        None => BASE,
        Some(Topic::Run) => RUN,
        Some(Topic::Example) => EXAMPLE,
        Some(Topic::Runner) => RUNNER,
        Some(Topic::Result) => RESULT,
    }
}

/// Writes the addressed card to stdout and nothing to stderr. Only a failed
/// write or flush is not exit 0.
pub fn cmd_help(tail: &[OsString]) -> i32 {
    let mut out = std::io::stdout().lock();
    let card = card(Topic::select(tail));
    match out.write_all(card.as_bytes()).and_then(|()| out.flush()) {
        Ok(()) => 0,
        Err(_) => 2,
    }
}
