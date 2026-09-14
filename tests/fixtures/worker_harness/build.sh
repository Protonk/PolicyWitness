#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUTPUT="${1:?usage: build.sh <output binary>}"
mkdir -p "$(dirname "${OUTPUT}")"
exec /usr/bin/xcrun --sdk macosx clang -Wall -Wextra -Werror -O2 -std=c11 \
  -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
  "${ROOT_DIR}/tests/suites/runner_c_worker_harness/harness.c" -o "${OUTPUT}"
