#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract worker_attempt_in_flight_at_deadline
test_require_pw
test_step run "a writerless FIFO blocks attempt 0 until the host deadline; the witnessed host cleanup must be projected as the cause"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "attempt-in-flight disposition contract failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_attempt_in_flight.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "host deadline, SIGKILL request and reaped signal project to the witnessed host cleanup cause" "{}"
