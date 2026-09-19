#!/usr/bin/env python3
"""CLI adapter for the three runner_filter_* suites.

blackbox owns envelope/step/evidence validation. Callers supply step identity,
operation, filter value and the attempt contract; an unavailable prediction
never skips the attempt checks. This adapter neither launches PW nor derives
expectations from the returned envelope or production filter tables.
"""
import argparse
import json
import sys
from pathlib import Path

from blackbox import validate_run_shape, validate_step
from consumer import recover_evidence


def validate_run(run, step_id, operation, filter_value, attempt_contract):
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
        if isinstance(sb, dict) and sb.get("effective_filter_value") != filter_value:
            errors.append(f"{step_id}: expected sandbox_check.effective_filter_value={filter_value!r} "
                          f"(got {sb.get('effective_filter_value')!r})")
        attempt = step.get("attempt")
        if not isinstance(attempt, dict):
            continue  # validate_step has reported the missing channel.
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
    if errors:
        return errors
    version = ((run.get('data') or {}).get('runner_result') or {}).get('schema_version', 0)
    if type(version) is int and version >= 7 and attempt_contract == 'sysctl_denied':
        answers = recover_evidence(run)
        answer = answers['steps'][0]
        if answers['comparison_groups']['unavailable'] != [step_id] or answers['failure_groups']['unattributed_failure'] != [step_id]:
            errors.append(f'{step_id}: cannot recover independent unavailable prediction and unattributed failure')
        required = {'prediction:query_not_requested', 'query_plan:prediction_unavailable_pair', 'sandbox_attribution_unestablished'}
        if not required <= set(answer['comparison']['limitations']):
            errors.append(f'{step_id}: cannot recover simultaneous planning, prediction and attribution limits')
        if answer['prediction_missing_reason'] != 'query_not_requested' or answer['attempt_missing_reason'] is not None:
            errors.append(f'{step_id}: unavailable prediction erased channel missing reasons')
        if answer['path_reporting'] != 'not_reported':
            errors.append(f'{step_id}: non-path query acquired path provenance')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--step-id", required=True)
    parser.add_argument("--operation", required=True)
    parser.add_argument("--filter-value", required=True)
    parser.add_argument("--attempt", choices=("file_open", "sysctl_denied"), required=True)
    args = parser.parse_args()
    try:
        run = json.loads(args.run.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"cannot read run JSON: {exc}", file=sys.stderr)
        return 1
    errors = validate_run(run, args.step_id, args.operation, args.filter_value, args.attempt)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("unavailable prediction and attempt evidence checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
