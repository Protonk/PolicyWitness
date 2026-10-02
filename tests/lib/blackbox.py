"""Checks shared by successful-run black-box suites.

Only JSON evidence and caller-authored expectations belong here. This module
does not launch processes, interpret policies, choose expectations, or skip
tests. Errors accumulate so a broken channel cannot conceal another failure.
"""

import contract
from consumer import validate


def envelope_skeleton(runner, *, ok=True, timeout_ms=240000):
    """A current-contract `kind: run` envelope around a constructed reply.

    Control files use this to put a hand-authored reply inside the uniform
    data skeleton (D2) so the full document validator can read it. The dossier
    it carries says nothing was selected; it is not a live observation.
    """
    reason = 'constructed control: no runner was selected'
    binary = {'path': None, 'actual_sha256': None, 'baseline_sha256': None,
              'verification': 'unavailable', 'reason': reason}
    return {
        'schema_version': contract.CONTROLLER_ENVELOPE, 'kind': 'run',
        'result': {'ok': ok, 'rc': None, 'exit_code': 0 if ok else 1,
                   'normalized_outcome': (runner or {}).get('normalized_outcome'), 'errno': None,
                   'error': None, 'stderr': None, 'stdout': None},
        'data': {
            'specimen': {
                'request_path': '/constructed/request.json',
                'policy': {'augmentation': {'status': 'not_applicable', 'applied': [], 'original_sha256': None,
                                            'applied_sha256': None, 'error': None},
                           'imports': {'status': 'not_applicable', 'closure_sha256': None, 'records': [],
                                       'cycle': None, 'exceeded': None, 'failure': None}},
                'host': {'macos_version': '14.0', 'macos_build': '23A000', 'kernel_release': '23.0.0', 'arch': 'arm64'},
                'runner_provenance': None, 'app_provenance': None,
                'binaries': {'service': dict(binary), 'worker': dict(binary), 'validator': dict(binary)}},
            'policy_check': None, 'timeout_ms': timeout_ms,
            'runner_client': {'argv': ['constructed-client'], 'started_at_unix_ms': 1000, 'ended_at_unix_ms': 2500,
                              'exit_code': 0, 'request_delivery': {'bytes_written': 2, 'error': None}},
            'runner_result': runner, 'sandbox_log_capture': None, 'runner_sandbox_diagnostics': None,
        },
    }


def validate_run_shape(run, expected_steps, *, policy_format=None,
                       require_sandboxed_after_apply=False, require_policy_sha256=False):
    """Return (errors, [(actual_step, expected_step), ...]) in received order.

    Match by ID even after an order error, so subsequent diagnostics name the
    right expectation. Never collapse duplicate returned IDs into a dictionary.
    The whole document is validated under the current contract; another
    version yields its one version error beside the step diagnostics.
    """
    errors = []
    if not isinstance(run, dict):
        return ["run is not an object"], []
    if run.get("kind") != "run":
        errors.append(f"expected kind=run (got {run.get('kind')!r})")
    result = run.get("result")
    if not isinstance(result, dict):
        errors.append("result is not an object")
    elif result.get("ok") is not True:
        errors.append(f"expected result.ok=true (got {result.get('ok')!r})")
    data = run.get("data")
    if not isinstance(data, dict):
        return errors + ["data is not an object"], []
    runner = data.get("runner_result")
    if not isinstance(runner, dict):
        return errors + ["missing data.runner_result"], []
    if runner.get("normalized_outcome") != "ok":
        errors.append(f"expected runner normalized_outcome=ok (got {runner.get('normalized_outcome')!r})")
    if policy_format and runner.get("policy_format") != policy_format:
        errors.append(f"expected policy_format={policy_format!r} (got {runner.get('policy_format')!r})")
    if require_sandboxed_after_apply and runner.get("sandboxed_after_apply") is not True:
        errors.append(f"expected sandboxed_after_apply=true (got {runner.get('sandboxed_after_apply')!r})")
    if require_policy_sha256 and not runner.get("policy_sha256"):
        errors.append("expected policy_sha256 to be present")

    steps = runner.get("steps")
    if not isinstance(steps, list):
        return errors + ["runner.steps is not a list"], []
    expected_ids = [exp.get("step_id") if isinstance(exp, dict) else None for exp in expected_steps]
    if any(not isinstance(key, str) or not key for key in expected_ids) or len(set(expected_ids)) != len(expected_ids):
        return errors + ["expected.json must have unique, nonempty step IDs"], []
    actual_ids = [step.get("step_id") if isinstance(step, dict) else None for step in steps]
    if actual_ids != expected_ids:
        errors.append(f"expected step IDs in order {expected_ids!r} (got {actual_ids!r})")

    by_id = dict(zip(expected_ids, expected_steps))
    matched = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            errors.append(f"runner.steps[{index}] is not an object")
            continue
        step_id = step.get("step_id")
        if not isinstance(step_id, str) or step_id not in by_id:
            errors.append(f"runner.steps[{index}]: unexpected step_id={step_id!r}")
            continue
        matched.append((step, by_id[step_id]))
    errors.extend(validate(run))
    return errors, matched


