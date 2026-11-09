"""An unapplied actor inherits its worker's own restriction.

`unapplied` means PolicyWitness applies no policy; it does not mean the actor
is unrestricted. This control places an owned copy of the installed worker in
a minimal bundle (the App Sandbox initializer takes its container identifier
from the signature's bundle identifier and aborts a bare executable), signs it
with the App Sandbox entitlement under a fixed test identifier, and launches it
through the owned host with an explicit selected-equipment test override. The same unapplied request
runs on the ordinary installed worker as the baseline, and the test process
reads the target itself. Under the restricted worker the test-owned target read
fails while a system file the App Sandbox permits still reads; the validator's
query for that actor's PID is the independent observation of the inherited
state. The entitlement is read back from the signed copy. The App Sandbox
initializer creates a container for the copy's fixed test identifier under
the user's Library; removing it needs Full Disk Access, which this harness
does not assume, so the container's presence before and after and the
removal attempt's result are recorded rather than asserted.
"""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve()
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parents[3] / 'lib')]
ROOT = HERE.parents[4]
from witness_capture import capture  # noqa: E402
import extension_actors  # noqa: E402
import build_context
from worker_exit_witness import worker_exit_witness  # noqa: E402
sys.path[:0] = [str(ROOT / 'tests/fixtures/byoxpc'), str(ROOT / 'tests/fixtures/caller_auth')]
import session  # noqa: E402
from bundle import command, save, signature  # noqa: E402

pw, directory, identity = sys.argv[1:]
out = Path(directory)
state = json.loads((out / 'session.json').read_text())
staging, bundle = Path(state['staging']), Path(state['bundle_path'])
assert bundle == staging / 'PWRunner.xpc' and staging.parent == Path('/private/tmp')
receipts = out / 'actor-inherited-restriction'
receipts.mkdir()
SANDBOX_KEY = 'com.apple.security.app-sandbox'
AVAILABLE = '/System/Library/CoreServices/SystemVersion.plist'

# ---- The owned restricted worker: the installed worker's bytes, re-signed with
# the App Sandbox entitlement under a unique identifier, outside the bundle.
installed = bundle / 'Contents/MacOS/pw-probe-runner'
identifier = 'com.policywitness.test.restricted-worker'
container = Path.home() / 'Library/Containers' / identifier
container_before = container.exists()
workspace = staging / 'restricted-worker'
workspace.mkdir()
bundle_copy = workspace / 'RestrictedWorker.app'
(bundle_copy / 'Contents/MacOS').mkdir(parents=True)
(bundle_copy / 'Contents/Info.plist').write_bytes(plistlib.dumps({
    'CFBundleIdentifier': identifier, 'CFBundleExecutable': 'pw-probe-runner', 'CFBundleName': 'RestrictedWorker',
    'CFBundlePackageType': 'APPL', 'CFBundleShortVersionString': '0', 'CFBundleVersion': '0'}))
restricted = bundle_copy / 'Contents/MacOS/pw-probe-runner'
shutil.copyfile(installed, restricted)
restricted.chmod(0o755)
assert hashlib.sha256(restricted.read_bytes()).hexdigest() == hashlib.sha256(installed.read_bytes()).hexdigest()
ownership = dict(kind='restricted-worker-control', workspace=str(workspace), artifacts=str(receipts),
                 run_id=os.environ.get('PW_TEST_RUN_ID'), identifier=identifier,
                 container=str(container), container_before=container_before, container_after=None,
                 container_removed=None, removal_error=None)
# Keep a separate durable receipt when this run could create a new container.
# Verified runner removal may delete session staging; it does not settle this
# independently owned resource or authorize deletion of a preexisting one.
recovery_root = None if container_before else Path(tempfile.mkdtemp(prefix='pw-container-recovery-', dir='/private/tmp'))
ownership['state_path'] = str((recovery_root or workspace) / 'ownership.json')
ownership['recovery_state'] = 'not_owned_preexisting' if container_before else 'pending_observation'
session.persist_state(ownership, receipts / 'ownership.json')
if recovery_root is not None:
    session.save(workspace / 'ownership.json', ownership)
base = session.entitlements(installed, receipts, 'installed-worker-entitlements', command) or {}
assert base.get(SANDBOX_KEY) is not True, ('installed worker is already sandboxed', base)
supplied = dict(base, **{SANDBOX_KEY: True})
plist = workspace / 'restricted.plist'
plist.write_bytes(plistlib.dumps(supplied))
command(receipts / 'sign-restricted', ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp',
        '-s', identity, '--entitlements', plist, bundle_copy], timeout=90)
readback = session.entitlements(restricted, receipts, 'restricted-worker-entitlements', command)
assert readback == supplied, (readback, supplied)
signed = signature(restricted, receipts / 'restricted-signature')
assert signed['Identifier'] == identifier, signed
ownership['signed_worker_sha256'] = hashlib.sha256(restricted.read_bytes()).hexdigest()
ownership['signature_identifier'] = signed['Identifier']
session.persist_state(ownership, receipts / 'ownership.json')
command(receipts / 'verify-restricted', ['/usr/bin/codesign', '--verify', '--strict', '--verbose=2', bundle_copy])

targets = staging / 'actor-targets'
targets.mkdir(exist_ok=True)
target = targets / 'restricted-target'
contents = b'PW inherited restriction target\n'
target.write_bytes(contents)
assert target.read_bytes() == contents  # the test process's own baseline read
read = extension_actors.read_probe


