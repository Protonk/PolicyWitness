"""Execute selected guide fences and retain their commands, outcomes and ownership.

The source reader selects displayed shell blocks; it is not a shell parser.
Explicit cut points put ownership and observations before the affected command.
The only substitutions are the three setup values APP, IDENTITY and ENT.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shlex
import shutil
import stat
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'docs'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/byoxpc'))
import build_context
import consumer
import markdown_reader
import session
from bundle import command, inventory, save
from worker_exit_witness import worker_exit_witness

VARIABLES = ('APP', 'PW', 'PW_WORK', 'PW_CONTRACT', 'PW_NONCE',
             'IDENTITY', 'ENT', 'PW_RUNNER_STAGE', 'BYO', 'SERVICE', 'PW_EXIT')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replace_once(text, before, after):
    assert text.count(before) == 1, ('guide setup substitution is ambiguous', before)
    return text.replace(before, after)


class Guide:
    def __init__(self, text, name):
        self.document = markdown_reader.Document(text, name)
        self.used = []

    def fence(self, section, needle):
        scope = self.document.section(section)
        assert scope is not None, ('guide section missing', section)
        blocks = [b for b in self.document.fences('sh') if scope.holds(b.lines) and needle in b.content]
        assert len(blocks) == 1, ('guide fence missing or ambiguous', section, needle, len(blocks))
        block = blocks[0]
        self.used.append(dict(section=section, lines_1_based=[block.lines[0] + 1, block.lines[1]],
                              sha256=sha(block.content.encode()), raw=block.content))
        return block.content


def split(text, markers):
    """Exact source-preserving fragments, with each named cut required once."""
    positions = [0]
    for marker in markers:
        assert text.count(marker) == 1, ('guide cut missing or ambiguous', marker)
        positions.append(text.index(marker))
    positions.append(len(text))
    assert positions == sorted(set(positions)), ('guide cuts are out of order', markers)
    parts = [text[a:b] for a, b in zip(positions, positions[1:])]
    assert ''.join(parts) == text
    return parts


def check_guide_copy(source, destination, out):
    """Require coherent copied contents and owner access under private staging."""
    original, copied = inventory(source), inventory(destination)
    expected = {}
    for name, entry in original.items():
        masked = dict(entry, mode=entry['mode'] & ~0o077)
        if stat.S_ISREG(entry['mode']):
            expected[name] = [masked]
        elif stat.S_ISDIR(entry['mode']):
            expected[name] = [entry, masked]
        else:
            expected[name] = [entry]
    differences = {name: dict(expected=expected.get(name), observed=copied.get(name))
                   for name in sorted(expected.keys() | copied.keys())
                   if copied.get(name) not in expected.get(name, [])}
    aliases = [name for name in sorted(original.keys() & copied.keys())
               if (destination / name).samefile(source / name)]
    save(out.with_suffix('.inventories.json'), dict(source=original, copied=copied))
    save(out.with_suffix('.comparison.json'), dict(
        mode_rule='regular files: source mode masked by 077; directories: source mode or source mode masked by 077; links: source mode',
        differences=differences, source_aliases=aliases))
    assert not differences, ('guide copy changed content, type, path or expected mode', differences)
    assert not aliases, ('guide copy aliases selected source', aliases)


def workspace(state):
    path = Path(state['workspace'])
    assert path.parent == Path('/private/tmp') and re.fullmatch(r'pw-guide\.[A-Za-z0-9]+', path.name), path
    assert path.resolve() == path and path.is_dir() and not path.is_symlink(), path
    identity = path.stat()
    assert [identity.st_dev, identity.st_ino] == state['workspace_identity'], 'workspace identity changed'
    assert Path(state['state_path']) == path / 'session.json'
    return path


def persist(state, out):
    session.persist_state(state, out / 'session.json')


def file_observation(path):
    if not os.path.lexists(path):
        return dict(path=str(path), present=False)
    observed = path.lstat()
    value = dict(path=str(path), present=True, device=observed.st_dev, inode=observed.st_ino,
                 mode=stat.S_IMODE(observed.st_mode), regular=stat.S_ISREG(observed.st_mode), size=observed.st_size)
    if value['regular']:
        value['sha256'] = sha(path.read_bytes())
    return value


def safe_disposition(path, expected_contract, admission_refusal=False):
    value = json.loads(path.read_bytes())
    assert value['build']['contract'] == expected_contract
    assert value['kind'] in ('run', 'runner_verify')
    inspected = value if value['kind'] == 'run' else value['data']['runner_result']
    errors = consumer.validate(inspected, expected_contract)
    assert not errors, errors
    witnessed, reason = worker_exit_witness(value)
    if witnessed:
        return dict(witnessed=True, reason=reason)
    runner = value.get('data', {}).get('runner_result')
    if admission_refusal and isinstance(runner, dict):
        assert value['result']['normalized_outcome'] == runner['normalized_outcome'] == 'bad_request'
        assert runner.get('runner_subprocess') is None and runner['steps'] == []
        assert all(p.get('validator_subprocess') is None for p in runner.get('phases', []))
        assert runner.get('request_failure') == value['data']['request_failure']
        assert runner['request_failure']['code'] in ('unknown_field', 'invalid_capture_nonce')
        return dict(witnessed=True, reason='host admission refusal before worker and validator creation')
    raise AssertionError((str(path), reason))


def copy_work_records(work, out):
    destination = out / 'work-records'
    destination.mkdir(exist_ok=True)
    copied = {}
    for path in work.iterdir():
        if path.is_file() and not path.is_symlink():
            shutil.copy2(path, destination / path.name)
            copied[path.name] = sha(path.read_bytes())
    save(out / 'work-records.json', copied)


WORK_CORE = ('kind', 'source_app', 'source_inventory', 'workspace', 'workspace_identity',
             'state_path', 'receipt_path', 'contract')


def external_owner(state, out):
    """Recover only the stage already armed in this workflow's durable owner."""
    expected = state.get('external')
    receipt = out / 'byoxpc-session.json'
    if expected is None:
        assert not os.path.lexists(receipt), 'unrecorded external owner'
        return None
    work = Path(state['workspace'])
    assert expected['workspace'] == str(work) and expected['workspace_identity'] == state['workspace_identity']
    assert expected['source_app'] == state['source_app'] and expected['source_inventory'] == state['source_inventory']
    stage = Path(expected['staging'])
    assert stage.parent == work and expected['state_path'] == str(stage / 'session.json')
    assert expected['receipt_path'] == str(receipt)
    durable = Path(expected['state_path'])
    if os.path.lexists(receipt):
        actual = session.owner_object(receipt)
    elif os.path.lexists(durable):
        actual = session.owner_object(durable)
        assert session.guide_core(actual) == expected, 'durable stage differs from armed ownership'
        session.owned_bundle(actual)
        save(receipt, actual)
    else:
        # Adoption arms the parent before writing the child owner and before
        # copy/sign/install. Only the exact still-empty stage can be retired.
        actual = dict(expected, install_attempted=False, install_finished=False, removed=False)
        session.owned_bundle(actual)
        assert not any(stage.iterdir()), 'missing external owner for nonempty stage'
        session.persist_state(actual, receipt)
    assert session.guide_core(actual) == expected, 'external owner belongs to another workflow'
    session.owned_bundle(actual)
    return receipt


