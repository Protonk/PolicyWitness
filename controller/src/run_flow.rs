//! Orchestrates a single run and builds the JSON envelope.
//!
//! The controller reads the request, parses the app evidence manifest once,
//! selects a runner, collects the specimen dossier, delivers the held request
//! string to the Swift client on stdin, gates the reply on its response
//! version, and records independent fallback compilation on `xpc_error`.
//!
//! Published worker preparation/application failures are runner_failed. The
//! fallback sbpl-check reports only its own compilation, not missing worker
//! progress or the cause of a lost reply.

use serde::Serialize;
use serde_json::Value;
use std::ffi::OsString;
use std::path::{Path, PathBuf};

use crate::app_layout::app_root_from_current_exe;
use crate::augments::{AugmentResolution, resolve_augments};
use crate::cli;
use crate::dossier::{
    AppProvenance, Augmentation, Binaries, HostFacts, Imports, PolicyDossier, Specimen,
};
use crate::evidence::{self, EvidenceManifest};
use crate::json_contract;
use crate::policy_check::{PolicyCheckCapture, run_policy_check};
use crate::porcelain_admission::{self, RunnerExecutionDiagnostics};
use crate::porcelain_records::{PWRunnerRequestFailure, PWRunnerRunResult};
use crate::request_patch::{RequestError, parse_request, validate_request_contract};
use crate::runner_client::{RunnerClientRun, run_pw_runner_client};
use crate::runner_manager::RunnerKind;
use crate::runner_select::{
    RunnerConnectionKind, parse_runner_selector_value, resolve_runner_target_with_registry,
    runner_provenance_from_target, strip_runner_selector,
};
const DEFAULT_TIMEOUT_MS: u64 = 240_000;

/// `data` of a `kind: "run"` envelope: the dossier plus the execution records.
/// Execution keys are present on every run envelope; an uncollected record is
/// null. Acquisition/submission observations belong to the client capture. The optional
/// request_failure is included only when supplied.
#[derive(Serialize)]
struct ExecutionData {
    pub specimen: Specimen,
    pub policy_check: Option<PolicyCheckCapture>,
    /// Fallback compilations for carried actor policy objects, in request
    /// order; absent for the ordinary form and when no fallback ran.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub actor_policy_checks: Option<Vec<ActorPolicyCheck>>,
    pub timeout_ms: Option<u64>,
    pub runner_client: Option<RunnerClientRun>,
    pub runner_result: Option<PWRunnerRunResult>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub request_failure: Option<RequestFailureProjection>,
}

/// One carried actor policy object's fallback compilation capture.
#[derive(Serialize)]
pub(crate) struct ActorPolicyCheck {
    pub actor_id: Option<String>,
    pub policy_check: PolicyCheckCapture,
}

#[derive(Serialize)]
struct RunData {
    #[serde(flatten)]
    execution: ExecutionData,
    runner_sandbox_diagnostics: Option<RunnerExecutionDiagnostics>,
}

// Execution result and diagnostics are derived only from the admitted reply.
struct CompletedExecution {
    data: ExecutionData,
    diagnostics: RunnerExecutionDiagnostics,
    result: json_contract::JsonResult,
    exit_code: i32,
}

/// The version gate for a received runner reply.
pub enum ReplyVersion {
    Supported,
    Unsupported(String),
    Malformed(String),
}

#[derive(Serialize)]
#[serde(untagged)]
pub(crate) enum RequestFailureProjection {
    Controller(crate::request_patch::RequestFailure),
    Runner(PWRunnerRequestFailure),
}

pub(crate) fn reply_version(reply: &PWRunnerRunResult) -> ReplyVersion {
    reply_contract(reply, json_contract::BUILD_CONTRACT)
}

pub(crate) fn reply_contract(reply: &PWRunnerRunResult, expected: &str) -> ReplyVersion {
    if expected == "unbound" || reply.producer.contract != expected {
        return ReplyVersion::Unsupported(reply.producer.contract.clone());
    }
    match porcelain_admission::admission_problem(reply) {
        Some(problem) => ReplyVersion::Malformed(problem),
        None => ReplyVersion::Supported,
    }
}

/// The dossier and any execution records available before reply admission.
fn execution_only(
    specimen: Specimen,
    timeout_ms: Option<u64>,
    runner_client: Option<RunnerClientRun>,
    runner_result: Option<PWRunnerRunResult>,
) -> RunData {
    RunData {
        execution: ExecutionData {
            specimen,
            policy_check: None,
            actor_policy_checks: None,
            timeout_ms,
            runner_client,
            runner_result,
            request_failure: None,
        },
        runner_sandbox_diagnostics: None,
    }
}

/// The uniform `kind: "run"` envelope for a controller failure before or
/// without execution: `tool_error`, exit 2, the dossier collected so far and
/// null execution records.
fn tool_error_envelope(
    specimen: Specimen,
    timeout_ms: Option<u64>,
    error: String,
) -> (json_contract::JsonResult, RunData) {
    (
        json_contract::JsonResult::new(false, 2, Some("tool_error"), Some(error)),
        execution_only(specimen, timeout_ms, None, None),
    )
}

/// What a run produces: the usage text request, or one rendered `kind: "run"`
/// envelope with the process exit code it carries. `cmd_run` prints it; the
/// controlled orchestration tests read it.
enum RunOutput {
    Help,
    Envelope { text: String, exit_code: i32 },
}

fn envelope<T: Serialize>(
    result: json_contract::JsonResult,
    data: &T,
    exit_code: i32,
) -> Result<RunOutput, String> {
    Ok(RunOutput::Envelope {
        text: json_contract::render_envelope("run", result, data)?,
        exit_code,
    })
}

fn tool_error(
    specimen: Specimen,
    timeout_ms: Option<u64>,
    error: String,
) -> Result<RunOutput, String> {
    let (result, data) = tool_error_envelope(specimen, timeout_ms, error);
    envelope(result, &data, 2)
}

fn bad_request(
    specimen: Specimen,
    timeout_ms: Option<u64>,
    error: RequestError,
) -> Result<RunOutput, String> {
    let mut data = execution_only(specimen, timeout_ms, None, None);
    data.execution.request_failure = Some(RequestFailureProjection::Controller(error.failure));
    envelope(
        json_contract::JsonResult::new(false, 1, Some("bad_request"), Some(error.message)),
        &data,
        1,
    )
}

/// The envelope for an error that escaped `cmd_run` (the `cli.rs` catch-all).
pub fn print_escaped_tool_error(error: String) -> Result<(), String> {
    let specimen = Specimen::unavailable(
        None,
        HostFacts::collect(),
        "the run failed before runner selection",
    );
    let (result, data) = tool_error_envelope(specimen, None, error);
    json_contract::print_envelope("run", result, &data)
}

/// The dependencies a run acquires from its environment, named at the
/// boundaries the controlled orchestration tests observe: where the app root
/// is, how the evidence manifest is read, where the external registry lives
/// and how the client and fallback compiler are invoked. Production binds the
/// real ones; a test binds counting or capturing closures around them and reads
/// the rendered envelope.
struct RunDependencies<'a> {
    pub app_root: &'a dyn Fn() -> Result<PathBuf, String>,
    pub load_manifest: &'a dyn Fn(&Path) -> Result<EvidenceManifest, String>,
    /// `None` resolves the registry from `PW_RUNNER_REGISTRY` or `$HOME`.
    pub registry_path: Option<&'a Path>,
    pub policy_check: &'a dyn Fn(&str) -> Result<PolicyCheckCapture, String>,
    pub client: &'a dyn Fn(
        &str,
        &str,
        u64,
        &RunnerConnectionKind,
    ) -> Result<(RunnerClientRun, Option<PWRunnerRunResult>), String>,
}

impl RunDependencies<'static> {
    pub fn production() -> Self {
        RunDependencies {
            app_root: &app_root_from_current_exe,
            load_manifest: &evidence::load_manifest,
            registry_path: None,
            client: &run_pw_runner_client,
            policy_check: &run_policy_check,
        }
    }
}

fn load_app_provenance(
    manifest: Result<&EvidenceManifest, &String>,
    manifest_path: &Path,
    app_root: &Path,
) -> Option<AppProvenance> {
    let manifest = manifest.ok()?;
    let verify = match std::env::var("PW_VERIFY_EVIDENCE").ok().as_deref() {
        Some("1") => Some(evidence::verify_manifest(manifest, app_root, manifest_path)),
        _ => None,
    };
    Some(AppProvenance {
        evidence_manifest_path: manifest_path.display().to_string(),
        evidence_verify: verify,
    })
}

/// The string SBPL source a parsed request carries, if any.
fn string_source(request: &Value) -> Option<&str> {
    request
        .get("policy")
        .and_then(|p| p.get("sbpl_source"))
        .and_then(Value::as_str)
}

/// The policy dossier for a resolved request and the admission decision:
/// the augmentation record, the import scan of the source selected for
/// invocation, and the refusal diagnostic when augment resolution failed.
/// Hashes identify only string source bytes that existed.
fn policy_dossier(
    original_source: Option<&str>,
    resolution: &AugmentResolution,
    selected_source: Option<&str>,
) -> (PolicyDossier, Option<RequestError>) {
    let (augmentation, error) = match resolution {
        AugmentResolution::NotPresent | AugmentResolution::StrippedNoOp => (
            match original_source {
                Some(source) => Augmentation::not_requested(Some(source)),
                None => Augmentation::not_applicable(),
            },
            None,
        ),
        AugmentResolution::Applied(record) => (
            Augmentation::applied(record, original_source.is_some()),
            None,
        ),
        AugmentResolution::BadRequest(error) => (
            Augmentation::failed(original_source, error.to_string()),
            Some(error.clone()),
        ),
    };
    let imports = if error.is_some() {
        Imports::not_applicable(Some("augmentation_failed".to_string()))
    } else {
        match selected_source {
            Some(source) => Imports::scan(source),
            None => Imports::not_applicable(None),
        }
    };
    (
        PolicyDossier {
            augmentation,
            imports,
        },
        error,
    )
}

/// Per-actor policy dossiers for the actor form, from each actor's
/// resolution, and the first refusal in actor order. The legacy dossier rules
/// apply to each policy object; an actor without a policy object gets a
/// not-applicable dossier.
pub(crate) fn actor_policy_dossiers(
    resolutions: &[crate::augments::ActorAugmentResolution],
) -> (Vec<crate::dossier::ActorDossier>, Option<RequestError>) {
    let mut dossiers = Vec::with_capacity(resolutions.len());
    let mut first_error = None;
    for actor in resolutions {
        let (policy, error) = policy_dossier(
            actor.original_source.as_deref(),
            &actor.resolution,
            actor.selected_source.as_deref(),
        );
        if first_error.is_none() {
            first_error = error;
        }
        dossiers.push(crate::dossier::ActorDossier {
            actor_id: actor.actor_id.clone(),
            mode: actor.mode.clone(),
            policy,
        });
    }
    (dossiers, first_error)
}

/// What a client capture permits. A delivery error is a controller failure
/// that takes precedence over any captured reply; otherwise the reply's
/// version gates every semantic reader.
pub(crate) enum ReplyAdmission {
    DeliveryFailed(String),
    Refused {
        outcome: &'static str,
        error: String,
    },
    Admitted,
}

pub(crate) fn admit_reply(
    client: &RunnerClientRun,
    reply: Option<&PWRunnerRunResult>,
) -> ReplyAdmission {
    if let Some(error) = client
        .request_delivery
        .as_ref()
        .and_then(|d| d.error.clone())
    {
        return ReplyAdmission::DeliveryFailed(error);
    }
    if let Some((outcome, error)) = client.failure() {
        return ReplyAdmission::Refused { outcome, error };
    }
    match reply.map(reply_version) {
        None | Some(ReplyVersion::Supported) => ReplyAdmission::Admitted,
        Some(ReplyVersion::Unsupported(version)) => ReplyAdmission::Refused {
            outcome: "unsupported_runner_response",
            error: format!(
                "runner reply carries contract {version}; this controller reads only {}",
                json_contract::BUILD_CONTRACT
            ),
        },
        Some(ReplyVersion::Malformed(error)) => ReplyAdmission::Refused {
            outcome: "malformed_runner_response",
            error,
        },
    }
}

fn runner_outcome(reply: Option<&PWRunnerRunResult>) -> &str {
    reply
        .map(|reply| reply.normalized_outcome.as_str())
        .unwrap_or("runner_response_unavailable")
}

/// The independent fallback compilation, requested only for an admitted
/// client-terminal `xpc_error`. A helper launch or delivery failure is recorded as an
/// unavailable capture; the runner reply is never changed by it.
fn fallback_policy_check(
    client: &RunnerClientRun,
    run: impl FnOnce() -> Result<PolicyCheckCapture, String>,
) -> Option<PolicyCheckCapture> {
    if !client.fallback_eligible() {
        return None;
    }
    Some(run().unwrap_or_else(PolicyCheckCapture::unavailable))
}

/// The actor form's fallback compilations: each carried resolved policy
/// object is checked on its own, never applied to another actor, and the
/// captures keep request order. None when the legacy rule withholds the
/// fallback or no actor carries a policy object.
fn actor_fallback_checks(
    client: &RunnerClientRun,
    policies: &[(Option<String>, Value)],
    run: &dyn Fn(&str) -> Result<PolicyCheckCapture, String>,
) -> Option<Vec<ActorPolicyCheck>> {
    if policies.is_empty() || !client.fallback_eligible() {
        return None;
    }
    Some(
        policies
            .iter()
            .map(|(actor_id, policy)| {
                let request = serde_json::json!({ "policy": policy }).to_string();
                ActorPolicyCheck {
                    actor_id: actor_id.clone(),
                    policy_check: run(&request).unwrap_or_else(PolicyCheckCapture::unavailable),
                }
            })
            .collect(),
    )
}

struct Parsed {
    request_path: Option<PathBuf>,
    timeout_ms: u64,
    runner_mode_arg: Option<String>,
}

enum Arguments {
    Run(Parsed),
    Help,
    /// An argument error: the path seen so far (if any) and the diagnostic.
    Error(Option<PathBuf>, String),
}

fn parse_arguments(args: &[OsString]) -> Arguments {
    let mut parsed = Parsed {
        request_path: None,
        timeout_ms: DEFAULT_TIMEOUT_MS,
        runner_mode_arg: None,
    };
    let mut idx = 0usize;
    while idx < args.len() {
        let arg = args[idx].to_string_lossy();
        if arg == "--" {
            break;
        }
        if !arg.starts_with('-') {
            parsed.request_path = Some(PathBuf::from(args[idx].clone()));
            idx += 1;
            continue;
        }
        match arg.as_ref() {
            "-h" | "--help" => return Arguments::Help,
            "--timeout-ms" => {
                let Some(value) = args
                    .get(idx + 1)
                    .and_then(|s| s.to_string_lossy().parse::<u64>().ok())
                else {
                    return Arguments::Error(None, "invalid value for --timeout-ms".to_string());
                };
                parsed.timeout_ms = value.max(1);
                idx += 2;
            }
            "--runner-mode" => {
                let Some(value) = args.get(idx + 1).and_then(|s| s.to_str()) else {
                    return Arguments::Error(
                        parsed.request_path,
                        "missing value for --runner-mode".to_string(),
                    );
                };
                if value == "machme" {
                    return Arguments::Error(
                        None,
                        "--runner-mode machme is not supported; use --runner-mode byoxpc"
                            .to_string(),
                    );
                }
                if RunnerKind::parse(value).is_none() {
                    return Arguments::Error(
                        None,
                        format!("invalid value for --runner-mode: {value}"),
                    );
                }
                parsed.runner_mode_arg = Some(value.to_string());
                idx += 2;
            }
            _ => return Arguments::Error(parsed.request_path, format!("unknown argument: {arg}")),
        }
    }
    Arguments::Run(parsed)
}

/// Inject `--runner-mode` into the request value; errors are request errors.
fn inject_runner_mode(request_value: &mut Value, mode: &str) -> Result<(), RequestError> {
    // Check the submitted selector before an option can replace an invalid value.
    parse_runner_selector_value(request_value)?;
    if mode == "machme" {
        return Err(RequestError::new(
            "invalid_value",
            &["runner", "mode"],
            "--runner-mode machme is not supported; use --runner-mode byoxpc",
        ));
    }
    let kind = RunnerKind::parse(mode).ok_or_else(|| {
        RequestError::new(
            "invalid_value",
            &["runner", "mode"],
            format!("invalid value for --runner-mode: {mode}"),
        )
    })?;
    let obj = request_value.as_object_mut().ok_or_else(|| {
        RequestError::new("type_mismatch", &[], "request.json must be a JSON object")
    })?;
    let runner_entry = obj
        .entry("runner")
        .or_insert_with(|| Value::Object(serde_json::Map::new()));
    if runner_entry.is_null() {
        *runner_entry = Value::Object(serde_json::Map::new());
    }
    let runner_obj = runner_entry.as_object_mut().ok_or_else(|| {
        RequestError::new("type_mismatch", &["runner"], "runner must be a JSON object")
    })?;
    if let Some(existing) = runner_obj.get("mode").and_then(|v| v.as_str()) {
        if existing != kind.as_str() {
            return Err(RequestError::new(
                "conflicting_selector",
                &["runner", "mode"],
                "request.json already includes runner.mode; remove it or omit --runner-mode",
            ));
        }
    } else {
        runner_obj.insert("mode".to_string(), Value::String(kind.as_str().to_string()));
    }
    Ok(())
}

pub fn cmd_run(args: &[OsString]) -> Result<i32, String> {
    match run(args, &RunDependencies::production())? {
        RunOutput::Help => {
            cli::print_usage();
            Ok(0)
        }
        RunOutput::Envelope { text, exit_code } => {
            println!("{text}");
            Ok(exit_code)
        }
    }
}

