//! `run`'s arguments.

use super::runner_kind::Reader;

enumerated!(
    /// An option `run` admits.
    RunOption {
        TimeoutMs,
        RunnerMode,
    }
);

/// What follows an option.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Value {
    /// A decimal count of milliseconds; a value below `min` is refused.
    Milliseconds { min: u64 },
    /// A word this reader of the runner-kind vocabulary admits.
    Kind(Reader),
}

pub struct RunOptionDef {
    pub spelling: &'static str,
    pub value: Value,
}

impl RunOption {
    pub const fn def(self) -> RunOptionDef {
        let (spelling, value) = match self {
            RunOption::TimeoutMs => ("--timeout-ms", Value::Milliseconds { min: 1 }),
            RunOption::RunnerMode => ("--runner-mode", Value::Kind(Reader::RunOption)),
        };
        RunOptionDef { spelling, value }
    }
}

/// Stops argument processing; everything after it is ignored.
pub const TERMINATOR: &str = "--";
/// An argument that does not start with this is the request path. A second
/// one is refused.
pub const FLAG_PREFIX: char = '-';

/// What one argument is to `run`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Token {
    Terminator,
    RequestPath,
    Option(RunOption),
    /// Flag-shaped and not an option: refused.
    UnknownFlag,
}

pub fn classify(argument: &str) -> Token {
    if argument == TERMINATOR {
        return Token::Terminator;
    }
    if !argument.starts_with(FLAG_PREFIX) {
        return Token::RequestPath;
    }
    RunOption::ALL
        .iter()
        .copied()
        .find(|option| option.def().spelling == argument)
        .map_or(Token::UnknownFlag, Token::Option)
}
