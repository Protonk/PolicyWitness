"""Independent fake OS/CLI commands with durable receipts; never calls real tools."""
import json
from pathlib import Path
import plistlib
import shutil
import sys

config = json.loads(Path(sys.argv[1]).read_text())
argv = sys.argv[2:]
mode = config['mode']
state_path = Path(config['state'])
state = json.loads(state_path.read_text()) if state_path.exists() else {'loaded': False, 'runners': [config['unrelated']]}
ownership = json.loads((Path(config['out']) / 'session.json').read_text())
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
    assert '-s' not in argv, 'fixture must delegate signing to the public installer'
    target = Path(argv[-1])
    staged = target == bundle
    if '--verify' in argv:
        if mode == 'bad_source_signature' and not staged:
            finish(7)
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
        if ent is not None:
            sys.stdout.buffer.write(plistlib.dumps(ent))
            sys.stdout.buffer.flush()
        finish()
    identifier = service if staged else 'pw-runner-client' if target.name == 'pw-runner-client' else 'fixture.source'
    team = 'WRONG' if mode == 'wrong_team' and staged else 'FIXTURETEAM'
    print(f'Identifier={identifier}\nTeamIdentifier={team}\nCDHash=fixture\n'
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
if argv[2] == 'list':
    reply({'runners': state['runners']})
if argv[2] == 'install':
    target = Path(argv[argv.index('--bundle') + 1])
    assert target == bundle and target.resolve() == target
    assert target != Path(config['source']) and target.parent.parent == Path('/private/tmp')
    assert '--allow-adhoc' not in argv and argv[argv.index('--identity') + 1] == 'fixture identity'
    if '--entitlements' in argv:
        receipt['entitlements'] = plistlib.loads(Path(argv[argv.index('--entitlements') + 1]).read_bytes())
    assert receipt.get('entitlements') == config['entitlements'], 'entitlements were not preserved'
    if mode == 'sign_failure':
        finish(17)
    executable = bundle / 'Contents/MacOS/PWRunner'
    executable.write_bytes(executable.read_bytes() + b' signed')
    if mode == 'helper_changed':
        (bundle / 'Contents/MacOS/pw-probe-runner').write_bytes(b'changed helper')
    plist.parent.mkdir(parents=True, exist_ok=True)
    plist.write_bytes(plistlib.dumps({'Label': service, 'ProgramArguments': [str(executable), '--mach-service', service],
                                     'MachServices': {service: True}}))
    state['loaded'] = True
    if mode == 'partial_install':
        finish(17)
    if mode == 'unowned_plist':
        plist.write_bytes(plistlib.dumps({'Label': 'someone.else'}))
        finish(17)
    record = {'id': 'owned-id', 'service_name': service, 'scope': 'user', 'bundle_path': str(bundle)}
    state['runners'].append(record)
    if mode == 'registered_unowned_plist':
        plist.write_bytes(plistlib.dumps({'Label': 'someone.else'}))
    if mode == 'malformed_install_reply':
        print('not JSON')
        finish()
    reply({'runner': record, 'plist_path': str(plist)})
if argv[2] == 'verify':
    reply({}, ok=mode != 'connection_failure')
assert argv[2:] == ['remove', '--id', 'owned-id'], 'removal did not target the owned registration'
if mode == 'remove_failure':
    finish(17)
state['runners'] = [r for r in state['runners'] if r['id'] != 'owned-id']
if mode not in ('remove_warning', 'remove_lies'):
    state['loaded'] = False
    plist.unlink()
reply({'warnings': ['bootout failed'] if mode == 'remove_warning' else []})
