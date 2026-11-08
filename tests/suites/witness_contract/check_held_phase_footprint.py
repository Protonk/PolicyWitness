"""Bounded Waiting measurements with external effects, matched counters and controls."""
import json
import math
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tests/lib'))
from footprint_observer import FootprintObserver, generation, require_sample, validate_batch
from footprint_workloads import HeldWorkload, ActorHostFixture, check_snapshot, check_held_binding


def save(path,value):
    Path(path).write_text(json.dumps(value,indent=2)+'\n')


def cpu(sample): return sample['user_ns']+sample['system_ns']


def check_wait_measurement(row):
    """Mechanism-neutral evidence; worker idleness is neither required nor refused."""
    assert set(row)=={'version','name','repetition','multiplier','quantum_ns','hold_min_ns','requested_ns','ready','effects','before','after','clock_before','clock_after','roles','snapshot','release','actual_min_ns','deltas_ns','observer','conditions','held_generations'}
    assert row['version']==1 and row['repetition'] in range(3) and row['multiplier'] in (1,3)
    q=row['quantum_ns']; minimum=max(1_000_000_000,100*q)
    assert q>=10_000_000 and row['hold_min_ns']==minimum
    assert row['requested_ns']>=minimum*row['multiplier']
    assert row['ready']['event']=='ready' and row['ready']['target_pid']>0
    assert len(row['effects'])>=3
    for effect in row['effects']:
        assert set(effect)=={'gate','target_unchanged','marker_unchanged','exec_connected','clock'}
        assert effect['gate']['event']=='held' and effect['gate']['closed'] is False
        assert effect['target_unchanged'] is True and effect['marker_unchanged'] is True and effect['exec_connected'] is False
    before,after=row['before'],row['after']; pids=[s['pid'] for s in before['samples']]
    validate_batch(before,pids); validate_batch(after,pids)
    check_held_binding(row['snapshot'],row['ready'],row['held_generations'],before)
    assert generation(before['samples'][-5])==generation(row['held_generations']['host'])
    assert generation(before['samples'][-4])==generation(row['held_generations']['validator'])
    assert row['ready']['observer_ack_clock']['end_ns']<=before['begin_ns']
    for effect in row['effects']:
        assert before['end_ns']<=effect['clock']['begin_ns']<=effect['clock']['end_ns']<=after['begin_ns']
    assert len(row['roles'])==len(pids) and len(set(row['roles']))==len(pids)
    assert row['roles'][-3:]==['busy_control','sleep_control','observer']
    assert row['roles'][-5:-3]==['host','validator']
    assert all(role.startswith('worker:') for role in row['roles'][:-5])
    assert row['ready']['target_pid'] in pids[:-5]
    for batch in (before,after): assert batch['end_ns']-batch['begin_ns']<=q, 'endpoint sampling skew'
    actual=after['begin_ns']-before['end_ns']
    assert actual==row['actual_min_ns'] and actual>=minimum*row['multiplier'], 'short hold'
    assert row['release']['before']['begin_ns']>=after['end_ns'], 'early release'
    deltas=[]
    for a,b in zip(before['samples'],after['samples']):
        require_sample(a); require_sample(b,generation(a))
        assert generation(a)['pid']==a['pid'] and generation(b)['pid']==b['pid']
        assert b['user_ns']>=a['user_ns'] and b['system_ns']>=a['system_ns']
        deltas.append(cpu(b)-cpu(a))
    assert row['deltas_ns']==deltas
    assert deltas[-3]>deltas[-2], 'busy CPU must exceed sleeping control'
    assert row['observer']==dict(pid=pids[-1],delta_ns=deltas[-1],cadence_ns=row['conditions']['cadence_ns'])
    assert pids[-1]!=row['ready']['target_pid'], 'observer presented as worker'
    a,b=row['clock_before'],row['clock_after']
    difference=(b['continuous_ns']-a['continuous_ns'])-(b['uptime_ns']-a['uptime_ns'])
    tolerance=sum(c['end_ns']-c['begin_ns'] for c in (a,b))+1_000_000
    assert abs(difference)<=tolerance, 'system sleep overlaps hold'
    assert row['conditions']['sleep_difference_ns']==difference and row['conditions']['sleep_tolerance_ns']==tolerance
    assert row['conditions']['cadence_ns']>0 and row['conditions']['calibration']
    if row['snapshot'] is not None:
        count=2 if row['name']=='actor_lifecycle' else int(row['name'].split('_')[-1])
        check_snapshot(row['snapshot'],row['name']=='actor_lifecycle',count)
        assert {a['pid'] for a in row['snapshot']['actors']}==set(pids[:-5])
        assert row['snapshot']['actors'][row['snapshot']['active_actor']]['pid']==row['ready']['target_pid']
    else: assert row['name']=='ordinary'
    return row


