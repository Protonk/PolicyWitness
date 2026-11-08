"""Authored binary controls for the independent porcelain structural reader."""
import ast
import base64
import copy
import json
from pathlib import Path
import tempfile
import struct
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import porcelain
import porcelain_schema
import receipts
import fixture_inputs


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
            ('bool', 1, b'\x01', True), ('bool', 1, b'\x00', False),
            ('text', 4, 'é'.encode(), 'é'),
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
                 ('announced_u32_max', record(1, field(1, b'\x02' + struct.pack('<I', 2**32 - 1))), table()),
                 ('combined_wrong_kind_and_short_payload', record(1, field(1, b'\x03' + struct.pack('<I', 8))), table()),
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

    def test_actual_reply_schema_preserves_conflicting_observations(self):
        # Stable wire tags are authored here, not obtained from RECORDS or a writer.
        # Unsupported semantic version and incompatible rc/outcome remain evidence.
        raw = b'PWP1' + bytes.fromhex(porcelain_schema.SCHEMA_FINGERPRINT) + record(55,
            field(1, tlv(2, struct.pack('<q', 999))),
            field(2, tlv(4, b'authored-control')),
            field(4, tlv(2, struct.pack('<q', 0))),
            field(5, tlv(4, b'bad_request')),
            field(7, tlv(2, struct.pack('<q', 1234))),
            field(13, tlv(7, bytes(4))),
            field(17, tlv(7, bytes(4))))
        projected = porcelain.decode(raw)
        self.assertEqual(projected, dict(schema_version=999, specimen_id='authored-control',
            rc=0, normalized_outcome='bad_request', pid=1234, steps=[], phases=[]))
        from consumer import validate
        errors = validate(projected)
        self.assertEqual(len(errors), 1)
        self.assertIn('unsupported runner response', errors[0])

    def test_public_projection_preserves_path_forms_and_conditional_null(self):
        schema = table('text')
        schema[1]['fields'][1]['name'] = 'input'
        schema[1]['fields'][2] = dict(name='resolved', type='text', optional=True)
        schema[1]['path_forms'] = ['resolved']
        raw = record(1, field(1, tlv(4, b'/a')), field(2, tlv(4, b'/a')))
        self.assertEqual(read(raw, schema), {'input': '/a', 'same_as_input': ['resolved']})
        self.assertEqual(read(record(1, field(1, tlv(4, b'/a'))), schema),
                         {'input': '/a', 'resolved': None, 'same_as_input': []})
        schema = table('text', optional=True)
        schema[1]['fields'][2] = dict(name='team_id', type='text', optional=True)
        schema[1]['conditional_null'] = {'team_id': 'observed'}
        self.assertEqual(read(record(1, field(1, tlv(4, b'id'))), schema),
                         {'observed': 'id', 'team_id': None})
        self.assertEqual(read(record(1, field(2, tlv(4, b'team'))), schema), {})
        self.assertEqual(read(record(1, field(1, tlv(4, b'id')), field(2, tlv(4, b'team'))), schema),
                         {'observed': 'id', 'team_id': 'team'})
        # Presentation order follows the schema's path_forms, not field tags.
        schema = table('text')
        schema[1]['fields'][1]['name'] = 'input'
        schema[1]['fields'][2] = dict(name='first', type='text', optional=True)
        schema[1]['fields'][3] = dict(name='second', type='text', optional=True)
        schema[1]['path_forms'] = ['second', 'first']
        raw = record(1, *(field(tag, tlv(4, b'/a')) for tag in (1, 2, 3)))
        self.assertEqual(read(raw, schema), {'input': '/a', 'same_as_input': ['second', 'first']})

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
            # A reduced bound tests the byte-limit mechanism without claiming
            # a full-size native capture or allocating the production allowance.
            with patch.object(porcelain, 'MAX_BYTES', len(raw) - 1), self.assertRaisesRegex(ValueError, 'byte limit'):
                porcelain.decode(raw)


