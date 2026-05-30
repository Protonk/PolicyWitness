#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="witness_contract"
PW_TEST_ID="debuggable_mode_rejected"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "request with runner.mode=debuggable — expect rejection"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json, sys
from pathlib import Path
spec = {
    "schema_version": 1,
    "specimen_id": "witness_contract_debuggable_rejected",
    "runner": {"mode": "debuggable"},
    "policy": {"format": "sbpl", "sbpl_source": "(version 1) (allow default)"},
    "probe_plan": [],
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
result = env.get("result") or {}
if result.get("ok") is True:
    raise SystemExit(
        "request with runner.mode=debuggable was accepted. "
        "`debuggable` is not a valid runner mode; specimens "
        "carrying it must fail at the controller's runner.mode "
        "parse step."
    )

# parse_runner_selector_value returns
# Err("invalid runner.mode value: debuggable"), which cmd_run wraps
# in a tool_error envelope before any runner is invoked.
outcome = result.get("normalized_outcome")
if outcome != "tool_error":
    raise SystemExit(
        f"expected normalized_outcome=tool_error from controller-side "
        f"parse rejection (got {outcome!r})"
    )
top_err = result.get("error") or ""
if "debuggable" not in top_err:
    raise SystemExit(
        f"expected error to name the rejected mode (got {top_err!r})"
    )
PY
ASSERT_RC=$?
set -e
if [[ "${ASSERT_RC}" -ne 0 ]]; then
  MSG="$(head -5 "${ASSERT_LOG}" | tr '\n' ' ' | sed 's/"/\\"/g')"
  test_fail "${MSG}" "{\"log\":\"${ASSERT_LOG}\"}"
fi

test_pass "runner.mode=debuggable is rejected" "{}"
