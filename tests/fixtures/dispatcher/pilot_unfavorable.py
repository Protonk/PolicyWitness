"""Construct a valid pilot comparison whose candidate does not improve.

This fixture exercises the existing worker-wait reader. It measures no app and
establishes no live timing claim; all ten trial inputs and calibration receipts
are independently constructed and retained for inspection.
"""
import json
from pathlib import Path
import sys


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def construct(root, out):
    if out.exists():
        raise ValueError('constructed pilot output must be fresh')
    sys.path.insert(0, str(root / 'tests/suites/witness_contract'))
    import worker_wait_pilot_controls as fixtures
    import worker_wait_pilot_reader as reader

    # Equal baseline and candidate timestamps imply zero differences in all
    # five pairs. This expectation is authored before invoking any reader.
    expected = dict(
        scope='constructed interpretation control; no live timing claim',
        pairs_required=5, accepted_rows=10, matched_indices=[0, 1, 2, 3, 4],
        component='p0.held_total', differences_ns=[0, 0, 0, 0, 0],
        improves_beyond_uncertainty_in_every_pair=False,
        improves_beyond_spread_in_every_pair=False,
        judgment='unfavorable',
        proposition='the candidate improves held total beyond uncertainty and spread in every required pair')
    write(out / 'independent-expectation.json', expected)
    for index in range(5):
        for app in ('baseline', 'candidate'):
            bundle = fixtures.ordinary_bundle(index=index)
            bundle['trial']['app'] = app
            fixtures.write_bundle(out, bundle)
    write(out / 'schedule.json', dict(
        required={'baseline/O1/rapid': 5, 'candidate/O1/rapid': 5},
        comparison=dict(apps=['baseline', 'candidate'], pairs_required=5,
                        pairing_rule='constructed: same cell, regime and repetition index')))
    fixtures.write_calibration(out)
    decomposition, summary = reader.read_artifacts(out)
    rows, pairs = decomposition['rows'], summary['pairs']
    assert (summary['instrument_gate'] or {}).get('credited') is True
    assert len(rows) == expected['accepted_rows']
    assert all(row['status'] == 'accepted' and not row['problems'] and not row['exclusions'] for row in rows)
    assert pairs['unpaired'] == [] and len(pairs['entries']) == 1
    entry = pairs['entries'][0]
    assert entry['pairs_required'] == expected['pairs_required']
    assert [pair['index'] for pair in entry['pairs']] == expected['matched_indices']
    actual = entry['components'][expected['component']]
    assert [pair['difference'] for pair in actual['pairs']] == expected['differences_ns']
    for field in ('improves_beyond_uncertainty_in_every_pair', 'improves_beyond_spread_in_every_pair'):
        assert actual[field] is expected[field]
    assert 'withheld' not in actual
    # This product judgment follows the actual reader's two established
    # comparison verdicts. Validity assertions above remain independently fatal.
    favorable = (actual['improves_beyond_uncertainty_in_every_pair'] is True
                 and actual['improves_beyond_spread_in_every_pair'] is True)
    conclusion = dict(scope=expected['scope'], valid=True,
                      proposition=expected['proposition'],
                      judgment='favorable' if favorable else 'unfavorable',
                      matched_pairs=len(entry['pairs']), component=expected['component'],
                      reader_conclusion=actual,
                      evidence=['independent-expectation.json', 'schedule.json',
                                'decomposition.json', 'summary.json', 'summary.md', 'clock-pair/calibration.json'])
    assert conclusion['judgment'] == expected['judgment']
    write(out / 'conclusion.json', conclusion)
    return conclusion


if __name__ == '__main__':
    construct(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
