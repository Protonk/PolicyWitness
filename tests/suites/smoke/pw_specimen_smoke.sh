#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="${PW_TEST_SUITE_OVERRIDE:-smoke}"
PW_TEST_ID="specimen_file_read_deny"

PW_BIN="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"
SPECIMEN_FIXTURE="${ROOT_DIR}/tests/fixtures/pw_runner/specimen_file_read_deny.json"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "run request via policy-witness"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

if [[ ! -f "${SPECIMEN_FIXTURE}" ]]; then
  test_fail "specimen fixture missing: ${SPECIMEN_FIXTURE}"
fi

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
render_specimen_with_runner "${SPECIMEN_FIXTURE}" "${SPECIMEN_PATH}"

# Note: sandboxed automation harnesses can block XPC lookup or unified log access.
# If this test fails with those symptoms, rerun from a normal Terminal.

RUN_STDOUT="${PW_TEST_ARTIFACTS}/policy_witness.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/policy_witness.run.stderr.txt"

set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
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

KIND_ERR="$(assert_runner_kind "${RUN_STDOUT}")" || test_fail "${KIND_ERR}" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"

test_pass "run smoke ok" "{}"
