#!/usr/bin/env bash
# Deliberately no `set -e`: helper failures must terminate this case themselves.
set -uo pipefail
FIXTURE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${1:?path to case library}"

test_begin "${CONTROL_SUITE}" "${CONTROL_ID}"
if [[ "${CONTROL_MODE}" == optional_skip ]]; then
  if ! require_pw_app "${PW_BIN}"; then exit 0; fi
  exit 2  # This control supplies a missing optional app.
fi
test_require_pw
test_step build "controlled fixture build"
test_build_fixture "${FIXTURE_DIR}/build.sh" "${PW_TEST_ARTIFACTS}/helper"
test_step check "controlled Python checker"
CHECK_LOG="${PW_TEST_ARTIFACTS}/assert custom.log"
if [[ "${CONTROL_MODE}" == log_open_failure ]]; then
  CHECK_LOG="${PW_TEST_ARTIFACTS}/missing-parent/assert.log"
fi
if [[ "${CONTROL_MODE}" == missing_command ]]; then
  test_run_logged "${CHECK_LOG}" "controlled checker failed"
elif [[ "${CONTROL_MODE}" == missing_checker ]]; then
  test_check_python "${CHECK_LOG}" "controlled checker failed"
else
  test_check_python "${CHECK_LOG}" "controlled checker failed" \
    "${FIXTURE_DIR}/command.py" check "${PW_BIN}" "${CONTROL_LITERAL}"
fi
test_step later "must only run after the checker succeeds"
test_run_logged "${PW_TEST_ARTIFACTS}/later.log" "controlled later stage failed" \
  /usr/bin/python3 "${FIXTURE_DIR}/command.py" later
test_pass "controlled case passed"
