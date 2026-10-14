#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/case.sh"

PW_TEST_SUITE="runner_filter_local_name"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

if test_selected prediction_unavailable_attempt_observed; then
test_begin "${PW_TEST_SUITE}" prediction_unavailable_attempt_observed
test_step "run" "local-name probe — prediction unavailable, the lookup the rule names still completes"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

# The policy denies the lookup by local-name. On the verified host that rule
# governs no lookup the worker can perform, so the real bootstrap_look_up of
# this launchd service completes while the host plans no prediction for it.
SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json, sys
from pathlib import Path
spec = {
    "schema_version": 4,
    "specimen_id": "runner_filter_local_name",
    "policy": {
        "format": "sbpl",
        "sbpl_source": (
            "(version 1)\n"
            "(allow default)\n"
            "(deny mach-lookup (local-name \"com.apple.logd\"))\n"
        ),
    },
    "probe_plan": [{
        "step_id": "logd_local",
        "sandbox_check": {
            "operation": "mach-lookup",
            "filter": {"kind": "local_name", "value": "com.apple.logd"},
        },
        "attempt": {"kind": "mach_lookup", "action": "bootstrap_look_up", "target": "com.apple.logd"},
    }],
}
Path(sys.argv[1]).write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/run.json"
set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" >"${RUN_STDOUT}" 2>"${PW_TEST_ARTIFACTS}/pw.stderr"
RC=$?
set -e

if [[ "${RC}" -ne 0 ]]; then
  test_fail "specimen should succeed (rc=${RC})" "{\"stdout\":\"${RUN_STDOUT}\"}"
fi

test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "filter prediction/attempt contract failed" \
  "${ROOT_DIR}/tests/lib/unavailable_prediction.py" "${RUN_STDOUT}" \
  --step-id logd_local --operation mach-lookup --filter-value com.apple.logd --attempt mach_lookup_allowed

test_pass "local_name: prediction_unavailable surfaced; the named lookup completed" "{}"
fi
