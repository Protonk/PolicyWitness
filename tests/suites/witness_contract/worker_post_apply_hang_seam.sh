#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="witness_contract"
PW_TEST_ID="worker_post_apply_hang_seam"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "_test_overrides.worker_post_apply_hang_ms drives runner_timeout"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json, sys
from pathlib import Path
spec = {
    "schema_version": 1,
    "specimen_id": "witness_contract_hang_seam",
    "policy": {"format": "sbpl", "sbpl_source": "(version 1) (allow default)"},
    "probe_plan": [],
    "_test_overrides": {
        "worker_post_apply_hang_ms": 5000,
        "worker_timeout_ms": 1500,
    },
}
Path(sys.argv[1]).write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/run.json"
START_MS="$(/usr/bin/python3 -c 'import time; print(int(time.time()*1000))')"
set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" >"${RUN_STDOUT}" 2>/dev/null
set -e
END_MS="$(/usr/bin/python3 -c 'import time; print(int(time.time()*1000))')"
ELAPSED_MS=$((END_MS - START_MS))

ASSERT_LOG="${PW_TEST_ARTIFACTS}/assertions.log"
set +e
PW_ELAPSED_MS="${ELAPSED_MS}" /usr/bin/python3 - "${RUN_STDOUT}" >"${ASSERT_LOG}" 2>&1 <<'PY'
import json, os, sys
from pathlib import Path
env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
runner = env.get("data", {}).get("runner_result") or {}
outcome = runner.get("normalized_outcome")
overrides = runner.get("test_overrides") or {}

if outcome == "bad_request" and "worker_post_apply_hang_ms" in (runner.get("error") or ""):
    raise SystemExit(
        "_test_overrides.worker_post_apply_hang_ms was rejected as "
        "an unrecognized field. The override should be plumbed through "
        "CWorkerOrchestrator into pw-probe-runner's --post-apply-hang-ms argv."
    )

if outcome != "runner_timeout":
    raise SystemExit(
        f"expected normalized_outcome=runner_timeout (got {outcome!r}). "
        "Either the override isn't honored, or the worker isn't actually hanging."
    )

if overrides.get("worker_post_apply_hang_ms") != 5000:
    raise SystemExit(f"expected test_overrides.worker_post_apply_hang_ms=5000 (got {overrides!r})")

elapsed = int(os.environ["PW_ELAPSED_MS"])
if elapsed < 1200 or elapsed > 4500:
    raise SystemExit(
        f"expected elapsed time ~1.5s (host deadline), got {elapsed}ms. "
        "Out of band suggests the timeout didn't drive the result."
    )
PY
ASSERT_RC=$?
set -e
if [[ "${ASSERT_RC}" -ne 0 ]]; then
  MSG="$(head -5 "${ASSERT_LOG}" | tr '\n' ' ' | sed 's/"/\\"/g')"
  test_fail "${MSG}" "{\"log\":\"${ASSERT_LOG}\"}"
fi

test_pass "worker_post_apply_hang_ms drives runner_timeout via host deadline (~${ELAPSED_MS}ms)" "{}"
