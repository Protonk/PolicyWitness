#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="runner_c_worker_harness"
SUITE_DIR="${ROOT_DIR}/tests/suites/runner_c_worker_harness"
ABI_DIR="${ROOT_DIR}/controller/tools/pw_probe_runner"

# pw-probe-runner lives bundle-locally inside each XPC service per
# RUNNER-RESHAPE-PLAN R5. Either copy works; we use PWRunner.xpc's.
WORKER_PATH="${PW_APP_DIR}/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner"

# Compile the harness once for the whole suite. xcrun won't have a
# build dir; drop it under tests/out so it's reproducible and
# rebuilt on schema changes.
HARNESS_BIN="${PW_TEST_OUT_DIR}/harness.runner_c_worker"
mkdir -p "$(dirname "${HARNESS_BIN}")"

check_prereqs() {
  if [[ ! -x "${WORKER_PATH}" ]]; then
    return 1
  fi
  if [[ ! -f "${ABI_DIR}/pw_probe_runner_abi.h" ]]; then
    return 1
  fi
  return 0
}

build_harness() {
  /usr/bin/xcrun --sdk macosx clang -Wall -Wextra -O2 -std=c11 \
    -I "${ABI_DIR}" \
    -o "${HARNESS_BIN}" \
    "${SUITE_DIR}/harness.c"
}

# ---- test_id: happy_default_allow ----------------------------------------

run_happy_default_allow() {
  local test_id="happy_default_allow"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "harness" "pw-probe-runner under (allow default): read /etc/hosts succeeds, sentinels fire, clean exit"

  if ! check_prereqs; then
    test_skip "missing dist/PolicyWitness.app or pw_probe_runner_abi.h — run ./build.sh first" "{}"
    return 0
  fi
  if [[ ! -x "${HARNESS_BIN}" ]]; then
    build_harness
  fi

  local result_file="${PW_TEST_ARTIFACTS}/result.json"
  set +e
  "${HARNESS_BIN}" "${WORKER_PATH}" "${test_id}" >"${result_file}" 2>"${PW_TEST_ARTIFACTS}/harness.stderr"
  local rc=$?
  set -e
  if [[ "${rc}" -ne 0 ]]; then
    test_fail "harness exited rc=${rc}" "{\"stderr\":\"${PW_TEST_ARTIFACTS}/harness.stderr\"}"
    return 0
  fi

  set +e
  /usr/bin/python3 - "${result_file}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1 <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

assert r["ready_byte_received"], "pre-apply ready byte not received"
assert r["applied"], f"applied sentinel never flipped: {r}"
assert r["apply_rc"] == 0, f"sandbox_apply returned {r['apply_rc']}"
assert r["done"], f"done sentinel never flipped: {r}"
assert not r["sent_sigkill"], "harness had to SIGKILL the worker; clean exit byte failed"
assert r["exit_code"] == 0, f"worker exit_code != 0: {r}"
assert r["term_signal"] is None, f"worker was signaled: {r}"

slots = r["slots"]
assert len(slots) == 1, f"expected 1 slot, got {len(slots)}"
s = slots[0]
assert s["completed"] == 1, f"slot not marked completed: {s}"
assert s["rc"] == 0, f"file open_read /etc/hosts under (allow default) should succeed: {s}"
assert s["observed_path"] == "/private/etc/hosts", \
    f"observed_path should be the F_GETPATH-canonical form: {s['observed_path']!r}"

print(f"ok: ready+applied+done+clean_exit; /etc/hosts opened (observed={s['observed_path']})")
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${PW_TEST_ARTIFACTS}/assert.log" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${PW_TEST_ARTIFACTS}/assert.log\",\"result\":\"${result_file}\"}"
    return 0
  fi
  test_pass "$(tail -1 "${PW_TEST_ARTIFACTS}/assert.log")" "{\"result\":\"${result_file}\"}"
}

# ---- test_id: bare_deny_default ------------------------------------------

