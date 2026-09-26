"""Exercise real staging/cleanup with independent fake signing and launchd tools."""
import json
from pathlib import Path
import plistlib
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/fixtures/byoxpc'))
from session import cleanup, command, install


def main():
    out = Path(sys.argv[1]).resolve()
    completed = []
    modes = ('success', 'no_entitlements', 'bad_source_signature', 'entitlement_diagnostic',
             'malformed_entitlements', 'sign_failure', 'partial_install', 'unowned_plist',
             'malformed_install_reply', 'wrong_team', 'changed_entitlements', 'helper_changed',
             'connection_failure', 'remove_failure', 'remove_warning', 'remove_lies', 'launchctl_equipment',
             'registered_unowned_plist', 'uncertain_install', 'uncertain_no_record',
             'adhoc_noauth', 'original_output_deleted', 'staging_delete_failure', 'repeated_cleanup')
    setup_ok = {'success', 'no_entitlements', 'remove_failure', 'remove_warning', 'remove_lies', 'registered_unowned_plist', 'adhoc_noauth', 'original_output_deleted', 'staging_delete_failure', 'repeated_cleanup'}
    retained = {'unowned_plist', 'remove_failure', 'remove_warning', 'remove_lies', 'registered_unowned_plist', 'uncertain_no_record'}
    for mode in modes:
        work = out / mode
        app = work / 'Selected.app'
        source = app / 'Contents/XPCServices/PWRunner.xpc'
        binary_dir = source / 'Contents/MacOS'
        binary_dir.mkdir(parents=True)
        info = {'CFBundleIdentifier': 'fixture.source', 'CFBundleExecutable': 'PWRunner',
                'CFBundlePackageType': 'XPC!', 'PWRunnerRequireSignedCaller': True,
                'PWRunnerAllowedIdentifiers': ['pw-runner-client']}
        (source / 'Contents/Info.plist').write_bytes(plistlib.dumps(info))
        for name in ('PWRunner', 'pw-probe-runner', 'sb_api_validator'):
            (binary_dir / name).write_bytes(('original ' + name).encode())
        client = app / 'Contents/MacOS/pw-runner-client'
        client.parent.mkdir(parents=True)
        client.write_bytes(b'original client')
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
            result = command(destination, ['/usr/bin/python3', ROOT / 'tests/fixtures/byoxpc/tools.py',
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
                        launch_agents=work / 'LaunchAgents',
                        variant='adhoc_noauth' if mode == 'adhoc_noauth' else 'team')
            except Exception as exc:
                errors['setup'] = str(exc)
            assert ('setup' not in errors) == (mode in setup_ok), (mode, errors)
            state = json.loads(state_path.read_text())
            durable = Path(state['state_path'])
            staging = Path(state['staging'])
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
            assert env.exists() == (mode in setup_ok and mode != 'original_output_deleted'), (mode, errors)
            actual_source = {str(p.relative_to(app)): p.read_bytes() for p in app.rglob('*') if p.is_file()}
            assert source_bytes == actual_source, 'selected app was changed'
            os_state = json.loads(Path(config['state']).read_text())
            assert unrelated in os_state['runners'], 'unrelated registration removed'
            if mode not in retained:
                assert os_state['runners'] == [unrelated] and not os_state['loaded'], (mode, os_state)
            receipts = [json.loads(line) for line in Path(config['receipts']).read_text().splitlines()]
            installs = [r for r in receipts if r['argv'][1:3] == ['runner', 'install']]
            assert len(installs) <= 1
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
