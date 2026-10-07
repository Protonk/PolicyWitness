"""Guard the contract version manifest, its generated copies and the generator."""
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
                'docs/QUESTIONS.md', 'docs/ARCHITECTURE.md', 'build.sh', 'tests/FAILURE-PROPAGATION-CONTRACT.md',
                'tests/fixtures/comparison/matrix.json'}


def limits_references():
    manifest = json.loads((ROOT / 'docs/limits.json').read_text())
    return {ref['path'] for row in manifest['limits'] for key in ('sources', 'checks') for ref in row[key]}


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

    def test_build_refuses_stale_contract_copy_before_signing_or_creating_output(self):
        root = self.checkout(extra=LIMITS_FILES | limits_references())
        self.stale_copy(root, 'controller/src/json_contract.rs')
        destination = root / 'dist'
        result = subprocess.run(['bash', str(root / 'build.sh')], cwd=root,
            env={**os.environ, 'IDENTITY': '', 'YOLO': '', 'DIST_DIR': str(destination)},
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
