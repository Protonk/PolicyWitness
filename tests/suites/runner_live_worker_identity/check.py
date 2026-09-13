"""Compare an independent live observation to the final production envelope."""
import json
from pathlib import Path
import secrets
import select
import subprocess
import sys
import tempfile


def main():
    pw, out_arg, observer_arg = sys.argv[1:]
    out, observer_bin = Path(out_arg).resolve(), str(Path(observer_arg).resolve())
    with tempfile.TemporaryDirectory(prefix="pw-live-", dir="/private/tmp") as work:
        socket_path = str(Path(work) / "rendezvous")
        allowed, denied = [Path(work) / secrets.token_hex(8) for _ in range(2)]
        for path in (allowed, denied):
            path.write_bytes(secrets.token_bytes(32))
        spec = {
            "schema_version": 1,
            "specimen_id": "live_worker_identity",
            "policy": {"format": "sbpl", "sbpl_source":
                       '(version 1)(allow default)(deny file-read-data (literal (param "TARGET")))',
                       "params": {"TARGET": str(denied)}},
            "probe_plan": [{
                "step_id": name,
                "sandbox_check": {"operation": "file-read-data",
                                  "filter": {"kind": "path", "value": str(path)}},
                "attempt": {"kind": "file", "action": "open_read", "target": str(path)},
            } for name, path in (("allowed", allowed), ("denied", denied))] + [{
                "step_id": "hold",
                "sandbox_check": {"operation": "process-exec*",
                                  "filter": {"kind": "path", "value": observer_bin}},
                "attempt": {"kind": "exec", "action": "spawn", "target": observer_bin,
                            "args": ["--hold", socket_path]},
            }],
        }
        request = out / "specimen.json"
        request.write_text(json.dumps(spec, indent=2) + "\n")
        with (out / "observer.stderr").open("w") as observer_err, \
                (out / "run.json").open("w") as pw_out, (out / "pw.stderr").open("w") as pw_err:
            observer = subprocess.Popen([observer_bin, "--observe", socket_path, str(allowed), str(denied)],
                                        stdout=subprocess.PIPE, stderr=observer_err, text=True)
            run = None
            try:
                ready, _, _ = select.select([observer.stdout], [], [], 5)
                assert ready and observer.stdout.readline() == "ready\n", "observer did not become ready"
                run = subprocess.Popen([pw, "run", str(request), "--no-log-capture"],
                                       stdout=pw_out, stderr=pw_err)
                observed, _ = observer.communicate(timeout=10)
                (out / "observer.json").write_text(observed)
                assert observer.returncode == 0, "observer failed; see observer.stderr"
                assert run.wait(timeout=15) == 0, "PW failed; see run.json and pw.stderr"
            finally:
                # The helper has its own seven-second deadline, including when
                # the client/observer fails. Never leave an unbounded hold alive.
                for child in (observer, run):
                    if child is not None and child.poll() is None:
                        child.kill()
                        child.wait()

    actual = json.loads((out / "observer.json").read_text())
    worker_pid, host_pid = actual["worker"]["pid"], actual["host"]["pid"]
    assert len({actual["helper"]["pid"], worker_pid, host_pid}) == 3
    assert actual["helper"]["ppid"] == worker_pid and actual["worker"]["ppid"] == host_pid
    assert actual["worker_checks"]["allowed_rc"] == 0
    assert actual["worker_checks"]["denied_rc"] > 0, actual
    assert actual["host_checks"]["allowed_rc"] == actual["host_checks"]["denied_rc"] == 0, actual
    envelope = json.loads((out / "run.json").read_text())
    assert envelope["result"]["ok"] is True
    runner = envelope["data"]["runner_result"]
    assert runner["normalized_outcome"] == "ok" and runner.get("test_overrides") is None
    assert runner["pid"] == runner["runner_subprocess"]["pid"] == worker_pid
    assert runner["runner_subprocess"]["exit_code"] == 0
    assert len(runner["steps"]) == 3
    steps = {s["step_id"]: s for s in runner["steps"]}
    assert set(steps) == {"allowed", "denied", "hold"}
    for step in steps.values():
        assert step["sandbox_check"]["pid"] == worker_pid
    for name, verdict in (("allowed", "allow"), ("denied", "deny")):
        check = steps[name]["sandbox_check"]
        assert check["outcome"] == verdict
        assert check["rc"] == actual["worker_checks"][f"{name}_rc"]
    assert steps["allowed"]["attempt"]["outcome"] == "ok"
    assert steps["denied"]["attempt"]["outcome"] == "open_failed"
    assert steps["denied"]["attempt"]["errno"] in (1, 13)
    hold = steps["hold"]["attempt"]
    assert hold["child_pid"] == actual["helper"]["pid"]
    assert hold["outcome"] == "ok" and hold["stdout"] == "released\n"
    print(f"OS-observed worker {worker_pid} denies the target; host {host_pid} allows it; PW agrees")


if __name__ == "__main__":
    main()
