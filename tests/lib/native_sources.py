#!/usr/bin/env python3
"""The native targets' source lists, read from Meson, checked against the tree.

Two readings of the same expectation. `declared_targets` reads the manifest in
file mode (`meson introspect meson.build --targets`), which needs no build
directory and lists every declaration, including those in branches Meson
would not evaluate; the `source_drift` suite and the order-barrier control use
it. `active_targets` reads a configured build directory, whose targets are the
ones Meson actually evaluated; `build.sh` checks it after compiling, before
any output is copied. A target name declared more than once is refused in
both readings rather than resolved, because a dead declaration can otherwise
stand in for the live one.

The expectation pins every target: the host carries every Swift file under
the core directory plus the service entry point, the shim every C file under
its directory, and the client, worker and validator their single known
files. This is a membership check. What the compiler does to those files is
the manifest's business, reviewed through its identity and the receipts.

The build-directory reading also checks the compile's closure for the
identity's C side: every repository file the compiler consumed for the worker
and the shim, as Ninja's dependency log records it, must be an identity
digest input. An include that reaches outside the digest's directories, by a
relative path or through a symlink, is named; the validator is outside the
identity by design and is not checked. Dependencies must have been recorded by
a completed compile.

    native_sources.py [--manifest meson.build] [--builddir DIR]

Exit 1 with one line per problem; exit 2 when Meson or Ninja cannot be read.
"""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IDENTITY_TARGETS = ('pw-probe-runner', 'PWCWorkerShim')
CORE_DIR = 'runner/Sources/PWRunnerCore'
SHIM_DIR = 'runner/Sources/PWCWorkerShim'
API = 'runner/Sources/PWRunnerCore/PWRunnerAPI.swift'
SERVICE_MAIN = 'runner/Services/PWRunner/main.swift'
CLIENT_MAIN = 'runner/Clients/PWRunnerClient/main.swift'
WORKER = 'controller/tools/pw_probe_runner/pw_probe_runner.c'
VALIDATOR = 'controller/tools/sb_api_validator/sb_api_validator.c'


class IntrospectionError(Exception):
    """Meson could not be run or its output could not be read."""


def introspect(argv, cwd):
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=60, cwd=cwd)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IntrospectionError(f"meson introspection failed: {' '.join(map(str, argv))}: {exc}") from exc
    if result.returncode != 0:
        raise IntrospectionError(f"meson introspection failed (rc={result.returncode}): {' '.join(map(str, argv))}\n"
                                 f"{result.stderr.strip()}")
    return result.stdout


def parse_targets(text, root, label):
    """Ordered sources per target, root-relative, plus the problems the listing itself shows."""
    try:
        listing = json.loads(text)
    except ValueError as exc:
        raise IntrospectionError(f"meson introspection returned malformed JSON: {exc}") from exc
    root = Path(root).resolve()
    counts = {}
    for target in listing:
        counts[target['name']] = counts.get(target['name'], 0) + 1
    problems = [f"  {label}: declares '{name}' {count} times; a target name must be declared once"
                for name, count in sorted(counts.items()) if count > 1]
    targets = {}
    for target in listing:
        name = target['name']
        if counts[name] > 1:
            continue
        sources = []
        for group in target['target_sources']:
            for source in group.get('sources', []):
                try:
                    sources.append(Path(source).resolve().relative_to(root).as_posix())
                except ValueError:
                    problems.append(f"  {label}: {name} source '{source}' is outside the repository")
        targets[name] = sources
    return targets, problems


def declared_targets(manifest=ROOT / 'meson.build', label='meson.build'):
    manifest = Path(manifest).resolve()
    return parse_targets(introspect(['meson', 'introspect', str(manifest), '--targets'], manifest.parent),
                         manifest.parent, label)


def active_targets(builddir, label='builddir'):
    builddir = Path(builddir).resolve()
    info = json.loads((builddir / 'meson-info/meson-info.json').read_text())
    root = Path(info['directories']['source'])
    options = {o['name']: o['value'] for o in json.loads(introspect(['meson', 'introspect', str(builddir), '--buildoptions'], root))}
    listing = introspect(['meson', 'introspect', str(builddir), '--targets'], root)
    targets, problems = parse_targets(listing, root, label)
    filenames = {t['name']: t['filename'] for t in json.loads(listing)}
    return targets, problems, root, bool(options.get('xpc', True)), filenames


