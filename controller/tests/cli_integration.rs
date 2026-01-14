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
        return PathBuf::from(val);
    }
    repo_root()
        .join("PolicyWitness.app")
        .join("Contents")
        .join("MacOS")
        .join("policy-witness")
}

fn require_pw_bin() -> PathBuf {
    let path = pw_bin_path();
    if !path.exists() {
        panic!(
            "PolicyWitness.app not found at {} (build the app or set PW_BIN_PATH)",
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
fn specimen_smoke_file_read_deny() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();

    // Note: sandboxed automation harnesses can block XPC lookup or unified log access.
    // If this test fails with those symptoms, rerun from a normal Terminal to confirm.

    let specimen = repo_root()
        .join("tests")
        .join("fixtures")
        .join("pw_runner")
        .join("specimen_file_read_deny.json");
    assert!(specimen.exists(), "missing specimen fixture: {}", specimen.display());
    let out = run_pw(
        &bin,
        &["run", specimen.to_str().expect("specimen path utf8")],
    );

    assert!(out.status.success(), "specimen failed: rc={:?}\nstderr:\n{}\nstdout:\n{}",
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
