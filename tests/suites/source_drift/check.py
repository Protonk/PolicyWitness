#!/usr/bin/env python3
"""Verify the runner source list and the testing registry are consistent.

The check has two halves:

1. Source-set drift between meson.build's explicit source lists and the
   tree. Every native target is pinned: the PWRunner target enumerates the
   Swift files that ship in PWRunner.xpc, the PWCWorkerShim target the C
   shim, the client's explicit shared contract sources and entry point, and
   each native helper's entry source. The
   test-only SwiftPM package (runner/Package.swift) compiles the host set
   but discovers it automatically by SwiftPM convention, so the SwiftPM
   side == on-disk by construction, and the drift that can actually ship a
   broken binary is the manifest lagging the tree, or naming a substitute.
   The shared reader in tests/lib/native_sources.py reads the manifest in
   file mode, which needs no build directory, and refuses a target name
   declared twice; build.sh applies the same expectation to the configured
   build directory after compiling.

2. Test-registry drift across what should be self-consistent project
   discipline:
     a. Every tests/suites/<name>/ has README.md, and every run.sh under
        one is a case command named by tests/catalog.json.
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
     h. Every stored property of PWRunnerTestOverrides in PWRunnerRequest.swift
        has a row in the `_test_overrides` table in runner/README.md, and
        every row names a property. That table is the only documented
        key list; runner/AGENTS.md points at it rather than carrying one.
     i. AGENTS.md, runner/AGENTS.md, tests/AGENTS.md and docs/BUILD.md each
        have a nonempty "Sandboxed automation harnesses" section. The root
        section links to the other three diagnostic sections. Wording is
        independent; section presence and routes do not establish good advice.
     j. Host invariance: no file under runner/Sources binds or calls a
        libsandbox entry point or loads the library. The XPC host never
        links, loads or calls libsandbox; the worker and the validator do.
        The check distinguishes comments and explanatory strings from native
        uses; the planner holds its positive/negative controls on constructed
        Swift/C text.

Every rule is a row of RULES: an ID, the function and its declared inputs.
Rules read the tree they are given and return records; the shared dispatcher
in tests/lib/drift_rules.py runs each selected row once, in table order, and
turns an expected-input failure (a missing file or section, an enum or struct
the parser cannot locate, invalid JSON, a Meson introspection failure) into a
precondition record for that rule alone, so the remaining rules still run.

Exit codes:
  0 — every selected rule evaluated and agreed
  1 — drift detected (including a document the Markdown reader refuses); details on stderr
  2 — at least one rule was blocked by its input; every other rule still ran and reported
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tests" / "lib"))
import native_sources  # noqa: E402  (shared with the order-barrier control and build.sh)
sys.path.insert(0, str(REPO_ROOT / "docs"))
import markdown_reader  # noqa: E402  (every Markdown structure below is read through it)
import repository_tree  # noqa: E402  (explicit-root inventories and reads)
import drift_rules  # noqa: E402  (rule rows, records and the dispatcher)
from drift_rules import InputFailure, Problem, Rule  # noqa: E402
from repository_tree import directory, inventory, members, optional, pattern, required  # noqa: E402

# Runner sources live under SwiftPM-convention target dirs. The source-set
# checks discover the on-disk set by walking these; the per-symbol contract
# checks below read specific files out of the core target. Both reference
# these dirs rather than the runner root, so the suite survives moving a
# file within Sources/ — only relocating a target dir touches this list.
# Every path here is repository-relative; a Tree supplies the root.
MESON_BUILD = "meson.build"
MESON_OPTIONS = "meson.options"
RUNNER_SOURCES = "runner/Sources"
CORE_DIR = "runner/Sources/PWRunnerCore"
SHIM_DIRS = ("runner/Sources/PWCWorkerShim",)
PWRUNNER_API = "runner/Sources/PWRunnerCore/PWRunnerAPI.swift"
PWRUNNER_REQUEST = "runner/Sources/PWRunnerCore/PWRunnerRequest.swift"
PROBE_RUNNER = "runner/Sources/PWRunnerCore/ProbeRunner.swift"
CWORKER_REQUEST_PLANNING = "runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift"
CWORKER_ORCHESTRATION_SOURCES = (
    CWORKER_REQUEST_PLANNING,
    "runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift",
    "runner/Sources/PWRunnerCore/CWorkerStepResults.swift",
    "runner/Sources/PWRunnerCore/CWorkerComparison.swift",
    "runner/Sources/PWRunnerCore/CWorkerDisposition.swift",
)
CWORKER_SWIFT = "runner/Sources/PWRunnerCore/CWorker.swift"
PW_PROBE_RUNNER_ABI = "controller/tools/pw_probe_runner/pw_probe_runner_abi.h"
POLICYWITNESS_MD = "docs/PolicyWitness.md"
RUNNER_README = "runner/README.md"
SUITES_DIR = "tests/suites"
CATALOG = "tests/catalog.json"
# The suite-coverage table lives in tests/README.md; the per-outcome
# coverage matrices live in tests/COVERAGE.md. (Both were formerly one
# tests/INDEX.md.)
TESTS_README = "tests/README.md"
TESTS_COVERAGE = "tests/COVERAGE.md"
MARKDOWN_HELPERS = tuple(markdown_reader.source_files())


def fail(msg: str) -> None:
    sys.stderr.write(msg + "\n")


def problem(key: str, message: str, path: str | None = None, line: int | None = None) -> Problem:
    """A drift record; the dispatcher stamps the rule ID."""
    return Problem(key, message, path, line)


def markdown(tree: repository_tree.Tree, relative: str):
    """A document parsed through the reader, reused within the tree by content and name."""
    return tree.parsed(relative, markdown_reader.parse)


def _json_input(text: str, name: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise InputFailure("input.json", f"{name}: invalid JSON: {error}", name, error.lineno) from error


def json_input(tree: repository_tree.Tree, relative: str):
    return tree.parsed(relative, _json_input)


# ---------------------------------------------------------------------------
# Source manifest checks.
#
# The disk walks here feed the summary line; the comparison itself lives in
# tests/lib/native_sources.py, which walks the same directories recursively
# and reports repository-relative paths. Moving a file within a target is
# invisible there; adding or removing a compiled file, or forgetting to wire
# it into meson.build, trips the diff.
# ---------------------------------------------------------------------------

CORE_SWIFT = repository_tree.Scope("core swift sources", (".swift",), base=CORE_DIR)
SHIM_C = tuple(repository_tree.Scope("shim C sources", (".c",), base=shim) for shim in SHIM_DIRS)
RUNNER_NATIVE = repository_tree.Scope("runner native sources", (".swift", ".c", ".h", ".m", ".mm"), base=RUNNER_SOURCES)


def disk_swift_files(tree: repository_tree.Tree) -> set[str]:
    return set(tree.inventory(CORE_SWIFT))


def disk_c_files(tree: repository_tree.Tree) -> set[str]:
    out: set[str] = set()
    for scope in SHIM_C:
        out.update(tree.inventory(scope))
    return out


def check_meson_source_lists(tree: repository_tree.Tree) -> list[Problem]:
    """meson.build's targets carry exactly the sources the tree holds for them.

    The shared reader lists the manifest's declarations in file mode, refuses
    a target name declared more than once, and compares every target with the
    tree: the host's core files plus the service entry point, the shim's C
    files, the client's shared contract sources and entry point, and each native
    helper's known entry source. build.sh
    applies the same expectation to the configured build directory after
    compiling. Both check membership only."""
    try:
        targets, problems = native_sources.declared_targets(tree.path(MESON_BUILD))
    except native_sources.IntrospectionError as exc:
        raise InputFailure("meson.introspection", str(exc), MESON_BUILD) from exc
    lines = problems + native_sources.problems(targets, native_sources.expected(tree.root), "meson.build")
    return [problem("meson.source_list", line, MESON_BUILD) for line in lines]


# ---------------------------------------------------------------------------
# Test-registry parsers
# ---------------------------------------------------------------------------

def suite_directories(tree: repository_tree.Tree) -> set[str]:
    """Every directory under tests/suites/ is a suite directory.

    A suite's cases reach the tree only through the catalog, so the directory
    set is the registry's on-disk side regardless of which scripts a suite
    holds; an include-only group such as opt_in has a README and no script."""
    suites = tree.path(SUITES_DIR)
    if not suites.is_dir():
        raise InputFailure("suites.missing_directory", f"missing suites directory: {SUITES_DIR}", SUITES_DIR)
    return {child.name for child in suites.iterdir() if child.is_dir() and child.name != "__pycache__"}


def suites_missing_readme(tree: repository_tree.Tree) -> list[str]:
    return sorted(name for name in suite_directories(tree) if not tree.exists(f"{SUITES_DIR}/{name}/README.md"))


def catalog_suites(tree: repository_tree.Tree) -> dict:
    data = json_input(tree, CATALOG)
    if not isinstance(data, dict) or not isinstance(data.get("suites"), dict):
        raise InputFailure("input.shape", f"{CATALOG}: no suites object", CATALOG)
    return data["suites"]


def catalog_commands(tree: repository_tree.Tree) -> set[str]:
    """Repository-relative scripts the catalog names as case commands, after suite inheritance."""
    out: set[str] = set()
    for group in catalog_suites(tree).values():
        for case in group.get('cases', []):
            command = (case if isinstance(case, dict) else {}).get('command', group.get('command'))
            if isinstance(command, list) and len(command) > 1:
                out.add(str(command[1]))
    return out


# A case script invoked: `bash tests/suites/...`, `./tests/suites/...`, or a bare script
# path standing as a command line. A bare path in a code span is a location unless
# the prose in front of it tells the reader to run it.
CASE_COMMAND = re.compile(r'(?:^|\s)(?:bash\s+|\./)tests/suites/[A-Za-z0-9_./-]+\.(?:sh|py)(?:\s|$)')
BARE_CASE_SCRIPT = re.compile(r'^tests/suites/[A-Za-z0-9_./-]+\.sh(?:\s|$)')
RUN_WORDS = re.compile(r'(?:^|\W)(?:run|runs|invoke|invokes|execute|executes|start|starts)\W*$', re.I)
RETIRED_DIRECT_OUTPUT = 'runs/direct'
# The one test interface may appear in release production only without selectors.
RELEASE_INPUTS = (optional('Makefile'), optional('tests/accept-release.sh'), pattern('tests/lib/release_*.py'))
TEST_SELECTORS = ('--suite', '--case', '--all')
RUN_SH_REMAINDER = re.compile(r"^(?:$|[;\"'\]\\]|--prune\b)")


def markdown_documents(tree: repository_tree.Tree) -> list[str]:
    """Every Markdown document the repository maintains, as relative paths: the
    command-document scope's pruned walk of the tree (the planner's disposable
    checkout is not a git repository, so Git is not consulted)."""
    return tree.inventory(repository_tree.COMMAND_DOCUMENTS)


def check_no_direct_case_commands_in_docs(tree: repository_tree.Tree) -> list[Problem]:
    """No document shows a case script as a command or names the retired direct output.

    A case runs only through tests/run.sh; a documented `bash tests/suites/...`, a
    `./tests/suites/...`, a fenced script line or a sentence telling the reader to
    run a script path is a second route in prose."""
    problems: list[Problem] = []
    for relative in markdown_documents(tree):
        try:
            document = markdown(tree, relative)
        except markdown_reader.Refused as error:
            problems.append(problem("reader.refused", f"  commands: {error}", relative))
            continue
        if RETIRED_DIRECT_OUTPUT in document.text:
            problems.append(problem("commands.retired_output",
                                    f"  commands: {relative} names the retired direct output tests/out/{RETIRED_DIRECT_OUTPUT}",
                                    relative))
        for block in document.blocks:
            if block.kind != 'fence':
                continue
            for line in block.content.splitlines():
                stripped = line.strip()
                if CASE_COMMAND.search(stripped) or BARE_CASE_SCRIPT.match(stripped):
                    problems.append(problem("commands.case_script",
                                            f"  commands: {relative} shows a case script as a command: {stripped[:80]!r}; "
                                            "cases run only through tests/run.sh", relative, block.lines[0] + 1))
        for inline in document.inlines:
            pieces = inline.pieces
            for index, (kind, value) in enumerate(pieces):
                if kind != 'code':
                    continue
                span = value.strip()
                told_to_run = (index > 0 and pieces[index - 1][0] == 'text' and bool(RUN_WORDS.search(pieces[index - 1][1])))
                if CASE_COMMAND.search(span) or (BARE_CASE_SCRIPT.match(span) and told_to_run):
                    problems.append(problem("commands.case_script",
                                            f"  commands: {relative} shows a case script as a command: {span[:80]!r}; "
                                            "cases run only through tests/run.sh", relative, inline.lines[0] + 1))
    return problems


def check_release_production_runs_the_default_battery(tree: repository_tree.Tree) -> list[Problem]:
    """Release production invokes tests/run.sh only without selectors.

    The Makefile, the acceptance entry point and the release helpers may name
    no `--suite`, `--case` or `--all`, and every `tests/run.sh` they invoke ends
    the command or continues with `--prune`; comment lines are not commands."""
    problems: list[Problem] = []
    for relative in tree.expand(RELEASE_INPUTS):
        for number, line in enumerate(tree.read_text(relative).splitlines(), 1):
            if line.lstrip().startswith('#'):
                continue
            for selector in TEST_SELECTORS:
                if re.search(r'(?<![\w-])' + re.escape(selector) + r'(?![\w-])', line):
                    problems.append(problem("release.selector",
                                            f"  release: {relative}:{number} names the test selector {selector}; "
                                            "release production runs tests/run.sh with no selectors", relative, number))
            for match in re.finditer(r'tests/run\.sh(.*)$', line):
                if not RUN_SH_REMAINDER.match(match.group(1).strip()):
                    problems.append(problem("release.arguments",
                                            f"  release: {relative}:{number} runs tests/run.sh with arguments: {line.strip()[:80]!r}",
                                            relative, number))
    return problems


def check_run_scripts_are_catalog_commands(tree: repository_tree.Tree) -> list[Problem]:
    """Every run.sh under a suite directory is a case command the dispatcher launches.

    A suite script that no catalog case names is a second way to run the
    suite's cases, outside the dispatcher's selection and accounting."""
    commands = catalog_commands(tree)
    problems: list[Problem] = []
    for script in tree.expand((pattern(f"{SUITES_DIR}/**/run.sh"),)):
        if script not in commands:
            problems.append(problem("catalog.not_a_command",
                                    f"  catalog: {script} is not a case command; cases run only through tests/run.sh", script))
    return problems


def default_suites_from_catalog(tree: repository_tree.Tree) -> set[str]:
    return {name for name, group in catalog_suites(tree).items()
            if any((case if isinstance(case, dict) else {}).get('default', group.get('default', True))
                   for case in group.get('cases', []))}


def required_section(tree: repository_tree.Tree, relative: str, heading: str, level: int | None = 2):
    """The document and its one section under this heading text; a missing section is a precondition failure."""
    document = markdown(tree, relative)
    found = document.section(heading, level)
    if found is None:
        raise InputFailure("section.missing", f"{relative} is missing the {'#' * (level or 2)} {heading!r} section", relative)
    return document, found


def section_rows(document, section) -> list[tuple]:
    """Body rows of the tables in a section."""
    return [row for table in document.tables if section.holds(table.lines) for row in table.rows]


def code_cell(cell, pattern: str) -> str | None:
    """The name in a cell that holds only a code span matching the pattern."""
    if cell.code == [cell.text] and re.fullmatch(pattern, cell.text):
        return cell.text
    return None


def parse_index_rows(tree: repository_tree.Tree) -> dict[str, str]:
    """Return {suite_name: tier} parsed from the suite-coverage table
    in tests/README.md.

    Only tables in the "Suite coverage" section count, so prose tables
    elsewhere in the README can't leak in.
    """
    document, section = required_section(tree, TESTS_README, "Suite coverage")
    rows: dict[str, str] = {}
    for cells in section_rows(document, section):
        name = code_cell(cells[0], r"[a-z][a-z0-9_]*")
        if name and len(cells) > 1 and re.match(r"[A-Za-z]", cells[1].text.strip()):
            rows[name] = cells[1].text.strip()
    return rows


def _parse_matrix_section(tree: repository_tree.Tree, heading: str) -> set[str]:
    document, section = required_section(tree, TESTS_COVERAGE, heading)
    return {name for cells in section_rows(document, section)
            if (name := code_cell(cells[0], r"[a-z][a-z0-9_]*"))}


def parse_matrix_outcomes(tree: repository_tree.Tree) -> set[str]:
    return _parse_matrix_section(tree, "Normalized outcome coverage matrix")


def parse_attempt_outcome_matrix(tree: repository_tree.Tree) -> set[str]:
    return _parse_matrix_section(tree, "Attempt outcome coverage matrix")


def _swift_enum_constants(text: str, name: str, enum_name: str) -> set[str]:
    """The string constants of one Swift enum; a parser the tree reuses by content."""
    enum_re = re.compile(
        r'(?:public\s+)?enum ' + re.escape(enum_name) + r'\s*\{(.*?)\n\}',
        re.DOTALL,
    )
    match = enum_re.search(text)
    if match is None:
        raise InputFailure("enum.missing", f"could not locate {enum_name} enum in {name}", name)
    body = match.group(1)
    constant_re = re.compile(r'(?:public\s+)?static let \w+\s*=\s*"([a-z_][a-z0-9_]*)"')
    return {m.group(1) for m in constant_re.finditer(body)}


def parse_normalized_outcomes(tree: repository_tree.Tree) -> set[str]:
    return tree.parsed(PWRUNNER_API, _swift_enum_constants, "NormalizedOutcome")


def parse_attempt_outcomes(tree: repository_tree.Tree) -> set[str]:
    return tree.parsed(PWRUNNER_API, _swift_enum_constants, "AttemptOutcome")


# ---------------------------------------------------------------------------
# Test-registry checks
# ---------------------------------------------------------------------------

def check_readmes_present(tree: repository_tree.Tree) -> list[Problem]:
    return [problem("readme.missing", f"  README: tests/suites/{name}/ has no README.md", f"{SUITES_DIR}/{name}")
            for name in suites_missing_readme(tree)]


def check_index_vs_disk(tree: repository_tree.Tree) -> list[Problem]:
    problems: list[Problem] = []
    on_disk = suite_directories(tree)
    in_index = set(parse_index_rows(tree).keys())
    in_catalog = set(catalog_suites(tree))
    if in_catalog != on_disk:
        problems.append(problem("catalog.suite_mismatch",
                                f'  catalog: suite directories and catalog disagree: {sorted(in_catalog ^ on_disk)}', CATALOG))

    for name in sorted(on_disk - in_index):
        problems.append(problem("index.missing_row",
                                f"  README: tests/suites/{name}/ exists but has no row in tests/README.md's suite-coverage table",
                                TESTS_README))
    for name in sorted(in_index - on_disk):
        problems.append(problem("index.unknown_row",
                                f"  README: tests/README.md has a suite-coverage row for {name!r} but no such tests/suites/{name}/ exists",
                                TESTS_README))
    return problems


def check_baseline_in_catalog_defaults(tree: repository_tree.Tree) -> list[Problem]:
    problems: list[Problem] = []
    rows = parse_index_rows(tree)
    defaults = default_suites_from_catalog(tree)
    for name, tier in sorted(rows.items()):
        if tier.lower() != "baseline":
            continue
        if name not in defaults:
            problems.append(problem("catalog.baseline_nondefault",
                                    f"  catalog: Baseline-tier suite {name!r} is missing from tests/catalog.json's default membership",
                                    CATALOG))
    return problems


def check_runner_outcome_suites_have_matrix_rows(tree: repository_tree.Tree) -> list[Problem]:
    problems: list[Problem] = []
    on_disk = suite_directories(tree)
    matrix = parse_matrix_outcomes(tree)
    for name in sorted(on_disk):
        if not name.startswith("runner_outcome_"):
            continue
        outcome = name[len("runner_outcome_"):]
        if outcome not in matrix:
            problems.append(problem("matrix.suite_without_row",
                                    f"  matrix: suite {name!r} has no row for outcome {outcome!r} "
                                    f"in the Normalized outcome coverage matrix", TESTS_COVERAGE))
    return problems


def check_normalized_outcomes_have_matrix_rows(tree: repository_tree.Tree) -> list[Problem]:
    problems: list[Problem] = []
    outcomes = parse_normalized_outcomes(tree)
    matrix = parse_matrix_outcomes(tree)
    for outcome in sorted(outcomes - matrix):
        problems.append(problem("matrix.missing_row",
                                f"  matrix: NormalizedOutcome.{outcome} has no row in tests/COVERAGE.md "
                                f"coverage matrix", TESTS_COVERAGE))
    for outcome in sorted(matrix - outcomes):
        problems.append(problem("matrix.unknown_row",
                                f"  matrix: coverage matrix lists {outcome!r} but no NormalizedOutcome "
                                f"constant by that name exists", TESTS_COVERAGE))
    return problems


def check_attempt_outcomes_have_matrix_rows(tree: repository_tree.Tree) -> list[Problem]:
    """Parallel to check_normalized_outcomes_have_matrix_rows but for
    the AttemptOutcome enum. Same drift guardrail so a new attempt
    outcome added to the enum can't ship without a row explaining
    where it gets emitted and how it's covered."""
    problems: list[Problem] = []
    outcomes = parse_attempt_outcomes(tree)
    matrix = parse_attempt_outcome_matrix(tree)
    for outcome in sorted(outcomes - matrix):
        problems.append(problem("attempt_matrix.missing_row",
                                f"  matrix: AttemptOutcome.{outcome} has no row in tests/COVERAGE.md "
                                f"attempt-outcome coverage matrix", TESTS_COVERAGE))
    for outcome in sorted(matrix - outcomes):
        problems.append(problem("attempt_matrix.unknown_row",
                                f"  matrix: attempt-outcome matrix lists {outcome!r} but no "
                                f"AttemptOutcome constant by that name exists", TESTS_COVERAGE))
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


