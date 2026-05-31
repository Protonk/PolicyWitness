#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="runner_use_c_worker"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

# ---- exec_fixture helper (built on demand by exec_* test cases) ----------
#
# Source lives under tests/suites/runner_use_c_worker/exec_fixture/helper.c;
# the compiled binary lands in tests/out/<run>/exec_fixture/helper. Not
# in the app bundle, not signed, not notarized — purely a test fixture
# the exec attempt cases drive through PW.
EXEC_FIXTURE_SRC="${ROOT_DIR}/tests/suites/runner_use_c_worker/exec_fixture/helper.c"
EXEC_FIXTURE_BIN="${PW_TEST_OUT_DIR}/exec_fixture/helper"
exec_fixture_built=0

ensure_exec_fixture() {
  if [[ "${exec_fixture_built}" -eq 1 ]]; then return 0; fi
  if [[ ! -f "${EXEC_FIXTURE_SRC}" ]]; then
    return 1
  fi
  mkdir -p "$(dirname "${EXEC_FIXTURE_BIN}")"
  if ! /usr/bin/xcrun --sdk macosx clang -Wall -Wextra -O2 -std=c11 \
       -o "${EXEC_FIXTURE_BIN}" "${EXEC_FIXTURE_SRC}" 2>"${PW_TEST_OUT_DIR}/exec_fixture/build.err"; then
    return 1
  fi
  exec_fixture_built=1
  return 0
}

# ---- test_id: happy_default_allow ----------------------------------------

run_happy_default_allow() {
  local test_id="happy_default_allow"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "run" "C-worker code path (pw-probe-runner + sb_api_validator --batch via CWorkerOrchestrator) assembles a full v4 envelope"

  if ! require_pw_app "${PW_BIN}"; then exit 0; fi

  local specimen="${PW_TEST_ARTIFACTS}/specimen.json"
  cat >"${specimen}" <<'EOF'
{
  "schema_version": 1,
  "specimen_id": "use_c_worker_happy",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1)(allow default)"
  },
  "probe_plan": [{
    "step_id": "s1",
    "sandbox_check": {
      "operation": "file-read-data",
      "filter": {"kind": "path", "value": "/etc/hosts"}
    },
    "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"}
  }]
}
EOF

  local run_stdout="${PW_TEST_ARTIFACTS}/run.json"
  set +e
  "${PW_BIN}" run "${specimen}" >"${run_stdout}" 2>/dev/null
  local rc=$?
  set -e
  if [[ "${rc}" -ne 0 ]]; then
    test_fail "specimen failed (rc=${rc})" "{\"stdout\":\"${run_stdout}\"}"
    return 0
  fi

  local assert_log="${PW_TEST_ARTIFACTS}/assert.log"
  set +e
  /usr/bin/python3 - "${run_stdout}" >"${assert_log}" 2>&1 <<'PY'
import json, sys
env = json.loads(open(sys.argv[1]).read())
r = env["data"]["runner_result"]

# Envelope shape: v4 + both subprocess records + override mirrored back.
assert r["schema_version"] == 4, "schema {0}".format(r["schema_version"])
assert r["normalized_outcome"] == "ok", "outcome {0}".format(r["normalized_outcome"])
assert r["rc"] == 0
assert r["validator_subprocess"] is not None, "validator_subprocess missing"
assert r["validator_subprocess"]["exit_code"] == 0
assert r["runner_subprocess"] is not None, "runner_subprocess missing"
assert r["runner_subprocess"]["exit_code"] == 0
# Production-shape specimens carry no _test_overrides, so the
# envelope should report test_overrides=null.
assert r.get("test_overrides") is None, "expected null test_overrides for production-shape run"

# top-level pid is the worker.
assert r["pid"] == r["runner_subprocess"]["pid"], "top-level pid should equal runner_subprocess.pid"

# Step: validator predicted allow, attempt observed ok, drift false.
assert len(r["steps"]) == 1
s = r["steps"][0]
assert s["sandbox_check"]["outcome"] == "allow"
assert s["attempt"]["outcome"] == "ok"
assert s["attempt"]["observed_path"] == "/private/etc/hosts"
assert s["drift"] is False, "drift expected False got {0}".format(s["drift"])
print("ok: v4 envelope, validator+worker subprocesses present, drift=false")
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${assert_log}" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${assert_log}\",\"stdout\":\"${run_stdout}\"}"
    return 0
  fi
  test_pass "C-worker path produces complete v4 envelope; drift=false for matching allow/ok" "{\"stdout\":\"${run_stdout}\"}"
}

# ---- test_id: bare_deny_default ------------------------------------------

run_bare_deny_default() {
  local test_id="bare_deny_default"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "run" "the downstream bug-report shape: (deny default) produces a coherent envelope on the C-worker path"

  if ! require_pw_app "${PW_BIN}"; then exit 0; fi

  local specimen="${PW_TEST_ARTIFACTS}/specimen.json"
  cat >"${specimen}" <<'EOF'
{
  "schema_version": 1,
  "specimen_id": "use_c_worker_deny_default",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1)(deny default)"
  },
  "probe_plan": [{
    "step_id": "s1",
    "sandbox_check": {
      "operation": "file-read-data",
      "filter": {"kind": "path", "value": "/etc/hosts"}
    },
    "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"}
  }]
}
EOF

  local run_stdout="${PW_TEST_ARTIFACTS}/run.json"
  set +e
  "${PW_BIN}" run "${specimen}" >"${run_stdout}" 2>/dev/null
  local rc=$?
  set -e
  if [[ "${rc}" -ne 0 ]]; then
    test_fail "specimen failed (rc=${rc})" "{\"stdout\":\"${run_stdout}\"}"
    return 0
  fi

  local assert_log="${PW_TEST_ARTIFACTS}/assert.log"
  set +e
  /usr/bin/python3 - "${run_stdout}" >"${assert_log}" 2>&1 <<'PY'
