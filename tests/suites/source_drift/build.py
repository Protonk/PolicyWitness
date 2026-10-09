"""Guard the build manifest, its generated figure and document copies, and the grounding rules that read build.sh."""
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
spec = importlib.util.spec_from_file_location('generate_build', ROOT / 'docs/generate_build.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
SCRIPT = (ROOT / 'build.sh').read_text()


class BuildDocumentationTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / generator.MANIFEST_NAME).read_text())
        self.document = ROOT / self.manifest['document']
        self.figures = [self.document.parent / f"{self.manifest['figure']}{suffix}" for suffix in ('.dot', '.svg')]

    # ---- a disposable checkout holding the generator's inputs, outputs and every cited file ----
    def cited(self):
        paths = set()
        for group in ('steps', 'refusals', 'signing', 'invocations', 'knobs', 'directories'):
            for item in self.manifest[group]:
                paths.update(ref['path'] for key in ('sources', 'checks') for ref in item[key])
        return paths

    def checkout(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-build-doc-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        paths = {'docs/generator_common.py', 'docs/generate_architecture.py', 'docs/generate_limits.py', 'docs/limits.json',
                 'tests/catalog.json', generator.GENERATOR_NAME, generator.MANIFEST_NAME, generator.BASELINE_NAME,
                 self.manifest['document'], 'build.sh', 'meson.build', 'Makefile', 'README.md', 'Info.plist',
                 'runner/Services/PWRunner/Info.plist', 'tests/lib/artifact.py', 'tests/build-evidence.py'}
        paths.update(str(p.relative_to(ROOT)) for p in self.figures)
        paths |= self.cited()
        for name in paths:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        return root

    def command(self, root, *args):
        return subprocess.run([sys.executable, '-B', str(root / generator.GENERATOR_NAME), *args],
                              cwd=root, capture_output=True, text=True, timeout=120)

    def load(self, data, root=ROOT):
        with tempfile.TemporaryDirectory(prefix='pw-build-manifest-') as directory:
            path = Path(directory) / 'build.json'
            path.write_text(json.dumps(data))
            return generator.load_manifest(path, root)

    # ---- currency ----
    def test_document_and_figure_are_current_and_the_rules_agree(self):
        result = self.command(ROOT, '--check')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith('ok: build manifest'), result.stdout)
        for path in self.figures:
            self.assertTrue(path.is_file(), path)
        rules = subprocess.run([sys.executable, '-B', str(ROOT / 'tests/suites/source_drift/build_rules.py')],
                               cwd=ROOT, capture_output=True, text=True, timeout=120)
        self.assertEqual(rules.returncode, 0, rules.stderr)
        self.assertIn('10 build documentation rules agree', rules.stdout)

    def test_manifest_rejects_broken_citations_references_and_ids(self):
        self.load(self.manifest)
        mutations = {
            'missing symbol': lambda d: d['steps'][2]['sources'][0].__setitem__('symbol', 'no_such_symbol_9f3'),
            'missing file': lambda d: d['steps'][2]['sources'][0].__setitem__('path', 'docs/no-such-file.md'),
            'unknown step in refusal': lambda d: d['refusals'][0].__setitem__('steps', ['no_such_step']),
            'duplicate step id': lambda d: d['steps'].append(copy.deepcopy(d['steps'][2])),
            'refusal not listed by its step': lambda d: d['steps'][1]['refusals'].pop(),
            'step lists unknown refusal': lambda d: d['steps'][1]['refusals'].append('no_such_refusal'),
            'self citation': lambda d: d['steps'][2]['sources'][0].update(path='docs/build.json', symbol='schema_version'),
            'output citation': lambda d: d['steps'][2]['sources'][0].update(path='docs/BUILD.md', symbol='BEGIN GENERATED BUILD'),
            'missing coverage': lambda d: d['refusals'][0]['checks'][0].pop('coverage'),
            'invalid coverage': lambda d: d['refusals'][0]['checks'][0].update(coverage='maybe'),
            'missing form': lambda d: d['refusals'][0]['checks'][0].pop('form'),
            'no test or rule': lambda d: d['steps'][2].update(checks=[]),
            'literal duration': lambda d: d['steps'][2].update(reads='7 seconds of git'),
            'old schema': lambda d: d.update(schema_version=1),
            'unknown variant': lambda d: d['steps'][2].update(variants=['debug']),
            'empty banner': lambda d: d['steps'][2].update(banners=['']),
            'two unbannered steps': lambda d: d['steps'].insert(3, dict(d['steps'][1], id='admission_two')),
            'unknown refusal kind': lambda d: d['refusals'][0].update(kind='maybe'),
            'non-decimal status': lambda d: d['refusals'][0].update(status=2),
            'unknown signing kind': lambda d: d['signing'][0].update(kind='maybe'),
            'knob without its default': lambda d: d['knobs'][0].update(default='9'),
            'directory facts': lambda d: d['directories'][0]['facts'].pop('Refused when'),
            'unknown field': lambda d: d['steps'][2].__setitem__('colour', 'red'),
            'make step not first': lambda d: d['steps'].append(d['steps'].pop(0)),
        }
        for name, mutate in mutations.items():
            data = copy.deepcopy(self.manifest)
            mutate(data)
            with self.assertRaises(ValueError, msg=name):
                self.load(data)

    def test_every_id_is_in_its_generated_region(self):
        text = self.document.read_text()
        regions = {}
        for region in generator.REGIONS:
            start = generator.REGION_START.format(region=region)
            end = generator.REGION_END.format(region=region)
            regions[region] = text.split(start)[1].split(end)[0]
        self.assertIn(f"{self.manifest['figure']}.svg", regions['FIGURE'])
        for step in self.manifest['steps']:
            self.assertIn(f"| {step['id']} |", regions['STEPS'], step['id'])
        for refusal in self.manifest['refusals']:
            self.assertIn(f"| {refusal['id']} |", regions['REFUSALS'], refusal['id'])
        for index, entry in enumerate(self.manifest['signing'], start=1):
            self.assertIn(f"| {index} | {generator.arch.cell(entry['target'])} |", regions['SIGNING'], entry['id'])
        for knob in self.manifest['knobs']:
            self.assertIn(f"| {knob['name']} |", regions['KNOBS'])
        for directory in self.manifest['directories']:
            self.assertIn(f"| {directory['path']} |", regions['DIRECTORIES'])

    def test_captions_state_the_verified_guarantee(self):
        def verified(text):
            return ('presence' in text and 'definition' in text and 'is not verified' in text
                    and not re.search(r'\b(exercises|covers|proves)\b', text))
        region = generator.render_figure(self.manifest)
        caption = next(line for line in region.splitlines() if line.startswith('*Figure:'))
        self.assertTrue(verified(caption))
        self.assertIn('refusal fires before the operation it protects, is not verified', caption)
        for render in (generator.render_steps, generator.render_refusals, generator.render_signing):
            summary = next(line for line in render(self.manifest).splitlines() if line.startswith('<summary>'))
            self.assertTrue(verified(summary), summary)
            for word in ('exercises', 'covers', 'proves'):
                self.assertFalse(verified(summary + ' ' + word))

    def test_svg_stamp_names_its_dot_text(self):
        dot_text = generator.render_dot(self.manifest)
        svg = self.figures[1].read_text(errors='replace')
        self.assertTrue(generator.svg_stamp_matches(svg, dot_text))
        self.assertFalse(generator.svg_stamp_matches(svg, dot_text + '\n'))

    def test_stale_copies_are_refused_then_regenerated_idempotently(self):
        root = self.checkout()
        self.assertEqual(self.command(root, '--check').returncode, 0, self.command(root, '--check').stderr)
        dot_path = root / 'docs' / f"{self.manifest['figure']}.dot"
        svg_path = dot_path.with_suffix('.svg')
        document = root / self.manifest['document']
        originals = {p: p.read_text(errors='replace') for p in (dot_path, svg_path, document)}
        for path, mutate, expected in (
            (dot_path, lambda t: t.replace('rankdir=', 'rankdir = '), 'stale or missing'),
            (svg_path, lambda t: t.replace('dot sha256 ', 'dot sha256 0'), 'stamp does not name'),
            (document, lambda t: t.replace(f"| {self.manifest['steps'][2]['id']} |", f"| {self.manifest['steps'][2]['id']}x |", 1), 'regions are stale'),
        ):
            path.write_text(mutate(originals[path]))
            result = self.command(root, '--check')
            self.assertEqual(result.returncode, 1, (path.name, result.stdout))
            self.assertIn(expected, result.stderr, path.name)
            self.assertEqual(path.read_text(errors='replace'), mutate(originals[path]), 'check wrote')
        result = self.command(root, '--skip-svg')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(dot_path.read_text(), originals[dot_path])
        self.assertEqual(document.read_text(), originals[document])
        result = self.command(root, '--check')
        self.assertEqual(result.returncode, 1)
        self.assertIn('stamp does not name', result.stderr)
        svg_path.write_text(originals[svg_path])
        self.assertEqual(self.command(root, '--check').returncode, 0)
        second = self.command(root, '--skip-svg')
        self.assertEqual(second.returncode, 0)
        self.assertIn('wrote nothing', second.stdout)

    def test_broken_marker_or_citation_stops_before_any_write(self):
        root = self.checkout()
        document = root / self.manifest['document']
        before = {p: p.read_text(errors='replace') for p in root.rglob('*') if p.is_file()}
        text = document.read_text()
        document.write_text(text.replace(generator.REGION_END.format(region='STEPS'), '', 1))
        result = self.command(root, '--skip-svg')
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn('expected exactly one ordered block', result.stderr)
        document.write_text(text)
        manifest_path = root / generator.MANIFEST_NAME
        data = json.loads(manifest_path.read_text())
        data['steps'][2]['sources'][0]['symbol'] = 'no_such_symbol_9f3'
        manifest_path.write_text(json.dumps(data))
        result = self.command(root, '--skip-svg')
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn('missing symbol', result.stderr)
        manifest_path.write_text(before[manifest_path])
        # A manifest that disagrees with the script is refused before any write, by the generator itself.
        script = root / 'build.sh'
        script.write_text(SCRIPT.replace('echo "==> Checking limits documentation"\n', 'echo "==> Checking limits documentation"\necho "==> An extra banner"\n', 1))
        result = self.command(root, '--skip-svg')
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn('banner order', result.stderr)
        script.write_text(SCRIPT)
        after = {p: p.read_text(errors='replace') for p in root.rglob('*') if p.is_file()}
        self.assertEqual(before, after, 'a refused generation changed the checkout')

    # ---- the grounding rules against mutations of a disposable copy of the script and its neighbours ----
    def mutated(self, old, new, count=1, text=SCRIPT):
        self.assertEqual(text.count(old), count, old)
        return text.replace(old, new)

    def test_script_mutations_are_named_by_their_rule(self):
        manifest = generator.load_manifest(ROOT / generator.MANIFEST_NAME, ROOT)
        model = generator.parse_script(SCRIPT)
        self.assertEqual(generator.banner_problems(manifest, model), [])
        self.assertEqual(generator.refusal_problems(manifest, model), [])
        self.assertEqual(generator.knob_problems(manifest, model), [])
        self.assertEqual(generator.signing_problems(manifest, model), [])
        self.assertEqual(generator.invocation_problems(manifest, model), [])
        cases = [
            ('reordered banner', generator.banner_problems,
             SCRIPT.replace('echo "==> Checking limits documentation"\n/usr/bin/python3 -B "${ROOT_DIR}/docs/generate_limits.py" --check\necho "==> Checking contract versions"',
                            'echo "==> Checking contract versions"\n/usr/bin/python3 -B "${ROOT_DIR}/docs/generate_limits.py" --check\necho "==> Checking limits documentation"', 1),
             'banner order: position 1'),
            ('removed banner', generator.banner_problems, self.mutated('echo "==> Compiling native executables"\n', ''), 'banner order'),
            ('banner variant moved', generator.banner_problems,
             self.mutated('  echo "==> Embedding PW runner client"\n', '').replace('if [[ "${BUILD_XPC}" == "1" ]]; then\n  echo "==> Embedding PW runner client"',
                                                                                 'echo "==> Embedding PW runner client"\nif [[ "${BUILD_XPC}" == "1" ]]; then', 0),
             'banner order'),
            ('added refusal', generator.refusal_problems,
             self.mutated('echo "==> Compiling native executables"\n', 'echo "==> Compiling native executables"\necho "ERROR: control refusal" 1>&2\nexit 2\n'),
             "refusal 'control refusal' at line"),
            ('removed refusal', generator.refusal_problems,
             self.mutated('  echo "ERROR: missing augments source dir at ${XPC_AUGMENTS_DIR}" 1>&2\n  exit 2\n', '  :\n'),
             'not printed by the script'),
            ('refusal moved to another step', generator.refusal_problems,
             self.mutated('if [[ ! -f "${ENTITLEMENTS_PLIST}" ]]; then\n  echo "ERROR: missing entitlements plist: ${ENTITLEMENTS_PLIST}" 1>&2\n  exit 2\nfi\n', '')
                 .replace('echo "==> Codesigning embedded MacOS tools"\n', 'echo "==> Codesigning embedded MacOS tools"\nif [[ ! -f "${ENTITLEMENTS_PLIST}" ]]; then\n  echo "ERROR: missing entitlements plist: ${ENTITLEMENTS_PLIST}" 1>&2\n  exit 2\nfi\n', 1),
             'refusal missing_entitlements: manifest steps'),
            ('changed exit status', generator.refusal_problems,
             self.mutated('      echo "ERROR: ${knob} must be 0 or 1 (got \'${!knob}\')" 1>&2\n      exit 2', '      echo "ERROR: ${knob} must be 0 or 1 (got \'${!knob}\')" 1>&2\n      exit 3'),
             'refusal knob_value: manifest status 2, script exit 3'),
            ('renamed knob', generator.knob_problems, SCRIPT.replace('BUILD_XPC', 'BUILD_XPX'), 'knobs: manifest'),
            ('knob accepts another value', generator.knob_problems, self.mutated('    0|1) ;;', '    0|1|2) ;;'), 'knob BUILD_XPC: manifest values'),
            ('knob default changed', generator.knob_problems, self.mutated('BUILD_XPC="${BUILD_XPC-1}"', 'BUILD_XPC="${BUILD_XPC-0}"'), 'knob BUILD_XPC: manifest default'),
            ('removed signing call', generator.signing_problems, self.mutated('sign_macho "${APP_BUNDLE}/Contents/MacOS/sbpl-check"\n', ''), 'signing order'),
            ('signing call moved out of its variant', generator.signing_problems,
             self.mutated('if [[ "${BUILD_XPC}" == "1" ]]; then\n  sign_macho "${APP_BUNDLE}/Contents/MacOS/pw-runner-client"\nfi\n', 'sign_macho "${APP_BUNDLE}/Contents/MacOS/pw-runner-client"\n'),
             'signing order: entry 1'),
            ('seal without entitlements', generator.signing_problems,
             self.mutated('codesign --force --options runtime --timestamp \\\n  --entitlements "${ENTITLEMENTS_PLIST}" \\\n  -s "${IDENTITY}" "${APP_BUNDLE}"', 'codesign --force --options runtime --timestamp -s "${IDENTITY}" "${APP_BUNDLE}"'),
             'signing order: entry 7'),
            ('helper moved to another step', generator.invocation_problems,
             self.mutated('echo "==> Checking every executable\'s signer"\n/usr/bin/python3 -B "${ROOT_DIR}/tests/lib/signer_check.py" "${APP_BUNDLE}" "${IDENTITY}"\n', 'echo "==> Checking every executable\'s signer"\n')
                 .replace('echo "==> Verifying signature + entitlements"\n', 'echo "==> Verifying signature + entitlements"\n/usr/bin/python3 -B "${ROOT_DIR}/tests/lib/signer_check.py" "${APP_BUNDLE}" "${IDENTITY}"\n', 1),
             "invocation 'tests/lib/signer_check.py' in step verify"),
            ('generator check removed', generator.invocation_problems,
             self.mutated('/usr/bin/python3 -B "${ROOT_DIR}/docs/generate_build.py" --check\n', ''), "invocation 'docs/generate_build.py --check' in step check_build_doc"),
        ]
        for name, rule, text, expected in cases:
            with self.subTest(mutation=name):
                self.assertNotEqual(text, SCRIPT, name)
                problems = rule(manifest, generator.parse_script(text))
                self.assertTrue(problems, name)
                self.assertTrue(any(expected in p for p in problems), (name, problems))

    def test_unsupported_script_forms_are_refused_by_the_parser(self):
        cases = [
            ('banner inside a function', self.mutated('usage() {\n', 'usage() {\n  echo "==> inside"\n'), 'inside a function or case'),
            ('refusal without an exit', self.mutated('      echo "ERROR: ${knob} must be 0 or 1 (got \'${!knob}\')" 1>&2\n      exit 2\n', '      echo "ERROR: ${knob} must be 0 or 1 (got \'${!knob}\')" 1>&2\n'), 'without a constant exit status'),
            ('single-quoted error', self.mutated('echo "ERROR: unknown argument: $1" 1>&2', "echo 'ERROR: unknown argument' 1>&2"), 'must be double-quoted'),
            ('elif', self.mutated('else\n  echo "==> Skipping embedded XPC build (BUILD_XPC=0)"', 'elif true; then\n  echo "==> Skipping embedded XPC build (BUILD_XPC=0)"'), 'elif is not a supported form'),
            ('unbalanced fi', SCRIPT + 'fi\n', 'unbalanced fi'),
            ('unknown codesign form', self.mutated('codesign --verify --deep --strict --verbose=2 "${APP_BUNDLE}"', 'codesign --remove-signature "${APP_BUNDLE}"'), 'neither a seal nor a verification'),
            ('refusal in an uncalled function', SCRIPT + 'orphan() {\n  echo "ERROR: never" 1>&2\n  exit 2\n}\n', 'never called'),
            ('unterminated heredoc', self.mutated("cat <<'USAGE'\n", "cat <<'USAGX'\n"), 'unterminated heredoc'),
        ]
        for name, text, expected in cases:
            with self.subTest(form=name):
                with self.assertRaises(generator.ParseError, msg=name) as context:
                    generator.parse_script(text)
                self.assertIn(expected, str(context.exception), name)

    def test_meson_makefile_inventory_and_baseline_mutations_are_named(self):
        manifest = generator.load_manifest(ROOT / generator.MANIFEST_NAME, ROOT)
        model = generator.parse_script(SCRIPT)
        meson = (ROOT / 'meson.build').read_text()
        self.assertEqual(generator.meson_problems(manifest, meson), [])
        added = meson.replace("  'b_lto': false,\n", "  'b_lto': false,\n  'b_colorout': 'auto',\n", 1)
        self.assertTrue(any("b_colorout must be 'auto'" in p and 'not in the manifest' in p for p in generator.meson_problems(manifest, added)))
        removed = meson.replace("  'b_lto': false,\n", '', 1)
        self.assertTrue(any('b_lto' in p and 'not asserted' in p for p in generator.meson_problems(manifest, removed)))
        makefile = (ROOT / 'Makefile').read_text()
        self.assertEqual(generator.makefile_problems(manifest, makefile), [])
        guardless = makefile.replace('\t\techo "ERROR: set IDENTITY to your Developer ID Application identity"; \\\n', '', 1)
        self.assertNotEqual(guardless, makefile)
        self.assertTrue(any('not printed' in p for p in generator.makefile_problems(manifest, guardless)))
        self.assertEqual(generator.inventory_problems(manifest, model, ROOT), [])
        root = self.checkout()
        artifact = root / 'tests/lib/artifact.py'
        artifact.write_text(artifact.read_text().replace("'sbpl-check'))", "'sbpl-check', 'extra-tool'))", 1))
        self.assertTrue(any('EXECUTABLES lists' in p for p in generator.inventory_problems(manifest, model, root)))
        artifact.write_text((ROOT / 'tests/lib/artifact.py').read_text())
        evidence = root / 'tests/build-evidence.py'
        evidence.write_text(evidence.read_text().replace('"sbpl-check",\n    ]', '"sbpl-check",\n        "extra-tool",\n    ]', 1))
        self.assertTrue(any('helper_names' in p for p in generator.inventory_problems(manifest, model, root)))
        evidence.write_text((ROOT / 'tests/build-evidence.py').read_text())
        readme = root / 'README.md'
        readme.write_text(readme.read_text().replace('  - `Contents/MacOS/sbpl-check`', '  - `Contents/MacOS/sbpl-checker`', 1))
        self.assertTrue(any("README 'What ships'" in p for p in generator.inventory_problems(manifest, model, root)))
        baseline = generator.load_baseline(ROOT / generator.BASELINE_NAME)
        self.assertEqual(generator.baseline_problems(manifest, baseline), [])
        shorter = {'schema_version': 1, 'entries': baseline['entries'][1:]}
        self.assertTrue(any('is not listed' in p for p in generator.baseline_problems(manifest, shorter)))
        longer = {'schema_version': 1, 'entries': baseline['entries'] + [dict(baseline['entries'][0], refusal='knob_value')]}
        self.assertTrue(any('now has a control' in p for p in generator.baseline_problems(manifest, longer)))
        with self.assertRaises(ValueError):
            generator.load_baseline(root / 'docs/build.json')

    def test_release_preflight_refuses_a_grown_build_baseline(self):
        release_spec = importlib.util.spec_from_file_location('preflight_build_baseline', ROOT / 'tests/lib/release_preflight.py')
        release = importlib.util.module_from_spec(release_spec)
        release_spec.loader.exec_module(release)
        entry = dict(refusal='example_refusal', variants=['full'], claim='an example', control='a sketch')
        rewritten = dict(entry, control='another sketch')
        for label, previous, candidate, refused in [('equal', [entry], [entry], False), ('subset', [entry], [], False),
                                                     ('superset', [entry], [entry, dict(entry, refusal='second')], True),
                                                     ('rewritten', [entry], [rewritten], True), ('predates', None, [entry], False)]:
            with self.subTest(case=label):
                directory = tempfile.TemporaryDirectory(prefix='pw-build-baseline-release-')
                self.addCleanup(directory.cleanup)
                root = Path(directory.name)
                def git(*args):
                    result = subprocess.run(['git', '-C', str(root), '-c', 'user.name=Build Control', '-c', 'user.email=build@example.invalid',
                                             '-c', 'commit.gpgsign=false', '-c', 'tag.gpgsign=false', *args], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                def commit(rows, tag):
                    if rows is not None:
                        path = root / generator.BASELINE_NAME
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(json.dumps(dict(schema_version=1, entries=rows)))
                    (root / 'version').write_text(tag)
                    git('add', '.'); git('commit', '-qm', tag); git('tag', '-a', tag, '-m', tag)
                git('init', '-q')
                commit(previous, 'v1.0.0')
                commit(candidate, 'v1.1.0')
                stamp, problems = release.inspect(root, remote=str(root))
                self.assertEqual(bool([p for p in problems if 'build baseline' in p]), refused, problems)
                self.assertEqual(stamp['build_baseline']['previous_tag'], 'v1.0.0')


if __name__ == '__main__':
    unittest.main()
