"""Run the real drift rules against disposable source and guidance mutations.

Each scenario mutates a copy of the checker's inputs, builds a fresh tree over
the copy and calls only the rules it names, in process, asserting the complete
record set of every named rule. The entry point itself is exercised by a few
subprocess scenarios: the baseline, independent faults in several rules, a
reader refusal and a precondition failure beside an independent fault, a
dispatcher that omits a registered rule, and restoration. The configured-native
controls on the real Meson boundary are `preflight/native_source_controls`.
"""
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'docs'))
import markdown_reader  # noqa: E402  (its file list and refusal; the fixtures below read Markdown themselves)
import generator_common  # noqa: E402  (static reading of the checker's RULES table)
import drift_rules  # noqa: E402
import fixture_inputs  # noqa: E402
import receipts as receipt_files  # noqa: E402
import repository_tree  # noqa: E402
from repository_tree import directory, required  # noqa: E402
sys.path.insert(0, str(ROOT / 'tests/suites/source_drift'))
import check  # noqa: E402  (the rule implementation; every scenario hands it a fixture tree)

HOST = Path('runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift')
PLANNER_SOURCE = Path('runner/Sources/PWRunnerCore/CWorkerRequestPlanning.swift')
CALL = 'if predictionUnavailableOpFilters.contains(PredictionUnavailablePair(operation: check.operation, filterKind: kind)) {'
HOST_BINDING = '@_silgen_name("sandbox_check") func forbidden() -> Int32'
RULES_BY_ID = {rule.id: rule for rule in check.RULES}
REFUSED = (markdown_reader.Refused,)

# Rule IDs the scenarios name.
PLANNER = 'prediction_unavailable_planner'
HOSTS = 'host_invariance'
MESON = 'meson_source_lists'
GUIDANCE = 'harness_guidance_routes'
GAPS = 'known_gap_index'
COMMANDS = 'no_direct_case_commands_in_docs'
RELEASE = 'release_production_runs_the_default_battery'
INDEX = 'index_vs_disk'
README = 'readmes_present'
CATALOG_COMMANDS = 'run_scripts_are_catalog_commands'
BASELINE = 'baseline_in_catalog_defaults'
NORMALIZED = 'normalized_outcomes_have_matrix_rows'
SUITE_ROWS = 'runner_outcome_suites_have_matrix_rows'
ATTEMPTS = 'attempt_outcomes_have_matrix_rows'
KINDS = 'attempt_kind_enum_agreement'
PAIRS = 'prediction_unavailable_agreement'
OVERRIDES = 'test_overrides_table_agreement'
CLI = 'cli_surface_agreement'
EVIDENCE = 'evidence_channel_paths'


@dataclass
class Scenario:
    """One mutation of the fixture and the complete records each named rule must produce over it."""
    name: str
    changes: dict                 # relative Path -> text
    expected: dict                # rule ID -> expected record keys (compared as multisets)
    diagnostic: str = None        # a substring some record's message must carry
    exact: dict = field(default_factory=dict)  # rule ID -> the exact ordered messages, where the key alone is not enough


# The checker itself and what its command imports, plus what file-mode Meson introspection needs beyond the
# rules' declared inputs: the manifest options, every C source and header of the native targets and the runner
# sources the manifest names, and the worker identity generator the native sources reader imports.
FIXTURE_INPUTS = (required('tests/suites/source_drift/check.py'), required('docs/repository_tree.py'),
                  required('tests/lib/drift_rules.py'), required('meson.options'),
                  directory('controller/tools/pw_probe_runner', ('.c', '.h')),
                  directory('controller/tools/sb_api_validator', ('.c', '.h')), directory('runner/Sources'),
                  required('tests/lib/native_sources.py'), required('docs/generate_worker_identity.py'))


def fixture(out):
    """A copy of only the declared inputs of the checker's rules and its command; never build products or
    previous runs. The receipt records what was copied and what it cost."""
    repo = out / 'repo'
    paths = set(fixture_inputs.rule_inputs(ROOT, check.RULES)) | set(fixture_inputs.expand(ROOT, FIXTURE_INPUTS))
    copied = fixture_inputs.copy_declared(ROOT, repo, paths)
    (out / 'fixture.json').write_text(json.dumps(dict(paths=sorted(paths), files=copied.files, directories=copied.directories,
                                                      bytes=copied.bytes, seconds=copied.seconds), indent=2) + '\n')
    return repo


def main(out):
    out.mkdir()
    file = receipt_files.Receipts(out / 'controls.json', 'source_drift/runner_source_manifests_agree', 'planner')
    repo = fixture(out)
    file.add(scenario='fixture', mode='fixture', **json.loads((out / 'fixture.json').read_text()) | {'paths': None})
    scenarios = (planner_scenarios(repo) + host_scenarios(repo) + meson_scenarios(repo) + guidance_scenarios(repo)
                 + structure_scenarios(repo) + gap_scenarios(repo) + route_scenarios(repo) + rule_gap_scenarios(repo))
    names = [scenario.name for scenario in scenarios]
    assert len(names) == len(set(names)), 'scenario names must be unique'
    receipts = []
    try:
        for group in (lambda: run_scenarios(repo, out, scenarios, file),
                      lambda: reversed_order_control(repo, out, scenarios, receipts),
                      lambda: registry_scenarios(repo, out), lambda: entry_point_scenarios(repo, out),
                      lambda: precondition_scenarios(repo, out), lambda: dispatch_omission_scenario(repo, out),
                      lambda: inventory_controls(out), lambda: isolation_controls(out), lambda: host_invariance_controls(out)):
            produced = group()
            receipts += produced
            file.extend(record for record in produced if record.get('scenario') not in {c.get('scenario') for c in file.controls})
    except BaseException:
        file.finish(ok=False, complete=False)
        raise
    file.finish(ok=True)
    print(f'{len(receipts)} source and guidance controls passed')


# ---------------------------------------------------------------------------
# In-process evaluation
# ---------------------------------------------------------------------------

def evaluate(repo, rule_ids):
    """A fresh tree over the fixture and only the named rules; records as plain data."""
    tree = repository_tree.Tree(repo)
    actual = {}
    for rule_id in rule_ids:
        result = drift_rules.attempt(tree, RULES_BY_ID[rule_id], refused=REFUSED)
        actual[rule_id] = dict(outcome=result.outcome,
                               records=[dict(key=p.key, path=p.path, line=p.line, severity=p.severity, message=p.message)
                                        for p in result.problems])
    return actual


def compare(scenario, actual):
    """Every named rule's records against the scenario's complete expectation."""
    problems = []
    for rule_id, keys in scenario.expected.items():
        got = actual[rule_id]['records']
        if rule_id in scenario.exact:
            if [r['message'] for r in got] != scenario.exact[rule_id]:
                problems.append(f'{rule_id}: messages {[r["message"] for r in got]} != {scenario.exact[rule_id]}')
        elif sorted(r['key'] for r in got) != sorted(keys):
            problems.append(f'{rule_id}: keys {sorted(r["key"] for r in got)} != {sorted(keys)}')
        blocked = any(r['severity'] == 'precondition' for r in got)
        if blocked != (actual[rule_id]['outcome'] == 'input_blocked'):
            problems.append(f'{rule_id}: outcome {actual[rule_id]["outcome"]} disagrees with its records')
    if scenario.diagnostic and not any(scenario.diagnostic in r['message'] for rule in actual.values() for r in rule['records']):
        problems.append(f'no record carries {scenario.diagnostic!r}')
    return problems


