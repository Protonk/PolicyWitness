#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract actor_timing_qualification
test_require_pw
test_step run "run matched one-, three- and eight-actor workloads, the aggregate limits workload and the eight-actor re-delegation and calibration shapes; measure every actor-form allowance"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "actor timing qualification failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_actor_timing_qualification.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "$(tail -1 "${PW_TEST_ARTIFACTS}/assertions.log")" "{\"report\":\"${PW_TEST_ARTIFACTS}/report.json\"}"
