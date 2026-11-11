"""Independent checks of native extension and fresh file observations.

These rules inspect published evidence, not policy text or effective permissions.
The lifecycle oracle separately checks action publication against worker slots.
"""
import re


def ordered_actions(runner):
    ordinary = runner.get('steps')
    ordinary = ordinary if isinstance(ordinary, list) else []
    events = runner.get('extension_events')
    if not isinstance(events, list) or not events:
        return ordinary
    phases = runner.get('phases')
    ids = [identity for phase in phases if isinstance(phase, dict) and isinstance(phase.get('action_ids'), list)
           for identity in phase.get('action_ids', []) if isinstance(identity, str)] if isinstance(phases, list) else []
    positions = {identity: i for i, identity in enumerate(ids)}
    return sorted(ordinary + events, key=lambda action: positions.get(
        action.get('step_id') if isinstance(action, dict) else None, len(ids)))


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _reference(value):
    return isinstance(value, str) and 0 < len(value.encode('utf-8')) <= 63 and '\0' not in value


def _identity(value):
    return isinstance(value, dict) and all(_integer(value.get(k), 0, (1 << bits) - 1)
        for k, bits in [('device', 64), ('inode', 64), ('mode', 32), ('uid', 32), ('gid', 32)])


def validate_fresh_read(attempt):
    read = attempt.get('fresh_read')
    expected = attempt.get('requested_kind') == 'file' and attempt.get('requested_action') == 'read_fresh' \
        and attempt.get('result_source') == 'worker'
    if read is None:
        return ['completed fresh read lacks syscall observations'] if expected else []
    if not expected or not isinstance(read, dict):
        return ['fresh read requires a completed read_fresh attempt']
    errors = []
    opened = read.get('open_rc')
    if not _integer(opened, -1, (1 << 31) - 1):
        return ['invalid fresh read open result']
    if opened == -1:
        if not _integer(read.get('open_errno'), 0, (1 << 31) - 1) or any(read.get(k) is not None
                for k in ('read_rc', 'read_errno', 'stat_rc', 'stat_errno', 'identity', 'close_rc', 'close_errno', 'content_hex')):
            errors.append('failed fresh open cannot supply read/stat/close evidence')
        if (attempt.get('rc'), attempt.get('errno'), attempt.get('outcome')) != (-1, read.get('open_errno') or None, 'read_failed'):
            errors.append('fresh open failure disagrees with attempt')
        return errors
    if read.get('open_errno') is not None:
        errors.append('successful fresh open cannot supply failure errno')
    for operation in ('read', 'stat', 'close'):
        rc, errno = read.get(operation + '_rc'), read.get(operation + '_errno')
        if not _integer(rc, -1, 64 if operation == 'read' else 0):
            errors.append('invalid fresh ' + operation + ' result')
        if (rc == -1 and not _integer(errno, 0, (1 << 31) - 1)) or (rc != -1 and errno is not None):
            errors.append('fresh ' + operation + ' errno lacks failure result')
    if (read.get('stat_rc') == 0 and not _identity(read.get('identity'))) or \
            (read.get('stat_rc') != 0 and read.get('identity') is not None):
        errors.append('fresh stat identity lacks successful stat')
    count, content = read.get('read_rc'), read.get('content_hex')
    if _integer(count, 0, 64):
        if not isinstance(content, str) or len(content) != count * 2 or re.fullmatch('[0-9a-f]*', content) is None:
            errors.append('fresh read bytes disagree with native byte count')
    elif content is not None:
        errors.append('failed fresh read cannot supply content')
    # The aggregate status preserves the first failure in syscall order.
    failed = [k for k in ('stat', 'read', 'close') if read.get(k + '_rc') == -1]
    expected_status = (-1, read.get(failed[0] + '_errno') or None, 'read_failed') if failed else (0, None, 'ok')
    if (attempt.get('rc'), attempt.get('errno'), attempt.get('outcome')) != expected_status:
        errors.append('fresh syscall results disagree with attempt')
    return errors


