#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"
test_begin runner_exec_inheritance mutation_controls
test_step build "compile test equipment for disposable worker variants"
HELPER="${PW_TEST_OUT_DIR}/inheritance-mutations/helper"
HARNESS="${PW_TEST_OUT_DIR}/inheritance-mutations/worker-harness"
if ! bash "${ROOT_DIR}/tests/fixtures/exec/build.sh" "${HELPER}" \
    >"${PW_TEST_ARTIFACTS}/build.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/build.log" >&2
  test_fail "inspection fixture build failed"
fi
if ! /usr/bin/xcrun --sdk macosx clang -Wall -Wextra -Werror -O2 -std=c11 \
    -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
    "${ROOT_DIR}/tests/suites/runner_c_worker_harness/harness.c" -o "${HARNESS}" \
    >>"${PW_TEST_ARTIFACTS}/build.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/build.log" >&2
  test_fail "worker harness build failed"
fi
test_step run "unmodified worker must pass; environment and descriptor leaks must be diagnosed"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/runner_exec_inheritance/opt_in/mutations.py" \
    "${PW_TEST_ARTIFACTS}" "${HELPER}" "${HARNESS}" \
    >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assert.log" >&2
  test_fail "mutation controls failed; see per-variant artifacts"
fi
test_pass "baseline worker accepted; deliberate environment and descriptor leaks rejected"
