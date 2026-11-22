"""Accepted input through the signed CLI and direct XPC, with an independent file effect."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import plistlib
import secrets
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import build_context
from run_capture import RunCapture
from seam_invocation import SeamCapture
from request_examples import CORPUS, examples, materialize
from porcelain import decode as decode_porcelain
from runner_client_capture import host_reply


def changed(specimen, path, value):
    result = copy.deepcopy(specimen)
    node = result
    for part in path[:-1]:
        node = node[part]
    node[path[-1]] = value
    return result


def composite_parameters(pw, out, directory, base):
    """Two fixed fresh-read targets; only ROOT changes between signed runs."""
    roots = [Path(directory) / 'parameter-a', Path(directory) / 'parameter-b']
    contents = [b'parameter root A\n', b'parameter root B\n']
    targets = []
    for root, content in zip(roots, contents):
        root.mkdir()
        target = root / 'payload'
        target.write_bytes(content)
        targets.append(target)
    before = [dict(path=str(path), device=path.stat().st_dev, inode=path.stat().st_ino,
                   content_hex=path.read_bytes().hex()) for path in targets]
    source = ('(version 1) (allow default) (deny file-read-data) '
              '(allow file-read-data (literal (string-append (param "ROOT") "/payload")))')
    for selected, root in enumerate(roots):
        specimen = copy.deepcopy(base)
        specimen['policy'] = dict(format='sbpl', sbpl_source=source, params={'ROOT': str(root)})
        specimen['probe_plan'] = [dict(step_id=f'read-{i}',
            sandbox_check=dict(operation='file-read-data', filter=dict(kind='path', value=str(path))),
            attempt=dict(kind='file', action='read_fresh', target=str(path)))
            for i, path in enumerate(targets)]
        case = out / f'composite-parameter-{selected}'
        capture = RunCapture(pw, case, specimen, cli_args=[])
        (case / 'independent-before.json').write_text(json.dumps(before, indent=2) + '\n')
        original = capture.request_path.read_bytes()
        with capture as run:
            rc = run.wait(timeout=30)
            envelope = run.load_json()
        assert capture.request_path.read_bytes() == original
        after = [dict(path=str(path), device=path.stat().st_dev, inode=path.stat().st_ino,
                      content_hex=path.read_bytes().hex()) for path in targets]
        (case / 'independent-after.json').write_text(json.dumps(after, indent=2) + '\n')
        assert after == before, 'owned input files changed during read controls'
        assert rc == 0 and envelope['result']['ok'] is True, envelope
        runner = envelope['data']['runner_result']
        assert runner['normalized_outcome'] == 'finished' and runner['sandboxed_after_apply'] is True, runner
        assert runner['policy_sha256'] == hashlib.sha256(source.encode()).hexdigest(), runner
        assert runner['runner_subprocess']['reaped'] is True and len(runner['steps']) == 2, runner
        for index, step in enumerate(runner['steps']):
            attempt, read = step['attempt'], step['attempt']['fresh_read']
            assert step['step_id'] == f'read-{index}', step
            assert attempt['requested_path'] == str(targets[index]), attempt
            assert attempt['requested_action'] == 'read_fresh' and attempt['result_source'] == 'worker', attempt
            if index == selected:
                assert attempt['outcome'] == 'ok' and attempt['rc'] == 0, attempt
                assert read['open_rc'] >= 0 and read['stat_rc'] == 0 and read['close_rc'] == 0, read
                assert read['read_rc'] == len(contents[index]) and read['content_hex'] == contents[index].hex(), read
                assert read['identity']['device'] == before[index]['device'], read
                assert read['identity']['inode'] == before[index]['inode'], read
            else:
                assert attempt['rc'] == -1 and read['open_rc'] == -1, attempt
                assert read['open_errno'] in (1, 13), read
                assert read.get('read_rc') is None and read.get('content_hex') is None, read
        # Prediction and effect remain separate fields; this example's oracle
        # is the seeded bytes and descriptor identity, not a comparison verdict.


def refusal_workflows(pw, client, service, out, effect, base, cli):
    """Pin each entry's first refusing owner and a concrete capture repair."""
    contract = build_context.candidate_contract()
    receipts = []
    # A repaired request can query one name and create at another.
    query_path = effect.with_name('query-only')
    base = changed(base, ['probe_plan', 0, 'sandbox_check', 'filter', 'value'], str(query_path))
    base['probe_plan'][0]['step_id'] = 'repaired-create'
    # Give these policy bytes a digest specific to this repair sequence.
    base['policy']['sbpl_source'] += '\n; ' + secrets.token_hex(8) + '\n'

    def remember(name, entry, expected, boundary, result):
        receipts.append(dict(name=name, entry=entry, expected_failure=expected,
                             expected_boundary=boundary, observed_outcome=result['normalized_outcome']))
        (out / 'repair-transitions.json').write_text(json.dumps(receipts, indent=2) + '\n')

    def cli_case(name, specimen, failure, boundary, *, raw=None):
        envelope = cli('repair-cli-' + name, specimen, accepted=failure is None,
                       failure=failure, raw=raw, expected_effect=b'')
        runner = envelope['data']['runner_result']
        assert (runner is not None) is (boundary == 'host'), envelope
        assert (envelope['data']['runner_client'] is not None) is (boundary == 'host'), envelope
        remember(name, 'cli', failure, boundary, envelope['result'])
        return runner

    def direct_case(name, specimen, failure):
        case = out / ('repair-xpc-' + name)
        case.mkdir()
        request = case / 'specimen.json'
        request.write_text(json.dumps(specimen, indent=2) + '\n')
        original = request.read_bytes()
        argv = [str(client), 'run', '--timeout-ms', '10000', service, str(request)]
        assert not effect.exists()
        with (case / 'capture.pwp').open('wb') as stdout, (case / 'stderr').open('wb') as stderr:
            process = subprocess.run(argv, stdout=stdout, stderr=stderr, timeout=20)
        (case / 'command.json').write_text(json.dumps(dict(argv=argv, returncode=process.returncode)) + '\n')
        assert process.returncode == 0 and request.read_bytes() == original, name
        reply = host_reply(decode_porcelain((case / 'capture.pwp').read_bytes(), 'capture'), contract)
        (case / 'reply.json').write_text(json.dumps(reply, indent=2) + '\n')
        observed = effect.is_file()
        (case / 'effect.json').write_text(json.dumps(dict(observed=observed, expected=failure is None)) + '\n')
        assert reply['producer']['contract'] == contract, reply
        if failure is not None:
            assert reply['normalized_outcome'] == 'bad_request' and reply['request_failure'] == failure, reply
            assert not observed and reply['steps'] == [] and reply.get('runner_subprocess') is None, reply
            assert all(phase.get('validator_subprocess') is None for phase in reply.get('phases', [])), reply
        else:
            assert reply['normalized_outcome'] == 'finished' and observed and effect.read_bytes() == b'', reply
            assert reply['sandboxed_after_apply'] is True and reply['runner_subprocess']['reaped'] is True, reply
            assert reply['steps'][0]['attempt']['outcome'] == 'ok', reply
            effect.unlink()
        remember(name, 'xpc', failure, 'host', reply)
        return reply

    # Each correction changes one failing component of the same capture intent.
    typo = changed(base, ['policy', 'capture_compiled_profiel'], True)
    corrected = copy.deepcopy(typo)
    corrected['policy']['capture_compiled_profile'] = corrected['policy'].pop('capture_compiled_profiel')
    captured = changed(corrected, ['policy', 'capture_nonce'], secrets.token_hex(16))
    repairs = [
        ('capture-0-typo', typo, dict(code='unknown_field', path=['policy', 'capture_compiled_profiel'])),
        ('capture-1-nonce-required', corrected, dict(code='invalid_capture_nonce', path=['policy', 'capture_nonce'])),
        ('capture-2-enabled', captured, None),
    ]
    for name, specimen, failure in repairs:
        for entry in ('cli', 'xpc'):
            if failure is None:
                specimen = changed(specimen, ['policy', 'capture_nonce'], secrets.token_hex(16))
            reply = cli_case(name, specimen, failure, 'host') if entry == 'cli' else direct_case(name, specimen, failure)
            assert not query_path.exists(), f'{entry}: the request created the query target'
            if failure is None:
                step, = reply['steps']
                assert step['step_id'] == specimen['probe_plan'][0]['step_id'], step
                assert step['sandbox_check']['filter_value'] == str(query_path), step
                assert step['attempt']['requested_path'] == str(effect) and step['attempt']['result_source'] == 'worker', step
                assert reply['runner_subprocess']['reaped'] is True, reply
                profile = reply['compiled_profile']
                assert profile['status'] == 'captured' and profile['producer'] == 'worker', profile
                assert profile['capture_stage'] == 'before_apply', profile
                assert profile['request_nonce'] == specimen['policy']['capture_nonce'], profile
                assert profile['worker_pid'] == reply['runner_subprocess']['pid'], profile
                source_digest = hashlib.sha256(specimen['policy']['sbpl_source'].encode()).hexdigest()
                assert profile['source_sha256'] == reply['policy_sha256'] == source_digest, profile
                bytecode = base64.b64decode(profile['bytecode_b64'], validate=True)
                assert len(bytecode) == profile['bytecode_length'] > 0, profile
                assert hashlib.sha256(bytecode).hexdigest() == profile['bytecode_sha256'], profile
                assert profile['parameter_count'] == 0, profile

    # CLI syntax precedes even JSON parsing. The next invocation removes only
    # the flag and therefore reaches the JSON owner; no host was contacted.
    capture = RunCapture(pw, out / 'repair-cli-argument-before-json', base, cli_args=['--not-a-run-option'])
    capture.request_path.write_text('{ malformed json')
    original = capture.request_path.read_bytes()
    with capture as run:
        assert run.wait(timeout=30) == 2
        envelope = run.load_json()
    assert capture.request_path.read_bytes() == original and not effect.exists()
    assert envelope['result']['normalized_outcome'] == 'tool_error', envelope
    assert 'unknown argument: --not-a-run-option' in envelope['result']['error'], envelope
    assert all(envelope['data'].get(key) is None for key in ('request_failure', 'runner_client', 'runner_result')), envelope
    remember('argument-before-json', 'cli', None, 'arguments', envelope['result'])
    cli_case('json-after-argument-repair', base, dict(code='invalid_json', path=[]), 'controller', raw='{ malformed json')

    compound = changed(corrected, ['policy', 'augments'], ['../outside'])
    compound['runner'] = {'mode': 42}
    compound['contract'] = 'test:workflow-foreign'
    current = changed(compound, ['contract'], contract)
    selected = changed(current, ['runner', 'mode'], 'standard')
    no_selector = copy.deepcopy(selected); del no_selector['runner']
    foreign = dict(code='unsupported_contract', path=['contract'], expected_contract=contract)
    # Direct XPC does not interpret any selector; it rejects the root key.
    rows = [
        ('identity-before-selector', compound, foreign, foreign, 'controller'),
        ('selector-before-augmentation', current, dict(code='type_mismatch', path=['runner', 'mode']),
            dict(code='unknown_field', path=['runner']), 'controller'),
        ('augmentation-before-host-meaning', selected, dict(code='invalid_value', path=['policy', 'augments', '0']),
            None, 'controller'),
        ('direct-augmentation-before-meaning', no_selector, dict(code='invalid_value', path=['policy', 'augments', '0']),
            dict(code='unresolved_augments', path=['policy', 'augments']), 'controller'),
    ]
    for name, specimen, cli_failure, host_failure, boundary in rows:
        cli_case(name, specimen, cli_failure, boundary)
        if host_failure is not None:
            direct_case(name, specimen, host_failure)
    # Removing augments from no_selector yields exactly the retained nonce
    # repair request above. Its next boundary and final correction ran already.
    del no_selector['policy']['augments']
    assert no_selector == corrected

    # Typed decode finishes before capacity admission. Fixing just the typo
    # exposes the existing 255-byte specimen-ID limit at both actual entries.
    oversized = dict(typo, specimen_id='x' * 256)
    decoded = copy.deepcopy(oversized); del decoded['policy']['capture_compiled_profiel']
    for name, specimen, failure in [
        ('decode-before-capacity', oversized, dict(code='unknown_field', path=['policy', 'capture_compiled_profiel'])),
        ('capacity-after-decode-repair', decoded, dict(code='admission_refused', path=['specimen_id'])),
    ]:
        for entry in ('cli', 'xpc'):
            reply = cli_case(name, specimen, failure, 'host') if entry == 'cli' else direct_case(name, specimen, failure)
            if name == 'capacity-after-decode-repair':
                refused = reply['admission_failure']
                assert (refused['field'], refused['actual'], refused['maximum'], refused['unit']) == ('specimen_id', 256, 255, 'utf8_bytes'), refused



