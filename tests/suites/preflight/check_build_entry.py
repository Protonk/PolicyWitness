"""Build entry controls: the unchanged build script refuses each early fault before the step it protects, offline.

Every control runs `build.sh` or `make` in a disposable checkout built from the declared inputs of the steps it
reaches, with no signed app and no identity supplied; it asserts the refusal, the banners that did and did not
print, and that no output or lock was created. The builder check uses a nested sandbox profile and the real
`sysctl`; the identity controls query the real keychain for an identity it does not hold. A receipt per control
records its elapsed time under the artifacts directory when one is given.
"""
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'docs'))
import fixture_inputs  # noqa: E402
import markdown_reader  # noqa: E402
import shim_probe  # noqa: E402


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f'docs/{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generator = load('generate_contract')
identity_generator = load('generate_worker_identity')
limits_generator = load('generate_limits')
# The build's environment: the knobs and an inherited lock claim never leak into a control build.
BUILD_ENV_EXCLUDED = ('BUILD_XPC', 'PW_INSPECTION', 'PW_FRESH_BUILD', 'PW_CHECKOUT_LOCK_FD', 'PW_CHECKOUT_LOCK_ROOT',
                      'PW_CHECKOUT_LOCK_NONCE', 'PW_CHECKOUT_LOCK_CHANNEL')
ENTRY_FILES = set(fixture_inputs.build_entry_inputs(ROOT))
LIMITS_FILES = ENTRY_FILES | set(fixture_inputs.generator_inputs(ROOT, 'limits'))
RECEIPTS = []


