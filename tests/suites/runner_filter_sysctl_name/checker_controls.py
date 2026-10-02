#!/usr/bin/env python3
"""Exercise the filter checker CLI with hand-authored evidence, without PW.

Keep inputs, expected statuses and diagnostics independent of the checker and
production code. Each caller's arguments are repeated deliberately so a generic
contract passing in another suite cannot substitute for checking these adapters.
Every control is a current-contract document: the record names the planning
exclusion, the attempt keeps its own observation, and the version is read exactly.
"""
import copy
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import contract
from blackbox import envelope_skeleton

CHECKER = ROOT / "tests/lib/unavailable_prediction.py"
CALLERS = (
    ("iokit_registry_entry_class", "iosurface_open", "iokit-open-service", "IOSurfaceRoot", "file_open"),
    ("iokit_user_client_class", "iosurfaceroot_uc", "iokit-open-user-client", "IOSurfaceRootUserClient", "file_open"),
    ("sysctl_name", "kern_osrelease", "sysctl-read", "kern.osrelease", "sysctl_denied"),
)


def current_reply(step_id, operation, value, sysctl):
    """A reply with one planning-excluded query beside a completed attempt."""
    step = {
        "step_id": step_id,
        "sandbox_check": {
            "pid": 1234, "operation": operation, "filter_kind": "sysctl_name" if sysctl else operation.split("-")[-1],
            "filter_value": value, "filter_type_id": None,
            "outcome": "prediction_unavailable", "rc": -1, "native_rc": None, "errno": None, "error": None,
            "result_source": "synthetic", "missing_reason": "query_not_requested",
        },
        "attempt": {
            "requested_kind": "sysctl" if sysctl else "file",
            "requested_action": "read" if sysctl else "open_read",
            "outcome": "sysctl_failed" if sysctl else "ok",
            "rc": 1 if sysctl else 0, "errno": 1 if sysctl else None, "error": None,
            "requested_path": "kern.osrelease" if sysctl else "/etc/hosts",
            "observed_path": None if sysctl else "/private/etc/hosts",
            "result_source": "worker",
            "lifecycle": {"boundary": {"state": "supported", "answer": "reached", "basis": ["slot", "attempt_support"]},
                          "result": {"state": "supported", "answer": "published", "basis": ["slot", "attempt_support"]},
                          "summary": "completed"},
        },
        # The relations come from the submitted scopes even though the query was
        # never asked: the sysctl pair names the same operation and target, the
        # IOKit placeholders name a different operation and a non-path target.
        "comparison": {
            "observation": "permission_failure" if sysctl else "succeeded",
            "observation_basis": "permission_errno" if sysctl else "completed_worker_status",
            "operation_relation": "matched" if sysctl else "different",
            "target_relation": "same_submitted" if sysctl else "unresolved",
            "order": "unestablished", "limitations": ["query_plan:prediction_unavailable_pair"],
        },
    }
    if not sysctl:
        step["attempt"]["path_diagnostics"] = {"input": "/etc/hosts", "observer": "runner_host",
                                              "phase": "after_orchestration", "same_as_input": [],
                                              "realpath_resolved": "/private/etc/hosts",
                                              "parent_realpath_resolved": "/private/etc/hosts"}
    return {
        "schema_version": contract.RESPONSE_SCHEMA, "normalized_outcome": "ok", "rc": 0, "error": None,
        "policy_format": "sbpl", "sandboxed_after_apply": True, "pid": 1234, "specimen_id": "control",
        "runner_subprocess": {"pid": 1234, "reaped": True, "exit_code": 0, "term_signal": None, "partial_steps": False,
                              "disposition": {"questions": {}, "steps": [], "issues": []},
                              "ordering": {"collection_closed_before_proceed": True, "proceed_set": True,
                                           "proceed_observed": True, "worker_lifetime_established": True,
                                           "protocol_violations": [], "validator_disposition": "not_needed"}},
        "steps": [step],
    }


