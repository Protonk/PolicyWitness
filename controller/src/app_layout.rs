//! Bundle layout for PolicyWitness.app.
//!
//! The controller resolves embedded tools relative to its own executable so the
//! app bundle can be relocated without rewriting paths. The built-in runner and
//! the three binary baselines are selected by the fixed relative paths below,
//! through the app evidence manifest; no Info.plist is read on a run.

use std::path::{Component, Path, PathBuf};

/// A binary the app ships at a fixed path, selected and compared by that path.
pub struct ShippedBinary {
    /// Path relative to the app root.
    pub rel_path: &'static str,
    /// The manifest `kind` the entry at that path must carry.
    pub kind: &'static str,
}

/// The built-in XPC service host.
pub const SHIPPED_SERVICE: ShippedBinary = ShippedBinary {
    rel_path: "Contents/XPCServices/PWRunner.xpc/Contents/MacOS/PWRunner",
    kind: "xpc-service",
};
/// The bundle-local C worker.
pub const SHIPPED_WORKER: ShippedBinary = ShippedBinary {
    rel_path: "Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner",
    kind: "xpc-embedded-helper",
};
/// The bundle-local validator; production traffic never uses the app-level copy.
pub const SHIPPED_VALIDATOR: ShippedBinary = ShippedBinary {
    rel_path: "Contents/XPCServices/PWRunner.xpc/Contents/MacOS/sb_api_validator",
    kind: "xpc-embedded-helper",
};

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