def validate_step(step, expected):
    """Check both channels plus explicitly supplied outcome/attempt/errno/comparison.

    Nullable fields must still be present. JSON booleans are not integers, and
    an unavailable prediction has a defined sentinel shape, not skip semantics.
    An explicit expected errno=None requires null. `expected.comparison` names
    D1 record fields that must equal the given values. Suite-specific policy
    and observation assertions stay with their callers.
    """
    errors = []
    fail = errors.append
    step_id = step["step_id"]
    comparison = step.get("comparison")
    for key, value in expected.get("comparison", {}).items():
        if not isinstance(comparison, dict) or comparison.get(key) != value:
            fail(f"{step_id}: expected comparison.{key}={value!r}")
    sb = step.get("sandbox_check")
    if not isinstance(sb, dict):
        fail(f"missing sandbox_check for {step_id}")
        sb = {}
    else:
        for key in ("pid", "operation", "filter_value", "filter_type_id", "errno", "error"):
            if key not in sb:
                fail(f"{step_id}: missing sandbox_check.{key}")
        if type(sb.get("pid")) is not int:
            fail(f"{step_id}: invalid sandbox_check.pid={sb.get('pid')!r}")
        if not isinstance(sb.get("operation"), str) or not sb.get("operation"):
            fail(f"{step_id}: invalid sandbox_check.operation={sb.get('operation')!r}")
        if sb.get("outcome") == "prediction_unavailable":
            if type(sb.get("rc")) is not int or sb["rc"] != -1:
                fail(f"{step_id}: expected unavailable sandbox_check.rc=-1 (got {sb.get('rc')!r})")
            for key in ("filter_type_id", "errno"):
                if sb.get(key) is not None:
                    fail(f"{step_id}: expected unavailable sandbox_check.{key}=null (got {sb[key]!r})")
        else:
            filter_type = sb.get("filter_type_id")
            nullable = sb.get("outcome") in ("error", "unsupported_operation")
            if type(filter_type) is not int and not (nullable and filter_type is None):
                fail(f"{step_id}: invalid sandbox_check.filter_type_id={filter_type!r}")
        if sb.get("errno") is not None and type(sb.get("errno")) is not int:
            fail(f"{step_id}: invalid sandbox_check.errno={sb.get('errno')!r}")
        if sb.get("error") is not None and not isinstance(sb.get("error"), str):
            fail(f"{step_id}: invalid sandbox_check.error={sb.get('error')!r}")
    if "sandbox_outcome" in expected and sb.get("outcome") != expected["sandbox_outcome"]:
        fail(f"{step_id}: expected sandbox_check {expected['sandbox_outcome']} (got {sb.get('outcome')!r})")

    attempt = step.get("attempt")
    if not isinstance(attempt, dict):
        fail(f"missing attempt for {step_id}")
    else:
        for key in ("rc", "errno", "requested_path", "observed_path"):
            if key not in attempt:
                fail(f"{step_id}: missing attempt.{key}")
        rc = attempt.get("rc")
        if type(rc) is not int:
            fail(f"{step_id}: invalid attempt.rc={rc!r}")
        elif "attempt_ok" in expected and (rc == 0) != expected["attempt_ok"]:
            fail(f"{step_id}: expected attempt_ok={expected['attempt_ok']!r} (got {rc == 0!r})")
        if attempt.get("errno") is not None and type(attempt["errno"]) is not int:
            fail(f"{step_id}: invalid attempt.errno={attempt['errno']!r}")
        if "errno" in expected and (type(attempt.get("errno")) is not type(expected["errno"])
                                     or attempt.get("errno") != expected["errno"]):
            fail(f"{step_id}: expected errno={expected['errno']!r} (got {attempt.get('errno')!r})")
    return errors
