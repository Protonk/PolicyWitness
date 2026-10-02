//! `sbpl-check`: host-side SBPL compile-check for diagnostics.
//!
//! This tool parses a PolicyWitness request JSON, extracts the SBPL policy,
//! and runs sandbox_compile_string to catch syntax and parameter errors.
//!
//! It also scans the source for `(param "NAME")` references and reports any
//! that are not supplied in `policy.params`. Libsandbox accepts an unbound
//! param by falling back to a sentinel false, which then trips a type check
//! deep in the compile pipeline with a message like "expected pattern, got
//! boolean" — useless to anyone debugging their policy. The pre-validation
//! lets us surface the missing names directly.

#[path = "../json_contract.rs"]
#[allow(dead_code)]
mod json_contract;

#[path = "../host_facts.rs"]
mod host_facts;
#[path = "../sbpl_imports.rs"]
mod sbpl_imports;
#[path = "../sbpl_lex.rs"]
mod sbpl_lex;

use serde::Deserialize;
use serde::Serialize;
use std::collections::{BTreeMap, BTreeSet};
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

#[derive(Serialize)]
struct CheckData {
    policy_format: String,
    policy_sha256: Option<String>,
    policy_closure_sha256: Option<String>,
    macos_build_version: Option<String>,
    params_present: bool,
    params_count: usize,
    params_referenced: Vec<String>,
    params_supplied: Vec<String>,
    params_missing: Vec<String>,
    params_unused: Vec<String>,
    /// False when the surface lexer saw `(param X)` with X non-literal — the
    /// reference is macro-indirected and beyond static scanning. Consumers
    /// must treat `params_missing: []` together with `params_scan_complete:
    /// false` as "we don't know" rather than "nothing required".
    params_scan_complete: bool,
    imports: Vec<sbpl_imports::ImportRecord>,
    imports_truncated: bool,
    imports_cycle: Option<Vec<String>>,
    compiled: bool,
    compile_error: Option<String>,
}

struct ParamDiff {
    referenced: Vec<String>,
    supplied: Vec<String>,
    missing: Vec<String>,
    unused: Vec<String>,
    scan_complete: bool,
}

fn compute_param_diff(source: &str, supplied: Option<&BTreeMap<String, String>>) -> ParamDiff {
    let scan = sbpl_lex::param_scan(source);
    let supplied_set: BTreeSet<String> = supplied
        .map(|p| p.keys().cloned().collect())
        .unwrap_or_default();
    let missing: Vec<String> = scan.refs.difference(&supplied_set).cloned().collect();
    let unused: Vec<String> = supplied_set.difference(&scan.refs).cloned().collect();
    ParamDiff {
        referenced: scan.refs.into_iter().collect(),
        supplied: supplied_set.into_iter().collect(),
        missing,
        unused,
        scan_complete: scan.scan_complete,
    }
}

fn missing_param_error(missing: &[String]) -> String {
    // Truncate the list so a profile that references many unbound params
    // doesn't produce a multi-kilobyte error string.
    const MAX_NAMES: usize = 16;
    let shown: Vec<&str> = missing.iter().take(MAX_NAMES).map(String::as_str).collect();
    let suffix = if missing.len() > MAX_NAMES {
        format!(" (+{} more)", missing.len() - MAX_NAMES)
    } else {
        String::new()
    };
    format!(
        "policy references params not supplied: {}{}",
        shown.join(", "),
        suffix
    )
}

fn empty_param_diff() -> ParamDiff {
    ParamDiff {
        referenced: Vec::new(),
        supplied: Vec::new(),
        missing: Vec::new(),
        unused: Vec::new(),
        scan_complete: true,
    }
}

fn usage() -> String {
    "\
usage:
  sbpl-check --request <request.json|->

notes:
  - reads the request JSON from the named file, or from stdin to EOF when the value is `-`
  - compiles policy.sbpl_source with the host's libsandbox and inventories its literal imports
  - prints a JSON envelope with compile status and error details"
        .to_string()
}