def run_scenarios(repo, out, scenarios, file=None):
    originals = {path: (repo / path).read_text() for scenario in scenarios for path in scenario.changes}
    receipts = []
    for scenario in scenarios:
        evidence = out / scenario.name
        evidence.mkdir()
        for path, source in originals.items():
            (repo / path).write_text(source)
        for path, source in scenario.changes.items():
            (repo / path).write_text(source)
            captured = evidence / path
            captured.parent.mkdir(parents=True, exist_ok=True)
            captured.write_text(source)
        start = time.perf_counter()
        actual = evaluate(repo, scenario.expected)
        elapsed = time.perf_counter() - start
        problems = compare(scenario, actual)
        record = dict(scenario=scenario.name, mode='in-process', rules=list(scenario.expected),
                      changed=[path.as_posix() for path in scenario.changes], expected=scenario.expected,
                      exact=scenario.exact or None, diagnostic=scenario.diagnostic, actual=actual,
                      elapsed_seconds=elapsed, problems=problems)
        (evidence / 'records.json').write_text(json.dumps(record, indent=2) + '\n')
        if file is not None:
            file.add(**record)
        if problems:
            raise AssertionError(f'{scenario.name}: ' + '\n'.join(problems) + '\n' + json.dumps(actual, indent=2))
        receipts.append(record)
    for path, source in originals.items():
        (repo / path).write_text(source)
        if (ROOT / path).read_text() != source:
            raise AssertionError(f'source controls changed the working input: {path}')
    return receipts


def reversed_order_control(repo, out, scenarios, forward):
    """The same scenarios in reverse order give the same records: nothing survives from one tree to the next."""
    originals = {path: (repo / path).read_text() for scenario in scenarios for path in scenario.changes}
    expected = {record['scenario']: record['actual'] for record in forward}
    mismatches = []
    for scenario in reversed(scenarios):
        for path, source in originals.items():
            (repo / path).write_text(source)
        for path, source in scenario.changes.items():
            (repo / path).write_text(source)
        if evaluate(repo, scenario.expected) != expected[scenario.name]:
            mismatches.append(scenario.name)
    for path, source in originals.items():
        (repo / path).write_text(source)
    record = dict(scenario='reversed-order', mode='in-process', compared=len(scenarios), mismatches=mismatches)
    (out / 'reversed-order.json').write_text(json.dumps(record, indent=2) + '\n')
    if mismatches:
        raise AssertionError(f'reversed order changed the records of {mismatches}')
    return [record]


# ---------------------------------------------------------------------------
# Scenario builders
# ---------------------------------------------------------------------------

def planner_scenarios(repo):
    """The host planner must consume the shared exclusion set and nothing else."""
    original = (repo / PLANNER_SOURCE).read_text()
    if original.count(CALL) != 1:
        raise AssertionError('fixture requires the current planner membership condition')
    assert original.count('func planValidatorQueries(') == 1, 'fixture requires the planner definition'
    mirror = '''
private let hostExclusions: Set<PredictionUnavailablePair> = [
    .init(operation: "iokit-open-service", filterKind: PWRunnerWire.sandboxFilterIokitRegistryEntryClass),
    .init(operation: "iokit-open-user-client", filterKind: PWRunnerWire.sandboxFilterIokitUserClientClass),
    .init(operation: "sysctl-read", filterKind: PWRunnerWire.sandboxFilterSysctlName),
]
'''
    no_call = original.replace(CALL, 'if false {')
    local, missing, clean = ['planner.local_table'], ['planner.missing_contains'], []
    table = 'must not define a local exclusion table'
    contains = 'planValidatorQueries must use'
    rows = [
        ('baseline', original, clean, None),
        ('mirror-three', original.replace(CALL, CALL.replace('predictionUnavailableOpFilters', 'hostExclusions')) + mirror,
         local + missing, table),
        ('mirror-four', original + mirror.replace('\n]', '\n    .init(operation: "file-read-data", filterKind: PWRunnerWire.sandboxFilterPath),\n]'),
         local, table),
        ('inferred-literal-table', original + '\nlet hostExclusions = [PredictionUnavailablePair(operation: "file-read-data", filterKind: PWRunnerWire.sandboxFilterPath)]\n',
         local, table),
        ('shadow-shared', original.replace(CALL, 'let predictionUnavailableOpFilters = knownFilterKinds\n        ' + CALL),
         local, 'shadow the shared set'),
        ('missing-call', no_call, missing, contains),
        ('missing-function', original.replace('func planValidatorQueries(', 'func absentPlanner(', 1),
         ['planner.missing_function'], 'could not locate planValidatorQueries'),
        ('comment-only-call', no_call.replace('if false {', '// ' + CALL + '\n        if false {'), missing, contains),
        ('nested-comment-only-call', no_call.replace('if false {', '/* outer /* nested */ ' + CALL + ' */ if false {'), missing, contains),
        ('string-only-call', no_call.replace('if false {', 'let example = "' + CALL + '"\n        if false {'), missing, contains),
        ('other-function-call', no_call + '\nfunc unrelated() {\n    ' + CALL + '\n    }\n}\n', missing, contains),
        ('formatting', original.replace(CALL, CALL.replace('if ', 'if\n            ').replace('.contains(', ' . contains (\n')), clean, None),
        ('commented-table', original + '\n/* example /* nested */\n' + mirror + '\n*/\n', clean, None),
        ('string-table', original + '\nlet example = """\n' + mirror + '\n"""\n', clean, None),
        ('restored', original, clean, None),
    ]
    scenarios = [Scenario(name, {PLANNER_SOURCE: source}, {PLANNER: keys}, diagnostic) for name, source, keys, diagnostic in rows]
    comparison = Path('runner/Sources/PWRunnerCore/CWorkerComparison.swift')
    comparison_source = (repo / comparison).read_text()
    scenarios += [
        Scenario('table-in-extracted-owner', {comparison: comparison_source + mirror}, {PLANNER: local}, table),
        Scenario('malformed-extracted-owner', {comparison: comparison_source + '\nlet malformed = "'},
                 {PLANNER: ['planner.unterminated_string']}, 'unterminated Swift string in planner guard'),
        Scenario('extracted-owner-restored', {comparison: comparison_source}, {PLANNER: clean}),
    ]
    return scenarios


def host_scenarios(repo):
    """File mutations of the host and the C shim, beside the constructed-snippet controls run once per case."""
    original = (repo / HOST).read_text()
    shim = Path('runner/Sources/PWCWorkerShim/PWCWorkerShim.c')
    shim_original = (repo / shim).read_text()
    native = 'the XPC host never links, loads or calls libsandbox'
    rows = [
        ('host-binding', HOST, original, HOST_BINDING, ['host.native_use']),
        ('host-unrelated-api', HOST, original,
         'let callback: @convention(c) (Int32) -> Int32 = ptr\nlet h = dlopen("/usr/lib/libSystem.B.dylib", RTLD_NOW)', []),
        ('shim-sandbox-call', shim, shim_original, 'void forbidden(void) { sandbox_free_error(0); }', ['host.native_use']),
        ('shim-symbol-constant', shim, shim_original,
         'const char *symbol = "sandbox_check"; void *f = dlsym(handle, symbol);', ['host.native_use']),
        ('shim-explanatory-string', shim, shim_original, 'const char *example = "sandbox_check(pid)";', []),
    ]
    return [Scenario(name, {path: source + '\n' + snippet + '\n'}, {HOSTS: keys}, native if keys else None)
            for name, path, source, snippet, keys in rows]


