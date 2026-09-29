// Included in run_flow::tests to exercise the private production assembly seam.
mod log_replay {
    use super::*;
    use crate::log_capture::{self, Boundary, CollectionBudget, LogTimeout};
    use crate::log_show::capture_show;
    use crate::sandbox_log::{observer_argv, parse_supervised_observer};
    use std::io::Write;
    use std::process::{Command, Stdio};

    fn native(plan: &[Value]) -> Value {
        let mut runner = worker("ok", None);
        runner["schema_version"] = json!(7);
        runner["steps"] = json!(plan.iter().map(|step| json!({
            "step_id": step["step_id"], "drift": null,
            "sandbox_check": {"outcome":"allow", "native_rc":0, "result_source":"validator"},
            "attempt": {"requested_kind":"file", "requested_action":step["attempt"]["action"],
                "requested_path":step["attempt"]["target"], "outcome":"open_failed", "errno":1,
                "native_rc":-1, "result_source":"worker"},
            "comparison": {"scope":"submitted_operation_and_target", "prediction":"allow",
                "observation":"permission_failure", "observation_basis":"permission_errno",
                "operation_relation":"matched", "target_relation":"same_submitted",
                "conclusion":"unavailable", "limitations":["state_stability_unestablished",
                    "query_attempt_order_unestablished", "sandbox_attribution_unestablished"]}
        })).collect::<Vec<_>>());
        runner
    }

    fn replay(plan: &[Value], lines: &[String], fault: &str, timeout: LogTimeout) -> Value {
        let runner = native(plan);
        let (result, data, code) = attach_sandbox_logs(
            complete_execution(execution_data(Some(runner.clone()))),
            &json!({"probe_plan":plan}),
            fault == "disabled",
            |pid, name, window| {
                assert_ne!(fault, "disabled", "disabled capture invoked its collector");
                let budget = timeout.start().unwrap();
                let argv = observer_argv("observer".into(), pid, name, &window).unwrap();
                assert_eq!(argv[6], "1969-12-31 23:59:59+0000");
                assert_eq!(argv[8], "1970-01-01 00:00:05+0000");
                if fault == "unavailable" {
                    let raw = log_capture::capture(
                        &mut Command::new("/no/such/log-observer"),
                        budget,
                        Boundary::Observer,
                    );
                    return Ok(parse_supervised_observer(raw, window, pid, name));
                }
                // Exercise the same absolute-budget decoding used at the observer
                // boundary; only the OS query command is replaced by supplied text.
                let inner_budget = CollectionBudget::from_argument(&budget.argument()).unwrap();
                let mut query = Command::new("/usr/bin/python3");
                query.args([
                    "-c",
                    r#"import os,sys,time
fault = sys.argv[2]
if fault == 'slow': time.sleep(.35)
if fault == 'stalled': time.sleep(60)
os.write(1, sys.argv[1].encode())
if fault == 'inner_stdout': os.write(1, b'x'*1048577)
if fault == 'inner_stderr': os.write(2, b'e'*131073)
if fault == 'nonzero': sys.exit(7)
"#,
                    &lines.join("\n"),
                    fault,
                ]);
                let inner = capture_show(&mut query, inner_budget);
                let complete = inner.report.complete();
                let truncated = inner.report.stdout.truncated || inner.report.stderr.truncated;
                let mut payload = json!({"observer_schema_version":1, "mode":"show", "pid":pid,
                    "process_name":name, "start":window.start, "end":window.end, "last":null,
                    "log_rc":inner.report.process.exit_code,
                    "log_error":if complete {None} else {inner.report.cutoff.as_ref().map(|c| &c.reason)},
                    "blocked_reason":null, "log_truncated":truncated,
                    "log_stdout":inner.stdout, "log_stderr":inner.stderr,
                    "observed_lines":inner.observed_lines, "deny_lines":inner.deny_lines,
                    "observed_deny":!inner.deny_events.is_empty(), "deny_events":inner.deny_events,
                    "collection":inner.report});
                if fault == "wrong_window" {
                    payload["start"] = json!("1970-01-01 00:00:00+0000");
                }
                let result = json_contract::JsonResult {
                    ok: complete,
                    rc: None,
                    exit_code: Some(if complete { 0 } else { 3 }),
                    normalized_outcome: None,
                    errno: None,
                    error: None,
                    stderr: None,
                    stdout: None,
                };
                let text = json_contract::render_envelope_limited(
                    "sandbox_log_observer_report",
                    result,
                    &payload,
                    true,
                    log_capture::OBSERVER_STDOUT_BYTES - 1,
                )
                .unwrap();
                // File-backed transport avoids argv-size ceilings for capacity and
                // overflow diagnostics. The supervised pipe is the receiver input.
                let file = std::env::temp_dir().join(format!(
                    "pw-log-replay-{}-{}-{}.json",
                    std::process::id(),
                    fault,
                    budget.started_monotonic_ns
                ));
                std::fs::write(
                    &file,
                    if fault == "malformed" {
                        "{broken"
                    } else {
                        &text
                    },
                )
                .unwrap();
                let mut observer = if fault == "outer_prefix" {
                    let mut command = Command::new("/usr/bin/python3");
                    command.args(["-c", "import os,sys,time; raw=open(sys.argv[1],'rb').read(); os.write(1,raw[:len(raw)//2]); time.sleep(60)"]);
                    command
                } else {
                    Command::new("/bin/cat")
                };
                observer.arg(&file);
                let raw = log_capture::capture(&mut observer, budget, Boundary::Observer);
                std::fs::remove_file(file).unwrap();
                Ok(parse_supervised_observer(raw, window, pid, name))
            },
        );
        assert_eq!(code, 0);
        let wire: Value =
            serde_json::from_str(&json_contract::render_envelope("run", result, &data).unwrap())
                .unwrap();
        assert_eq!(wire["data"]["runner_result"], runner);
        assert_eq!(wire["result"]["ok"], true);
        assert_eq!(wire["result"]["normalized_outcome"], "ok");
        assert_eq!(
            wire["data"]["runner_sandbox_diagnostics"]["process_disposition"],
            "clean_exit"
        );
        assert!(wire["data"]["runner_sandbox_diagnostics"]["termination_cause"].is_null());
        wire
    }