class PorcelainRejectedCaptureTests(receipts.TestCase):
    @staticmethod
    def capture_frame(protocol=None):
        # Tags and record identities are authored, not obtained from a writer or
        # generated field table. This is a complete local clock-error capture.
        import contract
        protocol = contract.RUNNER_PROTOCOL if protocol is None else protocol
        text = lambda value: tlv(4, value.encode('utf-8'))
        signed = lambda value: tlv(2, struct.pack('<q', value))
        error = record(67, field(1, text('local')), field(2, text('clock_error')),
            field(5, text('unavailable')), field(6, tlv(1, b'\x00')), field(7, tlv(1, b'\x00')))
        body = record(32, field(1, text('runner_client_capture')), field(2, signed(protocol)),
            field(3, signed(42)), field(4, text('mach_continuous_time_ns')),
            field(5, tlv(1, b'\x00')), field(9, tlv(3, struct.pack('<Q', 1))),
            field(10, tlv(7, struct.pack('<I', 0))), field(11, text('local_error')),
            field(12, record(60, field(1, text('not_invoked')))), field(13, text('local_error')),
            field(14, error))
        return b'PWP1' + bytes.fromhex(porcelain_schema.SCHEMA_FINGERPRINT) + body

    @staticmethod
    def rejected_client(raw, status='malformed', *, parse_error='wire rejected', truncated=False,
                        delivery_failed=False):
        received = len(raw) + int(truncated)
        return dict(request_delivery=dict(bytes_written=1, error='EPIPE' if delivery_failed else None),
            stdout_truncated=truncated, stdout_capture_error='retention lost' if truncated else None,
            stdout_parse_error=parse_error, stdout_bytes_received=received,
            stdout_bytes_retained=len(raw), capture_limit_bytes=len(raw),
            transport=dict(format='porcelain', data_base64=base64.b64encode(raw).decode('ascii')),
            transport_admission=status, transport_error='independent rejection control',
            submission='unknown', runner_reply_error=None)

    def test_raw_rejection_classification_and_delivery_precedence(self):
        import contract
        from runner_client_capture import validate_client, validate_capture
        valid = self.capture_frame()
        self.assertEqual(validate_capture(porcelain.decode(valid, 'capture')), [])
        unsupported = valid[:4] + bytes([valid[4] ^ 1]) + valid[5:]
        malformed = valid[:36] + b'not a complete value'
        cases = [
            ('fingerprint', self.rejected_client(unsupported, 'unsupported')),
            ('protocol', self.rejected_client(self.capture_frame(contract.RUNNER_PROTOCOL + 1),
                                             'unsupported', parse_error=None)),
            ('malformed', self.rejected_client(malformed)),
            # Even a complete value retained as a prefix cannot be admitted when
            # reception lost bytes; its body supplies no submission projection.
            ('retention', self.rejected_client(valid, parse_error=None, truncated=True)),
            ('delivery', self.rejected_client(valid, 'delivery_failed', parse_error=None,
                                             delivery_failed=True)),
            ('delivery_before_version', self.rejected_client(unsupported, 'delivery_failed',
                                                            delivery_failed=True)),
        ]
        for name, client in cases:
            with self.subTest(control=name):
                before = copy.deepcopy(client)
                self.assertEqual(validate_client(client, None), [])
                self.assertEqual(client, before, 'independent admission changed retained evidence')

    def test_raw_rejection_controls_refuse_corrupt_receipts_and_recovered_claims(self):
        from runner_client_capture import validate_client
        valid = self.capture_frame()
        raw = valid[:4] + bytes([valid[4] ^ 1]) + valid[5:]
        baseline = self.rejected_client(raw, 'unsupported')
        mutations = {
            'wrong_classification': lambda c: c.update(transport_admission='malformed'),
            'submission': lambda c: c.update(submission='invoked'),
            'host_error': lambda c: c.update(runner_reply_error='invented host interpretation'),
            'extra_wrapper_key': lambda c: c['transport'].update(submission=dict(state='invoked')),
            'wrong_format': lambda c: c['transport'].update(format='json'),
            'malformed_base64': lambda c: c['transport'].update(data_base64='!'),
            'wrong_retained_count': lambda c: c.update(stdout_bytes_retained=len(raw) - 1),
            'wrong_received_count': lambda c: c.update(stdout_bytes_received=len(raw) + 1),
            'wrong_cap': lambda c: c.update(capture_limit_bytes=len(raw) - 1),
            'wrong_truncation': lambda c: c.update(stdout_truncated=True),
            'missing_raw_receipt': lambda c: c.update(transport=None, transport_admission='malformed'),
        }
        for name, mutate in mutations.items():
            with self.subTest(control=name):
                client = copy.deepcopy(baseline); mutate(client)
                self.assertTrue(validate_client(client, None), name)
        self.assertTrue(validate_client(baseline, dict(pid=42)), 'rejected bytes supplied a host result')
        # Canonical padding is checked independently, not only alphabet/length.
        client = self.rejected_client(b'a')
        client['transport']['data_base64'] = 'YR=='
        self.assertTrue(validate_client(client, None), 'noncanonical base64 accepted')
        # A valid capture deliberately wrapped as rejected cannot acquire facts
        # through independent structural decoding or masquerade as a refusal.
        self.assertTrue(validate_client(self.rejected_client(valid, parse_error=None), None))



