"""Public CLI held workloads shared by Waiting and Aftermath. Cleanup is explicit."""
import json
from pathlib import Path
import secrets
import select
import shutil
import time
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
for path in ('tests/suites/witness_contract', 'tests/fixtures/validator', 'tests/fixtures/exec', 'tests/fixtures/footprint'):
    sys.path.insert(0, str(ROOT / path))
from check_ordering import step, specimen, save
from check_extensions import probe
from run_capture import RunCapture
from gate import Gate, install_bridge
from control import TreeControl, process_snapshot
from footprint_observer import require_sample, generation, GenerationExitObserver, sha256
from actor_host import ActorHostFixture
import consumer


def extension(name, operation, **fields):
    return dict(step_id=name, extension=dict(operation=operation, **fields))


def actor_specimen(target, marker, count=None):
    actor = lambda name, mode: dict(actor_id=name,equipment='unentitled' if mode=='unapplied' else 'selected',sandbox=dict(mode=mode, **({} if mode=='unapplied' else dict(policy=dict(format='sbpl',sbpl_source='(version 1)(allow default)')))))
    if count is not None:
        assert count in (1,3)
        # Constant three requested operations; extra workers park until their visit.
        actors=[actor('a'+str(i),'apply') for i in range(count)]
        actions=[step(target,'open_read',f'read{i}') for i in range(3)]
        phases=[dict(phase_id='hold',actor_id='a0',actions=actions if count==1 else actions[:1])]
        if count==3:
            phases += [dict(phase_id='later'+str(i),actor_id='a'+str(i),actions=[actions[i]]) for i in (1,2)]
        return dict(schema_version=6,specimen_id=secrets.token_hex(8),actors=actors,phases=phases),0
    phases=[
        ('issue','issuer',[extension('issueT','issue',family='file',authority='read',target=str(target),token_ref='T'),extension('sendD1','transfer',token_ref='T',recipient='subject',delivery_ref='D1')]),
        ('consume','subject',[extension('consumeH1','consume',delivery_ref='D1',handle_ref='H1')]),
        ('hold','subject',[probe('knownread',target),step(marker,'open_write','marker'),extension('consumeH2','consume',delivery_ref='D1',handle_ref='H2'),extension('releaseH1','release',handle_ref='H1'),extension('releaseH2','release',handle_ref='H2')]),
        ('latertransfer','issuer',[extension('sendD2','transfer',token_ref='T',recipient='subject',delivery_ref='D2')]),
        ('laterconsume','subject',[extension('consumeH3','consume',delivery_ref='D2',handle_ref='H3'),extension('releaseH3','release',handle_ref='H3')])]
    return dict(schema_version=6,specimen_id=secrets.token_hex(8),actors=[actor('issuer','unapplied'),actor('subject','apply')],phases=[dict(phase_id=n,actor_id=a,actions=x) for n,a,x in phases]),2


SNAPSHOT_KEYS={'version','scope','host_pid','phase_index','active_actor','begin_ticks','end_ticks','timebase_numer','timebase_denom','actors','regions','tokens','deliveries'}
ACTOR_KEYS={'actor_index','pid','setup','authority_status','activation','activation_observed','proceed','evidence_progress','visits','slots'}

