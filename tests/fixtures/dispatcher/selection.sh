#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
exec "${PW_PYTHON}" -B -S "${ROOT}/tests/fixtures/dispatcher/selection.py" "$(basename "$(dirname "$0")")" "$@"
