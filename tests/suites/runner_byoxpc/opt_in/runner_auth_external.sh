#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin "${PW_TEST_SUITE_OVERRIDE:-runner_byoxpc}" runner_auth_external
test_require_pw
SESSION_TOOL="${ROOT_DIR}/tests/fixtures/byoxpc/session.py"
cleanup() {
  local status=$?
  trap - EXIT
  /usr/bin/python3 "${SESSION_TOOL}" cleanup "${PW_BIN}" "${PW_TEST_ARTIFACTS}/session.json" || status=1
  exit "${status}"
}
trap cleanup EXIT
test_step install "install and verify a uniquely owned ad-hoc runner with caller-auth keys removed"
test_check_python "${PW_TEST_ARTIFACTS}/setup.log" "ad-hoc BYOXPC setup failed" \
  "${SESSION_TOOL}" install-noauth "${PW_BIN}" "${PW_APP_DIR}" "${PW_TEST_ARTIFACTS}" "${PW_TEST_ARTIFACTS}/runner_env.json" -
test_step cleanup "verify service, plist and registry absence before deleting staged ownership"
test_check_python "${PW_TEST_ARTIFACTS}/cleanup.log" "ad-hoc BYOXPC cleanup failed" \
  "${SESSION_TOOL}" cleanup "${PW_BIN}" "${PW_TEST_ARTIFACTS}/session.json"
trap - EXIT
test_pass "external runner installs without auth keys and is removed with verified absence"
