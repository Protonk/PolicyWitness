#!/usr/bin/env python3
"""Verify the runner source list and the testing registry are consistent.

The check has two halves:

1. Source-set drift between the two compile paths that ship Swift to
   PWRunner.xpc. build.sh and runner/Package.swift both enumerate the
   same set of Swift files; a file added to one but not the other never
   reaches the missing path. Same applies to the C shim.

2. Test-registry drift across what should be self-consistent project
   discipline:
     a. Every tests/suites/<name>/ with run.sh has README.md.
     b. Every Baseline-tier suite is in tests/run.sh's default list.
     c. Every tests/suites/<name>/ has a row in tests/INDEX.md, and
        every INDEX row maps to a real suite directory.
     d. Every runner_outcome_<X> suite corresponds to an outcome in the
        coverage matrix in tests/INDEX.md.
     e. Every NormalizedOutcome constant in runner/PWRunnerAPI.swift
        has a row in the coverage matrix.

Exit codes:
  0 — everything agrees
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
PWRUNNER_API = RUNNER_DIR / "PWRunnerAPI.swift"
SUITES_DIR = REPO_ROOT / "tests" / "suites"
TESTS_RUN_SH = REPO_ROOT / "tests" / "run.sh"
TESTS_INDEX = REPO_ROOT / "tests" / "INDEX.md"

EXCLUDED_SUBDIRS = {"services", "runner-client", "Tests", "include"}
EXCLUDED_FILES = {"Package.swift", "README.md", ".gitignore"}


def fail(msg: str) -> None:
    sys.stderr.write(msg + "\n")


# ---------------------------------------------------------------------------
# Source manifest checks (pre-existing behavior — unchanged)
# ---------------------------------------------------------------------------

def disk_swift_files() -> set[str]:
    out: set[str] = set()
    for path in RUNNER_DIR.iterdir():
        if path.is_dir() or path.name in EXCLUDED_FILES:
            continue
        if path.suffix == ".swift":
            out.add(path.name)
    return out


def disk_c_files() -> set[str]:
    return {p.name for p in RUNNER_DIR.iterdir() if p.is_file() and p.suffix == ".c"}


def build_sh_swift_files() -> set[str]:
    text = BUILD_SH.read_text(encoding="utf-8")
    decl_re = re.compile(
        r'^XPC_RUNNER_([A-Z_]+)_FILE="\$\{XPC_ROOT\}/([^"]+\.swift)"',
        re.MULTILINE,
    )
    declarations: dict[str, str] = {}
    for match in decl_re.finditer(text):
        declarations["XPC_RUNNER_" + match.group(1) + "_FILE"] = match.group(2)

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
    text = BUILD_SH.read_text(encoding="utf-8")
    shim_re = re.compile(
        r'^XPC_RUNNER_SANDBOX_SHIM="\$\{XPC_ROOT\}/([^"]+\.c)"',
        re.MULTILINE,
    )
    return {m.group(1) for m in shim_re.finditer(text)}


def package_swift_sources(target_name: str) -> set[str]:
    text = PACKAGE_SWIFT.read_text(encoding="utf-8")
    target_re = re.compile(
        r'\.(?:target|executableTarget)\(\s*name:\s*"'
        + re.escape(target_name)
        + r'".*?sources:\s*\[(.*?)\]',
        re.DOTALL,
    )
    match = target_re.search(text)
    if match is None:
        fail(f"could not find target {target_name!r} with a sources: array in Package.swift")
        sys.exit(2)
    return set(re.findall(r'"([^"]+)"', match.group(1)))


def diff_sets(label: str, manifests: dict[str, set[str]]) -> list[str]:
    union: set[str] = set().union(*manifests.values())
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


# ---------------------------------------------------------------------------
# Test-registry parsers
# ---------------------------------------------------------------------------

def suites_with_run_sh() -> set[str]:
    out: set[str] = set()
    if not SUITES_DIR.is_dir():
        fail(f"missing suites directory: {SUITES_DIR}")
        sys.exit(2)
    for child in SUITES_DIR.iterdir():
        if not child.is_dir():
            continue
        if (child / "run.sh").exists():
            out.add(child.name)
    return out


def suites_missing_readme() -> list[str]:
    out: list[str] = []
    for child in sorted(SUITES_DIR.iterdir()):
        if not child.is_dir():
            continue
        if not (child / "run.sh").exists():
            continue
        if not (child / "README.md").exists():
            out.append(child.name)
    return out


def default_suites_from_run_sh() -> set[str]:
    """Parse the default suite list from tests/run.sh.

    The script declares `suites=()` empty up top and then conditionally
    assigns the real defaults later — so a naive first-match grabs the
    empty array. Pick the assignment with the most entries instead,
    which is always the default-fill block.
    """
    text = TESTS_RUN_SH.read_text(encoding="utf-8")
    matches = re.findall(r'\bsuites=\(([^)]*)\)', text)
    if not matches:
        fail("could not locate any suites=(...) assignment in tests/run.sh")
        sys.exit(2)
    best = max(matches, key=lambda body: len(body.split()))
    return set(best.split())


def parse_index_rows() -> dict[str, str]:
    """Return {suite_name: tier} parsed from the suite table in INDEX.md.

    Only the first markdown table is considered; matrix rows below the
    Normalized outcome coverage matrix heading are skipped.
    """
    text = TESTS_INDEX.read_text(encoding="utf-8")
    # Split off the matrix section so we only parse the suite table.
    cut = text.split("## Normalized outcome coverage matrix", 1)[0]
    rows: dict[str, str] = {}
    row_re = re.compile(r'^\|\s*`([a-z][a-z0-9_]*)`\s*\|\s*([A-Za-z][^|]*?)\s*\|', re.MULTILINE)
    for match in row_re.finditer(cut):
        rows[match.group(1)] = match.group(2).strip()
    return rows


def parse_matrix_outcomes() -> set[str]:
    text = TESTS_INDEX.read_text(encoding="utf-8")
    parts = text.split("## Normalized outcome coverage matrix", 1)
    if len(parts) != 2:
        fail("tests/INDEX.md is missing the 'Normalized outcome coverage matrix' section")
        sys.exit(2)
    matrix_text = parts[1]
    # Stop at the next ## heading if present.
    next_heading = re.search(r'^##\s', matrix_text, re.MULTILINE)
    if next_heading:
        matrix_text = matrix_text[: next_heading.start()]
    row_re = re.compile(r'^\|\s*`([a-z][a-z0-9_]*)`\s*\|', re.MULTILINE)
    return {m.group(1) for m in row_re.finditer(matrix_text)}


def parse_normalized_outcomes() -> set[str]:
    text = PWRUNNER_API.read_text(encoding="utf-8")
    # public enum NormalizedOutcome { ... public static let foo = "bar" ... }
    enum_re = re.compile(
        r'public enum NormalizedOutcome\s*\{(.*?)\n\}',
        re.DOTALL,
    )
    match = enum_re.search(text)
    if match is None:
        fail("could not locate NormalizedOutcome enum in runner/PWRunnerAPI.swift")
        sys.exit(2)
    body = match.group(1)
    constant_re = re.compile(r'public static let \w+\s*=\s*"([a-z_][a-z0-9_]*)"')
    return {m.group(1) for m in constant_re.finditer(body)}


# ---------------------------------------------------------------------------
# Test-registry checks
# ---------------------------------------------------------------------------

def check_readmes_present() -> list[str]:
    missing = suites_missing_readme()
    return [f"  README: tests/suites/{name}/ has run.sh but no README.md" for name in missing]


def check_index_vs_disk() -> list[str]:
    problems: list[str] = []
    on_disk = suites_with_run_sh()
    in_index = set(parse_index_rows().keys())

    for name in sorted(on_disk - in_index):
        problems.append(f"  INDEX: tests/suites/{name}/ exists but has no row in tests/INDEX.md")
    for name in sorted(in_index - on_disk):
        problems.append(f"  INDEX: tests/INDEX.md has a row for {name!r} but no such tests/suites/{name}/ exists")
    return problems


def check_baseline_in_run_sh_defaults() -> list[str]:
    problems: list[str] = []
    rows = parse_index_rows()
    defaults = default_suites_from_run_sh()
    for name, tier in sorted(rows.items()):
        if tier.lower() != "baseline":
            continue
        if name not in defaults:
            problems.append(
                f"  run.sh: Baseline-tier suite {name!r} is missing from tests/run.sh's default suites=(...) list"
            )
    return problems


def check_runner_outcome_suites_have_matrix_rows() -> list[str]:
    problems: list[str] = []
    on_disk = suites_with_run_sh()
    matrix = parse_matrix_outcomes()
    for name in sorted(on_disk):
        if not name.startswith("runner_outcome_"):
            continue
        outcome = name[len("runner_outcome_"):]
        if outcome not in matrix:
            problems.append(
                f"  matrix: suite {name!r} has no row for outcome {outcome!r} "
                f"in the Normalized outcome coverage matrix"
            )
    return problems


def check_normalized_outcomes_have_matrix_rows() -> list[str]:
    problems: list[str] = []
    outcomes = parse_normalized_outcomes()
    matrix = parse_matrix_outcomes()
    for outcome in sorted(outcomes - matrix):
        problems.append(
            f"  matrix: NormalizedOutcome.{outcome} has no row in tests/INDEX.md "
            f"coverage matrix"
        )
    for outcome in sorted(matrix - outcomes):
        problems.append(
            f"  matrix: coverage matrix lists {outcome!r} but no NormalizedOutcome "
            f"constant by that name exists"
        )
    return problems


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

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
    problems.extend(check_readmes_present())
    problems.extend(check_index_vs_disk())
    problems.extend(check_baseline_in_run_sh_defaults())
    problems.extend(check_runner_outcome_suites_have_matrix_rows())
    problems.extend(check_normalized_outcomes_have_matrix_rows())

    if problems:
        fail("source/test-registry drift detected:")
        for line in problems:
            fail(line)
        fail("")
        fail("Each rule is mechanical: fix the missing file, row, or list entry")
        fail("named above. The guardrail exists so adding a new suite or outcome")
        fail("without registering it everywhere fails loudly here rather than")
        fail("silently in downstream consumers.")
        return 1

    suite_count = len(suites_with_run_sh())
    outcome_count = len(parse_normalized_outcomes())
    print(
        f"all drift checks pass: "
        f"{len(swift_manifests['disk (runner/*.swift)'])} swift, "
        f"{len(c_manifests['disk (runner/*.c)'])} c, "
        f"{suite_count} suites, "
        f"{outcome_count} outcomes."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
