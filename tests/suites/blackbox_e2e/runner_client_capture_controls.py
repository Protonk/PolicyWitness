"""Constructed reservation/capture reader controls, independent of producers."""
import base64
import copy
import json

import contract
from blackbox import envelope_skeleton
from runner_client_capture import validate_capture, host_reply


def run_capture_controls(run):
    reply = {'schema_version': contract.RESPONSE_SCHEMA, 'normalized_outcome': 'bad_request',
             'rc': 1, 'error': 'constructed host reply', 'steps': [], 'phases': []}
    baseline = envelope_skeleton(reply, ok=False)

    def client(document):
        return document['data']['runner_client']

    def capture(document):
        return client(document)['transport']

    def check(name, document, diagnostic=None):
        run('capture_' + name, document, rejected_by=diagnostic)

    def error(stage, reason, native=False):
        value = dict(stage=stage, reason=reason, message='constructed observation',
                     domain_truncated=False, message_truncated=False)
        if native:
            value.update(domain='NSCocoaErrorDomain', code=4097)
        return value

    def fail_terminal(document, terminal, why, *, invoked=True):
        value = capture(document)
        value.pop('runner_reply', None)
        value.update(terminal=terminal, error=why)
        if terminal == 'xpc_timeout':
            value['ended_continuous_ns'] = value['deadline_continuous_ns']
        if not invoked:
            value['submission'] = {'state': 'not_invoked'}
            client(document)['submission'] = 'not_invoked'
        document['data']['runner_result'] = None
        return document

    check('host_reply', baseline)
    assert host_reply(capture(baseline)) == reply
    null_optionals = copy.deepcopy(baseline)
    capture(null_optionals).update(error=None, submission_refusal=None)
    capture(null_optionals)['attempts'][0].update(error=None)
    check('optional_null_means_absent', null_optionals)
    different_identity = copy.deepcopy(baseline)
    # These PIDs report different observations; equality is never inferred.
    different_identity['data']['runner_result']['pid'] = 999
    raw = json.dumps(different_identity['data']['runner_result']).encode()
    capture(different_identity)['runner_reply'].update(bytes_received=len(raw), bytes_retained=len(raw),
        data_base64=base64.b64encode(raw).decode())
    check('host_and_client_identities_distinct', different_identity)

    for terminal, reason in [('xpc_error', 'xpc_error'), ('xpc_error', 'proxy_type_mismatch'), ('xpc_timeout', 'overall_deadline'),
                             ('protocol_error', 'invalid_control')]:
        document = fail_terminal(copy.deepcopy(baseline), terminal, error('submission', reason, terminal == 'xpc_error'))
        check('invoked_' + terminal + '_' + reason, document)
        changed = copy.deepcopy(document)
        client(changed)['submission'] = 'not_invoked'
        check('invoked_' + terminal + '_' + reason + '_cannot_project_not_invoked', changed, 'submission projection')

    refused = copy.deepcopy(baseline)
    capture(refused).pop('runner_reply')
    capture(refused).update(terminal='submission_refused', submission_refusal={
        'bytes_received': 200, 'sha256': 'b' * 64, 'status': 'reservation_refused',
        'host_pid': 125, 'host_instance': '33333333-3333-4333-8333-333333333333', 'reason': 'expired'})
    refused['data']['runner_result'] = None
    check('invoked_control_refusal', refused)
    host_clock_refusal = copy.deepcopy(refused)
    capture(host_clock_refusal)['submission_refusal']['reason'] = 'clock_error'
    check('host_clock_refusal_is_not_helper_clock_failure', host_clock_refusal)

    not_invoked = fail_terminal(copy.deepcopy(baseline), 'xpc_timeout',
                               error('acquisition', 'overall_deadline'), invoked=False)
    capture(not_invoked)['ended_continuous_ns'] = capture(not_invoked)['deadline_continuous_ns']
    check('grant_without_invocation_at_deadline', not_invoked)
    prepared_failure = copy.deepcopy(not_invoked)
    capture(prepared_failure).update(terminal='local_error', error=error('local', 'clock_error'))
    check('grant_without_invocation_local_failure', prepared_failure)

    occupied = fail_terminal(copy.deepcopy(baseline), 'xpc_timeout',
                            error('acquisition', 'overall_deadline'), invoked=False)
    value = capture(occupied)
    value.update(acquisition_stop='overall_deadline', ended_continuous_ns=value['deadline_continuous_ns'])
    value['attempts'][0]['outcome'] = 'occupied'
    value['attempts'][0]['control'].update(status='occupied')
    value['attempts'][0]['control'].pop('lease_ms')
    check('occupied_until_deadline', occupied)
    before_attempt = copy.deepcopy(occupied)
    capture(before_attempt)['attempts'] = []
    check('deadline_before_first_attempt', before_attempt)

    retried = copy.deepcopy(baseline)
    first = copy.deepcopy(capture(occupied)['attempts'][0])
    second = capture(retried)['attempts'][0]
    second.update(ordinal=2, attempt_id='44444444-4444-4444-8444-444444444444',
                  started_elapsed_ms=101, ended_elapsed_ms=102)
    capture(retried).update(attempts=[first, second], ended_continuous_ns=1200000000,
                           submission={'state': 'invoked', 'invoked_elapsed_ms': 103})
    check('occupied_then_single_invocation', retried)
    for outcome, reason in [('transport_error', 'xpc_error'), ('timeout', 'rpc_timeout')]:
        changed = copy.deepcopy(retried)
        attempt = capture(changed)['attempts'][0]
        attempt.pop('control')
        attempt.update(outcome=outcome, error=error('acquisition', reason, outcome == 'transport_error'))
        check('acquisition_' + outcome + '_then_grant', changed)

    exhausted = copy.deepcopy(occupied)
    value = capture(exhausted)
    value.update(acquisition_stop='attempt_limit', terminal='acquisition_failed',
                 error=error('acquisition', 'attempt_limit'), attempts=[])
    for index in range(256):
        attempt = copy.deepcopy(capture(occupied)['attempts'][0])
        attempt.update(ordinal=index + 1, attempt_id=f'{index + 1:08x}-1111-4111-8111-111111111111',
                       started_elapsed_ms=index * 101, ended_elapsed_ms=index * 101 + 1)
        value['attempts'].append(attempt)
    check('all_acquisition_attempts_retained', exhausted)

    invalid_control = fail_terminal(copy.deepcopy(baseline), 'protocol_error',
                                   error('acquisition', 'unsupported_protocol'), invoked=False)
    value = capture(invalid_control)
    value.update(acquisition_stop='protocol_error')
    value['attempts'][0].update(outcome='protocol_error',
        error=error('acquisition', 'unsupported_protocol'),
        control={'bytes_received': 10, 'sha256': 'c' * 64})
    check('unadmitted_control_only_count_and_hash', invalid_control)
    invalid_submission_control = fail_terminal(copy.deepcopy(baseline), 'protocol_error',
                                               error('submission', 'invalid_control'))
    capture(invalid_submission_control)['submission_refusal'] = {'bytes_received': 0, 'sha256': 'd' * 64}
    check('unadmitted_submission_control_only_count_and_hash', invalid_submission_control)

    local = fail_terminal(copy.deepcopy(baseline), 'local_error',
                          error('local', 'input_read_failed'), invoked=False)
    capture(local).update(acquisition_stop='local_error', attempts=[])
    check('local_failure_without_acquisition', local)
    initial_clock = copy.deepcopy(local)
    capture(initial_clock).update(clock_available=False, error=error('local', 'clock_error'))
    for key in ('started_continuous_ns', 'deadline_continuous_ns', 'ended_continuous_ns'):
        capture(initial_clock).pop(key)
    check('initial_clock_failure_without_invented_timestamps', initial_clock)
    explicit_null_clock = copy.deepcopy(initial_clock)
    capture(explicit_null_clock).update(started_continuous_ns=None, deadline_continuous_ns=None,
                                       ended_continuous_ns=None)
    check('initial_clock_failure_nullable_timestamps', explicit_null_clock)
    invoked_clock = fail_terminal(copy.deepcopy(baseline), 'local_error', error('local', 'clock_error'))
    capture(invoked_clock).update(clock_available=False, ended_continuous_ns=None)
    check('invoked_clock_failure_preserves_prior_readings', invoked_clock)
    retry_clock = copy.deepcopy(occupied)
    capture(retry_clock).update(clock_available=False, ended_continuous_ns=None, acquisition_stop='local_error',
                                terminal='local_error', error=error('local', 'clock_error'))
    check('clock_failure_between_attempts_preserves_completed_occupied', retry_clock)

    # A rejected parsed transport is retained, but no descendant can project a
    # submission or provide host records. Validation rejects falsely admitted
    # copies independently of the controller's classification.
    def rejected(name, value, status='malformed', source=baseline):
        errors = validate_capture(value)
        assert errors, (name, value)
        document = copy.deepcopy(source)
        client(document).update(transport=value, transport_admission=status,
            transport_error='constructed admission refusal', submission='unknown', runner_reply_error=None)
        document['data']['runner_result'] = None
        check('retained_' + name, document)
        falsely_admitted = copy.deepcopy(document)
        client(falsely_admitted).update(transport_admission='accepted', transport_error=None)
        check('reject_' + name, falsely_admitted, 'transport admission')

    for version in (contract.RUNNER_PROTOCOL - 1, contract.RUNNER_PROTOCOL + 1):
        opaque = {'protocol_version': version, 'unrecognized': {'attempts': [False]},
                  'submission': {'state': 'invoked'}, 'runner_reply': 'not current schema'}
        assert len(validate_capture(opaque)) == 1
        rejected('version_' + str(version), opaque, 'unsupported')
    for name, value in [('array', []), ('string', 'retained'), ('boolean', False), ('number', 2),
                        ('version_boolean', {'protocol_version': True}),
                        ('version_float', {'protocol_version': 2.0}),
                        ('version_string', {'protocol_version': '2'}), ('version_missing', {})]:
        rejected(name, value)

    faults = [
        ('missing_kind', lambda c: c.pop('kind')),
        ('unknown_field', lambda c: c.update(worker_pid=333)),
        ('client_pid_boolean', lambda c: c.update(client_pid=True)),
        ('clock_basis', lambda c: c.update(clock='wall_clock')),
        ('missing_clock_availability', lambda c: c.pop('clock_available')),
        ('clock_availability_type', lambda c: c.update(clock_available=0)),
        ('missing_available_clock', lambda c: c.pop('ended_continuous_ns')),
        ('unavailable_clock_with_reply', lambda c: c.update(clock_available=False)),
        ('clock_backwards', lambda c: c.update(ended_continuous_ns=0)),
        ('clock_overflow', lambda c: c.update(started_continuous_ns=2**64)),
        ('timeout_zero', lambda c: c.update(timeout_ms=0)),
        ('missing_attempts', lambda c: c.pop('attempts')),
        ('nonobject_attempt', lambda c: c.update(attempts=[[]])),
        ('ordinal', lambda c: c['attempts'][0].update(ordinal=0)),
        ('attempt_uuid', lambda c: c['attempts'][0].update(attempt_id='not-a-uuid')),
        ('attempt_time', lambda c: c['attempts'][0].update(ended_elapsed_ms=9999)),
        ('attempt_backwards', lambda c: c['attempts'][0].update(started_elapsed_ms=2)),
        ('no_grant', lambda c: c.update(attempts=[])),
        ('no_control', lambda c: c['attempts'][0].pop('control')),
        ('credential_retained', lambda c: c['attempts'][0]['control'].update(reservation_id='secret')),
        ('control_wrong_status', lambda c: c['attempts'][0]['control'].update(status='occupied')),
        ('control_hash', lambda c: c['attempts'][0]['control'].update(sha256='z' * 64)),
        ('control_too_large', lambda c: c['attempts'][0]['control'].update(bytes_received=65537)),
        ('host_pid', lambda c: c['attempts'][0]['control'].update(host_pid=0)),
        ('host_instance', lambda c: c['attempts'][0]['control'].update(host_instance='kernel-generation')),
        ('lease_exceeded', lambda c: c['attempts'][0]['control'].update(lease_ms=5001)),
        ('lease_absent', lambda c: c['attempts'][0]['control'].pop('lease_ms')),
        ('invocation_absent', lambda c: c['submission'].pop('invoked_elapsed_ms')),
        ('invocation_before_grant', lambda c: c['submission'].update(invoked_elapsed_ms=0)),
        ('invocation_after_capture', lambda c: c['submission'].update(invoked_elapsed_ms=101)),
        ('not_invoked_with_time', lambda c: c['submission'].update(state='not_invoked')),
        ('unknown_submission', lambda c: c['submission'].update(state='unknown')),
        ('unknown_stop', lambda c: c.update(acquisition_stop={})),
        ('unknown_terminal', lambda c: c.update(terminal=[])),
        ('missing_reply', lambda c: c.pop('runner_reply')),
        ('null_reply', lambda c: c.update(runner_reply=None)),
        ('received_count', lambda c: c['runner_reply'].update(bytes_received=1)),
        ('retained_count', lambda c: c['runner_reply'].update(bytes_retained=1)),
        ('negative_count', lambda c: c['runner_reply'].update(bytes_received=-1)),
        ('boolean_count', lambda c: c['runner_reply'].update(bytes_received=True)),
        ('truncation', lambda c: c['runner_reply'].update(truncated=True)),
        ('encoded_bytes', lambda c: c['runner_reply'].update(data_base64='%%%%')),
        ('noncanonical_base64', lambda c: c['runner_reply'].update(data_base64='Zh==', bytes_received=1, bytes_retained=1)),
        ('reply_with_error', lambda c: c.update(error=error('submission', 'xpc_error'))),
        ('combined_faults', lambda c: (c['runner_reply'].update(data_base64='?'), c['submission'].update(state='unknown'))),
    ]
    for name, mutate in faults:
        value = copy.deepcopy(capture(baseline))
        mutate(value)
        if name == 'combined_faults':
            assert len(validate_capture(value)) >= 2
        rejected(name, value)
    for name, source, mutate in [
        ('attempt_after_invocation', retried, lambda c: c['attempts'].reverse()),
        ('repeated_attempt_uuid', retried, lambda c: c['attempts'][1].update(attempt_id=c['attempts'][0]['attempt_id'])),
        ('early_attempt_limit', exhausted, lambda c: c['attempts'].pop()),
        ('unadmitted_control_claim', invalid_control, lambda c: c['attempts'][0]['control'].update(host_pid=123)),
        ('error_reason', local, lambda c: c['error'].update(reason='arbitrary')),
        ('terminal_error_stage', local, lambda c: c['error'].update(stage='submission')),
        ('terminal_error_reason_disagrees', occupied, lambda c: c['error'].update(reason='rpc_timeout')),
        ('error_oversized_utf8', local, lambda c: c['error'].update(message='é' * 513)),
        ('error_unpaired_native', local, lambda c: c['error'].update(code=4097)),
        ('error_absent_domain_truncated', local, lambda c: c['error'].update(domain_truncated=True)),
        ('refusal_error', refused, lambda c: c.update(error=error('submission', 'invalid_control'))),
        ('refusal_lease', refused, lambda c: c['submission_refusal'].update(lease_ms=1)),
        ('client_terminal_host_payload', local, lambda c: c.update(runner_reply=capture(baseline)['runner_reply'])),
        ('clock_failure_wrong_reason', initial_clock, lambda c: c['error'].update(reason='input_read_failed')),
        ('clock_failure_invented_end', invoked_clock, lambda c: c.update(ended_continuous_ns=1200000000)),
        ('early_timeout', occupied, lambda c: c.update(ended_continuous_ns=1200000000)),
        ('unadmitted_submission_control_claim', invalid_submission_control,
         lambda c: c['submission_refusal'].update(host_pid=125)),
    ]:
        value = copy.deepcopy(capture(source))
        mutate(value)
        rejected(name, value, source=source)

    for name, changes, status in [
        ('absent', {}, 'missing'),
        ('parsed_null', {'stdout_bytes_received': 4, 'stdout_bytes_retained': 4}, 'malformed'),
        ('truncated_stdout', {'stdout_truncated': True}, 'malformed'),
        ('invalid_outer_json', {'stdout_parse_error': 'constructed parse error'}, 'malformed'),
        ('capture_failed', {'stdout_capture_error': 'constructed capture error'}, 'malformed'),
    ]:
        document = copy.deepcopy(baseline)
        client(document).update(transport=None, transport_admission=status, transport_error='constructed refusal',
                                submission='unknown', **changes)
        document['data']['runner_result'] = None
        check(name + '_submission_unknown', document)
        client(document)['submission'] = 'not_invoked'
        check(name + '_cannot_invent_not_invoked', document, 'submission projection')

    delivery = copy.deepcopy(baseline)
    client(delivery).update(request_delivery={'bytes_written': 1, 'error': 'broken pipe'},
        transport_admission='delivery_failed', transport_error='delivery failed', submission='unknown')
    delivery['data']['runner_result'] = None
    check('delivery_error_precedes_admitted_looking_capture', delivery)
    client(delivery)['transport'] = {'protocol_version': 999, 'anything': [False]}
    check('delivery_error_precedes_unsupported_capture', delivery)

    for name, raw in [('empty', b''), ('invalid_utf8', b'\xff'), ('invalid_json', b'{'),
                      ('non_json_constant', b'NaN')]:
        document = copy.deepcopy(baseline)
        capture(document)['runner_reply'].update(bytes_received=len(raw), bytes_retained=len(raw),
            data_base64=base64.b64encode(raw).decode())
        document['data']['runner_result'] = None
        client(document)['runner_reply_error'] = 'constructed host-byte parse refusal'
        check('received_' + name + '_host_bytes', document)
        client(document)['runner_reply_error'] = None
        check('received_' + name + '_requires_diagnostic', document, 'unreadable host bytes')

    contradicted = copy.deepcopy(baseline)
    contradicted['data']['runner_result']['error'] = 'different host document'
    check('contradictory_host_result', contradicted, 'exact captured host reply bytes')
    no_carrier = copy.deepcopy(baseline)
    no_carrier['data']['runner_client'] = None
    check('host_result_requires_capture', no_carrier, 'requires an accepted runner client capture')
    fabricated_host = copy.deepcopy(local)
    fabricated_host['data']['runner_result'] = reply
    check('client_failure_is_not_host_reply', fabricated_host, 'client observations cannot supply a host result')
