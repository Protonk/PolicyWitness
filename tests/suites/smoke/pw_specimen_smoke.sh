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

# Note: sandboxed automation harnesses can block XPC lookup.
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

ASSERT_LOG="${PW_TEST_ARTIFACTS}/assertions.log"
ASSERT_RC=0
"${PW_PYTHON}" -B -S -P - "${RUN_STDOUT}" "${ROOT_DIR}/tests/lib" "${PW_APP_DIR}/Contents/Info.plist" >"${ASSERT_LOG}" 2>&1 <<'PY' || ASSERT_RC=$?
import json
import plistlib
import sys
from pathlib import Path

# A failed expectation about the envelope is this case's reported failure: it
# prints the expectation and exits 3. Any other exit is not a product verdict.
def refuse(message):
    print(message, file=sys.stderr)
    raise SystemExit(3)

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if env.get("kind") != "run":
    refuse(f"expected kind=run (got {env.get('kind')!r})")
# The build stamp is a coordinate: it must name the bundle that produced it.
build = env.get("build") or {}
info = plistlib.loads(Path(sys.argv[3]).read_bytes())
for key in ("version", "number", "describe", "commit"):
    if not isinstance(build.get(key), str) or not build[key]:
        refuse(f"envelope build.{key} missing (got {build.get(key)!r})")
if build["version"] != info.get("CFBundleShortVersionString") or build["number"] != info.get("CFBundleVersion"):
    refuse(f"envelope build stamp {build!r} disagrees with the app Info.plist "
           f"{info.get('CFBundleShortVersionString')!r}/{info.get('CFBundleVersion')!r}")
if build["describe"] != info.get("PWBuildDescribe") or build["commit"] != info.get("PWBuildCommit"):
    refuse(f"envelope build describe/commit disagree with the app Info.plist: {build!r}")
if env.get("result", {}).get("ok") is not True:
    refuse(f"expected top-level ok=true (got {env.get('result')!r})")

runner = env.get("data", {}).get("runner_result") or {}
# Independently inspect the candidate, then compare every producer report.
sys.path.insert(0, sys.argv[2])
import contract
import build_context
import subprocess
expected = build_context.candidate_contract(Path(sys.argv[3]).parents[1])
version = json.loads(subprocess.check_output([str(Path(sys.argv[3]).parent / 'MacOS/policy-witness'), '--version']))
transport = (env.get("data", {}).get("runner_client") or {}).get("transport") or {}
reported = {
    "--version build.contract": (version.get("build") or {}).get("contract"),
    "envelope build.contract": build.get("contract"),
    "runner_client transport.contract": transport.get("contract"),
    "runner_result producer.contract": (runner.get("producer") or {}).get("contract"),
}
for name, value in reported.items():
    if value != expected:
        refuse(f"{name} is {value!r}; the candidate plist declares {expected!r}")
evidence = (runner.get("runner_subprocess") or {}).get("worker_evidence") or {}
if evidence.get("abi_identity") != contract.WORKER_IDENTITY:
    refuse(f"built app reports worker ABI {evidence.get('abi_identity')!r}; "
           f"generated source identity says {contract.WORKER_IDENTITY}")
steps = runner.get("steps") or []
if len(steps) != 1:
    refuse(f"expected 1 step (got {len(steps)})")
step = steps[0]
sb = step.get("sandbox_check") or {}
if sb.get("outcome") != "deny":
    refuse(f"expected sandbox_check.outcome=deny (got {sb.get('outcome')!r})")
# Witness the OBSERVED denial, not just the validator's predicted verdict — the
# prediction channel is exactly the one PolicyWitness exists to flag when it
# drifts from kernel reality. Under (deny file-read-data) the open_read of
# /etc/hosts must actually fail with an errno.
at = step.get("attempt") or {}
if at.get("rc") == 0:
    refuse(f"expected the open_read to be DENIED (rc!=0) under (deny file-read-data), got rc={at.get('rc')!r}")
if at.get("errno") is None:
    refuse(f"expected an errno on the denied read, got {at.get('errno')!r}")
PY
if [[ "${ASSERT_RC}" -eq 3 ]]; then
  cat "${ASSERT_LOG}" >&2 || true
  test_fail "run envelope expectation failed: $(head -n 1 "${ASSERT_LOG}") (log: ${ASSERT_LOG})" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\",\"assertions\":\"${ASSERT_LOG}\"}"
elif [[ "${ASSERT_RC}" -ne 0 ]]; then
  # An unexpected error in the block ends the script without a terminal report.
  cat "${ASSERT_LOG}" >&2 || true
  exit "${ASSERT_RC}"
fi

KIND_ERR="$(assert_runner_kind "${RUN_STDOUT}")" || test_fail "${KIND_ERR}" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"

test_pass "run smoke ok" "{}"
