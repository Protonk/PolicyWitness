#!/usr/bin/env bash
# Build the pre-touch investigation's equipment into a scratch directory:
#   records/performance/pretouch/build.sh [OUT_DIR]   (default .tmp/pretouch-build)
# Produces pretouch_child, pretouch_harness and six copies of the test
# harness (touch/notouch x deny-default policy version 1/2/3) compiled against
# the current ABI header, then runs each once so the first-exec scan is not
# charged to a measured unit. Writes build.json with hashes and tool versions.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SRC="${ROOT}/records/performance/pretouch"
OUT="${1:-${ROOT}/.tmp/pretouch-build}"
WORKER="${ROOT}/dist/PolicyWitness.app/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner"
mkdir -p "${OUT}"
CC=(/usr/bin/xcrun --sdk macosx clang -Wall -Wextra -Werror -O2 -std=c11)

"${CC[@]}" "${SRC}/child.c" -lsandbox -o "${OUT}/pretouch_child"
"${CC[@]}" "${SRC}/harness.c" -o "${OUT}/pretouch_harness"
"${ROOT}/tests/lib/python.sh" "${SRC}/patch_harness.py" "${OUT}/variants" >/dev/null
for v in touch_v1 touch_v2 touch_v3 notouch_v1 notouch_v2 notouch_v3; do
  "${CC[@]}" -I "${ROOT}/controller/tools/pw_probe_runner" -I "${ROOT}/tests/fixtures/worker_lifecycle" \
    "${OUT}/variants/harness_${v}.c" -o "${OUT}/harness_${v}"
done

# The fixture restates the production region size; refuse a disagreement.
WORKER_REGION="$("${WORKER}" --version | sed -n 's/.*region_bytes=\([0-9]*\).*/\1/p')"
CHILD_REGION="$("${OUT}/pretouch_child" --version | sed -n 's/.*region_bytes=\([0-9]*\).*/\1/p')"
if [[ "${WORKER_REGION}" != "${CHILD_REGION}" ]]; then
  echo "refused: worker region_bytes ${WORKER_REGION} != fixture ${CHILD_REGION}" >&2
  exit 1
fi

# First exec of each new file, so Gatekeeper's scan precedes measurement.
"${OUT}/pretouch_harness" --version >/dev/null
for v in touch_v1 touch_v2 touch_v3 notouch_v1 notouch_v2 notouch_v3; do
  "${OUT}/harness_${v}" >/dev/null 2>&1 || true
done

{
  echo '{'
  echo "  \"clang\": \"$(/usr/bin/xcrun --sdk macosx clang --version | head -1)\","
  echo "  \"sdk\": \"$(/usr/bin/xcrun --sdk macosx --show-sdk-path)\","
  echo "  \"sdk_version\": \"$(/usr/bin/xcrun --sdk macosx --show-sdk-version)\","
  echo "  \"worker_version_line\": \"$("${WORKER}" --version)\","
  echo '  "sha256": {'
  first=1
  for f in "${SRC}"/child.c "${SRC}"/harness.c "${SRC}"/pretouch_shared.h "${SRC}"/patch_harness.py \
           "${ROOT}/tests/suites/runner_c_worker_harness/harness.c" \
           "${ROOT}/controller/tools/pw_probe_runner/pw_probe_runner_abi.h" "${WORKER}" \
           "${OUT}"/pretouch_child "${OUT}"/pretouch_harness "${OUT}"/harness_*_v? "${OUT}"/variants/*.diff; do
    [[ ${first} -eq 1 ]] || echo ','
    first=0
    printf '    "%s": "%s"' "${f#${ROOT}/}" "$(/usr/bin/shasum -a 256 "${f}" | cut -d' ' -f1)"
  done
  echo
  echo '  }'
  echo '}'
} > "${OUT}/build.json"
echo "${OUT}"
