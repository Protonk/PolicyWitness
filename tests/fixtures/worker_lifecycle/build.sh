#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUTPUT="${1:?usage: build.sh <output binary>}"

# Every output enters the warm-up inventory where it is compiled, with the
# status it must exit with when run with no arguments and stdin at EOF.
WARM_UP=()
compile_output() {
  local status="$1" output="$2"
  shift 2
  /usr/bin/xcrun --sdk macosx clang "$@" -o "${output}"
  WARM_UP+=("${output}" "${status}")
}

compile_output 92 "${OUTPUT}.issuer" -std=c11 -Wall -Wextra -Wno-deprecated-declarations -O2 \
  -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
  "${ROOT_DIR}/controller/tools/pw_probe_runner/pw_extension_issuer.c" -lsandbox
compile_output 90 "${OUTPUT}" -std=c11 -Wall -Wextra -Werror -O2 \
  -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
  "${ROOT_DIR}/tests/fixtures/worker_lifecycle/worker.c" -lsandbox
compile_output 2 "${OUTPUT}.apply-failure" -std=c11 -Wall -Wextra -Wno-deprecated-declarations -O2 \
  -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
  "${ROOT_DIR}/tests/fixtures/worker_lifecycle/apply_failure.c" -lsandbox
for control in CREATE SET; do
  compile_output 2 "${OUTPUT}.params-${control}" -std=c11 -Wall -Wextra -Wno-deprecated-declarations -O2 \
    -DPW_CONTROL_${control} -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
    "${ROOT_DIR}/tests/fixtures/worker_lifecycle/apply_failure.c" -lsandbox
done
compile_output 0 "${OUTPUT}.worker-limits" -std=c11 -Wall -Wextra -Wno-deprecated-declarations -O2 \
  "${ROOT_DIR}/tests/suites/runner_abi_layout/worker_limits.c" -lsandbox
compile_output 2 "${OUTPUT}.map-failure" -std=c11 -Wall -Wextra -Wno-deprecated-declarations -O2 \
  -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
  "${ROOT_DIR}/tests/fixtures/worker_lifecycle/map_failure.c" -lsandbox
compile_output 2 "${OUTPUT}.read-failure" -std=c11 -Wall -Wextra -Wno-deprecated-declarations -O2 \
  -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
  "${ROOT_DIR}/tests/fixtures/worker_lifecycle/policy_read_failure.c" -lsandbox
compile_output 90 "${OUTPUT}.validator" -std=c11 -Wall -Wextra -Werror -O2 \
  "${ROOT_DIR}/tests/fixtures/worker_lifecycle/validator.c"

compile_output 90 "${OUTPUT}.identity-mismatch" -std=c11 -Wall -Wextra -Werror -O2 -DPW_MISMATCHED_IDENTITY \
  -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
  "${ROOT_DIR}/tests/fixtures/worker_lifecycle/worker.c" -lsandbox
for suffix in clock-failure clock-failure-later clock-phase2 clock-sticky clock-expire2 clock-arith \
    clock-setup-failure clock-zero-factor clock-unrepresentable; do
  case "$suffix" in
    clock-failure) flags=(-DPW_CLOCK_BACKWARDS_STAGE=PW_CLOCK_PROCEED_START -DPW_CLOCK_BACKWARDS_READ=1) ;;
    clock-failure-later) flags=(-DPW_CLOCK_BACKWARDS_STAGE=PW_CLOCK_PROCEED_OBSERVE -DPW_CLOCK_BACKWARDS_READ=1) ;;
    clock-phase2) flags=(-DPW_CLOCK_BACKWARDS_STAGE=PW_CLOCK_PROCEED_START -DPW_CLOCK_BACKWARDS_READ=2 -DPW_CLOCK_PHASE_GATE) ;;
    clock-sticky) flags=(-DPW_CLOCK_BACKWARDS_STAGE=PW_CLOCK_EXEC_OBSERVE -DPW_CLOCK_BACKWARDS_READ=1) ;;
    clock-expire2) flags=(-DPW_CLOCK_EXPIRE_SECOND_PHASE -DPW_CLOCK_PHASE_GATE) ;;
    clock-arith) flags=(-DPW_CLOCK_EXEC_NEAR_CUTOFF) ;;
    clock-setup-failure) flags=(-DPW_CLOCK_SETUP_FAILURE) ;;
    clock-zero-factor) flags=(-DPW_CLOCK_ZERO_FACTOR) ;;
    clock-unrepresentable) flags=(-DPW_CLOCK_UNREPRESENTABLE) ;;
  esac
  compile_output 2 "${OUTPUT}.${suffix}" -std=c11 -Wall -Wextra -Wno-deprecated-declarations -O2 "${flags[@]}" \
    -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
    "${ROOT_DIR}/tests/fixtures/worker_lifecycle/clock_failure.c" -lsandbox
done

# Execute every output once with no arguments, stdin at EOF and only the
# standard descriptors open, so each exits at its first check. The first exec
# of a newly built file can take several hundred milliseconds, a substantial
# part of the fixture workers' 1,000 ms readiness wait, so tests must not be
# the first to execute a fixture. An unexpected status, a timeout or a launch
# error is reported and the remaining outputs still run; the build then fails,
# so its callers stop before the tests. Elapsed time is diagnostic only; it and
# the timeout use time.monotonic, which does not advance during system sleep.
/usr/bin/python3 -B -I - "${WARM_UP[@]}" <<'PY'
import subprocess, sys, time
inventory = sys.argv[1:]
failures = 0
for path, expected in zip(inventory[0::2], inventory[1::2]):
    start = time.monotonic()
    try:
        status = subprocess.run([path], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, timeout=30).returncode
    except subprocess.TimeoutExpired:
        status = 'timeout'
    except OSError as exc:
        status = f'launch error ({exc.strerror})'
    line = f'warm {path.rsplit("/", 1)[-1]}: rc={status} {int((time.monotonic() - start) * 1000)} ms'
    if str(status) != expected:
        failures += 1
        line += f'; expected rc={expected}'
    print(line)
if failures:
    print(f'warm-up failed for {failures} of {len(inventory) // 2} outputs')
    sys.exit(1)
PY
