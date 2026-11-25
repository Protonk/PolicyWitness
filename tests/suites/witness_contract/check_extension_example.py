"""Check the two-reader grant against the case's own open of the target."""
import errno
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import build_context
import consumer
import file_observation

TARGET = '/private/etc/hosts'
READS = (
    ('alice-before', 'alice-baseline', 'Alice'),
    ('bob-before', 'bob-baseline', 'Bob'),
    ('alice-during', 'alice-fresh', 'Alice'),
    ('bob-during', 'bob-fresh', 'Bob'),
)
FRESH = {'Alice': 'alice-fresh', 'Bob': 'bob-fresh'}


def sample(directory, when, target):
    observation = file_observation.observe_target(str(target), 64)
    (directory / f'target-{when}.json').write_text(json.dumps(observation, indent=2) + '\n')
    assert observation['readable'] and observation['regular_file'] and observation['prefix_length'] > 0, observation
    return observation


def reader_policy_mismatches(document, data):
    """Compare each unaugmented reader's submitted SBPL bytes with its own records."""
    mismatches = {}
    for reader in FRESH:
        source = consumer.actor_record(document, reader)['sandbox']['policy']['sbpl_source']
        expected = hashlib.sha256(source.encode('utf-8')).hexdigest()
        dossier = consumer.actor_record(data['specimen'], reader)
        prepared = dossier.get('policy', {}).get('augmentation', {})
        actor = consumer.actor_record(data['runner_result'], reader)
        for field, record in (('original_sha256', prepared), ('applied_sha256', prepared),
                              ('policy_sha256', actor), ('policy_received_sha256', actor)):
            actual = record.get(field)
            if actual != expected:
                mismatches[f'{reader}.{field}'] = {'submitted': expected, 'reported': actual}
    return mismatches


def check_lifecycle(document, data, recipient, target):
    """Published issuance, transfer acknowledgements and handle returns have different witnesses."""
    mismatches = reader_policy_mismatches(document, data)
    assert not mismatches, mismatches
    runner = data['runner_result']
    assert runner['normalized_outcome'] == 'finished', runner['normalized_outcome']
    phases = runner['phases']
    assert [(p['phase_id'], p['actor_id'], p['action_ids']) for p in phases] == [
        ('alice-before', 'Alice', ['alice-baseline']), ('bob-before', 'Bob', ['bob-baseline']),
        ('supply', 'issuer', ['issue', 'deliver']), ('consume', recipient, ['consume']),
        ('alice-during', 'Alice', ['alice-fresh']), ('bob-during', 'Bob', ['bob-fresh']),
        ('release', recipient, ['release'])]
    assert all(p['arrival_observed'] and p['completion_observed'] for p in phases)
    events = runner['extension_events']
    assert [(e['step_id'], e['actor_id'], e['operation']) for e in events] == [
        ('issue', 'issuer', 'issue'), ('deliver', 'issuer', 'transfer'),
        ('consume', recipient, 'consume'), ('release', recipient, 'release')]
    issue, transfer_event, consume, release = events
    for call in (issue, consume, release):
        assert call['call_boundary_observed'] and call['result_published'] and call['status'] == 'returned', call
    assert (issue['target'], issue['native_nonnull']) == (target, True), issue
    transfer, = runner['transfers']
    assert transfer_event['result_published'] and transfer_event['status'] == 'delivered'
    assert (transfer['source_actor_id'], transfer['recipient_actor_id']) == ('issuer', recipient)
    assert transfer['step_id'] == transfer_event['step_id']
    assert transfer['source_acknowledged'] and transfer['recipient_acknowledged']
    assert (transfer['status'], transfer['equality']) == ('delivered', 'equal'), transfer
    assert consume['delivery_ref'] == transfer['delivery_ref'] and consume['native_result'] != -1
    assert release['handle_ref'] == consume['handle_ref'] and release['native_result'] == 0
    actors = {a['actor_id']: a for a in runner['actors']}
    assert set(actors) == {'issuer', 'Alice', 'Bob'}
    assert len({actor['launch']['pid'] for actor in actors.values()}) == 3
    assert all(actor['subprocess']['reaped'] for actor in actors.values())
    for name in ('Alice', 'Bob'):
        assert actors[name]['applied'] and actors[name]['application_count'] == 1
        assert actors[name]['equipment']['resolved'] == 'selected'


