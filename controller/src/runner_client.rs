//! One reservation-aware helper invocation and its versioned capture.
//!
//! Client observations are admitted before decoding any host reply. Neither a
//! transport failure nor missing helper output authorizes another invocation.
use crate::porcelain::FrameError;
use crate::porcelain_records::{
    PWRunnerClientCapture as Capture, PWRunnerControlObservation as Control, PWRunnerRunResult,
    PWRunnerTransportError as TransportError,
};
use serde::Serialize;
#[cfg(test)]
use serde_json::Value;
use std::ffi::OsString;
use std::process::Command;

use crate::app_layout::resolve_contents_macos_tool;
use crate::runner_select::RunnerConnectionKind;
use crate::utils::{OutputCapture, RequestDelivery, now_unix_ms, run_with_stdin};

const REPLY_CAPTURE_BYTES: usize = 92 * 1024 * 1024;
const CONTROL_BYTES: i64 = 64 * 1024;
const ATTEMPT_LIMIT: usize = 256;

#[derive(Serialize)]
pub struct RunnerClientRun {
    pub argv: Vec<String>,
    pub started_at_unix_ms: u64,
    pub ended_at_unix_ms: u64,
    pub exit_code: i32,
    /// Local stdin delivery, never proof that the host received the specimen.
    pub request_delivery: Option<RequestDelivery>,
    #[serde(flatten)]
    pub output: OutputCapture,
    /// Typed admitted capture, or the exact retained bytes of a rejected frame.
    pub transport: Option<TransportCapture>,
    pub transport_admission: String,
    pub transport_error: Option<String>,
    /// Unknown unless a complete current capture was admitted.
    pub submission: String,
    /// Host bytes were received but cannot be read as a complete typed reply.
    pub runner_reply_error: Option<ReplyError>,
}

/// Why received host bytes supplied no typed reply.
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum ReplyRefusal {
    Truncated,
    UnsupportedSchema,
    Malformed,
}

/// The refusal decides the controller outcome; only the diagnostic is presented.
#[derive(Debug)]
pub struct ReplyError {
    pub refusal: ReplyRefusal,
    pub message: String,
}
impl Serialize for ReplyError {
    fn serialize<S: serde::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        serializer.serialize_str(&self.message)
    }
}

#[derive(Debug, PartialEq, Serialize)]
#[cfg_attr(test, derive(Clone))]
#[serde(untagged)]
pub enum TransportCapture {
    Typed(Capture),
    Rejected {
        format: &'static str,
        #[serde(serialize_with = "serialize_rejected_bytes")]
        data_base64: Vec<u8>,
    },
}

fn serialize_rejected_bytes<S: serde::Serializer>(
    bytes: &[u8],
    serializer: S,
) -> Result<S::Ok, S::Error> {
    crate::porcelain::Base64(bytes).serialize(serializer)
}

impl TransportCapture {
    fn terminal(&self) -> Option<&str> {
        match self {
            Self::Typed(v) => Some(&v.terminal),
            Self::Rejected { .. } => None,
        }
    }
    fn failure_message(&self) -> Option<&str> {
        match self {
            Self::Typed(v) => v.error.as_ref().map(|e| e.message.as_str()).or_else(|| {
                v.submission_refusal
                    .as_ref()
                    .and_then(|r| r.reason.as_deref())
            }),
            Self::Rejected { .. } => None,
        }
    }
}

fn require(condition: bool, diagnostic: &str) -> Result<(), String> {
    if condition {
        Ok(())
    } else {
        Err(diagnostic.into())
    }
}
fn uuid(value: &str) -> bool {
    value.len() == 36
        && value.bytes().enumerate().all(|(index, byte)| {
            if [8, 13, 18, 23].contains(&index) {
                byte == b'-'
            } else {
                byte.is_ascii_hexdigit()
            }
        })
}
fn validate_error(value: &TransportError) -> Result<(), String> {
    require(
        ["acquisition", "submission", "local"].contains(&value.stage.as_str()),
        "unknown transport error stage",
    )?;
    require(
        [
            "xpc_error",
            "interrupted",
            "invalidated",
            "rpc_timeout",
            "overall_deadline",
            "attempt_limit",
            "invalid_control",
            "unsupported_protocol",
            "control_too_large",
            "proxy_type_mismatch",
            "clock_error",
            "encoding_failed",
            "input_read_failed",
        ]
        .contains(&value.reason.as_str()),
        "unknown transport error reason",
    )?;
    require(
        value.message.len() <= 1024 && value.domain.as_ref().is_none_or(|s| s.len() <= 128),
        "transport error exceeds retained string limit",
    )?;
    require(
        value.domain.is_some() == value.code.is_some(),
        "native domain/code must be observed together",
    )?;
    require(
        !value.domain_truncated || value.domain.is_some(),
        "domain truncation without a domain",
    )?;
    // UTF-8 prefix truncation can end before the cap's final byte.
    require(
        !value.message_truncated || value.message.len() >= 1021,
        "impossible message truncation",
    )?;
    require(
        !value.domain_truncated || value.domain.as_ref().is_some_and(|s| s.len() >= 125),
        "impossible domain truncation",
    )
}
fn validate_control(value: &Control) -> Result<(), String> {
    require(value.bytes_received >= 0, "invalid control byte count")?;
    require(
        value.sha256.len() == 64
            && value
                .sha256
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b)),
        "invalid control byte hash",
    )?;
    let Some(status) = value.status.as_deref() else {
        return require(
            value.host_pid.is_none()
                && value.host_instance.is_none()
                && value.lease_ms.is_none()
                && value.reason.is_none(),
            "unadmitted control contains recovered claims",
        );
    };
    require(
        value.bytes_received > 0 && value.bytes_received <= CONTROL_BYTES,
        "admitted control exceeds its byte boundary",
    )?;
    require(
        value
            .host_pid
            .is_some_and(|pid| pid > 0 && i32::try_from(pid).is_ok())
            && value.host_instance.as_deref().is_some_and(uuid),
        "admitted control lacks host-reported identity",
    )?;
    match status {
        "granted" => require(
            value.lease_ms.is_some_and(|n| (1..=5000).contains(&n)) && value.reason.is_none(),
            "invalid granted lease",
        ),
        "occupied" => require(
            value.lease_ms.is_none() && value.reason.is_none(),
            "occupied control carries a grant or reason",
        ),
        "reservation_refused" => require(
            value.lease_ms.is_none()
                && value.reason.as_deref().is_some_and(|s| {
                    ["wrong", "expired", "absent", "consumed", "clock_error"].contains(&s)
                }),
            "invalid submission refusal",
        ),
        _ => Err("unknown admitted control status".into()),
    }
}

