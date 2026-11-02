#!/bin/bash
# Run a Python helper script as the entry points do: the pinned interpreter, checked
# and probed, started directly with -B -S so the /usr/bin/python3 shim and the
# interpreter's site-packages cannot change what the helper or its children see.
#   tests/lib/python.sh SCRIPT [ARG...]
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/python_start.sh"
pw_python_start || exit 2
pw_python_probe || exit 2
exec "${PW_PYTHON}" -B -S "$@"
