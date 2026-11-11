"""Constructed authoring controls for the public contract's syntax and joins."""
import json
from pathlib import Path
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'docs'))
sys.path.insert(0, str(ROOT / 'tests/lib'))
import generate_contract_stamps
import fixture_inputs
import receipts


def minimal_surface():
    """A small authored model; none of these rules describes product behavior."""
    return '''# Model control {demo: surface}
```contract
syntax: 1
artifact: "Constructed authoring control"
part: "assessment"
goldens: ["tests/fixtures/contract/compiled_profile.json"]
checks: ["source_drift"]
who: "controller"
where: "reply admission"
entry: ["cli", "direct"]
recipient: ["controller", "host"]
report: ["ordinary", "actors"]
```

## Fixture meanings {meanings: subject}
### Activate a phase {activate: definition}
```contract
defines: "action"
```
Activation releases one phase in this constructed model.
### Supported assessment {assessment: definition}
```contract
defines: "assessment"
```
An assessment depends on the model's check.

## Fixture report {report: subject}
```contract
record: "ContractFixture"
as: "sample"
```
The model separates retained records from a supported assessment.
### Status {status: field}
```contract
type: "string"
vocabulary: "open"
listed: "illustrative"
values: ["ready", "unknown"]
unknown: "Retain an unfamiliar label without assigning the listed meanings."
```
The reported state of this model.
### Phases {phases: field}
```contract
type: "[ContractPhase]"
```
Declared phases in order.
### Optional note {note: field}
```contract
type: "string?"
json_null: true
```
Null records the absence of a model note.

### Read the status {read_status: checks}
```contract
entry: ["cli"]
recipient: ["controller"]
report: ["ordinary"]
when: present(sample.status)
test: sample.status in ["ready", "unknown"]
failure: "first"
precedes: ["demo.report.release"]
```
The controller checks the status under this constructed rule.
#### Otherwise {failure: effect}
```contract
on: "failure"
bind.p: sample.phases
effects: [prevent(ref("demo.meanings.activate"), later(sample.phases, p)), retain_records(sample), withhold(ref("demo.meanings.assessment"))]
```
The record remains available when the assessment is withheld.
### Release a phase {release: acts}
```contract
when: present(sample.status)
requires: ["demo.report.read_status"]
free.effect: A satisfied model check releases its phase.
```
The model's second obligation follows the first check.
### Example with a fenced heading {example: example}
```text
# This is example text, not a contract heading.
```
The code fence remains part of this example.

## Phase record {phase: subject}
```contract
record: "ContractPhase"
as: "phase"
```
### ID {id: field}
```contract
type: "string"
```
The phase's declared identifier.

## Imported producer record {producer: subject}
```contract
record: "PWProducer"
as: "producer"
at: ["reply.producer"]
```
### Contract {contract: field}
The producer's embedded public contract assertion.
### Describe {describe: field}
The producer's recorded source description.
### Commit {commit: field}
The producer's recorded source commit.

## Fixture source {support: owner}
```contract
scope: "subtree"
grade: "source_read"
source: {"path": "tests/suites/source_drift/contract_tree_controls.py", "symbol": "minimal_surface"}
pins: "Constructed facts and field joins in this model only."
context: "A static authoring fixture."
limits: "Supplies no evidence of product execution."
```
'''


def component_surface():
    """Component identities for the authoring model, independent of product rules."""
    return '''# Model components {identity: surface}
```contract
syntax: 1
artifact: "Constructed component definitions"
part: "definitions"
goldens: ["tests/fixtures/contract/compiled_profile.json"]
checks: ["source_drift"]
```
## Acting components {definitions: subject}
### Controller actor {controller: definition}
```contract
defines: "component"
```
The component that interprets this model.
### Host actor {host: definition}
```contract
defines: "component"
```
The component that produces this model.
### Retained reader actor {reader: definition}
```contract
defines: "component"
```
The component that reads a retained model.
'''


