"""Required barrier controls; only disposable source and signed app copies mutate.

These deliberate implementation faults retain the baseline generated identity
to reach the ordering oracle beyond the mismatch guard. A normal build refuses
these edits until the identity is regenerated; source_drift separately proves
both edits change the identity.
"""
import json
from pathlib import Path
import plistlib
import secrets
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests/suites/witness_contract'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/caller_auth'))
sys.path.insert(0, str(ROOT / 'tests/lib'))
import native_sources
from check_ordering import held_effects, save
from bundle import command, cleanup_processes
import build_context
from artifact import digest, inventory, inspect, MANIFEST
from contract import WORKER_IDENTITY

SERVICE = Path('Contents/XPCServices/PWRunner.xpc')
WORKER = SERVICE / 'Contents/MacOS/pw-probe-runner'
UNENTITLED = SERVICE / 'Contents/MacOS/pw-probe-runner-unentitled'
EQUIPMENT = SERVICE / 'Contents/Resources/worker-equipment.json'
HOST = SERVICE / 'Contents/MacOS/PWRunner'


def replace_once(source, old, new):
    assert source.count(old) == 1, f'mutation anchor changed: {old!r}'
    return source.replace(old, new, 1)


def worker_source(source, gate):
    # Bypass each actual wait while retaining phase publications and attempts.
    return replace_once(source, '        wait_for_proceed(hdr, evidence, phase_index, &timing);',
        '        (void)wait_for_proceed; /* deliberate bypass */\n'
        '        atomic_store_explicit(&phase->arrived, 1u, memory_order_release);\n'
        f'        while (access({json.dumps(str(gate))}, F_OK) != 0) usleep(1000); /* test collection gate */\n'
        '        atomic_store_explicit(&phase->acknowledged, 1u, memory_order_release);\n'
        '        atomic_store_explicit(&hdr->proceed_observed, phase_index + 1u, memory_order_release);')


def host_source(source):
    release = '                    session.releaseVisit(index)\n'
    source = replace_once(source, release, '')
    return replace_once(source, '                if let hook = phaseBoundary { hook(pid, index) }',
                        release + '                if let hook = phaseBoundary { hook(pid, index) }')


def compile_worker(out, body):
    out.mkdir(parents=True, exist_ok=True)
    source = out / 'worker.c'; source.write_text(body)
    worker = out / 'worker'
    command(out / 'compile', ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-Wall', '-Wextra',
        '-Werror', '-O2', '-std=c11', '-I', ROOT / 'controller/tools/pw_probe_runner',
        source, '-lsandbox', '-o', worker], timeout=60)
    return worker


def driver(package, out, lifecycle, expected):
    meta = command(out / 'driver', ['/usr/bin/env', 'PW_LIFECYCLE_WORKER_FIXTURE=' + str(lifecycle),
        '/usr/bin/xcrun', 'swift', 'run', '--jobs', '2', '--package-path', package, 'PWRunnerCoreTests'], timeout=180, check=False)
    log = (out / 'driver/stdout').read_text() + (out / 'driver/stderr').read_text()
    assert 'SKIP' not in log, log
    if expected:
        assert meta['returncode'] == 1 and 'early worker publication while hook held' in log, log
        assert 'ack\nattempt\n' in log, 'missing independent lifecycle receipt in driver rejection: ' + log
    else:
        assert meta['returncode'] == 0 and '1/1 tests passed' in log, log
    return dict(rejected=expected, log=str(out / 'driver'))


def harness_control(harness, worker, out, expected):
    command(out / 'harness', [harness, worker, 'proceed_delayed_observed_quiescence'])
    value = json.loads((out / 'harness/stdout').read_text())
    result = command(out / 'harness-oracle', [sys.executable, '-B', '-S',
        ROOT / 'tests/suites/runner_c_worker_harness/check_proceed.py', out / 'harness/stdout'], check=False)
    assert value['applied'] and value['apply_rc'] == 0 and value['done'] and value['exit_code'] == 0, value
    assert all(s['completed'] and s['rc'] == 0 for s in value['slots']), value
    if expected:
        assert result['returncode'] != 0 and (value['early_completion'] or value['early_attempt']), value
    else:
        assert result['returncode'] == 0, value
    return dict(rejected=expected, early_completion=value['early_completion'], early_attempt=value['early_attempt'])


def meson_host_sources(out):
    """The production host source list, read from meson.build in file mode.

    The shared reader lists the PWRunner target without a build directory and
    regardless of the xpc option, refuses a duplicated declaration, and the
    whole manifest must agree with the tree before any host is compiled. The
    core sources are returned runner-relative, in declaration order; the
    service entry point is checked and returned separately."""
    command(out / 'introspect', ['meson', 'introspect', ROOT / 'meson.build', '--targets'], timeout=60)
    targets, problems = native_sources.parse_targets((out / 'introspect/stdout').read_text(), ROOT, 'meson.build')
    problems += native_sources.problems(targets, native_sources.expected(ROOT), 'meson.build')
    assert not problems, 'meson.build disagrees with the tree:\n' + '\n'.join(problems)
    sources = [s[len('runner/'):] for s in targets['PWRunner']]
    core = [s for s in sources if s.startswith('Sources/PWRunnerCore/') and s.endswith('.swift')]
    entry = [s for s in sources if s not in core]
    assert entry == ['Services/PWRunner/main.swift'], sources
    return core, entry[0]


