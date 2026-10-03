"""The OS permission control supplies the oracle; PW's classifier does not."""
import errno
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import consumer
from run_capture import RunCapture


def main():
    pw, out_arg = sys.argv[1:]
    out = Path(out_arg).resolve()
    records = {}
    with tempfile.TemporaryDirectory(prefix="pw-exec-dac-", dir="/private/tmp") as work:
        helper = Path(work) / "helper"
        shutil.copyfile("/usr/bin/true", helper)
        spec = {
            "schema_version": 4,
            "specimen_id": "execute_permission_control",
            "policy": {"format": "sbpl", "sbpl_source": "(version 1)(allow default)"},
            "probe_plan": [{
                "step_id": "exec",
                "sandbox_check": {"operation": "process-exec*",
                                  "filter": {"kind": "path", "value": str(helper)}},
                "attempt": {"kind": "exec", "action": "spawn", "target": str(helper)},
            }],
        }
        # Complete BOTH controls before asserting the records, so a classifier
        # defect cannot prevent the restored-permission case from being exercised.
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
        assert not consumer.validate(envelope), (name, consumer.validate(envelope))
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
    # The denied query names another target: the record relates the two
    # submitted targets and observes the permission failure by errno.
    assert denied["comparison"]["target_relation"] == "different_submitted", denied["comparison"]
    assert (denied["comparison"]["observation"], denied["comparison"]["observation_basis"]) == ("permission_failure", "permission_errno"), denied
    failure = steps["nonexecutable"]["attempt"]
    assert failure["outcome"] == "exec_failed" and failure["rc"] == -1
    assert failure["child_pid"] == 0 and failure["child_exit_code"] == -1
    assert failure["child_term_signal"] == 0
    assert failure["errno"] == errno.EACCES and "syscall_errno" not in failure
    assert "posix_spawn" in failure["error"]
    success = steps["executable"]["attempt"]
    assert success["outcome"] == "ok" and success["rc"] == 0
    assert success["child_pid"] > 0 and success["child_exit_code"] == 0
    assert success["child_term_signal"] == 0
    assert (steps["executable"]["comparison"]["observation"], steps["executable"]["comparison"]["observation_basis"]) == ("succeeded", "spawned_child")
    print("direct OS and PW controls agree: removing execute bits blocks spawn; restoring them succeeds",
          flush=True)
    # Ordinary execute-permission EACCES is a permission failure observed by
    # errno against an allow-all policy and a matching query: the record says
    # exactly that and attributes nothing to the sandbox.
    record = steps["nonexecutable"]["comparison"]
    assert record == {"observation": "permission_failure", "observation_basis": "permission_errno",
                      "operation_relation": "matched", "target_relation": "same_submitted",
                      "order": "query_first", "limitations": []}, record


if __name__ == "__main__":
    main()
