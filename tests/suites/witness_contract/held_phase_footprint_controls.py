"""Constructed receipt sensitivity, separate from native/live measurement credit."""
import copy
import json
from pathlib import Path
import sys

from check_held_phase_footprint import check_measurement
from footprint_workloads import check_snapshot, check_held_binding, cleanup_complete


def sample(pid,t,cpu):
    identity=dict(pid=pid,start_sec=100,start_usec=pid)
    calls={name:dict(begin_ns=t+i*2,end_ns=t+i*2+1,rc=0 if name=='rusage' else 1,errno=0) for i,name in enumerate(('generation_before','rusage','path','generation_after'))}
    return dict(pid=pid,status='ok',generation_before=identity,generation_after=identity.copy(),path='/fixture/pw-probe-runner',begin_ns=t,end_ns=t+8,calls=calls,raw_cpu_unit='mach_absolute_time_ticks',user_ticks=cpu,system_ticks=0,timebase_numer=1,timebase_denom=1,user_ns=cpu,system_ns=0,resident_bytes=100,phys_footprint_bytes=100)


def batch(t,cpus):
    samples=[sample(i+1,t+i*10,c) for i,c in enumerate(cpus)]
    return dict(version=1,clock='mach_continuous_time_ns',cpu_unit='ns',memory_unit='bytes',begin_ns=t,end_ns=t+len(samples)*10,samples=samples)


def clock(t): return dict(begin_ns=t,end_ns=t+10,continuous_ns=t+5,uptime_ns=t+5,clock='mach_continuous_time_ns')


def held_generations(workers,host,validator):
    ids=workers+[host,validator]
    initial={pid:sample(pid,200,0) for pid in ids}
    registrations=[dict(generation=initial[pid]['generation_before'],before=sample(pid,100,0),begin_ns=110,end_ns=120,after=sample(pid,130,0)) for pid in ids]
    return dict(workers=[initial[pid] for pid in workers],host=initial[host],validator=initial[validator],registrations=registrations,conversion_rounding_ns=1)

def baseline():
    before=batch(1000,[0,0,0,0,0,0]); after=batch(2_000_001_000,[500_000_000,2000,3000,900_000_000,1000,50_000_000])
    return dict(held_generations=held_generations([1],2,3),version=1,name='ordinary',repetition=0,multiplier=1,quantum_ns=10_000_000,hold_min_ns=1_000_000_000,requested_ns=1_100_000_000,
        ready=dict(event='ready',target_pid=1,observer_ack_clock=clock(800)),effects=[dict(gate=dict(event='held',closed=False),target_unchanged=True,marker_unchanged=True,exec_connected=False,clock=clock(2000+i)) for i in range(3)],
        before=before,after=after,clock_before=clock(900),clock_after=clock(2_000_002_000),roles=['worker:0','host','validator','busy_control','sleep_control','observer'],snapshot=None,
        release=dict(before=clock(2_000_003_000)),actual_min_ns=after['begin_ns']-before['end_ns'],deltas_ns=[500_000_000,2000,3000,900_000_000,1000,50_000_000],
        observer=dict(pid=6,delta_ns=50_000_000,cadence_ns=50_000_000),conditions=dict(cadence_ns=50_000_000,calibration='constructed',sleep_difference_ns=0,sleep_tolerance_ns=1_000_020))


