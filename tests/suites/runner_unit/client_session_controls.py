"""Compile the shipped client session with independent clock/connection controls."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/caller_auth'))
import native_sources
from bundle import command


def main():
    out, scratch = map(Path, sys.argv[1:])
    out.mkdir(parents=True)
    scratch.mkdir(parents=True)
    targets, problems = native_sources.declared_targets()
    problems += native_sources.problems(targets, native_sources.expected(ROOT), 'meson.build')
    assert not problems, problems
    sources = [p for p in targets['pw-runner-client'] if p != native_sources.CLIENT_MAIN]
    assert native_sources.CLIENT_SESSION in sources
    sources += ['runner/Tests/PWRunnerClientSessionTests/main.swift']
    hashes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}
    binary = scratch / 'PWRunnerClientSessionTests'
    command(out / 'compile', ['/usr/bin/xcrun', '--sdk', 'macosx', 'swiftc', '-Onone', '-g',
        '-target', 'arm64-apple-macosx26.0', '-module-cache-path', scratch / 'module-cache',
        '-o', binary, *[ROOT / p for p in sources]], timeout=180)
    (out / 'build-receipt.json').write_text(json.dumps(dict(
        sources=hashes, product_path=str(binary),
        product_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        scratch_path=str(scratch)), indent=2) + '\n')
    command(out / 'execution', [binary], timeout=60)
    print((out / 'execution/stdout').read_text())


if __name__ == '__main__':
    main()
