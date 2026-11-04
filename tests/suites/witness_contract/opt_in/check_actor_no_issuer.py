"""Actor execution launches no issuer helper; the declaration form still depends on it.

The owned installed copy's `pw-extension-issuer` is held aside under a recovery
record, exactly as the missing-issuer control does. With the file absent, the
declaration form is refused before any worker exists, while an actor-form
specimen whose issuing actor is its own process issues, transfers, consumes and
reads through the same installation. The exact bytes are restored and verified
afterwards and `runner validate` reports the damaged and the restored state.
Validation is not weakened: the invalid-installation diagnostic is part of the
retained evidence.
"""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parents[3] / 'lib')]
from check_extensions import ROOT, capture, specimen, probe  # noqa: E402
import extension_actors  # noqa: E402
from contract import REQUEST_SCHEMA  # noqa: E402
from worker_exit_witness import worker_exit_witness  # noqa: E402
sys.path.insert(0, str(ROOT / 'tests/fixtures/byoxpc'))
import session  # noqa: E402

pw, directory = sys.argv[1:]
out = Path(directory)
state = json.loads((out / 'session.json').read_text())
staging, bundle = Path(state['staging']), Path(state['bundle_path'])
assert bundle == staging / 'PWRunner.xpc' and staging.parent == Path('/private/tmp')
receipts = out / 'actor-no-issuer'
receipts.mkdir()
issuer = bundle / 'Contents/MacOS/pw-extension-issuer'
backup = staging / 'issuer-held-for-actor-contrast'
recovery = staging / 'actor-issuer-mutation.json'
assert issuer.is_file() and not backup.exists() and not recovery.exists()
digest = hashlib.sha256(issuer.read_bytes()).hexdigest()
ownership = dict(issuer=str(issuer), backup=str(backup), sha256=digest, restored=False)
session.save(recovery, ownership)
targets = staging / 'actor-targets'
targets.mkdir(exist_ok=True)
target = targets / 'no-issuer-target'
contents = b'PW actor no-issuer contrast\n'
target.write_bytes(contents)
read = extension_actors.read_probe
result = {}
issuer.rename(backup)
try:
    assert not issuer.exists() and hashlib.sha256(backup.read_bytes()).hexdigest() == digest
    # ---- Declaration form: refused before any worker exists.
    legacy = specimen(target, [[probe('legacy-read', target)]])
    envelope, reply = capture(pw, receipts, 'declaration', legacy, expected_rc=1, session_state=state)
    assert reply['normalized_outcome'] == 'bad_request', reply['normalized_outcome']
    assert reply['request_failure']['code'] == 'extension_issuer_unavailable', reply['request_failure']
    assert reply.get('runner_subprocess') is None and reply['steps'] == []
    assert reply['extensions'][0]['issuance_status'] == 'issuer_unavailable'
    assert envelope['data']['specimen']['binaries']['issuer']['verification'] == 'unavailable'
    result['declaration'] = dict(outcome=reply['normalized_outcome'], code=reply['request_failure']['code'],
                                 issuer_verification=envelope['data']['specimen']['binaries']['issuer']['verification'])

    # ---- Actor form: the issuing actor is its own fresh process; B reads
    # only under the consumed extension. No helper binary is needed or present.
    spec = {
        'schema_version': REQUEST_SCHEMA, 'specimen_id': 'actor_no_issuer',
        'actors': [extension_actors.unapplied_actor('A'), extension_actors.apply_actor('B', extension_actors.C_POLICY)],
        'phases': [
            {'phase_id': 'b_before', 'actor_id': 'B', 'actions': [read('b_read_before', target)]},
            {'phase_id': 'supply', 'actor_id': 'A', 'actions': [extension_actors.issue('a_issue', 'ta', target),
                                                                 extension_actors.transfer('a_to_b', 'ta', 'B', 'db')]},
            {'phase_id': 'b_use', 'actor_id': 'B', 'actions': [extension_actors.consume('b_consume', 'db', 'hb'),
                                                                read('b_read_after', target), extension_actors.release('b_release', 'hb')]},
        ]}
    envelope, runner = capture(pw, receipts, 'actors', spec, session_state=state)
    assert runner['execution_form'] == 'actors' and runner['normalized_outcome'] == 'ok', (runner['normalized_outcome'], runner.get('error'))
    assert envelope['data']['specimen']['binaries']['issuer']['verification'] == 'unavailable'
    worker_binary = envelope['data']['specimen']['binaries'].get('worker')
    assert runner.get('extensions') in (None, []), 'actor form carries no declaration record'
    witnessed, reason = worker_exit_witness(envelope)
    assert witnessed, reason
    for actor in runner['actors']:
        assert actor['subprocess']['reaped'] and actor['subprocess']['exit_code'] == 0, actor['actor_id']
    assert {a['actor_id']: a['setup_status'] for a in runner['actors']} == {'A': 'unapplied_declared', 'B': 'applied'}
    events = {e['step_id']: e for e in runner['extension_events']}
    steps = {s['step_id']: s for s in runner['steps']}
    a_issue, consume = events['a_issue'], events['b_consume']
    delivery, = runner['transfers']
    assert a_issue['status'] == 'returned' and a_issue['native_nonnull'] is True and a_issue['actor_id'] == 'A', a_issue
    assert delivery['status'] == 'delivered' and delivery['equality'] == 'equal', delivery
    assert consume['status'] == 'returned' and consume['native_result'] != -1 and consume['actor_id'] == 'B', consume
    before, after = steps['b_read_before']['attempt'], steps['b_read_after']['attempt']
    assert before['outcome'] == 'read_failed' and before['result_source'] == 'worker', before
    assert after['rc'] == 0 and after['fresh_read']['content_hex'] == contents.hex(), after
    assert after['fresh_read']['identity']['inode'] == target.stat().st_ino
    result['actors'] = dict(outcome=runner['normalized_outcome'], issuer_verification='unavailable',
                            worker_verification=worker_binary and worker_binary.get('verification'),
                            a_issue_nonnull=True, delivery=delivery['status'], b_consume=consume['native_result'],
                            b_read_before=before['outcome'], b_read_after_rc=after['rc'],
                            pids=[a['launch']['pid'] for a in runner['actors']])

    rc, raw, _ = session.tool(receipts, 'validate-missing', [pw, 'runner', 'validate'], invoke=session.command, check=False)
    validation = json.loads(raw)
    assert rc == 0 and validation['result']['ok'] is True and validation['data']['invalid'] >= 1
    assert any(f['service_name'] == state['service_name'] and f['binary'] == 'issuer'
               for f in validation['data']['failures']), validation
finally:
    assert not issuer.exists() and hashlib.sha256(backup.read_bytes()).hexdigest() == digest
    backup.rename(issuer)
    assert hashlib.sha256(issuer.read_bytes()).hexdigest() == digest
    ownership['restored'] = True
    session.save(recovery, ownership)
    session.save(receipts / 'restoration.json', ownership)
restored = session.envelope(receipts, 'validate-restored', [pw, 'runner', 'validate'], session.command)
assert not any(f['service_name'] == state['service_name'] for f in restored['failures']), restored
recovery.unlink()
session.save(receipts / 'contrast.json', result)
print('declaration form refused without the installed issuer; the actor form issued, delivered, consumed and read '
      'through the same installation with no issuer helper; exact issuer bytes restored and verified')