class PorcelainGeneratorTests(receipts.TestCase):
    """Literal invalid inputs must fail through the command without changing outputs."""
    OUTPUTS = ('runner/Sources/PWRunnerCore/PWPorcelainRecords.swift',
               'controller/src/porcelain_records.rs', 'tests/lib/porcelain_schema.py')

    @staticmethod
    def fingerprint(raw):
        tree = ast.parse(raw)
        return next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'SCHEMA_FINGERPRINT'
                            for target in node.targets))

    def fixture(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-porcelain-generator-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        paths = fixture_inputs.generator_inputs(ROOT, 'porcelain')
        fixture_inputs.copy_declared(ROOT, root, paths)
        (root / 'unowned-sentinel').write_bytes(b'outside generator ownership\n')
        self.track_inputs(root)
        return root

    def command(self, root, *args):
        return self.run_command([sys.executable, '-B', '-S', str(root / 'docs/generate_porcelain.py'), *args],
                                cwd=root, capture_output=True, text=True, timeout=60)

    def refused_unchanged(self, root, diagnostic):
        before = fixture_inputs.snapshot(root)
        result = self.command(root)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(diagnostic, result.stderr)
        self.assertEqual(fixture_inputs.snapshot(root), before, 'refused generation changed the fixture')

    def test_literal_invalid_ids_variants_and_cycles_do_not_write(self):
        source = json.loads((ROOT / 'docs/porcelain.json').read_text())

        def variant_tag(data, tag):
            value = data['variants']['PWDispositionValue'].pop('1')
            data['variants']['PWDispositionValue'][tag] = value

        def deep_graph(data):
            # Thirty-two record edges plus a scalar exceed the 32-value wire depth.
            for index in range(32):
                value_type = 'Deep' + str(index + 1) if index < 31 else 'String'
                data['records'].append(dict(id=1000 + index, name='Deep' + str(index), fields=[
                    dict(tag=1, name='child', swift_name='child', swift_type=value_type, mutable=True)]))
            data['records'][0]['fields'][0]['swift_type'] = 'Deep0'

        mutations = [
            ('boolean_record_id', lambda d: d['records'][0].update(id=True), 'invalid record ID'),
            ('boolean_field_tag', lambda d: d['records'][0]['fields'][0].update(tag=True), 'invalid field tag'),
            ('zero_variant_tag', lambda d: variant_tag(d, '0'), 'invalid variant tag'),
            ('noncanonical_variant_tag', lambda d: variant_tag(d, '01'), 'invalid variant tag'),
            ('overflow_variant_tag', lambda d: variant_tag(d, '65536'), 'invalid variant tag'),
            ('nonnumeric_variant_tag', lambda d: variant_tag(d, 'x'), 'invalid variant tag'),
            ('unknown_variant_type', lambda d: d['variants']['PWDispositionValue']['1'].update(type='NoSuchRecord'),
             'unknown variant type'),
            ('invalid_variant_name', lambda d: d['variants'].update({'invalid-name': {'1': {'name': 'Case', 'type': 'Int'}}}),
             'invalid variant name'),
            ('primitive_variant_name', lambda d: d['variants'].update({'String': {'1': {'name': 'Case', 'type': 'Int'}}}),
             'variant identity'),
            ('record_variant_name', lambda d: d['variants'].update({'CompiledProfileCapture': {'1': {'name': 'Case', 'type': 'Int'}}}),
             'variant identity'),
            ('primitive_record_name', lambda d: d['records'][0].update(name='String'),
             'invalid/shadowed record name'),
            ('invalid_record_name', lambda d: d['records'][0].update(name='bad-name'),
             'invalid/shadowed record name'),
            ('invalid_case_name', lambda d: d['variants']['PWDispositionValue']['1'].update(name='invalid-name'),
             'invalid variant case'),
            ('recursive_record', lambda d: d['records'][0]['fields'][0].update(swift_type='CompiledProfileCapture?'),
             'recursive schema'),
            ('recursive_variant', lambda d: d['variants']['PWDispositionValue']['1'].update(type='PWDispositionValue'),
             'recursive schema'),
            ('deep_record_graph', deep_graph, 'schema exceeds wire depth'),
        ]
        for name, mutate, diagnostic in mutations:
            with self.subTest(control=name):
                root = self.fixture()
                candidate = copy.deepcopy(source)
                mutate(candidate)
                (root / 'docs/porcelain.json').write_text(json.dumps(candidate))
                self.refused_unchanged(root, diagnostic)

    def test_duplicate_json_keys_refuse_before_outputs_change(self):
        original = (ROOT / 'docs/porcelain.json').read_text()
        self.assertIn('"tag": 1', original)
        for name, raw in [
            ('root', '{"version": 1,' + original.lstrip()[1:]),
            ('nested', original.replace('"tag": 1', '"tag": 1, "tag": 1', 1)),
        ]:
            with self.subTest(control=name):
                root = self.fixture()
                (root / 'docs/porcelain.json').write_text(raw)
                self.refused_unchanged(root, 'duplicate schema key')

    def test_malformed_late_output_prevents_earlier_write(self):
        root = self.fixture()
        result = self.command(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        # The first whole output needs rewriting; the last cannot be decoded.
        (root / self.OUTPUTS[0]).write_bytes(b'stale Swift output control\n')
        (root / self.OUTPUTS[2]).write_bytes(b'\xff')
        self.refused_unchanged(root, 'utf-8')

    def test_comment_only_change_preserves_wire_fingerprint_and_codecs(self):
        root = self.fixture()
        result = self.command(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        before = {path: (root / path).read_bytes() for path in self.OUTPUTS}
        data = json.loads((root / 'docs/porcelain.json').read_text())
        first = data['records'][0]
        source_before = (root / first['source']).read_bytes()
        first['fields'][0].setdefault('doc', []).append('// Porcelain comment-only control.')
        (root / 'docs/porcelain.json').write_text(json.dumps(data))
        result = self.command(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotEqual((root / first['source']).read_bytes(), source_before)
        self.assertIn('// Porcelain comment-only control.', (root / first['source']).read_text())
        self.assertEqual(self.fingerprint((root / self.OUTPUTS[2]).read_bytes()),
                         self.fingerprint(before[self.OUTPUTS[2]]))
        for path in self.OUTPUTS:
            self.assertEqual((root / path).read_bytes(), before[path], path)
        result = self.command(root, '--check')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_one_sided_regeneration_is_stale_and_old_fingerprint_is_refused(self):
        for mutation in ('add_field', 'drop_field', 'renumber_tag', 'change_kind', 'add_unknown_record'):
            with self.subTest(mutation=mutation):
                root = self.fixture()
                result = self.command(root)
                self.assertEqual(result.returncode, 0, result.stderr)
                before = {path: (root / path).read_bytes() for path in self.OUTPUTS}
                data = json.loads((root / 'docs/porcelain.json').read_text())
                first = data['records'][0]
                if mutation == 'add_field':
                    first['fields'].append(dict(tag=max(f['tag'] for f in first['fields']) + 1,
                        name='porcelain_control', swift_name='porcelain_control', swift_type='String?',
                        mutable=True, default='nil', json_null=False))
                elif mutation == 'drop_field':
                    first['fields'].pop()
                elif mutation == 'renumber_tag':
                    first['fields'][-1]['tag'] += 1
                elif mutation == 'change_kind':
                    self.assertEqual(first['fields'][-1]['swift_type'], 'Int?')
                    first['fields'][-1]['swift_type'] = 'String?'
                else:
                    path = 'runner/Sources/PWRunnerCore/PorcelainUnknownControl.swift'
                    data['records'].append(dict(id=1000, name='PorcelainUnknownControl', source=path, fields=[]))
                    (root / path).write_text('struct PorcelainUnknownControl {\n'
                        '    // BEGIN GENERATED PORCELAIN PorcelainUnknownControl\n'
                        '    // END GENERATED PORCELAIN PorcelainUnknownControl\n}\n')
                (root / 'docs/porcelain.json').write_text(json.dumps(data))
                result = self.command(root)
                self.assertEqual(result.returncode, 0, result.stderr)
                for path in self.OUTPUTS:
                    self.assertNotEqual((root / path).read_bytes(), before[path], path)
                if mutation == 'add_field':
                    self.assertIn('var porcelain_control: String? = nil', (root / first['source']).read_text())
                self.assertEqual(self.command(root, '--check').returncode, 0)
                old = self.fingerprint(before[self.OUTPUTS[2]])
                new = self.fingerprint((root / self.OUTPUTS[2]).read_bytes())
                self.assertNotEqual(old, new)
                # The independent reader rejects the sender's old schema before
                # reading its payload; no generated encoder supplies this input.
                stale_frame = b'PWP1' + bytes.fromhex(old) + record(55)
                with patch.object(porcelain_schema, 'SCHEMA_FINGERPRINT', new):
                    with self.assertRaisesRegex(ValueError, 'fingerprint mismatch'):
                        porcelain.decode(stale_frame)
                (root / self.OUTPUTS[1]).write_bytes(before[self.OUTPUTS[1]])
                snapshot = fixture_inputs.snapshot(root)
                result = self.command(root, '--check')
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn('stale porcelain output: controller/src/porcelain_records.rs', result.stderr)
                self.assertEqual(fixture_inputs.snapshot(root), snapshot, '--check rewrote a stale side')


if __name__ == '__main__':
    sys.exit(receipts.timed_main(sys.modules[__name__], 'source_drift/porcelain_codec', 'porcelain'))
