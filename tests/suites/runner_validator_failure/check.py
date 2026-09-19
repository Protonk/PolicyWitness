"""CLI contract for preservation and association of partial validator evidence."""
import errno
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from run_capture import RunCapture
from consumer import recover_evidence, validate_evidence_shape

FIXTURE = Path(__file__).resolve().parents[2] / 'fixtures' / 'validator'


def install_fixture(out, case):
    out.mkdir(parents=True, exist_ok=True)
    validator = out / 'validator.py'
    shutil.copyfile(FIXTURE / 'validator.py', validator)
    validator.chmod(0o755)
    shutil.copyfile(FIXTURE / f'{case}.json', validator.with_suffix('.case.json'))
    return validator


def assert_transcript(raw, probes, case):
    lines = raw.splitlines()
    assert len(lines) == (3 if case == 'malformed' else 2), lines
    for line, index, outcome, rc, error in zip(lines[:2], (1, 0), ('deny', 'allow'), (1, 0), (1, 0)):
        verdict = json.loads(line)
        for key, value in probes[index].items():
            assert verdict[key] == value, (key, verdict, probes[index])
        assert (verdict['outcome'], verdict['rc'], verdict['errno']) == (outcome, rc, error), verdict
    if case == 'malformed':
        assert lines[-1] == 'invalid-verdict:' + probes[-1]['step_id'], lines
        try:
            json.loads(lines[-1])
        except ValueError:
            pass
        else:
            raise AssertionError('malformed transcript tail was valid JSON')


def check_fixture(out):
    for case in ('eof', 'malformed'):
        validator = install_fixture(out / case, case)
        probes = [{'step_id': secrets.token_hex(16), 'operation': operation,
                   'filter_type': 'PATH', 'filter_value': f'/fixture/{secrets.token_hex(8)}'}
                  for operation in ('file-write-data', 'file-write-data', 'file-read-data')]
        raw_input = ''.join(json.dumps(p) + '\n' for p in probes)
        result = subprocess.run([str(validator), '--batch', str(os.getpid())], input=raw_input,
                                capture_output=True, text=True, timeout=15)
        (out / case / 'direct.stdout').write_text(result.stdout)
        (out / case / 'direct.stderr').write_text(result.stderr)
        assert result.returncode == 0 and not result.stderr, result
        assert_transcript(result.stdout, probes, case)
        received = json.loads(validator.with_suffix('.received.json').read_text())
        assert received == {'target_pid': os.getpid(), 'probes': probes}, received
        assert validator.with_suffix('.emitted.ndjson').read_text() == result.stdout
    print('fixture controls: two verdicts in reverse order, exact probe metadata, EOF or malformed tail')


