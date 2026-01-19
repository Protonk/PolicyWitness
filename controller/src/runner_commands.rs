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
use crate::run_flow::DEFAULT_TIMEOUT_MS;
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
}

#[derive(Serialize)]
struct RunnerVerifyData {
    runner_id: Option<String>,
    service_name: String,
    runner_pid: Option<i64>,
    normalized_outcome: String,
}

#[derive(Serialize)]
struct RunnerRefreshData {
    updated: usize,
    missing: usize,
}

fn runner_usage() -> String {
    "\
usage:
  policy-witness runner install --bundle <path> [--kind byoxpc|machme] [--service-name <name>] [--scope user|system]
                               [--identity <codesign-id>] [--entitlements <plist>]
                               [--executable <path>] [--bundle-id <id>] [--allow-adhoc]
                               [--env KEY=VALUE]
                               [--skip-bootstrap]
  policy-witness runner list
  policy-witness runner status --id <runner-id> | --service-name <name>
  policy-witness runner verify --id <runner-id> | --service-name <name> [--timeout-ms <n>]
  policy-witness runner remove --id <runner-id> | --service-name <name> [--skip-bootout]
  policy-witness runner refresh
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
                let kind = RunnerKind::parse(value.to_string_lossy().as_ref())
                    .ok_or_else(|| "invalid value for --kind".to_string())?;
                if matches!(kind, RunnerKind::Debuggable) {
                    return Err("runner install does not accept kind=debuggable".to_string());
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

    let bundle_info = if bundle_path.is_dir() {
        read_bundle_info(&bundle_path).ok()
    } else {
        None
    };

    let kind = if let Some(kind) = kind_override {
        kind
    } else if bundle_path.is_dir() {
        match bundle_info
            .as_ref()
            .and_then(|info| info.package_type.as_deref())
        {
            Some("XPC!") => RunnerKind::Byoxpc,
            _ => {
                return Err(
                    "bundle is not an XPC service (CFBundlePackageType != XPC!); pass --kind machme and --executable to install a Mach service binary"
                        .to_string(),
                );
            }
        }
    } else {
        RunnerKind::Machme
    };

    if matches!(kind, RunnerKind::Byoxpc) {
        if bundle_id_override.is_some() {
            return Err("byoxpc runners use CFBundleIdentifier; remove --bundle-id".to_string());
        }
        if executable_override.is_some() {
            return Err("byoxpc runners do not accept --executable".to_string());
        }
    }

    let (bundle_id, executable_path) = match kind {
        RunnerKind::Byoxpc => {
            let info = bundle_info.as_ref().ok_or_else(|| {
                "byoxpc runners require a bundle with Contents/Info.plist".to_string()
            })?;
            if info.package_type.as_deref() != Some("XPC!") {
                return Err(
                    "byoxpc runners require CFBundlePackageType=XPC! in Info.plist".to_string(),
                );
            }
            let executable_path = bundle_path
                .join("Contents")
                .join("MacOS")
                .join(&info.executable);
            (Some(info.bundle_id.clone()), executable_path)
        }
        RunnerKind::Machme => {
            if bundle_path.is_dir() && executable_override.is_none() {
                return Err(
                    "machme runners require --executable when --bundle is a directory".to_string(),
                );
            }
            let executable_path = executable_override.unwrap_or_else(|| bundle_path.clone());
            let bundle_id = bundle_id_override
                .clone()
                .or_else(|| bundle_info.as_ref().map(|info| info.bundle_id.clone()));
            (bundle_id, executable_path)
        }
        RunnerKind::Debuggable => {
            return Err("runner install does not accept kind=debuggable".to_string());
        }
    };

    if !executable_path.exists() {
        return Err(format!(
            "executable path not found: {}",
            executable_path.display()
        ));
    }

    let sign_target = match kind {
        RunnerKind::Byoxpc => bundle_path.clone(),
        RunnerKind::Machme => executable_path.clone(),
        RunnerKind::Debuggable => {
            return Err("runner install does not accept kind=debuggable".to_string());
        }
    };
    if let Some(identity) = identity.as_ref() {
        runner_manager::codesign_sign(
            &sign_target,
            identity,
            entitlements_path.as_deref(),
        )?;
    }
    runner_manager::codesign_verify(&sign_target)?;
    let signature = runner_manager::codesign_metadata(&executable_path)?;
    if signature.adhoc && !allow_adhoc {
        return Err("runner is ad-hoc signed; pass --allow-adhoc to accept".to_string());
    }

    let entitlements = if let Some(entitlements_path) = entitlements_path.as_deref() {
        runner_manager::entitlements_from_plist_path(entitlements_path)
    } else {
        runner_manager::entitlements_from_codesign(&executable_path)
    };

    let runner_id = runner_manager::random_id()?;
    let service_name = match kind {
        RunnerKind::Byoxpc => {
            let bundle_id = bundle_id
                .clone()
                .ok_or_else(|| "byoxpc runners require a CFBundleIdentifier".to_string())?;
            if let Some(requested) = service_name.as_ref() {
                if requested != &bundle_id {
                    return Err(format!(
                        "byoxpc service name must match CFBundleIdentifier ({bundle_id})"
                    ));
                }
            }
            bundle_id
        }
        RunnerKind::Machme => service_name
            .unwrap_or_else(|| runner_manager::generate_service_name(&runner_id)),
        RunnerKind::Debuggable => {
            return Err("runner install does not accept kind=debuggable".to_string());
        }
    };

    let plist_path = runner_manager::launchd_plist_path(&service_name, scope)?;
    if matches!(kind, RunnerKind::Byoxpc) && !env.contains_key("XPC_SERVICE_PATH") {
        // libxpc expects the bundle root for the XPC service when launching directly.
        env.insert(
            "XPC_SERVICE_PATH".to_string(),
            bundle_path.display().to_string(),
        );
    }
    if matches!(kind, RunnerKind::Byoxpc | RunnerKind::Machme) {
        // PWRunner reads this to advertise the Mach service name for NSXPC.
        env.insert(
            "PW_RUNNER_MACH_SERVICE_NAME".to_string(),
            service_name.clone(),
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

    let (registry_path, mut registry) = load_registry_or_default()?;
    if registry
        .runners
        .iter()
        .any(|r| r.id == record.id || r.service_name == record.service_name)
    {
        return Err("runner id or service name already registered".to_string());
    }
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
        None
    }
    .ok_or_else(|| "runner not found in registry".to_string())?;

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

fn cmd_runner_verify(args: &[OsString]) -> Result<i32, String> {
    let mut runner_id: Option<String> = None;
    let mut service_name: Option<String> = None;
    let mut timeout_ms: u64 = DEFAULT_TIMEOUT_MS;

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
        None
    }
    .ok_or_else(|| "runner not found in registry".to_string())?;

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
        RunnerKind::Byoxpc | RunnerKind::Machme => RunnerConnectionKind::MachService {
            privileged: matches!(record.scope, RunnerScope::System),
        },
        RunnerKind::Debuggable => {
            return Err("external runners cannot be kind=debuggable".to_string());
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
        None
    }
    .ok_or_else(|| "runner not found in registry".to_string())?;

    let record = registry.runners.remove(idx);
    let plist_path = runner_manager::launchd_plist_path(&record.service_name, record.scope)?;
    if !skip_bootout {
        runner_manager::launchctl_bootout(record.scope, &plist_path)?;
    }
    if plist_path.exists() {
        std::fs::remove_file(&plist_path)
            .map_err(|e| format!("failed to remove plist {}: {e}", plist_path.display()))?;
    }
    runner_manager::save_registry(&registry_path, &registry)?;

    let data = RunnerRemoveData {
        runner_id: record.id,
        service_name: record.service_name,
        plist_path: plist_path.display().to_string(),
        booted_out: !skip_bootout,
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

fn cmd_runner_refresh() -> Result<i32, String> {
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

    let data = RunnerRefreshData { updated, missing };
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
    json_contract::print_envelope("runner_refresh", result, &data)?;
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
        "refresh" => cmd_runner_refresh(),
        "-h" | "--help" | "help" => {
            println!("{}", runner_usage());
            Ok(0)
        }
        _ => Err(format!("unknown runner command: {sub}\n\n{}", runner_usage())),
    }
}
