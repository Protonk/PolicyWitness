#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract worker_wait_cost
test_require_pw
SIGNING_IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "${SIGNING_IDENTITY}" ]] || test_fail "worker wait cost screen needs matching Developer ID signing"
[[ -n "${PW_WAIT_COST_GATE:-}" && ! -e "${PW_WAIT_COST_GATE}" ]] || test_fail "fresh PW_WAIT_COST_GATE required"
ROLE="${PW_WAIT_COST_ROLE:-release}"
CANDIDATE="${PW_WAIT_COST_CANDIDATE:-baseline}"
if [[ "${CANDIDATE}" == wfet ]]; then
 test_run_logged "${PW_TEST_ARTIFACTS}/feature.log" "WFET hardware feature unavailable" \
  /usr/sbin/sysctl -n hw.optional.arm.FEAT_WFxT
 [[ "$(cat "${PW_TEST_ARTIFACTS}/feature.log")" == 1 ]] || test_fail "WFET feature must be explicitly present"
fi
test_build_fixture "${ROOT_DIR}/tests/fixtures/footprint/build.sh" "${PW_TEST_ARTIFACTS}/observer-bin" "${PW_TEST_ARTIFACTS}/observer-build.log"
test_build_fixture "${ROOT_DIR}/tests/fixtures/validator/build_bridge.sh" "${PW_TEST_ARTIFACTS}/bridge-bin" "${PW_TEST_ARTIFACTS}/bridge-build.log"
test_build_fixture "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${PW_TEST_ARTIFACTS}/helper" "${PW_TEST_ARTIFACTS}/helper-build.log"
test_step screen "stage identities and wait for the coordinator's bounded CPU window"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "worker wait cost screen failed" \
 "${ROOT_DIR}/tests/suites/witness_contract/worker_wait_cost.py" \
 "${PW_APP_DIR}" "${PW_TEST_ARTIFACTS}" "${SIGNING_IDENTITY}" \
 "${PW_TEST_ARTIFACTS}/observer-bin" "${PW_TEST_ARTIFACTS}/bridge-bin" "${PW_TEST_ARTIFACTS}/helper" \
 --role "${ROLE}" --candidate "${CANDIDATE}" --gate "${PW_WAIT_COST_GATE}" --minimum "${PW_WAIT_COST_MINIMUM:-0.1}"
test_pass "fixed CPU screen complete; result is not deployment or response acceptance"
