"""Run the real source checker against disposable source and guidance mutations."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import native_sources  # noqa: E402
sys.path.insert(0, str(ROOT / 'docs'))
import markdown_reader  # noqa: E402  (only for its file list; the fixtures below read Markdown themselves)
import generator_common  # noqa: E402  (static reading of the checker's RULES table)
import drift_rules  # noqa: E402
HOST = Path('runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift')
CALL = 'if predictionUnavailableOpFilters.contains(PredictionUnavailablePair(operation: check.operation, filterKind: kind)) {'
HOST_BINDING = '@_silgen_name("sandbox_check") func forbidden() -> Int32'


def declared_rules(repo):
    """The rule IDs the fixture's checker declares, read statically; never obtained by running it."""
    return [rule_id for rule_id, _ in generator_common.rule_declarations((repo / 'tests/suites/source_drift/check.py').read_text())]


def integrity_problems(repo, reported, extra=()):
    """Execution evidence that the dispatcher reported every declared rule exactly once, in table order."""
    if reported is None:
        return ['the checker wrote no result records']
    declared = declared_rules(repo)
    selected = [extra[i + 1] for i, argument in enumerate(extra[:-1]) if argument == '--rule'] or declared
    ids = [result['rule_id'] for result in reported['results']]
    expected = [rule_id for rule_id in declared if rule_id in selected]
    problems = []
    if ids != expected:
        problems.append(f'reported rules {ids} != declared {expected}')
    unknown = [result['rule_id'] for result in reported['results'] if result['outcome'] not in ('evaluated', 'input_blocked')]
    if unknown:
        problems.append(f'rules outside the two outcome categories: {unknown}')
    return problems


def run_checker(repo, evidence, extra=()):
    """The real checker over the fixture, with its stdout, stderr and result records captured beside the inputs."""
    results_path = evidence / 'results.json'
    argv = [sys.executable, '-B', '-S', str(repo / 'tests/suites/source_drift/check.py'), '--json', str(results_path), *extra]
    result = subprocess.run(argv, cwd=repo, capture_output=True, text=True, timeout=30)
    (evidence / 'stdout').write_text(result.stdout)
    (evidence / 'stderr').write_text(result.stderr)
    reported = json.loads(results_path.read_text()) if results_path.is_file() else None
    return argv, result, reported, integrity_problems(repo, reported, extra)


def expect_checker(repo, evidence, name, expected, diagnostic, extra=()):
    """Require the exact status, the diagnostic and a complete reported rule set; the receipt carries each rule's outcome."""
    argv, result, reported, integrity = run_checker(repo, evidence, extra)
    outcomes = {r['rule_id']: r['outcome'] for r in reported['results']} if reported else None
    record = dict(scenario=name, argv=argv, returncode=result.returncode, expected_returncode=expected,
                  expected_diagnostic=diagnostic, outcomes=outcomes, integrity=integrity)
    (evidence / 'command.json').write_text(json.dumps(record, indent=2) + '\n')
    if result.returncode != expected or (diagnostic and diagnostic not in result.stderr) or integrity:
        raise AssertionError(f'{name}: unexpected checker result: {record}\n{result.stdout}\n{result.stderr}')
    return record


def main(out):
    out.mkdir()
    repo = out / 'repo'
    # Copy only the checker's inputs, never build products or previous runs.
    paths = ['AGENTS.md', 'meson.build', 'meson.options', 'runner/README.md', 'runner/AGENTS.md', 'tests/README.md', 'tests/AGENTS.md',
             'tests/lib/native_sources.py', 'docs/generate_worker_identity.py',
             'controller/tools/pw_probe_runner/pw_worker_evidence.h', 'controller/tools/pw_probe_runner/pw_profile_capture.h',
             'controller/tools/pw_probe_runner/pw_extension_channel.h',
             'runner/Services/PWRunner/main.swift', 'runner/Clients/PWRunnerClient/main.swift',
             'tests/COVERAGE.md', 'tests/catalog.json', 'docs/PolicyWitness.md',
             'controller/tools/pw_probe_runner/pw_probe_runner_abi.h',
             'controller/src/cli.rs', 'controller/README.md', 'docs/ARCHITECTURE.md', 'docs/BUILD.md', 'docs/WORKER.md',
             'tests/fixtures/contract/response_shape.json',
             'tests/fixtures/contract/envelope_shape.json',
             'tests/suites/source_drift/check.py',
             'Makefile', 'tests/accept-release.sh', 'tests/lib/release_accept.py', 'tests/lib/release_archive.py']
    # The C sources are whatever the native expectation names for a C-only configuration,
    # so a new C target cannot be left out of the fixture.
    paths += sorted(set().union(*native_sources.expected(ROOT, xpc=False).values()))
    paths += [str(p.relative_to(ROOT)) for p in (ROOT / 'runner/Sources').rglob('*') if p.is_file()]
    paths += markdown_reader.source_files()
    paths += ['docs/repository_tree.py', 'tests/lib/drift_rules.py']
    paths += [str(p.relative_to(ROOT)) for pattern in ('*/run.sh', '*/README.md')
              for p in (ROOT / 'tests/suites').glob(pattern)]
    for name in paths:
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    original = (repo / HOST).read_text()
    if original.count(CALL) != 1:
        raise AssertionError('fixture requires the current planner membership condition')
    mirror = '''
private let hostExclusions: Set<PredictionUnavailablePair> = [
    .init(operation: "iokit-open-service", filterKind: PWRunnerWire.sandboxFilterIokitRegistryEntryClass),
    .init(operation: "iokit-open-user-client", filterKind: PWRunnerWire.sandboxFilterIokitUserClientClass),
    .init(operation: "sysctl-read", filterKind: PWRunnerWire.sandboxFilterSysctlName),
]
'''
    no_call = original.replace(CALL, 'if false {')
    scenarios = [
        ('baseline', original, 0, None),
        ('mirror-three', original.replace(CALL, CALL.replace('predictionUnavailableOpFilters', 'hostExclusions')) + mirror,
         1, 'must not define a local exclusion table'),
        ('mirror-four', original + mirror.replace('\n]', '\n    .init(operation: "file-read-data", filterKind: PWRunnerWire.sandboxFilterPath),\n]'),
         1, 'must not define a local exclusion table'),
        ('inferred-literal-table', original + '\nlet hostExclusions = [PredictionUnavailablePair(operation: "file-read-data", filterKind: PWRunnerWire.sandboxFilterPath)]\n',
         1, 'must not define a local exclusion table'),
        ('shadow-shared', original.replace(CALL, 'let predictionUnavailableOpFilters = knownFilterKinds\n        ' + CALL),
         1, 'shadow the shared set'),
        ('missing-call', no_call, 1, 'planValidatorQueries must use'),
        ('comment-only-call', no_call.replace('if false {', '// ' + CALL + '\n        if false {'),
         1, 'planValidatorQueries must use'),
        ('nested-comment-only-call', no_call.replace('if false {', '/* outer /* nested */ ' + CALL + ' */ if false {'),
         1, 'planValidatorQueries must use'),
        ('string-only-call', no_call.replace('if false {', 'let example = "' + CALL + '"\n        if false {'),
         1, 'planValidatorQueries must use'),
        ('other-function-call', no_call + '\nfunc unrelated() {\n    ' + CALL + '\n    }\n}\n',
         1, 'planValidatorQueries must use'),
        ('formatting', original.replace(CALL, CALL.replace('if ', 'if\n            ').replace('.contains(', ' . contains (\n')),
         0, None),
        ('commented-table', original + '\n/* example /* nested */\n' + mirror + '\n*/\n', 0, None),
        ('string-table', original + '\nlet example = """\n' + mirror + '\n"""\n', 0, None),
        ('restored', original, 0, None),
    ]
    scenarios = [(name, HOST, source, expected, diagnostic)
                 for name, source, expected, diagnostic in scenarios]
    shim = Path('runner/Sources/PWCWorkerShim/PWCWorkerShim.c')
    shim_original = (repo / shim).read_text()
    for name, path, source, snippet, expected in [
        ('host-binding', HOST, original, '@_silgen_name("sandbox_check") func native() -> Int32', 1),
        ('host-unrelated-api', HOST, original,
         'let callback: @convention(c) (Int32) -> Int32 = ptr\nlet h = dlopen("/usr/lib/libSystem.B.dylib", RTLD_NOW)', 0),
        ('shim-sandbox-call', shim, shim_original, 'void forbidden(void) { sandbox_free_error(0); }', 1),
        ('shim-symbol-constant', shim, shim_original,
         'const char *symbol = "sandbox_check"; void *f = dlsym(handle, symbol);', 1),
        ('shim-explanatory-string', shim, shim_original, 'const char *example = "sandbox_check(pid)";', 0),
    ]:
        scenarios.append((name, path, source + '\n' + snippet + '\n', expected,
                          'the XPC host never links, loads or calls libsandbox' if expected else None))
    # The Meson reader: a core file dropped from or added to the PWRunner target is
    # named by the diff; a missing host or shim target is named as such.
    manifest = Path('meson.build')
    manifest_original = (repo / manifest).read_text()
    core_line = "    'runner/Sources/PWRunnerCore/PathUtils.swift',\n"
    assert manifest_original.count(core_line) == 1, 'fixture requires the current PWRunner source list'
    host_declaration = manifest_original[manifest_original.index("pwrunner = executable('PWRunner',"):]
    host_declaration = host_declaration[:host_declaration.index('endif')]
    decoy = ('\nif false\n' + host_declaration.replace('pwrunner = ', 'pwrunner_decoy = ').rstrip() + '\nendif\n')
    worker_line = "  files('controller/tools/pw_probe_runner/pw_probe_runner.c'),"
    assert manifest_original.count(worker_line) == 1
    for name, mutated, diagnostic in [
        ('meson-core-file-dropped', manifest_original.replace(core_line, ''),
         "PWRunner lacks 'runner/Sources/PWRunnerCore/PathUtils.swift' which is in the tree"),
        ('meson-core-file-added', manifest_original.replace(core_line, core_line + "    'runner/Sources/PWRunnerCore/Missing.swift',\n"),
         "PWRunner has 'runner/Sources/PWRunnerCore/Missing.swift' which the tree does not expect"),
        ('meson-host-target-missing', manifest_original.replace("executable('PWRunner',", "executable('PWRunnerRenamed',"),
         "no 'PWRunner' target"),
        ('meson-shim-target-missing', manifest_original.replace("static_library('PWCWorkerShim',", "static_library('PWCWorkerShimRenamed',"),
         "no 'PWCWorkerShim' target"),
        # A dead declaration with the complete list beside a live one missing a
        # file: the duplicate name is refused instead of resolved.
        ('meson-duplicate-host-declaration', manifest_original.replace(core_line, '') + decoy,
         "declares 'PWRunner' 2 times"),
        ('meson-worker-source-substituted',
         manifest_original.replace(worker_line, "  files('controller/tools/pw_probe_runner/substitute/pw_probe_runner.c'),"),
         "pw-probe-runner has 'controller/tools/pw_probe_runner/substitute/pw_probe_runner.c' which the tree does not expect"),
    ]:
        assert mutated != manifest_original, name
        scenarios.append((name, manifest, mutated, 1, diagnostic))
    scenarios.append(('meson-restored', manifest, manifest_original, 0, None))
    scenarios = [(name, {path: source}, expected, diagnostic)
                 for name, path, source, expected, diagnostic in scenarios]
    scenarios += guidance_scenarios(repo)
    scenarios += structure_scenarios(repo)
    scenarios += gap_scenarios(repo)
    scenarios += route_scenarios(repo)
    scenarios += rule_gap_scenarios(repo)
    originals = {path: (repo / path).read_text()
                 for _, changes, _, _ in scenarios for path in changes}
    receipts = []
    for name, changes, expected, diagnostic in scenarios:
        evidence = out / name
        evidence.mkdir()
        for path, source in originals.items():
            (repo / path).write_text(source)
        for path, source in changes.items():
            (repo / path).write_text(source)
            captured = evidence / path
            captured.parent.mkdir(parents=True, exist_ok=True)
            captured.write_text(source)
        receipts.append(expect_checker(repo, evidence, name, expected, diagnostic))
    for path, source in originals.items():
        (repo / path).write_text(source)
        if (ROOT / path).read_text() != source:
            raise AssertionError(f'source controls changed the working input: {path}')
    receipts += registry_scenarios(repo, out)
    receipts += precondition_scenarios(repo, out)
    receipts += dispatch_omission_scenario(repo, out)
    receipts += inventory_controls(out)
    receipts += isolation_controls(out)
    receipts += host_invariance_controls(out)
    receipts += configured_controls(repo, manifest_original, worker_line, out)
    (out / 'controls.json').write_text(json.dumps({'ok': True, 'scenarios': receipts}, indent=2) + '\n')
    print(f'{len(receipts)} source and guidance controls passed')


