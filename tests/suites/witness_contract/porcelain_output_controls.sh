#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract porcelain_output_controls
test_require_pw
test_step output "verify a complete dense read-only run, then close public stdout at two fixed prefixes"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "porcelain output controls failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/porcelain_output_controls.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "complete public evidence and nonzero incomplete output after both pipe closures" "{}"
