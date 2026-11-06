"""The principal re-delegation specimen's exact policies and request shape.

One source for the bytes the policy qualification case compiles and applies and
the bytes the principal acceptance specimen submits. A qualification result
describes exactly these bytes; changing them here changes both cases.
"""
import hashlib

# B issues only under a consumed read extension and has no ordinary read
# allowance for the target. C has no issuance allowance at all.
B_POLICY = ('(version 1) (allow default) (deny file-read-data) (deny file-write*) (deny file-issue-extension) '
            '(allow file-read-data (extension "com.apple.app-sandbox.read")) '
            '(allow file-issue-extension (require-all (extension-class "com.apple.app-sandbox.read") '
            '(extension "com.apple.app-sandbox.read")))')
C_POLICY = ('(version 1) (allow default) (deny file-read-data) (deny file-write*) '
            '(allow file-read-data (extension "com.apple.app-sandbox.read"))')
# An ordinary allowance for the same target: the positive calibration policy.
CALIBRATION_POLICY = '(version 1) (allow default)'


def sha256_hex(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def read_probe(step_id, target):
    target = str(target)
    return {'step_id': step_id,
            'sandbox_check': {'operation': 'file-read-data', 'filter': {'kind': 'path', 'value': target}},
            'attempt': {'kind': 'file', 'action': 'read_fresh', 'target': target}}


def issue(step_id, token_ref, target, authority='read'):
    return {'step_id': step_id, 'extension': {'operation': 'issue', 'family': 'file', 'authority': authority,
                                              'target': str(target), 'token_ref': token_ref}}


def transfer(step_id, token_ref, recipient, delivery_ref):
    return {'step_id': step_id, 'extension': {'operation': 'transfer', 'token_ref': token_ref,
                                              'recipient': recipient, 'delivery_ref': delivery_ref}}


def consume(step_id, delivery_ref, handle_ref):
    return {'step_id': step_id, 'extension': {'operation': 'consume', 'delivery_ref': delivery_ref,
                                              'handle_ref': handle_ref}}


def release(step_id, handle_ref):
    return {'step_id': step_id, 'extension': {'operation': 'release', 'handle_ref': handle_ref}}


def apply_actor(actor_id, policy):
    return {'actor_id': actor_id, 'equipment': 'selected', 'sandbox': {'mode': 'apply', 'policy': {'format': 'sbpl', 'sbpl_source': policy}}}


def unapplied_actor(actor_id):
    return {'actor_id': actor_id, 'equipment': 'unentitled', 'sandbox': {'mode': 'unapplied'}}


def redelegation_specimen(target, *, schema_version, specimen_id='extension_redelegation',
                          b_policy=B_POLICY, c_policy=C_POLICY):
    """The plan's principal request with the test-owned target substituted."""
    target = str(target)
    return {
        'schema_version': schema_version, 'specimen_id': specimen_id,
        'actors': [unapplied_actor('A'), apply_actor('B', b_policy), apply_actor('C', c_policy)],
        'phases': [
            {'phase_id': 'b_before', 'actor_id': 'B', 'actions': [read_probe('b_read_before', target)]},
            {'phase_id': 'c_before', 'actor_id': 'C', 'actions': [read_probe('c_read_before', target)]},
            {'phase_id': 'initial_supply', 'actor_id': 'A', 'actions': [
                issue('a_issue', 'ta', target), transfer('a_to_b', 'ta', 'B', 'db')]},
            {'phase_id': 'b_consume', 'actor_id': 'B', 'actions': [consume('b_consume_first', 'db', 'hb')]},
            {'phase_id': 'b_redelegate', 'actor_id': 'B', 'actions': [
                read_probe('b_read_after', target), issue('b_issue', 'tb', target), transfer('b_to_c', 'tb', 'C', 'dc')]},
            {'phase_id': 'c_consume', 'actor_id': 'C', 'actions': [consume('c_consume_second', 'dc', 'hc')]},
            {'phase_id': 'c_effect', 'actor_id': 'C', 'actions': [read_probe('c_read_after', target), release('c_release', 'hc')]},
            {'phase_id': 'b_cleanup', 'actor_id': 'B', 'actions': [release('b_release', 'hb')]},
        ],
    }
