#!/bin/bash
# Run a command under tests/.checkout.lock: the supported entrypoint.
#
#   tests/lib/checkout_lock.sh [--root CHECKOUT] -- COMMAND [ARG...]
#
# The system /usr/bin/python3 is a launcher shim that inserts SDKROOT, CPATH,
# LIBRARY_PATH and MANPATH into the environment of everything it starts, and
# the interpreter may coerce LC_CTYPE, so once Python runs the caller's own
# state for these variables is lost. Before Python starts, shell builtins
# record each one's set or unset state and exact value here and pass them to
# checkout_lock.py as arguments; nothing is written. The owner binds them to
# its acquisition, restores them for the command it launches and hands them
# to every nested admission. A launcher nested inside an owned command uses
# its owner's requests instead. See checkout_lock.py for the protocol.
set -euo pipefail
LOCK_LIBRARY="${BASH_SOURCE[0]%/*}"
if [[ "${LOCK_LIBRARY}" == "${BASH_SOURCE[0]}" ]]; then
  LOCK_LIBRARY="."
fi
LOCK_REQUESTS=()
for LOCK_REQUEST_NAME in SDKROOT CPATH LIBRARY_PATH MANPATH LC_CTYPE; do
  if [[ -n "${!LOCK_REQUEST_NAME+set}" ]]; then
    LOCK_REQUESTS+=(--request "${LOCK_REQUEST_NAME}=${!LOCK_REQUEST_NAME}")
  else
    LOCK_REQUESTS+=(--request-unset "${LOCK_REQUEST_NAME}")
  fi
done
exec /usr/bin/python3 -B "${LOCK_LIBRARY}/checkout_lock.py" "${LOCK_REQUESTS[@]}" "$@"
