"""Grounding rules: the build manifest against build.sh, meson.build, the Makefile, the inventories and the baseline.

Each rule names the differing item. Agreement establishes textual consistency
between docs/build.json and the files it describes: the same banners in the
same order, the same refusal messages with the same statuses under the same
steps, the same knob values, the same signing calls, the same helper
invocations, a signing inventory equal to EXECUTABLES, and a baseline that
lists exactly the refusals without a behavioral or helper control. It does not
establish that a refusal fires or that it precedes the operation it protects;
the controls the manifest cites, and the baseline, carry that distinction.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('generate_build', ROOT / 'docs/generate_build.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def manifest():
    return generator.load_manifest(ROOT / generator.MANIFEST_NAME, ROOT)


def model():
    return generator.parse_script((ROOT / 'build.sh').read_text())


def check_banner_order():
    return generator.banner_problems(manifest(), model())


def check_refusals():
    return generator.refusal_problems(manifest(), model())


def check_meson_assertions():
    return generator.meson_problems(manifest(), (ROOT / 'meson.build').read_text())


def check_propagated_refusals():
    return generator.propagated_problems(manifest(), model())


def check_knobs():
    return generator.knob_problems(manifest(), model())


def check_signing():
    return generator.signing_problems(manifest(), model())


def check_invocations():
    return generator.invocation_problems(manifest(), model())


def check_makefile_entry():
    return generator.makefile_problems(manifest(), (ROOT / 'Makefile').read_text())


def check_inventory():
    return generator.inventory_problems(manifest(), model(), ROOT)


def check_baseline():
    return generator.baseline_problems(manifest(), generator.load_baseline(ROOT / generator.BASELINE_NAME))


def main():
    """Run every rule by name; the banner rule first, because the others map records to steps through it."""
    def run(name, rule):
        try:
            return [f'  {name}: {line}' for line in rule()]
        except (ValueError, OSError) as error:
            return [f'  {name}: {error}']
    problems = run('check_banner_order', lambda: check_banner_order())
    if not problems:
        problems += run('check_refusals', lambda: check_refusals())
        problems += run('check_meson_assertions', lambda: check_meson_assertions())
        problems += run('check_propagated_refusals', lambda: check_propagated_refusals())
        problems += run('check_knobs', lambda: check_knobs())
        problems += run('check_signing', lambda: check_signing())
        problems += run('check_invocations', lambda: check_invocations())
        problems += run('check_makefile_entry', lambda: check_makefile_entry())
        problems += run('check_inventory', lambda: check_inventory())
        problems += run('check_baseline', lambda: check_baseline())
    if problems:
        print('build documentation rules disagree:', file=sys.stderr)
        for line in problems:
            print(line, file=sys.stderr)
        return 1
    print('ok: 10 build documentation rules agree with build.sh, meson.build, the Makefile, the inventories and the baseline')
    return 0


if __name__ == '__main__':
    sys.exit(main())
