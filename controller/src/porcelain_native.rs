//! Independent native-attempt consistency checks over the admitted wire records.
use super::*;

fn errno_agrees(rc: i64, errno: Option<i32>) -> bool {
    if rc == -1 {
        errno.is_some_and(|e| e >= 0)
    } else {
        errno.is_none()
    }
}
fn attempt_status(
    attempt: &PWRunnerAttemptResult,
    failed: bool,
    errno: Option<i32>,
    outcome: &str,
) -> bool {
    attempt.rc == if failed { -1 } else { 0 }
        && attempt.errno == errno.filter(|e| *e != 0).map(i64::from)
        && attempt.outcome == if failed { outcome } else { "ok" }
}
fn metadata_valid(stat: &PWRunnerFileStat) -> bool {
    matches!(stat.rc, -1 | 0)
        && errno_agrees(i64::from(stat.rc), stat.errno)
        && if stat.rc == 0 {
            stat.identity.is_some() && stat.size.is_some()
        } else {
            stat.identity.is_none() && stat.size.is_none()
        }
}
pub(super) fn fresh_read_problem(a: &PWRunnerAttemptResult) -> Option<&'static str> {
    let expected = a.requested_kind.as_deref() == Some("file")
        && a.requested_action.as_deref() == Some("read_fresh")
        && a.result_source.as_deref() == Some("worker");
    let Some(r) = &a.fresh_read else {
        return expected.then_some("completed fresh read lacks syscall observations");
    };
    if !expected || r.open_rc < -1 {
        return Some("fresh read requires a completed read_fresh attempt");
    }
    if r.open_rc == -1 {
        return (!(errno_agrees(-1, r.open_errno)
            && r.read_rc.is_none()
            && r.read_errno.is_none()
            && r.stat_rc.is_none()
            && r.stat_errno.is_none()
            && r.identity.is_none()
            && r.close_rc.is_none()
            && r.close_errno.is_none()
            && r.content.is_none()
            && attempt_status(a, true, r.open_errno, "read_failed")))
        .then_some("failed fresh open cannot supply read/stat/close evidence");
    }
    let (Some(count), Some(stat), Some(close)) = (r.read_rc, r.stat_rc, r.close_rc) else {
        return Some("invalid fresh syscall results");
    };
    if r.open_errno.is_some()
        || !(-1..=64).contains(&count)
        || !matches!(stat, -1 | 0)
        || !matches!(close, -1 | 0)
    {
        return Some("invalid fresh syscall results");
    }
    if !errno_agrees(count, r.read_errno)
        || !errno_agrees(i64::from(stat), r.stat_errno)
        || !errno_agrees(i64::from(close), r.close_errno)
        || (stat == 0) != r.identity.is_some()
    {
        return Some("fresh syscall failure evidence disagrees");
    }
    if count >= 0 {
        if r.content.as_ref().map(Vec::len) != Some(count as usize) {
            return Some("fresh read bytes disagree with native count");
        }
    } else if r.content.is_some() {
        return Some("failed fresh read cannot supply content");
    }
    // Native order is stat, read, close. Preserve the first failure even when a
    // later syscall also fails or a successful read retains bytes.
    let failed = stat < 0 || count < 0 || close < 0;
    let errno = if stat < 0 {
        r.stat_errno
    } else if count < 0 {
        r.read_errno
    } else if close < 0 {
        r.close_errno
    } else {
        None
    };
    (!attempt_status(a, failed, errno, "read_failed"))
        .then_some("fresh syscall results disagree with attempt")
}
pub(super) fn fresh_write_problem(a: &PWRunnerAttemptResult) -> Option<&'static str> {
    let expected = a.requested_kind.as_deref() == Some("file")
        && matches!(
            a.requested_action.as_deref(),
            Some("write_fresh" | "create_fresh")
        )
        && a.result_source.as_deref() == Some("worker");
    let Some(w) = &a.fresh_write else {
        return expected.then_some("completed fresh write lacks syscall observations");
    };
    if !expected || w.open_rc < -1 {
        return Some("fresh write requires a completed fresh-write attempt");
    }
    let creating = a.requested_action.as_deref() == Some("create_fresh");
    if creating != w.preopen_stat.is_some() {
        return Some("fresh creation requires its pre-open metadata observation");
    }
    if [
        &w.preopen_stat,
        &w.opened_stat,
        &w.truncated_stat,
        &w.written_stat,
    ]
    .into_iter()
    .flatten()
    .any(|s| !metadata_valid(s))
    {
        return Some("file metadata lacks its native result or successful payload");
    }
    if !errno_agrees(i64::from(w.open_rc), w.open_errno) {
        return Some("fresh write open errno disagrees with native result");
    }
    let mut failed = false;
    let mut first = None;
    let mut observe = |rc: i64, errno: Option<i32>, short: bool| {
        if !failed && (rc < 0 || short) {
            failed = true;
            first = if rc < 0 { errno } else { None };
        }
    };
    observe(i64::from(w.open_rc), w.open_errno, false);
    if w.open_rc == -1 {
        if w.opened_stat.is_some()
            || w.truncate_rc.is_some()
            || w.truncate_errno.is_some()
            || w.truncated_stat.is_some()
            || w.write_rc.is_some()
            || w.write_errno.is_some()
            || w.written_stat.is_some()
            || w.close_rc.is_some()
            || w.close_errno.is_some()
        {
            return Some("failed fresh write open cannot supply later syscall evidence");
        }
    } else {
        let (Some(opened), Some(close)) = (&w.opened_stat, w.close_rc) else {
            return Some("fresh write lacks opened metadata or close result");
        };
        if !matches!(close, -1 | 0) || !errno_agrees(i64::from(close), w.close_errno) {
            return Some("fresh write lacks opened metadata or close result");
        }
        observe(i64::from(opened.rc), opened.errno, false);
        if creating {
            if w.truncate_rc.is_some() || w.truncate_errno.is_some() || w.truncated_stat.is_some() {
                return Some("exclusive creation must not fabricate truncation");
            }
        } else {
            let (Some(truncate), Some(stat)) = (w.truncate_rc, &w.truncated_stat) else {
                return Some("fresh write lacks truncation observations");
            };
            if !matches!(truncate, -1 | 0) || !errno_agrees(i64::from(truncate), w.truncate_errno) {
                return Some("fresh write lacks truncation observations");
            }
            observe(i64::from(truncate), w.truncate_errno, false);
            observe(i64::from(stat.rc), stat.errno, false);
        }
        if creating || w.truncate_rc == Some(0) {
            let (Some(count), Some(stat)) = (w.write_rc, &w.written_stat) else {
                return Some("fresh write lacks bounded transfer observations");
            };
            if !(-1..=1).contains(&count) || !errno_agrees(count, w.write_errno) {
                return Some("fresh write lacks bounded transfer observations");
            }
            observe(count, w.write_errno, count == 0);
            observe(i64::from(stat.rc), stat.errno, false);
        } else if w.write_rc.is_some() || w.write_errno.is_some() || w.written_stat.is_some() {
            return Some("failed truncation cannot supply a later write");
        }
        observe(i64::from(close), w.close_errno, false);
    }
    (!attempt_status(a, failed, first, "write_failed"))
        .then_some("fresh write syscalls disagree with attempt status")
}
pub(super) fn exec_problem(a: &PWRunnerAttemptResult) -> Option<&'static str> {
    let Some(v) = &a.exec_observation else {
        return None;
    };
    let Some(pid) = a
        .child_pid
        .and_then(|p| i32::try_from(p).ok())
        .filter(|p| *p > 0)
    else {
        return Some("exec observation requires positive native child PID");
    };
    if a.requested_kind.as_deref() != Some("exec")
        || a.requested_action.as_deref() != Some("spawn")
        || a.result_source.as_deref() != Some("worker")
        || a.lifecycle.as_ref().map(|l| l.summary.as_str()) != Some("completed")
    {
        return Some("exec observation requires published worker exec");
    }
    let (c, k, r) = (&v.collection, &v.cleanup, &v.reap);
    let positive = |e: Option<i32>| e.is_none_or(|e| e > 0);
    for s in [&c.stdout, &c.stderr] {
        if !positive(s.read_errno)
            || matches!(s.read_errno, Some(libc::EINTR | libc::EAGAIN))
            || !s
                .poll_revents
                .is_none_or(|e| (-32768..=32767).contains(&e) && e & 0x28 != 0 && e & 0x11 == 0)
            || (s.eof && (s.read_errno.is_some() || s.poll_revents.is_some()))
            || (s.read_errno.is_some() && s.poll_revents.is_some())
        {
            return Some("invalid exec stream observation");
        }
    }
    if !positive(c.waitid_errno)
        || !positive(c.poll_errno)
        || c.waitid_errno == Some(libc::EINTR)
        || c.poll_errno == Some(libc::EINTR)
    {
        return Some("invalid exec collection errno");
    }
    if c.clock_fault == Some(0) || r.clock_fault == Some(0) {
        return Some("invalid exec clock reason");
    }
    let stream_error = [&c.stdout, &c.stderr]
        .into_iter()
        .any(|s| s.read_errno.is_some() || s.poll_revents.is_some());
    let errors = c.waitid_errno.is_some() || c.poll_errno.is_some() || stream_error;
    if c.waitid_errno.is_some() && c.leader_exit_observed {
        return Some("waitid failure after already observed leader exit");
    }
    if c.waitid_errno.is_some() && (c.poll_errno.is_some() || stream_error)
        || c.poll_errno.is_some() && stream_error
    {
        return Some("incompatible exec collection branches");
    }
    let collection_valid = match c.stop_reason.as_str() {
        "leader_exit_and_eof" => {
            c.leader_exit_observed
                && c.stdout.eof
                && c.stderr.eof
                && !errors
                && c.clock_fault.is_none()
                && c.deadline_kind.is_none()
        }
        "deadline" => {
            matches!(c.deadline_kind.as_deref(), Some("child" | "plan"))
                && !errors
                && c.clock_fault.is_none()
        }
        "observation_error" => errors && c.clock_fault.is_none() && c.deadline_kind.is_none(),
        "clock_fault" => c.clock_fault.is_some() && !errors && c.deadline_kind.is_none(),
        _ => false,
    };
    if !collection_valid {
        return Some("exec collection stop contradicts observations");
    }
    let signal_valid = |s: &PWExecSignalRequest, target| {
        s.target == target
            && s.signal == libc::SIGKILL
            && match s.rc {
                -1 => s.errno.is_some_and(|e| e > 0),
                0 => s.errno.is_none(),
                _ => false,
            }
    };
    let failed_group = k
        .group_request
        .as_ref()
        .is_some_and(|g| g.rc == -1 && g.errno != Some(libc::ESRCH));
    let cleanup_valid = match k.state.as_str() {
        "not_requested" => {
            c.stop_reason == "leader_exit_and_eof"
                && k.group_request.is_none()
                && k.leader_fallback.is_none()
        }
        "ownership_unconfirmed" => {
            c.waitid_errno.is_some() && k.group_request.is_none() && k.leader_fallback.is_none()
        }
        "requested" => {
            c.stop_reason != "leader_exit_and_eof"
                && c.waitid_errno.is_none()
                && k.group_request
                    .as_ref()
                    .is_some_and(|g| signal_valid(g, -pid))
                && failed_group == k.leader_fallback.is_some()
                && k.leader_fallback
                    .as_ref()
                    .is_none_or(|f| signal_valid(f, pid))
        }
        _ => false,
    };
    if !cleanup_valid {
        return Some("exec cleanup contradicts native call roles");
    }
    let w = &r.last_wait;
    if !matches!(w.rc, -1 | 0) && w.rc != pid {
        return Some("invalid exec wait return");
    }
    if !(if w.rc == -1 {
        w.errno.is_some_and(|e| e > 0)
    } else {
        w.errno.is_none()
    }) || (w.rc == pid) != w.status.is_some()
    {
        return Some("exec wait errno or status lacks supporting return");
    }
    let (exit, signal) = w
        .status
        .map(|s| {
            let bits = s & 0x7f;
            (
                if bits == 0 { (s >> 8) & 0xff } else { -1 },
                if bits != 0 && bits != 127 { bits } else { 0 },
            )
        })
        .unwrap_or((-1, 0));
    if a.child_exit_code != Some(i64::from(exit)) || a.child_term_signal != Some(i64::from(signal))
    {
        return Some("exec legacy leader status disagrees with confirmed wait");
    }
    let reap_valid = match r.stop_reason.as_str() {
        "reaped" => w.rc == pid,
        "wait_error" => w.rc == -1 && w.errno != Some(libc::EINTR),
        stop @ ("ownership_unconfirmed" | "group_request_failed" | "clock_fault" | "deadline") => {
            (w.rc == 0 || (w.rc == -1 && w.errno == Some(libc::EINTR)))
                && match stop {
                    "ownership_unconfirmed" => k.state == "ownership_unconfirmed",
                    "group_request_failed" => k.state != "ownership_unconfirmed" && failed_group,
                    _ => {
                        k.state != "ownership_unconfirmed"
                            && !failed_group
                            && ((stop == "clock_fault") == r.clock_fault.is_some())
                    }
                }
        }
        _ => false,
    };
    (!reap_valid).then_some("exec reap stop contradicts final wait or branch priority")
}
pub(super) fn validate(reply: &PWRunnerRunResult, out: &mut Vec<IntegrityIssue>) {
    for step in &reply.steps {
        for (kind, problem) in [
            ("fresh_read", fresh_read_problem(&step.attempt)),
            ("fresh_write", fresh_write_problem(&step.attempt)),
            ("exec_observation", exec_problem(&step.attempt)),
        ] {
            if let Some(problem) = problem {
                issue(out, kind, format!("{}: {problem}", step.step_id));
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn ordinary_attempt() -> PWRunnerAttemptResult {
        super::super::tests::ordinary().steps.remove(0).attempt
    }
    fn stat(size: i64) -> PWRunnerFileStat {
        PWRunnerFileStat {
            rc: 0,
            errno: None,
            identity: Some(PWFileIdentity {
                device: 1,
                inode: 2,
                mode: 33152,
                uid: 501,
                gid: 20,
            }),
            size: Some(size),
        }
    }
    fn write(creating: bool) -> PWRunnerAttemptResult {
        let mut a = ordinary_attempt();
        a.requested_action = Some(
            if creating {
                "create_fresh"
            } else {
                "write_fresh"
            }
            .into(),
        );
        a.fresh_read = None;
        a.fresh_write = Some(PWRunnerFreshWrite {
            open_rc: 5,
            open_errno: None,
            truncate_rc: (!creating).then_some(0),
            truncate_errno: None,
            write_rc: Some(1),
            write_errno: None,
            close_rc: Some(0),
            close_errno: None,
            preopen_stat: creating.then_some(PWRunnerFileStat {
                rc: -1,
                errno: Some(libc::ENOENT),
                identity: None,
                size: None,
            }),
            opened_stat: Some(stat(if creating { 0 } else { 19 })),
            truncated_stat: (!creating).then_some(stat(0)),
            written_stat: Some(stat(1)),
        });
        a.rc = 0;
        a.errno = None;
        a.outcome = "ok".into();
        a
    }
    #[test]
    fn typed_exec_observation_corpus_retains_native_facts() {
        let cases: serde_json::Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/contract/exec_observation.json"
        ))
        .unwrap();
        for section in ["valid", "invalid"] {
            for case in cases[section].as_array().unwrap() {
                match serde_json::from_value::<PWRunnerAttemptResult>(case["attempt"].clone()) {
                    Ok(a) => {
                        let before = a.clone();
                        let problem = exec_problem(&a);
                        assert_eq!(
                            problem.is_none(),
                            section == "valid",
                            "{}: {problem:?}",
                            case["name"]
                        );
                        assert_eq!(a, before);
                    }
                    Err(e) => assert_eq!(section, "invalid", "{}: {e}", case["name"]),
                }
            }
        }
    }
    #[test]
    fn typed_fresh_read_preserves_bytes_and_first_failure() {
        let mut a = ordinary_attempt();
        assert!(fresh_read_problem(&a).is_none());
        a.rc = -1;
        a.errno = Some(libc::EBADF.into());
        a.outcome = "read_failed".into();
        a.fresh_read = Some(PWRunnerFreshRead {
            open_rc: 5,
            open_errno: None,
            read_rc: Some(2),
            read_errno: None,
            stat_rc: Some(-1),
            stat_errno: Some(libc::EBADF),
            identity: None,
            close_rc: Some(-1),
            close_errno: Some(libc::EINTR),
            content: Some(vec![0x00, 0xff]),
        });
        assert!(fresh_read_problem(&a).is_none());
        let before = a.clone();
        a.errno = Some(libc::EINTR.into());
        assert!(fresh_read_problem(&a).is_some());
        assert_eq!(a.fresh_read, before.fresh_read);
        a = before;
        a.fresh_read.as_mut().unwrap().content = Some(vec![0x00]);
        assert_eq!(
            fresh_read_problem(&a),
            Some("fresh read bytes disagree with native count")
        );
        a = ordinary_attempt();
        a.fresh_read.as_mut().unwrap().read_rc = Some(0);
        assert_eq!(
            fresh_read_problem(&a),
            Some("failed fresh open cannot supply read/stat/close evidence")
        );
    }
    #[test]
    fn typed_fresh_write_creation_and_failure_precedence() {
        for creating in [false, true] {
            assert!(fresh_write_problem(&write(creating)).is_none());
        }
        let mut a = write(false);
        let w = a.fresh_write.as_mut().unwrap();
        w.write_rc = Some(0);
        w.written_stat = Some(stat(0));
        w.close_rc = Some(-1);
        w.close_errno = Some(libc::EBADF);
        a.rc = -1;
        a.errno = None;
        a.outcome = "write_failed".into();
        assert!(
            fresh_write_problem(&a).is_none(),
            "short transfer must not inherit close errno"
        );
        let facts = a.fresh_write.clone();
        a.errno = Some(libc::EBADF.into());
        assert!(fresh_write_problem(&a).is_some());
        assert_eq!(a.fresh_write, facts);
        let mut a = write(true);
        let w = a.fresh_write.as_mut().unwrap();
        w.opened_stat = Some(PWRunnerFileStat {
            rc: -1,
            errno: Some(libc::EBADF),
            identity: None,
            size: None,
        });
        w.write_rc = Some(-1);
        w.write_errno = Some(libc::EIO);
        w.close_rc = Some(-1);
        w.close_errno = Some(libc::EINTR);
        a.rc = -1;
        a.errno = Some(libc::EBADF.into());
        a.outcome = "write_failed".into();
        assert!(fresh_write_problem(&a).is_none());
        a.errno = Some(libc::EIO.into());
        assert!(fresh_write_problem(&a).is_some());
        let mut a = write(true);
        a.fresh_write.as_mut().unwrap().truncate_rc = Some(0);
        assert!(fresh_write_problem(&a).is_some());
        let mut a = write(false);
        a.fresh_write
            .as_mut()
            .unwrap()
            .written_stat
            .as_mut()
            .unwrap()
            .size = None;
        assert!(fresh_write_problem(&a).is_some());
    }
}
