//! Orchestrates a single run and builds the JSON envelope.
//!
//! The controller reads the request, parses the app evidence manifest once,
//! selects a runner, collects the specimen dossier, delivers the held request
//! string to the Swift client on stdin, gates the reply on its response
//! version, and attaches best-effort evidence (sandbox logs, the fallback
//! helper compilation on `xpc_error`).
//!
//! Published worker preparation/application failures are runner_failed. The
//! fallback sbpl-check reports only its own compilation, not missing worker
//! progress or the cause of a lost reply. Unified-log capture is optional.

use serde::Serialize;
use serde_json::Value;
use serde_json::json;
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
use crate::log_capture::LogTimeout;
use crate::policy_check::{PolicyCheckCapture, run_policy_check};
use crate::request_patch::{RequestError, parse_request, validate_request_version};
use crate::runner_client::{RunnerClientRun, run_pw_runner_client};
use crate::runner_manager::RunnerKind;
use crate::runner_select::{
    RunnerConnectionKind, parse_runner_selector_value, resolve_runner_target_with_registry,
    runner_provenance_from_target, strip_runner_selector,
};
use crate::sandbox_log::{
    SandboxLogCapture, SandboxLogWindow, bounded_step_denies, capture_sandbox_logs_with_timeout,
    worker_pid,
};

pub const DEFAULT_TIMEOUT_MS: u64 = 240_000;

/// `data` of a `kind: "run"` envelope: the dossier plus the execution records.
/// Execution keys are present on every run envelope; an uncollected record is
/// null. The optional request_failure is included only when supplied.
#[derive(Serialize)]
struct ExecutionData {
    pub specimen: Specimen,
    pub policy_check: Option<PolicyCheckCapture>,
    pub timeout_ms: Option<u64>,
    pub runner_client: Option<RunnerClientRun>,
    pub runner_result: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub request_failure: Option<Value>,
}

#[derive(Serialize)]
struct RunData {
    #[serde(flatten)]
    execution: ExecutionData,
    sandbox_log_capture: Option<SandboxLogCapture>,
    runner_sandbox_diagnostics: Option<RunnerSandboxDiagnostics>,
}

// Completed before any optional collector runs. Log processing only borrows
// runner evidence and returns LogEvidence; it cannot rewrite this value.
struct CompletedExecution {
    data: ExecutionData,
    diagnostics: RunnerExecutionDiagnostics,
    result: json_contract::JsonResult,
    exit_code: i32,
}

struct LogEvidence {
    capture: Option<SandboxLogCapture>,
    diagnostics: RunnerLogDiagnostics,
}

#[derive(Serialize)]
struct RunnerSandboxDiagnostics {
    #[serde(flatten)]
    execution: RunnerExecutionDiagnostics,
    #[serde(flatten)]
    logs: RunnerLogDiagnostics,
}

#[derive(Serialize)]
struct RunnerExecutionDiagnostics {
    pub process_disposition: &'static str,
    pub termination_cause: Option<&'static str>,
    /// Projection of the worker disposition record's stop reason; null for an
    /// unresolved question.
    pub stop_reason: Option<String>,
    /// `valid` or `invalid` (claims withheld); null without a worker.
    pub disposition_integrity: Option<&'static str>,
    /// Integrity issues plus the record's own reported conflicts; empty when none.
    pub disposition_issues: Vec<Value>,
}

#[derive(Serialize)]
struct RunnerLogDiagnostics {
    pub correlation_status: &'static str,
    /// Step IDs whose attempt the runner itself classified as a permission-shaped
    /// failure and that no captured event names as a candidate. A non-empty
    /// list means this capture yielded no candidate for denials the attempts
    /// reported, not that nothing was denied; it makes no claim about the OS
    /// log store (a record can exist under another path form, such as a
    /// resolved symlink) and never says why. Null when correlation was not
    /// possible or the reply carries no per-step comparison.
    pub permission_failures_without_record: Option<Vec<String>>,
}

/// The version gate for a received runner reply.
pub enum ReplyVersion {
    Supported,
    Unsupported(serde_json::Number),
    Malformed(String),
}

/// Check a reply's `schema_version` before interpreting any of its records.
/// A missing or noninteger version is malformed; another integer is
/// unsupported. Nothing reads a reply under a previous version's rules.
pub fn reply_version(reply: &Value) -> ReplyVersion {
    match reply.get("schema_version") {
        None => ReplyVersion::Malformed("runner reply carries no schema_version".to_string()),
        Some(Value::Number(n)) if n.is_i64() || n.is_u64() => {
            if n.as_u64() == Some(u64::from(crate::json_contract::RESPONSE_SCHEMA_VERSION)) {
                ReplyVersion::Supported
            } else {
                ReplyVersion::Unsupported(n.clone())
            }
        }
        Some(other) => ReplyVersion::Malformed(format!(
            "runner reply schema_version is not an integer: {other}"
        )),
    }
}

fn result(
    ok: bool,
    exit_code: i32,
    outcome: &str,
    error: Option<String>,
) -> json_contract::JsonResult {
    json_contract::JsonResult {
        ok,
        rc: None,
        exit_code: Some(exit_code),
        normalized_outcome: Some(outcome.to_string()),
        errno: None,
        error,
        stderr: None,
        stdout: None,
    }
}

/// `data` for an envelope written without log collection: the dossier and
/// whatever execution records exist, every other key null.
fn execution_only(
    specimen: Specimen,
    timeout_ms: Option<u64>,
    runner_client: Option<RunnerClientRun>,
    runner_result: Option<Value>,
) -> RunData {
    RunData {
        execution: ExecutionData {
            specimen,
            policy_check: None,
            timeout_ms,
            runner_client,
            runner_result,
            request_failure: None,
        },
        sandbox_log_capture: None,
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
        result(false, 2, "tool_error", Some(error)),
        execution_only(specimen, timeout_ms, None, None),
    )
}

/// What a run produces: the usage text request, or one rendered `kind: "run"`
/// envelope with the process exit code it carries. `cmd_run` prints it; the
/// controlled orchestration tests read it.
pub enum RunOutput {
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
    data.execution.request_failure = Some(json!(error.failure));
    envelope(
        result(false, 1, "bad_request", Some(error.message)),
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
/// and how the client is invoked. Production binds the real ones; a test binds
/// counting or capturing closures around them and reads the rendered envelope.
pub struct RunDependencies<'a> {
    pub app_root: &'a dyn Fn() -> Result<PathBuf, String>,
    pub load_manifest: &'a dyn Fn(&Path) -> Result<EvidenceManifest, String>,
    /// `None` resolves the registry from `PW_RUNNER_REGISTRY` or `$HOME`.
    pub registry_path: Option<&'a Path>,
    pub client: &'a dyn Fn(
        &str,
        &str,
        u64,
        &RunnerConnectionKind,
    ) -> Result<(RunnerClientRun, Option<Value>), String>,
}

