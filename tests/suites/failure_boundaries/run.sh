#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
for case_id in admission fallback_helper validator_frames validator_association validator_overlong_request validator_removed_target; do
  test_selected "${case_id}" || continue
  test_begin failure_boundaries "${case_id}"
  test_require_pw
  test_step run "check ${case_id} through the signed CLI"
  test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "failure boundary contract failed" \
    "${ROOT_DIR}/tests/suites/failure_boundaries/check.py" "${case_id}" "${PW_TEST_ARTIFACTS}" "${PW_BIN}"
  test_pass "${case_id}: owning observer, retained evidence and unavailable channels verified"
done
