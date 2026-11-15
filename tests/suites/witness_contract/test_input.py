#!/usr/bin/env python3
"""Acquire the selected publisher and retain independently sampled owned passages."""
import copy
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile

import check_test_input as checker
from file_observation import observe_target
from worker_exit_witness import worker_exit_witness

LITERAL_TARGET = '/private/tmp/$EFFECT quote" backslash\\ café'


def invoke(directory, name, argv):
    directory = Path(directory)
    result = subprocess.run([str(arg) for arg in argv], capture_output=True)
    (directory / (name + '.command.json')).write_text(checker.encode([str(arg) for arg in argv]))
    (directory / (name + '.stdout')).write_bytes(result.stdout)
    (directory / (name + '.stderr')).write_bytes(result.stderr)
    (directory / (name + '.exit')).write_text(str(result.returncode) + '\n')
    return dict(argv=[str(arg) for arg in argv], stdout=result.stdout.decode('utf-8'),
                stderr=result.stderr.decode('utf-8'), exit=result.returncode)


def snapshot_document(path):
    snapshot = json.loads(Path(path).read_text())
    nodes = [node for surface in snapshot['surfaces'] for node in surface['public']['nodes']
             if node['id'] == 'request.specimen.read_input']
    blocks = re.findall(r'```json\n(.*?)\n```', nodes[0]['prose'], re.S) if len(nodes) == 1 else []
    return json.loads(blocks[0]) if len(blocks) == 1 else None


def emit(directory, name, emitter, target):
    return invoke(directory, name, [emitter, 'test-input', 'read', '--target', target])


def gate(directory, publication):
    report = checker.publication(publication)
    (Path(directory) / 'publication.json').write_text(checker.encode(publication))
    (Path(directory) / 'preparation-report.json').write_text(checker.encode(report))
    if not report['ok']:
        raise ValueError('publication preflight failed: ' + repr(sorted(checker.diagnostics(report))))


def start(directory, pw, app, snapshot, paths, *, emitter=None, observer=observe_target):
    """The real preflight path. No sampler or derivative runs before its gate."""
    emitter = emitter or pw
    version = invoke(directory, 'version', [pw, '--version'])
    try:
        listed = plistlib.loads((Path(app) / 'Contents/Info.plist').read_bytes()).get('PWContract')
    except (OSError, ValueError):
        listed = None
    try:
        rendered = snapshot_document(snapshot)
    except (OSError, ValueError, KeyError, TypeError):
        rendered = None
    identity = checker.get(checker.parsed(version['stdout']), 'data', 'contract')
    publication = dict(identity=identity, plist_contract=listed, version=version, snapshot=rendered,
                       targets=dict(a1=paths['A'], a2=paths['A'], b=paths['B'], literal=LITERAL_TARGET), emissions={})
    for name in ('a1', 'a2', 'literal'):
        publication['emissions'][name] = emit(directory, name, emitter, publication['targets'][name])
    gate(directory, publication)
    before = observer(paths['A'], checker.BOUND)
    (Path(directory) / 'initial-before.json').write_text(checker.encode(before))
    return publication, before


def write_in_place(path, payload):
    # Open/truncate the existing inode. All descriptors close before run.
    with open(path, 'r+b') as stream:
        stream.seek(0)
        stream.write(payload)
        stream.truncate()
        stream.flush()
        os.fsync(stream.fileno())


def cleanup_disposition(capture, identity, *, refusal=False, authored_fixture=False):
    """Admitted host reap, or the exact validated pre-launch host refusal."""
    run = capture.get('run') or {}
    envelope = checker.parsed(run.get('stdout'))
    if checker.get(envelope, 'build', 'contract') != identity:
        return False, 'no current-build envelope; worker exit unknown'
    reply = checker.consumer.admitted_reply(envelope, identity, allow_fixture_json=authored_fixture)
    if not isinstance(reply, dict):
        return False, 'no identity-admitted host reply; worker exit unknown'
    witnessed, reason = worker_exit_witness(dict(data=dict(runner_result=reply)))
    if witnessed:
        return witnessed, reason
    if refusal:
        failure = dict(code='unknown_field', path=['policy', checker.UNKNOWN])
        errors = checker.consumer.validate(envelope, identity, allow_fixture_json=authored_fixture)
        if not errors and checker.exact(run.get('exit'), 1) and \
                checker.get(envelope, 'result', 'normalized_outcome') == 'bad_request' and \
                checker.get(envelope, 'data', 'request_failure') == failure and \
                reply.get('request_failure') == failure and reply.get('normalized_outcome') == 'bad_request' and \
                reply.get('runner_subprocess') is None and reply.get('validator_subprocess') is None and \
                reply.get('steps') == [] and reply.get('phases') == [] and not reply.get('actors'):
            return True, 'validated exact host unknown-field refusal before worker or validator launch'
    return False, reason