def route_scenarios(repo):
    """A documented direct route or a release-specific selection is named by the real checker;
    a location, a comment and the selector-free invocations pass."""
    readme = Path('tests/README.md')
    makefile = Path('Makefile')
    accept = Path('tests/lib/release_accept.py')
    source = {path: (repo / path).read_text() for path in (readme, makefile, accept)}
    command = 'commands: tests/README.md shows a case script as a command'
    recipe = source[makefile].replace('\t@./tests/run.sh --prune\n', '\t@./tests/run.sh --prune\n\t@./tests/run.sh --suite smoke\n', 1)
    assert recipe != source[makefile], 'fixture requires the prune recipe'
    arguments = source[makefile].replace('\t@./tests/run.sh --prune\n', '\t@./tests/run.sh --prune\n\t@./tests/run.sh smoke\n', 1)
    acceptance_line = "        invoke(out / 'execution', ['bash', ROOT / 'tests/run.sh'], timeout=BATTERY_TIMEOUT_SECONDS, env=env, cwd=ROOT)\n"
    assert source[accept].count(acceptance_line) == 1, 'fixture requires the acceptance invocation'
    selected = source[accept].replace(acceptance_line, acceptance_line.replace("'tests/run.sh']", "'tests/run.sh', '--case', 'smoke/specimen_file_read_deny']"))
    return [
        ('route-fenced-script', {readme: source[readme] + '\n```sh\nbash tests/suites/smoke/pw_specimen_smoke.sh\n```\n'}, 1, command),
        ('route-fenced-bare-script', {readme: source[readme] + '\n```sh\ntests/suites/unit/fmt.sh\n```\n'}, 1, command),
        ('route-dot-slash-span', {readme: source[readme] + '\nUse `./tests/suites/unit/fmt.sh` here.\n'}, 1, command),
        ('route-run-sentence', {readme: source[readme] + '\nRun `tests/suites/unit/fmt.sh` to check formatting.\n'}, 1, command),
        ('route-location-span', {readme: source[readme] + '\n- **Location:** `tests/suites/unit/fmt.sh`\n'}, 0, None),
        ('route-direct-output', {readme: source[readme] + '\nOutput lands in `tests/out/runs/direct`.\n'}, 1, 'retired direct output'),
        ('route-makefile-selector', {makefile: recipe}, 1, 'names the test selector --suite'),
        ('route-makefile-arguments', {makefile: arguments}, 1, 'runs tests/run.sh with arguments'),
        ('route-makefile-comment', {makefile: source[makefile] + '\n# tests/run.sh --suite smoke is how a developer selects one suite\n'}, 0, None),
        ('route-acceptance-selector', {accept: selected}, 1, 'names the test selector --case'),
        ('route-restored', source, 0, None),
    ]


