#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract comparison_matrix
test_require_pw
test_step fixture "build the exit-status helpers the spawn rows copy into the scenario root"
export PW_COMPARISON_HELPER_FIXTURE="${PW_TEST_ARTIFACTS}/helper-fixture"
test_build_fixture "${ROOT_DIR}/tests/fixtures/comparison/build.sh" \
  "${PW_COMPARISON_HELPER_FIXTURE}" "${PW_TEST_ARTIFACTS}/helper-fixture-build.log"
test_step run "run the S, B and C specimens of tests/fixtures/comparison/matrix.json and check every step against its reviewed row"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "comparison matrix contract failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_comparison_matrix.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "every matrix row's comparison record, raw fields and file effects match the reviewed fixture" "{}"
