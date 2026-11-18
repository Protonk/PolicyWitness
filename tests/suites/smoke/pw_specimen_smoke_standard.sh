#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="${PW_TEST_SUITE_OVERRIDE:-smoke}"
PW_TEST_ID="specimen_file_read_deny_standard"

PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"
SPECIMEN_FIXTURE="${ROOT_DIR}/tests/fixtures/pw_runner/specimen_file_read_deny.json"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "run request via policy-witness (standard default)"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

if [[ ! -f "${SPECIMEN_FIXTURE}" ]]; then
  test_fail "specimen fixture missing: ${SPECIMEN_FIXTURE}"
fi

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
PW_TEST_RUNNER_MODE= PW_TEST_RUNNER_SERVICE= render_specimen_with_runner "${SPECIMEN_FIXTURE}" "${SPECIMEN_PATH}"

RUN_STDOUT="${PW_TEST_ARTIFACTS}/policy_witness.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/policy_witness.run.stderr.txt"

set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?
set -e

if [[ "${RC}" -ne 0 ]]; then
  test_fail "policy-witness run failed (rc=${RC})" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

ASSERT_LOG="${PW_TEST_ARTIFACTS}/assertions.log"
ASSERT_RC=0
"${PW_PYTHON}" -B -S -P - "${RUN_STDOUT}" >"${ASSERT_LOG}" 2>&1 <<'PY' || ASSERT_RC=$?
import json
import sys
from pathlib import Path

# A failed expectation about the envelope is this case's reported failure: it
# prints the expectation and exits 3. Any other exit is not a product verdict.
def refuse(message):
    print(message, file=sys.stderr)
    raise SystemExit(3)

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if env.get("kind") != "run":
    refuse(f"expected kind=run (got {env.get('kind')!r})")
if env.get("result", {}).get("ok") is not True:
    refuse(f"expected top-level ok=true (got {env.get('result')!r})")

runner_kind = (((env.get("data") or {}).get("specimen") or {}).get("runner_provenance") or {}).get("runner_kind")
if runner_kind != "standard":
    refuse(f"expected runner_kind='standard' (got {runner_kind!r})")
PY
if [[ "${ASSERT_RC}" -eq 3 ]]; then
  cat "${ASSERT_LOG}" >&2 || true
  test_fail "run envelope expectation failed: $(head -n 1 "${ASSERT_LOG}") (log: ${ASSERT_LOG})" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\",\"assertions\":\"${ASSERT_LOG}\"}"
elif [[ "${ASSERT_RC}" -ne 0 ]]; then
  # An unexpected error in the block ends the script without a terminal report.
  cat "${ASSERT_LOG}" >&2 || true
  exit "${ASSERT_RC}"
fi

test_pass "run smoke ok (standard default)" "{}"
