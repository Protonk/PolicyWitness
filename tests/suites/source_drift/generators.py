"""Uniform generator contracts, measurements and adversarial controls."""
import copy
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GENERATORS = ('contract', 'worker_identity', 'limits', 'architecture')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def build_checks(text):
    lines = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith('#')]
    signing = next(i for i, line in enumerate(lines) if re.search(r'^\s*codesign\s+--force', line))
    return {name for name in GENERATORS if any(
        re.search(r'/generate_' + name + r'\.py"\s+--check\s*$', line)
        for line in lines[:signing])}


def ownership(root, name):
    """Explicit regions and whole-file outputs; never infer ownership from a diff."""
    gen = module('owner_' + name, root / f'docs/generate_{name}.py')
    if name == 'contract':
        return {p: [(a, b) for a, b, _ in rs] for p, rs in gen.TARGETS.items()}, set()
    if name == 'worker_identity':
        regions = {}
        for p in gen.TARGETS:
            lines, start, end = gen.bounds((root / p).read_text())
            regions[p] = [(lines[start].rstrip('\n'), lines[end].rstrip('\n'))]
        return regions, set()
    if name == 'limits':
        return {'docs/LIMITS.md': [(gen.START, gen.END), (gen.COVERAGE_START, gen.COVERAGE_END)],
                gen.CONTRACT_NAME: [(gen.MATRIX_START, gen.MATRIX_END)],
                'docs/PolicyWitness.md': [(gen.GUIDE_START, gen.GUIDE_END),
                    (gen.GUIDE_QUESTIONS_START, gen.GUIDE_QUESTIONS_END),
                    (gen.GUIDE_RULES_START, gen.GUIDE_RULES_END)]}, set()
    data = json.loads((root / gen.MANIFEST_NAME).read_text())
    return {data['document']: [(gen.REGION_START.format(graph=g['id']),
                                gen.REGION_END.format(graph=g['id'])) for g in data['graphs']]}, {
        str(Path(data['document']).parent / (g['file'] + suffix))
        for g in data['graphs'] for suffix in ('.dot', '.svg')}


def outside(data, regions):
    if not regions:
        return data
    text = data.decode()
    for start, end in regions:
        if text.count(start) != 1 or text.count(end) != 1 or text.index(start) >= text.index(end):
            raise ValueError('broken ownership markers')
        a = text.index(start) + len(start)
        b = text.index(end)
        text = text[:a] + text[b:]
    return text


def changed_outside(before, after, regions, whole):
    changed = []
    for path in before.keys() | after.keys():
        if path in whole:
            continue
        if path not in before or path not in after:
            changed.append(path)
        elif outside(before[path], regions.get(path, [])) != outside(after[path], regions.get(path, [])):
            changed.append(path)
    return changed


