"""Explicit immutable test-package target; never provision during collection/run."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile
import urllib.request
import zipfile

from pytest_support import digest, read, write, value_digest


def identity(root):
    lock = read(root / 'tests/requirements-pytest.lock')
    if lock['python'] != f'{sys.version_info.major}.{sys.version_info.minor}':
        raise ValueError('pytest target requires Python ' + lock['python'])
    key = value_digest(dict(lock=lock, executable=str(Path(sys.executable).resolve()), version=sys.version))
    return lock, root / '.tmp/pytest' / key


def target(root):
    lock, path = identity(root)
    manifest = read(path / 'installed.json')
    if manifest['lock'] != lock or manifest['executable'] != str(Path(sys.executable).resolve()):
        raise ValueError('pytest package identity mismatch')
    files = {str(p.relative_to(path)): digest(p) for p in path.rglob('*') if p.is_file() and p.name != 'installed.json'}
    if files != manifest['files']:
        raise ValueError('pytest package files changed; provision a fresh target')
    return path, manifest


def provision(root, wheel_dir=None):
    import checkout_lock
    lock, destination = identity(root)
    with checkout_lock.owned(root):
        if destination.exists():
            target(root)
            return destination
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix='install-', dir=destination.parent))
        try:
            for package in lock['packages']:
                wheel = staging / package['filename']
                if wheel_dir:
                    shutil.copyfile(wheel_dir / package['filename'], wheel)
                else:
                    with urllib.request.urlopen(package['url'], timeout=30) as response:
                        wheel.write_bytes(response.read())
                if digest(wheel) != package['sha256']:
                    raise ValueError('wheel digest mismatch: ' + package['filename'])
                with zipfile.ZipFile(wheel) as archive:
                    for name in archive.namelist():
                        if name.startswith('/') or '..' in Path(name).parts or '.data' in name.split('/'):
                            raise ValueError('unsupported wheel member: ' + name)
                    archive.extractall(staging)
                wheel.unlink()
            manifest = dict(lock=lock, executable=str(Path(sys.executable).resolve()), version=sys.version,
                            files={str(p.relative_to(staging)): digest(p) for p in staging.rglob('*') if p.is_file()})
            write(staging / 'installed.json', manifest)
            staging.rename(destination)
        except BaseException:
            shutil.rmtree(staging)
            raise
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheels', type=Path)
    args = parser.parse_args()
    print(provision(Path(__file__).resolve().parents[2], args.wheels))
