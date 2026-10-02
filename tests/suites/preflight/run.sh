#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/case.sh"

if test_selected release_deadline_controls; then
test_begin preflight release_deadline_controls
test_step deadline "observe real hung commands, retained output, and kernel process exits"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "release deadline controls failed" \
  "${ROOT_DIR}/tests/suites/preflight/check_release_deadline.py" "${PW_TEST_ARTIFACTS}"
test_pass "release deadlines stop stubborn command groups once and preserve raw output"
fi

if test_selected release_controls; then
test_begin preflight release_controls
test_step fixture "build the fixture XPC host stubs"
export PW_DISPATCHER_HOST_FIXTURE="${PW_TEST_ARTIFACTS}/host-fixture"
test_build_fixture "${ROOT_DIR}/tests/fixtures/dispatcher/build.sh" \
  "${PW_DISPATCHER_HOST_FIXTURE}" "${PW_TEST_ARTIFACTS}/host-fixture-build.log"
test_step release "exercise uncertain Apple replies and final-archive acceptance using independent tools"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "release controls failed" \
  "${ROOT_DIR}/tests/suites/preflight/check_release.py" "${PW_TEST_ARTIFACTS}"
test_pass "release continuation requires known acceptance and checks the actual extracted archive"
fi

if test_selected release_publish_controls; then
test_begin preflight release_publish_controls
test_step publish "exercise the tag preflight, release archiving and GitHub publication offline"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "release publish controls failed" \
  "${ROOT_DIR}/tests/suites/preflight/check_release_publish.py" "${PW_TEST_ARTIFACTS}"
test_pass "release archiving and publication verify their inputs and refuse every mismatch"
fi

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