impl RunDependencies<'static> {
    pub fn production() -> Self {
        RunDependencies {
            app_root: &app_root_from_current_exe,
            load_manifest: &evidence::load_manifest,
            registry_path: None,
            client: &run_pw_runner_client,
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

/// What a client capture permits. A delivery error is a controller failure
/// that takes precedence over any captured reply; otherwise the reply's
/// version gates every semantic reader.
enum ReplyAdmission {
    DeliveryFailed(String),
    Refused {
        outcome: &'static str,
        error: String,
    },
    Admitted,
}

fn admit_reply(client: &RunnerClientRun, reply: Option<&Value>) -> ReplyAdmission {
    if let Some(error) = client
        .request_delivery
        .as_ref()
        .and_then(|d| d.error.clone())
    {
        return ReplyAdmission::DeliveryFailed(error);
    }
    match reply.map(reply_version) {
        None | Some(ReplyVersion::Supported) => ReplyAdmission::Admitted,
        Some(ReplyVersion::Unsupported(version)) => ReplyAdmission::Refused {
            outcome: "unsupported_runner_response",
            error: format!(
                "runner reply carries response schema {version}; this controller reads only {}",
                json_contract::RESPONSE_SCHEMA_VERSION
            ),
        },
        Some(ReplyVersion::Malformed(error)) => ReplyAdmission::Refused {
            outcome: "malformed_runner_response",
            error,
        },
    }
}

fn runner_outcome(reply: Option<&Value>) -> &str {
    reply
        .and_then(|v| v.get("normalized_outcome"))
        .and_then(Value::as_str)
        .unwrap_or("runner_output_not_json")
}

/// The independent fallback compilation, requested only for an admitted
/// `xpc_error` reply. A helper launch or delivery failure is recorded as an
/// unavailable capture; the runner reply is never changed by it.
fn fallback_policy_check(
    reply: Option<&Value>,
    run: impl FnOnce() -> Result<PolicyCheckCapture, String>,
) -> Option<PolicyCheckCapture> {
    if runner_outcome(reply) != "xpc_error" {
        return None;
    }
    Some(run().unwrap_or_else(PolicyCheckCapture::unavailable))
}

struct Parsed {
    request_path: Option<PathBuf>,
    timeout_ms: u64,
    runner_mode_arg: Option<String>,
    no_log_capture: bool,
    log_timeout: LogTimeout,
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
        no_log_capture: false,
        log_timeout: LogTimeout::default(),
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
            "--log-timeout-ms" => {
                let Some(value) = args.get(idx + 1).and_then(|s| s.to_str()) else {
                    return Arguments::Error(
                        parsed.request_path,
                        "missing value for --log-timeout-ms".to_string(),
                    );
                };
                match LogTimeout::parse(value) {
                    Ok(timeout) => parsed.log_timeout = timeout,
                    Err(e) => return Arguments::Error(None, e),
                }
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
            "--no-log-capture" => {
                parsed.no_log_capture = true;
                idx += 1;
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
pub fn run(args: &[OsString], deps: &RunDependencies) -> Result<RunOutput, String> {
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
    if let Err(error) = validate_request_version(&request_value) {
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
        Ok(pair) => pair,
        Err(error) => return tool_error(specimen, timeout_ms, error),
    };

    // The reply is retained unchanged on every refusal; nothing reads it
    // before admission.
    let (outcome, exit_code, error) = match admit_reply(&runner_client, runner_result.as_ref()) {
        ReplyAdmission::DeliveryFailed(error) => ("tool_error", 2, error),
        ReplyAdmission::Refused { outcome, error } => (outcome, 1, error),
        ReplyAdmission::Admitted => {
            let policy_check =
                fallback_policy_check(runner_result.as_ref(), || run_policy_check(&held));
            let execution = complete_execution(ExecutionData {
                specimen,
                policy_check,
                timeout_ms,
                runner_client: Some(runner_client),
                runner_result,
                request_failure: None,
            });
            let (result, data, exit_code) = attach_sandbox_logs(
                execution,
                &request_value,
                parsed.no_log_capture,
                |pid, process, window| {
                    capture_sandbox_logs_with_timeout(pid, process, window, parsed.log_timeout)
                },
            );
            return envelope(result, &data, exit_code);
        }
    };
    let data = execution_only(specimen, timeout_ms, Some(runner_client), runner_result);
    envelope(
        result(false, exit_code, outcome, Some(error)),
        &data,
        exit_code,
    )
}

fn complete_execution(mut data: ExecutionData) -> CompletedExecution {
    let diagnostics = execution_diagnostics(data.runner_result.as_ref());
    let runner_outcome = runner_outcome(data.runner_result.as_ref()).to_string();
    if runner_outcome == "bad_request" {
        data.request_failure = data
            .runner_result
            .as_ref()
            .and_then(|r| r.get("request_failure"))
            .cloned();
    }
    let ok = runner_outcome == "ok";
    let exit_code = if ok { 0 } else { 1 };

    let client_output = data.runner_client.as_ref().map(|c| &c.output);
    let error = if ok {
        None
    } else if let Some(v) = data
        .runner_result
        .as_ref()
        .and_then(|v| v.get("error"))
        .and_then(|v| v.as_str())
    {
        Some(v.to_string())
    } else if let Some(v) = client_output.and_then(|o| o.stdout_capture_error.as_ref()) {
        Some(v.clone())
    } else if let Some(v) = client_output.and_then(|o| o.stdout_parse_error.as_ref()) {
        Some(format!("runner output parse error: {v}"))
    } else {
        Some("run did not complete successfully".to_string())
    };

    let result = json_contract::JsonResult {
        ok,
        rc: None,
        exit_code: Some(exit_code),
        normalized_outcome: Some(runner_outcome),
        errno: None,
        error,
        stderr: None,
        stdout: None,
    };

    CompletedExecution {
        data,
        diagnostics,
        result,
        exit_code,
    }
}

// This is the production assembly seam. The collector receives only its query
// inputs; log processing has read-only execution evidence and returns only
// log-owned fields. Flattening merges the two channels into the existing wire
// shape without granting either channel ownership of the other's fields.
fn attach_sandbox_logs(
    execution: CompletedExecution,
    request: &Value,
    disabled: bool,
    collect: impl FnOnce(i64, &str, SandboxLogWindow) -> Result<SandboxLogCapture, String>,
) -> (json_contract::JsonResult, RunData, i32) {
    let logs = collect_log_evidence(
        execution.data.runner_result.as_ref(),
        request,
        execution.data.runner_client.as_ref(),
        disabled,
        collect,
    );
    let data = RunData {
        execution: execution.data,
        sandbox_log_capture: logs.capture,
        runner_sandbox_diagnostics: Some(RunnerSandboxDiagnostics {
            execution: execution.diagnostics,
            logs: logs.diagnostics,
        }),
    };
    (execution.result, data, execution.exit_code)
}

fn collect_log_evidence(
    runner: Option<&Value>,
    request: &Value,
    client: Option<&RunnerClientRun>,
    disabled: bool,
    collect: impl FnOnce(i64, &str, SandboxLogWindow) -> Result<SandboxLogCapture, String>,
) -> LogEvidence {
    let mut capture = if disabled {
        None
    } else {
        // The log window is the client span; the worker PID comes from the reply.
        match (worker_pid(runner), client) {
            (Some(pid), Some(client)) => {
                let window = SandboxLogWindow::runner_client_span(
                    client.started_at_unix_ms,
                    client.ended_at_unix_ms,
                );
                Some(
                    collect(i64::from(pid), "pw-probe-runner", window.clone()).unwrap_or_else(
                        |err| SandboxLogCapture {
                            window,
                            capture_status: "requested_unavailable".into(),
                            tool_exit_code: 1,
                            blocked_reason: None,
                            output: crate::utils::JsonOutputCapture::unavailable(
                                err,
                                crate::utils::OBSERVER_CAPTURE_BYTES,
                            ),
                            observer: None,
                            observed_deny: None,
                            deny_events: None,
                            step_denies: None,
                            supervision: None,
                            processing_cutoff: None,
                        },
                    ),
                )
            }
            _ => None,
        }
    };
    let diagnostics = finish_sandbox_log_capture(runner, request, disabled, &mut capture);
    LogEvidence {
        capture,
        diagnostics,
    }
}

// Association and log diagnostics share one availability gate; retained events
// from a failed capture or without an authoritative PID cannot gain candidates.
fn finish_sandbox_log_capture(
    runner: Option<&Value>,
    request: &Value,
    disabled: bool,
    capture: &mut Option<SandboxLogCapture>,
) -> RunnerLogDiagnostics {
    if let Some(capture) = capture.as_mut() {
        capture.step_denies = None;
        if !disabled && worker_pid(runner).is_some() && capture.capture_status == "captured" {
            if let (Some(steps), Some(events)) = (
                runner
                    .and_then(|r| r.get("steps"))
                    .and_then(Value::as_array),
                capture.deny_events.as_ref(),
            ) {
                let plan = request.get("probe_plan").and_then(Value::as_array);
                match bounded_step_denies(
                    steps,
                    plan.map(Vec::as_slice).unwrap_or(&[]),
                    events,
                    worker_pid(runner),
                    capture.supervision.as_ref().map(|r| r.budget),
                ) {
                    Ok(associations) => capture.step_denies = Some(associations),
                    Err(cutoff) => {
                        capture.capture_status = if cutoff.reason == "deadline" {
                            "timeout"
                        } else {
                            "overflow"
                        }
                        .into();
                        capture.processing_cutoff = Some(cutoff);
                    }
                }
            }
        }
    }
    log_diagnostics(runner, disabled, capture.as_ref())
}

// Execution disposition and optional log correlation are separate observations.
// No outcome gate, host/client PID fallback, or causal interpretation of a match.

// Worker disposition record projection (tests/FAILURE-PROPAGATION-CONTRACT.md,
// "Worker disposition record"). The controller validates the carried record
// against the raw facts it cites and projects from it; it never derives a
// competing lifecycle answer from raw fields or prose. Spellings are shared
// with tests/lib/lifecycle_contract.py.
const DISPOSITION_CLAIM_STATES: &[&str] =
    &["supported", "unresolved", "conflicting", "inapplicable"];
const DISPOSITION_RUN_QUESTIONS: &[&str] = &[
    "final_status",
    "stop_reason",
    "cleanup_trigger",
    "grace_end",
    "kill_request_and_result",
    "collection_basis",
    "progress_association",
];
const DISPOSITION_STEP_QUESTIONS: &[&str] = &[
    "step_boundary_reached",
    "step_result_published",
    "step_requested_operation_applicability",
];
const DISPOSITION_RUN_REFERENCES: &[&str] = &[
    "reaped",
    "exit_code",
    "term_signal",
    "poll_stop_reason",
    "exit_requested",
    "termination_request",
    "wait_errors",
    "cleanup_trigger",
    "grace_end",
    "collection_basis",
    "done_observed",
    "progress",
    "worker_failure",
    "plan",
];
const DISPOSITION_STEP_REFERENCES: &[&str] = &["slot", "attempt_support"];
const CAUSE_FOR_TRIGGER: &[(&str, &str)] = &[
    ("deadline_expiry", "host_sentinel_deadline"),
    ("completion", "host_exit_grace_exhausted"),
    ("poll_wait_error", "host_cleanup_after_wait_error"),
    ("policy_transfer_error", "host_cleanup_after_transfer_error"),
];

struct DispositionProjection {
    disposition: &'static str,
    cause: Option<&'static str>,
    stop_reason: Option<String>,
    integrity: Option<&'static str>,
    issues: Vec<Value>,
}

fn integrity_issue(kind: &str, detail: String) -> Value {
    json!({"kind": kind, "detail": detail})
}

fn reference_resolves(token: &str, sub: &Value, step: Option<&Value>) -> bool {
    let present = |key: &str| sub.get(key).map_or(false, |v| !v.is_null());
    match token {
        "slot" | "attempt_support" => {
            step.map_or(false, |s| s.get(token).map_or(false, |v| !v.is_null()))
        }
        // Step count/order are retained by record.steps and checked against the reply.
        "plan" => true,
        "worker_failure" => sub
            .get("worker_evidence")
            .and_then(|e| e.get("failure"))
            .map_or(false, |v| v.is_object()),
        "progress" => sub
            .get("worker_evidence")
            .and_then(|e| e.get("progress"))
            .map_or(false, |v| !v.is_null()),
        // The host records an explicit non-request as an absent object once it has
        // recorded the cleanup phase, so the token resolves beside exit_requested.
        "termination_request" => present("termination_request") || present("exit_requested"),
        other => present(other),
    }
}

fn same_termination_request(a: &Value, b: &Value) -> bool {
    a.is_object()
        && b.is_object()
        && ["signal", "rc"]
            .iter()
            .all(|k| a[*k].as_i64().is_some() && a[*k] == b[*k])
        && a["errno"] == b["errno"]
}

// Necessary witness sets. Extra references must still resolve; an unrelated
// existing field cannot substitute for the observations that support an answer.
fn sufficient_disposition_basis(name: &str, claim: &Value) -> bool {
    let has = |tokens: &[&str]| {
        tokens.iter().all(|t| {
            claim["basis"]
                .as_array()
                .map_or(false, |b| b.iter().any(|v| v.as_str() == Some(t)))
        })
    };
    match (name, claim["answer"].as_str()) {
        ("final_status", Some("signal")) => has(&["reaped", "term_signal"]),
        ("final_status", Some("exit_code")) => has(&["reaped", "exit_code"]),
        ("stop_reason", _) => has(&["poll_stop_reason"]),
        ("cleanup_trigger" | "grace_end", _) => has(&[name, "exit_requested"]),
        ("collection_basis", _) => has(&["collection_basis"]),
        ("kill_request_and_result", Some("requested")) => has(&["termination_request"]),
        ("kill_request_and_result", Some("none")) => {
            has(&["termination_request", "exit_requested"])
        }
        ("progress_association", Some("step_index" | "invalid")) => has(&["progress", "plan"]),
        ("progress_association", Some("none" | "parameter_index")) => has(&["progress"]),
        ("step_requested_operation_applicability", _) => has(&["attempt_support"]),
        ("step_boundary_reached", Some("reached")) => {
            has(&["progress"]) || has(&["slot", "attempt_support"])
        }
        ("step_boundary_reached", Some("not_reached")) => {
            has(&["progress", "slot", "collection_basis"])
        }
        ("step_result_published", Some("published")) => has(&["slot", "attempt_support"]),
        ("step_result_published", Some("unpublished")) => has(&["slot", "collection_basis"]),
        _ => true, // Preserve future answers without inventing semantics for them.
    }
}

type DispositionPosition = (usize, u64, u64);

fn disposition_progress(
    sub: &Value,
    count: usize,
) -> (Option<&str>, Option<i64>, Option<DispositionPosition>) {
    let progress = &sub["worker_evidence"]["progress"];
    let op = progress["operation"].as_u64();
    let phase = progress["phase"].as_u64();
    let order = [1, 2, 3, 4, 5, 6, 7, 8, 11, 9, 10]
        .iter()
        .position(|v| Some(*v) == op);
    let (Some(op), Some(phase @ (1 | 2)), Some(order)) = (op, phase, order) else {
        return (None, None, None);
    };
    let index = progress["index"].as_u64();
    let indexed = op == 9 || op == 4;
    if (indexed && index.is_none())
        || (!indexed && !progress["index"].is_null())
        || index.map_or(false, |i| i >= 0xfffff || (op == 9 && i >= count as u64))
        || progress["raw"].as_u64() != Some((op << 24) | (phase << 20) | index.map_or(0, |i| i + 1))
    {
        return (Some("invalid"), None, None);
    }
    (
        Some(if op == 9 {
            "step_index"
        } else if op == 4 {
            "parameter_index"
        } else {
            "none"
        }),
        index.map(|i| i as i64),
        Some((order, index.unwrap_or(0), phase)),
    )
}

fn disposition_summary(step: &Value) -> &'static str {
    let q = &step["questions"];
    let supported =
        |name: &str, answer: &str| q[name]["state"] == "supported" && q[name]["answer"] == answer;
    if step["attempt_support"] == "unsupported" {
        "unsupported"
    } else if supported("step_result_published", "published") {
        "completed"
    } else if q["step_boundary_reached"]["state"] == "conflicting"
        || q["step_result_published"]["state"] == "conflicting"
    {
        "conflicting"
    } else if supported("step_result_published", "unpublished")
        && supported("step_boundary_reached", "reached")
    {
        "started_without_result"
    } else if supported("step_result_published", "unpublished")
        && supported("step_boundary_reached", "not_reached")
    {
        "not_reached"
    } else {
        "unresolved"
    }
}

/// Structural and claim/basis validation of a carried record. Returns integrity
/// issues; `unrecognized_value` issues do not invalidate the record.
fn validate_disposition(
    record: &Value,
    sub: &Value,
    reply_steps: &[Value],
    reporting_failed: bool,
) -> Vec<Value> {
    let mut issues = Vec::new();
    let Some(questions) = record.get("questions").and_then(Value::as_object) else {
        return vec![integrity_issue(
            "malformed_record",
            "questions is not an object".into(),
        )];
    };
    let record_issues = record
        .get("issues")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    if record.get("issues").map_or(true, |v| !v.is_array()) {
        issues.push(integrity_issue(
            "malformed_record",
            "issues is not an array".into(),
        ));
    }
    let raw_str = |key: &str| sub.get(key).and_then(Value::as_str);
    let check_claim =
        |name: &str, claim: &Value, step: Option<(usize, &Value)>, issues: &mut Vec<Value>| {
            let where_ = match step {
                Some((i, _)) => format!("step {i} {name}"),
                None => name.to_string(),
            };
            let Some(state) = claim.get("state").and_then(Value::as_str) else {
                issues.push(integrity_issue(
                    "malformed_record",
                    format!("{where_}: claim without a state"),
                ));
                return;
            };
            if !DISPOSITION_CLAIM_STATES.contains(&state) {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("{where_}: unknown claim state {state}"),
                ));
                return;
            }
            match state {
                "supported" => {
                    if claim.get("answer").and_then(Value::as_str).is_none() {
                        issues.push(integrity_issue(
                            "invalid_claim",
                            format!("{where_}: supported claim without an answer"),
                        ));
                    }
                    match claim.get("basis").and_then(Value::as_array) {
                        Some(basis) if !basis.is_empty() => {
                            for value in basis {
                                let Some(token) = value.as_str() else {
                                    issues.push(integrity_issue(
                                        "invalid_claim",
                                        format!("{where_}: reference is not a string"),
                                    ));
                                    continue;
                                };
                                let known = DISPOSITION_RUN_REFERENCES.contains(&token)
                                    || (step.is_some()
                                        && DISPOSITION_STEP_REFERENCES.contains(&token));
                                if !known {
                                    issues.push(integrity_issue(
                                        "unresolved_reference",
                                        format!("{where_}: unknown reference {token}"),
                                    ));
                                } else if !reference_resolves(token, sub, step.map(|(_, s)| s)) {
                                    issues.push(integrity_issue(
                                        "unresolved_reference",
                                        format!("{where_}: {token} does not resolve"),
                                    ));
                                }
                            }
                        }
                        _ => issues.push(integrity_issue(
                            "invalid_claim",
                            format!("{where_}: supported claim without basis"),
                        )),
                    }
                    if !sufficient_disposition_basis(name, claim) {
                        issues.push(integrity_issue(
                            "invalid_claim",
                            format!("{where_}: insufficient witness references"),
                        ));
                    }
                }
                "conflicting" => {
                    let matches = claim
                        .get("issue")
                        .and_then(Value::as_u64)
                        .and_then(|i| record_issues.get(i as usize))
                        .map_or(false, |issue| {
                            issue.get("question").and_then(Value::as_str) == Some(name)
                                && issue.get("step_index").and_then(Value::as_u64)
                                    == step.map(|(i, _)| i as u64)
                                && issue["kind"] == "conflict"
                                && issue["rule"] == if name == "final_status" { "D1" } else { "D5" }
                                && [
                                    "final_status",
                                    "step_boundary_reached",
                                    "step_result_published",
                                ]
                                .contains(&name)
                                && issue["observations"].as_array().map_or(false, |obs| {
                                    let required: &[&str] = if name == "final_status" {
                                        &["exit_code", "term_signal"]
                                    } else {
                                        &["progress", "slot", "collection_basis"]
                                    };
                                    required
                                        .iter()
                                        .all(|t| obs.iter().any(|v| v.as_str() == Some(t)))
                                        && obs.iter().all(|v| {
                                            v.as_str().map_or(false, |t| {
                                                reference_resolves(t, sub, step.map(|(_, s)| s))
                                            })
                                        })
                                })
                        });
                    if !matches {
                        issues.push(integrity_issue(
                            "invalid_claim",
                            format!("{where_}: conflicting claim without a matching issue"),
                        ));
                    }
                }
                _ => {
                    if claim.get("reason").and_then(Value::as_str).is_none() {
                        issues.push(integrity_issue(
                            "invalid_claim",
                            format!("{where_}: {state} claim without a reason"),
                        ));
                    }
                }
            }
        };
    for name in DISPOSITION_RUN_QUESTIONS {
        match questions.get(*name) {
            Some(claim) => check_claim(name, claim, None, &mut issues),
            None => issues.push(integrity_issue(
                "malformed_record",
                format!("questions lacks {name}"),
            )),
        }
    }
    let reaped = sub.get("reaped").and_then(Value::as_bool) == Some(true);
    if raw_str("collection_basis") == Some("after_confirmed_reap") && !reaped {
        issues.push(integrity_issue(
            "invalid_claim",
            "collection_basis: terminal collection without a confirmed reap".into(),
        ));
    }
    for name in ["cleanup_trigger", "grace_end", "kill_request_and_result"] {
        if questions
            .get(name)
            .map_or(false, |q| q["state"] == "supported")
            && sub["exit_requested"] == false
        {
            issues.push(integrity_issue(
                "invalid_claim",
                format!("{name}: cleanup claim when exit was not requested"),
            ));
        }
    }
    let signal = sub.get("term_signal").and_then(Value::as_i64);
    let exit = sub.get("exit_code").and_then(Value::as_i64);
    if let Some(final_status) = questions.get("final_status") {
        let state = final_status.get("state").and_then(Value::as_str);
        let answer = final_status.get("answer").and_then(Value::as_str);
        let value = final_status.get("value").and_then(Value::as_i64);
        let contradiction = match (state, answer) {
            (Some("supported"), Some("signal")) => {
                !reaped || signal.is_none() || exit.is_some() || value != signal
            }
            (Some("supported"), Some("exit_code")) => {
                !reaped || exit.is_none() || signal.is_some() || value != exit
            }
            (Some("conflicting"), _) => !reaped || exit.is_none() || signal.is_none(),
            _ => false,
        };
        if contradiction {
            issues.push(integrity_issue(
                "invalid_claim",
                "final_status: claim contradicts reaped status".into(),
            ));
        }
    }
    for (name, key) in [
        ("stop_reason", "poll_stop_reason"),
        ("cleanup_trigger", "cleanup_trigger"),
        ("grace_end", "grace_end"),
        ("collection_basis", "collection_basis"),
    ] {
        if let Some(claim) = questions.get(name) {
            if claim.get("state").and_then(Value::as_str) == Some("supported")
                && claim.get("answer").and_then(Value::as_str) != raw_str(key)
            {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("{name}: claim contradicts the recorded host fact"),
                ));
            }
        }
    }
    if let Some(kill) = questions.get("kill_request_and_result") {
        if kill.get("state").and_then(Value::as_str) == Some("supported") {
            let request = sub
                .get("termination_request")
                .map_or(false, |v| v.is_object());
            match kill.get("answer").and_then(Value::as_str) {
                Some("requested")
                    if !request
                        || !same_termination_request(
                            &kill["value"],
                            &sub["termination_request"],
                        ) =>
                {
                    issues.push(integrity_issue(
                        "invalid_claim",
                        "kill_request_and_result: value differs from termination_request".into(),
                    ))
                }
                Some("none") if request => issues.push(integrity_issue(
                    "invalid_claim",
                    "kill_request_and_result: no-request claim beside a termination_request".into(),
                )),
                _ => {}
            }
        }
    }
    let Some(steps) = record.get("steps").and_then(Value::as_array) else {
        issues.push(integrity_issue(
            "malformed_record",
            "steps is not an array".into(),
        ));
        return issues;
    };
    if steps.len() != reply_steps.len() {
        issues.push(integrity_issue(
            "invalid_claim",
            format!(
                "disposition steps ({}) disagree with reply steps ({})",
                steps.len(),
                reply_steps.len()
            ),
        ));
    }
    let terminal = raw_str("collection_basis") == Some("after_confirmed_reap") && reaped;
    let (association, index, position) = disposition_progress(sub, steps.len());
    if let Some(claim) = questions.get("progress_association") {
        if claim["state"] == "supported"
            && matches!(
                claim["answer"].as_str(),
                Some("none" | "invalid" | "step_index" | "parameter_index")
            )
            && (claim["answer"].as_str() != association || claim["value"].as_i64() != index)
        {
            issues.push(integrity_issue(
                "invalid_claim",
                "progress_association: claim disagrees with progress identity".into(),
            ));
        }
    }
    if sub["partial_steps"].as_bool() != Some(steps.iter().any(|s| s["slot"] != "completed")) {
        issues.push(integrity_issue(
            "invalid_claim",
            "partial_steps disagrees with record slots".into(),
        ));
    }
    for (i, step) in steps.iter().enumerate() {
        if step.get("index").and_then(Value::as_u64) != Some(i as u64) {
            issues.push(integrity_issue(
                "malformed_record",
                format!("step {i} carries the wrong index"),
            ));
        }
        if let Some(reply_step) = reply_steps.get(i) {
            if step.get("step_id") != reply_step.get("step_id") {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i}: step_id disagrees with the reply"),
                ));
            }
        }
        let slot = step.get("slot").and_then(Value::as_str);
        let supported = step["attempt_support"] == "supported";
        let reached = position.map_or(false, |p| p >= (9, i as u64, 1));
        let returned = position.map_or(false, |p| p >= (9, i as u64, 2));
        let boundary_conflict =
            terminal && position.is_some() && !reached && slot == Some("completed");
        let result_conflict = terminal && returned && slot == Some("incomplete") && supported;
        if !matches!(slot, Some("completed" | "incomplete" | "absent")) {
            issues.push(integrity_issue(
                "malformed_record",
                format!("step {i}: unknown slot state"),
            ));
        }
        if !matches!(
            step.get("attempt_support").and_then(Value::as_str),
            Some("supported" | "unsupported")
        ) {
            issues.push(integrity_issue(
                "malformed_record",
                format!("step {i}: unknown attempt support"),
            ));
        }
        let Some(claims) = step.get("questions").and_then(Value::as_object) else {
            issues.push(integrity_issue(
                "malformed_record",
                format!("step {i}: questions is not an object"),
            ));
            continue;
        };
        for name in DISPOSITION_STEP_QUESTIONS {
            match claims.get(*name) {
                Some(claim) => check_claim(name, claim, Some((i, step)), &mut issues),
                None => issues.push(integrity_issue(
                    "malformed_record",
                    format!("step {i} lacks question {name}"),
                )),
            }
        }
        if let Some(applicability) = claims.get("step_requested_operation_applicability") {
            if applicability["state"] == "supported"
                && matches!(
                    applicability["answer"].as_str(),
                    Some("supported" | "unsupported")
                )
                && applicability["answer"] != step["attempt_support"]
            {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i}: applicability disagrees with attempt support"),
                ));
            }
        }
        if let Some(result) = claims.get("step_result_published") {
            if result.get("state").and_then(Value::as_str) == Some("supported") {
                match result.get("answer").and_then(Value::as_str) {
                    Some("published") if slot != Some("completed") || !supported => issues.push(integrity_issue("invalid_claim",
                        format!("step {i}: published claim on a slot that is not completed"))),
                    Some("unpublished") if slot != Some("incomplete") || !terminal || !supported || result_conflict => issues.push(integrity_issue(
                        "invalid_claim", format!("step {i}: unpublished claim needs an incomplete slot under terminal collection"))),
                    _ => {}
                }
            }
        }
        if let Some(boundary) = claims.get("step_boundary_reached") {
            let cites = |token: &str| {
                boundary["basis"].as_array().map_or(false, |basis| {
                    basis.iter().any(|v| v.as_str() == Some(token))
                })
            };
            let progress_witness = reached && cites("progress");
            let slot_witness =
                slot == Some("completed") && supported && cites("slot") && cites("attempt_support");
            if boundary.get("state").and_then(Value::as_str) == Some("supported")
                && boundary.get("answer").and_then(Value::as_str) == Some("not_reached")
                && (!terminal || slot == Some("completed") || position.is_none() || reached)
            {
                issues.push(integrity_issue("invalid_claim",
                    format!("step {i}: not_reached claim needs terminal collection and no completed slot")));
            }
            if boundary["state"] == "supported"
                && boundary["answer"] == "reached"
                && (boundary_conflict || !(progress_witness || slot_witness))
            {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i}: reached claim lacks an unopposed boundary witness"),
                ));
            }
        }
        for (name, conflict) in [
            ("step_boundary_reached", boundary_conflict),
            ("step_result_published", result_conflict),
        ] {
            if claims
                .get(name)
                .map_or(false, |q| q["state"] == "conflicting")
                && !conflict
            {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i} {name}: conflict without incompatible observations"),
                ));
            }
        }
        if let Some(reply) = reply_steps.get(i) {
            let attempt = &reply["attempt"];
            let completed = supported && slot == Some("completed");
            let reason = if completed {
                None
            } else if !supported {
                Some("attempt_not_supported")
            } else if slot == Some("absent") {
                Some("slot_absent")
            } else {
                Some("slot_incomplete")
            };
            if attempt["result_source"] != if completed { "worker" } else { "synthetic" }
                || attempt["missing_reason"].as_str() != reason
            {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i}: compatibility projections disagree with record"),
                ));
            }
            let lifecycle = &attempt["lifecycle"];
            if lifecycle["boundary"] != step["questions"]["step_boundary_reached"]
                || lifecycle["result"] != step["questions"]["step_result_published"]
            {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i}: lifecycle copies disagree with record"),
                ));
            }
            let summary = disposition_summary(step);
            match lifecycle["summary"].as_str() {
                Some(
                    s @ ("completed"
                    | "started_without_result"
                    | "not_reached"
                    | "unsupported"
                    | "unresolved"
                    | "conflicting"),
                ) if s != summary => issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i}: lifecycle summary disagrees with record"),
                )),
                None => issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i}: missing lifecycle summary"),
                )),
                _ => {}
            }
            let expected = match summary {
                "completed" => None,
                "unresolved" => Some("attempt:lifecycle_unresolved"),
                "conflicting" => Some("attempt:lifecycle_conflicting"),
                "unsupported" => Some("attempt:unsupported"),
                "not_reached" => Some("attempt:not_reached"),
                _ => Some("attempt:started_without_result"),
            };
            let limits: Vec<_> = reply["comparison"]["limitations"]
                .as_array()
                .into_iter()
                .flatten()
                .filter_map(Value::as_str)
                .filter(|l| {
                    [
                        "attempt:lifecycle_unresolved",
                        "attempt:lifecycle_conflicting",
                        "attempt:unsupported",
                        "attempt:not_reached",
                        "attempt:started_without_result",
                    ]
                    .contains(l)
                })
                .collect();
            if !(reporting_failed && reply["comparison"].is_null())
                && limits != expected.into_iter().collect::<Vec<_>>()
            {
                issues.push(integrity_issue(
                    "invalid_claim",
                    format!("step {i}: lifecycle limitations disagree with record"),
                ));
            }
        }
    }
    for (index, _) in record_issues.iter().enumerate() {
        let referenced = questions
            .values()
            .chain(
                steps
                    .iter()
                    .filter_map(|s| s["questions"].as_object())
                    .flat_map(|q| q.values()),
            )
            .any(|c| c["state"] == "conflicting" && c["issue"].as_u64() == Some(index as u64));
        if !referenced {
            issues.push(integrity_issue(
                "invalid_claim",
                format!("issue {index} is unreferenced"),
            ));
        }
    }
    issues
}

