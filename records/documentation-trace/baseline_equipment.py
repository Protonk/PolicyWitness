"""Inspect local prerequisites without building, signing, or running suites."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
commands = [
    ['uname', '-m'], ['sw_vers'], ['sysctl', '-n', 'hw.optional.arm64'],
    ['sysctl', '-n', 'sysctl.proc_translated'], ['xcode-select', '-p'],
    ['xcrun', '--sdk', 'macosx', '--show-sdk-version'],
    ['clang', '--version'], ['swift', '--version'], ['cargo', '--version'],
    ['rustc', '--version'], ['rustup', '--version'], ['rustup', 'target', 'list', '--installed'],
    ['rustfmt', '--version'], ['meson', '--version'], ['ninja', '--version'],
    ['security', 'list-keychains', '-d', 'user'],
]
observations = []
for argv in commands:
    try:
        run = subprocess.run(argv, capture_output=True, text=True, timeout=20)
        observations.append(dict(argv=argv, executable=shutil.which(argv[0]), exit_code=run.returncode,
                                 stdout=run.stdout, stderr=run.stderr))
    except (OSError, subprocess.TimeoutExpired) as error:
        observations.append(dict(argv=argv, error=str(error)))
sys.path.insert(0, str(ROOT / 'tests/lib'))
import pytest_packages
try:
    target, manifest = pytest_packages.target(ROOT)
    pytest = dict(valid=True, target=str(target), packages=[item['filename'] for item in manifest['lock']['packages']])
except (OSError, ValueError) as error:
    pytest = dict(valid=False, error=str(error))
targets = {}
for name in ('/etc/hosts', '/usr/share/dict/propernames', '/usr/share/dict/connectives'):
    try:
        path = Path(name)
        stat = path.stat()
        with path.open('rb') as stream:
            data = stream.read(4096)
        targets[name] = dict(regular=path.is_file(), device=stat.st_dev, inode=stat.st_ino,
                             size=stat.st_size, prefix_bytes=len(data), prefix_sha256=hashlib.sha256(data).hexdigest())
    except OSError as error:
        targets[name] = dict(error=str(error))
result = dict(python_executable=sys.executable, python_version=sys.version, commands=observations,
              pytest=pytest, example_targets=targets,
              app_present=(ROOT / 'dist/PolicyWitness.app/Contents/MacOS/policy-witness').is_file(),
              signing_identity_observation=dict(sandbox_stdout='     0 valid identities found\n',
                  escalated_stdout='  1) 1A6E85D06FC762993C8BD3E932556DED3985F030 "Developer ID Application: Adam Hyland (42D369QV8E)"\n     1 valid identities found\n',
                  command=['security', 'find-identity', '-v', '-p', 'codesigning'],
                  private_key_signing_tested=False))
destination = Path(__file__).with_name('baseline-equipment.json')
destination.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, indent=2))
