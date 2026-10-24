#!/usr/bin/env python3
"""Join one observe.py run into per-invocation lineage and named intervals.

Reads only the raw run directory (after verifying SHA256SUMS) and writes
summary.json and units.json to --out. Every interval names its two events and
their observers; absent observations stay null and are counted, never zeroed.

All events are placed on the CLOCK_MONOTONIC_RAW axis in microseconds. Harness
observations carry it directly. Kernel creation times (CLOCK_REALTIME) use the
wall-minus-monotonic offset read with that process's own discovery; the
controller's client span uses the offset read at controller spawn. Unified-log
machTimestamp values use the recorded mach timebase.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics
import sys


def sha256(path):
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def verify(run_dir):
    listed = {}
    for line in (run_dir / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        listed[name] = digest
    bad = [n for n, d in listed.items() if sha256(run_dir / n) != d]
    present = {str(p.relative_to(run_dir)) for p in run_dir.rglob('*') if p.is_file()} - {'SHA256SUMS'}
    if bad:
        raise SystemExit(f'checksum mismatch: {bad}')
    return {'listed': len(listed), 'unattested': sorted(present - set(listed))}


def us(at):
    """Monotonic microseconds of a harness observation."""
    return None if at is None else at['mono_ns'] // 1000


def offset_us(at):
    return (at['wall_ns'] - at['mono_ns']) // 1000


def start_us(record):
    """A kernel creation time moved to the monotonic axis by its discovery reading."""
    return None if record is None else record['kernel_start_wall_us'] - offset_us(record['first_seen'])


def exit_us(record):
    return None if record is None or record['exit'] is None else us(record['exit']['at'])


def diff_ms(later, earlier):
    return None if later is None or earlier is None else (later - earlier) / 1000


def describe(values):
    present = sorted(v for v in values if v is not None)
    out = {'n': len(present), 'absent': len(values) - len(present)}
    if present:
        out.update({'min': present[0], 'median': statistics.median(present),
                    'p90': present[max(0, -(-9 * len(present) // 10) - 1)], 'max': present[-1]})
    return out


def log_events(run_dir, timebase):
    path = run_dir / 'launchd-log.ndjson'
    events = []
    if not path.exists():
        return events
    for line in path.read_text().splitlines():
        if not line.startswith('{'):
            continue
        item = json.loads(line)
        if 'timestamp' not in item:
            continue
        events.append({'mono_us': item['machTimestamp'] * timebase[0] // timebase[1] // 1000 if timebase else None,
                       'timestamp': item['timestamp'], 'process_id': item['processID'],
                       'subsystem': item.get('subsystem', ''), 'message': item['eventMessage']})
    return events


KEPT_NAMES = ('Python', 'python', 'claude', 'codex', 'policy-witness', 'pw-runner-client', 'PWRunner',
              'pw-probe-runner', 'sb_api_validator', 'launchd', 'logd')


def top_cpu(probe):
    """The committed copy keeps CPU shares; names only for the interpreter, agents and PolicyWitness."""
    rows = []
    for line in probe.get('stdout', '').splitlines()[1:16]:
        fields = line.split(None, 3)
        if len(fields) < 4:
            continue
        name = fields[3].rsplit('/', 1)[-1]
        rows.append({'pid': int(fields[0]), 'ppid': int(fields[1]), 'cpu_percent': float(fields[2]),
                     'name': name if name.startswith(KEPT_NAMES) else '<other>'})
    return {'argv': probe['argv'], 'exit': probe.get('exit'), 'top_cpu': rows,
            'note': 'raw run.json retains the full snapshot locally'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    run_dir = args.run_dir
    attestation = verify(run_dir)
    run = json.loads((run_dir / 'run.json').read_text())
    processes = json.loads((run_dir / 'processes.json').read_text())
    # Early pilots recorded no timebase; their log events stay off the monotonic axis.
    logs = log_events(run_dir, (run.get('clock_identity_start') or {}).get('mach_timebase'))

    by_uniq = {p['uniqueid']: p for p in processes if p['uniqueid'] is not None}
    children = {}
    for p in processes:
        children.setdefault(p['parent_uniqueid'], []).append(p)

    # launchd's account, keyed by host pid: the domain it was spawned in, spawn and kill messages.
    launchd = {}
    domain_re = re.compile(r'^pid/(\d+)/com\.policywitness\.policy-witness\.PWRunner \[(\d+)\]$')
    for e in logs:
        m = domain_re.match(e['subsystem'])
        if e['process_id'] == 1 and m:
            entry = launchd.setdefault(int(m.group(2)), {'client_pid': int(m.group(1)), 'messages': []})
            entry['messages'].append({'mono_us': e['mono_us'], 'message': e['message']})
    invalidations = {}
    for e in logs:
        m = re.search(r'invalidated because the client process \(pid (\d+)\)', e['message'])
        if m and e['process_id'] != 1:
            invalidations.setdefault(e['process_id'], []).append(
                {'mono_us': e['mono_us'], 'client_pid': int(m.group(1))})

    units = []
    for status in run['units']:
        unit_dir = run_dir / status['unit_dir']
        controller = by_uniq.get(status['uniqueid'])
        envelope, parse_error = None, None
        try:
            envelope = json.loads((unit_dir / 'stdout.json').read_text())
        except (OSError, ValueError) as error:
            parse_error = repr(error)
        data = (envelope or {}).get('data') or {}
        reply = data.get('runner_result') or {}
        client_capture = data.get('runner_client') or {}
        subprocess_record = reply.get('runner_subprocess') or {}
        clients = [p for p in children.get(status['uniqueid'], []) if p['role'] == 'client']
        client = clients[0] if len(clients) == 1 else None
        worker_pid = subprocess_record.get('pid')
        workers = [p for p in processes if p['role'] == 'worker' and p['pid'] == worker_pid
                   and us(status['spawn_before']) <= start_us(p) <= us(status.get('note_exit') or status.get('reaped'))]
        worker = workers[0] if len(workers) == 1 else None
        host = by_uniq.get(worker['parent_uniqueid']) if worker else None
        host_basis = 'worker_parent_uniqueid' if host else None
        if host is None and reply.get('pid') and not subprocess_record:
            # Pre-worker replies carry the host's getpid(); match a host alive in the interval.
            candidates = [p for p in processes if p['role'] == 'host' and p['pid'] == reply['pid']
                          and us(status['spawn_before']) <= start_us(p)]
            if len(candidates) == 1:
                host, host_basis = candidates[0], 'pre_worker_reply_pid'
        if host is None and client is not None:
            # No worker in the reply (e.g. xpc_timeout): launchd names the host spawned in this client's domain.
            pids = [pid for pid, entry in launchd.items() if entry['client_pid'] == client['pid']]
            candidates = [p for p in processes if p['role'] == 'host' and p['pid'] in pids
                          and start_us(p) >= start_us(client)]
            if len(candidates) == 1:
                host, host_basis = candidates[0], 'launchd_domain_of_client'
        if worker is None and host is not None and not subprocess_record:
            spawned_workers = [p for p in children.get(host['uniqueid'], []) if p['role'] == 'worker']
            worker = spawned_workers[0] if len(spawned_workers) == 1 else None
        validators = [p for p in children.get(host['uniqueid'], []) if p['role'] == 'validator'] if host else []
        reply_validator_pids = [ph['validator_subprocess']['pid'] for ph in reply.get('phases', [])
                                if ph.get('validator_subprocess')]
        host_children = children.get(host['uniqueid'], []) if host else []
        account = launchd.get(host['pid']) if host else None
        kill = next((m for m in (account or {}).get('messages', []) if m['message'].startswith('signaled service')), None)
        spawned = next((m for m in (account or {}).get('messages', []) if m['message'].startswith('Successfully spawned')), None)
        exited = next((m for m in (account or {}).get('messages', []) if m['message'].startswith('exited ')), None)
        invalidated = invalidations.get(host['pid'], []) if host else []

        controller_spawn = us(status['spawn_before'])
        controller_exit = us(status.get('note_exit'))
        client_exit = exit_us(client)
        host_exit = exit_us(host)
        worker_exit = exit_us(worker)
        validator_exits = [exit_us(v) for v in validators]
        last_child_exit = max([x for x in [worker_exit, *validator_exits] if x is not None], default=None)
        host_exec = us(host['xpcproxy']['exec_observed']) if host and (host.get('xpcproxy') or {}).get('exec_observed') else None
        spawn_offset = offset_us(status['spawn_before'])

        def span_us(ms):
            return None if ms is None else ms * 1000 - spawn_offset
        unit = {
            'label': status['label'], 'unit_dir': status['unit_dir'],
            'controller_exit_code': status.get('exit_code'), 'envelope_parse_error': parse_error,
            'normalized_outcome': reply.get('normalized_outcome'),
            'envelope_outcome': (envelope or {}).get('result', {}).get('normalized_outcome'),
            'runner_acquisition_refusals': len(data.get('runner_acquisition') or []),
            'reply_pid': reply.get('pid'), 'reply_worker_pid': worker_pid,
            'reply_validator_pids': reply_validator_pids,
            'worker_reaped_per_reply': subprocess_record.get('reaped'),
            'validators_reaped_per_reply': [ph['validator_subprocess'].get('reaped') for ph in reply.get('phases', [])
                                            if ph.get('validator_subprocess')],
            'identities': {
                'controller': controller and {k: controller[k] for k in ('pid', 'kernel_start_wall_us', 'uniqueid')},
                'client': client and {k: client[k] for k in ('pid', 'kernel_start_wall_us', 'uniqueid')},
                'clients_matched': len(clients),
                'host': host and {k: host[k] for k in ('pid', 'kernel_start_wall_us', 'uniqueid', 'parent_uniqueid',
                                                        'responsible_pid')},
                'host_basis': host_basis,
                'worker': worker and {k: worker[k] for k in ('pid', 'kernel_start_wall_us', 'uniqueid')},
                'workers_matched': len(workers),
                'validators': [{k: v[k] for k in ('pid', 'kernel_start_wall_us', 'uniqueid')} for v in validators],
                'host_children_roles': sorted(p['role'] for p in host_children),
            },
            'checks': {
                'validator_pids_agree': sorted(v['pid'] for v in validators) == sorted(reply_validator_pids),
                'launchd_domain_client_pid': account and account['client_pid'],
                'launchd_domain_matches_client': bool(account and client and account['client_pid'] == client['pid']),
                'host_responsible_pid_equals_controller_responsible_pid': bool(
                    host and controller and host['responsible_pid'] == controller['responsible_pid']),
                'launchd_kill_message': kill and kill['message'],
                'launchd_exit_reason': exited and re.sub(r'(PWRunner\[)\d+\]', r'\1<host>]',
                                                         re.sub(r', ran for \d+ms$', '', exited['message'])),
                'host_invalidation_client_pids': [i['client_pid'] for i in invalidated],
                'host_exit_basis': host and host['exit'] and host['exit']['basis'],
                'host_fork_notifications': len(host['fork_notifications']) if host else None,
                'host_children_exiting_after_host': [
                    {'role': c['role'], 'pid': c['pid'], 'exit_basis': c['exit'] and c['exit']['basis'],
                     'after_host_exit_ms': diff_ms(exit_us(c), exit_us(host))}
                    for c in host_children if exit_us(c) is None or exit_us(host) is None
                    or exit_us(c) > exit_us(host)] if host else None,
            },
            'events_mono_us': {
                'controller_spawn_harness': controller_spawn,
                'controller_kernel_start': status.get('kernel_start_wall_us') and
                status['kernel_start_wall_us'] - offset_us(status['spawn_after']),
                'client_kernel_start': start_us(client),
                'client_span_start_controller_ms': span_us(client_capture.get('started_at_unix_ms')),
                'host_kernel_start_xpcproxy': start_us(host),
                'launchd_log_spawned': spawned and spawned['mono_us'],
                'host_exec_observed': host_exec,
                'worker_kernel_start': start_us(worker),
                'worker_exit_observed': worker_exit,
                'validator_exit_observed': validator_exits,
                'client_exit_observed': client_exit,
                'client_span_end_controller_ms': span_us(client_capture.get('ended_at_unix_ms')),
                'host_invalidation_log': invalidated[0]['mono_us'] if invalidated else None,
                'launchd_log_kill': kill and kill['mono_us'],
                'host_exit_observed': host_exit,
                'controller_exit_observed': controller_exit,
                'controller_reaped': us(status.get('reaped')),
            },
            'intervals_ms': {
                'W_controller_spawn_to_exit': diff_ms(controller_exit, controller_spawn),
                'C_client_span_controller_clock': diff_ms(span_us(client_capture.get('ended_at_unix_ms')),
                                                          span_us(client_capture.get('started_at_unix_ms'))),
                'client_start_to_host_start': diff_ms(start_us(host), start_us(client)),
                'host_start_to_exec': diff_ms(host_exec, start_us(host)),
                'host_lifetime_kernel_start_to_exit': diff_ms(host_exit, start_us(host)),
                'client_lifetime_kernel_start_to_exit': diff_ms(client_exit, start_us(client)),
                'host_exec_to_worker_start': diff_ms(start_us(worker), host_exec),
                'host_invalidation_log_to_host_exit': diff_ms(host_exit, invalidated[0]['mono_us'] if invalidated else None),
                'last_child_exit_to_client_exit': diff_ms(client_exit, last_child_exit),
                'last_child_exit_to_host_exit': diff_ms(host_exit, last_child_exit),
                'client_exit_to_host_exit': diff_ms(host_exit, client_exit),
                'launchd_kill_log_to_host_exit': diff_ms(host_exit, kill and kill['mono_us']),
                'launchd_kill_log_to_exit_log': diff_ms(exited and exited['mono_us'], kill and kill['mono_us']),
                'host_exit_to_launchd_exit_log': diff_ms(exited and exited['mono_us'], host_exit),
                'client_exit_to_launchd_kill_log': diff_ms(kill and kill['mono_us'], client_exit),
                'controller_exit_to_host_exit': diff_ms(host_exit, controller_exit),
            },
        }
        units.append(unit)

    # Successive and paired relations: the next controller's start against earlier hosts.
    for previous, current in zip(units, units[1:]) if run['series'] != 'overlap' else ():
        current['intervals_ms']['previous_host_exit_to_controller_spawn'] = diff_ms(
            current['events_mono_us']['controller_spawn_harness'], previous['events_mono_us']['host_exit_observed'])
        current['intervals_ms']['previous_host_exit_to_client_start'] = diff_ms(
            current['events_mono_us']['client_kernel_start'], previous['events_mono_us']['host_exit_observed'])
    pairs = []
    if run['series'] == 'overlap':
        for a, b in zip(units[0::2], units[1::2]):
            def span(unit, start, end):
                ev = unit['events_mono_us']
                return ev[start], ev[end]
            def overlap(x, y):
                if None in (*x, *y):
                    return None
                return (min(x[1], y[1]) - max(x[0], y[0])) / 1000
            pairs.append({
                'labels': [a['label'], b['label']],
                'controller_overlap_ms': overlap(span(a, 'controller_spawn_harness', 'controller_exit_observed'),
                                                 span(b, 'controller_spawn_harness', 'controller_exit_observed')),
                'client_overlap_ms': overlap(span(a, 'client_kernel_start', 'client_exit_observed'),
                                             span(b, 'client_kernel_start', 'client_exit_observed')),
                'host_overlap_ms': overlap(span(a, 'host_kernel_start_xpcproxy', 'host_exit_observed'),
                                           span(b, 'host_kernel_start_xpcproxy', 'host_exit_observed')),
                'distinct_host_generations': (a['identities']['host'] or {}).get('uniqueid')
                != (b['identities']['host'] or {}).get('uniqueid')
                if a['identities']['host'] and b['identities']['host'] else None,
            })

    hosts = [u['identities']['host'] for u in units if u['identities']['host']]
    # launchd messages counted from the first controller spawn to one second after the last controller exit.
    window = [min(u['events_mono_us']['controller_spawn_harness'] for u in units),
              max(u['events_mono_us']['controller_exit_observed'] or 0 for u in units) + 1_000_000] if units else [0, 0]
    owned = [p for p in processes if not p['baseline'] and not p['role'].startswith('foreign')]
    role_counts = {}
    for p in owned:
        role_counts[p['role']] = role_counts.get(p['role'], 0) + 1
    exec_reassigned = [{'key': p['key'], 'history': p['exec_notifications']} for p in processes
                       if p.get('exec_notifications')]
    interval_names = sorted({k for u in units for k in u['intervals_ms']})
    summary = {
        'run_id': run_dir.name, 'series': run['series'], 'count': run['count'],
        'stop_reason': run['stop_reason'], 'attestation': attestation,
        'observer': run['observer'],
        'wall_minus_mono_drift_us': offset_us(run['end_clocks']) - offset_us(run['start_clocks']), 'launchd_log': {k: run.get('launchd_log', {}).get(k) for k in ('argv', 'exit', 'error')},
        'launchd_log_events': len(logs),
        'launchd_window_mono_us': window,
        'launchd_exit_reasons_in_window': {
            r: sum(1 for e in logs if e['mono_us'] is not None and window[0] <= e['mono_us'] <= window[1] and e['message'].startswith('exited ')
                   and re.sub(r'(PWRunner\[)\d+\]', r'\1<host>]', re.sub(r', ran for \d+ms$', '', e['message'])) == r)
            for r in {re.sub(r'(PWRunner\[)\d+\]', r'\1<host>]', re.sub(r', ran for \d+ms$', '', e['message']))
                      for e in logs if e['mono_us'] is not None and window[0] <= e['mono_us'] <= window[1] and e['message'].startswith('exited ')}},
        'launchd_spawn_messages_in_window': sum(e['message'].startswith('Successfully spawned PWRunner')
                                                for e in logs if e['mono_us'] is not None and window[0] <= e['mono_us'] <= window[1]),
        'launchd_kill_messages_in_window': {m: sum(e['message'] == m for e in logs if e['mono_us'] is not None and window[0] <= e['mono_us'] <= window[1])
                                            for m in {e['message'] for e in logs if e['message'].startswith('signaled service')}},
        'controllers': len(units),
        'outcomes': {str(o): sum(u['normalized_outcome'] == o for u in units) for o in {u['normalized_outcome'] for u in units}},
        'controller_exit_codes': {str(c): sum(u['controller_exit_code'] == c for u in units)
                                  for c in {u['controller_exit_code'] for u in units}},
        'acquisition_refusals': sum(u['runner_acquisition_refusals'] for u in units),
        'hosts_identified': len(hosts),
        'distinct_host_generations': len({(h['pid'], h['kernel_start_wall_us'], h['uniqueid']) for h in hosts}),
        'host_basis': {str(b): sum(u['identities']['host_basis'] == b for u in units)
                       for b in {u['identities']['host_basis'] for u in units}},
        'owned_process_roles': role_counts,
        'unassociated_owned_processes': sorted(
            {p['key'] for p in owned} - {x for u in units for x in (
                [f"{u['identities'][r]['pid']}:{u['identities'][r]['kernel_start_wall_us']}"
                 for r in ('controller', 'client', 'host', 'worker') if u['identities'][r]]
                + [f"{v['pid']}:{v['kernel_start_wall_us']}" for v in u['identities']['validators']])}),
        'still_alive_at_end': run['still_alive_at_end'],
        'exec_reassignments': exec_reassigned,
        'checks': {name: {str(v): sum(str(u['checks'][name]) == str(v) for u in units)
                          for v in {str(u['checks'][name]) for u in units}}
                   for name in units[0]['checks']} if units else {},
        'intervals_ms': {name: describe([u['intervals_ms'].get(name) for u in units]) for name in interval_names},
        'pairs': pairs,
    }
    summary['raw_sha256sums_sha256'] = sha256(run_dir / 'SHA256SUMS')
    record = {k: v for k, v in run.items() if k not in ('conditions_start', 'conditions_end')}
    for key in ('conditions_start', 'conditions_end'):
        record[key] = {'at': run[key]['at'], 'probes': [
            top_cpu(probe) if probe['argv'][0] == '/bin/ps' else probe for probe in run[key]['probes']]}
    args.out.mkdir(parents=True, exist_ok=True)
    for name, value in (('summary.json', summary), ('units.json', units), ('run-record.json', record)):
        (args.out / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    json.dump(summary, sys.stdout, indent=2, sort_keys=True)
    print()


if __name__ == '__main__':
    main()
