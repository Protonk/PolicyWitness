#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

test_begin sbpl_allowdeny_consistency sbpl_allowdeny_v1
test_require_pw
test_step run "check file bytes independently, then reverse policy parameters"
test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "filesystem/parameter consistency failed" \
  "${ROOT_DIR}/tests/suites/sbpl_allowdeny_consistency/check.py" \
  "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${ROOT_DIR}/tests/fixtures/runner_smoke/v1"
test_pass "allowed writes changed real bytes; denied files survived both parameter bindings"