def capture_receipts(pw, out, effect, base):
    """Capture beside a compile failure, and a capture with two parameters.

    The compile failure leaves application unobserved, so the receipt withholds
    every capture field. The two-parameter digest is framed here from the
    stated rule, independently of the worker and host.
    """
    failing = copy.deepcopy(base)
    failing['policy'] = dict(format='sbpl', sbpl_source='(version 1)(not-a-real-sandbox-operation)',
                             capture_compiled_profile=True, capture_nonce=secrets.token_hex(16))
    with RunCapture(pw, out / 'capture_compile_failure', failing, cli_args=[]) as run:
        assert run.wait(timeout=30) == 1
        reply = run.load_json()['data']['runner_result']
    assert not effect.exists(), 'a compile failure ran its attempt'
    assert reply['normalized_outcome'] == 'runner_failed' and reply['sandboxed_after_apply'] is False, reply
    failure = reply['runner_subprocess']['worker_evidence']['failure']
    assert (failure['operation'], failure['native_kind']) == (5, 2), failure
    assert reply['compiled_profile'] == dict(status='unavailable', reason='successful_application_unconfirmed',
                                             worker_pid=reply['runner_subprocess']['pid']), reply['compiled_profile']

    params = {'a': '\u00e9', 'z': '2'}
    def framed(text):
        data = text.encode('utf-8')
        return len(data).to_bytes(4, 'little') + data
    pairs = sorted(hashlib.sha256(framed(k) + framed(v)).digest() for k, v in params.items())
    expected = hashlib.sha256(len(params).to_bytes(4, 'little') + b''.join(pairs)).hexdigest()
    captured = copy.deepcopy(base)
    captured['policy'].update(params=params, capture_compiled_profile=True, capture_nonce=secrets.token_hex(16))
    with RunCapture(pw, out / 'capture_two_parameters', captured, cli_args=[]) as run:
        assert run.wait(timeout=30) == 0
        reply = run.load_json()['data']['runner_result']
    assert effect.is_file(), reply
    effect.unlink()
    profile = reply['compiled_profile']
    assert profile['status'] == 'captured' and profile['request_nonce'] == captured['policy']['capture_nonce'], profile
    assert profile['parameter_count'] == 2 and profile['params_sha256'] == expected, (profile, expected)
    assert profile['source_sha256'] == hashlib.sha256(captured['policy']['sbpl_source'].encode()).hexdigest(), profile


