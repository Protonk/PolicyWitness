"""Independent fixture generations and finite observation comparisons for test_input."""
import hashlib

import check_test_input as c


def identity(sample):
    return tuple(c.get(sample, 'stat', field) for field in ('st_dev', 'st_ino'))


def replacement_rows(r, state):
    paths, passages = state['paths'], state['passages']
    transition = state.get('replacement') or {}
    old, new = transition.get('original'), transition.get('prepared')
    previous, temporary = paths['A'] + '.previous', paths['A'] + '.replacement'
    b = c.get(passages, 'b', 'before')
    fields = ('st_dev', 'st_mode', 'st_uid', 'st_gid', 'st_size')
    r.check('replacement', c.sample_ok(old, paths['A'], c.LONG) and
            c.sample_ok(new, temporary, c.LONG) and identity(old) == identity(c.get(passages, 'allowed_a', 'after')) and
            identity(new) not in (identity(old), identity(b)) and
            all(c.get(old, 'stat', f) == c.get(new, 'stat', f) for f in fields) and
            transition.get('renames') == [[paths['A'], previous], [temporary, paths['A']]],
            'separately prepared object, unchanged original, distinct inode and both recorded renames')
    for name in c.REPLACEMENTS:
        p = passages.get(name) or {}
        r.check(name + '.generation', all(identity(p.get(t)) == identity(new) for t in ('before', 'after')),
                'one replacement identity through every in-place update')
        for key, target, reference in (('parked', previous, old), ('bystander', paths['B'], b)):
            samples = [c.get(p, key, t) for t in ('before', 'after')]
            r.check(name + '.' + key, all(c.sample_ok(s, target, c.LONG) and identity(s) == identity(reference) for s in samples)
                    and not c.target_changes({target: samples[0]} if isinstance(samples[0], dict) else {}, {target: samples[1]}),
                    'unchanged bytes and identity of ' + target)


# Every observation is compared; these sets are authored independently of captures.
PAIRS = (
    ('allowed_a', 'replaced_a', {'descriptor_identity', 'external.inode'}),
    ('replaced_a', 'suffix_a', {'external.sha256'}),
    ('suffix_a', 'bound_a', {'external.length', 'external.sha256'}),
    ('bound_a', 'empty_a', {'content', 'external.length', 'external.sha256', 'external.prefix_sha256'}),
)


def facts(passage, reply, step_id='read-target'):
    document = c.parsed(c.get(passage, 'capture', 'input'))
    submitted = next((s for s in (c.get(document, 'probe_plan') or []) if s.get('step_id') == step_id), None)
    step = next((s for s in (c.get(reply, 'steps') or []) if s.get('step_id') == step_id), None)
    sample = (c.get(passage, 'peer', 'before') if c.get(submitted, 'attempt', 'target') != c.get(passage, 'before', 'target') else passage.get('before'))
    if submitted is None or step is None or not isinstance(sample, dict) or not sample.get('readable'):
        return None
    q, a = c.mapping(step.get('sandbox_check')), c.mapping(step.get('attempt'))
    read = c.mapping(a.get('fresh_read'))
    raw = read.get('content_hex')
    try:
        digest = hashlib.sha256(bytes.fromhex(raw)).hexdigest() if isinstance(raw, str) else None
    except ValueError:
        digest = None
    phase = next((p for p in reply.get('phases', []) if p.get('phase_id') == step.get('phase_id')), {})
    return {
        'request_bytes': c.get(passage, 'capture', 'input'),
        'query_operation': c.get(submitted, 'sandbox_check', 'operation'),
        'query_target': c.get(submitted, 'sandbox_check', 'filter', 'value'),
        'attempt_target': c.get(submitted, 'attempt', 'target'),
        'query': [q.get(k) for k in ('result_source', 'outcome', 'native_rc', 'errno')],
        'attempt': [a.get(k) for k in ('outcome', 'rc', 'errno')] +
                   [type(read.get('open_rc')) is int and read['open_rc'] >= 0,
                    c.exact(read.get('stat_rc'), 0), c.exact(read.get('close_rc'), 0)],
        'descriptor_identity': [c.get(read, 'identity', k) for k in ('device', 'inode')],
        'content': [read.get('read_rc'), digest],
        **{'external.' + k: sample.get(k) for k in ('length', 'sha256', 'prefix_sha256')},
        **{'external.' + k: c.get(sample, 'stat', field) for k, field in (('device', 'st_dev'), ('inode', 'st_ino'))},
        'ownership': [step.get('phase_id'), phase.get('ordinal'), step.get('actor_id'), phase.get('actor_visit')],
    }


def distinction_rows(r, state, admitted):
    rows = []
    pairs = [(left, 'read-target', right, 'read-target', diff) for left, right, diff in PAIRS]
    pairs += [('crossed', 'read-aa', 'crossed', 'read-ba', {'query_target', 'query'}),
              ('crossed', 'read-aa', 'crossed', 'read-ab', {'attempt_target', 'attempt', 'descriptor_identity', 'content', 'external.inode'}),
              ('crossed', 'read-bb', 'crossed', 'metadata-b', {'query_operation', 'query'})]
    for left, left_id, right, right_id, differences in pairs:
        a, b = [facts(state['passages'].get(name) or {}, admitted.get(name), ident) for name, ident in ((left, left_id), (right, right_id))]
        observed = {k: 'equal' if a[k] == b[k] else 'different' for k in a} if a is not None and b is not None else None
        expected = {k: 'different' if k in differences else 'equal' for k in (a or b or {})}
        ident = 'distinction.' + (left + '--' + right if left != right else left + '.' + left_id + '--' + right_id)
        r.check(ident, observed == expected, dict(expected=expected, observed=observed), available=observed is not None)
        rows.append(dict(id=ident, expected=expected, observed=observed))
    return rows
