//! SBPL preflight compiler for host-side diagnostics.
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

mod sbpl_lex;

use serde::Deserialize;
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::ffi::{CStr, CString};
use std::os::raw::{c_char, c_int, c_void};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::OnceLock;
use std::time::UNIX_EPOCH;

// Verified empirically on macOS 14.8.3 build 23J220 (see IMPORTS-PLAN.md §B):
// - Bare names with extension (e.g. "system.sb") resolve from the two
//   directories listed in IMPORT_SEARCH_PATHS, tried in order.
// - Names without `.sb` do NOT auto-append; libsandbox reports
//   `unable to open "foo": not found`.
// - Absolute paths (starting with `/`) are accepted as-is.
// - Imports are recursive (system.sb imports dyld-support.sb).
// - Search-order between the two directories could not be confirmed by
//   collision on this host (no overlapping filenames); the Profiles directory
//   is tried first by convention (modern signed-by-Apple location).
const IMPORT_SEARCH_PATHS: &[&str] = &[
    "/System/Library/Sandbox/Profiles",
    "/usr/share/sandbox",
];

const IMPORT_MAX_DEPTH: usize = 8;
const IMPORT_MAX_COUNT: usize = 64;

// Cap policy.sbpl_source size before handing it to the lexer or libsandbox.
// The lexer is O(n) and libsandbox would reject pathological inputs on its
// own, but bounding here gives a clean envelope error instead of a slow
// scan or a cryptic libsandbox failure. 4 MiB is far above any real-world
// hand-written profile (system.sb is ~150 KiB) and well below a level where
// a malicious request could exhaust memory.
const MAX_SBPL_SOURCE_BYTES: usize = 4 * 1024 * 1024;

// 0x1F (Information Separator One) joins the source body and the imports list
// in the closure hash so a profile that happens to contain the literal text of
// an imports manifest cannot collide with the genuine derivation. Document
// this once; do not change it without a deliberate hash-format bump.
const CLOSURE_HASH_SEPARATOR: u8 = 0x1F;

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
    policy_closure_sha256: Option<String>,
    macos_build_version: Option<String>,
    params_present: bool,
    params_count: usize,
    params_referenced: Vec<String>,
    params_supplied: Vec<String>,
    params_missing: Vec<String>,
    params_unused: Vec<String>,
    imports: Vec<ImportRecord>,
    imports_truncated: bool,
    imports_cycle: Option<Vec<String>>,
    compiled: bool,
    compile_error: Option<String>,
}

#[derive(Serialize, Clone)]
struct ImportRecord {
    /// The literal name as written in the source (`(import "NAME")`).
    name: String,
    /// Absolute path the resolver matched, or null when the name did not
    /// resolve in any of the search paths.
    resolved_path: Option<String>,
    /// Hex sha256 of the resolved file's contents, or null when unresolved.
    sha256: Option<String>,
    size_bytes: Option<u64>,
    mtime_unix: Option<i64>,
    /// Resolution error (e.g. "not found in search path", "permission denied",
    /// "depth limit exceeded"). Null on a clean resolution.
    error: Option<String>,
}

struct ParamDiff {
    referenced: Vec<String>,
    supplied: Vec<String>,
    missing: Vec<String>,
    unused: Vec<String>,
}

fn compute_param_diff(
    source: &str,
    supplied: Option<&BTreeMap<String, String>>,
) -> ParamDiff {
    let referenced = sbpl_lex::param_refs(source);
    let supplied_set: BTreeSet<String> = supplied
        .map(|p| p.keys().cloned().collect())
        .unwrap_or_default();
    let missing: Vec<String> = referenced.difference(&supplied_set).cloned().collect();
    let unused: Vec<String> = supplied_set.difference(&referenced).cloned().collect();
    ParamDiff {
        referenced: referenced.into_iter().collect(),
        supplied: supplied_set.into_iter().collect(),
        missing,
        unused,
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
    }
}

