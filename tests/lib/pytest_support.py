"""Standard-library durability and identity primitives for the pytest boundary."""
import hashlib
import json
import os
from pathlib import Path
import tempfile


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def value_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate key: ' + key)
            result[key] = value
        return result
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('expected regular evidence file: ' + str(path))
    return json.loads(path.read_text(), object_pairs_hook=unique)


def write(path, value):
    path = Path(path)
    if path.is_symlink() or path.parent.resolve() != path.parent:
        raise ValueError('redirected evidence: ' + str(path))
    fd, name = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def append(path, value):
    data = (json.dumps(value, sort_keys=True) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        if os.write(fd, data) != len(data):
            raise OSError('short evidence write')
        os.fsync(fd)
    finally:
        os.close(fd)


def rows(path):
    # Yield each decoded record: a broken tail must not discard the valid prefix.
    if Path(path).exists():
        with Path(path).open('rb') as stream:
            for line in stream:
                yield json.loads(line)


def contained(base, path):
    base, path = Path(base).resolve(), Path(path).absolute()
    if path.resolve() != path or base not in path.parents:
        raise ValueError('path escapes or redirects owned root: ' + str(path))
    return path
