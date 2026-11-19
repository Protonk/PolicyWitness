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

fn candidate_contract() -> String {
    let output = Command::new("/usr/bin/plutil")
        .args([
            "-extract",
            "PWContract",
            "raw",
            "-expect",
            "string",
            "-o",
            "-",
        ])
        .arg(app_path().join("Contents/Info.plist"))
        .output()
        .expect("inspect candidate plist");
    assert!(output.status.success(), "candidate plist contract missing");
    let value = String::from_utf8(output.stdout).expect("UTF-8 contract");
    let value = value.strip_suffix('\n').unwrap_or(&value).to_owned();
    assert!(!value.is_empty() && value != "unbound");
    value
}

fn run_pw(bin: &Path, args: &[&str]) -> Output {
    let mut args: Vec<String> = args.iter().map(|value| (*value).into()).collect();
    let mut submitted = None;
    if args.first().map(String::as_str) == Some("run")
        && args.len() > 1
        && Path::new(&args[1]).starts_with(repo_root().join("tests/fixtures"))
    {
        let mut value: serde_json::Value =
            serde_json::from_slice(&std::fs::read(&args[1]).unwrap()).unwrap();
        assert!(value.get("contract").is_none() && value.get("schema_version").is_none());
        value["contract"] = candidate_contract().into();
        static NEXT: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
        let file = env::temp_dir().join(format!(
            "pw-contract-request-{}-{}.json",
            std::process::id(),
            NEXT.fetch_add(1, std::sync::atomic::Ordering::Relaxed)
        ));
        use std::io::Write;
        std::fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&file)
            .unwrap()
            .write_all(&serde_json::to_vec(&value).unwrap())
            .unwrap();
        args[1] = file.to_string_lossy().into_owned();
        submitted = Some(file);
    }
    let output = Command::new(bin)
        .args(args)
        .output()
        .unwrap_or_else(|err| panic!("failed to run {}: {err}", bin.display()));
    if let Some(file) = submitted {
        std::fs::remove_file(file).unwrap();
    }
    output
}

#[test]
fn plain_cargo_build_cannot_admit_public_requests() {
    if !integration_enabled() {
        return;
    }
    let bin = Path::new(env!("CARGO_BIN_EXE_policy-witness"));
    let version = run_pw(bin, &["--version"]);
    let envelope: serde_json::Value = serde_json::from_slice(&version.stdout).unwrap();
    assert_eq!(envelope["build"]["contract"], "unbound");
    let request = env::temp_dir().join(format!("pw-unbound-{}.json", std::process::id()));
    std::fs::write(&request, br#"{"contract":"unbound","runner":false}"#).unwrap();
    let output = run_pw(bin, &["run", request.to_str().unwrap()]);
    std::fs::remove_file(request).unwrap();
    let envelope: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(output.status.code(), Some(1));
    assert_eq!(
        envelope["data"]["request_failure"]["code"],
        "unsupported_contract"
    );
    assert_eq!(
        envelope["data"]["request_failure"]["expected_contract"],
        "unbound"
    );
    assert!(envelope["data"]["runner_client"].is_null());
}

#[test]
fn version_dispatch_uses_the_first_argument() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();
    let reference = run_pw(&bin, &["--version"]);
    assert_eq!(reference.status.code(), Some(0));
    let expected: serde_json::Value = serde_json::from_slice(&reference.stdout).unwrap();
    let output = run_pw(&bin, &["version"]);
    assert_eq!(output.status.code(), Some(0));
    assert!(output.stderr.is_empty());
    let value: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    // Per-invocation timestamps belong to the envelope header; compare the
    // identity, result and version data rather than those fresh observations.
    for field in ["kind", "build", "result", "data"] {
        assert_eq!(value[field], expected[field], "version: {field}");
    }
    // The first argument alone selects the command, and it takes no other:
    // an argument after it is refused before anything it names is read.
    for args in [
        vec!["version", "unrecognized"],
        vec!["--version", "run", "/a/request/that/does/not/exist"],
        vec!["--version", "--invalid"],
    ] {
        let output = run_pw(&bin, &args);
        assert_eq!(output.status.code(), Some(2), "{args:?}");
        assert!(output.stdout.is_empty(), "{args:?}");
        assert_eq!(
            String::from_utf8(output.stderr).unwrap(),
            format!("policy-witness {}: accepts no arguments\n", args[0]),
            "{args:?}"
        );
    }
}

#[test]
fn supplied_direct_cargo_identity_is_embedded_without_release_provenance() {
    use sha2::Digest;

    if !integration_enabled() {
        return;
    }
    let artifacts = PathBuf::from(env::var_os("PW_TEST_ARTIFACTS").expect("dispatcher artifacts"))
        .join("direct-cargo-contract");
    let target = PathBuf::from(env::var_os("PW_TEST_SCRATCH").expect("dispatcher scratch"))
        .join("direct-cargo-contract");
    std::fs::create_dir(&artifacts).unwrap();
    std::fs::create_dir_all(target.parent().unwrap()).unwrap();
    std::fs::create_dir(&target).unwrap();
    let manifest = repo_root().join("controller/Cargo.toml");
    let binary = target.join("aarch64-apple-darwin/debug/policy-witness");
    let stamp_keys = [
        "PW_BUILD_CONTRACT",
        "PW_BUILD_VERSION",
        "PW_BUILD_NUMBER",
        "PW_BUILD_DESCRIBE",
        "PW_BUILD_COMMIT",
    ];
    let mut observations = Vec::new();
    // Reuse only this fresh target directory: each changed environment must
    // rebuild the non-test binary rather than answer with the previous value.
    for (label, supplied, expected) in [
        (
            "foreign",
            Some("test:direct-cargo-foreign"),
            "test:direct-cargo-foreign",
        ),
        ("release_form", Some("release:v9.9.9"), "release:v9.9.9"),
        ("empty", Some(""), "unbound"),
        ("absent", None, "unbound"),
    ] {
        let directory = artifacts.join(label);
        std::fs::create_dir(&directory).unwrap();
        let mut build = Command::new("cargo");
        build
            .args([
                "build",
                "--locked",
                "--offline",
                "--bin",
                "policy-witness",
                "--target",
                "aarch64-apple-darwin",
                "--target-dir",
            ])
            .arg(&target)
            .arg("--manifest-path")
            .arg(&manifest);
        for key in stamp_keys {
            build.env_remove(key);
        }
        if let Some(value) = supplied {
            build.env("PW_BUILD_CONTRACT", value);
        }
        std::fs::write(directory.join("build-command.txt"), format!("{build:?}\n")).unwrap();
        let built = build.output().expect("direct Cargo build");
        std::fs::write(directory.join("build.stdout"), &built.stdout).unwrap();
        std::fs::write(directory.join("build.stderr"), &built.stderr).unwrap();
        assert!(
            built.status.success(),
            "{label}: see {}",
            directory.display()
        );

        let bytes = std::fs::read(&binary).unwrap();
        let binary_hash = format!("{:x}", sha2::Sha256::digest(&bytes));
        std::fs::write(
            directory.join("binary.json"),
            serde_json::to_vec_pretty(
                &serde_json::json!({"path": binary, "bytes": bytes.len(), "sha256": binary_hash}),
            )
            .unwrap(),
        )
        .unwrap();
        let version = run_pw(&binary, &["--version"]);
        std::fs::write(directory.join("version.json"), &version.stdout).unwrap();
        std::fs::write(directory.join("version.stderr"), &version.stderr).unwrap();
        assert!(version.status.success(), "{label}: version failed");
        let value: serde_json::Value = serde_json::from_slice(&version.stdout).unwrap();
        assert_eq!(value["build"]["contract"], expected, "{label}");
        assert_eq!(value["data"]["contract"], expected, "{label}");
        for key in ["version", "number", "describe", "commit"] {
            assert_eq!(value["build"][key], "unknown", "{label}: provenance {key}");
        }

        // A matching bound assertion reaches selector admission; a mismatch,
        // empty binding or unbound producer stops at identity admission. No
        // app, host or worker is needed to observe either controller boundary.
        for (entry, asserted) in [("matching", expected), ("mismatch", "test:other")] {
            let request = directory.join(format!("{entry}.request.json"));
            let bytes = serde_json::to_vec(&serde_json::json!({
                "contract": asserted, "runner": false,
            }))
            .unwrap();
            std::fs::write(&request, &bytes).unwrap();
            let result = run_pw(&binary, &["run", request.to_str().unwrap()]);
            std::fs::write(directory.join(format!("{entry}.json")), &result.stdout).unwrap();
            std::fs::write(directory.join(format!("{entry}.stderr")), &result.stderr).unwrap();
            assert_eq!(std::fs::read(&request).unwrap(), bytes);
            assert_eq!(result.status.code(), Some(1), "{label}/{entry}");
            let envelope: serde_json::Value = serde_json::from_slice(&result.stdout).unwrap();
            let expected_failure = if entry == "matching" && expected != "unbound" {
                serde_json::json!({"code": "type_mismatch", "path": ["runner"]})
            } else {
                serde_json::json!({"code": "unsupported_contract", "path": ["contract"],
                                   "expected_contract": expected})
            };
            assert_eq!(
                envelope["data"]["request_failure"], expected_failure,
                "{label}/{entry}"
            );
            assert_eq!(envelope["result"]["normalized_outcome"], "bad_request");
            assert_eq!(envelope["build"]["contract"], expected);
            assert!(envelope["data"]["runner_client"].is_null());
            assert!(envelope["data"]["runner_result"].is_null());
            observations.push(serde_json::json!({"build": label, "supplied": supplied,
                "expected_identity": expected, "entry": entry, "asserted": asserted,
                "request_failure": expected_failure}));
            std::fs::write(
                artifacts.join("observations.json"),
                serde_json::to_vec_pretty(&observations).unwrap(),
            )
            .unwrap();
        }

        // Developer publication uses the emitting binary's identity without host admission.
        let published = run_pw(&binary, &["test-input", "read", "--target", "/absent"]);
        if expected == "unbound" {
            assert_eq!(published.status.code(), Some(2));
            assert!(published.stdout.is_empty());
        } else {
            assert_eq!(published.status.code(), Some(0));
            let value: serde_json::Value = serde_json::from_slice(&published.stdout).unwrap();
            assert_eq!(value["contract"], expected);
            assert_eq!(value["probe_plan"][0]["attempt"]["target"], "/absent");
        }

        // An unbound build emits nothing. A bound build emits its own
        // identity, and the selected app's `run` refuses that document at its
        // contract gate, before any client invocation.
        let emitted = run_pw(&binary, &["example"]);
        let example = directory.join("example.json");
        std::fs::write(&example, &emitted.stdout).unwrap();
        std::fs::write(directory.join("example.stderr"), &emitted.stderr).unwrap();
        if expected == "unbound" {
            assert_eq!(emitted.status.code(), Some(2), "{label}: example exit");
            assert!(emitted.stdout.is_empty(), "{label}: example stdout");
            let reason = String::from_utf8(emitted.stderr).unwrap();
            assert_eq!(reason.lines().count(), 1, "{label}: {reason:?}");
            assert!(reason.contains("no public identity"), "{label}: {reason:?}");
            continue;
        }
        assert_eq!(emitted.status.code(), Some(0), "{label}: example exit");
        assert!(emitted.stderr.is_empty(), "{label}: example stderr");
        let document: serde_json::Value = serde_json::from_slice(&emitted.stdout).unwrap();
        assert_eq!(document["contract"], expected, "{label}");
        let app_contract = candidate_contract();
        assert_ne!(app_contract, expected, "{label}");
        let refused = run_pw(&require_pw_bin(), &["run", example.to_str().unwrap()]);
        std::fs::write(directory.join("app-run.json"), &refused.stdout).unwrap();
        std::fs::write(directory.join("app-run.stderr"), &refused.stderr).unwrap();
        assert_eq!(std::fs::read(&example).unwrap(), emitted.stdout);
        assert_eq!(refused.status.code(), Some(1), "{label}: app run exit");
        let envelope: serde_json::Value = serde_json::from_slice(&refused.stdout).unwrap();
        assert_eq!(envelope["result"]["normalized_outcome"], "bad_request");
        assert_eq!(
            envelope["data"]["request_failure"],
            serde_json::json!({"code": "unsupported_contract", "path": ["contract"],
                               "expected_contract": app_contract}),
            "{label}"
        );
        assert!(envelope["data"]["runner_client"].is_null());
        assert!(envelope["data"]["runner_result"].is_null());
    }
}

