#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract extensions
test_require_pw
test_step run "native extension issuance, consumption and release in one worker with fresh reads"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "extension witness failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_extensions.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "native lifecycle and fresh descriptor observations retained with phase-local predictions"
