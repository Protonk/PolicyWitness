#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="runner_filter_iokit_registry_entry_class"
PW_TEST_ID="prediction_unavailable_attempt_observed"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "iokit-registry-entry-class probe — sandbox_check skipped, attempt observed"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

# The bug-report's canonical specimen: allow iokit-open-service for one
# class (IOHIDSystem), default-deny otherwise via the rest of the policy.
# We use a default-allow + explicit-deny shape instead so the attempt can
# meaningfully run and observe a kernel verdict, since (deny default)
# would kill the worker before it reaches the probe.
SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json, sys
from pathlib import Path
spec = {
    "schema_version": 1,
    "specimen_id": "runner_filter_iokit_registry_entry_class",
    "policy": {
        "format": "sbpl",
        "sbpl_source": (
            "(version 1)\n"
            "(allow default)\n"
            "(deny iokit-open-service (iokit-registry-entry-class \"IOSurfaceRoot\"))\n"
        ),
    },
    "probe_plan": [{
        "step_id": "iosurface_open",
        "sandbox_check": {
            "operation": "iokit-open-service",
            "filter": {"kind": "iokit_registry_entry_class", "value": "IOSurfaceRoot"},
        },
        # The runner's attempt machinery doesn't have an IOKit attempt
        # kind today, so we pair the sandbox_check with a benign file
        # access attempt — the assertion here is about the prediction
        # path, not about exercising the IOKit operation end-to-end.
        # IOKit attempts will land later when the C probe-runner (Step 4)
        # adds the operation.
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
        f"iokit_registry_entry_class (got {outcome!r}). Either the runner did not "
        f"recognize the filter kind, or the short-circuit was bypassed."
    )

# When prediction is unavailable, filter_type_id should be null (no
# numeric ID was used) and there should be no errno / error to mislead
# consumers.
if sb.get("filter_type_id") is not None:
    raise SystemExit(f"expected filter_type_id null for prediction_unavailable, got {sb.get('filter_type_id')!r}")
if sb.get("errno") is not None:
    raise SystemExit(f"expected errno null for prediction_unavailable, got {sb.get('errno')!r}")

# The attempt must still run — channel A is the reliable evidence.
attempt = steps[0].get("attempt") or {}
if attempt.get("rc") is None:
    raise SystemExit(f"expected attempt.rc populated, got {attempt!r}")

# Cross-check must mirror the prediction_unavailable signal.
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

test_pass "prediction_unavailable surfaced; attempt observed; cross-check mirrored" "{}"
