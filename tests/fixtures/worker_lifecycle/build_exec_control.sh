#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUTPUT="${1:?usage: build_exec_control.sh <output>}"
exec /usr/bin/xcrun --sdk macosx clang -Wall -Wextra -Werror -O2 -std=c11 \
  -I "${ROOT_DIR}/controller/tools/pw_probe_runner" \
  "${ROOT_DIR}/tests/fixtures/worker_lifecycle/exec_control.c" -lsandbox -o "${OUTPUT}"
