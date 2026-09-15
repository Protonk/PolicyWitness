#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

test_selected checker_controls || exit 0
test_begin "${PW_TEST_SUITE_OVERRIDE:-blackbox_e2e}" checker_controls
test_step checker "verify that prediction failures cannot hide attempt or correlation failures"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/blackbox_e2e/checker_controls.py" \
    "${PW_TEST_ARTIFACTS}" >"${PW_TEST_ARTIFACTS}/assertions.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assertions.log" >&2
  test_fail "blackbox checker controls failed"
fi
test_pass "blackbox checker reports independent evidence failures together"