def validate_fresh_write(attempt):
    write = attempt.get('fresh_write')
    action = attempt.get('requested_action')
    expected = attempt.get('requested_kind') == 'file' and action in ('write_fresh', 'create_fresh') \
        and attempt.get('result_source') == 'worker'
    if write is None:
        return ['completed fresh write lacks syscall observations'] if expected else []
    if not expected or not isinstance(write, dict):
        return ['fresh write requires a completed fresh-write attempt']
    errors = []
    create = action == 'create_fresh'
    failures = []

    def syscall(operation, maximum=0):
        result, error = write.get(operation + '_rc'), write.get(operation + '_errno')
        if not _integer(result, -1, maximum):
            errors.append('invalid fresh write ' + operation + ' result')
            return None
        if (result == -1 and not _integer(error, 0, (1 << 31) - 1)) or (result >= 0 and error is not None):
            errors.append('fresh write ' + operation + ' errno lacks failure result')
        if result == -1:
            failures.append(error or None)
        return result

    def metadata(name, *, diagnostic=False):
        value = write.get(name)
        if not isinstance(value, dict) or not _integer(value.get('rc'), -1, 0):
            errors.append('invalid fresh write ' + name + ' observation')
            return
        rc, error = value['rc'], value.get('errno')
        if rc == -1:
            if not _integer(error, 0, (1 << 31) - 1) or value.get('identity') is not None or value.get('size') is not None:
                errors.append('failed fresh write ' + name + ' carries identity/size or lacks errno')
            if not diagnostic:
                failures.append(error or None)
        elif error is not None or not _identity(value.get('identity')) or not _integer(value.get('size'), -(1 << 63), (1 << 63) - 1):
            errors.append('successful fresh write ' + name + ' lacks identity/size or carries errno')

    if create:
        metadata('preopen_stat', diagnostic=True)
    elif write.get('preopen_stat') is not None:
        errors.append('write_fresh cannot supply preopen metadata')
    opened = syscall('open', (1 << 31) - 1)
    if opened == -1:
        if any(write.get(key) is not None for key in ('opened_stat', 'truncate_rc', 'truncate_errno',
                'truncated_stat', 'write_rc', 'write_errno', 'written_stat', 'close_rc', 'close_errno')):
            errors.append('failed fresh write open cannot supply later syscall observations')
    elif opened is not None:
        metadata('opened_stat')
        if create:
            if any(write.get(key) is not None for key in ('truncate_rc', 'truncate_errno', 'truncated_stat')):
                errors.append('create_fresh cannot supply truncation observations')
            transfer = True
        else:
            truncate = syscall('truncate')
            metadata('truncated_stat')
            transfer = truncate == 0
        if transfer:
            count = syscall('write', 1)
            if count == 0:
                failures.append(None)  # A short write supplies no failure errno.
            metadata('written_stat')
        elif any(write.get(key) is not None for key in ('write_rc', 'write_errno', 'written_stat')):
            errors.append('failed fresh truncation cannot supply write observations')
        syscall('close')
    status = (-1, failures[0], 'write_failed') if failures else (0, None, 'ok')
    if (attempt.get('rc'), attempt.get('errno'), attempt.get('outcome')) != status:
        errors.append('fresh write syscall results disagree with attempt')
    return errors


ACTOR_TRANSFER_STATUSES = ('none', 'delivered', 'custody_unavailable', 'recipient_rejected', 'recipient_timeout',
                           'recipient_unavailable', 'request_invalid', 'host_timeout', 'clock_fault', 'copy_mismatch')
ACTOR_UNAVAILABLE_REASONS = ('token_unavailable', 'handle_unavailable', 'native_api_unavailable', 'repeated_action',
                             'authority_channel_unavailable', 'delivery_unavailable')
ACTOR_SETUP_ESTABLISHED = ('applied', 'unapplied_declared')


