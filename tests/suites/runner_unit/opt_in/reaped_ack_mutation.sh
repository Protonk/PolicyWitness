#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_unit reaped_ack_mutation
test_step controls "remove final acknowledgement reconciliation in a disposable host copy"
test_check_python "${PW_TEST_ARTIFACTS}/controls.log" "confirmed-reap acknowledgement mutation failed" \
  "${ROOT_DIR}/tests/suites/runner_unit/opt_in/reaped_ack_mutation.py" "${PW_TEST_ARTIFACTS}/controls"
test_pass "clean and fatal unseen acknowledgements require final reconciliation; prior ownership loss remains unqualified"
