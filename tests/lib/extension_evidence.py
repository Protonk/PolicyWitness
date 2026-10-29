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


DELIVERY_STATUSES = ('not_observed', 'delivered', 'token_unavailable', 'channel_rejected',
                     'native_api_unavailable', 'local_setup_failed')
DELIVERY_FAILURE_STATUSES = ('channel_rejected', 'local_setup_failed')
LOCAL_STAGES = ('core_limit', 'descriptor_metadata', 'mapping', 'descriptor_close')
CHANNEL_STAGES = ('channel_size', 'channel_header', 'channel_token')
CLEANUP_STAGES = ('descriptor_close', 'unmap')


def delivery_failure_problem(status, failure):
    """Shared structural rules for a worker delivery failure account."""
    if not isinstance(failure, dict):
        return 'delivery failure lacks its account'
    stage = failure.get('stage')
    local = stage in LOCAL_STAGES
    if not local and stage not in CHANNEL_STAGES:
        return 'unknown delivery failure stage'
    if (status == 'local_setup_failed') != local:
        return 'delivery failure stage disagrees with status'
    rc, err = failure.get('native_rc'), failure.get('errno')
    if local:
        if not _integer(rc, -(1 << 31), (1 << 31) - 1) or rc == 0 or not _integer(err, 0, (1 << 31) - 1):
            return 'local setup failure lacks its native result'
    elif stage == 'channel_size':
        if not _integer(rc, 0, 0) or err is not None:
            return 'undersized channel misreports its inspection result'
    elif rc is not None or err is not None:
        return 'channel rejection invents a native result'
    cleanup, cleanup_errno = failure.get('cleanup_stage'), failure.get('cleanup_errno')
    if cleanup is not None:
        if cleanup not in CLEANUP_STAGES or not _integer(cleanup_errno, 0, (1 << 31) - 1):
            return 'delivery cleanup failure lacks its errno'
        if cleanup == 'descriptor_close' and stage == 'descriptor_close':
            return 'descriptor closed twice'
    elif cleanup_errno is not None:
        return 'delivery cleanup errno without a stage'
    return None


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


