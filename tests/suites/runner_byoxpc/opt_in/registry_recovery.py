"""Real filesystem/CLI and GUI-domain controls; every service is uniquely owned.

HOME and PW_RUNNER_REGISTRY are supplied only to fixture child processes.
Durable staging owns recovery independently of the case's disposable output.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import secrets
import shutil
import subprocess
import sys
import tempfile

out, app, pw = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
staging = Path(tempfile.mkdtemp(prefix='pw-byoxpc-registry-', dir='/private/tmp'))
fixture_home = staging / 'home'
agents = fixture_home / 'Library/LaunchAgents'
agents.mkdir(parents=True)
registry = staging / 'registry/runners.json'
registry.parent.mkdir()
env = dict(os.environ, HOME=str(fixture_home), PW_RUNNER_REGISTRY=str(registry))
services, observations = [], []
sequence = 0


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def command(args, code=0, *, label='command'):
    global sequence
    sequence += 1
    result = subprocess.run([str(pw), *map(str, args)], env=env, capture_output=True, timeout=30)
    destination = out / f'{sequence:03d}-{label}'
    destination.mkdir(parents=True)
    (destination / 'stdout').write_bytes(result.stdout)
    (destination / 'stderr').write_bytes(result.stderr)
    save(destination / 'receipt.json', dict(argv=list(map(str, args)), returncode=result.returncode))
    assert result.returncode == code, (args, result.returncode, result.stdout, result.stderr)
    return result


def data(args, **kwargs):
    return json.loads(command(args, **kwargs).stdout)['data']


def records():
    return data(['runner', 'list'])


def prepare():
    service = 'com.policywitness.test.registry.s' + secrets.token_hex(12)
    bundle = staging / service / 'PWRunner.xpc'
    shutil.copytree(app / 'Contents/XPCServices/PWRunner.xpc', bundle)
    info_path = bundle / 'Contents/Info.plist'
    info = plistlib.loads(info_path.read_bytes())
    info['CFBundleIdentifier'] = service
    info.pop('PWRunnerRequireSignedCaller', None)
    info.pop('PWRunnerAllowedIdentifiers', None)
    info_path.write_bytes(plistlib.dumps(info))
    services.append(dict(service=service, bundle_path=str(bundle), plist_path=str(agents / (service + '.plist'))))
    save(staging / 'recovery.json', dict(registry=str(registry), fixture_home=str(fixture_home), services=services))
    return service, bundle, agents / (service + '.plist')


def install(bundle, *, live=False, code=0):
    args = ['runner', 'install', '--bundle', bundle, '--identity', '-', '--allow-adhoc']
    if not live: args.append('--skip-bootstrap')
    result = command(args, code=code, label='install')
    return json.loads(result.stdout)['data'] if code == 0 else result


def remove(service, *, retained=False, skip=False):
    args = ['runner', 'remove', '--service-name', service]
    if skip: args.append('--skip-bootout')
    result = data(args, label='remove')
    assert result['cleanup_retained'] is retained, result
    return result


failure = None
try:
    service, bundle, plist = prepare()
    installed = install(bundle)
    assert installed['state'] == installed['runner']['state'] == 'installed'
    assert not installed['bootstrapped'] and installed['loaded']['presence'] == 'absent', installed
    current = json.loads(registry.read_text())
    current['runners'][0]['state'] = 'pending'
    save(registry, current)
    assert data(['runner', 'status', '--service-name', service])['state'] == 'pending'
    specimen = staging / 'pending.json'
    save(specimen, dict(schema_version=3, specimen_id='pending', policy=dict(format='sbpl', sbpl_source='(version 1)\n(allow default)'),
                       runner=dict(mode='byoxpc', service=service), probe_plan=[]))
    rejected = command(['run', specimen, '--no-log-capture'], code=2)
    assert b'external runner is pending installation' in rejected.stderr + rejected.stdout
    remove(service, skip=True)
    observations.append('skip-bootstrap completes installation; pending status and specimen rejection; pending removal')

    for boundary in ('initial_pending_save', 'plist_creation', 'initial_cleanup_save'):
        service, bundle, plist = prepare()
        if boundary == 'initial_cleanup_save': install(bundle)
        before = registry.read_bytes()
        directory = agents if boundary == 'plist_creation' else registry.parent
        directory.chmod(0o500)
        try:
            if boundary == 'initial_cleanup_save':
                result = command(['runner', 'remove', '--service-name', service], code=2)
                assert plist.exists() and registry.read_bytes() == before
            else:
                result = install(bundle, code=2)
                assert not plist.exists()
            assert (b'failed to create' if boundary == 'plist_creation' else b'failed to atomically save') in result.stderr
        finally:
            directory.chmod(0o700)
        current = records()
        if boundary == 'initial_pending_save':
            assert registry.read_bytes() == before
            assert not any(r['service_name'] == service for r in current['runners'])
        else:
            if boundary == 'plist_creation':
                record = next(r for r in current['runners'] if r['service_name'] == service)
                assert record['state'] == 'pending' and b'pending runner' in result.stderr
            remove(service)
        observations.append(boundary)

    service, bundle, plist = prepare()
    install(bundle)
    original = plist.read_bytes()
    foreign = plistlib.loads(original); foreign['Label'] = 'unrelated.owner'
    plist.write_bytes(plistlib.dumps(foreign))
    result = remove(service, retained=True)
    assert result['warnings'] and plistlib.loads(plist.read_bytes())['Label'] == 'unrelated.owner'
    current = records()
    assert not current['runners'] and len(current['pending_cleanup']) == 1
    conflict = install(bundle, code=2)
    assert b'runner remove --service-name' in conflict.stderr
    report = data(['runner', 'reconcile'])
    row = next(r for r in report['records'] if r['runner']['service_name'] == service)
    assert row['recorded_state'] == 'pending_cleanup' and row['plist_ownership'] == 'unowned'
    plist.write_bytes(original)
    remove(service)
    command(['runner', 'remove', '--service-name', service], code=2)
    observations.append('uncertain plist ownership, pending-cleanup conflicts, reconcile and repeated removal')

    service, bundle, plist = prepare()
    install(bundle)
    lock = registry.with_name(registry.name + '.lock')
    with lock.open('r+') as held:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        prior = registry.read_bytes(), plist.read_bytes()
        for args in (['runner', 'validate'], ['runner', 'remove', '--service-name', service],
                     ['runner', 'install', '--bundle', bundle, '--identity', '-', '--allow-adhoc', '--skip-bootstrap']):
            rejected = command(args, code=2)
            assert b'registry busy' in rejected.stderr
        for args in (['runner', 'list'], ['runner', 'status', '--service-name', service], ['runner', 'reconcile']):
            command(args)
        verified = data(['runner', 'verify', '--service-name', service, '--timeout-ms', '100'], code=1)
        assert verified['state'] == 'installed'
        assert (registry.read_bytes(), plist.read_bytes()) == prior
    # Actual modifying child processes contend on one registry and retain one coherent record.
    writers = [subprocess.Popen([pw, 'runner', 'validate'], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(6)]
    for i, writer in enumerate(writers):
        stdout, stderr = writer.communicate(timeout=20)
        save(out / f'writer-{i}.json', dict(returncode=writer.returncode, stdout=stdout.decode(), stderr=stderr.decode()))
        assert writer.returncode in (0, 2)
        if writer.returncode: assert b'registry busy' in stderr
    assert len(records()['runners']) == 1
    remove(service)
    observations.append('concurrent modifying commands; lock-free read commands')

    orphan = agents / 'com.policywitness.test.unregistered.plist'
    orphan.write_bytes(plistlib.dumps(dict(Label='com.policywitness.test.unregistered', ProgramArguments=['/unowned/PWRunner'])))
    report = data(['runner', 'reconcile'])
    assert any(c['service_name'] == 'com.policywitness.test.unregistered' and c['ownership'] == 'unowned' for c in report['candidates'])
    orphan.chmod(0)
    try:
        report = data(['runner', 'reconcile'])
        assert any(e['path'] == str(orphan) and e['presence'] == 'unknown' for e in report['inspection_errors'])
    finally:
        orphan.chmod(0o600); orphan.unlink()
    observations.append('unregistered candidates and unknown inspection failures')

    service, bundle, plist = prepare()
    installed = install(bundle, live=True)
    assert installed['bootstrapped'] and installed['state'] == 'installed'
    data(['runner', 'verify', '--service-name', service])
    result = remove(service, retained=True, skip=True)
    assert result['plist_removed'] and not plist.exists()
    report = data(['runner', 'reconcile'])
    row = next(r for r in report['records'] if r['runner']['service_name'] == service)
    assert row['recorded_state'] == 'pending_cleanup' and row['service']['presence'] == 'present' and row['plist']['presence'] == 'absent'
    # Recovery is driven only by the durable registry and staged bundle pointer.
    disposable = staging / 'original-test-output'
    disposable.mkdir(); save(disposable / 'receipt.json', result)
    shutil.rmtree(disposable)
    assert Path(records()['pending_cleanup'][0]['bundle_path']) == bundle
    remove(service)
    observations.append('live bootstrap; skipped bootout retains service without plist; recovery after output deletion')
except BaseException as error:
    failure = error
finally:
    registry.parent.chmod(0o700); agents.chmod(0o700)
    clean = True
    try:
        current = records()
        for record in current['runners'] + current['pending_cleanup']:
            assert any(r['service'] == record['service_name'] and r['bundle_path'] == record['bundle_path'] for r in services)
            response = data(['runner', 'remove', '--service-name', record['service_name']])
            clean = clean and not response['cleanup_retained']
        for record in services:
            probe = subprocess.run(['/bin/launchctl', 'print', f'gui/{os.getuid()}/{record["service"]}'], capture_output=True, timeout=10)
            clean = clean and probe.returncode != 0 and f'Could not find service "{record["service"]}"'.encode() in probe.stderr
            clean = clean and not Path(record['plist_path']).exists()
    except BaseException as error:
        clean = False
        print(f'cleanup verification failed: {error}', file=sys.stderr)
    save(out / 'controls.json', dict(observations=observations, staging=str(staging), cleanup_verified=clean))
    if clean: shutil.rmtree(staging)
    else: raise RuntimeError(f'recovery retained at {staging}; inspect recovery.json and registry') from failure
if failure is not None: raise failure
print(f'{len(observations)} registry controls passed; owned service/plist absence verified')
