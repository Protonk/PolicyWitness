//! CLI contract integration tests for the controller binary.
//!
//! These tests run the built dist/PolicyWitness.app to validate the end-to-end
//! envelope shape. They are gated behind PW_INTEGRATION=1 so
//! `cargo test --tests` can run without a built app.

use std::env;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};

fn integration_enabled() -> bool {
    env::var("PW_INTEGRATION").ok().as_deref() == Some("1")
}

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("runner crate should live under repo root")
        .to_path_buf()
}

fn pw_bin_path() -> PathBuf {
    if let Ok(val) = env::var("PW_BIN_PATH") {
        // Allow CI or local runs to point at a non-standard build location.
        return PathBuf::from(val);
    }
    app_path()
        .join("Contents")
        .join("MacOS")
        .join("policy-witness")
}

fn app_path() -> PathBuf {
    env::var_os("PW_APP_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|| repo_root().join("dist/PolicyWitness.app"))
}

fn require_pw_bin() -> PathBuf {
    let path = pw_bin_path();
    if !path.exists() {
        // The integration suite assumes a built app bundle is available.
        panic!(
            "dist/PolicyWitness.app not found at {} (build the app or set PW_BIN_PATH)",
            path.display()
        );
    }
    path
}

fn sbpl_check_bin_path() -> PathBuf {
    app_path().join("Contents").join("MacOS").join("sbpl-check")
}

fn require_sbpl_check_bin() -> PathBuf {
    let path = sbpl_check_bin_path();
    if !path.exists() {
        panic!(
            "dist/PolicyWitness.app sbpl-check not found at {} (run `make build`)",
            path.display()
        );
    }
    path
}

fn run_pw(bin: &Path, args: &[&str]) -> Output {
    Command::new(bin)
        .args(args)
        .output()
        .unwrap_or_else(|err| panic!("failed to run {}: {err}", bin.display()))
}

#[test]
fn version_flag_reports_build_stamp_and_contract_versions() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();
    let out = run_pw(&bin, &["--version"]);
    assert!(
        out.status.success(),
        "--version failed: {:?}",
        out.status.code()
    );
    let envelope: serde_json::Value =
        serde_json::from_slice(&out.stdout).expect("parse version envelope");
    assert_eq!(envelope["kind"].as_str(), Some("version"));
    assert_eq!(envelope["result"]["ok"].as_bool(), Some(true));
    for key in ["version", "number", "describe", "commit"] {
        let value = envelope["build"][key].as_str().unwrap_or_default();
        assert!(
            !value.is_empty() && value != "unknown",
            "build.{key} = {value:?}"
        );
    }
    let manifest: serde_json::Value = serde_json::from_str(
        &std::fs::read_to_string(repo_root().join("docs/contract.json")).expect("read manifest"),
    )
    .expect("parse manifest");
    assert_eq!(envelope["data"]["contract"], manifest["versions"]);
}

#[test]
fn log_timeout_flag_and_disabled_capture_keep_execution_available() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();
    let request = repo_root().join("tests/fixtures/pw_runner/specimen_file_read_deny.json");
    for disabled in [false, true] {
        let mut args = vec!["run", request.to_str().unwrap(), "--log-timeout-ms", "1"];
        if disabled {
            args.push("--no-log-capture");
        }
        let out = run_pw(&bin, &args);
        assert!(
            out.status.success(),
            "{}",
            String::from_utf8_lossy(&out.stderr)
        );
        let envelope: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
        assert_eq!(
            envelope["data"]["runner_result"]["steps"][0]["sandbox_check"]["outcome"],
            "deny"
        );
        assert!(envelope["data"]["runner_result"]["steps"][0]["attempt"].is_object());
        let capture = &envelope["data"]["sandbox_log_capture"];
        if disabled {
            assert!(capture.is_null());
            assert_eq!(
                envelope["data"]["runner_sandbox_diagnostics"]["correlation_status"],
                "not_attempted"
            );
            assert!(
                envelope["data"]["runner_sandbox_diagnostics"]["permission_failures_without_record"]
                    .is_null()
            );
        } else {
            assert_eq!(capture["supervision"]["budget"]["timeout_ms"], 1);
            assert_eq!(capture["supervision"]["budget"]["timeout_source"], "cli");
            if capture["capture_status"] != "captured" {
                assert_eq!(
                    envelope["data"]["runner_sandbox_diagnostics"]["correlation_status"],
                    "unavailable"
                );
                assert!(capture["step_denies"].is_null());
            }
        }
    }
    for invalid in ["0", "-1", "unlimited", "18446744073709551615"] {
        let out = run_pw(
            &bin,
            &[
                "run",
                "/definitely-absent-specimen",
                "--no-log-capture",
                "--log-timeout-ms",
                invalid,
            ],
        );
        assert!(!out.status.success());
        let envelope: serde_json::Value =
            serde_json::from_slice(&out.stdout).expect("CLI admission error envelope");
        assert!(
            envelope["result"]["error"]
                .as_str()
                .unwrap()
                .contains("invalid value for --log-timeout-ms")
        );
        assert_eq!(envelope["result"]["exit_code"], 2);
        assert!(envelope["data"]["runner_result"].is_null());
        assert!(envelope["data"]["runner_client"].is_null());
        assert!(envelope["data"]["specimen"].is_object());
    }
}

