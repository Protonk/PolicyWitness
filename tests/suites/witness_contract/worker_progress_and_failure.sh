#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract worker_progress_and_failure
test_require_pw
test_build_fixture "${ROOT_DIR}/tests/fixtures/worker_lifecycle/build.sh" \
  "${PW_TEST_ARTIFACTS}/evidence-producer" "${PW_TEST_ARTIFACTS}/fixture-build.log"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "worker publication forwarding failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_worker_evidence.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${PW_TEST_ARTIFACTS}/evidence-producer"
test_pass "real worker success and compilation failure; unfamiliar publication survives worker-to-CLI forwarding"
