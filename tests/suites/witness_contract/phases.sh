#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract phases
test_require_pw
test_step run "fresh planning after ordinary phase effects, bounded collection and independent reader controls"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "phase witness failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_phases.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "ordered phases retain distinct collections, independent file effects and unavailable later predictions"
