"""The principal re-delegation specimen through the public CLI, with its
positive calibration and the narrow public contrasts.

The witnessing assertions are about the apparatus: three distinct fresh
processes from the selected equipment, the intended policy bytes applied once
in B and C, every native call, custody, transfer, consume and read either
published or in a specifically justified unavailable state, and associations
that bind the second issue to B's process and the second delivery to that
issue. The kernel's answers (a NULL issue, a failed consume, a denied read) are
recorded and compared; they are not forced. Re-delegation is credited only when
the complete chain published and C's fresh read returned the known bytes
where its baseline read had failed. Calibration must exercise real issuance,
transfer, consumption and access on this host; otherwise this case fails and
the coverage is missing rather than silently unavailable.
"""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
from check_extensions import capture  # noqa: E402
from contract import REQUEST_SCHEMA  # noqa: E402
import extension_actors  # noqa: E402
from worker_exit_witness import worker_exit_witness  # noqa: E402
from consumer import validate  # noqa: E402
from lifecycle_oracle import check_record  # noqa: E402

pw, directory, *session_path = sys.argv[1:]
# An optional BYOXPC session receipt routes every request through that owned
# runner and keeps the targets in its staging directory.
SESSION = json.loads(Path(session_path[0]).read_text()) if session_path else None
out = Path(directory)
out.mkdir(parents=True, exist_ok=True)
CONTENTS = b'PW re-delegation target\n'
CONTROL = b'PW unrelated control\n'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def by_id(items, key, value):
    matches = [i for i in items if i.get(key) == value]
    assert len(matches) == 1, (key, value, len(matches))
    return matches[0]


def step(runner, step_id):
    return by_id(runner['steps'], 'step_id', step_id)


def event(runner, step_id):
    return by_id(runner['extension_events'], 'step_id', step_id)


def read_outcome(runner, step_id, expected):
    """One fresh read's observation: rc, errno and whether the known bytes came back."""
    attempt = step(runner, step_id)['attempt']
    assert attempt['result_source'] == 'worker', (step_id, attempt)
    fresh = attempt.get('fresh_read') or {}
    content = bytes.fromhex(fresh['content_hex']) if fresh.get('content_hex') else None
    return {'rc': attempt['rc'], 'errno': attempt.get('errno'), 'open_rc': fresh.get('open_rc'),
            'bytes_match': content == expected, 'identity': fresh.get('identity')}


def apparatus_complete(envelope, runner, spec, policies):
    """The witnessing assertions every run of this case must satisfy."""
    assert validate(envelope) == [], validate(envelope)
    assert check_record(envelope) == [], check_record(envelope)
    assert runner['execution_form'] == 'actors', runner.get('execution_form')
    witnessed, reason = worker_exit_witness(envelope)
    assert witnessed, reason
    actors = {a['actor_id']: a for a in runner['actors']}
    assert set(actors) == {a['actor_id'] for a in spec['actors']}, actors.keys()
    pids = {name: a['launch']['pid'] for name, a in actors.items()}
    assert len(set(pids.values())) == len(pids), pids
    for name, actor in actors.items():
        sub = actor['subprocess']
        assert sub['reaped'] is True and sub['exit_code'] == 0 and sub['pid'] == pids[name], (name, sub)
        assert actor['launch']['parent_pid'] == runner['pid'], (name, actor['launch'])
        if name in policies:
            expected = sha256(policies[name].encode('utf-8'))
            assert actor['mode'] == 'apply' and actor['setup_status'] == 'applied' and actor['applied'] is True, (name, actor)
            assert actor['application_count'] == 1, (name, actor['application_count'])
            assert actor['policy_sha256'] == expected == actor['policy_received_sha256'], (name, actor)
        else:
            assert actor['mode'] == 'unapplied' and actor['setup_status'] == 'unapplied_declared', (name, actor)
            assert actor.get('applied') is None and actor['application_count'] == 0, (name, actor)
    for phase in runner['phases']:
        assert phase['arrival_observed'] and phase['completion_observed'], phase
        assert phase['ordering']['protocol_violations'] == [], phase
    for s in runner['steps']:
        assert s['sandbox_check']['pid'] == pids[s['actor_id']], s['step_id']
        assert s['comparison']['order'] == 'query_first', (s['step_id'], s['comparison'])
    for e in runner['extension_events']:
        assert e['result_published'] is True, e['step_id']
        assert e['actor_id'] == by_id(runner['phases'], 'phase_id', e['phase_id'])['actor_id'], e['step_id']
    assert runner['normalized_outcome'] == 'ok', (runner['normalized_outcome'], runner.get('error'))
    return pids


