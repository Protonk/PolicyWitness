#!/usr/bin/env bash
# Opt-in smoke test for the new PWRunner specimen execution path.
# Exercises:
#   - `pw-lab specimen` (canonical + instrumented runs)
#   - Channel D (sandbox_check) vs Channel A (attempt outcome) consistency
#   - Channel B deterministic deny marker (SBPL `message` emitted on deny)
#   - Channel C unified-log correlation via sandbox-log-observer (required for high confidence)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="opt_in"
PW_TEST_ID="pw_runner_specimen"

LAB_TOOL="${ROOT_DIR}/laboratory/pw-lab"
SPECIMEN_FIXTURE="${ROOT_DIR}/tests/fixtures/pw_runner/specimen_file_read_deny.json"
PW_BIN="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "specimen_eval" "run PWRunner specimen evaluation"

if [[ ! -x "${LAB_TOOL}" ]]; then
  test_fail "pw-lab tool is missing or not executable: ${LAB_TOOL}"
fi

if [[ ! -x "${PW_BIN}" ]]; then
  test_skip "PolicyWitness.app is missing or not built at ${PW_BIN}"
  exit 0
fi

if [[ ! -f "${SPECIMEN_FIXTURE}" ]]; then
  test_fail "specimen fixture missing: ${SPECIMEN_FIXTURE}"
fi

OUTDIR="${PW_TEST_ARTIFACTS}/specimen_run"
mkdir -p "${OUTDIR}"

set +e
#
# Note: `pw-lab specimen` is intentionally fail-closed about output directories
# to avoid mixing artifacts across runs. Keep the specimen output directory
# empty by writing this test's stdout/stderr logs *outside* the outdir.
#
SPECIMEN_STDOUT="${PW_TEST_ARTIFACTS}/pw_lab_specimen.stdout.txt"
SPECIMEN_STDERR="${PW_TEST_ARTIFACTS}/pw_lab_specimen.stderr.txt"
"${LAB_TOOL}" specimen "${SPECIMEN_FIXTURE}" --pw "${PW_BIN}" --outdir "${OUTDIR}" >"${SPECIMEN_STDOUT}" 2>"${SPECIMEN_STDERR}"
RC=$?
set -e

if [[ "${RC}" -eq 3 ]]; then
  test_skip "blocked: inside=true (run outside harness / with escalation)"
  exit 0
fi
if [[ "${RC}" -ne 0 ]]; then
  test_fail "pw-lab specimen failed (rc=${RC}); see ${OUTDIR}"
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
steps = obj.get("steps") or []
if len(steps) != 1:
    raise SystemExit(f"expected 1 step (got {len(steps)})")
step = steps[0]
if step.get("sandbox_check_outcome") != "deny":
    raise SystemExit(f"expected sandbox_check_outcome=deny (got {step.get('sandbox_check_outcome')!r})")

evidence = obj.get("evidence") or {}
sandbox_logs = (evidence.get("sandbox_logs") or {})
if sandbox_logs.get("observed_deny") is not True:
    raise SystemExit(f"expected evidence.sandbox_logs.observed_deny=true (got {sandbox_logs.get('observed_deny')!r})")
deny_marker = evidence.get("deny_marker") or {}
if not isinstance(deny_marker, dict) or deny_marker.get("observed") is not True:
    raise SystemExit(f"expected evidence.deny_marker.observed=true (got {deny_marker!r})")
uncertainty = obj.get("uncertainty") or {}
if uncertainty.get("confidence") != "high":
    raise SystemExit(f"expected uncertainty.confidence=high (got {uncertainty.get('confidence')!r})")
PY

test_pass "pw-runner specimen ok" "{}"
