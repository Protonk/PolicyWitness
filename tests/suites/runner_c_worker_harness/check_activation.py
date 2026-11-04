"""Independent oracle for the actor-form activation barrier and setup modes.

The harness envelope carries the worker's own publications; nothing here is
inferred from a scenario label alone. The policy hash is recomputed from the
policy text the harness delivered.
"""
import hashlib
import json
import sys
from pathlib import Path

r = json.loads(Path(sys.argv[1]).read_text())
name = r['scenario']
completed = [s['completed'] for s in r['slots']]
assert r['actor_mode'] in (1, 2), r
expected_hash = hashlib.sha256(r['policy'].encode()).hexdigest()

if name == 'activation_cutoff_past':
    # Refused at clock setup, before the policy read: no ready byte, no hash,
    # no setup publication, exit 12 with the cutoff failure and detail 1.
    assert not r['ready_byte_received'] and r['policy_hash_published'] == 0, r
    assert r['actor_setup'] == 0 and not r['applied'] and not r['done'], r
    assert r['exit_code'] == 12 and r['term_signal'] is None, r
    assert r['failure_published'] == 1 and r['failure'] == {
        'operation': 12, 'code': 15, 'detail': 1, 'native_kind': 0, 'errno_present': 0}, r
    assert not any(completed) and r['phase_arrived'] == 0, r
    print('ok: ' + name + '; a cutoff already past refuses before any policy byte')
    sys.exit(0)

# Every other row reads the policy and publishes its own hash before setup.
assert r['ready_byte_received'] and r['policy_hash_published'] == 1, r
assert r['policy_received_sha256'] == expected_hash, (r['policy_received_sha256'], expected_hash)
if r['actor_mode'] == 1:
    assert r['applied'] and r['apply_rc'] == 0 and r['actor_setup'] == 1, r
else:
    # Unapplied: declared setup, never applied, no apply result.
    assert not r['applied'] and r['apply_rc'] == 0 and r['actor_setup'] == 2, r
# Parked before activation: polls observed the setup publication with no
# attempt, completion or arrival.
assert r['quiescence_polls'] > 1, r
assert not r['early_completion'] and not r['early_attempt'] and not r['arrived_before_activation'], r
assert not r['sent_sigkill'] and r['exit_code'] == 0 and r['term_signal'] is None, r

if name in ('activation_named_ordinal', 'activation_under_deny_default', 'unapplied_actor_reads', 'unapplied_under_deny_default'):
    assert r['activation_set'] and r['activation_ms'] >= (300 if name.startswith('activation') else 100), r
    assert r['activation_observed'] == 1 and r['phase_arrived'] == 1 and r['phase_completed'] == 1, r
    assert r['proceed_set'] and r['proceed_observed'] == 1 and r['done'], r
    assert r['failure_published'] == 0 and all(completed), r
    slot = r['slots'][0]
    if name == 'activation_under_deny_default':
        assert slot['rc'] != 0 and slot['errno'] in (1, 13), slot
    else:
        # An unapplied actor under a deny-default text still reads: nothing
        # was applied. The applied allow-default actor reads as well.
        assert slot['rc'] == 0 and slot['observed_path'] == '/private/etc/hosts', slot
elif name == 'activation_greater_ordinal':
    assert r['activation_set'] and r['activation_observed'] == 0 and r['phase_arrived'] == 0, r
    assert r['done'] and not r['proceed_set'] and not any(completed), r
    assert r['failure_published'] == 1 and r['failure'] == {
        'operation': 13, 'code': 16, 'detail': 2, 'native_kind': 0, 'errno_present': 0}, r
    assert r['progress'] >> 24 == 13 and (r['progress'] >> 20) & 15 == 1, r
elif name == 'activation_withheld_cutoff':
    assert r['cutoff_set'] and not r['activation_set'] and r['phase_arrived'] == 0, r
    assert r['done'] and not r['proceed_set'] and not any(completed), r
    assert r['failure_published'] == 1 and r['failure'] == {
        'operation': 13, 'code': 15, 'detail': 0, 'native_kind': 0, 'errno_present': 0}, r
elif name == 'activation_cancel_while_parked':
    # Never activated and no cutoff: the exit request ends the parked wait
    # with an ordinary exit and no terminal publication.
    assert not r['activation_set'] and r['phase_arrived'] == 0 and not r['done'], r
    assert r['exit_requested'] == 1 and r['failure_published'] == 0 and not any(completed), r
else:
    raise AssertionError('unknown activation scenario: ' + name)
print('ok: ' + name + '; activation barrier, setup mode and policy hash established')
