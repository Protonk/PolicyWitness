#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract worker_sparse_failure
test_require_pw
test_build_fixture "${ROOT_DIR}/tests/fixtures/worker_lifecycle/build.sh" \
  "${PW_TEST_ARTIFACTS}/evidence-producer" "${PW_TEST_ARTIFACTS}/fixture-build.log"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "sparse worker evidence was lost" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_worker_sparse.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${PW_TEST_ARTIFACTS}/evidence-producer"
test_pass "worker source rejection and host EPIPE coexist; no-report and completed-probe failures retain independent facts"