#[test]
fn specimen_smoke_file_read_deny() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();

    // Sandboxed harnesses can block XPC lookup or unified log access; rerun from
    // a normal Terminal if failures look environment-related.

    let specimen = repo_root()
        .join("tests")
        .join("fixtures")
        .join("pw_runner")
        .join("specimen_file_read_deny.json");
    assert!(
        specimen.exists(),
        "missing specimen fixture: {}",
        specimen.display()
    );
    let out = run_pw(
        &bin,
        &["run", specimen.to_str().expect("specimen path utf8")],
    );

    assert!(
        out.status.success(),
        "specimen failed: rc={:?}\nstderr:\n{}\nstdout:\n{}",
        out.status.code(),
        String::from_utf8_lossy(&out.stderr),
        String::from_utf8_lossy(&out.stdout)
    );

    let stdout = String::from_utf8_lossy(&out.stdout);
    let envelope: serde_json::Value = serde_json::from_str(&stdout).expect("parse run envelope");
    assert_eq!(envelope.get("kind").and_then(|v| v.as_str()), Some("run"));
    assert_eq!(
        envelope
            .get("result")
            .and_then(|v| v.get("ok"))
            .and_then(|v| v.as_bool()),
        Some(true)
    );

    let runner = envelope
        .get("data")
        .and_then(|v| v.get("runner_result"))
        .cloned()
        .expect("missing data.runner_result");
    let steps = runner
        .get("steps")
        .and_then(|v| v.as_array())
        .cloned()
        .unwrap_or_default();
    assert_eq!(steps.len(), 1, "expected 1 step, got {}", steps.len());
    let step = &steps[0];
    let sb = step.get("sandbox_check").cloned().unwrap_or_default();
    assert_eq!(sb.get("outcome").and_then(|v| v.as_str()), Some("deny"));
}

static SBPL_CHECK_REQUESTS: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);

/// One `sbpl-check` invocation with `args`, optionally with `stdin` delivered
/// and closed before the output is collected.
fn run_sbpl_check(bin: &Path, args: &[&str], stdin: Option<&str>) -> Output {
    use std::io::Write;
    use std::process::Stdio;
    let mut child = Command::new(bin)
        .args(args)
        .stdin(if stdin.is_some() {
            Stdio::piped()
        } else {
            Stdio::null()
        })
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap_or_else(|err| panic!("failed to run {}: {err}", bin.display()));
    if let Some(input) = stdin {
        let mut pipe = child.stdin.take().expect("piped stdin");
        pipe.write_all(input.as_bytes()).expect("deliver request");
        drop(pipe);
    }
    child.wait_with_output().expect("collect sbpl-check output")
}

/// The request delivered as a file, or on stdin with `--request -`.
fn run_sbpl_check_request(bin: &Path, request: &str, via_stdin: bool) -> Output {
    if via_stdin {
        return run_sbpl_check(bin, &["--request", "-"], Some(request));
    }
    let serial = SBPL_CHECK_REQUESTS.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
    let tmp = std::env::temp_dir().join(format!(
        "pw-sbpl-check-{}-{serial}.json",
        std::process::id()
    ));
    std::fs::write(&tmp, request).expect("write sbpl-check request");
    let out = run_sbpl_check(
        bin,
        &["--request", tmp.to_str().expect("tmp path utf8")],
        None,
    );
    let _ = std::fs::remove_file(&tmp);
    out
}

const RETIRED_HELPER_FIELDS: [&str; 12] = [
    "params_referenced",
    "params_supplied",
    "params_missing",
    "params_unused",
    "params_scan_complete",
    "param_scan",
    "compiled",
    "compile_error",
    "imports",
    "imports_truncated",
    "imports_cycle",
    "policy_closure_sha256",
];

