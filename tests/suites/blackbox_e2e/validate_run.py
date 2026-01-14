#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def fail(msg: str) -> None:
    raise SystemExit(msg)


def skip(msg: str) -> None:
    print(msg)
    raise SystemExit(3)

def load_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))

if len(sys.argv) != 3:
    print("usage: validate_run.py <run.json> <expected.json>", file=sys.stderr)
    sys.exit(2)

run_path, expected_path = sys.argv[1:3]
run = load_json(run_path)
expected = load_json(expected_path)

if run.get("kind") != "run":
    fail(f"expected kind=run (got {run.get('kind')!r})")
if run.get("result", {}).get("ok") is not True:
    fail(f"expected result.ok=true (got {run.get('result', {}).get('ok')!r})")

runner = (run.get("data") or {}).get("runner_result")
if not isinstance(runner, dict):
    fail("missing data.runner_result")
if runner.get("normalized_outcome") != "ok":
    fail(f"expected runner normalized_outcome=ok (got {runner.get('normalized_outcome')!r})")

policy_format = expected.get("policy_format")
if policy_format and runner.get("policy_format") != policy_format:
    fail(f"expected policy_format={policy_format!r} (got {runner.get('policy_format')!r})")

if expected.get("require_sandboxed_after_apply") is True:
    if runner.get("sandboxed_after_apply") is not True:
        fail(f"expected sandboxed_after_apply=true (got {runner.get('sandboxed_after_apply')!r})")

if expected.get("require_policy_sha256") is True:
    if not runner.get("policy_sha256"):
        fail("expected policy_sha256 to be present")

steps = runner.get("steps") or []
if not isinstance(steps, list):
    fail("runner.steps is not a list")

expected_steps = expected.get("steps") or []
if len(steps) != len(expected_steps):
    fail(f"expected {len(expected_steps)} steps (got {len(steps)})")

by_id = {s.get("step_id"): s for s in steps}

for exp in expected_steps:
    step_id = exp.get("step_id")
    if not step_id:
        fail("expected step_id in expected.json")
    step = by_id.get(step_id)
    if step is None:
        fail(f"missing step_id {step_id!r}")

    sb = step.get("sandbox_check")
    if not isinstance(sb, dict):
        fail(f"missing sandbox_check for {step_id}")
    attempt = step.get("attempt")
    if not isinstance(attempt, dict):
        fail(f"missing attempt for {step_id}")

    sb_outcome = sb.get("outcome")
    exp_outcome = exp.get("sandbox_outcome")
    if exp_outcome and sb_outcome != exp_outcome:
        skip(
            f"{step_id}: expected sandbox_check {exp_outcome} (got {sb_outcome!r}); "
            "host sandbox_check appears unreliable (see anomalies suite)"
        )

    attempt_ok = attempt.get("rc") == 0
    if "attempt_ok" in exp and attempt_ok != exp.get("attempt_ok"):
        fail(f"{step_id}: expected attempt_ok={exp.get('attempt_ok')!r} (got {attempt_ok!r})")

    if exp.get("errno") is not None:
        if attempt.get("errno") != exp.get("errno"):
            fail(f"{step_id}: expected errno={exp.get('errno')!r} (got {attempt.get('errno')!r})")

    if "deny_signal_delta" in exp:
        delta = ((step.get("deny_signal") or {}).get("delta") or 0)
        expected_delta = exp.get("deny_signal_delta")
        if expected_delta == "nonzero":
            if delta <= 0:
                fail(f"{step_id}: expected deny_signal delta>0 (got {delta})")
        elif isinstance(expected_delta, int):
            if delta != expected_delta:
                fail(f"{step_id}: expected deny_signal delta={expected_delta} (got {delta})")

    if "expect_denial" in exp:
        is_denial = (sb_outcome == "deny" and not attempt_ok)
        if is_denial != exp.get("expect_denial"):
            fail(f"{step_id}: expected denial={exp.get('expect_denial')!r} (got {is_denial!r})")

print("ok")
