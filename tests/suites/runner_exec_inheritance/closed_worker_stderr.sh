#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
WORKER="${PW_APP_DIR}/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_exec_inheritance closed_worker_stderr
test_step characterize "compare open and closed worker stderr using the unchanged shipped worker"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "closed worker stderr characterization failed" \
  "${ROOT_DIR}/tests/suites/runner_exec_inheritance/opt_in/closed_worker_stderr.py" \
  "${WORKER}" "${PW_TEST_ARTIFACTS}"
test_pass "baseline stderr works; closed worker stderr produces independently observed child EBADF"
