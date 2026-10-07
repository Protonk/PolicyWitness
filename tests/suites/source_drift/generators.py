"""Uniform generator contracts, measurements and adversarial controls."""
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
            if any(match[1].startswith(name + '.') for match in common.authored_spans((root / document).read_text())):
                regions.setdefault(document, []).append(SPAN_MARKER)
    return regions, whole


# Every authored span's value, whatever its name, is owned inline; the markers stay.
SPAN_MARKER = ('<!-- span ', '<!-- /span -->')


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
        if (start, end) == SPAN_MARKER:
            text = re.sub(r'(<!-- span [^>]+ -->)(.*?)(<!-- /span -->)', r'\1\3', text, flags=re.S)
            continue
        if text.count(start) != 1 or text.count(end) != 1 or end not in text[text.index(start):]:
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


def scanned_documents(root=ROOT):
    """Historical routing/docs scan plus every Markdown generator target."""
    paths = set((root / 'docs').glob('*.md'))
    paths.update(root / name for name in ['README.md', 'AGENTS.md', 'runner/AGENTS.md', 'tests/README.md'])
    for name in GENERATORS:
        regions, _ = region_ownership(root, name)
        paths.update(root / name for name in regions if name.endswith('.md'))
    return sorted(paths)


def prose_text(text):
    gen = module('prose_limits', ROOT / 'docs/generate_limits.py')
    return '\n'.join(gen.prose_lines(text))


def broken_links(paths):
    """Check local files, heading anchors and backticked-symbol link labels (G11)."""
    from urllib.parse import unquote
    common = module('link_common', ROOT / 'docs/generator_common.py')
    broken = []
    for path in paths:
        prose = prose_text(path.read_text())
        # Keep a backticked link label; ignore other inline code examples.
        def code(match):
            if prose[max(0, match.start() - 1):match.start()] == '[' and prose[match.end():match.end()+2] == '](':
                return match[0]
            return ' ' * len(match[0])
        prose = re.sub(r'(`+)([^`]*?)\1', code, prose)
        if re.search(r'\]\s*\[|^\s*\[[^]\n]+\]:', prose, re.M):
            broken.append(f'{path}: reference-style link is not verified; use inline links')
        for match in re.finditer(r'\[([^]\n]+)\]\(([^\s)]+)\)', prose):
            label, target = match[1], match[2]
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                continue
            filename, separator, anchor = target.partition('#')
            destination = path.parent / unquote(filename) if filename else path
            if not destination.exists():
                broken.append(f'{path}: missing file {target}')
                continue
            if separator:
                if not destination.is_file() or unquote(anchor) not in common.heading_anchors(prose_text(destination.read_text())):
                    broken.append(f'{path}: missing heading {target}')
            # A backticked label is a symbol the target must hold: a code file holds it as
            # text, and a Markdown document holds it as the id or term the link names.
            if re.fullmatch(r'`[^`]+`', label):
                if not destination.is_file() or label[1:-1] not in destination.read_text(errors='replace'):
                    broken.append(f'{path}: missing symbol {label} in {target}')
    return broken

BASELINE_NAME = 'tests/fixtures/docs/prose_baseline.json'


def authored_prose(text):
    common = module('baseline_common', ROOT / 'docs/generator_common.py')
    text = prose_text(text)
    ranges = common.region_ranges(text)
    ranges += [(m.start(), m.end()) for m in common.SPAN_RE.finditer(text)]
    keep = [True] * len(text)
    for a, b in ranges:
        keep[a:b] = [False] * (b - a)
    text = ''.join(c if keep[i] else ('\n' if c == '\n' else ' ') for i, c in enumerate(text))
    return prose_text(text)


