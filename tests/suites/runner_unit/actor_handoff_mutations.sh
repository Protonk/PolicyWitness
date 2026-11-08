#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_unit actor_handoff_mutations
test_require_pw
test_step controls "compare one-shot handoffs and the inbound scan cursor with disposable payload-alias, removed-gate, shared-answer, early-erasure, scan-from-zero, prefix-past-hole, shared-word-prefix and missing-reset variants"
test_run_logged "${PW_TEST_ARTIFACTS}/controls.log" "actor handoff mutation controls failed" \
  "${PW_PYTHON}" -B -S "${ROOT_DIR}/tests/suites/runner_unit/actor_handoff_mutations.py" "${PW_TEST_ARTIFACTS}/controls" "${PW_TEST_SCRATCH}/build"
test_pass "baselines passed and eight mutations failed their designated observations"
