"""Recursive verification controls on never-launched, ad-hoc sealed copies.

No signing identity, launchd service or GUI session is involved. Every copy
lives in owned temporary staging; the installer runs with a fixture registry
and HOME supplied only to its child process, and never bootstraps. A small
Swift probe compiles the unchanged host core and calls only its static equipment
binder; it never launches a service or worker.
"""
import json
import hashlib
import os
from pathlib import Path
import plistlib
import secrets
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/fixtures/caller_auth'))
sys.path.insert(0, str(ROOT / 'tests/lib'))
import build_context
from bundle import SERVICE, command, inventory, save, signature
from build_receipt import record_build
from porcelain_fixture import decode_fixture

HELPERS = {'worker': 'Contents/MacOS/pw-probe-runner', 'unentitled_worker': 'Contents/MacOS/pw-probe-runner-unentitled'}
CODE_PAGE_OFFSET = 4096
INVENTORY_FAULTS = ('missing', 'duplicate_role', 'wrong_path', 'wrong_hash', 'wrong_contract',
                    'unknown_field', 'wrong_identity', 'escaping_path', 'substituted_path',
                    'resigned_stale_hash', 'nonempty_unentitled', 'wrong_cdhash', 'wrong_team', 'wrong_identifier')


def build_binding_probe(out, app):
    """Retain copied source/commands; put SwiftPM products in case scratch."""
    scratch_root = os.environ.get('PW_TEST_SCRATCH')
    assert scratch_root, 'binding probe requires dispatcher-owned PW_TEST_SCRATCH'
    scratch = Path(scratch_root).resolve() / 'equipment-binding-probe'
    receipt = out / 'binding-probe'
    receipt.mkdir()
    package = receipt / 'package'
    shutil.copytree(ROOT / 'runner/Sources', package / 'Sources')
    build_context.write_swift_context(package / 'Sources/PWRunnerCore/PWBuildContext.swift',
                                      build_context.candidate_contract(app))
    source = package / 'Sources/EquipmentBindingProbe'
    source.mkdir()
    shutil.copyfile(ROOT / 'tests/suites/preflight/equipment_binding_probe.swift', source / 'main.swift')
    (package / 'Package.swift').write_text(
        '// swift-tools-version: 5.10\nimport PackageDescription\n'
        'let package = Package(name: "EquipmentBindingProbe", platforms: [.macOS("26.0")], targets: [\n'
        '    .target(name: "PWCWorkerShim"),\n'
        '    .target(name: "PWRunnerCore", dependencies: ["PWCWorkerShim"],\n'
        '            swiftSettings: [.define("PW_PACKAGED_BUILD"), .unsafeFlags(["-enable-testing"])]),\n'
        '    .executableTarget(name: "EquipmentBindingProbe", dependencies: ["PWRunnerCore"])])\n')
    command(receipt / 'build', ['swift', 'build', '--jobs', '2', '--package-path', package,
            '--scratch-path', scratch, '--product', 'EquipmentBindingProbe'], timeout=300)
    return record_build(package, receipt, scratch, 'EquipmentBindingProbe', swift_command=['swift'])


