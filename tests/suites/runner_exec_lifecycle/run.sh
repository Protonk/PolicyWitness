#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

for test_id in timeout_preserves_output_and_continues closed_streams_continue leader_exit_descendant worker_dies_during_exec; do
  test_selected "${test_id}" || continue
  test_begin runner_exec_lifecycle "${test_id}"
  test_require_pw
  HELPER="${PW_TEST_ARTIFACTS}/helper"
  test_step build "compile shared exec fixture"
  test_build_fixture "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${HELPER}"
  test_step run "independently observe process lifetime, output and subsequent file effects"
  if [[ "${test_id}" == timeout_preserves_output_and_continues ]]; then
    test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "exec lifecycle contract failed" \
      "${ROOT_DIR}/tests/suites/runner_exec_lifecycle/check.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${HELPER}"
  else
    test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "exec lifecycle edge failed" \
      "${ROOT_DIR}/tests/suites/runner_exec_lifecycle/check_edges.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${HELPER}" "${test_id}"
  fi
  test_pass "${test_id}: process observations and retained evidence agree"
done
