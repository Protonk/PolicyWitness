#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin runner_specimen_isolation overlapping_runs_keep_evidence_separate
test_require_pw
HELPER="${PW_TEST_ARTIFACTS}/helper"
test_step build "compile shared exec fixture and OS process observer"
test_build_fixture "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${HELPER}"
test_step overlap "finish B while A stays held; compare independent evidence and reject cross-run swaps"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" \
  "specimen isolation contract failed" \
  "${ROOT_DIR}/tests/suites/runner_specimen_isolation/check.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${HELPER}"
test_pass "overlapping specimens retain their own processes, effects, and evidence; swap controls rejected"
