#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="${PW_TEST_SUITE_OVERRIDE:-runner_byoxpc}"
PW_TEST_ID="runner_install"

PW_BIN="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"
RUNNER_BUNDLE="${ROOT_DIR}/PolicyWitness.app/Contents/XPCServices/PWRunner.xpc"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "preflight" "install BYOXPC runner"

ENV_PATH_DEFAULT="${PW_TEST_ARTIFACTS}/runner_env.json"
RUNNER_ENV_PATH="${PW_TEST_RUNNER_ENV_PATH:-${ENV_PATH_DEFAULT}}"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

if ! require_runner_bundle "${RUNNER_BUNDLE}"; then
  exit 0
fi

INFO_PLIST="${RUNNER_BUNDLE}/Contents/Info.plist"
BUNDLE_ID="$(/usr/bin/plutil -extract CFBundleIdentifier raw -o - "${INFO_PLIST}" 2>/dev/null || true)"
if [[ -z "${BUNDLE_ID}" ]]; then
  test_fail "failed to read CFBundleIdentifier from ${INFO_PLIST}"
fi
cleanup_runner_service "${PW_BIN}" "${BUNDLE_ID}" "user"

INSTALL_STDOUT="${PW_TEST_ARTIFACTS}/runner_install.user.stdout.json"
INSTALL_STDERR="${PW_TEST_ARTIFACTS}/runner_install.user.stderr.txt"

set +e
"${PW_BIN}" runner install \
  --bundle "${RUNNER_BUNDLE}" \
  --kind byoxpc \
  --scope user \
  --allow-adhoc >"${INSTALL_STDOUT}" 2>"${INSTALL_STDERR}"
INSTALL_RC=$?
set -e

if [[ ${INSTALL_RC} -ne 0 ]]; then
  USER_ERR="$(cat "${INSTALL_STDERR}" 2>/dev/null || true)"
  if [[ "${USER_ERR}" == *"Domain does not support specified action"* || "${USER_ERR}" == *"Bootstrap failed: 125"* ]]; then
    if ! has_gui_launchd_domain; then
      skip_runner_install_non_gui "{\"stdout\":\"${INSTALL_STDOUT}\",\"stderr\":\"${INSTALL_STDERR}\"}"
      exit 0
    fi
    test_fail "runner install failed: ${USER_ERR}" "{\"stdout\":\"${INSTALL_STDOUT}\",\"stderr\":\"${INSTALL_STDERR}\"}"
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

VERIFY_STDOUT="${PW_TEST_ARTIFACTS}/runner_verify.user.stdout.json"
VERIFY_STDERR="${PW_TEST_ARTIFACTS}/runner_verify.user.stderr.txt"

set +e
"${PW_BIN}" runner verify --service-name "${SERVICE_NAME}" >"${VERIFY_STDOUT}" 2>"${VERIFY_STDERR}"
VERIFY_RC=$?
set -e

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

if [[ ${PY_STATUS} -eq 3 ]]; then
  skip_sandbox_restriction "{\"stdout\":\"${VERIFY_STDOUT}\",\"stderr\":\"${VERIFY_STDERR}\"}"
  exit 0
fi
if [[ ${PY_STATUS} -ne 0 || ${VERIFY_RC} -ne 0 ]]; then
  test_fail "runner verify failed" "{\"stdout\":\"${VERIFY_STDOUT}\",\"stderr\":\"${VERIFY_STDERR}\"}"
fi

/usr/bin/python3 - "${RUNNER_ENV_PATH}" "${RUNNER_ID}" "${SERVICE_NAME}" <<'PY'
import json
import sys
from pathlib import Path

out_path, rid, svc = sys.argv[1:4]
payload = {"runner_id": rid, "service_name": svc}
Path(out_path).parent.mkdir(parents=True, exist_ok=True)
Path(out_path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
PY

test_pass "byoxpc runner installed" "{\"runner_env\":\"${RUNNER_ENV_PATH}\"}"
