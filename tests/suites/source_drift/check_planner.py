"""Run the real source checker against disposable planner and host API mutations."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HOST = Path('runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift')
CALL = 'if predictionUnavailableOpFilters.contains(PredictionUnavailablePair(operation: check.operation, filterKind: kind)) {'


def main(out):
    out.mkdir()
    repo = out / 'repo'
    # Copy only the checker's inputs, never build products or previous runs.
    paths = ['AGENTS.md', 'meson.build', 'meson.options', 'runner/README.md', 'tests/README.md', 'docs/SIGNING.md',
             'tests/lib/native_sources.py', 'docs/generate_worker_identity.py', 'controller/tools/pw_probe_runner/pw_probe_runner.c',
             'controller/tools/pw_probe_runner/pw_worker_evidence.h', 'controller/tools/pw_probe_runner/pw_profile_capture.h',
             'controller/tools/sb_api_validator/sb_api_validator.c',
             'runner/Services/PWRunner/main.swift', 'runner/Clients/PWRunnerClient/main.swift',
             'tests/COVERAGE.md', 'tests/catalog.json', 'docs/PolicyWitness.md',
             'controller/tools/pw_probe_runner/pw_probe_runner_abi.h',
             'controller/src/cli.rs', 'controller/README.md', 'docs/ARCHITECTURE.md', 'docs/BUILD.md',
             'tests/fixtures/contract/response_shape.json',
             'tests/fixtures/contract/envelope_shape.json',
             'tests/suites/source_drift/check.py']
    paths += [str(p.relative_to(ROOT)) for p in (ROOT / 'runner/Sources').rglob('*') if p.is_file()]
    paths += [str(p.relative_to(ROOT)) for pattern in ('*/run.sh', '*/README.md')
              for p in (ROOT / 'tests/suites').glob(pattern)]
    for name in paths:
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    original = (repo / HOST).read_text()
    if original.count(CALL) != 1:
        raise AssertionError('fixture requires the current planner membership condition')
    mirror = '''
private let hostExclusions: Set<PredictionUnavailablePair> = [
    .init(operation: "iokit-open-service", filterKind: PWRunnerWire.sandboxFilterIokitRegistryEntryClass),
    .init(operation: "iokit-open-user-client", filterKind: PWRunnerWire.sandboxFilterIokitUserClientClass),
    .init(operation: "sysctl-read", filterKind: PWRunnerWire.sandboxFilterSysctlName),
]
'''
    no_call = original.replace(CALL, 'if false {')
    scenarios = [
        ('baseline', original, 0, None),
        ('mirror-three', original.replace(CALL, CALL.replace('predictionUnavailableOpFilters', 'hostExclusions')) + mirror,
         1, 'must not define a local exclusion table'),
        ('mirror-four', original + mirror.replace('\n]', '\n    .init(operation: "file-read-data", filterKind: PWRunnerWire.sandboxFilterPath),\n]'),
         1, 'must not define a local exclusion table'),
        ('inferred-literal-table', original + '\nlet hostExclusions = [PredictionUnavailablePair(operation: "file-read-data", filterKind: PWRunnerWire.sandboxFilterPath)]\n',
         1, 'must not define a local exclusion table'),
        ('shadow-shared', original.replace(CALL, 'let predictionUnavailableOpFilters = knownFilterKinds\n        ' + CALL),
         1, 'shadow the shared set'),
        ('missing-call', no_call, 1, 'planValidatorQueries must use'),
        ('comment-only-call', no_call.replace('if false {', '// ' + CALL + '\n        if false {'),
         1, 'planValidatorQueries must use'),
        ('nested-comment-only-call', no_call.replace('if false {', '/* outer /* nested */ ' + CALL + ' */ if false {'),
         1, 'planValidatorQueries must use'),
        ('string-only-call', no_call.replace('if false {', 'let example = "' + CALL + '"\n        if false {'),
         1, 'planValidatorQueries must use'),
        ('other-function-call', no_call + '\nfunc unrelated() {\n    ' + CALL + '\n    }\n}\n',
         1, 'planValidatorQueries must use'),
        ('formatting', original.replace(CALL, CALL.replace('if ', 'if\n            ').replace('.contains(', ' . contains (\n')),
         0, None),
        ('commented-table', original + '\n/* example /* nested */\n' + mirror + '\n*/\n', 0, None),
        ('string-table', original + '\nlet example = """\n' + mirror + '\n"""\n', 0, None),
        ('restored', original, 0, None),
    ]
    scenarios = [(name, HOST, source, expected, diagnostic)
                 for name, source, expected, diagnostic in scenarios]
    shim = Path('runner/Sources/PWCWorkerShim/PWCWorkerShim.c')
    shim_original = (repo / shim).read_text()
    for name, path, source, snippet, expected in [
        ('host-binding', HOST, original, '@_silgen_name("sandbox_check") func native() -> Int32', 1),
        ('host-unrelated-api', HOST, original,
         'let callback: @convention(c) (Int32) -> Int32 = ptr\nlet h = dlopen("/usr/lib/libSystem.B.dylib", RTLD_NOW)', 0),
        ('shim-sandbox-call', shim, shim_original, 'void forbidden(void) { sandbox_free_error(0); }', 1),
        ('shim-symbol-constant', shim, shim_original,
         'const char *symbol = "sandbox_check"; void *f = dlsym(handle, symbol);', 1),
        ('shim-explanatory-string', shim, shim_original, 'const char *example = "sandbox_check(pid)";', 0),
    ]:
        scenarios.append((name, path, source + '\n' + snippet + '\n', expected,
                          'the XPC host never links, loads or calls libsandbox' if expected else None))
    # The Meson reader: a core file dropped from or added to the PWRunner target is
    # named by the diff; a missing host or shim target is named as such.
    manifest = Path('meson.build')
    manifest_original = (repo / manifest).read_text()
    core_line = "    'runner/Sources/PWRunnerCore/PathUtils.swift',\n"
    assert manifest_original.count(core_line) == 1, 'fixture requires the current PWRunner source list'
    host_declaration = manifest_original[manifest_original.index("pwrunner = executable('PWRunner',"):]
    host_declaration = host_declaration[:host_declaration.index('endif')]
    decoy = ('\nif false\n' + host_declaration.replace('pwrunner = ', 'pwrunner_decoy = ').rstrip() + '\nendif\n')
    worker_line = "  files('controller/tools/pw_probe_runner/pw_probe_runner.c'),"
    assert manifest_original.count(worker_line) == 1
    for name, mutated, diagnostic in [
        ('meson-core-file-dropped', manifest_original.replace(core_line, ''),
         "PWRunner lacks 'runner/Sources/PWRunnerCore/PathUtils.swift' which is in the tree"),
        ('meson-core-file-added', manifest_original.replace(core_line, core_line + "    'runner/Sources/PWRunnerCore/Missing.swift',\n"),
         "PWRunner has 'runner/Sources/PWRunnerCore/Missing.swift' which the tree does not expect"),
        ('meson-host-target-missing', manifest_original.replace("executable('PWRunner',", "executable('PWRunnerRenamed',"),
         "no 'PWRunner' target"),
        ('meson-shim-target-missing', manifest_original.replace("static_library('PWCWorkerShim',", "static_library('PWCWorkerShimRenamed',"),
         "no 'PWCWorkerShim' target"),
        # A dead declaration with the complete list beside a live one missing a
        # file: the duplicate name is refused instead of resolved.
        ('meson-duplicate-host-declaration', manifest_original.replace(core_line, '') + decoy,
         "declares 'PWRunner' 2 times"),
        ('meson-worker-source-substituted',
         manifest_original.replace(worker_line, "  files('controller/tools/pw_probe_runner/substitute/pw_probe_runner.c'),"),
         "pw-probe-runner has 'controller/tools/pw_probe_runner/substitute/pw_probe_runner.c' which the tree does not expect"),
    ]:
        assert mutated != manifest_original, name
        scenarios.append((name, manifest, mutated, 1, diagnostic))
    scenarios.append(('meson-restored', manifest, manifest_original, 0, None))
    receipts = []
    for name, path, source, expected, diagnostic in scenarios:
        evidence = out / name
        evidence.mkdir()
        (repo / HOST).write_text(original)
        (repo / shim).write_text(shim_original)
        (repo / manifest).write_text(manifest_original)
        (repo / path).write_text(source)
        (evidence / path.name).write_text(source)
        argv = [sys.executable, '-B', str(repo / 'tests/suites/source_drift/check.py')]
        result = subprocess.run(argv, cwd=repo, capture_output=True, text=True, timeout=30)
        (evidence / 'stdout').write_text(result.stdout)
        (evidence / 'stderr').write_text(result.stderr)
        record = dict(scenario=name, argv=argv, returncode=result.returncode,
                      expected_returncode=expected, expected_diagnostic=diagnostic)
        (evidence / 'command.json').write_text(json.dumps(record, indent=2) + '\n')
        if result.returncode != expected or (diagnostic and diagnostic not in result.stderr):
            raise AssertionError(f'{name}: unexpected checker result: {record}\n{result.stdout}\n{result.stderr}')
        receipts.append(record)
    if (ROOT / HOST).read_text() != original:
        raise AssertionError('source controls changed the working planner')
    receipts += configured_controls(repo, manifest_original, worker_line, out)
    (out / 'controls.json').write_text(json.dumps({'ok': True, 'scenarios': receipts}, indent=2) + '\n')
    print(f'{len(receipts)} planner and host source controls passed')


def configured_controls(repo, manifest_original, worker_line, out):
    """The configured-directory reading build.sh uses: what Meson evaluated must be the tree,
    and what the compiler consumed for the worker must be in the identity.

    xpc=false configures and compiles only the two C executables, so these
    controls need no Swift discovery. The unmodified manifest passes; a worker
    declaration pointing at a substitute file, present on disk so Meson accepts
    it, is refused by name; a worker include reaching outside the digest's
    directories through a symlinked directory, or by a relative path, is
    refused by the closure check, and so is an include of an absolute path
    outside the checkout that is neither the SDK nor the developer directory.
    Finally the configured directory is copied
    along with the checkout, as build.sh invokes the check: the copy is named
    as the checkout and the directory's recorded source is refused."""
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
    outside = out / 'outside-checkout'
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
        for step, argv in (('setup', ['meson', 'setup', str(builddir), str(repo), '-Dxpc=false']),
                           ('compile', ['meson', 'compile', '-C', str(builddir)])):
            result = subprocess.run(argv, cwd=repo, capture_output=True, text=True, timeout=300)
            (evidence / f'{step}.stdout').write_text(result.stdout)
            (evidence / f'{step}.stderr').write_text(result.stderr)
            if result.returncode != 0:
                raise AssertionError(f'{name}: meson {step} failed: {result.stderr}')
        argv = [sys.executable, '-B', str(checker), '--builddir', str(builddir), '--root', str(repo)]
        result = subprocess.run(argv, cwd=repo, capture_output=True, text=True, timeout=60)
        (evidence / 'stdout').write_text(result.stdout)
        (evidence / 'stderr').write_text(result.stderr)
        record = dict(scenario=name, argv=argv, returncode=result.returncode,
                      expected_returncode=expected, expected_diagnostic=diagnostic)
        (evidence / 'command.json').write_text(json.dumps(record, indent=2) + '\n')
        if result.returncode != expected or (diagnostic and diagnostic not in result.stderr):
            raise AssertionError(f'{name}: unexpected configured check result: {record}\n{result.stdout}\n{result.stderr}')
        receipts.append(record)
    (repo / 'meson.build').write_text(manifest_original)
    worker.write_text(worker_original)
    copy = out / 'copied-checkout'
    shutil.copytree(repo, copy, symlinks=True)
    evidence = out / 'configured-copied-checkout'
    evidence.mkdir()
    argv = [sys.executable, '-B', str(copy / 'tests/lib/native_sources.py'), '--builddir', str(copy / 'builddir'), '--root', str(copy)]
    result = subprocess.run(argv, cwd=copy, capture_output=True, text=True, timeout=60)
    (evidence / 'stdout').write_text(result.stdout)
    (evidence / 'stderr').write_text(result.stderr)
    diagnostic = f'builddir: configured for {repo.resolve()}, not {copy.resolve()}'
    record = dict(scenario='configured-copied-checkout', argv=argv, returncode=result.returncode,
                  expected_returncode=1, expected_diagnostic=diagnostic)
    (evidence / 'command.json').write_text(json.dumps(record, indent=2) + '\n')
    if result.returncode != 1 or diagnostic not in result.stderr:
        raise AssertionError(f'copied checkout: unexpected configured check result: {record}\n{result.stdout}\n{result.stderr}')
    receipts.append(record)
    return receipts


if __name__ == '__main__':
    main(Path(sys.argv[1]))
