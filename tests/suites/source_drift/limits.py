"""Guard generated documentation, inventory validation, and local docs links."""
import copy
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
        self.guide = (ROOT / 'docs/PolicyWitness.md').read_text()

    def checkout(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-guide-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        paths = {'docs/generate_limits.py', 'docs/limits.json', 'docs/LIMITS.md',
                 'docs/PolicyWitness.md', 'build.sh'}
        for row in self.manifest['limits']:
            paths.update(ref['path'] for key in ['sources', 'checks'] for ref in row[key])
        for name in paths:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        return root

    def command(self, root, *args):
        return subprocess.run([sys.executable, '-B', str(root / 'docs/generate_limits.py'), *args],
                              cwd=root, capture_output=True, text=True, timeout=10)

    def load(self, data):
        with tempfile.TemporaryDirectory(prefix='pw-limits-') as directory:
            path = Path(directory) / 'limits.json'
            path.write_text(json.dumps(data))
            return generator.load_limits(path)

    def test_document_is_current(self):
        limits = self.load(self.manifest)
        self.assertEqual(self.document, generator.update_document(self.document, limits))
        self.assertEqual(self.guide, generator.update_guide(self.guide, self.document))
        subprocess.run([sys.executable, '-B', str(ROOT / 'docs/generate_limits.py'), '--check'], check=True)

    def test_shared_prose_and_all_rows_are_copied_without_repository_metadata(self):
        # Compare the actual document regions independently of update_guide.
        shared = self.document.split(generator.SHARED_START)[1].split(generator.SHARED_END)[0].strip()
        copied = self.guide.split(generator.GUIDE_START)[1].split(generator.GUIDE_END)[0].strip()
        expected = '\n'.join('#' + line if line.startswith('## ') else line
                             for line in shared.splitlines())
        self.assertEqual(copied, expected)
        for row in self.manifest['limits']:
            self.assertEqual(copied.count('(`' + row['id'] + '`)'), 1, row['id'])
        self.assertNotIn('Grounding and coverage', copied)
        self.assertNotIn('Maintaining this document', copied)

    def test_generation_updates_values_and_shared_prose_then_is_idempotent(self):
        root = self.checkout()
        manifest_path = root / 'docs/limits.json'
        data = json.loads(manifest_path.read_text())
        data['limits'][0]['value'] += 1
        manifest_path.write_text(json.dumps(data))
        source_path = root / 'docs/LIMITS.md'
        source_path.write_text(source_path.read_text().replace(
            'A profile accepted', 'An independently revised profile accepted', 1))
        guide_path = root / 'docs/PolicyWitness.md'
        outside_before = self.guide.split(generator.GUIDE_START)[0], self.guide.split(generator.GUIDE_END)[1]
        result = self.command(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        for path in [source_path, guide_path]:
            self.assertIn('262,144 UTF-8 bytes', path.read_text())
            self.assertIn('An independently revised profile accepted', path.read_text())
        guide = guide_path.read_text()
        self.assertEqual((guide.split(generator.GUIDE_START)[0], guide.split(generator.GUIDE_END)[1]), outside_before)
        before = source_path.read_bytes(), guide_path.read_bytes()
        self.assertEqual(self.command(root).returncode, 0)
        self.assertEqual((source_path.read_bytes(), guide_path.read_bytes()), before)
        result = self.command(root, '--check')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_check_and_staging_refuse_stale_or_incomplete_documents_without_writing(self):
        mutations = [
            ('LIMITS.md', lambda text: text.replace('262,143', '262,144', 1)),
            ('PolicyWitness.md', lambda text: text.replace('262,143', '262,144', 1)),
            ('LIMITS.md', lambda text: text.replace('A profile accepted', 'An edited profile accepted', 1)),
            ('PolicyWitness.md', lambda text: text.replace('A profile accepted', 'An edited profile accepted', 1)),
            ('PolicyWitness.md', lambda text: '\n'.join(line for line in text.splitlines()
                                                       if '(`policy_source`)' not in line)),
            ('PolicyWitness.md', lambda text: text.replace(generator.GUIDE_END, '')),
            ('PolicyWitness.md', lambda text: text + generator.GUIDE_START),
            ('LIMITS.md', lambda text: text.replace(generator.SHARED_END, '')),
            ('LIMITS.md', lambda text: text.replace(generator.COVERAGE_END, '')),
        ]
        for filename, mutate in mutations:
            with self.subTest(filename=filename, mutation=mutate):
                root = self.checkout()
                path = root / 'docs' / filename
                path.write_text(mutate(path.read_text()))
                source, guide = root / 'docs/LIMITS.md', root / 'docs/PolicyWitness.md'
                before = source.read_bytes(), guide.read_bytes()
                destination = root / 'release-guide.md'
                destination.write_text('previous release guide')
                for args in [('--check',), ('--stage-guide', str(destination))]:
                    result = self.command(root, *args)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertTrue('stale' in result.stderr or 'ordered block' in result.stderr, result.stderr)
                    self.assertEqual((source.read_bytes(), guide.read_bytes()), before)
                    self.assertEqual(destination.read_text(), 'previous release guide')

    def test_staged_guide_is_exact_and_standalone(self):
        root = self.checkout()
        with tempfile.TemporaryDirectory(prefix='pw-guide-release-') as release:
            destination = Path(release) / 'PolicyWitness.md'
            result = self.command(root, '--stage-guide', str(destination))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(destination.read_bytes(), (root / 'docs/PolicyWitness.md').read_bytes())
            self.assertEqual(list(Path(release).iterdir()), [destination])
            # Take the repository away; the copied section and internal links
            # must remain inspectable from the one shipped document.
            shutil.rmtree(root)
            with patch.object(generator, 'ROOT', root):
                generator.validate_guide(destination.read_text(), self.manifest['limits'])

    def test_shared_region_cannot_omit_tables_even_if_both_documents_would_agree(self):
        root = self.checkout()
        path = root / 'docs/LIMITS.md'
        text = path.read_text().replace(generator.SHARED_END, '')
        text = text.replace(generator.START, generator.SHARED_END + '\n' + generator.START, 1)
        path.write_text(text)
        before = (root / 'docs/PolicyWitness.md').read_bytes()
        result = self.command(root)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('exactly one limits row', result.stderr)
        self.assertEqual((root / 'docs/PolicyWitness.md').read_bytes(), before)

    def test_generation_rejects_dependencies_and_broken_anchors_even_when_source_is_updated(self):
        for link in ['[extra](LIMITS.md)', '[extra](limits.json)', '[extra](../tests/contract.md)',
                     '[extra](https://example.invalid/limits)', '[extra](#missing-section)',
                     '[extra][reference]\n\n[reference]: limits.json']:
            with self.subTest(link=link):
                root = self.checkout()
                path = root / 'docs/LIMITS.md'
                path.write_text(path.read_text().replace(generator.SHARED_START,
                    generator.SHARED_START + '\n\n' + link, 1))
                before = (root / 'docs/PolicyWitness.md').read_bytes()
                result = self.command(root)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual((root / 'docs/PolicyWitness.md').read_bytes(), before)
        root = self.checkout()
        path = root / 'docs/LIMITS.md'
        path.write_text(path.read_text().replace(generator.SHARED_START,
            generator.SHARED_START + '\n\nSee [admission](#specimen-admission).', 1))
        result = self.command(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        path = root / 'docs/PolicyWitness.md'
        path.write_text(path.read_text().replace('](#limits)', '](#missing-section)', 1))
        result = self.command(root, '--check')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('unresolved internal link', result.stderr)

    def test_build_refuses_stale_guide_before_signing_or_creating_output(self):
        root = self.checkout()
        path = root / 'docs/PolicyWitness.md'
        path.write_text(path.read_text().replace('262,143', '262,144', 1))
        destination = root / 'dist'
        result = subprocess.run(['bash', str(root / 'build.sh')], cwd=root,
            env={**os.environ, 'IDENTITY': '', 'YOLO': '', 'DIST_DIR': str(destination)},
            capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('stale PolicyWitness.md', result.stderr)
        self.assertFalse(destination.exists())

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
        before = ('handwritten introduction\n' + generator.START + '\n' + generator.END
                  + '\n' + generator.COVERAGE_START + '\n' + generator.COVERAGE_END
                  + '\nhandwritten end\n')
        rendered = generator.update_document(before, limits)
        self.assertTrue(rendered.startswith('handwritten introduction\n'))
        self.assertTrue(rendered.endswith('\nhandwritten end\n'))

    def test_links_in_moved_and_routing_documents(self):
        paths = list((ROOT / 'docs').glob('*.md')) + [ROOT / name for name in
            ['README.md', 'AGENTS.md', 'tests/README.md']]
        self.assertEqual(broken_links(paths), [])
        with tempfile.TemporaryDirectory(prefix='pw-link-') as directory:
            path = Path(directory) / 'doc.md'
            path.write_text('[missing](missing.md) [web](https://example.com)')
            self.assertEqual(len(broken_links([path])), 1)


if __name__ == '__main__':
    unittest.main()
