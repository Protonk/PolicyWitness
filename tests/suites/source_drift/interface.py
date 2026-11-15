"""Interface inventory, its joins, the residue baseline, the contract join and the literal rule: refusal controls."""
import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'docs'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import receipts
import fixture_inputs
import check
import interface_literals


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


generator = module('generate_interface', ROOT / 'docs/generate_interface.py')
contract = module('generate_contract_stamps_for_interface', ROOT / 'docs/generate_contract_stamps.py')


class InterfaceInventoryTests(receipts.TestCase):
    def setUp(self):
        self.inventory = json.loads((ROOT / generator.INVENTORY).read_text())

    def fixture(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-interface-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        fixture_inputs.copy_declared(ROOT, root, fixture_inputs.generator_inputs(ROOT, 'interface'))
        self.track_inputs(root)
        return root

    def command(self, root, *args):
        if root == ROOT:
            self.track_inputs(root, fixture_inputs.generator_inputs(root, 'interface'))
        return self.run_command([sys.executable, '-B', '-S', str(root / generator.GENERATOR_NAME), *args],
                                cwd=root, capture_output=True, text=True, timeout=60)

    def with_inventory(self, mutate):
        root = self.fixture()
        data = copy.deepcopy(self.inventory)
        mutate(data)
        (root / generator.INVENTORY).write_text(json.dumps(data, indent=2) + '\n')
        return root

    def entry(self, data, identifier):
        return next(entry for entry in data['entries'] if entry['id'] == identifier)

    def refused(self, root, expected, *args):
        """Both modes refuse with `expected` and change nothing."""
        before = fixture_inputs.snapshot(root)
        for mode in (('--check',), ()):
            result = self.command(root, *mode, *args)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn(expected, result.stderr)
            self.assertEqual(fixture_inputs.snapshot(root), before, 'a refusal changed the checkout')

    def test_current_copies(self):
        result = self.command(ROOT, '--check')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_stale_refusal_and_no_check_writes(self):
        root = self.fixture()
        joins = root / generator.JOINS
        data = json.loads(joins.read_text())
        data['entries_no_case_reaches'].append('stale.control')
        joins.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
        before = fixture_inputs.snapshot(root)
        result = self.command(root, '--check')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('stale: ' + generator.JOINS, result.stderr)
        self.assertEqual(fixture_inputs.snapshot(root), before)
        self.assertEqual(self.command(root).returncode, 0)
        self.assertEqual(self.command(root, '--check').returncode, 0)

    def test_inventory_refusals(self):
        def token(data):
            data['cards']['run']['text'] = data['cards']['run']['text'].replace('byoxpc', 'private')

        def reference(data):
            data['cards']['base']['references'].append('topic.absent')

        def duplicate(data):
            data['entries'].append(copy.deepcopy(data['entries'][0]))

        def kind(data):
            self.entry(data, 'tail.example')['kind'] = 'tolerates'

        def base(data):
            data['cards']['base']['text'] = 'run\nexample\n'

        def function(data):
            fact = next(f for f in data['result']['derived']['output_functions']
                        if f['of'] == 'normalized_outcome' and f['output'] == 'exit_code')
            fact['is_a_function'] = True

        def shared(data):
            data['result']['derived']['rows_sharing_outputs'].pop()

        def cards(data):
            self.entry(data, 'run.option.timeout_ms')['cards'] = ['run']

        def newline(data):
            data['cards']['result']['text'] += '\n'

        for mutate, expected in ((token, "card run: token 'private' comes from no referenced entry"),
                                 (reference, 'card base: references no entry: topic.absent'),
                                 (duplicate, 'duplicate identifier command.help'),
                                 (kind, "tail.example: unknown admission kind 'tolerates'"),
                                 (base, 'the base card does not list exactly the topic addresses'),
                                 (function, 'exit_code as a function of normalized_outcome is recorded as True; the rows give False'),
                                 (shared, 'rows sharing outputs are recorded as'),
                                 (cards, 'run.option.timeout_ms: its cards disagree with the cards that reference it'),
                                 (newline, 'card result: must end with exactly one newline')):
            with self.subTest(refusal=expected):
                self.refused(self.with_inventory(mutate), expected)

    def test_residue_accepts_reductions_and_refuses_new_members(self):
        # A member that moves between classes leaves every total unchanged and is still an addition.
        def moved(data):
            self.entry(data, 'tail.version')['kind'] = 'discards'
        root = self.with_inventory(moved)
        self.refused(root, 'new residue members need --refresh-residue and a reviewed diff:\n  /non_admits/discards/pub fn run: tail.version')
        result = self.command(root, '--refresh-residue')
        self.assertEqual(result.returncode, 0, result.stderr)
        classes = json.loads((root / generator.RESIDUE).read_text())['classes']['non_admits']
        self.assertIn('tail.version', classes['discards']['pub fn run']['members'])
        self.assertNotIn('tail.version', classes['refuses_always']['pub fn run']['members'])
        self.assertEqual(self.command(root, '--check').returncode, 0)

        # A removed member is a reduction; write mode records it without the refresh flag.
        # The member chosen is named by no retained mutation, which would otherwise be refused first.
        def reduced(data):
            data['entries'] = [entry for entry in data['entries'] if entry['id'] != 'runner_kind.machme@registry']
        root = self.with_inventory(reduced)
        self.assertNotEqual(self.command(root, '--check').returncode, 0)
        result = self.command(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        residue = json.loads((root / generator.RESIDUE).read_text())
        self.assertEqual(residue['classes']['non_admits']['alias']['registry'],
                         {'count': 1, 'members': ['runner_kind.debuggable@registry']})
        self.assertNotIn('runner_kind.machme@registry', residue['identifiers'])

    def test_expanded_enumeration_is_recorded_through_the_refresh(self):
        def expand(data):
            data['entries'] = [entry for entry in data['entries'] if entry['id'] != 'tail.test_input']
            self.entry(data, 'command.test_input')['relationships']['tail'] = 'test_input_arguments'
            template = self.entry(data, 'run.option.timeout_ms')
            for identifier, spelling in (('test_input.read', 'read'), ('test_input.option.target', '--target')):
                data['entries'].append({**copy.deepcopy(template), 'id': identifier, 'spellings': [spelling], 'cards': []})
        root = self.with_inventory(expand)
        self.refused(root, 'new residue members need --refresh-residue')
        before = fixture_inputs.snapshot(root)
        for entry, expected in (('tail.runner', 'tail.runner is still an inventory entry'),
                                ('tail.example', 'names no unenumerated entry of the baseline')):
            result = self.command(root, '--refresh-residue', '--expand', entry)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(expected, result.stderr)
            self.assertEqual(fixture_inputs.snapshot(root), before)
        result = self.command(root, '--expand', 'tail.test_input')
        self.assertIn('--expand records an expansion during --refresh-residue', result.stderr)
        result = self.command(root, '--refresh-residue', '--expand', 'tail.test_input')
        self.assertEqual(result.returncode, 0, result.stderr)
        residue = json.loads((root / generator.RESIDUE).read_text())
        self.assertEqual(residue['expansions'], [{'replaced': 'tail.test_input',
                                                  'exposed': ['test_input.option.target', 'test_input.read']}])
        self.assertNotIn('tail.test_input', residue['classes']['non_admits']['unenumerated']['pub fn run']['members'])
        # The record persists across ordinary runs while an exposed entry remains.
        self.assertEqual(self.command(root).returncode, 0)
        self.assertEqual(json.loads((root / generator.RESIDUE).read_text())['expansions'], residue['expansions'])

    def test_case_association_is_derived_from_arguments_and_required_results(self):
        reached = lambda *arguments: generator.exercised(list(arguments), self.inventory)
        self.assertEqual(reached('help'), ['command.help'])
        self.assertEqual(reached('help', 'run', 'junk'), ['command.help', 'topic.run', 'tail.help'])
        self.assertEqual(reached('help', '--run'), ['command.help', 'tail.help'])
        self.assertEqual(reached('help', {'hex': 'fffe'}), ['command.help', 'tail.help'])
        self.assertEqual(reached('run', '--runner-mode', 'byoxpc', '/r.json'),
                         ['command.run', 'run.option.runner_mode', 'runner_kind.byoxpc@run_option', 'run.request_path'])
        self.assertEqual(reached('run', '--runner-mode', 'machme'), ['command.run', 'run.option.runner_mode'])
        self.assertEqual(reached('run', '/r.json', '--bogus', '--timeout-ms', '5'),
                         ['command.run', 'run.request_path', 'run.unknown_flag'])
        self.assertEqual(reached('run', '--timeout-ms', '5', '--', '/r.json'),
                         ['command.run', 'run.option.timeout_ms', 'run.terminator'])
        self.assertEqual(reached('version'), ['command.version'])
        self.assertEqual(reached('--version', 'x'), ['command.version_flag', 'tail.version_flag'])
        self.assertEqual(reached('runner', 'list'), ['command.runner', 'tail.runner'])
        self.assertEqual(reached('example'), ['command.example'])
        self.assertEqual(reached('bogus'), [])
        self.assertEqual(reached(), [])
        envelope = lambda outcome, ok, status: {'stdout_json': {'/kind': 'run', '/result/normalized_outcome': outcome,
                                                               '/result/ok': ok, '/result/exit_code': status}}
        rows = lambda *fields: generator.result_rows(envelope(*fields), self.inventory)
        self.assertEqual(rows('tool_error', False, 2), ['result.tool_failure'])
        self.assertEqual(rows('finished', True, 0), ['result.admitted_finished'])
        self.assertEqual(rows('xpc_timeout', False, 1), ['result.admission_refusal', 'result.admitted_other'])
        # Two rows select these fields; the association cannot be derived.
        self.assertEqual(rows('bad_request', False, 1), ['result.local_request_refusal', 'result.admitted_other'])
        self.assertEqual(rows('runner_failed', False, 1), ['result.admitted_other'])
        self.assertEqual(rows('finished', False, 1), [])
        self.assertEqual(generator.result_rows({'stdout_json': {'/kind': 'version', '/result/ok': True}}, self.inventory), [])
        request = json.dumps({'contract': '{contract}', 'runner': {'mode': 'standard'}})
        self.assertEqual(generator.content_entries({'args': ['run', '{scratch}/r.json'], 'status': 2,
                                                    'files': {'r.json': request}}, self.inventory),
                         ['runner_kind.standard@request_selector'])
        self.assertEqual(generator.content_entries({'args': ['example'], 'status': 0}, self.inventory), ['example.document'])
        self.assertEqual(generator.content_entries({'args': ['example', 'x'], 'status': 2}, self.inventory), [])

    def test_join_records_are_checked(self):
        root = self.fixture()
        record = json.loads((root / generator.MUTATIONS).read_text())
        for mutate, expected in (
                (lambda r: r['mutations'].append({'id': 'control', 'entry': 'run.option.absent', 'mutation': 'x',
                                                  'checks': {'card': 'changed', 'contract': 'unchanged', 'cases': 'failed'}}),
                 'mutation control: names no entry: run.option.absent'),
                (lambda r: r['mutations'].append({'id': 'control', 'entry': 'command.run', 'mutation': 'x',
                                                  'checks': {'card': 'changed', 'contract': 'passed', 'cases': 'failed'}}),
                 "mutation control: each of ('card', 'contract', 'cases') takes one of"),
                (lambda r: r['mutations'].append({'id': 'control', 'entry': 'command.run', 'mutation': 'x',
                                                  'checks': {'card': 'changed', 'cases': 'failed'}}),
                 "mutation control: each of ('card', 'contract', 'cases') takes one of"),
                (lambda r: r['declared_associations'].append({'case': 'help.base', 'entry': 'topic.absent', 'reason': 'x'}),
                 'declared association names no entry: topic.absent'),
                (lambda r: r['declared_associations'].append({'case': 'absent.case', 'entry': 'command.run', 'reason': 'x'}),
                 'declared association names no case: absent.case')):
            with self.subTest(refusal=expected):
                data = copy.deepcopy(record)
                mutate(data)
                (root / generator.MUTATIONS).write_text(json.dumps(data))
                self.refused(root, expected)
        (root / generator.MUTATIONS).write_text(json.dumps(record))
        self.assertEqual(self.command(root, '--check').returncode, 0)

    def test_contract_join_compares_structured_facts_and_reports_prose(self):
        tree = contract.contract_module('tree').load_tree(ROOT)
        join = contract.contract_module('interface_join')
        problems, report = join.join(tree, self.inventory)
        self.assertEqual(problems, [])
        compared = {item['node']: len(item['compared']) for item in report}
        self.assertEqual(compared, {'request.specimen.emit_example': 0, 'request.options.precedence': 0,
                                    'refusals.controller.consequence.request_refusal': 3,
                                    'refusals.controller.consequence.tool_failure': 3,
                                    'envelope.data.select.finished': 4, 'envelope.data.select.other': 5})
        # A node with nothing compared is reported with the prose that stands uncompared.
        for item in report:
            if not item['compared']:
                self.assertTrue(item['prose'], item['node'])
        self.assertEqual(next(item for item in report if item['node'] == 'request.options.precedence')['free'], ['free.effect'])
        rows = lambda data: {row['id']: row for row in data['result']['rows']}

        def swap(data):
            first, second = rows(data)['result.admitted_finished'], rows(data)['result.admitted_other']
            first['order'], second['order'] = second['order'], first['order']

        for mutate, expected in (
                (lambda d: rows(d)['result.tool_failure']['outputs'].update(exit_code=3),
                 'set_value(envelope.result.exit_code, 2) disagrees with result.tool_failure, whose exit_code is 3'),
                (lambda d: rows(d)['result.admitted_finished']['outputs'].update(ok=False),
                 'set_value(envelope.result.ok, True) disagrees with result.admitted_finished, whose ok is false'),
                (lambda d: rows(d)['result.local_request_refusal']['outputs'].update(normalized_outcome={'fixed': 'refused'}),
                 "test envelope.result.normalized_outcome == 'bad_request' disagrees with result.local_request_refusal"),
                (lambda d: rows(d)['result.local_request_refusal']['outputs'].update(ok=True),
                 'set_value(envelope.result.ok, False) disagrees with result.local_request_refusal, whose ok is true'),
                (lambda d: rows(d)['result.admitted_finished']['inputs'].update(host_outcome={'is': 'bad_request'}),
                 "test envelope.data.runner_result.normalized_outcome == 'finished' disagrees with result.admitted_finished"),
                (lambda d: rows(d)['result.admitted_other']['inputs'].update(host_outcome='absent'),
                 'test True under a present host reply disagrees with result.admitted_other'),
                (lambda d: rows(d)['result.admitted_other']['outputs'].update(normalized_outcome={'fixed': 'failed'}),
                 'retains the host label, but result.admitted_other gives {"fixed": "failed"}'),
                (swap, "envelope.data.select: its first-match cases cite rows out of the relation's order"),
                (lambda d: d['result']['rows'].remove(rows(d)['result.tool_failure']),
                 'refusals.controller.consequence.tool_failure: interface names no inventory entry: result.tool_failure'),
                (lambda d: d['entries'].remove(self.entry(d, 'run.option.runner_mode')),
                 'request.options.precedence: interface names no inventory entry: run.option.runner_mode')):
            with self.subTest(disagreement=expected):
                data = copy.deepcopy(self.inventory)
                mutate(data)
                found, _ = join.join(tree, data)
                self.assertTrue(any(expected in problem for problem in found), found)

    def literal_fixture(self):
        directory = tempfile.TemporaryDirectory(prefix='pw-interface-literals-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        rule = next(rule for rule in check.RULES if rule.id == 'interface_literals')
        fixture_inputs.copy_declared(ROOT, root, fixture_inputs.expand(ROOT, rule.inputs, rule.helpers))
        self.track_inputs(root)
        return root

    def test_literal_rule_refuses_spellings_beside_the_tables(self):
        root = self.literal_fixture()
        self.assertEqual(interface_literals.findings(root, self.inventory), [])

        def edited(relative, old, new, expected):
            path = root / relative
            original = path.read_text()
            self.assertEqual(original.count(old), 1, (relative, old))
            path.write_text(original.replace(old, new))
            found = [message for _, _, message in interface_literals.findings(root, self.inventory)]
            path.write_text(original)
            self.assertTrue(found and all(expected in message for message in found), found)

        edited('controller/src/run_flow.rs', '        let arg = args[idx].to_string_lossy();\n',
               '        let arg = args[idx].to_string_lossy();\n        if arg == "--help" {\n            break;\n        }\n',
               'fn parse_arguments: compared with a literal: "--help"')
        edited('controller/src/cli.rs', 'pub fn run(argv: Vec<OsString>) -> i32 {\n',
               'pub fn run(argv: Vec<OsString>) -> i32 {\n    match argv.first().and_then(|first| first.to_str()) {\n'
               '        Some("-h") => return help::cmd_help(&[]),\n        _ => {}\n    }\n',
               'pub fn run: matched against a literal pattern: "-h"')
        edited('controller/src/help.rs', '    let card = card(Topic::select(tail));\n',
               '    let card = card(Topic::select(tail).filter(|_| !tail[0].to_string_lossy().starts_with("res")));\n',
               'pub fn cmd_help: starts_with on a literal: "res"')
        edited('controller/src/runner_select.rs', '    Reader::RequestSelector.resolve(value).ok_or_else(|| {\n',
               '    if matches!(value, "legacy") {\n        return Ok(RunnerKind::Byoxpc);\n    }\n'
               '    Reader::RequestSelector.resolve(value).ok_or_else(|| {\n',
               'fn parse_runner_mode: matched against a literal pattern: "legacy"')
        edited('controller/interface/cards.rs', '            out.line(depth, option.def().spelling);\n',
               '            out.line(depth, if depth > 9 { "--runner-mode" } else { option.def().spelling });\n',
               'the card renderer spells a card element itself: "--runner-mode"')
        edited('controller/src/runner_commands.rs', '    Reader::InstallOption\n',
               '    let _hint = "use byoxpc, not machme";\n    Reader::InstallOption\n',
               'a literal spells a word the runner-kind table aliases: "use byoxpc, not machme"')
        edited('controller/src/run_flow.rs', 'fn parse_arguments(args: &[OsString]) -> Arguments {',
               'fn parse_argument_vector(args: &[OsString]) -> Arguments {',
               "cannot read the governed block 'fn parse_arguments'")
        # A diagnostic, a field name passed as an argument and test code are not comparisons.
        self.assertEqual(interface_literals.findings(root, self.inventory), [])


if __name__ == '__main__':
    sys.exit(receipts.timed_main(sys.modules[__name__], 'source_drift/interface_inventory', 'interface'))
