#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract worker_wait_pilot
test_require_pw
SIGNING_IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "${SIGNING_IDENTITY}" ]] || test_fail "worker wait pilot needs a Developer ID Application identity matching the app team; set PW_BYOXPC_IDENTITY or IDENTITY"
# Extra driver arguments, for example --dry-run, --cells O1,A2, --window-seconds 120 or --clock-pair-trials 20.
PILOT_ARGS=()
if [[ -n "${PW_WORKER_WAIT_PILOT_ARGS:-}" ]]; then
  read -r -a PILOT_ARGS <<<"${PW_WORKER_WAIT_PILOT_ARGS}"
fi
test_step build "build the stamp worker, its uninstrumented twin and the native observer"
WORKER_BUILD="${PW_TEST_ARTIFACTS}/worker-build"
test_run_logged "${PW_TEST_ARTIFACTS}/worker-build.log" "worker fixture build failed" \
  bash "${ROOT_DIR}/tests/fixtures/worker_wait/build.sh" "${WORKER_BUILD}"
for worker in pw-probe-runner-stamps pw-probe-runner-plain; do
  [[ -f "${WORKER_BUILD}/${worker}" && -x "${WORKER_BUILD}/${worker}" ]] \
    || test_fail "worker fixture build produced no executable ${worker} (log: ${PW_TEST_ARTIFACTS}/worker-build.log)"
done
test_build_fixture "${ROOT_DIR}/tests/fixtures/footprint/build.sh" "${PW_TEST_ARTIFACTS}/observer-bin" "${PW_TEST_ARTIFACTS}/observer-build.log"
test_step run "stage stamped and neighbor apps, run the declared paced schedule and decompose the stamps"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "worker wait pilot failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_worker_wait_pilot.py" \
  "${PW_APP_DIR}" "${PW_TEST_ARTIFACTS}" "${SIGNING_IDENTITY}" \
  --worker-build "${WORKER_BUILD}" --observer "${PW_TEST_ARTIFACTS}/observer-bin" \
  ${PILOT_ARGS[@]+"${PILOT_ARGS[@]}"}
test_pass "declared coverage met with stamps, conditions, pacing and exclusions retained; see summary.md"