def validate_actor_extensions(runner):
    """The actor form's extension rules, shared with the Swift encoder and the
    controller: every event names a live actor and one of its phases,
    references resolve in the resource tables to their owners, transfers carry
    no native result, and each status is published only by the shape it claims."""
    events = runner.get('extension_events')
    if not isinstance(events, list):
        return ['actor form lacks extension event table']
    actors = runner.get('actors')
    resources = runner.get('resources')
    transfers = runner.get('transfers')
    if not isinstance(actors, list) or not actors or not isinstance(resources, dict) or not isinstance(transfers, list):
        return ['actor form lacks actor, resource or transfer tables']
    if any(runner.get(k) is not None for k in ('extensions', 'runner_subprocess', 'policy_sha256', 'sandboxed_after_apply')):
        return ['actor form carries singular projections']
    tokens, deliveries, handles = (resources.get(k) for k in ('tokens', 'deliveries', 'handles'))
    if not all(isinstance(t, list) for t in (tokens, deliveries, handles)) or len(actors) > 8 or len(tokens) > 32 \
            or len(deliveries) > 64 or len(handles) > 64 or len(transfers) > 64 or len(events) > 32 + 128 + 64 + 64:
        return ['actor extension record capacity']
    errors = []
    phases = [p for p in runner.get('phases', []) if isinstance(p, dict)] if isinstance(runner.get('phases'), list) else []
    ids = [i for p in phases for i in p.get('action_ids', []) if isinstance(i, str)]
    by_actor = {a.get('actor_id'): a for a in actors if isinstance(a, dict)}
    consumed, released = {}, set()

    for table, key in ((tokens, 'token_ref'), (deliveries, 'delivery_ref'), (handles, 'handle_ref'),
                       (transfers, 'delivery_ref')):
        references = [r.get(key) for r in table if isinstance(r, dict)]
        if len(references) != len(table) or any(not _reference(r) for r in references) \
                or len(set(r for r in references if isinstance(r, str))) != len(references):
            errors.append('resource and transfer references must be unique')

    def before(first, second):
        return first in ids and second in ids and ids.index(first) < ids.index(second)

    def owned(table, **match):
        return any(isinstance(r, dict) and all(r.get(k) == v for k, v in match.items()) for r in table)

    for event in events:
        if not isinstance(event, dict):
            errors.append('extension event is not an object'); continue
        actor_id, sid = event.get('actor_id'), event.get('step_id')
        actor = by_actor.get(actor_id) if isinstance(actor_id, str) else None
        if actor is None:
            errors.append('extension event actor'); continue
        matches = [p for p in phases if p.get('phase_id') == event.get('phase_id')
                   and isinstance(p.get('action_ids'), list) and sid in p['action_ids']]
        if len(matches) != 1 or matches[0].get('actor_id') != actor_id:
            errors.append('extension event phase association'); continue
        phase = matches[0]
        if event.get('family') != 'file':
            errors.append('extension event family'); continue
        operation, status = event.get('operation'), event.get('status')
        native, errno = event.get('native_result'), event.get('errno')
        called, published = event.get('call_boundary_observed'), event.get('result_published')
        if type(called) is not bool or type(published) is not bool:
            errors.append('extension boundary/publication must be boolean')
        token, delivery, handle = event.get('token_ref'), event.get('delivery_ref'), event.get('handle_ref')
        if operation == 'issue':
            if not _reference(token) or not owned(tokens, token_ref=token, actor_id=actor_id, step_id=sid) \
                    or handle is not None or delivery is not None:
                errors.append('issue reference')
            if status == 'returned' and (native not in (0, 1) or type(event.get('native_nonnull')) is not bool or event['native_nonnull'] != (native == 1)):
                errors.append('issue nonnull disagrees with native result')
        elif operation == 'transfer':
            if not _reference(token) or not _reference(delivery) or handle is not None or not owned(
                    deliveries, delivery_ref=delivery, token_ref=token, source_actor_id=actor_id, step_id=sid):
                errors.append('transfer reference')
            if not any(isinstance(t, dict) and t.get('token_ref') == token and t.get('actor_id') == actor_id
                       and before(t.get('step_id'), sid) for t in tokens):
                errors.append('transfer token owner/order')
            if called or native is not None or errno is not None:
                errors.append('transfer carries a native result')
            if (published is False) != (status == 'unresolved') or (status != 'unresolved' and status not in ACTOR_TRANSFER_STATUSES):
                errors.append('transfer status')
        elif operation == 'consume':
            if not _reference(delivery) or not _reference(handle) or token is not None or handle in consumed or not owned(
                    handles, handle_ref=handle, delivery_ref=delivery, actor_id=actor_id, step_id=sid):
                errors.append('consume reference')
            if not any(isinstance(d, dict) and d.get('delivery_ref') == delivery
                       and d.get('recipient_actor_id') == actor_id and before(d.get('step_id'), sid)
                       for d in deliveries):
                errors.append('consume delivery recipient/order')
            consumed[handle] = event
        elif operation == 'release':
            prior = consumed.get(handle)
            order = prior is not None and prior.get('step_id') in ids and sid in ids and ids.index(prior['step_id']) < ids.index(sid)
            if not _reference(handle) or token is not None or delivery is not None or handle in released or not order \
                    or not owned(handles, handle_ref=handle, actor_id=actor_id, release_step_id=sid):
                errors.append('release reference/order')
            released.add(handle)
            if status == 'returned' and (prior is None or prior.get('status') != 'returned'
                                         or not _integer(prior.get('native_result'), -(1 << 63), (1 << 63) - 1)
                                         or prior['native_result'] == -1):
                errors.append('release lacks an observed consume handle')
        else:
            errors.append('unknown extension operation'); continue
        if operation != 'transfer':
            if status == 'returned':
                if published is not True or called is not True or not _integer(native, -(1 << 63), (1 << 63) - 1) \
                        or not _integer(errno, 0, (1 << 31) - 1) or event.get('unavailable_reason') is not None:
                    errors.append('native extension result lacks publication')
            elif status == 'unavailable':
                if published is not True or called is not False or native is not None or errno is not None \
                        or event.get('unavailable_reason') not in ACTOR_UNAVAILABLE_REASONS:
                    errors.append('unavailable extension action fabricates a call')
            elif status == 'unresolved':
                if published is not False or native is not None or errno is not None or event.get('unavailable_reason') is not None:
                    errors.append('unpublished extension result must stay unresolved')
            else:
                errors.append('invalid extension event status')
        sub = actor.get('subprocess')
        if isinstance(sub, dict):
            record = sub.get('disposition')
            entries = record.get('steps') if isinstance(record, dict) else None
            entries = [s for s in entries if isinstance(s, dict) and s.get('step_id') == sid] if isinstance(entries, list) else []
            lifecycle = event.get('lifecycle')
            questions = entries[0].get('questions') if len(entries) == 1 else None
            if len(entries) != 1 or not isinstance(lifecycle, dict) or not isinstance(questions, dict) or \
                    published != (entries[0].get('slot') == 'completed' and entries[0].get('attempt_support') == 'supported') or \
                    lifecycle.get('boundary') != questions.get('step_boundary_reached') or \
                    lifecycle.get('result') != questions.get('step_result_published'):
                errors.append('extension publication disagrees with disposition')
        elif published is True or called is True or event.get('lifecycle') is not None:
            errors.append('extension action evidence lacks a worker')
        if (published is True or called is True) and (actor.get('setup_status') not in ACTOR_SETUP_ESTABLISHED
                or not isinstance(phase.get('ordering'), dict) or phase['ordering'].get('proceed_observed') is not True):
            errors.append('extension publication lacks setup and phase acknowledgement')
    for transfer in transfers:
        if not isinstance(transfer, dict) or transfer.get('status') not in ACTOR_TRANSFER_STATUSES or not owned(
                deliveries, delivery_ref=transfer.get('delivery_ref'), token_ref=transfer.get('token_ref'),
                source_actor_id=transfer.get('source_actor_id'), recipient_actor_id=transfer.get('recipient_actor_id'),
                step_id=transfer.get('step_id')):
            errors.append('transfer record association')
        if not isinstance(transfer, dict):
            continue
        source = next((e for e in events if isinstance(e, dict) and e.get('operation') == 'transfer'
                       and e.get('delivery_ref') == transfer.get('delivery_ref')), None)
        if source is None or transfer.get('phase_id') != source.get('phase_id') \
                or transfer.get('lifecycle') != source.get('lifecycle'):
            errors.append('transfer source phase/lifecycle association')
        if transfer.get('status') == 'delivered' and (transfer.get('request_published') is not True
                or transfer.get('custody_status') != 'held' or transfer.get('copy_status') != 'copied'
                or transfer.get('equality') != 'equal' or transfer.get('recipient_acknowledged') is not True):
            errors.append('delivered transfer lacks custody, copy or recipient acknowledgement')
        if transfer.get('source_acknowledged') is True and not any(isinstance(e, dict) and e.get('operation') == 'transfer'
                and e.get('step_id') == transfer.get('step_id') and e.get('actor_id') == transfer.get('source_actor_id')
                and e.get('result_published') is True and e.get('status') == transfer.get('status') for e in events):
            errors.append('source acknowledgement lacks matching publication')

    for table, operation, reference in ((tokens, 'issue', 'token_ref'), (handles, 'consume', 'handle_ref'),
                                      (deliveries, 'transfer', 'delivery_ref')):
        for resource in table:
            if not isinstance(resource, dict):
                errors.append('resource is not an object'); continue
            matches = [e for e in events if isinstance(e, dict) and e.get('operation') == operation
                       and e.get(reference) == resource.get(reference)]
            if len(matches) != 1:
                errors.append('resource lacks unique producing event'); continue
            event = matches[0]
            if operation == 'transfer':
                if resource.get('recipient_actor_id') not in by_actor:
                    errors.append('delivery recipient does not exist')
                host = next((t for t in transfers if isinstance(t, dict)
                             and t.get('delivery_ref') == resource.get(reference)), None)
                if host is not None:
                    # Host observations survive a missing source publication;
                    # the resource table must still describe those observations.
                    if resource.get('status') != host.get('status') or resource.get('equality') != host.get('equality'):
                        errors.append('delivery projection contradicts host transfer')
                    length = resource.get('delivered_length')
                    token = next((t for t in tokens if isinstance(t, dict) and t.get('token_ref') == resource.get('token_ref')), {})
                    if host.get('status') == 'delivered':
                        if not _integer(length, 1, 16383) or (token.get('token_length') is not None and length != token.get('token_length')):
                            errors.append('delivered length contradicts custody')
                    elif length is not None:
                        errors.append('undelivered resource carries delivered length')
                    continue
                if resource.get('equality') is not None or resource.get('delivered_length') is not None \
                        or event.get('status') not in ('none', 'host_timeout', 'clock_fault', 'unresolved'):
                    errors.append('delivery claims host observation without transfer')
                if event.get('result_published') is True and resource.get('status') != (event.get('unavailable_reason') or 'unrequested'):
                    errors.append('unobserved delivery status contradicts source')
            if event.get('result_published') is not True:
                lifecycle = event.get('lifecycle')
                boundary = lifecycle.get('boundary') if isinstance(lifecycle, dict) else None
                boundary = boundary if isinstance(boundary, dict) else {}
                status = 'not_reached' if boundary.get('state') == 'supported' and boundary.get('answer') == 'not_reached' and event.get('call_boundary_observed') is False else 'unresolved'
                if resource.get('status') != status:
                    errors.append('unpublished resource status contradicts lifecycle')
            elif operation == 'issue':
                statuses = ('unavailable',) if event.get('status') == 'unavailable' else ('null',) if event.get('native_result') == 0 else ('issued', 'issued_uncustodied')
                if resource.get('status') not in statuses:
                    errors.append('token status contradicts issue')
            elif operation == 'consume':
                status = 'unavailable' if event.get('status') == 'unavailable' else 'consume_failed' if event.get('native_result') == -1 else 'produced'
                if resource.get('status') != status:
                    errors.append('handle status or value contradicts consume')
            if operation == 'consume' and resource.get('native_handle') != (event.get('native_result') if resource.get('status') == 'produced' else None):
                errors.append('handle status or value contradicts consume')
            if operation == 'issue' and (resource.get('family') != 'file'
                    or resource.get('token_length') != event.get('token_length')
                    or (resource.get('status') == 'issued' and not _integer(resource.get('token_length'), 1, 16383))):
                errors.append('token metadata contradicts issue')
            if operation == 'consume':
                release = next((e for e in events if isinstance(e, dict) and e.get('operation') == 'release'
                                and e.get('handle_ref') == resource.get(reference)), None)
                if resource.get('release_step_id') != (release.get('step_id') if release else None) \
                        or resource.get('release_attempted') is not bool(release and release.get('call_boundary_observed')):
                    errors.append('handle release projection contradicts event')
                equal = [h.get('handle_ref') for h in handles if isinstance(h, dict)
                         and h.get('handle_ref') != resource.get(reference) and h.get('actor_id') == resource.get('actor_id')
                         and resource.get('native_handle') is not None and h.get('native_handle') == resource.get('native_handle')]
                observed = resource.get('raw_equal_handles')
                if not isinstance(observed, list) or any(not isinstance(x, str) for x in observed) \
                        or len(observed) != len(set(observed)) or set(observed) != set(equal):
                    errors.append('handle equality projection contradicts native handles')
    return errors


def validate_extensions(runner):
    """Applicable ordinary relationships; degradation form has a separate owner."""
    if runner.get('reporting_failure') is not None:
        return []
    from actor_evidence import validate_actor_evidence
    errors = validate_actor_evidence(runner)
    if runner.get('execution_form') == 'actors':
        errors.extend(validate_actor_extensions(runner))
    return errors
