#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin "${PW_TEST_SUITE_OVERRIDE:-runner_byoxpc}" runner_install
test_require_pw
RUNNER_ENV_PATH="${PW_TEST_RUNNER_ENV_PATH:-${PW_TEST_ARTIFACTS}/runner_env.json}"
SESSION_TOOL="${ROOT_DIR}/tests/fixtures/byoxpc/session.py"
# The wrapper owns cleanup across specimen cases. A direct setup invocation
# instead removes its installation on exit, including failed setup.
if [[ -z "${PW_TEST_RUNNER_ENV_PATH+x}" ]]; then
  cleanup() {
    local status=$?
    trap - EXIT
    /usr/bin/python3 "${SESSION_TOOL}" cleanup "${PW_BIN}" "${PW_TEST_ARTIFACTS}/session.json" || status=1
    exit "${status}"
  }
  trap cleanup EXIT
fi
IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "${IDENTITY}" ]] || test_fail "BYOXPC setup requires a matching Developer ID identity"
test_step install "copy, inspect, sign, install, and verify an owned BYOXPC runner"
test_check_python "${PW_TEST_ARTIFACTS}/setup.log" "BYOXPC setup failed" \
  "${SESSION_TOOL}" install "${PW_BIN}" "${PW_APP_DIR}" "${PW_TEST_ARTIFACTS}" "${RUNNER_ENV_PATH}" "${IDENTITY}"
test_pass "disposable BYOXPC runner signed, installed, and verified"
