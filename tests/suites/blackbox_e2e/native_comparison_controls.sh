#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

test_selected native_comparison_controls || exit 0
test_begin blackbox_e2e native_comparison_controls
test_step structure "name dynamic-library, platform-version, size and sandbox-import differences between executables"
if ! /usr/bin/python3 -B "${ROOT_DIR}/tests/suites/blackbox_e2e/native_comparison_controls.py" \
    "${PW_TEST_ARTIFACTS}" >"${PW_TEST_ARTIFACTS}/assertions.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assertions.log" >&2
  test_fail "structural comparison controls failed"
fi
test_pass "structural comparison names library, version, size and import differences"