/// Strict standard base64: no ignored bytes, alternate alphabet, excess
/// padding, or nonzero padding bits. Decode only the bounded retained bytes.
#[cfg(test)]
pub(crate) fn decode_base64(text: &str) -> Result<Vec<u8>, String> {
    fn digit(byte: u8) -> Option<u8> {
        match byte {
            b'A'..=b'Z' => Some(byte - b'A'),
            b'a'..=b'z' => Some(byte - b'a' + 26),
            b'0'..=b'9' => Some(byte - b'0' + 52),
            b'+' => Some(62),
            b'/' => Some(63),
            _ => None,
        }
    }
    require(
        text.len() % 4 == 0 && text.len() <= REPLY_CAPTURE_BYTES.div_ceil(3) * 4,
        "invalid or oversized reply base64",
    )?;
    let mut output = Vec::with_capacity((text.len() / 4 * 3).min(REPLY_CAPTURE_BYTES));
    let chunks = text.as_bytes().chunks_exact(4);
    let count = chunks.len();
    for (index, bytes) in chunks.enumerate() {
        let a = digit(bytes[0]).ok_or("invalid reply base64 alphabet")?;
        let b = digit(bytes[1]).ok_or("invalid reply base64 alphabet")?;
        output.push(a << 2 | b >> 4);
        if bytes[2] == b'=' {
            require(
                index + 1 == count && bytes[3] == b'=' && b & 15 == 0,
                "invalid reply base64 padding",
            )?;
        } else {
            let c = digit(bytes[2]).ok_or("invalid reply base64 alphabet")?;
            output.push(b << 4 | c >> 2);
            if bytes[3] == b'=' {
                require(
                    index + 1 == count && c & 3 == 0,
                    "invalid reply base64 padding",
                )?;
            } else {
                let d = digit(bytes[3]).ok_or("invalid reply base64 alphabet")?;
                output.push(c << 6 | d);
            }
        }
    }
    require(
        output.len() <= REPLY_CAPTURE_BYTES,
        "decoded reply exceeds retention limit",
    )?;
    Ok(output)
}

