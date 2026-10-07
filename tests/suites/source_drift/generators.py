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
    regions, whole = region_ownership(root, name)
    if name in {'limits', 'architecture'}:
        gen = module('span_owner_' + name, root / f'docs/generate_{name}.py')
        common = module('span_common', root / 'docs/generator_common.py')
        for document in gen.SPAN_DOCUMENTS:
            for match in common.authored_spans((root / document).read_text()):
                if match[1].startswith(name + '.'):
                    regions.setdefault(document, []).append((f'<!-- span {match[1]} -->', '<!-- /span -->'))
    return regions, whole


def region_ownership(root, name):
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
        if text.count(start) != 1 or (not start.startswith('<!-- span ') and text.count(end) != 1) or end not in text[text.index(start):]:
            raise ValueError('broken ownership markers')
        a = text.index(start) + len(start)
        b = text.index(end, a)
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

    def test_fact_keys_are_declared_and_columns_follow_the_declaration(self):
        gen = module('architecture_columns', ROOT / 'docs/generate_architecture.py')
        data = gen.load_manifest(ROOT / gen.MANIFEST_NAME)
        for graph in data['graphs']:
            if graph['id'] == 'byoxpc':
                self.assertLessEqual(len(graph['node_facts']), 8)
            # Reverse the declaration so collecting keys from items cannot satisfy this check.
            graph['node_facts'].reverse()
            graph['edge_facts'].reverse()
            region = gen.render_region(graph, 'ARCHITECTURE.md')
            for kind, leading in [('node', ['Id', 'Node', 'Kind']), ('edge', ['Id', 'From', 'To', 'Kind', 'Edge'])]:
                expected = '| ' + ' | '.join(leading + graph[kind + '_facts'] + ['Sources', 'Checks', 'Limits']) + ' |'
                self.assertIn(expected, region)
                collected = gen._fact_columns(graph[kind + 's'])
                if len(collected) > 1:
                    self.assertNotEqual(collected, graph[kind + '_facts'])
        for mutate in [
            lambda d: d['graphs'][0]['nodes'][0]['facts'].update(Unknown='control'),
            lambda d: d['graphs'][0]['node_facts'].append('Unused'),
        ]:
            self.refuse_manifest('architecture', mutate, 'undeclared or unused')

    def test_durations_and_sizes_render_from_limits(self):
        gen = module('architecture_limits', ROOT / 'docs/generate_architecture.py')
        data = gen.load_manifest(ROOT / gen.MANIFEST_NAME)
        rows = gen.generate_limits.load_limits(ROOT / 'docs/limits.json')
        table = gen.generate_limits.render(rows)
        for graph in data['graphs']:
            rendered = gen.render_region(graph, 'ARCHITECTURE.md', rows)
            dot = gen.render_dot(graph, data['styles'], 'ARCHITECTURE.md', rows)
            self.assertNotIn('{limit:', dot)
            for ident in gen.limit_ids(graph):
                row = next(row for row in rows if row['id'] == ident)
                cell = gen.format_value(row['value'], row['unit'])
                self.assertIn(cell, table)
                self.assertIn(cell, rendered)
                self.assertIn(cell, dot)
                self.assertIn(f'[`{ident}`](LIMITS.md#', rendered)
        self.assertEqual(gen.format_value(1, 'seconds'), '1 second')
        for literal in ['7 seconds', '7 ms', '7 MiB', 'seven seconds', '7-second']:
            self.refuse_manifest('architecture', lambda d: d['graphs'][0]['nodes'][0].update(note=literal), 'literal duration or size')
        self.refuse_manifest('architecture', lambda d: d['graphs'][0]['nodes'][0].update(note='{limit:missing}'), 'unknown limit')
        root = self.checkout()
        path = root / 'docs/limits.json'
        data = json.loads(path.read_text())
        next(row for row in data['limits'] if row['id'] == 'host_exit_delay')['value'] += 1
        path.write_text(json.dumps(data))
        before = {p: (root / p).read_bytes() for p in ['docs/limits.json', 'docs/LIMITS.md']}
        # A deterministic renderer fixture makes stamp checks independent of installed Graphviz.
        script = root / 'docs/generate_architecture.py'
        script.write_text(script.read_text().replace('def render_svg(dot_text):',
            'def render_svg(dot_text):\n    return ' + repr('<svg>fixture</svg>\n')))
        old_dot = (root / 'docs/architecture-topology.dot').read_text()
        result = self.command(root, 'architecture')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, {p: (root / p).read_bytes() for p in before})
        dot = (root / 'docs/architecture-topology.dot').read_text()
        self.assertNotEqual(old_dot, dot)
        self.assertIn('51 milliseconds', dot)
        self.assertIn('51 milliseconds', (root / 'docs/ARCHITECTURE.md').read_text())
        self.assertTrue(gen.svg_stamp_matches((root / 'docs/architecture-topology.svg').read_text(), 'topology', dot))
        self.assertEqual(self.command(root, 'limits').returncode, 0)
        self.assertIn('| 51 milliseconds |', (root / 'docs/LIMITS.md').read_text())
        # A renderer returning unresolved placeholders must be visible in dot output.
        broken = gen.render_dot.__globals__['resolve_graph']
        try:
            gen.render_dot.__globals__['resolve_graph'] = lambda graph, limits: graph
            architecture = json.loads((root / 'docs/architecture.json').read_text())
            self.assertIn('{limit:', gen.render_dot(architecture['graphs'][0],
                architecture['styles'], 'ARCHITECTURE.md', rows))
        finally:
            gen.render_dot.__globals__['resolve_graph'] = broken

    def test_spans_are_authored_outside_regions_and_copied_as_bytes(self):
        common = module('span_checks', ROOT / 'docs/generator_common.py')
        for name, filename, span in [
            ('architecture', 'docs/ARCHITECTURE.md', 'architecture.graphs'),
            ('limits', 'docs/LIMITS.md', 'limits.step_id.value'),
        ]:
            root = self.checkout()
            path = root / filename
            original = path.read_text()
            opening = f'<!-- span {span} -->'
            a = original.index(opening) + len(opening)
            b = original.index('<!-- /span -->', a)
            path.write_text(original[:a] + '99999' + original[b:])
            before = self.snapshot(root)
            result = self.command(root, name, '--check')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('stale span ' + span, result.stderr)
            self.assertEqual(self.snapshot(root), before)
            result = self.command(root, name)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(path.read_text(), original)
            before = self.snapshot(root)
            times = {p: (root / p).stat().st_mtime_ns for p in before}
            self.assertEqual(self.command(root, name).returncode, 0)
            self.assertEqual(self.snapshot(root), before)
            self.assertEqual(times, {p: (root / p).stat().st_mtime_ns for p in before})
            path.write_text(original.replace(opening, f'<!-- span {name}.no_such_count -->'))
            before = self.snapshot(root)
            for args in [('--check',), ()]:
                result = self.command(root, name, *args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('unknown span ' + name + '.no_such_count', result.stderr)
                self.assertEqual(self.snapshot(root), before)
        root = self.checkout()
        source = root / 'docs/LIMITS.md'
        source.write_text(source.read_text().replace('<!-- BEGIN SHARED LIMITS -->',
            '<!-- BEGIN SHARED LIMITS -->\n<!-- span limits.host_exit_delay.value_unit -->stale<!-- /span -->'))
        result = self.command(root, 'limits')
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = '<!-- span limits.host_exit_delay.value_unit -->50 milliseconds<!-- /span -->'
        self.assertIn(expected, source.read_text())
        guide = root / 'docs/PolicyWitness.md'
        self.assertIn(expected, guide.read_text())
        guide.write_text(guide.read_text().replace(expected, expected.replace('50 milliseconds', 'wrong')))
        before = self.snapshot(root)
        result = self.command(root, 'limits', '--check')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('stale PolicyWitness.md', result.stderr)
        self.assertEqual(self.snapshot(root), before)
        # Authored passes do not interpret or touch copied/generated bytes.
        text = '<!-- BEGIN GENERATED CONTROL --><!-- span limits.unknown -->x<!-- /span --><!-- END GENERATED CONTROL -->'
        self.assertEqual(common.render_spans(text, 'limits', {}), text)
        source.write_text(source.read_text().replace('<!-- BEGIN GENERATED LIMITS -->',
            '<!-- BEGIN GENERATED LIMITS -->\n<!-- span limits.host_exit_delay.value -->50<!-- /span -->'))
        result = self.command(root, 'limits', '--check')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('stale LIMITS.md', result.stderr)
        self.assertEqual(self.command(root, 'limits').returncode, 0)
        self.assertNotIn('<!-- span limits.host_exit_delay.value -->', source.read_text())

    def test_every_span_prefix_has_one_registered_owner(self):
        common = module('prefix_checks', ROOT / 'docs/generator_common.py')
        owners = {}
        for name in ('limits', 'architecture'):
            gen = module('prefix_' + name, ROOT / f'docs/generate_{name}.py')
            self.assertNotIn(name, owners)
            owners[name] = set(gen.SPAN_DOCUMENTS)
        for path in (ROOT / 'docs').glob('*.md'):
            # Fenced teaching examples are not authored spans.
            text = '\n'.join(module('prose', ROOT / 'docs/generate_limits.py').prose_lines(path.read_text()))
            text = re.sub(r"`+[^`]*`+", "", text)
            for match in common.authored_spans(text):
                prefix = match[1].split('.', 1)[0]
                self.assertIn(prefix, owners)
                self.assertIn(path.relative_to(ROOT).as_posix(), owners[prefix])


if __name__ == '__main__':
    unittest.main()
