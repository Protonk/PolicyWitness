"""Own a copied, signed user-scope runner through setup and verified removal.

The shell wrapper installs its cleanup trap before calling install(). The state
file is durable before any signing or installation. Tool injection is a Python
test boundary only; the CLI always uses the real commands.
"""
import json
import hashlib
import re
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


HELPERS = ('PWRunner', 'pw-probe-runner', 'pw-probe-runner-unentitled', 'sb_api_validator')


def binary_entitlements(bundle, out, label, invoke):
    """Each embedded executable's entitlements, read back separately."""
    return {name: entitlements(bundle / 'Contents/MacOS' / name, out, f'{label}-{name}', invoke) for name in HELPERS}


def equipment_inventory(bundle, out, label, invoke, *, expected_contract=None):
    """Independently bind the sealed two-role inventory to actual signed bytes."""
    from contract import WORKER_IDENTITY
    path = bundle / 'Contents/Resources/worker-equipment.json'
    assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(bundle.resolve()), path
    raw = path.read_bytes()
    assert len(raw) <= 1_048_576, 'equipment inventory exceeds input bound'
    value = json.loads(raw)
    assert set(value) == {'schema_version', 'contract', 'worker_identity', 'unsigned_worker_sha256', 'workers'}, value
    assert type(value['schema_version']) is int and value['schema_version'] == 1
    if expected_contract is None:
        expected_contract = plistlib.loads((bundle / 'Contents/Info.plist').read_bytes()).get('PWContract')
    assert value['contract'] == expected_contract and value['worker_identity'] == WORKER_IDENTITY, value
    assert re.fullmatch('[0-9a-f]{64}', value['unsigned_worker_sha256'])
    assert isinstance(value['workers'], list) and len(value['workers']) == 2
    seen = set()
    for row in value['workers']:
        assert set(row) == {'role', 'relative_path', 'sha256', 'cdhash', 'identifier', 'team_id', 'entitlements_xml'}, row
        role = row['role']
        assert role in ('selected', 'unentitled') and role not in seen, row
        seen.add(role)
        expected = 'Contents/MacOS/pw-probe-runner' + ('-unentitled' if role == 'unentitled' else '')
        assert row['relative_path'] == expected
        binary = bundle / expected
        assert binary.is_file() and not binary.is_symlink() and binary.resolve().is_relative_to(bundle.resolve())
        assert row['sha256'] == hashlib.sha256(binary.read_bytes()).hexdigest(), ('equipment signed hash mismatch', role)
        sig = signature(binary, out / (label + '-signature-' + role), invoke=invoke)
        team = None if sig['TeamIdentifier'] == 'not set' else sig['TeamIdentifier']
        assert row['cdhash'] == sig['CDHash'] and row['identifier'] == sig['Identifier'] and row['team_id'] == team
        assert isinstance(row['entitlements_xml'], str) and len(row['entitlements_xml'].encode()) <= 65_536
        expected_entitlements = plistlib.loads(row['entitlements_xml'].encode())
        observed = entitlements(binary, out, label + '-entitlements-' + role, invoke) or {}
        assert isinstance(expected_entitlements, dict) and expected_entitlements == observed
        assert role != 'unentitled' or not observed, 'unentitled equipment carries entitlements'
    save(out / (label + '.json'), value)
    return value


def service_present(state, out, label, invoke):
    rc, _, error = tool(out, label, ['/bin/launchctl', 'print', state['target']], invoke=invoke, check=False)
    if rc == 0:
        return True
    assert 'Could not find service' in error and state['service_name'] in error, (label, rc, error)
    return False


def session_invoke(pw, state, invoke):
    """Scope the registry override to this session's CLI calls, keeping HOME real."""
    def scoped(out, argv, **kwargs):
        if str(argv[0]) == str(pw):
            env = dict(os.environ)
            env.pop('PW_RUNNER_REGISTRY', None)
            if state.get('registry_path') is not None:
                env['PW_RUNNER_REGISTRY'] = state['registry_path']
            kwargs['env'] = env
        return invoke(out, argv, **kwargs)
    return scoped