def registry_scenarios(repo, out):
    """The suite registry's on-disk side: a run.sh no case names, a suite directory
    without a README and one the catalog lacks are each named by the real checker."""
    wrapper = repo / 'tests/suites/smoke/run.sh'
    nested = repo / 'tests/suites/smoke/retired/run.sh'
    stray = repo / 'tests/suites/stray_suite'

    def write_wrapper():
        wrapper.write_text('#!/usr/bin/env bash\nexec bash "$(dirname "$0")/pw_specimen_smoke.sh"\n')

    def stray_without_readme():
        stray.mkdir()
        (stray / 'notes.txt').write_text('a directory under tests/suites is a suite directory\n')

    def nested_wrapper():
        nested.parent.mkdir()
        nested.write_text('#!/usr/bin/env bash\nexit 0\n')

    readme = repo / 'tests/README.md'
    catalog = repo / 'tests/catalog.json'
    readme_original = readme.read_text()
    catalog_original = catalog.read_text()
    control = repo / 'tests/suites/baseline_control'

    def baseline_suite(default):
        """A Baseline-tier suite present on disk, in the coverage table and in the catalog, with one case."""
        control.mkdir(exist_ok=True)
        (control / 'README.md').write_text('# baseline_control\n')
        lines = readme_original.split('\n')
        start = lines.index('## Suite coverage')
        separator = next(i for i in range(start, len(lines)) if lines[i].startswith('| --- |'))
        lines.insert(separator + 1, '| `baseline_control` | Baseline | Control suite for the default-membership rule. | none | none |')
        readme.write_text('\n'.join(lines))
        data = json.loads(catalog_original)
        data['suites']['baseline_control'] = {'command': ['bash', 'tests/suites/baseline_control/run.sh'], 'requires': [],
                                              'cases': [{'id': 'control', 'description': 'control', 'default': default}]}
        catalog.write_text(json.dumps(data, indent=2) + '\n')

    def baseline_removed():
        shutil.rmtree(control)
        readme.write_text(readme_original)
        catalog.write_text(catalog_original)

    receipts = []
    for name, setup, expected, diagnostic in [
        ('registry-wrapper-script', write_wrapper, 1, 'tests/suites/smoke/run.sh is not a case command'),
        ('registry-wrapper-removed', wrapper.unlink, 0, None),
        ('registry-nested-wrapper', nested_wrapper, 1, 'tests/suites/smoke/retired/run.sh is not a case command'),
        ('registry-nested-wrapper-removed', lambda: shutil.rmtree(nested.parent), 0, None),
        ('registry-directory-without-readme', stray_without_readme, 1, 'tests/suites/stray_suite/ has no README.md'),
        ('registry-directory-outside-catalog', lambda: (stray / 'README.md').write_text('# stray_suite\n'),
         1, 'suite directories and catalog disagree'),
        ('registry-restored', lambda: shutil.rmtree(stray), 0, None),
        ('registry-baseline-suite-nondefault', lambda: baseline_suite(False), 1,
         "Baseline-tier suite 'baseline_control' is missing from tests/catalog.json's default membership"),
        ('registry-baseline-suite-default', lambda: baseline_suite(True), 0, None),
        ('registry-baseline-suite-removed', baseline_removed, 0, None),
    ]:
        setup()
        evidence = out / name
        evidence.mkdir()
        receipts.append(expect_checker(repo, evidence, name, expected, diagnostic))
    assert not wrapper.exists() and not stray.exists() and not control.exists()
    return receipts


def rule_gap_scenarios(repo):
    """Dedicated negative controls for the matrix, attempt-kind, test-seam, pair and landing-path rules,
    each with its converse where the rule has one, followed by restoration."""
    coverage = Path('tests/COVERAGE.md')
    swift = Path('runner/Sources/PWRunnerCore/CWorker.swift')
    header = Path('controller/tools/pw_probe_runner/pw_probe_runner_abi.h')
    runner_readme = Path('runner/README.md')
    guide = Path('docs/PolicyWitness.md')
    architecture = Path('docs/ARCHITECTURE.md')
    source = {path: (repo / path).read_text() for path in (coverage, swift, header, runner_readme, guide, architecture)}

    def rows_under(path, heading):
        lines = source[path].split('\n')
        start = lines.index(heading)
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('## ')), len(lines))
        return [line for line in lines[start:end] if line.startswith('| `')]

    def row_named(rows, name):
        return next(line for line in rows if line.startswith(f'| `{name}` |'))

    def renamed(row, old, new):
        return row.replace(f'`{old}`', f'`{new}`', 1)

    def without(path, line):
        assert source[path].count(line + '\n') == 1, (path, line[:40])
        return source[path].replace(line + '\n', '', 1)

    def with_after(path, anchor, line):
        assert source[path].count(anchor + '\n') == 1, (path, anchor[:40])
        return source[path].replace(anchor + '\n', anchor + '\n' + line + '\n', 1)

    rows = rows_under(coverage, '## Normalized outcome coverage matrix')
    timeout_row, last = row_named(rows, 'runner_timeout'), rows[-1]
    attempt_rows = rows_under(coverage, '## Attempt outcome coverage matrix')
    sysctl_row, attempt_last = row_named(attempt_rows, 'sysctl_failed'), attempt_rows[-1]
    swift_close = '    case extensionRelease = 11\n}'
    c_close = '    PW_ATTEMPT_EXTENSION_RELEASE = 11,\n} pw_attempt_kind_t;'
    assert source[swift].count(swift_close) == 1 and source[header].count(c_close) == 1, 'fixture requires the current attempt kinds'
    assert source[swift].count('    case sysctlRead     = 7\n') == 1
    seam_first = rows_under(runner_readme, '## Test seam: `_test_overrides`')[0]
    pair_line = next(line for line in source[guide].split('\n') if line.startswith('- `(iokit-open-service, iokit_registry_entry_class)`'))
    prediction_row = next(line for line in source[architecture].split('\n') if line.startswith('| Prediction |'))
    assert '`steps[].sandbox_check`' in prediction_row
    return [
        ('rule-runner-outcome-suite-row-removed', {coverage: without(coverage, timeout_row)}, 1,
         "suite 'runner_outcome_runner_timeout' has no row for outcome 'runner_timeout'"),
        ('rule-normalized-matrix-extra-row', {coverage: with_after(coverage, last, renamed(last, 'xpc_no_reply', 'bogus_outcome'))}, 1,
         "coverage matrix lists 'bogus_outcome' but no NormalizedOutcome constant by that name exists"),
        ('rule-attempt-matrix-row-removed', {coverage: without(coverage, sysctl_row)}, 1,
         'AttemptOutcome.sysctl_failed has no row in tests/COVERAGE.md attempt-outcome coverage matrix'),
        ('rule-attempt-matrix-extra-row',
         {coverage: with_after(coverage, attempt_last, renamed(attempt_last, 'no_completed_result', 'bogus_attempt'))}, 1,
         "attempt-outcome matrix lists 'bogus_attempt' but no AttemptOutcome constant by that name exists"),
        ('rule-matrix-restored', {coverage: source[coverage]}, 0, None),
        ('rule-attempt-kind-swift-extra',
         {swift: source[swift].replace(swift_close, '    case extensionRelease = 11\n    case extraKind = 12\n}', 1)}, 1,
         'Swift PWAttemptKind.EXTRA_KIND=12 has no matching pw_attempt_kind_t value'),
        ('rule-attempt-kind-c-extra',
         {header: source[header].replace(c_close, '    PW_ATTEMPT_EXTENSION_RELEASE = 11,\n    PW_ATTEMPT_EXTRA_KIND = 12,\n} pw_attempt_kind_t;', 1)}, 1,
         'C PW_ATTEMPT_EXTRA_KIND=12 has no matching PWAttemptKind raw value'),
        ('rule-attempt-kind-name-mismatch',
         {swift: source[swift].replace('    case sysctlRead     = 7\n', '    case sysctlQuery    = 7\n', 1)}, 1,
         'value 7 is PW_ATTEMPT_SYSCTL_READ in C but PWAttemptKind.SYSCTL_QUERY in Swift'),
        ('rule-attempt-kind-c-gap',
         {swift: source[swift].replace(swift_close, '    case extensionRelease = 11\n    case gapped = 13\n}', 1),
          header: source[header].replace(c_close, '    PW_ATTEMPT_EXTENSION_RELEASE = 11,\n    PW_ATTEMPT_GAPPED = 13,\n} pw_attempt_kind_t;', 1)}, 1,
         'pw_attempt_kind_t has a numeric gap at 12'),
        ('rule-attempt-kind-malformed-c-enum', {header: source[header].replace('} pw_attempt_kind_t;', '};', 1)}, 2,
         'could not locate pw_attempt_kind_t in pw_probe_runner_abi.h'),
        ('rule-attempt-kind-restored', {swift: source[swift], header: source[header]}, 0, None),
        ('rule-test-overrides-extra-row',
         {runner_readme: with_after(runner_readme, seam_first, renamed(seam_first, 'worker_executable_path', 'bogus_override'))}, 1,
         "runner/README.md's test-seam table lists 'bogus_override' but PWRunnerTestOverrides has no such property"),
        ('rule-test-overrides-restored', {runner_readme: source[runner_readme]}, 0, None),
        ('rule-pair-document-only', {guide: with_after(guide, pair_line, '- `(control-op, control_filter)` control')}, 1,
         "('control-op', 'control_filter') in docs (docs/PolicyWitness.md) but missing from swift (ProbeRunner.swift)"),
        ('rule-pair-restored', {guide: source[guide]}, 0, None),
        ('rule-evidence-unknown-landing',
         {architecture: source[architecture].replace(
             prediction_row, prediction_row.replace('`steps[].sandbox_check`', '`steps[].sandbox_check` and `steps[].bogus_landing`', 1), 1)}, 1,
         '`steps[].bogus_landing` is not a key of the reply shape golden'),
        ('rule-evidence-restored', {architecture: source[architecture]}, 0, None),
    ]