def chain(runner, pids):
    """Every link of the re-delegation chain as the reply records it."""
    tokens = {t['token_ref']: t for t in runner['resources']['tokens']}
    deliveries = {d['delivery_ref']: d for d in runner['resources']['deliveries']}
    handles = {h['handle_ref']: h for h in runner['resources']['handles']}
    transfers = {t['delivery_ref']: t for t in runner['transfers']}
    a_issue, b_issue = event(runner, 'a_issue'), event(runner, 'b_issue')
    b_consume, c_consume = event(runner, 'b_consume_first'), event(runner, 'c_consume_second')
    links = {
        'a_issue': {'status': a_issue['status'], 'native_nonnull': a_issue.get('native_nonnull'), 'errno': a_issue.get('errno'),
                    'token_length': a_issue.get('token_length'), 'custody': tokens['ta']['status']},
        'a_to_b': {'status': transfers.get('db', {}).get('status'), 'equality': transfers.get('db', {}).get('equality'),
                   'recipient_acknowledged': transfers.get('db', {}).get('recipient_acknowledged'), 'delivery': deliveries['db']['status']},
        'b_consume': {'status': b_consume['status'], 'native_result': b_consume.get('native_result'),
                      'errno': b_consume.get('errno'), 'unavailable_reason': b_consume.get('unavailable_reason'),
                      'handle': handles['hb']['status']},
        'b_issue': {'status': b_issue['status'], 'native_nonnull': b_issue.get('native_nonnull'), 'errno': b_issue.get('errno'),
                    'token_length': b_issue.get('token_length'), 'custody': tokens['tb']['status'],
                    'issued_by_pid': pids[b_issue['actor_id']], 'actor': b_issue['actor_id']},
        'b_to_c': {'status': transfers.get('dc', {}).get('status'), 'equality': transfers.get('dc', {}).get('equality'),
                   'recipient_acknowledged': transfers.get('dc', {}).get('recipient_acknowledged'), 'delivery': deliveries['dc']['status'],
                   'token': deliveries['dc']['token_ref']},
        'c_consume': {'status': c_consume['status'], 'native_result': c_consume.get('native_result'),
                      'errno': c_consume.get('errno'), 'unavailable_reason': c_consume.get('unavailable_reason'),
                      'handle': handles['hc']['status'], 'delivery': c_consume.get('delivery_ref')},
        'c_release': {'status': event(runner, 'c_release')['status'], 'native_result': event(runner, 'c_release').get('native_result')},
        'b_release': {'status': event(runner, 'b_release')['status'], 'native_result': event(runner, 'b_release').get('native_result')},
    }
    reads = {name: read_outcome(runner, name, CONTENTS) for name in ('b_read_before', 'c_read_before', 'b_read_after', 'c_read_after')}
    # The second delivery is bound to B's issue, never to A's token.
    assert links['b_to_c']['token'] == 'tb' and links['c_consume']['delivery'] == 'dc', links
    assert links['b_issue']['actor'] == 'B', links['b_issue']
    usable = (links['a_issue']['native_nonnull'] is True and links['a_issue']['custody'] == 'issued'
              and links['a_to_b']['status'] == 'delivered' and links['a_to_b']['equality'] == 'equal'
              and links['b_consume']['status'] == 'returned' and links['b_consume']['native_result'] != -1
              and reads['b_read_after']['rc'] == 0 and reads['b_read_after']['bytes_match']
              and links['b_issue']['native_nonnull'] is True and links['b_issue']['custody'] == 'issued'
              and links['b_to_c']['status'] == 'delivered' and links['b_to_c']['equality'] == 'equal'
              and links['c_consume']['status'] == 'returned' and links['c_consume']['native_result'] != -1
              and reads['c_read_after']['rc'] == 0 and reads['c_read_after']['bytes_match']
              and reads['b_read_before']['rc'] != 0 and reads['c_read_before']['rc'] != 0)
    first_break = next((name for name, ok in [
        ('a_issue', links['a_issue']['native_nonnull'] is True and links['a_issue']['custody'] == 'issued'),
        ('a_to_b', links['a_to_b']['status'] == 'delivered'),
        ('b_consume', links['b_consume']['status'] == 'returned' and links['b_consume']['native_result'] != -1),
        ('b_read_after', reads['b_read_after']['rc'] == 0 and reads['b_read_after']['bytes_match']),
        ('b_issue', links['b_issue']['native_nonnull'] is True and links['b_issue']['custody'] == 'issued'),
        ('b_to_c', links['b_to_c']['status'] == 'delivered'),
        ('c_consume', links['c_consume']['status'] == 'returned' and links['c_consume']['native_result'] != -1),
        ('c_read_after', reads['c_read_after']['rc'] == 0 and reads['c_read_after']['bytes_match']),
    ] if not ok), None)
    return {'links': links, 'reads': reads, 'credited': usable, 'first_break': first_break}