def _c_attempt_kinds(text: str, name: str) -> dict[int, str]:
    block_re = re.compile(r'typedef enum\s*\{(.*?)\}\s*pw_attempt_kind_t;', re.DOTALL)
    match = block_re.search(text)
    if match is None:
        raise InputFailure("enum.missing", "could not locate pw_attempt_kind_t in pw_probe_runner_abi.h", name)
    kinds: dict[int, str] = {}
    for m in re.finditer(r'\bPW_ATTEMPT_([A-Z0-9_]+)\s*=\s*(\d+)', match.group(1)):
        kinds[int(m.group(2))] = m.group(1)
    if not kinds:
        raise InputFailure("enum.empty", "pw_attempt_kind_t contains no parseable PW_ATTEMPT_* entries", name)
    return kinds


def parse_c_attempt_kinds(tree: repository_tree.Tree) -> dict[int, str]:
    return tree.parsed(PW_PROBE_RUNNER_ABI, _c_attempt_kinds)


def _swift_attempt_kinds(text: str, name: str) -> dict[int, str]:
    enum_re = re.compile(r'(?:public\s+)?enum PWAttemptKind:\s*UInt32\s*\{(.*?)\n\}', re.DOTALL)
    match = enum_re.search(text)
    if match is None:
        raise InputFailure("enum.missing", "could not locate PWAttemptKind in runner/Sources/PWRunnerCore/CWorker.swift", name)
    kinds: dict[int, str] = {}
    for m in re.finditer(r'\bcase\s+([A-Za-z][A-Za-z0-9]*)\s*=\s*(\d+)', match.group(1)):
        kinds[int(m.group(2))] = _camel_to_screaming_snake(m.group(1))
    if not kinds:
        raise InputFailure("enum.empty", "PWAttemptKind contains no parseable case entries", name)
    return kinds


