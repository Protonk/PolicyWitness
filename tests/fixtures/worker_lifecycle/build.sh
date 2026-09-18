#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUTPUT="${1:?usage: build.sh <output binary>}"
/usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Werror -O2 \
  -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
  "${ROOT_DIR}/tests/fixtures/worker_lifecycle/worker.c" -o "${OUTPUT}"
