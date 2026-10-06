//! External runner management commands.
//!
//! These subcommands install, verify, and list external runners in the local
//! registry. They also generate launchd plists to register Mach services.

use serde::Serialize;
use serde_json::{Value, json};
use std::collections::BTreeMap;
use std::ffi::OsString;
use std::path::{Path, PathBuf};

use crate::app_layout::{BUNDLE_VALIDATOR_REL, BUNDLE_WORKER_REL};
use crate::bundle::read_bundle_info;
use crate::json_contract;
use crate::runner_client::run_pw_runner_client;
use crate::runner_manager::{
    self, RunnerKind, RunnerOwnership, RunnerRecord, RunnerRegistry, RunnerScope, RunnerState,
};
use crate::runner_select::{RunnerConnectionKind, infer_record_kind};
use crate::utils::now_unix_ms;

#[derive(Serialize)]
struct RunnerInstallData {
    state: RunnerState,
    loaded: runner_manager::ServiceObservation,
    runner: RunnerRecord,
    plist_path: String,
    bootstrapped: bool,
}

#[derive(Serialize)]
struct RunnerVerifyData {
    state: RunnerState,
    runner_id: Option<String>,
    service_name: String,
    runner_pid: Option<i64>,
    normalized_outcome: String,
}

#[derive(Serialize)]
struct RunnerValidateData {
    updated: usize,
    missing: usize,
    /// Records with at least one verification or read-back failure, and the
    /// failures themselves, naming the record and the binary.
    invalid: usize,
    failures: Vec<runner_manager::ValidateFailure>,
}

#[derive(Serialize)]
struct RunnerNotFoundData {
    #[serde(skip_serializing_if = "Option::is_none")]
    requested_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    requested_service_name: Option<String>,
}

/// Emit a `not_found` envelope for a runner-lookup miss and return exit code 2.
///
/// `kind` should match the envelope kind the caller would have emitted on
/// success (e.g. `runner_remove`), so consumers can dispatch by kind and then
/// branch on `result.normalized_outcome`.
fn emit_runner_not_found(
    kind: &str,
    requested_id: Option<&str>,
    requested_service_name: Option<&str>,
) -> Result<i32, String> {
    let data = RunnerNotFoundData {
        requested_id: requested_id.map(str::to_string),
        requested_service_name: requested_service_name.map(str::to_string),
    };
    let result = json_contract::JsonResult {
        ok: false,
        rc: None,
        exit_code: Some(2),
        normalized_outcome: Some("not_found".to_string()),
        errno: None,
        error: Some("runner not found in registry".to_string()),
        stderr: None,
        stdout: None,
    };
    json_contract::print_envelope(kind, result, &data)?;
    Ok(2)
}

fn runner_usage() -> String {
    "\
usage:
  policy-witness runner install --bundle <path-to-xpc-bundle> [--kind byoxpc] [--service-name <name>] [--scope user|system]
                               [--identity <codesign-id>] [--entitlements <plist>]
                               [--allow-adhoc]
                               [--env KEY=VALUE]
                               [--skip-bootstrap]
  policy-witness runner list
  policy-witness runner status --id <runner-id> | --service-name <name>
  policy-witness runner verify --id <runner-id> | --service-name <name> [--timeout-ms <n>]
  policy-witness runner remove --id <runner-id> | --service-name <name> [--skip-bootout]
  policy-witness runner validate
  policy-witness runner reconcile
"
    .to_string()
}

fn load_registry_or_default() -> Result<(PathBuf, RunnerRegistry), String> {
    let registry_path = runner_manager::runner_registry_path()?;
    let registry = runner_manager::load_registry(&registry_path)?;
    Ok((registry_path, registry))
}