def identity_inputs(root):
    """The digest's input paths, read from the generator so the two cannot drift."""
    spec = importlib.util.spec_from_file_location('generate_worker_identity', Path(root) / 'docs/generate_worker_identity.py')
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    return set(generator.source_paths(Path(root)))


def recorded_dependencies(builddir, root):
    """Ninja's dependency log: per object, whether it is current and what the compiler consumed."""
    blocks, current = {}, None
    for line in introspect(['ninja', '-C', str(builddir), '-t', 'deps'], root).splitlines():
        if line and not line[0].isspace():
            name, _, rest = line.partition(': #deps')
            current = blocks[name] = dict(valid='(VALID)' in rest, deps=[])
        elif current is not None and line.strip():
            current['deps'].append(line.strip())
    return blocks


def closure_problems(builddir, root, targets, filenames, label):
    """Every repository file the compiler consumed for an identity target is a digest input."""
    builddir, root = Path(builddir).resolve(), Path(root).resolve()
    try:
        digest = identity_inputs(root)
    except ValueError as exc:
        return [f'  {label}: {exc}']
    blocks = recorded_dependencies(builddir, root)
    out = []
    for name in IDENTITY_TARGETS:
        if name not in targets:
            continue
        objdir = Path(filenames[name][0]).name + '.p/'
        objects = {obj: block for obj, block in blocks.items() if obj.startswith(objdir)}
        if not objects:
            out.append(f"  {label}: no recorded dependencies for {name}; compile before checking the closure")
        for obj, block in sorted(objects.items()):
            if not block['valid']:
                out.append(f"  {label}: recorded dependencies of {obj} are stale; compile before checking the closure")
                continue
            for dep in block['deps']:
                path = (builddir / dep).resolve()
                try:
                    relative = path.relative_to(root).as_posix()
                except ValueError:
                    continue  # the SDK and the toolchain
                if relative not in digest:
                    out.append(f"  {label}: {name} consumed '{relative}' which is not an identity input")
    return out


def expected(root, xpc=True):
    """Every target and exactly the files the tree holds for it."""
    root = Path(root).resolve()
    targets = {'sb_api_validator': {VALIDATOR}, 'pw-probe-runner': {WORKER}}
    if xpc:
        targets['PWCWorkerShim'] = {p.relative_to(root).as_posix() for p in (root / SHIM_DIR).rglob('*.c')}
        targets['pw-runner-client'] = {API, CLIENT_MAIN}
        targets['PWRunner'] = {p.relative_to(root).as_posix() for p in (root / CORE_DIR).rglob('*.swift')} | {SERVICE_MAIN}
    return targets


def problems(targets, expectation, label):
    """Every expected target present with exactly its expected sources, and nothing else."""
    out = [f"  {label}: unexpected target '{name}'" for name in sorted(set(targets) - set(expectation))]
    for name, want in expectation.items():
        if name not in targets:
            out.append(f"  {label}: no '{name}' target")
            continue
        have = set(targets[name])
        out += [f"  {label}: {name} lacks '{path}' which is in the tree" for path in sorted(want - have)]
        out += [f"  {label}: {name} has '{path}' which the tree does not expect" for path in sorted(have - want)]
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--manifest', type=Path, help='check the manifest in file mode (default when no --builddir)')
    parser.add_argument('--builddir', type=Path, help='check the targets a configured directory actually evaluated')
    args = parser.parse_args()
    try:
        if args.builddir:
            targets, found, root, xpc, filenames = active_targets(args.builddir)
            found += problems(targets, expected(root, xpc), 'builddir')
            found += closure_problems(args.builddir, root, targets, filenames, 'builddir')
            where = f"{args.builddir} (xpc={'true' if xpc else 'false'})"
        else:
            manifest = args.manifest or ROOT / 'meson.build'
            targets, found = declared_targets(manifest)
            found += problems(targets, expected(Path(manifest).resolve().parent), 'meson.build')
            where = str(manifest)
    except (IntrospectionError, OSError, ValueError, KeyError) as exc:
        print(f'native sources: {exc}', file=sys.stderr)
        return 2
    if found:
        print(f'native source lists differ from the tree ({where}):', file=sys.stderr)
        for line in found:
            print(line, file=sys.stderr)
        return 1
    closure = ' and the identity targets consumed only digest inputs' if args.builddir else ''
    print(f'ok: {len(targets)} native targets carry exactly the tree\'s sources{closure} ({where})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
