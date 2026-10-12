"""Public ordinary phases and bounded collection; fresh native file observations."""
import copy
import errno
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import consumer
from run_capture import RunCapture


def action(identity, path, operation='file-read-data', attempt='access'):
    return {'step_id': identity,
            'sandbox_check': {'operation': operation, 'filter': {'kind': 'path', 'value': str(path)}},
            'attempt': {'kind': 'file', 'action': attempt, 'target': str(path)}}


def run(pw, out, name, actions, overrides=None, expected_rc=0):
    spec = {'schema_version': 4, 'specimen_id': name,
            'policy': {'format': 'sbpl', 'sbpl_source': '(version 1)(allow default)'},
            'phases': [{'phase_id': f'p{i}', 'actions': a if isinstance(a, list) else [a]} for i, a in enumerate(actions)]}
    if overrides is not None:
        spec['_test_overrides'] = overrides
    with RunCapture(pw, out / name, spec, cli_args=['--no-log-capture']) as captured:
        assert captured.wait(timeout=30) == expected_rc
        envelope = captured.load_json()
    errors = consumer.validate(envelope)
    assert not errors, errors
    reply = envelope['data']['runner_result']
    assert reply.get('test_overrides') == overrides
    phases = reply['phases']
    assert [p['ordinal'] for p in phases] == list(range(1, len(actions) + 1))
    assert all(p['arrival_observed'] and p['completion_observed'] for p in phases)
    assert all(all(p['ordering'][k] for k in ('collection_closed_before_proceed', 'proceed_set', 'proceed_observed', 'worker_lifetime_established')) for p in phases)
    assert reply['runner_subprocess']['reaped'] is True
    return envelope, reply


def main():
    pw, destination = sys.argv[1:]
    out = Path(destination).resolve()
    removed, stable = out / 'removed', out / 'stable'
    removed.write_bytes(b'phase unlink witness\n')
    stable.write_bytes(b'phase stable witness\n')
    envelope, reply = run(pw, out, 'ordinary', [
        action('unlink', removed, 'file-write-unlink', 'unlink'),
        action('missing', removed), action('stable', stable)])
    assert not removed.exists() and stable.read_bytes() == b'phase stable witness\n'
    (out / 'independent-effects.json').write_text(json.dumps({'removed_absent': not removed.exists(), 'stable_hex': stable.read_bytes().hex()}) + '\n')
    first, missing, last = reply['steps']
    assert first['attempt']['rc'] == 0 and first['comparison']['order'] == 'query_first'
    assert missing['sandbox_check']['outcome'] == 'prediction_unavailable'
    assert missing['comparison']['order'] == 'unestablished'
    assert 'query_plan:path_unresolved_at_planning' in missing['comparison']['limitations']
    assert missing['attempt']['errno'] == errno.ENOENT
    assert reply['phases'][1]['collection_status'] == 'not_needed'
    assert 'validator_subprocess' not in reply['phases'][1]
    assert last['comparison']['order'] == 'query_first' and last['attempt']['rc'] == 0
    validators = [reply['phases'][i]['validator_subprocess'] for i in (0, 2)]
    assert validators[0]['pid'] != validators[1]['pid']
    assert [v['expected_step_ids'] for v in validators] == [['unlink'], ['stable']]
    assert all(v['reaped'] for v in validators)

    def rejected(name, mutate):
        changed = copy.deepcopy(envelope)
        mutate(changed['data']['runner_result'])
        errors = consumer.validate(changed)
        assert errors, name
        return {'control': name, 'errors': errors}

    controls = [
        rejected('wrong_ordinal', lambda r: r['phases'][2].update(ordinal=2)),
        rejected('wrong_phase', lambda r: r['steps'][2].update(phase_id='p0')),
        rejected('missing_preceding_completion', lambda r: r['phases'][0].update(completion_observed=False)),
        rejected('earlier_records_cannot_supply_later_query', lambda r: r['phases'][2].update(validator_subprocess=r['phases'][0]['validator_subprocess'])),
        rejected('duplicate_phase', lambda r: r['phases'][2].update(phase_id='p0')),
        rejected('action_partition', lambda r: r['phases'][2].update(action_ids=['missing'])),
    ]
    for field in ('ordering', 'action_ids', 'collection_status', 'ordinal', 'validator_subprocess'):
        controls.append(rejected('malformed_' + field, lambda r, key=field: r['phases'][2].update({key: 7 if key != 'ordinal' else []})))
    (out / 'consumer-controls.json').write_text(json.dumps(controls, indent=2) + '\n')

    recreated = out / 'recreated'
    recreated.write_bytes(b'original content before phase intervention')
    _, recreation = run(pw, out, 'unlink_recreate', [
        [action('remove', recreated, 'file-write-unlink', 'unlink'),
         action('recreate', recreated, 'file-write-data', 'create')],
        action('later_query', recreated)])
    assert recreated.read_bytes() == b''
    assert all(s['attempt']['rc'] == 0 for s in recreation['steps'])
    assert recreation['steps'][2]['comparison']['order'] == 'query_first'
    assert recreation['steps'][0]['phase_id'] != recreation['steps'][2]['phase_id']
    assert recreation['phases'][0]['completion_observed'] and recreation['phases'][1]['arrival_observed']
    assert recreation['phases'][1]['validator_subprocess']['expected_step_ids'] == ['later_query']
    (out / 'recreation-effect.json').write_text(json.dumps({'present': recreated.exists(), 'length': recreated.stat().st_size}) + '\n')

    validator = out / 'bounded-validator'
    command = ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2',
               str(ROOT / 'tests/fixtures/worker_lifecycle/validator.c'), '-o', str(validator)]
    built = subprocess.run(command, capture_output=True, text=True, timeout=60)
    (out / 'fixture-build.json').write_text(json.dumps({'argv': command, 'rc': built.returncode, 'stdout': built.stdout, 'stderr': built.stderr}, indent=2) + '\n')
    assert built.returncode == 0, built.stderr
    warmed = subprocess.run([str(validator)], input=b'', capture_output=True, timeout=30)
    assert warmed.returncode == 90
    overrides = {'validator_executable_path': str(validator), 'validator_total_timeout_ms': 100}
    _, exhausted = run(pw, out, 'aggregate', [action(f's{i}', stable, 'io_hang') for i in range(3)], overrides, 1)
    assert exhausted['normalized_outcome'] == 'validator_no_reply'
    assert exhausted['phases'][0]['validator_subprocess']['stdout_collection_stop'] == 'deadline'
    assert exhausted['phases'][0]['validator_subprocess']['reaped'] is True
    assert all(p['collection_status'] == 'budget_exhausted' and 'validator_subprocess' not in p for p in exhausted['phases'][1:])
    assert all(s['attempt']['rc'] == 0 for s in exhausted['steps'])
    assert all(s['comparison']['order'] == 'unestablished' for s in exhausted['steps'][1:])
    _, cutoff = run(pw, out, 'byte_limit', [action('s0', stable, 'byte_flood')], {'validator_executable_path': str(validator)}, 1)
    child = cutoff['phases'][0]['validator_subprocess']
    assert child['stdout_collection_stop'] == 'byte_limit' and len(child['records']) == 1
    assert 16384 < child['stdout_bytes_received'] <= 24576
    assert child['reaped'] is True and cutoff['steps'][0]['attempt']['rc'] == 0
    print('Public phases: independent unlink, fresh unavailable query, fresh native later query; eleven reader rejections; aggregate timeout and byte cutoff.')


if __name__ == '__main__':
    main()
