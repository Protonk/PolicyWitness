#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="runner_sandbox_denied"
PW_TEST_ID="bare_deny_default_v2_denied"

PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "bare (deny default) v2 specimen — expect runner_sandbox_denied"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

# Specimen taken verbatim from the bug report that motivated the host/worker
# split. Without any (allow ...) entries the worker process is sandbox-killed
# (either SIGKILL directly from the kernel or SIGTRAP from libSwift when
# vm_allocate is denied). The unsandboxed host survives, reaps the worker,
# and surfaces this as runner_sandbox_denied with the signal in
# runner_subprocess.term_signal.
SPECIMEN_PATH="${PW_TEST_ARTIFACTS}/specimen.json"
/usr/bin/python3 - "${SPECIMEN_PATH}" <<'PY'
import json
import sys
from pathlib import Path

specimen = {
    "schema_version": 1,
    "specimen_id": "runner_sandbox_denied_v2",
    "policy": {
        "format": "sbpl",
        "sbpl_source": (
            "(version 2)\n"
            "(deny default)\n"
            "(allow iokit-open-service (iokit-registry-entry-class \"IOHIDSystem\"))\n"
        ),
    },
    "probe_plan": [
        {
            "step_id": "p1",
            "sandbox_check": {
                "operation": "iokit-open-service",
                "filter": {"kind": "none", "value": ""},
            },
            "attempt": {
                "kind": "file",
                "action": "access",
                "target": "/tmp/x",
            },
        }
    ],
    # Force the Swift worker. This suite exercises the
    # `runner_sandbox_denied` outcome via a v2 deny-default policy
    # that the Swift worker can't survive (allocation traps in
    # Swift's runtime fire SIGKILL post-apply). The C worker has a
    # tiny post-apply syscall surface and DOES survive the same
    # policy — it's the whole point of the runner reshape. So the
    # specific failure mode this suite pins is Swift-worker
    # specific. A future suite can cover the analogous C-worker
    # runner_sandbox_denied path (worker dies from an explicit
    # sandbox-induced signal) once a deterministic specimen exists.
    "_test_overrides": {"use_c_worker": False},
}
Path(sys.argv[1]).write_text(json.dumps(specimen, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

RUN_STDOUT="${PW_TEST_ARTIFACTS}/policy_witness.run.stdout.json"
RUN_STDERR="${PW_TEST_ARTIFACTS}/policy_witness.run.stderr.txt"

set +e
"${PW_BIN}" run "${SPECIMEN_PATH}" >"${RUN_STDOUT}" 2>"${RUN_STDERR}"
RC=$?
set -e

# The runner reports failure (rc != 0) because the worker did not complete; the
# host's job is to *classify* the failure correctly, not hide it.
if [[ "${RC}" -eq 0 ]]; then
  test_fail "expected non-zero exit when worker is sandbox-denied (rc=${RC})" \
    "{\"stdout\":\"${RUN_STDOUT}\",\"stderr\":\"${RUN_STDERR}\"}"
fi

/usr/bin/python3 - "${RUN_STDOUT}" <<'PY'
import json
import sys
from pathlib import Path

env = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if env.get("kind") != "run":
    raise SystemExit(f"expected kind=run (got {env.get('kind')!r})")

result = env.get("result", {})
runner = env.get("data", {}).get("runner_result") or {}

if result.get("ok") is not False:
    raise SystemExit(f"expected top-level ok=false (got {result.get('ok')!r})")
if runner.get("normalized_outcome") != "runner_sandbox_denied":
    raise SystemExit(
        f"expected normalized_outcome=runner_sandbox_denied "
        f"(got {runner.get('normalized_outcome')!r})"
    )
if runner.get("schema_version", 0) < 3:
    raise SystemExit(f"expected runner schema_version >= 3 (got {runner.get('schema_version')!r})")

sub = runner.get("runner_subprocess") or {}
if not sub:
    raise SystemExit("missing runner_subprocess block")
term = sub.get("term_signal")
if not isinstance(term, int) or term <= 0:
    raise SystemExit(f"expected runner_subprocess.term_signal to be a positive int (got {term!r})")
# Either SIGKILL (kernel-issued) or a libSwift abort signal (SIGTRAP=5, SIGABRT=6)
# is acceptable — the bug-report specimen has been observed to produce both
# depending on host load order. The point is that *some* fatal signal was seen.
if term not in (5, 6, 9):
    # Don't hard-fail here — we may see other libSystem abort surfaces. But
    # warn loudly via the failure path so the test report is informative.
    raise SystemExit(
        f"unexpected term_signal value (got {term!r}); expected 5 (SIGTRAP), "
        f"6 (SIGABRT), or 9 (SIGKILL)"
    )
if runner.get("pid") != sub.get("pid"):
    raise SystemExit(
        f"runner pid should name the worker (runner={runner.get('pid')!r}, "
        f"sub={sub.get('pid')!r})"
    )
PY

test_pass "bare (deny default) v2 surfaced as runner_sandbox_denied" "{}"
