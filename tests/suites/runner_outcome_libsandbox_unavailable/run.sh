#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="runner_outcome_libsandbox_unavailable"
PW_TEST_ID="dlopen_failure_propagates_to_outcome"

PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "_test_overrides.libsandbox_path=/nonexistent — expect libsandbox_unavailable"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

# The override is carried through the request JSON, not an env var. launchd
# spawns the XPC service host with a clean environment, so a shell-set var
# never reaches the host; the request JSON does.
#
# Pointing libsandbox_path at a file that does not exist makes the real
# dlopen() return NULL with a real dlerror() string. The host's load
# fails, returns normalized_outcome="libsandbox_unavailable" with the
# override mirrored back under data.runner_result.test_overrides, and
# never spawns a worker. No code is faked.
FAKE_LIB="/nonexistent/policy-witness-libsandbox-not-real.dylib"

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
PW_FAKE_LIB="${FAKE_LIB}" /usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json
import os
import sys
from pathlib import Path

specimen = {
    "schema_version": 1,
    "specimen_id": "libsandbox_unavailable_probe",
    "policy": {
        "format": "sbpl",
        # The policy itself is irrelevant — the host bails before sandbox
        # compile when libsandbox cannot be loaded. (allow default) keeps
        # this specimen as the trivial happy path when the override is
        # absent, which is how the suite's negative control works.
        "sbpl_source": "(version 1) (allow default)",
    },
    "probe_plan": [],
    "_test_overrides": {
        "libsandbox_path": os.environ["PW_FAKE_LIB"],
    },
}
Path(sys.argv[1]).write_text(json.dumps(specimen, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/policy_witness.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/policy_witness.run.stderr.txt"

set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?
set -e

# A failed run is the expected outcome here, so a zero exit code is the bug.
if [[ "${RC}" -eq 0 ]]; then
  test_fail "expected non-zero exit when libsandbox cannot be loaded (rc=${RC})" \
    "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

PW_FAKE_LIB="${FAKE_LIB}" /usr/bin/python3 - "${RUN_STDOUT}" <<'PY'
import json
import os
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
fake_lib = os.environ["PW_FAKE_LIB"]

if env.get("kind") != "run":
    raise SystemExit(f"expected kind=run (got {env.get('kind')!r})")
result = env.get("result", {})
if result.get("ok") is not False:
    raise SystemExit(f"expected top-level ok=false (got {result.get('ok')!r})")

runner = env.get("data", {}).get("runner_result") or {}
outcome = runner.get("normalized_outcome")
if outcome != "libsandbox_unavailable":
    raise SystemExit(
        f"expected normalized_outcome=libsandbox_unavailable (got {outcome!r}); "
        f"the override did not reach SandboxLib.load(path:) or the classifier "
        f"shape changed."
    )

# The failure message should name the override path so a reader can tell
# the real loader was exercised (not a stub returning a constant).
error_msg = runner.get("error") or ""
if fake_lib not in error_msg:
    raise SystemExit(
        f"expected error to mention the override path {fake_lib!r}; "
        f"got error={error_msg!r}. Either the path wasn't propagated to "
        f"dlopen or the LoadError message no longer includes it."
    )

# Auditability: the response must reflect the override that was honored.
test_overrides = runner.get("test_overrides")
if not test_overrides:
    raise SystemExit(
        "expected runner_result.test_overrides to be populated when an "
        "override was supplied; got null. Production runs (no override) leave "
        "this field unset, so its presence is the audit signal."
    )
if test_overrides.get("libsandbox_path") != fake_lib:
    raise SystemExit(
        f"expected test_overrides.libsandbox_path={fake_lib!r}, "
        f"got {test_overrides.get('libsandbox_path')!r}"
    )

# The host short-circuits before spawning the worker when libsandbox cannot
# be loaded, so there should be no runner_subprocess block and no steps.
if runner.get("runner_subprocess") is not None:
    raise SystemExit(
        "expected runner_subprocess=null when host fails libsandbox load "
        f"(host should short-circuit before posix_spawn); got {runner.get('runner_subprocess')!r}"
    )
if runner.get("steps"):
    raise SystemExit(f"expected empty steps (got {runner.get('steps')!r})")
PY

test_pass "libsandbox unavailable propagated end-to-end with override reflected" "{}"
