"""Recursive verification controls on never-launched, ad-hoc sealed copies.

No signing identity, launchd service or GUI session is involved. Every copy
lives in owned temporary staging; the installer runs with a fixture registry
and HOME supplied only to its child process, and never bootstraps.
"""
import json
import os
from pathlib import Path
import plistlib
import secrets
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/fixtures/caller_auth'))
from bundle import SERVICE, command, inventory, save

HELPERS = {'worker': 'Contents/MacOS/pw-probe-runner', 'issuer': 'Contents/MacOS/pw-extension-issuer'}
CODE_PAGE_OFFSET = 4096


def main(app, out, pw):
    app = app.resolve()
    before = inventory(app)
    save(out / 'source-before.json', before)
    observations = {}
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
            # Seal the changed bundle ad hoc; the embedded helpers keep the
            # build's signatures, so the copy needs no identity to verify.
            command(out / name / 'seal', ['/usr/bin/codesign', '--force', '--options', 'runtime', '-s', '-', bundle], timeout=90)
            intact = verification(name + '-intact', bundle)
            assert intact == {'outer': 0, 'deep': 0, 'worker': 0, 'issuer': 0}, intact
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
                assert [f['binary'] for f in failures] == ['bundle', role], failures
                for failure in failures:
                    assert failure['runner_id'] == runner_id and failure['service_name'] == service
                    assert 'codesign verify failed' in failure['error'], failure
                listed = json.loads(cli(validated_name + '/list', ['runner', 'list'], code=0).stdout)['data']['runners']
                assert listed[0]['id'] == runner_id and listed[0]['signature']['valid'] is False
                assert listed[0][role + '_signature']['valid'] is False
                for other in ('worker', 'validator', 'issuer'):
                    if other != role:
                        assert listed[0][other + '_signature']['valid'] is True
            finally:
                removed = json.loads(cli(validated_name + '/remove', ['runner', 'remove', '--id', runner_id, '--skip-bootout'], code=0).stdout)
                assert removed['data'].get('cleanup_retained') is not True, removed
        final = json.loads(registry.read_text())
        assert not final['runners'] and not final.get('pending_cleanup'), final
        assert not list((home / 'Library/LaunchAgents').iterdir()), 'fixture LaunchAgents not empty'
    save(out / 'observations.json', observations)
    assert inventory(app) == before, 'the selected app changed'
    print(json.dumps(dict(controls=['refused-worker', 'validated-worker', 'refused-issuer', 'validated-issuer'], observations=observations)))


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
