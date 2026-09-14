#!/usr/bin/env bash
# Small helpers for baseline shell cases. Call test_begin first; the caller
# owns test_step/test_pass and decides which prerequisites and checks to run.
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/testlib.sh"

test_require_pw() {
  PW_APP_DIR="${PW_APP_DIR:-$(testlib_root)/dist/PolicyWitness.app}"
  PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"
  if [[ ! -f "${PW_BIN}" || ! -x "${PW_BIN}" ]]; then
    test_fail "built policy-witness missing or not executable: ${PW_BIN}"
  fi
}

# Commands are argv, never shell text. Preserve the real failing status before
# printing the log, and stop the case even if the caller has disabled errexit.
test_run_logged() {
  local log_path="$1"
  local failure_message="$2"
  shift 2
  if [[ $# -eq 0 ]]; then
    test_fail "missing command for log: ${log_path}"
  fi
  local status
  if "$@" >"${log_path}" 2>&1; then
    return 0
  else
    status=$?
  fi
  if [[ -f "${log_path}" ]]; then
    cat "${log_path}" >&2 || true
  fi
  test_fail "${failure_message} (exit ${status}; log: ${log_path})"
}

# Build scripts accept an output path and own their compiler flags/recipe.
test_build_fixture() {
  local build_script="$1"
  local output="$2"
  local log_path="${PW_TEST_ARTIFACTS}/build.log"
  test_run_logged "${log_path}" "fixture build failed" bash "${build_script}" "${output}"
  if [[ ! -f "${output}" || ! -x "${output}" ]]; then
    test_fail "fixture build produced no executable file: ${output} (log: ${log_path})"
  fi
}

test_check_python() {
  local log_path="$1"
  local failure_message="$2"
  shift 2
  if [[ $# -eq 0 ]]; then
    test_fail "missing Python checker for log: ${log_path}"
  fi
  test_run_logged "${log_path}" "${failure_message}" /usr/bin/python3 "$@"
}