fn validate_capture(value: &Capture) -> Result<(), String> {
    require(
        value.kind == "runner_client_capture"
            && value.protocol_version == i64::from(crate::json_contract::RUNNER_PROTOCOL_VERSION),
        "invalid client capture identity",
    )?;
    require(
        value.client_pid > 0
            && i32::try_from(value.client_pid).is_ok()
            && value.clock == "mach_continuous_time_ns"
            && value.timeout_ms > 0,
        "invalid client clock or identity",
    )?;
    if value.clock_available {
        require(
            value.started_continuous_ns.is_some()
                && value.deadline_continuous_ns.is_some()
                && value.ended_continuous_ns.is_some(),
            "available clock lacks readings",
        )?;
    } else {
        require(
            value.terminal == "local_error"
                && value
                    .error
                    .as_ref()
                    .is_some_and(|e| e.reason == "clock_error"),
            "unavailable clock lacks its terminal failure",
        )?;
        require(
            value.ended_continuous_ns.is_none(),
            "failed clock invents a terminal reading",
        )?;
        if value.started_continuous_ns.is_none() || value.deadline_continuous_ns.is_none() {
            require(
                value.attempts.is_empty() && value.submission.state == "not_invoked",
                "initial clock failure invents acquisition or execution",
            )?;
        }
    }
    let elapsed = match (value.started_continuous_ns, value.ended_continuous_ns) {
        (Some(start), Some(end)) => {
            require(end >= start, "backwards continuous clock")?;
            Some((end - start) / 1_000_000)
        }
        _ => None,
    };
    let deadline_elapsed = value
        .ended_continuous_ns
        .zip(value.deadline_continuous_ns)
        .is_some_and(|(end, deadline)| end >= deadline);
    require(
        value.attempts.len() <= ATTEMPT_LIMIT,
        "too many acquisition attempts",
    )?;
    let mut previous_end = 0;
    let mut ids = std::collections::HashSet::new();
    for (index, attempt) in value.attempts.iter().enumerate() {
        require(
            usize::try_from(attempt.ordinal).ok() == Some(index + 1)
                && uuid(&attempt.attempt_id)
                && ids.insert(attempt.attempt_id.to_ascii_lowercase()),
            "invalid acquisition attempt identity",
        )?;
        if value.clock_available {
            require(
                attempt.started_elapsed_ms.is_some() && attempt.ended_elapsed_ms.is_some(),
                "available attempt clock lacks readings",
            )?;
        }
        if let Some(start) = attempt.started_elapsed_ms {
            require(start >= previous_end, "backwards acquisition chronology")?;
        }
        if let Some(end) = attempt.ended_elapsed_ms {
            require(
                attempt.started_elapsed_ms.is_none_or(|start| end >= start)
                    && elapsed.is_none_or(|total| end <= total),
                "invalid acquisition attempt end",
            )?;
            previous_end = end;
        }
        if let Some(control) = &attempt.control {
            validate_control(control)?;
        }
        if let Some(error) = &attempt.error {
            validate_error(error)?;
            require(
                error.stage == "acquisition"
                    || (error.stage == "local"
                        && ["clock_error", "encoding_failed"].contains(&error.reason.as_str())),
                "attempt carries an unrelated error stage",
            )?;
            let reason_matches = match attempt.outcome.as_str() {
                "transport_error" => {
                    ["xpc_error", "interrupted", "invalidated"].contains(&error.reason.as_str())
                }
                "timeout" => ["rpc_timeout", "overall_deadline"].contains(&error.reason.as_str()),
                "protocol_error" => [
                    "invalid_control",
                    "unsupported_protocol",
                    "control_too_large",
                ]
                .contains(&error.reason.as_str()),
                "local_error" => ["proxy_type_mismatch", "clock_error", "encoding_failed"]
                    .contains(&error.reason.as_str()),
                _ => false,
            };
            require(
                reason_matches,
                "attempt outcome disagrees with its error reason",
            )?;
        }
        let status = attempt.control.as_ref().and_then(|c| c.status.as_deref());
        match attempt.outcome.as_str() {
            "granted" => require(
                status == Some("granted")
                    && attempt.error.is_none()
                    && index + 1 == value.attempts.len(),
                "invalid granted attempt",
            )?,
            "occupied" => require(
                status == Some("occupied") && attempt.error.is_none(),
                "invalid occupied attempt",
            )?,
            "transport_error" | "timeout" | "local_error" => require(
                attempt.control.is_none() && attempt.error.is_some(),
                "failed attempt lacks its error or invents control",
            )?,
            "protocol_error" => require(
                attempt.error.is_some() && status.is_none(),
                "invalid protocol-error attempt",
            )?,
            _ => return Err("unknown acquisition attempt outcome".into()),
        }
        if ["protocol_error", "local_error"].contains(&attempt.outcome.as_str()) {
            require(
                index + 1 == value.attempts.len(),
                "acquisition continued after terminal attempt failure",
            )?;
        }
    }
    if let Some(error) = &value.error {
        validate_error(error)?;
    }
    let granted = value
        .attempts
        .last()
        .is_some_and(|a| a.outcome == "granted");
    match value.acquisition_stop.as_str() {
        "granted" => require(
            granted,
            "acquisition grant has no admitted granting attempt",
        )?,
        "overall_deadline" => require(
            !granted && value.terminal == "xpc_timeout" && deadline_elapsed,
            "invalid acquisition deadline",
        )?,
        "attempt_limit" => require(
            !granted
                && value.attempts.len() == ATTEMPT_LIMIT
                && value.terminal == "acquisition_failed",
            "invalid acquisition attempt limit",
        )?,
        "protocol_error" => require(
            !granted
                && value.terminal == "protocol_error"
                && value
                    .attempts
                    .last()
                    .is_some_and(|a| a.outcome == "protocol_error"),
            "invalid acquisition protocol failure",
        )?,
        "local_error" => require(
            !granted
                && value.terminal == "local_error"
                && (!value.clock_available
                    || value
                        .attempts
                        .last()
                        .is_none_or(|a| a.outcome == "local_error")),
            "invalid local acquisition failure",
        )?,
        _ => return Err("unknown acquisition stop reason".into()),
    }
    let invoked = match value.submission.state.as_str() {
        "not_invoked" => {
            require(
                value.submission.invoked_elapsed_ms.is_none(),
                "uninvoked submission carries invocation time",
            )?;
            false
        }
        "invoked" => {
            require(
                granted && value.acquisition_stop == "granted",
                "submission lacks its reservation grant",
            )?;
            require(
                !value.clock_available || value.submission.invoked_elapsed_ms.is_some(),
                "available invocation clock lacks its reading",
            )?;
            require(
                value
                    .submission
                    .invoked_elapsed_ms
                    .is_none_or(|n| n >= previous_end && elapsed.is_none_or(|total| n <= total)),
                "invalid execution invocation time",
            )?;
            true
        }
        _ => return Err("unknown client submission state".into()),
    };
    require(
        invoked || (value.runner_reply.is_none() && value.submission_refusal.is_none()),
        "uninvoked execution carries a host reply",
    )?;
    require(
        value.runner_reply.is_some() == (value.terminal == "runner_reply"),
        "terminal disagrees with host reply capture",
    )?;
    require(
        value.terminal != "submission_refused" || value.submission_refusal.is_some(),
        "terminal lacks its control refusal",
    )?;
    if let Some(control) = &value.submission_refusal {
        require(
            invoked && ["submission_refused", "protocol_error"].contains(&value.terminal.as_str()),
            "terminal disagrees with submission control",
        )?;
        validate_control(control)?;
        if value.terminal == "protocol_error" {
            require(
                control.status.is_none(),
                "invalid submission control recovers claims",
            )?;
        }
    }
    match value.terminal.as_str() {
        "runner_reply" => require(
            invoked && value.error.is_none(),
            "invalid received runner reply",
        )?,
        "submission_refused" => {
            require(
                invoked && value.error.is_none(),
                "invalid refused execution",
            )?;
            let refusal = value.submission_refusal.as_ref().unwrap();
            validate_control(refusal)?;
            require(
                refusal.status.as_deref() == Some("reservation_refused"),
                "wrong submission control status",
            )?;
        }
        "xpc_error" => require(
            invoked
                && value.error.as_ref().is_some_and(|e| {
                    e.stage == "submission"
                        && [
                            "xpc_error",
                            "interrupted",
                            "invalidated",
                            "proxy_type_mismatch",
                        ]
                        .contains(&e.reason.as_str())
                }),
            "invalid post-submission XPC error",
        )?,
        "xpc_timeout" => require(
            value.error.as_ref().is_some_and(|e| {
                e.reason == "overall_deadline"
                    && e.stage == if invoked { "submission" } else { "acquisition" }
            }) && deadline_elapsed,
            "timeout lacks elapsed overall deadline",
        )?,
        "acquisition_failed" => require(
            !invoked
                && value.acquisition_stop == "attempt_limit"
                && value
                    .error
                    .as_ref()
                    .is_some_and(|e| e.stage == "acquisition" && e.reason == "attempt_limit"),
            "invalid acquisition failure",
        )?,
        "protocol_error" => require(
            value.error.as_ref().is_some_and(|e| {
                e.stage == (if invoked { "submission" } else { "acquisition" })
                    && [
                        "invalid_control",
                        "unsupported_protocol",
                        "control_too_large",
                    ]
                    .contains(&e.reason.as_str())
            }),
            "invalid terminal protocol error",
        )?,
        "local_error" => require(
            value.error.as_ref().is_some_and(|e| {
                (e.stage == "local"
                    && ["clock_error", "encoding_failed", "input_read_failed"]
                        .contains(&e.reason.as_str()))
                    || (e.stage == "acquisition" && e.reason == "proxy_type_mismatch")
            }) && (!invoked || !value.clock_available),
            "invalid terminal local error",
        )?,
        _ => return Err("unknown client terminal event".into()),
    }
    if granted && !invoked {
        require(
            value.terminal == "xpc_timeout" || value.terminal == "local_error",
            "grant lost without an explicit pre-invocation stop",
        )?;
    }
    if let Some(reply) = &value.runner_reply {
        require(
            reply.bytes_received >= 0
                && reply.bytes_retained >= 0
                && reply.bytes_retained == reply.bytes_received.min(REPLY_CAPTURE_BYTES as i64)
                && reply.truncated == (reply.bytes_retained < reply.bytes_received),
            "inconsistent reply byte retention",
        )?;
        require(
            usize::try_from(reply.bytes_retained).ok() == Some(reply.data.len()),
            "reply bytes disagree with retained count",
        )?;
    }
    Ok(())
}

impl RunnerClientRun {
    /// A current client failure, without inventing a host result. Host response
    /// version/semantic admission remains the caller's separate responsibility.
    pub fn failure(&self) -> Option<(&'static str, String)> {
        if let Some(error) = self
            .request_delivery
            .as_ref()
            .and_then(|d| d.error.as_ref())
        {
            return Some(("tool_error", error.clone()));
        }
        if self.transport_admission != "accepted" {
            let outcome = match self.transport_admission.as_str() {
                "missing" => "missing_runner_client",
                "unsupported" => "unsupported_runner_client",
                _ => "malformed_runner_client",
            };
            return Some((
                outcome,
                self.transport_error
                    .clone()
                    .unwrap_or_else(|| "client capture unavailable".into()),
            ));
        }
        if let Some(error) = &self.runner_reply_error {
            return Some((
                match error.refusal {
                    ReplyRefusal::Truncated => "runner_reply_truncated",
                    ReplyRefusal::UnsupportedSchema => "unsupported_runner_response",
                    ReplyRefusal::Malformed => "malformed_runner_response",
                },
                error.message.clone(),
            ));
        }
        let value = self.transport.as_ref().unwrap();
        let terminal = value
            .terminal()
            .expect("accepted capture has a terminal event");
        let outcome = match terminal {
            "runner_reply" => return None,
            "xpc_error" => "xpc_error",
            "xpc_timeout" => "xpc_timeout",
            "acquisition_failed" => "xpc_acquisition_failed",
            "submission_refused" => "xpc_submission_refused",
            "protocol_error" => "xpc_protocol_error",
            _ => "runner_client_error",
        };
        let message = value.failure_message().unwrap_or(terminal);
        Some((outcome, message.to_string()))
    }
    pub fn fallback_eligible(&self) -> bool {
        self.transport_admission == "accepted"
            && self
                .request_delivery
                .as_ref()
                .is_none_or(|d| d.error.is_none())
            && self
                .transport
                .as_ref()
                .is_some_and(|v| v.terminal() == Some("xpc_error"))
    }
}