    fn execution_only(wire: &Value) -> Value {
        let mut value = wire.clone();
        value
            .as_object_mut()
            .unwrap()
            .remove("generated_at_unix_ms");
        value["data"]
            .as_object_mut()
            .unwrap()
            .remove("sandbox_log_capture");
        for key in [
            "capture_status",
            "correlation_status",
            "first_deny",
            "permission_failures_without_record",
        ] {
            value["data"]["runner_sandbox_diagnostics"]
                .as_object_mut()
                .unwrap()
                .remove(key);
        }
        value
    }

    fn consumers(envelopes: &[Value]) {
        let mut child = Command::new("/usr/bin/python3")
            .args(["-B", "-c", r#"import json,sys
sys.path.insert(0,sys.argv[1])
from consumer import recover_evidence,validate_evidence_shape
from log_capture_contract import check_live_capture
for e in json.load(sys.stdin):
    assert not validate_evidence_shape(e), validate_evidence_shape(e)
    d=e['data']; c=d['sandbox_log_capture']; a=recover_evidence(e)['denials']
    assert a['capture']==c and a['diagnostics']==d['runner_sandbox_diagnostics']
    if c is None: assert a['candidates'] is None; continue
    assert a['window']==c['window'] and a['events']==c['deny_events']
    if c['capture_status']=='captured':
        check_live_capture(e,timeout_ms=c['supervision']['budget']['timeout_ms'],timeout_source=c['supervision']['budget']['timeout_source'])
        assert len(a['candidates'])==len(c['step_denies'])
        for got,want in zip(a['candidates'],c['step_denies']):
            assert got==dict(want,event=c['deny_events'][want['event_index']])
    else: assert a['candidates'] is None
"#])
            .arg(std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../tests/lib"))
            .stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped()).spawn().unwrap();
        child
            .stdin
            .take()
            .unwrap()
            .write_all(&serde_json::to_vec(envelopes).unwrap())
            .unwrap();
        let output = child.wait_with_output().unwrap();
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
    }

    #[test]
    fn supplied_text_survives_parser_receiver_association_and_consumer() {
        let plan: Vec<_> = [("early","open_read","/early"), ("late","open_read","/late"),
            ("a","open_write","/same"), ("b","open_write","/same"),
            ("silent","open_read","/silent"), ("op","open_read","/wrong-operation"),
            ("path","open_read","/wrong-path"), ("child","open_read","/child"),
            ("neighbour","open_read","/neighbour")].iter().map(|(id,action,path)|
                json!({"step_id":id,"attempt":{"kind":"file","action":action,"target":path}})).collect();
        let lines: Vec<_> = [
            "Sandbox: pw-probe-runner(42) deny(1) file-read-data /early",
            "Sandbox: pw-probe-runner(42) deny(1) file-read-data /late",
            "Sandbox: pw-probe-runner(42) deny(1) file-write-data /same",
            "Sandbox: pw-probe-runner(43) deny(1) file-read-data /child",
            "Sandbox: pw-probe-runner(420) deny(1) file-read-data /neighbour",
            "Sandbox: pw-probe-runner(42) deny(1) file-write-unlink /wrong-operation",
            "Sandbox: pw-probe-runner(42) deny(1) file-read-data /not-planned",
            "Sandbox: pw-probe-runner(42) deny(1) file-read-data /early",
        ]
        .iter()
        .map(|message| {
            format!("1970-01-01 00:00:02.000000+0000 localhost kernel[0]: (Sandbox) {message}")
        })
        .collect();
        let mut envelopes = Vec::new();
        let mut baseline = None;
        for (indices, expected) in [
            (
                vec![0, 1, 2, 3, 4, 5, 6, 7],
                vec![
                    (0, vec!["early"]),
                    (1, vec!["late"]),
                    (2, vec!["a", "b"]),
                    (7, vec!["early"]),
                ],
            ),
            (vec![0], vec![(0, vec!["early"])]),
            (vec![1], vec![(0, vec!["late"])]),
            (vec![], vec![]),
        ] {
            let supplied: Vec<_> = indices.iter().map(|&i| lines[i].clone()).collect();
            let wire = replay(&plan, &supplied, "complete", LogTimeout::default());
            let c = &wire["data"]["sandbox_log_capture"];
            assert_eq!(c["capture_status"], "captured");
            let events = c["deny_events"].as_array().unwrap();
            assert_eq!(events.len(), supplied.len());
            for (event, line) in events.iter().zip(&supplied) {
                assert_eq!(event["raw_line"], *line);
            }
            let associations = c["step_denies"].as_array().unwrap();
            assert_eq!(associations.len(), expected.len());
            for (association, (index, ids)) in associations.iter().zip(&expected) {
                assert_eq!(association["event_index"], *index);
                assert_eq!(association["candidate_step_ids"], json!(ids));
                assert_eq!(
                    association["association"],
                    if ids.len() == 1 {
                        "candidate"
                    } else {
                        "ambiguous"
                    }
                );
            }
            if let Some(before) = &baseline {
                assert_eq!(&execution_only(&wire), before);
            } else {
                baseline = Some(execution_only(&wire));
            }
            envelopes.push(wire);
        }
        for (fault, status) in [
            ("disabled", "disabled"),
            ("unavailable", "requested_unavailable"),
            ("wrong_window", "window_mismatch"),
            ("malformed", "parse_error"),
            ("outer_prefix", "timeout"),
            ("nonzero", "error"),
            ("inner_stdout", "overflow"),
            ("inner_stderr", "overflow"),
        ] {
            let timeout = if fault == "outer_prefix" {
                LogTimeout::parse("500").unwrap()
            } else {
                LogTimeout::default()
            };
            let wire = replay(&plan, &lines, fault, timeout);
            assert_eq!(execution_only(&wire), *baseline.as_ref().unwrap());
            let c = &wire["data"]["sandbox_log_capture"];
            let d = &wire["data"]["runner_sandbox_diagnostics"];
            assert_eq!(d["capture_status"], status, "{fault}");
            assert!(
                c["step_denies"].is_null()
                    && d["first_deny"].is_null()
                    && d["permission_failures_without_record"].is_null()
            );
            assert_eq!(
                d["correlation_status"],
                if fault == "disabled" {
                    "not_attempted"
                } else {
                    "unavailable"
                }
            );
            if ["wrong_window", "nonzero", "inner_stdout", "inner_stderr"].contains(&fault) {
                assert_eq!(c["deny_events"].as_array().unwrap().len(), lines.len());
                assert_eq!(c["observer"]["data"]["deny_events"], c["deny_events"]);
            }
            if fault == "outer_prefix" {
                assert!(c["observer"].is_null() && c["deny_events"].is_null());
                assert!(c["stdout_raw"].as_str().unwrap().starts_with('{'));
                assert!(c["stdout_parse_error"].is_string());
                assert_eq!(c["supervision"]["cutoff"]["reason"], "deadline");
                assert_eq!(c["supervision"]["cleanup"]["outcome"], "group_absent");
            }
            if fault.starts_with("inner_") {
                let cutoff = &c["observer"]["data"]["collection"]["cutoff"];
                let (stream, limit) = if fault == "inner_stdout" {
                    ("stdout", 1048576)
                } else {
                    ("stderr", 131072)
                };
                assert_eq!(cutoff["reason"], "output_overflow");
                assert_eq!(cutoff["stream"], stream);
                assert_eq!(cutoff["limit"], limit);
                assert_eq!(cutoff["observed"], limit + 1);
            }
            envelopes.push(wire);
        }
        consumers(&envelopes);
    }

    #[test]
    fn controlled_256_step_capture_keeps_every_long_target_candidate() {
        let paths: Vec<_> = (0..256)
            .map(|n| format!("/capacity/{n:03}/{}", "\u{1}".repeat(497)))
            .collect();
        assert!(paths.iter().all(|p| p.len() == 511));
        let plan: Vec<_> = paths
            .iter()
            .enumerate()
            .map(|(n, p)| {
                json!({"step_id":format!("{}{n:03}","s".repeat(60)),
            "attempt":{"kind":"file","action":"open_read","target":p}})
            })
            .collect();
        let lines: Vec<_> = paths
            .iter()
            .map(|p| format!("Sandbox: pw-probe-runner(42) deny(1) file-read-data {p}"))
            .collect();
        // The unoptimized all-path replay takes about ten seconds on the test
        // host. Give this capacity oracle a fixed 30-second test allowance;
        // production's default remains covered separately at 10 seconds.
        let wire = replay(
            &plan,
            &lines,
            "complete",
            LogTimeout::parse("30000").unwrap(),
        );
        let c = &wire["data"]["sandbox_log_capture"];
        assert_eq!(
            c["capture_status"], "captured",
            "outer={}, inner={}, processing={}",
            c["supervision"], c["observer"]["data"]["collection"], c["processing_cutoff"]
        );
        let events = c["deny_events"].as_array().unwrap();
        let associations = c["step_denies"].as_array().unwrap();
        assert_eq!(events.len(), 256);
        assert_eq!(associations.len(), 256);
        for n in 0..256 {
            assert_eq!(events[n]["raw_line"], lines[n]);
            assert_eq!(events[n]["path"], paths[n]);
            assert_eq!(associations[n]["event_index"], n);
            assert_eq!(
                associations[n]["candidate_step_ids"],
                json!([plan[n]["step_id"]])
            );
        }
        eprintln!(
            "controlled capacity: {} observer bytes; 256 retained 511-byte targets and candidates",
            c["stdout_bytes_received"]
        );
        consumers(&[wire]);
    }

    #[test]
    fn timeout_override_changes_waiting_only_across_both_boundaries() {
        let plan = vec![
            json!({"step_id":"early","attempt":{"kind":"file","action":"open_read","target":"/early"}}),
        ];
        let lines = vec!["Sandbox: pw-probe-runner(42) deny(1) file-read-data /early".into()];
        let mut baseline = None;
        for (fault, ms, expected) in [
            ("slow", 100, "timeout"),
            ("slow", 1500, "captured"),
            ("stalled", 1500, "timeout"),
        ] {
            let wire = replay(
                &plan,
                &lines,
                fault,
                LogTimeout::parse(&ms.to_string()).unwrap(),
            );
            if let Some(before) = &baseline {
                assert_eq!(&execution_only(&wire), before);
            } else {
                baseline = Some(execution_only(&wire));
            }
            let c = &wire["data"]["sandbox_log_capture"];
            assert_eq!(c["capture_status"], expected);
            assert_eq!(c["window"]["start"], "1969-12-31 23:59:59+0000");
            assert_eq!(c["window"]["end"], "1970-01-01 00:00:05+0000");
            assert_eq!(c["supervision"]["budget"]["timeout_ms"], ms);
            assert_eq!(c["supervision"]["budget"]["timeout_source"], "cli");
            assert_eq!(c["supervision"]["stdout"]["limit_bytes"], 33554432);
            assert_eq!(c["supervision"]["cleanup"]["grace_ms"], 1000);
            if expected == "captured" {
                assert_eq!(
                    c["observer"]["data"]["collection"]["budget"],
                    c["supervision"]["budget"]
                );
                assert_eq!(c["deny_events"].as_array().unwrap().len(), 1);
                assert_eq!(c["step_denies"][0]["candidate_step_ids"], json!(["early"]));
            } else {
                assert_eq!(c["supervision"]["cutoff"]["reason"], "deadline");
                assert!(c["step_denies"].is_null());
            }
        }
    }
}
