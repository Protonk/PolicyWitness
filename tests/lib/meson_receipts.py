#!/usr/bin/env python3
"""Record how a Meson build directory was configured and what it would run.

A receipt binds a comparison to exact inputs: tool versions and the resolved
Apple toolchain, the manifest and options with their hashes, the effective
build options and active targets of the configured directory, the targets the
manifest declares when read without a build directory, every compile and link
command Ninja runs for each native output (captured even when nothing is out
of date) and the outputs' hashes. Meson's own assertions enforce the fixed
native policy; a receipt records, it does not enforce.

    meson_receipts.py BUILDDIR OUT [--manifest meson.build]
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_FILES = ('meson.build', 'meson.options')


def sha256(path):
    hasher = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


class Recorder:
    def __init__(self, out):
        self.out = out
        self.journal = out / 'commands.jsonl'

    def run(self, argv, *, timeout=300, env=None, cwd=None):
        argv = [str(a) for a in argv]
        started = time.monotonic()
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=env, cwd=cwd)
        record = dict(argv=argv, returncode=result.returncode, elapsed_seconds=round(time.monotonic() - started, 3),
                      cwd=str(cwd) if cwd else None)
        with self.journal.open('a') as stream:
            stream.write(json.dumps(record) + '\n')
        return result

    def text(self, argv, **kwargs):
        result = self.run(argv, **kwargs)
        return result.stdout.strip() if result.returncode == 0 else f'<failed rc={result.returncode}: {result.stderr.strip()}>'


def tools(rec):
    env = os.environ
    return dict(
        meson=rec.text(['meson', '--version']), meson_path=shutil.which('meson'),
        ninja=rec.text(['ninja', '--version']), ninja_path=shutil.which('ninja'),
        xcode_select=rec.text(['xcode-select', '-p']),
        DEVELOPER_DIR=env.get('DEVELOPER_DIR'), SDKROOT=env.get('SDKROOT'),
        sdk_path=rec.text(['xcrun', '--sdk', 'macosx', '--show-sdk-path']),
        sdk_version=rec.text(['xcrun', '--sdk', 'macosx', '--show-sdk-version']),
        clang=rec.text(['xcrun', '--sdk', 'macosx', '-f', 'clang']),
        clang_version=rec.text(['xcrun', '--sdk', 'macosx', 'clang', '--version']).splitlines()[0],
        cc=rec.text(['xcrun', '--sdk', 'macosx', '-f', 'cc']),
        swiftc=rec.text(['xcrun', '--sdk', 'macosx', '-f', 'swiftc']),
        swiftc_version=rec.text(['xcrun', '--sdk', 'macosx', 'swiftc', '--version']).splitlines()[0],
        path=env.get('PATH'),
    )


def capture(builddir, out, manifest):
    out.mkdir(parents=True)
    rec = Recorder(out)
    receipt = dict(schema_version=1, captured_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                   root=str(ROOT), builddir=str(builddir), manifest=str(manifest), tools=tools(rec))

    copies = out / 'manifest'
    copies.mkdir()
    receipt['manifest_files'] = {}
    for name in MANIFEST_FILES:
        source = manifest.parent / name
        if source.is_file():
            shutil.copy2(source, copies / name)
            receipt['manifest_files'][name] = sha256(source)

    for name, argv in (('buildoptions', ['meson', 'introspect', builddir, '--buildoptions']),
                       ('targets', ['meson', 'introspect', builddir, '--targets']),
                       ('buildsystem_files', ['meson', 'introspect', builddir, '--buildsystem-files']),
                       ('targets-file-mode', ['meson', 'introspect', manifest, '--targets'])):
        result = rec.run(argv)
        if result.returncode != 0:
            raise SystemExit(f'{" ".join(map(str, argv))} failed: {result.stderr}')
        (out / f'{name}.json').write_text(result.stdout)
    for name in ('intro-compilers.json', 'intro-projectinfo.json', 'meson-info.json'):
        source = builddir / 'meson-info' / name
        if source.is_file():
            shutil.copy2(source, out / name)
    for name in ('meson-logs/meson-log.txt', 'compile_commands.json', 'build.ninja'):
        source = builddir / name
        if source.is_file():
            shutil.copy2(source, out / Path(name).name)

    options = {o['name']: o['value'] for o in json.loads((out / 'buildoptions.json').read_text())}
    receipt['options'] = {k: options[k] for k in sorted(options)
                          if k in ('inspection', 'xpc', 'buildtype', 'optimization', 'debug', 'warning_level',
                                   'b_ndebug', 'b_asneeded', 'b_colorout', 'b_lto', 'b_sanitize', 'b_pie',
                                   'b_staticpic', 'b_lundef', 'c_args', 'c_link_args', 'c_std',
                                   'swift_args', 'swift_link_args', 'strip', 'werror')}

    commands = out / 'commands'
    commands.mkdir()
    receipt['targets'] = []
    receipt['outputs'] = {}
    for target in json.loads((out / 'targets.json').read_text()):
        entry = dict(name=target['name'], id=target['id'], type=target['type'], filename=target['filename'],
                     sources=[s for group in target['target_sources'] for s in group.get('sources', [])],
                     parameters=[group.get('parameters', []) for group in target['target_sources']])
        receipt['targets'].append(entry)
        for filename in target['filename']:
            relative = os.path.relpath(filename, builddir)
            result = rec.run(['ninja', '-C', builddir, '-t', 'commands', relative])
            (commands / (Path(filename).name + '.txt')).write_text(result.stdout if result.returncode == 0 else result.stderr)
            if Path(filename).is_file():
                receipt['outputs'][relative] = dict(sha256=sha256(filename), size=Path(filename).stat().st_size)
    dry = rec.run(['ninja', '-C', builddir, '-n'])
    (out / 'dry-run.txt').write_text(dry.stdout + dry.stderr)
    receipt['no_work_pending'] = 'no work to do' in dry.stdout
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('builddir', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'meson.build')
    args = parser.parse_args()
    receipt = capture(args.builddir.resolve(), args.out.resolve(), args.manifest.resolve())
    print(json.dumps(dict(targets=[t['name'] for t in receipt['targets']], outputs=receipt['outputs'],
                          no_work_pending=receipt['no_work_pending'], receipt=str(args.out / 'receipt.json')), indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
