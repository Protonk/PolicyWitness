//! Bundle layout helpers for PolicyWitness.app.
//!
//! The controller resolves embedded tools relative to its own executable so the
//! app bundle can be relocated without rewriting paths.

use std::path::{Component, Path, PathBuf};

use crate::plist::plist_key_string;

pub const PW_RUNNER_STANDARD_SERVICE_DIR: &str = "PWRunner";
pub const PW_RUNNER_DEBUG_SERVICE_DIR: &str = "PWRunnerDebug";

#[derive(Clone)]
pub struct PWRunnerBundleInfo {
    pub bundle_id: String,
    pub executable: String,
}

pub fn validate_tool_name(tool_name: &str) -> Result<(), String> {
    let mut components = Path::new(tool_name).components();
    match (components.next(), components.next()) {
        (Some(Component::Normal(_)), None) => Ok(()),
        _ => Err(format!(
            "invalid tool name {tool_name:?} (must be a single path component)"
        )),
    }
}

pub fn app_root_from_current_exe() -> Result<PathBuf, String> {
    let exe = std::env::current_exe().map_err(|e| format!("current_exe() failed: {e}"))?;
    // Expected layout: dist/PolicyWitness.app/Contents/MacOS/policy-witness
    let contents_dir = exe
        .parent()
        .and_then(|p| p.parent())
        .ok_or_else(|| format!("unexpected executable location: {}", exe.display()))?;
    let app_root = contents_dir
        .parent()
        .ok_or_else(|| format!("unexpected executable location: {}", exe.display()))?;
    Ok(app_root.to_path_buf())
}

pub fn resolve_contents_macos_tool(tool_name: &str) -> Result<PathBuf, String> {
    validate_tool_name(tool_name)?;
    let exe = std::env::current_exe().map_err(|e| format!("current_exe() failed: {e}"))?;
    let contents_dir = exe
        .parent()
        .and_then(|p| p.parent())
        .ok_or_else(|| format!("unexpected executable location: {}", exe.display()))?;
    // Tools live alongside the controller under Contents/MacOS.
    let candidate = contents_dir.join("MacOS").join(tool_name);
    if candidate.exists() {
        return Ok(candidate);
    }
    Err(format!(
        "embedded tool not found in Contents/MacOS: {tool_name:?} (expected: {})",
        candidate.display()
    ))
}

pub fn resolve_pw_runner_bundle_info(
    app_root: &Path,
    service_dir: &str,
) -> Result<PWRunnerBundleInfo, String> {
    let plist = app_root
        .join("Contents")
        .join("XPCServices")
        .join(format!("{service_dir}.xpc"))
        .join("Contents")
        .join("Info.plist");
    if !plist.exists() {
        return Err(format!("missing PWRunner Info.plist: {}", plist.display()));
    }
    let bundle_id = plist_key_string(&plist, "CFBundleIdentifier")?;
    let executable = plist_key_string(&plist, "CFBundleExecutable")?;
    Ok(PWRunnerBundleInfo {
        bundle_id,
        executable,
    })
}