/// A pipe's write end whose read end is already closed: every write fails.
fn unwritable() -> std::process::Stdio {
    let (reader, writer) = std::io::pipe().expect("pipe");
    drop(reader);
    writer.into()
}

#[test]
fn example_write_failures_exit_2_without_a_panic() {
    use std::process::Stdio;

    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();
    let run = |args: &[&str], stdout: Stdio, stderr: Stdio| {
        Command::new(&bin)
            .args(args)
            .stdin(Stdio::null())
            .stdout(stdout)
            .stderr(stderr)
            .spawn()
            .expect("spawn")
            .wait_with_output()
            .expect("wait")
    };
    let reason = "policy-witness example: failed to write stdout\n";

    // The document cannot be written: exit 2 and one line for a person.
    let output = run(&["example"], unwritable(), Stdio::piped());
    assert_eq!(output.status.code(), Some(2));
    assert_eq!(String::from_utf8(output.stderr).unwrap(), reason);
    // Neither stream can be written: the exit status is the whole report.
    let output = run(&["example"], unwritable(), unwritable());
    assert_eq!(output.status.code(), Some(2));
    // A refusal whose reason cannot be written is still exit 2 with no output.
    let output = run(&["example", "extra"], Stdio::piped(), unwritable());
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());

    // A stderr closed at launch changes neither status.
    let shell = |script: &str| {
        Command::new("/bin/sh")
            .args(["-c", script])
            .arg(&bin)
            .stdin(Stdio::null())
            .output()
            .expect("shell")
    };
    let output = shell("exec \"$0\" example extra 2>&-");
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    let output = shell("exec \"$0\" example 2>&-");
    assert_eq!(output.status.code(), Some(0));
    let reference = run(&["example"], Stdio::piped(), Stdio::piped());
    assert_eq!(output.stdout, reference.stdout);
}

#[test]
fn example_prints_one_request_and_refuses_every_argument() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();
    let first = run_pw(&bin, &["example"]);
    assert_eq!(first.status.code(), Some(0));
    assert!(first.stderr.is_empty());
    let text = String::from_utf8(first.stdout.clone()).unwrap();
    let body = text.strip_suffix('\n').expect("one framing newline");
    assert!(!body.ends_with('\n'));
    let document: serde_json::Value = serde_json::from_str(body).unwrap();
    assert!(document.is_object());
    assert_eq!(document["contract"], candidate_contract());
    let second = run_pw(&bin, &["example"]);
    assert_eq!(second.status.code(), Some(0));
    assert_eq!(second.stdout, first.stdout);

    for args in [
        vec!["example", "--help"],
        vec!["example", "-h"],
        vec!["example", "help"],
        vec!["example", "read-hosts"],
        vec!["example", ""],
        vec!["example", "--version"],
    ] {
        let output = run_pw(&bin, &args);
        assert_eq!(output.status.code(), Some(2), "{args:?}");
        assert!(output.stdout.is_empty(), "{args:?}");
        assert_eq!(
            String::from_utf8(output.stderr).unwrap(),
            "policy-witness example: accepts no arguments\n",
            "{args:?}"
        );
    }
}

#[test]
fn version_flag_reports_build_stamp_and_contract() {
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
    assert_eq!(envelope["data"]["contract"], candidate_contract());
    assert_eq!(envelope["build"]["contract"], candidate_contract());
    assert!(envelope.get("schema_version").is_none());
}

