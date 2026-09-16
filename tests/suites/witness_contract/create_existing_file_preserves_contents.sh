#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin witness_contract create_existing_file_preserves_contents
test_require_pw
test_step run "create existing files under allowed and denied write policies; retain bytes and identities"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "existing-file create contract failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_create_existing.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "create preserves existing bytes and identities while enforcing write permission"
