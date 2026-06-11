#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="witness_contract"
PW_TEST_ID="drift_determination_via_validator_seam"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "stub validator forces a verdict that disagrees with a real attempt; assert the harness's drift determination (no live libsandbox bug needed)"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

# Why a stub validator. Real drift — libsandbox's userland sandbox_check
# disagreeing with kernel enforcement — is a libsandbox BUG we do not have a
# live example of; surfacing one is a PolicyWitness design goal, not a fixture
# we can rely on. To test how the harness *determines* drift without depending
# on such an example, we steer the validator's prediction (an INPUT to
# computeDrift) via `_test_overrides.validator_executable_path` and let the real
# C worker run the real attempt and the real computeDrift. Per the
# `_test_overrides` rule this is input-steering, not result-faking: the
# classifier and envelope assembly still run for real, and the run is
# self-describing (test_overrides is echoed).

# A stub validator that emits one verdict per probe with a fixed outcome.
make_stub() {  # $1=forced outcome (allow|deny)  $2=output path
  cat >"$2" <<PYEOF
#!/usr/bin/env python3
import json, sys
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        p = json.loads(line)
    except Exception:
        continue
    print(json.dumps({
        "kind": "sb_api_validator_verdict", "schema_version": 1,
        "step_id": p.get("step_id"), "operation": p.get("operation"),
        "filter_type": p.get("filter_type"), "filter_type_id": 1,
        "filter_value": p.get("filter_value"), "rc": 0, "errno": 0,
        "outcome": "$1",
    }))
    sys.stdout.flush()
PYEOF
  chmod +x "$2"
}

STUB_DENY="${PW_TEST_ARTIFACTS}/stub_validator_deny.py";  make_stub deny  "${STUB_DENY}"
STUB_ALLOW="${PW_TEST_ARTIFACTS}/stub_validator_allow.py"; make_stub allow "${STUB_ALLOW}"

write_spec() {  # $1=out path  $2=sbpl source  $3=validator stub path
  /usr/bin/python3 - "$1" "$2" "$3" <<'PY'
import json, sys
out, sbpl, stub = sys.argv[1], sys.argv[2], sys.argv[3]
spec = {
    "schema_version": 1,
    "specimen_id": "drift_seam",
    "policy": {"format": "sbpl", "sbpl_source": sbpl},
    "probe_plan": [{
        "step_id": "p1",
        "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "path", "value": "/etc/hosts"}},
        "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"},
    }],
    "_test_overrides": {"validator_executable_path": stub},
}
open(out, "w").write(json.dumps(spec, indent=2, sort_keys=True) + "\n")
PY
}

run_case() {  # $1=specimen  $2=stdout
  set +e
  "${PW_BIN}" run --no-log-capture "$1" >"$2" 2>/dev/null
  set -e
}

# Case A — prediction=deny vs a real SUCCESS. The read of /etc/hosts under
# (allow default) succeeds (observation=allow); the stub forces predict=deny.
# The disagreement is UNAMBIGUOUS (a success cannot be a DAC/missing-file
# artifact), so the harness must surface drift=true.
SPEC_TRUE="${PW_TEST_ARTIFACTS}/spec_drift_true.json"
RUN_TRUE="${PW_TEST_ARTIFACTS}/run_drift_true.json"
write_spec "${SPEC_TRUE}" "$(printf '(version 1)\n(allow default)\n')" "${STUB_DENY}"
run_case "${SPEC_TRUE}" "${RUN_TRUE}"

# Case B — prediction=allow vs a real DENY. The read is denied with EPERM under
# (deny file-read-data); the stub forces predict=allow. A predicted-allow that
# fails is AMBIGUOUS (could be sandbox or DAC), so the harness must NOT claim a
# false-positive drift — it reports drift=null ("no dishonest attribution").
SPEC_NULL="${PW_TEST_ARTIFACTS}/spec_drift_null.json"
RUN_NULL="${PW_TEST_ARTIFACTS}/run_drift_null.json"
write_spec "${SPEC_NULL}" "$(printf '(version 1) (allow default) (deny file-read-data)')" "${STUB_ALLOW}"
run_case "${SPEC_NULL}" "${RUN_NULL}"

ASSERT_LOG="${PW_TEST_ARTIFACTS}/assertions.log"
set +e
PW_RUN_TRUE="${RUN_TRUE}" PW_RUN_NULL="${RUN_NULL}" /usr/bin/python3 - >"${ASSERT_LOG}" 2>&1 <<'PY'
import json, os
from pathlib import Path

def load_step(path):
    env = json.loads(Path(path).read_text(encoding="utf-8"))
    rr = (env.get("data") or {}).get("runner_result") or {}
    if rr.get("normalized_outcome") == "bad_request" and "validator_executable_path" in (rr.get("error") or ""):
        raise SystemExit(
            "_test_overrides.validator_executable_path was rejected as an "
            "unrecognized field; the stub-validator seam is not plumbed."
        )
    if rr.get("normalized_outcome") != "ok":
        raise SystemExit(f"expected normalized_outcome=ok (got {rr.get('normalized_outcome')!r}); err={rr.get('error')!r}")
    if (rr.get("test_overrides") or {}).get("validator_executable_path") is None:
        raise SystemExit("expected test_overrides.validator_executable_path to be echoed (steered run must be self-describing)")
    steps = rr.get("steps") or []
    if len(steps) != 1:
        raise SystemExit(f"expected 1 step (got {len(steps)})")
    return steps[0]

# Case A: deny prediction vs real success -> drift True.
a = load_step(os.environ["PW_RUN_TRUE"])
if (a.get("sandbox_check") or {}).get("outcome") != "deny":
    raise SystemExit(f"A: expected steered prediction deny (got {(a.get('sandbox_check') or {}).get('outcome')!r})")
if (a.get("attempt") or {}).get("rc") != 0:
    raise SystemExit(f"A: expected the real read to succeed rc=0 (got {(a.get('attempt') or {}).get('rc')!r})")
if a.get("drift") is not True:
    raise SystemExit(f"A: expected drift=true (deny predicted, success observed) — got {a.get('drift')!r}")

# Case B: allow prediction vs ambiguous deny -> drift null (no false positive).
b = load_step(os.environ["PW_RUN_NULL"])
if (b.get("sandbox_check") or {}).get("outcome") != "allow":
    raise SystemExit(f"B: expected steered prediction allow (got {(b.get('sandbox_check') or {}).get('outcome')!r})")
if (b.get("attempt") or {}).get("rc") == 0:
    raise SystemExit("B: expected the real read to be denied (rc!=0) under (deny file-read-data)")
if b.get("drift") is not None:
    raise SystemExit(f"B: expected drift=null (ambiguous EPERM must not be a false-positive drift) — got {b.get('drift')!r}")
PY
ASSERT_RC=$?
set -e
if [[ "${ASSERT_RC}" -ne 0 ]]; then
  MSG="$(head -5 "${ASSERT_LOG}" | tr '\n' ' ' | sed 's/"/\\"/g')"
  test_fail "${MSG}" "{\"log\":\"${ASSERT_LOG}\"}"
fi

test_pass "drift determined e2e via steered prediction: deny-vs-success→true, allow-vs-ambiguous→null" "{}"
