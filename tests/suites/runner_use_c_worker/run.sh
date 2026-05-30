#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="runner_use_c_worker"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

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

# ---- test_id: unsupported_attempt_rejected (PR H #2 regression) ----------

run_unsupported_attempt_rejected() {
  local test_id="unsupported_attempt_rejected"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "run" "unknown (kind, action) combo → bad_request (used to silently report outcome=ok for an op that never ran)"

  if ! require_pw_app "${PW_BIN}"; then exit 0; fi

  local specimen="${PW_TEST_ARTIFACTS}/specimen.json"
  cat >"${specimen}" <<'EOF'
{
  "schema_version": 1,
  "specimen_id": "use_c_worker_bogus_attempt",
  "policy": {"format": "sbpl", "sbpl_source": "(version 1)(allow default)"},
  "probe_plan": [{
    "step_id": "s1",
    "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/etc/hosts"}},
    "attempt": {"kind": "file", "action": "totally_not_a_real_action", "target": "/etc/hosts"}
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
assert r["normalized_outcome"] == "bad_request", "outcome={0}".format(r["normalized_outcome"])
assert r["rc"] == 1
err = r.get("error") or ""
assert "unsupported attempt" in err, "error should name unsupported attempt: {0!r}".format(err)
assert "totally_not_a_real_action" in err, "error should echo the bad action: {0!r}".format(err)
assert r["steps"] == []
print("ok: unknown (kind, action) rejected pre-spawn as bad_request")
PY
  local arc=$?
  set -e
  if [[ "${arc}" -ne 0 ]]; then
    local msg
    msg="$(head -5 "${assert_log}" | tr '\n' ' ' | sed 's/"/\\"/g')"
    test_fail "${msg}" "{\"log\":\"${assert_log}\",\"stdout\":\"${run_stdout}\"}"
    return 0
  fi
  test_pass "unknown (kind, action) → bad_request (no silent ok)" "{\"stdout\":\"${run_stdout}\"}"
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

run_duplicate_step_id_rejected
run_unsupported_attempt_rejected
run_worker_timeout_ms_honored
run_drift_null_for_non_policy_failure
run_sandbox_check_pid_matches_worker
run_drift_null_for_dac_eacces
run_access_failure_classified
