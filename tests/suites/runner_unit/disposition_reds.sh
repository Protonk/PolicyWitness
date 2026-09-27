#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

# Non-default case: runs the Swift unit executable with PW_DISPOSITION_REDS=1 so
# DispositionResolverTests registers its integration-gap blocks. Those blocks
# fail until the resolver and record exist; every other block must pass, so an
# unrelated FAIL or a missing summary is an equipment or regression failure,
# not the expected red. See tests/OPT_IN_TESTS.md.
test_begin "runner_unit" "disposition_reds"
test_step "swift_run" "build and run PWRunnerCoreTests with PW_DISPOSITION_REDS=1"

if ! command -v swift >/dev/null 2>&1; then
  test_fail "swift toolchain not on PATH (install Xcode Command Line Tools)" "{}"
fi
PACKAGE_DIR="${ROOT_DIR}/runner"
RUN_LOG="${PW_TEST_ARTIFACTS}/pwrunner_core_tests.log"

test_step fixture "build the ABI-compatible child for the lifecycle controls"
export PW_LIFECYCLE_WORKER_FIXTURE="${PW_TEST_ARTIFACTS}/worker-lifecycle-fixture"
test_build_fixture "${ROOT_DIR}/tests/fixtures/worker_lifecycle/build.sh" \
  "${PW_LIFECYCLE_WORKER_FIXTURE}" "${PW_TEST_ARTIFACTS}/lifecycle-fixture-build.log"

set +e
PW_DISPOSITION_REDS=1 swift run --package-path "${PACKAGE_DIR}" PWRunnerCoreTests >"${RUN_LOG}" 2>&1
RC=$?
set -e

if ! grep -Eq '^[0-9]+/[0-9]+ tests passed$' "${RUN_LOG}"; then
  TAIL="$(tail -n 15 "${RUN_LOG}" | sed 's/"/\\"/g')"
  test_fail "PWRunnerCoreTests did not reach its summary (rc=${RC}); tail: ${TAIL}" "{\"log\":\"${RUN_LOG}\"}"
fi
if grep -Eq '^[[:space:]]*SKIP[[:space:]]' "${RUN_LOG}"; then
  test_fail "required Swift cases reported internal SKIP" "{\"log\":\"${RUN_LOG}\"}"
fi
GAP_FAILS="$(grep -Ec '^[[:space:]]*FAIL disposition gap:' "${RUN_LOG}" || true)"
OTHER_FAILS="$(grep -E '^[[:space:]]*FAIL ' "${RUN_LOG}" | grep -Evc 'FAIL disposition gap:' || true)"
if [[ "${OTHER_FAILS}" -ne 0 ]]; then
  test_fail "unrelated Swift failures beside the disposition gaps (${OTHER_FAILS})" "{\"log\":\"${RUN_LOG}\"}"
fi
if ! grep -Eq '^[[:space:]]*(ok|FAIL) +disposition gap:' "${RUN_LOG}"; then
  test_fail "no disposition gap block ran; check the PW_DISPOSITION_REDS gate" "{\"log\":\"${RUN_LOG}\"}"
fi
if [[ "${GAP_FAILS}" -ne 0 ]]; then
  test_fail "disposition integration gaps still open (${GAP_FAILS}); expected until the resolver lands" "{\"log\":\"${RUN_LOG}\"}"
fi
test_pass "every disposition gap block passes; promote by removing the gate" "{\"log\":\"${RUN_LOG}\"}"
