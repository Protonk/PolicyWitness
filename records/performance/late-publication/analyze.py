#!/usr/bin/env python3
"""Read one late-publication run into per-unit event orders and reached cases.

Verifies SHA256SUMS first, then writes units.json, summary.json and a trimmed
run-record.json to --out. Fixture times are CLOCK_MONOTONIC_RAW and reported
relative to the driver's release call. The case each unit reached is decided
from its observations, never from its label; a unit that reached a different
case is reported as such.
"""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys

KEPT_NAMES = ('Python', 'python', 'claude', 'codex', 'policy-witness', 'LatePublicationProbe',
              'pw-probe-runner', 'launchd', 'logd')
WNOHANG = 1
RUNNING, WAITING = 1, 3


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(run_dir):
    listed = dict(reversed(line.split('  ', 1)) for line in (run_dir / 'SHA256SUMS').read_text().splitlines())
    bad = [n for n, d in listed.items() if sha256(run_dir / n) != d]
    if bad:
        raise SystemExit(f'checksum mismatch: {bad}')
    present = {str(p.relative_to(run_dir)) for p in run_dir.rglob('*') if p.is_file()} - {'SHA256SUMS'}
    return {'listed': len(listed), 'unattested': sorted(present - set(listed))}


def describe(values):
    present = sorted(v for v in values if v is not None)
    out = {'n': len(present), 'absent': len(values) - len(present)}
    if present:
        out.update({'min': present[0], 'median': statistics.median(present), 'max': present[-1]})
    return out


def top_cpu(probe):
    rows = []
    for line in probe.get('stdout', '').splitlines()[1:16]:
        fields = line.split(None, 3)
        if len(fields) == 4:
            name = fields[3].rsplit('/', 1)[-1]
            rows.append({'pid': int(fields[0]), 'ppid': int(fields[1]), 'cpu_percent': float(fields[2]),
                         'name': name if name.startswith(KEPT_NAMES) else '<other>'})
    return {'argv': probe['argv'], 'exit': probe.get('exit'), 'top_cpu': rows,
            'note': 'raw run.json retains the full snapshot locally'}