def meson_scenarios(repo):
    """The Meson reader on real file-mode introspection: a core file dropped from or added to the PWRunner
    target is named by the diff; the client requires shared contract sources and excludes host processing;
    a missing host or shim target is named as such."""
    manifest = Path('meson.build')
    original = (repo / manifest).read_text()
    core_line = "    'runner/Sources/PWRunnerCore/PathUtils.swift',\n"
    assert original.count(core_line) == 1, 'fixture requires the current PWRunner source list'
    host_declaration = original[original.index("pwrunner = executable('PWRunner',"):]
    host_declaration = host_declaration[:host_declaration.index('endif')]
    decoy = ('\nif false\n' + host_declaration.replace('pwrunner = ', 'pwrunner_decoy = ').rstrip() + '\nendif\n')
    worker_line = "  files('controller/tools/pw_probe_runner/pw_probe_runner.c'),"
    assert original.count(worker_line) == 1
    client_line = "    pwrunner_contract, files('runner/Clients/PWRunnerClient/main.swift', 'runner/Clients/PWRunnerClient/PWRunnerClientSession.swift'),"
    assert original.count(client_line) == 1, 'fixture requires the explicit client contract boundary'
    client_without_coding = [
        'PWRunnerAPI', 'PWRunnerTransport', 'PWRunnerRequest', 'PWRunnerExtension',
        'PWRunnerPathEvidence', 'PWRunnerAttemptEvidence', 'PWRunnerPredictionEvidence',
        'PWRunnerStepEvidence', 'PWRunnerLifecycleEvidence', 'PWRunnerDisposition',
        'PWRunnerProfileCapture', 'PWRunnerReply',
    ]
    client_without_coding_line = '    files(' + ', '.join(
        repr('runner/Sources/PWRunnerCore/' + name + '.swift') for name in client_without_coding
    ) + ", 'runner/Clients/PWRunnerClient/main.swift', 'runner/Clients/PWRunnerClient/PWRunnerClientSession.swift'),"
    rows = [
        ('meson-core-file-dropped', original.replace(core_line, ''),
         ["  meson.build: PWRunner lacks 'runner/Sources/PWRunnerCore/PathUtils.swift' which is in the tree"]),
        ('meson-core-file-added', original.replace(core_line, core_line + "    'runner/Sources/PWRunnerCore/Missing.swift',\n"),
         ["  meson.build: PWRunner has 'runner/Sources/PWRunnerCore/Missing.swift' which the tree does not expect"]),
        ('meson-client-shared-file-dropped', original.replace(client_line,
            client_without_coding_line),
         ["  meson.build: pw-runner-client lacks 'runner/Sources/PWRunnerCore/PWRunnerCoding.swift' which is in the tree"]),
        ('meson-client-host-file-added', original.replace(client_line,
            "    pwrunner_contract, files('runner/Sources/PWRunnerCore/CWorkerDisposition.swift', 'runner/Clients/PWRunnerClient/main.swift', 'runner/Clients/PWRunnerClient/PWRunnerClientSession.swift'),"),
         ["  meson.build: pw-runner-client has 'runner/Sources/PWRunnerCore/CWorkerDisposition.swift' which the tree does not expect"]),
        ('meson-host-target-missing', original.replace("executable('PWRunner',", "executable('PWRunnerRenamed',"),
         ["  meson.build: unexpected target 'PWRunnerRenamed'", "  meson.build: no 'PWRunner' target"]),
        ('meson-shim-target-missing', original.replace("static_library('PWCWorkerShim',", "static_library('PWCWorkerShimRenamed',"),
         ["  meson.build: unexpected target 'PWCWorkerShimRenamed'", "  meson.build: no 'PWCWorkerShim' target"]),
        # A dead declaration with the complete list beside a live one missing a
        # file: the duplicate name is refused instead of resolved.
        ('meson-duplicate-host-declaration', original.replace(core_line, '') + decoy,
         ["  meson.build: declares 'PWRunner' 2 times; a target name must be declared once",
          "  meson.build: no 'PWRunner' target"]),
        ('meson-worker-source-substituted',
         original.replace(worker_line, "  files('controller/tools/pw_probe_runner/substitute/pw_probe_runner.c'),"),
         ["  meson.build: pw-probe-runner lacks 'controller/tools/pw_probe_runner/pw_probe_runner.c' which is in the tree",
          "  meson.build: pw-probe-runner has 'controller/tools/pw_probe_runner/substitute/pw_probe_runner.c' which the tree does not expect"]),
        ('meson-restored', original, []),
    ]
    scenarios = []
    for name, mutated, messages in rows:
        assert name == 'meson-restored' or mutated != original, name
        scenarios.append(Scenario(name, {manifest: mutated}, {MESON: ['meson.source_list'] * len(messages)}, exact={MESON: messages}))
    return scenarios


# The reader shapes the guidance rule still exercises at the rule layer: every body shape for one level-2 and
# one level-3 document, every route shape for one target. The other documents' and targets' repetitions are
# literal expectations in markdown.py.
BODY_SHAPES = ('fenced-body', 'comment-body', 'indented-body', 'fenced-section', 'comment-section', 'body-after-peer',
               'body-after-parent', 'short-fence-close', 'fake-heading-before-real')
ROUTE_SHAPES = ('fenced', 'comment', 'inline-example', 'image', 'code-label', 'code-label-example', 'wrapped-label',
                'split-label', 'indented-continuation', 'indented-example', 'indented-after-heading', 'list-continuation')
BODY_SHAPE_DOCUMENTS = ('AGENTS.md', 'tests/AGENTS.md')   # a level-2 and a level-3 section
ROUTE_SHAPE_TARGET = 'runner/AGENTS.md'


