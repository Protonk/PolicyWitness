"""Strict publication freshness from the actual bytes of an annotated tag.

Portable archive verification keeps its producing contract. New acceptance,
archival and publication require the corresponding source checkout, so no
current-source check is attributed to another tagged revision.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def git(root, *args):
    try:
        result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, timeout=60)
    except subprocess.TimeoutExpired as error:
        raise ValueError('publication source inspection timed out') from error
    if result.returncode:
        raise ValueError('publication source: ' + result.stderr.decode('utf-8', 'replace').strip())
    return result.stdout


def tagged_source(root, tag, commit=None):
    root = Path(root).resolve()
    if not isinstance(tag, str) or not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('publication requires an annotated release tag')
    if git(root, 'cat-file', '-t', 'refs/tags/' + tag).strip() != b'tag':
        raise ValueError('publication requires an annotated release tag')
    source = git(root, 'rev-parse', tag + '^{commit}').decode().strip()
    if commit is not None and source != commit:
        raise ValueError('publication source commit differs from the tagged app or archive')
    if git(root, 'rev-parse', 'HEAD').decode().strip() != source:
        raise ValueError('publication freshness requires the source checkout at ' + tag)
    if git(root, 'status', '--porcelain', '--untracked-files=all').strip():
        raise ValueError('publication source has uncommitted changes or untracked files')
    for row in git(root, 'ls-tree', '-rz', tag).split(b'\0'):
        if not row:
            continue
        meta, name = row.split(b'\t', 1)
        mode, kind, oid = meta.split()
        path = root / name.decode('utf-8')
        if kind != b'blob' or any((root / parent).is_symlink() for parent in path.relative_to(root).parents):
            raise ValueError('unsupported tagged publication source: ' + str(path))
        if mode == b'120000' and path.is_symlink():
            raw = os.fsencode(os.readlink(path))
        elif mode in (b'100644', b'100755') and not path.is_symlink() and path.is_file():
            raw = path.read_bytes()
        else:
            raise ValueError('unsupported tagged publication source: ' + str(path))
        actual = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest().encode()
        if actual != oid:
            raise ValueError('publication source differs from tagged bytes: ' + name.decode())
    return source


def require(root, tag, commit=None):
    """Return source-bound verification receipts; identities alone cannot pass."""
    root = Path(root).resolve()
    source = tagged_source(root, tag, commit)
    commands = []
    checks = [
        ('docs/generate_limits.py', ['--check', '--publication']),
        ('docs/generate_contract_stamps.py', ['--check', '--require-history', '--publication']),
    ]
    # This source-owned state is checked even when the frozen guide happens to
    # equal every current projection. Removing an artifact receipt or changing
    # the app label cannot make an active development boundary publishable.
    if (root / 'docs/publication.py').is_file():
        checks.insert(0, ('docs/publication.py', ['--require-publication']))
    for script, arguments in checks:
        # Older tagged generators retain their own strict entrypoint. The
        # development/publication distinction must not rewrite old archives.
        if '--publication' not in (root / script).read_text():
            arguments = [value for value in arguments if value != '--publication']
        argv = [sys.executable, '-B', '-S', str(root / script), *arguments]
        try:
            result = subprocess.run(argv, cwd=root, capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired as error:
            raise ValueError('publication freshness timed out: ' + script) from error
        commands.append(dict(argv=argv, returncode=result.returncode, stdout=result.stdout, stderr=result.stderr))
        if result.returncode:
            raise ValueError('publication freshness: ' + script + ': ' + (result.stderr.strip() or result.stdout.strip()))
    # Read the generated table only after its owning generator has established
    # equality with the tagged definitions and complete release history.
    text = (root / 'docs/CONTRACT.md').read_text()
    table = text.split('<!-- BEGIN GENERATED CONTRACT STAMPS -->', 1)[1].split('<!-- END GENERATED CONTRACT STAMPS -->', 1)[0]
    if re.search(r'\|\s*unreleased\s*\|', table):
        raise ValueError('publication freshness: contract surfaces remain unreleased')
    return dict(schema_version=1, status='current', tag=tag, source_commit=source,
                signed_guide_required=(root / 'docs/publication.py').is_file(),
                guide_sha256=hashlib.sha256((root / 'docs/PolicyWitness.md').read_bytes()).hexdigest(), commands=commands)
