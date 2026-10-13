"""Actual missing helper on an owned installed copy; preserve recovery on interruption."""
import hashlib
import json
from pathlib import Path
import sys

from check_extensions import ROOT, capture, specimen, probe
sys.path.insert(0, str(ROOT / 'tests/fixtures/byoxpc'))
import session


pw, directory = sys.argv[1:]
out = Path(directory)
state = json.loads((out / 'session.json').read_text())
staging, bundle = Path(state['staging']), Path(state['bundle_path'])
assert bundle == staging / 'PWRunner.xpc' and staging.parent == Path('/private/tmp')
receipts = out / 'missing-issuer'
receipts.mkdir()
session.retire_host(state, receipts, session.command)
issuer = bundle / 'Contents/MacOS/pw-extension-issuer'
backup = staging / 'issuer-held-for-missing-file-control'
recovery = staging / 'issuer-mutation.json'
assert issuer.is_file() and not backup.exists() and not recovery.exists()
digest = hashlib.sha256(issuer.read_bytes()).hexdigest()
ownership = dict(issuer=str(issuer), backup=str(backup), sha256=digest, restored=False)
session.save(recovery, ownership)
issuer.rename(backup)
try:
    assert not issuer.exists() and hashlib.sha256(backup.read_bytes()).hexdigest() == digest
    target = staging / 'extension-targets/extension-target'
    request = specimen(target, [[probe('missing-issuer-read', target)]])
    envelope, reply = capture(pw, receipts, 'refusal', request, expected_rc=1, session_state=state)
    assert reply['normalized_outcome'] == 'bad_request'
    assert reply['request_failure']['code'] == 'extension_issuer_unavailable'
    assert reply.get('runner_subprocess') is None and reply['steps'] == []
    assert reply['extensions'][0]['issuance_status'] == 'issuer_unavailable'
    assert envelope['data']['specimen']['binaries']['issuer']['verification'] == 'unavailable'
    rc, raw, _ = session.tool(receipts, 'validate-missing', [pw, 'runner', 'validate'], invoke=session.command, check=False)
    result = json.loads(raw)
    assert rc != 0 and result['result']['ok'] is False
    assert any(f['service_name'] == state['service_name'] and f['binary'] == 'issuer'
               for f in result['data']['failures']), result
finally:
    assert not issuer.exists() and hashlib.sha256(backup.read_bytes()).hexdigest() == digest
    backup.rename(issuer)
    assert hashlib.sha256(issuer.read_bytes()).hexdigest() == digest
    ownership['restored'] = True
    session.save(recovery, ownership)
    session.save(receipts / 'restoration.json', ownership)
session.envelope(receipts, 'validate-restored', [pw, 'runner', 'validate'], session.command)
recovery.unlink()
print('Missing installed issuer refused before worker launch; validation reports it; exact bytes restored and verified.')
