#!/bin/bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${ROOT_DIR}/tests/lib/python_start.sh"
pw_python_start || exit 2
pw_python_probe || exit 2
exec "${PW_PYTHON}" -B -S "${ROOT_DIR}/tests/lib/pytest_packages.py" "$@"
