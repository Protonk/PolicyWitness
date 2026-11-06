"""Missing selected equipment refuses before launch; exact bytes are restored.

Holding code aside invalidates the enclosing service seal as well as removing
its selected role. The live refusal retains whichever verification boundary it
actually reached. Pure binding controls separately cover a missing role behind
a valid injected service seal; this control does not re-sign a launched service.
"""
import hashlib
import json
from pathlib import Path
import stat
import sys

HERE = Path(__file__).resolve()
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parents[3] / 'lib')]
from witness_capture import capture
from contract import REQUEST_SCHEMA
sys.path[:0] = [str(HERE.parents[3] / 'fixtures/byoxpc'), str(HERE.parents[3] / 'fixtures/caller_auth')]
import session
from bundle import command, save

pw, directory = sys.argv[1:]
out = Path(directory)
state = json.loads((out / 'session.json').read_text())
staging, bundle = session.owned_bundle(state)
receipts = out / 'missing-equipment'
receipts.mkdir()
selected = bundle / 'Contents/MacOS/pw-probe-runner'
unentitled = bundle / 'Contents/MacOS/pw-probe-runner-unentitled'
backup = staging / 'selected-worker-held-for-control'
recovery = staging / 'selected-worker-recovery.json'
assert selected.is_file() and unentitled.is_file() and not backup.exists() and not recovery.exists()
original = hashlib.sha256(selected.read_bytes()).hexdigest()
other = hashlib.sha256(unentitled.read_bytes()).hexdigest()
mode = stat.S_IMODE(selected.stat().st_mode)
ownership = dict(target=str(selected), backup=str(backup), sha256=original, mode=mode, restored=False)
save(recovery, ownership)
invoke = session.session_invoke(pw, state, command)
selected.rename(backup)
try:
    assert not selected.exists() and hashlib.sha256(backup.read_bytes()).hexdigest() == original
    assert hashlib.sha256(unentitled.read_bytes()).hexdigest() == other
    request = {'schema_version': REQUEST_SCHEMA, 'specimen_id': 'missing_selected_equipment',
               'actors': [{'actor_id': 'subject', 'equipment': 'selected', 'sandbox': {'mode': 'unapplied'}}],
               'phases': [{'phase_id': 'main', 'actor_id': 'subject', 'actions': []}]}
    _, reply = capture(pw, receipts, 'refused', request, expected_rc=1, session_state=state)
    assert reply['normalized_outcome'] == 'runner_failed'
    assert reply['preparation_failure']['stage'] == 'equipment' and reply['preparation_failure']['code'] == 'equipment_binding_refused'
    assert all(a.get('launch') is None and a.get('subprocess') is None and a['setup_status'] == 'launch_refused' for a in reply['actors'])
    assert reply['steps'] == [] and reply['extension_events'] == [] and reply['transfers'] == []
    data = session.envelope(receipts, 'validate-missing', [pw, 'runner', 'validate'], invoke)
    assert data['invalid'] >= 1 and any(f['binary'] == 'worker' for f in data['failures']), data
    save(receipts / 'observed-refusal.json', dict(inventory=reply['equipment_inventory'], bindings=reply['equipment_bindings'],
                                               preparation_failure=reply['preparation_failure'], validation=data))
finally:
    # Never overwrite an unexpected replacement; retain durable recovery instead.
    assert not selected.exists(), 'selected path replaced while control held its bytes; recovery retained'
    assert backup.is_file() and hashlib.sha256(backup.read_bytes()).hexdigest() == original
    backup.rename(selected)
    assert hashlib.sha256(selected.read_bytes()).hexdigest() == original and stat.S_IMODE(selected.stat().st_mode) == mode
    assert hashlib.sha256(unentitled.read_bytes()).hexdigest() == other
    ownership['restored'] = True
    save(recovery, ownership); save(receipts / 'restoration.json', ownership)
    data = session.envelope(receipts, 'validate-restored', [pw, 'runner', 'validate'], invoke)
    assert data['invalid'] == 0, data
print('missing selected worker refused without fallback or spawn; reached seal/binding facts retained; exact worker bytes and validation restored')
