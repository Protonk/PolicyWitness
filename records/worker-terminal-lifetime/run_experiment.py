#!/usr/bin/env python3
"""Investigation equipment, outside the registered test battery; run under checkout_lock.sh."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / 'tests/lib'))
import checkout_lock

STAMP = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
OUT = HERE / ('experiment-' + STAMP)
OUT.mkdir()
BUILD = Path(tempfile.mkdtemp(prefix='pw-terminal-lifetime-', dir='/private/tmp'))
PASS_FDS = checkout_lock.inherited_fds()
if not PASS_FDS:
    raise SystemExit('run via tests/lib/checkout_lock.sh')
commands = []

def run(args, label, timeout=180):
    command = [str(a) for a in args]
    commands.append({'label': label, 'argv': command})
    (OUT / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
    with (OUT / (label + '.stdout')).open('wb') as stdout, (OUT / (label + '.stderr')).open('wb') as stderr:
        result = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr,
                                pass_fds=PASS_FDS, timeout=timeout)
    print(f'{label}: rc={result.returncode}', flush=True)
    if result.returncode:
        print((OUT / (label + '.stderr')).read_text(), file=sys.stderr)
        raise SystemExit(result.returncode)

sources = sorted((ROOT / 'runner/Sources').rglob('*'))
sources += sorted((ROOT / 'controller/tools/pw_probe_runner').glob('*'))
sources += [HERE / 'experiment-driver.swift', HERE / 'experiment-fixture.c', Path(__file__).resolve()]
hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sources if p.is_file() and p.suffix in {'.c', '.h', '.swift', '.py'}}
metadata = {'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'build_directory': str(BUILD), 'source_sha256': hashes,
            'scope': 'ABI fixture and copied Swift host; no sandbox validation or signed-app acceptance'}
(OUT / 'source.json').write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n')
print(f'output: {OUT}\nbuild: {BUILD}', flush=True)
run(['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2',
     '-I', ROOT / 'controller/tools/pw_probe_runner', HERE / 'experiment-fixture.c', '-o', BUILD / 'fixture'], 'fixture-build')
manifest = '''// swift-tools-version: 5.10
import PackageDescription
let package = Package(name: "TerminalInvestigation", platforms: [.macOS("26.0")], targets: [
 .target(name: "PWCWorkerShim"),
 .target(name: "PWRunnerCore", dependencies: ["PWCWorkerShim"], swiftSettings: [.unsafeFlags(["-enable-testing"])]),
 .executableTarget(name: "TerminalInvestigation", dependencies: ["PWRunnerCore"])
])
'''
for variant in ('baseline', 'candidate'):
    package = BUILD / variant
    shutil.copytree(ROOT / 'runner/Sources/PWRunnerCore', package / 'Sources/PWRunnerCore')
    shutil.copytree(ROOT / 'runner/Sources/PWCWorkerShim', package / 'Sources/PWCWorkerShim')
    (package / 'Sources/TerminalInvestigation').mkdir()
    shutil.copyfile(HERE / 'experiment-driver.swift', package / 'Sources/TerminalInvestigation/main.swift')
    (package / 'Package.swift').write_text(manifest)
    if variant == 'candidate':
        driver = package / 'Sources/PWRunnerCore/CWorker.swift'
        original = driver.read_text()
        marker = '    // Collection basis: whether every read below follows a successful reap. A\n'
        assert original.count(marker) == 1
        changed = original.replace(marker, '    if process.status != nil { observeAcknowledgement() }\n' + marker)
        driver.write_text(changed)
        (OUT / 'candidate-delta.txt').write_text('CWorker.swift before collection-basis snapshot:\n+    if process.status != nil { observeAcknowledgement() }\n')
        metadata['candidate_CWorker_sha256'] = hashlib.sha256(driver.read_bytes()).hexdigest()
    run(['/usr/bin/xcrun', 'swift', 'build', '--package-path', package, '--disable-sandbox',
         '--product', 'TerminalInvestigation'], variant + '-build')
    run([package / '.build/debug/TerminalInvestigation', BUILD / 'fixture', variant, OUT], variant + '-run', timeout=20)
    shutil.copyfile(OUT / (variant + '-run.stdout'), OUT / (variant + '.jsonl'))
    metadata[variant + '_driver_sha256'] = hashlib.sha256((package / '.build/debug/TerminalInvestigation').read_bytes()).hexdigest()
metadata['fixture_sha256'] = hashlib.sha256((BUILD / 'fixture').read_bytes()).hexdigest()
(OUT / 'source.json').write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n')
(OUT / 'result.json').write_text(json.dumps({'result': 'passed', 'cases': 4, 'catalog_case': False}, indent=2) + '\n')
print(f'PASS: 4 bounded controls; evidence {OUT}', flush=True)
