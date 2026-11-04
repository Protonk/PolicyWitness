#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract extension_redelegation
test_require_pw
test_step run "run the principal three-actor re-delegation specimen, its positive calibration and four narrow contrasts through the CLI"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "re-delegation witnessing failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_extension_redelegation.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "$(tail -1 "${PW_TEST_ARTIFACTS}/assertions.log")" "{\"report\":\"${PW_TEST_ARTIFACTS}/report.json\"}"
