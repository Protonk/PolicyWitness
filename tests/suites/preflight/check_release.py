"""Bounded release controls using actual archives and independent tool receipts."""
from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import artifact
from release_accept import accept
sys.path.insert(0, str(ROOT / 'tests/fixtures/dispatcher'))
from artifacts import bundle, fingerprint
sys.path.insert(0, str(ROOT / 'tests/fixtures/release'))
from tools import Tools, ID
spec = importlib.util.spec_from_file_location('notarization', ROOT / 'notarize.py')
notarization = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notarization)


def check(out):
    completed = []
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
        bundle(source)
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
