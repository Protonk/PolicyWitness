"""Seal final local preservation and review metadata after all observations finish."""
import datetime
import ast
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path('/private/tmp/pw-pytest-exec-candidate-20261030')
ACCEPTED=Path('/Users/raccoon/Desktop/Security/PolicyWitness')
RECORD=ROOT/'records/pytest-exec-adoption'
sys.path.insert(0,str(ROOT/'tests/lib'))
import artifact
import pytest_resources
import release_accept
from pytest_support import read,write,value_digest

def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()

def main():
    initial=read(RECORD/'state.json')
    state={}
    for root,expected in initial['existing_worktrees'].items():
        head=git(root,'rev-parse','HEAD');status=subprocess.check_output(['git','status','--short'],cwd=root,text=True)
        assert head==expected['head'] and status==expected['status'],(root,head,status)
        state[root]=dict(head=head,status=status)
    subprocess.run(['git','diff','--exit-code','8fd2c825..HEAD','--','controller','runner','records/workset',
        'tests/fixtures/worker_lifecycle/exec_control.c','tests/fixtures/worker_lifecycle/exec_call_policy.json'],cwd=ROOT,check=True)
    baseline=json.loads(subprocess.check_output(['git','show','8fd2c825:tests/RETAINED.json'],cwd=ROOT,text=True))
    now={r['path']:r for r in read(ROOT/'tests/RETAINED.json')['runs']}
    assert all(now[r['path']]==r for r in baseline['runs'])
    preservation=json.loads(subprocess.check_output(['/private/tmp/pw-pytest-boundary-venv/bin/python','-B','-I',
        'records/pytest-maintenance/snapshot.py','--verify'],cwd='/private/tmp/pw-pytest-maintenance-20261030',text=True))
    inventory=artifact.inventory(ACCEPTED/'dist/PolicyWitness.app')
    final=ROOT/'tests/out/runs/pytest-exec-acceptance-08'
    assert inventory==read(final/'artifact-integrity/before.json')
    assert read(final/'run.json')['ok']
    build_root=Path('/private/tmp/pw-pytest-exec-build-check-20261030')
    build=build_root/'tests/out/runs/pytest-exec-build-continuation-02'
    build_run=read(build/'run.json');assert build_run['ok']
    evidence=build/'suites/preflight/build_refusal_controls/artifacts'
    battery=read(evidence/'release-battery/acceptance/tests/run.json')
    assert battery['ok'] and battery['completion']==dict(completed=202,selected=202,skipped=0,unrun=0)
    outer=read(evidence/'release-battery/acceptance/acceptance.json')
    final_reader=release_accept.battery_problems(battery,Path(outer['extraction_dir'])/'PolicyWitness.app',
        expected=outer['execution_contract'],evidence=evidence/'release-battery/acceptance/tests')
    assert not final_reader,final_reader
    module=ast.parse(subprocess.check_output(['git','show','cecfdeef:tests/suites/preflight/opt_in/build_refusals.py'],cwd=build_root,text=True))
    mutations=next(n.value for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MUTATIONS' for t in n.targets))
    controls=[tuple(ast.literal_eval(v) for v in n.elts[:2]) for n in mutations.elts]
    log=(evidence/'assertions.log').read_text()
    assert len(controls)==16 and all(log.count('mutation '+name+': '+label+';')==1 for name,label in controls)
    registry=pytest_resources.inspect(ROOT)
    assert all(r['blocking']=='closed' for r in registry)
    prune=read(Path('/private/tmp/pytest-exec-prune-final.json'))
    assert not prune['failures'] and not prune['removed']
    write(RECORD/'pruning.json',prune)
    write(RECORD/'completion.json',dict(
        observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        code_commit=git(ROOT,'rev-parse','79dc6fbe'),
        source_before_review_commit=git(ROOT,'rev-parse','HEAD'),
        candidate_branch=git(ROOT,'branch','--show-current'),candidate_worktree=str(ROOT),
        endpoint='bounded implementation and verification complete; recommend acceptance for this family only',
        integration='not merged; no adoption of another family',
        protected_worktrees=state,prior_pin_entries_unchanged=len(baseline['runs']),
        original_counterfactual=dict(reference='0c22d256:records/workset/pytest-first.md',blob=git(ROOT,'rev-parse','0c22d256:records/workset/pytest-first.md')),
        preservation_verification=preservation,accepted_application_inventory_sha256=value_digest(inventory),
        actual_candidate_command_records=len(registry),unresolved_actual_candidate_records=[],
        final_family_run=dict(path=str(final),source=git(ROOT,'rev-parse','79dc6fbe'),run_id=read(final/'run.json')['run_id']),
        build_continuation=dict(path=str(build),source=git(build_root,'rev-parse','cecfdeef'),run_id=build_run['run_id'],battery_completion=battery['completion'],completed_mutations=controls,final_reader_problems=final_reader,independent_contract_identity=outer['execution_contract']['identity']),
        current_toolchain=dict(clang=subprocess.check_output(['/usr/bin/xcrun','--sdk','macosx','clang','--version'],text=True),
            sdk=subprocess.check_output(['/usr/bin/xcrun','--sdk','macosx','--show-sdk-version'],text=True).strip(),
            os=subprocess.check_output(['/usr/bin/sw_vers'],text=True)),
        retention='decisive and consequential runs pinned in owning worktrees; ambiguous nested fixture records retained',
        retirement='plan and associated records remain for acceptance review, then retire together per CONTRIBUTING.md'))
    print(json.dumps(dict(protected_worktrees=len(state),prior_pins=len(baseline['runs']),actual_commands=len(registry),preservation=preservation)))

if __name__=='__main__':main()
