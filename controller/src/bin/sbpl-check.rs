//! `sbpl-check`: host-side SBPL compile-check for diagnostics.
//!
//! This tool parses a PolicyWitness request JSON, extracts the SBPL policy,
//! inventories its literal `(import ...)` closure and compiles the source with
//! the host's libsandbox, passing `policy.params` through `sandbox_set_param`.
//! Native compilation decides the verdict; the helper repeats it and records
//! the last native stage it attempted. The helper performs no parameter scan
//! of its own: what an unbound `(param "NAME")` means is the compiler's call,
//! and its diagnostic is copied unchanged.

#[path = "../json_contract.rs"]
#[allow(dead_code)]
mod json_contract;
#[cfg(test)]
#[path = "../shape.rs"]
mod shape;

#[path = "../host_facts.rs"]
mod host_facts;
#[path = "../sbpl_imports.rs"]
mod sbpl_imports;
#[path = "../sbpl_lex.rs"]
mod sbpl_lex;

use serde::Deserialize;
use serde::Serialize;
use std::collections::BTreeMap;
use std::ffi::{CStr, CString};
use std::os::raw::{c_char, c_int, c_void};
use std::path::PathBuf;

#[link(name = "sandbox")]
unsafe extern "C" {
    fn sandbox_compile_string(
        profile: *const c_char,
        params: *const c_void,
        errorbuf: *mut *mut c_char,
    ) -> *mut c_void;
    fn sandbox_free_error(errorbuf: *mut c_char);
    fn sandbox_free_profile(profile: *mut c_void);
    fn sandbox_create_params() -> *mut c_void;
    fn sandbox_set_param(params: *mut c_void, key: *const c_char, value: *const c_char) -> c_int;
    fn sandbox_free_params(params: *mut c_void);
}

#[derive(Deserialize)]
struct CheckRequest {
    policy: CheckPolicy,
}

#[derive(Deserialize)]
struct CheckPolicy {
    format: String,
    sbpl_source: Option<String>,
    params: Option<BTreeMap<String, String>>,
}

/// The native stage a compile record describes: the last call attempted.
/// Names align with the worker's `PW_OP_PARAMS_CREATE`, `PW_OP_PARAM_SET` and
/// `PW_OP_COMPILE` without importing its ABI.
#[derive(Serialize, Clone, Copy, Debug, PartialEq)]
#[serde(rename_all = "snake_case")]
enum Stage {
    ParamsCreate,
    ParamSet,
    Compile,
}

/// The last native stage attempted and how it ended. Not a history of calls:
/// a record at `compile` says setup, if any, completed.
#[derive(Serialize, Clone, Debug, PartialEq)]
struct CompileRecord {
    stage: Stage,
    ok: bool,
    /// Setup failures carry helper text naming the failed call. A compile
    /// failure carries the compiler's decoded error buffer unchanged, or null
    /// when the compiler returned no profile and no diagnostic.
    error: Option<String>,
}

/// The literal import closure the helper walked before compiling, with the
/// closure hash over the source and every resolved import. Resolution errors,
/// truncation and cycles stay here; they never change the verdict.
#[derive(Serialize)]
struct ImportInventory {
    records: Vec<sbpl_imports::ImportRecord>,
    truncated: bool,
    cycle: Option<Vec<String>>,
    policy_closure_sha256: String,
}

#[derive(Serialize)]
struct CheckData {
    policy_format: String,
    /// Null on an input refusal; the hash of `policy.sbpl_source` otherwise.
    policy_sha256: Option<String>,
    macos_build_version: Option<String>,
    /// Whether the request carried a `policy.params` map at all. An empty map
    /// is present; a missing or null map is not.
    params_present: bool,
    params_count: usize,
    /// Null when input was refused before any native call.
    compile: Option<CompileRecord>,
    /// Null when input was refused before the walk; otherwise the performed
    /// walk, with empty `records` when the source imports nothing.
    import_inventory: Option<ImportInventory>,
}

struct CheckReport {
    result: json_contract::JsonResult,
    data: CheckData,
}

const NO_DIAGNOSTIC_SUMMARY: &str = "sandbox_compile_string returned NULL without a diagnostic";

/// The libsandbox calls the check makes, behind one boundary so the unit
/// controls can script results and account for every allocation. Production
/// binds [`LibSandbox`]; nothing selects another implementation at run time.
trait Native {
    fn create_params(&mut self) -> *mut c_void;
    fn set_param(&mut self, params: *mut c_void, key: &CStr, value: &CStr) -> c_int;
    fn free_params(&mut self, params: *mut c_void);
    fn compile(
        &mut self,
        source: &CStr,
        params: *mut c_void,
        error: &mut *mut c_char,
    ) -> *mut c_void;
    fn free_error(&mut self, error: *mut c_char);
    fn free_profile(&mut self, profile: *mut c_void);
}

struct LibSandbox;

