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
        if type(index.get('schema_version')) is not int or index['schema_version'] != 1 or not isinstance(index.get('runs'), list):
            raise ValueError('expected schema_version 1 and a runs array')
        paths = []
        for entry in index['runs']:
            if not isinstance(entry, dict) or set(entry) != {'path', 'run_id', 'reason', 'source', 'app_inventory'}:
                raise ValueError('invalid retained entry fields')
            path = bounded_path(root, root / 'tests/out' / relative_path(entry['path']))
            if path.exists() and not path.is_dir():
                raise ValueError(f'retained path is not a directory: {path}')
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


def valid_owner(path):
    owner = read_object(path / 'owner.json')
    if (type(owner.get('schema_version')) is not int or owner['schema_version'] != 1 or owner.get('out_dir') != str(path)
            or not isinstance(owner.get('run_id'), str) or not RUN_ID.fullmatch(owner['run_id'])
            or type(owner.get('started_at_unix_ms')) is not int or owner['started_at_unix_ms'] < 0):
        raise ValueError(f'no valid managed run ownership: {path}')
    return owner


def prune_rows(root, retained, *, busy=False):
    base = bounded_path(root, root / 'tests/out')
    runs = bounded_path(root, base / 'runs')
    rows = []
    if runs.exists():
        if not runs.is_dir():
            raise ValueError(f'managed runs root is not a directory: {runs}')
        for path in sorted(runs.iterdir()):
            # Files are outside the pruning interface. Links are reported but
            # never traversed or removed, even when they point to a directory.
            if path.is_symlink():
                rows.append(dict(path=str(path.relative_to(base)), disposition='keep: unmanaged', reason='symlink redirect'))
                continue
            if not path.is_dir():
                continue
            protected = retained_overlap(path, retained)
            state = disposition(path)
            decision = ('keep: retained' if protected else 'delete' if state == 'completed'
                        else 'keep: active or interrupted' if busy and state == 'interrupted'
                        else 'keep: ' + state)
            rows.append(dict(path=str(path.relative_to(base)), disposition=decision))
    if base.exists():
        for path in sorted(base.iterdir()):
            if path == runs or not path.is_dir():
                continue
            rows.append(dict(path=str(path.relative_to(base)), disposition='keep: unmanaged',
                             reason='outside tests/out/runs', retained=bool(retained_overlap(path, retained))))
    return rows


def unfinished_row(root, name, retained):
    if not isinstance(name, str) or not RUN_ID.fullmatch(name) or name in ('.', '..'):
        raise ValueError('--unfinished requires one direct run directory name')
    path = bounded_path(root, root / 'tests/out/runs' / name)
    if retained_overlap(path, retained):
        raise ValueError(f'cannot remove retained output: {path}')
    if not path.is_dir():
        raise ValueError(f'no managed run directory: {path}')
    valid_owner(path)
    state = disposition(path)
    if state not in ('interrupted', 'ambiguous'):
        raise ValueError(f'--unfinished requires interrupted or ambiguous managed output; got {state}: {path}')
    return dict(path='runs/' + name, disposition='delete', previous_disposition='keep: ' + state)


def prune(root, *, apply=False, unfinished=None):
    """Preview a read-only snapshot; apply re-evaluates under the checkout lock."""
    import shutil
    retained = load_index(root)
    if unfinished is not None:
        unfinished_row(root, unfinished, retained)
    else:
        prune_rows(root, retained)
    if not apply:
        with checkout_lock(root, preview=True) as busy:
            pass
        return {'schema_version': 1, 'apply': False, 'checkout_busy': busy,
                'runs': prune_rows(root, retained, busy=busy), 'removed': [], 'failures': []}
    with checkout_lock(root):
        retained = load_index(root)
        rows = ([unfinished_row(root, unfinished, retained)] if unfinished is not None
                else prune_rows(root, retained))
        result = {'schema_version': 1, 'apply': True, 'checkout_busy': False,
                  'runs': rows, 'removed': [], 'failures': []}
        for row in rows:
            if row['disposition'] != 'delete':
                continue
            path = root / 'tests/out' / row['path']
            try:
                # Recheck directly before removing, including index edits.
                retained = load_index(root)
                if unfinished is not None:
                    unfinished_row(root, unfinished, retained)
                else:
                    replacement_allowed(root, path, retained)
                    if disposition(path) != 'completed':
                        raise ValueError('run no longer has valid completion evidence')
                shutil.rmtree(path)
                result['removed'].append(row['path'])
            except (OSError, ValueError) as exc:
                result['failures'].append({'path': row['path'], 'error': str(exc)})
        return result
