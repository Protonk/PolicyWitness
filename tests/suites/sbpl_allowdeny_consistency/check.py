"""Observe file effects outside PW, with the probe plan fixed across two runs."""
import copy
import json
from pathlib import Path
import secrets
import subprocess
import sys


def main():
    pw, out_arg, fixture_arg = sys.argv[1:]
    out, fixture = Path(out_arg).resolve(), Path(fixture_arg)
    spec = json.loads((fixture / "specimen.template.json").read_text())
    spec["policy"]["sbpl_source"] = (fixture / "profile.sbpl").read_text()
    paths = []
    for _ in range(2):
        directory = out / secrets.token_hex(8)
        directory.mkdir()
        paths.append(directory / secrets.token_hex(8))

    file_steps = [s for s in spec["probe_plan"] if s["attempt"]["kind"] == "file"]
    assert len(file_steps) == 2
    for step, path in zip(file_steps, paths):
        step["attempt"]["target"] = str(path)
        step["sandbox_check"]["filter"]["value"] = str(path)
    # Neither target names nor step IDs encode the expected decision.
    for step in spec["probe_plan"]:
        step["step_id"] = secrets.token_hex(8)
    fixed_plan = copy.deepcopy(spec["probe_plan"])

    for round_number, allowed_index in enumerate((0, 1)):
        denied_index = 1 - allowed_index
        seeds = [secrets.token_bytes(64) for _ in paths]
        for i, (path, seed) in enumerate(zip(paths, seeds)):
            path.write_bytes(seed)
            (out / f"round{round_number}.file{i}.before").write_bytes(seed)
        spec["policy"]["params"] = {
            "ALLOW_WRITE_DIR": str(paths[allowed_index].parent),
            "DENY_WRITE_DIR": str(paths[denied_index].parent),
        }
        assert spec["probe_plan"] == fixed_plan
        request = out / f"round{round_number}.specimen.json"
        request.write_text(json.dumps(spec, indent=2) + "\n")
        with (out / f"round{round_number}.run.json").open("w") as stdout, \
                (out / f"round{round_number}.stderr").open("w") as stderr:
            run = subprocess.run([pw, "run", str(request), "--no-log-capture"],
                                 stdout=stdout, stderr=stderr, timeout=20)

        # Read and preserve the external evidence before consulting PW's report.
        after = [path.read_bytes() for path in paths]
        for i, data in enumerate(after):
            (out / f"round{round_number}.file{i}.after").write_bytes(data)
        assert after[allowed_index] and after[allowed_index] != seeds[allowed_index], \
            f"round {round_number}: allowed write did not leave changed, nonempty data"
        assert after[denied_index] == seeds[denied_index], \
            f"round {round_number}: denied write changed the file"
        assert run.returncode == 0, f"PW exit={run.returncode}; see round{round_number}.run.json"
        envelope = json.loads((out / f"round{round_number}.run.json").read_text())
        assert envelope["kind"] == "run" and envelope["result"]["ok"] is True
        runner = envelope["data"]["runner_result"]
        assert runner["normalized_outcome"] == "ok"
        assert runner["policy_format"] == "sbpl"
        assert runner["sandboxed_after_apply"] is True
        assert runner.get("test_overrides") is None
        assert len(runner["steps"]) == len(fixed_plan) == 4
        by_id = {s["step_id"]: s for s in runner["steps"]}
        assert set(by_id) == {s["step_id"] for s in fixed_plan}
        # The fixture retains its two Mach steps; this test's external oracle
        # covers file writes, not Mach service liveness.
        for i, planned in enumerate(file_steps):
            step = by_id[planned["step_id"]]
            attempt = step["attempt"]
            assert attempt["requested_path"] == str(paths[i])
            assert "normalized_path" in attempt and "observed_path" in attempt
            if i == allowed_index:
                assert step["sandbox_check"]["outcome"] == "allow"
                assert attempt["exit_code"] == 0 and attempt["syscall_errno"] is None
                assert step["deny_signal"]["delta"] == 0
            else:
                assert step["sandbox_check"]["outcome"] == "deny"
                assert attempt["exit_code"] != 0 and attempt["syscall_errno"] in (1, 13)
        print(f"round {round_number}: external bytes and reported decisions agree")


if __name__ == "__main__":
    main()
