"""Verify the retained raw observations and build links before reporting them."""
import collections, hashlib,json,re
from pathlib import Path
out=Path(__file__).resolve().parents[1]
def get(p): return json.loads((out/p).read_bytes())
cal=[]
for group,labels in [('sysctl',['absent','present']),('service',['absent','platform','power']),('client',['absent','power'])]:
    first=None
    for label in labels:
        f='calibration/'+group+'-'+label
        rows=[line.split() for line in (out/(f+'.stdout')).read_text().splitlines() if re.match(r'^\d+\s',line)]
        assert [int(r[0]) for r in rows]==list(range(1,201))
        assert all(len(r)==4 and r[3]=='-' for r in rows)
        assert get(f+'.json')['rc']==1
        if first is None:first=rows
        differences=[[int(r[0]),r[1:],a[1:]] for r,a in zip(rows,first) if r!=a]
        assert not differences
        counter=collections.Counter(r[2] for r in rows)
        cal.append(dict(scan=f,row_count=len(rows),row_diffs_against_first=differences,
                changed_allow_side_ids=[int(r[0]) for r,a in zip(rows,first) if r[2]!=a[2]],allow_side_counts=counter,
                strict_matches=[],row_digest=hashlib.sha256(json.dumps(rows).encode()).hexdigest()))
(out/'calibration/comparison.json').write_text(json.dumps(cal,indent=2)+'\n')
for k in ['regular','fifo-short','fifo-ordinary']:
    d=get('blocking/'+k+'.json'); obs=get('blocking/'+k+'-lifecycle.json'); r=d['data']['runner_result']; sub=r['runner_subprocess']
    assert r['producer']['contract']==d['build']['contract']=='release:v0.3.8'
    assert sub['reaped'] and not sub['wait_errors'] and (out/'blocking'/(k+'.stderr')).stat().st_size==0
    assert not any('watchdog' in e['event'] for e in obs['events'])
    if k!='regular':
        assert sub['term_signal']==9 and sub['done_observed'] is False and sub['termination_request']==dict(rc=0,signal=9)
        assert obs['live_matches_report'] and obs['rc']==1 and d['result']['normalized_outcome']=='runner_timeout'
        live=next(e for e in obs['events'] if e['event']=='live-candidate')
        assert live['ppid']==next(a['control']['host_pid'] for a in d['data']['runner_client']['transport']['attempts'] if a.get('control',{}).get('status')=='granted')
        assert live['pid']==sub['pid'] and any(v['exit'] and v['pid']==live['pid'] for e in obs['events'] for v in e.get('events',[]))
        assert any(e['event']=='ps-after' and e['rc']==1 and not e['stdout'] for e in obs['events'])
for k,entries,marker in [('explicit',[1,1],True),('nil',[0,0],False),('empty',[0,0],False),('cleared',[1,0],True)]:
    rec=[json.loads(l) for l in (out/'environment'/(k+'.stdout')).read_text().splitlines()]
    snap=get('environment/'+k+'-ps.json')['snapshot']
    assert snap['pid']==rec[-1]['pid'] and snap['controlled_marker_visible']==marker and [d['entries'] for d in rec]==entries
obs=get('environment/env-lifecycle.json'); env=get('environment/worker-ps-sanitized.json')
assert obs['reported_worker']==env['pid'] and obs['live_matches_report'] and env['same_bytes'] and env['plain_rc']==env['environment_rc']==0
for label in ['original','mutant','clean-mutant']:
    inventory=get('provenance/'+label+'/worker-equipment.json')
    apps=get('provenance/'+label+'/current-bytes.json')
    build=json.loads(apps['controller']['stdout'])['build']
    assert build['contract']==inventory['contract'] and inventory['worker_identity'] in apps['worker']['stdout']
    for p in (out/'mutation'/(label+'-fifo')).glob('*/response.json'):
        d=json.loads(p.read_bytes())
        o=json.loads(p.with_name('observations.json').read_bytes())
        rr=d['data']['runner_result']; s=rr['steps'][0]['attempt']
        assert o['request_contract']==o['response_contract']==build['contract']==rr['producer']['contract']
        assert o['host']==next(a['control']['host_pid'] for a in d['data']['runner_client']['transport']['attempts'] if a.get('control',{}).get('status')=='granted')
        assert rr['runner_subprocess']['reaped'] and o['reaped'] and s['requested_action']=='open_read'
        if o['mode']=='connected-empty':
            assert any(e['event']=='blocking_writer_open_returned' for e in o['events'])
            assert (s['outcome'],o['outcome'])==(('no_completed_result','runner_timeout') if label=='original' else ('ok','finished'))
        else:
            sample=next(e for e in o['events'] if e['event']=='post_run_sample')
            assert o['outcome']=='finished' and o['rc']==0 and s['outcome']=='ok'
            expect={'original':{'two-bytes':'79'},'mutant':{'two-bytes':'7a79'},'clean-mutant':{'two-bytes':'7a79'}}[label].get(o['mode'],'EAGAIN' if label=='original' else '7a')
            assert sample.get('bytes_hex',sample.get('name'))==expect
print('Passed table, native-build linkage, FIFO lifecycle, environment control, and byte-effect checks.')
