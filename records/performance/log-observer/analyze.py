#!/usr/bin/env python3
"""Recompute the two pilot comparisons from attested local raw files."""
import collections
import hashlib
import json
from pathlib import Path
import re
import statistics

import pilot
import summarize

RUNS = ('20261023T233408639400Z-log-pilot-b841', '20261023T233625785042Z-log-pilot-b841')
BASE = Path(__file__).resolve().parent.parent


def stats(values):
    return {'n': len(values), 'min': min(values), 'median': statistics.median(values),
            'max': max(values), 'observations': values}


def main():
    result = {'format_version': 1, 'runs': [], 'comparison_method':
              'Separate runs; exact raw-byte comparison, worker-token matching, no pooled population estimate.'}
    all_pids = []
    historical_payloads = []
    config = json.loads(pilot.CONFIG.read_text())
    pilot.verify_config(config)
    original = json.loads((pilot.OLD_RUN / config['historical_anchor']['file']).read_text())
    original_log = original['data']['sandbox_log_capture']['observer']['data']['log_stdout'].encode()
    for run_id in RUNS:
        raw = BASE / 'runs' / run_id
        exported = BASE / 'evidence' / run_id
        summary = summarize.summarize(raw)
        assert summary == json.loads((exported / 'summary.json').read_text())
        assert summary['integrity'] == {'verified_files': 192, 'unattested': []}
        manifest = json.loads((raw / 'manifest.json').read_text())
        assert manifest['config'] == config
        assert manifest['entries'] == pilot.schedule(config)
        for name, source in (('pilot.py', pilot.HERE / 'pilot.py'), ('summarize.py', pilot.HERE / 'summarize.py'),
                             ('measure.py', pilot.HERE.parent / 'harness/measure.py'),
                             (pilot.FIXTURE.name, pilot.FIXTURE)):
            assert (raw / name).read_bytes() == source.read_bytes()
        run = summary['run']
        assert run['counts'] == {'completed': 44} and run['exit_status'] == 0
        assert run['cleanup']['state'] == 'complete' and run['duration_s'] < 180
        output = {'run_id': run_id, 'started_at': run['started_at'], 'finished_at': run['finished_at'],
                  'duration_s': run['duration_s'], 'cleanup_s': run['cleanup']['elapsed_s'],
                  'integrity': summary['integrity'], 'conditions': {}, 'counts': dict(run['counts']),
                  'cost': [], 'method_pairs': [], 'width_pairs': [], 'availability': [], 'native_attempts': [],
                  'repeated_content': [], 'all_stderr_empty': True, 'no_sleep_or_clock_fault': True,
                  'all_groups_absent': True, 'source_snapshots_match': True}
        for name in ('conditions-start.json', 'conditions-end.json'):
            conditions = json.loads((raw / name).read_text())
            assert all(p['state'] == 'ok' for p in conditions['probes'].values())
            output['conditions'][name] = {
                'observed_at': conditions['observed_at'],
                'probes': {k: v['stdout'] for k, v in conditions['probes'].items()
                           if k in ('os', 'architecture', 'hardware', 'power', 'thermal', 'git_head')},
                'background_servers': conditions['background_servers']}
        log_bytes = {}
        cost_rows = collections.defaultdict(list)
        availability = collections.defaultdict(list)
        for row in summary['observations']:
            sub = raw / row['directory']
            s = row['status']
            assert s['state'] == 'completed' and s['exit_code'] == 0 and s['cutoff'] is None
            assert s['cleanup'] == 'group_absent' and not s['sleep_detected'] and not s['clock_fault']
            assert all(v['eof'] and v['read'] == v['retained'] for v in s['streams'].values())
            assert not (sub / 'stderr.bin').read_bytes()
            independent_wall = (s['clocks_end']['monotonic_raw_ns'] - s['clocks_start']['monotonic_raw_ns']) / 1e6
            independent_process = (s['wait4_monotonic_raw'] - s['popen_enter_monotonic_raw']) * 1000
            assert independent_wall == s['wall_ms'] and independent_process == s['process_wall_ms']
            data = (sub / 'stdout.bin').read_bytes()
            if row['kind'] == 'specimen':
                envelope = json.loads(data)
                assert envelope['build'] == config['identity']['version']['build']
                assert envelope['result']['ok'] and envelope['result']['normalized_outcome'] == 'ok'
                assert envelope['data']['sandbox_log_capture'] is None
                runner = envelope['data']['runner_result']
                all_pids.append(runner['runner_subprocess']['pid'])
                assert len(runner['steps']) == 1
                step = runner['steps'][0]
                output['native_attempts'].append({'event': row['event'], 'worker_pid': runner['runner_subprocess']['pid'],
                    'prediction': step['sandbox_check']['outcome'], 'query_operation': step['sandbox_check']['operation'],
                    'attempt_outcome': step['attempt']['outcome'], 'attempt_rc': step['attempt']['rc'],
                    'attempt_error': step['attempt']['error'], 'attempt_lifecycle': step['attempt']['lifecycle']['summary'],
                    'comparison_observation': step['comparison']['observation'],
                    'comparison_order': step['comparison']['order'], 'target_relation': step['comparison']['target_relation']})
                continue
            if row['method'] == 'observer':
                envelope = json.loads(data)
                assert envelope['build'] == config['identity']['version']['build']
                assert envelope['result']['ok'] is True and row['observer_query_matches']
                inner = envelope['data']['collection']
                assert inner['cutoff'] is None and inner['process']['exit_code'] == 0 and inner['process']['reaped']
                assert inner['cleanup']['outcome'] == 'child_reaped'
                assert not envelope['data']['log_truncated'] and not envelope['data']['log_error']
                assert not envelope['data']['log_stderr']
                data = envelope['data']['log_stdout'].encode()
            assert hashlib.sha256(data).hexdigest() == row['log_sha256']
            log_bytes[row['sequence']] = data
            if row['kind'] == 'cost':
                cost_rows[(row['condition'], row['method'])].append(row)
                if row['condition'] == 'original':
                    historical_payloads.append(data)
            else:
                availability[row['event']].append(row)
                query = row['request']['metadata']['query']
                token = rb'Sandbox:[ \t]+pw-probe-runner\(' + str(query['pid']).encode() + rb'\)[ \t]+deny\([0-9]+\)[ \t]+mach-lookup[ \t]+com\.apple\.logd(?:\s|$)'
                matching = [line for line in data.splitlines() if re.search(token, line)]
                assert len(matching) == 1
                output['availability'].append({'sequence': row['sequence'], 'event': row['event'],
                    'cohort': row['cohort'], 'nominal_delay_s': row['nominal_delay_s'],
                    'actual_start_s': row['actual_launch_delay_s'], 'actual_finish_s': row['actual_finish_delay_s'],
                    'process_wall_ms': s['process_wall_ms'], 'bytes': len(data),
                    'worker_matching_deny_lines': len(matching), 'log_sha256': hashlib.sha256(data).hexdigest(),
                    'query': query})
        for (condition, method), rows in cost_rows.items():
            output['cost'].append({'condition': condition, 'method': method,
                'process_wall_ms': stats([r['status']['process_wall_ms'] for r in rows]),
                'wall_ms': stats([r['status']['wall_ms'] for r in rows]),
                'cpu_ms': stats([(r['status']['cpu_user_s'] + r['status']['cpu_system_s']) * 1000 for r in rows]),
                'log_bytes': [r['log_bytes'] for r in rows],
                'worker_candidate_lines': [len(r['worker_candidate_line_hashes']) for r in rows],
                'sequence_numbers': [r['sequence'] for r in rows],
                'inner_elapsed_ms': [r['observer']['collection']['elapsed_ms'] for r in rows] if method == 'observer' else None})
        for condition in sorted({r['condition'] for r in summary['observations'] if r['kind'] == 'cost'}):
            for block in (1, 2):
                observer = next(r for r in cost_rows[(condition, 'observer')] if r['block'] == block)
                direct = next(r for r in cost_rows[(condition, 'direct')] if r['block'] == block)
                assert log_bytes[observer['sequence']] == log_bytes[direct['sequence']]
                output['method_pairs'].append({'condition': condition, 'block': block, 'same_raw_bytes': True,
                    'observer_minus_direct_ms': observer['status']['process_wall_ms'] - direct['status']['process_wall_ms']})
        for method in ('observer', 'direct'):
            for block in (1, 2):
                original_row = next(r for r in cost_rows[('original', method)] if r['block'] == block)
                wide = next(r for r in cost_rows[('wide_60s', method)] if r['block'] == block)
                assert log_bytes[original_row['sequence']] == log_bytes[wide['sequence']]
                output['width_pairs'].append({'method': method, 'block': block, 'same_raw_bytes': True,
                    'wide_minus_original_ms': wide['status']['process_wall_ms'] - original_row['status']['process_wall_ms']})
        for event, rows in availability.items():
            if len(rows) == 1:
                continue
            values = [log_bytes[r['sequence']] for r in rows]
            assert len(rows) == 3 and all(v == values[0] for v in values)
            assert all(r['request']['metadata']['query'] == rows[0]['request']['metadata']['query'] for r in rows)
            output['repeated_content'].append({'event': event, 'query_count': 3, 'same_query': True,
                'byte_identical': True, 'bytes': len(values[0]), 'sha256': hashlib.sha256(values[0]).hexdigest()})
        result['runs'].append(output)
    assert len(all_pids) == len(set(all_pids)) == 16
    assert len(historical_payloads) == 8
    result.update(distinct_workers=len(set(all_pids)), current_artifacts_match_both_runs=True,
                  historical_original_and_eight_pilot_original_queries_byte_identical=all(v == original_log for v in historical_payloads),
                  historical_original_log_bytes=len(original_log))
    target = BASE / 'evidence/log-observer-pilot-analysis.json'
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'analysis': str(target.relative_to(pilot.ROOT)), 'runs': len(result['runs']),
                      'distinct_workers': result['distinct_workers'],
                      'historical_bytes_identical': result['historical_original_and_eight_pilot_original_queries_byte_identical']}))


if __name__ == '__main__':
    main()