class ContractTreeTests(receipts.TestCase):
    def setUp(self):
        super().setUp()
        self.model = generate_contract_stamps.contract_module('tree')
        self.track_inputs(ROOT, generate_contract_stamps.input_paths(ROOT))
        self.track_inputs(ROOT, ['tests/suites/source_drift/contract_tree_controls.py'])

    def load(self, body=None, strict=True, additions=None):
        files = {'docs/contract/control.surface.md': body or minimal_surface()}
        files.update(additions or {})
        def read(path):
            return files[path] if path in files else (ROOT / path).read_text()
        return self.model.load_tree(ROOT, read=read, paths=list(files), strict=strict)

    def changed(self, before, after):
        body = minimal_surface()
        self.assertIn(before, body)
        changed = body.replace(before, after, 1)
        self.assertNotEqual(changed, body, 'mutation must change its authored input')
        return changed

    def test_complete_fixture_joins_imported_fields_and_renders_distinctions(self):
        tree = self.load()
        rendered = self.model.render(tree)
        self.assertEqual(tree.free_counts, dict(condition=0, dependency=0, effect=1, when=0))
        self.assertEqual(tree.uncovered_records, [])
        self.assertIn('# This is example text, not a contract heading.', rendered)
        self.assertEqual(tree.index['demo.report.read_status'].context['recipient'], ['controller'])
        self.assertEqual(tree.index['demo.report.release'].context['recipient'], ['controller', 'host'])
        self.assertEqual(tree.index['demo.producer.contract'].field_info['swift_type'], 'String')
        self.assertEqual(self.model.render(self.load()), rendered)
        facts = tree.index['demo.report.read_status.failure'].expressions['effects']
        self.assertIn('retain_records', __import__('ast').dump(facts))
        self.assertIn('withhold', __import__('ast').dump(facts))


    def test_binding_domains_and_selectors_render_without_cardinality_claim(self):
        body = minimal_surface().replace('bind.p: sample.phases\n', '', 1)
        body = body.replace('test: sample.status in ["ready", "unknown"]',
                            'bind.p: sample.phases\nbind.q: sample.phases\nbind.r: reply.steps\n'
                            'match.q: sample.phases[q].id == sample.phases[p].id\n'
                            'test: sample.status in ["ready", "unknown"]', 1)
        rendered = self.model.render(self.load(body))
        rule = rendered.split('### Read the status', 1)[1].split('### Release a phase', 1)[0]
        self.assertIn('Binding `p`: entry in `sample.phases`.', rule)
        self.assertIn('Binding `q`: entry in `sample.phases`.', rule)
        self.assertIn('Binding `r`: entry in `reply.steps`.', rule)
        self.assertIn('Association restriction for `q`: `sample.phases[q].id` = `sample.phases[p].id`.', rule)
        self.assertNotIn('unique', rule)
        self.assertNotIn('exactly one', rule)
        self.assertNotIn('for each', rule)
        row = next(line for line in rendered.split('## Controller findings', 1)[1].splitlines()
                   if '#contract-demo-report-read_status)' in line)
        self.assertIn('sample.phases[q].id', row)
        self.assertIn('sample.phases[p].id', row)
        self.assertIn('`reply.steps`', row)

    def test_findings_include_direct_effects_child_triggers_and_consequence_prose(self):
        body = minimal_surface().replace('failure: "first"',
                                        'effects: set_value(sample.status, "reviewed")\n'
                                        'free.effect: Keep the direct retained explanation.\n'
                                        'failure: "first"', 1)
        body = body.replace('### Release a phase {release: acts}',
                            '#### Successful consequence {success: effect}\n```contract\n'
                            'on: "success"\nfree.effect: retain the successful model note.\n```\n'
                            'The successful note carries its own consequence detail.\n'
                            '### Release a phase {release: acts}', 1)
        rendered = self.model.render(self.load(body))
        row = next(line for line in rendered.split('## Controller findings', 1)[1].splitlines()
                   if '#contract-demo-report-read_status)' in line)
        self.assertIn('sets `sample.status` to `"reviewed"`.', row)
        self.assertIn('Keep the direct retained explanation.', row)
        self.assertIn('On failure, prevents', row)
        self.assertIn('The record remains available when the assessment is withheld.', row)
        self.assertIn('On success, retain the successful model note.', row)
        self.assertIn('The successful note carries its own consequence detail.', row)
        self.assertNotIn('The controller checks the status under this constructed rule.', row)
        self.assertNotIn('Requires', row)
        self.assertNotIn('Applies when', row)

    def test_record_alias_locations_render_at_their_own_subject(self):
        rendered = self.model.render(self.load())
        subject = rendered.split('## Imported producer record', 1)[1]
        self.assertIn('Record `producer` locations: `reply.producer`.', subject)
        current = self.model.render(self.model.load_tree(ROOT))
        receipt = current.split('Record `receipt` locations:', 1)[1].split('\n', 1)[0]
        self.assertIn('`reply.compiled_profile`', receipt)
        self.assertIn('`reply.actors[a].compiled_profile`', receipt)

    def test_referenced_actors_replace_inheritance_and_select_joint_controller_check(self):
        body = minimal_surface().replace('who: "controller"',
                                        'who: ["identity.definitions.host"]', 1)
        joint = 'who: ["identity.definitions.controller", "identity.definitions.reader"]'
        body = body.replace('entry: ["cli"]', joint + '\nentry: ["cli"]', 1)
        additions = {'docs/contract/components.surface.md': component_surface()}
        tree = self.load(body, additions=additions)
        self.assertEqual(tree.index['demo.report.read_status'].context['who'],
                         ['identity.definitions.controller', 'identity.definitions.reader'])
        self.assertEqual(tree.index['demo.report.release'].context['who'], ['identity.definitions.host'])
        rendered = self.model.render(tree)
        self.assertIn('[Controller actor](#contract-identity-definitions-controller), '
                      '[Retained reader actor](#contract-identity-definitions-reader) checks at reply admission.', rendered)
        findings = rendered.split('## Controller findings', 1)[1]
        self.assertIn('#contract-demo-report-read_status)', findings)
        host_only = body.replace(joint, 'who: ["identity.definitions.host"]', 1)
        # A controller-like display title cannot turn a host actor into the controller.
        host_only = host_only.replace('### Read the status', '### Controller-like host check', 1)
        host_findings = self.model.render(self.load(host_only, additions=additions)).split('## Controller findings', 1)[1]
        self.assertNotIn('#contract-demo-report-read_status)', host_findings)

    def test_actor_reference_refusals_preserve_source_location(self):
        additions = {'docs/contract/components.surface.md': component_surface()}
        for value, diagnostic in (
                ('[]', 'list of nonempty strings'),
                ('[""]', 'list of nonempty strings'),
                ('[1]', 'list of nonempty strings'),
                ('{}', 'nonempty string'),
                ('["identity.definitions.controller", "identity.definitions.controller"]', 'repeats a value'),
                ('["missing.component"]', 'unresolved node reference'),
                ('["demo.report"]', 'inappropriate subject reference'),
                ('["demo.meanings.activate"]', 'requires a component definition')):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, diagnostic) as caught:
                self.load(self.changed('who: "controller"', 'who: ' + value), additions=additions)
            self.assertIn('docs/contract/control.surface.md:', str(caught.exception))
            self.assertIn(': demo:', str(caught.exception))

    def test_literal_actor_compatibility_and_referenced_public_meaning(self):
        rendered = self.model.render(self.load())
        self.assertIn('#contract-demo-report-read_status)', rendered.split('## Controller findings', 1)[1])
        joint_label = self.changed('who: "controller"', 'who: "controller and retained reader"')
        self.assertNotIn('#contract-demo-report-read_status)',
                         self.model.render(self.load(joint_label)).split('## Controller findings', 1)[1])
        body = self.changed('who: "controller"', 'who: ["identity.definitions.controller"]')
        path = 'docs/contract/components.surface.md'
        before = self.model.public_payload(self.load(body, additions={path: component_surface()}), 'demo')
        self.assertIn('identity.definitions.controller', {node['id'] for node in before['shared']})
        changed = component_surface().replace('The component that interprets this model.',
                                             'The component that interprets this model and retains its decision.')
        self.assertNotEqual(before, self.model.public_payload(self.load(body, additions={path: changed}), 'demo'))

    def test_current_public_checks_use_resolved_actors_and_all_controller_rows(self):
        tree = self.model.load_tree(ROOT)
        checks = [node for node in tree.nodes if node.kind == 'checks']
        self.assertTrue(checks)
        for node in checks:
            with self.subTest(check=node.id):
                self.assertIsInstance(node.context['who'], list)
        expected = {'transport.client.admit', 'wire.frame.admit', 'actor_evidence.gate.check',
                    'profile.receipt.labels', 'envelope.data.admit', 'installation.commands.ownership'}
        findings = self.model.render(tree).split('\n## Controller findings\n', 1)[1].split('\n## Known gaps\n', 1)[0]
        for node in checks:
            link = '#contract-' + node.id.replace('.', '-') + ')'
            with self.subTest(check=node.id):
                self.assertEqual(link in findings, node.id in expected)
        wire_row = next(line for line in findings.splitlines() if '#contract-wire-frame-admit)' in line)
        self.assertIn('See the linked rule.', wire_row)

    def test_public_coverage_accounts_for_entire_imported_record_families(self):
        complete = self.model.load_tree(ROOT)
        self.assertTrue(any(n.facts.get('coverage') == 'public' for n in complete.surfaces))
        declared = {n.record for n in complete.nodes if n.record}
        imported = {name for name, record in complete.records.items() if record.get('coverage_required')}
        self.assertLessEqual(imported, declared)
        # The same small fixture remains valid for selected coverage, but a
        # public promise cannot silently omit whole ambient input/output roots.
        self.load()
        body = self.changed('syntax: 1', 'syntax: 1\ncoverage: "public"')
        with self.assertRaisesRegex(ValueError, 'uncovered referenced records'):
            self.load(body)

    def test_tree_and_fact_shape_refusals(self):
        controls = [
            ('{phase: subject}', '{report: subject}', 'duplicate node identifier'),
            ('## Phase record', '#### Phase record', 'illegal'),
            ('{phase: subject}', '{phase: mystery}', 'typed node'),
            ('## Phase record {phase: subject}', '## Phase record {phase: field}', 'illegal'),
            ('syntax: 1', 'syntax: 1\nsyntax: 1', 'duplicate'),
            ('syntax: 1', 'unexpected: 1\nsyntax: 1', 'unknown'),
            ('syntax: 1', 'syntax: 2', 'unsupported source syntax'),
            ('## Fixture meanings {meanings: subject}', '## Fixture meanings {meanings: subject}\nProse before facts.\n```contract\nwho: "host"\n```', 'facts must precede'),
        ]
        for before, after, diagnostic in controls:
            with self.subTest(diagnostic=diagnostic, change=after):
                with self.assertRaisesRegex(ValueError, diagnostic):
                    self.load(self.changed(before, after))

    def test_object_paths_binding_and_safe_expression_refusals(self):
        expressions = [
            ('sample.misspelled == "ready"', 'unknown field'),
            ('sample.status[p] == "ready"', 'noncollection'),
            ('sample.phases[p].id == "a"', 'not bound'),
            ('__import__("os").system("false")', 'unsupported expression call'),
            ('(lambda: True)()', 'unsupported expression call'),
            ('sample.status', 'expected boolean'),
            ('sample.status == 1', 'incompatible comparison'),
            ('sample.status ** 2', 'unsupported expression syntax'),
            ('present("literal")', 'requires an object'),
        ]
        for expression, diagnostic in expressions:
            with self.subTest(expression=expression):
                with self.assertRaisesRegex(ValueError, diagnostic):
                    self.load(self.changed('test: sample.status in ["ready", "unknown"]', 'test: ' + expression))
        with self.assertRaisesRegex(ValueError, 'unbound index'):
            self.load(self.changed('test: sample.status in ["ready", "unknown"]', 'match.p: sample.status == "ready"'))
        with self.assertRaisesRegex(ValueError, 'belongs to'):
            self.load(self.changed('bind.p: sample.phases', 'bind.p: reply.steps').replace('later(sample.phases, p)', 'sample.phases[p]'))

    def test_condition_forms_and_conjoined_context_are_preserved(self):
        body = minimal_surface().replace('record: "ContractFixture"', 'when: present(reply.producer)\nrecord: "ContractFixture"', 1)
        body = body.replace('test: sample.status in ["ready", "unknown"]',
                            'test: implies(present(sample.note), not (sample.note == None) and (sample.status == "ready" or sample.status == "unknown"))')
        tree = self.load(body)
        context = tree.index['demo.report.read_status'].context['when']
        self.assertIn('present(reply.producer)', context)
        self.assertIn('present(sample.status)', context)
        expression = tree.index['demo.report.read_status'].expressions['test']
        names = {node.id for node in __import__('ast').walk(expression) if isinstance(node, __import__('ast').Name)}
        self.assertIn('implies', names)

    def test_applicability_cannot_widen_and_order_is_explicit(self):
        for key in ('entry', 'recipient', 'report'):
            before = {'entry': 'entry: ["cli"]', 'recipient': 'recipient: ["controller"]', 'report': 'report: ["ordinary"]'}[key]
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'widens inherited'):
                self.load(self.changed(before, key + ': ["undeclared"]'))
        with self.assertRaisesRegex(ValueError, 'check-order cycle'):
            self.load(self.changed('requires: ["demo.report.read_status"]', 'requires: ["demo.report.read_status"]\nprecedes: ["demo.report.read_status"]'))
        with self.assertRaisesRegex(ValueError, 'unresolved node reference'):
            self.load(self.changed('requires: ["demo.report.read_status"]', 'requires: ["missing.rule"]'))
        with self.assertRaisesRegex(ValueError, 'requirement reference'):
            self.load(self.changed('requires: ["demo.report.read_status"]', 'requires: ["demo.meanings.activate"]'))

    def test_field_coverage_vocabulary_and_support_are_required(self):
        for before, after, diagnostic in (
                ('### Commit {commit: field}\nThe producer\'s recorded source commit.\n', '', 'field coverage differs'),
                ('{commit: field}', '{unknown: field}', 'unknown public field'),
                ('The producer\'s recorded source commit.', '', 'no authored meaning'),
                ('listed: "illustrative"\n', '', 'list completeness'),
                ('unknown: "Retain an unfamiliar label without assigning the listed meanings."\n', '', 'unknown must'),
                ('grade: "source_read"', 'grade: "verified"', 'owner grade'),
                ('"symbol": "minimal_surface"', '"symbol": "' + '_'.join(['absent', 'citation', 'symbol']) + '"', 'missing symbol'),
                ('scope: "subtree"', 'scope: "self"', 'no graded support'),
                ('who: "controller"\n', '', 'lacks particulars')):
            with self.subTest(change=after, diagnostic=diagnostic), self.assertRaisesRegex(ValueError, diagnostic):
                self.load(self.changed(before, after))

    def test_effect_operands_preserve_scope_and_record_assessment_distinction(self):
        for expression, diagnostic in (
                ('[retain_records(sample.status)]', 'requires a record'),
                ('[prevent(ref("demo.meanings.assessment"), sample)]', 'requires an action'),
                ('[prevent(ref("demo.meanings.activate"), sample.status)]', 'explicit record'),
                ('[withhold(ref("demo.meanings.activate"))]', 'not an action'),
                ('[invent_effect(sample)]', 'unsupported expression call')):
            with self.subTest(expression=expression), self.assertRaisesRegex(ValueError, diagnostic):
                body = minimal_surface()
                start = next(line for line in body.splitlines() if line.startswith('effects:'))
                self.load(self.changed(start, 'effects: ' + expression))

    def test_execution_credit_requires_run_source_and_release_case(self):
        source = 'source: {"path": "tests/suites/source_drift/contract_tree_controls.py", "symbol": "minimal_surface"}'
        check = 'check: {"path": "tests/suites/source_drift/contract_tree_controls.py", "symbol": "test_tree_and_fact_shape_refusals", "form": "test"}'
        base = self.changed('grade: "source_read"', 'grade: "executed"').replace(source, source + '\n' + check)
        for suffix, diagnostic in (('', 'run must'), ('\nrun: "constructed-run"', 'source_snapshot or build'),
                                   ('\nrun: "constructed-run"\nsource_snapshot: "fixture"\nrelease: "v0.3.7"', 'case must')):
            with self.subTest(suffix=suffix), self.assertRaisesRegex(ValueError, diagnostic):
                self.load(base.replace('grade: "executed"', 'grade: "executed"' + suffix))
        self.load(base.replace('grade: "executed"', 'grade: "executed"\nrun: "constructed-run"\nsource_snapshot: "fixture"\nrelease: "v0.3.7"\ncase: "source_drift/build_contracts"'))

    def test_public_payload_includes_meaning_but_excludes_evidence_metadata(self):
        before = self.model.public_payload(self.load(), 'demo')
        changed_owner = self.load(self.changed('Supplies no evidence of product execution.', 'The fixture describes parsing only.'))
        self.assertEqual(before, self.model.public_payload(changed_owner, 'demo'))
        changed_meaning = self.load(self.changed('The phase\'s declared identifier.', 'The phase identifier with revised meaning.'))
        self.assertNotEqual(before, self.model.public_payload(changed_meaning, 'demo'))
        changed_example = self.load(self.changed('The code fence remains part of this example.', 'An additional public example statement.'))
        self.assertNotEqual(before, self.model.public_payload(changed_example, 'demo'))

    def test_referenced_record_meaning_enters_dependent_surface_and_links_its_fields(self):
        body = minimal_surface()
        start = body.index('## Phase record')
        end = body.index('## Imported producer record')
        phase = body[start:end]
        body = body[:start] + body[end:]
        shared = '''# Shared record {shared: surface}
```contract
syntax: 1
artifact: "Shared model definition"
part: "definitions"
goldens: ["tests/fixtures/contract/compiled_profile.json"]
checks: ["source_drift"]
```
''' + phase
        path = 'docs/contract/shared.surface.md'
        tree = self.load(body, additions={path: shared})
        before = self.model.public_payload(tree, 'demo')
        self.assertIn('shared.phase.id', {node['id'] for node in before['shared']})
        self.assertIn('[Phase record](#contract-shared-phase)', self.model.render(tree))
        changed = shared.replace('The phase\'s declared identifier.', 'A revised shared identifier meaning.')
        self.assertNotEqual(changed, shared)
        self.assertNotEqual(before, self.model.public_payload(self.load(body, additions={path: changed}), 'demo'))
        with self.assertRaisesRegex(ValueError, 'inline record.*declared twice'):
            self.load(minimal_surface(), additions={path: shared})

    def test_example_whitespace_inside_values_is_public_content(self):
        body = minimal_surface().replace('# This is example text, not a contract heading.', 'value = "a  b"')
        changed = body.replace('value = "a  b"', 'value = "a b"')
        self.assertNotEqual(body, changed)
        self.assertNotEqual(self.model.public_payload(self.load(body), 'demo'),
                            self.model.public_payload(self.load(changed), 'demo'))

    def test_free_text_counts_ratchet_by_kind(self):
        runtime = generate_contract_stamps.contract_module('runtime')
        tree = self.load()
        runtime.check_ratchet(ROOT, tree, dict(condition=0, dependency=0, effect=1, when=0))
        with self.assertRaisesRegex(ValueError, 'count grew'):
            runtime.check_ratchet(ROOT, tree, dict(condition=0, dependency=0, effect=0, when=0))
        body = self.changed('free.effect: A satisfied model check releases its phase.', 'effects: retain_records(sample)')
        runtime.check_ratchet(ROOT, self.load(body), dict(condition=0, dependency=0, effect=1, when=0))
        self.assertEqual(self.load(self.changed('free.effect: A satisfied model check releases its phase.',
                                               'free.effect: Rewording preserves one free relationship.')).free_counts,
                         tree.free_counts)