/// Resolve a bare import name against `IMPORT_SEARCH_PATHS`. Absolute paths are
/// returned as-is when the file exists. Returns the first match.
fn resolve_import_path(name: &str) -> Option<PathBuf> {
    if name.starts_with('/') {
        let abs = PathBuf::from(name);
        return if abs.exists() { Some(abs) } else { None };
    }
    for base in IMPORT_SEARCH_PATHS {
        let candidate = Path::new(base).join(name);
        if candidate.exists() {
            return Some(candidate);
        }
    }
    None
}

fn build_import_record(name: String, resolved: PathBuf) -> ImportRecord {
    let bytes = match std::fs::read(&resolved) {
        Ok(b) => b,
        Err(err) => {
            return ImportRecord {
                name,
                resolved_path: Some(resolved.display().to_string()),
                sha256: None,
                size_bytes: None,
                mtime_unix: None,
                error: Some(format!("read failed: {err}")),
            };
        }
    };
    let digest = Sha256::digest(&bytes);
    let sha = digest.iter().map(|b| format!("{b:02x}")).collect::<String>();
    let metadata = std::fs::metadata(&resolved).ok();
    let size_bytes = metadata.as_ref().map(|m| m.len());
    let mtime_unix = metadata
        .as_ref()
        .and_then(|m| m.modified().ok())
        .and_then(|t| t.duration_since(UNIX_EPOCH).ok())
        .map(|d| d.as_secs() as i64);
    ImportRecord {
        name,
        resolved_path: Some(resolved.display().to_string()),
        sha256: Some(sha),
        size_bytes,
        mtime_unix,
        error: None,
    }
}

struct ResolvedImports {
    records: Vec<ImportRecord>,
    truncated: bool,
    /// First cycle detected during the walk, expressed as the chain of import
    /// names from the closest enclosing visit down to the back-edge that
    /// closed the cycle. None when no cycle was hit.
    cycle: Option<Vec<String>>,
}

struct ResolverState {
    records: Vec<ImportRecord>,
    /// Canonical paths fully resolved at any point in the walk (incl. their
    /// transitive imports). Used for diamond dedup — recording the same file
    /// twice is noise, not a cycle.
    visited: BTreeSet<PathBuf>,
    /// Canonical paths currently mid-expansion. A child whose canonical path
    /// is in here closes a cycle.
    in_progress: Vec<PathBuf>,
    /// Names mirroring `in_progress`, kept so the reported cycle chain is
    /// in the caller's namespace rather than the resolver's filesystem form.
    in_progress_names: Vec<String>,
    truncated: bool,
    cycle: Option<Vec<String>>,
    /// Unresolved names already recorded — second sighting is silent dedup.
    unresolved_seen: BTreeSet<String>,
}

fn dfs_visit_import(name: String, depth: usize, state: &mut ResolverState) {
    if state.records.len() >= IMPORT_MAX_COUNT {
        state.truncated = true;
        return;
    }

    match resolve_import_path(&name) {
        Some(path) => {
            let canonical = std::fs::canonicalize(&path).unwrap_or_else(|_| path.clone());

            // Cycle: the canonical path is currently being expanded somewhere
            // above us in the chain. Record the first cycle we see and stop
            // expanding that branch; subsequent cycles in the same walk are
            // not recorded (the field is single-valued by contract).
            if state.in_progress.iter().any(|p| p == &canonical) {
                if state.cycle.is_none() {
                    let mut chain = state.in_progress_names.clone();
                    chain.push(name);
                    state.cycle = Some(chain);
                }
                return;
            }

            // Diamond: already fully resolved on a different path. Silent
            // skip — the existing record is authoritative.
            if !state.visited.insert(canonical.clone()) {
                return;
            }

            if depth >= IMPORT_MAX_DEPTH {
                state.truncated = true;
                state.records.push(ImportRecord {
                    name,
                    resolved_path: Some(canonical.display().to_string()),
                    sha256: None,
                    size_bytes: None,
                    mtime_unix: None,
                    error: Some(format!(
                        "depth limit exceeded ({IMPORT_MAX_DEPTH})"
                    )),
                });
                return;
            }

            let record = build_import_record(name.clone(), canonical.clone());
            let resolved_ok = record.error.is_none();
            state.records.push(record);
            if !resolved_ok {
                return;
            }

            state.in_progress.push(canonical.clone());
            state.in_progress_names.push(name);

            if let Ok(content) = std::fs::read_to_string(&canonical) {
                for child in sbpl_lex::import_refs(&content) {
                    if state.records.len() >= IMPORT_MAX_COUNT {
                        state.truncated = true;
                        break;
                    }
                    dfs_visit_import(child, depth + 1, state);
                }
            }

            state.in_progress.pop();
            state.in_progress_names.pop();
        }
        None => {
            if !state.unresolved_seen.insert(name.clone()) {
                return;
            }
            state.records.push(ImportRecord {
                name,
                resolved_path: None,
                sha256: None,
                size_bytes: None,
                mtime_unix: None,
                error: Some("not found in search path".to_string()),
            });
        }
    }
}

