#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract worker_wait_pilot_controls
test_step run "accept complete constructed pilot receipts and reject independent page, clock-order, file, condition and pooling faults"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "worker wait pilot reader controls failed" \
 "${ROOT_DIR}/tests/suites/witness_contract/worker_wait_pilot_controls.py" "${PW_TEST_ARTIFACTS}"
test_pass "worker-wait pilot reader sensitivity verified at constructed scope"
