"""Real codesign controls, mutating only a disposable, never-launched app copy."""
import json
from pathlib import Path
import plistlib
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/fixtures/caller_auth'))
from bundle import command, inventory, save, sign
sys.path.insert(0, str(ROOT / 'tests/lib'))
from artifact import inspect
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
            assert observe('adhoc_helper_inspected')['ok'], 'the inspector is signer-agnostic by design'
            named = signer_check.problems(app, leaf)
            save(out / 'signer-adhoc.json', named)
            scenarios.append('adhoc_helper_named')
            assert named == [f'Contents/MacOS/sbpl-check: signed by ad hoc, not {leaf}'], named
            shutil.copy2(source / top_helper.relative_to(app), top_helper)
            assert signer_check.problems(app, leaf) == [], 'restoration must recover the signer check'

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
            assert not stale['ok'] and {e['code'] for e in stale['errors']} == {'manifest_hash'}, stale
            assert any(e['path'] == 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/PWRunner'
                       for e in stale['errors']), stale
    finally:
        after = inventory(source)
        save(out / 'source-after.json', after)
        assert after == before, 'signed controls changed the selected source app'
    save(out / 'controls.json', scenarios)
    print(f'{len(scenarios)} real signature controls passed')


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3])
