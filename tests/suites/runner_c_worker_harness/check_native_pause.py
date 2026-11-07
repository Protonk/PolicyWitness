"""Independent applicability oracle. Logs are supplemental, never an absence proof."""
import copy
import json
import sys
from pathlib import Path

POLICIES = {"allow_default", "deny_default", "v2_original", "unapplied"}


def check(rows, log_status):
    failures, intervals = [], []
    expected = {(p, m): 3 for p in POLICIES for m in ("ordinary", "interrupted")}
    actual = {}
    generations = set()
    primitives = {r['primitive'] for r in rows}
    if len(primitives) != 1:
        failures.append('mixed or missing primitives')
    for r in rows:
        label = f"{r['policy']}/{r['mode']}/pid={r['pid']}"
        def require(value, reason):
            if not value:
                failures.append(f"{label}: {reason}")
        require(r['version'] == 1 and r['primitive'] in {'nanosleep', 'mach_wait_until'} and r['requested_ns'] == 1_000_000,
                'configuration')
        key = r['policy'], r['mode']
        actual[key] = actual.get(key, 0) + 1
        require(r['ready'] == 1 and r['finished'] == 1 and r['reaped'] and not r['timed_out']
                and r['exit_code'] == 0 and r['term_signal'] == 0, 'lifecycle')
        require(r['setup_rc'] == 0 and r['numer'] > 0 and r['denom'] > 0 and r['handler_rc'] == 0, 'setup')
        require((r['unapplied'] == 1 and r['compile_ok'] == 0) if r['policy'] == 'unapplied'
                else (r['unapplied'] == 0 and r['compile_ok'] == 1 and r['apply_rc'] == 0), 'application')
        a, b = r['before'], r['after']
        for o in (a, b):
            require(o['identity_rc'] == o['identity_size'] and o['cpu_rc'] == 0
                    and o['pid'] == r['pid'] and o['start_sec'] > 0, 'live observation')
            require(o['begin_ticks'] <= o['end_ticks'], 'observation time')
        generation = lambda o: (o['pid'], o['ppid'], o['start_sec'], o['start_usec'])
        require(generation(a) == generation(b), 'generation changed')
        require(generation(a) not in generations, 'generation reused')
        generations.add(generation(a))
        require(a['end_ticks'] <= b['begin_ticks'], 'interval order')
        require(b['user_ticks'] >= a['user_ticks'] and b['system_ticks'] >= a['system_ticks'],
                'CPU counter regression')
        samples = r['samples']
        require(len(samples) == 64, 'missing pauses')
        require(bool(samples) and samples[0]['rc'] == 0, 'first pause failed')
        interrupted = 0
        last = a['end_ticks']
        for s in samples:
            require(last <= s['begin_ticks'] <= s['end_ticks'] <= b['begin_ticks'], 'pause time')
            last = s['end_ticks']
            is_interrupted = (s['rc'] == -1 and s['errno'] == 4) if r['primitive'] == 'nanosleep' else s['rc'] == 14
            require(s['rc'] == 0 or is_interrupted, 'native pause failure')
            if r['primitive'] == 'mach_wait_until':
                require(s['errno'] == 0, 'Mach result has POSIX errno')
            elapsed = (s['end_ticks'] - s['begin_ticks']) * r['numer'] / max(1, r['denom'])
            if s['rc'] == 0:
                require(elapsed >= 1_000_000, 'no demonstrated full pause')
            interrupted += is_interrupted
        if r['mode'] == 'interrupted':
            require(interrupted > 0 and r['signals'] > 0 and r['signal_calls'] > 0
                    and r['signal_errors'] == 0, 'interruption missing')
        else:
            require(interrupted == 0 and r['signals'] == 0 and r['signal_calls'] == 0, 'unexpected interruption')
        scale = r['numer'] / max(1, r['denom'])
        cpu = ((b['user_ticks'] - a['user_ticks']) + (b['system_ticks'] - a['system_ticks'])) * scale
        lower = (b['begin_ticks'] - a['end_ticks']) * scale
        upper = (b['end_ticks'] - a['begin_ticks']) * scale
        require(cpu >= 0 and lower > 0, 'CPU/elapsed interval')
        # This demonstrates idleness only in the uninterrupted native control;
        # it is not the plan's integrated 90% matched-worker acceptance test.
        if r['mode'] == 'ordinary':
            require(cpu + 2_000_000 < lower / 2, 'no demonstrated idle interval')
        intervals.append({'label': label, 'cpu_ns': cpu, 'elapsed_lower_ns': lower,
                          'elapsed_upper_ns': upper, 'interruptions': interrupted})
    if actual != expected:
        failures.append(f'configuration repetitions: {actual}')
    return {'version': 1, 'qualified': not failures, 'failures': failures, 'intervals': intervals,
            'log_status': log_status, 'log_role': 'supplemental; no absence or causal attribution',
            'scope': 'recorded policies, equipment and explicit first call only; no integrated wait or sleep/wake claim'}


