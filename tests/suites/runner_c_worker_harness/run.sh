#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/case.sh"

PW_TEST_SUITE="runner_c_worker_harness"
ABI_DIR="${ROOT_DIR}/controller/tools/pw_probe_runner"

# pw-probe-runner lives bundle-locally inside each XPC service.
WORKER_PATH="${PW_APP_DIR}/Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner"

# Compile the harness once for the whole suite. xcrun won't have a
# build dir; drop it under tests/out so it's reproducible and
# rebuilt on schema changes.
HARNESS_BIN="${PW_TEST_OUT_DIR}/harness.runner_c_worker"
mkdir -p "$(dirname "${HARNESS_BIN}")"
harness_built=0

check_prereqs() {
  if [[ ! -x "${WORKER_PATH}" ]]; then
    return 1
  fi
  if [[ ! -f "${ABI_DIR}/pw_probe_runner_abi.h" ]]; then
    return 1
  fi
  return 0
}

ensure_harness() {
  if [[ "${harness_built}" -eq 0 ]]; then
    test_build_fixture "${ROOT_DIR}/tests/fixtures/worker_harness/build.sh" "${HARNESS_BIN}"
    harness_built=1
  fi
}

# Begin the case, run one harness scenario, and leave its JSON at RESULT_FILE.
# Returns non-zero (after test_skip) when prereqs are missing so the
# caller can `|| return 0`; calls test_fail (which exits) if the harness
# itself errors.
run_harness_case() {
  local test_id="$1" scenario="$2" desc="$3"
  test_selected "${test_id}" || return 1
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "harness" "${desc}"
  if ! check_prereqs; then
    test_skip "missing dist/PolicyWitness.app or pw_probe_runner_abi.h — run ./build.sh first" "{}"
    return 1
  fi
  ensure_harness
  RESULT_FILE="${PW_TEST_ARTIFACTS}/result.json"
  if "${HARNESS_BIN}" "${WORKER_PATH}" "${scenario}" >"${RESULT_FILE}" 2>"${PW_TEST_ARTIFACTS}/harness.stderr"; then
    return 0
  else
    local rc=$?
    test_fail "harness exited rc=${rc}" "{\"stderr\":\"${PW_TEST_ARTIFACTS}/harness.stderr\"}"
  fi
}

# Turn a python assertion exit code into a pass/fail. The python block is
# expected to print a one-line ok message on success (used as the pass note).
finish_from_assert_log() {
  local arc="$1"
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${PW_TEST_ARTIFACTS}/assert.log" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${PW_TEST_ARTIFACTS}/assert.log\",\"result\":\"${RESULT_FILE}\"}"
  fi
  test_pass "$(tail -1 "${PW_TEST_ARTIFACTS}/assert.log")" "{\"result\":\"${RESULT_FILE}\"}"
}

# Uniform assertion for the pre-apply self-defense scenarios: the worker
# must exit with a specific code, having flipped no sentinels and written
# no ready byte.
run_refusal_case() {
  local test_id="$1" scenario="$2" expect_code="$3" desc="$4"
  run_harness_case "${test_id}" "${scenario}" "${desc}" || return 0
  set +e
  PW_EXPECT_CODE="${expect_code}" /usr/bin/python3 - "${RESULT_FILE}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1 <<'PY'
import json, os, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
want = int(os.environ["PW_EXPECT_CODE"])
assert r["exit_code"] == want, \
    f"expected worker exit_code={want}, got exit_code={r['exit_code']!r} term_signal={r['term_signal']!r}"
assert r["term_signal"] is None, f"worker should exit with a code, not a signal: {r}"
assert not r["applied"], f"applied must stay false on a pre-apply refusal: {r}"
assert not r["done"], f"done must stay false on a pre-apply refusal: {r}"
assert not r["ready_byte_received"], f"ready byte must not precede a pre-apply refusal: {r}"
assert not r["sent_sigkill"], f"worker should self-exit; no SIGKILL fallback expected: {r}"
if r['scenario'] == 'policy_overflow':
    assert r['failure_published'] == 1, r
    assert r['failure'] == {'operation': 2, 'code': 2, 'detail': 262143,
                            'native_kind': 0, 'errno_present': 0}, r
if r['scenario'] == 'policy_nul':
    assert r['failure_published'] == 1, r
    assert r['failure'] == {'operation': 2, 'code': 9, 'detail': 26,
                            'native_kind': 0, 'errno_present': 0}, r
print(f"ok: worker refused with exit_code={want}; no ready/applied/done")
PY
  local arc=$?
  set -e
  finish_from_assert_log "${arc}"
}

