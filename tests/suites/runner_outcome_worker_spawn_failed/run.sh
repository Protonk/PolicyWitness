#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="runner_outcome_worker_spawn_failed"
PW_TEST_ID="posix_spawn_enoent_propagates_to_outcome"

PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "_test_overrides.worker_executable_path=/nonexistent — expect worker_spawn_failed"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

# Pointing worker_executable_path at a file that does not exist makes
# posix_spawn() return ENOENT for a real reason. The host's spawn-side
# Result.failure flows into PWRunnerService's worker_spawn_failed branch
# and back over real XPC. Nothing is stubbed.
FAKE_WORKER="/nonexistent/policy-witness-worker-not-real"

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
PW_FAKE_WORKER="${FAKE_WORKER}" /usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json
import os
import sys
from pathlib import Path

specimen = {
    "schema_version": 1,
    "specimen_id": "worker_spawn_failed_probe",
    "policy": {
        "format": "sbpl",
        # Policy is irrelevant — we never reach sandbox apply.
        "sbpl_source": "(version 1) (allow default)",
    },
    "probe_plan": [],
    "_test_overrides": {
        "worker_executable_path": os.environ["PW_FAKE_WORKER"],
    },
}
Path(sys.argv[1]).write_text(json.dumps(specimen, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/policy_witness.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/policy_witness.run.stderr.txt"

set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?
set -e

if [[ "${RC}" -eq 0 ]]; then
  test_fail "expected non-zero exit when worker cannot be spawned (rc=${RC})" \
    "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

PW_FAKE_WORKER="${FAKE_WORKER}" /usr/bin/python3 - "${RUN_STDOUT}" <<'PY'
import json
import os
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
fake = os.environ["PW_FAKE_WORKER"]

if env.get("kind") != "run":
    raise SystemExit(f"expected kind=run (got {env.get('kind')!r})")
if env.get("result", {}).get("ok") is not False:
    raise SystemExit(f"expected ok=false (got {env.get('result')!r})")

runner = env.get("data", {}).get("runner_result") or {}
outcome = runner.get("normalized_outcome")
if outcome != "worker_spawn_failed":
    raise SystemExit(
        f"expected normalized_outcome=worker_spawn_failed (got {outcome!r}); "
        f"the override did not reach posix_spawn or the classifier shape changed."
    )

error_msg = runner.get("error") or ""
# Either the override path appears in the error string, or the underlying
# posix_spawn errno does. Both are evidence we exercised the real spawn.
if "posix_spawn" not in error_msg and fake not in error_msg:
    raise SystemExit(
        f"expected error to mention posix_spawn or the override path; "
        f"got error={error_msg!r}"
    )

overrides = runner.get("test_overrides")
if not overrides:
    raise SystemExit("expected runner_result.test_overrides to be populated")
if overrides.get("worker_executable_path") != fake:
    raise SystemExit(
        f"expected test_overrides.worker_executable_path={fake!r}, "
        f"got {overrides.get('worker_executable_path')!r}"
    )

# No worker was spawned, so runner_subprocess must be absent.
if runner.get("runner_subprocess") is not None:
    raise SystemExit(
        f"expected runner_subprocess=null when posix_spawn fails; "
        f"got {runner.get('runner_subprocess')!r}"
    )
if runner.get("steps"):
    raise SystemExit(f"expected empty steps (got {runner.get('steps')!r})")
PY

test_pass "worker_spawn_failed propagated end-to-end with override reflected" "{}"