fn project_disposition(
    sub: &Value,
    reply_steps: &[Value],
    reporting_failed: bool,
) -> DispositionProjection {
    let Some(record) = sub.get("disposition").filter(|r| !r.is_null()) else {
        // A worker subprocess without the record is invalid; its claims are withheld.
        return DispositionProjection {
            disposition: "withheld",
            cause: Some("unknown"),
            stop_reason: None,
            integrity: Some("invalid"),
            issues: vec![integrity_issue(
                "missing_record",
                "a worker subprocess requires a disposition record".into(),
            )],
        };
    };
    let mut issues = validate_disposition(record, sub, reply_steps, reporting_failed);
    let invalid = issues
        .iter()
        .any(|i| i.get("kind").and_then(Value::as_str) != Some("unrecognized_value"));
    if invalid {
        return DispositionProjection {
            disposition: "withheld",
            cause: Some("unknown"),
            stop_reason: None,
            integrity: Some("invalid"),
            issues,
        };
    }
    let questions = &record["questions"];
    let claim = |name: &str| &questions[name];
    let state = |name: &str| claim(name).get("state").and_then(Value::as_str);
    let answer = |name: &str| claim(name).get("answer").and_then(Value::as_str);
    let final_state = state("final_status");
    let final_answer = answer("final_status");
    let final_value = claim("final_status").get("value").and_then(Value::as_i64);
    let disposition = match (final_state, final_answer) {
        (Some("supported"), Some("signal")) => "signaled",
        (Some("supported"), Some("exit_code")) => {
            if final_value == Some(0) {
                "clean_exit"
            } else {
                "nonzero_exit"
            }
        }
        (Some("supported"), Some(other)) => {
            issues.push(integrity_issue(
                "unrecognized_value",
                format!("final_status: unrecognized answer {other}"),
            ));
            "unrecognized"
        }
        (Some("conflicting"), _) => "conflicting",
        (Some("unresolved"), _) | (Some("inapplicable"), _) => "unconfirmed",
        _ => "unrecognized",
    };
    let mut cause = if disposition == "clean_exit" {
        None
    } else {
        Some("unknown")
    };
    if disposition == "signaled" {
        let requested_signal = claim("kill_request_and_result")
            .get("value")
            .and_then(|v| v.get("signal"))
            .and_then(Value::as_i64);
        let requested_rc = claim("kill_request_and_result")
            .get("value")
            .and_then(|v| v.get("rc"))
            .and_then(Value::as_i64);
        if state("cleanup_trigger") == Some("supported")
            && state("grace_end") == Some("supported")
            && answer("grace_end") == Some("exhausted")
            && state("kill_request_and_result") == Some("supported")
            && answer("kill_request_and_result") == Some("requested")
            && requested_rc == Some(0)
            && requested_signal == final_value
        {
            if let Some((_, label)) = CAUSE_FOR_TRIGGER
                .iter()
                .find(|(trigger, _)| Some(*trigger) == answer("cleanup_trigger"))
            {
                cause = Some(label);
            }
        }
    }
    let stop_reason = if state("stop_reason") == Some("supported") {
        answer("stop_reason")
            .filter(|s| {
                [
                    "sentinel_deadline",
                    "done",
                    "child_reaped",
                    "wait_error",
                    "policy_write_error",
                ]
                .contains(s)
            })
            .map(str::to_string)
    } else {
        None
    };
    if let Some(conflicts) = record.get("issues").and_then(Value::as_array) {
        issues.extend(conflicts.iter().cloned());
    }
    DispositionProjection {
        disposition,
        cause,
        stop_reason,
        integrity: Some("valid"),
        issues,
    }
}

fn execution_diagnostics(runner: Option<&Value>) -> RunnerExecutionDiagnostics {
    let pid = worker_pid(runner);
    let sub = runner.and_then(|r| r.get("runner_subprocess"));
    let reply_steps: Vec<Value> = runner
        .and_then(|r| r.get("steps"))
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    let projection = match (pid, sub) {
        (Some(_), Some(sub)) => project_disposition(
            sub,
            &reply_steps,
            runner.map_or(false, |r| {
                r["normalized_outcome"] == "runner_reporting_failed"
                    && r["reporting_failure"].is_object()
            }),
        ),
        _ => DispositionProjection {
            disposition: "no_worker",
            cause: None,
            stop_reason: None,
            integrity: None,
            issues: vec![],
        },
    };
    RunnerExecutionDiagnostics {
        process_disposition: projection.disposition,
        termination_cause: projection.cause,
        stop_reason: projection.stop_reason,
        disposition_integrity: projection.integrity,
        disposition_issues: projection.issues,
    }
}

fn log_diagnostics(
    runner: Option<&Value>,
    disabled: bool,
    capture: Option<&SandboxLogCapture>,
) -> RunnerLogDiagnostics {
    let pid = worker_pid(runner);
    let captured = capture.map_or(false, |c| c.capture_status == "captured");
    let events = capture.and_then(|c| c.deny_events.as_ref());
    let pid_match = match (pid, events) {
        (Some(pid), Some(events)) if captured => events.iter().any(|e| e.pid == Some(pid)),
        _ => false,
    };
    let correlation_status = if disabled || pid.is_none() {
        "not_attempted"
    } else if !captured || events.is_none() {
        "unavailable"
    } else if pid_match {
        "pid_match"
    } else {
        "no_match"
    };
    let permission_failures_without_record =
        if matches!(correlation_status, "pid_match" | "no_match") {
            permission_failures_without_record(runner, capture)
        } else {
            None
        };
    RunnerLogDiagnostics {
        correlation_status,
        permission_failures_without_record,
    }
}

