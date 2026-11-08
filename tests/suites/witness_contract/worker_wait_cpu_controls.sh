#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract worker_wait_cpu_controls
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "neutral CPU reader controls failed" \
 "${ROOT_DIR}/tests/suites/witness_contract/worker_wait_cpu_controls.py" "${PW_TEST_ARTIFACTS}"
test_pass "quiet-worker evidence accepted without weakening generation, effects, interval or sensitivity checks"
