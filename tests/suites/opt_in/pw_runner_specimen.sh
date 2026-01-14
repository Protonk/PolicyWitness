#!/usr/bin/env bash
# Opt-in smoke test for PolicyWitness's unified-log correlation path.
#
# Purpose:
# - Validate that `policy-witness run` can attach sandbox deny evidence via the embedded
#   `sandbox-log-observer` tool when invoked from an unsandboxed caller.
#
# Opt-in reason:
# - Unified Logging access is sandbox-sensitive; in sandboxed automation harnesses the observer is often
#   blocked, which would create noisy failures unrelated to PolicyWitness itself.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="opt_in"
PW_TEST_ID="pw_runner_specimen"

SPECIMEN_FIXTURE="${ROOT_DIR}/tests/fixtures/pw_runner/specimen_file_read_deny.json"
PW_BIN="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "run a deny specimen and require sandbox-log correlation"

if [[ ! -x "${PW_BIN}" ]]; then
  test_skip "PolicyWitness.app is missing or not built at ${PW_BIN}"
  exit 0
fi

if [[ ! -f "${SPECIMEN_FIXTURE}" ]]; then
  test_fail "specimen fixture missing: ${SPECIMEN_FIXTURE}"
fi

# Note: sandboxed automation harnesses can block XPC lookup or unified log access.
# If this test fails with those symptoms, rerun from a normal Terminal.

set +e
RUN_STDOUT="${PW_TEST_ARTIFACTS}/policy_witness.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/policy_witness.run.stderr.txt"
"${PW_BIN}" run "${SPECIMEN_FIXTURE}" --log-last "20s" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?
set -e

if [[ "${RC}" -ne 0 ]]; then
  test_fail "policy-witness run failed (rc=${RC})" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

set +e
/usr/bin/python3 - "${RUN_STDOUT}" <<'PY'
import json
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if env.get("kind") != "run":
    raise SystemExit(f"expected kind=run (got {env.get('kind')!r})")
if env.get("result", {}).get("ok") is not True:
    raise SystemExit(f"expected result.ok=true (got {env.get('result', {}).get('ok')!r})")

runner = env.get("data", {}).get("runner_result") or {}
if runner.get("normalized_outcome") != "ok":
    raise SystemExit(f"expected runner normalized_outcome=ok (got {runner.get('normalized_outcome')!r})")
steps = runner.get("steps") or []
if len(steps) != 1:
    raise SystemExit(f"expected 1 step (got {len(steps)})")
sb = (steps[0].get("sandbox_check") or {})
if sb.get("outcome") != "deny":
    raise SystemExit(f"expected sandbox_check.outcome=deny (got {sb.get('outcome')!r})")

cap = env.get("data", {}).get("sandbox_log_capture")
if not isinstance(cap, dict):
    raise SystemExit("missing data.sandbox_log_capture (controller did not attach capture results)")
status = cap.get("capture_status")
observed = cap.get("observed_deny")
if status != "captured":
    print(f"SKIP: sandbox_log_capture capture_status={status!r}", file=sys.stderr)
    raise SystemExit(3)
if observed is not True:
    raise SystemExit(f"expected sandbox_log_capture.observed_deny=true (got {observed!r})")
PY
PY_STATUS=$?
set -e

if [[ ${PY_STATUS} -eq 3 ]]; then
  test_skip "sandbox-log-observer unavailable on this host (see artifacts)" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
  exit 0
fi
if [[ ${PY_STATUS} -ne 0 ]]; then
  test_fail "sandbox-log correlation did not meet expectations" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

test_pass "sandbox-log correlation ok" "{}"
