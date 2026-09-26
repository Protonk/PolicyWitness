"""Required barrier controls; only disposable source and signed app copies mutate."""
import json
from pathlib import Path
import plistlib
import re
import secrets
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests/suites/witness_contract'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/caller_auth'))
from check_ordering import held_effects, save
from bundle import command, cleanup_processes
from artifact import digest, inventory, inspect, MANIFEST

SERVICE = Path('Contents/XPCServices/PWRunner.xpc')
WORKER = SERVICE / 'Contents/MacOS/pw-probe-runner'
HOST = SERVICE / 'Contents/MacOS/PWRunner'


def replace_once(source, old, new):
    assert source.count(old) == 1, f'mutation anchor changed: {old!r}'
    return source.replace(old, new, 1)


def worker_source(source):
    # Preserve acknowledgement and all ordinary attempts; only bypass the wait.
    return replace_once(source, '    wait_for_proceed(hdr, evidence, args.proceed_wait_ms);',
        '    (void)wait_for_proceed; /* required negative control: bypass wait */\n'
        '    atomic_store_explicit(&hdr->proceed_observed, 1u, memory_order_release);')


def host_source(source):
    release = '                storeRelease(rawBase, offset: PWShmLayout.proceedOffset, 1)\n                proceedSet = true\n'
    source = replace_once(source, release, '')
    return replace_once(source, '                if let hook = postApplied { hook(pid) }',
                        release + '                if let hook = postApplied { hook(pid) }')


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
        '/usr/bin/xcrun', 'swift', 'run', '--package-path', package, 'PWRunnerCoreTests'], timeout=180, check=False)
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
    result = command(out / 'harness-oracle', ['/usr/bin/python3',
        ROOT / 'tests/suites/runner_c_worker_harness/check_proceed.py', out / 'harness/stdout'], check=False)
    assert value['applied'] and value['apply_rc'] == 0 and value['done'] and value['exit_code'] == 0, value
    assert all(s['completed'] and s['rc'] == 0 for s in value['slots']), value
    if expected:
        assert result['returncode'] != 0 and (value['early_completion'] or value['early_attempt']), value
    else:
        assert result['returncode'] == 0, value
    return dict(rejected=expected, early_completion=value['early_completion'], early_attempt=value['early_attempt'])


def build_host(package, work, out):
    objects = []
    for name in ('PWSandboxCheckShim', 'PWCWorkerShim'):
        obj = work / (name + '.o'); objects.append(obj)
        command(out / ('compile-' + name), ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-c',
            package / 'Sources' / name / (name + '.c'), '-o', obj])
    # Follow build.sh's production source inventory, refusing silent divergence.
    sources = re.findall(r'^XPC_RUNNER_[A-Z_]+_FILE="\$\{XPC_ROOT\}/([^"\n]+\.swift)"',
                         (ROOT / 'build.sh').read_text(), re.M)
    assert set(sources) == {str(p.relative_to(package)) for p in (package / 'Sources/PWRunnerCore').glob('*.swift')}, sources
    host = work / 'PWRunner'
    command(out / 'compile-host', ['/usr/bin/xcrun', '--sdk', 'macosx', 'swiftc', '-Onone', '-g',
        '-module-cache-path', work / 'module-cache', '-o', host,
        *[package / p for p in sources], ROOT / 'runner/Services/PWRunner/main.swift', *objects], timeout=180)
    return host


def signed_copy(source, work, out, identity, worker, host=None):
    app = work / out.name / 'PolicyWitness.app'
    command(out / 'copy', ['/usr/bin/ditto', source, app])
    shutil.copy2(worker, app / WORKER)
    if host: shutil.copy2(host, app / HOST)
    app_id = 'com.policywitness.test.order.a' + secrets.token_hex(10)
    service_id = 'com.policywitness.test.order.s' + secrets.token_hex(10)
    for bundle, identifier in ((app, app_id), (app / SERVICE, service_id)):
        plist = bundle / 'Contents/Info.plist'; value = plistlib.loads(plist.read_bytes())
        value['CFBundleIdentifier'] = identifier; plist.write_bytes(plistlib.dumps(value))
    command(out / 'sign-worker', ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp', '-s', identity, app / WORKER], timeout=90)
    command(out / 'sign-service', ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp',
        '--entitlements', ROOT / 'runner/Services/PWRunner/Entitlements.plist', '-s', identity, app / SERVICE], timeout=90)
    command(out / 'evidence', ['/usr/bin/python3', ROOT / 'tests/build-evidence.py', '--app-bundle', app,
        '--app-entitlements', ROOT / 'PolicyWitness.entitlements'], timeout=120)
    command(out / 'sign-app', ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp',
        '--entitlements', ROOT / 'PolicyWitness.entitlements', '-s', identity, app], timeout=90)
    report = inspect(app); save(out / 'artifact.json', report)
    assert report['ok'], report
    save(out / 'hashes.json', dict(worker=digest(app / WORKER), host=digest(app / HOST), manifest=digest(app / MANIFEST)))
    return app


def cli_control(app, out, bridge, helper, expected):
    before = inventory(app)
    try:
        held_effects(app / 'Contents/MacOS/policy-witness', out / 'cli', bridge, helper)
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
            host = build_host(package, work, base)
            candidate = signed_copy(app, work, base, identity, worker, host)
            baseline['cli'] = cli_control(candidate, base, out / 'bridge', out / 'helper', False)
            summaries.append(baseline); save(out / 'mutations.json', summaries)
            mutant = out / 'worker_bypass'; mutant.mkdir()
            bad_worker = compile_worker(mutant, worker_source(c_source))
            result = dict(variant='worker_bypass', harness=harness_control(out / 'harness', bad_worker, mutant, True))
            candidate = signed_copy(app, work, mutant, identity, bad_worker)
            result['cli'] = cli_control(candidate, mutant, out / 'bridge', out / 'helper', True)
            summaries.append(result); save(out / 'mutations.json', summaries)
            mutant = out / 'host_bypass'; mutant.mkdir()
            patched = host_source(swift_source)
            (mutant / 'CWorker.swift').write_text(patched)
            (package / 'Sources/PWRunnerCore/CWorker.swift').write_text(patched)
            result = dict(variant='host_bypass', driver=driver(package, mutant, out / 'lifecycle', True))
            host = build_host(package, work, mutant)
            candidate = signed_copy(app, work, mutant, identity, worker, host)
            result['cli'] = cli_control(candidate, mutant, out / 'bridge', out / 'helper', True)
            summaries.append(result); save(out / 'mutations.json', summaries)
        finally:
            cleanup_processes(work, out)
            assert inventory(app) == before, 'selected production app changed'
    print(json.dumps(summaries, indent=2))


if __name__ == '__main__': main()