def guidance_scenarios(repo):
    """Exercise local sections and diagnostic routes without comparing wording."""
    paths = [Path(p) for p in ('AGENTS.md', 'runner/AGENTS.md', 'tests/AGENTS.md', 'docs/BUILD.md')]
    documents = {path: (repo / path).read_text() for path in paths}
    scenarios = []
    heading = 'Sandboxed automation harnesses'
    count, empty, route = ['guidance.heading_count'], ['guidance.empty'], ['guidance.missing_route']
    root_bounds = None
    levels = {}
    for path, source in documents.items():
        match = re.search(r'^(#{2,6}) ' + heading + r'\n', source, re.M)
        assert match, f'fixture requires the warning in {path}'
        start = match.end()
        level = len(match[1])
        levels[path.as_posix()] = level
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
            ('rewritten', body_change(independent), [], None),
            ('rewrapped', body_change('\n' + ' '.join(body.split()) + '\n\n'), [], None),
            ('reordered', body_change('\n' + '\n\n'.join(reversed(paragraphs)) + '\n\n'), [], None),
            ('local-prose', body_change(body + 'Local diagnostic control.\n\n'), [], None),
            ('heading-missing', source[:match.start()] + source[end:], count, diagnostic + ' expected one'),
            ('heading-duplicate', body_change(body + match[0] + '\nDuplicate guidance.\n\n'), count, diagnostic + ' expected one'),
            ('empty', body_change('\n\n'), empty, diagnostic + ' empty'),
            ('headings-only', body_change('\n' + '#' * (level + 1) + ' Local topic\n\n'), empty, diagnostic + ' empty'),
            ('fenced-body', body_change('\n```text\n' + body + '\n```\n\n'), empty, diagnostic + ' empty'),
            ('comment-body', body_change('\n<!--\n' + body + '\n-->\n\n'), empty, diagnostic + ' empty'),
            ('indented-body', body_change('\n' + '\n'.join('    ' + line for line in body.splitlines()) + '\n\n'), empty, diagnostic + ' empty'),
            ('fenced-section', source[:match.start()] + '~~~~text\n' + section + '\n~~~~\n\n' + source[end:], count, diagnostic + ' expected one'),
            ('comment-section', source[:match.start()] + '<!--\n' + section + '\n-->\n\n' + source[end:], count, diagnostic + ' expected one'),
            ('body-after-peer', body_change('\n' + '#' * level + ' Other guidance\n\n' + body), empty, diagnostic + ' empty'),
            ('body-after-parent', body_change('\n' + '#' * (level - 1) + ' Other guidance\n\n' + body), empty, diagnostic + ' empty'),
            # A fence's shorter marker does not close it, and comments in an
            # example must not hide the real section that follows.
            ('short-fence-close', body_change('\n````text\n```\n' + body + '\n````\n\n'), empty, diagnostic + ' empty'),
            ('fake-heading-before-real', source[:match.start()] + '```text\n<!--\n' + match[0] + '```\n\n' + source[match.start():], [], None),
        ]
        for kind, value, keys, message in changed:
            if kind in BODY_SHAPES and path.as_posix() not in BODY_SHAPE_DOCUMENTS:
                continue  # transferred to the reader's own expectations
            scenarios.append(Scenario(f'guidance-{kind}-{name}', {path: value}, {GUIDANCE: keys}, message))
        if path == paths[0]:
            root_bounds = (start, end)
        scenarios.append(Scenario(f'guidance-restored-{name}', {path: source}, {GUIDANCE: []}))
    assert sorted(levels[d] for d in BODY_SHAPE_DOCUMENTS) == [2, 3], levels

    root = paths[0]
    source = documents[root]
    start, end = root_bounds
    body = source[start:end]
    for target in ('runner/AGENTS.md', 'tests/AGENTS.md', 'docs/BUILD.md'):
        fragment = target + '#sandboxed-automation-harnesses'
        link = re.search(r'\[[^\]\n]+\]\(' + re.escape(fragment) + r'\)', body)[0]
        diagnostic = f'harness guidance: AGENTS.md: missing diagnostic route {fragment}'
        variants = [
            ('removed', '', route),
            ('wrong-path', link.replace(target, 'missing/AGENTS.md'), route),
            ('wrong-fragment', link.replace('#sandboxed-automation-harnesses', '#missing'), route),
            ('fenced', '\n```markdown\n' + link + '\n```\n', route),
            ('comment', '<!-- ' + link + ' -->', route),
            ('inline-example', '`' + link + '`', route),
            ('image', '!' + link, route),
            ('relabeled', '[Other diagnostic wording](' + fragment + ')', []),
            ('relative-path', link.replace(target, './' + target), []),
            ('code-label', '[`' + target + '`](' + fragment + ')', []),
            ('code-label-example', '`` [`' + target + '`](' + fragment + ') ``', route),
            ('wrapped-label', '[Wrapped diagnostic\nwording](' + fragment + ')', []),
            # Neither a label nor code within it continues across a blank line.
            ('split-label', '[Split `diagnostic\n\nwording`](' + fragment + ')', route),
            ('indented-continuation', 'continued\n    ' + link, []),
            ('indented-example', '\n\n    ' + link + '\n\n', route),
            ('indented-after-heading', '\n\n#### Example\n    ' + link + '\n\n', route),
            # A list item's content after a blank line stays in the item.
            ('list-continuation', '\n\n- Diagnostics are\n\n    ' + link + '\n\n', []),
        ]
        name = target.replace('/', '-').replace('.', '-')
        for kind, replacement, keys in variants:
            if kind in ROUTE_SHAPES and target != ROUTE_SHAPE_TARGET:
                continue  # transferred to the reader's own expectations
            changed = source[:start] + body.replace(link, replacement, 1) + source[end:]
            scenarios.append(Scenario(f'guidance-route-{kind}-{name}', {root: changed}, {GUIDANCE: keys}, diagnostic if keys else None))
        # A working link elsewhere in the root document cannot supply this route.
        moved = link + '\n\n' + source[:start] + body.replace(link, '', 1) + source[end:]
        scenarios.append(Scenario(f'guidance-route-outside-section-{name}', {root: moved}, {GUIDANCE: route}, diagnostic))
    # The pinned parser reads an inline comment containing "--" as text; the reader refuses it.
    # A word first keeps the comment inline: one that begins a line is an HTML block.
    commented = source[:start] + body.replace(link, 'see <!-- a -- b ' + link + ' -->', 1) + source[end:]
    scenarios.append(Scenario('guidance-route-unrecognized-comment', {root: commented}, {GUIDANCE: ['reader.refused']}, 'remove the "--"'))
    scenarios.append(Scenario('guidance-routes-restored', {root: source}, {GUIDANCE: []}))
    scenarios.append(Scenario('guidance-restored', documents, {GUIDANCE: []}))
    return scenarios


def structure_scenarios(repo):
    """Each table, list, fence and paragraph a rule reads stops counting inside a comment."""
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
    scenarios.append(Scenario('structure-suite-row-comment', hidden('tests/README.md', row, row.replace(f'`{name}`', f'<!-- `{name}` -->', 1)),
                              {INDEX: ['index.missing_row']}, f'tests/suites/{name}/ exists but has no row'))
    row, name = first_row('tests/COVERAGE.md', '## Normalized outcome coverage matrix')
    scenarios.append(Scenario('structure-matrix-row-comment', hidden('tests/COVERAGE.md', row, row.replace(f'`{name}`', f'<!-- `{name}` -->', 1)),
                              {NORMALIZED: ['matrix.missing_row'], SUITE_ROWS: []}, f'NormalizedOutcome.{name} has no row'))
    row, name = first_row('runner/README.md', '## Test seam: `_test_overrides`')
    scenarios.append(Scenario('structure-override-row-comment', hidden('runner/README.md', row, row.replace(f'`{name}`', f'<!-- `{name}` -->', 1)),
                              {OVERRIDES: ['test_overrides.missing_row']}, f'PWRunnerTestOverrides.{name} has no row'))
    pair = '`(iokit-open-service, iokit_registry_entry_class)`'
    scenarios.append(Scenario('structure-pair-comment', hidden('docs/PolicyWitness.md', '- ' + pair, f'- <!-- {pair} -->'),
                              {PAIRS: ['prediction.swift_only']}, "('iokit-open-service', 'iokit_registry_entry_class') in swift"))
    surface = lines('controller/README.md').index('## CLI surface (contract)')
    scenarios.append(Scenario('structure-cli-fence-comment',
                              wrapped('controller/README.md', lambda line: line == '```text', lambda line: line == '```', surface),
                              # The section's next text block, the runner subcommands, then disagrees with the usage.
                              {CLI: ['cli.mismatch']}, 'CLI surface drift between'))
    scenarios.append(Scenario('structure-known-gap-comment',
                              wrapped('docs/ARCHITECTURE.md', lambda line: line.startswith('Known gap'), lambda line: not line.strip()),
                              {GAPS: ['known_gaps.index_order']}, 'known gaps: docs/ARCHITECTURE.md: the index lists'))
    scenarios.append(Scenario('structure-evidence-table-comment',
                              wrapped('docs/ARCHITECTURE.md', lambda line: line.startswith('| Channel'), lambda line: not line.strip()),
                              {EVIDENCE: ['evidence.table_missing']}, 'evidence channels: table missing'))
    # The parser pads a short row to the header's width; an empty landing cell is still reported.
    row = next(line for line in lines('docs/ARCHITECTURE.md') if line.startswith('| Prediction |'))
    scenarios.append(Scenario('structure-evidence-short-row', hidden('docs/ARCHITECTURE.md', row, '|'.join(row.split('|')[:4]) + '|'),
                              {EVIDENCE: ['evidence.no_landing']}, 'evidence channels: row has no landing column'))
    scenarios.append(Scenario('structure-known-gap-ordered-index',
                              hidden('docs/ARCHITECTURE.md', '- [Why these processes exist](#', '1. [Why these processes exist](#'),
                              {GAPS: ['known_gaps.index_entry']}, 'an index bullet must open with a link'))
    return scenarios


