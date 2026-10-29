"""Exercise unchanged exec-reader assertions against disposable source defects.

Only the test package is copied/mutated. The fixture publishes constructed ABI
facts, and no sandbox policy or actual exec child is involved. Source identity
stays unchanged deliberately to reach the publication and absence oracles.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tests/lib"))
from build_receipt import record_build

SWIFT = ['/usr/bin/xcrun', 'swift']
scratch = Path(sys.argv[2]).resolve()
OUT = Path(sys.argv[1]).resolve()
OUT.mkdir(parents=True)
commands = []


def run(label, argv, *, env=None, timeout=180):
    args = [str(value) for value in argv]
    commands.append(dict(label=label, argv=args))
    (OUT / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
    with (OUT / (label + '.log')).open('w') as log:
        result = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                env=env, timeout=timeout)
    return result.returncode, (OUT / (label + '.log')).read_text()


package = OUT / 'runner'
shutil.copytree(ROOT / 'runner/Sources', package / 'Sources')
shutil.copy2(ROOT / 'runner/Package.swift', package / 'Package.swift')
tests = package / 'Tests/PWRunnerCoreTests'
shutil.copytree(ROOT / 'runner/Tests/PWRunnerCoreTests', tests)
(tests / 'main.swift').write_text('import Foundation\nlet tk = TestKit()\nrunExecObservationTests(tk)\n'
                                  'print(tk.summary())\nexit(tk.exitCode())\n')
contract = OUT / 'tests/fixtures/contract'
contract.mkdir(parents=True)
shutil.copy2(ROOT / 'tests/fixtures/contract/exec_observation.json', contract / 'exec_observation.json')
native = OUT / 'native'
native.mkdir()
for header in (ROOT / 'controller/tools/pw_probe_runner').glob('*.h'):
    shutil.copy2(header, native / header.name)
fixture_source = OUT / 'fixtures/worker_lifecycle/worker.c'
fixture_source.parent.mkdir(parents=True)
shutil.copy2(ROOT / 'tests/fixtures/worker_lifecycle/worker.c', fixture_source)
diagnostic = OUT / 'fixtures/diagnostic_transport'
diagnostic.mkdir()
shutil.copy2(ROOT / 'tests/fixtures/diagnostic_transport/worker.h', diagnostic / 'worker.h')
(OUT / 'source-sha256.json').write_text(json.dumps({str(p.relative_to(OUT)): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in sorted(OUT.rglob('*')) if p.is_file()}, indent=2, sort_keys=True) + '\n')
fixture = OUT / 'lifecycle-fixture'
rc, log = run('fixture-build', ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-std=c11', '-Wall', '-Wextra',
    '-Werror', '-O2', '-I', native, fixture_source, '-lsandbox', '-o', fixture])
assert rc == 0, log
rc, log = run('fixture-warm', [fixture], timeout=30)
assert rc == 90, (rc, log)
worker = package / 'Sources/PWRunnerCore/CWorker.swift'
api = package / 'Sources/PWRunnerCore/PWRunnerAttemptEvidence.swift'
fixed_worker, fixed_api = worker.read_text(), api.read_text()
gate = '        if completed != 1 {\n'
absence = '        exec_observation = try container.decodeIfPresent(PWExecObservation.self, forKey: .exec_observation)\n'
assert fixed_worker.count(gate) == 1 and fixed_api.count(absence) == 1, 'mutation anchors changed'
invented = '''        exec_observation = try container.decodeIfPresent(PWExecObservation.self, forKey: .exec_observation)
            ?? (requested_kind == "exec" ? PWExecObservation(collection: PWExecCollectionObservation(stop_reason: "leader_exit_and_eof",
                leader_exit_observed: true, stdout: PWExecStreamObservation(eof: true), stderr: PWExecStreamObservation(eof: true)),
                cleanup: PWExecCleanupObservation(state: "not_requested"),
                reap: PWExecReapObservation(stop_reason: "reaped", last_wait: PWExecWaitObservation(rc: 4242, status: 0))) : nil)
'''
environment = dict(os.environ, PW_LIFECYCLE_WORKER_FIXTURE=str(fixture))
results = []
try:
    for variant in ('baseline', 'decode_unpublished', 'invent_absent_metadata'):
        worker.write_text(fixed_worker.replace(gate, '        if false { // deliberate publication bypass\n', 1)
                          if variant == 'decode_unpublished' else fixed_worker)
        api.write_text(fixed_api.replace(absence, invented, 1) if variant == 'invent_absent_metadata' else fixed_api)
        for name, source in [('CWorker', worker), ('PWRunnerAttemptEvidence', api)]:
            shutil.copy2(source, OUT / (variant + '-' + name + '.swift'))
        rc, log = run(variant, [*SWIFT, 'run', '--package-path', package, '--scratch-path', scratch, 'PWRunnerCoreTests'], env=environment)
        failures = [line.strip() for line in log.splitlines() if line.strip().startswith('FAIL ')]
        assert 'SKIP' not in log, log
        if variant == 'baseline':
            assert rc == 0 and '3/3 tests passed' in log and not failures, log
        elif variant == 'decode_unpublished':
            assert rc == 1 and '2/3 tests passed' in log and len(failures) == 1, log
            assert 'C slot completion gates payload and malformed publication degrades: expected nil, got PWExecObservation' in failures[0], log
        else:
            assert rc == 1, log
            assert any('independent native combinations retain cleanup separate from leader status:' in line
                       and 'absence cannot become not_requested' in line for line in failures), log
        results.append(dict(variant=variant, exit_code=rc, expected_rejections=failures,
            worker_sha256=hashlib.sha256(worker.read_bytes()).hexdigest(), api_sha256=hashlib.sha256(api.read_bytes()).hexdigest()))
        (OUT / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
finally:
    worker.write_text(fixed_worker)
    api.write_text(fixed_api)
print(json.dumps(results, indent=2))
record_build(package, OUT, scratch, "PWRunnerCoreTests", swift_command=SWIFT)
