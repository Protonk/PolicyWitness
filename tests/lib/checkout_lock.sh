#!/bin/bash
# Run a command under tests/.checkout.lock: the supported entrypoint.
#   tests/lib/checkout_lock.sh [--root CHECKOUT] -- COMMAND [ARG...]
# Witness the caller with shell builtins, then start Python directly. 'u'
# means unset; 's' followed by the exact value means set, including empty.
# Each nested front end records its own environment. Nothing restores values.
set -euo pipefail
LOCK_LIBRARY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${LOCK_LIBRARY}/python_start.sh"
for PW_WITNESS_NAME in SDKROOT CPATH LIBRARY_PATH MANPATH LC_CTYPE; do
  if [[ -n "${!PW_WITNESS_NAME+set}" ]]; then
    export "PW_ENV_WITNESS_${PW_WITNESS_NAME}=s${!PW_WITNESS_NAME}"
  else
    export "PW_ENV_WITNESS_${PW_WITNESS_NAME}=u"
  fi
done
unset PW_WITNESS_NAME
exec "${PW_PYTHON}" -B "${LOCK_LIBRARY}/checkout_lock.py" "$@"