#[test]
fn specimen_smoke_file_read_deny() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();

    // Sandboxed harnesses can block XPC lookup; rerun from
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
    assert_eq!(envelope["result"]["normalized_outcome"], "finished");
    assert_eq!(runner["normalized_outcome"], "finished");
    let steps = runner
        .get("steps")
        .and_then(|v| v.as_array())
        .cloned()
        .unwrap_or_default();
    assert_eq!(steps.len(), 1, "expected 1 step, got {}", steps.len());
    let step = &steps[0];
    let sb = step.get("sandbox_check").cloned().unwrap_or_default();
    assert_eq!(sb.get("outcome").and_then(|v| v.as_str()), Some("deny"));
    assert_eq!(step["attempt"]["outcome"], "open_failed");
    assert_ne!(step["attempt"]["rc"], 0);
    assert_eq!(step["comparison"]["observation"], "permission_failure");
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
            "parameters omitted",
            "(version 1) (allow default)",
            None,
            "ok",
            0,
        ),
        (
            "parameters null",
            "(version 1) (allow default)",
            Some(serde_json::Value::Null),
            "ok",
            0,
        ),
        (
            "parameters empty map",
            "(version 1) (allow default)",
            Some(serde_json::json!({})),
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
            "required path parameter null map",
            path_param,
            Some(serde_json::Value::Null),
            "compile_error",
            1,
        ),
        (
            "required path parameter empty map",
            path_param,
            Some(serde_json::json!({})),
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
    let artifacts = PathBuf::from(env::var_os("PW_TEST_ARTIFACTS").expect("dispatcher artifacts"))
        .join("native-parameter-cases");
    std::fs::create_dir(&artifacts).expect("fresh helper artifacts");
    for (index, (label, source, params, outcome, exit)) in cases.into_iter().enumerate() {
        let mut policy = serde_json::json!({"format": "sbpl", "sbpl_source": source});
        if let Some(params) = &params {
            policy["params"] = params.clone();
        }
        let request = serde_json::json!({"policy": policy, "probe_plan": []}).to_string();
        // Alternate file and stdin delivery across the table.
        let via_stdin = index % 2 == 1;
        let out = run_sbpl_check_request(&bin, &request, via_stdin);
        let case = artifacts.join(format!("{index:02}"));
        std::fs::create_dir(&case).unwrap();
        std::fs::write(case.join("request.json"), &request).unwrap();
        std::fs::write(case.join("stdout.json"), &out.stdout).unwrap();
        std::fs::write(case.join("stderr"), &out.stderr).unwrap();
        std::fs::write(case.join("receipt.json"), serde_json::to_vec_pretty(&serde_json::json!({
            "label": label, "binary": bin, "delivery": if via_stdin {"stdin"} else {"file"},
            "expected_outcome": outcome, "expected_exit": exit, "observed_exit": out.status.code()
        })).unwrap()).unwrap();
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
        // Null and omission both decode as absent; an empty object remains
        // present even though all three pass zero entries to the compiler.
        let (present, count) = match &params {
            None | Some(serde_json::Value::Null) => (false, 0),
            Some(serde_json::Value::Object(map)) => (true, map.len()),
            other => panic!("invalid parameter fixture: {other:?}"),
        };
        assert_eq!(data["params_present"], present, "{label}");
        assert_eq!(data["params_count"], count, "{label}");
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
            "contract": candidate_contract(), "specimen_id": "same-as-input",
            "policy": {"format": "sbpl", "sbpl_source": "(version 1)(allow default)"},
            "probe_plan": [{"step_id": "s",
                "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": target}},
                "attempt": {"kind": "file", "action": "open_read", "target": target}}]
        })
        .to_string(),
    )
    .unwrap();
    let out = run_pw(&bin, &["run", specimen.to_str().unwrap()]);
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
            "contract": candidate_contract(), "specimen_id": "unicode-path",
            "policy": {"format": "sbpl", "sbpl_source": "(version 1)(allow default)"},
            "probe_plan": [{"step_id": "unicode", "sandbox_check": {
                "operation": "file-read-data", "filter": {"kind": "path", "value": submitted}},
                "attempt": {"kind": "file", "action": "open_read", "target": submitted}}]
        })
        .to_string(),
    )
    .unwrap();
    let output = run_pw(&bin, &["run", request.to_str().unwrap()]);
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
    let request = serde_json::json!({
        "contract": candidate_contract(),
        "specimen_id": "augment_applied",
        "policy": {
            "format": "sbpl",
            "sbpl_source": "(version 1)\n(allow default)\n",
            "augments": ["exec_baseline"]
        },
        "probe_plan": []
    })
    .to_string();
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
        Some("finished"),
        "augmented run did not finish: envelope={envelope}"
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
    let request = serde_json::json!({
        "contract": candidate_contract(),
        "specimen_id": "augment_unknown",
        "policy": {
            "format": "sbpl",
            "sbpl_source": "(version 1)\n(allow default)\n",
            "augments": ["this_augment_definitely_does_not_exist_42"]
        },
        "probe_plan": []
    })
    .to_string();
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
    let request = serde_json::json!({
        "contract": candidate_contract(),
        "specimen_id": "augment_invalid",
        "policy": {
            "format": "sbpl",
            "sbpl_source": "(version 1)\n(allow default)\n",
            "augments": ["../etc/passwd"]
        },
        "probe_plan": []
    })
    .to_string();
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
    assert_eq!(envelope["data"]["request_failure"]["code"], "invalid_value");
    assert_eq!(
        envelope["data"]["request_failure"]["path"],
        serde_json::json!(["policy", "augments", "0"])
    );
    assert!(envelope["data"]["runner_client"].is_null());
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

#[test]
fn test_input_publishes_read_from_the_installed_binary() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();
    let target = "/nonexistent-parent/../$EFFECT quote\" backslash\\ newline\n é";
    let mut outputs = Vec::new();
    for _ in 0..2 {
        let output = Command::new(&bin)
            .args(["test-input", "read", "--target", target])
            .current_dir("/")
            .stdin(std::process::Stdio::null())
            .output()
            .unwrap();
        assert_eq!(output.status.code(), Some(0));
        assert!(output.stderr.is_empty());
        assert!(output.stdout.ends_with(b"\n") && !output.stdout.ends_with(b"\n\n"));
        let document: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
        assert_eq!(
            document,
            serde_json::json!({
                "contract": candidate_contract(), "specimen_id": "test-input",
                "policy": {"format": "sbpl", "sbpl_source": "(version 1)\n(allow default)"},
                "probe_plan": [{"step_id": "read-target",
                    "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": target}},
                    "attempt": {"kind": "file", "action": "read_fresh", "target": target}}]
            })
        );
        outputs.push(output.stdout);
    }
    assert_eq!(outputs[0], outputs[1]);
}

#[test]
fn test_input_cli_refusals_and_write_failures_exit_2_safely() {
    use std::os::unix::ffi::OsStringExt;
    use std::process::Stdio;
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();
    for args in [
        vec!["lesson", "create", "--target", "/x"],
        vec!["test-input"],
        vec!["test-input", "read"],
        vec!["test-input", "future", "--target", "/x"],
        vec!["test-input", "read", "--target", "relative"],
        vec!["test-input", "read", "--target", ""],
        vec!["test-input", "read", "--target", "/x", "--target", "/y"],
    ] {
        let output = Command::new(&bin).args(args).output().unwrap();
        assert_eq!(output.status.code(), Some(2));
        assert!(output.stdout.is_empty());
    }
    let output = Command::new(&bin)
        .args(["test-input", "read", "--target"])
        .arg(std::ffi::OsString::from_vec(vec![b'/', 255]))
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    let output = Command::new(&bin)
        .args(["test-input", "read", "--target", "/x"])
        .stdout(unwritable())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap()
        .wait_with_output()
        .unwrap();
    assert_eq!(output.status.code(), Some(2));
    assert!(!String::from_utf8_lossy(&output.stderr).contains("panicked"));
    for (script, expected) in [
        ("exec \"$0\" test-input read --target /x 2>&-", 0),
        ("exec \"$0\" test-input read --target relative 2>&-", 2),
    ] {
        let output = Command::new("/bin/sh")
            .args(["-c", script])
            .arg(&bin)
            .output()
            .unwrap();
        assert_eq!(output.status.code(), Some(expected));
        if expected == 2 {
            assert!(output.stdout.is_empty());
        }
    }
}

