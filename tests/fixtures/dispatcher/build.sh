#!/usr/bin/env bash
# Compile the fixture Mach-O stubs the dispatcher and preflight controls lay
# into fake bundles: <output> imports nothing from libsandbox (the valid host
# and the stand-in for every other executable); <output>.imports-sandbox calls
# sandbox_check (the host-invariance control); <output>.controller is the
# runnable stub controller that records its own invocation.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUTPUT="${1:?usage: build.sh <output binary>}"
SRC="${ROOT_DIR}/tests/fixtures/dispatcher"
/usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Werror -O2 \
  "${SRC}/host_clean.c" -o "${OUTPUT}"
/usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Werror -O2 \
  "${SRC}/host_imports_sandbox.c" -lsandbox -o "${OUTPUT}.imports-sandbox"
/usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Werror -O2 \
  "${SRC}/controller_stub.c" -o "${OUTPUT}.controller"
