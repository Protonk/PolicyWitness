#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract held_phase_footprint
test_require_pw
SIGNING_IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "${SIGNING_IDENTITY}" ]] || test_fail "held actor footprint needs a Developer ID Application identity matching the app team; set PW_BYOXPC_IDENTITY or IDENTITY"
test_build_fixture "${ROOT_DIR}/tests/fixtures/footprint/build.sh" "${PW_TEST_ARTIFACTS}/observer-bin" "${PW_TEST_ARTIFACTS}/observer-build.log"
test_build_fixture "${ROOT_DIR}/tests/fixtures/validator/build_bridge.sh" "${PW_TEST_ARTIFACTS}/bridge-bin" "${PW_TEST_ARTIFACTS}/bridge-build.log"
test_build_fixture "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${PW_TEST_ARTIFACTS}/helper" "${PW_TEST_ARTIFACTS}/helper-build.log"
test_step run "measure declared repeated held intervals with native matched controls"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "held phase footprint failed" \
 "${ROOT_DIR}/tests/suites/witness_contract/check_held_phase_footprint.py" \
 "${PW_APP_DIR}" "${PW_TEST_ARTIFACTS}" "${SIGNING_IDENTITY}" "${PW_TEST_ARTIFACTS}/bridge-bin" "${PW_TEST_ARTIFACTS}/helper" "${PW_TEST_ARTIFACTS}/observer-bin"
test_pass "matched holds and actor authority publications verified"
