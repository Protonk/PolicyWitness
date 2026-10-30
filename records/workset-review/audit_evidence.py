"""Read retained workset evidence without executing tests or changing old output.

Run from the repository root with Python 3. Writes only this review's audit.json.
This checks account consistency and identities, not semantic dependency closure.
"""
import collections
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests/out"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main():
    findings = []
    runs = {}
    for pin in read(ROOT / "tests/RETAINED.json")["runs"]:
        path = OUT / pin["path"]
        if not (path / "run.json").is_file():
            # Archived release acceptance has its own format.
            owner = read(path / "owner.json")
            findings.append({"path": pin["path"], "direct_run": False,
                             "exists": path.exists(), "run_id": owner["run_id"],
                             "pin_id_matches": owner["run_id"] == pin["run_id"],
                             "owner_sha256": sha(path / "owner.json")})
            continue
        run = read(path / "run.json")
        runs[pin["path"]] = run
        findings.append({"path": pin["path"], "run_id": run["run_id"],
                         "pin_id_matches": run["run_id"] == pin["run_id"],
                         "counts": run["counts"], "completion": run["completion"],
                         "run_json_sha256": sha(path / "run.json"),
                         "failures": [r["id"] for r in run["case_results"] if r["status"] == "fail"]})

    credit_path = OUT / "runs/workset-final-retirement-01/combined-acceptance-credit.json"
    credit = read(credit_path)
    errors = []
    checked = []
    for row in credit["cases"] + [credit["additional_caller_auth"]]:
        path = OUT / row["run"]
        run = runs[row["run"]]
        matches = [r for r in run["case_results"] if r["id"] == row["id"]]
        plan = read(path / "plan.json")
        selected = [r for r in plan["cases"] if r["id"] == row["id"]]
        issues = []
        if run["run_id"] != row["run_id"]: issues.append("run ID mismatch")
        if len(matches) != 1 or matches[0]["status"] != "pass" or matches[0]["state"] != "completed":
            issues.append("not a unique completed pass")
        if len(selected) != 1: issues.append("not uniquely selected")
        if matches and matches[0].get("system_sleep_ms") != 0: issues.append("sleep not zero")
        suite, test_id = row["id"].split("/", 1)
        report_path = path / "suites" / suite / test_id / "report.json"
        report = read(report_path)
        if report["status"] != "pass" or report["suite"] != suite or report["test_id"] != test_id:
            issues.append("individual report mismatch")
        invocations = [i for i in run["invocations"] if any(r["id"] == row["id"] for r in i["case_results"])]
        if len(invocations) != 1 or invocations[0]["returncode"] != 0 or invocations[0]["harness_errors"]:
            issues.append("invocation failed or has harness errors")
        if issues: errors.append({"case": row["id"], "issues": issues})
        checked.append({"id": row["id"], "run": row["run"], "report_sha256": sha(report_path),
                        "credit": row.get("credit", "separate_caller_auth")})
    ids = [c["id"] for c in credit["cases"]]
    plan = read(OUT / "runs/f2-reservation-final-01/plan.json")
    plan_ids = {c["id"] for c in plan["cases"]}
    if len(ids) != len(set(ids)): errors.append("duplicate credits")
    if set(ids) != plan_ids: errors.append("credit/full-selection mismatch")

    inventory_path = OUT / "runs/f2-reservation-final-01/artifact-integrity/before.json"
    inventory = read(inventory_path)
    app = ROOT / "dist/PolicyWitness.app"
    inventory_errors = []
    actual_names = {"."} | {str(p.relative_to(app)) for p in app.rglob("*")}
    if actual_names != set(inventory):
        inventory_errors.append({"extra": sorted(actual_names - set(inventory)),
                                 "missing": sorted(set(inventory) - actual_names)})
    for name, entry in inventory.items():
        path = app / name
        if not path.exists(): inventory_errors.append([name, "absent"]); continue
        if path.lstat().st_mode != entry["mode"]: inventory_errors.append([name, "mode"])
        if "sha256" in entry and sha(path) != entry["sha256"]: inventory_errors.append([name, "hash"])
    inventory_equal = {}
    for name in ["f2-reservation-final-01", "f2-reservation-replacements-01", "f2-native-route-04"]:
        for when in ["before", "after"]:
            p = OUT / "runs" / name / "artifact-integrity" / (when + ".json")
            inventory_equal[name + "/" + when] = p.read_bytes() == inventory_path.read_bytes()

    flow_before = git("show", "4407d0ae:controller/src/run_flow.rs").split(b"#[cfg(test)]", 1)[0]
    flow_after = git("show", "8500baff:controller/src/run_flow.rs").split(b"#[cfg(test)]", 1)[0]
    frozen = git("show", "0c22d256:records/workset/pytest-first.md")
    c0_final = git("show", "67fff425:records/workset/pytest-first.md")
    result = {
        "endpoint": git("rev-parse", "HEAD").decode().strip(),
        "retained_runs": findings, "credit_errors": errors,
        "credit_counts": dict(collections.Counter(c["credit"] for c in credit["cases"])),
        "distinct_required": len(set(ids)), "same_as_final_selection": set(ids) == plan_ids,
        "full_selection_defaults": sum(c["default"] for c in plan["cases"]),
        "full_selection_byoxpc": sum(c["suite"] == "runner_byoxpc" for c in plan["cases"]),
        "checked_cases": checked,
        "app_inventory_sha256": sha(inventory_path), "historical_inventory_equality": inventory_equal,
        "current_app_inventory_errors": inventory_errors,
        "production_run_flow_prefix_equal": flow_before == flow_after,
        "frozen_counterfactual_equal": frozen == c0_final,
        "frozen_counterfactual_sha256": hashlib.sha256(frozen).hexdigest(),
        "limitations": ["Does not infer complete dependencies or semantic correctness from file identity.",
                        "Does not execute native operations, tests, signing verification or cleanup."]}
    (Path(__file__).parent / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ["retained_runs", "checked_cases"]}, indent=2))


if __name__ == "__main__":
    main()
