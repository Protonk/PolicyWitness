#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="source_drift"
PW_TEST_ID="runner_source_manifests_agree"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "diff" "compare runner/ on-disk source set against build.sh and Package.swift"

CHECK_PY="${ROOT_DIR}/tests/suites/source_drift/check.py"
RUN_LOG="${PW_TEST_ARTIFACTS}/check.log"

set +e
/usr/bin/python3 "${CHECK_PY}" >"${RUN_LOG}" 2>&1
RC=$?
set -e

if [[ "${RC}" -ne 0 ]]; then
  TAIL="$(tail -n 20 "${RUN_LOG}" | sed 's/"/\\"/g')"
  test_fail "manifests disagree: ${TAIL}" "{\"log\":\"${RUN_LOG}\"}"
fi

SUMMARY="$(tail -n 1 "${RUN_LOG}")"
test_pass "${SUMMARY}" "{\"log\":\"${RUN_LOG}\"}"
