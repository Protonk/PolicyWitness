#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract max_targets_reply_survives
test_require_pw
test_step run "long-target, escaped-path, maximal independent-query and exec replies; admission refusal of oversized query values and filter/attempt labels"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "maximum-target reply contract failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_max_target_reply.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "five measured workloads returned intact; oversized query values and filter/attempt labels refused before any process work" "{}"
