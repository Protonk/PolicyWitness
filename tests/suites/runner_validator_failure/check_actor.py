"""Actor-form collection failures through the signed CLI.

One actor, one phase and one write, with the actor's sandbox mode `apply` or
`unapplied` and the validator a nonexistent path or a transcript that prints
one line that is not JSON. A failed collection selects the same failed summary
in both modes; an unapplied actor whose collection succeeds stays `finished`.
Every row is evaluated and its problems are reported together.
"""
import base64
import errno
import json
from pathlib import Path
import secrets
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import build_context
import consumer
from lifecycle_oracle import check_record
from run_capture import RunCapture
from seam_invocation import SeamCapture

from check import install_fixture

HOSTILE = '/nonexistent/pw-validator-not-real'
ROWS = [('apply', 'spawn'), ('unapplied', 'spawn'), ('apply', 'decode'), ('unapplied', 'decode'), ('unapplied', 'none')]
OUTCOME = {'none': 'finished', 'spawn': 'validator_spawn_failed', 'decode': 'validator_decode_failure'}


def specimen(mode, target):
    sandbox = ({'mode': 'apply', 'policy': {'format': 'sbpl', 'sbpl_source': '(version 1)(allow default)'}}
               if mode == 'apply' else {'mode': 'unapplied'})
    return {'contract': build_context.candidate_contract(), 'specimen_id': f'actor_validator_failure_{mode}',
            'actors': [{'actor_id': 'subject', 'sandbox': sandbox}],
            'phases': [{'phase_id': 'main', 'actor_id': 'subject', 'actions': [{
                'step_id': 'write',
                'sandbox_check': {'operation': 'file-write-data', 'filter': {'kind': 'path', 'value': str(target)}},
                'attempt': {'kind': 'file', 'action': 'open_write', 'target': str(target)}}]}]}


