"""First-use screen only: direct progress/lifecycle evidence, no deployment credit."""
import copy
import json
from pathlib import Path
import sys

POLICIES = ('unapplied', 'allow_default', 'deny_default', 'file_read')


def check(rows):
    failures, counts, generations, observations = [], {}, set(), []
    primitives = {r.get('primitive') for r in rows if isinstance(r, dict)}
    if len(primitives) != 1 or not primitives <= {'wfe', 'wfet'}:
        failures.append('mixed/missing primitive')
    for index, r in enumerate(rows):
        label = f'trial {index}'
        def require(value, reason):
            if not value:
                failures.append(f'{label}: {reason}')
        try:
            require(r['version'] == 1 and r['policy'] in POLICIES, 'configuration')
            counts[r['policy']] = counts.get(r['policy'], 0) + 1
            require(r['ready'] == r['entered'] == r['first_returned'] == r['finished'] == r['reaped'] == 1,
                    'missing instruction/progress/lifecycle')
            require(r['rescued'] == r['supervisor_interrupted'] == r['term_signal'] == r['exit_code'] == 0,
                    'rescue/interruption/native ending')
            require(r['finished_at_after'] == 0, 'CPU endpoint outside active screen')
            require(r['setup_rc'] == 0 and r['numer'] > 0 and r['denom'] > 0 and r['frequency'] > 0, 'clock setup')
            require((r['unapplied'] == 1 and r['compiled'] == 0) if r['policy'] == 'unapplied'
                    else (r['unapplied'] == 0 and r['compiled'] == 1 and r['apply_rc'] == 0), 'application')
            scale = r['numer'] / r['denom']
            require(500_000_000 <= (r['cutoff']-r['start'])*scale < 500_000_000+scale, 'cutoff conversion')
            require(r['cutoff'] <= r['end'] and (r['end']-r['start'])*scale <= 550_000_000, 'autonomous cutoff')
            require(r['passes'] >= 64 and len(r['samples']) == 64, 'incomplete waits')
            require(r['local_timeout_ns'] == 100_000, 'timed configuration')
            if r['primitive'] == 'wfet':
                require(r['feature_rc'] == 0 and r['feature'] == 1 and r['feature_size'] == 4, 'feature gate')
            a, b = r['before'], r['after']
            for o in (a, b):
                require(o['identity_rc'] == o['identity_size'] and o['identity_size'] > 0
                        and o['cpu_rc'] == 0 and o['pid'] == r['pid']
                        and o['ppid'] == r['supervisor_pid'] and o['start_sec'] > 0, 'live owned generation')
                require(o['begin'] <= o['end'], 'observation order')
            generation = lambda o: tuple(o[k] for k in ('pid', 'ppid', 'start_sec', 'start_usec'))
            require(generation(a) == generation(b) and generation(a) not in generations, 'changed/reused generation')
            generations.add(generation(a))
            require(a['end'] <= r['silent_begin'] <= r['start'] < r['silent_end'] <= b['begin'] <= b['end'] <= r['end'], 'silent interval order')
            require((r['silent_end']-r['silent_begin'])*scale >= 150_000_000, 'short silent interval')
            require(b['user_ticks'] >= a['user_ticks'] and b['system_ticks'] >= a['system_ticks'], 'CPU counter regression')
            last = r['start']
            for sample in r['samples']:
                require(last <= sample['begin'] <= sample['end'] <= r['end'], 'instruction bracket order')
                require(sample['end']-sample['begin'] <= r['max_span'], 'maximum below retained bracket')
                if r['primitive'] == 'wfet':
                    ticks = (r['frequency'] * 100_000 + 999_999_999) // 1_000_000_000
                    require(sample['deadline']-sample['counter'] == ticks
                            and 0 <= sample['counter'] <= sample['deadline'] < 2**64, 'virtual timeout conversion')
                else:
                    require(sample['counter'] == sample['deadline'] == 0, 'untimed counter payload')
                last = sample['end']
            observations.append(dict(policy=r['policy'], pid=r['pid'], passes=r['passes'],
                                     first_span_ns=(r['samples'][0]['end']-r['samples'][0]['begin'])*scale,
                                     max_span_ns=r['max_span']*scale,
                                     cpu_ns=((b['user_ticks']-a['user_ticks'])+(b['system_ticks']-a['system_ticks']))*scale,
                                     elapsed_lower_ns=(b['begin']-a['end'])*scale))
        except (KeyError, TypeError, ValueError, ZeroDivisionError, IndexError) as exc:
            failures.append(f'{label}: malformed evidence: {exc}')
    if counts != {p: 3 for p in POLICIES}:
        failures.append('missing/excess profile repetitions')
    return dict(version=1, screen_passed=not failures, failures=failures, observations=observations,
                scope='First explicit instruction, same-generation silent interval and own cutoff only; no integrated protocol, deployment, benefit, migration or sleep/resume credit.')


