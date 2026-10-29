#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin sandbox_extensions_native directory
test_step build "build independent directory extension experiment"
test_build_fixture "${ROOT_DIR}/tests/fixtures/sandbox_extensions/build.sh" "${PW_TEST_ARTIFACTS}/native"
test_step run "sign, inspect authority and validate directory writes and persistence"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "native directory experiment failed" \
  "${ROOT_DIR}/tests/suites/sandbox_extensions_native/directory_check.py" "${PW_TEST_ARTIFACTS}"
test_pass "directory modification, exclusive creation, lifecycle controls and persistence verified"