def actor_empty_step_id(pw, client, service, out, directory):
    """An actor-form request with one empty action identifier is refused before any actor launches.

    The empty identifier follows an action that would create a file, so a
    launch would leave the file behind. The same request with a nonempty
    identifier runs and creates it.
    """
    contract = build_context.candidate_contract()
    effect = Path(directory) / 'actor-empty-step'
    failure = dict(code='empty_step_id', path=['phases', '0', 'actions', '1', 'step_id'])

    def specimen(step_id):
        return dict(contract=contract, specimen_id='actor-empty-step',
            actors=[dict(actor_id='subject', sandbox=dict(mode='unapplied'))],
            phases=[dict(phase_id='main', actor_id='subject', actions=[
                dict(step_id='effect',
                     sandbox_check=dict(operation='file-write-create', filter=dict(kind='path', value=str(effect))),
                     attempt=dict(kind='file', action='create', target=str(effect))),
                dict(step_id=step_id,
                     sandbox_check=dict(operation='file-read-data', filter=dict(kind='path', value='/etc/hosts')),
                     attempt=dict(kind='file', action='open_read', target='/etc/hosts'))])])

    def refused(reply, created):
        assert reply['normalized_outcome'] == 'bad_request' and reply['request_failure'] == failure, reply
        assert reply['steps'] == [] and reply.get('phases') == [] and reply.get('runner_subprocess') is None, reply
        assert not any(isinstance(actor, dict) and (actor.get('launch') is not None or actor.get('subprocess') is not None)
                       for actor in reply.get('actors') or []), reply
        assert not created, 'a refused actor request created its first action\'s file'

    case = out / 'actor-empty-step-cli'
    with RunCapture(pw, case, specimen(''), cli_args=[]) as run:
        rc = run.wait(timeout=30)
        created = effect.exists()
        (case / 'effect.json').write_text(json.dumps(dict(created=created)) + '\n')
        envelope = run.load_json()
    assert rc == 1 and envelope['result']['normalized_outcome'] == 'bad_request' and envelope['result']['ok'] is False, envelope
    assert envelope['data']['request_failure'] == failure, envelope
    assert envelope['data']['runner_client'] is not None, envelope
    refused(envelope['data']['runner_result'], created)

    case = out / 'actor-empty-step-xpc'
    case.mkdir()
    request = case / 'specimen.json'
    request.write_text(json.dumps(specimen('')) + '\n')
    with (case / 'capture.pwp').open('wb') as stdout, (case / 'stderr').open('wb') as stderr:
        result = subprocess.run([str(client), 'run', '--timeout-ms', '10000', service, str(request)],
                                stdout=stdout, stderr=stderr, timeout=20)
    created = effect.exists()
    (case / 'effect.json').write_text(json.dumps(dict(created=created)) + '\n')
    assert result.returncode == 0, result.returncode
    reply = host_reply(decode_porcelain((case / 'capture.pwp').read_bytes(), 'capture'), contract)
    (case / 'reply.json').write_text(json.dumps(reply, indent=2) + '\n')
    assert reply['producer']['contract'] == contract, reply
    refused(reply, created)

    case = out / 'actor-nonempty-step-cli'
    with RunCapture(pw, case, specimen('read'), cli_args=[]) as run:
        rc = run.wait(timeout=30)
        created = effect.is_file() and effect.read_bytes() == b''
        (case / 'effect.json').write_text(json.dumps(dict(created=created)) + '\n')
        envelope = run.load_json()
    reply = envelope['data']['runner_result']
    assert rc == 0 and reply['normalized_outcome'] == 'finished' and envelope['data'].get('request_failure') is None, envelope
    assert created, 'the nonempty neighbour did not run its first action'
    actor, = reply['actors']
    assert actor['setup_status'] == 'unapplied_declared' and actor['launch']['pid'] == actor['subprocess']['pid'], actor
    assert [step['step_id'] for step in reply['steps']] == ['effect', 'read'], reply['steps']
    effect.unlink()


