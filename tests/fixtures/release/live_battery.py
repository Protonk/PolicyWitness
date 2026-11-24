"""Verify a normally built development candidate's ZIP, or show strict release acceptance refusing it.

Internal equipment for build_refusal_controls. Candidate verification runs the
acceptance helper in development-candidate mode: extraction, signature
inspection, the app's --version and the default battery are real and run once.
Of the commands the helper runs through its command boundary, any other is
refused before it runs, notarization, staple validation, Gatekeeper assessment
and a dispatcher command with selectors among them; signature inspection runs
its own tools outside that boundary. Strict release acceptance is given accepting
staple-validation and Gatekeeper stand-ins and must refuse before reaching
them or the dispatcher; the stand-ins establish only that the refusal does not
depend on an Apple response.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'docs'))
import artifact
import build_contract
import publication
import release_accept
import release_commands
import retention
import run_ownership


class Boundary:
    """One extraction of the archive, the extracted app's --version and the default battery with no selectors."""

    def __init__(self, archive):
        self.archive, self.extracted, self.calls = str(archive), None, []

    def admit(self, argv):
        command = list(map(str, argv))
        self.calls.append(command)
        if command[:4] == ['/usr/bin/ditto', '-x', '-k', self.archive] and len(command) == 5 and self.extracted is None:
            self.extracted = Path(command[4]) / 'PolicyWitness.app'
            return
        version = None if self.extracted is None else [str(self.extracted / 'Contents/MacOS/policy-witness'), '--version']
        if command != version and command != ['bash', str(ROOT / 'tests/run.sh')]:
            raise AssertionError(f'candidate verification may not run {command}')


def candidate(archive, out):
    archive, out = archive.resolve(), out.absolute()
    before = artifact.digest(archive)
    boundary = Boundary(archive)

    def invoke(directory, argv, **kwargs):
        boundary.admit(argv)
        return release_commands.command(directory, argv, **kwargs)

    with run_ownership.acceptance_output(ROOT, out, lambda: retention.protected_paths(ROOT)):
        result = release_accept.accept(archive, out, invoke=invoke, mode='development-candidate')
        report = run_ownership.read_object(out / 'acceptance.json')
        contract = build_contract.identity(ROOT)
        head = build_contract.git(ROOT, 'rev-parse', 'HEAD')
        release_commands.save(out / 'candidate-verification.json', dict(
            ok=result == 0, archive_sha256=before, calls=boundary.calls, source_contract=contract, source_head=head,
            **{key: report.get(key) for key in ('kind', 'contract', 'publication', 'apple_assessment', 'source')}))
        assert result == 0, (out / 'acceptance.json').read_text()
        assert report['kind'] == 'development_candidate', report['kind']
        assert contract.startswith('development:') and report['contract'] == contract, (report['contract'], contract)
        assert report['publication'] == publication.record(ROOT, contract), report['publication']
        assert report['apple_assessment'] == dict(status='not_performed', reason='development_candidate'), report['apple_assessment']
        assert report['source']['app_commit'] == head, (report['source'], head)
        assert report['source']['agreement_scope'] == 'build_contract_inputs', report['source']
        assert len(boundary.calls) == 3 and boundary.calls[-1] == ['bash', str(ROOT / 'tests/run.sh')], boundary.calls
        run = run_ownership.read_object(out / 'tests/run.json')
        assert run['plan']['selection'] == dict(mode='default', cases=[], suites=[]), run['plan']['selection']
        assert run['ok'] and run['completion']['selected'] == run['completion']['completed'] > 0
        assert run['completion']['skipped'] == run['completion']['unrun'] == 0
        assert artifact.digest(archive) == before
        # Repeat the archive binding's independent extraction, including modes.
        from release_archive import extracted_final
        with extracted_final(archive) as extracted:
            assert artifact.inventory(extracted) == run_ownership.read_object(out / 'tests/artifact-integrity/before.json')
    print(json.dumps(dict(acceptance=str(out), run_id=run['run_id'], completion=run['completion'])))


def strict(archive, out):
    archive, out = archive.resolve(), out.absolute()
    before = artifact.digest(archive)
    boundary = Boundary(archive)
    reached = []

    def invoke(directory, argv, **kwargs):
        command = list(map(str, argv))
        if command[:3] == ['/usr/bin/xcrun', 'stapler', 'validate'] or command[0] == '/usr/sbin/spctl':
            boundary.calls.append(command)
            reached.append(command)
            directory.mkdir()
            (directory / 'stdout').write_text('Controlled Apple assessment; no real assessment performed.\n')
            (directory / 'stderr').write_text('')
            release_commands.save(directory / 'command.json', dict(
                argv=command, timeout_seconds=kwargs['timeout'], elapsed_seconds=0,
                returncode=0, timed_out=False, interrupted=False, controlled=True))
            return
        if command[0] == 'bash':
            boundary.calls.append(command)
            raise AssertionError(f'strict acceptance reached the dispatcher: {command}')
        boundary.admit(argv)
        return release_commands.command(directory, argv, **kwargs)

    with run_ownership.acceptance_output(ROOT, out, lambda: retention.protected_paths(ROOT)):
        result = release_accept.accept(archive, out, invoke=invoke)
        report = run_ownership.read_object(out / 'acceptance.json')
        release_commands.save(out / 'strict-acceptance.json', dict(
            refused=result != 0, archive_sha256=before, calls=boundary.calls, stand_ins_reached=reached,
            kind=report.get('kind'), errors=report.get('errors')))
        assert result == 1 and report['ok'] is False and report['kind'] == 'release_acceptance', report
        assert not reached, reached
        assert not any(command[0] == 'bash' for command in boundary.calls), boundary.calls
        assert not Path(report['extraction_dir']).exists()
        assert artifact.digest(archive) == before
    print(json.dumps(dict(acceptance=str(out), errors=report['errors'])))


if __name__ == '__main__':
    if sys.argv[1] == '--strict':
        strict(Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        candidate(Path(sys.argv[1]), Path(sys.argv[2]))
