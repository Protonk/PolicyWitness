//! Bundle metadata helpers for external runners.
//!
//! External XPC services are packaged as bundles with Info.plist metadata; we
//! read only the keys PolicyWitness needs to wire launchd and verify identity.

use std::path::Path;

use crate::plist::plist_key_string;

pub struct BundleInfo {
    pub bundle_id: String,
    pub executable: String,
    pub package_type: Option<String>,
}

pub fn read_bundle_info(bundle_path: &Path) -> Result<BundleInfo, String> {
    let plist = bundle_path.join("Contents").join("Info.plist");
    if !plist.exists() {
        return Err(format!("missing Info.plist at {}", plist.display()));
    }
    let bundle_id = plist_key_string(&plist, "CFBundleIdentifier")?;
    let executable = plist_key_string(&plist, "CFBundleExecutable")?;
    let package_type = plist_key_string(&plist, "CFBundlePackageType").ok();
    Ok(BundleInfo {
        bundle_id,
        executable,
        package_type,
    })
}