def guidance_scenarios(repo):
    """Exercise local sections and diagnostic routes without comparing wording."""
    paths = [Path(p) for p in ('AGENTS.md', 'runner/AGENTS.md', 'tests/AGENTS.md', 'docs/BUILD.md')]
    documents = {path: (repo / path).read_text() for path in paths}
    scenarios = []
    heading = 'Sandboxed automation harnesses'
    root_bounds = None
    for path, source in documents.items():
        match = re.search(r'^(#{2,6}) ' + heading + r'\n', source, re.M)
        assert match, f'fixture requires the warning in {path}'
        start = match.end()
        level = len(match[1])
        following = re.search(r'^#{1,' + str(level) + r'} ', source[start:], re.M)
        end = start + following.start() if following else len(source)
        body = source[start:end]
        name = str(path).replace('/', '-').replace('.', '-')
        diagnostic = f'harness guidance: {path}:'
        section = source[match.start():end]
        # The fixture locates the authored section directly, independently of
        # the checker's comment/fence reader.
        def body_change(value):
            return source[:start] + value + source[end:]
        links = re.findall(r'\[[^\]\n]+\]\([^)\n]+\)', body) if path == paths[0] else []
        independent = '\nA separately written diagnostic explanation.\n\n' + '\n'.join(links) + '\n\n'
        paragraphs = body.strip().split('\n\n')
        changed = [
            ('rewritten', body_change(independent), 0, None),
            ('rewrapped', body_change('\n' + ' '.join(body.split()) + '\n\n'), 0, None),
            ('reordered', body_change('\n' + '\n\n'.join(reversed(paragraphs)) + '\n\n'), 0, None),
            ('local-prose', body_change(body + 'Local diagnostic control.\n\n'), 0, None),
            ('heading-missing', source[:match.start()] + source[end:], 1, diagnostic + ' expected one'),
            ('heading-duplicate', body_change(body + match[0] + '\nDuplicate guidance.\n\n'), 1, diagnostic + ' expected one'),
            ('empty', body_change('\n\n'), 1, diagnostic + ' empty'),
            ('headings-only', body_change('\n' + '#' * (level + 1) + ' Local topic\n\n'), 1, diagnostic + ' empty'),
            ('fenced-body', body_change('\n```text\n' + body + '\n```\n\n'), 1, diagnostic + ' empty'),
            ('comment-body', body_change('\n<!--\n' + body + '\n-->\n\n'), 1, diagnostic + ' empty'),
            ('indented-body', body_change('\n' + '\n'.join('    ' + line for line in body.splitlines()) + '\n\n'), 1, diagnostic + ' empty'),
            ('fenced-section', source[:match.start()] + '~~~~text\n' + section + '\n~~~~\n\n' + source[end:], 1, diagnostic + ' expected one'),
            ('comment-section', source[:match.start()] + '<!--\n' + section + '\n-->\n\n' + source[end:], 1, diagnostic + ' expected one'),
            ('body-after-peer', body_change('\n' + '#' * level + ' Other guidance\n\n' + body), 1, diagnostic + ' empty'),
            ('body-after-parent', body_change('\n' + '#' * (level - 1) + ' Other guidance\n\n' + body), 1, diagnostic + ' empty'),
            # A fence's shorter marker does not close it, and comments in an
            # example must not hide the real section that follows.
            ('short-fence-close', body_change('\n````text\n```\n' + body + '\n````\n\n'), 1, diagnostic + ' empty'),
            ('fake-heading-before-real', source[:match.start()] + '```text\n<!--\n' + match[0] + '```\n\n' + source[match.start():], 0, None),
        ]
        scenarios.extend((f'guidance-{kind}-{name}', {path: value}, status, message)
                         for kind, value, status, message in changed)
        if path == paths[0]:
            root_bounds = (start, end)
        scenarios.append((f'guidance-restored-{name}', {path: source}, 0, None))

    root = paths[0]
    source = documents[root]
    start, end = root_bounds
    body = source[start:end]
    for target in ('runner/AGENTS.md', 'tests/AGENTS.md', 'docs/BUILD.md'):
        route = target + '#sandboxed-automation-harnesses'
        link = re.search(r'\[[^\]\n]+\]\(' + re.escape(route) + r'\)', body)[0]
        diagnostic = f'harness guidance: AGENTS.md: missing diagnostic route {route}'
        variants = [
            ('removed', '', 1),
            ('wrong-path', link.replace(target, 'missing/AGENTS.md'), 1),
            ('wrong-fragment', link.replace('#sandboxed-automation-harnesses', '#missing'), 1),
            ('fenced', '\n```markdown\n' + link + '\n```\n', 1),
            ('comment', '<!-- ' + link + ' -->', 1),
            ('inline-example', '`' + link + '`', 1),
            ('image', '!' + link, 1),
            ('relabeled', '[Other diagnostic wording](' + route + ')', 0),
            ('relative-path', link.replace(target, './' + target), 0),
            ('code-label', '[`' + target + '`](' + route + ')', 0),
            ('code-label-example', '`` [`' + target + '`](' + route + ') ``', 1),
            ('wrapped-label', '[Wrapped diagnostic\nwording](' + route + ')', 0),
            # Neither a label nor code within it continues across a blank line.
            ('split-label', '[Split `diagnostic\n\nwording`](' + route + ')', 1),
            ('indented-continuation', 'continued\n    ' + link, 0),
            ('indented-example', '\n\n    ' + link + '\n\n', 1),
            ('indented-after-heading', '\n\n#### Example\n    ' + link + '\n\n', 1),
            # A list item's content after a blank line stays in the item.
            ('list-continuation', '\n\n- Diagnostics are\n\n    ' + link + '\n\n', 0),
        ]
        name = target.replace('/', '-').replace('.', '-')
        for kind, replacement, status in variants:
            changed = source[:start] + body.replace(link, replacement, 1) + source[end:]
            scenarios.append((f'guidance-route-{kind}-{name}', {root: changed}, status,
                              diagnostic if status else None))
        # A working link elsewhere in the root document cannot supply this route.
        moved = link + '\n\n' + source[:start] + body.replace(link, '', 1) + source[end:]
        scenarios.append((f'guidance-route-outside-section-{name}', {root: moved}, 1, diagnostic))
    # The pinned parser reads an inline comment containing "--" as text; the reader refuses it.
    # A word first keeps the comment inline: one that begins a line is an HTML block.
    commented = source[:start] + body.replace(link, 'see <!-- a -- b ' + link + ' -->', 1) + source[end:]
    scenarios.append(('guidance-route-unrecognized-comment', {root: commented}, 1, 'remove the "--"'))
    scenarios.append(('guidance-routes-restored', {root: source}, 0, None))

    scenarios.append(('guidance-restored', documents, 0, None))
    return scenarios


