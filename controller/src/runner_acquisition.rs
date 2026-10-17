//! Reconnect only after an admitted, pre-worker refusal from a proven host
//! generation. Unknown process observations never establish retirement.
use crate::run_flow::{ReplyVersion, reply_version};
use crate::runner_client::RunnerClientRun;
use serde::Serialize;
use serde_json::Value;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct Generation {
    pub pid: i32,
    pub start_sec: u64,
    pub start_usec: u64,
    pub executable_path: Option<PathBuf>,
}

pub trait ProcessObserver {
    fn observe(&self, pid: i32, with_path: bool) -> Result<Option<Generation>, String>;
    fn now(&self) -> Instant {
        Instant::now()
    }
    fn wait(&self, duration: Duration) {
        std::thread::sleep(duration);
    }
}

pub struct NativeObserver;
impl ProcessObserver for NativeObserver {
    fn observe(&self, pid: i32, with_path: bool) -> Result<Option<Generation>, String> {
        fn identity(pid: i32) -> Result<Option<Generation>, String> {
            let mut info: libc::proc_bsdinfo = unsafe { std::mem::zeroed() };
            let size = std::mem::size_of_val(&info) as i32;
            let count = unsafe {
                // A zero/short reply without a fresh errno is unknown, never
                // evidence of absence inherited from an earlier probe.
                *libc::__error() = 0;
                libc::proc_pidinfo(
                    pid,
                    libc::PROC_PIDTBSDINFO,
                    0,
                    (&mut info as *mut libc::proc_bsdinfo).cast(),
                    size,
                )
            };
            if count != size {
                let error = std::io::Error::last_os_error();
                return if count <= 0 && error.raw_os_error() == Some(libc::ESRCH) {
                    Ok(None)
                } else {
                    Err(format!("proc_pidinfo({pid}): returned {count}, {error}"))
                };
            }
            Ok(Some(Generation {
                pid,
                start_sec: info.pbi_start_tvsec,
                start_usec: info.pbi_start_tvusec,
                executable_path: None,
            }))
        }
        let Some(mut process) = identity(pid)? else {
            return Ok(None);
        };
        if with_path {
            let mut bytes = vec![0u8; libc::PROC_PIDPATHINFO_MAXSIZE as usize];
            let count = unsafe {
                *libc::__error() = 0;
                libc::proc_pidpath(pid, bytes.as_mut_ptr().cast(), bytes.len() as u32)
            };
            if count <= 0 {
                return Err(format!(
                    "proc_pidpath({pid}): {}",
                    std::io::Error::last_os_error()
                ));
            }
            use std::os::unix::ffi::OsStringExt;
            bytes.truncate(bytes.iter().position(|b| *b == 0).unwrap_or(bytes.len()));
            // Bracket the path read with start-time reads: a reused PID cannot
            // join the old generation's identity to a new executable.
            if identity(pid)?.as_ref() != Some(&process) {
                return Err(format!(
                    "process generation changed while identifying {pid}"
                ));
            }
            process.executable_path = Some(std::ffi::OsString::from_vec(bytes).into());
        }
        Ok(Some(process))
    }
}

#[derive(Serialize)]
pub struct RefusedAttempt {
    pub runner_client: Value,
    pub runner_result: Value,
    pub generation: Generation,
    pub observed_exit: Option<ExitObservation>,
    pub wait_outcome: String,
    pub observation_error: Option<String>,
}

#[derive(Serialize)]
pub struct ExitObservation {
    pub basis: &'static str,
    pub observed_at_unix_ms: u64,
    pub replacement: Option<Generation>,
}

pub struct Acquired {
    pub client: RunnerClientRun,
    pub reply: Option<Value>,
    pub refusals: Vec<RefusedAttempt>,
}

pub struct AcquisitionError {
    pub error: String,
    pub refusals: Vec<RefusedAttempt>,
}

