#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract extension_directory
test_require_pw
test_step run "directory authority with independent modification, exclusive creation and persistence observations"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "directory extension witness failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_extension_directory.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "directory authority controls, fresh writes, creation and withheld publication verified"