def check_cli(case, out, pw):
    validator = install_fixture(out, case)
    with tempfile.TemporaryDirectory(prefix='pw-validator-', dir='/private/tmp') as work:
        paths = [Path(work) / secrets.token_hex(8) for _ in range(3)]
        seeds = [secrets.token_bytes(64) for _ in paths]
        for i, (path, seed) in enumerate(zip(paths, seeds)):
            path.write_bytes(seed)
            (out / f'before_{i}.bin').write_bytes(seed)
        plan = [{
            'step_id': secrets.token_hex(12),
            'sandbox_check': {'operation': operation, 'filter': {'kind': 'path', 'value': str(path)}},
            'attempt': {'kind': 'file', 'action': action, 'target': str(path)},
        } for path, operation, action in zip(paths,
                ('file-write-data', 'file-write-data', 'file-read-data'),
                ('open_write', 'open_write', 'access'))]
        specimen = {
            'schema_version': 1, 'specimen_id': f'validator_failure_{case}',
            'policy': {'format': 'sbpl', 'sbpl_source': '(version 1)(allow default)'
                       '(deny file-write-data (literal (param "NO_WRITE")))'
                       '(deny file-read-data (literal (param "NO_READ")))',
                       'params': {'NO_WRITE': str(paths[1]), 'NO_READ': str(paths[2])}},
            'probe_plan': plan,
            '_test_overrides': {'validator_executable_path': str(validator)},
        }
        with RunCapture(pw, out, specimen,
                        cli_args=['--no-log-capture', '--timeout-ms', '15000']) as run:
            rc = run.wait(timeout=20)
            # Check real effects before relying on the envelope's attempt claims.
            after = [path.read_bytes() for path in paths]
            for i, data in enumerate(after):
                (out / f'after_{i}.bin').write_bytes(data)
            assert after[0] and after[0] != seeds[0], 'allowed write did not change the target'
            assert after[1:] == seeds[1:], 'denied write/access changed the protected files'
            envelope = run.load_json()
            runner = envelope['data']['runner_result']
            assert type(runner.get('schema_version')) is int and runner['schema_version'] == 7, runner
            assert not validate_evidence_shape(envelope), validate_evidence_shape(envelope)
            answers = recover_evidence(envelope)
            (out / 'consumer-answers.json').write_text(json.dumps(answers, indent=2) + '\n')
            ids = [s['step_id'] for s in plan]
            assert answers['comparison_groups']['agreement'] == ids[:1]
            assert answers['comparison_groups']['directional_consistency'] == ids[1:2]
            assert answers['comparison_groups']['unavailable'] == ids[2:]
            assert answers['failure_groups']['unattributed_failure'] == ids[1:]
            assert answers['failure_groups']['missing_result'] == []
            absent = answers['steps'][2]
            assert absent['prediction_missing_reason'] == 'validator_no_verdict'
            assert absent['attempt_missing_reason'] is None
            assert {'prediction:validator_no_verdict', 'sandbox_attribution_unestablished'} <= set(absent['comparison']['limitations'])
            assert absent['query']['native_rc'] is None
            assert absent['attempt']['outcome'] == 'access_failed'
            assert absent['attempt']['errno'] in (errno.EPERM, errno.EACCES)
            assert rc == 1 and envelope['result']['ok'] is False, envelope
            expected = 'validator_unavailable' if case == 'eof' else 'validator_decode_failure'
            assert runner['normalized_outcome'] == expected and runner['rc'] == 1, runner
            assert runner['test_overrides'] == specimen['_test_overrides'], runner
            worker = runner['runner_subprocess']
            assert worker['exit_code'] == 0 and worker.get('term_signal') is None, worker
            assert worker['partial_steps'] is False and worker['pid'] == runner['pid'], worker
            validator_status = runner['validator_subprocess']
            assert validator_status['pid'] > 0 and validator_status['exit_code'] == 0, validator_status
            assert validator_status.get('term_signal') is None, validator_status
            received = json.loads(validator.with_suffix('.received.json').read_text())
            probes = [{'step_id': step['step_id'], 'operation': step['sandbox_check']['operation'],
                       'filter_type': 'PATH', 'filter_value': step['attempt']['target']} for step in plan]
            assert received == {'target_pid': worker['pid'], 'probes': probes}, received
            assert_transcript(validator.with_suffix('.emitted.ndjson').read_text(), probes, case)
            if case == 'eof':
                assert 'returned 2' in runner['error'] and 'expected 3' in runner['error'], runner['error']
            else:
                assert 'parse failed' in runner['error'], runner['error']
                assert validator_status['decode_fault']['kind'] == 'json', validator_status
                import base64
                assert base64.b64decode(validator_status['decode_fault']['context_b64']).decode() == 'invalid-verdict:' + plan[-1]['step_id']
            steps = runner['steps']
            assert [s['step_id'] for s in steps] == [s['step_id'] for s in plan], steps
            for i, (step, outcome) in enumerate(zip(steps, ('ok', 'open_failed', 'access_failed'))):
                attempt = step['attempt']
                assert attempt['outcome'] == outcome, (step['step_id'], attempt)
                assert attempt['requested_path'] == str(paths[i]), attempt
                assert type(attempt['rc']) is int and (attempt['rc'] == 0) == (i == 0), attempt
                if i == 0:
                    assert attempt['errno'] is None and attempt['observed_path'] == str(paths[i]), attempt
                else:
                    assert attempt['errno'] in (errno.EPERM, errno.EACCES), attempt
                    assert attempt['error'], attempt
                prediction = step['sandbox_check']
                assert prediction['pid'] == worker['pid'], prediction
                assert prediction['operation'] == probes[i]['operation'], prediction
                assert prediction['filter_value'] == str(paths[i]), prediction
            for step, expected in zip(steps[:2], (('allow', 0, 0), ('deny', 1, 1))):
                prediction = step['sandbox_check']
                assert (prediction['outcome'], prediction['rc'], prediction['errno']) == expected, step
                assert step['drift'] is (False if expected[0] == 'allow' else None), step
                assert step['comparison']['conclusion'] == ('agreement' if expected[0] == 'allow' else 'directional_consistency'), step
            gap = steps[2]
            assert gap['sandbox_check']['outcome'] == 'error', gap
            assert 'no validator verdict' in gap['sandbox_check']['error'], gap
            assert gap['drift'] is None, 'missing prediction must have explicit drift:null'
            print(f'{case}: partial verdicts joined by ID, all three attempt outcomes/effects preserved, gap explicit')


if __name__ == '__main__':
    mode, out_arg, *args = sys.argv[1:]
    out = Path(out_arg).resolve()
    if mode == 'fixture':
        check_fixture(out)
    else:
        assert mode in ('eof', 'malformed'), mode
        check_cli(mode, out, *args)