def with_control_reads(spec, control):
    for phase in spec['phases']:
        if phase['phase_id'] in ('b_before', 'c_before'):
            phase['actions'].append(extension_actors.read_probe(phase['phase_id'].split('_')[0] + '_control_before', control))
    return spec


def contrast_specs(target, control):
    """Narrow public contrasts: each omits or weakens one link of the principal shape."""
    base = lambda name, **kw: with_control_reads(extension_actors.redelegation_specimen(target, schema_version=REQUEST_SCHEMA,
                                                                                             specimen_id=name, **kw), control)
    specs = {}
    spec = base('contrast_omit_b_consume')
    by_id(spec['phases'], 'phase_id', 'b_consume')['actions'] = []
    by_id(spec['phases'], 'phase_id', 'b_cleanup')['actions'] = []
    specs['omit_b_consume'] = spec
    no_issue_allowance = extension_actors.B_POLICY.replace(
        ' (allow file-issue-extension (require-all (extension-class "com.apple.app-sandbox.read") (extension "com.apple.app-sandbox.read")))', '')
    assert no_issue_allowance != extension_actors.B_POLICY
    specs['remove_b_issuance_allowance'] = base('contrast_remove_b_issuance_allowance', b_policy=no_issue_allowance)
    spec = base('contrast_omit_c_consume')
    by_id(spec['phases'], 'phase_id', 'c_consume')['actions'] = []
    by_id(spec['phases'], 'phase_id', 'c_effect')['actions'] = [extension_actors.read_probe('c_read_after', target)]
    specs['omit_c_consume'] = spec
    no_predicate = extension_actors.C_POLICY.replace(' (allow file-read-data (extension "com.apple.app-sandbox.read"))', '')
    assert no_predicate != extension_actors.C_POLICY
    specs['omit_c_extension_predicate'] = base('contrast_omit_c_extension_predicate', c_policy=no_predicate)
    return specs


report = {'environment': {'macos': platform.mac_ver()[0], 'kernel': os.uname().release, 'machine': os.uname().machine,
                          'euid': os.geteuid()},
          'policies': {'B': extension_actors.sha256_hex(extension_actors.B_POLICY), 'C': extension_actors.sha256_hex(extension_actors.C_POLICY)}}

def scratch_directory():
    if SESSION is None:
        return tempfile.TemporaryDirectory(prefix='pw-redelegation-', dir='/private/tmp')
    owned = Path(SESSION['staging']) / 'actor-targets' / 'redelegation'
    owned.mkdir(parents=True)
    return contextlib.nullcontext(str(owned))


