"""Independent mutations of a retained native capture; no native calls here."""
from copy import deepcopy
import json
from pathlib import Path

from lifecycle_oracle import check_record


def run_extension_controls(run):
    fixture = Path(__file__).resolve().parents[2] / 'fixtures/blackbox_e2e/checker/response18/extension_run.json'
    baseline = json.loads(fixture.read_text())
    assert check_record(baseline) == [], check_record(baseline)
    run('extension_native_capture', baseline)
    abnormal = json.loads(fixture.with_name('issuer_abnormal_run.json').read_text())
    run('issuer_abnormal_capture', abnormal)
    assert check_record(abnormal) == []
    missing = deepcopy(abnormal)
    declaration = missing['data']['runner_result']['extensions'][0]
    declaration['issuance_status'] = 'issuer_result_missing'
    rule = 'missing issuer result carries publication or payload'
    run('issuer_missing_published_result', missing, rejected_by=rule)
    assert any(f.get('detail') == rule for f in check_record(missing))
    issuer = declaration['issuer']
    issuer['result_published'] = False
    for key in ('native_nonnull', 'errno', 'token_length', 'uid', 'euid', 'gid', 'egid'):
        issuer.pop(key, None)
    for called in (False, True):
        issuer['call_boundary_observed'] = called
        run('issuer_missing_boundary_' + str(called), missing)
        assert check_record(missing) == []
        assert issuer['exit_code'] == 87 and issuer['reaped'] is True
    for index, (key, value) in enumerate([
            ('result_published', True), ('result_published', None), ('native_nonnull', False),
            ('errno', 0), ('token_length', 0), ('uid', 0), ('euid', 0), ('gid', 0), ('egid', 0)]):
        changed = deepcopy(missing)
        changed['data']['runner_result']['extensions'][0]['issuer'][key] = value
        run('issuer_missing_payload_' + str(index), changed, rejected_by=rule)
        assert any(f.get('detail') == rule for f in check_record(changed))
    changed = deepcopy(missing)
    changed['data']['runner_result']['extensions'][0].pop('issuer')
    run('issuer_missing_record', changed, rejected_by=rule)
    assert any(f.get('detail') == rule for f in check_record(changed))
    for status in ('issuer_timeout', 'issuer_wait_error'):
        interrupted = deepcopy(abnormal)
        interrupted['data']['runner_result']['extensions'][0]['issuance_status'] = status
        run(status + '_retains_publication', interrupted)
        assert check_record(interrupted) == []
    for key, value in [('exit_code', 0), ('result_published', False), ('reaped', False), ('token_length', 0)]:
        changed = deepcopy(abnormal)
        changed['data']['runner_result']['extensions'][0]['issuer'][key] = value
        run('issuer_abnormal_' + key, changed, rejected_by='abnormal issuer exit lacks publication and reap')
        assert check_record(changed)

    for name, value in [('integer', 7), ('boolean', True), ('string', 'invalid'),
                        ('object', {'invalid': True}), ('entry', [7])]:
        document = deepcopy(baseline)
        document['data']['runner_result']['phases'] = value
        run('phase_collection_malformed_' + name, document,
            rejected_by='phase is not an object' if name == 'entry' else 'phases must be a bounded array')
        findings = check_record(document)
        assert any(f['kind'] == 'phase_collection' for f in findings), (name, findings)

    cases = json.loads((fixture.parents[3] / 'contract/phase_collection.json').read_text())
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
            phase['validator_subprocess'].update(reaped=case['reaped'], exit_code=None, term_signal=None)
        phase.pop('validator_spawn_failure', None)
        if case['spawn_failure']:
            phase['validator_spawn_failure'] = dict(origin='runner_host', operation='posix_spawn',
                executable_path='/controlled/validator', return_code=2, diagnostic='controlled spawn failure')
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

    def event(document, index=0):
        return runner(document)['extension_events'][index]

    mutations = [
        ('no_call_boundary', lambda d: event(d).update(call_boundary_observed=False), 'lacks publication'),
        ('no_result_publication', lambda d: event(d).update(result_published=False), 'publication'),
        ('unpublished_native_value', lambda d: event(d).update(status='unresolved', result_published=False), 'must stay unresolved'),
        ('unavailable_with_call', lambda d: event(d).update(status='unavailable', unavailable_reason='token_unavailable'), 'fabricates a call'),
        ('native_boolean', lambda d: event(d).update(native_result=True), 'lacks publication'),
        ('native_float', lambda d: event(d).update(native_result=1.0), 'lacks publication'),
        ('native_overflow', lambda d: event(d).update(native_result=2**63), 'lacks publication'),
        ('release_int_overflow', lambda d: event(d, 1).update(native_result=2**31), 'lacks publication'),
        ('release_without_handle', lambda d: event(d).update(native_result=-1), 'observed consume handle'),
        ('release_wrong_handle', lambda d: event(d, 1).update(handle_ref='another'), 'reference/order'),
        ('release_token_reference', lambda d: event(d, 1).update(token_ref='token'), 'reference/order'),
        ('consume_wrong_token', lambda d: event(d).update(token_ref='another'), 'reference/order'),
        ('aliased_handle', lambda d: event(d).update(handle_ref='token'), 'invalid extension action/handle'),
        ('wrong_phase', lambda d: event(d).update(phase_id='absent'), 'phase association'),
        ('reordered_events', lambda d: runner(d)['extension_events'].reverse(), 'partition'),
        ('duplicate_event', lambda d: runner(d)['extension_events'].append(deepcopy(event(d))), 'capacity'),
        ('duplicate_declaration', lambda d: runner(d)['extensions'].append(deepcopy(runner(d)['extensions'][0])), 'capacity'),
        ('removed_declaration', lambda d: runner(d).update(extensions=[]), 'require one declaration'),
        ('lost_delivery', lambda d: runner(d)['extensions'][0].update(delivery_status='not_observed', delivered_bytes=None), 'consumption lacks delivery'),
        ('oversized_delivery', lambda d: runner(d)['extensions'][0].update(delivered_bytes=16384), 'bounded issuance'),
        ('unreaped_issuer', lambda d: runner(d)['extensions'][0]['issuer'].update(reaped=False), 'clean issuer reap'),
        ('unpublished_issuer', lambda d: runner(d)['extensions'][0]['issuer'].update(result_published=False), 'publication'),
        ('missing_issuer_marker', lambda d: runner(d)['extensions'][0]['issuer'].update(call_boundary_observed=False), 'publication'),
        ('missing_apply', lambda d: runner(d).update(sandboxed_after_apply=False), 'application and phase acknowledgement'),
        ('missing_ack', lambda d: runner(d)['phases'][0]['ordering'].update(proceed_observed=False), 'application and phase acknowledgement'),
        ('missing_slot', lambda d: runner(d)['runner_subprocess']['disposition']['steps'].pop(1), 'disagrees with disposition'),
        ('invented_slot', lambda d: runner(d)['runner_subprocess']['disposition']['steps'][1].update(slot='incomplete'), 'disagrees with disposition'),
        ('copied_wrong_claim', lambda d: event(d)['lifecycle']['result'].update(answer='unpublished'), 'disagrees with disposition'),
        ('unknown_native_operation', lambda d: event(d).update(operation='future'), 'unknown extension operation'),
    ]
    for name, change, diagnostic in mutations:
        document = deepcopy(baseline)
        change(document)
        run('extension_' + name, document, rejected_by=diagnostic)
        # The separate lifecycle oracle also rejects invented native evidence.
        if name not in ('reordered_events',):
            assert check_record(document), ('oracle accepted', name)

    # A native consume failure has no handle for release. Access observations
    # remain independently meaningful even when they show a successful read.
    refused = deepcopy(baseline)
    event(refused)['native_result'] = -1
    event(refused, 1).update(status='unavailable', call_boundary_observed=False,
        unavailable_reason='handle_unavailable')
    event(refused, 1).pop('native_result'); event(refused, 1).pop('errno')
    run('extension_native_failure_keeps_access', refused)
    assert check_record(refused) == [], check_record(refused)

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
        run('extension_read_' + name, document, rejected_by=diagnostic)
    document = deepcopy(baseline)
    runner(document)['steps'][0]['attempt']['fresh_read']['read_rc'] = 0
    run('extension_read_after_failed_open', document, rejected_by='failed fresh open cannot supply')
    document = deepcopy(baseline)
    runner(document)['steps'][1]['attempt'].pop('fresh_read')
    run('extension_read_missing_observation', document, rejected_by='lacks syscall observations')
