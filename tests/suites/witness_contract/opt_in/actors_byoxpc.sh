#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract actors_byoxpc
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
test_step install "install an owned runner with the selected app's own worker entitlements"
test_check_python "${PW_TEST_ARTIFACTS}/setup.log" "actor BYOXPC setup failed" \
  "$SESSION_TOOL" install "$PW_BIN" "$PW_APP_DIR" "$PW_TEST_ARTIFACTS" "${PW_TEST_ARTIFACTS}/runner_env.json" "$IDENTITY"
export PW_RUNNER_REGISTRY="$("${PW_PYTHON}" -B -S -P -c 'import json,sys; print(json.load(open(sys.argv[1]))["PW_RUNNER_REGISTRY"])' "${PW_TEST_ARTIFACTS}/runner_env.json")"
test_step redelegation "repeat the principal re-delegation, calibration and contrasts through the owned runner's selected worker"
test_check_python "${PW_TEST_ARTIFACTS}/redelegation.log" "BYOXPC actor re-delegation failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_extension_redelegation.py" "$PW_BIN" "${PW_TEST_ARTIFACTS}/redelegation" "${PW_TEST_ARTIFACTS}/session.json"
test_step no_issuer "hold the installed issuer aside: the declaration form is refused, the actor form issues and consumes with no helper, exact bytes restored"
test_check_python "${PW_TEST_ARTIFACTS}/no-issuer.log" "actor no-issuer contrast failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/opt_in/check_actor_no_issuer.py" "$PW_BIN" "${PW_TEST_ARTIFACTS}"
test_step inherited "an unapplied actor on an App Sandbox-signed copy of the worker inherits that restriction; the ordinary worker is the baseline"
test_check_python "${PW_TEST_ARTIFACTS}/inherited.log" "actor inherited restriction control failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/opt_in/check_actor_inherited_restriction.py" "$PW_BIN" "${PW_TEST_ARTIFACTS}" "$IDENTITY"
test_check_python "${PW_TEST_ARTIFACTS}/cleanup.log" "actor BYOXPC cleanup failed" \
  "$SESSION_TOOL" cleanup "$PW_BIN" "${PW_TEST_ARTIFACTS}/session.json"
trap - EXIT
test_pass "BYOXPC actor re-delegation, no-issuer contrast and inherited-restriction control pass with verified cleanup"
