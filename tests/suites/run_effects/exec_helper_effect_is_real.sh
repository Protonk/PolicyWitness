#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin run_effects exec_helper_effect_is_real
test_require_pw
test_step build "compile the shared exec fixture"
test_build_fixture "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${PW_TEST_ARTIFACTS}/exec-helper"
test_step run "spawn the helper with --write under deny default plus exec_baseline, with and without a write allow"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "exec helper effect contract failed" \
  "${ROOT_DIR}/tests/suites/run_effects/check_exec_effect.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${PW_TEST_ARTIFACTS}/exec-helper"
test_pass "an allowed helper's file write is real; a denied helper runs but leaves no file"
