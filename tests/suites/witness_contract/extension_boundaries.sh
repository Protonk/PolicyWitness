#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract extension_boundaries
test_require_pw
test_step run "native issuer faults, consume/release interruption, transient-token confinement and descriptor closure"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "extension boundary controls failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_extension_boundaries.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "native boundary publications and token confinement retained independently"