def collection_row(pw, out, work, mode, failure):
    """Run one specimen; return the list of ways its evidence departs from the expectation."""
    name = f'{mode}-{failure}'
    case_out = out / name
    target = work / name
    seed = secrets.token_bytes(64)
    target.write_bytes(seed)
    spec = specimen(mode, target)
    validator = None
    if failure == 'none':
        capture = RunCapture(pw, case_out / 'run', spec, cli_args=[])
        controls = None
    else:
        if failure == 'decode':
            validator = install_fixture(case_out / 'validator', 'malformed_only')
        controls = {'validator_executable_path': HOSTILE if validator is None else str(validator)}
        capture = SeamCapture(pw, case_out / 'run', spec, controls=controls,
                              scenario='actor_validator_failure.' + name, cli_args=[])
    with capture as run:
        rc = run.wait(timeout=40)
        # The file is read before the envelope's attempt claims are.
        after = target.read_bytes()
        (case_out / 'effect.json').write_text(json.dumps(dict(before_hex=seed.hex(), after_hex=after.hex())) + '\n')
        envelope = run.load_json()

    problems = []

    def check(label, actual, wanted):
        if actual != wanted:
            problems.append(f'{label}: observed {actual!r}, expected {wanted!r}')

    failed = failure != 'none'
    expected = OUTCOME[failure]
    check('write changed the target', bool(after) and after != seed, True)
    check('CLI exit status', rc, 1 if failed else 0)
    result = envelope['result']
    check('result', (result['normalized_outcome'], result['ok'], result['exit_code']), (expected, not failed, 1 if failed else 0))
    runner = envelope['data']['runner_result']
    check('reply summary', (runner['normalized_outcome'], runner['rc']), (expected, 1 if failed else 0))
    check('reply test_overrides', runner.get('test_overrides'), controls)
    check('consumer.validate', consumer.validate(envelope, build_context.candidate_contract()), [])
    check('lifecycle oracle', check_record(envelope, build_context.candidate_contract()), [])

    actor, = runner['actors']
    check('actor mode and setup', (actor['mode'], actor['setup_status']),
          (mode, 'applied' if mode == 'apply' else 'unapplied_declared'))
    check('actor application', (actor.get('applied'), actor['application_count']), (True, 1) if mode == 'apply' else (None, 0))
    worker = actor['subprocess']
    check('actor worker ending', (worker['reaped'], worker.get('exit_code'), worker.get('term_signal')), (True, 0, None))

    phase, = runner['phases']
    ordering = phase['ordering']
    check('phase collection', (phase['collection_status'], phase['arrival_observed'], phase['completion_observed']),
          ('collected', True, True))
    check('phase release', (ordering['collection_closed_before_proceed'], ordering['proceed_set'], ordering['proceed_observed'],
                            ordering['protocol_violations']), (True, True, True, []))
    check('validator disposition', ordering['validator_disposition'], 'not_spawned' if failure == 'spawn' else 'reaped')
    process = phase.get('validator_subprocess')
    spawn = phase.get('validator_spawn_failure')
    if failure == 'spawn':
        check('validator subprocess', process, None)
        check('spawn failure record', spawn and (spawn['origin'], spawn['operation'], spawn['executable_path'], spawn['return_code']),
              ('runner_host', 'posix_spawn', HOSTILE, errno.ENOENT))
        check('error names the refused path', HOSTILE in (runner.get('error') or ''), True)
    else:
        check('spawn failure record', spawn, None)
        check('validator ending', process and (process['reaped'], process.get('exit_code'), process.get('term_signal')), (True, 0, None))
    probe = {'step_id': 'write', 'operation': 'file-write-data', 'filter_type': 'PATH', 'filter_value': str(target)}
    if failure == 'decode':
        emitted = validator.with_suffix('.emitted.ndjson').read_bytes()
        check('transcript', emitted, b'invalid-verdict:write\n')
        check('validator received', json.loads(validator.with_suffix('.received.json').read_text()),
              {'target_pid': actor['launch']['pid'], 'probes': [probe]})
        fault = (process or {}).get('decode_fault') or {}
        check('decode fault', (fault.get('origin'), fault.get('kind'), fault.get('byte_offset'), fault.get('frame_bytes')),
              ('runner_host', 'json', 0, len(emitted) - 1))
        check('decode fault context', base64.b64decode(fault.get('context_b64', '')), emitted[:-1])
        check('accepted records', (process or {}).get('records') or [], [])
    if failure == 'none':
        check('accepted records', [(r['step_id'], r['outcome'], r['rc']) for r in process['records']], [('write', 'allow', 0)])
        check('association issues and faults', (process['association_issues'], process.get('decode_fault'), process.get('io_error')),
              ([], None, None))

    step, = runner['steps']
    attempt, query, comparison = step['attempt'], step['sandbox_check'], step['comparison']
    check('step owner', (step['step_id'], step['actor_id'], step['phase_id']), ('write', 'subject', 'main'))
    check('attempt', (attempt['result_source'], attempt['outcome'], attempt['rc']), ('worker', 'ok', 0))
    check('observation', comparison['observation'], 'succeeded')
    if failed:
        check('query', (query['result_source'], query.get('native_rc'), query.get('missing_reason')),
              ('synthetic', None, 'validator_not_invoked' if failure == 'spawn' else 'validator_no_verdict'))
        check('order', comparison['order'], 'unestablished')
    else:
        check('query', (query['result_source'], query['outcome'], query.get('native_rc')), ('validator', 'allow', 0))
        check('order', comparison['order'], 'query_first')
    return problems


def main(pw, out):
    failures = {}
    with tempfile.TemporaryDirectory(prefix='pw-actor-validator-', dir='/private/tmp') as work:
        for mode, failure in ROWS:
            problems = collection_row(pw, out, Path(work), mode, failure)
            print(('PASS' if not problems else 'FAIL'), mode, failure, flush=True)
            for problem in problems:
                print('    ' + problem, flush=True)
            if problems:
                failures[f'{mode}-{failure}'] = problems
    (out / 'rows.json').write_text(json.dumps(dict(rows=[f'{m}-{f}' for m, f in ROWS], failures=failures), indent=2) + '\n')
    assert not failures, sorted(failures)
    print('a failed actor-phase collection selects the summary in both sandbox modes; the all-success unapplied actor finishes')


if __name__ == '__main__':
    pw, out_arg = sys.argv[1:]
    main(pw, Path(out_arg).resolve())
