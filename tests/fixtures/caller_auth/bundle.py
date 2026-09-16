"""Disposable built-in XPC apps, assembled from the selected production app.

This fixture owns signing and command capture, not authorization expectations.
Never re-sign a launched bundle: each service gets a unique identity beforehand.
"""
import json
import os
from pathlib import Path
import plistlib
import re
import secrets
import shutil
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
from artifact import digest, inventory

CLIENT = Path('Contents/MacOS/pw-runner-client')
SERVICE = Path('Contents/XPCServices/PWRunner.xpc')


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def command(out, argv, *, timeout=30, check=True):
    out.mkdir(parents=True)
    meta = {'argv': list(map(str, argv)), 'returncode': None, 'harness_timeout': False}
    save(out / 'command.json', meta)
    started = time.monotonic()
    try:
        with (out / 'stdout').open('wb') as stdout, (out / 'stderr').open('wb') as stderr:
            result = subprocess.run(meta['argv'], stdout=stdout, stderr=stderr, timeout=timeout)
        meta['returncode'] = result.returncode
    except subprocess.TimeoutExpired:
        meta['harness_timeout'] = True
        raise
    finally:
        meta['elapsed_seconds'] = time.monotonic() - started
        save(out / 'command.json', meta)
    if check and meta['returncode'] != 0:
        raise AssertionError(f'command failed: {out}: {(out / "stderr").read_text()}')
    return meta


def signature(path, out, *, invoke=command):
    invoke(out, ['/usr/bin/codesign', '-d', '--verbose=4', '--entitlements', '-', path])
    text = (out / 'stderr').read_text()
    fields = dict(re.findall(r'^(Identifier|TeamIdentifier|CDHash|Timestamp)=(.*)$', text, re.M))
    fields.update(adhoc='Signature=adhoc' in text,
                  runtime=bool(re.search(r'flags=0x[0-9a-f]+\([^\n]*\bruntime\b', text)),
                  entitlements=(out / 'stdout').read_text().strip())
    save(out / 'signature.json', fields)
    return fields


def sign(path, identity, identifier, out):
    # Match build.sh's hardened runtime and trusted timestamp. Preserve the
    # selected binary's embedded entitlements, rather than adding test privileges.
    argv = ['/usr/bin/codesign', '--force', '--options', 'runtime',
            '--preserve-metadata=entitlements', '--identifier', identifier, '-s', identity]
    if identity != '-':
        argv.append('--timestamp')
    command(out, [*argv, path], timeout=90)


def candidate(source, work, out, identity, identifier):
    path = work / out.name / 'pw-runner-client'
    path.parent.mkdir()
    shutil.copy2(source / CLIENT, path)
    sign(path, identity, identifier, out / 'sign')
    return path


def prepare(source, work, out, identity, client, *, allow_identifier=None, auth_off=False):
    app = work / out.name / 'PolicyWitness.app'
    app.parent.mkdir()
    command(out / 'copy', ['/usr/bin/ditto', source, app])
    service_id = 'com.policywitness.test.auth.s' + secrets.token_hex(12)
    app_id = 'com.policywitness.test.auth.a' + secrets.token_hex(12)
    shutil.copy2(client, app / CLIENT)
    # This unchanged, signed client proves the restricted endpoint is reachable
    # after the negative call and lets its otherwise idle host reply and exit.
    recovery = app / 'Contents/MacOS/pw-runner-client.authorized'
    shutil.copy2(source / CLIENT, recovery)
    for bundle, identifier in ((app, app_id), (app / SERVICE, service_id)):
        path = bundle / 'Contents/Info.plist'
        plist = plistlib.loads(path.read_bytes())
        plist['CFBundleIdentifier'] = identifier
        if bundle != app:
            if allow_identifier is not None:
                plist['PWRunnerAllowedIdentifiers'].append(allow_identifier)
            if auth_off:
                plist['PWRunnerRequireSignedCaller'] = False
            save(out / 'runner-info.json', plist)
        path.write_bytes(plistlib.dumps(plist))
    # The nested tools retain their original signatures. Seal the changed
    # service, then the outer app. --deep is verification only, never signing.
    sign(app / SERVICE, identity, service_id, out / 'sign-service')
    sign(app, identity, app_id, out / 'sign-app')
    command(out / 'verify', ['/usr/bin/codesign', '--verify', '--deep', '--strict', app])
    assert digest(app / CLIENT) == digest(client), 'outer signing changed the candidate client'
    assert digest(recovery) == digest(source / CLIENT), 'authorized control client changed'
    return {'app': app, 'client': app / CLIENT, 'authorized_client': recovery,
            'service': service_id, 'app_id': app_id, 'out': out}


def cleanup_processes(work, out):
    """Only stop binaries whose full executable paths belong to this fixture."""
    observations = []

    def owned():
        result = subprocess.run(['/bin/ps', '-axo', 'pid=,comm='],
                                capture_output=True, text=True, timeout=5, check=True)
        return {int(parts[0]): parts[1] for line in result.stdout.splitlines()
                if len(parts := line.strip().split(None, 1)) == 2
                and parts[1].startswith(str(work) + '/')}

    try:
        # Successful hosts exit shortly after replying. Rejected connections can
        # leave idle hosts; cleanup is not counted as authorization evidence.
        for sig in (None, signal.SIGTERM, signal.SIGKILL):
            processes = owned()
            observations.append({'signal': sig, 'processes': processes})
            for pid in processes if sig is not None else ():
                try:
                    os.kill(pid, sig)
                except ProcessLookupError:
                    pass
            deadline = time.monotonic() + 2
            while processes and time.monotonic() < deadline:
                time.sleep(0.05)
                processes = owned()
            if not processes:
                return
        raise AssertionError(f'fixture processes survived cleanup: {processes}')
    finally:
        save(out / 'cleanup.json', observations)
