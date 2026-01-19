import Foundation
import Darwin

// Path normalization and observation helpers used by probe attempts.
@_silgen_name("fcntl")
private func fcntl_getpath(_ fd: Int32, _ cmd: Int32, _ value: UnsafeMutablePointer<CChar>?) -> Int32

struct CanonicalPath {
    var input: String
    var normalized: String
    var resolved: String?
}

// Normalize paths for reporting:
// - If realpath succeeds, use the resolved absolute path.
// - Otherwise, standardize absolute paths and leave relative paths as-is.
func canonicalizePath(_ input: String) -> CanonicalPath {
    var buf = [CChar](repeating: 0, count: Int(PATH_MAX))
    let rc = input.withCString { ptr in
        realpath(ptr, &buf)
    }
    if rc != nil {
        let resolved = String(cString: buf)
        return CanonicalPath(input: input, normalized: resolved, resolved: resolved)
    }
    let normalized: String
    if input.hasPrefix("/") {
        normalized = URL(fileURLWithPath: input).standardizedFileURL.path
    } else {
        normalized = input
    }
    return CanonicalPath(input: input, normalized: normalized, resolved: nil)
}

// Resolve the kernel's view of an open file descriptor, when available.
func observedPathForFd(_ fd: Int32) -> String? {
    var buf = [CChar](repeating: 0, count: Int(PATH_MAX))
    let rc: Int32 = buf.withUnsafeMutableBufferPointer { ptr in
        guard let base = ptr.baseAddress else {
            return -1
        }
        return fcntl_getpath(fd, F_GETPATH, base)
    }
    if rc == 0 {
        return String(cString: buf)
    }
    return nil
}