import json, sys
env = json.loads(open(sys.argv[1]).read())
r = env["data"]["runner_result"]

# The run itself succeeded — both children completed cleanly.
# The libsandbox-drift design property says the envelope should carry
# the verdict AND the observation even when they disagree.
assert r["normalized_outcome"] == "ok", "outcome {0}".format(r["normalized_outcome"])
assert r["rc"] == 0
assert r["runner_subprocess"]["exit_code"] == 0, "worker should clean-exit under (deny default)"

s = r["steps"][0]
# Validator predicted deny; kernel actually denied; both agree.
assert s["sandbox_check"]["outcome"] == "deny", "sb={0}".format(s["sandbox_check"]["outcome"])
assert s["attempt"]["rc"] == 1, "attempt rc={0}".format(s["attempt"]["rc"])
# EPERM=1 or EACCES=13.
assert s["attempt"]["errno"] in (1, 13), "attempt errno={0}".format(s["attempt"]["errno"])
assert s["attempt"]["outcome"] == "open_failed"
assert s["drift"] is False, "drift expected False (both deny) got {0}".format(s["drift"])

print("ok: worker survived (deny default); validator+attempt agree on deny; drift=false")
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${assert_log}" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${assert_log}\",\"stdout\":\"${run_stdout}\"}"
    return 0
  fi
  test_pass "bug-report (deny default) shape: worker survives, verdict+observation both deny, drift=false" "{\"stdout\":\"${run_stdout}\"}"
}

# ---- test_id: prediction_unavailable_pair --------------------------------

run_prediction_unavailable_pair() {
  local test_id="prediction_unavailable_pair"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "run" "an op+filter pair in the prediction_unavailable set: orchestrator skips the validator probe, synthesizes the verdict directly"

  if ! require_pw_app "${PW_BIN}"; then exit 0; fi

  local specimen="${PW_TEST_ARTIFACTS}/specimen.json"
  cat >"${specimen}" <<'EOF'
{
  "schema_version": 1,
  "specimen_id": "use_c_worker_prediction_unavailable",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1)(allow default)(deny iokit-open-service (iokit-registry-entry-class \"IOSurfaceRoot\"))"
  },
  "probe_plan": [{
    "step_id": "s1",
    "sandbox_check": {
      "operation": "iokit-open-service",
      "filter": {"kind": "iokit_registry_entry_class", "value": "IOSurfaceRoot"}
    },
    "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"}
  }]
}
EOF

  local run_stdout="${PW_TEST_ARTIFACTS}/run.json"
  set +e
  "${PW_BIN}" run "${specimen}" >"${run_stdout}" 2>/dev/null
  local rc=$?
  set -e
  if [[ "${rc}" -ne 0 ]]; then
    test_fail "specimen failed (rc=${rc})" "{\"stdout\":\"${run_stdout}\"}"
    return 0
  fi

  local assert_log="${PW_TEST_ARTIFACTS}/assert.log"
  set +e
  /usr/bin/python3 - "${run_stdout}" >"${assert_log}" 2>&1 <<'PY'
import json, sys
env = json.loads(open(sys.argv[1]).read())
r = env["data"]["runner_result"]
s = r["steps"][0]

# Verdict was synthesized — validator was never asked.
assert s["sandbox_check"]["outcome"] == "prediction_unavailable", \
    "sb_outcome={0}".format(s["sandbox_check"]["outcome"])
assert s["sandbox_check"]["rc"] == -1, \
    "rc sentinel expected -1, got {0}".format(s["sandbox_check"]["rc"])
# drift undefined for prediction_unavailable cases.
assert s["drift"] is None, \
    "drift should be null for prediction_unavailable, got {0}".format(s["drift"])
# The attempt still ran (and succeeded under allow default + the iokit
# deny that doesn't cover /etc/hosts file reads).
assert s["attempt"]["outcome"] == "ok"
print("ok: prediction_unavailable verdict synthesized; validator not asked; drift=null")
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${assert_log}" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${assert_log}\",\"stdout\":\"${run_stdout}\"}"
    return 0
  fi
  test_pass "(op,filter) in prediction_unavailable set: verdict synthesized, drift=null" "{\"stdout\":\"${run_stdout}\"}"
}

# ---- test_id: duplicate_step_id_rejected (PR H #1 regression) ------------

run_duplicate_step_id_rejected() {
  local test_id="duplicate_step_id_rejected"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "run" "two probe steps with the same step_id → bad_request (used to trap the Dictionary join and kill the XPC service)"

  if ! require_pw_app "${PW_BIN}"; then exit 0; fi

  local specimen="${PW_TEST_ARTIFACTS}/specimen.json"
  cat >"${specimen}" <<'EOF'
{
  "schema_version": 1,
  "specimen_id": "use_c_worker_dup_step_id",
  "policy": {"format": "sbpl", "sbpl_source": "(version 1)(allow default)"},
  "probe_plan": [
    {"step_id": "dup", "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/etc/hosts"}}, "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"}},
    {"step_id": "dup", "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/etc/hosts"}}, "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"}}
  ]
}
EOF

  local run_stdout="${PW_TEST_ARTIFACTS}/run.json"
  set +e
  "${PW_BIN}" run "${specimen}" >"${run_stdout}" 2>/dev/null
  set -e

  local assert_log="${PW_TEST_ARTIFACTS}/assert.log"
  set +e
  /usr/bin/python3 - "${run_stdout}" >"${assert_log}" 2>&1 <<'PY'
import json, sys
env = json.loads(open(sys.argv[1]).read())
r = env["data"]["runner_result"]
assert r["normalized_outcome"] == "bad_request", "outcome={0}".format(r["normalized_outcome"])
assert r["rc"] == 1
assert "duplicate step_id" in (r.get("error") or ""), \
    "error should name the duplicate: {0!r}".format(r.get("error"))
