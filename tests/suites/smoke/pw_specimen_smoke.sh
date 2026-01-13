#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="smoke"
PW_TEST_ID="pw_specimen_smoke"

PW_BIN="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"
SPECIMEN_FIXTURE="${ROOT_DIR}/tests/fixtures/pw_runner/specimen_file_read_deny.json"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "specimen_eval" "run specimen evaluation via policy-witness"

if [[ ! -x "${PW_BIN}" ]]; then
  test_skip "PolicyWitness.app is missing or not built at ${PW_BIN}"
  exit 0
fi

if [[ ! -f "${SPECIMEN_FIXTURE}" ]]; then
  test_fail "specimen fixture missing: ${SPECIMEN_FIXTURE}"
fi

# If we are running inside a sandboxed harness, specimen execution is expected
# to be blocked (nested-sandbox + unified log access constraints).
INSIDE="$("${PW_BIN}" inside --bare 2>/dev/null || true)"
if [[ "${INSIDE}" == "true" ]]; then
  test_skip "blocked: inside=true (rerun outside harness / with escalation)"
  exit 0
fi

OUTDIR="${PW_TEST_ARTIFACTS}/specimen_run"
mkdir -p "${OUTDIR}"

SPECIMEN_STDOUT="${PW_TEST_ARTIFACTS}/policy_witness.specimen.stdout.txt"
SPECIMEN_STDERR="${PW_TEST_ARTIFACTS}/policy_witness.specimen.stderr.txt"

set +e
"${PW_BIN}" specimen "${SPECIMEN_FIXTURE}" --outdir "${OUTDIR}" --force >"${SPECIMEN_STDOUT}" 2>"${SPECIMEN_STDERR}"
RC=$?
set -e

if [[ "${RC}" -eq 3 ]]; then
  test_skip "blocked: inside=true (rerun outside harness / with escalation)"
  exit 0
fi
if [[ "${RC}" -ne 0 ]]; then
  test_fail "policy-witness specimen failed (rc=${RC}); see ${OUTDIR}"
fi

SUMMARY_JSON="${OUTDIR}/lab_summary.json"
if [[ ! -f "${SUMMARY_JSON}" ]]; then
  test_fail "missing lab_summary.json at ${SUMMARY_JSON}"
fi

/usr/bin/python3 - "${SUMMARY_JSON}" <<'PY'
import json
import sys
from pathlib import Path

obj = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert obj.get("driver") == "pw_runner"
assert obj.get("profile") == "PWRunner"
steps = obj.get("steps") or []
if len(steps) != 1:
    raise SystemExit(f"expected 1 step (got {len(steps)})")
step = steps[0]
if step.get("sandbox_check_outcome") != "deny":
    raise SystemExit(f"expected sandbox_check_outcome=deny (got {step.get('sandbox_check_outcome')!r})")
PY

test_pass "specimen smoke ok" "{}"