def registry(pw, out, label, invoke):
    data = envelope(out, label, [pw, 'runner', 'list'], invoke)
    return data['runners'] + [row.get('runner', row) for row in data.get('pending_cleanup', [])]



GUIDE_CORE = ('layout', 'workspace', 'workspace_identity', 'staging', 'staging_identity',
              'bundle_path', 'service_name', 'target', 'plist_path', 'state_path',
              'receipt_path', 'source_app', 'source_inventory', 'registry_path', 'variant')


def guide_core(state):
    return {key: state[key] for key in GUIDE_CORE}


def owner_object(path):
    assert path.is_file() and not path.is_symlink(), f'owner is not a regular file: {path}'
    value = json.loads(path.read_text())
    assert isinstance(value, dict), f'owner is not an object: {path}'
    return value


def owned_bundle(state):
    staging, bundle = Path(state['staging']), Path(state['bundle_path'])
    if state.get('layout') == 'guide_workflow':
        assert state['registry_path'] is None, 'guide session must use the default registry'
        assert Path(state['state_path']) == staging / 'session.json'
        parent = Path(state['workspace'])
        assert parent.parent == Path('/private/tmp') and re.fullmatch(r'pw-guide\.[A-Za-z0-9]+', parent.name), parent
        assert parent.resolve() == parent and parent.is_dir() and not parent.is_symlink(), parent
        observed = parent.stat()
        assert [observed.st_dev, observed.st_ino] == state['workspace_identity'], 'guide workspace identity changed'
        assert staging.parent == parent and re.fullmatch(r'runner\.[A-Za-z0-9]+', staging.name), staging
        assert staging.resolve() == staging and bundle == staging / 'PWRunner.guide.xpc', state
        if staging.exists():
            observed = staging.stat()
            assert [observed.st_dev, observed.st_ino] == state['staging_identity'], 'guide staging identity changed'
        else:
            assert state.get('removed'), 'guide staging disappeared before verified cleanup'
        expected = f'com.policywitness.guide.{os.getuid()}.{staging.name}'
        assert state['service_name'] == expected, state
        assert Path(state['plist_path']) == Path.home() / 'Library/LaunchAgents' / (expected + '.plist'), state
    else:
        assert state.get('layout') in (None, 'byoxpc'), 'unknown session layout'
        assert staging.parent == Path('/private/tmp') and staging.name.startswith('pw-byoxpc-'), staging
        assert staging.resolve() == staging and bundle == staging / 'PWRunner.xpc', state
        assert state['service_name'].startswith('com.policywitness.test.byoxpc.s'), state
    assert bundle.resolve() == bundle, 'staged bundle redirected through a symlink'
    assert state['target'] == f'gui/{os.getuid()}/{state["service_name"]}', state
    return staging, bundle


def persist_state(state, receipt=None):
    path = Path(state['state_path'])
    temporary = path.with_suffix('.tmp')
    save(temporary, state)
    temporary.replace(path)
    if receipt is not None and receipt.parent.exists():
        save(receipt, state)


