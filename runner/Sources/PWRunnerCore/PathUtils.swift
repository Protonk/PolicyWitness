import Foundation
import Darwin

// Path normalization helpers for query planning and host path diagnostics.

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

/// The parent directory through realpath(3) with the literal leaf appended:
/// the path form the kernel names for a created or unlinked entry, or for a
/// symlink acted on itself. Nil for a relative path, a missing or dot leaf, or a
/// parent the host cannot resolve.
func parentRealpathResolved(_ input: String) -> String? {
    guard input.hasPrefix("/"), !input.hasSuffix("/"), let slash = input.lastIndex(of: "/") else {
        return nil
    }
    let leaf = String(input[input.index(after: slash)...])
    if leaf.isEmpty || leaf == "." || leaf == ".." {
        return nil
    }
    let parent = slash == input.startIndex ? "/" : String(input[..<slash])
    guard let resolvedParent = canonicalizePath(parent).resolved else {
        return nil
    }
    return resolvedParent == "/" ? "/" + leaf : resolvedParent + "/" + leaf
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

// Standard /usr/share/firmlinks mappings as shipped on Catalina+. Used as a
// fallback when the file itself is unreadable. The source paths are absolute; the targets are
// the data-volume-relative subpaths (which get `/System/Volumes/Data/`
// prepended at load time). Order does not matter — we re-sort by descending
// prefix length for longest-match.
private let firmlinksBuiltinFallback: [(String, String)] = [
    ("/AppleInternal", "AppleInternal"),
    ("/Applications", "Applications"),
    ("/Library", "Library"),
    ("/System/Library/Caches", "System/Library/Caches"),
    ("/System/Library/Assets", "System/Library/Assets"),
    ("/System/Library/PreinstalledAssets", "System/Library/PreinstalledAssets"),
    ("/System/Library/AssetsV2", "System/Library/AssetsV2"),
    ("/System/Library/PreinstalledAssetsV2", "System/Library/PreinstalledAssetsV2"),
    ("/System/Library/CoreServices/CoreTypes.bundle/Contents/Library",
     "System/Library/CoreServices/CoreTypes.bundle/Contents/Library"),
    ("/System/Library/Speech", "System/Library/Speech"),
    ("/Users", "Users"),
    ("/Volumes", "Volumes"),
    ("/cores", "cores"),
    ("/opt", "opt"),
    ("/private", "private"),
    ("/usr/local", "usr/local"),
    ("/usr/libexec/cups", "usr/libexec/cups"),
    ("/usr/share/snmp", "usr/share/snmp"),
]

private struct FirmlinkMap {
    // Sorted by descending source-prefix length so the first match is the
    // most specific (e.g. `/System/Library/Caches` wins over a hypothetical
    // `/System`).
    let mappings: [(prefix: String, target: String)]

    static let shared: FirmlinkMap = parse(path: "/usr/share/firmlinks")

    static func parse(path: String) -> FirmlinkMap {
        // Try the on-disk file first so we pick up any host-local changes;
        // fall back to the built-in mapping when the read fails (sandbox or
        // missing file). Either way the map is non-empty on every supported
        // macOS.
        if let contents = try? String(contentsOfFile: path, encoding: .utf8) {
            var pairs: [(String, String)] = []
            for rawLine in contents.split(separator: "\n", omittingEmptySubsequences: true) {
                let line = String(rawLine)
                let parts = line.split(separator: "\t", maxSplits: 1, omittingEmptySubsequences: false)
                guard parts.count == 2 else { continue }
                let source = String(parts[0])
                let targetRel = String(parts[1])
                guard source.hasPrefix("/"), !targetRel.isEmpty else { continue }
                pairs.append((source, "/System/Volumes/Data/\(targetRel)"))
            }
            if !pairs.isEmpty {
                pairs.sort { $0.0.count > $1.0.count }
                return FirmlinkMap(mappings: pairs)
            }
        }
        var fallback: [(String, String)] = firmlinksBuiltinFallback.map {
            ($0.0, "/System/Volumes/Data/\($0.1)")
        }
        fallback.sort { $0.0.count > $1.0.count }
        return FirmlinkMap(mappings: fallback)
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
/// is not absolute or when no mapping prefix matches. The map itself is
/// always non-empty on a supported macOS — see `firmlinksBuiltinFallback`.
func firmlinkResolved(_ input: String) -> String? {
    return FirmlinkMap.shared.resolve(input)
}

/// Pure-string substitution for the three standard userspace symlinks that
/// exist on every shipped macOS: `/etc`, `/tmp`, `/var` -> `/private/etc`,
/// `/private/tmp`, `/private/var`. Returns the input unchanged when no
/// substitution applies.
///
/// Used as a fallback for `realpath(3)` when the runner is operating inside
/// its own sandbox that denies the stat libsandbox would need (e.g. a
/// `(deny default)` profile under which file-read-metadata is unavailable).
/// Knowing these three mappings is enough to recover the realpath-equivalent
/// form for the prefixes that actually matter in practice.
func wellKnownSymlinksResolved(_ input: String) -> String {
    let mappings: [(String, String)] = [
        ("/etc", "/private/etc"),
        ("/tmp", "/private/tmp"),
        ("/var", "/private/var"),
    ]
    for (prefix, target) in mappings {
        if input == prefix {
            return target
        }
        if input.hasPrefix(prefix + "/") {
            return target + input.dropFirst(prefix.count)
        }
    }
    return input
}
