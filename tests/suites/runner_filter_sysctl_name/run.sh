#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="runner_filter_sysctl_name"
PW_TEST_ID="prediction_unavailable_attempt_observed"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "sysctl-name probe — sandbox_check skipped, attempt observed"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json, sys
from pathlib import Path
spec = {
    "schema_version": 1,
    "specimen_id": "runner_filter_sysctl_name",
    "policy": {
        "format": "sbpl",
        "sbpl_source": (
            "(version 1)\n"
            "(allow default)\n"
            "(deny sysctl-read (sysctl-name \"kern.osrelease\"))\n"
        ),
    },
    "probe_plan": [{
        "step_id": "kern_osrelease",
        "sandbox_check": {
            "operation": "sysctl-read",
            "filter": {"kind": "sysctl_name", "value": "kern.osrelease"},
        },
        # Sysctl attempts aren't a runner attempt kind today; we pair with
        # a benign file access so the attempt slot is populated for
        # envelope shape checks. The runner's actual sysctl exercise
        # lands when the C probe-runner (Step 4) adds the operation.
        "attempt": {"kind": "file", "action": "access", "target": "/etc/hosts"},
    }],
}
Path(sys.argv[1]).write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/run.json"
set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" --sonoma-cross-check >"${RUN_STDOUT}" 2>/dev/null
RC=$?
set -e

if [[ "${RC}" -ne 0 ]]; then
  test_fail "specimen should succeed (rc=${RC})" "{\"stdout\":\"${RUN_STDOUT}\"}"
fi

ASSERT_LOG="${PW_TEST_ARTIFACTS}/assertions.log"
set +e
/usr/bin/python3 - "${RUN_STDOUT}" >"${ASSERT_LOG}" 2>&1 <<'PY'
import json, sys
from pathlib import Path
env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
runner = env.get("data", {}).get("runner_result") or {}
steps = runner.get("steps") or []
if not steps:
    raise SystemExit(f"expected 1 step, got 0 (outcome={runner.get('normalized_outcome')!r})")
sb = steps[0].get("sandbox_check") or {}
outcome = sb.get("outcome")
if outcome != "prediction_unavailable":
    raise SystemExit(
        f"expected step.sandbox_check.outcome=prediction_unavailable for "
        f"sysctl_name (got {outcome!r}). The runner did not recognize the "
        f"filter kind or the short-circuit was bypassed."
    )
if sb.get("rc") != -1:
    raise SystemExit(
        f"expected step.sandbox_check.rc=-1 sentinel for prediction_unavailable "
        f"(got {sb.get('rc')!r}); rc==0 would falsely look like allow"
    )
if sb.get("filter_type_id") is not None:
    raise SystemExit(f"expected filter_type_id null, got {sb.get('filter_type_id')!r}")
if sb.get("errno") is not None:
    raise SystemExit(f"expected errno null, got {sb.get('errno')!r}")

attempt = steps[0].get("attempt") or {}
if attempt.get("rc") is None:
    raise SystemExit(f"expected attempt.rc populated, got {attempt!r}")

cross = env.get("data", {}).get("sonoma_cross_check") or {}
cross_steps = cross.get("steps") or []
if not cross_steps:
    raise SystemExit("expected sonoma_cross_check.steps to be present")
cstep = cross_steps[0]
if cstep.get("status") != "skipped":
    raise SystemExit(f"expected cross-check status=skipped, got {cstep.get('status')!r}")
err = cstep.get("error") or ""
if "prediction_unavailable" not in err:
    raise SystemExit(f"expected cross-check error to identify prediction_unavailable (got {err!r})")
PY
ASSERT_RC=$?
set -e
if [[ "${ASSERT_RC}" -ne 0 ]]; then
  MSG="$(head -5 "${ASSERT_LOG}" | tr '\n' ' ' | sed 's/"/\\"/g')"
  test_fail "${MSG}" "{\"log\":\"${ASSERT_LOG}\"}"
fi

test_pass "sysctl_name: prediction_unavailable surfaced; attempt observed; cross-check mirrored" "{}"
