#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="${PW_TEST_SUITE_OVERRIDE:-smoke}"
PW_TEST_ID="specimen_file_read_deny"

PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"
SPECIMEN_FIXTURE="${ROOT_DIR}/tests/fixtures/pw_runner/specimen_file_read_deny.json"

test_selected "${PW_TEST_ID}" || exit 0
test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "run request via policy-witness"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

if [[ ! -f "${SPECIMEN_FIXTURE}" ]]; then
  test_fail "specimen fixture missing: ${SPECIMEN_FIXTURE}"
fi

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
render_specimen_with_runner "${SPECIMEN_FIXTURE}" "${SPECIMEN_PATH}"

# Note: sandboxed automation harnesses can block XPC lookup or unified log access.
# If this test fails with those symptoms, rerun from a normal Terminal.

RUN_STDOUT="${PW_TEST_ARTIFACTS}/policy_witness.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/policy_witness.run.stderr.txt"

set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?
set -e

if [[ "${RC}" -ne 0 ]]; then
  test_fail "policy-witness run failed (rc=${RC})" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

/usr/bin/python3 - "${RUN_STDOUT}" "${ROOT_DIR}/tests/lib" "${PW_APP_DIR}/Contents/Info.plist" <<'PY'
import json
import plistlib
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert env.get("kind") == "run"
# The build stamp is a coordinate: it must name the bundle that produced it.
build = env.get("build") or {}
info = plistlib.loads(Path(sys.argv[3]).read_bytes())
for key in ("version", "number", "describe", "commit"):
    if not isinstance(build.get(key), str) or not build[key]:
        raise SystemExit(f"envelope build.{key} missing (got {build.get(key)!r})")
if build["version"] != info.get("CFBundleShortVersionString") or build["number"] != info.get("CFBundleVersion"):
    raise SystemExit(f"envelope build stamp {build!r} disagrees with the app Info.plist "
                     f"{info.get('CFBundleShortVersionString')!r}/{info.get('CFBundleVersion')!r}")
if build["describe"] != info.get("PWBuildDescribe") or build["commit"] != info.get("PWBuildCommit"):
    raise SystemExit(f"envelope build describe/commit disagree with the app Info.plist: {build!r}")
assert env.get("result", {}).get("ok") is True

runner = env.get("data", {}).get("runner_result") or {}
# The one exact contract check: a built app must report the numbers in
# docs/contract.json. Every other suite asserts the minimum it depends on.
sys.path.insert(0, sys.argv[2])
import contract
if runner.get("schema_version") != contract.RESPONSE_SCHEMA:
    raise SystemExit(f"built app reports response schema {runner.get('schema_version')!r}; "
                     f"docs/contract.json says {contract.RESPONSE_SCHEMA}")
evidence = (runner.get("runner_subprocess") or {}).get("worker_evidence") or {}
if evidence.get("abi_version") != contract.WORKER_ABI:
    raise SystemExit(f"built app reports worker ABI {evidence.get('abi_version')!r}; "
                     f"docs/contract.json says {contract.WORKER_ABI}")
steps = runner.get("steps") or []
if len(steps) != 1:
    raise SystemExit(f"expected 1 step (got {len(steps)})")
step = steps[0]
sb = step.get("sandbox_check") or {}
if sb.get("outcome") != "deny":
    raise SystemExit(f"expected sandbox_check.outcome=deny (got {sb.get('outcome')!r})")
# Witness the OBSERVED denial, not just the validator's predicted verdict — the
# prediction channel is exactly the one PolicyWitness exists to flag when it
# drifts from kernel reality. Under (deny file-read-data) the open_read of
# /etc/hosts must actually fail with an errno.
at = step.get("attempt") or {}
if at.get("rc") == 0:
    raise SystemExit(f"expected the open_read to be DENIED (rc!=0) under (deny file-read-data), got rc={at.get('rc')!r}")
if at.get("syscall_errno") is None:
    raise SystemExit(f"expected a syscall_errno on the denied read, got {at.get('syscall_errno')!r}")
PY

KIND_ERR="$(assert_runner_kind "${RUN_STDOUT}")" || test_fail "${KIND_ERR}" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"

test_pass "run smoke ok" "{}"
