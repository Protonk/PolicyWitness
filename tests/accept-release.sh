#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${ROOT_DIR}/tests/lib/python_start.sh"
source "${ROOT_DIR}/tests/lib/testlib.sh"
exec "${PW_PYTHON}" -B "${ROOT_DIR}/tests/lib/release_accept.py" "$@"
