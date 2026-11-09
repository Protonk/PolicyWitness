"""Exercise real staging/cleanup with independent fake signing and launchd tools."""
import json
import hashlib
from pathlib import Path
import plistlib
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/fixtures/byoxpc'))
from session import cleanup, command, install
from contract import WORKER_IDENTITY
from build_context import TEST_CONTRACT


def main():
    out = Path(sys.argv[1]).resolve()
    completed = []
    modes = ('success', 'no_entitlements', 'bad_source_signature', 'entitlement_diagnostic',
             'malformed_entitlements', 'unentitled_entitlements', 'missing_inventory', 'changed_inventory', 'source_reseal_failure', 'sign_failure', 'partial_install', 'unowned_plist',
             'malformed_install_reply', 'wrong_team', 'changed_entitlements', 'helper_changed',
             'connection_failure', 'remove_failure', 'remove_warning', 'remove_lies', 'launchctl_equipment',
             'registered_unowned_plist', 'uncertain_install', 'uncertain_no_record',
             'adhoc_noauth', 'original_output_deleted', 'staging_delete_failure', 'repeated_cleanup', 'registry_nonempty')
    setup_ok = {'success', 'no_entitlements', 'remove_failure', 'remove_warning', 'remove_lies', 'registered_unowned_plist', 'adhoc_noauth', 'original_output_deleted', 'staging_delete_failure', 'repeated_cleanup', 'registry_nonempty'}
    retained = {'unowned_plist', 'remove_failure', 'remove_warning', 'remove_lies', 'registered_unowned_plist', 'uncertain_no_record', 'registry_nonempty'}
    for mode in modes:
        work = out / mode
        app = work / 'Selected.app'
        source = app / 'Contents/XPCServices/PWRunner.xpc'
        binary_dir = source / 'Contents/MacOS'
        binary_dir.mkdir(parents=True)
        info = {'CFBundleIdentifier': 'fixture.source', 'CFBundleExecutable': 'PWRunner',
                'CFBundlePackageType': 'XPC!', 'PWContract': TEST_CONTRACT, 'PWRunnerRequireSignedCaller': True,
                'PWRunnerAllowedIdentifiers': ['pw-runner-client']}
        (source / 'Contents/Info.plist').write_bytes(plistlib.dumps(info))
        for name in ('PWRunner', 'pw-probe-runner', 'pw-probe-runner-unentitled', 'sb_api_validator'):
            (binary_dir / name).write_bytes(('original ' + name).encode())
        client = app / 'Contents/MacOS/pw-runner-client'
        client.parent.mkdir(parents=True)
        client.write_bytes(b'original client')
        worker_roles = [('selected', 'pw-probe-runner'), ('unentitled', 'pw-probe-runner-unentitled')]
        equipment = dict(schema_version=1, contract=TEST_CONTRACT, worker_identity=WORKER_IDENTITY,
                         unsigned_worker_sha256=hashlib.sha256((binary_dir / 'pw-probe-runner').read_bytes()).hexdigest(), workers=[])
        source_entitlements = None if mode == 'no_entitlements' else {'com.apple.security.cs.allow-jit': True, 'fixture.array': ['literal', 42]}
        for role, name in worker_roles:
            equipment['workers'].append(dict(role=role, relative_path='Contents/MacOS/' + name,
                sha256=hashlib.sha256((binary_dir / name).read_bytes()).hexdigest(), cdhash='a' * 40,
                identifier='fixture.source', team_id='FIXTURETEAM',
                entitlements_xml=plistlib.dumps((source_entitlements or {}) if role == 'selected' else {}).decode()))
        resource = source / 'Contents/Resources/worker-equipment.json'
        resource.parent.mkdir()
        if mode != 'missing_inventory':
            if mode == 'changed_inventory': equipment['workers'][0]['sha256'] = 'f' * 64
            resource.write_text(json.dumps(equipment))
        source_bytes = {str(p.relative_to(app)): p.read_bytes() for p in app.rglob('*') if p.is_file()}
        artifacts = work / 'artifacts'
        artifacts.mkdir()
        unrelated = {'id': 'unrelated', 'service_name': 'user.runner', 'scope': 'user', 'bundle_path': '/do/not/touch.xpc'}
        config = {'mode': mode, 'state': str(work / 'os.json'), 'receipts': str(work / 'receipts.jsonl'),
                  'out': str(artifacts), 'source': str(source), 'pw': str(app / 'Contents/MacOS/policy-witness'),
                  'unrelated': unrelated, 'entitlements': None if mode == 'no_entitlements' else
                  {'com.apple.security.cs.allow-jit': True, 'fixture.array': ['literal', 42]}}
        config_path = work / 'config.json'
        config_path.write_text(json.dumps(config))

        def invoke(destination, argv, **kwargs):
            result = command(destination, [sys.executable, '-B', '-S', ROOT / 'tests/fixtures/byoxpc/tools.py',
                                           config_path, *argv], **kwargs)
            if mode in ('uncertain_install', 'uncertain_no_record') and argv[1:3] == ['runner', 'install']:
                # Preserve a tool observation of incomplete execution, as a
                # real timeout/interruption does; cleanup must not infer absence.
                result.update(returncode=None, harness_timeout=True)
                (destination / 'command.json').write_text(json.dumps(result))
                raise TimeoutError('controlled incomplete installation')
            return result

        errors = {}
        env = artifacts / 'runner_env.json'
        state_path = artifacts / 'session.json'
        try:
            try:
                install(config['pw'], app, artifacts, env, 'fixture identity', invoke=invoke,
                        launch_agents=work / 'LaunchAgents', registry_root=work / 'registries',
                        variant='adhoc_noauth' if mode == 'adhoc_noauth' else 'team')
            except Exception as exc:
                errors['setup'] = str(exc)
            assert ('setup' not in errors) == (mode in setup_ok), (mode, errors)
            state = json.loads(state_path.read_text())
            durable = Path(state['state_path'])
            staging = Path(state['staging'])
            assert Path(state['registry_path']).parent.parent == work / 'registries'
            assert json.loads(durable.read_text()) == state, 'durable ownership differs from receipt'
            if mode == 'original_output_deleted':
                config['ownership'] = str(durable)
                config_path.write_text(json.dumps(config))
                shutil.rmtree(artifacts)
                state_path = durable
            if mode == 'staging_delete_failure':
                def fail_delete(path):
                    if path.name == 'PWRunner.xpc':
                        raise OSError('controlled interrupted staging deletion')
                    shutil.rmtree(path)
                try:
                    cleanup(config['pw'], state_path, invoke=invoke, remove_tree=fail_delete)
                    raise AssertionError('injected deletion failure did not fail')
                except RuntimeError:
                    assert durable.exists() and json.loads(durable.read_text())['removed']
                    assert not json.loads(Path(config['state']).read_text())['loaded']
            try:
                cleanup(config['pw'], state_path, invoke=invoke)
                if mode == 'repeated_cleanup':
                    cleanup(config['pw'], state_path, invoke=invoke)
            except Exception as exc:
                errors['cleanup'] = str(exc)
            assert ('cleanup' in errors) == (mode in retained), (mode, errors)
            assert staging.exists() == (mode in retained), (mode, errors)
            assert Path(state['registry_path']).parent.exists() == (mode in retained), (mode, errors)
            assert env.exists() == (mode in setup_ok and mode != 'original_output_deleted'), (mode, errors)
            actual_source = {str(p.relative_to(app)): p.read_bytes() for p in app.rglob('*') if p.is_file()}
            assert source_bytes == actual_source, 'selected app was changed'
            os_state = json.loads(Path(config['state']).read_text())
            if mode == 'registry_nonempty':
                assert os_state['runners'] == [unrelated] and not os_state['loaded'], os_state
            if mode not in retained:
                assert os_state['runners'] == [] and not os_state['loaded'], (mode, os_state)
            receipts = [json.loads(line) for line in Path(config['receipts']).read_text().splitlines()]
            assert all(r['registry_path'] == state['registry_path'] for r in receipts if r['argv'][0] == config['pw'])
            assert not (artifacts / 'verify-host-retired.json').exists()
            installs = [r for r in receipts if r['argv'][1:3] == ['runner', 'install']]
            assert len(installs) <= 1
            reseals = [r for r in receipts if r['argv'][0] == '/usr/bin/codesign' and '-s' in r['argv']]
            assert len(reseals) <= 1
            if installs:
                assert len(reseals) == 1 and reseals[0]['rc'] == 0, 'installer reached before a successful source reseal'
                assert receipts.index(reseals[0]) < receipts.index(installs[0])
                assert reseals[0]['argv'][-1] == state['bundle_path']
                assert reseals[0]['argv'][reseals[0]['argv'].index('-s') + 1] == 'fixture identity'
            if mode in ('missing_inventory', 'changed_inventory', 'source_reseal_failure'):
                assert not installs, 'source equipment/reseal refusal reached installation'

            removals = [r for r in receipts if r['argv'][1:3] == ['runner', 'remove']]
            assert all(r['argv'][3:] == ['--id', 'owned-id'] for r in removals)
            if mode == 'partial_install':
                assert len(removals) == 1, 'pending partial install did not use public removal'
            if mode in ('unowned_plist', 'registered_unowned_plist'):
                assert not any(r['argv'][1] == 'bootout' for r in receipts), 'unowned plist triggered bootout'
                assert not removals, 'unowned plist triggered public removal'
            if mode in ('malformed_install_reply', 'uncertain_install'):
                assert len(removals) == 1, 'missing install output suppressed cleanup'
            (work / 'observations.json').write_text(json.dumps({'errors': errors, 'retained': staging.exists()}, indent=2))
            completed.append(mode)
        finally:
            # Fake tools created no real service. Remove deliberately retained
            # fixture data only after recording/asserting the retention behavior.
            if state_path.exists():
                staging = Path(json.loads(state_path.read_text())['staging'])
                if staging.exists():
                    shutil.rmtree(staging)
        print(f'{mode}: ok', flush=True)
    (out / 'controls.json').write_text(json.dumps(completed, indent=2) + '\n')
    print(f'{len(completed)} BYOXPC ownership controls passed')


if __name__ == '__main__':
    main()
