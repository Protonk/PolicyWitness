#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_byoxpc retirement_observations
test_require_pw
SESSION_TOOL="${ROOT_DIR}/tests/fixtures/byoxpc/session.py"
cleanup() {
  local status=$?
  trap - EXIT
  "${PW_PYTHON}" -B -S "${SESSION_TOOL}" cleanup "${PW_BIN}" "${PW_TEST_ARTIFACTS}/session.json" || status=1
  exit "$status"
}
trap cleanup EXIT
IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "$IDENTITY" ]] || test_fail "matching Developer ID required"
test_check_python "${PW_TEST_ARTIFACTS}/setup.log" "owned BYOXPC setup failed" \
  "$SESSION_TOOL" install "$PW_BIN" "$PW_APP_DIR" "$PW_TEST_ARTIFACTS" "${PW_TEST_ARTIFACTS}/runner_env.json" "$IDENTITY"
export PW_RUNNER_REGISTRY="$("${PW_PYTHON}" -B -S -P -c 'import json,sys; print(json.load(open(sys.argv[1]))["PW_RUNNER_REGISTRY"])' "${PW_TEST_ARTIFACTS}/runner_env.json")"
test_step observe "capture 48 ordinary empty-plan requests at fixed gaps, generations and direct exit observations"
test_check_python "${PW_TEST_ARTIFACTS}/observations.log" "retirement experiment incomplete" \
  "${ROOT_DIR}/tests/suites/runner_byoxpc/opt_in/retirement_observations.py" "$PW_BIN" "$PW_TEST_ARTIFACTS"
test_check_python "${PW_TEST_ARTIFACTS}/cleanup.log" "BYOXPC cleanup failed" \
  "$SESSION_TOOL" cleanup "$PW_BIN" "${PW_TEST_ARTIFACTS}/session.json"
trap - EXIT
test_pass "observational experiment completed and service removal verified; outcomes do not establish BYOXPC reliability"
