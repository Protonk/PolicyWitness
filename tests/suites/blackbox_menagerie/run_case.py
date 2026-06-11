#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def load_manifest(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases") or []
    by_id = {case.get("case_id"): case for case in cases}
    return data, by_id


def substitute(value, mapping):
    if isinstance(value, str):
        out = value
        for key, replacement in mapping.items():
            out = out.replace(f"{{{{{key}}}}}", replacement)
        return out
    if isinstance(value, list):
        return [substitute(item, mapping) for item in value]
    if isinstance(value, dict):
        return {k: substitute(v, mapping) for k, v in value.items()}
    return value


def resolve_case(case_id, manifest):
    _, by_id = load_manifest(manifest)
    case = by_id.get(case_id)
    if not case:
        raise SystemExit(f"unknown case_id: {case_id}")
    return case


def compute_roots(case, run_id):
    base_prefix = case.get("root_prefix") or "/private/tmp"
    base_prefix = base_prefix.rstrip("/")
    canon_root = f"{base_prefix}/pw-menagerie/{run_id}/{case['case_id']}"

    if canon_root.startswith("/private/tmp"):
        alias_root = canon_root.replace("/private/tmp", "/tmp", 1)
    elif canon_root.startswith("/private/var/tmp"):
        alias_root = canon_root.replace("/private/var/tmp", "/var/tmp", 1)
    else:
        alias_root = canon_root

    tmp_canon_root = f"/private/tmp/pw-menagerie/{run_id}/{case['case_id']}"
    tmp_alias_root = f"/tmp/pw-menagerie/{run_id}/{case['case_id']}"
    var_canon_root = f"/private/var/tmp/pw-menagerie/{run_id}/{case['case_id']}"
    var_alias_root = f"/var/tmp/pw-menagerie/{run_id}/{case['case_id']}"

    mapping = {
        "RUN_ID": run_id,
        "CASE_ID": case["case_id"],
        "CANON_ROOT": canon_root,
        "ALIAS_ROOT": alias_root,
        "TMP_CANON_ROOT": tmp_canon_root,
        "TMP_ALIAS_ROOT": tmp_alias_root,
        "VAR_CANON_ROOT": var_canon_root,
        "VAR_ALIAS_ROOT": var_alias_root,
    }
    return mapping


def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_sbpl(sbpl_path: Path, replacements, mapping):
    sbpl = sbpl_path.read_text(encoding="utf-8")
    if replacements:
        for needle, replacement in replacements.items():
            replacement = substitute(replacement, mapping)
            if needle not in sbpl:
                raise SystemExit(f"sbpl replacement missing: {needle!r} in {sbpl_path}")
            sbpl = sbpl.replace(needle, replacement)
    return sbpl


def run_policy_witness(pw_bin: Path, specimen_path: Path, stdout_path: Path, stderr_path: Path):
    with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
        proc = subprocess.run([str(pw_bin), "run", str(specimen_path)], stdout=out, stderr=err)
    return proc.returncode


def load_run_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"failed to parse run JSON: {exc}")