/// Binary capture admission keeps original rejected bytes and interprets only
/// complete retained frames. The helper has already drained both output pipes;
/// this cap changes retained evidence, never producer reception or execution.
fn parse_runner_client_output(
    argv: &[OsString],
    started: u64,
    ended: u64,
    out: &std::process::Output,
    request_delivery: Option<RequestDelivery>,
) -> (RunnerClientRun, Option<PWRunnerRunResult>) {
    let limit = crate::utils::RUNNER_CAPTURE_BYTES;
    let retained = &out.stdout[..out.stdout.len().min(limit)];
    let stdout_truncated = out.stdout.len() > limit;
    let stderr_retained = &out.stderr[..out.stderr.len().min(limit)];
    let mut run = RunnerClientRun {
        argv: argv.iter().map(|s| s.to_string_lossy().into_owned()).collect(),
        started_at_unix_ms: started,
        ended_at_unix_ms: ended,
        exit_code: out.status.code().unwrap_or(1),
        request_delivery,
        output: OutputCapture {
            stdout_parse_error: None,
            stdout_truncated,
            stdout_capture_error: stdout_truncated.then(|| format!(
                "controller truncated runner client stdout: received {} bytes, retained {} bytes (cap {})",
                out.stdout.len(), retained.len(), limit)),
            stdout_bytes_received: Some(out.stdout.len()),
            stdout_bytes_retained: Some(retained.len()),
            stderr_bytes_received: Some(out.stderr.len()),
            stderr_bytes_retained: Some(stderr_retained.len()),
            capture_limit_bytes: limit,
            stdout_raw: None,
            stderr: String::from_utf8_lossy(stderr_retained).into_owned(),
            stderr_truncated: out.stderr.len() > limit,
        },
        transport: None,
        transport_admission: "missing".into(),
        transport_error: None,
        submission: "unknown".into(),
        runner_reply_error: None,
    };
    let admission = (|| -> Result<Capture, (&str, String)> {
        if let Some(error) = run.request_delivery.as_ref().and_then(|d| d.error.as_ref()) {
            return Err(("delivery_failed", error.clone()));
        }
        if let Some(error) = &run.output.stdout_capture_error {
            return Err(("malformed", error.clone()));
        }
        if retained.is_empty() {
            return Err(("missing", "runner client produced no capture".into()));
        }
        let capture: Capture = crate::porcelain::decode(retained).map_err(|error| {
            let status = match error {
                FrameError::UnsupportedSchema => "unsupported",
                FrameError::Malformed(_) => "malformed",
            };
            let error = error.to_string();
            run.output.stdout_parse_error = Some(error.clone());
            (status, error)
        })?;
        if capture.protocol_version != i64::from(crate::json_contract::RUNNER_PROTOCOL_VERSION) {
            return Err((
                "unsupported",
                format!(
                    "client capture protocol {} is unsupported",
                    capture.protocol_version
                ),
            ));
        }
        validate_capture(&capture).map_err(|error| ("malformed", error))?;
        Ok(capture)
    })();
    match admission {
        Ok(capture) => {
            run.transport_admission = "accepted".into();
            run.submission = capture.submission.state.clone();
            let reply = capture.runner_reply.as_ref().and_then(|raw| {
                let (refusal, message) = if raw.truncated {
                    (
                        ReplyRefusal::Truncated,
                        "runner reply retention was truncated; no complete host reply is available"
                            .into(),
                    )
                } else {
                    match crate::porcelain::decode::<PWRunnerRunResult>(&raw.data) {
                        Ok(reply) => return Some(reply),
                        // The host frame names another schema: a version
                        // refusal, with its bytes retained in the capture.
                        Err(FrameError::UnsupportedSchema) => (
                            ReplyRefusal::UnsupportedSchema,
                            "runner reply frame names an unsupported porcelain schema; \
                             this controller reads only the schema it was built with"
                                .into(),
                        ),
                        Err(FrameError::Malformed(error)) => (
                            ReplyRefusal::Malformed,
                            format!("runner reply is not a complete typed record: {error}"),
                        ),
                    }
                };
                run.runner_reply_error = Some(ReplyError { refusal, message });
                None
            });
            run.transport = Some(TransportCapture::Typed(capture));
            (run, reply)
        }
        Err((status, error)) => {
            run.transport_admission = status.into();
            run.transport_error = Some(error);
            if !retained.is_empty() {
                run.transport = Some(TransportCapture::Rejected {
                    format: "porcelain",
                    data_base64: retained.to_vec(),
                });
            }
            (run, None)
        }
    }
}

unsafe extern "C" {
    fn mach_continuous_time() -> u64;
}
fn deadline_ticks(
    now: u64,
    milliseconds: u64,
    numerator: u32,
    denominator: u32,
) -> Result<u64, String> {
    require(
        numerator != 0 && denominator != 0,
        "invalid continuous-clock timebase",
    )?;
    let nanoseconds = u128::from(milliseconds) * 1_000_000;
    let ticks = (nanoseconds * u128::from(denominator)).div_ceil(u128::from(numerator));
    Ok(now.saturating_add(ticks.min(u128::from(u64::MAX)) as u64))
}
fn continuous_deadline(milliseconds: u64) -> Result<u64, String> {
    let mut info = libc::mach_timebase_info { numer: 0, denom: 0 };
    if unsafe { libc::mach_timebase_info(&mut info) } != 0 {
        return Err("cannot read continuous-clock timebase".into());
    }
    deadline_ticks(
        unsafe { mach_continuous_time() },
        milliseconds,
        info.numer,
        info.denom,
    )
}
fn client_argv(
    timeout_ms: u64,
    deadline: u64,
    connection: &RunnerConnectionKind,
) -> Result<Vec<OsString>, String> {
    let tool = resolve_contents_macos_tool("pw-runner-client")?;
    let mut argv = vec![
        tool.into_os_string(),
        "run".into(),
        "--timeout-ms".into(),
        timeout_ms.to_string().into(),
        "--deadline-ticks".into(),
        deadline.to_string().into(),
    ];
    match connection {
        RunnerConnectionKind::XpcService => {}
        RunnerConnectionKind::MachService { privileged } => {
            argv.push("--mach-service".into());
            if *privileged {
                argv.push("--privileged".into());
            }
        }
    }
    Ok(argv)
}