/// One run through production orchestration: argument admission, one manifest
/// load, runner selection, the dossier, the held request's delivery and the
/// reply's admission. Every exit renders the uniform `kind: "run"` envelope.
fn run(args: &[OsString], deps: &RunDependencies) -> Result<RunOutput, String> {
    let host = HostFacts::collect();
    let parsed = match parse_arguments(args) {
        Arguments::Help => return Ok(RunOutput::Help),
        Arguments::Error(path, error) => {
            let specimen = Specimen::unavailable(
                path.map(|p| p.to_string_lossy().to_string()),
                host,
                "no runner was selected: invalid arguments",
            );
            return tool_error(specimen, None, error);
        }
        Arguments::Run(parsed) => parsed,
    };
    let timeout_ms = Some(parsed.timeout_ms);
    let request_path_text = parsed
        .request_path
        .as_ref()
        .map(|p| p.to_string_lossy().to_string());

    let app_root = (deps.app_root)()?;
    // One manifest load per run; selection, provenance and the binary records
    // all read this value.
    let manifest_path = evidence::manifest_path_from_app_root(&app_root);
    let manifest: Result<EvidenceManifest, String> = (deps.load_manifest)(&manifest_path);
    let app_provenance = load_app_provenance(manifest.as_ref(), &manifest_path, &app_root);

    // A refusal before selection: the request value is absent.
    let refused = |error: String| -> Result<RunOutput, String> {
        let mut specimen = Specimen::unavailable(
            request_path_text.clone(),
            host.clone(),
            "no runner was selected",
        );
        specimen.app_provenance = app_provenance.clone();
        tool_error(specimen, timeout_ms, error)
    };
    let refused_request = |error: RequestError| -> Result<RunOutput, String> {
        let mut specimen = Specimen::unavailable(
            request_path_text.clone(),
            host.clone(),
            "no runner was selected: malformed request",
        );
        specimen.app_provenance = app_provenance.clone();
        bad_request(specimen, timeout_ms, error)
    };

    let Some(request_path) = parsed.request_path.clone() else {
        return refused("missing <request.json>".to_string());
    };
    if !request_path.exists() {
        return refused(format!(
            "request.json not found: {}",
            request_path.display()
        ));
    }
    let request_text = match std::fs::read_to_string(&request_path) {
        Ok(text) => text,
        Err(error) => return refused(format!("failed to read request.json: {error}")),
    };
    let mut request_value = match parse_request(&request_text) {
        Ok(value) => value,
        Err(error) => return refused_request(error),
    };
    if let Err(error) = validate_request_contract(&request_value) {
        return refused_request(error);
    }
    if let Some(mode) = parsed.runner_mode_arg.as_deref() {
        if let Err(error) = inject_runner_mode(&mut request_value, mode) {
            return refused_request(error);
        }
    }

    let selector = match parse_runner_selector_value(&request_value) {
        Ok(selector) => selector,
        Err(error) => return refused_request(error),
    };
    let selection = resolve_runner_target_with_registry(
        &app_root,
        manifest.as_ref(),
        &selector,
        deps.registry_path,
    );

    // Resolve named augments before the runner (and the fallback compilation)
    // so every reader sees the same bytes. The original string's hash is
    // taken before resolution replaces it.
    let original_source = string_source(&request_value).map(str::to_string);
    let resolution = resolve_augments(&mut request_value, &app_root);
    let (policy, augmentation_error) = policy_dossier(
        original_source.as_deref(),
        &resolution,
        string_source(&request_value),
    );
    // The actor form resolves each actor's own policy and keeps one dossier
    // per actor; the first refusal in actor order is the request's refusal.
    let actor_resolutions = crate::augments::resolve_actor_augments(&mut request_value, &app_root);
    let (actor_dossiers, augmentation_error) = if actor_resolutions.is_empty() {
        (None, augmentation_error)
    } else {
        let (dossiers, error) = actor_policy_dossiers(&actor_resolutions);
        (Some(dossiers), augmentation_error.or(error))
    };
    let actor_policies: Vec<(Option<String>, Value)> = request_value
        .get("actors")
        .and_then(Value::as_array)
        .map(|actors| {
            actors
                .iter()
                .filter_map(|actor| {
                    let policy = actor.get("sandbox")?.get("policy")?;
                    policy.is_object().then(|| {
                        (
                            actor
                                .get("actor_id")
                                .and_then(Value::as_str)
                                .map(str::to_string),
                            policy.clone(),
                        )
                    })
                })
                .collect()
        })
        .unwrap_or_default();

    let (runner_target, binaries, runner_provenance, selection_error) = match selection {
        Ok(target) => {
            let binaries = Binaries::observe(&app_root, &target, &request_value, manifest.as_ref());
            let provenance = runner_provenance_from_target(&target);
            (Some(target), binaries, Some(provenance), None)
        }
        Err(error) => (None, Binaries::unselected(&error), None, Some(error)),
    };
    let specimen = Specimen {
        request_path: request_path_text.clone(),
        policy,
        host,
        runner_provenance,
        app_provenance,
        binaries,
        actors: actor_dossiers,
    };

    if let Some(error) = selection_error {
        return tool_error(specimen, timeout_ms, error);
    }
    let runner_target = runner_target.expect("selection succeeded");

    if let Some(error) = augmentation_error {
        return bad_request(specimen, timeout_ms, error);
    }

    // Selection is already recorded in the dossier. The runner receives only
    // fields it implements; direct XPC callers cannot silently request selection.
    strip_runner_selector(&mut request_value);

    // The held request string: serialized once, delivered to every reader.
    // Replacing the file after this point cannot change the submitted bytes.
    let held = serde_json::to_string_pretty(&request_value)
        .map_err(|e| format!("failed to encode request JSON: {e}"))?;

    let (runner_client, runner_result) = match (deps.client)(
        &runner_target.service_name,
        &held,
        parsed.timeout_ms,
        &runner_target.connection,
    ) {
        Ok(value) => value,
        Err(error) => return tool_error(specimen, timeout_ms, error),
    };

    // A decoded reply stays in the envelope on every refusal; nothing
    // interprets it before admission.
    let (outcome, exit_code, error) = match admit_reply(&runner_client, runner_result.as_ref()) {
        ReplyAdmission::DeliveryFailed(error) => ("tool_error", 2, error),
        ReplyAdmission::Refused { outcome, error } => (outcome, 1, error),
        ReplyAdmission::Admitted => {
            let policy_check = fallback_policy_check(&runner_client, || (deps.policy_check)(&held));
            let actor_policy_checks =
                actor_fallback_checks(&runner_client, &actor_policies, deps.policy_check);
            let execution = complete_execution(ExecutionData {
                specimen,
                policy_check,
                actor_policy_checks,
                timeout_ms,
                runner_client: Some(runner_client),
                runner_result,
                request_failure: None,
            });
            let (result, data, exit_code) = execution_envelope(execution);
            return envelope(result, &data, exit_code);
        }
    };
    let mut data = execution_only(specimen, timeout_ms, Some(runner_client), runner_result);
    data.execution.policy_check =
        fallback_policy_check(data.execution.runner_client.as_ref().unwrap(), || {
            (deps.policy_check)(&held)
        });
    data.execution.actor_policy_checks = actor_fallback_checks(
        data.execution.runner_client.as_ref().unwrap(),
        &actor_policies,
        deps.policy_check,
    );
    envelope(
        json_contract::JsonResult::new(false, exit_code, Some(outcome), Some(error)),
        &data,
        exit_code,
    )
}

fn complete_execution(mut data: ExecutionData) -> CompletedExecution {
    let diagnostics = porcelain_admission::execution_diagnostics(data.runner_result.as_ref());
    let runner_outcome = runner_outcome(data.runner_result.as_ref()).to_string();
    if runner_outcome == "bad_request" {
        data.request_failure = data.runner_result.as_ref().and_then(|reply| {
            reply
                .request_failure
                .clone()
                .map(RequestFailureProjection::Runner)
        });
    }
    let ok = runner_outcome == "finished";
    let exit_code = if ok { 0 } else { 1 };

    let client_output = data.runner_client.as_ref().map(|c| &c.output);
    let error = if ok {
        None
    } else if let Some(v) = data
        .runner_result
        .as_ref()
        .and_then(|reply| reply.error.as_deref())
    {
        Some(v.to_string())
    } else if let Some(v) = client_output.and_then(|o| o.stdout_capture_error.as_ref()) {
        Some(v.clone())
    } else if let Some(v) = client_output.and_then(|o| o.stdout_parse_error.as_ref()) {
        Some(format!("runner output parse error: {v}"))
    } else {
        Some("run did not complete successfully".to_string())
    };

    let result =
        json_contract::JsonResult::new(ok, exit_code, Some(runner_outcome.as_str()), error);

    CompletedExecution {
        data,
        diagnostics,
        result,
        exit_code,
    }
}

