#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract order_barrier_mutations
test_require_pw
SIGNING_IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "${SIGNING_IDENTITY}" ]] || test_fail "required barrier mutation control needs a Developer ID Application identity matching the app team; set PW_BYOXPC_IDENTITY or IDENTITY"
test_step build "build independent bridge, exec observer, C harness and lifecycle fixture"
test_build_fixture "${ROOT_DIR}/tests/fixtures/validator/build_bridge.sh" "${PW_TEST_ARTIFACTS}/bridge" "${PW_TEST_ARTIFACTS}/bridge-build.log"
test_build_fixture "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${PW_TEST_ARTIFACTS}/helper" "${PW_TEST_ARTIFACTS}/helper-build.log"
test_build_fixture "${ROOT_DIR}/tests/fixtures/worker_harness/build.sh" "${PW_TEST_ARTIFACTS}/harness" "${PW_TEST_ARTIFACTS}/harness-build.log"
test_build_fixture "${ROOT_DIR}/tests/fixtures/worker_lifecycle/build.sh" "${PW_TEST_ARTIFACTS}/lifecycle" "${PW_TEST_ARTIFACTS}/lifecycle-build.log"
test_step run "baseline must pass; worker and host bypasses must cause early effects while collection is held"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "barrier mutation controls failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/opt_in/mutations.py" \
  "${PW_APP_DIR}" "${PW_TEST_ARTIFACTS}" "${SIGNING_IDENTITY}"
test_pass "baseline accepted; both bypasses rejected by component gate and independent CLI effects"
