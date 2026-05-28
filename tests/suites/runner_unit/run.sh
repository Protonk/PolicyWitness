#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="runner_unit"
PW_TEST_ID="pwrunner_core_unit_executable"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "swift_run" "build and run PWRunnerCoreTests via SwiftPM"

if ! command -v swift >/dev/null 2>&1; then
  test_skip "swift toolchain not on PATH (install Xcode Command Line Tools)" "{}"
  exit 0
fi

PACKAGE_DIR="${ROOT_DIR}/runner"
if [[ ! -f "${PACKAGE_DIR}/Package.swift" ]]; then
  test_skip "missing runner/Package.swift" "{}"
  exit 0
fi

RUN_LOG="${PW_TEST_ARTIFACTS}/pwrunner_core_tests.log"

set +e
swift run --package-path "${PACKAGE_DIR}" PWRunnerCoreTests >"${RUN_LOG}" 2>&1
RC=$?
set -e

if [[ "${RC}" -ne 0 ]]; then
  # Surface the last few lines of the log inline so the failure is visible
  # in the events stream without needing the artifact path.
  TAIL="$(tail -n 15 "${RUN_LOG}" | sed 's/"/\\"/g; s/\n/ /g')"
  test_fail "PWRunnerCoreTests exited rc=${RC}; tail: ${TAIL}" \
    "{\"log\":\"${RUN_LOG}\"}"
fi

# Parse the summary line ("N/M tests passed") to surface counts in the
# success message.
SUMMARY="$(grep -E '^[0-9]+/[0-9]+ tests passed$' "${RUN_LOG}" | tail -n 1 || true)"
if [[ -z "${SUMMARY}" ]]; then
  test_fail "PWRunnerCoreTests output missing summary line" "{\"log\":\"${RUN_LOG}\"}"
fi

test_pass "${SUMMARY}" "{\"log\":\"${RUN_LOG}\"}"