# ---- test_id: happy_default_allow ----------------------------------------

run_happy_default_allow() {
  run_harness_case "happy_default_allow" "happy_default_allow" \
    "pw-probe-runner under (allow default): read /etc/hosts succeeds, sentinels fire, clean exit" || return 0
  set +e
  /usr/bin/python3 - "${RESULT_FILE}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1 <<'PY'
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
  finish_from_assert_log "${arc}"
}

# ---- test_id: bare_deny_default ------------------------------------------

run_bare_deny_default() {
  run_harness_case "bare_deny_default" "bare_deny_default" \
    "pw-probe-runner under bare (deny default): worker still completes; slot reports kernel deny" || return 0
  set +e
  /usr/bin/python3 - "${RESULT_FILE}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1 <<'PY'
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
  finish_from_assert_log "${arc}"
}

# ---- test_id: exit_byte_clean --------------------------------------------

run_exit_byte_clean() {
  run_harness_case "exit_byte_clean" "exit_byte_clean" \
    "worker observes exit_requested in shm and _exit(0)s before harness SIGKILL" || return 0
  set +e
  /usr/bin/python3 - "${RESULT_FILE}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1 <<'PY'
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
  finish_from_assert_log "${arc}"
}

# ---- test_id: max_slots_deny_default ---------------------------------------

run_max_slots_deny_default() {
  run_harness_case "max_slots_deny_default" "max_slots_deny_default" \
    "worker completes all 256 shared-memory slots under bare (deny default)" || return 0
  set +e
  /usr/bin/python3 - "${RESULT_FILE}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1 <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

assert r["ready_byte_received"], "pre-apply ready byte not received"
assert r["applied"], f"applied sentinel never flipped: {r}"
assert r["apply_rc"] == 0, f"sandbox_apply returned {r['apply_rc']}"
assert r["done"], f"done sentinel never flipped: {r}"
assert not r["sent_sigkill"], "worker did not clean-exit after max-slot run"
assert r["exit_code"] == 0, f"worker exit_code != 0: {r}"

slots = r["slots"]
assert len(slots) == 256, f"expected 256 slots, got {len(slots)}"
for idx in (0, 1, 2, 127, 255):
    s = slots[idx]
    assert s["step_id"] == f"none_{idx:03d}", f"slot {idx} step_id mismatch: {s}"
    assert s["completed"] == 1, f"slot {idx} not completed: {s}"
    assert s["rc"] == 0, f"PW_ATTEMPT_NONE slot {idx} should rc=0: {s}"
    assert s["errno"] == 0, f"PW_ATTEMPT_NONE slot {idx} should errno=0: {s}"

missing = [i for i, s in enumerate(slots) if s["completed"] != 1]
assert not missing, f"incomplete slots: {missing[:10]}"
print("ok: 256 slots completed across the full shared-memory region under deny-default")
PY
  local arc=$?
  set -e
  finish_from_assert_log "${arc}"
}

# ---- test_id: sigkill_fallback ---------------------------------------------

run_sigkill_fallback() {
  run_harness_case "sigkill_fallback" "sigkill_fallback" \
    "host SIGKILL fallback reaps worker when clean exit byte is withheld" || return 0
  set +e
  /usr/bin/python3 - "${RESULT_FILE}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1 <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

assert r["ready_byte_received"], "pre-apply ready byte not received"
assert r["applied"], f"applied sentinel never flipped: {r}"
assert r["done"], f"done sentinel never flipped: {r}"
assert r["sent_sigkill"], f"expected harness SIGKILL fallback, got clean exit: {r}"
assert r["exit_code"] is None, f"worker should not have clean-exited: {r}"
assert r["term_signal"] == 9, f"expected SIGKILL term_signal=9: {r}"

slots = r["slots"]
assert len(slots) == 1, f"expected 1 slot, got {len(slots)}"
assert slots[0]["completed"] == 1, f"slot should complete before fallback kill: {slots[0]}"
print("ok: host SIGKILL fallback reaped worker after withheld exit byte")
PY
  local arc=$?
  set -e
  finish_from_assert_log "${arc}"
}

