#!/usr/bin/env bash
# No errexit: test_fail must terminate the process itself. The receipt after
# the call independently proves whether a public finalizer returned.
set -u
source "$1"
shift
if [[ "${CONTROL_SETUP}" == before_begin ]]; then
  # Supply reporting paths without granting cleanup ownership through test_begin.
  PW_TEST_SUITE="${CONTROL_SUITE}"
  PW_TEST_ID="${CONTROL_ID}"
  PW_TEST_DIR="${CONTROL_CASE_DIR}"
  PW_TEST_REPORT="${PW_TEST_DIR}/report.json"
  PW_TEST_EVENTS_LOCAL="${PW_TEST_DIR}/events.jsonl"
  PW_TEST_ARTIFACTS="${PW_TEST_DIR}/artifacts"
  PW_TEST_SCRATCH="${PW_TEST_DIR}/scratch"
  export PW_TEST_SUITE PW_TEST_ID PW_TEST_DIR PW_TEST_REPORT
  export PW_TEST_EVENTS_LOCAL PW_TEST_ARTIFACTS PW_TEST_SCRATCH
  mkdir -p "${PW_TEST_ARTIFACTS}"
else
  test_begin "${CONTROL_SUITE}" "${CONTROL_ID}"
fi
mkdir -p "${PW_TEST_SCRATCH}/nested" "${CONTROL_OUTSIDE_SCRATCH}"
printf 'temporary\n' >"${PW_TEST_SCRATCH}/nested/build-state"
printf 'evidence\n' >"${PW_TEST_ARTIFACTS}/retained"
printf 'outside\n' >"${CONTROL_OUTSIDE_SCRATCH}/retained"
if [[ "${CONTROL_SETUP}" == reassigned_dir ]]; then
  PW_TEST_DIR="${CONTROL_REASSIGNED_DIR}"
  mkdir -p "${PW_TEST_DIR}/scratch"
  printf 'reassigned\n' >"${PW_TEST_DIR}/scratch/retained"
fi
# Read the exported value and bytes in a child before the finalizer can remove
# them; the Python controller derives the expected path independently.
"${PW_PYTHON}" -B -S -P - "${CONTROL_SETUP_RECEIPT}" <<'PY'
import json
import os
from pathlib import Path
import sys
scratch = Path(os.environ['PW_TEST_SCRATCH'])
Path(sys.argv[1]).write_text(json.dumps({
    'scratch': str(scratch),
    'populated': (scratch / 'nested/build-state').read_text(),
}) + '\n')
PY
PW_TEST_SCRATCH="${CONTROL_OUTSIDE_SCRATCH}"
"${CONTROL_FINALIZER}" "$@"
status=$?
printf '%s\n' "${status}" >"${CONTROL_RETURN_RECEIPT}"
exit "${status}"