def gap_scenarios(repo):
    """Exercise every tour's paragraph/index ownership."""
    scenarios = []
    for name in ('ARCHITECTURE', 'BUILD', 'WORKER'):
        path = Path(f'docs/{name}.md')
        source = (repo / path).read_text()
        heading = '## Known gaps'
        assert source.count(heading) == 1
        added = source.replace(heading, '## Gap control\n\nKnown gap: controlled incomplete guarantee.\n\n' + heading)
        indexed = added.rstrip() + '\n- [Gap control](#gap-control): controlled guarantee.\n'
        label = f'known gaps: docs/{name}.md'
        scenarios.extend([
            Scenario(f'gap-unindexed-{name}', {path: added}, {GAPS: ['known_gaps.index_order']}, label),
            Scenario(f'gap-indexed-{name}', {path: indexed}, {GAPS: []}),
            Scenario(f'gap-heading-missing-{name}', {path: source.replace(heading, '## Other ending')}, {GAPS: ['known_gaps.final_section']}, label),
            Scenario(f'gap-spurious-index-{name}', {path: source.rstrip() + '\n- [Gap control](#gap-control)\n'}, {GAPS: ['known_gaps.index_order']}, label),
            Scenario(f'gap-restored-{name}', {path: source}, {GAPS: []}),
        ])
    return scenarios


def route_scenarios(repo):
    """A documented direct route or a release-specific selection is named; a location, a comment and the
    selector-free invocations pass."""
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
    script = ['commands.case_script']
    return [
        Scenario('route-fenced-script', {readme: source[readme] + '\n```sh\nbash tests/suites/smoke/pw_specimen_smoke.sh\n```\n'}, {COMMANDS: script}, command),
        Scenario('route-fenced-bare-script', {readme: source[readme] + '\n```sh\ntests/suites/unit/fmt.sh\n```\n'}, {COMMANDS: script}, command),
        Scenario('route-dot-slash-span', {readme: source[readme] + '\nUse `./tests/suites/unit/fmt.sh` here.\n'}, {COMMANDS: script}, command),
        Scenario('route-run-sentence', {readme: source[readme] + '\nRun `tests/suites/unit/fmt.sh` to check formatting.\n'}, {COMMANDS: script}, command),
        Scenario('route-location-span', {readme: source[readme] + '\n- **Location:** `tests/suites/unit/fmt.sh`\n'}, {COMMANDS: []}),
        Scenario('route-direct-output', {readme: source[readme] + '\nOutput lands in `tests/out/runs/direct`.\n'}, {COMMANDS: ['commands.retired_output']}, 'retired direct output'),
        Scenario('route-makefile-selector', {makefile: recipe}, {RELEASE: ['release.selector', 'release.arguments']}, 'names the test selector --suite'),
        Scenario('route-makefile-arguments', {makefile: arguments}, {RELEASE: ['release.arguments']}, 'runs tests/run.sh with arguments'),
        Scenario('route-makefile-comment', {makefile: source[makefile] + '\n# tests/run.sh --suite smoke is how a developer selects one suite\n'}, {RELEASE: []}),
        Scenario('route-acceptance-selector', {accept: selected}, {RELEASE: ['release.selector']}, 'names the test selector --case'),
        Scenario('route-restored', source, {COMMANDS: [], RELEASE: []}),
    ]


