#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

# Opt-in: installs an owned, disposable BYOXPC runner copy (launchd, GUI
# session, Developer ID) and reads the dossier of a run selected through it.
test_begin witness_contract dossier_witness_byoxpc
test_require_pw
SESSION_TOOL="${ROOT_DIR}/tests/fixtures/byoxpc/session.py"
cleanup() {
  local status=$?
  trap - EXIT
  /usr/bin/python3 "${SESSION_TOOL}" cleanup "${PW_BIN}" "${PW_TEST_ARTIFACTS}/session.json" || status=1
  exit "${status}"
}
trap cleanup EXIT
IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "${IDENTITY}" ]] || test_fail "BYOXPC setup requires a matching Developer ID identity"
test_step install "copy, sign, install and verify an owned BYOXPC runner"
test_check_python "${PW_TEST_ARTIFACTS}/setup.log" "BYOXPC setup failed" \
  "${SESSION_TOOL}" install "${PW_BIN}" "${PW_APP_DIR}" "${PW_TEST_ARTIFACTS}" "${PW_TEST_ARTIFACTS}/runner_env.json" "${IDENTITY}"
test_step run "the dossier of a run selected through the installed runner: provenance, bundle-local binaries hashed against the shipped baselines"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "BYOXPC dossier witness failed" \
  "${ROOT_DIR}/tests/suites/witness_contract/check_dossier.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}/byoxpc" \
  --byoxpc "${PW_TEST_ARTIFACTS}/runner_env.json" --session "${PW_TEST_ARTIFACTS}/session.json"
test_pass "the BYOXPC selection's dossier reports the installed bundle's binaries and hashes against the shipped baselines" "{}"