def request(name, override):
    spec = {'contract': build_context.candidate_contract(), 'specimen_id': name,
            'actors': [dict(extension_actors.unapplied_actor('R'), equipment='selected')],
            'phases': [{'phase_id': 'reads', 'actor_id': 'R',
                        'actions': [read('owned_target', target), read('system_file', AVAILABLE)]}]}
    if override:
        spec['_test_overrides'] = {'actor_equipment_executable_paths': {'selected': str(restricted)}}
        spec['actors'][0]['equipment'] = 'selected'
    return spec


def observe(name, override):
    envelope, runner = capture(pw, receipts, name, request(name, override), session_state=state)
    assert runner['execution_form'] == 'actors' and runner['normalized_outcome'] == 'finished', (runner['normalized_outcome'], runner.get('error'))
    witnessed, reason = worker_exit_witness(envelope)
    assert witnessed, reason
    actor, = runner['actors']
    assert actor['setup_status'] == 'unapplied_declared' and actor.get('applied') is None, actor
    assert actor['subprocess']['reaped'] and actor['subprocess']['exit_code'] == 0, actor
    ownership.setdefault('workers', []).append(dict(case=name, pid=actor['launch']['pid'],
        reaped=actor['subprocess']['reaped'], exit_code=actor['subprocess']['exit_code']))
    session.persist_state(ownership, receipts / 'ownership.json')
    steps = {s['step_id']: s for s in runner['steps']}
    for step in steps.values():
        assert step['attempt']['result_source'] == 'worker', step
        assert step['sandbox_check']['outcome'] in ('allow', 'deny'), ('validator query did not run', step['sandbox_check'])
        assert step['sandbox_check']['pid'] == actor['launch']['pid'], ('query not bound to the actor', step['sandbox_check'])
    row = {step_id: dict(attempt=s['attempt']['outcome'], rc=s['attempt']['rc'], errno=s['attempt'].get('errno'),
                         query=s['sandbox_check']['outcome'], query_pid=s['sandbox_check']['pid'])
           for step_id, s in steps.items()}
    row['actor'] = dict(pid=actor['launch']['pid'], setup_status=actor['setup_status'],
                        equipment=actor['equipment'],
                        worker=envelope['data']['specimen']['binaries'].get('worker'),
                        inherited_descriptors=actor['launch']['inherited_descriptors'])
    return row, steps


observations = {}
try:
    # ---- Baseline: the ordinary installed worker, unapplied, reads both.
    baseline, steps = observe('baseline', override=False)
    assert steps['owned_target']['attempt']['rc'] == 0 and steps['owned_target']['attempt']['fresh_read']['content_hex'] == contents.hex(), baseline
    assert steps['system_file']['attempt']['rc'] == 0, baseline
    assert baseline['owned_target']['query'] == 'allow' and baseline['system_file']['query'] == 'allow', baseline
    observations['baseline'] = baseline

    # ---- Restricted: the App Sandbox worker, still unapplied by PolicyWitness.
    restricted_row, steps = observe('restricted', override=True)
    container_after = container.exists()
    owned, system = steps['owned_target']['attempt'], steps['system_file']['attempt']
    assert owned['outcome'] == 'read_failed' and owned['rc'] != 0, ('inherited restriction not observed', owned)
    assert system['rc'] == 0, ('available access under the restriction failed', system)
    assert restricted_row['owned_target']['query'] == 'deny', ('validator did not observe the inherited denial', restricted_row)
    assert restricted_row['system_file']['query'] == 'allow', restricted_row
    assert restricted_row['actor']['pid'] != baseline['actor']['pid']
    assert target.read_bytes() == contents
    restricted_row['container_created'] = container_after
    observations['restricted'] = restricted_row
finally:
    ownership['container_after'] = container.exists()
    if ownership['container_after'] and not ownership['container_before']:
        removal = subprocess.run(['/bin/rm', '-rf', str(container)], capture_output=True, text=True, timeout=30)
        ownership['container_removed'] = not container.exists()
        ownership['removal_error'] = removal.stderr.strip() or None
    else:
        ownership['container_removed'] = False
        if ownership['container_before']:
            ownership['removal_error'] = 'preexisting container; cleanup is not owned by this run'
    ownership['recovery_state'] = ('not_owned_preexisting' if ownership['container_before'] else
                                   'unresolved_manual' if ownership['container_after'] and not ownership['container_removed'] else 'settled')
    session.persist_state(ownership, receipts / 'ownership.json')
    session.save(workspace / 'ownership.json', ownership)
    if recovery_root is not None and ownership['recovery_state'] == 'settled':
        # Only this receipt and its uniquely created parent are owned here.
        Path(ownership['state_path']).unlink()
        recovery_root.rmdir()
save(receipts / 'observations.json', dict(identifier=identifier, entitlements=supplied, available_path=AVAILABLE,
                                         target=str(target), observations=observations))
print('unapplied actor on the App Sandbox worker: owned target read refused (errno %s) and queried deny, system file read '
      'and queried allow; the ordinary worker read both; entitlement read back; container %s'
      % (observations['restricted']['owned_target']['errno'],
         'removed' if ownership['container_removed'] else 'retained at %s (%s)' % (container, ownership['removal_error'] or 'not created')))
