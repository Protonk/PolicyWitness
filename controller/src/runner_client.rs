//! One reservation-aware helper invocation and its versioned capture.
//!
//! Client observations are admitted before decoding any host reply. Neither a
//! transport failure nor missing helper output authorizes another invocation.
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::ffi::OsString;
use std::process::Command;

use crate::app_layout::resolve_contents_macos_tool;
use crate::runner_select::RunnerConnectionKind;
#[cfg(test)]
use crate::utils::RUNNER_CAPTURE_BYTES;
use crate::utils::{
    JsonOutputCapture, RequestDelivery, capture_json_output, now_unix_ms, run_with_stdin,
};

const REPLY_CAPTURE_BYTES: usize = 64 * 1024 * 1024;
const CONTROL_BYTES: u64 = 64 * 1024;
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
    pub output: JsonOutputCapture,
    /// Parsed client frame, including opaque rejected versions/structures.
    pub transport: Option<Value>,
    pub transport_admission: String,
    pub transport_error: Option<String>,
    /// Unknown unless a complete current capture was admitted.
    pub submission: String,
    /// Host bytes were received but cannot be read as a complete JSON reply.
    pub runner_reply_error: Option<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Capture {
    kind: String,
    protocol_version: u32,
    client_pid: i32,
    clock: String,
    clock_available: bool,
    started_continuous_ns: Option<u64>,
    deadline_continuous_ns: Option<u64>,
    ended_continuous_ns: Option<u64>,
    timeout_ms: u64,
    attempts: Vec<Attempt>,
    acquisition_stop: String,
    submission: Submission,
    terminal: String,
    error: Option<TransportError>,
    runner_reply: Option<ReplyCapture>,
    submission_refusal: Option<Control>,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Attempt {
    ordinal: usize,
    attempt_id: String,
    started_elapsed_ms: Option<u64>,
    ended_elapsed_ms: Option<u64>,
    outcome: String,
    control: Option<Control>,
    error: Option<TransportError>,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Submission {
    state: String,
    invoked_elapsed_ms: Option<u64>,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Control {
    bytes_received: u64,
    sha256: String,
    status: Option<String>,
    host_pid: Option<i32>,
    host_instance: Option<String>,
    lease_ms: Option<u64>,
    reason: Option<String>,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct TransportError {
    stage: String,
    reason: String,
    domain: Option<String>,
    code: Option<i64>,
    message: String,
    domain_truncated: bool,
    message_truncated: bool,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ReplyCapture {
    bytes_received: u64,
    bytes_retained: usize,
    truncated: bool,
    data_base64: String,
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
    require(
        value.bytes_received <= i64::MAX as u64,
        "invalid control byte count",
    )?;
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
        value.host_pid.is_some_and(|pid| pid > 0)
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
fn decode_base64(text: &str) -> Result<Vec<u8>, String> {
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

fn validate_capture(value: &Capture) -> Result<Option<Vec<u8>>, String> {
    require(
        value.kind == "runner_client_capture"
            && value.protocol_version == crate::json_contract::RUNNER_PROTOCOL_VERSION,
        "invalid client capture identity",
    )?;
    require(
        value.client_pid > 0 && value.clock == "mach_continuous_time_ns" && value.timeout_ms > 0,
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
            attempt.ordinal == index + 1
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
            reply.bytes_received <= i64::MAX as u64
                && reply.bytes_retained as u64
                    == reply.bytes_received.min(REPLY_CAPTURE_BYTES as u64)
                && reply.truncated == ((reply.bytes_retained as u64) < reply.bytes_received),
            "inconsistent reply byte retention",
        )?;
        let decoded = decode_base64(&reply.data_base64)?;
        require(
            decoded.len() == reply.bytes_retained,
            "reply base64 length disagrees with retained count",
        )?;
        Ok(Some(decoded))
    } else {
        Ok(None)
    }
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
            let truncated = self
                .transport
                .as_ref()
                .is_some_and(|v| v["runner_reply"]["truncated"] == true);
            return Some((
                if truncated {
                    "runner_reply_truncated"
                } else {
                    "malformed_runner_response"
                },
                error.clone(),
            ));
        }
        let value = self.transport.as_ref().unwrap();
        let terminal = value["terminal"].as_str().unwrap();
        let outcome = match terminal {
            "runner_reply" => return None,
            "xpc_error" => "xpc_error",
            "xpc_timeout" => "xpc_timeout",
            "acquisition_failed" => "xpc_acquisition_failed",
            "submission_refused" => "xpc_submission_refused",
            "protocol_error" => "xpc_protocol_error",
            _ => "runner_client_error",
        };
        let message = value["error"]["message"]
            .as_str()
            .or_else(|| value["submission_refusal"]["reason"].as_str())
            .unwrap_or(terminal);
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
                .is_some_and(|v| v["terminal"] == "xpc_error")
    }
}

fn parse_runner_client_output(
    argv: &[OsString],
    started: u64,
    ended: u64,
    out: &std::process::Output,
    request_delivery: Option<RequestDelivery>,
) -> (RunnerClientRun, Option<Value>) {
    let (output, transport) =
        capture_json_output(out, "runner client", crate::utils::RUNNER_CAPTURE_BYTES);
    let mut run = RunnerClientRun {
        argv: argv
            .iter()
            .map(|s| s.to_string_lossy().to_string())
            .collect(),
        started_at_unix_ms: started,
        ended_at_unix_ms: ended,
        exit_code: out.status.code().unwrap_or(1),
        request_delivery,
        output,
        transport,
        transport_admission: "missing".into(),
        transport_error: None,
        submission: "unknown".into(),
        runner_reply_error: None,
    };
    let mut reply = None;
    let admission = (|| -> Result<(), (&str, String)> {
        if let Some(error) = run.request_delivery.as_ref().and_then(|d| d.error.as_ref()) {
            return Err(("delivery_failed", error.clone()));
        }
        if let Some(error) = run
            .output
            .stdout_capture_error
            .as_ref()
            .or(run.output.stdout_parse_error.as_ref())
        {
            return Err(("malformed", error.clone()));
        }
        let value = run
            .transport
            .as_ref()
            .ok_or(("missing", "runner client produced no capture".into()))?;
        let protocol = match value.get("protocol_version") {
            Some(Value::Number(number)) if number.is_u64() || number.is_i64() => number,
            _ => {
                return Err((
                    "malformed",
                    "client capture lacks an integer protocol_version".into(),
                ));
            }
        };
        if protocol.as_u64() != Some(u64::from(crate::json_contract::RUNNER_PROTOCOL_VERSION)) {
            return Err((
                "unsupported",
                format!("client capture protocol {protocol} is unsupported"),
            ));
        }
        let capture: Capture = serde_json::from_value(value.clone())
            .map_err(|e| ("malformed", format!("malformed client capture: {e}")))?;
        let bytes = validate_capture(&capture).map_err(|e| ("malformed", e))?;
        run.submission = capture.submission.state;
        if let Some(bytes) = bytes {
            if capture.runner_reply.as_ref().unwrap().truncated {
                run.runner_reply_error = Some(
                    "runner reply retention was truncated; no complete host reply is available"
                        .into(),
                );
            } else {
                match serde_json::from_slice(&bytes) {
                    Ok(value) => reply = Some(value),
                    Err(error) => {
                        run.runner_reply_error =
                            Some(format!("runner reply is not complete JSON: {error}"))
                    }
                }
            }
        }
        Ok(())
    })();
    match admission {
        Ok(()) => run.transport_admission = "accepted".into(),
        Err((status, error)) => {
            run.transport_admission = status.into();
            run.transport_error = Some(error);
        }
    }
    (run, reply)
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
) -> Result<(RunnerClientRun, Option<Value>), String> {
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
) -> Result<(RunnerClientRun, Option<Value>), String> {
    run_client_stdin_with_clock(argv, request, now_unix_ms)
}
fn run_client_stdin_with_clock(
    argv: &[OsString],
    request: Vec<u8>,
    mut clock: impl FnMut() -> u64,
) -> Result<(RunnerClientRun, Option<Value>), String> {
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
    let bytes = reply.map(|r| serde_json::to_vec(r).unwrap());
    let frame = test_capture_bytes(bytes.as_deref());
    let output = std::process::Output {
        status: std::os::unix::process::ExitStatusExt::from_raw(if reply.is_some() {
            0
        } else {
            256
        }),
        stdout: serde_json::to_vec(&frame).unwrap(),
        stderr: b"fixed runner-client diagnostic".to_vec(),
    };
    parse_runner_client_output(
        &["controlled-client".into()],
        1000,
        2500,
        &output,
        Some(RequestDelivery {
            bytes_written: 2,
            error: None,
        }),
    )
    .0
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::process::Stdio;

    #[test]
    fn path_wire_fixtures_survive_capture_serialization_and_independent_consumer() {
        use std::io::Write;
        let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("..");
        let fixture = root.join("tests/fixtures/contract/path_diagnostics.json");
        let original: Value = serde_json::from_slice(&std::fs::read(&fixture).unwrap()).unwrap();
        let output = Command::new("/usr/bin/python3")
            .args([
                "-B",
                "-c",
                "import sys; sys.stdout.buffer.write(open(sys.argv[1], 'rb').read())",
            ])
            .arg(&fixture)
            .output()
            .unwrap();
        assert!(output.status.success());
        let output = std::process::Output {
            stdout: serde_json::to_vec(&test_capture_bytes(Some(&output.stdout))).unwrap(),
            ..output
        };
        let (capture, parsed) = parse_runner_client_output(&[], 0, 1, &output, None);
        assert!(capture.output.stdout_capture_error.is_none());
        assert_eq!(parsed.as_ref(), Some(&original));
        // Forward valid and malformed representations unchanged. The independent
        // consumer owns interpretation; the controller must not normalize them.
        let mut consumer = Command::new("/usr/bin/python3")
            .arg("-B")
            .arg(root.join("tests/lib/path_diagnostics_contract.py"))
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .unwrap();
        consumer
            .stdin
            .take()
            .unwrap()
            .write_all(&serde_json::to_vec(&parsed.unwrap()).unwrap())
            .unwrap();
        let answer = consumer.wait_with_output().unwrap();
        assert!(
            answer.status.success(),
            "{}",
            String::from_utf8_lossy(&answer.stderr)
        );
    }

    // Real subprocess producers exercise full capture before prefix selection.
    fn producer(program: &str) -> (RunnerClientRun, Option<Value>, Vec<u8>) {
        let argv = vec![
            OsString::from("/usr/bin/python3"),
            OsString::from("-c"),
            OsString::from(program),
        ];
        let output = Command::new(&argv[0]).args(&argv[1..]).output().unwrap();
        assert!(output.status.success());
        let (capture, parsed) = parse_runner_client_output(&argv, 0, 1, &output, None);
        (capture, parsed, output.stdout)
    }

    #[test]
    fn transport_preserves_current_replies_with_unfamiliar_values_and_other_versions() {
        use serde_json::json;
        let current = i64::from(crate::json_contract::RESPONSE_SCHEMA_VERSION);
        // A current-version reply whose strings the controller does not
        // recognize is received unchanged: the version gate and the readers
        // decide later, never the transport.
        let mut replies = vec![
            json!({"schema_version": current, "normalized_outcome": "ok", "steps": [{
            "step_id": "spawn",
            "sandbox_check": {"outcome": "allow", "rc": 0, "native_rc": 0, "path_diagnostics": {
                "input": "/submitted", "observer": "runner_host", "stage": "after_orchestration"}},
            "attempt": {"outcome": "exec_failed", "rc": 37, "child_pid": 123, "child_exit_code": 37,
                "stdout": "controlled marker", "requested_kind": "exec", "requested_action": "spawn"},
            "comparison": {"observation": "succeeded", "observation_basis": "spawned_child",
                "operation_relation": "matched", "target_relation": "same_submitted",
                "order": "future_order", "limitations": ["future_evidence_limit"]}}],
            "runner_subprocess": {"ordering": {
                "collection_closed_before_proceed": true, "proceed_set": true,
                "proceed_observed": true, "validator_disposition": "unconfirmed",
                "worker_lifetime_established": true, "protocol_violations": ["future_fault"]}},
            "validator_spawn_failure": {
                "origin": "runner_host", "operation": "posix_spawn",
                "executable_path": "/unknown/validator-\"\u{e9}\"", "return_code": 2147483647,
                "diagnostic": "unfamiliar native launch diagnostic"}}),
        ];
        // Other and malformed versions are transported as received; nothing
        // here coerces or rejects them.
        for version in [current - 1, current + 1] {
            replies.push(
                json!({"schema_version": version, "steps": [{"step_id": "s", "drift": false}]}),
            );
        }
        replies.push(json!({"schema_version": current.to_string(), "steps": []}));
        replies.push(json!({"steps": []}));
        for original in replies {
            let output = crate::utils::receiver_fixture(
                &test_capture_bytes(Some(original.to_string().as_bytes())).to_string(),
                "valid",
                crate::utils::RUNNER_CAPTURE_BYTES,
            );
            let (capture, received) = parse_runner_client_output(&[], 0, 1, &output, None);
            assert!(capture.output.stdout_capture_error.is_none());
            assert_eq!(received, Some(original));
        }
    }

    fn python(program: &str) -> Vec<OsString> {
        vec![
            OsString::from("/usr/bin/python3"),
            OsString::from("-c"),
            OsString::from(program),
        ]
    }

    #[test]
    fn delivery_completes_a_request_larger_than_the_pipe_buffer() {
        // The child reads only after a delay, so the writer must block on a
        // full pipe and still deliver every byte before closing stdin.
        let request = vec![b'x'; 1 << 20];
        let argv = python(
            "import sys, time, json; time.sleep(0.2); data = sys.stdin.buffer.read(); \
             print(json.dumps({'bytes': len(data), 'uniform': data == b'x' * len(data)}))",
        );
        let (run, reply) =
            run_client_stdin_with_clock(&argv, request.clone(), now_unix_ms).unwrap();
        assert_eq!(
            run.request_delivery,
            Some(RequestDelivery {
                bytes_written: request.len(),
                error: None
            })
        );
        assert_eq!(
            run.transport,
            Some(serde_json::json!({"bytes": request.len(), "uniform": true}))
        );
        assert!(
            reply.is_none(),
            "the producer is not a current client capture"
        );
        assert_eq!(run.exit_code, 0);
        let wire = serde_json::to_value(&run).unwrap();
        assert_eq!(wire["request_delivery"]["bytes_written"], request.len());
        assert!(wire["request_delivery"]["error"].is_null());
    }

    #[test]
    fn a_child_that_exits_without_reading_breaks_the_pipe_without_terminating_the_controller() {
        let request = vec![b'x'; 1 << 20];
        let argv = python("import sys; sys.exit(3)");
        let (run, reply) =
            run_client_stdin_with_clock(&argv, request.clone(), now_unix_ms).unwrap();
        let delivery = run.request_delivery.clone().unwrap();
        let error = delivery.error.expect("the broken pipe is recorded");
        assert!(
            error.contains("request delivery failed after") && error.contains("Broken pipe"),
            "{error}"
        );
        assert!(delivery.bytes_written < request.len());
        assert!(reply.is_none());
        assert_eq!(run.exit_code, 3);
        assert!(run.output.stdout_parse_error.is_some() || run.output.stdout_raw.is_none());
    }

    #[test]
    fn a_delivery_error_is_recorded_beside_a_captured_failure_reply() {
        let request = vec![b'x'; 1 << 20];
        let argv = python(
            "import sys, json; print(json.dumps({'schema_version': 0, 'normalized_outcome': \
             'xpc_error', 'error': 'controlled failure reply'})); sys.exit(1)",
        );
        let (run, reply) = run_client_stdin_with_clock(&argv, request, now_unix_ms).unwrap();
        let delivery = run.request_delivery.clone().unwrap();
        assert!(
            delivery
                .error
                .as_deref()
                .unwrap_or("")
                .contains("Broken pipe")
        );
        assert!(
            reply.is_none(),
            "failed local delivery must not admit a host reply"
        );
        let rejected = run
            .transport
            .as_ref()
            .expect("opaque producer JSON remains available");
        assert_eq!(rejected["normalized_outcome"], "xpc_error");
        assert_eq!(rejected["error"], "controlled failure reply");
        assert_eq!(run.submission, "unknown");
        assert_eq!(run.exit_code, 1);
    }

    #[test]
    fn unfamiliar_diagnostics_survive_runner_capture() {
        let records = crate::utils::transport_diagnostics();
        let original = serde_json::json!({"data": {"diagnostics": records},
            "result": {"ok": false, "normalized_outcome": "runner_failed", "rc": 1}});
        for mode in ["valid", "oversized"] {
            let output = crate::utils::receiver_fixture(
                &test_capture_bytes(Some(original.to_string().as_bytes())).to_string(),
                mode,
                crate::utils::RUNNER_CAPTURE_BYTES,
            );
            let (capture, received) = parse_runner_client_output(&[], 0, 1, &output, None);
            if mode == "valid" {
                assert_eq!(received, Some(original.clone()));
                assert!(capture.output.stdout_capture_error.is_none());
            } else {
                assert!(serde_json::from_slice::<Value>(&output.stdout).is_ok());
                assert!(received.is_none());
                assert!(capture.output.stdout_capture_error.is_some());
                assert!(capture.output.stdout_parse_error.is_none());
            }
        }
    }

    #[test]
    fn recorded_span_brackets_the_child_process() {
        // The child reports its own clock twice, around a sleep; both readings
        // must fall inside the span the controller records for it.
        let argv = vec![
            OsString::from("/usr/bin/python3"),
            OsString::from("-c"),
            OsString::from(
                "import json, time; a = int(time.time() * 1000); time.sleep(0.3); \
                 b = int(time.time() * 1000); print(json.dumps({'a': a, 'b': b}))",
            ),
        ];
        let (run, parsed) = run_client_stdin(&argv, Vec::new()).unwrap();
        assert!(parsed.is_none());
        let reply = run
            .transport
            .as_ref()
            .expect("opaque child JSON is retained");
        let (a, b) = (reply["a"].as_u64().unwrap(), reply["b"].as_u64().unwrap());
        assert!(
            run.started_at_unix_ms <= a,
            "{} <= {a}",
            run.started_at_unix_ms
        );
        assert!(b <= run.ended_at_unix_ms, "{b} <= {}", run.ended_at_unix_ms);
        assert!(run.ended_at_unix_ms - run.started_at_unix_ms >= 300);
        assert_eq!(run.exit_code, 0);
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

    #[test]
    fn valid_oversized_producer_is_receiver_loss_not_malformed_json() {
        let (capture, parsed, full) = producer(&format!(
            "import sys; sys.stdout.write('{{\"value\":\"' + 'x'*{} + '\"}}')",
            RUNNER_CAPTURE_BYTES
        ));
        assert!(
            serde_json::from_slice::<Value>(&full).is_ok(),
            "producer emitted valid complete JSON"
        );
        assert!(parsed.is_none());
        let wire = serde_json::to_value(&capture).unwrap();
        assert_eq!(wire["stdout_bytes_received"], RUNNER_CAPTURE_BYTES + 12);
        assert_eq!(wire["stdout_bytes_retained"], RUNNER_CAPTURE_BYTES);
        assert!(
            wire["stdout_capture_error"]
                .as_str()
                .unwrap()
                .contains("controller truncated")
        );
        assert_eq!(
            capture.output.stdout_bytes_received,
            Some(RUNNER_CAPTURE_BYTES + 12)
        );
        assert_eq!(
            capture.output.stdout_bytes_retained,
            Some(RUNNER_CAPTURE_BYTES)
        );
        assert_eq!(capture.output.capture_limit_bytes, RUNNER_CAPTURE_BYTES);
        assert!(capture.output.stdout_truncated);
        assert!(capture.output.stdout_parse_error.is_none());
        assert!(
            capture
                .output
                .stdout_capture_error
                .unwrap()
                .contains("controller truncated")
        );
    }

    #[test]
    fn malformed_within_cap_is_a_parse_error() {
        let (capture, parsed, full) = producer("import sys; sys.stdout.write('invalid-json')");
        assert!(serde_json::from_slice::<Value>(&full).is_err());
        assert!(parsed.is_none());
        assert_eq!(capture.output.stdout_bytes_received, Some(12));
        assert_eq!(capture.output.stdout_bytes_retained, Some(12));
        assert!(!capture.output.stdout_truncated);
        assert!(capture.output.stdout_capture_error.is_none());
        assert!(capture.output.stdout_parse_error.is_some());
    }

    #[test]
    fn invalid_utf8_is_not_repaired_into_accepted_json() {
        let (capture, parsed, full) =
            producer("import sys; sys.stdout.buffer.write(b'{\"v\":\"' + bytes([255]) + b'\"}')");
        assert!(serde_json::from_slice::<Value>(&full).is_err());
        assert!(parsed.is_none());
        assert!(!capture.output.stdout_truncated);
        assert!(capture.output.stdout_capture_error.is_none());
        assert!(capture.output.stdout_parse_error.is_some());
        assert_eq!(capture.output.stdout_bytes_received, Some(9));
    }

    #[test]
    fn multibyte_cut_counts_bytes_before_lossy_conversion() {
        // stdout: the cap falls inside a three-byte character; stderr exceeds the
        // cap with whole three-byte characters, regardless of the cap modulo three.
        let (capture, parsed, full) = producer(&format!(
            "import sys; sys.stdout.buffer.write(b'{{\"v\":\"' + b'x'*({} - 7) + bytes([0xe2,0x82,0xac]) + b'\"}}'); sys.stderr.buffer.write(bytes([0xe2,0x82,0xac])*{})",
            RUNNER_CAPTURE_BYTES,
            RUNNER_CAPTURE_BYTES / 3 + 1
        ));
        assert!(serde_json::from_slice::<Value>(&full).is_ok());
        assert!(parsed.is_none());
        assert_eq!(
            capture.output.stdout_bytes_received,
            Some(RUNNER_CAPTURE_BYTES + 4)
        );
        assert_eq!(
            capture.output.stdout_bytes_retained,
            Some(RUNNER_CAPTURE_BYTES)
        );
        assert_eq!(
            capture.output.stderr_bytes_received,
            Some(3 * (RUNNER_CAPTURE_BYTES / 3 + 1))
        );
        assert_eq!(
            capture.output.stderr_bytes_retained,
            Some(RUNNER_CAPTURE_BYTES)
        );
        let text = capture.output.stdout_raw.unwrap();
        assert!(text.ends_with('\u{fffd}'));
        assert_eq!(text.len(), RUNNER_CAPTURE_BYTES + 2);
        assert!(capture.output.stdout_capture_error.is_some());
        assert!(capture.output.stdout_parse_error.is_none());
    }

    fn captured(frame: &Value) -> (RunnerClientRun, Option<Value>) {
        let output = std::process::Output {
            status: std::os::unix::process::ExitStatusExt::from_raw(0),
            stdout: serde_json::to_vec(frame).unwrap(),
            stderr: Vec::new(),
        };
        parse_runner_client_output(
            &[],
            0,
            1,
            &output,
            Some(RequestDelivery {
                bytes_written: 2,
                error: None,
            }),
        )
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
    fn rejected_capture_never_recovers_nonexecution_or_host_claims() {
        let original = test_capture_bytes(Some(br#"{"schema_version":24,"pid":999}"#));
        let mutations: Vec<Box<dyn Fn(&mut Value)>> = vec![
            Box::new(|v| v["submission"]["state"] = "not_invoked".into()),
            Box::new(|v| v["acquisition_stop"] = "overall_deadline".into()),
            Box::new(|v| v["attempts"][0]["ordinal"] = 2.into()),
            Box::new(|v| {
                v["attempts"][0]["control"]["reservation_id"] = "credential must not escape".into()
            }),
            Box::new(|v| v["attempts"][0]["control"]["host_pid"] = 0.into()),
            Box::new(|v| v["attempts"][0]["control"]["lease_ms"] = 5001.into()),
            Box::new(|v| v["runner_reply"]["bytes_retained"] = 0.into()),
            Box::new(|v| v["runner_reply"]["data_base64"] = "Zh==".into()),
            Box::new(|v| v["clock_available"] = false.into()),
            Box::new(|v| {
                v.as_object_mut()
                    .unwrap()
                    .remove("submission")
                    .map(|_| ())
                    .unwrap()
            }),
        ];
        for mutate in mutations {
            let mut frame = original.clone();
            mutate(&mut frame);
            let (capture, host) = captured(&frame);
            assert_eq!(capture.transport_admission, "malformed", "{frame}");
            assert_eq!(capture.submission, "unknown");
            assert_eq!(capture.transport, Some(frame));
            assert!(host.is_none() && capture.runner_reply_error.is_none());
        }
        for version in [
            serde_json::json!(-1),
            serde_json::json!(1),
            serde_json::json!(u64::MAX),
        ] {
            let mut frame = original.clone();
            frame["protocol_version"] = version;
            frame["submission"] = serde_json::json!({"invented":"must not be inspected"});
            let (capture, host) = captured(&frame);
            assert_eq!(capture.transport_admission, "unsupported");
            assert_eq!(capture.submission, "unknown");
            assert!(host.is_none());
        }
    }

    #[test]
    fn grant_followed_by_deadline_does_not_invent_an_invocation() {
        let mut frame = test_capture_bytes(None);
        frame["submission"] = serde_json::json!({"state":"not_invoked"});
        frame["terminal"] = "xpc_timeout".into();
        frame["deadline_continuous_ns"] = 1004000000u64.into();
        frame["error"] = serde_json::json!({"stage":"acquisition","reason":"overall_deadline",
            "message":"deadline expired after grant","domain_truncated":false,"message_truncated":false});
        let (capture, host) = captured(&frame);
        assert_eq!(
            capture.transport_admission, "accepted",
            "{:?}",
            capture.transport_error
        );
        assert_eq!(capture.submission, "not_invoked");
        assert_eq!(capture.failure().unwrap().0, "xpc_timeout");
        assert_eq!(
            capture.transport.as_ref().unwrap()["acquisition_stop"],
            "granted"
        );
        assert!(host.is_none() && !capture.fallback_eligible());
    }

    #[test]
    fn clock_failure_preserves_known_submission_without_inventing_a_terminal_clock() {
        for invoked in [false, true] {
            let mut frame = test_capture_bytes(None);
            frame["clock_available"] = false.into();
            frame["terminal"] = "local_error".into();
            frame.as_object_mut().unwrap().remove("ended_continuous_ns");
            frame["error"] = serde_json::json!({"stage":"local","reason":"clock_error",
                "message":"clock unavailable","domain_truncated":false,"message_truncated":false});
            if !invoked {
                frame["submission"] = serde_json::json!({"state":"not_invoked"});
                frame["attempts"] = serde_json::json!([]);
                frame["acquisition_stop"] = "local_error".into();
                frame
                    .as_object_mut()
                    .unwrap()
                    .remove("started_continuous_ns");
                frame
                    .as_object_mut()
                    .unwrap()
                    .remove("deadline_continuous_ns");
            }
            let (capture, host) = captured(&frame);
            assert_eq!(
                capture.transport_admission, "accepted",
                "{:?}",
                capture.transport_error
            );
            assert_eq!(
                capture.submission,
                if invoked { "invoked" } else { "not_invoked" }
            );
            assert!(host.is_none());
        }
    }

    #[test]
    fn host_bytes_are_not_replaced_with_client_error_shapes() {
        for bytes in [b"".as_slice(), b"not-json", &[255]] {
            let (capture, host) = captured(&test_capture_bytes(Some(bytes)));
            assert_eq!(capture.transport_admission, "accepted");
            assert_eq!(capture.submission, "invoked");
            assert!(host.is_none() && capture.runner_reply_error.is_some());
            assert_eq!(capture.failure().unwrap().0, "malformed_runner_response");
        }
        let (capture, host) = captured(&test_capture_bytes(None));
        assert_eq!(capture.transport_admission, "accepted");
        assert_eq!(capture.failure().unwrap().0, "xpc_error");
        assert!(capture.fallback_eligible() && host.is_none());
    }

    #[test]
    fn local_delivery_failure_precedes_even_a_complete_current_capture() {
        let frame = test_capture_bytes(Some(br#"{"schema_version":24,"pid":999}"#));
        let output = std::process::Output {
            status: std::os::unix::process::ExitStatusExt::from_raw(0),
            stdout: serde_json::to_vec(&frame).unwrap(),
            stderr: Vec::new(),
        };
        let (capture, host) = parse_runner_client_output(
            &[],
            0,
            1,
            &output,
            Some(RequestDelivery {
                bytes_written: 1,
                error: Some("controlled delivery failure".into()),
            }),
        );
        assert_eq!(capture.transport_admission, "delivery_failed");
        assert_eq!(capture.transport, Some(frame));
        assert_eq!(capture.submission, "unknown");
        assert!(host.is_none() && capture.runner_reply_error.is_none());
        assert!(!capture.fallback_eligible());
    }

    #[test]
    fn submission_proxy_failure_keeps_the_irreversible_invocation_observation() {
        let mut frame = test_capture_bytes(None);
        frame["error"] = serde_json::json!({"stage":"submission","reason":"proxy_type_mismatch",
            "message":"remote proxy type mismatch","domain_truncated":false,"message_truncated":false});
        let (capture, host) = captured(&frame);
        assert_eq!(
            capture.transport_admission, "accepted",
            "{:?}",
            capture.transport_error
        );
        assert_eq!(capture.submission, "invoked");
        assert_eq!(capture.failure().unwrap().0, "xpc_error");
        assert!(host.is_none());
        // The same local failure cannot claim a transport retry during acquisition.
        frame["attempts"][0]["ordinal"] = 2.into();
        frame["attempts"][0]["started_elapsed_ms"] = 1.into();
        frame["attempts"][0]["ended_elapsed_ms"] = 2.into();
        frame["attempts"].as_array_mut().unwrap().insert(0, serde_json::json!({
            "ordinal":1,"attempt_id":"33333333-3333-4333-8333-333333333333",
            "started_elapsed_ms":0,"ended_elapsed_ms":1,"outcome":"transport_error",
            "error":{"stage":"acquisition","reason":"proxy_type_mismatch",
                "message":"remote proxy type mismatch","domain_truncated":false,"message_truncated":false}}));
        let (capture, _) = captured(&frame);
        assert_eq!(capture.transport_admission, "malformed");
        assert_eq!(capture.submission, "unknown");
    }

    #[test]
    fn submission_refusal_is_separate_from_host_results_and_never_replayed() {
        for reason in ["wrong", "expired", "absent", "consumed", "clock_error"] {
            let mut frame = test_capture_bytes(None);
            frame.as_object_mut().unwrap().remove("error");
            frame["terminal"] = "submission_refused".into();
            frame["submission_refusal"] = serde_json::json!({"bytes_received":100,"sha256":"b".repeat(64),
                "status":"reservation_refused","host_pid":42,"host_instance":"22222222-2222-4222-8222-222222222222","reason":reason});
            let (capture, host) = captured(&frame);
            assert_eq!(
                capture.transport_admission, "accepted",
                "{:?}",
                capture.transport_error
            );
            assert_eq!(capture.submission, "invoked");
            assert_eq!(capture.failure().unwrap().0, "xpc_submission_refused");
            assert!(host.is_none() && !capture.fallback_eligible());
        }
        // Invalid Bool=false control bytes retain their count/hash only.
        let mut frame = test_capture_bytes(None);
        frame["terminal"] = "protocol_error".into();
        frame["error"] = serde_json::json!({"stage":"submission","reason":"invalid_control",
            "message":"invalid control","domain_truncated":false,"message_truncated":false});
        frame["submission_refusal"] =
            serde_json::json!({"bytes_received":5,"sha256":"b".repeat(64)});
        let (capture, host) = captured(&frame);
        assert_eq!(
            capture.transport_admission, "accepted",
            "{:?}",
            capture.transport_error
        );
        assert_eq!(capture.submission, "invoked");
        assert!(host.is_none() && !capture.fallback_eligible());
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
}
