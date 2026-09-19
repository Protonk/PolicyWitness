#!/usr/bin/env python3
"""Exercise the checker CLI with independently specified evidence and faults."""
import copy
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "tests/fixtures/blackbox_e2e"
CHECKER = Path(__file__).with_name("validate_run.py")


def main():
    artifacts = Path(sys.argv[1])
    artifacts.mkdir(parents=True, exist_ok=True)
    baseline = json.loads((FIXTURES / "checker/valid_run.json").read_text())
    prediction_error = "fs_write_allowed: expected sandbox_check allow"
    later_attempt_error = "mach_lookup_denied: expected attempt_ok=False"
    failures = []

    def check(name, envelope, diagnostics=(), case="BBX-001"):
        run_path = artifacts / f"{name}.json"
        run_path.write_text(json.dumps(envelope, indent=2) + "\n")
        result = subprocess.run(
            [sys.executable, str(CHECKER), str(run_path),
             str(FIXTURES / case / "expected.json")],
            capture_output=True, text=True, timeout=5,
        )
        output = result.stdout + result.stderr
        (artifacts / f"{name}.log").write_text(f"rc={result.returncode}\n{output}")
        expected_rc = 1 if diagnostics else 0
        if result.returncode != expected_rc or any(note not in output for note in diagnostics):
            failures.append(f"{name}: expected rc={expected_rc}, diagnostics={diagnostics!r}; "
                            f"got rc={result.returncode}, output={output!r}")
        else:
            print(f"{name}: ok", flush=True)

    check("valid", baseline)

    current = copy.deepcopy(baseline)
    current["data"]["runner_result"]["schema_version"] = 7
    for i, step in enumerate(current["data"]["runner_result"]["steps"]):
        step["attempt"].update(requested_kind="mach_lookup" if i == 2 else "file",
                               requested_action="bootstrap_look_up" if i == 2 else "open_write")
        step["drift"] = False if i == 0 else None
        step["comparison"] = dict(scope="submitted_operation_and_target",
            prediction="allow" if i == 0 else "deny",
            observation="succeeded" if i == 0 else "permission_failure",
            observation_basis="completed_worker_status" if i == 0 else "permission_errno",
            operation_relation="matched", target_relation="same_submitted",
            conclusion="agreement" if i == 0 else "directional_consistency",
            limitations=["query_attempt_order_unestablished", "state_stability_unestablished"])
        paths = step["sandbox_check"].get("path_diagnostics")
        if paths is not None:
            paths.update(observer="runner_host", phase="after_orchestration")
    check("response7", current)
    missing = copy.deepcopy(current)
    del missing["data"]["runner_result"]["steps"][0]["comparison"]
    check("response7_missing_comparison", missing, ("fs_write_allowed: missing comparison",))
    broken_current = copy.deepcopy(current)
    first, _, last = broken_current["data"]["runner_result"]["steps"]
    first["sandbox_check"] = None
    last["attempt"] = None
    check("response7_malformed_independent_channels", broken_current,
          ("missing sandbox_check for fs_write_allowed", "missing attempt for mach_lookup_denied"))

    broken = copy.deepcopy(baseline)
    attempt = broken["data"]["runner_result"]["steps"][2]["attempt"]
    attempt.update(outcome="ok", rc=0, exit_code=0)
    check("wrong_later_attempt", broken, (later_attempt_error,))

    broken["data"]["runner_result"]["steps"][0]["sandbox_check"]["outcome"] = "deny"
    check("prediction_and_later_attempt", broken, (prediction_error, later_attempt_error))

    mismatch = copy.deepcopy(baseline)
    mismatch["data"]["runner_result"]["steps"][0]["sandbox_check"]["outcome"] = "deny"
    check("wrong_prediction", mismatch, (prediction_error,))

    broken = copy.deepcopy(mismatch)
    broken["data"]["runner_result"]["steps"][0]["attempt"].update(rc=-1, exit_code=-1)
    check("prediction_and_same_attempt", broken,
          (prediction_error, "fs_write_allowed: expected attempt_ok=True"))

    # Neither a malformed prediction object nor a missing attempt may prevent
    # the other channel or a sibling step from being checked.
    broken = copy.deepcopy(baseline)
    first, _, last = broken["data"]["runner_result"]["steps"]
    first["sandbox_check"] = None
    first["attempt"].update(rc=-1, exit_code=-1)
    del last["attempt"]
    check("malformed_channels", broken,
          ("missing sandbox_check for fs_write_allowed",
           "fs_write_allowed: expected attempt_ok=True", "missing attempt for mach_lookup_denied"))

    broken = copy.deepcopy(mismatch)
    broken["data"]["runner_result"]["steps"][2]["step_id"] = "fs_write_denied"
    check("prediction_and_duplicate_id", broken, (prediction_error, "expected step IDs in order"))

    broken = copy.deepcopy(baseline)
    broken["data"]["runner_result"]["steps"].reverse()
    check("reordered_steps", broken, ("expected step IDs in order",))

    missing = json.loads((FIXTURES / "checker/missing_path_run.json").read_text())
    check("expected_unavailable", missing, case="BBX-002")

    broken = copy.deepcopy(missing)
    broken["data"]["runner_result"]["steps"][2]["attempt"].update(rc=1, exit_code=1)
    check("unavailable_and_later_attempt", broken,
          ("fs_read_allowed: expected attempt_ok=True",), case="BBX-002")

    broken = copy.deepcopy(missing)
    del broken["data"]["runner_result"]["steps"][0]["drift"]
    check("unavailable_missing_drift", broken,
          ("fs_read_missing: expected unavailable prediction to have explicit drift=null",), case="BBX-002")

    broken = copy.deepcopy(missing)
    broken["data"]["runner_result"]["steps"][0]["sandbox_check"]["rc"] = 0
    check("unavailable_wrong_sentinel", broken,
          ("fs_read_missing: expected unavailable sandbox_check.rc=-1",), case="BBX-002")

    broken = copy.deepcopy(missing)
    broken["data"]["runner_result"]["steps"][0]["sandbox_check"].update(outcome="allow", rc=0, filter_type_id=1)
    check("invented_missing_path_prediction", broken,
          ("fs_read_missing: expected sandbox_check prediction_unavailable",), case="BBX-002")

    broken = copy.deepcopy(baseline)
    broken["data"]["runner_result"]["steps"][0]["sandbox_check"]["filter_type_id"] = None
    check("real_verdict_missing_filter_type", broken,
          ("fs_write_allowed: invalid sandbox_check.filter_type_id=None",))

    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
