#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract extension_policy_qualification
test_require_pw
test_step run "compile and apply the principal specimen's B policy with a baseline fresh read and an ordinary control"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "policy qualification failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_extension_policy_qualification.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "consumed-extension issuance policy compiles with sbpl-check and applies in a fresh worker"
