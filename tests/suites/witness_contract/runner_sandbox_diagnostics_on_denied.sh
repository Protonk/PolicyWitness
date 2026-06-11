#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="witness_contract"
PW_TEST_ID="runner_sandbox_diagnostics_on_denied"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "kill-signal seam drives runner_sandbox_denied; assert diagnostics object + null first_deny"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

# `(allow default)` so sandbox_apply succeeds; the worker_post_apply_kill_signal
# seam then raises SIGKILL on the worker AFTER `applied` but BEFORE `done`. The
# host observes applied=1, done=0, and a foreign termination signal — which the
# classifier maps to runner_sandbox_denied (the same observable shape a real
# kernel sandbox kill produces). This makes the outcome — and the controller's
# diagnostics-on-denied path — reachable deterministically, with no dependency
# on a real fatal-on-deny kernel event.
SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json, sys
from pathlib import Path
spec = {
    "schema_version": 1,
    "specimen_id": "witness_contract_sandbox_denied_seam",
    "policy": {"format": "sbpl", "sbpl_source": "(version 1)\n(allow default)\n"},
    "probe_plan": [{
        "step_id": "p1",
        "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/etc/hosts"}},
        "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"},
    }],
    "_test_overrides": {"worker_post_apply_kill_signal": 9},
}
Path(sys.argv[1]).write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/run.json"
# Default log capture (NOT --no-log-capture): exercises the controller's
# observer invocation on a runner_sandbox_denied outcome end-to-end.
set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" >"${RUN_STDOUT}" 2>/dev/null
set -e

ASSERT_LOG="${PW_TEST_ARTIFACTS}/assertions.log"
set +e
/usr/bin/python3 - "${RUN_STDOUT}" >"${ASSERT_LOG}" 2>&1 <<'PY'
import json, sys
from pathlib import Path
env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
data = env.get("data") or {}
runner = data.get("runner_result") or {}

outcome = runner.get("normalized_outcome")
if outcome == "bad_request" and "worker_post_apply_kill_signal" in (runner.get("error") or ""):
    raise SystemExit(
        "_test_overrides.worker_post_apply_kill_signal was rejected as an "
        "unrecognized field. The override should be plumbed through "
        "CWorkerOrchestrator into pw-probe-runner's --post-apply-kill-signal argv."
    )
if outcome != "runner_sandbox_denied":
    raise SystemExit(
        f"expected normalized_outcome=runner_sandbox_denied (got {outcome!r}). "
        "Either the kill seam isn't honored, or the host classified the foreign "
        "signal differently."
    )

# The error names the real artifact of the failure (the foreign signal),
# catching "outcome string is right but came from a fake code path".
err = runner.get("error") or ""
if "signal" not in err:
    raise SystemExit(f"expected error to mention the termination signal (got {err!r})")

# The override was honored and echoed back — catches a stale build that
# silently ignores `worker_post_apply_kill_signal`.
echoed = (runner.get("test_overrides") or {}).get("worker_post_apply_kill_signal")
if echoed != 9:
    raise SystemExit(f"expected test_overrides.worker_post_apply_kill_signal=9 (got {echoed!r})")

# The worker was reaped with the foreign signal (9), not a host-grace SIGKILL.
sub = runner.get("runner_subprocess") or {}
if sub.get("term_signal") != 9:
    raise SystemExit(f"expected runner_subprocess.term_signal=9 (got {sub!r})")

# Controller synthesis: the outer diagnostics object is present for
# runner_sandbox_denied so consumers can branch on first_deny != null directly.
diag = data.get("runner_sandbox_diagnostics")
if diag is None:
    raise SystemExit("data.runner_sandbox_diagnostics must be present on runner_sandbox_denied")

# first_deny is null HERE: the worker self-killed under (allow default), so no
# kernel sandbox deny exists for its pid. A *populated* first_deny needs a real
# fatal-on-deny kernel event, which is OS-dependent and unforgeable — that path
# is covered by the controller unit tests (run_flow::tests / sandbox_log::tests).
if diag.get("first_deny") is not None:
    raise SystemExit(f"expected first_deny=null (no kernel deny for allow-default self-kill); got {diag!r}")

# The controller invoked the observer for the worker pid (the capture object is
# present regardless of whether the unified log was readable on this host).
if data.get("sandbox_log_capture") is None:
    raise SystemExit("expected data.sandbox_log_capture present (controller captures logs on runner_sandbox_denied)")
PY
ASSERT_RC=$?
set -e
if [[ "${ASSERT_RC}" -ne 0 ]]; then
  MSG="$(head -5 "${ASSERT_LOG}" | tr '\n' ' ' | sed 's/"/\\"/g')"
  test_fail "${MSG}" "{\"log\":\"${ASSERT_LOG}\"}"
fi

test_pass "runner_sandbox_denied via kill seam → diagnostics object present, first_deny null, observer invoked" "{}"