pub fn acquire(
    timeout_ms: u64,
    executable: Option<&Path>,
    observer: &dyn ProcessObserver,
    client: impl Fn(u64) -> Result<(RunnerClientRun, Option<Value>), String>,
) -> Result<Acquired, AcquisitionError> {
    let started = observer.now();
    let budget = Duration::from_millis(timeout_ms);
    let mut remaining_ms = timeout_ms;
    let mut refusals = Vec::new();
    loop {
        let (capture, reply) = client(remaining_ms).map_err(|error| AcquisitionError {
            error,
            refusals: std::mem::take(&mut refusals),
        })?;
        let qualifying = reply.as_ref().filter(|reply| {
            executable.is_some()
                && capture
                    .request_delivery
                    .as_ref()
                    .is_none_or(|d| d.error.is_none())
                && matches!(reply_version(reply), ReplyVersion::Supported)
                && reply["normalized_outcome"] == "already_ran"
                && reply["steps"].as_array().is_some_and(Vec::is_empty)
                && reply.get("runner_subprocess").is_none_or(Value::is_null)
        });
        let generation = qualifying.and_then(|reply| {
            let pid = i32::try_from(reply["pid"].as_i64()?)
                .ok()
                .filter(|pid| *pid > 0)?;
            let process = observer.observe(pid, true).ok()??;
            (process.executable_path.as_deref() == executable).then_some(process)
        });
        let Some(generation) = generation else {
            return Ok(Acquired {
                client: capture,
                reply,
                refusals,
            });
        };
        let mut attempt = RefusedAttempt {
            runner_client: serde_json::to_value(&capture).expect("client serialization"),
            runner_result: reply.as_ref().unwrap().clone(),
            generation: generation.clone(),
            observed_exit: None,
            wait_outcome: "deadline".into(),
            observation_error: None,
        };
        let mut retired = false;
        while observer.now().saturating_duration_since(started) < budget {
            let observation = observer.observe(generation.pid, false);
            let exit = match observation {
                Ok(None) => Some(("esrch", None)),
                Ok(Some(current))
                    if current.start_sec != generation.start_sec
                        || current.start_usec != generation.start_usec =>
                {
                    Some(("pid_reused", Some(current)))
                }
                Ok(Some(_)) => None,
                Err(error) => {
                    attempt.wait_outcome = "observation_failed".into();
                    attempt.observation_error = Some(error);
                    break;
                }
            };
            if let Some((basis, replacement)) = exit {
                attempt.observed_exit = Some(ExitObservation {
                    basis,
                    replacement,
                    observed_at_unix_ms: crate::utils::now_unix_ms(),
                });
                attempt.wait_outcome = "retired".into();
                retired = true;
                break;
            }
            // Polling cadence is not an acquisition budget or attempt limit.
            let remaining =
                budget.saturating_sub(observer.now().saturating_duration_since(started));
            observer.wait(remaining.min(Duration::from_millis(10)));
        }
        refusals.push(attempt);
        remaining_ms = budget
            .saturating_sub(observer.now().saturating_duration_since(started))
            .as_millis() as u64;
        if !retired || remaining_ms == 0 {
            return Ok(Acquired {
                client: capture,
                reply,
                refusals,
            });
        }
    }
}

#[cfg(test)]
pub mod tests {
    use super::*;
    use serde_json::json;
    use std::cell::{Cell, RefCell};
    use std::collections::VecDeque;