run_bare_deny_default() {
  local test_id="bare_deny_default"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "harness" "pw-probe-runner under bare (deny default): worker still completes; slot reports kernel deny"

  if ! check_prereqs; then
    test_skip "missing dist/PolicyWitness.app or pw_probe_runner_abi.h — run ./build.sh first" "{}"
    return 0
  fi
  if [[ ! -x "${HARNESS_BIN}" ]]; then
    build_harness
  fi

  local result_file="${PW_TEST_ARTIFACTS}/result.json"
  set +e
  "${HARNESS_BIN}" "${WORKER_PATH}" "${test_id}" >"${result_file}" 2>"${PW_TEST_ARTIFACTS}/harness.stderr"
  local rc=$?
  set -e
  if [[ "${rc}" -ne 0 ]]; then
    test_fail "harness exited rc=${rc}" "{\"stderr\":\"${PW_TEST_ARTIFACTS}/harness.stderr\"}"
    return 0
  fi

  set +e
  /usr/bin/python3 - "${result_file}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1 <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

# This scenario is the downstream bug-report shape. The PRE-Step-5
# Swift worker died here without producing step results. The C
# worker must survive: sentinels fire, the slot reports the kernel
# deny, and the worker exits cleanly.
assert r["ready_byte_received"], "pre-apply ready byte not received under (deny default)"
assert r["applied"], f"applied sentinel never flipped — worker died pre-apply? {r}"
assert r["apply_rc"] == 0, f"sandbox_apply returned {r['apply_rc']}"
assert r["done"], f"done sentinel never flipped — this is the bug-report regression: {r}"
assert not r["sent_sigkill"], "harness had to SIGKILL the worker; clean exit byte failed under (deny default)"
assert r["exit_code"] == 0, f"worker exit_code != 0: {r}"

slots = r["slots"]
assert len(slots) == 1
s = slots[0]
assert s["completed"] == 1, f"slot not marked completed under (deny default): {s}"
# The kernel denies the open; rc=1, errno is EACCES (13) or EPERM (1).
# We accept either to avoid pinning a specific kernel revision.
assert s["rc"] == 1, f"file open_read /etc/hosts under (deny default) should be denied: {s}"
assert s["errno"] in (1, 13), \
    f"expected errno EPERM (1) or EACCES (13) for the kernel deny, got {s['errno']}"

print(f"ok: worker survived (deny default); slot reports kernel deny errno={s['errno']}")
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${PW_TEST_ARTIFACTS}/assert.log" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${PW_TEST_ARTIFACTS}/assert.log\",\"result\":\"${result_file}\"}"
    return 0
  fi
  test_pass "$(tail -1 "${PW_TEST_ARTIFACTS}/assert.log")" "{\"result\":\"${result_file}\"}"
}

# ---- test_id: exit_byte_clean --------------------------------------------

run_exit_byte_clean() {
  local test_id="exit_byte_clean"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "harness" "worker observes exit_requested in shm and _exit(0)s before harness SIGKILL"

  if ! check_prereqs; then
    test_skip "missing dist/PolicyWitness.app or pw_probe_runner_abi.h — run ./build.sh first" "{}"
    return 0
  fi
  if [[ ! -x "${HARNESS_BIN}" ]]; then
    build_harness
  fi

  local result_file="${PW_TEST_ARTIFACTS}/result.json"
  set +e
  "${HARNESS_BIN}" "${WORKER_PATH}" "${test_id}" >"${result_file}" 2>"${PW_TEST_ARTIFACTS}/harness.stderr"
  local rc=$?
  set -e
  if [[ "${rc}" -ne 0 ]]; then
    test_fail "harness exited rc=${rc}" "{\"stderr\":\"${PW_TEST_ARTIFACTS}/harness.stderr\"}"
    return 0
  fi

  set +e
  /usr/bin/python3 - "${result_file}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1 <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

# Focused assertion: the exit byte was the reason the worker exited,
# not the harness's SIGKILL grace timer.
assert not r["sent_sigkill"], "harness had to SIGKILL — exit byte didn't work"
assert r["exit_code"] == 0, f"worker did not _exit(0): {r}"
assert r["term_signal"] is None, f"worker was signaled instead of _exit'ing: {r}"
print("ok: worker _exit(0) in response to exit_requested, no SIGKILL needed")
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${PW_TEST_ARTIFACTS}/assert.log" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${PW_TEST_ARTIFACTS}/assert.log\",\"result\":\"${result_file}\"}"
    return 0
  fi
  test_pass "$(tail -1 "${PW_TEST_ARTIFACTS}/assert.log")" "{\"result\":\"${result_file}\"}"
}

run_happy_default_allow
run_bare_deny_default
run_exit_byte_clean
