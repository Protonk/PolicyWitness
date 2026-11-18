"""Seam invocation adapter controls against a stand-in controller and client.

The stand-in records the arguments and request bytes it actually received and
emits bytes this control chose. Expected documents and bytes are written out
here, not read back from the adapter's record.
"""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

TESTS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TESTS / 'lib'))
import seam_invocation
from seam_invocation import EXPERIMENTAL, SeamCapture, Submission

STAND_IN = '''#!{python} -BS
import json, os, signal, sys, time
from pathlib import Path
receipts = Path(__file__).resolve().parents[3] / 'receipts'
if sys.argv[1:] == ['--version']:
    print(json.dumps(dict(build=dict(contract='test:stand-in', commit='constructed'))))
    sys.exit(0)
assert sys.argv[1] == 'run' or sys.argv[1:3] == ['test-input', 'run'], sys.argv
if '--refuse' in sys.argv:
    sys.stderr.write('stand-in usage refusal before reading any request\\n')
    sys.exit(2)
source = next(arg for arg in sys.argv[2:] if arg == '-' or arg.endswith('.json'))
raw = sys.stdin.buffer.read() if source == '-' else Path(source).read_bytes()
document = json.loads(raw)
(receipts / (document['specimen_id'] + '.json')).write_text(json.dumps(dict(
    program=Path(sys.argv[0]).name, argv=sys.argv[1:], request_hex=raw.hex())) + '\\n')
sys.stdout.buffer.write(bytes.fromhex(document['stdout_hex'])); sys.stdout.buffer.flush()
sys.stderr.buffer.write(b'stand-in diagnostic\\n'); sys.stderr.buffer.flush()
if document.get('signal'):
    os.kill(os.getpid(), document['signal'])
time.sleep(document.get('hold_seconds', 0))
sys.exit(document.get('exit_code', 0))
'''
REPLY = b'{"reply": "bytes \xff"}'  # not UTF-8: raw output is kept as bytes
FILES = ['controls.json', 'delivered-request.json', 'invocation.json', 'ordinary-request.json', 'stderr', 'stdout']


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    root = Path(sys.argv[1]).resolve()
    assert Path(os.environ['PW_TEST_ARTIFACTS']).resolve() in (root, *root.parents)
    evidence = Path(os.environ['PW_TEST_ARTIFACTS']).resolve() / 'seam-invocations'
    macos = root / 'StandIn.app/Contents/MacOS'
    macos.mkdir(parents=True)
    (root / 'receipts').mkdir()
    pw, client = macos / 'policy-witness', macos / 'pw-runner-client'
    for program in (pw, client):
        program.write_text(STAND_IN.format(python=sys.executable))
        program.chmod(0o755)
    completed = []

    def passed(name):
        completed.append(name)
        print(f'{name}: ok', flush=True)

    def record(scenario):
        return json.loads((evidence / scenario / 'invocation.json').read_text())

    def receipt(specimen_id):
        return json.loads((root / 'receipts' / (specimen_id + '.json')).read_text())

    def request(specimen_id, **fields):
        return dict(specimen_id=specimen_id, stdout_hex=REPLY.hex(), **fields)

    # RunCapture form: the capture directory is unchanged and the evidence stands beside it.
    spec = request('capture', exit_code=3)
    controls = {'worker_timeout_ms': 200, 'validator_executable_path': '/nonexistent/validator'}
    ordinary = (json.dumps(spec, indent=2) + '\n').encode()
    delivered = (json.dumps(dict(spec, _test_overrides=controls), indent=2) + '\n').encode()
    capture = SeamCapture(pw, root / 'capture', spec, controls=controls, scenario='control.capture',
                          cli_args=['--timeout-ms', '10'])
    intended = record('control.capture')
    argv = [str(pw), 'run', str(root / 'capture/specimen.json'), '--timeout-ms', '10']
    assert intended['state'] == 'intended' and intended['argv'] == argv and intended['pid'] is None
    assert intended['requested_route'] == 'legacy_request_block' and intended['requested_controls'] == controls
    assert intended['entry'] == 'cli' and intended['app']['build_contract'] == 'test:stand-in'
    assert intended['app']['app_path'] == str(root / 'StandIn.app') and intended['app']['version_exit_status'] == 0
    assert (evidence / 'control.capture/ordinary-request.json').read_bytes() == ordinary
    assert (evidence / 'control.capture/delivered-request.json').read_bytes() == delivered
    assert json.loads((evidence / 'control.capture/controls.json').read_text()) == controls
    assert not (root / 'receipts/capture.json').exists(), 'intent recorded only after launch'
    with capture as run:
        assert run.wait(timeout=10) == 3
    assert (root / 'capture/specimen.json').read_bytes() == delivered
    assert (root / 'capture/run.json').read_bytes() == REPLY
    assert receipt('capture') == dict(program='policy-witness', argv=argv[1:], request_hex=delivered.hex())
    done = record('control.capture')
    assert sorted(path.name for path in (evidence / 'control.capture').iterdir()) == FILES
    assert (done['state'], done['returncode'], done['exit_code'], done['term_signal']) == ('exited', 3, 3, None)
    assert done['start_monotonic_ns'] <= done['exit_observed_monotonic_ns'] and done['pid'] > 0
    assert (evidence / 'control.capture/stdout').read_bytes() == REPLY
    assert done['stdout']['sha256'] == digest(REPLY) and done['stderr']['bytes'] == 20
    assert done['ordinary_request']['sha256'] == digest(ordinary) and done['delivered_request']['sha256'] == digest(delivered)
    assert done['delivered_request']['channel'] == 'path' and 'took effect' in done['limits']
    passed('capture_keeps_request_controls_delivery_and_raw_output')

    # The intent survives a refusal that never reads the request, and a failed launch.
    with SeamCapture(pw, root / 'refused', request('refused'), controls={'worker_pre_ready_hang_ms': 60001},
                     scenario='control.early_refusal', cli_args=['--refuse']) as run:
        assert run.wait(timeout=10) == 2
    refused = record('control.early_refusal')
    assert refused['state'] == 'exited' and refused['returncode'] == 2
    assert refused['requested_controls'] == {'worker_pre_ready_hang_ms': 60001} and refused['argv'][-1] == '--refuse'
    assert (evidence / 'control.early_refusal/stderr').read_bytes() == b'stand-in usage refusal before reading any request\n'
    assert not (root / 'receipts/refused.json').exists()
    missing = macos / 'missing' / 'policy-witness'
    try:
        SeamCapture(missing, root / 'unlaunched', request('unlaunched'), controls={'worker_timeout_ms': 1},
                    scenario='control.launch_failure').start()
    except FileNotFoundError:
        pass
    else:
        raise AssertionError('missing executable launched')
    failed = record('control.launch_failure')
    assert failed['state'] == 'launch_failed' and failed['launch_error'] and failed['returncode'] is None
    assert failed['requested_controls'] == {'worker_timeout_ms': 1} and failed['argv'][0] == str(missing)
    assert failed['app']['build_contract'] is None and failed['app']['error'], failed['app']
    assert (evidence / 'control.launch_failure/delivered-request.json').is_file()
    passed('intent_survives_early_refusal_and_launch_failure')

    # A signal is the process's status, not an adapter judgment.
    with SeamCapture(pw, root / 'signaled', request('signaled', signal=signal.SIGTERM),
                     controls={'worker_post_apply_kill_signal': 9}, scenario='control.signal') as run:
        assert run.wait(timeout=10) == -signal.SIGTERM
    signaled = record('control.signal')
    assert (signaled['returncode'], signaled['exit_code'], signaled['term_signal']) == (-15, None, 15)
    # Leaving the context with the process alive is RunCapture's cleanup kill; the record keeps that status.
    with SeamCapture(pw, root / 'held', request('held', hold_seconds=30), controls={'worker_post_apply_hang_ms': 30000},
                     scenario='control.cleanup_kill') as run:
        assert record('control.cleanup_kill')['state'] == 'launched' and run.pid == record('control.cleanup_kill')['pid']
    killed = record('control.cleanup_kill')
    assert (killed['state'], killed['returncode'], killed['term_signal']) == ('exited', -9, 9)
    assert json.loads((root / 'held/capture.json').read_text())['cleanup_kill_requested'] is True
    passed('signal_and_cleanup_kill_status_recorded')

    # Process form: the client on standard input in the caller's encoding, the controller from a path.
    spec = request('stdin')
    compact = lambda document: json.dumps(document).encode()
    submission = Submission(client, 'control.stdin', spec, {'worker_post_apply_hang_ms': 5},
                            run_args=['--mach-service', '--request', '-', 'service.name'], encode=compact)
    assert submission.argv == [str(client), 'run', '--mach-service', '--request', '-', 'service.name']
    process = submission.start(stdout=root / 'stdin.out', stderr=root / 'stdin.err', start_new_session=True)
    assert process.wait(timeout=10) == 0 and process.poll() == 0 and process.pid > 0
    expected = compact(dict(spec, _test_overrides={'worker_post_apply_hang_ms': 5}))
    assert receipt('stdin') == dict(program='pw-runner-client', argv=submission.argv[1:], request_hex=expected.hex())
    piped = record('control.stdin')
    assert piped['entry'] == 'client' and piped['delivered_request']['channel'] == 'stdin'
    assert piped['delivered_request']['path'] is None and piped['app']['controller'] == str(pw)
    assert (evidence / 'control.stdin/ordinary-request.json').read_bytes() == compact(spec)
    assert (evidence / 'control.stdin/delivered-request.json').read_bytes() == expected
    assert (root / 'stdin.out').read_bytes() == (evidence / 'control.stdin/stdout').read_bytes() == REPLY
    path = root / 'path-request.json'
    submission = Submission(pw, 'control.path', request('path', exit_code=1), {'validator_io_timeout_ms': 500},
                            run_args=[path, '--timeout-ms', 7], request_path=path)
    assert json.loads(path.read_text()) == submission.delivered
    result = submission.run(timeout=10)
    assert (result.returncode, result.stdout, result.stderr) == (1, REPLY, b'stand-in diagnostic\n')
    assert receipt('path')['argv'] == ['run', str(path), '--timeout-ms', '7']
    assert record('control.path')['state'] == 'exited'
    passed('process_form_delivers_on_stdin_and_path')

    # Refusals leave no evidence directory and launch nothing.
    before = sorted(path.name for path in evidence.iterdir())
    for name, change, error in (
            ('empty', dict(controls={}), ValueError),
            ('unselected', dict(controls={'worker_executable_path': '/x'}), ValueError),
            ('mixed', dict(controls={'worker_timeout_ms': 1, 'actor_equipment_executable_paths': {}}), ValueError),
            ('not_a_mapping', dict(controls=[('worker_timeout_ms', 1)]), ValueError),
            ('request_block', dict(request=dict(request('block'), _test_overrides={})), ValueError),
            ('scenario_reuse', dict(scenario='control.capture'), FileExistsError),
            ('scenario_path', dict(scenario='../outside'), ValueError),
            ('unknown_program', dict(pw=macos / 'other-tool'), ValueError)):
        arguments = dict(pw=pw, request=request('refusal-' + name), controls={'worker_timeout_ms': 1},
                         scenario='control.refusal.' + name)
        arguments.update(change)
        try:
            SeamCapture(arguments['pw'], root / ('refusal-' + name), arguments['request'],
                        controls=arguments['controls'], scenario=arguments['scenario'])
        except error:
            pass
        else:
            raise AssertionError('accepted: ' + name)
        assert not (root / ('refusal-' + name)).exists(), name
    assert sorted(path.name for path in evidence.iterdir()) == before
    assert json.loads((evidence / 'control.capture/invocation.json').read_text()) == done
    changed = SeamCapture(pw, root / 'changed', request('changed'), controls={'worker_timeout_ms': 1},
                          scenario='control.changed_delivery')
    changed.request_path.write_text(json.dumps(request('changed', exit_code=9)) + '\n')
    try:
        changed.start()
    except RuntimeError as exc:
        assert 'changed after its intent' in str(exc)
    else:
        raise AssertionError('a rewritten delivered request launched')
    assert record('control.changed_delivery')['state'] == 'intended' and not (root / 'receipts/changed.json').exists()
    passed('refusals_write_and_launch_nothing')

    # Command form for shell cases: the same record, the submission's status, 70 for the adapter's own failure.
    ordinary = b'{"specimen_id": "command", "stdout_hex": "6f6b", "exit_code": 7}\n'
    (root / 'command-ordinary.json').write_bytes(ordinary)
    command = [sys.executable, '-B', '-S', str(TESTS / 'lib/seam_invocation.py'), '--scenario', 'control.command',
               '--request', str(root / 'command-ordinary.json'), '--controls', '{"worker_pre_ready_hang_ms": 2000}',
               '--delivered', str(root / 'command-delivered.json'), '--stdout', str(root / 'command.out'),
               '--stderr', str(root / 'command.err'), '--', str(pw), str(root / 'command-delivered.json'), '--timeout-ms', '9']
    result = subprocess.run(command, capture_output=True, timeout=30)
    assert (result.returncode, result.stdout, result.stderr) == (7, b'', b''), result
    assert (root / 'command.out').read_bytes() == b'ok'
    assert (evidence / 'control.command/ordinary-request.json').read_bytes() == ordinary
    assert json.loads((root / 'command-delivered.json').read_text()) == dict(
        specimen_id='command', stdout_hex='6f6b', exit_code=7, _test_overrides={'worker_pre_ready_hang_ms': 2000})
    assert receipt('command')['argv'] == ['run', str(root / 'command-delivered.json'), '--timeout-ms', '9']
    assert record('control.command')['returncode'] == 7
    repeated = subprocess.run(command, capture_output=True, timeout=30)
    assert repeated.returncode == 70 and b'already recorded' in repeated.stderr, repeated
    usage = subprocess.run(command[:6], capture_output=True, timeout=30)
    assert usage.returncode == 70 and b'required' in usage.stderr, usage
    (root / 'command-signal.json').write_text(json.dumps(request('command-signal', signal=signal.SIGKILL)))
    command[5:8] = ['control.command_signal', '--request', str(root / 'command-signal.json')]
    assert subprocess.run(command, capture_output=True, timeout=30).returncode == 128 + signal.SIGKILL
    passed('command_form_propagates_status')

    # Experimental route: the request is delivered as given and the controls travel beside it.
    spec = request('experimental', exit_code=4)
    controls = {'worker_timeout_ms': 200, 'validator_executable_path': '/nonexistent/validator'}
    ordinary = (json.dumps(spec, indent=2) + '\n').encode()
    capture = SeamCapture(pw, root / 'experimental', spec, controls=controls, scenario='control.experimental',
                          cli_args=['--timeout-ms', '10'], route=EXPERIMENTAL)
    argv = [str(pw), 'test-input', 'run', str(root / 'experimental/specimen.json'), '--worker-timeout-ms', '200',
            '--validator-executable-path', '/nonexistent/validator', '--timeout-ms', '10']
    intended = record('control.experimental')
    assert intended['state'] == 'intended' and intended['argv'] == argv == capture.argv
    assert intended['requested_route'] == 'experimental_cli' and intended['requested_controls'] == controls
    assert json.loads((root / 'experimental/capture.json').read_text())['argv'] == argv
    assert (evidence / 'control.experimental/ordinary-request.json').read_bytes() == ordinary
    assert (evidence / 'control.experimental/delivered-request.json').read_bytes() == ordinary
    assert json.loads((evidence / 'control.experimental/controls.json').read_text()) == controls
    with capture as run:
        assert run.wait(timeout=10) == 4
    assert (root / 'experimental/specimen.json').read_bytes() == ordinary
    assert receipt('experimental') == dict(program='policy-witness', argv=argv[1:], request_hex=ordinary.hex())
    assert record('control.experimental')['returncode'] == 4
    # No controls, and a request that carries its own block, are submissions this route can make.
    blocked = request('experimental-block', _test_overrides={'worker_executable_path': '/x'})
    with SeamCapture(pw, root / 'experimental-block', blocked, controls={}, scenario='control.experimental_block',
                     route=EXPERIMENTAL) as run:
        assert run.wait(timeout=10) == 0
    assert run.argv == [str(pw), 'test-input', 'run', str(root / 'experimental-block/specimen.json')]
    assert receipt('experimental-block')['request_hex'] == (json.dumps(blocked, indent=2) + '\n').encode().hex()
    assert record('control.experimental_block')['requested_controls'] == {}
    # The client receives one controls object; the controller receives one flag per control.
    spec = request('experimental-stdin')
    submission = Submission(client, 'control.experimental_stdin', spec, {'worker_post_apply_hang_ms': 5},
                            run_args=['--request', '-', 'service.name'], encode=compact, route=EXPERIMENTAL)
    assert submission.argv == [str(client), 'run', '--experimental-controls', '{"worker_post_apply_hang_ms": 5}',
                               '--request', '-', 'service.name']
    assert submission.run(timeout=10).returncode == 0
    assert receipt('experimental-stdin') == dict(program='pw-runner-client', argv=submission.argv[1:],
                                                 request_hex=compact(spec).hex())
    piped = record('control.experimental_stdin')
    assert piped['requested_route'] == 'experimental_client' and piped['delivered_request']['channel'] == 'stdin'
    assert (evidence / 'control.experimental_stdin/delivered-request.json').read_bytes() == compact(spec)
    path = root / 'experimental-path.json'
    raw = b'{"specimen_id": "experimental-path",\n "stdout_hex": "6f6b"}'
    submission = Submission(pw, 'control.experimental_path', json.loads(raw), {'validator_io_timeout_ms': 500},
                            run_args=[path, '--timeout-ms', 7], request_path=path, ordinary_bytes=raw, route=EXPERIMENTAL)
    assert submission.argv == [str(pw), 'test-input', 'run', '--validator-io-timeout-ms', '500', str(path), '--timeout-ms', '7']
    assert submission.run(timeout=10).stdout == b'ok' and path.read_bytes() == raw
    assert receipt('experimental-path') == dict(program='policy-witness', argv=submission.argv[1:], request_hex=raw.hex())
    assert record('control.experimental_path')['requested_route'] == 'experimental_cli'
    before = sorted(path.name for path in evidence.iterdir())
    for name, arguments in (
            ('unselected', dict(pw=pw, controls={'worker_executable_path': '/x'}, route=EXPERIMENTAL)),
            ('client_capture', dict(pw=client, controls={'worker_timeout_ms': 1}, route=EXPERIMENTAL)),
            ('unknown_route', dict(pw=pw, controls={'worker_timeout_ms': 1}, route='experimental_cli'))):
        try:
            SeamCapture(arguments['pw'], root / ('experimental-refusal-' + name), request('experimental-refusal-' + name),
                        controls=arguments['controls'], scenario='control.experimental_refusal.' + name,
                        route=arguments['route'])
        except ValueError:
            pass
        else:
            raise AssertionError('accepted: ' + name)
        assert not (root / ('experimental-refusal-' + name)).exists(), name
    assert sorted(path.name for path in evidence.iterdir()) == before
    (root / 'command-experimental.json').write_bytes(b'{"specimen_id": "command-experimental", "stdout_hex": "6f6b"}')
    command = [sys.executable, '-B', '-S', str(TESTS / 'lib/seam_invocation.py'), '--scenario', 'control.command_experimental',
               '--request', str(root / 'command-experimental.json'), '--controls', '{"worker_pre_ready_hang_ms": 2000}',
               '--route', 'experimental', '--delivered', str(root / 'command-experimental-delivered.json'),
               '--stdout', str(root / 'command-experimental.out'), '--stderr', str(root / 'command-experimental.err'),
               '--', str(pw), str(root / 'command-experimental-delivered.json')]
    assert subprocess.run(command, capture_output=True, timeout=30).returncode == 0
    assert (root / 'command-experimental-delivered.json').read_bytes() == (root / 'command-experimental.json').read_bytes()
    assert receipt('command-experimental')['argv'] == ['test-input', 'run', '--worker-pre-ready-hang-ms', '2000',
                                                       str(root / 'command-experimental-delivered.json')]
    assert record('control.command_experimental')['requested_route'] == 'experimental_cli'
    passed('experimental_route_delivers_request_unchanged_and_controls_beside_it')

    assert seam_invocation.scenario_for(root / 'a' / 'b') == '.'.join((*root.relative_to(evidence.parent).parts, 'a', 'b'))
    (root / 'seam-controls.json').write_text(json.dumps(completed, indent=2) + '\n')
    print(f'{len(completed)} seam invocation controls passed')


if __name__ == '__main__':
    main()
