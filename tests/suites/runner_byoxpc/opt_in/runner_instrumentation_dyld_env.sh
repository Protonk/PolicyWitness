#!/usr/bin/env bash
# Opt-in test for external runner env injection + dyld_env port.
#
# Purpose:
# - Install an external runner with DYLD_* env vars and verify dyld_env reports them.
#
# Opt-in reason:
# - Requires launchd service install/bootstrapping and an unsandboxed caller.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="${PW_TEST_SUITE_OVERRIDE:-runner_byoxpc}"
PW_TEST_ID="runner_instrumentation_dyld_env"

PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"
RUNNER_BUNDLE_SRC="${PW_APP_DIR}/Contents/XPCServices/PWRunner.xpc"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "preflight" "check runner bundle and toolchain"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

if ! require_runner_bundle "${RUNNER_BUNDLE_SRC}"; then
  exit 0
fi

CLANG_PATH="$(require_clang)" || exit 0
SDKROOT="$(require_macos_sdk)" || exit 0

test_step "build_dylib" "compile no-op dylib for DYLD_INSERT_LIBRARIES"

SRC_PATH="${PW_TEST_ARTIFACTS}/dyld_env.c"
DYLIB_PATH="${PW_TEST_ARTIFACTS}/libpw_dyld_env.dylib"
BUILD_LOG="${PW_TEST_ARTIFACTS}/clang_build.log"

/usr/bin/python3 - "${SRC_PATH}" <<'PY'
import sys

src_path = sys.argv[1]
code = """int pw_dummy(void) {
    return 0;
}
"""
with open(src_path, "w", encoding="utf-8") as fh:
    fh.write(code)
PY

set +e
"${CLANG_PATH}" -isysroot "${SDKROOT}" -dynamiclib -o "${DYLIB_PATH}" "${SRC_PATH}" >"${BUILD_LOG}" 2>&1
CLANG_RC=$?
set -e
if [[ ${CLANG_RC} -ne 0 ]]; then
  test_fail "clang failed to build dylib" "{\"log_path\":\"${BUILD_LOG}\"}"
fi

test_step "prep_bundle" "prepare runner bundle with DYLD entitlements"

RUNNER_BUNDLE="${PW_TEST_ARTIFACTS}/PWRunner.dyld_env.xpc"
rm -rf "${RUNNER_BUNDLE}"
cp -R "${RUNNER_BUNDLE_SRC}" "${RUNNER_BUNDLE}"

INFO_PLIST="${RUNNER_BUNDLE}/Contents/Info.plist"
if [[ ! -f "${INFO_PLIST}" ]]; then
  test_fail "missing Info.plist in runner bundle copy"
fi

/usr/bin/python3 - "${INFO_PLIST}" <<'PY'
import plistlib
import sys
from pathlib import Path

path = Path(sys.argv[1])
plist = plistlib.load(path.open('rb'))
plist.pop("PWRunnerRequireSignedCaller", None)
plist.pop("PWRunnerAllowedIdentifiers", None)
plist["CFBundleIdentifier"] = "com.yourteam.policy-witness.PWRunnerDyldEnv"
plistlib.dump(plist, path.open('wb'))
PY

BUNDLE_ID="$(/usr/bin/plutil -extract CFBundleIdentifier raw -o - "${INFO_PLIST}" 2>/dev/null || true)"
if [[ -z "${BUNDLE_ID}" ]]; then
  test_fail "failed to read CFBundleIdentifier from ${INFO_PLIST}"
fi
cleanup_runner_service "${PW_BIN}" "${BUNDLE_ID}" "user"

ENTITLEMENTS_PLIST="${PW_TEST_ARTIFACTS}/dyld_env.entitlements.plist"
cat > "${ENTITLEMENTS_PLIST}" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>com.apple.security.cs.allow-dyld-environment-variables</key>
  <true/>
</dict>
</plist>
PLIST

/usr/bin/codesign --force --options runtime --entitlements "${ENTITLEMENTS_PLIST}" -s - "${RUNNER_BUNDLE}" >/dev/null 2>&1 \
  || test_fail "ad-hoc codesign with dyld env entitlements failed"

test_step "install_runner" "install external runner with DYLD_INSERT_LIBRARIES"

INSTALL_STDOUT="${PW_TEST_ARTIFACTS}/runner_install.user.stdout.json"
INSTALL_STDERR="${PW_TEST_ARTIFACTS}/runner_install.user.stderr.txt"

