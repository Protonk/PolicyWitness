"""Footprint inventory, generated copies and refusal controls."""
import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'docs'))
import receipts
import fixture_inputs
spec = importlib.util.spec_from_file_location('generate_footprint', ROOT / 'docs/generate_footprint.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class FootprintDocumentationTests(receipts.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / generator.MANIFEST_NAME).read_text())

    def load(self, data):
        with tempfile.TemporaryDirectory(prefix='pw-footprint-manifest-') as directory:
            path = Path(directory) / 'footprint.json'
            path.write_text(json.dumps(data))
            self.evidence.capture(path.parent, [path.name], 'manifest mutation')
            return generator.load_manifest(path, ROOT)

    def command(self, root, *args):
        self.track_inputs(root, fixture_inputs.generator_inputs(root, 'footprint'))
        return self.run_command([sys.executable, '-B', '-S', str(root / generator.GENERATOR_NAME), *args],
                                cwd=root, capture_output=True, text=True, timeout=60)

    def test_current_document(self):
        result = self.command(ROOT, '--check')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_strict_manifest(self):
        self.load(self.manifest)
        mutations = [
            lambda d: d.update(schema_version=True),
            lambda d: d.update(extra='unknown'),
            lambda d: d['rows'].append(copy.deepcopy(d['rows'][0])),
            lambda d: d['rows'][0]['quantity'].update(evidence='guess'),
            lambda d: d['rows'][0]['quantity'].update(value=-1, unit='bytes'),
            lambda d: d['rows'][0]['quantity'].update(limit='missing_limit'),
            lambda d: d['rows'][0]['subject'].update(kind='unknown'),
            lambda d: d['rows'][0]['checks'][0].update(kind='unknown'),
            lambda d: d['rows'][0]['checks'][0].update(pins=''),
            lambda d: d['rows'][0]['checks'][0].update(symbol='missing_footprint_assertion'),
            lambda d: d['rows'][0]['sources'][0].update(path='../outside'),
            lambda d: d['rows'][0].update(conditions='7 bytes'),
        ]
        for mutate in mutations:
            data = copy.deepcopy(self.manifest)
            mutate(data)
            with self.assertRaises(ValueError):
                self.load(data)
        with self.assertRaises(ValueError):
            json.loads('{"x":1,"x":2}', object_pairs_hook=generator.unique_object)

    def test_stale_refusal_and_no_check_writes(self):
        with tempfile.TemporaryDirectory(prefix='pw-footprint-check-') as directory:
            root = Path(directory)
            fixture_inputs.copy_declared(ROOT, root, fixture_inputs.generator_inputs(ROOT, 'footprint'))
            path = root / self.manifest['document']
            path.write_text(path.read_text().replace('| fw1 |', '| stale |', 1))
            before = fixture_inputs.snapshot(root)
            result = self.command(root, '--check')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('stale footprint', result.stderr)
            self.assertEqual(fixture_inputs.snapshot(root), before)

    def test_regions_spans_and_authored_text(self):
        data = self.load(self.manifest)
        path = ROOT / data['document']
        content = path.read_text()
        rendered = generator.render_document(content, data)
        self.assertEqual(rendered, content)
        value = next(iter(generator.span_values(data)))
        authored = f'\nQuantity <!-- span footprint.{value} -->stale<!-- /span -->.\n'
        output = generator.render_document(content + authored, data)
        self.assertIn(generator.span_values(data)[value], output[len(content):])
        with self.assertRaises(ValueError):
            generator.render_document(content + '\nValue <!-- span footprint.missing -->x<!-- /span -->.\n', data)
        with self.assertRaises(ValueError):
            generator.render_document(content.replace('<!-- END GENERATED FOOTPRINT WAITING -->', ''), data)


if __name__ == '__main__':
    sys.exit(receipts.timed_main(sys.modules[__name__], 'source_drift/footprint_documentation', 'footprint'))
