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
    pub protocol_version: u32,
}

/// `Print` alone cannot distinguish the integer 2 from the string "2".
/// Ask plutil to enforce the plist type before parsing its decimal output.
fn protocol_marker(plist: &Path) -> Result<u32, String> {
    let output = Command::new("/usr/bin/plutil")
        .args([
            "-extract",
            "PWRunnerProtocolVersion",
            "raw",
            "-expect",
            "integer",
            "-o",
            "-",
        ])
        .arg(plist)
        .output()
        .map_err(|error| format!("cannot read runner protocol marker: {error}"))?;
    if !output.status.success() {
        return Err(format!(
            "PWRunnerProtocolVersion must be an integer: {}{}",
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr)
        ));
    }
    parse_protocol_marker(&output.stdout)
}

fn parse_protocol_marker(bytes: &[u8]) -> Result<u32, String> {
    let text = std::str::from_utf8(bytes)
        .map_err(|_| "runner protocol marker is not UTF-8")?
        .trim();
    if text.is_empty() || !text.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err("runner protocol marker must be a nonnegative integer".into());
    }
    text.parse()
        .map_err(|_| "runner protocol marker is outside the supported integer range".into())
}

pub fn read_bundle_info(bundle_path: &Path) -> Result<BundleInfo, String> {
    let plist = bundle_path.join("Contents").join("Info.plist");
    if !plist.exists() {
        return Err(format!("missing Info.plist at {}", plist.display()));
    }
    let bundle_id = plist_key_string(&plist, "CFBundleIdentifier")?;
    let executable = plist_key_string(&plist, "CFBundleExecutable")?;
    let package_type = plist_key_string(&plist, "CFBundlePackageType").ok();
    let protocol_version = protocol_marker(&plist)?;
    Ok(BundleInfo {
        bundle_id,
        executable,
        package_type,
        protocol_version,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn protocol_marker_requires_an_actual_plist_integer() {
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
            (
                "integer",
                "<key>PWRunnerProtocolVersion</key><integer>2</integer>",
                true,
            ),
            (
                "string",
                "<key>PWRunnerProtocolVersion</key><string>2</string>",
                false,
            ),
            (
                "real",
                "<key>PWRunnerProtocolVersion</key><real>2</real>",
                false,
            ),
            (
                "boolean",
                "<key>PWRunnerProtocolVersion</key><true/>",
                false,
            ),
            ("missing", "", false),
        ] {
            std::fs::write(&path, format!("<?xml version=\"1.0\" encoding=\"UTF-8\"?><plist version=\"1.0\"><dict>{value}</dict></plist>")).unwrap();
            let observed = protocol_marker(&path);
            if accepted {
                assert_eq!(observed.unwrap(), 2, "{label}");
            } else {
                assert!(observed.is_err(), "{label} was admitted as {observed:?}");
            }
        }
        std::fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn protocol_marker_integer_range_is_explicit() {
        assert_eq!(parse_protocol_marker(b"2\n").unwrap(), 2);
        for bad in [
            b"".as_slice(),
            b"2.0",
            b"-1",
            b"true",
            b"\"2\"",
            b"4294967296",
        ] {
            assert!(parse_protocol_marker(bad).is_err(), "{bad:?}");
        }
    }
}
