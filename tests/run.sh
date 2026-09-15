#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Source-time assertion guard has no filesystem side effects.
source "${ROOT_DIR}/tests/lib/testlib.sh"
exec /usr/bin/python3 -B "${ROOT_DIR}/tests/lib/test_cli.py" "$@"
