#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/case.sh"

PW_TEST_SUITE="runner_filter_iokit_user_client_class"
PW_TEST_ID="prediction_unavailable_attempt_observed"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "iokit-user-client-class probe — prediction unavailable, attempt observed"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json, sys
from pathlib import Path
spec = {
    "schema_version": 1,
    "specimen_id": "runner_filter_iokit_user_client_class",
    "policy": {
        "format": "sbpl",
        "sbpl_source": (
            "(version 1)\n"
            "(allow default)\n"
            "(deny iokit-open-user-client (iokit-user-client-class \"IOSurfaceRootUserClient\"))\n"
        ),
    },
    "probe_plan": [{
        "step_id": "iosurfaceroot_uc",
        "sandbox_check": {
            "operation": "iokit-open-user-client",
            "filter": {"kind": "iokit_user_client_class", "value": "IOSurfaceRootUserClient"},
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
  --step-id iosurfaceroot_uc --operation iokit-open-user-client --filter-value IOSurfaceRootUserClient --attempt file_open \
  --expected-schema-version 7

test_pass "iokit_user_client_class: prediction_unavailable surfaced; attempt observed" "{}"
