//! Select a help card or field entry from the text embedded at build time.

use std::ffi::OsString;
use std::io::Write;

use crate::interface::commands::{Command, Topic};

const BASE: &str = include_str!(concat!(env!("OUT_DIR"), "/help/base.txt"));
const RUN: &str = include_str!(concat!(env!("OUT_DIR"), "/help/run.txt"));
const EXAMPLE: &str = include_str!(concat!(env!("OUT_DIR"), "/help/example.txt"));
const RUNNER: &str = include_str!(concat!(env!("OUT_DIR"), "/help/runner.txt"));
const RESULT: &str = include_str!(concat!(env!("OUT_DIR"), "/help/result.txt"));

include!(concat!(env!("OUT_DIR"), "/help/fields.rs"));

pub fn card(topic: Option<Topic>) -> &'static str {
    match topic {
        None => BASE,
        Some(Topic::Run) => RUN,
        Some(Topic::Example) => EXAMPLE,
        Some(Topic::Runner) => RUNNER,
        Some(Topic::Result) => RESULT,
    }
}

/// Only the run topic takes a field selector. Other topics retain their card.
pub fn cmd_help(tail: &[OsString]) -> i32 {
    let topic = Topic::select(tail);
    let card = if topic == Some(Topic::Run) && tail.len() > 1 {
        let help = Command::Help.def().spelling;
        let run = Topic::Run.address();
        let key = match &tail[1..] {
            [key] => key.to_str(),
            _ => None,
        };
        let Some(key) = key else {
            let operand = crate::interface::field_help::OPERAND;
            crate::cli::diagnose(&format!("Usage: {help} {run} [{operand}]"));
            return 2;
        };
        match crate::interface::field_help::select_field(key) {
            Some(field) => match field.entry {
                Some(entry) => field_text(entry.id),
                None => {
                    crate::cli::diagnose(&format!(
                        "No help entry for this admission field. See {help} {run} for available entries.\n{ADMISSION_REFERENCE}"
                    ));
                    return 2;
                }
            },
            None => {
                crate::cli::diagnose(&format!(
                    "Unknown {help} {run} key. See {help} {run} for available entries."
                ));
                return 2;
            }
        }
    } else {
        card(topic)
    };
    let mut out = std::io::stdout().lock();
    match out.write_all(card.as_bytes()).and_then(|()| out.flush()) {
        Ok(()) => 0,
        Err(_) => 2,
    }
}