# ---- test_id: params_round_trip --------------------------------------------

run_params_round_trip() {
  run_harness_case "params_round_trip" "params_round_trip" \
    "policy.params reach the kernel: (subpath (param \"TARGET\")) denies /etc/hosts when TARGET=/private/etc" || return 0
  set +e
  /usr/bin/python3 - "${RESULT_FILE}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1 <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

# Three distinguishable outcomes:
#   (a) compile failed: sandbox_compile_string couldn't resolve
#       (param "TARGET") so apply_rc=-1, done is set, no slots ran.
#       Means the worker built a params object but it was empty or
#       the SET failed silently.
#   (b) compile + apply succeeded but slot rc=0: the param was
#       parsed but its value didn't reach the compiled profile,
#       so the kernel allowed /etc/hosts.
#   (c) compile + apply succeeded AND slot rc=1 with errno=EPERM:
#       the param TARGET=/private/etc reached the compiled profile,
#       the kernel saw the deny rule, and the open was denied.
#
# (c) is the only outcome that proves end-to-end round-trip.
#
# SBPL subpath matches the kernel-canonical path, NOT user-visible
# aliases — /etc realpaths to /private/etc on macOS, so TARGET must
# be /private/etc for the deny rule to fire on a /etc/hosts open.
# This is a SBPL semantic detail, not a worker concern; both the C
# harness (harness.c::populate_params_target) and this assertion text
# document it so a future debugger doesn't waste time on /etc.
assert r["ready_byte_received"], "pre-apply ready byte not received"
assert r["apply_rc"] == 0, \
    f"sandbox_compile_string + apply failed (apply_rc={r['apply_rc']}); params didn't construct the profile"
assert r["applied"], f"applied sentinel never flipped: {r}"
assert r["done"], f"done sentinel never flipped: {r}"
assert not r["sent_sigkill"], "worker did not clean-exit"
assert r["exit_code"] == 0, f"worker exit_code != 0: {r}"

slots = r["slots"]
assert len(slots) == 1, f"expected 1 slot, got {len(slots)}"
s = slots[0]
assert s["completed"] == 1, f"slot not marked completed: {s}"
assert s["rc"] == 1, \
    f"TARGET=/private/etc should make /etc/hosts open fail with EPERM; got rc={s['rc']} errno={s['errno']}. " \
    f"This means the param didn't reach the kernel — likely a worker bug in the sandbox_set_param path."
assert s["errno"] in (1, 13), \
    f"expected errno EPERM (1) or EACCES (13) for the param-driven kernel deny, got {s['errno']}"

print(f"ok: TARGET=/private/etc round-tripped; kernel denied /etc/hosts with errno={s['errno']}")
PY
  local arc=$?
  set -e
  finish_from_assert_log "${arc}"
}

# ---- test_id: unlink_allow / unlink_deny (PW_ATTEMPT_FILE_UNLINK) ----------

run_unlink_allow() {
  run_harness_case "unlink_allow" "unlink_allow" \
    "file unlink under (allow default): worker removes the harness temp file" || return 0
  set +e
  /usr/bin/python3 - "${RESULT_FILE}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1 <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert r["applied"] and r["done"] and r["exit_code"] == 0, f"worker did not complete cleanly: {r}"
s = r["slots"][0]
assert s["completed"] == 1, f"slot not completed: {s}"
assert s["rc"] == 0, f"unlink under (allow default) should succeed: {s}"
assert r["target_exists_after"] is False, f"target should be gone after a successful unlink: {r}"
print("ok: unlink removed the target under (allow default)")
PY
  local arc=$?
  set -e
  finish_from_assert_log "${arc}"
}

