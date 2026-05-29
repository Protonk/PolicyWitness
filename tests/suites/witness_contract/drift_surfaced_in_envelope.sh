#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="witness_contract"
PW_TEST_ID="drift_surfaced_in_envelope"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "specimen where prediction disagrees with observation; expect steps[].drift=true"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

# Use the known BBX-001 anomaly: mach-lookup with a global-name in a
# (deny ...) rule. sandbox_check returns allow while the actual
# bootstrap_look_up returns the policy's denial. This is the canonical
# libsandbox-drift case we already document in the anomalies suite.
SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json, sys
from pathlib import Path
spec = {
    "schema_version": 1,
    "specimen_id": "witness_contract_drift",
    "policy": {
        "format": "sbpl",
        "sbpl_source": (
            "(version 1)\n"
            "(allow default)\n"
            "(deny mach-lookup (global-name \"com.apple.cfprefsd.xpc.daemon\"))\n"
        ),
    },
    "probe_plan": [{
        "step_id": "ml1",
        "sandbox_check": {
            "operation": "mach-lookup",
            "filter": {"kind": "global_name", "value": "com.apple.cfprefsd.xpc.daemon"},
        },
        "attempt": {
            "kind": "mach_lookup",
            "action": "bootstrap_look_up",
            "target": "com.apple.cfprefsd.xpc.daemon",
        },
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
    raise SystemExit(f"no steps observed; outcome={runner.get('normalized_outcome')!r}")
step = steps[0]
if "drift" not in step:
    raise SystemExit(
        "PHASE 0 — steps[0].drift field absent. "
        "Passes when R10 lands (the response schema bump that adds steps[].drift)."
    )
if step["drift"] is not True:
    sb_outcome = (step.get("sandbox_check") or {}).get("outcome")
    at_outcome = (step.get("attempt") or {}).get("outcome")
    raise SystemExit(
        f"expected drift=true for the BBX-001 mach-lookup anomaly "
        f"(sb_outcome={sb_outcome!r}, attempt_outcome={at_outcome!r})"
    )
PY
ASSERT_RC=$?
set -e
if [[ "${ASSERT_RC}" -ne 0 ]]; then
  MSG="$(head -5 "${ASSERT_LOG}" | tr '\n' ' ' | sed 's/"/\\"/g')"
  test_fail "${MSG}" "{\"log\":\"${ASSERT_LOG}\"}"
fi

test_pass "drift between verdict and attempt surfaced on a known anomaly" "{}"
