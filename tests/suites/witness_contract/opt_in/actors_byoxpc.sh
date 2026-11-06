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
SUPPLIED="${PW_TEST_ARTIFACTS}/supplied.plist"
"${PW_PYTHON}" -B -S -P - "$SUPPLIED" <<'PYTHON'
import plistlib, sys
from pathlib import Path
Path(sys.argv[1]).write_bytes(plistlib.dumps({'com.apple.security.cs.allow-jit': True, 'com.apple.security.cs.allow-unsigned-executable-memory': False}))
PYTHON
test_step install "install one owned runner with independently signed selected and unentitled workers"
test_check_python "${PW_TEST_ARTIFACTS}/setup.log" "actor BYOXPC setup failed" \
  "$SESSION_TOOL" install "$PW_BIN" "$PW_APP_DIR" "$PW_TEST_ARTIFACTS" "${PW_TEST_ARTIFACTS}/runner_env.json" "$IDENTITY" "$SUPPLIED"
export PW_RUNNER_REGISTRY="$("${PW_PYTHON}" -B -S -P -c 'import json,sys; print(json.load(open(sys.argv[1]))["PW_RUNNER_REGISTRY"])' "${PW_TEST_ARTIFACTS}/runner_env.json")"
test_step readback "read both worker roles, host and validator from installed bytes and registry"
test_check_python "${PW_TEST_ARTIFACTS}/readback.log" "worker equipment read-back failed" \
  "${ROOT_DIR}/tests/suites/runner_byoxpc/opt_in/entitlement_readback.py" "$PW_BIN" "$PW_TEST_ARTIFACTS" "$SUPPLIED"
test_step equipment "mixed packaged authority, reordered actors and a same-selected substitution rejected independently of native success"
test_check_python "${PW_TEST_ARTIFACTS}/equipment.log" "mixed equipment control failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/opt_in/check_actor_equipment.py" "$PW_BIN" "$PW_TEST_ARTIFACTS"
test_step lifecycle "actor issuance, placement, omission, fresh access and termination dependency"
test_check_python "${PW_TEST_ARTIFACTS}/extensions.log" "BYOXPC extension workload failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_extensions.py" "$PW_BIN" "${PW_TEST_ARTIFACTS}/extensions" "${PW_TEST_ARTIFACTS}/session.json"
test_step directory "directory modification, exclusive creation and independent persistence"
test_check_python "${PW_TEST_ARTIFACTS}/directory.log" "BYOXPC directory workload failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_extension_directory.py" "$PW_BIN" "${PW_TEST_ARTIFACTS}/directory" "${PW_TEST_ARTIFACTS}/session.json"
test_step phases "ordinary phases preserve independent attempts and native query observations"
test_check_python "${PW_TEST_ARTIFACTS}/phases.log" "BYOXPC ordinary phases failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_phases.py" "$PW_BIN" "${PW_TEST_ARTIFACTS}/phases" "${PW_TEST_ARTIFACTS}/session.json"
test_step maximum "maximum ordinary, phased, fresh-file, actor and escaped-output replies"
test_check_python "${PW_TEST_ARTIFACTS}/maximum.log" "BYOXPC maximum replies failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_max_target_reply.py" "$PW_BIN" "${PW_TEST_ARTIFACTS}/maximum" "${PW_TEST_ARTIFACTS}/session.json"
test_step redelegation "principal re-delegation observations, successful calibration and narrow contrasts"
test_check_python "${PW_TEST_ARTIFACTS}/redelegation.log" "BYOXPC actor re-delegation failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_extension_redelegation.py" "$PW_BIN" "${PW_TEST_ARTIFACTS}/redelegation" "${PW_TEST_ARTIFACTS}/session.json"
test_step inherited "unapplied instrumented selected worker retains its signed App Sandbox restriction"
test_check_python "${PW_TEST_ARTIFACTS}/inherited.log" "actor inherited restriction control failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/opt_in/check_actor_inherited_restriction.py" "$PW_BIN" "$PW_TEST_ARTIFACTS" "$IDENTITY"
test_check_python "${PW_TEST_ARTIFACTS}/provenance.log" "BYOXPC equipment provenance failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_extension_provenance.py" "${PW_TEST_ARTIFACTS}"
test_step missing_equipment "hold only selected worker aside, retain actual refusal boundary, restore exact bytes"
test_check_python "${PW_TEST_ARTIFACTS}/missing-equipment.log" "missing equipment control failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/opt_in/check_missing_equipment.py" "$PW_BIN" "$PW_TEST_ARTIFACTS"
test_check_python "${PW_TEST_ARTIFACTS}/cleanup.log" "actor BYOXPC cleanup failed" \
  "$SESSION_TOOL" cleanup "$PW_BIN" "${PW_TEST_ARTIFACTS}/session.json"
trap - EXIT
test_pass "BYOXPC mixed equipment, lifecycle, directory, ordinary phases, maximal replies, re-delegation observations and inherited restriction pass with verified runner cleanup"
