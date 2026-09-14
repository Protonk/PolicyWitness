#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_exec_inheritance mutation_controls
test_step build "compile test equipment for disposable worker variants"
HELPER="${PW_TEST_OUT_DIR}/inheritance-mutations/helper"
HARNESS="${PW_TEST_OUT_DIR}/inheritance-mutations/worker-harness"
test_build_fixture "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${HELPER}"
test_build_fixture "${ROOT_DIR}/tests/fixtures/worker_harness/build.sh" "${HARNESS}" \
  "${PW_TEST_ARTIFACTS}/harness-build.log"
test_step run "unmodified worker must pass; environment and descriptor leaks must be diagnosed"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/runner_exec_inheritance/opt_in/mutations.py" \
    "${PW_TEST_ARTIFACTS}" "${HELPER}" "${HARNESS}" \
    >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assert.log" >&2
  test_fail "mutation controls failed; see per-variant artifacts"
fi
test_pass "baseline worker accepted; deliberate environment and descriptor leaks rejected"
