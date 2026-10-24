#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract worker_termination
test_require_pw
test_step run "ordinary denied writes precede self-signal; worker disposition retains independent cause evidence"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "termination contract failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_worker_termination.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "process disposition, denied writes, prediction evidence and worker disposal remain independent" "{}"
