#!/usr/bin/python3
"""Submit one retained ZIP, then ask notarytool to wait once for up to five minutes.

Only a recognized Accepted response permits later Makefile steps. This wrapper
never retries, polls itself, staples, rebuilds, or infers status from prose.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent / 'tests/lib'))
from artifact import digest
from release_commands import command, save


def response(path):
    def unique_fields(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('ambiguous duplicate response field')
            value[key] = item
        return value

    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=unique_fields)
    except (ValueError, OSError) as exc:
        raise RuntimeError(f'unrecognized Apple response; inspect {path} and its sibling stderr') from exc
    if not isinstance(value, dict):
        raise RuntimeError(f'unrecognized Apple response; inspect {path}')
    return value


def submission_id(value):
    raw = value.get('id')
    if not isinstance(raw, str):
        raise RuntimeError('Apple response has no recognized submission ID; inspect raw output before any new submission')
    try:
        return str(uuid.UUID(raw))
    except ValueError as exc:
        raise RuntimeError('unrecognized submission ID; inspect raw output before any new submission') from exc


def submit(archive, profile, out, *, invoke=command):
    report = dict(schema_version=1, archive=str(archive), state='stopped', submission_id=None)
    save(out / 'result.json', report)
    try:
        report['sha256'] = digest(archive)
        retained = out / 'submitted.zip'
        shutil.copyfile(archive, retained)
        if digest(retained) != report['sha256']:
            raise RuntimeError('archive changed while retaining the submission')
        save(out / 'result.json', report)
        invoke(out / 'submit', ['/usr/bin/xcrun', 'notarytool', 'submit', retained,
               '--keychain-profile', profile, '--no-wait', '--output-format', 'json'], timeout=180)
        report['submission_id'] = submission_id(response(out / 'submit/stdout'))
        save(out / 'result.json', report)
        # A separate wait retains the ID even when Apple never finishes. The
        # outer deadline also covers hangs outside notarytool's own wait timer.
        invoke(out / 'wait', ['/usr/bin/xcrun', 'notarytool', 'wait', report['submission_id'],
               '--keychain-profile', profile, '--timeout', '5m', '--output-format', 'json'], timeout=330)
        answer = response(out / 'wait/stdout')
        report['observed_status'] = answer.get('status')
        if submission_id(answer) != report['submission_id'] or answer.get('status') != 'Accepted':
            raise RuntimeError('no recognized Accepted response for this submission; inspect wait output; no continuation performed')
        if digest(archive) != report['sha256'] or digest(retained) != report['sha256']:
            raise RuntimeError('archive changed during submission; do not continue with the current dist artifacts')
        report['state'] = 'accepted'
    except (OSError, ValueError, RuntimeError, KeyboardInterrupt) as exc:
        report['error'] = str(exc) or 'interrupted'
        print(f'STOP: {report["error"]}\nRetained submission: {out}\nSee SIGNING.md before continuing.', file=sys.stderr)
    finally:
        save(out / 'result.json', report)
    return 0 if report['state'] == 'accepted' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('archive', type=Path)
    parser.add_argument('keychain_profile')
    args = parser.parse_args()
    archive = args.archive.resolve()
    if not archive.is_file() or not args.keychain_profile.strip():
        parser.error('provide an existing ZIP and an explicit keychain profile')
    out = Path(tempfile.mkdtemp(prefix='notarization-', dir=archive.parent))
    print(f'Notarization evidence: {out}', flush=True)
    return submit(archive, args.keychain_profile, out)


if __name__ == '__main__':
    raise SystemExit(main())
