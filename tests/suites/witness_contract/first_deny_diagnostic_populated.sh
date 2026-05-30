#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="witness_contract"
PW_TEST_ID="first_deny_diagnostic_populated"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "bare deny-default specimen; expect runner_sandbox_diagnostics.first_deny populated"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json, sys
from pathlib import Path
spec = {
    "schema_version": 1,
    "specimen_id": "witness_contract_first_deny",
    "policy": {"format": "sbpl", "sbpl_source": "(version 2)\n(deny default)\n(allow iokit-open-service (iokit-registry-entry-class \"IOHIDSystem\"))\n"},
    "probe_plan": [{
        "step_id": "p1",
        "sandbox_check": {"operation": "iokit-open-service", "filter": {"kind": "none", "value": ""}},
        "attempt": {"kind": "file", "action": "access", "target": "/tmp/x"},
    }],
}
Path(sys.argv[1]).write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/run.json"
set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" >"${RUN_STDOUT}" 2>/dev/null
set -e

ASSERT_LOG="${PW_TEST_ARTIFACTS}/assertions.log"
set +e
/usr/bin/python3 - "${RUN_STDOUT}" >"${ASSERT_LOG}" 2>&1 <<'PY'
import json, sys
from pathlib import Path
env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
data = env.get("data") or {}
diag = data.get("runner_sandbox_diagnostics")
if diag is None:
    raise SystemExit("data.runner_sandbox_diagnostics field absent")
first = diag.get("first_deny")
if first is None:
    capture = data.get("sandbox_log_capture") or {}
    raise SystemExit(
        f"first_deny is null; capture_status={capture.get('capture_status')!r}. "
        "May be a sandboxed-harness limitation if running under a restricted shell."
    )
if not isinstance(first.get("operation"), str) or not first["operation"]:
    raise SystemExit(f"expected first_deny.operation to be a non-empty string (got {first!r})")
PY
ASSERT_RC=$?
set -e
if [[ "${ASSERT_RC}" -ne 0 ]]; then
  MSG="$(head -5 "${ASSERT_LOG}" | tr '\n' ' ' | sed 's/"/\\"/g')"
  test_fail "${MSG}" "{\"log\":\"${ASSERT_LOG}\"}"
fi

test_pass "first_deny diagnostic populated from log capture" "{}"
