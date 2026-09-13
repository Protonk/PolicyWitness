#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_step(step, exp):
    # Collect each channel's errors independently. A prediction discrepancy
    # must not stop validation of this attempt or any subsequent step.
    errors = []
    fail = errors.append
    step_id = exp["step_id"]
    sb = step.get("sandbox_check")
    if not isinstance(sb, dict):
        fail(f"missing sandbox_check for {step_id}")
        sb = {}
    else:
        for key in ("scope", "effective_filter_value", "pid", "operation", "filter_type_id", "errno", "error"):
            if key not in sb:
                fail(f"{step_id}: missing sandbox_check.{key}")
        if type(sb.get("pid")) is not int:
            fail(f"{step_id}: invalid sandbox_check.pid={sb.get('pid')!r}")
        if not isinstance(sb.get("operation"), str) or not sb.get("operation"):
            fail(f"{step_id}: invalid sandbox_check.operation={sb.get('operation')!r}")
        if sb.get("outcome") == "prediction_unavailable":
            # This is an explicit result contract, never a reason to skip.
            # PolicyWitness.md: unavailable predictions use rc=-1 and null
            # errno/filter_type_id/drift; the attempt must still be checked.
            if type(sb.get("rc")) is not int or sb["rc"] != -1:
                fail(f"{step_id}: expected unavailable sandbox_check.rc=-1 (got {sb.get('rc')!r})")
            for key in ("filter_type_id", "errno"):
                if sb.get(key) is not None:
                    fail(f"{step_id}: expected unavailable sandbox_check.{key}=null (got {sb[key]!r})")
            if "drift" not in step or step["drift"] is not None:
                fail(f"{step_id}: expected unavailable prediction to have explicit drift=null")
        elif type(sb.get("filter_type_id")) is not int:
            fail(f"{step_id}: invalid sandbox_check.filter_type_id={sb.get('filter_type_id')!r}")
        if sb.get("errno") is not None and type(sb.get("errno")) is not int:
            fail(f"{step_id}: invalid sandbox_check.errno={sb.get('errno')!r}")
        if sb.get("error") is not None and not isinstance(sb.get("error"), str):
            fail(f"{step_id}: invalid sandbox_check.error={sb.get('error')!r}")

    sb_outcome = sb.get("outcome")
    exp_outcome = exp.get("sandbox_outcome")
    if exp_outcome and sb_outcome != exp_outcome:
        fail(f"{step_id}: expected sandbox_check {exp_outcome} (got {sb_outcome!r})")

    attempt = step.get("attempt")
    attempt_ok = None
    if not isinstance(attempt, dict):
        fail(f"missing attempt for {step_id}")
    else:
        for key in ("exit_code", "syscall_errno", "requested_path", "normalized_path", "observed_path"):
            if key not in attempt:
                fail(f"{step_id}: missing attempt.{key}")
        exit_code = attempt.get("exit_code")
        if type(exit_code) is not int:
            fail(f"{step_id}: invalid attempt.exit_code={exit_code!r}")
        else:
            attempt_ok = exit_code == 0
            if "attempt_ok" in exp and attempt_ok != exp["attempt_ok"]:
                fail(f"{step_id}: expected attempt_ok={exp['attempt_ok']!r} (got {attempt_ok!r})")
        if type(attempt.get("rc")) is int and attempt["rc"] != exit_code:
            fail(f"{step_id}: attempt.rc mismatch (rc={attempt['rc']!r} exit_code={exit_code!r})")
        if exp.get("errno") is not None:
            got_errno = attempt.get("syscall_errno", attempt.get("errno"))
            if got_errno != exp["errno"]:
                fail(f"{step_id}: expected errno={exp['errno']!r} (got {got_errno!r})")

    if "deny_signal_delta" in exp:
        signal = step.get("deny_signal")
        delta = signal.get("delta") if isinstance(signal, dict) else None
        expected_delta = exp["deny_signal_delta"]
        if type(delta) is not int:
            fail(f"{step_id}: invalid deny_signal.delta={delta!r}")
        elif expected_delta == "nonzero" and delta <= 0:
            fail(f"{step_id}: expected deny_signal delta>0 (got {delta})")
        elif type(expected_delta) is int and delta != expected_delta:
            fail(f"{step_id}: expected deny_signal delta={expected_delta} (got {delta})")

    if "expect_denial" in exp and sb_outcome is not None and attempt_ok is not None:
        is_denial = sb_outcome == "deny" and not attempt_ok
        if is_denial != exp["expect_denial"]:
            fail(f"{step_id}: expected denial={exp['expect_denial']!r} (got {is_denial!r})")

    return errors


def validate_run(run, expected):
    errors = []
    fail = errors.append
    if run.get("kind") != "run":
        fail(f"expected kind=run (got {run.get('kind')!r})")
    if run.get("result", {}).get("ok") is not True:
        fail(f"expected result.ok=true (got {run.get('result', {}).get('ok')!r})")

    runner = (run.get("data") or {}).get("runner_result")
    if not isinstance(runner, dict):
        return errors + ["missing data.runner_result"]
    if runner.get("normalized_outcome") != "ok":
        fail(f"expected runner normalized_outcome=ok (got {runner.get('normalized_outcome')!r})")

    policy_format = expected.get("policy_format")
    if policy_format and runner.get("policy_format") != policy_format:
        fail(f"expected policy_format={policy_format!r} (got {runner.get('policy_format')!r})")
    if expected.get("require_sandboxed_after_apply") is True and runner.get("sandboxed_after_apply") is not True:
        fail(f"expected sandboxed_after_apply=true (got {runner.get('sandboxed_after_apply')!r})")
    if expected.get("require_policy_sha256") is True and not runner.get("policy_sha256"):
        fail("expected policy_sha256 to be present")

    steps = runner.get("steps")
    if not isinstance(steps, list):
        return errors + ["runner.steps is not a list"]
    expected_steps = expected["steps"]
    expected_ids = [exp["step_id"] for exp in expected_steps]
    if any(not isinstance(key, str) or not key for key in expected_ids) or len(set(expected_ids)) != len(expected_ids):
        return errors + ["expected.json must have unique, nonempty step IDs"]
    actual_ids = [step.get("step_id") if isinstance(step, dict) else None for step in steps]
    if actual_ids != expected_ids:
        fail(f"expected step IDs in order {expected_ids!r} (got {actual_ids!r})")

    by_id = {exp["step_id"]: exp for exp in expected_steps}
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            fail(f"runner.steps[{index}] is not an object")
            continue
        step_id = step.get("step_id")
        if not isinstance(step_id, str) or step_id not in by_id:
            fail(f"runner.steps[{index}]: unexpected step_id={step_id!r}")
            continue
        errors.extend(validate_step(step, by_id[step_id]))
    return errors


def main():
    if len(sys.argv) != 3:
        print("usage: validate_run.py <run.json> <expected.json>", file=sys.stderr)
        return 2
    errors = validate_run(load_json(sys.argv[1]), load_json(sys.argv[2]))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