assert r.get("runner_subprocess") is None, "no worker should have spawned"
assert r.get("validator_subprocess") is None, "no validator should have spawned"
assert r["steps"] == []
print("ok: duplicate step_id rejected pre-spawn as bad_request")
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${assert_log}" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${assert_log}\",\"stdout\":\"${run_stdout}\"}"
    return 0
  fi
  test_pass "duplicate step_id → bad_request before spawn (no XPC crash)" "{\"stdout\":\"${run_stdout}\"}"
}

# ---- test_id: unsupported_attempt_per_step_skip --------------------------

run_unsupported_attempt_per_step_skip() {
  local test_id="unsupported_attempt_per_step_skip"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "run" "unknown (kind, action) combo → per-step attempt.outcome=unsupported (run still ok; sibling step + sandbox_check verdict survive)"

  if ! require_pw_app "${PW_BIN}"; then exit 0; fi

  # Two probes: a valid file probe and one with an unknown
  # attempt (kind, action). Pins both halves of the per-step skip
  # contract: the good step runs normally AND the unrecognized
  # step's sandbox_check verdict still runs while its attempt
  # surfaces as outcome=unsupported.
  local specimen="${PW_TEST_ARTIFACTS}/specimen.json"
  cat >"${specimen}" <<'EOF'
{
  "schema_version": 1,
  "specimen_id": "use_c_worker_mixed_attempt_support",
  "policy": {"format": "sbpl", "sbpl_source": "(version 1)(deny default)(allow file-read*)"},
  "probe_plan": [
    {"step_id": "good",
     "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/etc/hosts"}},
     "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"}},
    {"step_id": "unknown_attempt",
     "sandbox_check": {"operation": "iokit-open-user-client", "filter": {"kind": "none"}},
     "attempt": {"kind": "iokit", "action": "open", "target": "irrelevant"}}
  ]
}
EOF

  local run_stdout="${PW_TEST_ARTIFACTS}/run.json"
  set +e
  "${PW_BIN}" run "${specimen}" >"${run_stdout}" 2>/dev/null
  set -e

  local assert_log="${PW_TEST_ARTIFACTS}/assert.log"
  set +e
  /usr/bin/python3 - "${run_stdout}" >"${assert_log}" 2>&1 <<'PY'
import json, sys
env = json.loads(open(sys.argv[1]).read())
r = env["data"]["runner_result"]

# Run completes; the unsupported-attempt step doesn't kill the plan.
assert r["normalized_outcome"] == "ok", "outcome={0!r}".format(r["normalized_outcome"])
assert r["rc"] == 0

steps = r["steps"]
assert len(steps) == 2, "expected both steps in envelope, got {0}".format(len(steps))

# Step 0: the good probe runs end-to-end as a sanity check.
good = steps[0]
assert good["step_id"] == "good"
assert good["sandbox_check"]["outcome"] == "allow", good["sandbox_check"]
assert good["attempt"]["outcome"] == "ok", good["attempt"]
assert good["drift"] is False, "drift={0!r}".format(good["drift"])

# Step 1: unknown attempt kind. sandbox_check still ran (none-filter
# probe under the iokit-open-user-client op isn't in the
# prediction-unavailable set), attempt is unsupported, drift is null.
ua = steps[1]
assert ua["step_id"] == "unknown_attempt"
sb = ua["sandbox_check"]
assert sb["outcome"] in ("allow", "deny"), "sandbox_check should produce a verdict, got {0!r}".format(sb["outcome"])
at = ua["attempt"]
assert at["outcome"] == "unsupported", "attempt.outcome={0!r}".format(at["outcome"])
err = at.get("error") or ""
assert "iokit" in err and "open" in err, "attempt.error should name kind+action, got {0!r}".format(err)
assert ua["drift"] is None, "drift should be null when attempt didn't produce a verdict, got {0!r}".format(ua["drift"])

print("ok: unknown attempt downgrades to per-step skip; sibling step + sandbox_check verdict survive")
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${assert_log}" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${assert_log}\",\"stdout\":\"${run_stdout}\"}"
    return 0
  fi
  test_pass "unknown attempt → per-step skip; sibling step + sandbox_check verdict survive" "{\"stdout\":\"${run_stdout}\"}"
}

# ---- test_id: worker_timeout_ms_honored (PR H #3 regression) ------------

run_worker_timeout_ms_honored() {
  local test_id="worker_timeout_ms_honored"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "run" "worker_timeout_ms=500 + worker_post_apply_hang_ms=1500 → runner_timeout (used to be ignored, returning ok after the full hang)"

  if ! require_pw_app "${PW_BIN}"; then exit 0; fi

  local specimen="${PW_TEST_ARTIFACTS}/specimen.json"
  cat >"${specimen}" <<'EOF'
{
  "schema_version": 1,
  "specimen_id": "use_c_worker_timeout",
  "policy": {"format": "sbpl", "sbpl_source": "(version 1)(allow default)"},
  "probe_plan": [{
    "step_id": "s1",
    "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/etc/hosts"}},
    "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"}
  }],
  "_test_overrides": {
    "worker_timeout_ms": 500,
    "worker_post_apply_hang_ms": 1500
  }
}
EOF

  local run_stdout="${PW_TEST_ARTIFACTS}/run.json"
  set +e
  "${PW_BIN}" run "${specimen}" >"${run_stdout}" 2>/dev/null
  set -e

  local assert_log="${PW_TEST_ARTIFACTS}/assert.log"
  set +e
  /usr/bin/python3 - "${run_stdout}" >"${assert_log}" 2>&1 <<'PY'
import json, sys
env = json.loads(open(sys.argv[1]).read())
r = env["data"]["runner_result"]
assert r["normalized_outcome"] == "runner_timeout", "outcome={0}".format(r["normalized_outcome"])
assert r["rc"] == 1
# Mirror-back of both overrides should survive into the response.
to = r["test_overrides"]
assert to["worker_timeout_ms"] == 500
assert to["worker_post_apply_hang_ms"] == 1500
print("ok: worker_timeout_ms drives the C-worker sentinel deadline; outcome=runner_timeout")
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${assert_log}" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${assert_log}\",\"stdout\":\"${run_stdout}\"}"
    return 0
  fi
  test_pass "worker_timeout_ms honored on C-worker path (sentinel fires before hang completes)" "{\"stdout\":\"${run_stdout}\"}"
}

