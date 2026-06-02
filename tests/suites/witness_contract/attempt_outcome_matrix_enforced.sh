#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="witness_contract"
PW_TEST_ID="attempt_outcome_matrix_enforced"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "check" "AttemptOutcome enum exists and source_drift enforces a matrix row per constant"

API_FILE="${ROOT_DIR}/runner/PWRunnerAPI.swift"
COVERAGE_FILE="${ROOT_DIR}/tests/COVERAGE.md"
DRIFT_CHECK="${ROOT_DIR}/tests/suites/source_drift/check.py"

ASSERT_LOG="${PW_TEST_ARTIFACTS}/assertions.log"
set +e
/usr/bin/python3 - "${API_FILE}" "${COVERAGE_FILE}" "${DRIFT_CHECK}" >"${ASSERT_LOG}" 2>&1 <<'PY'
import re
import sys
from pathlib import Path

api = Path(sys.argv[1]).read_text(encoding="utf-8")
index = Path(sys.argv[2]).read_text(encoding="utf-8")
drift = Path(sys.argv[3]).read_text(encoding="utf-8")

# 1. AttemptOutcome enum must exist in PWRunnerAPI.swift.
if "public enum AttemptOutcome" not in api:
    raise SystemExit(
        "AttemptOutcome enum is not defined in runner/PWRunnerAPI.swift."
    )

# 2. tests/COVERAGE.md must contain a matrix section for attempt outcomes.
if "## Attempt outcome coverage matrix" not in index:
    raise SystemExit(
        "tests/COVERAGE.md has no 'Attempt outcome coverage matrix' section."
    )

# 3. source_drift's check must reference attempt outcomes.
if "AttemptOutcome" not in drift:
    raise SystemExit(
        "tests/suites/source_drift/check.py does not enforce the AttemptOutcome matrix."
    )

# 4. Every AttemptOutcome constant has a matrix row.
enum_re = re.compile(r"public enum AttemptOutcome\s*\{(.*?)\n\}", re.DOTALL)
match = enum_re.search(api)
if match is None:
    raise SystemExit("AttemptOutcome enum declaration could not be parsed")
constants = set(re.findall(r'public static let \w+\s*=\s*"([a-z_][a-z0-9_]*)"', match.group(1)))

# Slice off just the matrix section.
matrix_part = index.split("## Attempt outcome coverage matrix", 1)[1]
next_heading = re.search(r"^##\s", matrix_part, re.MULTILINE)
if next_heading:
    matrix_part = matrix_part[: next_heading.start()]
matrix_rows = set(re.findall(r"^\|\s*`([a-z][a-z0-9_]*)`\s*\|", matrix_part, re.MULTILINE))

missing = sorted(constants - matrix_rows)
orphan = sorted(matrix_rows - constants)
if missing or orphan:
    raise SystemExit(
        f"AttemptOutcome matrix inconsistent: missing rows for {missing!r}; "
        f"orphan rows for {orphan!r}."
    )
PY
ASSERT_RC=$?
set -e
if [[ "${ASSERT_RC}" -ne 0 ]]; then
  MSG="$(head -5 "${ASSERT_LOG}" | tr '\n' ' ' | sed 's/"/\\"/g')"
  test_fail "${MSG}" "{\"log\":\"${ASSERT_LOG}\"}"
fi

test_pass "AttemptOutcome enum present, matrix consistent, source_drift enforces" "{}"
