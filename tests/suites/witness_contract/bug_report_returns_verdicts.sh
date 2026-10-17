#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PW_APP_DIR="${PW_APP_DIR:-${ROOT_DIR}/dist/PolicyWitness.app}"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="witness_contract"
PW_TEST_ID="bug_report_returns_verdicts"
PW_BIN="${PW_BIN:-${PW_APP_DIR}/Contents/MacOS/policy-witness}"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "run" "bug-report specimen: verdict, applied release chain, published attempt and confirmed cleanup"

if ! require_pw_app "${PW_BIN}"; then
  exit 0
fi

# The bug-report specimen, and its allow-default neighbour as the positive
# open/path control. The policy text is the only difference.
for name in specimen neighbour; do
  /usr/bin/python3 - "${PW_TEST_ARTIFACTS}/${name}.json" "${name}" <<'PY'
import json, sys
from pathlib import Path
policy = {"specimen": "(version 2)\n(deny default)\n(allow file-read-data)",
          "neighbour": "(version 2)\n(allow default)"}[sys.argv[2]]
spec = {
    "schema_version": 5,
    "specimen_id": "witness_contract_verdicts" if sys.argv[2] == "specimen" else "witness_contract_verdicts_allow_default",
    "policy": {"format": "sbpl", "sbpl_source": policy},
    "probe_plan": [{
        "step_id": "fr1",
        "sandbox_check": {"operation": "file-read-data", "filter": {"kind": "none"}},
        "attempt": {"kind": "file", "action": "open_read", "target": "/etc/hosts"},
    }],
}
Path(sys.argv[1]).write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
  set +e
  "${PW_BIN}" run "${PW_TEST_ARTIFACTS}/${name}.json" >"${PW_TEST_ARTIFACTS}/${name}-run.json" 2>/dev/null
  set -e
done

ASSERT_LOG="${PW_TEST_ARTIFACTS}/assertions.log"
set +e
/usr/bin/python3 - "${PW_TEST_ARTIFACTS}/specimen-run.json" "${PW_TEST_ARTIFACTS}/neighbour-run.json" >"${ASSERT_LOG}" 2>&1 <<'PY'
import json, sys
from pathlib import Path

def load(path):
    env = json.loads(Path(path).read_text(encoding="utf-8"))
    return env.get("data", {}), env.get("data", {}).get("runner_result") or {}

def worker_account(label, data, runner):
    """Application, release/acknowledgement, publication and cleanup, read from
    the reply's own observations. None of these establishes a policy cause."""
    steps = runner.get("steps") or []
    if not steps:
        raise SystemExit(f"{label}: steps[] is empty (outcome={runner.get('normalized_outcome')!r})")
    sub = runner.get("runner_subprocess") or {}
    assert runner.get("sandboxed_after_apply") is True, f"{label}: no published application"
    failure = (sub.get("worker_evidence") or {}).get("failure")
    assert failure is None, f"{label}: worker failure published: {failure}"
    ordering = (runner.get("phases") or [{}])[0].get("ordering") or {}
    for link in ("collection_closed_before_proceed", "proceed_set", "proceed_observed", "worker_lifetime_established"):
        assert ordering.get(link) is True, f"{label}: release/acknowledgement link {link} missing: {ordering}"
    assert ordering.get("protocol_violations") == [], f"{label}: {ordering}"
    attempt = steps[0].get("attempt") or {}
    assert attempt.get("result_source") == "worker", f"{label}: attempt not published by the worker: {attempt}"
    assert (attempt.get("lifecycle") or {}).get("summary") == "completed", f"{label}: {attempt.get('lifecycle')}"
    assert sub.get("done_observed") is True and sub.get("reaped") is True, f"{label}: {sub}"
    assert sub.get("exit_code") == 0 and sub.get("term_signal") is None, f"{label}: worker cleanup unconfirmed: {sub}"
    assert (data.get("runner_sandbox_diagnostics") or {}).get("process_disposition") == "clean_exit", label
    return steps[0], attempt

data, runner = load(sys.argv[1])
step, attempt = worker_account("specimen", data, runner)
# The prediction: (deny default)(allow file-read-data) answers allow. Pin it:
# accepting deny would let a flipped-verdict regression pass.
outcome = (step.get("sandbox_check") or {}).get("outcome")
assert outcome == "allow", f"expected sandbox_check.outcome=allow for (allow file-read-data), got {outcome!r}"
# The attempt, independently: the open actually ran and returned. A completed
# permission failure is valid timing evidence; success is not required.
rc, err = attempt.get("rc"), attempt.get("errno")
assert isinstance(rc, int), f"attempt.rc is not an int: {rc!r}"
assert (rc == 0 and err is None) or (rc != 0 and isinstance(err, int) and err > 0), f"rc={rc!r} errno={err!r}"
observed = attempt.get("observed_path")
assert observed in (None, "/private/etc/hosts"), f"descriptor-derived path disagrees: {observed!r}"
order = (step.get("comparison") or {}).get("order")
assert order == "query_first", f"established release chain should support query_first, got {order!r}"
print(f"specimen: prediction={outcome}; open rc={rc} errno={err} observed_path={observed!r}; order={order}")

data, runner = load(sys.argv[2])
step, attempt = worker_account("neighbour", data, runner)
assert attempt.get("rc") == 0 and attempt.get("errno") is None, f"allow-default open failed: {attempt}"
assert attempt.get("observed_path") == "/private/etc/hosts", f"allow-default path evidence: {attempt.get('observed_path')!r}"
print("neighbour: allow-default open succeeded with descriptor-derived /private/etc/hosts")
PY
ASSERT_RC=$?
set -e
if [[ "${ASSERT_RC}" -ne 0 ]]; then
  MSG="$(head -5 "${ASSERT_LOG}" | tr '\n' ' ' | sed 's/"/\\"/g')"
  test_fail "${MSG}" "{\"log\":\"${ASSERT_LOG}\"}"
fi

test_pass "$(head -1 "${ASSERT_LOG}")" "{\"log\":\"${ASSERT_LOG}\"}"