def structure_scenarios(repo):
    """Each table, list, fence and paragraph the checker reads stops counting inside a comment."""
    def lines(path):
        return (repo / path).read_text().split('\n')

    def first_row(path, heading):
        text = lines(path)
        start = text.index(heading)
        row = next(line for line in text[start:] if line.startswith('| `'))
        return row, row.split('`')[1]

    def hidden(path, old, new):
        source = (repo / path).read_text()
        assert source.count(old) >= 1, (path, old)
        return {Path(path): source.replace(old, new, 1)}

    def wrapped(path, first, last, after=0):
        text = lines(path)
        a = next(i for i in range(after, len(text)) if first(text[i]))
        b = next(i for i in range(a + 1, len(text)) if last(text[i]))
        return {Path(path): '\n'.join(text[:a] + ['<!--'] + text[a:b + 1] + ['-->'] + text[b + 1:])}

    scenarios = []
    row, name = first_row('tests/README.md', '## Suite coverage')
    scenarios.append(('structure-suite-row-comment', hidden('tests/README.md', row, row.replace(f'`{name}`', f'<!-- `{name}` -->', 1)),
                      1, f'tests/suites/{name}/ exists but has no row'))
    row, name = first_row('tests/COVERAGE.md', '## Normalized outcome coverage matrix')
    scenarios.append(('structure-matrix-row-comment', hidden('tests/COVERAGE.md', row, row.replace(f'`{name}`', f'<!-- `{name}` -->', 1)),
                      1, f'NormalizedOutcome.{name} has no row'))
    row, name = first_row('runner/README.md', '## Test seam: `_test_overrides`')
    scenarios.append(('structure-override-row-comment', hidden('runner/README.md', row, row.replace(f'`{name}`', f'<!-- `{name}` -->', 1)),
                      1, f'PWRunnerTestOverrides.{name} has no row'))
    pair = '`(iokit-open-service, iokit_registry_entry_class)`'
    scenarios.append(('structure-pair-comment', hidden('docs/PolicyWitness.md', '- ' + pair, f'- <!-- {pair} -->'),
                      1, "('iokit-open-service', 'iokit_registry_entry_class') in swift"))
    surface = lines('controller/README.md').index('## CLI surface (contract)')
    scenarios.append(('structure-cli-fence-comment',
                      wrapped('controller/README.md', lambda line: line == '```text', lambda line: line == '```', surface),
                      # The section's next text block, the runner subcommands, then disagrees with the usage.
                      1, 'CLI surface drift between'))
    scenarios.append(('structure-known-gap-comment',
                      wrapped('docs/ARCHITECTURE.md', lambda line: line.startswith('Known gap'), lambda line: not line.strip()),
                      1, 'known gaps: docs/ARCHITECTURE.md: the index lists'))
    scenarios.append(('structure-evidence-table-comment',
                      wrapped('docs/ARCHITECTURE.md', lambda line: line.startswith('| Channel'), lambda line: not line.strip()),
                      1, 'evidence channels: table missing'))
    # The parser pads a short row to the header's width; an empty landing cell is still reported.
    row = next(line for line in lines('docs/ARCHITECTURE.md') if line.startswith('| Prediction |'))
    scenarios.append(('structure-evidence-short-row', hidden('docs/ARCHITECTURE.md', row, '|'.join(row.split('|')[:4]) + '|'),
                      1, 'evidence channels: row has no landing column'))
    scenarios.append(('structure-known-gap-ordered-index',
                      hidden('docs/ARCHITECTURE.md', '- [Why these processes exist](#', '1. [Why these processes exist](#'),
                      1, 'an index bullet must open with a link'))
    return scenarios


def gap_scenarios(repo):
    """Exercise every tour's paragraph/index ownership through the real checker."""
    scenarios = []
    for name in ('ARCHITECTURE', 'BUILD', 'WORKER'):
        path = Path(f'docs/{name}.md')
        source = (repo / path).read_text()
        heading = '## Known gaps'
        assert source.count(heading) == 1
        added = source.replace(heading,
            '## Gap control\n\nKnown gap: controlled incomplete guarantee.\n\n' + heading)
        indexed = added.rstrip() + '\n- [Gap control](#gap-control): controlled guarantee.\n'
        scenarios.extend([
            (f'gap-unindexed-{name}', {path: added}, 1, f'known gaps: docs/{name}.md'),
            (f'gap-indexed-{name}', {path: indexed}, 0, None),
            (f'gap-heading-missing-{name}', {path: source.replace(heading, '## Other ending')},
             1, f'known gaps: docs/{name}.md'),
            (f'gap-spurious-index-{name}', {path: source.rstrip() + '\n- [Gap control](#gap-control)\n'},
             1, f'known gaps: docs/{name}.md'),
            (f'gap-restored-{name}', {path: source}, 0, None),
        ])
    return scenarios


def configured_controls(repo, manifest_original, worker_line, out):
    """The configured-directory reading build.sh uses: what Meson evaluated must be the tree,
    and what the compiler consumed for the worker must be in the identity.

    xpc=false configures and compiles only the two C executables, so these
    controls need no Swift discovery. The unmodified manifest passes; a worker
    declaration pointing at a substitute file, present on disk so Meson accepts
    it, is refused by name; a worker include reaching outside the digest's
    directories through a symlinked directory, or by a relative path, is
    refused by the closure check, and so is an include of an absolute path
    outside the checkout that is neither the SDK nor the developer directory.
    Finally the configured directory is copied
    along with the checkout, as build.sh invokes the check: the copy is named
    as the checkout and the directory's recorded source is refused."""
    checker = repo / 'tests/lib/native_sources.py'
    substitute = repo / 'controller/tools/pw_probe_runner/substitute/pw_probe_runner.c'
    substitute.parent.mkdir()
    shutil.copy2(repo / 'controller/tools/pw_probe_runner/pw_probe_runner.c', substitute)
    for header in (repo / 'controller/tools/pw_probe_runner').glob('*.h'):
        shutil.copy2(header, substitute.parent / header.name)
    worker = repo / 'controller/tools/pw_probe_runner/pw_probe_runner.c'
    worker_original = worker.read_text()
    escape = repo / 'controller/src/escape.h'
    escape.parent.mkdir(exist_ok=True)
    escape.write_text('#define PW_AUDIT_ESCAPE 1\n')
    (repo / 'audit-headers').mkdir()
    (repo / 'audit-headers/audit.h').write_text('#define PW_AUDIT_VALUE 17\n')
    outside = out / 'outside-checkout'
    outside.mkdir()
    (outside / 'escape.h').write_text('#define PW_OUTSIDE_VALUE 23\n')
    link = repo / 'controller/tools/pw_probe_runner/audit-link'
    include_line = '#include "pw_probe_runner_abi.h"\n'
    assert worker_original.count(include_line) == 1
    receipts = []
    for name, manifest, source, symlink, expected, diagnostic in [
        ('configured-unmodified', manifest_original, worker_original, False, 0, None),
        ('configured-worker-substituted',
         manifest_original.replace(worker_line, "  files('controller/tools/pw_probe_runner/substitute/pw_probe_runner.c'),"),
         worker_original, False, 1,
         "pw-probe-runner has 'controller/tools/pw_probe_runner/substitute/pw_probe_runner.c' which the tree does not expect"),
        ('configured-symlinked-include', manifest_original,
         worker_original.replace(include_line, include_line + '#include "audit-link/audit.h"\n'), True, 1,
         "symlink under identity sources: controller/tools/pw_probe_runner/audit-link"),
        ('configured-relative-escape', manifest_original,
         worker_original.replace(include_line, include_line + '#include "../../src/escape.h"\n'), False, 1,
         "pw-probe-runner consumed 'controller/src/escape.h' which is not an identity input"),
        ('configured-absolute-escape', manifest_original,
         worker_original.replace(include_line, include_line + f'#include "{(outside / "escape.h").resolve()}"\n'), False, 1,
         f"pw-probe-runner consumed '{(outside / 'escape.h').resolve()}' outside the checkout, the SDK and the developer directory"),
        ('configured-restored', manifest_original, worker_original, False, 0, None),
    ]:
        evidence = out / name
        evidence.mkdir()
        (repo / 'meson.build').write_text(manifest)
        (evidence / 'meson.build').write_text(manifest)
        worker.write_text(source)
        (evidence / 'pw_probe_runner.c').write_text(source)
        if link.is_symlink():
            link.unlink()
        if symlink:
            link.symlink_to('../../../audit-headers')
        builddir = repo / 'builddir'
        shutil.rmtree(builddir, ignore_errors=True)
        for step, argv in (('setup', ['meson', 'setup', str(builddir), str(repo), '-Dxpc=false']),
                           ('compile', ['meson', 'compile', '-C', str(builddir)])):
            result = subprocess.run(argv, cwd=repo, capture_output=True, text=True, timeout=300)
            (evidence / f'{step}.stdout').write_text(result.stdout)
            (evidence / f'{step}.stderr').write_text(result.stderr)
            if result.returncode != 0:
                raise AssertionError(f'{name}: meson {step} failed: {result.stderr}')
        argv = [sys.executable, '-B', '-S', str(checker), '--builddir', str(builddir), '--root', str(repo)]
        result = subprocess.run(argv, cwd=repo, capture_output=True, text=True, timeout=60)
        (evidence / 'stdout').write_text(result.stdout)
        (evidence / 'stderr').write_text(result.stderr)
        record = dict(scenario=name, argv=argv, returncode=result.returncode,
                      expected_returncode=expected, expected_diagnostic=diagnostic)
        (evidence / 'command.json').write_text(json.dumps(record, indent=2) + '\n')
        if result.returncode != expected or (diagnostic and diagnostic not in result.stderr):
            raise AssertionError(f'{name}: unexpected configured check result: {record}\n{result.stdout}\n{result.stderr}')
        receipts.append(record)
    (repo / 'meson.build').write_text(manifest_original)
    worker.write_text(worker_original)
    copy = out / 'copied-checkout'
    shutil.copytree(repo, copy, symlinks=True)
    evidence = out / 'configured-copied-checkout'
    evidence.mkdir()
    argv = [sys.executable, '-B', '-S', str(copy / 'tests/lib/native_sources.py'), '--builddir', str(copy / 'builddir'), '--root', str(copy)]
    result = subprocess.run(argv, cwd=copy, capture_output=True, text=True, timeout=60)
    (evidence / 'stdout').write_text(result.stdout)
    (evidence / 'stderr').write_text(result.stderr)
    diagnostic = f'builddir: configured for {repo.resolve()}, not {copy.resolve()}'
    record = dict(scenario='configured-copied-checkout', argv=argv, returncode=result.returncode,
                  expected_returncode=1, expected_diagnostic=diagnostic)
    (evidence / 'command.json').write_text(json.dumps(record, indent=2) + '\n')
    if result.returncode != 1 or diagnostic not in result.stderr:
        raise AssertionError(f'copied checkout: unexpected configured check result: {record}\n{result.stdout}\n{result.stderr}')
    receipts.append(record)
    return receipts


