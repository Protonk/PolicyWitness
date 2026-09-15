#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/case.sh"

PW_TEST_SUITE="runner_filter_sysctl_name"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

# Exercise all three caller contracts without needing the app.
test_begin "${PW_TEST_SUITE}" checker_controls
test_step checker "unavailable predictions must retain step identity and attempt checks"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "filter checker controls failed" \
  "${ROOT_DIR}/tests/suites/runner_filter_sysctl_name/checker_controls.py" "${PW_TEST_ARTIFACTS}"
test_pass "all three filter adapters accept valid evidence and reject broken channels"

test_begin "${PW_TEST_SUITE}" prediction_unavailable_attempt_observed
test_step "run" "sysctl-name probe — prediction unavailable, attempt observed"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json, sys
from pathlib import Path
spec = {
    "schema_version": 1,
    "specimen_id": "runner_filter_sysctl_name",
    "policy": {
        "format": "sbpl",
        "sbpl_source": (
            "(version 1)\n"
            "(allow default)\n"
            "(deny sysctl-read (sysctl-name \"kern.osrelease\"))\n"
        ),
    },
    "probe_plan": [{
        "step_id": "kern_osrelease",
        "sandbox_check": {
            "operation": "sysctl-read",
            "filter": {"kind": "sysctl_name", "value": "kern.osrelease"},
        },
        "attempt": {"kind": "sysctl", "action": "read", "target": "kern.osrelease"},
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
  --step-id kern_osrelease --operation sysctl-read --filter-value kern.osrelease --attempt sysctl_denied

test_pass "sysctl_name: prediction_unavailable surfaced; sysctl attempt observed" "{}"