def parse_swift_attempt_kinds(tree: repository_tree.Tree) -> dict[int, str]:
    return tree.parsed(CWORKER_SWIFT, _swift_attempt_kinds)


def check_attempt_kind_enum_agreement(tree: repository_tree.Tree) -> list[Problem]:
    problems: list[Problem] = []
    c_kinds = parse_c_attempt_kinds(tree)
    swift_kinds = parse_swift_attempt_kinds(tree)

    c_values = set(c_kinds)
    swift_values = set(swift_kinds)
    for value in sorted(c_values - swift_values):
        problems.append(problem("attempt_kind.c_only",
                                f"  attempt-kind: C PW_ATTEMPT_{c_kinds[value]}={value} has no "
                                f"matching PWAttemptKind raw value", PW_PROBE_RUNNER_ABI))
    for value in sorted(swift_values - c_values):
        problems.append(problem("attempt_kind.swift_only",
                                f"  attempt-kind: Swift PWAttemptKind.{swift_kinds[value]}={value} "
                                f"has no matching pw_attempt_kind_t value", CWORKER_SWIFT))

    if c_values:
        expected = set(range(0, max(c_values) + 1))
        for value in sorted(expected - c_values):
            problems.append(problem("attempt_kind.gap", f"  attempt-kind: pw_attempt_kind_t has a numeric gap at {value}",
                                    PW_PROBE_RUNNER_ABI))

    for value in sorted(c_values & swift_values):
        if c_kinds[value] != swift_kinds[value]:
            problems.append(problem("attempt_kind.name_mismatch",
                                    f"  attempt-kind: value {value} is PW_ATTEMPT_{c_kinds[value]} in C "
                                    f"but PWAttemptKind.{swift_kinds[value]} in Swift", CWORKER_SWIFT))
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


