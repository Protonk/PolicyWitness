"""Run ownership, retained evidence, and the stable checkout execution lock.

Never unlink .checkout.lock: an open lock belongs to its inode, so replacing
that file would let later operations run concurrently with its current holder.
"""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path, PurePosixPath
import re
import time

RUN_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def read_object(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'expected a regular JSON file: {path}')
    value = json.loads(path.read_text(), object_pairs_hook=unique_object)
    if not isinstance(value, dict):
        raise ValueError(f'expected a JSON object: {path}')
    return value


def relative_path(value):
    if not isinstance(value, str) or not value:
        raise ValueError('expected a nonempty relative path')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or str(path) != value or value == '.':
        raise ValueError(f'invalid relative path: {value!r}')
    return path


def bounded_path(root, path):
    base = root / 'tests/out'
    path = Path(path)
    if not path.is_absolute():
        path = root / path
    if '..' in path.parts or (path != base and base not in path.parents):
        raise ValueError(f'output path must remain within {base}: {path}')
    if path.resolve() != path:
        raise ValueError(f'symlink redirects are not allowed in output paths: {path}')
    return path


def load_index(root):
    try:
        index = read_object(root / 'tests/RETAINED.json')
        if index.get('schema_version') != 1 or not isinstance(index.get('runs'), list):
            raise ValueError('expected schema_version 1 and a runs array')
        paths = []
        for entry in index['runs']:
            if not isinstance(entry, dict) or set(entry) != {'path', 'run_id', 'reason', 'source', 'app_inventory'}:
                raise ValueError('invalid retained entry fields')
            path = bounded_path(root, root / 'tests/out' / relative_path(entry['path']))
            if path in paths:
                raise ValueError(f'duplicate retained path: {path}')
            if not isinstance(entry['run_id'], str) or not RUN_ID.fullmatch(entry['run_id']):
                raise ValueError('invalid retained run_id')
            if not isinstance(entry['reason'], str) or not entry['reason'].strip():
                raise ValueError('retained reason is required')
            if entry['source'] is not None and (not isinstance(entry['source'], str)
                    or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', entry['source'])):
                raise ValueError('source must be a full commit hash or null')
            if entry['app_inventory'] is not None:
                bounded_path(root, path / relative_path(entry['app_inventory']))
            paths.append(path)
        return paths
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise ValueError(f'invalid retention index tests/RETAINED.json: {exc}') from exc


def overlaps(path, other):
    return path == other or path in other.parents or other in path.parents


def retained_overlap(path, retained):
    return next((other for other in retained if overlaps(path, other)), None)


def disposition(path):
    """Classify a real directory from ownership and terminal evidence, not location."""
    owner_path = path / 'owner.json'
    if not os.path.lexists(owner_path):
        return 'unmanaged'
    try:
        owner = read_object(owner_path)
        started = owner['started_at_unix_ms']
        if (owner.get('schema_version') != 1 or owner.get('out_dir') != str(path)
                or not isinstance(owner.get('run_id'), str) or not RUN_ID.fullmatch(owner['run_id'])
                or type(started) is not int or started < 0):
            return 'ambiguous'
        if not os.path.lexists(path / 'run.json'):
            return 'interrupted'
        run = read_object(path / 'run.json')
        finished = run['finished_at_unix_ms']
        completion = run['completion']
        if (run.get('schema_version') != 1 or run.get('terminal') is not True
                or run.get('run_id') != owner['run_id'] or run.get('started_at_unix_ms') != started
                or type(finished) is not int or finished < started
                or run.get('duration_ms') != finished - started or type(run.get('ok')) is not bool
                or run['configuration']['out_dir'] != str(path)
                or not isinstance(completion, dict)
                or set(completion) != {'selected', 'completed', 'skipped', 'unrun'}
                or any(type(v) is not int or v < 0 for v in completion.values())
                or completion['selected'] != sum(completion[k] for k in ('completed', 'skipped', 'unrun'))):
            return 'ambiguous'
        cases, selected = run['case_results'], run['plan']['cases']
        if (not isinstance(cases, list) or not isinstance(selected, list)
                or len(cases) != completion['selected'] or len(selected) != len(cases)
                or run['plan']['configuration'] != run['configuration']
                or sorted(c['id'] for c in cases) != sorted(c['id'] for c in selected)
                or len({c['id'] for c in cases}) != len(cases)
                or any(c['state'] not in ('completed', 'skipped', 'unrun') for c in cases)
                or any(completion[state] != sum(c['state'] == state for c in cases)
                       for state in ('completed', 'skipped', 'unrun'))):
            return 'ambiguous'
        return 'completed'
    except (OSError, ValueError, KeyError, TypeError):
        return 'ambiguous'


def replacement_allowed(root, out, retained):
    bounded_path(root, out)
    protected = retained_overlap(out, retained)
    if protected:
        raise ValueError(f'output overlaps retained path {protected}; choose a fresh output directory')
    if out.exists():
        if not out.is_dir():
            raise ValueError(f'output is not a directory: {out}')
        # A newly created empty directory has no evidence to replace.
        if not any(out.iterdir()):
            return
        state = disposition(out)
        if state != 'completed':
            remedy = ('inspect it or use --prune --apply --unfinished <name>'
                      if state in ('interrupted', 'ambiguous') else 'choose a fresh output directory')
            raise ValueError(f'refusing replacement of {state} output {out}; {remedy}')


@contextmanager
def checkout_lock(root, *, preview=False):
    path = root / 'tests/.checkout.lock'
    # A preview must leave even a checkout without a lock file unchanged.
    if preview and not os.path.lexists(path):
        yield False
        return
    flags = os.O_RDWR | os.O_NOFOLLOW | (0 if preview else os.O_CREAT)
    fd = os.open(path, flags, 0o600)
    acquired = False
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except BlockingIOError:
            if not preview:
                raise ValueError('checkout busy: another execution or mutating operation holds tests/.checkout.lock')
        if acquired and not preview:
            metadata = json.dumps({'pid': os.getpid(), 'started_at_unix_ms': time.time_ns() // 1_000_000}) + '\n'
            os.ftruncate(fd, 0)
            os.write(fd, metadata.encode())
        yield not acquired
    finally:
        if acquired:
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