class ContractHistoryTests(receipts.TestCase):
    def setUp(self):
        super().setUp()
        self.runtime = generate_contract_stamps.contract_module('runtime')

    def git(self, root, *args):
        result = self.run_command(['git', '-C', str(root), '-c', 'user.name=Contract control',
                                  '-c', 'user.email=contract-control@example.invalid',
                                  '-c', 'commit.gpgsign=false', '-c', 'tag.gpgsign=false', *args],
                                 capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def commit(self, root, tag):
        self.git(root, 'add', '.')
        self.git(root, 'commit', '-qm', 'Constructed release ' + tag)
        self.git(root, 'tag', '-a', tag, '-m', 'Constructed release control')

    def fixture(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-tree-history-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        fixture_inputs.copy_declared(ROOT, root, [*generate_contract_stamps.input_paths(ROOT),
                                                 'tests/suites/source_drift/contract_tree_controls.py'])
        for path in (root / 'docs/contract').glob('*.surface.md'):
            path.unlink()
        for name in ('docs/contract/public.json', 'docs/contract/free_text.json'):
            (root / name).unlink(missing_ok=True)
        shapes = root / 'tests/fixtures/contract/surfaces'
        shapes.mkdir(parents=True, exist_ok=True)
        (shapes / 'demo.json').write_text('{}\n')
        (shapes / 'retired.json').write_text('{}\n')
        rows = [dict(id=name, artifact=name, goldens=[f'tests/fixtures/contract/surfaces/{name}.json'],
                     definition='docs/CONTRACT.md', checks=['source_drift'])
                for name in ('demo', 'retired')]
        (root / 'docs/contract_surfaces.json').write_text(json.dumps(dict(surfaces=rows)))
        table = self.runtime.BEGIN + '\n| Surface | User artifact | Last changed |\n| --- | --- | --- |\n' + \
                '| `demo` | demo | v0.3.6 |\n| `retired` | retired | v0.3.6 |\n' + self.runtime.END + '\n'
        legacy = '\n'.join(f'<!-- BEGIN CONTRACT {name} -->Original {name}.<!-- END CONTRACT {name} -->'
                           for name in ('demo', 'retired'))
        (root / 'docs/CONTRACT.md').write_text(legacy + '\n' + table)
        (root / 'docs/PolicyWitness.md').write_text('# Guide\n\n' + table)
        self.track_inputs(root)
        self.git(root, 'init')
        self.commit(root, 'v0.3.6')
        (root / 'docs/contract_surfaces.json').unlink()
        body = minimal_surface().replace('tests/fixtures/contract/compiled_profile.json',
                                         'tests/fixtures/contract/surfaces/demo.json')
        (root / 'docs/contract/control.surface.md').write_text(body)
        (root / self.runtime.BASELINE).write_text(self.runtime.canonical(dict(condition=0, dependency=0, effect=1, when=0)))
        self.evidence.capture_tracked('legacy release with current authored tree')
        return root

    def write(self, root, release):
        values = self.runtime.render(root, release, refresh_shapes=True)
        for name, _, after in values:
            (root / name).write_text(after)
        return values

    def released(self):
        root = self.fixture()
        self.write(root, 'v0.3.7')
        self.commit(root, 'v0.3.7')
        return root

    def test_prepared_tree_release_reproduces_after_tag_and_preserves_legacy_removal(self):
        root = self.released()
        self.assertTrue(self.runtime.check(root, require_history=True))
        self.assertTrue(all(before == after for _, before, after in self.runtime.render(root)))
        state = self.runtime.stamps(root)
        self.assertEqual(state['demo']['stamp'], 'v0.3.7')
        self.assertEqual(state['retired']['stamp'], 'v0.3.7')
        self.assertTrue(state['retired']['removed'])
        path = root / 'docs/contract/control.surface.md'
        before = path.read_text()
        after = before.replace('The phase\'s declared identifier.', 'The next release changes this model meaning.')
        self.assertNotEqual(before, after)
        path.write_text(after)
        self.write(root, 'v0.3.8')
        self.commit(root, 'v0.3.8')
        self.assertTrue(self.runtime.check(root, require_history=True))
        state = self.runtime.stamps(root)
        self.assertEqual(state['demo']['stamp'], 'v0.3.8')
        self.assertEqual(state['retired']['stamp'], 'v0.3.7')
        self.assertEqual([tag for tag, _ in self.runtime.history(root)], ['v0.3.6', 'v0.3.7', 'v0.3.8'])

    def test_history_free_check_preserves_tables_and_release_regeneration_refuses(self):
        root = self.released()
        self.git(root, 'tag', '-d', 'v0.3.6', 'v0.3.7')
        paths = (*self.runtime.OUTPUTS, 'docs/contract/public.json', self.runtime.BASELINE)
        before = {name: (root / name).read_bytes() for name in paths}
        self.assertFalse(self.runtime.check(root))
        with self.assertRaisesRegex(ValueError, 'history unavailable'):
            self.runtime.check(root, require_history=True)
        for release in (None, 'v0.3.7', 'v0.3.8'):
            with self.subTest(release=release), self.assertRaisesRegex(ValueError, 'history unavailable'):
                self.runtime.render(root, release)
        self.assertEqual(before, {name: (root / name).read_bytes() for name in paths})
        path = root / 'docs/CONTRACT.md'
        path.write_text(path.read_text().replace('The phase\'s declared identifier.', 'Stale rendered meaning.'))
        with self.assertRaisesRegex(ValueError, 'stale generated contract'):
            self.runtime.check(root)

    def test_history_dependency_survives_all_surfaces_moving_to_new_layout(self):
        root = self.released()
        self.git(root, 'tag', '-d', 'v0.3.6')
        with self.assertRaisesRegex(ValueError, 'history unavailable.*v0.3.6'):
            self.runtime.render(root)
        with self.assertRaisesRegex(ValueError, 'history unavailable.*v0.3.6'):
            self.runtime.history(root)

    def test_released_snapshot_remains_readable_when_authoring_syntax_changes(self):
        root = self.released()
        expected = self.runtime.history(root)
        path = root / 'docs/contract/control.surface.md'
        path.write_text('Unrecognizable future authoring syntax.\n')
        self.assertEqual(self.runtime.history(root), expected)
        with self.assertRaises(ValueError):
            self.runtime.render(root)

    def test_unknown_released_layout_and_missing_legacy_input_refuse(self):
        root = self.released()
        (root / 'docs/contract/public.json').unlink()
        self.commit(root, 'v0.3.8')
        with self.assertRaisesRegex(ValueError, 'v0.3.8: missing or unsupported'):
            self.runtime.history(root)
        root = self.fixture()
        # The legacy manifest at this new tag refers to a missing required
        # region/golden. A current-tree copy cannot fill the released input.
        legacy_manifest = self.git(root, 'show', 'v0.3.6:docs/contract_surfaces.json')
        (root / 'docs/contract_surfaces.json').write_text(legacy_manifest)
        (root / 'tests/fixtures/contract/surfaces/retired.json').unlink()
        self.commit(root, 'v0.3.7')
        with self.assertRaisesRegex(ValueError, 'v0.3.7: missing contract history input'):
            self.runtime.history(root)

    def test_guide_and_support_edits_leave_public_stamps_while_meaning_changes_move_them(self):
        root = self.released()
        guide = root / 'docs/PolicyWitness.md'
        guide.write_text(guide.read_text() + '\nAn unrelated workflow explanation.\n')
        source = root / 'docs/contract/control.surface.md'
        before = source.read_text()
        changed = before.replace('Supplies no evidence of product execution.', 'This fixture supports authoring checks only.')
        self.assertNotEqual(changed, before)
        source.write_text(changed)
        self.assertEqual(self.runtime.stamps(root)['demo']['stamp'], 'v0.3.7')
        source.write_text(changed.replace('The phase\'s declared identifier.', 'A changed public field meaning.'))
        self.assertEqual(self.runtime.stamps(root)['demo']['stamp'], 'unreleased')
