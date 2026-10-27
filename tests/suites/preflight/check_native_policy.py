"""Native policy controls: meson.build's fixed policy assertions and output-target assertion refuse what they say.

Every asserted option is poisoned in turn in a configured directory of the real checkout, and the regeneration the
next compile triggers must refuse it by name before anything compiles; with one assertion removed from a copy of
the native sources that option's control fails and the grounding rule names it; an x86_64 macOS host is refused at
setup, a directory configured for it before the assertion existed is refused at its next compile, and a copy
without the assertion configures while the rule names the missing row. Intermediates go under PW_TEST_SCRATCH. A
receipt per control records its launches and elapsed time under the artifacts directory when one is given.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'docs'))
import fixture_inputs  # noqa: E402
import receipts  # noqa: E402
from repository_tree import directory, required  # noqa: E402

spec = importlib.util.spec_from_file_location('generate_build', ROOT / 'docs/generate_build.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
# The native sources Meson evaluates: the manifest and options, every file of the native tools, the runner
# sources, the service and the client.
NATIVE_INPUTS = (required('meson.build'), required('meson.options'), directory('controller/tools'),
                 directory('runner/Sources'), directory('runner/Services'), directory('runner/Clients'))


def scratch(prefix):
    base = os.environ.get('PW_TEST_SCRATCH')
    if base:
        Path(base).mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix=prefix, dir=base)


class NativePolicyTests(receipts.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / generator.MANIFEST_NAME).read_text())
        self.track_inputs(ROOT, fixture_inputs.expand(ROOT, NATIVE_INPUTS) + ['docs/build.json'])

    def run_meson(self, argv, timeout=300):
        return self.run_command(argv, capture_output=True, text=True, timeout=timeout)

    def native_copy(self):
        """A copy of the native sources under scratch, from declarations rather than Git."""
        held = scratch('pw-native-copy-')
        self.addCleanup(held.cleanup)
        root = Path(held.name)
        copied = fixture_inputs.copy_declared(ROOT, root, fixture_inputs.expand(ROOT, NATIVE_INPUTS))
        print(f'fixture: {copied.files} files, {copied.bytes} bytes, {copied.seconds:.3f} s')
        self.track_inputs(root, fixture_inputs.expand(ROOT, NATIVE_INPUTS))
        return root

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
            held = scratch('pw-meson-policy-')
            self.addCleanup(held.cleanup)
            builddir = Path(held.name) / 'builddir'
            setup = self.run_meson(['meson', 'setup', str(builddir), str(ROOT), f'-Dxpc={xpc}'])
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)
            configure = self.run_meson(['meson', 'configure', str(builddir), f'-D{name}={value}'])
            self.assertEqual(configure.returncode, 0, 'meson configure records the value; the assertion runs at the next regeneration')
            compile_ = self.run_meson(['meson', 'compile', '-C', str(builddir)])
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
        root = self.native_copy()
        meson = root / 'meson.build'
        text = meson.read_text()
        self.assertEqual(text.count("  'b_lto': false,\n"), 1)
        meson.write_text(text.replace("  'b_lto': false,\n", '', 1))
        builddir = root / 'builddir'
        setup = self.run_meson(['meson', 'setup', str(builddir), str(root), '-Dxpc=false'])
        self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)
        configure = self.run_meson(['meson', 'configure', str(builddir), '-Db_lto=true'])
        self.assertEqual(configure.returncode, 0, configure.stdout + configure.stderr)
        compile_ = self.run_meson(['meson', 'compile', '-C', str(builddir)], timeout=600)
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
        held = scratch('pw-meson-target-')
        self.addCleanup(held.cleanup)
        work = Path(held.name)
        cross = work / 'x86_64.ini'
        cross.write_text("[binaries]\nc = 'cc'\n[host_machine]\nsystem = 'darwin'\n"
                         "cpu_family = 'x86_64'\ncpu = 'x86_64'\nendian = 'little'\n")

        self.track_inputs(work, ['x86_64.ini'])

        def setup(source, name):
            return self.run_meson(['meson', 'setup', str(work / name), str(source), '-Dxpc=false', '--cross-file', str(cross)])
        message = 'Assert failed: output target: the native products are macOS arm64 code, but Meson is configured for host darwin x86_64\n'
        refused = setup(ROOT, 'x86_64')
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn(message, refused.stdout + refused.stderr)
        self.assertFalse((work / 'x86_64/build.ninja').exists(), 'a refused setup left a configured directory')
        # A copy of the native sources without the assertion: an x86_64 host configures, the rule names the missing row,
        # and restoring the assertion makes the next compile's regeneration refuse before anything compiles.
        source = self.native_copy()
        meson = source / 'meson.build'
        text = meson.read_text()
        start = text.index("assert(host_machine.system() == 'darwin'")
        end = text.index('host_machine.cpu_family()))\n', start) + len('host_machine.cpu_family()))\n')
        meson.write_text(text[:start] + text[end:])
        bypassed = setup(source, 'regenerated')
        self.assertEqual(bypassed.returncode, 0, 'with the assertion removed an x86_64 host configures: the control would fail here')
        self.assertTrue(any('output-target assertion' in p for p in generator.meson_problems(self.manifest, meson.read_text())))
        meson.write_text(text)
        regenerated = self.run_meson(['meson', 'compile', '-C', str(work / 'regenerated')])
        self.assertNotEqual(regenerated.returncode, 0)
        self.assertIn(message, regenerated.stdout + regenerated.stderr)
        self.assertNotIn('Compiling C object', regenerated.stdout + regenerated.stderr)
        changed = text.replace("host_machine.cpu_family() == 'aarch64'", "host_machine.cpu_family() == 'x86_64'", 1)
        self.assertNotEqual(changed, text)
        self.assertTrue(any('requires host' in p for p in generator.meson_problems(self.manifest, changed)))
        self.assertEqual(generator.meson_problems(self.manifest, text), [])


def main(argv):
    """Run the controls; with an artifacts directory, write a receipt per control (partial on failure)."""
    if len(argv) > 1:
        os.environ['PW_TEST_ARTIFACTS'] = argv[1]
    return receipts.timed_main(sys.modules[__name__], 'preflight/native_policy_controls', 'check_native_policy', mode='meson')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
