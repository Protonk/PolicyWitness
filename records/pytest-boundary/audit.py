"""Read-only evidence audit; writes only this investigation's inventory.json."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
MAIN=Path('/Users/raccoon/Desktop/Security/PolicyWitness')


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    original=json.loads(git('show','77eb9875:tests/RETAINED.json'))['runs']
    pins=read(ROOT/'tests/RETAINED.json')['runs']
    retained=[]
    for path in sorted((ROOT/'tests/out/runs').glob('pytest-boundary-*')):
        run=read(path/'run.json')
        matches=[p for p in pins if p['path']==str(path.relative_to(ROOT/'tests/out'))]
        assert len(matches)==1 and matches[0]['run_id']==run['run_id']
        retained.append(dict(path=str(path),run_id=run['run_id'],ok=run['ok'],completion=run['completion'],
                             source=matches[0]['source'],run_sha256=sha(path/'run.json')))
    app=MAIN/'dist/PolicyWitness.app'
    inventory_path=MAIN/'tests/out/runs/f2-reservation-final-01/artifact-integrity/before.json'
    inventory=read(inventory_path)
    errors=[]
    if {'.'}|{str(p.relative_to(app)) for p in app.rglob('*')} != set(inventory):
        errors.append('path set')
    for name,entry in inventory.items():
        path=app/name
        if path.lstat().st_mode!=entry['mode']:errors.append(name+':mode')
        if 'sha256' in entry and sha(path)!=entry['sha256']:errors.append(name+':bytes')
    candidate=['common.py','engine.py','supervisor.py','resource_owner.py','recover.py']
    demo=['observe.py','test_subject.py','pytest.ini',*candidate]
    equality={name:git('show','832e7717:records/pytest-boundary/'+name)==(ROOT/'records/pytest-boundary'/name).read_bytes()
              for name in demo}
    os.environ['BOUNDARY_ROOT']=str(ROOT)
    sys.path.insert(0,str(Path(__file__).parent))
    from common import account, rows
    native_reconciliation={}
    for name in ('old','stale','adapted'):
        path=ROOT/'tests/out/runs'/('pytest-boundary-replay-'+name+'-01')/'candidate'
        prior=read(path/'run.json')
        results,failures=account([c['id'] for c in prior['plan']['cases']],list(rows(path/'reports.jsonl')),
                                prior['engine_returncode'],prior['resources'])
        native_reconciliation[name]=dict(same_cases=results==prior['case_results'],same_errors=failures==prior['harness_errors'])
    resource_records=[]
    for path in sorted((ROOT/'tests/out/runs').glob('pytest-boundary-*/candidates/*/resources/*/record.json')):
        record=read(path)
        resource_records.append(dict(path=str(path),state=record['state'],pid=record.get('pid'),
                    resource_exists=Path(record['resource']).exists(),socket_dir_exists=Path(record['socket_dir']).exists()))
    frozen=git('show','0c22d256:records/workset/pytest-first.md')
    result=dict(accepted_baseline='77eb987554eef10ffa3371ffb21b235097562a78',
                reviewed_source=git('rev-parse','HEAD').decode().strip(),
                prior_pins_unchanged=all(p in pins for p in original),
                main_retention_unchanged=read(MAIN/'tests/RETAINED.json')['runs']==original,
                accepted_app_inventory_errors=errors,app_inventory_sha256=sha(inventory_path),
                c0_2_sha256=hashlib.sha256(frozen).hexdigest(),
                demo_dependencies_equal_final=equality,retained_runs=retained,
                native_journals_reconciled_with_final_reader=native_reconciliation,
                source_lines={n:len((ROOT/'records/pytest-boundary'/n).read_text().splitlines())
                              for n in [*candidate,'native_adapter.py','test_native.py','observe.py','observe_replay.py','test_subject.py']},
                resource_records=resource_records,
                protected_existing={str(p):p.exists() for p in [Path('/private/tmp/pw-extension-directory-uge3532e'),
                    Path('/private/tmp/pw-f2-stage1'),Path('/private/tmp/pw-f2-controlled-prep'),
                    Path('/Users/raccoon/Desktop/Security/PolicyWitness-pytest-trial-evidence')]},
                limitations=['Hashes establish identity, not complete semantic dependencies.',
                             'No new original-worker exit or signing verification is inferred.'])
    (ROOT/'records/pytest-boundary/inventory.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('resource_records','retained_runs')},indent=2))
    assert not errors and all(equality.values()) and result['prior_pins_unchanged'] and result['main_retention_unchanged']
    assert all(all(r.values()) for r in native_reconciliation.values())


if __name__=='__main__':
    main()