def check_measurement(row):
    """Historical busy-worker oracle; keep its original meaning and callers."""
    check_wait_measurement(row)
    assert all(delta>row['deltas_ns'][-2] for delta in row['deltas_ns'][:-5]), 'worker CPU must exceed sleeping control'
    return row


def calibrate(observer,out):
    with observer.spawn_control('busy') as busy, observer.spawn_control('sleep') as sleeper:
        samples=[]
        pids=[busy.pid,sleeper.pid,observer.process.pid]
        for _ in range(80):
            samples.append(observer.sample(pids)); time.sleep(.002)
        sparse_before=observer.sample(pids); time.sleep(.2); sparse_after=observer.sample(pids)
    counters=[cpu(require_sample(b['samples'][0])) for b in samples]
    increments=[b-a for a,b in zip(counters,counters[1:])]
    assert all(d>=0 for d in increments) and any(d>0 for d in increments)
    smallest=min(d for d in increments if d>0)
    quantum=max(10_000_000,math.ceil(smallest/10_000_000)*10_000_000)
    receipt=dict(version=1,dense_cadence_requested_ns=2_000_000,dense_observer_delta_ns=cpu(samples[-1]['samples'][-1])-cpu(samples[0]['samples'][-1]),sparse_control=dict(before=sparse_before,after=sparse_after,observer_delta_ns=cpu(sparse_after['samples'][-1])-cpu(sparse_before['samples'][-1])),batches=samples,raw_deltas_ns=increments,smallest_positive_ns=smallest,
        plateaus=sum(d==0 for d in increments),accounting_quantum_ns=quantum,
        interpretation='Observed counter increments under running busy control; declared quantum is conservative and machine specific, not universal.')
    save(out/'calibration.json',receipt); return quantum


def measure(pw,out,bridge,helper,observer,host,name,quantum,repetition,multiplier,conditions):
    out.mkdir(parents=True)
    actor_count=int(name.split('_')[-1]) if name in ('actor_1','actor_3') else None
    work=HeldWorkload(pw,out,bridge,helper,observer,actor_host=host if name!='ordinary' else None,actor_count=actor_count,lifecycle=name=='actor_lifecycle')
    row=None; primary=None
    try:
        work.start()
        with observer.spawn_control('busy') as busy, observer.spawn_control('sleep') as sleeper:
            pids=[s['pid'] for s in work.workers]+[work.host['pid'],work.validator['pid'],busy.pid,sleeper.pid,observer.process.pid]
            minimum=max(1_000_000_000,100*quantum); requested=minimum*multiplier+100_000_000
            effects=[]; clock_before=observer.clock(); before=observer.sample(pids)
            # Request margin above required conservative interval; effects read independently throughout.
            deadline=time.monotonic_ns()+requested
            while True:
                effect=work.effects(); effect['clock']=observer.clock(); effects.append(effect)
                if time.monotonic_ns()>=deadline: break
                time.sleep(.05)
            after=observer.sample(pids); clock_after=observer.clock()
            actual=after['begin_ns']-before['end_ns']
            difference=(clock_after['continuous_ns']-clock_before['continuous_ns'])-(clock_after['uptime_ns']-clock_before['uptime_ns'])
            tolerance=sum(c['end_ns']-c['begin_ns'] for c in (clock_before,clock_after))+1_000_000
            deltas=[cpu(b)-cpu(a) for a,b in zip(before['samples'],after['samples'])]
            row=dict(version=1,name=name,repetition=repetition,multiplier=multiplier,quantum_ns=quantum,hold_min_ns=minimum,requested_ns=requested,
                held_generations=work.held_generations,ready=work.ready,effects=effects,before=before,after=after,clock_before=clock_before,clock_after=clock_after,
                roles=[f'worker:{i}' for i in range(len(work.workers))]+['host','validator','busy_control','sleep_control','observer'],snapshot=work.snapshot,
                release=None,actual_min_ns=actual,deltas_ns=deltas,observer=dict(pid=pids[-1],delta_ns=deltas[-1],cadence_ns=50_000_000),
                conditions=dict(conditions,cadence_ns=50_000_000,sleep_difference_ns=difference,sleep_tolerance_ns=tolerance))
            save(out/'measurement.json',row)
            work.release(); row['release']=work.interventions[0]; save(out/'measurement.json',row)
            work.complete(); check_measurement(row)
            expected={s['pid'] for s in [*work.workers,work.host]}
            deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                events=work.exits.read_exit_events(.1)
                if expected <= {e['generation']['pid'] for e in events}: break
            save(out/'primary-end-observations.json',dict(events=events,registrations=work.exits.registrations))
            assert expected <= {e['generation']['pid'] for e in events}, 'required process ending unobserved before cleanup'
    except BaseException as exc:
        primary=exc; save(out/'failure.json',dict(error=repr(exc),measurement_present=row is not None)); raise
    finally:
        try: work.finish()
        except BaseException as exc:
            save(out/'cleanup-failure.json',dict(error=repr(exc)))
            if primary is None: raise
    return row