#[test]
fn sbpl_check_verdicts_follow_the_native_compiler() {
    if !integration_enabled() {
        return;
    }
    let bin = require_sbpl_check_bin();
    let path_param = "(version 1) (deny default) (allow file-read* (subpath (param \"ROOT\")))";
    let cases: Vec<(&str, &str, Option<serde_json::Value>, &str, i32)> = vec![
        (
            "plain success",
            "(version 1) (allow default)",
            None,
            "ok",
            0,
        ),
        (
            "unused definition",
            "(version 1) (allow default) (define unused (param \"OPTIONAL\"))",
            None,
            "ok",
            0,
        ),
        (
            "optional guard",
            "(version 1) (deny default) (if (param \"DEBUG\") (allow file-read* (subpath \"/tmp\")))",
            None,
            "ok",
            0,
        ),
        (
            "required path parameter absent",
            path_param,
            None,
            "compile_error",
            1,
        ),
        (
            "required path parameter supplied",
            path_param,
            Some(serde_json::json!({"ROOT": "/private/tmp"})),
            "ok",
            0,
        ),
        (
            "other compiler error beside missing name",
            "(version 1) (deny default) (allow bogus-op) (allow file-read* (subpath (param \"ROOT\")))",
            None,
            "compile_error",
            1,
        ),
        (
            "string composition needs a value",
            "(version 1) (deny default) (allow file-read* (subpath (string-append (param \"HOME\") \"/x\")))",
            None,
            "compile_error",
            1,
        ),
        (
            "nonliteral parameter name",
            "(version 1) (deny default) (define (h pn) (allow file-read* (subpath (param pn)))) (h \"FOO\")",
            None,
            "compile_error",
            1,
        ),
        (
            "supplied value unusable",
            path_param,
            Some(serde_json::json!({"ROOT": ""})),
            "compile_error",
            1,
        ),
        (
            "parameter text in a comment and an unused supplied value",
            "(version 1) (allow default)\n; (param \"GHOST\")",
            Some(serde_json::json!({"UNUSED": "value"})),
            "ok",
            0,
        ),
    ];
    for (index, (label, source, params, outcome, exit)) in cases.into_iter().enumerate() {
        let mut policy = serde_json::json!({"format": "sbpl", "sbpl_source": source});
        if let Some(params) = &params {
            policy["params"] = params.clone();
        }
        let request = serde_json::json!({"policy": policy, "probe_plan": []}).to_string();
        // Alternate file and stdin delivery across the table.
        let out = run_sbpl_check_request(&bin, &request, index % 2 == 1);
        let stdout = String::from_utf8_lossy(&out.stdout);
        let envelope: serde_json::Value = serde_json::from_str(&stdout).unwrap_or_else(|err| {
            panic!(
                "{label}: envelope did not parse ({err})\nstdout:\n{stdout}\nstderr:\n{}",
                String::from_utf8_lossy(&out.stderr)
            )
        });
        assert_eq!(out.status.code(), Some(exit), "{label}: {envelope}");
        assert_eq!(envelope["kind"], "sbpl_check", "{label}");
        assert_eq!(
            envelope["result"]["normalized_outcome"], outcome,
            "{label}: {envelope}"
        );
        assert_eq!(envelope["result"]["exit_code"], exit, "{label}");
        assert_eq!(envelope["result"]["ok"], exit == 0, "{label}");
        let data = envelope["data"]
            .as_object()
            .unwrap_or_else(|| panic!("{label}: data is not an object"));
        for field in RETIRED_HELPER_FIELDS {
            assert!(
                !data.contains_key(field),
                "{label}: retired field {field} present"
            );
        }
        assert_eq!(data["policy_format"], "sbpl", "{label}");
        assert_eq!(
            data["policy_sha256"].as_str().map(str::len),
            Some(64),
            "{label}"
        );
        assert_eq!(data["params_present"], params.is_some(), "{label}");
        assert_eq!(
            data["params_count"],
            params.as_ref().map_or(0, |p| p.as_object().unwrap().len()),
            "{label}"
        );
        assert_eq!(data["compile"]["stage"], "compile", "{label}: {envelope}");
        assert_eq!(data["compile"]["ok"], exit == 0, "{label}: {envelope}");
        let inventory = &data["import_inventory"];
        assert_eq!(inventory["records"], serde_json::json!([]), "{label}");
        assert_eq!(inventory["truncated"], false, "{label}");
        assert!(inventory["cycle"].is_null(), "{label}");
        assert_eq!(
            inventory["policy_closure_sha256"].as_str().map(str::len),
            Some(64),
            "{label}"
        );
        if exit == 0 {
            assert!(data["compile"]["error"].is_null(), "{label}: {envelope}");
            assert!(envelope["result"]["error"].is_null(), "{label}: {envelope}");
        } else {
            // The native diagnostic is present and identical in both fields;
            // its wording is the OS's and is not pinned here.
            let diagnostic = data["compile"]["error"]
                .as_str()
                .unwrap_or_else(|| panic!("{label}: no compiler diagnostic: {envelope}"));
            assert!(!diagnostic.is_empty(), "{label}");
            assert_eq!(envelope["result"]["error"], diagnostic, "{label}");
        }
    }
}

#[test]
fn sbpl_check_argument_and_request_failures_exit_2_without_an_envelope() {
    if !integration_enabled() {
        return;
    }
    let bin = require_sbpl_check_bin();
    let dir = std::env::temp_dir().join(format!("pw-sbpl-check-exit2-{}", std::process::id()));
    std::fs::create_dir_all(&dir).unwrap();
    let malformed = dir.join("malformed.json");
    std::fs::write(&malformed, "{not json").unwrap();
    let absent = dir.join("absent").join("request.json");
    let cases: Vec<(&str, Vec<&str>, Option<&str>)> = vec![
        ("no arguments", vec![], None),
        ("unknown argument", vec!["--bogus"], None),
        ("missing --request value", vec!["--request"], None),
        (
            "unreadable request path",
            vec!["--request", absent.to_str().unwrap()],
            None,
        ),
        (
            "malformed request file",
            vec!["--request", malformed.to_str().unwrap()],
            None,
        ),
        (
            "malformed request on stdin",
            vec!["--request", "-"],
            Some("{not json"),
        ),
        (
            "request without a policy on stdin",
            vec!["--request", "-"],
            Some("{\"probe_plan\": []}"),
        ),
    ];
    for (label, args, stdin) in cases {
        let out = run_sbpl_check(&bin, &args, stdin);
        assert_eq!(out.status.code(), Some(2), "{label}");
        assert!(out.stdout.is_empty(), "{label}: no JSON envelope on stdout");
        assert!(!out.stderr.is_empty(), "{label}: a message on stderr");
    }
    let _ = std::fs::remove_dir_all(&dir);
}

