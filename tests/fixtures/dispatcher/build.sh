#!/usr/bin/env bash
# Compile the fixture XPC host stubs the dispatcher and preflight controls lay
# into fake bundles: <output> imports nothing from libsandbox (the valid host);
# <output>.imports-sandbox calls sandbox_check (the host-invariance control).
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUTPUT="${1:?usage: build.sh <output binary>}"
SRC="${ROOT_DIR}/tests/fixtures/dispatcher"
/usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Werror -O2 \
  "${SRC}/host_clean.c" -o "${OUTPUT}"
/usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Werror -O2 \
  "${SRC}/host_imports_sandbox.c" -lsandbox -o "${OUTPUT}.imports-sandbox"
