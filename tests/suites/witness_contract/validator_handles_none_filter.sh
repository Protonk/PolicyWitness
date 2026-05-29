#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="witness_contract"
PW_TEST_ID="validator_handles_none_filter"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "bug-report v2 specimen with --sonoma-cross-check; expect filter.kind=none to return a verdict"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json, sys
from pathlib import Path
spec = {
    "schema_version": 1,
    "specimen_id": "witness_contract_none_filter",
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
"${PW_BIN}" run "${SPECIMEN_PATH}" --sonoma-cross-check >"${RUN_STDOUT}" 2>/dev/null
set -e

ASSERT_LOG="${PW_TEST_ARTIFACTS}/assertions.log"
set +e
/usr/bin/python3 - "${RUN_STDOUT}" >"${ASSERT_LOG}" 2>&1 <<'PY'
import json, sys
from pathlib import Path
env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
cross = env.get("data", {}).get("sonoma_cross_check") or {}
steps = cross.get("steps") or []
if not steps:
    raise SystemExit("PHASE 0 — no sonoma_cross_check.steps present at all (passes when R1 lands)")
step = steps[0]
status = step.get("status")
err = step.get("error") or ""
if status == "skipped" and "filter.kind=none" in err:
    raise SystemExit("PHASE 0 — validator skipped NONE filter (passes when R1 lands)")
if status != "ok":
    raise SystemExit(f"expected step status=ok (got {status!r}, error={err!r})")
verdict = step.get("validator_outcome")
if verdict not in ("allow", "deny"):
    raise SystemExit(f"expected validator_outcome allow|deny (got {verdict!r})")
PY
ASSERT_RC=$?
set -e
if [[ "${ASSERT_RC}" -ne 0 ]]; then
  MSG="$(head -5 "${ASSERT_LOG}" | tr '\n' ' ' | sed 's/"/\\"/g')"
  test_fail "${MSG}" "{\"log\":\"${ASSERT_LOG}\"}"
fi

test_pass "NONE filter cross-check returns a verdict" "{}"