#[test]
fn sandbox_check_emits_path_diagnostics_for_etc_hosts() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();

    let specimen = repo_root()
        .join("tests")
        .join("fixtures")
        .join("pw_runner")
        .join("specimen_file_read_deny.json");
    assert!(
        specimen.exists(),
        "missing specimen fixture: {}",
        specimen.display()
    );

    let out = run_pw(
        &bin,
        &["run", specimen.to_str().expect("specimen path utf8")],
    );
    assert!(
        out.status.success(),
        "specimen failed: rc={:?}\nstderr:\n{}\nstdout:\n{}",
        out.status.code(),
        String::from_utf8_lossy(&out.stderr),
        String::from_utf8_lossy(&out.stdout)
    );

    let stdout = String::from_utf8_lossy(&out.stdout);
    let envelope: serde_json::Value = serde_json::from_str(&stdout).expect("parse run envelope");

    let runner = envelope
        .get("data")
        .and_then(|v| v.get("runner_result"))
        .cloned()
        .expect("missing data.runner_result");
    let steps = runner
        .get("steps")
        .and_then(|v| v.as_array())
        .cloned()
        .unwrap_or_default();
    assert_eq!(steps.len(), 1, "expected 1 step, got {}", steps.len());

    let sb = steps[0]
        .get("sandbox_check")
        .cloned()
        .expect("missing sandbox_check on step");
    let diag = sb
        .get("path_diagnostics")
        .cloned()
        .expect("missing path_diagnostics on path-filter sandbox_check");

    assert_eq!(
        diag.get("input").and_then(|v| v.as_str()),
        Some("/etc/hosts")
    );
    // Both forms differ from the input here, so both are present as strings
    // and nothing is listed as equal to the input.
    assert_eq!(diag.get("same_as_input"), Some(&serde_json::json!([])));
    assert_eq!(
        diag.get("realpath_resolved").and_then(|v| v.as_str()),
        Some("/private/etc/hosts"),
        "realpath should fold the /etc symlink"
    );
    // /private is firmlinked to /System/Volumes/Data/private on a stock macOS
    // install; if this assertion ever fails, /usr/share/firmlinks changed
    // shape and the firmlink parser needs re-verification.
    assert_eq!(
        diag.get("firmlink_resolved").and_then(|v| v.as_str()),
        Some("/System/Volumes/Data/private/etc/hosts"),
        "firmlink resolution should land on the Data volume"
    );
    assert!(
        diag.get("data_volume_form").is_none(),
        "data_volume_form was retired with response 9"
    );
}

#[test]
fn sandbox_check_path_diagnostics_lists_forms_equal_to_input() {
    // A canonical path resolves to itself: the equal form is named in
    // same_as_input and its key is omitted, so the path is carried once.
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();
    let dir = std::env::temp_dir().join(format!("pw-same-as-input-{}", std::process::id()));
    let target = std::path::Path::new("/private/tmp")
        .join(dir.file_name().unwrap())
        .join("target");
    std::fs::create_dir_all(target.parent().unwrap()).unwrap();
    std::fs::write(&target, b"x").unwrap();
    let specimen = dir.join("specimen.json");
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::write(
        &specimen,
        serde_json::json!({
            "schema_version": 4, "specimen_id": "same-as-input",
            "policy": {"format": "sbpl", "sbpl_source": "(version 1)(allow default)"},
            "probe_plan": [{"step_id": "s",
                "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": target}},
                "attempt": {"kind": "file", "action": "open_read", "target": target}}]
        })
        .to_string(),
    )
    .unwrap();
    let out = run_pw(
        &bin,
        &["run", specimen.to_str().unwrap(), "--no-log-capture"],
    );
    assert!(out.status.success(), "specimen failed");
    let envelope: serde_json::Value =
        serde_json::from_str(&String::from_utf8_lossy(&out.stdout)).expect("parse run envelope");
    let sb = envelope
        .pointer("/data/runner_result/steps/0/sandbox_check")
        .cloned()
        .expect("missing sandbox_check");
    assert!(
        sb.get("effective_filter_value").is_none(),
        "effective_filter_value was retired with response 9"
    );
    let diag = sb
        .get("path_diagnostics")
        .and_then(|v| v.as_object())
        .cloned()
        .expect("missing path_diagnostics");
    assert_eq!(diag.get("input").and_then(|v| v.as_str()), target.to_str());
    assert_eq!(
        diag.get("same_as_input"),
        Some(&serde_json::json!(["realpath_resolved"]))
    );
    assert!(
        !diag.contains_key("realpath_resolved"),
        "a form equal to the input must not repeat it: {diag:?}"
    );
    assert_eq!(
        diag.get("firmlink_resolved").and_then(|v| v.as_str()),
        Some(format!("/System/Volumes/Data{}", target.display()).as_str())
    );
    let _ = std::fs::remove_dir_all(&dir);
    let _ = std::fs::remove_dir_all(target.parent().unwrap());
}