impl Native for LibSandbox {
    fn create_params(&mut self) -> *mut c_void {
        unsafe { sandbox_create_params() }
    }
    fn set_param(&mut self, params: *mut c_void, key: &CStr, value: &CStr) -> c_int {
        unsafe { sandbox_set_param(params, key.as_ptr(), value.as_ptr()) }
    }
    fn free_params(&mut self, params: *mut c_void) {
        unsafe { sandbox_free_params(params) }
    }
    fn compile(
        &mut self,
        source: &CStr,
        params: *mut c_void,
        error: &mut *mut c_char,
    ) -> *mut c_void {
        unsafe { sandbox_compile_string(source.as_ptr(), params, error) }
    }
    fn free_error(&mut self, error: *mut c_char) {
        unsafe { sandbox_free_error(error) }
    }
    fn free_profile(&mut self, profile: *mut c_void) {
        unsafe { sandbox_free_profile(profile) }
    }
}

/// The import walk the check performs on admitted source. Production binds
/// `sbpl_imports::resolve_imports`; the unit controls count calls and supply
/// constructed inventories.
type ImportWalk<'a> = dyn FnMut(&str) -> sbpl_imports::ResolvedImports + 'a;

enum Refusal {
    BadRequest(String),
    PolicyTooLarge(String),
}

/// One `policy.params` entry converted for the native call, with the key kept
/// for setup diagnostics. The value is never echoed.
struct NativeParam {
    key: String,
    key_c: CString,
    value_c: CString,
}

/// Validated input with every native C string already built, so no
/// conversion failure can follow a native allocation.
struct AdmittedInput<'a> {
    source: &'a str,
    source_c: CString,
    params: Vec<NativeParam>,
}

/// Validate format, source presence, the source byte cap and every native C
/// string, in that order. Nothing here walks imports or touches libsandbox.
fn admit(policy: &CheckPolicy) -> Result<AdmittedInput<'_>, Refusal> {
    if policy.format != "sbpl" {
        return Err(Refusal::BadRequest(
            "unsupported policy.format (expected sbpl)".to_string(),
        ));
    }
    let source = policy
        .sbpl_source
        .as_deref()
        .ok_or_else(|| Refusal::BadRequest("missing policy.sbpl_source".to_string()))?;
    if source.len() > sbpl_imports::MAX_SBPL_SOURCE_BYTES {
        return Err(Refusal::PolicyTooLarge(format!(
            "policy.sbpl_source is {} bytes; cap is {} bytes",
            source.len(),
            sbpl_imports::MAX_SBPL_SOURCE_BYTES
        )));
    }
    let source_c = CString::new(source)
        .map_err(|_| Refusal::BadRequest("policy.sbpl_source contains NUL".to_string()))?;
    let mut params = Vec::new();
    for (key, value) in policy.params.iter().flatten() {
        let key_c = CString::new(key.as_str())
            .map_err(|_| Refusal::BadRequest("a policy.params key contains NUL".to_string()))?;
        let value_c = CString::new(value.as_str()).map_err(|_| {
            Refusal::BadRequest(format!("policy.params value for {key} contains NUL"))
        })?;
        params.push(NativeParam {
            key: key.clone(),
            key_c,
            value_c,
        });
    }
    Ok(AdmittedInput {
        source,
        source_c,
        params,
    })
}

/// Native parameter setup and compilation. Every allocation acquired is
/// released on every return; an absent or empty params map makes no setup
/// call and passes NULL to the compiler.
fn compile_with(native: &mut dyn Native, input: &AdmittedInput<'_>) -> CompileRecord {
    let mut params_obj: *mut c_void = std::ptr::null_mut();
    if !input.params.is_empty() {
        params_obj = native.create_params();
        if params_obj.is_null() {
            return CompileRecord {
                stage: Stage::ParamsCreate,
                ok: false,
                error: Some("sandbox_create_params returned NULL".to_string()),
            };
        }
        for param in &input.params {
            let rc = native.set_param(params_obj, &param.key_c, &param.value_c);
            if rc != 0 {
                native.free_params(params_obj);
                return CompileRecord {
                    stage: Stage::ParamSet,
                    ok: false,
                    error: Some(format!(
                        "sandbox_set_param failed for {}: rc={rc}",
                        param.key
                    )),
                };
            }
        }
    }

    let mut err_buf: *mut c_char = std::ptr::null_mut();
    let profile = native.compile(&input.source_c, params_obj, &mut err_buf);
    let diagnostic = if err_buf.is_null() {
        None
    } else {
        // Text, decoded by the existing C-string convention, never a raw-byte
        // receipt. An empty native string stays an empty string.
        let text = unsafe { CStr::from_ptr(err_buf) }
            .to_string_lossy()
            .into_owned();
        native.free_error(err_buf);
        Some(text)
    };
    if !profile.is_null() {
        native.free_profile(profile);
    }
    if !params_obj.is_null() {
        native.free_params(params_obj);
    }

    // A profile beside an error buffer remains a failure; a NULL profile
    // without a diagnostic is a completed call with nothing to quote.
    let ok = !profile.is_null() && diagnostic.is_none();
    CompileRecord {
        stage: Stage::Compile,
        ok,
        error: diagnostic,
    }
}

