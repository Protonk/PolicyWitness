#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin witness_contract dossier_witness
test_require_pw
test_step run "the specimen dossier against the request that ran, host facts and manifest read independently, executable overrides, refusals and the stdin delivery receipt"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "dossier witness failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_dossier.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
test_pass "data.specimen reports the submitted policy, host, runner, manifest and binaries as independently observed; refusals keep the uniform envelope" "{}"