def validate_extensions(runner):
    declarations = runner.get('extensions', [])
    events = runner.get('extension_events', [])
    if not isinstance(declarations, list) or len(declarations) > 1 or not isinstance(events, list) or len(events) > 2:
        return ['extension record capacity or type']
    if events and len(declarations) != 1:
        return ['extension events require one declaration']
    errors = []
    declaration = declarations[0] if declarations and isinstance(declarations[0], dict) else {}
    if declarations:
        if not _reference(declaration.get('token_ref')) or declaration.get('extension_class') not in (
                'com.apple.app-sandbox.read', 'com.apple.app-sandbox.read-write'):
            errors.append('invalid extension declaration reference/class')
        for key in ('submitted_target', 'resolved_target'):
            value = declaration.get(key)
            if (key == 'submitted_target' or value is not None) and (not isinstance(value, str)
                    or not 0 < len(value.encode('utf-8')) <= 1023 or '\0' in value):
                errors.append('invalid extension ' + key)
        prepared = declaration.get('preparation_status')
        if prepared not in ('not_started', 'resolution_failed', 'metadata_failed', 'prepared'):
            errors.append('invalid extension preparation status')
        if prepared == 'prepared' and (not _identity(declaration.get('identity')) or not declaration.get('resolved_target')
                                      or declaration.get('preparation_errno') is not None):
            errors.append('extension preparation lacks resolution/identity')
        if prepared in ('resolution_failed', 'metadata_failed') and not _integer(declaration.get('preparation_errno'), 0, (1 << 31) - 1):
            errors.append('extension preparation failure lacks errno')
        if prepared != 'prepared' and declaration.get('identity') is not None:
            errors.append('extension identity lacks successful preparation')
        if declaration.get('issuance_status') not in ('not_started', 'issuer_unavailable', 'channel_setup_failed',
                'spawn_failed', 'issuer_timeout', 'issuer_wait_error', 'issuer_result_missing', 'issuer_abnormal_exit', 'native_api_unavailable',
                'native_refusal', 'token_oversized', 'invalid_transport', 'issued'):
            errors.append('invalid extension issuance status')
        issuer = declaration.get('issuer')
        issuer = issuer if isinstance(issuer, dict) else {}
        if declaration.get('issuance_status') == 'issuer_result_missing' and (
                issuer.get('result_published') is not False or any(issuer.get(k) is not None
                for k in ('native_nonnull', 'errno', 'token_length', 'uid', 'euid', 'gid', 'egid'))):
            errors.append('missing issuer result carries publication or payload')
        for key in ('call_boundary_observed', 'result_published'):
            if issuer and type(issuer.get(key)) is not bool:
                errors.append('invalid issuer ' + key)
        if issuer.get('native_nonnull') is not None and (type(issuer['native_nonnull']) is not bool
                or issuer.get('result_published') is not True or issuer.get('call_boundary_observed') is not True
                or not _integer(issuer.get('errno'), 0, (1 << 31) - 1)):
            errors.append('issuer native result lacks call/publication')
        if issuer.get('result_published') is not True and any(issuer.get(k) is not None
                for k in ('native_nonnull', 'errno', 'token_length', 'uid', 'euid', 'gid', 'egid')):
            errors.append('unpublished issuer result carries payload')
        issued = declaration.get('issuance_status') == 'issued'
        if declaration.get('issuance_status') == 'issuer_abnormal_exit' and (
                issuer.get('result_published') is not True or issuer.get('call_boundary_observed') is not True
                or issuer.get('native_nonnull') is not True or issuer.get('reaped') is not True
                or not _integer(issuer.get('token_length'), 1, 16383)
                or not (_integer(issuer.get('term_signal'), 1, 31) or _integer(issuer.get('exit_code'), 1, 255))):
            errors.append('abnormal issuer exit lacks publication and reap')
        if issued and (prepared != 'prepared' or issuer.get('native_nonnull') is not True
                or issuer.get('result_published') is not True or issuer.get('call_boundary_observed') is not True
                or issuer.get('reaped') is not True or issuer.get('exit_code') != 0 or issuer.get('term_signal') is not None
                or not _integer(issuer.get('pid'), 1, (1 << 31) - 1)
                or not _integer(issuer.get('token_length'), 1, 16383)):
            errors.append('issued extension lacks bounded native result and clean issuer reap')
        if type(declaration.get('host_buffer_erased')) is not bool:
            errors.append('extension erasure observation must be boolean')
        delivery = declaration.get('delivery_status')
        if delivery not in DELIVERY_STATUSES:
            errors.append('invalid extension delivery status')
        failure = declaration.get('delivery_failure')
        cleanup = declaration.get('delivery_cleanup_failure')
        if cleanup is not None and (delivery != 'native_api_unavailable' or not isinstance(cleanup, dict)
                or cleanup.get('stage') != 'descriptor_close'
                or not _integer(cleanup.get('errno'), 0, (1 << 31) - 1)):
            errors.append('invalid independent delivery cleanup failure')
        if delivery in DELIVERY_FAILURE_STATUSES:
            problem = delivery_failure_problem(delivery, failure)
            if problem:
                errors.append(problem)
            elif delivery == 'channel_rejected' and not issued:
                errors.append('channel rejection without an issued token')
        elif failure is not None:
            errors.append('delivery failure account without a failure status')
        if delivery == 'delivered':
            if not issued or not _integer(declaration.get('delivered_bytes'), 1, 16383) \
                    or declaration['delivered_bytes'] != issuer.get('token_length'):
                errors.append('extension delivery lacks bounded issuance')
        elif declaration.get('delivered_bytes') is not None:
            errors.append('undelivered extension carries delivered byte count')
    phases = runner.get('phases')
    phases = [p for p in phases if isinstance(p, dict)] if isinstance(phases, list) else []
    ids = [i for p in phases for i in p.get('action_ids', [])] if all(isinstance(p.get('action_ids'), list) for p in phases) else []
    consume, released = None, False
    for event in events:
        if not isinstance(event, dict):
            errors.append('extension event is not an object'); continue
        sid = event.get('step_id')
        matches = [p for p in phases if p.get('phase_id') == event.get('phase_id')
                   and isinstance(p.get('action_ids'), list) and sid in p['action_ids']]
        if len(matches) != 1:
            errors.append('extension event phase association')
        if not _reference(sid) or not _reference(event.get('handle_ref')) or event.get('handle_ref') == declaration.get('token_ref'):
            errors.append('invalid extension action/handle reference')
        operation, status = event.get('operation'), event.get('status')
        native, errno = event.get('native_result'), event.get('errno')
        called, published = event.get('call_boundary_observed'), event.get('result_published')
        if type(called) is not bool or type(published) is not bool:
            errors.append('extension boundary/publication must be boolean')
        if operation == 'consume':
            if consume is not None or released or event.get('token_ref') != declaration.get('token_ref'):
                errors.append('extension consume reference/order')
            consume = event
        elif operation == 'release':
            if released or consume is None or event.get('token_ref') is not None or event.get('handle_ref') != consume.get('handle_ref') \
                    or sid not in ids or consume.get('step_id') not in ids or ids.index(consume['step_id']) >= ids.index(sid):
                errors.append('extension release reference/order')
            if status == 'returned' and (consume is None or consume.get('status') != 'returned'
                    or not _integer(consume.get('native_result'), -(1 << 63), (1 << 63) - 1) or consume['native_result'] == -1):
                errors.append('release lacks an observed consume handle')
            released = True
        else:
            errors.append('unknown extension operation')
        if status == 'returned':
            bits = 32 if operation == 'release' else 64
            if published is not True or called is not True or not _integer(native, -(1 << (bits - 1)), (1 << (bits - 1)) - 1) \
                    or not _integer(errno, 0, (1 << 31) - 1) or event.get('unavailable_reason') is not None:
                errors.append('native extension result lacks publication')
            if operation == 'consume' and declaration.get('delivery_status') != 'delivered':
                errors.append('consumption lacks delivery')
        elif status == 'unavailable':
            reason = event.get('unavailable_reason')
            if published is not True or called is not False or native is not None or errno is not None \
                    or reason not in ('token_unavailable', 'handle_unavailable', 'native_api_unavailable', 'repeated_action'):
                errors.append('unavailable extension action fabricates a call')
            if (reason == 'handle_unavailable' and operation != 'release') or (reason == 'token_unavailable' and operation != 'consume'):
                errors.append('unavailable extension reason disagrees with operation')
        elif status == 'unresolved':
            if published is not False or native is not None or errno is not None or event.get('unavailable_reason') is not None:
                errors.append('unpublished extension result must stay unresolved')
        else:
            errors.append('invalid extension event status')
        sub = runner.get('runner_subprocess')
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
        if (published is True or called is True) and (runner.get('sandboxed_after_apply') is not True or len(matches) != 1
                or not isinstance(matches[0].get('ordering'), dict) or matches[0]['ordering'].get('proceed_observed') is not True):
            errors.append('extension publication lacks application and phase acknowledgement')
    return errors
