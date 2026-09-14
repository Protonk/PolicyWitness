#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
CASE="${1:?expected eof or malformed}"
SUITE="${2:-runner_validator_failure}"
case "${CASE}" in
  eof) TEST_ID=validator_unavailable_reports_degraded ;;
  malformed) TEST_ID=validator_decode_failure_reports_degraded ;;
  *) exit 2 ;;
esac
test_begin "${SUITE}" "${TEST_ID}"
test_require_pw
test_step run "reverse two verdicts, then ${CASE}; preserve completed evidence and its step association"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" \
  "validator failure contract failed" \
  "${ROOT_DIR}/tests/suites/runner_validator_failure/check.py" \
  "${CASE}" "${PW_TEST_ARTIFACTS}" "${PW_BIN}"
test_pass "partial verdicts retain step identity; three completed attempts survive validator degradation"