def adopt_guide(app, receipt, workspace_owner, staging, bundle, service):
    """Own the guide's already-created empty stage before copying or signing.

    The guide case owns the containing work directory and records its inode;
    this helper owns the external service through the ordinary cleanup path.
    """
    assert not os.path.lexists(receipt), f'ownership receipt already exists: {receipt}'
    parent = Path(workspace_owner['workspace'])
    assert Path(workspace_owner['state_path']) == parent / 'session.json'
    durable = owner_object(parent / 'session.json')
    assert durable['kind'] == 'guide_workflow' and durable['workspace_identity'] == workspace_owner['workspace_identity']
    assert durable['workspace'] == str(parent) and durable['state_path'] == str(parent / 'session.json')
    assert durable['source_app'] == str(app.resolve()) and durable['removed'] is False
    assert workspace_owner['receipt_path'] == str(receipt.parent / 'session.json')
    parent_receipt = owner_object(Path(workspace_owner['receipt_path']))
    for key in ('kind', 'source_app', 'source_inventory', 'workspace', 'workspace_identity', 'state_path', 'receipt_path', 'contract'):
        assert durable[key] == parent_receipt[key] == workspace_owner[key], 'guide parent ownership disagrees'
    assert staging.is_dir() and not any(staging.iterdir()), 'guide staging must be new and empty'
    observed = staging.stat()
    state = dict(layout='guide_workflow', workspace=str(parent),
                 workspace_identity=workspace_owner['workspace_identity'],
                 staging_identity=[observed.st_dev, observed.st_ino],
                 source_app=str(app.resolve()), source_inventory=workspace_owner['source_inventory'],
                 staging=str(staging), bundle_path=str(bundle), service_name=service,
                 target=f'gui/{os.getuid()}/{service}',
                 plist_path=str(Path.home() / 'Library/LaunchAgents' / (service + '.plist')),
                 install_attempted=False, install_finished=False, removed=False,
                 state_path=str(staging / 'session.json'), receipt_path=str(receipt),
                 registry_path=None, variant='guide')
    owned_bundle(state)
    source = app.resolve() / SERVICE
    for path in source.rglob('*'):
        assert path.resolve().is_relative_to(source.resolve()), f'runner path escapes bundle: {path}'
    assert workspace_owner.get('external') is None, 'guide external stage already armed'
    workspace_owner['external'] = guide_core(state)
    persist_state(workspace_owner, Path(workspace_owner['receipt_path']))
    persist_state(state, receipt)


def install(pw, app, out, env_path, identity, *, invoke=command, launch_agents=None, variant="team", supplied_entitlements=None, default_location=False, registry_root=None):
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
    registry_root = registry_root or Path.home() / 'Library/Application Support/PolicyWitness/test-sessions'
    state['registry_path'] = None if default_location else str(registry_root / service / 'runners.json')
    persist_state(state, receipt)
    invoke = session_invoke(pw, state, invoke)
    _, bundle = owned_bundle(state)
    existing = registry(pw, out, 'registry-before', invoke)
    envelope(out, 'reconcile-before', [pw, 'runner', 'reconcile'], invoke)
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
    source_equipment = equipment_inventory(source, out, 'source-equipment', invoke)
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
    # Renaming Info.plist invalidates the copied service seal. Re-seal this
    # owned, never-launched source with the known Developer ID before the
    # public installer independently verifies its source inventory and seal.
    reseal = ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp', '-s', identity]
    if source_entitlements is not None:
        source_plist = staging / 'source-entitlements.plist'
        source_plist.write_bytes(plistlib.dumps(source_entitlements))
        reseal += ['--entitlements', source_plist]
    tool(out, 'reseal-renamed-source', reseal + [bundle], invoke=invoke, timeout=90)
    tool(out, 'verify-renamed-source', ['/usr/bin/codesign', '--verify', '--deep', '--strict', bundle], invoke=invoke)
    argv = [pw, 'runner', 'install', '--bundle', bundle, '--kind', 'byoxpc', '--scope', 'user']
    argv += ['--identity', '-', '--allow-adhoc'] if variant == 'adhoc_noauth' else ['--identity', identity]
    if supplied is not None:
        entitlement_path = staging / 'entitlements.plist'
        entitlement_path.write_bytes(plistlib.dumps(supplied))
        argv += ['--entitlements', entitlement_path]
    # The public installer owns installed worker signing and inventory rewrite. It may bootstrap
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
    # and the unentitled worker and validator with the identity alone before sealing the bundle, so
    # their bytes change; read each binary back separately instead.
    embedded = binary_entitlements(bundle, out, 'staged', invoke)
    assert embedded['PWRunner'] == supplied, ('host entitlements', embedded['PWRunner'])
    assert embedded['pw-probe-runner'] == supplied, ('worker entitlements', embedded['pw-probe-runner'])
    assert embedded['sb_api_validator'] is None, ('validator entitlements', embedded['sb_api_validator'])
    assert embedded['pw-probe-runner-unentitled'] is None, ('unentitled worker entitlements', embedded['pw-probe-runner-unentitled'])
    for helper in ('pw-probe-runner', 'pw-probe-runner-unentitled', 'sb_api_validator'):
        helper_sig = signature(bundle / 'Contents/MacOS' / helper, out / ('staged-signature-' + helper), invoke=invoke)
        if variant == 'adhoc_noauth':
            assert helper_sig['adhoc'], (helper, helper_sig)
        else:
            assert helper_sig['TeamIdentifier'] == team and not helper_sig['adhoc'], (helper, helper_sig)
    for field, expected in (('entitlements', supplied), ('worker_entitlements', supplied), ('validator_entitlements', None), ('unentitled_worker_entitlements', None)):
        keys = sorted(expected) if expected else []
        assert record[field]['keys'] == keys and record[field]['error'] is None, (field, record.get(field))
    installed_equipment = equipment_inventory(bundle, out, 'installed-equipment', invoke)
    assert installed_equipment['unsigned_worker_sha256'] == source_equipment['unsigned_worker_sha256']
    assert installed_equipment['worker_identity'] == source_equipment['worker_identity']
    assert record['worker_equipment_inventory'] == installed_equipment
    assert record['source_worker_equipment_inventory'] == source_equipment
    assert record['unentitled_worker_sha256'] == next(r['sha256'] for r in installed_equipment['workers'] if r['role'] == 'unentitled')
    # Record every runner-related process alive before the connection, so a
    # host claimed by a foreign client is attributable from the artifacts.
    tool(out, 'processes-before-verify', ['/bin/ps', '-axo', 'pid=,ppid=,lstart=,comm='], invoke=invoke, check=False)
    # A connection failure here is a failed case, never an automatic skip.
    envelope(out, 'verify-connection', [pw, 'runner', 'verify', '--service-name', service], invoke)
    assert inventory(app) == json.loads((out / 'source-before.json').read_text()), 'setup changed selected app'
    save(env_path, {'runner_id': record['id'], 'service_name': service, 'PW_RUNNER_REGISTRY': state['registry_path']})


