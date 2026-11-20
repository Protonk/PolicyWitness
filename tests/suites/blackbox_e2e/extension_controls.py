"""Independent ordinary-file, validator-ownership and actor-evidence controls.

The ordinary fixture is constructed from ordinary records with no declaration
or native lifecycle action. Actor fixtures exercise the bounded subaccount
reader; complete lifecycle/transport remains separately checked by the live
actor driver and cross-reader controls.
"""
from copy import deepcopy
import json
from pathlib import Path

from lifecycle_oracle import check_fixture_record as check_record
from consumer import validate_fixture as validate
from blackbox import envelope_skeleton, recapture_host_reply
from actor_evidence import validate_actor_evidence, _metadata_fits
from extension_evidence import validate_actor_extensions


def patch(document, path, value):
    parts = path.lstrip('/').split('/')
    target = document
    for key in parts[:-1]:
        target = target[int(key)] if isinstance(target, list) else target[key]
    target[int(parts[-1]) if isinstance(target, list) else parts[-1]] = deepcopy(value)


def run_extension_controls(run):
    fixtures = Path(__file__).resolve().parents[2] / 'fixtures/contract'
    ordinary = json.loads((fixtures / 'ordinary_phase_reply.json').read_text())
    # Author one successful ordinary read beside the retained denied-open
    # neighbor. These hypothetical syscall facts make every later byte/count,
    # stat/close and fresh-write mutation exercise its intended channel.
    # They are constructed input, with no native access or calibration credit.
    read_step = ordinary['steps'][1]
    read_step['attempt'].update(rc=0, errno=None, outcome='ok',
        observed_path=read_step['attempt']['requested_path'],
        fresh_read=dict(open_rc=17, read_rc=32, stat_rc=0,
            identity=dict(device=3, inode=42, mode=33152, uid=501, gid=20),
            close_rc=0, content_hex='ab' * 32))
    read_step['comparison'].update(observation='succeeded',
        observation_basis='completed_worker_status')
    baseline = envelope_skeleton(ordinary)
    baseline['data']['runner_sandbox_diagnostics'] = dict(process_disposition='clean_exit',
        termination_cause=None, stop_reason='done', disposition_integrity='valid', disposition_issues=[])
    assert check_record(baseline) == [], check_record(baseline)
    run('ordinary_fresh_read_and_phases', baseline)
    for case in json.loads((fixtures / 'evidence_types.json').read_text()):
        document = deepcopy(baseline)
        for change in case['patches']:
            patch(document['data']['runner_result'], change['path'], change['value'])
        recapture_host_reply(document)
        before = deepcopy(document)
        errors, findings = validate(document), check_record(document)
        assert (not errors) == case['accepted'], (case['name'], errors)
        assert (not findings) == case['accepted'], (case['name'], findings)
        assert document == before, case['name']
    for name, value in [('integer', 7), ('boolean', True), ('string', 'invalid'),
                        ('object', {'invalid': True}), ('entry', [7])]:
        document = deepcopy(baseline)
        document['data']['runner_result']['phases'] = value
        run('phase_collection_malformed_' + name, document,
            rejected_by='phase is not an object' if name == 'entry' else 'phases must be a bounded array')
        findings = check_record(document)
        assert any(f['kind'] == 'phase_collection' for f in findings), (name, findings)

    cases = json.loads((fixtures / 'phase_collection.json').read_text())
    for case in cases:
        document = deepcopy(baseline)
        reply = document['data']['runner_result']
        # An empty final phase leaves every existing action/claim untouched.
        phase = deepcopy(reply['phases'][-1])
        phase.update(phase_id='collection_control', ordinal=len(reply['phases']) + 1,
                     action_ids=[], arrival_observed=case['status'] != 'not_reached',
                     completion_observed=False, collection_status=case['status'])
        phase['ordering'].update(validator_disposition=case['disposition'],
            collection_closed_before_proceed=case['disposition'] != 'not_invoked',
            proceed_set=False, proceed_observed=False, worker_lifetime_established=False)
        if case['reaped'] is None:
            phase.pop('validator_subprocess', None)
        else:
            # The carrier phase has no actions: its collection is its own, with an
            # empty plan and no records.
            phase['validator_subprocess'].update(phase_id=phase['phase_id'], ordinal=phase['ordinal'],
                expected_step_ids=[], records=[], association_issues=[],
                reaped=case['reaped'], exit_code=None, term_signal=None)
        phase.pop('validator_spawn_failure', None)
        if case['spawn_failure']:
            phase['validator_spawn_failure'] = dict(origin='runner_host', operation='posix_spawn',
                executable_path='/controlled/validator', return_code=2, diagnostic='controlled spawn failure')
            # A reply that records a failed spawn is not finished; only the
            # collection evidence varies between these rows.
            reply.update(normalized_outcome='validator_spawn_failed', rc=1, error='controlled spawn failure')
            document['result'].update(normalized_outcome='validator_spawn_failed', ok=False, exit_code=1,
                                      error='controlled spawn failure')
        reply['phases'].append(phase)
        diagnostic = None if case['accepted'] else 'phase collection status contradicts validator evidence'
        run('phase_collection_' + case['name'], document, rejected_by=diagnostic)
        findings = check_record(document)
        assert (not findings) == case['accepted'], (case['name'], findings)
        if case['accepted'] and case['status'] == 'not_reached':
            for field in ('ordering', 'ordering.validator_disposition'):
                # An ordering string has the wrong type; a disposition string
                # has the right type and belongs to the vocabulary control below.
                values = (7, True, 'wrong', []) if field == 'ordering' else (7, True, [], {})
                for value in values:
                    changed = deepcopy(document)
                    changed_phase = changed['data']['runner_result']['phases'][-1]
                    if field == 'ordering':
                        changed_phase[field] = value
                    else:
                        changed_phase['ordering']['validator_disposition'] = value
                    run('phase_type_' + field + '_' + type(value).__name__, changed,
                        rejected_by='phase collection evidence has an invalid type')
                    assert any(f['kind'] == 'phase_collection' for f in check_record(changed))
            changed = deepcopy(document)
            changed['data']['runner_result']['phases'][-1]['ordering']['validator_disposition'] = 'wrong'
            run('phase_unknown_validator_disposition', changed,
                rejected_by='phase collection status contradicts validator evidence')
            assert any(f['kind'] == 'phase_collection' for f in check_record(changed))
        if case['accepted'] and case['status'] == 'collected' and case['disposition'] == 'not_spawned':
            changed = deepcopy(document)
            changed['data']['runner_result']['phases'][-1]['validator_spawn_failure'] = {}
            run('empty_spawn_' + case['name'], changed, rejected_by='invalid validator_spawn_failure record')
            # The oracle validates claims, not every record's required fields.
            assert check_record(changed) == []
            changed['data']['runner_result']['phases'][-1]['validator_spawn_failure'] = 7
            run('mistyped_spawn_' + case['name'], changed,
                rejected_by='phase collection evidence has an invalid type')
            assert any(f['kind'] == 'phase_collection' for f in check_record(changed))

    def runner(document):
        return document['data']['runner_result']

    # Validator collection ownership: every phase of this model queries the same
    # path under a different action ID, so a borrowed block differs only in its
    # identity, plan and record IDs. Each reader must reject the transplant for the
    # stated reason; the lifecycle oracle surfaces the shared phase-evidence finding.
    phases = runner(baseline)['phases']
    assert len(phases) == 3 and len({s['sandbox_check']['filter_value'] for s in runner(baseline)['steps']}) == 1
    def collection(document, index):
        return runner(document)['phases'][index]['validator_subprocess']
    transplants = [
        ('whole_block', lambda d: runner(d)['phases'][0].__setitem__('validator_subprocess', deepcopy(collection(baseline, 1))), 'names another phase'),
        ('identity_only', lambda d: collection(d, 1).update(phase_id=phases[0]['phase_id']), 'names another phase'),
        ('ordinal_only', lambda d: collection(d, 1).update(ordinal=1), 'names another phase'),
        ('expected_ids_only', lambda d: collection(d, 1).update(expected_step_ids=deepcopy(collection(baseline, 0)['expected_step_ids'])), 'eligible query plan'),
        ('records_only', lambda d: collection(d, 1).update(records=deepcopy(collection(baseline, 0)['records'])), 'association issues disagree'),
        ('missing_identity', lambda d: collection(d, 1).pop('phase_id'), 'lacks phase ownership'),
        ('missing_plan', lambda d: collection(d, 1).pop('expected_step_ids'), 'lacks its expected plan'),
        ('records_erased', lambda d: collection(d, 1).update(records=[]), 'association issues disagree'),
        ('issues_erased_with_duplicate', lambda d: collection(d, 1)['records'].append(deepcopy(collection(d, 1)['records'][0])), 'association issues disagree'),
    ]
    for name, change, reason in transplants:
        document = deepcopy(baseline)
        change(document)
        run('validator_ownership_' + name, document, rejected_by=reason)
        findings = check_record(document)
        assert any(f['kind'] == 'phase_collection' and reason in f.get('detail', '') for f in findings), (name, findings)
    # Sequential children may reuse a numeric PID; ownership never reads PIDs.
    reused = deepcopy(baseline)
    collection(reused, 1)['pid'] = collection(reused, 0)['pid']
    run('validator_ownership_reused_pid', reused)
    assert check_record(reused) == []

    for name, changes, diagnostic in [
        ('wrong_byte_count', {'read_rc': 1}, 'bytes disagree'),
        ('float_byte_count', {'read_rc': 32.0}, 'invalid fresh read result'),
        ('boolean_byte_count', {'read_rc': True}, 'invalid fresh read result'),
        ('overlong_read', {'read_rc': 65}, 'invalid fresh read result'),
        ('invalid_hex', {'content_hex': 'zz' * 32}, 'bytes disagree'),
        ('failed_read_with_bytes', {'read_rc': -1, 'read_errno': 5}, 'cannot supply content'),
        ('failed_stat_with_identity', {'stat_rc': -1, 'stat_errno': 9}, 'identity lacks'),
        ('missing_close', {'close_rc': None}, 'invalid fresh close result'),
        ('success_errno', {'open_errno': 13}, 'successful fresh open'),
    ]:
        document = deepcopy(baseline)
        runner(document)['steps'][1]['attempt']['fresh_read'].update(changes)
        run('ordinary_read_' + name, document, rejected_by=diagnostic)
    document = deepcopy(baseline)
    runner(document)['steps'][0]['attempt']['fresh_read']['read_rc'] = 0
    run('ordinary_read_after_failed_open', document, rejected_by='failed fresh open cannot supply')
    document = deepcopy(baseline)
    runner(document)['steps'][1]['attempt'].pop('fresh_read')
    run('ordinary_read_missing_observation', document, rejected_by='lacks syscall observations')

    from fresh_write_controls import run_fresh_write_controls
    run_fresh_write_controls(run, baseline)
    # Both independent implementations read this hand-authored corpus. These
    # are subaccount interpretation controls, never synthetic native authority.
    actor_cases = json.loads((fixtures / 'actor_evidence.json').read_text())
    for case in actor_cases:
        reply = json.loads((fixtures / case.get('fixture', 'actor_authority_reply.json')).read_text())
        before_patch = deepcopy(reply)
        for change in case['patches']:
            patch(reply, change['path'], change['value'])
        if case['patches']:
            assert reply != before_patch, ('inert actor evidence mutation', case['name'])
        before = deepcopy(reply)
        errors = validate_actor_evidence(reply)
        assert reply == before, case['name']
        assert (not errors) == case['accepted'], (case['name'], errors)
        if case.get('diagnostic'):
            assert any(case['diagnostic'] in error for error in errors), (case['name'], errors)
    readiness_controls(fixtures)
    custody_relation_controls(fixtures)
    assert _metadata_fits(['é' * 16384, None])
    assert not _metadata_fits(['é' * 16384, 'x'])
    assert not _metadata_fits([True])
    oversized = json.loads((fixtures / 'actor_authority_reply.json').read_text())
    oversized['equipment_bindings'][0]['reason'] = 'é' * 16385
    before = deepcopy(oversized)
    assert 'equipment binding metadata bound' in validate_actor_evidence(oversized)
    assert oversized == before
    print(f"{len(actor_cases)} independent actor setup/equipment/application/gate controls checked", flush=True)


