#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from validate_run import validate_run


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
