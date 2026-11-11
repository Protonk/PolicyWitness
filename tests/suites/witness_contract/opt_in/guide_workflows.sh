#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin witness_contract guide_workflows
test_require_pw
GUIDE_TOOL="${ROOT_DIR}/tests/suites/witness_contract/opt_in/guide_workflows.py"
cleanup() {
  local status=$?
  trap - EXIT
  "${PW_PYTHON}" -B -S "${GUIDE_TOOL}" cleanup "${PW_APP_DIR}" "${PW_TEST_ARTIFACTS}" || status=1
  exit "${status}"
}
trap cleanup EXIT
IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "${IDENTITY}" ]] || test_fail "guide workflows require a matching Developer ID identity"
test_step workflows "execute the staged guide's saved-request, repair, helper and owned BYOXPC workflows"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "guide workflow or owned cleanup failed" \
  "${GUIDE_TOOL}" run "${PW_APP_DIR}" "${PW_TEST_ARTIFACTS}" "${IDENTITY}"
test_pass "the selected guide's commands produced independently observed file effects, concrete capture repairs and verified runner removal" "{}"
