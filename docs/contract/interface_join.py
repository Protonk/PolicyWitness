"""Join contract nodes to the committed interface inventory.

A node's `interface` fact lists inventory identifiers. Each must resolve, and
the node's structured facts are compared with the entry: literal `set_value`
effects on result fields, `test` comparisons with literals, listed vocabulary
values, inherited effects and applicability, and the order of first-match
cases. The report names what was compared and what was not; a resolved
identifier gives no credit to prose or `free.*` text beside it.
"""
import ast
import json

INVENTORY = 'controller/interface/inventory.json'
# Operand bindings: where the contract writes the run result's fields and the
# admitted host reply. `normalized_outcome` names both an output and the host
# label, so the comparison cannot go by the last path component alone.
RESULT = 'envelope.result.'
HOST_REPLY = 'envelope.data.runner_result'
HOST_OUTCOME = HOST_REPLY + '.normalized_outcome'


def load(root):
    return json.loads((root / INVENTORY).read_text())


def identifiers(inventory):
    """Every citable identifier with its kind of record."""
    known = {entry['id']: ('entry', entry) for entry in inventory['entries']}
    known.update({row['id']: ('row', row) for row in inventory['result']['rows']})
    known['result.fields'] = ('fields', inventory['result']['fields'])
    known[inventory['example']['id']] = ('example', inventory['example'])
    return known


def _path(expression):
    return ast.unparse(expression) if isinstance(expression, (ast.Attribute, ast.Name)) else None


def _literal(expression):
    """(True, value) for a literal the comparison reads; (False, None) otherwise."""
    if isinstance(expression, ast.Constant) and type(expression.value) in (bool, int, str):
        return True, expression.value
    if isinstance(expression, ast.Name) and expression.id in ('True', 'False'):
        return True, expression.id == 'True'
    return False, None


def _body(node, key):
    expression = node.expressions.get(key)
    return getattr(expression, 'body', expression)


def _set_values(node):
    """`set_value(target, value)` calls of the node and of the rule and cases enclosing it."""
    calls, current = [], node
    while current is not None and current.kind not in ('subject', 'surface'):
        body = _body(current, 'effects')
        items = body.elts if isinstance(body, (ast.List, ast.Tuple)) else [body] if body is not None else []
        for item in items:
            if isinstance(item, ast.Call) and getattr(item.func, 'id', None) == 'set_value':
                calls.append((current.id, item.args[0], item.args[1]))
        current = current.parent
    return calls


def _same(expected, actual):
    return type(expected) is type(actual) and expected == actual


def _host_present(node):
    when = node.context.get('when')
    if not when:
        return False
    def requires_presence(item):
        if isinstance(item, ast.BoolOp) and isinstance(item.op, ast.And):
            return any(requires_presence(term) for term in item.values)
        return (isinstance(item, ast.Call) and getattr(item.func, 'id', None) == 'present'
                and len(item.args) == 1 and _path(item.args[0]) == HOST_REPLY)
    return requires_presence(ast.parse(when, mode='eval').body)