#[test]
fn path_diagnostics_preserves_native_unicode_spelling() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();
    let dir = std::path::Path::new("/private/tmp")
        .join(format!("pw-unicode-path-{}", std::process::id()));
    std::fs::create_dir_all(&dir).unwrap();
    let observed = dir.join("cafe\u{301}");
    let submitted = dir.join("caf\u{e9}");
    std::fs::write(&observed, b"unicode path witness").unwrap();
    // Independent native realpath observation on the same file. This requires
    // the normalization-insensitive filesystem used by the supported macOS host.
    let native = std::fs::canonicalize(&submitted).unwrap();
    assert_ne!(native.as_os_str(), submitted.as_os_str());
    let request = dir.join("specimen.json");
    std::fs::write(
        &request,
        serde_json::json!({
            "schema_version": 4, "specimen_id": "unicode-path",
            "policy": {"format": "sbpl", "sbpl_source": "(version 1)(allow default)"},
            "probe_plan": [{"step_id": "unicode", "sandbox_check": {
                "operation": "file-read-data", "filter": {"kind": "path", "value": submitted}},
                "attempt": {"kind": "file", "action": "open_read", "target": submitted}}]
        })
        .to_string(),
    )
    .unwrap();
    let output = run_pw(
        &bin,
        &["run", request.to_str().unwrap(), "--no-log-capture"],
    );
    assert!(output.status.success());
    let envelope: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    let step = &envelope["data"]["runner_result"]["steps"][0];
    assert_eq!(step["attempt"]["outcome"], "ok");
    let path = &step["sandbox_check"]["path_diagnostics"];
    assert_eq!(
        path["input"].as_str().unwrap().as_bytes(),
        submitted.to_str().unwrap().as_bytes()
    );
    assert_eq!(
        path["realpath_resolved"].as_str().unwrap().as_bytes(),
        native.to_str().unwrap().as_bytes()
    );
    assert_eq!(path["same_as_input"], serde_json::json!([]));
    std::fs::remove_dir_all(&dir).unwrap();
}

#[test]
fn sandbox_check_path_diagnostics_survives_strict_sandbox() {
    // Under `(deny default)` the worker can't stat /etc/hosts.
    // path_diagnostics is computed by the unsandboxed host (so
    // realpath_resolved is reliably populated), but the derived
    // forms must be present and correct regardless — that is the
    // load-bearing assertion this test pins.
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();

    let specimen = repo_root()
        .join("tests")
        .join("fixtures")
        .join("pw_runner")
        .join("specimen_path_diagnostics_strict.json");
    assert!(
        specimen.exists(),
        "missing specimen fixture: {}",
        specimen.display()
    );

    let out = run_pw(
        &bin,
        &["run", specimen.to_str().expect("specimen path utf8")],
    );
    assert!(
        out.status.success(),
        "specimen failed: rc={:?}\nstderr:\n{}\nstdout:\n{}",
        out.status.code(),
        String::from_utf8_lossy(&out.stderr),
        String::from_utf8_lossy(&out.stdout)
    );

    let stdout = String::from_utf8_lossy(&out.stdout);
    let envelope: serde_json::Value = serde_json::from_str(&stdout).expect("parse run envelope");
    let sb = envelope
        .get("data")
        .and_then(|v| v.get("runner_result"))
        .and_then(|v| v.get("steps"))
        .and_then(|v| v.as_array())
        .and_then(|steps| steps.first().cloned())
        .and_then(|s| s.get("sandbox_check").cloned())
        .expect("missing sandbox_check on first step");

    let diag = sb
        .get("path_diagnostics")
        .and_then(|v| v.as_object())
        .cloned()
        .expect("missing path_diagnostics on path-filter check");

    // Every form is in exactly one state: named in same_as_input, present as a
    // string, or present as an explicit null. A missing key that is not listed
    // would leave a consumer unable to tell "unavailable" from "not emitted".
    let same: Vec<&str> = diag
        .get("same_as_input")
        .and_then(|v| v.as_array())
        .expect("same_as_input must be a list")
        .iter()
        .filter_map(|v| v.as_str())
        .collect();
    for key in ["realpath_resolved", "firmlink_resolved"] {
        assert!(
            same.contains(&key) != diag.contains_key(key),
            "path_diagnostics form {key:?} must be either listed as equal or carried; got {diag:?}"
        );
    }
    assert!(
        !diag.contains_key("data_volume_form"),
        "data_volume_form was retired with response 9"
    );

    assert_eq!(
        diag.get("input").and_then(|v| v.as_str()),
        Some("/etc/hosts")
    );
    // Whether realpath_resolved is populated is sandbox-dependent and not the
    // load-bearing assertion here — the derived form must be present.
    assert_eq!(
        diag.get("firmlink_resolved").and_then(|v| v.as_str()),
        Some("/System/Volumes/Data/private/etc/hosts"),
        "firmlink_resolved must be derivable from the well-known symlink \
         substitution even when realpath(3) is blocked by the sandbox \
         (firmlinks map is warmed pre-sandbox and has a built-in fallback)"
    );
}

