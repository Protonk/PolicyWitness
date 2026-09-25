#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin run_effects run_installs_nothing
test_require_pw
test_step run "inventory the runner registry and launchd plist directories around one plain run"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "plain run changed persistent registration" \
  "${ROOT_DIR}/tests/suites/run_effects/check_installs_nothing.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "a plain run adds no launchd plist and leaves the runner registry unchanged"