run_unlink_deny() {
  run_harness_case "unlink_deny" "unlink_deny" \
    "file unlink under (deny default): worker is denied; target survives" || return 0
  set +e
  /usr/bin/python3 - "${RESULT_FILE}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1 <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert r["applied"] and r["done"] and r["exit_code"] == 0, f"worker did not complete cleanly: {r}"
s = r["slots"][0]
assert s["completed"] == 1, f"slot not completed: {s}"
assert s["rc"] == 1, f"unlink under (deny default) should be denied (rc=1): {s}"
assert s["errno"] in (1, 13), f"expected EPERM(1)/EACCES(13) on the kernel deny, got errno={s['errno']}: {s}"
assert r["target_exists_after"] is True, f"target must survive a denied unlink: {r}"
print(f"ok: unlink denied (errno={s['errno']}); target survived under (deny default)")
PY
  local arc=$?
  set -e
  finish_from_assert_log "${arc}"
}

# ---- test_id: create_allow (PW_ATTEMPT_FILE_CREATE) ------------------------

run_create_allow() {
  run_harness_case "create_allow" "create_allow" \
    "file create under (allow default): worker creates the (absent) target" || return 0
  set +e
  /usr/bin/python3 - "${RESULT_FILE}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1 <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert r["applied"] and r["done"] and r["exit_code"] == 0, f"worker did not complete cleanly: {r}"
s = r["slots"][0]
assert s["completed"] == 1, f"slot not completed: {s}"
assert s["rc"] == 0, f"create under (allow default) should succeed: {s}"
# F_GETPATH canonicalizes the fd while it is open; the create path should
# resolve under /private/... (or wherever TMPDIR points), not be empty.
assert s["observed_path"], f"create should capture observed_path from the open fd: {s}"
assert r["target_exists_after"] is True, f"target must exist after a successful create: {r}"
print(f"ok: create made the target (observed_path={s['observed_path']})")
PY
  local arc=$?
  set -e
  finish_from_assert_log "${arc}"
}

# ---- test_id: compile_failure (worker survives malformed SBPL) -------------

run_compile_failure() {
  run_harness_case "compile_failure" "compile_failure" \
    "malformed SBPL: apply_rc=-1, done flips, applied stays 0, worker still clean-exits" || return 0
  set +e
  /usr/bin/python3 - "${RESULT_FILE}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1 <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
# The compile fails before the ready byte and before apply, so:
assert r["ready_byte_received"] is False, f"compile fails before the ready byte: {r}"
assert r["applied"] is False, f"applied must stay false when compile fails: {r}"
assert r["apply_rc"] == -1, f"apply_rc must be -1 on compile failure (got {r['apply_rc']}): {r}"
# ...but the worker still flips done and honors the exit byte rather than dying.
assert r["done"] is True, f"done must flip so the host stops polling: {r}"
assert r["sent_sigkill"] is False, f"worker should clean-exit on the exit byte, not need SIGKILL: {r}"
assert r["exit_code"] == 0, f"worker should _exit(0) after reporting the compile failure: {r}"
# No attempts ran.
assert r["slots"][0]["completed"] == 0, f"no slot should run when compile fails: {r['slots'][0]}"
print("ok: worker reported compile failure (apply_rc=-1, done) and clean-exited")
PY
  local arc=$?
  set -e
  finish_from_assert_log "${arc}"
}

run_happy_default_allow
run_bare_deny_default
run_exit_byte_clean
run_max_slots_deny_default
run_sigkill_fallback
run_params_round_trip

# File unlink and creation of an absent target through the worker ABI.
run_unlink_allow
run_unlink_deny
run_create_allow

# #2 — pre-apply self-defense / refusal branches.
run_compile_failure
run_refusal_case "abi_mismatch_refused"        "abi_mismatch"        4 \
  "header abi_version != worker build → exit 4, no apply"
run_refusal_case "prepared_unset_refused"      "prepared_unset"      5 \
  "host did not set prepared=1 → exit 5, no apply"
run_refusal_case "step_count_overflow_refused" "step_count_overflow" 6 \
  "header step_count > PW_SHM_MAX_STEPS → exit 6"
run_refusal_case "policy_overflow_refused"     "policy_overflow"     7 \
  "policy exceeds the 256 KiB cap → exit 7"
run_refusal_case "policy_nul_refused"          "policy_nul"          9 \
  "policy carries an embedded NUL → exit 9, no prefix compiled"
