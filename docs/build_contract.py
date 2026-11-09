#!/usr/bin/env python3
"""Compute a public build contract; never accept a caller-supplied identity."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from source_identity import source_paths

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ('controller/src', 'controller/tools', 'runner/Sources', 'runner/Clients',
               'runner/Services', 'runner/augments')
FILES = ('build.sh', 'meson.build', 'meson.options', 'runner/Package.swift',
         'controller/Cargo.toml', 'controller/Cargo.lock', 'controller/build.rs',
         'Info.plist', 'PolicyWitness.entitlements', 'docs/build_contract.py',
         'docs/source_identity.py', 'tests/build_equipment.py', 'tests/build-evidence.py')
# This declaration is independent of Git and applies equally to source copies.
# New source files in these languages and bundled resources are discovered;
# executables, editor/OS files and documentation are not compiler inputs.
SUFFIXES = ('.rs', '.c', '.h', '.swift', '.sb', '.plist', '.ent')
FILES += ('tests/lib/build_provenance.py', 'tests/lib/signer_check.py',
          'tests/lib/cargo_config.py', 'tests/lib/checkout_lock.py', 'tests/lib/output_target.py')
RELEASE = re.compile(r'v[0-9]+\.[0-9]+\.[0-9]+')


def git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def inputs(root):
    return source_paths(root, DIRECTORIES, FILES, SUFFIXES)


def release_bytes_match(root, tag, paths):
    """Compare actual bytes with tagged blobs, without consulting index flags."""
    tree = subprocess.run(['git', '-C', str(root), 'ls-tree', '-rz', tag],
                          capture_output=True, check=True).stdout
    blobs = {}
    for entry in tree.split(b'\0'):
        if not entry:
            continue
        metadata, raw_name = entry.split(b'\t', 1)
        name = raw_name.decode('utf-8')
        if name in FILES or (Path(name).suffix in SUFFIXES and
                            any(name.startswith(directory + '/') for directory in DIRECTORIES)):
            mode, kind, oid = metadata.split()
            if kind != b'blob' or mode not in (b'100644', b'100755'):
                return False
            blobs[name] = oid
    if set(paths) != set(blobs):
        return False
    # Read the stored bytes, not a checkout transformed by filters or index hints.
    result = subprocess.run(['git', '-C', str(root), 'cat-file', '--batch'],
                            input=b'\n'.join(blobs[name] for name in paths) + b'\n',
                            capture_output=True, check=True).stdout
    cursor = 0
    for name in paths:
        end = result.index(b'\n', cursor)
        _, kind, length = result[cursor:end].split()
        size = int(length)
        cursor = end + 1
        if kind != b'blob' or result[cursor:cursor + size] != (root / name).read_bytes():
            return False
        cursor += size + 1
    return True


def identity(root):
    digest = hashlib.sha256(b'PolicyWitness public build contract\0')
    paths = inputs(root)
    for name in paths:
        for part in (name.encode(), (root / name).read_bytes()):
            digest.update(len(part).to_bytes(8, 'big'))
            digest.update(part)
    # A directory nested in another repository is not this source checkout.
    top = git(root, 'rev-parse', '--show-toplevel')
    if top and Path(top).resolve() == root.resolve() and git(root, 'status', '--porcelain', '--untracked-files=all') == '':
        tags = git(root, 'tag', '--points-at', 'HEAD') or ''
        releases = [tag for tag in tags.splitlines()
                    if RELEASE.fullmatch(tag) and git(root, 'cat-file', '-t', 'refs/tags/' + tag) == 'tag']
        if len(releases) == 1 and release_bytes_match(root, releases[0], paths):
            return 'release:' + releases[0]
        if len(releases) > 1:
            raise ValueError('ambiguous release: multiple annotated release tags at HEAD')
    return 'development:' + digest.hexdigest()


def swift(context):
    return '\n'.join(['// Build-generated context; not a source-tree identity input.',
        'enum PWBuildContext {',
        *[f'    static let {key} = {json.dumps(value)}' for key, value in context.items()], '}', ''])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--swift', type=Path)
    parser.add_argument('--swift-stdout', action='store_true')
    parser.add_argument('--describe', default='unknown')
    parser.add_argument('--commit', default='unknown')
    args = parser.parse_args()
    try:
        value = identity(args.root)
        if args.swift_stdout:
            expected = os.environ.get('PW_BUILD_CONTRACT')
            if expected is not None and value != expected:
                raise ValueError('Swift build context differs from PW_BUILD_CONTRACT')
            print(swift(dict(contract=value, describe=git(args.root, 'describe', '--tags', '--match', 'v[0-9]*', '--always', '--dirty') or 'unknown',
                             commit=git(args.root, 'rev-parse', 'HEAD') or 'unknown')), end='')
            return
        if args.swift:
            body = swift(dict(contract=value, describe=args.describe, commit=args.commit))
            if not args.swift.exists() or args.swift.read_text() != body:
                args.swift.write_text(body)
        print(value)
    except (OSError, ValueError) as error:
        parser.exit(1, f'build contract: {error}\n')


if __name__ == '__main__':
    main()
