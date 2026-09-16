#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

# Keep this entry point independent of the case helpers it is checking.
if test_selected python_startup; then
test_begin shell_helpers python_startup
test_step controls "reject disabled Python assertions before executing cases or replacing evidence"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/shell_helpers/check_python_startup.py" \
    "${PW_TEST_ARTIFACTS}" >"${PW_TEST_ARTIFACTS}/assertions.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assertions.log" >&2
  test_fail "Python startup controls failed; see artifacts/assertions.log"
fi
test_pass "optimized Python is rejected; normal assertion failures remain test failures"

fi

if test_selected controls; then
test_begin shell_helpers controls
test_step controls "exercise case failures, logs, prerequisites, and stage ordering"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/shell_helpers/check.py" \
    "${PW_TEST_ARTIFACTS}" >"${PW_TEST_ARTIFACTS}/assertions.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assertions.log" >&2
  test_fail "shell helper controls failed; see artifacts/assertions.log"
fi
test_pass "shell helpers retain diagnostics and case identity; failures prevent later stages"

fi

if test_selected script_groups; then
test_begin shell_helpers script_groups
test_step controls "observe child execution, wrapper phases, skips, and failure continuation"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/shell_helpers/check_scripts.py" \
    "${PW_TEST_ARTIFACTS}" >"${PW_TEST_ARTIFACTS}/assertions.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assertions.log" >&2
  test_fail "script-group controls failed; see artifacts/assertions.log"
fi
test_pass "wrappers preserve child order, streams, phase boundaries, and failing status"

fi

if test_selected finalizers; then
test_begin shell_helpers finalizers
test_step controls "observe result-helper returns, quiet output, and matching terminal evidence"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/shell_helpers/check_finalizers.py" \
    "${PW_TEST_ARTIFACTS}" >"${PW_TEST_ARTIFACTS}/assertions.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assertions.log" >&2
  test_fail "finalizer controls failed; see artifacts/assertions.log"
fi
test_pass "result helpers preserve terminal evidence, literal data, logging, and exit behavior"

fi

if test_selected worker_setup; then
test_begin shell_helpers worker_setup
test_step controls "exercise the worker suite with failed builds, failed harnesses, and independent transcripts"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/shell_helpers/check_worker_setup.py" \
    "${PW_TEST_ARTIFACTS}" >"${PW_TEST_ARTIFACTS}/assertions.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assertions.log" >&2
  test_fail "worker setup controls failed; see artifacts/assertions.log"
fi
test_pass "worker cases share setup; equipment failures stop before assertions and preserve evidence"
fi

if test_selected byoxpc_setup; then
test_begin shell_helpers byoxpc_setup
test_step controls "exercise disposable signing, partial installation, and verified removal with fake tools"
if ! /usr/bin/python3 "${ROOT_DIR}/tests/suites/shell_helpers/check_byoxpc_setup.py" \
    "${PW_TEST_ARTIFACTS}" >"${PW_TEST_ARTIFACTS}/assertions.log" 2>&1; then
  cat "${PW_TEST_ARTIFACTS}/assertions.log" >&2
  test_fail "BYOXPC ownership controls failed; see artifacts/assertions.log"
fi
test_pass "BYOXPC staging preserves the source, owns partial installation, and verifies cleanup"
fi
