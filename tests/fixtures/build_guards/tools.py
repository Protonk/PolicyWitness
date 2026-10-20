#!/usr/bin/env -S ${PW_PYTHON} -B
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
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


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
    result = subprocess.run(argv, pass_fds=lock_fds())
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
        stream.write(json.dumps(dict(tool=tool, args=args, executed=argv, status=result.returncode, injected=injected)) + '\n')
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
