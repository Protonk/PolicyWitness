#!/usr/bin/env bash
set -euo pipefail
FIXTURE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT="${1:?usage: build.sh <output binary>}"
mkdir -p "$(dirname "${OUTPUT}")"
exec /usr/bin/xcrun --sdk macosx clang -Wall -Wextra -Werror -O2 -std=c11 \
  "${FIXTURE_DIR}/helper.c" -o "${OUTPUT}"
