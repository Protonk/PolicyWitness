"""Replay retained raw battery records through an identified reporting revision.

This is a read-only investigation, not another test execution or release acceptance.
The source run is never modified. Input command accounts are allowlisted; derived
run/dispatch/family judgments are comparison targets only. The adapter cannot
reconstruct erased intermediate history, execute dependency gates, or establish
that an old experimental resource remains absent.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def snapshot(repository, revision, destination):
    """Only tracked reporting modules, not an additional implementation checkout."""
    if destination.exists():
        raise ValueError('reader snapshot must be fresh')
    commit = subprocess.check_output(['git', '-C', str(repository), 'rev-parse', revision + '^{commit}'], text=True).strip()
    names = subprocess.check_output(['git', '-C', str(repository), 'ls-tree', '-r', '--name-only', commit,
                                     '--', 'tests/lib'], text=True).splitlines()
    names = [name for name in names if name.endswith('.py') and '/vendor/' not in name]
    sources = {}
    for name in names:
        data = subprocess.check_output(['git', '-C', str(repository), 'show', commit + ':' + name])
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        sources[name] = hashlib.sha256(data).hexdigest()
    write(destination / 'reader-snapshot.json', dict(commit=commit, sources=sources))
    return commit


# These fields record command execution, never case/report acceptance.
COMMAND_FIELDS = ('state', 'returncode', 'started_at_unix_ms', 'finished_at_unix_ms',
                  'system_sleep_ms', 'system_sleep_error')
RUN_COMPARISON_FIELDS = ('schema_version', 'run_id', 'terminal', 'ok', 'execution_contract', 'counts_scope',
                        'counts', 'suites', 'reports', 'requested_suites', 'requested_cases',
                        'case_outcome_counts', 'case_results', 'completion', 'harness_errors')


def groups(plan):
    found = []
    for case in plan['cases']:
        if (case['context'] == 'byoxpc' and found and found[-1][0]['context'] == 'byoxpc'
                and case['command'] == found[-1][0]['command']):
            found[-1].append(case)
        else:
            found.append([case])
    return found


def partition_events(path, selected):
    """Preserve bytes and order. Reject history that cannot be assigned from raw identities."""
    owners = {}
    for index, group in enumerate(selected):
        for case in group:
            if case.get('engine') != 'pytest':
                key = (case['report_suite'], case['test_id'])
                if key in owners:
                    raise ValueError('ambiguous selected event identity')
                owners[key] = index
    parts = [bytearray() for _ in selected]
    previous = -1
    raw = path.read_bytes() if path.exists() else b''
    for line in raw.splitlines(keepends=True):
        row = json.loads(line)
        key = (row.get('suite'), row.get('test_id'))
        if key not in owners:
            raise ValueError('event has no selected invocation; use an independently captured fixture history')
        index = owners[key]
        if index < previous:
            raise ValueError('noncontiguous event history cannot be reconstructed from final files')
        parts[index].extend(line)
        previous = index
    if b''.join(parts) != raw:
        raise ValueError('event partition changed retained bytes')
    return list(map(bytes, parts))


def clone_case(source, destination):
    """APFS clone if available, ordinary copy otherwise; never share writable hard links."""
    if source.is_symlink():
        raise ValueError('replay case directory must not be a symlink: ' + str(source))
    destination.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == 'darwin':
        result = subprocess.run(['/bin/cp', '-cR', str(source), str(destination)], capture_output=True)
        if result.returncode == 0:
            return
        if destination.exists():
            shutil.rmtree(destination)
    shutil.copytree(source, destination, symlinks=True)


def inventory(path):
    files = {}
    for p in sorted(path.rglob('*')):
        relative = str(p.relative_to(path))
        if p.is_symlink():
            files[relative] = dict(symlink=str(p.readlink()))
        elif p.is_file():
            files[relative] = dict(sha256=sha(p))
    return files


def semantic_run(run):
    # No identities, observation contents or authority are normalized. Replay's
    # own finish timestamp is a new execution of the reader, not the experiment.
    result = {field:run.get(field) for field in RUN_COMPARISON_FIELDS}
    for field in ('outcomes', 'observation_reports'):
        if field in run:
            result[field] = run[field]
    result['invocations'] = [{field:item.get(field) for field in
        ('index', 'requested_suite', 'cases', *COMMAND_FIELDS, 'report_paths',
         'reports', 'harness_errors', 'case_results', 'family')}
        for item in run.get('invocations', [])]
    return result


def differences(left, right):
    return [key for key in sorted(left.keys() | right.keys())
            if key not in left or key not in right or left[key] != right[key]]


def replay(reader, evidence, destination):
    if destination.exists():
        raise ValueError('replay output must be fresh')
    evidence = evidence.resolve(strict=True)
    destination = destination.absolute()
    if destination == evidence or evidence in destination.parents:
        raise ValueError('replay output must be outside original evidence')
    stamp = read(reader / 'reader-snapshot.json')
    for name, expected in stamp['sources'].items():
        if sha(reader / name) != expected:
            raise ValueError('reader snapshot bytes changed: ' + name)
    sys.path.insert(0, str(reader / 'tests/lib'))
    import artifact
    import pytest_family
    import suite_run
    import release_accept

    plan = read(evidence / 'plan.json')
    owner = read(evidence / 'owner.json')
    dispatch = read(evidence / 'dispatch.json')
    selected = groups(plan)
    if dispatch['run_id'] != owner['run_id'] or len(dispatch['invocations']) != len(selected):
        raise ValueError('command account does not match captured selection/run')
    chunks = partition_events(evidence / 'events.jsonl', selected)
    destination.mkdir(parents=True)
    write(destination / 'plan.json', plan)
    raw_files = {name:sha(evidence / name) for name in ('owner.json','plan.json','dispatch.json')}
    if (evidence / 'events.jsonl').exists():
        raw_files['events.jsonl'] = sha(evidence / 'events.jsonl')
    invocations, commands, family_targets = [], [], {}
    previous_events, previous_reports, seen = b'', {}, {}
    (destination / 'events.jsonl').write_bytes(b'')
    with (destination / 'replay.stdout').open('w') as stdout, (destination / 'replay.stderr').open('w') as stderr:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            for index, group in enumerate(selected):
                command = dispatch['invocations'][index]
                if command['index'] != index or [c['id'] for c in command['cases']] != [c['id'] for c in group]:
                    raise ValueError('recorded command grouping differs from captured selection')
                account = {field:command.get(field) for field in COMMAND_FIELDS}
                # Blocked/launch-failed paths do not retain all prerequisite
                # observations needed to rederive the reason. Do not reuse it.
                if account['state'] != 'exited' or type(account['returncode']) is not int:
                    raise ValueError('replay requires recorded exits; use dispatcher controls for unstarted history')
                recorded = dict(account)
                if group[0].get('engine') == 'pytest':
                    # The dispatcher family status is computed from family.ok,
                    # not a second process-wait observation. Recompute below.
                    recorded.pop('returncode')
                commands.append(dict(index=index, cases=[c['id'] for c in group], **recorded))
                item = dict(index=index, requested_suite=group[0]['suite'], cases=group,
                            case_results=[], report_paths=[], reports=[], harness_errors=[], **account)
                for case in group:
                    relative = Path('suites') / case['report_suite'] / case['test_id']
                    source = evidence / relative
                    if source.exists():
                        raw_files.update({str(relative / name):value for name,value in inventory(source).items()})
                        clone_case(source, destination / relative)
                with (destination / 'events.jsonl').open('ab') as stream:
                    stream.write(chunks[index])
                if group[0].get('engine') == 'pytest':
                    case = group[0]
                    base = destination / 'suites' / case['id']
                    source = evidence / 'suites' / case['id']
                    selection = read(source / 'selection.json')
                    if selection != case['items']:
                        raise ValueError('family collection differs from pre-execution plan')
                    # This one field is process.wait()'s recorded observation;
                    # no derived family outcome, item or error enters replay.
                    engine_returncode = read(source / 'family.json')['engine_returncode']
                    if type(engine_returncode) is not int:
                        raise ValueError('family engine exit must be a recorded integer')
                    operations = []
                    for line in (source / 'operations.jsonl').read_bytes().splitlines() if (source / 'operations.jsonl').exists() else []:
                        event = json.loads(line)
                        if event['kind'] == 'registered':
                            operations.append(event['operation_id'])
                    family = pytest_family.account(selection, base / 'phases.jsonl', engine_returncode,
                                                   read(source / 'ownership.json'), operations)
                    item['family'] = family
                    item['returncode'] = 0 if family['ok'] else 1
                    if (base / 'family.json').is_symlink():
                        raise ValueError('replay family projection must not be a symlink')
                    write(base / 'family.json', family)
                    family_targets[case['id']] = read(source / 'family.json')
                    commands[-1]['engine_returncode'] = engine_returncode
                else:
                    if item['returncode'] != 0:
                        suite_run.problem(item, 'suite_exit', f"case command exited with status {item['returncode']}")
                    previous_events, previous_reports = suite_run.reconcile(item, destination, owner['run_id'],
                        previous_events, previous_reports, seen, plan['configuration']['python']['realpath'])
                if group[0].get('engine') == 'pytest' and item['returncode'] != 0:
                    suite_run.problem(item, 'suite_exit', f"case command exited with status {item['returncode']}")
                suite_run.account(item)
                invocations.append(item)
            integrity = None
            if any({'app','worker'} & set(c['requires']) for c in plan['cases']):
                source = evidence / 'artifact-integrity'
                for name in ('before.json','after.json','inspection.json'):
                    raw_files['artifact-integrity/' + name] = sha(source / name)
                before, after, inspection = (read(source / name) for name in ('before.json','after.json','inspection.json'))
                delta = artifact.changes(before, after)
                integrity = dict(app=plan['configuration']['app_dir'], valid_before=inspection['ok'],
                                 unchanged=not delta, report_dir='artifact-integrity', harness_errors=[])
                if not inspection['ok']:
                    suite_run.integrity_error(integrity,'artifact_invalid',
                        'selected app failed inspection; see artifact-integrity/inspection.json', findings=inspection['errors'])
                if delta:
                    suite_run.integrity_error(integrity,'artifact_changed',
                        'selected app changed during testing; see artifact-integrity/changes.json',paths=list(delta))
                clone_case(source, destination / 'artifact-integrity')
            exit_code = suite_run.finish(destination, owner['run_id'], owner['started_at_unix_ms'], invocations, plan, integrity)
            run = read(destination / 'run.json')
            try:
                battery = release_accept.battery_problems(run, Path(plan['configuration']['app_dir']),
                    expected=plan['execution_contract'], evidence=destination)
            except (OSError, ValueError, KeyError, TypeError) as error:
                battery = ['reader refused producer contract: ' + str(error)]
    # Derived summaries are opened here only as comparison targets.
    target = read(evidence / 'run.json')
    actual = semantic_run(run)
    target_semantics = semantic_run(target)
    semantic_differences = differences(actual, target_semantics)
    families = {case['id']:read(destination / 'suites' / case['id'] / 'family.json')
                for case in plan['cases'] if case.get('engine') == 'pytest'}
    summary = dict(schema_version=1, investigation='raw reporting replay', reader=stamp,
        input=str(evidence), output=str(destination), source_run_id=owner['run_id'],
        raw_input_files=raw_files, command_accounts=commands, exit_code=exit_code,
        battery_problems=battery, semantic=actual,
        target_differences=semantic_differences,
        family_target_differences=[name for name in families if families[name] != family_targets[name]],
        limits=['No dependency gate execution; use dispatcher fixtures.',
                'No reconstruction of erased event/report history.',
                'No current resource or release-acceptance claim.',
                'Reader finish wall time is new; original command times and identities are unchanged.'])
    write(destination / 'replay.json', summary)
    # Verify all copied source bytes used by the replay stayed unchanged.
    for name, value in raw_files.items():
        expected = value if isinstance(value,str) else value.get('sha256')
        if expected is not None and sha(evidence / name) != expected:
            raise ValueError('source evidence changed during replay: ' + name)
        if isinstance(value,dict) and 'symlink' in value:
            path = evidence / name
            if not path.is_symlink() or str(path.readlink()) != value['symlink']:
                raise ValueError('source evidence symlink changed during replay: ' + name)
    return summary


def compare(left, right, destination):
    a, b = read(left / 'replay.json'), read(right / 'replay.json')
    if a['raw_input_files'] != b['raw_input_files'] or a['command_accounts'] != b['command_accounts']:
        raise ValueError('replays did not consume identical raw records and command observations')
    changed = differences(a['semantic'], b['semantic'])
    value = dict(left=str(left),right=str(right),same_raw_inputs=True,
                 semantic_differences=changed, exit_codes=[a['exit_code'],b['exit_code']],
                 battery_problems=[a['battery_problems'],b['battery_problems']],
                 agrees=not changed and a['exit_code']==b['exit_code'] and a['battery_problems']==b['battery_problems'])
    write(destination,value)
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    commands=parser.add_subparsers(dest='command',required=True)
    capture=commands.add_parser('snapshot')
    capture.add_argument('repository',type=Path);capture.add_argument('revision');capture.add_argument('destination',type=Path)
    run=commands.add_parser('replay')
    run.add_argument('reader',type=Path);run.add_argument('evidence',type=Path);run.add_argument('destination',type=Path)
    comparison=commands.add_parser('compare')
    comparison.add_argument('left',type=Path);comparison.add_argument('right',type=Path);comparison.add_argument('destination',type=Path)
    args=parser.parse_args()
    try:
        if args.command=='snapshot': print(snapshot(args.repository,args.revision,args.destination))
        elif args.command=='replay':
            result=replay(args.reader,args.evidence,args.destination)
            print(json.dumps({k:result[k] for k in ('exit_code','battery_problems','target_differences','family_target_differences')}))
        else:
            result=compare(args.left,args.right,args.destination)
            print(json.dumps(result));return 0 if result['agrees'] else 1
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
        parser.exit(2,'reporting replay: '+str(error)+'\n')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