/// The deadline starts before resolution/spawn/stdin delivery, not when the
/// helper finally begins acquiring a connection. There is one invocation.
pub fn run_pw_runner_client(
    service_name: &str,
    request: &str,
    timeout_ms: u64,
    connection: &RunnerConnectionKind,
) -> Result<(RunnerClientRun, Option<PWRunnerRunResult>), String> {
    let timeout_ms = timeout_ms.max(1);
    let deadline = continuous_deadline(timeout_ms)?;
    let mut argv = client_argv(timeout_ms, deadline, connection)?;
    argv.push("--request".into());
    argv.push("-".into());
    argv.push(service_name.into());
    run_client_stdin(&argv, request.as_bytes().to_vec())
}
fn run_client_stdin(
    argv: &[OsString],
    request: Vec<u8>,
) -> Result<(RunnerClientRun, Option<PWRunnerRunResult>), String> {
    run_client_stdin_with_clock(argv, request, now_unix_ms)
}
fn run_client_stdin_with_clock(
    argv: &[OsString],
    request: Vec<u8>,
    mut clock: impl FnMut() -> u64,
) -> Result<(RunnerClientRun, Option<PWRunnerRunResult>), String> {
    let started = clock();
    let mut command = Command::new(&argv[0]);
    command.args(&argv[1..]);
    let (out, delivery) = run_with_stdin(command, request)
        .map_err(|e| format!("failed to run pw-runner-client: {e}"))?;
    let ended = clock();
    Ok(parse_runner_client_output(
        argv,
        started,
        ended,
        &out,
        Some(delivery),
    ))
}

#[cfg(test)]
fn encode_base64(bytes: &[u8]) -> String {
    let alphabet = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut result = String::new();
    for chunk in bytes.chunks(3) {
        result.push(alphabet[(chunk[0] >> 2) as usize] as char);
        result.push(
            alphabet[(((chunk[0] & 3) << 4) | chunk.get(1).copied().unwrap_or(0) >> 4) as usize]
                as char,
        );
        result.push(if chunk.len() > 1 {
            alphabet[(((chunk[1] & 15) << 2) | chunk.get(2).copied().unwrap_or(0) >> 6) as usize]
                as char
        } else {
            '='
        });
        result.push(if chunk.len() > 2 {
            alphabet[(chunk[2] & 63) as usize] as char
        } else {
            '='
        });
    }
    result
}

#[cfg(test)]
pub(crate) fn test_capture_bytes(reply: Option<&[u8]>) -> Value {
    let mut value = serde_json::json!({
        "kind":"runner_client_capture", "protocol_version":crate::json_contract::RUNNER_PROTOCOL_VERSION,
        "client_pid":123, "clock":"mach_continuous_time_ns", "clock_available":true, "started_continuous_ns":1000000000u64,
        "deadline_continuous_ns":61000000000u64, "ended_continuous_ns":1005000000u64, "timeout_ms":60000,
        "attempts":[{"ordinal":1,"attempt_id":"11111111-1111-4111-8111-111111111111",
            "started_elapsed_ms":0,"ended_elapsed_ms":1,"outcome":"granted",
            "control":{"bytes_received":200,"sha256":"a".repeat(64),"status":"granted",
                "host_pid":42,"host_instance":"22222222-2222-4222-8222-222222222222","lease_ms":5000}}],
        "acquisition_stop":"granted", "submission":{"state":"invoked","invoked_elapsed_ms":2},
        "terminal":if reply.is_some() {"runner_reply"} else {"xpc_error"}
    });
    if let Some(bytes) = reply {
        value["runner_reply"] = serde_json::json!({"bytes_received":bytes.len(),"bytes_retained":bytes.len(),
            "truncated":false,"data_base64":encode_base64(bytes)});
    } else {
        value["error"] = serde_json::json!({"stage":"submission","reason":"xpc_error","domain":"NSCocoaErrorDomain",
            "code":4097,"message":"controlled XPC error","domain_truncated":false,"message_truncated":false});
    }
    value
}

#[cfg(test)]
pub(crate) fn test_shape_capture() -> Value {
    // Field-complete shape sample; mutually exclusive terminal fields are
    // combined only here. Semantic acceptance has independent controls below.
    let mut value = test_capture_bytes(Some(b"{}"));
    let error = serde_json::json!({"stage":"acquisition","reason":"xpc_error","domain":"NSCocoaErrorDomain",
        "code":4097,"message":"constructed","domain_truncated":false,"message_truncated":false});
    value["attempts"][0]["ordinal"] = serde_json::json!(2);
    value["attempts"][0]["started_elapsed_ms"] = serde_json::json!(1);
    value["attempts"][0]["ended_elapsed_ms"] = serde_json::json!(2);
    value["attempts"].as_array_mut().unwrap().insert(0, serde_json::json!({"ordinal":1,
        "attempt_id":"33333333-3333-4333-8333-333333333333", "started_elapsed_ms":0,"ended_elapsed_ms":1,
        "outcome":"transport_error","error":error.clone()}));
    value["error"] = error;
    value["submission_refusal"] = serde_json::json!({"bytes_received":100,"sha256":"b".repeat(64),
        "status":"reservation_refused","host_pid":42,"host_instance":"22222222-2222-4222-8222-222222222222","reason":"wrong"});
    value
}

