#!/usr/bin/env python3
"""Stand-in controls only. Never execute PolicyWitness or query unified logs."""
import collections
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import threading
from types import SimpleNamespace

import pilot
import summarize


def main():
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    raw = pilot.ROOT / 'records/performance/runs' / (stamp + '-log-preparation-controls')
    evidence = pilot.ROOT / 'records/performance/evidence' / raw.name
    os.umask(0o077)
    raw.mkdir(mode=0o700)
    evidence.mkdir()
    ledger = {'started_at': pilot.common.utc(), 'raw_directory': str(raw.relative_to(pilot.ROOT)),
              'live_queries': 0, 'live_specimen_executions': 0, 'checks': [],
              'sources': {str(p.relative_to(pilot.ROOT)): pilot.common.digest(p)
                          for p in (Path(__file__), pilot.HERE / 'pilot.py', pilot.HERE / 'summarize.py',
                                    pilot.HERE.parent / 'harness/measure.py')}}
    for source in (Path(__file__), pilot.HERE / 'pilot.py', pilot.HERE / 'summarize.py'):
        shutil.copyfile(source, raw / source.name)

    def save():
        (evidence / 'controls.json').write_text(json.dumps(ledger, indent=2) + '\n')

    def check(name, detail=None):
        ledger['checks'].append({'name': name, 'result': 'passed', 'detail': detail})
        save()

    def launch(name, program, timeout=2, limit=4096):
        status = pilot.capture(raw / name, [sys.executable, '-B', '-S', '-c', program], timeout,
                               {'stdout': limit, 'stderr': 4096}, {'control': name})
        (evidence / (name + '-status.json')).write_text(json.dumps(status, indent=2) + '\n')
        return status

    try:
        config = json.loads(pilot.CONFIG.read_text())
        entries = pilot.schedule(config)
        assert collections.Counter(e['kind'] for e in entries) == {'cost': 24, 'specimen': 8, 'availability': 12}
        costs = [e for e in entries if e['kind'] == 'cost']
        assert [(e['condition'], e['method']) for e in costs[:12]] == list(reversed(
            [(e['condition'], e['method']) for e in costs[12:]]))
        for event in {e['event'] for e in entries if 'event' in e}:
            chosen = [e for e in entries if e.get('event') == event]
            assert chosen[0]['kind'] == 'specimen'
            assert [e['nominal_delay_s'] for e in chosen[1:]] == (
                [0, 2, 10] if chosen[0]['cohort'] == 'repeated' else [int(chosen[0]['cohort'].split('_')[1])])
        check('schedule', {'cost_queries': 24, 'fresh_events': 8, 'availability_queries': 12,
                           'second_block_reverses_order': True})
        q = config['historical_anchor']['query']
        assert pilot.direct_argv(q) == ['/usr/bin/log', 'show', '--style', 'syslog', '--info', '--debug',
                                        '--start', q['start'], '--end', q['end'], '--predicate', q['predicate']]
        assert pilot.window(1001, 1999)['start'] == '1969-12-31 23:59:59+0000'
        assert pilot.window(1001, 1999)['end'] == '1970-01-01 00:00:04+0000'
        try:
            pilot.window(2000, 1000)
        except ValueError:
            pass
        else:
            raise AssertionError('reversed clock accepted')
        original = json.loads((pilot.OLD_RUN / 'invocations/00007/stdout.json').read_text())
        query = pilot.event_query(original)
        assert query['pid'] == original['data']['runner_result']['runner_subprocess']['pid']
        mutated = json.loads(json.dumps(original))
        mutated['data']['runner_result']['runner_subprocess']['pid'] = None
        try:
            pilot.event_query(mutated)
        except ValueError:
            pass
        else:
            raise AssertionError('missing worker PID accepted')
        check('query_and_identity', 'production historical predicate/window agree; no fallback PID; backwards span refused')
        with (pilot.ROOT / 'tests/.checkout.lock').open('a+') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            s = launch('ordinary', 'import sys; print("one\\ntwo"); print("diagnostic", file=sys.stderr)')
            assert s['state'] == 'completed' and s['exit_code'] == 0 and s['cleanup'] == 'group_absent'
            assert (raw / 'ordinary/stdout.bin').read_bytes() == b'one\ntwo\n'
            assert all(p['eof'] for p in s['streams'].values())
            check('ordinary_capture', 'exact stdout/stderr, EOF, wait4 and group absence')
            s = launch('nonzero', 'import sys; print("retained"); sys.exit(7)')
            assert s['state'] == 'completed' and s['exit_code'] == 7
            check('nonzero_preserved')
            s = launch('deadline', 'import time; print("partial", flush=True); time.sleep(30)', .1)
            assert s['state'] == 'deadline' and s['exit_code'] == -9 and s['cleanup'] == 'group_absent'
            assert s['wall_ms'] < 1500 and (raw / 'deadline/stdout.bin').read_bytes() == b'partial\n'
            check('deadline', 'partial stdout survives; owned group killed and absent within cleanup allowance')
            s = launch('overflow', 'import os; os.write(1, b"x"*4096)', limit=64)
            assert s['state'] == 'output_overflow' and s['streams']['stdout']['retained'] == 64
            assert s['streams']['stdout']['read'] == 65 and s['cleanup'] == 'group_absent'
            check('output_limit', '64 bytes retained, 65th byte witnesses overflow')
            # Leader exit alone must not finish a capture with an inherited writer.
            s = launch('inherited_writer', 'import os,time; pid=os.fork(); '
                       'time.sleep(30) if pid==0 else os._exit(0)', .1)
            assert s['state'] == 'deadline' and 'exit_observed_monotonic_raw' in s
            assert s['exit_code'] == 0 and s['cleanup'] == 'group_absent'
            check('inherited_writer', 'leader exit retained until deadline/group signal; child writer removed')
            prior_handler = signal.signal(signal.SIGINT, pilot.common.interrupt)
            timer = threading.Timer(.1, lambda: os.kill(os.getpid(), signal.SIGINT))
            timer.start()
            try:
                s = launch('interrupt', 'import time; print("partial", flush=True); time.sleep(30)')
            finally:
                timer.join()
                signal.signal(signal.SIGINT, prior_handler)
                pilot.common.INTERRUPTED = None
            assert s['state'] == 'interrupted' and s['cleanup'] == 'group_absent'
            check('interrupt', 'actual SIGINT recorded; partial output retained and owned group absent')
            missing = pilot.capture(raw / 'missing', ['/definitely/missing/pw-log-control'], 1,
                                    {'stdout': 64, 'stderr': 64}, {'control': 'launch_failure'})
            assert missing['state'] == 'spawn_error' and missing['exit_code'] is None
            check('launch_failure')
        a, b, c = map(lambda x: summarize.sha(x.encode()), ('a', 'b', 'changed'))
        comparison = summarize.compare([a, a, b], [b, a, a])
        assert comparison['reordered_only'] and comparison['duplicates_after'] == {a: 2}
        comparison = summarize.compare([a, b], [a, c, c])
        assert comparison['removed_line_hashes'] == {b: 1}
        assert comparison['added_line_hashes'] == {c: 2}
        assert not comparison['same_multiset']
        assert summarize.compare([], [])['same_sequence']
        assert summarize.fingerprints(b'a\n\n') != summarize.fingerprints(b'a\n')
        assert len(summarize.worker_lines(b'Sandbox: pw-probe-runner(123) deny(1) file\n'
                                         b'Sandbox: pw-probe-runner(1123) deny(1) file\n', 123)) == 1
        check('record_comparison', 'empty, additions/removals, duplicates, order and byte differences remain distinguishable')
        # A small raw-format fixture crosses the reader, including a failed JSON
        # observer reply with process exit 0. Failure must not become success.
        fixture = raw / 'reader-fixture'
        fixture.mkdir()
        reader_entries = []
        for i, (method, payload) in enumerate((('direct', b'a\na\nb\n'), ('direct', b'b\na\na\n'),
                ('observer', json.dumps({'kind': 'sandbox_log_observer_report', 'schema_version': 7,
                    'result': {'ok': False}, 'data': {'observer_schema_version': 2, **q,
                    'log_rc': 1, 'log_error': 'blocked', 'blocked_reason': 'control', 'log_truncated': False,
                    'observed_lines': 0, 'observed_deny': False, 'collection': {}, 'log_stdout': '',
                    'log_stderr': 'control', 'deny_events': []}}).encode())), 1):
            sub = fixture / str(i)
            sub.mkdir()
            entry = {'sequence': i, 'directory': str(i), 'kind': 'availability' if i < 3 else 'cost',
                     'method': method, 'event': 'control', 'query': q, 'condition': 'control'}
            reader_entries.append(entry)
            pilot.common.atomic(sub / 'status.json', dict(s, state='completed', exit_code=0, cutoff=None))
            pilot.common.atomic(sub / 'request.json', {'metadata': {'query': q, 'origin_monotonic_raw': 0}})
            (sub / 'stdout.bin').write_bytes(payload)
            (sub / 'stderr.bin').write_bytes(b'')
        pilot.common.atomic(fixture / 'manifest.json', {'entries': reader_entries})
        pilot.common.atomic(fixture / 'run.json', {'cleanup': {'state': 'incomplete'}})
        (fixture / 'SHA256SUMS').write_text(''.join(f'{pilot.common.digest(p)}  {p.relative_to(fixture)}\n'
                                                    for p in sorted(fixture.rglob('*')) if p.is_file()))
        result = summarize.summarize(fixture)
        assert result['availability_comparisons'][0]['all_lines']['reordered_only']
        assert result['observations'][2]['observer_result']['ok'] is False
        assert result['run']['cleanup']['state'] == 'incomplete'
        (fixture / 'unattested.txt').write_text('deliberately uncovered control')
        assert summarize.verify(fixture)['unattested'] == ['unattested.txt']
        copy = raw / 'tamper-copy'
        shutil.copytree(fixture, copy)
        (copy / '1/stdout.bin').write_bytes(b'tampered')
        try:
            summarize.summarize(copy)
        except ValueError as exc:
            assert 'checksum' in str(exc)
        else:
            raise AssertionError('checksum mismatch accepted')
        check('reader_integrity_and_outcomes', 'failed observer/exit0 retained, incomplete cleanup and uncovered files reported, mismatch refused')
        # Exercise all driver decisions, finalization and the reader using only
        # stand-in executables. Real specimen/log argv is retained as metadata,
        # never launched. Shortened delays test scheduling, not OS availability.
        original_capture, original_schedule = pilot.capture, pilot.schedule
        def control_schedule(config):
            answer = original_schedule(config)
            for entry in answer:
                if entry['kind'] == 'availability':
                    entry['nominal_delay_s'] /= 1000
            return answer

        def control_capture(directory, argv, timeout, limits, metadata):
            if metadata['kind'] == 'specimen':
                payload = json.dumps(original).encode()
            elif metadata['method'] == 'observer':
                payload = json.dumps({'kind': 'sandbox_log_observer_report', 'schema_version': 7,
                    'result': {'ok': True}, 'data': {'observer_schema_version': 2, **metadata['query'],
                    'log_rc': 0, 'log_error': None, 'blocked_reason': None, 'log_truncated': False,
                    'observed_lines': 0, 'observed_deny': False, 'collection': {}, 'log_stdout': '',
                    'log_stderr': '', 'deny_events': []}}).encode()
            else:
                payload = b''
            command = [sys.executable, '-B', '-S', '-c', f'import sys; sys.stdout.buffer.write({payload!r})']
            return original_capture(directory, command, timeout, limits,
                                    dict(metadata, standin=True, unexecuted_production_argv=argv))

        pilot.capture, pilot.schedule = control_capture, control_schedule
        driver_id = stamp + '-log-driver-standin'
        try:
            rc = pilot.run(SimpleNamespace(run_id=driver_id, note='STAND-IN DRIVER CONTROL: no PW or log query; '
                                          'old envelope replayed, delays /1000, synthetic empty query replies.'))
        finally:
            pilot.capture, pilot.schedule = original_capture, original_schedule
        driver_raw = pilot.ROOT / 'records/performance/runs' / driver_id
        driver_summary = summarize.summarize(driver_raw)
        assert rc == 0 and driver_summary['run']['counts'] == {'completed': 44}
        assert driver_summary['run']['cleanup']['state'] == 'complete'
        assert not driver_summary['integrity']['unattested']
        assert len(driver_summary['availability_comparisons']) == 4
        availability = [r for r in driver_summary['observations'] if r['kind'] == 'availability']
        assert len(availability) == 12
        assert all(r['actual_launch_delay_s'] >= r['nominal_delay_s'] for r in availability)
        assert all(r['request']['metadata']['standin'] for r in driver_summary['observations'])
        assert all(r['status']['cleanup'] == 'group_absent' for r in driver_summary['observations'])
        for name in ('run.json', 'SHA256SUMS'):
            shutil.copyfile(driver_raw / name, evidence / ('driver-' + name))
        check('full_driver_standin', {'raw_directory': str(driver_raw.relative_to(pilot.ROOT)),
                                     'observations': 44, 'availability_queries': 12,
                                     'comparison_pairs': 4, 'integrity': driver_summary['integrity'],
                                     'cleanup': driver_summary['run']['cleanup']})
        original_ceiling, original_reserve = pilot.CEILING, pilot.RESERVE
        ceiling_id = stamp + '-log-ceiling-standin'
        def slow_capture(directory, argv, timeout, limits, metadata):
            return original_capture(directory, [sys.executable, '-B', '-S', '-c',
                                    'import time; print("control", flush=True); time.sleep(30)'],
                                    timeout, limits, dict(metadata, standin=True, unexecuted_production_argv=argv))
        pilot.capture, pilot.CEILING, pilot.RESERVE = slow_capture, 3.5, .5
        try:
            rc = pilot.run(SimpleNamespace(run_id=ceiling_id, note='STAND-IN CEILING CONTROL: '
                                          'no PW or log query; 3.5s ceiling, .5s reserve, sleeping stand-in.'))
        finally:
            pilot.capture, pilot.CEILING, pilot.RESERVE = original_capture, original_ceiling, original_reserve
        ceiling_raw = pilot.ROOT / 'records/performance/runs' / ceiling_id
        ceiling_summary = summarize.summarize(ceiling_raw)
        assert rc == 1 and ceiling_summary['run']['stop_reason'] == 'ceiling'
        assert ceiling_summary['run']['counts'] == {'deadline': 1, 'never_started': 43}
        assert ceiling_summary['observations'][0]['request']['metadata']['timeout_source'] == 'ceiling'
        assert ceiling_summary['run']['duration_s'] < 3.5
        assert ceiling_summary['run']['cleanup']['state'] == 'complete'
        for name in ('run.json', 'SHA256SUMS'):
            shutil.copyfile(ceiling_raw / name, evidence / ('ceiling-' + name))
        check('full_driver_ceiling', {'raw_directory': str(ceiling_raw.relative_to(pilot.ROOT)),
                                     'counts': ceiling_summary['run']['counts'],
                                     'duration_s': ceiling_summary['run']['duration_s'],
                                     'integrity': ceiling_summary['integrity']})
        ledger['result'] = 'passed'
    except BaseException as exc:
        ledger.update(result='failed', error=repr(exc))
        raise
    finally:
        ledger['finished_at'] = pilot.common.utc()
        save()
        (raw / 'SHA256SUMS').write_text(''.join(f'{pilot.common.digest(p)}  {p.relative_to(raw)}\n'
                                                for p in sorted(raw.rglob('*')) if p.is_file() and p != raw / 'SHA256SUMS'))
        shutil.copyfile(raw / 'SHA256SUMS', evidence / 'SHA256SUMS')
    print(json.dumps({'evidence': str(evidence.relative_to(pilot.ROOT)), 'result': ledger['result'],
                      'live_queries': 0, 'live_specimen_executions': 0}))


if __name__ == '__main__':
    main()