// The runner's own per-step classification is the only input: a step counts
// when `comparison.observation` is `permission_failure`. Candidate membership
// comes from the associations already computed for this capture. A reply whose
// steps carry no comparison cannot be classified and yields null.
fn permission_failures_without_record(
    runner: Option<&Value>,
    capture: Option<&SandboxLogCapture>,
) -> Option<Vec<String>> {
    let steps = runner?.get("steps")?.as_array()?;
    if !steps.is_empty()
        && !steps
            .iter()
            .any(|s| s.pointer("/comparison/observation").is_some())
    {
        return None;
    }
    let recorded: std::collections::HashSet<&str> = capture
        .and_then(|c| c.step_denies.as_ref())
        .map(|associations| {
            associations
                .iter()
                .flat_map(|a| a.candidate_step_ids.iter().map(String::as_str))
                .collect()
        })
        .unwrap_or_default();
    Some(
        steps
            .iter()
            .filter(|s| {
                s.pointer("/comparison/observation").and_then(Value::as_str)
                    == Some("permission_failure")
            })
            .filter_map(|s| s.get("step_id").and_then(Value::as_str))
            .filter(|id| !recorded.contains(id))
            .map(str::to_string)
            .collect(),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sandbox_log::{SandboxDenyEvent, capture_sandbox_logs, match_step_denies};
    use crate::utils::{JsonOutputCapture, RequestDelivery};
    use serde_json::json;

    include!("log_replay_tests.rs");

    /// Fixed host facts: execution bytes are compared across collector states.
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
        let stdout = serde_json::to_vec(&runner).unwrap();
        let (output, _) = crate::utils::capture_json_output(
            &std::process::Output {
                status: std::os::unix::process::ExitStatusExt::from_raw(0),
                stdout,
                stderr: b"fixed runner-client diagnostic".to_vec(),
            },
            "runner",
            crate::utils::RUNNER_CAPTURE_BYTES,
        );
        RunnerClientRun {
            argv: vec!["controlled-client".into()],
            started_at_unix_ms: 1_000,
            ended_at_unix_ms: 2_500,
            exit_code: 0,
            request_delivery: Some(RequestDelivery {
                bytes_written: 2,
                error: None,
            }),
            output,
        }
    }

    fn execution_data(runner: Option<Value>) -> ExecutionData {
        ExecutionData {
            specimen: specimen(),
            policy_check: None,
            timeout_ms: Some(DEFAULT_TIMEOUT_MS),
            runner_client: Some(client_run(runner.as_ref())),
            runner_result: runner,
            request_failure: None,
        }
    }

    fn diagnostics_with_logs(
        runner: Option<&Value>,
        disabled: bool,
        capture: Option<&SandboxLogCapture>,
    ) -> RunnerSandboxDiagnostics {
        RunnerSandboxDiagnostics {
            execution: execution_diagnostics(runner),
            logs: log_diagnostics(runner, disabled, capture),
        }
    }

    // ---- Current-schema reply builders -------------------------------------
    // Every step carries the lifecycle copies and validator record the
    // controller and the independent consumer check; the record is derived
    // from the same subprocess facts the reply states.

    fn operation(action: &str) -> &'static str {
        match action {
            "open_read" | "access" => "file-read-data",
            "open_write" => "file-write-data",
            "unlink" => "file-write-unlink",
            other => panic!("unmapped action {other}"),
        }
    }

    fn failed_outcome(action: &str) -> &'static str {
        match action {
            "unlink" => "unlink_failed",
            "access" => "access_failed",
            _ => "open_failed",
        }
    }

    fn query(action: &str, path: &str) -> Value {
        json!({"outcome": "allow", "rc": 0, "native_rc": 0, "errno": 0, "error": null, "pid": 42,
            "result_source": "validator", "operation": operation(action), "filter_kind": "path",
            "filter_type_id": 1, "filter_value": path,
            "path_diagnostics": {"input": path, "observer": "runner_host", "phase": "after_orchestration",
                "same_as_input": ["realpath_resolved", "firmlink_resolved"]}})
    }

    fn attempt_paths(path: &str) -> Value {
        json!({"input": path, "observer": "runner_host", "phase": "after_orchestration",
            "same_as_input": ["realpath_resolved", "parent_realpath_resolved"]})
    }

    /// A completed, supported file step whose attempt reports `observation`.
    fn step(id: &str, action: &str, path: &str, observation: &str) -> Value {
        let (outcome, rc, errno, basis) = match observation {
            "succeeded" => ("ok", 0, Value::Null, "completed_worker_status"),
            "permission_failure" => (failed_outcome(action), -1, json!(1), "permission_errno"),
            "other_failure" => (
                failed_outcome(action),
                -1,
                json!(2),
                "completed_worker_status",
            ),
            other => panic!("unmapped observation {other}"),
        };
        let boundary = json!({"state": "supported", "answer": "reached", "basis": ["slot", "attempt_support"]});
        let result = json!({"state": "supported", "answer": "published", "basis": ["slot", "attempt_support"]});
        json!({"step_id": id, "sandbox_check": query(action, path),
            "attempt": {"requested_kind": "file", "requested_action": action, "requested_path": path,
                "outcome": outcome, "rc": rc, "errno": errno, "error": null, "observed_path": null,
                "result_source": "worker", "path_diagnostics": attempt_paths(path),
                "lifecycle": {"boundary": boundary, "result": result, "summary": "completed"}},
            "comparison": {"observation": observation, "observation_basis": basis,
                "operation_relation": "matched", "target_relation": "same_submitted",
                "order": "query_first", "limitations": []}})
    }

    /// A step whose attempt never published: an incomplete slot under terminal
    /// collection, with the boundary question unresolved.
    fn incomplete_step(id: &str, action: &str, path: &str) -> Value {
        let boundary = json!({"state": "unresolved", "reason": "no_progress_word"});
        let result = json!({"state": "supported", "answer": "unpublished",
            "basis": ["slot", "collection_basis"]});
        json!({"step_id": id, "sandbox_check": query(action, path),
            "attempt": {"requested_kind": "file", "requested_action": action, "requested_path": path,
                "outcome": "not_run_worker_died", "rc": -1, "errno": null,
                "error": "no completed attempt result: slot publication incomplete",
                "observed_path": null, "result_source": "synthetic", "missing_reason": "slot_incomplete",
                "path_diagnostics": attempt_paths(path),
                "lifecycle": {"boundary": boundary, "result": result, "summary": "unresolved"}},
            "comparison": {"observation": "unavailable", "observation_basis": "no_completed_worker_result",
                "operation_relation": "matched", "target_relation": "same_submitted",
                "order": "query_first", "limitations": ["attempt:lifecycle_unresolved"]}})
    }

    /// The disposition record the host carries for `sub` and the reply's steps.
    fn disposition_for(sub: &Value, steps: &[Value]) -> Value {
        let supported = |answer: Value, basis: &[&str]| json!({"state": "supported", "answer": answer, "basis": basis});
        let exit_requested = sub["exit_requested"] == true;
        let final_status = if sub["term_signal"].is_i64() {
            json!({"state": "supported", "answer": "signal", "value": sub["term_signal"],
                "basis": ["reaped", "term_signal"]})
        } else {
            json!({"state": "supported", "answer": "exit_code", "value": sub["exit_code"],
                "basis": ["reaped", "exit_code"]})
        };
        let cleanup = |name: &str| {
            if exit_requested {
                supported(sub[name].clone(), &[name, "exit_requested"])
            } else {
                json!({"state": "inapplicable", "reason": "exit_not_requested"})
            }
        };
        let kill = if sub["termination_request"].is_object() {
            json!({"state": "supported", "answer": "requested", "value": sub["termination_request"],
                "basis": ["termination_request"]})
        } else {
            json!({"state": "inapplicable", "reason": "exit_not_requested"})
        };
        let records: Vec<Value> = steps
            .iter()
            .enumerate()
            .map(|(i, s)| {
                let lifecycle = &s["attempt"]["lifecycle"];
                let slot = if s["attempt"]["result_source"] == "worker" {
                    "completed"
                } else {
                    "incomplete"
                };
                json!({"index": i, "step_id": s["step_id"], "slot": slot, "attempt_support": "supported",
                    "questions": {"step_boundary_reached": lifecycle["boundary"],
                        "step_result_published": lifecycle["result"],
                        "step_requested_operation_applicability":
                            supported(json!("supported"), &["attempt_support"])}})
            })
            .collect();
        json!({"questions": {
                "final_status": final_status,
                "stop_reason": supported(sub["poll_stop_reason"].clone(), &["poll_stop_reason"]),
                "cleanup_trigger": cleanup("cleanup_trigger"),
                "grace_end": cleanup("grace_end"),
                "kill_request_and_result": kill,
                "collection_basis": supported(sub["collection_basis"].clone(), &["collection_basis"]),
                "progress_association": {"state": "inapplicable", "reason": "no_progress_word"}},
            "steps": records, "issues": []})
    }

    /// A reply under the current response schema. A signal means the host's
    /// sentinel deadline expired and it killed the worker during cleanup.
    fn reply_with(outcome: &str, signal: Option<i32>, steps: Vec<Value>) -> Value {
        let partial = steps
            .iter()
            .any(|s| s["attempt"]["result_source"] != "worker");
        let mut sub = json!({"pid": 42, "reaped": true, "term_signal": signal,
            "exit_code": signal.is_none().then_some(0),
            "poll_stop_reason": if signal.is_some() { "sentinel_deadline" } else { "done" },
            "done_observed": signal.is_none(), "exit_requested": signal.is_some(),
            "termination_request": signal.map(|s| json!({"signal": s, "rc": 0})),
            "cleanup_trigger": signal.map(|_| "deadline_expiry"),
            "grace_end": signal.map(|_| "exhausted"),
            "collection_basis": "after_confirmed_reap", "partial_steps": partial,
            "wait_errors": [], "ready_byte_received": true,
            "ordering": {"collection_closed_before_proceed": true, "proceed_set": true,
                "proceed_observed": true, "validator_disposition": "reaped",
                "worker_lifetime_established": true, "protocol_violations": []}});
        sub["disposition"] = disposition_for(&sub, &steps);
        let records: Vec<Value> = steps
            .iter()
            .map(|s| {
                let q = &s["sandbox_check"];
                json!({"step_id": s["step_id"], "operation": q["operation"], "filter_type": "PATH",
                    "filter_type_id": 1, "filter_value": q["filter_value"], "outcome": q["outcome"],
                    "rc": q["rc"], "errno": q["errno"]})
            })
            .collect();
        let ok = outcome == "ok";
        json!({"schema_version": json_contract::RESPONSE_SCHEMA_VERSION, "specimen_id": "controlled",
            "run_kind": null, "rc": if ok { 0 } else { 1 }, "normalized_outcome": outcome,
            "error": if ok { Value::Null } else { json!("controlled worker failure") },
            "pid": 9999, "bundle_id": "controlled.service", "policy_format": "sbpl",
            "policy_sha256": "0".repeat(64), "sandboxed_after_apply": true, "test_overrides": null,
            "runner_subprocess": sub,
            "validator_subprocess": {"pid": 43, "reaped": true, "exit_code": 0, "records": records},
            "steps": steps})
    }

    fn worker(outcome: &str, signal: Option<i32>) -> Value {
        reply_with(outcome, signal, vec![])
    }

    /// A degraded reply: the host withheld every comparison and said so.
    fn reporting_failed(mut runner: Value) -> Value {
        runner["normalized_outcome"] = json!("runner_reporting_failed");
        runner["rc"] = json!(1);
        runner["error"] = json!("controlled reporting failure");
        runner["reporting_failure"] = json!({"origin": "runner_host", "diagnostic": "controlled",
            "original_rc": 0, "original_normalized_outcome": "ok", "original_error": null,
            "evidence_retained": true});
        for step in runner["steps"].as_array_mut().unwrap() {
            step["comparison"] = Value::Null;
        }
        runner
    }

    fn event(pid: Option<i32>) -> SandboxDenyEvent {
        SandboxDenyEvent {
            pid,
            process: Some("pw-probe-runner".into()),
            operation: Some("file-write-data".into()),
            path: Some("/attempt".into()),
            raw_line: Some("ordinary denied write before unrelated self-signal".into()),
        }
    }

    fn capture_with(status: &str, events: Vec<SandboxDenyEvent>) -> SandboxLogCapture {
        SandboxLogCapture {
            window: SandboxLogWindow::runner_client_span(0, 1),
            capture_status: status.into(),
            tool_exit_code: 0,
            blocked_reason: None,
            output: crate::utils::JsonOutputCapture::unavailable(
                String::new(),
                crate::utils::OBSERVER_CAPTURE_BYTES,
            ),
            observer: None,
            observed_deny: Some(!events.is_empty()),
            deny_events: Some(events),
            step_denies: None,
            supervision: None,
            processing_cutoff: None,
        }
    }

    /// The independent consumer: every envelope must validate under the
    /// current contract, and the log channel is read through `denials`.
    fn consume(envelopes: &[Value]) -> Vec<Value> {
        use std::io::Write;
        use std::process::{Command, Stdio};
        let mut child = Command::new("/usr/bin/python3")
            .args(["-B", "-c", "import json, sys; sys.path.insert(0, sys.argv[1]); from consumer import validate, denials; es = json.load(sys.stdin); errors = [validate(e) for e in es]; assert not any(errors), errors; print(json.dumps([denials(e) for e in es]))"])
            .arg(Path::new(env!("CARGO_MANIFEST_DIR")).join("../tests/lib"))
            .stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped()).spawn().unwrap();
        child
            .stdin
            .take()
            .unwrap()
            .write_all(&serde_json::to_vec(envelopes).unwrap())
            .unwrap();
        let output = child.wait_with_output().unwrap();
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
        let answers: Vec<Value> = serde_json::from_slice(&output.stdout).unwrap();
        assert_eq!(answers.len(), envelopes.len());
        answers
    }

    const DATA_KEYS: [&str; 7] = [
        "policy_check",
        "runner_client",
        "runner_result",
        "runner_sandbox_diagnostics",
        "sandbox_log_capture",
        "specimen",
        "timeout_ms",
    ];
    const DIAGNOSTIC_KEYS: [&str; 7] = [
        "correlation_status",
        "disposition_integrity",
        "disposition_issues",
        "permission_failures_without_record",
        "process_disposition",
        "stop_reason",
        "termination_cause",
    ];
    const LOG_OWNED_DIAGNOSTICS: [&str; 2] =
        ["correlation_status", "permission_failures_without_record"];

    fn keys(value: &Value) -> Vec<&str> {
        value
            .as_object()
            .unwrap()
            .keys()
            .map(String::as_str)
            .collect()
    }

    /// The envelope with the log channel and its diagnostics removed: what must
    /// stay byte-identical across collector states.
    fn execution_bytes(wire: &Value) -> Vec<u8> {
        let mut value = wire.clone();
        value
            .as_object_mut()
            .unwrap()
            .remove("generated_at_unix_ms");
        value["data"]
            .as_object_mut()
            .unwrap()
            .remove("sandbox_log_capture");
        for key in LOG_OWNED_DIAGNOSTICS {
            assert!(
                value["data"]["runner_sandbox_diagnostics"]
                    .as_object_mut()
                    .unwrap()
                    .remove(key)
                    .is_some()
            );
        }
        serde_json::to_vec(&value).unwrap()
    }

    #[test]
    fn collector_states_preserve_the_serialized_execution_half() {
        // Independent native observations with two indistinguishable candidates
        // and one permission failure that has no matching captured path.
        let request = json!({"probe_plan": [
            {"step_id": "a", "attempt": {"kind": "file", "action": "open_write", "target": "/attempt"}},
            {"step_id": "b", "attempt": {"kind": "file", "action": "open_write", "target": "/attempt"}},
            {"step_id": "silent", "attempt": {"kind": "file", "action": "open_write", "target": "/silent"}}
        ]});
        let steps = vec![
            step("a", "open_write", "/attempt", "permission_failure"),
            step("b", "open_write", "/attempt", "permission_failure"),
            step("silent", "open_write", "/silent", "permission_failure"),
        ];
        let runner = reply_with("ok", None, steps.clone());
        let failed = reply_with("runner_failed", Some(9), steps.clone());
        let mut no_pid = runner.clone();
        no_pid["pid"] = json!(42); // A matching host/client PID is not authoritative.
        no_pid["runner_subprocess"]
            .as_object_mut()
            .unwrap()
            .remove("pid");
        let fixture: Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/disposition/response14/a1_expected.json"
        ))
        .unwrap();
        let no_comparisons = reporting_failed(runner.clone());
        let cases = [
            (Some(runner), 0, "clean_exit", Value::Null, true),
            (
                Some(failed),
                1,
                "signaled",
                json!("host_sentinel_deadline"),
                true,
            ),
            (Some(no_pid), 0, "no_worker", Value::Null, true),
            (
                Some(fixture["data"]["runner_result"].clone()),
                1,
                "signaled",
                json!("host_sentinel_deadline"),
                false,
            ),
            (Some(no_comparisons), 1, "clean_exit", Value::Null, false),
            (None, 1, "no_worker", Value::Null, false),
        ];
        for (runner, expected_exit, disposition, cause, permission_steps) in cases {
            let mut baseline = None;
            for state in [
                "events",
                "empty",
                "unrelated",
                "blocked",
                "error",
                "capture_error",
                "parse_error",
                "invalid_reply",
                "window_mismatch",
                "invalid_window",
                "requested_unavailable",
                "timeout",
                "overflow",
                "disabled",
            ] {
                let execution = complete_execution(execution_data(runner.clone()));
                let client = serde_json::to_value(&execution.data.runner_client).unwrap();
                let pid = worker_pid(runner.as_ref());
                let disabled = state == "disabled";
                let mut invoked = false;
                let (result, data, exit_code) = attach_sandbox_logs(
                    execution,
                    &request,
                    disabled,
                    |actual_pid, name, window| {
                        invoked = true;
                        assert_eq!(Some(actual_pid), pid.map(i64::from));
                        assert_eq!(name, "pw-probe-runner");
                        assert_eq!(
                            (window.started_at_unix_ms, window.ended_at_unix_ms),
                            (1_000, 2_500)
                        );
                        if state == "requested_unavailable" {
                            return Err("controlled collector launch failure".into());
                        }
                        let status = match state {
                            "events" | "empty" | "unrelated" => "captured",
                            other => other,
                        };
                        let events = match state {
                            "empty" => vec![],
                            "unrelated" => vec![event(Some(99))],
                            // Every failed capture deliberately retains a matching
                            // diagnostic event. Status, not event presence, gates it.
                            _ => vec![event(Some(99)), event(pid)],
                        };
                        let mut capture = capture_with(status, events);
                        capture.window = window;
                        capture.observer = Some(json!({"data": {"diagnostic": "retained reply"}}));
                        // Reject precomputed/stale associations supplied by a collector.
                        capture.step_denies = Some(match_step_denies(
                            runner
                                .as_ref()
                                .and_then(|r| r["steps"].as_array())
                                .map(Vec::as_slice)
                                .unwrap_or(&[]),
                            request["probe_plan"].as_array().unwrap(),
                            capture.deny_events.as_ref().unwrap(),
                            pid,
                        ));
                        Ok(capture)
                    },
                );
                assert_eq!(invoked, !disabled && pid.is_some(), "{state}");
                assert_eq!(exit_code, expected_exit, "{state}");
                let text = json_contract::render_envelope("run", result, &data).unwrap();
                let wire: Value = serde_json::from_str(&text).unwrap();
                assert_eq!(wire["schema_version"], json_contract::SCHEMA_VERSION);
                assert_eq!(wire["result"]["exit_code"], expected_exit, "{state}");
                assert_eq!(wire["result"]["ok"], expected_exit == 0, "{state}");
                assert_eq!(
                    wire["data"]["runner_result"],
                    runner.clone().unwrap_or(Value::Null),
                    "{state}"
                );
                assert_eq!(wire["data"]["runner_client"], client, "{state}");
                assert_eq!(
                    keys(&wire["data"]),
                    DATA_KEYS,
                    "internal ownership structs must not change the data wire shape",
                );
                assert!(wire["data"].get("error").is_none());
                let diag = &wire["data"]["runner_sandbox_diagnostics"];
                assert_eq!(
                    keys(diag),
                    DIAGNOSTIC_KEYS,
                    "internal ownership structs must not change the diagnostics wire shape",
                );
                assert_eq!(diag["process_disposition"], disposition, "{state}");
                assert_eq!(diag["termination_cause"], cause, "{state}");
                let cap = &wire["data"]["sandbox_log_capture"];
                if disabled || pid.is_none() {
                    assert!(cap.is_null());
                    assert_eq!(diag["correlation_status"], "not_attempted");
                    assert!(diag["permission_failures_without_record"].is_null());
                } else if matches!(state, "events" | "empty" | "unrelated") {
                    assert_eq!(cap["capture_status"], "captured");
                    assert_eq!(
                        diag["correlation_status"],
                        if state == "events" {
                            "pid_match"
                        } else {
                            "no_match"
                        }
                    );
                    if permission_steps {
                        assert_eq!(
                            diag["permission_failures_without_record"],
                            if state == "events" {
                                json!(["silent"])
                            } else {
                                json!(["a", "b", "silent"])
                            }
                        );
                        if state == "events" {
                            assert_eq!(cap["step_denies"].as_array().unwrap().len(), 1);
                            assert_eq!(cap["step_denies"][0]["event_index"], 1);
                            assert_eq!(
                                cap["step_denies"][0]["candidate_step_ids"],
                                json!(["a", "b"])
                            );
                            assert_eq!(cap["step_denies"][0]["association"], "ambiguous");
                        } else {
                            assert_eq!(cap["step_denies"], json!([]));
                        }
                    } else {
                        // Classified steps yield an empty list; withheld
                        // comparisons yield null, never an invented list.
                        let classified = runner.as_ref().map_or(false, |r| {
                            r["steps"].as_array().map_or(false, |steps| {
                                steps
                                    .iter()
                                    .any(|s| s.pointer("/comparison/observation").is_some())
                            })
                        });
                        assert_eq!(
                            diag["permission_failures_without_record"],
                            if classified { json!([]) } else { Value::Null },
                            "{state}"
                        );
                    }
                } else {
                    assert_eq!(cap["capture_status"], state);
                    assert_eq!(diag["correlation_status"], "unavailable");
                    assert!(cap["step_denies"].is_null());
                    assert!(diag["permission_failures_without_record"].is_null());
                    if state != "requested_unavailable" {
                        assert_eq!(cap["deny_events"][1]["pid"], pid.unwrap());
                        assert_eq!(cap["observer"]["data"]["diagnostic"], "retained reply");
                    }
                }
                // Remove only the two log-owned diagnostic fields and the log
                // subtree. Everything else must be byte-identical across states.
                let bytes = execution_bytes(&wire);
                if let Some(baseline) = &baseline {
                    assert_eq!(&bytes, baseline, "execution changed under {state}");
                } else {
                    baseline = Some(bytes);
                }
            }
        }
    }

    #[test]
    fn real_subprocess_failures_preserve_execution_and_withhold_associations() {
        use crate::log_capture::{self, Boundary, LogTimeout, TimeoutSource};
        let native: Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/disposition/response14/a1_expected.json"
        ))
        .unwrap();
        let runner = native["data"]["runner_result"].clone();
        let mut baseline = None;
        for (script, expected) in [
            ("import time; time.sleep(60)", "timeout"),
            ("import os; os.write(1,b'x'*33554433)", "overflow"),
            ("import os; os.write(2,b'e'*131073)", "overflow"),
            ("import sys; sys.exit(7)", "error"),
            (
                "import os,signal; os.kill(os.getpid(),signal.SIGTERM)",
                "error",
            ),
            ("print('{broken')", "parse_error"),
        ] {
            let (result, data, code) = attach_sandbox_logs(
                complete_execution(execution_data(Some(runner.clone()))),
                &json!({"probe_plan":[]}),
                false,
                |pid, process, window| {
                    let mut command = std::process::Command::new("/usr/bin/python3");
                    command.args(["-c", script]);
                    let budget = LogTimeout {
                        milliseconds: if expected == "timeout" { 150 } else { 3000 },
                        source: TimeoutSource::Cli,
                    }
                    .start()
                    .unwrap();
                    let raw = log_capture::capture(&mut command, budget, Boundary::Observer);
                    Ok(crate::sandbox_log::parse_supervised_observer(
                        raw, window, pid, process,
                    ))
                },
            );
            assert_eq!(code, 1);
            let wire: Value = serde_json::from_str(
                &json_contract::render_envelope("run", result, &data).unwrap(),
            )
            .unwrap();
            assert_eq!(wire["data"]["runner_result"], runner);
            let capture = &wire["data"]["sandbox_log_capture"];
            assert_eq!(capture["capture_status"], expected);
            assert_eq!(capture["supervision"]["cleanup"]["outcome"], "group_absent");
            assert!(capture["step_denies"].is_null());
            let diag = &wire["data"]["runner_sandbox_diagnostics"];
            assert_eq!(diag["correlation_status"], "unavailable");
            assert!(diag["permission_failures_without_record"].is_null());
            let bytes = execution_bytes(&wire);
            if let Some(baseline) = &baseline {
                assert_eq!(&bytes, baseline, "{expected}");
            } else {
                baseline = Some(bytes);
            }
        }
    }

    #[test]
    fn retained_events_without_worker_identity_never_acquire_associations() {
        let request = json!({"probe_plan": [{"step_id": "s", "attempt": {
            "kind": "file", "action": "open_write", "target": "/attempt"}}]});
        for sub in [
            Value::Null,
            json!({"pid": 0}),
            json!({"pid": -1}),
            json!({"pid": 4_294_967_338_u64}),
        ] {
            let runner = json!({"pid": 42, "runner_subprocess": sub, "steps": [{"step_id": "s",
                "comparison": {"observation": "permission_failure"}}]});
            let mut capture = capture_with("captured", vec![event(Some(42))]);
            capture.step_denies = Some(match_step_denies(
                runner["steps"].as_array().unwrap(),
                request["probe_plan"].as_array().unwrap(),
                capture.deny_events.as_ref().unwrap(),
                Some(42),
            ));
            assert_eq!(capture.step_denies.as_ref().unwrap().len(), 1);
            let mut capture = Some(capture);
            let diagnostics =
                finish_sandbox_log_capture(Some(&runner), &request, false, &mut capture);
            assert!(capture.as_ref().unwrap().step_denies.is_none());
            assert_eq!(
                capture
                    .as_ref()
                    .unwrap()
                    .deny_events
                    .as_ref()
                    .unwrap()
                    .len(),
                1
            );
            assert_eq!(diagnostics.correlation_status, "not_attempted");
            assert!(diagnostics.permission_failures_without_record.is_none());
        }
    }

    #[test]
    fn no_match_is_distinguished_by_unrecorded_permission_failures() {
        fn plan(ids: &[&str]) -> Value {
            json!({"probe_plan": ids.iter().map(|id| json!({"step_id": id, "attempt": {
                "kind": "file", "action": "open_write", "target": format!("/{id}")}})).collect::<Vec<_>>()})
        }
        fn denied(path: &str) -> SandboxDenyEvent {
            let mut e = event(Some(42));
            e.path = Some(path.into());
            e
        }
        let ids = ["recorded", "silent", "fine"];
        let request = plan(&ids);
        let runner = reply_with(
            "ok",
            None,
            vec![
                step("recorded", "open_write", "/recorded", "permission_failure"),
                step("silent", "open_write", "/silent", "permission_failure"),
                step("fine", "open_write", "/fine", "succeeded"),
            ],
        );
        // One denial recorded, one not: only the silent one is listed.
        let mut cap = Some(capture_with("captured", vec![denied("/recorded")]));
        let diag = finish_sandbox_log_capture(Some(&runner), &request, false, &mut cap);
        assert_eq!(diag.correlation_status, "pid_match");
        assert_eq!(
            diag.permission_failures_without_record,
            Some(vec!["silent".to_string()])
        );
        // No record at all: no_match names the denials the attempts reported.
        let mut cap = Some(capture_with("captured", vec![event(Some(99))]));
        let diag = finish_sandbox_log_capture(Some(&runner), &request, false, &mut cap);
        assert_eq!(diag.correlation_status, "no_match");
        assert_eq!(
            diag.permission_failures_without_record,
            Some(vec!["recorded".to_string(), "silent".to_string()])
        );
        let wire = serde_json::to_value(&diag).unwrap();
        assert_eq!(
            wire["permission_failures_without_record"],
            json!(["recorded", "silent"])
        );
        // Nothing permission-shaped: the list is empty, not null.
        let clean = reply_with(
            "ok",
            None,
            vec![
                step("fine", "open_write", "/fine", "succeeded"),
                step("other", "open_write", "/other", "other_failure"),
            ],
        );
        let mut cap = Some(capture_with("captured", vec![]));
        let diag = finish_sandbox_log_capture(Some(&clean), &request, false, &mut cap);
        assert_eq!(diag.permission_failures_without_record, Some(vec![]));
        // Comparisons withheld by a reporting failure, uncorrelated or disabled:
        // null, never an invented list.
        let withheld = reporting_failed(runner.clone());
        let mut cap = Some(capture_with("captured", vec![]));
        let diag = finish_sandbox_log_capture(Some(&withheld), &request, false, &mut cap);
        assert_eq!(diag.correlation_status, "no_match");
        assert_eq!(diag.permission_failures_without_record, None);
        for (status, disabled) in [
            ("error", false),
            ("window_mismatch", false),
            ("captured", true),
        ] {
            let mut cap = Some(capture_with(status, vec![]));
            let diag = finish_sandbox_log_capture(Some(&runner), &request, disabled, &mut cap);
            assert_ne!(diag.correlation_status, "no_match", "{status}");
            assert_eq!(diag.permission_failures_without_record, None, "{status}");
        }
        let diag = finish_sandbox_log_capture(Some(&runner), &request, false, &mut None);
        assert_eq!(diag.correlation_status, "unavailable");
        assert_eq!(diag.permission_failures_without_record, None);
    }

    #[test]
    fn argument_errors_are_reported_before_any_runner_or_specimen_work() {
        for value in [
            "0",
            "-1",
            "+1",
            "1.5",
            "unlimited",
            "18446744073709551615",
            "18446744073709551616",
        ] {
            for disabled in [false, true] {
                let mut args = vec!["--log-timeout-ms".into(), value.into()];
                if disabled {
                    args.push("--no-log-capture".into());
                }
                match parse_arguments(&args) {
                    Arguments::Error(None, error) => assert!(
                        error.contains("invalid value for --log-timeout-ms"),
                        "{error}"
                    ),
                    _ => panic!("{value}: accepted"),
                }
            }
        }
        match parse_arguments(&[
            "--log-timeout-ms".into(),
            "1".into(),
            "--no-log-capture".into(),
        ]) {
            Arguments::Run(parsed) => {
                assert!(parsed.no_log_capture);
                assert!(parsed.request_path.is_none());
                assert_eq!(parsed.timeout_ms, DEFAULT_TIMEOUT_MS);
            }
            _ => panic!("valid finite timeout must pass option admission"),
        }
        match parse_arguments(&["--log-timeout-ms".into()]) {
            Arguments::Error(None, error) => assert!(error.contains("missing value")),
            _ => panic!("missing value accepted"),
        }
        for (flag, value) in [
            ("--timeout-ms", "invalid"),
            ("--log-timeout-ms", "0"),
            ("--runner-mode", "invalid"),
        ] {
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
            ("log_window_pad", crate::sandbox_log::LOG_WINDOW_PAD_SECONDS),
            (
                "controller_output",
                crate::utils::RUNNER_CAPTURE_BYTES as u64,
            ),
            (
                "policy_helper_output",
                crate::utils::HELPER_CAPTURE_BYTES as u64,
            ),
            (
                "log_observer_output",
                crate::utils::OBSERVER_CAPTURE_BYTES as u64,
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

    #[test]
    fn observer_windows_survive_association_serialization_and_consumer_recovery() {
        use crate::sandbox_log::parse_observer_output;
        use std::os::unix::process::ExitStatusExt;
        use std::process::{ExitStatus, Output};

        let window = SandboxLogWindow::runner_client_span(1_000, 2_500);
        let good = json!({"start": window.start, "end": window.end, "last": null});
        let mut replies = vec![("matching", good.clone(), "captured")];
        for (name, field, value) in [
            ("wrong_start", "start", json!("1970-01-01 00:00:02+0000")),
            ("wrong_end", "end", json!("1970-01-01 00:00:04+0000")),
            ("trailing", "last", json!("10s")),
            ("null_start", "start", Value::Null),
        ] {
            let mut reply = good.clone();
            reply[field] = value;
            replies.push((name, reply, "window_mismatch"));
        }
        for field in ["start", "end"] {
            let mut reply = good.clone();
            reply.as_object_mut().unwrap().remove(field);
            replies.push((field, reply, "window_mismatch"));
        }
        replies.push(("missing_bounds", json!({"last": "10s"}), "window_mismatch"));
        replies.push(("clock_rollback", Value::Null, "invalid_window"));

        let request = json!({"probe_plan": [{"step_id": "s", "attempt": {
            "kind": "file", "action": "open_write", "target": "/attempt"}}]});
        let events = json!([{"pid": 42, "process": "pw-probe-runner", "operation": "file-write-data",
            "path": "/attempt", "raw_line": "retained observer evidence"}]);
        let mut envelopes = Vec::new();
        for signaled in [false, true] {
            let outcome = if signaled { "runner_failed" } else { "ok" };
            let runner = reply_with(
                outcome,
                signaled.then_some(9),
                vec![step("s", "open_write", "/attempt", "permission_failure")],
            );
            for (name, bounds, expected_status) in &replies {
                let mut observer = json!({"data": bounds});
                let mut capture = Some(if *expected_status == "invalid_window" {
                    capture_sandbox_logs(
                        42,
                        "pw-probe-runner",
                        SandboxLogWindow::runner_client_span(5_000, 4_000),
                    )
                    .unwrap()
                } else {
                    observer["data"]["observed_deny"] = json!(true);
                    observer["data"]["deny_events"] = events.clone();
                    let out = Output {
                        status: ExitStatus::from_raw(0),
                        stdout: serde_json::to_vec(&observer).unwrap(),
                        stderr: vec![],
                    };
                    parse_observer_output(&out, window.clone())
                });
                let execution = complete_execution(execution_data(Some(runner.clone())));
                let (result, data, exit_code) =
                    attach_sandbox_logs(execution, &request, false, |_, _, _| {
                        Ok(capture.take().unwrap())
                    });
                assert_eq!(exit_code, i32::from(signaled));
                let text = json_contract::render_envelope("run", result, &data).unwrap();
                let wire: Value = serde_json::from_str(&text).unwrap();
                assert_eq!(wire["result"]["ok"], !signaled);
                assert_eq!(wire["result"]["normalized_outcome"], outcome);
                assert_eq!(wire["data"]["runner_result"], runner);
                let cap = &wire["data"]["sandbox_log_capture"];
                let diag = &wire["data"]["runner_sandbox_diagnostics"];
                assert_eq!(cap["capture_status"], *expected_status, "{name}");
                if *expected_status == "invalid_window" {
                    assert!(cap["observer"].is_null() && cap["deny_events"].is_null());
                    assert!(cap["window"]["start"].is_null() && cap["window"]["end"].is_null());
                    assert_eq!(cap["window"]["started_at_unix_ms"], 5_000);
                    assert_eq!(cap["window"]["ended_at_unix_ms"], 4_000);
                } else {
                    assert_eq!(cap["observer"], observer);
                    assert_eq!(cap["deny_events"], events);
                    assert_eq!(cap["observed_deny"], true);
                }
                if *expected_status == "captured" {
                    assert_eq!(cap["step_denies"][0]["candidate_step_ids"], json!(["s"]));
                    assert_eq!(diag["correlation_status"], "pid_match");
                } else {
                    assert!(
                        cap["step_denies"].is_null(),
                        "{name}: no candidate from unusable interval"
                    );
                    assert_eq!(diag["correlation_status"], "unavailable");
                }
                envelopes.push(wire);
            }
        }
        // The real independent consumer reads serialized production output.
        let answers = consume(&envelopes);
        for (wire, recovered) in envelopes.iter().zip(answers) {
            let cap = &wire["data"]["sandbox_log_capture"];
            let diag = &wire["data"]["runner_sandbox_diagnostics"];
            assert_eq!(recovered["capture"], *cap);
            assert_eq!(recovered["window"], cap["window"]);
            assert_eq!(recovered["events"], cap["deny_events"]);
            assert_eq!(recovered["capture_status"], cap["capture_status"]);
            assert_eq!(recovered["diagnostics"], *diag);
            assert_eq!(recovered["correlation_status"], diag["correlation_status"]);
            if cap["capture_status"] == "captured" {
                assert_eq!(recovered["candidates"][0]["event"], events[0]);
                assert_eq!(
                    recovered["candidates"][0]["candidate_step_ids"],
                    json!(["s"])
                );
            } else {
                assert!(recovered["candidates"].is_null());
                assert_eq!(recovered["association_reporting"], "not_reported");
            }
        }
    }

    #[test]
    fn padded_records_survive_assembly_and_consumer_recovery() {
        use crate::sandbox_log::{observer_argv, parse_observer_output};
        use std::process::Command;

        // Native permission failures and expected event subsets are specified
        // independently of the timestamp-selection fixture and matching code.
        let paths = [
            "/before",
            "/lower-bound",
            "/start-pad",
            "/start-slack",
            "/early",
            "/short-tail",
            "/short-pad",
            "/short-bound",
            "/late",
            "/end-slack",
            "/end-pad",
            "/upper-bound",
            "/after",
        ];
        let plan: Vec<_> = paths
            .iter()
            .map(|path| {
                json!({"step_id": path,
            "attempt": {"kind":"file", "action":"open_read", "target":path}})
            })
            .collect();
        let request = json!({"probe_plan":plan});
        let runner = reply_with(
            "ok",
            None,
            paths
                .iter()
                .map(|path| step(path, "open_read", path, "permission_failure"))
                .collect(),
        );
        let fixture = Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../tests/fixtures/deny_capture/observer.py");
        let mut envelopes = Vec::new();
        for (start, end, expected) in [
            (
                1_999,
                22_001,
                vec![
                    "/lower-bound",
                    "/start-pad",
                    "/start-slack",
                    "/early",
                    "/short-tail",
                    "/short-pad",
                    "/short-bound",
                    "/late",
                    "/end-slack",
                    "/end-pad",
                    "/upper-bound",
                ],
            ),
            (
                1_999,
                2_001,
                vec![
                    "/lower-bound",
                    "/start-pad",
                    "/start-slack",
                    "/early",
                    "/short-tail",
                    "/short-pad",
                    "/short-bound",
                ],
            ),
            (
                13_000,
                23_000,
                vec!["/late", "/end-slack", "/end-pad", "/upper-bound"],
            ),
            (40_000, 50_000, vec![]),
        ] {
            let mut execution = execution_data(Some(runner.clone()));
            let client = execution.runner_client.as_mut().unwrap();
            client.started_at_unix_ms = start;
            client.ended_at_unix_ms = end;
            let (result, data, code) = attach_sandbox_logs(
                complete_execution(execution),
                &request,
                false,
                |pid, process, window| {
                    let argv = observer_argv("observer".into(), pid, process, &window).unwrap();
                    let out = Command::new("/usr/bin/python3")
                        .arg(&fixture)
                        .args(&argv[1..])
                        .output()
                        .unwrap();
                    assert!(
                        out.status.success(),
                        "{}",
                        String::from_utf8_lossy(&out.stderr)
                    );
                    Ok(parse_observer_output(&out, window))
                },
            );
            assert_eq!(code, 0);
            let wire: Value = serde_json::from_str(
                &json_contract::render_envelope("run", result, &data).unwrap(),
            )
            .unwrap();
            assert_eq!(wire["data"]["runner_result"], runner);
            let cap = &wire["data"]["sandbox_log_capture"];
            assert_eq!(cap["capture_status"], "captured");
            assert_eq!(cap["window"]["pad_seconds"], 2);
            let events = cap["deny_events"].as_array().unwrap();
            assert_eq!(
                events
                    .iter()
                    .map(|e| e["path"].as_str().unwrap())
                    .collect::<Vec<_>>(),
                expected
            );
            assert_eq!(cap["observer"]["data"]["deny_events"], cap["deny_events"]);
            let candidates = cap["step_denies"].as_array().unwrap();
            assert_eq!(candidates.len(), expected.len());
            for (index, path) in expected.iter().enumerate() {
                assert_eq!(candidates[index]["event_index"], index);
                assert_eq!(candidates[index]["candidate_step_ids"], json!([path]));
                assert_eq!(candidates[index]["association"], "candidate");
                assert_eq!(candidates[index]["matching_evidence"][0]["path"], *path);
            }
            let diag = &wire["data"]["runner_sandbox_diagnostics"];
            assert_eq!(
                diag["correlation_status"],
                if expected.is_empty() {
                    "no_match"
                } else {
                    "pid_match"
                }
            );
            assert_eq!(
                diag["permission_failures_without_record"],
                json!(
                    paths
                        .iter()
                        .filter(|p| !expected.contains(p))
                        .collect::<Vec<_>>()
                )
            );
            envelopes.push(wire);
        }
        let answers = consume(&envelopes);
        for (wire, recovered) in envelopes.iter().zip(answers) {
            let cap = &wire["data"]["sandbox_log_capture"];
            assert_eq!(recovered["capture"], *cap);
            assert_eq!(recovered["window"], cap["window"]);
            assert_eq!(recovered["events"], cap["deny_events"]);
            assert_eq!(
                recovered["diagnostics"],
                wire["data"]["runner_sandbox_diagnostics"]
            );
            let candidates = recovered["candidates"].as_array().unwrap();
            assert_eq!(
                candidates.len(),
                cap["step_denies"].as_array().unwrap().len()
            );
            for (candidate, original) in candidates
                .iter()
                .zip(cap["step_denies"].as_array().unwrap())
            {
                assert_eq!(
                    candidate["candidate_step_ids"],
                    original["candidate_step_ids"]
                );
                assert_eq!(
                    candidate["matching_evidence"],
                    original["matching_evidence"]
                );
                assert_eq!(
                    candidate["event"],
                    cap["deny_events"][original["event_index"].as_u64().unwrap() as usize]
                );
            }
        }
    }

    #[test]
    fn incomplete_attempt_retains_independent_prediction_and_event_beside_the_record() {
        let runner = reply_with(
            "runner_failed",
            Some(9),
            vec![incomplete_step("s", "open_write", "/attempt")],
        );
        let before = runner.clone();
        let plan = [json!({"step_id": "s", "attempt": {
            "kind": "file", "action": "open_write", "target": "/attempt"}})];
        let cap = capture_with("captured", vec![event(Some(42))]);
        let associations = match_step_denies(
            runner["steps"].as_array().unwrap(),
            &plan,
            cap.deny_events.as_ref().unwrap(),
            Some(42),
        );
        assert_eq!(associations.len(), 1);
        assert_eq!(associations[0].event_index, 0);
        assert_eq!(associations[0].candidate_step_ids, ["s"]);
        assert_eq!(associations[0].association, "candidate");
        let diag = diagnostics_with_logs(Some(&runner), false, Some(&cap));
        // The denial does not explain the signal; the record's witnessed host
        // cleanup does, and the incomplete slot is a lifecycle fact beside it.
        assert_eq!(diag.execution.process_disposition, "signaled");
        assert_eq!(
            diag.execution.termination_cause,
            Some("host_sentinel_deadline")
        );
        assert_eq!(diag.execution.disposition_integrity, Some("valid"));
        assert_eq!(diag.logs.correlation_status, "pid_match");
        assert_eq!(runner, before);
        assert_eq!(cap.deny_events.as_ref().unwrap().len(), 1);
        assert_eq!(
            runner["steps"][0]["comparison"]["limitations"],
            json!(["attempt:lifecycle_unresolved"])
        );
    }

    #[test]
    fn ordinary_denial_and_unrelated_signal_remain_separate_observations() {
        let runner = worker("runner_failed", Some(9));
        let original = runner.clone();
        let cap = capture_with("captured", vec![event(Some(99)), event(Some(42))]);
        let diag = diagnostics_with_logs(Some(&runner), false, Some(&cap));
        assert_eq!(diag.execution.process_disposition, "signaled");
        assert_eq!(
            diag.execution.termination_cause,
            Some("host_sentinel_deadline")
        );
        assert_eq!(diag.logs.correlation_status, "pid_match");
        assert_eq!(cap.deny_events.as_ref().unwrap().len(), 2);
        assert_eq!(runner, original);
    }

    #[test]
    fn capture_conditions_do_not_change_execution_status_or_cause() {
        let runner = worker("runner_failed", Some(9));
        let original = runner.clone();
        for (disabled, status, expected_correlation) in [
            (true, "captured", "not_attempted"),
            (false, "blocked", "unavailable"),
            (false, "error", "unavailable"),
            (false, "requested_unavailable", "unavailable"),
            (false, "captured", "no_match"),
        ] {
            let cap = capture_with(status, vec![]);
            let diag = diagnostics_with_logs(Some(&runner), disabled, Some(&cap));
            assert_eq!(diag.logs.correlation_status, expected_correlation);
            assert_eq!(diag.execution.process_disposition, "signaled");
            assert_eq!(
                diag.execution.termination_cause,
                Some("host_sentinel_deadline")
            );
            assert_eq!(runner, original);
        }
    }

    #[test]
    fn successful_run_keeps_correlations_without_a_termination_cause() {
        let runner = worker("ok", None);
        let cap = capture_with("captured", vec![event(Some(42))]);
        let diag = diagnostics_with_logs(Some(&runner), false, Some(&cap));
        assert_eq!(diag.execution.process_disposition, "clean_exit");
        assert_eq!(diag.execution.stop_reason.as_deref(), Some("done"));
        assert_eq!(diag.logs.correlation_status, "pid_match");
        assert_eq!(diag.execution.termination_cause, None);
        assert_eq!(runner["normalized_outcome"], "ok");
    }

    #[test]
    fn no_worker_never_uses_host_or_client_pid() {
        for outcome in ["bad_request", "xpc_error", "worker_spawn_failed"] {
            let runner =
                json!({"pid": 42, "normalized_outcome": outcome, "runner_subprocess": null});
            let cap = capture_with("captured", vec![event(Some(42))]);
            let diag = diagnostics_with_logs(Some(&runner), false, Some(&cap));
            assert_eq!(diag.execution.process_disposition, "no_worker");
            assert_eq!(diag.execution.disposition_integrity, None);
            assert_eq!(diag.logs.correlation_status, "not_attempted");
            assert!(diag.logs.permission_failures_without_record.is_none());
        }
    }

    #[test]
    fn missing_mismatched_pid_and_unavailable_events_never_supply_a_correlation() {
        let runner = worker("runner_failed", Some(9));
        for (status, expected) in [
            ("captured", "no_match"),
            ("blocked", "unavailable"),
            ("parse_error", "unavailable"),
        ] {
            let cap = capture_with(status, vec![event(None), event(Some(99))]);
            let diag = diagnostics_with_logs(Some(&runner), false, Some(&cap));
            assert_eq!(diag.logs.correlation_status, expected, "{status}");
        }
        let mut cap = capture_with("captured", vec![]);
        cap.deny_events = None;
        let diag = diagnostics_with_logs(Some(&runner), false, Some(&cap));
        assert_eq!(diag.logs.correlation_status, "unavailable");
        let diag = diagnostics_with_logs(Some(&runner), false, None);
        assert_eq!(diag.logs.correlation_status, "unavailable");
    }

    #[test]
    fn unconfirmed_reap_does_not_manufacture_clean_disposition_from_status_storage() {
        let mut runner = worker("runner_failed", None);
        runner["runner_subprocess"]["reaped"] = json!(false);
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        // The record claims an exit status its reap evidence does not support.
        assert_eq!(diag.execution.process_disposition, "withheld");
        assert_eq!(diag.execution.disposition_integrity, Some("invalid"));
        assert_eq!(diag.execution.termination_cause, Some("unknown"));
    }

    #[test]
    fn conflicting_status_representation_is_not_silently_resolved() {
        let mut runner = worker("runner_failed", Some(9));
        // One final reap represented as both a clean exit and a signal.
        runner["runner_subprocess"]["exit_code"] = json!(0);
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert!(
            !matches!(
                diag.execution.process_disposition,
                "signaled" | "clean_exit"
            ),
            "exit_code 0 beside term_signal 9 is an invalid status pair; \
             an unqualified disposition ({}) resolves it silently",
            diag.execution.process_disposition
        );
        assert_eq!(diag.execution.termination_cause, Some("unknown"));
        assert_eq!(diag.logs.correlation_status, "not_attempted");
    }

    #[test]
    fn conflicting_status_reports_the_status_rule() {
        // The host itself recorded the conflict under rule D1.
        let mut runner = worker("runner_failed", Some(9));
        runner["runner_subprocess"]["exit_code"] = json!(0);
        runner["runner_subprocess"]["disposition"]["questions"]["final_status"] =
            json!({"state": "conflicting", "issue": 0});
        runner["runner_subprocess"]["disposition"]["issues"] = json!([{
            "kind": "conflict", "rule": "D1", "question": "final_status",
            "observations": ["exit_code", "term_signal"],
            "detail": "one successful reap represented as both an exit status and a signal"}]);
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert_eq!(diag.execution.process_disposition, "conflicting");
        assert_eq!(diag.execution.disposition_integrity, Some("valid"));
        assert_eq!(diag.execution.termination_cause, Some("unknown"));
        let wire = serde_json::to_value(&diag).unwrap();
        let issues = wire["disposition_issues"].as_array().cloned().unwrap();
        assert!(
            issues.iter().any(|i| i["rule"] == json!("D1")),
            "issue must name the status rule D1"
        );
    }

    // The runner reply carries the record the contract names; the controller
    // projects the witnessed host cleanup instead of ignoring the object.
    fn disposition_reply(cause_trigger: &str, reaped: bool) -> Value {
        let mut runner = worker("runner_timeout", Some(9));
        let sub = &mut runner["runner_subprocess"];
        sub["reaped"] = json!(reaped);
        sub["poll_stop_reason"] = json!("sentinel_deadline");
        sub["exit_requested"] = json!(true);
        sub["termination_request"] = json!({"signal": 9, "rc": 0});
        sub["cleanup_trigger"] = json!(cause_trigger);
        sub["grace_end"] = json!("exhausted");
        sub["collection_basis"] = json!("after_confirmed_reap");
        sub["partial_steps"] = json!(false);
        sub["disposition"] = json!({
            "questions": {
                "final_status": {"state": "supported", "answer": "signal", "value": 9, "basis": ["reaped", "term_signal"]},
                "stop_reason": {"state": "supported", "answer": "sentinel_deadline", "basis": ["poll_stop_reason"]},
                "cleanup_trigger": {"state": "supported", "answer": cause_trigger, "basis": ["cleanup_trigger", "exit_requested"]},
                "grace_end": {"state": "supported", "answer": "exhausted", "basis": ["grace_end", "exit_requested"]},
                "kill_request_and_result": {"state": "supported", "answer": "requested",
                    "value": {"signal": 9, "rc": 0}, "basis": ["termination_request"]},
                "collection_basis": {"state": "supported", "answer": "after_confirmed_reap", "basis": ["collection_basis"]},
                "progress_association": {"state": "inapplicable", "reason": "no_progress_word"}
            },
            "steps": [], "issues": []
        });
        runner["steps"] = json!([]);
        runner
    }

    #[test]
    fn disposition_record_projects_witnessed_host_cleanup_cause() {
        let runner = disposition_reply("deadline_expiry", true);
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert_eq!(
            diag.execution.termination_cause,
            Some("host_sentinel_deadline"),
            "the controller ignores the carried disposition record and reports a generic cause"
        );
        assert_eq!(diag.execution.process_disposition, "signaled");
        let wire = serde_json::to_value(&diag).unwrap();
        assert_eq!(wire["disposition_integrity"], json!("valid"));
        assert_eq!(wire["stop_reason"], json!("sentinel_deadline"));
    }

    #[test]
    fn record_contradicting_its_basis_is_withheld() {
        // A supported signal claim while the reply says the worker was never reaped.
        let runner = disposition_reply("deadline_expiry", false);
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert_eq!(
            diag.execution.process_disposition, "withheld",
            "an assembled claim that contradicts its basis must be withheld, not re-derived"
        );
        assert_eq!(diag.execution.termination_cause, Some("unknown"));
        let wire = serde_json::to_value(&diag).unwrap();
        assert_eq!(wire["disposition_integrity"], json!("invalid"));
        assert!(
            wire["disposition_issues"]
                .as_array()
                .map_or(false, |v| !v.is_empty())
        );
    }

    #[test]
    fn unrecognized_future_trigger_never_projects_a_cause() {
        let runner = disposition_reply("host_future_trigger", true);
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert_eq!(diag.execution.termination_cause, Some("unknown"));
        assert_ne!(diag.execution.process_disposition, "clean_exit");
    }

    #[test]
    fn reply_without_a_disposition_record_is_withheld() {
        for record in [Value::Null, json!(null)] {
            let mut runner = disposition_reply("deadline_expiry", true);
            runner["runner_subprocess"]["disposition"] = record;
            let diag = diagnostics_with_logs(Some(&runner), true, None);
            assert_eq!(diag.execution.process_disposition, "withheld");
            assert_eq!(diag.execution.disposition_integrity, Some("invalid"));
            assert_eq!(diag.execution.termination_cause, Some("unknown"));
            assert_eq!(diag.execution.stop_reason, None);
            assert_eq!(
                diag.execution.disposition_issues[0]["kind"],
                "missing_record"
            );
        }
        let mut runner = disposition_reply("deadline_expiry", true);
        runner["runner_subprocess"]
            .as_object_mut()
            .unwrap()
            .remove("disposition");
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert_eq!(diag.execution.process_disposition, "withheld");
    }

    #[test]
    fn disposition_cannot_hide_a_second_status_representation() {
        let mut runner = disposition_reply("deadline_expiry", true);
        runner["runner_subprocess"]["exit_code"] = json!(0);
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert_eq!(diag.execution.process_disposition, "withheld");
        assert_eq!(diag.execution.termination_cause, Some("unknown"));
    }

    #[test]
    fn disposition_request_value_must_match_the_observed_request() {
        for (field, value) in [
            ("rc", json!(-1)),
            ("signal", json!(15)),
            ("errno", json!(1)),
        ] {
            let mut runner = disposition_reply("deadline_expiry", true);
            runner["runner_subprocess"]["termination_request"][field] = value;
            let diag = diagnostics_with_logs(Some(&runner), true, None);
            assert_eq!(
                diag.execution.process_disposition, "withheld",
                "mismatched {field}"
            );
            assert_eq!(diag.execution.termination_cause, Some("unknown"));
        }
    }

    #[test]
    fn disposition_requires_typed_sufficient_resolving_basis() {
        for basis in [
            json!([17]),
            json!([null]),
            json!([{}]),
            json!(["wait_errors"]),
            json!(["exit_requested"]),
            json!(["term_signal"]),
        ] {
            let mut runner = disposition_reply("deadline_expiry", true);
            runner["runner_subprocess"]["disposition"]["questions"]["final_status"]["basis"] =
                basis.clone();
            let diag = diagnostics_with_logs(Some(&runner), true, None);
            assert_eq!(
                diag.execution.process_disposition, "withheld",
                "basis {basis}"
            );
        }
    }

    #[test]
    fn unknown_stop_is_preserved_without_becoming_a_known_projection() {
        let mut runner = disposition_reply("deadline_expiry", true);
        runner["runner_subprocess"]["poll_stop_reason"] = json!("future_stop");
        runner["runner_subprocess"]["disposition"]["questions"]["stop_reason"]["answer"] =
            json!("future_stop");
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert_eq!(diag.execution.stop_reason, None);
        assert_eq!(diag.execution.process_disposition, "signaled");
        assert_eq!(
            runner["runner_subprocess"]["poll_stop_reason"],
            json!("future_stop")
        );
    }

    #[test]
    fn disposition_checks_step_proofs_issues_and_projection_copies() {
        let envelope: Value = serde_json::from_str(include_str!(
            "../../tests/fixtures/disposition/response14/a1_expected.json"
        ))
        .unwrap();
        let base = &envelope["data"]["runner_result"];
        let diag = diagnostics_with_logs(Some(base), true, None);
        assert_eq!(
            diag.execution.disposition_integrity,
            Some("valid"),
            "{:?}",
            diag.execution.disposition_issues
        );
        // The degraded-reply contract intentionally withholds comparisons while
        // retaining independently usable lifecycle observations.
        let mut degraded = base.clone();
        degraded["normalized_outcome"] = json!("runner_reporting_failed");
        degraded["reporting_failure"] = json!({"origin":"runner_host", "evidence_retained":true});
        for step in degraded["steps"].as_array_mut().unwrap() {
            step["comparison"] = Value::Null;
        }
        let diag = diagnostics_with_logs(Some(&degraded), true, None);
        assert_eq!(diag.execution.disposition_integrity, Some("valid"));
        assert_eq!(
            diag.execution.termination_cause,
            Some("host_sentinel_deadline")
        );
        let mutations = [
            (
                "/runner_subprocess/disposition/questions/progress_association/value",
                json!(1),
            ),
            ("/runner_subprocess/partial_steps", json!(false)),
            (
                "/steps/0/attempt/lifecycle/boundary/answer",
                json!("not_reached"),
            ),
            ("/steps/0/attempt/lifecycle/summary", json!("not_reached")),
            ("/steps/0/attempt/result_source", json!("worker")),
            ("/steps/0/comparison/limitations", json!([])),
            (
                "/runner_subprocess/disposition/steps/0/questions/step_boundary_reached/answer",
                json!("not_reached"),
            ),
            (
                "/runner_subprocess/disposition/steps/1/questions/step_boundary_reached/answer",
                json!("reached"),
            ),
        ];
        for (path, value) in mutations {
            let mut runner = base.clone();
            *runner.pointer_mut(path).expect(path) = value;
            let diag = diagnostics_with_logs(Some(&runner), true, None);
            assert_eq!(
                diag.execution.disposition_integrity,
                Some("invalid"),
                "{path}"
            );
        }
        let mut runner = base.clone();
        let issue = json!({"kind":"conflict", "rule":"D5", "question":"step_boundary_reached", "step_index":0,
            "observations":["progress","slot","collection_basis"], "detail":"fabricated conflict"});
        runner["runner_subprocess"]["disposition"]["issues"] = json!([issue]);
        let fake = json!({"state":"conflicting", "issue":0});
        runner["runner_subprocess"]["disposition"]["steps"][0]["questions"]["step_boundary_reached"] =
            fake.clone();
        runner["steps"][0]["attempt"]["lifecycle"]["boundary"] = fake;
        runner["steps"][0]["attempt"]["lifecycle"]["summary"] = json!("conflicting");
        runner["steps"][0]["comparison"]["limitations"] = json!(["attempt:lifecycle_conflicting"]);
        let diag = diagnostics_with_logs(Some(&runner), true, None);
        assert_eq!(diag.execution.disposition_integrity, Some("invalid"));
    }

    #[test]
    fn malformed_disposition_questions_are_withheld_without_panicking() {
        for name in DISPOSITION_RUN_QUESTIONS {
            let mut runner = disposition_reply("deadline_expiry", true);
            runner["runner_subprocess"]["disposition"]["questions"]
                .as_object_mut()
                .unwrap()
                .remove(*name);
            let diag = diagnostics_with_logs(Some(&runner), true, None);
            assert_eq!(
                diag.execution.process_disposition, "withheld",
                "missing {name}"
            );
        }
        for state in [json!("future_state"), json!(17), Value::Null] {
            let mut runner = disposition_reply("deadline_expiry", true);
            runner["runner_subprocess"]["disposition"]["questions"]["stop_reason"]["state"] = state;
            let diag = diagnostics_with_logs(Some(&runner), true, None);
            assert_eq!(diag.execution.process_disposition, "withheld");
        }
    }

    // ---- D5: the reply version gate ----------------------------------------

    #[test]
    fn reply_versions_are_gated_exactly() {
        let current = i64::from(json_contract::RESPONSE_SCHEMA_VERSION);
        assert!(matches!(
            reply_version(&json!({"schema_version": current})),
            ReplyVersion::Supported
        ));
        for other in [current - 1, current + 1, 1, 0, -1] {
            match reply_version(&json!({"schema_version": other})) {
                ReplyVersion::Unsupported(version) => assert_eq!(version.as_i64(), Some(other)),
                _ => panic!("{other} was not refused as unsupported"),
            }
        }
        match reply_version(&json!({"schema_version": u64::MAX})) {
            ReplyVersion::Unsupported(version) => assert_eq!(version.as_u64(), Some(u64::MAX)),
            _ => panic!("a large integer version is unsupported, not malformed"),
        }
        for malformed in [
            json!({}),
            json!({"schema_version": null}),
            json!({"schema_version": "13"}),
            json!({"schema_version": 13.0}),
            json!({"schema_version": [13]}),
        ] {
            match reply_version(&malformed) {
                ReplyVersion::Malformed(error) => {
                    assert!(error.contains("schema_version"), "{malformed}: {error}")
                }
                _ => panic!("{malformed} was not refused as malformed"),
            }
        }
    }

    #[test]
    fn delivery_failure_takes_precedence_and_retains_the_reply_unread() {
        let current = i64::from(json_contract::RESPONSE_SCHEMA_VERSION);
        let reply = worker("ok", None);
        let unsupported = json!({"schema_version": current + 1, "normalized_outcome": "ok"});
        let mut broken = client_run(Some(&reply));
        broken.request_delivery = Some(RequestDelivery {
            bytes_written: 1,
            error: Some("request delivery failed after 1 bytes: Broken pipe (os error 32)".into()),
        });
        let intact = client_run(Some(&reply));
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
                assert!(
                    error.contains(&format!("response schema {}", current + 1)),
                    "{error}"
                );
                assert!(error.contains(&format!("reads only {current}")), "{error}");
            }
            _ => panic!("unsupported version admitted"),
        }
        match admit_reply(&intact, Some(&json!({"schema_version": "x"}))) {
            ReplyAdmission::Refused { outcome, .. } => {
                assert_eq!(outcome, "malformed_runner_response")
            }
            _ => panic!("malformed version admitted"),
        }
        // The refusal envelope retains the capture and the reply unchanged, with
        // no policy check, no log channel and no diagnostics.
        let data = execution_only(specimen(), Some(7), Some(broken), Some(unsupported.clone()));
        let text = json_contract::render_envelope(
            "run",
            result(false, 2, "tool_error", Some("controlled".into())),
            &data,
        )
        .unwrap();
        let wire: Value = serde_json::from_str(&text).unwrap();
        assert_eq!(keys(&wire["data"]), DATA_KEYS);
        assert_eq!(wire["data"]["runner_result"], unsupported);
        assert_eq!(
            wire["data"]["runner_client"]["request_delivery"]["bytes_written"],
            1
        );
        assert!(wire["data"]["runner_client"]["request_delivery"]["error"].is_string());
        assert!(wire["data"]["policy_check"].is_null());
        assert!(wire["data"]["sandbox_log_capture"].is_null());
        assert!(wire["data"]["runner_sandbox_diagnostics"].is_null());
        assert_eq!(wire["data"]["timeout_ms"], 7);
        assert_eq!(wire["result"]["exit_code"], 2);
        assert_eq!(wire["result"]["normalized_outcome"], "tool_error");
        assert!(wire["data"].get("error").is_none());
    }

    #[test]
    fn fallback_compilation_is_requested_only_for_an_admitted_xpc_error() {
        let xpc_error = json!({"schema_version": json_contract::RESPONSE_SCHEMA_VERSION,
            "normalized_outcome": "xpc_error", "error": "NSCocoaErrorDomain:4099 refused", "steps": []});
        let before = xpc_error.clone();
        let mut invoked = 0;
        let capture = fallback_policy_check(Some(&xpc_error), || {
            invoked += 1;
            Err("sbpl-check request delivery failed: Broken pipe".into())
        });
        assert_eq!(invoked, 1);
        let capture = capture.expect("an xpc_error reply requests the helper");
        assert_eq!(capture.status, "unavailable");
        assert!(capture.envelope.is_none());
        assert!(
            capture.output.stderr.contains("Broken pipe"),
            "{}",
            capture.output.stderr
        );
        // The original reply is retained exactly as received.
        assert_eq!(xpc_error, before);
        let mut invoked = 0;
        for reply in [
            Some(worker("ok", None)),
            Some(worker("runner_failed", Some(9))),
            Some(worker("xpc_timeout", None)),
            None,
        ] {
            assert!(
                fallback_policy_check(reply.as_ref(), || {
                    invoked += 1;
                    Err("never requested".into())
                })
                .is_none()
            );
        }
        assert_eq!(invoked, 0);

        // Helper success, rejection and an unavailable capture leave the
        // runner reply and the controller's outcome unchanged.
        let helper_envelope = |outcome: &str| {
            json!({"schema_version": json_contract::SCHEMA_VERSION, "kind": "sbpl_check",
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
                output: JsonOutputCapture::unavailable(
                    String::new(),
                    crate::utils::HELPER_CAPTURE_BYTES,
                ),
                envelope: envelope.clone(),
            };
            let completed = complete_execution(ExecutionData {
                specimen: specimen(),
                policy_check: Some(capture),
                timeout_ms: Some(7),
                runner_client: None,
                runner_result: Some(xpc_error.clone()),
                request_failure: None,
            });
            assert_eq!(completed.exit_code, 1, "{status}");
            assert_eq!(
                completed.result.normalized_outcome.as_deref(),
                Some("xpc_error"),
                "{status}"
            );
            assert_eq!(
                completed.result.error.as_deref(),
                Some("NSCocoaErrorDomain:4099 refused"),
                "{status}"
            );
            assert_eq!(
                completed.data.runner_result,
                Some(before.clone()),
                "{status}"
            );
            let check = completed.data.policy_check.as_ref().unwrap();
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
        assert_eq!(wire["schema_version"], json_contract::SCHEMA_VERSION);
        assert_eq!(wire["result"]["ok"], false);
        assert_eq!(wire["result"]["exit_code"], 2);
        assert_eq!(wire["result"]["normalized_outcome"], "tool_error");
        assert_eq!(wire["result"]["error"], "missing <request.json>");
        assert_eq!(keys(&wire["data"]), DATA_KEYS);
        for key in [
            "policy_check",
            "runner_client",
            "runner_result",
            "sandbox_log_capture",
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
        let hash = crate::sbpl_imports::sha256_hex(source);
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
    // `run` with its production dependencies replaced at the four boundaries:
    // a counting loader around the real manifest reader, a synthetic app root,
    // an on-disk registry fixture and a capturing client that answers with a
    // current-schema reply. Every assertion reads the rendered envelope or a
    // capture; nothing here reconstructs orchestration or counts source calls.
    mod orchestration {
        use super::*;
        use crate::app_layout::{
            SHIPPED_SERVICE, SHIPPED_VALIDATOR, SHIPPED_WORKER, ShippedBinary,
        };
        use crate::runner_manager::{
            RUNNER_PROTOCOL_VERSION, RUNNER_REGISTRY_SCHEMA_VERSION, RunnerEntitlements,
            RunnerRecord, RunnerRegistry, RunnerScope, RunnerSignature, RunnerState,
        };
        use std::cell::RefCell;
        use std::fs;

        const ROLES: [&ShippedBinary; 3] = [&SHIPPED_SERVICE, &SHIPPED_WORKER, &SHIPPED_VALIDATOR];
        const ROLE_NAMES: [&str; 3] = ["service", "worker", "validator"];
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
            bundle
        }

        fn signature() -> RunnerSignature {
            RunnerSignature {
                team_id: Some("TEAM123456".into()),
                identity: Some("Developer ID Application: Controlled (TEAM123456)".into()),
                cdhash: Some("ab".repeat(20)),
                valid: true,
                adhoc: false,
            }
        }

        fn entitlements(keys: &[&str]) -> RunnerEntitlements {
            RunnerEntitlements {
                raw_plist: Some("<plist version=\"1.0\"><dict/></plist>".into()),
                keys: keys.iter().map(|k| k.to_string()).collect(),
                error: None,
            }
        }

        fn record(bundle: &Path, keys: &[&str]) -> RunnerRecord {
            RunnerRecord {
                state: RunnerState::Installed,
                ownership: None,
                id: "runner-ext".into(),
                service_name: EXTERNAL_SERVICE.into(),
                bundle_path: bundle.display().to_string(),
                executable_path: bundle.join("Contents/MacOS/PWRunner").display().to_string(),
                bundle_id: Some(EXTERNAL_SERVICE.into()),
                scope: RunnerScope::User,
                protocol_version: RUNNER_PROTOCOL_VERSION,
                signature: signature(),
                entitlements: entitlements(keys),
                installed_at_unix_ms: 1,
                kind: Some(RunnerKind::Byoxpc),
            }
        }

        fn registry_fixture(root: &Path, runners: Vec<RunnerRecord>) -> PathBuf {
            let registry = RunnerRegistry {
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
                "schema_version": crate::json_contract::REQUEST_SCHEMA_VERSION, "specimen_id": "controlled",
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
                "schema_version": json_contract::RESPONSE_SCHEMA_VERSION,
                "normalized_outcome": "ok", "rc": 0, "pid": 77,
                "specimen_id": "controlled", "steps": [],
            })
        }

        /// Production orchestration with the four dependencies controlled.
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
                Ok((client_run(Some(&reply)), Some(reply)))
            };
            let app_root = app.to_path_buf();
            let deps = RunDependencies {
                app_root: &|| Ok(app_root.clone()),
                load_manifest: &load_manifest,
                registry_path: registry,
                client: &client,
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
            for version in [
                json!(1),
                json!(json_contract::REQUEST_SCHEMA_VERSION + 1),
                json!(null),
                json!(true),
            ] {
                let mut value = original.clone();
                value["schema_version"] = version;
                // These would fail if interpreted before the version gate.
                value["runner"] = json!({"mode": "unknown-mode"});
                value["policy"]["augments"] = json!(["unknown_augment"]);
                let bytes = serde_json::to_vec(&value).unwrap();
                fs::write(&request, &bytes).unwrap();
                let observed =
                    observe(&app, None, &[request.to_str().unwrap(), "--no-log-capture"]);
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
            let observed = observe(&app, None, &[request.to_str().unwrap(), "--no-log-capture"]);
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
            assert_eq!(wire["result"]["normalized_outcome"], "ok");
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
            assert!(wire["data"]["sandbox_log_capture"].is_null());
            assert_eq!(
                wire["data"]["runner_sandbox_diagnostics"]["correlation_status"],
                "not_attempted"
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
                let observed =
                    observe(&app, None, &[request.to_str().unwrap(), "--no-log-capture"]);
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
        fn refused_reply_versions_request_no_fallback_compilation() {
            // Through production admission: a reply under another response
            // version is refused before anything reads it, so no helper is
            // requested and `policy_check` is null. An admitted `xpc_error`
            // reply requests the helper; the synthetic app embeds none, so the
            // capture is unavailable while the reply and the outcome stand.
            let root = scratch("refused-reply-versions");
            let app = synthetic_app(&root);
            install_manifest(&app, ManifestState::Valid);
            let request = request_file(&root, None);
            let args = [request.to_str().unwrap(), "--no-log-capture"];
            let current = i64::from(json_contract::RESPONSE_SCHEMA_VERSION);
            for (label, reply, outcome) in [
                (
                    "previous",
                    json!({"schema_version": current - 1, "normalized_outcome": "xpc_error",
                        "error": "refused", "steps": []}),
                    "unsupported_runner_response",
                ),
                (
                    "next",
                    json!({"schema_version": current + 1, "normalized_outcome": "xpc_error",
                        "error": "refused", "steps": []}),
                    "unsupported_runner_response",
                ),
                (
                    "string",
                    json!({"schema_version": current.to_string(), "normalized_outcome": "xpc_error",
                        "error": "refused", "steps": []}),
                    "malformed_runner_response",
                ),
                (
                    "missing",
                    json!({"normalized_outcome": "xpc_error", "error": "refused", "steps": []}),
                    "malformed_runner_response",
                ),
            ] {
                let observed = observe_reply(&app, None, &args, reply.clone());
                assert_eq!(observed.calls.len(), 1, "{label}");
                let (wire, exit_code) = envelope_of(&observed.output);
                assert_eq!(exit_code, 1, "{label}");
                assert_eq!(wire["result"]["normalized_outcome"], outcome, "{label}");
                assert!(wire["data"]["policy_check"].is_null(), "{label}");
                assert_eq!(wire["data"]["runner_result"], reply, "{label}");
            }
            let xpc_error = json!({"schema_version": current, "normalized_outcome": "xpc_error",
                "error": "NSCocoaErrorDomain:4099 refused", "steps": []});
            let observed = observe_reply(&app, None, &args, xpc_error.clone());
            let (wire, exit_code) = envelope_of(&observed.output);
            assert_eq!(exit_code, 1);
            assert_eq!(wire["result"]["normalized_outcome"], "xpc_error");
            assert_eq!(wire["result"]["error"], "NSCocoaErrorDomain:4099 refused");
            assert_eq!(wire["data"]["runner_result"], xpc_error);
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
                &[
                    request.to_str().unwrap(),
                    "--no-log-capture",
                    "--timeout-ms",
                    "7000",
                ],
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
                let observed = observe(
                    &app,
                    Some(&registry),
                    &[request.to_str().unwrap(), "--no-log-capture"],
                );
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
                    "external runner does not satisfy required entitlements",
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
                let observed = observe(
                    &app,
                    Some(&registry),
                    &[request.to_str().unwrap(), "--no-log-capture"],
                );
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
                &["/r.json", "--log-timeout-ms", "0"],
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
                    vec![missing.to_str().unwrap(), "--no-log-capture"],
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
    // by the helpers' own tests (`sandbox-log-observer.rs`, `sbpl-check.rs`).
    mod envelope_shape {
        use super::*;
        use crate::dossier::{AppProvenance, Augmentation, BinaryRecord, Imports, PolicyDossier};
        use crate::evidence::{VerifyMismatch, VerifyReport};
        use crate::log_capture::{
            Boundary, CleanupObservation, CollectionBudget, Cutoff, ProcessObservation,
            StreamObservation, Supervision, SyscallObservation, TimeoutSource,
        };
        use crate::policy_check::PolicyCheckCapture;
        use crate::runner_manager::{RunnerEntitlements, RunnerSignature};
        use crate::runner_select::RunnerTarget;
        use crate::sandbox_log::{SandboxLogMatchEvidence, SandboxLogStepDeny, SandboxLogWindow};
        use crate::sbpl_imports::ImportRecord;
        use crate::utils::JsonOutputCapture;

        fn full_result() -> json_contract::JsonResult {
            json_contract::JsonResult {
                ok: true,
                rc: Some(0),
                exit_code: Some(0),
                normalized_outcome: Some("ok".into()),
                errno: Some(0),
                error: Some("constructed".into()),
                stderr: Some("".into()),
                stdout: Some("".into()),
            }
        }

        fn capture(limit: usize) -> JsonOutputCapture {
            JsonOutputCapture {
                stdout_parse_error: Some("constructed".into()),
                stdout_truncated: false,
                stdout_capture_error: Some("constructed".into()),
                stdout_bytes_received: Some(2),
                stdout_bytes_retained: Some(2),
                stderr_bytes_received: Some(0),
                stderr_bytes_retained: Some(0),
                capture_limit_bytes: limit,
                stdout_raw: Some("{}".into()),
                stderr: String::new(),
                stderr_truncated: false,
            }
        }

        fn stream() -> StreamObservation {
            StreamObservation {
                limit_bytes: 1024,
                bytes_read: 2,
                bytes_retained: 2,
                eof: true,
                truncated: false,
                read_error: Some("constructed".into()),
            }
        }

        fn cutoff() -> Cutoff {
            Cutoff {
                reason: "deadline".into(),
                stream: Some("stdout".into()),
                limit: Some(1024),
                observed: Some(1025),
                detail: Some("constructed".into()),
            }
        }

        fn supervision(boundary: Boundary) -> Supervision {
            Supervision {
                boundary,
                budget: CollectionBudget {
                    timeout_ms: 10_000,
                    timeout_source: TimeoutSource::Default,
                    started_monotonic_ns: 1,
                    deadline_monotonic_ns: 2,
                },
                reserve_ms: 1_000,
                elapsed_ms: 150,
                cutoff: Some(cutoff()),
                stdout: stream(),
                stderr: stream(),
                process: ProcessObservation {
                    pid: Some(42),
                    exit_observed: true,
                    reaped: true,
                    exit_code: Some(0),
                    term_signal: Some(9),
                    wait_error: Some("constructed".into()),
                },
                cleanup: CleanupObservation {
                    scope: "process_group".into(),
                    target: Some(42),
                    grace_ms: 1_000,
                    ownership: "owned".into(),
                    signal: Some(9),
                    signal_result: Some(SyscallObservation {
                        rc: -1,
                        errno: Some(1),
                    }),
                    signal_before_reap: true,
                    ownership_released: true,
                    group_probe: Some(SyscallObservation {
                        rc: -1,
                        errno: Some(3),
                    }),
                    outcome: "group_absent".into(),
                    detail: Some("constructed".into()),
                },
            }
        }

        fn deny_event() -> SandboxDenyEvent {
            SandboxDenyEvent {
                pid: Some(42),
                process: Some("pw-probe-runner".into()),
                operation: Some("file-read-data".into()),
                path: Some("/private/etc/hosts".into()),
                raw_line: Some("constructed deny line".into()),
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

        /// The observer's report with every field present, in the frame the
        /// observer prints; `sandbox-log-observer.rs` compares its own emitted
        /// shape with the golden subtree this fixture records.
        fn observer_report() -> Value {
            nested_envelope(
                "sandbox_log_observer_report",
                json!({
                    "observer_schema_version": 2, "mode": "show", "duration_ms": 1,
                    "stop_on_pid_exit": false, "plan_id": "p", "row_id": "r", "correlation_id": "c",
                    "pid": 42, "process_name": "pw-probe-runner", "predicate": "constructed",
                    "start": "2026-01-01 00:00:00+0000", "end": "2026-01-01 00:00:05+0000", "last": "1m",
                    "log_rc": 0, "log_stdout": "", "log_stderr": "", "log_error": "constructed",
                    "blocked_reason": "constructed", "log_truncated": false, "observed_lines": 1,
                    "observed_deny": true,
                    "deny_events": [serde_json::to_value(deny_event()).unwrap()],
                    "collection": serde_json::to_value(supervision(Boundary::LogShow)).unwrap(),
                }),
            )
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
                    team_id: Some("TEAM123456".into()),
                    identity: Some("constructed".into()),
                    cdhash: Some("ab".repeat(20)),
                    valid: true,
                    adhoc: false,
                }),
                entitlements: Some(RunnerEntitlements {
                    raw_plist: Some("<plist/>".into()),
                    keys: vec!["com.apple.security.app-sandbox".into()],
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
                },
            };
            let reply = json!({
                "schema_version": json_contract::RESPONSE_SCHEMA_VERSION,
                "normalized_outcome": "ok", "rc": 0, "pid": 42, "steps": [],
            });
            let data = RunData {
                execution: ExecutionData {
                    specimen,
                    policy_check: Some(PolicyCheckCapture {
                        status: "ok".into(),
                        tool_exit_code: 0,
                        output: capture(crate::utils::HELPER_CAPTURE_BYTES),
                        envelope: Some(sbpl_check_envelope()),
                    }),
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
                    }),
                    runner_result: Some(reply),
                    // Field-complete shape fixture, including an optional refusal record.
                    request_failure: Some(
                        json!({"code": "unknown_field", "path": ["policy", "typo"],
                        "expected_schema": json_contract::REQUEST_SCHEMA_VERSION}),
                    ),
                },
                sandbox_log_capture: Some(SandboxLogCapture {
                    window: SandboxLogWindow {
                        kind: "runner_client_span",
                        started_at_unix_ms: 1_000,
                        ended_at_unix_ms: 2_500,
                        pad_seconds: 2,
                        start: Some("1969-12-31 23:59:59+0000".into()),
                        end: Some("1970-01-01 00:00:05+0000".into()),
                    },
                    capture_status: "captured".into(),
                    tool_exit_code: 0,
                    blocked_reason: Some("constructed".into()),
                    output: capture(crate::utils::OBSERVER_CAPTURE_BYTES),
                    observer: Some(observer_report()),
                    observed_deny: Some(true),
                    deny_events: Some(vec![deny_event()]),
                    step_denies: Some(vec![SandboxLogStepDeny {
                        event_index: 0,
                        candidate_step_ids: vec!["s".into()],
                        association: "candidate".into(),
                        matching_evidence: vec![SandboxLogMatchEvidence {
                            step_id: "s".into(),
                            operation: "file-read-data".into(),
                            operation_source: "submitted_attempt",
                            requested_kind: "file".into(),
                            requested_action: "open_read".into(),
                            path: "/private/etc/hosts".into(),
                            path_sources: vec!["submitted_attempt.target".into()],
                        }],
                    }]),
                    supervision: Some(supervision(Boundary::Observer)),
                    processing_cutoff: Some(cutoff()),
                }),
                runner_sandbox_diagnostics: Some(RunnerSandboxDiagnostics {
                    execution: RunnerExecutionDiagnostics {
                        process_disposition: "clean_exit",
                        termination_cause: Some("host_sentinel_deadline"),
                        stop_reason: Some("done".into()),
                        disposition_integrity: Some("valid"),
                        disposition_issues: vec![integrity_issue(
                            "missing_record",
                            "constructed".into(),
                        )],
                    },
                    logs: RunnerLogDiagnostics {
                        correlation_status: "pid_match",
                        permission_failures_without_record: Some(vec!["s".into()]),
                    },
                }),
            };
            (full_result(), data)
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
            crate::shape::check_golden(
                &golden,
                "controller_envelope",
                u64::from(json_contract::SCHEMA_VERSION),
                &current,
                "envelope_shape.candidate.json",
            )
            .unwrap();
        }
    }
}
