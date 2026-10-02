"""Independent process/pipe observations at exec lifecycle boundaries."""
import json
import os
from pathlib import Path
import secrets
import signal
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'fixtures/exec'))
from control import TreeControl, ExitObserver, process_snapshot
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import consumer
from run_capture import RunCapture


def main():
    pw, directory, helper, mode = sys.argv[1:]
    out = Path(directory)
    with tempfile.TemporaryDirectory(prefix='pw-exec-edge-', dir='/private/tmp') as work:
        root = Path(work)
        control = TreeControl(root / 'control')
        worker_observer = ExitObserver()
        seed = secrets.token_bytes(64)
        before, after = root / 'before', root / 'after'
        for path in (before, after): path.write_bytes(seed)
        def write_step(name, target):
            return dict(step_id=name, sandbox_check=dict(operation='file-write-data',
                filter=dict(kind='path', value=str(target))),
                attempt=dict(kind='file', action='open_write', target=str(target)))
        request = dict(schema_version=1, specimen_id=mode,
            policy=dict(format='sbpl', sbpl_source='(version 1)(allow default)'), probe_plan=[
                write_step('before', before),
                dict(step_id='exec', sandbox_check=dict(operation='process-exec*',
                    filter=dict(kind='path', value=helper)),
                    attempt=dict(kind='exec', action='spawn', target=helper, args=['--tree', control.path])),
                write_step('after', after)])
        run = RunCapture(pw, out, request, cli_args=['--no-log-capture', '--timeout-ms', '30000'])
        try:
            run.start()
            pids = control.accept()
            groups = {role: os.getpgid(pid) for role, pid in pids.items()}
            assert groups['P'] == groups['C'] == pids['P'], groups
            control.assert_running()
            if mode == 'closed_streams_continue':
                for role in ('P', 'C'): control.close_streams(role)
                # EOF is already acknowledged by each writer. The worker must
                # permit both to continue doing work before their natural exit.
                time.sleep(0.3)
                control.assert_running()
                control.release()
            elif mode == 'leader_exit_descendant':
                control.exit_leader()
                assert pids['C'] not in control.exits()
            elif mode == 'worker_dies_during_exec':
                peer = process_snapshot(helper, pids['P'])
                worker = process_snapshot(helper, peer['ppid'])
                assert Path(worker['path']).name == 'pw-probe-runner', worker
                # The live socket peer plus its observed parent establish this
                # test's worker ownership; no PID comes from PW's output.
                worker_observer.watch(worker['pid'])
                os.kill(worker['pid'], signal.SIGKILL)
                worker_observer.assert_stopped()
                (out / 'worker.json').write_text(json.dumps(worker, indent=2))
            else:
                raise AssertionError(mode)
            rc = run.wait(timeout=25)
            if mode == 'worker_dies_during_exec':
                control.assert_running()  # absence of slot publication is not proof of no spawn
            else:
                control.assert_stopped()
            assert before.read_bytes() != seed
            assert (after.read_bytes() == seed) == (mode == 'worker_dies_during_exec')
            (out / 'observations.json').write_text(json.dumps(dict(pids=pids, groups=groups,
                exited=sorted(control.exited), elapsed=run.elapsed_seconds), indent=2))
            envelope = run.load_json()
            assert not consumer.validate(envelope), consumer.validate(envelope)
            runner = envelope['data']['runner_result']
            first, middle, last = runner['steps']
            assert first['attempt']['outcome'] == 'ok'
            attempt = middle['attempt']
            if mode == 'worker_dies_during_exec':
                assert rc != 0 and runner['normalized_outcome'] == 'runner_failed', runner['normalized_outcome']
                assert runner['runner_subprocess']['term_signal'] == signal.SIGKILL
                for step in (middle, last):
                    assert step['attempt']['outcome'] == 'not_run_worker_died', step
                    for field in ('child_pid', 'child_exit_code', 'child_term_signal'):
                        assert step['attempt'].get(field) is None, step
                    assert step['comparison']['observation'] == 'unavailable', step
                    assert step['comparison']['observation_basis'] == 'no_completed_worker_result', step
                assert runner['runner_subprocess']['partial_steps'] is True
            else:
                assert rc == 0 and runner['normalized_outcome'] == 'ok'
                assert last['attempt']['outcome'] == 'ok'
                assert attempt['child_pid'] == pids['P'] and attempt['child_exit_code'] == 0
                assert attempt['child_term_signal'] == 0
                assert attempt['stdout'] == 'exec_fixture: hello from helper\n'
                assert attempt['outcome'] == ('ok' if mode == 'closed_streams_continue' else 'exec_failed')
                if mode == 'leader_exit_descendant':
                    assert 'deadline' in attempt['error']
                    # The helper spawned: the record observes the spawn and nothing
                    # about the sandbox for the deadline that followed.
                    assert middle['comparison']['observation_basis'] == 'spawned_child', middle['comparison']
                    assert middle['comparison']['limitations'] == [], middle['comparison']
            print(f'{mode}: independent pipe/exit/effect observations match retained evidence')
        finally:
            try: control.close()
            finally:
                worker_observer.close()
                run.close()


if __name__ == '__main__':
    main()