def validate_run(expected_steps, run_data):
    if run_data.get("kind") != "run":
        return (1, f"expected kind=run (got {run_data.get('kind')!r})")
    if run_data.get("result", {}).get("ok") is not True:
        return (1, f"expected result.ok=true (got {run_data.get('result', {}).get('ok')!r})")

    runner = (run_data.get("data") or {}).get("runner_result")
    if not isinstance(runner, dict):
        return (1, "missing data.runner_result")
    if runner.get("normalized_outcome") != "ok":
        return (1, f"expected runner normalized_outcome=ok (got {runner.get('normalized_outcome')!r})")
    if runner.get("sandboxed_after_apply") is not True:
        return (1, f"expected sandboxed_after_apply=true (got {runner.get('sandboxed_after_apply')!r})")
    if not runner.get("policy_sha256"):
        return (1, "expected policy_sha256 to be present")

    steps = runner.get("steps") or []
    expected_steps = expected_steps or []
    if len(steps) != len(expected_steps):
        return (1, f"expected {len(expected_steps)} steps (got {len(steps)})")

    by_id = {step.get("step_id"): step for step in steps}
    mismatch_notes = []

    for exp in expected_steps:
        step_id = exp.get("step_id")
        step = by_id.get(step_id)
        if not step:
            return (1, f"missing step_id {step_id!r}")

        attempt = step.get("attempt")
        sb = step.get("sandbox_check")
        if not isinstance(attempt, dict) or not isinstance(sb, dict):
            return (1, f"missing attempt/sandbox_check for {step_id}")

        if "exit_code" not in attempt:
            return (1, f"{step_id}: missing attempt.exit_code")
        if "syscall_errno" not in attempt:
            return (1, f"{step_id}: missing attempt.syscall_errno")
        for key in ("requested_path", "normalized_path", "observed_path"):
            if key not in attempt:
                return (1, f"{step_id}: missing attempt.{key}")
        if "scope" not in sb:
            return (1, f"{step_id}: missing sandbox_check.scope")
        if "effective_filter_value" not in sb:
            return (1, f"{step_id}: missing sandbox_check.effective_filter_value")
        for key in ("pid", "operation", "filter_type_id", "errno", "error"):
            if key not in sb:
                return (1, f"{step_id}: missing sandbox_check.{key}")
        if not isinstance(sb.get("pid"), int):
            return (1, f"{step_id}: invalid sandbox_check.pid={sb.get('pid')!r}")
        if not isinstance(sb.get("operation"), str) or not sb.get("operation"):
            return (1, f"{step_id}: invalid sandbox_check.operation={sb.get('operation')!r}")
        # filter_type_id is the resolved libsandbox filter type. It is only
        # populated for a real allow/deny verdict; the rc=-1 sentinels
        # (prediction_unavailable, unsupported_operation) carry filter_type_id
        # null by design, so only require an int when the validator actually
        # produced a verdict. (Without this gate read_missing — a legitimately
        # prediction_unavailable step — fails flakily whenever its path can't
        # be canonicalized.)
        if sb.get("outcome") in ("allow", "deny"):
            if not isinstance(sb.get("filter_type_id"), int):
                return (1, f"{step_id}: invalid sandbox_check.filter_type_id={sb.get('filter_type_id')!r}")
        if sb.get("errno") is not None and not isinstance(sb.get("errno"), int):
            return (1, f"{step_id}: invalid sandbox_check.errno={sb.get('errno')!r}")
        if sb.get("error") is not None and not isinstance(sb.get("error"), str):
            return (1, f"{step_id}: invalid sandbox_check.error={sb.get('error')!r}")

        exit_code = attempt.get("exit_code")
        if not isinstance(exit_code, int):
            return (1, f"{step_id}: invalid attempt.exit_code={exit_code!r}")
        if isinstance(attempt.get("rc"), int) and attempt.get("rc") != exit_code:
            return (1, f"{step_id}: attempt.rc mismatch (rc={attempt.get('rc')!r} exit_code={exit_code!r})")
        attempt_ok = exit_code == 0
        exp_meta = exp.get("expect") or {}
        exp_attempt = exp.get("attempt") or {}

        if "attempt_ok" in exp_meta:
            if attempt_ok != exp_meta.get("attempt_ok"):
                return (1, f"{step_id}: expected attempt_ok={exp_meta.get('attempt_ok')!r} (got {attempt_ok!r})")

        # Assert the HARNESS's own determination, not just the observation.
        # `predict` pins libsandbox's userland verdict (sandbox_check.outcome);
        # `drift` pins how the harness reconciled that prediction with the
        # kernel observation. Before this, the menagerie checked attempt_ok vs
        # the author's `policy` model but never the harness's drift field — so a
        # broken drift computation (e.g. hard-wired False, or a false-positive
        # True on an ambiguous EPERM) would have passed green. `drift` is
        # tri-state, so we test key-presence (None is a real expected value,
        # distinct from "unspecified").
        if "predict" in exp_meta:
            if sb.get("outcome") != exp_meta["predict"]:
                return (1, f"{step_id}: expected sandbox_check.outcome={exp_meta['predict']!r} (got {sb.get('outcome')!r})")
        if "drift" in exp_meta:
            if step.get("drift") != exp_meta["drift"]:
                return (1, f"{step_id}: expected drift={exp_meta['drift']!r} (got {step.get('drift')!r})")

        if exp_attempt.get("kind") == "file":
            expected_target = exp_attempt.get("target")
            if expected_target and attempt.get("requested_path") != expected_target:
                return (
                    1,
                    f"{step_id}: expected requested_path={expected_target!r} (got {attempt.get('requested_path')!r})",
                )
            if not attempt_ok and attempt.get("syscall_errno") is None:
                return (1, f"{step_id}: expected syscall_errno on failed file attempt")
            if attempt_ok and attempt.get("syscall_errno") is not None:
                return (1, f"{step_id}: unexpected syscall_errno on successful file attempt")
            if attempt_ok and exp_attempt.get("action") in ("open_read", "open_write", "create"):
                if attempt.get("observed_path") is None:
                    return (1, f"{step_id}: expected observed_path for successful open/create")

        if "errno" in exp_meta and exp_meta.get("errno") is not None:
            got_errno = attempt.get("syscall_errno", attempt.get("errno"))
            if got_errno != exp_meta.get("errno"):
                return (
                    1,
                    f"{step_id}: expected errno={exp_meta.get('errno')!r} (got {got_errno!r})",
                )

        policy = exp_meta.get("policy")
        mismatch_reason = exp_meta.get("mismatch_reason")
        if policy in ("allow", "deny"):
            policy_allows = policy == "allow"
            policy_match = (policy_allows == attempt_ok)
            if mismatch_reason:
                if policy_match:
                    return (3, f"{step_id}: expected mismatch ({mismatch_reason}) not observed")
                mismatch_notes.append(f"{step_id}:{mismatch_reason}")
            else:
                if not policy_match:
                    return (1, f"{step_id}: policy={policy} but attempt_ok={attempt_ok}")

    if mismatch_notes:
        note = ", ".join(mismatch_notes)
        return (0, f"ok (mismatch evidence: {note})")

    return (0, "ok")


