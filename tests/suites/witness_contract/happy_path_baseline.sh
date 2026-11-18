#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="witness_contract"
PW_TEST_ID="happy_path_baseline"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "(allow default) specimen with one file open_read step"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
"${PW_PYTHON}" -B -S -P - "${SPECIMEN_PATH}" <<'PY'
import os, sys
sys.path.insert(0, os.environ['PW_CONTRACT_TEST_LIB'])
import build_context
import json, sys
from pathlib import Path
spec = {
    'contract': build_context.candidate_contract(),
    "specimen_id": "witness_contract_baseline",
    "policy": {"format": "sbpl", "sbpl_source": "(version 1) (allow default)"},
    "probe_plan": [{
        "step_id": "fr1",
        "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/etc/hosts"}},
        "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"},
    }],
}
Path(sys.argv[1]).write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/run.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/run.stderr.txt"
set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?
set -e
if [[ "${RC}" -ne 0 ]]; then
  test_fail "baseline specimen should succeed (rc=${RC})" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

ASSERT_LOG="${PW_TEST_ARTIFACTS}/assertions.log"
ASSERT_RC=0
"${PW_PYTHON}" -B -S -P - "${RUN_STDOUT}" >"${ASSERT_LOG}" 2>&1 <<'PY' || ASSERT_RC=$?
import json, sys
from pathlib import Path

# A failed expectation about the envelope is this case's reported failure: it
# prints the expectation and exits 3. Any other exit is not a product verdict.
def refuse(message):
    print(message, file=sys.stderr)
    raise SystemExit(3)

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if env.get("result", {}).get("ok") is not True:
    refuse(f"expected ok=true, got {env.get('result')!r}")
runner = env.get("data", {}).get("runner_result") or {}
if runner.get("normalized_outcome") != "finished":
    refuse(f"expected outcome=finished, got {runner.get('normalized_outcome')!r}")
steps = runner.get("steps") or []
if len(steps) != 1:
    refuse(f"expected 1 step, got {len(steps)}")
sb = steps[0].get("sandbox_check") or {}
if sb.get("outcome") != "allow":
    refuse(f"expected sandbox_check.outcome=allow, got {sb.get('outcome')!r}")
at = steps[0].get("attempt") or {}
# Witness that the ALLOWED read actually succeeded, not merely that the attempt
# channel is present. `(allow default)` + open_read of /etc/hosts must return
# rc==0 and capture the opened path; a failed read (rc!=0) would mean the allow
# did not take effect and must not pass as the "happy path" baseline.
if at.get("rc") != 0:
    refuse(f"expected attempt.rc==0 (allowed read should succeed), got {at.get('rc')!r}")
if not at.get("observed_path"):
    refuse(f"expected attempt.observed_path on a successful open_read, got {at.get('observed_path')!r}")
sub = runner.get("runner_subprocess") or {}
if not isinstance(sub.get("pid"), int):
    refuse(f"expected runner_subprocess.pid to be int, got {sub!r}")
PY
if [[ "${ASSERT_RC}" -eq 3 ]]; then
  cat "${ASSERT_LOG}" >&2 || true
  test_fail "baseline envelope expectation failed: $(head -n 1 "${ASSERT_LOG}") (log: ${ASSERT_LOG})" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\",\"assertions\":\"${ASSERT_LOG}\"}"
elif [[ "${ASSERT_RC}" -ne 0 ]]; then
  # An unexpected error in the block ends the script without a terminal report.
  cat "${ASSERT_LOG}" >&2 || true
  exit "${ASSERT_RC}"
fi

test_pass "baseline happy-path verdict and attempt both produced" "{}"
