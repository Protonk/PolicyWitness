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

if test_selected release_rotation_controls; then
test_begin preflight release_rotation_controls
test_step rotation "verify portable test evidence, pins, atomic retirement and interrupted cleanup"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "release rotation controls failed" \
  "${ROOT_DIR}/tests/suites/preflight/check_release_rotation.py" "${PW_TEST_ARTIFACTS}"
test_pass "portable release evidence and transactional rotation preserve pins and survive interruption"
fi

if test_selected codesign.preflight; then
bash "${ROOT_DIR}/tests/suites/preflight/preflight.sh"
fi

if test_selected byoxpc_verification_controls; then
test_begin preflight byoxpc_verification_controls
test_step verification "refuse installation of, and report validation failure for, a copy whose worker or issuer code changed after sealing"
test_require_pw
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "BYOXPC verification controls failed" \
  "${ROOT_DIR}/tests/suites/preflight/check_byoxpc_verification.py" "${PW_APP_DIR}" "${PW_TEST_ARTIFACTS}" "${PW_BIN}"
test_pass "installation and validation verify the copied bundle recursively; a changed worker or issuer is refused and reported"
fi

if test_selected build_provenance_controls; then
test_begin preflight build_provenance_controls
test_step helpers "exercise the lock, stamp, fresh-mode, Cargo judgment, SDK, signature-display and record readers with constructed inputs"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "build provenance controls failed" \
  "${ROOT_DIR}/tests/suites/preflight/check_build_provenance.py"
test_pass "lock claims are admitted only by a live owner; holds outlive killed owners; helpers write only owned, admitted paths; stamps, judgments, SDK versions, signature displays and records are decided without adopting unknowns"
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
test_pass "real signatures and manifest hashes independently reject corrupted copies; the signer check names an ad hoc helper"
fi

if test_selected build_guard_controls; then
test_begin preflight build_guard_controls
test_step build "observe minimum-version and signer refusals through the unchanged build script in both variants"
test_require_pw
SIGNING_IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "${SIGNING_IDENTITY}" ]] || test_fail "matching signing identity required"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "build guard controls failed" \
  "${ROOT_DIR}/tests/suites/preflight/opt_in/build_guards.py" \
  "${PW_TEST_ARTIFACTS}" "${SIGNING_IDENTITY}"
test_pass "wrong minima preserve previous outputs; an ad hoc helper passes deep verification but stops before packaging"
fi

if test_selected build_toolchain_switch_controls; then
test_begin preflight build_toolchain_switch_controls
test_step switch "build under the selected developer directory, refuse reuse under the Command Line Tools, recover fresh"
test_require_pw
SIGNING_IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "${SIGNING_IDENTITY}" ]] || test_fail "matching signing identity required"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "build toolchain switch controls failed" \
  "${ROOT_DIR}/tests/suites/preflight/opt_in/build_toolchain_switch.py" \
  "${PW_TEST_ARTIFACTS}" "${SIGNING_IDENTITY}"
test_pass "a real toolchain switch refuses reuse by the fields that differ and recovers under fresh mode"
fi

if test_selected build_refusal_controls; then
test_begin preflight build_refusal_controls
test_step build "drive the unchanged build script through every baseline refusal and observe the operation each one protects"
test_require_pw
SIGNING_IDENTITY="$(resolve_app_signing_identity "${PW_APP_DIR}")"
[[ -n "${SIGNING_IDENTITY}" ]] || test_fail "matching signing identity required"
test_check_python "${PW_TEST_ARTIFACTS}/assertions.log" "build refusal controls failed" \
  "${ROOT_DIR}/tests/suites/preflight/opt_in/build_refusals.py" \
  "${PW_TEST_ARTIFACTS}" "${SIGNING_IDENTITY}"
test_pass "every manifest refusal fires in its variants before the operation it protects; the fresh-mode state sequence, lock and record limits hold; bypassed and displaced guards fail their control"
fi