def _compare_row(node, row, outputs, problems, compared, uncompared):
    uncompared.append(f'{row["id"]}: input class {json.dumps(row["inputs"]["class"])} '
                      '(no structured contract binding)')
    for owner, target, value in _set_values(node):
        path = _path(target) or ''
        if not path.startswith(RESULT) or path[len(RESULT):] not in outputs:
            continue
        name = path[len(RESULT):]
        expected = row['outputs'][name]
        literal, authored = _literal(value)
        label = f'{owner}: set_value({path}, {ast.unparse(value)})'
        if literal:
            fixed = expected.get('fixed') if isinstance(expected, dict) else expected
            if isinstance(expected, dict) and 'fixed' not in expected or not _same(fixed, authored):
                problems.append(f'{node.id}: {label} disagrees with {row["id"]}, whose {name} is {json.dumps(expected)}')
            compared.append(label)
        elif _path(value) == HOST_OUTCOME:
            if expected != 'host_label':
                problems.append(f'{node.id}: {label} retains the host label, but {row["id"]} gives {json.dumps(expected)}')
            compared.append(label)
        else:
            uncompared.append(label)
    test = _body(node, 'test')
    if test is None:
        return
    label = f'{node.id}: test {ast.unparse(test)}'
    host = row['inputs']['host_outcome']
    if (isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)
            and _literal(test.comparators[0])[0]):
        authored = _literal(test.comparators[0])[1]
        left = _path(test.left)
        if left == RESULT + 'normalized_outcome':
            expected = row['outputs']['normalized_outcome']
            if not isinstance(expected, dict) or not _same(expected.get('fixed'), authored):
                problems.append(f'{label} disagrees with {row["id"]}, whose normalized_outcome is {json.dumps(expected)}')
            compared.append(label)
            return
        if left == HOST_OUTCOME:
            if host != {'is': authored}:
                problems.append(f'{label} disagrees with {row["id"]}, whose host label condition is {json.dumps(host)}')
            compared.append(label)
            return
    if _literal(test) == (True, True) and _host_present(node):
        # The last case of a first-match rule that applies to a present host reply.
        if host != 'present':
            problems.append(f'{label} under a present host reply disagrees with {row["id"]}, '
                            f'whose host label condition is {json.dumps(host)}')
        compared.append(label + ' under present(' + HOST_REPLY + ')')
        return
    uncompared.append(label)


def join(tree, inventory):
    """(problems, report) for every node that cites the inventory."""
    known = identifiers(inventory)
    outputs = [field['name'] for field in inventory['result']['fields']]
    problems, report = [], []
    for node in tree.nodes:
        cited = node.facts.get('interface')
        if not cited:
            continue
        compared, uncompared = [], []
        if node.context.get('when'):
            # A fallback test can use a necessary presence conjunct below;
            # the complete applicability expression is not evaluated here.
            uncompared.append(f'{node.id}: applicability {node.context["when"]}')
        rows = []
        for identifier in cited:
            if identifier not in known:
                problems.append(f'{node.id}: interface names no inventory entry: {identifier}')
                continue
            kind, value = known[identifier]
            if kind == 'row':
                rows.append(value)
                _compare_row(node, value, outputs, problems, compared, uncompared)
        if 'values' in node.facts:
            spelled = sorted(spelling for identifier in cited if known.get(identifier, ('', None))[0] == 'entry'
                             for spelling in known[identifier][1]['spellings'])
            label = f'{node.id}: values {json.dumps(node.facts["values"])}'
            if sorted(node.facts['values']) != spelled:
                problems.append(f'{label} disagrees with the cited entries, which spell {json.dumps(spelled)}')
            compared.append(label)
        report.append({
            'node': node.id, 'interface': cited, 'compared': compared, 'uncompared': uncompared,
            'free': sorted(key for key in node.facts if key.startswith('free.')),
            'free_when': node.context.get('free_when', []),
            'prose': bool(node.prose.strip()),
            '_rows': [row['id'] for row in rows],
        })
    # First-match cases must cite rows in the relation's own order.
    cases = {item['node']: item['_rows'] for item in report}
    order = {row['id']: row['order'] for row in inventory['result']['rows']}
    for node in tree.nodes:
        if node.facts.get('selection') != 'first_match':
            continue
        sequence = [(child.id, order[row]) for child in node.children if child.kind == 'outcome'
                    for row in cases.get(child.id, [])]
        if [position for _, position in sequence] != sorted(position for _, position in sequence):
            problems.append(f'{node.id}: its first-match cases cite rows out of the relation\'s order: '
                            + ', '.join(f'{child} ({position})' for child, position in sequence))
        elif len(sequence) > 1:
            for item in report:
                if item['node'] == sequence[-1][0]:
                    item['compared'].append(f'{node.id}: first-match case order')
    for item in report:
        del item['_rows']
    return problems, report


def check(root, tree):
    """Refuse an unresolved identifier or a structured fact the inventory contradicts."""
    if not any(node.facts.get('interface') for node in tree.nodes):
        return []
    try:
        inventory = load(root)
    except (OSError, ValueError) as error:
        raise ValueError(f'interface inventory unavailable: {INVENTORY}: {error}') from None
    problems, report = join(tree, inventory)
    if problems:
        raise ValueError('contract and interface inventory disagree:\n  ' + '\n  '.join(problems))
    return report