/// One step of an interface case: the invocation and what it must produce.
/// Expectations are spelled in the corpus; nothing here reads the interface
/// definitions or the inventory.
fn run_interface_step(bin: &Path, step: &serde_json::Value, scratch: &Path) -> Result<(), String> {
    use std::os::unix::ffi::OsStringExt;
    use std::process::Stdio;

    let place = |text: &str| text.replace("{scratch}", &scratch.to_string_lossy());
    for (name, content) in step["files"].as_object().into_iter().flatten() {
        let content = content.as_str().expect("a file's text");
        let content = if content.contains("{contract}") {
            content.replace("{contract}", &candidate_contract())
        } else {
            content.to_string()
        };
        std::fs::write(scratch.join(name), content).map_err(|error| error.to_string())?;
    }
    let mut command = Command::new(bin);
    for argument in step["args"].as_array().expect("args") {
        match argument {
            serde_json::Value::String(text) => command.arg(place(text)),
            other => {
                let hex = other["hex"]
                    .as_str()
                    .expect("an argument is text or hex bytes");
                let bytes = (0..hex.len())
                    .step_by(2)
                    .map(|index| u8::from_str_radix(&hex[index..index + 2], 16).unwrap())
                    .collect();
                command.arg(std::ffi::OsString::from_vec(bytes))
            }
        };
    }
    for (name, value) in step["env"].as_object().into_iter().flatten() {
        command.env(name, place(value.as_str().expect("an environment value")));
    }
    command.stdin(Stdio::null()).stderr(Stdio::piped());
    match step["stdout_pipe"].as_str() {
        None => command.stdout(Stdio::piped()),
        Some("no_reader") => command.stdout(unwritable()),
        Some(other) => panic!("unknown stdout_pipe {other}"),
    };
    let output = command
        .output()
        .map_err(|error| format!("launch: {error}"))?;
    let mut problems = Vec::new();
    let status = output.status.code();
    if status.map(i64::from) != step["status"].as_i64() {
        problems.push(format!("status {status:?}, expected {}", step["status"]));
    }
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    if let Some(expected) = step["stdout"].as_str() {
        if output.stdout != expected.as_bytes() {
            problems.push(format!("stdout {stdout:?}, expected {expected:?}"));
        }
    }
    if let Some(expected) = step["stdout_json"].as_object() {
        match serde_json::from_slice::<serde_json::Value>(&output.stdout) {
            Ok(value) => {
                for (pointer, wanted) in expected {
                    if value.pointer(pointer) != Some(wanted) {
                        problems.push(format!(
                            "stdout {pointer} is {:?}, expected {wanted}",
                            value.pointer(pointer)
                        ));
                    }
                }
                if !stdout.ends_with('\n') || stdout.ends_with("\n\n") {
                    problems.push("stdout is not one document and one newline".into());
                }
            }
            Err(error) => problems.push(format!("stdout is not one JSON document: {error}")),
        }
    }
    match (step["stderr"].as_str(), step["stderr_prefix"].as_str()) {
        (Some(expected), None) => {
            if output.stderr != expected.as_bytes() {
                problems.push(format!("stderr {stderr:?}, expected {expected:?}"));
            }
        }
        (None, Some(prefix)) => {
            if !stderr.starts_with(prefix) {
                problems.push(format!("stderr {stderr:?}, expected the prefix {prefix:?}"));
            }
        }
        _ => panic!("a step states stderr or stderr_prefix, one of them"),
    }
    if let Some(name) = step["save_stdout"].as_str() {
        std::fs::write(scratch.join(name), &output.stdout).map_err(|error| error.to_string())?;
    }
    if problems.is_empty() {
        Ok(())
    } else {
        Err(problems.join("; "))
    }
}

/// Runs every case of the corpus and returns the failures, each named.
fn run_interface_cases(bin: &Path, corpus: &serde_json::Value) -> Vec<String> {
    // Tests in this binary run in parallel; each call takes directories of its own.
    static CALLS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
    let call = CALLS.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    let mut failures = Vec::new();
    for (index, case) in corpus["cases"]
        .as_array()
        .expect("cases")
        .iter()
        .enumerate()
    {
        let id = case["id"].as_str().expect("case id");
        let scratch = env::temp_dir().join(format!(
            "pw-interface-{}-{call}-{index}",
            std::process::id()
        ));
        std::fs::create_dir_all(&scratch).unwrap();
        let steps = match case["steps"].as_array() {
            Some(steps) => steps.clone(),
            None => vec![case.clone()],
        };
        for (number, step) in steps.iter().enumerate() {
            if let Err(problem) = run_interface_step(bin, step, &scratch) {
                failures.push(format!("{id} step {number}: {problem}"));
            }
        }
        std::fs::remove_dir_all(&scratch).unwrap();
    }
    failures
}

fn interface_corpus() -> serde_json::Value {
    serde_json::from_str(include_str!("interface_cases.json")).expect("the case corpus")
}

#[test]
fn interface_cases_hold_on_the_signed_controller() {
    if !integration_enabled() {
        return;
    }
    let failures = run_interface_cases(&require_pw_bin(), &interface_corpus());
    assert!(failures.is_empty(), "{}", failures.join("\n"));
}

/// The executor rejects a wrong status and output on the wrong stream.
#[test]
fn interface_case_executor_rejects_wrong_status_and_stream() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();
    let case = |status: i64, stdout: &str, stderr: &str| {
        serde_json::json!({"cases": [{"id": "control", "args": ["help"], "status": status,
                                      "stdout": stdout, "stderr": stderr}]})
    };
    let card = "run\nexample\nresult\n";
    assert!(run_interface_cases(&bin, &case(0, card, "")).is_empty());
    let wrong_status = run_interface_cases(&bin, &case(2, card, ""));
    assert!(wrong_status.len() == 1 && wrong_status[0].contains("status Some(0), expected 2"));
    let wrong_stream = run_interface_cases(&bin, &case(0, "", card));
    assert!(
        wrong_stream.len() == 1
            && wrong_stream[0].contains("stdout")
            && wrong_stream[0].contains("stderr"),
        "{wrong_stream:?}"
    );
}

/// What each card shows is what the same binary does: a listed topic
/// addresses a card of its own, a shown option and value pass argument
/// admission, and the example card's lines are the emitted specimen's.
/// Every expectation is read from the binary's output, none from the
/// interface definitions.
#[test]
fn help_cards_agree_with_execution() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();
    let card = |args: &[&str]| {
        let output = run_pw(&bin, args);
        assert_eq!(output.status.code(), Some(0), "{args:?}");
        assert!(output.stderr.is_empty(), "{args:?}");
        String::from_utf8(output.stdout).unwrap()
    };
    let base = card(&["help"]);
    assert!(base.lines().count() > 0);
    for topic in base.lines() {
        let addressed = card(&["help", topic]);
        assert_ne!(addressed, base, "{topic} addresses its own card");
        assert_eq!(addressed.lines().next(), Some(topic));
    }

    let run = card(&["help", "run"]);
    let mut lines = run.lines();
    let command = lines.next().unwrap();
    let mut option = None;
    let mut pairs = 0;
    for line in lines {
        match line.strip_prefix("    ") {
            Some(value) => {
                let option: &str = option.expect("a value follows its option");
                let output = run_pw(&bin, &[command, option, value]);
                let envelope: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
                assert_eq!(
                    envelope["result"]["error"], "missing <request.json>",
                    "{command} {option} {value} passes argument admission"
                );
                pairs += 1;
            }
            None => option = Some(line.strip_prefix("  ").expect("an option line")),
        }
    }
    assert!(pairs > 0, "the run card shows no option value");

    let example = card(&["help", "example"]);
    let mut lines = example.lines();
    let command = lines.next().unwrap();
    let emitted: serde_json::Value =
        serde_json::from_slice(&run_pw(&bin, &[command]).stdout).expect("the emitted specimen");
    let mut expected = Vec::new();
    for phase in emitted["phases"].as_array().unwrap() {
        expected.push(format!("  {}", phase["phase_id"].as_str().unwrap()));
        for action in phase["actions"].as_array().unwrap() {
            expected.push(format!(
                "    {} {}",
                action["attempt"]["action"].as_str().unwrap(),
                action["attempt"]["target"].as_str().unwrap()
            ));
        }
    }
    assert_eq!(lines.collect::<Vec<_>>(), expected);
}

/// Help needs nothing a run needs. The Cargo-built binary, which has no
/// bundle around it, with no usable home directory, no registry and
/// malformed tails, prints the bytes the bundled binary prints, with status 0
/// and an empty stderr. A copy of the bundle's own signed executable cannot
/// stand in for it: outside its bundle the system refuses to run it.
#[test]
fn help_needs_no_app_home_registry_or_valid_tail() {
    use std::os::unix::ffi::OsStringExt;
    use std::os::unix::fs::PermissionsExt;
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();
    let scratch = env::temp_dir().join(format!("pw-help-prerequisites-{}", std::process::id()));
    std::fs::create_dir_all(&scratch).unwrap();
    let unbundled = Path::new(env!("CARGO_BIN_EXE_policy-witness"));
    let unwritable = scratch.join("unwritable-home");
    std::fs::create_dir(&unwritable).unwrap();
    std::fs::set_permissions(&unwritable, std::fs::Permissions::from_mode(0o500)).unwrap();
    let absent = scratch.join("absent");
    let non_utf8 = || std::ffi::OsString::from_vec(vec![0xff, 0xfe]);
    let tails: Vec<Vec<std::ffi::OsString>> = vec![
        vec![],
        vec!["run".into()],
        vec!["run".into(), "--bad".into(), non_utf8()],
        vec!["example".into(), "extra".into()],
        vec!["result".into(), "--".into()],
        vec![non_utf8()],
        vec!["bogus".into(), "run".into()],
    ];
    for tail in &tails {
        let reference = Command::new(&bin).arg("help").args(tail).output().unwrap();
        assert_eq!(reference.status.code(), Some(0), "{tail:?}");
        assert!(reference.stderr.is_empty(), "{tail:?}");
        assert!(reference.stdout.ends_with(b"\n") && !reference.stdout.ends_with(b"\n\n"));
        let states: [(&str, Option<&Path>, Option<&Path>); 4] = [
            ("no HOME", None, None),
            ("absent HOME", Some(&absent), None),
            ("unwritable HOME", Some(&unwritable), None),
            ("absent registry", Some(&absent), Some(&absent)),
        ];
        for (state, home, registry) in states {
            let mut command = Command::new(unbundled);
            command
                .arg("help")
                .args(tail)
                .env_remove("HOME")
                .env_remove("PW_RUNNER_REGISTRY");
            if let Some(home) = home {
                command.env("HOME", home);
            }
            if let Some(registry) = registry {
                command.env("PW_RUNNER_REGISTRY", registry);
            }
            let output = command.stdin(std::process::Stdio::null()).output().unwrap();
            assert_eq!(output.status.code(), Some(0), "{state}: {tail:?}");
            assert!(output.stderr.is_empty(), "{state}: {tail:?}");
            assert_eq!(output.stdout, reference.stdout, "{state}: {tail:?}");
        }
    }
    std::fs::set_permissions(&unwritable, std::fs::Permissions::from_mode(0o700)).unwrap();
    std::fs::remove_dir_all(&scratch).unwrap();
}