def rule_gap_scenarios(repo):
    """Dedicated negative controls for the matrix, attempt-kind, test-seam, pair and landing-path rules,
    each with its converse where the rule has one, followed by restoration."""
    coverage = Path('tests/COVERAGE.md')
    swift = Path('runner/Sources/PWRunnerCore/CWorker.swift')
    header = Path('controller/tools/pw_probe_runner/pw_probe_runner_abi.h')
    runner_readme = Path('runner/README.md')
    request = Path('runner/Sources/PWRunnerCore/PWRunnerRequest.swift')
    guide = Path('docs/PolicyWitness.md')
    architecture = Path('docs/ARCHITECTURE.md')
    source = {path: (repo / path).read_text() for path in (coverage, swift, header, runner_readme, request, guide, architecture)}
    assert source[request].count('struct PWRunnerTestOverrides: Codable {') == 1, 'fixture requires the override definition'

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
    swift_close = '    case fileCreateFresh = 13\n}'
    c_close = '    PW_ATTEMPT_FILE_CREATE_FRESH = 13,\n} pw_attempt_kind_t;'
    assert source[swift].count(swift_close) == 1 and source[header].count(c_close) == 1, 'fixture requires the current attempt kinds'
    assert source[swift].count('    case sysctlRead     = 7\n') == 1
    seam_first = rows_under(runner_readme, '## Test seam: `_test_overrides`')[0]
    pair_line = next(line for line in source[guide].split('\n') if line.startswith('- `(iokit-open-service, iokit_registry_entry_class)`'))
    prediction_row = next(line for line in source[architecture].split('\n') if line.startswith('| Prediction |'))
    assert '`steps[].sandbox_check`' in prediction_row
    matrices = {NORMALIZED: [], SUITE_ROWS: [], ATTEMPTS: []}
    return [
        Scenario('rule-runner-outcome-suite-row-removed', {coverage: without(coverage, timeout_row)},
                 {SUITE_ROWS: ['matrix.suite_without_row'], NORMALIZED: ['matrix.missing_row']},
                 "suite 'runner_outcome_runner_timeout' has no row for outcome 'runner_timeout'"),
        Scenario('rule-normalized-matrix-extra-row', {coverage: with_after(coverage, last, renamed(last, 'validator_unavailable', 'bogus_outcome'))},
                 {NORMALIZED: ['matrix.unknown_row'], SUITE_ROWS: []},
                 "coverage matrix lists 'bogus_outcome' but no NormalizedOutcome constant by that name exists"),
        Scenario('rule-attempt-matrix-row-removed', {coverage: without(coverage, sysctl_row)}, {ATTEMPTS: ['attempt_matrix.missing_row']},
                 'AttemptOutcome.sysctl_failed has no row in tests/COVERAGE.md attempt-outcome coverage matrix'),
        Scenario('rule-attempt-matrix-extra-row',
                 {coverage: with_after(coverage, attempt_last, renamed(attempt_last, 'no_completed_result', 'bogus_attempt'))},
                 {ATTEMPTS: ['attempt_matrix.unknown_row']},
                 "attempt-outcome matrix lists 'bogus_attempt' but no AttemptOutcome constant by that name exists"),
        Scenario('rule-matrix-restored', {coverage: source[coverage]}, matrices),
        Scenario('rule-attempt-kind-swift-extra',
                 {swift: source[swift].replace(swift_close, '    case fileCreateFresh = 13\n    case extraKind = 14\n}', 1)},
                 {KINDS: ['attempt_kind.swift_only']}, 'Swift PWAttemptKind.EXTRA_KIND=14 has no matching pw_attempt_kind_t value'),
        Scenario('rule-attempt-kind-c-extra',
                 {header: source[header].replace(c_close, '    PW_ATTEMPT_FILE_CREATE_FRESH = 13,\n    PW_ATTEMPT_EXTRA_KIND = 14,\n} pw_attempt_kind_t;', 1)},
                 {KINDS: ['attempt_kind.c_only']}, 'C PW_ATTEMPT_EXTRA_KIND=14 has no matching PWAttemptKind raw value'),
        Scenario('rule-attempt-kind-name-mismatch',
                 {swift: source[swift].replace('    case sysctlRead     = 7\n', '    case sysctlQuery    = 7\n', 1)},
                 {KINDS: ['attempt_kind.name_mismatch']}, 'value 7 is PW_ATTEMPT_SYSCTL_READ in C but PWAttemptKind.SYSCTL_QUERY in Swift'),
        Scenario('rule-attempt-kind-c-gap',
                 {swift: source[swift].replace(swift_close, '    case fileCreateFresh = 13\n    case gapped = 15\n}', 1),
                  header: source[header].replace(c_close, '    PW_ATTEMPT_FILE_CREATE_FRESH = 13,\n    PW_ATTEMPT_GAPPED = 15,\n} pw_attempt_kind_t;', 1)},
                 {KINDS: ['attempt_kind.gap']}, 'pw_attempt_kind_t has a numeric gap at 14'),
        Scenario('rule-attempt-kind-malformed-c-enum', {header: source[header].replace('} pw_attempt_kind_t;', '};', 1)},
                 {KINDS: ['enum.missing']}, 'could not locate pw_attempt_kind_t in pw_probe_runner_abi.h'),
        Scenario('rule-attempt-kind-restored', {swift: source[swift], header: source[header]}, {KINDS: []}),
        Scenario('rule-test-overrides-extra-row',
                 {runner_readme: with_after(runner_readme, seam_first, renamed(seam_first, 'worker_executable_path', 'bogus_override'))},
                 {OVERRIDES: ['test_overrides.unknown_row']},
                 "runner/README.md's test-seam table lists 'bogus_override' but PWRunnerTestOverrides has no such property"),
        Scenario('rule-test-overrides-missing-definition',
                 {request: source[request].replace('struct PWRunnerTestOverrides: Codable {', 'struct AbsentOverrides: Codable {', 1)},
                 {OVERRIDES: ['struct.missing']},
                 'could not locate PWRunnerTestOverrides in runner/Sources/PWRunnerCore/PWRunnerRequest.swift'),
        Scenario('rule-test-overrides-restored', {runner_readme: source[runner_readme], request: source[request]}, {OVERRIDES: []}),
        Scenario('rule-pair-document-only', {guide: with_after(guide, pair_line, '- `(control-op, control_filter)` control')},
                 {PAIRS: ['prediction.docs_only']},
                 "('control-op', 'control_filter') in docs (docs/PolicyWitness.md) but missing from swift (ProbeRunner.swift)"),
        Scenario('rule-pair-restored', {guide: source[guide]}, {PAIRS: []}),
        Scenario('rule-evidence-unknown-landing',
                 {architecture: source[architecture].replace(
                     prediction_row, prediction_row.replace('`steps[].sandbox_check`', '`steps[].sandbox_check` and `steps[].bogus_landing`', 1), 1)},
                 {EVIDENCE: ['evidence.unknown_landing']}, '`steps[].bogus_landing` is not a key of the reply shape golden'),
        Scenario('rule-evidence-restored', {architecture: source[architecture]}, {EVIDENCE: []}),
    ]


def registry_scenarios(repo, out):
    """The suite registry's on-disk side: a run.sh no case names, a suite directory without a README, one the
    catalog lacks and a Baseline suite with no default case are each named; each scenario records the paths it
    created or deleted and their contents."""
    wrapper = repo / 'tests/suites/smoke/run.sh'
    nested = repo / 'tests/suites/smoke/retired/run.sh'
    stray = repo / 'tests/suites/stray_suite'
    readme = repo / 'tests/README.md'
    catalog = repo / 'tests/catalog.json'
    readme_original = readme.read_text()
    catalog_original = catalog.read_text()
    control = repo / 'tests/suites/baseline_control'

    def write_wrapper():
        wrapper.write_text('#!/usr/bin/env bash\nexec bash "$(dirname "$0")/pw_specimen_smoke.sh"\n')
        return {wrapper}, set()

    def stray_without_readme():
        stray.mkdir()
        (stray / 'notes.txt').write_text('a directory under tests/suites is a suite directory\n')
        return {stray / 'notes.txt'}, set()

    def stray_readme():
        (stray / 'README.md').write_text('# stray_suite\n')
        return {stray / 'README.md'}, set()

    def nested_wrapper():
        nested.parent.mkdir()
        nested.write_text('#!/usr/bin/env bash\nexit 0\n')
        return {nested}, set()

    def remove(*paths):
        def removal():
            for path in paths:
                shutil.rmtree(path) if path.is_dir() else path.unlink()
            return set(), set(paths)
        return removal

    def baseline_suite(default):
        def setup():
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
            return {control / 'README.md', readme, catalog}, set()
        return setup

    def baseline_removed():
        shutil.rmtree(control)
        readme.write_text(readme_original)
        catalog.write_text(catalog_original)
        return {readme, catalog}, {control}

    registry = {README: [], INDEX: [], CATALOG_COMMANDS: []}
    receipts = []
    for name, setup, expected, diagnostic in [
        ('registry-wrapper-script', write_wrapper, {CATALOG_COMMANDS: ['catalog.not_a_command']}, 'tests/suites/smoke/run.sh is not a case command'),
        ('registry-wrapper-removed', remove(wrapper), {CATALOG_COMMANDS: []}, None),
        ('registry-nested-wrapper', nested_wrapper, {CATALOG_COMMANDS: ['catalog.not_a_command']}, 'tests/suites/smoke/retired/run.sh is not a case command'),
        ('registry-nested-wrapper-removed', remove(nested.parent), {CATALOG_COMMANDS: []}, None),
        ('registry-directory-without-readme', stray_without_readme,
         {README: ['readme.missing'], INDEX: ['catalog.suite_mismatch', 'index.missing_row']}, 'tests/suites/stray_suite/ has no README.md'),
        ('registry-directory-outside-catalog', stray_readme,
         {README: [], INDEX: ['catalog.suite_mismatch', 'index.missing_row']}, 'suite directories and catalog disagree'),
        ('registry-restored', remove(stray), registry, None),
        ('registry-baseline-suite-nondefault', baseline_suite(False), {BASELINE: ['catalog.baseline_nondefault'], INDEX: []},
         "Baseline-tier suite 'baseline_control' is missing from tests/catalog.json's default membership"),
        ('registry-baseline-suite-default', baseline_suite(True), {BASELINE: [], INDEX: []}, None),
        ('registry-baseline-suite-removed', baseline_removed, {BASELINE: [], INDEX: []}, None),
    ]:
        created, deleted = setup()
        evidence = out / name
        evidence.mkdir()
        contents = {}
        for path in sorted(created):
            relative = path.relative_to(repo).as_posix()
            contents[relative] = path.read_text()
            captured = evidence / relative
            captured.parent.mkdir(parents=True, exist_ok=True)
            captured.write_text(contents[relative])
        scenario = Scenario(name, {}, expected, diagnostic)
        start = time.perf_counter()
        actual = evaluate(repo, expected)
        elapsed = time.perf_counter() - start
        problems = compare(scenario, actual)
        record = dict(scenario=name, mode='in-process', rules=list(expected), created=contents,
                      deleted=sorted(path.relative_to(repo).as_posix() for path in deleted), expected=expected,
                      diagnostic=diagnostic, actual=actual, elapsed_seconds=elapsed, problems=problems)
        (evidence / 'records.json').write_text(json.dumps(record, indent=2) + '\n')
        if problems:
            raise AssertionError(f'{name}: ' + '\n'.join(problems) + '\n' + json.dumps(actual, indent=2))
        receipts.append(record)
    assert not wrapper.exists() and not stray.exists() and not control.exists()
    return receipts


