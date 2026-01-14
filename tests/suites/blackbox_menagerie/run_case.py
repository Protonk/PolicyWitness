#!/usr/bin/env python3
import argparse
import base64
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


def validate_run(case, run_data):
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
    expected_steps = case.get("steps") or []
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

        attempt_ok = attempt.get("rc") == 0
        exp_meta = exp.get("expect") or {}

        if "attempt_ok" in exp_meta:
            if attempt_ok != exp_meta.get("attempt_ok"):
                return (1, f"{step_id}: expected attempt_ok={exp_meta.get('attempt_ok')!r} (got {attempt_ok!r})")

        if "errno" in exp_meta and exp_meta.get("errno") is not None:
            if attempt.get("errno") != exp_meta.get("errno"):
                return (1, f"{step_id}: expected errno={exp_meta.get('errno')!r} (got {attempt.get('errno')!r})")

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
    elif policy_format == "compiled_bytes":
        blob_path = fixtures_root / policy.get("compiled_blob_path", "")
        if not blob_path.exists():
            raise SystemExit(f"missing compiled_blob_path: {blob_path}")
        data = blob_path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        policy_spec = {"format": "compiled_bytes", "compiled_profile_b64": b64}
    else:
        raise SystemExit(f"unknown policy.format: {policy_format!r}")

    steps = substitute(case.get("steps") or [], mapping)
    specimen = {
        "schema_version": 1,
        "specimen_id": case["case_id"],
        "policy": policy_spec,
        "probe_plan": steps,
    }

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
        err_text = stderr_path.read_text(encoding="utf-8", errors="ignore")
        if policy_format == "compiled_bytes":
            if "sandbox_register_profile failed" in err_text or "sandbox_apply failed: Operation not permitted" in err_text:
                print("compiled profile registration not permitted on this host")
                return 3
            try:
                run_data = load_run_json(stdout_path)
            except SystemExit:
                run_data = None
            if isinstance(run_data, dict):
                error = (run_data.get("result") or {}).get("error") or ""
                if "sandbox_register_profile failed" in error or "sandbox_apply failed" in error:
                    print("compiled profile registration not permitted on this host")
                    return 3
        print(f"policy-witness run failed (rc={rc})")
        return 1

    run_data = load_run_json(stdout_path)
    status, message = validate_run(case, run_data)
    print(message)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
