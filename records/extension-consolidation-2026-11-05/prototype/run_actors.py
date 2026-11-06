#!/usr/bin/env python3
"""Build and run isolated signed production-actor driver; no runner install.

Usage: run_actors.py NEW_OUTPUT APP IDENTITY
All artifacts stay in NEW_OUTPUT. A unique App Sandbox container is recorded;
its removal is attempted only if this invocation created it.
"""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import signal
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import extension_actors as a
out, app = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
identity = sys.argv[3]
out.mkdir(parents=True, exist_ok=False)

def save(name, value):
    (out / name).write_text(json.dumps(value, indent=2) + '\n')

def command(name, args, check=True, timeout=300):
    p = subprocess.Popen([str(x) for x in args], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(p.pid, signal.SIGKILL)
        stdout, stderr = p.communicate()
    (out / (name + '.stdout')).write_bytes(stdout)
    (out / (name + '.stderr')).write_bytes(stderr)
    save(name + '.command.json', dict(argv=[str(x) for x in args], rc=p.returncode,
                                    deadline=timed_out, supervisor_pid=p.pid))
    if check:
        assert not timed_out and p.returncode == 0, name
    return stdout

package = out / 'package'
shutil.copytree(ROOT / 'runner/Sources', package / 'Sources')
(package / 'Sources/AuthorityPrototype').mkdir()
shutil.copyfile(Path(__file__).with_name('main.swift'), package / 'Sources/AuthorityPrototype/main.swift')
manifest = (ROOT / 'runner/Package.swift').read_text()
start = manifest.index('        .executableTarget(')
manifest = manifest[:start] + '''        .executableTarget(name: "AuthorityPrototype", dependencies: ["PWRunnerCore"])
    ]
)
'''
(package / 'Package.swift').write_text(manifest)
save('sources.json', {str(p.relative_to(package)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in package.rglob('*') if p.is_file()})
command('os', ['/usr/bin/sw_vers'])
command('build', ['/usr/bin/xcrun', 'swift', 'build', '--package-path', package,
                  '--scratch-path', out / 'build', '--product', 'AuthorityPrototype'])
bin_path = command('bin-path', ['/usr/bin/xcrun', 'swift', 'build', '--package-path', package,
                                '--scratch-path', out / 'build', '--show-bin-path']).decode().strip()
host = Path(bin_path) / 'AuthorityPrototype'
bundle = app / 'Contents/XPCServices/PWRunner.xpc/Contents/MacOS'
selected, unentitled = out / 'selected', out / 'unentitled'
for target in (selected, unentitled):
    shutil.copyfile(bundle / 'pw-probe-runner', target)
    target.chmod(0o755)
unsigned_hash = hashlib.sha256(selected.read_bytes()).hexdigest()
assert unsigned_hash == hashlib.sha256(unentitled.read_bytes()).hexdigest()
entitled_plist = out / 'selected.plist'
entitled_plist.write_bytes(plistlib.dumps({'com.apple.security.cs.allow-jit': True}))

def sign(name, binary, plist=None):
    args = ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp', '-s', identity]
    if plist:
        args += ['--entitlements', plist]
    command('sign-' + name, args + [binary])
    command('verify-' + name, ['/usr/bin/codesign', '--verify', '--strict', '--verbose=2', binary])
    command('signature-' + name, ['/usr/bin/codesign', '-dvvv', binary])
    raw = command('entitlements-' + name, ['/usr/bin/codesign', '-d', '--entitlements', ':-', binary])
    return plistlib.loads(raw) if raw.strip() else {}

assert sign('host', host, entitled_plist) == {'com.apple.security.cs.allow-jit': True}
assert sign('selected', selected, entitled_plist) == {'com.apple.security.cs.allow-jit': True}
assert sign('unentitled', unentitled) == {}
target = out / 'target'
contents = b'PW production actor equipment\n'
target.write_bytes(contents)
schema = json.loads((ROOT / 'docs/contract.json').read_text())['versions']['request_schema']
policy = '(version 1)(allow default)(deny file-read-data)(allow file-read-data (extension "com.apple.app-sandbox.read"))'
spec = dict(schema_version=schema, specimen_id='equipment', actors=[a.unapplied_actor('issuer'), a.apply_actor('subject', policy)], phases=[
    dict(phase_id='baseline', actor_id='subject', actions=[a.read_probe('before', target)]),
    dict(phase_id='supply', actor_id='issuer', actions=[a.read_probe('issuer_read', target), a.issue('issue', 't', target), a.transfer('transfer', 't', 'subject', 'd')]),
    dict(phase_id='consume', actor_id='subject', actions=[a.consume('consume', 'd', 'h')]),
    dict(phase_id='access', actor_id='subject', actions=[a.read_probe('after', target), a.release('release', 'h')]),
    dict(phase_id='released', actor_id='subject', actions=[a.read_probe('after_release', target)])])

def run(name, request, workers):
    save(name + '.request.json', request)
    raw = command(name, [host, out / (name + '.request.json'), *workers, bundle / 'sb_api_validator'], timeout=90)
    result = json.loads(raw)
    assert result['quiescence'] == ['reaped'] * len(workers), result
    reply = result['reply']
    assert reply['normalized_outcome'] == 'ok', reply
    pids = {r['launch']['pid'] for r in reply['actors']}
    assert len(pids) == len(workers)
    for row in result['live_processes']:
        assert row['pid'] in pids
        assert row['guest_rc'] == row['validity_rc'] == row['static_code_rc'] == row['signing_rc'] == 0, row
        assert Path(row['path']).resolve() == Path(workers[row['actor']]).resolve(), row
    for row in reply['actors']:
        assert row['subprocess']['reaped'] and row['subprocess']['exit_code'] == 0, row
    assert target.read_bytes() == contents
    return result

def reads(result):
    return {s['step_id']: s['attempt'] for s in result['reply']['steps']}

principal = run('principal', spec, [unentitled, selected])
observed = reads(principal)
assert observed['before']['rc'] != 0
assert observed['issuer_read']['fresh_read']['content_hex'] == contents.hex()
assert observed['after']['fresh_read']['content_hex'] == contents.hex()
for row in principal['live_processes']:
    expected = {} if row['actor'] == 0 else {'com.apple.security.cs.allow-jit': True}
    assert row['entitlements'] == expected, row
events = {e['step_id']: e for e in principal['reply']['extension_events']}
assert events['issue']['native_nonnull']
assert events['consume']['native_result'] != -1
assert events['release']['result_published']
substitution = run('same_selected_substitution', spec, [selected, selected])
assert all(r['entitlements'].get('com.apple.security.cs.allow-jit') is True for r in substitution['live_processes'])
save('substitution-control.json', {'rejected_unentitled_claim': any(r['actor'] == 0 and r['entitlements'] != {} for r in substitution['live_processes']),
                                'meaning': 'live code identity/read-back rejects the claimed equipment despite a successful extension lifecycle'})

identifier = 'com.policywitness.test.equipment-' + uuid.uuid4().hex
restricted_bundle = out / 'Restricted.app'
(restricted_bundle / 'Contents/MacOS').mkdir(parents=True)
restricted = restricted_bundle / 'Contents/MacOS/pw-probe-runner'
shutil.copyfile(bundle / 'pw-probe-runner', restricted)
restricted.chmod(0o755)
(restricted_bundle / 'Contents/Info.plist').write_bytes(plistlib.dumps(dict(CFBundleIdentifier=identifier,
    CFBundleExecutable='pw-probe-runner', CFBundlePackageType='APPL', CFBundleVersion='0')))
sandbox_plist = out / 'sandbox.plist'
sandbox_plist.write_bytes(plistlib.dumps({'com.apple.security.app-sandbox': True}))
assert sign('restricted', restricted_bundle, sandbox_plist) == {'com.apple.security.app-sandbox': True}
container = Path.home() / 'Library/Containers' / identifier
ownership = dict(identifier=identifier, container=str(container), before=container.exists(), after=None, removed=None)
save('container-ownership.json', ownership)
restriction_spec = dict(schema_version=schema, specimen_id='unapplied_restriction', actors=[a.unapplied_actor('subject')],
    phases=[dict(phase_id='read', actor_id='subject', actions=[a.read_probe('target', target),
               a.read_probe('system', '/System/Library/CoreServices/SystemVersion.plist')])])
try:
    baseline = run('unapplied_baseline', restriction_spec, [selected])
    restriction = run('unapplied_restricted', restriction_spec, [restricted])
    assert reads(baseline)['target']['fresh_read']['content_hex'] == contents.hex()
    assert reads(restriction)['target']['rc'] != 0
    assert reads(restriction)['system']['rc'] == 0
    assert restriction['reply']['actors'][0]['setup_status'] == 'unapplied_declared'
    assert restriction['reply']['actors'][0]['application_count'] == 0
    assert restriction['live_processes'][0]['entitlements']['com.apple.security.app-sandbox'] is True
finally:
    ownership['after'] = container.exists()
    if not ownership['before'] and ownership['after']:
        command('remove-container', ['/bin/rm', '-rf', container], check=False)
        ownership['removed'] = not container.exists()
    save('container-ownership.json', ownership)
save('summary.json', dict(principal='passed', same_selected_substitution='unentitled_claim_rejected',
     unapplied_restriction='observed', pre_sign_worker_sha256=unsigned_hash,
     signed_hashes={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (host, selected, unentitled, restricted)},
     container=ownership, limitation='No XPC/registry/equipment admission implementation; allow-jit is a distinguishing granted key, not an effective-authority claim.'))
print('Production actor equipment prototype passed; see summary.json and container-ownership.json')
