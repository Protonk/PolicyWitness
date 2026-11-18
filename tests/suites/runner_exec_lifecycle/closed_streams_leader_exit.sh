#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_exec_lifecycle closed_streams_leader_exit
test_require_pw
HELPER="${PW_TEST_ARTIFACTS}/helper"
ACCOUNT="${PW_TEST_ARTIFACTS}/account.json"
CHECK_LOG="${PW_TEST_ARTIFACTS}/assert.log"
account_value() {
  "${PW_PYTHON}" -B -S -P -c 'import json, sys
value = json.load(open(sys.argv[1]))
for key in sys.argv[2:]:
    value = value[key]
print(value if isinstance(value, str) else json.dumps(value, sort_keys=True))' "${ACCOUNT}" "$@"
}
test_step build "compile the existing independently controlled exec fixture"
test_build_fixture "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${HELPER}"
test_step run "observe the same-group descendant after stream closure and leader exit, then judge the reply and the later file effect"
CHECK_STATUS=0
"${PW_PYTHON}" -B -S "${ROOT_DIR}/tests/suites/runner_exec_lifecycle/check_closed_streams_leader_exit.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${HELPER}" >"${CHECK_LOG}" 2>&1 || CHECK_STATUS=$?
# The checker writes its account only after every observation and judgment is
# made. Publish it even when the cleanup that follows fails.
if [[ -f "${ACCOUNT}" ]]; then
  test_observe descendant_lifetime "$(account_value descendant_lifetime)" \
    "${PW_TEST_ARTIFACTS}/observations.json" "${PW_TEST_ARTIFACTS}/classifier-controls.json" \
    "${PW_TEST_ARTIFACTS}/capture.json" "${PW_TEST_ARTIFACTS}/cleanup.json"
  test_observe exec_reply "$(account_value exec_reply)" \
    "${PW_TEST_ARTIFACTS}/specimen.json" "${PW_TEST_ARTIFACTS}/run.json" \
    "${PW_TEST_ARTIFACTS}/pw.stderr" "${PW_TEST_ARTIFACTS}/capture.json"
  test_observe later_file_effect "$(account_value later_file_effect)" \
    "${PW_TEST_ARTIFACTS}/before.bin" "${PW_TEST_ARTIFACTS}/after.bin"
  for judgment in truthful_exec_account later_step_effect; do
    test_judge "${judgment}" "$(account_value judgments "${judgment}" result)" "$(account_value judgments "${judgment}" detail)"
  done
fi
if [[ "${CHECK_STATUS}" -ne 0 ]]; then
  cat "${CHECK_LOG}" >&2 || true
  test_fail "same-group descendant observation, its required evidence or fixture cleanup failed (exit ${CHECK_STATUS}; log: ${CHECK_LOG})"
fi
test_complete "descendant lifetime after ordinary completion recorded without a verdict ($(account_value descendant_lifetime history)); reply account and later file effect judged; fixture cleanup confirmed"