fn verdict(compile: &CompileRecord) -> (&'static str, i32, Option<String>) {
    match compile {
        CompileRecord { ok: true, .. } => ("ok", 0, None),
        CompileRecord {
            stage: Stage::Compile,
            error,
            ..
        } => (
            "compile_error",
            1,
            Some(
                error
                    .clone()
                    .unwrap_or_else(|| NO_DIAGNOSTIC_SUMMARY.to_string()),
            ),
        ),
        CompileRecord { error, .. } => ("setup_error", 1, error.clone()),
    }
}

/// Admission, import inventory, native setup and compilation, then the
/// verdict, in that order. An input refusal performs no walk and no native
/// call and leaves both groups explicitly null.
fn check(
    request: &CheckRequest,
    native: &mut dyn Native,
    walk: &mut ImportWalk<'_>,
) -> CheckReport {
    let policy = &request.policy;
    let params_present = policy.params.is_some();
    let params_count = policy.params.as_ref().map_or(0, BTreeMap::len);
    let data = |policy_sha256, compile, import_inventory| CheckData {
        policy_format: policy.format.clone(),
        policy_sha256,
        macos_build_version: host_facts::macos_build_version(),
        params_present,
        params_count,
        compile,
        import_inventory,
    };

    let admitted = match admit(policy) {
        Ok(admitted) => admitted,
        Err(refusal) => {
            let (outcome, error) = match refusal {
                Refusal::BadRequest(error) => ("bad_request", error),
                Refusal::PolicyTooLarge(error) => ("policy_too_large", error),
            };
            return CheckReport {
                result: json_contract::JsonResult::new(false, 1, Some(outcome), Some(error)),
                data: data(None, None, None),
            };
        }
    };

    let policy_sha256 = sbpl_imports::sha256_hex(admitted.source);
    let resolved = walk(admitted.source);
    let inventory = ImportInventory {
        policy_closure_sha256: sbpl_imports::compute_closure_hash(
            admitted.source,
            &resolved.records,
        ),
        records: resolved.records,
        truncated: resolved.truncated,
        cycle: resolved.cycle,
    };
    let compile = compile_with(native, &admitted);
    let (outcome, exit_code, error) = verdict(&compile);
    CheckReport {
        result: json_contract::JsonResult::new(exit_code == 0, exit_code, Some(outcome), error),
        data: data(Some(policy_sha256), Some(compile), Some(inventory)),
    }
}

