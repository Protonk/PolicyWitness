#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

export PW_TEST_QUIET=1

PW_TEST_SUITE="anomalies"
PW_TEST_ID="sonoma_cross_check"

PW_BIN="${PW_BIN:-${ROOT_DIR}/PolicyWitness.app/Contents/MacOS/policy-witness}"
SBPL_FIXTURE="${ROOT_DIR}/tests/fixtures/runner_smoke/v1/profile.sbpl"
SPECIMEN_TEMPLATE="${ROOT_DIR}/tests/fixtures/runner_smoke/v1/specimen.template.json"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "sonoma_cross_check_consistency" "verify sb_api_validator cross-check matches sandbox_check"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi
if [[ ! -f "${SBPL_FIXTURE}" ]]; then
  test_fail "fixture missing: ${SBPL_FIXTURE}"
fi
if [[ ! -f "${SPECIMEN_TEMPLATE}" ]]; then
  test_fail "fixture missing: ${SPECIMEN_TEMPLATE}"
fi

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
"${PW_BIN}" run "${SPECIMEN_JSON}" --sonoma-cross-check >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
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

cc = (env.get("data", {}) or {}).get("sonoma_cross_check")
if not isinstance(cc, dict):
    raise SystemExit("missing data.sonoma_cross_check")

status = cc.get("status")
if status in ("unavailable", "blocked", "skipped"):
    msg = cc.get("error") or f"sonoma_cross_check status={status}"
    print(msg)
    raise SystemExit(3)

if status != "ok":
    raise SystemExit(f"expected sonoma_cross_check.status=ok (got {status!r})")

counts = cc.get("counts") or {}
if counts.get("mismatches", 0) != 0:
    raise SystemExit(f"expected mismatches=0 (got {counts.get('mismatches')!r})")
if counts.get("errors", 0) != 0:
    raise SystemExit(f"expected errors=0 (got {counts.get('errors')!r})")
if counts.get("skipped", 0) != 0:
    raise SystemExit(f"expected skipped=0 (got {counts.get('skipped')!r})")

steps = cc.get("steps") or []
if len(steps) != 4:
    raise SystemExit(f"expected 4 cross-check steps (got {len(steps)})")

for step in steps:
    sid = step.get("step_id")
    if step.get("status") != "ok":
        raise SystemExit(f"{sid}: expected status=ok (got {step.get('status')!r})")
    if step.get("mismatch") is True:
        raise SystemExit(f"{sid}: mismatch=true")
    expected = step.get("expected_outcome")
    actual = step.get("validator_outcome")
    if expected != actual:
        raise SystemExit(f"{sid}: expected {expected!r} == {actual!r}")
PY
)"
PY_STATUS=$?
set -e

if [[ ${PY_STATUS} -eq 3 ]]; then
  PY_ERR="${PY_ERR//$'\n'/ }"
  test_skip "sonoma cross-check unavailable: ${PY_ERR}" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

if [[ ${PY_STATUS} -ne 0 ]]; then
  if [[ -z "${PY_ERR}" ]]; then
    PY_ERR="sonoma cross-check validation failed"
  fi
  PY_ERR="${PY_ERR//$'\n'/ }"
  test_fail "${PY_ERR}" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

test_pass_note "sonoma cross-check ok" "{}"