def inventory_controls(out):
    """Discovery is a pruned walk with the documented scope semantics.

    An independently specified fixture holds nested and untracked files, prefix
    near misses, a root and a nested `builddir`, hidden files and directories,
    paths the Markdown and shell scopes treat differently, file, directory and
    broken symlinks, a directory named with the suffix, an unreadable selected
    input and large excluded subtrees. The rules' own discovery must select
    exactly the listed entries in lexical order, and an independent instrument
    on directory enumeration must show the excluded subtrees were never entered."""
    import os
    import tempfile
    import time
    sys.path.insert(0, str(ROOT / 'tests/suites/source_drift'))
    import check  # noqa: E402
    import direct_python  # noqa: E402
    import repository_tree  # noqa: E402
    # The fixture is scratch, not evidence: it holds a `runner/.build` directory and large excluded
    # subtrees that the harness would refuse under artifacts. The receipt lists every created path.
    scratch = os.environ.get('PW_TEST_SCRATCH')
    if scratch:
        Path(scratch).mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix='inventory-', dir=scratch))
    created = ['README.md', 'README.MD', 'notes.markdown', 'builddir.md', 'build.sh',
               'nested/untracked.md', 'nested/deeper/leaf.md', 'nested/.hidden.md', 'nested/.hidden/b.md',
               'nested/builddir/a.md', '.hidden/a.md', '.tmp/a.md', 'records/a.md', 'records-old/keep.md',
               'builddir/a.md', 'builddir-old/a.md', 'dist/PolicyWitness.md', 'dist/archive/a.md',
               'dist/archive-old/keep.md', 'dist/evidence/a.md', 'controller/target/a.md',
               'controller/targets/keep.md', 'tests/lib/vendor/a.md', 'tests/lib/vendor/keep.sh',
               'tests/lib/vendored/keep.md', 'runner/.build/a.md', 'directory.md/inner.md',
               'tests/out/hidden.md', 'tests/out/drop.sh', 'tests/output/keep.md', 'tests/output/keep.sh',
               'tests/run.sh', 'tests/.hidden/keep.sh', 'tests/nested/out/keep.sh', 'tests/suites/x/run.sh',
               'tests/dir.sh/inner.sh', 'tests/notes.md']
    for name in created:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'{name}\n')
    large = {}
    for index in range(300):
        case = root / f'tests/out/runs/run-{index:03d}/suites/source_drift/case'
        case.mkdir(parents=True)
        (case / 'notes.md').write_text('retained output\n')
        (case / 'run.sh').write_text('retained output\n')
    for index in range(100):
        record = root / f'records/investigation-{index:03d}/evidence'
        record.mkdir(parents=True)
        (record / 'notes.md').write_text('record\n')
    for index in range(20):
        (root / f'builddir/sub-{index:02d}').mkdir()
        (root / f'builddir/sub-{index:02d}/a.md').write_text('build state\n')
    large['tests/out'] = sum(1 for _ in (root / 'tests/out').rglob('*'))
    large['records'] = sum(1 for _ in (root / 'records').rglob('*'))
    large['builddir'] = sum(1 for _ in (root / 'builddir').rglob('*'))
    (root / 'linked.md').symlink_to('README.md')
    (root / 'linked-dir').symlink_to('nested', target_is_directory=True)
    (root / 'broken.md').symlink_to('missing.md')
    (root / 'tests/linked.sh').symlink_to('run.sh')
    (root / 'tests/linked-dir').symlink_to('suites', target_is_directory=True)
    (root / 'tests/broken.sh').symlink_to('missing.sh')
    unreadable = root / 'unreadable.md'
    unreadable.write_text('secret\n')
    unreadable.chmod(0)
    expected_markdown = ['README.md', 'broken.md', 'controller/targets/keep.md', 'directory.md', 'directory.md/inner.md',
                         'dist/PolicyWitness.md', 'dist/archive-old/keep.md', 'linked.md', 'nested/builddir/a.md',
                         'nested/deeper/leaf.md', 'nested/untracked.md', 'records-old/keep.md', 'tests/lib/vendored/keep.md',
                         'tests/notes.md', 'tests/output/keep.md', 'unreadable.md']
    expected_markdown_listed = ['.', 'controller', 'controller/targets', 'directory.md', 'dist', 'dist/archive-old', 'nested',
                                'nested/builddir', 'nested/deeper', 'records-old', 'runner', 'tests', 'tests/dir.sh',
                                'tests/lib', 'tests/lib/vendored', 'tests/nested', 'tests/nested/out', 'tests/output',
                                'tests/suites', 'tests/suites/x']
    expected_shell = ['tests/.hidden/keep.sh', 'tests/broken.sh', 'tests/dir.sh', 'tests/dir.sh/inner.sh',
                      'tests/lib/vendor/keep.sh', 'tests/linked.sh', 'tests/nested/out/keep.sh', 'tests/output/keep.sh',
                      'tests/run.sh', 'tests/suites/x/run.sh']
    expected_shell_listed = ['tests', 'tests/.hidden', 'tests/dir.sh', 'tests/lib', 'tests/lib/vendor', 'tests/lib/vendored',
                             'tests/nested', 'tests/nested/out', 'tests/output', 'tests/suites', 'tests/suites/x']
    excluded_roots = {'markdown': ('tests/out', 'records', 'builddir', 'builddir-old', '.hidden', '.tmp', 'dist/archive',
                                   'dist/evidence', 'controller/target', 'tests/lib/vendor', 'runner/.build', 'nested/.hidden',
                                   'linked-dir', 'tests/linked-dir'),
                      'shell': ('tests/out', 'tests/linked-dir')}

    def observed(call):
        """Directories enumerated during the call, recorded independently of the walker's own account."""
        entered = []
        original = os.scandir

        def counted(path='.'):
            entered.append(Path(os.fspath(path)))
            return original(path)
        os.scandir = counted
        start = time.perf_counter()
        try:
            result = call()
        finally:
            os.scandir = original
        relative = [p.relative_to(root).as_posix() if p != root else '.' for p in entered]
        return result, relative, time.perf_counter() - start

    markdown_tree = repository_tree.Tree(root)
    markdown, markdown_entered, markdown_seconds = observed(lambda: check.markdown_documents(markdown_tree))
    shell, shell_entered, shell_seconds = observed(lambda: direct_python.shell_scripts(root))
    shell = [p.relative_to(root).as_posix() for p in shell]
    problems = []
    if markdown != expected_markdown:
        problems.append(f'markdown inventory {markdown} != {expected_markdown}')
    if shell != expected_shell:
        problems.append(f'shell inventory {shell} != {expected_shell}')
    for label, entered, expected in (('markdown', markdown_entered, expected_markdown_listed),
                                     ('shell', shell_entered, expected_shell_listed)):
        if sorted(entered) != expected:
            problems.append(f'{label} walk entered {sorted(entered)} != {expected}')
        roots = excluded_roots[label]
        descended = [d for d in entered if d in roots or d.startswith(tuple(r + '/' for r in roots))]
        if descended:
            problems.append(f'{label} walk entered excluded directories: {descended}')
    if sorted(markdown_tree.listed) != sorted(markdown_entered):
        problems.append(f"the tree's own account {sorted(markdown_tree.listed)} != observed {sorted(markdown_entered)}")
    for relative in ('directory.md', 'broken.md', 'unreadable.md'):
        try:
            markdown_tree.read_text(relative)
            problems.append(f'{relative}: read succeeded')
        except repository_tree.MissingInput as error:
            if relative != 'broken.md':
                problems.append(f'{relative}: {error}')
        except repository_tree.UnreadableInput as error:
            if relative == 'broken.md':
                problems.append(f'{relative}: {error}')
    try:
        markdown_tree.expand([repository_tree.required('absent.md')])
        problems.append('expand accepted a missing required input')
    except repository_tree.MissingInput:
        pass
    expanded = markdown_tree.expand([repository_tree.required('README.md'), repository_tree.optional('absent.md'),
                                     repository_tree.directory('nested', ('.md',), recursive=False),
                                     repository_tree.inventory(repository_tree.TEST_SHELL_SCRIPTS)])
    if expanded != sorted({'README.md', 'nested/.hidden.md', 'nested/untracked.md', *expected_shell}):
        problems.append(f'expand selected {expanded}')
    # A directory declared without suffixes selects every non-directory entry beneath it.
    unsuffixed = markdown_tree.expand([repository_tree.directory('nested')])
    if unsuffixed != ['nested/.hidden.md', 'nested/.hidden/b.md', 'nested/builddir/a.md', 'nested/deeper/leaf.md',
                      'nested/untracked.md']:
        problems.append(f'unsuffixed directory declaration selected {unsuffixed}')
    # An entry whose metadata cannot be read stays a candidate and discovery completes. The failure is
    # raised at the enumeration boundary the walker uses, since an unreadable parent would fail the
    # listing itself rather than one entry's metadata.
    (root / 'metadata.md').write_text('metadata\n')
    (root / 'metadata-dir').mkdir()
    (root / 'metadata-dir/inner.md').write_text('inner\n')

    class FailingEntry:
        def __init__(self, entry):
            self.name, self.path = entry.name, entry.path

        def is_dir(self, follow_symlinks=True):
            raise PermissionError(13, 'Permission denied', self.path)

    class Listing:
        def __init__(self, inner):
            self.inner = inner

        def __enter__(self):
            return self

        def __exit__(self, *_):
            self.inner.close()

        def __iter__(self):
            for entry in self.inner:
                yield FailingEntry(entry) if entry.name in ('metadata.md', 'metadata-dir') else entry

    original = os.scandir
    os.scandir = lambda path='.': Listing(original(path))
    try:
        with_failure = check.markdown_documents(repository_tree.Tree(root))
    except OSError as error:
        problems.append(f'discovery aborted on unreadable metadata: {error!r}')
        with_failure = []
    finally:
        os.scandir = original
    if with_failure != sorted(expected_markdown + ['metadata.md']):
        problems.append(f'discovery with unreadable metadata selected {with_failure}')
    for name in ('metadata.md', 'metadata-dir/inner.md'):
        (root / name).unlink()
    (root / 'metadata-dir').rmdir()
    unreadable.chmod(0o644)
    shutil.rmtree(root)
    record = dict(scenario='inventory-scopes', root=str(root), created=created, large_excluded_entries=large,
                  markdown=dict(selected=markdown, entered=markdown_entered, seconds=markdown_seconds),
                  shell=dict(selected=shell, entered=shell_entered, seconds=shell_seconds),
                  expanded=expanded, problems=problems)
    (out / 'inventory-controls.json').write_text(json.dumps(record, indent=2) + '\n')
    if problems:
        raise AssertionError('inventory controls: ' + '\n'.join(problems))
    return [dict(scenario='inventory-scopes', expected_returncode=None, returncode=None,
                 expected_diagnostic=None, markdown_entered=len(markdown_entered), shell_entered=len(shell_entered))]


