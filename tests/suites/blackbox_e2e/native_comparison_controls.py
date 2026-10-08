#!/usr/bin/env python3
"""Exercise the structural executable comparison through its CLI with constructed mutants.

A tiny C program is compiled once with the macOS SDK clang. Each control
compares a candidate with that baseline through `tests/lib/native_compare.py
exe`: an identical copy must compare equal, and byte-level edits to the
Mach-O load commands that leave the code untouched must each be named by the
comparer (a changed dynamic-library version, a changed library name, a changed
platform minimum version). A second program with more code must differ by
section size, and a program that imports a sandbox symbol must fail the
host's no-sandbox-imports requirement. Every control retains its inputs, the
comparison report, stdout and stderr. No app, migration output or signing
identity is needed.
"""
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
COMPARER = ROOT / 'tests/lib/native_compare.py'
CLANG = ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-Wall', '-O2', '-std=c11']
MH_MAGIC_64 = 0xfeedfacf
LC_LOAD_DYLIB = 0x0c
LC_BUILD_VERSION = 0x32

PROGRAM = '#include <stdio.h>\nint main(void) { puts("control"); return 0; }\n'
LARGER = ('#include <stdio.h>\nstatic int work(int n) { int s = 0; for (int i = 0; i < n; i++) s += i * i; return s; }\n'
          'int main(int argc, char **argv) { (void)argv; printf("%d\\n", work(argc * 1000)); return 0; }\n')
SANDBOX = ('#include <stdio.h>\nextern int sandbox_check(int pid, const char *op, int type, ...);\n'
           'int main(void) { printf("%d\\n", sandbox_check(1, "file-read-data", 0)); return 0; }\n')


def compile_program(out, name, source, *extra):
    out.mkdir(parents=True, exist_ok=True)
    path = out / name
    (out / (name + '.c')).write_text(source)
    subprocess.run([*CLANG, *extra, '-o', str(path), str(out / (name + '.c'))], check=True, timeout=120)
    return path


def load_commands(data):
    assert struct.unpack_from('<I', data)[0] == MH_MAGIC_64, 'control expects a single-architecture 64-bit Mach-O'
    ncmds = struct.unpack_from('<I', data, 16)[0]
    offset = 32
    for _ in range(ncmds):
        cmd, size = struct.unpack_from('<II', data, offset)
        yield cmd, offset, size
        offset += size


def mutate(baseline, target, edit):
    data = bytearray(baseline.read_bytes())
    edited = 0
    for cmd, offset, size in load_commands(data):
        edited += edit(data, cmd, offset, size)
    assert edited == 1, f'expected exactly one edited load command, edited {edited}'
    target.write_bytes(data)
    target.chmod(0o755)


def dylib_versions(data, cmd, offset, size):
    if cmd != LC_LOAD_DYLIB:
        return 0
    struct.pack_into('<II', data, offset + 16, 0x640000, 0x630000)  # current 100.0.0, compatibility 99.0.0
    return 1


def dylib_name(data, cmd, offset, size):
    if cmd != LC_LOAD_DYLIB:
        return 0
    name_offset = struct.unpack_from('<I', data, offset + 8)[0]
    start = offset + name_offset
    end = data.index(b'\0', start)
    name = bytes(data[start:end])
    assert name == b'/usr/lib/libSystem.B.dylib', name
    data[start:end] = b'/usr/lib/libSystem.X.dylib'
    return 1


def minimum_os(data, cmd, offset, size):
    if cmd != LC_BUILD_VERSION:
        return 0
    struct.pack_into('<I', data, offset + 12, 13 << 16)  # minos 13.0
    return 1


def main():
    out = Path(sys.argv[1])
    baseline = compile_program(out / 'baseline', 'control', PROGRAM)
    results = []

    def run(name, candidate, *, differs=(), fails_requirement=False, options=()):
        directory = out / name
        directory.mkdir(parents=True, exist_ok=True)
        report_path = directory / 'comparison.json'
        process = subprocess.run([sys.executable, '-B', str(COMPARER), 'exe', str(candidate), str(baseline),
                                  '--out', str(report_path), *options], text=True, capture_output=True, timeout=120)
        (directory / 'stdout.txt').write_text(process.stdout)
        (directory / 'stderr.txt').write_text(process.stderr)
        report = json.loads(report_path.read_text())
        fields = {d['field'] for d in report['differences']}
        expected_rc = 1 if differs or fails_requirement else 0
        assert process.returncode == expected_rc and report['equal'] == (expected_rc == 0), (name, process.returncode, fields, process.stderr)
        for field in differs:
            assert any(f == field or f.startswith(field + '[') for f in fields), (name, field, fields)
        if not differs:
            assert not fields, (name, fields)
        assert bool(report['requirements_failed']) == fails_requirement, (name, report['requirements_failed'])
        results.append(dict(name=name, returncode=process.returncode, differences=sorted(fields),
                            requirements_failed=report['requirements_failed']))
        (out / 'controls.json').write_text(json.dumps(results, indent=2) + '\n')

    identical = out / 'identical' / 'control'
    identical.parent.mkdir(parents=True, exist_ok=True)
    identical.write_bytes(baseline.read_bytes())
    identical.chmod(0o755)
    run('identical', identical)
    for name, edit, field in (('dylib_versions', dylib_versions, 'dylibs'), ('dylib_name', dylib_name, 'dylibs'),
                              ('minimum_os', minimum_os, 'build_version')):
        candidate = out / name / 'control'
        candidate.parent.mkdir(parents=True, exist_ok=True)
        mutate(baseline, candidate, edit)
        run(name, candidate, differs=(field,))
    run('larger_program', compile_program(out / 'larger_program', 'control', LARGER), differs=('section_sizes[__TEXT,__text]',))
    sandboxed = compile_program(out / 'sandbox_import', 'control', SANDBOX, '-lsandbox')
    run('sandbox_import', sandboxed, differs=('dylibs', 'sandbox_imports', 'undefined'), fails_requirement=True,
        options=('--no-sandbox-imports',))
    print(f'{len(results)} structural comparison controls passed')


if __name__ == '__main__':
    main()
