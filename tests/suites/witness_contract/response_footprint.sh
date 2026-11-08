#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract response_footprint
test_require_pw
test_build_fixture "${ROOT_DIR}/tests/fixtures/footprint/build.sh" "${PW_TEST_ARTIFACTS}/footprint-observer" "${PW_TEST_ARTIFACTS}/observer-build.log"
test_step run "sample fresh shipped controllers and preserve exact response representations"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "response footprint failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_response_footprint.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${PW_TEST_ARTIFACTS}/footprint-observer"
test_pass "complete ordinary and actor replies; typed binary ownership account and sampled controller memory" "{}"
