"""Reproduce the first-cycle analysis from immutable local raw evidence.

Run from the repository root with tests/lib/python.sh and this file's path.
This writes analysis.json beside itself; it never changes a raw run directory.
"""
import collections
import hashlib
import json
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PERFORMANCE = ROOT / 'records/performance'
sys.path.insert(0, str(PERFORMANCE / 'harness'))
import summarize

RUN_ID = HERE.name
PILOTS = ('20261023T201755491161Z-pilot', '20261023T202250234510Z-pilot')


def read(path):
    return json.loads(path.read_text())


def stats(values):
    ordered = sorted(values)
    return {'n': len(values), 'minimum': ordered[0], 'median': statistics.median(ordered),
            'p90': ordered[(9 * len(ordered) + 9) // 10 - 1], 'maximum': ordered[-1]}


def analyze():
    raw = PERFORMANCE / 'runs' / RUN_ID
    summary = summarize.summarize(raw)  # Includes checksum verification.
    assert summary == read(HERE / 'summary.json'), 'saved summary differs from rederivation'
    assert summary['counts_match_run']
    assert not summary['missing_statuses'] and not summary['unexpected_statuses']
    manifest = read(raw / 'manifest.json')
    by_sequence = {row['sequence']: row for row in summary['observations']}
    wait_methods = collections.Counter()
    envelope_builds = collections.Counter()
    child_exit_signals = collections.Counter()
    raw_wall = collections.defaultdict(list)
    for entry in manifest['entries']:
        directory = raw / entry['directory']
        status = read(directory / 'status.json')
        envelope = read(directory / 'stdout.json')
        row = by_sequence[entry['sequence']]
        assert 'host_pid' not in row
        assert row['runner_result_pid'] == envelope.get('data', {}).get('runner_result', {}).get('pid')
        wait_methods[status['wait_method']] += 1
        envelope_builds[json.dumps(envelope['build'], sort_keys=True)] += 1
        child_exit_signals[str(status['term_signal'])] += 1
        start, end = status['clocks_start'], status['clocks_end']
        measured = (end['monotonic_raw_ns'] - start['monotonic_raw_ns']) / 1e6
        assert measured == row['measures_ms']['W']
        assert status['system_sleep_ms'] == 0 and not status['sleep_detected']
        assert status['exit_status'] == 0 and status['state'] == 'completed'
        raw_wall[entry['cell']].append(measured)
    for group in summary['groups']:
        assert stats(raw_wall[group['cell']]) == group['measures_ms']['W']
    snapshot_matches = {}
    for source in (raw / 'harness').rglob('*'):
        if source.is_file():
            current = PERFORMANCE / 'harness' / source.relative_to(raw / 'harness')
            snapshot_matches[str(source.relative_to(raw))] = source.read_bytes() == current.read_bytes()
    # The post-run reader corrects the role assigned to runner_result.pid.
    assert all(value for name, value in snapshot_matches.items() if name != 'harness/summarize.py')
    fixture_matches = {}
    for specimen in (raw / 'specimens').glob('*.json'):
        current = ROOT / 'tests/fixtures/pw_runner' / ('specimen_' + specimen.name)
        fixture_matches[specimen.name] = specimen.read_bytes() == current.read_bytes()
    assert all(fixture_matches.values())
    cells = {}
    for group in summary['groups']:
        cell = group['cell']
        rows = [r for r in summary['observations'] if r['cell'] == cell]
        cells[cell] = {'stratum': group['stratum'], 'measures_ms': group['measures_ms'],
                       'quarters': {}}
        for quarter in range(4):
            sample = [r for r in rows if quarter * 33 < r['round'] <= (quarter + 1) * 33]
            cells[cell]['quarters'][str(quarter + 1)] = {
                measure: stats([r['measures_ms'][measure] for r in sample])
                for measure in ('W', 'C', 'R', 'S', 'L') if measure in sample[0]['measures_ms']}
        if cell.endswith('/capture'):
            gaps = [r['measures_ms']['L'] - r['measures_ms']['L_inner'] for r in rows]
            cells[cell]['log_endpoint_gap_ms'] = stats(gaps)
        cells[cell]['maximum_W_observation'] = max(rows, key=lambda r: r['measures_ms']['W'])
    comparisons = {}
    for pilot_id in PILOTS:
        pilot_raw = PERFORMANCE / 'runs' / pilot_id
        pilot = summarize.summarize(pilot_raw)
        assert not pilot['unattested'] and not pilot['excluded']
        assert read(pilot_raw / 'manifest.json')['identity']['files'] == manifest['identity']['files']
        comparisons[pilot_id] = {}
        for group in pilot['groups']:
            if group['warmup']:
                continue
            cell = group['cell']
            comparisons[pilot_id][cell] = {}
            for measure in ('W', 'C', 'R', 'S', 'L', 'U'):
                if measure not in group['measures_ms']:
                    continue
                before = group['measures_ms'][measure]
                after = cells[cell]['measures_ms'][measure]
                comparisons[pilot_id][cell][measure] = {
                    'pilot': before, 'operator': after,
                    'median_difference_ms': after['median'] - before['median'],
                    'median_difference_percent': 100 * (after['median'] / before['median'] - 1)
                    if before['median'] != 0 else None}
    specimen_rows = [r for r in summary['observations'] if r['cell'] != 'version']
    results = {
        'run_id': RUN_ID, 'raw_evidence': 'gitignored; available only in this checkout',
        'checks': {'all_listed_checksums_verified': True, 'unattested': summary['unattested'],
                   'excluded': summary['excluded'], 'counts': summary['counts'],
                   'raw_wall_statistics_match_summary': True,
                   'harness_snapshot_matches': snapshot_matches, 'fixtures_match': fixture_matches,
                   'envelope_builds': dict(envelope_builds), 'wait_methods': dict(wait_methods),
                   'controller_term_signals': dict(child_exit_signals)},
        'sample_sizes': {'invocations': len(summary['observations']), 'specimen_runs': len(specimen_rows),
                         'distinct_host_pids': 'not established by retained successful-run fields',
                         'unique_worker_pids': len({r['worker_pid'] for r in specimen_rows})},
        'cells': cells, 'pilot_comparisons': comparisons,
        'analysis_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'definitions': {'quarters': 'rounds 1–33, 34–66, 67–99, 100–132; n=33 per cell in each',
                        'harness_snapshot_difference': 'summarize.py alone changed after execution: summary format 2 corrects the top-level PID label; invocation machinery is identical',
                        'log_endpoint_gap_ms': 'L minus L_inner, shared origin; not an isolated controller stage',
                        'pilot_comparisons': 'separate per-cell descriptive distributions; warm-ups excluded; no causal attribution',
                        'p90': 'nearest rank, ceil(0.9*n), without interpolation'}}
    (HERE / 'analysis.json').write_text(json.dumps(results, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'run_id': RUN_ID, 'checks': 'passed', 'cells': len(cells)}))


if __name__ == '__main__':
    analyze()
