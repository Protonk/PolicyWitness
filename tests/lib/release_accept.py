"""Accept one final release ZIP: inspect its extracted app and run the default battery against it."""
import argparse
import json
import os
import plistlib
import re
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tempfile
import zipfile
import uuid
import retention
import run_ownership
import execution_contract
import outcomes
from pytest_support import read, contained

import artifact
import release_evidence
import publication_freshness
from release_commands import command, save

ROOT = Path(__file__).resolve().parents[2]
# The battery's bound: an initial operational ceiling, revised from recorded
# elapsed times. The receipt records the limit and the elapsed time; expiry
# fails acceptance and keeps whatever the dispatcher wrote.
BATTERY_TIMEOUT_SECONDS = 7200
# Default members whose envelopes name the runner that served them; acceptance
# reads them out of the battery to require the bundled standard runner.
PROVENANCE_ENVELOPES = ('smoke/specimen_file_read_deny/artifacts/policy_witness.run.stdout.json',
                        'witness_contract/happy_path_baseline/artifacts/run.json')


def battery_summary(run):
    summary = dict(run_id=run.get('run_id'), completion=run.get('completion'),
                   started_at_unix_ms=run.get('started_at_unix_ms'), finished_at_unix_ms=run.get('finished_at_unix_ms'),
                   duration_ms=run.get('duration_ms'))
    if 'outcomes' in run:
        summary['outcomes'] = run['outcomes']
    return summary


def battery_problems(run, app, *, expected=None, evidence=None):
    """Why a nested run is not a passing default battery against the extracted app; empty when it is."""
    problems = []
    completion = run.get('completion') or {}
    if run.get('ok') is not True or run.get('terminal') is not True:
        problems.append('the run did not pass')
    if not completion.get('selected') or completion.get('completed') != completion.get('selected'):
        problems.append('not every selected case completed')
    if completion.get('skipped') or completion.get('unrun'):
        problems.append('skipped or unrun cases')
    if run.get('harness_errors'):
        problems.append('harness errors')
    if (run.get('requested_cases') or run.get('requested_suites')
            or (run.get('plan') or {}).get('selection', {}).get('mode') != 'default'):
        problems.append('a selection other than the default battery')
    if (run.get('configuration') or {}).get('app_dir') != str(app):
        problems.append('a tested app other than the extracted one')
    integrity = run.get('artifact_integrity') or {}
    if integrity.get('valid_before') is not True or integrity.get('unchanged') is not True:
        problems.append('an invalid or changed app')
    # Completion is allowed only under independently captured new authority;
    # the required raw account is checked below. Legacy all-pass rules remain.
    completed_cases = set()
    if expected and expected.get('profile') == execution_contract.PROFILE:
        completed_cases = {row['id'] for row in expected['selected'] if 'outcome_contract' in row}
        completed_cases.update(name for name, selection in expected['family_selections'].items()
                               if selection and selection.get('schema_version') == 2
                               and any('outcome_contract' in item for item in selection['items']))
    if any(c.get('status') != 'pass' and not (c.get('status') == 'complete' and c.get('id') in completed_cases)
           for c in run.get('case_results') or []):
        problems.append('a case that did not pass')
    if expected is not None:
        try:
            def load_bytes(name):
                return contained(evidence, evidence / name).read_bytes()
            def load_json(name):
                return (outcomes.decode(load_bytes(name)) if expected.get('profile') == execution_contract.PROFILE
                        else read(contained(evidence, evidence / name)))
            problems += execution_contract.problems(run, expected, load_json, load_bytes)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            problems.append('required family evidence: ' + str(exc))
    return problems


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


def development_source(app, info, version, inspection, *, root=ROOT):
    """Bind a private candidate run to actual build inputs and both source revisions."""
    sys.path.insert(0, str(root / 'docs'))
    import build_contract
    import publication
    contract = build_contract.identity(root)
    if not contract.startswith('development:'):
        raise ValueError('candidate verification requires development source identity')
    if info.get('PWContract') != contract or version.get('build', {}).get('contract') != contract:
        raise ValueError('candidate app and current source build contracts differ')
    if type(info.get('PWPublicationBoundary')) is not int or info['PWPublicationBoundary'] != 1:
        raise ValueError('candidate requires signed publication boundary evidence')
    boundary = publication.validate(inspection.get('publication'), contract)
    if boundary != publication.record(root, contract):
        raise ValueError('candidate signed guide differs from the checked-out guide')
    commit = info.get('PWBuildCommit')
    provenance = json.loads((app / artifact.PROVENANCE).read_bytes())
    if (not isinstance(commit, str) or not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', commit)
            or version.get('build', {}).get('commit') != commit
            or provenance.get('source', {}).get('commit') != commit):
        raise ValueError('candidate app source commits differ or are unavailable')
    reporter = build_contract.git(root, 'rev-parse', 'HEAD')
    status = build_contract.git(root, 'status', '--porcelain', '--untracked-files=all')
    if not reporter or status is None:
        raise ValueError('candidate reporting source is unavailable')
    # Reporting may have changed since the app was built. The equality claim is
    # limited to the actual build-contract inputs, not the entire checkout.
    return contract, boundary, dict(app_commit=commit, reporting_commit=reporter,
        reporting_dirty=bool(status), build_contract=contract,
        agreement_scope='build_contract_inputs')


