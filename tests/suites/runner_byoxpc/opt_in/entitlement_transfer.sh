#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_byoxpc entitlement_transfer
test_require_pw
SESSION_TOOL="${ROOT_DIR}/tests/fixtures/byoxpc/session.py"
# Two owned installations, each with its own session receipt and cleanup.
cleanup() {
  local status=$?
  trap - EXIT
  for copy in granted denied; do
    /usr/bin/python3 "${SESSION_TOOL}" cleanup "${PW_BIN}" "${PW_TEST_ARTIFACTS}/${copy}/session.json" || status=1
  done
  exit "$status"
}
trap cleanup EXIT
IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "$IDENTITY" ]] || test_fail "matching Developer ID required"
for copy in granted denied; do
  mkdir -p "${PW_TEST_ARTIFACTS}/${copy}"
  /usr/bin/python3 - "${PW_TEST_ARTIFACTS}/${copy}/supplied.plist" "${copy}" <<'PY'
import plistlib, sys
from pathlib import Path
Path(sys.argv[1]).write_bytes(plistlib.dumps({'com.apple.security.cs.allow-jit': sys.argv[2] == 'granted'}))
PY
  test_step "install_${copy}" "install an owned runner whose supplied plist sets the key ${copy/granted/true}"
  test_check_python "${PW_TEST_ARTIFACTS}/${copy}/setup.log" "owned BYOXPC setup (${copy}) failed" \
    "$SESSION_TOOL" install "$PW_BIN" "$PW_APP_DIR" "${PW_TEST_ARTIFACTS}/${copy}" "${PW_TEST_ARTIFACTS}/${copy}/runner_env.json" "$IDENTITY" "${PW_TEST_ARTIFACTS}/${copy}/supplied.plist"
done
test_step transfer "a selector requiring the key is admitted only by the worker that holds it true; the conditioned write's bytes are read independently"
test_check_python "${PW_TEST_ARTIFACTS}/transfer.log" "entitlement transfer failed" \
  "${ROOT_DIR}/tests/suites/runner_byoxpc/opt_in/entitlement_transfer.py" "$PW_BIN" "$PW_TEST_ARTIFACTS"
for copy in granted denied; do
  test_check_python "${PW_TEST_ARTIFACTS}/${copy}/cleanup.log" "BYOXPC cleanup (${copy}) failed" \
    "$SESSION_TOOL" cleanup "$PW_BIN" "${PW_TEST_ARTIFACTS}/${copy}/session.json"
done
trap - EXIT
test_pass "required_entitlements admits the true-valued worker and refuses the false-valued one by name; only the admitted worker completes the conditioned write; service removal verified"
