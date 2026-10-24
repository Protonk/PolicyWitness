#!/usr/bin/env python3
"""Read one measure.py run into per-unit observations and per-condition summaries.

Verifies SHA256SUMS first. Writes units.json, summary.json and a trimmed
run-record.json to --out. Times are CLOCK_MONOTONIC_RAW; rusage_info CPU fields
are mach ticks converted with the fixture's recorded timebase. Absent
observations stay null and are counted.
"""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys

KEPT_NAMES = ('Python', 'python', 'claude', 'codex', 'policy-witness', 'PhaseBarrierProbe',
              'pw-probe-runner', 'launchd', 'logd')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(run_dir):
    listed = dict(reversed(line.split('  ', 1)) for line in (run_dir / 'SHA256SUMS').read_text().splitlines())
    bad = [n for n, d in listed.items() if sha256(run_dir / n) != d]
    if bad:
        raise SystemExit(f'checksum mismatch: {bad}')
    present = {str(p.relative_to(run_dir)) for p in run_dir.rglob('*') if p.is_file()} - {'SHA256SUMS'}
    return {'listed': len(listed), 'unattested': sorted(present - set(listed))}


def ms(later, earlier):
    return None if later is None or earlier is None else (later - earlier) / 1e6


def describe(values):
    present = sorted(v for v in values if v is not None)
    out = {'n': len(present), 'absent': len(values) - len(present)}
    if present:
        out.update({'min': present[0], 'median': statistics.median(present),
                    'p90': present[max(0, -(-9 * len(present) // 10) - 1)], 'max': present[-1]})
    return out


def cpu_delta(a, b, ticks_ns):
    """Worker CPU between two rusage reads, over the window between them."""
    if not a or not b or a.get('rc') != 0 or b.get('rc') != 0:
        return None
    if a['proc_start_abstime'] != b['proc_start_abstime']:
        return {'generation_mismatch': True}
    window = (b['before_ns'] - a['after_ns']) / 1e6
    d = {k: (b[k] - a[k]) * ticks_ns / 1e6 for k in
         ('user_time', 'system_time', 'user_ptime', 'system_ptime', 'runnable_time')}
    cpu = d['user_time'] + d['system_time']
    return {'window_ms': window, 'cpu_ms': cpu, 'cpu_fraction_of_window': cpu / window if window > 0 else None,
            'pcore_cpu_ms': d['user_ptime'] + d['system_ptime'], 'user_ms': d['user_time'],
            'system_ms': d['system_time'], 'runnable_ms': d['runnable_time'],
            'cycles': b['cycles'] - a['cycles'], 'instructions': b['instructions'] - a['instructions'],
            'exited_by_second_read': b['proc_exit_abstime'] != 0}


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


def unit_record(run_dir, status):
    unit_dir = run_dir / 'units' / f'{status["sequence"]:03d}-{status["condition"]}'
    base = {'sequence': status['sequence'], 'round': status['round'], 'condition': status['condition'],
            'state': status['state'], 'exit': status.get('exit'),
            'harness_elapsed_ms': ms(status['end']['mono_ns'], status['start']['mono_ns']),
            'identified_worker_survived': status['identified_worker_survived'],
            'worker_processes_after_unit': status['worker_processes_after_unit']}
    try:
        f = json.loads((unit_dir / 'fixture.json').read_text())
    except (OSError, ValueError) as error:
        return {**base, 'fixture_record_error': repr(error)}
    ticks_ns = f['mach_timebase'][0] / f['mach_timebase'][1]
    kind, driver = next(iter(f['driver'].items()))
    out = driver if kind == 'success' else (driver[1] if isinstance(driver, list) and len(driver) > 1 else None)
    hook = f['hook']
    entry, exit_ = hook.get('entry_ns'), hook.get('exit_ns')
    releases = [c['at_ns'] for c in f['release_ordinal_calls']]
    vnode = [e['at_ns'] for e in f['kevents'] if e['kind'] == 'vnode']
    proc = [e['at_ns'] for e in f['kevents'] if e['kind'] == 'proc']
    identity = hook.get('worker_identity_entry') or {}
    cal_a, cal_b = f['calibration']['before'], f['calibration']['after']
    cal_ticks = (cal_b['rusage_info']['user_time'] + cal_b['rusage_info']['system_time']
                 - cal_a['rusage_info']['user_time'] - cal_a['rusage_info']['system_time'])
    cal_us = (cal_b['getrusage']['user_us'] + cal_b['getrusage']['system_us']
              - cal_a['getrusage']['user_us'] - cal_a['getrusage']['system_us'])
    children = f['children_usage']
    fixture_hold = None
    if hook.get('fixture_usage_entry') and hook.get('fixture_usage_exit'):
        a, b = hook['fixture_usage_entry'], hook['fixture_usage_exit']
        fixture_hold = (b['user_us'] + b['system_us'] - a['user_us'] - a['system_us']) / 1000
    dense = f.get('dense_samples') or []
    dense_record = None
    if dense:
        ok = [s for s in dense if s['rc'] == 0]
        in_hold = [s for s in ok if exit_ is not None and s['after_ns'] <= exit_]
        after_hold = [s for s in ok if exit_ is not None and s['before_ns'] >= exit_]
        gaps = [(b['before_ns'] - a['before_ns']) / 1e6 for a, b in zip(dense, dense[1:])]
        dense_record = {
            'samples': len(dense), 'failed_reads': len(dense) - len(ok),
            'read_cost_us': describe([(s['after_ns'] - s['before_ns']) / 1e3 for s in dense]),
            'interval_ms': describe(gaps),
            'hold_span': cpu_delta(in_hold[0], in_hold[-1], ticks_ns) if len(in_hold) > 1 else None,
            'after_hold_span': cpu_delta(after_hold[0], after_hold[-1], ticks_ns) if len(after_hold) > 1 else None,
            'last_read_exited': bool(ok) and ok[-1]['proc_exit_abstime'] != 0,
        }
    entry_sample = hook.get('sample_entry')
    # Kernel stamps on the monotonic axis: creation time (wall µs) through the
    # wall/monotonic pair read at hook entry; mach absolute stamps through the
    # absolute/continuous pair read there (CLOCK_MONOTONIC_RAW is continuous time).
    clocks = hook.get('clocks_entry')
    start_mono = exit_abs_mono = None
    if clocks and identity.get('start_wall_us') is not None:
        start_mono = identity['start_wall_us'] * 1000 - (clocks['wall_before_ns'] - clocks['mono_ns'])
    exit_abstime = max([s.get('proc_exit_abstime') or 0 for s in
                        [hook.get('sample_exit') or {}] + list(f.get('dense_samples') or [])], default=0)
    if clocks and exit_abstime:
        exit_abs_mono = (exit_abstime + clocks['mach_continuous'] - clocks['mach_absolute']) * ticks_ns
    lifetime_cpu = (children['after']['user_us'] + children['after']['system_us']
                    - children['before']['user_us'] - children['before']['system_us']) / 1000
    before_hook_cpu = None if not entry_sample or entry_sample['rc'] != 0 else \
        (entry_sample['user_time'] + entry_sample['system_time']) * ticks_ns / 1e6
    life = ms(proc[0], start_mono) if proc and start_mono else None
    pre_hook = ms(entry, start_mono) if start_mono else None
    phases = (out or {}).get('phases') or []
    slots = (out or {}).get('slots') or []
    evidence = (out or {}).get('workerEvidence') or {}
    return {
        **base,
        'driver_result': kind,
        'hold_requested_ms': f['options']['hold_ms'], 'proceed_wait_ms': f['options']['proceed_wait_ms'],
        'sampling': f['options']['sampling'],
        'identity': {'worker_pid': identity.get('pid'), 'worker_uniqueid': identity.get('uniqueid'),
                     'worker_start_wall_us': identity.get('start_wall_us'), 'worker_ppid': identity.get('ppid'),
                     'fixture_pid': f['fixture_pid'], 'worker_parent_is_fixture': identity.get('ppid') == f['fixture_pid'],
                     'worker_path': identity.get('path'),
                     'reply_worker_pid': (out or {}).get('workerPid')},
        'phase': phases[0] if phases else None,
        'slot': {k: slots[0].get(k) for k in ('rc', 'errnoVal', 'completed', 'error')} if slots else None,
        'worker_failure': evidence.get('failure'),
        'host': {k: (out or {}).get(k) for k in ('applied', 'applyRC', 'done', 'exitCode', 'termSignal', 'reaped',
                                                   'pollStopReason', 'cleanupTrigger', 'graceEnd', 'collectionBasis',
                                                   'proceedSet', 'proceedObserved', 'proceedOwnershipEstablished',
                                                   'orderingProtocolViolations', 'readyWait', 'sentinelWait',
                                                   'graceWait')},
        'witness': {'file_at_hook_entry': hook.get('file_exists_at_entry'),
                    'file_at_hook_exit': hook.get('file_exists_at_exit'),
                    'file_after_run': f['file_exists_after_run'], 'unlink_events': len(vnode),
                    'release_calls': len(releases), 'worker_exit_events': len(proc)},
        'intervals_ms': {
            'run_start_to_hook_entry': ms(entry, f['run_start_ns']),
            'hold_actual': ms(exit_, entry),
            'hold_overshoot': None if exit_ is None else ms(exit_, entry) - f['options']['hold_ms'],
            'hook_exit_to_release_call': ms(releases[0], exit_) if releases else None,
            'release_call_to_unlink_event': ms(vnode[0], releases[0]) if releases and vnode else None,
            'unlink_event_to_worker_exit_event': ms(proc[0], vnode[0]) if vnode and proc else None,
            'hook_entry_to_worker_exit_event': ms(proc[0], entry) if proc else None,
            'hook_exit_to_worker_exit_event': ms(proc[0], exit_) if proc else None,
            'run_total': ms(f['run_end_ns'], f['run_start_ns']),
            'worker_start_to_hook_entry': pre_hook,
            'worker_start_to_exit_event': life,
            'kernel_exit_stamp_to_exit_event': ms(proc[0], exit_abs_mono) if proc and exit_abs_mono else None,
        },
        'worker_cpu': {
            'before_hook_entry_ms': before_hook_cpu,
            'before_hook_entry_fraction_of_elapsed': before_hook_cpu / pre_hook if before_hook_cpu is not None and pre_hook else None,
            'lifetime_fraction_of_elapsed': lifetime_cpu / life if life else None,
            'hold_boundary': cpu_delta(entry_sample, hook.get('sample_exit'), ticks_ns),
            'dense': dense_record,
            'lifetime_ms_from_children_usage': lifetime_cpu,
        },
        'fixture_cpu_during_hold_ms': fixture_hold,
        'calibration_ticks_per_us': cal_ticks / cal_us if cal_us else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    attestation = verify(args.run_dir)
    run = json.loads((args.run_dir / 'run.json').read_text())
    statuses = [json.loads(p.read_text()) for p in sorted((args.run_dir / 'units').glob('*/status.json'))]
    units = [unit_record(args.run_dir, s) for s in statuses]

    def pick(u, *path):
        for key in path:
            if u is None:
                return None
            u = u.get(key) if isinstance(u, dict) else None
        return u

    measures = {
        'hold_actual_ms': ('intervals_ms', 'hold_actual'),
        'hold_overshoot_ms': ('intervals_ms', 'hold_overshoot'),
        'hook_exit_to_release_call_ms': ('intervals_ms', 'hook_exit_to_release_call'),
        'release_call_to_unlink_event_ms': ('intervals_ms', 'release_call_to_unlink_event'),
        'hook_entry_to_worker_exit_event_ms': ('intervals_ms', 'hook_entry_to_worker_exit_event'),
        'run_start_to_hook_entry_ms': ('intervals_ms', 'run_start_to_hook_entry'),
        'hold_cpu_ms': ('worker_cpu', 'hold_boundary', 'cpu_ms'),
        'hold_cpu_fraction': ('worker_cpu', 'hold_boundary', 'cpu_fraction_of_window'),
        'hold_pcore_cpu_ms': ('worker_cpu', 'hold_boundary', 'pcore_cpu_ms'),
        'hold_runnable_ms': ('worker_cpu', 'hold_boundary', 'runnable_ms'),
        'hold_window_ms': ('worker_cpu', 'hold_boundary', 'window_ms'),
        'dense_hold_cpu_fraction': ('worker_cpu', 'dense', 'hold_span', 'cpu_fraction_of_window'),
        'dense_interval_median_ms': ('worker_cpu', 'dense', 'interval_ms', 'median'),
        'worker_cpu_before_hook_entry_ms': ('worker_cpu', 'before_hook_entry_ms'),
        'worker_lifetime_cpu_ms': ('worker_cpu', 'lifetime_ms_from_children_usage'),
        'worker_lifetime_cpu_fraction': ('worker_cpu', 'lifetime_fraction_of_elapsed'),
        'worker_start_to_hook_entry_ms': ('intervals_ms', 'worker_start_to_hook_entry'),
        'worker_start_to_exit_event_ms': ('intervals_ms', 'worker_start_to_exit_event'),
        'before_hook_cpu_fraction': ('worker_cpu', 'before_hook_entry_fraction_of_elapsed'),
        'kernel_exit_stamp_to_exit_event_ms': ('intervals_ms', 'kernel_exit_stamp_to_exit_event'),
        'fixture_cpu_during_hold_ms': ('fixture_cpu_during_hold_ms',),
        'ready_wait_elapsed_ms': ('host', 'readyWait', 'elapsed_ms'),
        'harness_unit_elapsed_ms': ('harness_elapsed_ms',),
    }
    by_condition = {}
    for name in dict.fromkeys(u['condition'] for u in units):
        group = [u for u in units if u['condition'] == name]
        by_condition[name] = {
            'n': len(group), 'sequences': [u['sequence'] for u in group],
            'outcomes': {key: sorted({json.dumps(pick(u, *path), sort_keys=True) for u in group}) for key, path in {
                'phase': ('phase',), 'slot_rc_completed': ('slot',), 'worker_failure': ('worker_failure',),
                'poll_stop': ('host', 'pollStopReason'), 'cleanup_trigger': ('host', 'cleanupTrigger'),
                'grace_end': ('host', 'graceEnd'), 'collection_basis': ('host', 'collectionBasis'),
                'exit_code': ('host', 'exitCode'), 'term_signal': ('host', 'termSignal'),
                'witness': ('witness',), 'survived': ('identified_worker_survived',),
                'parent_is_fixture': ('identity', 'worker_parent_is_fixture')}.items()},
            'measures': {key: describe([pick(u, *path) for u in group]) for key, path in measures.items()},
        }
    record = {k: v for k, v in run.items() if k not in ('conditions_start', 'conditions_end')}
    for key in ('conditions_start', 'conditions_end'):
        record[key] = {'at': run[key]['at'], 'probes': [top_cpu(p) if p['argv'][0] == '/bin/ps' else p
                                                        for p in run[key]['probes']]}
    summary = {'run_id': args.run_dir.name, 'plan': run['plan'], 'stop_reason': run['stop_reason'],
               'attestation': attestation, 'raw_sha256sums_sha256': sha256(args.run_dir / 'SHA256SUMS'),
               'units_run': run['units_run'], 'never_started': run['never_started'],
               'order': [f"{u['sequence']}:{u['condition']}" for u in units],
               'unclean_units': [u['sequence'] for u in units if u['state'] != 'exited' or u['exit'] != 0],
               'survivors': [u['sequence'] for u in units if u['identified_worker_survived']],
               'worker_processes_after_run': run['worker_processes_after'],
               'distinct_worker_generations': len({(pick(u, 'identity', 'worker_pid'),
                                                    pick(u, 'identity', 'worker_start_wall_us')) for u in units}),
               'calibration_ticks_per_us': describe([u.get('calibration_ticks_per_us') for u in units]),
               'by_condition': by_condition}
    args.out.mkdir(parents=True, exist_ok=True)
    for name, value in (('units.json', units), ('summary.json', summary), ('run-record.json', record)):
        (args.out / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    json.dump(summary, sys.stdout, indent=2, sort_keys=True)
    print()


if __name__ == '__main__':
    main()
