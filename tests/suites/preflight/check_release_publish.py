"""Offline controls for the tag preflight, release archiving and GitHub publication."""
from contextlib import redirect_stderr, redirect_stdout
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import release_archive
import release_evidence
import release_preflight
import release_publish
import retention
import release_runs
sys.path.insert(0, str(ROOT / 'tests/fixtures/dispatcher'))
from repository import completed_output
import fixture_bundle
sys.path.insert(0, str(ROOT / 'tests/fixtures/release'))
from publish_tools import GitHub

GIT = ['git', '-c', 'user.name=pw', '-c', 'user.email=pw@example.invalid', '-c', 'commit.gpgsign=false',
       '-c', 'tag.gpgsign=false']


def git(repo, *args):
    return subprocess.run([*GIT, '-C', str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def make_repo(work):
    """A real repository with one commit and a bare origin, so tag and remote checks are genuine."""
    repo, remote = work / 'repo', work / 'remote.git'
    repo.mkdir()
    subprocess.run(['git', 'init', '-q', '--bare', str(remote)], check=True)
    git(repo, 'init', '-q', '-b', 'main')
    (repo / 'README.md').write_text('fixture\n')
    git(repo, 'add', 'README.md')
    git(repo, 'commit', '-q', '-m', 'initial')
    git(repo, 'remote', 'add', 'origin', str(remote))
    git(repo, 'push', '-q', 'origin', 'main')
    (repo / 'tests').mkdir()
    (repo / 'tests/RETAINED.json').write_text('{"schema_version": 1, "runs": []}\n')
    return repo


def expect_problem(problems, needle):
    assert any(needle in problem for problem in problems), (needle, problems)


def check_preflight(out):
    # Version coordinates need not be consecutive. Use real annotated tags
    # and a local bare remote; no product tag or external publication is made.
    skipped = out / 'skipped-version'
    skipped.mkdir()
    skipped_repo = make_repo(skipped)
    git(skipped_repo, 'tag', '-a', 'v0.2.8', '-m', 'previous release')
    git(skipped_repo, 'commit', '-q', '--allow-empty', '-m', 'next release')
    git(skipped_repo, 'tag', '-a', 'v0.3.0', '-m', 'skip 0.2.9')
    stamp, problems = release_preflight.inspect(skipped_repo)
    assert problems == [] and stamp['version'] == '0.3.0', (stamp, problems)
    assert stamp['describe'] == 'v0.3.0' and stamp['build_number'] == '2', stamp
    assert stamp['prose_baseline']['previous_tag'] == 'v0.2.8', stamp
    assert stamp['build_baseline']['previous_tag'] == 'v0.2.8', stamp
    (skipped / 'preflight.json').write_text(json.dumps(stamp, indent=2) + '\n')

    work = out / 'preflight'
    work.mkdir()
    repo = make_repo(work)
    stamp, problems = release_preflight.inspect(repo)
    expect_problem(problems, 'not at a release tag')
    assert stamp['version'] == '0.0.0' and stamp['build_number'] == '1', stamp

    git(repo, 'tag', 'v0.9.0')  # lightweight
    _, problems = release_preflight.inspect(repo)
    expect_problem(problems, 'lightweight')
    git(repo, 'tag', '-d', 'v0.9.0')

    git(repo, 'tag', '-a', 'v0.9.0', '-m', 'PolicyWitness 0.9.0')
    (repo / 'README.md').write_text('dirty\n')
    _, problems = release_preflight.inspect(repo)
    expect_problem(problems, 'uncommitted changes')
    (repo / 'README.md').write_text('fixture\n')

    stamp, problems = release_preflight.inspect(repo)
    assert problems == [] and stamp['version'] == '0.9.0' and stamp['tag'] == 'v0.9.0', (stamp, problems)
    assert stamp['remote_tag'] is None and stamp['head'] == git(repo, 'rev-parse', 'HEAD')

    git(repo, 'push', '-q', 'origin', 'v0.9.0')
    stamp, problems = release_preflight.inspect(repo)
    assert problems == [] and stamp['remote_tag'] == git(repo, 'rev-parse', 'v0.9.0'), (stamp, problems)

    (repo / 'dist/archive/v0.9.0').mkdir(parents=True)
    _, problems = release_preflight.inspect(repo)
    expect_problem(problems, 'already exists')
    shutil.rmtree(repo / 'dist')

    git(repo, 'tag', '-d', 'v0.9.0')
    (repo / 'second').write_text('2\n')
    git(repo, 'add', 'second')
    git(repo, 'commit', '-q', '-m', 'second')
    git(repo, 'tag', '-a', 'v0.9.0', '-m', 'moved')
    _, problems = release_preflight.inspect(repo)
    expect_problem(problems, 'different v0.9.0')
    _, problems = release_preflight.inspect(repo, remote='nowhere')
    expect_problem(problems, 'cannot query nowhere')

    # The CLI stops in strict mode and only warns with --report; the stamp is still reported.
    with patch.object(release_preflight, 'ROOT', repo):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            strict = release_preflight.main(['--format', 'version'])
        assert strict == 1 and stdout.getvalue() == '' and 'STOP:' in stderr.getvalue()
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            report = release_preflight.main(['--report'])
        assert report == 0 and 'WARNING:' in stderr.getvalue()
        assert json.loads(stdout.getvalue())['version'] == '0.9.0'
    return repo


def check_branch_names(out):
    """Compare real build stamps and release decisions at one source/path under new refs."""
    work = out / 'branch-names'
    work.mkdir()
    repo = make_repo(work)
    git(repo, 'branch', 'master')
    git(repo, 'branch', 'doc-rework')
    source = (ROOT / 'build.sh').read_text()
    start = source.index('PW_BUILD_DESCRIBE=')
    end = source.index('echo "==> Build stamp:', start)
    stamp_source = source[start:end]
    assert 'PW_BUILD_COMMIT=' in stamp_source and 'PW_BUILD_NUMBER=' in stamp_source
    command = ('ROOT_DIR="$1"\n' + stamp_source +
               '\nprintf "%s\\n" "$PW_BUILD_DESCRIBE" "$PW_BUILD_COMMIT" "$PW_VERSION" "$PW_BUILD_NUMBER"\n')
    env = {key: value for key, value in os.environ.items()
           if key not in {'PW_VERSION', 'PW_BUILD_NUMBER'}}
    receipts = []
    for state in ('untagged', 'tagged', 'dirty'):
        if state == 'tagged':
            git(repo, 'tag', '-a', 'v0.9.1', '-m', 'branch comparison')
        elif state == 'dirty':
            (repo / 'README.md').write_text('dirty branch comparison\n')
        original = None
        for branch in ('main', 'master', 'doc-rework', f'renamed-{state}'):
            if branch.startswith('renamed-'):
                git(repo, 'switch', '-q', '-c', f'new-{state}')
                git(repo, 'branch', '-m', branch)
            else:
                git(repo, 'switch', '-q', branch)
            actual_branch = git(repo, 'branch', '--show-current')
            assert actual_branch == branch
            result = subprocess.run(['/bin/bash', '-euc', command, 'branch-stamp', str(repo)],
                                    env=env, capture_output=True, text=True, check=True)
            describe, commit, version, number = result.stdout.splitlines()
            build_stamp = dict(describe=describe, head=commit, version=version, build_number=number)
            stamp, problems = release_preflight.inspect(repo)
            assert build_stamp == {key: stamp[key] for key in build_stamp}, (build_stamp, stamp)
            if state == 'untagged':
                expect_problem(problems, 'not at a release tag')
                assert len(problems) == 1 and version == '0.0.0'
            elif state == 'tagged':
                assert problems == [] and describe == 'v0.9.1'
            else:
                expect_problem(problems, 'uncommitted changes')
                assert len(problems) == 1 and describe == 'v0.9.1-dirty'
            observation = dict(build_stamp=build_stamp, preflight=stamp, problems=problems)
            if original is None:
                original = observation
            assert observation == original, (state, branch, original, observation)
            receipts.append(dict(state=state, branch=branch, observation=observation))
    (work / 'build-stamp.sh').write_text(command)
    (work / 'comparisons.json').write_text(json.dumps(receipts, indent=2) + '\n')


FIXTURE_RECORD = None
FIXTURE_MEMBERS = None


def prepare_provenance_fixture(out):
    """Real linker-signed Mach-O members, described by the independent fixture writer."""
    global FIXTURE_RECORD, FIXTURE_MEMBERS
    host = out / 'provenance-host'
    subprocess.run(['bash', str(ROOT / 'tests/fixtures/dispatcher/build.sh'), str(host)], check=True, capture_output=True)
    app = out / 'provenance-fixture.app'
    fixture_bundle.bundle(app, host)
    data = json.loads((app / fixture_bundle.RECORD).read_text())
    data['configuration']['knobs']['BUILD_XPC'] = '0'
    data['toolchain']['compilers']['swift'] = dict(status='not applicable', reason='partial build: the XPC pieces were not compiled')
    paths = ('Contents/MacOS/policy-witness', 'Contents/MacOS/sandbox-log-observer', 'Contents/MacOS/sbpl-check')
    data['outputs'] = [o for o in data['outputs'] if o['rel_path'] in paths]
    data['signing']['nested'] = [o for o in data['signing']['nested'] if o['rel_path'] in paths]
    data['source'].update(describe='fixture-A', version='0.9.0', build_number='3')
    FIXTURE_RECORD = data
    FIXTURE_MEMBERS = {path: (app / path).read_bytes() for path in paths}


def fixture_record(build):
    data = copy.deepcopy(FIXTURE_RECORD)
    data['source']['describe'] = f'fixture-{build}'
    return data


def make_dist(repo, *, version='0.9.0', commit=None, describe=None, attempt=True, record=True):
    # Rotation controls import this fixture directly, without this module's
    # main(). Prepare its independent Mach-O members for every entrypoint.
    if FIXTURE_MEMBERS is None:
        with tempfile.TemporaryDirectory(prefix='pw-release-fixture-', dir='/private/tmp') as directory:
            prepare_provenance_fixture(Path(directory))
    commit = commit or git(repo, 'rev-parse', 'HEAD')
    dist = repo / 'dist'
    dist.mkdir(exist_ok=True)
    archive = dist / 'PolicyWitness.zip'
    info = dict(CFBundleShortVersionString=version, CFBundleVersion='3', PWBuildCommit=commit,
                PWBuildDescribe=describe or f'v{version}')
    with zipfile.ZipFile(archive, 'w') as zipped:
        zipped.writestr('PolicyWitness.app/Contents/Info.plist', plistlib.dumps(info))
        for relative, data in FIXTURE_MEMBERS.items():
            zipped.writestr('PolicyWitness.app/' + relative, data)
        if record:
            zipped.writestr('PolicyWitness.app/Contents/Resources/Evidence/provenance.json', json.dumps(FIXTURE_RECORD))
    (dist / 'PolicyWitness.md').write_text(f'# guide {version}\n')
    # The working app is build B by now: a later build whose record must never reach the archive of A's accepted ZIP.
    working = dist / 'PolicyWitness.app/Contents/Resources/Evidence'
    working.mkdir(parents=True, exist_ok=True)
    (working / 'provenance.json').write_text(json.dumps(fixture_record('B')))
    (dist / 'PolicyWitness.app/Contents/MacOS').mkdir(parents=True, exist_ok=True)
    (dist / 'PolicyWitness.app/Contents/MacOS/policy-witness').write_bytes(b'#!/bin/sh\n# build B\n')
    if not attempt:
        return dist, None
    session = release_evidence.create(archive)
    (session / 'notarization').mkdir()
    (session / 'notarization/result.json').write_text(json.dumps(dict(
        schema_version=1, state='accepted', observed_status='Accepted', archive=str(archive),
        sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), submission_id='00000000-1111-2222-3333-444444444444')))
    for step in ('staple', 'staple-validation', 'gatekeeper', 're-zip'):
        (session / step).mkdir()
        (session / step / 'command.json').write_text(json.dumps(dict(
            argv=[step], timeout_seconds=1, returncode=0, timed_out=False, interrupted=False, elapsed_seconds=0.1)))
    run_dir = repo / 'tests/out/release-acceptance' / ('run-' + version.replace('.', '-'))
    with retention.acceptance_output(repo, run_dir) as owner:
        owner['run_id'] = 'accept-' + version
        (run_dir / 'before.json').write_text('{}\n')
        completed_output(run_dir / 'tests')
        for name in ('owner.json', 'run.json'):
            path = run_dir / 'tests' / name
            value = json.loads(path.read_text())
            value['run_id'] = 'nested-accept-' + version
            path.write_text(json.dumps(value))
        (run_dir / 'acceptance.json').write_text(json.dumps(dict(
            schema_version=1, archive=str(archive), ok=True, errors=[],
            sha256_before=hashlib.sha256(archive.read_bytes()).hexdigest(),
            sha256_after=hashlib.sha256(archive.read_bytes()).hexdigest())))
    release_evidence.record_acceptance(session, run_dir / 'acceptance.json')
    return dist, session


def make_battery(repo, dist, *, version='0.9.0', **overrides):
    run_dir = repo / 'tests/out/runs' / f'release-{version}-default'
    (run_dir / 'artifact-integrity').mkdir(parents=True)
    (run_dir / 'artifact-integrity/before.json').write_text('{}\n')
    completed_output(run_dir)
    owner = json.loads((run_dir / 'owner.json').read_text())
    owner['run_id'] = 'battery-' + version
    (run_dir / 'owner.json').write_text(json.dumps(owner))
    run = json.loads((run_dir / 'run.json').read_text())
    run.update(schema_version=1, run_id=owner['run_id'], ok=True, terminal=True,
               counts={'fail': 0, 'pass': 3, 'skip': 0, 'total': 3},
               completion=dict(selected=3, completed=3, skipped=0, unrun=0),
               requested_cases=[], requested_suites=[], harness_errors=[],
               artifact_integrity=dict(app=str((dist / 'PolicyWitness.app').resolve()), unchanged=True, valid_before=True))
    run['plan']['cases'] = [dict(id='fixture/' + str(i)) for i in range(3)]
    run['case_results'] = [dict(id=c['id'], state='completed', status='pass') for c in run['plan']['cases']]
    run.update(overrides)
    (run_dir / 'run.json').write_text(json.dumps(run))
    return run_dir


def check_archive(out):
    work = out / 'archive'
    work.mkdir()
    repo = make_repo(work)
    git(repo, 'tag', '-a', 'v0.9.0', '-m', 'PolicyWitness 0.9.0')
    dist, session = make_dist(repo)
    battery = make_battery(repo, dist)
    notes = work / 'notes.md'
    notes.write_text('PolicyWitness 0.9.0 fixture notes\n')
    # A non-accepted decoy attempt must not confuse --latest.
    decoy = release_evidence.create(dist / 'PolicyWitness.zip')
    attempt_name = session.name

    assert release_archive.find_latest(dist) == session
    dest, added = release_archive.archive(session, dist=dist, root=repo, notes=notes, battery=battery)
    assert dest == dist / 'archive/v0.9.0'
    expected = {'PolicyWitness-0.9.0.zip', 'PolicyWitness.md', 'SHA256SUMS', 'release.json', 'evidence'}
    assert {p.name for p in dest.iterdir()} == expected, sorted(p.name for p in dest.iterdir())
    assert (dest / 'PolicyWitness-0.9.0.zip').read_bytes() == (dist / 'PolicyWitness.zip').read_bytes()
    sums = dict(line.split()[::-1] for line in (dest / 'SHA256SUMS').read_text().splitlines())
    assert sums == {name: hashlib.sha256((dest / name).read_bytes()).hexdigest()
                    for name in ('PolicyWitness-0.9.0.zip', 'PolicyWitness.md')}, sums
    assert not session.exists() and (dist / 'evidence' / (attempt_name + '.archived')).read_text().strip() == str(dest / 'evidence')
    assert (dest / 'evidence/release-notes.md').read_text() == notes.read_text()
    assert {p.name for p in (dest / 'evidence').iterdir()} >= {'notarization', 'staple', 're-zip', 'acceptance.json', 'release.json', 'README.md'}
    assert decoy.is_dir(), 'the decoy attempt was moved'
    record = json.loads((dest / 'release.json').read_text())
    assert record['version'] == '0.9.0' and record['tag'] == 'v0.9.0' and record['origin'] is None
    assert record['source_commit'] == git(repo, 'rev-parse', 'HEAD') and record['build_number'] == '3'
    assert record['sha256'] == sums['PolicyWitness-0.9.0.zip'] and record['notarization_submission_id'].startswith('00000000')
    assert record['acceptance'] == dict(path=release_runs.BUNDLE + '/acceptance.json',
                                      original_path='release-acceptance/run-0-9-0/acceptance.json', ok=True, sha256=record['sha256'])
    assert record['battery'] == dict(path=release_runs.BUNDLE + '/battery.json',
                                   original_path='runs/release-0.9.0-default', run_id='battery-0.9.0')
    assert [r['archived_path'] for r in record['receipts']] == [
        'evidence/notarization', 'evidence/staple', 'evidence/staple-validation', 'evidence/gatekeeper',
        'evidence/re-zip', 'evidence/acceptance.json', 'evidence/release.json']
    assert all(r['original_path'].startswith('dist/evidence/' + attempt_name) for r in record['receipts'])
    assert [e['path'] for e in added] == ['release-acceptance/run-0-9-0', 'runs/release-0.9.0-default']
    assert added[0]['run_id'] == 'accept-0.9.0' and added[0]['app_inventory'] == 'before.json'
    assert added[1]['app_inventory'] == 'artifact-integrity/before.json'
    assert all(e['release'] == 'v0.9.0' for e in added)
    assert all(e['source'] == record['source_commit'] and '0.9.0' in e['reason'] for e in added)
    retained = retention.load_index(repo)
    assert retained == [repo / 'tests/out/release-acceptance/run-0-9-0', repo / 'tests/out/runs/release-0.9.0-default']
    release_runs.verify_release(dest)
    # The archived record and the final controller hash are A's, read from the accepted ZIP; the working app is B.
    with zipfile.ZipFile(dest / 'PolicyWitness-0.9.0.zip') as zipped:
        member = zipped.read('PolicyWitness.app/Contents/Resources/Evidence/provenance.json')
        controller = hashlib.sha256(zipped.read('PolicyWitness.app/Contents/MacOS/policy-witness')).hexdigest()
    archived_record = dest / 'evidence/provenance.json'
    assert archived_record.read_bytes() == member and json.loads(member)['source']['describe'] == 'fixture-A'
    assert json.loads((dist / 'PolicyWitness.app/Contents/Resources/Evidence/provenance.json').read_text())['source']['describe'] == 'fixture-B'
    provenance = record['provenance']
    assert provenance['path'] == 'evidence/provenance.json' and provenance['sha256'] == hashlib.sha256(member).hexdigest()
    assert provenance['controller_sha256'] == controller != hashlib.sha256(b'#!/bin/sh\n# build B\n').hexdigest()
    assert isinstance(provenance['app_signature'], dict) and 'status' in provenance['app_signature']
    # A swapped archived record, a record that differs from the ZIP's, and a changed controller hash are refused on verification.
    original_record, original_release = archived_record.read_bytes(), (dest / 'release.json').read_bytes()
    for name, mutate, needle in (
            ('swapped record', lambda: archived_record.write_bytes(json.dumps(fixture_record('other')).encode()), 'checksum mismatch'),
            ('controller hash', lambda: (dest / 'release.json').write_text(json.dumps(dict(record, provenance=dict(provenance, controller_sha256='0' * 64)))), 'controller hash differs'),
            ('record hash', lambda: (dest / 'release.json').write_text(json.dumps(dict(record, provenance=dict(provenance, sha256='0' * 64)))), 'checksum mismatch'),
            ('missing seal facts', lambda: (dest / 'release.json').write_text(json.dumps(dict(record, provenance=dict(provenance, app_signature=None)))), 'seal facts')):
        mutate()
        try:
            release_runs.verify_release(dest)
        except ValueError as exc:
            assert needle in str(exc), (name, exc)
        else:
            raise AssertionError(f'{name}: verification passed')
        archived_record.write_bytes(original_record)
        (dest / 'release.json').write_bytes(original_release)
    release_runs.verify_release(dest)
    # Archiving the same version again is refused before anything is written.
    try:
        release_archive.archive(decoy, dist=dist, root=repo)
    except ValueError as exc:
        assert 'already exists' in str(exc) or 'acceptance.json' in str(exc), exc
    else:
        raise AssertionError('second archive was allowed')

    # Each refusal leaves the distribution untouched.
    scenarios = {
        'acceptance_hash': ('final ZIP bytes differ', lambda r, d, s: (s / 'acceptance.json').write_text(
            json.dumps(dict(path=json.loads((s / 'acceptance.json').read_text())['path'], ok=True, sha256='0' * 64)))),
        'acceptance_failed': ('acceptance did not pass', lambda r, d, s: (s / 'acceptance.json').write_text(
            json.dumps(dict(path=json.loads((s / 'acceptance.json').read_text())['path'], ok=False, sha256=json.loads((s / 'acceptance.json').read_text())['sha256'])))),
        'notarization_pending': ('not accepted', lambda r, d, s: (s / 'notarization/result.json').write_text(
            json.dumps(dict(state='unknown', submission_id='x')))),
        'wrong_commit': ('but v0.9.0 names', lambda r, d, s: git(r, 'tag', '-d', 'v0.9.0') and None or (
            (r / 'later').write_text('x\n'), git(r, 'add', 'later'), git(r, 'commit', '-q', '-m', 'later'),
            git(r, 'tag', '-a', 'v0.9.0', '-m', 'moved'))),
        'missing_tag': ('no local tag', lambda r, d, s: git(r, 'tag', '-d', 'v0.9.0')),
        'lightweight_tag': ('lightweight', lambda r, d, s: (git(r, 'tag', '-d', 'v0.9.0'), git(r, 'tag', 'v0.9.0'))),
        'missing_guide': ('staged guide missing', lambda r, d, s: (d / 'PolicyWitness.md').unlink()),
        'missing_notes': ('release notes missing', None),
    }
    for name, (needle, mutate) in scenarios.items():
        scenario = out / 'archive' / name
        scenario.mkdir()
        repo2 = make_repo(scenario)
        git(repo2, 'tag', '-a', 'v0.9.0', '-m', 'PolicyWitness 0.9.0')
        dist2, session2 = make_dist(repo2)
        battery2 = make_battery(repo2, dist2)
        if mutate is not None:
            mutate(repo2, dist2, session2)
        before = sorted(str(p.relative_to(dist2)) for p in dist2.rglob('*'))
        retained_before = (repo2 / 'tests/RETAINED.json').read_text()
        try:
            release_archive.archive(session2, dist=dist2, root=repo2, battery=battery2,
                                    notes=None if mutate is not None else scenario / 'absent.md')
        except ValueError as exc:
            assert needle in str(exc), (name, exc)
        else:
            raise AssertionError(f'{name}: archive was allowed')
        assert sorted(str(p.relative_to(dist2)) for p in dist2.rglob('*')) == before, name
        assert (repo2 / 'tests/RETAINED.json').read_text() == retained_before, name

    # Battery evidence must be a passing, unchanged, default run against the final app.
    for name, overrides, needle in [
            ('failed', dict(ok=False), 'not a completed passing run'),
            ('skipped', dict(completion=dict(selected=3, completed=2, skipped=1, unrun=0)), 'skips'),
            ('selection', dict(requested_suites=['smoke']), 'default selection'),
            ('changed_app', dict(artifact_integrity=dict(app='/nowhere/PolicyWitness.app', unchanged=True, valid_before=True)), 'final app'),
            ('mutated', dict(artifact_integrity=dict(app=str((dist / 'PolicyWitness.app').resolve()), unchanged=False, valid_before=True)), 'unchanged')]:
        scenario = out / 'archive' / f'battery_{name}'
        scenario.mkdir()
        repo3 = make_repo(scenario)
        git(repo3, 'tag', '-a', 'v0.9.0', '-m', 'PolicyWitness 0.9.0')
        dist3, session3 = make_dist(repo3)
        if name == 'changed_app':
            battery3 = make_battery(repo3, dist3, **overrides)
        else:
            battery3 = make_battery(repo3, dist3, **overrides)
        try:
            release_archive.archive(session3, dist=dist3, root=repo3, battery=battery3)
        except ValueError as exc:
            assert 'battery run rejected' in str(exc) and needle in str(exc), (name, exc)
        else:
            raise AssertionError(f'battery {name} was accepted')
        assert not (dist3 / 'archive').exists() and session3.is_dir()

    # An accepted ZIP without a record is refused before anything is staged.
    scenario = out / 'archive' / 'missing_record'
    scenario.mkdir()
    repo5 = make_repo(scenario)
    git(repo5, 'tag', '-a', 'v0.9.0', '-m', 'PolicyWitness 0.9.0')
    dist5, session5 = make_dist(repo5, record=False)
    before = sorted(str(p.relative_to(dist5)) for p in dist5.rglob('*'))
    try:
        release_archive.archive(session5, dist=dist5, root=repo5, battery=make_battery(repo5, dist5))
    except ValueError as exc:
        assert 'carries no provenance record' in str(exc), exc
    else:
        raise AssertionError('a ZIP without a record was archived')
    assert sorted(str(p.relative_to(dist5)) for p in dist5.rglob('*')) == before

    # --latest requires exactly one accepted attempt for the current final ZIP.
    scenario = out / 'archive' / 'latest'
    scenario.mkdir()
    repo4 = make_repo(scenario)
    git(repo4, 'tag', '-a', 'v0.9.0', '-m', 'PolicyWitness 0.9.0')
    dist4, session4 = make_dist(repo4)
    assert release_archive.find_latest(dist4) == session4
    (dist4 / 'PolicyWitness.zip').write_bytes(b'rebuilt')
    try:
        release_archive.find_latest(dist4)
    except ValueError as exc:
        assert 'found 0' in str(exc), exc
    else:
        raise AssertionError('a rebuilt ZIP still matched an attempt')
    with patch.object(release_archive, 'ROOT', repo4):
        stderr = io.StringIO()
        with redirect_stderr(stderr), redirect_stdout(io.StringIO()):
            try:
                release_archive.main(['--latest', '--dist', str(dist4)])
            except SystemExit as exc:
                assert exc.code == 1, exc
            else:
                raise AssertionError('CLI archived a rebuilt ZIP')
        assert 'STOP: expected exactly one accepted attempt' in stderr.getvalue()
    return repo, dest, notes


def check_publish(out, repo, dest, notes):
    work = out / 'publish'
    work.mkdir()
    remote_tags = lambda: git(repo, 'ls-remote', '--tags', 'origin')
    assert 'v0.9.0' not in remote_tags()
    github = GitHub(work / 'receipts.jsonl')
    with patch.object(release_publish, 'run', github):
        meta, created = release_publish.publish(dest, notes=notes, root=repo)
    assert created and meta['tagName'] == 'v0.9.0'
    assert 'refs/tags/v0.9.0' in remote_tags(), 'tag was not pushed'
    creates = [c for c in github.calls if c[1:3] == ['release', 'create']]
    assert len(creates) == 1 and creates[0][3] == 'v0.9.0'
    assert [Path(a).name for a in creates[0][4:7]] == ['PolicyWitness-0.9.0.zip', 'SHA256SUMS', 'PolicyWitness.md']
    assert creates[0][creates[0].index('--title') + 1] == 'PolicyWitness 0.9.0'
    assert github.release['notes'] == notes.read_text()
    downloads = [c for c in github.calls if c[1:3] == ['release', 'download']]
    assert {c[c.index('--pattern') + 1] for c in downloads} == set(github.assets), downloads
    record = json.loads((dest / 'release.json').read_text())
    assert record['origin'] == dict(kind='github_release', release_url=meta['url'],
                                    asset_url='https://github.invalid/releases/download/v0.9.0/PolicyWitness-0.9.0.zip')
    assert json.loads((dest / 'evidence/github-release.json').read_text()) == meta
    assert record['receipts'][-1]['archived_path'] == 'evidence/github-release.json'
    assert record['notes'] and 'match' in record['notes'][0]

    # A second run verifies and creates nothing; damaged local evidence stops before any call.
    calls_before = len(github.calls)
    with patch.object(release_publish, 'run', github):
        meta2, created2 = release_publish.publish(dest, root=repo)
    assert not created2 and meta2 == meta
    assert not any(c[1:3] == ['release', 'create'] for c in github.calls[calls_before:])
    assert json.loads((dest / 'release.json').read_text()) == record
    calls_before = len(github.calls)
    (dest / 'release.json').write_text(json.dumps(dict(record, source_commit='0' * 40)))
    with patch.object(release_publish, 'run', github):
        try:
            release_publish.publish(dest, root=repo)
        except ValueError as exc:
            assert 'ZIP stamp differs from the release record' in str(exc), exc
        else:
            raise AssertionError('mismatched source was published')
    assert len(github.calls) == calls_before
    (dest / 'release.json').write_text(json.dumps(record, indent=2) + '\n')

    copy = work / 'corrupt-evidence'
    shutil.copytree(dest, copy)
    (copy / release_runs.BUNDLE / 'runs.tar.gz').write_bytes(b'corrupt')
    with patch.object(release_publish, 'run', github):
        try:
            release_publish.publish(copy, root=repo)
        except ValueError as exc:
            assert 'test evidence archive checksum mismatch' in str(exc), exc
        else:
            raise AssertionError('damaged evidence was published')
    assert len(github.calls) == calls_before

    # The local tag is checked separately from the archive's internal consistency.
    original_tag = git(repo, 'rev-parse', 'v0.9.0')
    git(repo, 'commit', '--allow-empty', '-q', '-m', 'other commit')
    git(repo, 'tag', '-f', '-a', 'v0.9.0', '-m', 'moved')
    with patch.object(release_publish, 'run', github):
        try:
            release_publish.publish(dest, root=repo)
        except ValueError as exc:
            assert 'does not name the archived commit' in str(exc), exc
        else:
            raise AssertionError('mismatched tag was published')
    assert all(c[0] == 'git' and c[3] == 'rev-parse' for c in github.calls[calls_before:])
    git(repo, 'update-ref', 'refs/tags/v0.9.0', original_tag)

    # Mismatched digests or bytes stop before origin is recorded.
    for mode, needle in (('digest_mismatch', 'GitHub digest'), ('corrupt_download', 'downloaded bytes differ')):
        copy = work / mode
        shutil.copytree(dest, copy)
        unpublished = json.loads((copy / 'release.json').read_text())
        unpublished['origin'] = None
        (copy / 'release.json').write_text(json.dumps(unpublished, indent=2) + '\n')
        (copy / 'evidence/github-release.json').unlink()
        broken = GitHub(work / f'{mode}.jsonl', mode=mode)
        broken.release, broken.assets = github.release, dict(github.assets)
        with patch.object(release_publish, 'run', broken):
            try:
                release_publish.publish(copy, root=repo)
            except ValueError as exc:
                assert needle in str(exc), (mode, exc)
            else:
                raise AssertionError(f'{mode} was recorded as published')
        assert json.loads((copy / 'release.json').read_text())['origin'] is None
        assert not (copy / 'evidence/github-release.json').exists()
        assert not any(c[1:3] == ['release', 'create'] for c in broken.calls)

    # The CLI reports the verified release without a stray create.
    with patch.object(release_publish, 'run', github), patch.object(release_publish, 'ROOT', repo):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            assert release_publish.main([str(dest)]) == 0
        assert stdout.getvalue().startswith('verified https://github.invalid/releases/tag/v0.9.0')

    # Historical releases without a portable bundle remain publishable.
    legacy = work / 'legacy'
    shutil.copytree(dest, legacy)
    historical = json.loads((legacy / 'release.json').read_text())
    historical.pop('test_evidence')
    (legacy / 'release.json').write_text(json.dumps(historical))
    shutil.rmtree(legacy / release_runs.BUNDLE)
    with patch.object(release_publish, 'run', github):
        _, created = release_publish.publish(legacy, root=repo)
    assert not created


def main(out):
    out.mkdir(parents=True, exist_ok=True)
    check_preflight(out)
    check_branch_names(out)
    repo, dest, notes = check_archive(out)
    check_publish(out, repo, dest, notes)
    print('release publish controls passed: tag preflight, archive assembly with retention, and '
          'GitHub publication verify their inputs and refuse every mismatch')


if __name__ == '__main__':
    main(Path(sys.argv[1]))
