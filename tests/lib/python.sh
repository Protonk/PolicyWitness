#!/bin/bash
# Run a Python helper as the entry points do: the selected developer directory's
# python3 started directly with -B, so the /usr/bin/python3 shim cannot change
# the environment the helper's children inherit.
#   tests/lib/python.sh SCRIPT [ARG...]
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/python_start.sh"
exec "${PW_PYTHON}" -B "$@"
