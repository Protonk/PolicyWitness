"""Exercise real ZIP acceptance and its default battery with Apple responses supplied locally.

Internal equipment for build_refusal_controls. Extraction, signature inspection,
the dispatcher and every case are real. Only notarization, staple validation and
Gatekeeper responses are stand-ins; this establishes no Apple acceptance.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests/lib'))
import artifact
import notarize
import release_accept
import release_commands
import retention
from tools import Tools


def check(archive, out):
    archive, out = archive.resolve(), out.absolute()
    before = artifact.digest(archive)
    calls = []

    def invoke(directory, argv, **kwargs):
        command = list(map(str, argv))
        calls.append(command)
        if command[:3] == ['/usr/bin/xcrun', 'stapler', 'validate'] or command[0] == '/usr/sbin/spctl':
            directory.mkdir()
            (directory / 'stdout').write_text('Controlled Apple assessment; no real assessment performed.\n')
            (directory / 'stderr').write_text('')
            release_commands.save(directory / 'command.json', dict(
                argv=command, timeout_seconds=kwargs['timeout'], elapsed_seconds=0,
                returncode=0, timed_out=False, interrupted=False, controlled=True))
            return
        assert command[0] in ('/usr/bin/ditto', 'bash'), command
        if command[0] == 'bash':
            assert command == ['bash', str(ROOT / 'tests/run.sh')], command
        return release_commands.command(directory, argv, **kwargs)

    with retention.acceptance_output(ROOT, out):
        submission = out / 'controlled-notarization'
        submission.mkdir()
        assert notarize.submit(archive, 'unused-fixture-profile', submission,
                               invoke=Tools('accepted', submission / 'calls.jsonl')) == 0
        result = release_accept.accept(archive, out, invoke=invoke)
        release_commands.save(out / 'rehearsal.json', dict(
            ok=result == 0, archive_sha256=before, calls=calls,
            controlled=['notarization', 'staple-validation', 'gatekeeper']))
        assert result == 0, (out / 'acceptance.json').read_text()
        run = retention.read_object(out / 'tests/run.json')
        assert run['plan']['selection'] == dict(mode='default', cases=[], suites=[]), run['plan']['selection']
        assert run['ok'] and run['completion']['selected'] == run['completion']['completed'] > 0
        assert run['completion']['skipped'] == run['completion']['unrun'] == 0
        assert len([argv for argv in calls if argv[0] == 'bash']) == 1, calls
        assert artifact.digest(archive) == before
        # Repeat the archive binding's independent extraction, including modes.
        from release_archive import extracted_final
        with extracted_final(archive) as extracted:
            assert artifact.inventory(extracted) == retention.read_object(out / 'tests/artifact-integrity/before.json')
    print(json.dumps(dict(acceptance=str(out), run_id=run['run_id'], completion=run['completion'])))


if __name__ == '__main__':
    check(Path(sys.argv[1]), Path(sys.argv[2]))
