#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin run_effects aftermath_footprint
test_require_pw
SIGNING_IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "${SIGNING_IDENTITY}" ]] || test_fail "actor aftermath footprint needs a Developer ID Application identity matching the app team; set PW_BYOXPC_IDENTITY or IDENTITY"
test_build_fixture "${ROOT_DIR}/tests/fixtures/validator/build_bridge.sh" "${PW_TEST_ARTIFACTS}/bridge-bin" "${PW_TEST_ARTIFACTS}/bridge-build.log"
test_build_fixture "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${PW_TEST_ARTIFACTS}/helper" "${PW_TEST_ARTIFACTS}/helper-build.log"
test_build_fixture "${ROOT_DIR}/tests/fixtures/footprint/build.sh" "${PW_TEST_ARTIFACTS}/observer-bin" "${PW_TEST_ARTIFACTS}/observer-build.log"
test_step observe "inventory completion and invoked timeout before fixture interventions"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "aftermath footprint observation failed" \
  "${ROOT_DIR}/tests/suites/run_effects/check_aftermath_footprint.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${PW_TEST_ARTIFACTS}/bridge-bin" \
  "${PW_TEST_ARTIFACTS}/helper" "${PW_TEST_ARTIFACTS}/observer-bin" "${SIGNING_IDENTITY}"
test_pass "all inventoried states and independent worker endings retained before cleanup"