def main(app, out, pw):
    app = app.resolve()
    before = inventory(app)
    save(out / 'source-before.json', before)
    observations = {}
    binding_probe = build_binding_probe(out, app)
    with tempfile.TemporaryDirectory(prefix='pw-byoxpc-verify-', dir='/private/tmp') as temporary:
        staging = Path(temporary).resolve()
        home = staging / 'home'
        (home / 'Library/LaunchAgents').mkdir(parents=True)
        registry = staging / 'registry/runners.json'
        registry.parent.mkdir()
        env = dict(os.environ, HOME=str(home), PW_RUNNER_REGISTRY=str(registry))

        def cli(label, args, *, code):
            result = subprocess.run([str(pw), *map(str, args)], env=env, capture_output=True, timeout=60)
            directory = out / label
            directory.mkdir(parents=True)
            (directory / 'stdout').write_bytes(result.stdout)
            (directory / 'stderr').write_bytes(result.stderr)
            save(directory / 'receipt.json', dict(argv=list(map(str, args)), returncode=result.returncode))
            assert result.returncode == code, (label, result.returncode, result.stdout, result.stderr)
            return result

        def verification(name, bundle):
            rows = {}
            for label, args in (('outer', ['--verify', '--verbose=2', bundle]),
                                ('deep', ['--verify', '--deep', '--strict', '--verbose=2', bundle]),
                                *[(role, ['--verify', '--verbose=2', bundle / relative]) for role, relative in HELPERS.items()]):
                rows[label] = command(out / name / ('verify-' + label), ['/usr/bin/codesign', *args], check=False)['returncode']
            observations[name] = rows
            return rows

        def copy(name):
            service = 'com.policywitness.test.verification.s' + secrets.token_hex(12)
            bundle = staging / name / 'PWRunner.xpc'
            bundle.parent.mkdir()
            command(out / name / 'copy', ['/usr/bin/ditto', app / SERVICE, bundle])
            info_path = bundle / 'Contents/Info.plist'
            info = plistlib.loads(info_path.read_bytes())
            info['CFBundleIdentifier'] = service
            info.pop('PWRunnerRequireSignedCaller', None)
            info.pop('PWRunnerAllowedIdentifiers', None)
            info_path.write_bytes(plistlib.dumps(info))
            # This is a never-launched ad-hoc fixture. Give both workers and
            # validator the same ad-hoc team context, then independently emit
            # the signing-dependent inventory before sealing the renamed host.
            equipment_path = bundle / 'Contents/Resources/worker-equipment.json'
            equipment = json.loads(equipment_path.read_text())
            save(out / name / 'source-equipment.json', equipment)
            for helper in ('pw-probe-runner', 'pw-probe-runner-unentitled', 'sb_api_validator'):
                command(out / name / ('sign-' + helper), ['/usr/bin/codesign', '--force', '--options', 'runtime', '-s', '-', bundle / 'Contents/MacOS' / helper])
            for row in equipment['workers']:
                binary = bundle / row['relative_path']
                signed = signature(binary, out / name / ('signature-' + row['role']))
                row['sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
                row['cdhash'] = signed['CDHash']; row['identifier'] = signed['Identifier']
                row['team_id'] = None if signed['TeamIdentifier'] == 'not set' else signed['TeamIdentifier']
                readback = out / name / ('entitlements-' + row['role'])
                command(readback, ['/usr/bin/codesign', '-d', '--entitlements', '-', '--xml', binary])
                raw = (readback / 'stdout').read_bytes()
                entitlements = plistlib.loads(raw) if raw.strip() else {}
                assert isinstance(entitlements, dict)
                row['entitlements_xml'] = plistlib.dumps(entitlements).decode()
            equipment_path.write_text(json.dumps(equipment, indent=2) + '\n')
            command(out / name / 'seal', ['/usr/bin/codesign', '--force', '--options', 'runtime', '-s', '-', bundle], timeout=90)
            intact = verification(name + '-intact', bundle)
            assert intact == {'outer': 0, 'deep': 0, 'worker': 0, 'unentitled_worker': 0}, intact
            return service, bundle

        def corrupt(name, bundle, role):
            # One signed byte in a mapped code page; the signature blob stays
            # intact. The copy is never launched.
            worker = bundle / HELPERS[role]
            with worker.open('r+b') as stream:
                stream.seek(CODE_PAGE_OFFSET)
                value = stream.read(1)
                assert value, 'expected a Mach-O code page'
                stream.seek(CODE_PAGE_OFFSET)
                stream.write(bytes([value[0] ^ 1]))
            save(out / name / 'corruption.json', dict(offset=CODE_PAGE_OFFSET, old=value[0], new=value[0] ^ 1, executed=False))
            rows = verification(name + '-corrupt', bundle)
            assert rows['deep'] != 0 and rows[role] != 0, ('corruption must fail recursive and individual verification', rows)
            return rows

        install_args = ['runner', 'install', '--kind', 'byoxpc', '--scope', 'user', '--allow-adhoc', '--skip-bootstrap']

        for role in HELPERS:
            refused_name, validated_name = 'refused-' + role, 'validated-' + role
            # A changed signed helper must fail installation before registration.
            service, bundle = copy(refused_name)
            corrupt(refused_name, bundle, role)
            refused = cli(refused_name + '/install', [*install_args, '--bundle', bundle], code=2)
            assert b'codesign verify failed' in refused.stderr, refused.stderr
            assert not registry.exists() or not json.loads(registry.read_text())['runners']

            # Validate the independently changed helper after registration.
            service, bundle = copy(validated_name)
            installed = json.loads(cli(validated_name + '/install', [*install_args, '--bundle', bundle], code=0).stdout)
            assert installed['result']['ok'] is True and installed['data']['runner']['state'] == 'installed'
            runner_id = installed['data']['runner']['id']
            try:
                corrupt(validated_name, bundle, role)
                data = json.loads(cli(validated_name + '/validate', ['runner', 'validate'], code=0).stdout)['data']
                failures = data.get('failures')
                assert data.get('invalid') == 1 and isinstance(failures, list), data
                assert [f['binary'] for f in failures if f['binary'] != 'equipment_inventory'] == ['bundle', role], failures
                for failure in failures:
                    assert failure['runner_id'] == runner_id and failure['service_name'] == service
                    assert 'codesign verify failed' in failure['error'] or failure['binary'] == 'equipment_inventory', failure
                listed = json.loads(cli(validated_name + '/list', ['runner', 'list'], code=0).stdout)['data']['runners']
                assert listed[0]['id'] == runner_id and listed[0]['signature']['valid'] is False
                assert listed[0][role + '_signature']['valid'] is False
                for other in ('worker', 'validator', 'unentitled_worker'):
                    if other != role:
                        assert listed[0][other + '_signature']['valid'] is True
            finally:
                removed = json.loads(cli(validated_name + '/remove', ['runner', 'remove', '--id', runner_id, '--skip-bootout'], code=0).stdout)
                assert removed['data'].get('cleanup_retained') is not True, removed
        # Valid signatures cannot conceal a mismatched or malformed service
        # inventory. Each mutation is made on a never-launched copy and the
        # enclosing service is re-sealed, leaving the independent inventory
        # verifier as the refusal boundary rather than damaged code signing.
        for fault in INVENTORY_FAULTS:
            name = 'inventory-' + fault
            _, bundle = copy(name)
            path = bundle / 'Contents/Resources/worker-equipment.json'
            original_inventory = path.read_bytes()
            original_bundle = inventory(bundle)
            backup = bundle.parent / 'original.xpc'
            command(out / name / 'backup', ['/usr/bin/ditto', bundle, backup])
            assert inventory(backup) == original_bundle
            save(out / name / 'original-bundle.json', original_bundle)
            (out / name / 'original-equipment.json').write_bytes(original_inventory)
            expected_error = {
                'missing': 'equipment inventory',
                'duplicate_role': 'equipment inventory must contain exactly one selected',
                'wrong_path': 'invalid selected equipment inventory row',
                'wrong_hash': 'selected equipment differs from its sealed inventory',
                'wrong_cdhash': 'selected equipment differs from its sealed inventory',
                'wrong_team': 'unentitled equipment differs from its sealed inventory',
                'wrong_identifier': 'selected equipment differs from its sealed inventory',
                'wrong_contract': 'unsupported or malformed worker equipment inventory',
                'unknown_field': 'unknown field',
                'escaping_path': 'invalid selected equipment inventory row',
                'substituted_path': 'invalid selected equipment inventory row',
                'resigned_stale_hash': 'selected equipment differs from its sealed inventory',
                'nonempty_unentitled': 'unentitled equipment entitlement dictionary is invalid',
            }.get(fault)
            baseline = None
            try:
                if fault == 'wrong_identity':
                    command(out / name / 'binding-baseline', [binding_probe, bundle])
                    baseline = decode_fixture((out / name / 'binding-baseline/stdout').read_bytes(), 'binding')
                    save(out / name / 'binding-baseline/projection.json', baseline)
                    assert baseline['compiled_identity'] == json.loads(original_inventory)['worker_identity'], baseline
                    assert baseline['inventory']['status'] == 'verified' and baseline['inventory']['seal_osstatus'] == 0, baseline
                    assert 'failure_reason' not in baseline and len(baseline['executable_paths']) == 1, baseline
                    assert Path(baseline['executable_paths'][0]).samefile(bundle / HELPERS['worker']), baseline
                    assert [(r['role'], r['source'], r['status']) for r in baseline['bindings']] == [('selected', 'packaged', 'bound'), ('unentitled', 'packaged', 'bound')], baseline
                equipment = json.loads(original_inventory)
                rows_by_role = {row['role']: row for row in equipment['workers']}
                selected_row = rows_by_role['selected']
                if fault == 'missing':
                    path.unlink()
                else:
                    if fault == 'duplicate_role': rows_by_role['unentitled']['role'] = 'selected'
                    elif fault == 'wrong_path': selected_row['relative_path'] = '../outside'
                    elif fault == 'wrong_hash': selected_row['sha256'] = 'f' * 64
                    elif fault == 'wrong_cdhash':
                        old = selected_row['cdhash']
                        selected_row['cdhash'] = ('0' if old[0] != '0' else '1') + old[1:]
                    elif fault == 'wrong_team': rows_by_role['unentitled']['team_id'] = 'WRONGTEAM'
                    elif fault == 'wrong_identifier': selected_row['identifier'] += '.substituted'
                    elif fault == 'wrong_contract': equipment['contract'] = 'test:foreign'
                    elif fault == 'unknown_field': equipment['unknown'] = True
                    elif fault == 'wrong_identity':
                        # Well-formed but incompatible, not a syntax-error surrogate.
                        old = equipment['worker_identity']
                        equipment['worker_identity'] = ('0' if old[0] != '0' else '1') + old[1:]
                    elif fault == 'escaping_path':
                        escaped = bundle.parent / 'escaped-worker'
                        shutil.copy2(bundle / HELPERS['worker'], escaped)
                        command(out / name / 'verify-escaped', ['/usr/bin/codesign', '--verify', '--strict', escaped])
                        assert hashlib.sha256(escaped.read_bytes()).hexdigest() == selected_row['sha256']
                        selected_row['relative_path'] = '../escaped-worker'
                    elif fault == 'substituted_path':
                        selected_row['relative_path'] = HELPERS['unentitled_worker']
                    elif fault in ('resigned_stale_hash', 'nonempty_unentitled'):
                        role = 'selected' if fault == 'resigned_stale_hash' else 'unentitled'
                        row = rows_by_role[role]
                        binary = bundle / row['relative_path']
                        old_hash = row['sha256']
                        args = ['/usr/bin/codesign', '--force', '--options', 'runtime', '-s', '-']
                        if fault == 'resigned_stale_hash':
                            # Force different signed bytes; refresh all other metadata
                            # so only the recorded SHA-256 remains stale.
                            args += ['--identifier', 'com.policywitness.test.resigned-worker']
                        else:
                            entitlements = out / name / 'nonempty-entitlements.plist'
                            entitlements.write_bytes(plistlib.dumps({'com.apple.security.cs.allow-jit': True}))
                            args += ['--entitlements', entitlements]
                        command(out / name / 'resign-worker', [*args, binary])
                        signed = signature(binary, out / name / 'resigned-signature')
                        readback = out / name / 'resigned-entitlements'
                        command(readback, ['/usr/bin/codesign', '-d', '--entitlements', '-', '--xml', binary])
                        raw = (readback / 'stdout').read_bytes()
                        observed = plistlib.loads(raw) if raw.strip() else {}
                        assert isinstance(observed, dict)
                        actual_hash = hashlib.sha256(binary.read_bytes()).hexdigest()
                        assert actual_hash != old_hash, 're-signing must change the signed bytes'
                        row.update(cdhash=signed['CDHash'], identifier=signed['Identifier'],
                                   team_id=None if signed['TeamIdentifier'] == 'not set' else signed['TeamIdentifier'],
                                   entitlements_xml=plistlib.dumps(observed).decode())
                        if fault == 'nonempty_unentitled':
                            assert observed == {'com.apple.security.cs.allow-jit': True}, observed
                            row['sha256'] = actual_hash
                        else:
                            assert observed == {}, observed
                            assert row['sha256'] == old_hash
                        save(out / name / 'signed-mutation.json', dict(role=role, old_sha256=old_hash,
                             actual_sha256=actual_hash, recorded_sha256=row['sha256'], entitlements=observed))
                    path.write_text(json.dumps(equipment))
                if path.exists():
                    (out / name / 'mutated-equipment.json').write_bytes(path.read_bytes())
                else:
                    save(out / name / 'mutated-equipment-absent.json', {'exists': False})
                command(out / name / 'reseal', ['/usr/bin/codesign', '--force', '--options', 'runtime', '-s', '-', bundle])
                rows = verification(name + '-valid-seal', bundle)
                assert all(code == 0 for code in rows.values()), (fault, rows)
                for role, relative in HELPERS.items():
                    binary = bundle / relative
                    signature(binary, out / name / ('mutated-signature-' + role))
                    command(out / name / ('mutated-entitlements-' + role),
                            ['/usr/bin/codesign', '-d', '--entitlements', '-', '--xml', binary])
                if fault == 'wrong_identity':
                    # Installation authenticates the selected service's own
                    # source inventory. Compatibility belongs to that host's
                    # compiled layout, not the controller's build identity.
                    command(out / name / 'binding-refused', [binding_probe, bundle])
                    refused_binding = decode_fixture((out / name / 'binding-refused/stdout').read_bytes(), 'binding')
                    save(out / name / 'binding-refused/projection.json', refused_binding)
                    assert refused_binding['compiled_identity'] == baseline['compiled_identity']
                    assert refused_binding['inventory']['seal_osstatus'] == 0, refused_binding
                    assert refused_binding['inventory']['status'] == 'refused', refused_binding
                    assert refused_binding['inventory']['reason'] == 'worker_identity_mismatch', refused_binding
                    assert refused_binding['failure_stage'] == 'equipment' and refused_binding['failure_code'] == 'equipment_binding_refused', refused_binding
                    assert refused_binding['failure_reason'] == 'worker_identity_mismatch', refused_binding
                    assert 'executable_paths' not in refused_binding and refused_binding['bindings'] == [] and refused_binding['entitlements'] == [], refused_binding
                else:
                    refused = cli(name + '/install', [*install_args, '--bundle', bundle], code=2)
                    assert expected_error.encode() in refused.stderr, (fault, expected_error, refused.stderr)
                    assert b'codesign verify failed' not in refused.stderr, refused.stderr
                assert not registry.exists() or not json.loads(registry.read_text()).get('runners'), 'inventory refusal registered a runner'
                assert not list((home / 'Library/LaunchAgents').iterdir()), 'inventory refusal published a launchd plist'
            finally:
                # These copies never launch or bootstrap. Restore the complete
                # original signed tree, including host signature/CodeResources,
                # and independently verify both exact bytes and valid seals.
                assert bundle.parent == staging / name and backup.parent == bundle.parent
                assert inventory(backup) == original_bundle, 'owned original backup changed'
                shutil.rmtree(bundle)
                command(out / name / 'restore', ['/usr/bin/ditto', backup, bundle])
                assert inventory(bundle) == original_bundle, 'original bundle bytes not restored'
                assert path.read_bytes() == original_inventory
                restored = verification(name + '-restored', bundle)
                assert all(code == 0 for code in restored.values()), restored
                if fault == 'wrong_identity' and baseline is not None:
                    command(out / name / 'binding-restored', [binding_probe, bundle])
                    restored_binding = decode_fixture((out / name / 'binding-restored/stdout').read_bytes(), 'binding')
                    save(out / name / 'binding-restored/projection.json', restored_binding)
                    # Security may spell the same inode through /tmp or
                    # /private/tmp. Compare those paths by filesystem identity;
                    # every other observation must be exactly restored.
                    comparable = json.loads(json.dumps(restored_binding))
                    assert Path(comparable['inventory']['path']).samefile(baseline['inventory']['path'])
                    comparable['inventory']['path'] = baseline['inventory']['path']
                    assert len(comparable['bindings']) == len(baseline['bindings'])
                    for actual, expected in zip(comparable['bindings'], baseline['bindings']):
                        assert Path(actual['path']).samefile(expected['path']), (actual, expected)
                        actual['path'] = expected['path']
                    assert len(comparable['executable_paths']) == len(baseline['executable_paths'])
                    for actual, expected in zip(comparable['executable_paths'], baseline['executable_paths']):
                        assert Path(actual).samefile(expected), (actual, expected)
                    comparable['executable_paths'] = baseline['executable_paths']
                    assert comparable == baseline, (restored_binding, baseline)
                save(out / name / 'restoration.json', dict(exact_bundle_restored=True,
                     exact_inventory_restored=True, signatures=restored,
                     service_executed=False, worker_launched=False))
        final = json.loads(registry.read_text())
        assert not final['runners'] and not final.get('pending_cleanup'), final
        assert not list((home / 'Library/LaunchAgents').iterdir()), 'fixture LaunchAgents not empty'
    save(out / 'observations.json', observations)
    assert inventory(app) == before, 'the selected app changed'
    print(json.dumps(dict(controls=['refused-worker', 'validated-worker', 'refused-unentitled_worker', 'validated-unentitled_worker', *['inventory-' + fault for fault in INVENTORY_FAULTS]], observations=observations)))


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
