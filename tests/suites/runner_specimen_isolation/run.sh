#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

test_begin runner_specimen_isolation overlapping_runs_keep_evidence_separate
[[ -x "${PW_BIN}" ]] || test_fail "built policy-witness missing: ${PW_BIN}"
HELPER="${PW_TEST_ARTIFACTS}/helper"
test_step build "compile shared exec fixture and OS process observer"
if ! bash "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${HELPER}" \
    >"${PW_TEST_ARTIFACTS}/build.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/build.log" >&2
  test_fail "exec fixture build failed"
fi
test_step overlap "finish B while A stays held; compare independent evidence and reject cross-run swaps"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/runner_specimen_isolation/check.py" \
    "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${HELPER}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assert.log" >&2
  test_fail "specimen isolation contract failed; see artifacts"
fi
test_pass "overlapping specimens retain their own processes, effects, and evidence; swap controls rejected"
