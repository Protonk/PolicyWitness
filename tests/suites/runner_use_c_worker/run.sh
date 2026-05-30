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
  test_step "run" "_test_overrides.use_c_worker=true routes through pw-probe-runner + sb_api_validator --batch; full v4 envelope assembles"

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
  }],
  "_test_overrides": { "use_c_worker": true }
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
assert r["test_overrides"]["use_c_worker"] is True, "override not mirrored back"

# top-level pid is the worker (per v3+ contract; preserved at v4).
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
  test_pass "use_c_worker=true produces complete v4 envelope; drift=false for matching allow/ok" "{\"stdout\":\"${run_stdout}\"}"
}

# ---- test_id: bare_deny_default ------------------------------------------

run_bare_deny_default() {
  local test_id="bare_deny_default"
  test_begin "${PW_TEST_SUITE}" "${test_id}"
  test_step "run" "the downstream bug-report shape: (deny default) produces a coherent envelope on the C-worker path (Swift worker dies here)"

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
  }],
  "_test_overrides": { "use_c_worker": true }
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
  }],
  "_test_overrides": { "use_c_worker": true }
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

run_happy_default_allow
run_bare_deny_default
run_prediction_unavailable_pair
