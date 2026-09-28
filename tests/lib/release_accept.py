"""Accept one final release ZIP by inspecting and exercising its extracted app."""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tempfile
import zipfile
import uuid
import retention

import artifact
import release_evidence
from release_commands import command, save

ROOT = Path(__file__).resolve().parents[2]
CASES = ('smoke/specimen_file_read_deny', 'witness_contract/happy_path_baseline')


def archive_layout(archive):
    # ditto owns extraction, including macOS metadata. Reject ambiguous roots
    # and path escapes before handing it an archive. The shipped app has no links.
    with zipfile.ZipFile(archive) as zipped:
        seen = set()
        for entry in zipped.infolist():
            name = entry.filename.rstrip('/')
            path = PurePosixPath(name)
            if (not name or str(path) != name or path.is_absolute() or '..' in path.parts
                    or path.parts[0] not in ('PolicyWitness.app', '__MACOSX') or name in seen
                    or stat.S_ISLNK(entry.external_attr >> 16)):
                raise ValueError(f'unsupported archive member: {entry.filename}')
            seen.add(name)
        if 'PolicyWitness.app/Contents/Info.plist' not in seen:
            raise ValueError('archive has no PolicyWitness.app/Contents/Info.plist')


def accept(archive, out, *, invoke=command, inspect=artifact.inspect):
    retention.replacement_allowed(ROOT, out / 'tests', retention.load_index(ROOT))
    report = dict(schema_version=1, archive=str(archive), ok=False, errors=[], selected_cases=list(CASES))
    save(out / 'acceptance.json', report)
    staging, app, before = None, None, None
    completed = False
    try:
        report['sha256_before'] = artifact.digest(archive)
        save(out / 'acceptance.json', report)
        archive_layout(archive)
        staging = Path(tempfile.mkdtemp(prefix='pw-release-', dir='/private/tmp'))
        report['extraction_dir'] = str(staging)
        invoke(out / 'extract', ['/usr/bin/ditto', '-x', '-k', archive, staging], timeout=60)
        app = staging / 'PolicyWitness.app'
        if not app.is_dir() or app.is_symlink():
            raise ValueError('extraction did not produce the expected app directory')
        before = artifact.inventory(app)
        save(out / 'before.json', before)
        inspection = inspect(app)
        save(out / 'inspection.json', inspection)
        if not inspection['ok']:
            raise ValueError('extracted app failed artifact inspection; see inspection.json')
        invoke(out / 'staple-validation', ['/usr/bin/xcrun', 'stapler', 'validate', '-v', app], timeout=60)
        invoke(out / 'gatekeeper', ['/usr/sbin/spctl', '-a', '-vv', '--type', 'execute', app], timeout=60)
        # The ZIP is the sole app selection. Ignore inherited PW settings rather
        # than letting a usable local build or BYOXPC configuration replace it.
        env = {k: v for k, v in os.environ.items() if not k.startswith('PW_')}
        run_out = out / 'tests'
        env.update(PW_APP_DIR=str(app), PW_TEST_OUT_DIR=str(run_out), PYTHONDONTWRITEBYTECODE='1')
        argv = ['bash', ROOT / 'tests/run.sh']
        for case in CASES:
            argv.extend(['--case', case])
        invoke(out / 'execution', argv, timeout=180, env=env, cwd=ROOT)
        run = json.loads((run_out / 'run.json').read_bytes())
        expected = dict(selected=2, completed=2, skipped=0, unrun=0)
        if (run.get('ok') is not True or run.get('completion') != expected
                or run.get('configuration', {}).get('app_dir') != str(app)
                or {c['id'] for c in run.get('case_results', [])} != set(CASES)
                or any(c.get('status') != 'pass' for c in run['case_results'])):
            raise ValueError('release cases did not pass against the extracted app; see tests/run.json')
        # Both specimens must actually have used the bundled standard runner.
        for relative in ('smoke/specimen_file_read_deny/artifacts/policy_witness.run.stdout.json',
                         'witness_contract/happy_path_baseline/artifacts/run.json'):
            envelope = json.loads((run_out / 'suites' / relative).read_bytes())
            if envelope.get('data', {}).get('runner_provenance', {}).get('runner_kind') != 'standard':
                raise ValueError(f'release specimen did not use the standard runner: {relative}')
        completed = True
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile, KeyboardInterrupt) as exc:
        report['errors'].append(str(exc) or 'interrupted')
    finally:
        try:
            if before is not None:
                after = artifact.inventory(app)
                save(out / 'after.json', after)
                delta = artifact.changes(before, after)
                save(out / 'changes.json', delta)
                if delta:
                    report['errors'].append('extracted app changed during acceptance; see changes.json')
            report['sha256_after'] = artifact.digest(archive)
            if report.get('sha256_before') != report['sha256_after']:
                report['errors'].append('input archive changed during acceptance')
        except (OSError, ValueError) as exc:
            report['errors'].append(f'final integrity check failed: {exc}')
        if staging is not None:
            try:
                shutil.rmtree(staging)
            except OSError as exc:
                report['errors'].append(f'extraction cleanup failed: {exc}')
        report['ok'] = completed and not report['errors']
        save(out / 'acceptance.json', report)
    print(f'Release acceptance: {out / "acceptance.json"}', flush=True)
    if report['ok']:
        entry = dict(path=str(out.relative_to(ROOT / 'tests/out')), run_id=run['run_id'],
                     reason='Release ZIP acceptance', source=None, app_inventory='before.json')
        print('Suggested tests/RETAINED.json entry: ' + json.dumps(entry, sort_keys=True), flush=True)
    for error in report['errors']:
        print(f'STOP: {error}', file=sys.stderr)
    return 0 if report['ok'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('archive', type=Path, help='final stapled release ZIP; resolved from the current directory')
    parser.add_argument('--evidence-dir', type=Path, help='release attempt to receive an acceptance pointer')
    args = parser.parse_args()
    archive = args.archive.resolve()
    if not archive.is_file():
        parser.error('provide an existing final release ZIP')
    base = ROOT / 'tests/out/release-acceptance'
    # The test dispatcher owns and replaces its output directory.
    if base.resolve() != base or base in archive.parents:
        parser.error('release output must be a real directory separate from the input archive')
    out = base / ('run-' + uuid.uuid4().hex)
    try:
        if args.evidence_dir:
            release_evidence.check_archive(args.evidence_dir, archive)
        retention.replacement_allowed(ROOT, out, retention.load_index(ROOT))
        out.mkdir(parents=True)
        result = accept(archive, out)
        if args.evidence_dir:
            release_evidence.record_acceptance(args.evidence_dir, out / 'acceptance.json')
        return result
    except (ValueError, OSError, KeyError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    raise SystemExit(main())