# ---------------------------------------------------------------------------
# The entry point: a few subprocess scenarios with exact status, output and order
# ---------------------------------------------------------------------------

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
    start = time.perf_counter()
    result = subprocess.run(argv, cwd=repo, capture_output=True, text=True, timeout=30)
    elapsed = time.perf_counter() - start
    (evidence / 'stdout').write_text(result.stdout)
    (evidence / 'stderr').write_text(result.stderr)
    reported = json.loads(results_path.read_text()) if results_path.is_file() else None
    return argv, result, reported, integrity_problems(repo, reported, extra), elapsed


def entry_point_scenarios(repo, out):
    """The command itself: exact exit status, the summary and facts lines, stderr in table order, every rule reported."""
    readme = Path('AGENTS.md')
    manifest = Path('meson.build')
    originals = {path: (repo / path).read_text() for path in (readme, manifest, HOST, PLANNER_SOURCE)}
    declared = declared_rules(repo)
    core_line = "    'runner/Sources/PWRunnerCore/PathUtils.swift',\n"
    route = re.search(r'\[[^\]\n]+\]\(runner/AGENTS\.md#sandboxed-automation-harnesses\)', originals[readme])[0]
    mirror_three = originals[PLANNER_SOURCE].replace(CALL, CALL.replace('predictionUnavailableOpFilters', 'hostExclusions')) + \
        '\nprivate let hostExclusions: Set<PredictionUnavailablePair> = []\n'

    def order_of(stderr, markers):
        positions = [stderr.find(marker) for marker in markers]
        return positions if all(position >= 0 for position in positions) else None

    def expect_baseline(result, reported):
        problems = []
        if result.returncode != 0:
            problems.append(f'status {result.returncode}')
        if not result.stdout.startswith('rules: 19 evaluated, 0 input_blocked, 0 gate_blocked\n'):
            problems.append('summary line missing')
        if not result.stdout.rstrip('\n').splitlines()[-1].startswith('all drift checks pass: '):
            problems.append('facts line is not last')
        if result.stderr:
            problems.append('stderr is not empty')
        return problems

    def expect_combined(result, reported):
        problems = []
        outcomes = {r['rule_id']: r for r in reported['results']}
        if result.returncode != 1:
            problems.append(f'status {result.returncode}')
        keys = {rule_id: sorted(p['key'] for p in r['problems']) for rule_id, r in outcomes.items() if r['problems']}
        if keys != {MESON: ['meson.source_list'], PLANNER: ['planner.local_table', 'planner.missing_contains'], GUIDANCE: ['guidance.missing_route']}:
            problems.append(f'records {keys}')
        positions = order_of(result.stderr, ["PWRunner lacks 'runner/Sources/PWRunnerCore/PathUtils.swift'",
                                             'must not define a local exclusion table', 'missing diagnostic route runner/AGENTS.md'])
        if positions is None or positions != sorted(positions):
            problems.append(f'stderr order {positions} is not table order')
        if 'rules: 19 evaluated, 0 input_blocked, 0 gate_blocked' not in result.stdout:
            problems.append('summary line missing')
        return problems

    # The command-document scan reads the refused document under every name the scope lists for it: the file
    # and each symlink to it (CLAUDE.md is one in this repository).
    aliases = [relative for relative in check.markdown_documents(repository_tree.Tree(repo))
               if (repo / relative).is_symlink() and (repo / relative).resolve() == (repo / readme).resolve()]

    def expect_refusal(result, reported):
        problems = []
        outcomes = {r['rule_id']: r for r in reported['results']}
        if result.returncode != 1:
            problems.append(f'status {result.returncode}')
        keys = {rule_id: sorted(p['key'] for p in r['problems']) for rule_id, r in outcomes.items() if r['problems']}
        # The refused document is read by the command-document scan and by the guidance rule; both report it.
        if keys != {COMMANDS: ['reader.refused'] * (1 + len(aliases)), GUIDANCE: ['reader.refused'], HOSTS: ['host.native_use']}:
            problems.append(f'records {keys} with aliases {aliases}')
        refused = sorted(p['path'] for p in outcomes[COMMANDS]['problems'])
        if refused != sorted([readme.as_posix(), *aliases]):
            problems.append(f'refused documents {refused}')
        if any(outcomes[rule_id]['outcome'] != 'evaluated' for rule_id in (COMMANDS, GUIDANCE)):
            problems.append('a refused document is not an evaluated rule')
        positions = order_of(result.stderr, ['  commands: AGENTS.md', '  markdown: AGENTS.md', 'the XPC host never links, loads or calls libsandbox'])
        if positions is None or positions != sorted(positions):
            problems.append(f'stderr order {positions} is not table order')
        return problems

    receipts = []
    for name, changes, expect in [
        ('entry-baseline', {}, expect_baseline),
        ('entry-combined-faults', {manifest: originals[manifest].replace(core_line, ''), readme: originals[readme].replace(route, '', 1),
                                   PLANNER_SOURCE: mirror_three}, expect_combined),
        ('entry-refusal-with-fault', {readme: originals[readme].replace(route, 'see <!-- a -- b ' + route + ' -->', 1),
                                      HOST: originals[HOST] + '\n' + HOST_BINDING + '\n'}, expect_refusal),
        ('entry-restored', {}, expect_baseline),
    ]:
        for path, text in originals.items():
            (repo / path).write_text(text)
        evidence = out / name
        evidence.mkdir()
        for path, text in changes.items():
            assert text != originals[path], (name, path)
            (repo / path).write_text(text)
            captured = evidence / path
            captured.parent.mkdir(parents=True, exist_ok=True)
            captured.write_text(text)
        argv, result, reported, integrity, elapsed = run_checker(repo, evidence)
        problems = expect(result, reported) + integrity if reported else ['no result records'] + integrity
        record = dict(scenario=name, mode='entry-point', argv=argv, returncode=result.returncode,
                      changed=[path.as_posix() for path in changes], declared=len(declared),
                      outcomes={r['rule_id']: r['outcome'] for r in reported['results']} if reported else None,
                      stdout=str(evidence / 'stdout'), stderr=str(evidence / 'stderr'), results=str(evidence / 'results.json'),
                      launches=[dict(step='check', argv=argv, returncode=result.returncode, elapsed_seconds=elapsed)],
                      elapsed_seconds=elapsed, problems=problems)
        (evidence / 'command.json').write_text(json.dumps(record, indent=2) + '\n')
        if problems:
            raise AssertionError(f'{name}: {problems}\n{result.stdout}\n{result.stderr}')
        receipts.append(record)
    for path, text in originals.items():
        (repo / path).write_text(text)
    return receipts


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
        argv, result, reported, integrity, elapsed = run_checker(repo, evidence)
        outcomes = {r['rule_id']: r for r in reported['results']} if reported else {}
        record = dict(scenario=name, mode='entry-point', argv=argv, returncode=result.returncode, integrity=integrity,
                      outcomes={rule_id: r['outcome'] for rule_id, r in outcomes.items()},
                      records={rule_id: r['problems'] for rule_id, r in outcomes.items() if r['problems']},
                      stdout=str(evidence / 'stdout'), stderr=str(evidence / 'stderr'), results=str(evidence / 'results.json'),
                      launches=[dict(step='check', argv=argv, returncode=result.returncode, elapsed_seconds=elapsed)],
                      elapsed_seconds=elapsed)
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
        host_records = outcomes.get(HOSTS, {}).get('problems', [])
        if not any(r['key'] == 'host.native_use' and r['path'] == HOST.as_posix() for r in host_records):
            problems.append(f'host diagnostic missing from the records: {host_records}')
        for text in ('the XPC host never links, loads or calls libsandbox', "tests/README.md is missing the ## 'Suite coverage' section",
                     'input_blocked: index_vs_disk, baseline_in_catalog_defaults'):
            if text not in result.stderr + result.stdout:
                problems.append(f'output lacks {text!r}')
        others = [rule_id for rule_id, r in outcomes.items() if r['problems'] and rule_id not in blocked and rule_id != HOSTS]
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
    assert any(rule_id == HOSTS for rule_id, _ in generator_common.rule_declarations(mutated))
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
        argv, result, reported, integrity, elapsed = run_checker(repo, evidence)
        reported_ids = [r['rule_id'] for r in reported['results']] if reported else []
        record = dict(scenario=name, mode='entry-point', argv=argv, returncode=result.returncode, reported=reported_ids,
                      integrity=integrity, stdout=str(evidence / 'stdout'), stderr=str(evidence / 'stderr'),
                      results=str(evidence / 'results.json'),
                      launches=[dict(step='check', argv=argv, returncode=result.returncode, elapsed_seconds=elapsed)],
                      elapsed_seconds=elapsed)
        (evidence / 'command.json').write_text(json.dumps(record, indent=2) + '\n')
        problems = []
        if result.returncode != expect_status:
            problems.append(f'status {result.returncode} != {expect_status}')
        if expect_integrity:
            if HOSTS in reported_ids:
                problems.append('the omitted rule was reported')
            if not any(HOSTS in line for line in integrity):
                problems.append(f'the integrity check did not name the omitted rule: {integrity}')
        elif integrity or len(reported_ids) != 19:
            problems.append(f'restored dispatcher: {integrity} {reported_ids}')
        if problems:
            raise AssertionError(f'{name}: {problems}\n{result.stdout}\n{result.stderr}')
        receipts.append(record)
    return receipts