/// Walk the imports referenced from `source`, recursing into resolved files,
/// stopping at `IMPORT_MAX_DEPTH` and `IMPORT_MAX_COUNT`. Returns each unique
/// resolved file at most once, and reports the first cycle observed.
fn resolve_imports(source: &str) -> ResolvedImports {
    let mut state = ResolverState {
        records: Vec::new(),
        visited: BTreeSet::new(),
        in_progress: Vec::new(),
        in_progress_names: Vec::new(),
        truncated: false,
        cycle: None,
        unresolved_seen: BTreeSet::new(),
    };

    for name in sbpl_lex::import_refs(source) {
        dfs_visit_import(name, 0, &mut state);
    }

    // Sort for deterministic output: resolved-path first (when present), then
    // by name. The closure hash also sorts before hashing, so this matches.
    state.records.sort_by(|a, b| {
        a.resolved_path
            .as_deref()
            .unwrap_or("")
            .cmp(b.resolved_path.as_deref().unwrap_or(""))
            .then_with(|| a.name.cmp(&b.name))
    });
    ResolvedImports {
        records: state.records,
        truncated: state.truncated,
        cycle: state.cycle,
    }
}

/// Hash combining the user's SBPL source with the resolved imports' content
/// hashes. Reproducible iff every file we resolved is content-identical on
/// the verifying host. Imports that didn't resolve are excluded — their
/// absence is recorded in `imports[].error` for separate inspection.
///
/// The separator byte is appended unconditionally, so this hash is never
/// equal to `policy_sha256` even when the imports list is empty. That's
/// intentional: consumers tell "no imports" by checking `imports.is_empty()`,
/// not by comparing the two hashes.
fn compute_closure_hash(source: &str, imports: &[ImportRecord]) -> String {
    let mut payload: Vec<u8> = Vec::with_capacity(source.len() + 256);
    payload.extend_from_slice(source.as_bytes());
    payload.push(CLOSURE_HASH_SEPARATOR);
    let mut lines: Vec<String> = imports
        .iter()
        .filter_map(|r| match (r.resolved_path.as_ref(), r.sha256.as_ref()) {
            (Some(path), Some(sha)) => Some(format!("{path} {sha}")),
            _ => None,
        })
        .collect();
    lines.sort();
    payload.extend_from_slice(lines.join("\n").as_bytes());
    let digest = Sha256::digest(&payload);
    digest.iter().map(|b| format!("{b:02x}")).collect()
}