def prose_sites(root=ROOT):
    """Exact prose sites: one entry per line holding a literal, one per unread citation link."""
    common = module('measurement_common', ROOT / 'docs/generator_common.py')
    pattern = re.compile(common.DURATION_SIZE_RE.pattern + r'|\b\d[\d,]*-steps?\b', re.I)
    identifier = re.compile(r'[A-Za-z_][A-Za-z0-9_.:]*(?:\(\))?')
    boundary = re.compile(r'[.!?](?:\s|$)|\n\s*\n|\||\]\([^\s)]+\)')
    entries = []
    for path in scanned_documents(root):
        text = authored_prose(path.read_text())
        document = path.relative_to(root).as_posix()
        lines = set()
        for match in pattern.finditer(text):
            a, b = text.rfind('\n', 0, match.start()) + 1, text.find('\n', match.end())
            lines.add((a, b if b >= 0 else len(text)))
        for a, b in sorted(lines):
            entries.append(dict(document=document, invariant='G9', kind='literal', text=text[a:b]))
        # A citation pair is a backticked identifier that the linked file holds, in the same
        # sentence or table cell as a link whose label is not already a symbol.
        for link in re.finditer(r'\[([^]\n]+)\]\(([^\s)]+)\)', text):
            label, target = link[1], link[2].split('#', 1)[0]
            if re.fullmatch(r'`[^`]+`', label) or not target or re.match(r'^[\w+.-]+:', target):
                continue
            if Path(target).suffix.lower() == '.md' or not (path.parent / target).is_file():
                continue
            cited = (path.parent / target).read_text(errors='replace')
            start = max(0, link.start() - 240)
            window = text[start:link.start()]
            edges = list(boundary.finditer(window))
            if edges:
                start += edges[-1].end()
                window = text[start:link.start()]
            tokens = [token for token in re.finditer(r'`([^`\n]+)`', window)
                      if identifier.fullmatch(token[1]) and len(token[1]) >= 3 and token[1] in cited]
            if tokens:
                entries.append(dict(document=document, invariant='G11', kind='citation_pair',
                                    text=text[start + tokens[0].start():link.end()]))
    return sorted(entries, key=lambda row: (row['document'], row['kind'], row['text']))


def baseline_problems(root=ROOT, entries=None):
    from collections import Counter
    release = module('baseline_schema', ROOT / 'tests/lib/release_preflight.py')
    if entries is None:
        entries = json.loads((root / BASELINE_NAME).read_text())['entries']
    release.baseline_entries(json.dumps(dict(schema_version=1, entries=entries)))
    key = lambda row: tuple(row[k] for k in ('document', 'invariant', 'kind', 'text'))
    found = Counter(key(row) for row in prose_sites(root))
    listed = Counter(key(row) for row in entries if row['kind'] != 'count')
    problems = [f'unlisted prose site: {row}' for row in (found - listed).elements()]
    problems += [f'baseline site no longer occurs: {row}' for row in (listed - found).elements()]
    scanned = {path.relative_to(root).as_posix() for path in scanned_documents(root)}
    for row in entries:
        if row['kind'] == 'count':
            path = root / row['document']
            if row['document'] not in scanned or row['text'] not in authored_prose(path.read_text()):
                problems.append(f'baseline count no longer occurs: {row}')
    return problems


