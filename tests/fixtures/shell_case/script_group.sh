#!/usr/bin/env bash
# Invoke the real helper with both caller errexit settings and literal paths.
set -u
if [[ "${CONTROL_ERREXIT}" == 1 ]]; then set -e; fi
source "$1"
shift
before="$-"
if test_run_scripts "$@"; then status=0; else status=$?; fi
[[ "$-" == "${before}" ]] || exit 90
exit "${status}"
