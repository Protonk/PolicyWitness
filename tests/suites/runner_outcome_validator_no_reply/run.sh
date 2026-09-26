#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_outcome_validator_no_reply validator_io_deadline_releases_worker
test_require_pw
test_step run "real validator I/O deadline retains a partial prediction and releases both file attempts"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "validator deadline contract failed" \
  "${ROOT_DIR}/tests/suites/runner_outcome_validator_no_reply/check.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "validator_no_reply, honored deadline override, retained ordered prediction, both independent file effects"
