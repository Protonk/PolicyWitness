"""Managed run ownership, shared receipt IO, and the stable checkout execution lock.

Never unlink .checkout.lock: an open lock belongs to its inode, so replacing
that file would let later operations run concurrently with its current holder.
"""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
import checkout_lock as ownership  # noqa: E402

RUN_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}')
RELEASE_TAG = re.compile(r'v\d+\.\d+\.\d+')


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


def atomic_json(path, value):
    """Install complete JSON on the same filesystem; never follow an output link."""
    if path.is_symlink() or path.parent.resolve() != path.parent:
        raise ValueError(f'symlink redirects are not allowed: {path}')
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'w') as stream:
            if path.exists():
                os.fchmod(stream.fileno(), path.stat().st_mode & 0o7777)
            stream.write(json.dumps(value, indent=2) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


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
        owner = valid_owner(path)
        started = owner['started_at_unix_ms']
        if not os.path.lexists(path / 'run.json'):
            return 'interrupted'
        run = read_object(path / 'run.json')
        finished = run['finished_at_unix_ms']
        completion = run['completion']
        if (type(run.get('schema_version')) is not int or run['schema_version'] != 1 or run.get('terminal') is not True
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
    from pytest_resources import guard
    guard(root, purpose='disposal', target=out)
    bounded_path(root, out)
    protected = retained_overlap(out, retained)
    if protected:
        raise ValueError(f'output overlaps retained path {protected}; choose a fresh output directory')
    base = root / 'tests/out'
    if out in (base, base / 'runs', base / 'release-acceptance') or any(
            overlaps(out, base / name) for name in ('.retention', '.release-rotation', 'pytest-owners')):
        raise ValueError('output overlaps a managed container or ownership/quarantine area')
    if out.exists():
        if not out.is_dir():
            raise ValueError(f'output is not a directory: {out}')
        # A newly created empty directory has no evidence to replace.
        if not any(out.iterdir()):
            return
        state = disposition(out)
        if state != 'completed':
            remedy = ('inspect it or use --prune --apply'
                      if state in ('interrupted', 'ambiguous') else 'choose a fresh output directory')
            raise ValueError(f'refusing replacement of {state} output {out}; {remedy}')


@contextmanager
def checkout_lock(root, *, preview=False, purpose='execution'):
    """Own tests/.checkout.lock for the block; a preview only observes whether it is held.

    Acquisition, nested admission under an inherited claim and the busy
    refusal belong to tests/lib/checkout_lock.py; this yields that owner's
    scope, so a caller that launches protected children passes the held
    descriptor through it. Nothing unlocks explicitly: closing the last
    descriptor releases the lock. A preview yields whether the lock is busy
    and holds it for the block when it was free, without an owner record.
    """
    if preview:
        with ownership.preview(root) as busy:
            yield busy
        return
    with ownership.owned(root, purpose=purpose) as scope:
        yield scope


def valid_owner(path):
    owner = read_object(path / 'owner.json')
    if (type(owner.get('schema_version')) is not int or owner['schema_version'] != 1 or owner.get('out_dir') != str(path)
            or not isinstance(owner.get('run_id'), str) or not RUN_ID.fullmatch(owner['run_id'])
            or type(owner.get('started_at_unix_ms')) is not int or owner['started_at_unix_ms'] < 0):
        raise ValueError(f'no valid managed run ownership: {path}')
    return owner


@contextmanager
def acceptance_output(root, out, protection):
    """Own acceptance through extraction, nested tests and final receipts.

    Creation takes the checkout lock. A separate lifetime lock protects the
    outer operation while allowing its child dispatcher to take that same
    checkout lock. Release cleanup probes the lifetime lock without blocking.
    """
    with checkout_lock(root):
        bounded_path(root, out)
        replacement_allowed(root, out, protection())
        out.mkdir(parents=True)  # Acceptance always uses a fresh directory.
        fd = os.open(out / 'acceptance.lock', os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            owner = dict(schema_version=1, kind='release_acceptance', run_id='accept-' + uuid.uuid4().hex,
                         out_dir=str(out), started_at_unix_ms=time.time_ns() // 1_000_000)
            atomic_json(out / 'owner.json', owner)
        except BaseException:
            os.close(fd)
            raise
    try:
        yield owner
    finally:
        try:
            owner.update(terminal=True, finished_at_unix_ms=time.time_ns() // 1_000_000)
            atomic_json(out / 'owner.json', owner)
        finally:
            os.close(fd)


def acceptance_busy(path):
    lock = path / 'acceptance.lock'
    if not os.path.lexists(lock):
        raise ValueError('acceptance ownership has no lifetime lock')
    fd = os.open(lock, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    finally:
        os.close(fd)


def describe(path):
    """Ownership and recorded times, independent of names, mtime and size."""
    acceptance = path.parent.name == 'release-acceptance'
    if acceptance and acceptance_busy(path):
        raise ValueError('active acceptance')
    owner = valid_owner(path)
    started, finished = owner['started_at_unix_ms'], None
    if acceptance:
        if owner.get('kind') != 'release_acceptance':
            raise ValueError('unrecognized acceptance owner')
        state = 'interrupted'
        if owner.get('terminal') is True:
            finished = owner.get('finished_at_unix_ms')
            if type(finished) is not int or finished < started:
                raise ValueError('invalid acceptance completion time')
            state = 'completed'
    else:
        state = disposition(path)
        if state == 'completed':
            finished = read_object(path / 'run.json')['finished_at_unix_ms']
    return dict(run_id=owner['run_id'], started_at_unix_ms=started,
                finished_at_unix_ms=finished, disposition=state)