def fixture_unit(unit_dir, status):
    f = json.loads((unit_dir / 'fixture.json').read_text())
    ticks_ns = f['mach_timebase'][0] / f['mach_timebase'][1]
    kind, out = next(iter(f['driver'].items()))
    if kind != 'success':
        return {'driver_result': kind, 'reached': 'not_reached:driver_failure'}
    release = f['release_ordinal_calls'][0]['at_ns'] if f['release_ordinal_calls'] else None

    def rel(ns):
        return None if ns is None or release is None else (ns - release) / 1e6

    calls = f['process_calls']
    worker_pid = out['workerPid']
    sentinel_sleeps = [c for c in calls if c['call'] == 'sleep' and c['requested_ns'] <= 2_000_000]
    first_sentinel = sentinel_sleeps[0]['start_ns'] if sentinel_sleeps else None
    grace_sleeps = [c for c in calls if c['call'] == 'sleep' and c['requested_ns'] == 10_000_000
                    and first_sentinel is not None and c['start_ns'] > first_sentinel]
    last_sentinel_end = sentinel_sleeps[-1]['end_ns'] if sentinel_sleeps else None
    grace_waits = [c for c in calls if c['call'] == 'wait' and c['options'] == WNOHANG
                   and last_sentinel_end is not None and c['start_ns'] >= last_sentinel_end]
    reap = next((c for c in calls if c['call'] == 'wait' and c['rc'] == worker_pid), None)
    kill = next((c for c in calls if c['call'] == 'kill'), None)
    unblock = next((e for e in f['events'] if e['kind'] == 'unblock'), None)
    exit_event = next((e for e in f['events'] if e['kind'] == 'worker_exit_kevent'), None)
    exit_request_bracket = ([rel(last_sentinel_end), rel(grace_waits[0]['start_ns'])]
                            if out['pollStopReason'] == 'sentinel_deadline' and grace_waits else None)

    # Scheduler state and CPU before release, and between release and the exit request.
    samples = [s for s in f['samples'] if s.get('rc') == 0]

    def states(s):
        return sorted({t.get('run_state') for t in s.get('threads', []) if 'run_state' in t})

    def cpu_ms(s):
        return (s['user_time'] + s['system_time']) * ticks_ns / 1e6
    before_release = [s for s in samples if release is not None and s['after_ns'] <= release]
    expiry_start = (last_sentinel_end if out['pollStopReason'] == 'sentinel_deadline' else None)
    window_end = expiry_start or (exit_event or {}).get('at_ns')
    pending = [s for s in samples if release is not None and s['before_ns'] >= release
               and window_end is not None and s['after_ns'] <= window_end]
    # Accounting advances in steps of up to ~10 ms; compare samples at least 50 ms apart.
    flat = None
    if len(pending) >= 2 and pending[-1]['before_ns'] - pending[1]['before_ns'] >= 50_000_000:
        flat = cpu_ms(pending[-1]) - cpu_ms(pending[1])
    slot = out['slots'][0]
    phase = out['phases'][0]
    evidence = out.get('workerEvidence') or {}
    unblock_ok = bool(unblock and unblock.get('open_fd_valid') and unblock.get('write_rc') == 1)
    grace_end_ns = (kill or {}).get('start_ns') or (reap or {}).get('end_ns')
    record = {
        'driver_result': kind,
        'worker': {'pid': worker_pid,
                   'identity': (f['hook'].get('worker_identity_entry') or {}),
                   'parent_is_fixture': (f['hook'].get('worker_identity_entry') or {}).get('ppid') == f['fixture_pid']},
        'times_ms_from_release': {
            'hook_entry': rel(f['hook'].get('entry_ns')), 'hook_exit': rel(f['hook'].get('exit_ns')),
            'exit_request_bracket': exit_request_bracket,
            'grace_entry_detected': rel(next((e['at_ns'] for e in f['events']
                                              if e['kind'] == 'grace_entry_detected'), None)),
            'fifo_release_open_returned': rel((unblock or {}).get('open_end_ns')),
            'worker_exit_event': rel((exit_event or {}).get('at_ns')),
            'kill_call': rel((kill or {}).get('start_ns')),
            'reap_wait_returned': rel((reap or {}).get('end_ns')),
        },
        'fifo_release': unblock and {k: unblock.get(k) for k in ('open_fd_valid', 'open_errno', 'write_rc')},
        'states': {
            'before_release': [states(s) for s in before_release],
            'release_to_expiry_or_exit': [states(s) for s in pending],
            'cpu_growth_ms_over_pending_window': flat,
            'pending_window_ms': (pending[-1]['before_ns'] - pending[1]['before_ns']) / 1e6 if len(pending) >= 2 else None,
        },
        'host': {k: out.get(k) for k in ('pollStopReason', 'cleanupTrigger', 'graceEnd', 'collectionBasis',
                                         'sentinelWait', 'graceWait', 'terminationRequest', 'reaped',
                                         'exitCode', 'termSignal', 'exitRequested')},
        'kill': kill and {k: kill[k] for k in ('signal', 'rc', 'errno')},
        'reap_status': (reap or {}).get('status'),
        'final': {'applied': out['applied'], 'done': out['done'], 'phase': phase,
                  'slot': {k: slot.get(k) for k in ('completed', 'rc', 'errnoVal', 'observedPath', 'error',
                                                     'callBoundary')},
                  'progress': evidence.get('progress'), 'failure': evidence.get('failure'),
                  'failure_state': evidence.get('failure_state')},
        'classified': f['classified'],
        'target_existed_after_run': f['target_existed_after_run'],
    }
    host = record['host']
    deadline = host['pollStopReason'] == 'sentinel_deadline'
    blocked_before_expiry = (bool(pending) and all(st == [WAITING] for st in record['states']['release_to_expiry_or_exit'])
                             and flat is not None and flat < 1.0)
    if host['pollStopReason'] == 'done' and slot['completed'] and out['done'] and not kill:
        reached = 'timely'
    elif (deadline and host['graceEnd'] == 'reaped_during_grace' and out['done'] and slot['completed']
          and not unblock and not kill and blocked_before_expiry):
        reached = 'late_done'
    elif (deadline and host['graceEnd'] == 'reaped_during_grace' and slot['completed'] and unblock_ok
          and exit_request_bracket and rel(unblock['open_end_ns']) > exit_request_bracket[1]
          and blocked_before_expiry and not kill):
        reached = 'late_slot'
    elif deadline and host['graceEnd'] == 'exhausted' and kill and not slot['completed']:
        reached = 'grace_exhausted'
    else:
        reached = 'not_reached'
    record['blocked_before_expiry'] = blocked_before_expiry
    record['reached'] = reached
    return record


