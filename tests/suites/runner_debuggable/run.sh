#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

failures=0

run_test() {
  local script="$1"
  set +e
  bash "${script}"
  local status=$?
  set -e
  if [[ ${status} -ne 0 ]]; then
    failures=1
  fi
}

export PW_TEST_SUITE_OVERRIDE="runner_debuggable"
unset PW_TEST_RUNNER_MODE
unset PW_TEST_RUNNER_SERVICE
unset PW_TEST_RUNNER_EXPECT_KIND
export PW_TEST_RUNNER_MODE="debuggable"
export PW_TEST_RUNNER_EXPECT_KIND="debuggable"

run_test "${ROOT_DIR}/tests/suites/smoke/pw_specimen_smoke.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/pw_instrumentation_execmem.sh"
run_test "${ROOT_DIR}/tests/suites/smoke/pw_instrumentation_invalid_phase.sh"
run_test "${ROOT_DIR}/tests/suites/blackbox_menagerie/run.sh"
run_test "${ROOT_DIR}/tests/suites/blackbox_e2e/run.sh"

if [[ ${failures} -ne 0 ]]; then
  exit 1
fi
