#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_unit host_setup_oracle_sensitivity
test_step controls "characterize accepted endpoint and mapping-cleanup counterexamples with independent observations"
test_run_logged "${PW_TEST_ARTIFACTS}/controls.log" "host setup oracle characterization failed" \
  "${PW_PYTHON}" -B -S "${ROOT_DIR}/tests/suites/runner_unit/host_setup_oracle_sensitivity.py" "${PW_TEST_ARTIFACTS}/controls" "${PW_TEST_SCRATCH}/build"
test_pass "unchanged setup oracle accepted the baseline and independently observed controlled counterexamples; no product-safety claim"
