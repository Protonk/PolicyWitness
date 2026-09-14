#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin runner_live_worker_identity independent_worker_and_host_queries
test_require_pw
test_step build "compile test-owned observer/helper with no PW source dependencies"
OBSERVER="${PW_TEST_ARTIFACTS}/observer"
test_run_logged "${PW_TEST_ARTIFACTS}/build.log" "observer compilation failed" \
    /usr/bin/xcrun --sdk macosx clang -Wall -Wextra -Werror \
    "${ROOT_DIR}/tests/suites/runner_live_worker_identity/observer.c" -o "${OBSERVER}" \
    -lsandbox -lproc
test_step run "observe helper peer PID, worker/host ancestry, and live sandbox_check verdicts"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "live worker identity check failed" \
  "${ROOT_DIR}/tests/suites/runner_live_worker_identity/check.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${OBSERVER}"
test_pass "OS-observed worker identity and independent predictions match PW; host remains unrestricted"