def build_host(package, work, out, app):
    objects = []
    for name in ('PWCWorkerShim',):
        obj = work / (name + '.o'); objects.append(obj)
        command(out / ('compile-' + name), ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-c',
            package / 'Sources' / name / (name + '.c'), '-o', obj])
    # Follow the production source inventory; the reader has already refused divergence from the tree.
    sources, entry = meson_host_sources(out)
    host = work / 'PWRunner'
    context = build_context.write_swift_context(out / 'PWBuildContext.swift', build_context.candidate_contract(app))
    command(out / 'compile-host', ['/usr/bin/xcrun', '--sdk', 'macosx', 'swiftc', '-j', '2', '-Onone', '-g',
        '-module-cache-path', work / 'module-cache', '-o', host,
        '-D', 'PW_PACKAGED_BUILD', context, *[package / p for p in sources], package / entry, *objects], timeout=180)
    return host


def signed_copy(source, work, out, identity, worker, host=None):
    app = work / out.name / 'PolicyWitness.app'
    command(out / 'copy', ['/usr/bin/ditto', source, app])
    # One controlled implementation supplies both required packaged roles.
    # Keep its actual pre-sign hash; never reuse the production worker hash.
    common_hash = digest(worker)
    original_equipment = json.loads((app / EQUIPMENT).read_bytes())
    assert original_equipment['worker_identity'] == WORKER_IDENTITY
    save(out / 'source-equipment.json', original_equipment)
    command(out / 'common-worker-identity', [worker, '--version'])
    reported = (out / 'common-worker-identity/stdout').read_text().split()
    assert 'abi_identity=' + WORKER_IDENTITY in reported, reported
    for relative in (WORKER, UNENTITLED):
        shutil.copy2(worker, app / relative)
        assert digest(app / relative) == common_hash
    if host: shutil.copy2(host, app / HOST)
    assembly = dict(variant=out.name, common_input_sha256=common_hash,
                    common_source_sha256=digest(worker.parent / 'worker.c'),
                    declared_worker_identity=WORKER_IDENTITY,
                    generated_identity_regenerated_for_mutation=False,
                    identity_is_mutated_source_digest=False,
                    provenance_kind='substitution',
                    note='Controlled binaries retain the baseline ABI identity to reach the ordering oracle; '
                         'it does not describe the mutated source. Actual bytes and substitution provenance remain separate.',
                    stages=['copy_common_worker_to_both_roles'])
    if (out / 'CWorker.swift').exists():
        assembly['mutated_host_source_sha256'] = digest(out / 'CWorker.swift')
    save(out / 'equipment-assembly.json', assembly)
    app_id = 'com.policywitness.test.order.a' + secrets.token_hex(10)
    service_id = 'com.policywitness.test.order.s' + secrets.token_hex(10)
    for bundle, identifier in ((app, app_id), (app / SERVICE, service_id)):
        plist = bundle / 'Contents/Info.plist'; value = plistlib.loads(plist.read_bytes())
        value['CFBundleIdentifier'] = identifier; plist.write_bytes(plistlib.dumps(value))
    selected_entitlements = ROOT / 'runner/Services/PWRunner/Entitlements.plist'
    assert plistlib.loads(selected_entitlements.read_bytes()) == {}, 'this ordering fixture requires empty worker entitlements'
    command(out / 'sign-worker', ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp',
        '--entitlements', selected_entitlements, '-s', identity, app / WORKER], timeout=90)
    assembly['stages'].append('sign_selected'); save(out / 'equipment-assembly.json', assembly)
    command(out / 'sign-unentitled-worker', ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp',
        '-s', identity, app / UNENTITLED], timeout=90)
    assembly['stages'].append('sign_unentitled'); save(out / 'equipment-assembly.json', assembly)
    # The owning emitter reads actual hashes/signatures/plists after signing.
    # This publication precedes the service seal, just as normal assembly does.
    command(out / 'equipment', [sys.executable, '-B', '-S', ROOT / 'tests/build_equipment.py',
        '--bundle', app / SERVICE, '--unsigned-worker', worker, '--worker-identity', WORKER_IDENTITY], timeout=90)
    equipment_bytes = (app / EQUIPMENT).read_bytes()
    (out / 'worker-equipment.json').write_bytes(equipment_bytes)
    equipment = json.loads(equipment_bytes)
    assert equipment['unsigned_worker_sha256'] == common_hash and digest(worker) == common_hash
    assert equipment['worker_identity'] == WORKER_IDENTITY
    assert {row['role'] for row in equipment['workers']} == {'selected', 'unentitled'} and len(equipment['workers']) == 2
    for row in equipment['workers']:
        expected = WORKER if row['role'] == 'selected' else UNENTITLED
        assert app / SERVICE / row['relative_path'] == app / expected
        assert row['sha256'] == digest(app / expected)
        assert plistlib.loads(row['entitlements_xml'].encode()) == {}, row
    assembly['stages'].append('emit_inventory'); save(out / 'equipment-assembly.json', assembly)
    command(out / 'sign-service', ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp',
        '--entitlements', ROOT / 'runner/Services/PWRunner/Entitlements.plist', '-s', identity, app / SERVICE], timeout=90)
    assembly['stages'].append('seal_service'); save(out / 'equipment-assembly.json', assembly)
    assert (app / EQUIPMENT).read_bytes() == equipment_bytes, 'service sealing changed inventory bytes'
    command(out / 'evidence', [sys.executable, '-B', '-S', ROOT / 'tests/build-evidence.py', '--app-bundle', app,
        '--app-entitlements', ROOT / 'PolicyWitness.entitlements', '--substitution-of', source, '--identity', identity], timeout=120)
    command(out / 'sign-app', ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp',
        '--entitlements', ROOT / 'PolicyWitness.entitlements', '-s', identity, app], timeout=90)
    report = inspect(app); save(out / 'artifact.json', report)
    assert report['ok'], report
    assembly['stages'].append('substitution_evidence_and_app_seal')
    save(out / 'equipment-assembly.json', assembly)
    save(out / 'hashes.json', dict(common_worker=common_hash, worker=digest(app / WORKER),
        unentitled_worker=digest(app / UNENTITLED), equipment_inventory=digest(app / EQUIPMENT),
        host=digest(app / HOST), manifest=digest(app / MANIFEST)))
    return app