def cleanup(pw, out, *, invoke=command, remove_tree=shutil.rmtree):
    receipt = out / 'session.json'
    if not os.path.lexists(receipt):
        return
    state = session.owner_object(receipt)
    assert state['kind'] == 'guide_workflow' and state['receipt_path'] == str(receipt)
    if state.get('removed'):
        assert not os.path.lexists(state['workspace']), 'removed workspace reappeared'
        if state.get('cleanup_error'):
            assert state.get('cleanup_verified'), 'removed owner retains an unverified cleanup error'
            state.pop('cleanup_error')
            save(receipt, state)
        return
    if not os.path.lexists(state['workspace']):
        assert state.get('cleanup_verified'), 'workspace disappeared before cleanup was verified'
        state['removed'] = True
        state.pop('cleanup_error', None)
        save(receipt, state)
        return
    work = workspace(state)
    durable_path = work / 'session.json'
    if not os.path.lexists(durable_path):
        assert state.get('cleanup_verified') and not any(work.iterdir()), 'unverified or nonempty workspace lost its owner'
        work.rmdir()
        state['removed'] = True
        state.pop('cleanup_error', None)
        save(receipt, state)
        return
    durable = session.owner_object(durable_path)
    workspace(durable)
    assert {k: durable[k] for k in WORK_CORE} == {k: state[k] for k in WORK_CORE}, 'durable work ownership disagrees with receipt'
    if state.get('external') is not None:
        assert durable.get('external') == state['external'], 'armed external ownership changed'
    state = durable  # Its mutable journal can be ahead of the artifact copy.
    try:
        if not state.get('cleanup_verified'):
            copy_work_records(work, out)
            assert not state.get('command_uncertain'), 'harness interruption: retain workspace and runner ownership'
            exits = {row['name']: safe_disposition(work / row['output'], state['contract'], row['admission_refusal'])
                     for row in state['invocations']}
            save(out / 'worker-cleanup-witnesses.json', exits)
            byoxpc = external_owner(state, out)
            if byoxpc is not None:
                session.cleanup(pw, byoxpc, invoke=invoke, remove_tree=remove_tree)
            after = inventory(Path(state['source_app']))
            save(out / 'source-after.json', after)
            assert after == state['source_inventory'], 'guide workflow changed selected app'
            state['cleanup_verified'] = True
            state.pop('cleanup_error', None)
            persist(state, out)
            copy_work_records(work, out)
        # Every machine resource was resolved before entering this phase.
        # Keep the durable record until every other owned child is gone.
        for child in sorted(work.iterdir()):
            if child == durable_path:
                continue
            if child.is_dir() and not child.is_symlink():
                remove_tree(child)
            else:
                child.unlink()
        durable_path.unlink()
        work.rmdir()
        state['removed'] = True
        state.pop('cleanup_error', None)
        save(receipt, state)
    except BaseException as error:
        state['cleanup_error'] = str(error)
        if work.exists():
            persist(state, out)
        else:
            save(receipt, state)
        raise RuntimeError(f'guide cleanup pending: {work}: {error}') from error


