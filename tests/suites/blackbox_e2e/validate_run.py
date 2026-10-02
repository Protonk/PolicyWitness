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
        rc = attempt.get("rc") if isinstance(attempt, dict) else None
        attempt_ok = rc == 0 if type(rc) is int else None
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
