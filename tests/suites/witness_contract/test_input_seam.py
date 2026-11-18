#!/usr/bin/env python3
"""Submit the published read input with `test-input run` and retain what each submission showed.

Every submission that carries controls goes through the seam invocation adapter,
so its command, controls and delivered request are recorded before launch. The checker in check_test_input_seam.py owns the plan
and every expectation; this driver only prepares, launches, samples and records.
"""
import json
from pathlib import Path
import plistlib
import shutil
import subprocess

import check_test_input as publication
import check_test_input_seam as checker
import consumer
from file_observation import observe_target
from porcelain import decode as decode_porcelain
from run_capture import RunCapture
from runner_client_capture import host_reply, validate_capture
from seam_invocation import SeamCapture, Submission
from worker_exit_witness import worker_exit_witness

FIXTURES = Path(__file__).resolve().parents[2] / 'fixtures/validator'
CLI_ARGS = ['--timeout-ms', '20000']
WAIT_SECONDS = 60


def disposition(record):
    """Whether this record itself shows that no worker of the submission remains."""
    envelope, reply = record.get('envelope'), record.get('reply')
    if record.get('exit') == 2 and isinstance(envelope, dict) and publication.get(envelope, 'data', 'runner_client') is None:
        return True, 'the controller reports no client invocation'
    if record.get('exit') == 2 and record.get('stdout_bytes') == 0:
        return True, 'usage refusal with no output; nothing was submitted'
    if not isinstance(reply, dict):
        return False, 'no identity-admitted host reply; worker exit unknown'
    child = publication.get(reply, 'phases', 0, 'validator_subprocess')
    if isinstance(child, dict) and child.get('reaped') is not True:
        return False, 'validator not reaped; it may still run'
    witnessed, reason = worker_exit_witness(dict(data=dict(runner_result=reply)))
    if witnessed:
        return witnessed, reason
    if reply.get('normalized_outcome') == 'bad_request' and reply.get('runner_subprocess') is None and \
            reply.get('steps') == [] and not reply.get('phases') and not reply.get('actors') and \
            isinstance(reply.get('request_failure'), dict):
        return True, 'host request refusal before worker or validator launch'
    if reply.get('normalized_outcome') == 'worker_spawn_failed' and reply.get('runner_subprocess') is None and \
            not reply.get('actors'):
        return True, 'the host reports that its worker spawn failed; it has no worker to reap'
    return False, reason


