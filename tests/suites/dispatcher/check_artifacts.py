"""Inspect real file damage through the public dispatcher, using fake codesign.

Expected outcomes come from explicit scenarios and independent execution receipts;
the fixture never imports the inspector or derives expected errors from it.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/fixtures/dispatcher'))
from repository import install_runner
from artifacts import bundle, seal, fingerprint


def exercise(out, name):
    work = out / name
    repo = work / 'repository'
    install_runner(ROOT, repo, {'probe': {
        'command': ['bash', 'tests/suites/probe/run.sh'], 'cases': [
            {'id': 'app', 'requires': ['app']}, {'id': 'worker', 'requires': ['worker']},
            {'id': 'offline'}]}}, signed_fixtures=True)
    for source, relative in [('selection.sh', 'tests/suites/probe/run.sh'),
                              ('selection.py', 'tests/fixtures/dispatcher/selection.py')]:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'tests/fixtures/dispatcher' / source, path)
        path.chmod(0o755)
    app = repo / 'dist/PolicyWitness.app'
    bundle(app)
    helper = app / 'Contents/MacOS/pw-runner-client'
    manifest_path = app / 'Contents/Resources/Evidence/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    expected_issue = None
    if name == 'missing_helper':
        helper.unlink()
        expected_issue = 'required_component'
    elif name == 'damaged_signature':
        helper.write_bytes(b'broken signed bytes')
        expected_issue = 'signature'
    elif name == 'resigned_stale_manifest':
        helper.write_bytes(b'changed and resealed')
        seal(app)
        expected_issue = 'manifest_hash'
    elif name == 'missing_manifest_entry':
        manifest['entries'] = [e for e in manifest['entries'] if e['rel_path'] != 'Contents/MacOS/pw-runner-client']
        manifest_path.write_text(json.dumps(manifest))
        seal(app)
        expected_issue = 'manifest_missing'
    elif name == 'duplicate_manifest_entry':
        manifest['entries'].append(manifest['entries'][0])
        manifest_path.write_text(json.dumps(manifest))
        seal(app)
        expected_issue = 'manifest_entry'
    elif name == 'invalid_manifest':
        manifest_path.write_text('[]')
        seal(app)
        expected_issue = 'manifest'
    elif name == 'external_helper':
        external = repo / 'external'
        helper.rename(external)
        helper.symlink_to(external)
        seal(app)
        expected_issue = 'required_component'
    before = fingerprint(app)
    receipts = work / 'receipts.jsonl'
    modes = {'probe/app': name} if name.startswith('mutate_') else {}
    env = {k: v for k, v in os.environ.items() if not k.startswith('PW_')}
    env.update(CONTROL_SELECTION_RECEIPTS=str(receipts), CONTROL_SELECTION_MODES=json.dumps(modes),
               PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run(['bash', str(repo / 'tests/run.sh')], env=env, capture_output=True, timeout=30)
    (work / 'stdout').write_bytes(result.stdout)
    (work / 'stderr').write_bytes(result.stderr)
    run = json.loads((repo / 'tests/out/run.json').read_text())
    integrity = run['artifact_integrity']
    evidence = repo / 'tests/out/artifact-integrity'
    issues = json.loads((evidence / 'inspection.json').read_text())
    executed = [json.loads(line)['id'] for line in receipts.read_text().splitlines()]
    assert result.returncode == (0 if name == 'valid' else 1), (name, result.stderr)
    assert run['ok'] is (name == 'valid')
    assert integrity['valid_before'] is (expected_issue is None)
    if expected_issue:
        assert expected_issue in {e['code'] for e in issues['errors']}, issues
        assert executed == ['probe/offline'], executed
        assert run['completion'] == dict(selected=3, completed=1, unrun=2, skipped=0)
        assert fingerprint(app) == before, 'inspection repaired or modified damaged input'
        assert integrity['unchanged'] is True
        if name == 'resigned_stale_manifest':
            assert all(s['returncode'] == 0 for s in issues['signatures'])
    else:
        assert executed == ['probe/app', 'probe/worker', 'probe/offline']
        delta = json.loads((evidence / 'changes.json').read_text())
        if name.startswith('mutate_'):
            assert integrity['unchanged'] is False
            assert 'artifact_changed' in {e['code'] for e in run['harness_errors']}
            assert set(delta) == {'Contents', 'Contents/added-resource', 'Contents/new-link',
                                  'Contents/MacOS/pw-runner-client', 'Contents/Resources/Evidence/symbols.json'}
            assert delta['Contents/new-link']['after']['symlink'] == 'added-resource'
            assert delta['Contents/Resources/Evidence/symbols.json']['after'] is None
            assert helper.read_bytes() == b'changed during case execution\n', 'guard repaired the input'
        else:
            assert integrity['unchanged'] is True and delta == {}
    return name


if __name__ == '__main__':
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    cases = [exercise(out, name) for name in ('valid', 'missing_helper', 'damaged_signature',
        'resigned_stale_manifest', 'missing_manifest_entry', 'duplicate_manifest_entry',
        'invalid_manifest', 'external_helper', 'mutate_pass', 'mutate_fail', 'mutate_crash')]
    (out / 'controls.json').write_text(json.dumps(cases, indent=2) + '\n')
    print(f'{len(cases)} artifact controls passed')
