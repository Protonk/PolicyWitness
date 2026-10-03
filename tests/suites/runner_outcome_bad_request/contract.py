"""Accepted input through the signed CLI and direct XPC, with an independent file effect."""
import copy
import json
from pathlib import Path
import plistlib
import secrets
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
from contract import REQUEST_SCHEMA, RESPONSE_SCHEMA
from run_capture import RunCapture
from request_examples import CORPUS, examples, materialize


def changed(specimen, path, value):
    result = copy.deepcopy(specimen)
    node = result
    for part in path[:-1]:
        node = node[part]
    node[path[-1]] = value
    return result


def main():
    pw, out = Path(sys.argv[1]), Path(sys.argv[2])
    app = pw.parents[2]
    client = pw.with_name('pw-runner-client')
    with (app / 'Contents/XPCServices/PWRunner.xpc/Contents/Info.plist').open('rb') as stream:
        service = plistlib.load(stream)['CFBundleIdentifier']
    with tempfile.TemporaryDirectory(prefix='pw-request-contract-', dir='/private/tmp') as directory:
        effect = Path(directory) / 'created'
        base = dict(schema_version=REQUEST_SCHEMA, specimen_id='input-contract',
                    policy=dict(format='sbpl', sbpl_source='(version 1) (allow default)'),
                    probe_plan=[dict(step_id='create',
                        sandbox_check=dict(operation='file-write-create', filter=dict(kind='path', value=str(effect))),
                        attempt=dict(kind='file', action='create', target=str(effect)))])

        def cli(name, specimen, *, accepted=False, error='', args=(), failure=None, raw=None, prediction=None):
            capture = RunCapture(pw, out / name, specimen, cli_args=['--no-log-capture', *args])
            if raw is not None:
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
                assert runner['steps'][0]['attempt']['outcome'] == 'ok', runner
                if prediction:
                    assert runner['steps'][0]['sandbox_check']['outcome'] == prediction, runner
                if specimen['policy'].get('capture_applied_profile'):
                    assert runner['applied_profile']['request_nonce'] == specimen['policy']['capture_nonce'], runner
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
                    assert runner.get('validator_subprocess') is None, runner
                else:
                    assert env['data']['runner_client'] is None, env

        (out / 'examples.json').write_bytes(CORPUS.read_bytes())
        for example in examples():
            specimen = materialize(example, effect, secrets.token_hex(16))
            expected = example['expected']
            cli('lesson-cli-' + example['id'], specimen, accepted=expected['cli'] is None,
                failure=expected['cli'], raw=example.get('raw_request'), prediction=example.get('prediction'))
            specimen = materialize(example, effect, secrets.token_hex(16))
            case = out / ('lesson-xpc-' + example['id']); case.mkdir()
            request = case / 'specimen.json'
            request.write_text(example['raw_request'] if 'raw_request' in example else json.dumps(specimen) + '\n')
            original = request.read_bytes()
            with (case / 'reply.json').open('wb') as stdout, (case / 'stderr').open('wb') as stderr:
                result = subprocess.run([str(client), 'run', '--timeout-ms', '10000', service, str(request)],
                                        stdout=stdout, stderr=stderr, timeout=20)
            assert request.read_bytes() == original, example['id']
            assert result.returncode == 0, example['id']
            reply = json.loads((case / 'reply.json').read_text())
            observed = effect.is_file()
            (case / 'effect.json').write_text(json.dumps(dict(observed=observed, expected=expected['xpc'] is None)) + '\n')
            if expected['xpc'] is None:
                assert reply['normalized_outcome'] == 'ok' and observed, (example['id'], reply)
                if example.get('prediction'):
                    assert reply['steps'][0]['sandbox_check']['outcome'] == example['prediction'], reply
                if specimen['policy'].get('capture_applied_profile'):
                    assert reply['applied_profile']['request_nonce'] == specimen['policy']['capture_nonce'], reply
                effect.unlink()
            else:
                assert reply['normalized_outcome'] == 'bad_request' and reply['request_failure'] == expected['xpc'], (example['id'], reply)
                assert not observed and reply['steps'] == [], reply
                assert reply.get('runner_subprocess') is None and reply.get('validator_subprocess') is None, reply

        cli('selector_alias', dict(base, runner_mode='standard', required_entitlements=[]), accepted=True)
        cli('selector_nested', dict(base, runner=dict(mode='standard', required_entitlements=[])), accepted=True)
        cli('selector_null_option', dict(base, runner=None), accepted=True, args=['--runner-mode', 'standard'])

        for i, version in enumerate([1, 2, REQUEST_SCHEMA + 1, None, '3', True, 3.5]):
            cli(f'version-{i}', changed(base, ['schema_version'], version), error='expected')
        missing = copy.deepcopy(base); del missing['schema_version']
        cli('missing_version', missing, error='schema_version')
        paths = [[], ['policy'], ['probe_plan', 0], ['probe_plan', 0, 'sandbox_check'],
                 ['probe_plan', 0, 'sandbox_check', 'filter'], ['probe_plan', 0, 'attempt']]
        for i, path in enumerate(paths):
            cli(f'unknown-{i}', changed(base, path + ['misspelled_intent'], True), error='misspelled_intent')
        cli('capture_typo', changed(base, ['policy', 'capture_applied_profiel'], True), error='capture_applied_profiel')
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
            ('direct_version', changed(base, ['schema_version'], 1), 'unsupported request schema'),
            ('direct_unknown', changed(base, ['policy', 'capture_applied_profiel'], True), 'capture_applied_profiel'),
            ('direct_selector', dict(base, runner=dict(mode='standard')), 'runner'),
            ('direct_augment', changed(base, ['policy', 'augments'], ['exec_baseline']), 'policy.augments'),
        ]:
            case = out / name; case.mkdir()
            request = case / 'specimen.json'; request.write_text(json.dumps(specimen) + '\n')
            with (case / 'reply.json').open('wb') as stdout, (case / 'stderr').open('wb') as stderr:
                result = subprocess.run([str(client), 'run', '--timeout-ms', '10000', service, str(request)],
                                        stdout=stdout, stderr=stderr, timeout=20)
            assert result.returncode == 0, name
            reply = json.loads((case / 'reply.json').read_text())
            assert reply['schema_version'] == RESPONSE_SCHEMA, reply
            if error is None:
                assert reply['normalized_outcome'] == 'ok' and effect.is_file(), reply
                effect.unlink()
            else:
                assert reply['normalized_outcome'] == 'bad_request' and error in reply['error'], reply
                assert reply.get('runner_subprocess') is None and reply['steps'] == [], reply
                assert not effect.exists(), name
    print('current requests execute; invalid versions, unknown fields and malformed intent refuse before attempts')


if __name__ == '__main__':
    main()
