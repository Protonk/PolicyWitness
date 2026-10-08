#!/usr/bin/env python3
"""Compare native executables and assembled apps by structure, not by bytes.

Repeated direct Swift builds of identical sources differ in bytes, and the
accepted linker additions change C output bytes, so byte equality is not the
acceptance gate. For an executable this compares the file type, the dynamic
libraries with their versions, the load-command sequence (ignoring the code
signature), each segment's sections, the platform build version, the sizes of
the code and data segments, the undefined symbols, the undefined `_sandbox_*`
imports and the Swift module names found in mangled symbols. `__LINKEDIT`
and the total from size(1) are recorded, not compared: signing and the
debug map change them without changing the program.

For an assembled app it compares the bundle layout, the evidence manifest's
`(id, kind, rel_path)` inventory and entitlements, the exported `_pw_*`
markers in `symbols.json`, every executable as above, and both Info.plists
except the accounted build stamps (and, for a temporary signed copy, the
fresh bundle identifiers). Signatures and content hashes are not compared.

    native_compare.py exe CANDIDATE BASELINE [--out REPORT] [--expect-module NAME] [--no-sandbox-imports]
    native_compare.py app CANDIDATE BASELINE [--out REPORT] [--temporary-copy] [--across-builds]

With --across-builds the two apps were built from different sources, so the
code and data sizes are recorded rather than compared; libraries, load
commands, segment and section names, imports, markers and entitlements are
still compared. Reports identify differing fields, not their source causes;
source attribution and live behavioral validation require separate review.

Exit 1 when a compared field differs. The report lists every difference and
every recorded-only field so each accepted difference is visible.
"""
import argparse
import json
import plistlib
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import artifact

STRICT_SEGMENTS = ('__TEXT', '__DATA_CONST', '__DATA')
RECORDED_SEGMENTS = ('__LINKEDIT',)
IGNORED_LOAD_COMMANDS = ('LC_CODE_SIGNATURE',)
STAMP_KEYS = ('CFBundleShortVersionString', 'CFBundleVersion', 'PWBuildDescribe', 'PWBuildCommit')
IDENTIFIER_KEYS = ('CFBundleIdentifier',)
SWIFT_MODULE_RE = re.compile(r'\$s(\d+)([A-Za-z_][A-Za-z0-9_]*)')


def run(argv):
    result = subprocess.run([str(a) for a in argv], capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f'{argv[0]} failed on {argv[-1]}: {result.stderr.strip()}')
    return result.stdout


def load_commands(path):
    """Parse otool -l into a list of load commands with their sections."""
    commands = []
    current = None
    section = None
    for line in run(['/usr/bin/otool', '-l', path]).splitlines():
        stripped = line.strip()
        if stripped.startswith('Load command '):
            current = {'sections': []}
            section = None
            commands.append(current)
            continue
        if stripped == 'Section':
            section = {}
            current['sections'].append(section)
            continue
        if current is None or ' ' not in stripped:
            continue
        key, _, value = stripped.partition(' ')
        target = section if section is not None else current
        target.setdefault(key, value.strip())
    return commands


def describe(path):
    path = Path(path)
    commands = load_commands(path)
    segments = [c for c in commands if c.get('cmd') in ('LC_SEGMENT_64', 'LC_SEGMENT')]
    build = next((c for c in commands if c.get('cmd') == 'LC_BUILD_VERSION'), {})
    all_symbols = run(['/usr/bin/nm', path])
    modules = {m.group(2)[:int(m.group(1))] for m in SWIFT_MODULE_RE.finditer(all_symbols)
               if len(m.group(2)) >= int(m.group(1))}
    undefined = sorted({line.split()[-1] for line in run(['/usr/bin/nm', '-u', path]).splitlines() if line.strip()})
    size_lines = run(['/usr/bin/size', path]).splitlines()
    size = dict(zip(size_lines[0].split(), size_lines[1].split())) if len(size_lines) >= 2 else {}
    return dict(
        path=str(path),
        file_type=run(['/usr/bin/file', '-b', path]).strip(),
        dylibs=[c['name'].split(' (offset')[0] + ' ' + c.get('current version', '') + ' ' + c.get('compatibility version', '')
                for c in commands if c.get('cmd') in ('LC_LOAD_DYLIB', 'LC_LOAD_WEAK_DYLIB', 'LC_REEXPORT_DYLIB')],
        load_commands=[c['cmd'] for c in commands if c.get('cmd') not in IGNORED_LOAD_COMMANDS],
        segments={c['segname']: [s.get('sectname') for s in c['sections']] for c in segments},
        segment_sizes={c['segname']: dict(vmsize=c.get('vmsize'), filesize=c.get('filesize')) for c in segments},
        section_sizes={c['segname'] + ',' + s.get('sectname', ''): s.get('size') for c in segments for s in c['sections']},
        build_version={k: build.get(k) for k in ('platform', 'minos', 'sdk')},
        uuid=next((c.get('uuid') for c in commands if c.get('cmd') == 'LC_UUID'), None),
        code_signature=any(c.get('cmd') == 'LC_CODE_SIGNATURE' for c in commands),
        size=size,
        undefined=undefined,
        sandbox_imports=artifact.sandbox_imports(run(['/usr/bin/nm', '-u', path])),
        swift_modules=sorted(modules),
    )


