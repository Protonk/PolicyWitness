#!/usr/bin/env python3
"""Verify pilot raw evidence and export content hashes and observation summaries."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import statistics


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fingerprints(data):
    # Compare exact byte lines, including headers, whitespace and order. No
    # heuristic timestamp removal or record-ID inference; blank lines retained.
    return [sha(line) for line in data.splitlines(keepends=True)]


def compare(before, after):
    a, b = collections.Counter(before), collections.Counter(after)
    return {'same_sequence': before == after, 'same_multiset': a == b,
            'added_line_hashes': dict(b - a), 'removed_line_hashes': dict(a - b),
            'reordered_only': a == b and before != after,
            'duplicates_before': {k: n for k, n in a.items() if n > 1},
            'duplicates_after': {k: n for k, n in b.items() if n > 1},
            'modification_identity': 'unestablished; changed lines appear as removals/additions'}


def worker_lines(data, pid):
    token = rb'Sandbox:[ \t]+pw-probe-runner\(' + str(pid).encode() + rb'\)(?:[ \t]|$)'
    return [sha(line) for line in data.splitlines(keepends=True) if re.search(token, line, re.IGNORECASE)]


def verify(directory):
    expected = {}
    for line in (directory / 'SHA256SUMS').read_text().splitlines():
        value, name = line.split('  ', 1)
        path = directory / name
        if Path(name).is_absolute() or not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError('checksum path escapes raw directory')
        if name in expected or sha(path.read_bytes()) != value:
            raise ValueError(f'duplicate or mismatched checksum: {name}')
        expected[name] = value
    files = {str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()}
    return {'verified_files': len(expected), 'unattested': sorted(files - set(expected) - {'SHA256SUMS'})}


def summarize(directory):
    integrity = verify(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    run = json.loads((directory / 'run.json').read_text())
    rows = []
    for entry in manifest['entries']:
        path = directory / entry['directory']
        status = json.loads((path / 'status.json').read_text())
        row = dict(entry, status=status)
        if (path / 'request.json').exists():
            request = json.loads((path / 'request.json').read_text())
            row['request'] = request
            if entry['kind'] == 'availability' and 'popen_enter_monotonic_raw' in status:
                row['actual_launch_delay_s'] = status['popen_enter_monotonic_raw'] - request['metadata']['origin_monotonic_raw']
                row['actual_finish_delay_s'] = (status['wait4_monotonic_raw'] - request['metadata']['origin_monotonic_raw']
                                                if 'wait4_monotonic_raw' in status else None)
        if (path / 'stdout.bin').exists():
            raw = (path / 'stdout.bin').read_bytes()
            row['stdout_sha256'] = sha(raw)
            row['stderr_sha256'] = sha((path / 'stderr.bin').read_bytes())
            if entry['kind'] == 'specimen':
                try:
                    envelope = json.loads(raw)
                    row['execution_result'] = envelope['result']
                    row['worker_pid'] = envelope['data']['runner_result']['runner_subprocess']['pid']
                except (ValueError, KeyError, TypeError) as exc:
                    row['reader_error'] = repr(exc)
            else:
                log = raw
                if entry['method'] == 'observer':
                    log = None
                    try:
                        envelope = json.loads(raw)
                        if envelope['kind'] != 'sandbox_log_observer_report' or envelope['schema_version'] != 7:
                            raise ValueError('unsupported observer envelope')
                        data = envelope['data']
                        if data['observer_schema_version'] != 2:
                            raise ValueError('unsupported observer schema')
                        row['observer'] = {k: data[k] for k in (
                            'log_rc', 'log_error', 'blocked_reason', 'log_truncated', 'observed_lines',
                            'observed_deny', 'collection')}
                        row['observer_result'] = envelope['result']
                        row['observer_query_matches'] = all(data[k] == entry['query'][k]
                                                            for k in ('pid', 'start', 'end', 'predicate'))
                        log = data['log_stdout'].encode('utf-8')
                        row['log_stderr_sha256'] = sha(data['log_stderr'].encode('utf-8'))
                        row['deny_event_line_hashes'] = [sha(e['raw_line'].encode('utf-8')) for e in data['deny_events']]
                    except (ValueError, KeyError, TypeError) as exc:
                        row['reader_error'] = repr(exc)
                if log is not None:
                    row.update(log_bytes=len(log), log_sha256=sha(log), line_hashes=fingerprints(log))
                    # Candidate subset only; full output is compared above too.
                    query = row['request']['metadata']['query']
                    row['worker_candidate_line_hashes'] = worker_lines(log, query['pid'])
        rows.append(row)
    comparisons = []
    prior = {}
    for row in rows:
        if row['kind'] != 'availability' or 'line_hashes' not in row:
            continue
        event = row['event']
        if event in prior:
            previous = prior[event]
            same_query = row['request']['metadata']['query'] == previous['request']['metadata']['query']
            if not same_query:
                raise ValueError('availability repetitions changed query')
            comparisons.append({'event': event, 'before_sequence': previous['sequence'],
                                'after_sequence': row['sequence'], 'query_identical': same_query,
                                'all_lines': compare(previous['line_hashes'], row['line_hashes']),
                                'worker_candidates': compare(previous['worker_candidate_line_hashes'],
                                                             row['worker_candidate_line_hashes'])})
        prior[event] = row
    groups = collections.defaultdict(list)
    for row in rows:
        status = row['status']
        if row['kind'] != 'cost' or 'wall_ms' not in status:
            continue
        outcome = json.dumps({'state': status['state'], 'exit_code': status['exit_code'],
                              'cutoff': status['cutoff'], 'cleanup': status['cleanup'],
                              'sleep_detected': status['sleep_detected'], 'clock_fault': status['clock_fault'],
                              'observer_result': row.get('observer_result', {}).get('ok'),
                              'observer_error': row.get('observer', {}).get('log_error'),
                              'observer_log_rc': row.get('observer', {}).get('log_rc'),
                              'observer_truncated': row.get('observer', {}).get('log_truncated'),
                              'observer_query_matches': row.get('observer_query_matches'),
                              'reader_error': row.get('reader_error')}, sort_keys=True)
        groups[(row['condition'], row['method'], outcome)].append(status)
    distributions = [{'condition': key[0], 'method': key[1], 'outcome': json.loads(key[2]),
                      'n': len(values), 'durations_ms': {
                          measure: {'n': len(readable), 'absent': len(values) - len(readable),
                                    'min': min(readable) if readable else None,
                                    'median': statistics.median(readable) if readable else None,
                                    'max': max(readable) if readable else None, 'observations': readable}
                          for measure in ('wall_ms', 'process_wall_ms')
                          for readable in [[v[measure] for v in values if type(v.get(measure)) in (int, float)]]}}
                     for key, values in groups.items()]
    return {'format_version': 1, 'run': run, 'integrity': integrity, 'observations': rows,
            'cost_distributions': distributions, 'availability_comparisons': comparisons,
            'matching_limits': 'Exact byte-line hashes preserve duplicate counts/order, but supply no stable OS record identity. '
                               'A removal plus addition cannot establish a modified record. Observer log text may be lossy on decoding failure. '
                               'Header/footer differences remain in full comparisons; worker-candidate filtering is not causal attribution.',
            'raw_evidence': 'Local-only gitignored files; hashes are not a portable copy of raw log content.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if args.out.resolve().is_relative_to(args.directory.resolve()):
        raise ValueError('derived evidence must stay outside the raw run')
    result = summarize(args.directory)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / 'summary.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    for name in ('manifest.json', 'run.json', 'SHA256SUMS'):
        (args.out / name).write_bytes((args.directory / name).read_bytes())
    print(json.dumps({'output': str(args.out), 'observations': len(result['observations']),
                      'integrity': result['integrity']}))


if __name__ == '__main__':
    main()
