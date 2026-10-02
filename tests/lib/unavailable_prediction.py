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

import consumer
from blackbox import validate_run_shape, validate_step


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
        if isinstance(sb, dict) and sb.get("filter_value") != filter_value:
            errors.append(f"{step_id}: expected sandbox_check.filter_value={filter_value!r} "
                          f"(got {sb.get('filter_value')!r})")
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
    # The planning exclusion and the attempt are independent channels: the
    # record names the exclusion and claims no order, and the attempt keeps
    # its own observation beside it.
    step = consumer.select(consumer.steps(run), step_id=step_id)[0]
    comparison = step["comparison"]
    if comparison["order"] != "unestablished" or "query_plan:prediction_unavailable_pair" not in comparison["limitations"]:
        errors.append(f"{step_id}: planning exclusion must carry order=unestablished and the pair limitation")
    if step["sandbox_check"].get("result_source") != "synthetic" or step["sandbox_check"].get("missing_reason") != "query_not_requested":
        errors.append(f"{step_id}: unavailable prediction erased the synthetic query_not_requested record")
    if attempt_contract == "sysctl_denied":
        if (comparison["observation"], comparison["observation_basis"]) != ("permission_failure", "permission_errno"):
            errors.append(f"{step_id}: denied sysctl must be observed as a permission failure by errno")
        if "path_diagnostics" in step["sandbox_check"]:
            errors.append(f"{step_id}: non-path query acquired path provenance")
    elif comparison["observation"] not in ("succeeded", "other_failure"):
        errors.append(f"{step_id}: file-open placeholder observation {comparison['observation']!r} is not a supported-file result")
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