fn copy_tree(from: &Path, to: &Path) {
    std::fs::create_dir_all(to).unwrap();
    for entry in std::fs::read_dir(from).unwrap() {
        let entry = entry.unwrap();
        let target = to.join(entry.file_name());
        if entry.file_type().unwrap().is_dir() {
            copy_tree(&entry.path(), &target);
        } else {
            std::fs::copy(entry.path(), target).unwrap();
        }
    }
}

/// The package's build script compares the inventory it renders with the
/// committed copy. In a copy of the package, a changed definition and a
/// changed committed inventory each stop Cargo before the binary compiles,
/// naming the copy and the command that regenerates it. Incompatible card
/// references are rejected by rendering before that freshness comparison.
#[test]
fn stale_interface_inventory_stops_the_build_script() {
    if !integration_enabled() {
        return;
    }
    let scratch = PathBuf::from(env::var_os("PW_TEST_SCRATCH").expect("dispatcher scratch"))
        .join("stale-interface-inventory");
    let artifacts = PathBuf::from(env::var_os("PW_TEST_ARTIFACTS").expect("dispatcher artifacts"))
        .join("stale-interface-inventory");
    std::fs::create_dir_all(&scratch).unwrap();
    std::fs::create_dir(&artifacts).unwrap();
    let package = scratch.join("controller");
    let source = repo_root().join("controller");
    std::fs::create_dir(&package).unwrap();
    for file in ["Cargo.toml", "Cargo.lock", "build.rs"] {
        std::fs::copy(source.join(file), package.join(file)).unwrap();
    }
    for directory in ["src", "interface", "integration"] {
        copy_tree(&source.join(directory), &package.join(directory));
    }
    let check = |label: &str| {
        let mut command = Command::new("cargo");
        command
            .args([
                "check",
                "--locked",
                "--offline",
                "--bin",
                "policy-witness",
                "--target",
                "aarch64-apple-darwin",
                "--target-dir",
            ])
            .arg(scratch.join("target"))
            .arg("--manifest-path")
            .arg(package.join("Cargo.toml"));
        for key in [
            "PW_BUILD_CONTRACT",
            "PW_BUILD_VERSION",
            "PW_BUILD_NUMBER",
            "PW_BUILD_DESCRIBE",
            "PW_BUILD_COMMIT",
            "PW_INTERFACE_REFRESH",
        ] {
            command.env_remove(key);
        }
        let output = command.output().expect("cargo check");
        std::fs::write(artifacts.join(format!("{label}.stderr")), &output.stderr).unwrap();
        (
            output.status.success(),
            String::from_utf8_lossy(&output.stderr).into_owned(),
        )
    };
    let stale = "controller/interface/inventory.json is stale";
    let remedy = "tests/lib/python.sh docs/generate_interface.py --refresh-inventory";

    let (passed, stderr) = check("unchanged");
    assert!(passed, "{stderr}");

    let definitions = package.join("src/interface/run_args.rs");
    let original = std::fs::read_to_string(&definitions).unwrap();
    assert_eq!(original.matches("\"--runner-mode\"").count(), 1);
    std::fs::write(
        &definitions,
        original.replace("\"--runner-mode\"", "\"--runner-kind\""),
    )
    .unwrap();
    let (passed, stderr) = check("changed-definition");
    assert!(!passed);
    assert!(
        stderr.contains(stale) && stderr.contains(remedy),
        "{stderr}"
    );
    std::fs::write(&definitions, &original).unwrap();

    for (label, relative, old, new, reason) in [
        (
            "option-without-kind-words",
            "interface/cards.rs",
            "pub const RUN_OPTION: RunOption = RunOption::RunnerMode;",
            "pub const RUN_OPTION: RunOption = RunOption::TimeoutMs;",
            "TimeoutMs does not take a runner-kind word",
        ),
        (
            "topic-with-another-command",
            "src/interface/commands.rs",
            "Topic::Run => Address::Command(Command::Run)",
            "Topic::Run => Address::Command(Command::Version)",
            "Run heads a card whose topic is not that command",
        ),
    ] {
        let path = package.join(relative);
        let original = std::fs::read_to_string(&path).unwrap();
        assert_eq!(original.matches(old).count(), 1, "{label}");
        std::fs::write(&path, original.replace(old, new)).unwrap();
        let (passed, stderr) = check(label);
        assert!(!passed && stderr.contains(reason), "{label}: {stderr}");
        std::fs::write(&path, original).unwrap();
    }

    let committed = package.join("interface/inventory.json");
    let original = std::fs::read_to_string(&committed).unwrap();
    assert_eq!(original.matches("--runner-mode\\n").count(), 1);
    std::fs::write(
        &committed,
        original.replace("--runner-mode\\n", "--runner-kind\\n"),
    )
    .unwrap();
    let (passed, stderr) = check("changed-committed-copy");
    assert!(!passed);
    assert!(
        stderr.contains(stale) && stderr.contains(remedy),
        "{stderr}"
    );
    std::fs::write(&committed, &original).unwrap();

    let (passed, stderr) = check("restored");
    assert!(passed, "{stderr}");
}

/// A directory of one test's own, removed when the test ends. Modes a test
/// changes are restored first, so a failed assertion leaves nothing behind
/// that cannot be removed.
struct Scratch {
    root: PathBuf,
    restore: Vec<(PathBuf, u32)>,
}

impl Scratch {
    fn new(name: &str) -> Self {
        let root = env::temp_dir().join(format!("pw-{name}-{}", std::process::id()));
        std::fs::create_dir(&root).unwrap();
        // The temporary directory is reached through a symlink; a recorded
        // launchd plist location refuses a symlinked ancestor.
        let root = std::fs::canonicalize(root).unwrap();
        Scratch {
            root,
            restore: Vec::new(),
        }
    }

    /// Sets `mode` on `path` now and `restored` when the test ends.
    fn set_mode(&mut self, path: &Path, mode: u32, restored: u32) {
        use std::os::unix::fs::PermissionsExt;
        self.restore.push((path.to_path_buf(), restored));
        std::fs::set_permissions(path, std::fs::Permissions::from_mode(mode)).unwrap();
    }
}

impl Drop for Scratch {
    fn drop(&mut self) {
        use std::os::unix::fs::PermissionsExt;
        for (path, mode) in self.restore.drain(..).rev() {
            let _ = std::fs::set_permissions(&path, std::fs::Permissions::from_mode(mode));
        }
        let _ = std::fs::remove_dir_all(&self.root);
    }
}

/// One controller invocation whose `HOME` and registry location are supplied
/// to the child alone, so no row reads the user's registry or LaunchAgents.
fn run_with_registry(bin: &Path, args: &[&str], home: &Path, registry: &Path) -> Output {
    Command::new(bin)
        .args(args)
        .env("HOME", home)
        .env("PW_RUNNER_REGISTRY", registry)
        .stdin(std::process::Stdio::null())
        .output()
        .unwrap_or_else(|err| panic!("failed to run {}: {err}", bin.display()))
}

/// Each row's invocation and what it returned, kept beside the case's log.
fn save_rows(name: &str, rows: &[serde_json::Value]) {
    let directory =
        PathBuf::from(env::var_os("PW_TEST_ARTIFACTS").expect("dispatcher artifacts")).join(name);
    std::fs::create_dir(&directory).unwrap();
    std::fs::write(
        directory.join("rows.json"),
        serde_json::to_vec_pretty(rows).unwrap(),
    )
    .unwrap();
}

