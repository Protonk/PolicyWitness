#!/usr/bin/env python3
"""Drive both checker CLIs with independent evidence and deliberate faults.

These expectations are authored here, never obtained from the checker or the
observed result. Keep the mutations and required diagnostics outside tests/lib.
"""
import copy
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BASELINE = ROOT / "tests/fixtures/blackbox_e2e/checker/missing_path_run.json"


def main():
    artifacts = Path(sys.argv[1])
    artifacts.mkdir(parents=True, exist_ok=True)
    baseline = json.loads(BASELINE.read_text())
    baseline["data"]["runner_result"]["policy_sha256"] = "a" * 64
    expectations = {
        "blackbox_e2e": {
            "policy_format": "sbpl", "require_sandboxed_after_apply": True,
            "steps": [
                {"step_id": "fs_read_missing", "sandbox_outcome": "prediction_unavailable",
                 "attempt_ok": False, "errno": 2, "drift": None},
                {"step_id": "mach_lookup_invalid", "sandbox_outcome": "allow",
                 "attempt_ok": False, "drift": None},
                {"step_id": "fs_read_allowed", "sandbox_outcome": "allow",
                 "attempt_ok": True, "drift": False},
            ],
        },
        "blackbox_menagerie": {"steps": [
            {"step_id": "fs_read_missing",
             "expect": {"predict": "prediction_unavailable", "attempt_ok": False,
                        "errno": 2, "drift": None}},
            {"step_id": "mach_lookup_invalid",
             "expect": {"predict": "allow", "attempt_ok": False, "drift": None}},
            {"step_id": "fs_read_allowed",
             "expect": {"predict": "allow", "attempt_ok": True, "drift": False}},
        ]},
    }
    failures = []
    count = 0

    def check(name, envelope, diagnostics=(), *, expected=None, suites=None, status=0):
        nonlocal count
        for suite in suites or expectations:
            count += 1
            stem = artifacts / f"{suite}.{name}"
            run_path = Path(f"{stem}.run.json")
            expected_path = Path(f"{stem}.expected.json")
            run_path.write_text(json.dumps(envelope, indent=2) + "\n")
            expected_path.write_text(json.dumps((expected or expectations)[suite], indent=2) + "\n")
            checker = ROOT / "tests/suites" / suite / "validate_run.py"
            result = subprocess.run(
                [sys.executable, str(checker), str(run_path), str(expected_path)],
                capture_output=True, text=True, timeout=5,
            )
            output = result.stdout + result.stderr
            Path(f"{stem}.log").write_text(f"rc={result.returncode}\n{output}")
            if result.returncode != status or any(note not in output for note in diagnostics):
                failures.append(f"{suite}/{name}: expected rc={status}, diagnostics={diagnostics!r}; "
                                f"got rc={result.returncode}, output={output!r}")
            else:
                print(f"{suite}/{name}: ok", flush=True)

    def mutate():
        envelope = copy.deepcopy(baseline)
        return envelope, envelope["data"]["runner_result"]["steps"]

    check("valid_nullable_evidence", baseline)
    for channel, key, diagnostic in (
        ("sandbox_check", "errno", "missing sandbox_check.errno"),
        ("sandbox_check", "filter_type_id", "missing sandbox_check.filter_type_id"),
        ("attempt", "observed_path", "missing attempt.observed_path"),
    ):
        broken, steps = mutate()
        del steps[0][channel][key]
        check(f"missing_{channel}_{key}", broken, (diagnostic,), status=1)

    broken, steps = mutate()
    del steps[1]["drift"]  # A real allow verdict, not the unavailable sentinel.
    check("missing_expected_null_drift", broken, ("mach_lookup_invalid: missing drift",), status=1)

    broken, steps = mutate()
    steps[0]["sandbox_check"]["rc"] = 0
    check("unavailable_wrong_sentinel", broken, ("expected unavailable sandbox_check.rc=-1",), status=1)
    broken, steps = mutate()
    del steps[0]["drift"]
    check("unavailable_missing_drift", broken,
          ("expected unavailable prediction to have explicit drift=null",), status=1)

    for channel, key in (("sandbox_check", "pid"), ("sandbox_check", "filter_type_id"),
                         ("sandbox_check", "errno"), ("attempt", "exit_code"),
                         ("attempt", "syscall_errno"), ("attempt", "rc")):
        broken, steps = mutate()
        steps[2][channel][key] = False
        check(f"boolean_{channel}_{key}", broken, (f"invalid {channel}.{key}",), status=1)

    broken, steps = mutate()
    steps[2]["drift"] = 0
    check("integer_drift", broken, ("invalid drift",), status=1)

    for name in ("duplicate", "reordered", "missing", "unknown", "non_object"):
        broken, steps = mutate()
        if name == "duplicate":
            steps[2]["step_id"] = steps[1]["step_id"]
        elif name == "reordered":
            steps.reverse()
        elif name == "missing":
            steps.pop()
        elif name == "unknown":
            steps[1]["step_id"] = "unrequested_step"
        else:
            steps[1] = None
        check(f"{name}_step", broken, ("expected step IDs in order",), status=1)

    broken, steps = mutate()
    steps[0]["sandbox_check"]["outcome"] = "deny"
    steps[2]["attempt"].update(rc=1, exit_code=1)
    check("prediction_and_later_attempt", broken,
          ("fs_read_missing: expected sandbox_check prediction_unavailable",
           "fs_read_allowed: expected attempt_ok=True"), status=1)

    broken, steps = mutate()
    steps[0]["sandbox_check"] = None
    steps[0]["attempt"].update(rc=0, exit_code=0)
    del steps[2]["attempt"]
    check("independent_malformed_channels", broken,
          ("missing sandbox_check for fs_read_missing", "fs_read_missing: expected attempt_ok=False",
           "missing attempt for fs_read_allowed"), status=1)

    for key in ("result", "data"):
        broken, _ = mutate()
        broken[key] = []
        check(f"malformed_{key}", broken, (f"{key} is not an object",), status=1)

    # The shared checks accept the documented nullable filter type on explicit
    # error/sentinel results. Neither suite may silently skip their attempts.
    for outcome, errno in (("deny", None), ("error", 5), ("unsupported_operation", 22)):
        changed, steps = mutate()
        steps[1]["sandbox_check"].update(outcome=outcome, rc=1 if outcome == "deny" else -1,
                                         filter_type_id=2 if outcome == "deny" else None, errno=errno,
                                         error=None if outcome == "deny" else "validator control failure")
        expected = copy.deepcopy(expectations)
        expected["blackbox_e2e"]["steps"][1]["sandbox_outcome"] = outcome
        expected["blackbox_menagerie"]["steps"][1]["expect"]["predict"] = outcome
        check(f"explicit_{outcome}", changed, expected=expected)

    # Envelope requirements remain choices made by each suite.
    changed, _ = mutate()
    del changed["data"]["runner_result"]["policy_sha256"]
    check("optional_hash", changed, suites=("blackbox_e2e",))
    check("required_hash", changed, ("expected policy_sha256 to be present",),
          suites=("blackbox_menagerie",), status=1)

    # A pending host-dependent mismatch skip must wait for every assertion.
    # The first step intentionally has no attempt_ok expectation here.
    expected = copy.deepcopy(expectations)
    first = expected["blackbox_menagerie"]["steps"][0]["expect"]
    del first["attempt_ok"]
    first.update(policy="deny", mismatch_reason="control_boundary")
    check("unobserved_mismatch", baseline, ("expected mismatch (control_boundary) not observed",),
          expected=expected, suites=("blackbox_menagerie",), status=3)
    broken, steps = mutate()
    steps[2]["attempt"].update(rc=1, exit_code=1)
    check("pending_skip_and_later_failure", broken, ("fs_read_allowed: expected attempt_ok=True",),
          expected=expected, suites=("blackbox_menagerie",), status=1)
    first["policy"] = "allow"
    check("observed_mismatch", baseline, ("mismatch evidence: fs_read_missing:control_boundary",),
          expected=expected, suites=("blackbox_menagerie",))
    del first["mismatch_reason"]
    check("unannotated_mismatch", baseline, ("fs_read_missing: policy=allow but attempt_ok=False",),
          expected=expected, suites=("blackbox_menagerie",), status=1)

    expected = copy.deepcopy(expectations)
    expected["blackbox_menagerie"]["steps"][2]["attempt"] = {
        "kind": "file", "action": "open_read", "target": "/private/tmp/pw-bbx-checker/allow.txt"}
    check("file_observation", baseline, expected=expected, suites=("blackbox_menagerie",))
    broken, steps = mutate()
    steps[2]["attempt"]["observed_path"] = None
    check("missing_file_observation", broken, ("expected observed_path for successful open/create",),
          expected=expected, suites=("blackbox_menagerie",), status=1)
    broken, steps = mutate()
    steps[2]["attempt"]["requested_path"] = "/wrong/target"
    check("wrong_file_target", broken, ("expected requested_path",),
          expected=expected, suites=("blackbox_menagerie",), status=1)

    expected = copy.deepcopy(expectations)
    expected["blackbox_e2e"]["steps"][1].update(deny_signal_delta=0, expect_denial=False)
    check("signal_and_denial", baseline, expected=expected, suites=("blackbox_e2e",))
    broken, steps = mutate()
    steps[1]["deny_signal"]["delta"] = 1
    check("wrong_signal_delta", broken, ("expected deny_signal delta=0",),
          expected=expected, suites=("blackbox_e2e",), status=1)
    broken, steps = mutate()
    steps[1]["sandbox_check"].update(outcome="deny", rc=1)
    expected["blackbox_e2e"]["steps"][1]["sandbox_outcome"] = "deny"
    check("wrong_denial_classification", broken, ("expected denial=False",),
          expected=expected, suites=("blackbox_e2e",), status=1)

    if failures:
        raise SystemExit("\n".join(failures))
    print(f"{count} checker controls passed")


if __name__ == "__main__":
    main()