def actor_snapshot():
    slot=lambda complete: dict(slot=0,completed=complete,call_boundary=complete,native_valid=complete,native_not_minus_one=bool(complete))
    visit=lambda n,g,a,c:dict(visit=n,global_phase=g,arrived=a,acknowledged=c,completed=c)
    actors=[dict(actor_index=0,pid=1,setup=2,authority_status=1,activation=1,activation_observed=1,proceed=1,evidence_progress=0,visits=[visit(0,1,1,1),visit(1,4,0,0)],slots=[slot(1)]),
        dict(actor_index=1,pid=5,setup=1,authority_status=1,activation=3,activation_observed=3,proceed=1,evidence_progress=0,visits=[visit(0,2,1,1),visit(1,3,1,0),visit(2,5,0,0)],slots=[slot(1)]+[dict(slot=i,completed=0,call_boundary=0,native_valid=0,native_not_minus_one=False) for i in range(1,8)])]
    def operands(delivery=0,handle=0,recipient=0,last=False):
        return dict(token_index=0,delivery_index=delivery,handle_index=handle,recipient_index=recipient,last_use=last)
    issuer=[('issueT',14,operands()),('sendD1',15,operands(recipient=1)),('sendD2',15,operands(delivery=1,recipient=1))]
    subject=[('consumeH1',10,operands()),('knownread',9,None),('marker',2,None),('consumeH2',10,operands(handle=1,last=True)),('releaseH1',11,operands()),('releaseH2',11,operands(handle=1)),('consumeH3',10,operands(delivery=1,handle=2,last=True)),('releaseH3',11,operands(handle=2))]
    actors[0]['slots']=[dict(slot=i,step_id=n,attempt_kind=k,operands=o,completed=int(i<2),call_boundary=int(i==0),native_valid=int(i==0),native_not_minus_one=i==0) for i,(n,k,o) in enumerate(issuer)]
    for row,(name,kind,operands) in zip(actors[1]['slots'],subject): row.update(step_id=name,attempt_kind=kind,operands=operands)
    return dict(version=1,scope='instrumented_host_pre_collection',host_pid=9,phase_index=2,active_actor=1,begin_ticks=1,end_ticks=2,timebase_numer=1,timebase_denom=1,actors=actors,
        regions=[dict(actor_index=0,bytes=17600,inbound_count=0,outbound_count=1,host_mapping=True),dict(actor_index=1,bytes=34048,inbound_count=2,outbound_count=0,host_mapping=True)],
        tokens=[dict(token_index=0,actor_index=0,last_use_slot=2,accepted=True,length=128,erased=False,mapping_available=True)],
        deliveries=[dict(delivery_index=i,token_index=0,source_actor=0,recipient_actor=1,inbound_position=i,committed=1 if i==0 else 0,acknowledged=1 if i==0 else 0,settled=1 if i==0 else 0,length=128 if i==0 else 0,host_equality='equal' if i==0 else 'not_observed') for i in range(2)])


