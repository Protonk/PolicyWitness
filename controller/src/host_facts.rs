//! Host facts read through `sysctlbyname`.
//!
//! Shared by the `sbpl-check` diagnostic helper and the controller. Each
//! reader returns the kernel's string for one name, or `None` when the read
//! fails; callers serialize `None` as null and carry on.

use std::ffi::CString;
use std::sync::OnceLock;

/// Read one string-valued sysctl by name. `None` when the name is unknown,
/// the read fails, or the value is empty or not UTF-8.
pub fn sysctl_string(name: &str) -> Option<String> {
    let c_name = CString::new(name).ok()?;
    let mut len: libc::size_t = 0;
    // First call sizes the buffer; the kernel reports the length including
    // the trailing NUL.
    let rc = unsafe {
        libc::sysctlbyname(
            c_name.as_ptr(),
            std::ptr::null_mut(),
            &mut len,
            std::ptr::null_mut(),
            0,
        )
    };
    if rc != 0 || len == 0 {
        return None;
    }
    let mut buf = vec![0u8; len];
    let rc = unsafe {
        libc::sysctlbyname(
            c_name.as_ptr(),
            buf.as_mut_ptr() as *mut libc::c_void,
            &mut len,
            std::ptr::null_mut(),
            0,
        )
    };
    if rc != 0 {
        return None;
    }
    buf.truncate(len);
    if let Some(nul) = buf.iter().position(|&b| b == 0) {
        buf.truncate(nul);
    }
    let text = String::from_utf8(buf).ok()?;
    let trimmed = text.trim();
    if trimmed.is_empty() {
        None
    } else {
        Some(trimmed.to_string())
    }
}

/// Cached `kern.osversion` (the macOS build, e.g. `23J220`). Returns None on
/// a host where the read fails; the field then serializes as null and the
/// rest of the envelope is unaffected.
pub fn macos_build_version() -> Option<String> {
    static CACHE: OnceLock<Option<String>> = OnceLock::new();
    CACHE
        .get_or_init(|| sysctl_string("kern.osversion"))
        .clone()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn build_version_matches_the_kernel_string() {
        // kern.osversion is defined on every macOS kernel; the cached reader
        // must return the same string as a direct read.
        let direct = sysctl_string("kern.osversion").expect("kern.osversion readable");
        assert_eq!(macos_build_version().as_deref(), Some(direct.as_str()));
        assert_eq!(macos_build_version(), macos_build_version());
    }

    #[test]
    fn unknown_name_is_none() {
        assert!(sysctl_string("kern.pw_no_such_sysctl_name").is_none());
        assert!(sysctl_string("kern.os\0version").is_none());
    }

    #[test]
    fn host_fact_names_read_as_strings() {
        for name in [
            "kern.osproductversion",
            "kern.osversion",
            "kern.osrelease",
            "hw.machine",
        ] {
            let value = sysctl_string(name).unwrap_or_else(|| panic!("{name} readable"));
            assert!(
                !value.is_empty() && !value.contains('\0'),
                "{name}: {value:?}"
            );
        }
    }
}
