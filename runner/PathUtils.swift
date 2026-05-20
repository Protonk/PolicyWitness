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

// Firmlinks parser + helpers used to surface candidate kernel-side forms of a
// sandbox_check path argument. Apple-internal sandbox_check matches subpath
// rules against the kernel's post-firmlink view of a path; userland realpath
// returns the post-symlink form (e.g. `/etc/hosts` -> `/private/etc/hosts`)
// but does not apply the firmlink mapping that moves writable subtrees onto
// the Data volume (`/private` -> `/System/Volumes/Data/private` on most
// modern installs). Exposing all candidate forms in probe output lets a
// caller see which prefix actually would have matched.
//
// /usr/share/firmlinks format: one `source<TAB>target` mapping per line,
// where source is absolute and target is data-volume-relative (no leading
// slash). Lazily loaded once per process.

private struct FirmlinkMap {
    // Sorted by descending source-prefix length so the first match is the
    // most specific (e.g. `/System/Library/Caches` wins over a hypothetical
    // `/System`).
    let mappings: [(prefix: String, target: String)]

    static let shared: FirmlinkMap = parse(path: "/usr/share/firmlinks")

    static func parse(path: String) -> FirmlinkMap {
        guard let contents = try? String(contentsOfFile: path, encoding: .utf8) else {
            return FirmlinkMap(mappings: [])
        }
        var pairs: [(String, String)] = []
        for rawLine in contents.split(separator: "\n", omittingEmptySubsequences: true) {
            let line = String(rawLine)
            let parts = line.split(separator: "\t", maxSplits: 1, omittingEmptySubsequences: false)
            guard parts.count == 2 else { continue }
            let source = String(parts[0])
            let targetRel = String(parts[1])
            guard source.hasPrefix("/"), !targetRel.isEmpty else { continue }
            let target = "/System/Volumes/Data/\(targetRel)"
            pairs.append((source, target))
        }
        pairs.sort { $0.0.count > $1.0.count }
        return FirmlinkMap(mappings: pairs)
    }

    func resolve(_ input: String) -> String? {
        guard input.hasPrefix("/") else { return nil }
        for (prefix, target) in mappings {
            if input == prefix {
                return target
            }
            if input.hasPrefix(prefix + "/") {
                let suffix = input.dropFirst(prefix.count)
                return target + suffix
            }
        }
        return nil
    }
}

/// Apply the firmlinks mapping to an absolute path. Returns nil when the path
/// is not absolute, when /usr/share/firmlinks is unreadable, or when no
/// mapping prefix matches.
func firmlinkResolved(_ input: String) -> String? {
    return FirmlinkMap.shared.resolve(input)
}

/// Heuristic shortcut for the most common firmlinked subtree: paths under
/// `/private/` get the `/System/Volumes/Data` prefix. Returns nil for paths
/// that don't start with `/private`. Useful as a sanity check when
/// firmlinkResolved is unavailable (e.g. on systems where the file is
/// missing) and for highlighting the most common Q2-class divergence.
func dataVolumeForm(_ input: String) -> String? {
    if input == "/private" {
        return "/System/Volumes/Data/private"
    }
    if input.hasPrefix("/private/") {
        return "/System/Volumes/Data\(input)"
    }
    return nil
}
