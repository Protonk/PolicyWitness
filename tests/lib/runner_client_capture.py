"""Independent admission of protocol-2 client observations and exact host bytes.

This reader never treats a client terminal or a reservation control as a host
RunResult. Unsupported versions stop admission before descendant inspection.
No production encoder, parser, classifier or limit manifest supplies its rules.
"""
import base64
import binascii
from copy import deepcopy
import json
import re
import uuid

import contract

REPLY_BYTES = 64 * 1024 * 1024
U64_MAX = 2**64 - 1
I64_MAX = 2**63 - 1
STOPS = ('granted', 'overall_deadline', 'attempt_limit', 'protocol_error', 'local_error')
OUTCOMES = ('granted', 'occupied', 'transport_error', 'timeout', 'protocol_error', 'local_error')
TERMINALS = ('runner_reply', 'xpc_error', 'xpc_timeout', 'acquisition_failed',
             'submission_refused', 'protocol_error', 'local_error')
REASONS = ('xpc_error', 'interrupted', 'invalidated', 'rpc_timeout', 'overall_deadline',
           'attempt_limit', 'invalid_control', 'unsupported_protocol', 'control_too_large',
           'proxy_type_mismatch', 'clock_error', 'encoding_failed', 'input_read_failed')


def _integer(value, minimum=0, maximum=I64_MAX):
    return type(value) is int and minimum <= value <= maximum


def _uuid(value):
    if not isinstance(value, str):
        return False
    try:
        return str(uuid.UUID(value)) == value.lower()
    except ValueError:
        return False


def _object(value, required, optional, path, errors):
    if not isinstance(value, dict):
        errors.append(path + ' is not an object')
        return False
    missing, extra = set(required) - value.keys(), value.keys() - set(required) - set(optional)
    if missing:
        errors.append(path + ' missing fields: ' + ', '.join(sorted(missing)))
    if extra:
        errors.append(path + ' unknown fields: ' + ', '.join(sorted(extra)))
    # Codable omits nil fields; JSON null has the same absence semantics.
    # Admission operates on a private copy, never changing retained evidence.
    for key in optional:
        if key in value and value[key] is None:
            del value[key]
    return True


def _error(value, path, errors, stage=None):
    if not _object(value, ('stage', 'reason', 'message', 'domain_truncated', 'message_truncated'),
                   ('domain', 'code'), path, errors):
        return
    if value.get('stage') not in ('acquisition', 'submission', 'local') or (
            stage is not None and value.get('stage') != stage):
        errors.append(path + ' invalid stage')
    if value.get('reason') not in REASONS:
        errors.append(path + ' invalid reason')
    for key, bound in (('message', 1024), ('domain', 128)):
        if key not in value and key == 'domain':
            continue
        text = value.get(key)
        try:
            count = len(text.encode('utf-8')) if isinstance(text, str) else None
        except UnicodeEncodeError:
            count = None
        if count is None or count > bound:
            errors.append(path + '.' + key + ' exceeds its UTF-8 bound or is not a string')
        elif value.get(key + '_truncated') is True and count < bound - 3:
            errors.append(path + '.' + key + ' truncation flag lacks a bounded prefix')
    for key in ('domain_truncated', 'message_truncated'):
        if type(value.get(key)) is not bool:
            errors.append(path + '.' + key + ' is not boolean')
    if ('domain' in value) != ('code' in value) or (
            'code' in value and not _integer(value['code'], -(2**63))):
        errors.append(path + ' native domain and code must be paired')
    if 'domain' not in value and value.get('domain_truncated') is not False:
        errors.append(path + ' absent domain cannot be truncated')


