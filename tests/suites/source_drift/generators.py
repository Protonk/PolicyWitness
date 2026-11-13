"""Uniform generator contracts, measurements and adversarial controls."""
import importlib.util
import io
import json
import re
import subprocess
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
import contract_fixture  # noqa: E402
import markdown_reader  # noqa: E402
import repository_tree  # noqa: E402
GENERATORS = fixture_inputs.GENERATORS
# Files no generator owns, placed in every fixture so a write outside owned regions is visible in a snapshot.
SENTINELS = {'SENTINEL.md': '# Sentinel\n\nNo generator owns this file.\n', 'sentinel/notes.txt': 'unrelated\n'}


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
    if name in {'limits', 'architecture', 'build', 'footprint'}:
        gen = module('span_owner_' + name, root / f'docs/generate_{name}.py')
        common = module('span_common', root / 'docs/generator_common.py')
        documents = gen.span_documents(root) if hasattr(gen, 'span_documents') else gen.SPAN_DOCUMENTS
        for document in documents:
            if any(match[1].startswith(name + '.') for match in common.authored_spans((root / document).read_text(), document)):
                regions.setdefault(document, []).append(SPAN_MARKER)
    return regions, whole


# Every authored span's value, whatever its name, is owned inline; the markers stay.
SPAN_MARKER = ('<!-- span ', '<!-- /span -->')


def region_ownership(root, name):
    """Explicit regions and whole-file outputs; never infer ownership from a diff."""
    gen = module('owner_' + name, root / f'docs/generate_{name}.py')
    if name == 'porcelain':
        return gen.ownership(root)
    if name == 'contract_stamps':
        runtime = gen.contract_module('runtime')
        return {'docs/PolicyWitness.md': [(gen.BEGIN, gen.END)]}, {
            'docs/CONTRACT.md', runtime.history_v1.SNAPSHOT, runtime.BASELINE,
            *runtime.collected_shapes(root)}
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
                    (gen.GUIDE_RULES_START, gen.GUIDE_RULES_END),
                    (gen.GUIDE_SCENARIOS_START, gen.GUIDE_SCENARIOS_END),
                    (gen.GUIDE_EXTENSION_START, gen.GUIDE_EXTENSION_END),
                    (gen.GUIDE_COVERAGE_START, gen.GUIDE_COVERAGE_END)]}, set()
    data = json.loads((root / gen.MANIFEST_NAME).read_text())
    if name == 'footprint':
        return {data['document']: [(f'<!-- BEGIN GENERATED FOOTPRINT {region} -->',
                                    f'<!-- END GENERATED FOOTPRINT {region} -->')
                                   for region in ('WAITING', 'RESPONSE', 'AFTERMATH', 'BACKING', 'ENDINGS', 'COVERAGE')]}, set()
    if name == 'build':
        return {data['document']: [(gen.REGION_START.format(region=r), gen.REGION_END.format(region=r)) for r in gen.REGIONS]}, {
            str(Path(data['document']).parent / (data['figure'] + suffix)) for suffix in ('.dot', '.svg')}
    regions, whole = {}, set()
    for graph in data['graphs']:
        document = gen.graph_document(data, graph)
        regions.setdefault(document, []).append((gen.REGION_START.format(graph=graph['id']),
                                                 gen.REGION_END.format(graph=graph['id'])))
        whole.update(str(Path(document).parent / (graph['file'] + suffix)) for suffix in ('.dot', '.svg'))
    return regions, whole



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
    paths.update(root / name for name in repository_tree.Tree(root).inventory(repository_tree.CONTRACT_SURFACES))
    paths.update(root / name for name in ['README.md', 'AGENTS.md', 'controller/AGENTS.md', 'runner/AGENTS.md', 'tests/README.md', 'tests/AGENTS.md'])
    for name in GENERATORS:
        if name == 'contract_stamps':
            # Prose discovery must still observe a newly authored or malformed
            # surface before the contract model can collect its output shapes.
            paths.update(root / path for path in ('docs/CONTRACT.md', 'docs/PolicyWitness.md'))
            continue
        regions, _ = region_ownership(root, name)
        paths.update(root / name for name in regions if name.endswith('.md'))
    return sorted(paths)


def public_link_documents(path):
    """Markdown links plus public free.* values carried inside contract fences."""
    text = path.read_text()
    common = module('link_common', ROOT / 'docs/generator_common.py')
    return [markdown_reader.parse(text, str(path)),
            *(markdown_reader.parse(value, f'{path}:{line + 1}')
              for line, value in common.contract_public_prose(text, str(path)).items())]


def prose_inputs(root=ROOT):
    """The prose scope and the local files its links name, as relative paths: a fixture for the link rule
    needs the destinations, not only the documents."""
    root = Path(root)
    found = set()
    for path in scanned_documents(root):
        found.add(path.relative_to(root).as_posix())
        for link in (link for document in public_link_documents(path) for link in document.links):
            target = link.target.split('#')[0]
            if target and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                destination = (path.parent / target).resolve()
                if destination.is_relative_to(root.resolve()):
                    found.add(destination.relative_to(root.resolve()).as_posix())
    return sorted(found)


def broken_links(paths):
    """Check local files, heading anchors and backticked-symbol link labels (G11)."""
    broken = []
    for path in paths:
        documents = public_link_documents(path)
        if any(document.references for document in documents):
            broken.append(f'{path}: reference-style link is not verified; use inline links')
        for link in (link for document in documents for link in document.links):
            target = link.target
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                continue
            filename, separator, anchor = target.partition('#')
            destination = path.parent / filename if filename else path
            if not destination.exists():
                broken.append(f'{path}: missing file {target}')
                continue
            if separator:
                if not destination.is_file() or anchor not in markdown_reader.read(destination).anchors:
                    broken.append(f'{path}: missing heading {target}')
            # A backticked label is a symbol the target must hold: a code file holds it as
            # text, and a Markdown document holds it as the id or term the link names.
            if link.code_label is not None:
                if not destination.is_file() or link.code_label not in destination.read_text(errors='replace'):
                    broken.append(f'{path}: missing symbol `{link.code_label}` in {target}')
    return broken

BASELINE_NAME = 'tests/fixtures/docs/prose_baseline.json'