def readiness_controls(fixtures):
    """Python-only readiness relations of a worker setup scope; the Rust reader
    does not hold them, so these rows stay out of the shared corpus."""
    def body(name='actor_authority_reply.json'):
        return json.loads((fixtures / name).read_text())

    def subject(reply):
        return reply['authority_setup']['workers'][1]

    ready_cells = 'ready setup lacks a required scope or its successful cells'
    rows = [
        ('core_limit_removed', lambda r: subject(r).update(
            operations=[op for op in subject(r)['operations'] if op['slot'] != 3]), [ready_cells]),
        ('core_limit_failed', lambda r: next(op for op in subject(r)['operations'] if op['slot'] == 3).update(
            state='failed', native_rc=-1, errno=1), [ready_cells]),
        ('ready_not_required', lambda r: subject(r).update(required=False), [ready_cells]),
        ('host_regions_emptied', lambda r: r['authority_setup']['host'].update(regions=[]),
         ['ready worker setup lacks a ready host region']),
        ('not_required_on_required_scope', lambda r: subject(r).update(disposition='not_required'),
         ['not_required setup on a required scope', 'established actor setup lacks an observed ready scope']),
        ('applied_actor_without_decision', lambda r: subject(r).update(publication='not_observed', disposition=None),
         ['established actor setup lacks an observed ready scope']),
    ]
    assert validate_actor_evidence(body()) == []
    for name, change, diagnostics in rows:
        reply = body()
        change(reply)
        errors = validate_actor_evidence(reply)
        assert all(any(d in e for e in errors) for d in diagnostics), (name, errors)

    def primary(slot, cell):
        def change(reply):
            operations = subject(reply)['operations']
            operations[:] = [op for op in operations if op['slot'] != slot] + [cell]
            subject(reply)['primary_operation'] = slot
        return change
    # Each clause alone: a primary operation on an otherwise complete ready
    # scope, and only the subject's own region not ready beside a ready one.
    isolated = [
        ('ready_with_primary_page_size', primary(6, dict(slot=6, operation='page_size', role='setup', state='failed',
            native_kind='integer', native_rc=-1, errno=12)), [ready_cells]),
        ('ready_with_primary_cleanup_cell', primary(12, dict(slot=12, operation='rejected_mapping_munmap', role='cleanup',
            state='failed', native_kind='integer', native_rc=-1, errno=22)),
         ['setup primary operation lacks independent failure', ready_cells]),
        ('subject_region_not_ready',
         lambda r: r['authority_setup']['host']['regions'][1].update(disposition='failed'),
         ['ready worker setup lacks a ready host region']),
    ]
    for name, change, expected in isolated:
        reply = body()
        change(reply)
        assert validate_actor_evidence(reply) == expected, (name, validate_actor_evidence(reply))
    rows += isolated
    # Accepted neighbours: a terminal refusal after a partial prefix, and an
    # unpublished decision with cells beside an actor whose setup timed out.
    assert validate_actor_evidence(body('actor_setup_failure_reply.json')) == []
    unpublished = body()
    subject(unpublished).update(publication='not_observed', disposition=None)
    unpublished['actors'][1]['setup_status'] = 'setup_timeout'
    assert validate_actor_evidence(unpublished) == [], validate_actor_evidence(unpublished)
    print(f'{len(rows)} refused and 3 accepted readiness relation controls checked', flush=True)