def _control(value, path, errors, expected=None):
    if not _object(value, ('bytes_received', 'sha256'),
                   ('status', 'host_pid', 'host_instance', 'lease_ms', 'reason'), path, errors):
        return
    if not _integer(value.get('bytes_received')):
        errors.append(path + ' invalid byte count')
    digest = value.get('sha256')
    if not isinstance(digest, str) or re.fullmatch('[0-9a-f]{64}', digest) is None:
        errors.append(path + ' invalid SHA-256')
    if expected is None:
        if set(value) - {'bytes_received', 'sha256'}:
            errors.append(path + ' rejected control carries interpreted fields')
        return
    if value.get('status') != expected:
        errors.append(path + ' status disagrees with observation')
    if not _integer(value.get('bytes_received'), 1, 65536):
        errors.append(path + ' admitted control exceeds byte bound')
    if not _integer(value.get('host_pid'), 1, 2**31 - 1) or not _uuid(value.get('host_instance')):
        errors.append(path + ' invalid host-reported identity')
    if expected == 'granted':
        if not _integer(value.get('lease_ms'), 1, 5000) or 'reason' in value:
            errors.append(path + ' invalid granted lease or reason')
    elif expected == 'occupied':
        if 'lease_ms' in value or 'reason' in value:
            errors.append(path + ' occupied control carries grant/refusal fields')
    elif expected == 'reservation_refused':
        if 'lease_ms' in value or value.get('reason') not in ('wrong', 'expired', 'absent', 'consumed', 'clock_error'):
            errors.append(path + ' invalid reservation refusal')