def check_prediction_unavailable_planner(tree: repository_tree.Tree) -> list[Problem]:
    prefix = '  prediction_unavailable planner: '
    sources = {}
    for path in CWORKER_ORCHESTRATION_SOURCES:
        try:
            sources[path] = swift_code(tree.read_text(path))
        except ValueError as exc:
            return [problem("planner.unterminated_string", prefix + str(exc), path)]
    problems = []
    # No local pair collection, literal operation/filter entry, or shadow of
    # the shared symbol. Dynamic construction of the current query pair stays
    # valid. Cover the extracted orchestration owners so moving a table outside
    # the planner function or into another helper does not hide it.
    for path, code in sources.items():
        if (re.search(r'Set\s*<\s*PredictionUnavailablePair\s*>|\[\s*PredictionUnavailablePair\s*\]', code)
                or re.search(r'(?:\.\s*init|\bPredictionUnavailablePair)\s*\(\s*operation\s*:\s*""\s*,\s*filterKind\s*:', code)
                or re.search(r'\b(?:let|var)\s+predictionUnavailableOpFilters\b', code)):
            problems.append(problem("planner.local_table",
                                    prefix + path.rsplit('/', 1)[-1] + ' must not define a local exclusion table or shadow the shared set',
                                    path))
    code = sources[CWORKER_REQUEST_PLANNING]
    match = re.search(r'\bfunc\s+planValidatorQueries\b[^{}]*\{', code)
    if match is None:
        return problems + [problem("planner.missing_function", prefix + 'could not locate planValidatorQueries', CWORKER_REQUEST_PLANNING)]
    start = end = match.end()
    depth = 1
    while end < len(code) and depth:
        depth += (code[end] == '{') - (code[end] == '}')
        end += 1
    if depth or not re.search(r'\bif\s+predictionUnavailableOpFilters\s*\.\s*contains\s*\(', code[start:end - 1]):
        problems.append(problem("planner.missing_contains",
                                prefix + 'planValidatorQueries must use if predictionUnavailableOpFilters.contains(...)',
                                CWORKER_REQUEST_PLANNING))
    return problems