#[test]
fn sandbox_check_path_diagnostics_host_produces_realpath_under_strict_sandbox() {
    // path_diagnostics is computed by the unsandboxed runner host
    // (PWRunnerService.enrichPathDiagnostics) after the worker
    // reports back. The host's realpath(3) is NOT blocked by the
    // worker's (deny default) policy, so realpath_resolved is
    // populated even when the worker itself couldn't stat the path.
    //
    // This is the positive assertion the survives_strict_sandbox
    // test deliberately avoided: a regression that moves
    // path_diagnostics computation back into the worker (or
    // otherwise prevents host realpath from running) silently breaks
    // the host-producer contract without breaking the shape-only
    // assertions above. This test catches that.
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();

    let specimen = repo_root()
        .join("tests")
        .join("fixtures")
        .join("pw_runner")
        .join("specimen_path_diagnostics_strict.json");
    assert!(
        specimen.exists(),
        "missing specimen fixture: {}",
        specimen.display()
    );

    let out = run_pw(
        &bin,
        &["run", specimen.to_str().expect("specimen path utf8")],
    );
    assert!(out.status.success(), "specimen failed");

    let envelope: serde_json::Value =
        serde_json::from_str(&String::from_utf8_lossy(&out.stdout)).expect("parse run envelope");

    let realpath = envelope
        .pointer("/data/runner_result/steps/0/sandbox_check/path_diagnostics/realpath_resolved")
        .and_then(|v| v.as_str())
        .unwrap_or_else(|| {
            panic!(
                "expected realpath_resolved to be a populated string under \
             (deny default) — the host should compute it without the \
             worker's sandbox restriction. Did path_diagnostics move \
             back into the worker?"
            )
        });

    // /etc/hosts resolves to /private/etc/hosts on every shipped macOS
    // since the /etc symlink is canonical. If the host's realpath
    // returned anything else, something has changed about the system
    // that we want to know about.
    assert_eq!(
        realpath, "/private/etc/hosts",
        "host-produced realpath_resolved for /etc/hosts should be \
         /private/etc/hosts on macOS (got {realpath:?})"
    );
}

#[test]
fn augment_applied_records_the_applied_augmentation() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();

    // exec_baseline ships as three (allow ...) rules in checkpoint 4.
    // Splicing it into a permissive policy must succeed end-to-end and
    // record distinct original/applied
    // hashes; the hash difference proves the controller actually
    // appended bytes regardless of what those bytes grant.
    let tmp = std::env::temp_dir().join(format!("pw-augment-applied-{}.json", std::process::id()));
    let request = r#"{
        "schema_version": 4,
        "specimen_id": "augment_applied",
        "policy": {
            "format": "sbpl",
            "sbpl_source": "(version 1)\n(allow default)\n",
            "augments": ["exec_baseline"]
        },
        "probe_plan": []
    }"#;
    std::fs::write(&tmp, request).expect("write augment request");

    let out = run_pw(&bin, &["run", tmp.to_str().expect("tmp path utf8")]);
    let _ = std::fs::remove_file(&tmp);

    // The augmented run must succeed end-to-end. Asserting on exit
    // status + normalized_outcome catches regressions that preserve
    // the augmentation record but break the sbpl-check compile or the
    // runner — e.g. a future bug that forwards the augments key past
    // controller resolution would cause the runner to reject the
    // spec, and we'd still see the augmentation record in the envelope.
    assert!(
        out.status.success(),
        "augmented run failed: rc={:?}\nstderr:\n{}\nstdout:\n{}",
        out.status.code(),
        String::from_utf8_lossy(&out.stderr),
        String::from_utf8_lossy(&out.stdout)
    );
    let stdout = String::from_utf8_lossy(&out.stdout);
    let envelope: serde_json::Value = serde_json::from_str(&stdout).expect("parse run envelope");
    assert_eq!(
        envelope
            .pointer("/result/normalized_outcome")
            .and_then(|v| v.as_str()),
        Some("ok"),
        "augmented run did not reach ok: envelope={envelope}"
    );

    let aug = envelope
        .pointer("/data/specimen/policy/augmentation")
        .cloned()
        .expect("data.specimen.policy.augmentation missing on augmented run");
    assert_eq!(aug["status"], "applied");
    assert!(aug["error"].is_null());
    let applied: Vec<String> = aug
        .get("applied")
        .and_then(|v| v.as_array())
        .map(|arr| {
            arr.iter()
                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                .collect()
        })
        .unwrap_or_default();
    assert_eq!(applied, vec!["exec_baseline".to_string()]);

    let original = aug
        .get("original_sha256")
        .and_then(|v| v.as_str())
        .expect("original_sha256 missing");
    let applied_hash = aug
        .get("applied_sha256")
        .and_then(|v| v.as_str())
        .expect("applied_sha256 missing");
    assert_ne!(
        original, applied_hash,
        "splicing a non-empty augment must change the policy hash"
    );
    assert_eq!(original.len(), 64);
    assert_eq!(applied_hash.len(), 64);

    // The runner must have run against the spliced source. Hard
    // assertion catches a regression that forwards the original
    // request to the runner while still recording the augmentation.
    // This is the load-bearing splice invariant now that the sbpl-check compile no
    // longer runs on the happy path (the worker is the sole compiler):
    // `policy_check` is null on a successful run, so the runner's
    // own `policy_sha256` is what proves the spliced bytes reached the
    // compiler.
    let runner_sha = envelope
        .pointer("/data/runner_result/policy_sha256")
        .and_then(|v| v.as_str())
        .expect("data.runner_result.policy_sha256 missing — runner may not have been invoked");
    assert_eq!(
        runner_sha, applied_hash,
        "runner_result.policy_sha256 must equal applied_sha256 when augments are spliced"
    );

    // The sbpl-check compile does not run on a healthy run — it is reserved for the
    // xpc_error disambiguation path — so the field is null here.
    assert!(
        envelope
            .pointer("/data/policy_check")
            .map_or(true, |v| v.is_null()),
        "policy_check must be null on a successful run (sbpl-check is xpc_error-only): {envelope}"
    );
}

