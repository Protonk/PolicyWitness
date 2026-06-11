#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="runner_apply_isolation_v2"
PW_TEST_ID="deny_default_v2_worker_reply"

PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "run v2 deny-default specimen through host/worker split"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json
import sys
from pathlib import Path

specimen = {
    "schema_version": 1,
    "specimen_id": "runner_apply_isolation_v2",
    "policy": {
        "format": "sbpl",
        # Keep default-deny semantics while allowing low-level runtime syscalls
        # the worker needs to encode and write its report. The old single-process
        # runner still lost the XPC reply path because mach-lookup remains denied.
        "sbpl_source": "(version 2)\n(deny default)\n(allow syscall-unix)\n(allow syscall-mach)\n(allow file-test-existence)\n",
    },
    "probe_plan": [],
}
Path(sys.argv[1]).write_text(json.dumps(specimen, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/policy_witness.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/policy_witness.run.stderr.txt"

set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?
set -e

if [[ "${RC}" -ne 0 ]]; then
  test_fail "policy-witness run failed (rc=${RC})" "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

/usr/bin/python3 - "${RUN_STDOUT}" <<'PY'
import json
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if env.get("kind") != "run":
    raise SystemExit(f"expected kind=run (got {env.get('kind')!r})")
if env.get("result", {}).get("ok") is not True:
    raise SystemExit(f"expected top-level ok=true (got {env.get('result')!r})")

runner = env.get("data", {}).get("runner_result") or {}
if runner.get("schema_version", 0) < 3:
    raise SystemExit(f"expected runner schema_version >= 3 (got {runner.get('schema_version')!r})")
if runner.get("normalized_outcome") != "ok":
    raise SystemExit(f"expected runner normalized_outcome=ok (got {runner.get('normalized_outcome')!r})")
# The point of this suite is the apply/isolation, so witness it: the worker
# must report it actually self-applied the (deny default) policy, not merely
# reply cleanly. Without this, a no-op / short-circuited sandbox_apply would
# pass green.
if runner.get("sandboxed_after_apply") is not True:
    raise SystemExit(
        "expected sandboxed_after_apply=true — worker must witness it applied the "
        f"policy, not just reply (got {runner.get('sandboxed_after_apply')!r})"
    )
sub = runner.get("runner_subprocess") or {}
if not sub:
    raise SystemExit("missing runner_subprocess")
if runner.get("pid") != sub.get("pid"):
    raise SystemExit(f"runner pid should name worker pid (runner={runner.get('pid')!r}, sub={sub.get('pid')!r})")
if sub.get("exit_code") != 0 or sub.get("term_signal") is not None:
    raise SystemExit(f"expected clean worker exit (got {sub!r})")
if sub.get("partial_steps") is not False:
    raise SystemExit(f"expected partial_steps=false (got {sub.get('partial_steps')!r})")
if runner.get("steps") != []:
    raise SystemExit(f"expected empty steps (got {runner.get('steps')!r})")
PY

test_pass "v2 deny-default worker replied through unsandboxed host" "{}"
