#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_c_worker_harness arm_wait
PRIMITIVE="${PW_ARM_WAIT_PRIMITIVE:-wfe}"
[[ "${PRIMITIVE}" == wfe || "${PRIMITIVE}" == wfet ]] || test_fail "unknown ARM primitive"
[[ -n "${PW_ARM_WAIT_GATE:-}" && ! -e "${PW_ARM_WAIT_GATE}" ]] || test_fail "a fresh PW_ARM_WAIT_GATE is required"
PROBE="${PW_TEST_ARTIFACTS}/arm-wait"
test_run_logged "${PW_TEST_ARTIFACTS}/build.log" "ARM screen build failed" \
 /usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Werror -O2 -arch arm64 -mmacosx-version-min=26.0 \
 -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
 "${ROOT_DIR}/tests/suites/runner_c_worker_harness/opt_in/arm_wait.c" -lsandbox -o "${PROBE}"
cp "${ROOT_DIR}/tests/suites/runner_c_worker_harness/opt_in/arm_wait.c" "${PW_TEST_ARTIFACTS}/"
cp "${ROOT_DIR}/tests/suites/runner_c_worker_harness/check_arm_wait.py" "${PW_TEST_ARTIFACTS}/"
cp "${ROOT_DIR}/tests/suites/runner_c_worker_harness/arm_wait_driver.py" "${PW_TEST_ARTIFACTS}/"
cp -R "${ROOT_DIR}/controller/tools/pw_probe_runner" "${PW_TEST_ARTIFACTS}/worker-source"
{
 /usr/bin/git -C "${ROOT_DIR}" rev-parse HEAD
 /usr/bin/git -C "${ROOT_DIR}" status --short
 /usr/bin/uname -a
 /usr/bin/sw_vers
 /usr/bin/pmset -g batt
 /usr/sbin/sysctl hw.model hw.ncpu hw.optional.arm.FEAT_WFxT hw.optional.arm.FEAT_ECV
 /usr/bin/xcrun --sdk macosx --show-sdk-version
 /usr/bin/xcrun clang --version
 /usr/bin/lipo -archs "${PROBE}"
} >"${PW_TEST_ARTIFACTS}/platform.txt" 2>&1
/usr/bin/xcrun otool -tvV "${PROBE}" >"${PW_TEST_ARTIFACTS}/disassembly.txt"
test_step screen "prepare identities, await the coordinator's gate, then execute twelve first-use children"
test_check_python "${PW_TEST_ARTIFACTS}/driver.log" "ARM screen equipment failed" \
 "${ROOT_DIR}/tests/suites/runner_c_worker_harness/arm_wait_driver.py" \
 "${PROBE}" "${PRIMITIVE}" "${PW_TEST_ARTIFACTS}" "${PW_ARM_WAIT_GATE}"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "ARM first-use screen failed" \
 "${ROOT_DIR}/tests/suites/runner_c_worker_harness/check_arm_wait.py" "${PW_TEST_ARTIFACTS}/results.ndjson"
test_pass "first-use ARM instructions and autonomous cutoff observed; no deployment or integrated protocol credit"