fn cmd_runner_install(args: &[OsString]) -> Result<i32, String> {
    let mut bundle_path: Option<PathBuf> = None;
    let mut service_name: Option<String> = None;
    let mut scope = RunnerScope::User;
    let mut identity: Option<String> = None;
    let mut entitlements_path: Option<PathBuf> = None;
    let mut executable_override: Option<PathBuf> = None;
    let mut bundle_id_override: Option<String> = None;
    let mut kind_override: Option<RunnerKind> = None;
    let mut allow_adhoc = false;
    let mut skip_bootstrap = false;
    let mut env: BTreeMap<String, String> = BTreeMap::new();

    let mut idx = 0;
    while idx < args.len() {
        let arg = args[idx].to_string_lossy();
        match arg.as_ref() {
            "--bundle" => {
                let path = args
                    .get(idx + 1)
                    .ok_or_else(|| "missing value for --bundle".to_string())?;
                bundle_path = Some(PathBuf::from(path));
                idx += 2;
            }
            "--service-name" => {
                let name = args
                    .get(idx + 1)
                    .ok_or_else(|| "missing value for --service-name".to_string())?;
                service_name = Some(name.to_string_lossy().to_string());
                idx += 2;
            }
            "--scope" => {
                let value = args
                    .get(idx + 1)
                    .ok_or_else(|| "missing value for --scope".to_string())?;
                let scope_str = value.to_string_lossy();
                scope = RunnerScope::parse(scope_str.as_ref())
                    .ok_or_else(|| "invalid value for --scope".to_string())?;
                idx += 2;
            }
            "--identity" => {
                let value = args
                    .get(idx + 1)
                    .ok_or_else(|| "missing value for --identity".to_string())?;
                identity = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--entitlements" => {
                let path = args
                    .get(idx + 1)
                    .ok_or_else(|| "missing value for --entitlements".to_string())?;
                entitlements_path = Some(PathBuf::from(path));
                idx += 2;
            }
            "--executable" => {
                let path = args
                    .get(idx + 1)
                    .ok_or_else(|| "missing value for --executable".to_string())?;
                executable_override = Some(PathBuf::from(path));
                idx += 2;
            }
            "--bundle-id" => {
                let value = args
                    .get(idx + 1)
                    .ok_or_else(|| "missing value for --bundle-id".to_string())?;
                bundle_id_override = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--kind" => {
                let value = args
                    .get(idx + 1)
                    .ok_or_else(|| "missing value for --kind".to_string())?;
                let raw = value.to_string_lossy();
                if raw == "machme" {
                    return Err("--kind machme is not supported; use --kind byoxpc".to_string());
                }
                let kind = RunnerKind::parse(raw.as_ref())
                    .ok_or_else(|| format!("invalid value for --kind: {raw}"))?;
                if matches!(kind, RunnerKind::Standard) {
                    return Err(format!(
                        "runner install does not accept kind={}",
                        kind.as_str()
                    ));
                }
                kind_override = Some(kind);
                idx += 2;
            }
            "--allow-adhoc" => {
                allow_adhoc = true;
                idx += 1;
            }
            "--env" => {
                let value = args
                    .get(idx + 1)
                    .ok_or_else(|| "missing value for --env".to_string())?;
                let raw = value.to_string_lossy();
                let (key, val) = raw
                    .split_once('=')
                    .ok_or_else(|| "invalid --env (expected KEY=VALUE)".to_string())?;
                if key.is_empty() {
                    return Err("invalid --env (empty key)".to_string());
                }
                env.insert(key.to_string(), val.to_string());
                idx += 2;
            }
            "--skip-bootstrap" => {
                skip_bootstrap = true;
                idx += 1;
            }
            _ => return Err(format!("unknown argument: {arg}")),
        }
    }

    let bundle_path = bundle_path.ok_or_else(|| "missing --bundle".to_string())?;
    let bundle_path = std::fs::canonicalize(&bundle_path)
        .map_err(|e| format!("bundle path not found: {}: {e}", bundle_path.display()))?;
    if !bundle_path.exists() {
        return Err(format!("bundle path not found: {}", bundle_path.display()));
    }

    // byoxpc is the only kind `runner install` accepts. The CLI parser above
    // already rejects standard; here we accept an explicit
    // `--kind byoxpc` and otherwise default to it, and reject anything that
    // somehow surfaced as a different variant (defensive).
    let kind = kind_override.unwrap_or(RunnerKind::Byoxpc);
    if !matches!(kind, RunnerKind::Byoxpc) {
        return Err(format!(
            "runner install does not accept kind={}",
            kind.as_str()
        ));
    }

    if bundle_id_override.is_some() {
        return Err("external runners use CFBundleIdentifier; remove --bundle-id".to_string());
    }
    if executable_override.is_some() {
        return Err("external runners do not accept --executable; \
             the binary is derived from <bundle>/Contents/MacOS/<CFBundleExecutable>"
            .to_string());
    }

    if !bundle_path.is_dir() {
        return Err(
            "external runners require a `.xpc` bundle directory (not a plain binary); \
             pass --bundle <path-to-PWRunner.xpc>"
                .to_string(),
        );
    }
    let bundle_info = read_bundle_info(&bundle_path).map_err(|e| {
        format!(
            "failed to read {}/Contents/Info.plist: {e}",
            bundle_path.display()
        )
    })?;
    if bundle_info.package_type.as_deref() != Some("XPC!") {
        return Err(format!(
            "external runners require CFBundlePackageType=XPC! in Info.plist (got {:?})",
            bundle_info.package_type.as_deref().unwrap_or("absent")
        ));
    }

    let bundle_id = bundle_info.bundle_id.clone();
    let executable_path = bundle_path
        .join("Contents")
        .join("MacOS")
        .join(&bundle_info.executable);
    if !executable_path.exists() {
        return Err(format!(
            "executable path not found: {}",
            executable_path.display()
        ));
    }

    // The XPC bundle is the launchctl target and the enclosing seal. The
    // embedded worker and validator are signed first, as nested code, so the
    // seal records their hashes and the worker holds the supplied
    // entitlements; see `sign_install_tree`.
    let sign_target = bundle_path.clone();

    // Resolve the service name early so we can fail fast on registry conflicts
    // before touching codesign, launchd, or the on-disk plist. byoxpc's
    // service name must equal the bundle's CFBundleIdentifier — that's how
    // launchd routes Mach service lookups to the XPC service host.
    let runner_id = runner_manager::random_id()?;
    if let Some(requested) = service_name.as_ref() {
        if requested != &bundle_id {
            return Err(format!(
                "byoxpc service name must match CFBundleIdentifier ({bundle_id})"
            ));
        }
    }
    let service_name = bundle_id.clone();
    let bundle_id = Some(bundle_id);

    let registry_path = runner_manager::runner_registry_path()?;
    let _registry_lock = runner_manager::lock_registry(&registry_path)?;
    let mut registry = runner_manager::load_registry(&registry_path)?;
    if let Some(existing) = runner_manager::conflicting_record(
        &registry,
        &service_name,
        &bundle_path.to_string_lossy(),
        &executable_path.to_string_lossy(),
    ) {
        return Err(format!(
            "service name '{}' is already registered as runner '{}'; run \
             `policy-witness runner remove --service-name {}` to remove it first",
            existing.service_name, existing.id, existing.service_name
        ));
    }

    let plist_path = runner_manager::launchd_plist_path(&service_name, scope)?;
    match std::fs::symlink_metadata(&plist_path) {
        Ok(_) => {
            return Err(format!(
                "launchd plist already exists: {}; inspect runner reconcile",
                plist_path.display()
            ));
        }
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => (),
        Err(e) => return Err(format!("cannot inspect launchd plist: {e}")),
    }
    // Re-sign the bundle tree when the caller supplied a signing flag. The
    // two modes are:
    //   --identity <id>      : sign with the named identity, optionally
    //                          embedding --entitlements.
    //   --allow-adhoc + --entitlements : ad-hoc re-sign so the embedded
    //                                    entitlements actually match the
    //                                    plist (registry would otherwise lie).
    // Either way the embedded worker receives the entitlements and the
    // validator the identity alone, before the enclosing bundle is sealed.
    // Passing --entitlements without either flag silently used to leave the
    // existing signature untouched; that footgun is now rejected.
    if let Some(identity) = identity.as_ref() {
        runner_manager::sign_install_tree(
            &sign_target,
            identity,
            entitlements_path.as_deref(),
            &mut runner_manager::codesign_sign,
        )?;
    } else if allow_adhoc && entitlements_path.is_some() {
        runner_manager::sign_install_tree(
            &sign_target,
            "-",
            entitlements_path.as_deref(),
            &mut runner_manager::codesign_sign,
        )?;
    } else if entitlements_path.is_some() {
        return Err(
            "--entitlements requires --identity <id> or --allow-adhoc to re-sign the binary; \
             without one of those the supplied entitlements would not be embedded"
                .to_string(),
        );
    }
    runner_manager::codesign_verify(&sign_target)?;
    let signature = runner_manager::codesign_metadata(&executable_path)?;
    if signature.adhoc && !allow_adhoc {
        return Err("runner is ad-hoc signed; pass --allow-adhoc to accept".to_string());
    }

    // Always read entitlements from the binaries so the registry reflects what
    // the kernel will actually enforce, not what the caller's plist asked for.
    // The host, the worker and the validator are read back separately: the
    // worker is the process the specimen policy applies to.
    let entitlements = runner_manager::entitlements_from_codesign(&executable_path);
    let (worker_signature, worker_entitlements) =
        runner_manager::read_back(&bundle_path.join(BUNDLE_WORKER_REL))?;
    let (validator_signature, validator_entitlements) =
        runner_manager::read_back(&bundle_path.join(BUNDLE_VALIDATOR_REL))?;

    let plist_path = runner_manager::launchd_plist_path(&service_name, scope)?;
    if !env.contains_key("XPC_SERVICE_PATH") {
        // libxpc expects the bundle root for the XPC service when launching directly.
        env.insert(
            "XPC_SERVICE_PATH".to_string(),
            bundle_path.display().to_string(),
        );
    }
    let plist_contents = runner_manager::build_launchd_plist(
        &service_name,
        &executable_path,
        if env.is_empty() { None } else { Some(&env) },
        kind,
    );
    let record = RunnerRecord {
        state: RunnerState::Pending,
        ownership: Some(RunnerOwnership {
            plist_path: plist_path.to_string_lossy().into_owned(),
            launchd_domain: runner_manager::launchctl_target(scope)?,
            owner_uid: runner_manager::current_uid_string()?
                .parse()
                .map_err(|_| "invalid uid")?,
            plist_sha256: runner_manager::content_hash(plist_contents.as_bytes()),
        }),
        id: runner_id.clone(),
        service_name: service_name.clone(),
        bundle_path: bundle_path.display().to_string(),
        executable_path: executable_path.display().to_string(),
        bundle_id,
        scope,
        protocol_version: runner_manager::RUNNER_PROTOCOL_VERSION,
        signature,
        entitlements,
        installed_at_unix_ms: now_unix_ms(),
        kind: Some(kind),
        worker_signature: Some(worker_signature),
        worker_entitlements: Some(worker_entitlements),
        validator_signature: Some(validator_signature),
        validator_entitlements: Some(validator_entitlements),
    };

    let record = runner_manager::install_record(&registry_path, &mut registry, record, || {
        runner_manager::write_launchd_plist(&plist_path, &plist_contents)?;
        if !skip_bootstrap {
            runner_manager::launchctl_bootstrap(scope, &plist_path)?;
        }
        Ok(())
    })?;
    let loaded =
        runner_manager::inspect_service(&runner_manager::launchctl_target(scope)?, &service_name);

    let data = RunnerInstallData {
        state: record.state,
        loaded,
        runner: record,
        plist_path: plist_path.display().to_string(),
        bootstrapped: !skip_bootstrap,
    };
    let result = json_contract::JsonResult {
        ok: true,
        rc: None,
        exit_code: Some(0),
        normalized_outcome: Some("ok".to_string()),
        errno: None,
        error: None,
        stderr: None,
        stdout: None,
    };
    json_contract::print_envelope("runner_install", result, &data)?;
    Ok(0)
}

