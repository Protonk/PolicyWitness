#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
exec /usr/bin/python3 -B "${ROOT}/tests/fixtures/dispatcher/cancellation.py" "$@"