def check_snapshot(snapshot, lifecycle=False, count=None):
    assert set(snapshot)==SNAPSHOT_KEYS, 'unknown or missing snapshot metadata'
    assert snapshot['version']==1 and snapshot['scope']=='instrumented_host_pre_collection'
    assert snapshot['begin_ticks']<=snapshot['end_ticks'] and snapshot['timebase_denom']>0 and snapshot['timebase_numer']>0 and snapshot['begin_ticks']>0
    actors=snapshot['actors']; assert len(actors)==(2 if lifecycle else count)
    assert len({a['pid'] for a in actors})==len(actors)
    assert [a['actor_index'] for a in actors]==list(range(len(actors)))
    for a in actors:
        assert set(a)==ACTOR_KEYS and a['setup'] in (1,2)
        assert all(type(a[k]) is int and a[k]>=0 for k in ('actor_index','pid','setup','authority_status','activation','activation_observed','proceed','evidence_progress'))
        assert a['pid']>0
        for v in a['visits']:
            assert set(v)=={'visit','global_phase','arrived','acknowledged','completed'}
            assert all(type(v[k]) is int and v[k]>=0 for k in v)
        for s in a['slots']:
            assert set(s)=={'slot','step_id','attempt_kind','operands','completed','call_boundary','native_valid','native_not_minus_one'}
            assert type(s['native_not_minus_one']) is bool
            if s['operands'] is not None:
                assert set(s['operands'])=={'token_index','delivery_index','handle_index','recipient_index','last_use'}
                assert type(s['operands']['last_use']) is bool
                assert all(type(s['operands'][k]) is int and s['operands'][k]>=0 for k in set(s['operands'])-{'last_use'})
            assert all(type(s[k]) is int and s[k] in (0,1) for k in ('completed','call_boundary','native_valid'))
    active=actors[snapshot['active_actor']]
    held=next(v for v in active['visits'] if v['global_phase']==snapshot['phase_index']+1)
    assert held['arrived']==1 and held['acknowledged']==0 and held['completed']==0
    assert active['proceed']==held['visit']
    for r in snapshot['regions']:
        assert set(r)=={'actor_index','bytes','inbound_count','outbound_count','host_mapping'}
        assert r['bytes']==1152+(r['inbound_count']+r['outbound_count'])*16448 and r['host_mapping'] is True
    for t in snapshot['tokens']:
        assert set(t)=={'token_index','actor_index','last_use_slot','accepted','length','erased','mapping_available'}
        assert all(type(t[k]) is bool for k in ('accepted','erased','mapping_available'))
        assert all(type(t[k]) is int and t[k]>=0 for k in ('token_index','actor_index','last_use_slot','length'))
    for d in snapshot['deliveries']:
        assert set(d)=={'delivery_index','token_index','source_actor','recipient_actor','inbound_position','committed','acknowledged','settled','length','host_equality'}
        assert all(type(d[k]) is int and d[k]>=0 for k in set(d)-{'host_equality'})
    if not lifecycle:
        for index,a in enumerate(actors):
            if index!=snapshot['active_actor']:
                assert a['activation']==a['activation_observed']==a['proceed']==0
                assert all(v['arrived']==v['acknowledged']==v['completed']==0 for v in a['visits'])
    if lifecycle:
        assert snapshot['phase_index']==2 and snapshot['active_actor']==1
        issuer,subject=actors
        assert issuer['setup']==2 and subject['setup']==1 and issuer['authority_status']==subject['authority_status']==1
        assert issuer['visits'][0]['completed']==1 and issuer['visits'][1]['arrived']==0
        assert issuer['activation']==issuer['activation_observed']==1
        assert subject['activation']==subject['activation_observed']==3
        assert len(snapshot['regions'])==2 and len(snapshot['tokens'])==1 and len(snapshot['deliveries'])==2
        t=snapshot['tokens'][0]; d=snapshot['deliveries'][0]
        assert t['token_index']==d['token_index']==0 and t['actor_index']==d['source_actor']==0 and d['recipient_actor']==1
        assert t['accepted'] is True and t['length']>0 and not t['erased'] and t['mapping_available'] is True and t['last_use_slot']>1
        assert d['committed']==d['acknowledged']==d['settled']==1 and d['length']==t['length'] and d['host_equality']=='equal'
        h1=subject['slots'][0]
        assert h1['completed']==h1['call_boundary']==h1['native_valid']==1 and h1['native_not_minus_one'] is True
        assert all(s['completed']==s['call_boundary']==0 for s in subject['slots'][1:6])
    # Exact fixture-owned input associations make publication labels auditable.
    def operands(token=0,delivery=0,handle=0,recipient=0,last=False):
        return dict(token_index=token,delivery_index=delivery,handle_index=handle,recipient_index=recipient,last_use=last)
    if lifecycle:
        expected_slots=[
            [('issueT',14,operands()),('sendD1',15,operands(recipient=1)),('sendD2',15,operands(delivery=1,recipient=1))],
            [('consumeH1',10,operands()),('knownread',9,None),('marker',2,None),('consumeH2',10,operands(handle=1,last=True)),('releaseH1',11,operands()),('releaseH2',11,operands(handle=1)),('consumeH3',10,operands(delivery=1,handle=2,last=True)),('releaseH3',11,operands(handle=2))]]
        expected_visits=[[(0,1,1,1,1),(1,4,0,0,0)],[(0,2,1,1,1),(1,3,1,0,0),(2,5,0,0,0)]]
        assert [(r['actor_index'],r['outbound_count'],r['inbound_count']) for r in snapshot['regions']]==[(0,1,0),(1,0,2)]
        assert t['last_use_slot']==2 and 0<t['length']<16384
        for index,d in enumerate(snapshot['deliveries']):
            assert (d['delivery_index'],d['token_index'],d['source_actor'],d['recipient_actor'],d['inbound_position'])==(index,0,0,1,index)
            if index==1:
                assert d['committed']==d['acknowledged']==d['settled']==d['length']==0 and d['host_equality']=='not_observed'
    else:
        assert snapshot['phase_index']==snapshot['active_actor']==0
        expected_slots=[[('read'+str(i),1,None) for i in range(3)]] if count==1 else [[('read'+str(i),1,None)] for i in range(3)]
        expected_visits=[[(0,i+1,1 if i==0 else 0,0,0)] for i in range(count)]
        assert not snapshot['regions'] and not snapshot['tokens'] and not snapshot['deliveries']
    for index,a in enumerate(actors):
        slots=a['slots']; expected=expected_slots[index]
        assert len(slots)==len(expected) and [s['slot'] for s in slots]==list(range(len(expected)))
        assert [(s['step_id'],s['attempt_kind'],s['operands']) for s in slots]==expected
        assert [(v['visit'],v['global_phase'],v['arrived'],v['acknowledged'],v['completed']) for v in a['visits']]==expected_visits[index]
        completed=2 if lifecycle and index==0 else 1 if lifecycle else 0
        assert [s['completed'] for s in slots]==[1]*completed+[0]*(len(slots)-completed)
        assert all(s['call_boundary']==s['native_valid']==0 and s['native_not_minus_one'] is False for s in slots[completed:])
    return snapshot


