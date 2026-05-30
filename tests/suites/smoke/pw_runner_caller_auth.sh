#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="${PW_TEST_SUITE_OVERRIDE:-smoke}"
PW_TEST_ID="runner_caller_auth"

PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"
CLIENT_BIN="${PW_APP_DIR}/Contents/MacOS/pw-runner-client"
REQUEST_JSON="${ROOT_DIR}/tests/fixtures/pw_runner/specimen_file_read_deny.json"
RUNNER_STD_BUNDLE="${PW_APP_DIR}/Contents/XPCServices/PWRunner.xpc"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

if [[ ! -x "${CLIENT_BIN}" ]]; then
  test_fail "missing pw-runner-client at ${CLIENT_BIN}"
fi

if [[ ! -f "${REQUEST_JSON}" ]]; then
  test_fail "missing request fixture at ${REQUEST_JSON}"
fi

if ! require_runner_bundle "${RUNNER_STD_BUNDLE}"; then
  exit 0
fi

read_bundle_id() {
  local info_plist="$1"
  /usr/bin/plutil -extract CFBundleIdentifier raw -o - "${info_plist}" 2>/dev/null || true
}

STD_INFO_PLIST="${RUNNER_STD_BUNDLE}/Contents/Info.plist"
STD_SERVICE="$(read_bundle_id "${STD_INFO_PLIST}")"
if [[ -z "${STD_SERVICE}" ]]; then
  test_fail "failed to read CFBundleIdentifier from built-in runner Info.plist"
fi

run_client_expect_ok() {
  local service_name="$1"
  local tag="$2"
  local out_json="${PW_TEST_ARTIFACTS}/client.${tag}.stdout.json"
  local out_err="${PW_TEST_ARTIFACTS}/client.${tag}.stderr.txt"

  set +e
  "${CLIENT_BIN}" run --timeout-ms 2000 "${service_name}" "${REQUEST_JSON}" >"${out_json}" 2>"${out_err}"
  local rc=$?
  set -e

  if [[ ${rc} -ne 0 ]]; then
    test_fail "pw-runner-client failed (rc=${rc})" "{\"stdout\":\"${out_json}\",\"stderr\":\"${out_err}\"}"
  fi

  /usr/bin/python3 - "${out_json}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if payload.get("normalized_outcome") != "ok":
    raise SystemExit(f"expected normalized_outcome='ok' (got {payload.get('normalized_outcome')!r})")
PY
}

run_client_expect_denied() {
  local client_path="$1"
  local service_name="$2"
  local tag="$3"
  local out_json="${PW_TEST_ARTIFACTS}/client.${tag}.stdout.json"
  local out_err="${PW_TEST_ARTIFACTS}/client.${tag}.stderr.txt"

  set +e
  "${client_path}" run --timeout-ms 2000 "${service_name}" "${REQUEST_JSON}" >"${out_json}" 2>"${out_err}"
  local rc=$?
  set -e

  if [[ ${rc} -eq 0 ]]; then
    test_fail "unauthorized client unexpectedly succeeded" "{\"stdout\":\"${out_json}\",\"stderr\":\"${out_err}\"}"
  fi

  /usr/bin/python3 - "${out_json}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if payload.get("normalized_outcome") == "ok":
    raise SystemExit("expected non-ok normalized_outcome for unauthorized client")
PY
}

test_step "authorized_call" "authorized client can reach built-in runner"
run_client_expect_ok "${STD_SERVICE}" "std"

test_step "unauthorized_adhoc" "ad-hoc client is rejected by built-in runner"
BAD_CLIENT="${PW_TEST_ARTIFACTS}/pw-runner-client.adhoc"
cp "${CLIENT_BIN}" "${BAD_CLIENT}"
/usr/bin/codesign --force -s - "${BAD_CLIENT}" >/dev/null 2>&1 || test_fail "ad-hoc codesign failed"
run_client_expect_denied "${BAD_CLIENT}" "${STD_SERVICE}" "adhoc"

IDENTITY="$(/usr/bin/security find-identity -v -p codesigning | /usr/bin/awk -F'"' '/Developer ID Application:/{print $2; exit}')"
if [[ -z "${IDENTITY}" ]]; then
  test_log "skip allowlist mismatch check (no Developer ID identity found)"
  test_pass "caller auth checks ok" "{}"
  exit 0
fi

test_step "unauthorized_identifier" "same-team client with different identifier is rejected"
MISMATCH_CLIENT="${PW_TEST_ARTIFACTS}/pw-runner-client.mismatch"
cp "${CLIENT_BIN}" "${MISMATCH_CLIENT}"
/usr/bin/codesign --force -s "${IDENTITY}" --identifier "com.policywitness.test.notallowed" "${MISMATCH_CLIENT}" >/dev/null 2>&1 \
  || test_fail "codesign with mismatched identifier failed"
run_client_expect_denied "${MISMATCH_CLIENT}" "${STD_SERVICE}" "mismatch"

test_pass "caller auth checks ok" "{}"
