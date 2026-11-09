//! Bundle metadata helpers for external runners.
//!
//! External XPC services are packaged as bundles with Info.plist metadata; we
//! read only the keys PolicyWitness needs to wire launchd and verify identity.

use std::path::Path;
use std::process::Command;

use crate::plist::plist_key_string;

pub struct BundleInfo {
    pub bundle_id: String,
    pub executable: String,
    pub package_type: Option<String>,
    pub contract: String,
}

/// Ask plutil to enforce the plist string type before exact contract admission.
fn contract_marker(plist: &Path) -> Result<String, String> {
    let output = Command::new("/usr/bin/plutil")
        .args([
            "-extract",
            "PWContract",
            "raw",
            "-expect",
            "string",
            "-o",
            "-",
        ])
        .arg(plist)
        .output()
        .map_err(|error| format!("cannot read runner contract marker: {error}"))?;
    if !output.status.success() {
        return Err(format!(
            "PWContract must be a string: {}{}",
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr)
        ));
    }
    parse_contract_marker(&output.stdout)
}

fn parse_contract_marker(bytes: &[u8]) -> Result<String, String> {
    let raw = std::str::from_utf8(bytes).map_err(|_| "runner contract marker is not UTF-8")?;
    let text = raw.strip_suffix('\n').unwrap_or(raw);
    if text.is_empty() {
        return Err("runner contract marker must be nonempty".into());
    }
    Ok(text.to_owned())
}

pub fn read_bundle_info(bundle_path: &Path) -> Result<BundleInfo, String> {
    let plist = bundle_path.join("Contents").join("Info.plist");
    if !plist.exists() {
        return Err(format!("missing Info.plist at {}", plist.display()));
    }
    let bundle_id = plist_key_string(&plist, "CFBundleIdentifier")?;
    let executable = plist_key_string(&plist, "CFBundleExecutable")?;
    let package_type = plist_key_string(&plist, "CFBundlePackageType").ok();
    let contract = contract_marker(&plist)?;
    Ok(BundleInfo {
        bundle_id,
        executable,
        package_type,
        contract,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn contract_marker_requires_an_actual_plist_string() {
        let root = std::env::temp_dir().join(format!(
            "pw-protocol-plist-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir(&root).unwrap();
        let path = root.join("Info.plist");
        for (label, value, accepted) in [
            ("string", "<key>PWContract</key><integer>2</integer>", false),
            ("string", "<key>PWContract</key><string>2</string>", true),
            ("real", "<key>PWContract</key><real>2</real>", false),
            ("boolean", "<key>PWContract</key><true/>", false),
            ("missing", "", false),
        ] {
            std::fs::write(&path, format!("<?xml version=\"1.0\" encoding=\"UTF-8\"?><plist version=\"1.0\"><dict>{value}</dict></plist>")).unwrap();
            let observed = contract_marker(&path);
            if accepted {
                assert_eq!(observed.unwrap(), "2", "{label}");
            } else {
                assert!(observed.is_err(), "{label} was admitted as {observed:?}");
            }
        }
        std::fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn contract_marker_preserves_exact_string_bytes() {
        assert_eq!(parse_contract_marker(b"2\n").unwrap(), "2");
        assert_eq!(
            parse_contract_marker(b" test:context \n").unwrap(),
            " test:context "
        );
        for bad in [b"".as_slice(), b"\xff"] {
            assert!(parse_contract_marker(bad).is_err(), "{bad:?}");
        }
    }
}
