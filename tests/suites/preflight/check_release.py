"""Bounded release controls using actual archives and independent tool receipts."""
from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import artifact
import release_evidence
from release_accept import accept
sys.path.insert(0, str(ROOT / 'tests/fixtures/dispatcher'))
from fixture_bundle import bundle, fingerprint
sys.path.insert(0, str(ROOT / 'tests/fixtures/release'))
from tools import Tools, ID
spec = importlib.util.spec_from_file_location('notarization', ROOT / 'notarize.py')
notarization = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notarization)


def check_evidence(out):
    work = out / 'evidence_layout'
    work.mkdir()
    distribution = work / 'Custom dist with spaces'
    distribution.mkdir()
    archive = distribution / 'PolicyWitness.zip'
    info = dict(CFBundleShortVersionString='0.2.3', CFBundleVersion='268', PWBuildCommit='a' * 40)
    with zipfile.ZipFile(archive, 'w') as zipped:
        zipped.writestr('PolicyWitness.app/Contents/Info.plist', plistlib.dumps(info))
    original = archive.read_bytes()
    session = release_evidence.create(archive)
    assert session.parent == distribution / 'evidence'
    assert set(p.name for p in distribution.iterdir()) == {'PolicyWitness.zip', 'evidence'}
    assert json.loads((session / 'release.json').read_text())['submitted_sha256'] == artifact.digest(archive)
    tools = Tools('accepted', work / 'notary-receipts.jsonl')
    real_submit = notarization.submit

    def submit(archive, profile, out):
        return real_submit(archive, profile, out, invoke=tools)

    argv = ['notarize.py', str(archive), 'fixture-profile', '--evidence-dir', str(session)]
    with (work / 'notary.log').open('w') as log, redirect_stdout(log), redirect_stderr(log):
        with patch.object(sys, 'argv', argv), patch.object(notarization, 'submit', side_effect=submit):
            assert notarization.main() == 0
            for mode in ('duplicate', 'changed_archive', 'wrong_archive'):
                if mode == 'changed_archive':
                    archive.write_bytes(original + b'changed')
                elif mode == 'wrong_archive':
                    archive.write_bytes(original)
                    other = distribution / 'other.zip'
                    other.write_bytes(original)
                    argv[1] = str(other)
                try:
                    notarization.main()
                except SystemExit as exc:
                    assert exc.code == 2, (mode, exc)
                else:
                    raise AssertionError(f'{mode} submission was allowed')
    assert len(tools.calls) == 2, 'refused submission made an Apple call'
    assert (session / 'notarization/submitted.zip').read_bytes() == original

    # The actual command CLI must share the attempt, preserve failed receipts,
    # and refuse duplicate/path-escaping steps before invoking any process.
    receipt = work / 'executions'
    command = [sys.executable, '-B', '-c',
               'import pathlib,sys; p=pathlib.Path(sys.argv[1]); '
               'p.write_text(p.read_text()+"called\\n" if p.exists() else "called\\n"); '
               'print("partial receipt"); sys.exit(7)', str(receipt)]
    wrapper = [sys.executable, '-B', str(ROOT / 'tests/lib/release_commands.py')]
    def call(step):
        return subprocess.run([*wrapper, '--step', step, str(session), '10', *command],
                              capture_output=True, text=True, timeout=20)
    assert call('gatekeeper').returncode == 1
    assert receipt.read_text() == 'called\n'
    before = fingerprint(session / 'gatekeeper')
    assert call('gatekeeper').returncode == 1
    assert call('../escape').returncode == 2
    assert receipt.read_text() == 'called\n', 'refused step executed again'
    assert fingerprint(session / 'gatekeeper') == before, 'old command receipt changed'
    assert (session / 'gatekeeper/stdout').read_text() == 'partial receipt\n'
    assert 'exit 7' in (session / 'README.md').read_text()
    assert 'Notarization | accepted' in (session / 'README.md').read_text()

    acceptance = work / 'acceptance.json'
    acceptance.write_text(json.dumps(dict(archive=str(archive), ok=False,
                                         sha256_after=artifact.digest(archive))))
    release_evidence.record_acceptance(session, acceptance)
    pointer = json.loads((session / 'acceptance.json').read_text())
    assert pointer == dict(path=str(acceptance), ok=False, sha256=artifact.digest(archive))
    assert 'Archive acceptance | failed' in (session / 'README.md').read_text()
    acceptance.write_text(json.dumps(dict(archive=str(other), ok=True)))
    try:
        release_evidence.record_acceptance(session, acceptance)
    except ValueError:
        pass
    else:
        raise AssertionError('foreign archive acceptance attached to session')
    assert json.loads((session / 'acceptance.json').read_text()) == pointer


