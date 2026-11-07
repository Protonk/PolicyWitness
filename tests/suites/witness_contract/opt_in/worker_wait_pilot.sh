#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract worker_wait_pilot
test_require_pw
SIGNING_IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "${SIGNING_IDENTITY}" ]] || test_fail "worker wait pilot needs a Developer ID Application identity matching the app team; set PW_BYOXPC_IDENTITY or IDENTITY"
# Extra driver arguments, for example --dry-run, --cells O1,A2, --window-seconds 120, --clock-pair-trials 20
# or a comparison: --compare-app PATH --compare-tree DIR.
PILOT_ARGS=()
if [[ -n "${PW_WORKER_WAIT_PILOT_ARGS:-}" ]]; then
  read -r -a PILOT_ARGS <<<"${PW_WORKER_WAIT_PILOT_ARGS}"
fi
COMPARE_APP=""
COMPARE_TREE=""
COMPARE_BUILD=""
for ((i = 0; i < ${#PILOT_ARGS[@]}; i++)); do
  case "${PILOT_ARGS[i]}" in
    --compare-app) COMPARE_APP="${PILOT_ARGS[i + 1]:-}" ;;
    --compare-app=*) COMPARE_APP="${PILOT_ARGS[i]#--compare-app=}" ;;
    --compare-tree) COMPARE_TREE="${PILOT_ARGS[i + 1]:-}" ;;
    --compare-tree=*) COMPARE_TREE="${PILOT_ARGS[i]#--compare-tree=}" ;;
  esac
done
if [[ -n "${COMPARE_APP}" && -z "${COMPARE_TREE}" ]]; then
  test_fail "a comparison needs --compare-tree, the candidate checkout the compare app was built from"
fi
test_step build "build the stamp worker, its uninstrumented twin and the native observer"
WORKER_BUILD="${PW_TEST_ARTIFACTS}/worker-build"
test_run_logged "${PW_TEST_ARTIFACTS}/worker-build.log" "worker fixture build failed" \
  bash "${ROOT_DIR}/tests/fixtures/worker_wait/build.sh" "${WORKER_BUILD}"
COMPARE_ARGS=()
if [[ -n "${COMPARE_APP}" ]]; then
  # The candidate's stamp worker: this fixture over the candidate tree's worker source and identity.
  COMPARE_BUILD="${PW_TEST_ARTIFACTS}/worker-build-candidate"
  test_run_logged "${PW_TEST_ARTIFACTS}/worker-build-candidate.log" "candidate worker fixture build failed" \
    bash "${ROOT_DIR}/tests/fixtures/worker_wait/build.sh" "${COMPARE_BUILD}" "${COMPARE_TREE}"
  COMPARE_ARGS=(--compare-worker-build "${COMPARE_BUILD}")
fi
for build in "${WORKER_BUILD}" ${COMPARE_BUILD:+"${COMPARE_BUILD}"}; do
  for worker in pw-probe-runner-stamps pw-probe-runner-plain; do
    [[ -f "${build}/${worker}" && -x "${build}/${worker}" ]] \
      || test_fail "worker fixture build produced no executable ${build}/${worker} (logs: ${PW_TEST_ARTIFACTS}/worker-build*.log)"
  done
done
test_build_fixture "${ROOT_DIR}/tests/fixtures/footprint/build.sh" "${PW_TEST_ARTIFACTS}/observer-bin" "${PW_TEST_ARTIFACTS}/observer-build.log"
test_step run "stage the stamped and neighbor apps, or the baseline and candidate apps, run the declared paced schedule and decompose the stamps"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "worker wait pilot failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_worker_wait_pilot.py" \
  "${PW_APP_DIR}" "${PW_TEST_ARTIFACTS}" "${SIGNING_IDENTITY}" \
  --worker-build "${WORKER_BUILD}" --observer "${PW_TEST_ARTIFACTS}/observer-bin" \
  ${PILOT_ARGS[@]+"${PILOT_ARGS[@]}"} ${COMPARE_ARGS[@]+"${COMPARE_ARGS[@]}"}
test_pass "declared coverage met with stamps, conditions, pacing and exclusions retained; see summary.md"