# ---- test_id: drift_null_for_non_policy_failure (PR H #5 regression) ----
#
# The audit reproducer: (allow default) + mach_lookup of a missing
# service. Validator says allow (per the policy). bootstrap_look_up
# returns BOOTSTRAP_UNKNOWN_SERVICE (kr=1102) because the service
# doesn't exist — not because the sandbox denied it. Pre-fix the
# orchestrator treated every non-ok attempt as a deny observation,
# so this case surfaced as drift=true. Post-fix the orchestrator
# inspects the failure kind: only EPERM/EACCES on file and
# BOOTSTRAP_NOT_PRIVILEGED (kr=1100) on mach count as denials.

run_drift_null_for_non_policy_failure() {
  local test_id="drift_null_for_non_policy_failure"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "run" "(allow default) + mach_lookup of a missing service → drift=null (BOOTSTRAP_UNKNOWN_SERVICE isn't a sandbox verdict; used to surface as drift=true)"

  if ! require_pw_app "${PW_BIN}"; then exit 0; fi

  local specimen="${PW_TEST_ARTIFACTS}/specimen.json"
  cat >"${specimen}" <<'EOF'
{
  "schema_version": 1,
  "specimen_id": "use_c_worker_unknown_service_drift",
  "policy": {"format": "sbpl", "sbpl_source": "(version 1)(allow default)"},
  "probe_plan": [{
    "step_id": "s_unknown_service",
    "sandbox_check": {"operation": "mach-lookup", "filter": {"kind": "global_name", "value": "com.pw.test.no-such-service"}},
    "attempt": {"kind": "mach_lookup", "action": "bootstrap_look_up", "target": "com.pw.test.no-such-service"}
  }]
}
EOF

  local run_stdout="${PW_TEST_ARTIFACTS}/run.json"
  set +e
  "${PW_BIN}" run "${specimen}" >"${run_stdout}" 2>/dev/null
  set -e

  local assert_log="${PW_TEST_ARTIFACTS}/assert.log"
  set +e
  /usr/bin/python3 - "${run_stdout}" >"${assert_log}" 2>&1 <<'PY'
import json, sys
env = json.loads(open(sys.argv[1]).read())
r = env["data"]["runner_result"]
assert r["normalized_outcome"] == "ok", "outcome={0}".format(r["normalized_outcome"])
s = r["steps"][0]
# Validator predicts allow (the service name isn't in any deny rule).
assert s["sandbox_check"]["outcome"] == "allow", \
    "validator should allow unknown service under (allow default): {0}".format(s["sandbox_check"]["outcome"])
# Attempt failed at the kernel: BOOTSTRAP_UNKNOWN_SERVICE.
assert s["attempt"]["outcome"] == "lookup_failed", \
    "attempt outcome: {0}".format(s["attempt"]["outcome"])
err = s["attempt"].get("error") or ""
assert "kr=1102" in err, "error should name BOOTSTRAP_UNKNOWN_SERVICE kr=1102: {0!r}".format(err)
# Critical: drift must be null. Pre-fix it was true because every
# non-ok attempt counted as a deny observation.
assert s["drift"] is None, \
    "drift should be null for non-policy failure (kr=1102), got {0}".format(s["drift"])
print("ok: missing-service lookup yields drift=null (not libsandbox drift)")
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${assert_log}" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${assert_log}\",\"stdout\":\"${run_stdout}\"}"
    return 0
  fi
  test_pass "drift=null for BOOTSTRAP_UNKNOWN_SERVICE (non-policy failure)" "{\"stdout\":\"${run_stdout}\"}"
}

# ---- test_id: sandbox_check_pid_matches_worker (PR H #7 regression) ------

run_sandbox_check_pid_matches_worker() {
  local test_id="sandbox_check_pid_matches_worker"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "run" "sandbox_check.pid on every step matches the worker PID (pre-fix was 0 for validator-backed, host PID for synthesized)"

  if ! require_pw_app "${PW_BIN}"; then exit 0; fi

  local specimen="${PW_TEST_ARTIFACTS}/specimen.json"
  cat >"${specimen}" <<'EOF'
{
  "schema_version": 1,
  "specimen_id": "use_c_worker_sb_pid",
  "policy": {"format": "sbpl", "sbpl_source": "(version 1)(allow default)"},
  "probe_plan": [
    {"step_id": "s_validator", "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/etc/hosts"}}, "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"}},
    {"step_id": "s_synth", "sandbox_check": {"operation": "iokit-open-service", "filter": {"kind": "iokit_registry_entry_class", "value": "IOSurfaceRoot"}}, "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"}}
  ]
}
EOF

  local run_stdout="${PW_TEST_ARTIFACTS}/run.json"
  set +e
  "${PW_BIN}" run "${specimen}" >"${run_stdout}" 2>/dev/null
  set -e

  local assert_log="${PW_TEST_ARTIFACTS}/assert.log"
  set +e
  /usr/bin/python3 - "${run_stdout}" >"${assert_log}" 2>&1 <<'PY'
import json, sys
env = json.loads(open(sys.argv[1]).read())
r = env["data"]["runner_result"]
worker_pid = r["runner_subprocess"]["pid"]
for s in r["steps"]:
    sb_pid = s["sandbox_check"]["pid"]
    assert sb_pid == worker_pid, \
        "step {0}: sandbox_check.pid={1}, expected worker_pid={2}".format(s["step_id"], sb_pid, worker_pid)
print("ok: sandbox_check.pid == worker_pid for both validator-backed and synthesized verdicts")
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${assert_log}" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${assert_log}\",\"stdout\":\"${run_stdout}\"}"
    return 0
  fi
  test_pass "sandbox_check.pid is the worker PID on both validator-backed and synthesized verdicts" "{\"stdout\":\"${run_stdout}\"}"
}

