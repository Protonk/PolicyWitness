#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="witness_contract"
PW_TEST_ID="bug_report_returns_verdicts"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "bug-report specimen produces sandbox_check verdicts in steps[]"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json, sys
from pathlib import Path
spec = {
    "schema_version": 1,
    "specimen_id": "witness_contract_verdicts",
    "policy": {"format": "sbpl", "sbpl_source": "(version 2)\n(deny default)\n(allow file-read-data)"},
    "probe_plan": [{
        "step_id": "fr1",
        "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "none", "value": ""}},
        "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"},
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
runner = env.get("data", {}).get("runner_result") or {}
steps = runner.get("steps") or []
if not steps:
    outcome = runner.get("normalized_outcome")
    raise SystemExit(
        f"PHASE 0 — steps[] is empty (outcome={outcome!r}); the worker dies under bare deny-default. "
        "Passes when Step 6 lands (C worker + validator-primary) or sooner via cross-check augmentation."
    )
sb = steps[0].get("sandbox_check") or {}
if sb.get("outcome") not in ("allow", "deny"):
    raise SystemExit(f"expected sandbox_check.outcome in (allow,deny), got {sb.get('outcome')!r}")
PY
ASSERT_RC=$?
set -e
if [[ "${ASSERT_RC}" -ne 0 ]]; then
  MSG="$(head -5 "${ASSERT_LOG}" | tr '\n' ' ' | sed 's/"/\\"/g')"
  test_fail "${MSG}" "{\"log\":\"${ASSERT_LOG}\"}"
fi

test_pass "bug-report specimen yields a verdict for the first probe" "{}"