def parse_swift_prediction_unavailable_pairs(tree: repository_tree.Tree) -> set[tuple[str, str]]:
    text = tree.read_text(PROBE_RUNNER)
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
        raise InputFailure("pairs.missing",
                           "could not locate predictionUnavailableOpFilters in runner/Sources/PWRunnerCore/ProbeRunner.swift",
                           PROBE_RUNNER)
    body = match.group(1)
    # Map the Swift constant references to their wire strings via the
    # PWRunnerWire constants in PWRunnerAPI.swift.
    wire = parse_pwrunner_wire_filter_constants(tree)
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
                raise InputFailure("pairs.unknown_constant",
                                   f"predictionUnavailableOpFilters references "
                                   f"PWRunnerWire.{const_name} but no such constant is "
                                   f"defined in runner/Sources/PWRunnerCore/PWRunnerAPI.swift", PROBE_RUNNER)
        else:
            kind = literal
        pairs.add((operation, kind))
    return pairs


def _wire_filter_constants(text: str, name: str) -> dict[str, str]:
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


def parse_pwrunner_wire_filter_constants(tree: repository_tree.Tree) -> dict[str, str]:
    return tree.parsed(PWRUNNER_API, _wire_filter_constants)


def parse_docs_prediction_unavailable_pairs(tree: repository_tree.Tree) -> set[tuple[str, str]]:
    """Extract (op, filter) pairs from the list after docs/PolicyWitness.md's
    "Currently in this category:" paragraph, formatted as
    `(operation, filter_kind)` at the start of each bullet."""
    document = markdown(tree, POLICYWITNESS_MD)
    section = document.section("Filter kinds where prediction is unavailable")
    marker = None if section is None else next(
        (inline for inline in document.inlines if inline.kind == "paragraph" and section.holds(inline.lines)
         and inline.text.startswith("Currently in this category:")), None)
    if marker is None:
        raise InputFailure("section.missing",
                           "could not locate 'Filter kinds where prediction is unavailable' "
                           "section in docs/PolicyWitness.md (or its 'Currently in this category:' paragraph)",
                           POLICYWITNESS_MD)
    pairs = set()
    for item in document.items:
        if item.first and section.holds(item.lines) and item.lines[0] >= marker.lines[1]:
            pair = re.fullmatch(r"\(([a-z][a-z0-9-]*)\s*,\s*([a-z][a-z0-9_]*)\)", item.first.leading_code or "")
            if pair:
                pairs.add((pair.group(1), pair.group(2)))
    return pairs


def check_prediction_unavailable_agreement(tree: repository_tree.Tree) -> list[Problem]:
    swift_pairs = parse_swift_prediction_unavailable_pairs(tree)
    docs_pairs = parse_docs_prediction_unavailable_pairs(tree)
    problems: list[Problem] = []
    # Treat the Swift ProbeRunner set as the canonical source and
    # compare every other source against it. A single canonical
    # reduces N^2 pair comparisons to N — and makes the failure
    # messages name the disagreeing source clearly.
    canonical = swift_pairs
    others = [
        ("docs (docs/PolicyWitness.md)", docs_pairs, POLICYWITNESS_MD),
    ]
    for label, other, path in others:
        for pair in sorted(canonical - other):
            problems.append(problem("prediction.swift_only",
                                    f"  prediction_unavailable: {pair} in swift (ProbeRunner.swift) but missing from {label}", path))
        for pair in sorted(other - canonical):
            problems.append(problem("prediction.docs_only",
                                    f"  prediction_unavailable: {pair} in {label} but missing from swift (ProbeRunner.swift)", path))
    return problems


# ---------------------------------------------------------------------------
# Host invariance: the XPC host source never names the native sandbox API.
#
# The host must not link, load or call libsandbox. Every native sandbox
# operation belongs to the worker (pw-probe-runner), validator
# (sb_api_validator), or extension issuer (pw-extension-issuer). The host
# joins their observations without executing their sandbox API work. The
# companion binary check is
# tests/lib/artifact.py (`nm -u` on the shipped PWRunner).
# ---------------------------------------------------------------------------

