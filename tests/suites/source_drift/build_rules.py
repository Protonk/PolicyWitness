"""Grounding rules: the build manifest against build.sh, meson.build, the Makefile, the inventories and the baseline.

Each rule names the differing item. Agreement establishes textual consistency
between docs/build.json and the files it describes: the same banners in the
same order, the same refusal messages with the same statuses under the same
steps, the same knob values, the same signing calls, the same helper
invocations, a signing inventory equal to EXECUTABLES, and a baseline that
lists exactly the refusals without a behavioral or helper control. It does not
establish that a refusal fires or that it precedes the operation it protects;
the controls the manifest cites, and the baseline, carry that distinction.

This table is the one gated exception to the flat rule policy, not a general
dependency scheduler: `banner_order` runs first, because the other rows map
manifest records to script steps through the banners, and when it is not clean
(a banner problem, or a manifest or script that cannot be parsed) the nine
remaining rows are reported as blocked by it and never called. Once the gate
opens, each row reports its own input failure without blocking later rows.
The CLI keeps its 0/1 status: any reported failure is 1. The standalone
generator's `check`/`write` keep their own banner gate and refusal before write.
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'docs'))
import drift_rules  # noqa: E402
import repository_tree  # noqa: E402
from drift_rules import InputFailure, Problem, Rule  # noqa: E402
from repository_tree import required  # noqa: E402
spec = importlib.util.spec_from_file_location('generate_build', ROOT / 'docs/generate_build.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)

MANIFEST = generator.MANIFEST_NAME
SCRIPT = 'build.sh'
BASELINE = generator.BASELINE_NAME
MESON = 'meson.build'
MAKEFILE = 'Makefile'
INVENTORY_FILES = ('tests/lib/artifact.py', 'tests/build-evidence.py', 'README.md')
GENERATOR_HELPERS = ('docs/generate_build.py', 'docs/generator_common.py', 'docs/generate_architecture.py',
                     'docs/generate_limits.py', 'docs/limits.json', 'tests/catalog.json')
GATE = 'banner_order'


def _manifest(text, name, tree):
    """The validated manifest; one load per tree and manifest content."""
    try:
        return generator.load_manifest(tree.path(name), tree.root)
    except (ValueError, OSError) as error:
        raise InputFailure('manifest.invalid', f'{name}: {error}', name) from error


def manifest(tree):
    return tree.parsed(MANIFEST, _manifest, tree)


def _model(text, name):
    try:
        return generator.parse_script(text)
    except ValueError as error:
        raise InputFailure('script.unparseable', f'{name}: {error}', name) from error


def model(tree):
    """The script model; one parse per tree and script content."""
    return tree.parsed(SCRIPT, _model)


def records(key, lines, path):
    return [Problem(key, line, path) for line in lines]


def check_banner_order(tree):
    return records('build.banner_order', generator.banner_problems(manifest(tree), model(tree)), SCRIPT)


def check_refusals(tree):
    return records('build.refusals', generator.refusal_problems(manifest(tree), model(tree)), SCRIPT)


def check_meson_assertions(tree):
    return records('build.meson_assertions', generator.meson_problems(manifest(tree), tree.read_text(MESON)), MESON)


def check_propagated_refusals(tree):
    return records('build.propagated_refusals', generator.propagated_problems(manifest(tree), model(tree)), SCRIPT)


def check_knobs(tree):
    return records('build.knobs', generator.knob_problems(manifest(tree), model(tree)), SCRIPT)


def check_signing(tree):
    return records('build.signing', generator.signing_problems(manifest(tree), model(tree)), SCRIPT)


def check_invocations(tree):
    return records('build.invocations', generator.invocation_problems(manifest(tree), model(tree)), SCRIPT)


def check_makefile_entry(tree):
    return records('build.makefile_entry', generator.makefile_problems(manifest(tree), tree.read_text(MAKEFILE)), MAKEFILE)


def check_inventory(tree):
    for name in INVENTORY_FILES:
        if not tree.exists(name):
            raise repository_tree.MissingInput(name, 'no such file')
    return records('build.inventory', generator.inventory_problems(manifest(tree), model(tree), tree.root), INVENTORY_FILES[0])


def _baseline(text, name, tree):
    try:
        return generator.load_baseline(tree.path(name))
    except (ValueError, OSError) as error:
        raise InputFailure('baseline.invalid', f'{name}: {error}', name) from error


def check_baseline(tree):
    baseline = tree.parsed(BASELINE, _baseline, tree)
    return records('build.baseline', generator.baseline_problems(manifest(tree), baseline), BASELINE)


SCRIPT_INPUTS = (required(MANIFEST), required(SCRIPT))
RULES = (
    Rule('banner_order', check_banner_order, inputs=SCRIPT_INPUTS, helpers=GENERATOR_HELPERS),
    Rule('refusals', check_refusals, inputs=SCRIPT_INPUTS, helpers=GENERATOR_HELPERS),
    Rule('meson_assertions', check_meson_assertions, inputs=(required(MANIFEST), required(MESON)), helpers=GENERATOR_HELPERS),
    Rule('propagated_refusals', check_propagated_refusals, inputs=SCRIPT_INPUTS, helpers=GENERATOR_HELPERS),
    Rule('knobs', check_knobs, inputs=SCRIPT_INPUTS, helpers=GENERATOR_HELPERS),
    Rule('signing', check_signing, inputs=SCRIPT_INPUTS, helpers=GENERATOR_HELPERS),
    Rule('invocations', check_invocations, inputs=SCRIPT_INPUTS, helpers=GENERATOR_HELPERS),
    Rule('makefile_entry', check_makefile_entry, inputs=(required(MANIFEST), required(MAKEFILE)), helpers=GENERATOR_HELPERS),
    Rule('inventory', check_inventory, inputs=(*SCRIPT_INPUTS, *(required(name) for name in INVENTORY_FILES)),
         helpers=GENERATOR_HELPERS),
    Rule('baseline', check_baseline, inputs=(required(MANIFEST), required(BASELINE)), helpers=GENERATOR_HELPERS),
)


def run(tree, selected=None):
    """The gated table over one tree, for in-process controls."""
    return drift_rules.run_gated(tree, RULES, GATE, selected)


def main(argv=None):
    """Run every rule by name; the banner rule first, because the others map records to steps through it."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', type=Path, default=ROOT, help='the checkout to read (default: this repository)')
    parser.add_argument('--rule', action='append', dest='rules', metavar='ID', help='run only this rule, after the gate (repeatable)')
    parser.add_argument('--json', type=Path, metavar='PATH', help='also write every result record to this file')
    args = parser.parse_args(argv)
    tree = repository_tree.Tree(args.root)
    try:
        results = drift_rules.run_gated(tree, RULES, GATE, args.rules)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    if args.json:
        args.json.write_text(json.dumps(drift_rules.to_json(results), indent=2) + '\n')
    problems = []
    for result in results:
        problems += [f'  check_{result.rule_id}: {record.message}' for record in result.problems]
        if result.outcome == 'gate_blocked':
            problems.append(f'  check_{result.rule_id}: not evaluated: blocked by check_{result.blocked_by}')
    for line in drift_rules.summary_lines(results):
        print(line)
    if any(result.problems for result in results):
        print('build documentation rules disagree:', file=sys.stderr)
        for line in problems:
            print(line, file=sys.stderr)
        return 1
    print(f'ok: {len(results)} build documentation rules agree with build.sh, meson.build, the Makefile, the inventories and the baseline')
    return 0


if __name__ == '__main__':
    sys.exit(main())