run_happy_default_allow
run_bare_deny_default
run_prediction_unavailable_pair
# ---- test_id: drift_null_for_dac_eacces (PR I #1 regression) -------------
#
# A real chmod 000 file owned by us returns EACCES from open(),
# despite policy (allow default). The validator predicts allow, the
# attempt observes EACCES — but the denial came from filesystem DAC,
# not from the kernel sandbox. Reporting drift=true would be dishonest
# attribution (validator was right about sandbox; the failure had
# nothing to do with libsandbox). Post-fix the orchestrator
# classifies file EPERM/EACCES as deniedAmbiguous and returns
# drift=null for the (allow, ambiguous) case.

run_drift_null_for_dac_eacces() {
  local test_id="drift_null_for_dac_eacces"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "run" "(allow default) + file with mode 000 → drift=null (EACCES is ambiguous between sandbox and DAC; used to surface as drift=true)"

  if ! require_pw_app "${PW_BIN}"; then exit 0; fi

  local target="${PW_TEST_ARTIFACTS}/no-read.txt"
  : >"${target}"
  chmod 000 "${target}"
  # Cleanup on exit so the artifacts dir can be removed cleanly.
  trap 'chmod 600 "'"${target}"'" 2>/dev/null || true' RETURN

  local specimen="${PW_TEST_ARTIFACTS}/specimen.json"
  /usr/bin/python3 - "${specimen}" "${target}" <<'PY'
import json, sys
from pathlib import Path
spec = {
    "schema_version": 1,
    "specimen_id": "use_c_worker_dac_eacces_drift",
    "policy": {"format": "sbpl", "sbpl_source": "(version 1)(allow default)"},
    "probe_plan": [{
        "step_id": "s_dac",
        "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": sys.argv[2]}},
        "attempt": {"kind": "file", "action": "open_read", "target": sys.argv[2]},
    }],
}
Path(sys.argv[1]).write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

  local run_stdout="${PW_TEST_ARTIFACTS}/run.json"
  set +e
  "${PW_BIN}" run "${specimen}" >"${run_stdout}" 2>/dev/null
  set -e

  local assert_log="${PW_TEST_ARTIFACTS}/assert.log"
  set +e
  /usr/bin/python3 - "${run_stdout}" >"${assert_log}" 2>&1 <<'PY'
import json, sys
env = json.loads(open(sys.argv[1]).read())
r = env["data"]["runner_result"]
assert r["normalized_outcome"] == "ok"
s = r["steps"][0]
# Validator predicts allow under (allow default).
assert s["sandbox_check"]["outcome"] == "allow", \
    "validator should allow under (allow default): {0}".format(s["sandbox_check"]["outcome"])
assert s["attempt"]["outcome"] == "open_failed"
# EACCES = 13. The kernel returned it; we don't know if sandbox or
# DAC caused it.
assert s["attempt"]["errno"] == 13, "expected EACCES (13), got {0}".format(s["attempt"]["errno"])
# Critical: drift must be null. (allow, ambiguous-deny) → null per
# the asymmetric drift rule.
assert s["drift"] is None, \
    "drift should be null for (allow, ambiguous-EACCES), got {0}".format(s["drift"])
print("ok: DAC EACCES yields drift=null when validator predicts allow")
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${assert_log}" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${assert_log}\",\"stdout\":\"${run_stdout}\"}"
    return 0
  fi
  test_pass "drift=null for DAC EACCES (validator=allow, observation=ambiguous)" "{\"stdout\":\"${run_stdout}\"}"
}

# ---- test_id: access_failure_classified (PR I #2 regression) -------------
#
# A file/access attempt that fails with EPERM/EACCES used to land as
# attempt.outcome="unsupported" because buildAttemptResult had no
# case for attemptActionAccess. Post-fix the C worker's access(R_OK)
# call is mapped to AttemptOutcome.accessFailed with the errno
# preserved.

run_access_failure_classified() {
  local test_id="access_failure_classified"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "run" "(deny file-read-data /private/etc) + file/access on /etc/hosts → outcome=access_failed (was 'unsupported')"

  if ! require_pw_app "${PW_BIN}"; then exit 0; fi

  local specimen="${PW_TEST_ARTIFACTS}/specimen.json"
  cat >"${specimen}" <<'EOF'
{
  "schema_version": 1,
  "specimen_id": "use_c_worker_access_failed",
  "policy": {"format": "sbpl", "sbpl_source": "(version 1)(allow default)(deny file-read-data (subpath \"/private/etc\"))"},
  "probe_plan": [{
    "step_id": "s_access",
    "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/etc/hosts"}},
    "attempt": {"kind": "file", "action": "access", "target": "/etc/hosts"}
  }]
}
EOF

  local run_stdout="${PW_TEST_ARTIFACTS}/run.json"
  set +e
  "${PW_BIN}" run "${specimen}" >"${run_stdout}" 2>/dev/null
  set -e

  local assert_log="${PW_TEST_ARTIFACTS}/assert.log"
  set +e
  /usr/bin/python3 - "${run_stdout}" >"${assert_log}" 2>&1 <<'PY'
import json, sys
env = json.loads(open(sys.argv[1]).read())
r = env["data"]["runner_result"]
s = r["steps"][0]
# Attempt was access(R_OK) which the worker DOES run. It fails
# because the deny rule covers /private/etc (canonical form of
# /etc/hosts). Pre-fix the orchestrator surfaced this as
# outcome=unsupported even though the syscall ran.
assert s["attempt"]["outcome"] == "access_failed", \
    "expected outcome=access_failed, got {0!r} (pre-fix this was 'unsupported')".format(s["attempt"]["outcome"])
assert s["attempt"]["rc"] == 1
# EPERM (1) or EACCES (13). The kernel sandbox kills the access
# call; either errno is plausible across macOS revisions.
assert s["attempt"]["errno"] in (1, 13), \
    "expected EPERM/EACCES, got {0}".format(s["attempt"]["errno"])
