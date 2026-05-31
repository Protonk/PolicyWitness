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
             worker's sandbox restriction. Did path_diagnostics move \
             back into the worker?"
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
fn augment_applied_emits_policy_augmentation_block() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();

    // exec_baseline is shipped as a comment-only no-op in checkpoint 1.
    // Splicing it into a permissive policy must succeed end-to-end and
    // populate data.policy_augmentation with distinct original/applied
    // hashes.
    let tmp = std::env::temp_dir().join(format!(
        "pw-augment-applied-{}.json",
        std::process::id()
    ));
    let request = r#"{
        "schema_version": 1,
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
    // the policy_augmentation block but break preflight or the
    // runner — e.g. a future bug that forwards the augments key past
    // controller resolution would cause the runner to reject the
    // spec, and we'd still see policy_augmentation in the envelope.
    assert!(
        out.status.success(),
        "augmented run failed: rc={:?}\nstderr:\n{}\nstdout:\n{}",
        out.status.code(),
        String::from_utf8_lossy(&out.stderr),
        String::from_utf8_lossy(&out.stdout)
    );
    let stdout = String::from_utf8_lossy(&out.stdout);
    let envelope: serde_json::Value =
        serde_json::from_str(&stdout).expect("parse run envelope");
    assert_eq!(
        envelope
            .pointer("/result/normalized_outcome")
            .and_then(|v| v.as_str()),
        Some("ok"),
        "augmented run did not reach ok: envelope={envelope}"
    );

    let aug = envelope
        .pointer("/data/policy_augmentation")
        .cloned()
        .expect("data.policy_augmentation missing on augmented run");
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

    // Preflight must have run against the spliced source. Hard
    // assertion (not if-let) — a regression that runs preflight on
    // the pre-splice request would silently produce the wrong
    // compile report.
    let preflight_sha = envelope
        .pointer("/data/policy_preflight/policy_sha256")
        .and_then(|v| v.as_str())
        .expect("data.policy_preflight.policy_sha256 missing");
    assert_eq!(
        preflight_sha, applied_hash,
        "policy_preflight.policy_sha256 must equal applied_sha256 — preflight ran on the pre-splice source"
    );

    // The runner must have run against the spliced source. Hard
    // assertion catches a regression that forwards the original
    // request to the runner while still emitting policy_augmentation.
    let runner_sha = envelope
        .pointer("/data/runner_result/policy_sha256")
        .and_then(|v| v.as_str())
        .expect("data.runner_result.policy_sha256 missing — runner may not have been invoked");
    assert_eq!(
        runner_sha, applied_hash,
        "runner_result.policy_sha256 must equal applied_sha256 when augments are spliced"
    );
}

#[test]
fn unknown_augment_short_circuits_to_bad_request() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();

    let tmp = std::env::temp_dir().join(format!(
        "pw-augment-unknown-{}.json",
        std::process::id()
    ));
    let request = r#"{
        "schema_version": 1,
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

    let envelope: serde_json::Value = serde_json::from_str(&String::from_utf8_lossy(&out.stdout))
        .expect("parse run envelope");
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

    // Runner must NOT have been invoked. data.runner_result is null
    // and runner_client.argv carries the synthetic marker.
    assert!(
        envelope
            .pointer("/data/runner_result")
            .map(|v| v.is_null())
            .unwrap_or(true),
        "data.runner_result must be absent/null when augment resolution fails"
    );
    let argv: Vec<String> = envelope
        .pointer("/data/runner_client/argv")
        .and_then(|v| v.as_array())
        .map(|arr| {
            arr.iter()
                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                .collect()
        })
        .unwrap_or_default();
    assert_eq!(
        argv,
        vec!["(runner not invoked)".to_string()],
        "runner_client.argv should mark the runner as not invoked"
    );

    // data.policy_augmentation must be absent/null — we never produced
    // an applied list because resolution failed.
    assert!(
        envelope
            .pointer("/data/policy_augmentation")
            .map(|v| v.is_null())
            .unwrap_or(true),
        "data.policy_augmentation should be absent/null when augment resolution fails"
    );
}

#[test]
fn invalid_augment_name_rejected_as_bad_request() {
    if !integration_enabled() {
        return;
    }
    let bin = require_pw_bin();

    let tmp = std::env::temp_dir().join(format!(
        "pw-augment-invalid-{}.json",
        std::process::id()
    ));
    // "../etc/passwd" is the canonical traversal attempt; the resolver
    // must reject it for shape, not for whether the file exists.
    let request = r#"{
        "schema_version": 1,
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
    let envelope: serde_json::Value = serde_json::from_str(&String::from_utf8_lossy(&out.stdout))
        .expect("parse run envelope");
    assert_eq!(
        envelope
            .pointer("/result/normalized_outcome")
            .and_then(|v| v.as_str()),
        Some("bad_request")
    );
}

#[test]
fn absent_augments_omits_policy_augmentation_block() {
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
        serde_json::from_str(&String::from_utf8_lossy(&out.stdout))
            .expect("parse run envelope");
    let aug = envelope.pointer("/data/policy_augmentation");
    assert!(
        aug.map(|v| v.is_null()).unwrap_or(true),
        "data.policy_augmentation should be absent/null for a request without augments \
         (got {aug:?})"
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
