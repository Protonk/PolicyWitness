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
import time

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


HELPERS = ('PWRunner', 'pw-probe-runner', 'sb_api_validator')


def binary_entitlements(bundle, out, label, invoke):
    """The host's, the worker's and the validator's entitlements, read back separately."""
    return {name: entitlements(bundle / 'Contents/MacOS' / name, out, f'{label}-{name}', invoke) for name in HELPERS}


def service_present(state, out, label, invoke):
    rc, _, error = tool(out, label, ['/bin/launchctl', 'print', state['target']], invoke=invoke, check=False)
    if rc == 0:
        return True
    assert 'Could not find service' in error and state['service_name'] in error, (label, rc, error)
    return False


def retire_host(pid, out, timeout=5.0):
    """Wait for the host a verify or run reached to exit; a PID is required."""
    assert isinstance(pid, int) and pid > 0, ('verify reported no host PID', pid)
    deadline = time.monotonic() + timeout
    while True:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            break
        assert time.monotonic() < deadline, f'host {pid} did not retire within {timeout} s'
        time.sleep(0.02)
    save(out / 'verify-host-retired.json', {'pid': pid, 'retired': True})


def registry(pw, out, label, invoke):
    data = envelope(out, label, [pw, 'runner', 'list'], invoke)
    return data['runners'] + data.get('pending_cleanup', [])


def owned_bundle(state):
    staging, bundle = Path(state['staging']), Path(state['bundle_path'])
    assert staging.parent == Path('/private/tmp') and staging.name.startswith('pw-byoxpc-'), staging
    assert staging.resolve() == staging and bundle == staging / 'PWRunner.xpc', state
    assert bundle.resolve() == bundle, 'staged bundle redirected through a symlink'
    assert state['service_name'].startswith('com.policywitness.test.byoxpc.s'), state
    assert state['target'] == f'gui/{os.getuid()}/{state["service_name"]}', state
    return staging, bundle


def persist_state(state, receipt=None):
    path = Path(state['state_path'])
    temporary = path.with_suffix('.tmp')
    save(temporary, state)
    temporary.replace(path)
    if receipt is not None and receipt.parent.exists():
        save(receipt, state)


def install(pw, app, out, env_path, identity, *, invoke=command, launch_agents=None, variant="team", supplied_entitlements=None):
    receipt = out / 'session.json'
    assert not receipt.exists(), f'ownership receipt already exists: {receipt}'
    app = app.resolve()
    save(out / 'source-before.json', inventory(app))
    staging = Path(tempfile.mkdtemp(prefix='pw-byoxpc-', dir='/private/tmp'))
    service = 'com.policywitness.test.byoxpc.s' + secrets.token_hex(12)
    launch_agents = launch_agents or Path.home() / 'Library/LaunchAgents'
    state = {'source_app': str(app), 'staging': str(staging),
             'bundle_path': str(staging / 'PWRunner.xpc'), 'service_name': service,
             'target': f'gui/{os.getuid()}/{service}', 'plist_path': str(launch_agents / (service + '.plist')),
             'install_attempted': False, 'install_finished': False, 'removed': False,
             'state_path': str(staging / 'session.json'), 'receipt_path': str(receipt),
             'source_inventory': inventory(app), 'variant': variant}
    persist_state(state, receipt)
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
    # The supplied plist is what the installer embeds; by default the source's
    # own entitlements, otherwise the caller's dictionary, saved beside the receipts.
    supplied = source_entitlements if supplied_entitlements is None else dict(supplied_entitlements)
    save(out / 'supplied-entitlements.json', {'present': supplied is not None, 'value': supplied})
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
    if variant == 'adhoc_noauth':
        info.pop('PWRunnerRequireSignedCaller', None)
        info.pop('PWRunnerAllowedIdentifiers', None)
    info_path.write_bytes(plistlib.dumps(info))
    save(out / 'staged-info.json', info)
    argv = [pw, 'runner', 'install', '--bundle', bundle, '--kind', 'byoxpc', '--scope', 'user']
    argv += ['--identity', '-', '--allow-adhoc'] if variant == 'adhoc_noauth' else ['--identity', identity]
    if supplied is not None:
        entitlement_path = staging / 'entitlements.plist'
        entitlement_path.write_bytes(plistlib.dumps(supplied))
        argv += ['--entitlements', entitlement_path]
    # The public installer owns the one signing operation. It may bootstrap
    # after persisting pending ownership; arm cleanup before invoking it.
    state['install_attempted'] = True
    persist_state(state, receipt)
    rc, raw, error = tool(out, 'install', argv, invoke=invoke, check=False, timeout=90)
    state['install_finished'] = True
    persist_state(state, receipt)
    assert rc == 0, ('installation failed', rc, error)
    installed = json.loads(raw)
    assert installed['result']['ok'] is True, installed
    data = installed['data']
    record = data['runner']
    assert record['service_name'] == service and record['scope'] == 'user', record
    assert Path(record['bundle_path']).resolve() == bundle and record['id'], record
    assert Path(data['plist_path']) == Path(state['plist_path']), data
    state['runner_id'] = record['id']
    persist_state(state, receipt)
    tool(out, 'verify-staged', ['/usr/bin/codesign', '--verify', '--deep', '--strict', bundle], invoke=invoke)
    sig = signature(bundle, out / 'staged-signature', invoke=invoke)
    assert sig['Identifier'] == service and sig['runtime'], sig
    if variant == 'adhoc_noauth':
        assert sig['adhoc'] and sig['TeamIdentifier'] == 'not set', sig
    else:
        assert sig['TeamIdentifier'] == team and not sig['adhoc'] and sig.get('Timestamp'), sig
    assert entitlements(bundle, out, 'staged-entitlements', invoke) == supplied, 'entitlements changed'
    # The installer signs the embedded worker with the supplied entitlements
    # and the validator with the identity alone before sealing the bundle, so
    # their bytes change; read each binary back separately instead.
    embedded = binary_entitlements(bundle, out, 'staged', invoke)
    assert embedded['PWRunner'] == supplied, ('host entitlements', embedded['PWRunner'])
    assert embedded['pw-probe-runner'] == supplied, ('worker entitlements', embedded['pw-probe-runner'])
    assert embedded['sb_api_validator'] is None, ('validator entitlements', embedded['sb_api_validator'])
    for helper in ('pw-probe-runner', 'sb_api_validator'):
        helper_sig = signature(bundle / 'Contents/MacOS' / helper, out / ('staged-signature-' + helper), invoke=invoke)
        if variant == 'adhoc_noauth':
            assert helper_sig['adhoc'], (helper, helper_sig)
        else:
            assert helper_sig['TeamIdentifier'] == team and not helper_sig['adhoc'], (helper, helper_sig)
    for field, expected in (('entitlements', supplied), ('worker_entitlements', supplied), ('validator_entitlements', None)):
        keys = sorted(expected) if expected else []
        assert record[field]['keys'] == keys and record[field]['error'] is None, (field, record.get(field))
    # Record every runner-related process alive before the connection, so a
    # host claimed by a foreign client is attributable from the artifacts.
    tool(out, 'processes-before-verify', ['/bin/ps', '-axo', 'pid=,ppid=,lstart=,comm='], invoke=invoke, check=False)
    # A connection failure here is a failed case, never an automatic skip.
    verified = envelope(out, 'verify-connection', [pw, 'runner', 'verify', '--service-name', service], invoke)
    # The verify request consumed a host. Until that host has exited, a
    # connection can still reach it and meet its terminal claim (already_ran),
    # so wait for its retirement before handing the runner to the caller; the
    # next request then only waits for launchd's respawn throttle.
    retire_host(verified.get('runner_pid'), out)
    assert inventory(app) == json.loads((out / 'source-before.json').read_text()), 'setup changed selected app'
    save(env_path, {'runner_id': record['id'], 'service_name': service})