    struct Observer {
        base: Instant,
        elapsed: Cell<Duration>,
        reads: RefCell<VecDeque<Result<Option<Generation>, String>>>,
    }
    impl ProcessObserver for Observer {
        fn observe(&self, _: i32, _: bool) -> Result<Option<Generation>, String> {
            self.reads
                .borrow_mut()
                .pop_front()
                .expect("unexpected process read")
        }
        fn now(&self) -> Instant {
            self.base + self.elapsed.get()
        }
        fn wait(&self, duration: Duration) {
            self.elapsed.set(self.elapsed.get() + duration);
        }
    }
    fn observer(reads: Vec<Result<Option<Generation>, String>>) -> Observer {
        Observer {
            base: Instant::now(),
            elapsed: Cell::new(Duration::ZERO),
            reads: RefCell::new(reads.into()),
        }
    }
    fn generation() -> Generation {
        Generation {
            pid: 17,
            start_sec: 1,
            start_usec: 2,
            executable_path: Some("/runner".into()),
        }
    }
    fn refusal() -> Value {
        json!({"schema_version": crate::json_contract::RESPONSE_SCHEMA_VERSION, "normalized_outcome": "already_ran", "steps": [], "pid": 17})
    }
    fn capture(at: u64) -> RunnerClientRun {
        RunnerClientRun {
            argv: vec!["client".into()],
            started_at_unix_ms: at,
            ended_at_unix_ms: at + 1,
            exit_code: 1,
            request_delivery: None,
            output: crate::utils::JsonOutputCapture::unavailable(
                String::new(),
                crate::utils::RUNNER_CAPTURE_BYTES,
            ),
        }
    }
    pub fn shape_attempt() -> RefusedAttempt {
        RefusedAttempt {
            runner_client: serde_json::to_value(capture(1)).unwrap(),
            runner_result: refusal(),
            generation: generation(),
            observed_exit: Some(ExitObservation {
                basis: "pid_reused",
                observed_at_unix_ms: 3,
                replacement: Some(generation()),
            }),
            wait_outcome: "retired".into(),
            observation_error: Some("constructed".into()),
        }
    }
    #[test]
    fn every_nonqualifying_reply_stops_without_process_reads() {
        for mutate in [
            |v: &mut Value| v["normalized_outcome"] = json!("ok"),
            |v: &mut Value| v["steps"] = json!([{}]),
            |v: &mut Value| v["steps"] = Value::Null,
            |v: &mut Value| v["runner_subprocess"] = json!({}),
            |v: &mut Value| v["schema_version"] = json!(0),
            |v: &mut Value| v["schema_version"] = json!("23"),
            |v: &mut Value| v["pid"] = json!(-1),
        ] {
            let mut reply = refusal();
            mutate(&mut reply);
            let result = acquire(100, Some(Path::new("/runner")), &observer(vec![]), |_| {
                Ok((capture(1), Some(reply.clone())))
            })
            .ok()
            .unwrap();
            assert!(result.refusals.is_empty());
            assert_eq!(result.reply, Some(reply));
        }
    }
    #[test]
    fn failed_delivery_and_builtin_do_not_reacquire() {
        let result = acquire(100, None, &observer(vec![]), |_| {
            Ok((capture(1), Some(refusal())))
        })
        .ok()
        .unwrap();
        assert!(result.refusals.is_empty());
        let result = acquire(100, Some(Path::new("/runner")), &observer(vec![]), |_| {
            let mut client = capture(1);
            client.request_delivery = Some(crate::utils::RequestDelivery {
                bytes_written: 0,
                error: Some("broken pipe".into()),
            });
            Ok((client, Some(refusal())))
        })
        .ok()
        .unwrap();
        assert!(result.refusals.is_empty());
    }
    #[test]
    fn unknown_absent_or_wrong_executable_is_not_a_qualifying_generation() {
        let mut wrong = generation();
        wrong.executable_path = Some("/neighbor".into());
        for read in [Err("denied".into()), Ok(None), Ok(Some(wrong))] {
            let result = acquire(
                100,
                Some(Path::new("/runner")),
                &observer(vec![read]),
                |_| Ok((capture(1), Some(refusal()))),
            )
            .ok()
            .unwrap();
            assert!(result.refusals.is_empty());
        }
    }
    #[test]
    fn retirement_and_pid_reuse_allow_only_a_fresh_attempt_with_remaining_budget() {
        let mut replacement = generation();
        replacement.start_usec += 1;
        for retired in [None, Some(replacement)] {
            let obs = observer(vec![
                Ok(Some(generation())),
                Ok(Some(generation())),
                Ok(retired.clone()),
            ]);
            let calls = Cell::new(0);
            let result = acquire(100, Some(Path::new("/runner")), &obs, |budget| {
                let index = calls.get();
                calls.set(index + 1);
                assert_eq!(budget, if index == 0 { 100 } else { 90 });
                Ok((
                    capture(if index == 0 { 1 } else { 1000 }),
                    Some(if index == 0 {
                        refusal()
                    } else {
                        json!({"normalized_outcome":"ok"})
                    }),
                ))
            })
            .ok()
            .unwrap();
            assert_eq!(calls.get(), 2);
            assert_eq!(result.refusals.len(), 1);
            assert_eq!(
                result.refusals[0].observed_exit.as_ref().unwrap().basis,
                if retired.is_none() {
                    "esrch"
                } else {
                    "pid_reused"
                }
            );
            // Downstream log windows receive only this returned client span.
            assert_eq!(result.client.started_at_unix_ms, 1000);
            assert_eq!(result.refusals[0].runner_client["started_at_unix_ms"], 1);
        }
    }
    #[test]
    fn deadline_or_unknown_observation_returns_last_refusal_with_receipt() {
        for failed in [false, true] {
            let obs = observer(vec![
                Ok(Some(generation())),
                if failed {
                    Err("denied".into())
                } else {
                    Ok(Some(generation()))
                },
            ]);
            let result = acquire(10, Some(Path::new("/runner")), &obs, |_| {
                Ok((capture(1), Some(refusal())))
            })
            .ok()
            .unwrap();
            assert_eq!(result.reply, Some(refusal()));
            assert_eq!(result.refusals.len(), 1);
            let attempt = &result.refusals[0];
            assert!(attempt.observed_exit.is_none());
            assert_eq!(
                attempt.wait_outcome,
                if failed {
                    "observation_failed"
                } else {
                    "deadline"
                }
            );
        }
    }
    #[test]
    fn multiple_refusals_share_one_budget_and_launch_failure_preserves_history() {
        let obs = observer(vec![
            Ok(Some(generation())),
            Ok(None),
            Ok(Some(generation())),
        ]);
        let calls = Cell::new(0);
        let result = acquire(10, Some(Path::new("/runner")), &obs, |_| {
            calls.set(calls.get() + 1);
            if calls.get() == 2 {
                obs.elapsed.set(Duration::from_millis(10));
            }
            let mut reply = refusal();
            reply["specimen_id"] = json!(calls.get().to_string());
            Ok((capture(calls.get()), Some(reply)))
        })
        .ok()
        .unwrap();
        assert_eq!(calls.get(), 2);
        assert_eq!(result.refusals.len(), 2);
        assert_eq!(result.client.started_at_unix_ms, 2);
        assert_eq!(result.reply.as_ref().unwrap()["specimen_id"], "2");
        let obs = observer(vec![Ok(Some(generation())), Ok(None)]);
        let calls = Cell::new(0);
        let error = acquire(10, Some(Path::new("/runner")), &obs, |_| {
            calls.set(calls.get() + 1);
            if calls.get() == 2 {
                Err("launch failed".into())
            } else {
                Ok((capture(1), Some(refusal())))
            }
        })
        .err()
        .unwrap();
        assert_eq!(error.error, "launch failed");
        assert_eq!(error.refusals.len(), 1);
    }
}
