"""Refute reusable payload/answer cells and premature erasure in disposable sources.

Synthetic authority bytes establish channel and publication ownership only.
No sandbox extension API is called; no shipped app is changed.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
from build_receipt import record_build


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def command(out, label, argv, expected=0, marker=None):
    receipt = dict(argv=argv, stage='prepared')
    path = out / (label + '.command.json')
    save(path, receipt)
    with (out / (label + '.log')).open('w') as stream:
        child = subprocess.Popen(argv, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        receipt.update(stage='running', pid=child.pid)
        save(path, receipt)
        timed_out = False
        try:
            child.wait(timeout=240)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=10)
    receipt.update(stage='exited', returncode=child.returncode, timed_out=timed_out)
    save(path, receipt)
    assert not timed_out, ('fixture timeout is not mutation detection', path)
    assert child.returncode == expected, (label, child.returncode, expected)
    output = (out / (label + '.log')).read_text()
    if marker:
        assert marker in output, ('designated observation missing', label, marker)
    return dict(returncode=child.returncode, marker=marker)


def mutate(path, old, new, out):
    before = path.read_text()
    assert before.count(old) == 1, ('mutation anchor changed; review required', str(path), old)
    prior = digest(path)
    path.write_text(before.replace(old, new))
    save(out / 'mutation.json', dict(path=str(path), before=old, after=new,
                                    original_sha256=prior, mutated_sha256=digest(path)))


def swift_variant(out, scratch, alias):
    out.mkdir(parents=True)
    package = out / 'runner'
    shutil.copytree(ROOT / 'runner/Sources', package / 'Sources')
    shutil.copyfile(ROOT / 'runner/Package.swift', package / 'Package.swift')
    tests = package / 'Tests/PWRunnerCoreTests'
    tests.mkdir(parents=True)
    for name in ('TestKit.swift', 'ActorAuthorityTests.swift'):
        shutil.copyfile(ROOT / 'runner/Tests/PWRunnerCoreTests' / name, tests / name)
    (tests / 'main.swift').write_text('''import Darwin
import Foundation
@testable import PWRunnerCore
do {
    try runHandoffCopyBoundaryControl()
    print("HANDOFF_COPY_ACCEPTED")
} catch let failure as TestFailure {
    print("CONTROL_REJECTED: " + failure.message)
    exit(73)
} catch {
    print("UNEXPECTED_FAILURE: \\(error)")
    exit(74)
}
''')
    if alias:
        mutate(package / 'Sources/PWRunnerCore/AuthorityCustody.swift',
               'return base?.advanced(by: PWAuthorityLayout.slotsOffset + index * PWAuthorityLayout.slotBytes)',
               'return base?.advanced(by: PWAuthorityLayout.slotsOffset + 0 * PWAuthorityLayout.slotBytes)', out)
    command(out, 'build', ['swift', 'build', '--package-path', str(package), '--scratch-path', str(scratch),
                           '--product', 'PWRunnerCoreTests'])
    product = record_build(package, out, scratch, 'PWRunnerCoreTests', swift_command=['swift'])
    return command(out, 'run', [str(product)], expected=73 if alias else 0,
                   marker='CONTROL_REJECTED: handoff copy preserves first issue bytes' if alias else 'HANDOFF_COPY_ACCEPTED')


def gate_variant(out,scratch,removed):
    out.mkdir(parents=True)
    package=out/'runner'
    shutil.copytree(ROOT/'runner/Sources',package/'Sources')
    shutil.copyfile(ROOT/'runner/Package.swift',package/'Package.swift')
    tests=package/'Tests/PWRunnerCoreTests';tests.mkdir(parents=True)
    for name in ('TestKit.swift','ActorSchedulerTests.swift'):
        shutil.copyfile(ROOT/'runner/Tests/PWRunnerCoreTests'/name,tests/name)
    (tests/'main.swift').write_text(r'''import Darwin
import Foundation
@testable import PWRunnerCore
do {
    try runTerminationGateBoundaryControl()
    print("TERMINATION_GATE_ACCEPTED")
} catch let failure as TestFailure {
    print("CONTROL_REJECTED: " + failure.message)
    exit(73)
} catch { print("UNEXPECTED_FAILURE: \(error)"); exit(74) }
''')
    if removed:
        mutate(package/'Sources/PWRunnerCore/ActorScheduler.swift',
            '            if let dependency=entry.terminationDependency {\n                var gate=observeTermination',
            '            if let dependency=entry.terminationDependency, false {\n                var gate=observeTermination',out)
    command(out,'build',['swift','build','--package-path',str(package),'--scratch-path',str(scratch),'--product','PWRunnerCoreTests'])
    product=record_build(package,out,scratch,'PWRunnerCoreTests',swift_command=['swift'])
    # Copied #filePath is not the repository equipment root. Bind the exact
    # existing app explicitly and retain its identity in the fixture receipt.
    app=Path(os.environ.get('PW_APP_DIR',str(ROOT/'dist/PolicyWitness.app'))).resolve()
    worker=app/'Contents/XPCServices/PWRunner.xpc/Contents/MacOS/pw-probe-runner'
    save(out/'equipment.json',dict(path=str(worker),sha256=digest(worker)))
    return command(out,'run',['/usr/bin/env','PW_APP_DIR='+str(app),str(product)],expected=73 if removed else 0,
        marker='CONTROL_REJECTED: termination gate precedes dependent collection' if removed else 'TERMINATION_GATE_ACCEPTED')


def c_variant(out, scratch, variant):
    out.mkdir(parents=True)
    scratch.mkdir(parents=True)
    worker = out / 'root/controller/tools/pw_probe_runner'
    worker.mkdir(parents=True)
    for path in (ROOT / 'controller/tools/pw_probe_runner').glob('*.h'):
        shutil.copyfile(path, worker / path.name)
    shutil.copyfile(ROOT / 'controller/tools/pw_probe_runner/pw_probe_runner.c', worker / 'pw_probe_runner.c')
    fixture = out / 'root/tests/fixtures/extension_controls/authority_binding.c'
    fixture.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / 'tests/fixtures/extension_controls/authority_binding.c', fixture)
    marker = None
    if variant == 'shared_answer':
        mutate(worker / 'pw_probe_runner.c',
               'wait_exchange(&cell->acknowledged, timing, index, &status)',
               'wait_exchange(&authority->transfers[0].acknowledged, timing, index, &status)', out)
        marker = 'CONTROL_REJECTED: late first answer cannot complete second transfer'
    elif variant == 'early_erase':
        mutate(worker / 'pw_probe_runner.c',
               '    slot->ext_custody_status = status;\n',
               '    slot->ext_custody_status = status;\n    pw_extension_erase(out->token, PW_EXTENSION_TOKEN_BYTES);\n', out)
        marker = 'CONTROL_REJECTED: custody timeout preserves host-owned publication'
    product = scratch / 'authority-binding'
    command(out, 'build', ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-Wall', '-Wextra', '-Werror',
                            '-Wno-deprecated-declarations', '-O2', '-std=c11', str(fixture), '-lsandbox', '-o', str(product)])
    save(out / 'build-receipt.json', dict(product_path=str(product), product_sha256=digest(product)))
    return command(out, 'run', [str(product)], expected=73 if marker else 0,
                   marker=marker or 'outbound publication remains immutable across timeout, next issue and worker cleanup')


def main(out, scratch):
    out.mkdir(parents=True)
    inputs = [ROOT / 'runner/Package.swift', ROOT / 'runner/Tests/PWRunnerCoreTests/TestKit.swift',
              ROOT / 'runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift',
              ROOT / 'runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift',
              ROOT / 'tests/fixtures/extension_controls/authority_binding.c', Path(__file__), Path(__file__).with_suffix('.sh'),
              ROOT / 'tests/lib/build_receipt.py']
    inputs += [p for p in (ROOT / 'runner/Sources').rglob('*') if p.is_file()]
    inputs += list((ROOT / 'controller/tools/pw_probe_runner').glob('*.h'))
    inputs += [ROOT / 'controller/tools/pw_probe_runner/pw_probe_runner.c']
    save(out / 'source-manifest.json', {str(p.relative_to(ROOT)): digest(p) for p in inputs})
    results = {}
    for alias in (False, True):
        name = 'swift_alias' if alias else 'swift_baseline'
        results[name] = swift_variant(out / name, scratch / name, alias)
        save(out / 'results.json', results)
    for removed in (False,True):
        name='gate_removed' if removed else 'gate_baseline'
        results[name]=gate_variant(out/name,scratch/name,removed)
        save(out/'results.json',results)
    for variant in ('baseline', 'shared_answer', 'early_erase'):
        name = 'c_' + variant
        results[name] = c_variant(out / name, scratch / name, variant)
        save(out / 'results.json', results)
    print('Three baselines passed; outbound alias, removed termination gate, shared answer and early erasure failed designated observations.')


if __name__ == '__main__':
    assert __debug__, 'assertions required'
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