def cli_unit(unit_dir, status):
    try:
        envelope = json.loads((unit_dir / 'stdout.txt').read_text())
    except (OSError, ValueError) as error:
        return {'envelope_error': repr(error), 'reached': 'not_reached:no_envelope'}
    data = envelope.get('data') or {}
    reply = data.get('runner_result') or {}
    sub = reply.get('runner_subprocess') or {}
    step = (reply.get('steps') or [{}])[0]
    attempt = step.get('attempt') or {}
    release = status.get('fifo_release') or {}
    spawn = status['start']['mono_ns']
    record = {
        'controller_exit': status.get('exit'), 'envelope_outcome': (envelope.get('result') or {}).get('normalized_outcome'),
        'normalized_outcome': reply.get('normalized_outcome'), 'error': reply.get('error'),
        'worker_pid': sub.get('pid'),
        'runner_subprocess': {k: sub.get(k) for k in ('poll_stop_reason', 'cleanup_trigger', 'grace_end',
                                                       'collection_basis', 'sentinel_wait', 'exit_grace_wait',
                                                       'termination_request', 'reaped', 'exit_code', 'term_signal',
                                                       'done_observed', 'partial_steps', 'exit_requested')},
        'worker_progress': (sub.get('worker_evidence') or {}).get('progress'),
        'worker_failure': (sub.get('worker_evidence') or {}).get('failure'),
        'attempt': {k: attempt.get(k) for k in ('rc', 'errno', 'missing_reason', 'observed_path', 'slot',
                                                 'completed', 'requested_kind')},
        'step_keys': sorted(step.keys()),
        'disposition_questions': {k: v.get('answer') for k, v in
                                  ((sub.get('disposition') or {}).get('questions') or {}).items()},
        'fifo_release': release and {'open_end_ms_after_spawn': (release['open_end_ns'] - spawn) / 1e6
                                     if 'open_end_ns' in release else None,
                                     'open_errno': release.get('open_errno'), 'write_rc': release.get('write_rc')},
        'controller_ms': (status['end']['mono_ns'] - spawn) / 1e6,
        'target_existed_after_run': status.get('target_existed_after_run'),
    }
    s = record['runner_subprocess']
    if s['poll_stop_reason'] == 'done' and reply.get('normalized_outcome') == 'ok':
        reached = 'timely'
    elif s['poll_stop_reason'] == 'sentinel_deadline' and s['grace_end'] == 'reaped_during_grace' and not release:
        reached = 'late_done'
    elif (s['poll_stop_reason'] == 'sentinel_deadline' and s['grace_end'] == 'reaped_during_grace'
          and release.get('write_rc') == 1):
        reached = 'late_slot'
    elif s['poll_stop_reason'] == 'sentinel_deadline' and s['grace_end'] == 'exhausted':
        reached = 'grace_exhausted'
    else:
        reached = 'not_reached'
    record['reached'] = reached
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    attestation = verify(args.run_dir)
    run = json.loads((args.run_dir / 'run.json').read_text())
    units = []
    for status_path in sorted((args.run_dir / 'units').glob('*/status.json')):
        status = json.loads(status_path.read_text())
        body = (fixture_unit if status['kind'] == 'fixture' else cli_unit)(status_path.parent, status)
        units.append({'sequence': status['sequence'], 'kind': status['kind'], 'case': status['case'],
                      'state': status['state'], 'exit': status.get('exit'),
                      'worker_processes_after_unit': status['worker_processes_after_unit'], **body})
    intended = {'timely': 'timely', 'late-done': 'late_done', 'late-slot': 'late_slot',
                'grace-exhausted': 'grace_exhausted'}
    cases = {}
    for unit in units:
        key = f"{unit['kind']}:{unit['case']}"
        entry = cases.setdefault(key, {'n': 0, 'reached': {}, 'sequences': []})
        entry['n'] += 1
        entry['sequences'].append(unit['sequence'])
        entry['reached'][unit['reached']] = entry['reached'].get(unit['reached'], 0) + 1
    fixture_units = [u for u in units if u['kind'] == 'fixture']
    timing = {}
    for case in intended:
        group = [u for u in fixture_units if u['case'] == case]
        timing[case] = {name: describe([(u['times_ms_from_release'].get(name) if not isinstance(
            u['times_ms_from_release'].get(name), list) else u['times_ms_from_release'][name][1]) for u in group])
            for name in ('exit_request_bracket', 'grace_entry_detected', 'fifo_release_open_returned',
                         'worker_exit_event', 'kill_call', 'reap_wait_returned')}
    record = {k: v for k, v in run.items() if k not in ('conditions_start', 'conditions_end')}
    for key in ('conditions_start', 'conditions_end'):
        record[key] = {'at': run[key]['at'], 'probes': [top_cpu(p) if p['argv'][0] == '/bin/ps' else p
                                                        for p in run[key]['probes']]}
    summary = {'run_id': args.run_dir.name, 'stop_reason': run['stop_reason'], 'attestation': attestation,
               'raw_sha256sums_sha256': sha256(args.run_dir / 'SHA256SUMS'),
               'units_run': run['units_run'], 'never_started': run['never_started'],
               'order': [f"{u['sequence']}:{u['kind']}:{u['case']}" for u in units],
               'past_deadline': [u['sequence'] for u in units if u['state'] != 'exited'],
               'survivors': [u['sequence'] for u in units if u['worker_processes_after_unit']],
               'worker_processes_after_run': run['worker_processes_after'],
               'cases': cases,
               'mismatched': [u['sequence'] for u in units
                              if u['reached'] != intended[u['case'].removeprefix('cli-')]],
               'fixture_times_ms_from_release': timing}
    args.out.mkdir(parents=True, exist_ok=True)
    for name, value in (('units.json', units), ('summary.json', summary), ('run-record.json', record)):
        (args.out / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    json.dump(summary, sys.stdout, indent=2, sort_keys=True)
    print()


if __name__ == '__main__':
    main()
