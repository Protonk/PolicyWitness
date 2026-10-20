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
HOST = Path('runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift')
CALL = 'if predictionUnavailableOpFilters.contains(PredictionUnavailablePair(operation: check.operation, filterKind: kind)) {'


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
             'tests/suites/source_drift/check.py']
    # The C sources are whatever the native expectation names for a C-only configuration,
    # so a new C target cannot be left out of the fixture.
    paths += sorted(set().union(*native_sources.expected(ROOT, xpc=False).values()))
    paths += [str(p.relative_to(ROOT)) for p in (ROOT / 'runner/Sources').rglob('*') if p.is_file()]
    paths += markdown_reader.source_files()
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
        argv = [sys.executable, '-B', str(repo / 'tests/suites/source_drift/check.py')]
        result = subprocess.run(argv, cwd=repo, capture_output=True, text=True, timeout=30)
        (evidence / 'stdout').write_text(result.stdout)
        (evidence / 'stderr').write_text(result.stderr)
        record = dict(scenario=name, argv=argv, returncode=result.returncode,
                      expected_returncode=expected, expected_diagnostic=diagnostic)
        (evidence / 'command.json').write_text(json.dumps(record, indent=2) + '\n')
        if result.returncode != expected or (diagnostic and diagnostic not in result.stderr):
            raise AssertionError(f'{name}: unexpected checker result: {record}\n{result.stdout}\n{result.stderr}')
        receipts.append(record)
    for path, source in originals.items():
        (repo / path).write_text(source)
        if (ROOT / path).read_text() != source:
            raise AssertionError(f'source controls changed the working input: {path}')
    receipts += configured_controls(repo, manifest_original, worker_line, out)
    (out / 'controls.json').write_text(json.dumps({'ok': True, 'scenarios': receipts}, indent=2) + '\n')
    print(f'{len(receipts)} source and guidance controls passed')


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

    agents = paths[0]
    architecture = Path('docs/ARCHITECTURE.md')
    documents[architecture] = (repo / architecture).read_text()
    for path, label in [(agents, '- **One-way sandbox per process**:'),
                        (architecture, '- **One-way sandbox per process.**')]:
        source = documents[path]
        assert source.count(label) == 1
        scenarios.append((f'guidance-principle-prose-{path.stem}',
                          {path: source.replace(label, label + ' Independent explanation control.')}, 0, None))
    source = documents[agents]
    lines = source.splitlines(keepends=True)
    first = next(i for i, line in enumerate(lines) if line.startswith('- **One-way sandbox per process**:'))
    second = next(i for i, line in enumerate(lines) if line.startswith('- **Host/worker split**:'))
    removed = ''.join(lines[:second] + lines[second + 1:])
    reordered = lines.copy()
    reordered[first], reordered[second] = reordered[second], reordered[first]
    for name, changed in [('removed', removed),
                          ('renamed', source.replace('**Host/worker split**', '**Host separation**', 1)),
                          ('reordered', ''.join(reordered))]:
        scenarios.append((f'guidance-principle-label-{name}', {agents: changed}, 1, 'core ideas:'))
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
                      hidden('docs/ARCHITECTURE.md', '- [Principles as enforced constraints](#', '1. [Principles as enforced constraints](#'),
                      1, 'an index bullet must open with a link'))
    scenarios.append(('structure-core-idea-comment',
                      hidden('AGENTS.md', '- **Host/worker split**:', '- <!-- **Host/worker split** -->:'), 1, 'core ideas:'))
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
        argv = [sys.executable, '-B', str(checker), '--builddir', str(builddir), '--root', str(repo)]
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
    argv = [sys.executable, '-B', str(copy / 'tests/lib/native_sources.py'), '--builddir', str(copy / 'builddir'), '--root', str(copy)]
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


if __name__ == '__main__':
    main(Path(sys.argv[1]))
