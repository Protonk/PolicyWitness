#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract unfamiliar_diagnostic_transport
test_require_pw
test_build_fixture "${ROOT_DIR}/tests/fixtures/worker_lifecycle/build.sh" \
  "${PW_TEST_ARTIFACTS}/transport-producer" "${PW_TEST_ARTIFACTS}/fixture-build.log"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "unfamiliar diagnostic transport failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_diagnostic_transport.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${PW_TEST_ARTIFACTS}/transport-producer"
test_pass "two unfamiliar payloads preserved; publication, decode and independent failure controls retained"
