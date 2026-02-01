#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="${PW_TEST_SUITE_OVERRIDE:-runner_byoxpc}"
PW_TEST_ID="runner_auth_external"

PW_BIN="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"
REQUEST_JSON="${ROOT_DIR}/tests/fixtures/pw_runner/specimen_file_read_deny.json"
SRC_BUNDLE="${ROOT_DIR}/PolicyWitness.app/Contents/XPCServices/PWRunner.xpc"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "preflight" "install BYOXPC runner without caller auth keys"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

if ! require_runner_bundle "${SRC_BUNDLE}"; then
  exit 0
fi

if [[ ! -f "${REQUEST_JSON}" ]]; then
  test_fail "missing request fixture at ${REQUEST_JSON}"
fi

if ! has_gui_launchd_domain; then
  skip_runner_install_non_gui
  exit 0
fi

BUNDLE_COPY="${PW_TEST_ARTIFACTS}/PWRunner.noauth.xpc"
rm -rf "${BUNDLE_COPY}"
cp -R "${SRC_BUNDLE}" "${BUNDLE_COPY}"

INFO_PLIST="${BUNDLE_COPY}/Contents/Info.plist"
/usr/bin/python3 - "${INFO_PLIST}" <<'PY'
import plistlib
import sys
from pathlib import Path

path = Path(sys.argv[1])
plist = plistlib.load(path.open('rb'))
plist.pop("PWRunnerRequireSignedCaller", None)
plist.pop("PWRunnerAllowedIdentifiers", None)
plist["CFBundleIdentifier"] = "com.yourteam.policy-witness.PWRunnerNoAuth"
plistlib.dump(plist, path.open('wb'))
PY

/usr/bin/python3 - "${INFO_PLIST}" <<'PY'
import plistlib
import sys
from pathlib import Path

plist = plistlib.load(Path(sys.argv[1]).open('rb'))
if "PWRunnerRequireSignedCaller" in plist or "PWRunnerAllowedIdentifiers" in plist:
    raise SystemExit("auth keys still present in external runner Info.plist")
PY

/usr/bin/codesign --force -s - "${BUNDLE_COPY}" >/dev/null 2>&1 || test_fail "ad-hoc codesign failed"

INSTALL_STDOUT="${PW_TEST_ARTIFACTS}/runner_install.user.stdout.json"
INSTALL_STDERR="${PW_TEST_ARTIFACTS}/runner_install.user.stderr.txt"

set +e
"${PW_BIN}" runner install \
  --bundle "${BUNDLE_COPY}" \
  --kind byoxpc \
  --scope user \
  --allow-adhoc >"${INSTALL_STDOUT}" 2>"${INSTALL_STDERR}"
INSTALL_RC=$?
set -e

if [[ ${INSTALL_RC} -ne 0 ]]; then
  USER_ERR="$(cat "${INSTALL_STDERR}" 2>/dev/null || true)"
  if [[ "${USER_ERR}" == *"Domain does not support specified action"* || "${USER_ERR}" == *"Bootstrap failed: 125"* ]]; then
    skip_runner_install_non_gui "{\"stdout\":\"${INSTALL_STDOUT}\",\"stderr\":\"${INSTALL_STDERR}\"}"
    exit 0
  fi
  skip_runner_install_failed "{\"stdout\":\"${INSTALL_STDOUT}\",\"stderr\":\"${INSTALL_STDERR}\"}"
  exit 0
fi

read -r RUNNER_ID SERVICE_NAME < <(/usr/bin/python3 - "${INSTALL_STDOUT}" <<'PY'
import json
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
data = env.get("data") or {}
runner = data.get("runner") or {}
rid = runner.get("id") or ""
svc = runner.get("service_name") or ""
if not rid or not svc:
    raise SystemExit("missing runner id/service name from install output")
print(rid, svc)
PY
)
if [[ -z "${RUNNER_ID}" || -z "${SERVICE_NAME}" ]]; then
  test_fail "missing runner id/service name"
fi

cleanup() {
  "${PW_BIN}" runner remove --id "${RUNNER_ID}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

test_step "verify_runner" "verify external runner"
VERIFY_STDOUT="${PW_TEST_ARTIFACTS}/runner_verify.user.stdout.json"
VERIFY_STDERR="${PW_TEST_ARTIFACTS}/runner_verify.user.stderr.txt"

set +e
"${PW_BIN}" runner verify --service-name "${SERVICE_NAME}" >"${VERIFY_STDOUT}" 2>"${VERIFY_STDERR}"
VERIFY_RC=$?
set -e

set +e
/usr/bin/python3 - "${VERIFY_STDOUT}" <<'PY'
import json
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
result = env.get("result", {})
if result.get("ok") is True:
    raise SystemExit(0)
outcome = result.get("normalized_outcome") or ""
err = result.get("error") or ""
if outcome == "xpc_error" and ("Sandbox restriction" in err or "NSCocoaErrorDomain" in err):
    raise SystemExit(3)
raise SystemExit(f"expected result.ok=true (got {result.get('ok')!r})")
PY
PY_STATUS=$?
set -e

if [[ ${PY_STATUS} -eq 3 ]]; then
  skip_sandbox_restriction "{\"stdout\":\"${VERIFY_STDOUT}\",\"stderr\":\"${VERIFY_STDERR}\"}"
  exit 0
fi
if [[ ${PY_STATUS} -ne 0 || ${VERIFY_RC} -ne 0 ]]; then
  test_fail "runner verify failed" "{\"stdout\":\"${VERIFY_STDOUT}\",\"stderr\":\"${VERIFY_STDERR}\"}"
fi

test_pass "external runner installs without auth keys" "{}"
