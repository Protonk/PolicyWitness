#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract max_exec_steps_spawn
test_require_pw
test_step run "256 exec steps of /usr/bin/true; every attempt must spawn a clean child"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "maximum exec plan contract failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_max_exec_steps.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "every exec step of a 256-step plan spawned; the worker's descriptor limit fit the plan" "{}"
