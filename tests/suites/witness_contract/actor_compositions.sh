#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract actor_compositions
test_require_pw
test_step run "exercise two issuers, fan-out, repeated handles, self-transfer and empty revisits through the public actor form"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "actor composition witnessing failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_actor_compositions.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "$(tail -1 "${PW_TEST_ARTIFACTS}/assertions.log")" "{\"report\":\"${PW_TEST_ARTIFACTS}/report.json\"}"
