#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

test_begin exec_fixture controls
test_step build "compile shared exec fixture"
HELPER="${PW_TEST_ARTIFACTS}/helper"
if ! bash "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${HELPER}" \
    >"${PW_TEST_ARTIFACTS}/build.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/build.log" >&2
  test_fail "exec fixture build failed"
fi
test_step check "verify output, lifecycle, process-state inspection, and forwarding with direct OS controls"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/exec_fixture/check.py" \
    "${HELPER}" "${PW_TEST_ARTIFACTS}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assert.log" >&2
  test_fail "exec fixture controls failed; see artifacts/assert.log"
fi
test_pass "fixture controls distinguish output/status, live descendants, inherited resources, and invalid reports"