def precondition_scenarios(repo, out):
    """A shared bad input blocks exactly the rules that read it, each with its own record, while every other rule
    runs: the suite-coverage heading is removed and a host binding is added in one scenario, and a later rule's
    nonzero finding proves the dispatcher continued past the precondition failures."""
    readme = repo / 'tests/README.md'
    host = repo / HOST
    originals = {path: path.read_text() for path in (readme, host)}
    assert originals[readme].count('## Suite coverage') == 1, 'fixture requires the suite coverage heading'
    declared = declared_rules(repo)
    assert len(declared) == 19, declared
    receipts = []

    def scenario(name, mutate, expect):
        for path, text in originals.items():
            path.write_text(text)
        mutate()
        evidence = out / name
        evidence.mkdir()
        for path in originals:
            captured = evidence / path.relative_to(repo)
            captured.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, captured)
        argv, result, reported, integrity = run_checker(repo, evidence)
        outcomes = {r['rule_id']: r for r in reported['results']} if reported else {}
        record = dict(scenario=name, argv=argv, returncode=result.returncode, integrity=integrity,
                      outcomes={rule_id: r['outcome'] for rule_id, r in outcomes.items()},
                      records={rule_id: r['problems'] for rule_id, r in outcomes.items() if r['problems']})
        (evidence / 'command.json').write_text(json.dumps(record, indent=2) + '\n')
        problems = expect(result, outcomes) + integrity
        if problems:
            raise AssertionError(f'{name}: {problems}\n{result.stdout}\n{result.stderr}')
        receipts.append(record)

    def combined():
        readme.write_text(originals[readme].replace('## Suite coverage', '## Missing coverage', 1))
        host.write_text(originals[host] + '\n' + HOST_BINDING + '\n')

    def expect_combined(result, outcomes):
        problems = []
        blocked = sorted(rule_id for rule_id, r in outcomes.items() if r['outcome'] == 'input_blocked')
        evaluated = [rule_id for rule_id, r in outcomes.items() if r['outcome'] == 'evaluated']
        if result.returncode != 2:
            problems.append(f'status {result.returncode} != 2')
        if blocked != ['baseline_in_catalog_defaults', 'index_vs_disk']:
            problems.append(f'input_blocked {blocked}')
        for rule_id in blocked:
            records = outcomes[rule_id]['problems']
            if (len(records) != 1 or records[0]['key'] != 'section.missing' or records[0]['path'] != 'tests/README.md'
                    or records[0]['severity'] != 'precondition'):
                problems.append(f'{rule_id} records {records}')
        if len(outcomes) != 19 or len(evaluated) != 17:
            problems.append(f'{len(outcomes)} rules reported, {len(evaluated)} evaluated')
        host_records = outcomes.get('host_invariance', {}).get('problems', [])
        if not any(r['key'] == 'host.native_use' and r['path'] == HOST.as_posix() for r in host_records):
            problems.append(f'host diagnostic missing from the records: {host_records}')
        for text in ('the XPC host never links, loads or calls libsandbox', "tests/README.md is missing the ## 'Suite coverage' section",
                     'input_blocked: index_vs_disk, baseline_in_catalog_defaults'):
            if text not in result.stderr + result.stdout:
                problems.append(f'output lacks {text!r}')
        others = [rule_id for rule_id, r in outcomes.items() if r['problems'] and rule_id not in blocked and rule_id != 'host_invariance']
        if others:
            problems.append(f'unexpected records from {others}')
        return problems

    def expect_restored(result, outcomes):
        problems = []
        if result.returncode != 0:
            problems.append(f'status {result.returncode} != 0')
        if len(outcomes) != 19 or any(r['outcome'] != 'evaluated' or r['problems'] for r in outcomes.values()):
            problems.append('not every rule evaluated cleanly after restoration')
        return problems

    scenario('precondition-combined', combined, expect_combined)
    scenario('precondition-restored', lambda: None, expect_restored)
    return receipts


