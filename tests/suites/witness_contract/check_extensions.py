"""Real extension lifecycle and fresh-descriptor observations through the CLI."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import consumer
from contract import REQUEST_SCHEMA
from run_capture import RunCapture


def probe(identity, target):
    return {'step_id': identity, 'sandbox_check': {'operation': 'file-read-data',
            'filter': {'kind': 'path', 'value': str(target)}},
            'attempt': {'kind': 'file', 'action': 'read_fresh', 'target': str(target)}}


def intervention(identity, operation):
    value = {'operation': operation, 'handle_ref': 'handle'}
    if operation == 'consume':
        value['token_ref'] = 'token'
    return {'step_id': identity, 'extension': value}


def specimen(target, phases):
    return {'schema_version': REQUEST_SCHEMA, 'specimen_id': 'extensions',
            'policy': {'format': 'sbpl', 'sbpl_source': '(version 1)(allow default)(deny file-read-data)(allow file-read-data (extension "com.apple.app-sandbox.read"))'},
            'extensions': [{'token_ref': 'token', 'target': str(target)}],
            'phases': [{'phase_id': f'p{i}', 'actions': actions} for i, actions in enumerate(phases)]}


def main():
    pw, directory = sys.argv[1:]
    out = Path(directory).resolve()
    target = out / 'extension-target'
    contents = b'PW extension fresh read witness\n'
    target.write_bytes(contents)
    metadata = target.stat()
    spec = specimen(target, [[probe('before', target), intervention('consume', 'consume')],
                             [probe('during', target), intervention('release', 'release')],
                             [probe('after', target)]])
    with RunCapture(pw, out / 'lifecycle', spec, cli_args=['--no-log-capture']) as captured:
        assert captured.wait(timeout=40) == 0
        envelope = captured.load_json()
    runner = envelope['data']['runner_result']
    assert runner['normalized_outcome'] == 'ok', runner
    assert runner['sandboxed_after_apply'] and runner['runner_subprocess']['reaped']
    declaration, = runner['extensions']
    assert declaration['preparation_status'] == 'prepared'
    assert declaration['identity']['inode'] == metadata.st_ino
    assert declaration['identity']['device'] == metadata.st_dev
    assert declaration['issuance_status'] == 'issued' and declaration['delivery_status'] == 'delivered'
    issuer = declaration['issuer']
    assert issuer['native_nonnull'] and issuer['result_published'] and issuer['call_boundary_observed']
    assert issuer['reaped'] and issuer['exit_code'] == 0 and issuer['euid'] == os.geteuid()
    assert issuer['pid'] != runner['runner_subprocess']['pid']
    consume, release = runner['extension_events']
    assert consume['native_result'] != -1 and consume['status'] == 'returned'
    assert release['native_result'] == 0 and release['status'] == 'returned'
    assert consume['handle_ref'] == release['handle_ref'] == 'handle'
    before, during, after = [x['attempt'] for x in runner['steps']]
    assert before['rc'] != 0 and after['rc'] != 0
    read = during['fresh_read']
    assert during['rc'] == 0 and read['open_rc'] >= 0 and read['close_rc'] == 0
    assert bytes.fromhex(read['content_hex']) == contents and read['read_rc'] == len(contents)
    assert read['identity']['inode'] == metadata.st_ino and read['identity']['device'] == metadata.st_dev
    assert all(x['comparison']['order'] == 'query_first' for x in runner['steps'])
    assert all(p['arrival_observed'] and p['completion_observed'] for p in runner['phases'])
    assert target.read_bytes() == contents
    (out / 'independent-observations.json').write_text(json.dumps({'device': metadata.st_dev,
        'inode': metadata.st_ino, 'content_hex': contents.hex(), 'unchanged_contents': True}, indent=2) + '\n')
    errors = consumer.validate(envelope)
    assert not errors, errors
    print('One worker: native issuance/consume handle/release, three collections and fresh access evidence.')


if __name__ == '__main__':
    main()