print("ok: file/access failure classified as access_failed (not unsupported)")
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${assert_log}" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${assert_log}\",\"stdout\":\"${run_stdout}\"}"
    return 0
  fi
  test_pass "file/access failure surfaces as access_failed with errno preserved" "{\"stdout\":\"${run_stdout}\"}"
}

# ---- test_id: exec_attempt_without_baseline_fails_cleanly ----------------
#
# Drives the wire+orchestrator integration for the new `exec` /
# `spawn` attempt kind end-to-end. Under `(deny default)` with no
# augment, posix_spawn is denied by the kernel sandbox; the
# orchestrator must surface this as outcome=exec_failed with
# child_pid==0 and errno∈{EPERM,EACCES}. That sentinel pair is the
# clean "sandbox blocked spawn" tell — anything else (child_pid>0,
# or a different errno, or a setup-failure error string) means the
# resource-setup model has regressed and the witness is no longer
# honest.
#
# Augmented-success coverage (an exec attempt that actually runs
# under deny-default + the shipped exec_baseline augment) lands
# alongside the empirical exec_baseline.sb in checkpoint 4.

run_exec_attempt_without_baseline_fails_cleanly() {
  local test_id="exec_attempt_without_baseline_fails_cleanly"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "run" "(deny default) + exec /usr/bin/true → exec_failed with child_pid=0, errno EPERM/EACCES from posix_spawn"

  if ! require_pw_app "${PW_BIN}"; then exit 0; fi

  local specimen="${PW_TEST_ARTIFACTS}/specimen.json"
  cat >"${specimen}" <<'EOF'
{
  "schema_version": 1,
  "specimen_id": "use_c_worker_exec_unaugmented",
  "policy": {"format": "sbpl", "sbpl_source": "(version 1)(deny default)"},
  "probe_plan": [{
    "step_id": "s_exec",
    "sandbox_check": {"operation": "process-exec*", "filter": {"kind": "path", "value": "/usr/bin/true"}},
    "attempt": {"kind": "exec", "action": "spawn", "target": "/usr/bin/true"}
  }]
}
EOF

  local run_stdout="${PW_TEST_ARTIFACTS}/run.json"
  set +e
  "${PW_BIN}" run "${specimen}" >"${run_stdout}" 2>/dev/null
  set -e

  local assert_log="${PW_TEST_ARTIFACTS}/assert.log"
  set +e
  /usr/bin/python3 - "${run_stdout}" >"${assert_log}" 2>&1 <<'PY'
import json, sys
env = json.loads(open(sys.argv[1]).read())
r = env["data"]["runner_result"]

# Run itself completed cleanly — the worker spawned, applied the
# policy, ran the attempt (which was denied), and exited.
assert r["normalized_outcome"] == "ok", "outcome={0}".format(r["normalized_outcome"])
assert r["runner_subprocess"]["exit_code"] == 0, \
    "worker should clean-exit even when its attempt is denied"

s = r["steps"][0]
# Prediction channel: process-exec* + path is a working sandbox_check
# invocation (the canonical SBPL operation name carries the star;
# the unstar'd "process-exec" returns EINVAL from sandbox_check on
# this macOS revision). The validator should predict deny against
# (deny default).
assert s["sandbox_check"]["outcome"] == "deny", \
    "sandbox_check outcome={0!r} (validator should predict deny under deny-default)".format(
        s["sandbox_check"]["outcome"])
# Both channels agree on deny, so drift is False, not None.
assert s.get("drift") is False, \
    "drift should be False (validator+attempt agree on deny); got {0!r}".format(s.get("drift"))

a = s["attempt"]
assert a["outcome"] == "exec_failed", \
    "expected outcome=exec_failed, got {0!r}".format(a["outcome"])
assert a["rc"] == -1, "spawn-failure rc sentinel: expected -1, got {0}".format(a["rc"])
# THE LOAD-BEARING PIN: child_pid must be 0. If it's > 0, spawn
# actually happened and the failure was the child's own exit code —
# that would mean the worker's resource-setup model leaked
# post-apply or the deny default policy isn't blocking spawn.
assert a["child_pid"] == 0, \
    "child_pid must be 0 when posix_spawn was blocked; got {0}".format(a["child_pid"])
# EPERM (1) or EACCES (13) from posix_spawn. Anything else means
# the failure came from a different source (e.g., a pre-spawn
# setup syscall) — also a witness-honesty regression.
assert a["errno"] in (1, 13), \
    "expected EPERM/EACCES from posix_spawn; got errno={0}".format(a["errno"])
# Error string should identify posix_spawn — pins the message
# format so a future refactor can't silently move the failure
# attribution.
assert a.get("error") and "posix_spawn" in a["error"], \
    "error should identify posix_spawn; got {0!r}".format(a.get("error"))
# child_exit_code stays at the "no child ran" sentinel.
assert a["child_exit_code"] == -1, \
    "child_exit_code sentinel for spawn failure: expected -1, got {0}".format(a["child_exit_code"])
assert a["child_term_signal"] == 0, \
    "child_term_signal sentinel for spawn failure: expected 0, got {0}".format(a["child_term_signal"])

print("ok: unaugmented exec fails cleanly via posix_spawn — child_pid=0, errno {0}".format(a["errno"]))
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${assert_log}" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${assert_log}\",\"stdout\":\"${run_stdout}\"}"
    return 0
  fi
  test_pass "unaugmented exec under (deny default) → posix_spawn EPERM/EACCES with child_pid=0" "{\"stdout\":\"${run_stdout}\"}"
}