/// What one row of a registry control must return: the whole stderr beside
/// an empty stdout, or pointer values of the envelope beside an empty stderr.
enum Returned<'a> {
    Refusal(&'a str),
    Envelope(Vec<(&'a str, serde_json::Value)>),
}

/// The four fields every envelope of a runner command carries.
fn runner_envelope<'a>(kind: &str, outcome: &str, exit: i32) -> Vec<(&'a str, serde_json::Value)> {
    vec![
        ("/kind", kind.into()),
        ("/result/normalized_outcome", outcome.into()),
        ("/result/ok", (exit == 0).into()),
        ("/result/exit_code", exit.into()),
    ]
}

/// The registry loader's reading of a path, through the commands that load
/// it. Only a path where inspection finds no entry is an empty registry. An
/// ancestor that cannot be searched, an ancestor that is a file, a file that
/// cannot be read and a symlink whose target is missing each refuse, naming
/// the path and the system error: a runner command with one line on stderr,
/// no envelope and exit 2, and `run` with an external selector as its tool
/// error. The same registry is read while it is reachable.
#[test]
fn registry_that_cannot_be_read_refuses_and_only_an_absent_path_is_empty() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();
    let mut scratch = Scratch::new("registry-inspection");
    let root = scratch.root.clone();
    let home = root.join("home");
    std::fs::create_dir(&home).unwrap();
    let service = "com.policywitness.test.registry-inspection";
    let recorded = serde_json::json!({"schema_version": 1, "runners": [{
        "id": "runner-recorded", "service_name": service,
        "bundle_path": "/private/tmp/pw-recorded/PWRunner.xpc",
        "executable_path": "/private/tmp/pw-recorded/PWRunner.xpc/Contents/MacOS/PWRunner",
        "bundle_id": service, "scope": "user", "contract": candidate_contract(),
        "signature": {"team_id": null, "identity": null, "cdhash": null,
                      "valid": true, "adhoc": true},
        "entitlements": {"raw_plist": null, "keys": [], "error": null},
        "installed_at_unix_ms": 1, "kind": "byoxpc"}]})
    .to_string();
    let request = root.join("request.json");
    std::fs::write(
        &request,
        serde_json::json!({
            "contract": candidate_contract(), "specimen_id": "registry-inspection",
            "policy": {"format": "sbpl", "sbpl_source": "(version 1)\n(allow default)\n"},
            "probe_plan": [], "runner": {"mode": "byoxpc", "service": service}
        })
        .to_string(),
    )
    .unwrap();
    let request = request.to_str().unwrap().to_owned();

    let absent = root.join("absent").join("runners.json");
    let sealed = root.join("sealed").join("runners.json");
    let unreadable = root.join("unreadable").join("runners.json");
    let dangling = root.join("dangling").join("runners.json");
    let target = root.join("dangling").join("missing-target.json");
    let below_file = root.join("file").join("runners.json");
    for registry in [&sealed, &unreadable] {
        std::fs::create_dir(registry.parent().unwrap()).unwrap();
        std::fs::write(registry, &recorded).unwrap();
    }
    std::fs::create_dir(dangling.parent().unwrap()).unwrap();
    std::os::unix::fs::symlink(&target, &dangling).unwrap();
    std::fs::write(root.join("file"), "not a directory").unwrap();

    let mut rows = Vec::new();
    let mut row = |state: &str, registry: &Path, args: &[&str], status: i32, returned: Returned| {
        let output = run_with_registry(&bin, args, &home, registry);
        let stdout = String::from_utf8_lossy(&output.stdout).into_owned();
        let stderr = String::from_utf8_lossy(&output.stderr).into_owned();
        let mut problems = Vec::new();
        if output.status.code() != Some(status) {
            problems.push(format!(
                "status {:?}, expected {status}",
                output.status.code()
            ));
        }
        match returned {
            Returned::Refusal(line) => {
                if !stdout.is_empty() {
                    problems.push("stdout is not empty".to_string());
                }
                if stderr != line {
                    problems.push(format!("stderr {stderr:?}, expected {line:?}"));
                }
            }
            Returned::Envelope(pointers) => {
                if !stderr.is_empty() {
                    problems.push(format!("stderr {stderr:?}, expected none"));
                }
                match serde_json::from_str::<serde_json::Value>(&stdout) {
                    Ok(envelope) => {
                        for (pointer, wanted) in pointers {
                            if envelope.pointer(pointer) != Some(&wanted) {
                                problems.push(format!(
                                    "{pointer} is {:?}, expected {wanted}",
                                    envelope.pointer(pointer)
                                ));
                            }
                        }
                    }
                    Err(error) => problems.push(format!("stdout is not one envelope: {error}")),
                }
            }
        }
        rows.push(serde_json::json!({
            "state": state, "registry": registry, "args": args,
            "status": output.status.code(), "stdout": stdout, "stderr": stderr,
            "problems": problems,
        }));
    };
    let status_args = ["runner", "status", "--service-name", service];
    let verify_args = ["runner", "verify", "--service-name", service];
    let readers: [&[&str]; 4] = [
        &["runner", "list"],
        &["runner", "reconcile"],
        &status_args,
        &verify_args,
    ];
    let inspect = |registry: &Path, error: &str| {
        format!(
            "cannot inspect runner registry {}: {error}",
            registry.display()
        )
    };
    let unread =
        |registry: &Path, error: &str| format!("failed to read {}: {error}", registry.display());
    let tool_error = |error: String| {
        Returned::Envelope(vec![
            ("/kind", "run".into()),
            ("/result/normalized_outcome", "tool_error".into()),
            ("/result/exit_code", 2.into()),
            ("/result/error", error.into()),
            ("/data/runner_client", serde_json::Value::Null),
        ])
    };
    let denied = "Permission denied (os error 13)";

    // No entry, and no directory to hold one: the empty registry and a
    // lookup miss in its own envelope.
    let mut listed = runner_envelope("runner_registry", "ok", 0);
    listed.push(("/data/runners", serde_json::json!([])));
    listed.push(("/data/pending_cleanup", serde_json::json!([])));
    row(
        "absent",
        &absent,
        &["runner", "list"],
        0,
        Returned::Envelope(listed),
    );
    let mut reconciled = runner_envelope("runner_reconcile", "ok", 0);
    reconciled.push(("/data/registry_path", absent.to_str().unwrap().into()));
    reconciled.push(("/data/records", serde_json::json!([])));
    row(
        "absent",
        &absent,
        &["runner", "reconcile"],
        0,
        Returned::Envelope(reconciled),
    );
    row(
        "absent",
        &absent,
        &status_args,
        2,
        Returned::Envelope(runner_envelope("runner_status", "not_found", 2)),
    );
    let absent_created = std::fs::symlink_metadata(absent.parent().unwrap()).is_ok();

    // The recorded registry while its directory can be searched.
    let mut listed = runner_envelope("runner_registry", "ok", 0);
    listed.push(("/data/runners/0/service_name", service.into()));
    row(
        "reachable",
        &sealed,
        &["runner", "list"],
        0,
        Returned::Envelope(listed),
    );
    let mut found = runner_envelope("runner_status", "ok", 0);
    found.push(("/data/service_name", service.into()));
    row(
        "reachable",
        &sealed,
        &status_args,
        0,
        Returned::Envelope(found),
    );

    // The same registry under a directory that cannot be searched.
    scratch.set_mode(sealed.parent().unwrap(), 0o000, 0o700);
    let line = inspect(&sealed, denied) + "\n";
    for args in readers {
        row(
            "inaccessible ancestor",
            &sealed,
            args,
            2,
            Returned::Refusal(&line),
        );
    }
    row(
        "inaccessible ancestor",
        &sealed,
        &["run", &request],
        2,
        tool_error(inspect(&sealed, denied)),
    );
    // A command that replaces the registry takes its lock first and is
    // refused there.
    let lock = format!("open registry lock {}.lock: {denied}\n", sealed.display());
    let writers: [&[&str]; 2] = [
        &["runner", "validate"],
        &["runner", "remove", "--service-name", service],
    ];
    for args in writers {
        row(
            "inaccessible ancestor",
            &sealed,
            args,
            2,
            Returned::Refusal(&lock),
        );
    }

    // A registry file that cannot be read, in a directory that can be searched.
    scratch.set_mode(&unreadable, 0o000, 0o600);
    let line = unread(&unreadable, denied) + "\n";
    for args in readers {
        row(
            "unreadable file",
            &unreadable,
            args,
            2,
            Returned::Refusal(&line),
        );
    }
    row(
        "unreadable file",
        &unreadable,
        &["run", &request],
        2,
        tool_error(unread(&unreadable, denied)),
    );

    // A symlink whose target is missing is an entry that cannot be read. The
    // command that would save a registry there leaves the link as it was.
    let missing = "No such file or directory (os error 2)";
    let line = unread(&dangling, missing) + "\n";
    for args in readers {
        row(
            "symlink to a missing target",
            &dangling,
            args,
            2,
            Returned::Refusal(&line),
        );
    }
    row(
        "symlink to a missing target",
        &dangling,
        &["run", &request],
        2,
        tool_error(unread(&dangling, missing)),
    );
    row(
        "symlink to a missing target",
        &dangling,
        &["runner", "validate"],
        2,
        Returned::Refusal(&line),
    );
    let link_kept = std::fs::symlink_metadata(&dangling).is_ok_and(|m| m.file_type().is_symlink())
        && std::fs::symlink_metadata(&target).is_err();

    // An ancestor that is a regular file.
    let not_a_directory = "Not a directory (os error 20)";
    let line = inspect(&below_file, not_a_directory) + "\n";
    for args in readers {
        row(
            "ancestor is a file",
            &below_file,
            args,
            2,
            Returned::Refusal(&line),
        );
    }
    row(
        "ancestor is a file",
        &below_file,
        &["run", &request],
        2,
        tool_error(inspect(&below_file, not_a_directory)),
    );

    save_rows("registry-inspection", &rows);
    let mut problems: Vec<String> = rows
        .iter()
        .flat_map(|row| {
            row["problems"]
                .as_array()
                .unwrap()
                .iter()
                .map(move |problem| format!("{}: {}: {problem}", row["state"], row["args"]))
        })
        .collect();
    if absent_created {
        problems.push("absent: a read-only command created the registry directory".into());
    }
    if !link_kept {
        problems.push("symlink to a missing target: the link was replaced or followed".into());
    }
    assert!(problems.is_empty(), "{}", problems.join("\n"));
}

