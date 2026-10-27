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
sys.path.insert(0, str(ROOT / 'docs'))
sys.path.insert(0, str(ROOT / 'tests/lib'))
import fixture_inputs  # noqa: E402
import markdown_reader  # noqa: E402
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
        copied = fixture_inputs.copy_declared(ROOT, root, fixture_inputs.generator_inputs(ROOT, 'build'))
        print(f'fixture: {copied.files} files, {copied.bytes} bytes, {copied.seconds:.3f} s')
        return root

    def command(self, root, *args):
        return subprocess.run([sys.executable, '-B', '-S', str(root / generator.GENERATOR_NAME), *args],
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
        # The grounding rules' command runs once per case, from the suite script; its gate is controlled below.

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
            'condition on an unbannered step': lambda d: d['steps'][1].__setitem__('when', 'fresh'),
            'unknown condition': lambda d: next(s for s in d['steps'] if s.get('when')).__setitem__('when', 'sometimes'),
            'asserts on a script row': lambda d: d['refusals'][0].__setitem__('asserts', ['optimization']),
            'meson row without asserts': lambda d: next(r for r in d['refusals'] if r['kind'] == 'meson').pop('asserts'),
            'duplicate asserted option': lambda d: next(r for r in d['refusals'] if r['kind'] == 'meson')['asserts'].append('optimization'),
            'empty asserts': lambda d: next(r for r in d['refusals'] if r['kind'] == 'meson').__setitem__('asserts', []),
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
            regions[region] = markdown_reader.parse(text.split(start)[1].split(end)[0])

        def first(region):
            return [row[0].text for table in regions[region].tables for row in table.rows]
        self.assertIn(f"{self.manifest['figure']}.svg", [Path(l.target).name for l in regions['FIGURE'].links if l.image])
        for step in self.manifest['steps']:
            self.assertIn(step['id'], first('STEPS'), step['id'])
        for refusal in self.manifest['refusals']:
            self.assertIn(refusal['id'], first('REFUSALS'), refusal['id'])
        signing = [(row[0].text, row[1].text) for table in regions['SIGNING'].tables for row in table.rows]
        for index, entry in enumerate(self.manifest['signing'], start=1):
            target = markdown_reader.parse(generator.arch.cell(entry['target'])).inlines[0].text
            self.assertIn((str(index), target), signing, entry['id'])
        for item in self.manifest['invocations']:
            self.assertIn(item['id'], first('INVOCATIONS'), item['id'])
        for knob in self.manifest['knobs']:
            self.assertIn(knob['name'], first('KNOBS'))
        for directory in self.manifest['directories']:
            self.assertIn(directory['path'], first('DIRECTORIES'))

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

    def test_figure_labels_links_and_paths_render_as_claimed(self):
        """Labels break on real newlines, every node links to an existing heading, and the edges follow each variant's path."""
        dot_text = generator.render_dot(self.manifest)
        svg = self.figures[1].read_text(errors='replace')
        self.assertNotIn('\\n', svg, 'a literal backslash-n reached the rendered figure')
        anchors = markdown_reader.read(self.document).anchors
        for anchor in set(re.findall(r'URL="BUILD\.md#([^"]+)"', dot_text)):
            self.assertIn(anchor, anchors)
        self.assertIn('assemble -> embed_client [color=', dot_text)
        self.assertIn('assemble -> skip_xpc [style=dashed]', dot_text)
        self.assertIn('skip_xpc -> assembled [style=dashed]', dot_text)
        self.assertIn('embed_services -> assembled [color=', dot_text)
        self.assertIn('assembled -> presign;', dot_text)
        self.assertNotIn('embed_services -> skip_xpc', dot_text)
        self.assertIn('sign_tools -> evidence [style=dashed]', dot_text)
        # The fresh-only step hangs off its predecessor and rejoins; the direct edge beside it is the incremental path.
        self.assertIn('cargo_admit -> fresh [style=dotted]', dot_text)
        self.assertIn('fresh -> cargo [style=dotted]', dot_text)
        self.assertIn('cargo_admit -> cargo;', dot_text)
        self.assertIn('(fresh mode only)', dot_text)
        self.assertIn('fresh mode only', svg)

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
             SCRIPT.replace('echo "==> Checking limits documentation"\n"${PW_PYTHON}" -B -S "${ROOT_DIR}/docs/generate_limits.py" --check\necho "==> Checking contract versions"',
                            'echo "==> Checking contract versions"\n"${PW_PYTHON}" -B -S "${ROOT_DIR}/docs/generate_limits.py" --check\necho "==> Checking limits documentation"', 1),
             'banner order: position 2'),
            ('removed banner', generator.banner_problems, self.mutated('echo "==> Compiling native executables"\n', ''), 'banner order'),
            ('banner variant moved', generator.banner_problems,
             self.mutated('  echo "==> Embedding PW runner client"\n', '').replace('if [[ "${BUILD_XPC}" == "1" ]]; then\n  echo "==> Embedding PW runner client"',
                                                                                 'echo "==> Embedding PW runner client"\nif [[ "${BUILD_XPC}" == "1" ]]; then', 0),
             'banner order'),
            ('added refusal', generator.refusal_problems,
             self.mutated('echo "==> Compiling native executables"\n', 'echo "==> Compiling native executables"\necho "ERROR: control refusal" 1>&2\nexit 2\n'),
             "refusal 'control refusal' at line"),
            ('removed refusal', generator.refusal_problems,
             self.mutated('    echo "ERROR: expected Meson output at ${native_bin}" 1>&2\n    exit 2\n', '    :\n'),
             'not printed by the script'),
            ('refusal moved to another step', generator.refusal_problems,
             self.mutated('    echo "ERROR: missing tracked build input: ${tree_input}" 1>&2\n    exit 2\n', '    :\n')
                 .replace('echo "==> Checking limits documentation"\n', 'echo "==> Checking limits documentation"\nif [[ ! -e "${ROOT_DIR}/${tree_input}" ]]; then\n  echo "ERROR: missing tracked build input: ${tree_input}" 1>&2\n  exit 2\nfi\n', 1),
             'refusal missing_tree_input: manifest steps'),
            ('fresh condition removed from a step', generator.banner_problems,
             self.mutated('if [[ "${PW_FRESH_BUILD}" == "1" ]]; then\n  echo "==> Replacing the build caches', 'if true; then\n  echo "==> Replacing the build caches'),
             'step fresh: manifest condition'),
            ('helper subcommand changed', generator.invocation_problems,
             self.mutated('build_provenance.py" stamp-check --root', 'build_provenance.py" stamp-extend --root'),
             "invocation 'tests/lib/build_provenance.py stamp-check --root' in step builddir"),
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
             f"signing order: entry {next(i for i, row in enumerate(manifest['signing'], 1) if row['id'] == 'seal_app')}"),
            ('helper moved to another step', generator.invocation_problems,
             self.mutated('echo "==> Checking every executable\'s signer"\n"${PW_PYTHON}" -B -S "${ROOT_DIR}/tests/lib/signer_check.py" "${APP_BUNDLE}" "${IDENTITY}"\n', 'echo "==> Checking every executable\'s signer"\n')
                 .replace('echo "==> Verifying signature + entitlements"\n', 'echo "==> Verifying signature + entitlements"\n"${PW_PYTHON}" -B -S "${ROOT_DIR}/tests/lib/signer_check.py" "${APP_BUNDLE}" "${IDENTITY}"\n', 1),
             "invocation 'tests/lib/signer_check.py' in step verify"),
            ('generator check removed', generator.invocation_problems,
             self.mutated('"${PW_PYTHON}" -B -S "${ROOT_DIR}/docs/generate_build.py" --check\n', ''), "invocation 'docs/generate_build.py --check' in step check_build_doc"),
            ('timestamp dropped from the signatures', generator.signing_problems,
             self.mutated('  codesign --force --options runtime --timestamp -s "${IDENTITY}" "${target}"', '  codesign --force --options runtime -s "${IDENTITY}" "${target}"'),
             'signing order: entry 1'),
            ('target directory dropped from cargo', generator.invocation_problems,
             self.mutated('  --target-dir "${CARGO_TARGET_DIR_PINNED}" \\\n', ''), 'invocation inv_cargo: manifest flags'),
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
            ('errexit dropped', self.mutated('set -euo pipefail', 'set -uo pipefail'), "must begin with 'set -euo pipefail'"),
        ]
        for name, text, expected in cases:
            with self.subTest(form=name):
                with self.assertRaises(generator.ParseError, msg=name) as context:
                    generator.parse_script(text)
                self.assertIn(expected, str(context.exception), name)

    def test_readme_inventory_reads_rendered_bullets_only(self):
        text = (ROOT / 'README.md').read_text()
        bullet = '  - `Contents/MacOS/sbpl-check` (SBPL compile-check helper)'
        self.assertEqual(text.count(bullet), 1)
        paths, services = generator.readme_inventory(text)
        self.assertIn('Contents/MacOS/sbpl-check', paths)
        for hidden in ('  <!--\n' + bullet + '\n  -->', '  ```text\n' + bullet + '\n  ```', '  `' + bullet.strip() + '`'):
            with self.subTest(hidden=hidden):
                moved, moved_services = generator.readme_inventory(text.replace(bullet, hidden, 1))
                self.assertEqual(moved, [p for p in paths if p != 'Contents/MacOS/sbpl-check'])
                self.assertEqual(moved_services, services)

    def test_meson_makefile_inventory_and_baseline_mutations_are_named(self):
        manifest = generator.load_manifest(ROOT / generator.MANIFEST_NAME, ROOT)
        model = generator.parse_script(SCRIPT)
        meson = (ROOT / 'meson.build').read_text()
        self.assertEqual(generator.meson_problems(manifest, meson), [])
        added = meson.replace("  'b_lto': false,\n", "  'b_lto': false,\n  'b_colorout': 'auto',\n", 1)
        self.assertTrue(any("'b_colorout'" in p and 'not in the manifest' in p for p in generator.meson_problems(manifest, added)))
        removed = meson.replace("  'b_lto': false,\n", '', 1)
        self.assertTrue(any('b_lto' in p and 'not asserted' in p for p in generator.meson_problems(manifest, removed)))
        reordered = meson.replace("  'b_lto': false,\n  'b_coverage': false,\n", "  'b_coverage': false,\n  'b_lto': false,\n", 1)
        self.assertTrue(any('order' in p for p in generator.meson_problems(manifest, reordered)))
        retemplated = meson.replace('only inspection and xpc are configurable', 'only inspection is configurable', 1)
        self.assertTrue(any('template' in p for p in generator.meson_problems(manifest, retemplated)))
        split = copy.deepcopy(manifest)
        family = next(r for r in split['refusals'] if r['kind'] == 'meson')
        family['asserts'] = family['asserts'][:-1]
        self.assertTrue(any('swift_link_args' in p and 'not in the manifest' in p for p in generator.meson_problems(split, meson)))
        makefile = (ROOT / 'Makefile').read_text()
        self.assertEqual(generator.makefile_problems(manifest, makefile), [])
        guardless = makefile.replace('\t@echo "==> [build] build, sign and embed evidence into $(DIST_DIR)/PolicyWitness.app"\n', '', 1)
        self.assertNotEqual(guardless, makefile)
        self.assertTrue(any('not printed' in p for p in generator.makefile_problems(manifest, guardless)))
        self.assertEqual(generator.inventory_problems(manifest, model, ROOT), [])
        root = self.checkout()
        artifact = root / 'tests/lib/artifact.py'
        artifact.write_text(self.mutated("'sbpl-check'", "'sbpl-check', 'extra-tool'", text=artifact.read_text()))
        self.assertTrue(any('EXECUTABLES lists' in p for p in generator.inventory_problems(manifest, model, root)))
        artifact.write_text((ROOT / 'tests/lib/artifact.py').read_text())
        evidence = root / 'tests/build-evidence.py'
        evidence.write_text(self.mutated('"sbpl-check",', '"sbpl-check",\n        "extra-tool",', text=evidence.read_text()))
        self.assertTrue(any('helper_names' in p for p in generator.inventory_problems(manifest, model, root)))
        evidence.write_text((ROOT / 'tests/build-evidence.py').read_text())
        readme = root / 'README.md'
        readme.write_text(readme.read_text().replace('  - `Contents/MacOS/sbpl-check`', '  - `Contents/MacOS/sbpl-checker`', 1))
        self.assertTrue(any("README 'Build and bundle'" in p for p in generator.inventory_problems(manifest, model, root)))
        baseline = generator.load_baseline(ROOT / generator.BASELINE_NAME)
        self.assertEqual(generator.baseline_problems(manifest, baseline), [])
        # A refusal whose only checks are textual must be listed; a listed refusal with a control must not be.
        uncovered = copy.deepcopy(manifest)
        first = uncovered['refusals'][0]
        first['checks'] = [c for c in first['checks'] if c['coverage'] == 'textual']
        self.assertEqual(generator.coverage(first), 'textual')
        self.assertTrue(any(f"refusal {first['id']} has no behavioral or helper control and is not listed" in p
                            for p in generator.baseline_problems(uncovered, baseline)))
        entry = dict(refusal=first['id'], variants=first['variants'], claim='a claim', control='a control')
        listed = {'schema_version': 1, 'entries': baseline['entries'] + [entry]}
        self.assertEqual(generator.baseline_problems(uncovered, listed), [])
        self.assertTrue(any(f"listed refusal {first['id']} is unknown or now has a control" in p
                            for p in generator.baseline_problems(manifest, listed)))
        variants = {'schema_version': 1, 'entries': baseline['entries'] + [dict(entry, variants=['full'] if first['variants'] != ['full'] else ['partial'])]}
        self.assertTrue(any('variants' in p and 'differ' in p for p in generator.baseline_problems(uncovered, variants)))
        with self.assertRaises(ValueError):
            generator.load_baseline(root / 'docs/build.json')

    def test_rule_table_gates_on_the_banner_rule(self):
        """The banner row runs first. When it reports, or cannot parse its inputs, the nine other rows are blocked
        by it and never called; once it is clean, a later row's input failure blocks that row alone."""
        spec = importlib.util.spec_from_file_location('build_rules_gate', ROOT / 'tests/suites/source_drift/build_rules.py')
        rules = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rules)
        root = self.checkout()
        suffix = [rule.id for rule in rules.RULES if rule.id != rules.GATE]
        self.assertEqual(len(suffix), 9)

        def outcomes():
            return {result.rule_id: result for result in rules.run(rules.repository_tree.Tree(root))}

        def clean(results):
            return [rule_id for rule_id, result in results.items() if result.outcome != 'evaluated' or result.problems]

        self.assertEqual(clean(outcomes()), [])
        script = root / 'build.sh'
        original = script.read_text()
        reordered = SCRIPT.replace(
            'echo "==> Checking limits documentation"\n"${PW_PYTHON}" -B -S "${ROOT_DIR}/docs/generate_limits.py" --check\necho "==> Checking contract versions"',
            'echo "==> Checking contract versions"\n"${PW_PYTHON}" -B -S "${ROOT_DIR}/docs/generate_limits.py" --check\necho "==> Checking limits documentation"', 1)
        self.assertNotEqual(reordered, original)
        # The knob mutation must keep every cited symbol present, or the manifest load itself becomes the precondition.
        knob_changed = lambda text: text.replace('    0|1) ;;', '    0|1|2) ;;', 1)
        self.assertNotEqual(knob_changed(original), original)
        script.write_text(knob_changed(reordered))
        both = outcomes()
        self.assertEqual(both[rules.GATE].outcome, 'evaluated')
        self.assertTrue(any('banner order' in p.message for p in both[rules.GATE].problems), both[rules.GATE].problems)
        for name in suffix:
            self.assertEqual((both[name].outcome, both[name].blocked_by, both[name].problems), ('gate_blocked', rules.GATE, []), name)
        # A removed banner is also the manifest's cited symbol: the manifest load is a precondition failure of
        # the gate, and the rows behind it are still gate-blocked.
        script.write_text(self.mutated('echo "==> Compiling native executables"\n', ''))
        removed = outcomes()
        self.assertEqual((removed[rules.GATE].outcome, removed[rules.GATE].problems[0].key), ('input_blocked', 'manifest.invalid'))
        self.assertEqual({name: removed[name].outcome for name in suffix}, {name: 'gate_blocked' for name in suffix})
        script.write_text(knob_changed(original))
        banner_repaired = outcomes()
        self.assertEqual(banner_repaired[rules.GATE].problems, [])
        self.assertEqual([name for name in suffix if banner_repaired[name].outcome != 'evaluated'], [])
        self.assertTrue(any('knob BUILD_XPC: manifest values' in p.message for p in banner_repaired['knobs'].problems))
        self.assertEqual([name for name in suffix if name != 'knobs' and banner_repaired[name].problems], [])
        script.write_text(original)
        self.assertEqual(clean(outcomes()), [])
        script.write_text(self.mutated('usage() {\n', 'usage() {\n  echo "==> inside"\n'))
        unparsed = outcomes()
        self.assertEqual((unparsed[rules.GATE].outcome, unparsed[rules.GATE].problems[0].key), ('input_blocked', 'script.unparseable'))
        self.assertEqual({name: unparsed[name].outcome for name in suffix}, {name: 'gate_blocked' for name in suffix})
        script.write_text(original)
        baseline = root / generator.BASELINE_NAME
        baseline_text = baseline.read_text()
        baseline.write_text('{')
        later = outcomes()
        self.assertEqual(later[rules.GATE].outcome, 'evaluated')
        self.assertEqual((later['baseline'].outcome, later['baseline'].problems[0].key), ('input_blocked', 'baseline.invalid'))
        self.assertEqual([name for name in suffix if name != 'baseline' and later[name].outcome != 'evaluated'], [])
        baseline.write_text(baseline_text)
        self.assertEqual(clean(outcomes()), [])
        script.write_text(knob_changed(reordered))
        result = subprocess.run([sys.executable, '-B', '-S', str(ROOT / 'tests/suites/source_drift/build_rules.py'), '--root', str(root)],
                                cwd=root, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('check_knobs: not evaluated: blocked by check_banner_order', result.stderr)
        self.assertNotIn('knob BUILD_XPC', result.stderr)
        self.assertIn('gate_blocked: refusals, meson_assertions', result.stdout)
        script.write_text(original)

    def test_meson_policy_assertions_refuse_each_option(self):
        """Every option meson.build asserts: a configured directory accepts the changed value, and the regeneration
        the next compile triggers refuses it by name, before anything compiles. The label option is reached only
        through the effective options it is derived from."""
        other = {'optimization': '2', 'debug': 'true', 'warning_level': '1', 'werror': 'true', 'strip': 'true',
                 'unity': 'on', 'b_ndebug': 'true', 'b_lto': 'true', 'b_coverage': 'true', 'b_pgo': 'generate',
                 'b_bitcode': 'true', 'b_pie': 'true', 'b_staticpic': 'false', 'b_lundef': 'false',
                 'b_sanitize': 'address', 'c_std': 'c11', 'c_args': '-DPROBE=1',
                 'c_link_args': '-Wl,-headerpad_max_install_names', 'swift_args': '-DPROBE',
                 'swift_link_args': '-Xlinker -headerpad_max_install_names'}
        assertions = dict(generator.meson_assertions((ROOT / 'meson.build').read_text()))
        self.assertEqual(sorted(other), sorted(name for name in assertions if name != 'buildtype'))
        self.assertIn('buildtype', assertions)

        def poisoned(name, value, xpc):
            directory = tempfile.TemporaryDirectory(prefix='pw-meson-policy-')
            self.addCleanup(directory.cleanup)
            builddir = Path(directory.name) / 'builddir'
            setup = subprocess.run(['meson', 'setup', str(builddir), str(ROOT), f'-Dxpc={xpc}'], capture_output=True, text=True, timeout=300)
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)
            configure = subprocess.run(['meson', 'configure', str(builddir), f'-D{name}={value}'], capture_output=True, text=True, timeout=300)
            self.assertEqual(configure.returncode, 0, 'meson configure records the value; the assertion runs at the next regeneration')
            compile_ = subprocess.run(['meson', 'compile', '-C', str(builddir)], capture_output=True, text=True, timeout=300)
            self.assertNotEqual(compile_.returncode, 0, name)
            return compile_.stdout + compile_.stderr

        family = next(r for r in self.manifest['refusals'] if r['kind'] == 'meson')
        self.assertEqual(family['asserts'], list(assertions), 'the one manifest row lists every asserted option in order')
        for name, value in other.items():
            with self.subTest(option=name):
                output = poisoned(name, value, 'true' if name.startswith('swift') else 'false')
                self.assertIn(f'Assert failed: fixed native policy: {name} must be', output, output[-800:])
                self.assertIn('(got ', output)
                self.assertNotIn('Compiling C object', output)
        with self.subTest(option='buildtype'):
            output = poisoned('buildtype', 'debug', 'false')
            self.assertRegex(output, r'fixed native policy: (optimization|debug) must be')
            self.assertNotIn('fixed native policy: buildtype must be', output)

    def test_bypassing_one_meson_policy_assertion_fails_its_control(self):
        """The collapsed row stands for every option: with one assertion removed from meson.build, that option's control
        no longer refuses (the compile succeeds), and the grounding rule names the option the manifest still asserts."""
        directory = tempfile.TemporaryDirectory(prefix='pw-meson-bypass-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT)
        for name in set(names.decode().split('\0')) - {''}:
            source, target = ROOT / name, root / name
            if source.is_file() and (name.startswith(('controller/tools/', 'runner/Sources/', 'runner/Services/', 'runner/Clients/'))
                                     or name in ('meson.build', 'meson.options')):
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        meson = root / 'meson.build'
        text = meson.read_text()
        self.assertEqual(text.count("  'b_lto': false,\n"), 1)
        meson.write_text(text.replace("  'b_lto': false,\n", '', 1))
        builddir = root / 'builddir'
        setup = subprocess.run(['meson', 'setup', str(builddir), str(root), '-Dxpc=false'], capture_output=True, text=True, timeout=300)
        self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)
        configure = subprocess.run(['meson', 'configure', str(builddir), '-Db_lto=true'], capture_output=True, text=True, timeout=300)
        self.assertEqual(configure.returncode, 0, configure.stdout + configure.stderr)
        compile_ = subprocess.run(['meson', 'compile', '-C', str(builddir)], capture_output=True, text=True, timeout=600)
        self.assertEqual(compile_.returncode, 0, 'with the assertion removed the departing option is accepted: the control would fail here')
        self.assertNotIn('fixed native policy: b_lto', compile_.stdout + compile_.stderr)
        problems = generator.meson_problems(self.manifest, meson.read_text())
        self.assertTrue(any('b_lto' in p and 'not asserted' in p for p in problems), problems)

    def test_meson_output_target_assertion_refuses_other_hosts(self):
        """meson.build requires an arm64 macOS host machine. A cross file naming an x86_64 macOS host, the technique that
        produces such a configuration here, is refused at setup by name; a directory configured for x86_64 before the
        assertion existed is refused by the regeneration its next compile triggers, before anything compiles. With the
        assertion removed the x86_64 setup succeeds, so the control would fail, and the grounding rule names the missing
        assertion; a changed requirement is named too."""
        directory = tempfile.TemporaryDirectory(prefix='pw-meson-target-')
        self.addCleanup(directory.cleanup)
        work = Path(directory.name)
        cross = work / 'x86_64.ini'
        cross.write_text("[binaries]\nc = 'cc'\n[host_machine]\nsystem = 'darwin'\n"
                         "cpu_family = 'x86_64'\ncpu = 'x86_64'\nendian = 'little'\n")

        def setup(source, name):
            return subprocess.run(['meson', 'setup', str(work / name), str(source), '-Dxpc=false', '--cross-file', str(cross)],
                                  capture_output=True, text=True, timeout=300)
        message = 'Assert failed: output target: the native products are macOS arm64 code, but Meson is configured for host darwin x86_64\n'
        refused = setup(ROOT, 'x86_64')
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn(message, refused.stdout + refused.stderr)
        self.assertFalse((work / 'x86_64/build.ninja').exists(), 'a refused setup left a configured directory')
        # A copy of the native sources without the assertion: an x86_64 host configures, the rule names the missing row,
        # and restoring the assertion makes the next compile's regeneration refuse before anything compiles.
        source = work / 'source'
        names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT)
        for name in set(names.decode().split('\0')) - {''}:
            if (ROOT / name).is_file() and (name.startswith(('controller/tools/', 'runner/Sources/', 'runner/Services/', 'runner/Clients/'))
                                            or name in ('meson.build', 'meson.options')):
                (source / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, source / name)
        meson = source / 'meson.build'
        text = meson.read_text()
        start = text.index("assert(host_machine.system() == 'darwin'")
        end = text.index('host_machine.cpu_family()))\n', start) + len('host_machine.cpu_family()))\n')
        meson.write_text(text[:start] + text[end:])
        bypassed = setup(source, 'regenerated')
        self.assertEqual(bypassed.returncode, 0, 'with the assertion removed an x86_64 host configures: the control would fail here')
        self.assertTrue(any('output-target assertion' in p for p in generator.meson_problems(self.manifest, meson.read_text())))
        meson.write_text(text)
        regenerated = subprocess.run(['meson', 'compile', '-C', str(work / 'regenerated')], capture_output=True, text=True, timeout=300)
        self.assertNotEqual(regenerated.returncode, 0)
        self.assertIn(message, regenerated.stdout + regenerated.stderr)
        self.assertNotIn('Compiling C object', regenerated.stdout + regenerated.stderr)
        changed = text.replace("host_machine.cpu_family() == 'aarch64'", "host_machine.cpu_family() == 'x86_64'", 1)
        self.assertTrue(any('requires host' in p for p in generator.meson_problems(self.manifest, changed)))
        self.assertEqual(generator.meson_problems(self.manifest, text), [])

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
