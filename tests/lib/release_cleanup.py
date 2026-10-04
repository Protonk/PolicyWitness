"""Release-checkpoint policy for working test output; no age or size thresholds."""
import fcntl
import os
import retention

CONTAINERS = ('runs', 'release-acceptance')


def output_path(value):
    relative = retention.relative_path(value)
    if (len(relative.parts) != 2 or relative.parts[0] not in CONTAINERS
            or not retention.RUN_ID.fullmatch(relative.name)):
        raise ValueError('cleanup requires a direct managed run or acceptance directory')
    return relative


def acceptance_busy(path):
    lock = path / 'acceptance.lock'
    if not os.path.lexists(lock):
        if (path / 'owner.json').exists():
            raise ValueError('acceptance ownership has no lifetime lock')
        return False  # Legacy acceptance used only nested dispatcher ownership.
    fd = os.open(lock, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    finally:
        os.close(fd)


def describe(path):
    """Ownership and recorded times, independent of names, mtime and size."""
    acceptance = path.parent.name == 'release-acceptance'
    if acceptance and acceptance_busy(path):
        raise ValueError('active acceptance')
    owned = path
    if acceptance and not os.path.lexists(path / 'owner.json'):
        # Legacy acceptance must have both its report and genuine nested output.
        report = retention.read_object(path / 'acceptance.json')
        if report.get('schema_version') != 1 or type(report.get('ok')) is not bool:
            raise ValueError('unrecognized legacy acceptance')
        owned = path / 'tests'
        retention.bounded_path(path.parents[3], owned)
    owner = retention.valid_owner(owned)
    started, finished = owner['started_at_unix_ms'], None
    if acceptance and owned == path:
        if owner.get('kind') != 'release_acceptance':
            raise ValueError('unrecognized acceptance owner')
        state = 'interrupted'
        if owner.get('terminal') is True:
            finished = owner.get('finished_at_unix_ms')
            if type(finished) is not int or finished < started:
                raise ValueError('invalid acceptance completion time')
            state = 'completed'
    else:
        state = retention.disposition(owned)
        if state == 'completed':
            finished = retention.read_object(owned / 'run.json')['finished_at_unix_ms']
    return dict(run_id=owner['run_id'], started_at_unix_ms=started,
                finished_at_unix_ms=finished, disposition=state)


def cleanup_blocker(path):
    """Inspect actual case receipts, not nested fixture copies or log text.

    External-runner recovery remains owned by its existing session equipment.
    This helper never contacts launchd, removes services or follows staging links.
    """
    tests = path / 'tests' if path.parent.name == 'release-acceptance' else path
    if tests.is_symlink():
        return 'redirected nested test output'
    suites = tests / 'suites'
    if suites.is_symlink():
        return 'redirected suite output'
    if not suites.exists():
        return None
    # Only suite/case/artifacts is the dispatcher's case layout. Recursing into
    # fixture repositories would mistake intentional failure controls for leaks.
    for suite in suites.iterdir():
        if suite.is_symlink():
            return 'redirected suite output'
        if not suite.is_dir():
            continue
        for case in suite.iterdir():
            if case.is_symlink():
                return 'redirected case output'
            if not case.is_dir():
                continue
            artifacts = case / 'artifacts'
            if artifacts.is_symlink():
                return 'redirected case artifacts'
            session = artifacts / 'session.json'
            if os.path.lexists(session):
                state = retention.read_object(session)
                if state.get('removed') is not True or state.get('cleanup_error'):
                    return f'pending external-runner cleanup: {session.relative_to(path)}'
            if suite.name == 'runner_byoxpc' and case.name == 'registry_recovery':
                receipt = artifacts / 'controls.json'
                if not receipt.exists() or retention.read_object(receipt).get('cleanup_verified') is not True:
                    return 'pending registry recovery cleanup'
    return None


def candidates(root):
    """Unknown output is reported and left alone, including links and files."""
    found, kept = {}, []
    for container in CONTAINERS:
        base = retention.bounded_path(root, root / 'tests/out' / container)
        if not base.exists():
            continue
        for path in sorted(base.iterdir()):
            relative = container + '/' + path.name
            try:
                output_path(relative)
                retention.bounded_path(root, path)
                if not path.is_dir():
                    raise ValueError('not a managed directory')
                found[relative] = describe(path)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                kept.append(dict(path=relative, reason=str(exc)))
    return found, kept
