"""Two signed source variants, one request shape, independently observed file effects.

The append variant intentionally violates open_write's documented truncation.
Both variants add launch traces. Neither is a production-equivalence claim.
"""
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import build_context
from run_capture import RunCapture


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def fixture_digest(root):
    names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard',
                                     '--', 'tests/fixtures'], cwd=root).decode().split('\0')
    values = [(name, sha256((root / name).read_bytes()).hexdigest())
              for name in sorted(set(filter(None, names))) if (root / name).is_file()]
    return sha256(json.dumps(values, separators=(',', ':')).encode()).hexdigest()


def command(out, label, argv, *, cwd=ROOT, env=None, timeout=900):
    with (out / (label + '.stdout')).open('wb') as stdout, (out / (label + '.stderr')).open('wb') as stderr:
        result = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, stdout=stdout, stderr=stderr, timeout=timeout)
    save(out / (label + '.command.json'), dict(argv=list(map(str, argv)), cwd=str(cwd), returncode=result.returncode))
    assert result.returncode == 0, (label, result.returncode)


def main():
    out, identity = Path(sys.argv[1]).resolve(), sys.argv[2]
    staging = Path(tempfile.mkdtemp(prefix='pw-same-shape-', dir='/private/tmp'))
    ownership = dict(staging=str(staging), worktrees=[], complete=False)
    save(out / 'ownership.json', ownership)
    env = {key: value for key, value in os.environ.items() if not key.startswith('PW_CHECKOUT_LOCK_')}
    patch = subprocess.check_output(['git', 'diff', '--binary', 'HEAD'], cwd=ROOT)
    (out / 'candidate.patch').write_bytes(patch)
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    client_trace, worker_trace = staging / 'client-started', staging / 'worker-started'
    products = {}
    authored_fixtures = fixture_digest(ROOT)
    for mode in ('truncate', 'append'):
        case = out / mode; case.mkdir()
        checkout = staging / mode
        command(case, 'worktree-add', ['git', 'worktree', 'add', '--detach', checkout, 'HEAD'])
        ownership['worktrees'].append(str(checkout)); save(out / 'ownership.json', ownership)
        command(case, 'apply-candidate', ['git', 'apply', '--binary', out / 'candidate.patch'], cwd=checkout)
        for relative in filter(None, untracked):
            source, target = ROOT / relative, checkout / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            assert source.is_file() and not source.is_symlink(), relative
            shutil.copy2(source, target)
        if mode == 'truncate':
            package = checkout / 'runner/Package.swift'
            original_package = package.read_text()
            package.write_text(original_package.replace('    targets: [',
                '    targets: [\n        .executableTarget(name: "PWUnboundControls", dependencies: ["PWRunnerCore"], path: "Tests/Unbound"),', 1))
            fixture = checkout / 'runner/Tests/Unbound'; fixture.mkdir()
            main = fixture / 'main.swift'
            main.write_text('''import Foundation
@testable import PWRunnerCore
precondition(PWBuildContext.contract == "unbound")
do {
    _ = try JSONDecoder().decode(PWRunnerRunSpec.self, from: Data(#"{"contract":"unbound","runner":false}"#.utf8))
    fatalError("unbound request admitted")
} catch let failure as PWRunnerRequestFailure {
    precondition(failure.code == "unsupported_contract" && failure.expected_contract == "unbound")
}
print("plain SwiftPM context is unbound and refuses before descendant parsing")
''')
            shutil.copy2(main, case / 'Unbound.swift')
            command(case, 'unbound-swiftpm', ['swift', 'run', '--package-path', checkout / 'runner',
                '--scratch-path', staging / 'unbound-swift', 'PWUnboundControls'], env=env)
            package.write_text(original_package)
            shutil.rmtree(fixture)
        worker = checkout / 'controller/tools/pw_probe_runner/pw_probe_runner.c'
        source = worker.read_text()
        anchor = 'int main(int argc, char **argv) {'
        assert source.count(anchor) == 1
        trace = f'\n    int trace_fd = open({json.dumps(str(worker_trace))}, O_WRONLY | O_CREAT | O_APPEND, 0600);\n    if (trace_fd >= 0) {{ (void)write(trace_fd, "worker\\n", 7); close(trace_fd); }}'
        source = source.replace(anchor, anchor + trace)
        if mode == 'append':
            anchor = 'int fd = open(slot->target, O_WRONLY | O_TRUNC);'
            assert source.count(anchor) == 1
            source = source.replace(anchor, 'int fd = open(slot->target, O_WRONLY | O_APPEND);')
        worker.write_text(source)
        client = checkout / 'runner/Clients/PWRunnerClient/main.swift'
        source = client.read_text(); anchor = 'private func run(args: [String]) -> Never {'
        assert source.count(anchor) == 1
        source = source.replace(anchor, anchor + f'\n    if let trace = fopen({json.dumps(str(client_trace))}, "a") {{ fputs("client\\n", trace); fclose(trace) }}')
        client.write_text(source)
        command(case, 'worker-identity', ['tests/lib/python.sh', 'docs/generate_worker_identity.py'], cwd=checkout, env=env)
        command(case, 'signed-build', ['make', 'build', 'IDENTITY=' + identity], cwd=checkout, env=env)
        app = checkout / 'dist/PolicyWitness.app'
        context = build_context.candidate_contract(app)
        assert fixture_digest(checkout) == authored_fixtures, 'building a different source changed a fixture'
        save(case / 'product.json', dict(contract=context, app=str(app),
            fixtures_sha256=authored_fixtures,
            controller_sha256=sha256((app / 'Contents/MacOS/policy-witness').read_bytes()).hexdigest(),
            request_shape_sha256=sha256((checkout / 'tests/fixtures/contract/surfaces/request.json').read_bytes()).hexdigest(),
            reply_shape_sha256=sha256((checkout / 'tests/fixtures/contract/response_shape.json').read_bytes()).hexdigest(),
            worker_source_sha256=sha256(worker.read_bytes()).hexdigest(), instrumentation=True))
        (case / 'instrumented.patch').write_bytes(subprocess.check_output(['git', 'diff', '--binary', 'HEAD'], cwd=checkout))
        shutil.copy2(app / 'Contents/Info.plist', case / 'Info.plist')
        shutil.copy2(app / 'Contents/Resources/Evidence/provenance.json', case / 'provenance.json')
        products[mode] = (app, context)
    assert products['truncate'][1] != products['append'][1]
    a, b = (json.loads((out / mode / 'product.json').read_text()) for mode in products)
    assert a['request_shape_sha256'] == b['request_shape_sha256']
    assert a['reply_shape_sha256'] == b['reply_shape_sha256']
    effect = staging / 'effect'; seed = b'original-content'
    observations = []
    for receiver, assertion in [('truncate', 'truncate'), ('append', 'truncate'), ('append', 'append'), ('truncate', 'append')]:
        app, expected = products[receiver]; asserted = products[assertion][1]
        for trace in (client_trace, worker_trace): trace.unlink(missing_ok=True)
        effect.write_bytes(seed)
        request = dict(contract=asserted, specimen_id=receiver + '-' + assertion,
            policy=dict(format='sbpl', sbpl_source='(version 1)(allow default)'),
            probe_plan=[dict(step_id='write', sandbox_check=dict(operation='file-write-data', filter=dict(kind='path', value=str(effect))),
                attempt=dict(kind='file', action='open_write', target=str(effect)))])
        with RunCapture(app / 'Contents/MacOS/policy-witness', out / request['specimen_id'], request) as run:
            original = run.request_path.read_bytes()
            rc = run.wait(timeout=30); envelope = run.load_json()
            assert run.request_path.read_bytes() == original
        observed = effect.read_bytes()
        traces = {trace.name: trace.read_text() if trace.exists() else None for trace in (client_trace, worker_trace)}
        if receiver == assertion:
            assert rc == 0 and envelope['result']['ok'] is True, envelope
            assert all(traces.values()), traces
            assert observed == (b'x' if receiver == 'truncate' else seed + b'x'), observed
            assert envelope['data']['runner_result']['runner_subprocess']['reaped'] is True
        else:
            assert rc == 1 and envelope['result']['normalized_outcome'] == 'bad_request', envelope
            assert envelope['data']['request_failure']['expected_contract'] == expected
            assert envelope['data']['runner_client'] is None and envelope['data']['runner_result'] is None
            assert observed == seed and not any(traces.values()), (observed, traces)
        observations.append(dict(receiver=receiver, assertion=assertion, returncode=rc, before_hex=seed.hex(),
                                 after_hex=observed.hex(), launch_traces=traces))
        save(out / 'observations.json', observations)
    for checkout in ownership['worktrees']:
        command(out, 'remove-' + Path(checkout).name, ['git', 'worktree', 'remove', '--force', checkout])
    ownership['complete'] = True; save(out / 'ownership.json', ownership)
    shutil.rmtree(staging)
    print('same request and reply shape; source-specific contracts prevent the foreign file effect before either process launch')


if __name__ == '__main__':
    main()
