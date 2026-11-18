"""Durable explicit observations for shell cases; selection owns their authority."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import outcomes
from pytest_support import append, contained, read, write


def account(directory):
    value = dict(schema_version=1, observations=[], judgments=[], failures=[])
    for line in (directory / 'outcomes.jsonl').read_bytes().splitlines():
        row = outcomes.decode(line)
        if not isinstance(row, dict) or set(row) != {'kind', 'record'}:
            raise ValueError('invalid observation journal record')
        if row['kind'] not in ('observations', 'judgments', 'failures'):
            raise ValueError('unknown observation journal record')
        value[row['kind']].append(row['record'])
    return value


def load_bytes(directory, name):
    path = contained(directory, directory / name)
    if not path.is_file():
        raise ValueError('missing observation evidence: ' + name)
    return path.read_bytes()


_UNPUBLISHED = object()


def verify(directory, spec, published=_UNPUBLISHED):
    errors = []
    try:
        if read(directory / 'outcome-contract.json') != spec:
            errors.append('case authority differs from selection')
        value = account(directory)
        if read(directory / 'outcomes.json') != value:
            errors.append('observation snapshot differs from journal')
        if published is not _UNPUBLISHED and published != value:
            errors.append('terminal observation account differs from journal')
        result = outcomes.assess(spec, value, lambda name: load_bytes(directory, name))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        value = published if isinstance(published, dict) else {}
        result = outcomes.assess(spec, value, lambda name: load_bytes(directory, name))
        errors.append('required observation evidence: ' + str(exc))
    result['errors'].extend(errors)
    if errors:
        result.update(valid=False, accepted=False)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('init', 'observe', 'judge', 'failure', 'status'))
    parser.add_argument('arguments', nargs='*')
    args = parser.parse_args()
    directory = Path(os.environ['PW_TEST_DIR']).resolve()
    contracts = outcomes.decode(os.environ.get('PW_TEST_OUTCOME_CONTRACTS', '{}'))
    key = os.environ['PW_TEST_SUITE'] + '/' + os.environ['PW_TEST_ID']
    spec = contracts.get(key)
    if args.action == 'init':
        if spec is None:
            return
        outcomes.validate_spec(spec)
        write(directory / 'outcome-contract.json', spec)
        if (directory / 'outcomes.jsonl').exists():
            raise ValueError('observation journal already exists')
        (directory / 'outcomes.jsonl').touch()
        write(directory / 'outcomes.json', account(directory))
        return
    if spec is None:
        raise ValueError('case has no selected observation contract')
    outcomes.validate_spec(spec)
    if args.action == 'status':
        result = verify(directory, spec)
        write(directory / 'outcome-assessment.json', result)
        print('complete' if result['accepted'] else 'fail')
        return
    if args.action == 'observe':
        identifier, facts, *files = args.arguments
        evidence = []
        for name in files:
            path = contained(directory, Path(name) if Path(name).is_absolute() else directory / name)
            evidence.append(dict(path=path.relative_to(directory).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        kind, record = 'observations', dict(id=identifier, facts=outcomes.decode(facts), evidence=evidence)
    elif args.action == 'judge':
        identifier, result, detail = args.arguments
        matches = [j for j in spec['judgments'] if j['id'] == identifier]
        if len(matches) != 1:
            raise ValueError('judgment is not selected: ' + identifier)
        kind, record = 'judgments', dict(**matches[0], result=result, detail=detail)
    else:
        kind, record = 'failures', dict(kind=args.arguments[0], message=args.arguments[1], evidence=[])
    append(directory / 'outcomes.jsonl', dict(kind=kind, record=record))
    write(directory / 'outcomes.json', account(directory))


if __name__ == '__main__':
    main()
