#!/usr/bin/env python3
"""Run one specimen denying each supported non-file attempt kind, with log capture.

Usage: live_probe_existing.py POLICY_WITNESS_BIN OUT_DIR

The question is what the kernel's records for these denials look like (operation
spelling, process and PID) beside the controller's associations. A file read
denial is included as a delivery control. Asserts nothing about PW.
"""
import json
import secrets
import subprocess
import sys
import time
from pathlib import Path


def main():
    pw, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=False)
    root = Path('/private/tmp') / f'pw-ak-{secrets.token_hex(6)}'
    root.mkdir()
    denied = root / 'denied_data'
    denied.write_bytes(b'x')
    policy = ('(version 1) (allow default) '
              '(deny mach-lookup (global-name "com.apple.logd")) '
              '(deny sysctl-read (sysctl-name "kern.osrelease")) '
              '(deny process-exec (literal "/usr/bin/true")) '
              f'(deny file-read-data (literal "{denied}"))')
    plan = [
        {'step_id': 'mach', 'sandbox_check': {'operation': 'mach-lookup',
            'filter': {'kind': 'global_name', 'value': 'com.apple.logd'}},
         'attempt': {'kind': 'mach_lookup', 'action': 'bootstrap_look_up', 'target': 'com.apple.logd'}},
        {'step_id': 'sysctl', 'sandbox_check': {'operation': 'sysctl-read',
            'filter': {'kind': 'sysctl_name', 'value': 'kern.osrelease'}},
         'attempt': {'kind': 'sysctl', 'action': 'read', 'target': 'kern.osrelease'}},
        {'step_id': 'exec', 'sandbox_check': {'operation': 'process-exec*',
            'filter': {'kind': 'path', 'value': '/usr/bin/true'}},
         'attempt': {'kind': 'exec', 'action': 'spawn', 'target': '/usr/bin/true'}},
        {'step_id': 'read', 'sandbox_check': {'operation': 'file-read-data',
            'filter': {'kind': 'path', 'value': str(denied)}},
         'attempt': {'kind': 'file', 'action': 'open_read', 'target': str(denied)}},
    ]
    request = {'schema_version': 5, 'specimen_id': 'attempt_kind_existing_probe',
               'policy': {'format': 'sbpl', 'sbpl_source': policy}, 'probe_plan': plan}
    (out / 'request.json').write_text(json.dumps(request, indent=2))
    started = time.time()
    proc = subprocess.run([str(pw), 'run', str(out / 'request.json')], capture_output=True, timeout=180)
    ended = time.time()
    (out / 'envelope.json').write_bytes(proc.stdout)
    (out / 'stderr.txt').write_bytes(proc.stderr)
    (out / 'observations.json').write_text(json.dumps(
        {'pw': str(pw), 'returncode': proc.returncode, 'started': started, 'ended': ended,
         'root': str(root)}, indent=2))
    denied.unlink()
    root.rmdir()
    print(f'returncode={proc.returncode} stdout_bytes={len(proc.stdout)} root_removed={not root.exists()}')


if __name__ == '__main__':
    main()
