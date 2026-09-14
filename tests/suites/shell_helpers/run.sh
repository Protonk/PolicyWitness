#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

# Keep this entry point independent of the case helpers it is checking.
test_begin shell_helpers controls
test_step controls "exercise case failures, logs, prerequisites, and stage ordering"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/shell_helpers/check.py" \
    "${PW_TEST_ARTIFACTS}" >"${PW_TEST_ARTIFACTS}/assertions.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assertions.log" >&2
  test_fail "shell helper controls failed; see artifacts/assertions.log"
fi
test_pass "shell helpers retain diagnostics and case identity; failures prevent later stages"

test_begin shell_helpers script_groups
test_step controls "observe child execution, wrapper phases, skips, and failure continuation"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/shell_helpers/check_scripts.py" \
    "${PW_TEST_ARTIFACTS}" >"${PW_TEST_ARTIFACTS}/assertions.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assertions.log" >&2
  test_fail "script-group controls failed; see artifacts/assertions.log"
fi
test_pass "wrappers preserve child order, streams, phase boundaries, and failing status"
