"""Guard generated documentation, inventory validation, and local docs links."""
import copy
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('generate_limits', ROOT / 'docs/generate_limits.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def broken_links(paths):
    broken = []
    for path in paths:
        # Local Markdown file links, including generated source/test references.
        # Ignore anchors and URL schemes; no network requests are made.
        for target in re.findall(r'\]\(([^\s)]+)\)', path.read_text()):
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                continue
            target = target.split('#', 1)[0]
            if target and not (path.parent / target).exists():
                broken.append(f'{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}: {target}')
    return broken


class LimitsDocumentationTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / 'docs/limits.json').read_text())
        self.document = (ROOT / 'docs/LIMITS.md').read_text()

    def load(self, data):
        with tempfile.TemporaryDirectory(prefix='pw-limits-') as directory:
            path = Path(directory) / 'limits.json'
            path.write_text(json.dumps(data))
            return generator.load_limits(path)

    def test_document_is_current(self):
        limits = self.load(self.manifest)
        self.assertEqual(self.document, generator.update_document(self.document, limits))
        subprocess.run([sys.executable, str(ROOT / 'docs/generate_limits.py'), '--check'], check=True)

    def test_every_value_has_an_exercised_owner(self):
        # Each of these tests compares its declared inventory IDs with its
        # actual checked IDs. An arbitrary source reference cannot stand in.
        owners = {
            'tests/suites/runner_abi_layout/limits.py',
            'runner/Tests/PWRunnerCoreTests/LimitsContractTests.swift',
            'controller/src/run_flow.rs',
            'controller/src/bin/sbpl-check.rs',
            'controller/src/bin/sandbox-log-observer.rs',
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
        before = 'handwritten introduction\n' + generator.START + '\n' + generator.END + '\nhandwritten end\n'
        rendered = generator.update_document(before, limits)
        self.assertTrue(rendered.startswith('handwritten introduction\n'))
        self.assertTrue(rendered.endswith('\nhandwritten end\n'))

    def test_links_in_moved_and_routing_documents(self):
        paths = list((ROOT / 'docs').glob('*.md')) + [ROOT / name for name in
            ['README.md', 'AGENTS.md', 'PolicyWitness.md', 'tests/README.md']]
        self.assertEqual(broken_links(paths), [])
        with tempfile.TemporaryDirectory(prefix='pw-link-') as directory:
            path = Path(directory) / 'doc.md'
            path.write_text('[missing](missing.md) [web](https://example.com)')
            self.assertEqual(len(broken_links([path])), 1)


if __name__ == '__main__':
    unittest.main()