def accept(archive, out, *, invoke=command, inspect=artifact.inspect, mode='release'):
    if mode not in ('release', 'development-candidate'):
        raise ValueError('unknown archive verification mode')
    run_ownership.replacement_allowed(ROOT, out / 'tests', retention.protected_paths(ROOT))
    report = dict(schema_version=4, kind='release_acceptance' if mode == 'release' else 'development_candidate', execution_contract=execution_contract.defaults(ROOT), archive=str(archive), ok=False, errors=[],
                  battery=dict(timeout_seconds=BATTERY_TIMEOUT_SECONDS))
    if (out / 'owner.json').exists():
        report['run_id'] = run_ownership.valid_owner(out)['run_id']
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
        info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
        invoke(out / 'version', [app / 'Contents/MacOS/policy-witness', '--version'], timeout=30)
        version = json.loads((out / 'version/stdout').read_text())
        if mode == 'development-candidate':
            report['contract'], report['publication'], report['source'] = development_source(app, info, version, inspection)
            report['apple_assessment'] = dict(status='not_performed', reason='development_candidate')
        else:
            expected_contract = 'release:v' + info['CFBundleShortVersionString']
            if info.get('PWContract') != expected_contract or version.get('build', {}).get('contract') != expected_contract:
                raise ValueError('released archive does not report ' + expected_contract)
            report['contract'] = expected_contract
            report['publication'] = publication_freshness.require(ROOT, expected_contract.removeprefix('release:'), info.get('PWBuildCommit'))
            if (inspection.get('publication') or {}).get('status') == 'withheld':
                raise ValueError('publication withheld by signed artifact boundary')
            signed_guide = inspection.get('publication')
            if report['publication'].get('signed_guide_required') and not signed_guide:
                raise ValueError('tagged source requires a signed guide receipt')
            if signed_guide and signed_guide['guide']['sha256'] != report['publication']['guide_sha256']:
                raise ValueError('signed guide differs from the tagged release guide')
            invoke(out / 'staple-validation', ['/usr/bin/xcrun', 'stapler', 'validate', '-v', app], timeout=60)
            invoke(out / 'gatekeeper', ['/usr/sbin/spctl', '-a', '-vv', '--type', 'execute', app], timeout=60)
        # The ZIP is the sole app selection. Ignore inherited PW settings rather
        # than letting a usable local build or BYOXPC configuration replace it.
        env = {k: v for k, v in os.environ.items() if not k.startswith('PW_')}
        run_out = out / 'tests'
        env.update(PW_APP_DIR=str(app), PW_TEST_OUT_DIR=str(run_out), PYTHONDONTWRITEBYTECODE='1')
        # The default battery through the one test interface, with no selectors:
        # release production selects exactly as ordinary development does.
        invoke(out / 'execution', ['bash', ROOT / 'tests/run.sh'], timeout=BATTERY_TIMEOUT_SECONDS, env=env, cwd=ROOT)
        run = json.loads((run_out / 'run.json').read_bytes())
        report['battery'].update(battery_summary(run))
        problems = battery_problems(run, app, expected=report['execution_contract'], evidence=run_out)
        if problems:
            raise ValueError('the default battery did not pass against the extracted app: '
                             + '; '.join(problems) + '; see tests/run.json')
        # Both specimens must actually have used the bundled standard runner.
        for relative in PROVENANCE_ENVELOPES:
            path = run_out / 'suites' / relative
            if not path.is_file():
                raise ValueError(f'release specimen evidence missing from the battery: {relative}')
            envelope = json.loads(path.read_bytes())
            if ((envelope.get('data') or {}).get('specimen') or {}).get('runner_provenance', {}).get('runner_kind') != 'standard':
                raise ValueError(f'release specimen did not use the standard runner: {relative}')
        completed = True
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile, KeyboardInterrupt) as exc:
        report['errors'].append(str(exc) or 'interrupted')
    finally:
        # The receipt and whatever the dispatcher wrote stay with the acceptance,
        # passed, failed or timed out.
        try:
            receipt = out / 'execution/command.json'
            if receipt.is_file():
                record = json.loads(receipt.read_bytes())
                report['battery'].update(elapsed_seconds=record.get('elapsed_seconds'), timed_out=record.get('timed_out'))
            nested = out / 'tests/run.json'
            if 'run_id' not in report['battery'] and nested.is_file():
                report['battery'].update(battery_summary(json.loads(nested.read_bytes())))
        except (OSError, ValueError) as exc:
            report['errors'].append(f'battery receipt unreadable: {exc}')
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
    label = 'Release acceptance' if mode == 'release' else 'Development candidate verification'
    print(f'{label}: {out / "acceptance.json"}', flush=True)
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
        with run_ownership.acceptance_output(ROOT, out, lambda: retention.protected_paths(ROOT)):
            result = accept(archive, out)
            if args.evidence_dir:
                release_evidence.record_acceptance(args.evidence_dir, out / 'acceptance.json')
        return result
    except (ValueError, OSError, KeyError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    raise SystemExit(main())
