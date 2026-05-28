#!/usr/bin/env python3
"""Verify the runner source list is consistent across both build paths.

Two manifests enumerate the Swift files that compile into the PWRunner.xpc
service: build.sh (production) and runner/Package.swift (test-only SwiftPM
layout). They must agree literally — otherwise a new file shipped via one
path won't show up in the other, and either the production binary or the
unit-test target will silently drop it.

Same check applies to the single C shim file (PWSandboxCheckShim.c).

Exit codes:
  0 — manifests agree
  1 — drift detected; details printed to stderr
  2 — script error (unable to parse a manifest)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER_DIR = REPO_ROOT / "runner"
BUILD_SH = REPO_ROOT / "build.sh"
PACKAGE_SWIFT = RUNNER_DIR / "Package.swift"

# Subdirectories under runner/ that are intentionally outside the
# PWRunner.xpc / PWRunnerCore source set.
EXCLUDED_SUBDIRS = {"services", "runner-client", "Tests", "include"}
# Files at runner/ root that are not Swift source code shipped in the runner.
EXCLUDED_FILES = {"Package.swift", "README.md", ".gitignore"}


def fail(msg: str) -> None:
    sys.stderr.write(msg + "\n")


def disk_swift_files() -> set[str]:
    """Swift files at runner/ root that should appear in both manifests."""
    out: set[str] = set()
    for path in RUNNER_DIR.iterdir():
        if path.is_dir():
            continue
        if path.name in EXCLUDED_FILES:
            continue
        if path.suffix == ".swift":
            out.add(path.name)
    return out


def disk_c_files() -> set[str]:
    """C source files at runner/ root."""
    out: set[str] = set()
    for path in RUNNER_DIR.iterdir():
        if path.is_dir():
            continue
        if path.suffix == ".c":
            out.add(path.name)
    return out


def build_sh_swift_files() -> set[str]:
    """Files compiled into PWRunner.xpc by build.sh's swiftc invocation.

    We parse two layers: the variable declarations (XPC_RUNNER_*_FILE=...)
    that resolve to file paths, and the references to those variables
    inside the swiftc command for the service bundle. A variable that
    isn't referenced is treated as drift even if it's declared.
    """
    text = BUILD_SH.read_text(encoding="utf-8")

    # XPC_RUNNER_FOO_FILE="${XPC_ROOT}/Bar.swift"
    decl_re = re.compile(
        r'^XPC_RUNNER_([A-Z_]+)_FILE="\$\{XPC_ROOT\}/([^"]+\.swift)"',
        re.MULTILINE,
    )
    declarations: dict[str, str] = {}
    for match in decl_re.finditer(text):
        var_name = "XPC_RUNNER_" + match.group(1) + "_FILE"
        declarations[var_name] = match.group(2)

    # Find the swiftc block that builds the service binaries and extract
    # every "${XPC_RUNNER_*_FILE}" reference inside it.
    svc_block_re = re.compile(
        r'echo "==> Building embedded PWRunner XPC services".*?for svc_name.*?done',
        re.DOTALL,
    )
    block_match = svc_block_re.search(text)
    if block_match is None:
        fail("could not locate the PWRunner XPC services swiftc block in build.sh")
        sys.exit(2)
    referenced = set(re.findall(r'\$\{(XPC_RUNNER_[A-Z_]+_FILE)\}', block_match.group(0)))

    files: set[str] = set()
    for var in referenced:
        if var not in declarations:
            fail(f"build.sh references {var} in the swiftc call but never declares it")
            sys.exit(2)
        files.add(declarations[var])
    return files


def build_sh_c_files() -> set[str]:
    """C source files compiled into PWRunner.xpc by build.sh."""
    text = BUILD_SH.read_text(encoding="utf-8")
    shim_re = re.compile(
        r'^XPC_RUNNER_SANDBOX_SHIM="\$\{XPC_ROOT\}/([^"]+\.c)"',
        re.MULTILINE,
    )
    files: set[str] = set()
    for match in shim_re.finditer(text):
        files.add(match.group(1))
    return files


def package_swift_sources(target_name: str) -> set[str]:
    """Files listed in the `sources:` array of a SwiftPM target."""
    text = PACKAGE_SWIFT.read_text(encoding="utf-8")
    # Anchor on .target(name: "<target>", ...) ... sources: [...]
    target_re = re.compile(
        r'\.(?:target|executableTarget)\(\s*name:\s*"' + re.escape(target_name) + r'".*?sources:\s*\[(.*?)\]',
        re.DOTALL,
    )
    match = target_re.search(text)
    if match is None:
        fail(f"could not find target {target_name!r} with a sources: array in Package.swift")
        sys.exit(2)
    body = match.group(1)
    entries = re.findall(r'"([^"]+)"', body)
    return set(entries)


def diff_sets(label: str, manifests: dict[str, set[str]]) -> list[str]:
    """Return a list of human-readable mismatch lines; empty when agreed."""
    union = set().union(*manifests.values())
    problems: list[str] = []
    for filename in sorted(union):
        present_in = [name for name, files in manifests.items() if filename in files]
        if len(present_in) == len(manifests):
            continue
        missing_from = sorted(set(manifests) - set(present_in))
        problems.append(
            f"  {label}: {filename!r} is in {present_in} but missing from {missing_from}"
        )
    return problems


def main() -> int:
    swift_manifests = {
        "disk (runner/*.swift)": disk_swift_files(),
        "build.sh (PWRunner.xpc swiftc)": build_sh_swift_files(),
        "Package.swift (PWRunnerCore target)": package_swift_sources("PWRunnerCore"),
    }
    c_manifests = {
        "disk (runner/*.c)": disk_c_files(),
        "build.sh (XPC_RUNNER_SANDBOX_SHIM)": build_sh_c_files(),
        "Package.swift (PWSandboxCheckShim target)": package_swift_sources("PWSandboxCheckShim"),
    }

    problems: list[str] = []
    problems.extend(diff_sets("swift", swift_manifests))
    problems.extend(diff_sets("c", c_manifests))

    if problems:
        fail("runner source manifests disagree:")
        for line in problems:
            fail(line)
        fail("")
        fail("Fix by adding the file to every manifest that should ship it, or")
        fail("by removing it from manifests that should not. The three sources of")
        fail("truth (disk, build.sh, Package.swift) must agree on the runner/ root")
        fail("file set; subdirectories under EXCLUDED_SUBDIRS are managed separately.")
        return 1

    print(
        f"runner source manifests agree: "
        f"{len(swift_manifests['disk (runner/*.swift)'])} swift, "
        f"{len(c_manifests['disk (runner/*.c)'])} c"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