def authored_prose(text, name='<text>'):
    """Lines of prose blocks with generated and copied regions and span values blanked; other lines are empty."""
    common = module('baseline_common', ROOT / 'docs/generator_common.py')
    hidden = common.authoring_excluded_ranges(text, name) + [(m.start(), m.end()) for m in common.SPAN_RE.finditer(text)]
    keep = [True] * len(text)
    for a, b in hidden:
        keep[a:b] = [False] * (b - a)
    blanked = ''.join(c if keep[i] else ('\n' if c == '\n' else ' ') for i, c in enumerate(text))
    prose = set(markdown_reader.parse(text, name).prose_lines) | set(common.contract_public_prose(text, name))
    return '\n'.join(line if i in prose else '' for i, line in enumerate(blanked.split('\n')))


def citation_pairs(path, text):
    """Backticked identifiers the linked code file holds, before the link in the same sentence or table cell."""
    common = module('pair_common', ROOT / 'docs/generator_common.py')
    identifier = re.compile(r'[A-Za-z_][A-Za-z0-9_.:]*(?:\(\))?')
    document = markdown_reader.parse(text, str(path))
    regions = common.authoring_excluded_ranges(text, str(path))
    pairs = []
    for inline in document.inlines:
        if any(a <= document.offset(inline.lines[0]) < b for a, b in regions):
            continue
        # Each window holds the code spans since the last boundary, with their rendered offsets.
        window, offset, span, ended = [], 0, False, False
        for kind, value in inline.pieces:
            if kind == 'html':
                # A comment is invisible: a sentence end before it still ends the sentence.
                span = bool(re.match(r'<!--\s*span\b', value)) or (span and not re.match(r'<!--\s*/span\b', value))
                continue
            if span:
                continue
            if kind == 'text':
                cut = max((m.end() for m in re.finditer(r'[.!?](?=\s)|\|', value)), default=None)
                if cut is not None or (ended and value[:1].isspace()):
                    window = []
                ended = bool(re.search(r'[.!?]$', value))
                offset += len(value)
                continue
            if kind == 'code':
                window.append((value, offset))
                offset += len(value) + 2
                ended = False
                continue
            # A link or image ends the window; only a link to a code file can pair.
            link, near = value, [code for code, start in window if offset - start <= 240] if not ended else []
            window, ended = [], False
            offset += len(link.label) + 4
            target = link.target.split('#', 1)[0]
            if (kind == 'image' or link.code_label is not None or not target or re.match(r'^[\w+.-]+:', target)
                    or Path(target).suffix.lower() == '.md' or not (path.parent / target).is_file()):
                continue
            cited = (path.parent / target).read_text(errors='replace')
            held = [code for code in near if identifier.fullmatch(code) and len(code) >= 3 and code in cited]
            if held:
                pairs.append(f'`{held[0]}` … [{link.label}]({link.target})')
    # free.* facts are authored public Markdown, even though their carrier is
    # a contract fence. Parsing each raw value keeps its relative link base.
    for value in common.contract_public_prose(text, str(path)).values():
        pairs.extend(citation_pairs(path, value))
    return pairs


