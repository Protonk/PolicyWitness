#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUTPUT="${1:?usage: build.sh <output binary>}"
mkdir -p "$(dirname "${OUTPUT}")"
set -x
exec /usr/bin/xcrun --sdk macosx clang -Wall -Wextra -Werror -O2 -g -std=c11 \
  -fno-builtin-malloc -fno-builtin-free -mmacosx-version-min=26.0 \
  "${ROOT_DIR}/tests/fixtures/sandbox_extensions/native.c" -lsandbox -o "${OUTPUT}"
