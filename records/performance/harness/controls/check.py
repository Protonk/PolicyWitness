#!/usr/bin/env python3
"""Run the investigation's small controls and retain each terminal transcript."""
import argparse
import datetime
import json
import os
from pathlib import Path
import signal
import statistics
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
import summarize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('synthetic', 'live', 'overlap'), required=True)
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    evidence = ROOT / 'records/performance/evidence' / (stamp + '-' + args.mode + '-controls')
    evidence.mkdir(parents=True)
    ledger = {'mode': args.mode, 'checks': [], 'started_at': stamp}
    raw = ROOT / 'records/performance/runs'

    def save():
        (evidence / 'controls.json').write_text(json.dumps(ledger, indent=2) + '\n')

    def run(label, extra, expected, interrupt=False, pilot=False):
        run_id = stamp + '-' + label
        argv = ['/usr/bin/env', '-i', 'PATH=/usr/bin:/bin:/usr/sbin:/sbin',
                'HOME=' + str(Path.home()), str(ROOT / 'tests/lib/python.sh'),
                str(HERE.parent / 'measure.py'), '--expect-build', '841',
                '--config', 'pilot' if pilot else 'control', '--run-id', run_id,
                '--note', 'Harness control or interactive pilot; agent session active. Operator reported AC power, other apps mostly closed, possible calls and screen lock.',
                *extra]
        terminal = evidence / label
        terminal.mkdir()
        (terminal / 'argv.json').write_text(json.dumps(argv, indent=2) + '\n')
        started = time.monotonic()
        with (terminal / 'stdout.txt').open('w') as out, (terminal / 'stderr.txt').open('w') as err:
            child = subprocess.Popen(argv, stdout=out, stderr=err, cwd=ROOT, start_new_session=True)
            if interrupt:
                marker = raw / run_id / 'invocations/00001/stdout.json'
                end = time.monotonic() + 10
                while not (marker.exists() and (interrupt == 'live' or marker.stat().st_size)) and child.poll() is None and time.monotonic() < end:
                    time.sleep(.01)
                if interrupt == 'live':
                    time.sleep(.1)
                if child.poll() is None:
                    os.kill(child.pid, signal.SIGINT)
            rc = child.wait(timeout=210)
        result = {'label': label, 'argv': argv, 'exit_status': rc, 'expected': expected,
                  'elapsed_s': time.monotonic() - started, 'run_id': run_id}
        ledger['checks'].append(result)
        save()
        assert rc == expected, result
        summary = None
        if (raw / run_id).exists():
            summary = summarize.export(raw / run_id, ROOT / 'records/performance/evidence' / run_id)
            assert summary['counts_match_run'] and not summary['missing_statuses'] and not summary['unexpected_statuses']
            if summary['run']['cleanup']['state'] == 'complete':
                assert not summary['unattested'], summary['unattested']
        return summary, raw / run_id, result

    try:
        if args.mode == 'synthetic':
            sleeper = ['--pw', str(HERE / 'sleeper.py')]
            quick = ['--pw', str(HERE / 'quick.py')]
            s, path, result = run('identity-refusal', quick + ['--expect-build', '842'], 2)
            assert not path.exists()
            s, path, result = run('interrupt', sleeper, 1, interrupt=True)
            assert s['counts'] == {'interrupted': 1, 'never_started': 2}, s['counts']
            s, path, result = run('nominal-deadline', sleeper + ['--nominal-s', '.2'], 0)
            for entry in summarize.read(path / 'manifest.json')['entries']:
                status = summarize.read(path / entry['directory'] / 'status.json')
                assert status['state'] == 'harness_timeout' and status['deadline_source'] == 'nominal'
                assert [x['signal'] for x in status['signals']] == [15, 9]
            s, path, result = run('ceiling-deadline', sleeper + ['--ceiling-s', '8', '--cleanup-reserve-s', '4', '--start-margin-s', '.2'], 1)
            status = summarize.read(path / 'invocations/00001/status.json')
            assert status['state'] == 'harness_timeout' and status['deadline_source'] == 'ceiling'
            assert [x['signal'] for x in status['signals']] == [15, 9]
            assert s['run']['duration_s'] < 8 and result['elapsed_s'] < 8
            s, path, result = run('cleanup-exhaustion', quick + ['--control', 'delayed-cleanup', '--cleanup-reserve-s', '.5'], 3)
            assert s['run']['cleanup']['state'] == 'incomplete' and s['unattested']
            assert (path / 'run.json').exists()
            # A deliberately incomplete attestation remains usable; mismatches never do.
            # Exercise a mismatch on a disposable copy, keeping original run bytes intact.
            import shutil
            copy = raw / (stamp + '-tamper-copy')
            shutil.copytree(path, copy)
            with (copy / 'run.json').open('a') as f:
                f.write(' ')
            try:
                summarize.summarize(copy)
            except ValueError as exc:
                assert 'checksum mismatch' in str(exc)
                ledger['checks'].append({'label': 'checksum-mismatch', 'result': 'refused', 'error': str(exc), 'copy': str(copy)})
            else:
                raise AssertionError('tampered attestation accepted')
            # Independent interpretation controls: faulty telemetry is not variability,
            # and a negative mixed-clock residual must survive extraction.
            entry = {'specimen': 'control', 'capture': False}
            status = {'wall_ms': 3, 'rusage': {'ru_utime': .001, 'ru_stime': .002}}
            envelope = {'data': {'runner_client': {'started_at_unix_ms': 100, 'ended_at_unix_ms': 105},
                         'runner_result': {'runner_subprocess': {
                             'ready_wait': {'elapsed_ms': 10, 'clock_fault': False},
                             'sentinel_wait': {'elapsed_ms': 4, 'excluded_ms': 1, 'clock_fault': False},
                             'exit_grace_wait': {'elapsed_ms': 0, 'clock_fault': False}}}}}
            values, missing = summarize.measures(entry, status, envelope)
            assert values['client_residual_without_X'] == -9
            assert missing['L'] == missing['L_inner'] == 'inapplicable'
            sub = envelope['data']['runner_result']['runner_subprocess']
            sub['ready_wait']['elapsed_ms'] = '10'
            sub['sentinel_wait']['clock_fault'] = True
            sub.pop('exit_grace_wait')
            values, missing = summarize.measures(entry, status, envelope)
            assert missing['R'] == missing['S'] == missing['X'] == 'invalid'
            assert missing['G'] == 'absent'
            ledger['checks'].append({'label': 'telemetry-interpretation', 'result': 'passed',
                                     'establishes': ['negative residual retained', 'disabled log measures inapplicable',
                                                    'wrong type and clock fault invalid', 'missing grace absent']})
        elif args.mode == 'live':
            s, path, result = run('pilot', [], 0, pilot=True)
            assert s['counts'] == {'completed': 70}, s['counts']
            # Independent raw W extraction and median, plus a fresh-shell summary comparison.
            manifest = summarize.read(path / 'manifest.json')
            for group in s['groups']:
                walls = []
                for seq in group['sequences']:
                    entry = next(e for e in manifest['entries'] if e['sequence'] == seq)
                    status = summarize.read(path / entry['directory'] / 'status.json')
                    walls.append((status['clocks_end']['monotonic_raw_ns'] - status['clocks_start']['monotonic_raw_ns']) / 1e6)
                assert statistics.median(walls) == group['measures_ms']['W']['median']
            fresh = evidence / 'fresh-summary'
            argv = ['/usr/bin/env', '-i', 'PATH=/usr/bin:/bin:/usr/sbin:/sbin', 'HOME=' + str(Path.home()),
                    str(ROOT / 'tests/lib/python.sh'), str(HERE.parent / 'summarize.py'), str(path), '--out', str(fresh)]
            answer = subprocess.run(argv, capture_output=True, text=True, cwd=ROOT, timeout=30)
            ledger['checks'].append({'label': 'fresh-summary', 'argv': argv, 'exit_status': answer.returncode,
                                     'stdout': answer.stdout, 'stderr': answer.stderr})
            assert answer.returncode == 0
            assert summarize.read(fresh / 'summary.json') == s
            s, path, result = run('missing-request', ['--control', 'missing-request'], 0)
            assert s['counts'] == {'completed': 3}
            status = summarize.read(path / 'invocations/00001/status.json')
            assert status['exit_status'] == 2 and status['stdout_bytes'] > 0
            assert summarize.read(path / 'invocations/00002/status.json')['state'] == 'completed'
            s, path, result = run('short-rehearsal', ['--config', 'short', '--rounds', '1', '--execution-context', 'interactive'], 0)
            assert s['counts'] == {'completed': 11}
            s, path, result = run('live-interrupt', [], 1, interrupt='live', pilot=True)
            assert s['counts'] == {'interrupted': 1, 'never_started': 69}, s['counts']
        else:
            s, path, result = run('overlap', ['--config', 'overlap'], 0)
            assert s['counts'] == {'completed': 20}, s['counts']
            assert len({row['pair'] for row in s['observations']}) == 10
        ledger['result'] = 'passed'
    except Exception as exc:
        ledger.update(result='failed', error=repr(exc))
        save()
        raise
    save()
    print(json.dumps({'evidence': str(evidence), 'result': ledger['result']}))


if __name__ == '__main__':
    main()