class Workflow:
    def __init__(self, app, identity, out):
        assert not os.path.lexists(out / 'session.json'), 'existing guide owner must be recovered before another run'
        self.app, self.identity, self.out = app.resolve(), identity, out
        self.pw = self.app / 'Contents/MacOS/policy-witness'
        self.state_file = out / 'shell-state.sh'
        self.values_file = out / 'shell-values'
        self.state = None
        self.number = 0
        self.contract = build_context.candidate_contract(self.app)
        self.env = dict(os.environ)
        assert 'PW_RUNNER_REGISTRY' not in self.env, 'guide workflow uses the displayed default registry'
        for key in ('BASH_ENV', 'ENV'):
            self.env.pop(key, None)
        self.values = {}
        source = ROOT / 'docs/PolicyWitness.md'
        staged = self.app.parent / 'PolicyWitness.md'
        assert staged.is_file() and source.read_bytes() == staged.read_bytes(), 'selected app has a different staged guide'
        shutil.copy2(source, out / 'PolicyWitness.md')
        self.guide = Guide(source.read_text(), str(source))
        self.source_inventory = inventory(self.app)
        save(out / 'source-before.json', self.source_inventory)
        save(out / 'inputs.json', dict(app=str(self.app), pw=str(self.pw), identity=identity,
             contract=self.contract, guide=str(source), staged_guide=str(staged), guide_sha256=sha(source.read_bytes()),
             interpreter='/bin/bash', substitutions=['APP', 'IDENTITY', 'ENT']))

    def run(self, name, text, *, timeout=90):
        self.number += 1
        directory = self.out / 'commands' / f'{self.number:02}-{name}'
        directory.mkdir(parents=True)
        script = directory / 'fragment.sh'
        # No errexit: the displayed refusal recipes deliberately invoke exit 1.
        # Save the fragment status before bookkeeping can replace it.
        prefix = ('source ' + shlex.quote(str(self.state_file)) + '\n') if self.state_file.exists() else ''
        if name == 'copy-runner':
            prefix += 'type -a cp > ' + shlex.quote(str(directory / 'copy-command-resolution.txt')) + ' 2>&1\n'
        suffix = ('\nPW_GUIDE_FRAGMENT_STATUS=$?\n'
                  '{ for PW_GUIDE_VAR in ' + ' '.join(VARIABLES) + '; do\n'
                  '  declare -p "$PW_GUIDE_VAR" 2>/dev/null || :\n'
                  'done; printf \'umask \'; umask; } > ' + shlex.quote(str(self.state_file)) + '\n'
                  ': > ' + shlex.quote(str(self.values_file)) + '\n'
                  'for PW_GUIDE_VAR in ' + ' '.join(VARIABLES) + '; do\n'
                  '  printf \'%s\\0%s\\0\' "$PW_GUIDE_VAR" "${!PW_GUIDE_VAR}" >> ' + shlex.quote(str(self.values_file)) + '\n'
                  'done\nexit "$PW_GUIDE_FRAGMENT_STATUS"\n')
        script.write_text(prefix + text + suffix)
        (directory / 'guide-fragment.sh').write_text(text)
        save(self.out / 'guide-fences.json', self.guide.used)
        if self.state:
            self.state['command_uncertain'] = name
            persist(self.state, self.out)
        result = command(directory / 'capture', ['/bin/bash', script], check=False, timeout=timeout, env=self.env)
        if self.state:
            self.state['command_uncertain'] = None
            persist(self.state, self.out)
        assert result['returncode'] == 0, (name, result)
        raw = self.values_file.read_bytes().split(b'\0')
        assert raw[-1] == b'' and len(raw[:-1]) == 2 * len(VARIABLES)
        self.values = {key.decode(): value.decode() for key, value in zip(raw[:-1:2], raw[1:-1:2])}
        return result

    def own_work(self):
        work = Path(self.values['PW_WORK'])
        assert work.is_dir() and not any(work.iterdir()), 'guide workspace must be new and empty'
        observed = work.stat()
        self.state = dict(kind='guide_workflow', source_app=str(self.app), source_inventory=self.source_inventory,
                          workspace=str(work), workspace_identity=[observed.st_dev, observed.st_ino],
                          state_path=str(work / 'session.json'), receipt_path=str(self.out / 'session.json'),
                          contract=self.contract, invocations=[], command_uncertain=None, external=None, removed=False)
        workspace(self.state)
        persist(self.state, self.out)
        self.work = work

    def observe(self, name, target, present):
        value = file_observation(self.work / target)
        save(self.out / (name + '.json'), value)
        assert value['present'] is present, value
        if present:
            assert value['regular'] and value['size'] == 0 and value['mode'] == 0o600, value
        return value

    def invoke(self, name, text, output, *, admission_refusal=False):
        request = self.work / (name + '.json') if name != 'verify' else None
        original = request.read_bytes() if request else None
        self.state['invocations'].append(dict(name=name, output=output, admission_refusal=admission_refusal,
                                             request_sha256=sha(original) if original is not None else None))
        persist(self.state, self.out)
        self.run(name, text)
        if request:
            assert request.read_bytes() == original, 'request changed during guide invocation'
        safe_disposition(self.work / output, self.contract, admission_refusal)

    def envelope(self, name, kind, rc=None):
        value = json.loads((self.work / (name + '.json')).read_bytes())
        assert value['kind'] == kind and value['build']['contract'] == self.contract, value
        if rc is not None:
            assert int((self.work / (name.replace('-result', '') + '-exit.txt')).read_text()) == rc
            assert value['result']['ok'] is (rc == 0), value
        return value

    def created(self, name, target):
        value = self.envelope(name + '-result', 'run', 0)
        errors = consumer.validate(value, self.contract)
        assert not errors, errors
        runner = value['data']['runner_result']
        assert runner['normalized_outcome'] == 'finished' and runner['sandboxed_after_apply'] is True, runner
        assert len(runner['steps']) == 1 and runner['steps'][0]['step_id'] == 'create', runner
        attempt = runner['steps'][0]['attempt']
        assert attempt['requested_action'] == 'create' and attempt['requested_path'] == str(self.work / target), attempt
        assert attempt['outcome'] == 'ok' and attempt['rc'] == 0, attempt
        self.observe(name + '-independent-after', target, True)
        return value, runner

    def refuse(self, name, code, field):
        value = self.envelope(name + '-result', 'run', 1)
        expected = dict(code=code, path=['policy', field])
        assert value['data']['request_failure'] == expected, value
        assert value['data']['runner_result']['request_failure'] == expected
        self.observe(name + '-independent-after', 'capture-target', False)

    def requests(self):
        # Each displayed repair preserves the prior JSON bytes and changes one
        # actual policy prerequisite, apart from the initial new effect target.
        names = ['create', 'capture-typo', 'capture-no-nonce', 'capture', 'byoxpc-create']
        values = {name: json.loads((self.work / (name + '.json')).read_bytes()) for name in names}
        assert all(value['contract'] == self.contract for value in values.values())
        typo = json.loads(json.dumps(values['capture-typo']))
        typo['policy']['capture_compiled_profile'] = typo['policy'].pop('capture_compiled_profiel')
        assert typo == values['capture-no-nonce']
        typo['policy']['capture_nonce'] = self.values['PW_NONCE']
        assert typo == values['capture']
        save(self.out / 'request-hashes.json', {name: sha((self.work / (name + '.json')).read_bytes()) for name in names})

    def perform(self):
        quick = self.guide.fence('Quick start', 'APP="/Applications/PolicyWitness.app"')
        quick = replace_once(quick, 'APP="/Applications/PolicyWitness.app"', 'APP=' + shlex.quote(str(self.app)))
        setup, version, contract, shown = split(quick, ['"$PW" --version', 'PW_CONTRACT=', "printf 'Contract:"])
        self.run('prepare-work', setup)
        self.own_work()
        self.run('version', version)
        version_value = json.loads((self.work / 'version.json').read_bytes())
        assert version_value['build']['contract'] == self.contract
        self.run('contract', contract)
        assert self.values['PW_CONTRACT'] == self.contract
        self.run('show-contract', shown)
        self.observe('create-independent-before', 'created', False)
        create = self.guide.fence('Quick start', 'cat > "$PW_WORK/create.json"')
        prepare, execute = split(create, ['if test ! -e'])
        self.run('create-request', prepare)
        original_create = (self.work / 'create.json').read_bytes()
        self.invoke('create', execute, 'create-result.json')
        self.created('create', 'created')
        saved = {name: (self.work / name).stat().st_mtime_ns for name in ('create-result.json', 'create-exit.txt')}
        result_bytes = (self.work / 'create-result.json').read_bytes()
        effect_before = file_observation(self.work / 'created')
        self.run('create-existing-target-guard', execute)
        assert (self.work / 'create-result.json').read_bytes() == result_bytes
        assert {name: (self.work / name).stat().st_mtime_ns for name in saved} == saved
        assert file_observation(self.work / 'created') == effect_before
        save(self.out / 'existing-target-guard.json', dict(result_unchanged=True, effect_unchanged=True, saved_mtime_ns=saved))
        for name, needle, code, field in [
            ('capture-typo', '> "$PW_WORK/capture-typo.json"', 'unknown_field', 'capture_compiled_profiel'),
            ('capture-no-nonce', "sed 's/capture_compiled_profiel/", 'invalid_capture_nonce', 'capture_nonce')]:
            text = self.guide.fence('Try an accepted request and a refusal', needle)
            prepare, execute = split(text, ['"$PW" run'])
            self.run(name + '-request', prepare)
            original = (self.work / (name + '.json')).read_bytes()
            self.observe(name + '-independent-before', 'capture-target', False)
            self.invoke(name, execute, name + '-result.json', admission_refusal=True)
            self.refuse(name, code, field)
            assert (self.work / (name + '.json')).read_bytes() == original
        nonce = self.guide.fence('Try an accepted request and a refusal', 'PW_NONCE=$(')
        generate, display = split(nonce, ["printf '%s\\n'"])
        self.run('nonce', generate)
        assert re.fullmatch('[0-9a-f]{32}', self.values['PW_NONCE'])
        self.run('show-nonce', display)
        capture = self.guide.fence('Try an accepted request and a refusal', 'capture-no-nonce.json" > "$PW_WORK/capture.json')
        prepare, execute = split(capture, ['if test ! -e'])
        self.run('capture-request', prepare)
        self.observe('capture-independent-before', 'capture-target', False)
        self.invoke('capture', execute, 'capture-result.json')
        _, runner = self.created('capture', 'capture-target')
        profile = runner['compiled_profile']
        assert profile['status'] == 'captured', ('healthy capture workflow needs its positive receipt', profile)
        assert profile['producer'] == 'worker' and profile['capture_stage'] == 'before_apply'
        assert profile['request_nonce'] == self.values['PW_NONCE']
        assert profile['worker_pid'] == runner['runner_subprocess']['pid']
        raw = base64.b64decode(profile['bytecode_b64'], validate=True)
        assert len(raw) == profile['bytecode_length'] > 0 and sha(raw) == profile['bytecode_sha256']
        source = json.loads((self.work / 'capture.json').read_bytes())['policy']['sbpl_source'].encode()
        assert profile['source_sha256'] == sha(source) and profile['source_length'] == len(source)
        assert profile['parameter_count'] == 0
        save(self.out / 'compiled-object-observation.json', dict(length=len(raw), sha256=sha(raw), worker_pid=profile['worker_pid']))
        helper = self.guide.fence('SBPL check (sbpl-check)', '"$APP/Contents/MacOS/sbpl-check"')
        before = {p.name: file_observation(p) for p in [self.work / 'created', self.work / 'capture-target']}
        self.run('helper', helper)
        helper_value = self.envelope('compile-result', 'sbpl_check', 0)
        assert helper_value['data']['compile'] == dict(stage='compile', ok=True, error=None)
        assert helper_value['data']['policy_sha256'] == sha(source)
        after = {p.name: file_observation(p) for p in [self.work / 'created', self.work / 'capture-target']}
        save(self.out / 'helper-file-observations.json', dict(before=before, after=after))
        assert before == after
        assert (self.work / 'create.json').read_bytes() == original_create
        self.external()
        self.requests()
        save(self.out / 'guide-fences.json', self.guide.used)
        save(self.out / 'workflow-result.json', dict(commands_and_assertions_complete=True, contract=self.contract,
            guide_sha256=sha((self.out / 'PolicyWitness.md').read_bytes()),
            native_workflows=['create', 'capture-refusal-repair', 'helper', 'byoxpc-lifecycle'],
            interpretation_evidence='separate constructed reader corpus', capture_status=profile['status']))

    def external(self):
        text = self.guide.fence('External runners (BYOXPC)', '"$PW" runner list > "$PW_WORK/runners-before.json"')
        listed, reconciled = split(text, ['"$PW" runner reconcile'])
        self.run('list-before', listed)
        self.run('reconcile-before', reconciled)
        prior = self.envelope('runners-before', 'runner_registry')['data']
        assert prior['runners'] == [] and prior.get('pending_cleanup', []) == [], \
            'guide workflow needs an empty default registry: validate refreshes every installed record'
        self.envelope('reconcile-before', 'runner_reconcile')
        source_bundle = self.app / 'Contents/XPCServices/PWRunner.xpc'
        selected = session.entitlements(source_bundle / 'Contents/MacOS/pw-probe-runner', self.out, 'selected-entitlements', command)
        assert selected is None or isinstance(selected, dict)
        entitlement_path = self.work / 'selected-entitlements.plist'
        entitlement_path.write_bytes(plistlib.dumps(selected or {}))
        text = self.guide.fence('Install a BYOXPC runner', 'IDENTITY="Developer ID Application: Your Name (TEAMID)"')
        text = replace_once(text, 'IDENTITY="Developer ID Application: Your Name (TEAMID)"', 'IDENTITY=' + shlex.quote(self.identity))
        text = replace_once(text, 'ENT="/absolute/path/to/your-entitlements.plist"', 'ENT=' + shlex.quote(str(entitlement_path)))
        setup, copied, metadata, signed = split(text, ['cp -R ', '/usr/libexec/PlistBuddy ', '/usr/bin/codesign '])
        self.run('prepare-runner', setup)
        session.adopt_guide(self.app, self.out / 'byoxpc-session.json', self.state,
                            Path(self.values['PW_RUNNER_STAGE']), Path(self.values['BYO']), self.values['SERVICE'])
        byostate = json.loads((self.out / 'byoxpc-session.json').read_text())
        assert not any(r['service_name'] == byostate['service_name'] for r in session.registry(self.pw, self.out, 'owned-registry-before', command))
        assert not os.path.lexists(byostate['plist_path'])
        assert not session.service_present(byostate, self.out, 'owned-service-before', command)
        self.run('copy-runner', copied)
        destination = Path(self.values['BYO'])
        check_guide_copy(source_bundle, destination, self.out / 'copied-runner')
        self.run('name-runner', metadata)
        self.run('sign-runner', signed)
        install = self.guide.fence('Install a BYOXPC runner', '"$PW" runner install --bundle')
        installed, listed, reconciled = split(install, ['"$PW" runner list', '"$PW" runner reconcile'])
        byostate['install_attempted'] = True
        session.persist_state(byostate, self.out / 'byoxpc-session.json')
        self.run('install', installed)
        byostate['install_finished'] = True
        session.persist_state(byostate, self.out / 'byoxpc-session.json')
        value = self.envelope('install', 'runner_install', 0)
        record = value['data']['runner']
        assert record['service_name'] == self.values['SERVICE'] and record['scope'] == 'user'
        assert Path(record['bundle_path']) == destination
        assert value['data']['plist_path'] == byostate['plist_path']
        byostate['runner_id'] = record['id']
        session.persist_state(byostate, self.out / 'byoxpc-session.json')
        self.run('list-installed', listed)
        self.run('reconcile-installed', reconciled)
        rows = self.envelope('runners-after-install', 'runner_registry')['data']['runners']
        assert [r['id'] for r in rows if r['service_name'] == self.values['SERVICE']] == [record['id']]
        assert session.service_present(byostate, self.out, 'owned-service-installed', command)
        plist = plistlib.loads(Path(byostate['plist_path']).read_bytes())
        assert plist['Label'] == byostate['service_name']
        assert plist['ProgramArguments'][0] == str(destination / 'Contents/MacOS/PWRunner')
        assert plist['MachServices'] == {byostate['service_name']: True}
        save(self.out / 'installed-plist.json', plist)
        verify = self.guide.fence('Verify the runner', '"$PW" runner status')
        status, verify = split(verify, ['"$PW" runner verify'])
        self.run('status', status)
        status_value = self.envelope('status', 'runner_status')['data']
        assert status_value['id'] == record['id'] and status_value['service_name'] == byostate['service_name']
        self.invoke('verify', verify, 'verify.json')
        value = self.envelope('verify', 'runner_verify', 0)
        runner = value['data']['runner_result']
        assert value['data']['runner_id'] == record['id'] and value['data']['service_name'] == self.values['SERVICE']
        assert runner['bundle_id'] == self.values['SERVICE']
        assert value['data']['normalized_outcome'] == runner['normalized_outcome'] == 'finished'
        assert value['data']['runner_pid'] == runner['pid'] and runner['sandboxed_after_apply'] is True
        assert runner['steps'] == []
        create = self.guide.fence('Use the runner in a specimen', 'guide-byoxpc-create')
        prepare, execute = split(create, ['if test ! -e'])
        self.run('byoxpc-request', prepare)
        self.observe('byoxpc-independent-before', 'byoxpc-created', False)
        self.invoke('byoxpc-create', execute, 'byoxpc-create-result.json')
        _, selected_runner = self.created('byoxpc-create', 'byoxpc-created')
        assert selected_runner['bundle_id'] == self.values['SERVICE']
        finish = self.guide.fence('List, validate, or remove runners', '"$PW" runner validate')
        validate, remove, listed, reconciled = split(finish, ['"$PW" runner remove', '"$PW" runner list', '"$PW" runner reconcile'])
        self.run('validate', validate)
        validation = self.envelope('validate', 'runner_validate', 0)['data']
        assert validation == dict(updated=1, missing=0, invalid=0, failures=[]), validation
        installed_equipment = session.equipment_inventory(destination, self.out, 'independent-installed-equipment', command, expected_contract=self.contract)
        observed_entitlements = session.binary_entitlements(destination, self.out, 'independent-installed', command)
        assert (observed_entitlements['pw-probe-runner'] or {}) == (selected or {})
        assert observed_entitlements['pw-probe-runner-unentitled'] is None
        assert observed_entitlements['sb_api_validator'] is None
        self.run('remove', remove)
        value = self.envelope('remove', 'runner_remove', 0)
        assert not value['data'].get('warnings') and not value['data'].get('cleanup_retained'), value
        self.run('list-removed', listed)
        self.run('reconcile-removed', reconciled)
        rows = self.envelope('runners-after-remove', 'runner_registry')['data']
        all_rows = rows['runners'] + [row.get('runner', row) for row in rows.get('pending_cleanup', [])]
        assert not any(row['service_name'] == self.values['SERVICE'] for row in all_rows)
        self.envelope('reconcile-after-remove', 'runner_reconcile')
        assert not session.service_present(byostate, self.out, 'owned-service-removed', command)
        assert not os.path.lexists(byostate['plist_path'])
        save(self.out / 'independent-runner-removal.json', dict(service_absent=True, plist_absent=True,
             registry_absent=True, service_name=byostate['service_name'], bundle_path=byostate['bundle_path']))


