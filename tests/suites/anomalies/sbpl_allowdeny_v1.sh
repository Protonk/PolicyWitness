#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

export PW_TEST_QUIET=1

PW_TEST_SUITE="anomalies"
PW_TEST_ID="sbpl_allowdeny_v1"

PW_BIN="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"
SBPL_FIXTURE="${ROOT_DIR}/tests/fixtures/runner_smoke/v1/profile.sbpl"
SPECIMEN_TEMPLATE="${ROOT_DIR}/tests/fixtures/runner_smoke/v1/specimen.template.json"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "anomaly_probe" "probe alleged sandbox anomaly (SBPL allow vs sandbox_check deny)"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi
if [[ ! -f "${SBPL_FIXTURE}" ]]; then
  test_fail "fixture missing: ${SBPL_FIXTURE}"
fi
if [[ ! -f "${SPECIMEN_TEMPLATE}" ]]; then
  test_fail "fixture missing: ${SPECIMEN_TEMPLATE}"
fi

# Note: sandboxed automation harnesses can block XPC lookup or unified log access.
# If this test fails with those symptoms, rerun from a normal Terminal.

WORK_ROOT="${PW_TEST_ARTIFACTS}/workspace"
ALLOW_DIR="${WORK_ROOT}/allow-write"
DENY_DIR="${WORK_ROOT}/deny-write"
ALLOW_FILE="${ALLOW_DIR}/existing.txt"
DENY_FILE="${DENY_DIR}/existing.txt"

mkdir -p "${ALLOW_DIR}" "${DENY_DIR}"
printf 'seed\n' >"${ALLOW_FILE}"
printf 'seed\n' >"${DENY_FILE}"

SPECIMEN_JSON="${PW_TEST_ARTIFACTS}/specimen.rendered.json"

/usr/bin/python3 - "${SBPL_FIXTURE}" "${SPECIMEN_TEMPLATE}" "${SPECIMEN_JSON}" "${ALLOW_FILE}" "${DENY_FILE}" "${DENY_DIR}" <<'PY'
import json
import os
import sys
from pathlib import Path

sbpl_path, template_path, out_path, allow_file, deny_file, deny_dir = sys.argv[1:7]

sbpl = Path(sbpl_path).read_text(encoding="utf-8")
template = json.loads(Path(template_path).read_text(encoding="utf-8"))

def rp(p: str) -> str:
    return os.path.realpath(p)

deny_dir_rp = rp(deny_dir)
allow_file_rp = rp(allow_file)
deny_file_rp = rp(deny_file)
allow_dir_rp = rp(str(Path(allow_file_rp).parent))

template["policy"]["sbpl_source"] = sbpl
template["policy"]["params"]["ALLOW_WRITE_DIR"] = allow_dir_rp
template["policy"]["params"]["DENY_WRITE_DIR"] = deny_dir_rp

for step in template.get("probe_plan", []):
    attempt = step.get("attempt") or {}
    sandbox_check = step.get("sandbox_check") or {}
    filt = (sandbox_check.get("filter") or {})

    if attempt.get("kind") == "file":
        if attempt.get("target") == "__ALLOW_WRITE_FILE__":
            attempt["target"] = allow_file_rp
            filt["value"] = allow_file_rp
        elif attempt.get("target") == "__DENY_WRITE_FILE__":
            attempt["target"] = deny_file_rp
            filt["value"] = deny_file_rp

Path(out_path).write_text(json.dumps(template, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/policy_witness.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/policy_witness.run.stderr.txt"

set +e
"${PW_BIN}" run "${SPECIMEN_JSON}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?
set -e

if [[ "${RC}" -ne 0 ]]; then
  test_fail "policy-witness run failed (rc=${RC})" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

set +e
PY_ERR="$(
  /usr/bin/python3 - "${RUN_STDOUT}" 2>&1 <<'PY'
import json
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if env.get("kind") != "run":
    raise SystemExit(f"expected kind=run (got {env.get('kind')!r})")
if env.get("result", {}).get("ok") is not True:
    raise SystemExit(f"expected result.ok=true (got {env.get('result', {}).get('ok')!r})")

obj = env.get("data", {}).get("runner_result") or {}

if obj.get("normalized_outcome") != "ok":
    raise SystemExit(f"expected normalized_outcome=ok (got {obj.get('normalized_outcome')!r})")
if obj.get("policy_format") != "sbpl":
    raise SystemExit(f"expected policy_format=sbpl (got {obj.get('policy_format')!r})")
if obj.get("sandboxed_after_apply") is not True:
    raise SystemExit(f"expected sandboxed_after_apply=true (got {obj.get('sandboxed_after_apply')!r})")

steps = obj.get("steps") or []
if len(steps) != 4:
    raise SystemExit(f"expected 4 steps (got {len(steps)})")

by_id = {s.get("step_id"): s for s in steps}

def require_step(step_id: str):
    if step_id not in by_id:
        raise SystemExit(f"missing step_id {step_id!r}; have {sorted(by_id.keys())}")
    return by_id[step_id]

def sb_outcome(s):
    return (s.get("sandbox_check") or {}).get("outcome")

def attempt_rc(s):
    return (s.get("attempt") or {}).get("rc")

def sig_delta(s):
    return ((s.get("deny_signal") or {}).get("delta") or 0)

allowed_file = require_step("fs_write_allowed")
if sb_outcome(allowed_file) != "deny":
    raise SystemExit(f"Anomaly not reproduced: fs_write_allowed expected sandbox_check=deny (got {sb_outcome(allowed_file)!r})")
if attempt_rc(allowed_file) != 0:
    raise SystemExit(f"Anomaly not reproduced: fs_write_allowed expected attempt rc=0 (got {attempt_rc(allowed_file)!r})")
if sig_delta(allowed_file) != 0:
    raise SystemExit(f"Anomaly not reproduced: fs_write_allowed expected deny_signal delta=0 (got {sig_delta(allowed_file)!r})")

denied_file = require_step("fs_write_denied")
if sb_outcome(denied_file) != "deny":
    raise SystemExit(f"fs_write_denied: expected sandbox_check deny (got {sb_outcome(denied_file)!r})")
if attempt_rc(denied_file) == 0:
    raise SystemExit("fs_write_denied: expected attempt failure (rc != 0)")

_ = require_step("mach_lookup_allowed")
_ = require_step("mach_lookup_denied")
PY
)"
PY_STATUS=$?
set -e

if [[ ${PY_STATUS} -ne 0 ]]; then
  if [[ -z "${PY_ERR}" ]]; then
    PY_ERR="anomaly validation failed"
  fi
  PY_ERR="${PY_ERR//$'\n'/ }"
  test_fail "${PY_ERR}" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

test_pass_note "Anomaly: sandbox_check denied a path explicitly allowed by the SBPL profile -- fs_write_allowed expected sandbox_check=allow but got deny" "{}"
