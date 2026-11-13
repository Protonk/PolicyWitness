"""Verify public build identities, derived surface stamps and internal worker identity."""
import copy
import hashlib
import importlib.util
import json
import plistlib
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'lib'))
import abi_golden
import fixture_inputs

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'docs'))
sys.path.insert(0, str(ROOT / 'tests/lib'))
import receipts  # noqa: E402
identity_spec = importlib.util.spec_from_file_location('generate_worker_identity', ROOT / 'docs/generate_worker_identity.py')
identity_generator = importlib.util.module_from_spec(identity_spec)
identity_spec.loader.exec_module(identity_generator)
architecture_spec = importlib.util.spec_from_file_location('generate_architecture', ROOT / 'docs/generate_architecture.py')
architecture_generator = importlib.util.module_from_spec(architecture_spec)
architecture_spec.loader.exec_module(architecture_generator)

class WorkerIdentityTests(receipts.TestCase):
    def test_abi_layout_comparator_detects_size_and_format_changes(self):
        golden = (ROOT / 'tests/fixtures/contract/abi_layout.txt').read_text()
        self.assertEqual(abi_golden.compare(golden, golden), ('ok', ''))
        self.assertEqual(abi_golden.compare(golden, '')[0], 'missing_golden')
        size = abi_golden.parse(golden)['PW_SHM_HEADER_BYTES']
        changed = golden.replace(f'PW_SHM_HEADER_BYTES={size}', f'PW_SHM_HEADER_BYTES={int(size) + 8}', 1)
        status, detail = abi_golden.compare(changed, golden)
        self.assertEqual(status, 'update')
        self.assertIn('PW_SHM_HEADER_BYTES', detail)
        self.assertEqual(abi_golden.compare(golden + '\n', golden)[0], 'update')

    def checkout(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-identity-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        copied = fixture_inputs.copy_declared(ROOT, root, fixture_inputs.generator_inputs(ROOT, 'worker_identity'))
        print(f'fixture: {copied.files} files, {copied.bytes} bytes, {copied.seconds:.3f} s')
        self.track_inputs(root)
        return root

    def command(self, root, *args):
        if root == ROOT:
            self.track_inputs(root, fixture_inputs.generator_inputs(root, 'worker_identity'))
        return self.run_command([sys.executable, '-B', '-S', str(root / 'docs/generate_worker_identity.py'), *args],
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
            ('runner/Sources/PWRunnerCore/ActorSession.swift',
             'storeRelease(rawBase, offset: PWShmLayout.proceedOffset, ordinal)',
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

    def test_private_worker_owners_change_identity(self):
        changes = [
            ('pw_worker_timing.h', 'uint64_t raw = PW_CONTINUOUS_READ(stage);',
             'uint64_t raw = PW_CONTINUOUS_READ(stage) + 1;'),
            ('pw_worker_exec.h', 'POSIX_SPAWN_CLOEXEC_DEFAULT | POSIX_SPAWN_SETPGROUP',
             'POSIX_SPAWN_SETPGROUP'),
        ]
        for owner, old, new in changes:
            with self.subTest(owner=owner):
                root = self.checkout()
                expected = identity_generator.identity(root)
                path = root / 'controller/tools/pw_probe_runner' / owner
                text = path.read_text()
                self.assertEqual(text.count(old), 1)
                path.write_text(text.replace(old, new, 1))
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


class PublicBuildContractTests(receipts.TestCase):
    def test_source_copies_ignore_artifacts_and_release_checks_actual_bytes(self):
        import build_contract as contract
        root = self.checkout()
        expected = contract.identity(root)
        for name in ('controller/tools/sb_api_validator/sb_api_validator', 'controller/src/.DS_Store'):
            (root / name).write_bytes(b'incidental local bytes')
        self.assertEqual(contract.identity(root), expected)
        (root / '.gitignore').write_text('/controller/tools/sb_api_validator/sb_api_validator\n.DS_Store\n')
        self.git(root, 'init')
        self.commit(root)
        self.git(root, 'tag', '-a', 'v9.0.0', '-m', 'control')
        self.assertEqual(contract.identity(root), 'release:v9.0.0')
        source = root / 'controller/src/main.rs'
        self.git(root, 'update-index', '--assume-unchanged', 'controller/src/main.rs')
        source.write_bytes(source.read_bytes() + b'\n// hidden by the index flag\n')
        self.assertEqual(self.git(root, 'status', '--porcelain'), '')
        self.assertTrue(contract.identity(root).startswith('development:'))
        self.assertNotEqual(contract.identity(root), expected)

    def test_swift_context_refuses_a_different_compilation_identity(self):
        import build_contract
        import os
        root = self.checkout()
        for expected, status in ((build_contract.identity(root), 0), ('test:foreign', 1), ('', 1)):
            result = self.run_command([sys.executable, '-B', str(root / 'docs/build_contract.py'), '--swift-stdout'],
                env={**os.environ, 'PW_BUILD_CONTRACT': expected}, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, status, result.stderr)

    def checkout(self):
        import build_contract
        directory = tempfile.TemporaryDirectory(prefix='pw-public-contract-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        fixture_inputs.copy_declared(ROOT, root,
            build_contract.inputs(ROOT))
        self.track_inputs(root)
        return root

    def git(self, root, *args):
        result = self.run_command(['git', '-C', str(root), '-c', 'user.name=Contract control',
            '-c', 'user.email=contract@example.invalid', *args], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def commit(self, root, message='control'):
        self.git(root, 'add', '.')
        self.git(root, 'commit', '-m', message)

    def test_build_identity_tracks_shipped_inputs_and_requires_an_annotated_clean_release(self):
        import build_contract as contract
        root = self.checkout()
        loose = contract.identity(root)
        self.assertTrue(loose.startswith('development:'))
        self.git(root, 'init')
        self.commit(root)
        self.git(root, 'tag', 'v9.0.0')
        self.assertEqual(contract.identity(root), loose, 'lightweight tag is not a release')
        self.git(root, 'tag', '-d', 'v9.0.0')
        self.git(root, 'tag', '-a', 'v9.0.0', '-m', 'control')
        self.assertEqual(contract.identity(root), 'release:v9.0.0')
        (root / 'notes.md').write_text('documentation')
        self.assertEqual(contract.identity(root), loose, 'dirty release becomes development')
        self.commit(root)
        self.assertEqual(contract.identity(root), loose, 'documentation-only commit does not change source digest')
        previous = loose
        for name in ('controller/src/main.rs', 'runner/augments/mach-register.sb', 'PolicyWitness.entitlements',
                     'controller/src/lessons/create.json', 'controller/src/lessons/capture_typo.json'):
            path = root / name
            if not path.exists():
                path = next((root / 'runner/augments').glob('*.sb'))
            path.write_bytes(path.read_bytes() + b'\n')
            current = contract.identity(root)
            self.assertNotEqual(current, previous)
            previous = current
        source = root / 'controller/src/main.rs'
        source.unlink()
        source.symlink_to(root / 'controller/Cargo.toml')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            contract.identity(root)

    def test_out_of_checkout_environment_cannot_assert_a_release(self):
        import os
        import build_contract
        root = self.checkout()
        result = self.run_command([sys.executable, '-B', str(root / 'docs/build_contract.py')],
            env={**os.environ, 'PW_BUILD_CONTRACT': 'release:v9.9.9', 'PW_BUILD_VERSION': '9.9.9',
                 'PW_BUILD_DESCRIBE': 'v9.9.9'}, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), build_contract.identity(root))

    def test_presign_contract_guard_refuses_changed_sources(self):
        """Execute the script's exact guard with stable and changed source inputs."""
        import build_contract
        import os
        root = self.checkout()
        script = (ROOT / 'build.sh').read_text()
        start = script.index('CURRENT_BUILD_CONTRACT=')
        guard = script[start:script.index('\nfi', start) + 3]
        env = {**os.environ, 'ROOT_DIR': str(root), 'PW_PYTHON': sys.executable,
               'PW_BUILD_CONTRACT': build_contract.identity(root)}
        def run():
            return self.run_command(['/bin/bash', '-e', '-c', guard + '\nprintf reached'],
                env=env, capture_output=True, text=True, timeout=10)
        stable = run()
        self.assertEqual((stable.returncode, stable.stdout), (0, 'reached'), stable.stderr)
        path = root / 'controller/src/main.rs'
        path.write_text(path.read_text() + '\n// changed while compiling\n')
        changed = run()
        self.assertEqual(changed.returncode, 1)
        self.assertNotIn('reached', changed.stdout)
        self.assertIn('public build contract changed during compilation', changed.stderr)


class SurfaceStampTests(PublicBuildContractTests):
    def test_current_tree_has_complete_stamp_derivation(self):
        import generate_contract_stamps as stamps
        self.assertTrue(stamps.check(ROOT, require_history=True))

    def test_stamped_source_copy_and_no_tags_clone_validate_without_erasing_stamps(self):
        import generate_contract_stamps as stamps
        import shutil
        root = self.stamp_checkout()
        self.write_tables(root, 'v9.0.0')
        self.commit(root)
        self.git(root, 'tag', '-a', 'v9.0.0', '-m', 'control')
        self.assertTrue(stamps.check(root, require_history=True))
        for label in ('source-copy', 'no-tags'):
            target = root.parent / (root.name + '-' + label)
            self.addCleanup(shutil.rmtree, target)
            if label == 'no-tags':
                self.git(root, 'clone', '--no-tags', str(root), str(target))
            else:
                shutil.copytree(root, target, ignore=shutil.ignore_patterns('.git'))
            before = fixture_inputs.snapshot(target)
            self.assertFalse(stamps.check(target))
            with self.assertRaisesRegex(ValueError, 'history unavailable'):
                stamps.check(target, require_history=True)
            for proposed in (None, 'v9.0.1'):
                with self.assertRaisesRegex(ValueError, 'history unavailable'):
                    stamps.render(target, proposed)
            self.assertEqual(before, fixture_inputs.snapshot(target))

    def stamp_checkout(self):
        import generate_contract_stamps as stamps
        import contract_fixture
        directory = tempfile.TemporaryDirectory(prefix='pw-surface-stamps-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        fixture_inputs.copy_declared(ROOT, root, stamps.input_paths(ROOT))
        # An independent, unreferenced surface makes removal observable without
        # deleting meanings still required by a public record elsewhere.
        path = root / 'docs/contract/99-fixture_aux.surface.md'
        path.write_text('# Fixture-only surface {fixture_aux: surface}\n\n```contract\n'
                        'syntax: 1\nartifact: "Fixture"\npart: "definitions"\n'
                        'goldens: ["tests/fixtures/contract/surfaces/fixture_aux.json"]\n'
                        'checks: ["unit"]\n```\n\n'
                        '## Meaning {meaning: definition}\n\nFixture-only meaning.\n')
        (root / 'tests/fixtures/contract/surfaces/fixture_aux.json').write_text('{"records": {}}\n')
        contract_fixture.fresh_authoring(root, stamps)
        self.git(root, 'init')
        return root

    def write_tables(self, root, release=None):
        import generate_contract_stamps as stamps
        import contract_fixture
        contract_fixture.write_outputs(root, stamps.render(root, release, refresh_shapes=True))

    def replace(self, root, name, old, new):
        path = root / name
        before = path.read_text()
        self.assertIn(old, before, name)
        after = before.replace(old, new, 1)
        self.assertNotEqual(before, after)
        path.write_text(after)

    def release_fixture(self):
        root = self.stamp_checkout()
        self.write_tables(root, 'v9.0.0')
        self.commit(root)
        self.git(root, 'tag', '-a', 'v9.0.0', '-m', 'control')
        return root

    def test_pending_release_reproduces_after_tagging_and_tracks_removal(self):
        import generate_contract_stamps as stamps
        root = self.stamp_checkout()
        self.assertTrue(all(v['stamp'] == 'unreleased' for v in stamps.stamps(root).values()))
        self.write_tables(root, 'v9.0.0')
        self.commit(root)
        self.git(root, 'tag', '-a', 'v9.0.0', '-m', 'control')
        self.assertTrue(all(before == after for _, before, after in stamps.render(root)))
        # Reader guidance outside the guide table is not a second meaning source.
        guide = root / 'docs/PolicyWitness.md'
        guide.write_text(guide.read_text() + '\nFixture-only guide explanation.\n')
        self.assertTrue(all(v['stamp'] == 'v9.0.0' for v in stamps.stamps(root).values()))
        self.replace(root, 'docs/contract/99-fixture_aux.surface.md',
                     'Fixture-only meaning.', 'Changed fixture-only meaning.')
        values = stamps.stamps(root)
        self.assertEqual(values['fixture_aux']['stamp'], 'unreleased')
        self.assertEqual(values['profile']['stamp'], 'v9.0.0')
        (root / 'docs/contract/99-fixture_aux.surface.md').unlink()
        pending = stamps.stamps(root, 'v9.0.1')
        self.assertEqual(pending['fixture_aux']['stamp'], 'v9.0.1')
        self.assertTrue(pending['fixture_aux']['removed'])
        self.write_tables(root, 'v9.0.1')
        self.commit(root)
        self.git(root, 'tag', '-a', 'v9.0.1', '-m', 'control')
        self.assertTrue(all(before == after for _, before, after in stamps.render(root)))
        self.assertTrue(stamps.stamps(root)['fixture_aux']['removed'])

    def test_golden_change_moves_its_surface_and_malformed_region_refuses(self):
        import generate_contract_stamps as stamps
        root = self.release_fixture()
        path = root / 'tests/fixtures/contract/surfaces/profile.json'
        data = json.loads(path.read_text())
        data['fixture_added_shape'] = 'string'
        path.write_text(json.dumps(data))
        self.assertEqual(stamps.stamps(root)['profile']['stamp'], 'unreleased')
        with self.assertRaisesRegex(ValueError, 'stale surface shape goldens'):
            stamps.render(root)
        self.write_tables(root)
        self.replace(root, 'docs/contract/99-fixture_aux.surface.md',
                     '{fixture_aux: surface}', '{fixture_aux: unknown_kind}')
        with self.assertRaises(ValueError):
            stamps.render(root)

    def test_surface_ownership_and_collected_shapes_require_review(self):
        import generate_contract_stamps as stamps
        root = self.release_fixture()
        stamps.check_shapes(root)
        source = 'runner/Sources/PWRunnerCore/PWRunnerRequest.swift'
        original = (root / source).read_text()
        self.replace(root, source, 'case contract, specimen_id', 'case new_intent, contract, specimen_id')
        with self.assertRaisesRegex(ValueError, 'missing declared type'):
            stamps.check_shapes(root)
        (root / source).write_text(original)
        self.replace(root, 'docs/contract/99-fixture_aux.surface.md',
                     'checks: ["unit"]', 'checks: ["nonexistent_suite"]')
        with self.assertRaisesRegex(ValueError, 'unknown verification suite'):
            stamps.render(root)

    def test_reservation_and_selector_keys_move_the_surfaces_that_use_them(self):
        import generate_contract_stamps as stamps
        root = self.release_fixture()
        source = 'runner/Sources/PWRunnerCore/PWRunnerTransport.swift'
        original = (root / source).read_text()
        self.replace(root, source, 'case contract, attempt_id, lease_ms',
                     'case future_key, contract, attempt_id, lease_ms')
        # A new key without a declaration cannot be silently blessed by recollection.
        with self.assertRaisesRegex(ValueError, 'missing declared type'):
            stamps.check_shapes(root, refresh=True)
        (root / source).write_text(original)
        before = stamps.collected_shapes(root)
        self.replace(root, 'controller/src/runner_select.rs',
                     '&["id", "service", "required_entitlements", "mode"]',
                     '&["future_key", "id", "service", "required_entitlements", "mode"]')
        with self.assertRaisesRegex(ValueError, 'stale surface shape goldens'):
            stamps.check_shapes(root)
        after = stamps.collected_shapes(root)
        self.assertEqual({name for name in before if before[name] != after[name]},
                         {'tests/fixtures/contract/surfaces/request.json'})
        self.write_tables(root)
        stamps.check_shapes(root)
        self.assertEqual(stamps.stamps(root)['request']['stamp'], 'unreleased')

    def test_reservation_limits_and_host_wire_declarations_move_their_surfaces(self):
        import generate_contract_stamps as stamps
        import generate_porcelain
        mutations = [
            ('limit', name, None) for name in ('reservation_lease', 'reservation_rpc_wait',
                                             'reservation_attempts', 'reservation_retry_delay', 'client_rpc_wait')
        ] + [('wire', 'tag', 100), ('wire', 'swift_type', 'Int32')]
        for kind, key, replacement in mutations:
            with self.subTest(kind=kind, key=key):
                root = self.release_fixture()
                before = stamps.collected_shapes(root)
                path = root / ('docs/limits.json' if kind == 'limit' else 'docs/porcelain.json')
                data = json.loads(path.read_text())
                if kind == 'limit':
                    next(row for row in data['limits'] if row['id'] == key)['value'] += 1
                    expected = {'transport', 'installation'}
                else:
                    record = next(row for row in data['records'] if row['name'] == 'PWRunnerRunResult')
                    field = next(field for field in record['fields'] if field['name'] == 'rc')
                    self.assertNotEqual(field[key], replacement)
                    field[key] = replacement
                    record['fields'].sort(key=lambda field: field['tag'])
                    expected = {'wire'} if key == 'tag' else {'wire', 'reply'}
                path.write_text(json.dumps(data))
                if kind == 'wire':
                    # The schema and imported Swift declaration must agree before
                    # a field can supply a reviewed shape. This is source-only.
                    for name, content in generate_porcelain.outputs(root, data).items():
                        (root / name).write_text(content)
                with self.assertRaisesRegex(ValueError, 'stale surface shape goldens'):
                    stamps.check_shapes(root)
                after = stamps.collected_shapes(root)
                changed = {Path(name).stem for name in before if before[name] != after[name]}
                self.assertEqual(changed, expected)
                self.write_tables(root)
                stamps.check_shapes(root)
                self.assertTrue(expected <= {name for name, row in stamps.stamps(root).items()
                                             if row['stamp'] == 'unreleased'})


class ContractReaderControls(receipts.TestCase):
    def reader(self, name, root=ROOT):
        path = f'docs/contract/{name}.py'
        self.track_inputs(root, [path])
        spec = importlib.util.spec_from_file_location('contract_reader_' + name, root / path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def source_fixture(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-contract-reader-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        declared = fixture_inputs.generator_inputs(ROOT, 'contract_stamps')
        collector = self.reader('record_definitions')
        self.assertLessEqual(set(collector.input_paths(ROOT)), set(declared))
        fixture_inputs.copy_declared(ROOT, root, declared)
        self.track_inputs(root)
        return root

    def files_fixture(self, files):
        directory = tempfile.TemporaryDirectory(prefix='pw-contract-history-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        for name, value in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value)
        self.track_inputs(root)
        return root

    def replace_source(self, root, name, before, after):
        path = root / name
        original = path.read_text()
        self.assertIn(before, original, f'control has lost its source target: {name}')
        changed = original.replace(before, after, 1)
        self.assertNotEqual(changed, original, f'control did not change {name}')
        path.write_text(changed)
        self.evidence.capture_tracked('mutated reader input')


class RecordDefinitionTests(ContractReaderControls):
    def test_equipment_team_id_requires_a_key_and_accepts_json_null(self):
        root = self.source_fixture()
        reader = self.reader('record_definitions', root)
        records, _ = reader.load(root)
        record = records['ActorEquipmentManifest.Worker']
        field = record['fields']['team_id']
        self.assertTrue(field['required_key'])
        self.assertTrue(field['optional'])
        self.assertTrue(field['json_null'])
        self.assertEqual(reader.field_type(field), 'string')
        self.assertEqual(reader.field_presence(record, field), 'required; may be null')

        path = 'runner/Sources/PWRunnerCore/ActorEquipment.swift'
        guard = 'guard c.contains(.team_id) else { throw ActorEquipmentProblem("missing team_id") }'
        decode = 'team_id = try c.decodeIfPresent(String.self, forKey: .team_id)'
        for before, after in ((guard, ''),
                              (decode, decode.replace('decodeIfPresent', 'decode')),
                              (guard + '\n            ' + decode,
                               decode + '\n            ' + guard)):
            with self.subTest(decoder=after):
                changed_root = self.source_fixture()
                self.replace_source(changed_root, path, before, after)
                with self.assertRaisesRegex(ValueError, 'required-key nullable decoder needs review'):
                    self.reader('record_definitions', changed_root).load(changed_root)

    def test_declared_fixture_imports_public_roots_without_path_specific_duplicates(self):
        root = self.source_fixture()
        reader = self.reader('record_definitions', root)
        reads = set()

        def read(name):
            reads.add(name)
            return (root / name).read_text()

        swift = sorted(p.relative_to(root).as_posix()
                       for p in (root / 'runner/Sources/PWRunnerCore').glob('*.swift'))
        records, aliases = reader.load(root, read=read, swift_paths=swift)
        self.assertLessEqual(reads, set(reader.input_paths(root)))
        self.assertEqual(aliases['envelope'], 'rust.RunEnvelope')
        self.assertEqual(aliases['request'], 'PWRunnerRunSpec')
        self.assertEqual(records['rust.RunEnvelope']['fields']['data']['swift_type'], 'rust.RunData')
        self.assertEqual(records['rust.RunEnvelope']['fields']['build']['swift_type'], 'rust.BuildStamp')
        self.assertEqual(records['rust.HelperEnvelope']['fields']['build']['swift_type'], 'rust.BuildStamp')
        self.assertTrue(all(record['coverage_required'] for record in records.values()))
        self.assertFalse(any(name.startswith('shape.') for name in records))
        for name in ('rust.ExecutionData', 'rust.OutputCapture', 'rust.EvidenceEntry'):
            self.assertNotIn(name, records)
        with self.assertRaisesRegex(ValueError, 'own swift_paths'):
            reader.load(root, read=read)

    def test_public_projection_types_and_presence_follow_the_owners(self):
        root = self.source_fixture()
        reader = self.reader('record_definitions', root)
        records, _ = reader.load(root)
        expected = [
            ('ActorEquipmentManifest', 'worker_identity', 'string', 'as defined below'),
            ('ActorEquipmentManifest.Worker', 'sha256', 'string', 'as defined below'),
            ('PWRunnerControlReply', 'reason', 'string', 'omitted when absent'),
            ('rust.ServiceObservation', 'presence', 'string', 'required'),
            ('rust.RunnerRecord', 'contract', 'string', 'omitted when empty'),
            ('rust.CleanupReport', 'warnings', 'array of string', 'omitted when empty'),
            ('rust.PolicyCheckCapture', 'envelope', 'JSON value', 'null when absent'),
            ('PWRunnerAttemptPathDiagnostics', 'same_as_input', 'array of string', 'required'),
            ('PWRunnerAttemptPathDiagnostics', 'realpath_resolved', 'string',
             'omitted when named in same_as_input; otherwise present, possibly null'),
            ('PWRunnerEquipmentBinding', 'team_id', 'string',
             'present when identifier has a value; may be null'),
            ('rust.TransportCapture.Rejected', 'data_base64', 'string (base64)', 'required'),
        ]
        for name, key, expected_type, expected_presence in expected:
            with self.subTest(record=name, key=key):
                field = records[name]['fields'][key]
                self.assertEqual(reader.field_type(field), expected_type)
                self.assertEqual(reader.field_presence(records[name], field), expected_presence)
        self.assertNotIn('execObservationDecodeProblem', records['PWRunnerAttemptResult']['fields'])
        self.assertEqual(records['PWRunnerRunSpec']['fields']['probe_plan']['swift_type'], '[PWRunnerProbeStep]?')
        self.assertEqual(records['rust.RunnerClientRun']['fields']['runner_reply_error']['swift_type'], 'String?')
        self.assertEqual(records['rust.RunnerClientRun']['fields']['stdout_truncated']['swift_type'], 'Bool')
        self.assertNotIn('output', records['rust.RunnerClientRun']['fields'])
        self.assertEqual(records['rust.RunnerSignature']['additional_type'], 'JSON')
        self.assertTrue(records['rust.RunnerSignature']['open'])
        self.assertEqual(records['PWRunnerPhaseAction']['variants'],
                         {'probe': 'PWRunnerProbeStep', 'extensionAction': 'PWRunnerExtensionAction'})
        self.assertEqual(records['rust.TransportCapture']['variants'],
                         {'Typed': 'PWRunnerClientCapture', 'Rejected': 'rust.TransportCapture.Rejected'})
        self.assertEqual(records['PWDispositionValue']['variants'],
                         {'Integer': 'Int', 'Request': 'PWRunnerTerminationRequest'})
        for name in ('PWRunnerPhaseAction', 'rust.TransportCapture', 'rust.RequestFailureProjection'):
            self.assertEqual(records[name]['fields'], {})

    def test_reachable_source_additions_enter_coverage_and_unreachable_test_types_do_not(self):
        root = self.source_fixture()
        self.replace_source(root, 'controller/src/runner_commands.rs',
            'struct RunnerVerifyData {', 'struct RunnerVerifyData {\n    future_observation: bool,')
        path = root / 'controller/src/runner_commands.rs'
        path.write_text(path.read_text() + '\n#[cfg(test)]\n#[derive(Serialize)]\n'
                        'struct FixtureOnly {\n    ignored: FutureType,\n}\n'
                        '\n#[derive(Serialize)]\nstruct UnreachableControl {\n    ignored: FutureType,\n}\n')
        self.evidence.capture_tracked('reachable and test-only declarations')
        records, _ = self.reader('record_definitions', root).load(root)
        self.assertEqual(records['rust.RunnerVerifyData']['fields']['future_observation']['swift_type'], 'Bool')
        self.assertTrue(records['rust.RunnerVerifyData']['coverage_required'])
        self.assertNotIn('rust.FixtureOnly', records)
        self.assertNotIn('rust.UnreachableControl', records)

    def test_native_omission_change_changes_the_imported_presence(self):
        root = self.source_fixture()
        self.replace_source(root, 'controller/src/runner_manager.rs',
            '#[serde(default, skip_serializing_if = "String::is_empty")]', '#[serde(default)]')
        reader = self.reader('record_definitions', root)
        records, _ = reader.load(root)
        record = records['rust.RunnerRecord']
        self.assertEqual(reader.field_presence(record, record['fields']['contract']), 'required')

    def test_unreadable_or_unresolved_source_forms_refuse_instead_of_guessing(self):
        cases = [
            ('controller/src/runner_commands.rs', 'struct RunnerVerifyData {',
             'struct RunnerVerifyData {\n    future: FutureType,', 'unresolved type rust.FutureType'),
            ('controller/src/runner_commands.rs', 'struct RunnerVerifyData {',
             'struct RunnerVerifyData {\n    #[cfg(test)]\n    future: bool,', 'conditional field attributes'),
            ('controller/src/runner_commands.rs', 'struct RunnerVerifyData {',
             'struct RunnerVerifyData {\n    #[serde(serialize_with = "future")]\n    future: bool,', 'unsupported serde attribute'),
            ('controller/src/runner_client.rs', 'pub struct RunnerClientRun {',
             'pub struct RunnerClientRun {\n    pub stdout_truncated: bool,', 'colliding flattened fields'),
            ('controller/src/runner_client.rs', 'serialize_with = "serialize_rejected_bytes"',
             'serialize_with = "future_projection"', 'rejected-byte projection needs review'),
            ('controller/src/runner_manager.rs', 'pub extra: BTreeMap<String, Value>,',
             'pub extra: BTreeMap<u64, Value>,', 'unsupported JSON map key type'),
            ('runner/Sources/PWRunnerCore/PWRunnerRequest.swift', 'case contract, specimen_id',
             'case future, contract, specimen_id', 'missing declared type'),
            ('runner/Sources/PWRunnerCore/PWRunnerRequest.swift', 'case worker_executable_path, worker_timeout_ms',
             'case worker_timeout_ms', 'CodingKeys and porcelain field sets disagree'),
            ('runner/Sources/PWRunnerCore/PWRunnerRequest.swift', 'case probe(PWRunnerProbeStep)',
             'case empty\n    case probe(PWRunnerProbeStep)', 'alternative needs review'),
        ]
        for path, before, after, diagnostic in cases:
            with self.subTest(source=path, diagnostic=diagnostic):
                root = self.source_fixture()
                self.replace_source(root, path, before, after)
                with self.assertRaisesRegex(ValueError, diagnostic):
                    self.reader('record_definitions', root).load(root)

    def test_observed_golden_cannot_override_a_declared_type_or_add_a_field(self):
        for key, value, diagnostic in (
                ('generated_at_unix_ms', 'string', 'declared number'),
                ('fabricated_field', 'string', 'has no declared field')):
            with self.subTest(key=key):
                root = self.source_fixture()
                path = root / 'tests/fixtures/contract/envelope_shape.json'
                golden = json.loads(path.read_text())
                golden['shape']['envelope'][key] = value
                path.write_text(json.dumps(golden))
                self.evidence.capture_tracked('changed envelope shape')
                with self.assertRaisesRegex(ValueError, diagnostic):
                    self.reader('record_definitions', root).load(root)


class RetainedContractReaderTests(ContractReaderControls):
    def legacy_fixture(self):
        row = dict(id='request', artifact='Authored legacy control',
                   definition='docs/CONTRACT.md',
                   definitions=['docs/PolicyWitness.md#second', 'docs/PolicyWitness.md#first'],
                   goldens=['shapes/one.json', 'shapes/two.json'], checks=['source_drift'])
        return self.files_fixture({
            'docs/contract_surfaces.json': json.dumps({'surfaces': [row]}),
            'tests/catalog.json': json.dumps({'suites': {'source_drift': {}, 'unit': {}}}),
            'docs/CONTRACT.md': 'Outside.\n<!-- BEGIN CONTRACT request -->Alpha\n beta<!-- END CONTRACT request -->\nIgnored.',
            'docs/PolicyWitness.md': '<!-- BEGIN CONTRACT first -->first<!-- END CONTRACT first -->\n'
                                    '<!-- BEGIN CONTRACT second -->second<!-- END CONTRACT second -->',
            'shapes/one.json': '{"z":"é", "a":[2,1]}',
            'shapes/two.json': '{"value":7}',
        })

    def snapshot_fixture(self):
        return self.files_fixture({
            'docs/contract/public.json': json.dumps({
                'format': 'policywitness.contract.public.v1', 'history': ['v0.3.6'],
                'surfaces': [dict(id='request', artifact='Authored snapshot control',
                                  goldens=['shapes/one.json'],
                                  public={'entries': [{'id': 'a', 'text': 'Alpha'}]})]}),
            'shapes/one.json': '{"shape":{"x":"number"}}',
        })

    def test_legacy_framing_whitespace_and_golden_order_match_the_retained_format(self):
        reader = self.reader('history_v0')
        root = self.legacy_fixture()
        read = lambda name: (root / name).read_text()
        row, = reader.surfaces(read)
        # Independently spelled preimage pins the old payload framing, Unicode
        # escaping, object-key order, array order and supplementary-region order.
        expected = hashlib.sha256(
            b'["Alpha beta second first",[{"a":[2,1],"z":"\\u00e9"},{"value":7}]]').hexdigest()
        self.assertEqual(reader.surface_hash(read, row), expected)
        (root / 'shapes/one.json').write_text('{"a": [2, 1], "z": "\\u00e9"}')
        self.replace_source(root, 'docs/CONTRACT.md', 'Alpha\n beta', '\n Alpha\t beta \n')
        self.assertEqual(reader.surface_hash(read, row), expected)
        metadata = dict(row, artifact='Changed description', checks=['unit'])
        self.assertEqual(reader.surface_hash(read, metadata), expected)
        self.assertNotEqual(reader.surface_hash(read, dict(row, definitions=list(reversed(row['definitions'])))), expected)
        self.assertNotEqual(reader.surface_hash(read, dict(row, goldens=list(reversed(row['goldens'])))), expected)
        (root / 'shapes/one.json').write_text('{"a":[1,2],"z":"é"}')
        self.assertNotEqual(reader.surface_hash(read, row), expected)

    def test_legacy_manifest_and_region_refusals_remain_strict(self):
        reader = self.reader('history_v0')
        for change, diagnostic in (
                (lambda v: v.update(version=1), 'invalid contract surfaces manifest'),
                (lambda v: v['surfaces'][0].update(extra=True), 'invalid surface fields'),
                (lambda v: v['surfaces'].append(copy.deepcopy(v['surfaces'][0])), 'duplicate or invalid surface id'),
                (lambda v: v['surfaces'][0].update(goldens=[]), 'missing golden or verification'),
                (lambda v: v['surfaces'][0].update(checks=['missing']), 'unknown verification suite'),
                (lambda v: v['surfaces'][0].update(definition='../outside'), 'repository-relative')):
            with self.subTest(diagnostic=diagnostic):
                root = self.legacy_fixture()
                path = root / 'docs/contract_surfaces.json'
                value = json.loads(path.read_text())
                change(value)
                path.write_text(json.dumps(value))
                with self.assertRaisesRegex(ValueError, diagnostic):
                    reader.surfaces(lambda name: (root / name).read_text())
        for path, region in (('docs/CONTRACT.md', 'request'), ('docs/PolicyWitness.md', 'second')):
            for mode in ('missing', 'duplicate', 'reversed'):
                with self.subTest(path=path, mode=mode):
                    root = self.legacy_fixture()
                    read = lambda name: (root / name).read_text()
                    row, = reader.surfaces(read)
                    start, stop = f'<!-- BEGIN CONTRACT {region} -->', f'<!-- END CONTRACT {region} -->'
                    text = (root / path).read_text()
                    if mode == 'missing':
                        text = text.replace(stop, '')
                    elif mode == 'duplicate':
                        text += start
                    else:
                        text = text.replace(start, '@CONTROL@').replace(stop, start).replace('@CONTROL@', stop)
                    (root / path).write_text(text)
                    with self.assertRaisesRegex(ValueError, 'expected one ordered definition region'):
                        reader.surface_hash(read, row)

    def test_snapshot_framing_uses_released_public_content_and_own_goldens(self):
        reader = self.reader('history_v1')
        root = self.snapshot_fixture()
        read = lambda name: (root / name).read_text()
        row, = reader.surfaces(read)
        expected = hashlib.sha256(b'["policywitness.contract.public.v1",'
            b'{"entries":[{"id":"a","text":"Alpha"}]},[{"shape":{"x":"number"}}]]').hexdigest()
        self.assertEqual(reader.surface_hash(read, row), expected)
        self.assertEqual(reader.surface_hash(read, dict(row, artifact='Other metadata')), expected)
        snapshot_path = root / 'docs/contract/public.json'
        snapshot = json.loads(snapshot_path.read_text())
        snapshot['history'].append('v0.3.7')
        snapshot_path.write_text(json.dumps(snapshot))
        updated_row, = reader.surfaces(read)
        self.assertEqual(reader.surface_hash(read, updated_row), expected)
        (root / 'docs/contract/current-syntax-is-unreadable.md').write_text('Unrelated current authoring.')
        self.assertEqual(reader.surface_hash(read, row), expected)
        changed = copy.deepcopy(row)
        changed['public']['entries'][0]['text'] = 'Changed obligation'
        self.assertNotEqual(reader.surface_hash(read, changed), expected)
        (root / 'shapes/one.json').write_text('{"shape":{"x":"string"}}')
        self.assertNotEqual(reader.surface_hash(read, row), expected)

    def test_snapshot_rejects_unknown_format_missing_fields_and_invalid_history(self):
        reader = self.reader('history_v1')
        changes = [
            ('unknown format', lambda v: v.update(format='future-format')),
            ('extra top-level key', lambda v: v.update(extra=True)),
            ('missing history', lambda v: v.pop('history')),
            ('invalid history container', lambda v: v.update(history='v0.3.6')),
            ('duplicate historical tag', lambda v: v.update(history=['v0.3.6', 'v0.3.6'])),
            ('invalid historical tag', lambda v: v.update(history=['main'])),
            ('nontext historical tag', lambda v: v.update(history=[{}])),
            ('invalid surface container', lambda v: v.update(surfaces={})),
            ('extra row key', lambda v: v['surfaces'][0].update(extra=True)),
            ('duplicate id', lambda v: v['surfaces'].append(copy.deepcopy(v['surfaces'][0]))),
            ('invalid id', lambda v: v['surfaces'][0].update(id='Invalid-ID')),
            ('missing artifact', lambda v: v['surfaces'][0].update(artifact='')),
            ('empty public', lambda v: v['surfaces'][0].update(public={})),
            ('scalar public', lambda v: v['surfaces'][0].update(public='unstructured')),
        ]
        for label, change in changes:
            with self.subTest(control=label):
                root = self.snapshot_fixture()
                path = root / 'docs/contract/public.json'
                value = json.loads(path.read_text())
                change(value)
                path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    reader.surfaces(lambda name: (root / name).read_text())

    def test_snapshot_rejects_nontext_duplicate_and_nonrelative_golden_paths(self):
        reader = self.reader('history_v1')
        for goldens in ([], ['shapes/one.json', 'shapes/one.json'], [{}], [[]], [7],
                        ['/tmp/shape.json'], ['../shape.json'], ['.'], [''],
                        ['./shape.json'], ['shapes//one.json']):
            with self.subTest(goldens=goldens):
                root = self.snapshot_fixture()
                path = root / 'docs/contract/public.json'
                value = json.loads(path.read_text())
                value['surfaces'][0]['goldens'] = goldens
                path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    reader.surfaces(lambda name: (root / name).read_text())

    def test_missing_released_inputs_propagate_without_current_tree_fallback(self):
        for version, factory, missing in (
                ('history_v0', self.legacy_fixture, 'docs/contract_surfaces.json'),
                ('history_v0', self.legacy_fixture, 'tests/catalog.json'),
                ('history_v0', self.legacy_fixture, 'docs/CONTRACT.md'),
                ('history_v0', self.legacy_fixture, 'docs/PolicyWitness.md'),
                ('history_v0', self.legacy_fixture, 'shapes/one.json'),
                ('history_v1', self.snapshot_fixture, 'docs/contract/public.json'),
                ('history_v1', self.snapshot_fixture, 'shapes/one.json')):
            with self.subTest(version=version, missing=missing):
                reader = self.reader(version)
                root = factory()
                (root / missing).unlink()
                read = lambda name: (root / name).read_text()
                with self.assertRaises(FileNotFoundError):
                    for row in reader.surfaces(read):
                        reader.surface_hash(read, row)


from contract_tree_controls import ContractHistoryTests, ContractTreeTests  # noqa: E402


if __name__ == '__main__':
    sys.exit(receipts.timed_main(sys.modules[__name__], 'source_drift/build_contracts', 'build-contracts'))
