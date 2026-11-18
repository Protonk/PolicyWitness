"""Constructed controls for the worker-wait pilot driver's advisory conclusion.

Each row hands the driver's improvement_conclusion one matched-pair record and
states, in the row, the judgment and facts it must report. The records are the
reader's own output for the dispatcher's constructed equal-pair comparison and
authored verdict records in the shape the reader writes. No app is measured
and no live timing is claimed.

The driver is imported in this process alone. Importing it adds the live
case's directories to the search path and loads that case's capture, seam,
gate and footprint helpers, so these controls run beside the dispatcher's
constructed pilot comparison and not inside the pilot-controls family.
"""
import json
from pathlib import Path
import sys

# The reader's verdict keys, spelled here and not read from the reader or the driver.
IMPROVES = 'improves_beyond_uncertainty_in_every_pair'
IMPROVES_SPREAD = 'improves_beyond_spread_in_every_pair'
WORSENS = 'worsens_beyond_instrument_uncertainty'
WORSENS_SPREAD = 'worsens_beyond_spread_in_any_pair'
WORSENS_SPREAD_EVERY = 'worsens_beyond_spread_in_every_pair'
REQUIRED_PAIRS = 5


def series(improves, improves_spread, worsens, withheld=None):
    """One component's verdict record over the required pairs."""
    value = {'pairs': [dict(index=index) for index in range(REQUIRED_PAIRS)], IMPROVES: improves,
             IMPROVES_SPREAD: improves_spread, WORSENS: worsens, WORSENS_SPREAD: worsens,
             WORSENS_SPREAD_EVERY: False if worsens is not None else None}
    if withheld is not None:
        value['withheld'] = withheld
    return value


def comparison(**cells):
    """A matched-pair record with one rapid entry per named cell."""
    return dict(entries=[dict(cell=cell, regime='rapid', pairs_required=REQUIRED_PAIRS, components=components)
                         for cell, components in cells.items()], unpaired=[])


IMPROVED = series(True, True, False)
WORSENED = series(False, False, True)


def rows(reader_equal_pairs):
    """(name, pairs, cells, dry_run, expected facts, text the detail must contain)."""
    return [
        ('favorable_every_held_total_improves', comparison(O1={'p0.held_total': IMPROVED}), ['O1'], False,
         dict(judgment='favorable', comparison=True, dry_run=False, improved=1, worsened=0, uncovered=[]),
         'all 1 held-total series improve'),
        ('favorable_ignores_other_components', comparison(O1={'p0.held_total': IMPROVED, 'p0.release_to_ack': WORSENED}), ['O1'], False,
         dict(judgment='favorable', improved=1, worsened=0, component_series=2), 'all 1 held-total series improve'),
        ('worsening', comparison(O1={'p0.held_total': WORSENED}), ['O1'], False,
         dict(judgment='unfavorable', comparison=True, improved=0, worsened=1), '1 worsen beyond instrument uncertainty'),
        ('one_series_of_two_worsens', comparison(O1={'p0.held_total': IMPROVED}, O64={'p0.held_total': WORSENED}), ['O1', 'O64'], False,
         dict(judgment='unfavorable', improved=1, worsened=1), '1 of 2 held-total series improve'),
        ('improves_beyond_uncertainty_but_not_spread', comparison(O1={'p0.held_total': series(True, False, False)}), ['O1'], False,
         dict(judgment='unfavorable', improved=0, worsened=0), '0 of 1 held-total series improve'),
        ('withheld_verdict', comparison(O1={'p0.held_total': series(None, None, None, '3 established of 5 required pairs')}), ['O1'], False,
         dict(judgment='unfavorable', improved=0, worsened=0), '0 of 1 held-total series improve'),
        ('cell_without_held_total_pairs', comparison(O1={'p0.held_total': IMPROVED}), ['O1', 'A2'], False,
         dict(judgment='unfavorable', improved=1, uncovered=['A2/rapid']), "no held-total pairs for ['A2/rapid']"),
        ('no_candidate_compared', None, ['O1'], False,
         dict(judgment='unfavorable', comparison=False, dry_run=False, improved=0, worsened=0, series=[]),
         'this run compared no candidate'),
        ('dry_run_earns_no_measurement_credit', comparison(O1={'p0.held_total': IMPROVED}), ['O1'], True,
         dict(judgment='unfavorable', comparison=True, dry_run=True, improved=1), 'a dry run establishes mechanics only'),
        ('reader_output_for_five_equal_pairs', reader_equal_pairs, ['O1'], False,
         dict(judgment='unfavorable', comparison=True, improved=0, worsened=0, uncovered=[], unpaired=0, groups=1),
         '0 of 1 held-total series improve'),
    ]


def main():
    root, summary, out = (Path(value).resolve() for value in sys.argv[1:4])
    sys.path.insert(0, str(root / 'tests/suites/witness_contract'))
    import check_worker_wait_pilot as driver
    reader_equal_pairs = json.loads(summary.read_text())['pairs']
    assert reader_equal_pairs and len(reader_equal_pairs['entries']) == 1, 'the constructed comparison has one cell and regime'
    out.mkdir(parents=True)
    results, problems = [], []
    for name, pairs, cells, dry_run, expected, text in rows(reader_equal_pairs):
        actual = driver.improvement_conclusion(pairs, cells, ['rapid'], dry_run)
        differing = {key: dict(expected=value, actual=actual.get(key)) for key, value in expected.items() if actual.get(key) != value}
        if text not in actual.get('detail', ''):
            differing['detail'] = dict(expected_to_contain=text, actual=actual.get('detail'))
        if actual.get('authority') != 'advisory':
            differing['authority'] = dict(expected='advisory', actual=actual.get('authority'))
        results.append(dict(control=name, cells=cells, dry_run=dry_run, expected=dict(expected, detail_contains=text),
                            conclusion=actual, differing=differing))
        if differing:
            problems.append(f'{name}: {json.dumps(differing, sort_keys=True)}')
    (out / 'controls.json').write_text(json.dumps(dict(
        scope='constructed inputs to the pilot driver\'s advisory conclusion; no live timing claim',
        reader_summary=str(summary), controls=results), indent=2) + '\n')
    assert not problems, 'pilot conclusion controls: ' + '; '.join(problems)
    print(f'{len(results)} pilot conclusion controls passed')


if __name__ == '__main__':
    main()
