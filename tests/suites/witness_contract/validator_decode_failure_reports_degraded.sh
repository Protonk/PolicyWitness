#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="witness_contract"
PW_TEST_ID="validator_decode_failure_reports_degraded"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "_test_overrides.validator_executable_path → stub emitting non-NDJSON; expect validator_decode_failure with attempts preserved"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

# Stub validator: drain the probes off stdin (so the host's probe write
# completes cleanly — a write failure would classify as no_reply instead),
# then emit a line that is NOT valid NDJSON and exit 0. The host parses the
# stream, hits verdictParseFailed, and classifies validator_decode_failure.
STUB="${PW_TEST_ARTIFACTS}/validator_decode_stub.sh"
cat >"${STUB}" <<'STUBEOF'
#!/bin/sh
cat >/dev/null
printf 'this is not ndjson at all\n'
exit 0
STUBEOF
chmod +x "${STUB}"

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
PW_STUB_PATH="${STUB}" /usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json, os, sys
from pathlib import Path
spec = {
    "schema_version": 1,
    "specimen_id": "witness_contract_validator_decode_failure",
    "policy": {"format": "sbpl", "sbpl_source": "(version 1) (allow default)"},
    "probe_plan": [{
        "step_id": "fr1",
        "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/etc/hosts"}},
        "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"},
    }],
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
if outcome != "validator_decode_failure":
    raise SystemExit(
        f"expected normalized_outcome=validator_decode_failure (got {outcome!r}); "
        f"the stub emitted non-NDJSON, so the host should hit verdictParseFailed."
    )

# Degradation property: attempts are still observed even though the
# validator's verdicts were unparseable.
steps = runner.get("steps") or []
if not steps:
    raise SystemExit("expected attempts to be present even when the validator stream is unparseable")
at = steps[0].get("attempt") or {}
if not isinstance(at.get("rc"), int):
    raise SystemExit(f"expected attempt.rc populated (got {at!r})")
PY
ASSERT_RC=$?
set -e
if [[ "${ASSERT_RC}" -ne 0 ]]; then
  MSG="$(head -5 "${ASSERT_LOG}" | tr '\n' ' ' | sed 's/"/\\"/g')"
  test_fail "${MSG}" "{\"log\":\"${ASSERT_LOG}\"}"
fi

test_pass "validator_decode_failure surfaces with attempts preserved" "{}"