def cleanup(pw, state_path, *, invoke=command, remove_tree=shutil.rmtree):
    if not os.path.lexists(state_path):
        return
    receipt = state_path
    state = owner_object(state_path)
    durable = Path(state['state_path'])
    if state.get('layout') == 'guide_workflow':
        owned_bundle(state)
        if os.path.lexists(durable):
            latest = owner_object(durable)
            assert guide_core(latest) == guide_core(state), 'guide durable ownership disagrees with receipt'
            state = latest
    elif durable.exists():
        state = json.loads(durable.read_text())
    staging, bundle = owned_bundle(state)
    invoke = session_invoke(pw, state, invoke)
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
        if state.get('registry_path') is not None:
            registry_path = Path(state['registry_path'])
            assert registry_path.name == 'runners.json' and registry_path.parent.name == state['service_name']
            assert registry_path.parent.resolve() == registry_path.parent, 'registry directory redirected'
            # Never delete an occupied registry, an unknown file, or a lock
            # inode held by another process. A crash leaves this durable owner.
            if registry_path.parent.exists():
                import fcntl
                lock = registry_path.with_suffix('.json.lock')
                with lock.open('a+') as holder:
                    fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    entries = registry(pw, out, 'registry-empty', invoke)
                    assert not entries, 'session registry is not empty; retaining ownership'
                    assert set(p.name for p in registry_path.parent.iterdir()) <= {'runners.json', 'runners.json.lock'}, 'unexpected registry files'
                    registry_path.unlink(missing_ok=True)
                    lock.unlink()
                    registry_path.parent.rmdir()
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
    if sys.argv[1] in ('install', 'install-noauth', 'install-default'):
        # An optional seventh argument names an entitlements plist to supply
        # instead of the source's own.
        supplied = plistlib.loads(Path(sys.argv[7]).read_bytes()) if len(sys.argv) > 7 else None
        install(sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4]), Path(sys.argv[5]), sys.argv[6],
                variant='adhoc_noauth' if sys.argv[1] == 'install-noauth' else 'team', supplied_entitlements=supplied, default_location=sys.argv[1] == 'install-default')
    elif sys.argv[1] == 'cleanup':
        cleanup(sys.argv[2], Path(sys.argv[3]))
    else:
        raise SystemExit('expected install or cleanup')
