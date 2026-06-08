#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="runner_ready_byte_resilience"
PW_TEST_ID="slow_compile_ready_byte_survives_sigpipe"

PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "worker whose ready byte lands on a host-closed pipe still applies + scores"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

# Regression for the com.apple.WebProcess SIGPIPE bug. A large profile's
# sandbox_compile_string runs longer than the host's readyByteTimeout
# (default 1000ms). The worker writes its pre-apply ready byte only after
# that compile, by which point the host has closed --ready-fd. The worker
# must NOT die of SIGPIPE on that write: it must continue to sandbox_apply
# and report through the shm sentinels, so the run still scores normally.
#
# Mechanism (no 13s WebProcess compile needed — the seam models it):
#   - worker_pre_ready_hang_ms=2000 makes pw-probe-runner nanosleep 2000ms
#     BEFORE the ready byte. The host's default 1000ms readyByteTimeout
#     fires first and closes the read end, so the worker's later ready-byte
#     write hits a closed pipe.
#   - With SIGPIPE ignored, that write returns EPIPE and the worker
#     proceeds: applies (allow default), runs the probe, flips done, exits
#     cleanly. Outcome=ok, validator ran, no signal.
#   - On the pre-fix worker this same path SIGPIPEs the worker before apply:
#     no `applied`, apply_rc reads zero-init 0, outcome=sandbox_apply_failed,
#     term_signal=13. So this suite fails loudly on a regression.

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json
import sys
from pathlib import Path

specimen = {
    "schema_version": 1,
    "specimen_id": "ready_byte_resilience_probe",
    "policy": {
        "format": "sbpl",
        "sbpl_source": "(version 1) (allow default)",
    },
    "probe_plan": [
        {
            "step_id": "fr1",
            "sandbox_check": {
                "operation": "file-read-data",
                "filter": {"kind": "path", "value": "/etc/hosts"},
            },
            "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"},
        }
    ],
    "_test_overrides": {
        # 2000ms > the host's default 1000ms readyByteTimeout, so the host
        # closes --ready-fd before the worker writes its ready byte.
        "worker_pre_ready_hang_ms": 2000,
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

if [[ "${RC}" -ne 0 ]]; then
  test_fail "expected exit 0 (worker should survive the closed ready pipe and apply), rc=${RC}" \
    "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

/usr/bin/python3 - "${RUN_STDOUT}" <<'PY'
import json
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

if env.get("kind") != "run":
    raise SystemExit(f"expected kind=run (got {env.get('kind')!r})")
if env.get("result", {}).get("ok") is not True:
    raise SystemExit(
        f"expected ok=true (got {env.get('result')!r}); a regression here is the "
        f"SIGPIPE death — the worker took the ready-byte write as fatal before apply."
    )

runner = env.get("data", {}).get("runner_result") or {}
outcome = runner.get("normalized_outcome")
if outcome != "ok":
    raise SystemExit(
        f"expected normalized_outcome=ok (got {outcome!r}); on the pre-fix worker "
        f"this is 'sandbox_apply_failed' because the worker SIGPIPEs on the ready "
        f"byte before sandbox_apply runs."
    )

# The worker must have survived and exited cleanly — NOT died of SIGPIPE (13).
sub = runner.get("runner_subprocess") or {}
if not sub:
    raise SystemExit("missing runner_subprocess (worker should have spawned)")
if sub.get("term_signal") is not None:
    raise SystemExit(
        f"expected runner_subprocess.term_signal=null (got {sub.get('term_signal')!r}); "
        f"term_signal=13 is the SIGPIPE regression this suite guards against."
    )
if sub.get("exit_code") != 0:
    raise SystemExit(f"expected runner_subprocess.exit_code=0 (got {sub.get('exit_code')!r})")

# Worker survived → applied → the validator child ran and scored the probe.
if "validator_subprocess" not in runner:
    raise SystemExit("expected validator_subprocess (worker applied, so the validator should have run)")
steps = runner.get("steps") or []
if len(steps) != 1:
    raise SystemExit(f"expected 1 scored step (got {len(steps)})")

overrides = runner.get("test_overrides")
if not overrides:
    raise SystemExit("expected runner_result.test_overrides to be populated")
if overrides.get("worker_pre_ready_hang_ms") != 2000:
    raise SystemExit(
        f"expected test_overrides.worker_pre_ready_hang_ms=2000 "
        f"(got {overrides.get('worker_pre_ready_hang_ms')!r}); a stale build that "
        f"ignores the override would otherwise pass."
    )
PY

test_pass "worker survived closed ready pipe, applied, and scored the probe" "{}"