fn cmd_runner_list() -> Result<i32, String> {
    let (_, registry) = load_registry_or_default()?;
    let result = json_contract::JsonResult {
        ok: true,
        rc: None,
        exit_code: Some(0),
        normalized_outcome: Some("ok".to_string()),
        errno: None,
        error: None,
        stderr: None,
        stdout: None,
    };
    json_contract::print_envelope("runner_registry", result, &registry)?;
    Ok(0)
}

fn cmd_runner_status(args: &[OsString]) -> Result<i32, String> {
    let mut runner_id: Option<String> = None;
    let mut service_name: Option<String> = None;

    let mut idx = 0;
    while idx < args.len() {
        let arg = args[idx].to_string_lossy();
        match arg.as_ref() {
            "--id" => {
                let value = args
                    .get(idx + 1)
                    .ok_or_else(|| "missing value for --id".to_string())?;
                runner_id = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--service-name" => {
                let value = args
                    .get(idx + 1)
                    .ok_or_else(|| "missing value for --service-name".to_string())?;
                service_name = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            _ => return Err(format!("unknown argument: {arg}")),
        }
    }

    let (_, registry) = load_registry_or_default()?;
    let record = if let Some(id) = runner_id.as_ref() {
        registry.runners.iter().find(|r| &r.id == id)
    } else if let Some(service) = service_name.as_ref() {
        registry.runners.iter().find(|r| &r.service_name == service)
    } else {
        return Err("runner status requires --id or --service-name".to_string());
    };

    let record = match record {
        Some(record) => record,
        None => {
            return emit_runner_not_found(
                "runner_status",
                runner_id.as_deref(),
                service_name.as_deref(),
            );
        }
    };

    let result = json_contract::JsonResult {
        ok: true,
        rc: None,
        exit_code: Some(0),
        normalized_outcome: Some("ok".to_string()),
        errno: None,
        error: None,
        stderr: None,
        stdout: None,
    };
    json_contract::print_envelope("runner_status", result, record)?;
    Ok(0)
}

/// `runner verify` is meant to be a fast health check — most integrators call
/// it defensively in teardown loops where a 4-minute default (the value used
/// by `policy-witness run`) hangs the wrapper when the agent is gone. Keep
/// the default short; callers waiting on a real cold-spawn can pass
/// `--timeout-ms` explicitly.
const RUNNER_VERIFY_DEFAULT_TIMEOUT_MS: u64 = 5_000;

/// The fixed verification specimen: an allow-all policy with no probe steps.
fn verify_request() -> Value {
    json!({
        "schema_version": crate::json_contract::REQUEST_SCHEMA_VERSION,
        "specimen_id": "runner_verify",
        "run_kind": "runner_verify",
        "policy": {
            "format": "sbpl",
            "sbpl_source": "(version 1)\n(allow default)\n"
        },
        "probe_plan": []
    })
}

/// The verification projection of a received reply: its PID and outcome are
/// read only under the current response schema. Another or a malformed version
/// is reported as the corresponding controller outcome with a null PID, never
/// read under other rules.
fn project_verify_reply(runner_result: Option<&Value>) -> (Option<i64>, String) {
    match runner_result.map(crate::run_flow::reply_version) {
        None => (None, "runner_output_not_json".to_string()),
        Some(crate::run_flow::ReplyVersion::Supported) => (
            runner_result
                .and_then(|v| v.get("pid"))
                .and_then(|v| v.as_i64()),
            runner_result
                .and_then(|v| v.get("normalized_outcome"))
                .and_then(|v| v.as_str())
                .unwrap_or("runner_output_not_json")
                .to_string(),
        ),
        Some(crate::run_flow::ReplyVersion::Unsupported(_)) => {
            (None, "unsupported_runner_response".to_string())
        }
        Some(crate::run_flow::ReplyVersion::Malformed(_)) => {
            (None, "malformed_runner_response".to_string())
        }
    }
}

fn cmd_runner_verify(args: &[OsString]) -> Result<i32, String> {
    let mut runner_id: Option<String> = None;
    let mut service_name: Option<String> = None;
    let mut timeout_ms: u64 = RUNNER_VERIFY_DEFAULT_TIMEOUT_MS;

    let mut idx = 0;
    while idx < args.len() {
        let arg = args[idx].to_string_lossy();
        match arg.as_ref() {
            "--id" => {
                let value = args
                    .get(idx + 1)
                    .ok_or_else(|| "missing value for --id".to_string())?;
                runner_id = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--service-name" => {
                let value = args
                    .get(idx + 1)
                    .ok_or_else(|| "missing value for --service-name".to_string())?;
                service_name = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--timeout-ms" => {
                let value = args
                    .get(idx + 1)
                    .and_then(|s| s.to_string_lossy().parse::<u64>().ok())
                    .ok_or_else(|| "invalid value for --timeout-ms".to_string())?;
                timeout_ms = value.max(1);
                idx += 2;
            }
            _ => return Err(format!("unknown argument: {arg}")),
        }
    }

    let (_, registry) = load_registry_or_default()?;
    let record = if let Some(id) = runner_id.as_ref() {
        registry.runners.iter().find(|r| &r.id == id)
    } else if let Some(service) = service_name.as_ref() {
        registry.runners.iter().find(|r| &r.service_name == service)
    } else {
        return Err("runner verify requires --id or --service-name".to_string());
    };

    let record = match record {
        Some(record) => record,
        None => {
            return emit_runner_not_found(
                "runner_verify",
                runner_id.as_deref(),
                service_name.as_deref(),
            );
        }
    };

    // The held verification request, delivered on the client's stdin like a
    // run's request; no temporary file is written.
    let held = serde_json::to_string_pretty(&verify_request())
        .map_err(|e| format!("failed to encode verify request: {e}"))?;

    let record_kind = infer_record_kind(record);
    let connection = match record_kind {
        RunnerKind::Byoxpc => RunnerConnectionKind::MachService {
            privileged: matches!(record.scope, RunnerScope::System),
        },
        RunnerKind::Standard => {
            return Err("external runners cannot be built-in kinds".to_string());
        }
    };
    let (_, runner_result) =
        run_pw_runner_client(&record.service_name, &held, timeout_ms, &connection)?;
    let (runner_pid, outcome) = project_verify_reply(runner_result.as_ref());

    let ok = outcome == "ok";
    let data = RunnerVerifyData {
        state: record.state,
        runner_id: Some(record.id.clone()),
        service_name: record.service_name.clone(),
        runner_pid,
        normalized_outcome: outcome.clone(),
    };
    let result = json_contract::JsonResult {
        ok,
        rc: None,
        exit_code: Some(if ok { 0 } else { 1 }),
        normalized_outcome: Some(outcome),
        errno: None,
        error: None,
        stderr: None,
        stdout: None,
    };
    json_contract::print_envelope("runner_verify", result, &data)?;
    Ok(if ok { 0 } else { 1 })
}

fn cmd_runner_remove(args: &[OsString]) -> Result<i32, String> {
    let mut runner_id: Option<String> = None;
    let mut service_name: Option<String> = None;
    let mut skip_bootout = false;

    let mut idx = 0;
    while idx < args.len() {
        let arg = args[idx].to_string_lossy();
        match arg.as_ref() {
            "--id" => {
                let value = args
                    .get(idx + 1)
                    .ok_or_else(|| "missing value for --id".to_string())?;
                runner_id = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--service-name" => {
                let value = args
                    .get(idx + 1)
                    .ok_or_else(|| "missing value for --service-name".to_string())?;
                service_name = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--skip-bootout" => {
                skip_bootout = true;
                idx += 1;
            }
            _ => return Err(format!("unknown argument: {arg}")),
        }
    }

    let registry_path = runner_manager::runner_registry_path()?;
    let _registry_lock = runner_manager::lock_registry(&registry_path)?;
    let mut registry = runner_manager::load_registry(&registry_path)?;
    if runner_id.is_none() && service_name.is_none() {
        return Err("runner remove requires --id or --service-name".to_string());
    }
    let Some(data) = runner_manager::remove_record(
        &registry_path,
        &mut registry,
        runner_id.as_deref(),
        service_name.as_deref(),
        skip_bootout,
        &mut runner_manager::NativeCleanup,
    )?
    else {
        return emit_runner_not_found(
            "runner_remove",
            runner_id.as_deref(),
            service_name.as_deref(),
        );
    };
    let result = json_contract::JsonResult {
        ok: true,
        rc: None,
        exit_code: Some(0),
        normalized_outcome: Some("ok".to_string()),
        errno: None,
        error: None,
        stderr: None,
        stdout: None,
    };
    json_contract::print_envelope("runner_remove", result, &data)?;
    Ok(0)
}

/// Walk the registry, verify each runner's bundle recursively and re-read
/// the host's, the worker's and the validator's on-disk signatures and
/// entitlements, reporting which failed. This is *registry-internal*
/// validation — it does not reconcile against launchctl or LaunchAgents/.
/// Callers wanting that use the report-only reconcile command.
fn cmd_runner_validate() -> Result<i32, String> {
    let registry_path = runner_manager::runner_registry_path()?;
    let _registry_lock = runner_manager::lock_registry(&registry_path)?;
    let mut registry = runner_manager::load_registry(&registry_path)?;
    let mut missing = 0usize;
    let mut invalid = 0usize;
    let mut failures = Vec::new();
    for record in registry.runners.iter_mut() {
        let exec_path = Path::new(&record.executable_path);
        if !exec_path.exists() {
            missing += 1;
            record.signature.valid = false;
            record.entitlements.error = Some("executable missing".to_string());
            continue;
        }
        let found = runner_manager::validate_record(
            record,
            &runner_manager::codesign_verify,
            &runner_manager::codesign_verify_binary,
            &runner_manager::read_back,
        );
        if !found.is_empty() {
            invalid += 1;
            failures.extend(found);
        }
        if record.kind.is_none() {
            record.kind = Some(infer_record_kind(record));
        }
    }
    let updated = registry.runners.len();
    runner_manager::save_registry(&registry_path, &registry)?;

    let data = RunnerValidateData {
        updated,
        missing,
        invalid,
        failures,
    };
    let result = json_contract::JsonResult {
        ok: true,
        rc: None,
        exit_code: Some(0),
        normalized_outcome: Some("ok".to_string()),
        errno: None,
        error: None,
        stderr: None,
        stdout: None,
    };
    json_contract::print_envelope("runner_validate", result, &data)?;
    Ok(0)
}

fn cmd_runner_reconcile() -> Result<i32, String> {
    let (path, registry) = load_registry_or_default()?;
    let mut records = Vec::new();
    let mut candidates = Vec::new();
    let mut inspection_errors = Vec::new();
    for (state, record) in registry
        .runners
        .iter()
        .map(|r| {
            (
                match r.state {
                    RunnerState::Pending => "pending",
                    RunnerState::Installed => "installed",
                },
                r,
            )
        })
        .chain(
            registry
                .pending_cleanup
                .iter()
                .map(|r| ("pending_cleanup", &r.runner)),
        )
    {
        let observation = match runner_manager::record_location(record) {
            Ok((plist_path, domain)) => {
                let service = runner_manager::inspect_service(&domain, &record.service_name);
                let plist = runner_manager::inspect_plist(&plist_path);
                json!({"recorded_state":state, "runner":record, "plist_path":plist_path, "launchd_domain":domain,
                    "service_ownership":runner_manager::service_ownership(record, &service),
                    "plist_ownership":runner_manager::plist_ownership(record, &plist),
                    "service":service, "plist":plist})
            }
            Err(error) => {
                json!({"recorded_state":state, "runner":record, "service":{"presence":"unknown"},
                "plist":{"presence":"unknown"}, "ownership":"unknown", "error":error})
            }
        };
        records.push(observation);
    }
    let mut directories = vec![(RunnerScope::System, PathBuf::from("/Library/LaunchDaemons"))];
    match runner_manager::launchd_plist_path("placeholder", RunnerScope::User) {
        Ok(path) => directories.push((
            RunnerScope::User,
            path.parent().expect("plist parent").to_path_buf(),
        )),
        Err(error) => inspection_errors.push(json!({"presence":"unknown", "error":error})),
    }
    for (scope, directory) in directories {
        let entries = match std::fs::read_dir(&directory) {
            Ok(entries) => entries,
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => continue,
            Err(error) => {
                inspection_errors.push(
                    json!({"path":directory, "presence":"unknown", "error":error.to_string()}),
                );
                continue;
            }
        };
        for entry in entries {
            let entry = match entry {
                Ok(entry) => entry,
                Err(error) => {
                    inspection_errors.push(
                        json!({"path":directory, "presence":"unknown", "error":error.to_string()}),
                    );
                    continue;
                }
            };
            let plist_path = entry.path();
            if plist_path.extension().and_then(|v| v.to_str()) != Some("plist") {
                continue;
            }
            let plist = runner_manager::inspect_plist(&plist_path);
            if let Some(error) = &plist.error {
                inspection_errors
                    .push(json!({"path":plist_path,"presence":"unknown","error":error}));
            }
            let config = plist.config.as_ref();
            let label = config.and_then(|c| c.get("Label")).and_then(|v| v.as_str());
            let executable = config
                .and_then(|c| {
                    c.pointer("/ProgramArguments/0")
                        .or_else(|| c.get("Program"))
                })
                .and_then(|v| v.as_str());
            let candidate = label.is_some_and(|l| l.starts_with("com.policywitness."))
                || executable.is_some_and(|p| {
                    Path::new(p).file_name().and_then(|n| n.to_str()) == Some("PWRunner")
                })
                || (config.is_none()
                    && plist_path
                        .file_name()
                        .is_some_and(|n| n.to_string_lossy().starts_with("com.policywitness.")));
            if !candidate {
                continue;
            }
            let registered = registry
                .runners
                .iter()
                .chain(registry.pending_cleanup.iter().map(|c| &c.runner))
                .any(|r| label == Some(r.service_name.as_str()) && r.scope == scope);
            if registered {
                continue;
            }
            let service = label.and_then(|label| {
                runner_manager::launchctl_target(scope)
                    .ok()
                    .map(|domain| runner_manager::inspect_service(&domain, label))
            });
            candidates.push(json!({"recorded_state":"unregistered", "scope":scope, "service_name":label,
                "executable_path":executable, "plist_path":plist_path, "service":service, "plist":plist,
                "ownership":if config.is_none() {"unknown"} else if label.is_none() || executable.is_none() {"ambiguous"} else {"unowned"}}));
        }
    }
    let data = json!({"registry_path":path, "records":records, "candidates":candidates, "inspection_errors":inspection_errors});
    let result = json_contract::JsonResult {
        ok: true,
        rc: None,
        exit_code: Some(0),
        normalized_outcome: Some("ok".into()),
        errno: None,
        error: None,
        stderr: None,
        stdout: None,
    };
    json_contract::print_envelope("runner_reconcile", result, &data)?;
    Ok(0)
}

pub fn cmd_runner(args: &[OsString]) -> Result<i32, String> {
    if args.is_empty() {
        return Err(format!("missing runner command\n\n{}", runner_usage()));
    }
    let sub = args[0].to_string_lossy().to_string();
    let rest = &args[1..];
    match sub.as_str() {
        "install" => cmd_runner_install(rest),
        "list" => cmd_runner_list(),
        "status" => cmd_runner_status(rest),
        "verify" => cmd_runner_verify(rest),
        "remove" => cmd_runner_remove(rest),
        "validate" => cmd_runner_validate(),
        "reconcile" => {
            if !rest.is_empty() {
                return Err("runner reconcile accepts no arguments".into());
            }
            cmd_runner_reconcile()
        }
        "-h" | "--help" | "help" => {
            println!("{}", runner_usage());
            Ok(0)
        }
        _ => Err(format!(
            "unknown runner command: {sub}\n\n{}",
            runner_usage()
        )),
    }
}

#[cfg(test)]
mod verify_tests {
    use super::*;

    #[test]
    fn verification_default_wait_is_five_seconds() {
        assert_eq!(RUNNER_VERIFY_DEFAULT_TIMEOUT_MS, 5_000);
    }

    #[test]
    fn verification_request_is_the_fixed_allow_all_specimen() {
        let request = verify_request();
        assert_eq!(
            request["schema_version"],
            crate::json_contract::REQUEST_SCHEMA_VERSION
        );
        assert_eq!(request["probe_plan"], json!([]));
        assert_eq!(request["run_kind"], "runner_verify");
        assert_eq!(request["specimen_id"], "runner_verify");
        assert_eq!(request["policy"]["format"], "sbpl");
        // Delivered as one held string; the client reads it from stdin.
        let held = serde_json::to_string_pretty(&request).unwrap();
        assert_eq!(serde_json::from_str::<Value>(&held).unwrap(), request);
    }

    #[test]
    fn verification_launch_failure_is_an_error() {
        // A unit-test binary has no embedded client beside it: launch fails
        // before any reply exists and the error carries the tool's name.
        let error = match run_pw_runner_client(
            "controlled.service",
            "{}",
            1,
            &RunnerConnectionKind::XpcService,
        ) {
            Ok(_) => panic!("a missing client cannot be invoked"),
            Err(error) => error,
        };
        assert!(error.contains("pw-runner-client"), "{error}");
    }

    #[test]
    fn verification_projects_only_current_replies() {
        let current = i64::from(crate::json_contract::RESPONSE_SCHEMA_VERSION);
        assert_eq!(
            project_verify_reply(None),
            (None, "runner_output_not_json".to_string())
        );
        assert_eq!(
            project_verify_reply(Some(
                &json!({"schema_version": current, "pid": 77, "normalized_outcome": "ok"})
            )),
            (Some(77), "ok".to_string())
        );
        assert_eq!(
            project_verify_reply(Some(&json!({"schema_version": current, "pid": 77}))),
            (Some(77), "runner_output_not_json".to_string())
        );
        for other in [current - 1, current + 1] {
            assert_eq!(
                project_verify_reply(Some(
                    &json!({"schema_version": other, "pid": 77, "normalized_outcome": "ok"})
                )),
                (None, "unsupported_runner_response".to_string())
            );
        }
        for malformed in [
            json!({"pid": 77, "normalized_outcome": "ok"}),
            json!({"schema_version": current.to_string(), "pid": 77, "normalized_outcome": "ok"}),
        ] {
            assert_eq!(
                project_verify_reply(Some(&malformed)),
                (None, "malformed_runner_response".to_string())
            );
        }
    }
}