def main():
    pw, out = Path(sys.argv[1]), Path(sys.argv[2])
    app = pw.parents[2]
    client = pw.with_name('pw-runner-client')
    with (app / 'Contents/XPCServices/PWRunner.xpc/Contents/Info.plist').open('rb') as stream:
        service = plistlib.load(stream)['CFBundleIdentifier']
    with tempfile.TemporaryDirectory(prefix='pw-request-contract-', dir='/private/tmp') as directory:
        effect = Path(directory) / 'created'
        base = dict(contract=build_context.candidate_contract(), specimen_id='input-contract',
                    policy=dict(format='sbpl', sbpl_source='(version 1) (allow default)'),
                    probe_plan=[dict(step_id='create',
                        sandbox_check=dict(operation='file-write-create', filter=dict(kind='path', value=str(effect))),
                        attempt=dict(kind='file', action='create', target=str(effect)))])

        def cli(name, specimen, *, accepted=False, error='', args=(), failure=None, raw=None, prediction=None, expected_effect=None):
            capture = RunCapture(pw, out / name, specimen, cli_args=[*args])
            if isinstance(raw, bytes):
                capture.request_path.write_bytes(raw)
            elif raw is not None:
                capture.request_path.write_text(raw)
            original = capture.request_path.read_bytes()
            with capture as run:
                rc = run.wait(timeout=30)
                env = run.load_json()
                assert run.request_path.read_bytes() == original, name
            observed = effect.is_file()
            (out / name / 'effect.json').write_text(json.dumps(dict(accepted=accepted, observed=observed)) + '\n')
            runner = env['data']['runner_result']
            if accepted:
                assert rc == 0 and env['result']['ok'] is True, env
                assert observed, f'{name}: accepted request produced no file effect'
                if expected_effect is not None:
                    assert effect.read_bytes() == expected_effect, name
                # The singular form's first step is the witness; the actor
                # form's accepted examples carry a step named `effect`.
                created = runner['steps'][0] if 'actors' not in specimen else next(s for s in runner['steps'] if s['step_id'] == 'effect')
                assert created['attempt']['outcome'] == 'ok', created
                if prediction:
                    assert created['sandbox_check']['outcome'] == prediction, created
                if (specimen.get('policy') or {}).get('capture_compiled_profile'):
                    assert runner['compiled_profile']['request_nonce'] == specimen['policy']['capture_nonce'], runner
                    assert runner['compiled_profile']['producer'] == 'worker' and runner['compiled_profile']['capture_stage'] == 'before_apply', runner
                    assert runner['sandboxed_after_apply'] is True, runner
                else:
                    assert runner.get('compiled_profile') is None, runner
                effect.unlink()
            else:
                assert rc == 1 and env['result']['normalized_outcome'] == 'bad_request' and env['result']['ok'] is False, env
                assert error in (env['result'].get('error') or ''), (name, env)
                diagnostic = env['data']['request_failure']
                assert isinstance(diagnostic['code'], str) and 'path' in diagnostic, env
                if failure is not None:
                    assert diagnostic == failure, (name, diagnostic, failure)
                assert not observed, f'{name}: refused intent still executed'
                if runner is not None:
                    assert runner['request_failure'] == diagnostic, env
                    assert runner['normalized_outcome'] == 'bad_request', runner
                    assert runner.get('runner_subprocess') is None and runner['steps'] == [], runner
                    assert (runner.get('phases') or [{}])[0].get('validator_subprocess') is None, runner
                else:
                    assert env['data']['runner_client'] is None, env

            return env

        (out / 'examples.json').write_bytes(CORPUS.read_bytes())
        for example in examples():
            specimen = materialize(example, effect, secrets.token_hex(16))
            expected = copy.deepcopy(example['expected'])
            for diagnostic in expected.values():
                if diagnostic and diagnostic.get('expected_contract') is True:
                    diagnostic['expected_contract'] = build_context.candidate_contract()
            cli('corpus-cli-' + example['id'], specimen, accepted=expected['cli'] is None,
                failure=expected['cli'], raw=example.get('raw_request'), prediction=example.get('prediction'))
            specimen = materialize(example, effect, secrets.token_hex(16))
            case = out / ('corpus-xpc-' + example['id']); case.mkdir()
            request = case / 'specimen.json'
            request.write_text(example['raw_request'] if 'raw_request' in example else json.dumps(specimen) + '\n')
            original = request.read_bytes()
            with (case / 'capture.pwp').open('wb') as stdout, (case / 'stderr').open('wb') as stderr:
                result = subprocess.run([str(client), 'run', '--timeout-ms', '10000', service, str(request)],
                                        stdout=stdout, stderr=stderr, timeout=20)
            assert request.read_bytes() == original, example['id']
            assert result.returncode == 0, example['id']
            reply = host_reply(decode_porcelain((case / 'capture.pwp').read_bytes(), 'capture'), build_context.candidate_contract())
            observed = effect.is_file()
            (case / 'effect.json').write_text(json.dumps(dict(observed=observed, expected=expected['xpc'] is None)) + '\n')
            if expected['xpc'] is None:
                assert reply['normalized_outcome'] == 'finished' and observed, (example['id'], reply)
                created = reply['steps'][0] if 'actors' not in specimen else next(s for s in reply['steps'] if s['step_id'] == 'effect')
                assert created['attempt']['outcome'] == 'ok', created
                if example.get('prediction'):
                    assert created['sandbox_check']['outcome'] == example['prediction'], created
                if (specimen.get('policy') or {}).get('capture_compiled_profile'):
                    assert reply['compiled_profile']['request_nonce'] == specimen['policy']['capture_nonce'], reply
                    assert reply['compiled_profile']['producer'] == 'worker' and reply['compiled_profile']['capture_stage'] == 'before_apply', reply
                    assert reply['sandboxed_after_apply'] is True, reply
                else:
                    assert reply.get('compiled_profile') is None, reply
                effect.unlink()
            else:
                assert reply['normalized_outcome'] == 'bad_request' and reply['request_failure'] == expected['xpc'], (example['id'], reply)
                assert not observed and reply['steps'] == [], reply
                assert reply.get('runner_subprocess') is None and (reply.get('phases') or [{}])[0].get('validator_subprocess') is None, reply

        composite_parameters(pw, out, directory, base)
        refusal_workflows(pw, client, service, out, effect, base, cli)

        # A completed application survives as its own observation when abnormal
        # worker completion makes the earlier compiler capture unavailable.
        interrupted = copy.deepcopy(base)
        interrupted['policy'].update(capture_compiled_profile=True, capture_nonce=secrets.token_hex(16))
        with SeamCapture(pw, out / 'capture_worker_death', interrupted,
                         controls={'worker_post_apply_kill_signal': 9},
                         scenario='bad_request.capture_worker_death', cli_args=[]) as run:
            assert run.wait(timeout=30) != 0
            reply = run.load_json()['data']['runner_result']
        assert reply['sandboxed_after_apply'] is True, reply
        assert reply['runner_subprocess']['term_signal'] == 9, reply
        receipt = reply['compiled_profile']
        assert receipt == dict(status='unavailable', reason='worker_not_complete',
                               worker_pid=reply['runner_subprocess']['pid']), receipt
        assert effect.is_file(), reply
        effect.unlink()
        capture_receipts(pw, out, effect, base)

        cli('selector_alias', dict(base, runner_mode='standard', required_entitlements=[]), accepted=True)
        cli('selector_nested', dict(base, runner=dict(mode='standard', required_entitlements=[])), accepted=True)
        cli('selector_null_option', dict(base, runner=None), accepted=True, args=['--runner-mode', 'standard'])

        for i, version in enumerate([1, 2, "test:foreign", None, '3', True, 3.5]):
            cli(f'version-{i}', changed(base, ['contract'], version), error='expected')
        missing = copy.deepcopy(base); del missing['contract']
        cli('missing_contract', missing, error='contract')
        legacy = dict(missing, schema_version=6, runner={'misspelled': True})
        cli('old_marker_only', legacy, error='contract', failure=dict(code='missing_field', path=['contract'], expected_contract=build_context.candidate_contract()))
        paths = [[], ['policy'], ['probe_plan', 0], ['probe_plan', 0, 'sandbox_check'],
                 ['probe_plan', 0, 'sandbox_check', 'filter'], ['probe_plan', 0, 'attempt']]
        for i, path in enumerate(paths):
            cli(f'unknown-{i}', changed(base, path + ['misspelled_intent'], True), error='misspelled_intent')
        cli('capture_typo', changed(base, ['policy', 'capture_compiled_profiel'], True), error='capture_compiled_profiel')
        cli('override_typo', dict(base, _test_overrides=dict(worker_timeuot_ms=1)), error='worker_timeuot_ms')
        cli('bad_parameter_type', changed(base, ['policy', 'params'], {'TARGET': 42}), error='policy.params.TARGET')
        cli('bad_optional_type', changed(base, ['probe_plan', 0, 'attempt', 'args'], 'argument'), error='attempt.args')
        cli('selector_typo', dict(base, runner=dict(servce='external')), error='servce')
        cli('selector_bad_entitlement', dict(base, required_entitlements=['required', 42]), error='required_entitlements[1]')
        cli('selector_bad_shape', dict(base, runner=False), failure=dict(code='type_mismatch', path=['runner']))
        cli('selector_bad_type', dict(base, runner=dict(mode=42)), error='runner.mode', args=['--runner-mode', 'standard'])
        cli('augment_bad_source', changed(base, ['policy'], dict(format='sbpl', sbpl_source=42,
            augments=['exec_baseline'])), error='policy.sbpl_source')

        # The XPC boundary must independently gate versions and reject intent
        # that only the controller can honor; the CLI's validation is insufficient.
        for name, specimen, error in [
            ('direct_current', base, None),
            ('direct_old_marker', legacy, 'missing_field'),
            ('direct_foreign', changed(base, ['contract'], 'test:foreign'), 'unsupported_contract'),
            ('direct_unknown', changed(base, ['policy', 'capture_compiled_profiel'], True), 'capture_compiled_profiel'),
            ('direct_selector', dict(base, runner=dict(mode='standard')), 'runner'),
            ('direct_augment', changed(base, ['policy', 'augments'], ['exec_baseline']), 'policy.augments'),
        ]:
            case = out / name; case.mkdir()
            request = case / 'specimen.json'; request.write_text(json.dumps(specimen) + '\n')
            with (case / 'capture.pwp').open('wb') as stdout, (case / 'stderr').open('wb') as stderr:
                result = subprocess.run([str(client), 'run', '--timeout-ms', '10000', service, str(request)],
                                        stdout=stdout, stderr=stderr, timeout=20)
            assert result.returncode == 0, name
            reply = host_reply(decode_porcelain((case / 'capture.pwp').read_bytes(), 'capture'), build_context.candidate_contract())
            assert reply['producer']['contract'] == build_context.candidate_contract(), reply
            if error is None:
                assert reply['normalized_outcome'] == 'finished' and effect.is_file(), reply
                effect.unlink()
            else:
                assert reply['normalized_outcome'] == 'bad_request' and error in reply['error'], reply
                if name in ('direct_old_marker', 'direct_foreign'):
                    assert reply['request_failure'] == dict(code=error, path=['contract'], expected_contract=build_context.candidate_contract()), reply
                assert reply.get('runner_subprocess') is None and reply['steps'] == [], reply
                assert not effect.exists(), name
        actor_empty_step_id(pw, client, service, out, directory)
    print('current requests execute; invalid versions, unknown fields and malformed intent refuse before attempts')


if __name__ == '__main__':
    main()
