"""Deterministic source discovery shared by build and worker identities."""
from pathlib import Path


def source_paths(root, directories, files, suffixes=None):
    root = Path(root)
    paths = set(files)
    for name in (*directories, *files):
        path = root / name
        for component in (path, *path.parents):
            if component == root:
                break
            if component.is_symlink():
                raise ValueError(f'symlink under identity sources: {name}')
        if not path.exists():
            raise ValueError(f'missing identity source: {name}')
    for directory in directories:
        found = set()
        for path in (root / directory).rglob('*'):
            if path.is_symlink():
                raise ValueError(f'symlink under identity sources: {path.relative_to(root)}')
            if path.is_file() and (suffixes is None or path.suffix in suffixes):
                found.add(path.relative_to(root).as_posix())
            elif not path.is_file() and not path.is_dir():
                raise ValueError(f'nonregular identity source: {path.relative_to(root)}')
        if not found:
            raise ValueError(f'missing protocol sources: {directory}')
        paths.update(found)
    for name in paths:
        if not (root / name).is_file():
            raise ValueError(f'nonregular identity source: {name}')
    return sorted(paths)
