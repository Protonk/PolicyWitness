#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

test_selected comparison_controls || exit 0
test_begin blackbox_e2e comparison_controls
test_step comparison "reject structural and command changes while allowing corroborated relocation"
if ! /usr/bin/python3 -B "${ROOT_DIR}/tests/suites/blackbox_e2e/comparison_controls.py" \
    "${PW_TEST_ARTIFACTS}" >"${PW_TEST_ARTIFACTS}/assertions.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assertions.log" >&2
  test_fail "envelope comparison controls failed"
fi
test_pass "envelope comparison preserves structure and command semantics"