#[test]
fn unknown_augment_short_circuits_to_bad_request() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();

    let tmp = std::env::temp_dir().join(format!("pw-augment-unknown-{}.json", std::process::id()));
    let request = r#"{
        "schema_version": 4,
        "specimen_id": "augment_unknown",
        "policy": {
            "format": "sbpl",
            "sbpl_source": "(version 1)\n(allow default)\n",
            "augments": ["this_augment_definitely_does_not_exist_42"]
        },
        "probe_plan": []
    }"#;
    std::fs::write(&tmp, request).expect("write augment request");

    let out = run_pw(&bin, &["run", tmp.to_str().expect("tmp path utf8")]);
    let _ = std::fs::remove_file(&tmp);

    assert_eq!(
        out.status.code(),
        Some(1),
        "expected exit code 1 (bad augment); stderr:\n{}\nstdout:\n{}",
        String::from_utf8_lossy(&out.stderr),
        String::from_utf8_lossy(&out.stdout)
    );

    let envelope: serde_json::Value =
        serde_json::from_str(&String::from_utf8_lossy(&out.stdout)).expect("parse run envelope");
    assert_eq!(
        envelope
            .pointer("/result/normalized_outcome")
            .and_then(|v| v.as_str()),
        Some("bad_request")
    );
    let error = envelope
        .pointer("/result/error")
        .and_then(|v| v.as_str())
        .unwrap_or("");
    assert!(
        error.contains("this_augment_definitely_does_not_exist_42"),
        "result.error should name the bad augment (got {error:?})"
    );

    // Runner must NOT have been invoked. data.runner_result and
    // data.runner_client are null; the dossier records the refusal.
    assert!(
        envelope
            .pointer("/data/runner_result")
            .map(|v| v.is_null())
            .unwrap_or(true),
        "data.runner_result must be absent/null when augment resolution fails"
    );
    assert!(
        envelope
            .pointer("/data/runner_client")
            .map_or(true, |v| v.is_null()),
        "data.runner_client must be null when the runner is not invoked"
    );

    // The augmentation record reports the refusal: no applied names, no
    // applied hash, the original hash and the diagnostic; the import scan
    // did not run.
    let aug = envelope
        .pointer("/data/specimen/policy/augmentation")
        .cloned()
        .expect("data.specimen.policy.augmentation missing on a refused run");
    assert_eq!(aug["status"], "failed");
    assert_eq!(aug["applied"], serde_json::json!([]));
    assert_eq!(aug["original_sha256"].as_str().map(str::len), Some(64));
    assert!(aug["applied_sha256"].is_null());
    assert!(
        aug["error"]
            .as_str()
            .is_some_and(|e| e.contains("this_augment_definitely_does_not_exist_42")),
        "augmentation.error should name the bad augment (got {aug})"
    );
    let imports = &envelope["data"]["specimen"]["policy"]["imports"];
    assert_eq!(imports["status"], "not_applicable");
    assert_eq!(imports["failure"], "augmentation_failed");
    assert_eq!(imports["records"], serde_json::json!([]));
}

