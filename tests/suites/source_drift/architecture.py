"""Guard the architecture manifest and its generated dot, SVG and document copies."""
import copy
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('generate_architecture', ROOT / 'docs/generate_architecture.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class ArchitectureDocumentationTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / generator.MANIFEST_NAME).read_text())
        self.document = ROOT / self.manifest['document']
        self.figures = [self.document.parent / f"{g['file']}{suffix}"
                        for g in self.manifest['graphs'] for suffix in ('.dot', '.svg')]

    def checkout(self):
        """A disposable checkout holding the generator's inputs and outputs and every cited file."""
        directory = tempfile.TemporaryDirectory(prefix='pw-architecture-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        paths = {'docs/generator_common.py', 'tests/catalog.json', generator.GENERATOR_NAME, generator.MANIFEST_NAME, self.manifest['document']}
        paths.update(str(p.relative_to(ROOT)) for p in self.figures)
        for graph in self.manifest['graphs']:
            for item in graph['nodes'] + graph['edges']:
                paths.update(ref['path'] for key in ('sources', 'checks') for ref in item[key])
        for name in paths:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        return root

    def command(self, root, *args):
        return subprocess.run([sys.executable, '-B', str(root / generator.GENERATOR_NAME), *args],
                              cwd=root, capture_output=True, text=True, timeout=60)

    def load(self, data):
        with tempfile.TemporaryDirectory(prefix='pw-arch-manifest-') as directory:
            path = Path(directory) / 'architecture.json'
            path.write_text(json.dumps(data))
            return generator.load_manifest(path, ROOT)

    def test_document_and_figures_are_current(self):
        result = self.command(ROOT, '--check')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith('ok: architecture manifest'), result.stdout)
        for path in self.figures:
            self.assertTrue(path.is_file(), path)

    def test_manifest_rejects_broken_citations_references_and_ids(self):
        self.load(self.manifest)  # the real manifest validates
        graph = self.manifest['graphs'][0]
        node = graph['nodes'][0]
        edge = graph['edges'][0]
        mutations = {
            'missing symbol': lambda d: d['graphs'][0]['nodes'][0]['sources'][0].__setitem__('symbol', 'no_such_symbol_9f3'),
            'missing file': lambda d: d['graphs'][0]['nodes'][0]['sources'][0].__setitem__('path', 'docs/no-such-file.md'),
            'unknown edge end': lambda d: d['graphs'][0]['edges'][0].__setitem__('to', 'no_such_node'),
            'duplicate node id': lambda d: d['graphs'][0]['nodes'].append(copy.deepcopy(node)),
            'duplicate edge id': lambda d: d['graphs'][0]['edges'].append(copy.deepcopy(edge)),
            'no sources': lambda d: d['graphs'][0]['edges'][0].__setitem__('sources', []),
            'unknown kind': lambda d: d['graphs'][0]['nodes'][0].__setitem__('kind', 'no_such_kind'),
            'cluster names unknown node': lambda d: d['graphs'][0]['clusters'][0]['nodes'].append('no_such_node'),
            'unknown field': lambda d: d['graphs'][0]['nodes'][0].__setitem__('colour', 'red'),
            'old schema': lambda d: d.update(schema_version=1),
            'missing form': lambda d: d['graphs'][0]['nodes'][0]['checks'][0].pop('form'),
            'invalid form': lambda d: d['graphs'][0]['nodes'][0]['checks'][0].update(form='maybe'),
            'self citation': lambda d: d['graphs'][0]['nodes'][0]['sources'][0].update(path='docs/architecture.json', symbol='schema_version'),
            'empty note': lambda d: d['graphs'][0]['nodes'][0].__setitem__('note', ' '),
        }
        for name, mutate in mutations.items():
            data = copy.deepcopy(self.manifest)
            mutate(data)
            with self.assertRaises(ValueError, msg=name):
                self.load(data)

    def test_every_id_is_in_its_generated_region(self):
        text = self.document.read_text()
        for graph in self.manifest['graphs']:
            start = generator.REGION_START.format(graph=graph['id'])
            end = generator.REGION_END.format(graph=graph['id'])
            region = text.split(start)[1].split(end)[0]
            self.assertIn(f"{graph['file']}.svg", region)
            for item in graph['nodes'] + graph['edges']:
                self.assertIn(f"| {item['id']} |", region, (graph['id'], item['id']))
            unpinned = [i['id'] for i in graph['nodes'] + graph['edges'] if not i['checks']]
            if unpinned:
                self.assertIn('Claims without a cited check:', region)
                for ident in unpinned:
                    self.assertIn(f"`{ident}`", region.split('Claims without a cited check:')[1])
            else:
                self.assertIn('Every node and edge above cites at least one test or rule.', region)

    def test_svg_stamps_name_their_dot_text(self):
        document_name = self.document.name
        for graph in self.manifest['graphs']:
            dot_text = generator.render_dot(graph, self.manifest['styles'], document_name)
            svg = (self.document.parent / f"{graph['file']}.svg").read_text(errors='replace')
            self.assertTrue(generator.svg_stamp_matches(svg, graph['id'], dot_text), graph['id'])
            self.assertFalse(generator.svg_stamp_matches(svg, graph['id'], dot_text + '\n'))
            self.assertFalse(generator.svg_stamp_matches(svg, 'other_graph', dot_text))

    def test_stale_copies_are_refused_then_regenerated_idempotently(self):
        root = self.checkout()
        self.assertEqual(self.command(root, '--check').returncode, 0)
        graph = self.manifest['graphs'][0]
        dot_path = root / self.manifest['document'].rsplit('/', 1)[0] / f"{graph['file']}.dot"
        svg_path = dot_path.with_suffix('.svg')
        document = root / self.manifest['document']
        originals = {p: p.read_text(errors='replace') for p in (dot_path, svg_path, document)}
        for path, mutate, expected in (
            (dot_path, lambda t: t.replace('rankdir=', 'rankdir = '), 'stale or missing'),
            (svg_path, lambda t: t.replace('dot sha256 ', 'dot sha256 0'), 'stamp does not name'),
            (document, lambda t: t.replace(f"| {graph['nodes'][0]['id']} |", f"| {graph['nodes'][0]['id']}x |", 1), 'regions are stale'),
        ):
            path.write_text(mutate(originals[path]))
            result = self.command(root, '--check')
            self.assertEqual(result.returncode, 1, (path.name, result.stdout))
            self.assertIn(expected, result.stderr, path.name)
            self.assertEqual(path.read_text(errors='replace'), mutate(originals[path]), 'check wrote')
        # Regeneration restores the dot text and the document without Graphviz; the
        # SVG stays stale until rendered, and the check says so.
        result = self.command(root, '--skip-svg')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(dot_path.read_text(), originals[dot_path])
        self.assertEqual(document.read_text(), originals[document])
        result = self.command(root, '--check')
        self.assertEqual(result.returncode, 1)
        self.assertIn('stamp does not name', result.stderr)
        self.assertNotIn('stale or missing', result.stderr)
        svg_path.write_text(originals[svg_path])
        self.assertEqual(self.command(root, '--check').returncode, 0)
        second = self.command(root, '--skip-svg')
        self.assertEqual(second.returncode, 0)
        self.assertIn('wrote nothing', second.stdout)

    def test_broken_marker_or_citation_stops_before_any_write(self):
        root = self.checkout()
        document = root / self.manifest['document']
        before = {p: p.read_text(errors='replace') for p in root.rglob('*') if p.is_file()}
        graph = self.manifest['graphs'][0]
        text = document.read_text()
        document.write_text(text.replace(generator.REGION_END.format(graph=graph['id']), '', 1))
        result = self.command(root, '--skip-svg')
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn('expected exactly one ordered block', result.stderr)
        document.write_text(text)
        manifest_path = root / generator.MANIFEST_NAME
        data = json.loads(manifest_path.read_text())
        data['graphs'][0]['edges'][0]['sources'][0]['symbol'] = 'no_such_symbol_9f3'
        manifest_path.write_text(json.dumps(data))
        result = self.command(root, '--skip-svg')
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn('missing symbol', result.stderr)
        manifest_path.write_text(before[manifest_path])
        after = {p: p.read_text(errors='replace') for p in root.rglob('*') if p.is_file()}
        self.assertEqual(before, after, 'a refused generation changed the checkout')


if __name__ == '__main__':
    unittest.main()
