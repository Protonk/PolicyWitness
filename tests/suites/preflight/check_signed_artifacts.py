"""Real codesign controls, mutating only a disposable, never-launched app copy."""
import hashlib
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/fixtures/caller_auth'))
from bundle import command, inventory, save, sign
sys.path.insert(0, str(ROOT / 'tests/lib'))
from artifact import inspect
import build_provenance
import signer_check


def main(source, out, identity):
    before = inventory(source)
    save(out / 'source-before.json', before)
    scenarios = []
    try:
        with tempfile.TemporaryDirectory(prefix='pw-artifact-control-', dir='/private/tmp') as temporary:
            app = Path(temporary) / 'PolicyWitness.app'
            command(out / 'copy', ['/usr/bin/ditto', source, app])

            def observe(name):
                result = inspect(app)
                save(out / (name + '.json'), result)
                scenarios.append(name)
                return result

            assert observe('valid')['ok'], 'copied app must start valid'
            helper = app / 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner'
            original = source / helper.relative_to(app)
            helper.unlink()
            missing = observe('missing_helper')
            assert not missing['ok'] and any(e['code'] == 'required_component' for e in missing['errors'])
            shutil.copy2(original, helper)
            with helper.open('r+b') as stream:
                stream.seek(4096)
                value = stream.read(1)
                assert value, 'expected a Mach-O code page'
                stream.seek(4096)
                stream.write(bytes([value[0] ^ 1]))
            damaged = observe('damaged_signature')
            assert not damaged['ok'] and any(e['code'] == 'signature' for e in damaged['errors'])
            shutil.copy2(original, helper)
            assert observe('restored')['ok'], 'restoration must recover the original valid copy'

            # The signer check build.sh runs after the seal: the copy's own leaf
            # identity signs every executable; a helper re-signed ad hoc, which
            # the seal, the deep verification and the inspector all accept, is
            # named, and nothing else is.
            leaf = signer_check.signature(app / 'Contents/MacOS/policy-witness')['leaf']
            assert leaf and signer_check.problems(app, leaf) == [], 'every executable must carry the app leaf identity'
            top_helper = app / 'Contents/MacOS/sbpl-check'
            command(out / 'adhoc-helper', ['/usr/bin/codesign', '--force', '--options', 'runtime', '-s', '-', top_helper])
            # The inspector's signer-consistency rule names the one executable whose signer differs from the controller's.
            inconsistent = observe('adhoc_helper_inspected')
            assert not inconsistent['ok'] and [e['path'] for e in inconsistent['errors'] if e['code'] == 'signer'] == ['Contents/MacOS/sbpl-check'], inconsistent['errors']
            named = signer_check.problems(app, leaf)
            save(out / 'signer-adhoc.json', named)
            scenarios.append('adhoc_helper_named')
            assert named == [f'Contents/MacOS/sbpl-check: signed by ad hoc, not {leaf}'], named
            # The command build.sh runs: status 1 and the header naming the identity, over the same copy.
            cli = subprocess.run([sys.executable, '-B', str(ROOT / 'tests/lib/signer_check.py'), str(app), leaf],
                                 capture_output=True, text=True, timeout=120)
            save(out / 'signer-cli.json', dict(argv=cli.args, returncode=cli.returncode, stdout=cli.stdout, stderr=cli.stderr))
            scenarios.append('signer_cli_refuses')
            assert cli.returncode == 1 and f'executables or seals not signed by {leaf} with the hardened runtime' in cli.stderr and 'sbpl-check' in cli.stderr, cli.stderr
            shutil.copy2(source / top_helper.relative_to(app), top_helper)
            assert signer_check.problems(app, leaf) == [], 'restoration must recover the signer check'
            assert observe('adhoc_helper_restored')['ok']

            service = app / 'Contents/XPCServices/PWRunner.xpc'
            info_path = service / 'Contents/Info.plist'
            info = plistlib.loads(info_path.read_bytes())
            info['PWArtifactIntegrityControl'] = True
            info_path.write_bytes(plistlib.dumps(info))
            # Change a sealed resource, then sign inside-out without refreshing
            # the manifest. This reproduces a valid signature over stale evidence.
            sign(service, identity, info['CFBundleIdentifier'], out / 'sign-service')
            app_id = plistlib.loads((app / 'Contents/Info.plist').read_bytes())['CFBundleIdentifier']
            sign(app, identity, app_id, out / 'sign-app')
            command(out / 'verify-resigned', ['/usr/bin/codesign', '--verify', '--deep', '--strict', app])
            stale = observe('resigned_stale_manifest')
            assert all(s['returncode'] == 0 for s in stale['signatures']), stale
            assert not stale['ok'] and {e['code'] for e in stale['errors']} == {'manifest_hash', 'provenance_hash'}, stale
            assert any(e['path'] == 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/PWRunner'
                       for e in stale['errors']), stale

            # Semantically faulty records, validly re-signed with their manifest entry refreshed, so only the
            # record's own checks can reject them: every signature verifies and the inspector still refuses.
            faulty_app = Path(temporary) / 'Record.app'
            command(out / 'copy-record-faults', ['/usr/bin/ditto', source, faulty_app])
            record_path = faulty_app / 'Contents/Resources/Evidence/provenance.json'
            manifest_path = faulty_app / 'Contents/Resources/Evidence/manifest.json'
            original_record, original_manifest = record_path.read_bytes(), manifest_path.read_bytes()
            helper_rel = 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner'

            def observe_record(name):
                result = inspect(faulty_app)
                save(out / (name + '.json'), result)
                scenarios.append(name)
                return result

            helper = lambda r: next(o for o in r['outputs'] if o['rel_path'] == helper_rel)
            # Each fault with the exact codes it must produce: the record's shape (`provenance`), its agreement with the
            # bytes, the manifest and the load commands, and with codesign's own display of each nested signature.
            faults = {
                'resigned_record_wrong_sdk': (lambda r: helper(r).__setitem__('sdk', '1.0'), {'provenance_metadata', 'provenance'}),
                'resigned_record_wrong_hash': (lambda r: helper(r).__setitem__('sha256', 'f' * 64), {'provenance_hash'}),
                'resigned_record_missing_output': (lambda r: r['outputs'].remove(helper(r)), {'provenance_output', 'provenance'}),
                'resigned_record_duplicate_output': (lambda r: r['outputs'].append(dict(helper(r))), {'provenance_output', 'provenance'}),
                'resigned_record_controller_hash': (lambda r: next(o for o in r['outputs'] if o['rel_path'] == 'Contents/MacOS/policy-witness').__setitem__('sha256', 'a' * 64),
                                                    {'provenance_hash', 'provenance'}),
                'resigned_record_unsupported': (lambda r: r.__setitem__('schema_version', 99), {'provenance'}),
                'resigned_record_null_section': (lambda r: r.__setitem__('toolchain', None), {'provenance'}),
                'resigned_record_missing_section': (lambda r: r.pop('configuration'), {'provenance'}),
                'resigned_record_wrong_type': (lambda r: r['source'].__setitem__('dirty', 'no'), {'provenance'}),
                'resigned_record_null_deployment_target': (lambda r: r['configuration'].__setitem__('deployment_target', None), {'provenance'}),
                'resigned_record_malformed_request': (lambda r: r['configuration']['requests'].__setitem__('SDKROOT', dict(state='maybe')), {'provenance'}),
                'resigned_record_null_required_observation': (lambda r: r['toolchain']['compilers']['c'].__setitem__('observed', None), {'provenance'}),
                'resigned_record_linker_tool': (lambda r: helper(r)['tools'][0].__setitem__('version', helper(r)['tools'][0]['version'] + '.1'),
                                                {'provenance_metadata'}),
                'resigned_record_signature_claim': (lambda r: helper(r)['signature'].__setitem__('runtime', not helper(r)['signature']['runtime']),
                                                    {'provenance_signature'}),
            }
            for name, (mutate, codes) in faults.items():
                record = json.loads(original_record)
                mutate(record)
                record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
                manifest = json.loads(original_manifest)
                for entry in manifest['entries']:
                    if entry['rel_path'] == 'Contents/Resources/Evidence/provenance.json':
                        entry['sha256'] = hashlib.sha256(record_path.read_bytes()).hexdigest()
                manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
                sign(faulty_app, identity, app_id, out / ('sign-app-' + name))
                command(out / ('verify-' + name), ['/usr/bin/codesign', '--verify', '--deep', '--strict', faulty_app])
                faulty = observe_record(name)
                assert all(s['returncode'] == 0 for s in faulty['signatures']), (name, faulty['signatures'])
                assert not faulty['ok'] and {e['code'] for e in faulty['errors']} == codes, (name, faulty['errors'])
            record_path.write_bytes(original_record)
            manifest_path.write_bytes(original_manifest)
            sign(faulty_app, identity, app_id, out / 'sign-app-restored-record')
            assert observe_record('resigned_record_restored')['ok'], 'the restored record and manifest pass again under the new seal'
            # A record for other bytes with the same inventory: the helper's bytes change, the record keeps the old hash.
            with (faulty_app / helper_rel).open('ab') as stream:
                stream.write(b'\0other bytes')
            swapped = observe_record('swapped_record_other_bytes')
            assert not swapped['ok'] and 'provenance_hash' in {e['code'] for e in swapped['errors']}, swapped['errors']

            # The output target, inspected on copies whose every signature verifies and whose manifest hashes agree with
            # the bytes: an x86_64 helper and an unlisted universal library, real Mach-O signed with the identity, each fail
            # for architecture. A record that still claims the target for the x86_64 bytes, and one that describes them
            # truthfully, are each a separate record fault beside the bytes' own.
            target_app = Path(temporary) / 'Target.app'
            command(out / 'copy-target-faults', ['/usr/bin/ditto', source, target_app])
            record_path = target_app / 'Contents/Resources/Evidence/provenance.json'
            manifest_path = target_app / 'Contents/Resources/Evidence/manifest.json'
            target_record, target_manifest = record_path.read_bytes(), manifest_path.read_bytes()
            program = Path(temporary) / 'outside.c'
            program.write_text('int main(void) { return 0; }\n')
            built = {}
            for name, flags in (('x86_64', ['-arch', 'x86_64']), ('universal-dylib', ['-arch', 'arm64', '-arch', 'x86_64', '-dynamiclib'])):
                built[name] = Path(temporary) / name
                command(out / f'compile-{name}', ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', *flags, '-mmacosx-version-min=26.0',
                                                  program, '-o', built[name]], timeout=120)
                listed = subprocess.run(['/usr/bin/lipo', '-archs', str(built[name])], capture_output=True, text=True, check=True).stdout.split()
                assert listed == (['x86_64'] if name == 'x86_64' else ['x86_64', 'arm64']), (name, listed)
            top_rel = 'Contents/MacOS/sbpl-check'

            def reseal(name, edit_record, add_library=False):
                """Substitute, sign with the identity, refresh the record and the manifest as described, reseal and inspect."""
                if edit_record is not None:
                    shutil.copy2(built['x86_64'], target_app / top_rel)
                    sign(target_app / top_rel, identity, 'sbpl-check', out / f'sign-helper-{name}')
                if add_library:
                    library = target_app / 'Contents/Resources/plugin.dylib'
                    shutil.copy2(built['universal-dylib'], library)
                    sign(library, identity, 'plugin', out / f'sign-library-{name}')
                record = json.loads(target_record)
                if edit_record is not None:
                    entry = next(o for o in record['outputs'] if o['rel_path'] == top_rel)
                    entry['sha256'] = hashlib.sha256((target_app / top_rel).read_bytes()).hexdigest()
                    entry['signature'] = signer_check.facts(signer_check.signature(target_app / top_rel))
                    edit_record(entry)
                record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
                manifest = json.loads(target_manifest)
                for item in manifest['entries']:
                    if item['rel_path'] in (top_rel, 'Contents/Resources/Evidence/provenance.json'):
                        item['sha256'] = hashlib.sha256((target_app / item['rel_path']).read_bytes()).hexdigest()
                manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
                sign(target_app, identity, app_id, out / f'sign-app-{name}')
                command(out / f'verify-{name}', ['/usr/bin/codesign', '--verify', '--deep', '--strict', target_app])
                result = inspect(target_app)
                save(out / (name + '.json'), result)
                scenarios.append(name)
                assert all(s['returncode'] == 0 for s in result['signatures']), (name, result['signatures'])
                assert not any(e['code'] in ('manifest_hash', 'provenance_hash', 'signer', 'signature') for e in result['errors']), (name, result['errors'])
                return result

            def describe_bytes(entry):
                metadata = build_provenance.output_metadata(target_app / top_rel)
                observed = build_provenance.output_observation(target_app / top_rel)
                entry.update({k: metadata[k] for k in ('uuid', 'platform', 'minos', 'sdk', 'tools')},
                             architectures=observed['architectures'], container=observed['container'])
            claims = reseal('resigned_x86_64_helper_record_claims_target', lambda entry: None)
            assert {e['code'] for e in claims['errors']} == {'output_target', 'provenance_metadata'}, claims['errors']
            assert [e['message'] for e in claims['errors'] if e['code'] == 'output_target'] == ['architecture x86_64, not exactly arm64']
            assert any("record architectures ['arm64'] differs from the bytes ['x86_64']" in e['message'] for e in claims['errors'])
            truthful = reseal('resigned_x86_64_helper_record_describes_bytes', describe_bytes)
            assert {e['code'] for e in truthful['errors']} == {'output_target', 'provenance'}, truthful['errors']
            assert any('not the output target' in e['message'] for e in truthful['errors'] if e['code'] == 'provenance')
            shutil.copy2(source / top_rel, target_app / top_rel)
            unlisted = reseal('resigned_unlisted_universal_library', None, add_library=True)
            assert [(e['code'], e['path']) for e in unlisted['errors']] == [('output_target', 'Contents/Resources/plugin.dylib')] * 2, unlisted['errors']
            # A universal dSYM is debug data in every slice, not an extra executable. Seal it as a resource and
            # require the real inspector to accept the bundle without adding the debug file to the code inventory.
            (target_app / 'Contents/Resources/plugin.dylib').unlink()
            debug = Path(temporary) / 'debug-universal'
            command(out / 'compile-universal-debug', ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-arch', 'arm64',
                                                      '-arch', 'x86_64', '-g', program, '-o', debug], timeout=120)
            dsym = target_app / 'Contents/Resources/debug-universal.dSYM'
            command(out / 'universal-dsym', ['/usr/bin/xcrun', 'dsymutil', debug, '-o', dsym])
            debug_result = reseal('resigned_universal_dsym', None)
            assert debug_result['ok'], debug_result['errors']
            assert len(debug_result['output_target']) == len(build_provenance.FULL_OUTPUTS), debug_result['output_target']
    finally:
        after = inventory(source)
        save(out / 'source-after.json', after)
        assert after == before, 'signed controls changed the selected source app'
    save(out / 'controls.json', scenarios)
    print(f'{len(scenarios)} real signature controls passed')


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3])
