#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin witness_contract pre_apply_failure_reports_no_policy_verdict
test_require_pw
test_step run "pre-apply deadline retains missing evidence; the same un-overridden specimen supplies real allow/deny controls"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "pre-apply evidence contract failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_pre_apply_failure.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "pre-apply failure makes no library or policy claim; positive control retains real verdicts and attempts; signal channel is null"
