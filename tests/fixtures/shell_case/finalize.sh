#!/usr/bin/env bash
# No errexit: test_fail must terminate the process itself. The receipt after
# the call independently proves whether a public finalizer returned.
set -u
source "$1"
shift
test_begin "${CONTROL_SUITE}" "${CONTROL_ID}"
"${CONTROL_FINALIZER}" "$@"
status=$?
printf '%s\n' "${status}" >"${CONTROL_RETURN_RECEIPT}"
exit "${status}"
