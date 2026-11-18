//! `run`'s arguments, and the controls `test-input run` admits beside them.

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

enumerated!(
    /// A test control: an argument `test-input run` admits and `run` does not.
    Control {
        WorkerTimeoutMs,
        WorkerPreReadyHangMs,
        WorkerPostApplyHangMs,
        WorkerPostApplyKillSignal,
        WorkerKillBeforePublishSlot,
        ValidatorExecutablePath,
        ValidatorIoTimeoutMs,
        ValidatorTotalTimeoutMs,
    }
);

/// What follows a control.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ControlValue {
    /// A signed 64-bit decimal integer, delivered as written: the runner
    /// and its worker decide each control's range.
    Integer,
    /// Text, delivered as written.
    Text,
}

pub struct ControlDef {
    pub spelling: &'static str,
    /// The control's member name in the object the runner client receives.
    pub key: &'static str,
    pub value: ControlValue,
}

impl Control {
    pub const fn def(self) -> ControlDef {
        use ControlValue::{Integer, Text};
        let (spelling, key, value) = match self {
            Control::WorkerTimeoutMs => ("--worker-timeout-ms", "worker_timeout_ms", Integer),
            Control::WorkerPreReadyHangMs => (
                "--worker-pre-ready-hang-ms",
                "worker_pre_ready_hang_ms",
                Integer,
            ),
            Control::WorkerPostApplyHangMs => (
                "--worker-post-apply-hang-ms",
                "worker_post_apply_hang_ms",
                Integer,
            ),
            Control::WorkerPostApplyKillSignal => (
                "--worker-post-apply-kill-signal",
                "worker_post_apply_kill_signal",
                Integer,
            ),
            Control::WorkerKillBeforePublishSlot => (
                "--worker-kill-before-publish-slot",
                "worker_kill_before_publish_slot",
                Integer,
            ),
            Control::ValidatorExecutablePath => (
                "--validator-executable-path",
                "validator_executable_path",
                Text,
            ),
            Control::ValidatorIoTimeoutMs => (
                "--validator-io-timeout-ms",
                "validator_io_timeout_ms",
                Integer,
            ),
            Control::ValidatorTotalTimeoutMs => (
                "--validator-total-timeout-ms",
                "validator_total_timeout_ms",
                Integer,
            ),
        };
        ControlDef {
            spelling,
            key,
            value,
        }
    }
}

/// The command whose arguments are being read.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Form {
    /// `run`.
    Run,
    /// `test-input run`: `run`'s arguments and the controls.
    TestInputRun,
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
    Control(Control),
    /// Flag-shaped and neither an option nor a control of this form: refused.
    UnknownFlag,
}

pub fn classify(argument: &str, form: Form) -> Token {
    if argument == TERMINATOR {
        return Token::Terminator;
    }
    if !argument.starts_with(FLAG_PREFIX) {
        return Token::RequestPath;
    }
    let option = RunOption::ALL
        .iter()
        .copied()
        .find(|option| option.def().spelling == argument);
    if let Some(option) = option {
        return Token::Option(option);
    }
    let controls: &[Control] = match form {
        Form::Run => &[],
        Form::TestInputRun => Control::ALL,
    };
    controls
        .iter()
        .copied()
        .find(|control| control.def().spelling == argument)
        .map_or(Token::UnknownFlag, Token::Control)
}