def constructed(primitive):
    rows = []
    for policy in POLICIES:
        for _ in range(3):
            pid = 100+len(rows)
            a = dict(begin=0,end=10,identity_rc=136,identity_size=136,identity_errno=0,cpu_rc=0,cpu_errno=0,
                     pid=pid,ppid=99,start_sec=1000,start_usec=pid,user_ticks=0,system_ticks=0)
            b = dict(a,begin=150_000_030,end=150_000_040,user_ticks=100_000_000)
            samples = [dict(begin=30+i*1000,end=1030+i*1000,counter=0 if primitive=='wfe' else 1000+i*1000,
                            deadline=0 if primitive=='wfe' else 101000+i*1000) for i in range(64)]
            rows.append(dict(version=1,primitive=primitive,policy=policy,pid=pid,supervisor_pid=99,
                             feature=1,feature_rc=0,feature_errno=0,feature_size=4,ready=1,entered=1,
                             first_returned=1,finished=1,finished_at_after=0,rescued=0,reaped=1,exit_code=0,
                             term_signal=0,supervisor_interrupted=0,setup_rc=0,compiled=int(policy!='unapplied'),
                             apply_rc=0,apply_errno=0,unapplied=int(policy=='unapplied'),numer=1,denom=1,
                             frequency=1_000_000_000,start=30,end=500_000_030,cutoff=500_000_030,
                             passes=500_000,max_span=1000,silent_begin=20,silent_end=150_000_020,
                             local_timeout_ns=100_000,before=a,after=b,samples=samples))
    return rows


def controls(out):
    rejected = []
    edits = {
        'application_missing': lambda r: r.update(compiled=0,unapplied=0),
        'instruction_unentered': lambda r: r.update(entered=0),
        'never_returned': lambda r: r.update(first_returned=0),
        'missing_progress': lambda r: r.update(finished=0),
        'watchdog_rescue': lambda r: r.update(rescued=1),
        'signal': lambda r: r.update(term_signal=4),
        'unreaped': lambda r: r.update(reaped=0),
        'wrong_generation': lambda r: r['after'].update(start_sec=123),
        'wrong_parent': lambda r: r['after'].update(ppid=123),
        'missing_native_counter': lambda r: r['after'].update(cpu_rc=-1),
        'counter_regression': lambda r: r['before'].update(system_ticks=1),
        'short_silence': lambda r: r.update(silent_end=1000),
        'premature_cutoff': lambda r: r.update(end=499_000_000),
        'unbounded_cutoff': lambda r: r.update(end=551_000_030),
        'wrong_cutoff_clock': lambda r: r.update(cutoff=40),
        'missing_samples': lambda r: r['samples'].pop(),
        'inverted_bracket': lambda r: r['samples'][0].update(end=1),
        'combined': lambda r: r.update(reaped=0,entered=0,finished=0,rescued=1),
    }
    for primitive in ('wfe','wfet'):
        good = constructed(primitive); assert check(good)['screen_passed']
        for name, edit in edits.items():
            rows = copy.deepcopy(good); edit(rows[3]); result = check(rows)
            assert not result['screen_passed'], name
            if name == 'combined': assert len(result['failures']) >= 2
            rejected.append(f'{primitive}/{name}')
        for rows in (good[:-1], good+[good[0]]): assert not check(rows)['screen_passed']
    for key, value in (('feature',0),('feature_size',8),('frequency',24_000_000)):
        rows = constructed('wfet'); rows[0][key]=value; assert not check(rows)['screen_passed']; rejected.append(key)
    rows = constructed('wfet'); rows[0]['samples'][0]['deadline']=2**64; assert not check(rows)['screen_passed']; rejected.append('overflow')
    Path(out,'controls.json').write_text(json.dumps(dict(accepted=['wfe','wfet'],rejected=rejected,scope='constructed only'),indent=2)+'\n')
    print(f'{len(rejected)} independent corrupt ARM screen receipts rejected')


if __name__ == '__main__':
    if sys.argv[1] == '--controls':
        controls(sys.argv[2])
    else:
        p = Path(sys.argv[1]); result = check([json.loads(s) for s in p.read_text().splitlines()])
        p.with_name('screen.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2)); sys.exit(0 if result['screen_passed'] else 1)
