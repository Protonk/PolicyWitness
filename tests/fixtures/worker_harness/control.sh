#!/usr/bin/env bash
exec /usr/bin/python3 "${CONTROL_WORKER_DRIVER}" "$(basename "$0")" "$@"