def crossed_gate(directory, state, *, authored_fixture=False):
    """Only the same acquisition's established matrix permits the actor derivative."""
    report = checker.evaluate(state, authored_fixture=authored_fixture)
    rows = [row for row in report['rows'] if row['id'].startswith(('crossed.', 'distinction.crossed.'))]
    passed = bool(rows) and all(row['status'] == 'passed' for row in rows)
    (Path(directory) / 'crossed-gate.json').write_text(checker.encode(dict(ok=passed, rows=rows)))
    if not passed:
        raise ValueError('crossed native expectations failed; returning form not submitted')


def run_case(directory, pw, app, snapshot):
    directory = Path(directory)
    directory.mkdir(parents=True)
    # The dispatcher inspects this case-level receipt before ordinary pruning.
    session_receipt = directory.parent / 'session.json'
    assert not os.path.lexists(session_receipt), 'existing test-input owner requires recovery'
    work = Path(tempfile.mkdtemp(prefix='pw-test-input-', dir='/private/tmp')).resolve(strict=True)
    os.chmod(work, 0o700)
    stat = work.stat()
    ownership = dict(kind='test_input', staging=str(work), artifacts=str(directory.resolve()),
                     session_receipt=str(session_receipt.resolve()),
                     identity=[stat.st_dev, stat.st_ino], attempts=[], removed=False)

    def persist_owner():
        (work / 'ownership.json').write_text(checker.encode(ownership))
        (directory / 'ownership.json').write_text(checker.encode(ownership))
        session_receipt.write_text(checker.encode(ownership))

    persist_owner()
    state = None
    try:
        paths = dict(A=str(work / 'A'), B=str(work / 'B'))
        a, b = Path(paths['A']), Path(paths['B'])
        a.write_bytes(checker.SHORT_0)
        a.chmod(0o600)
        for name, payload in [('short_0', checker.SHORT_0), ('short_1', checker.SHORT_1), ('long', checker.LONG)]:
            (directory / (name + '.bytes')).write_bytes(payload)
        publication, first = start(directory, pw, app, snapshot, paths)
        state = dict(paths=paths, publication=publication, passages={})
        identities = {}

        def save():
            (directory / 'state.json').write_text(checker.encode(state))

        def passage(name, raw, target, before=None):
            dest = directory / name
            dest.mkdir()
            input_path = dest / 'input.json'
            input_path.write_text(raw)
            document = checker.parsed(raw)
            expected = checker.expected_inputs(dict(publication=publication, paths=paths))[name]
            exact_emission = (publication['emissions']['a1']['stdout'] if name in ('initial_a', 'updated_a') else
                              publication['emissions']['b']['stdout'] if name == 'b' else
                              state['passages']['allowed_a']['capture']['input'] if name in checker.REPLACEMENTS else None)
            transformed = document == expected and (exact_emission is None or raw == exact_emission)
            observed_before = before if before is not None else observe_target(target, checker.BOUND)
            (dest / 'before.json').write_text(checker.encode(observed_before))
            payload = checker.payload_for(name)
            fixture = checker.sample_ok(observed_before, target, payload)
            current_identity = (checker.get(observed_before, 'stat', 'st_dev'),
                                checker.get(observed_before, 'stat', 'st_ino'))
            retained = target not in identities or identities[target] == current_identity
            peer = observe_target(paths['B'], checker.BOUND) if name in ('crossed', 'returning') else None
            preflight = dict(transformation=transformed, fixture=fixture, retained_identity=retained)
            if peer is not None:
                preflight['peer'] = checker.sample_ok(peer, paths['B'], checker.LONG) and (peer['stat']['st_dev'], peer['stat']['st_ino']) == identities[paths['B']]

            (dest / 'preflight.json').write_text(checker.encode(preflight))
            assert all(preflight.values()), (name, 'pre-submission conditions failed', preflight)
            identities.setdefault(target, current_identity)
            capture = dict(input=input_path.read_text(), request_path=str(input_path))
            state['passages'][name] = dict(before=observed_before, after=None, capture=capture)
            companions = dict(parked=paths['A'] + '.previous', bystander=paths['B']) if name in checker.REPLACEMENTS else {}
            if name in ('crossed', 'returning'):
                companions['peer'] = paths['B']
            for key, path in companions.items():
                state['passages'][name][key] = dict(before=peer if key == 'peer' else observe_target(path, checker.BOUND), after=None)
            save()
            entry = dict(passage=name, capture=str(dest.resolve()), worker_exit_witnessed=False,
                         witness='submission may be in progress')
            ownership['attempts'].append(entry)
            persist_owner()
            try:
                capture['run'] = invoke(dest, 'run', [pw, 'run', input_path])
            finally:
                observed_after = observe_target(target, checker.BOUND)
                (dest / 'after.json').write_text(checker.encode(observed_after))
                state['passages'][name]['after'] = observed_after
                for key, path in companions.items():
                    state['passages'][name][key]['after'] = observe_target(path, checker.BOUND)
                entry['worker_exit_witnessed'], entry['witness'] = cleanup_disposition(
                    capture, publication['identity'], refusal=name == 'refusal')
                persist_owner()
                save()
            assert entry['worker_exit_witnessed'], ('unresolved native disposition; stop before changing fixtures', entry)

        a_raw = publication['emissions']['a1']['stdout']
        passage('initial_a', a_raw, paths['A'], first)
        write_in_place(a, checker.SHORT_1)
        passage('updated_a', a_raw, paths['A'])
        write_in_place(a, checker.LONG)
        b.write_bytes(checker.LONG)
        b.chmod(0o600)
        publication['emissions']['b'] = emit(directory, 'b', pw, paths['B'])
        gate(directory, publication)
        extended = state['extended_a'] = observe_target(paths['A'], checker.BOUND)
        b_before = observe_target(paths['B'], checker.BOUND)
        equal_fields = ('st_dev', 'st_mode', 'st_uid', 'st_gid', 'st_size')
        pair = dict(a_recipe=checker.sample_ok(extended, paths['A'], checker.LONG),
                    b_recipe=checker.sample_ok(b_before, paths['B'], checker.LONG),
                    retained_a=(checker.get(extended, 'stat', 'st_dev'), checker.get(extended, 'stat', 'st_ino')) == identities[paths['A']],
                    equal_metadata=all(checker.get(extended, 'stat', key) == checker.get(b_before, 'stat', key)
                                       for key in equal_fields),
                    distinct_inodes=checker.get(extended, 'stat', 'st_ino') != checker.get(b_before, 'stat', 'st_ino'))
        (directory / 'pair-preflight.json').write_text(checker.encode(dict(checks=pair, a=extended, b=b_before)))
        save()
        assert all(pair.values()), ('controlled A/B prerequisites failed before B submission', pair)
        b_raw = publication['emissions']['b']['stdout']
        passage('b', b_raw, paths['B'], b_before)
        bad = json.loads(b_raw)
        bad['policy'][checker.UNKNOWN] = True
        passage('refusal', checker.encode(bad), paths['B'])
        repaired = copy.deepcopy(bad)
        del repaired['policy'][checker.UNKNOWN]
        passage('repair', checker.encode(repaired), paths['B'])
        denied = json.loads(b_raw)
        denied['policy']['sbpl_source'] = checker.policy_for(paths['B'])
        passage('denied_b', checker.encode(denied), paths['B'])
        allowed = json.loads(a_raw)
        allowed['policy'] = copy.deepcopy(denied['policy'])
        passage('allowed_a', checker.encode(allowed), paths['A'])
        crossed = json.loads(b_raw)
        crossed['policy'] = copy.deepcopy(denied['policy'])
        template = crossed['probe_plan'][0]
        crossed['probe_plan'] = []
        for ident, operation, queried, attempted in (
                ('read-aa', 'file-read-data', 'A', 'A'), ('read-ab', 'file-read-data', 'A', 'B'),
                ('read-ba', 'file-read-data', 'B', 'A'), ('read-bb', 'file-read-data', 'B', 'B'),
                ('metadata-b', 'file-read-metadata', 'B', 'B')):
            row = copy.deepcopy(template)
            row['step_id'] = ident
            row['sandbox_check']['operation'] = operation
            row['sandbox_check']['filter']['value'] = paths[queried]
            row['attempt']['target'] = paths[attempted]
            crossed['probe_plan'].append(row)
        passage('crossed', checker.encode(crossed), paths['A'])
        crossed_gate(directory, state)
        returning = dict(contract=crossed['contract'], specimen_id=crossed['specimen_id'],
                         actors=[dict(actor_id=actor, equipment='selected',
                                      sandbox=dict(mode='apply', policy=copy.deepcopy(crossed['policy']))) for actor in ('Left', 'Right')],
                         phases=[dict(phase_id=phase, actor_id=actor, actions=copy.deepcopy(crossed['probe_plan'][start:stop]))
                                 for phase, actor, start, stop in (('left-first', 'Left', 0, 2),
                                     ('right-only', 'Right', 2, 3), ('left-second', 'Left', 3, 5))])
        passage('returning', checker.encode(returning), paths['A'])
        original = observe_target(paths['A'], checker.BOUND)
        temporary, previous = Path(paths['A'] + '.replacement'), Path(paths['A'] + '.previous')
        temporary.write_bytes(checker.LONG)
        temporary.chmod(0o600)
        prepared = observe_target(str(temporary), checker.BOUND)
        transition = state['replacement'] = dict(original=original, prepared=prepared, renames=[])
        save()
        assert checker.sample_ok(original, paths['A'], checker.LONG)
        assert (original['stat']['st_dev'], original['stat']['st_ino']) == identities[paths['A']]
        assert checker.sample_ok(prepared, str(temporary), checker.LONG)
        assert all(original['stat'][k] == prepared['stat'][k] for k in equal_fields)
        assert prepared['stat']['st_ino'] not in (original['stat']['st_ino'], b_before['stat']['st_ino'])
        for src, dst in ((a, previous), (temporary, a)):
            src.rename(dst)
            transition['renames'].append([str(src), str(dst)])
            save()
        identities[paths['A']] = (prepared['stat']['st_dev'], prepared['stat']['st_ino'])
        saved = state['passages']['allowed_a']['capture']['input']
        passage('replaced_a', saved, paths['A'])
        for name, payload in (('suffix_a', checker.PREFIX + b'e'), ('empty_a', b''), ('bound_a', checker.PREFIX)):
            write_in_place(a, payload)
            passage(name, saved, paths['A'])
        report = checker.evaluate(state)
        checker.write_report(directory, report)
        assert report['ok'], 'test-input observations did not meet independently pinned expectations'
        # Count what was recorded: each invocation left its argv beside its output.
        commands = {str(p.relative_to(directory)): json.loads(p.read_text())[1:]
                    for p in sorted(directory.rglob('*.command.json'))}
        verbs = [argv[0] for argv in commands.values()]
        refused = [name for name in checker.PASSAGES if state['passages'][name]['capture']['run']['exit'] != 0]
        accounting = dict(submissions=verbs.count('run'), execution_passages=verbs.count('run') - len(refused),
                          refusals=len(refused), publication_commands=verbs.count('test-input'),
                          version_commands=verbs.count('--version'), commands=sorted(commands), owned_directory=str(work),
                          cleanup='owned directory after witnessed exits or exact host refusal')
        (directory / 'accounting.json').write_text(checker.encode(accounting))
        counted = {key: accounting[key] for key in ('submissions', 'execution_passages', 'refusals',
                                                    'publication_commands', 'version_commands')}
        assert counted == dict(submissions=13, execution_passages=12, refusals=1, publication_commands=4,
                               version_commands=1) and len(commands) == 18, accounting
    finally:
        cleanup_safe = all(entry['worker_exit_witnessed'] for entry in ownership['attempts'])
        try:
            observed = work.lstat()
            same_directory = not work.is_symlink() and work.is_dir() and \
                [observed.st_dev, observed.st_ino] == ownership['identity'] and work.parent == Path('/private/tmp')
        except OSError as error:
            same_directory = False
            ownership['cleanup_error'] = str(error)
        if cleanup_safe and same_directory:
            shutil.rmtree(work)
            ownership['removed'] = True
        else:
            ownership['recovery'] = 'Confirm every unwitnessed worker exit and this directory identity before removing the exact owned staging directory.'
            if same_directory:
                persist_owner()
        (directory / 'cleanup.json').write_text(checker.encode(ownership))
        (directory / 'ownership.json').write_text(checker.encode(ownership))
        session_receipt.write_text(checker.encode(ownership))
        if not cleanup_safe or not same_directory:
            raise AssertionError('test-input staging retained after unknown cleanup: ' + str(work))
    return state


if __name__ == '__main__':
    run_case(*sys.argv[1:])
