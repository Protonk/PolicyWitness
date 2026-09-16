"""Own a copied, signed user-scope runner through setup and verified removal.

The shell wrapper installs its cleanup trap before calling install(). The state
file is durable before any signing or installation. Tool injection is a Python
test boundary only; the CLI always uses the real commands.
"""
import json
import os
from pathlib import Path
import plistlib
import secrets
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'caller_auth'))
from bundle import CLIENT, SERVICE, command, inventory, save, signature


def tool(out, label, argv, *, invoke=command, check=True, timeout=30):
    directory = out / label
    result = invoke(directory, argv, check=check, timeout=timeout)
    return result['returncode'], (directory / 'stdout').read_bytes(), (directory / 'stderr').read_text()


def envelope(out, label, argv, invoke):
    _, raw, _ = tool(out, label, argv, invoke=invoke, timeout=90)
    value = json.loads(raw)
    assert value['result']['ok'] is True, (label, value)
    return value['data']


def entitlements(target, out, label, invoke):
    _, raw, error = tool(out, label, ['/usr/bin/codesign', '-d', '--entitlements', '-', '--xml', target], invoke=invoke)
    # codesign documents empty stdout for a signature with no entitlements.
    # A warning/error is not that condition: never silently replace it with {}.
    unexpected = [line for line in error.splitlines() if line and not line.startswith('Executable=')]
    assert not unexpected, (label, 'entitlement extraction diagnostics', unexpected)
    value = plistlib.loads(raw) if raw.strip() else None
    assert value is None or isinstance(value, dict), (label, 'entitlements are not a dictionary')
    save(out / (label + '.json'), {'present': value is not None, 'value': value})
    return value


def service_present(state, out, label, invoke):
    rc, _, error = tool(out, label, ['/bin/launchctl', 'print', state['target']], invoke=invoke, check=False)
    if rc == 0:
        return True
    assert 'Could not find service' in error and state['service_name'] in error, (label, rc, error)
    return False


def registry(pw, out, label, invoke):
    return envelope(out, label, [pw, 'runner', 'list'], invoke)['runners']


def owned_bundle(state):
    staging, bundle = Path(state['staging']), Path(state['bundle_path'])
    assert staging.parent == Path('/private/tmp') and staging.name.startswith('pw-byoxpc-'), staging
    assert staging.resolve() == staging and bundle == staging / 'PWRunner.xpc', state
    assert bundle.resolve() == bundle, 'staged bundle redirected through a symlink'
    assert state['service_name'].startswith('com.policywitness.test.byoxpc.s'), state
    assert state['target'] == f'gui/{os.getuid()}/{state["service_name"]}', state
    return staging, bundle


def install(pw, app, out, env_path, identity, *, invoke=command, launch_agents=None):
    state_path = out / 'session.json'
    assert not state_path.exists(), f'ownership state already exists: {state_path}'
    app = app.resolve()
    save(out / 'source-before.json', inventory(app))
    staging = Path(tempfile.mkdtemp(prefix='pw-byoxpc-', dir='/private/tmp'))
    service = 'com.policywitness.test.byoxpc.s' + secrets.token_hex(12)
    launch_agents = launch_agents or Path.home() / 'Library/LaunchAgents'
    state = {'source_app': str(app), 'staging': str(staging),
             'bundle_path': str(staging / 'PWRunner.xpc'), 'service_name': service,
             'target': f'gui/{os.getuid()}/{service}', 'plist_path': str(launch_agents / (service + '.plist')),
             'install_attempted': False, 'removed': False}
    save(state_path, state)
    _, bundle = owned_bundle(state)
    existing = registry(pw, out, 'registry-before', invoke)
    assert not any(r['service_name'] == service for r in existing), 'test service already registered'
    assert not os.path.lexists(state['plist_path']), 'test launchd plist already exists'
    assert not service_present(state, out, 'launchd-before', invoke), 'test service already loaded'
    source = app / SERVICE
    tool(out, 'verify-source', ['/usr/bin/codesign', '--verify', '--deep', '--strict', source], invoke=invoke)
    tool(out, 'verify-client', ['/usr/bin/codesign', '--verify', '--strict', app / CLIENT], invoke=invoke)
    source_sig = signature(source, out / 'source-signature', invoke=invoke)
    client_sig = signature(app / CLIENT, out / 'client-signature', invoke=invoke)
    team = client_sig['TeamIdentifier']
    assert team not in ('', 'not set') and source_sig['TeamIdentifier'] == team, 'runner/client teams differ'
    assert not source_sig['adhoc'] and source_sig['runtime'], source_sig
    source_entitlements = entitlements(source, out, 'source-entitlements', invoke)
    # Reject path escapes before copying or signing; published runners have no
    # need for external symlinks. The signer must only encounter owned files.
    for path in source.rglob('*'):
        assert path.resolve().is_relative_to(source.resolve()), f'runner path escapes bundle: {path}'
    tool(out, 'copy', ['/usr/bin/ditto', source, bundle], invoke=invoke)
    copied = inventory(bundle)
    assert copied == inventory(source), 'runner copy differs before modification'
    for relative in copied:
        assert not (bundle / relative).samefile(source / relative), f'copy aliases source: {relative}'
    info_path = bundle / 'Contents/Info.plist'
    info = plistlib.loads(info_path.read_bytes())
    assert info['CFBundlePackageType'] == 'XPC!' and info['CFBundleExecutable'] == 'PWRunner', info
    assert info.get('PWRunnerRequireSignedCaller') is True, 'source caller authentication is disabled'
    assert client_sig['Identifier'] in info['PWRunnerAllowedIdentifiers'], info
    info['CFBundleIdentifier'] = service
    info_path.write_bytes(plistlib.dumps(info))
    save(out / 'staged-info.json', info)
    argv = [pw, 'runner', 'install', '--bundle', bundle, '--kind', 'byoxpc', '--scope', 'user', '--identity', identity]
    if source_entitlements is not None:
        entitlement_path = staging / 'entitlements.plist'
        entitlement_path.write_bytes(plistlib.dumps(source_entitlements))
        argv += ['--entitlements', entitlement_path]
    # The public installer owns the one signing operation. It may bootstrap
    # before recording the runner, so cleanup must be armed before invoking it.
    state['install_attempted'] = True
    save(state_path, state)
    data = envelope(out, 'install', argv, invoke)
    record = data['runner']
    assert record['service_name'] == service and record['scope'] == 'user', record
    assert Path(record['bundle_path']).resolve() == bundle and record['id'], record
    assert Path(data['plist_path']) == Path(state['plist_path']), data
    state['runner_id'] = record['id']
    save(state_path, state)
    tool(out, 'verify-staged', ['/usr/bin/codesign', '--verify', '--deep', '--strict', bundle], invoke=invoke)
    sig = signature(bundle, out / 'staged-signature', invoke=invoke)
    assert sig['Identifier'] == service and sig['TeamIdentifier'] == team, sig
    assert sig['runtime'] and not sig['adhoc'] and sig.get('Timestamp'), sig
    assert entitlements(bundle, out, 'staged-entitlements', invoke) == source_entitlements, 'entitlements changed'
    current = inventory(bundle)
    for helper in ('pw-probe-runner', 'sb_api_validator'):
        key = 'Contents/MacOS/' + helper
        assert current[key] == copied[key], f'installer changed embedded helper: {helper}'
    # A connection failure here is a failed case, never an automatic skip.
    envelope(out, 'verify-connection', [pw, 'runner', 'verify', '--service-name', service], invoke)
    assert inventory(app) == json.loads((out / 'source-before.json').read_text()), 'setup changed selected app'
    save(env_path, {'runner_id': record['id'], 'service_name': service})


