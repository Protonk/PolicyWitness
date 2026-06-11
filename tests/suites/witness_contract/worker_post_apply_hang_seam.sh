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
# --no-log-capture: a hung worker produces no deny evidence to capture, so the
# post-run `log show` scan would be pure overhead. Skipping it keeps the test
# fast and independent of the host's unified-log archive size. It is no longer
# load-bearing for correctness — the assertion below reads the envelope, not
# wall-clock — but there's no reason to pay for the scan.
set +e
"${PW_BIN}" run --no-log-capture "${SPECIMEN_PATH}" >"${RUN_STDOUT}" 2>/dev/null
set -e

ASSERT_LOG="${PW_TEST_ARTIFACTS}/assertions.log"
set +e
/usr/bin/python3 - "${RUN_STDOUT}" >"${ASSERT_LOG}" 2>&1 <<'PY'
import json, sys
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

# Tight, deterministic proof that the host deadline DROVE the result: the host
# fires its sentinel deadline (worker_timeout_ms=1500), then its reap grace
# timer (exitGraceMs=1000) expires while the worker is still mid-hang (5000ms),
# so the host SIGKILLs it — `runner_subprocess.term_signal == 9`. This replaces
# the old wall-clock bound, which measured controller launch + XPC cold-start +
# the unified-log scan and so was both fragile (host-dependent) and indirect.
# The failure modes it pins down:
#   - override ignored / worker not hanging -> worker exits cleanly,
#     term_signal is null (and outcome would not even be runner_timeout);
#   - host stops SIGKILLing on the grace path -> term_signal != 9.
sub = runner.get("runner_subprocess") or {}
term_signal = sub.get("term_signal")
if term_signal != 9:
    raise SystemExit(
        f"expected runner_subprocess.term_signal=9 (SIGKILL from the host grace "
        f"timer), got {term_signal!r} with runner_subprocess={sub!r}. The host "
        "deadline did not drive a kill of the hung worker."
    )
PY
ASSERT_RC=$?
set -e
if [[ "${ASSERT_RC}" -ne 0 ]]; then
  MSG="$(head -5 "${ASSERT_LOG}" | tr '\n' ' ' | sed 's/"/\\"/g')"
  test_fail "${MSG}" "{\"log\":\"${ASSERT_LOG}\"}"
fi

test_pass "worker_post_apply_hang_ms drives runner_timeout; host grace timer SIGKILLed the hung worker (term_signal=9)" "{}"
