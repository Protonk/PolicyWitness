#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"
source "${ROOT_DIR}/tests/lib/testlib.sh"
CASE="${1:?expected eof or malformed}"
SUITE="${2:-runner_validator_failure}"
case "${CASE}" in
  eof) TEST_ID=validator_unavailable_reports_degraded ;;
  malformed) TEST_ID=validator_decode_failure_reports_degraded ;;
  *) exit 2 ;;
esac
test_begin "${SUITE}" "${TEST_ID}"
[[ -x "${PW_BIN}" ]] || test_fail "built policy-witness missing: ${PW_BIN}"
test_step run "reverse two verdicts, then ${CASE}; preserve completed evidence and its step association"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/runner_validator_failure/check.py" \
    "${CASE}" "${PW_TEST_ARTIFACTS}" "${PW_BIN}" >"${PW_TEST_ARTIFACTS}/assertions.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assertions.log" >&2
  test_fail "validator failure contract failed; see artifacts/assertions.log"
fi
test_pass "partial verdicts retain step identity; three completed attempts survive validator degradation"
