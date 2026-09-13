#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

test_begin sbpl_allowdeny_consistency sbpl_allowdeny_v1
test_step run "check file bytes independently, then reverse policy parameters"
[[ -x "${PW_BIN}" ]] || test_fail "built policy-witness missing: ${PW_BIN}"

if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/sbpl_allowdeny_consistency/check.py" \
    "${PW_BIN}" "${PW_TEST_ARTIFACTS}" "${ROOT_DIR}/tests/fixtures/runner_smoke/v1" \
    >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assert.log" >&2
  test_fail "filesystem/parameter consistency failed; see artifacts/assert.log"
fi
test_pass "allowed writes changed real bytes; denied files survived both parameter bindings"
