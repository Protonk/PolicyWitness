//! SBPL import inventory and closure hashing.
//!
//! Shared by the `sbpl-check` diagnostic helper and the controller: both walk
//! the literal `(import "NAME")` closure of an SBPL source under the same
//! search paths and bounds, and derive the same closure hash from the bytes
//! they read. Neither identifies what the worker's compiler read; macro
//! evaluation is outside this scan.

use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use std::path::{Path, PathBuf};
use std::time::UNIX_EPOCH;

use crate::sbpl_lex;

// Verified empirically on macOS 14.8.3 build 23J220:
// - Bare names with extension (e.g. "system.sb") resolve from the two
//   directories listed in IMPORT_SEARCH_PATHS, tried in order.
// - Names without `.sb` do NOT auto-append; libsandbox reports
//   `unable to open "foo": not found`.
// - Absolute paths (starting with `/`) are accepted as-is.
// - Imports are recursive (system.sb imports dyld-support.sb).
// - Search-order between the two directories could not be confirmed by
//   collision on this host (no overlapping filenames); the Profiles directory
//   is tried first by convention (modern signed-by-Apple location).
pub const IMPORT_SEARCH_PATHS: &[&str] =
    &["/System/Library/Sandbox/Profiles", "/usr/share/sandbox"];

pub const IMPORT_MAX_DEPTH: usize = 8;
pub const IMPORT_MAX_COUNT: usize = 64;

// Cap policy.sbpl_source size before handing it to the lexer or libsandbox.
// The lexer is O(n) and libsandbox would reject pathological inputs on its
// own, but bounding here gives a clean envelope error instead of a slow
// scan or a cryptic libsandbox failure. 4 MiB is far above any real-world
// hand-written profile (system.sb is ~150 KiB) and well below a level where
// a malicious request could exhaust memory.
pub const MAX_SBPL_SOURCE_BYTES: usize = 4 * 1024 * 1024;

// 0x1F (Information Separator One) joins the source body and the imports list
// in the closure hash so a profile that happens to contain the literal text of
// an imports manifest cannot collide with the genuine derivation. Document
// this once; do not change it without a deliberate hash-format bump.
const CLOSURE_HASH_SEPARATOR: u8 = 0x1F;

#[derive(serde::Serialize, Clone, Debug)]
pub struct ImportRecord {
    /// The literal name as written in the source (`(import "NAME")`).
    pub name: String,
    /// Absolute path the resolver matched, or null when the name did not
    /// resolve in any of the search paths.
    pub resolved_path: Option<String>,
    /// Hex sha256 of the resolved file's contents, or null when unresolved.
    pub sha256: Option<String>,
    pub size_bytes: Option<u64>,
    pub mtime_unix: Option<i64>,
    /// Resolution error (e.g. "not found in search path", "permission denied",
    /// "depth limit exceeded"). Null on a clean resolution.
    pub error: Option<String>,
}

pub fn sha256_hex(data: &str) -> String {
    let digest = Sha256::digest(data.as_bytes());
    digest.iter().map(|b| format!("{b:02x}")).collect()
}