# ---- test_id: exec_attempt_with_baseline_succeeds ------------------------
#
# Companion to exec_attempt_without_baseline_fails_cleanly. Same
# (deny default) policy, but the caller opts into the shipped
# `exec_baseline` augment. The controller splices the augment into
# the caller's source; the worker compiles the spliced bytes and
# posix_spawn now succeeds. Pins the user-facing contract that
# `augments: ["exec_baseline"]` is sufficient to let a
# libSystem-dynamic helper run under minimal-deny.
#
# Asserts:
#   - normalized_outcome == "ok"
#   - data.policy_augmentation present, applied == ["exec_baseline"],
#     original_sha256 != applied_sha256
#   - runner_result.policy_sha256 == applied_sha256
#     (proves the runner compiled the spliced source, not the
#     pre-splice source)
#   - attempt.outcome == "ok" with child_pid > 0, child_exit_code == 0,
#     stdout round-trips the helper's marker line

run_exec_attempt_with_baseline_succeeds() {
  local test_id="exec_attempt_with_baseline_succeeds"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "build" "compile exec_fixture/helper.c"
  if ! require_pw_app "${PW_BIN}"; then exit 0; fi
  if ! ensure_exec_fixture; then
    test_skip "could not build exec_fixture helper (clang missing?)" \
      "{\"src\":\"${EXEC_FIXTURE_SRC}\"}"
    return 0
  fi
  test_step "run" "(deny default) + augments:[exec_baseline] + exec fixture helper → ok"

  local specimen="${PW_TEST_ARTIFACTS}/specimen.json"
  /usr/bin/python3 - "${specimen}" "${EXEC_FIXTURE_BIN}" <<'PY'
import json, sys
spec = {
  "schema_version": 1,
  "specimen_id": "use_c_worker_exec_baseline_succeeds",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1)\n(deny default)\n",
    "augments": ["exec_baseline"],
  },
  "probe_plan": [{
    "step_id": "s_exec",
    "sandbox_check": {"operation": "process-exec*",
                      "filter": {"kind": "path", "value": sys.argv[2]}},
    "attempt": {"kind": "exec", "action": "spawn", "target": sys.argv[2]},
  }],
}
open(sys.argv[1], "w").write(json.dumps(spec))
PY

  local run_stdout="${PW_TEST_ARTIFACTS}/run.json"
  set +e
  "${PW_BIN}" run "${specimen}" >"${run_stdout}" 2>/dev/null
  set -e

  local assert_log="${PW_TEST_ARTIFACTS}/assert.log"
  set +e
  /usr/bin/python3 - "${run_stdout}" >"${assert_log}" 2>&1 <<'PY'
import json, sys
env = json.loads(open(sys.argv[1]).read())
assert env["result"]["normalized_outcome"] == "ok", \
    "top-level outcome={0}".format(env["result"]["normalized_outcome"])

aug = env["data"].get("policy_augmentation")
assert aug is not None, "data.policy_augmentation missing on augmented run"
assert aug["applied"] == ["exec_baseline"], \
    "applied={0!r}".format(aug["applied"])
assert aug["original_sha256"] != aug["applied_sha256"], \
    "hashes should differ when augment splices content"

r = env["data"]["runner_result"]
assert r["policy_sha256"] == aug["applied_sha256"], \
    "runner_result.policy_sha256 ({0}) != applied_sha256 ({1}) — runner did not compile spliced source".format(
        r["policy_sha256"], aug["applied_sha256"])

s = r["steps"][0]
# Prediction channel: validator must predict allow against the
# spliced (deny default) + exec_baseline policy. Pins that the
# validator (a) accepts process-exec* + path and (b) sees the
# spliced policy, not the pre-splice source. drift=false because
# attempt + validator both say allow.
assert s["sandbox_check"]["outcome"] == "allow", \
    "sandbox_check should predict allow when augment grants process-exec*; got {0!r}".format(
        s["sandbox_check"]["outcome"])
assert s.get("drift") is False, \
    "drift should be False (validator+attempt agree on allow); got {0!r}".format(s.get("drift"))

a = s["attempt"]
assert a["outcome"] == "ok", "attempt outcome={0}".format(a["outcome"])
assert a["rc"] == 0, "attempt rc={0}".format(a["rc"])
assert a["child_pid"] > 0, "child_pid={0} (spawn should have produced a child)".format(a["child_pid"])
assert a["child_exit_code"] == 0, "child_exit_code={0}".format(a["child_exit_code"])
assert a["child_term_signal"] == 0, "child_term_signal={0}".format(a["child_term_signal"])
assert a.get("stdout") == "exec_fixture: hello from helper\n", \
    "stdout round-trip mismatch: {0!r}".format(a.get("stdout"))
assert a.get("stderr") is None, "stderr={0!r}".format(a.get("stderr"))

print("ok: augmented exec under (deny default) reached ok via exec_baseline; prediction agrees")
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${assert_log}" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${assert_log}\",\"stdout\":\"${run_stdout}\"}"
    return 0
  fi
  test_pass "augmented exec under (deny default) reached ok via exec_baseline" \
    "{\"stdout\":\"${run_stdout}\"}"
}

# ---- test_id: exec_attempt_args_and_stderr_round_trip --------------------
#
# Drives the exec attempt with caller-supplied args + stderr output.
# Pins:
#   - args ["--stderr", "hello-stderr"] reach the helper as argv[1..]
#   - attempt.stderr round-trips the helper's stderr write
#   - attempt.stdout still carries the default marker
#   - exit code propagates (0 in this case)

