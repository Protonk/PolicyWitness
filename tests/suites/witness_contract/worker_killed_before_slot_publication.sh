#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract worker_killed_before_slot_publication
test_require_pw
test_step run "SIGKILL after a slot's native return and before its publication: the created file is observed independently while the reply withholds the result"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "killed-before-publication contract failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_killed_before_publication.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "unpublished native result withheld as no_completed_result with started_without_result; completed prefix and not_reached suffix preserved; native effect observed independently" "{}"
