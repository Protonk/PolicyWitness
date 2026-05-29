//! CLI contract integration tests for the controller binary.
//!
//! These tests run the built dist/PolicyWitness.app to validate the end-to-end
//! envelope shape and instrumentation injection behavior. They are gated behind
//! PW_INTEGRATION=1 so `cargo test --tests` can run without a built app.

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
    repo_root()
        .join("dist")
        .join("PolicyWitness.app")
        .join("Contents")
        .join("MacOS")
        .join("policy-witness")
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

fn sbpl_preflight_bin_path() -> PathBuf {
    repo_root()
        .join("dist")
        .join("PolicyWitness.app")
        .join("Contents")
        .join("MacOS")
        .join("sbpl-preflight")
}

fn require_sbpl_preflight_bin() -> PathBuf {
    let path = sbpl_preflight_bin_path();
    if !path.exists() {
        panic!(
            "dist/PolicyWitness.app sbpl-preflight not found at {} (run `make build`)",
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

    // Sandboxed harnesses can block XPC lookup or unified log access; rerun from
    // a normal Terminal if failures look environment-related.

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

#[test]
fn instrumentation_injects_by_flag() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();

    let specimen = repo_root()
        .join("tests")
        .join("fixtures")
        .join("pw_runner")
        .join("specimen_file_read_deny.json");
    assert!(specimen.exists(), "missing specimen fixture: {}", specimen.display());

    let instrumentation = repo_root()
        .join("tests")
        .join("fixtures")
        .join("instrumentation")
        .join("debug_wait.json");
    assert!(
        instrumentation.exists(),
        "missing instrumentation fixture: {}",
        instrumentation.display()
    );

    let out = run_pw(
        &bin,
        &[
            "run",
            "--instrumentation",
            instrumentation.to_str().expect("instrumentation path utf8"),
            specimen.to_str().expect("specimen path utf8"),
        ],
    );

    assert!(
        out.status.success(),
        "instrumentation run failed: rc={:?}\nstderr:\n{}\nstdout:\n{}",
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
    let inst = runner
        .get("instrumentation")
        .cloned()
        .expect("missing runner_result.instrumentation");
    let ports = inst
        .get("ports")
        .and_then(|v| v.as_array())
        .cloned()
        .unwrap_or_default();
    assert!(!ports.is_empty(), "expected instrumentation ports");
    let port = &ports[0];
    assert_eq!(
        port.get("kind").and_then(|v| v.as_str()),
        Some("debug_wait")
    );
    assert_eq!(
        port.get("status").and_then(|v| v.as_str()),
        Some("ok")
    );
}

#[test]
fn instrumentation_rejects_existing() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();

    let specimen = repo_root()
        .join("tests")
        .join("fixtures")
        .join("pw_runner")
        .join("specimen_instrumentation_debug_wait.json");
    assert!(specimen.exists(), "missing specimen fixture: {}", specimen.display());

    let instrumentation = repo_root()
        .join("tests")
        .join("fixtures")
        .join("instrumentation")
        .join("debug_wait.json");
    assert!(
        instrumentation.exists(),
        "missing instrumentation fixture: {}",
        instrumentation.display()
    );

    let out = run_pw(
        &bin,
        &[
            "run",
            "--instrumentation",
            instrumentation.to_str().expect("instrumentation path utf8"),
            specimen.to_str().expect("specimen path utf8"),
        ],
    );

    assert!(
        !out.status.success(),
        "expected failure when instrumentation already present"
    );
    assert_eq!(out.status.code(), Some(2));

    let stdout = String::from_utf8_lossy(&out.stdout);
    let envelope: serde_json::Value = serde_json::from_str(&stdout).expect("parse run envelope");
    assert_eq!(
        envelope
            .get("result")
            .and_then(|v| v.get("normalized_outcome"))
            .and_then(|v| v.as_str()),
        Some("tool_error")
    );
    let error = envelope
        .get("result")
        .and_then(|v| v.get("error"))
        .and_then(|v| v.as_str())
        .unwrap_or("");
    assert!(
        error.contains("instrumentation"),
        "expected error to mention instrumentation (got {error:?})"
    );
}

#[test]
fn preflight_missing_params_returns_clean_outcome() {
    if !integration_enabled() {
        return;
    }
    let bin = require_sbpl_preflight_bin();

    let tmp = std::env::temp_dir().join(format!(
        "pw-preflight-missing-{}.json",
        std::process::id()
    ));
    let request = r#"{
        "policy": {
            "format": "sbpl",
            "sbpl_source": "(version 1)\n(deny default)\n(allow file-read-data (subpath (param \"HOME\")))\n"
        },
        "probe_plan": []
    }"#;
    std::fs::write(&tmp, request).expect("write preflight request");

    let out = run_pw(&bin, &["--request", tmp.to_str().expect("tmp path utf8")]);
    let _ = std::fs::remove_file(&tmp);

    assert_eq!(
        out.status.code(),
        Some(1),
        "expected exit code 1 (missing params); got {:?}\nstderr:\n{}",
        out.status.code(),
        String::from_utf8_lossy(&out.stderr)
    );

    let stdout = String::from_utf8_lossy(&out.stdout);
    let envelope: serde_json::Value =
        serde_json::from_str(&stdout).expect("parse preflight envelope");
    assert_eq!(
        envelope.get("kind").and_then(|v| v.as_str()),
        Some("sbpl_preflight")
    );
    assert_eq!(
        envelope
            .get("result")
            .and_then(|v| v.get("normalized_outcome"))
            .and_then(|v| v.as_str()),
        Some("missing_params"),
        "expected normalized_outcome=missing_params (envelope={envelope})"
    );

    let data = envelope.get("data").expect("missing data block");
    let missing: Vec<String> = data
        .get("params_missing")
        .and_then(|v| v.as_array())
        .map(|arr| {
            arr.iter()
                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                .collect()
        })
        .unwrap_or_default();
    assert_eq!(missing, vec!["HOME".to_string()]);

    let referenced: Vec<String> = data
        .get("params_referenced")
        .and_then(|v| v.as_array())
        .map(|arr| {
            arr.iter()
                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                .collect()
        })
        .unwrap_or_default();
    assert_eq!(referenced, vec!["HOME".to_string()]);

    // The libsandbox-side cryptic message must still be surfaced under
    // compile_error so the diagnostic is auditable.
    let compile_error = data
        .get("compile_error")
        .and_then(|v| v.as_str())
        .unwrap_or("");
    assert!(
        compile_error.contains("expected pattern"),
        "expected compile_error to still carry the libsandbox message (got {compile_error:?})"
    );
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
    assert!(specimen.exists(), "missing specimen fixture: {}", specimen.display());

    let out = run_pw(&bin, &["run", specimen.to_str().expect("specimen path utf8")]);
    assert!(
        out.status.success(),
        "specimen failed: rc={:?}\nstderr:\n{}\nstdout:\n{}",
        out.status.code(),
        String::from_utf8_lossy(&out.stderr),
        String::from_utf8_lossy(&out.stdout)
    );

    let stdout = String::from_utf8_lossy(&out.stdout);
    let envelope: serde_json::Value =
        serde_json::from_str(&stdout).expect("parse run envelope");

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
    assert_eq!(
        diag.get("data_volume_form").and_then(|v| v.as_str()),
        Some("/System/Volumes/Data/private/etc/hosts"),
        "data_volume_form should apply the /private heuristic"
    );
}

#[test]
fn sandbox_check_path_diagnostics_survives_strict_sandbox() {
    // Repro of the downstream report: under `(deny default)` the runner
    // worker can't stat /etc/hosts. The pre-RUNNER-RESHAPE-PLAN-Step-3
    // producer (worker-side) hit this stat block and emitted
    // realpath_resolved=null, relying on wellKnownSymlinksResolved as
    // the fallback for firmlink_resolved and data_volume_form. After
    // Step 3 the producer is host-side (unsandboxed), so
    // realpath_resolved is populated even under (deny default). Either
    // way, the derived forms must be present and correct — that is the
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
    assert!(specimen.exists(), "missing specimen fixture: {}", specimen.display());

    let out = run_pw(&bin, &["run", specimen.to_str().expect("specimen path utf8")]);
    assert!(
        out.status.success(),
        "specimen failed: rc={:?}\nstderr:\n{}\nstdout:\n{}",
        out.status.code(),
        String::from_utf8_lossy(&out.stderr),
        String::from_utf8_lossy(&out.stdout)
    );

    let stdout = String::from_utf8_lossy(&out.stdout);
    let envelope: serde_json::Value =
        serde_json::from_str(&stdout).expect("parse run envelope");
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

    // All four documented keys must be present (string or explicit null) so
    // consumers can distinguish "computed and the result was null" from
    // "field was not emitted at all".
    for key in ["input", "realpath_resolved", "firmlink_resolved", "data_volume_form"] {
        assert!(
            diag.contains_key(key),
            "path_diagnostics missing key {key:?}; got {diag:?}"
        );
    }

    assert_eq!(
        diag.get("input").and_then(|v| v.as_str()),
        Some("/etc/hosts")
    );
    // Whether realpath_resolved is populated is sandbox-dependent and not the
    // load-bearing assertion here — the derived forms must be present.
    assert_eq!(
        diag.get("firmlink_resolved").and_then(|v| v.as_str()),
        Some("/System/Volumes/Data/private/etc/hosts"),
        "firmlink_resolved must be derivable from the well-known symlink \
         substitution even when realpath(3) is blocked by the sandbox \
         (firmlinks map is warmed pre-sandbox and has a built-in fallback)"
    );
    assert_eq!(
        diag.get("data_volume_form").and_then(|v| v.as_str()),
        Some("/System/Volumes/Data/private/etc/hosts"),
        "data_volume_form must be populated for /etc paths via the \
         well-known symlink fallback"
    );
}

#[test]
fn sandbox_check_path_diagnostics_host_produces_realpath_under_strict_sandbox() {
    // Pins the Step 3 (R4) producer move: path_diagnostics is computed
    // by the unsandboxed runner host (PWRunnerService.enrichPathDiagnostics)
    // after the worker reports back. The host's realpath(3) is NOT
    // blocked by the worker's (deny default) policy, so realpath_resolved
    // is populated even when the worker itself couldn't stat the path.
    //
    // This is the positive assertion the survives_strict_sandbox test
    // deliberately avoided: a regression that moves path_diagnostics
    // computation back into the worker (or otherwise prevents host
    // realpath from running) silently breaks the Step-3 contract
    // without breaking the shape-only assertions above. This test
    // catches that.
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();

    let specimen = repo_root()
        .join("tests")
        .join("fixtures")
        .join("pw_runner")
        .join("specimen_path_diagnostics_strict.json");
    assert!(specimen.exists(), "missing specimen fixture: {}", specimen.display());

    let out = run_pw(&bin, &["run", specimen.to_str().expect("specimen path utf8")]);
    assert!(out.status.success(), "specimen failed");

    let envelope: serde_json::Value = serde_json::from_str(
        &String::from_utf8_lossy(&out.stdout)
    ).expect("parse run envelope");

    let realpath = envelope
        .pointer("/data/runner_result/steps/0/sandbox_check/path_diagnostics/realpath_resolved")
        .and_then(|v| v.as_str())
        .unwrap_or_else(|| panic!(
            "expected realpath_resolved to be a populated string under \
             (deny default) — the host should compute it without the \
             worker's sandbox restriction. Step 3 (R4) producer regression?"
        ));

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
fn preflight_records_import_provenance_for_system_sb() {
    if !integration_enabled() {
        return;
    }
    let bin = require_sbpl_preflight_bin();

    let tmp = std::env::temp_dir().join(format!(
        "pw-preflight-imports-{}.json",
        std::process::id()
    ));
    let request = r#"{
        "policy": {
            "format": "sbpl",
            "sbpl_source": "(version 1)\n(deny default)\n(import \"system.sb\")\n(allow file-read-data)\n"
        },
        "probe_plan": []
    }"#;
    std::fs::write(&tmp, request).expect("write preflight request");

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
        serde_json::from_str(&stdout).expect("parse preflight envelope");

    let data = envelope.get("data").expect("missing data block");
    let policy_sha = data
        .get("policy_sha256")
        .and_then(|v| v.as_str())
        .expect("policy_sha256 missing");
    let closure_sha = data
        .get("policy_closure_sha256")
        .and_then(|v| v.as_str())
        .expect("policy_closure_sha256 missing");
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

    let imports = data
        .get("imports")
        .and_then(|v| v.as_array())
        .expect("imports missing");
    assert!(
        imports.len() >= 1,
        "expected at least one resolved import, got {}",
        imports.len()
    );

    let system_sb = imports
        .iter()
        .find(|imp| imp.get("name").and_then(|v| v.as_str()) == Some("system.sb"))
        .expect("system.sb should be in imports");
    assert_eq!(
        system_sb
            .get("resolved_path")
            .and_then(|v| v.as_str()),
        Some("/System/Library/Sandbox/Profiles/system.sb"),
        "system.sb should resolve from the Profiles directory"
    );
    let sha = system_sb
        .get("sha256")
        .and_then(|v| v.as_str())
        .unwrap_or("");
    assert_eq!(sha.len(), 64, "sha256 should be a 64-char hex string");
}
