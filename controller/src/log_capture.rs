//! Bounded subprocess supervision used only by the optional log channel.
//!
//! A controller-spawned observer leads an owned process group. The observer's
//! log child inherits that group; its direct supervisor must never signal it.

use serde::{Deserialize, Serialize};
use std::io::{self, Read};
use std::os::fd::AsRawFd;
use std::os::unix::process::{CommandExt, ExitStatusExt};
use std::process::{Child, Command, Stdio};
use std::time::{Duration, Instant};

pub const DEFAULT_LOG_TIMEOUT_MS: u64 = 10_000;
pub const CLEANUP_GRACE_MS: u64 = 1_000;
pub const LOG_STDOUT_BYTES: usize = 1024 * 1024;
pub const LOG_STDERR_BYTES: usize = 128 * 1024;
// Raw text is repeated as log_stdout, deny_lines and event.raw_line, with
// parsed fields beside it. Allow JSON's six-byte escaping and event metadata.
pub const OBSERVER_STDOUT_BYTES: usize = 32 * 1024 * 1024;
pub const OBSERVER_STDERR_BYTES: usize = 128 * 1024;
pub const MAX_DENY_EVENTS: usize = 8192;
pub const MAX_ASSOCIATION_BYTES: usize = 8 * 1024 * 1024;
pub const MAX_ASSOCIATIONS: usize = 4096;
pub const MAX_CORRELATION_STEPS: usize = 256;
pub const MAX_OBSERVER_JSON_TOKENS: usize = 262_144;
pub const MAX_OBSERVER_METADATA_BYTES: usize = 4096;

#[derive(Clone, Copy, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum TimeoutSource {
    Default,
    Cli,
}

#[derive(Clone, Copy, Debug)]
pub struct LogTimeout {
    pub milliseconds: u64,
    pub source: TimeoutSource,
}

impl Default for LogTimeout {
    fn default() -> Self {
        Self {
            milliseconds: DEFAULT_LOG_TIMEOUT_MS,
            source: TimeoutSource::Default,
        }
    }
}

impl LogTimeout {
    pub fn parse(value: &str) -> Result<Self, String> {
        if value.is_empty() || !value.bytes().all(|b| b.is_ascii_digit()) {
            return Err(
                "invalid value for --log-timeout-ms: expected positive integer milliseconds".into(),
            );
        }
        let milliseconds = value
            .parse::<u64>()
            .map_err(|_| "invalid value for --log-timeout-ms: overflow".to_string())?;
        let setting = Self {
            milliseconds,
            source: TimeoutSource::Cli,
        };
        setting.start()?; // Validate even when capture is disabled, before runner invocation.
        Ok(setting)
    }

    pub fn start(self) -> Result<CollectionBudget, String> {
        CollectionBudget::at(monotonic_ns()?, self)
    }
}

