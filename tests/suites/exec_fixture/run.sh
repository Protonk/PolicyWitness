#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin exec_fixture controls
test_step build "compile shared exec fixture"
HELPER="${PW_TEST_ARTIFACTS}/helper"
test_build_fixture "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${HELPER}"
test_step check "verify output, independent tree release, lifecycle, process identity, and inherited state"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" \
  "exec fixture controls failed" \
  "${ROOT_DIR}/tests/suites/exec_fixture/check.py" \
  "${HELPER}" "${PW_TEST_ARTIFACTS}"
test_pass "fixture controls distinguish independent process trees, output/status, inherited resources, and invalid reports"
