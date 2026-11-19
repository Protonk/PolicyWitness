"""Deterministic source discovery shared by build and worker identities."""
import os
from pathlib import Path
import stat


def source_paths(root, directories, files, suffixes=None):
    root = Path(root)
    paths = set(files)

    def inspect(name, *, declared=None):
        try:
            mode = (root / name).lstat().st_mode
        except OSError as error:
            if declared is not None and isinstance(error, FileNotFoundError):
                raise ValueError(f'missing identity source: {declared}') from error
            raise ValueError(f'uninspectable identity source: {name}: {error.strerror}') from error
        if stat.S_ISLNK(mode):
            raise ValueError(f'symlink under identity sources: {declared or name}')
        return mode

    # An explicitly named file may be outside every discovered tree. Check
    # its ancestors too, before looking through them.
    for name in (*directories, *files):
        relative = Path(name)
        for parent in reversed(relative.parents):
            if parent != Path('.'):
                inspect(parent, declared=name)
        mode = inspect(relative, declared=name)
        if name in files and not stat.S_ISREG(mode):
            raise ValueError(f'nonregular identity source: {name}')
        if name in directories and not stat.S_ISDIR(mode):
            raise ValueError(f'identity source root is not a directory: {name}')

    for directory in directories:
        pending = [Path(directory)]
        found = set()
        while pending:
            current = pending.pop()
            try:
                names = os.listdir(root / current)
            except OSError as error:
                raise ValueError(f'unreadable identity source directory: {current}: {error.strerror}') from error
            for name in names:
                path = current / name
                mode = inspect(path)
                if stat.S_ISDIR(mode):
                    pending.append(path)
                elif not stat.S_ISREG(mode):
                    raise ValueError(f'nonregular identity source: {path}')
                elif suffixes is None or path.suffix in suffixes:
                    found.add(path.as_posix())
        if not found:
            raise ValueError(f'no selected identity source under: {directory}')
        paths.update(found)
    return sorted(paths)