def measurements(root=ROOT):
    """Current manifest and prose coverage counts, without treating citations as proof."""
    from collections import Counter
    architecture = json.loads((root / 'docs/architecture.json').read_text())
    limits = json.loads((root / 'docs/limits.json').read_text())['limits']
    items = [i for g in architecture['graphs'] for i in g['nodes'] + g['edges']]
    checks = [r for i in items for r in i['checks']]
    entries = json.loads((root / BASELINE_NAME).read_text())['entries'] if (root / BASELINE_NAME).exists() else []
    return dict(graphs=len(architecture['graphs']), nodes=sum(len(g['nodes']) for g in architecture['graphs']),
                edges=sum(len(g['edges']) for g in architecture['graphs']),
                architecture_citations=sum(len(i['sources']) + len(i['checks']) for i in items),
                architecture_checks=len(checks), architecture_forms=dict(Counter(r.get('form', 'missing') for r in checks)),
                limits=len(limits), limit_checks=sum(len(i['checks']) for i in limits),
                limit_kinds=dict(Counter(r['kind'] for i in limits for r in i['checks'])),
                baseline=dict({'G9': 0, 'G11': 0}, **Counter(row['invariant'] for row in entries)))


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
        for path in scanned_documents():
            # Fenced teaching examples are not authored spans.
            text = '\n'.join(module('prose', ROOT / 'docs/generate_limits.py').prose_lines(path.read_text()))
            text = re.sub(r"`+[^`]*`+", "", text)
            for match in common.authored_spans(text):
                prefix = match[1].split('.', 1)[0]
                self.assertIn(prefix, owners)
                self.assertIn(path.relative_to(ROOT).as_posix(), owners[prefix])

    def test_prose_links_resolve_anchors_and_symbol_links(self):
        self.assertEqual(broken_links(scanned_documents()), [])
        directory = tempfile.TemporaryDirectory(prefix='pw-prose-links-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / 'source.py').write_text('def defined():\n    pass\n')
        (root / 'target.md').write_text('# Target\n## Repeated\n## Repeated\n')
        path = root / 'doc.md'
        (root / 'target.md').write_text('# Target\n## Repeated\n## Repeated\nA row names (`step_id`).\n')
        path.write_text('[target](target.md#repeated-1) [`defined`](source.py) [file](source.py) [`step_id`](target.md#target)')
        self.assertEqual(broken_links([path]), [])
        for content, expected in [
            ('[target](target.md#absent)', 'missing heading'),
            ('[`absent`](source.py)', 'missing symbol'),
            ('[`absent`](target.md)', 'missing symbol'),
            ('[target][reference]\n\n[reference]: target.md', 'reference-style'),
            ('[target](absent.md)', 'missing file'),
            ('# Here\n[here](#absent)', 'missing heading'),
        ]:
            path.write_text(content)
            self.assertIn(expected, '\n'.join(broken_links([path])))

    def test_prose_baseline_is_consistent_and_growth_is_explicit(self):
        self.assertEqual(baseline_problems(), [])
        root = self.checkout()
        baseline = json.loads((root / BASELINE_NAME).read_text())['entries']
        path = root / 'docs/ARCHITECTURE.md'
        for prose, kind in [('A new delay lasts 7 seconds.', 'literal'),
                            ('The `load_manifest` ([generate_architecture.py](generate_architecture.py)) routine.', 'citation_pair')]:
            original = path.read_text()
            path.write_text(original + '\n' + prose + '\n')
            self.assertTrue(baseline_problems(root, baseline))
            added = prose_sites(root)
            for row in prose_sites():
                added.remove(row)
            self.assertEqual(len(added), 1)
            self.assertEqual(added[0]['kind'], kind)
            self.assertEqual(baseline_problems(root, baseline + added), [])
            path.write_text(original)
        # The corrected scan: UTF-8 counts are not durations, one line is one site, and a
        # backticked token the linked file does not hold is not a citation.
        original = path.read_text()
        path.write_text(original + '\nIt counts UTF-8 bytes, two 7 ms waits and 9 ms more.\n'
                        + 'The `no_such_symbol_q7` ([generate_architecture.py](generate_architecture.py)) case.\n')
        added = prose_sites(root)
        for row in prose_sites():
            added.remove(row)
        self.assertEqual([(row['kind'], row['text']) for row in added],
                         [('literal', 'It counts UTF-8 bytes, two 7 ms waits and 9 ms more.')])
        path.write_text(original)
        missing = dict(document='docs/ARCHITECTURE.md', invariant='G9', kind='literal', text='A vanished delay lasts 7 seconds.')
        self.assertTrue(baseline_problems(root, baseline + [missing]))
        counts = measurements(root)['baseline']
        self.assertEqual(set(counts), {'G9', 'G11'})
        print('prose baseline coverage:', json.dumps(counts, sort_keys=True))

    def test_release_preflight_refuses_a_grown_baseline(self):
        from contextlib import redirect_stderr, redirect_stdout
        import io
        from unittest.mock import patch
        release = module('preflight_baseline', ROOT / 'tests/lib/release_preflight.py')
        entry = dict(document='docs/example.md', invariant='G9', kind='literal', text='7 seconds')
        rewritten = dict(entry, text='8 seconds')
        for label, previous, candidate, refused in [
            ('equal', [entry], [entry], False),
            ('subset', [entry], [], False),
            ('superset', [entry], [entry, rewritten], True),
            ('rewritten', [entry], [rewritten], True),
            ('predates', None, [entry], False),
            ('version_reset', [entry], [entry], False),
        ]:
            with self.subTest(case=label):
                directory = tempfile.TemporaryDirectory(prefix='pw-baseline-release-')
                self.addCleanup(directory.cleanup)
                root = Path(directory.name)
                def git(*args):
                    result = subprocess.run(['git', '-C', str(root), '-c', 'user.name=Generator Control',
                        '-c', 'user.email=generator@example.invalid', '-c', 'commit.gpgsign=false',
                        '-c', 'tag.gpgsign=false', *args], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    return result.stdout
                def commit(rows, tag):
                    path = root / BASELINE_NAME
                    if rows is not None:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(json.dumps(dict(schema_version=1, entries=rows)))
                    (root / 'version').write_text(tag)
                    git('add', '.')
                    git('commit', '-qm', tag)
                    git('tag', '-a', tag, '-m', tag)
                git('init', '-q')
                previous_tag, candidate_tag = 'v1.0.0', 'v1.1.0'
                if label == 'version_reset':
                    commit([entry, rewritten], 'v9.0.0')
                    previous_tag, candidate_tag = 'v2.3.0', 'v0.2.3'
                commit(previous, previous_tag)
                commit(candidate, candidate_tag)
                stamp, problems = release.inspect(root, remote=str(root))
                self.assertEqual(bool(problems), refused, problems)
                self.assertEqual(stamp['prose_baseline']['previous_tag'], previous_tag)
                if previous is None:
                    self.assertEqual(stamp['prose_baseline']['status'], 'previous release predates baseline')
                if refused:
                    self.assertIn('baseline grew', problems[0])
                    with patch.object(release, 'ROOT', root), redirect_stderr(io.StringIO()) as err, redirect_stdout(io.StringIO()):
                        self.assertEqual(release.main(['--remote', str(root)]), 1)
                        self.assertEqual(release.main(['--remote', str(root), '--report']), 0)
                    self.assertIn('WARNING: prose baseline grew', err.getvalue())

    def test_whole_file_staging_is_owned_and_idempotent(self):
        root = self.checkout()
        destination = root / 'staged-guide.md'
        before = self.snapshot(root)
        result = self.command(root, 'limits', '--stage-guide', str(destination))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(destination.read_bytes(), (root / 'docs/PolicyWitness.md').read_bytes())
        self.assertEqual(changed_outside(before, self.snapshot(root), {}, {'staged-guide.md'}), [])
        timestamp = destination.stat().st_mtime_ns
        self.assertEqual(self.command(root, 'limits', '--stage-guide', str(destination)).returncode, 0)
        self.assertEqual(destination.stat().st_mtime_ns, timestamp)

    def test_architecture_render_failure_leaves_every_copy_untouched(self):
        root = self.checkout()
        path = root / 'docs/architecture.json'
        data = json.loads(path.read_text())
        data['graphs'][0]['nodes'][0]['label'] += ' changed'
        path.write_text(json.dumps(data))
        script = root / 'docs/generate_architecture.py'
        script.write_text(script.read_text().replace('def render_svg(dot_text):',
            'def render_svg(dot_text):\n    raise RuntimeError("controlled render refusal")'))
        before = self.snapshot(root)
        result = self.command(root, 'architecture')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('controlled render refusal', result.stderr)
        self.assertEqual(self.snapshot(root), before)

    def test_readme_form_table_is_a_copy_of_the_shared_rules(self):
        common = module('form_rules', ROOT / 'docs/generator_common.py')
        readme = (ROOT / 'tests/suites/source_drift/README.md').read_text()
        self.assertIn('\n'.join(common.form_table()), readme)
        for form, _, _ in common.FORM_RULES:
            self.assertEqual(readme.count(f'\n| `{form}` |'), 1, form)
            self.assertTrue(common.allowed_file(form, 'tests/suites/source_drift/check.py') in (True, False))
        with self.assertRaises(ValueError):
            common.allowed_file('maybe', 'tests/suites/source_drift/check.py')

    def test_document_graph_cites_every_drift_rule(self):
        import ast
        tree = ast.parse((ROOT / 'tests/suites/source_drift/check.py').read_text())
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        rules = {n.func.id for n in ast.walk(main)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id.startswith('check_')}
        self.assertTrue(rules)
        data = json.loads((ROOT / 'docs/architecture.json').read_text())
        graph = next(g for g in data['graphs'] if g['id'] == 'documents')
        node = next(n for n in graph['nodes'] if n['id'] == 'drift_check')
        cited = {r['symbol'] for r in node['checks']
                 if r['form'] == 'rule' and r['path'] == 'tests/suites/source_drift/check.py'}
        self.assertEqual(cited, rules)

    def test_ownership_is_unique_and_unknown_prefixes_are_rejected(self):
        owners, whole_files = {}, {}
        common = module('ownership_checks', ROOT / 'docs/generator_common.py')
        for name in GENERATORS:
            regions, whole = ownership(ROOT, name)
            for path in whole:
                self.assertNotIn(path, whole_files)
                whole_files[path] = name
            for path, markers in regions.items():
                text = (ROOT / path).read_text()
                for start, end in markers:
                    if (start, end) == SPAN_MARKER:
                        continue  # inline, and authored_spans admits none inside a region
                    a = text.index(start)
                    b = text.index(end, a) + len(end)
                    for owner, left, right in owners.get(path, []):
                        self.assertFalse(max(a, left) < min(b, right), (path, owner, name))
                    owners.setdefault(path, []).append((name, a, b))
        self.assertFalse(set(owners) & set(whole_files))
        authored = common.authored_spans('<!-- span unknown.value -->1<!-- /span -->')
        self.assertTrue(any(m[1].split('.', 1)[0] not in {'architecture', 'limits'} for m in authored))



if __name__ == '__main__':
    unittest.main()
