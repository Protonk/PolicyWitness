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
from fixture_bundle import bundle, seal, fingerprint, manifest as write_manifest, record as write_record

# The compiled fixture hosts: the suite wrapper builds them once per run.
HOST = Path(os.environ['PW_DISPATCHER_HOST_FIXTURE'])
HOST_IMPORTS_SANDBOX = HOST.with_name(HOST.name + '.imports-sandbox')
WORKER_IMPORTS_CLOCK = HOST.with_name(HOST.name + '.imports-clock')
WORKER_CONTINUOUS_CLOCK = HOST.with_name(HOST.name + '.continuous-clock')
OUTSIDE_TARGET = {name: HOST.with_name(HOST.name + '.' + name) for name in ('x86_64', 'universal', 'one-slice-fat', 'x86_64.dSYM')}
WORKER_REL = 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner'


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
    worker = {'worker_imports_clock': WORKER_IMPORTS_CLOCK, 'worker_continuous_clock': WORKER_CONTINUOUS_CLOCK}.get(name)
    bundle(app, HOST_IMPORTS_SANDBOX if name == 'host_imports_sandbox' else HOST, worker=worker)
    helper = app / 'Contents/MacOS/pw-runner-client'
    manifest_path = app / 'Contents/Resources/Evidence/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    expected_issue = None
    expected_codes = None   # where set, exactly the error codes the fault produces, so one fault never hides another
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
    elif name == 'host_imports_sandbox':
        # The bundle is intact and sealed; only the host's undefined symbols differ.
        expected_issue = 'host_invariance'
    elif name == 'worker_imports_clock':
        # The bundle is intact and sealed; only the worker's undefined symbols differ.
        expected_issue = 'worker_clock'
    elif name == 'worker_unreadable_imports':
        # Bytes nm cannot read, with the manifest following: inspection failure
        # must be an error, never an empty (passing) import set.
        (app / WORKER_REL).write_bytes(b'not a Mach-O worker\n')
        for entry in manifest['entries']:
            if entry['rel_path'] == WORKER_REL:
                entry['sha256'] = fingerprint(app / WORKER_REL)
        manifest_path.write_text(json.dumps(manifest))
        seal(app)
        expected_issue = 'worker_clock'
    elif name == 'missing_record':
        (app / 'Contents/Resources/Evidence/provenance.json').unlink()
        seal(app)
        expected_issue = 'required_component'
    elif name == 'stale_record':
        # The helper changed and the manifest followed, but the record kept the old bytes: the record's hash check names it.
        helper.write_bytes(helper.read_bytes() + b'\0changed')
        for entry in manifest['entries']:
            if entry['rel_path'] == 'Contents/MacOS/pw-runner-client':
                entry['sha256'] = fingerprint(helper)
        manifest_path.write_text(json.dumps(manifest))
        seal(app)
        expected_issue = 'provenance_hash'
    elif name == 'contradictory_record':
        record_path = app / 'Contents/Resources/Evidence/provenance.json'
        record = json.loads(record_path.read_text())
        next(o for o in record['outputs'] if o['rel_path'] == 'Contents/MacOS/pw-runner-client')['uuid'] = 'FFFFFFFF-0000-0000-0000-000000000000'
        record_path.write_text(json.dumps(record))
        for entry in manifest['entries']:
            if entry['rel_path'] == 'Contents/Resources/Evidence/provenance.json':
                entry['sha256'] = fingerprint(record_path)
        manifest_path.write_text(json.dumps(manifest))
        seal(app)
        expected_issue = 'provenance_metadata'
    elif name == 'x86_64_helper':
        # Bytes outside the output target with everything else consistent: the manifest and the record both describe
        # them truthfully. The inspector refuses the bytes, and the record's own validation refuses an output that is
        # not the target; nothing else is wrong.
        shutil.copyfile(OUTSIDE_TARGET['x86_64'], helper)
        write_record(app)
        write_manifest(app)
        seal(app)
        expected_issue, expected_codes = 'output_target', {'output_target', 'provenance'}
    elif name == 'one_slice_fat_helper':
        # The arm64 stub in a one-slice fat container: the same load commands, UUID and architecture name. The record
        # keeps claiming a thin file with the new hash, so the container is the only fact it gets wrong, and the bytes
        # and the record are refused as two separate faults.
        shutil.copyfile(OUTSIDE_TARGET['one-slice-fat'], helper)
        record_path = app / 'Contents/Resources/Evidence/provenance.json'
        record = json.loads(record_path.read_text())
        next(o for o in record['outputs'] if o['rel_path'] == 'Contents/MacOS/pw-runner-client')['sha256'] = fingerprint(helper)
        record_path.write_text(json.dumps(record))
        write_manifest(app)
        seal(app)
        expected_issue, expected_codes = 'output_target', {'output_target', 'provenance_metadata'}
    elif name == 'unlisted_universal_code':
        # Code the manifest does not list and no name implies is found by its header: inventory is no bypass.
        shutil.copyfile(OUTSIDE_TARGET['universal'], app / 'Contents/Resources/plugin.data')
        seal(app)
        expected_issue, expected_codes = 'output_target', {'output_target'}
    elif name == 'x86_64_dsym':
        # A dSYM companion of an x86_64 executable beside a helper is debug data, not code: the bundle stays valid.
        shutil.copytree(OUTSIDE_TARGET['x86_64.dSYM'], app / 'Contents/MacOS/pw-runner-client.dSYM')
        seal(app)
    before = fingerprint(app)
    receipts = work / 'receipts.jsonl'
    modes = {'probe/app': name} if name.startswith('mutate_') else {}
    env = {k: v for k, v in os.environ.items() if not k.startswith('PW_')}
    env.update(CONTROL_SELECTION_RECEIPTS=str(receipts), CONTROL_SELECTION_MODES=json.dumps(modes),
               PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run(['bash', str(repo / 'tests/run.sh')], env=env, capture_output=True, timeout=30)
    (work / 'stdout').write_bytes(result.stdout)
    (work / 'stderr').write_bytes(result.stderr)
    run = json.loads((repo / 'tests/out/runs/default/run.json').read_text())
    integrity = run['artifact_integrity']
    evidence = repo / 'tests/out/runs/default/artifact-integrity'
    issues = json.loads((evidence / 'inspection.json').read_text())
    executed = [json.loads(line)['id'] for line in receipts.read_text().splitlines()]
    valid = name in ('valid', 'worker_continuous_clock', 'x86_64_dsym')
    assert result.returncode == (0 if valid else 1), (name, result.stderr)
    assert run['ok'] is valid
    assert integrity['valid_before'] is (expected_issue is None)
    if expected_issue:
        assert expected_issue in {e['code'] for e in issues['errors']}, issues
        if expected_codes is not None:
            assert {e['code'] for e in issues['errors']} == expected_codes, issues['errors']
        assert executed == ['probe/offline'], executed
        assert run['completion'] == dict(selected=3, completed=1, unrun=2, skipped=0)
        assert fingerprint(app) == before, 'inspection repaired or modified damaged input'
        assert integrity['unchanged'] is True
        if name == 'resigned_stale_manifest':
            assert all(s['returncode'] == 0 for s in issues['signatures'])
        if name == 'host_imports_sandbox':
            assert all(s['returncode'] == 0 for s in issues['signatures'])
            assert issues['host_invariance']['sandbox_symbols'] == ['_sandbox_check'], issues['host_invariance']
        if name == 'worker_imports_clock':
            assert all(s['returncode'] == 0 for s in issues['signatures'])
            assert issues['worker_clock']['returncode'] == 0, issues['worker_clock']
            assert issues['worker_clock']['forbidden'] == ['_clock_gettime'], issues['worker_clock']
        if name == 'worker_unreadable_imports':
            receipt = issues['worker_clock']
            assert receipt['returncode'] != 0 and receipt.get('error') and receipt['undefined'] is None, receipt
    else:
        assert executed == ['probe/app', 'probe/worker', 'probe/offline']
        assert issues['host_invariance']['returncode'] == 0, issues['host_invariance']
        assert issues['host_invariance']['sandbox_symbols'] == [], issues['host_invariance']
        assert issues['worker_clock']['returncode'] == 0 and issues['worker_clock']['forbidden'] == [], issues['worker_clock']
        assert issues['output_target'] and not any(o['target_problems'] for o in issues['output_target']), issues['output_target']
        if name == 'x86_64_dsym':
            assert not any('.dSYM' in o['path'] for o in issues['output_target']), 'debug data was inspected as code'
        if name == 'worker_continuous_clock':
            # The permitted continuous clock is read from the worker's real imports.
            assert '_mach_continuous_time' in issues['worker_clock']['undefined'], issues['worker_clock']
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
        'invalid_manifest', 'external_helper', 'host_imports_sandbox', 'worker_imports_clock',
        'worker_continuous_clock', 'worker_unreadable_imports', 'missing_record', 'stale_record',
        'contradictory_record', 'x86_64_helper', 'one_slice_fat_helper', 'unlisted_universal_code', 'x86_64_dsym',
        'mutate_pass', 'mutate_fail', 'mutate_crash')]
    (out / 'controls.json').write_text(json.dumps(cases, indent=2) + '\n')
    print(f'{len(cases)} artifact controls passed')