def check_held_binding(snapshot,ready,held,before=None):
    assert set(held)=={'workers','host','validator','registrations','conversion_rounding_ns'}
    assert held['conversion_rounding_ns']==1
    samples=[*held['workers'],held['host'],held['validator']]
    expected={s['pid']:generation(require_sample(s)) for s in samples}
    assert all(generation(s)['pid']==s['pid'] for s in samples)
    assert len(expected)==len(samples)
    registrations=held['registrations']
    assert len(registrations)==len(expected) and {r['generation']['pid'] for r in registrations}==set(expected)
    for registration in registrations:
        identity=expected[registration['generation']['pid']]
        assert registration['generation']==identity
        require_sample(registration['before'],identity); require_sample(registration['after'],identity)
        assert registration['before']['pid']==registration['after']['pid']==identity['pid']
        assert registration['before']['end_ns']<=registration['begin_ns']<=registration['end_ns']<=registration['after']['begin_ns']
        if before is not None: assert registration['after']['end_ns']<=before['begin_ns']
    assert ready['target_pid'] in {s['pid'] for s in held['workers']}
    if before is not None:
        for sample in before['samples']:
            if sample['pid'] in expected:
                require_sample(sample,expected[sample['pid']]); assert generation(sample)['pid']==sample['pid']
                original=next(s for s in samples if s['pid']==sample['pid'])
                assert original['end_ns']<=before['begin_ns']
                assert sample['user_ns']>=original['user_ns'] and sample['system_ns']>=original['system_ns']
        assert set(expected)<={s['pid'] for s in before['samples']}
    if snapshot is not None:
        assert snapshot['host_pid']==held['host']['pid']
        assert {a['pid'] for a in snapshot['actors']}=={s['pid'] for s in held['workers']}
        assert snapshot['actors'][snapshot['active_actor']]['pid']==ready['target_pid']
        numerator,denominator=snapshot['timebase_numer'],snapshot['timebase_denom']
        assert type(numerator) is int and numerator>0 and type(denominator) is int and denominator>0
        # Ceil preserves a conservative end when converting native ticks to ns.
        snapshot_end=(snapshot['end_ticks']*numerator+denominator-1)//denominator
        assert snapshot_end<=ready['observer_ack_clock']['begin_ns']+held['conversion_rounding_ns']
    return held