set +e
"${PW_BIN}" runner install \
  --bundle "${RUNNER_BUNDLE}" \
  --kind byoxpc \
  --scope user \
  --allow-adhoc \
  --env "DYLD_INSERT_LIBRARIES=${DYLIB_PATH}" >"${INSTALL_STDOUT}" 2>"${INSTALL_STDERR}"
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

cleanup() {
  if [[ -n "${RUNNER_ID:-}" ]]; then
    "${PW_BIN}" runner remove --id "${RUNNER_ID}" >/dev/null 2>&1 || true
  fi
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

RUNNER_PID="$(
  /usr/bin/python3 - "${VERIFY_STDOUT}" <<'PY'
import json
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
pid = env.get("data", {}).get("runner_pid")
if pid is None:
    sys.exit(0)
print(pid)
PY
)"

if [[ -n "${RUNNER_PID}" ]]; then
  for _ in $(/usr/bin/seq 1 40); do
    if ! /bin/ps -p "${RUNNER_PID}" >/dev/null 2>&1; then
      break
    fi
    /bin/sleep 0.05
  done
  if /bin/ps -p "${RUNNER_PID}" >/dev/null 2>&1; then
    /bin/launchctl kickstart -k "gui/$(/usr/bin/id -u)/${SERVICE_NAME}" >/dev/null 2>&1 || true
    /bin/sleep 0.05
  fi
fi

test_step "run" "run specimen against external runner with dyld_env"

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
INSTRUMENTATION_JSON="${PW_TEST_ARTIFACTS}/instrumentation.json"

/usr/bin/python3 - "${SPECIMEN_PATH}" "${SERVICE_NAME}" <<'PY'
import json
import sys

path, service = sys.argv[1:3]
spec = {
    "schema_version": 1,
    "specimen_id": "instrumentation_dyld_env",
    "runner": {"service": service, "mode": "byoxpc"},
    "policy": {
        "format": "sbpl",
        "sbpl_source": "(version 1) (allow default)"
    },
    "probe_plan": [],
}
with open(path, "w", encoding="utf-8") as fh:
    json.dump(spec, fh, indent=2, sort_keys=True)
PY

/usr/bin/python3 - "${INSTRUMENTATION_JSON}" "${DYLIB_PATH}" <<'PY'
import json
import sys

path, dylib = sys.argv[1:3]
payload = {
    "version": 1,
    "ports": [
        {"kind": "dyld_env", "expected": {"DYLD_INSERT_LIBRARIES": dylib}}
    ],
}
with open(path, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, indent=2, sort_keys=True)
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/policy_witness.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/policy_witness.run.stderr.txt"

set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" --instrumentation "${INSTRUMENTATION_JSON}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?

/usr/bin/python3 - "${RUN_STDOUT}" <<'PY'
import json
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if env.get("kind") != "run":
    raise SystemExit(f"expected kind=run (got {env.get('kind')!r})")

result = env.get("result", {})
if result.get("ok") is not True:
    outcome = result.get("normalized_outcome") or ""
    err = result.get("error") or ""
    if outcome == "xpc_error" and ("Sandbox restriction" in err or "NSCocoaErrorDomain" in err):
        print("SKIP: xpc error (sandbox restriction)", file=sys.stderr)
        raise SystemExit(3)
    raise SystemExit(f"expected result.ok=true (got {result.get('ok')!r})")

runner = env.get("data", {}).get("runner_result") or {}
inst = runner.get("instrumentation") or {}
ports = inst.get("ports") or []
if len(ports) != 1:
    raise SystemExit(f"expected 1 instrumentation port (got {len(ports)})")
port = ports[0]
if port.get("kind") != "dyld_env":
    raise SystemExit(f"expected kind=dyld_env (got {port.get('kind')!r})")
if port.get("status") != "ok":
    raise SystemExit(f"expected status=ok (got {port.get('status')!r})")
dyld = port.get("dyld_env") or {}
present = set(dyld.get("keys_present") or [])
if "DYLD_INSERT_LIBRARIES" not in present:
    raise SystemExit("expected DYLD_INSERT_LIBRARIES in keys_present")
kind = (env.get("data", {}) or {}).get("runner_provenance", {}).get("runner_kind")
if kind != "byoxpc":
    raise SystemExit(f"expected runner_kind=byoxpc (got {kind!r})")
PY
PY_STATUS=$?
set -e

if [[ ${PY_STATUS} -eq 3 ]]; then
  skip_sandbox_restriction "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
  exit 0
fi
if [[ ${PY_STATUS} -ne 0 || ${RC} -ne 0 ]]; then
  test_fail "dyld_env instrumentation did not meet expectations" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

test_pass "dyld_env instrumentation ok" "{}"