/// Resolve a bare import name against `IMPORT_SEARCH_PATHS`. Absolute paths are
/// returned as-is when the file exists. Returns the first match.
pub fn resolve_import_path(name: &str) -> Option<PathBuf> {
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

fn build_import_record(name: String, resolved: PathBuf) -> (ImportRecord, Option<Vec<u8>>) {
    let bytes = match read_regular_file(&resolved) {
        Ok(b) => b,
        Err(err) => {
            return (
                ImportRecord {
                    name,
                    resolved_path: Some(resolved.display().to_string()),
                    sha256: None,
                    size_bytes: None,
                    mtime_unix: None,
                    error: Some(err),
                },
                None,
            );
        }
    };
    let digest = Sha256::digest(&bytes);
    let sha = digest
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect::<String>();
    let metadata = std::fs::metadata(&resolved).ok();
    let size_bytes = metadata.as_ref().map(|m| m.len());
    let mtime_unix = metadata
        .as_ref()
        .and_then(|m| m.modified().ok())
        .and_then(|t| t.duration_since(UNIX_EPOCH).ok())
        .map(|d| d.as_secs() as i64);
    (
        ImportRecord {
            name,
            resolved_path: Some(resolved.display().to_string()),
            sha256: Some(sha),
            size_bytes,
            mtime_unix,
            error: None,
        },
        Some(bytes),
    )
}

/// Two binaries include this module by path and each reads a subset of these
/// fields: sbpl-check reports `truncated`; the controller dossier reports
/// `exceeded` and `nonliteral_imports`.
#[allow(dead_code)]
pub struct ResolvedImports {
    pub records: Vec<ImportRecord>,
    /// True when a bound stopped the traversal; `exceeded` names which one.
    pub truncated: bool,
    /// The first bound hit, `depth` or `count`, or None.
    pub exceeded: Option<String>,
    /// True when some `(import ...)` form in the scanned sources carried a
    /// nonliteral argument the scanner could not follow.
    pub nonliteral_imports: bool,
    /// First cycle detected during the walk, expressed as the chain of import
    /// names from the closest enclosing visit down to the back-edge that
    /// closed the cycle. None when no cycle was hit.
    pub cycle: Option<Vec<String>>,
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
    exceeded: Option<String>,
    nonliteral_imports: bool,
    cycle: Option<Vec<String>>,
    /// Unresolved names already recorded — second sighting is silent dedup.
    unresolved_seen: BTreeSet<String>,
}

fn exceed(state: &mut ResolverState, bound: &str) {
    state.truncated = true;
    if state.exceeded.is_none() {
        state.exceeded = Some(bound.to_string());
    }
}

/// Open one resolved import once: `fstat` the descriptor to require a regular
/// file, then read the bytes that are both hashed and lexed.
fn read_regular_file(path: &Path) -> Result<Vec<u8>, String> {
    use std::io::Read;
    let mut file = std::fs::File::open(path).map_err(|e| format!("read failed: {e}"))?;
    let metadata = file.metadata().map_err(|e| format!("fstat failed: {e}"))?;
    if !metadata.is_file() {
        return Err("not a regular file".to_string());
    }
    let mut bytes = Vec::with_capacity(metadata.len() as usize);
    file.read_to_end(&mut bytes)
        .map_err(|e| format!("read failed: {e}"))?;
    Ok(bytes)
}

fn dfs_visit_import(name: String, depth: usize, state: &mut ResolverState) {
    if state.records.len() >= IMPORT_MAX_COUNT {
        exceed(state, "count");
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
                exceed(state, "depth");
                state.records.push(ImportRecord {
                    name,
                    resolved_path: Some(canonical.display().to_string()),
                    sha256: None,
                    size_bytes: None,
                    mtime_unix: None,
                    error: Some(format!("depth limit exceeded ({IMPORT_MAX_DEPTH})")),
                });
                return;
            }

            let (record, bytes) = build_import_record(name.clone(), canonical.clone());
            state.records.push(record);
            let Some(bytes) = bytes else { return };
            // The same bytes that were hashed are lexed. A file that is not
            // UTF-8 cannot be scanned for imports and is an incomplete inventory.
            let content = match String::from_utf8(bytes) {
                Ok(text) => text,
                Err(_) => {
                    if let Some(last) = state.records.last_mut() {
                        last.error =
                            Some("not valid UTF-8; its imports were not scanned".to_string());
                    }
                    return;
                }
            };

            state.in_progress.push(canonical.clone());
            state.in_progress_names.push(name);

            let scan = sbpl_lex::import_scan(&content);
            if !scan.scan_complete {
                state.nonliteral_imports = true;
            }
            for child in scan.refs {
                if state.records.len() >= IMPORT_MAX_COUNT {
                    exceed(state, "count");
                    break;
                }
                dfs_visit_import(child, depth + 1, state);
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
pub fn resolve_imports(source: &str) -> ResolvedImports {
    let mut state = ResolverState {
        records: Vec::new(),
        visited: BTreeSet::new(),
        in_progress: Vec::new(),
        in_progress_names: Vec::new(),
        truncated: false,
        exceeded: None,
        nonliteral_imports: false,
        cycle: None,
        unresolved_seen: BTreeSet::new(),
    };

    let scan = sbpl_lex::import_scan(source);
    state.nonliteral_imports = !scan.scan_complete;
    for name in scan.refs {
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
        exceeded: state.exceeded,
        nonliteral_imports: state.nonliteral_imports,
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
pub fn compute_closure_hash(source: &str, imports: &[ImportRecord]) -> String {
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
            "pw-sbpl-imports-test-{label}-{}-{}",
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