def compare(candidate, baseline, *, expect_module=None, no_sandbox_imports=False, same_sources=True):
    left, right = describe(candidate), describe(baseline)
    differences = []

    def check(name, a, b):
        if a != b:
            differences.append(dict(field=name, candidate=a, baseline=b))

    check('file_type', left['file_type'], right['file_type'])
    check('dylibs', left['dylibs'], right['dylibs'])
    check('load_commands', left['load_commands'], right['load_commands'])
    check('segments', left['segments'], right['segments'])
    check('build_version', left['build_version'], right['build_version'])
    if same_sources:
        for segment in STRICT_SEGMENTS:
            check(f'segment_sizes[{segment}]', left['segment_sizes'].get(segment), right['segment_sizes'].get(segment))
        for key in sorted(set(left['section_sizes']) | set(right['section_sizes'])):
            if key.split(',')[0] in STRICT_SEGMENTS:
                check(f'section_sizes[{key}]', left['section_sizes'].get(key), right['section_sizes'].get(key))
        check('size[__TEXT]', left['size'].get('__TEXT'), right['size'].get('__TEXT'))
        check('size[__DATA]', left['size'].get('__DATA'), right['size'].get('__DATA'))
    check('undefined', left['undefined'], right['undefined'])
    check('sandbox_imports', left['sandbox_imports'], right['sandbox_imports'])
    check('swift_modules', left['swift_modules'], right['swift_modules'])
    requirements = []
    if expect_module is not None and expect_module not in left['swift_modules']:
        requirements.append(f'candidate lacks Swift module {expect_module!r}: {left["swift_modules"]}')
    if no_sandbox_imports and left['sandbox_imports']:
        requirements.append(f'candidate imports libsandbox symbols: {left["sandbox_imports"]}')
    recorded = {name: dict(candidate=left[name], baseline=right[name]) for name in ('uuid', 'code_signature', 'size')}
    recorded['segment_sizes'] = {s: dict(candidate=left['segment_sizes'].get(s), baseline=right['segment_sizes'].get(s))
                                 for s in (RECORDED_SEGMENTS if same_sources else RECORDED_SEGMENTS + STRICT_SEGMENTS)}
    return dict(candidate=left, baseline=right, differences=differences, requirements_failed=requirements,
                recorded_only=recorded, equal=not differences and not requirements)


def plist(path):
    return plistlib.loads(Path(path).read_bytes())


def compare_apps(candidate, baseline, *, temporary_copy=False, across_builds=False):
    candidate, baseline = Path(candidate), Path(baseline)
    differences = []

    def check(name, a, b):
        if a != b:
            differences.append(dict(field=name, candidate=a, baseline=b))

    check('layout', sorted(artifact.inventory(candidate)), sorted(artifact.inventory(baseline)))
    manifests = [json.loads((app / artifact.MANIFEST).read_text()) for app in (candidate, baseline)]
    check('manifest.entries', [sorted((e['id'], e['kind'], e['rel_path']) for e in m['entries']) for m in manifests][0],
          [sorted((e['id'], e['kind'], e['rel_path']) for e in m['entries']) for m in manifests][1])
    check('manifest.entitlements', {e['rel_path']: e.get('entitlements') for e in manifests[0]['entries']},
          {e['rel_path']: e.get('entitlements') for e in manifests[1]['entries']})
    check('manifest.app_entitlements', manifests[0]['app_entitlements'], manifests[1]['app_entitlements'])
    check('manifest.app_binary_rel_path', manifests[0]['app_binary_rel_path'], manifests[1]['app_binary_rel_path'])
    if not temporary_copy:
        check('manifest.app_bundle_id', manifests[0]['app_bundle_id'], manifests[1]['app_bundle_id'])
    symbols = [json.loads((app / artifact.SYMBOLS).read_text()) for app in (candidate, baseline)]
    check('symbols.pw_markers', {e['rel_path']: sorted(s for s in e['symbols'] if s.startswith('pw_')) for e in symbols[0]['entries']},
          {e['rel_path']: sorted(s for s in e['symbols'] if s.startswith('pw_')) for e in symbols[1]['entries']})
    executables = {}
    for relative in artifact.EXECUTABLES:
        report = compare(candidate / relative, baseline / relative, same_sources=not across_builds)
        executables[relative] = report
        for difference in report['differences']:
            differences.append(dict(field=f'{relative}: {difference["field"]}', candidate=difference['candidate'],
                                    baseline=difference['baseline']))
    plists = {}
    for relative in ('Contents/Info.plist', artifact.SERVICE + '/Contents/Info.plist'):
        left, right = plist(candidate / relative), plist(baseline / relative)
        excluded = STAMP_KEYS + (IDENTIFIER_KEYS if temporary_copy else ())
        plists[relative] = dict(candidate={k: left.get(k) for k in excluded}, baseline={k: right.get(k) for k in excluded})
        check(f'{relative} (without {", ".join(excluded)})', {k: v for k, v in left.items() if k not in excluded},
              {k: v for k, v in right.items() if k not in excluded})
    return dict(candidate=str(candidate), baseline=str(baseline), temporary_copy=temporary_copy,
                across_builds=across_builds, differences=differences, executables=executables,
                plists_recorded_only=plists, equal=not differences)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('mode', choices=('exe', 'app'))
    parser.add_argument('candidate', type=Path)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--expect-module')
    parser.add_argument('--no-sandbox-imports', action='store_true')
    parser.add_argument('--temporary-copy', action='store_true')
    parser.add_argument('--across-builds', action='store_true')
    args = parser.parse_args()
    if args.mode == 'exe':
        report = compare(args.candidate, args.baseline, expect_module=args.expect_module,
                         no_sandbox_imports=args.no_sandbox_imports)
    else:
        report = compare_apps(args.candidate, args.baseline, temporary_copy=args.temporary_copy,
                              across_builds=args.across_builds)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + '\n')
    summary = dict(equal=report['equal'], differences=report['differences'],
                   requirements_failed=report.get('requirements_failed', []))
    print(json.dumps(summary, indent=2))
    return 0 if report['equal'] else 1


if __name__ == '__main__':
    sys.exit(main())
