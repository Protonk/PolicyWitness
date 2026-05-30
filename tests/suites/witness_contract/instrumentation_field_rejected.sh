#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="witness_contract"
PW_TEST_ID="instrumentation_field_rejected"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "request carrying retired top-level 'instrumentation' field — expect bad_request"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

# Swift's JSONDecoder ignores unknown keys, so without a guard the
# decoder would happily decode the request as a valid PWRunnerRunSpec
# with the instrumentation field silently dropped — and the run would
# succeed. PWRunnerService.rejectedRetiredRequestKey runs a separate
# JSONSerialization pass to flag the retired key and emit a clean
# bad_request. This test is the load-bearing guard against the field
# being silently re-accepted.
SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json, sys
from pathlib import Path
spec = {
    "schema_version": 1,
    "specimen_id": "witness_contract_instrumentation_rejected",
    "policy": {"format": "sbpl", "sbpl_source": "(version 1) (allow default)"},
    "probe_plan": [],
    # `instrumentation` is not a supported top-level field. The
    # runner must reject any request that carries it rather than
    # silently dropping it (Swift's JSONDecoder ignores unknown keys
    # by default; the rejection runs as an explicit pre-decode pass).
    "instrumentation": {
        "version": 1,
        "ports": [{"kind": "debug_wait", "sleep_ms": 1}],
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
result = env.get("result") or {}
runner = env.get("data", {}).get("runner_result") or {}

if result.get("ok") is True:
    raise SystemExit(
        "request carrying retired 'instrumentation' field was accepted "
        "(result.ok=true). PWRunnerService.rejectedRetiredRequestKey "
        "should have produced normalized_outcome=bad_request before any "
        "worker spawn."
    )

outcome = runner.get("normalized_outcome")
if outcome != "bad_request":
    raise SystemExit(
        f"expected runner_result.normalized_outcome=bad_request "
        f"(got {outcome!r})"
    )
err = runner.get("error") or ""
if "instrumentation" not in err:
    raise SystemExit(
        f"expected error to name the retired field 'instrumentation' "
        f"(got {err!r})"
    )
PY
ASSERT_RC=$?
set -e
if [[ "${ASSERT_RC}" -ne 0 ]]; then
  MSG="$(head -5 "${ASSERT_LOG}" | tr '\n' ' ' | sed 's/"/\\"/g')"
  test_fail "${MSG}" "{\"log\":\"${ASSERT_LOG}\"}"
fi

test_pass "request with retired 'instrumentation' field is rejected as bad_request" "{}"
