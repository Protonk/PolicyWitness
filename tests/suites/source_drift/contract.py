"""Guard the contract version manifest, its generated copies and the generator."""
import copy
import importlib.util
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import abi_golden

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('generate_contract', ROOT / 'docs/generate_contract.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
identity_spec = importlib.util.spec_from_file_location('generate_worker_identity', ROOT / 'docs/generate_worker_identity.py')
identity_generator = importlib.util.module_from_spec(identity_spec)
identity_spec.loader.exec_module(identity_generator)

# build.sh checks the limits documents first; a build checkout needs their inputs.
LIMITS_FILES = {'docs/generator_common.py', 'tests/catalog.json', 'docs/generate_limits.py', 'docs/limits.json', 'docs/LIMITS.md', 'docs/PolicyWitness.md',
                'docs/QUESTIONS.md', 'docs/ARCHITECTURE.md', 'docs/REQUEST-GRAMMAR.md', 'build.sh', 'tests/FAILURE-PROPAGATION-CONTRACT.md',
                'tests/fixtures/comparison/matrix.json'}


def limits_references():
    manifest = json.loads((ROOT / 'docs/limits.json').read_text())
    return {ref['path'] for row in manifest['limits'] for key in ('sources', 'checks') for ref in row[key]}


def build_references():
    """Everything the build generator's check reads: its manifest, script inputs, inventories, baseline, copies and every cited file."""
    manifest = json.loads((ROOT / 'docs/build.json').read_text())
    paths = {'docs/generate_build.py', 'docs/build.json', 'docs/BUILD.md', 'docs/build-steps.dot', 'docs/build-steps.svg',
             'tests/fixtures/docs/build_baseline.json', 'build.sh', 'meson.build', 'Makefile', 'README.md', 'Info.plist',
             'runner/Services/PWRunner/Info.plist', 'tests/lib/artifact.py', 'tests/build-evidence.py'}
    for group in ('steps', 'refusals', 'signing', 'invocations', 'knobs', 'directories'):
        for item in manifest[group]:
            paths.update(ref['path'] for key in ('sources', 'checks') for ref in item[key])
    return paths


def architecture_references():
    """Everything the architecture check reads: the manifest, its generator, the document, the figures and every cited file."""
    manifest = json.loads((ROOT / 'docs/architecture.json').read_text())
    paths = {'docs/architecture.json', 'docs/generate_architecture.py', manifest['document']}
    for graph in manifest['graphs']:
        paths |= {f"docs/{graph['file']}.dot", f"docs/{graph['file']}.svg"}
        for item in graph['nodes'] + graph['edges']:
            paths |= {ref['path'] for key in ('sources', 'checks') for ref in item[key]}
    return paths


class ContractVersionTests(unittest.TestCase):
    def setUp(self):
        self.manifest_path = ROOT / 'docs/contract.json'
        self.manifest = json.loads(self.manifest_path.read_text())
        self.versions = generator.load_versions(self.manifest_path)
        self.targets = list(generator.TARGETS)

    def checkout(self, extra=()):
        directory = tempfile.TemporaryDirectory(prefix='pw-contract-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        for name in {'docs/generate_contract.py', 'docs/contract.json', *self.targets, *extra}:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        return root

    def command(self, root, *args):
        return subprocess.run([sys.executable, '-B', str(root / 'docs/generate_contract.py'), *args],
                              cwd=root, capture_output=True, text=True, timeout=10)

    def snapshot(self, root):
        return {rel: (root / rel).read_bytes() for rel in self.targets}

    @staticmethod
    def body(text, start, end):
        return text.split(start, 1)[1].split(end, 1)[0].strip('\n')

    @staticmethod
    def outside(text, regions):
        for start, end, _ in regions:
            begin, finish = generator.block_bounds(text, start, end)
            text = text[:begin] + text[finish:]
        return text

    def stale_copy(self, root, rel):
        """Rewrite one target's first region with the next version numbers."""
        start, end, render = generator.TARGETS[rel][0]
        path = root / rel
        text = path.read_text()
        stale = generator.replace_block(text, start, end, render({k: v + 1 for k, v in self.versions.items()}))
        self.assertNotEqual(stale, text, rel)
        path.write_text(stale)

    def test_every_generated_copy_is_current(self):
        for rel, before, after in generator.render_all(ROOT, self.versions):
            self.assertEqual(before, after, rel)
        result = self.command(ROOT, '--check')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('all generated copies current', result.stdout)

    def test_python_constants_match_manifest(self):
        module_spec = importlib.util.spec_from_file_location('pw_contract', ROOT / 'tests/lib/contract.py')
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        self.assertEqual({'request_schema': module.REQUEST_SCHEMA, 'response_schema': module.RESPONSE_SCHEMA,
                          'controller_envelope': module.CONTROLLER_ENVELOPE},
                         self.manifest['versions'])

    def test_copies_table_names_generated_symbols_with_their_values(self):
        for key, copies in generator.COPIES.items():
            for path, symbol in copies:
                self.assertIn(path, generator.TARGETS, (key, path))
                text = (ROOT / path).read_text()
                name = symbol.rsplit('.', 1)[-1]
                pattern = re.compile(r'\b' + re.escape(name) + r'\b[^\n]*?\b' + str(self.versions[key]) + r'u?\b')
                self.assertTrue(any(pattern.search(self.body(text, s, e)) for s, e, _ in generator.TARGETS[path]),
                                (key, path, symbol))

    def test_generation_updates_every_copy_then_is_idempotent(self):
        root = self.checkout()
        data = copy.deepcopy(self.manifest)
        for offset, key in enumerate(generator.KEYS, start=10):
            data['versions'][key] += offset
        (root / 'docs/contract.json').write_text(json.dumps(data, indent=2) + '\n')
        result = self.command(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        new = generator.load_versions(root / 'docs/contract.json')
        for rel, regions in generator.TARGETS.items():
            text = (root / rel).read_text()
            for start, end, render in regions:
                self.assertEqual(self.body(text, start, end), render(new), rel)
            self.assertEqual(self.outside(text, regions), self.outside((ROOT / rel).read_text(), regions), rel)
        before = self.snapshot(root)
        self.assertEqual(self.command(root).returncode, 0)
        self.assertEqual(self.snapshot(root), before)
        result = self.command(root, '--check')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_check_refuses_each_stale_copy_without_writing_and_generation_repairs_it(self):
        for rel in self.targets:
            with self.subTest(rel=rel):
                root = self.checkout()
                self.stale_copy(root, rel)
                before = self.snapshot(root)
                result = self.command(root, '--check')
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('stale ' + rel, result.stderr)
                self.assertEqual(self.snapshot(root), before)
                result = self.command(root)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.snapshot(root), self.snapshot(ROOT))

    def test_broken_markers_stop_generation_before_any_write(self):
        for rel in self.targets:
            start, end, _ = generator.TARGETS[rel][0]
            mutations = (
                ('missing_end', lambda t: t.replace(end, '', 1)),
                ('duplicate_start', lambda t: t + '\n' + start + '\n'),
                ('reversed', lambda t: t.replace(start, '', 1).replace(end, end + '\n' + start, 1)),
            )
            for label, mutate in mutations:
                with self.subTest(rel=rel, mutation=label):
                    root = self.checkout()
                    (root / rel).write_text(mutate((root / rel).read_text()))
                    self.stale_copy(root, next(r for r in self.targets if r != rel))
                    before = self.snapshot(root)
                    for args in ((), ('--check',)):
                        result = self.command(root, *args)
                        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                        self.assertIn('exactly one ordered block', result.stderr)
                        self.assertEqual(self.snapshot(root), before)

    def test_manifest_rejects_invalid_shapes_and_the_command_writes_nothing(self):
        mutations = [
            ('missing key', lambda d: d['versions'].pop('response_schema')),
            ('extra key', lambda d: d['versions'].update(extra=1)),
            ('string', lambda d: d['versions'].update(response_schema='8')),
            ('zero', lambda d: d['versions'].update(response_schema=0)),
            ('boolean', lambda d: d['versions'].update(response_schema=True)),
            ('manifest version', lambda d: d.update(schema_version=2)),
            ('top-level extra', lambda d: d.update(extra=1)),
            ('not an object', lambda d: d.update(versions=[1, 8, 7, 1])),
        ]
        for label, mutate in mutations:
            with self.subTest(mutation=label):
                data = copy.deepcopy(self.manifest)
                mutate(data)
                with tempfile.TemporaryDirectory(prefix='pw-contract-manifest-') as directory:
                    path = Path(directory) / 'contract.json'
                    path.write_text(json.dumps(data))
                    with self.assertRaises(ValueError):
                        generator.load_versions(path)
        with self.assertRaises(ValueError):
            json.loads('{"a":1,"a":2}', object_pairs_hook=generator.unique_object)
        root = self.checkout()
        data = copy.deepcopy(self.manifest)
        data['versions']['response_schema'] = 'eight'
        (root / 'docs/contract.json').write_text(json.dumps(data))
        self.stale_copy(root, self.targets[0])
        before = self.snapshot(root)
        for args in ((), ('--check',)):
            result = self.command(root, *args)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('positive integer', result.stderr)
            self.assertEqual(self.snapshot(root), before)

    def test_abi_layout_golden_is_current_and_comparison_classifies_changes(self):
        golden = (ROOT / 'tests/fixtures/contract/abi_layout.txt').read_text()
        self.assertEqual(abi_golden.compare(golden, golden), ('ok', ''))
        self.assertEqual(abi_golden.compare(golden, '')[0], 'missing_golden')
        values = abi_golden.parse(golden)
        size = values['PW_SHM_HEADER_BYTES']
        moved = golden.replace(f'PW_SHM_HEADER_BYTES={size}', f'PW_SHM_HEADER_BYTES={int(size) + 8}', 1)
        status, detail = abi_golden.compare(moved, golden)
        self.assertEqual(status, 'update')
        self.assertIn('PW_SHM_HEADER_BYTES', detail)
        self.assertEqual(abi_golden.compare(golden + '\n', golden)[0], 'update')

    def test_reply_shape_golden_records_the_manifest_version(self):
        golden = json.loads((ROOT / 'tests/fixtures/contract/response_shape.json').read_text())
        self.assertEqual(golden['response_schema'], self.versions['response_schema'])
        self.assertIn('reply', golden['shape'])
        self.assertEqual(golden['shape']['reply']['schema_version'], 'number')

    def build_checkout(self):
        """A checkout in which every check before the signing identity passes."""
        extra = LIMITS_FILES | limits_references() | architecture_references() | build_references() | {'Info.plist', 'meson.build', 'meson.options'}
        extra |= set(identity_generator.source_paths(ROOT)) | set(identity_generator.TARGETS)
        return self.checkout(extra=extra)

    def build(self, root, env, timeout=120, args=()):
        """Run build.sh in a checkout with the knobs unset unless env sets them; return the result and the output path."""
        destination = root / 'dist'
        base = {name: value for name, value in os.environ.items() if name not in ('BUILD_XPC', 'PW_INSPECTION')}
        result = subprocess.run(['bash', str(root / 'build.sh'), *args], cwd=root,
            env={**base, 'DIST_DIR': str(destination), **env}, capture_output=True, text=True, timeout=timeout)
        return result, destination

    def test_build_refuses_a_non_developer_id_identity_before_cargo(self):
        """Every check before the identity step passes in the checkout; the identity class stops the build."""
        root = self.build_checkout()
        for identity in ('Apple Development: Nobody (TEAMID00AA)', 'Mac Developer: Nobody (TEAMID00AA)', '-'):
            with self.subTest(identity=identity):
                result, destination = self.build(root, {'IDENTITY': identity})
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn('Checking host/worker identity', result.stdout)
                self.assertIn('Build stamp', result.stdout)
                self.assertIn('Selecting the macOS SDK', result.stdout)
                self.assertIn('must name a Developer ID Application identity', result.stderr)
                self.assertNotIn('Building Rust', result.stdout)
                self.assertFalse(destination.exists())
                self.assertFalse((root / 'builddir').exists())

    def test_build_refuses_a_stale_identity_copy_before_compiling_and_writes_nothing(self):
        """A committed stale copy is refused with the regenerating command; the build repairs nothing itself."""
        root = self.build_checkout()
        target = root / 'tests/lib/contract.py'
        value = identity_generator.identity(root)
        self.assertIn(value, target.read_text())
        target.write_text(target.read_text().replace(value, '0' * 64))
        before = {name: (root / name).read_bytes() for name in identity_generator.TARGETS}
        result, destination = self.build(root, {'IDENTITY': ''})
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('Checking host/worker identity', result.stdout)
        self.assertIn('stale tests/lib/contract.py; run python3 docs/generate_worker_identity.py', result.stderr)
        self.assertNotIn('Build stamp', result.stdout)
        self.assertNotIn('Building Rust', result.stdout)
        self.assertEqual({name: (root / name).read_bytes() for name in before}, before)
        self.assertFalse(destination.exists())
        self.assertFalse((root / 'builddir').exists())

    def test_build_refuses_a_knob_value_other_than_0_or_1_before_any_check(self):
        root = self.checkout(extra={'build.sh'})
        for knob in ('BUILD_XPC', 'PW_INSPECTION'):
            for value in ('', '2', ' 1', 'true'):
                with self.subTest(knob=knob, value=value):
                    result, destination = self.build(root, {knob: value, 'IDENTITY': ''}, timeout=10)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn(f"{knob} must be 0 or 1 (got '{value}')", result.stderr)
                    self.assertNotIn('Checking limits documentation', result.stdout)
                    self.assertFalse(destination.exists())
        # Unset, 0 and 1 pass the gate: the first documentation check runs next.
        for env in ({}, {'BUILD_XPC': '0', 'PW_INSPECTION': '0'}, {'BUILD_XPC': '1', 'PW_INSPECTION': '1'}):
            with self.subTest(env=env):
                result, _ = self.build(root, {**env, 'IDENTITY': ''}, timeout=10)
                self.assertIn('Checking limits documentation', result.stdout)

    def test_build_refuses_a_build_directory_configured_for_another_checkout_before_cargo(self):
        """Meson keeps compiling the directory a build directory was set up for; the script compares before Cargo."""
        root = self.build_checkout()
        builddir = root / 'builddir'
        (builddir / 'meson-info').mkdir(parents=True)
        (builddir / 'build.ninja').write_text('# control\n')
        other = tempfile.TemporaryDirectory(prefix='pw-other-checkout-')
        self.addCleanup(other.cleanup)
        info = builddir / 'meson-info/meson-info.json'
        info.write_text(json.dumps({'directories': {'source': other.name}}))
        result, destination = self.build(root, {'IDENTITY': ''})
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('Selecting the macOS SDK', result.stdout)
        self.assertIn(f'is configured for {os.path.realpath(other.name)}, not this checkout', result.stderr)
        self.assertNotIn('IDENTITY is not set', result.stderr)
        self.assertNotIn('Building Rust', result.stdout)
        self.assertFalse(destination.exists())
        # The same record naming this checkout passes the gate; the next refusal is the identity's.
        info.write_text(json.dumps({'directories': {'source': str(root)}}))
        result, _ = self.build(root, {'IDENTITY': ''})
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('IDENTITY is not set', result.stderr)
        # A configured directory whose record cannot be read is refused too.
        info.unlink()
        result, _ = self.build(root, {'IDENTITY': ''})
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('has no readable meson-info', result.stderr)

    def test_build_refuses_an_unknown_argument_before_any_check(self):
        root = self.checkout(extra={'build.sh'})
        result, destination = self.build(root, {'IDENTITY': ''}, timeout=10, args=('--bogus',))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('unknown argument: --bogus', result.stderr)
        self.assertIn('usage:', result.stderr)
        self.assertNotIn('Checking limits documentation', result.stdout)
        self.assertFalse(destination.exists())
        # The one accepted argument prints the usage and stops before any check.
        result, _ = self.build(root, {'IDENTITY': ''}, timeout=10, args=('--help',))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('usage:', result.stdout)
        self.assertNotIn('Checking limits documentation', result.stdout)

    def test_build_refuses_a_malformed_plist_minimum_after_its_banner_and_before_the_sdk(self):
        root = self.build_checkout()
        plist = root / 'Info.plist'
        data = plistlib.loads(plist.read_bytes())
        data['LSMinimumSystemVersion'] = '26'
        plist.write_bytes(plistlib.dumps(data))
        result, destination = self.build(root, {'IDENTITY': ''})
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("Info.plist LSMinimumSystemVersion is not a major.minor version: '26'", result.stderr)
        self.assertIn('Supported macOS (Info.plist LSMinimumSystemVersion): 26', result.stdout)
        self.assertNotIn('Selecting the macOS SDK', result.stdout)
        self.assertFalse(destination.exists())

    def test_build_refuses_a_developer_id_identity_the_keychain_lacks_before_cargo(self):
        root = self.build_checkout()
        result, destination = self.build(root, {'IDENTITY': 'Developer ID Application: Nobody (TEAMID00AA)'})
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('codesigning identity not found in your keychain', result.stderr)
        self.assertIn('Checking the signing identity', result.stdout)
        self.assertNotIn('Building Rust', result.stdout)
        self.assertFalse(destination.exists())
        self.assertFalse((root / 'builddir').exists())

    def test_build_refuses_a_stale_architecture_copy_before_compiling(self):
        root = self.build_checkout()
        document = root / 'docs/ARCHITECTURE.md'
        node = json.loads((ROOT / 'docs/architecture.json').read_text())['graphs'][0]['nodes'][0]['id']
        text = document.read_text()
        self.assertIn(f'| {node} |', text)
        document.write_text(text.replace(f'| {node} |', f'| {node}x |', 1))
        result, destination = self.build(root, {'IDENTITY': ''})
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('architecture documentation is stale', result.stderr)
        self.assertIn('Checking contract versions', result.stdout)
        self.assertNotIn('Checking build documentation', result.stdout)
        self.assertFalse(destination.exists())

    def test_build_refuses_a_stale_build_document_copy_before_compiling(self):
        root = self.build_checkout()
        document = root / 'docs/BUILD.md'
        text = document.read_text()
        self.assertIn('| admission |', text)
        document.write_text(text.replace('| admission |', '| admissionx |', 1))
        result, destination = self.build(root, {'IDENTITY': ''})
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('build documentation is stale', result.stderr)
        self.assertIn('Checking build documentation', result.stdout)
        self.assertNotIn('Checking host/worker identity', result.stdout)
        self.assertFalse(destination.exists())

    def test_make_build_refuses_without_an_identity_and_never_runs_the_script(self):
        """The Makefile's guard stops before build.sh; with an identity the recipe passes it and DIST_DIR through."""
        directory = tempfile.TemporaryDirectory(prefix='pw-make-build-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        shutil.copy2(ROOT / 'Makefile', root / 'Makefile')
        marker = root / 'ran.json'
        script = root / 'build.sh'
        script.write_text('#!/usr/bin/env bash\nprintf \'{"IDENTITY": "%s", "DIST_DIR": "%s"}\' "${IDENTITY:-}" "${DIST_DIR:-}" > ran.json\n')
        script.chmod(0o755)
        env = {name: value for name, value in os.environ.items() if name != 'IDENTITY'}
        result = subprocess.run(['make', 'build'], cwd=root, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('ERROR: set IDENTITY to your Developer ID Application identity', result.stdout)
        self.assertFalse(marker.exists(), 'the guard must stop before build.sh runs')
        identity = 'Developer ID Application: Control (TEAMID00AA)'
        result = subprocess.run(['make', 'build', f'IDENTITY={identity}', 'DIST_DIR=out'], cwd=root, env=env,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('==> [build] build, sign and embed evidence into out/PolicyWitness.app', result.stdout)
        self.assertEqual(json.loads(marker.read_text()), {'IDENTITY': identity, 'DIST_DIR': 'out'})

    def test_build_refuses_stale_contract_copy_before_signing_or_creating_output(self):
        root = self.checkout(extra=LIMITS_FILES | limits_references())
        self.stale_copy(root, 'controller/src/json_contract.rs')
        destination = root / 'dist'
        result = subprocess.run(['bash', str(root / 'build.sh')], cwd=root,
            env={**os.environ, 'IDENTITY': '', 'DIST_DIR': str(destination)},
            capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('Checking limits documentation', result.stdout)
        self.assertIn('stale controller/src/json_contract.rs', result.stderr)
        self.assertFalse(destination.exists())


class WorkerIdentityTests(unittest.TestCase):
    def checkout(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-identity-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        for name in {*identity_generator.source_paths(ROOT), *identity_generator.TARGETS}:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        return root

    def command(self, root, *args):
        return subprocess.run([sys.executable, '-B', str(root / 'docs/generate_worker_identity.py'), *args],
                              cwd=root, capture_output=True, text=True, timeout=10)

    def test_identity_is_current_relocatable_and_regeneration_is_idempotent(self):
        root = self.checkout()
        expected = identity_generator.identity(ROOT)
        self.assertEqual(identity_generator.identity(root), expected)
        self.assertRegex(expected, r'^[0-9a-f]{64}$')
        result = self.command(root, '--check')
        self.assertEqual(result.returncode, 0, result.stderr)
        before = {name: (root / name).read_bytes() for name in identity_generator.TARGETS}
        self.assertEqual(self.command(root).returncode, 0)
        self.assertEqual(before, {name: (root / name).read_bytes() for name in before})

    def test_layout_and_both_handshake_implementations_change_identity(self):
        changes = [
            ('controller/tools/pw_probe_runner/pw_probe_runner_abi.h',
             '#define PW_SHM_MAX_STEPS    256u', '#define PW_SHM_MAX_STEPS    257u'),
            ('controller/tools/pw_probe_runner/pw_probe_runner.c',
             'atomic_load_explicit(&hdr->proceed, memory_order_acquire)',
             'atomic_load_explicit(&hdr->proceed, memory_order_relaxed)'),
            ('runner/Sources/PWRunnerCore/CWorker.swift',
             'storeRelease(rawBase, offset: PWShmLayout.proceedOffset, 1)',
             'storeRelease(rawBase, offset: PWShmLayout.proceedOffset, 0)'),
        ]
        for name, old, new in changes:
            with self.subTest(source=name):
                root = self.checkout()
                expected = identity_generator.identity(root)
                path = root / name
                self.assertIn(old, path.read_text())
                path.write_text(path.read_text().replace(old, new))
                changed = identity_generator.identity(root)
                self.assertNotEqual(changed, expected)
                self.assertEqual(self.command(root, '--check').returncode, 1)
                self.assertEqual(self.command(root).returncode, 0)
                self.assertEqual(self.command(root, '--check').returncode, 0)
                self.assertEqual(identity_generator.identity(root), changed)
                for target in identity_generator.TARGETS:
                    self.assertIn(changed, (root / target).read_text())

    def test_native_manifest_inputs_change_identity(self):
        for name in ('meson.build', 'meson.options'):
            with self.subTest(source=name):
                self.assertIn(name, identity_generator.SOURCE_FILES)
                root = self.checkout()
                expected = identity_generator.identity(root)
                path = root / name
                path.write_text(path.read_text() + '\n# a comment changes the identity\n')
                self.assertNotEqual(identity_generator.identity(root), expected)
                self.assertEqual(self.command(root, '--check').returncode, 1)
                self.assertEqual(self.command(root).returncode, 0)
                self.assertEqual(self.command(root, '--check').returncode, 0)

    def test_symlinks_under_identity_sources_are_refused(self):
        for label, make in (('directory', lambda link: link.symlink_to('../../../outside')),
                            ('file', lambda link: link.symlink_to('../../../outside/helper.h'))):
            with self.subTest(symlink=label):
                root = self.checkout()
                (root / 'outside').mkdir()
                (root / 'outside/helper.h').write_text('#define OUTSIDE 1\n')
                link = root / 'controller/tools/pw_probe_runner/link.h' if label == 'file' else root / 'controller/tools/pw_probe_runner/link'
                make(link)
                with self.assertRaises(ValueError):
                    identity_generator.identity(root)
                result = self.command(root, '--check')
                self.assertEqual(result.returncode, 1)
                self.assertIn('symlink under identity sources: controller/tools/pw_probe_runner/link', result.stderr)
                result = self.command(root)
                self.assertEqual(result.returncode, 1)

    def test_new_protocol_helpers_are_discovered_but_tests_are_not_identity_inputs(self):
        root = self.checkout()
        expected = identity_generator.identity(root)
        test = root / 'runner/Tests/new.swift'
        test.parent.mkdir(parents=True, exist_ok=True)
        test.write_text('// test only\n')
        self.assertEqual(identity_generator.identity(root), expected)
        helper = root / 'controller/tools/pw_probe_runner/new_helper.h'
        helper.write_text('#define NEW_PROTOCOL_DETAIL 1\n')
        added = identity_generator.identity(root)
        self.assertNotEqual(added, expected)
        helper.rename(helper.with_name('renamed_helper.h'))
        self.assertNotEqual(identity_generator.identity(root), added)

    def test_stale_generated_value_is_detected_and_repaired_without_changing_identity(self):
        root = self.checkout()
        expected = identity_generator.identity(root)
        header = root / identity_generator.TARGETS[0]
        header.write_text(header.read_text().replace(expected, '0' * 64))
        self.assertEqual(identity_generator.identity(root), expected)
        self.assertEqual(self.command(root, '--check').returncode, 1)
        self.assertEqual(self.command(root).returncode, 0)
        self.assertEqual(self.command(root, '--check').returncode, 0)

    def test_missing_marker_refuses_without_partial_writes(self):
        root = self.checkout()
        target = root / identity_generator.TARGETS[-1]
        target.write_text(target.read_text().replace(identity_generator.END, 'broken marker'))
        before = {name: (root / name).read_bytes() for name in identity_generator.TARGETS}
        result = self.command(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn('exactly one ordered', result.stderr)
        self.assertEqual(before, {name: (root / name).read_bytes() for name in before})


if __name__ == '__main__':
    unittest.main()
