"""Retain dispatcher receipts and compare the two complete default selections."""
from pathlib import Path
import collections, hashlib,json,os,shutil
out=Path(__file__).resolve().parents[1]/'mutation'
def read(p):return json.loads(p.read_bytes())
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
both={}
family_items={}
for label in ['original','mutant','clean-mutant']:
    src=Path('/private/tmp/pw-findings-b7113f57-'+label)/'tests/out/runs'/('four-findings-'+label+'-equipped')
    dest=out/(label+'-battery');dest.mkdir(exist_ok=True)
    for n in ['owner.json','run.json','events.jsonl','dispatch.json','plan.json']:
        shutil.copyfile(src/n,dest/n)
    shutil.copytree(src/'artifact-integrity',dest/'artifact-integrity',dirs_exist_ok=True)
    effects=src/'suites/run_effects/file_actions_have_exact_effects'
    shutil.copytree(effects,dest/'file_actions_have_exact_effects',dirs_exist_ok=True)
    run=read(src/'run.json');plan=read(src/'plan.json')
    family_items[label]={}
    family_counts={}
    for family in plan['execution_contract']['family_selections'].values():
        name=family['family']
        rel=next(c['family_report'] for c in run['case_results'] if c['id']==name)
        report=read(src/rel)
        ids=[i['id'] for i in family['items']]
        outcomes={i['id']:i['outcome'] for i in report['items']}
        family_items[label][name]=(ids,outcomes)
        family_counts[name]=dict(collection=len(ids),outcomes=dict(collections.Counter(outcomes.values())))
    sels=[c['id'] for c in plan['cases']]
    results={c['id']:{k:c[k] for k in ['status','state','context']} for c in run['case_results']}
    assert len(sels)==len(set(sels))==len(results)
    both[label]=dict(run_id=run['run_id'],run_path=str(src),summary_sha256=sha(src/'run.json'),
        terminal=run['terminal'],ok=run['ok'],duration_ms=run['duration_ms'],completion=run['completion'],
        pytest_families=family_counts,case_outcome_counts=run['case_outcome_counts'],harness_errors=run['harness_errors'],
        artifact_integrity=run['artifact_integrity'],selection=plan['selection']['mode'],ids=sels,
        case_status=results,failed_or_skipped=[c for c in run['case_results'] if c['status'] not in ('pass','complete')],
        slept=[c['id'] for c in run['case_results'] if (c.get('system_sleep_ms') or 0)>0])
cmp={}
for variant in ['mutant','clean-mutant']:
    a,b=both['original'],both[variant]
    ids_a={f:data[0] for f,data in family_items['original'].items()}
    ids_b={f:data[0] for f,data in family_items[variant].items()}
    changed_items=[dict(id=item_id,original=original_outcome,mutant=family_items[variant][f][1].get(item_id))
                   for f,(_,outcomes) in family_items['original'].items()
                   for item_id,original_outcome in outcomes.items() if family_items[variant][f][1].get(item_id)!=original_outcome]
    cmp[variant]=dict(same_pytest_selection=ids_a==ids_b,changed_pytest_items=changed_items,same_pytest_items_and_outcomes=family_items['original']==family_items[variant],same_ordered_selection=a['ids']==b['ids'],added=sorted(set(b['ids'])-set(a['ids'])),
         removed=sorted(set(a['ids'])-set(b['ids'])),case_status_changes=[dict(case=k,original=a['case_status'][k],mutant=b['case_status'][k]) for k in a['ids'] if k in b['case_status'] and a['case_status'][k]!=b['case_status'][k]])
for data in both.values(): data.pop('case_status');data.pop('ids')
write(out/'battery-comparison.json',dict(comparison=cmp,runs=both))
print(json.dumps(dict(comparison=cmp,outcomes={k:v['case_outcome_counts'] for k,v in both.items()}),indent=2))
