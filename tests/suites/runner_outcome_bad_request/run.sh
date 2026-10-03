#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/case.sh"

PW_TEST_SUITE="runner_outcome_bad_request"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

# ----------------------------------------------------------------------
# Case 1: swift_decode_failure
# ----------------------------------------------------------------------
# Well-formed JSON that the Rust controller passes through unchanged
# (valid JSON object, so it reaches the runner) but PWRunnerRunSpec
# cannot decode (missing required specimen_id).
# Hits the JSON decode branch of PWRunnerService.runSpecimen.
#
# Do not use "not json at all" here: the Rust controller rejects
# malformed JSON before invoking the runner, so that input would never
# reach the Swift decode path we want to cover.

if test_selected swift_decode_failure; then
PW_TEST_ID="swift_decode_failure"
test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "request JSON missing specimen_id — expect bad_request"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen_decode.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json
import sys
from pathlib import Path

# Has policy.format + sbpl_source so it is a plausible request the
# controller forwards untouched. Missing the required specimen_id field so
# the Swift PWRunnerRunSpec decoder rejects it.
spec = {
    "schema_version": 4,
    "policy": {
        "format": "sbpl",
        "sbpl_source": "(version 1) (allow default)",
    },
    "probe_plan": [],
}
Path(sys.argv[1]).write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/decode.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/decode.run.stderr.txt"

set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?
set -e

if [[ "${RC}" -eq 0 ]]; then
  test_fail "expected non-zero exit when request decode fails (rc=${RC})" \
    "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

/usr/bin/python3 - "${RUN_STDOUT}" <<'PY'
import json
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if env.get("kind") != "run":
    raise SystemExit(f"expected kind=run (got {env.get('kind')!r})")
if env.get("result", {}).get("ok") is not False:
    raise SystemExit(f"expected ok=false (got {env.get('result')!r})")

runner = env.get("data", {}).get("runner_result") or {}
outcome = runner.get("normalized_outcome")
if outcome != "bad_request":
    raise SystemExit(
        f"expected normalized_outcome=bad_request (got {outcome!r}); "
        f"the Swift decoder may have been changed to accept the missing fields."
    )

error_msg = runner.get("error") or ""
if "request decode failed" not in error_msg:
    raise SystemExit(
        f"expected error to mention 'request decode failed'; got error={error_msg!r}"
    )

# Host short-circuits before spawning the worker.
if runner.get("runner_subprocess") is not None:
    raise SystemExit(
        f"expected runner_subprocess=null on decode failure; got {runner.get('runner_subprocess')!r}"
    )
if runner.get("steps"):
    raise SystemExit(f"expected empty steps (got {runner.get('steps')!r})")
PY

test_pass "Swift decode failure surfaced as bad_request" "{}"


# ----------------------------------------------------------------------
# Case 2: missing_required_filter_value
# ----------------------------------------------------------------------
# Fully Swift-decodable spec with one probe step whose sandbox_check.filter
# is `kind=path, value=""`. This passes JSON decode, then trips
# request meaning validation at the host ("filter.value required").

fi

if test_selected missing_required_filter_value; then
PW_TEST_ID="missing_required_filter_value"
test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "probe step with kind=path but empty value — expect bad_request"

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen_filter.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json
import sys
from pathlib import Path

spec = {
    "schema_version": 4,
    "specimen_id": "missing_required_filter_value_probe",
    "policy": {
        "format": "sbpl",
        "sbpl_source": "(version 1) (allow default)",
    },
    "probe_plan": [
        {
            "step_id": "p1",
            "sandbox_check": {
                "operation": "file-read-data",
                # kind=path requires a non-empty value; empty/missing
                # value is the trigger validateSandboxChecks asserts on.
                "filter": {"kind": "path", "value": ""},
            },
            "attempt": {"kind": "file", "action": "open_read", "target": "/tmp/x"},
        }
    ],
}
Path(sys.argv[1]).write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/filter.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/filter.run.stderr.txt"

set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?
set -e

if [[ "${RC}" -eq 0 ]]; then
  test_fail "expected non-zero exit when filter.value is missing for a kind that requires one (rc=${RC})" \
    "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

/usr/bin/python3 - "${RUN_STDOUT}" <<'PY'
import json
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if env.get("kind") != "run":
    raise SystemExit(f"expected kind=run (got {env.get('kind')!r})")
if env.get("result", {}).get("ok") is not False:
    raise SystemExit(f"expected ok=false (got {env.get('result')!r})")

runner = env.get("data", {}).get("runner_result") or {}
outcome = runner.get("normalized_outcome")
if outcome != "bad_request":
    raise SystemExit(
        f"expected normalized_outcome=bad_request (got {outcome!r}); "
        f"validateSandboxChecks may have been changed to accept "
        f"kind=path with an empty value."
    )

error_msg = runner.get("error") or ""
if "filter.value required" not in error_msg and "kind path" not in error_msg:
    raise SystemExit(
        f"expected error to identify the missing-value rejection; got error={error_msg!r}"
    )

if runner.get("runner_subprocess") is not None:
    raise SystemExit(
        f"expected runner_subprocess=null on validation failure; got {runner.get('runner_subprocess')!r}"
    )
if runner.get("steps"):
    raise SystemExit(f"expected empty steps (got {runner.get('steps')!r})")
PY

test_pass "missing required filter.value surfaced as bad_request" "{}"
fi

if test_selected accepted_input_contract; then
  test_begin runner_outcome_bad_request accepted_input_contract
  test_require_pw
  test_step contract "exercise current inputs and explicit refusals through CLI and direct XPC"
  test_check_python "${PW_TEST_ARTIFACTS}/assert.log" "accepted input contract failed" \
    "${ROOT_DIR}/tests/suites/runner_outcome_bad_request/contract.py" "${PW_BIN}" "${PW_TEST_ARTIFACTS}"
  test_pass "current requests execute; malformed intent refuses before attempts"
fi