def check_read(attempt, observation):
    target, stat = observation['target'], observation['stat']
    problems = (file_observation.fresh_syscalls(attempt, 64)
                + file_observation.fresh_identity(attempt, {'device': stat['st_dev'], 'inode': stat['st_ino']}, target)
                + file_observation.fresh_content(attempt, observation, target))
    assert not problems, problems
    assert attempt['rc'] == 0


def opened_steps(runner, observation):
    """IDs of the read steps whose worker opened the sampled file; every other read failed at open with a permission errno."""
    steps = runner['steps']
    assert [(s['phase_id'], s['step_id'], s['actor_id']) for s in steps] == list(READS)
    target = observation['target']
    opened = []
    for step in steps:
        attempt = step['attempt']
        query = step['sandbox_check']
        assert (query['operation'], query['filter_value']) == ('file-read-data', target)
        assert step['comparison']['order'] == 'query_first'
        assert (attempt['requested_action'], attempt['requested_path'], attempt['result_source']) == (
            'read_fresh', target, 'worker')
        if attempt['fresh_read']['open_rc'] >= 0:
            check_read(attempt, observation)
            opened.append(step['step_id'])
        else:
            assert attempt['fresh_read']['open_rc'] == attempt['rc'] == -1
            assert attempt['fresh_read']['open_errno'] in (errno.EPERM, errno.EACCES)
    return opened


def grant_alone_changed_access(opened, recipient):
    """Only the recipient opened the file, and only after consuming."""
    return opened == [FRESH[recipient]]


def verify_emission(directory):
    assert (directory / 'emit.exit').read_text().strip() == '0'
    assert not (directory / 'emit.stderr').read_bytes()
    document = json.loads((directory / 'emit.stdout').read_bytes())
    assert document.pop('contract') == build_context.candidate_contract()
    surfaces = json.loads((ROOT / 'docs/contract/public.json').read_bytes())['surfaces']
    request = next(s for s in surfaces if s['id'] == 'request')
    node = next(n for n in request['public']['nodes'] if n['id'] == 'request.specimen.extension_example')
    assert document == node['document']
    # Moving the grant compares like with like only if the readers are declared alike.
    readers = {actor['actor_id']: {key: value for key, value in actor.items() if key != 'actor_id'}
               for actor in document['actors'] if actor['actor_id'] != 'issuer'}
    assert set(readers) == set(FRESH) and readers['Alice'] == readers['Bob'], readers
    assert [(p['actor_id'], [s['step_id'] for s in p['actions']]) for p in document['phases'] if p['actor_id'] == 'Bob'] == [
        ('Bob', ['bob-baseline']), ('Bob', ['bob-fresh'])]
    # Bound the workload independently before submitting any of the printed bytes.
    ordinary = [s for p in document['phases'] for s in p['actions'] if 'attempt' in s]
    assert [s['step_id'] for s in ordinary] == [step for _, step, _ in READS]
    for step in ordinary:
        assert step['attempt'] == {'kind': 'file', 'action': 'read_fresh', 'target': TARGET}
        assert step['sandbox_check'] == {'operation': 'file-read-data', 'filter': {'kind': 'path', 'value': TARGET}}
    grants = [s['extension'] for p in document['phases'] for s in p['actions'] if 'extension' in s]
    assert [g['operation'] for g in grants] == ['issue', 'transfer', 'consume', 'release']
    assert (grants[0]['family'], grants[0]['authority'], grants[0]['target']) == ('file', 'read', TARGET)
    assert grants[1]['recipient'] == 'Alice'


def round_trip(stage, directory):
    if stage == 'prepare':
        verify_emission(directory)
        sample(directory, 'before', TARGET)
        return
    after = sample(directory, 'after', TARGET)
    before = json.loads((directory / 'target-before.json').read_bytes())
    assert before == after, (before, after)
    assert (directory / 'run.exit').read_text().strip() == '0'
    envelope = json.loads((directory / 'run.stdout').read_bytes())
    errors = consumer.validate(envelope, build_context.candidate_contract())
    assert not errors, errors
    raw = (directory / 'emit.stdout').read_bytes()
    assert envelope['data']['specimen']['request_sha256'] == hashlib.sha256(raw).hexdigest()
    assert envelope['result']['ok'] and envelope['result']['normalized_outcome'] == 'finished'
    runner = envelope['data']['runner_result']
    assert runner['specimen_id'] == 'extension'
    check_lifecycle(json.loads(raw), envelope['data'], 'Alice', TARGET)
    opened = opened_steps(runner, before)
    assert grant_alone_changed_access(opened, 'Alice'), opened


if __name__ == '__main__':
    stage, directory = sys.argv[1:]
    round_trip(stage, Path(directory))
