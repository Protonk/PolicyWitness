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
PROBE_RUNNER = RUNNER_DIR / "ProbeRunner.swift"
CWORKER_ORCHESTRATOR = RUNNER_DIR / "CWorkerOrchestrator.swift"
POLICYWITNESS_MD = REPO_ROOT / "PolicyWitness.md"
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
    """Collect every C source file build.sh declares as an XPC_RUNNER_*_SHIM
    relative to XPC_ROOT. Currently two: PWSandboxCheckShim.c (the
    sandbox_check trampoline) and PWCWorkerShim.c (atomic + shm_open
    helpers for the Swift CWorker driver). Adding a third shim is a
    single line edit here and a matching declaration in build.sh."""
    text = BUILD_SH.read_text(encoding="utf-8")
    shim_re = re.compile(
        r'^XPC_RUNNER_(?:SANDBOX|CWORKER)_SHIM="\$\{XPC_ROOT\}/([^"]+\.c)"',
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


def _parse_matrix_section(heading: str) -> set[str]:
    text = TESTS_INDEX.read_text(encoding="utf-8")
    parts = text.split(heading, 1)
    if len(parts) != 2:
        fail(f"tests/INDEX.md is missing the {heading!r} section")
        sys.exit(2)
    matrix_text = parts[1]
    # Stop at the next ## heading if present.
    next_heading = re.search(r'^##\s', matrix_text, re.MULTILINE)
    if next_heading:
        matrix_text = matrix_text[: next_heading.start()]
    row_re = re.compile(r'^\|\s*`([a-z][a-z0-9_]*)`\s*\|', re.MULTILINE)
    return {m.group(1) for m in row_re.finditer(matrix_text)}


def parse_matrix_outcomes() -> set[str]:
    return _parse_matrix_section("## Normalized outcome coverage matrix")


def parse_attempt_outcome_matrix() -> set[str]:
    return _parse_matrix_section("## Attempt outcome coverage matrix")


def _parse_swift_enum_constants(enum_name: str) -> set[str]:
    text = PWRUNNER_API.read_text(encoding="utf-8")
    enum_re = re.compile(
        r'public enum ' + re.escape(enum_name) + r'\s*\{(.*?)\n\}',
        re.DOTALL,
    )
    match = enum_re.search(text)
    if match is None:
        fail(f"could not locate {enum_name} enum in runner/PWRunnerAPI.swift")
        sys.exit(2)
    body = match.group(1)
    constant_re = re.compile(r'public static let \w+\s*=\s*"([a-z_][a-z0-9_]*)"')
    return {m.group(1) for m in constant_re.finditer(body)}


def parse_normalized_outcomes() -> set[str]:
    return _parse_swift_enum_constants("NormalizedOutcome")


def parse_attempt_outcomes() -> set[str]:
    return _parse_swift_enum_constants("AttemptOutcome")


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


def check_attempt_outcomes_have_matrix_rows() -> list[str]:
    """Parallel to check_normalized_outcomes_have_matrix_rows but for
    the AttemptOutcome enum. Same drift guardrail so a new attempt
    outcome added to the enum can't ship without a row explaining
    where it gets emitted and how it's covered."""
    problems: list[str] = []
    outcomes = parse_attempt_outcomes()
    matrix = parse_attempt_outcome_matrix()
    for outcome in sorted(outcomes - matrix):
        problems.append(
            f"  matrix: AttemptOutcome.{outcome} has no row in tests/INDEX.md "
            f"attempt-outcome coverage matrix"
        )
    for outcome in sorted(matrix - outcomes):
        problems.append(
            f"  matrix: attempt-outcome matrix lists {outcome!r} but no "
            f"AttemptOutcome constant by that name exists"
        )
    return problems


# ---------------------------------------------------------------------------
# Prediction-unavailable (op, filter) pair agreement.
#
# Three sources of truth must list the same set of pairs:
#   - runner/ProbeRunner.swift::predictionUnavailableOpFilters (canonical)
#   - runner/CWorkerOrchestrator.swift::predictionUnavailableOpFiltersHostMirror
#   - PolicyWitness.md "Filter kinds where prediction is unavailable"
#
# A pair added to one but not the other means a request that should skip
# in the runner only skips in one path, or that the documented contract
# diverges from the runtime — both bad.
# ---------------------------------------------------------------------------

def parse_swift_prediction_unavailable_pairs() -> set[tuple[str, str]]:
    text = PROBE_RUNNER.read_text(encoding="utf-8")
    # private let predictionUnavailableOpFilters: Set<PredictionUnavailablePair> = [
    #     .init(operation: "iokit-open-service",
    #           filterKind: PWRunnerWire.sandboxFilterIokitRegistryEntryClass),
    #     ...
    # ]
    block_re = re.compile(
        r'predictionUnavailableOpFilters[^\[]*\[(.*?)\n\]',
        re.DOTALL,
    )
    match = block_re.search(text)
    if match is None:
        fail("could not locate predictionUnavailableOpFilters in runner/ProbeRunner.swift")
        sys.exit(2)
    body = match.group(1)
    # Map the Swift constant references to their wire strings via the
    # PWRunnerWire constants in PWRunnerAPI.swift.
    wire = parse_pwrunner_wire_filter_constants()
    pair_re = re.compile(
        r'\.init\(operation:\s*"([^"]+)"\s*,\s*filterKind:\s*(?:PWRunnerWire\.([A-Za-z]+)|"([^"]+)")',
    )
    pairs: set[tuple[str, str]] = set()
    for m in pair_re.finditer(body):
        operation = m.group(1)
        const_name = m.group(2)
        literal = m.group(3)
        if const_name:
            kind = wire.get(const_name)
            if kind is None:
                fail(
                    f"predictionUnavailableOpFilters references "
                    f"PWRunnerWire.{const_name} but no such constant is "
                    f"defined in runner/PWRunnerAPI.swift"
                )
                sys.exit(2)
        else:
            kind = literal
        pairs.add((operation, kind))
    return pairs


def parse_pwrunner_wire_filter_constants() -> dict[str, str]:
    text = PWRUNNER_API.read_text(encoding="utf-8")
    # Inside `enum PWRunnerWire` (or `public enum PWRunnerWire`), grab
    # `static let foo = "bar"` whether or not it's marked public.
    enum_re = re.compile(
        r'(?:public\s+)?enum PWRunnerWire\s*\{(.*?)\n\}',
        re.DOTALL,
    )
    match = enum_re.search(text)
    if match is None:
        return {}
    body = match.group(1)
    const_re = re.compile(
        r'(?:public\s+)?static let (\w+)\s*=\s*"([^"]*)"',
    )
    return {m.group(1): m.group(2) for m in const_re.finditer(body)}


def parse_orchestrator_prediction_unavailable_pairs() -> set[tuple[str, str]]:
    """CWorkerOrchestrator carries its own host-side mirror of the
    prediction_unavailable (op, filter) pair set. source_drift
    enforces it against the Swift / docs sets so a future addition
    to either doesn't leave the orchestrator silently routing the
    new pair through the validator (producing bad_filter responses
    instead of the synthesized prediction_unavailable verdict)."""
    text = CWORKER_ORCHESTRATOR.read_text(encoding="utf-8")
    block_re = re.compile(
        r'predictionUnavailableOpFiltersHostMirror[^\[]*\[(.*?)\n\]',
        re.DOTALL,
    )
    match = block_re.search(text)
    if match is None:
        fail("could not locate predictionUnavailableOpFiltersHostMirror in runner/CWorkerOrchestrator.swift")
        sys.exit(2)
    body = match.group(1)
    wire = parse_pwrunner_wire_filter_constants()
    pair_re = re.compile(
        r'\.init\(operation:\s*"([^"]+)"\s*,\s*filterKind:\s*(?:PWRunnerWire\.([A-Za-z]+)|"([^"]+)")',
    )
    pairs: set[tuple[str, str]] = set()
    for m in pair_re.finditer(body):
        operation = m.group(1)
        const_name = m.group(2)
        literal = m.group(3)
        if const_name:
            kind = wire.get(const_name)
            if kind is None:
                fail(
                    f"predictionUnavailableOpFiltersHostMirror references "
                    f"PWRunnerWire.{const_name} but no such constant is "
                    f"defined in runner/PWRunnerAPI.swift"
                )
                sys.exit(2)
        else:
            kind = literal
        pairs.add((operation, kind))
    return pairs


def parse_docs_prediction_unavailable_pairs() -> set[tuple[str, str]]:
    """Extract (op, filter) pairs from PolicyWitness.md "Currently in
    this category:" bullets, formatted as
    `(operation, filter_kind)` at the start of each bullet."""
    text = POLICYWITNESS_MD.read_text(encoding="utf-8")
    section_re = re.compile(
        r'## Filter kinds where prediction is unavailable.*?Currently in this category:\s*\n(.*?)(?:\n##|\Z)',
        re.DOTALL,
    )
    match = section_re.search(text)
    if match is None:
        fail(
            "could not locate 'Filter kinds where prediction is unavailable' "
            "section in PolicyWitness.md (or its 'Currently in this category:' marker)"
        )
        sys.exit(2)
    body = match.group(1)
    pair_re = re.compile(r'-\s*`\(([a-z][a-z0-9-]*)\s*,\s*([a-z][a-z0-9_]*)\)`')
    return {(m.group(1), m.group(2)) for m in pair_re.finditer(body)}


def check_prediction_unavailable_agreement() -> list[str]:
    swift_pairs = parse_swift_prediction_unavailable_pairs()
    docs_pairs = parse_docs_prediction_unavailable_pairs()
    orch_pairs = parse_orchestrator_prediction_unavailable_pairs()
    problems: list[str] = []
    # Treat the Swift ProbeRunner set as the canonical source and
    # compare every other source against it. A single canonical
    # reduces N^2 pair comparisons to N — and makes the failure
    # messages name the disagreeing source clearly.
    canonical = swift_pairs
    others = [
        ("docs (PolicyWitness.md)", docs_pairs),
        ("orchestrator host-mirror (CWorkerOrchestrator.swift)", orch_pairs),
    ]
    for label, other in others:
        for pair in sorted(canonical - other):
            problems.append(
                f"  prediction_unavailable: {pair} in swift (ProbeRunner.swift) but missing from {label}"
            )
        for pair in sorted(other - canonical):
            problems.append(
                f"  prediction_unavailable: {pair} in {label} but missing from swift (ProbeRunner.swift)"
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
    # Each C shim is its own SwiftPM target with its own sources block;
    # the union of those source sets has to match disk and build.sh.
    package_c_sources = (
        package_swift_sources("PWSandboxCheckShim")
        | package_swift_sources("PWCWorkerShim")
    )
    c_manifests = {
        "disk (runner/*.c)": disk_c_files(),
        "build.sh (XPC_RUNNER_*_SHIM)": build_sh_c_files(),
        "Package.swift (PWSandboxCheckShim + PWCWorkerShim sources)": package_c_sources,
    }

    problems: list[str] = []
    problems.extend(diff_sets("swift", swift_manifests))
    problems.extend(diff_sets("c", c_manifests))
    problems.extend(check_readmes_present())
    problems.extend(check_index_vs_disk())
    problems.extend(check_baseline_in_run_sh_defaults())
    problems.extend(check_runner_outcome_suites_have_matrix_rows())
    problems.extend(check_normalized_outcomes_have_matrix_rows())
    problems.extend(check_attempt_outcomes_have_matrix_rows())
    problems.extend(check_prediction_unavailable_agreement())

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
    attempt_outcome_count = len(parse_attempt_outcomes())
    pu_pairs = parse_swift_prediction_unavailable_pairs()
    print(
        f"all drift checks pass: "
        f"{len(swift_manifests['disk (runner/*.swift)'])} swift, "
        f"{len(c_manifests['disk (runner/*.c)'])} c, "
        f"{suite_count} suites, "
        f"{outcome_count} normalized outcomes, "
        f"{attempt_outcome_count} attempt outcomes, "
        f"{len(pu_pairs)} prediction_unavailable pairs."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
