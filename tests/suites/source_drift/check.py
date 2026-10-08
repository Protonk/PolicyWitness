#!/usr/bin/env python3
"""Verify the runner source list and the testing registry are consistent.

The check has two halves:

1. Source-set drift between meson.build's explicit host source lists and
   the on-disk runner source tree. The PWRunner target enumerates the Swift
   files and the PWCWorkerShim target the C shim that ship in PWRunner.xpc
   by explicit path; the test-only SwiftPM package (runner/Package.swift)
   compiles the same set but discovers it automatically by SwiftPM
   convention (everything under Sources/PWRunnerCore and the Sources/<Shim>
   dir). So the SwiftPM side == on-disk by construction, and the drift that
   can actually ship a broken binary is the manifest lagging the tree: a
   file added under Sources/PWRunnerCore but missing from the target never
   reaches the XPC binary (and vice versa). We compare disk and meson.build
   directly; the manifest is read by file-mode introspection, which needs no
   build directory.

2. Test-registry drift across what should be self-consistent project
   discipline:
     a. Every tests/suites/<name>/ with run.sh has README.md.
     b. Every Baseline-tier suite is in tests/catalog.json's default membership.
     c. Every tests/suites/<name>/ has a row in the suite-coverage
        table in tests/README.md, and every table row maps to a real
        suite directory.
     d. Every runner_outcome_<X> suite corresponds to an outcome in the
        coverage matrix in tests/COVERAGE.md.
     e. Every NormalizedOutcome constant in runner/Sources/PWRunnerCore/PWRunnerAPI.swift
        has a row in the coverage matrix.
     f. Every AttemptOutcome constant has a row in the attempt-outcome
        coverage matrix.
     g. The C and Swift C-worker attempt-kind enums agree by raw value
        and name.
     h. Every stored property of PWRunnerTestOverrides in PWRunnerAPI.swift
        has a row in the `_test_overrides` table in runner/README.md, and
        every row names a property. That table is the only documented
        key list; runner/AGENTS.md points at it rather than carrying one.
     i. The first paragraph under the "Sandboxed automation harnesses"
        heading is identical in AGENTS.md, runner/README.md and
        tests/README.md and docs/SIGNING.md. The note is carried in four
        places on purpose; each copy adds its own local paragraph after the
        shared one.
     j. Host invariance: no file under runner/Sources binds or calls a
        libsandbox entry point or loads the library. The XPC host never
        links, loads or calls libsandbox; the worker and the validator do.
        The check distinguishes comments and explanatory strings from native
        uses, with positive/negative controls on constructed Swift/C text.

Exit codes:
  0 — everything agrees
  1 — drift detected; details printed to stderr
  2 — script error (unable to parse a manifest)
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER_DIR = REPO_ROOT / "runner"
MESON_BUILD = REPO_ROOT / "meson.build"
# Runner sources live under SwiftPM-convention target dirs. The source-set
# checks discover the on-disk set by walking these; the per-symbol contract
# checks below read specific files out of the core target. Both reference
# these dirs rather than the runner root, so the suite survives moving a
# file within Sources/ — only relocating a target dir touches this list.
CORE_DIR = RUNNER_DIR / "Sources" / "PWRunnerCore"
SHIM_DIRS = [
    RUNNER_DIR / "Sources" / "PWCWorkerShim",
]
PWRUNNER_API = CORE_DIR / "PWRunnerAPI.swift"
PROBE_RUNNER = CORE_DIR / "ProbeRunner.swift"
CWORKER_ORCHESTRATOR = CORE_DIR / "CWorkerOrchestrator.swift"
CWORKER_SWIFT = CORE_DIR / "CWorker.swift"
PW_PROBE_RUNNER_ABI = REPO_ROOT / "controller" / "tools" / "pw_probe_runner" / "pw_probe_runner_abi.h"
POLICYWITNESS_MD = REPO_ROOT / "docs/PolicyWitness.md"
RUNNER_README = RUNNER_DIR / "README.md"
SUITES_DIR = REPO_ROOT / "tests" / "suites"
# The suite-coverage table lives in tests/README.md; the per-outcome
# coverage matrices live in tests/COVERAGE.md. (Both were formerly one
# tests/INDEX.md.)
TESTS_README = REPO_ROOT / "tests" / "README.md"
TESTS_COVERAGE = REPO_ROOT / "tests" / "COVERAGE.md"


def fail(msg: str) -> None:
    sys.stderr.write(msg + "\n")


# ---------------------------------------------------------------------------
# Source manifest checks.
#
# Both halves return paths relative to runner/ (POSIX), e.g.
# "Sources/PWRunnerCore/CWorker.swift", so the disk walk and meson.build's
# target sources compare directly without name-vs-path normalization.
# Discovery is recursive under the target dirs, so the suite does not assume
# any particular flat layout — moving a file within a target is invisible
# here; only adding/removing a compiled file (or forgetting to wire it into
# meson.build) trips the diff.
# ---------------------------------------------------------------------------

def disk_swift_files() -> set[str]:
    return {p.relative_to(RUNNER_DIR).as_posix() for p in CORE_DIR.rglob("*.swift")}


def disk_c_files() -> set[str]:
    out: set[str] = set()
    for shim_dir in SHIM_DIRS:
        out.update(p.relative_to(RUNNER_DIR).as_posix() for p in shim_dir.rglob("*.c"))
    return out


def meson_declared_targets() -> dict[str, list[str]]:
    """Targets and their sources as meson.build declares them.

    File-mode introspection reads the manifest without a build directory, so
    the host and shim declarations are listed regardless of the `xpc` guard; a
    configured directory would list only its active targets. Introspection
    failure is a script error: the manifest cannot be read, so nothing about
    its source list is known."""
    argv = ["meson", "introspect", str(MESON_BUILD), "--targets"]
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=60, cwd=REPO_ROOT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        fail(f"meson introspection failed: {' '.join(argv)}: {exc}")
        sys.exit(2)
    if result.returncode != 0:
        fail(f"meson introspection failed (rc={result.returncode}): {' '.join(argv)}\n{result.stderr.strip()}")
        sys.exit(2)
    try:
        targets = json.loads(result.stdout)
    except ValueError as exc:
        fail(f"meson introspection returned malformed JSON: {exc}")
        sys.exit(2)
    return {t["name"]: [s for group in t["target_sources"] for s in group.get("sources", [])] for t in targets}


def _meson_target_files(targets: dict[str, list[str]], name: str, domain: str, suffix: str,
                        entry_points: set[str], problems: list[str]) -> set[str]:
    """The runner-relative sources of one declared target inside one source domain.

    `entry_points` are accepted beside the domain (the service and client
    `main.swift` are not core sources); any other source is a problem, as is a
    missing target."""
    if name not in targets:
        problems.append(f"  meson: meson.build declares no {name!r} target")
        return set()
    files: set[str] = set()
    for source in targets[name]:
        try:
            relative = Path(source).resolve().relative_to(RUNNER_DIR.resolve()).as_posix()
        except ValueError:
            problems.append(f"  meson: {name} source {source!r} is outside runner/")
            continue
        if relative in entry_points:
            continue
        if relative.startswith(domain) and relative.endswith(suffix):
            files.add(relative)
        else:
            problems.append(f"  meson: {name} source {relative!r} is outside its domain {domain!r}")
    return files


def check_meson_source_lists() -> list[str]:
    """meson.build's host and shim source lists equal the tree.

    The PWRunner target carries the core Swift sources plus the service entry
    point; the PWCWorkerShim target carries the shim C sources. Each set is
    compared with its on-disk domain; a file in one set but not the other is
    reported by name, and a missing target is reported as such."""
    problems: list[str] = []
    targets = meson_declared_targets()
    swift = _meson_target_files(targets, "PWRunner", "Sources/PWRunnerCore/", ".swift",
                                {"Services/PWRunner/main.swift"}, problems)
    c = _meson_target_files(targets, "PWCWorkerShim", "Sources/PWCWorkerShim/", ".c", set(), problems)
    problems.extend(diff_sets("swift", {
        "disk (runner/Sources/PWRunnerCore/**/*.swift)": disk_swift_files(),
        "meson.build (PWRunner target)": swift,
    }))
    problems.extend(diff_sets("c", {
        "disk (runner/Sources/<shim>/**/*.c)": disk_c_files(),
        "meson.build (PWCWorkerShim target)": c,
    }))
    return problems


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


def default_suites_from_catalog() -> set[str]:
    groups = json.loads((REPO_ROOT / 'tests/catalog.json').read_text())['suites']
    return {name for name, group in groups.items()
            if any((case if isinstance(case, dict) else {}).get('default', group.get('default', True))
                   for case in group.get('cases', []))}


def parse_index_rows() -> dict[str, str]:
    """Return {suite_name: tier} parsed from the suite-coverage table
    in tests/README.md.

    Only the table under the "## Suite coverage" heading is considered;
    parsing stops at the next "## " heading so prose tables elsewhere in
    the README can't leak in.
    """
    text = TESTS_README.read_text(encoding="utf-8")
    parts = text.split("## Suite coverage", 1)
    if len(parts) != 2:
        fail("tests/README.md is missing the '## Suite coverage' section")
        sys.exit(2)
    section = parts[1]
    next_heading = re.search(r'^##\s', section, re.MULTILINE)
    if next_heading:
        section = section[: next_heading.start()]
    rows: dict[str, str] = {}
    row_re = re.compile(r'^\|\s*`([a-z][a-z0-9_]*)`\s*\|\s*([A-Za-z][^|]*?)\s*\|', re.MULTILINE)
    for match in row_re.finditer(section):
        rows[match.group(1)] = match.group(2).strip()
    return rows


def _parse_matrix_section(heading: str) -> set[str]:
    text = TESTS_COVERAGE.read_text(encoding="utf-8")
    parts = text.split(heading, 1)
    if len(parts) != 2:
        fail(f"tests/COVERAGE.md is missing the {heading!r} section")
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
        r'(?:public\s+)?enum ' + re.escape(enum_name) + r'\s*\{(.*?)\n\}',
        re.DOTALL,
    )
    match = enum_re.search(text)
    if match is None:
        fail(f"could not locate {enum_name} enum in runner/Sources/PWRunnerCore/PWRunnerAPI.swift")
        sys.exit(2)
    body = match.group(1)
    constant_re = re.compile(r'(?:public\s+)?static let \w+\s*=\s*"([a-z_][a-z0-9_]*)"')
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
    in_catalog = set(json.loads((REPO_ROOT / 'tests/catalog.json').read_text())['suites'])
    if in_catalog != on_disk:
        problems.append(f'  catalog: suite directories and catalog disagree: {sorted(in_catalog ^ on_disk)}')

    for name in sorted(on_disk - in_index):
        problems.append(f"  README: tests/suites/{name}/ exists but has no row in tests/README.md's suite-coverage table")
    for name in sorted(in_index - on_disk):
        problems.append(f"  README: tests/README.md has a suite-coverage row for {name!r} but no such tests/suites/{name}/ exists")
    return problems


def check_baseline_in_catalog_defaults() -> list[str]:
    problems: list[str] = []
    rows = parse_index_rows()
    defaults = default_suites_from_catalog()
    for name, tier in sorted(rows.items()):
        if tier.lower() != "baseline":
            continue
        if name not in defaults:
            problems.append(
                f"  catalog: Baseline-tier suite {name!r} is missing from tests/catalog.json's default membership"
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
            f"  matrix: NormalizedOutcome.{outcome} has no row in tests/COVERAGE.md "
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
            f"  matrix: AttemptOutcome.{outcome} has no row in tests/COVERAGE.md "
            f"attempt-outcome coverage matrix"
        )
    for outcome in sorted(matrix - outcomes):
        problems.append(
            f"  matrix: attempt-outcome matrix lists {outcome!r} but no "
            f"AttemptOutcome constant by that name exists"
        )
    return problems


# ---------------------------------------------------------------------------
# C-worker attempt-kind enum agreement.
#
# The host writes PWAttemptKind raw values into shm; the C worker reads those
# values as pw_attempt_kind_t. A mismatch is not a schema error, it is a runtime
# lie about which syscall ran. Keep the enums mechanically locked.
# ---------------------------------------------------------------------------

def _camel_to_screaming_snake(value: str) -> str:
    step1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', value)
    step2 = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', step1)
    return step2.upper()


def parse_c_attempt_kinds() -> dict[int, str]:
    text = PW_PROBE_RUNNER_ABI.read_text(encoding="utf-8")
    block_re = re.compile(r'typedef enum\s*\{(.*?)\}\s*pw_attempt_kind_t;', re.DOTALL)
    match = block_re.search(text)
    if match is None:
        fail("could not locate pw_attempt_kind_t in pw_probe_runner_abi.h")
        sys.exit(2)
    kinds: dict[int, str] = {}
    for m in re.finditer(r'\bPW_ATTEMPT_([A-Z0-9_]+)\s*=\s*(\d+)', match.group(1)):
        kinds[int(m.group(2))] = m.group(1)
    if not kinds:
        fail("pw_attempt_kind_t contains no parseable PW_ATTEMPT_* entries")
        sys.exit(2)
    return kinds


def parse_swift_attempt_kinds() -> dict[int, str]:
    text = CWORKER_SWIFT.read_text(encoding="utf-8")
    enum_re = re.compile(r'(?:public\s+)?enum PWAttemptKind:\s*UInt32\s*\{(.*?)\n\}', re.DOTALL)
    match = enum_re.search(text)
    if match is None:
        fail("could not locate PWAttemptKind in runner/Sources/PWRunnerCore/CWorker.swift")
        sys.exit(2)
    kinds: dict[int, str] = {}
    for m in re.finditer(r'\bcase\s+([A-Za-z][A-Za-z0-9]*)\s*=\s*(\d+)', match.group(1)):
        kinds[int(m.group(2))] = _camel_to_screaming_snake(m.group(1))
    if not kinds:
        fail("PWAttemptKind contains no parseable case entries")
        sys.exit(2)
    return kinds


def check_attempt_kind_enum_agreement() -> list[str]:
    problems: list[str] = []
    c_kinds = parse_c_attempt_kinds()
    swift_kinds = parse_swift_attempt_kinds()

    c_values = set(c_kinds)
    swift_values = set(swift_kinds)
    for value in sorted(c_values - swift_values):
        problems.append(
            f"  attempt-kind: C PW_ATTEMPT_{c_kinds[value]}={value} has no "
            f"matching PWAttemptKind raw value"
        )
    for value in sorted(swift_values - c_values):
        problems.append(
            f"  attempt-kind: Swift PWAttemptKind.{swift_kinds[value]}={value} "
            f"has no matching pw_attempt_kind_t value"
        )

    if c_values:
        expected = set(range(0, max(c_values) + 1))
        for value in sorted(expected - c_values):
            problems.append(f"  attempt-kind: pw_attempt_kind_t has a numeric gap at {value}")

    for value in sorted(c_values & swift_values):
        if c_kinds[value] != swift_kinds[value]:
            problems.append(
                f"  attempt-kind: value {value} is PW_ATTEMPT_{c_kinds[value]} in C "
                f"but PWAttemptKind.{swift_kinds[value]} in Swift"
            )
    return problems


# ---------------------------------------------------------------------------
# Prediction-unavailable (op, filter) pair agreement.
#
# The shared Swift set and documentation must list the same pairs:
#   - runner/Sources/PWRunnerCore/ProbeRunner.swift::predictionUnavailableOpFilters (canonical)
#   - docs/PolicyWitness.md "Filter kinds where prediction is unavailable"
#
# A pair added to one but not the other means a request that should skip
# in the runner disagrees with the documented runtime contract.
# The host planner must consume the shared set without another literal table.
# ---------------------------------------------------------------------------

def swift_code(text: str) -> str:
    """Mask comments and string contents for the mechanical planner guard.

    This is not a Swift parser. Preserve token separation, handle nested block
    comments, and mask ordinary/multiline strings so prose cannot satisfy the
    guard. The repository's planner structure is checked explicitly below.
    """
    strings = re.compile(r'""".*?"""|"(?:\\.|[^"\\])*"', re.DOTALL)
    result = []
    offset = 0
    while offset < len(text):
        if text.startswith('//', offset):
            end = text.find('\n', offset)
            offset = len(text) if end < 0 else end
            result.append(' ')
        elif text.startswith('/*', offset):
            depth = 1
            offset += 2
            while offset < len(text) and depth:
                if text.startswith('/*', offset):
                    depth += 1
                    offset += 2
                elif text.startswith('*/', offset):
                    depth -= 1
                    offset += 2
                else:
                    offset += 1
            result.append(' ')
        elif text[offset] == '"':
            match = strings.match(text, offset)
            if match is None:
                raise ValueError('unterminated Swift string in planner guard')
            result.append('""')
            offset = match.end()
        else:
            result.append(text[offset])
            offset += 1
    return ''.join(result)


def check_prediction_unavailable_planner() -> list[str]:
    prefix = '  prediction_unavailable planner: '
    try:
        code = swift_code(CWORKER_ORCHESTRATOR.read_text(encoding='utf-8'))
    except ValueError as exc:
        return [prefix + str(exc)]
    problems = []
    # No local pair collection, literal operation/filter entry, or shadow of
    # the shared symbol. Dynamic construction of the current query pair stays
    # valid. Check the whole host file so a table cannot move out of the function.
    if (re.search(r'Set\s*<\s*PredictionUnavailablePair\s*>|\[\s*PredictionUnavailablePair\s*\]', code)
            or re.search(r'(?:\.\s*init|\bPredictionUnavailablePair)\s*\(\s*operation\s*:\s*""\s*,\s*filterKind\s*:', code)
            or re.search(r'\b(?:let|var)\s+predictionUnavailableOpFilters\b', code)):
        problems.append(prefix + 'CWorkerOrchestrator.swift must not define a local exclusion table or shadow the shared set')
    match = re.search(r'\bfunc\s+planValidatorQueries\b[^{}]*\{', code)
    if match is None:
        return problems + [prefix + 'could not locate planValidatorQueries']
    start = end = match.end()
    depth = 1
    while end < len(code) and depth:
        depth += (code[end] == '{') - (code[end] == '}')
        end += 1
    if depth or not re.search(r'\bif\s+predictionUnavailableOpFilters\s*\.\s*contains\s*\(', code[start:end - 1]):
        problems.append(prefix + 'planValidatorQueries must use if predictionUnavailableOpFilters.contains(...)')
    return problems


def parse_swift_prediction_unavailable_pairs() -> set[tuple[str, str]]:
    text = PROBE_RUNNER.read_text(encoding="utf-8")
    # let predictionUnavailableOpFilters: Set<PredictionUnavailablePair> = [
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
        fail("could not locate predictionUnavailableOpFilters in runner/Sources/PWRunnerCore/ProbeRunner.swift")
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
                    f"defined in runner/Sources/PWRunnerCore/PWRunnerAPI.swift"
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


def parse_docs_prediction_unavailable_pairs() -> set[tuple[str, str]]:
    """Extract (op, filter) pairs from docs/PolicyWitness.md "Currently in
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
            "section in docs/PolicyWitness.md (or its 'Currently in this category:' marker)"
        )
        sys.exit(2)
    body = match.group(1)
    pair_re = re.compile(r'-\s*`\(([a-z][a-z0-9-]*)\s*,\s*([a-z][a-z0-9_]*)\)`')
    return {(m.group(1), m.group(2)) for m in pair_re.finditer(body)}