def cleanup(pw, state_path, *, invoke=command, remove_tree=shutil.rmtree):
    if not state_path.exists():
        return
    receipt = state_path
    state = json.loads(state_path.read_text())
    durable = Path(state['state_path'])
    if durable.exists():
        state = json.loads(durable.read_text())
    staging, bundle = owned_bundle(state)
    if not staging.exists():
        assert state['removed'], 'staging disappeared before verified cleanup'
        return
    assert durable == staging / 'session.json', 'recovery record escaped staging'
    # Cleanup receipts also survive deletion of the originating run output.
    out = staging / ('cleanup-' + secrets.token_hex(8))
    out.mkdir()
    try:
        if state['install_attempted']:
            entries = registry(pw, out, 'registry-before', invoke)
            matches = [r for r in entries if r['service_name'] == state['service_name']]
            assert len(matches) <= 1, 'ambiguous registry ownership'
            assert matches or state['install_finished'] or state['removed'], \
                'installer completion is uncertain and no recovery record exists; retain staging for inspection'
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
                assert not data.get('warnings') and not data.get('cleanup_retained'), ('runner cleanup incomplete; retaining bundle', data)
            assert not service_present(state, out, 'launchd-after', invoke), 'service still loaded after removal'
            assert not os.path.lexists(plist), 'launchd plist remains after removal'
            assert not any(r['service_name'] == state['service_name'] for r in registry(pw, out, 'registry-after', invoke)), 'runner remains registered'
        after = inventory(Path(state['source_app']))
        save(out / 'source-after.json', after)
        assert after == state['source_inventory'], 'test changed selected app'
        state['removed'] = True
        state.pop('cleanup_error', None)
        persist_state(state, receipt)
        if receipt.parent != staging and receipt.parent.exists():
            shutil.copytree(out, receipt.parent / out.name)
        # Keep ownership through bundle deletion; a failure is safely retryable.
        for child in staging.iterdir():
            if child == durable:
                continue
            if child.is_dir() and not child.is_symlink():
                remove_tree(child)
            else:
                child.unlink()
        durable.unlink()
        staging.rmdir()
    except BaseException as error:
        state['cleanup_error'] = str(error)
        persist_state(state, receipt)
        raise RuntimeError(f'cleanup failed; retained {bundle}; service {state["service_name"]}: {error}') from error


if __name__ == '__main__':
    if sys.argv[1] in ('install', 'install-noauth'):
        # An optional seventh argument names an entitlements plist to supply
        # instead of the source's own.
        supplied = plistlib.loads(Path(sys.argv[7]).read_bytes()) if len(sys.argv) > 7 else None
        install(sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4]), Path(sys.argv[5]), sys.argv[6],
                variant='adhoc_noauth' if sys.argv[1] == 'install-noauth' else 'team', supplied_entitlements=supplied)
    elif sys.argv[1] == 'cleanup':
        cleanup(sys.argv[2], Path(sys.argv[3]))
    else:
        raise SystemExit('expected install or cleanup')
