#!/usr/bin/env bash
# Compile the exit-status helpers the comparison matrix rows spawn: <output>
# exits 0 (helper_true, helper_locked) and <output>.exit1 exits 1 (helper_false).
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
OUTPUT="${1:?usage: build.sh <output binary>}"
SRC="${ROOT_DIR}/tests/fixtures/comparison/helper_status.c"
/usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Werror -O2 -DPW_EXIT_STATUS=0 "${SRC}" -o "${OUTPUT}"
/usr/bin/xcrun --sdk macosx clang -std=c11 -Wall -Wextra -Werror -O2 -DPW_EXIT_STATUS=1 "${SRC}" -o "${OUTPUT}.exit1"