fn usage() -> String {
    "\
usage:
  sbpl-check --request <request.json|->

notes:
  - reads the request JSON from the named file, or from stdin to EOF when the value is `-`
  - compiles policy.sbpl_source with the host's libsandbox and inventories its literal imports
  - prints a JSON envelope with the native verdict, the last compile stage and error details"
        .to_string()
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.is_empty() {
        eprintln!("{}", usage());
        std::process::exit(2);
    }

    let mut request_path: Option<PathBuf> = None;
    let mut idx = 0usize;
    while idx < args.len() {
        match args[idx].as_str() {
            "-h" | "--help" => {
                println!("{}", usage());
                return;
            }
            "--request" => {
                if let Some(path) = args.get(idx + 1) {
                    request_path = Some(PathBuf::from(path));
                    idx += 2;
                } else {
                    eprintln!("missing value for --request");
                    eprintln!("{}", usage());
                    std::process::exit(2);
                }
            }
            other => {
                eprintln!("unknown argument: {other}\n\n{}", usage());
                std::process::exit(2);
            }
        }
    }

    let request_path = match request_path {
        Some(path) => path,
        None => {
            eprintln!("missing --request\n\n{}", usage());
            std::process::exit(2);
        }
    };

    let text = if request_path.as_os_str() == "-" {
        let mut text = String::new();
        if let Err(err) = std::io::Read::read_to_string(&mut std::io::stdin().lock(), &mut text) {
            eprintln!("failed to read request: {err}");
            std::process::exit(2);
        }
        text
    } else {
        match std::fs::read_to_string(&request_path) {
            Ok(text) => text,
            Err(err) => {
                eprintln!("failed to read request: {err}");
                std::process::exit(2);
            }
        }
    };

    let parsed: CheckRequest = match serde_json::from_str(&text) {
        Ok(req) => req,
        Err(err) => {
            eprintln!("failed to parse request.json: {err}");
            std::process::exit(2);
        }
    };

    let mut walk = sbpl_imports::resolve_imports;
    let report = check(&parsed, &mut LibSandbox, &mut walk);
    let exit_code = report.result.exit_code.unwrap_or(1);
    let _ = json_contract::print_envelope("sbpl_check", report.result, &report.data);
    std::process::exit(exit_code);
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::{Value, json};
    use std::collections::BTreeSet;

    const RETIRED_FIELDS: [&str; 6] = [
        "params_referenced",
        "params_supplied",
        "params_missing",
        "params_unused",
        "params_scan_complete",
        "param_scan",
    ];

    /// Scripted libsandbox. Every allocation is a real heap object the check
    /// must hand back exactly once: a free of an unknown or already released
    /// pointer panics, and `release_complete` says whether anything leaked.
    struct FakeNative {
        /// Per create call: allocate an object (`true`) or return NULL.
        create: Vec<bool>,
        /// Per set call, in order; a missing entry means 0.
        set: Vec<c_int>,
        /// Whether the compiler returns a profile, and its error buffer.
        profile: bool,
        diagnostic: Option<&'static str>,
        create_calls: usize,
        set_calls: Vec<(String, String)>,
        /// Source bytes and whether a params object was passed.
        compile_calls: Vec<(Vec<u8>, bool)>,
        live_params: BTreeSet<usize>,
        live_errors: BTreeSet<usize>,
        live_profiles: BTreeSet<usize>,
        freed_params: usize,
        freed_errors: usize,
        freed_profiles: usize,
    }

    impl FakeNative {
        fn new(profile: bool, diagnostic: Option<&'static str>) -> Self {
            FakeNative {
                create: vec![true],
                set: Vec::new(),
                profile,
                diagnostic,
                create_calls: 0,
                set_calls: Vec::new(),
                compile_calls: Vec::new(),
                live_params: BTreeSet::new(),
                live_errors: BTreeSet::new(),
                live_profiles: BTreeSet::new(),
                freed_params: 0,
                freed_errors: 0,
                freed_profiles: 0,
            }
        }

        fn release_complete(&self) -> bool {
            self.live_params.is_empty()
                && self.live_errors.is_empty()
                && self.live_profiles.is_empty()
        }

        fn untouched(&self) -> bool {
            self.create_calls == 0 && self.set_calls.is_empty() && self.compile_calls.is_empty()
        }
    }

    impl Native for FakeNative {
        fn create_params(&mut self) -> *mut c_void {
            let allocate = self.create.get(self.create_calls).copied().unwrap_or(true);
            self.create_calls += 1;
            if !allocate {
                return std::ptr::null_mut();
            }
            let ptr = Box::into_raw(Box::new(0xA5u8)) as *mut c_void;
            self.live_params.insert(ptr as usize);
            ptr
        }
        fn set_param(&mut self, params: *mut c_void, key: &CStr, value: &CStr) -> c_int {
            assert!(
                self.live_params.contains(&(params as usize)),
                "set on a foreign params object"
            );
            let rc = self.set.get(self.set_calls.len()).copied().unwrap_or(0);
            self.set_calls.push((
                key.to_str().unwrap().to_string(),
                value.to_str().unwrap().to_string(),
            ));
            rc
        }
        fn free_params(&mut self, params: *mut c_void) {
            assert!(
                self.live_params.remove(&(params as usize)),
                "params freed twice or never allocated"
            );
            self.freed_params += 1;
            unsafe { drop(Box::from_raw(params as *mut u8)) };
        }
        fn compile(
            &mut self,
            source: &CStr,
            params: *mut c_void,
            error: &mut *mut c_char,
        ) -> *mut c_void {
            if !params.is_null() {
                assert!(
                    self.live_params.contains(&(params as usize)),
                    "compile with a foreign params object"
                );
            }
            self.compile_calls
                .push((source.to_bytes().to_vec(), !params.is_null()));
            if let Some(text) = self.diagnostic {
                let ptr = CString::new(text).unwrap().into_raw();
                self.live_errors.insert(ptr as usize);
                *error = ptr;
            }
            if self.profile {
                let ptr = Box::into_raw(Box::new(0x5Au8)) as *mut c_void;
                self.live_profiles.insert(ptr as usize);
                ptr
            } else {
                std::ptr::null_mut()
            }
        }
        fn free_error(&mut self, error: *mut c_char) {
            assert!(
                self.live_errors.remove(&(error as usize)),
                "error buffer freed twice or never allocated"
            );
            self.freed_errors += 1;
            unsafe { drop(CString::from_raw(error)) };
        }
        fn free_profile(&mut self, profile: *mut c_void) {
            assert!(
                self.live_profiles.remove(&(profile as usize)),
                "profile freed twice or never allocated"
            );
            self.freed_profiles += 1;
            unsafe { drop(Box::from_raw(profile as *mut u8)) };
        }
    }

    fn request(policy: Value) -> CheckRequest {
        serde_json::from_value(json!({ "policy": policy })).unwrap()
    }

    fn wire(report: &CheckReport) -> Value {
        let text =
            json_contract::render_envelope("sbpl_check", report.result.clone(), &report.data)
                .unwrap();
        serde_json::from_str(&text).unwrap()
    }

    /// Drive the real routine with the scripted compiler and a counting walk
    /// over the real resolver. Returns the envelope and the walked sources.
    fn run_with(native: &mut FakeNative, policy: Value) -> (Value, Vec<String>) {
        let mut walked = Vec::new();
        let wire = {
            let mut walk = |source: &str| {
                walked.push(source.to_string());
                sbpl_imports::resolve_imports(source)
            };
            wire(&check(&request(policy), native, &mut walk))
        };
        assert_scan_free(&wire);
        (wire, walked)
    }

    /// Every emitted envelope: the retired scan fields are absent by key, and
    /// no producer outcome is `missing_params`.
    fn assert_scan_free(wire: &Value) {
        let data = wire["data"].as_object().unwrap();
        for field in RETIRED_FIELDS {
            assert!(
                !data.contains_key(field),
                "{field} must be absent, not null"
            );
        }
        assert_ne!(wire["result"]["normalized_outcome"], "missing_params");
        for key in ["compile", "import_inventory", "policy_sha256"] {
            assert!(data.contains_key(key), "{key} is an explicit key");
        }
    }

    fn assert_verdict(wire: &Value, outcome: &str, exit_code: i64) {
        assert_eq!(wire["kind"], "sbpl_check");
        assert_eq!(wire["schema_version"], json_contract::SCHEMA_VERSION);
        assert_eq!(wire["result"]["normalized_outcome"], outcome, "{wire}");
        assert_eq!(wire["result"]["exit_code"], exit_code, "{wire}");
        assert_eq!(wire["result"]["ok"], exit_code == 0, "{wire}");
    }

    fn source_of_bytes(bytes: usize) -> String {
        // Multibyte scalars first so the byte count and the character count
        // disagree; the remainder pads to the exact byte length.
        let euros = bytes / 3;
        let mut source = "€".repeat(euros);
        source.push_str(&"x".repeat(bytes - euros * 3));
        assert_eq!(source.len(), bytes);
        assert!(source.chars().count() < bytes);
        source
    }

    #[test]
    fn input_refusals_precede_every_walk_and_native_call() {
        let cap = sbpl_imports::MAX_SBPL_SOURCE_BYTES;
        let cases: Vec<(&str, Value, &str, i64, &str)> = vec![
            (
                "unsupported format",
                json!({"format": "bytecode", "sbpl_source": "(version 1)", "params": {"A": "1"}}),
                "bad_request",
                1,
                "unsupported policy.format (expected sbpl)",
            ),
            (
                "missing source",
                json!({"format": "sbpl", "params": {"A": "1", "B": "2"}}),
                "bad_request",
                1,
                "missing policy.sbpl_source",
            ),
            (
                "null source",
                json!({"format": "sbpl", "sbpl_source": null}),
                "bad_request",
                1,
                "missing policy.sbpl_source",
            ),
            (
                "over cap",
                json!({"format": "sbpl", "sbpl_source": source_of_bytes(cap + 1), "params": {}}),
                "policy_too_large",
                1,
                "bytes; cap is",
            ),
            (
                "NUL in source",
                json!({"format": "sbpl", "sbpl_source": "(version 1)\u{0}(allow default)"}),
                "bad_request",
                1,
                "policy.sbpl_source contains NUL",
            ),
            (
                "NUL in key",
                json!({"format": "sbpl", "sbpl_source": "(version 1)", "params": {"K\u{0}EY": "v"}}),
                "bad_request",
                1,
                "a policy.params key contains NUL",
            ),
            (
                "NUL in value",
                json!({"format": "sbpl", "sbpl_source": "(version 1)", "params": {"ROOT": "a\u{0}b"}}),
                "bad_request",
                1,
                "policy.params value for ROOT contains NUL",
            ),
        ];
        for (label, policy, outcome, exit_code, error) in cases {
            let expected_present = policy.get("params").is_some_and(|p| !p.is_null());
            let expected_count = policy["params"].as_object().map_or(0, |p| p.len());
            let mut native = FakeNative::new(true, None);
            let (wire, walked) = run_with(&mut native, policy);
            assert_verdict(&wire, outcome, exit_code);
            let text = wire["result"]["error"].as_str().unwrap();
            assert!(text.contains(error), "{label}: {text}");
            assert!(!text.contains("a\u{0}b"), "{label}: value echoed");
            assert!(wire["data"]["compile"].is_null(), "{label}");
            assert!(wire["data"]["import_inventory"].is_null(), "{label}");
            assert!(wire["data"]["policy_sha256"].is_null(), "{label}");
            assert_eq!(wire["data"]["params_present"], expected_present, "{label}");
            assert_eq!(wire["data"]["params_count"], expected_count, "{label}");
            assert!(walked.is_empty(), "{label}: refused input was walked");
            assert!(
                native.untouched(),
                "{label}: refused input reached libsandbox"
            );
            assert!(native.release_complete());
        }
    }

    #[test]
    fn source_byte_cap_counts_utf8_bytes_not_characters() {
        let cap = sbpl_imports::MAX_SBPL_SOURCE_BYTES;
        let at_cap = source_of_bytes(cap);
        let mut native = FakeNative::new(true, None);
        let (wire, walked) = run_with(
            &mut native,
            json!({"format": "sbpl", "sbpl_source": at_cap}),
        );
        assert_verdict(&wire, "ok", 0);
        assert_eq!(walked, vec![at_cap.clone()]);
        assert_eq!(native.compile_calls.len(), 1);
        assert_eq!(native.compile_calls[0].0, at_cap.as_bytes());
        assert!(native.release_complete());

        // One byte over, with fewer characters than the cap: refused before
        // the walk and before any native call.
        let mut over = String::from("€");
        over.push_str(&"x".repeat(cap - 2));
        assert_eq!(over.len(), cap + 1);
        assert!(over.chars().count() < cap);
        let mut native = FakeNative::new(true, None);
        let (wire, walked) = run_with(&mut native, json!({"format": "sbpl", "sbpl_source": over}));
        assert_verdict(&wire, "policy_too_large", 1);
        assert_eq!(
            wire["result"]["error"],
            format!(
                "policy.sbpl_source is {} bytes; cap is {cap} bytes",
                cap + 1
            )
        );
        assert!(walked.is_empty());
        assert!(native.untouched());
    }

    #[test]
    fn absent_null_and_empty_params_compile_without_setup_calls() {
        let source = "(version 1)\n(allow default)\n";
        for (label, policy, present) in [
            (
                "absent",
                json!({"format": "sbpl", "sbpl_source": source}),
                false,
            ),
            (
                "null",
                json!({"format": "sbpl", "sbpl_source": source, "params": null}),
                false,
            ),
            (
                "empty",
                json!({"format": "sbpl", "sbpl_source": source, "params": {}}),
                true,
            ),
        ] {
            let mut native = FakeNative::new(true, None);
            let (wire, walked) = run_with(&mut native, policy);
            assert_verdict(&wire, "ok", 0);
            assert_eq!(wire["data"]["params_present"], present, "{label}");
            assert_eq!(wire["data"]["params_count"], 0, "{label}");
            assert_eq!(
                wire["data"]["compile"],
                json!({"stage": "compile", "ok": true, "error": null}),
                "{label}"
            );
            assert!(wire["result"]["error"].is_null(), "{label}");
            assert_eq!(native.create_calls, 0, "{label}");
            assert!(native.set_calls.is_empty(), "{label}");
            assert_eq!(
                native.compile_calls,
                vec![(source.as_bytes().to_vec(), false)]
            );
            assert_eq!(native.freed_profiles, 1, "{label}");
            assert!(native.release_complete(), "{label}");
            // A performed walk with no imports is an object with empty records,
            // distinct from the null of a refusal.
            assert_eq!(walked, vec![source.to_string()]);
            let inventory = &wire["data"]["import_inventory"];
            assert_eq!(inventory["records"], json!([]), "{label}");
            assert_eq!(inventory["truncated"], false, "{label}");
            assert!(inventory["cycle"].is_null(), "{label}");
            assert_eq!(
                inventory["policy_closure_sha256"],
                sbpl_imports::compute_closure_hash(source, &[]),
                "{label}"
            );
            assert_eq!(
                wire["data"]["policy_sha256"],
                sbpl_imports::sha256_hex(source),
                "{label}"
            );
        }
    }

    #[test]
    fn params_create_failure_is_a_setup_error_before_any_set_or_compile() {
        let mut native = FakeNative::new(true, None);
        native.create = vec![false];
        let (wire, walked) = run_with(
            &mut native,
            json!({"format": "sbpl", "sbpl_source": "(version 1)", "params": {"ROOT": "/tmp"}}),
        );
        assert_verdict(&wire, "setup_error", 1);
        assert_eq!(
            wire["data"]["compile"],
            json!({"stage": "params_create", "ok": false, "error": "sandbox_create_params returned NULL"})
        );
        assert_eq!(
            wire["result"]["error"],
            "sandbox_create_params returned NULL"
        );
        assert_eq!(native.create_calls, 1);
        assert!(native.set_calls.is_empty());
        assert!(native.compile_calls.is_empty());
        assert_eq!(
            native.freed_params, 0,
            "nothing to free after a NULL create"
        );
        assert!(native.release_complete());
        assert_eq!(walked.len(), 1, "admitted input is walked before setup");
        assert!(wire["data"]["import_inventory"].is_object());
    }

    #[test]
    fn a_later_set_failure_names_the_call_and_key_without_the_value() {
        let mut native = FakeNative::new(true, None);
        native.set = vec![0, 97];
        let (wire, _) = run_with(
            &mut native,
            json!({"format": "sbpl", "sbpl_source": "(version 1)",
                "params": {"ALPHA": "/first", "BETA": "secret-value"}}),
        );
        assert_verdict(&wire, "setup_error", 1);
        assert_eq!(wire["data"]["compile"]["stage"], "param_set");
        assert_eq!(wire["data"]["compile"]["ok"], false);
        let error = wire["data"]["compile"]["error"].as_str().unwrap();
        assert_eq!(wire["result"]["error"], error);
        assert!(
            error.contains("sandbox_set_param")
                && error.contains("BETA")
                && error.contains("rc=97"),
            "{error}"
        );
        assert!(!error.contains("secret-value"), "value echoed: {error}");
        assert_eq!(
            native.set_calls,
            vec![
                ("ALPHA".to_string(), "/first".to_string()),
                ("BETA".to_string(), "secret-value".to_string())
            ]
        );
        assert!(
            native.compile_calls.is_empty(),
            "no compiler call after a failed set"
        );
        assert_eq!(native.freed_params, 1);
        assert!(native.release_complete());
    }

    #[test]
    fn compiler_diagnostics_are_copied_unchanged_into_both_error_fields() {
        for diagnostic in ["controlled diagnostic: expected pattern, got boolean ✓", ""] {
            let mut native = FakeNative::new(false, Some(diagnostic));
            let (wire, _) = run_with(
                &mut native,
                json!({"format": "sbpl", "sbpl_source": "(version 1)", "params": {"ROOT": "/tmp"}}),
            );
            assert_verdict(&wire, "compile_error", 1);
            assert_eq!(
                wire["data"]["compile"],
                json!({"stage": "compile", "ok": false, "error": diagnostic}),
                "{diagnostic:?}"
            );
            assert_eq!(wire["result"]["error"], diagnostic, "{diagnostic:?}");
            assert_eq!(native.compile_calls.len(), 1);
            assert!(
                native.compile_calls[0].1,
                "the params object reached the compiler"
            );
            assert_eq!(native.freed_errors, 1, "{diagnostic:?}");
            assert_eq!(native.freed_params, 1, "{diagnostic:?}");
            assert_eq!(native.freed_profiles, 0, "{diagnostic:?}");
            assert!(native.release_complete(), "{diagnostic:?}");
        }
    }

    #[test]
    fn a_null_profile_without_a_diagnostic_is_a_compile_error_with_the_helper_summary() {
        let mut native = FakeNative::new(false, None);
        let (wire, _) = run_with(
            &mut native,
            json!({"format": "sbpl", "sbpl_source": "(version 1)", "params": {"ROOT": "/tmp"}}),
        );
        assert_verdict(&wire, "compile_error", 1);
        assert_eq!(
            wire["data"]["compile"],
            json!({"stage": "compile", "ok": false, "error": null})
        );
        assert_eq!(wire["result"]["error"], NO_DIAGNOSTIC_SUMMARY);
        assert_eq!(native.compile_calls.len(), 1);
        assert_eq!(native.freed_errors, 0);
        assert_eq!(native.freed_params, 1);
        assert!(native.release_complete());
    }

    #[test]
    fn a_profile_succeeds_alone_and_fails_beside_an_error_buffer() {
        let policy =
            json!({"format": "sbpl", "sbpl_source": "(version 1)", "params": {"ROOT": "/tmp"}});
        let mut native = FakeNative::new(true, None);
        let (wire, _) = run_with(&mut native, policy.clone());
        assert_verdict(&wire, "ok", 0);
        assert_eq!(
            wire["data"]["compile"],
            json!({"stage": "compile", "ok": true, "error": null})
        );
        assert!(wire["result"]["error"].is_null());
        assert_eq!(
            (
                native.freed_profiles,
                native.freed_params,
                native.freed_errors
            ),
            (1, 1, 0)
        );
        assert!(native.release_complete());

        let mut native = FakeNative::new(true, Some("profile and diagnostic together"));
        let (wire, _) = run_with(&mut native, policy);
        assert_verdict(&wire, "compile_error", 1);
        assert_eq!(
            wire["data"]["compile"],
            json!({"stage": "compile", "ok": false, "error": "profile and diagnostic together"})
        );
        assert_eq!(wire["result"]["error"], "profile and diagnostic together");
        assert_eq!(
            (
                native.freed_profiles,
                native.freed_params,
                native.freed_errors
            ),
            (1, 1, 1)
        );
        assert!(native.release_complete());
    }

    fn record(name: &str, error: Option<&str>) -> sbpl_imports::ImportRecord {
        sbpl_imports::ImportRecord {
            name: name.into(),
            resolved_path: error.is_none().then(|| format!("/constructed/{name}")),
            sha256: error.is_none().then(|| "e".repeat(64)),
            size_bytes: error.is_none().then_some(3),
            mtime_unix: error.is_none().then_some(1),
            error: error.map(str::to_string),
        }
    }

    fn inventory_variant(label: &str) -> sbpl_imports::ResolvedImports {
        let mut resolved = sbpl_imports::ResolvedImports {
            records: vec![record("ok.sb", None)],
            truncated: false,
            exceeded: None,
            nonliteral_imports: false,
            cycle: None,
            failure: None,
        };
        match label {
            "errors" => {
                resolved
                    .records
                    .push(record("missing.sb", Some("not found in search path")));
                resolved.failure = Some("not found in search path".into());
            }
            "truncated" => {
                resolved.truncated = true;
                resolved.exceeded = Some("depth".into());
            }
            "cycle" => resolved.cycle = Some(vec!["a.sb".into(), "b.sb".into(), "a.sb".into()]),
            _ => {}
        }
        resolved
    }

    #[test]
    fn inventory_findings_survive_in_their_group_and_never_change_the_verdict() {
        let source = "(version 1)\n(import \"ok.sb\")\n";
        for (profile, diagnostic, outcome, exit_code) in [
            (true, None, "ok", 0),
            (
                false,
                Some("controlled compiler failure"),
                "compile_error",
                1,
            ),
        ] {
            let mut baseline: Option<(Value, Value)> = None;
            for label in ["clean", "errors", "truncated", "cycle"] {
                let mut native = FakeNative::new(profile, diagnostic);
                let mut walks = 0;
                let wire = {
                    let mut walk = |seen: &str| {
                        assert_eq!(seen, source);
                        walks += 1;
                        inventory_variant(label)
                    };
                    wire(&check(
                        &request(json!({"format": "sbpl", "sbpl_source": source})),
                        &mut native,
                        &mut walk,
                    ))
                };
                assert_scan_free(&wire);
                assert_eq!(walks, 1, "{label}");
                assert_verdict(&wire, outcome, exit_code);
                assert!(native.release_complete(), "{label}");
                // The same controlled native result: the same result block
                // and compile record for every inventory variant.
                let verdict = (wire["result"].clone(), wire["data"]["compile"].clone());
                match &baseline {
                    None => baseline = Some(verdict),
                    Some(first) => assert_eq!(first, &verdict, "{label}"),
                }
                let expected = inventory_variant(label);
                let inventory = &wire["data"]["import_inventory"];
                assert_eq!(
                    inventory["records"],
                    serde_json::to_value(&expected.records).unwrap(),
                    "{label}"
                );
                assert_eq!(inventory["truncated"], expected.truncated, "{label}");
                assert_eq!(inventory["cycle"], json!(expected.cycle), "{label}");
                assert_eq!(
                    inventory["policy_closure_sha256"],
                    sbpl_imports::compute_closure_hash(source, &expected.records),
                    "{label}"
                );
                if label == "errors" {
                    assert!(inventory["records"][1]["sha256"].is_null());
                    assert_eq!(inventory["records"][1]["error"], "not found in search path");
                }
            }
        }
    }

    /// The check envelope with every field present, through the frame `main`
    /// prints. The controller's envelope golden records this subtree from a
    /// fixture in `run_flow.rs` (`data.policy_check.envelope`); the two must agree.
    #[test]
    fn check_shape_agrees_with_the_envelope_golden() {
        let data = CheckData {
            policy_format: "sbpl".into(),
            policy_sha256: Some("f".repeat(64)),
            macos_build_version: Some("23J220".into()),
            params_present: true,
            params_count: 1,
            compile: Some(CompileRecord {
                stage: Stage::Compile,
                ok: true,
                error: Some("constructed".into()),
            }),
            import_inventory: Some(ImportInventory {
                records: vec![sbpl_imports::ImportRecord {
                    name: "system.sb".into(),
                    resolved_path: Some("/System/Library/Sandbox/Profiles/system.sb".into()),
                    sha256: Some("f".repeat(64)),
                    size_bytes: Some(1),
                    mtime_unix: Some(1),
                    error: Some("constructed".into()),
                }],
                truncated: false,
                cycle: Some(vec!["a".into(), "b".into()]),
                policy_closure_sha256: "f".repeat(64),
            }),
        };
        let result = json_contract::JsonResult {
            ok: true,
            rc: Some(0),
            exit_code: Some(0),
            normalized_outcome: Some("ok".into()),
            errno: Some(0),
            error: Some("constructed".into()),
            stderr: Some(String::new()),
            stdout: Some(String::new()),
        };
        let text = json_contract::render_envelope("sbpl_check", result, &data).unwrap();
        let wire: serde_json::Value = serde_json::from_str(&text).unwrap();
        assert_scan_free(&wire);
        let mut emitted = shape::Shape::new();
        shape::collect(&wire, "sbpl_check", &[], &mut emitted).unwrap();
        let golden: serde_json::Value = serde_json::from_str(include_str!(
            "../../../tests/fixtures/contract/envelope_shape.json"
        ))
        .unwrap();
        let recorded =
            shape::golden_subtree(&golden, "envelope.data.policy_check.envelope", "sbpl_check");
        assert!(
            !recorded.is_empty(),
            "the envelope golden records no sbpl-check envelope"
        );
        shape::same_shape(&recorded, &emitted).unwrap();
    }

    #[test]
    fn documented_helper_limits() {
        let manifest: serde_json::Value =
            serde_json::from_str(include_str!("../../../docs/limits.json")).unwrap();
        let owned: BTreeMap<&str, usize> = manifest["limits"]
            .as_array()
            .unwrap()
            .iter()
            .filter(|row| {
                row["checks"].as_array().unwrap().iter().any(|check| {
                    check["path"] == "controller/src/bin/sbpl-check.rs" && check["kind"] == "value"
                })
            })
            .map(|row| {
                (
                    row["id"].as_str().unwrap(),
                    row["value"].as_u64().unwrap() as usize,
                )
            })
            .collect();
        assert_eq!(
            owned,
            BTreeMap::from([
                ("helper_source", sbpl_imports::MAX_SBPL_SOURCE_BYTES),
                ("helper_import_depth", sbpl_imports::IMPORT_MAX_DEPTH),
                ("helper_import_count", sbpl_imports::IMPORT_MAX_COUNT),
            ])
        );
    }
}
