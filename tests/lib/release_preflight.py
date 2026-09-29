"""Check that HEAD is a releasable source state and report the stamp build.sh will use.

A release build comes from a clean tree at an annotated v<major>.<minor>.<patch>
tag that the remote either lacks or holds identically, for a version that has no
archive yet. `build.sh` derives the version it stamps from the nearest `v*` tag,
so building before tagging notarizes a build stamped with the previous version.
--report prints the same findings as warnings and exits 0, so a rehearsal
notarization still records what it is stamping.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
RELEASE_TAG = re.compile(r'v\d+\.\d+\.\d+')


def git(root, *args, check=True):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True)
    if result.returncode != 0:
        if check:
            raise ValueError(f"git {' '.join(args)} failed: {result.stderr.strip() or result.returncode}")
        return None
    return result.stdout.strip()


def inspect(root, *, remote='origin', dist='dist'):
    """Return (stamp, problems). The stamp mirrors build.sh; problems are release refusals."""
    root = Path(root)
    describe = git(root, 'describe', '--tags', '--match', 'v[0-9]*', '--always', '--dirty')
    match = re.match(r'v(\d+\.\d+\.\d+)', describe)
    stamp = dict(head=git(root, 'rev-parse', 'HEAD'), describe=describe,
                 version=match.group(1) if match else '0.0.0',
                 build_number=git(root, 'rev-list', '--count', 'HEAD'), tag=None, remote_tag=None)
    problems = []
    if git(root, 'status', '--porcelain', '--untracked-files=no'):
        problems.append('working tree has uncommitted changes to tracked files')
    tag = git(root, 'describe', '--tags', '--exact-match', '--match', 'v[0-9]*', 'HEAD', check=False)
    if tag is None:
        problems.append(f'HEAD is not at a release tag; build.sh would stamp {describe}')
        return stamp, problems
    stamp['tag'] = tag
    if not RELEASE_TAG.fullmatch(tag):
        problems.append(f'{tag} is not a v<major>.<minor>.<patch> tag')
    if git(root, 'cat-file', '-t', tag) != 'tag':
        problems.append(f'{tag} is a lightweight tag; release tags are annotated')
    listing = git(root, 'ls-remote', '--tags', remote, f'refs/tags/{tag}', check=False)
    if listing is None:
        problems.append(f'cannot query {remote} for {tag}')
    else:
        # An annotated tag lists its object and a peeled ^{} line; compare the tag object.
        remote_ids = [line.split()[0] for line in listing.splitlines()
                      if len(line.split()) == 2 and line.split()[1] == f'refs/tags/{tag}']
        stamp['remote_tag'] = remote_ids[0] if remote_ids else None
        if remote_ids and remote_ids[0] != git(root, 'rev-parse', tag):
            problems.append(f'{remote} already holds a different {tag}')
    archive = root / dist / 'archive' / tag
    if archive.exists():
        problems.append(f'{archive} already exists; a version is released once')
    return stamp, problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--report', action='store_true', help='print findings as warnings and exit 0')
    parser.add_argument('--format', choices=('json', 'version'), default='json')
    parser.add_argument('--remote', default='origin')
    parser.add_argument('--dist', default='dist', help='distribution directory relative to the repository')
    args = parser.parse_args(argv)
    try:
        stamp, problems = inspect(ROOT, remote=args.remote, dist=args.dist)
    except (OSError, ValueError) as exc:
        parser.exit(1, f'STOP: {exc}\n')
    label = 'WARNING' if args.report else 'STOP'
    for problem in problems:
        print(f'{label}: {problem}', file=sys.stderr)
    if problems and not args.report:
        return 1
    if args.format == 'version':
        print(stamp['version'])
    else:
        print(json.dumps(dict(stamp, problems=problems), indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