def run_seam(directory, pw, app, work, identity, attempts, persist):
    """Run every planned submission; `attempts` and `persist` are the owning case's cleanup record."""
    directory = Path(directory)
    directory.mkdir()
    client = Path(pw).with_name('pw-runner-client')
    service = plistlib.loads((Path(app) / 'Contents/XPCServices/PWRunner.xpc/Contents/Info.plist').read_bytes())['CFBundleIdentifier']
    target = str(Path(work) / 'seam-target')
    Path(target).write_bytes(publication.LONG)
    Path(target).chmod(0o600)
    validator = Path(work) / 'validator.py'
    shutil.copyfile(FIXTURES / 'validator.py', validator)
    validator.chmod(0o755)
    shutil.copyfile(FIXTURES / 'deadline.json', validator.with_suffix('.case.json'))
    state = dict(identity=identity, target=target, payload_hex=publication.LONG.hex(), validator=str(validator),
                 read={}, scenarios={})

    def save():
        (directory / 'state.json').write_text(publication.encode(state))

    def command(name, argv):
        dest = directory / name
        dest.mkdir()
        result = subprocess.run([str(arg) for arg in argv], capture_output=True, timeout=WAIT_SECONDS)
        record = dict(argv=[str(arg) for arg in argv], exit=result.returncode,
                      stdout=result.stdout.decode('utf-8', 'replace'), stderr=result.stderr.decode('utf-8', 'replace'))
        (dest / 'command.json').write_text(publication.encode(record['argv']))
        (dest / 'stdout').write_bytes(result.stdout)
        (dest / 'stderr').write_bytes(result.stderr)
        (dest / 'exit').write_text(str(result.returncode) + '\n')
        return record

    def owned(name, launch):
        """Sample, launch and sample again, with the submission in the case's cleanup record throughout."""
        record = dict(before=observe_target(target, publication.BOUND), after=None)
        state['scenarios'][name] = record
        entry = dict(passage='seam.' + name, capture=str((directory / name).resolve()), worker_exit_witnessed=False,
                     witness='submission may be in progress')
        attempts.append(entry)
        persist()
        try:
            launch(record)
        finally:
            record['after'] = observe_target(target, publication.BOUND)
            entry['worker_exit_witnessed'], entry['witness'] = disposition(record)
            persist()
            save()
        assert entry['worker_exit_witnessed'], ('unresolved native disposition; stop before the next submission', entry)

    def read_envelope(record, stdout):
        record['envelope'] = envelope = publication.parsed(stdout)
        admitted = isinstance(envelope, dict) and publication.get(envelope, 'build', 'contract') == identity
        record['consumer_errors'] = consumer.validate(envelope, identity) if admitted else ['no current-build envelope']
        record['reply'] = consumer.admitted_reply(envelope, identity) if admitted else None

    def capture(name, document, controls=None):
        """One controller submission: through the adapter when `controls` is a mapping, plain `run` otherwise."""
        def launch(record):
            if controls is None:
                run = RunCapture(pw, directory / name, document, cli_args=CLI_ARGS)
            else:
                run = SeamCapture(pw, directory / name, document, controls=controls, scenario='test_input.' + name,
                                  cli_args=CLI_ARGS)
            with run:
                record['exit'] = run.wait(timeout=WAIT_SECONDS)
            record.update(argv=run.argv, stderr=run.stderr_path.read_text(), stdout_bytes=run.stdout_path.stat().st_size,
                          delivered_document=json.loads(run.request_path.read_text()))
            if controls is not None:
                record.update(invocation=json.loads((run.seam / 'invocation.json').read_text()),
                              ordinary=(run.seam / 'ordinary-request.json').read_text(),
                              delivered=(run.seam / 'delivered-request.json').read_text())
            read_envelope(record, run.stdout_path.read_text())
        owned(name, launch)

    def direct(name, document, controls):
        """One runner-client submission, with its capture decoded by the independent reader."""
        def launch(record):
            dest = directory / name
            dest.mkdir()
            request = dest / 'specimen.json'
            submission = Submission(client, 'test_input.' + name, document, controls,
                                    run_args=['--timeout-ms', '20000', service, request], request_path=request)
            result = submission.run(timeout=WAIT_SECONDS)
            (dest / 'capture.pwp').write_bytes(result.stdout)
            record.update(argv=submission.argv, exit=result.returncode, stderr=result.stderr.decode('utf-8', 'replace'),
                          stdout_bytes=len(result.stdout),
                          invocation=json.loads((submission.seam / 'invocation.json').read_text()),
                          ordinary=(submission.seam / 'ordinary-request.json').read_text(),
                          delivered=(submission.seam / 'delivered-request.json').read_text())
            try:
                record['capture'] = decoded = decode_porcelain(result.stdout, 'capture')
                record['capture_errors'] = validate_capture(decoded, identity)
                record['reply'] = host_reply(decoded, identity) if not record['capture_errors'] else None
            except (ValueError, KeyError, TypeError) as error:
                record.update(capture=None, capture_errors=[f'{type(error).__name__}: {error}'], reply=None)
            (dest / 'reply.json').write_text(publication.encode(record['reply']))
        owned(name, launch)

    def usage(name, command_words, arguments):
        """A command line the controller refuses: launched directly, since no controls mapping spells it.

        The request it names is the admissible published input, so only the arguments can be refused."""
        def launch(record):
            request = directory / ('usage.' + name + '.json')
            request.write_text(publication.encode(checker.expected_document(identity, target)))
            result = command('usage.' + name, [pw, *command_words, *(request if item is None else item for item in arguments)])
            record.update(result, request_path=str(request), stdout_bytes=len(result['stdout'].encode()))
            read_envelope(record, record['stdout'])
        owned('usage.' + name, launch)

    state['read']['first'] = command('read-first', [pw, 'test-input', 'read', '--target', target])
    document = checker.expected_document(identity, target)
    capture('neighbour', document)
    capture('zero_controls', document, {})
    for name in checker.ACTIVATIONS:
        capture(name, checker.request_for(name, identity, target), checker.controls_for(name, state))
        if name == 'validator_io_timeout_ms':
            receipt = validator.with_suffix('.received.json')
            state['scenarios'][name]['validator_receipt'] = publication.parsed(receipt.read_text()) if receipt.exists() else None
            for path in (receipt, validator.with_suffix('.emitted.ndjson')):
                if path.exists():
                    shutil.copyfile(path, directory / name / path.name)
            save()
    for name, (arguments, _) in checker.USAGE.items():
        usage(name, ['test-input', 'run'], arguments)
    usage('ordinary_run', ['run'], checker.ORDINARY_USAGE[0])
    capture('combined', document, checker.COMBINED)
    capture('unreached', document, checker.UNREACHED)
    capture('floor', document, checker.FLOOR)
    capture('early_refusal', checker.request_for('early_refusal', identity, target), checker.EARLY)
    for key, value in checker.NATIVE_RANGE.items():
        capture('native_range.' + key, document, {key: value})
    for name in ('cli', 'inert', 'mixed', 'empty'):
        block, controls = ({}, {}) if name == 'empty' else checker.LEGACY_BLOCKS[name]
        capture('legacy_block.' + name, checker.request_for(name, identity, target, block), controls)
    direct('client.activation', document, checker.CLIENT_CONTROLS)
    direct('legacy_block.client', checker.request_for('client', identity, target, checker.LEGACY_BLOCKS['client'][0]), {})
    direct('client.fractional', document, checker.CLIENT_FRACTIONAL)
    # The two substitutions the request block keeps are ordinary submissions: no selected control, no adapter.
    for name, block in checker.UNSELECTED.items():
        capture('unselected.' + name, checker.request_for(name, identity, target, block))

    # The read publisher under a profile that denies fork, and a command that must launch under the same profile.
    denial = ['/usr/bin/sandbox-exec', '-p', checker.DENIAL, pw]
    state['read']['denied'] = command('read-denied', [*denial, 'test-input', 'read', '--target', target])

    def denied_run(record):
        request = directory / 'denied-run.json'
        request.write_text(publication.encode(document))
        record.update(command('denied_run', [*denial, 'test-input', 'run', request]))
        record['stdout_bytes'] = len(record['stdout'].encode())
        read_envelope(record, record['stdout'])
    owned('denied_run', denied_run)
    state['read']['last'] = command('read-last', [pw, 'test-input', 'read', '--target', target])
    save()
    report = checker.evaluate(state)
    publication.write_report(directory, report)
    assert report['ok'], 'test-input run observations did not meet independently pinned expectations'
    return state