/// The result forms of the runner commands: a completed command reports
/// `ok`, true and exit 0 in its envelope; a usage or argument refusal writes
/// its reason to stderr, prints no envelope and exits 2.
#[test]
fn runner_commands_report_ok_or_refuse_on_stderr_without_an_envelope() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();
    let scratch = Scratch::new("runner-result-forms");
    let home = scratch.root.join("home");
    std::fs::create_dir(&home).unwrap();
    let registry = scratch.root.join("registry").join("runners.json");
    let directory = registry.parent().unwrap();

    // A reason followed by the usage text, or the reason alone.
    let usage = "\n\nusage:\n";
    let refusals: [(&[&str], &str, bool); 6] = [
        (&["runner"], "missing runner command", true),
        (&["runner", "bogus"], "unknown runner command: bogus", true),
        (
            &["runner", "list", "extra"],
            "runner list accepts no arguments",
            false,
        ),
        (
            &["runner", "status"],
            "runner status requires --id or --service-name",
            false,
        ),
        (
            &["runner", "status", "--id"],
            "missing value for --id",
            false,
        ),
        (
            &["runner", "install", "--scope", "everyone"],
            "invalid value for --scope",
            false,
        ),
    ];
    for (args, reason, with_usage) in refusals {
        let output = run_with_registry(&bin, args, &home, &registry);
        assert_eq!(output.status.code(), Some(2), "{args:?}");
        assert!(output.stdout.is_empty(), "{args:?}");
        let stderr = String::from_utf8(output.stderr).unwrap();
        if with_usage {
            assert!(
                stderr.starts_with(&format!("{reason}{usage}")),
                "{args:?}: {stderr:?}"
            );
        } else {
            assert_eq!(stderr, format!("{reason}\n"), "{args:?}");
        }
    }
    // None of those created a registry, a lock or a directory for them.
    assert!(std::fs::symlink_metadata(directory).is_err());

    // A completed command reports `ok`, true and exit 0. Of these three only
    // validation replaces the registry, so only it creates the directory,
    // the lock and the file.
    let completed: [(&[&str], &str); 3] = [
        (&["runner", "list"], "runner_registry"),
        (&["runner", "reconcile"], "runner_reconcile"),
        (&["runner", "validate"], "runner_validate"),
    ];
    for (args, kind) in completed {
        let output = run_with_registry(&bin, args, &home, &registry);
        assert_eq!(output.status.code(), Some(0), "{args:?}");
        assert!(output.stderr.is_empty(), "{args:?}");
        let envelope: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
        assert_eq!(envelope["kind"], kind, "{args:?}");
        assert_eq!(envelope["result"]["normalized_outcome"], "ok", "{args:?}");
        assert_eq!(envelope["result"]["ok"], true, "{args:?}");
        assert_eq!(envelope["result"]["exit_code"], 0, "{args:?}");
        assert_eq!(
            std::fs::symlink_metadata(directory).is_ok(),
            kind == "runner_validate",
            "{args:?}"
        );
    }
    assert_eq!(
        serde_json::from_slice::<serde_json::Value>(&std::fs::read(&registry).unwrap()).unwrap(),
        serde_json::json!({"schema_version": 1, "runners": [], "pending_cleanup": []})
    );
}

/// One process with the given standard output and standard error. `input`,
/// when given, is written to its standard input, which is then closed.
fn launch(
    program: &Path,
    args: &[&str],
    environment: &[(&str, &Path)],
    input: Option<&str>,
    stdout: std::process::Stdio,
    stderr: std::process::Stdio,
) -> Output {
    use std::io::Write;
    use std::process::Stdio;
    let mut command = Command::new(program);
    command.args(args).stdout(stdout).stderr(stderr);
    for (name, value) in environment {
        command.env(name, value);
    }
    command.stdin(if input.is_some() {
        Stdio::piped()
    } else {
        Stdio::null()
    });
    let mut child = command.spawn().expect("spawn");
    if let Some(input) = input {
        // A child that ends before reading leaves a closed pipe; that write
        // is not what a row observes.
        let _ = child.stdin.take().unwrap().write_all(input.as_bytes());
    }
    child.wait_with_output().expect("wait")
}

/// The envelope publishers with a standard output that cannot be written:
/// `--version`, `version`, `run`, `test-input run`, the runner commands and
/// `sbpl-check` each exit 2 with one line on stderr, and exit 2 all the same
/// when stderr cannot be written either. A standard output closed at launch
/// is another state: the process holds a descriptor that discards what it is
/// given, no write fails and the command's own status stands.
#[test]
fn envelope_write_failures_exit_2_with_one_line_and_never_a_panic() {
    use std::process::Stdio;
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();
    let helper = require_sbpl_check_bin();
    let scratch = Scratch::new("envelope-write-failure");
    let home = scratch.root.join("home");
    std::fs::create_dir(&home).unwrap();
    let registry = scratch.root.join("registry").join("runners.json");
    let environment: [(&str, &Path); 2] = [("HOME", &home), ("PW_RUNNER_REGISTRY", &registry)];
    let missing = scratch.root.join("missing-request.json");
    let missing = missing.to_str().unwrap();
    let allow_all = r#"{"policy": {"format": "sbpl", "sbpl_source": "(version 1)(allow default)"}, "probe_plan": []}"#;

    // The program, its arguments and standard input, the line a failed write
    // leaves on stderr, and the status the command has when its envelope is
    // written.
    let publishers: [(&Path, &[&str], Option<&str>, &str, i32); 9] = [
        (
            &bin,
            &["--version"],
            None,
            "policy-witness --version: failed to write stdout\n",
            0,
        ),
        (
            &bin,
            &["version"],
            None,
            "policy-witness version: failed to write stdout\n",
            0,
        ),
        (
            &bin,
            &["run", missing],
            None,
            "policy-witness run: failed to write stdout\n",
            2,
        ),
        (
            &bin,
            &["test-input", "run", missing],
            None,
            "policy-witness test-input: failed to write stdout\n",
            2,
        ),
        (
            &bin,
            &["runner", "list"],
            None,
            "failed to write stdout\n",
            0,
        ),
        (
            &bin,
            &["runner", "reconcile"],
            None,
            "failed to write stdout\n",
            0,
        ),
        (
            &bin,
            &["runner", "status", "--service-name", "absent.service"],
            None,
            "failed to write stdout\n",
            2,
        ),
        (&helper, &["--help"], None, "failed to write stdout\n", 0),
        (
            &helper,
            &["--request", "-"],
            Some(allow_all),
            "failed to write stdout\n",
            0,
        ),
    ];
    let mut rows = Vec::new();
    let mut problems = Vec::new();
    for (program, args, input, line, own_status) in publishers {
        let name = program.file_name().unwrap().to_string_lossy().into_owned();
        let mut observe = |state: &str, output: Output, status: i32, stderr: Option<&str>| {
            let text = String::from_utf8_lossy(&output.stderr).into_owned();
            let mut found = Vec::new();
            if output.status.code() != Some(status) {
                found.push(format!(
                    "status {:?}, expected {status}",
                    output.status.code()
                ));
            }
            if stderr.is_some_and(|expected| text != expected) {
                found.push(format!("stderr {text:?}, expected {stderr:?}"));
            }
            problems.extend(
                found
                    .iter()
                    .map(|problem| format!("{name} {args:?}: {state}: {problem}")),
            );
            rows.push(serde_json::json!({
                "program": name, "args": args, "state": state,
                "status": output.status.code(), "stdout_bytes": output.stdout.len(),
                "stderr": text, "problems": found,
            }));
        };
        observe(
            "stdout without a reader",
            launch(
                program,
                args,
                &environment,
                input,
                unwritable(),
                Stdio::piped(),
            ),
            2,
            Some(line),
        );
        observe(
            "stdout and stderr without a reader",
            launch(
                program,
                args,
                &environment,
                input,
                unwritable(),
                unwritable(),
            ),
            2,
            None,
        );
        let mut shell = vec!["-c", "exec \"$0\" \"$@\" >&-", program.to_str().unwrap()];
        shell.extend_from_slice(args);
        observe(
            "stdout closed at launch",
            launch(
                Path::new("/bin/sh"),
                &shell,
                &environment,
                input,
                Stdio::piped(),
                Stdio::piped(),
            ),
            own_status,
            Some(""),
        );
    }
    // A refusal whose reason cannot be written is still exit 2 with no output.
    let output = launch(
        &helper,
        &[],
        &environment,
        None,
        Stdio::piped(),
        unwritable(),
    );
    if output.status.code() != Some(2) || !output.stdout.is_empty() {
        problems.push(format!(
            "sbpl-check without arguments, stderr without a reader: status {:?}, {} stdout bytes",
            output.status.code(),
            output.stdout.len()
        ));
    }
    rows.push(serde_json::json!({
        "program": "sbpl-check", "args": [], "state": "stderr without a reader",
        "status": output.status.code(), "stdout_bytes": output.stdout.len(),
    }));
    save_rows("envelope-write-failure", &rows);
    assert!(problems.is_empty(), "{}", problems.join("\n"));
    // No row created a registry: the runner rows read an absent one.
    assert!(std::fs::symlink_metadata(registry.parent().unwrap()).is_err());
}

