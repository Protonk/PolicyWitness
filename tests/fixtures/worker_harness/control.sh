#!/usr/bin/env bash
exec "${PW_PYTHON}" -B -S "${CONTROL_WORKER_DRIVER}" "$(basename "$0")" "$@"
