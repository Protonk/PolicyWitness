"""Observe the real release command CLI's deadlines, bytes, and process exits."""
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/fixtures/exec'))
from control import TreeControl, ExitObserver

WRAPPER = ROOT / 'tests/lib/release_commands.py'
FIXTURE = ROOT / 'tests/fixtures/release/hanging_command.py'
DEADLINE = 5
# Includes the wrapper's five-second interrupt grace and scheduling headroom,
# but remains well below the fixture's independent 45-second backstop.
OUTER_DEADLINE = 15


def exercise(out, name):
    work = out / name
    work.mkdir()
    evidence = work / 'commands'
    evidence.mkdir()
    receipts = work / 'invocations.jsonl'
    config_path = work / 'fixture.json'
    stdout_bytes = b'{"partial": "' + secrets.token_hex(16).encode() + b'\x00\xff'
    stderr_bytes = b'pending response\r\n\x00\xfe' + secrets.token_bytes(32)
    argv = ['/usr/bin/python3', '-B', str(FIXTURE), str(config_path), 'literal ; $() " argument']
    env = {k: v for k, v in os.environ.items() if not k.startswith('PW_')}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    observation = dict(scenario=name)
    with tempfile.TemporaryDirectory(prefix='pw-release-deadline-', dir='/private/tmp') as temporary:
        tree = TreeControl(Path(temporary) / 'gate')
        wrapper = ExitObserver()
        process = None
        try:
            config_path.write_text(json.dumps(dict(socket=tree.path, receipts=str(receipts),
                stdout_hex=stdout_bytes.hex(), stderr_hex=stderr_bytes.hex(),
                parent_exits_on_interrupt=name == 'parent_exits')) + '\n')
            started = time.monotonic()
            with (work / 'wrapper.stdout').open('wb') as stdout, (work / 'wrapper.stderr').open('wb') as stderr:
                process = subprocess.Popen(['/usr/bin/python3', '-B', str(WRAPPER),
                    str(evidence), str(DEADLINE), *argv], env=env,
                    stdout=stdout, stderr=stderr, start_new_session=True)
                wrapper.watch(process.pid)
                peers = tree.accept(timeout=DEADLINE)
                tree.assert_running()
                # Prove the test equipment resists SIGINT before relying on it
                # to distinguish interruption from actual forced termination.
                for role in ('C',) if name == 'parent_exits' else ('P', 'C'):
                    os.kill(peers[role], signal.SIGINT)
                tree.assert_running()
                observation.update(wrapper_pid=process.pid, peers=peers,
                                   sigint_survivors=['C'] if name == 'parent_exits' else ['P', 'C'])
                groups = {role: os.getpgid(pid) for role, pid in peers.items()}
                observation['process_groups'] = groups
                assert groups['P'] == peers['P'] == groups['C'], 'wrapper did not own the command group'
                assert groups['P'] != os.getpgid(process.pid), 'command shares wrapper process group'
                captures = list(evidence.glob('release-step-*/command'))
                assert len(captures) == 1, captures
                capture = captures[0]
                assert (capture / 'stdout').read_bytes() == stdout_bytes, 'partial stdout not flushed/captured'
                assert (capture / 'stderr').read_bytes() == stderr_bytes, 'partial stderr not flushed/captured'
                if name == 'released':
                    tree.release()
                observation['returncode'] = process.wait(timeout=max(0.01, OUTER_DEADLINE - (time.monotonic() - started)))
                observation['elapsed_seconds'] = time.monotonic() - started
                wrapper.assert_stopped()
                # All process exits must precede teardown, which can itself
                # release or kill the fixture and therefore cannot prove success.
                tree.assert_stopped(timeout=1)
                observation['exited_peers'] = sorted(tree.exited)

            invocations = [json.loads(line) for line in receipts.read_text().splitlines()]
            assert invocations == [dict(pid=peers['P'], argv=argv[3:])], 'command was retried or arguments changed'
            assert list(evidence.glob('release-step-*/command')) == captures, 'extra command captures'
            assert (capture / 'stdout').read_bytes() == stdout_bytes, 'raw stdout changed on finalization'
            assert (capture / 'stderr').read_bytes() == stderr_bytes, 'raw stderr changed on finalization'
            record = json.loads((capture / 'command.json').read_text())
            assert record['argv'] == argv and record['timeout_seconds'] == DEADLINE
            assert record['interrupted'] is False, 'deadline misattributed to user interruption'
            if name == 'released':
                assert observation['returncode'] == 0 and record['returncode'] == 0
                assert record['timed_out'] is False
            else:
                assert observation['returncode'] == 1 and record['timed_out'] is True
                assert DEADLINE <= observation['elapsed_seconds'] < OUTER_DEADLINE
                if name == 'parent_exits':
                    assert record['returncode'] == 0, 'zero exit during cleanup concealed the deadline'
                else:
                    assert type(record['returncode']) is int and record['returncode'] < 0, 'stubborn command did not terminate by signal'
                diagnostic = (work / 'wrapper.stderr').read_text()
                assert 'timed out' in diagnostic and 'remote work may still be pending' in diagnostic
            observation['ok'] = True
        except BaseException as exc:
            observation['error'] = str(exc)
            raise
        finally:
            observation['exited_before_teardown'] = sorted(tree.exits())
            (work / 'observation.json').write_text(json.dumps(observation, indent=2) + '\n')
            tree.close()
            if process is not None and process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=3)
            wrapper.close()


if __name__ == '__main__':
    out = Path(sys.argv[1]).resolve()
    cases = ['released', 'stubborn_tree', 'parent_exits']
    for name in cases:
        exercise(out, name)
    (out / 'controls.json').write_text(json.dumps(cases, indent=2) + '\n')
    print(f'{len(cases)} release deadline controls passed')