#[cfg(test)]
pub(crate) fn test_client_run(reply: Option<&Value>) -> RunnerClientRun {
    // Authored fixture input for controlled orchestration, never transport
    // admission. Binary admission itself is exercised by binary_tests.
    let bytes = reply.map(|r| serde_json::to_vec(r).unwrap());
    test_client_run_bytes(bytes.as_deref())
}
#[cfg(test)]
pub(crate) fn test_client_run_bytes(reply: Option<&[u8]>) -> RunnerClientRun {
    let capture: Capture = serde_json::from_value(test_capture_bytes(reply)).unwrap();
    RunnerClientRun {
        argv: vec!["controlled-client".into()],
        started_at_unix_ms: 1000,
        ended_at_unix_ms: 2500,
        exit_code: if reply.is_some() { 0 } else { 1 },
        request_delivery: Some(RequestDelivery {
            bytes_written: 2,
            error: None,
        }),
        output: OutputCapture {
            stdout_parse_error: None,
            stdout_truncated: false,
            stdout_capture_error: None,
            stdout_bytes_received: None,
            stdout_bytes_retained: None,
            stderr_bytes_received: Some(30),
            stderr_bytes_retained: Some(30),
            capture_limit_bytes: crate::utils::RUNNER_CAPTURE_BYTES,
            stdout_raw: None,
            stderr: "fixed runner-client diagnostic".into(),
            stderr_truncated: false,
        },
        transport: Some(TransportCapture::Typed(capture)),
        transport_admission: "accepted".into(),
        transport_error: None,
        submission: "invoked".into(),
        runner_reply_error: None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn reply_capture_limit_matches_documented_capacity() {
        let manifest: serde_json::Value =
            serde_json::from_str(include_str!("../../docs/limits.json")).unwrap();
        let limits = manifest["limits"].as_array().unwrap();
        let owned: std::collections::BTreeMap<&str, u64> = limits
            .iter()
            .filter(|row| {
                row["checks"].as_array().unwrap().iter().any(|check| {
                    check["path"] == "controller/src/runner_client.rs" && check["kind"] == "value"
                })
            })
            .map(|row| (row["id"].as_str().unwrap(), row["value"].as_u64().unwrap()))
            .collect();
        assert_eq!(
            owned,
            std::collections::BTreeMap::from([(
                "client_reply_retention",
                REPLY_CAPTURE_BYTES as u64
            )])
        );
    }
    #[test]
    fn strict_base64_rejects_noncanonical_or_ignored_bytes() {
        for (text, expected) in [("", ""), ("Zg==", "f"), ("Zm8=", "fo"), ("Zm9v", "foo")] {
            assert_eq!(decode_base64(text).unwrap(), expected.as_bytes());
        }
        for bad in [
            "Zg", "Zh==", "Zm9=", "Zg===", "Zg==\n", "Zg==AAAA", "_w==", "====",
        ] {
            assert!(decode_base64(bad).is_err(), "{bad}");
        }
    }
    #[test]
    fn deadline_conversion_rounds_up_and_saturates_without_resetting_the_origin() {
        assert_eq!(deadline_ticks(17, 1, 125, 3).unwrap(), 24_017);
        assert_eq!(deadline_ticks(17, 1, 3, 1).unwrap(), 333_351);
        assert_eq!(
            deadline_ticks(u64::MAX - 1, u64::MAX, 1, u32::MAX).unwrap(),
            u64::MAX
        );
        assert!(deadline_ticks(0, 1, 0, 1).is_err());
        assert!(deadline_ticks(0, 1, 1, 0).is_err());
    }
    #[test]
    fn backwards_clock_readings_are_retained() {
        let argv = vec![OsString::from("/usr/bin/true")];
        for (started, ended) in [(5_000, 4_000), (5_999, 5_001)] {
            let mut readings = [started, ended].into_iter();
            let (run, _) =
                run_client_stdin_with_clock(&argv, Vec::new(), || readings.next().unwrap())
                    .unwrap();
            assert!(readings.next().is_none());
            assert_eq!(
                (run.started_at_unix_ms, run.ended_at_unix_ms),
                (started, ended)
            );
            assert_eq!(run.exit_code, 0);
        }
    }
}

#[cfg(test)]
mod binary_tests {
    use super::*;

    // Authored independently of the generated writer/schema field tables. Only
    // the negotiated fingerprint follows the candidate so field/tag mistakes
    // are not silently copied into these admission expectations.
    fn value(kind: u8, bytes: &[u8]) -> Vec<u8> {
        let mut out = vec![kind];
        out.extend_from_slice(&(bytes.len() as u32).to_le_bytes());
        out.extend_from_slice(bytes);
        out
    }
    fn signed(n: i64) -> Vec<u8> {
        value(2, &n.to_le_bytes())
    }
    fn unsigned(n: u64) -> Vec<u8> {
        value(3, &n.to_le_bytes())
    }
    fn text(s: &str) -> Vec<u8> {
        value(4, s.as_bytes())
    }
    fn boolean(b: bool) -> Vec<u8> {
        value(1, &[u8::from(b)])
    }
    fn list(items: &[Vec<u8>]) -> Vec<u8> {
        let mut bytes = (items.len() as u32).to_le_bytes().to_vec();
        for item in items {
            bytes.extend_from_slice(item);
        }
        value(7, &bytes)
    }
    fn record(id: u16, fields: &[(u16, Vec<u8>)]) -> Vec<u8> {
        let mut bytes = id.to_le_bytes().to_vec();
        for (tag, item) in fields {
            bytes.extend_from_slice(&tag.to_le_bytes());
            bytes.extend_from_slice(item);
        }
        value(6, &bytes)
    }
    fn frame(record: Vec<u8>) -> Vec<u8> {
        let mut bytes = b"PWP1".to_vec();
        bytes.extend_from_slice(&crate::porcelain_records::FINGERPRINT);
        bytes.extend_from_slice(&record);
        bytes
    }
    fn host() -> Vec<u8> {
        frame(record(
            55,
            &[
                (
                    1,
                    signed(i64::from(crate::json_contract::RESPONSE_SCHEMA_VERSION)),
                ),
                (2, text("typed\0é")),
                (4, signed(1)),
                (5, text("future_native_outcome")),
                (7, signed(42)),
                (13, list(&[])),
                (17, list(&[])),
            ],
        ))
    }
    fn capture(host: Option<&[u8]>, protocol: i64, client_pid: i64, received: i64) -> Vec<u8> {
        let control = record(
            34,
            &[
                (1, signed(200)),
                (2, text(&"a".repeat(64))),
                (3, text("granted")),
                (4, signed(42)),
                (5, text("22222222-2222-4222-8222-222222222222")),
                (6, signed(5000)),
            ],
        );
        let attempt = record(
            19,
            &[
                (1, signed(1)),
                (2, text("11111111-1111-4111-8111-111111111111")),
                (3, unsigned(0)),
                (4, unsigned(1)),
                (5, text("granted")),
                (6, control),
            ],
        );
        let submission = record(60, &[(1, text("invoked")), (2, unsigned(2))]);
        let mut fields = vec![
            (1, text("runner_client_capture")),
            (2, signed(protocol)),
            (3, signed(client_pid)),
            (4, text("mach_continuous_time_ns")),
            (5, boolean(true)),
            (6, unsigned(1_000_000_000)),
            (7, unsigned(61_000_000_000)),
            (8, unsigned(1_005_000_000)),
            (9, unsigned(60_000)),
            (10, list(&[attempt])),
            (11, text("granted")),
            (12, submission),
            (
                13,
                text(if host.is_some() {
                    "runner_reply"
                } else {
                    "xpc_error"
                }),
            ),
        ];
        if let Some(bytes) = host {
            fields.push((
                15,
                record(
                    51,
                    &[
                        (1, signed(received)),
                        (2, signed(bytes.len() as i64)),
                        (3, boolean(false)),
                        (4, value(5, bytes)),
                    ],
                ),
            ));
        } else {
            fields.push((
                14,
                record(
                    67,
                    &[
                        (1, text("submission")),
                        (2, text("xpc_error")),
                        (5, text("independent failure")),
                        (6, boolean(false)),
                        (7, boolean(false)),
                    ],
                ),
            ));
        }
        frame(record(32, &fields))
    }
    fn parse(
        bytes: Vec<u8>,
        delivery: Option<&str>,
    ) -> (RunnerClientRun, Option<PWRunnerRunResult>) {
        let output = std::process::Output {
            status: std::os::unix::process::ExitStatusExt::from_raw(0),
            stdout: bytes,
            stderr: b"diagnostic".to_vec(),
        };
        parse_runner_client_output(
            &[],
            10,
            20,
            &output,
            Some(RequestDelivery {
                bytes_written: 2,
                error: delivery.map(str::to_string),
            }),
        )
    }
    fn protocol() -> i64 {
        i64::from(crate::json_contract::RUNNER_PROTOCOL_VERSION)
    }

    #[test]
    fn independent_binary_records_reach_typed_storage_without_text_conversion() {
        let host = host();
        let bytes = capture(Some(&host), protocol(), 123, host.len() as i64);
        let count = bytes.len();
        let (run, reply) = parse(bytes, None);
        assert_eq!(
            run.transport_admission, "accepted",
            "{:?}",
            run.transport_error
        );
        assert_eq!(run.submission, "invoked");
        assert!(run.failure().is_none());
        assert_eq!(reply.unwrap().specimen_id, "typed\0é");
        let Some(TransportCapture::Typed(capture)) = run.transport else {
            panic!("not typed");
        };
        assert_eq!(capture.runner_reply.unwrap().data, host);
        assert_eq!(run.output.stdout_bytes_received, Some(count));
        assert_eq!(run.output.stdout_bytes_retained, Some(count));
        assert!(run.output.stdout_raw.is_none());
    }

    #[test]
    fn arbitrary_rejected_host_bytes_survive_and_do_not_become_claims() {
        for host in [vec![], vec![0, 255, 0], b"{}".to_vec()] {
            let (run, reply) = parse(
                capture(Some(&host), protocol(), 123, host.len() as i64),
                None,
            );
            assert_eq!(run.transport_admission, "accepted");
            assert_eq!(run.failure().unwrap().0, "malformed_runner_response");
            assert!(!run.fallback_eligible());
            assert!(reply.is_none());
            let Some(TransportCapture::Typed(capture)) = run.transport else {
                panic!("not typed");
            };
            assert_eq!(capture.runner_reply.unwrap().data, host);
        }
    }

    #[test]
    fn host_frame_naming_another_schema_is_a_version_refusal_with_bytes_retained() {
        let mut other = host();
        other[4] ^= 1;
        // A body that is also unreadable cannot turn the version refusal into
        // a malformed one: the fingerprint is decided first.
        let mut other_and_cut = other.clone();
        other_and_cut.truncate(40);
        for host in [other, other_and_cut] {
            let (run, reply) = parse(
                capture(Some(&host), protocol(), 123, host.len() as i64),
                None,
            );
            assert_eq!(run.transport_admission, "accepted");
            assert_eq!(run.submission, "invoked");
            assert!(reply.is_none());
            let (outcome, message) = run.failure().unwrap();
            assert_eq!(outcome, "unsupported_runner_response");
            assert!(
                message.contains("unsupported porcelain schema"),
                "{message}"
            );
            assert!(!run.fallback_eligible());
            // Presentation carries the diagnostic text alone.
            assert_eq!(
                serde_json::to_value(&run).unwrap()["runner_reply_error"],
                message
            );
            let Some(TransportCapture::Typed(capture)) = run.transport else {
                panic!("not typed");
            };
            assert_eq!(capture.runner_reply.unwrap().data, host);
        }
        // A header cut inside the fingerprint names no schema.
        let cut = host()[..20].to_vec();
        let (run, _) = parse(capture(Some(&cut), protocol(), 123, cut.len() as i64), None);
        assert_eq!(run.failure().unwrap().0, "malformed_runner_response");
    }

    #[test]
    fn malformed_capture_keeps_exact_bytes_and_no_recovered_submission() {
        let good = capture(None, protocol(), 123, 0);
        let mut unsupported = good.clone();
        unsupported[4] ^= 1;
        let mut trailing = good.clone();
        trailing.push(0);
        for bytes in [
            vec![0, 255, 0],
            good[..good.len() - 1].to_vec(),
            unsupported,
            trailing,
            capture(None, protocol(), i64::MAX, 0),
            capture(Some(&[0]), protocol(), 123, -1),
        ] {
            let (run, reply) = parse(bytes.clone(), None);
            assert_ne!(run.transport_admission, "accepted");
            assert_eq!(run.submission, "unknown");
            assert!(reply.is_none() && run.runner_reply_error.is_none());
            assert!(run.output.stdout_raw.is_none());
            assert!(!run.fallback_eligible());
            let Some(TransportCapture::Rejected { data_base64, .. }) = run.transport else {
                panic!("no raw rejection");
            };
            assert_eq!(data_base64, bytes);
        }
    }

    #[test]
    fn unsupported_protocol_and_delivery_failure_preserve_boundaries() {
        let (run, reply) = parse(capture(None, protocol() + 1, 123, 0), None);
        assert_eq!(run.transport_admission, "unsupported");
        assert_eq!(run.submission, "unknown");
        assert!(reply.is_none());
        let bytes = capture(Some(&host()), protocol(), 123, host().len() as i64);
        let (run, reply) = parse(bytes.clone(), Some("controlled delivery failure"));
        assert_eq!(run.transport_admission, "delivery_failed");
        assert_eq!(run.failure().unwrap().0, "tool_error");
        assert_eq!(run.submission, "unknown");
        assert!(reply.is_none() && run.runner_reply_error.is_none());
        let Some(TransportCapture::Rejected { data_base64, .. }) = run.transport else {
            panic!("no receipt");
        };
        assert_eq!(data_base64, bytes);
    }

    #[test]
    fn typed_transport_failure_owns_fallback_and_public_rejection_formats_at_output() {
        let (run, reply) = parse(capture(None, protocol(), 123, 0), None);
        assert_eq!(run.transport_admission, "accepted");
        assert_eq!(
            run.failure().unwrap(),
            ("xpc_error", "independent failure".into())
        );
        assert!(run.fallback_eligible());
        assert!(reply.is_none());
        let (bad, _) = parse(vec![0, 255, 0], None);
        // Presentation alone converts opaque bytes to base64.
        let json = serde_json::to_value(&bad).unwrap();
        assert_eq!(json["transport"]["format"], "porcelain");
        assert_eq!(json["transport"]["data_base64"], "AP8A");
        assert!(json["stdout_raw"].is_null());
    }
    #[test]
    fn typed_capture_semantics_reject_conflicts_without_repair() {
        let original: Capture = crate::porcelain::decode(&capture(
            Some(&host()),
            protocol(),
            123,
            host().len() as i64,
        ))
        .unwrap();
        assert!(validate_capture(&original).is_ok());
        let mutations: Vec<Box<dyn Fn(&mut Capture)>> = vec![
            Box::new(|v| v.submission.state = "not_invoked".into()),
            Box::new(|v| v.acquisition_stop = "overall_deadline".into()),
            Box::new(|v| v.attempts[0].ordinal = 2),
            Box::new(|v| v.attempts[0].control.as_mut().unwrap().host_pid = Some(0)),
            Box::new(|v| v.attempts[0].control.as_mut().unwrap().lease_ms = Some(5001)),
            Box::new(|v| v.runner_reply.as_mut().unwrap().bytes_retained = 0),
            Box::new(|v| v.clock_available = false),
        ];
        for mutate in mutations {
            let mut bad = original.clone();
            mutate(&mut bad);
            let before = bad.clone();
            assert!(validate_capture(&bad).is_err(), "{bad:?}");
            assert_eq!(
                bad, before,
                "validation must not repair or discard observations"
            );
        }
    }

    fn typed_failure_run(capture: Capture) -> RunnerClientRun {
        validate_capture(&capture).unwrap();
        let mut run = test_client_run(None);
        run.submission = capture.submission.state.clone();
        run.transport = Some(TransportCapture::Typed(capture));
        run
    }

    #[test]
    fn grant_deadline_and_clock_failure_preserve_submission() {
        let mut deadline: Capture =
            crate::porcelain::decode(&capture(None, protocol(), 123, 0)).unwrap();
        deadline.submission.state = "not_invoked".into();
        deadline.submission.invoked_elapsed_ms = None;
        deadline.terminal = "xpc_timeout".into();
        deadline.deadline_continuous_ns = Some(1_004_000_000);
        let error = deadline.error.as_mut().unwrap();
        error.stage = "acquisition".into();
        error.reason = "overall_deadline".into();
        let run = typed_failure_run(deadline);
        assert_eq!(run.submission, "not_invoked");
        assert_eq!(run.failure().unwrap().0, "xpc_timeout");
        assert!(!run.fallback_eligible());
        for invoked in [false, true] {
            let mut c: Capture =
                crate::porcelain::decode(&capture(None, protocol(), 123, 0)).unwrap();
            c.clock_available = false;
            c.ended_continuous_ns = None;
            c.terminal = "local_error".into();
            c.error.as_mut().unwrap().stage = "local".into();
            c.error.as_mut().unwrap().reason = "clock_error".into();
            if !invoked {
                c.submission.state = "not_invoked".into();
                c.submission.invoked_elapsed_ms = None;
                c.attempts.clear();
                c.acquisition_stop = "local_error".into();
                c.started_continuous_ns = None;
                c.deadline_continuous_ns = None;
            }
            let run = typed_failure_run(c);
            assert_eq!(
                run.submission,
                if invoked { "invoked" } else { "not_invoked" }
            );
            assert!(!run.fallback_eligible());
        }
    }

    #[test]
    fn refusal_and_proxy_failure_are_not_retried_or_host_results() {
        for reason in ["wrong", "expired", "absent", "consumed", "clock_error"] {
            let mut c: Capture =
                crate::porcelain::decode(&capture(None, protocol(), 123, 0)).unwrap();
            c.error = None;
            c.terminal = "submission_refused".into();
            c.submission_refusal = Some(Control {
                bytes_received: 100,
                sha256: "b".repeat(64),
                status: Some("reservation_refused".into()),
                host_pid: Some(42),
                host_instance: Some("22222222-2222-4222-8222-222222222222".into()),
                lease_ms: None,
                reason: Some(reason.into()),
            });
            let run = typed_failure_run(c);
            assert_eq!(run.submission, "invoked");
            assert_eq!(run.failure().unwrap().0, "xpc_submission_refused");
            assert!(!run.fallback_eligible());
        }
        let mut c: Capture = crate::porcelain::decode(&capture(None, protocol(), 123, 0)).unwrap();
        c.error.as_mut().unwrap().reason = "proxy_type_mismatch".into();
        let run = typed_failure_run(c);
        assert_eq!(run.submission, "invoked");
        assert_eq!(run.failure().unwrap().0, "xpc_error");
    }

    fn python(program: String) -> Vec<OsString> {
        vec![
            "/usr/bin/python3".into(),
            "-B".into(),
            "-c".into(),
            program.into(),
        ]
    }
    #[test]
    fn binary_reply_after_large_stdin_and_broken_pipe_preserves_delivery_precedence() {
        let reply = host();
        let wire = capture(Some(&reply), protocol(), 123, reply.len() as i64);
        let hex: String = wire.iter().map(|b| format!("{b:02x}")).collect();
        let request = vec![b'x'; 1 << 20];
        let program = format!(
            "import sys; data=sys.stdin.buffer.read(); assert len(data)=={}; sys.stdout.buffer.write(bytes.fromhex('{hex}'))",
            request.len()
        );
        let (run, reply) = run_client_stdin(&python(program), request.clone()).unwrap();
        assert_eq!(run.request_delivery.unwrap().bytes_written, request.len());
        assert!(reply.is_some());
        assert_eq!(run.transport_admission, "accepted");
        let program = format!(
            "import sys; sys.stdout.buffer.write(bytes.fromhex('{hex}')); sys.stdout.flush(); sys.exit(1)"
        );
        let (run, reply) = run_client_stdin(&python(program), request).unwrap();
        assert!(run.request_delivery.as_ref().unwrap().error.is_some());
        assert_eq!(run.transport_admission, "delivery_failed");
        assert_eq!(run.submission, "unknown");
        assert!(reply.is_none());
        let Some(TransportCapture::Rejected { data_base64, .. }) = run.transport else {
            panic!("lost bytes")
        };
        assert_eq!(data_base64, wire);
    }
    #[test]
    fn process_span_and_opaque_nonprotocol_diagnostics_survive_collection() {
        let program = "import time,struct,sys; a=int(time.time()*1000); time.sleep(0.3); b=int(time.time()*1000); sys.stdout.buffer.write(struct.pack('<QQ',a,b)); sys.stderr.buffer.write(b'\\x00\\xffnative detail')";
        let (run, reply) = run_client_stdin(&python(program.into()), vec![]).unwrap();
        assert!(reply.is_none());
        let Some(TransportCapture::Rejected { data_base64, .. }) = run.transport else {
            panic!("lost bytes")
        };
        let a = u64::from_le_bytes(data_base64[..8].try_into().unwrap());
        let b = u64::from_le_bytes(data_base64[8..].try_into().unwrap());
        assert!(run.started_at_unix_ms <= a && b <= run.ended_at_unix_ms);
        assert!(run.ended_at_unix_ms - run.started_at_unix_ms >= 300);
        assert_eq!(run.output.stderr_bytes_received, Some(15));
        assert!(run.output.stderr.contains("native detail"));
    }
    #[test]
    fn retention_loss_precedes_decode_and_keeps_exact_prefix() {
        let bytes = vec![0xfe; crate::utils::RUNNER_CAPTURE_BYTES + 1];
        let (run, reply) = parse(bytes, None);
        assert!(reply.is_none());
        assert!(run.output.stdout_capture_error.is_some());
        assert!(run.output.stdout_parse_error.is_none());
        assert_eq!(run.submission, "unknown");
        let Some(TransportCapture::Rejected { data_base64, .. }) = run.transport else {
            panic!("lost prefix")
        };
        assert_eq!(data_base64.len(), crate::utils::RUNNER_CAPTURE_BYTES);
        assert!(data_base64.iter().all(|b| *b == 0xfe));
    }
}
