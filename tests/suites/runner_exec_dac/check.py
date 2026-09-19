"""The OS permission control supplies the oracle; PW's classifier does not."""
import errno
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from run_capture import RunCapture


def main():
    pw, out_arg = sys.argv[1:]
    out = Path(out_arg).resolve()
    records = {}
    with tempfile.TemporaryDirectory(prefix="pw-exec-dac-", dir="/private/tmp") as work:
        helper = Path(work) / "helper"
        shutil.copyfile("/usr/bin/true", helper)
        spec = {
            "schema_version": 1,
            "specimen_id": "execute_permission_control",
            "policy": {"format": "sbpl", "sbpl_source": "(version 1)(allow default)"},
            "probe_plan": [{
                "step_id": "exec",
                "sandbox_check": {"operation": "process-exec*",
                                  "filter": {"kind": "path", "value": str(helper)}},
                "attempt": {"kind": "exec", "action": "spawn", "target": str(helper)},
            }],
        }
        # Complete BOTH controls before asserting drift, so the known defect
        # cannot prevent the restored-permission case from being exercised.
        for name, mode in (("nonexecutable", 0o644), ("executable", 0o755), ("deny_prediction_dac", 0o644)):
            helper.chmod(mode)
            if name == "deny_prediction_dac":
                # Deny a separate submitted query while leaving the attempted
                # helper allowed by SBPL. DAC is independently observed below.
                query = Path(work) / "denied-query"
                shutil.copyfile("/usr/bin/true", query)
                spec["policy"]["sbpl_source"] = '(version 1)(allow default)(deny process-exec* (literal "' + str(query) + '"))'
                spec["probe_plan"][0]["sandbox_check"]["filter"]["value"] = str(query)
            try:
                direct_run = subprocess.run([str(helper)], capture_output=True, timeout=5)
                direct = {"spawned": True, "exit_code": direct_run.returncode}
            except OSError as exc:
                direct = {"spawned": False, "errno": exc.errno}
            (out / f"{name}.direct.json").write_text(json.dumps(direct, indent=2) + "\n")
            with RunCapture(pw, out / name, spec, cli_args=['--no-log-capture']) as run:
                records[name] = (direct, run.wait(timeout=20), run.load_json())

    steps = {}
    for name, (direct, rc, envelope) in records.items():
        assert rc == 0 and envelope["result"]["ok"] is True, (name, rc, envelope)
        runner = envelope["data"]["runner_result"]
        assert runner["normalized_outcome"] == "ok"
        assert runner.get("test_overrides") is None
        assert len(runner["steps"]) == 1
        step = runner["steps"][0]
        assert step["step_id"] == "exec"
        assert step["sandbox_check"]["outcome"] == ("deny" if name == "deny_prediction_dac" else "allow"), (name, step)
        steps[name] = step

    assert records["nonexecutable"][0] == {"spawned": False, "errno": errno.EACCES}
    assert records["executable"][0] == {"spawned": True, "exit_code": 0}
    assert records["deny_prediction_dac"][0] == {"spawned": False, "errno": errno.EACCES}
    denied = steps["deny_prediction_dac"]
    assert denied["attempt"]["errno"] == errno.EACCES and denied["attempt"]["outcome"] == "exec_failed", denied
    assert denied["drift"] is None and denied["deny_signal"] is None, denied
    failure = steps["nonexecutable"]["attempt"]
    assert failure["outcome"] == "exec_failed" and failure["rc"] == -1
    assert failure["child_pid"] == 0 and failure["child_exit_code"] == -1
    assert failure["child_term_signal"] == 0
    assert failure["errno"] == failure["syscall_errno"] == errno.EACCES
    assert "posix_spawn" in failure["error"]
    success = steps["executable"]["attempt"]
    assert success["outcome"] == "ok" and success["rc"] == 0
    assert success["child_pid"] > 0 and success["child_exit_code"] == 0
    assert success["child_term_signal"] == 0
    assert steps["executable"]["drift"] is None
    print("direct OS and PW controls agree: removing execute bits blocks spawn; restoring them succeeds",
          flush=True)
    assert steps["nonexecutable"]["drift"] is None, \
        ("ordinary execute-permission EACCES must yield drift=null, got "
         f"{steps['nonexecutable']['drift']!r}; allow-all policy and direct OS control rule out "
         "using this errno alone as evidence of sandbox drift")


if __name__ == "__main__":
    main()
