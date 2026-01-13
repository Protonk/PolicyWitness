use std::env;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::time::{SystemTime, UNIX_EPOCH};

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

fn now_unix_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

#[test]
fn inside_bare_prints_bool() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();
    let out = run_pw(&bin, &["inside", "--bare"]);
    assert!(out.status.success());
    let stdout = String::from_utf8_lossy(&out.stdout).trim().to_string();
    assert!(
        stdout == "true" || stdout == "false",
        "expected true/false, got {stdout:?}"
    );
}

#[test]
fn specimen_smoke_file_read_deny() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();

    // If we are running inside a sandboxed harness, specimen execution is expected to be blocked.
    let inside = run_pw(&bin, &["inside", "--bare"]);
    if inside.status.success() {
        let stdout = String::from_utf8_lossy(&inside.stdout).trim().to_string();
        if stdout == "true" {
            return;
        }
    }

    let specimen = repo_root()
        .join("tests")
        .join("fixtures")
        .join("pw_runner")
        .join("specimen_file_read_deny.json");
    assert!(specimen.exists(), "missing specimen fixture: {}", specimen.display());

    let outdir = std::env::temp_dir().join(format!(
        "pw_specimen_smoke_{}_{}",
        std::process::id(),
        now_unix_ms()
    ));

    let out = run_pw(
        &bin,
        &[
            "specimen",
            specimen.to_str().expect("specimen path utf8"),
            "--outdir",
            outdir.to_str().expect("outdir path utf8"),
            "--force",
        ],
    );

    // `specimen` uses exit code 3 to mean "blocked: inside=true". Treat as skip.
    if out.status.code() == Some(3) {
        return;
    }
    assert!(out.status.success(), "specimen failed: rc={:?}\nstderr:\n{}\nstdout:\n{}",
        out.status.code(),
        String::from_utf8_lossy(&out.stderr),
        String::from_utf8_lossy(&out.stdout)
    );

    let summary_path = outdir.join("lab_summary.json");
    assert!(summary_path.exists(), "missing {}", summary_path.display());

    let summary_text = std::fs::read_to_string(&summary_path).expect("read lab_summary.json");
    let summary: serde_json::Value =
        serde_json::from_str(&summary_text).expect("parse lab_summary.json");

    assert_eq!(summary.get("labbook_version").and_then(|v| v.as_u64()), Some(1));
    assert_eq!(summary.get("driver").and_then(|v| v.as_str()), Some("pw_runner"));
    assert_eq!(
        summary.get("profile").and_then(|v| v.as_str()),
        Some("PWRunner")
    );

    let steps = summary.get("steps").and_then(|v| v.as_array()).cloned().unwrap_or_default();
    assert_eq!(steps.len(), 1, "expected 1 step, got {}", steps.len());
    let step = &steps[0];
    assert_eq!(
        step.get("sandbox_check_outcome").and_then(|v| v.as_str()),
        Some("deny")
    );
}

