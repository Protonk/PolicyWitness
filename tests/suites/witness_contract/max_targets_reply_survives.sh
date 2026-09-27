#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract max_targets_reply_survives
test_require_pw
test_step run "long-target, escaped-path, independent-query and exec replies; explicit loss for an admitted over-cap reply"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "maximum-target reply contract failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_max_target_reply.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "four measured workloads returned intact; admitted over-cap reply retained explicit receiver-loss evidence" "{}"
