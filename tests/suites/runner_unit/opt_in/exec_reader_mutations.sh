#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_unit exec_reader_mutations
test_step controls "mutate publication gating and absence handling in disposable Swift sources"
test_check_python "${PW_TEST_ARTIFACTS}/controls.log" "exec reader mutation controls failed" \
  "${ROOT_DIR}/tests/suites/runner_unit/opt_in/exec_reader_mutations.py" "${PW_TEST_ARTIFACTS}/controls"
test_pass "baseline accepts independent exec facts; publication bypass and invented metadata fail designated assertions"
