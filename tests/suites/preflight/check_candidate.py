"""Development candidate admission through real archives and constructed command responses."""
from contextlib import redirect_stdout, redirect_stderr
import hashlib
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
sys.path.insert(0, str(ROOT / 'tests/fixtures/dispatcher'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/release'))
sys.path.insert(0, str(ROOT / 'docs'))
import artifact
import build_contract
import execution_contract
import publication
import publication_freshness
import release_evidence
from release_accept import accept
from fixture_bundle import bundle, fingerprint
from tools import Tools

APP_COMMIT = '0' * 40


class CandidateTools(Tools):
    def __init__(self, mode, receipts, contract, commit=APP_COMMIT):
        super().__init__(mode, receipts)
        self.version_contract, self.version_commit = contract, commit

    def __call__(self, out, argv, **kwargs):
        super().__call__(out, argv, **kwargs)
        if list(map(str, argv))[1:] == ['--version']:
            (out / 'stdout').write_text(json.dumps(dict(build=dict(
                contract=self.version_contract, commit=self.version_commit))))


def check_candidate(out):
    contract = build_contract.identity(ROOT)
    assert contract.startswith('development:'), contract
    modes = ('valid', 'foreign_contract', 'foreign_version', 'foreign_commit',
             'missing_boundary', 'missing_marker', 'wrong_boundary', 'release_identity',
             'xpc_failure', 'timeout', 'wrong_runner', 'mutated_app')
    completed = []
    for mode in modes:
        work = out / ('candidate_' + mode)
        work.mkdir()
        source = work / 'PolicyWitness.app'
        bundle(source, Path(os.environ['PW_DISPATCHER_HOST_FIXTURE']))
        selected = ('development:' + 'f' * 64 if mode == 'foreign_contract' else
                    'release:v0.9.0' if mode == 'release_identity' else contract)
        info_path = source / 'Contents/Info.plist'
        info = plistlib.loads(info_path.read_bytes())
        info.update(CFBundleShortVersionString='0.9.0', PWContract=selected,
                    PWBuildCommit=APP_COMMIT, PWPublicationBoundary=1)
        if mode == 'missing_marker':
            del info['PWPublicationBoundary']
        info_path.write_bytes(plistlib.dumps(info))
        boundary = publication.record(ROOT, selected)
        if mode == 'wrong_boundary':
            boundary['build_contract'] = 'development:' + 'a' * 64
        publication.write(source / publication.RECORD, boundary)
        manifest_path = source / artifact.MANIFEST
        manifest = json.loads(manifest_path.read_bytes())
        manifest['entries'].append(dict(id='evidence.publication', kind='evidence', rel_path=publication.RECORD,
            sha256=hashlib.sha256((source / publication.RECORD).read_bytes()).hexdigest()))
        manifest_path.write_text(json.dumps(manifest))
        if mode == 'missing_boundary':
            (source / publication.RECORD).unlink()
        archive = work / 'candidate.zip'
        with zipfile.ZipFile(archive, 'w') as zipped:
            for path in source.rglob('*'):
                if path.is_file():
                    zipped.write(path, 'PolicyWitness.app/' + str(path.relative_to(source)))
        initial, source_before = archive.read_bytes(), fingerprint(source)
        tools = CandidateTools(mode, work / 'receipts.jsonl',
            'development:' + 'b' * 64 if mode == 'foreign_version' else selected,
            'f' * 40 if mode == 'foreign_commit' else APP_COMMIT)
        real_run = subprocess.run

        def modeled(argv, *args, **kwargs):
            if '-dvv' in argv:
                return real_run(argv, *args, **kwargs)
            return subprocess.CompletedProcess(argv, 0, '', '')

        def inspect(app):
            # Only signature verification success is modeled. Byte inventory,
            # manifest, load commands and signature displays remain observations.
            with patch.object(artifact.subprocess, 'run', side_effect=modeled):
                return artifact.inspect(app)

        with (work / 'stdout').open('w') as stdout, (work / 'stderr').open('w') as stderr:
            with redirect_stdout(stdout), redirect_stderr(stderr), \
                    patch.object(execution_contract, 'defaults', return_value=tools.contract), \
                    patch.object(publication_freshness, 'require', side_effect=AssertionError('candidate requested release freshness')):
                result = accept(archive, work, invoke=tools, inspect=inspect, mode='development-candidate')
        report = json.loads((work / 'acceptance.json').read_text())
        assert result == (0 if mode == 'valid' else 1), (mode, report)
        assert report['schema_version'] == 4 and report['kind'] == 'development_candidate'
        assert report['ok'] is (mode == 'valid')
        executed = [a for a in tools.calls if a[0] == 'bash']
        assert bool(executed) is (mode in ('valid', 'xpc_failure', 'timeout', 'wrong_runner', 'mutated_app'))
        assert not any(a[0] == '/usr/sbin/spctl' or a[1:3] == ['stapler', 'validate'] for a in tools.calls)
        assert archive.read_bytes() == initial and fingerprint(source) == source_before
        assert not Path(report['extraction_dir']).exists()
        if mode == 'valid':
            assert report['publication']['status'] == 'withheld'
            assert report['apple_assessment'] == dict(status='not_performed', reason='development_candidate')
            assert report['source']['app_commit'] == APP_COMMIT
            assert report['source']['reporting_commit'] == build_contract.git(ROOT, 'rev-parse', 'HEAD')
            assert report['source']['reporting_commit'] != APP_COMMIT
            assert report['source']['build_contract'] == contract
            assert report['source']['agreement_scope'] == 'build_contract_inputs'
            # The ordinary public route refuses these same development bytes
            # before any battery or Apple assessment, without a caller selector.
            strict = work / 'strict-release'
            strict.mkdir()
            strict_tools = CandidateTools('valid', strict / 'receipts.jsonl', contract)
            with (strict / 'stdout').open('w') as stdout, (strict / 'stderr').open('w') as stderr:
                with redirect_stdout(stdout), redirect_stderr(stderr), \
                        patch.object(execution_contract, 'defaults', return_value=strict_tools.contract):
                    assert accept(archive, strict, invoke=strict_tools, inspect=inspect) == 1
            strict_report = json.loads((strict / 'acceptance.json').read_text())
            assert strict_report['kind'] == 'release_acceptance'
            assert any('does not report release:v0.9.0' in error for error in strict_report['errors'])
            assert not any(a[0] == 'bash' for a in strict_tools.calls)
            assert not Path(strict_report['extraction_dir']).exists()
            session = release_evidence.create(archive)
            downgraded_candidate = dict(report, schema_version=3)
            del downgraded_candidate['kind']
            for label, variant in (
                    ('candidate', report), ('missing-kind', {k: v for k, v in report.items() if k != 'kind'}),
                    ('historical-downgrade', downgraded_candidate),
                    ('unsupported-version', dict(report, schema_version=5, kind='release_acceptance'))):
                path = work / ('refused-pointer-' + label + '.json')
                path.write_text(json.dumps(variant))
                before = fingerprint(session)
                try:
                    release_evidence.record_acceptance(session, path)
                except ValueError as exc:
                    assert 'not release acceptance' in str(exc) or 'unsupported acceptance' in str(exc), exc
                else:
                    raise AssertionError('candidate or unsupported receipt attached to release attempt')
                assert fingerprint(session) == before
            completed.append('candidate_receipt_schema_and_kind_downgrade')
        completed.append('candidate_' + mode)
    release_evidence.require_release_acceptance(dict(schema_version=3, ok=True))
    release_evidence.require_release_acceptance(dict(schema_version=3, contract='release:v0.9.0',
        publication=dict(status='current'), source=dict(commit='a' * 40)))
    release_evidence.require_release_acceptance(dict(schema_version=4, kind='release_acceptance'))
    # Each explicit field independently prevents a historical-format claim
    # from weakening the receipt. The expected markers are fixture literals.
    for marker in (
            dict(contract='development:' + 'a' * 64),
            dict(publication=dict(status='withheld')),
            dict(publication=dict(build_contract='development:' + 'a' * 64)),
            dict(apple_assessment=dict(status='not_performed')),
            dict(apple_assessment=dict(reason='development_candidate')),
            dict(source=dict(build_contract='development:' + 'a' * 64)),
            dict(source=dict(agreement_scope='build_contract_inputs'))):
        try:
            release_evidence.require_release_acceptance(dict(schema_version=3, **marker))
        except ValueError as exc:
            assert 'explicit development candidate evidence' in str(exc), (marker, exc)
        else:
            raise AssertionError(('historical format erased explicit candidate evidence', marker))
    completed.append('candidate_receipt_known_evidence_fields')
    return completed