def cleanup(pw, state_path, *, invoke=command):
    if not state_path.exists():
        return
    out = state_path.parent
    state = json.loads(state_path.read_text())
    staging, bundle = owned_bundle(state)
    try:
        if state['install_attempted'] and not state['removed']:
            capture_path = out / 'install/command.json'
            capture = json.loads(capture_path.read_text()) if capture_path.exists() else {}
            assert capture.get('returncode') is not None and not capture.get('harness_timeout'), \
                'installer completion is uncertain; retain staging for inspection'
            entries = registry(pw, out, 'cleanup-registry-before', invoke)
            matches = [r for r in entries if r['service_name'] == state['service_name']]
            assert len(matches) <= 1, 'ambiguous registry ownership'
            present = service_present(state, out, 'cleanup-launchd-before', invoke)
            plist = Path(state['plist_path'])
            if os.path.lexists(plist):
                assert plist.is_file() and not plist.is_symlink(), 'launchd plist is not an owned regular file'
                config = plistlib.loads(plist.read_bytes())
                assert config.get('Label') == state['service_name'], 'plist label mismatch'
                assert config.get('ProgramArguments', [None])[0] == str(bundle / 'Contents/MacOS/PWRunner'), 'plist executable mismatch'
                assert config.get('MachServices') == {state['service_name']: True}, 'plist services mismatch'
            if matches:
                record = matches[0]
                assert record['scope'] == 'user' and Path(record['bundle_path']).resolve() == bundle, 'registry ownership mismatch'
                data = envelope(out, 'remove', [pw, 'runner', 'remove', '--id', record['id']], invoke)
                assert not data.get('warnings'), ('runner removal warnings; retaining bundle', data)
            elif present or os.path.lexists(plist):
                # Partial install without a registry record: follow the documented
                # manual recipe only after the exact plist proves ownership.
                assert plist.is_file() and not plist.is_symlink(), 'partial install has no owned plist'
                if present:
                    tool(out, 'partial-bootout', ['/bin/launchctl', 'bootout', state['target']], invoke=invoke)
                assert not service_present(state, out, 'partial-launchd-after', invoke), 'partial service still loaded'
                plist.unlink()
            assert not service_present(state, out, 'cleanup-launchd-after', invoke), 'service still loaded after removal'
            assert not os.path.lexists(plist), 'launchd plist remains after removal'
            assert not any(r['service_name'] == state['service_name'] for r in registry(pw, out, 'cleanup-registry-after', invoke)), 'runner remains registered'
        # Prove source preservation even when signing/setup failed.
        state['removed'] = True
        save(state_path, state)
        shutil.rmtree(staging)
    except BaseException as error:
        state['cleanup_error'] = str(error)
        save(state_path, state)
        raise RuntimeError(f'cleanup failed; retained {bundle}; service {state["service_name"]}: {error}') from error
    finally:
        after = inventory(Path(state['source_app']))
        save(out / 'source-after.json', after)
        assert after == json.loads((out / 'source-before.json').read_text()), 'test changed selected app'


if __name__ == '__main__':
    if sys.argv[1] == 'install':
        install(sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4]), Path(sys.argv[5]), sys.argv[6])
    elif sys.argv[1] == 'cleanup':
        cleanup(sys.argv[2], Path(sys.argv[3]))
    else:
        raise SystemExit('expected install or cleanup')