def validate_capture(value):
    """Return errors, gating the protocol version before any child field."""
    if not isinstance(value, dict):
        return ['malformed runner client capture: not an object']
    version = value.get('protocol_version')
    if type(version) is not int:
        return ['malformed runner client capture: protocol_version is not an integer']
    if version != contract.RUNNER_PROTOCOL:
        return [f'unsupported runner client capture: protocol_version {version}']
    value = deepcopy(value)
    errors = []
    _object(value, ('kind', 'protocol_version', 'client_pid', 'clock', 'clock_available', 'timeout_ms', 'attempts',
                    'acquisition_stop', 'submission', 'terminal'),
            ('error', 'runner_reply', 'submission_refusal', 'started_continuous_ns',
             'deadline_continuous_ns', 'ended_continuous_ns'), 'capture', errors)
    if value.get('kind') != 'runner_client_capture':
        errors.append('capture invalid kind')
    if not _integer(value.get('client_pid'), 1, 2**31 - 1):
        errors.append('capture invalid client PID')
    if value.get('clock') != 'mach_continuous_time_ns':
        errors.append('capture invalid clock basis')
    available = value.get('clock_available')
    if type(available) is not bool:
        errors.append('capture clock_available is not boolean')
    for key in ('started_continuous_ns', 'deadline_continuous_ns', 'ended_continuous_ns', 'timeout_ms'):
        if key != 'timeout_ms' and available is False and value.get(key) is None:
            continue
        if not _integer(value.get(key), 1 if key == 'timeout_ms' else 0, U64_MAX):
            errors.append('capture invalid ' + key)
    start, end = value.get('started_continuous_ns'), value.get('ended_continuous_ns')
    elapsed = None
    if _integer(start, 0, U64_MAX) and _integer(end, 0, U64_MAX):
        if end < start:
            errors.append('capture clock moved backwards')
        else:
            elapsed = (end - start) // 1_000_000
    stop, terminal = value.get('acquisition_stop'), value.get('terminal')
    if stop not in STOPS:
        errors.append('capture invalid acquisition stop')
    if terminal not in TERMINALS:
        errors.append('capture invalid terminal')
    if available is False and (terminal != 'local_error' or not isinstance(value.get('error'), dict)
                               or value['error'].get('reason') != 'clock_error'):
        errors.append('capture unavailable clock requires local clock_error')
    if available is False and end is not None:
        errors.append('capture unavailable clock cannot invent an end timestamp')
    attempts = value.get('attempts')
    if not isinstance(attempts, list) or len(attempts) > 256:
        errors.append('capture attempts must be an array of at most 256 observations')
        attempts = []
    if (start is None or value.get('deadline_continuous_ns') is None) and attempts:
        errors.append('capture cannot acquire before observing its start clock and deadline')
    previous_end, ids, grants = 0, set(), []
    for index, attempt in enumerate(attempts, 1):
        path = f'capture.attempts[{index - 1}]'
        if not _object(attempt, ('ordinal', 'attempt_id', 'outcome'),
                       ('control', 'error', 'started_elapsed_ms', 'ended_elapsed_ms'), path, errors):
            continue
        if not _integer(attempt.get('ordinal'), index, index):
            errors.append(path + ' ordinal is not its one-based position')
        attempt_id = attempt.get('attempt_id')
        if not _uuid(attempt_id) or attempt_id.lower() in ids:
            errors.append(path + ' invalid or repeated attempt UUID')
        else:
            ids.add(attempt_id.lower())
        begin, finish = attempt.get('started_elapsed_ms'), attempt.get('ended_elapsed_ms')
        valid_begin = _integer(begin, 0, U64_MAX)
        valid_finish = _integer(finish, 0, U64_MAX)
        if not ((valid_begin or available is False and begin is None) and
                (valid_finish or available is False and finish is None)):
            errors.append(path + ' invalid elapsed times')
        elif ((valid_begin and begin < previous_end) or
              (valid_begin and valid_finish and finish < begin) or
              (elapsed is not None and valid_finish and finish > elapsed)):
            errors.append(path + ' elapsed times disagree with ordered capture')
        elif valid_finish:
            previous_end = finish
        outcome = attempt.get('outcome')
        if outcome not in OUTCOMES:
            errors.append(path + ' invalid outcome')
        if index < len(attempts) and outcome in ('granted', 'protocol_error', 'local_error'):
            errors.append(path + ' terminal acquisition cannot be retried')
        if outcome == 'granted':
            grants.append(index)
        admitted = outcome in ('granted', 'occupied')
        if admitted and 'control' not in attempt:
            errors.append(path + ' admitted acquisition lacks control observation')
        if 'control' in attempt:
            _control(attempt['control'], path + '.control', errors, outcome if admitted else None)
            if not admitted and outcome != 'protocol_error':
                errors.append(path + ' received control requires a protocol observation')
        if admitted == ('error' in attempt):
            errors.append(path + ' acquisition error disagrees with outcome')
        if 'error' in attempt:
            _error(attempt['error'], path + '.error', errors)
            if isinstance(attempt['error'], dict):
                stage, reason = attempt['error'].get('stage'), attempt['error'].get('reason')
                if stage not in ('acquisition', 'local') or (
                        stage == 'local' and reason not in ('clock_error', 'encoding_failed')):
                    errors.append(path + ' invalid acquisition error stage/reason')
                allowed_reasons = {
                    'transport_error': ('xpc_error', 'interrupted', 'invalidated'),
                    'timeout': ('rpc_timeout', 'overall_deadline'),
                    'protocol_error': ('invalid_control', 'unsupported_protocol', 'control_too_large'),
                    'local_error': ('clock_error', 'encoding_failed', 'proxy_type_mismatch'),
                }.get(outcome, ()) if isinstance(outcome, str) else ()
                if reason not in allowed_reasons:
                    errors.append(path + ' error reason disagrees with acquisition outcome')
    if (stop == 'granted' and grants != [len(attempts)]) or (stop != 'granted' and grants):
        errors.append('capture grant must be the final acquisition and stop further acquisition')
    if stop == 'attempt_limit' and len(attempts) != 256:
        errors.append('capture attempt_limit requires all 256 attempts')
    deadline = value.get('deadline_continuous_ns')
    if (stop == 'overall_deadline' and _integer(deadline, 0, U64_MAX)
            and _integer(end, 0, U64_MAX) and end < deadline):
        errors.append('capture overall deadline was not reached')
    if (stop in ('protocol_error', 'local_error') and not (stop == 'local_error' and available is False) and attempts and
            (not isinstance(attempts[-1], dict) or attempts[-1].get('outcome') != stop)):
        errors.append('capture acquisition stop disagrees with final attempt')
    submission = value.get('submission')
    state = None
    if _object(submission, ('state',), ('invoked_elapsed_ms',), 'capture.submission', errors):
        state = submission.get('state')
        if state not in ('not_invoked', 'invoked'):
            errors.append('capture invalid submission state')
        if state == 'invoked':
            invoked = submission.get('invoked_elapsed_ms')
            if stop != 'granted' or not (_integer(invoked, previous_end, U64_MAX) or
                                        available is False and invoked is None) or (
                    elapsed is not None and _integer(invoked, 0, U64_MAX) and invoked > elapsed):
                errors.append('capture invocation requires the final grant and ordered elapsed time')
        elif 'invoked_elapsed_ms' in submission:
            errors.append('capture not_invoked carries invocation time')
    if terminal in ('runner_reply', 'submission_refused', 'xpc_error') and state != 'invoked':
        errors.append('capture terminal requires invoked submission')
    if state == 'not_invoked':
        expected = {'granted': 'xpc_timeout', 'overall_deadline': 'xpc_timeout',
                    'attempt_limit': 'acquisition_failed', 'protocol_error': 'protocol_error',
                    'local_error': 'local_error'}.get(stop) if isinstance(stop, str) else None
        if terminal != expected and not (stop == 'granted' and terminal == 'local_error'):
            errors.append('capture uninvoked terminal disagrees with acquisition stop')
    if state == 'invoked' and (terminal == 'acquisition_failed' or terminal == 'local_error' and available is not False):
        errors.append('capture invoked submission cannot return to acquisition or local preparation')
    if ('runner_reply' in value) != (terminal == 'runner_reply'):
        errors.append('capture host reply presence disagrees with terminal')
    if terminal == 'submission_refused' and 'submission_refusal' not in value:
        errors.append('capture refusal presence disagrees with terminal')
    if 'submission_refusal' in value:
        if state != 'invoked' or terminal not in ('submission_refused', 'protocol_error'):
            errors.append('capture refusal presence disagrees with terminal')
        _control(value['submission_refusal'], 'capture.submission_refusal', errors,
                 'reservation_refused' if terminal == 'submission_refused' else None)
    if 'error' in value:
        _error(value['error'], 'capture.error', errors)
        if isinstance(value['error'], dict):
            stage, reason = value['error'].get('stage'), value['error'].get('reason')
            expected_stage = 'submission' if state == 'invoked' else 'acquisition'
            if terminal == 'local_error':
                coherent = (stage == 'local' and reason in ('clock_error', 'encoding_failed', 'input_read_failed') or
                            stage == 'acquisition' and reason == 'proxy_type_mismatch')
            else:
                reasons = {'xpc_error': ('xpc_error', 'interrupted', 'invalidated', 'proxy_type_mismatch'),
                           'xpc_timeout': ('overall_deadline',), 'acquisition_failed': ('attempt_limit',),
                           'protocol_error': ('invalid_control', 'unsupported_protocol', 'control_too_large')}
                coherent = stage == expected_stage and reason in (reasons.get(terminal, ()) if isinstance(terminal, str) else ())
            if not coherent:
                errors.append('capture terminal error stage/reason disagrees with state')
    if terminal in ('runner_reply', 'submission_refused') and 'error' in value:
        errors.append('capture reply/refusal carries a client error')
    if terminal not in ('runner_reply', 'submission_refused') and 'error' not in value:
        errors.append('capture failed terminal lacks structured error')
    if terminal == 'xpc_timeout' and isinstance(value.get('error'), dict):
        if value['error'].get('reason') != 'overall_deadline' or (
                _integer(end, 0, U64_MAX) and _integer(deadline, 0, U64_MAX) and end < deadline):
            errors.append('capture xpc_timeout requires the reached overall deadline')
    if 'runner_reply' in value:
        reply = value['runner_reply']
        if _object(reply, ('bytes_received', 'bytes_retained', 'truncated', 'data_base64'), (),
                   'capture.runner_reply', errors):
            received, retained = reply.get('bytes_received'), reply.get('bytes_retained')
            counts = _integer(received) and _integer(retained, 0, REPLY_BYTES)
            if not counts or retained != min(received, REPLY_BYTES):
                errors.append('capture.runner_reply invalid received/retained byte counts')
            if type(reply.get('truncated')) is not bool or (
                    counts and reply.get('truncated') != (received > retained)):
                errors.append('capture.runner_reply truncated marker disagrees with counts')
            encoded = reply.get('data_base64')
            if not isinstance(encoded, str) or len(encoded) > 4 * ((REPLY_BYTES + 2) // 3):
                errors.append('capture.runner_reply invalid encoded byte string')
            else:
                try:
                    raw = base64.b64decode(encoded, validate=True)
                    if base64.b64encode(raw).decode('ascii') != encoded or len(raw) != retained:
                        errors.append('capture.runner_reply encoded bytes disagree with retained count or canonical base64')
                except (ValueError, binascii.Error):
                    errors.append('capture.runner_reply malformed base64')
    return errors


def validate_client(client, runner):
    """Check controller admission/projection without interpreting rejected bodies."""
    if client is None:
        return [] if runner is None else ['host result requires an accepted runner client capture']
    if not isinstance(client, dict):
        return ['data.runner_client is not an object']
    errors = []
    required = ('request_delivery', 'transport', 'transport_admission', 'transport_error',
                'submission', 'runner_reply_error')
    for key in required:
        if key not in client:
            errors.append('data.runner_client missing ' + key)
    delivery = client.get('request_delivery')
    delivery_failed = False
    if delivery is not None:
        if not isinstance(delivery, dict) or not _integer(delivery.get('bytes_written')) or (
                delivery.get('error') is not None and not isinstance(delivery['error'], str)):
            errors.append('invalid data.runner_client.request_delivery')
        elif delivery.get('error') is not None:
            delivery_failed = True
    capture = client.get('transport')
    outer_failed = (client.get('stdout_truncated') is True or
                    client.get('stdout_parse_error') is not None or
                    client.get('stdout_capture_error') is not None)
    if delivery_failed:
        expected, capture_errors = 'delivery_failed', []
    elif outer_failed:
        expected, capture_errors = 'malformed', []
        if capture is not None:
            errors.append('incomplete or unparsed stdout cannot supply a parsed transport capture')
    elif capture is None:
        received = client.get('stdout_bytes_received')
        # A complete parsed JSON null is malformed capture content; empty
        # stdout supplies no parsed value. Both transport slots serialize null.
        expected, capture_errors = ('malformed' if _integer(received, 1) else 'missing'), []
    else:
        capture_errors = validate_capture(capture)
        expected = ('unsupported' if capture_errors and capture_errors[0].startswith('unsupported ')
                    else 'malformed' if capture_errors else 'accepted')
    if client.get('transport_admission') != expected:
        errors.append('runner client transport admission disagrees with independent admission' +
                      (': ' + '; '.join(capture_errors) if capture_errors else ''))
    diagnostic = client.get('transport_error')
    if expected == 'accepted':
        if diagnostic is not None:
            errors.append('accepted runner client capture carries an admission error')
    elif not isinstance(diagnostic, str) or not diagnostic:
        errors.append('rejected runner client capture lacks an admission error')
    projection = capture['submission']['state'] if expected == 'accepted' else 'unknown'
    if client.get('submission') != projection:
        errors.append('runner client submission projection requires admitted complete capture')
    reply_error = client.get('runner_reply_error')
    if expected != 'accepted':
        if runner is not None or reply_error is not None:
            errors.append('rejected client capture cannot supply host result or host-byte diagnostics')
        return errors
    if capture['terminal'] != 'runner_reply':
        if runner is not None or reply_error is not None:
            errors.append('client observations cannot supply a host result or host-byte diagnostics')
        return errors
    try:
        parsed = host_reply(capture)
    except ValueError:
        if runner is not None or not isinstance(reply_error, str) or not reply_error:
            errors.append('unreadable host bytes require null host result and a host-byte diagnostic')
    else:
        if reply_error is not None:
            errors.append('complete parsed host bytes carry a host-byte diagnostic')
        # JSON scalar type matters: bool and int compare equal in Python.
        if json.dumps(parsed, sort_keys=True) != json.dumps(runner, sort_keys=True):
            errors.append('host result differs from exact captured host reply bytes')
    return errors


def host_reply(value):
    """Parse exact admitted complete host bytes, without reading host semantics."""
    errors = validate_capture(value)
    if errors:
        raise ValueError(errors[0])
    if value['terminal'] != 'runner_reply':
        raise ValueError('client capture has no host reply')
    reply = value['runner_reply']
    if reply['truncated']:
        raise ValueError('host reply bytes are truncated')
    try:
        raw = base64.b64decode(reply['data_base64'], validate=True)
        def invalid_constant(text):
            raise ValueError('non-JSON numeric constant ' + text)
        return json.loads(raw.decode('utf-8'), parse_constant=invalid_constant)
    except (UnicodeDecodeError, ValueError, binascii.Error) as error:
        raise ValueError('host reply bytes are not UTF-8 JSON: ' + str(error)) from error