/// Cached `sw_vers -buildVersion` lookup. Returns None on the rare host where
/// sw_vers isn't available (e.g. CI containers); the field then serializes as
/// null and the rest of the envelope is unaffected.
fn macos_build_version() -> Option<String> {
    static CACHE: OnceLock<Option<String>> = OnceLock::new();
    CACHE
        .get_or_init(|| {
            let out = Command::new("/usr/bin/sw_vers")
                .arg("-buildVersion")
                .stdout(Stdio::piped())
                .stderr(Stdio::null())
                .output()
                .ok()?;
            if !out.status.success() {
                return None;
            }
            let text = String::from_utf8(out.stdout).ok()?;
            let trimmed = text.trim();
            if trimmed.is_empty() {
                None
            } else {
                Some(trimmed.to_string())
            }
        })
        .clone()
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
        let diff = empty_param_diff();
        let data = PreflightData {
            policy_format: format,
            policy_sha256: None,
            policy_closure_sha256: None,
            macos_build_version: macos_build_version(),
            params_present: params.is_some(),
            params_count: params.map(|p| p.len()).unwrap_or(0),
            params_referenced: diff.referenced,
            params_supplied: diff.supplied,
            params_missing: diff.missing,
            params_unused: diff.unused,
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
        let _ = json_contract::print_envelope("sbpl_preflight", result, &data);
        std::process::exit(1);
    }

    let source = match parsed.policy.sbpl_source.as_ref() {
        Some(src) => src,
        None => {
            let diff = empty_param_diff();
            let data = PreflightData {
                policy_format: format,
                policy_sha256: None,
                policy_closure_sha256: None,
                macos_build_version: macos_build_version(),
                params_present: params.is_some(),
                params_count: params.map(|p| p.len()).unwrap_or(0),
                params_referenced: diff.referenced,
                params_supplied: diff.supplied,
                params_missing: diff.missing,
                params_unused: diff.unused,
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
            let _ = json_contract::print_envelope("sbpl_preflight", result, &data);
            std::process::exit(1);
        }
    };

    if source.len() > MAX_SBPL_SOURCE_BYTES {
        let diff = empty_param_diff();
        let msg = format!(
            "policy.sbpl_source is {} bytes; cap is {} bytes",
            source.len(),
            MAX_SBPL_SOURCE_BYTES
        );
        let data = PreflightData {
            policy_format: format,
            policy_sha256: None,
            policy_closure_sha256: None,
            macos_build_version: macos_build_version(),
            params_present: params.is_some(),
            params_count: params.map(|p| p.len()).unwrap_or(0),
            params_referenced: diff.referenced,
            params_supplied: diff.supplied,
            params_missing: diff.missing,
            params_unused: diff.unused,
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
        let _ = json_contract::print_envelope("sbpl_preflight", result, &data);
        std::process::exit(1);
    }

    let policy_sha = sha256_hex(source);
    let diff = compute_param_diff(source, params);
    let resolved = resolve_imports(source);
    let policy_closure_sha = compute_closure_hash(source, &resolved.records);

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
        (
            "compile_error".to_string(),
            compile_error.clone(),
            1,
        )
    };

    let data = PreflightData {
        policy_format: format,
        policy_sha256: Some(policy_sha),
        policy_closure_sha256: Some(policy_closure_sha),
        macos_build_version: macos_build_version(),
        params_present: params.is_some(),
        params_count: params.map(|p| p.len()).unwrap_or(0),
        params_referenced: diff.referenced,
        params_supplied: diff.supplied,
        params_missing: diff.missing,
        params_unused: diff.unused,
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
    let _ = json_contract::print_envelope("sbpl_preflight", result, &data);
    std::process::exit(exit_code);
}

#[cfg(test)]
mod tests {
    use super::*;

    fn record(name: &str, path: &str, sha: &str) -> ImportRecord {
        ImportRecord {
            name: name.to_string(),
            resolved_path: Some(path.to_string()),
            sha256: Some(sha.to_string()),
            size_bytes: Some(0),
            mtime_unix: Some(0),
            error: None,
        }
    }

    fn unresolved(name: &str) -> ImportRecord {
        ImportRecord {
            name: name.to_string(),
            resolved_path: None,
            sha256: None,
            size_bytes: None,
            mtime_unix: None,
            error: Some("not found in search path".to_string()),
        }
    }

    #[test]
    fn closure_hash_is_stable_for_identical_inputs() {
        let src = "(version 1)\n(import \"a.sb\")\n";
        let imports = vec![record("a.sb", "/p/a.sb", "deadbeef")];
        let h1 = compute_closure_hash(src, &imports);
        let h2 = compute_closure_hash(src, &imports);
        assert_eq!(h1, h2);
    }

    #[test]
    fn closure_hash_changes_when_source_changes() {
        let imports = vec![record("a.sb", "/p/a.sb", "deadbeef")];
        let h1 = compute_closure_hash("(version 1)", &imports);
        let h2 = compute_closure_hash("(version 2)", &imports);
        assert_ne!(h1, h2);
    }

    #[test]
    fn closure_hash_changes_when_import_sha_changes() {
        let src = "(version 1)";
        let h1 = compute_closure_hash(src, &[record("a.sb", "/p/a.sb", "aaa")]);
        let h2 = compute_closure_hash(src, &[record("a.sb", "/p/a.sb", "bbb")]);
        assert_ne!(h1, h2);
    }

    #[test]
    fn closure_hash_is_order_invariant() {
        let src = "(version 1)";
        let order_a = vec![
            record("a.sb", "/p/a.sb", "111"),
            record("b.sb", "/p/b.sb", "222"),
        ];
        let order_b = vec![
            record("b.sb", "/p/b.sb", "222"),
            record("a.sb", "/p/a.sb", "111"),
        ];
        assert_eq!(
            compute_closure_hash(src, &order_a),
            compute_closure_hash(src, &order_b)
        );
    }

    #[test]
    fn closure_hash_excludes_unresolved_imports() {
        let src = "(version 1)";
        let resolved_only = vec![record("a.sb", "/p/a.sb", "111")];
        let with_unresolved = vec![record("a.sb", "/p/a.sb", "111"), unresolved("missing.sb")];
        // Adding an unresolved entry must not affect the closure hash — the
        // hash only covers content we actually read.
        assert_eq!(
            compute_closure_hash(src, &resolved_only),
            compute_closure_hash(src, &with_unresolved)
        );
    }

    #[test]
    fn closure_hash_differs_from_policy_sha_when_imports_resolved() {
        let src = "(version 1)";
        let policy_sha = sha256_hex(src);
        let closure = compute_closure_hash(src, &[record("a.sb", "/p/a.sb", "111")]);
        assert_ne!(policy_sha, closure);
    }

    #[test]
    fn resolve_import_path_handles_absolute() {
        // /bin/sh exists on every macOS host.
        let resolved = resolve_import_path("/bin/sh").expect("/bin/sh should resolve");
        assert_eq!(resolved, PathBuf::from("/bin/sh"));
        assert!(resolve_import_path("/nonexistent/xyz-9999").is_none());
    }

    #[test]
    fn resolve_import_path_finds_system_profile() {
        // system.sb ships in /System/Library/Sandbox/Profiles on every supported
        // macOS version. If this test fails the import search path needs a
        // re-verification (see the comment at IMPORT_SEARCH_PATHS).
        let resolved = resolve_import_path("system.sb")
            .expect("system.sb should resolve from the sandbox profile search path");
        assert!(
            resolved.starts_with("/System/Library/Sandbox/Profiles")
                || resolved.starts_with("/usr/share/sandbox"),
            "unexpected resolved path: {resolved:?}"
        );
    }

    #[test]
    fn resolve_import_path_returns_none_for_unknown_name() {
        assert!(resolve_import_path("definitely-not-a-real-profile-xyzzy.sb").is_none());
    }

    fn tmp_dir(label: &str) -> PathBuf {
        let dir = std::env::temp_dir().join(format!(
            "pw-preflight-test-{label}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir_all(&dir).expect("mkdir tmp");
        dir
    }

    #[test]
    fn resolve_imports_detects_two_node_cycle() {
        let dir = tmp_dir("cycle2");
        let a = dir.join("a.sb");
        let b = dir.join("b.sb");
        std::fs::write(&a, format!("(import \"{}\")\n", b.display())).unwrap();
        std::fs::write(&b, format!("(import \"{}\")\n", a.display())).unwrap();

        let src = format!("(version 1)\n(import \"{}\")\n", a.display());
        let resolved = resolve_imports(&src);

        let cycle = resolved.cycle.expect("expected a cycle to be reported");
        assert!(
            cycle.len() >= 2,
            "cycle chain should have at least the two participants, got {cycle:?}"
        );
        // The back-edge name (last in chain) must be one of the participants
        // and must equal a name earlier in the chain (the closing node).
        let last = cycle.last().unwrap();
        assert!(
            cycle[..cycle.len() - 1].contains(last),
            "cycle's last entry should close back to a node already in the chain: {cycle:?}"
        );

        // Both files were still recorded, and dfs didn't crash or loop.
        assert!(
            resolved.records.iter().any(|r| r.name.ends_with("a.sb")),
            "a.sb should appear in records"
        );
        assert!(
            resolved.records.iter().any(|r| r.name.ends_with("b.sb")),
            "b.sb should appear in records"
        );

        std::fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn resolve_imports_no_cycle_for_diamond() {
        // a imports b and c; both b and c import d. d is visited via two
        // distinct paths but that's a diamond, not a cycle.
        let dir = tmp_dir("diamond");
        let a = dir.join("a.sb");
        let b = dir.join("b.sb");
        let c = dir.join("c.sb");
        let d = dir.join("d.sb");
        std::fs::write(
            &a,
            format!(
                "(import \"{}\")\n(import \"{}\")\n",
                b.display(),
                c.display()
            ),
        )
        .unwrap();
        std::fs::write(&b, format!("(import \"{}\")\n", d.display())).unwrap();
        std::fs::write(&c, format!("(import \"{}\")\n", d.display())).unwrap();
        std::fs::write(&d, "(allow default)\n").unwrap();

        let src = format!("(import \"{}\")\n", a.display());
        let resolved = resolve_imports(&src);

        assert!(
            resolved.cycle.is_none(),
            "diamond import shape must not be reported as a cycle, got {:?}",
            resolved.cycle
        );
        // d should be recorded exactly once.
        let d_count = resolved
            .records
            .iter()
            .filter(|r| r.name.ends_with("d.sb"))
            .count();
        assert_eq!(d_count, 1, "diamond visit should dedup d.sb");

        std::fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn resolve_imports_truncates_on_count_cap() {
        // Generate a chain of imports longer than IMPORT_MAX_COUNT to verify
        // the count-cap path sets truncated.
        let dir = tmp_dir("count-cap");
        let n = IMPORT_MAX_COUNT + 5;
        for i in 0..n {
            let p = dir.join(format!("f{i}.sb"));
            let body = if i + 1 < n {
                let next = dir.join(format!("f{}.sb", i + 1));
                format!("(import \"{}\")\n", next.display())
            } else {
                "(allow default)\n".to_string()
            };
            std::fs::write(&p, body).unwrap();
        }
        let src = format!("(import \"{}\")\n", dir.join("f0.sb").display());
        let resolved = resolve_imports(&src);
        assert!(resolved.truncated, "count cap should set truncated=true");
        assert!(
            resolved.records.len() <= IMPORT_MAX_COUNT + 1,
            "should not exceed cap meaningfully, got {} records",
            resolved.records.len()
        );

        std::fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn resolve_imports_truncates_on_depth_cap() {
        // Build a strictly nested chain deeper than IMPORT_MAX_DEPTH, kept
        // well under the count cap so the depth path is what fires.
        let dir = tmp_dir("depth-cap");
        let n = IMPORT_MAX_DEPTH + 3;
        for i in 0..n {
            let p = dir.join(format!("d{i}.sb"));
            let body = if i + 1 < n {
                let next = dir.join(format!("d{}.sb", i + 1));
                format!("(import \"{}\")\n", next.display())
            } else {
                "(allow default)\n".to_string()
            };
            std::fs::write(&p, body).unwrap();
        }
        let src = format!("(import \"{}\")\n", dir.join("d0.sb").display());
        let resolved = resolve_imports(&src);
        assert!(
            resolved.truncated,
            "depth cap should set truncated=true (records: {})",
            resolved.records.len()
        );
        let depth_errors: Vec<_> = resolved
            .records
            .iter()
            .filter(|r| r.error.as_deref().unwrap_or("").contains("depth limit"))
            .collect();
        assert!(
            !depth_errors.is_empty(),
            "expected at least one depth-limit error record"
        );

        std::fs::remove_dir_all(&dir).ok();
    }
}
