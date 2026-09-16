"""Observe public-command cancellation through receipts and kernel exit events."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/fixtures/dispatcher'))
from repository import install_runner
from artifacts import bundle
sys.path.insert(0, str(ROOT / 'tests/fixtures/exec'))
from control import TreeControl, ExitObserver


def exercise(out, interrupt, app_guard=False):
    name = 'interrupt' if interrupt else 'release'
    if app_guard:
        name += '_artifact'
    work = out / name
    repo = work / 'fixture repo'
    install_runner(ROOT, repo, {'cancel': {'requires': ['app'] if app_guard else [], 'cases': [
        {'id': case, 'command': ['bash', 'tests/fixtures/dispatcher/cancellation.sh', case]}
        for case in ('completed', 'active', 'queued')]}}, signed_fixtures=app_guard)
    if app_guard:
        bundle(repo / 'dist/PolicyWitness.app')
    for leaf in ('cancellation.sh', 'cancellation.py'):
        relative = Path('tests/fixtures/dispatcher') / leaf
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
        target.chmod(0o755)
    child_out = repo / 'tests/out'
    receipts = work / 'receipts.jsonl'
    env = {k: v for k, v in os.environ.items() if not k.startswith('PW_')}
    env.update(PW_TEST_RUN_ID=name, PW_TEST_OUT_DIR=str(child_out),
               PYTHONDONTWRITEBYTECODE='1', CONTROL_CANCEL_RECEIPTS=str(receipts))
    observation = {'scenario': name}
    with tempfile.TemporaryDirectory(prefix='pw-cancel-', dir='/private/tmp') as socket_dir:
        tree = TreeControl(Path(socket_dir) / 'gate')
        dispatcher = ExitObserver()
        process = None
        try:
            env['CONTROL_CANCEL_SOCKET'] = tree.path
            with (work / 'stdout.txt').open('wb') as stdout, (work / 'stderr.txt').open('wb') as stderr:
                # Isolate the signal from the auditor and the enclosing suite.
                process = subprocess.Popen(['bash', str(repo / 'tests/run.sh')], cwd=work,
                                           env=env, stdout=stdout, stderr=stderr, start_new_session=True)
                dispatcher.watch(process.pid)
                peers = tree.accept()
                tree.assert_running()
                # Confirm the equipment really survives SIGINT before asking
                # the dispatcher to stop it; a cooperative helper is too easy.
                os.kill(peers['C'], signal.SIGINT)
                tree.assert_running()
                observation['helper_survived_direct_sigint'] = True
                observation.update(dispatcher_pid=process.pid, peers=peers,
                                   process_groups={role: os.getpgid(pid) for role, pid in peers.items()})
                completed = child_out / 'suites/cancel/completed/report.json'
                prior_bytes = completed.read_bytes()
                prior_events = (child_out / 'events.jsonl').read_bytes()
                partial = child_out / 'suites/cancel/active/artifacts/partial.bin'
                assert partial.read_bytes() == b'partial observation\x00\xff\n'
                assert b'active fixture reached rendezvous' in (work / 'stdout.txt').read_bytes()
                assert [json.loads(line)['case'] for line in receipts.read_text().splitlines()] == ['completed', 'active']
                started = time.monotonic()
                if interrupt:
                    if app_guard:
                        (repo / 'dist/PolicyWitness.app/Contents/MacOS/pw-runner-client').write_bytes(b'mutated before cancellation')
                    os.killpg(process.pid, signal.SIGINT)
                else:
                    tree.release()
                observation['returncode'] = process.wait(timeout=6)
                observation['elapsed_after_action_seconds'] = time.monotonic() - started
                dispatcher.assert_stopped()
                # Check exits before fixture teardown can release or kill peers.
                tree.assert_stopped(timeout=2)
                observation['exited_peers'] = sorted(tree.exited)

            run = json.loads((child_out / 'run.json').read_text())
            if app_guard:
                assert run['artifact_integrity']['valid_before'] is True
                assert run['artifact_integrity']['unchanged'] is (not interrupt)
                delta = json.loads((child_out / 'artifact-integrity/changes.json').read_text())
                assert set(delta) == ({'Contents/MacOS/pw-runner-client'} if interrupt else set())
                if interrupt:
                    assert 'artifact_changed' in {e['code'] for e in run['harness_errors']}
            journal = json.loads((child_out / 'dispatch.json').read_text())
            assert journal['invocations'] == run['invocations']
            assert completed.read_bytes() == prior_bytes
            assert (child_out / 'events.jsonl').read_bytes().startswith(prior_events)
            assert partial.read_bytes() == b'partial observation\x00\xff\n'
            assert [case['id'] for case in run['case_results']] == ['cancel/completed', 'cancel/active', 'cancel/queued']
            executed = [json.loads(line)['case'] for line in receipts.read_text().splitlines()]
            if interrupt:
                assert observation['returncode'] != 0 and run['ok'] is False
                assert executed == ['completed', 'active'], 'queued case executed after cancellation'
                assert run['completion'] == dict(selected=3, completed=1, skipped=0, unrun=2)
                assert [case['state'] for case in run['case_results']] == ['completed', 'unrun', 'unrun']
                assert [case['reason'] for case in run['case_results'][1:]] == ['interrupted', 'interrupted']
                assert [item['state'] for item in run['invocations']] == ['exited', 'interrupted', 'blocked']
                assert run['invocations'][2]['blocked_reason'] == 'interrupted'
                assert 'interrupted' in {e['code'] for e in run['harness_errors']}
                assert not (child_out / 'suites/cancel/queued').exists()
            else:
                assert observation['returncode'] == 0 and run['ok'] is True
                assert executed == ['completed', 'active', 'queued']
                assert run['completion'] == dict(selected=3, completed=3, skipped=0, unrun=0)
            observation['ok'] = True
        except BaseException as exc:
            observation['error'] = str(exc)
            raise
        finally:
            observation['exited_before_teardown'] = sorted(tree.exits())
            (work / 'observation.json').write_text(json.dumps(observation, indent=2) + '\n')
            # Never credit this cleanup as dispatcher behavior. Release stubborn
            # peers before closing their observer, including on a failed test.
            tree.close()
            if process is not None and process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=3)
            dispatcher.close()


if __name__ == '__main__':
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    for interrupted in (False, True):
        exercise(out, interrupted)
        exercise(out, interrupted, app_guard=True)
    (out / 'controls.json').write_text(json.dumps(['release', 'interrupt', 'release_artifact', 'interrupt_artifact']) + '\n')
    print('4 cancellation controls passed')
