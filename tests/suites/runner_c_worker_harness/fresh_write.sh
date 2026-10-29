#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_c_worker_harness fresh_write
test_step build "compile production fresh-write paths with independent native substitutions"
if ! /usr/bin/xcrun --sdk macosx clang -Wall -Wextra -Werror -Wno-deprecated-declarations \
    -O2 -std=c11 "${ROOT_DIR}/tests/fixtures/extension_controls/write_control.c" \
    -lsandbox -o "${PW_TEST_ARTIFACTS}/write-control" >"${PW_TEST_ARTIFACTS}/build.log" 2>&1; then
  test_fail "fresh-write native control failed to compile"
fi
test_step run "preserve call ordering, native failures, short writes and unattempted evidence"
if ! "${PW_TEST_ARTIFACTS}/write-control" >"${PW_TEST_ARTIFACTS}/controls.log" 2>&1; then
  test_fail "fresh-write native controls failed"
fi
test_pass "15 production fresh-write native controls passed"
