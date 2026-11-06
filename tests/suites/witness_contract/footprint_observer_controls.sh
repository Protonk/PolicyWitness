#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract footprint_observer_controls
test_build_fixture "${ROOT_DIR}/tests/fixtures/footprint/build.sh" "${PW_TEST_ARTIFACTS}/footprint-observer" "${PW_TEST_ARTIFACTS}/observer-build.log"
test_step run "calibrate persistent native meter with acknowledged live children"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "footprint observer controls failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/footprint_observer_controls.py" \
  "${PW_TEST_ARTIFACTS}/footprint-observer" "${PW_TEST_ARTIFACTS}"
test_pass "live observer sensitivity and receipt corruption rejection verified"