class BuildEntryTests(unittest.TestCase):
    def setUp(self):
        self.versions = generator.load_versions(ROOT / 'docs/contract.json')
        self.started = time.perf_counter()

    def tearDown(self):
        RECEIPTS.append(dict(test=self.id().split('.')[-1], elapsed_seconds=time.perf_counter() - self.started))

    def checkout(self, extra=()):
        directory = tempfile.TemporaryDirectory(prefix='pw-build-entry-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        copied = fixture_inputs.copy_declared(ROOT, root, fixture_inputs.generator_inputs(ROOT, 'contract'), extra=extra)
        print(f'fixture: {copied.files} files, {copied.bytes} bytes, {copied.seconds:.3f} s')
        return root

    def build_checkout(self):
        """A checkout in which every check before the signing identity passes."""
        extra = (LIMITS_FILES | set(fixture_inputs.generator_inputs(ROOT, 'architecture'))
                 | set(fixture_inputs.generator_inputs(ROOT, 'build')) | set(fixture_inputs.build_script_inputs(ROOT))
                 | set(fixture_inputs.generator_inputs(ROOT, 'worker_identity')) | {'Info.plist', 'meson.build', 'meson.options'})
        return self.checkout(extra=extra)

    def build(self, root, env, timeout=120, args=()):
        """Run build.sh in a checkout with the knobs unset unless env sets them; return the result and the output path."""
        destination = root / 'dist'
        base = {name: value for name, value in os.environ.items() if name not in BUILD_ENV_EXCLUDED}
        result = subprocess.run(['bash', str(root / 'build.sh'), *args], cwd=root,
                                env={**base, 'DIST_DIR': str(destination), **env}, capture_output=True, text=True, timeout=timeout)
        return result, destination

    def stale_copy(self, root, rel):
        """Rewrite one target's first region with the next version numbers."""
        start, end, render = generator.TARGETS[rel][0]
        path = root / rel
        text = path.read_text()
        stale = generator.replace_block(text, start, end, render({k: v + 1 for k, v in self.versions.items()}))
        self.assertNotEqual(stale, text, rel)
        path.write_text(stale)

    def test_build_refuses_an_identity_of_another_class_as_absent_before_cargo(self):
        """Every check before the identity step passes in the checkout; an identity the keychain does not list stops the
        build, whatever its class. The class itself is established on the signatures after the seal, not here."""
        root = self.build_checkout()
        for identity in ('Apple Development: Nobody (TEAMID00AA)', 'Mac Developer: Nobody (TEAMID00AA)', '-'):
            with self.subTest(identity=identity):
                result, destination = self.build(root, {'IDENTITY': identity})
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn('Verifying the checkout lock', result.stdout)
                self.assertIn('Checking host/worker identity', result.stdout)
                self.assertIn('Build stamp', result.stdout)
                self.assertIn('Selecting the macOS SDK', result.stdout)
                self.assertIn('Checking the native build directory', result.stdout)
                self.assertIn('codesigning identity not found in your keychain', result.stderr)
                self.assertNotIn('must name a Developer ID Application identity', result.stderr)
                self.assertNotIn('Admitting the Cargo', result.stdout)
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
        self.assertIn('stale tests/lib/contract.py; run tests/lib/python.sh docs/generate_worker_identity.py', result.stderr)
        self.assertNotIn('Build stamp', result.stdout)
        self.assertNotIn('Building Rust', result.stdout)
        self.assertEqual({name: (root / name).read_bytes() for name in before}, before)
        self.assertFalse(destination.exists())
        self.assertFalse((root / 'builddir').exists())

    def test_build_refuses_an_unexecutable_interpreter_before_any_python(self):
        root = self.checkout(extra=ENTRY_FILES)
        profile = root / 'resolver.sb'
        profile.write_text('(version 1)(allow default)(deny mach-lookup)(deny process-exec)'
                           '(allow process-exec (literal "/bin/bash") (literal "/usr/sbin/sysctl") (literal "/usr/bin/dirname"))')
        env = {k: v for k, v in os.environ.items() if k not in BUILD_ENV_EXCLUDED}
        env.update(SDKROOT='', PW_PYTHON='/usr/bin/false')
        result = subprocess.run(['/usr/bin/sandbox-exec', '-f', str(profile), '/bin/bash', str(root / 'build.sh')],
                                cwd=root, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('direct Python unavailable', result.stderr)
        self.assertIn('/opt/homebrew/opt/python@3.14/bin/python3.14', result.stderr)
        self.assertFalse(shim_probe.installation_requests(result.stdout, result.stderr))
        self.assertFalse((root / 'tests/.checkout.lock').exists())
        self.assertFalse((root / 'controller/target').exists())
        self.assertFalse((root / 'dist').exists())

    def test_build_refuses_a_builder_it_cannot_confirm_before_anything_else(self):
        """The native builder check is the script's first executable block, built from shell builtins and the two absolute
        sysctl probes, ahead of the knobs, the arguments, the tracked inputs, Python and SDK setup and the lock front end.
        A profile lets only bash and sysctl execute and denies Mach lookups: with hw.optional.arm64 unreadable, a bad knob,
        an unknown argument and an invalid SDKROOT, the builder refusal is the only output, so nothing it precedes ran.
        Without the unreadable read the same native shell passes the check and meets the knob refusal. A probe the profile
        forbids to execute (status 126) still reaches the diagnostic, both probes named, rather than exiting under set -e."""
        text = (ROOT / 'build.sh').read_text()
        body = text.split('set -euo pipefail\n', 1)[1]
        guard = body[:body.index('\nROOT_DIR=')]
        code = [line.strip() for line in guard.splitlines() if line.strip() and not line.lstrip().startswith('#')]
        self.assertTrue(code and code[0].startswith('if NATIVE_ARM64="$(/usr/sbin/sysctl -n hw.optional.arm64)"'), code[:1])
        self.assertEqual(set(re.findall(r'(?<![\w$])/[\w./-]+', '\n'.join(code))), {'/usr/sbin/sysctl'}, code)
        for later in ('for knob in BUILD_XPC', 'usage() {', 'for tree_input in', 'source "${ROOT_DIR}/tests/lib/python_start.sh"',
                      'exec /bin/bash "${ROOT_DIR}/tests/lib/checkout_lock.sh"'):
            self.assertNotIn(later, guard)
            self.assertIn(later, body)
        root = self.checkout(extra=ENTRY_FILES)
        rules = '(version 1)(allow default)(deny mach-lookup)(deny process-exec)(allow process-exec (literal "/bin/bash") (literal "/usr/sbin/sysctl"))'
        env = {k: v for k, v in os.environ.items() if k not in BUILD_ENV_EXCLUDED}
        env.update(BUILD_XPC='2', SDKROOT=str(root / 'missing.sdk'), IDENTITY='')

        def run(profile, *args):
            path = root / 'native.sb'
            path.write_text(profile)
            return subprocess.run(['/usr/bin/sandbox-exec', '-f', str(path), '/bin/bash', str(root / 'build.sh'), *args],
                                  cwd=root, env=env, capture_output=True, text=True, timeout=30)
        refused = run(rules + shim_probe.UNREADABLE_ARM64, '--bogus')
        self.assertEqual(refused.returncode, 2, refused.stdout + refused.stderr)
        self.assertEqual((refused.stdout, refused.stderr),
                         ('', 'ERROR: this build runs only natively on Apple Silicon (hw.optional.arm64=<empty>, sysctl.proc_translated=0)\n'))
        native = run(rules)
        self.assertEqual(native.returncode, 2, native.stdout + native.stderr)
        self.assertIn("BUILD_XPC must be 0 or 1 (got '2')", native.stderr)
        self.assertNotIn('runs only natively', native.stderr)
        failed = run('(version 1)(allow default)(deny mach-lookup)(deny process-exec (literal "/usr/sbin/sysctl"))')
        self.assertEqual(failed.returncode, 2, failed.stdout + failed.stderr)
        self.assertIn('ERROR: this build runs only natively on Apple Silicon (hw.optional.arm64=<failed: status 126>, '
                      'sysctl.proc_translated=<failed: status 126>)', failed.stderr)
        self.assertEqual(failed.stdout, '')
        for path in ('tests/.checkout.lock', 'controller/target', 'dist'):
            self.assertFalse((root / path).exists(), path)

    def test_build_refuses_a_knob_value_other_than_0_or_1_before_any_check(self):
        root = self.checkout(extra=ENTRY_FILES)
        for knob in ('BUILD_XPC', 'PW_INSPECTION', 'PW_FRESH_BUILD'):
            for value in ('', '2', ' 1', 'true'):
                with self.subTest(knob=knob, value=value):
                    result, destination = self.build(root, {knob: value, 'IDENTITY': ''}, timeout=10)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn(f"{knob} must be 0 or 1 (got '{value}')", result.stderr)
                    self.assertNotIn('Verifying the checkout lock', result.stdout)
                    self.assertNotIn('Checking limits documentation', result.stdout)
                    self.assertFalse(destination.exists())
                    self.assertFalse((root / 'tests/.checkout.lock').exists(), 'a refused knob must not take the lock')
        # Unset, 0 and 1 pass the gate: the lock is taken and verified, then the first documentation check runs.
        for env in ({}, {'BUILD_XPC': '0', 'PW_INSPECTION': '0', 'PW_FRESH_BUILD': '0'}, {'BUILD_XPC': '1', 'PW_INSPECTION': '1', 'PW_FRESH_BUILD': '1'}):
            with self.subTest(env=env):
                result, _ = self.build(root, {**env, 'IDENTITY': ''}, timeout=10)
                self.assertIn('Verifying the checkout lock', result.stdout)
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
        # The same record naming this checkout passes the source gate; a configured directory
        # without a toolchain stamp is then refused rather than adopted, still before the identity.
        info.write_text(json.dumps({'directories': {'source': str(root)}}))
        result, _ = self.build(root, {'IDENTITY': ''})
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('has no pw-toolchain.json', result.stderr)
        self.assertNotIn('IDENTITY is not set', result.stderr)
        # Fresh mode replaces the directory instead of validating it: the next refusal is the identity's.
        result, _ = self.build(root, {'IDENTITY': '', 'PW_FRESH_BUILD': '1'})
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('fresh mode: the directory is replaced after admission', result.stdout)
        self.assertIn('IDENTITY is not set', result.stderr)
        self.assertTrue((builddir / 'build.ninja').exists(), 'admission before the identity removes nothing')
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
        self.assertIn(node, [row[0].text for table in markdown_reader.parse(text).tables for row in table.rows])
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
        self.assertIn('admission', [row[0].text for table in markdown_reader.parse(text).tables for row in table.rows])
        document.write_text(text.replace('| admission |', '| admissionx |', 1))
        result, destination = self.build(root, {'IDENTITY': ''})
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('build documentation is stale', result.stderr)
        self.assertIn('Checking build documentation', result.stdout)
        self.assertNotIn('Checking host/worker identity', result.stdout)
        self.assertFalse(destination.exists())

    def test_make_default_and_help_print_the_header_without_running_other_targets(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-make-help-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        makefile = root / 'Makefile'
        (root / 'tests/lib').mkdir(parents=True)
        shutil.copy2(ROOT / 'tests/lib/sdk_guard.sh', root / 'tests/lib/sdk_guard.sh')
        text = (ROOT / 'Makefile').read_text()
        self.assertIn('Operator entry points', text, 'the header mutation must change its input')
        env = {name: value for name, value in os.environ.items()
               if name not in ('MAKEFLAGS', 'MFLAGS', 'MAKEOVERRIDES', 'MAKELEVEL', 'APPLY')}
        env.update(IDENTITY='Developer ID Application: Control (TEAMID00AA)', NOTARY_KEYCHAIN_PROFILE='control')
        for name in ('build.sh', 'tests/run.sh'):
            script = root / name
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text('#!/bin/sh\ntouch unexpected-target\nexit 97\n')
            script.chmod(0o755)
        for header in (text, text.replace('Operator entry points', 'Edited operator entry points', 1)):
            makefile.write_text(header)
            lines = []
            for line in header.splitlines():
                if not line.startswith('#'):
                    break
                lines.append(line[2:] if line.startswith('# ') else line[1:])
            expected = '\n'.join(lines) + '\n'
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            for args in ([], ['help']):
                result = subprocess.run(['make', *args], cwd=root, env=env, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout, expected)
                self.assertEqual(result.stderr, '')
                self.assertEqual({p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}, before)

    def test_make_build_runs_the_script_which_names_the_make_invocation_in_its_identity_refusal(self):
        """After SDK admission, make build runs build.sh with IDENTITY, DIST_DIR and, only when the caller set it,
        PW_FRESH_BUILD. The script's identity refusal names the make invocation to use."""
        directory = tempfile.TemporaryDirectory(prefix='pw-make-build-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        shutil.copy2(ROOT / 'Makefile', root / 'Makefile')
        (root / 'tests/lib').mkdir(parents=True)
        shutil.copy2(ROOT / 'tests/lib/sdk_guard.sh', root / 'tests/lib/sdk_guard.sh')
        marker = root / 'ran.json'
        script = root / 'build.sh'
        script.write_text('#!/usr/bin/env bash\nprintf \'{"IDENTITY": "%s", "DIST_DIR": "%s", "PW_FRESH_BUILD": "%s"}\' "${IDENTITY:-}" "${DIST_DIR:-}" "${PW_FRESH_BUILD-unset}" > ran.json\n')
        script.chmod(0o755)
        # make release exports command-line assignments through MAKEFLAGS as
        # well as individual variables; removing IDENTITY alone is insufficient.
        env = {name: value for name, value in os.environ.items()
               if name not in ('IDENTITY', 'PW_FRESH_BUILD', 'MAKEFLAGS', 'MFLAGS', 'MAKEOVERRIDES', 'MAKELEVEL')}
        result = subprocess.run(['make', 'build'], cwd=root, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('==> [build] build, sign and embed evidence into dist/PolicyWitness.app', result.stdout)
        self.assertEqual(json.loads(marker.read_text()), {'IDENTITY': '', 'DIST_DIR': 'dist', 'PW_FRESH_BUILD': 'unset'})
        identity = 'Developer ID Application: Control (TEAMID00AA)'
        result = subprocess.run(['make', 'build', f'IDENTITY={identity}', 'DIST_DIR=out', 'PW_FRESH_BUILD=1'], cwd=root, env=env,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(marker.read_text()), {'IDENTITY': identity, 'DIST_DIR': 'out', 'PW_FRESH_BUILD': '1'})
        # The real script's refusal names the make invocation: no identity at all stops it before Cargo.
        real = self.build_checkout()
        result, destination = self.build(real, {'IDENTITY': ''})
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("make build IDENTITY='Developer ID Application:", result.stderr)
        self.assertNotIn('Building Rust', result.stdout)
        self.assertFalse(destination.exists())

    def test_build_refuses_stale_contract_copy_before_signing_or_creating_output(self):
        root = self.checkout(extra=LIMITS_FILES)
        self.stale_copy(root, 'controller/src/json_contract.rs')
        destination = root / 'dist'
        result = subprocess.run(['bash', str(root / 'build.sh')], cwd=root,
                                env={**{k: v for k, v in os.environ.items() if k not in BUILD_ENV_EXCLUDED}, 'IDENTITY': '', 'DIST_DIR': str(destination)},
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('Checking limits documentation', result.stdout)
        self.assertIn('stale controller/src/json_contract.rs', result.stderr)
        self.assertFalse(destination.exists())

    def test_build_refuses_stale_guide_before_signing_or_creating_output(self):
        """A stale copied guide stops the build at its first documentation check, before anything is created."""
        root = self.checkout(extra=LIMITS_FILES)
        path = root / 'docs/PolicyWitness.md'
        self.assertIn('262,143', path.read_text())
        path.write_text(path.read_text().replace('262,143', '262,144', 1))
        destination = root / 'dist'
        result = subprocess.run(['bash', str(root / 'build.sh')], cwd=root,
                                env={**{k: v for k, v in os.environ.items() if k not in BUILD_ENV_EXCLUDED}, 'IDENTITY': '', 'DIST_DIR': str(destination)},
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('stale PolicyWitness.md', result.stderr)
        self.assertFalse(destination.exists())


def main(argv):
    artifacts = Path(argv[1]) if len(argv) > 1 else None
    result = unittest.main(argv=argv[:1], exit=False, verbosity=2).result
    if artifacts is not None:
        artifacts.mkdir(parents=True, exist_ok=True)
        (artifacts / 'receipts.json').write_text(json.dumps(dict(schema_version=1, case='preflight/build_entry_controls',
                                                                 mode='build-script', ok=result.wasSuccessful(), controls=RECEIPTS),
                                                            indent=2) + '\n')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
