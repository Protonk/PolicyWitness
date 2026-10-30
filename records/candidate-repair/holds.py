"""Read-only enumeration of ownership records in this review's runs.

Usage: python3 -I -B records/candidate-repair/holds.py OUTPUT.json RUN_NAME...
Reads with the worktree's own pytest_resources.inspect; never recovers, signals
or removes anything. Historical PID fields are reported, not probed.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import pytest_resources
from pytest_support import read


def fixture_roots(run):
    # Nested fixture checkouts keep their registry at <repo>/tests/out/pytest-owners.
    return sorted({p.parents[2] for p in run.rglob('tests/out/pytest-owners') if p.is_dir()})


def describe(root, actual):
    rows = []
    for row in pytest_resources.inspect(root):
        entry = dict(scope='worktree registry' if actual else 'nested fixture', root=str(root), **row)
        try:
            record = read(row['path'])
            settlement = record.get('settlement') or {}
            entry.update(state=record.get('state'), operation_id=record.get('operation_id'),
                         argv=record.get('argv'), historical_owner_pid=record.get('owner_pid'),
                         historical_command_pid=record.get('command_pid'),
                         settlement_never_launched=settlement.get('never_launched'),
                         launch_error=settlement.get('launch_error'),
                         socket_dir=record.get('socket_dir'),
                         socket_dir_present=Path(record['socket_dir']).exists())
        except (OSError, ValueError, KeyError, TypeError) as exc:
            entry['read_error'] = str(exc)
        if not actual:
            entry['read_only_inspection'] = (f"cd {root} && /opt/homebrew/opt/python@3.14/bin/python3.14 -I -B -c "
                                             f"'import sys;sys.path.insert(0,\"{ROOT}/tests/lib\");import json,pytest_resources;"
                                             f"print(json.dumps(pytest_resources.inspect(\"{root}\"),indent=1))'")
        rows.append(entry)
    return rows


def main(output, names):
    result = dict(worktree=str(ROOT), actual=describe(ROOT, True), runs={})
    for name in names:
        run = ROOT / 'tests/out/runs' / name
        result['runs'][name] = dict(run_id=read(run / 'owner.json')['run_id'],
                                    nested=[r for root in fixture_roots(run) for r in describe(root, False)])
    unresolved = [r for run in result['runs'].values() for r in run['nested'] if r['blocking'] != 'closed']
    result['summary'] = dict(actual_records=len(result['actual']),
                             actual_unresolved=[r for r in result['actual'] if r['blocking'] != 'closed'],
                             nested_unresolved=len(unresolved),
                             nested_by_run={k: sum(r['blocking'] != 'closed' for r in v['nested']) for k, v in result['runs'].items()})
    Path(output).write_text(json.dumps(result, indent=1, sort_keys=True) + '\n')
    print(json.dumps(result['summary'], indent=1, default=str))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
