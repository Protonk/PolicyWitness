#!/usr/bin/env bash
# Compile the fixture Mach-O stubs the dispatcher and preflight controls lay
# into fake bundles: <output> imports nothing from libsandbox (the valid host
# and the stand-in for every other executable); <output>.imports-sandbox calls
# sandbox_check (the host-invariance control); <output>.imports-clock calls
# clock_gettime and <output>.continuous-clock calls mach_continuous_time (the
# worker clock controls); <output>.controller is the runnable stub controller
# that records its own invocation. Each is compiled for arm64 explicitly: the
# stand-ins must be the output target (a thin arm64 Mach-O for macOS) whatever
# architecture the compiler or the calling process defaults to. Four more stand
# outside it for the inspector's output target controls: <output>.x86_64,
# <output>.universal (arm64 and x86_64), <output>.one-slice-fat (the clean arm64
# stub in a fat container of one slice) and <output>.x86_64.dSYM, the dSYM
# companion of an x86_64 executable, which is debug data and not code.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUTPUT="${1:?usage: build.sh <output binary>}"
SRC="${ROOT_DIR}/tests/fixtures/dispatcher"
/usr/bin/xcrun --sdk macosx clang -arch arm64 -std=c11 -Wall -Wextra -Werror -O2 \
  "${SRC}/host_clean.c" -o "${OUTPUT}"
/usr/bin/xcrun --sdk macosx clang -arch arm64 -std=c11 -Wall -Wextra -Werror -O2 \
  "${SRC}/host_imports_sandbox.c" -lsandbox -o "${OUTPUT}.imports-sandbox"
/usr/bin/xcrun --sdk macosx clang -arch arm64 -std=c11 -Wall -Wextra -Werror -O2 \
  "${SRC}/worker_imports_clock.c" -o "${OUTPUT}.imports-clock"
/usr/bin/xcrun --sdk macosx clang -arch arm64 -std=c11 -Wall -Wextra -Werror -O2 \
  "${SRC}/worker_continuous_clock.c" -o "${OUTPUT}.continuous-clock"
/usr/bin/xcrun --sdk macosx clang -arch arm64 -std=c11 -Wall -Wextra -Werror -O2 \
  "${SRC}/controller_stub.c" -o "${OUTPUT}.controller"
/usr/bin/xcrun --sdk macosx clang -arch x86_64 -std=c11 -Wall -Wextra -Werror -O2 \
  "${SRC}/host_clean.c" -o "${OUTPUT}.x86_64"
/usr/bin/xcrun --sdk macosx clang -arch arm64 -arch x86_64 -std=c11 -Wall -Wextra -Werror -O2 \
  "${SRC}/host_clean.c" -o "${OUTPUT}.universal"
# The linker signs only arm64 output ad hoc; the others are signed ad hoc here, so
# every stand-in carries the same signature facts and only its architecture differs.
/usr/bin/codesign --force -s - "${OUTPUT}.x86_64" "${OUTPUT}.universal"
/usr/bin/lipo -create "${OUTPUT}" -output "${OUTPUT}.one-slice-fat"
/usr/bin/xcrun --sdk macosx clang -arch x86_64 -g -std=c11 -Wall -Wextra -Werror -O2 \
  -c "${SRC}/host_clean.c" -o "${OUTPUT}.x86_64-debug.o"
/usr/bin/xcrun --sdk macosx clang -arch x86_64 "${OUTPUT}.x86_64-debug.o" -o "${OUTPUT}.x86_64-debug"
rm -rf "${OUTPUT}.x86_64.dSYM"
/usr/bin/xcrun dsymutil "${OUTPUT}.x86_64-debug" -o "${OUTPUT}.x86_64.dSYM"
