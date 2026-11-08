"""Authored binary controls for the independent porcelain structural reader."""
from pathlib import Path
import struct
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import porcelain
import porcelain_schema
import receipts


def tlv(kind, payload):
    return bytes([kind]) + struct.pack('<I', len(payload)) + payload


def field(tag, value):
    return struct.pack('<H', tag) + value


def record(ident, *fields):
    return tlv(6, struct.pack('<H', ident) + b''.join(fields))


def table(descriptor='i64', optional=False, json_null=False):
    return {1: {'name': 'Control', 'fields': {1: dict(name='observed', type=descriptor,
             optional=optional, json_null=json_null)}}}


def read(raw, records=None):
    value, end = porcelain.Reader(raw, records or table()).value(0, len(raw), {'record': 1})
    if end != len(raw):
        raise ValueError('trailing test document')
    return value


class PorcelainCodecTests(receipts.TestCase):
    def test_authored_values_preserve_width_absence_and_raw_bytes(self):
        for descriptor, kind, payload, expected in [
            ('i64', 2, struct.pack('<q', -(2**63)), -(2**63)),
            ('u64', 3, struct.pack('<Q', 2**64 - 1), 2**64 - 1),
            ('bool', 1, b'\x01', True), ('text', 4, 'é'.encode(), 'é'),
            ('bytes', 5, b'\xff\x00', '/wA='),
        ]:
            with self.subTest(descriptor=descriptor):
                raw = record(1, field(1, tlv(kind, payload)))
                self.assertEqual(read(raw, table(descriptor)), {'observed': expected})
        self.assertEqual(read(record(1), table(optional=True)), {})
        self.assertEqual(read(record(1), table(optional=True, json_null=True)), {'observed': None})
        self.assertEqual(read(record(1, field(1, tlv(2, bytes(8))))), {'observed': 0})

    def test_malformed_primitives_and_record_fields_refuse(self):
        valid = field(1, tlv(2, bytes(8)))
        cases = [('missing', record(1), table()),
                 ('unknown_record', record(2, valid), table()),
                 ('duplicate', record(1, valid, valid), table()),
                 ('unknown_tag', record(1, field(2, tlv(2, bytes(8)))), table()),
                 ('wrong_kind', record(1, field(1, tlv(3, bytes(8)))), table()),
                 ('short_integer', record(1, field(1, tlv(2, bytes(7)))), table()),
                 ('signed_overflow', record(1, field(1, tlv(2, struct.pack('<q', 2**31)))), table('i32')),
                 ('unsigned_overflow', record(1, field(1, tlv(3, struct.pack('<Q', 2**32)))), table('u32')),
                 ('bool', record(1, field(1, tlv(1, b'\x02'))), table('bool')),
                 ('utf8', record(1, field(1, tlv(4, b'\xff'))), table('text')),
                 ('short_payload', record(1, valid)[:-1], table()),
                 ('trailing', record(1, valid) + b'x', table())]
        for name, raw, schema in cases:
            with self.subTest(control=name), self.assertRaises(ValueError):
                read(raw, schema)
        schema = table()
        schema[1]['fields'][2] = dict(name='second', type='i64', optional=True)
        with self.assertRaisesRegex(ValueError, 'unordered'):
            read(record(1, field(2, tlv(2, bytes(8))), valid), schema)

    def test_homogeneous_lists_sorted_maps_variants_and_depth(self):
        item = tlv(4, b'a')
        good_list = record(1, field(1, tlv(7, struct.pack('<I', 1) + item)))
        self.assertEqual(read(good_list, table({'list': 'text'})), {'observed': ['a']})
        for payload in [struct.pack('<I', 2**32 - 1), struct.pack('<I', 0) + item,
                        struct.pack('<I', 1) + tlv(2, bytes(8))]:
            with self.assertRaises(ValueError):
                read(record(1, field(1, tlv(7, payload))), table({'list': 'text'}))
        pair = item + tlv(2, struct.pack('<q', 3))
        self.assertEqual(read(record(1, field(1, tlv(8, struct.pack('<I', 1) + pair))),
                              table({'map': 'i64'})), {'observed': {'a': 3}})
        for payload in [struct.pack('<I', 2) + pair + pair,
                        struct.pack('<I', 2) + tlv(4, b'b') + tlv(2, bytes(8)) + pair]:
            with self.assertRaisesRegex(ValueError, 'map key'):
                read(record(1, field(1, tlv(8, payload))), table({'map': 'i64'}))
        variant = tlv(9, struct.pack('<H', 1) + tlv(2, struct.pack('<q', -1)))
        self.assertEqual(read(record(1, field(1, variant)), table({'variant': 'PWDispositionValue'})),
                         {'observed': -1})
        with self.assertRaisesRegex(ValueError, 'variant case'):
            read(record(1, field(1, tlv(9, b'\x03\x00' + item))), table({'variant': 'PWDispositionValue'}))
        schema = table({'record': 1}, optional=True)
        raw = record(1)
        for _ in range(porcelain.MAX_DEPTH):
            raw = record(1, field(1, raw))
        with self.assertRaisesRegex(ValueError, 'depth'):
            read(raw, schema)

    def test_public_projection_preserves_path_forms_and_conditional_null(self):
        schema = table('text')
        schema[1]['fields'][1]['name'] = 'input'
        schema[1]['fields'][2] = dict(name='resolved', type='text', optional=True)
        schema[1]['path_forms'] = ['resolved']
        raw = record(1, field(1, tlv(4, b'/a')), field(2, tlv(4, b'/a')))
        self.assertEqual(read(raw, schema), {'input': '/a', 'same_as_input': ['resolved']})
        self.assertEqual(read(record(1, field(1, tlv(4, b'/a'))), schema),
                         {'input': '/a', 'resolved': None, 'same_as_input': []})
        schema = table('text')
        schema[1]['conditional_null'] = {'team_id': 'observed'}
        self.assertEqual(read(record(1, field(1, tlv(4, b'id'))), schema),
                         {'observed': 'id', 'team_id': None})

    def test_json_host_fixture_requires_explicit_opt_in(self):
        from blackbox import envelope_skeleton
        from runner_client_capture import host_reply
        import contract
        value = {'schema_version': contract.RESPONSE_SCHEMA, 'normalized_outcome': 'bad_request',
                 'rc': 1, 'error': 'authored control', 'steps': [], 'phases': []}
        capture = envelope_skeleton(value, ok=False)['data']['runner_client']['transport']
        with self.assertRaisesRegex(ValueError, 'porcelain'):
            host_reply(capture)
        self.assertEqual(host_reply(capture, allow_fixture_json=True), value)

    def test_magic_fingerprint_root_and_complete_input_are_independent_gates(self):
        header = b'PWP1' + bytes.fromhex(porcelain_schema.SCHEMA_FINGERPRINT)
        raw = header + record(1, field(1, tlv(2, bytes(8))))
        with patch.object(porcelain_schema, 'RECORDS', table()), patch.object(porcelain_schema, 'ROOTS', {'reply': 1}):
            self.assertEqual(porcelain.decode(raw), {'observed': 0})
            for mutant in [b'JSON' + raw[4:], raw[:4] + bytes([raw[4] ^ 1]) + raw[5:], raw[:-1], raw + b'x']:
                with self.assertRaises(ValueError):
                    porcelain.decode(mutant)
            with patch.object(porcelain, 'MAX_BYTES', len(raw) - 1), self.assertRaisesRegex(ValueError, 'byte limit'):
                porcelain.decode(raw)


if __name__ == '__main__':
    sys.exit(receipts.timed_main(sys.modules[__name__], 'source_drift/porcelain_codec', 'porcelain'))