def dispatch_omission_scenario(repo, out):
    """A dispatcher that omits a registered rule is caught by execution evidence, not by static reading: the
    mutated checker still declares the row and main() still uses the table, it passes a host binding it never
    examined, and the reported rule set lacks the declared row."""
    checker = repo / 'tests/suites/source_drift/check.py'
    host = repo / HOST
    originals = {path: path.read_text() for path in (checker, host)}
    marker = 'results = drift_rules.run_rules(tree, RULES, args.rules, refused=(markdown_reader.Refused,))'
    assert originals[checker].count(marker) == 1, 'fixture requires the current dispatcher call'
    mutated = originals[checker].replace(
        marker, "results = drift_rules.run_rules(tree, [rule for rule in RULES if rule.id != 'host_invariance'], "
                "args.rules, refused=(markdown_reader.Refused,))")
    assert any(rule_id == 'host_invariance' for rule_id, _ in generator_common.rule_declarations(mutated))
    receipts = []
    for name, texts, expect_status, expect_integrity in (
            ('dispatch-omission', {checker: mutated, host: originals[host] + '\n' + HOST_BINDING + '\n'}, 0, True),
            ('dispatch-restored', originals, 0, False)):
        for path, text in texts.items():
            path.write_text(text)
        evidence = out / name
        evidence.mkdir()
        for path in texts:
            captured = evidence / path.relative_to(repo)
            captured.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, captured)
        argv, result, reported, integrity = run_checker(repo, evidence)
        reported_ids = [r['rule_id'] for r in reported['results']] if reported else []
        record = dict(scenario=name, argv=argv, returncode=result.returncode, reported=reported_ids, integrity=integrity)
        (evidence / 'command.json').write_text(json.dumps(record, indent=2) + '\n')
        problems = []
        if result.returncode != expect_status:
            problems.append(f'status {result.returncode} != {expect_status}')
        if expect_integrity:
            if 'host_invariance' in reported_ids:
                problems.append('the omitted rule was reported')
            if not any('host_invariance' in line for line in integrity):
                problems.append(f'the integrity check did not name the omitted rule: {integrity}')
        elif integrity or len(reported_ids) != 19:
            problems.append(f'restored dispatcher: {integrity} {reported_ids}')
        if problems:
            raise AssertionError(f'{name}: {problems}\n{result.stdout}\n{result.stderr}')
        receipts.append(record)
    return receipts


def isolation_controls(out):
    """Fresh trees observe current bytes: two roots sharing a relative path give their own records in either
    order, a same-size rewrite with its mtime restored is seen, and a deleted input blocks the rule until it
    is recreated. The rule is called in process over each root."""
    import os
    import tempfile
    sys.path.insert(0, str(ROOT / 'tests/suites/source_drift'))
    import check  # noqa: E402
    import repository_tree  # noqa: E402
    scratch = os.environ.get('PW_TEST_SCRATCH')
    if scratch:
        Path(scratch).mkdir(parents=True, exist_ok=True)
    base = Path(tempfile.mkdtemp(prefix='isolation-', dir=scratch))
    rule = next(r for r in check.RULES if r.id == 'cli_surface_agreement')
    roots = {}
    for name in ('a', 'b'):
        root = base / name
        for relative in (check.CLI_RS, check.CONTROLLER_README):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        roots[name] = root
    original = (roots['a'] / check.CONTROLLER_README).read_text()
    line = next(l for l in original.splitlines() if l.startswith('policy-witness '))
    altered = line[:-1] + ('X' if line[-1] != 'X' else 'Y')
    (roots['b'] / check.CONTROLLER_README).write_text(original.replace(line, altered, 1))

    def observe(root):
        result = drift_rules.attempt(repository_tree.Tree(root), rule, refused=(check.markdown_reader.Refused,))
        return [result.outcome, sorted({p.key for p in result.problems})]

    clean, mismatch = ['evaluated', []], ['evaluated', ['cli.mismatch']]
    observations = {'a_then_b': [observe(roots['a']), observe(roots['b'])],
                    'b_then_a': [observe(roots['b']), observe(roots['a'])]}
    readme_a = roots['a'] / check.CONTROLLER_README
    before = readme_a.stat()
    readme_a.write_text(original.replace(line, altered, 1))
    os.utime(readme_a, ns=(before.st_atime_ns, before.st_mtime_ns))
    after = readme_a.stat()
    observations['same_size_mtime_restored'] = observe(roots['a'])
    observations['same_size_identity'] = dict(size_unchanged=after.st_size == before.st_size,
                                              mtime_unchanged=after.st_mtime_ns == before.st_mtime_ns)
    readme_a.write_text(original)
    observations['rewritten_back'] = observe(roots['a'])
    readme_a.unlink()
    observations['deleted'] = observe(roots['a'])
    readme_a.write_text(original)
    observations['recreated'] = observe(roots['a'])
    shutil.rmtree(base)
    expected = {'a_then_b': [clean, mismatch], 'b_then_a': [mismatch, clean], 'same_size_mtime_restored': mismatch,
                'same_size_identity': dict(size_unchanged=True, mtime_unchanged=True), 'rewritten_back': clean,
                'deleted': ['input_blocked', ['input.missing']], 'recreated': clean}
    problems = [f'{name}: {observations[name]} != {expected[name]}' for name in expected if observations[name] != expected[name]]
    record = dict(scenario='isolation-fresh-trees', rule=rule.id, observations=observations, problems=problems)
    (out / 'isolation-controls.json').write_text(json.dumps(record, indent=2) + '\n')
    if problems:
        raise AssertionError('isolation controls: ' + '; '.join(problems))
    return [dict(scenario='isolation-fresh-trees', expected_returncode=None, returncode=None, expected_diagnostic=None)]


def host_invariance_controls(out):
    """Controls distinguish native use from schema, prose and unrelated APIs; they test the rule, once per case."""
    sys.path.insert(0, str(ROOT / 'tests/suites/source_drift'))
    import check  # noqa: E402
    accepted = [
        'let name = "sandbox_check(pid) and dlopen(x) are examples"',
        '// sandbox_apply(p)\n/* outer /* sandbox_free_error(e) */ dlsym(h, "sandbox_check") */',
        'var sandbox_check: PWRunnerSandboxCheckResult\nenum CodingKeys { case sandbox_check }',
        'let label = "sandbox_check"\nlet policy = """\n(allow default)\n"""',
        'let f: @convention(c) (Int32) -> Int32 = ptr',
        'let h = dlopen("/usr/lib/libSystem.B.dylib", RTLD_NOW)',
        'let f = dlsym(h, "malloc")',
        'let library = "/usr/lib/libSystem.B.dylib"\nlet h = dlopen(library, RTLD_NOW)',
        'let name: String = "malloc"\nlet f = dlsym(h, name)',
        '@_silgen_name("posix_spawn") func spawn() -> Int32',
        'let example = #"dlopen("/usr/lib/libsandbox.dylib", RTLD_NOW)"#',
    ]
    rejected = []
    for name in sorted(check.HOST_SANDBOX_SYMBOLS):
        rejected += [
            f'{name}(value)',
            f'int {name}(void *value);',
            f'@_silgen_name("{name}") func native() -> Int32',
            f'let f = dlsym(handle, "{name}")',
            f'let symbol: String = "{name}"\nlet f = dlsym(handle, symbol)',
            f'const char *symbol = "{name}"; void *f = dlsym(handle, symbol);',
            f'#define SYMBOL "{name}"\nvoid *f = dlsym(handle, SYMBOL);',
        ]
    rejected += [
        'let h = dlopen("/usr/lib/libsandbox.dylib", RTLD_NOW)',
        'let library = "/usr/lib/libsandbox.1.dylib"\nlet h = dlopen(library, RTLD_NOW)',
        'const char *library = "/usr/lib/libsandbox.dylib"; void *h = dlopen(library, RTLD_NOW);',
        '@_silgen_name(#"sandbox_check"#) func native() -> Int32',
        'extern int native(void) __asm__("sandbox_check");',
    ]
    problems = []
    outcomes = []
    for expected, snippets in ((False, accepted), (True, rejected)):
        for snippet in snippets:
            found = check.host_invariance_problems('control', snippet)
            outcomes.append(dict(snippet=snippet, expected_rejection=expected, records=[p.message for p in found]))
            if bool(found) != expected:
                problems.append(f'expected rejection={expected}: {snippet!r}: {found}')
    record = dict(scenario='host-invariance-controls', accepted=len(accepted), rejected=len(rejected), outcomes=outcomes, problems=problems)
    (out / 'host-invariance-controls.json').write_text(json.dumps(record, indent=2) + '\n')
    if problems:
        raise AssertionError('host invariance controls: ' + '; '.join(problems))
    return [dict(scenario='host-invariance-controls', expected_returncode=None, returncode=None, expected_diagnostic=None)]


if __name__ == '__main__':
    main(Path(sys.argv[1]))
