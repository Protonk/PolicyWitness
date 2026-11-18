"""Declared observations and product judgments, separate from experiment validity.

Specifications are captured before execution. Accounts retain explicit results;
ordinary exceptions remain execution failures and are never converted to judgments.
This module does not supervise commands or establish resource ownership. Those
obligations remain with the producing engine and its independent readers.
"""
import hashlib
import json
from pathlib import PurePosixPath
import re

SCHEMA_VERSION = 1
AUTHORITIES = ('enforced', 'advisory')
RESULTS = ('favorable', 'unfavorable')
FAILURES = ('execution', 'validity', 'cleanup')
DIGEST = re.compile(r'[0-9a-f]{64}')


def decode(data):
    """Explicit-account JSON is unambiguous; duplicate keys/nonfinite values refuse."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate outcome evidence key: ' + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError('nonfinite outcome evidence number: ' + value)
    return json.loads(data, object_pairs_hook=unique, parse_constant=constant)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _ids(rows, label):
    if not isinstance(rows, list) or any(not isinstance(row, dict) or not _text(row.get('id')) for row in rows):
        raise ValueError(label + ' must be a list of identified records')
    values = [row['id'] for row in rows]
    if len(values) != len(set(values)):
        raise ValueError('duplicate ' + label + ' identity')
    return set(values)


def validate_spec(spec):
    """Validate a pre-execution specification; no result may choose its authority."""
    if not isinstance(spec, dict) or type(spec.get('schema_version')) is not int or spec['schema_version'] != SCHEMA_VERSION:
        raise ValueError('unsupported outcome specification')
    if set(spec) - {'schema_version', 'observations', 'judgments', 'commands'}:
        raise ValueError('unknown outcome specification field')
    if 'commands' in spec and spec['commands'] not in ('none', 'recorded'):
        raise ValueError('invalid command declaration')
    observed = _ids(spec.get('observations'), 'observation')
    if not observed:
        raise ValueError('an explicit experiment promises observations')
    for row in spec['observations']:
        if set(row) != {'id', 'promise'} or not _text(row['promise']):
            raise ValueError('an observation requires its promise')
    _ids(spec.get('judgments'), 'judgment')
    for row in spec['judgments']:
        if set(row) != {'id', 'authority', 'proposition', 'observations'}:
            raise ValueError('invalid judgment declaration')
        if row['authority'] not in AUTHORITIES or not _text(row['proposition']):
            raise ValueError('invalid judgment authority or proposition')
        references = row['observations']
        if (not isinstance(references, list) or not references or any(not isinstance(name, str) for name in references)
                or len(set(references)) != len(references) or not set(references) <= observed):
            raise ValueError('judgment requires distinct declared observations')
    return spec


def empty_account():
    return dict(schema_version=SCHEMA_VERSION, observations=[], judgments=[], failures=[])


def file_reference(path, data):
    """Construct a reference from retained bytes; paths are relative to the account owner."""
    _path(path)
    return dict(path=path, sha256=hashlib.sha256(data).hexdigest())


def _path(name):
    if not isinstance(name, str) or not name or '\\' in name or '\0' in name:
        raise ValueError('invalid evidence path')
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or path.as_posix() != name or name == '.':
        raise ValueError('evidence path is not a bounded relative name')
    return name


def validate_evidence(references, load_bytes=None, *, required=True):
    if not isinstance(references, list) or (required and not references):
        raise ValueError('completed observation requires evidence references')
    paths = []
    for reference in references:
        if not isinstance(reference, dict) or set(reference) != {'path', 'sha256'}:
            raise ValueError('invalid evidence reference')
        name = _path(reference['path'])
        if not isinstance(reference['sha256'], str) or not DIGEST.fullmatch(reference['sha256']):
            raise ValueError('invalid evidence digest')
        if load_bytes is not None:
            data = load_bytes(name)
            if not isinstance(data, bytes) or hashlib.sha256(data).hexdigest() != reference['sha256']:
                raise ValueError('evidence changed: ' + name)
        paths.append(name)
    if len(set(paths)) != len(paths):
        raise ValueError('duplicate evidence reference')


def assess(spec, account, load_bytes=None):
    """Reconcile a required account, preserving readable partial observations.

    Without load_bytes this checks structure only, for provisional projections.
    An acceptance reader must supply the owner's bounded byte loader, and must
    independently validate engine phases, commands, source identity and cleanup.
    """
    validate_spec(spec)
    errors, observations, judgments = [], [], []
    expected_observations = {row['id']: row for row in spec['observations']}
    expected_judgments = {row['id']: row for row in spec['judgments']}
    if not isinstance(account, dict) or type(account.get('schema_version')) is not int or account['schema_version'] != SCHEMA_VERSION:
        account = empty_account()
        errors.append('required outcome account missing or unsupported')
    elif set(account) != {'schema_version', 'observations', 'judgments', 'failures'}:
        errors.append('outcome account fields differ from the required form')
    for role, expected, accepted_rows in (('observations', expected_observations, observations),
                                          ('judgments', expected_judgments, judgments)):
        rows = account.get(role)
        try:
            actual_ids = _ids(rows, role)
        except ValueError as exc:
            errors.append(str(exc))
            rows = rows if isinstance(rows, list) else []
            actual_ids = {row['id'] for row in rows if isinstance(row, dict) and _text(row.get('id'))}
        if actual_ids != set(expected):
            errors.append(role + ' differ from specification: missing=' + repr(sorted(set(expected) - actual_ids))
                          + ', unexpected=' + repr(sorted(actual_ids - set(expected))))
        seen = set()
        for row in rows:
            try:
                if not isinstance(row, dict) or row.get('id') not in expected or row['id'] in seen:
                    raise ValueError('unexpected or duplicate ' + role + ' record')
                seen.add(row['id'])
                if role == 'observations':
                    if set(row) != {'id', 'facts', 'evidence'}:
                        raise ValueError('observation fields differ from the required form')
                    json.dumps(row['facts'], allow_nan=False)
                    validate_evidence(row['evidence'], load_bytes)
                else:
                    if set(row) != {'id', 'authority', 'proposition', 'observations', 'result', 'detail'}:
                        raise ValueError('judgment fields differ from the required form')
                    if any(row.get(key) != value for key, value in expected[row['id']].items()):
                        raise ValueError('judgment declaration or authority differs from specification')
                    if row['result'] not in RESULTS or not isinstance(row['detail'], str):
                        raise ValueError('invalid judgment result or detail')
                accepted_rows.append(row)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                errors.append(role + ': ' + str(exc))
    valid_observation_ids = {row['id'] for row in observations}
    for row in judgments:
        if not set(row['observations']) <= valid_observation_ids:
            errors.append('judgment lacks required valid observations: ' + row['id'])
    failures = account.get('failures')
    if not isinstance(failures, list):
        errors.append('missing experiment failure account')
    else:
        for row in failures:
            try:
                if (not isinstance(row, dict) or set(row) != {'kind', 'message', 'evidence'}
                        or row['kind'] not in FAILURES or not _text(row['message'])):
                    raise ValueError('invalid experiment failure')
                validate_evidence(row['evidence'], load_bytes, required=False)
                errors.append(row['kind'] + ': ' + row['message'])
            except (OSError, ValueError, KeyError, TypeError) as exc:
                errors.append('experiment failure: ' + str(exc))
    blocking = [row for row in judgments if row['authority'] == 'enforced' and row['result'] == 'unfavorable']
    advisory = [row for row in judgments if row['authority'] == 'advisory']
    judged_observations = {name for row in spec['judgments'] for name in row['observations']}
    informational = [row for row in observations if row['id'] not in judged_observations]
    counts = dict(observations=dict(promised=len(expected_observations), completed=len(observations)),
                  enforced={result:sum(row['authority'] == 'enforced' and row['result'] == result for row in judgments) for result in RESULTS},
                  advisory={result:sum(row['result'] == result for row in advisory) for result in RESULTS},
                  informational=len(informational))
    return dict(valid=not errors, accepted=not errors and not blocking, errors=errors,
                blocking_judgments=blocking, advisory_judgments=advisory,
                informational_completions=informational, counts=counts)


def summarize(assessments):
    """Summarize named parent/nested accounts without adding their distinct scopes."""
    assessments = list(assessments)
    result = {}
    for scope in ('parent', 'nested'):
        rows = [(name, value) for level, name, value in assessments if level == scope]
        result[scope] = dict(experiments=len(rows), invalid_accounts=sum(not value['valid'] for _, value in rows),
            observations={key: sum(value['counts']['observations'][key] for _, value in rows) for key in ('promised', 'completed')},
            enforced={key: sum(value['counts']['enforced'][key] for _, value in rows) for key in ('favorable', 'unfavorable')},
            advisory={key: sum(value['counts']['advisory'][key] for _, value in rows) for key in ('favorable', 'unfavorable')},
            informational=sum(value['counts']['informational'] for _, value in rows))
    return result
