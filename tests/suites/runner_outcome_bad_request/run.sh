#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="runner_outcome_bad_request"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

# ----------------------------------------------------------------------
# Case 1: swift_decode_failure
# ----------------------------------------------------------------------
# Well-formed JSON that the Rust controller passes through unchanged
# (policy fields are present so policy_preflight succeeds) but
# PWRunnerRunSpec cannot decode (missing required schema_version and
# specimen_id). Hits the JSON decode branch of PWRunnerService.runSpecimen.
#
# Do not use "not json at all" here: the Rust controller rejects
# malformed JSON before invoking the runner, so that input would never
# reach the Swift decode path we want to cover.

PW_TEST_ID="swift_decode_failure"
test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "request JSON missing schema_version / specimen_id — expect bad_request"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen_decode.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json
import sys
from pathlib import Path

# Has policy.format + sbpl_source so the Rust preflight passes.
# Missing the required schema_version and specimen_id fields so the
# Swift PWRunnerRunSpec decoder rejects it.
spec = {
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
# validateSandboxChecks at the host ("filter.value required for kind path").
#
# This used to be an `unknown_filter_kind` case (filter.kind set to
# something not in knownFilterKinds). After the unknown-kind path was
# downgraded to per-step prediction_unavailable rather than a
# plan-killer, "unknown kind" no longer reaches bad_request. The
# value-required branch is the remaining filter-side bad_request
# trigger and exercises the same emit site
# (PWRunnerService.runSpecimen catching SpecValidationError from
# validateSandboxChecks in runner/Sources/PWRunnerCore/ProbeRunner.swift).

PW_TEST_ID="missing_required_filter_value"
test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "probe step with kind=path but empty value — expect bad_request"

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen_filter.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json
import sys
from pathlib import Path

spec = {
    "schema_version": 1,
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
