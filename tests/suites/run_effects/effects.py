"""What an attempt did to the filesystem, stated as pure expectations.

Snapshots are taken by the checkers outside PolicyWitness, before and after a
run, and compared here. The functions take plain dictionaries so the direct
controls can feed them fabricated observations and require rejection.
"""
import hashlib
import json
import stat
from pathlib import Path

IDENTITY_FIELDS = ('size', 'mode', 'dev', 'ino', 'nlink', 'mtime_ns', 'ctime_ns')
HELPER_LINE = b'exec_fixture: wrote by helper\n'


def snapshot(path):
    path = Path(path)
    try:
        info = path.lstat()
    except FileNotFoundError:
        return {'path': str(path), 'exists': False}
    assert stat.S_ISREG(info.st_mode), f'not a regular file: {path}'
    return {
        'path': str(path), 'exists': True, 'bytes': path.read_bytes(),
        'size': info.st_size, 'mode': stat.S_IMODE(info.st_mode),
        'dev': info.st_dev, 'ino': info.st_ino, 'nlink': info.st_nlink,
        'mtime_ns': info.st_mtime_ns, 'ctime_ns': info.st_ctime_ns,
    }


def record(snap, out, name):
    """Retain a snapshot: raw bytes beside a JSON description with a digest."""
    described = {key: value for key, value in snap.items() if key != 'bytes'}
    if snap['exists']:
        (out / f'{name}.bytes').write_bytes(snap['bytes'])
        described['sha256'] = hashlib.sha256(snap['bytes']).hexdigest()
        described['mode'] = f'{snap["mode"]:04o}'
    (out / f'{name}.json').write_text(json.dumps(described, indent=2) + '\n')


def expect_truncated_to_one_byte(before, after):
    assert before['exists'] and after['exists'], 'open_write target must exist before and after'
    assert after['bytes'] == b'x', f'open_write must leave exactly one x byte, got {after["bytes"][:16]!r}'
    assert after['size'] == 1, f'open_write must leave size 1, got {after["size"]}'
    assert (after['dev'], after['ino']) == (before['dev'], before['ino']), \
        'open_write must truncate in place, not replace the file'
    assert after['mode'] == before['mode'], 'open_write must not change permission bits'


def expect_created_empty(before, after):
    assert not before['exists'], 'create control must start from an absent target'
    assert after['exists'], 'create must produce the target'
    assert after['size'] == 0 and after['bytes'] == b'', 'create must not write bytes'
    assert after['mode'] == 0o600, f'create must produce mode 0600, got {after["mode"]:04o}'
    assert after['nlink'] == 1, f'created file must have one link, got {after["nlink"]}'


def expect_absent(after):
    assert not after['exists'], f'target must be absent: {after["path"]}'


def expect_unchanged(before, after):
    assert before['exists'] and after['exists'], 'target must exist before and after'
    assert after['bytes'] == before['bytes'], 'bytes changed'
    for field in IDENTITY_FIELDS:
        assert after[field] == before[field], f'{field} changed: {before[field]!r} -> {after[field]!r}'


def expect_helper_marker(after):
    assert after['exists'], 'helper did not create the marker'
    assert after['bytes'] == HELPER_LINE, f'marker bytes are not the helper line: {after["bytes"][:40]!r}'
    assert after['mode'] == 0o600, f'helper creates with mode 0600, got {after["mode"]:04o}'


def expect_inventory_unchanged(before, after):
    changed = sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))
    assert not changed, 'persistent registration changed: ' + ', '.join(changed)


def describe_run(run):
    """One line of PW's own report for a failure message; never an oracle."""
    try:
        runner = run.load_json()['data']['runner_result']
    except Exception as exc:  # noqa: BLE001 - diagnostics only
        return f'PW envelope unreadable ({exc})'
    return f'PW reported normalized_outcome={runner.get("normalized_outcome")!r} error={runner.get("error")!r}'
