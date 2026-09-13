#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

test_begin runner_live_worker_identity independent_worker_and_host_queries
[[ -x "${PW_BIN}" ]] || test_fail "built policy-witness missing: ${PW_BIN}"
test_step build "compile test-owned observer/helper with no PW source dependencies"
OBSERVER="${PW_TEST_ARTIFACTS}/observer"
if ! /usr/bin/xcrun --sdk macosx clang -Wall -Wextra -Werror \
    "${ROOT_DIR}/tests/suites/runner_live_worker_identity/observer.c" -o "${OBSERVER}" \
    -lsandbox -lproc >"${PW_TEST_ARTIFACTS}/build.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/build.log" >&2
  test_fail "observer compilation failed"
fi
test_step run "observe helper peer PID, worker/host ancestry, and live sandbox_check verdicts"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/runner_live_worker_identity/check.py" \
    "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${OBSERVER}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assert.log" >&2
  test_fail "live worker identity check failed; see artifacts/assert.log and observer.stderr"
fi
test_pass "OS-observed worker identity and independent predictions match PW; host remains unrestricted"
