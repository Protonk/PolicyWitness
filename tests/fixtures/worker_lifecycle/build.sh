#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUTPUT="${1:?usage: build.sh <output binary>}"
/usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Werror -O2 \
  -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
  "${ROOT_DIR}/tests/fixtures/worker_lifecycle/worker.c" -lsandbox -o "${OUTPUT}"
/usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Wno-deprecated-declarations -O2 \
  -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
  "${ROOT_DIR}/tests/fixtures/worker_lifecycle/apply_failure.c" -lsandbox -o "${OUTPUT}.apply-failure"
for control in CREATE SET; do
  /usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Wno-deprecated-declarations -O2 \
    -DPW_CONTROL_${control} -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
    "${ROOT_DIR}/tests/fixtures/worker_lifecycle/apply_failure.c" -lsandbox -o "${OUTPUT}.params-${control}"
done
/usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Wno-deprecated-declarations -O2 \
  "${ROOT_DIR}/tests/suites/runner_abi_layout/worker_limits.c" -lsandbox -o "${OUTPUT}.worker-limits"
/usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Wno-deprecated-declarations -O2 \
  -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
  "${ROOT_DIR}/tests/fixtures/worker_lifecycle/map_failure.c" -lsandbox -o "${OUTPUT}.map-failure"
/usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Werror -O2 \
  "${ROOT_DIR}/tests/fixtures/worker_lifecycle/validator.c" -o "${OUTPUT}.validator"

/usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Werror -O2 -DPW_MISMATCHED_IDENTITY \
  -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
  "${ROOT_DIR}/tests/fixtures/worker_lifecycle/worker.c" -lsandbox -o "${OUTPUT}.identity-mismatch"
for suffix in clock-failure clock-failure-later; do
  flags=(-DPW_CLOCK_FAIL_INITIAL)
  if [[ "$suffix" == clock-failure-later ]]; then flags+=(-DPW_CLOCK_FAIL_LATER); fi
  /usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Wno-deprecated-declarations -O2 "${flags[@]}" \
    -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
    "${ROOT_DIR}/tests/fixtures/worker_lifecycle/clock_failure.c" -lsandbox -o "${OUTPUT}.${suffix}"
done

# Exec every fixture once with no arguments, stdin at EOF and only the standard
# descriptors open, so each exits at its first check. Gatekeeper evaluates a
# newly linked executable on its first exec (syspolicyd's first-launch scan,
# about 200 ms on a fresh macOS 26 machine); charged to a driver test with a
# 150 ms I/O deadline, that cost fails the test. The status and the elapsed time
# are reported, not checked: the tests own every behavioral assertion.
/usr/bin/python3 -B -I - "${OUTPUT}" "${OUTPUT}".* <<'PY'
import subprocess, sys, time
for path in sys.argv[1:]:
    start = time.monotonic()
    try:
        status = subprocess.run([path], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, timeout=30).returncode
    except subprocess.TimeoutExpired:
        status = 'timeout'
    print(f'warm {path.rsplit("/", 1)[-1]}: rc={status} {int((time.monotonic() - start) * 1000)} ms')
PY