def custody_relation_controls(fixtures):
    """A transfer the host held custody for names a token that is issued or
    unresolved. This fixture's extension relations are partial, so each row is
    compared with the unchanged body's findings."""
    reply = json.loads((fixtures / 'actor_authority_reply.json').read_text())
    diagnostic = 'held transfer custody contradicts its token status'
    baseline = validate_actor_extensions(reply)
    assert diagnostic not in baseline, baseline

    def errors(change):
        changed = deepcopy(reply)
        change(changed)
        return validate_actor_extensions(changed)

    def token(r):
        return r['resources']['tokens'][0]

    def unavailable_custody(r):
        r['transfers'][0].update(custody_status='unavailable', status='custody_unavailable')
        r['resources']['deliveries'][0].update(status='custody_unavailable')

    def second_token(status):
        def change(r):
            added = deepcopy(token(r))
            added.update(token_ref='t2', step_id='issue2', status=status)
            r['resources']['tokens'].append(added)
        return change

    assert errors(lambda r: token(r).update(status='issued_uncustodied')) == baseline + [diagnostic]
    # The held transfer names token t; an issued token t2 cannot stand in for it.
    assert diagnostic in errors(lambda r: (second_token('issued')(r), token(r).update(status='issued_uncustodied')))
    for name, change in [
        ('issued_beside_unavailable_custody', unavailable_custody),
        ('issued_uncustodied_beside_unavailable_custody',
         lambda r: (unavailable_custody(r), token(r).update(status='issued_uncustodied'))),
        # An unresolved token beside held custody; the issue rule separately
        # refuses it here because this fixture's issue result is published.
        ('unresolved_beside_held_custody', lambda r: token(r).update(status='unresolved')),
        ('uncustodied_second_token_beside_held_custody', second_token('issued_uncustodied')),
    ]:
        assert diagnostic not in errors(change), (name, errors(change))
    print('custody relation controls checked', flush=True)
