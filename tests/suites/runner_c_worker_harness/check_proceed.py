"""Independent scenario oracle: never infer attempt absence from a summary label."""
import json
import sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text())
name = r['scenario']
assert r['applied'] and r['apply_rc'] == 0 and r['done'], r
assert not r['early_completion'] and not r['early_attempt'], r
completed = [s['completed'] for s in r['slots']]
expired = name in {'proceed_never_set', 'proceed_late_after_expiry', 'proceed_wait_budget_short', 'host_lost_while_waiting'}
if name == 'proceed_expiry_release_boundary':
    expired = r['failure_published'] == 1
if expired:
    assert r['failure_published'] == 1 and r['failure']['operation'] == 11, r
    assert r['failure']['code'] == 8 and r['failure']['detail'] == 100, r
    assert r['progress'] >> 24 == 11 and (r['progress'] >> 20) & 15 == 1, r
    assert not any(completed) and r['proceed_observed'] == 0, r
else:
    assert r['failure_published'] == 0 and all(completed), r
    assert r['proceed_set'] and r['proceed_observed'] == 1, r
if name in {'proceed_delayed_observed_quiescence', 'proceed_under_bare_deny_default', 'max_slots_proceed', 'proceed_wait_budget_long', 'proceed_wait_budget_short'}:
    assert r['quiescence_polls'] > 1 and r['held_ms'] >= 500, r
if name in {'proceed_before_applied', 'proceed_under_bare_deny_default'}:
    assert all(s['rc'] != 0 and s['errno'] in (1,13) for s in r['slots']), r
if name == 'max_slots_proceed':
    assert len(completed) == 256, r
if name == 'host_lost_while_waiting':
    assert r['sent_sigkill'] and r['term_signal'] == 9, r
else:
    assert not r['sent_sigkill'] and r['exit_code'] == 0, r
print('ok: ' + name + '; release branch and no premature attempts established')
