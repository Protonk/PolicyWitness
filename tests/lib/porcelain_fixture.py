"""Independent binary reader for two fixed, test-only observation receipts.

The high record IDs belong only to the equipment-binding and host-setup
fixtures, not the production response schema. Nested records retain the current
schema fingerprint and use the independent porcelain reader. This module never
constructs a RunResult or adds semantic observations to a native receipt.
"""
import porcelain
import porcelain_schema

# The fixtures retain bounded equipment metadata or one worker's setup account.
# Refuse oversized fixture output before structural traversal.
MAX_FIXTURE_BYTES = 4 * 1024 * 1024


def _record(name):
    matches = [ident for ident, record in porcelain_schema.RECORDS.items() if record['name'] == name]
    if len(matches) != 1:
        raise ValueError('fixture nested record is unavailable: ' + name)
    return {'record': matches[0]}


def _fields(rows):
    return {tag: dict(name=name, type=kind, optional=optional)
            for tag, (name, kind, optional) in enumerate(rows, 1)}


FIXTURES = {
    'binding': (65001, _fields([
        ('compiled_identity', 'text', False),
        ('inventory', _record('PWRunnerEquipmentInventory'), False),
        ('bindings', {'list': _record('PWRunnerEquipmentBinding')}, False),
        ('entitlements', {'list': _record('PWRunnerEquipmentEntitlements')}, False),
        ('actors', {'list': _record('PWRunnerActorEquipment')}, False),
        ('executable_paths', {'list': 'text'}, True),
        ('failure_stage', 'text', True),
        ('failure_code', 'text', True),
        ('failure_reason', 'text', True),
    ])),
    'setup_worker': (65002, _fields([
        ('worker_pid', 'i32', False),
        ('ready_byte_received', 'bool', False),
        ('ready_wait', _record('PWHostWait'), True),
        ('sentinel_wait', _record('PWHostWait'), True),
        ('grace_wait', _record('PWHostWait'), True),
        ('poll_stop_reason', 'text', True),
        ('exit_requested', 'bool', True),
        ('termination_request', _record('PWRunnerTerminationRequest'), True),
        ('reaped', 'bool', True),
        ('exit_code', 'i32', True),
        ('term_signal', 'i32', True),
        ('wait_errors', {'list': _record('PWRunnerWaitError')}, True),
        ('cleanup_trigger', 'text', True),
        ('grace_end', 'text', True),
        ('collection_basis', 'text', True),
    ])),
}


def decode_fixture(data, kind):
    """Project exactly one complete known fixture record; preserve omissions."""
    if len(data) > MAX_FIXTURE_BYTES:
        raise ValueError('fixture receipt exceeds byte limit')
    if len(data) < 36 or data[:4] != b'PWP1':
        raise ValueError('wrong fixture magic or short header')
    if data[4:36] != bytes.fromhex(porcelain_schema.SCHEMA_FINGERPRINT):
        raise ValueError('fixture nested-schema fingerprint mismatch')
    ident, fields = FIXTURES[kind]
    if ident in porcelain_schema.RECORDS:
        raise ValueError('fixture record identity collides with production schema')
    records = {**porcelain_schema.RECORDS, ident: dict(name=kind, fields=fields)}
    value, end = porcelain.Reader(data, records).value(36, len(data), {'record': ident})
    if end != len(data):
        raise ValueError('trailing fixture bytes')
    return value
