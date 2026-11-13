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
from request_examples import CORPUS, LESSON_SOURCES, examples, materialize
from porcelain import decode as decode_porcelain
from runner_client_capture import host_reply


def changed(specimen, path, value):
    result = copy.deepcopy(specimen)
    node = result
    for part in path[:-1]:
        node = node[part]
    node[path[-1]] = value
    return result


# Reviewed direct-host observations on the supported macOS build. Each order
# keeps an explicit expectation; controller-owned selectors refuse as a whole.
# A missing entry refuses completion after retaining every observation.
HOST_DUPLICATE_EXPECTATIONS = {
    'contract-ab': 'first',
    'contract-ba': 'first',
    'policy-ab': 'first',
    'policy-ba': 'first',
    'step_id-ab': 'first',
    'step_id-ba': 'first',
    'target-ab': 'first',
    'target-ba': 'first',
    'selector-ab': dict(code='unknown_field', path=['runner']),
    'selector-ba': dict(code='unknown_field', path=['runner']),
    'selector_mode-ab': dict(code='unknown_field', path=['runner']),
    'selector_mode-ba': dict(code='unknown_field', path=['runner']),
}


def duplicate_entries(pw, client, service, out, directory):
    out = out / 'duplicate-keys'
    out.mkdir()
    contract = build_context.candidate_contract()
    targets = [Path(directory) / 'duplicate-a', Path(directory) / 'duplicate-b']
    source = '(version 1) (allow default)'
    base = dict(contract=contract, specimen_id='duplicate-keys',
                policy=dict(format='sbpl', sbpl_source=source),
                probe_plan=[dict(step_id='create',
                    sandbox_check=dict(operation='file-write-create', filter=dict(kind='path', value=str(targets[0]))),
                    attempt=dict(kind='file', action='create', target=str(targets[0])))])
    rows = [
        ('contract', ['contract'], contract, 'test:duplicate-foreign'),
        ('policy', ['policy'], dict(format='sbpl', sbpl_source=source + '\n; policy a\n'),
                              dict(format='sbpl', sbpl_source=source + '\n; policy b\n')),
        ('step_id', ['probe_plan', 0, 'step_id'], 'step-a', 'step-b'),
        ('target', ['probe_plan', 0, 'attempt', 'target'], str(targets[0]), str(targets[1])),
        ('selector', ['runner'], dict(mode='standard'), False),
        ('selector_mode', ['runner', 'mode'], 'standard', 42),
    ]
    observations, unpinned = [], []

    def record(value):
        observations.append(value)
        (out / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n')

    def expected(label, selected, entry):
        failure = None
        if label == 'contract' and selected == 1:
            failure = dict(code='unsupported_contract', path=['contract'], expected_contract=contract)
        if label in ('selector', 'selector_mode'):
            if entry == 'xpc':
                failure = dict(code='unknown_field', path=['runner'])
            elif selected == 1:
                failure = dict(code='type_mismatch', path=['runner'] if label == 'selector' else ['runner', 'mode'])
        if failure is not None:
            return dict(outcome='bad_request', failure=failure,
                        boundary='controller' if entry == 'cli' else 'host', effects=[])
        policy_source = source + ('\n; policy a\n' if selected == 0 else '\n; policy b\n') if label == 'policy' else source
        target = selected if label == 'target' else 0
        return dict(outcome='finished', boundary='host', effects=[target],
                    step_id=('step-a' if selected == 0 else 'step-b') if label == 'step_id' else 'create',
                    policy_sha256=hashlib.sha256(policy_source.encode()).hexdigest(),
                    target=str(targets[target]))

    def run(entry, name, specimen, raw):
        case = out / (entry + '-' + name)
        assert not any(path.exists() for path in targets), 'fresh effect targets required'
        if entry == 'cli':
            capture = RunCapture(pw, case, specimen, cli_args=[])
            capture.request_path.write_text(raw)
            original = capture.request_path.read_bytes()
            with capture as process:
                rc = process.wait(timeout=30)
                envelope = process.load_json()
            assert capture.request_path.read_bytes() == original
            reply = envelope['data']['runner_result']
            failure = envelope['data'].get('request_failure')
            outcome = envelope['result']['normalized_outcome']
            boundary = 'host' if reply is not None else 'controller'
            if reply is None:
                assert envelope['data']['runner_client'] is None, envelope
            else:
                assert envelope['data']['runner_client'] is not None, envelope
            assert rc == (0 if outcome == 'finished' else 1), envelope
            assert envelope['result']['ok'] is (outcome == 'finished'), envelope
        else:
            case.mkdir()
            request = case / 'specimen.json'
            request.write_text(raw)
            original = request.read_bytes()
            argv = [str(client), 'run', '--timeout-ms', '10000', service, str(request)]
            with (case / 'capture.pwp').open('wb') as stdout, (case / 'stderr').open('wb') as stderr:
                process = subprocess.run(argv, stdout=stdout, stderr=stderr, timeout=20)
            (case / 'command.json').write_text(json.dumps(dict(argv=argv, returncode=process.returncode), indent=2) + '\n')
            assert process.returncode == 0, (name, process.returncode)
            assert request.read_bytes() == original
            reply = host_reply(decode_porcelain((case / 'capture.pwp').read_bytes(), 'capture'), contract)
            (case / 'reply.json').write_text(json.dumps(reply, indent=2) + '\n')
            failure, outcome, boundary = reply.get('request_failure'), reply['normalized_outcome'], 'host'
        effects = [i for i, path in enumerate(targets) if path.exists()]
        (case / 'effects.json').write_text(json.dumps(dict(created=effects), indent=2) + '\n')
        for i in effects:
            assert targets[i].is_file() and targets[i].read_bytes() == b'', 'create must leave an empty file'
        if reply is not None:
            assert reply['producer']['contract'] == contract, reply
        if outcome == 'bad_request':
            assert isinstance(failure, dict) and isinstance(failure.get('code'), str) and isinstance(failure.get('path'), list), failure
            assert effects == [], (name, effects)
            if reply is not None:
                assert reply.get('request_failure') == failure, reply
                assert reply.get('runner_subprocess') is None and reply['steps'] == [], reply
                assert all(p.get('validator_subprocess') is None for p in reply.get('phases', [])), reply
            observed = dict(outcome=outcome, failure=failure, boundary=boundary, effects=effects)
        else:
            assert outcome == 'finished' and failure is None, (name, outcome, failure)
            assert reply['sandboxed_after_apply'] is True, reply
            step, = reply['steps']
            assert step['attempt']['outcome'] == 'ok' and step['attempt']['result_source'] == 'worker', step
            assert reply['runner_subprocess']['reaped'] is True, reply
            observed = dict(outcome=outcome, boundary=boundary, effects=effects,
                            step_id=step['step_id'], policy_sha256=reply['policy_sha256'],
                            target=step['attempt']['requested_path'])
        for i in effects:
            targets[i].unlink()
        return observed

    for label, path, first, second in rows:
        skeleton = copy.deepcopy(base)
        if label == 'selector_mode':
            skeleton['runner'] = {}
        for entry in ('cli', 'xpc'):
            # Canonical twins use independently authored expectations; none of
            # their observed output becomes the duplicate-row oracle.
            for selected, value in enumerate((first, second)):
                specimen = changed(skeleton, path, value)
                actual = run(entry, f'{label}-canonical-{selected}', specimen, json.dumps(specimen))
                wanted = expected(label, selected, entry)
                record(dict(entry=entry, label=label, canonical=selected, expected=wanted, observed=actual))
                assert actual == wanted, (entry, label, selected, actual, wanted)
            for order, indices in [('ab', [0, 1]), ('ba', [1, 0])]:
                specimen = changed(skeleton, path, '__PW_DUPLICATE_MEMBER__')
                raw = json.dumps(specimen)
                key = json.dumps(path[-1])
                needle = key + ': "__PW_DUPLICATE_MEMBER__"'
                assert raw.count(needle) == 1
                values = [first, second]
                raw = raw.replace(needle, ', '.join(key + ': ' + json.dumps(values[i]) for i in indices), 1)
                actual = run(entry, label + '-' + order, specimen, raw)
                possibilities = [expected(label, i, entry) for i in indices]
                if entry == 'cli':
                    record(dict(entry=entry, label=label, order=order, expected=possibilities[1], observed=actual))
                    assert actual == possibilities[1], (entry, label, order, actual, possibilities[1])
                else:
                    matches = [i for i, value in enumerate(possibilities) if actual == value]
                    name = label + '-' + order
                    wanted = HOST_DUPLICATE_EXPECTATIONS.get(name)
                    record(dict(entry=entry, label=label, order=order, independently_expected=possibilities,
                                observed=actual, matching_positions=matches, pinned=wanted))
                    if wanted is None:
                        # Selection and whole-input refusal are both still
                        # observations to settle. Neither silently passes.
                        unpinned.append(dict(case=name, observed=actual, matching_positions=matches))
                    elif wanted in ('first', 'last'):
                        assert actual == possibilities[0 if wanted == 'first' else 1], (name, actual, wanted)
                    else:
                        assert isinstance(wanted, dict) and isinstance(wanted.get('code'), str), (name, wanted)
                        assert actual == dict(outcome='bad_request', failure=wanted, boundary='host', effects=[]), (name, actual, wanted)
    (out / 'unresolved-host-precedence.json').write_text(json.dumps(unpinned, indent=2) + '\n')
    assert not unpinned, ('review direct-host receipts and pin HOST_DUPLICATE_EXPECTATIONS; no precedence is assumed', unpinned)


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
            if failure is None:
                profile = reply['compiled_profile']
                assert profile['status'] == 'captured' and profile['producer'] == 'worker', profile
                assert profile['capture_stage'] == 'before_apply', profile
                assert profile['request_nonce'] == specimen['policy']['capture_nonce'], profile
                assert profile['worker_pid'] == reply['runner_subprocess']['pid'], profile
                assert profile['source_sha256'] == hashlib.sha256(base['policy']['sbpl_source'].encode()).hexdigest(), profile
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



def emitted_lessons(pw, out, effect, cli):
    """Submit the selected app's emitted lesson documents unchanged through `run`.

    The app supplies each document. The expected admission or refusal and the
    file effect remain the corpus row's, authored apart from the emitter.
    """
    sources = {case['id']: case['request_source'] for case in json.loads(CORPUS.read_text())
               if 'request_source' in case}
    # Every app-owned input needs a row; an absent row must not pass by omission.
    assert set(sources.values()) == LESSON_SOURCES, sources
    for example in examples():
        if example['id'] not in sources:
            continue
        name = 'lesson-emitted-' + example['id']
        directory = out / name; directory.mkdir()
        assert not effect.exists(), name
        emitted = subprocess.run([str(pw), 'lesson', Path(sources[example['id']]).stem, '--target', str(effect)],
                                 stdin=subprocess.DEVNULL, capture_output=True, timeout=20)
        (directory / 'lesson.stdout').write_bytes(emitted.stdout)
        (directory / 'lesson.stderr').write_bytes(emitted.stderr)
        (directory / 'lesson.exit').write_text(f'{emitted.returncode}\n')
        assert emitted.returncode == 0 and emitted.stderr == b'', (name, emitted.returncode, emitted.stderr)
        expected = example['expected']['cli']
        cli(name, json.loads(emitted.stdout), accepted=expected is None, failure=expected,
            raw=emitted.stdout, prediction=example.get('prediction'))
        assert (directory / 'specimen.json').read_bytes() == emitted.stdout, name


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
            cli('lesson-cli-' + example['id'], specimen, accepted=expected['cli'] is None,
                failure=expected['cli'], raw=example.get('raw_request'), prediction=example.get('prediction'))
            specimen = materialize(example, effect, secrets.token_hex(16))
            case = out / ('lesson-xpc-' + example['id']); case.mkdir()
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

        emitted_lessons(pw, out, effect, cli)
        composite_parameters(pw, out, directory, base)
        refusal_workflows(pw, client, service, out, effect, base, cli)

        # A completed application survives as its own observation when abnormal
        # worker completion makes the earlier compiler capture unavailable.
        interrupted = copy.deepcopy(base)
        interrupted['policy'].update(capture_compiled_profile=True, capture_nonce=secrets.token_hex(16))
        interrupted['_test_overrides'] = {'worker_post_apply_kill_signal': 9}
        with RunCapture(pw, out / 'capture_worker_death', interrupted, cli_args=[]) as run:
            assert run.wait(timeout=30) != 0
            reply = run.load_json()['data']['runner_result']
        assert reply['sandboxed_after_apply'] is True, reply
        assert reply['runner_subprocess']['term_signal'] == 9, reply
        receipt = reply['compiled_profile']
        assert receipt['status'] == 'unavailable' and receipt['reason'] == 'worker_not_complete', receipt
        assert all(receipt.get(key) is None for key in ('producer', 'capture_stage', 'bytecode_b64')), receipt
        assert effect.is_file(), reply
        effect.unlink()

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
        duplicate_entries(pw, client, service, out, directory)
    print('current requests execute; invalid versions, unknown fields and malformed intent refuse before attempts')


if __name__ == '__main__':
    main()
