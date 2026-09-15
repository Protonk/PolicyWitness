#!/usr/bin/env bash
# Conditional sourcing and disabled errexit must not bypass startup rejection.
set +e
set -u
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
if source "${ROOT_DIR}/tests/lib/case.sh"; then
  :
fi

printf 'started\n' >"${PW_CONTROL_STARTED}"
test_begin probe assertions
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "assertion checker failed" \
  "${ROOT_DIR}/tests/fixtures/shell_case/python_assertion.py"
printf 'continued\n' >"${PW_CONTROL_CONTINUED}"
test_pass "assertion checker completed"