def apply_runner_selector(specimen):
    mode = os.environ.get("PW_TEST_RUNNER_MODE") or ""
    service = os.environ.get("PW_TEST_RUNNER_SERVICE") or ""
    if not mode and not service:
        return
    runner = specimen.get("runner") or {}
    if mode:
        runner["mode"] = mode
    if service:
        runner["service"] = service
    if runner:
        specimen["runner"] = runner


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--case", dest="case_id", required=True)
    parser.add_argument("--artifacts", required=True)
    parser.add_argument("--fixtures", required=True)
    parser.add_argument("--pw-bin", required=True)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    fixtures_root = Path(args.fixtures)
    artifacts_dir = Path(args.artifacts)
    pw_bin = Path(args.pw_bin)

    case = resolve_case(args.case_id, manifest_path)

    run_id = os.environ.get("PW_TEST_RUN_ID", "unknown")
    mapping = compute_roots(case, run_id)

    case_vars = substitute(case.get("vars") or {}, mapping)
    mapping.update(case_vars)

    for file_spec in case.get("files") or []:
        path = substitute(file_spec.get("path"), mapping)
        content = substitute(file_spec.get("content", ""), mapping)
        write_file(Path(path), content)

    policy = case.get("policy") or {}
    policy_format = policy.get("format")
    if policy_format == "sbpl":
        sbpl_path = fixtures_root / policy.get("sbpl_path", "")
        if not sbpl_path.exists():
            raise SystemExit(f"missing sbpl_path: {sbpl_path}")
        sbpl = load_sbpl(sbpl_path, case.get("sbpl_replacements"), mapping)
        params = substitute(policy.get("params") or {}, mapping)
        policy_spec = {"format": "sbpl", "sbpl_source": sbpl}
        if params:
            policy_spec["params"] = params
    else:
        raise SystemExit(f"unknown policy.format: {policy_format!r}")

    steps = substitute(case.get("steps") or [], mapping)
    specimen = {
        "schema_version": 1,
        "specimen_id": case["case_id"],
        "policy": policy_spec,
        "probe_plan": steps,
    }
    apply_runner_selector(specimen)

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    specimen_path = artifacts_dir / "specimen.rendered.json"
    stdout_path = artifacts_dir / "policy_witness.run.stdout.json"
    stderr_path = artifacts_dir / "policy_witness.run.stderr.txt"
    specimen_path.write_text(json.dumps(specimen, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if not pw_bin.exists() or not os.access(pw_bin, os.X_OK):
        print(f"missing policy-witness binary at {pw_bin}")
        return 3

    rc = run_policy_witness(pw_bin, specimen_path, stdout_path, stderr_path)
    if rc != 0:
        print(f"policy-witness run failed (rc={rc})")
        return 1

    run_data = load_run_json(stdout_path)
    status, message = validate_run(steps, run_data)
    expected_kind = os.environ.get("PW_TEST_RUNNER_EXPECT_KIND")
    if expected_kind:
        actual_kind = (run_data.get("data") or {}).get("runner_provenance", {}).get("runner_kind")
        if actual_kind != expected_kind:
            print(f"expected runner_kind={expected_kind!r} (got {actual_kind!r})")
            return 1
    print(message)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
