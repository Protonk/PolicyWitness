#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_c_worker_harness authority_binding
mkdir -p "${PW_TEST_SCRATCH}"
test_step build "compile the production recipient with a counted consume boundary"
test_run_logged "${PW_TEST_ARTIFACTS}/build.log" "authority binding control failed to compile" \
  /usr/bin/xcrun --sdk macosx clang -Wall -Wextra -Werror -Wno-deprecated-declarations -O2 -std=c11 \
  "${ROOT_DIR}/tests/fixtures/extension_controls/authority_binding.c" -lsandbox -o "${PW_TEST_SCRATCH}/authority-binding"
test_step run "reject wrong associations; bind delayed answers and immutable payloads to their operations"
test_run_logged "${PW_TEST_ARTIFACTS}/controls.log" "authority binding controls failed" "${PW_TEST_SCRATCH}/authority-binding"
test_pass "assigned deliveries, delayed answers, payload ownership and host settlement observed independently"
