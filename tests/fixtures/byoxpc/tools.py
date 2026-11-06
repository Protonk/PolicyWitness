"""Independent fake OS/CLI commands with durable receipts; never calls real tools."""
import json
import hashlib
import os
from pathlib import Path
import plistlib
import shutil
import sys

config = json.loads(Path(sys.argv[1]).read_text())
argv = sys.argv[2:]
mode = config['mode']
state_path = Path(config['state'])
state = json.loads(state_path.read_text()) if state_path.exists() else {'loaded': False, 'runners': [config['unrelated']] if mode == 'registry_nonempty' else [], 'pending_cleanup': []}
ownership = json.loads(Path(config.get('ownership', str(Path(config['out']) / 'session.json'))).read_text())
bundle = Path(ownership['bundle_path'])
service = ownership['service_name']
plist = Path(ownership['plist_path'])
receipt = {'argv': argv}


def finish(rc=0, value=None):
    state_path.write_text(json.dumps(state))
    with Path(config['receipts']).open('a') as stream:
        stream.write(json.dumps({**receipt, 'rc': rc}) + '\n')
    if value is not None:
        print(json.dumps(value))
    raise SystemExit(rc)


def reply(data, ok=True):
    finish(0 if ok else 1, {'result': {'ok': ok}, 'data': data})


if argv[0] == '/usr/bin/ditto':
    assert Path(argv[2]) == bundle and Path(argv[1]) != bundle
    shutil.copytree(argv[1], argv[2], symlinks=True)
    finish()
if argv[0] == '/usr/bin/codesign':
    if '-s' in argv:
        assert Path(argv[-1]) == bundle and argv[argv.index('-s') + 1] == 'fixture identity'
        assert not state['loaded'] and not any(r['service_name'] == service for r in state['runners']), 'renamed source resealed after installation'
        assert '--force' in argv and '--timestamp' in argv and '--options' in argv
        if mode == 'source_reseal_failure':
            finish(17)
        executable = bundle / 'Contents/MacOS/PWRunner'
        executable.write_bytes(executable.read_bytes() + b' renamed-source-seal')
        state['renamed_source_sealed'] = True
        finish()
    target = Path(argv[-1])
    staged = target == bundle or target.is_relative_to(bundle)
    if '--verify' in argv:
        if mode == 'bad_source_signature' and not staged:
            finish(7)
        if mode == 'helper_changed' and staged and '--deep' in argv:
            # A helper changed after sealing fails recursive verification.
            print('nested code is modified or invalid', file=sys.stderr)
            finish(1)
        finish()
    if '--xml' in argv:
        if mode == 'entitlement_diagnostic' and not staged:
            print('warning: entitlement extraction failed', file=sys.stderr)
            finish()
        if mode == 'malformed_entitlements' and not staged:
            print('not a plist')
            finish()
        ent = config['entitlements']
        if mode == 'changed_entitlements' and staged:
            ent = {'unexpected': True}
        if target.name in ('sb_api_validator', 'pw-probe-runner-unentitled'):
            # These helpers receive the identity without the worker plist.
            ent = None
        if mode == 'unentitled_entitlements' and staged and target.name == 'pw-probe-runner-unentitled':
            ent = {'unexpected': True}
        if ent is not None:
            sys.stdout.buffer.write(plistlib.dumps(ent))
            sys.stdout.buffer.flush()
        finish()
    identifier = service if staged and target.name == 'PWRunner.xpc' else 'pw-runner-client' if target.name == 'pw-runner-client' else 'fixture.source'
    team = 'not set' if mode == 'adhoc_noauth' and staged else 'WRONG' if mode == 'wrong_team' and staged else 'FIXTURETEAM'
    if mode == 'adhoc_noauth' and staged:
        print('Signature=adhoc', file=sys.stderr)
    cdhash = 'a' * 40
    print(f'Identifier={identifier}\nTeamIdentifier={team}\nCDHash={cdhash}\n'
          'CodeDirectory flags=0x10000(runtime)\nTimestamp=fixture timestamp', file=sys.stderr)
    finish()
if argv[0] == '/bin/launchctl':
    assert argv[-1] == ownership['target']
    if argv[1] == 'print':
        if mode == 'launchctl_equipment':
            print('operation not permitted', file=sys.stderr)
            finish(1)
        if state['loaded']:
            finish()
        print(f'Could not find service "{service}" in domain for user gui', file=sys.stderr)
        finish(113)
    assert argv[1] == 'bootout'
    state['loaded'] = False
    finish()
assert argv[0] == config['pw'] and argv[1] == 'runner', argv
assert os.environ.get('PW_RUNNER_REGISTRY') == ownership['registry_path']
registry_path = Path(ownership['registry_path'])
registry_path.parent.mkdir(parents=True, exist_ok=True)
registry_path.write_text(json.dumps(state))
receipt['registry_path'] = str(registry_path)
if argv[2] == 'list':
    reply({'runners': state['runners'], 'pending_cleanup': state['pending_cleanup']})
