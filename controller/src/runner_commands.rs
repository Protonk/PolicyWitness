//! External runner management commands.
//!
//! These subcommands install, verify, and list external runners in the local
//! registry. They also generate launchd plists to register Mach services.

use serde::Serialize;
use serde_json::json;
use std::collections::BTreeMap;
use std::ffi::OsString;
use std::path::{Path, PathBuf};

use crate::bundle::read_bundle_info;
use crate::json_contract;
use crate::runner_client::run_pw_runner_client;
use crate::runner_manager::{self, RunnerKind, RunnerRecord, RunnerRegistry, RunnerScope};
use crate::runner_select::{infer_record_kind, RunnerConnectionKind};
use crate::utils::now_unix_ms;

#[derive(Serialize)]
struct RunnerInstallData {
    runner: RunnerRecord,
    plist_path: String,
    bootstrapped: bool,
}

#[derive(Serialize)]
struct RunnerRemoveData {
    runner_id: String,
    service_name: String,
    plist_path: String,
    booted_out: bool,
    plist_removed: bool,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    warnings: Vec<String>,
}

#[derive(Serialize)]
struct RunnerVerifyData {
    runner_id: Option<String>,
    service_name: String,
    runner_pid: Option<i64>,
    normalized_outcome: String,
}

#[derive(Serialize)]
struct RunnerValidateData {
    updated: usize,
    missing: usize,
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
                let path = args.get(idx + 1).ok_or_else(|| "missing value for --bundle".to_string())?;
                bundle_path = Some(PathBuf::from(path));
                idx += 2;
            }
            "--service-name" => {
                let name = args.get(idx + 1).ok_or_else(|| "missing value for --service-name".to_string())?;
                service_name = Some(name.to_string_lossy().to_string());
                idx += 2;
            }
            "--scope" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --scope".to_string())?;
                let scope_str = value.to_string_lossy();
                scope = RunnerScope::parse(scope_str.as_ref())
                    .ok_or_else(|| "invalid value for --scope".to_string())?;
                idx += 2;
            }
            "--identity" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --identity".to_string())?;
                identity = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--entitlements" => {
                let path = args.get(idx + 1).ok_or_else(|| "missing value for --entitlements".to_string())?;
                entitlements_path = Some(PathBuf::from(path));
                idx += 2;
            }
            "--executable" => {
                let path = args.get(idx + 1).ok_or_else(|| "missing value for --executable".to_string())?;
                executable_override = Some(PathBuf::from(path));
                idx += 2;
            }
            "--bundle-id" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --bundle-id".to_string())?;
                bundle_id_override = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--kind" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --kind".to_string())?;
                let raw = value.to_string_lossy();
                if raw == "machme" {
                    return Err("--kind machme is not supported; use --kind byoxpc".to_string());
                }
                let kind = RunnerKind::parse(raw.as_ref())
                    .ok_or_else(|| format!("invalid value for --kind: {raw}"))?;
                if matches!(kind, RunnerKind::Debuggable | RunnerKind::Standard) {
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
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --env".to_string())?;
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
    if !bundle_path.exists() {
        return Err(format!("bundle path not found: {}", bundle_path.display()));
    }

    // byoxpc is the only kind `runner install` accepts. The CLI parser above
    // already rejects standard/debuggable; here we accept an explicit
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
        return Err(
            "external runners use CFBundleIdentifier; remove --bundle-id".to_string()
        );
    }
    if executable_override.is_some() {
        return Err(
            "external runners do not accept --executable; \
             the binary is derived from <bundle>/Contents/MacOS/<CFBundleExecutable>"
                .to_string(),
        );
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

    // The XPC bundle is the signing/launchctl target; codesign treats it as
    // a single unit and the inner binary's signature is derived from the
    // bundle's seal.
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

    let (registry_path, mut registry) = load_registry_or_default()?;
    if let Some(existing) = registry
        .runners
        .iter()
        .find(|r| r.service_name == service_name)
    {
        return Err(format!(
            "service name '{}' is already registered as runner '{}'; run \
             `policy-witness runner remove --service-name {}` to remove it first",
            existing.service_name, existing.id, existing.service_name
        ));
    }

    // Re-sign the bundle (or its inner binary) when the caller supplied a
    // signing flag. The two modes are:
    //   --identity <id>      : sign with the named identity, optionally
    //                          embedding --entitlements.
    //   --allow-adhoc + --entitlements : ad-hoc re-sign so the embedded
    //                                    entitlements actually match the
    //                                    plist (registry would otherwise lie).
    // Passing --entitlements without either flag silently used to leave the
    // existing signature untouched; that footgun is now rejected.
    if let Some(identity) = identity.as_ref() {
        runner_manager::codesign_sign(
            &sign_target,
            identity,
            entitlements_path.as_deref(),
        )?;
    } else if allow_adhoc && entitlements_path.is_some() {
        runner_manager::codesign_sign(&sign_target, "-", entitlements_path.as_deref())?;
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

    // Always read entitlements from the binary so the registry reflects what
    // the kernel will actually enforce, not what the caller's plist asked for.
    let entitlements = runner_manager::entitlements_from_codesign(&executable_path);

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
    runner_manager::write_launchd_plist(&plist_path, &plist_contents)?;
    if !skip_bootstrap {
        if let Err(err) = runner_manager::launchctl_bootstrap(scope, &plist_path) {
            let present = runner_manager::launchctl_service_present(scope, &service_name)
                .unwrap_or(false);
            if !present {
                return Err(err);
            }
            eprintln!("warning: {err} (service appears loaded; continuing)");
        }
    }

    let record = RunnerRecord {
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
    };

    registry.runners.push(record.clone());
    runner_manager::save_registry(&registry_path, &registry)?;

    let data = RunnerInstallData {
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
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --id".to_string())?;
                runner_id = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--service-name" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --service-name".to_string())?;
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

fn cmd_runner_verify(args: &[OsString]) -> Result<i32, String> {
    let mut runner_id: Option<String> = None;
    let mut service_name: Option<String> = None;
    let mut timeout_ms: u64 = RUNNER_VERIFY_DEFAULT_TIMEOUT_MS;

    let mut idx = 0;
    while idx < args.len() {
        let arg = args[idx].to_string_lossy();
        match arg.as_ref() {
            "--id" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --id".to_string())?;
                runner_id = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--service-name" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --service-name".to_string())?;
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

    let temp_dir = std::env::temp_dir().join("pw-runner-verify");
    std::fs::create_dir_all(&temp_dir)
        .map_err(|e| format!("failed to create temp dir: {e}"))?;
    let request_path = temp_dir.join(format!("verify-{}.json", now_unix_ms()));

    let spec = json!({
        "schema_version": 1,
        "specimen_id": "runner_verify",
        "run_kind": "runner_verify",
        "policy": {
            "format": "sbpl",
            "sbpl_source": "(version 1)\n(allow default)\n"
        },
        "probe_plan": []
    });
    std::fs::write(&request_path, serde_json::to_string_pretty(&spec).unwrap())
        .map_err(|e| format!("failed to write verify request: {e}"))?;

    let record_kind = infer_record_kind(record);
    let connection = match record_kind {
        RunnerKind::Byoxpc => RunnerConnectionKind::MachService {
            privileged: matches!(record.scope, RunnerScope::System),
        },
        RunnerKind::Debuggable | RunnerKind::Standard => {
            return Err("external runners cannot be built-in kinds".to_string());
        }
    };
    let (_, runner_result) =
        run_pw_runner_client(&record.service_name, &request_path, timeout_ms, &connection)?;
    let runner_pid = runner_result
        .as_ref()
        .and_then(|v| v.get("pid"))
        .and_then(|v| v.as_i64());
    let outcome = runner_result
        .as_ref()
        .and_then(|v| v.get("normalized_outcome"))
        .and_then(|v| v.as_str())
        .unwrap_or("runner_output_not_json")
        .to_string();

    let ok = outcome == "ok";
    let data = RunnerVerifyData {
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
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --id".to_string())?;
                runner_id = Some(value.to_string_lossy().to_string());
                idx += 2;
            }
            "--service-name" => {
                let value = args.get(idx + 1).ok_or_else(|| "missing value for --service-name".to_string())?;
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

    let (registry_path, mut registry) = load_registry_or_default()?;
    let idx = if let Some(id) = runner_id.as_ref() {
        registry.runners.iter().position(|r| &r.id == id)
    } else if let Some(service) = service_name.as_ref() {
        registry.runners.iter().position(|r| &r.service_name == service)
    } else {
        return Err("runner remove requires --id or --service-name".to_string());
    };

    let idx = match idx {
        Some(idx) => idx,
        None => {
            return emit_runner_not_found(
                "runner_remove",
                runner_id.as_deref(),
                service_name.as_deref(),
            );
        }
    };

    let record = registry.runners.remove(idx);
    let plist_path = runner_manager::launchd_plist_path(&record.service_name, record.scope)?;

    // Remove is the integrator's escape hatch for cleaning up dirty state, so
    // launchctl and on-disk failures must not strand the registry entry.
    // Surface them as warnings on a successful envelope instead.
    let mut warnings: Vec<String> = Vec::new();
    let mut booted_out = false;
    if !skip_bootout {
        match runner_manager::launchctl_bootout(record.scope, &plist_path) {
            Ok(()) => booted_out = true,
            Err(err) => warnings.push(format!("launchctl bootout: {err}")),
        }
    }

    let plist_removed = if plist_path.exists() {
        match std::fs::remove_file(&plist_path) {
            Ok(()) => true,
            Err(err) => {
                warnings.push(format!(
                    "failed to remove plist {}: {err}",
                    plist_path.display()
                ));
                false
            }
        }
    } else {
        false
    };

    runner_manager::save_registry(&registry_path, &registry)?;

    let data = RunnerRemoveData {
        runner_id: record.id,
        service_name: record.service_name,
        plist_path: plist_path.display().to_string(),
        booted_out,
        plist_removed,
        warnings,
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

/// Walk the registry and re-read each runner's on-disk signature and
/// entitlements. This is *registry-internal* validation — it does not
/// reconcile against launchctl or LaunchAgents/. Callers wanting that
/// will need a separate gc/reconcile command.
fn cmd_runner_validate() -> Result<i32, String> {
    let (registry_path, mut registry) = load_registry_or_default()?;
    let mut missing = 0usize;
    for record in registry.runners.iter_mut() {
        let exec_path = Path::new(&record.executable_path);
        if !exec_path.exists() {
            missing += 1;
            record.signature.valid = false;
            record.entitlements.error = Some("executable missing".to_string());
            continue;
        }
        if let Ok(sig) = runner_manager::codesign_metadata(exec_path) {
            record.signature = sig;
        }
        record.entitlements = runner_manager::entitlements_from_codesign(exec_path);
        if record.kind.is_none() {
            record.kind = Some(infer_record_kind(record));
        }
    }
    let updated = registry.runners.len();
    runner_manager::save_registry(&registry_path, &registry)?;

    let data = RunnerValidateData { updated, missing };
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
        "-h" | "--help" | "help" => {
            println!("{}", runner_usage());
            Ok(0)
        }
        _ => Err(format!("unknown runner command: {sub}\n\n{}", runner_usage())),
    }
}
