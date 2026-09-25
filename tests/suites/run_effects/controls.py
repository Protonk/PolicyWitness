"""Feed the effect expectations fabricated observations.

Each expectation must accept the observation the live cases rely on and reject
the wrong ones a lying or broken worker would produce. No PolicyWitness code
or app is involved.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import effects  # noqa: E402

ABSENT = {'path': '/fabricated', 'exists': False}


def present(**overrides):
    snap = {'path': '/fabricated', 'exists': True, 'bytes': b'seed', 'size': 4, 'mode': 0o640,
            'dev': 1, 'ino': 2, 'nlink': 1, 'mtime_ns': 10, 'ctime_ns': 10}
    snap.update(overrides)
    return snap


def main():
    out = Path(sys.argv[1]).resolve()
    seed = present()
    one_x = present(bytes=b'x', size=1)
    created = {'bytes': b'', 'size': 0, 'mode': 0o600}
    marker = present(bytes=effects.HELPER_LINE, size=len(effects.HELPER_LINE), mode=0o600)
    inventory = {'registry_sha256': None, 'user_launch_agents': ['a.plist'], 'reported_registry': {'runners': []}}
    controls = [
        ('truncated accepts one x byte in place', effects.expect_truncated_to_one_byte, (seed, one_x), False),
        ('truncated rejects an untouched seed', effects.expect_truncated_to_one_byte, (seed, present()), True),
        ('truncated rejects two bytes', effects.expect_truncated_to_one_byte, (seed, present(bytes=b'xx', size=2)), True),
        ('truncated rejects a replaced inode', effects.expect_truncated_to_one_byte, (seed, present(bytes=b'x', size=1, ino=3)), True),
        ('truncated rejects changed mode', effects.expect_truncated_to_one_byte, (seed, present(bytes=b'x', size=1, mode=0o600)), True),
        ('truncated rejects an absent result', effects.expect_truncated_to_one_byte, (seed, ABSENT), True),
        ('created accepts empty 0600', effects.expect_created_empty, (ABSENT, present(**created)), False),
        ('created rejects mode 0644', effects.expect_created_empty, (ABSENT, present(bytes=b'', size=0, mode=0o644)), True),
        ('created rejects written bytes', effects.expect_created_empty, (ABSENT, present(bytes=b'x', size=1, mode=0o600)), True),
        ('created rejects a seeded start', effects.expect_created_empty, (seed, present(**created)), True),
        ('created rejects an absent result', effects.expect_created_empty, (ABSENT, ABSENT), True),
        ('absent accepts absent', effects.expect_absent, (ABSENT,), False),
        ('absent rejects present', effects.expect_absent, (seed,), True),
        ('unchanged accepts identical', effects.expect_unchanged, (seed, present()), False),
        ('unchanged rejects changed bytes', effects.expect_unchanged, (seed, present(bytes=b'seeD')), True),
        ('unchanged rejects a new inode', effects.expect_unchanged, (seed, present(ino=9)), True),
        ('unchanged rejects a changed mtime', effects.expect_unchanged, (seed, present(mtime_ns=11)), True),
        ('unchanged rejects a changed mode', effects.expect_unchanged, (seed, present(mode=0o600)), True),
        ('unchanged rejects an absent result', effects.expect_unchanged, (seed, ABSENT), True),
        ('marker accepts the helper line at 0600', effects.expect_helper_marker, (marker,), False),
        ('marker rejects other bytes', effects.expect_helper_marker, (present(bytes=b'nope\n', size=5, mode=0o600),), True),
        ('marker rejects mode 0644', effects.expect_helper_marker, (present(bytes=effects.HELPER_LINE, size=len(effects.HELPER_LINE), mode=0o644),), True),
        ('marker rejects absent', effects.expect_helper_marker, (ABSENT,), True),
        ('inventory accepts equal', effects.expect_inventory_unchanged, (inventory, dict(inventory)), False),
        ('inventory rejects a new plist', effects.expect_inventory_unchanged,
         (inventory, dict(inventory, user_launch_agents=['a.plist', 'pw.plist'])), True),
        ('inventory rejects a registry that appeared', effects.expect_inventory_unchanged,
         (inventory, dict(inventory, registry_sha256='abc')), True),
        ('inventory rejects a reported runner', effects.expect_inventory_unchanged,
         (inventory, dict(inventory, reported_registry={'runners': [{'id': 'x'}]})), True),
    ]
    results = []
    for name, expectation, args, rejects in controls:
        try:
            expectation(*args)
            raised, message = False, None
        except AssertionError as exc:
            raised, message = True, str(exc)
        assert raised == rejects, f'{name}: expected rejection={rejects}, got {message!r}'
        results.append({'control': name, 'rejects': rejects, 'message': message})
        print(f'{name}: {"rejected" if raised else "accepted"} as required', flush=True)
    (out / 'controls.json').write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
    main()
