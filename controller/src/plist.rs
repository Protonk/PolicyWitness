//! Minimal plist reader helpers.
//!
//! We shell out to PlistBuddy to match Apple tooling and keep dependencies
//! small; this is used for bundle Info.plist lookups.

use std::path::Path;
use std::process::{Command, Stdio};

pub fn plist_key_string(plist_path: &Path, key: &str) -> Result<String, String> {
    let plist = plist_path
        .to_str()
        .ok_or_else(|| format!("non-utf8 plist path: {}", plist_path.display()))?;
    let cmd = "/usr/libexec/PlistBuddy";
    let out = Command::new(cmd)
        .args(["-c", &format!("Print :{key}"), plist])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("failed to run {cmd}: {e}"))?;
    if !out.status.success() {
        let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
        let stdout = String::from_utf8_lossy(&out.stdout).trim().to_string();
        let msg = if !stderr.is_empty() { stderr } else { stdout };
        return Err(format!(
            "PlistBuddy failed for {} key {}: {}",
            plist_path.display(),
            key,
            msg
        ));
    }
    Ok(String::from_utf8_lossy(&out.stdout).trim().to_string())
}