def log_account(rows, known, status, lines):
    events = []
    for line in lines.splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if 'eventMessage' in item:
            events.append(item)
    matched = []
    for r in [*rows, known]:
        for e in events:
            if f"native-pause({r['pid']})" in e['eventMessage']:
                matched.append({'pid': r['pid'], 'mode': r['mode'], 'policy': r['policy'],
                                'message': e['eventMessage'], 'timestamp': e.get('timestamp'),
                                'mach_timestamp': e.get('machTimestamp'),
                                'inside_pause': any(s['begin_ticks'] <= e.get('machTimestamp', -1) <= s['end_ticks']
                                                    for s in r['samples'])})
    positive = any(e['pid'] == known['pid'] for e in matched)
    return {'status': status, 'collection': 'available' if status == 0 else 'unavailable',
            'matched_events': matched,
            'known_denial_native_observed': known['denial_rc'] == -1 and known['denial_errno'] in (1, 13),
            'known_denial_log': ('observed' if positive else 'not_observed') if status == 0 else 'unavailable',
            'limit': 'A matching event establishes only that event; silence or unavailable collection establishes no absence.'}


def controls():
    # Independent synthetic complete evidence, not derived from a live result.
    rows = []
    for p in sorted(POLICIES):
        for mode in ('ordinary', 'interrupted'):
            for repeat in range(3):
                pid = 100 + len(rows)
                a = dict(begin_ticks=0, end_ticks=10, identity_rc=136, identity_size=136,
                         identity_errno=0, cpu_rc=0, cpu_errno=0, pid=pid, ppid=99,
                         start_sec=1000, start_usec=pid, user_ticks=0, system_ticks=0)
                b = dict(a, begin_ticks=70_000_000, end_ticks=70_000_010, user_ticks=100_000)
                samples = [dict(begin_ticks=1000+i*1_000_000, end_ticks=1000+(i+1)*1_000_000,
                                rc=-1 if mode == 'interrupted' and i == 1 else 0,
                                errno=4 if mode == 'interrupted' and i == 1 else 60) for i in range(64)]
                rows.append(dict(version=1, primitive='nanosleep', requested_ns=1_000_000,
                                 policy=p, mode=mode, pid=pid, ready=1, finished=1, reaped=True,
                                 timed_out=0, exit_code=0, term_signal=0, setup_rc=0, numer=1, denom=1,
                                 handler_rc=0, unapplied=int(p == 'unapplied'), compile_ok=int(p != 'unapplied'),
                                 apply_rc=0, before=a, after=b, samples=samples,
                                 signals=int(mode == 'interrupted'), signal_calls=int(mode == 'interrupted'), signal_errors=0))
    for status in (0, 77):
        assert check(rows, status)['qualified'], status
    mach_rows = copy.deepcopy(rows)
    for r in mach_rows:
        r['primitive'] = 'mach_wait_until'
        for s in r['samples']:
            if s['rc'] == -1:
                s['rc'] = 14
            s['errno'] = 0
    assert check(mach_rows, 77)['qualified']
    mutations = {
        'native pause failure': lambda r: r['samples'][0].update(rc=-1, errno=1),
        'lifecycle': lambda r: r.update(reaped=False),
        'generation changed': lambda r: r['after'].update(start_usec=999),
        'application': lambda r: r.update(apply_rc=-1),
        'no demonstrated full pause': lambda r: r['samples'][0].update(end_ticks=1001),
        'live observation': lambda r: r['before'].update(identity_rc=0),
        'no demonstrated idle interval': lambda r: r['after'].update(user_ticks=69_000_000),
        'missing pauses': lambda r: r['samples'].pop(),
        'CPU counter regression': lambda r: r['after'].update(system_ticks=-1),
    }
    for diagnostic, mutate in mutations.items():
        changed = copy.deepcopy(rows); mutate(changed[0])
        result = check(changed, 77)
        assert not result['qualified'] and any(diagnostic in f for f in result['failures']), result
    changed = copy.deepcopy(rows)
    changed[0]['samples'][0].update(rc=-1, errno=1)
    changed[0]['reaped'] = False
    result = check(changed, 77)
    assert any('native pause failure' in f for f in result['failures'])
    assert any('lifecycle' in f for f in result['failures'])
    mach_rows[0]['samples'][0].update(rc=53)
    assert any('native pause failure' in f for f in check(mach_rows, 77)['failures'])
    changed = copy.deepcopy(rows); changed[0]['primitive'] = 'mach_wait_until'
    assert 'mixed or missing primitives' in check(changed, 0)['failures']
    changed = copy.deepcopy(rows); changed[3]['signals'] = 0
    assert any('interruption missing' in f for f in check(changed, 77)['failures'])
    known = dict(rows[0], pid=999, mode='known_denial', denial_rc=-1, denial_errno=1, samples=[])
    assert log_account(rows, known, 77, '')['known_denial_log'] == 'unavailable'
    assert log_account(rows, known, 0, '')['known_denial_log'] == 'not_observed'
    event = json.dumps({'eventMessage': 'Sandbox: native-pause(999) deny(1) file-read-data /etc/hosts'})
    assert log_account(rows, known, 0, event)['known_denial_log'] == 'observed'
    print('ok: unavailable logs permit complete evidence and preserve required and combined failures')


if __name__ == '__main__':
    if sys.argv[1:] == ['--controls']:
        controls()
    else:
        path = Path(sys.argv[1])
        rows = [json.loads(s) for s in path.read_text().splitlines()]
        status = int(Path(sys.argv[2]).read_text())
        result = check(rows, status)
        result['logs'] = log_account(rows, json.loads(path.with_name('known-denial.json').read_text()),
                                     status, path.with_name('deny-log.ndjson').read_text())
        path.with_name('summary.json').write_text(json.dumps(result, indent=2) + '\n')
        for failure in result['failures']:
            print(failure)
        print(f"qualified={result['qualified']}; log status={result['log_status']}")
        sys.exit(0 if result['qualified'] else 1)
