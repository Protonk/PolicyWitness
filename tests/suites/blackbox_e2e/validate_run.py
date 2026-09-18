#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from blackbox import validate_run_shape, validate_step


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_run(run, expected):
    errors, matched = validate_run_shape(
        run, expected["steps"], policy_format=expected.get("policy_format"),
        require_sandboxed_after_apply=expected.get("require_sandboxed_after_apply") is True,
        require_policy_sha256=expected.get("require_policy_sha256") is True,
    )
    fail = errors.append
    for step, exp in matched:
        errors.extend(validate_step(step, exp))
        step_id = exp["step_id"]
        sb = step.get("sandbox_check")
        sb_outcome = sb.get("outcome") if isinstance(sb, dict) else None
        attempt = step.get("attempt")
        exit_code = attempt.get("exit_code") if isinstance(attempt, dict) else None
        attempt_ok = exit_code == 0 if type(exit_code) is int else None
        runner = (run.get("data") or {}).get("runner_result") or {}
        if exp.get("deny_signal_unavailable") is True or runner.get("schema_version", 0) >= 5:
            if "deny_signal" not in step or step["deny_signal"] is not None:
                fail(f"{step_id}: expected explicit deny_signal=null")
        # Legacy expectations remain usable when validating stored old replies.
        elif "deny_signal_delta" in exp:
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
