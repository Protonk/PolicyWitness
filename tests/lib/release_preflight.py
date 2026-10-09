"""Check that HEAD is a releasable source state and report the stamp build.sh will use.

A release build comes from a clean tree at an annotated v<major>.<minor>.<patch>
tag that the remote either lacks or holds identically, for a version that has no
archive yet. `build.sh` derives the version it stamps from the nearest `v*` tag,
so building before tagging notarizes a build stamped with the previous version.
--report prints the same findings as warnings and exits 0, so a rehearsal
notarization still records what it is stamping.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
RELEASE_TAG = re.compile(r'v\d+\.\d+\.\d+')
BASELINE_NAME = 'tests/fixtures/docs/prose_baseline.json'
BUILD_BASELINE_NAME = 'tests/fixtures/docs/build_baseline.json'


def git(root, *args, check=True):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True)
    if result.returncode != 0:
        if check:
            raise ValueError(f"git {' '.join(args)} failed: {result.stderr.strip() or result.returncode}")
        return None
    return result.stdout.strip()


def baseline_entries(text):
    """A multiset preserves repeated exact prose sites; changed text is a new site."""
    data = json.loads(text)
    if not isinstance(data, dict) or set(data) != {'schema_version', 'entries'} or data['schema_version'] != 1:
        raise ValueError('expected prose baseline schema_version 1')
    if not isinstance(data['entries'], list):
        raise ValueError('prose baseline entries must be a list')
    keys = ('document', 'invariant', 'kind', 'text')
    for row in data['entries']:
        if not isinstance(row, dict) or set(row) != set(keys) or any(not isinstance(row[k], str) or not row[k] for k in keys):
            raise ValueError('malformed prose baseline entry')
        path = Path(row['document'])
        if path.is_absolute() or '..' in path.parts or path.suffix != '.md':
            raise ValueError('baseline document must be repository-relative Markdown')
        if (row['invariant'], row['kind']) not in {('G9', 'literal'), ('G9', 'count'), ('G11', 'citation_pair')}:
            raise ValueError('unknown baseline invariant or kind')
    return Counter(tuple(row[k] for k in keys) for row in data['entries'])


def build_baseline_entries(text):
    """One entry per uncovered refusal; a rewritten claim or control is a new entry."""
    data = json.loads(text)
    if not isinstance(data, dict) or set(data) != {'schema_version', 'entries'} or data['schema_version'] != 1:
        raise ValueError('expected build baseline schema_version 1')
    if not isinstance(data['entries'], list):
        raise ValueError('build baseline entries must be a list')
    keys = ('refusal', 'variants', 'claim', 'control')
    for row in data['entries']:
        if not isinstance(row, dict) or set(row) != set(keys) or not isinstance(row['variants'], list):
            raise ValueError('malformed build baseline entry')
        if any(not isinstance(row[k], str) or not row[k] for k in ('refusal', 'claim', 'control')):
            raise ValueError('malformed build baseline entry')
    return Counter((row['refusal'], tuple(row['variants']), row['claim'], row['control']) for row in data['entries'])


def previous_release(root, tag):
    """The previous annotated release reachable before this commit, if any."""
    parent = git(root, 'rev-parse', '--verify', 'HEAD^', check=False)
    previous, excluded = None, []
    while parent:
        candidate = git(root, 'describe', '--abbrev=0', '--match', 'v[0-9]*',
                        *excluded, parent, check=False)
        if candidate is None:
            break
        if RELEASE_TAG.fullmatch(candidate) and candidate != tag:
            previous = candidate
            break
        excluded += ['--exclude', candidate]
    return previous


def inspect_build_baseline(root, tag):
    """The build baseline against the previous release: it may shrink, never grow or rewrite an entry."""
    previous = previous_release(root, tag)
    current = git(root, 'show', f'HEAD:{BUILD_BASELINE_NAME}', check=False)
    prior = git(root, 'show', f'{previous}:{BUILD_BASELINE_NAME}', check=False) if previous else None
    report = dict(previous_tag=previous, status='no previous release' if previous is None else 'previous release predates baseline')
    now = build_baseline_entries(current) if current is not None else None
    if prior is None:
        return report, []
    before = build_baseline_entries(prior)
    if now is None:
        return dict(report, status='missing baseline'), ['release removed the build baseline']
    added = now - before
    report.update(status='grown' if added else 'non-growing', additions=sum(added.values()))
    return report, ([f'build baseline grew against {previous}: {sum(added.values())} added or rewritten entries'] if added else [])


def inspect_baseline(root, tag):
    """Compare against the previous annotated release reachable before this commit."""
    parent = git(root, 'rev-parse', '--verify', 'HEAD^', check=False)
    previous, excluded = None, []
    while parent:
        candidate = git(root, 'describe', '--abbrev=0', '--match', 'v[0-9]*',
                        *excluded, parent, check=False)
        if candidate is None:
            break
        if RELEASE_TAG.fullmatch(candidate) and candidate != tag:
            previous = candidate
            break
        excluded += ['--exclude', candidate]
    current = git(root, 'show', f'HEAD:{BASELINE_NAME}', check=False)
    prior = git(root, 'show', f'{previous}:{BASELINE_NAME}', check=False) if previous else None
    report = dict(previous_tag=previous, status='no previous release' if previous is None else 'previous release predates baseline')
    # Validate even an inaugural baseline: malformed entries cannot establish a release ceiling.
    now = baseline_entries(current) if current is not None else None
    if prior is None:
        return report, []
    before = baseline_entries(prior)
    if now is None:
        return dict(report, status='missing baseline'), ['release removed the prose baseline']
    added = now - before
    report.update(status='grown' if added else 'non-growing', additions=sum(added.values()))
    return report, ([f'prose baseline grew against {previous}: {sum(added.values())} added or rewritten site(s)'] if added else [])


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
    stamp['prose_baseline'], baseline_problems = inspect_baseline(root, tag)
    problems.extend(baseline_problems)
    stamp['build_baseline'], build_problems = inspect_build_baseline(root, tag)
    problems.extend(build_problems)
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
    baseline = stamp.get('prose_baseline', {})
    if baseline.get('status') in {'no previous release', 'previous release predates baseline'}:
        print(f"NOTE: prose baseline: {baseline['status']} ({baseline.get('previous_tag')})", file=sys.stderr)
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
