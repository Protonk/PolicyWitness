#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_c_worker_harness actor_operations
test_step controls "count explicit native-operation boundaries and reject skipped calls, wrong delivery and inherited-descriptor reads"
test_run_logged "${PW_TEST_ARTIFACTS}/controls.log" "actor operation controls failed" \
  "${PW_PYTHON}" -B -S "${ROOT_DIR}/tests/suites/runner_c_worker_harness/actor_operations.py" \
  "${PW_TEST_ARTIFACTS}" "${PW_TEST_SCRATCH}"
test_pass "baseline passed and five disposable source mutations failed at their designated independent observation"
