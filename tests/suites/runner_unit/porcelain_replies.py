"""Replay Swift reporting receipts through the independent binary reader.

These are constructed reporting/codec controls, not observations of native
execution or of a pipe interrupted by the kernel. Prefix controls establish
that an incomplete emitted frame cannot be read as a complete reply.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import porcelain
from contract import WORKER_IDENTITY


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def require_subset(expected, actual, path):
    if isinstance(expected, dict):
        require(isinstance(actual, dict), path + ': expected object')
        for key, value in expected.items():
            if value is None and key not in actual:
                continue  # Authored absent observation; shape checks own null-versus-omission.
            require(key in actual, path + ': missing authored key ' + key)
            require_subset(value, actual[key], path + '.' + key)
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), path + ': array differs')
        for index, value in enumerate(expected):
            require_subset(value, actual[index], path + '[' + str(index) + ']')
    else:
        require(type(actual) is type(expected) and actual == expected, path + ': authored value differs')


def json_bytes(value):
    return len(json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode())


def collect_shape(value, path, shape):
    def kind(item):
        if item is None: return 'null'
        if isinstance(item, bool): return 'boolean'
        if isinstance(item, (int, float)): return 'number'
        if isinstance(item, str): return 'string'
        if isinstance(item, list): return 'array'
        if isinstance(item, dict): return 'object'
        raise AssertionError('unknown JSON type')
    keys = shape.setdefault(path, {})
    for key, child in value.items():
        typ = kind(child)
        old = keys.get(key)
        require(old in (None, 'null', typ) or typ == 'null', 'shape conflict at ' + path + '.' + key)
        if old in (None, 'null'): keys[key] = typ
        if isinstance(child, dict): collect_shape(child, path + '.' + key, shape)
        if isinstance(child, list):
            for item in child:
                if isinstance(item, dict): collect_shape(item, path + '.' + key + '[]', shape)


def replay_paths(artifacts):
    for i in range(3):
        for j in range(3):
            reply = porcelain.decode((artifacts / 'porcelain-paths' / (str(i) + '-' + str(j) + '.pwp')).read_bytes())
            step = reply['steps'][0]
            for object, fields in [(step['sandbox_check']['path_diagnostics'], ('realpath_resolved', 'firmlink_resolved')),
                                   (step['attempt']['path_diagnostics'], ('realpath_resolved', 'parent_realpath_resolved'))]:
                require(object['input'] == '/caf\u00e9', 'path input UTF-8 changed')
                require(object['observer'] == 'runner_host' and object['stage'] == 'after_orchestration', 'path provenance changed')
                expected_same = []
                for field, state in zip(fields, (i, j)):
                    if state == 0:
                        expected_same.append(field)
                        require(field not in object, 'same path was emitted twice')
                    elif state == 1:
                        require(object[field] == '/cafe\u0301', 'canonically equivalent UTF-8 observation was compacted')
                    else:
                        require(field in object and object[field] is None, 'unknown path lost explicit null')
                require(object['same_as_input'] == expected_same, 'path presentation order or byte identity differs')


def replay_dispositions(artifacts):
    directory = artifacts / 'porcelain-disposition'
    conflict = porcelain.decode((directory / 'publication-conflict.pwp').read_bytes())
    require(conflict['runner_subprocess']['disposition']['issues'][0]['rule'] == 'D5', 'publication conflict was dropped')
    rejected = porcelain.decode((directory / 'contradictory-claim.pwp').read_bytes())
    require(rejected['reporting_failure']['evidence_retained'] is True, 'contradictory claim was discarded')
    require(rejected['runner_subprocess']['disposition']['questions']['final_status']['answer'] == 'signal', 'rejected claim rewritten')
    require(rejected['runner_subprocess']['exit_code'] == 0 and rejected['runner_subprocess'].get('term_signal') is None,
            'contradictory raw status rewritten')
    absent = porcelain.decode((directory / 'absent-question.pwp').read_bytes())
    require('final_status' not in absent['runner_subprocess']['disposition']['questions'], 'missing question acquired a default claim')
    require(absent['reporting_failure']['evidence_retained'] is True, 'partial account was discarded')
    wire = (directory / 'unknown-progress.pwp').read_bytes()
    require(wire[:36] == (directory / 'publication-conflict.pwp').read_bytes()[:36], 'subprocess frame differs')
    record_id = next(i for i, row in porcelain.porcelain_schema.RECORDS.items() if row['name'] == 'PWRunnerSubprocess')
    sub, end = porcelain.Reader(wire, porcelain.porcelain_schema.RECORDS).value(36, len(wire), {'record': record_id})
    require(end == len(wire) and sub['worker_evidence']['progress']['operation'] == 200,
            'unknown progress observation did not cross the binary boundary')

REQUIRED_SHAPE = [('reply', 'reporting_failure'), ('reply.steps[].attempt', 'missing_reason'), ('reply.phases[].validator_subprocess', 'term_signal'), ('reply.runner_subprocess', 'exit_code'), ('reply.runner_subprocess', 'term_signal'), ('reply.runner_subprocess', 'policy_transfer_error'), ('reply.runner_subprocess', 'policy_transfer_timeout'), ('reply.runner_subprocess.worker_evidence', 'failure'), ('reply.actors[].subprocess.worker_evidence.failure', 'native_result'), ('reply.actors[].subprocess.worker_evidence.failure', 'errno'), ('reply.actors[].subprocess.worker_evidence.failure', 'index'), ('reply.actors[].subprocess.worker_evidence.progress', 'index'), ('reply.actors[].subprocess', 'term_signal'), ('reply.actors[].subprocess', 'policy_transfer_error'), ('reply.actors[].subprocess', 'policy_transfer_timeout'), ('reply.actors[].subprocess.termination_request', 'signal'), ('reply.actors[].subprocess.termination_request', 'rc'), ('reply.actors[].subprocess.termination_request', 'errno'), ('reply.actors[].subprocess.wait_errors[]', 'stage'), ('reply.actors[].subprocess.wait_errors[]', 'rc'), ('reply.actors[].subprocess.wait_errors[]', 'errno'), ('reply.actors[].subprocess.ready_wait', 'native_errno'), ('reply.actors[].subprocess.disposition.questions.final_status', 'reason'), ('reply.actors[].subprocess.disposition.questions.progress_association', 'reason'), ('reply.actors[].subprocess.disposition.questions.kill_request_and_result.value', 'errno'), ('reply.actors[].subprocess.disposition.steps[].questions.step_boundary_reached', 'reason'), ('reply.actors[].subprocess.disposition.steps[].questions.step_result_published', 'reason'), ('reply.actors[].subprocess.disposition.steps[].questions.step_result_published', 'issue'), ('reply.actors[].subprocess.disposition.issues[]', 'kind'), ('reply.actors[].subprocess.disposition.issues[]', 'rule'), ('reply.actors[].subprocess.disposition.issues[]', 'question'), ('reply.actors[].subprocess.disposition.issues[]', 'step_index'), ('reply.actors[].subprocess.disposition.issues[]', 'observations'), ('reply.actors[].subprocess.disposition.issues[]', 'detail'), ('reply.actors[]', 'compiled_profile'), ('reply.actors[].compiled_profile', 'status'), ('reply.actors[].compiled_profile', 'reason'), ('reply.actors[].compiled_profile', 'worker_pid'), ('reply.actors[].compiled_profile', 'producer'), ('reply.actors[].compiled_profile', 'capture_stage'), ('reply.actors[].compiled_profile', 'request_nonce'), ('reply.actors[].compiled_profile', 'profile_type'), ('reply.actors[].compiled_profile', 'bytecode_length'), ('reply.actors[].compiled_profile', 'bytecode_sha256'), ('reply.actors[].compiled_profile', 'bytecode_b64'), ('reply.actors[].compiled_profile', 'source_sha256'), ('reply.actors[].compiled_profile', 'source_length'), ('reply.actors[].compiled_profile', 'params_sha256'), ('reply.actors[].compiled_profile', 'parameter_count'), ('reply.runner_subprocess.disposition.issues[]', 'rule'), ('reply.runner_subprocess.disposition.steps[].questions.step_result_published', 'issue'), ('reply.runner_subprocess.disposition.steps[].questions.step_result_published', 'reason'), ('reply.runner_subprocess.disposition.steps[].questions.step_boundary_reached', 'reason'), ('reply.steps[].attempt.lifecycle.boundary', 'reason'), ('reply.steps[].attempt.lifecycle.result', 'reason'), ('reply.runner_subprocess.disposition.questions.cleanup_trigger', 'reason'), ('reply.runner_subprocess.disposition.questions.grace_end', 'reason'), ('reply.runner_subprocess.disposition.questions.kill_request_and_result', 'reason')]



def replay_shapes_and_sizes(artifacts):
    directory = artifacts / 'porcelain-shapes'
    documents = [porcelain.decode(path.read_bytes()) for path in sorted(directory.glob('*.pwp'))]
    require(len(documents) >= 30, 'shape companions missing')
    shape = {}
    for document in documents: collect_shape(document, 'reply', shape)
    for path, key in REQUIRED_SHAPE:
        require(shape.get(path, {}).get(key) not in (None, 'null'), path + '.' + key + ' lacks a typed fixture')
    candidate = dict(shape=shape)
    golden = json.loads((ROOT / 'tests/fixtures/contract/response_shape.json').read_text())
    if candidate != golden:
        target = artifacts / 'response_shape.candidate.json'
        target.write_text(json.dumps(candidate, indent=2, sort_keys=True) + '\n')
        raise AssertionError('independent public reply shape differs; review ' + str(target))
    dense = artifacts / 'porcelain-dense'
    account = json.loads((dense / 'accounting-inputs.json').read_text())
    policy, caps = account['string_policy'], account['capacities']
    unknown = set()
    def maximize(value, key=None):
        if isinstance(value, str):
            if key not in policy: unknown.add(key); return value
            return '\x01' * policy[key] if policy[key] is not None else value
        if isinstance(value, list): return [maximize(item, key) for item in value]
        if isinstance(value, dict): return {k: maximize(v, k) for k, v in value.items()}
        return value
    for document in documents: maximize(document)
    require(not unknown, 'unclassified public reply strings: ' + repr(sorted(unknown)))
    maximize({'future_reply_string': 'unclassified'})
    require(unknown == {'future_reply_string'}, 'unknown-string negative control failed')
    unknown.clear()
    sizes = []
    for name in ('ordinary', 'exec', 'fresh-write'):
        wire = (dense / (name + '.pwp')).read_bytes()
        document = porcelain.decode(wire)
        require(len(document['steps']) == caps['steps'] == 256, name + ': dense population missing')
        require(len(document['phases']) == caps['ordinary_phases'] == 8, name + ': phase population missing')
        require(len(wire) < 96_468_992 and len(wire) <= 128 * 1024 * 1024, name + ': binary cap exceeded')
        if name == 'exec':
            require(all(step['attempt'].get('exec_observation') is not None for step in document['steps']), 'dense exec observations missing')
        if name == 'fresh-write':
            require(all(step['attempt'].get('fresh_write') is not None for step in document['steps']), 'dense fresh-write observations missing')
        sizes.append(dict(name=name, binary_bytes=len(wire), public_json_bytes=json_bytes(document)))
    components, allowance = actor_account(documents, policy, caps)
    report = dict(scope='constructed dense binary receipts and conservative public JSON component union',
                  dense=sizes, actor_json_allowance=allowance,
                  limitations=['Dense observations do not prove a global binary maximum.',
                               'The incompatible component union bounds presentation components, not reachable execution or transport memory.'])
    (dense / 'sizes.json').write_text(json.dumps(report, indent=2) + '\n')


def actor_account(documents, policy, caps):
    import base64
    def union(values, path):
        present = [v for v in values if v is not None]
        if not present: return None
        objects = [v for v in present if isinstance(v, dict)]
        if objects:
            result = {key: union([v[key] for v in objects if key in v], path + '.' + key)
                      for key in set().union(*(v.keys() for v in objects))}
            if len(objects) != len(present): require(json_bytes(result) >= 20, 'scalar alternative undercounted')
            return result
        arrays = [v for v in present if isinstance(v, list)]
        if arrays:
            capacities = {'actor.subprocess.disposition.steps': 0, 'actor.subprocess.disposition.issues': 0,
                          'phase.action_ids': 0, 'phase.validator_subprocess.records': 0,
                          'phase.validator_subprocess.expected_step_ids': 0,
                          'phase.validator_subprocess.association_issues': 0,
                          'actor.visits': caps['phases'], 'actor.launch.inherited_descriptors': 4,
                          'actor.subprocess.wait_errors': 5, 'phase.validator_subprocess.wait_errors': 5,
                          'handle.raw_equal_handles': caps['handles'], 'phase.ordering.protocol_violations': 16}
            count = caps['references'] if path.endswith(('.basis', '.observations')) else capacities.get(path)
            require(count is not None, 'unclassified actor reply array capacity: ' + path)
            if count == 0: return []
            require(all(len(v) <= count for v in arrays), 'actor array exceeds its accounted capacity: ' + path)
            elements = [item for array in arrays for item in array]
            if not elements:
                elements = {'phase.ordering.protocol_violations': ['attempt_or_acknowledgement_after_proceed_failure'],
                            'handle.raw_equal_handles': ['\x01' * policy['handle_ref']]}.get(path)
            require(elements, 'actor reply array has no populated fixture: ' + path)
            return [union(elements, path + '[]')] * count
        if isinstance(present[0], bool): return False
        if isinstance(present[0], int): return -(1 << 63)
        if isinstance(present[0], str):
            key = path.rsplit('.', 1)[-1].replace('[]', '')
            require(key in policy, 'unclassified actor string: ' + key)
            if policy[key] is not None: return '\x01' * policy[key]
            if key in ('bytecode_b64', 'context_b64'):
                return base64.b64encode(b'\xff' * (caps['capture_bytes'] if key == 'bytecode_b64' else 256)).decode()
            require(all(len(v.encode()) <= 128 and all(32 <= ord(c) < 127 for c in v) for v in present),
                    'review actor fixed vocabulary ceiling: ' + path)
            return 'v' * 128
        raise AssertionError('unclassified actor value: ' + path)
    def components_for(docs):
        actors = [{k: v for k, v in a.items() if k not in ('equipment', 'application')} for d in docs for a in d.get('actors', [])]
        dispositions = [a['subprocess']['disposition'] for a in actors if (a.get('subprocess') or {}).get('disposition')]
        resources = [d['resources'] for d in docs if d.get('resources')]
        candidates = dict(actor=actors,
            phase=[{k: v for k, v in p.items() if k != 'termination_gate'} for d in docs for p in d['phases']],
            event=[e for d in docs for e in d.get('extension_events', [])],
            transfer=[t for d in docs for t in d.get('transfers', [])],
            token=[v for d in resources for v in d['tokens']], delivery=[v for d in resources for v in d['deliveries']],
            handle=[v for d in resources for v in d['handles']], disposition_step=[v for d in dispositions for v in d['steps']],
            disposition_issue=[v for d in dispositions for v in d['issues']], schedule=[d['schedule'] for d in docs if d.get('schedule')])
        for key, values in candidates.items(): require(values, 'actor size component lacks a fixture: ' + key)
        result = {key: union(values, key) for key, values in candidates.items()}
        require(isinstance(result['actor'].get('compiled_profile', {}).get('bytecode_b64'), str),
                'actor size account requires an encoded captured-profile fixture')
        return result
    components = components_for(documents)
    actor = components['actor']
    for field in ('pid', 'native_rc', 'raw_status', 'stage', 'observed_ns', 'ownership_unbroken', 'departure_requested', 'capture_ordinal'):
        require(field in actor['owned_reap'], 'owned reap omitted: ' + field)
    for field in ('term_signal', 'termination_request', 'policy_transfer_error', 'policy_transfer_timeout'):
        require(field in actor['subprocess'], 'failure companion omitted: ' + field)
    require(set(components['phase']['activation_observation']) >= {'capture_ordinal', 'observed_ns'}, 'activation omitted')
    gates = [p['termination_gate'] for d in documents for p in d['phases'] if p.get('termination_gate')]
    require(gates and all(set(g['observation']) == {'capture_ordinal'} for g in gates if g.get('observation')), 'gate repeats owned reap')
    for values, path, fragment in [([{'future_array': []}], 'actor', 'unclassified actor reply array'),
                                   ([[0] * 5], 'actor.launch.inherited_descriptors', 'exceeds its accounted capacity')]:
        try: union(values, path)
        except AssertionError as error: require(fragment in str(error), 'wrong negative-control refusal')
        else: raise AssertionError('array accounting negative control accepted')
    missing = copy.deepcopy(documents)
    for d in missing:
        for actor in d.get('actors', []): actor.pop('compiled_profile', None)
    try: components_for(missing)
    except AssertionError as error: require('captured-profile fixture' in str(error), 'wrong missing-capture refusal')
    else: raise AssertionError('missing-capture negative control accepted')
    populations = dict(actor=caps['actors'], phase=caps['phases'],
        event=caps['issues'] + caps['deliveries'] + caps['handles'] + caps['releases'], transfer=caps['deliveries'],
        token=caps['issues'], delivery=caps['deliveries'], handle=caps['handles'], disposition_step=caps['actions'],
        disposition_issue=caps['actors'] + 2 * caps['actions'], schedule=1)
    setup = (524288 + caps['entitlement_records'] * caps['entitlement_bytes'] * 6
             + caps['actors'] * 2 * caps['required_entitlements'] * (caps['entitlement_key_bytes'] * 6 + 3)
             + caps['entitlement_records'] * caps['metadata_bytes'] + caps['phases'] * 4096 + 4096 + 32768)
    require(setup <= 8 * 1024 * 1024, 'consolidation populations exceed JSON allowance')
    allowance = sum(populations[key] * (json_bytes(value) + 1) for key, value in components.items()) + 8 * 1024 * 1024
    return components, allowance


def replay(artifacts):
    receipts = artifacts / 'porcelain-replies'
    decoded = {}
    results = []
    for name in ('normal', 'rich-failure', 'minimal-failure'):
        wire_path = receipts / (name + '.pwp')
        wire = wire_path.read_bytes()
        actual = porcelain.decode(wire, 'reply')
        (receipts / (name + '.decoded.json')).write_text(
            json.dumps(actual, ensure_ascii=False, indent=2) + '\n')
        decoded[name] = actual
        results.append(dict(name=name, bytes=len(wire),
                            sha256=hashlib.sha256(wire).hexdigest()))

        # Keep the complete positive receipt and exact interrupted prefixes.
        # Cuts include framing, fingerprint, root header/identity and the last
        # byte, independently of the generated record/field tables.
        cuts = sorted({0, 1, 4, 35, 36, 40, 41, 42, len(wire) // 2, len(wire) - 1})
        partials = receipts / 'interrupted'
        partials.mkdir(exist_ok=True)
        refusals = []
        for cut in cuts:
            require(0 <= cut < len(wire), name + ': missing complete positive receipt')
            prefix = wire[:cut]
            (partials / (name + '.' + str(cut) + '.partial')).write_bytes(prefix)
            try:
                porcelain.decode(prefix, 'reply')
            except ValueError as error:
                refusals.append(dict(retained_bytes=cut, error=str(error),
                                     sha256=hashlib.sha256(prefix).hexdigest()))
            else:
                raise AssertionError(name + ': interrupted prefix was accepted at ' + str(cut))
        results[-1]['interrupted_prefixes'] = refusals

    normal = decoded['normal']
    expected_normal = json.loads((ROOT / 'tests/fixtures/contract/normal_reply.json').read_text())
    expected_normal['producer'] = dict(contract='test:policy-witness', describe='unknown', commit='unknown')
    expected_normal['runner_subprocess']['worker_evidence']['abi_identity'] = WORKER_IDENTITY
    require_subset(expected_normal, normal, 'normal')
    null_pid = porcelain.decode((receipts / 'null-query-pid.pwp').read_bytes(), 'reply')
    require('pid' in null_pid['steps'][0]['sandbox_check'] and null_pid['steps'][0]['sandbox_check']['pid'] is None,
            'unknown query subject lost explicit null')
    populated = porcelain.decode((receipts / 'populated.pwp').read_bytes(), 'reply')
    require(populated['steps'] and populated['runner_subprocess'], 'populated receipt lost evidence')
    require(set(populated) >= {'reporting_failure', 'preparation_failure', 'equipment_inventory',
            'equipment_bindings', 'equipment_entitlements', 'authority_setup', 'resources', 'schedule'},
            'populated receipt lost an optional record')
    rich = decoded['rich-failure']
    minimal = decoded['minimal-failure']
    require('reporting_failure' not in normal, 'normal fixture unexpectedly degraded')
    require(len(normal['steps']) == 1 and normal['steps'][0]['comparison']['order'] == 'query_first',
            'normal positive comparison missing')
    require(normal['runner_subprocess']['reaped'] is False
            and normal['runner_subprocess'].get('exit_code') is None,
            'normal fixture no longer supplies the unconfirmed-reap control')
    require(normal['runner_subprocess']['disposition']['questions']['final_status']['state'] == 'unresolved',
            'unconfirmed reap acquired a final status')

    for name, reply, retained in [('rich-failure', rich, True), ('minimal-failure', minimal, False)]:
        failure = reply['reporting_failure']
        require(reply['normalized_outcome'] == 'runner_reporting_failed' and reply['rc'] == 1,
                name + ': reporting failure changed execution summary into success')
        require(isinstance(reply.get('error'), str) and reply['error'], name + ': absent failure diagnostic')
        require(failure['origin'] == 'runner_host' and failure['evidence_retained'] is retained,
                name + ': incorrect evidence retention claim')
        require(isinstance(failure.get('diagnostic'), str) and failure['diagnostic'],
                name + ': absent reporting diagnostic')
        for field in ('rc', 'normalized_outcome', 'error'):
            require(failure.get('original_' + field) == normal.get(field),
                    name + ': original summary changed at ' + field)
        require(all(step.get('comparison') is None for step in reply['steps']),
                name + ': unsupported comparison survived')

    expected_rich = copy.deepcopy(normal)
    expected_rich['steps'][0]['phase_id'] = 'missing'
    for step in expected_rich['steps']:
        step.pop('comparison')
    for field in ('rc', 'normalized_outcome', 'error', 'reporting_failure'):
        expected_rich[field] = rich[field]
    require(rich == expected_rich,
            'rich rejection changed facts beyond the injected association and withdrawn comparisons')

    identity = ('producer', 'specimen_id', 'run_kind', 'pid', 'bundle_id', 'policy_format', 'policy_sha256')
    for field in identity:
        require(minimal.get(field) == normal.get(field), 'minimal identity changed at ' + field)
    require(minimal['steps'] == [] and minimal['phases'] == [], 'minimal reply retained unreported observations')
    require(set(minimal) <= set(identity) | {'rc', 'normalized_outcome', 'error', 'steps', 'phases', 'reporting_failure'},
            'minimal reply retained rich evidence despite evidence_retained=false')
    require('evidence-preserving encoding also failed' in minimal['error'],
            'minimal reply omits the rich writer failure')

    replay_shapes_and_sizes(artifacts)
    replay_dispositions(artifacts)
    replay_paths(artifacts)

    report = dict(status='passed', scope='constructed Swift reporting receipts and interrupted-frame decoding',
                  limitations=['No native ending or XPC-copy observation.',
                               'Prefix rejection is not an actual interrupted-pipe emission trial.'],
                  receipts=results)
    (receipts / 'replay.json').write_text(json.dumps(report, indent=2) + '\n')
    print('normal, rich and minimal binary receipts pass independent projection controls; '
          'facts, failure retention and 30 interrupted prefixes checked')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: porcelain_replies.py ARTIFACTS')
    replay(Path(sys.argv[1]))
