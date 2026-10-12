#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin sandbox_extensions_native feasibility
test_step build "build independent native extension experiment"
test_build_fixture "${ROOT_DIR}/tests/fixtures/sandbox_extensions/build.sh" "${PW_TEST_ARTIFACTS}/native"
test_step run "sign, read back authority, run native controls and independently validate observations"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "native extension feasibility failed" \
  "${ROOT_DIR}/tests/suites/sandbox_extensions_native/check.py" "${PW_TEST_ARTIFACTS}"
test_pass "native lifecycle, independent effects, lifetime and allocation controls verified"
