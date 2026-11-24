"""Guard generated documentation (limits, matrix table, shared rules), inventory validation, and local docs links."""
import copy
import importlib.util
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'docs'))
sys.path.insert(0, str(ROOT / 'tests/lib'))
import receipts  # noqa: E402
import fixture_inputs  # noqa: E402
import markdown_reader  # noqa: E402
spec = importlib.util.spec_from_file_location('generate_limits', ROOT / 'docs/generate_limits.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)

class LimitsDocumentationTests(receipts.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / 'docs/limits.json').read_text())
        self.document = (ROOT / 'docs/LIMITS.md').read_text()
        self.contract = (ROOT / generator.CONTRACT_NAME).read_text()
        self.guide = (ROOT / 'docs/PolicyWitness.md').read_text()

    def checkout(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-guide-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        copied = fixture_inputs.copy_declared(ROOT, root, fixture_inputs.generator_inputs(ROOT, 'limits'))
        print(f'fixture: {copied.files} files, {copied.bytes} bytes, {copied.seconds:.3f} s')
        self.track_inputs(root)
        return root

    def command(self, root, *args):
        if root == ROOT:
            self.track_inputs(root, fixture_inputs.generator_inputs(root, 'limits'))
        start = time.perf_counter()
        result = self.run_command([sys.executable, '-B', '-S', str(root / 'docs/generate_limits.py'), *([] if root == ROOT else ['--publication']), *args],
                                cwd=root, capture_output=True, text=True, timeout=10)
        print(f'command: {" ".join(args)} rc={result.returncode} {time.perf_counter() - start:.3f} s')
        return result

    def load(self, data):
        with tempfile.TemporaryDirectory(prefix='pw-limits-') as directory:
            path = Path(directory) / 'limits.json'
            path.write_text(json.dumps(data))
            self.evidence.capture(path.parent, [path.name], 'manifest mutation')
            return generator.load_limits(path)

    def test_document_is_current(self):
        limits = self.load(self.manifest)
        self.assertEqual(self.document, generator.update_document(self.document, limits))
        generator.validate_guide(self.guide)
        result = self.command(ROOT, '--check', '--publication')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_contract_sources_render_public_spans_and_leave_support_and_examples(self):
        root = self.checkout()
        name = 'docs/contract/zz-limit-control.surface.md'
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        text = '''# Scalar control {scalar: surface}

Public allowance <!-- span limits.step_id.value -->STALE_PUBLIC<!-- /span --> UTF-8 bytes.

```contract
free.effect: Retain <!-- span limits.step_id.value -->STALE_FREE<!-- /span --> UTF-8 bytes.
context: "Metadata <!-- span limits.unknown -->unchanged<!-- /span -->"
```

## Evidence owner {support: owner}

Support <!-- span limits.unknown -->unchanged<!-- /span -->.

```contract
free.effect: Owner metadata <!-- span limits.unknown -->unchanged<!-- /span -->.
```

## Public example {example: example}

```text
<!-- span limits.unknown -->unchanged<!-- /span -->
```

<!-- BEGIN GENERATED FALSE_SOURCE_CLAIM -->
An authored source still has <!-- span limits.step_id.value -->STALE_PUBLIC<!-- /span --> UTF-8 bytes.
<!-- END GENERATED FALSE_SOURCE_CLAIM -->
'''
        path.write_text(text)
        nested_name = 'docs/contract/nested/ignored.surface.md'
        nested = root / nested_name
        nested.parent.mkdir()
        nested.write_text('Value <!-- span limits.unknown -->unchanged<!-- /span -->.\n')
        self.track_inputs(root, [name, nested_name])
        self.assertIn(name, generator.span_documents(root))
        self.assertIn(name, generator.input_paths(root))
        self.assertNotIn(nested_name, generator.span_documents(root))
        self.assertNotIn(nested_name, generator.input_paths(root))

        destination = root / 'staged-guide.md'
        destination.write_text('previous staged guide')
        before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
        for args in (('--check',), ('--stage-guide', str(destination))):
            result = self.command(root, *args)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(name, result.stderr)
            self.assertIn('stale span limits.step_id.value', result.stderr)
            self.assertEqual({p: p.read_bytes() for p in before}, before)
        result = self.command(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = next(row['value'] for row in self.manifest['limits'] if row['id'] == 'step_id')
        expected = text.replace('STALE_PUBLIC', str(value)).replace('STALE_FREE', str(value))
        self.assertEqual(path.read_text(), expected)
        self.assertEqual(nested.read_bytes(), before[nested])
        result = self.command(root, '--check')
        self.assertEqual(result.returncode, 0, result.stderr)
        original_mtime = path.stat().st_mtime_ns
        self.assertEqual(self.command(root).returncode, 0)
        self.assertEqual(path.stat().st_mtime_ns, original_mtime)

        path.write_text(expected.replace('limits.step_id.value', 'limits.unknown', 1))
        before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
        for args in (('--check',), ()):
            result = self.command(root, *args)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('unknown span limits.unknown', result.stderr)
            self.assertEqual({p: p.read_bytes() for p in before}, before)

    def test_matrix_table_equals_the_generator_output_for_every_fixture_row(self):
        rows = generator.load_matrix(ROOT / generator.MATRIX_NAME)
        self.assertEqual(self.contract, generator.update_contract(self.contract, rows))
        region = self.contract.split(generator.MATRIX_START)[1].split(generator.MATRIX_END)[0]
        table, = markdown_reader.parse(region).tables
        self.assertEqual([cells[0].text for cells in table.rows], [row['id'] for row in rows])

        def shown(cell):
            return cell.text, cell.code

        def expected(markup):
            inline = markdown_reader.parse(markup).inlines[0]
            return inline.text, inline.code
        for row, cells in zip(rows, table.rows):
            self.assertEqual([shown(c) for c in cells[1:3]], [expected(row['specimen']), expected(row['scenario'])], row['id'])
            self.assertEqual(shown(cells[3]), (row['query'], [row['query']]), row['id'])
            self.assertEqual(shown(cells[-1]), expected(row['control']), row['id'])
            limitations = row['comparison']['limitations']
            self.assertEqual(shown(cells[9]), (', '.join(limitations), limitations) if limitations else ('—', []), row['id'])

    def test_matrix_fixture_rejects_rows_the_table_cannot_render(self):
        rows = json.loads((ROOT / generator.MATRIX_NAME).read_text())
        mutations = [
            lambda d: d['rows'].append(copy.deepcopy(d['rows'][0])),
            lambda d: d['rows'][0].pop('control'),
            lambda d: d['rows'][0]['comparison'].pop('order'),
            lambda d: d['rows'][0]['comparison'].update(limitations='none'),
            lambda d: d.update(rows=[]),
        ]
        for mutate in mutations:
            data = copy.deepcopy(rows)
            mutate(data)
            with tempfile.TemporaryDirectory(prefix='pw-matrix-') as directory:
                path = Path(directory) / 'matrix.json'
                path.write_text(json.dumps(data))
                self.evidence.capture(path.parent, [path.name], 'manifest mutation')
                with self.assertRaises(ValueError):
                    generator.load_matrix(path)

    def test_check_and_staging_refuse_stale_or_incomplete_documents_without_writing(self):
        root = self.checkout()
        guide = root / 'docs/PolicyWitness.md'
        destination = root / 'staged.md'
        destination.write_bytes(b'previous')
        for label, change in [
            ('stale value', self.guide.replace('64 bytes<!-- /span -->', '63 bytes<!-- /span -->', 1)),
            ('companion file', self.guide + '\n[lookup](REQUEST.md)\n'),
            ('missing heading', self.guide + '\n[lookup](#missing-heading)\n'),
            ('reference', self.guide + '\n[lookup]: LIMITS.md\n'),
            ('image', self.guide + '\n![image](missing.png)\n'),
        ]:
            with self.subTest(label=label):
                self.assertNotEqual(change, self.guide)
                guide.write_text(change)
                outcome = self.command(root, '--stage-guide', str(destination))
                self.assertNotEqual(outcome.returncode, 0)
                self.assertEqual(guide.read_text(), change)
                self.assertEqual(destination.read_bytes(), b'previous')
        guide.write_text(self.guide)
        result = self.command(root, '--stage-guide', str(destination))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(destination.read_bytes(), guide.read_bytes())

    def test_every_value_has_an_exercised_owner(self):
        # Each of these tests compares its declared inventory IDs with its
        # actual checked IDs. An arbitrary source reference cannot stand in.
        owners = {
            'tests/suites/runner_abi_layout/limits.py',
            'tests/suites/runner_c_worker_harness/check_sysctl.py',
            'runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift',
            'runner/Tests/PWRunnerCoreTests/ReservationAdmissionTests.swift',
            'controller/src/run_flow.rs',
            'controller/src/request_patch.rs',
            'controller/src/runner_client.rs',
            'controller/src/porcelain.rs',
            'controller/src/bin/sbpl-check.rs',
            'controller/src/runner_manager.rs',
            'controller/src/runner_commands.rs',
        }
        for row in self.manifest['limits']:
            paths = {ref['path'] for ref in row['checks'] if ref['kind'] == 'value'}
            self.assertTrue(paths and paths <= owners, row['id'])

    def test_stale_and_missing_blocks_are_detected(self):
        limits = self.load(self.manifest)
        stale = self.document.replace('262,143', '262,144', 1)
        self.assertNotEqual(stale, generator.update_document(stale, limits))
        for broken in [self.document.replace(generator.END, ''), self.document + generator.START]:
            with self.assertRaises(ValueError):
                generator.update_document(broken, limits)

    def test_manifest_rejects_invalid_metadata_and_dangling_owners(self):
        mutations = [
            lambda d: d.update(schema_version=1),
            lambda d: d['limits'][0]['checks'][0].pop('form'),
            lambda d: d['limits'][0]['checks'][0].pop('kind'),
            lambda d: d['limits'][0]['checks'][0].update(form='control'),
            lambda d: d['limits'].append(copy.deepcopy(d['limits'][0])),
            lambda d: d['limits'][0].update(value=True),
            lambda d: d['limits'][0].update(unit='characters'),
            lambda d: d['limits'][0].update(behavior=''),
            lambda d: d['limits'][0].update(checks=[]),
            lambda d: d['limits'][0]['sources'][0].update(path='missing.c'),
            lambda d: d['limits'][0]['sources'][0].update(symbol='missing_symbol_xyz'),
            lambda d: d['limits'][0]['checks'][0].update(path='missing_test.py'),
        ]
        for mutate in mutations:
            data = copy.deepcopy(self.manifest)
            mutate(data)
            with self.assertRaises(ValueError):
                self.load(data)
        with self.assertRaises(ValueError):
            json.loads('{"value":1,"value":2}', object_pairs_hook=generator.unique_object)

    def test_rendering_preserves_handwritten_explanations(self):
        limits = self.load(self.manifest)
        before = ('handwritten introduction\n' + generator.START + '\n' + generator.END
                  + '\n' + generator.COVERAGE_START + '\n' + generator.COVERAGE_END
                  + '\nhandwritten end\n')
        rendered = generator.update_document(before, limits)
        self.assertTrue(rendered.startswith('handwritten introduction\n'))
        self.assertTrue(rendered.endswith('\nhandwritten end\n'))

    def test_staging_matches_the_signed_receipt_before_replacing_outputs(self):
        import build_contract
        import publication
        contract = build_contract.identity(ROOT)
        receipt = publication.record(ROOT, contract)
        with tempfile.TemporaryDirectory(prefix='pw-guide-stage-') as temporary:
            directory = Path(temporary)
            guide = directory / 'PolicyWitness.md'
            staged = directory / 'publication.json'
            signed = directory / 'signed.json'
            args = ('--stage-development', str(staged), '--build-contract', contract, '--signed-receipt', str(signed))
            guide.write_bytes(b'previous guide')
            staged.write_bytes(b'previous receipt')
            changed = copy.deepcopy(receipt)
            changed['guide']['sha256'] = '0' * 64
            publication.write(signed, changed)
            refused = self.command(ROOT, *args)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn('differs from the signed publication receipt', refused.stderr)
            self.assertEqual(guide.read_bytes(), b'previous guide')
            self.assertEqual(staged.read_bytes(), b'previous receipt')
            publication.write(signed, receipt)
            passed = self.command(ROOT, *args)
            self.assertEqual(passed.returncode, 0, passed.stderr)
            self.assertEqual(staged.read_bytes(), signed.read_bytes())
            self.assertEqual(guide.read_bytes(), (ROOT / publication.GUIDE).read_bytes())


class DevelopmentPublicationTests(receipts.TestCase):
    def test_signed_boundary_requires_exact_identity_and_complete_evidence(self):
        import hashlib
        import publication
        expected = publication.record(ROOT, 'development:control')
        self.assertEqual(expected['guide']['sha256'], hashlib.sha256((ROOT / publication.GUIDE).read_bytes()).hexdigest())
        self.assertEqual(publication.validate(expected, 'development:control'), expected)
        for change in (lambda x: x.pop('guide'), lambda x: x.update(status='current'),
                       lambda x: x['guide'].update(sha256='invalid'),
                       lambda x: x.update(build_contract='development:other')):
            value = copy.deepcopy(expected)
            change(value)
            with self.assertRaisesRegex(ValueError, 'inconsistent publication boundary'):
                publication.validate(value, 'development:control')


if __name__ == '__main__':
    sys.exit(receipts.timed_main(sys.modules[__name__], 'source_drift/limits_documentation', 'limits'))
