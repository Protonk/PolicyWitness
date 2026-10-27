"""Native source controls: the configured-directory reading build.sh uses, on the real Meson boundary.

What Meson evaluated must be the tree, and what the compiler consumed for the worker must be in the identity.
`xpc=false` configures and compiles only the C executables (the worker, the validator and the extension issuer),
so these controls need no Swift discovery. The unmodified manifest passes; a worker declaration pointing at a
substitute file, present on disk so Meson accepts it, is refused by name; a worker include reaching outside the
digest's directories through a symlinked directory, or by a relative path, is refused by the closure check, and
so is an include of an absolute path outside the checkout that is neither the SDK nor the developer directory.
Finally the configured directory is copied along with the checkout, as build.sh invokes the check: the copy is
named as the checkout and the directory's recorded source is refused. The fixture, its build directory and the
copied checkout live under PW_TEST_SCRATCH; the mutated inputs, command output and receipts under the artifacts
directory. Each receipt counts the setup, compile and check launches with their elapsed times.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'docs'))
import fixture_inputs  # noqa: E402
from repository_tree import directory, required  # noqa: E402

# What Meson evaluates and the configured check reads: the manifest and options, every C source and header of
# the native tools, the runner sources, and the shared readers the check runs.
CONFIGURED_INPUTS = (required('meson.build'), required('meson.options'),
                     directory('controller/tools/pw_probe_runner', ('.c', '.h')),
                     directory('controller/tools/sb_api_validator', ('.c', '.h')), directory('runner/Sources'),
                     required('tests/lib/native_sources.py'), required('docs/generate_worker_identity.py'))


def launch(argv, cwd, timeout, launches, step):
    start = time.perf_counter()
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    launches.append(dict(step=step, argv=argv, returncode=result.returncode, elapsed_seconds=time.perf_counter() - start))
    return result


def configured_controls(repo, scratch, out):
    manifest_original = (repo / 'meson.build').read_text()
    worker_line = "  files('controller/tools/pw_probe_runner/pw_probe_runner.c'),"
    assert manifest_original.count(worker_line) == 1, 'fixture requires the current worker declaration'
    checker = repo / 'tests/lib/native_sources.py'
    substitute = repo / 'controller/tools/pw_probe_runner/substitute/pw_probe_runner.c'
    substitute.parent.mkdir()
    shutil.copy2(repo / 'controller/tools/pw_probe_runner/pw_probe_runner.c', substitute)
    for header in (repo / 'controller/tools/pw_probe_runner').glob('*.h'):
        shutil.copy2(header, substitute.parent / header.name)
    worker = repo / 'controller/tools/pw_probe_runner/pw_probe_runner.c'
    worker_original = worker.read_text()
    escape = repo / 'controller/src/escape.h'
    escape.parent.mkdir(exist_ok=True)
    escape.write_text('#define PW_AUDIT_ESCAPE 1\n')
    (repo / 'audit-headers').mkdir()
    (repo / 'audit-headers/audit.h').write_text('#define PW_AUDIT_VALUE 17\n')
    outside = scratch / 'outside-checkout'
    outside.mkdir()
    (outside / 'escape.h').write_text('#define PW_OUTSIDE_VALUE 23\n')
    link = repo / 'controller/tools/pw_probe_runner/audit-link'
    include_line = '#include "pw_probe_runner_abi.h"\n'
    assert worker_original.count(include_line) == 1
    receipts = []
    for name, manifest, source, symlink, expected, diagnostic in [
        ('configured-unmodified', manifest_original, worker_original, False, 0, None),
        ('configured-worker-substituted',
         manifest_original.replace(worker_line, "  files('controller/tools/pw_probe_runner/substitute/pw_probe_runner.c'),"),
         worker_original, False, 1,
         "pw-probe-runner has 'controller/tools/pw_probe_runner/substitute/pw_probe_runner.c' which the tree does not expect"),
        ('configured-symlinked-include', manifest_original,
         worker_original.replace(include_line, include_line + '#include "audit-link/audit.h"\n'), True, 1,
         "symlink under identity sources: controller/tools/pw_probe_runner/audit-link"),
        ('configured-relative-escape', manifest_original,
         worker_original.replace(include_line, include_line + '#include "../../src/escape.h"\n'), False, 1,
         "pw-probe-runner consumed 'controller/src/escape.h' which is not an identity input"),
        ('configured-absolute-escape', manifest_original,
         worker_original.replace(include_line, include_line + f'#include "{(outside / "escape.h").resolve()}"\n'), False, 1,
         f"pw-probe-runner consumed '{(outside / 'escape.h').resolve()}' outside the checkout, the SDK and the developer directory"),
        ('configured-restored', manifest_original, worker_original, False, 0, None),
    ]:
        evidence = out / name
        evidence.mkdir()
        (repo / 'meson.build').write_text(manifest)
        (evidence / 'meson.build').write_text(manifest)
        worker.write_text(source)
        (evidence / 'pw_probe_runner.c').write_text(source)
        if link.is_symlink():
            link.unlink()
        if symlink:
            link.symlink_to('../../../audit-headers')
        builddir = repo / 'builddir'
        shutil.rmtree(builddir, ignore_errors=True)
        launches = []
        for step, argv in (('setup', ['meson', 'setup', str(builddir), str(repo), '-Dxpc=false']),
                           ('compile', ['meson', 'compile', '-C', str(builddir)])):
            result = launch(argv, repo, 300, launches, step)
            (evidence / f'{step}.stdout').write_text(result.stdout)
            (evidence / f'{step}.stderr').write_text(result.stderr)
            if result.returncode != 0:
                raise AssertionError(f'{name}: meson {step} failed: {result.stderr}')
        argv = [sys.executable, '-B', '-S', str(checker), '--builddir', str(builddir), '--root', str(repo)]
        result = launch(argv, repo, 60, launches, 'check')
        (evidence / 'stdout').write_text(result.stdout)
        (evidence / 'stderr').write_text(result.stderr)
        record = dict(scenario=name, mode='meson', argv=argv, returncode=result.returncode, expected_returncode=expected,
                      expected_diagnostic=diagnostic, launches=launches,
                      elapsed_seconds=sum(entry['elapsed_seconds'] for entry in launches))
        (evidence / 'command.json').write_text(json.dumps(record, indent=2) + '\n')
        if result.returncode != expected or (diagnostic and diagnostic not in result.stderr):
            raise AssertionError(f'{name}: unexpected configured check result: {record}\n{result.stdout}\n{result.stderr}')
        receipts.append(record)
    (repo / 'meson.build').write_text(manifest_original)
    worker.write_text(worker_original)
    copy = scratch / 'copied-checkout'
    shutil.copytree(repo, copy, symlinks=True)
    evidence = out / 'configured-copied-checkout'
    evidence.mkdir()
    argv = [sys.executable, '-B', '-S', str(copy / 'tests/lib/native_sources.py'), '--builddir', str(copy / 'builddir'), '--root', str(copy)]
    launches = []
    result = launch(argv, copy, 60, launches, 'check')
    (evidence / 'stdout').write_text(result.stdout)
    (evidence / 'stderr').write_text(result.stderr)
    diagnostic = f'builddir: configured for {repo.resolve()}, not {copy.resolve()}'
    record = dict(scenario='configured-copied-checkout', mode='meson', argv=argv, returncode=result.returncode,
                  expected_returncode=1, expected_diagnostic=diagnostic, launches=launches,
                  elapsed_seconds=launches[0]['elapsed_seconds'])
    (evidence / 'command.json').write_text(json.dumps(record, indent=2) + '\n')
    if result.returncode != 1 or diagnostic not in result.stderr:
        raise AssertionError(f'copied checkout: unexpected configured check result: {record}\n{result.stdout}\n{result.stderr}')
    receipts.append(record)
    return receipts


def main(argv):
    out = Path(argv[1])
    out.mkdir(parents=True, exist_ok=True)
    base = os.environ.get('PW_TEST_SCRATCH')
    if base:
        Path(base).mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix='native-sources-', dir=base))
    repo = scratch / 'repo'
    copied = fixture_inputs.copy_declared(ROOT, repo, fixture_inputs.expand(ROOT, CONFIGURED_INPUTS))
    print(f'fixture: {copied.files} files, {copied.bytes} bytes, {copied.seconds:.3f} s')
    receipts = configured_controls(repo, scratch, out)
    (out / 'receipts.json').write_text(json.dumps(dict(
        schema_version=1, case='preflight/native_source_controls', mode='meson', ok=True,
        fixture=dict(files=copied.files, directories=copied.directories, bytes=copied.bytes, seconds=copied.seconds),
        controls=receipts), indent=2) + '\n')
    shutil.rmtree(scratch, ignore_errors=True)
    print(f'{len(receipts)} configured native source controls passed; '
          f'{sum(len(r["launches"]) for r in receipts)} launches counted')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
