#!/usr/bin/env python3
"""Validate a captured menagerie run without launching PolicyWitness."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from blackbox import validate_run_shape, validate_step


def validate_run(expected_steps, run_data):
    errors, matched = validate_run_shape(
        run_data, expected_steps, require_sandboxed_after_apply=True,
        require_policy_sha256=True,
    )
    mismatch_notes = []
    pending_skips = []
    for step, exp in matched:
        step_id = exp["step_id"]
        exp_meta = exp.get("expect") or {}
        common = {key: exp_meta[key] for key in ("attempt_ok", "errno", "drift") if key in exp_meta}
        if "predict" in exp_meta:
            common["sandbox_outcome"] = exp_meta["predict"]
        errors.extend(validate_step(step, common))

        # These are specimen-specific observations and policy expectations,
        # separate from the common evidence shape and correlation contract.
        attempt = step.get("attempt")
        if not isinstance(attempt, dict):
            continue
        exit_code = attempt.get("exit_code")
        attempt_ok = exit_code == 0 if type(exit_code) is int else None
        exp_attempt = exp.get("attempt") or {}
        if exp_attempt.get("kind") == "file":
            expected_target = exp_attempt.get("target")
            if expected_target and attempt.get("requested_path") != expected_target:
                errors.append(f"{step_id}: expected requested_path={expected_target!r} "
                              f"(got {attempt.get('requested_path')!r})")
            if attempt_ok is False and attempt.get("syscall_errno") is None:
                errors.append(f"{step_id}: expected syscall_errno on failed file attempt")
            if attempt_ok is True and attempt.get("syscall_errno") is not None:
                errors.append(f"{step_id}: unexpected syscall_errno on successful file attempt")
            if attempt_ok is True and exp_attempt.get("action") in ("open_read", "open_write", "create"):
                if attempt.get("observed_path") is None:
                    errors.append(f"{step_id}: expected observed_path for successful open/create")

        policy = exp_meta.get("policy")
        mismatch_reason = exp_meta.get("mismatch_reason")
        if policy in ("allow", "deny") and attempt_ok is not None:
            policy_match = (policy == "allow") == attempt_ok
            if mismatch_reason:
                if policy_match:
                    pending_skips.append(f"{step_id}: expected mismatch ({mismatch_reason}) not observed")
                else:
                    mismatch_notes.append(f"{step_id}:{mismatch_reason}")
            elif not policy_match:
                errors.append(f"{step_id}: policy={policy} but attempt_ok={attempt_ok}")

    # A host-dependent mismatch is only a skip if all evidence checks passed.
    if errors:
        return 1, "\n".join(errors)
    if pending_skips:
        return 3, "\n".join(pending_skips)
    if mismatch_notes:
        return 0, f"ok (mismatch evidence: {', '.join(mismatch_notes)})"
    return 0, "ok"


def main():
    if len(sys.argv) != 3:
        print("usage: validate_run.py <run.json> <expected.json>", file=sys.stderr)
        return 2
    run = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    expected = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    status, message = validate_run(expected["steps"], run)
    print(message)
    return status


if __name__ == "__main__":
    sys.exit(main())
