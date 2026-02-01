#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="${PW_TEST_SUITE_OVERRIDE:-smoke}"
PW_TEST_ID="specimen_instrumentation_execmem"

PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"
SPECIMEN_FIXTURE="${ROOT_DIR}/tests/fixtures/pw_runner/specimen_instrumentation_execmem.json"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "run specimen with execmem_probe instrumentation"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

if [[ ! -f "${SPECIMEN_FIXTURE}" ]]; then
  test_fail "specimen fixture missing: ${SPECIMEN_FIXTURE}"
fi

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
render_specimen_with_runner "${SPECIMEN_FIXTURE}" "${SPECIMEN_PATH}"

RUN_STDOUT="${PW_TEST_ARTIFACTS}/policy_witness.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/policy_witness.run.stderr.txt"

set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?
set -e

if [[ "${RC}" -ne 0 ]]; then
  test_fail "policy-witness run failed (rc=${RC})" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

/usr/bin/python3 - "${RUN_STDOUT}" <<'PY'
import json
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert env.get("kind") == "run"
assert env.get("result", {}).get("ok") is True

runner = env.get("data", {}).get("runner_result") or {}
inst = runner.get("instrumentation") or {}
ports = inst.get("ports") or []
if len(ports) != 1:
    raise SystemExit(f"expected 1 instrumentation port (got {len(ports)})")
port = ports[0]
if port.get("kind") != "execmem_probe":
    raise SystemExit(f"expected kind=execmem_probe (got {port.get('kind')!r})")
status = port.get("status")
probe = port.get("execmem_probe") or {}
if status == "ok":
    if probe.get("mmap_succeeded") is not True:
        raise SystemExit(f"expected mmap_succeeded=true (got {probe.get('mmap_succeeded')!r})")
elif status == "error":
    if probe.get("mmap_succeeded") is not False:
        raise SystemExit(f"expected mmap_succeeded=false (got {probe.get('mmap_succeeded')!r})")
    if probe.get("errno") is None:
        raise SystemExit("expected errno to be set on execmem failure")
    if not port.get("error"):
        raise SystemExit("expected error message on execmem failure")
else:
    raise SystemExit(f"unexpected status for execmem_probe: {status!r}")
PY

KIND_ERR="$(assert_runner_kind "${RUN_STDOUT}")" || test_fail "${KIND_ERR}" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"

test_pass "execmem_probe instrumentation ok" "{}"
