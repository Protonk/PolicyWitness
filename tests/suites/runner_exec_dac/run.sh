#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

test_begin runner_exec_dac execute_permission_is_not_sandbox_drift
test_step run "compare direct execution and PW with execute permission absent, then restored"
[[ -x "${PW_BIN}" ]] || test_fail "built policy-witness missing: ${PW_BIN}"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/runner_exec_dac/check.py" \
    "${PW_BIN}" "${PW_TEST_ARTIFACTS}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assert.log" >&2
  test_fail "exec permission attribution failed; see artifacts/assert.log"
fi
test_pass "execute permission controls spawning; ordinary EACCES yields drift=null"
