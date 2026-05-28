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
# Case 2: unknown_filter_kind
# ----------------------------------------------------------------------
# Fully Swift-decodable spec with one probe step whose sandbox_check.filter.kind
# is "not-a-real-kind". This passes JSON decode then trips
# validateSandboxChecks at the host (`unsupported filter.kind ...`).
#
# Note: the plan called this case "unknown_sandbox_operation", but the
# operation field is only checked for emptiness — any non-empty string
# passes. The supported-set check is on filter.kind, so that's the
# field this case exercises.

PW_TEST_ID="unknown_filter_kind"
test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "probe step with unsupported filter.kind — expect bad_request"

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen_filter.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json
import sys
from pathlib import Path

spec = {
    "schema_version": 1,
    "specimen_id": "bad_filter_kind_probe",
    "policy": {
        "format": "sbpl",
        "sbpl_source": "(version 1) (allow default)",
    },
    "probe_plan": [
        {
            "step_id": "p1",
            "sandbox_check": {
                "operation": "file-read-data",
                "filter": {"kind": "not-a-real-kind", "value": ""},
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
  test_fail "expected non-zero exit when filter.kind is unsupported (rc=${RC})" \
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
        f"validateSandboxChecks may have been changed to accept this filter.kind."
    )

error_msg = runner.get("error") or ""
if "not-a-real-kind" not in error_msg and "filter.kind" not in error_msg:
    raise SystemExit(
        f"expected error to identify the unknown filter.kind; got error={error_msg!r}"
    )

if runner.get("runner_subprocess") is not None:
    raise SystemExit(
        f"expected runner_subprocess=null on validation failure; got {runner.get('runner_subprocess')!r}"
    )
if runner.get("steps"):
    raise SystemExit(f"expected empty steps (got {runner.get('steps')!r})")
PY

test_pass "unsupported filter.kind surfaced as bad_request" "{}"
