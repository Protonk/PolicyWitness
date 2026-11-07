#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"
test_begin runner_c_worker_harness native_pause
PRIMITIVE="${PW_NATIVE_PAUSE_PRIMITIVE:-nanosleep}"
[[ "${PRIMITIVE}" == nanosleep || "${PRIMITIVE}" == mach_wait_until ]] || test_fail "unknown pause primitive"
printf '%s\n' "${PRIMITIVE}" >"${PW_TEST_ARTIFACTS}/primitive.txt"
PROBE="${PW_TEST_ARTIFACTS}/native-pause"
test_step build "compile a fresh-process first-pause applicability probe"
test_run_logged "${PW_TEST_ARTIFACTS}/build.log" "native pause build failed" \
  /usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Werror -O2 \
  -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
  "${ROOT_DIR}/tests/suites/runner_c_worker_harness/opt_in/native_pause.c" -lsandbox -o "${PROBE}"
cp "${ROOT_DIR}/tests/suites/runner_c_worker_harness/opt_in/native_pause.c" "${PW_TEST_ARTIFACTS}/"
cp "${ROOT_DIR}/tests/suites/runner_c_worker_harness/check_native_pause.py" "${PW_TEST_ARTIFACTS}/"
cp -R "${ROOT_DIR}/controller/tools/pw_probe_runner" "${PW_TEST_ARTIFACTS}/worker-source"
{
  /usr/bin/git -C "${ROOT_DIR}" rev-parse HEAD
  /usr/bin/git -C "${ROOT_DIR}" status --short
  /usr/bin/uname -a
  /usr/bin/sw_vers
  /usr/bin/pmset -g batt
  /usr/sbin/sysctl hw.model hw.ncpu hw.memsize
  /usr/bin/xcrun --sdk macosx --show-sdk-version
  /usr/bin/xcrun clang --version
  /usr/bin/lipo -archs "${PROBE}"
} >"${PW_TEST_ARTIFACTS}/platform.txt" 2>&1
APP="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
if [[ -d "${APP}/Contents/Resources/Evidence" ]]; then
  cp -R "${APP}/Contents/Resources/Evidence" "${PW_TEST_ARTIFACTS}/baseline-app-evidence"
  cp "${APP}/Contents/XPCServices/PWRunner.xpc/Contents/Resources/worker-equipment.json" "${PW_TEST_ARTIFACTS}/"
  "${APP}/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner" --version >"${PW_TEST_ARTIFACTS}/worker-version.txt"
fi
test_step installed "retain installed call paths without warming the measured children"
set +e
/usr/bin/xcrun lldb --batch \
  -o 'image list libsystem_c.dylib libsystem_kernel.dylib libsystem_pthread.dylib' \
  -o 'disassemble -n nanosleep' -o 'disassemble -n __semwait_signal' \
  -o 'disassemble -n _init_clock_port' -o 'disassemble -n _libc_initializer' \
  -o 'disassemble -n _libc_fork_child' -o 'disassemble -n pthread_testcancel' \
  -o 'disassemble -n mach_wait_until' "${PROBE}" >"${PW_TEST_ARTIFACTS}/installed-disassembly.txt" 2>&1
echo "$?" >"${PW_TEST_ARTIFACTS}/installed-disassembly.status"
set -e
START="$(/bin/date '+%Y-%m-%d %H:%M:%S')"
test_step measure "three fresh children per policy and mode; first pause, interruption, CPU and reaping"
for repeat in 1 2 3; do
  for policy in allow_default deny_default v2_original unapplied; do
    for mode in ordinary interrupted; do
      "${PROBE}" "${policy}" "${mode}" "${PRIMITIVE}" >>"${PW_TEST_ARTIFACTS}/results.ndjson" 2>>"${PW_TEST_ARTIFACTS}/probe.stderr"
    done
  done
done
test_step diagnostics "separate known-denial control and bounded supplemental log query"
"${PROBE}" deny_default known_denial "${PRIMITIVE}" >"${PW_TEST_ARTIFACTS}/known-denial.json" 2>>"${PW_TEST_ARTIFACTS}/probe.stderr"
# Include the final partial second; a truncated end excludes the control just
# issued. Logging may still omit it: no positive control is assumed observed.
END="$(/bin/date -v+1S '+%Y-%m-%d %H:%M:%S')"
set +e
/usr/bin/log show --start "${START}" --end "${END}" --style ndjson \
  --predicate 'process == "kernel" AND eventMessage CONTAINS "native-pause("' \
  >"${PW_TEST_ARTIFACTS}/deny-log.ndjson" 2>"${PW_TEST_ARTIFACTS}/deny-log.stderr"
echo "$?" >"${PW_TEST_ARTIFACTS}/deny-log.status"
set -e
printf '%s\n' "start=${START}" "end=${END}" >"${PW_TEST_ARTIFACTS}/log-window.txt"
/usr/bin/pmset -g batt >"${PW_TEST_ARTIFACTS}/power-after.txt"
test_step assert "required observations qualify independently of supplemental log availability"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "native pause applicability failed" \
  "${ROOT_DIR}/tests/suites/runner_c_worker_harness/check_native_pause.py" \
  "${PW_TEST_ARTIFACTS}/results.ndjson" "${PW_TEST_ARTIFACTS}/deny-log.status"
test_pass "first post-apply pause, idle intervals, interruption and independent reaping observed"
