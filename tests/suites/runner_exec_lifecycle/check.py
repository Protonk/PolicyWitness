"""CLI contract: bounded exec cleanup, retained output, and plan continuation."""
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "fixtures" / "exec"))
from control import TreeControl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
from run_capture import RunCapture


def main():
    pw, out_arg, helper_arg = sys.argv[1:]
    out, helper = Path(out_arg).resolve(), str(Path(helper_arg).resolve())
    with tempfile.TemporaryDirectory(prefix="pw-exec-tree-", dir="/private/tmp") as work:
        control = TreeControl(Path(work) / "control")
        target = Path(work) / "after"
        seed = secrets.token_bytes(64)
        target.write_bytes(seed)
        (out / "before.bin").write_bytes(seed)
        stderr_marker = secrets.token_hex(16)
        spec = {
            "schema_version": 1,
            "specimen_id": "exec_timeout_continuation",
            "policy": {"format": "sbpl", "sbpl_source": "(version 1)(allow default)"},
            "probe_plan": [{
                "step_id": "hang",
                "sandbox_check": {"operation": "process-exec*",
                                  "filter": {"kind": "path", "value": helper}},
                "attempt": {"kind": "exec", "action": "spawn", "target": helper,
                            "args": ["--stderr", stderr_marker, "--tree", control.path]},
            }, {
                "step_id": "after",
                "sandbox_check": {"operation": "file-write-data",
                                  "filter": {"kind": "path", "value": str(target)}},
                "attempt": {"kind": "file", "action": "open_write", "target": str(target)},
            }],
        }
        run = RunCapture(pw, out, spec, cli_args=['--no-log-capture', '--timeout-ms', '30000'])
        try:
            run.start()
            pids = control.accept()
            # The fixture does not establish its own process group. Observe
            # PW's isolation before either process can exit.
            groups = {role: os.getpgid(pid) for role, pid in pids.items()}
            assert groups['P'] == groups['C'] == pids['P'], (pids, groups)
            (out / "started.json").write_text(json.dumps({'pids': pids, 'groups': groups}, indent=2))
            rc = run.wait(timeout=25)
            elapsed = run.elapsed_seconds
            # Observe cleanup before closing control sockets or sending quit.
            control.assert_stopped()
            (out / "exited.json").write_text(json.dumps({'pids': sorted(control.exited),
                                                        'elapsed_seconds': elapsed}, indent=2))
            after = target.read_bytes()
            (out / "after.bin").write_bytes(after)
            assert after and after != seed, "the step after the timed-out exec did not write data"
            assert 8 <= elapsed < 25, f"expected the public 10-second exec deadline, elapsed={elapsed:.2f}s"
            assert rc == 0, f"specimen failed instead of continuing: CLI exit {rc}"
            envelope = run.load_json()
            runner = envelope['data']['runner_result']
            assert envelope['result']['ok'] is True and runner['normalized_outcome'] == 'ok'
            assert runner.get('test_overrides') is None
            assert runner['runner_subprocess']['exit_code'] == 0
            assert runner['runner_subprocess'].get('term_signal') is None
            assert runner['runner_subprocess']['partial_steps'] is False
            assert [s['step_id'] for s in runner['steps']] == ['hang', 'after']
            hang, following = runner['steps']
            attempt = hang['attempt']
            assert attempt['child_pid'] == pids['P']
            assert attempt['outcome'] == 'exec_failed' and attempt['rc'] == -1
            assert attempt['child_term_signal'] == 9 and attempt['child_exit_code'] == -1
            assert 'deadline' in attempt['error']
            assert attempt['stdout'] == 'exec_fixture: hello from helper\n'
            assert attempt['stderr'] == stderr_marker + '\n'
            assert hang['sandbox_check']['outcome'] == 'allow' and hang['drift'] is False
            assert hang['comparison']['observation_basis'] == 'spawned_child'
            assert 'exec_result_failed_after_spawn' in hang['comparison']['limitations']
            assert following['attempt']['outcome'] == 'ok'
            assert following['sandbox_check']['outcome'] == 'allow' and following['drift'] is False
            print(f"both processes stopped, output retained, later write observed; elapsed={elapsed:.2f}s")
        finally:
            try:
                control.close()
            finally:
                run.close()


if __name__ == '__main__':
    main()
