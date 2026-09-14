#!/usr/bin/env python3
"""CLI adapter for the three runner_filter_* suites.

blackbox owns envelope/step/evidence validation. Callers supply step identity,
operation and the attempt contract; an unavailable prediction never skips the
attempt checks. This adapter neither launches PW nor derives expectations from
the returned envelope or production filter tables.
"""
import argparse
import json
import sys
from pathlib import Path

from blackbox import validate_run_shape, validate_step


def validate_run(run, step_id, operation, attempt_contract):
    expected = {"step_id": step_id, "sandbox_outcome": "prediction_unavailable"}
    if attempt_contract == "sysctl_denied":
        expected["attempt_ok"] = False
    errors, matched = validate_run_shape(run, [expected], policy_format="sbpl")
    for step, exp in matched:
        errors.extend(validate_step(step, exp))
        sb = step.get("sandbox_check")
        if isinstance(sb, dict) and sb.get("operation") != operation:
            errors.append(f"{step_id}: expected sandbox_check.operation={operation!r} "
                          f"(got {sb.get('operation')!r})")
        attempt = step.get("attempt")
        if not isinstance(attempt, dict):
            continue  # validate_step has reported the missing channel.
        if "rc" not in attempt:
            errors.append(f"{step_id}: missing attempt.rc")
        if attempt_contract == "file_open":
            # These are supported file-open placeholders, not IOKit witnesses.
            if attempt.get("outcome") not in ("ok", "open_failed"):
                errors.append(f"{step_id}: expected supported file-open attempt "
                              f"(got {attempt.get('outcome')!r})")
        else:
            if attempt.get("outcome") != "sysctl_failed":
                errors.append(f"{step_id}: expected attempt.outcome=sysctl_failed "
                              f"(got {attempt.get('outcome')!r})")
            errno = attempt.get("errno")
            if type(errno) is not int or errno not in (1, 13):
                errors.append(f"{step_id}: expected attempt.errno=EPERM/EACCES (got {errno!r})")
            if errno != attempt.get("syscall_errno"):
                errors.append(f"{step_id}: attempt.errno and syscall_errno disagree")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--step-id", required=True)
    parser.add_argument("--operation", required=True)
    parser.add_argument("--attempt", choices=("file_open", "sysctl_denied"), required=True)
    args = parser.parse_args()
    try:
        run = json.loads(args.run.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"cannot read run JSON: {exc}", file=sys.stderr)
        return 1
    errors = validate_run(run, args.step_id, args.operation, args.attempt)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("unavailable prediction and attempt evidence checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
