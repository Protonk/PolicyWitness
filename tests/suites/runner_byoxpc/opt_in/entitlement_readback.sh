#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_byoxpc entitlement_readback
test_require_pw
SESSION_TOOL="${ROOT_DIR}/tests/fixtures/byoxpc/session.py"
cleanup() {
  local status=$?
  trap - EXIT
  /usr/bin/python3 "${SESSION_TOOL}" cleanup "${PW_BIN}" "${PW_TEST_ARTIFACTS}/session.json" || status=1
  exit "$status"
}
trap cleanup EXIT
IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "$IDENTITY" ]] || test_fail "matching Developer ID required"
SUPPLIED="${PW_TEST_ARTIFACTS}/supplied.plist"
/usr/bin/python3 - "${SUPPLIED}" <<'PY'
import plistlib, sys
from pathlib import Path
Path(sys.argv[1]).write_bytes(plistlib.dumps({'com.apple.security.cs.allow-jit': True}))
PY
test_step install "install an owned runner with a supplied entitlements plist"
test_check_python "${PW_TEST_ARTIFACTS}/setup.log" "owned BYOXPC setup failed" \
  "$SESSION_TOOL" install "$PW_BIN" "$PW_APP_DIR" "$PW_TEST_ARTIFACTS" "${PW_TEST_ARTIFACTS}/runner_env.json" "$IDENTITY" "$SUPPLIED"
test_step readback "read the host's, the worker's and the validator's entitlements and signatures back from the installed copy and the registry"
test_check_python "${PW_TEST_ARTIFACTS}/readback.log" "entitlement read-back failed" \
  "${ROOT_DIR}/tests/suites/runner_byoxpc/opt_in/entitlement_readback.py" "$PW_BIN" "$PW_TEST_ARTIFACTS" "$SUPPLIED"
test_check_python "${PW_TEST_ARTIFACTS}/cleanup.log" "BYOXPC cleanup failed" \
  "$SESSION_TOOL" cleanup "$PW_BIN" "${PW_TEST_ARTIFACTS}/session.json"
trap - EXIT
test_pass "the installed worker holds the supplied entitlements; the registry records every binary's read-back; service removal verified"
