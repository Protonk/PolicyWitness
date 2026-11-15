//! Selection of the `run` result: the outcome label, `ok`, and the one exit
//! status that is both the result's exit field and the process status.

enumerated!(
    /// An outcome label the controller itself selects.
    Label {
        BadRequest,
        ToolError,
        Finished,
        RunnerResponseUnavailable,
    }
);

impl Label {
    pub const fn spelling(self) -> &'static str {
        match self {
            Label::BadRequest => "bad_request",
            Label::ToolError => "tool_error",
            Label::Finished => "finished",
            Label::RunnerResponseUnavailable => "runner_response_unavailable",
        }
    }
}

enumerated!(
    /// Why client or reply admission refused a capture.
    Refusal {
        MissingRunnerClient,
        UnsupportedRunnerClient,
        MalformedRunnerClient,
        RunnerReplyTruncated,
        UnsupportedRunnerResponse,
        MalformedRunnerResponse,
        XpcError,
        XpcTimeout,
        XpcAcquisitionFailed,
        XpcSubmissionRefused,
        XpcProtocolError,
        RunnerClientError,
    }
);

impl Refusal {
    pub const fn spelling(self) -> &'static str {
        match self {
            Refusal::MissingRunnerClient => "missing_runner_client",
            Refusal::UnsupportedRunnerClient => "unsupported_runner_client",
            Refusal::MalformedRunnerClient => "malformed_runner_client",
            Refusal::RunnerReplyTruncated => "runner_reply_truncated",
            Refusal::UnsupportedRunnerResponse => "unsupported_runner_response",
            Refusal::MalformedRunnerResponse => "malformed_runner_response",
            Refusal::XpcError => "xpc_error",
            Refusal::XpcTimeout => "xpc_timeout",
            Refusal::XpcAcquisitionFailed => "xpc_acquisition_failed",
            Refusal::XpcSubmissionRefused => "xpc_submission_refused",
            Refusal::XpcProtocolError => "xpc_protocol_error",
            Refusal::RunnerClientError => "runner_client_error",
        }
    }
}

/// What the controller concluded about one run, before a result exists.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Disposition<'a> {
    /// The controller refused the request it read.
    LocalRequestRefusal,
    /// The controller could not do its own work, request delivery included.
    ToolFailure,
    /// Client or reply admission refused the capture.
    AdmissionRefusal(Refusal),
    /// The capture was admitted. `host_outcome` is the admitted host
    /// reply's label, absent when the completion carries no host reply.
    /// `integrity_issues` counts the controller's findings about the reply.
    Admitted {
        host_outcome: Option<&'a str>,
        integrity_issues: usize,
    },
}

enumerated!(
    /// The class of a disposition.
    Class {
        LocalRequestRefusal,
        ToolFailure,
        AdmissionRefusal,
        Admitted,
    }
);

impl Disposition<'_> {
    pub const fn class(&self) -> Class {
        match self {
            Disposition::LocalRequestRefusal => Class::LocalRequestRefusal,
            Disposition::ToolFailure => Class::ToolFailure,
            Disposition::AdmissionRefusal(_) => Class::AdmissionRefusal,
            Disposition::Admitted { .. } => Class::Admitted,
        }
    }
}

/// A row's condition on the admitted host label.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Host {
    /// The row does not read the host label.
    Unread,
    Is(Label),
    Present,
    Absent,
}

/// Where a row's outcome label comes from.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Outcome {
    Fixed(Label),
    /// The selected refusal's label.
    Refusal,
    /// The admitted host label, retained.
    HostLabel,
}

enumerated!(
    /// The rows of the relation, in selection order: the first row whose
    /// class and host condition hold is selected.
    Row {
        LocalRequestRefusal,
        ToolFailure,
        AdmissionRefusal,
        AdmittedFinished,
        AdmittedOther,
        AdmittedUnavailable,
    }
);

pub struct RowDef {
    pub class: Class,
    pub host: Host,
    pub outcome: Outcome,
    pub ok: bool,
    pub exit: i32,
}

impl Row {
    pub const fn def(self) -> RowDef {
        let (class, host, outcome, ok, exit) = match self {
            Row::LocalRequestRefusal => (
                Class::LocalRequestRefusal,
                Host::Unread,
                Outcome::Fixed(Label::BadRequest),
                false,
                1,
            ),
            Row::ToolFailure => (
                Class::ToolFailure,
                Host::Unread,
                Outcome::Fixed(Label::ToolError),
                false,
                2,
            ),
            Row::AdmissionRefusal => (
                Class::AdmissionRefusal,
                Host::Unread,
                Outcome::Refusal,
                false,
                1,
            ),
            Row::AdmittedFinished => (
                Class::Admitted,
                Host::Is(Label::Finished),
                Outcome::HostLabel,
                true,
                0,
            ),
            Row::AdmittedOther => (Class::Admitted, Host::Present, Outcome::HostLabel, false, 1),
            Row::AdmittedUnavailable => (
                Class::Admitted,
                Host::Absent,
                Outcome::Fixed(Label::RunnerResponseUnavailable),
                false,
                1,
            ),
        };
        RowDef {
            class,
            host,
            outcome,
            ok,
            exit,
        }
    }
}

/// The selected result. `exit` is the result's exit field and the process
/// status; nothing else supplies either.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Selection {
    pub row: Row,
    pub outcome: String,
    pub ok: bool,
    pub exit: i32,
}

pub fn select(disposition: &Disposition) -> Selection {
    let (refusal, host_outcome) = match *disposition {
        Disposition::AdmissionRefusal(refusal) => (Some(refusal), None),
        Disposition::Admitted { host_outcome, .. } => (None, host_outcome),
        Disposition::LocalRequestRefusal | Disposition::ToolFailure => (None, None),
    };
    let class = disposition.class();
    for row in Row::ALL.iter().copied() {
        let def = row.def();
        let host_holds = match def.host {
            Host::Unread => true,
            Host::Is(label) => host_outcome == Some(label.spelling()),
            Host::Present => host_outcome.is_some(),
            Host::Absent => host_outcome.is_none(),
        };
        if def.class != class || !host_holds {
            continue;
        }
        let outcome = match def.outcome {
            Outcome::Fixed(label) => Some(label.spelling()),
            Outcome::Refusal => refusal.map(Refusal::spelling),
            Outcome::HostLabel => host_outcome,
        };
        if let Some(outcome) = outcome {
            return Selection {
                row,
                outcome: outcome.to_string(),
                ok: def.ok,
                exit: def.exit,
            };
        }
    }
    // The build script evaluates every class with every host label, so a
    // relation with a gap stops the build.
    unreachable!("every disposition has a row that supplies its outcome")
}