#[test]
fn invalid_augment_name_rejected_as_bad_request() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();

    let tmp = std::env::temp_dir().join(format!("pw-augment-invalid-{}.json", std::process::id()));
    // "../etc/passwd" is the canonical traversal attempt; the resolver
    // must reject it for shape, not for whether the file exists.
    let request = r#"{
        "schema_version": 4,
        "specimen_id": "augment_invalid",
        "policy": {
            "format": "sbpl",
            "sbpl_source": "(version 1)\n(allow default)\n",
            "augments": ["../etc/passwd"]
        },
        "probe_plan": []
    }"#;
    std::fs::write(&tmp, request).expect("write augment request");

    let out = run_pw(&bin, &["run", tmp.to_str().expect("tmp path utf8")]);
    let _ = std::fs::remove_file(&tmp);

    assert_eq!(out.status.code(), Some(1));
    let envelope: serde_json::Value =
        serde_json::from_str(&String::from_utf8_lossy(&out.stdout)).expect("parse run envelope");
    assert_eq!(
        envelope
            .pointer("/result/normalized_outcome")
            .and_then(|v| v.as_str()),
        Some("bad_request")
    );
}

#[test]
fn absent_augments_record_not_requested() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();

    let specimen = repo_root()
        .join("tests")
        .join("fixtures")
        .join("pw_runner")
        .join("specimen_file_read_deny.json");
    let out = run_pw(&bin, &["run", specimen.to_str().expect("specimen utf8")]);
    let envelope: serde_json::Value =
        serde_json::from_str(&String::from_utf8_lossy(&out.stdout)).expect("parse run envelope");
    let aug = envelope
        .pointer("/data/specimen/policy/augmentation")
        .cloned()
        .expect("data.specimen.policy.augmentation missing");
    assert_eq!(
        aug["status"], "not_requested",
        "a request without augments records not_requested (got {aug})"
    );
    assert_eq!(aug["applied"], serde_json::json!([]));
    assert!(aug["error"].is_null());
    assert_eq!(aug["original_sha256"].as_str().map(str::len), Some(64));
    assert_eq!(aug["original_sha256"], aug["applied_sha256"]);
    assert_eq!(
        envelope.pointer("/data/runner_result/policy_sha256"),
        Some(&aug["applied_sha256"]),
        "the reply's policy hash is the applied hash on a completed run"
    );
}

#[test]
fn sbpl_check_records_import_provenance_for_system_sb() {
    if !integration_enabled() {
        return;
    }
    let bin = require_sbpl_check_bin();

    let tmp =
        std::env::temp_dir().join(format!("pw-sbpl-check-imports-{}.json", std::process::id()));
    let request = r#"{
        "policy": {
            "format": "sbpl",
            "sbpl_source": "(version 1)\n(deny default)\n(import \"system.sb\")\n(allow file-read-data)\n"
        },
        "probe_plan": []
    }"#;
    std::fs::write(&tmp, request).expect("write sbpl-check request");

    let out = run_pw(&bin, &["--request", tmp.to_str().expect("tmp path utf8")]);
    let _ = std::fs::remove_file(&tmp);

    assert_eq!(
        out.status.code(),
        Some(0),
        "expected exit code 0 (compile ok); got {:?}\nstderr:\n{}",
        out.status.code(),
        String::from_utf8_lossy(&out.stderr)
    );

    let stdout = String::from_utf8_lossy(&out.stdout);
    let envelope: serde_json::Value =
        serde_json::from_str(&stdout).expect("parse sbpl-check envelope");

    let data = envelope.get("data").expect("missing data block");
    let policy_sha = data
        .get("policy_sha256")
        .and_then(|v| v.as_str())
        .expect("policy_sha256 missing");
    let inventory = data
        .get("import_inventory")
        .and_then(|v| v.as_object())
        .expect("import_inventory missing");
    let closure_sha = inventory
        .get("policy_closure_sha256")
        .and_then(|v| v.as_str())
        .expect("import_inventory.policy_closure_sha256 missing");
    assert_ne!(
        policy_sha, closure_sha,
        "closure hash should differ from policy_sha256 when imports were resolved"
    );

    let build = data
        .get("macos_build_version")
        .and_then(|v| v.as_str())
        .unwrap_or("");
    assert!(
        !build.is_empty(),
        "macos_build_version should be populated (got {build:?})"
    );

    assert_eq!(inventory.get("truncated"), Some(&serde_json::json!(false)));
    assert_eq!(inventory.get("cycle"), Some(&serde_json::Value::Null));
    assert_eq!(
        data.get("compile"),
        Some(&serde_json::json!({"stage": "compile", "ok": true, "error": null}))
    );
    let imports = inventory
        .get("records")
        .and_then(|v| v.as_array())
        .expect("import_inventory.records missing");
    assert!(
        imports.len() >= 1,
        "expected at least one resolved import, got {}",
        imports.len()
    );

    let system_sb = imports
        .iter()
        .find(|imp| imp.get("name").and_then(|v| v.as_str()) == Some("system.sb"))
        .expect("system.sb should be in import_inventory.records");
    assert_eq!(
        system_sb.get("resolved_path").and_then(|v| v.as_str()),
        Some("/System/Library/Sandbox/Profiles/system.sb"),
        "system.sb should resolve from the Profiles directory"
    );
    let sha = system_sb
        .get("sha256")
        .and_then(|v| v.as_str())
        .unwrap_or("");
    assert_eq!(sha.len(), 64, "sha256 should be a 64-char hex string");
}
