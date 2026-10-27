#!/usr/bin/env python3
"""Read one pre-touch run into per-unit observations and per-condition summaries.

Verifies SHA256SUMS first, then writes units.json, summary.json and a trimmed
run-record.json to --out. Each unit's condition (which pages were backed before
spawn and before application) and outcome (whether the post-apply store was
published and read back by the host) are decided from the recorded
observations, never from the unit's label. Kernel sandbox reports from the
unified log are attached to units by process id and time.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import statistics
import sys

KEPT_NAMES = ('Python', 'python', 'claude', 'codex', 'policy-witness', 'pretouch', 'harness_',
              'pw-probe-runner', 'launchd', 'logd')
STAGES = ['none', 'mapped', 'policy_read', 'pre_touched', 'compiled', 'wait_go1', 'applied', 'witnessed',
          'wait_go2', 'storing', 'stored', 'readback', 'second_map', 'anon_map', 'done', 'wait_go3']
DENY = re.compile(r'Sandbox: (?P<name>[^()]+)\((?P<pid>\d+)\) deny\((?P<count>\d+)\) (?P<what>.*)')
INCORE = 1
# BSD syscall numbers named in syscall-unix reports; sys/syscall.h of the SDK.
SYSCALLS = {'5': 'open', '117': 'getrusage', '197': 'mmap'}


def describe_report(what):
    parts = what.split(' ')
    if parts[0] == 'syscall-unix' and len(parts) > 1 and parts[1] in SYSCALLS:
        return f'syscall-unix {parts[1]} ({SYSCALLS[parts[1]]})'
    return what


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


def backed(snapshot, pages):
    if snapshot['rc'] != 0:
        return 'unavailable'
    flags = [snapshot['vec'][p] & INCORE for p in pages]
    return 'all' if all(flags) else 'none' if not any(flags) else 'mixed'


def fixture_unit(unit_dir, status):
    try:
        r = json.loads((unit_dir / 'result.json').read_text())
    except (OSError, ValueError) as error:
        return {'result_error': repr(error), 'reached': 'not_reached:no_result'}
    c, m, child = r['ctrl'], r['mincore'], r['child']
    pages = list(range(r['probe_page'], r['probe_page'] + r['probe_pages']))
    ticks_ns = r['timebase']['numer'] / r['timebase']['denom']
    policy, touch = r['policy_name'], r['touch']
    deny_policy = policy.startswith('deny')
    expect_before = touch in ('host', 'both', 'prod')
    expect_pre_apply = touch != 'none'
    condition = {
        'probe_backed_after_ftruncate': backed(m['after_map'], pages),
        'probe_backed_before_spawn': backed(m['before_spawn'], pages),
        'probe_backed_pre_apply': backed(m['pre_apply'], pages),
        'probe_backed_post_apply': backed(m['post_apply'], pages),
        'probe_backed_post_store': backed(m['post_store'], pages),
        'region_pages_backed_before_spawn': sum(1 for v in m['before_spawn']['vec'] if v & INCORE),
        'region_pages_backed_after_reap': sum(1 for v in m['after_reap']['vec'] if v & INCORE),
        'child_region_pages_resident': [r['region'][k].get('pages_resident') for k in
                                        ('child_pre_apply', 'child_post_apply', 'child_post_store')],
        'child_region_matches_mapping': all(
            r['region'][k].get('rc') == 0 and r['region'][k]['address'] == c['child_base']
            and r['region'][k]['size'] >= r['region_bytes'] and r['region'][k]['share_mode'] == r['region']['host_before_spawn'].get('share_mode')
            for k in ('child_pre_apply', 'child_post_apply', 'child_post_store')),
        'child_pre_touch_requested': c and r['child_pre_touch'],
        'expected_backed_before_spawn': 'all' if expect_before else 'none',
        'expected_backed_pre_apply': 'all' if expect_pre_apply else 'none',
    }
    condition['established'] = (condition['probe_backed_before_spawn'] == condition['expected_backed_before_spawn']
                                and condition['probe_backed_pre_apply'] == condition['expected_backed_pre_apply']
                                and condition['probe_backed_post_apply'] == condition['expected_backed_pre_apply'])
    witness_ok = ((c['witness_open_rc'] == -1 and c['witness_open_errno'] == 1) if deny_policy
                  else c['witness_open_rc'] >= 0)
    application = {
        'apply_called': c['apply_called'], 'apply_rc': c['apply_rc'], 'apply_errno': c['apply_errno'],
        'compile_ok': c['compile_ok'], 'compile_error': c['compile_error'] or None,
        'witness_open_rc': c['witness_open_rc'], 'witness_open_errno': c['witness_open_errno'],
        'witness_as_expected': witness_ok,
        'applied_as_intended': (c['apply_called'] == 1 and c['apply_rc'] == 0) if policy != 'noapply' else c['apply_called'] == 0,
    }
    rusage_ok = [rc == 0 for rc in c['rusage_rc']]
    faults = {
        'pre_apply_sample': c['minflt'][0] if rusage_ok[0] else None,
        'at_exit': child['rusage']['minflt'],
        'after_pre_apply_sample': child['rusage']['minflt'] - c['minflt'][0] if rusage_ok[0] else None,
        'post_apply_getrusage': {'rc': c['rusage_rc'][1], 'errno': c['rusage_errno'][1]},
        'store_interval': c['minflt'][2] - c['minflt'][1] if rusage_ok[1] and rusage_ok[2] else None,
    }
    t = c['t']

    def rel(stage_name):
        v = t[STAGES.index(stage_name)]
        return None if v == 0 else (v - r['host_times']['spawn_start']) * ticks_ns / 1e6
    store = {
        'stage': STAGES[c['stage']] if c['stage'] < len(STAGES) else c['stage'],
        'pages_stored': c['pages_stored'], 'pages_requested': r['probe_pages'],
        'child_readback_ok': c['readback_ok'], 'host_read_matches': r['probe']['all_match'],
        'store_ns': (t[STAGES.index('stored')] - t[STAGES.index('storing')]) * ticks_ns
        if t[STAGES.index('stored')] and t[STAGES.index('storing')] else None,
        'host_values': r['probe']['values'] if r['probe_pages'] == 1 else {'n': len(r['probe']['values'])},
    }
    controls = {
        'second_map': {'rc': c['second_map_rc'], 'errno': c['second_map_errno'], 'store_ok': c['second_map_store_ok'],
                       'host_marker_match': r['second_marker']['match']},
        'anon_map': {'rc': c['anon_map_rc'], 'errno': c['anon_map_errno'], 'store_ok': c['anon_store_ok']},
    }
    disposition = {'exit_code': child['exit_code'], 'term_signal': child['term_signal'], 'killed': child['killed'],
                   'exit_code_intent': c['exit_code_intent'], 'waits': {k: v['state'] for k, v in r['waits'].items()}}
    completed = child['exit_code'] == 0 and not child['killed'] and all(v['state'] == 'reached' for v in r['waits'].values())
    if (completed and c['stage'] >= STAGES.index('stored') and c['pages_stored'] == r['probe_pages']
            and r['probe']['all_match'] and c['readback_ok']):
        reached = 'published'
    elif c['stage'] >= STAGES.index('stored') and not r['probe']['all_match']:
        reached = 'stored_unreadable'
    elif child['term_signal'] is not None and c['stage'] == STAGES.index('storing'):
        reached = 'died_during_store'
    elif (child['term_signal'] is not None or child['exit_code'] not in (0, None)) and c['stage'] < STAGES.index('storing'):
        reached = 'ended_before_store'
    else:
        reached = 'not_reached'
    return {'policy': policy, 'touch': touch, 'probe_pages': r['probe_pages'], 'probe_page': r['probe_page'],
            'child_pid': r['child_pid'], 'policy_text': r['policy_text'],
            'condition': condition, 'application': application, 'faults': faults, 'store': store,
            'controls': controls, 'disposition': disposition,
            'timeline_ms_from_spawn': {name: rel(name) for name in ('mapped', 'compiled', 'applied', 'storing', 'stored', 'done')},
            'reached': reached}


def shipped_unit(unit_dir, status):
    try:
        h = json.loads((unit_dir / 'stdout.txt').read_text())
    except (OSError, ValueError) as error:
        return {'harness_error': repr(error), 'reached': 'not_reached:no_envelope'}
    slots = h.get('slots') or []
    all_completed = bool(slots) and all(s.get('completed') == 1 or s.get('completed') is True for s in slots)
    record = {'variant': status['variant'], 'scenario': h.get('scenario'), 'worker_pid': h.get('worker_pid'),
              'ready_byte_received': h.get('ready_byte_received'), 'applied': h.get('applied'), 'apply_rc': h.get('apply_rc'),
              'done': h.get('done'), 'sent_sigkill': h.get('sent_sigkill'), 'exit_code': h.get('exit_code'),
              'term_signal': h.get('term_signal'), 'slot_count': len(slots), 'all_slots_completed': all_completed,
              'slot0': {k: slots[0].get(k) for k in ('completed', 'rc', 'errno', 'observed_path')} if slots else None,
              'harness_exit': status.get('exit')}
    if (record['applied'] in (1, True) and record['done'] in (1, True) and all_completed and record['exit_code'] == 0
            and not record['sent_sigkill']):
        record['reached'] = 'published'
    else:
        record['reached'] = 'not_reached'
    return record


def deny_reports(run_dir):
    path = run_dir / 'deny-log.ndjson'
    if not path.is_file():
        return None
    reports = []
    for line in path.read_text().splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        match = DENY.search(event.get('eventMessage', ''))
        if not match:
            continue
        reports.append({'timestamp': event.get('timestamp'), 'name': match['name'].strip(), 'pid': int(match['pid']),
                        'count': int(match['count']), 'what': match['what'].strip(),
                        'duplicate_summary': 'duplicate reports' in event.get('eventMessage', '')})
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    attestation = verify(args.run_dir)
    run = json.loads((args.run_dir / 'run.json').read_text())
    reports = deny_reports(args.run_dir)
    by_pid = {}
    for report in reports or []:
        by_pid.setdefault(report['pid'], []).append(report)
    units = []
    for status_path in sorted((args.run_dir / 'units').glob('*/status.json')):
        status = json.loads(status_path.read_text())
        body = (fixture_unit if status['kind'] == 'fixture' else shipped_unit)(status_path.parent, status)
        pid = body.get('child_pid') if status['kind'] == 'fixture' else body.get('worker_pid')
        body['sandbox_reports'] = [{k: v for k, v in rep.items() if k != 'pid'} for rep in by_pid.get(pid, [])]
        units.append({'sequence': status['sequence'], 'kind': status['kind'], 'case': status['case'],
                      'state': status['state'], 'harness_exit': status.get('exit'),
                      'processes_after_unit': status['processes_after_unit'], **body})
    conditions = {}
    for u in units:
        if u['kind'] == 'fixture' and 'condition' in u:
            key = f"fixture:{u['policy']}:{u['touch']}:p{u['probe_pages']}"
            e = conditions.setdefault(key, {'n': 0, 'sequences': [], 'reached': Counter(), 'established': 0,
                                            'applied_as_intended': 0, 'witness_as_expected': 0,
                                            'faults_after_pre_apply_sample': [], 'store_interval_faults': [],
                                            'store_ns': [], 'second_map': Counter(), 'anon_map': Counter(),
                                            'post_apply_getrusage': Counter(), 'exit_codes': Counter(),
                                            'sandbox_report_ops': Counter(), 'backed_before_spawn': Counter(),
                                            'backed_pre_apply': Counter(), 'backed_post_store': Counter()})
            e['n'] += 1
            e['sequences'].append(u['sequence'])
            e['reached'][u['reached']] += 1
            e['established'] += bool(u['condition']['established'])
            e['applied_as_intended'] += bool(u['application']['applied_as_intended'])
            e['witness_as_expected'] += bool(u['application']['witness_as_expected'])
            e['faults_after_pre_apply_sample'].append(u['faults']['after_pre_apply_sample'])
            e['store_interval_faults'].append(u['faults']['store_interval'])
            e['store_ns'].append(u['store']['store_ns'])
            sm, am = u['controls']['second_map'], u['controls']['anon_map']
            e['second_map'][f"rc={sm['rc']} errno={sm['errno']} marker={sm['host_marker_match']}"] += 1
            e['anon_map'][f"rc={am['rc']} errno={am['errno']} store_ok={am['store_ok']}"] += 1
            g = u['faults']['post_apply_getrusage']
            e['post_apply_getrusage'][f"rc={g['rc']} errno={g['errno']}"] += 1
            e['exit_codes'][str(u['disposition']['exit_code'])] += 1
            e['backed_before_spawn'][u['condition']['probe_backed_before_spawn']] += 1
            e['backed_pre_apply'][u['condition']['probe_backed_pre_apply']] += 1
            e['backed_post_store'][u['condition']['probe_backed_post_store']] += 1
            for rep in u['sandbox_reports']:
                if not rep['duplicate_summary']:
                    e['sandbox_report_ops'][describe_report(rep['what'])] += rep['count']
        elif u['kind'] == 'shipped':
            key = f"shipped:{u.get('variant')}:{u.get('scenario')}"
            e = conditions.setdefault(key, {'n': 0, 'sequences': [], 'reached': Counter(), 'exit_codes': Counter(),
                                            'slot0': Counter(), 'sandbox_report_ops': Counter()})
            e['n'] += 1
            e['sequences'].append(u['sequence'])
            e['reached'][u['reached']] += 1
            e['exit_codes'][str(u.get('exit_code'))] += 1
            if u.get('slot0'):
                e['slot0'][f"completed={u['slot0']['completed']} rc={u['slot0']['rc']} errno={u['slot0']['errno']}"] += 1
            for rep in u['sandbox_reports']:
                if not rep['duplicate_summary']:
                    e['sandbox_report_ops'][describe_report(rep['what'])] += rep['count']
    for e in conditions.values():
        for k in ('faults_after_pre_apply_sample', 'store_interval_faults', 'store_ns'):
            if k in e:
                e[k] = describe(e[k])
        for k, v in list(e.items()):
            if isinstance(v, Counter):
                e[k] = dict(v)
    record = {k: v for k, v in run.items() if k not in ('conditions_start', 'conditions_end')}
    for key in ('conditions_start', 'conditions_end'):
        record[key] = {'at': run[key]['at'], 'probes': [top_cpu(p) if p['argv'][0] == '/bin/ps' else p
                                                        for p in run[key]['probes']]}
    summary = {'run_id': args.run_dir.name, 'stop_reason': run['stop_reason'], 'attestation': attestation,
               'raw_sha256sums_sha256': sha256(args.run_dir / 'SHA256SUMS'),
               'units_run': run['units_run'], 'never_started': run['never_started'],
               'order': [f"{u['sequence']}:{u['case']}" for u in units],
               'past_deadline': [u['sequence'] for u in units if u['state'] != 'exited'],
               'survivors': [u['sequence'] for u in units if u['processes_after_unit']],
               'processes_after_run': run['processes_after'],
               'deny_log': {'collected': reports is not None, 'exit': (run.get('deny_log') or {}).get('exit'),
                            'reports': len(reports or []),
                            'unattributed': [r for r in (reports or []) if r['pid'] not in
                                             {u.get('child_pid') or u.get('worker_pid') for u in units}]},
               'fixture_units_not_established': [u['sequence'] for u in units
                                                 if u['kind'] == 'fixture' and not u.get('condition', {}).get('established')],
               'fixture_units_not_published': [u['sequence'] for u in units
                                               if u['kind'] == 'fixture' and u['reached'] != 'published'],
               'shipped_units_not_published': [u['sequence'] for u in units
                                               if u['kind'] == 'shipped' and u['reached'] != 'published'],
               'conditions': conditions}
    args.out.mkdir(parents=True, exist_ok=True)
    for name, value in (('units.json', units), ('summary.json', summary), ('run-record.json', record)):
        (args.out / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    json.dump(summary, sys.stdout, indent=2, sort_keys=True)
    print()


if __name__ == '__main__':
    main()
