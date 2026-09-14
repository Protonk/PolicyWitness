#!/usr/bin/env bash
# Copied to a tiny fixture repository as each selected suite's runner.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
NAME="$(basename "$(dirname "${BASH_SOURCE[0]}")")"
source "${ROOT_DIR}/tests/lib/testlib.sh"

case "${NAME}" in
  silent) exit 0 ;;
  crash) exit 23 ;;
  wrapper)
    bash "${ROOT_DIR}/tests/suites/leaf/run.sh"
    exit 0
    ;;
esac

SUITE="${NAME}"
if [[ "${NAME}" == leaf ]]; then SUITE=reported_alias; fi
test_begin "${SUITE}" fixture_case
if [[ "${NAME}" == signal_exit ]]; then kill -TERM "$$"; fi
if [[ "${NAME}" == skip ]]; then test_skip "explicit fixture limitation"; exit 0; fi
if [[ "${NAME}" == fail_then_zero ]]; then
  (test_fail "deliberate failed report") || true
  exit 0
fi
test_pass "fixture reports success"
case "${NAME}" in
  pass_then_crash) exit 19 ;;
  unfinished) test_begin "${SUITE}" unfinished_case ;;
  duplicate_end) test_pass "second terminal event" ;;
  pass|leaf) ;;
  *) /usr/bin/python3 "${ROOT_DIR}/tests/fixtures/dispatcher/alter.py" \
       "${NAME}" "${PW_TEST_REPORT}" "${PW_TEST_EVENTS}" ;;
esac
