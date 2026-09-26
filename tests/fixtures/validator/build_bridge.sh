#!/usr/bin/env bash
set -euo pipefail
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT="${1:?expected output executable}"
mkdir -p "$(dirname "${OUTPUT}")"
xcrun --sdk macosx clang -Wall -Wextra -Werror -O2 -fobjc-arc \
  "${SOURCE_DIR}/bridge.m" -framework Foundation -lsandbox -o "${OUTPUT}"
