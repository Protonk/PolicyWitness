#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_validator_failure actor_collection_failure_reports_degraded
test_require_pw
test_step run "one actor in each sandbox mode with a failed validator spawn and an undecodable reply; observe each write before decoding"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "actor collection failure contract failed" \
  "${ROOT_DIR}/tests/suites/runner_validator_failure/check_actor.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "a failed actor-phase collection selects the summary in both sandbox modes; completed writes and phase evidence retained"
