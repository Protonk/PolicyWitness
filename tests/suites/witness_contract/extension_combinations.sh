#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract extension_combinations
test_require_pw
test_step combined "matrix-driven faults retain publication, native outcomes and independent interruption receipts"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "combined extension controls failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_extension_combinations.py" "$PW_BIN" "$PW_TEST_ARTIFACTS"
test_pass "combined extension failures retain independent observations without invented completion or token disclosure"
