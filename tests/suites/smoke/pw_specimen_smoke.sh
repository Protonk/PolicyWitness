#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="smoke"
PW_TEST_ID="pw_specimen_smoke"

PW_BIN="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"
SPECIMEN_FIXTURE="${ROOT_DIR}/tests/fixtures/pw_runner/specimen_file_read_deny.json"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "run request via policy-witness"

if [[ ! -x "${PW_BIN}" ]]; then
  test_skip "PolicyWitness.app is missing or not built at ${PW_BIN}"
  exit 0
fi

if [[ ! -f "${SPECIMEN_FIXTURE}" ]]; then
  test_fail "specimen fixture missing: ${SPECIMEN_FIXTURE}"
fi

# Some automation harnesses run commands inside an OS sandbox. In that context,
# specimen execution can fail for reasons unrelated to PolicyWitness itself
# (XPC lookup restrictions, unified log access restrictions).
if [[ -n "${CODEX_SANDBOX:-}" ]]; then
  test_skip "sandboxed automation harness detected (CODEX_SANDBOX is set); rerun from a normal Terminal"
  exit 0
fi

RUN_STDOUT="${PW_TEST_ARTIFACTS}/policy_witness.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/policy_witness.run.stderr.txt"

set +e
"${PW_BIN}" run "${SPECIMEN_FIXTURE}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?
set -e

if [[ "${RC}" -ne 0 ]]; then
  test_fail "policy-witness run failed (rc=${RC})" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

/usr/bin/python3 - "${RUN_STDOUT}" <<'PY'
import json
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert env.get("kind") == "run"
assert env.get("result", {}).get("ok") is True

runner = env.get("data", {}).get("runner_result") or {}
steps = runner.get("steps") or []
if len(steps) != 1:
    raise SystemExit(f"expected 1 step (got {len(steps)})")
step = steps[0]
sb = step.get("sandbox_check") or {}
if sb.get("outcome") != "deny":
    raise SystemExit(f"expected sandbox_check.outcome=deny (got {sb.get('outcome')!r})")
PY

test_pass "run smoke ok" "{}"
