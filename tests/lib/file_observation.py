"""Same-descriptor file samples and small correspondence checks.

Callers own bounds, prerequisites, stability decisions and workload expectations.
The record constructor is only for explicitly constructed checker controls.
"""
import hashlib
import json
import os
import stat as stat_module

STAT_FIELDS = ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns')


def _get(value, *path):
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _spell(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _exact_int(value, expected):
    return type(value) is int and value == expected


def fresh(attempt):
    return attempt.get('fresh_read') if isinstance(attempt.get('fresh_read'), dict) else {}


def observe_target(target, bound, opener=os.open):
    """One sample: identity and content read from one descriptor this process opened, then closed.

    `opener` opens the path and returns the descriptor. The observer controls
    pass one that changes what the path names as the open returns, so that
    everything read afterwards is read after the change.
    """
    record = {'target': target, 'resolved': None, 'regular_file': False, 'readable': False, 'error': None}
    try:
        record['resolved'] = os.path.realpath(target, strict=True)
        descriptor = opener(target, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
    except OSError as error:
        record['error'] = f'{type(error).__name__}: {error}'
        return record
    try:
        status = os.fstat(descriptor)
        record.update(regular_file=stat_module.S_ISREG(status.st_mode),
                      stat={field: getattr(status, field) for field in STAT_FIELDS})
        if record['regular_file']:
            data = b''
            while chunk := os.read(descriptor, 1 << 20):
                data += chunk
            prefix = data[:bound]
            # Digests and lengths support the equality observations; the bytes are not retained.
            record.update(readable=True, sha256=hashlib.sha256(data).hexdigest(), length=len(data),
                          prefix_sha256=hashlib.sha256(prefix).hexdigest(), prefix_length=len(prefix))
    except OSError as error:
        record['error'] = f'{type(error).__name__}: {error}'
    finally:
        os.close(descriptor)
    return record


def target_changes(before, after):
    """For each path read before the run, the ways its sample after the run differs."""
    after = after or {}
    changes = {}
    for target, earlier in (before or {}).items():
        if not (earlier.get('regular_file') and earlier.get('readable')):
            continue
        later = after.get(target)
        if later is None or not later.get('readable'):
            changes[target] = ['was not read after the run']
            continue
        differing = [field for field in STAT_FIELDS if _get(earlier, 'stat', field) != _get(later, 'stat', field)]
        if earlier.get('resolved') != later.get('resolved'):
            differing.insert(0, 'resolved path')
        for name, kind in (('prefix_sha256', str), ('prefix_length', int), ('sha256', str), ('length', int)):
            if type(earlier.get(name)) is not kind or earlier.get(name) != later.get(name):
                differing.insert(0, name)
        if differing:
            changes[target] = ['differs in ' + ', '.join(differing)]
    return changes


def fresh_syscalls(attempt, bound):
    read, problems = fresh(attempt), []
    # A successful open returns any nonnegative descriptor, including zero.
    if type(read.get('open_rc')) is not int or read['open_rc'] < 0:
        problems.append(f'`open_rc` is {_spell(read.get("open_rc"))}')
    for name in ('stat_rc', 'close_rc'):
        if not _exact_int(read.get(name), 0):
            problems.append(f'`{name}` is {_spell(read.get(name))}')
    if type(read.get('read_rc')) is not int or not 0 <= read['read_rc'] <= bound:
        problems.append(f'`read_rc` is {_spell(read.get("read_rc"))}')
    return problems

def fresh_identity(attempt, expected, target):
    found = {key: _get(fresh(attempt), 'identity', key) for key in expected}
    return [] if all(type(found[key]) is int and found[key] == expected[key] for key in found) else \
        [f'the descriptor identity is {_spell(found)}; this checker observed {_spell(expected)} for {target}']

def fresh_content(attempt, observed, target):
    read, problems = fresh(attempt), []
    if not _exact_int(read.get('read_rc'), observed.get('prefix_length')):
        problems.append(f'`read_rc` is {_spell(read.get("read_rc"))}; this checker read a bounded prefix of '
                        f'{_spell(observed.get("prefix_length"))} bytes from {target}')
    try:
        digest = hashlib.sha256(bytes.fromhex(read.get('content_hex'))).hexdigest()
    except (TypeError, ValueError):
        digest = None
    if digest is None or digest != observed.get('prefix_sha256'):
        problems.append(f'the bytes read have SHA-256 {_spell(digest)}; the bounded prefix this checker read '
                        f'from {target} has {_spell(observed.get("prefix_sha256"))}')
    return problems


def fresh_record(data, identity, *, bound, descriptor=5):
    """Construct successful syscall facts for explicitly supplied bytes/identity."""
    prefix = data[:bound]
    return dict(open_rc=descriptor, stat_rc=0, read_rc=len(prefix), close_rc=0,
                identity=dict(identity), content_hex=prefix.hex())
