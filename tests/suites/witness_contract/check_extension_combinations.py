"""Combined native faults: matrix expectations plus independent observer receipts."""
import json
from pathlib import Path
import sys

from check_extension_boundaries import ROOT, run_case, write_json


def lookup(value, path):
    for key in path.split('.'):
        if isinstance(value, dict):
            value = value.get(key)
        elif isinstance(value, list) and key.isdecimal() and int(key) < len(value):
            value = value[int(key)]
        else:
            return None
    return value


def check_row(row, runner, observed):
    for source, expectations in ((runner, row['runner_assert']), (observed, row['observer_assert'])):
        for path, expected in expectations.items():
            actual = lookup(source, path)
            assert (type(actual) is int and actual > 0) if expected == '>0' else actual == expected, \
                (row['id'], path, expected, actual)
    step = next(step for step in runner['steps'] if step['step_id'] == row['step_id'])
    assert step['comparison'] == row['comparison'], (row['id'], step['comparison'], row['comparison'])
    for path, expected in row['assert'].items():
        assert lookup(step, path) == expected, (row['id'], path, expected, lookup(step, path))
    # Every retained fresh read is tied to the independently unchanged fixture.
    expected = b'PW boundary witness\n'
    for step in runner['steps']:
        read = step['attempt'].get('fresh_read') or {}
        if read.get('read_rc', -1) >= 0:
            assert bytes.fromhex(read['content_hex']) == expected


def main():
    pw, directory = sys.argv[1:]
    out = Path(directory).resolve()
    matrix = json.loads((ROOT / 'tests/fixtures/comparison/matrix.json').read_text())
    rows = [row for row in matrix['rows'] if row['specimen'] == 'extension_combinations']
    assert rows, 'missing combined-fault matrix rows'
    results = []
    for row in rows:
        try:
            results.append(run_case(pw, out, row['id'], row['issuer_mode'], row['worker_mode'], row))
        except Exception as exc:
            results.append(dict(case=row['id'], ok=False, error=str(exc)))
        write_json(out / 'results.json', results)
    assert all(r['ok'] for r in results), results
    print(f'{len(rows)} combined-fault matrix rows passed with independent receipts and both readers.')


if __name__ == '__main__':
    main()
