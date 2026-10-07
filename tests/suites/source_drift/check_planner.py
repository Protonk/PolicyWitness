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
    paths = ['AGENTS.md', 'build.sh', 'runner/README.md', 'tests/README.md',
             'tests/COVERAGE.md', 'tests/catalog.json', 'docs/PolicyWitness.md',
             'controller/tools/pw_probe_runner/pw_probe_runner_abi.h',
             'controller/src/cli.rs', 'controller/README.md', 'docs/ARCHITECTURE.md',
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
    receipts = []
    for name, path, source, expected, diagnostic in scenarios:
        evidence = out / name
        evidence.mkdir()
        (repo / HOST).write_text(original)
        (repo / shim).write_text(shim_original)
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
    (out / 'controls.json').write_text(json.dumps({'ok': True, 'scenarios': receipts}, indent=2) + '\n')
    print(f'{len(receipts)} planner and host source controls passed')


if __name__ == '__main__':
    main(Path(sys.argv[1]))
