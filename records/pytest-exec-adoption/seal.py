"""Read retained adoption evidence and write the associated review indexes."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import shlex
import sys

ROOT=Path('/private/tmp/pw-pytest-exec-candidate-20261030')
COMPARISON=Path('/private/tmp/pw-pytest-exec-comparison-20261030')
BUILD=Path('/private/tmp/pw-pytest-exec-build-check-20261030')
ACCEPTED=Path('/Users/raccoon/Desktop/Security/PolicyWitness')
RECORD=ROOT/'records/pytest-exec-adoption'
sys.path.insert(0,str(ROOT/'tests/lib'))
import artifact
import pytest_resources
from pytest_support import read,digest,value_digest,write
F='runner_c_worker_harness/exec_control_states'


def main():
    roots=[ROOT,COMPARISON,BUILD]
    index=[];pending=[]
    for root in roots:
        pins={r['path']:r for r in read(root/'tests/RETAINED.json')['runs']}
        for out in sorted((root/'tests/out/runs').glob('pytest-exec-*')):
            relative=str(out.relative_to(root/'tests/out'))
            if relative not in pins:raise ValueError('unsealed material run '+str(out))
            run=read(out/'run.json');pin=pins[relative]
            checks={p:digest(out/p) for p in ('owner.json','plan.json','run.json') if (out/p).is_file()}
            files=artifact.inventory(out)
            row=dict(worktree=str(root),path=str(out),run_id=run['run_id'],source=pin['source'],pin=pin,
                     ok=run['ok'],completion=run['completion'],harness_errors=run.get('harness_errors',[]),
                     cases=[{k:c.get(k) for k in ('id','status','state','execution_state','accounting_state')} for c in run['case_results']],
                     key_sha256=checks,inventory_sha256=value_digest(files),inventory_entries=len(files))
            if (out/'suites'/F/'family.json').is_file():
                family=read(out/'suites'/F/'family.json');owner=read(out/'suites'/F/'ownership.json')
                row['family']=dict(ok=family['ok'],items=len(family['items']),operations=len(family['operations']),ownership_closed=owner['closed'],sha256=digest(out/'suites'/F/'family.json'))
            index.append(row)
            fixture=out/'suites/dispatcher/pytest_controls/artifacts'
            for path in sorted(fixture.glob('*/repo/tests/out/pytest-owners/*/*/record.json')):
                record=read(path)
                if pytest_resources.disposition(record)=='closed':continue
                scenario=path.relative_to(fixture).parts[0]
                endpoint=Path(record['socket_dir'])
                facts={}
                observations=fixture/'observations.json'
                if observations.exists():
                    facts['controller_observations']=dict(path=str(observations),sha256=digest(observations),
                        related=[r for r in read(observations) if str(path) in json.dumps(r) or str(fixture/scenario) in json.dumps(r)])
                for name in ('independent-starts.json','independent-exits.json'):
                    p=fixture/scenario/name
                    if p.exists():facts[name]=dict(path=str(p),sha256=digest(p),value=read(p))
                if (Path(record['root'])/'tests/run.sh').exists():
                    recovery_command='cd '+shlex.quote(record['root'])+' && bash tests/run.sh --recover-ownership '+shlex.quote(record['run_id'])
                else:
                    code='import json,sys;from pathlib import Path;sys.path.insert(0,'+repr(str(ROOT/'tests/lib'))+');import pytest_resources;print(json.dumps(pytest_resources.recover(Path('+repr(record['root'])+'),'+repr(record['run_id'])+'),indent=2))'
                    recovery_command='/opt/homebrew/opt/python@3.14/bin/python3.14 -B -S -P -c '+shlex.quote(code)
                pending.append(dict(run=str(out),fixture=scenario,record=str(path),sha256=digest(path),
                    root=record['root'],run_id=record['run_id'],operation_id=record['operation_id'],
                    state=record['state'],automatic_disposition=pytest_resources.disposition(record),
                    historical_identity={k:record.get(k) for k in ('family','item','owner_pid','engine_pid','controller_pid','command_pid','command_pgid','lock_identity','out','artifacts','argv')},
                    missing_prerequisites='Authenticated matching settlement with launch authority revoked and group absence (or affirmative never-launched receipt); historical PID numbers and state labels are insufficient.',
                    socket_dir=str(endpoint),socket_dir_exists=endpoint.exists(),facts=facts,
                    recovery_preview_command=recovery_command,
                    recovery_driver='fixture public command' if (Path(record['root'])/'tests/run.sh').exists() else 'current neutral reader; minimal historical fixture has no public launcher',
                    disposition='Retained fixture evidence; do not infer cleanup from a historical PID. External controlled exits, when recorded, do not substitute for an absent authenticated owner settlement.'))
    write(RECORD/'evidence-index.json',dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),runs=index))
    live=pytest_resources.inspect(ROOT)
    if any(r['blocking']!='closed' for r in live):raise ValueError('actual candidate ownership unresolved')
    recovery=dict(candidate_worktree=str(ROOT),candidate_registry=str(pytest_resources.base(ROOT)),
        candidate_actual_records=len(live),candidate_unresolved=[],retained_fixture_records=pending,
        previous_protected_resources=dict(status='unchanged; no recovery attempted',
          description='The frozen investigation early-run resource and unknown-worker directory retain their prior disposition.',
          prior_record=str(ROOT/'records/pytest-maintenance/resource-recovery.md')))
    write(RECORD/'recovery-index.json',recovery)
    old=COMPARISON/'tests/out/runs/pytest-exec-current-normal-01/suites'/F/'artifacts'
    # Choose the final current candidate family observation explicitly.
    normal=ROOT/'tests/out/runs/pytest-exec-acceptance-08/suites'/F/'artifacts'
    old_ledger=read(old/'observed-call-policy.json');new_ledger=read(normal/'production/observed-call-policy.json')
    assert old_ledger==new_ledger and len(new_ledger)==58
    old_source=read(old/'production/source-sha256.json');new_source=read(normal/'production/sources.json')
    assert old_source=={k:v for k,v in new_source.items() if Path(k).suffix in ('.c','.h')}
    original=subprocess.check_output(['git','show','77eb987554eef10ffa3371ffb21b235097562a78:tests/suites/runner_c_worker_harness/check_exec_evidence.py'],cwd=ROOT,text=True)
    dictionaries={}
    for node in ast.walk(ast.parse(original)):
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('mutations','expected_assertions'):
            dictionaries[node.targets[0].id]=ast.literal_eval(node.value)
    module=ast.parse((ROOT/'tests/suites/runner_c_worker_harness/exec_domain.py').read_text())
    declaration=next(n.value for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MUTATIONS' for t in n.targets))
    pairs=[tuple(ast.literal_eval(a) for a in call.args) for call in declaration.elts]
    assert {n:v for n,v,e in pairs}==dictionaries['mutations']
    assert {n:e for n,v,e in pairs}==dictionaries['expected_assertions']
    proof=dict(ledger_attempts=58,ledger_equal=True,ledger_sha256=value_digest(new_ledger),native_input_closure_equal=True,
        native_files=len(old_source),mutation_statements_and_expected_assertions_equal=True,mutation_count=len(pairs),
        native_fixture_sha256=digest(ROOT/'tests/fixtures/worker_lifecycle/exec_control.c'),
        golden_sha256=digest(ROOT/'tests/fixtures/worker_lifecycle/exec_call_policy.json'))
    write(RECORD/'native-comparison.json',proof)
    # The diagnostic control is independent of the candidate's summary renderer.
    control=ROOT/'tests/out/runs/pytest-exec-acceptance-08/suites/dispatcher/pytest_controls/artifacts'
    walkthrough=[]
    for scenario in ('integrated-normal','formation','accepted-mutation','wrong-rejection','timed-out-rejection','timed-out-baseline','baseline','both-phases','input-finalizer','cleanup-finalizer','setup-acquired','missing-packages','death-engine','death-interrupt','publication-summary','publication-start'):
        name='death' if scenario.startswith('death-') else 'run'
        out=control/scenario/'repo/tests/out/runs'/name
        run=read(out/'run.json');parent=run['case_results'][0];folder=out/'suites'/F
        row=dict(scenario=scenario,parent_path=str(out/'run.json'),parent={k:parent.get(k) for k in ('status','state','execution_state','accounting_state','reason')})
        console=control/scenario/('invocation.log' if scenario.startswith('death-') else 'run-invocation/stdout')
        if console.exists():
            text=console.read_text()
            row['ordinary_display']=dict(path=str(console),sha256=digest(console),family_lines=[v for v in text.splitlines() if v.startswith('FAMILY ')])
            if parent.get('accounting_state') in ('incomplete','unavailable'):
                assert parent['execution_state']+'/'+parent['accounting_state'] in text
        if (folder/'family.json').exists():
            family=read(folder/'family.json');row['family_path']=str(folder/'family.json')
            row['items']=[dict(id=i['id'],outcome=i['outcome'],phases={p:r['outcome'] for p,r in i['phases'].items()}) for i in family['items']]
            row['summary_path']=str(folder/'summary.txt');row['summary_exists']=(folder/'summary.txt').exists()
            if row['summary_exists']:
                row['summary_sha256']=digest(folder/'summary.txt')
                row['scope_lines']=[line for line in (folder/'summary.txt').read_text().splitlines() if line.startswith(('FAMILY','SHARED','OWNERSHIP','ACCOUNT:'))]
            paths=['selection.json','phases.jsonl','pytest.txt','ownership.json','operations.jsonl']
            row['resolved_evidence']={p:digest(folder/p) for p in paths if (folder/p).is_file()}
            if scenario in ('integrated-normal','formation','accepted-mutation','wrong-rejection','timed-out-rejection'):
                variant=folder/'artifacts/collection_from_final_reap'
                row['expectation']=read(variant/'expectation.json')
                if (variant/'observation.json').exists():row['observation']=read(variant/'observation.json')
                row['variant_path']=str(variant)
                row['native_evidence']={p:dict(path=str(variant/p),sha256=digest(variant/p)) for p in ('build/stdout','build/stderr','build/command.json','run/stdout','run/stderr','run/command.json') if (variant/p).exists()}
                sources=variant/('sources-before-formation.json' if scenario=='formation' else 'sources.json')
                hashes=read(sources)
                assert all(digest(variant/name)==hash for name,hash in hashes.items())
                row['retained_sources_match_receipt']=True
            if (folder/'artifacts/baseline.json').exists():row['baseline']=read(folder/'artifacts/baseline.json')
            if scenario in ('input-finalizer','cleanup-finalizer'):
                row['shared_finalizer']=read(folder/'artifacts/session-finalizer.json')
                row['input_integrity']=read(folder/'artifacts/input-integrity.json')
                row['per_variant_sources_match']=all(all(digest(p.parent/n)==h for n,h in read(p).items()) for p in (folder/'artifacts').glob('*/sources.json'))
        walkthrough.append(row)
    write(RECORD/'walkthrough.json',dict(scenarios=walkthrough,old_failure_report=read(COMPARISON/'tests/out/runs/pytest-exec-current-formation-01/suites'/F/'report.json')))
    print(json.dumps(dict(runs=len(index),candidate_records=len(live),retained_fixture_records=len(pending),native=proof)))

if __name__=='__main__':main()