run_refusal_case "param_count_overflow_refused" "param_count_overflow" 8 \
  "header param_count > PW_SHM_MAX_PARAMS → exit 8"

# ---- test_id: exec_descriptor_limit_{raised,capped} -----------------------
# The worker budgets actual free slots and reserves descriptors for imports,
# file probes and spawn actions. Excess execs fail before pipe creation.

run_exec_descriptor_limit() {
  local test_id="$1" scenario="$2" mode="$3"
  run_harness_case "${test_id}" "${scenario}" \
    "32 exec slots with controlled descriptor limits and inheritance (${mode})" || return 0
  set +e
  PW_MODE="${mode}" /usr/bin/python3 - "${RESULT_FILE}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1 <<'PY'
import json, os, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
mode = os.environ["PW_MODE"]
assert r["ready_byte_received"] and r["applied"] and r["apply_rc"] == 0 and r["done"], r
assert not r["sent_sigkill"] and r["exit_code"] == 0 and r["term_signal"] is None, r
assert r["failure_published"] == 0, f"a descriptor shortfall is per-step evidence, never a run failure: {r}"
all_slots = r["slots"]
assert all(s["completed"] == 1 for s in all_slots), all_slots
slots = [s for s in all_slots if "child_pid" in s]
reads = [s for s in all_slots if "child_pid" not in s]
assert len(slots) == 32, slots
if mode.startswith("capped"):
    assert [s["step_id"] for s in reads] == ["read_etc_hosts", "read_after_exec"], reads
    assert all(s["rc"] == 0 and s["errno"] == 0 and s["observed_path"] == "/private/etc/hosts"
               for s in reads), reads
else:
    assert not reads, reads
spawned = [s for s in slots if s["child_pid"] > 0]
failed = [s for s in slots if s["child_pid"] == 0]
assert all(s["rc"] == 0 and s["errno"] == 0 and s["child_exit_code"] == 0
           and s["child_term_signal"] == 0 and s["error"] == "" for s in spawned), spawned
if mode in ("raised", "inherited"):
    assert len(spawned) == 32, f"every slot must spawn once the soft limit is raised; first failures: {failed[:2]}"
    if mode == "inherited":
        assert r["inherited_extra_fds"] == 80 and r["rlimit_soft"] == 128 and r["rlimit_hard"] == 4096, r
    print(f"ok: 32 clean execs with soft limit {r['rlimit_soft']} and {r['inherited_extra_fds']} extra inherited descriptors")
else:
    assert failed, "hard cap must refuse excess exec slots"
    if mode == "capped_empty":
        assert not spawned, "cap 64 cannot fit pipes plus the 64-descriptor reserve"
    else:
        assert spawned, "available exec capacity must still spawn clean children"
    assert [s["child_pid"] > 0 for s in slots] == [True] * len(spawned) + [False] * len(failed), \
        "only exec slots beyond the budget may fail"
    for s in failed:
        assert s["errno"] == 24 and s["rc"] == -1, s
        assert s["child_exit_code"] == -1 and s["child_term_signal"] == 0, s
        assert s["error"].startswith("exec descriptor budget: RLIMIT_NOFILE"), s
        assert "reserve 64" in s["error"] and "pipe(" not in s["error"], s
    print(f"ok: hard cap {r['rlimit_hard']}: {len(spawned)} clean execs, {len(failed)} budget refusals; imports and both reads succeeded")
PY
  local arc=$?
  set -e
  finish_from_assert_log "${arc}"
}

run_exec_descriptor_limit "exec_descriptor_limit_raised" "exec_descriptor_limit_raised" "raised"
run_exec_descriptor_limit "exec_descriptor_limit_capped" "exec_descriptor_limit_capped" "capped_empty"
for cap in 126 127 128 129; do
  run_exec_descriptor_limit "exec_descriptor_cap_${cap}" "exec_descriptor_cap_${cap}" "capped"
done
run_exec_descriptor_limit "exec_descriptor_inherited" "exec_descriptor_inherited" "inherited"

# ---- test_id: exec_attempt_budget_{remainder,sequence} ---------------------
# Six /bin/sleep helpers each outlive their deadline. The worker's exec attempt
# budget clamps the last spawned child's deadline to the remainder, refuses
# later exec steps before spawn, and the trailing read still runs; `done`
# publishes near the budget edge instead of after six full deadlines.