fn execution_envelope(execution: CompletedExecution) -> (json_contract::JsonResult, RunData, i32) {
    let data = RunData {
        execution: execution.data,
        runner_sandbox_diagnostics: Some(execution.diagnostics),
    };
    (execution.result, data, execution.exit_code)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::porcelain_admission::IntegrityIssue;
    use crate::reply_fixtures::*;
    use crate::utils::RequestDelivery;
    #[cfg(test)]
    use serde_json::json;

    fn fixture_reply(value: Value) -> PWRunnerRunResult {
        serde_json::from_value(value).expect("authored fixture must have the typed record shape")
    }
    fn integrity_issue(kind: &'static str, detail: String) -> IntegrityIssue {
        IntegrityIssue {
            kind: kind.into(),
            detail,
            subject_path: None,
            rule: None,
            question: None,
            step_index: None,
            observations: None,
        }
    }

    #[test]
    fn typed_completion_preserves_native_failure_beside_finished_summary() {
        // Authored JSON is fixture input only; production receives binary records.
        let mut reply: PWRunnerRunResult =
            serde_json::from_value(crate::reply_fixtures::ordinary_template()).unwrap();
        reply.producer = crate::porcelain_records::PWProducer::current();
        reply.steps[0].attempt.rc = -1;
        reply.steps[0].attempt.errno = Some(1);
        reply.steps[0].attempt.outcome = "open_failed".into();
        let data = ExecutionData {
            specimen: specimen(),
            policy_check: None,
            actor_policy_checks: None,
            timeout_ms: Some(DEFAULT_TIMEOUT_MS),
            runner_client: None,
            runner_result: Some(reply.clone()),
            request_failure: None,
        };
        let execution = complete_execution(data);
        assert_eq!(execution.exit_code, 0);
        assert!(execution.result.ok);
        assert_eq!(
            execution.data.runner_result.as_ref().unwrap().steps[0]
                .attempt
                .rc,
            -1
        );
        let (result, data, code) = execution_envelope(execution);
        let public: Value =
            serde_json::from_str(&json_contract::render_envelope("run", result, &data).unwrap())
                .unwrap();
        assert_eq!(code, 0);
        assert_eq!(
            public["data"]["runner_result"]["steps"][0]["attempt"]["errno"],
            1
        );
        assert_eq!(public["result"]["normalized_outcome"], "finished");
        assert_eq!(data.execution.runner_result, Some(reply));
    }

    /// Fixed host facts for constructed execution envelopes.
    fn host() -> HostFacts {
        HostFacts {
            macos_version: Some("14.0".into()),
            macos_build: Some("23A000".into()),
            kernel_release: Some("23.0.0".into()),
            arch: Some("arm64".into()),
        }
    }

    fn specimen() -> Specimen {
        Specimen::unavailable(
            Some("/controlled/request.json".into()),
            host(),
            "controlled fixture: no runner was selected",
        )
    }

    fn client_run(runner: Option<&Value>) -> RunnerClientRun {
        crate::runner_client::test_client_run(runner)
    }

    fn execution_data(runner: Option<Value>) -> ExecutionData {
        ExecutionData {
            specimen: specimen(),
            policy_check: None,
            actor_policy_checks: None,
            timeout_ms: Some(DEFAULT_TIMEOUT_MS),
            runner_client: Some(client_run(runner.as_ref())),
            runner_result: runner.map(fixture_reply),
            request_failure: None,
        }
    }

    fn driver_execution(reply: PWRunnerRunResult, raw: &[u8]) -> ExecutionData {
        ExecutionData {
            specimen: specimen(),
            policy_check: None,
            actor_policy_checks: None,
            timeout_ms: Some(DEFAULT_TIMEOUT_MS),
            runner_client: Some(crate::runner_client::test_client_run_bytes(Some(raw))),
            runner_result: Some(reply),
            request_failure: None,
        }
    }

    const DATA_KEYS: [&str; 6] = [
        "policy_check",
        "runner_client",
        "runner_result",
        "runner_sandbox_diagnostics",
        "specimen",
        "timeout_ms",
    ];
    const DIAGNOSTIC_KEYS: [&str; 5] = [
        "disposition_integrity",
        "disposition_issues",
        "process_disposition",
        "stop_reason",
        "termination_cause",
    ];
    fn keys(value: &Value) -> Vec<&str> {
        value
            .as_object()
            .unwrap()
            .keys()
            .map(String::as_str)
            .collect()
    }

    #[test]
    fn finished_run_preserves_successful_and_failed_attempts() {
        let steps = vec![
            step("allowed", "open_read", "/allowed", "succeeded"),
            step("denied", "open_read", "/denied", "permission_failure"),
            step("missing", "open_read", "/missing", "other_failure"),
        ];
        for outcome in ["finished", "ok", "runner_failed", "validator_unavailable"] {
            let reply = reply_with(outcome, None, steps.clone());
            let (result, data, code) =
                execution_envelope(complete_execution(execution_data(Some(reply.clone()))));
            let wire: Value = serde_json::from_str(
                &json_contract::render_envelope("run", result, &data).unwrap(),
            )
            .unwrap();
            assert_eq!(code, if outcome == "finished" { 0 } else { 1 });
            assert_eq!(wire["result"]["ok"], outcome == "finished");
            assert_eq!(wire["result"]["normalized_outcome"], outcome);
            assert_eq!(
                serde_json::from_value::<PWRunnerRunResult>(wire["data"]["runner_result"].clone())
                    .unwrap(),
                fixture_reply(reply.clone())
            );
            assert_eq!(reply["steps"][0]["attempt"]["outcome"], "ok");
            assert_eq!(reply["steps"][1]["attempt"]["outcome"], "open_failed");
            assert_eq!(reply["steps"][2]["attempt"]["errno"], 2);
        }
    }

    #[test]
    fn execution_envelopes_preserve_raw_evidence_and_emit_only_execution_fields() {
        let rows = vec![
            step("a", "open_write", "/attempt", "permission_failure"),
            fresh_open_permission_failure("fresh", "/fresh"),
            incomplete_step("pending", "open_read", "/pending"),
        ];
        for phased in [false, true] {
            let mut steps = rows.clone();
            if phased {
                for (i, row) in steps.iter_mut().enumerate() {
                    row["phase_id"] = json!(format!("phase{i}"));
                }
            }
            let success = reply_with("finished", None, steps.clone());
            let failed = reply_with("runner_failed", Some(9), steps);
            let mut no_pid = success.clone();
            // A missing worker record is representable; a subprocess without
            // its required native PID is rejected by structural admission.
            no_pid["runner_subprocess"] = Value::Null;
            for (runner, code, disposition, cause) in [
                (Some(success.clone()), 0, "clean_exit", Value::Null),
                (Some(failed), 1, "signaled", json!("host_sentinel_deadline")),
                (Some(no_pid), 0, "withheld", json!("unknown")),
                (
                    Some(reporting_failed(success)),
                    1,
                    "clean_exit",
                    Value::Null,
                ),
                (None, 1, "no_worker", Value::Null),
            ] {
                let execution = complete_execution(execution_data(runner.clone()));
                let client = serde_json::to_value(&execution.data.runner_client).unwrap();
                let (result, data, exit_code) = execution_envelope(execution);
                let wire: Value = serde_json::from_str(
                    &json_contract::render_envelope("run", result, &data).unwrap(),
                )
                .unwrap();
                assert_eq!(exit_code, code);
                assert_eq!(wire["result"]["exit_code"], code);
                assert_eq!(
                    serde_json::from_value::<Option<PWRunnerRunResult>>(
                        wire["data"]["runner_result"].clone()
                    )
                    .unwrap(),
                    runner.clone().map(fixture_reply)
                );
                assert_eq!(wire["data"]["runner_client"], client);
                assert_eq!(keys(&wire["data"]), DATA_KEYS);
                let diagnostics = &wire["data"]["runner_sandbox_diagnostics"];
                assert_eq!(keys(diagnostics), DIAGNOSTIC_KEYS);
                assert_eq!(
                    diagnostics["process_disposition"],
                    disposition,
                    "phased={phased}, code={code}, reply={:?}, diagnostics={diagnostics}",
                    runner.as_ref().map(|r| &r["normalized_outcome"])
                );
                assert_eq!(diagnostics["termination_cause"], cause);
            }
        }
    }

    #[test]
    fn malformed_phase_claims_withhold_projection_and_preserve_raw_reply() {
        let mut baseline = worker("finished", None);
        baseline["phases"][0]["collection_status"] = json!("not_reached");
        baseline["phases"][0]["validator_subprocess"] = Value::Null;
        baseline["phases"][0]["ordering"]["validator_disposition"] = json!("not_invoked");
        for path in ["/phases/0/ordering/validator_disposition"] {
            let mut malformed = baseline.clone();
            *malformed.pointer_mut(path).unwrap() = json!("future_disposition");
            for degraded in [false, true] {
                let reply = if degraded {
                    reporting_failed(malformed.clone())
                } else {
                    malformed.clone()
                };
                let (result, data, code) =
                    execution_envelope(complete_execution(execution_data(Some(reply.clone()))));
                let wire: Value = serde_json::from_str(
                    &json_contract::render_envelope("run", result, &data).unwrap(),
                )
                .unwrap();
                assert_eq!(
                    serde_json::from_value::<PWRunnerRunResult>(
                        wire["data"]["runner_result"].clone()
                    )
                    .unwrap(),
                    fixture_reply(reply.clone())
                );
                assert_eq!(code, if degraded { 1 } else { 0 });
                let diagnostics = &wire["data"]["runner_sandbox_diagnostics"];
                if degraded {
                    assert!(
                        !diagnostics["disposition_issues"]
                            .as_array()
                            .unwrap()
                            .iter()
                            .any(|i| i["kind"] == "phase_collection")
                    );
                    assert_eq!(reply["normalized_outcome"], "runner_reporting_failed");
                } else {
                    assert_eq!(diagnostics["disposition_integrity"], "invalid");
                    assert_eq!(diagnostics["process_disposition"], "withheld");
                    assert_eq!(diagnostics["termination_cause"], "unknown");
                    assert!(
                        diagnostics["disposition_issues"]
                            .as_array()
                            .unwrap()
                            .iter()
                            .any(|i| i["kind"] == "phase_collection")
                    );
                }
            }
        }
    }

    #[test]
    #[ignore = "requires real Swift driver receipts; default runner_unit invokes this exact test"]
    fn policy_transfer_driver_replies_cross_assembly_and_consumer() {
        use std::io::Write;
        use std::process::{Command, Stdio};
        let directory = std::env::var("PW_POLICY_TRANSFER_REPLIES")
            .expect("runner_unit receipt directory required");
        for (name, filename) in [
            ("timeout", "policy-transfer-timeout.pwp"),
            ("unconfirmed", "policy-transfer-unconfirmed.pwp"),
            ("refused", "policy-transfer-refused.pwp"),
            ("reporting", "policy-transfer-reporting.pwp"),
            ("combined", "combined-phases.pwp"),
        ] {
            let raw = std::fs::read(std::path::Path::new(&directory).join(filename)).unwrap();
            let typed: PWRunnerRunResult = crate::porcelain::decode(&raw).unwrap();
            let reply = serde_json::to_value(&typed).unwrap();
            assert_eq!(
                reply["normalized_outcome"],
                match name {
                    "combined" => "validator_no_reply",
                    // The shipped worker's length refusal after the host's transfer
                    // timeout takes the existing worker-failure precedence.
                    "refused" => "runner_failed",
                    "reporting" => "runner_reporting_failed",
                    _ => "runner_timeout",
                }
            );
            let (result, data, code) =
                execution_envelope(complete_execution(driver_execution(typed, &raw)));
            assert_eq!(code, 1);
            let wire: Value = serde_json::from_str(
                &json_contract::render_envelope("run", result, &data).unwrap(),
            )
            .unwrap();
            assert_eq!(
                serde_json::from_value::<PWRunnerRunResult>(wire["data"]["runner_result"].clone())
                    .unwrap(),
                fixture_reply(reply.clone())
            );
            let diagnostics = &wire["data"]["runner_sandbox_diagnostics"];
            assert_eq!(diagnostics["disposition_integrity"], "valid");
            if name == "combined" {
                assert_eq!(
                    reply["phases"][0]["ordering"]["validator_disposition"],
                    "unconfirmed"
                );
                assert_eq!(
                    reply["phases"][1]["validator_subprocess"]["records"][0]["step_id"],
                    "later"
                );
            } else if name == "timeout" {
                assert_eq!(diagnostics["stop_reason"], "policy_transfer_deadline");
                assert_eq!(
                    diagnostics["termination_cause"],
                    "host_cleanup_after_transfer_timeout"
                );
            } else if name == "refused" {
                // Host timeout retained beside the worker's EOF receipt and refusal;
                // the worker exited on its own code, so no cleanup cause is projected.
                assert_eq!(diagnostics["stop_reason"], "policy_transfer_deadline");
                let sub = &reply["runner_subprocess"];
                assert_eq!(sub["policy_transfer_timeout"]["bytes_written"], 28);
                assert_eq!(sub["policy_transfer_timeout"]["bytes_expected"], 43);
                assert_eq!(
                    sub["worker_evidence"]["policy_read"],
                    json!({"bytes_expected": 43, "bytes_received": 28})
                );
                assert_eq!(sub["worker_evidence"]["failure"]["operation"], 2);
                assert_eq!(sub["worker_evidence"]["failure"]["code"], 13);
                assert_eq!(sub["worker_evidence"]["failure"]["detail"], 28);
                assert!(sub["worker_evidence"]["readiness"].is_null());
                assert_eq!(sub["exit_code"], 11);
                assert!(sub["term_signal"].is_null() && sub["termination_request"].is_null());
                assert_eq!(sub["grace_end"], "reaped_during_grace");
                assert_eq!(sub["cleanup_trigger"], "policy_transfer_timeout");
                assert_eq!(reply["sandboxed_after_apply"], false);
            } else if name == "reporting" {
                let sub = &reply["runner_subprocess"];
                assert_eq!(reply["reporting_failure"]["evidence_retained"], true);
                assert_eq!(sub["worker_evidence"]["policy_read"]["bytes_received"], 29);
                assert_eq!(sub["worker_evidence"]["failure"]["detail"], 28);
                assert!(
                    reply["steps"]
                        .as_array()
                        .unwrap()
                        .iter()
                        .all(|s| s["comparison"].is_null())
                );
            } else {
                assert!(
                    reply["runner_subprocess"]["exit_code"].is_null()
                        && reply["runner_subprocess"]["term_signal"].is_null()
                );
            }
            let mut child = Command::new("/usr/bin/python3").args(["-B", "-c", r#"import json,sys
sys.path.insert(0,sys.argv[1])
from consumer import validate_fixture,lifecycle as live_lifecycle
from functools import partial
validate = partial(validate_fixture, expected_contract="test:policy-witness")
lifecycle = partial(live_lifecycle, expected_contract="test:policy-witness")
from lifecycle_oracle import check_record as live_check_record
check_record = partial(live_check_record, expected_contract="test:policy-witness")
from blackbox import recapture_host_reply
e=json.load(sys.stdin); errors=validate(e); assert not errors,errors
errors=check_record(e); assert not errors,errors
sub=e['data']['runner_result']['runner_subprocess']
if e['data']['runner_result']['specimen_id']=='M08':
    phases=e['data']['runner_result']['phases']
    assert phases[0]['validator_subprocess']['stdout_collection_stop']=='deadline'
    assert phases[0]['validator_subprocess']['reaped'] is False
    assert [r['step_id'] for r in phases[1]['validator_subprocess']['records']]==['later']
else:
    assert sub.get('policy_transfer_error') is None and sub['policy_transfer_timeout']['bytes_written'] < sub['policy_transfer_timeout']['bytes_expected']
    if e['data']['runner_result'].get('reporting_failure') is None:
        assert lifecycle(e)['projections']['stop_reason']=='policy_transfer_deadline'
if e['data']['runner_result']['specimen_id']=='timeout':
    import copy
    # Construct a partial EOF observation before a cleanup kill; no later worker
    # evidence is present. The fixture itself does not publish this receipt.
    partial=copy.deepcopy(e); s=partial['data']['runner_result']['runner_subprocess']
    s['worker_evidence']['policy_read']={'bytes_expected':s['policy_transfer_timeout']['bytes_expected'],
        'bytes_received':s['policy_transfer_timeout']['bytes_written']}
    recapture_host_reply(partial)
    assert validate(partial)==[], validate(partial)
if e['data']['runner_result'].get('reporting_failure') is not None:
    import copy
    assert sub['worker_evidence']['policy_read']['bytes_received']==29
    assert sub['worker_evidence']['failure']['detail']==28
    assert all(s.get('comparison') is None for s in e['data']['runner_result']['steps'])
    malformed=copy.deepcopy(e)
    malformed['data']['runner_result']['runner_subprocess']['worker_evidence']['policy_read'].pop('bytes_received')
    recapture_host_reply(malformed)
    assert any('policy_read' in x for x in validate(malformed))
if e['data']['runner_result']['specimen_id']=='refused' and e['data']['runner_result'].get('reporting_failure') is None:
    import copy
    read=sub['worker_evidence']['policy_read']
    assert read=={'bytes_expected':43,'bytes_received':28} and sub['worker_evidence']['failure']['detail']==28, sub
    # Rejected variants: a refusal detail that is not the received count, a host
    # expectation that disagrees with the receipt, and a receipt member out of range.
    def rejected(mutate):
        bad=copy.deepcopy(e); mutate(bad['data']['runner_result']['runner_subprocess'])
        recapture_host_reply(bad)
        errors=validate(bad)
        assert any('policy_read' in x for x in errors), errors
    rejected(lambda s: s['worker_evidence']['failure'].update(detail=29))
    rejected(lambda s: s['policy_transfer_timeout'].update(bytes_expected=44))
    rejected(lambda s: s['worker_evidence']['policy_read'].update(bytes_received=-1))
    rejected(lambda s: s['worker_evidence']['policy_read'].pop('bytes_received'))
"#]).arg(std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../tests/lib"))
                .stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped()).spawn().unwrap();
            child
                .stdin
                .take()
                .unwrap()
                .write_all(&serde_json::to_vec(&wire).unwrap())
                .unwrap();
            let output = child.wait_with_output().unwrap();
            assert!(
                output.status.success(),
                "{}",
                String::from_utf8_lossy(&output.stderr)
            );
            std::fs::write(
                std::path::Path::new(&directory)
                    .join(format!("policy-transfer-{name}-envelope.json")),
                serde_json::to_vec_pretty(&wire).unwrap(),
            )
            .unwrap();
        }
    }

    #[test]
    #[ignore = "requires constructed Swift receipts; default runner_unit invokes this exact test"]
    fn reader_definition_corpus_cross_readers() {
        use std::process::Command;
        let directory =
            std::path::PathBuf::from(std::env::var("PW_POLICY_TRANSFER_REPLIES").unwrap())
                .join("reader-corpus");
        let manifest: Value =
            serde_json::from_slice(&std::fs::read(directory.join("swift.json")).unwrap()).unwrap();
        let mut cases = manifest["cases"].as_array().unwrap().clone();
        let writer_receipt: Value = serde_json::from_slice(
            &std::fs::read(directory.join("../porcelain-replies/writer-cap-receipt.json")).unwrap(),
        )
        .unwrap();
        cases.push(json!({"id": "writer-cap-minimal",
            "raw_file": "../porcelain-replies/writer-cap-minimal.pwp",
            "origin": "production_writer_capacity_refusal", "expected_semantic": true,
            "rule": "actual rich text budget refusal emits default minimal reporting",
            "writer_receipt": writer_receipt, "required_issues": [], "required_consumer_issues": []}));
        let mut rows = Vec::new();
        let mut problems = Vec::new();
        for case in &cases {
            let id = case["id"].as_str().unwrap();
            let filename = case["raw_file"]
                .as_str()
                .map(str::to_owned)
                .unwrap_or_else(|| format!("{id}.pwp"));
            let raw = std::fs::read(directory.join(filename)).unwrap();
            let typed: PWRunnerRunResult = crate::porcelain::decode(&raw).unwrap();
            let reply = serde_json::to_value(&typed).unwrap();
            if let Some(receipt) = case.get("writer_receipt") {
                if receipt["input"] != "constructed attempt.error"
                    || receipt["input_utf8_bytes"] != 134_217_729_u64
                    || receipt["frame_limit_bytes"] != 134_217_728_u64
                    || receipt["writer_calls"] != 2
                    || receipt["writer_failures"]
                        != json!(["text exceeds byte limit", "text exceeds byte limit"])
                    || receipt["emitted_bytes"] != json!(raw.len())
                    || reply["reporting_failure"]["evidence_retained"] != false
                    || reply["steps"] != json!([])
                    || reply["phases"] != json!([])
                {
                    problems.push(format!(
                        "{id}: actual writer-failure receipt or minimal consequence changed"
                    ));
                }
            }
            if let Some(expected) = case.get("application_expected") {
                let actor = reply["actors"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .find(|actor| actor["actor_id"] == expected["actor_id"])
                    .unwrap();
                if actor["application"]["state"] != expected["state"]
                    || actor["application"]["basis"] != expected["basis"]
                {
                    problems.push(format!(
                        "{id}: decoded application pair changed from its eligible source"
                    ));
                }
            }
            let issues = porcelain_admission::admit_reply(&typed)
                .err()
                .unwrap_or_default();
            let admitted = issues.is_empty();
            if admitted != case["expected_semantic"].as_bool().unwrap() {
                problems.push(format!("{id}: semantic admission {admitted}; {issues:?}"));
            }
            let issue_json = serde_json::to_value(&issues).unwrap();
            let mut previous_issue = None;
            for expected in case["required_issues"].as_array().into_iter().flatten() {
                match issues
                    .iter()
                    .position(|issue| issue.detail == expected.as_str().unwrap())
                {
                    Some(position) => {
                        if previous_issue.is_some_and(|previous| previous >= position) {
                            problems
                                .push(format!("{id}: required issue order changed; {issues:?}"));
                        }
                        previous_issue = Some(position);
                    }
                    None => {
                        problems.push(format!("{id}: missing exact issue {expected}; {issues:?}"))
                    }
                }
            }
            let outcome = typed.normalized_outcome.clone();
            let (result, data, code) =
                execution_envelope(complete_execution(driver_execution(typed, &raw)));
            let envelope: Value = serde_json::from_str(
                &json_contract::render_envelope("run", result, &data).unwrap(),
            )
            .unwrap();
            if envelope["data"]["runner_result"] != reply {
                problems.push(format!("{id}: assembly changed retained reply"));
            }
            if code != (if outcome == "finished" { 0 } else { 1 })
                || envelope["result"]["ok"] != json!(outcome == "finished")
                || envelope["result"]["normalized_outcome"] != json!(outcome)
            {
                problems.push(format!("{id}: semantic findings changed outer result/exit"));
            }
            let diagnostics = &envelope["data"]["runner_sandbox_diagnostics"];
            for expected in case["required_subject_issues"]
                .as_array()
                .into_iter()
                .flatten()
            {
                let matched = diagnostics["disposition_issues"]
                    .as_array()
                    .into_iter()
                    .flatten()
                    .filter(|issue| {
                        issue["detail"] == expected["detail"]
                            && issue["subject_path"] == expected["subject_path"]
                    })
                    .count();
                if matched != 1 {
                    problems.push(format!(
                        "{id}: expected exactly one finding at the inspected subject {expected}; {diagnostics}"
                    ));
                }
            }
            if !admitted
                && (diagnostics["process_disposition"] != "withheld"
                    || diagnostics["termination_cause"] != "unknown"
                    || diagnostics["disposition_integrity"] != "invalid")
            {
                problems.push(format!(
                    "{id}: rejected semantic record retained an aggregate certification"
                ));
            }
            let mut row = case.clone();
            row["rust_accepts"] = json!(admitted);
            row["issues"] = issue_json;
            row["reply"] = reply;
            row["envelope"] = envelope;
            row["exit_code"] = json!(code);
            rows.push(row);
        }
        // JSON-only inputs have no typed Swift equivalent. Deserialize is a
        // test helper, not a production reply transport. Preserve both views.
        let actor = rows.iter().find(|r| r["id"] == "actor-complete").unwrap()["reply"].clone();
        let preparation =
            rows.iter().find(|r| r["id"] == "preparation-0").unwrap()["reply"].clone();
        let ordinary = rows.iter().find(|r| r["id"] == "ordinary").unwrap()["reply"].clone();
        let mut json_rows = Vec::new();
        for (id, base, field, replacement, typed_expected, raw_expected) in [
            (
                "actor-preparation-null",
                &actor,
                "preparation_failure",
                Some(Value::Null),
                Some(true),
                false,
            ),
            (
                "ordinary-preparation-null",
                &ordinary,
                "preparation_failure",
                Some(Value::Null),
                Some(true),
                true,
            ),
            (
                "preparation-events-absent",
                &preparation,
                "extension_events",
                None,
                Some(false),
                false,
            ),
            (
                "preparation-events-null",
                &preparation,
                "extension_events",
                Some(Value::Null),
                Some(false),
                false,
            ),
            (
                "preparation-events-empty",
                &preparation,
                "extension_events",
                Some(json!([])),
                Some(true),
                true,
            ),
            (
                "preparation-events-wrong-type",
                &preparation,
                "extension_events",
                Some(json!("list")),
                None,
                false,
            ),
            (
                "actor-preparation-wrong-type",
                &actor,
                "preparation_failure",
                Some(json!(false)),
                None,
                false,
            ),
        ] {
            let mut input = base.clone();
            if let Some(value) = replacement {
                input[field] = value;
            } else {
                input.as_object_mut().unwrap().remove(field);
            }
            let mut row = json!({"id": id, "origin": "json_test_only", "input": input,
                "expected_raw_consumer": raw_expected, "expected_normalized_semantic": typed_expected});
            match serde_json::from_value::<PWRunnerRunResult>(input) {
                Ok(typed) => {
                    let issues = porcelain_admission::admit_reply(&typed)
                        .err()
                        .unwrap_or_default();
                    if Some(issues.is_empty()) != typed_expected {
                        problems.push(format!("{id}: unexpected normalized admission; {issues:?}"));
                    }
                    row["typed_decode"] = json!(true);
                    row["normalized"] = serde_json::to_value(&typed).unwrap();
                    row["issues"] = serde_json::to_value(&issues).unwrap();
                    row["rust_accepts"] = json!(issues.is_empty());
                }
                Err(error) => {
                    if typed_expected.is_some() {
                        problems.push(format!("{id}: {error}"));
                    }
                    row["typed_decode"] = json!(false);
                    row["typed_error"] = json!(error.to_string());
                }
            }
            json_rows.push(row);
        }
        let report = json!({"domain": manifest["domain"], "cases": rows, "json_only": json_rows,
            "rust_failures": problems});
        std::fs::write(
            directory.join("rust.json"),
            serde_json::to_vec_pretty(&report).unwrap(),
        )
        .unwrap();
        let python = std::env::var("PW_PYTHON").unwrap_or_else(|_| "/usr/bin/python3".into());
        let script = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../tests/suites/runner_unit/reader_corpus.py");
        let output = Command::new(python)
            .arg("-B")
            .arg(script)
            .arg(&directory)
            .output()
            .unwrap();
        assert!(problems.is_empty(), "{}", problems.join("\n"));
        assert!(
            output.status.success(),
            "{}\n{}",
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr)
        );
    }

    #[test]
    #[ignore = "requires real Swift driver receipts; default runner_unit invokes this exact test"]
    fn actor_driver_replies_cross_readers() {
        use std::io::Write;
        use std::process::{Command, Stdio};
        let directory = std::env::var("PW_POLICY_TRANSFER_REPLIES").unwrap();
        let mut controls = Vec::new();
        for name in [
            "complete",
            "setup",
            "interrupted",
            "transfer-interrupted",
            "late-setup",
            "failed-setup",
        ] {
            let raw = std::fs::read(
                std::path::Path::new(&directory).join(format!("actor-review-{name}.pwp")),
            )
            .unwrap();
            let typed: PWRunnerRunResult = crate::porcelain::decode(&raw).unwrap();
            let reply = serde_json::to_value(&typed).unwrap();
            if name == "late-setup" {
                let actor = &reply["actors"][1];
                assert_eq!(actor["setup_status"], "setup_timeout");
                assert_eq!(actor["applied"], true);
                assert_eq!(actor["application_count"], 1);
                assert_eq!(actor["application"]["state"], "observed");
                assert_eq!(actor["application"]["basis"], "applied_publication");
                assert!(
                    reply["phases"]
                        .as_array()
                        .unwrap()
                        .iter()
                        .filter(|phase| phase["actor_id"] == actor["actor_id"])
                        .all(|phase| phase["arrival_observed"] == false
                            && phase["completion_observed"] == false
                            && phase["collection_status"] == "not_reached")
                );
            }
            controls.push(json!({"name": name, "reply": reply, "accepted": true}));
            let changes = match name {
                "complete" => vec![
                    ("/extension_events/0/native_nonnull", json!(false)),
                    ("/resources/tokens/0/status", json!("null")),
                    ("/resources/handles/0/native_handle", json!(999999)),
                    ("/transfers/0/recipient_acknowledged", json!(false)),
                    ("/transfers/0/equality", json!("unequal")),
                    ("/transfers/0/status", json!("custody_unavailable")),
                    ("/transfers", json!([])),
                    ("/resources/deliveries/0/status", json!("not_reached")),
                    ("/resources/deliveries/0/equality", json!("unequal")),
                    ("/resources/deliveries/0/delivered_length", json!(0)),
                    ("/resources/handles/0/release_attempted", json!(false)),
                    ("/resources/handles/0/raw_equal_handles", json!(["hc"])),
                    ("/transfers/0/phase_id", json!("b_redelegate")),
                ],
                "transfer-interrupted" => vec![("/transfers/0/source_acknowledged", json!(true))],
                "late-setup" => vec![("/actors/1/application_count", json!(0))],
                "failed-setup" => vec![],
                _ => vec![("/resources/tokens/0/status", json!("not_reached"))],
            };
            for (pointer, value) in changes {
                let mut changed = reply.clone();
                *changed.pointer_mut(pointer).unwrap() = value;
                controls.push(json!({"name": format!("{name}:{pointer}"), "reply": changed, "accepted": false}));
            }
            if name == "complete" {
                let mut changed = reply.clone();
                changed["extension_events"][2]["delivery_ref"] = json!("dc");
                changed["resources"]["handles"][0]["delivery_ref"] = json!("dc");
                controls.push(json!({"name": "consume another recipient's future delivery", "reply": changed, "accepted": false}));
                for token in ["absent", "tb"] {
                    let mut changed = reply.clone();
                    changed["extension_events"][1]["token_ref"] = json!(token);
                    changed["resources"]["deliveries"][0]["token_ref"] = json!(token);
                    changed["transfers"][0]["token_ref"] = json!(token);
                    controls.push(json!({"name": format!("transfer unowned token {token}"), "reply": changed, "accepted": false}));
                }
                for pointer in [
                    "/resources/tokens",
                    "/resources/deliveries",
                    "/resources/handles",
                    "/transfers",
                ] {
                    let mut changed = reply.clone();
                    let rows = changed
                        .pointer_mut(pointer)
                        .unwrap()
                        .as_array_mut()
                        .unwrap();
                    rows.push(rows[0].clone());
                    controls.push(json!({"name": format!("duplicate {pointer}"), "reply": changed, "accepted": false}));
                }
                let mut changed = reply.clone();
                changed["extension_events"][0]["native_nonnull"] = json!(false);
                changed["transfers"] = json!([]);
                controls.push(json!({"name": "combined native contradiction and missing host transfer", "reply": changed, "accepted": false,
                    "required_issues": ["issue nonnull disagrees with native result", "delivery claims host observation without transfer"]}));
            }
        }
        for control in &controls {
            let diagnostics = porcelain_admission::execution_diagnostics(Some(&fixture_reply(
                control["reply"].clone(),
            )));
            assert_eq!(
                diagnostics.disposition_integrity != Some("invalid"),
                control["accepted"] == true,
                "{}: {:?}",
                control["name"],
                diagnostics.disposition_issues
            );
            for expected in control["required_issues"].as_array().into_iter().flatten() {
                assert!(
                    serde_json::to_string(&diagnostics.disposition_issues)
                        .unwrap()
                        .contains(expected.as_str().unwrap())
                );
            }
        }
        // Independently read the same actual publications and rejected variants.
        // The Python oracle does not call the Swift or Rust classifiers.
        let mut child = Command::new("/usr/bin/python3")
            .args([
                "-B",
                "-c",
                r#"
import json, sys
from copy import deepcopy
sys.path.insert(0, sys.argv[1])
from consumer import validate_fixture, validate_shape, REPLY_SHAPE
from functools import partial
validate = partial(validate_fixture, expected_contract="test:policy-witness")
for control in json.load(sys.stdin):
    errors = validate(control['reply'])
    assert (not errors) == control['accepted'], (control['name'], errors)
    for expected in control.get('required_issues', []):
        assert expected in errors, (control['name'], expected, errors)
    if control['name'] == 'failed-setup':
        evidence = control['reply']['actors'][1]['subprocess']['worker_evidence']
        # Shape-only controls preserve optionality and type checking. The live
        # compile failure above establishes the public native_result path;
        # constructed neighboring fields exercise the rest of the same type.
        for component, fields in [('failure', {'native_result': 0, 'errno': 22, 'index': 0}),
                                  ('progress', {'index': 0})]:
            path = 'reply.actors[].subprocess.worker_evidence.' + component
            complete = dict(evidence[component], **fields)
            for absent in [None, *fields]:
                value = deepcopy(complete)
                if absent is not None:
                    del value[absent]
                errors = []
                validate_shape(value, path, REPLY_SHAPE, errors)
                assert not errors, (path, absent, errors)
            for field in fields:
                value = dict(complete, **{field: 'wrong type'})
                errors = []
                validate_shape(value, path, REPLY_SHAPE, errors)
                assert errors == [f'{path}.{field} is string, not number'], errors
            errors = []
            validate_shape(dict(complete, unexpected=True), path, REPLY_SHAPE, errors)
            assert errors == [f'unknown key {path}.unexpected'], errors
"#,
            ])
            .arg(std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../tests/lib"))
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .unwrap();
        child
            .stdin
            .take()
            .unwrap()
            .write_all(&serde_json::to_vec(&controls).unwrap())
            .unwrap();
        let output = child.wait_with_output().unwrap();
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
        std::fs::write(
            std::path::Path::new(&directory).join("actor-review-reader-controls.json"),
            serde_json::to_vec_pretty(&controls).unwrap(),
        )
        .unwrap();
    }

    #[test]
    #[ignore = "requires real Swift driver receipts; default runner_unit invokes this exact test"]
    fn worker_clock_driver_replies_cross_assembly_and_consumer() {
        use std::io::Write;
        use std::process::{Command, Stdio};
        let directory = std::env::var("PW_POLICY_TRANSFER_REPLIES")
            .expect("runner_unit receipt directory required");
        let mut replies: Vec<(String, &str)> = Vec::new();
        for reason in ["native", "zero_factor", "unrepresentable"] {
            for delivery in ["buffered", "blocked"] {
                replies.push((format!("setup-{reason}-{delivery}"), "runner_failed"));
            }
        }
        for (name, outcome) in [
            ("phase2-own-sample", "runner_failed"),
            ("phase2-own-sample-delayed-host", "runner_failed"),
            ("phase2-expiry", "runner_failed"),
            ("phase2-expiry-delayed-host", "runner_failed"),
            ("sticky-provenance", "runner_failed"),
            ("arithmetic-local", "finished"),
        ] {
            replies.push((name.to_string(), outcome));
        }
        for (name, outcome) in replies {
            let path = std::path::Path::new(&directory).join(format!("worker-clock-{name}.pwp"));
            let raw = std::fs::read(&path).unwrap();
            let typed: PWRunnerRunResult = crate::porcelain::decode(&raw).unwrap();
            let reply = serde_json::to_value(&typed).unwrap();
            assert_eq!(reply["normalized_outcome"], outcome, "{name}");
            let (result, data, code) =
                execution_envelope(complete_execution(driver_execution(typed, &raw)));
            assert_eq!(code, if outcome == "finished" { 0 } else { 1 }, "{name}");
            let wire: Value = serde_json::from_str(
                &json_contract::render_envelope("run", result, &data).unwrap(),
            )
            .unwrap();
            assert_eq!(
                serde_json::from_value::<PWRunnerRunResult>(wire["data"]["runner_result"].clone())
                    .unwrap(),
                fixture_reply(reply.clone())
            );
            let diagnostics = &wire["data"]["runner_sandbox_diagnostics"];
            assert_eq!(diagnostics["disposition_integrity"], "valid", "{name}");
            let sub = &reply["runner_subprocess"];
            let failure = &sub["worker_evidence"]["failure"];
            let record = |op: u64, code: u64, detail: u64| {
                assert_eq!(
                    (&failure["operation"], &failure["code"], &failure["detail"]),
                    (&json!(op), &json!(code), &json!(detail)),
                    "{name}"
                );
                assert!(failure["native_result"].is_null() && failure["errno"].is_null());
            };
            if name.starts_with("setup-") {
                // Clock setup is a pre-apply refusal: published failure, exit 12,
                // no completion, application, readiness or policy receipt.
                assert_eq!(failure["operation"], 12);
                assert_eq!(sub["worker_evidence"]["progress"]["operation"], 12);
                assert!(failure["errno"].is_null());
                assert!(sub["worker_evidence"]["policy_read"].is_null());
                assert_eq!(sub["exit_code"], 12);
                assert_eq!(sub["done_observed"], false);
                assert_eq!(reply["sandboxed_after_apply"], false);
            } else {
                match name.as_str() {
                    "phase2-own-sample" | "phase2-own-sample-delayed-host" => record(11, 14, 3),
                    "phase2-expiry" | "phase2-expiry-delayed-host" => record(11, 8, 60_000),
                    "sticky-provenance" => record(11, 14, 6),
                    _ => assert!(failure.is_null(), "{name}"),
                }
                // Phase 1's chain survives; phase 2 acts only when released.
                assert_eq!(reply["phases"][0]["ordering"]["proceed_observed"], true);
                let released = name == "arithmetic-local";
                assert_eq!(reply["phases"][1]["ordering"]["proceed_observed"], released);
                assert_eq!(
                    reply["steps"][1]["comparison"]["order"],
                    if released {
                        "query_first"
                    } else {
                        "unestablished"
                    }
                );
            }
            let mut child = Command::new("/usr/bin/python3")
                .args([
                    "-B",
                    "-c",
                    r#"import json,sys
sys.path.insert(0,sys.argv[1])
from consumer import validate_fixture,lifecycle as live_lifecycle
from functools import partial
validate = partial(validate_fixture, expected_contract="test:policy-witness")
lifecycle = partial(live_lifecycle, expected_contract="test:policy-witness")
from lifecycle_oracle import check_record as live_check_record
check_record = partial(live_check_record, expected_contract="test:policy-witness")
e=json.load(sys.stdin); errors=validate(e); assert not errors,errors
errors=check_record(e); assert not errors,errors
sub=e['data']['runner_result']['runner_subprocess']
if sys.argv[2].startswith('setup-'):
    assert sub['worker_evidence']['failure']['operation']==12 and sub['exit_code']==12, sub
    assert lifecycle(e)['summaries']==['not_reached'], lifecycle(e)
else:
    steps=e['data']['runner_result']['steps']
    assert steps[0]['attempt']['result_source']=='worker', steps[0]
"#,
                ])
                .arg(std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../tests/lib"))
                .arg(&name)
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .spawn()
                .unwrap();
            child
                .stdin
                .take()
                .unwrap()
                .write_all(&serde_json::to_vec(&wire).unwrap())
                .unwrap();
            let output = child.wait_with_output().unwrap();
            assert!(
                output.status.success(),
                "{name}: {}",
                String::from_utf8_lossy(&output.stderr)
            );
            std::fs::write(
                std::path::Path::new(&directory).join(format!("worker-clock-{name}-envelope.json")),
                serde_json::to_vec_pretty(&wire).unwrap(),
            )
            .unwrap();
        }
    }

    #[test]
    fn argument_errors_are_reported_before_any_runner_or_specimen_work() {
        for (flag, value) in [("--timeout-ms", "invalid"), ("--runner-mode", "invalid")] {
            assert!(
                matches!(
                    parse_arguments(&["/r.json".into(), flag.into(), value.into()]),
                    Arguments::Error(None, _)
                ),
                "{flag}: invalid flag values carry no request path"
            );
        }
        // The path seen so far is retained for the dossier of the refusal.
        match parse_arguments(&["/r.json".into(), "--bogus".into()]) {
            Arguments::Error(Some(path), error) => {
                assert_eq!(path, PathBuf::from("/r.json"));
                assert!(error.contains("unknown argument"));
            }
            _ => panic!("unknown argument accepted"),
        }
        assert!(matches!(parse_arguments(&["-h".into()]), Arguments::Help));
    }

    #[test]
    fn documented_controller_limits() {
        let manifest: serde_json::Value =
            serde_json::from_str(include_str!("../../docs/limits.json")).unwrap();
        let owned: std::collections::BTreeMap<&str, u64> = manifest["limits"]
            .as_array()
            .unwrap()
            .iter()
            .filter(|row| {
                row["checks"].as_array().unwrap().iter().any(|check| {
                    check["path"] == "controller/src/run_flow.rs" && check["kind"] == "value"
                })
            })
            .map(|row| (row["id"].as_str().unwrap(), row["value"].as_u64().unwrap()))
            .collect();
        let actual = std::collections::BTreeMap::from([
            ("client_rpc_wait", DEFAULT_TIMEOUT_MS),
            (
                "controller_output",
                crate::utils::RUNNER_CAPTURE_BYTES as u64,
            ),
            (
                "policy_helper_output",
                crate::utils::HELPER_CAPTURE_BYTES as u64,
            ),
        ]);
        assert_eq!(owned, actual);
        // The behavioral oracle is independent of the documented value.
        let cap = crate::utils::RUNNER_CAPTURE_BYTES;
        for len in [cap - 1, cap, cap + 1] {
            let bytes = vec![b'x'; len];
            let (text, truncated) = crate::utils::truncate_output(&bytes, cap);
            assert_eq!(text.len(), len.min(cap));
            assert_eq!(truncated, len > cap);
        }
    }

    // ---- D5: the reply version gate ----------------------------------------

    #[test]
    fn compiled_profile_context_is_gated_after_the_response_version() {
        let cases: Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/contract/compiled_profile.json"
        ))
        .unwrap();
        for case in cases.as_array().unwrap() {
            let mut input = worker("finished", None);
            input["compiled_profile"] = case["receipt"].clone();
            let typed = serde_json::from_value::<PWRunnerRunResult>(input);
            let accepted = typed
                .as_ref()
                .is_ok_and(|r| matches!(reply_version(r), ReplyVersion::Supported));
            assert_eq!(
                accepted,
                case["valid"].as_bool().unwrap(),
                "{}",
                case["name"]
            );
            if let Ok(mut old) = typed {
                old.producer.contract = "test:foreign".into();
                assert!(matches!(reply_version(&old), ReplyVersion::Unsupported(_)));
            }
        }
    }

    #[test]
    fn reply_versions_are_gated_exactly() {
        let current = json_contract::BUILD_CONTRACT;
        let mut reply = fixture_reply(worker("finished", None));
        assert!(matches!(reply_version(&reply), ReplyVersion::Supported));
        for other in ["test:previous", "test:next", "", "unbound"] {
            reply.producer.contract = other.into();
            match reply_version(&reply) {
                ReplyVersion::Unsupported(version) => assert_eq!(version, other),
                _ => panic!("{other} admitted"),
            }
        }
        // Missing, wrong-kind, overflow and unknown tags are rejected by binary
        // structural admission before a typed value exists (porcelain controls).
    }

    #[test]
    fn delivery_failure_takes_precedence_and_retains_the_client_frame_unread() {
        let current = json_contract::BUILD_CONTRACT;
        let reply = worker("finished", None);
        let mut unsupported = fixture_reply(reply.clone());
        unsupported.producer.contract = "test:foreign".into();
        let mut broken = client_run(Some(&reply));
        broken.request_delivery = Some(RequestDelivery {
            bytes_written: 1,
            error: Some("request delivery failed after 1 bytes: Broken pipe (os error 32)".into()),
        });
        broken.transport_admission = "delivery_failed".into();
        broken.transport_error = broken.request_delivery.as_ref().unwrap().error.clone();
        broken.submission = "unknown".into();
        let retained_transport = broken.transport.clone();
        let intact = client_run(Some(&reply));
        let reply = fixture_reply(reply);
        for captured in [Some(&reply), Some(&unsupported), None] {
            match admit_reply(&broken, captured) {
                ReplyAdmission::DeliveryFailed(error) => assert!(error.contains("Broken pipe")),
                _ => panic!("delivery error must take precedence"),
            }
        }
        assert!(matches!(
            admit_reply(&intact, Some(&reply)),
            ReplyAdmission::Admitted
        ));
        assert!(matches!(
            admit_reply(&intact, None),
            ReplyAdmission::Admitted
        ));
        match admit_reply(&intact, Some(&unsupported)) {
            ReplyAdmission::Refused { outcome, error } => {
                assert_eq!(outcome, "unsupported_runner_response");
                assert!(error.contains("contract test:foreign"), "{error}");
                assert!(error.contains(&format!("reads only {current}")), "{error}");
            }
            _ => panic!("unsupported version admitted"),
        }
        // Failed local delivery retains the outer capture opaquely, without
        // recovering a host body, policy check or diagnostics.
        let data = execution_only(specimen(), Some(7), Some(broken), None);
        let text = json_contract::render_envelope(
            "run",
            json_contract::JsonResult::new(false, 2, Some("tool_error"), Some("controlled".into())),
            &data,
        )
        .unwrap();
        let wire: Value = serde_json::from_str(&text).unwrap();
        assert_eq!(keys(&wire["data"]), DATA_KEYS);
        assert!(wire["data"]["runner_result"].is_null());
        assert_eq!(
            wire["data"]["runner_client"]["transport"],
            serde_json::to_value(retained_transport.unwrap()).unwrap()
        );
        assert_eq!(wire["data"]["runner_client"]["submission"], "unknown");
        assert_eq!(
            wire["data"]["runner_client"]["request_delivery"]["bytes_written"],
            1
        );
        assert!(wire["data"]["runner_client"]["request_delivery"]["error"].is_string());
        assert!(wire["data"]["policy_check"].is_null());
        assert!(wire["data"]["runner_sandbox_diagnostics"].is_null());
        assert_eq!(wire["data"]["timeout_ms"], 7);
        assert_eq!(wire["result"]["exit_code"], 2);
        assert_eq!(wire["result"]["normalized_outcome"], "tool_error");
        assert!(wire["data"].get("error").is_none());
    }

    #[test]
    fn fallback_compilation_is_requested_only_for_an_admitted_xpc_error() {
        let xpc_error = json!({"producer": crate::reply_fixtures::producer(),
            "normalized_outcome": "xpc_error", "error": "NSCocoaErrorDomain:4099 refused", "steps": [], "phases":[], "specimen_id":"controlled", "rc":1, "pid":42});
        let failed_client = client_run(None);
        let before = serde_json::to_value(&failed_client).unwrap();
        let mut invoked = 0;
        let capture = fallback_policy_check(&failed_client, || {
            invoked += 1;
            Err("sbpl-check request delivery failed: Broken pipe".into())
        });
        assert_eq!(invoked, 1);
        let capture = capture.expect("an admitted client xpc_error requests the helper");
        assert_eq!(capture.status, "unavailable");
        assert!(capture.envelope.is_none());
        assert!(
            capture.output.stderr.contains("Broken pipe"),
            "{}",
            capture.output.stderr
        );
        assert_eq!(serde_json::to_value(&failed_client).unwrap(), before);
        let mut invoked = 0;
        for reply in [
            worker("finished", None),
            worker("runner_failed", Some(9)),
            worker("xpc_timeout", None),
            xpc_error.clone(),
        ] {
            assert!(
                fallback_policy_check(&client_run(Some(&reply)), || {
                    invoked += 1;
                    Err("never requested".into())
                })
                .is_none()
            );
        }
        let mut missing = client_run(None);
        missing.transport = None;
        missing.transport_admission = "missing".into();
        missing.transport_error = Some("no complete client capture".into());
        missing.submission = "unknown".into();
        assert!(
            fallback_policy_check(&missing, || {
                invoked += 1;
                Err("never requested".into())
            })
            .is_none()
        );
        assert_eq!(invoked, 0);

        // Helper success, rejection and an unavailable capture leave the
        // client evidence and the controller's outcome unchanged.
        let helper_envelope = |outcome: &str| {
            json!({"build": {"contract": json_contract::BUILD_CONTRACT}, "kind": "sbpl_check",
                "result": {"normalized_outcome": outcome}, "data": {}})
        };
        let captures = [
            ("ok", Some(helper_envelope("ok"))),
            ("compile_error", Some(helper_envelope("compile_error"))),
            ("unavailable", None),
        ];
        for (status, envelope) in captures {
            let capture = PolicyCheckCapture {
                status: status.into(),
                tool_exit_code: if status == "ok" { 0 } else { 1 },
                output: crate::utils::TextOutputCapture::unavailable(
                    String::new(),
                    crate::utils::HELPER_CAPTURE_BYTES,
                ),
                envelope: envelope.clone(),
            };
            let client = client_run(None);
            let (outcome, error) = client.failure().unwrap();
            let mut data = execution_only(specimen(), Some(7), Some(client), None);
            data.execution.policy_check = Some(capture);
            let text = json_contract::render_envelope(
                "run",
                json_contract::JsonResult::new(false, 1, Some(outcome), Some(error)),
                &data,
            )
            .unwrap();
            let wire: Value = serde_json::from_str(&text).unwrap();
            assert_eq!(
                wire["result"]["normalized_outcome"], "xpc_error",
                "{status}"
            );
            assert_eq!(wire["result"]["error"], "controlled XPC error", "{status}");
            assert!(wire["data"]["runner_result"].is_null(), "{status}");
            assert_eq!(wire["data"]["runner_client"], before, "{status}");
            let check = data.execution.policy_check.as_ref().unwrap();
            assert_eq!(check.status, status);
            assert_eq!(check.envelope, envelope);
        }
    }

    #[test]
    fn tool_error_envelope_has_the_uniform_run_shape() {
        let (result, data) = tool_error_envelope(specimen(), None, "missing <request.json>".into());
        let text = json_contract::render_envelope("run", result, &data).unwrap();
        let wire: Value = serde_json::from_str(&text).unwrap();
        assert_eq!(wire["kind"], "run");
        assert_eq!(wire["build"]["contract"], json_contract::BUILD_CONTRACT);
        assert_eq!(wire["result"]["ok"], false);
        assert_eq!(wire["result"]["exit_code"], 2);
        assert_eq!(wire["result"]["normalized_outcome"], "tool_error");
        assert_eq!(wire["result"]["error"], "missing <request.json>");
        assert_eq!(keys(&wire["data"]), DATA_KEYS);
        for key in [
            "policy_check",
            "runner_client",
            "runner_result",
            "runner_sandbox_diagnostics",
            "timeout_ms",
        ] {
            assert!(wire["data"][key].is_null(), "{key}");
        }
        let specimen = &wire["data"]["specimen"];
        assert_eq!(
            keys(specimen),
            [
                "app_provenance",
                "binaries",
                "host",
                "policy",
                "request_path",
                "runner_provenance"
            ]
        );
        assert_eq!(specimen["request_path"], "/controlled/request.json");
        assert_eq!(specimen["host"]["macos_build"], "23A000");
        assert_eq!(
            specimen["policy"]["augmentation"]["status"],
            "not_applicable"
        );
        assert_eq!(specimen["policy"]["imports"]["status"], "not_applicable");
        for role in ["service", "worker", "validator"] {
            assert_eq!(specimen["binaries"][role]["verification"], "unavailable");
            assert!(specimen["binaries"][role]["reason"].is_string());
        }
    }

    #[test]
    fn policy_dossier_follows_the_request_state_table() {
        let source = "(version 1)\n(allow default)\n";
        let hash = crate::digest::sha256_hex(source);
        // String source, no augments (also null or empty augments).
        for resolution in [
            AugmentResolution::NotPresent,
            AugmentResolution::StrippedNoOp,
        ] {
            let (policy, error) = policy_dossier(Some(source), &resolution, Some(source));
            assert!(error.is_none());
            assert_eq!(policy.augmentation.status, "not_requested");
            assert!(policy.augmentation.applied.is_empty());
            assert_eq!(
                policy.augmentation.original_sha256.as_deref(),
                Some(hash.as_str())
            );
            assert_eq!(
                policy.augmentation.applied_sha256.as_deref(),
                Some(hash.as_str())
            );
            assert!(policy.augmentation.error.is_none());
            assert_eq!(policy.imports.status, "complete");
            assert!(policy.imports.closure_sha256.is_some());
            assert!(policy.imports.records.is_empty() && policy.imports.failure.is_none());
        }
        // Augments successfully applied; the original hash only if a string existed.
        let record = crate::augments::PolicyAugmentation {
            applied: vec!["exec_baseline".into()],
            original_sha256: hash.clone(),
            applied_sha256: "a".repeat(64),
        };
        let applied_source = "(version 1)\n(allow default)\n; augment\n";
        for original in [Some(source), None] {
            let (policy, error) = policy_dossier(
                original,
                &AugmentResolution::Applied(record.clone()),
                Some(applied_source),
            );
            assert!(error.is_none());
            assert_eq!(policy.augmentation.status, "applied");
            assert_eq!(
                policy.augmentation.applied,
                vec!["exec_baseline".to_string()]
            );
            assert_eq!(
                policy.augmentation.original_sha256.as_deref(),
                original.map(|_| hash.as_str())
            );
            assert_eq!(
                policy.augmentation.applied_sha256.as_deref(),
                Some("a".repeat(64).as_str())
            );
            assert_eq!(policy.imports.status, "complete");
            assert_eq!(
                policy.imports.closure_sha256,
                Some(crate::sbpl_imports::compute_closure_hash(
                    applied_source,
                    &[]
                ))
            );
        }
        // Augment resolution refused: atomic, nothing applied, imports not run.
        let refusal = AugmentResolution::BadRequest(RequestError::new(
            "augment_unavailable",
            &["policy", "augments", "0"],
            "unknown augment: nope",
        ));
        let (policy, error) = policy_dossier(Some(source), &refusal, Some(source));
        assert_eq!(
            error.as_ref().map(|e| e.message.as_str()),
            Some("unknown augment: nope")
        );
        assert_eq!(policy.augmentation.status, "failed");
        assert!(policy.augmentation.applied.is_empty());
        assert_eq!(
            policy.augmentation.original_sha256.as_deref(),
            Some(hash.as_str())
        );
        assert!(policy.augmentation.applied_sha256.is_none());
        assert_eq!(
            policy.augmentation.error.as_deref(),
            Some("unknown augment: nope")
        );
        assert_eq!(policy.imports.status, "not_applicable");
        assert_eq!(
            policy.imports.failure.as_deref(),
            Some("augmentation_failed")
        );
        assert!(policy.imports.closure_sha256.is_none() && policy.imports.records.is_empty());
        // Missing or malformed source, no augments applied: nothing to hash or scan.
        let (policy, error) = policy_dossier(None, &AugmentResolution::NotPresent, None);
        assert!(error.is_none());
        assert_eq!(policy.augmentation.status, "not_applicable");
        assert!(policy.augmentation.original_sha256.is_none());
        assert!(policy.augmentation.applied_sha256.is_none());
        assert!(policy.augmentation.error.is_none());
        assert_eq!(policy.imports.status, "not_applicable");
        assert!(policy.imports.failure.is_none());
        let wire = serde_json::to_value(&policy).unwrap();
        assert_eq!(
            keys(&wire["augmentation"]),
            [
                "applied",
                "applied_sha256",
                "error",
                "original_sha256",
                "status"
            ]
        );
        assert_eq!(
            keys(&wire["imports"]),
            [
                "closure_sha256",
                "cycle",
                "exceeded",
                "failure",
                "records",
                "status"
            ]
        );
    }

    #[test]
    fn actor_policy_dossiers_follow_each_actor_and_report_the_first_refusal() {
        use crate::augments::ActorAugmentResolution;
        let source = "(version 1)\n(allow default)\n";
        let hash = crate::digest::sha256_hex(source);
        let resolutions = vec![
            ActorAugmentResolution {
                index: 0,
                actor_id: Some("A".into()),
                mode: Some("unapplied".into()),
                original_source: None,
                selected_source: None,
                resolution: AugmentResolution::NotPresent,
            },
            ActorAugmentResolution {
                index: 1,
                actor_id: Some("B".into()),
                mode: Some("apply".into()),
                original_source: Some(source.into()),
                selected_source: Some(source.into()),
                resolution: AugmentResolution::StrippedNoOp,
            },
            ActorAugmentResolution {
                index: 2,
                actor_id: None,
                mode: Some("apply".into()),
                original_source: Some(source.into()),
                selected_source: Some(source.into()),
                resolution: AugmentResolution::BadRequest(RequestError::new(
                    "augment_unavailable",
                    &["actors", "2", "sandbox", "policy", "augments", "0"],
                    "unknown augment: nope",
                )),
            },
        ];
        let (dossiers, error) = actor_policy_dossiers(&resolutions);
        assert_eq!(dossiers.len(), 3);
        assert_eq!(dossiers[0].actor_id.as_deref(), Some("A"));
        assert_eq!(dossiers[0].mode.as_deref(), Some("unapplied"));
        assert_eq!(dossiers[0].policy.augmentation.status, "not_applicable");
        assert_eq!(dossiers[0].policy.imports.status, "not_applicable");
        assert_eq!(dossiers[1].policy.augmentation.status, "not_requested");
        assert_eq!(
            dossiers[1].policy.augmentation.applied_sha256.as_deref(),
            Some(hash.as_str())
        );
        assert_eq!(dossiers[1].policy.imports.status, "complete");
        assert!(dossiers[2].actor_id.is_none());
        assert_eq!(dossiers[2].policy.augmentation.status, "failed");
        assert_eq!(
            error.as_ref().map(|e| e.failure.code.as_str()),
            Some("augment_unavailable")
        );
        let wire = serde_json::to_value(&dossiers[1]).unwrap();
        assert_eq!(keys(&wire), ["actor_id", "mode", "policy"]);
        let mut specimen = specimen();
        assert!(
            serde_json::to_value(&specimen)
                .unwrap()
                .get("actors")
                .is_none()
        );
        specimen.actors = Some(dossiers);
        assert_eq!(
            serde_json::to_value(&specimen).unwrap()["actors"]
                .as_array()
                .unwrap()
                .len(),
            3
        );
    }

    #[test]
    fn runner_mode_injection_rules() {
        let mut request = json!({"policy": {}, "runner": {"id": "external"}});
        assert!(
            inject_runner_mode(&mut request, "machme")
                .unwrap_err()
                .message
                .contains("byoxpc")
        );
        assert!(
            inject_runner_mode(&mut request, "nope")
                .unwrap_err()
                .message
                .contains("invalid value for --runner-mode")
        );
        inject_runner_mode(&mut request, "byoxpc").unwrap();
        assert_eq!(request["runner"]["mode"], "byoxpc");
        inject_runner_mode(&mut request, "byoxpc").unwrap();
        assert!(
            inject_runner_mode(&mut request, "standard")
                .unwrap_err()
                .message
                .contains("already includes runner.mode")
        );
        let mut scalar = json!({"runner": 5});
        assert!(
            inject_runner_mode(&mut scalar, "standard")
                .unwrap_err()
                .message
                .contains("runner must be a JSON object")
        );
    }

    // ---- Controlled orchestration --------------------------------------------
    // `run` with its production dependencies replaced at the observed boundaries:
    // a counting loader around the real manifest reader, a synthetic app root,
    // an on-disk registry fixture and a capturing client that answers with a
    // current-schema reply. Every assertion reads the rendered envelope or a
    // capture; nothing here reconstructs orchestration or counts source calls.
    mod orchestration {
        use super::*;
        use crate::app_layout::{
            SHIPPED_SERVICE, SHIPPED_UNENTITLED_WORKER, SHIPPED_VALIDATOR, SHIPPED_WORKER,
            ShippedBinary,
        };
        use crate::runner_manager::{
            BUILD_CONTRACT, RUNNER_REGISTRY_SCHEMA_VERSION, RunnerEntitlements, RunnerRecord,
            RunnerRegistry, RunnerScope, RunnerSignature, RunnerState,
        };
        use std::cell::RefCell;
        use std::fs;

        const ROLES: [&ShippedBinary; 4] = [
            &SHIPPED_SERVICE,
            &SHIPPED_WORKER,
            &SHIPPED_VALIDATOR,
            &SHIPPED_UNENTITLED_WORKER,
        ];
        const ROLE_NAMES: [&str; 4] = ["service", "worker", "validator", "unentitled_worker"];
        const SERVICE_ID: &str = "com.controlled.pw.PWRunner";
        const EXTERNAL_SERVICE: &str = "com.controlled.runner";

        struct ClientCall {
            service_name: String,
            request: String,
            timeout_ms: u64,
            connection: RunnerConnectionKind,
        }

        struct Observed {
            loads: Vec<PathBuf>,
            calls: Vec<ClientCall>,
            output: RunOutput,
        }

        fn scratch(tag: &str) -> PathBuf {
            let stamp = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos();
            let root = std::env::temp_dir().join(format!(
                "pw-orchestration-{tag}-{}-{stamp}",
                std::process::id()
            ));
            fs::create_dir_all(&root).unwrap();
            root
        }

        fn write(path: &Path, bytes: &[u8]) {
            fs::create_dir_all(path.parent().unwrap()).unwrap();
            fs::write(path, bytes).unwrap();
        }

        /// A synthetic app root: the three shipped binaries as distinct small
        /// files at their fixed paths, and no Info.plist anywhere.
        fn synthetic_app(root: &Path) -> PathBuf {
            let app = root.join("PolicyWitness.app");
            for role in ROLES {
                write(
                    &app.join(role.rel_path),
                    format!("binary at {}", role.rel_path).as_bytes(),
                );
            }
            app
        }

        fn manifest_json(app: &Path) -> Value {
            let entry = |id: &str, bundle_id: Option<&str>, role: &ShippedBinary| {
                json!({
                    "id": id, "kind": role.kind, "bundle_id": bundle_id, "rel_path": role.rel_path,
                    "sha256": evidence::sha256_hex(&app.join(role.rel_path)).unwrap(),
                    "lc_uuid": null, "entitlements": {"com.apple.security.app-sandbox": true},
                    "entitlements_error": null,
                })
            };
            json!({
                "schema_version": evidence::EVIDENCE_SCHEMA_VERSION,
                "entries": [
                    entry(SERVICE_ID, Some(SERVICE_ID), &SHIPPED_SERVICE),
                    entry("pw-probe-runner", None, &SHIPPED_WORKER),
                    entry("sb_api_validator", None, &SHIPPED_VALIDATOR),
                    entry("pw-probe-runner-unentitled", None, &SHIPPED_UNENTITLED_WORKER),
                ],
                "notes": ["controlled"],
            })
        }

        #[derive(Clone, Copy)]
        enum ManifestState {
            Valid,
            Missing,
            Invalid,
        }

        fn install_manifest(app: &Path, state: ManifestState) -> PathBuf {
            let path = evidence::manifest_path_from_app_root(app);
            match state {
                ManifestState::Valid => write(&path, manifest_json(app).to_string().as_bytes()),
                ManifestState::Missing => {}
                ManifestState::Invalid => {
                    write(&path, br#"{"schema_version": 1, "entries": "not a list"}"#)
                }
            }
            path
        }

        fn manifest_hash(app: &Path, role: &ShippedBinary) -> String {
            evidence::sha256_hex(&app.join(role.rel_path)).unwrap()
        }

        /// An external bundle laid out like a BYOXPC copy of the shipped
        /// service: service and validator bytes equal the shipped ones, the
        /// worker differs.
        fn byoxpc_bundle(root: &Path, app: &Path) -> PathBuf {
            let bundle = root.join("Runner.xpc");
            let macos = bundle.join("Contents").join("MacOS");
            write(
                &macos.join("PWRunner"),
                &fs::read(app.join(SHIPPED_SERVICE.rel_path)).unwrap(),
            );
            write(&macos.join("pw-probe-runner"), b"a different worker");
            write(
                &macos.join("sb_api_validator"),
                &fs::read(app.join(SHIPPED_VALIDATOR.rel_path)).unwrap(),
            );
            write(
                &macos.join("pw-probe-runner-unentitled"),
                &fs::read(app.join(SHIPPED_UNENTITLED_WORKER.rel_path)).unwrap(),
            );
            bundle
        }

        fn signature() -> RunnerSignature {
            RunnerSignature {
                extra: Default::default(),
                team_id: Some("TEAM123456".into()),
                identity: Some("Developer ID Application: Controlled (TEAM123456)".into()),
                cdhash: Some("ab".repeat(20)),
                valid: true,
                adhoc: false,
            }
        }

        fn entitlements(keys: &[&str]) -> RunnerEntitlements {
            RunnerEntitlements {
                extra: Default::default(),
                raw_plist: Some("<plist version=\"1.0\"><dict/></plist>".into()),
                keys: keys.iter().map(|k| k.to_string()).collect(),
                granted: keys.iter().map(|k| k.to_string()).collect(),
                error: None,
            }
        }

        fn record(bundle: &Path, keys: &[&str]) -> RunnerRecord {
            RunnerRecord {
                extra: Default::default(),
                state: RunnerState::Installed,
                ownership: None,
                id: "runner-ext".into(),
                service_name: EXTERNAL_SERVICE.into(),
                bundle_path: bundle.display().to_string(),
                executable_path: bundle.join("Contents/MacOS/PWRunner").display().to_string(),
                bundle_id: Some(EXTERNAL_SERVICE.into()),
                scope: RunnerScope::User,
                contract: BUILD_CONTRACT.into(),
                signature: signature(),
                entitlements: entitlements(keys),
                installed_at_unix_ms: 1,
                kind: Some(RunnerKind::Byoxpc),
                worker_signature: Some(signature()),
                worker_entitlements: Some(entitlements(keys)),
                validator_signature: Some(signature()),
                validator_entitlements: Some(entitlements(&[])),
                unentitled_worker_sha256: None,
                worker_equipment_inventory: None,
                source_worker_equipment_inventory: None,
                issuer_signature: None,
                issuer_entitlements: None,
                unentitled_worker_signature: Some(signature()),
                unentitled_worker_entitlements: Some(entitlements(&[])),
            }
        }

        fn registry_fixture(root: &Path, runners: Vec<RunnerRecord>) -> PathBuf {
            let registry = RunnerRegistry {
                extra: Default::default(),
                schema_version: RUNNER_REGISTRY_SCHEMA_VERSION,
                runners,
                pending_cleanup: Vec::new(),
            };
            let path = root.join("runners.json");
            write(&path, serde_json::to_string(&registry).unwrap().as_bytes());
            path
        }

        fn request_file(root: &Path, runner: Option<Value>) -> PathBuf {
            let mut request = json!({
                "contract": crate::json_contract::BUILD_CONTRACT, "specimen_id": "controlled",
                "policy": {"format": "sbpl", "sbpl_source": "(version 1)\n(allow default)\n"},
                "probe_plan": [],
            });
            if let Some(runner) = runner {
                request["runner"] = runner;
            }
            let path = root.join("request.json");
            write(
                &path,
                serde_json::to_string_pretty(&request).unwrap().as_bytes(),
            );
            path
        }

        fn byoxpc_request(root: &Path, required: &[&str]) -> PathBuf {
            request_file(
                root,
                Some(
                    json!({"id": "runner-ext", "mode": "byoxpc", "required_entitlements": required}),
                ),
            )
        }

        fn controlled_reply() -> Value {
            json!({
                "producer": crate::reply_fixtures::producer(),
                "normalized_outcome": "finished", "rc": 0, "pid": 77,
                "specimen_id": "controlled", "steps": [], "phases": [],
            })
        }

        /// Production orchestration with app, manifest, registry and client controlled.
        fn observe(app: &Path, registry: Option<&Path>, args: &[&str]) -> Observed {
            observe_reply(app, registry, args, controlled_reply())
        }

        /// The same orchestration with the controlled client returning `reply`.
        fn observe_reply(
            app: &Path,
            registry: Option<&Path>,
            args: &[&str],
            reply: Value,
        ) -> Observed {
            observe_client(app, registry, args, Some(reply))
        }

        /// `None` is an admitted client XPC failure, with no host result.
        fn observe_client(
            app: &Path,
            registry: Option<&Path>,
            args: &[&str],
            reply: Option<Value>,
        ) -> Observed {
            let loads = RefCell::new(Vec::new());
            let calls = RefCell::new(Vec::new());
            let load_manifest = |path: &Path| {
                loads.borrow_mut().push(path.to_path_buf());
                evidence::load_manifest(path)
            };
            let client = |service_name: &str,
                          request: &str,
                          timeout_ms: u64,
                          connection: &RunnerConnectionKind| {
                calls.borrow_mut().push(ClientCall {
                    service_name: service_name.to_string(),
                    request: request.to_string(),
                    timeout_ms,
                    connection: *connection,
                });
                let reply = reply.clone();
                let mut run = client_run(reply.as_ref());
                let typed = reply.and_then(|value| match serde_json::from_value(value) {
                    Ok(record) => Some(record),
                    Err(error) => {
                        run.runner_reply_error = Some(crate::runner_client::ReplyError {
                            refusal: crate::runner_client::ReplyRefusal::Malformed,
                            message: error.to_string(),
                        });
                        None
                    }
                });
                Ok((run, typed))
            };
            let app_root = app.to_path_buf();
            let deps = RunDependencies {
                app_root: &|| Ok(app_root.clone()),
                load_manifest: &load_manifest,
                registry_path: registry,
                client: &client,
                policy_check: &run_policy_check,
            };
            let args: Vec<OsString> = args.iter().map(OsString::from).collect();
            let output = run(&args, &deps).expect("run completes");
            Observed {
                loads: loads.into_inner(),
                calls: calls.into_inner(),
                output,
            }
        }

        fn envelope_of(output: &RunOutput) -> (Value, i32) {
            match output {
                RunOutput::Envelope { text, exit_code } => {
                    (serde_json::from_str(text).unwrap(), *exit_code)
                }
                RunOutput::Help => panic!("usage requested"),
            }
        }

        fn forwarded_request_value(path: &Path) -> Value {
            let mut value: Value = serde_json::from_slice(&fs::read(path).unwrap()).unwrap();
            // Expect only worker-owned fields after controller selection.
            for key in [
                "runner",
                "runner_id",
                "runner_service",
                "required_entitlements",
                "runner_mode",
            ] {
                value.as_object_mut().unwrap().remove(key);
            }
            value
        }

        #[test]
        fn invalid_request_version_stops_before_selection_augments_or_client_invocation() {
            let root = scratch("input-version");
            let app = synthetic_app(&root);
            install_manifest(&app, ManifestState::Valid);
            let request = request_file(&root, None);
            let original: Value = serde_json::from_slice(&fs::read(&request).unwrap()).unwrap();
            for version in [json!(1), json!("test:foreign"), json!(null), json!(true)] {
                let mut value = original.clone();
                value["contract"] = version;
                // These would fail if interpreted before the version gate.
                value["runner"] = json!({"mode": "unknown-mode"});
                value["policy"]["augments"] = json!(["unknown_augment"]);
                let bytes = serde_json::to_vec(&value).unwrap();
                fs::write(&request, &bytes).unwrap();
                let observed = observe(&app, None, &[request.to_str().unwrap()]);
                assert!(observed.calls.is_empty());
                let (wire, code) = envelope_of(&observed.output);
                assert_eq!(code, 1);
                assert_eq!(wire["result"]["normalized_outcome"], "bad_request");
                assert!(
                    wire["result"]["error"]
                        .as_str()
                        .unwrap()
                        .contains("expected")
                );
                assert!(wire["data"]["runner_result"].is_null());
                assert_eq!(fs::read(&request).unwrap(), bytes);
            }
            fs::remove_dir_all(root).unwrap();
        }

        #[test]
        fn runner_mode_option_cannot_overwrite_a_malformed_selector() {
            let mut value = json!({"runner": {"mode": 42}});
            assert!(
                inject_runner_mode(&mut value, "standard")
                    .unwrap_err()
                    .message
                    .contains("runner.mode")
            );
            assert_eq!(value["runner"]["mode"], 42);
        }

        #[test]
        fn builtin_run_loads_the_manifest_once_and_every_reader_consumes_it() {
            let root = scratch("builtin");
            let app = synthetic_app(&root);
            let manifest_path = install_manifest(&app, ManifestState::Valid);
            let request = request_file(&root, None);
            let observed = observe(&app, None, &[request.to_str().unwrap()]);
            assert_eq!(observed.loads, vec![manifest_path.clone()]);
            assert_eq!(observed.calls.len(), 1);
            let call = &observed.calls[0];
            // Selection consumed the loaded manifest: the service name is its
            // entry's bundle_id, which no file under the app root carries.
            assert_eq!(call.service_name, SERVICE_ID);
            assert!(matches!(call.connection, RunnerConnectionKind::XpcService));
            assert_eq!(call.timeout_ms, DEFAULT_TIMEOUT_MS);
            let delivered: Value = serde_json::from_str(&call.request).unwrap();
            assert_eq!(delivered, forwarded_request_value(&request));
            let (wire, exit_code) = envelope_of(&observed.output);
            assert_eq!(exit_code, 0);
            assert_eq!(wire["result"]["ok"], true);
            assert_eq!(wire["result"]["normalized_outcome"], "finished");
            let specimen = &wire["data"]["specimen"];
            // App provenance consumed the same load: it names the loaded path.
            assert_eq!(
                specimen["app_provenance"]["evidence_manifest_path"],
                manifest_path.display().to_string()
            );
            assert_eq!(specimen["runner_provenance"]["runner_kind"], "standard");
            assert_eq!(
                specimen["runner_provenance"]["runner_service_name"],
                SERVICE_ID
            );
            assert_eq!(
                specimen["runner_provenance"]["runner_executable_path"],
                app.join(SHIPPED_SERVICE.rel_path).display().to_string()
            );
            assert_eq!(
                specimen["runner_provenance"]["runner_entitlements"]["keys"],
                json!(["com.apple.security.app-sandbox"])
            );
            // The binary dossier consumed it too: every role sits at the
            // manifest's uniquely typed path, so no comparison record is needed.
            for role in ROLE_NAMES {
                assert!(specimen["binaries"][role].is_null(), "{role}");
            }
            assert_eq!(wire["data"]["runner_result"], controlled_reply());
            assert_eq!(
                wire["data"]["runner_client"]["request_delivery"]["bytes_written"],
                2
            );
            assert_eq!(
                keys(&wire["data"]["runner_sandbox_diagnostics"]),
                DIAGNOSTIC_KEYS
            );
            fs::remove_dir_all(&root).unwrap();
        }

        #[test]
        fn builtin_manifest_failures_refuse_before_the_client_with_one_load() {
            for (label, state, detail) in [
                ("missing", ManifestState::Missing, "failed to read manifest"),
                (
                    "invalid",
                    ManifestState::Invalid,
                    "failed to parse manifest",
                ),
            ] {
                let root = scratch(label);
                let app = synthetic_app(&root);
                let manifest_path = install_manifest(&app, state);
                let request = request_file(&root, None);
                let observed = observe(&app, None, &[request.to_str().unwrap()]);
                assert_eq!(observed.loads, vec![manifest_path.clone()], "{label}");
                assert!(observed.calls.is_empty(), "{label}: zero client calls");
                let (wire, exit_code) = envelope_of(&observed.output);
                assert_eq!(exit_code, 2, "{label}");
                assert_eq!(wire["result"]["ok"], false);
                assert_eq!(wire["result"]["normalized_outcome"], "tool_error");
                let error = wire["result"]["error"].as_str().unwrap().to_string();
                assert!(
                    error.contains("built-in runner unavailable")
                        && error.contains(manifest_path.to_str().unwrap())
                        && error.contains(detail),
                    "{label}: {error}"
                );
                let specimen = &wire["data"]["specimen"];
                assert!(specimen["app_provenance"].is_null(), "{label}");
                assert!(specimen["runner_provenance"].is_null(), "{label}");
                for role in ROLE_NAMES {
                    assert_eq!(specimen["binaries"][role]["verification"], "unavailable");
                    assert_eq!(
                        specimen["binaries"][role]["reason"], error,
                        "{label}: {role}"
                    );
                    assert!(specimen["binaries"][role]["path"].is_null());
                }
                assert!(wire["data"]["runner_client"].is_null());
                assert!(wire["data"]["runner_result"].is_null());
                fs::remove_dir_all(&root).unwrap();
            }
        }

        #[test]
        fn compiled_profile_labels_determine_the_public_admission_outcome() {
            let root = scratch("profile-label-outcomes");
            let app = synthetic_app(&root);
            install_manifest(&app, ManifestState::Valid);
            let request = request_file(&root, None);
            let args = [request.to_str().unwrap()];
            let cases: Value = serde_json::from_str(include_str!(
                "../../tests/fixtures/contract/compiled_profile.json"
            ))
            .unwrap();
            for case in cases.as_array().unwrap() {
                let mut reply = worker("finished", None);
                reply["compiled_profile"] = case["receipt"].clone();
                let retained = serde_json::from_value::<PWRunnerRunResult>(reply.clone()).ok();
                let observed = observe_reply(&app, None, &args, reply);
                let (wire, exit_code) = envelope_of(&observed.output);
                let valid = case["valid"].as_bool().unwrap();
                let label = &case["name"];
                assert_eq!(observed.calls.len(), 1, "{label}");
                assert_eq!(exit_code, if valid { 0 } else { 1 }, "{label}");
                assert_eq!(wire["result"]["ok"], valid, "{label}");
                assert_eq!(
                    wire["result"]["normalized_outcome"],
                    if valid {
                        "finished"
                    } else {
                        "malformed_runner_response"
                    },
                    "{label}"
                );
                assert_eq!(
                    serde_json::from_value::<Option<PWRunnerRunResult>>(
                        wire["data"]["runner_result"].clone()
                    )
                    .unwrap(),
                    retained,
                    "{label}: structurally decoded reports remain available"
                );
                assert!(wire["data"]["policy_check"].is_null(), "{label}");
                assert_eq!(
                    wire["data"]["runner_sandbox_diagnostics"].is_null(),
                    !valid,
                    "{label}"
                );
            }
            fs::remove_dir_all(&root).unwrap();
        }

        #[test]
        fn refused_reply_versions_request_no_fallback_compilation() {
            // Through production admission: a reply under another response
            // version is refused before anything reads it, so no helper is
            // requested and `policy_check` is null. The "string" and "missing"
            // rows stand for host bytes that supply no typed record: the
            // authored JSON fails this test's fixture reader, as a wrong-kind or
            // absent field fails the binary reader (porcelain controls). The same holds for a host
            // body naming xpc_error: only a client transport observation can
            // authorize the separate fallback compiler.
            let root = scratch("refused-reply-versions");
            let app = synthetic_app(&root);
            install_manifest(&app, ManifestState::Valid);
            let request = request_file(&root, None);
            let args = [request.to_str().unwrap()];
            let current = json_contract::BUILD_CONTRACT;
            for (label, reply, outcome) in [
                (
                    "previous",
                    json!({"producer": {"contract":"test:previous", "describe":"test", "commit":"test"}, "normalized_outcome": "xpc_error",
                        "error": "refused", "steps": [], "phases":[], "specimen_id":"controlled", "rc":1, "pid":42}),
                    "unsupported_runner_response",
                ),
                (
                    "next",
                    json!({"producer": {"contract":"test:next", "describe":"test", "commit":"test"}, "normalized_outcome": "xpc_error",
                        "error": "refused", "steps": [], "phases":[], "specimen_id":"controlled", "rc":1, "pid":42}),
                    "unsupported_runner_response",
                ),
                (
                    "string",
                    json!({"producer": {"contract":6}, "normalized_outcome": "xpc_error",
                        "error": "refused", "steps": [], "phases":[], "specimen_id":"controlled", "rc":1, "pid":42}),
                    "malformed_runner_response",
                ),
                (
                    "missing",
                    json!({"normalized_outcome": "xpc_error", "error": "refused", "steps": [], "phases":[], "specimen_id":"controlled", "rc":1, "pid":42}),
                    "malformed_runner_response",
                ),
            ] {
                let observed = observe_reply(&app, None, &args, reply.clone());
                assert_eq!(observed.calls.len(), 1, "{label}");
                let (wire, exit_code) = envelope_of(&observed.output);
                assert_eq!(exit_code, 1, "{label}");
                assert_eq!(wire["result"]["normalized_outcome"], outcome, "{label}");
                assert!(wire["data"]["policy_check"].is_null(), "{label}");
                if outcome == "malformed_runner_response" {
                    assert!(wire["data"]["runner_result"].is_null(), "{label}");
                } else {
                    assert_eq!(wire["data"]["runner_result"], reply, "{label}");
                }
            }
            let xpc_error = json!({"producer": crate::reply_fixtures::producer(), "normalized_outcome": "xpc_error",
                "error": "NSCocoaErrorDomain:4099 refused", "steps": [], "phases":[], "specimen_id":"controlled", "rc":1, "pid":42});
            let observed = observe_reply(&app, None, &args, xpc_error.clone());
            let (wire, exit_code) = envelope_of(&observed.output);
            assert_eq!(exit_code, 1);
            assert_eq!(wire["result"]["normalized_outcome"], "xpc_error");
            assert_eq!(wire["result"]["error"], "NSCocoaErrorDomain:4099 refused");
            assert_eq!(wire["data"]["runner_result"], xpc_error);
            assert!(wire["data"]["policy_check"].is_null());

            // A client-side failure after submission requests the fallback
            // compiler once, without resubmitting or creating a host result.
            let observed = observe_client(&app, None, &args, None);
            assert_eq!(observed.calls.len(), 1);
            let (wire, exit_code) = envelope_of(&observed.output);
            assert_eq!(exit_code, 1);
            assert_eq!(wire["result"]["normalized_outcome"], "xpc_error");
            assert_eq!(wire["result"]["error"], "controlled XPC error");
            assert!(wire["data"]["runner_result"].is_null());
            assert!(wire["data"]["runner_sandbox_diagnostics"].is_null());
            assert_eq!(wire["data"]["runner_client"]["submission"], "invoked");
            assert_eq!(
                wire["data"]["runner_client"]["transport"]["terminal"],
                "xpc_error"
            );
            let check = &wire["data"]["policy_check"];
            assert_eq!(check["status"], "unavailable");
            assert!(check["envelope"].is_null());
            assert!(
                check["stderr"].as_str().unwrap().contains("sbpl-check"),
                "{check}"
            );
            for key in [
                "compiled",
                "compile_error",
                "normalized_outcome",
                "policy_format",
                "policy_sha256",
            ] {
                assert!(check.get(key).is_none(), "{key} projection retired");
            }
            fs::remove_dir_all(&root).unwrap();
        }

        #[test]
        fn actor_fallback_uses_held_policy_objects_before_host_mode_admission() {
            // Exercise controller orchestration with controlled transport and
            // compilation. These invalid actor forms never reach a real host.
            let root = scratch("actor-fallback-raw");
            let app = synthetic_app(&root);
            install_manifest(&app, ManifestState::Valid);
            let allow = json!({"format":"sbpl", "sbpl_source":"(version 1) (allow default)"});
            let deny = json!({"format":"sbpl", "sbpl_source":"(version 1) (deny default)"});
            let path = root.join("request.json");
            for (first, last) in [(&allow, &deny), (&deny, &allow)] {
                let raw = r#"{
                    "contract":"BUILD_CONTRACT", "specimen_id":"raw-actor-fallback",
                    "runner":{"mode":"standard"}, "actors":[
                        {"actor_id":"future", "sandbox":{"mode":"future", "policy":FIRST_POLICY, "policy":LAST_POLICY}},
                        {"actor_id":"unapplied", "sandbox":{"mode":"unapplied", "policy":ALLOW_POLICY}},
                        {"sandbox":{"policy":DENY_POLICY}},
                        {"actor_id":17, "sandbox":{"mode":9, "policy":ALLOW_POLICY}},
                        {"actor_id":"absent", "sandbox":{"mode":"apply"}},
                        {"actor_id":"scalar", "sandbox":{"mode":"apply", "policy":"ignored"}}
                    ], "phases":[]
                }"#
                    .replace("BUILD_CONTRACT", json_contract::BUILD_CONTRACT)
                    .replace("FIRST_POLICY", &first.to_string())
                    .replace("LAST_POLICY", &last.to_string())
                    .replace("ALLOW_POLICY", &allow.to_string())
                    .replace("DENY_POLICY", &deny.to_string());
                // Independent expected held object: the duplicate's last value,
                // the original actor order and removal of controller options.
                let expected = json!({
                    "contract":json_contract::BUILD_CONTRACT, "specimen_id":"raw-actor-fallback",
                    "actors":[
                        {"actor_id":"future", "sandbox":{"mode":"future", "policy":last}},
                        {"actor_id":"unapplied", "sandbox":{"mode":"unapplied", "policy":allow}},
                        {"sandbox":{"policy":deny}},
                        {"actor_id":17, "sandbox":{"mode":9, "policy":allow}},
                        {"actor_id":"absent", "sandbox":{"mode":"apply"}},
                        {"actor_id":"scalar", "sandbox":{"mode":"apply", "policy":"ignored"}}
                    ], "phases":[]
                });
                for delivered_refusal in [false, true] {
                    write(&path, raw.as_bytes());
                    let reply = delivered_refusal.then(|| {
                        json!({
                            "producer": crate::reply_fixtures::producer(),
                            "normalized_outcome":"bad_request", "rc":1, "pid":77,
                            "specimen_id":"raw-actor-fallback", "steps":[], "phases":[],
                            "error":"controlled host refusal"
                        })
                    });
                    let capture = client_run(reply.as_ref());
                    let captured = serde_json::to_value(&capture).unwrap();
                    let pending = RefCell::new(Some((capture, reply.clone().map(fixture_reply))));
                    let client_inputs = RefCell::new(Vec::new());
                    let helper_inputs = RefCell::new(Vec::new());
                    let client = |_: &str, held: &str, _: u64, _: &RunnerConnectionKind| {
                        client_inputs.borrow_mut().push(held.to_owned());
                        write(&path, b"changed after the request was held");
                        Ok(pending.borrow_mut().take().unwrap())
                    };
                    let helper = |held: &str| {
                        helper_inputs.borrow_mut().push(held.to_owned());
                        Err("controlled compiler unavailable".to_owned())
                    };
                    let deps = RunDependencies {
                        app_root: &|| Ok(app.clone()),
                        load_manifest: &evidence::load_manifest,
                        registry_path: None,
                        client: &client,
                        policy_check: &helper,
                    };
                    let output = run(&[path.as_os_str().to_owned()], &deps).unwrap();
                    let (wire, exit_code) = envelope_of(&output);
                    let inputs = client_inputs.borrow();
                    assert_eq!(inputs.len(), 1, "one client invocation");
                    assert_eq!(serde_json::from_str::<Value>(&inputs[0]).unwrap(), expected);
                    assert_eq!(wire["data"]["runner_client"], captured);
                    assert_eq!(wire["data"]["runner_result"], json!(reply));
                    assert_eq!(exit_code, 1);
                    assert!(!wire["result"]["ok"].as_bool().unwrap());
                    if delivered_refusal {
                        assert_eq!(wire["result"]["normalized_outcome"], "bad_request");
                        assert!(helper_inputs.borrow().is_empty());
                        assert!(wire["data"]["policy_check"].is_null());
                        assert!(wire["data"].get("actor_policy_checks").is_none());
                    } else {
                        assert_eq!(wire["result"]["normalized_outcome"], "xpc_error");
                        assert_eq!(
                            *helper_inputs.borrow(),
                            vec![
                                inputs[0].clone(),
                                json!({"policy":last}).to_string(),
                                json!({"policy":allow}).to_string(),
                                json!({"policy":deny}).to_string(),
                                json!({"policy":allow}).to_string(),
                            ]
                        );
                        let checks = wire["data"]["actor_policy_checks"].as_array().unwrap();
                        assert_eq!(checks.len(), 4);
                        assert_eq!(
                            checks
                                .iter()
                                .map(|row| row["actor_id"].clone())
                                .collect::<Vec<_>>(),
                            vec![
                                json!("future"),
                                json!("unapplied"),
                                Value::Null,
                                Value::Null
                            ]
                        );
                        assert!(
                            checks
                                .iter()
                                .all(|row| row["policy_check"]["status"] == "unavailable")
                        );
                        assert_eq!(wire["data"]["policy_check"]["status"], "unavailable");
                        assert!(wire["data"]["runner_sandbox_diagnostics"].is_null());
                    }
                }
            }
            fs::remove_dir_all(&root).unwrap();
        }

        #[test]
        fn actor_fallback_preserves_resolved_inputs_order_and_transport_evidence() {
            // These are valid actor-form inputs, but the controlled client does
            // not contact a host. Admitted terminal xpc_error authorizes only
            // diagnostic compilation, not a claim of host request admission.
            let root = scratch("actor-fallback");
            let app = synthetic_app(&root);
            install_manifest(&app, ManifestState::Valid);
            write(
                &app.join("Contents/Resources/Augments/read_control.sb"),
                b"(deny file-read-data)",
            );
            let request = json!({
                "contract": json_contract::BUILD_CONTRACT,
                "specimen_id": "actor-fallback", "runner": {"mode": "standard"},
                "actors": [
                    {"actor_id": "zeta", "sandbox": {"mode": "apply", "policy": {
                        "format": "sbpl", "sbpl_source": "(version 1) (allow default)",
                        "augments": ["read_control"]}}},
                    {"actor_id": "middle", "sandbox": {"mode": "unapplied"}},
                    {"actor_id": "alpha", "sandbox": {"mode": "apply", "policy": {
                        "format": "sbpl", "sbpl_source": "(version 1) (deny default)",
                        "params": {"TAG": "alpha"}}}}
                ],
                "phases": [
                    {"phase_id": "first", "actor_id": "zeta", "actions": []},
                    {"phase_id": "second", "actor_id": "middle", "actions": []},
                    {"phase_id": "third", "actor_id": "alpha", "actions": []}
                ]
            });
            // Independent expected policy objects: do not use the resolver or
            // collect expectations from the delivered request.
            let zeta = json!({"format": "sbpl",
                "sbpl_source": "(version 1) (allow default)\n(deny file-read-data)"});
            let alpha = json!({"format": "sbpl",
                "sbpl_source": "(version 1) (deny default)", "params": {"TAG": "alpha"}});
            let mut expected = request.clone();
            expected.as_object_mut().unwrap().remove("runner");
            expected["actors"][0]["sandbox"]["policy"] = zeta.clone();
            let path = root.join("request.json");
            for label in [
                "eligible",
                "helper-unavailable",
                "host-ok",
                "host-xpc-error",
                "missing-capture",
                "delivery-failed",
            ] {
                write(&path, request.to_string().as_bytes());
                let reply = match label {
                    "host-ok" => Some(controlled_reply()),
                    "host-xpc-error" => Some(json!({
                        "producer": crate::reply_fixtures::producer(),
                        "normalized_outcome": "xpc_error", "error": "host body", "steps": [], "phases":[], "pid":42,"rc":1,"specimen_id":"controlled"
                    })),
                    _ => None,
                };
                let mut capture = client_run(reply.as_ref());
                if label == "missing-capture" {
                    capture.transport = None;
                    capture.transport_admission = "missing".into();
                    capture.transport_error = Some("no complete client capture".into());
                    capture.submission = "unknown".into();
                } else if label == "delivery-failed" {
                    capture.request_delivery.as_mut().unwrap().error = Some("Broken pipe".into());
                }
                let captured = serde_json::to_value(&capture).unwrap();
                let pending = RefCell::new(Some((capture, reply.clone().map(fixture_reply))));
                let client_inputs = RefCell::new(Vec::new());
                let helper_inputs = RefCell::new(Vec::new());
                let helper_outputs = RefCell::new(Vec::new());
                let client = |_: &str, held: &str, _: u64, _: &RunnerConnectionKind| {
                    client_inputs.borrow_mut().push(held.to_owned());
                    // A changed on-disk request must not replace either the
                    // held whole request or the resolved actor policies.
                    write(&path, b"request replaced after client invocation");
                    Ok(pending.borrow_mut().take().unwrap())
                };
                let helper = |held: &str| {
                    let index = helper_inputs.borrow().len();
                    helper_inputs.borrow_mut().push(held.to_owned());
                    let result = if index == 0 || (index == 2 && label == "helper-unavailable") {
                        Err(format!("controlled helper failure {index}"))
                    } else {
                        let status = if index == 1 { "ok" } else { "compile_error" };
                        Ok(PolicyCheckCapture {
                            status: status.into(),
                            tool_exit_code: if index == 1 { 0 } else { 1 },
                            output: crate::utils::TextOutputCapture::unavailable(
                                format!("helper {index}"),
                                crate::utils::HELPER_CAPTURE_BYTES,
                            ),
                            envelope: Some(json!({
                                "build": {"contract": json_contract::BUILD_CONTRACT},
                                "kind": "sbpl_check",
                                "result": {"normalized_outcome": status},
                                "data": {"controlled_call": index}
                            })),
                        })
                    };
                    let expected_capture = match &result {
                        Ok(value) => serde_json::to_value(value).unwrap(),
                        Err(error) => {
                            serde_json::to_value(PolicyCheckCapture::unavailable(error.clone()))
                                .unwrap()
                        }
                    };
                    helper_outputs.borrow_mut().push(expected_capture);
                    result
                };
                let deps = RunDependencies {
                    app_root: &|| Ok(app.clone()),
                    load_manifest: &evidence::load_manifest,
                    registry_path: None,
                    client: &client,
                    policy_check: &helper,
                };
                let output = run(&[path.as_os_str().to_owned()], &deps).unwrap();
                let (wire, exit_code) = envelope_of(&output);
                let inputs = client_inputs.borrow();
                assert_eq!(inputs.len(), 1, "{label}: no resubmission");
                assert_eq!(serde_json::from_str::<Value>(&inputs[0]).unwrap(), expected);
                assert_eq!(wire["data"]["runner_client"], captured, "{label}");
                assert_eq!(wire["data"]["runner_result"], json!(reply), "{label}");
                let eligible = matches!(label, "eligible" | "helper-unavailable");
                let checks = helper_inputs.borrow();
                if eligible {
                    assert_eq!(exit_code, 1);
                    assert_eq!(wire["result"]["normalized_outcome"], "xpc_error");
                    assert_eq!(wire["result"]["error"], "controlled XPC error");
                    assert!(wire["data"]["runner_result"].is_null());
                    assert!(wire["data"]["runner_sandbox_diagnostics"].is_null());
                    assert_eq!(
                        *checks,
                        vec![
                            inputs[0].clone(),
                            json!({"policy": zeta}).to_string(),
                            json!({"policy": alpha}).to_string(),
                        ],
                        "{label}: whole held request, then policies in request order"
                    );
                    let outputs = helper_outputs.borrow();
                    assert_eq!(wire["data"]["policy_check"], outputs[0]);
                    assert_eq!(wire["data"]["policy_check"]["status"], "unavailable");
                    assert_eq!(
                        wire["data"]["actor_policy_checks"][0]["policy_check"]["status"],
                        "ok"
                    );
                    assert_eq!(
                        wire["data"]["actor_policy_checks"][1]["policy_check"]["status"],
                        if label == "helper-unavailable" {
                            "unavailable"
                        } else {
                            "compile_error"
                        }
                    );
                    assert_eq!(
                        wire["data"]["actor_policy_checks"],
                        json!([
                            {"actor_id": "zeta", "policy_check": outputs[1]},
                            {"actor_id": "alpha", "policy_check": outputs[2]},
                        ])
                    );
                } else {
                    assert!(checks.is_empty(), "{label}: no helper invocation");
                    assert!(wire["data"]["policy_check"].is_null());
                    assert!(wire["data"].get("actor_policy_checks").is_none());
                }
            }
            fs::remove_dir_all(&root).unwrap();
        }

        #[test]
        fn byoxpc_run_with_a_manifest_compares_the_bundle_copies_with_its_baselines() {
            let root = scratch("byoxpc");
            let app = synthetic_app(&root);
            let manifest_path = install_manifest(&app, ManifestState::Valid);
            let bundle = byoxpc_bundle(&root, &app);
            let record = record(&bundle, &["com.apple.security.cs.allow-jit"]);
            let registry = registry_fixture(&root, vec![record.clone()]);
            let request = byoxpc_request(&root, &["com.apple.security.cs.allow-jit"]);
            let observed = observe(
                &app,
                Some(&registry),
                &[request.to_str().unwrap(), "--timeout-ms", "7000"],
            );
            assert_eq!(observed.loads, vec![manifest_path.clone()]);
            assert_eq!(observed.calls.len(), 1);
            let call = &observed.calls[0];
            assert_eq!(call.service_name, EXTERNAL_SERVICE);
            assert!(matches!(
                call.connection,
                RunnerConnectionKind::MachService { privileged: false }
            ));
            assert_eq!(call.timeout_ms, 7000);
            let (wire, exit_code) = envelope_of(&observed.output);
            assert_eq!(exit_code, 0);
            let specimen = &wire["data"]["specimen"];
            assert_eq!(
                specimen["app_provenance"]["evidence_manifest_path"],
                manifest_path.display().to_string()
            );
            let provenance = &specimen["runner_provenance"];
            assert_eq!(provenance["runner_kind"], "byoxpc");
            assert_eq!(provenance["runner_registry_id"], "runner-ext");
            assert_eq!(
                provenance["runner_bundle_path"],
                bundle.display().to_string()
            );
            assert_eq!(
                provenance["runner_signature"],
                serde_json::to_value(&record.signature).unwrap()
            );
            assert_eq!(
                provenance["runner_entitlements"],
                serde_json::to_value(&record.entitlements).unwrap()
            );
            // The helpers' read-backs travel from the registry record as recorded.
            assert_eq!(
                provenance["runner_worker_entitlements"],
                serde_json::to_value(&record.worker_entitlements).unwrap()
            );
            assert_eq!(
                provenance["runner_worker_signature"],
                serde_json::to_value(&record.worker_signature).unwrap()
            );
            assert_eq!(
                provenance["runner_validator_entitlements"],
                serde_json::to_value(&record.validator_entitlements).unwrap()
            );
            assert_eq!(
                provenance["runner_validator_signature"],
                serde_json::to_value(&record.validator_signature).unwrap()
            );
            // The binary records compare the bundle copies with the baselines
            // the one loaded manifest carries.
            let binaries = &specimen["binaries"];
            assert_eq!(binaries["service"]["verification"], "match");
            assert_eq!(
                binaries["service"]["baseline_sha256"],
                manifest_hash(&app, &SHIPPED_SERVICE)
            );
            assert_eq!(binaries["worker"]["verification"], "mismatch");
            assert_eq!(
                binaries["worker"]["baseline_sha256"],
                manifest_hash(&app, &SHIPPED_WORKER)
            );
            assert_ne!(
                binaries["worker"]["actual_sha256"],
                binaries["worker"]["baseline_sha256"]
            );
            assert_eq!(binaries["validator"]["verification"], "match");
            assert_eq!(
                binaries["validator"]["baseline_sha256"],
                manifest_hash(&app, &SHIPPED_VALIDATOR)
            );
            fs::remove_dir_all(&root).unwrap();
        }

        #[test]
        fn byoxpc_run_without_a_manifest_still_receives_the_held_request() {
            for (label, state, detail) in [
                ("missing", ManifestState::Missing, "failed to read manifest"),
                (
                    "invalid",
                    ManifestState::Invalid,
                    "failed to parse manifest",
                ),
            ] {
                let root = scratch(label);
                let app = synthetic_app(&root);
                let manifest_path = install_manifest(&app, state);
                let bundle = byoxpc_bundle(&root, &app);
                let record = record(&bundle, &["com.apple.security.cs.allow-jit"]);
                let registry = registry_fixture(&root, vec![record.clone()]);
                let request = byoxpc_request(&root, &["com.apple.security.cs.allow-jit"]);
                let observed = observe(&app, Some(&registry), &[request.to_str().unwrap()]);
                assert_eq!(observed.loads, vec![manifest_path.clone()], "{label}");
                // The valid external runner receives the held request despite
                // the manifest failure.
                assert_eq!(observed.calls.len(), 1, "{label}");
                let call = &observed.calls[0];
                assert_eq!(call.service_name, EXTERNAL_SERVICE);
                assert!(matches!(
                    call.connection,
                    RunnerConnectionKind::MachService { privileged: false }
                ));
                let delivered: Value = serde_json::from_str(&call.request).unwrap();
                assert_eq!(delivered, forwarded_request_value(&request), "{label}");
                let (wire, exit_code) = envelope_of(&observed.output);
                assert_eq!(exit_code, 0, "{label}");
                assert_eq!(wire["result"]["ok"], true);
                let specimen = &wire["data"]["specimen"];
                assert!(specimen["app_provenance"].is_null(), "{label}");
                // Registry-sourced provenance does not depend on the manifest.
                assert_eq!(
                    specimen["runner_provenance"]["runner_registry_id"],
                    "runner-ext"
                );
                assert_eq!(
                    specimen["runner_provenance"]["runner_signature"],
                    serde_json::to_value(&record.signature).unwrap()
                );
                for role in ROLE_NAMES {
                    let binary = &specimen["binaries"][role];
                    assert_eq!(binary["verification"], "unavailable", "{label}: {role}");
                    assert!(binary["baseline_sha256"].is_null(), "{label}: {role}");
                    let reason = binary["reason"].as_str().unwrap();
                    assert!(
                        reason.contains("app evidence manifest unavailable")
                            && reason.contains(detail)
                            && reason.contains(manifest_path.to_str().unwrap()),
                        "{label}: {role}: {reason}"
                    );
                    let path = PathBuf::from(binary["path"].as_str().unwrap());
                    assert!(
                        path.starts_with(&bundle),
                        "{label}: {role}: {}",
                        path.display()
                    );
                    assert_eq!(
                        binary["actual_sha256"],
                        evidence::sha256_hex(&path).unwrap(),
                        "{label}: {role}"
                    );
                }
                assert_eq!(wire["data"]["runner_result"], controlled_reply());
                assert!(wire["data"]["runner_client"]["request_delivery"].is_object());
                fs::remove_dir_all(&root).unwrap();
            }
        }

        #[test]
        fn byoxpc_selection_failures_make_one_load_and_no_client_call() {
            let root = scratch("refusals");
            let app = synthetic_app(&root);
            let manifest_path = install_manifest(&app, ManifestState::Valid);
            let bundle = byoxpc_bundle(&root, &app);
            let mut pending = record(&bundle, &["A"]);
            pending.id = "pending-ext".into();
            pending.service_name = "com.controlled.pending".into();
            pending.state = RunnerState::Pending;
            let registry = registry_fixture(&root, vec![record(&bundle, &["A"]), pending]);
            let cases: [(&str, Value, &str); 3] = [
                (
                    "entitlement shortfall",
                    json!({"id": "runner-ext", "mode": "byoxpc", "required_entitlements": ["A", "B"]}),
                    "external runner worker does not hold required entitlement \"B\": absent",
                ),
                (
                    "unknown id",
                    json!({"id": "ghost", "mode": "byoxpc"}),
                    "external runner not found in registry",
                ),
                (
                    "pending record",
                    json!({"id": "pending-ext", "mode": "byoxpc"}),
                    "external runner is pending installation",
                ),
            ];
            for (label, runner, expected) in cases {
                let request = request_file(&root, Some(runner));
                let observed = observe(&app, Some(&registry), &[request.to_str().unwrap()]);
                assert_eq!(observed.loads, vec![manifest_path.clone()], "{label}");
                assert!(observed.calls.is_empty(), "{label}");
                let (wire, exit_code) = envelope_of(&observed.output);
                assert_eq!(exit_code, 2, "{label}");
                assert_eq!(wire["result"]["normalized_outcome"], "tool_error");
                assert_eq!(wire["result"]["error"], expected, "{label}");
                let specimen = &wire["data"]["specimen"];
                assert!(specimen["runner_provenance"].is_null(), "{label}");
                assert_eq!(
                    specimen["app_provenance"]["evidence_manifest_path"],
                    manifest_path.display().to_string()
                );
                for role in ROLE_NAMES {
                    assert_eq!(
                        specimen["binaries"][role]["reason"], expected,
                        "{label}: {role}"
                    );
                }
            }
            fs::remove_dir_all(&root).unwrap();
        }

        #[test]
        fn refusals_before_selection_load_at_most_once_and_never_invoke_the_client() {
            let root = scratch("arguments");
            let app = synthetic_app(&root);
            let manifest_path = install_manifest(&app, ManifestState::Valid);
            // Argument refusals never reach the app root.
            for args in [
                &["--bogus"][..],
                &["--runner-mode", "machme"],
                &["--timeout-ms", "soon"],
                &["/r.json", "--bogus"],
            ] {
                let observed = observe(&app, None, args);
                assert!(observed.loads.is_empty(), "{args:?}");
                assert!(observed.calls.is_empty(), "{args:?}");
                let (wire, exit_code) = envelope_of(&observed.output);
                assert_eq!(exit_code, 2, "{args:?}");
                assert_eq!(wire["result"]["normalized_outcome"], "tool_error");
                assert!(
                    wire["data"]["specimen"]["app_provenance"].is_null(),
                    "{args:?}"
                );
            }
            let observed = observe(&app, None, &["--help"]);
            assert!(matches!(observed.output, RunOutput::Help));
            assert!(observed.loads.is_empty() && observed.calls.is_empty());
            // Request refusals after admission carry the provenance of the one load.
            let missing = root.join("absent.json");
            for (label, args, error) in [
                ("no path", vec![], "missing <request.json>"),
                (
                    "absent file",
                    vec![missing.to_str().unwrap()],
                    "request.json not found",
                ),
            ] {
                let observed = observe(&app, None, &args);
                assert_eq!(observed.loads, vec![manifest_path.clone()], "{label}");
                assert!(observed.calls.is_empty(), "{label}");
                let (wire, exit_code) = envelope_of(&observed.output);
                assert_eq!(exit_code, 2, "{label}");
                assert!(
                    wire["result"]["error"].as_str().unwrap().contains(error),
                    "{label}: {}",
                    wire["result"]["error"]
                );
                assert_eq!(
                    wire["data"]["specimen"]["app_provenance"]["evidence_manifest_path"],
                    manifest_path.display().to_string(),
                    "{label}"
                );
                assert!(wire["data"]["specimen"]["runner_provenance"].is_null());
            }
            fs::remove_dir_all(&root).unwrap();
        }
    }

    // ---- Envelope shape golden ------------------------------------------------
    // A field-complete `kind: "run"` envelope: every optional object populated
    // and every key typed. `tests/fixtures/contract/envelope_shape.json`
    // records its shape per object path; the runner reply inside it is opaque
    // here because `response_shape.json` records that shape. The nested
    // helper envelopes are hand-built here and checked against the same golden
    // by the helper's own tests (`sbpl-check.rs`).
    mod envelope_shape {
        use super::*;
        use crate::dossier::{AppProvenance, Augmentation, BinaryRecord, Imports, PolicyDossier};
        use crate::evidence::{VerifyMismatch, VerifyReport};
        use crate::policy_check::PolicyCheckCapture;
        use crate::runner_manager::{RunnerEntitlements, RunnerSignature};
        use crate::runner_select::RunnerTarget;
        use crate::sbpl_imports::ImportRecord;
        use crate::utils::OutputCapture;

        fn full_result() -> json_contract::JsonResult {
            json_contract::JsonResult {
                ok: true,
                rc: Some(0),
                exit_code: Some(0),
                normalized_outcome: Some("finished".into()),
                errno: Some(0),
                error: Some("constructed".into()),
                stderr: Some("".into()),
                stdout: Some("".into()),
            }
        }

        fn capture(limit: usize) -> OutputCapture {
            OutputCapture {
                stdout_parse_error: Some("constructed".into()),
                stdout_truncated: false,
                stdout_capture_error: Some("constructed".into()),
                stdout_bytes_received: Some(2),
                stdout_bytes_retained: Some(2),
                stderr_bytes_received: Some(0),
                stderr_bytes_retained: Some(0),
                capture_limit_bytes: limit,
                stderr: String::new(),
                stderr_truncated: false,
            }
        }

        fn text_capture(limit: usize) -> crate::utils::TextOutputCapture {
            crate::utils::TextOutputCapture {
                capture: capture(limit),
                stdout_raw: Some("{}".into()),
            }
        }

        fn import_record() -> ImportRecord {
            ImportRecord {
                name: "system.sb".into(),
                resolved_path: Some("/System/Library/Sandbox/Profiles/system.sb".into()),
                sha256: Some("f".repeat(64)),
                size_bytes: Some(1),
                mtime_unix: Some(1),
                error: Some("constructed".into()),
            }
        }

        fn nested_envelope(kind: &str, data: Value) -> Value {
            let text = json_contract::render_envelope(kind, full_result(), &data).unwrap();
            serde_json::from_str(&text).unwrap()
        }

        /// The fallback compilation's envelope with every field present;
        /// `sbpl-check.rs` compares its own emitted shape with this subtree.
        fn sbpl_check_envelope() -> Value {
            nested_envelope(
                "sbpl_check",
                json!({
                    "policy_format": "sbpl", "policy_sha256": "f".repeat(64),
                    "macos_build_version": "23J220",
                    "params_present": true, "params_count": 1,
                    "compile": {"stage": "compile", "ok": true, "error": "constructed"},
                    "import_inventory": {
                        "records": [serde_json::to_value(import_record()).unwrap()],
                        "truncated": false, "cycle": ["a", "b"],
                        "policy_closure_sha256": "f".repeat(64),
                    },
                }),
            )
        }

        fn binary() -> BinaryRecord {
            BinaryRecord {
                path: Some("/constructed/binary".into()),
                actual_sha256: Some("a".repeat(64)),
                baseline_sha256: Some("b".repeat(64)),
                verification: "mismatch".into(),
                reason: Some("constructed".into()),
            }
        }

        fn field_complete_run_envelope() -> (json_contract::JsonResult, RunData) {
            let target = RunnerTarget {
                kind: RunnerKind::Byoxpc,
                connection: RunnerConnectionKind::MachService { privileged: false },
                service_name: "com.constructed.runner".into(),
                bundle_id: Some("com.constructed.runner".into()),
                bundle_path: Some(PathBuf::from("/constructed/Runner.xpc")),
                executable_path: Some(PathBuf::from(
                    "/constructed/Runner.xpc/Contents/MacOS/PWRunner",
                )),
                registry_id: Some("runner-ext".into()),
                signature: Some(RunnerSignature {
                    extra: Default::default(),
                    team_id: Some("TEAM123456".into()),
                    identity: Some("constructed".into()),
                    cdhash: Some("ab".repeat(20)),
                    valid: true,
                    adhoc: false,
                }),
                entitlements: Some(RunnerEntitlements {
                    extra: Default::default(),
                    raw_plist: Some("<plist/>".into()),
                    keys: vec!["com.apple.security.app-sandbox".into()],
                    granted: vec!["com.apple.security.app-sandbox".into()],
                    error: Some("constructed".into()),
                }),
                worker_signature: Some(RunnerSignature {
                    extra: Default::default(),
                    team_id: Some("TEAM123456".into()),
                    identity: Some("constructed".into()),
                    cdhash: Some("cd".repeat(20)),
                    valid: true,
                    adhoc: false,
                }),
                worker_entitlements: Some(RunnerEntitlements {
                    extra: Default::default(),
                    raw_plist: Some("<plist/>".into()),
                    keys: vec!["com.apple.security.cs.allow-jit".into()],
                    granted: vec!["com.apple.security.cs.allow-jit".into()],
                    error: Some("constructed".into()),
                }),
                validator_signature: Some(RunnerSignature {
                    extra: Default::default(),
                    team_id: Some("TEAM123456".into()),
                    identity: Some("constructed".into()),
                    cdhash: Some("ef".repeat(20)),
                    valid: true,
                    adhoc: false,
                }),
                validator_entitlements: Some(RunnerEntitlements {
                    extra: Default::default(),
                    raw_plist: Some("<plist/>".into()),
                    keys: vec![],
                    granted: vec![],
                    error: Some("constructed".into()),
                }),
                unentitled_worker_signature: Some(RunnerSignature {
                    extra: Default::default(),
                    team_id: Some("TEAM123456".into()),
                    identity: Some("constructed".into()),
                    cdhash: Some("12".repeat(20)),
                    valid: true,
                    adhoc: false,
                }),
                unentitled_worker_entitlements: Some(RunnerEntitlements {
                    extra: Default::default(),
                    raw_plist: Some("<plist/>".into()),
                    keys: vec![],
                    granted: vec![],
                    error: Some("constructed".into()),
                }),
            };
            let specimen = Specimen {
                request_path: Some("/constructed/request.json".into()),
                policy: PolicyDossier {
                    augmentation: Augmentation {
                        status: "applied".into(),
                        applied: vec!["augment".into()],
                        original_sha256: Some("c".repeat(64)),
                        applied_sha256: Some("d".repeat(64)),
                        error: Some("constructed".into()),
                    },
                    imports: Imports {
                        status: "incomplete".into(),
                        closure_sha256: Some("e".repeat(64)),
                        records: vec![import_record()],
                        cycle: Some(vec!["a".into(), "b".into()]),
                        exceeded: Some("depth".into()),
                        failure: Some("constructed".into()),
                    },
                },
                host: host(),
                runner_provenance: Some(runner_provenance_from_target(&target)),
                app_provenance: Some(AppProvenance {
                    evidence_manifest_path: "/constructed/manifest.json".into(),
                    evidence_verify: Some(VerifyReport {
                        ok: false,
                        checked: 1,
                        mismatches: vec![VerifyMismatch {
                            id: "tool".into(),
                            rel_path: "Contents/MacOS/tool".into(),
                            expected_sha256: Some("a".repeat(64)),
                            actual_sha256: Some("b".repeat(64)),
                            error: Some("constructed".into()),
                        }],
                        manifest_path: "/constructed/manifest.json".into(),
                        schema_version: 1,
                        notes: Some(vec!["constructed".into()]),
                    }),
                }),
                binaries: Binaries {
                    service: Some(binary()),
                    worker: Some(binary()),
                    validator: Some(binary()),
                    unentitled_worker: Some(binary()),
                },
                actors: Some(vec![crate::dossier::ActorDossier {
                    actor_id: Some("B".into()),
                    mode: Some("apply".into()),
                    policy: PolicyDossier {
                        augmentation: Augmentation {
                            status: "applied".into(),
                            applied: vec!["augment".into()],
                            original_sha256: Some("c".repeat(64)),
                            applied_sha256: Some("d".repeat(64)),
                            error: Some("constructed".into()),
                        },
                        imports: Imports {
                            status: "incomplete".into(),
                            closure_sha256: Some("e".repeat(64)),
                            records: vec![import_record()],
                            cycle: Some(vec!["a".into(), "b".into()]),
                            exceeded: Some("depth".into()),
                            failure: Some("constructed".into()),
                        },
                    },
                }]),
            };
            let reply = json!({
                "producer": crate::reply_fixtures::producer(),
                "normalized_outcome": "finished", "rc": 0, "pid": 42, "specimen_id":"shape", "steps": [], "phases": [],
            });
            let data = RunData {
                execution: ExecutionData {
                    specimen,
                    policy_check: Some(PolicyCheckCapture {
                        status: "ok".into(),
                        tool_exit_code: 0,
                        output: text_capture(crate::utils::HELPER_CAPTURE_BYTES),
                        envelope: Some(sbpl_check_envelope()),
                    }),
                    actor_policy_checks: Some(vec![ActorPolicyCheck {
                        actor_id: Some("B".into()),
                        policy_check: PolicyCheckCapture {
                            status: "ok".into(),
                            tool_exit_code: 0,
                            output: text_capture(crate::utils::HELPER_CAPTURE_BYTES),
                            envelope: Some(sbpl_check_envelope()),
                        },
                    }]),
                    timeout_ms: Some(DEFAULT_TIMEOUT_MS),
                    runner_client: Some(RunnerClientRun {
                        argv: vec!["constructed-client".into()],
                        started_at_unix_ms: 1_000,
                        ended_at_unix_ms: 2_500,
                        exit_code: 0,
                        request_delivery: Some(RequestDelivery {
                            bytes_written: 2,
                            error: Some("constructed".into()),
                        }),
                        output: capture(crate::utils::RUNNER_CAPTURE_BYTES),
                        transport: Some(crate::runner_client::TransportCapture::Typed(
                            serde_json::from_value(crate::runner_client::test_shape_capture())
                                .unwrap(),
                        )),
                        transport_admission: "accepted".into(),
                        transport_error: Some("constructed".into()),
                        submission: "invoked".into(),
                        runner_reply_error: Some(crate::runner_client::ReplyError {
                            refusal: crate::runner_client::ReplyRefusal::Malformed,
                            message: "constructed".into(),
                        }),
                    }),
                    runner_result: Some(fixture_reply(reply)),
                    // Field-complete shape fixture, including an optional refusal record.
                    request_failure: Some(RequestFailureProjection::Runner(
                        serde_json::from_value(
                            json!({"code": "unknown_field", "path": ["policy", "typo"],
                        "expected_contract": json_contract::BUILD_CONTRACT}),
                        )
                        .unwrap(),
                    )),
                },
                runner_sandbox_diagnostics: Some(RunnerExecutionDiagnostics {
                    process_disposition: "clean_exit",
                    termination_cause: Some("host_sentinel_deadline"),
                    stop_reason: Some("done".into()),
                    disposition_integrity: Some("valid"),
                    disposition_issues: vec![IntegrityIssue {
                        subject_path: Some(vec!["steps".into()]),
                        ..integrity_issue("missing_record", "constructed".into())
                    }],
                    actors: Some(vec![
                        crate::porcelain_admission::ActorExecutionDiagnostics {
                            actor_id: Some("B".into()),
                            process_disposition: "clean_exit",
                            termination_cause: Some("host_sentinel_deadline"),
                            stop_reason: Some("done".into()),
                            disposition_integrity: Some("valid"),
                            disposition_issues: vec![IntegrityIssue {
                                subject_path: Some(vec!["steps".into()]),
                                ..integrity_issue("missing_record", "constructed".into())
                            }],
                        },
                    ]),
                }),
            };
            (full_result(), data)
        }

        /// Compare `current` with the golden at `golden_path`. Anything but `Ok`
        /// writes the candidate beside the case artifacts and fails with this
        /// advice: review the diff, update the affected contract definitions and
        /// examples, then replace the golden and regenerate the surface views.
        fn check_golden(
            golden_path: &Path,
            current: &crate::shape::Shape,
            candidate_name: &str,
        ) -> Result<(), String> {
            let golden: Option<Value> = std::fs::read(golden_path)
                .ok()
                .and_then(|bytes| serde_json::from_slice(&bytes).ok());
            let verdict = crate::shape::classify(golden.as_ref(), current);
            if verdict == crate::shape::Verdict::Ok {
                return Ok(());
            }
            let artifacts = std::env::var_os("PW_TEST_ARTIFACTS")
                .map(std::path::PathBuf::from)
                .unwrap_or_else(std::env::temp_dir);
            let candidate_path = artifacts.join(candidate_name);
            let candidate = serde_json::json!({ "shape": crate::shape::shape_to_value(current) });
            let mut text = serde_json::to_string_pretty(&candidate).map_err(|e| e.to_string())?;
            text.push('\n');
            std::fs::write(&candidate_path, text)
                .map_err(|e| format!("{}: {e}", candidate_path.display()))?;
            let advice = format!(
                "review the diff, then replace {} with {}",
                golden_path.display(),
                candidate_path.display()
            );
            Err(match verdict {
                crate::shape::Verdict::Ok => unreachable!(),
                crate::shape::Verdict::MissingGolden => format!("no shape golden; {advice}"),
                crate::shape::Verdict::Update(detail) => format!("{detail}; {advice}"),
            })
        }

        #[test]
        fn envelope_shape_golden_agrees_with_the_manifest() {
            let (result, data) = field_complete_run_envelope();
            let text = json_contract::render_envelope("run", result, &data).unwrap();
            let wire: Value = serde_json::from_str(&text).unwrap();
            let mut current = crate::shape::Shape::new();
            crate::shape::collect(
                &wire,
                "envelope",
                &["envelope.data.runner_result"],
                &mut current,
            )
            .unwrap();
            // The fixture types every key it carries; the reply golden owns the reply.
            for (path, keys) in &current {
                for (key, kind) in keys {
                    assert_ne!(kind, "null", "{path}.{key} is untyped in the fixture");
                }
            }
            assert_eq!(current["envelope.data"]["runner_result"], "object");
            assert!(!current.contains_key("envelope.data.runner_result"));
            let golden = Path::new(env!("CARGO_MANIFEST_DIR"))
                .join("../tests/fixtures/contract/envelope_shape.json");
            check_golden(&golden, &current, "envelope_shape.candidate.json").unwrap();
        }
    }
}
