#!/usr/bin/env -S ${PW_PYTHON} -B -S
"""Delegate to real tools, injecting one fault at the selected boundary.

The configuration names the real tools, a receipt file and one fault:

  replacements  after a successful `cargo build` or `meson compile`, each
                named target is backed up once and overwritten with the
                source binary (a real Mach-O built for another minimum or
                against another SDK), keeping it executable
  codesign      a `codesign --force` call on the named target runs with the
                replacement argument list instead of the script's flags, so a
                signature is made without a secure timestamp or ad hoc; the
                script's signing list stays intact

Every call runs the real tool otherwise, with the checkout lock descriptors
the claim names passed on as every protected launch must, and records a
receipt naming what was injected. The script's own checks make every refusal.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def lock_fds():
    """The claim's descriptors open in this process; Python would close them in the real tool by default."""
    found = []
    for name in ('PW_CHECKOUT_LOCK_FD', 'PW_CHECKOUT_LOCK_CHANNEL'):
        try:
            fd = int(os.environ.get(name, ''))
            os.fstat(fd)
        except (ValueError, OSError):
            continue
        found.append(fd)
    return tuple(sorted(set(found)))


def inventory_snapshot(bundle):
    path = bundle / 'Contents/Resources/worker-equipment.json'
    if not path.exists():
        return None
    data = path.read_bytes()
    return dict(sha256=hashlib.sha256(data).hexdigest(), manifest=json.loads(data))


def main():
    tool = Path(sys.argv[0]).name
    config = json.loads(Path(os.environ['PW_BUILD_GUARD_CONFIG']).read_text())
    args = sys.argv[1:]
    argv = [config['tools'][tool], *args]
    target = Path(args[-1]) if args else None
    injected = []
    override = config.get('codesign')
    if tool == 'codesign' and override and '--force' in args and target == Path(override['target']):
        argv = ['/usr/bin/codesign', *override['argv'], str(target)]
        injected.append(dict(kind='codesign', target=str(target), argv=argv))
    # Observe the real calls, including both sides of the final inner signing
    # operation. A file present only at seal entry was emitted in that interval;
    # reading source order alone cannot establish this execution fact.
    equipment = None
    if tool == 'codesign' and '--force' in args and target is not None:
        bundle = next((p for p in (target, *target.parents) if p.suffix == '.xpc'), None)
        if bundle is not None:
            equipment = dict(bundle=str(bundle), before=inventory_snapshot(bundle))
            if target.name in ('pw-probe-runner', 'pw-probe-runner-unentitled'):
                equipment['input_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
                equipment['unsigned_worker_sha256'] = hashlib.sha256(Path(config['unsigned_worker']).read_bytes()).hexdigest()
    started_ns = time.monotonic_ns()
    result = subprocess.run(argv, pass_fds=lock_fds())
    finished_ns = time.monotonic_ns()
    if equipment is not None:
        equipment['after'] = inventory_snapshot(Path(equipment['bundle']))
    if result.returncode == 0:
        for replacement in config.get('replacements', []):
            if replacement['tool'] != tool or not args or args[0] != replacement['first']:
                continue
            backups = Path(config['backups'])
            backups.mkdir(parents=True, exist_ok=True)
            for path in replacement['targets']:
                path = Path(path)
                backup = backups / path.name
                if backup.exists():
                    raise RuntimeError('a scenario must inject each target exactly once')
                shutil.copy2(path, backup)
                shutil.copy2(replacement['source'], path)
                path.chmod(0o755)
                injected.append(dict(kind='replacement', target=str(path), source=replacement['source']))
    with Path(config['receipt']).open('a') as stream:
        stream.write(json.dumps(dict(tool=tool, args=args, executed=argv, status=result.returncode, injected=injected, equipment=equipment,
                                     started_ns=started_ns, finished_ns=finished_ns)) + '\n')
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
