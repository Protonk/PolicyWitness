"""Read-only evidence inspection; writes only this plan's review indexes.

Run after the material run is complete, console attached and pin installed.
This is investigation equipment, not a harness entry point or recovery action.
"""
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
RECORD = ROOT / 'records/coherence'
BASELINE = Path('/private/tmp/pw-pytest-exec-candidate-20261030')
ACCEPTED = Path('/Users/raccoon/Desktop/Security/PolicyWitness')
OUT = ROOT / 'tests/out/runs/coherence-01'
F = 'runner_c_worker_harness/exec_control_states'
sys.path.insert(0, str(ROOT / 'tests/lib'))
import artifact
import pytest_resources
from pytest_support import read, write, digest, value_digest


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


def main():
    run = read(OUT / 'run.json')
    assert run['ok'] and run['terminal']
    assert run['completion'] == dict(selected=11, completed=11, skipped=0, unrun=0)
    pins = read(ROOT / 'tests/RETAINED.json')['runs']
    pin = next(r for r in pins if r['path'] == 'runs/coherence-01')
    assert pin['run_id'] == run['run_id'] and pin['source'] == git(ROOT, 'rev-parse', '6b35e27a')
    inherited = json.loads(subprocess.check_output(['git', 'show', '809ef178:tests/RETAINED.json'], cwd=ROOT))
    assert all(row in pins for row in inherited['runs'])
    inventory = artifact.inventory(OUT)
    family = read(OUT / 'suites' / F / 'family.json')
    write(RECORD / 'evidence-index.json', dict(
        review_baseline=git(ROOT, 'rev-parse', '809ef178'), tested_source=pin['source'],
        worktree=str(ROOT), path=str(OUT), run_id=run['run_id'], pin=pin,
        command=read(OUT / 'plan.json')['selection'], completion=run['completion'],
        cases=run['case_results'], legacy_counts=run['counts'], parent_counts=run['case_outcome_counts'],
        harness_errors=run['harness_errors'], artifact_integrity=run['artifact_integrity'],
        family_items=len(family['items']), family_operations=len(family['operations']),
        inventory_entries=len(inventory), inventory_sha256=value_digest(inventory),
        key_sha256={n:digest(OUT / n) for n in ('run.json','owner.json','plan.json','console.txt')}))

    fixtures = OUT / 'suites/dispatcher/pytest_controls/artifacts'
    observations = read(fixtures / 'observations.json')
    unresolved = []
    for path in sorted(fixtures.glob('*/repo/tests/out/pytest-owners/*/*/record.json')):
        r = read(path)
        if pytest_resources.disposition(r) == 'closed':
            continue
        scenario = path.relative_to(fixtures).parts[0]
        evidence = {n:dict(path=str(fixtures / scenario / n), sha256=digest(fixtures / scenario / n),
                          value=read(fixtures / scenario / n))
                    for n in ('independent-starts.json','independent-exits.json') if (fixtures / scenario / n).exists()}
        if (Path(r['root']) / 'tests/run.sh').exists():
            preview = 'cd ' + shlex.quote(r['root']) + ' && tests/run.sh --recover-ownership ' + shlex.quote(r['run_id'])
        else:
            code = 'import json,sys;from pathlib import Path;sys.path.insert(0,' + repr(str(ROOT / 'tests/lib')) + ');import pytest_resources;print(json.dumps(pytest_resources.recover(Path(' + repr(r['root']) + '),' + repr(r['run_id']) + '),indent=2))'
            preview = '/opt/homebrew/opt/python@3.14/bin/python3.14 -B -S -P -c ' + shlex.quote(code)
        unresolved.append(dict(scenario=scenario, record=str(path), sha256=digest(path),
            identity={k:r.get(k) for k in ('root','run_id','operation_id','state','out','artifacts','socket_dir','family','item','token','nonce','lock_identity','controller_pid','engine_pid','owner_pid','command_pid','command_pgid','argv')},
            blocking=pytest_resources.disposition(r), recovery_preview=preview,
            independent=evidence, observations=[o for o in observations if str(path) in json.dumps(o) or str(fixtures / scenario) in json.dumps(o)],
            missing='Authenticated matching settlement, revoked launch authority and group absence (or affirmative never-launched receipt). Historical PID, direct return, external exits and available lock do not supply missing owner settlement.',
            disposition='Retain fixture record and enclosing pinned run; no historical PID signaling or forced closure.'))
    actual = pytest_resources.inspect(ROOT)
    assert actual and all(r['blocking'] == 'closed' for r in actual)
    write(RECORD / 'recovery-index.json', dict(worktree=str(ROOT), registry=str(pytest_resources.base(ROOT)),
        actual_commands=actual, actual_unresolved=[], retained_fixtures=unresolved,
        prior_recovery_index=str(BASELINE / 'records/pytest-exec-adoption/recovery-index.json'),
        prior_resource_supplement=str(BASELINE / 'records/pytest-maintenance/resource-recovery.md')))

    walkthrough = []
    for scenario, name in [('integrated-normal','run'),('wrong-rejection','run'),('baseline','run'),
                           ('input-finalizer','run'),('cleanup-finalizer','run'),('death-engine','death'),('missing-packages','run')]:
        output = fixtures / scenario / 'repo/tests/out/runs' / name
        report = read(output / 'run.json'); folder = output / 'suites' / F
        item = dict(scenario=scenario, output=str(output), parent=report['case_results'][0], overall_ok=report['ok'])
        if (folder / 'family.json').exists():
            f = read(folder / 'family.json')
            item['items'] = [dict(id=i['id'], outcome=i['outcome'], started=i['started'],
                                 phases={p:v['outcome'] for p,v in i['phases'].items()}) for i in f['items']]
            item['display_opening'] = (folder / 'summary.txt').read_text().splitlines()[:2]
            item['phase_report'] = str(folder / 'phases.jsonl')
        if scenario == 'wrong-rejection':
            native = folder / 'artifacts/collection_from_final_reap'
            item['native'] = {n:dict(path=str(native / n), sha256=digest(native / n), value=read(native / n))
                              for n in ('expectation.json','observation.json','sources.json')}
        walkthrough.append(item)
    write(RECORD / 'walkthrough.json', walkthrough)

    assert git(BASELINE, 'rev-parse', 'HEAD') == git(ROOT, 'rev-parse', '809ef178')
    assert not git(BASELINE, 'status', '--short')
    protected = read(BASELINE / 'records/pytest-exec-adoption/completion.json')['protected_worktrees']
    for path, expected in protected.items():
        assert git(path, 'rev-parse', 'HEAD') == expected['head']
        assert git(path, 'status', '--short') == expected['status'].strip()
    previous = read(BASELINE / 'records/pytest-exec-adoption/evidence-index.json')['runs']
    for row in previous:
        prior = Path(row['path']); prior_root = Path(row['worktree'])
        assert row['pin'] in read(prior_root / 'tests/RETAINED.json')['runs']
        assert all(digest(prior / n) == sha for n,sha in row['key_sha256'].items())
    app = artifact.inventory(ACCEPTED / 'dist/PolicyWitness.app')
    assert app == read(BASELINE / 'tests/out/runs/pytest-exec-acceptance-08/artifact-integrity/before.json')
    assert app == read(OUT / 'artifact-integrity/before.json')
    earlier = json.loads(subprocess.check_output(['/private/tmp/pw-pytest-boundary-venv/bin/python','-B','-I',
        'records/pytest-maintenance/snapshot.py','--verify'],cwd='/private/tmp/pw-pytest-maintenance-20261030'))
    write(RECORD / 'preservation.json', dict(baseline_head=git(BASELINE,'rev-parse','HEAD'), baseline_clean=True,
        prior_adoption_pins_and_key_records_verified=len(previous),
        verification_limit='Prior adoption full tree hashes retained in baseline index; this pass checks their pins and key records, not all 459345 files again.',
        earlier_investigation=earlier, inherited_pin_entries_unchanged=len(inherited['runs']),
        protected_worktrees=protected, accepted_app_sha256=value_digest(app),
        original_counterfactual_blob=git(ROOT,'rev-parse','0c22d256:records/workset/pytest-first.md')))
    print(json.dumps(dict(run_id=run['run_id'], actual_closed=len(actual), unresolved_fixtures=len(unresolved), inventory_entries=len(inventory))))


if __name__ == '__main__':
    main()