class GeneratorContractTests(unittest.TestCase):
    def checkout(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-generators-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        # Source files only; never copy build products or accumulated evidence.
        names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others',
                                         '--exclude-standard'], cwd=ROOT).decode().split('\0')
        for name in filter(None, names):
            source = ROOT / name
            if not source.is_file():
                continue
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return root

    def command(self, root, name, *args):
        return subprocess.run([sys.executable, '-B', str(root / f'docs/generate_{name}.py'), *args],
                              cwd=root, capture_output=True, text=True, timeout=60)

    def snapshot(self, root):
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*')
                if p.is_file() and '__pycache__' not in p.parts}

    def test_build_checks_every_generator_before_signing(self):
        text = (ROOT / 'build.sh').read_text()
        self.assertEqual(build_checks(text), set(GENERATORS))
        for name in GENERATORS:
            changed = '\n'.join(line for line in text.splitlines()
                                if not (f'generate_{name}.py' in line and '--check' in line))
            self.assertNotEqual(build_checks(changed), set(GENERATORS), name)

    def test_regeneration_changes_nothing_outside_regions(self):
        for name in GENERATORS:
            with self.subTest(generator=name):
                root = self.checkout()
                regions, whole = ownership(root, name)
                if name == 'worker_identity':
                    path = root / 'controller/tools/pw_probe_runner/pw_probe_runner.c'
                    path.write_text(path.read_text() + '\n/* identity property control */\n')
                else:
                    path = root / f'docs/{name}.json'
                    data = json.loads(path.read_text())
                    if name == 'contract':
                        data['versions']['response_schema'] += 1
                    elif name == 'limits':
                        data['limits'][0]['value'] += 1
                    else:
                        data['graphs'][0]['nodes'][0]['label'] += ' property control'
                    path.write_text(json.dumps(data))
                before = self.snapshot(root)
                result = self.command(root, name, *(['--skip-svg'] if name == 'architecture' else []))
                self.assertEqual(result.returncode, 0, result.stderr)
                after = self.snapshot(root)
                self.assertNotEqual(before, after)
                self.assertEqual(changed_outside(before, after, regions, whole), [])
                # A real command that corrupts bytes past its END marker must fail the property.
                target = next(iter(regions))
                script = root / f'docs/generate_{name}.py'
                script.write_text(script.read_text().replace('sys.exit(main())',
                    'code = main()\n    target = ROOT / ' + repr(target) +
                    '\n    target.write_text(target.read_text() + "x")\n    sys.exit(code)'))
                before = self.snapshot(root)
                result = self.command(root, name, *(['--skip-svg'] if name == 'architecture' else []))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(changed_outside(before, self.snapshot(root), regions, whole), [target])

    def refuse_manifest(self, name, mutate, expected):
        root = self.checkout()
        path = root / f'docs/{name}.json'
        data = json.loads(path.read_text())
        mutate(data)
        path.write_text(json.dumps(data))
        before = self.snapshot(root)
        for args in [('--check',), ('--skip-svg',) if name == 'architecture' else ()]:
            result = self.command(root, name, *args)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn(expected, result.stderr)
            self.assertEqual(self.snapshot(root), before, 'refusal changed checkout')

    def test_check_citations_carry_a_form_and_tests_are_defined(self):
        gen = module('architecture_checks', ROOT / 'docs/generate_architecture.py')
        gen.load_manifest(ROOT / gen.MANIFEST_NAME)
        node = lambda d: d['graphs'][0]['nodes'][0]
        for mutate, message in [
            (lambda d: node(d)['checks'][0].pop('form'), 'malformed checks'),
            (lambda d: node(d).update(checks=[dict(path='tests/fixtures/byoxpc/session.py', symbol='install', form='test')]), 'not defined'),
            (lambda d: node(d).update(checks=[dict(path='tests/fixtures/byoxpc/session.py', symbol='install', form='control')]), 'at least one test or rule'),
            (lambda d: node(d).update(checks=[dict(path='tests/suites/source_drift/generators.py', symbol='build_checks', form='rule')]), 'not defined'),
        ]:
            self.refuse_manifest('architecture', mutate, message)

    def test_limits_check_forms_and_value_owners(self):
        gen = module('limits_checks', ROOT / 'docs/generate_limits.py')
        gen.load_limits(ROOT / 'docs/limits.json')
        for mutate, message in [
            (lambda d: d['limits'][0]['checks'][0].pop('form'), 'malformed checks'),
            (lambda d: d['limits'][0]['checks'][0].pop('kind'), 'malformed checks'),
            (lambda d: d['limits'][0]['checks'][0].update(form='control'), 'not defined'),
            (lambda d: d['limits'][0]['checks'][0].update(path='tests/fixtures/byoxpc/session.py', symbol='install', form='control'), 'value owner'),
            (lambda d: d['limits'][0]['sources'][0].update(path='docs/LIMITS.md', symbol='BEGIN GENERATED LIMITS'), 'self-citation'),
        ]:
            self.refuse_manifest('limits', mutate, message)

    def test_manifests_do_not_cite_themselves_or_their_outputs(self):
        self.refuse_manifest('architecture', lambda d: d['graphs'][0]['nodes'][0].update(
            sources=[dict(path=d['document'], symbol='BEGIN GENERATED ARCHITECTURE GRAPH')]), 'self-citation')

    def test_captions_state_the_verified_guarantee(self):
        gen = module('architecture_caption', ROOT / 'docs/generate_architecture.py')
        data = gen.load_manifest(ROOT / gen.MANIFEST_NAME)
        def verified(text):
            return ('presence' in text and 'definition' in text and
                    'whether a test asserts the row is not verified' in text and
                    not re.search(r'\b(exercises|covers|proves)\b', text))
        for graph in data['graphs']:
            region = gen.render_region(graph, 'ARCHITECTURE.md')
            caption = next(line for line in region.splitlines() if line.startswith('*Figure:'))
            summary = next(line for line in region.splitlines() if line.startswith('<summary>'))
            for text in (caption, summary):
                self.assertTrue(verified(text))
                self.assertFalse(verified(text.replace('whether a test asserts the row is not verified', '')))
                for word in ('exercises', 'covers', 'proves'):
                    self.assertFalse(verified(text + ' ' + word))


if __name__ == '__main__':
    unittest.main()