def main(out):
    good=baseline(); check_measurement(good)
    actor=actor_snapshot(); check_snapshot(actor,True)
    faults=[]
    def fault(name,edit,base=good,checker=check_measurement):
        bad=copy.deepcopy(base); edit(bad); faults.append((name,bad,checker))
    fault('missing_gate',lambda r:r.pop('ready'))
    fault('early_unlink',lambda r:r['effects'][0].update(target_unchanged=False))
    fault('early_marker',lambda r:r['effects'][0].update(marker_unchanged=False))
    fault('early_exec',lambda r:r['effects'][0].update(exec_connected=True))
    fault('missing_exec_observation',lambda r:r['effects'][0].pop('exec_connected'))
    fault('early_release',lambda r:r['release'].update(before=clock(1200)))
    fault('short_hold',lambda r:r.update(hold_min_ns=1))
    fault('oversized_skew',lambda r:r['before'].update(end_ns=20_000_000))
    fault('sleep_overlap',lambda r:r['clock_after'].update(uptime_ns=1))
    fault('missing_sample',lambda r:r['before']['samples'].pop())
    fault('native_error',lambda r:r['after']['samples'][0]['calls']['rusage'].update(rc=-1))
    fault('generation_changed',lambda r:r['after']['samples'][0]['generation_after'].update(start_sec=200))
    fault('decreasing_counter',lambda r:r['before']['samples'][0].update(system_ns=1,system_ticks=1))
    fault('observer_as_worker',lambda r:r['ready'].update(target_pid=6))
    def swap(r,a,b):
        for key in ('user_ns','system_ns','user_ticks','system_ticks'):
            r['after']['samples'][a][key],r['after']['samples'][b][key]=r['after']['samples'][b][key],r['after']['samples'][a][key]
        r['deltas_ns'][a],r['deltas_ns'][b]=r['deltas_ns'][b],r['deltas_ns'][a]
    fault('busy_sleep_swapped',lambda r:swap(r,3,4))
    fault('worker_sleep_swapped',lambda r:swap(r,0,4))
    def equal(r,i):
        r['after']['samples'][i]['user_ns']=1000; r['after']['samples'][i]['user_ticks']=1000; r['deltas_ns'][i]=1000
    fault('busy_sleep_equal',lambda r:equal(r,3))
    fault('worker_sleep_equal',lambda r:equal(r,0))
    for name,edit in (
        ('presence_as_parked',lambda r:r['actors'][0].pop('visits')),
        ('pre_consume',lambda r:r['actors'][1]['slots'][0].update(completed=0)),
        ('withdrawn_delivery',lambda r:r['deliveries'][0].update(committed=0)),
        ('missing_delivery',lambda r:r['deliveries'].pop()),
        ('erased_custody',lambda r:r['tokens'][0].update(erased=True)),
        ('erasure_as_unmapping',lambda r:r['tokens'][0].update(erased=True,mapping_available=False)),
        ('release_attempted',lambda r:r['actors'][1]['slots'][4].update(call_boundary=1)),
        ('swapped_reference',lambda r:r['deliveries'][0].update(token_index=1)),
        ('bearer_dump',lambda r:r['tokens'][0].update(token_hex='secret'))):
        fault(name,edit,actor,lambda r:check_snapshot(r,True))
    fault('missing_release_slot',lambda r:r['actors'][1]['slots'].pop(4),actor,lambda r:check_snapshot(r,True))
    fault('missing_issuer_slot',lambda r:r['actors'][0]['slots'].pop(),actor,lambda r:check_snapshot(r,True))
    fault('duplicate_slot',lambda r:r['actors'][1]['slots'][4].update(slot=3),actor,lambda r:check_snapshot(r,True))
    fault('wrong_step_association',lambda r:r['actors'][1]['slots'][4].update(step_id='consumeH2'),actor,lambda r:check_snapshot(r,True))
    fault('wrong_handle_association',lambda r:r['actors'][1]['slots'][4]['operands'].update(handle_index=1),actor,lambda r:check_snapshot(r,True))
    fault('duplicate_region_actor',lambda r:r['regions'][1].update(actor_index=0),actor,lambda r:check_snapshot(r,True))
    fault('swapped_delivery_position',lambda r:r['deliveries'][0].update(inbound_position=1),actor,lambda r:check_snapshot(r,True))
    fault('swapped_later_delivery',lambda r:r['deliveries'][1].update(delivery_index=0),actor,lambda r:check_snapshot(r,True))
    fault('exact_capacity_length',lambda r:r['tokens'][0].update(length=16384),actor,lambda r:check_snapshot(r,True))
    fault('overcapacity_length',lambda r:r['tokens'][0].update(length=16385),actor,lambda r:check_snapshot(r,True))
    fault('wrong_held_generation',lambda r:r['held_generations']['host']['generation_before'].update(start_sec=101))
    bound=held_generations([1,5],9,10); ready=dict(event='ready',target_pid=5,observer_ack_clock=clock(800))
    check_held_binding(actor,ready,bound)
    fault('wrong_host',lambda r:r.update(host_pid=99),actor,lambda r:check_held_binding(r,ready,bound))
    fault('late_snapshot',lambda r:r.update(end_ticks=1000),actor,lambda r:check_held_binding(r,ready,bound))
    fault('invalid_timebase',lambda r:r.update(timebase_numer=0),actor,lambda r:check_held_binding(r,ready,bound))
    partial=copy.deepcopy(bound); partial['registrations'].pop()
    try: check_held_binding(actor,ready,partial)
    except AssertionError: pass
    else: raise AssertionError('partial watcher registration accepted')
    generations={r['generation']['pid']:r['generation'] for r in bound['registrations']}
    ends=[dict(generation=g) for g in generations.values()]
    assert cleanup_complete(generations,generations,ends,True)
    assert not cleanup_complete(generations,{1:generations[1]},[dict(generation=generations[1])],True)
    assert not cleanup_complete(generations,generations,ends,False)
    assert not cleanup_complete(generations,generations,ends,True,True,['P'])
    results=[]
    for name,bad,checker in faults:
        try: checker(bad)
        except (AssertionError,KeyError,TypeError,ValueError,IndexError): results.append(name)
        else: raise AssertionError('corrupt receipt accepted: '+name)
    Path(out,'controls.json').write_text(json.dumps(dict(scope='constructed checker sensitivity, no live measurements credited',accepted=['ordinary','actor_lifecycle'],rejected=results),indent=2)+'\n')
    print(f'{len(results)} independent corrupt Waiting receipts rejected')

if __name__=='__main__': main(*sys.argv[1:])