with scratch_directory() as scratch:
    target = Path(scratch) / 'target'
    control = Path(scratch) / 'control'
    target.write_bytes(CONTENTS)
    control.write_bytes(CONTROL)
    identity = os.stat(target)
    report['target'] = {'path': str(target), 'sha256': sha256(CONTENTS), 'device': identity.st_dev, 'inode': identity.st_ino}

    # ---- Principal specimen.
    spec = with_control_reads(extension_actors.redelegation_specimen(target, schema_version=REQUEST_SCHEMA), control)
    envelope, runner = capture(pw, out, 'principal', spec, session_state=SESSION)
    pids = apparatus_complete(envelope, runner, spec, {'B': extension_actors.B_POLICY, 'C': extension_actors.C_POLICY})
    principal = chain(runner, pids)
    for name in ('b_control_before', 'c_control_before'):
        principal['reads'][name] = read_outcome(runner, name, CONTROL)
    # Fresh-descriptor identity of every successful read is the prepared target.
    for name, read in principal['reads'].items():
        if read['rc'] == 0 and name.endswith('after'):
            assert read['identity'] and read['identity']['inode'] == identity.st_ino, (name, read)
    principal['pids'] = pids
    principal['app_build'] = envelope['build']
    report['principal'] = principal
    assert target.read_bytes() == CONTENTS

    # ---- Positive calibration: a simple supported allowance must exercise the
    # real issue, transfer, consume and fresh-access path on this host.
    calibration_spec = {
        'schema_version': REQUEST_SCHEMA, 'specimen_id': 'extension_calibration',
        'actors': [extension_actors.unapplied_actor('A'), extension_actors.apply_actor('B', extension_actors.C_POLICY)],
        'phases': [
            {'phase_id': 'b_before', 'actor_id': 'B', 'actions': [extension_actors.read_probe('b_read_before', target)]},
            {'phase_id': 'supply', 'actor_id': 'A', 'actions': [
                extension_actors.issue('a_issue', 'ta', target), extension_actors.transfer('a_to_b', 'ta', 'B', 'db')]},
            {'phase_id': 'b_use', 'actor_id': 'B', 'actions': [
                extension_actors.consume('b_consume', 'db', 'hb'), extension_actors.read_probe('b_read_after', target),
                extension_actors.release('b_release', 'hb')]},
        ]}
    envelope, runner = capture(pw, out, 'calibration', calibration_spec, session_state=SESSION)
    pids = apparatus_complete(envelope, runner, calibration_spec, {'B': extension_actors.C_POLICY})
    a_issue, b_consume = event(runner, 'a_issue'), event(runner, 'b_consume')
    transfer = by_id(runner['transfers'], 'delivery_ref', 'db')
    before, after = read_outcome(runner, 'b_read_before', CONTENTS), read_outcome(runner, 'b_read_after', CONTENTS)
    calibration = {'a_issue': {'native_nonnull': a_issue.get('native_nonnull'), 'errno': a_issue.get('errno')},
                   'transfer': transfer['status'], 'equality': transfer['equality'],
                   'b_consume': {'status': b_consume['status'], 'native_result': b_consume.get('native_result')},
                   'reads': {'before': before, 'after': after}, 'pids': pids}
    report['calibration'] = calibration
    assert a_issue.get('native_nonnull') is True, ('calibration issuance refused; positive coverage missing', calibration)
    assert transfer['status'] == 'delivered' and transfer['equality'] == 'equal', calibration
    assert b_consume['status'] == 'returned' and b_consume['native_result'] != -1, calibration
    assert before['rc'] != 0 and after['rc'] == 0 and after['bytes_match'], calibration

    # ---- Narrow contrasts: each omits or weakens one link; the chain must not
    # be credited, and every remaining link is still published.
    report['contrasts'] = {}
    for name, contrast in contrast_specs(target, control).items():
        envelope, runner = capture(pw, out, name, contrast, session_state=SESSION)
        policies = {a['actor_id']: a['sandbox']['policy']['sbpl_source'] for a in contrast['actors'] if a['sandbox']['mode'] == 'apply'}
        pids = apparatus_complete(envelope, runner, contrast, policies)
        present = {e['step_id'] for e in runner['extension_events']}
        observed = {
            'events': {e['step_id']: {'status': e['status'], 'native_result': e.get('native_result'),
                                      'native_nonnull': e.get('native_nonnull'), 'unavailable_reason': e.get('unavailable_reason')}
                       for e in runner['extension_events']},
            'transfers': {t['delivery_ref']: t['status'] for t in runner['transfers']},
            'reads': {s['step_id']: read_outcome(runner, s['step_id'], CONTENTS if 'control' not in s['step_id'] else CONTROL)
                      for s in runner['steps']},
            'omitted_links': sorted({'a_issue', 'a_to_b', 'b_consume_first', 'b_issue', 'b_to_c', 'c_consume_second'} - present),
            'pids': pids,
        }
        # A chain with an omitted or unavailable link is never credited.
        complete = {'a_issue', 'a_to_b', 'b_consume_first', 'b_issue', 'b_to_c', 'c_consume_second'} <= present
        credited = complete and chain(runner, pids)['credited']
        observed['credited'] = credited
        if name in ('omit_b_consume', 'omit_c_consume'):
            assert not complete and not credited, (name, observed)
        elif name == 'remove_b_issuance_allowance':
            # B's second issue ran under a policy without the issuance allowance;
            # its result is recorded, and a usable chain would contradict the
            # consumed-extension dependency this contrast removed.
            observed['comparison'] = 'b_issue result under the weakened policy versus the principal run'
        elif name == 'omit_c_extension_predicate':
            observed['comparison'] = "C's read after consume under a policy without the extension predicate versus the principal run"
        report['contrasts'][name] = observed

(out / 'report.json').write_text(json.dumps(report, indent=2, default=str) + '\n')
summary = ('re-delegation credited' if report['principal']['credited']
           else f"re-delegation not credited; first break at {report['principal']['first_break']}")
print(f"principal {summary}; calibration exercised issue, transfer, consume and fresh access; "
      f"{len(report['contrasts'])} contrasts recorded (actors {report['principal']['pids']})")