# Native uses in the host, including the C shim. This is a source convention,
# not complete Swift/C analysis: computed symbol/library names are outside it.
HOST_SANDBOX_SYMBOLS = frozenset({
    'sandbox_check', 'sandbox_apply', 'sandbox_compile_string',
    'sandbox_create_params', 'sandbox_set_param', 'sandbox_free_params',
    'sandbox_free_profile', 'sandbox_free_error',
    'sandbox_extension_issue_file', 'sandbox_extension_consume', 'sandbox_extension_release',
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


def host_invariance_problems(label: str, text: str) -> list[Problem]:
    """Find native calls/bindings and literal sandbox lookups, allowing prose."""
    try:
        tokens = host_tokens(text)
    except ValueError as exc:
        return [problem("host.unparsed", f'  host invariance: {label}: {exc}', label)]
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
            problems.append(problem("host.native_use", f'  host invariance: {label}:{line} uses {prohibited}; '
                                    'the XPC host never links, loads or calls libsandbox', label, line))
    return problems


def check_host_invariance(tree: repository_tree.Tree) -> list[Problem]:
    problems: list[Problem] = []
    for relative in tree.inventory(RUNNER_NATIVE):
        problems.extend(host_invariance_problems(relative, tree.read_text(relative)))
    return problems


# ---------------------------------------------------------------------------
# `_test_overrides` key table agreement.
#
# runner/README.md's test-seam table is the only documented list of override
# keys; runner/AGENTS.md points at it instead of carrying a copy. Lock the
# table to the Codable struct so a key added to one cannot ship without the
# other.
# ---------------------------------------------------------------------------

def _test_override_fields(text: str, name: str) -> set[str]:
    struct_re = re.compile(
        r'(?:public\s+)?struct PWRunnerTestOverrides\s*:\s*Codable\s*\{(.*?)\n\}',
        re.DOTALL,
    )
    match = struct_re.search(text)
    if match is None:
        raise InputFailure("struct.missing", "could not locate PWRunnerTestOverrides in runner/Sources/PWRunnerCore/PWRunnerRequest.swift",
                           name)
    field_re = re.compile(r'^\s*(?:public\s+)?var ([a-z_][a-z0-9_]*)\s*:', re.MULTILINE)
    fields = {m.group(1) for m in field_re.finditer(match.group(1))}
    if not fields:
        raise InputFailure("struct.empty", "PWRunnerTestOverrides contains no parseable stored properties", name)
    return fields


def parse_test_override_fields(tree: repository_tree.Tree) -> set[str]:
    return tree.parsed(PWRUNNER_REQUEST, _test_override_fields)


def parse_readme_test_override_rows(tree: repository_tree.Tree) -> set[str]:
    """Return the keys tabulated in runner/README.md's
    "Test seam: `_test_overrides`" section, so other tables in the README
    can't leak in."""
    document, section = required_section(tree, RUNNER_README, "Test seam: _test_overrides")
    return {name for cells in section_rows(document, section)
            if (name := code_cell(cells[0], r"[a-z_][a-z0-9_]*"))}


def check_test_overrides_table_agreement(tree: repository_tree.Tree) -> list[Problem]:
    problems: list[Problem] = []
    fields = parse_test_override_fields(tree)
    rows = parse_readme_test_override_rows(tree)
    for name in sorted(fields - rows):
        problems.append(problem("test_overrides.missing_row",
                                f"  test_overrides: PWRunnerTestOverrides.{name} has no row in "
                                f"runner/README.md's test-seam table", RUNNER_README))
    for name in sorted(rows - fields):
        problems.append(problem("test_overrides.unknown_row",
                                f"  test_overrides: runner/README.md's test-seam table lists {name!r} "
                                f"but PWRunnerTestOverrides has no such property", RUNNER_README))
    return problems


# ---------------------------------------------------------------------------
# Workflow-local harness guidance and diagnostic routes.
# The rule checks usable entry sections and links, not advice or wording.
# ---------------------------------------------------------------------------

HARNESS_GUIDANCE_HEADING = "Sandboxed automation harnesses"
HARNESS_GUIDANCE_FILES = ("AGENTS.md", "runner/AGENTS.md", "tests/AGENTS.md", "docs/BUILD.md")
HARNESS_GUIDANCE_ROUTES = tuple((path, "sandboxed-automation-harnesses") for path in HARNESS_GUIDANCE_FILES[1:])


def check_harness_guidance_routes(tree: repository_tree.Tree) -> list[Problem]:
    problems: list[Problem] = []
    sections = {}
    for relative in HARNESS_GUIDANCE_FILES:
        document = markdown(tree, relative)
        found = document.sections(HARNESS_GUIDANCE_HEADING)
        label = f"  harness guidance: {relative}"
        if len(found) != 1:
            problems.append(problem("guidance.heading_count",
                                    f"{label}: expected one '{HARNESS_GUIDANCE_HEADING}' heading; found {len(found)}", relative))
            continue
        section = found[0]
        # Headings alone cannot supply guidance; comments, code and HTML are not prose.
        body = [inline for inline in document.inlines if inline.kind != "heading" and section.holds(inline.lines)]
        if not any(re.search(r"\w", inline.text) for inline in body):
            problems.append(problem("guidance.empty", f"{label}: empty '{HARNESS_GUIDANCE_HEADING}' section", relative,
                                    section.lines[0] + 1))
            continue
        sections[relative] = (document, section)

    root = HARNESS_GUIDANCE_FILES[0]
    if root in sections:
        document, section = sections[root]
        routes = set()
        for link in document.links:
            if link.image or not section.holds(link.inline.lines):
                continue
            filename, separator, fragment = link.target.partition("#")
            if separator and filename and not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", filename):
                routes.add((posixpath.normpath(posixpath.join(posixpath.dirname(root), filename)), fragment))
        for relative, fragment in HARNESS_GUIDANCE_ROUTES:
            if (relative, fragment) not in routes:
                problems.append(problem("guidance.missing_route",
                                        f"  harness guidance: AGENTS.md: missing diagnostic route "
                                        f"{relative}#{fragment} in '{HARNESS_GUIDANCE_HEADING}'", root))
    return problems


# ---------------------------------------------------------------------------
# CLI surface agreement.
#
# controller/README.md ("CLI surface (contract)") promises the exact usage
# lines and controller/src/cli.rs prints them. A flag added or removed on one
# side only ships a README that lies about the binary; compare the lines.
# ---------------------------------------------------------------------------
CLI_RS = "controller/src/cli.rs"
CONTROLLER_README = "controller/README.md"


def parse_cli_usage_lines(tree: repository_tree.Tree) -> list[str]:
    text = tree.read_text(CLI_RS)
    match = re.search(r"usage:\n(.*?)\n\nnotes:", text, re.DOTALL)
    if match is None:
        return []
    return [line[2:] for line in match.group(1).splitlines() if line.startswith("  policy-witness ")]


def parse_readme_surface_lines(tree: repository_tree.Tree) -> list[str]:
    document = markdown(tree, CONTROLLER_README)
    section = document.section("CLI surface (contract)", 2)
    fence = next((block for block in document.fences("text") if section and section.holds(block.lines)), None)
    if fence is None:
        return []
    return [line for line in fence.content.splitlines() if line.startswith("policy-witness ")]


def check_cli_surface_agreement(tree: repository_tree.Tree) -> list[Problem]:
    problems: list[Problem] = []
    cli = parse_cli_usage_lines(tree)
    readme = parse_readme_surface_lines(tree)
    if not cli:
        problems.append(problem("cli.usage_missing", "controller/src/cli.rs: could not locate the usage block (usage: ... notes:)", CLI_RS))
    if not readme:
        problems.append(problem("cli.readme_missing", "controller/README.md: could not locate the CLI surface (contract) text block",
                                CONTROLLER_README))
    if cli and readme and cli != readme:
        lines = ["CLI surface drift between controller/src/cli.rs usage and controller/README.md:"]
        lines += [f"  cli.rs   : {line}" for line in cli] + [f"  README.md: {line}" for line in readme]
        problems.append(problem("cli.mismatch", "\n".join(lines), CONTROLLER_README))
    return problems


ARCHITECTURE_DOC = "docs/ARCHITECTURE.md"
SHAPE_GOLDENS = {"reply": "tests/fixtures/contract/response_shape.json",
                 "envelope": "tests/fixtures/contract/envelope_shape.json"}


BUILD_DOC = "docs/BUILD.md"
WORKER_DOC = "docs/WORKER.md"


def handwritten(tree: repository_tree.Tree, relative: str):
    """The document and a test for lines outside its generated regions, which hold no handwritten text."""
    document = markdown(tree, relative)
    regions = [(document.line_of(m.start()), document.line_of(m.end()) + 1) for m in
               re.finditer(r"<!-- BEGIN GENERATED ([^>]+?) -->.*?<!-- END GENERATED \1 -->", document.text, re.S)]
    return document, lambda lines: not any(a <= lines[0] < b for a, b in regions)


def check_known_gap_index(tree: repository_tree.Tree) -> list[Problem]:
    """Every paragraph opening with "Known gap" is indexed, in order, by the last section, which lists nothing else.

    The convention holds in the architecture, build and worker tours."""
    problems = []
    for relative in (ARCHITECTURE_DOC, BUILD_DOC, WORKER_DOC):
        problems.extend(known_gap_index_problems(tree, relative))
    return problems


def known_gap_index_problems(tree: repository_tree.Tree, name: str) -> list[Problem]:
    parsed, authored = handwritten(tree, name)
    headings = [h for h in parsed.headings if h.level == 2 and authored((h.line, h.line + 1))]
    if not headings or headings[-1].text != "Known gaps":
        return [problem("known_gaps.final_section", f"  known gaps: {name} must end with a '## Known gaps' section", name)]
    index_start = headings[-1].line
    gaps = []
    for paragraph in parsed.inlines:
        if (paragraph.kind != "paragraph" or paragraph.depth or not authored(paragraph.lines)
                or not paragraph.text.startswith("Known gap")):
            continue
        owner = [h for h in headings if h.line < paragraph.lines[0]]
        if paragraph.lines[0] >= index_start or not owner:
            return [problem("known_gaps.misplaced",
                            f"  known gaps: {name}: a Known gap paragraph must sit under the section whose promise it limits: {paragraph.text[:60]!r}",
                            name, paragraph.lines[0] + 1)]
        gaps.append(markdown_reader.slug(owner[-1].text))
    linked = []
    for item in parsed.items:
        if item.depth or item.lines[0] < index_start or not authored(item.lines):
            continue
        link = item.first.leading_link if item.first and not item.ordered else None
        if link is None or not link.target.startswith("#"):
            return [problem("known_gaps.index_entry",
                            f"  known gaps: {name}: an index bullet must open with a link to its section: {(item.first.text if item.first else '')[:60]!r}",
                            name, item.lines[0] + 1)]
        linked.append(link.target[1:])
    if linked != gaps:
        return [problem("known_gaps.index_order",
                        f"  known gaps: {name}: the index lists {linked} but the Known gap paragraphs sit under {gaps}", name)]
    return []


def check_evidence_channel_paths(tree: repository_tree.Tree) -> list[Problem]:
    """Every landing path in the evidence-channels table resolves in a shape golden."""
    document, authored = handwritten(tree, ARCHITECTURE_DOC)
    section = document.section("Evidence channels and ownership", 2)
    if section is None:
        return [problem("evidence.section_missing", "  evidence channels: section missing from docs/ARCHITECTURE.md", ARCHITECTURE_DOC)]
    rows = [row for table in document.tables if section.holds(table.lines) and authored(table.lines) for row in table.rows]
    if not rows:
        return [problem("evidence.table_missing", "  evidence channels: table missing from docs/ARCHITECTURE.md", ARCHITECTURE_DOC)]
    shapes = {}
    for name, relative in SHAPE_GOLDENS.items():
        golden = json_input(tree, relative)
        if not isinstance(golden, dict) or "shape" not in golden:
            raise InputFailure("input.shape", f"{relative}: no shape member", relative)
        shapes[name] = set(golden["shape"])
    problems: list[Problem] = []
    for cells in rows:
        # The parser pads a short row to the header's width, so a missing landing path is an empty cell.
        if len(cells) < 4 or not cells[3].code:
            problems.append(problem("evidence.no_landing",
                                    f"  evidence channels: row has no landing column: {cells[0].text[:60]!r}", ARCHITECTURE_DOC))
            continue
        for path in cells[3].code:
            golden = "envelope" if path.startswith("data.") else "reply"
            if f"{golden}.{path}" not in shapes[golden]:
                problems.append(problem("evidence.unknown_landing",
                                        f"  evidence channels: `{path}` is not a key of the {golden} shape golden", ARCHITECTURE_DOC))
    return problems


# ---------------------------------------------------------------------------
# The rule table: every production rule, in the order the dispatcher runs
# them. Rows declare what a rule reads (an auditable account for fixture
# construction, not a claim of complete reachability) and the helper modules
# a fixture must carry; they declare no prerequisites on other rows.
# ---------------------------------------------------------------------------

RULES = (
    Rule("meson_source_lists", check_meson_source_lists,
         inputs=(required(MESON_BUILD), required(MESON_OPTIONS), directory(CORE_DIR, (".swift",)),
                 *(directory(shim, (".c",)) for shim in SHIM_DIRS),
                 *(required(path) for path in (native_sources.API, native_sources.SERVICE_MAIN, native_sources.CLIENT_MAIN,
                                               native_sources.WORKER, native_sources.VALIDATOR, native_sources.ISSUER))),
         helpers=("tests/lib/native_sources.py",)),
    Rule("readmes_present", check_readmes_present,
         inputs=(members(SUITES_DIR), pattern(f"{SUITES_DIR}/*/README.md"))),
    Rule("index_vs_disk", check_index_vs_disk,
         inputs=(members(SUITES_DIR), required(CATALOG), required(TESTS_README)), helpers=MARKDOWN_HELPERS),
    Rule("run_scripts_are_catalog_commands", check_run_scripts_are_catalog_commands,
         inputs=(pattern(f"{SUITES_DIR}/**/run.sh"), required(CATALOG))),
    Rule("no_direct_case_commands_in_docs", check_no_direct_case_commands_in_docs,
         inputs=(inventory(repository_tree.COMMAND_DOCUMENTS),), helpers=MARKDOWN_HELPERS),
    Rule("release_production_runs_the_default_battery", check_release_production_runs_the_default_battery,
         inputs=RELEASE_INPUTS),
    Rule("baseline_in_catalog_defaults", check_baseline_in_catalog_defaults,
         inputs=(required(CATALOG), required(TESTS_README)), helpers=MARKDOWN_HELPERS),
    Rule("runner_outcome_suites_have_matrix_rows", check_runner_outcome_suites_have_matrix_rows,
         inputs=(members(SUITES_DIR), required(TESTS_COVERAGE)), helpers=MARKDOWN_HELPERS),
    Rule("normalized_outcomes_have_matrix_rows", check_normalized_outcomes_have_matrix_rows,
         inputs=(required(PWRUNNER_API), required(TESTS_COVERAGE)), helpers=MARKDOWN_HELPERS),
    Rule("attempt_outcomes_have_matrix_rows", check_attempt_outcomes_have_matrix_rows,
         inputs=(required(PWRUNNER_API), required(TESTS_COVERAGE)), helpers=MARKDOWN_HELPERS),
    Rule("attempt_kind_enum_agreement", check_attempt_kind_enum_agreement,
         inputs=(required(CWORKER_SWIFT), required(PW_PROBE_RUNNER_ABI))),
    Rule("prediction_unavailable_agreement", check_prediction_unavailable_agreement,
         inputs=(required(PROBE_RUNNER), required(PWRUNNER_API), required(POLICYWITNESS_MD)), helpers=MARKDOWN_HELPERS),
    Rule("prediction_unavailable_planner", check_prediction_unavailable_planner,
         inputs=tuple(required(path) for path in CWORKER_ORCHESTRATION_SOURCES)),
    Rule("test_overrides_table_agreement", check_test_overrides_table_agreement,
         inputs=(required(PWRUNNER_REQUEST), required(RUNNER_README)), helpers=MARKDOWN_HELPERS),
    Rule("harness_guidance_routes", check_harness_guidance_routes,
         inputs=tuple(required(path) for path in HARNESS_GUIDANCE_FILES), helpers=MARKDOWN_HELPERS),
    Rule("cli_surface_agreement", check_cli_surface_agreement,
         inputs=(required(CLI_RS), required(CONTROLLER_README)), helpers=MARKDOWN_HELPERS),
    Rule("host_invariance", check_host_invariance,
         inputs=(directory(RUNNER_SOURCES, (".swift", ".c", ".h", ".m", ".mm")),)),
    Rule("known_gap_index", check_known_gap_index,
         inputs=(required(ARCHITECTURE_DOC), required(BUILD_DOC), required(WORKER_DOC)), helpers=MARKDOWN_HELPERS),
    Rule("evidence_channel_paths", check_evidence_channel_paths,
         inputs=(required(ARCHITECTURE_DOC), *(required(path) for path in SHAPE_GOLDENS.values())), helpers=MARKDOWN_HELPERS),
)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def facts(tree: repository_tree.Tree) -> str:
    """The summary line; every parse it needs was made by a rule and is reused from the tree."""
    return (f"all drift checks pass: "
            f"{len(disk_swift_files(tree))} swift, "
            f"{len(disk_c_files(tree))} c, "
            f"{len(suite_directories(tree))} suites, "
            f"{len(parse_normalized_outcomes(tree))} normalized outcomes, "
            f"{len(parse_attempt_outcomes(tree))} attempt outcomes, "
            f"{len(parse_swift_prediction_unavailable_pairs(tree))} prediction_unavailable pairs, "
            f"{len(parse_test_override_fields(tree))} test override keys.")


def main(argv=None) -> int:
    # SwiftPM auto-discovers the same files off disk (convention layout, no
    # sources: arrays to parse), so the load-bearing comparison is the tree
    # against the explicit lists in meson.build.
    parser = argparse.ArgumentParser(description="Run the source and test-registry drift rules over one checkout.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="the checkout to read (default: this repository)")
    parser.add_argument("--rule", action="append", dest="rules", metavar="ID", help="run only this rule (repeatable)")
    parser.add_argument("--json", type=Path, metavar="PATH", help="also write every result record to this file")
    args = parser.parse_args(argv)
    tree = repository_tree.Tree(args.root)
    try:
        results = drift_rules.run_rules(tree, RULES, args.rules, refused=(markdown_reader.Refused,))
    except ValueError as error:
        fail(str(error))
        return 2
    if args.json:
        args.json.write_text(json.dumps(drift_rules.to_json(results), indent=2) + "\n")
    status = drift_rules.status(results)
    for line in drift_rules.summary_lines(results):
        print(line)
    if status:
        fail("source/test-registry drift detected:" if status == 1 else "source/test-registry rules blocked by their inputs:")
        for result in results:
            for record in result.problems:
                fail(f"  {result.rule_id}: blocked by input: {record.message}" if record.severity == "precondition"
                     else record.message)
        fail("")
        fail("Each rule is mechanical: fix the missing file, row, or list entry")
        fail("named above. The guardrail exists so adding a new suite or outcome")
        fail("without registering it everywhere fails loudly here rather than")
        fail("silently in downstream consumers.")
        return status
    print(facts(tree) if args.rules is None else f"{len(results)} selected drift rules pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