if argv[2] == 'reconcile':
    reply({'records': [], 'candidates': []})
if argv[2] == 'install':
    target = Path(argv[argv.index('--bundle') + 1])
    assert target == bundle and target.resolve() == target
    assert target != Path(config['source']) and target.parent.parent == Path('/private/tmp')
    if mode == 'adhoc_noauth':
        assert '--allow-adhoc' in argv and argv[argv.index('--identity') + 1] == '-'
        info = plistlib.loads((bundle / 'Contents/Info.plist').read_bytes())
        assert 'PWRunnerRequireSignedCaller' not in info and 'PWRunnerAllowedIdentifiers' not in info
    else:
        assert '--allow-adhoc' not in argv and argv[argv.index('--identity') + 1] == 'fixture identity'
    if '--entitlements' in argv:
        receipt['entitlements'] = plistlib.loads(Path(argv[argv.index('--entitlements') + 1]).read_bytes())
    assert receipt.get('entitlements') == config['entitlements'], 'entitlements were not preserved'
    assert state.get('renamed_source_sealed'), 'installer accepted unsealed renamed source'
    if mode in ('sign_failure', 'uncertain_no_record'):
        finish(17)
    executable = bundle / 'Contents/MacOS/PWRunner'
    executable.write_bytes(executable.read_bytes() + b' signed')
    if mode == 'helper_changed':
        (bundle / 'Contents/MacOS/pw-probe-runner').write_bytes(b'changed helper')
    embedded = receipt.get('entitlements')
    read_back = lambda value: {'raw_plist': None, 'keys': sorted(value) if value else [],
                               'granted': sorted(k for k, v in (value or {}).items() if v is True), 'error': None}
    record = {'id': 'owned-id', 'service_name': service, 'scope': 'user', 'bundle_path': str(bundle), 'state': 'pending',
              'entitlements': read_back(embedded), 'worker_entitlements': read_back(embedded),
              'validator_entitlements': read_back(None), 'unentitled_worker_entitlements': read_back(None)}
    inventory_path = bundle / 'Contents/Resources/worker-equipment.json'
    source_inventory = json.loads(inventory_path.read_text())
    current_inventory = json.loads(inventory_path.read_text())
    for row in current_inventory['workers']:
        row['sha256'] = hashlib.sha256((bundle / row['relative_path']).read_bytes()).hexdigest()
        row['team_id'] = None if mode == 'adhoc_noauth' else 'WRONG' if mode == 'wrong_team' else 'FIXTURETEAM'
        row['entitlements_xml'] = plistlib.dumps((embedded or {}) if row['role'] == 'selected' else {}).decode()
    inventory_path.write_text(json.dumps(current_inventory))
    record['worker_equipment_inventory'] = current_inventory
    record['source_worker_equipment_inventory'] = source_inventory
    record['unentitled_worker_sha256'] = next(r['sha256'] for r in current_inventory['workers'] if r['role'] == 'unentitled')
    state['runners'].append(record)
    plist.parent.mkdir(parents=True, exist_ok=True)
    plist.write_bytes(plistlib.dumps({'Label': service, 'ProgramArguments': [str(executable), '--mach-service', service],
                                     'MachServices': {service: True}}))
    state['loaded'] = True
    if mode == 'partial_install':
        finish(17)
    if mode == 'unowned_plist':
        plist.write_bytes(plistlib.dumps({'Label': 'someone.else'}))
        finish(17)
    record['state'] = 'installed'
    if mode == 'registered_unowned_plist':
        plist.write_bytes(plistlib.dumps({'Label': 'someone.else'}))
    if mode == 'malformed_install_reply':
        print('not JSON')
        finish()
    reply({'runner': record, 'plist_path': str(plist)})
if argv[2] == 'verify':
    reply({'runner_pid': os.getpid()}, ok=mode != 'connection_failure')
assert argv[2:] == ['remove', '--id', 'owned-id'], 'removal did not target the owned registration'
if mode == 'remove_failure':
    finish(17)
owned = next(r for r in state['runners'] + state['pending_cleanup'] if r['id'] == 'owned-id')
state['runners'] = [r for r in state['runners'] if r['id'] != 'owned-id']
state['pending_cleanup'] = [owned] if mode == 'remove_warning' else []
if mode not in ('remove_warning', 'remove_lies'):
    state['loaded'] = False
    plist.unlink(missing_ok=True)
if mode == 'remove_warning':
    plist.unlink(missing_ok=True)
reply({'warnings': ['bootout failed'] if mode == 'remove_warning' else [],
       'cleanup_retained': mode == 'remove_warning'})
