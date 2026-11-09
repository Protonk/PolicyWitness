"""Disposable, source-receipted host instrumentation; signed workers stay unchanged."""
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import secrets
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/caller_auth'))
import build_context
from artifact import inventory, digest, inspect
from bundle import command, save

SERVICE = Path('Contents/XPCServices/PWRunner.xpc')
HOST = SERVICE / 'Contents/MacOS/PWRunner'
EQUIPMENT = SERVICE / 'Contents/Resources/worker-equipment.json'

class ActorHostFixture:
    def __init__(self, source_app, out, identity):
        self.source_app = Path(source_app).resolve(); self.out = Path(out).resolve()
        self.identity = identity
        self.snapshots = self.out / 'snapshots'
        self.app = self.out / 'PolicyWitness.app'
        self.pw = self.app / 'Contents/MacOS/policy-witness'

    def build(self):
        self.out.mkdir(parents=True, exist_ok=False); self.snapshots.mkdir()
        original = inventory(self.source_app); save(self.out / 'source-inventory.json', original)
        package = self.out / 'runner'; shutil.copytree(ROOT / 'runner', package, ignore=shutil.ignore_patterns('.build', '.swiftpm'))
        scratch = Path(os.environ['PW_TEST_SCRATCH']) / ('footprint-host-' + secrets.token_hex(8)); scratch.mkdir(parents=True)
        path = package / 'Sources/PWRunnerCore/ActorScheduler.swift'
        source = path.read_text(); anchor = '                collect(entry.phaseIndex, entry.actorIndex, session.pid)'
        assert source.count(anchor) == 1, 'snapshot anchor changed'
        patched = source.replace(anchor, '                footprintSnapshot(self, phase: entry.phaseIndex, actor: entry.actorIndex)\n' + anchor)
        path.write_text(patched)
        hook = package / 'Sources/PWRunnerCore/FootprintSnapshot.swift'
        hook.write_text('let FOOTPRINT_SNAPSHOT_DIRECTORY = ' + json.dumps(str(self.snapshots)) + '\n' + (Path(__file__).parent / 'actor_snapshot.swift').read_text())
        save(self.out / 'source-patch.json', dict(scope='host-only pre-collection metadata; unchanged signed workers',
            source_sha256=digest(ROOT / 'runner/Sources/PWRunnerCore/ActorScheduler.swift'),
            patched_sha256=digest(path), hook_sha256=digest(hook), original=source, patched=patched))
        spec = importlib.util.spec_from_file_location('footprint_mutation_build', ROOT / 'tests/suites/witness_contract/opt_in/mutations.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        sources, entry = module.meson_host_sources(self.out / 'source-list')
        obj = scratch / 'shim.o'
        command(self.out / 'compile-shim', ['/usr/bin/xcrun','clang','-arch','arm64','-mmacosx-version-min=26.0','-c',package / 'Sources/PWCWorkerShim/PWCWorkerShim.c','-o',obj])
        host = scratch / 'PWRunner'
        context = build_context.write_swift_context(self.out / 'PWBuildContext.swift', build_context.candidate_contract(self.source_app))
        command(self.out / 'compile-host', ['/usr/bin/xcrun','swiftc','-j','2','-Onone','-g','-target','arm64-apple-macosx26.0','-module-cache-path',scratch / 'module-cache','-o',host,
            '-D','PW_PACKAGED_BUILD',context,*[package / p for p in sources],hook,package / entry,obj], timeout=180)
        command(self.out / 'copy', ['/usr/bin/ditto',self.source_app,self.app])
        unchanged = [SERVICE / 'Contents/MacOS' / name for name in ('pw-probe-runner','pw-probe-runner-unentitled','sb_api_validator')] + [EQUIPMENT]
        hashes = {str(p): digest(self.app / p) for p in unchanged}
        shutil.copy2(host,self.app / HOST)
        for bundle, prefix in ((self.app,'a'),(self.app / SERVICE,'s')):
            p=bundle / 'Contents/Info.plist'; value=plistlib.loads(p.read_bytes())
            value['CFBundleIdentifier']='com.policywitness.test.footprint.'+prefix+secrets.token_hex(10)
            p.write_bytes(plistlib.dumps(value))
        command(self.out / 'sign-service',['/usr/bin/codesign','--force','--options','runtime','--timestamp','--entitlements',ROOT / 'runner/Services/PWRunner/Entitlements.plist','-s',self.identity,self.app / SERVICE],timeout=90)
        command(self.out / 'evidence',[sys.executable,'-B','-S',ROOT / 'tests/build-evidence.py','--app-bundle',self.app,'--app-entitlements',ROOT / 'PolicyWitness.entitlements','--substitution-of',self.source_app,'--identity',self.identity],timeout=120)
        command(self.out / 'sign-app',['/usr/bin/codesign','--force','--options','runtime','--timestamp','--entitlements',ROOT / 'PolicyWitness.entitlements','-s',self.identity,self.app],timeout=90)
        assert {str(p):digest(self.app / p) for p in unchanged} == hashes
        assert inventory(self.source_app) == original, 'source app changed'
        save(self.out / 'unchanged-worker-inventory.json',hashes)
        report=inspect(self.app); save(self.out / 'artifact.json',report); assert report['ok'],report
        return self

    def snapshot(self, host_pid, phase):
        return json.loads((self.snapshots / f'{host_pid}-{phase}.json').read_text())
