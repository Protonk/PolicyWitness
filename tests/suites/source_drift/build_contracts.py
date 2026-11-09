"""Verify public build identities, derived surface stamps and internal worker identity."""
import copy
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
        for name in ('controller/src/main.rs', 'runner/augments/mach-register.sb', 'PolicyWitness.entitlements'):
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
            before = {name: (target / name).read_bytes() for name in stamps.OUTPUTS}
            self.assertFalse(stamps.check(target))
            with self.assertRaisesRegex(ValueError, 'history unavailable'):
                stamps.check(target, require_history=True)
            with self.assertRaisesRegex(ValueError, 'history unavailable'):
                stamps.render(target)
            self.assertEqual(before, {name: (target / name).read_bytes() for name in before})

    def stamp_checkout(self):
        import generate_contract_stamps as stamps
        directory = tempfile.TemporaryDirectory(prefix='pw-surface-stamps-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        fixture_inputs.copy_declared(ROOT, root, stamps.input_paths(ROOT))
        self.git(root, 'init')
        return root

    def write_tables(self, root, release=None):
        import generate_contract_stamps as stamps
        for name, _, after in stamps.render(root, release):
            (root / name).write_text(after)

    def test_pending_release_reproduces_after_tagging_and_tracks_removal(self):
        import generate_contract_stamps as stamps
        root = self.stamp_checkout()
        self.assertTrue(all(v['stamp'] == 'unreleased' for v in stamps.stamps(root).values()))
        self.write_tables(root, 'v9.0.0')
        self.commit(root)
        self.git(root, 'tag', '-a', 'v9.0.0', '-m', 'control')
        self.assertTrue(all(before == after for _, before, after in stamps.render(root)))
        path = root / 'docs/CONTRACT.md'
        path.write_text(path.read_text() + '\nExplanatory text outside the definitions.\n')
        self.assertTrue(all(v['stamp'] == 'v9.0.0' for v in stamps.stamps(root).values()))
        path.write_text(path.read_text().replace('<!-- BEGIN CONTRACT request -->',
            '<!-- BEGIN CONTRACT request -->\nA changed normative example.'))
        values = stamps.stamps(root)
        self.assertEqual(values['request']['stamp'], 'unreleased')
        self.assertEqual(values['profile']['stamp'], 'v9.0.0')
        manifest = root / stamps.MANIFEST
        data = json.loads(manifest.read_text())
        data['surfaces'] = [r for r in data['surfaces'] if r['id'] != 'profile']
        manifest.write_text(json.dumps(data))
        pending = stamps.stamps(root, 'v9.0.1')
        self.assertEqual(pending['profile']['stamp'], 'v9.0.1')
        self.assertTrue(pending['profile']['removed'])
        self.write_tables(root, 'v9.0.1')
        self.commit(root)
        self.git(root, 'tag', '-a', 'v9.0.1', '-m', 'control')
        self.assertTrue(all(before == after for _, before, after in stamps.render(root)))
        self.assertTrue(stamps.stamps(root)['profile']['removed'])

    def test_golden_change_moves_its_surface_and_malformed_region_refuses(self):
        import generate_contract_stamps as stamps
        root = self.stamp_checkout()
        self.write_tables(root, 'v9.0.0')
        self.commit(root)
        self.git(root, 'tag', '-a', 'v9.0.0', '-m', 'control')
        path = root / 'tests/fixtures/contract/surfaces/profile.json'
        data = json.loads(path.read_text())
        data['shape']['reply.compiled_profile']['added'] = 'string'
        path.write_text(json.dumps(data))
        self.assertEqual(stamps.stamps(root)['profile']['stamp'], 'unreleased')
        path = root / 'docs/CONTRACT.md'
        path.write_text(path.read_text().replace('<!-- END CONTRACT profile -->', ''))
        with self.assertRaisesRegex(ValueError, 'ordered definition'):
            stamps.render(root)

    def test_surface_ownership_and_collected_shapes_require_review(self):
        import generate_contract_stamps as stamps
        root = self.stamp_checkout()
        self.write_tables(root, 'v9.0.0')
        self.commit(root)
        self.git(root, 'tag', '-a', 'v9.0.0', '-m', 'control')
        stamps.check_shapes(root)
        source = root / 'runner/Sources/PWRunnerCore/PWRunnerRequest.swift'
        source.write_text(source.read_text().replace('case contract, specimen_id', 'case new_intent, contract, specimen_id'))
        with self.assertRaisesRegex(ValueError, 'stale surface shape goldens'):
            stamps.check_shapes(root)
        stamps.check_shapes(root, refresh=True)
        stamps.check_shapes(root)
        path = root / stamps.MANIFEST
        data = json.loads(path.read_text())
        data['surfaces'][0]['checks'] = ['nonexistent_suite']
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'unknown verification suite'):
            stamps.render(root)

    def test_reservation_and_selector_keys_move_the_surfaces_that_use_them(self):
        import generate_contract_stamps as stamps
        for filename, old, new, expected in (
            ('runner/Sources/PWRunnerCore/PWRunnerTransport.swift',
             'case contract, attempt_id, lease_ms', 'case future_key, contract, attempt_id, lease_ms',
             {'transport', 'installation'}),
            ('controller/src/runner_select.rs',
             '&["id", "service", "required_entitlements", "mode"]',
             '&["future_key", "id", "service", "required_entitlements", "mode"]', {'request'}),
        ):
            with self.subTest(source=filename):
                root = self.stamp_checkout()
                self.write_tables(root, 'v9.0.0')
                self.commit(root)
                self.git(root, 'tag', '-a', 'v9.0.0', '-m', 'control')
                path = root / filename
                self.assertIn(old, path.read_text())
                path.write_text(path.read_text().replace(old, new))
                with self.assertRaisesRegex(ValueError, 'stale surface shape goldens'):
                    stamps.check_shapes(root)
                stamps.check_shapes(root, refresh=True)
                changed = {name for name, row in stamps.stamps(root).items() if row['stamp'] == 'unreleased'}
                self.assertEqual(changed, expected)

    def test_reservation_limits_and_host_wire_declarations_move_their_surfaces(self):
        import generate_contract_stamps as stamps
        mutations = [
            ('limit', name, None) for name in ('reservation_lease', 'reservation_rpc_wait',
                                             'reservation_attempts', 'reservation_retry_delay', 'client_rpc_wait')
        ] + [('wire', 'tag', 100), ('wire', 'swift_type', 'Int32')]
        for kind, key, replacement in mutations:
            with self.subTest(kind=kind, key=key):
                root = self.stamp_checkout()
                self.write_tables(root, 'v9.0.0')
                self.commit(root)
                self.git(root, 'tag', '-a', 'v9.0.0', '-m', 'control')
                path = root / ('docs/limits.json' if kind == 'limit' else 'docs/porcelain.json')
                data = json.loads(path.read_text())
                if kind == 'limit':
                    next(row for row in data['limits'] if row['id'] == key)['value'] += 1
                    expected = {'transport', 'installation'}
                else:
                    record = next(row for row in data['records'] if row['name'] == 'PWRunnerRunResult')
                    next(field for field in record['fields'] if field['name'] == 'rc')[key] = replacement
                    record['fields'].sort(key=lambda field: field['tag'])
                    expected = {'transport'}
                path.write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, 'stale surface shape goldens'):
                    stamps.check_shapes(root)
                stamps.check_shapes(root, refresh=True)
                changed = {name for name, row in stamps.stamps(root).items() if row['stamp'] == 'unreleased'}
                self.assertEqual(changed, expected)


if __name__ == '__main__':
    sys.exit(receipts.timed_main(sys.modules[__name__], 'source_drift/build_contracts', 'build-contracts'))