run_exec_attempt_args_and_stderr_round_trip() {
  local test_id="exec_attempt_args_and_stderr_round_trip"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  if ! require_pw_app "${PW_BIN}"; then exit 0; fi
  if ! ensure_exec_fixture; then
    test_skip "could not build exec_fixture helper" \
      "{\"src\":\"${EXEC_FIXTURE_SRC}\"}"
    return 0
  fi
  test_step "run" "exec helper --stderr 'hello-stderr' → stderr round-trips, stdout still default"

  local specimen="${PW_TEST_ARTIFACTS}/specimen.json"
  /usr/bin/python3 - "${specimen}" "${EXEC_FIXTURE_BIN}" <<'PY'
import json, sys
spec = {
  "schema_version": 1,
  "specimen_id": "use_c_worker_exec_args_stderr",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1)\n(deny default)\n",
    "augments": ["exec_baseline"],
  },
  "probe_plan": [{
    "step_id": "s_exec_args",
    "sandbox_check": {"operation": "process-exec*",
                      "filter": {"kind": "path", "value": sys.argv[2]}},
    "attempt": {"kind": "exec", "action": "spawn", "target": sys.argv[2],
                "args": ["--stderr", "hello-stderr"]},
  }],
}
open(sys.argv[1], "w").write(json.dumps(spec))
PY

  local run_stdout="${PW_TEST_ARTIFACTS}/run.json"
  set +e
  "${PW_BIN}" run "${specimen}" >"${run_stdout}" 2>/dev/null
  set -e

  local assert_log="${PW_TEST_ARTIFACTS}/assert.log"
  set +e
  /usr/bin/python3 - "${run_stdout}" >"${assert_log}" 2>&1 <<'PY'
import json, sys
env = json.loads(open(sys.argv[1]).read())
s = env["data"]["runner_result"]["steps"][0]
assert s["sandbox_check"]["outcome"] == "allow", \
    "sandbox_check should predict allow under augment; got {0!r}".format(
        s["sandbox_check"]["outcome"])
assert s.get("drift") is False, \
    "drift should be False (validator+attempt agree); got {0!r}".format(s.get("drift"))
a = s["attempt"]
assert a["outcome"] == "ok", "outcome={0}".format(a["outcome"])
assert a["rc"] == 0
assert a.get("stdout") == "exec_fixture: hello from helper\n", \
    "stdout={0!r}".format(a.get("stdout"))
assert a.get("stderr") == "hello-stderr\n", \
    "stderr={0!r} (args may not have reached the helper)".format(a.get("stderr"))
print("ok: args reached helper, stdout/stderr round-tripped, prediction agrees")
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${assert_log}" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${assert_log}\",\"stdout\":\"${run_stdout}\"}"
    return 0
  fi
  test_pass "exec args + stdout/stderr round-trip through the worker" \
    "{\"stdout\":\"${run_stdout}\"}"
}

# ---- test_id: exec_attempt_stdout_truncation_marker ----------------------
#
# Helper writes more bytes to stdout than the slot can hold
# (PW_SHM_CHILD_OUTPUT_BYTES = 1024). The worker must truncate AND
# append the "... [truncated]" marker so a consumer can tell the
# output was capped.

run_exec_attempt_stdout_truncation_marker() {
  local test_id="exec_attempt_stdout_truncation_marker"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  if ! require_pw_app "${PW_BIN}"; then exit 0; fi
  if ! ensure_exec_fixture; then
    test_skip "could not build exec_fixture helper" \
      "{\"src\":\"${EXEC_FIXTURE_SRC}\"}"
    return 0
  fi
  test_step "run" "exec helper --stdout-bytes 4096 → captured up to 1023 bytes with truncation marker"

  local specimen="${PW_TEST_ARTIFACTS}/specimen.json"
  /usr/bin/python3 - "${specimen}" "${EXEC_FIXTURE_BIN}" <<'PY'
import json, sys
spec = {
  "schema_version": 1,
  "specimen_id": "use_c_worker_exec_truncation",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1)\n(deny default)\n",
    "augments": ["exec_baseline"],
  },
  "probe_plan": [{
    "step_id": "s_exec_trunc",
    "sandbox_check": {"operation": "process-exec*",
                      "filter": {"kind": "path", "value": sys.argv[2]}},
    "attempt": {"kind": "exec", "action": "spawn", "target": sys.argv[2],
                "args": ["--stdout-bytes", "4096"]},
  }],
}
open(sys.argv[1], "w").write(json.dumps(spec))
PY

  local run_stdout="${PW_TEST_ARTIFACTS}/run.json"
  set +e
  "${PW_BIN}" run "${specimen}" >"${run_stdout}" 2>/dev/null
  set -e

  local assert_log="${PW_TEST_ARTIFACTS}/assert.log"
  set +e
  /usr/bin/python3 - "${run_stdout}" >"${assert_log}" 2>&1 <<'PY'
import json, sys
env = json.loads(open(sys.argv[1]).read())
s = env["data"]["runner_result"]["steps"][0]
assert s["sandbox_check"]["outcome"] == "allow"
assert s.get("drift") is False
a = s["attempt"]
assert a["outcome"] == "ok", "outcome={0}".format(a["outcome"])
out = a.get("stdout") or ""
# Buffer is PW_SHM_CHILD_OUTPUT_BYTES (1024); reader is 1023 bytes + NUL.
# Truncation marker eats the tail: "\n... [truncated]" is 16 bytes.
assert len(out) > 0, "stdout should not be empty"
assert len(out) < 1024, "stdout {0} bytes should fit in the slot buffer".format(len(out))
assert "[truncated]" in out, "truncation marker missing from captured stdout (len={0})".format(len(out))
# Body should be 'A' fill before the marker.
body = out.split("\n... [truncated]")[0]
assert set(body) == {"A"}, "body should be 'A' fill, got chars {0!r}".format(set(body))
print("ok: stdout truncated to {0} bytes with marker; body is 'A' fill".format(len(out)))
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${assert_log}" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${assert_log}\",\"stdout\":\"${run_stdout}\"}"
    return 0
  fi
  test_pass "oversized stdout truncated with [truncated] marker" \
    "{\"stdout\":\"${run_stdout}\"}"
}

run_duplicate_step_id_rejected
run_unsupported_attempt_per_step_skip
run_worker_timeout_ms_honored
run_drift_null_for_non_policy_failure
run_sandbox_check_pid_matches_worker
run_drift_null_for_dac_eacces
run_access_failure_classified
run_exec_attempt_without_baseline_fails_cleanly
run_exec_attempt_with_baseline_succeeds
run_exec_attempt_args_and_stderr_round_trip
run_exec_attempt_stdout_truncation_marker