def check_prediction_unavailable_agreement() -> list[str]:
    swift_pairs = parse_swift_prediction_unavailable_pairs()
    docs_pairs = parse_docs_prediction_unavailable_pairs()
    problems: list[str] = []
    # Treat the Swift ProbeRunner set as the canonical source and
    # compare every other source against it. A single canonical
    # reduces N^2 pair comparisons to N — and makes the failure
    # messages name the disagreeing source clearly.
    canonical = swift_pairs
    others = [
        ("docs (docs/PolicyWitness.md)", docs_pairs),
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
# Host invariance: the XPC host source never names the native sandbox API.
#
# The host must not link, load or call libsandbox. Every native sandbox
# operation belongs to the worker (pw-probe-runner) or the validator
# (sb_api_validator). The host joins their observations without executing
# either child's sandbox API work. The companion binary check is
# tests/lib/artifact.py (`nm -u` on the shipped PWRunner).
# ---------------------------------------------------------------------------

# Native uses in the host, including the C shim. This is a source convention,
# not complete Swift/C analysis: computed symbol/library names are outside it.
HOST_SANDBOX_SYMBOLS = frozenset({
    'sandbox_check', 'sandbox_apply', 'sandbox_compile_string',
    'sandbox_create_params', 'sandbox_set_param', 'sandbox_free_params',
    'sandbox_free_profile', 'sandbox_free_error',
})


def host_tokens(text):
    """Tokens and original offsets; comments disappear, literals retain context."""
    tokens = []
    literal_pattern = re.compile(r'(\#*)("""|"|\')')
    token_pattern = re.compile(r'[A-Za-z_][A-Za-z_0-9]*|[^\s]')
    offset = 0
    while offset < len(text):
        if text.startswith('//', offset):
            end = text.find('\n', offset)
            offset = len(text) if end < 0 else end
            continue
        if text.startswith('/*', offset):
            depth = 1
            offset += 2
            while offset < len(text) and depth:
                if text.startswith('/*', offset):
                    depth += 1
                    offset += 2
                elif text.startswith('*/', offset):
                    depth -= 1
                    offset += 2
                else:
                    offset += 1
            if depth:
                raise ValueError('unterminated block comment')
            continue
        literal = literal_pattern.match(text, offset)
        if literal:
            start = offset
            hashes, quote = literal.groups()
            offset += len(literal.group())
            body = offset
            closing = quote + hashes
            escape = '\\' + hashes
            while offset < len(text) and not text.startswith(closing, offset):
                offset += len(escape) + 1 if text.startswith(escape, offset) else 1
            if offset >= len(text):
                raise ValueError('unterminated string literal')
            tokens.append((text[body:offset], start, True))
            offset += len(closing)
            continue
        match = token_pattern.match(text, offset)
        if match:
            tokens.append((match.group(), offset, False))
            offset += len(match.group())
        else:
            offset += 1
    return tokens


def host_invariance_problems(label: str, text: str) -> list[str]:
    """Find native calls/bindings and literal sandbox lookups, allowing prose."""
    try:
        tokens = host_tokens(text)
    except ValueError as exc:
        return [f'  host invariance: {label}: {exc}']
    # Simple Swift/C constants, including typed Swift lets and C #defines.
    constants = {}
    for i, (value, _, literal) in enumerate(tokens):
        if literal or value not in ('let', 'var', 'const', 'define'):
            continue
        end = i + 1
        while end < len(tokens) and tokens[end][0] not in ('=', ';', '{', '}'):
            if tokens[end][2]:
                break
            end += 1
        if end < len(tokens) and tokens[end][0] == '=':
            name = tokens[i + 1][0] if value in ('let', 'var') else tokens[end - 1][0]
            end += 1
        elif value == 'define' and i + 2 < len(tokens):
            name, end = tokens[i + 1][0], i + 2
        else:
            continue
        if end < len(tokens) and tokens[end][2]:
            constants[name] = tokens[end][0]

    def argument_value(argument):
        if len(argument) != 1:
            return None
        value, _, literal = argument[0]
        return value if literal else constants.get(value)

    problems = []
    for i, (name, offset, literal) in enumerate(tokens[:-1]):
        if literal or tokens[i + 1][0] != '(' or tokens[i + 1][2]:
            continue
        prohibited = name if name in HOST_SANDBOX_SYMBOLS else None
        if name in ('_silgen_name', '_cdecl', 'asm', '__asm', '__asm__', 'dlsym', 'dlopen'):
            arguments, current, depth = [], [], 0
            for token in tokens[i + 2:]:
                value, _, quoted = token
                if not quoted and value == ')' and depth == 0:
                    arguments.append(current)
                    break
                if not quoted and value == ',' and depth == 0:
                    arguments.append(current)
                    current = []
                    continue
                if not quoted and value in ('(', '[', '{'):
                    depth += 1
                elif not quoted and value in (')', ']', '}'):
                    depth -= 1
                current.append(token)
            index = 1 if name == 'dlsym' else 0
            value = argument_value(arguments[index]) if len(arguments) > index else None
            if name == 'dlopen':
                if value and re.fullmatch(r'libsandbox(?:\.[0-9]+)*\.dylib', Path(value).name):
                    prohibited = f'{name}({value})'
            elif value in HOST_SANDBOX_SYMBOLS:
                prohibited = f'{name}({value})'
        if prohibited:
            line = text.count('\n', 0, offset) + 1
            problems.append(f'  host invariance: {label}:{line} uses {prohibited}; '
                            'the XPC host never links, loads or calls libsandbox')
    return problems


def check_host_invariance() -> list[str]:
    problems: list[str] = []
    for path in sorted((RUNNER_DIR / 'Sources').rglob('*')):
        if path.suffix in ('.swift', '.c', '.h', '.m', '.mm'):
            problems.extend(host_invariance_problems(str(path.relative_to(REPO_ROOT)), path.read_text(encoding='utf-8')))
    return problems


def host_invariance_controls() -> list[str]:
    """Controls distinguish native use from schema, prose and unrelated APIs."""
    problems = []
    accepted = [
        'let name = "sandbox_check(pid) and dlopen(x) are examples"',
        '// sandbox_apply(p)\n/* outer /* sandbox_free_error(e) */ dlsym(h, "sandbox_check") */',
        'var sandbox_check: PWRunnerSandboxCheckResult\nenum CodingKeys { case sandbox_check }',
        'let label = "sandbox_check"\nlet policy = """\n(allow default)\n"""',
        'let f: @convention(c) (Int32) -> Int32 = ptr',
        'let h = dlopen("/usr/lib/libSystem.B.dylib", RTLD_NOW)',
        'let f = dlsym(h, "malloc")',
        'let library = "/usr/lib/libSystem.B.dylib"\nlet h = dlopen(library, RTLD_NOW)',
        'let name: String = "malloc"\nlet f = dlsym(h, name)',
        '@_silgen_name("posix_spawn") func spawn() -> Int32',
        'let example = #"dlopen("/usr/lib/libsandbox.dylib", RTLD_NOW)"#',
    ]
    rejected = []
    for name in sorted(HOST_SANDBOX_SYMBOLS):
        rejected += [
            f'{name}(value)',
            f'int {name}(void *value);',
            f'@_silgen_name("{name}") func native() -> Int32',
            f'let f = dlsym(handle, "{name}")',
            f'let symbol: String = "{name}"\nlet f = dlsym(handle, symbol)',
            f'const char *symbol = "{name}"; void *f = dlsym(handle, symbol);',
            f'#define SYMBOL "{name}"\nvoid *f = dlsym(handle, SYMBOL);',
        ]
    rejected += [
        'let h = dlopen("/usr/lib/libsandbox.dylib", RTLD_NOW)',
        'let library = "/usr/lib/libsandbox.1.dylib"\nlet h = dlopen(library, RTLD_NOW)',
        'const char *library = "/usr/lib/libsandbox.dylib"; void *h = dlopen(library, RTLD_NOW);',
        '@_silgen_name(#"sandbox_check"#) func native() -> Int32',
        'extern int native(void) __asm__("sandbox_check");',
    ]
    for expected, snippets in ((False, accepted), (True, rejected)):
        for snippet in snippets:
            found = host_invariance_problems('control', snippet)
            if bool(found) != expected:
                problems.append(f'  host invariance control: expected rejection={expected}: {snippet!r}: {found}')
    return problems


# ---------------------------------------------------------------------------
# `_test_overrides` key table agreement.
#
# runner/README.md's test-seam table is the only documented list of override
# keys; runner/AGENTS.md points at it instead of carrying a copy. Lock the
# table to the Codable struct so a key added to one cannot ship without the
# other.
# ---------------------------------------------------------------------------

def parse_test_override_fields() -> set[str]:
    text = PWRUNNER_API.read_text(encoding="utf-8")
    struct_re = re.compile(
        r'(?:public\s+)?struct PWRunnerTestOverrides\s*:\s*Codable\s*\{(.*?)\n\}',
        re.DOTALL,
    )
    match = struct_re.search(text)
    if match is None:
        fail("could not locate PWRunnerTestOverrides in runner/Sources/PWRunnerCore/PWRunnerAPI.swift")
        sys.exit(2)
    field_re = re.compile(r'^\s*(?:public\s+)?var ([a-z_][a-z0-9_]*)\s*:', re.MULTILINE)
    fields = {m.group(1) for m in field_re.finditer(match.group(1))}
    if not fields:
        fail("PWRunnerTestOverrides contains no parseable stored properties")
        sys.exit(2)
    return fields


def parse_readme_test_override_rows() -> set[str]:
    """Return the keys tabulated under runner/README.md's
    "## Test seam: `_test_overrides`" heading. Parsing stops at the next
    "## " heading so other tables in the README can't leak in."""
    text = RUNNER_README.read_text(encoding="utf-8")
    heading = "## Test seam: `_test_overrides`"
    parts = text.split(heading, 1)
    if len(parts) != 2:
        fail(f"runner/README.md is missing the {heading!r} section")
        sys.exit(2)
    section = parts[1]
    next_heading = re.search(r'^##\s', section, re.MULTILINE)
    if next_heading:
        section = section[: next_heading.start()]
    row_re = re.compile(r'^\|\s*`([a-z_][a-z0-9_]*)`\s*\|', re.MULTILINE)
    return {m.group(1) for m in row_re.finditer(section)}


def check_test_overrides_table_agreement() -> list[str]:
    problems: list[str] = []
    fields = parse_test_override_fields()
    rows = parse_readme_test_override_rows()
    for name in sorted(fields - rows):
        problems.append(
            f"  test_overrides: PWRunnerTestOverrides.{name} has no row in "
            f"runner/README.md's test-seam table"
        )
    for name in sorted(rows - fields):
        problems.append(
            f"  test_overrides: runner/README.md's test-seam table lists {name!r} "
            f"but PWRunnerTestOverrides has no such property"
        )
    return problems


# ---------------------------------------------------------------------------
# Sandboxed-harness note agreement.
#
# The note under "Sandboxed automation harnesses" is carried in four files on
# purpose: AGENTS.md (orientation), runner/README.md (what the refusal looks
# like in the envelope), tests/README.md (what the dispatcher can detect) and
# docs/SIGNING.md (which build steps need an unsandboxed shell).
# Each copy adds a local paragraph; the first paragraph is shared and must stay
# identical so the copies read as one maintained note rather than drift.
# Whitespace is normalized because the READMEs hard-wrap and AGENTS.md does not.
# ---------------------------------------------------------------------------

HARNESS_NOTE_HEADING = "Sandboxed automation harnesses"
HARNESS_NOTE_FILES = [REPO_ROOT / "AGENTS.md", RUNNER_README, TESTS_README, REPO_ROOT / "docs/SIGNING.md"]


def parse_harness_note_paragraph(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    heading_re = re.compile(
        r'^#{2,6}\s+' + re.escape(HARNESS_NOTE_HEADING) + r'\s*$', re.MULTILINE
    )
    match = heading_re.search(text)
    if match is None:
        fail(f"{path.relative_to(REPO_ROOT)} has no '{HARNESS_NOTE_HEADING}' heading")
        sys.exit(2)
    paragraphs = [p for p in re.split(r'\n\s*\n', text[match.end():]) if p.strip()]
    if not paragraphs:
        fail(f"{path.relative_to(REPO_ROOT)}: '{HARNESS_NOTE_HEADING}' has no paragraph")
        sys.exit(2)
    return " ".join(paragraphs[0].split())


def check_harness_note_agreement() -> list[str]:
    problems: list[str] = []
    canonical_path = HARNESS_NOTE_FILES[0]
    canonical = parse_harness_note_paragraph(canonical_path)
    for path in HARNESS_NOTE_FILES[1:]:
        if parse_harness_note_paragraph(path) != canonical:
            problems.append(
                f"  harness note: the shared first paragraph differs between "
                f"{canonical_path.relative_to(REPO_ROOT)} and {path.relative_to(REPO_ROOT)}. "
                f"This note is carried in four places on purpose; edit all four copies together or none."
            )
    return problems


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# CLI surface agreement.
#
# controller/README.md ("CLI surface (contract)") promises the exact usage
# lines and controller/src/cli.rs prints them. A flag added or removed on one
# side only ships a README that lies about the binary; compare the lines.
# ---------------------------------------------------------------------------
CLI_RS = REPO_ROOT / "controller" / "src" / "cli.rs"
CONTROLLER_README = REPO_ROOT / "controller" / "README.md"


def parse_cli_usage_lines() -> list[str]:
    if not CLI_RS.is_file():
        return []
    text = CLI_RS.read_text(encoding="utf-8")
    match = re.search(r"usage:\n(.*?)\n\nnotes:", text, re.DOTALL)
    if match is None:
        return []
    return [line[2:] for line in match.group(1).splitlines() if line.startswith("  policy-witness ")]


def parse_readme_surface_lines() -> list[str]:
    if not CONTROLLER_README.is_file():
        return []
    text = CONTROLLER_README.read_text(encoding="utf-8")
    match = re.search(r"## CLI surface \(contract\).*?```text\n(.*?)```", text, re.DOTALL)
    if match is None:
        return []
    return [line for line in match.group(1).splitlines() if line.startswith("policy-witness ")]


def check_cli_surface_agreement() -> list[str]:
    problems: list[str] = []
    cli = parse_cli_usage_lines()
    readme = parse_readme_surface_lines()
    if not cli:
        problems.append("controller/src/cli.rs: could not locate the usage block (usage: ... notes:)")
    if not readme:
        problems.append("controller/README.md: could not locate the CLI surface (contract) text block")
    if cli and readme and cli != readme:
        problems.append("CLI surface drift between controller/src/cli.rs usage and controller/README.md:")
        problems.extend(f"  cli.rs   : {line}" for line in cli)
        problems.extend(f"  README.md: {line}" for line in readme)
    return problems


ARCHITECTURE_DOC = REPO_ROOT / "docs/ARCHITECTURE.md"
SHAPE_GOLDENS = {"reply": REPO_ROOT / "tests/fixtures/contract/response_shape.json",
                 "envelope": REPO_ROOT / "tests/fixtures/contract/envelope_shape.json"}


def architecture_prose() -> str:
    """The handwritten text of the architecture document: no generated regions, no fenced blocks."""
    text = ARCHITECTURE_DOC.read_text()
    text = re.sub(r"<!-- BEGIN GENERATED ARCHITECTURE GRAPH \S+ -->.*?<!-- END GENERATED ARCHITECTURE GRAPH \S+ -->",
                  "", text, flags=re.S)
    kept, fence = [], None
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            delimiter = match.group(1)
            if fence is None:
                fence = delimiter
            elif delimiter[0] == fence[0] and len(delimiter) >= len(fence):
                fence = None
        elif fence is None:
            kept.append(line)
    return "\n".join(kept)


def heading_anchor(heading: str) -> str:
    return re.sub(r"[^\w -]", "", heading.lower()).replace(" ", "-")


def section(prose: str, heading: str) -> str | None:
    match = re.search(r"^## " + re.escape(heading) + r"\s*$(.*?)(?=^## |\Z)", prose, re.M | re.S)
    return match.group(1) if match else None


def check_known_gap_index() -> list[str]:
    """Every paragraph opening with "Known gap" is indexed, in order, by the last section, which lists nothing else."""
    prose = architecture_prose()
    headings = [(m.start(), m.group(1).strip()) for m in re.finditer(r"^## (.+?)\s*$", prose, re.M)]
    if not headings or headings[-1][1] != "Known gaps":
        return ["  known gaps: docs/ARCHITECTURE.md must end with a '## Known gaps' section"]
    index_start = headings[-1][0]
    gaps = []
    for paragraph in re.finditer(r"(?:(?<=\n\n)|^)Known gap[^\n]*(?:\n(?!\n)[^\n]*)*", prose, re.M):
        owner = [h for h in headings if h[0] < paragraph.start()]
        if paragraph.start() >= index_start or not owner:
            return [f"  known gaps: a Known gap paragraph must sit under the section whose promise it limits: {paragraph.group(0)[:60]!r}"]
        gaps.append(heading_anchor(owner[-1][1]))
    bullets = re.findall(r"^- (.*)$", prose[index_start:], re.M)
    linked = []
    for bullet in bullets:
        match = re.match(r"\[[^\]]+\]\(#([^)]+)\)", bullet)
        if not match:
            return [f"  known gaps: an index bullet must open with a link to its section: {bullet[:60]!r}"]
        linked.append(match.group(1))
    if linked != gaps:
        return [f"  known gaps: the index lists {linked} but the Known gap paragraphs sit under {gaps}"]
    return []


def check_evidence_channel_paths() -> list[str]:
    """Every landing path in the evidence-channels table resolves in a shape golden."""
    prose = architecture_prose()
    body = section(prose, "Evidence channels and ownership")
    if body is None:
        return ["  evidence channels: section missing from docs/ARCHITECTURE.md"]
    rows = [line for line in body.splitlines()
            if line.startswith("| ") and not line.startswith(("| Channel", "| ---"))]
    if not rows:
        return ["  evidence channels: table missing from docs/ARCHITECTURE.md"]
    shapes = {name: set(json.loads(path.read_text())["shape"]) for name, path in SHAPE_GOLDENS.items()}
    problems: list[str] = []
    for row in rows:
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if len(cells) < 4:
            problems.append(f"  evidence channels: row has no landing column: {row[:60]!r}")
            continue
        for path in re.findall(r"`([^`]+)`", cells[3]):
            golden = "envelope" if path.startswith("data.") else "reply"
            if f"{golden}.{path}" not in shapes[golden]:
                problems.append(f"  evidence channels: `{path}` is not a key of the {golden} shape golden")
    return problems


def check_core_ideas_agreement() -> list[str]:
    """The principles list in the architecture document names the core ideas of AGENTS.md, in order."""
    ideas = section((REPO_ROOT / "AGENTS.md").read_text(), "Core ideas")
    principles = section(architecture_prose(), "Principles as enforced constraints")
    if ideas is None or principles is None:
        return ["  core ideas: AGENTS.md 'Core ideas' or docs/ARCHITECTURE.md 'Principles as enforced constraints' is missing"]
    expected = re.findall(r"^- \*\*(.+?)\*\*", ideas, re.M)
    actual = [lead.rstrip(".") for lead in re.findall(r"^- \*\*(.+?)\*\*", principles, re.M)]
    if not expected or expected != actual:
        return [f"  core ideas: AGENTS.md lists {expected} but the architecture principles are {actual}"]
    return []


def main() -> int:
    # SwiftPM auto-discovers the same files off disk (convention layout, no
    # sources: arrays to parse), so the load-bearing comparison is the on-disk
    # Sources/ tree against the explicit list that builds a PWRunner.xpc:
    # meson.build's PWRunner target.
    problems: list[str] = []
    problems.extend(check_meson_source_lists())
    problems.extend(check_readmes_present())
    problems.extend(check_index_vs_disk())
    problems.extend(check_baseline_in_catalog_defaults())
    problems.extend(check_runner_outcome_suites_have_matrix_rows())
    problems.extend(check_normalized_outcomes_have_matrix_rows())
    problems.extend(check_attempt_outcomes_have_matrix_rows())
    problems.extend(check_attempt_kind_enum_agreement())
    problems.extend(check_prediction_unavailable_agreement())
    problems.extend(check_prediction_unavailable_planner())
    problems.extend(check_test_overrides_table_agreement())
    problems.extend(check_harness_note_agreement())
    problems.extend(check_cli_surface_agreement())
    problems.extend(host_invariance_controls())
    problems.extend(check_host_invariance())
    problems.extend(check_known_gap_index())
    problems.extend(check_evidence_channel_paths())
    problems.extend(check_core_ideas_agreement())

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
        f"{len(disk_swift_files())} swift, "
        f"{len(disk_c_files())} c, "
        f"{suite_count} suites, "
        f"{outcome_count} normalized outcomes, "
        f"{attempt_outcome_count} attempt outcomes, "
        f"{len(pu_pairs)} prediction_unavailable pairs, "
        f"{len(parse_test_override_fields())} test override keys."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