# ---------------------------------------------------------------------------
# Tree, isolation and rule-snippet controls
# ---------------------------------------------------------------------------

def scratch_directory(prefix):
    scratch = os.environ.get('PW_TEST_SCRATCH')
    if scratch:
        Path(scratch).mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=prefix, dir=scratch))


def inventory_controls(out):
    """Discovery is a pruned walk with the documented scope semantics.

    An independently specified fixture holds nested and untracked files, prefix
    near misses, a root and a nested `builddir`, hidden files and directories,
    paths the Markdown and shell scopes treat differently, file, directory and
    broken symlinks, a directory named with the suffix, an unreadable selected
    input and large excluded subtrees. The rules' own discovery must select
    exactly the listed entries in lexical order, and an independent instrument
    on directory enumeration must show the excluded subtrees were never entered."""
    import direct_python  # noqa: E402
    # The fixture is scratch, not evidence: it holds a `runner/.build` directory and large excluded
    # subtrees that the harness would refuse under artifacts. The receipt lists every created path.
    root = scratch_directory('inventory-')
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
    record = dict(scenario='inventory-scopes', mode='in-process', root=str(root), created=created, large_excluded_entries=large,
                  markdown=dict(selected=markdown, entered=markdown_entered, seconds=markdown_seconds),
                  shell=dict(selected=shell, entered=shell_entered, seconds=shell_seconds),
                  expanded=expanded, problems=problems)
    (out / 'inventory-controls.json').write_text(json.dumps(record, indent=2) + '\n')
    if problems:
        raise AssertionError('inventory controls: ' + '\n'.join(problems))
    return [dict(scenario='inventory-scopes', mode='in-process', markdown_entered=len(markdown_entered), shell_entered=len(shell_entered))]


def isolation_controls(out):
    """Fresh trees observe current bytes: two roots sharing a relative path give their own records in either
    order, a same-size rewrite with its mtime restored is seen, and a deleted input blocks the rule until it
    is recreated. The rule is called in process over each root."""
    base = scratch_directory('isolation-')
    rule = RULES_BY_ID[CLI]
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
        result = drift_rules.attempt(repository_tree.Tree(root), rule, refused=REFUSED)
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
    # A deliberately weakened evaluator that ignores the supplied root and reads the real checkout cannot meet
    # the same expectations: it sees no mismatch for root b and no missing input after the deletion.
    weakened = {'b': [drift_rules.attempt(repository_tree.Tree(ROOT), rule, refused=REFUSED).outcome,
                      sorted({p.key for p in drift_rules.attempt(repository_tree.Tree(ROOT), rule, refused=REFUSED).problems})]}
    readme_a.unlink()
    weakened['deleted'] = weakened['b']
    readme_a.write_text(original)
    shutil.rmtree(base)
    expected = {'a_then_b': [clean, mismatch], 'b_then_a': [mismatch, clean], 'same_size_mtime_restored': mismatch,
                'same_size_identity': dict(size_unchanged=True, mtime_unchanged=True), 'rewritten_back': clean,
                'deleted': ['input_blocked', ['input.missing']], 'recreated': clean}
    problems = [f'{name}: {observations[name]} != {expected[name]}' for name in expected if observations[name] != expected[name]]
    if weakened['b'] == mismatch or weakened['deleted'] == expected['deleted']:
        problems.append(f'a root-ignoring evaluator met the expectations: {weakened}')
    observations['weakened_evaluator'] = weakened
    record = dict(scenario='isolation-fresh-trees', mode='in-process', rule=rule.id, observations=observations, problems=problems)
    (out / 'isolation-controls.json').write_text(json.dumps(record, indent=2) + '\n')
    if problems:
        raise AssertionError('isolation controls: ' + '; '.join(problems))
    return [dict(scenario='isolation-fresh-trees', mode='in-process')]


def host_invariance_controls(out):
    """Controls distinguish native use from schema, prose and unrelated APIs; they test the rule, once per case."""
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
    record = dict(scenario='host-invariance-controls', mode='in-process', accepted=len(accepted), rejected=len(rejected),
                  outcomes=outcomes, problems=problems)
    (out / 'host-invariance-controls.json').write_text(json.dumps(record, indent=2) + '\n')
    if problems:
        raise AssertionError('host invariance controls: ' + '; '.join(problems))
    return [dict(scenario='host-invariance-controls', mode='in-process')]


if __name__ == '__main__':
    main(Path(sys.argv[1]))
