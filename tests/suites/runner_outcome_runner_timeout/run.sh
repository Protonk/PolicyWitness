#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="runner_outcome_runner_timeout"
PW_TEST_ID="host_kills_hung_worker"

PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "worker hangs in post-sandbox instrumentation; host times out and SIGKILLs"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

# This suite proves the host enforces its own deadline even when the
# worker survives sandbox apply. We do not test the *client*-side timeout
# (--timeout-ms) — that surfaces xpc_timeout from pw-runner-client, a
# different code path. Here we want the host's WorkerProcess deadline to
# fire, classify as runner_timeout, and SIGKILL the worker.
#
# Mechanism:
#   - worker_timeout_ms=2000 lowers the default 90s host deadline.
#   - A post_sandbox debug_wait port sleeps 8000ms in the worker, well
#     past the host's deadline.
#   - When the host hits 2000ms with no frame received, it SIGKILLs the
#     worker (term_signal=9, host-issued — not sandbox-issued) and
#     classifies as runner_timeout. The timedOut branch in
#     classifyWorkerResult takes precedence over the term_signal=9 path
#     that would otherwise be runner_sandbox_denied.

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json
import sys
from pathlib import Path

specimen = {
    "schema_version": 1,
    "specimen_id": "runner_timeout_probe",
    "policy": {
        "format": "sbpl",
        "sbpl_source": "(version 1) (allow default)",
    },
    "instrumentation": {
        "version": 1,
        "ports": [
            {"kind": "debug_wait", "phase": "post_sandbox", "sleep_ms": 8000}
        ],
    },
    "probe_plan": [],
    "_test_overrides": {
        "worker_timeout_ms": 2000,
    },
}
Path(sys.argv[1]).write_text(json.dumps(specimen, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/policy_witness.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/policy_witness.run.stderr.txt"

# Give the client a generous timeout — we want the *host* to time out
# first, not the client. Default is 240000ms; keep it.
START_MS="$(/usr/bin/python3 -c 'import time; print(int(time.time()*1000))')"
set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?
set -e
END_MS="$(/usr/bin/python3 -c 'import time; print(int(time.time()*1000))')"
ELAPSED_MS=$((END_MS - START_MS))

if [[ "${RC}" -eq 0 ]]; then
  test_fail "expected non-zero exit when worker times out (rc=${RC})" \
    "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

PW_ELAPSED_MS="${ELAPSED_MS}" /usr/bin/python3 - "${RUN_STDOUT}" <<'PY'
import json
import os
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
elapsed = int(os.environ["PW_ELAPSED_MS"])

if env.get("kind") != "run":
    raise SystemExit(f"expected kind=run (got {env.get('kind')!r})")
if env.get("result", {}).get("ok") is not False:
    raise SystemExit(f"expected ok=false (got {env.get('result')!r})")

runner = env.get("data", {}).get("runner_result") or {}
outcome = runner.get("normalized_outcome")
if outcome != "runner_timeout":
    raise SystemExit(
        f"expected normalized_outcome=runner_timeout (got {outcome!r}); "
        f"the host deadline override did not fire, or it raced with worker "
        f"completion. The debug_wait port should have held the worker open "
        f"for 8s — well past the 2s host deadline."
    )

# The host SIGKILLs the worker on timeout, so term_signal should be 9
# and exit_code should be null. partial_steps is false (probe_plan is empty).
sub = runner.get("runner_subprocess") or {}
if not sub:
    raise SystemExit("missing runner_subprocess (worker should have spawned)")
if sub.get("term_signal") != 9:
    raise SystemExit(
        f"expected runner_subprocess.term_signal=9 after host SIGKILL "
        f"(got {sub.get('term_signal')!r}); the worker may have exited on "
        f"its own before the host deadline."
    )
if sub.get("exit_code") is not None:
    raise SystemExit(
        f"expected runner_subprocess.exit_code=null when terminated by signal "
        f"(got {sub.get('exit_code')!r})"
    )

overrides = runner.get("test_overrides")
if not overrides:
    raise SystemExit("expected runner_result.test_overrides to be populated")
if overrides.get("worker_timeout_ms") != 2000:
    raise SystemExit(
        f"expected test_overrides.worker_timeout_ms=2000 "
        f"(got {overrides.get('worker_timeout_ms')!r})"
    )

# Sanity: the run should finish near the 2s host deadline, not the 8s
# instrumentation sleep. Generous bound — anything under 6s proves the
# host shortened the worker's life rather than waiting for the sleep.
if elapsed >= 6000:
    raise SystemExit(
        f"run took {elapsed}ms — expected close to the 2000ms host deadline. "
        f"Suggests the timeout didn't fire and we waited for the worker's "
        f"natural exit instead."
    )

if runner.get("steps"):
    raise SystemExit(f"expected empty steps (got {runner.get('steps')!r})")
PY

test_pass "runner_timeout fired at host deadline (~${ELAPSED_MS}ms)" "{}"