def check(out):
    check_evidence(out)
    completed = ['evidence_layout']
    for mode in ('accepted', 'agreement', 'unknown_submit', 'pending', 'rejected',
                 'unknown_status', 'wrong_id', 'ambiguous_response', 'wait_timeout', 'changed_archive'):
        work = out / ('notary_' + mode)
        work.mkdir()
        archive = work / 'original.zip'
        archive.write_bytes(b'opaque fixture submission')
        tools = Tools(mode, work / 'receipts.jsonl')
        with (work / 'stdout').open('w') as stdout, (work / 'stderr').open('w') as stderr:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                result = notarization.submit(archive, 'fixture-profile', work, invoke=tools)
        record = json.loads((work / 'result.json').read_text())
        assert result == (0 if mode == 'accepted' else 1), (mode, record)
        assert (work / 'submitted.zip').read_bytes() == b'opaque fixture submission'
        calls = [argv[2] for argv in tools.calls]
        assert calls == (['submit'] if mode in ('agreement', 'unknown_submit') else ['submit', 'wait']), calls
        if len(calls) == 2:
            assert record['submission_id'] == ID
        assert (record['state'] == 'accepted') is (mode == 'accepted')
        completed.append('notary_' + mode)

    for mode in ('valid', 'missing_helper', 'stale_manifest', 'missing_staple',
                 'xpc_failure', 'skipped', 'wrong_runner', 'mutated_app', 'corrupt_zip'):
        work = out / ('archive_' + mode)
        work.mkdir()
        source = work / 'PolicyWitness.app'
        bundle(source, Path(os.environ['PW_DISPATCHER_HOST_FIXTURE']))
        if mode == 'missing_helper':
            (source / 'Contents/MacOS/pw-runner-client').unlink()
        if mode == 'stale_manifest':
            (source / 'Contents/MacOS/pw-runner-client').write_bytes(b'resigned bytes')
        archive = work / 'release.zip'
        with zipfile.ZipFile(archive, 'w') as zipped:
            for path in source.rglob('*'):
                if path.is_file():
                    zipped.write(path, 'PolicyWitness.app/' + str(path.relative_to(source)))
        if mode == 'corrupt_zip':
            archive.write_bytes(b'corrupt zip')
        initial = archive.read_bytes()
        source_before = fingerprint(source)
        tools = Tools(mode, work / 'receipts.jsonl')

        def inspect(app):
            # Model only signature success here: all manifest/layout/inventory
            # checking remains real. Actual signatures have separate live controls.
            with patch.object(artifact.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')):
                return artifact.inspect(app)

        with (work / 'stdout').open('w') as stdout, (work / 'stderr').open('w') as stderr:
            with redirect_stdout(stdout), redirect_stderr(stderr), patch.dict(os.environ, {
                    'PW_APP_DIR': str(source), 'PW_BIN': str(source / 'Contents/MacOS/policy-witness'),
                    'PW_TEST_RUNNER_MODE': 'byoxpc'}):
                result = accept(archive, work, invoke=tools, inspect=inspect)
        record = json.loads((work / 'acceptance.json').read_text())
        assert result == (0 if mode == 'valid' else 1), (mode, record)
        assert record['ok'] is (mode == 'valid')
        if mode == 'valid':
            line = next(line for line in (work / 'stdout').read_text().splitlines()
                        if line.startswith('Suggested tests/RETAINED.json entry: '))
            entry = json.loads(line.split(': ', 1)[1])
            assert entry == dict(path=str(work.relative_to(ROOT / 'tests/out')),
                                 run_id='release-fixture', reason='Release ZIP acceptance',
                                 source=None, app_inventory='before.json')
        assert archive.read_bytes() == initial and fingerprint(source) == source_before
        if record.get('extraction_dir'):
            assert not Path(record['extraction_dir']).exists(), 'extraction was not cleaned up'
        executed = [a for a in tools.calls if a[0] == 'bash']
        assert bool(executed) is (mode in ('valid', 'xpc_failure', 'skipped', 'wrong_runner', 'mutated_app'))
        if mode == 'mutated_app':
            assert set(json.loads((work / 'changes.json').read_text())) == {'Contents/Info.plist'}
        completed.append('archive_' + mode)
    (out / 'controls.json').write_text(json.dumps(completed, indent=2) + '\n')
    print(f'{len(completed)} release controls passed')


if __name__ == '__main__':
    check(Path(sys.argv[1]).resolve())