run_exec_attempt_budget() {
  local test_id="$1" mode="$2"
  run_harness_case "${test_id}" "${test_id}" \
    "six deadline-hitting helpers under a shortened exec attempt budget (${mode})" || return 0
  set +e
  PW_MODE="${mode}" /usr/bin/python3 - "${RESULT_FILE}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1 <<'PY'
import json, os, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
mode = os.environ["PW_MODE"]
budget = {"remainder": 1000, "sequence": 1500}[mode]
assert r["ready_byte_received"] and r["applied"] and r["apply_rc"] == 0 and r["done"], r
assert not r["sent_sigkill"] and r["exit_code"] == 0 and r["term_signal"] is None, r
assert r["failure_published"] == 0, f"a budget refusal is per-step evidence, never a run failure: {r}"
slots = r["slots"]
assert all(s["completed"] == 1 for s in slots), slots
execs = [s for s in slots if "child_pid" in s]
reads = [s for s in slots if "child_pid" not in s]
assert len(execs) == 6 and [s["step_id"] for s in reads] == ["read_after_budget"], slots
read = reads[0]
assert read["rc"] == 0 and read["errno"] == 0 and read["observed_path"] == "/private/etc/hosts", read
spawned = [s for s in execs if s["child_pid"] > 0]
refused = [s for s in execs if s["child_pid"] == 0]
assert spawned and refused, execs
assert [s["child_pid"] > 0 for s in execs] == [True] * len(spawned) + [False] * len(refused), \
    "spawns must precede refusals: the budget only runs down"
for s in spawned:
    assert s["rc"] == -1 and s["errno"] == 0, s
    assert s["child_exit_code"] == -1 and s["child_term_signal"] == 9, s
    assert "deadline" in s["error"] and "SIGKILL'd" in s["error"], s
for s in refused:
    assert s["rc"] == -1 and s["errno"] == 60, s
    assert s["child_exit_code"] == -1 and s["child_term_signal"] == 0, s
    assert s["stdout"] == "" and s["stderr"] == "", s
    assert s["error"] == f"exec attempt budget: {budget} ms exhausted before spawn", s
if mode == "remainder":
    # A ten-second default deadline never fits a one-second budget: exactly one
    # child spawns with the remainder as its deadline; the rest are refused.
    assert len(spawned) == 1 and "(exec attempt budget remainder)" in spawned[0]["error"], spawned
else:
    # Several 500 ms deadlines fit before the budget ends the sequence. Only the
    # last spawned child can have been bounded by the remainder.
    assert len(spawned) >= 2, spawned
    assert all("(exec attempt budget remainder)" not in s["error"] for s in spawned[:-1]), spawned
span = r["done_after_applied_ms"]
assert 0 <= span < budget + 1000, f"done must publish near the budget edge, not after every deadline: {span} ms"
print(f"ok: {mode}: {len(spawned)} helper(s) killed at a deadline, {len(refused)} exec steps refused before spawn, "
      f"trailing read succeeded, done {span} ms after applied")
PY
  local arc=$?
  set -e
  finish_from_assert_log "${arc}"
}

run_exec_attempt_budget "exec_attempt_budget_remainder" "remainder"
run_exec_attempt_budget "exec_attempt_budget_sequence" "sequence"

run_proceed_control() {
  local scenario="$1"
  run_harness_case "${scenario}" "${scenario}" "Exercise release, acknowledgement and attempt exclusion: ${scenario}" || return 0
  set +e
  /usr/bin/python3 "${ROOT_DIR}/tests/suites/runner_c_worker_harness/check_proceed.py" "${RESULT_FILE}" >"${PW_TEST_ARTIFACTS}/assert.log" 2>&1
  local arc=$?
  set -e
  finish_from_assert_log "${arc}"
}
for scenario in proceed_never_set proceed_late_after_expiry proceed_before_applied \
  proceed_delayed_observed_quiescence proceed_under_bare_deny_default \
  proceed_wait_budget_short proceed_wait_budget_long proceed_expiry_release_boundary \
  host_lost_while_waiting max_slots_proceed; do
  run_proceed_control "$scenario"
done
