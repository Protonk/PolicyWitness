#!/usr/bin/env bash
# Native applicability of the worker's continuous clock on this machine: the
# production clock helpers in fresh processes under the original version-2
# policy, bare deny-default and allow-default, beside the standalone old-clock
# neighbour. Observations are scoped to the recorded machine and installed
# implementation; missing deny records are not proof of safety.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/case.sh"

SAMPLES="${PW_NATIVE_CLOCK_SAMPLES:-2000000}"
REPEATS=3

test_begin runner_c_worker_harness native_clock
test_step build "compile the production clock helpers into a fresh-process native probe"
PROBE="${PW_TEST_ARTIFACTS}/native-clock"
test_run_logged "${PW_TEST_ARTIFACTS}/build.log" "native clock probe build failed" \
  /usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Werror -O2 \
  -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
  "${ROOT_DIR}/tests/suites/runner_c_worker_harness/opt_in/native_clock.c" -lsandbox -o "${PROBE}"

test_step platform "record the machine, translation state, SDK and Mach-O architectures"
PLATFORM="${PW_TEST_ARTIFACTS}/platform.txt"
{
  echo "uname_m=$(/usr/bin/uname -m)"
  echo "proc_translated=$(/usr/sbin/sysctl -n sysctl.proc_translated 2>/dev/null || echo unavailable)"
  /usr/bin/sw_vers
  echo "sdk_version=$(/usr/bin/xcrun --sdk macosx --show-sdk-version)"
  echo "sdk_build=$(/usr/bin/xcrun --sdk macosx --show-sdk-build-version)"
  echo "clang=$(/usr/bin/xcrun --sdk macosx clang --version | head -1)"
  echo "probe_archs=$(/usr/bin/lipo -archs "${PROBE}")"
  WORKER="${PW_APP_DIR}/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner"
  if [[ -f "${WORKER}" ]]; then echo "worker_archs=$(/usr/bin/lipo -archs "${WORKER}")"; else echo "worker_archs=absent"; fi
} >"${PLATFORM}" 2>&1

# The installed implementation, inspected by a separate process so the
# measured path is not warmed. A selected fallback is retained, not asserted.
test_step installed "disassemble the installed continuous and absolute clocks"
set +e
/usr/bin/xcrun lldb --batch -o 'disassemble -n mach_continuous_time' -o 'disassemble -n mach_absolute_time' \
  "${PROBE}" >"${PW_TEST_ARTIFACTS}/installed-disassembly.txt" 2>&1
echo "status=$?" >>"${PW_TEST_ARTIFACTS}/installed-disassembly.txt"
set -e

test_step measure "fresh processes: production, first-explicit-after-apply and old-clock variants"
START="$(/bin/date '+%Y-%m-%d %H:%M:%S')"
RESULTS="${PW_TEST_ARTIFACTS}/results.ndjson"
: >"${RESULTS}"
for repeat in $(seq 1 "${REPEATS}"); do
  for policy in v2_original deny_default allow_default; do
    for variant in production first_after_apply old_clock; do
      if ! "${PROBE}" "${policy}" "${variant}" "${SAMPLES}" >>"${RESULTS}" 2>>"${PW_TEST_ARTIFACTS}/probe.stderr"; then
        test_fail "native clock probe did not reap its child (${policy} ${variant} repeat ${repeat})" \
          "{\"results\":\"${RESULTS}\"}"
      fi
    done
  done
done

# Kernel deny records for the probe's PIDs, when log access is available.
test_step deny_log "retain available sandbox deny records for the probe processes"
set +e
/usr/bin/log show --start "${START}" --style ndjson \
  --predicate 'process == "kernel" AND eventMessage CONTAINS "native-clock("' \
  >"${PW_TEST_ARTIFACTS}/deny-log.ndjson" 2>"${PW_TEST_ARTIFACTS}/deny-log.stderr"
echo "$?" >"${PW_TEST_ARTIFACTS}/deny-log.status"
set -e

test_step assert "every continuous-clock sample is usable; the old clock is recorded as observed"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "native clock applicability failed" - \
  "${RESULTS}" "${PW_TEST_ARTIFACTS}/deny-log.ndjson" "${PW_TEST_ARTIFACTS}/deny-log.status" <<'PY'
import json, sys
from pathlib import Path
rows = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
assert len(rows) == 27, f'expected 27 fresh-process observations, got {len(rows)}'
pids = []
for row in rows:
    label = f"{row['policy']} {row['variant']} pid={row['pid']}"
    assert row['reaped'] and row['exit_code'] == 0 and row['term_signal'] == 0 and row['finished'] == 1, label + f': {row}'
    assert row['compile_ok'] == 1 and row['apply_rc'] == 0, label + f': application failed: {row}'
    if row['variant'] != 'old_clock':
        assert row['setup_rc'] == 0 and row['numer'] and row['denom'], label + f': timebase setup: {row}'
        assert row['valid'] == row['samples'] and row['rejected'] == 0, label + f': unusable sample: {row}'
        assert row['elapsed_last'] >= row['elapsed_first'], label
    pids.append(row['pid'])
old = [r for r in rows if r['variant'] == 'old_clock']
failures = [r for r in old if r['old_failures']]
denies = []
if Path(sys.argv[3]).read_text().strip() == '0':
    for line in Path(sys.argv[2]).read_text().splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        message = event.get('eventMessage', '')
        if any(f'native-clock({pid})' in message for pid in pids):
            denies.append(message)
summary = {'continuous_samples': sum(r['valid'] for r in rows if r['variant'] != 'old_clock'),
           'timebase': sorted({(r['numer'], r['denom']) for r in rows if r['variant'] != 'old_clock'}),
           'old_clock_runs_with_failure': [(r['policy'], r['pid'], r['old_failures'], r['old_first_errno']) for r in failures],
           'deny_records': len(denies), 'deny_log_status': Path(sys.argv[3]).read_text().strip()}
Path(sys.argv[1]).with_name('summary.json').write_text(json.dumps(summary, indent=2) + '\n')
# The continuous-clock probes must not need a denied path: a deny record for
# a continuous-clock PID is a failure even when every sample validated.
continuous = {r['pid'] for r in rows if r['variant'] != 'old_clock'}
offending = [m for m in denies if any(f'native-clock({pid})' in m for pid in continuous)]
assert not offending, f'continuous-clock probes recorded denials: {offending[:3]}'
print(f"ok: {summary['continuous_samples']} continuous samples usable at {summary['timebase']}; "
      f"old clock failed in {len(failures)} of {len(old)} runs; {len(denies)} deny records (log status {summary['deny_log_status']})")
PY
test_pass "$(tail -1 "${PW_TEST_ARTIFACTS}/assertions.log")" "{\"results\":\"${RESULTS}\"}"
