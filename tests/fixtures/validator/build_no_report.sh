#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUTPUT="${1:?usage: build_no_report.sh <output>}"
exec /usr/bin/xcrun --sdk macosx clang -Wall -O2 -std=c11 \
  -I "${ROOT_DIR}/controller/tools/sb_api_validator" \
  "${ROOT_DIR}/tests/fixtures/validator/no_report.c" -lsandbox -o "${OUTPUT}"
