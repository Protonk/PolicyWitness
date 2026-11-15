//! Top-level commands and help topics.

use std::ffi::{OsStr, OsString};

enumerated!(
    /// A first argument the dispatcher recognizes.
    Command {
        Help,
        Run,
        Example,
        TestInput,
        Runner,
        VersionFlag,
        Version,
    }
);

/// What the dispatcher does with the arguments after a command.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Tail {
    /// The first argument addresses a help topic; the rest are discarded.
    Topic,
    /// `run_args` governs every argument.
    RunArguments,
    /// Any argument is refused.
    RefusesAny,
    /// The command's own parser receives the arguments; its definitions are
    /// not enumerated here.
    Unenumerated,
}

pub struct CommandDef {
    pub spelling: &'static str,
    pub tail: Tail,
}

impl Command {
    pub const fn def(self) -> CommandDef {
        let (spelling, tail) = match self {
            Command::Help => ("help", Tail::Topic),
            Command::Run => ("run", Tail::RunArguments),
            Command::Example => ("example", Tail::RefusesAny),
            Command::TestInput => ("test-input", Tail::Unenumerated),
            Command::Runner => ("runner", Tail::Unenumerated),
            Command::VersionFlag => ("--version", Tail::RefusesAny),
            Command::Version => ("version", Tail::RefusesAny),
        };
        CommandDef { spelling, tail }
    }

    /// The command a first argument names: an exact comparison of the whole
    /// argument, so a differently cased or non-UTF-8 argument names none.
    pub fn recognize(argument: &OsStr) -> Option<Command> {
        Command::ALL
            .iter()
            .copied()
            .find(|command| argument == OsStr::new(command.def().spelling))
    }
}

/// A tail the command's rule refused.
#[derive(Debug, PartialEq, Eq)]
pub struct TailRefused;

impl Tail {
    /// The arguments the command's handler receives.
    pub fn admit(self, arguments: &[OsString]) -> Result<&[OsString], TailRefused> {
        match self {
            Tail::Topic | Tail::RunArguments | Tail::Unenumerated => Ok(arguments),
            Tail::RefusesAny if arguments.is_empty() => Ok(arguments),
            Tail::RefusesAny => Err(TailRefused),
        }
    }
}

enumerated!(
    /// A help topic: one card beside the base card.
    Topic {
        Run,
        Example,
        Result,
    }
);

/// Where a topic's address comes from.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Address {
    /// The topic describes a command and shares its spelling.
    Command(Command),
    /// The topic has a spelling of its own.
    Own(&'static str),
}

impl Topic {
    pub const fn source(self) -> Address {
        match self {
            Topic::Run => Address::Command(Command::Run),
            Topic::Example => Address::Command(Command::Example),
            Topic::Result => Address::Own("result"),
        }
    }

    pub const fn address(self) -> &'static str {
        match self.source() {
            Address::Command(command) => command.def().spelling,
            Address::Own(spelling) => spelling,
        }
    }

    /// The topic the argument after `help` addresses. Only that argument is
    /// read; an absent, unregistered or non-UTF-8 one addresses no topic.
    pub fn select(tail: &[OsString]) -> Option<Topic> {
        let argument = tail.first()?;
        Topic::ALL
            .iter()
            .copied()
            .find(|topic| argument.as_os_str() == OsStr::new(topic.address()))
    }
}