def main():
    artifacts = Path(sys.argv[1])
    artifacts.mkdir(parents=True, exist_ok=True)
    failures = []
    count = 0
    for name, step_id, operation, value, attempt_contract in CALLERS:
        sysctl = name == "sysctl_name"
        baseline = envelope_skeleton(current_reply(step_id, operation, value, sysctl))

        def check(label, envelope, diagnostics=(), status=1, raw=None):
            nonlocal count
            count += 1
            stem = artifacts / f"{name}.{label}"
            run_path = Path(f"{stem}.run.json")
            run_path.write_text(raw if raw is not None else json.dumps(envelope, indent=2) + "\n")
            argv = [sys.executable, str(CHECKER), str(run_path), "--step-id", step_id,
                    "--operation", operation, "--filter-value", value, "--attempt", attempt_contract]
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
        # The version is read exactly: other and malformed versions are one error.
        for label, version in (("previous", contract.RESPONSE_SCHEMA - 1), ("next", contract.RESPONSE_SCHEMA + 1),
                               ("null", None), ("string", str(contract.RESPONSE_SCHEMA)),
                               ("float", float(contract.RESPONSE_SCHEMA)), ("boolean", True)):
            changed, _ = mutate()
            changed["data"]["runner_result"]["schema_version"] = version
            expected = "unsupported runner response" if type(version) is int and not isinstance(version, bool) else "malformed runner response"
            check("version_" + label, changed, (expected,))
        changed, _ = mutate()
        changed["schema_version"] = contract.CONTROLLER_ENVELOPE + 1
        check("version_envelope_next", changed, ("unsupported controller envelope",))
        changed, step = mutate()
        del step["comparison"]["order"]
        check("missing_order", changed, ("invalid comparison.order",))
        changed, step = mutate()
        step["comparison"]["limitations"] = []
        check("missing_plan_limitation", changed, ("exactly one query_plan limitation",))
        changed, step = mutate()
        step["comparison"]["order"] = "query_first"
        check("order_claimed_without_record", changed, ("lacks eligible record",))
        changed, _ = mutate()
        del changed["data"]["runner_result"]["runner_subprocess"]["ordering"]
        check("missing_ordering", changed, ("ordering is required",))
        changed, step = mutate()
        del step["comparison"]
        del step["attempt"]["requested_kind"]
        del step["attempt"]["requested_action"]
        check("missing_current_evidence", changed,
              ("missing comparison", "missing attempt.requested_kind", "missing attempt.requested_action"))
        # One unknown key proves this CLI reaches the shared shape allowlist;
        # blackbox_e2e/checker_controls owns the validator's own controls.
        changed, step = mutate()
        step["drift"] = None
        check("unknown_key_reaches_consumer", changed, ("unknown key reply.steps[].drift",))
        changed, step = mutate()
        step["comparison"]["limitations"].append("sandbox_attribution_unestablished")
        check("foreign_limitation", changed, ("outside the vocabulary",))
        changed, step = mutate()
        if sysctl:
            step["attempt"].update(errno=13)
            check("eacces_denial", changed, status=0)
        else:
            # Supported file work can report an OS failure. These placeholders
            # check attempt reporting, not IOKit enforcement.
            step["attempt"].update(outcome="open_failed", rc=1, errno=2, observed_path=None)
            step["comparison"].update(observation="other_failure", observation_basis="completed_worker_status")
            check("supported_file_failure", changed, status=0)

        for channel, keys in (
            ("sandbox_check", ("pid", "operation", "filter_value", "filter_type_id", "errno", "error")),
            ("attempt", ("errno", "requested_path", "observed_path", "rc")),
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
        broken, step = mutate()
        step["sandbox_check"].update(result_source="validator", missing_reason=None)
        check("unavailable_without_synthetic_record", broken, ("synthetic query_not_requested record",))

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
        step["sandbox_check"]["filter_value"] = "unrequested-filter-value"
        check("wrong_filter_value", broken, ("expected sandbox_check.filter_value=",))
        broken, step = mutate()
        step["sandbox_check"].update(outcome="allow", rc=0, filter_type_id=1)
        check("wrong_prediction", broken, ("expected sandbox_check prediction_unavailable",))
        broken, step = mutate()
        step["attempt"]["rc"] = False
        check("boolean_attempt_rc", broken, ("invalid attempt.rc",))

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
                step["attempt"].update(errno=errno)
                check(f"not_a_denial_{errno}", broken, ("expected attempt.errno=EPERM/EACCES",))
            broken, step = mutate()
            step["attempt"].update(rc=0)
            check("denial_with_success_status", broken, ("expected attempt_ok=False",))
            broken, step = mutate()
            step["sandbox_check"]["path_diagnostics"] = {"input": "kern.osrelease", "observer": "runner_host",
                                                        "phase": "after_orchestration",
                                                        "same_as_input": ["realpath_resolved", "firmlink_resolved"]}
            check("non_path_query_with_path_provenance", broken, ("non-path query acquired path provenance",))

    if failures:
        raise SystemExit("\n".join(failures))
    print(f"{count} filter checker controls passed")


if __name__ == "__main__":
    main()
