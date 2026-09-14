#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/case.sh"

PW_TEST_SUITE="runner_filter_iokit_registry_entry_class"
PW_TEST_ID="prediction_unavailable_attempt_observed"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "iokit-registry-entry-class probe — prediction unavailable, attempt observed"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

# Default allow keeps the paired file attempt independent of the IOKit deny.
SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json, sys
from pathlib import Path
spec = {
    "schema_version": 1,
    "specimen_id": "runner_filter_iokit_registry_entry_class",
    "policy": {
        "format": "sbpl",
        "sbpl_source": (
            "(version 1)\n"
            "(allow default)\n"
            "(deny iokit-open-service (iokit-registry-entry-class \"IOSurfaceRoot\"))\n"
        ),
    },
    "probe_plan": [{
        "step_id": "iosurface_open",
        "sandbox_check": {
            "operation": "iokit-open-service",
            "filter": {"kind": "iokit_registry_entry_class", "value": "IOSurfaceRoot"},
        },
        # Supported file work populates the attempt slot; it does not witness IOKit enforcement.
        "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"},
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
  --step-id iosurface_open --operation iokit-open-service --attempt file_open

test_pass "prediction_unavailable surfaced; attempt observed" "{}"
