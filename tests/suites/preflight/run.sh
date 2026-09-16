#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

if test_selected codesign.preflight; then
bash "${ROOT_DIR}/tests/suites/preflight/preflight.sh"
fi

if test_selected signed_artifact_controls; then
test_begin preflight signed_artifact_controls
test_step signing "inspect intact, damaged, and re-signed disposable app copies"
test_require_pw
SIGNING_IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "${SIGNING_IDENTITY}" ]] || test_fail "matching signing identity required"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "signed artifact controls failed" \
  "${ROOT_DIR}/tests/suites/preflight/check_signed_artifacts.py" \
  "${PW_APP_DIR}" "${PW_TEST_ARTIFACTS}" "${SIGNING_IDENTITY}"
test_pass "real signatures and manifest hashes independently reject corrupted copies"
fi