def main(app,out,identity,bridge,helper,binary):
    app=Path(app).resolve(); out=Path(out).resolve()
    conditions=dict(os_version=subprocess.run(['/usr/bin/sw_vers'],capture_output=True,text=True,check=True).stdout,hardware=subprocess.run(['/usr/sbin/sysctl','hw.model','hw.ncpu','hw.memsize'],capture_output=True,text=True,check=True).stdout,source_hashes={str(p.relative_to(ROOT)): __import__('hashlib').sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),ROOT/'tests/lib/footprint_workloads.py',ROOT/'tests/fixtures/footprint/actor_snapshot.swift')},calibration=str(out/'calibration.json'),repetitions=3,power_source=subprocess.run(['/usr/bin/pmset','-g','batt'],capture_output=True,text=True,check=True).stdout,
        competing_load=subprocess.run(['/usr/bin/uptime'],capture_output=True,text=True,check=True).stdout,
        scope='External worker CPU; actor state from disposable instrumented host; no summed memory or idle claim.')
    save(out/'conditions-before.json',conditions)
    host=ActorHostFixture(app,out/'actor-host',identity).build()
    with FootprintObserver(binary,out/'observer') as observer:
        quantum=calibrate(observer,out)
        save(out/'declared-measurements.json',dict(quantum_ns=quantum,hold_min_ns=max(1_000_000_000,100*quantum),multipliers=[1,3],repetitions=3,names=['ordinary','actor_1','actor_3','actor_lifecycle']))
        rows=[]; failures=[]
        # Preserve all required repetitions, including contrary measurements.
        for name in ('ordinary','actor_1','actor_3','actor_lifecycle'):
            for multiplier in (1,3):
                for repeat in range(3):
                    directory=out/f'{name}-{multiplier}-{repeat}'
                    try: rows.append(measure(app/'Contents/MacOS/policy-witness',directory,bridge,helper,observer,host,name,quantum,repeat,multiplier,conditions))
                    except Exception as exc:
                        failures.append(dict(directory=str(directory),error=repr(exc)))
                        owner=json.loads((directory/'ownership.json').read_text())
                        if owner['cleanup_retained']:
                            save(out/'summary.json',dict(completed=len(rows),required=24,failures=failures,stopped_for_unresolved_cleanup=True))
                            raise
        save(out/'summary.json',dict(completed=len(rows),required=24,failures=failures,quantum_ns=quantum))
        assert not failures and len(rows)==24,failures
    print('24 matched Waiting holds retain selected-effect guards, CPU and actor authority publications')

if __name__=='__main__': main(*sys.argv[1:])