/// A digest of every entry under `root`: relative path, kind, and a file's
/// bytes or a link's target.
fn tree_digest(root: &Path) -> String {
    use sha2::Digest;
    fn visit(root: &Path, directory: &Path, hasher: &mut sha2::Sha256) {
        let mut entries: Vec<PathBuf> = std::fs::read_dir(directory)
            .unwrap()
            .map(|entry| entry.unwrap().path())
            .collect();
        entries.sort();
        for path in entries {
            let kind = std::fs::symlink_metadata(&path).unwrap().file_type();
            hasher.update(
                path.strip_prefix(root)
                    .unwrap()
                    .to_string_lossy()
                    .as_bytes(),
            );
            if kind.is_symlink() {
                hasher.update(b"\0link\0");
                hasher.update(
                    std::fs::read_link(&path)
                        .unwrap()
                        .to_string_lossy()
                        .as_bytes(),
                );
            } else if kind.is_dir() {
                hasher.update(b"\0directory\0");
                visit(root, &path, hasher);
            } else {
                hasher.update(b"\0file\0");
                hasher.update(std::fs::read(&path).unwrap());
            }
            hasher.update(b"\0");
        }
    }
    let mut hasher = sha2::Sha256::new();
    visit(root, root, &mut hasher);
    format!("{:x}", hasher.finalize())
}

/// `runner install` with `--env XPC_SERVICE_PATH` set to anything but the
/// bundle path refuses before it changes anything. The bundle is a copy of
/// the selected app's own service, which passes every other check an install
/// makes, and the command asks for signing: an install that went ahead would
/// re-sign the copy, save a registry record and write a launchd plist whose
/// service path its own cleanup does not accept. The bundle path itself as
/// the value is not refused by this rule: beside a service name that is not
/// the bundle's identifier, the refusal is the later one for the name.
#[test]
fn runner_install_refuses_a_service_path_other_than_the_bundle_before_any_change() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();
    let scratch = Scratch::new("install-service-path");
    let root = scratch.root.clone();
    let home = root.join("home");
    std::fs::create_dir(&home).unwrap();
    let registry = root.join("registry").join("runners.json");
    let bundle = root.join("PWRunner.xpc");
    let copied = Command::new("/usr/bin/ditto")
        .arg(app_path().join("Contents/XPCServices/PWRunner.xpc"))
        .arg(&bundle)
        .output()
        .expect("copy the service bundle");
    assert!(copied.status.success(), "{copied:?}");
    let identifier = Command::new("/usr/bin/plutil")
        .args(["-extract", "CFBundleIdentifier", "raw", "-o", "-"])
        .arg(bundle.join("Contents/Info.plist"))
        .output()
        .expect("read the bundle identifier");
    assert!(identifier.status.success(), "{identifier:?}");
    let identifier = String::from_utf8(identifier.stdout).unwrap();
    let identifier = identifier.trim_end();
    let entitlements = root.join("entitlements.plist");
    std::fs::write(
        &entitlements,
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<plist version=\"1.0\"><dict/></plist>\n",
    )
    .unwrap();
    let before = tree_digest(&bundle);
    let bundle_text = bundle.to_str().unwrap();
    let install = |service_path: &Path, more: &[&str]| {
        let supplied = format!("XPC_SERVICE_PATH={}", service_path.display());
        let mut args = vec![
            "runner",
            "install",
            "--bundle",
            bundle_text,
            "--allow-adhoc",
            "--entitlements",
            entitlements.to_str().unwrap(),
            "--skip-bootstrap",
            "--env",
            &supplied,
        ];
        args.extend_from_slice(more);
        run_with_registry(&bin, &args, &home, &registry)
    };
    // What a row left behind: a registry directory, anything under the home
    // directory, a changed bundle.
    let changes = |label: &str| {
        let mut found = Vec::new();
        if std::fs::symlink_metadata(registry.parent().unwrap()).is_ok() {
            found.push(format!("{label}: a registry directory was created"));
        }
        if std::fs::read_dir(&home).unwrap().next().is_some() {
            found.push(format!("{label}: the home directory was written"));
        }
        if tree_digest(&bundle) != before {
            found.push(format!("{label}: the bundle was changed"));
        }
        found
    };
    let mut rows = Vec::new();
    let mut problems = Vec::new();

    let elsewhere = root.join("elsewhere").join("PWRunner.xpc");
    let output = install(&elsewhere, &[]);
    let stderr = String::from_utf8_lossy(&output.stderr).into_owned();
    let refusal = format!(
        "--env XPC_SERVICE_PATH={} differs from the bundle path {}; omit it or supply the bundle path\n",
        elsewhere.display(),
        bundle.display()
    );
    if output.status.code() != Some(2) || !output.stdout.is_empty() || stderr != refusal {
        problems.push(format!(
            "another path: status {:?}, {} stdout bytes, stderr {stderr:?}",
            output.status.code(),
            output.stdout.len()
        ));
    }
    let changed = changes("another path");
    // When an install went ahead, its own report of the plist it wrote.
    let reconciled = std::fs::symlink_metadata(&registry).is_ok().then(|| {
        let report = run_with_registry(&bin, &["runner", "reconcile"], &home, &registry);
        serde_json::from_slice::<serde_json::Value>(&report.stdout)
            .ok()
            .and_then(|value| value.pointer("/data/records").cloned())
    });
    rows.push(serde_json::json!({
        "row": "another path", "status": output.status.code(),
        "stdout": String::from_utf8_lossy(&output.stdout), "stderr": stderr,
        "changes": changed, "reconcile_records": reconciled,
    }));
    problems.extend(changed);

    let output = install(&bundle, &["--service-name", "not.the.bundle.identifier"]);
    let stderr = String::from_utf8_lossy(&output.stderr).into_owned();
    let later = format!("byoxpc service name must match CFBundleIdentifier ({identifier})\n");
    if output.status.code() != Some(2) || !output.stdout.is_empty() || stderr != later {
        problems.push(format!(
            "the bundle path: status {:?}, {} stdout bytes, stderr {stderr:?}",
            output.status.code(),
            output.stdout.len()
        ));
    }
    rows.push(serde_json::json!({
        "row": "the bundle path, beside another service name",
        "status": output.status.code(), "stderr": stderr,
    }));

    save_rows("install-service-path", &rows);
    assert!(problems.is_empty(), "{}", problems.join("\n"));
}