def controls(out):
    """Source extraction refuses ambiguity; ownership refuses replacement/escape."""
    def refuses(fn):
        try:
            fn()
        except (AssertionError, markdown_reader.Refused):
            return
        raise AssertionError('negative guide control was accepted')
    guide = Guide('# Example\n\n```sh\necho original\n```\n', 'constructed')
    raw = guide.fence('Example', 'echo original')
    assert raw == 'echo original\n'
    refuses(lambda: guide.fence('Example', 'missing'))
    duplicate = Guide('# Example\n\n```sh\necho x\n```\n\n```sh\necho x\n```\n', 'constructed')
    refuses(lambda: duplicate.fence('Example', 'echo x'))
    assert split('first\nsecond\nthird\n', ['second\n', 'third\n']) == ['first\n', 'second\n', 'third\n']
    refuses(lambda: split('x\nx\n', ['x\n']))
    refuses(lambda: split('first\nsecond\nthird\n', ['third\n', 'second\n']))
    refuses(lambda: replace_once('APP=x\nAPP=x\n', 'APP=x', 'APP=y'))
    # Construct the copy's expected private-file modes independently of the
    # comparison helper, then keep content and execute-bit failures distinct.
    copy_control = out / 'copy-controls'
    original, copied = copy_control / 'source', copy_control / 'copied'
    original.mkdir(parents=True); copied.mkdir()
    original.chmod(0o755); copied.chmod(0o755)
    for base, mode in ((original, 0o755), (copied, 0o700)):
        (base / 'worker').write_bytes(b'unchanged executable bytes')
        (base / 'worker').chmod(mode)
    check_guide_copy(original, copied, copy_control / 'accepted-directory-0755')
    copied.chmod(0o700)
    check_guide_copy(original, copied, copy_control / 'accepted-directory-0700')
    (copied / 'worker').write_bytes(b'changed executable bytes')
    refuses(lambda: check_guide_copy(original, copied, copy_control / 'changed-content'))
    (copied / 'worker').write_bytes(b'unchanged executable bytes')
    (copied / 'worker').chmod(0o600)
    refuses(lambda: check_guide_copy(original, copied, copy_control / 'missing-execute'))
    # Pure path controls use the helper's guide branch without native commands.
    import secrets
    work = Path('/private/tmp') / ('pw-guide.' + secrets.token_hex(12))
    work.mkdir(mode=0o700)
    try:
        stage = work / 'runner.control'
        stage.mkdir()
        observed, staged = work.stat(), stage.stat()
        state = dict(layout='guide_workflow', workspace=str(work), workspace_identity=[observed.st_dev, observed.st_ino],
                     staging=str(stage), staging_identity=[staged.st_dev, staged.st_ino],
                     bundle_path=str(stage / 'PWRunner.guide.xpc'), service_name=f'com.policywitness.guide.{os.getuid()}.runner.control')
        state['target'] = f'gui/{os.getuid()}/{state["service_name"]}'
        state['plist_path'] = str(Path.home() / 'Library/LaunchAgents' / (state['service_name'] + '.plist'))
        state['registry_path'] = None
        state['state_path'] = str(stage / 'session.json')
        assert session.owned_bundle(state) == (stage, stage / 'PWRunner.guide.xpc')
        for changed in [dict(workspace_identity=[observed.st_dev, observed.st_ino + 1]),
                        dict(staging_identity=[staged.st_dev, staged.st_ino + 1]),
                        dict(bundle_path=str(work / 'other.xpc')), dict(service_name=state['service_name'] + '.other'),
                        dict(plist_path=str(work / 'foreign.plist'))]:
            refuses(lambda changed=changed: session.owned_bundle(dict(state, **changed)))
        (stage / 'PWRunner.guide.xpc').symlink_to(out, target_is_directory=True)
        refuses(lambda: session.owned_bundle(state))
    finally:
        shutil.rmtree(work)
    save(out / 'constructed-controls.json', dict(extraction='accepted exact source; refused missing, duplicate and reordered cuts',
         ownership='accepted exact guide layout; refused changed inode, wrong bundle/service and symlink escape'))


def main():
    mode, app, out = sys.argv[1:4]
    app, out = Path(app), Path(out)
    if mode == 'cleanup':
        cleanup(app / 'Contents/MacOS/policy-witness', out)
        return
    assert mode == 'run' and len(sys.argv) == 5
    controls(out)
    from guide_workflow_ownership_controls import check
    check(out / 'ownership-controls')
    workflow = Workflow(app, sys.argv[4], out)
    try:
        workflow.perform()
    finally:
        # The wrapper repeats this idempotently if the Python process exits.
        cleanup(workflow.pw, out)


if __name__ == '__main__':
    main()