fn compile_sbpl(source: &str, params: Option<&BTreeMap<String, String>>) -> Result<(), String> {
    let mut param_cstrings: Vec<CString> = Vec::new();
    let params_obj: *mut c_void = if let Some(params) = params {
        if params.is_empty() {
            std::ptr::null_mut()
        } else {
            let obj = unsafe { sandbox_create_params() };
            if obj.is_null() {
                return Err("sandbox_create_params returned NULL".to_string());
            }
            for (key, value) in params.iter() {
                let key_c = CString::new(key.as_str())
                    .map_err(|_| format!("invalid param key (NUL): {key}"))?;
                let value_c = CString::new(value.as_str())
                    .map_err(|_| format!("invalid param value for {key} (NUL)"))?;
                let rc = unsafe { sandbox_set_param(obj, key_c.as_ptr(), value_c.as_ptr()) };
                if rc != 0 {
                    unsafe { sandbox_free_params(obj) };
                    return Err(format!("sandbox_set_param failed for {key}: rc={rc}"));
                }
                param_cstrings.push(key_c);
                param_cstrings.push(value_c);
            }
            obj
        }
    } else {
        std::ptr::null_mut()
    };

    let mut err_buf: *mut c_char = std::ptr::null_mut();
    let profile = unsafe {
        let cstr = CString::new(source).map_err(|_| "sbpl_source contains NUL".to_string())?;
        sandbox_compile_string(cstr.as_ptr(), params_obj, &mut err_buf)
    };

    if !err_buf.is_null() {
        let message = unsafe {
            let msg = CStr::from_ptr(err_buf).to_string_lossy().to_string();
            sandbox_free_error(err_buf);
            msg
        };
        if !profile.is_null() {
            unsafe { sandbox_free_profile(profile) };
        }
        if !params_obj.is_null() {
            unsafe { sandbox_free_params(params_obj) };
        }
        return Err(format!("sandbox_compile_string failed: {message}"));
    }

    if profile.is_null() {
        if !params_obj.is_null() {
            unsafe { sandbox_free_params(params_obj) };
        }
        return Err("sandbox_compile_string failed (no profile and no error)".to_string());
    }

    unsafe { sandbox_free_profile(profile) };
    if !params_obj.is_null() {
        unsafe { sandbox_free_params(params_obj) };
    }
    Ok(())
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

    let format = parsed.policy.format;
    let params = parsed.policy.params.as_ref();

    if format != "sbpl" {
        let diff = empty_param_diff();
        let data = CheckData {
            policy_format: format,
            policy_sha256: None,
            policy_closure_sha256: None,
            macos_build_version: host_facts::macos_build_version(),
            params_present: params.is_some(),
            params_count: params.map(|p| p.len()).unwrap_or(0),
            params_referenced: diff.referenced,
            params_supplied: diff.supplied,
            params_missing: diff.missing,
            params_unused: diff.unused,
            params_scan_complete: diff.scan_complete,
            imports: Vec::new(),
            imports_truncated: false,
            imports_cycle: None,
            compiled: false,
            compile_error: Some("unsupported policy.format (expected sbpl)".to_string()),
        };
        let result = json_contract::JsonResult {
            ok: false,
            rc: None,
            exit_code: Some(1),
            normalized_outcome: Some("unsupported_format".to_string()),
            errno: None,
            error: Some("unsupported policy.format (expected sbpl)".to_string()),
            stderr: None,
            stdout: None,
        };
        let _ = json_contract::print_envelope("sbpl_check", result, &data);
        std::process::exit(1);
    }

    let source = match parsed.policy.sbpl_source.as_ref() {
        Some(src) => src,
        None => {
            let diff = empty_param_diff();
            let data = CheckData {
                policy_format: format,
                policy_sha256: None,
                policy_closure_sha256: None,
                macos_build_version: host_facts::macos_build_version(),
                params_present: params.is_some(),
                params_count: params.map(|p| p.len()).unwrap_or(0),
                params_referenced: diff.referenced,
                params_supplied: diff.supplied,
                params_missing: diff.missing,
                params_unused: diff.unused,
                params_scan_complete: diff.scan_complete,
                imports: Vec::new(),
                imports_truncated: false,
                imports_cycle: None,
                compiled: false,
                compile_error: Some("missing policy.sbpl_source".to_string()),
            };
            let result = json_contract::JsonResult {
                ok: false,
                rc: None,
                exit_code: Some(1),
                normalized_outcome: Some("bad_policy".to_string()),
                errno: None,
                error: Some("missing policy.sbpl_source".to_string()),
                stderr: None,
                stdout: None,
            };
            let _ = json_contract::print_envelope("sbpl_check", result, &data);
            std::process::exit(1);
        }
    };

    if source.len() > sbpl_imports::MAX_SBPL_SOURCE_BYTES {
        let diff = empty_param_diff();
        let msg = format!(
            "policy.sbpl_source is {} bytes; cap is {} bytes",
            source.len(),
            sbpl_imports::MAX_SBPL_SOURCE_BYTES
        );
        let data = CheckData {
            policy_format: format,
            policy_sha256: None,
            policy_closure_sha256: None,
            macos_build_version: host_facts::macos_build_version(),
            params_present: params.is_some(),
            params_count: params.map(|p| p.len()).unwrap_or(0),
            params_referenced: diff.referenced,
            params_supplied: diff.supplied,
            params_missing: diff.missing,
            params_unused: diff.unused,
            params_scan_complete: diff.scan_complete,
            imports: Vec::new(),
            imports_truncated: false,
            imports_cycle: None,
            compiled: false,
            compile_error: Some(msg.clone()),
        };
        let result = json_contract::JsonResult {
            ok: false,
            rc: None,
            exit_code: Some(1),
            normalized_outcome: Some("policy_too_large".to_string()),
            errno: None,
            error: Some(msg),
            stderr: None,
            stdout: None,
        };
        let _ = json_contract::print_envelope("sbpl_check", result, &data);
        std::process::exit(1);
    }

    let policy_sha = sbpl_imports::sha256_hex(source);
    let diff = compute_param_diff(source, params);
    let resolved = sbpl_imports::resolve_imports(source);
    let policy_closure_sha = sbpl_imports::compute_closure_hash(source, &resolved.records);

    // Always run libsandbox so syntax errors surface alongside any missing-param
    // diagnostic. Missing params take precedence in `normalized_outcome` because
    // they explain the compile error users would otherwise see (the cryptic
    // "expected pattern, got boolean").
    let compile_result = compile_sbpl(source, params);
    let compiled = compile_result.is_ok();
    let compile_error = compile_result.err();

    let (normalized_outcome, error_msg, exit_code) = if !diff.missing.is_empty() {
        (
            "missing_params".to_string(),
            Some(missing_param_error(&diff.missing)),
            1,
        )
    } else if compiled {
        ("ok".to_string(), None, 0)
    } else {
        ("compile_error".to_string(), compile_error.clone(), 1)
    };

    let data = CheckData {
        policy_format: format,
        policy_sha256: Some(policy_sha),
        policy_closure_sha256: Some(policy_closure_sha),
        macos_build_version: host_facts::macos_build_version(),
        params_present: params.is_some(),
        params_count: params.map(|p| p.len()).unwrap_or(0),
        params_referenced: diff.referenced,
        params_supplied: diff.supplied,
        params_missing: diff.missing,
        params_unused: diff.unused,
        params_scan_complete: diff.scan_complete,
        imports: resolved.records,
        imports_truncated: resolved.truncated,
        imports_cycle: resolved.cycle,
        compiled,
        compile_error,
    };
    let result = json_contract::JsonResult {
        ok: exit_code == 0,
        rc: None,
        exit_code: Some(exit_code),
        normalized_outcome: Some(normalized_outcome),
        errno: None,
        error: error_msg,
        stderr: None,
        stdout: None,
    };
    let _ = json_contract::print_envelope("sbpl_check", result, &data);
    std::process::exit(exit_code);
}

#[cfg(test)]
mod tests {
    use super::*;

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