// CLOCK_MONOTONIC's boot-relative nanoseconds are shared across processes.
// Instant has no portable wire representation and wall time cannot be a timer.
pub fn monotonic_ns() -> Result<u64, String> {
    let mut ts = libc::timespec {
        tv_sec: 0,
        tv_nsec: 0,
    };
    if unsafe { libc::clock_gettime(libc::CLOCK_MONOTONIC, &mut ts) } != 0 {
        return Err(format!("CLOCK_MONOTONIC: {}", io::Error::last_os_error()));
    }
    u64::try_from(ts.tv_sec)
        .ok()
        .and_then(|s| s.checked_mul(1_000_000_000))
        .and_then(|s| {
            u64::try_from(ts.tv_nsec)
                .ok()
                .and_then(|n| s.checked_add(n))
        })
        .ok_or_else(|| "CLOCK_MONOTONIC cannot be represented as u64 nanoseconds".into())
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CollectionBudget {
    pub timeout_ms: u64,
    pub timeout_source: TimeoutSource,
    pub started_monotonic_ns: u64,
    pub deadline_monotonic_ns: u64,
}

impl CollectionBudget {
    fn at(start: u64, setting: LogTimeout) -> Result<Self, String> {
        let delta = setting
            .milliseconds
            .checked_mul(1_000_000)
            .filter(|n| *n != 0)
            .ok_or_else(|| {
                "invalid value for --log-timeout-ms: zero or nanosecond overflow".to_string()
            })?;
        let deadline = start
            .checked_add(delta)
            .filter(|d| d.checked_add(CLEANUP_GRACE_MS * 1_000_000).is_some())
            .ok_or_else(|| {
                "invalid value for --log-timeout-ms: monotonic deadline overflow".to_string()
            })?;
        if Instant::now()
            .checked_add(Duration::from_nanos(delta))
            .is_none()
        {
            return Err("invalid value for --log-timeout-ms: monotonic deadline overflow".into());
        }
        Ok(Self {
            timeout_ms: setting.milliseconds,
            timeout_source: setting.source,
            started_monotonic_ns: start,
            deadline_monotonic_ns: deadline,
        })
    }

    #[allow(dead_code)] // Used by the observer binary and shared-budget controls.
    pub fn from_argument(value: &str) -> Result<Self, String> {
        let budget: Self =
            serde_json::from_str(value).map_err(|e| format!("invalid collection budget: {e}"))?;
        let expected = Self::at(
            budget.started_monotonic_ns,
            LogTimeout {
                milliseconds: budget.timeout_ms,
                source: budget.timeout_source,
            },
        )?;
        if expected.deadline_monotonic_ns != budget.deadline_monotonic_ns
            || budget.started_monotonic_ns > monotonic_ns()?
        {
            return Err("invalid collection budget: inconsistent monotonic bounds".into());
        }
        Ok(budget)
    }

    pub fn argument(self) -> String {
        serde_json::to_string(&self).expect("fixed numeric collection budget")
    }

    pub fn expired(self) -> bool {
        monotonic_ns().map_or(true, |now| now >= self.deadline_monotonic_ns)
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Boundary {
    Observer,
    LogShow,
}

impl Boundary {
    fn limits(self) -> (usize, usize) {
        match self {
            Self::Observer => (OBSERVER_STDOUT_BYTES, OBSERVER_STDERR_BYTES),
            Self::LogShow => (LOG_STDOUT_BYTES, LOG_STDERR_BYTES),
        }
    }
}

#[derive(Debug, Deserialize, Serialize)]
pub struct Cutoff {
    pub reason: String,
    pub stream: Option<String>,
    pub limit: Option<u64>,
    pub observed: Option<u64>,
    pub detail: Option<String>,
}

impl Cutoff {
    pub fn reason(reason: &str, detail: Option<String>) -> Self {
        Self {
            reason: reason.into(),
            stream: None,
            limit: None,
            observed: None,
            detail,
        }
    }
    pub fn limit(reason: &str, stream: &str, limit: usize, observed: usize) -> Self {
        Self {
            reason: reason.into(),
            stream: Some(stream.into()),
            limit: Some(limit as u64),
            observed: Some(observed as u64),
            detail: None,
        }
    }
}

#[derive(Debug, Deserialize, Serialize)]
pub struct StreamObservation {
    pub limit_bytes: usize,
    pub bytes_read: usize,
    pub bytes_retained: usize,
    pub eof: bool,
    pub truncated: bool,
    pub read_error: Option<String>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct ProcessObservation {
    pub pid: Option<i32>,
    pub exit_observed: bool,
    pub reaped: bool,
    pub exit_code: Option<i32>,
    pub term_signal: Option<i32>,
    pub wait_error: Option<String>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct SyscallObservation {
    pub rc: i32,
    pub errno: Option<i32>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct CleanupObservation {
    pub scope: String,
    pub target: Option<i32>,
    pub grace_ms: u64,
    pub ownership: String,
    pub signal: Option<i32>,
    pub signal_result: Option<SyscallObservation>,
    pub signal_before_reap: bool,
    pub ownership_released: bool,
    pub group_probe: Option<SyscallObservation>,
    pub outcome: String,
    pub detail: Option<String>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct Supervision {
    pub boundary: Boundary,
    pub budget: CollectionBudget,
    pub elapsed_ms: u64,
    pub cutoff: Option<Cutoff>,
    pub stdout: StreamObservation,
    pub stderr: StreamObservation,
    pub process: ProcessObservation,
    pub cleanup: CleanupObservation,
}

impl Supervision {
    pub fn complete(&self) -> bool {
        self.cutoff.is_none()
            && self.stdout.eof
            && self.stderr.eof
            && self.stdout.bytes_read == self.stdout.bytes_retained
            && self.stdout.bytes_retained <= self.stdout.limit_bytes
            && self.stderr.bytes_read == self.stderr.bytes_retained
            && self.stderr.bytes_retained <= self.stderr.limit_bytes
            && !self.stdout.truncated
            && !self.stderr.truncated
            && self.stdout.read_error.is_none()
            && self.stderr.read_error.is_none()
            && self.process.pid.is_some_and(|pid| pid > 0)
            && self.process.exit_observed
            && self.process.reaped
            && self.process.exit_code == Some(0)
            && self.process.term_signal.is_none()
            && self.process.wait_error.is_none()
            && self.cleanup.target == self.process.pid
            && self.cleanup.ownership == "owned"
            && self.cleanup.ownership_released
            && match self.boundary {
                Boundary::Observer => {
                    self.cleanup.scope == "process_group"
                        && self.cleanup.outcome == "group_absent"
                        && self
                            .cleanup
                            .group_probe
                            .as_ref()
                            .is_some_and(|p| p.rc == -1 && p.errno == Some(libc::ESRCH))
                }
                Boundary::LogShow => {
                    self.cleanup.scope == "direct_child" && self.cleanup.outcome == "child_reaped"
                }
            }
    }
}

pub struct ProcessCapture {
    pub stdout: Vec<u8>,
    pub stderr: Vec<u8>,
    pub supervision: Supervision,
}

trait ProcessOps {
    fn read(
        &mut self,
        mut pipe: &mut dyn Read,
        bytes: &mut Vec<u8>,
        observation: &mut StreamObservation,
    ) -> io::Result<bool> {
        read_once(&mut pipe, bytes, observation)
    }
    fn observe(&mut self, pid: i32) -> io::Result<bool> {
        observe_exit(pid)
    }
    fn signal(&mut self, target: i32, value: i32) -> SyscallObservation {
        signal(target, value)
    }
    fn reap(&mut self, child: &mut Child, observation: &mut ProcessObservation) -> io::Result<()> {
        reap(child, observation)
    }
}
struct NativeOps;
impl ProcessOps for NativeOps {}

fn finish(mut capture: ProcessCapture, entry: Instant) -> ProcessCapture {
    capture.supervision.elapsed_ms = monotonic_ns()
        .ok()
        .map(|now| now.saturating_sub(capture.supervision.budget.started_monotonic_ns) / 1_000_000)
        .unwrap_or(entry.elapsed().as_millis() as u64);
    capture
}

fn stream(limit: usize) -> StreamObservation {
    StreamObservation {
        limit_bytes: limit,
        bytes_read: 0,
        bytes_retained: 0,
        eof: false,
        truncated: false,
        read_error: None,
    }
}

fn nonblocking(pipe: &impl AsRawFd) -> io::Result<()> {
    let fd = pipe.as_raw_fd();
    let flags = unsafe { libc::fcntl(fd, libc::F_GETFL) };
    if flags == -1 || unsafe { libc::fcntl(fd, libc::F_SETFL, flags | libc::O_NONBLOCK) } == -1 {
        Err(io::Error::last_os_error())
    } else {
        Ok(())
    }
}

// One bounded read per stream per turn, including one extra byte to witness
// overflow. The byte count is what crossed this pipe, never an estimated total.
fn read_once(
    pipe: &mut impl Read,
    bytes: &mut Vec<u8>,
    observation: &mut StreamObservation,
) -> io::Result<bool> {
    if observation.eof || observation.truncated || observation.read_error.is_some() {
        return Ok(false);
    }
    let mut buf = [0_u8; 8192];
    let maximum = buf
        .len()
        .min(observation.limit_bytes.saturating_sub(bytes.len()) + 1);
    match pipe.read(&mut buf[..maximum]) {
        Ok(0) => {
            observation.eof = true;
            Ok(false)
        }
        Ok(n) => {
            observation.bytes_read += n;
            let keep = n.min(observation.limit_bytes.saturating_sub(bytes.len()));
            bytes.extend_from_slice(&buf[..keep]);
            observation.bytes_retained = bytes.len();
            observation.truncated = keep != n;
            Ok(true)
        }
        Err(e)
            if matches!(
                e.kind(),
                io::ErrorKind::WouldBlock | io::ErrorKind::Interrupted
            ) =>
        {
            Ok(false)
        }
        Err(e) => {
            observation.read_error = Some(e.to_string());
            Err(e)
        }
    }
}

// No caller may reap between observe_exit and the last owned signal.
fn observe_exit(pid: i32) -> io::Result<bool> {
    let mut info: libc::siginfo_t = unsafe { std::mem::zeroed() };
    let rc = unsafe {
        libc::waitid(
            libc::P_PID,
            pid as libc::id_t,
            &mut info,
            libc::WEXITED | libc::WNOHANG | libc::WNOWAIT,
        )
    };
    if rc == -1 {
        return Err(io::Error::last_os_error());
    }
    Ok(unsafe { info.si_pid() } == pid)
}

fn signal(target: i32, value: i32) -> SyscallObservation {
    let rc = unsafe { libc::kill(target, value) };
    SyscallObservation {
        rc,
        errno: (rc == -1)
            .then(|| io::Error::last_os_error().raw_os_error())
            .flatten(),
    }
}

fn reap(child: &mut Child, observation: &mut ProcessObservation) -> io::Result<()> {
    if let Some(status) = child.try_wait()? {
        observation.exit_observed = true;
        observation.reaped = true;
        observation.exit_code = status.code();
        observation.term_signal = status.signal();
    }
    Ok(())
}

pub fn capture(
    command: &mut Command,
    budget: CollectionBudget,
    boundary: Boundary,
) -> ProcessCapture {
    capture_with_limits(command, budget, boundary, boundary.limits())
}

pub(crate) fn capture_with_limits(
    command: &mut Command,
    budget: CollectionBudget,
    boundary: Boundary,
    limits: (usize, usize),
) -> ProcessCapture {
    capture_with_ops(command, budget, boundary, limits, &mut NativeOps)
}

fn capture_with_ops(
    command: &mut Command,
    budget: CollectionBudget,
    boundary: Boundary,
    limits: (usize, usize),
    ops: &mut impl ProcessOps,
) -> ProcessCapture {
    let entry = Instant::now();
    let mut answer = ProcessCapture {
        stdout: Vec::new(),
        stderr: Vec::new(),
        supervision: Supervision {
            boundary,
            budget,
            elapsed_ms: 0,
            cutoff: None,
            stdout: stream(limits.0),
            stderr: stream(limits.1),
            process: ProcessObservation {
                pid: None,
                exit_observed: false,
                reaped: false,
                exit_code: None,
                term_signal: None,
                wait_error: None,
            },
            cleanup: CleanupObservation {
                scope: if boundary == Boundary::Observer {
                    "process_group"
                } else {
                    "direct_child"
                }
                .into(),
                target: None,
                grace_ms: CLEANUP_GRACE_MS,
                ownership: "not_started".into(),
                signal: None,
                signal_result: None,
                signal_before_reap: false,
                ownership_released: false,
                group_probe: None,
                outcome: "not_started".into(),
                detail: None,
            },
        },
    };
    let remaining = match monotonic_ns() {
        Ok(now) => budget.deadline_monotonic_ns.saturating_sub(now),
        Err(e) => {
            answer.supervision.cutoff = Some(Cutoff::reason("clock_error", Some(e)));
            return finish(answer, entry);
        }
    };
    let deadline = entry
        .checked_add(Duration::from_nanos(remaining))
        .unwrap_or(entry);
    if remaining == 0 {
        answer.supervision.cutoff = Some(Cutoff::reason("deadline", None));
        return finish(answer, entry);
    }
    command
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    if boundary == Boundary::Observer {
        command.process_group(0);
    }
    let mut child = match command.spawn() {
        Ok(child) => child,
        Err(e) => {
            answer.supervision.cutoff = Some(Cutoff::reason("launch_error", Some(e.to_string())));
            return finish(answer, entry);
        }
    };
    let pid = child.id() as i32;
    let report = &mut answer.supervision;
    report.process.pid = Some(pid);
    report.cleanup.target = Some(pid);
    report.cleanup.ownership = "owned".into();
    let mut stdout = child.stdout.take().expect("piped stdout");
    let mut stderr = child.stderr.take().expect("piped stderr");
    if let Err(e) = nonblocking(&stdout).and_then(|_| nonblocking(&stderr)) {
        report.cutoff = Some(Cutoff::reason("pipe_setup_error", Some(e.to_string())));
    }
    while report.cutoff.is_none() {
        if Instant::now() >= deadline {
            report.cutoff = Some(Cutoff::reason("deadline", None));
            break;
        }
        if !report.process.exit_observed {
            match ops.observe(pid) {
                Ok(exited) => report.process.exit_observed = exited,
                Err(e) if e.kind() == io::ErrorKind::Interrupted => continue,
                Err(e) => {
                    report.process.wait_error = Some(e.to_string());
                    report.cleanup.ownership = "lost".into();
                    report.cutoff = Some(Cutoff::reason("wait_error", Some(e.to_string())));
                    break;
                }
            }
        }
        let mut progressed = false;
        for (pipe, bytes, observation, name) in [
            (
                &mut stdout as &mut dyn Read,
                &mut answer.stdout,
                &mut report.stdout,
                "stdout",
            ),
            (
                &mut stderr as &mut dyn Read,
                &mut answer.stderr,
                &mut report.stderr,
                "stderr",
            ),
        ] {
            match ops.read(&mut *pipe, bytes, observation) {
                Ok(got) => progressed |= got,
                Err(e) => {
                    observation.read_error = Some(e.to_string());
                    report.cutoff =
                        Some(Cutoff::reason("read_error", Some(format!("{name}: {e}"))));
                }
            }
            if observation.truncated {
                report.cutoff = Some(Cutoff::limit(
                    "output_overflow",
                    name,
                    observation.limit_bytes,
                    observation.bytes_read,
                ));
            }
            if report.cutoff.is_some() {
                break;
            }
        }
        if report.process.exit_observed {
            if report.stdout.eof && report.stderr.eof {
                break;
            }
            if !progressed {
                report.cutoff = Some(Cutoff::reason("pipe_open_after_exit", None));
                break;
            }
        }
        if !progressed {
            std::thread::sleep(
                Duration::from_millis(2).min(deadline.saturating_duration_since(Instant::now())),
            );
        }
    }

    // Cleanup is one fixed grace, capped by the original deadline plus grace.
    // Group signalling is done exactly once while the unreaped leader pins PGID.
    let cleanup_deadline = Instant::now().min(deadline) + Duration::from_millis(CLEANUP_GRACE_MS);
    if report.cleanup.ownership == "owned" {
        if boundary == Boundary::Observer || !report.process.exit_observed {
            report.cleanup.signal = Some(libc::SIGKILL);
            report.cleanup.signal_before_reap = true;
            report.cleanup.signal_result = Some(ops.signal(
                if boundary == Boundary::Observer {
                    -pid
                } else {
                    pid
                },
                libc::SIGKILL,
            ));
        }
        loop {
            if let Err(e) = ops.reap(&mut child, &mut report.process) {
                if e.kind() != io::ErrorKind::Interrupted {
                    report.process.wait_error = Some(e.to_string());
                    report.cleanup.ownership = "lost".into();
                    report.cleanup.detail = Some(format!("wait failed: {e}"));
                    break;
                }
            }
            if report.process.reaped {
                report.cleanup.ownership_released = true;
            }
            if boundary == Boundary::Observer && report.process.reaped {
                // This is observation only; no group signal can follow reaping.
                let probe = ops.signal(-pid, 0);
                let absent = probe.rc == -1 && probe.errno == Some(libc::ESRCH);
                report.cleanup.group_probe = Some(probe);
                if absent {
                    report.cleanup.outcome = "group_absent".into();
                    break;
                }
            } else if boundary == Boundary::LogShow && report.process.reaped {
                report.cleanup.outcome = "child_reaped".into();
                break;
            }
            if Instant::now() >= cleanup_deadline {
                report.cleanup.detail = Some("cleanup grace exhausted".into());
                break;
            }
            std::thread::sleep(
                Duration::from_millis(2)
                    .min(cleanup_deadline.saturating_duration_since(Instant::now())),
            );
        }
    } else {
        report.cleanup.detail = Some("ownership lost; signalling withheld".into());
    }
    if report.cleanup.outcome == "not_started" {
        report.cleanup.outcome = "unconfirmed".into();
        if report.cutoff.is_none() {
            report.cutoff = Some(Cutoff::reason(
                "cleanup_unconfirmed",
                report.cleanup.detail.clone(),
            ));
        }
    }
    if report.cutoff.is_none()
        && (report.process.exit_code != Some(0) || report.process.term_signal.is_some())
    {
        report.cutoff = Some(Cutoff::reason("process_exit", None));
    }
    finish(answer, entry)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn documented_collection_limits() {
        let manifest: serde_json::Value = serde_json::from_str(include_str!(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../docs/limits.json"
        )))
        .unwrap();
        let owned: std::collections::BTreeMap<_, _> =
            manifest["limits"]
                .as_array()
                .unwrap()
                .iter()
                .filter(|row| {
                    row["checks"].as_array().unwrap().iter().any(|c| {
                        c["path"] == "controller/src/log_capture.rs" && c["kind"] == "value"
                    })
                })
                .map(|row| (row["id"].as_str().unwrap(), row["value"].as_u64().unwrap()))
                .collect();
        let actual = std::collections::BTreeMap::from([
            ("log_show_stdout", LOG_STDOUT_BYTES as u64),
            ("log_show_stderr", LOG_STDERR_BYTES as u64),
            ("log_observer_stderr", OBSERVER_STDERR_BYTES as u64),
            ("log_collection_timeout", DEFAULT_LOG_TIMEOUT_MS as u64),
            ("log_cleanup_grace", CLEANUP_GRACE_MS as u64),
            ("log_deny_events", MAX_DENY_EVENTS as u64),
            ("log_candidate_count", MAX_ASSOCIATIONS as u64),
            ("log_candidate_bytes", MAX_ASSOCIATION_BYTES as u64),
            ("log_correlation_steps", MAX_CORRELATION_STEPS as u64),
            ("log_reply_structure", MAX_OBSERVER_JSON_TOKENS as u64),
            ("log_observer_metadata", MAX_OBSERVER_METADATA_BYTES as u64),
        ]);
        assert_eq!(owned, actual);
    }

    fn python(script: &str) -> Command {
        let mut command = Command::new("/usr/bin/python3");
        command.args(["-c", script]);
        command
    }

    fn budget(ms: u64) -> CollectionBudget {
        LogTimeout {
            milliseconds: ms,
            source: TimeoutSource::Cli,
        }
        .start()
        .unwrap()
    }

    fn absent(pid: i32) {
        let deadline = Instant::now() + Duration::from_secs(2);
        loop {
            let observed = signal(-pid, 0);
            if observed.rc == -1 && observed.errno == Some(libc::ESRCH) {
                return;
            }
            assert!(
                Instant::now() < deadline,
                "group {pid} remains: {observed:?}"
            );
            std::thread::sleep(Duration::from_millis(5));
        }
    }

    #[test]
    fn timeout_values_are_finite_and_shared_without_restart() {
        for value in [
            "",
            "0",
            "-1",
            "+1",
            " 1",
            "1.2",
            "unlimited",
            "18446744073709551615",
            "18446744073709551616",
        ] {
            assert!(LogTimeout::parse(value).is_err(), "{value}");
        }
        assert_eq!(LogTimeout::default().milliseconds, DEFAULT_LOG_TIMEOUT_MS);
        let allowance = LogTimeout::parse("500").unwrap();
        let before = allowance.start().unwrap();
        std::thread::sleep(Duration::from_millis(40));
        let received = CollectionBudget::from_argument(&before.argument()).unwrap();
        assert_eq!(received.deadline_monotonic_ns, before.deadline_monotonic_ns);
        assert!(monotonic_ns().unwrap() > received.started_monotonic_ns + 20_000_000);
        assert!(CollectionBudget::at(u64::MAX - 10, allowance).is_err());
        let mut bad = serde_json::to_value(before).unwrap();
        bad["deadline_monotonic_ns"] = serde_json::json!(before.deadline_monotonic_ns + 1);
        assert!(CollectionBudget::from_argument(&bad.to_string()).is_err());
    }

    #[test]
    fn both_raw_streams_are_bounded_at_exact_edges() {
        for boundary in [Boundary::Observer, Boundary::LogShow] {
            for target in ["stdout", "stderr"] {
                for count in [63, 64, 65] {
                    let script = format!(
                        "import os; os.write({}, b'x'*{count})",
                        if target == "stdout" { 1 } else { 2 }
                    );
                    let output =
                        capture_with_limits(&mut python(&script), budget(1000), boundary, (64, 64));
                    let r = &output.supervision;
                    let stream = if target == "stdout" {
                        &r.stdout
                    } else {
                        &r.stderr
                    };
                    assert_eq!(stream.bytes_read, count);
                    assert_eq!(stream.bytes_retained, count.min(64));
                    assert_eq!(stream.truncated, count > 64);
                    if count <= 64 {
                        assert!(r.complete(), "{r:?}");
                    } else {
                        let reason = r.cutoff.as_ref().unwrap();
                        assert_eq!(reason.reason, "output_overflow");
                        assert_eq!(reason.stream.as_deref(), Some(target));
                        assert_eq!((reason.limit, reason.observed), (Some(64), Some(65)));
                    }
                    if boundary == Boundary::Observer {
                        absent(r.process.pid.unwrap());
                    }
                }
            }
        }
    }

    #[test]
    fn simultaneous_output_cannot_deadlock_or_read_past_limits() {
        let script = "import os, threading; t=threading.Thread(target=lambda: os.write(2, b'e'*200000)); t.start(); os.write(1,b'o'*200000); t.join()";
        let output = capture_with_limits(
            &mut python(script),
            budget(1000),
            Boundary::Observer,
            (32768, 32768),
        );
        assert_eq!(
            output.supervision.cutoff.as_ref().unwrap().reason,
            "output_overflow"
        );
        assert!(output.stdout.len() <= 32768 && output.stderr.len() <= 32768);
        assert!(
            output.supervision.stdout.bytes_read <= 32769
                && output.supervision.stderr.bytes_read <= 32769
        );
        assert_eq!(output.supervision.cleanup.outcome, "group_absent");
        absent(output.supervision.process.pid.unwrap());
    }

    #[test]
    fn larger_allowance_buys_time_only_and_still_bounds_hangs() {
        for ms in [100, 700] {
            let start = Instant::now();
            let output = capture(
                &mut python("import time; time.sleep(.25); print('complete')"),
                budget(ms),
                Boundary::Observer,
            );
            assert_eq!(output.supervision.budget.timeout_ms, ms);
            assert_eq!(output.supervision.stdout.limit_bytes, OBSERVER_STDOUT_BYTES);
            assert_eq!(output.supervision.cleanup.grace_ms, CLEANUP_GRACE_MS);
            if ms == 100 {
                assert_eq!(
                    output.supervision.cutoff.as_ref().unwrap().reason,
                    "deadline"
                );
            } else {
                assert!(output.supervision.complete(), "{:?}", output.supervision);
            }
            assert!(start.elapsed() < Duration::from_millis(ms + CLEANUP_GRACE_MS + 500));
            let hang = capture(
                &mut python("import time; time.sleep(60)"),
                budget(ms),
                Boundary::Observer,
            );
            assert_eq!(hang.supervision.cutoff.as_ref().unwrap().reason, "deadline");
            absent(hang.supervision.process.pid.unwrap());
        }
    }

    #[test]
    fn observer_death_cleans_unannounced_children_with_open_or_closed_pipes() {
        for close_pipes in [false, true] {
            // The helper never supplies JSON or announces a child PID. It does
            // independently verify membership before its immediate signal death.
            let script = format!(
                r#"import os, signal, time
assert os.getpgid(0) == os.getpid()
ready_r, ready_w = os.pipe()
pid = os.fork()
if pid == 0:
    assert os.getpgid(0) == os.getppid()
    if {close_pipes}:
        os.close(1); os.close(2)
    os.write(ready_w, b'!')
    os.close(ready_r); os.close(ready_w)
    time.sleep(60)
else:
    os.close(ready_w)
    assert os.read(ready_r, 1) == b'!'
    os.close(ready_r)
    os.kill(os.getpid(), signal.SIGKILL)
"#,
                close_pipes = if close_pipes { "True" } else { "False" }
            );
            let output = capture(&mut python(&script), budget(1500), Boundary::Observer);
            let r = output.supervision;
            assert!(!r.complete());
            assert_eq!(r.process.term_signal, Some(libc::SIGKILL));
            assert!(
                r.process.reaped && r.cleanup.signal_before_reap && r.cleanup.ownership_released
            );
            assert_eq!(r.cleanup.outcome, "group_absent", "{r:?}");
            assert!(
                output.stdout.is_empty(),
                "no child lifecycle announcement or reply"
            );
            assert!(
                output.stderr.is_empty(),
                "fixture membership assertions failed"
            );
            absent(r.process.pid.unwrap());
        }
    }

    #[test]
    fn launch_exit_and_closed_pipe_hang_have_explicit_facts() {
        let launch = capture(
            &mut Command::new("/no/such/pw-collector"),
            budget(500),
            Boundary::Observer,
        );
        assert_eq!(
            launch.supervision.cutoff.as_ref().unwrap().reason,
            "launch_error"
        );
        assert!(launch.supervision.process.pid.is_none());
        assert_eq!(launch.supervision.cleanup.ownership, "not_started");
        for (script, code, sig, reason) in [
            ("import sys; sys.exit(7)", Some(7), None, "process_exit"),
            (
                "import os,signal; os.kill(os.getpid(),signal.SIGTERM)",
                None,
                Some(libc::SIGTERM),
                "process_exit",
            ),
            (
                "import os,time; os.close(1); os.close(2); time.sleep(60)",
                None,
                Some(libc::SIGKILL),
                "deadline",
            ),
        ] {
            let out = capture(&mut python(script), budget(300), Boundary::Observer);
            assert_eq!(out.supervision.cutoff.as_ref().unwrap().reason, reason);
            assert_eq!(out.supervision.process.exit_code, code);
            assert_eq!(out.supervision.process.term_signal, sig);
            absent(out.supervision.process.pid.unwrap());
        }
    }

    struct FaultOps {
        fault: &'static str,
        reaped: bool,
        signals: usize,
    }
    impl ProcessOps for FaultOps {
        fn read(
            &mut self,
            mut pipe: &mut dyn Read,
            bytes: &mut Vec<u8>,
            observation: &mut StreamObservation,
        ) -> io::Result<bool> {
            if self.fault == "read" {
                Err(io::Error::from_raw_os_error(libc::EIO))
            } else {
                read_once(&mut pipe, bytes, observation)
            }
        }
        fn observe(&mut self, pid: i32) -> io::Result<bool> {
            if self.fault == "ownership" {
                Err(io::Error::from_raw_os_error(libc::ECHILD))
            } else {
                observe_exit(pid)
            }
        }
        fn signal(&mut self, target: i32, value: i32) -> SyscallObservation {
            if value != 0 {
                assert!(!self.reaped, "no signal after releasing the owned PID");
                self.signals += 1;
                if self.fault == "signal" {
                    return SyscallObservation {
                        rc: -1,
                        errno: Some(libc::EPERM),
                    };
                }
            } else if self.fault == "probe" {
                return SyscallObservation {
                    rc: -1,
                    errno: Some(libc::EPERM),
                };
            }
            signal(target, value)
        }
        fn reap(&mut self, child: &mut Child, result: &mut ProcessObservation) -> io::Result<()> {
            if self.fault == "reap" {
                return Err(io::Error::from_raw_os_error(libc::ECHILD));
            }
            reap(child, result)?;
            self.reaped |= result.reaped;
            Ok(())
        }
    }

    #[test]
    fn pipe_read_failure_retains_reason_and_still_cleans_owned_group() {
        let mut ops = FaultOps {
            fault: "read",
            reaped: false,
            signals: 0,
        };
        let out = capture_with_ops(
            &mut python("import time; time.sleep(60)"),
            budget(500),
            Boundary::Observer,
            (64, 64),
            &mut ops,
        );
        assert_eq!(
            out.supervision.cutoff.as_ref().unwrap().reason,
            "read_error"
        );
        assert!(out.supervision.stdout.read_error.is_some());
        assert_eq!(out.supervision.stdout.bytes_read, 0);
        assert_eq!(out.supervision.cleanup.outcome, "group_absent");
        assert!(!out.supervision.complete());
        absent(out.supervision.process.pid.unwrap());
    }

    #[test]
    fn cleanup_failures_and_lost_ownership_remain_unconfirmed() {
        for fault in ["ownership", "signal", "probe", "reap"] {
            let mut ops = FaultOps {
                fault,
                reaped: false,
                signals: 0,
            };
            let out = capture_with_ops(
                &mut python("import time; time.sleep(60)"),
                budget(50),
                Boundary::Observer,
                (1024, 1024),
                &mut ops,
            );
            assert_eq!(out.supervision.cleanup.outcome, "unconfirmed");
            assert!(!out.supervision.complete());
            assert_eq!(ops.signals, if fault == "ownership" { 0 } else { 1 });
            let pid = out.supervision.process.pid.unwrap();
            if !out.supervision.process.reaped {
                // Independent fixture teardown owns this still-unreaped child.
                assert!(observe_exit(pid).is_ok());
                signal(-pid, libc::SIGKILL);
                let until = Instant::now() + Duration::from_secs(2);
                loop {
                    let rc = unsafe { libc::waitpid(pid, std::ptr::null_mut(), libc::WNOHANG) };
                    if rc == pid {
                        break;
                    }
                    assert!(rc >= 0 && Instant::now() < until);
                    std::thread::sleep(Duration::from_millis(2));
                }
            }
            absent(pid);
        }
    }
}
