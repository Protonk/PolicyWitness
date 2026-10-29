#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract extensions_byoxpc
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
"${PW_PYTHON}" -B -S -P - "$SUPPLIED" <<'PY'
import plistlib, sys
from pathlib import Path
Path(sys.argv[1]).write_bytes(plistlib.dumps({'com.apple.security.cs.allow-jit': True}))
PY
test_step install "install an owned runner; read back issuer and worker authority independently"
test_check_python "${PW_TEST_ARTIFACTS}/setup.log" "extension BYOXPC setup failed" \
  "$SESSION_TOOL" install "$PW_BIN" "$PW_APP_DIR" "$PW_TEST_ARTIFACTS" "${PW_TEST_ARTIFACTS}/runner_env.json" "$IDENTITY" "$SUPPLIED"
export PW_RUNNER_REGISTRY="$("${PW_PYTHON}" -B -S -P -c 'import json,sys; print(json.load(open(sys.argv[1]))["PW_RUNNER_REGISTRY"])' "${PW_TEST_ARTIFACTS}/runner_env.json")"
test_check_python "${PW_TEST_ARTIFACTS}/readback.log" "extension issuer read-back failed" \
  "${ROOT_DIR}/tests/suites/runner_byoxpc/opt_in/entitlement_readback.py" "$PW_BIN" "$PW_TEST_ARTIFACTS" "$SUPPLIED"
test_step lifecycle "repeat native lifecycle, placement, omission and target preparation through BYOXPC"
test_check_python "${PW_TEST_ARTIFACTS}/extensions.log" "BYOXPC extension workload failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_extensions.py" "$PW_BIN" "${PW_TEST_ARTIFACTS}/extensions" "${PW_TEST_ARTIFACTS}/session.json"
test_step directory "repeat directory modification, exclusive creation and independent persistence through BYOXPC"
test_check_python "${PW_TEST_ARTIFACTS}/directory.log" "BYOXPC directory extension workload failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_extension_directory.py" "$PW_BIN" "${PW_TEST_ARTIFACTS}/directory" "${PW_TEST_ARTIFACTS}/session.json"
test_step phases "repeat independent unlink, fresh unavailable planning and later native query through BYOXPC"
test_check_python "${PW_TEST_ARTIFACTS}/phases.log" "BYOXPC ordinary phases failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_phases.py" "$PW_BIN" "${PW_TEST_ARTIFACTS}/phases" "${PW_TEST_ARTIFACTS}/session.json"
test_step maximum "exercise maximum ordinary, phased, fresh-read/write, lifecycle and escaped-output replies through BYOXPC"
test_check_python "${PW_TEST_ARTIFACTS}/maximum.log" "BYOXPC maximum replies failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_max_target_reply.py" "$PW_BIN" "${PW_TEST_ARTIFACTS}/maximum" "${PW_TEST_ARTIFACTS}/session.json"
test_check_python "${PW_TEST_ARTIFACTS}/provenance.log" "BYOXPC extension provenance failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_extension_provenance.py" "${PW_TEST_ARTIFACTS}"
test_step missing_issuer "remove only the owned installed issuer, observe refusal and validation, then restore exact bytes"
test_check_python "${PW_TEST_ARTIFACTS}/missing-issuer.log" "live missing issuer control failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_missing_issuer.py" "$PW_BIN" "${PW_TEST_ARTIFACTS}"
test_check_python "${PW_TEST_ARTIFACTS}/cleanup.log" "BYOXPC extension cleanup failed" \
  "$SESSION_TOOL" cleanup "$PW_BIN" "${PW_TEST_ARTIFACTS}/session.json"
trap - EXIT
test_pass "BYOXPC native lifecycle and ordinary phase controls pass with separate issuer authority and verified cleanup"
