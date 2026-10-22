#!/usr/bin/env bash
set -euo pipefail
FIXTURE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${PW_PYTHON}" -B -S "${FIXTURE_DIR}/command.py" build "${1:?output path}"
