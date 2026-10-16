"""A real native toolchain switch through DEVELOPER_DIR: Xcode and the Command Line Tools on the acceptance machine.

Equipment: the selected developer directory (xcode-select) and
/Library/Developer/CommandLineTools must both exist and resolve distinct C
compiler identities. Missing or indistinct equipment is a failure, never a
skip or a wrapper fallback. The control builds under A with fresh mode,
reuses the caches under A, is refused incompatible reuse under B, recovers
under B with explicit fresh mode, and records which stamped fields actually
differed between the two toolchains. Different compiler builds or SDK
locations do not imply different SDK versions: only the observed distinctions
are credited, read from the stamp, the record and independent probes of each
developer directory. No second Rust toolchain is involved.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'tests/suites/preflight/opt_in'))
import build_provenance as prov
from build_refusals import Checkout, check, passing, preserved, save, BEFORE_CARGO

CLT = Path('/Library/Developer/CommandLineTools')


def probe(developer_dir, argv, sdkroot=None):
    env = dict(os.environ, DEVELOPER_DIR=str(developer_dir))
    if sdkroot:
        env['SDKROOT'] = str(sdkroot)
    result = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=120)
    return result.stdout.strip().splitlines()[0] if result.returncode == 0 and result.stdout.strip() else None


def links(developer_dir, sdk, work):
    """Whether the developer directory compiles and links a C and a Swift program against the SDK, through xcrun."""
    work.mkdir(parents=True, exist_ok=True)
    (work / 'hello.c').write_text('int main(void) { return 0; }\n')
    (work / 'hello.swift').write_text('print("hello")\n')
    env = dict(os.environ, DEVELOPER_DIR=str(developer_dir), SDKROOT=str(sdk))
    receipts = []
    for argv in (['/usr/bin/xcrun', '--sdk', str(sdk), 'clang', '-mmacosx-version-min=26.0', str(work / 'hello.c'), '-o', str(work / 'hello-c')],
                 ['/usr/bin/xcrun', '--sdk', str(sdk), 'swiftc', '-target', 'arm64-apple-macosx26.0', str(work / 'hello.swift'), '-o', str(work / 'hello-swift')]):
        result = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=300)
        receipts.append(dict(argv=argv, returncode=result.returncode, stderr=result.stderr[-1500:]))
    save(work / 'link-receipts.json', receipts)
    return all(r['returncode'] == 0 for r in receipts)


def usable_sdk(developer_dir, out):
    """The SDK the build will select under a developer directory: xcrun's default when its linker consumes it, else the
    newest SDK of that directory that links, named through SDKROOT. The choice and every probe are recorded."""
    default = probe(developer_dir, ['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-path'])
    tried = []
    candidates = [Path(default)] if default else []
    candidates += sorted((p for p in (developer_dir / 'SDKs').glob('MacOSX*.sdk') if not p.is_symlink() and p.is_dir()),
                         key=lambda p: p.name, reverse=True)
    for sdk in candidates:
        if sdk in tried:
            continue
        tried.append(sdk)
        if links(developer_dir, sdk, out / ('link-' + developer_dir.name.replace('/', '_')) / sdk.name):
            return sdk, (None if str(sdk) == default else str(sdk)), tried
    return None, None, tried


def facts(developer_dir, sdkroot=None):
    """Independent probes of a developer directory and its selected SDK: what the stamp fields should contain."""
    request = str(sdkroot) if sdkroot else 'macosx'
    return {
        'developer_dir': str(developer_dir),
        'sdk.path': probe(developer_dir, ['/usr/bin/xcrun', '--sdk', request, '--show-sdk-path']),
        'sdk.version': probe(developer_dir, ['/usr/bin/xcrun', '--sdk', request, '--show-sdk-version']),
        'sdk.build': probe(developer_dir, ['/usr/bin/xcrun', '--sdk', request, '--show-sdk-build-version']),
        'compilers.c.identity': probe(developer_dir, ['/usr/bin/cc', '--version'], sdkroot),
        'compilers.swift.identity': probe(developer_dir, ['/usr/bin/swiftc', '--version'], sdkroot),
    }


def equipment(out):
    selected = Path(subprocess.check_output(['/usr/bin/xcode-select', '-p'], text=True).strip())
    candidates = [p for p in (selected, CLT) if p.is_dir()]
    assert len(candidates) == 2 and candidates[0] != candidates[1], f'equipment: two developer directories are required; found {candidates}'
    sdks = {}
    for side, directory in (('A', selected), ('B', CLT)):
        sdk, named, tried = usable_sdk(directory, out)
        assert sdk is not None, f'equipment: developer directory {side} ({directory}) links no C and Swift program against any of its SDKs: {tried}'
        sdks[side] = dict(sdk=str(sdk), sdkroot=named, tried=[str(p) for p in tried])
    a, b = facts(selected, sdks['A']['sdkroot']), facts(CLT, sdks['B']['sdkroot'])
    save(out / 'equipment.json', dict(a=a, b=b, sdks=sdks,
                                      note='an SDK named under sdkroot is passed to the build as SDKROOT because the directory\'s default SDK does not link with its own tools'))
    for side, found in (('A', a), ('B', b)):
        assert all(found[key] for key in ('sdk.path', 'sdk.version', 'sdk.build', 'compilers.c.identity', 'compilers.swift.identity')), \
            f'equipment: developer directory {side} ({found["developer_dir"]}) does not resolve every compiler and SDK fact: {found}'
    assert a['compilers.c.identity'] != b['compilers.c.identity'], \
        f'equipment: the two developer directories resolve the same C compiler identity ({a["compilers.c.identity"]}); a switch is not observable'
    differing = sorted(key for key in a if a[key] != b[key])
    save(out / 'distinct-fields.json', dict(differing=differing, equal=sorted(key for key in a if a[key] == b[key])))
    return selected, CLT, a, b, differing, sdks


def test_toolchain_switch(out, identity):
    assert identity.startswith('Developer ID Application: '), 'a Developer ID Application identity is required'
    selected, clt, a, b, differing, sdks = equipment(out)
    records = []
    with tempfile.TemporaryDirectory(prefix='pw-toolchain-switch-', dir='/private/tmp') as temporary:
        co = Checkout(Path(temporary), identity, out)
        env_a, env_b = dict(DEVELOPER_DIR=str(selected)), dict(DEVELOPER_DIR=str(clt))
        for env, side in ((env_a, 'A'), (env_b, 'B')):
            if sdks[side]['sdkroot']:
                env['SDKROOT'] = sdks[side]['sdkroot']
        started = time.monotonic()
        first = co.build('switch-1-fresh-A', 'full', env=env_a, fresh='1')
        passing(co, first, 'full')
        stamp_a = json.loads(first.stamp)['fields']
        for key in ('developer_dir', 'sdk.path', 'sdk.version', 'sdk.build', 'compilers.c.identity', 'compilers.swift.identity'):
            assert stamp_a[key] == a[key], (key, stamp_a[key], a[key])
        assert first.record['toolchain']['developer_dir']['source'] == 'DEVELOPER_DIR'
        assert first.record['toolchain']['sdk']['source'] == ('SDKROOT named by the caller' if sdks['A']['sdkroot'] else 'xcrun --sdk macosx default')
        assert first.record['toolchain']['compilers']['c']['observed']['identity'] == a['compilers.c.identity']
        assert first.record['toolchain']['compilers']['swift']['observed']['identity'] == a['compilers.swift.identity']
        records.append(dict(step='fresh-A', status=first.status, stamp=stamp_a, elapsed_seconds=round(time.monotonic() - started, 1)))
        reused = co.build('switch-2-reuse-A', 'full', env=env_a)
        passing(co, reused, 'full')
        assert reused.stamp == first.stamp and all(j['fresh'] for j in reused.judgments().values())
        records.append(dict(step='reuse-A', status=reused.status))
        refused = co.build('switch-3-reuse-B', 'full', env=env_b)
        check(refused, 1, 'a changed toolchain cannot reuse this directory', present=('Checking the native build directory',),
              absent=('Checking the signing identity', *BEFORE_CARGO))
        named = next((key for key in ('developer_dir', 'sdk.path', 'sdk.version', 'sdk.build', 'compilers.c.identity', 'compilers.swift.identity')
                      if f'with {key} =' in refused.stderr), None)
        assert named in differing, f'the refusal names {named!r}, which the independent probes do not distinguish: {differing}'
        assert refused.stamp == first.stamp and not refused.calls('cargo', 'build') and not refused.calls('meson')
        preserved(refused)
        records.append(dict(step='reuse-B-refused', status=refused.status, named_field=named))
        recovered = co.build('switch-4-fresh-B', 'full', env=env_b, fresh='1')
        passing(co, recovered, 'full')
        stamp_b = json.loads(recovered.stamp)['fields']
        for key in ('developer_dir', 'sdk.path', 'sdk.version', 'sdk.build', 'compilers.c.identity', 'compilers.swift.identity'):
            assert stamp_b[key] == b[key], (key, stamp_b[key], b[key])
        assert {key for key in stamp_a if stamp_a[key] != stamp_b.get(key)} >= set(differing), 'the stamps distinguish every field the probes distinguish'
        assert recovered.record['toolchain']['compilers']['c']['observed']['identity'] == b['compilers.c.identity']
        assert recovered.record['toolchain']['sdk']['source'] == ('SDKROOT named by the caller' if sdks['B']['sdkroot'] else 'xcrun --sdk macosx default')
        assert recovered.record['toolchain']['xcode']['status'] == ('ok' if (clt / 'usr/bin/xcodebuild').exists() else 'unknown'), recovered.record['toolchain']['xcode']
        outputs = {o['rel_path']: o for o in recovered.record['outputs']}
        assert all(prov.normalize_version(o['sdk']) == prov.normalize_version(b['sdk.version']) for o in outputs.values()), outputs
        records.append(dict(step='fresh-B', status=recovered.status, stamp=stamp_b, xcode=recovered.record['toolchain']['xcode']))
        back = co.build('switch-5-reuse-A-refused', 'full', env=env_a)
        check(back, 1, 'a changed toolchain cannot reuse this directory', absent=BEFORE_CARGO)
        preserved(back)
        records.append(dict(step='reuse-A-refused', status=back.status))
        save(out / 'switch.json', dict(developer_dirs=dict(a=str(selected), b=str(clt)), sdks=sdks, distinct_fields=differing,
                                       equal_fields=sorted(k for k in a if a[k] == b[k]), steps=records))
    print(f'toolchain switch: {len(records)} steps; fields that differed between A and B: {", ".join(differing)}')


if __name__ == '__main__':
    test_toolchain_switch(Path(sys.argv[1]).resolve(), sys.argv[2])
