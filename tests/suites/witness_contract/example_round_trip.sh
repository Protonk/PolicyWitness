#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract example_round_trip
test_require_pw

# This case holds no specimen. It runs the selected app directly, retains the
# raw stdout, stderr and exit status of every invocation, and submits the
# emitted bytes unchanged.
CHECKER="${ROOT_DIR}/tests/suites/witness_contract/check_example_round_trip.py"
CAPTURE="${PW_TEST_ARTIFACTS}/capture"
mkdir "${CAPTURE}"

invoke() {
  local prefix="$1"
  shift
  local status=0
  "${PW_BIN}" "$@" >"${prefix}.stdout" 2>"${prefix}.stderr" || status=$?
  printf '%s\n' "${status}" >"${prefix}.exit"
}

test_step emit "print the app's version and its example twice"
invoke "${CAPTURE}/version" --version
invoke "${CAPTURE}/example-1" example
invoke "${CAPTURE}/example-2" example

test_step prepare "gate the emitted bytes, observe the attempt targets and change the bytes in one place per refusal"
if ! "${PW_PYTHON}" -B -S "${CHECKER}" prepare "${CAPTURE}" "${PW_APP_DIR}" \
    "${ROOT_DIR}/docs/contract/public.json" >"${PW_TEST_ARTIFACTS}/prepare.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/prepare.log" >&2 || true
  test_fail "the emitted document was not submitted (report: ${CAPTURE}/report.json)"
fi

test_step run "submit the emitted bytes through run, then each changed input"
invoke "${CAPTURE}/run" run "${CAPTURE}/example-1.stdout"
test_run_logged "${PW_TEST_ARTIFACTS}/observe-after.log" "target observation after the run failed" \
  "${PW_PYTHON}" -B -S "${CHECKER}" observe-after "${CAPTURE}"
for directory in "${CAPTURE}"/refusals/*/; do
  invoke "${directory}run" run "${directory}input.json"
done

test_step check "read the retained captures"
test_check_python "${PW_TEST_ARTIFACTS}/check.log" "example round trip failed (report: ${CAPTURE}/report.json)" \
  "${CHECKER}" evaluate "${CAPTURE}"
test_pass "the app's own example passes from example through run; every changed input is refused at its boundary" "{}"
