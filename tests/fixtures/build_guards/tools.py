#!/usr/bin/python3
"""Delegate to real tools, injecting a bad output only at the selected boundary."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    tool = Path(sys.argv[0]).name
    config = json.loads(Path(os.environ['PW_BUILD_GUARD_CONFIG']).read_text())
    args = sys.argv[1:]
    argv = [config['tools'][tool], *args]
    target = Path(args[-1]) if args else None
    injected = False
    # Keep the build's signing list intact. Simulate a signer that leaves this
    # helper ad hoc, then let the real seal, verification and signer check run.
    if tool == 'codesign' and config['fault'] == 'signer' and '--force' in args:
        if target == Path(config['dist']) / 'PolicyWitness.app/Contents/MacOS/sbpl-check':
            argv = ['/usr/bin/codesign', '--force', '--options', 'runtime', '-s', '-', str(target)]
            injected = True
    result = subprocess.run(argv)
    if result.returncode == 0 and config['fault'] == tool:
        if tool == 'cargo' or (tool == 'meson' and args[0] == 'compile'):
            target = Path(config['target'])
            backup = Path(config['backup'])
            if backup.exists():
                raise RuntimeError('a scenario must inject exactly once')
            shutil.copy2(target, backup)
            shutil.copy2(config['wrong_binary'], target)
            injected = True
    with Path(config['receipt']).open('a') as stream:
        stream.write(json.dumps(dict(tool=tool, args=args, executed=argv,
                                     status=result.returncode, injected=injected)) + '\n')
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
