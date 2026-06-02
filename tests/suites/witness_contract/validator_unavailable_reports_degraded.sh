#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="witness_contract"
PW_TEST_ID="validator_unavailable_reports_degraded"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "_test_overrides.validator_executable_path → stub emitting too few verdicts; expect validator_unavailable with attempts preserved"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

# Stub validator: drain the probes, emit exactly ONE valid NDJSON verdict,
# then clean-exit. The specimen carries TWO predictable probes, so the host
# sees a clean exit with verdicts.count (1) < expectedVerdictCount (2) and
# classifies validator_unavailable — "PW ran in attempts-only degradation
# mode" for the missing tail.
STUB="${PW_TEST_ARTIFACTS}/validator_unavailable_stub.sh"
cat >"${STUB}" <<'STUBEOF'
#!/bin/sh
cat >/dev/null
printf '{"step_id":"fr1","operation":"file-read-data","filter_type":"PATH","filter_value":"/etc/hosts","outcome":"allow","rc":0,"errno":0}\n'
exit 0
STUBEOF
chmod +x "${STUB}"

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
PW_STUB_PATH="${STUB}" /usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json, os, sys
from pathlib import Path
# Two predictable (path-filter) probes → expectedVerdictCount == 2.
plan = [{
    "step_id": f"fr{i+1}",
    "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/etc/hosts"}},
    "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"},
} for i in range(2)]
spec = {
    "schema_version": 1,
    "specimen_id": "witness_contract_validator_unavailable",
    "policy": {"format": "sbpl", "sbpl_source": "(version 1) (allow default)"},
    "probe_plan": plan,
    "_test_overrides": {
        "validator_executable_path": os.environ["PW_STUB_PATH"],
    },
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
outcome = runner.get("normalized_outcome")
err = runner.get("error") or ""

if outcome == "bad_request" and "validator_executable_path" in err:
    raise SystemExit(
        "_test_overrides.validator_executable_path was rejected as an "
        "unrecognized field; it should route through ValidatorClient."
    )
if outcome != "validator_unavailable":
    raise SystemExit(
        f"expected normalized_outcome=validator_unavailable (got {outcome!r}); "
        f"the stub emitted 1 of 2 expected verdicts on a clean exit."
    )
# The error should name the shortfall so a consumer can see how degraded.
if "expected 2" not in err:
    raise SystemExit(f"expected error to report the verdict shortfall (got {err!r})")

# Degradation property: attempts for BOTH steps are still observed.
steps = runner.get("steps") or []
if len(steps) != 2:
    raise SystemExit(f"expected 2 attempts preserved despite the validator shortfall (got {len(steps)})")
for s in steps:
    at = s.get("attempt") or {}
    if not isinstance(at.get("rc"), int):
        raise SystemExit(f"expected attempt.rc populated for {s.get('step_id')!r} (got {at!r})")
PY
ASSERT_RC=$?
set -e
if [[ "${ASSERT_RC}" -ne 0 ]]; then
  MSG="$(head -5 "${ASSERT_LOG}" | tr '\n' ' ' | sed 's/"/\\"/g')"
  test_fail "${MSG}" "{\"log\":\"${ASSERT_LOG}\"}"
fi

test_pass "validator_unavailable surfaces with both attempts preserved" "{}"
