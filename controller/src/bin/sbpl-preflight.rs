//! SBPL preflight compiler for host-side diagnostics.
//!
//! This tool parses a PolicyWitness request JSON, extracts the SBPL policy,
//! and runs sandbox_compile_string to catch syntax and parameter errors.

#[path = "../json_contract.rs"]
#[allow(dead_code)]
mod json_contract;

use serde::Deserialize;
use serde::Serialize;
use sha2::{Digest, Sha256};
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
    fn sandbox_set_param(params: *mut c_void, key: *const c_char, value: *const c_char)
        -> c_int;
    fn sandbox_free_params(params: *mut c_void);
}

#[derive(Deserialize)]
struct PreflightRequest {
    policy: PreflightPolicy,
}

#[derive(Deserialize)]
struct PreflightPolicy {
    format: String,
    sbpl_source: Option<String>,
    params: Option<BTreeMap<String, String>>,
}

#[derive(Serialize)]
struct PreflightData {
    policy_format: String,
    policy_sha256: Option<String>,
    params_present: bool,
    params_count: usize,
    compiled: bool,
    compile_error: Option<String>,
}

fn usage() -> String {
    "\
usage:
  sbpl-preflight --request <request.json>

notes:
  - reads request.json and compiles policy.sbpl_source
  - prints a JSON envelope with compile status and error details"
        .to_string()
}

fn sha256_hex(data: &str) -> String {
    let digest = Sha256::digest(data.as_bytes());
    digest.iter().map(|b| format!("{b:02x}")).collect()
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
                let rc = unsafe {
                    sandbox_set_param(obj, key_c.as_ptr(), value_c.as_ptr())
                };
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

    let text = match std::fs::read_to_string(&request_path) {
        Ok(text) => text,
        Err(err) => {
            eprintln!("failed to read request: {err}");
            std::process::exit(2);
        }
    };

    let parsed: PreflightRequest = match serde_json::from_str(&text) {
        Ok(req) => req,
        Err(err) => {
            eprintln!("failed to parse request.json: {err}");
            std::process::exit(2);
        }
    };

    let format = parsed.policy.format;
    let params = parsed.policy.params.as_ref();

    if format != "sbpl" {
        let data = PreflightData {
            policy_format: format,
            policy_sha256: None,
            params_present: params.is_some(),
            params_count: params.map(|p| p.len()).unwrap_or(0),
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
        let _ = json_contract::print_envelope("sbpl_preflight", result, &data);
        std::process::exit(1);
    }

    let source = match parsed.policy.sbpl_source.as_ref() {
        Some(src) => src,
        None => {
            let data = PreflightData {
                policy_format: format,
                policy_sha256: None,
                params_present: params.is_some(),
                params_count: params.map(|p| p.len()).unwrap_or(0),
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
            let _ = json_contract::print_envelope("sbpl_preflight", result, &data);
            std::process::exit(1);
        }
    };

    let policy_sha = sha256_hex(source);
    let compile_result = compile_sbpl(source, params);
    match compile_result {
        Ok(()) => {
            let data = PreflightData {
                policy_format: format,
                policy_sha256: Some(policy_sha),
                params_present: params.is_some(),
                params_count: params.map(|p| p.len()).unwrap_or(0),
                compiled: true,
                compile_error: None,
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
            let _ = json_contract::print_envelope("sbpl_preflight", result, &data);
            std::process::exit(0);
        }
        Err(err) => {
            let data = PreflightData {
                policy_format: format,
                policy_sha256: Some(policy_sha),
                params_present: params.is_some(),
                params_count: params.map(|p| p.len()).unwrap_or(0),
                compiled: false,
                compile_error: Some(err.clone()),
            };
            let result = json_contract::JsonResult {
                ok: false,
                rc: None,
                exit_code: Some(1),
                normalized_outcome: Some("compile_error".to_string()),
                errno: None,
                error: Some(err),
                stderr: None,
                stdout: None,
            };
            let _ = json_contract::print_envelope("sbpl_preflight", result, &data);
            std::process::exit(1);
        }
    }
}