def cli_control(app, out, bridge, helper, expected, collection_started=None):
    before = inventory(app)
    try:
        held_effects(app / 'Contents/MacOS/policy-witness', out / 'cli', bridge, helper, collection_started)
    except AssertionError as error:
        assert expected and str(error) in ('early unlink while collection held', 'early exec connection while collection held'), str(error)
        observations = json.loads((out / 'cli/effects.json').read_text())
        assert any(not s['present'] for s in observations['held_samples']), observations
        assert any(s['exec_connected'] for s in observations['held_samples']), observations
        result = dict(rejected=True, reason=str(error))
    else:
        assert not expected, 'barrier bypass escaped external effect observer'
        result = dict(rejected=False)
    finally:
        assert inventory(app) == before, 'candidate app changed during execution'
    return result


def main():
    app, out, identity = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3]
    before = inventory(app)
    c_source = (ROOT / 'controller/tools/pw_probe_runner/pw_probe_runner.c').read_text()
    swift_source = (ROOT / 'runner/Sources/PWRunnerCore/CWorker.swift').read_text()
    summaries = []
    with tempfile.TemporaryDirectory(prefix='pw-order-mut-', dir='/private/tmp') as work_arg:
        work = Path(work_arg)
        try:
            package = work / 'runner'
            shutil.copytree(ROOT / 'runner', package, ignore=shutil.ignore_patterns('.build', '*.md'))
            shutil.copy2(Path(__file__).with_name('driver_main.swift'), package / 'Tests/PWRunnerCoreTests/main.swift')
            base = out / 'baseline'; base.mkdir()
            worker = compile_worker(base, c_source)
            baseline = dict(variant='baseline', driver=driver(package, base, out / 'lifecycle', False),
                            harness=harness_control(out / 'harness', worker, base, False))
            # Rebuild the unmodified service as the positive control for the host recipe.
            host = build_host(package, work, base, app)
            candidate = signed_copy(app, work, base, identity, worker, host)
            baseline['cli'] = cli_control(candidate, base, out / 'bridge', out / 'helper', False)
            summaries.append(baseline); save(out / 'mutations.json', summaries)
            mutant = out / 'worker_bypass'; mutant.mkdir()
            bypass_gate = work / 'worker-bypass-ready'
            bad_worker = compile_worker(mutant, worker_source(c_source, bypass_gate))
            bypass_gate.touch()
            result = dict(variant='worker_bypass', harness=harness_control(out / 'harness', bad_worker, mutant, True))
            bypass_gate.unlink()
            candidate = signed_copy(app, work, mutant, identity, bad_worker)
            result['cli'] = cli_control(candidate, mutant, out / 'bridge', out / 'helper', True, bypass_gate.touch)
            summaries.append(result); save(out / 'mutations.json', summaries)
            mutant = out / 'host_bypass'; mutant.mkdir()
            patched = host_source(swift_source)
            (mutant / 'CWorker.swift').write_text(patched)
            (package / 'Sources/PWRunnerCore/CWorker.swift').write_text(patched)
            result = dict(variant='host_bypass', driver=driver(package, mutant, out / 'lifecycle', True))
            host = build_host(package, work, mutant, app)
            candidate = signed_copy(app, work, mutant, identity, worker, host)
            result['cli'] = cli_control(candidate, mutant, out / 'bridge', out / 'helper', True)
            summaries.append(result); save(out / 'mutations.json', summaries)
        finally:
            cleanup_processes(work, out)
            assert inventory(app) == before, 'selected production app changed'
    print(json.dumps(summaries, indent=2))


if __name__ == '__main__': main()