def cleanup_complete(discovered,registered,events,setup_complete,tree_expected=False,tree_roles=()):
    expected=set(discovered)
    return (setup_complete and bool(expected) and set(registered)==expected
            and len(events)==len(expected) and {e['generation']['pid'] for e in events}==expected
            and all(e['generation']==registered[e['generation']['pid']] for e in events)
            and (not tree_expected or set(tree_roles)=={'P','C'}))


class HeldWorkload:
    def __init__(self,pw,out,bridge,helper,observer,*,actor_host=None,actor_count=None,lifecycle=False,timeout_ms=60000,ordinary_small=False):
        self.out=Path(out); self.out.mkdir(parents=True,exist_ok=True)
        self.work=Path(tempfile.mkdtemp(prefix='pw-footprint-',dir='/private/tmp'))
        self.observer=observer; self.actor_host=actor_host; self.actor_count=actor_count; self.lifecycle=lifecycle; self.ordinary_small=ordinary_small
        self.target=self.work/'target'; self.marker=self.work/'marker'; self.seed=b'PW footprint known bytes\n'; self.target.write_bytes(self.seed); self.marker.write_bytes(b'unchanged')
        self.helper=helper; self.tree=TreeControl(self.work/'tree'); self.gate=Gate(self.work/'gate')
        validator=install_bridge(bridge,self.out/'bridge',self.gate.path)
        if actor_host:
            spec,self.phase=actor_specimen(self.target,self.marker,None if lifecycle else actor_count)
            spec['_test_overrides']=dict(validator_executable_path=str(validator)); pw=actor_host.pw
        else:
            self.phase=0
            spec=specimen([probe('knownread',self.target),step(self.marker,'open_write','marker')] if ordinary_small else [step(self.target,'unlink','unlink'),dict(step_id='exec',sandbox_check=dict(operation='process-exec*',filter=dict(kind='path',value=str(helper))),attempt=dict(kind='exec',action='spawn',target=str(helper),args=['--tree',self.tree.path]))],overrides=dict(validator_executable_path=str(validator)))
        self.spec=spec; self.run=RunCapture(pw,self.out/'run',spec,cli_args=['--timeout-ms',timeout_ms]); self.snapshot=None
        self.exits=GenerationExitObserver(observer); self.cleanup_confirmed=False; self.setup_complete=False; self.discovered_pids=set(); self.tree_expected=False
        self.records=[]; self.interventions=[]; self.workers=[]; self.host=None; self.released=False
        save(self.out/'ownership.json',dict(staging=str(self.work),cleanup_retained=True,scope='test owned exclusive temporary directory; process cleanup requires acquired generation'))

    def start(self):
        self.run.start(); ready=self.gate.accept(); ready['observer_ack_clock']=self.observer.clock()
        self.discovered_pids.update((ready['target_pid'],self.gate.pid))
        self.persist_ownership()
        worker=process_snapshot(self.helper,ready['target_pid']); parent=worker['ppid']
        self.discovered_pids.add(parent); self.persist_ownership()
        assert process_snapshot(self.helper,self.gate.pid)['ppid']==parent
        self.host=require_sample(self.observer.inspect(parent))
        if self.actor_host:
            self.snapshot=self.actor_host.snapshot(parent,self.phase)
            self.discovered_pids.update(a['pid'] for a in self.snapshot.get('actors',[]) if type(a.get('pid')) is int and a['pid']>0)
            self.persist_ownership()
            check_snapshot(self.snapshot,self.lifecycle,self.actor_count)
            pids=[a['pid'] for a in self.snapshot['actors']]
        else: pids=[ready['target_pid']]
        self.discovered_pids.update(pids); self.persist_ownership()
        self.workers=[]
        for pid in pids:
            self.workers.append(require_sample(self.observer.inspect(pid))); self.persist_ownership()
        for sample in self.workers:
            assert process_snapshot(self.helper,sample['pid'])['ppid']==parent
            assert sample['path'].endswith(('pw-probe-runner','pw-probe-runner-unentitled'))
        assert ready['target_pid'] in pids
        for _ in range(ready['queries']): self.records.append(self.gate.query()); self.gate.emit()
        self.validator=require_sample(self.observer.inspect(self.gate.pid))
        for sample in [*self.workers,self.host,self.validator]: self.exits.watch(sample['pid'],generation(sample))
        self.binary_provenance=[dict(pid=s['pid'],path=s['path'],sha256=sha256(s['path']),bytes=Path(s['path']).stat().st_size) for s in [*self.workers,self.host,self.validator]]
        save(self.out/'binary-provenance.json',self.binary_provenance)
        self.ready=ready; self.setup_complete=True; self.persist_ownership()
        self.held_generations=dict(workers=self.workers,host=self.host,validator=self.validator,registrations=list(self.exits.registrations),conversion_rounding_ns=1)
        check_held_binding(self.snapshot,ready,self.held_generations)
        save(self.out/'held-snapshot.json',dict(ready=ready,host=self.host,workers=self.workers,snapshot=self.snapshot))
        return self

    def persist_ownership(self):
        save(self.out/'ownership.json',dict(staging=str(self.work),cleanup_retained=True,setup_complete=self.setup_complete,discovered_pids=sorted(self.discovered_pids),registered=[generation(r['before']) for r in self.exits.registrations],workers=[generation(s) for s in self.workers],host=generation(self.host) if self.host else None))

    def effects(self):
        ping=self.gate.ping()
        return dict(gate=ping,target_unchanged=self.target.exists() and self.target.read_bytes()==self.seed,marker_unchanged=self.marker.read_bytes()==b'unchanged',exec_connected=bool(select.select([self.tree.listener],[],[],0)[0]))

    def release(self):
        self.interventions.append(dict(operation='gate.finish',before=self.observer.clock()))
        save(self.out/'interventions.json',self.interventions)
        self.tree_expected=not self.actor_host and not self.ordinary_small
        self.gate.finish(); self.released=True
        self.interventions[-1]['after']=self.observer.clock(); save(self.out/'interventions.json',self.interventions)
        if not self.actor_host and not self.ordinary_small:
            pids=self.tree.accept(); self.tree.assert_running(); assert not self.target.exists()
            for pid in pids.values():
                self.discovered_pids.add(pid); self.persist_ownership()
                self.exits.watch(pid)
            leader=process_snapshot(self.helper,pids['P']); child=process_snapshot(self.helper,pids['C'])
            assert leader['ppid']==self.ready['target_pid'] and child['ppid']==leader['pid']
            save(self.out/'released-effects.json',dict(target_absent=True,leader=leader,descendant=child))
            self.tree.release(); self.tree.assert_stopped()

    def complete(self):
        if self.actor_host and self.actor_count==3 and not self.lifecycle:
            for _ in range(2):
                self.gate.reader.close(); self.gate.peer.close()
                ready=self.gate.accept()
                self.discovered_pids.add(self.gate.pid); self.persist_ownership()
                validator=require_sample(self.observer.inspect(self.gate.pid))
                self.exits.watch(self.gate.pid,generation(validator))
                for _ in range(ready['queries']): self.gate.query(); self.gate.emit()
                self.gate.finish()
        rc=self.run.wait(timeout=20); value=self.run.load_json(); assert rc==0 and not consumer.validate(value),value
        runner=value['data']['runner_result']; assert runner['normalized_outcome']=='ok',runner
        assert all(s['attempt']['outcome']=='ok' for s in runner['steps']),runner
        if not self.actor_host:
            ordering=runner['phases'][0]['ordering']
            assert all(ordering[k] for k in ('collection_closed_before_proceed','proceed_set','proceed_observed','worker_lifetime_established')) and not ordering['protocol_violations']
            assert all(s['comparison']['order']=='query_first' for s in runner['steps'])
        if self.ordinary_small:
            assert self.target.read_bytes()==self.seed and self.marker.read_bytes()==b'x'
            read=next(s for s in runner['steps'] if s['step_id']=='knownread')['attempt']['fresh_read']
            assert bytes.fromhex(read['content_hex'])==self.seed and read['read_rc']==len(self.seed)
        if self.lifecycle:
            assert self.target.read_bytes()==self.seed and self.marker.read_bytes()==b'x'
            read=next(s for s in runner['steps'] if s['step_id']=='knownread')['attempt']['fresh_read']
            assert bytes.fromhex(read['content_hex'])==self.seed and read['read_rc']==len(self.seed)
            events=runner['extension_events']; assert len(events)==9,events
            for event in events:
                assert event['result_published'],event
                if event['operation']!='transfer': assert event['call_boundary_observed'],event
                if event['operation']=='consume': assert event['native_result']!=-1,event
                if event['operation']=='release': assert event['native_result']==0,event
            assert len(runner['transfers'])==2 and all(t['equality']=='equal' and t['recipient_acknowledged'] for t in runner['transfers'])
        return runner

    def finish(self):
        # Caller must persist its primary snapshot before this explicit intervention.
        self.interventions.append(dict(operation='gate.close/tree.close/run.close',before=self.observer.clock()))
        save(self.out/'interventions.json',self.interventions); self.gate.save(self.out/'gate-events.json')
        errors=[]
        for pid in self.tree.pids.values():
            self.discovered_pids.add(pid); self.persist_ownership()
            if pid not in self.exits.registered:
                try: self.exits.watch(pid)
                except BaseException as exc: errors.append(repr(exc))
        for close in (self.gate.close,self.tree.close,self.run.close):
            try: close()
            except BaseException as exc: errors.append(repr(exc))
        self.interventions[-1].update(after=self.observer.clock(),errors=errors); save(self.out/'interventions.json',self.interventions)
        observation_begin=self.observer.clock()
        expected=set(self.discovered_pids)
        deadline=time.monotonic()+5
        events=[]
        while expected and time.monotonic()<deadline:
            events=self.exits.read_exit_events(.1)
            if {e['generation']['pid'] for e in events}==expected: break
        confirmed=cleanup_complete(expected,self.exits.registered,events,self.setup_complete,self.tree_expected,self.tree.pids)
        save(self.out/'cleanup-end-observations.json',dict(begin=observation_begin,end=self.observer.clock(),events=events,registrations=self.exits.registrations,expected_pids=sorted(expected),setup_complete=self.setup_complete,all_registered_ends=confirmed))
        self.exits.close()
        self.cleanup_confirmed=confirmed and not errors
        if self.cleanup_confirmed:
            assert self.work.parent==Path('/private/tmp') and self.work.name.startswith('pw-footprint-')
            self.interventions.append(dict(operation='remove_owned_staging',path=str(self.work),before=self.observer.clock()))
            save(self.out/'interventions.json',self.interventions)
            shutil.rmtree(self.work)
            self.interventions[-1]['after']=self.observer.clock(); save(self.out/'interventions.json',self.interventions)
        save(self.out/'ownership.json',dict(staging=str(self.work),cleanup_retained=not self.cleanup_confirmed,cleanup_errors=errors,discovered_pids=sorted(self.discovered_pids),registered_generations=list(self.exits.registered.values()),setup_complete=self.setup_complete,workers=[generation(s) for s in self.workers],host=generation(self.host) if self.host else None))
        assert self.cleanup_confirmed,dict(errors=errors,unresolved=sorted(expected-{e['generation']['pid'] for e in events}))
