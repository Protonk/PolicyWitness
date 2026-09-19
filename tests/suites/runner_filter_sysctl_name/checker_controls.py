#!/usr/bin/env python3
"""Exercise the filter checker CLI with hand-authored evidence, without PW.

Keep inputs, expected statuses and diagnostics independent of the checker and
production code. Each caller's arguments are repeated deliberately so a generic
contract passing in another suite cannot substitute for checking these adapters.
"""
import copy
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CHECKER = ROOT / "tests/lib/unavailable_prediction.py"
CALLERS = (
    ("iokit_registry_entry_class", "iosurface_open", "iokit-open-service", "IOSurfaceRoot", "file_open"),
    ("iokit_user_client_class", "iosurfaceroot_uc", "iokit-open-user-client", "IOSurfaceRootUserClient", "file_open"),
    ("sysctl_name", "kern_osrelease", "sysctl-read", "kern.osrelease", "sysctl_denied"),
)


def main():
    artifacts = Path(sys.argv[1])
    artifacts.mkdir(parents=True, exist_ok=True)
    failures = []
    count = 0
    for name, step_id, operation, value, attempt_contract in CALLERS:
        sysctl = name == "sysctl_name"
        baseline = {
            "kind": "run", "result": {"ok": True},
            "data": {"runner_result": {
                "normalized_outcome": "ok", "policy_format": "sbpl",
                "steps": [{
                    "step_id": step_id, "drift": None,
                    "sandbox_check": {
                        "scope": "post_sandbox", "pid": 1234, "operation": operation,
                        "effective_filter_value": value, "filter_type_id": None,
                        "outcome": "prediction_unavailable", "rc": -1, "errno": None, "error": None,
                    },
                    "attempt": {
                        "outcome": "sysctl_failed" if sysctl else "ok",
                        "rc": 1 if sysctl else 0, "exit_code": 1 if sysctl else 0,
                        "errno": 1 if sysctl else None, "syscall_errno": 1 if sysctl else None,
                        "requested_path": "kern.osrelease" if sysctl else "/etc/hosts",
                        "normalized_path": None, "observed_path": None if sysctl else "/private/etc/hosts",
                    },
                }],
            }},
        }

        def check(label, envelope, diagnostics=(), status=1, raw=None, expected_schema_version=None):
            nonlocal count
            count += 1
            stem = artifacts / f"{name}.{label}"
            run_path = Path(f"{stem}.run.json")
            run_path.write_text(raw if raw is not None else json.dumps(envelope, indent=2) + "\n")
            argv = [sys.executable, str(CHECKER), str(run_path), "--step-id", step_id,
                    "--operation", operation, "--filter-value", value, "--attempt", attempt_contract]
            if expected_schema_version is not None:
                argv.extend(["--expected-schema-version", str(expected_schema_version)])
            result = subprocess.run(argv, capture_output=True, text=True, timeout=5)
            output = result.stdout + result.stderr
            Path(f"{stem}.log").write_text(f"argv={argv!r}\nrc={result.returncode}\n{output}")
            if result.returncode != status or any(note not in output for note in diagnostics):
                failures.append(f"{name}/{label}: expected rc={status}, diagnostics={diagnostics!r}; "
                                f"got rc={result.returncode}, output={output!r}")
            else:
                print(f"{name}/{label}: ok", flush=True)

        def mutate():
            envelope = copy.deepcopy(baseline)
            return envelope, envelope["data"]["runner_result"]["steps"][0]

        check("valid_nullable_evidence", baseline, status=0)
        # Current live output must not take the compatibility path used by stored
        # fixtures. These reports are authored here, independent of PW output.
        current, step = mutate()
        current["data"]["runner_result"]["schema_version"] = 7
        step["attempt"].update(requested_kind="sysctl" if sysctl else "file",
                               requested_action="read" if sysctl else "open_read",
                               missing_reason=None)
        step["sandbox_check"]["missing_reason"] = "query_not_requested"
        step["comparison"] = {
            "scope": "submitted_operation_and_target", "prediction": "unavailable",
            "observation": "permission_failure" if sysctl else "succeeded",
            "observation_basis": "permission_errno" if sysctl else "completed_worker_status",
            "operation_relation": "unresolved", "target_relation": "unresolved",
            "conclusion": "unavailable", "limitations": [
                "query_attempt_order_unestablished", "state_stability_unestablished",
                "prediction:query_not_requested", "query_plan:prediction_unavailable_pair",
            ] + (["sandbox_attribution_unestablished"] if sysctl else []),
        }
        check("current_live_evidence", current, status=0, expected_schema_version=7)
        for label, version in (("v4", 4), ("v5", 5), ("v6", 6), ("absent", None)):
            legacy = copy.deepcopy(baseline)
            if version is not None:
                legacy["data"]["runner_result"]["schema_version"] = version
            check("legacy_fixture_" + label, legacy, status=0)
            check("legacy_cannot_replace_live_" + label, legacy,
                  ("expected runner schema_version=7",), expected_schema_version=7)
        for label, version in (("old", 6), ("null", None), ("string", "7"),
                               ("float", 7.0), ("boolean", True), ("future", 8)):
            changed = copy.deepcopy(current)
            changed["data"]["runner_result"]["schema_version"] = version
            check("wrong_live_version_" + label, changed,
                  ("expected runner schema_version=7",), expected_schema_version=7)
        changed = copy.deepcopy(current)
        current_step = changed["data"]["runner_result"]["steps"][0]
        del current_step["comparison"]
        del current_step["attempt"]["requested_kind"]
        del current_step["attempt"]["requested_action"]
        check("missing_current_evidence", changed,
              ("missing comparison", "missing attempt.requested_kind", "missing attempt.requested_action"),
              expected_schema_version=7)
        changed, step = mutate()
        if sysctl:
            step["attempt"].update(errno=13, syscall_errno=13)
            check("eacces_denial", changed, status=0)
        else:
            # Supported file work can report an OS failure. These placeholders
            # check attempt reporting, not IOKit enforcement.
            step["attempt"].update(outcome="open_failed", rc=1, exit_code=1,
                                   errno=2, syscall_errno=2, observed_path=None)
            check("supported_file_failure", changed, status=0)

        for channel, keys in (
            ("sandbox_check", ("scope", "pid", "operation", "effective_filter_value",
                               "filter_type_id", "errno", "error")),
            ("attempt", ("exit_code", "errno", "syscall_errno", "requested_path", "normalized_path", "observed_path", "rc")),
        ):
            for key in keys:
                broken, step = mutate()
                del step[channel][key]
                check(f"missing_{channel}_{key}", broken, (f"missing {channel}.{key}",))

        for sentinel in (0, -1.0, False):
            broken, step = mutate()
            step["sandbox_check"]["rc"] = sentinel
            check(f"wrong_sentinel_{sentinel}", broken, ("expected unavailable sandbox_check.rc=-1",))
        for key in ("filter_type_id", "errno"):
            broken, step = mutate()
            step["sandbox_check"][key] = 0
            check(f"unavailable_nonnull_{key}", broken, (f"expected unavailable sandbox_check.{key}=null",))
        for drift in ("missing", False, True):
            broken, step = mutate()
            if drift == "missing":
                del step["drift"]
            else:
                step["drift"] = drift
            check(f"unavailable_drift_{drift}", broken, ("explicit drift=null",))

        for label in ("wrong", "duplicate", "missing"):
            broken, step = mutate()
            steps = broken["data"]["runner_result"]["steps"]
            if label == "wrong":
                step["step_id"] = "unrequested_step"
            elif label == "duplicate":
                steps.append(copy.deepcopy(step))
            else:
                steps.clear()
            check(f"{label}_step", broken, ("expected step IDs in order",))

        broken, step = mutate()
        step["sandbox_check"]["operation"] = "unrequested-operation"
        check("wrong_operation", broken, ("expected sandbox_check.operation=",))
        broken, step = mutate()
        step["sandbox_check"]["effective_filter_value"] = "unrequested-filter-value"
        check("wrong_filter_value", broken, ("expected sandbox_check.effective_filter_value=",))
        broken, step = mutate()
        step["sandbox_check"].update(outcome="allow", rc=0, filter_type_id=1)
        check("wrong_prediction", broken, ("expected sandbox_check prediction_unavailable",))
        broken, step = mutate()
        step["attempt"]["rc"] = False
        check("boolean_attempt_rc", broken, ("invalid attempt.rc",))
        broken, step = mutate()
        step["attempt"]["rc"] = 5
        check("rc_disagreement", broken, ("attempt.rc mismatch",))

        attempt_diagnostic = "expected attempt.outcome=sysctl_failed" if sysctl else "expected supported file-open attempt"
        broken, step = mutate()
        step["attempt"]["outcome"] = "unsupported"
        check("unavailable_with_unsupported_attempt", broken, (attempt_diagnostic,))
        step["sandbox_check"]["rc"] = 0
        check("prediction_and_attempt_failure", broken,
              ("expected unavailable sandbox_check.rc=-1", attempt_diagnostic))
        broken, step = mutate()
        del step["attempt"]
        check("missing_attempt", broken, (f"missing attempt for {step_id}",))
        broken, step = mutate()
        step["sandbox_check"] = None
        step["attempt"]["rc"] = False
        check("malformed_prediction_and_attempt", broken,
              (f"missing sandbox_check for {step_id}", "invalid attempt.rc"))

        broken, _ = mutate()
        broken["result"]["ok"] = False
        check("failed_result", broken, ("expected result.ok=true",))
        broken, _ = mutate()
        broken["data"]["runner_result"]["normalized_outcome"] = "runner_failed"
        check("failed_runner", broken, ("expected runner normalized_outcome=ok",))
        broken, _ = mutate()
        broken["data"]["runner_result"]["policy_format"] = "unrequested-format"
        check("wrong_policy_format", broken, ("expected policy_format='sbpl'",))
        check("malformed_json", None, ("cannot read run JSON",), raw="{invalid")
        check("non_object_json", [], ("run is not an object",))

        if sysctl:
            for errno in (None, 2, True):
                broken, step = mutate()
                step["attempt"].update(errno=errno, syscall_errno=errno)
                check(f"not_a_denial_{errno}", broken, ("expected attempt.errno=EPERM/EACCES",))
            broken, step = mutate()
            step["attempt"]["syscall_errno"] = 13
            check("denial_errno_disagreement", broken, ("attempt.errno mismatch",))
            broken, step = mutate()
            step["attempt"].update(rc=0, exit_code=0)
            check("denial_with_success_status", broken, ("expected attempt_ok=False",))

    if failures:
        raise SystemExit("\n".join(failures))
    print(f"{count} filter checker controls passed")


if __name__ == "__main__":
    main()