def span_marker_problems(path, text, owners):
    """Span markers in a scanned document: inline in prose, opened and closed in turn, each with a registered owner."""
    common = module('marker_common', ROOT / 'docs/generator_common.py')
    regions = common.authoring_excluded_ranges(text, str(path))
    document = markdown_reader.parse(text, str(path))
    name = path.relative_to(ROOT).as_posix()

    def authored(lines):
        return not any(a <= document.offset(lines[0]) < b for a, b in regions)
    problems = []
    # A marker that begins a line is an HTML block, which GitHub shows as raw HTML.
    for block in document.blocks:
        if block.kind == 'html' and authored(block.lines) and re.search(r'<!--\s*/?span\b', block.content):
            problems.append(f'{name}:{block.lines[0] + 1}: span marker in an HTML block')
    for inline in document.inlines:
        if not authored(inline.lines):
            continue
        markers = [value for kind, value in inline.pieces if kind == 'html' and re.match(r'<!--\s*/?span\b', value)]
        if [marker.startswith('<!-- span ') for marker in markers] != [True, False] * (len(markers) // 2):
            problems.append(f'{name}:{inline.lines[0] + 1}: span markers do not open and close in turn')
            continue
        for marker in markers[::2]:
            span = re.match(r'<!-- span ([a-z][a-z0-9_]*)\.', marker)
            if not span or name not in owners.get(span[1], ()):
                problems.append(f'{name}:{inline.lines[0] + 1}: {marker} has no registered owner')
    for line, value in common.contract_public_prose(text, str(path)).items():
        problems.extend(problem.replace(f'{name}:1:', f'{name}:{line + 1}:', 1)
                        for problem in span_marker_problems(path, value, owners))
    return problems


def prose_sites(root=ROOT):
    """Exact prose sites: one entry per line holding a literal, one per unread citation link."""
    common = module('measurement_common', ROOT / 'docs/generator_common.py')
    pattern = re.compile(common.DURATION_SIZE_RE.pattern + r'|\b\d[\d,]*-steps?\b', re.I)
    entries = []
    for path in scanned_documents(root):
        source = path.read_text()
        text = authored_prose(source, str(path))
        document = path.relative_to(root).as_posix()
        lines = set()
        for match in pattern.finditer(text):
            a, b = text.rfind('\n', 0, match.start()) + 1, text.find('\n', match.end())
            lines.add((a, b if b >= 0 else len(text)))
        for a, b in sorted(lines):
            entries.append(dict(document=document, invariant='G9', kind='literal', text=text[a:b]))
        for pair in citation_pairs(path, source):
            entries.append(dict(document=document, invariant='G11', kind='citation_pair', text=pair))
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
            if row['document'] not in scanned or row['text'] not in authored_prose(path.read_text(), row['document']):
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


class GeneratorContractTests(receipts.TestCase):
    def checkout(self, generators=GENERATORS):
        """The declared inputs of the named generators, never build products or accumulated evidence, plus
        sentinel files no generator owns; the fixture is not a Git repository."""
        directory = tempfile.TemporaryDirectory(prefix='pw-generators-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        paths = set()
        for name in generators:
            paths.update(fixture_inputs.generator_inputs(ROOT, name))
        copied = fixture_inputs.copy_declared(ROOT, root, paths)
        for name, text in SENTINELS.items():
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_text(text)
        print(f'fixture: {copied.files} files, {copied.bytes} bytes, {copied.seconds:.3f} s')
        self.track_inputs(root)
        return root

    def command(self, root, name, *args):
        if root == ROOT:
            self.track_inputs(root, fixture_inputs.generator_inputs(root, name))
        start = time.perf_counter()
        result = self.run_command([sys.executable, '-B', '-S', str(root / f'docs/generate_{name}.py'), *args],
                                cwd=root, capture_output=True, text=True, timeout=60)
        print(f'command: generate_{name} {" ".join(args)} rc={result.returncode} {time.perf_counter() - start:.3f} s')
        return result

    def snapshot(self, root):
        start = time.perf_counter()
        taken = fixture_inputs.snapshot(root)
        print(f'snapshot: {len(taken)} files, {sum(map(len, taken.values()))} bytes, {time.perf_counter() - start:.3f} s')
        return taken

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
                if name == 'contract_stamps':
                    contract_fixture.fresh_authoring(root, module('fresh_contract', root / 'docs/generate_contract_stamps.py'))
                regions, whole = ownership(root, name)
                if name == 'worker_identity':
                    path = root / 'controller/tools/pw_probe_runner/pw_probe_runner.c'
                    path.write_text(path.read_text() + '\n/* identity property control */\n')
                elif name == 'contract_stamps':
                    gen = module('mutation_contract', root / 'docs/generate_contract_stamps.py')
                    tree = gen.contract_module('tree').load_tree(root)
                    node = next(node for node in tree.nodes if node.kind == 'definition' and node.prose)
                    path = root / node.source
                    original = path.read_text()
                    self.assertEqual(original.count(node.prose), 1)
                    changed = original.replace(node.prose, node.prose + '\n\nAuthored property control.', 1)
                    self.assertNotEqual(original, changed)
                    path.write_text(changed)
                else:
                    path = root / f'docs/{name}.json'
                    data = json.loads(path.read_text())
                    if name == 'limits':
                        data['limits'][0]['value'] += 1
                    elif name == 'footprint':
                        data['rows'][0]['title'] += ' property control'
                    elif name == 'porcelain':
                        data['records'][0]['fields'][0]['name'] += 'PropertyControl'
                    elif name == 'build':
                        data['steps'][2]['reads'] += ' (property control)'
                    else:
                        data['graphs'][0]['nodes'][0]['label'] += ' property control'
                    path.write_text(json.dumps(data))
                before = self.snapshot(root)
                result = self.command(root, name, *(['--skip-svg'] if name in ('architecture', 'build') else ['--release', 'v9.0.0'] if name == 'contract_stamps' else []))
                self.assertEqual(result.returncode, 0, result.stderr)
                after = self.snapshot(root)
                self.assertNotEqual(before, after)
                self.assertEqual(changed_outside(before, after, regions, whole), [])
                # Repeat the identical command before changing any input or
                # generator. Equal bytes alone would miss an unnecessary rewrite.
                modified = {path: (root / path).stat().st_mtime_ns for path in after}
                repeated = self.command(root, name, *(['--skip-svg'] if name in ('architecture', 'build') else ['--release', 'v9.0.0'] if name == 'contract_stamps' else []))
                self.assertEqual(repeated.returncode, 0, repeated.stderr)
                self.assertEqual(self.snapshot(root), after)
                self.assertEqual({path: (root / path).stat().st_mtime_ns for path in after}, modified)
                # A real command that corrupts bytes past its END marker must fail the property.
                target = next(iter(regions))
                script = root / f'docs/generate_{name}.py'
                original = script.read_text()
                self.assertIn('sys.exit(main())', original)
                script.write_text(original.replace('sys.exit(main())',
                    'code = main()\n    target = ROOT / ' + repr(target) +
                    '\n    target.write_text(target.read_text() + "x")\n    sys.exit(code)'))
                before = self.snapshot(root)
                result = self.command(root, name, *(['--skip-svg'] if name in ('architecture', 'build') else ['--release', 'v9.0.0'] if name == 'contract_stamps' else []))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(changed_outside(before, self.snapshot(root), regions, whole), [target])

    def refuse_manifest(self, name, mutate, expected):
        root = self.checkout()
        path = root / f'docs/{name}.json'
        data = json.loads(path.read_text())
        mutate(data)
        path.write_text(json.dumps(data))
        before = self.snapshot(root)
        for args in [('--check',), ('--skip-svg',) if name in ('architecture', 'build') else ()]:
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
            sources=[dict(path=d['document'], symbol=f"BEGIN GENERATED ARCHITECTURE GRAPH {d['graphs'][0]['id']}")]), 'self-citation')

    def test_captions_state_the_verified_guarantee(self):
        gen = module('architecture_caption', ROOT / 'docs/generate_architecture.py')
        data = gen.load_manifest(ROOT / gen.MANIFEST_NAME)
        def verified(text, worker):
            if worker:
                scope = 'source-symbol presence' in text and 'definitions' in text
            else:
                scope = ('presence' in text and 'definition' in text and
                         'whether a test asserts the row is not verified' in text)
            return scope and not re.search(r'\b(exercises|covers|proves)\b|assertion coverage', text)
        for graph in data['graphs']:
            region = gen.render_region(graph, 'ARCHITECTURE.md')
            caption = next(line for line in region.splitlines() if line.startswith('*Figure:'))
            summary = next(line for line in region.splitlines() if line.startswith('<summary>'))
            worker = graph['id'] == 'worker_capabilities'
            for text in (caption, summary):
                self.assertTrue(verified(text, worker))
                # Each form must state the mechanical boundary. Removing either
                # part of the positive form must fail just as removing the old
                # explicit disclaimer does for the other graphs.
                required = (('source-symbol presence', 'definitions') if worker else
                            ('whether a test asserts the row is not verified',))
                for phrase in required:
                    self.assertFalse(verified(text.replace(phrase, ''), worker))
                for word in ('exercises', 'covers', 'proves', 'assertion coverage verified'):
                    self.assertFalse(verified(text + ' ' + word, worker))

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
                checks = 'Checks and assertion scope' if graph['id'] == 'worker_capabilities' else 'Checks'
                expected = '| ' + ' | '.join(leading + graph[kind + '_facts'] + ['Sources', checks, 'Limits']) + ' |'
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
            ('architecture', 'docs/ARCHITECTURE.md', 'architecture.documents.architecture.graphs'),
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
            '<!-- BEGIN SHARED LIMITS -->\nThe delay is <!-- span limits.host_exit_delay.value_unit -->stale<!-- /span -->'))
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

    def test_footprint_quantities_have_owned_regions_and_spans(self):
        gen = module('footprint_quantities', ROOT / 'docs/generate_footprint.py')
        root = self.checkout()
        path = root / 'docs/FOOTPRINT.md'
        original = path.read_text()
        row = json.loads((root / gen.MANIFEST_NAME).read_text())['rows'][0]['id']
        span = f'footprint.{row}.quantity'
        authored = f'\nQuantity <!-- span {span} -->stale<!-- /span -->.\n'
        path.write_text(original + authored)
        before = self.snapshot(root)
        result = self.command(root, 'footprint', '--check')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.snapshot(root), before)
        regions, whole = ownership(root, 'footprint')
        result = self.command(root, 'footprint')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(changed_outside(before, self.snapshot(root), regions, whole), [])
        rendered = path.read_text()
        self.assertNotIn('stale<!-- /span -->', rendered)
        # Byte/time values inside a footprint region/span do not create baseline
        # entries; the same authored claim outside either owner must do so.
        visible = authored_prose(rendered + '\nUnowned 7654321 bytes.\n', str(path))
        self.assertNotIn('<!-- span', visible)
        self.assertIn('Unowned 7654321 bytes.', visible)
        self.assertNotIn('| ' + row + ' |', visible)
        path.write_text(rendered.replace(f'<!-- span {span} -->', '<!-- span footprint.missing -->'))
        before = self.snapshot(root)
        result = self.command(root, 'footprint', '--check')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('unknown span footprint.missing', result.stderr)
        self.assertEqual(self.snapshot(root), before)

    def test_a_span_marker_that_begins_a_line_is_refused(self):
        # The marker would start an HTML block, which GitHub renders outside its paragraph.
        root = self.checkout()
        path = root / 'docs/LIMITS.md'
        opening = '  of <!-- span limits.step_id.value -->'
        self.assertEqual(path.read_text().count(opening), 1)
        path.write_text(path.read_text().replace(opening, '  of\n  <!-- span limits.step_id.value -->'))
        before = self.snapshot(root)
        for args in [('--check',), ()]:
            result = self.command(root, 'limits', *args)
            self.assertNotEqual(result.returncode, 0)
            self.assertRegex(result.stderr, r'docs/LIMITS\.md:\d+: span marker in an HTML block')
            self.assertEqual(self.snapshot(root), before)

    def test_markdown_citations_name_headings_heading_code_or_markers(self):
        common = module('markdown_citations', ROOT / 'docs/generator_common.py')
        directory = tempfile.TemporaryDirectory(prefix='pw-citations-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.track_inputs(root)
        (root / 'doc.md').write_text(
            '## Real heading\n\n## Test seam: `_seam`\n\n<!-- BEGIN GENERATED THING -->\n<!-- END GENERATED THING -->\n\n'
            '<!--\n## Commented heading\n-->\n\n```text\n## Fenced heading\n<!-- BEGIN GENERATED FENCED -->\n```\n\n'
            'Prose names Prose heading and `BEGIN GENERATED PROSE`.\n\n<!-- note: BEGIN GENERATED QUOTED -->\n')
        for symbol in ('Real heading', '_seam', 'BEGIN GENERATED THING'):
            common.citation({'path': 'doc.md', 'symbol': symbol}, root)
        for symbol in ('Commented heading', 'Fenced heading', 'BEGIN GENERATED FENCED', 'Prose heading',
                       'BEGIN GENERATED PROSE', 'BEGIN GENERATED TH', 'BEGIN GENERATED QUOTED'):
            with self.subTest(symbol=symbol), self.assertRaisesRegex(ValueError, 'missing symbol'):
                common.citation({'path': 'doc.md', 'symbol': symbol}, root)

    def test_every_span_prefix_has_one_registered_owner(self):
        common = module('prefix_checks', ROOT / 'docs/generator_common.py')
        owners = {}
        for name in ('limits', 'architecture', 'build', 'footprint'):
            gen = module('prefix_' + name, ROOT / f'docs/generate_{name}.py')
            self.assertNotIn(name, owners)
            owners[name] = set(gen.span_documents(ROOT) if hasattr(gen, 'span_documents') else gen.SPAN_DOCUMENTS)
        for path in scanned_documents():
            self.assertEqual(span_marker_problems(path, path.read_text(), owners), [])
        document = ROOT / 'docs/ARCHITECTURE.md'
        for text, expected in [('Text\n<!-- span limits.step_id.value -->1<!-- /span -->\n', 'in an HTML block'),
                               ('Waits <!-- span limits.step_id.value -->50 ms.\n', 'open and close in turn'),
                               ('Value <!-- span nobody.value -->1<!-- /span -->\n', 'no registered owner'),
                               ('Value `<!-- span nobody.value -->` in code.\n', None)]:
            problems = span_marker_problems(document, text, owners)
            self.assertEqual(bool(problems), expected is not None, (text, problems))
            if expected:
                self.assertIn(expected, problems[0])

    def test_prose_links_resolve_anchors_and_symbol_links(self):
        self.assertEqual(broken_links(scanned_documents()), [])
        directory = tempfile.TemporaryDirectory(prefix='pw-prose-links-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.track_inputs(root)
        (root / 'source.py').write_text('def defined():\n    pass\n')
        (root / 'target.md').write_text('# Target\n## Repeated\n## Repeated\n')
        path = root / 'doc.md'
        (root / 'target.md').write_text('# Target\n## Repeated\n## Repeated\nA row names (`step_id`).\n\n'
                                      '<a id="contract-stable-node"></a>\n\n'
                                      '```html\n<a id="fenced-target"></a>\n```\n')
        path.write_text('[target](target.md#repeated-1) [`defined`](source.py) [file](source.py) '
                        '[`step_id`](target.md#target) [stable](target.md#contract-stable-node)')
        self.assertEqual(broken_links([path]), [])
        for content, expected in [
            ('[target](target.md#absent)', 'missing heading'),
            ('[example](target.md#fenced-target)', 'missing heading'),
            ('[`absent`](source.py)', 'missing symbol'),
            ('[`absent`](target.md)', 'missing symbol'),
            ('[target][reference]\n\n[reference]: target.md', 'reference-style'),
            ('[target](absent.md)', 'missing file'),
            ('# Here\n[here](#absent)', 'missing heading'),
            ('[wrapped\nlabel](absent.md)', 'missing file'),
            ('[`a]b`](source.py)', 'missing symbol'),
            ('[![badge](missing.png)](target.md#target)', 'missing file missing.png'),
        ]:
            path.write_text(content)
            self.assertIn(expected, '\n'.join(broken_links([path])))
        # Text in a comment or inline code is not a link.
        for content in ('<!-- [target](absent.md) -->', '`[target](absent.md)`', '<!--\n[target](absent.md)\n-->'):
            path.write_text(content)
            self.assertEqual(broken_links([path]), [], content)

    def test_line_level_prose_keeps_lines_and_reads_only_prose(self):
        span = '<!-- span limits.step_id.value -->11 seconds<!-- /span -->'
        text = ('Intro.\n\n```text\nFenced 7 seconds.\n```\n\n<!--\nCommented 8 seconds.\n-->\n\n    Indented 9 seconds.\n\n'
                '<!-- BEGIN GENERATED CONTROL -->\n| Region 10 seconds |\n| --- |\n<!-- END GENERATED CONTROL -->\n\n'
                f'A span {span} and a real 12 seconds.\n')
        prose = authored_prose(text)
        # The blanked text keeps every line where the parser reported it.
        self.assertEqual(len(prose.split('\n')), len(text.split('\n')))
        kept = [(n, line) for n, line in enumerate(prose.split('\n')) if line.strip()]
        self.assertEqual(kept, [(0, 'Intro.'), (17, 'A span ' + ' ' * len(span) + ' and a real 12 seconds.')])

    def test_surface_prose_scope_includes_public_meaning_and_excludes_support(self):
        root = self.checkout()
        fixture_inputs.copy_declared(ROOT, root, prose_inputs(ROOT))
        fixture = root / 'docs/contract/99-scan.surface.md'
        text = ('# Scan {scan: surface}\n\n'
                '```contract\nsyntax: 1\nfree.condition: Public allowance is 709 bytes.\n```\n\n'
                '## Value {value: definition}\n\nPublic capacity is 701 bytes.\n\n'
                '```text\nFenced capacity is 702 bytes.\n```\n\n'
                '### Support {support: owner}\n\nSupport capacity is 703 bytes.\n\n'
                '```contract\nfree.effect: Support allowance is 710 bytes.\n```\n\n'
                'Owner span <!-- span nobody.value -->704 bytes<!-- /span -->.\n\n'
                '## Next {next: definition}\n\nPublic delay is 705 seconds.\n\n'
                '<!-- BEGIN GENERATED CLAIM -->\n\nClaimed generated capacity is 708 bytes.\n\n'
                '<!-- END GENERATED CLAIM -->\n')
        fixture.write_text(text)
        self.assertIn(fixture, scanned_documents(root), 'a new surface without owned spans is authored input')
        prose = authored_prose(text, str(fixture))
        self.assertIn('Public capacity is 701 bytes.', prose)
        self.assertIn('Public delay is 705 seconds.', prose)
        self.assertIn('Public allowance is 709 bytes.', prose)
        self.assertIn('Claimed generated capacity is 708 bytes.', prose,
                      'a generated-marker claim cannot exempt an authored surface')
        for value in ('702 bytes', '703 bytes', '704 bytes', '710 bytes'):
            self.assertNotIn(value, prose)
        # The marker scanner shares the support boundary even for an unknown
        # span prefix. The same marker in public prose remains an error.
        original_path = ROOT / 'docs/contract/99-scan.surface.md'
        self.assertEqual(span_marker_problems(original_path, text, {}), [])
        public_marker = text + '\nValue <!-- span nobody.value -->706 bytes<!-- /span -->.\n'
        self.assertTrue(span_marker_problems(original_path, public_marker, {}))
        free_marker = text.replace('Public allowance is 709 bytes.',
                                   'Public allowance <!-- span nobody.value -->709 bytes<!-- /span -->.')
        self.assertTrue(span_marker_problems(original_path, free_marker, {}))
        (fixture.parent / 'scan.py').write_text('def public_symbol():\n    pass\n\ndef support_symbol():\n    pass\n')
        cited = text.replace('Public allowance is 709 bytes.',
                             'The `public_symbol` ([source](scan.py)) supplies the allowance.').replace(
                             'Support allowance is 710 bytes.',
                             'The `support_symbol` ([source](scan.py)) supplies support.')
        self.assertEqual(citation_pairs(fixture, cited), ['`public_symbol` … [source](scan.py)'])
        fixture.write_text(cited)
        self.assertIn('docs/contract/scan.py', prose_inputs(root))
        self.assertEqual(broken_links([fixture]), [])
        fixture.write_text(cited.replace('[source](scan.py)', '[source](missing-scan.py)', 1))
        self.assertTrue(any('missing file missing-scan.py' in problem for problem in broken_links([fixture])))
        gen = module('scan_contract', ROOT / 'docs/generate_contract_stamps.py')
        rendered = gen.DOCUMENT_BEGIN + '\nGenerated capacity is 707 bytes.\n' + gen.DOCUMENT_END + '\n'
        self.assertNotIn('707 bytes', authored_prose(rendered, 'docs/CONTRACT.md'))

    def test_prose_baseline_is_consistent_and_growth_is_explicit(self):
        self.assertEqual(baseline_problems(), [])
        # The scan reads the prose scope and the files its citation pairs link to, beside the baseline itself.
        root = self.checkout()
        fixture_inputs.copy_declared(ROOT, root, prose_inputs(ROOT), extra=[BASELINE_NAME])
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
                        + 'The `no_such_symbol_q7` ([generate_architecture.py](generate_architecture.py)) case.\n'
                        + '\nThe `load_manifest` routine ends here.<!-- note --> See [generate_architecture.py](generate_architecture.py).\n')
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
                self.track_inputs(root)
                def git(*args):
                    result = self.run_command(['git', '-C', str(root), '-c', 'user.name=Generator Control',
                        '-c', 'user.email=generator@example.invalid', '-c', 'commit.gpgsign=false',
                        '-c', 'tag.gpgsign=false', *args], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    return result.stdout
                import generate_contract_stamps as stamps
                import build_contract
                fixture_inputs.copy_declared(ROOT, root, sorted(set(stamps.input_paths(ROOT)) | set(build_contract.inputs(ROOT))))
                contract_fixture.fresh_authoring(root, stamps)
                def commit(rows, tag):
                    path = root / BASELINE_NAME
                    if rows is not None:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(json.dumps(dict(schema_version=1, entries=rows)))
                    else:
                        path.unlink(missing_ok=True)
                    (root / 'version').write_text(tag)
                    contract_fixture.write_outputs(root, stamps.render(root, tag))
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

    def test_example_source_edit_is_stale_until_regeneration_and_moves_content_and_identity(self):
        import generate_contract_stamps as stamps
        import build_contract
        directory = tempfile.TemporaryDirectory(prefix='pw-example-source-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        fixture_inputs.copy_declared(ROOT, root, sorted(set(stamps.input_paths(ROOT)) | set(build_contract.inputs(ROOT))))
        self.track_inputs(root)
        contract_fixture.fresh_authoring(root, module('example_contract', root / 'docs/generate_contract_stamps.py'))
        source = root / 'controller/src/example.rs'
        original = source.read_text()

        def generated():
            snapshot = json.loads((root / 'docs/contract/public.json').read_text())
            request = next(row for row in snapshot['surfaces'] if row['id'] == 'request')
            return (root / 'docs/CONTRACT.md').read_text(), request['public'], build_contract.identity(root)

        self.assertEqual(self.command(root, 'contract_stamps', '--check').returncode, 0)
        before = generated()
        edited = original.replace('"specimen_id":"example"', '"specimen_id":"example-edited"')
        self.assertNotEqual(edited, original)
        source.write_text(edited)
        taken = self.snapshot(root)
        result = self.command(root, 'contract_stamps', '--check')
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('stale generated contract: docs/CONTRACT.md, docs/contract/public.json', result.stderr)
        self.assertEqual(self.snapshot(root), taken, 'refusal changed checkout')
        result = self.command(root, 'contract_stamps')
        self.assertEqual(result.returncode, 0, result.stderr)
        after = generated()
        for label, earlier, later in zip(('rendered contract', 'request surface payload', 'build identity'), before, after):
            self.assertNotEqual(earlier, later, label)
        self.assertIn('"specimen_id": "example-edited"', after[0])
        self.assertEqual(self.command(root, 'contract_stamps', '--check').returncode, 0)
        # A forbidden member is refused by the check and by generation, naming the source.
        forbidden = edited.replace('{"specimen_id":"example-edited"', '{"contract":"release:v0.0.0","specimen_id":"example-edited"')
        self.assertNotEqual(forbidden, edited)
        source.write_text(forbidden)
        taken = self.snapshot(root)
        for args in (('--check',), ()):
            result = self.command(root, 'contract_stamps', *args)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("controller/src/example.rs: EXAMPLE_DOCUMENT carries the forbidden member 'contract'", result.stderr)
            self.assertEqual(self.snapshot(root), taken, 'refusal changed checkout')

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
        for graph in data['graphs']:
            graph['nodes'][0]['label'] += ' changed'
        path.write_text(json.dumps(data))
        script = root / 'docs/generate_architecture.py'
        script.write_text(script.read_text().replace('def render_svg(dot_text):',
            'def render_svg(dot_text):\n    if \"digraph \" + \"' + data['graphs'][-1]['id'] + '\" in dot_text:\n        raise RuntimeError("controlled render refusal")\n    return "<svg/>"'))
        before = self.snapshot(root)
        result = self.command(root, 'architecture')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('controlled render refusal', result.stderr)
        self.assertEqual(self.snapshot(root), before)

    def test_readme_form_table_is_a_copy_of_the_shared_rules(self):
        common = module('form_rules', ROOT / 'docs/generator_common.py')
        readme = (ROOT / 'tests/suites/source_drift/README.md').read_text()
        self.assertIn('\n'.join(common.form_table()), readme)
        # The copy is a table GitHub renders, not text in a comment or fence.

        def cells(table):
            return [[(cell.text, cell.code) for cell in row] for row in (table.header, *table.rows)]
        expected = cells(markdown_reader.parse('\n'.join(common.form_table())).tables[0])
        tables = markdown_reader.parse(readme).tables
        self.assertEqual(sum(cells(table) == expected for table in tables), 1)
        for form, _, _ in common.FORM_RULES:
            self.assertEqual(sum(row[0].code == [form] for table in tables for row in table.rows), 1, form)
            self.assertTrue(common.allowed_file(form, 'tests/suites/source_drift/check.py') in (True, False))
        with self.assertRaises(ValueError):
            common.allowed_file('maybe', 'tests/suites/source_drift/check.py')

    def test_document_graph_cites_every_drift_rule(self):
        common = module('rule_table', ROOT / 'docs/generator_common.py')
        rules = {function for _, function in common.rule_declarations((ROOT / 'tests/suites/source_drift/check.py').read_text())}
        self.assertTrue(rules)
        data = json.loads((ROOT / 'docs/architecture.json').read_text())
        graph = next(g for g in data['graphs'] if g['id'] == 'documents')
        node = next(n for n in graph['nodes'] if n['id'] == 'drift_check')
        cited = {r['symbol'] for r in node['checks']
                 if r['form'] == 'rule' and r['path'] == 'tests/suites/source_drift/check.py'}
        self.assertEqual(cited, rules)

    def test_rule_citations_read_the_rules_table(self):
        """A rule citation resolves through the module's static RULES table: a defined but unregistered function,
        an orphan table, a removed or duplicated row and an undefined function are refused without running it."""
        common = module('rule_table_citations', ROOT / 'docs/generator_common.py')
        good = ('def check_a(tree):\n    return []\n\n\nRULES = (\n    Rule("a", check_a),\n)\n\n\n'
                'def main():\n    return run(RULES)\n')

        def cite(text, symbol='check_a'):
            with tempfile.TemporaryDirectory(prefix='pw-rule-table-') as directory:
                path = Path(directory) / 'tests/suites/source_drift/x.py'
                path.parent.mkdir(parents=True)
                path.write_text(text)
                common.citation(dict(path='tests/suites/source_drift/x.py', symbol=symbol, form='rule'), Path(directory), check=True)

        cite(good)
        self.assertEqual(common.rule_declarations(good), (('a', 'check_a'),))
        for name, text, symbol, message in [
            ('defined but unregistered', good.replace('def check_a(tree):', 'def check_b(tree):\n    return []\n\n\ndef check_a(tree):'),
             'check_b', 'not defined'),
            ('orphan table', good.replace('return run(RULES)', 'return run(())'), 'check_a', 'does not use the RULES table'),
            ('removed row', good.replace('    Rule("a", check_a),\n', ''), 'check_a', 'not defined'),
            ('duplicated row', good.replace('    Rule("a", check_a),\n', '    Rule("a", check_a),\n    Rule("a", check_a),\n'),
             'check_a', 'duplicate rule ID'),
            ('undefined function', good.replace('Rule("a", check_a)', 'Rule("a", check_missing)'), 'check_a', 'undefined function'),
            ('malformed row', good.replace('Rule("a", check_a)', 'Rule(check_a)'), 'check_a', 'each RULES row'),
            ('two tables', good + '\nRULES = ()\n', 'check_a', 'expected one'),
            ('call from main without a table', 'def check_a(tree):\n    return []\n\n\ndef main():\n    return check_a(None)\n',
             'check_a', 'not defined'),
        ]:
            with self.subTest(case=name):
                with self.assertRaises(ValueError) as context:
                    cite(text, symbol)
                self.assertIn(message, str(context.exception))

    def test_fixture_declarations_cover_each_generators_inputs(self):
        """Each generator's declared inputs include an independently listed set of files it is known to read;
        discovery follows a new citation, a new target document and a new native helper; a relocated fixture
        without Git loads every helper module from inside the fixture; an omitted helper is a clear refusal."""
        known = {
            'porcelain': ['docs/porcelain.json', 'docs/generate_porcelain.py',
                          'runner/Sources/PWRunnerCore/PWPorcelainRecords.swift',
                          'controller/src/porcelain_records.rs', 'tests/lib/porcelain_schema.py'],
            'contract_stamps': ['docs/generate_contract_stamps.py', 'docs/CONTRACT.md', 'docs/PolicyWitness.md',
                                'docs/contract/00-identity.surface.md', 'docs/contract/tree.py',
                                'docs/contract/runtime.py', 'docs/contract/record_definitions.py',
                                'docs/contract/history_v0.py', 'docs/contract/history_v1.py',
                                'docs/contract/public.json', 'docs/contract/free_text.json',
                                'docs/generator_common.py', 'docs/markdown_reader.py'],
            'worker_identity': ['docs/generate_worker_identity.py', 'build.sh', 'meson.build', 'meson.options', 'runner/Package.swift',
                                'controller/tools/pw_probe_runner/pw_probe_runner.c', 'controller/tools/pw_probe_runner/pw_probe_runner_abi.h',
                                'runner/Sources/PWRunnerCore/CWorker.swift', 'tests/lib/contract.py'],
            'limits': ['docs/generate_limits.py', 'docs/generator_common.py', 'docs/markdown_reader.py', 'docs/limits.json',
                       'docs/LIMITS.md', 'docs/PolicyWitness.md', 'docs/QUESTIONS.md', 'tests/FAILURE-PROPAGATION-CONTRACT.md',
                       'tests/fixtures/comparison/matrix.json', 'tests/catalog.json', 'docs/ARCHITECTURE.md', 'controller/README.md'],
            'architecture': ['docs/generate_architecture.py', 'docs/generate_limits.py', 'docs/generator_common.py',
                             'docs/markdown_reader.py', 'docs/architecture.json', 'docs/limits.json', 'docs/ARCHITECTURE.md',
                             'docs/WORKER.md', 'tests/catalog.json', 'tests/suites/source_drift/check.py'],
            'footprint': ['docs/generate_footprint.py', 'docs/generator_common.py', 'docs/generate_limits.py',
                          'docs/footprint.json', 'docs/limits.json', 'docs/FOOTPRINT.md',
                          'docs/markdown_reader.py', 'tests/catalog.json'],
            'build': ['docs/generate_build.py', 'docs/generate_architecture.py', 'docs/generate_limits.py', 'docs/generator_common.py',
                      'docs/markdown_reader.py', 'docs/build.json', 'docs/BUILD.md', 'docs/build-steps.dot', 'docs/build-steps.svg',
                      'tests/fixtures/docs/build_baseline.json', 'build.sh', 'meson.build', 'Makefile', 'README.md',
                      'tests/lib/artifact.py', 'tests/build-evidence.py', 'tests/suites/source_drift/build_rules.py'],
        }
        for name in GENERATORS:
            with self.subTest(generator=name):
                declared = set(fixture_inputs.generator_inputs(ROOT, name))
                self.assertEqual(sorted(set(known[name]) - declared), [], name)
                self.assertTrue(all((ROOT / path).is_file() for path in declared), name)
        # A new citation, a new target document and a new native helper reach the declarations.
        with tempfile.TemporaryDirectory(prefix='pw-declared-') as directory:
            root = Path(directory)
            self.track_inputs(root)
            fixture_inputs.copy_declared(ROOT, root, fixture_inputs.generator_inputs(ROOT, 'limits')
                                         + fixture_inputs.generator_inputs(ROOT, 'architecture')
                                         + fixture_inputs.generator_inputs(ROOT, 'worker_identity'))
            limits = json.loads((root / 'docs/limits.json').read_text())
            limits['limits'][0]['sources'].append(dict(path='tests/fixtures/new_cited.py', symbol='cited'))
            (root / 'docs/limits.json').write_text(json.dumps(limits))
            self.assertIn('tests/fixtures/new_cited.py', fixture_inputs.generator_inputs(root, 'limits'))
            arch = json.loads((root / 'docs/architecture.json').read_text())
            arch['graphs'][0]['document'] = 'docs/NEW-TOUR.md'
            (root / 'docs/architecture.json').write_text(json.dumps(arch))
            declared = fixture_inputs.generator_inputs(root, 'architecture')
            self.assertIn('docs/NEW-TOUR.md', declared)
            self.assertIn(f"docs/{arch['graphs'][0]['file']}.dot", declared)
            (root / 'controller/tools/pw_probe_runner/pw_new_helper.c').write_text('/* new helper */\n')
            self.assertIn('controller/tools/pw_probe_runner/pw_new_helper.c', fixture_inputs.generator_inputs(root, 'worker_identity'))
            (root / 'docs/limits.json').write_text('{')
            self.assertTrue({'docs/limits.json', 'docs/generate_limits.py'} <= set(fixture_inputs.generator_inputs(root, 'limits')))
        # Copied command entry points run in fresh interpreters from inside the fixture, importing helpers from it.
        root = self.checkout()
        probe = ('import importlib.util, json, sys\n'
                 'spec = importlib.util.spec_from_file_location("probe", sys.argv[1]); module = importlib.util.module_from_spec(spec)\n'
                 'spec.loader.exec_module(module)\n'
                 'if hasattr(module, "contract_module"): module.contract_module("runtime")\n'
                 'print(json.dumps({name: value.__file__ for name, value in sys.modules.copy().items() '
                 'if getattr(value, "__file__", None) and (name in ("generator_common", "markdown_reader", "generate_limits", '
                 '"generate_architecture") or "/docs/contract/" in value.__file__)}))\n')
        for name in GENERATORS:
            with self.subTest(fresh_import=name):
                result = self.run_command([sys.executable, '-B', '-S', '-c', probe, str(root / f'docs/generate_{name}.py')],
                                        cwd=root, capture_output=True, text=True, timeout=60)
                self.assertEqual(result.returncode, 0, result.stderr)
                loaded = json.loads(result.stdout)
                for module_name, path in loaded.items():
                    self.assertTrue(Path(path).resolve().is_relative_to(root.resolve()), (name, module_name, path))
                if name in ('limits', 'architecture', 'build', 'footprint'):
                    self.assertIn('generator_common', loaded)
                if name == 'contract_stamps':
                    self.assertLessEqual({'runtime.py', 'tree.py', 'history_v0.py', 'history_v1.py',
                                          'record_definitions.py'},
                                         {Path(path).name for path in loaded.values()})
        (root / 'docs/contract/history_v0.py').unlink()
        result = self.command(root, 'contract_stamps', '--check')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('history_v0', result.stderr)
        # An omitted helper is a clear refusal, not a silent pass.
        (root / 'docs/generator_common.py').unlink()
        result = self.command(root, 'limits', '--check')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('generator_common', result.stderr)

    def test_prose_inputs_include_every_local_link_destination(self):
        """The prose scope's declaration closes over the local files its links name, not only the documents."""
        documents = [p.relative_to(ROOT).as_posix() for p in scanned_documents(ROOT)]
        declared = set(prose_inputs(ROOT))
        self.assertTrue(set(documents) <= declared)
        targets = set()
        for path in scanned_documents(ROOT):
            for link in (link for document in public_link_documents(path) for link in document.links):
                target = link.target.split('#')[0]
                if target and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                    targets.add((path.parent / target).resolve().relative_to(ROOT.resolve()).as_posix())
        self.assertTrue(targets)
        self.assertEqual(sorted(targets - declared), [])

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
        authored = common.authored_spans('Value <!-- span unknown.value -->1<!-- /span -->')
        self.assertTrue(any(m[1].split('.', 1)[0] not in {'architecture', 'limits', 'build', 'footprint'} for m in authored))



class ReceiptContractTests(receipts.TestCase):
    def test_failed_subtests_and_fixture_errors_have_their_own_receipts(self):
        class Probe(receipts.TestCase):
            def test_a(self):
                with self.subTest(value='rejected'):
                    self.fail('deliberate subtest failure')
                with self.subTest(value='accepted'):
                    self.assertTrue(True)

            def test_b(self):
                pass

            def test_c(self):
                raise ValueError('deliberate error')

            def test_d(self):
                self.addCleanup(lambda: (_ for _ in ()).throw(ValueError('cleanup failure')))

        class SetupProbe(receipts.TestCase):
            @classmethod
            def setUpClass(cls):
                raise ValueError('class setup failure')

            def test_never_reached(self):
                raise AssertionError('must not run')

        with tempfile.TemporaryDirectory(prefix='pw-receipts-') as directory:
            root = Path(directory)
            file = receipts.Receipts(root / 'receipts.json', 'probe', 'unittest')
            runner = unittest.TextTestRunner(stream=io.StringIO(), resultclass=lambda *a, **kw: receipts.TimedResult(*a, receipts=file, **kw))
            result = runner.run(unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                                                   for cls in (Probe, SetupProbe)]))
            file.finish(result.wasSuccessful())
            data = json.loads(file.path.read_text())
            self.assertFalse(data['ok'])
            self.assertTrue(data['complete'])
            self.assertEqual([c['status'] for c in data['controls']], ['fail', 'pass', 'error', 'error', 'error'])
            self.assertEqual([s['status'] for s in data['controls'][0]['subtests']], ['fail', 'pass'])
            self.assertEqual(data['controls'][1]['subtests'], [])
            self.assertEqual(data['controls'][1]['failed_subtests'], [])
            self.assertTrue(all(c['elapsed_seconds'] >= 0 for c in data['controls']))
            self.evidence.capture(root, label='receipt outcomes')

    def test_command_receipts_keep_inputs_output_and_failed_launches(self):
        with tempfile.TemporaryDirectory(prefix='pw-receipt-command-') as directory:
            root = Path(directory)
            inputs = root / 'inputs'
            inputs.mkdir()
            (inputs / 'changed').write_text('before')
            (inputs / 'deleted').write_text('remove me')
            file = receipts.Receipts(root / 'receipts.json', 'probe', 'unittest')
            record = file.add(id='000', inputs=[], launches=[])
            evidence = receipts.Control(file, record)
            evidence.track(inputs)
            (inputs / 'changed').write_text('after')
            (inputs / 'deleted').unlink()
            (inputs / 'added').write_text('new')
            (inputs / 'alias').symlink_to('changed')
            result = evidence.run([sys.executable, '-B', '-S', '-P', '-c',
                                   'import sys; print("output"); print("diagnostic", file=sys.stderr); sys.exit(3)'],
                                  capture_output=True, text=True)
            self.assertEqual(result.returncode, 3)
            launch = record['launches'][0]
            self.assertEqual((root / launch['stdout']).read_text(), 'output\n')
            self.assertEqual((root / launch['stderr']).read_text(), 'diagnostic\n')
            snapshot = json.loads((root / launch['inputs'][0]).read_text())
            self.assertEqual(snapshot['changed'], ['added', 'alias', 'changed', 'deleted'])
            self.assertEqual(snapshot['entries']['alias']['target'], 'changed')
            self.assertEqual((root / snapshot['entries']['changed']['blob']).read_text(), 'after')
            with self.assertRaises(subprocess.TimeoutExpired):
                evidence.run([sys.executable, '-B', '-S', '-P', '-c',
                              'import time; print("started", flush=True); time.sleep(60)'], timeout=1, capture_output=True)
            self.assertEqual(record['launches'][-1]['status'], 'timeout')
            self.assertEqual((root / record['launches'][-1]['stdout']).read_bytes(), b'started\n')
            with self.assertRaises(FileNotFoundError):
                evidence.run([str(root / 'absent-command')])
            self.assertEqual(record['launches'][-1]['status'], 'error')
            with self.assertRaises(subprocess.CalledProcessError):
                evidence.run([sys.executable, '-B', '-S', '-P', '-c', 'raise SystemExit(4)'], check=True)
            self.assertEqual(record['launches'][-1]['returncode'], 4)
            file.finish(False, complete=False)
            data = json.loads(file.path.read_text())
            self.assertFalse(data['complete'])
            self.assertEqual(len(data['controls'][0]['launches']), 4)
            self.assertTrue(all(c['elapsed_seconds'] >= 0 for c in record['launches']))
            self.evidence.capture(root, label='command evidence')


if __name__ == '__main__':
    sys.exit(receipts.timed_main(sys.modules[__name__], 'source_drift/generator_contract', 'generators'))
