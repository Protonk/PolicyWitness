"""Parse, check and render the authored public-contract tree.

Markdown owns the hierarchy. Expressions describe relationships; this module
checks their syntax and references and never evaluates a contract condition.
"""
from __future__ import annotations

import ast
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import sys

DOCS = Path(__file__).resolve().parents[1]
if str(DOCS) not in sys.path:
    sys.path.insert(0, str(DOCS))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import generator_common
import markdown_reader
import record_definitions

SYNTAX = 1
PARTS = ('identity', 'definitions', 'input', 'delivery', 'report',
         'assessment', 'installation', 'version')
RULE_KINDS = {'acts', 'reports', 'checks'}
KINDS = {'surface', 'subject', 'definition', 'field', *RULE_KINDS,
         'condition', 'effect', 'outcome', 'gap', 'example', 'owner'}
ANNOTATION = re.compile(r'(.*?)\s+\{([a-z_][a-z0-9_]*):\s*([a-z_]+)\}')
IDENTIFIER = re.compile(r'[a-z_][a-z0-9_]*')
SET_CONTEXT = {'entry', 'recipient', 'report'}
CONTEXT = {'who', 'where', *SET_CONTEXT, 'when'}
EXPRESSION_KEYS = {'when', 'test', 'effects', 'object', 'required_when', 'present_when'}
FREE_KINDS = {'when', 'condition', 'dependency', 'effect'}
ORDER_KINDS = {*RULE_KINDS, 'condition', 'effect', 'outcome'}
AUXILIARY = {'gap', 'example', 'owner'}
CHILDREN = {
    'surface': {'subject', 'definition', *AUXILIARY},
    'subject': {'subject', 'definition', 'field', *RULE_KINDS, *AUXILIARY},
    'definition': {'definition', 'condition', 'outcome', *AUXILIARY},
    'field': {'condition', 'outcome', *AUXILIARY},
    'acts': {'condition', 'effect', 'outcome', *AUXILIARY},
    'reports': {'condition', 'effect', 'outcome', *AUXILIARY},
    'checks': {'condition', 'effect', 'outcome', *AUXILIARY},
    'condition': {'condition', 'effect', *AUXILIARY},
    'effect': {'effect', *AUXILIARY},
    'outcome': {'condition', 'effect', *AUXILIARY},
    'gap': {'owner'}, 'example': {'owner', 'gap'}, 'owner': set(),
}
COMMON_FACTS = {*CONTEXT, 'uses', 'after', 'precedes', 'requires'}
FACTS_BY_KIND = {
    'surface': {'syntax', 'artifact', 'part', 'goldens', 'checks', 'coverage'},
    'subject': {'record', 'as', 'at', 'part', 'coverage', 'open'},
    'definition': {'defines', 'type', 'value', 'object'},
    'field': {'name', 'type', 'optional', 'json_null', 'projection', 'default',
              'vocabulary', 'listed', 'values', 'unknown', 'required_when', 'present_when'},
    'acts': {'effects', 'failure'},
    'reports': {'effects', 'failure'},
    'checks': {'test', 'effects', 'failure'},
    'condition': {'test'},
    'effect': {'on', 'effects'},
    'outcome': {'value', 'object', 'test', 'effects'},
    'gap': {'kind', 'scope'},
    'example': set(),
    'owner': {'scope', 'grade', 'source', 'check', 'pins', 'context', 'limits',
              'run', 'source_snapshot', 'build', 'release', 'case'},
}
DEFINITION_KINDS = {'action', 'event', 'assessment', 'record', 'condition',
                    'value', 'component', 'boundary', 'entry', 'recipient', 'report'}
CALL_ARITY = {'present': 1, 'absent': 1, 'implies': 2, 'ref': 1, 'later': 2,
              'set_value': 2, 'prevent': 2, 'retain_records': 1,
              'retain_assessments': 1, 'withhold': 1, 'emit': 2,
              'count': 1, 'length': 1, 'variant': 2}
EFFECT_CALLS = {'set_value', 'prevent', 'retain_records', 'retain_assessments',
                'withhold', 'emit'}
COMPARE_OPERATORS = {ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
                     ast.In, ast.NotIn}
PUBLIC_EXCLUSIONS = {'syntax', 'goldens', 'checks', 'coverage'}


class ContractError(ValueError):
    pass


@dataclass
class Binding:
    domain: str
    member_type: str
    index_type: str = 'Int'


@dataclass
class Node:
    id: str
    local: str
    kind: str
    title: str
    level: int
    facts: dict
    prose: str
    source: str
    line: int
    fact_lines: dict = field(default_factory=dict)
    parent: Node | None = None
    children: list[Node] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    aliases: dict = field(default_factory=dict)
    bindings: dict = field(default_factory=dict)
    expressions: dict = field(default_factory=dict)
    references: set = field(default_factory=set)
    object_types: dict = field(default_factory=dict)
    record: str | None = None
    field_info: dict | None = None

    @property
    def surface_id(self):
        return self.id.split('.')[0]

    def fail(self, message, key=None):
        line = self.fact_lines.get(key, self.line)
        raise ContractError(f'{self.source}:{line}: {self.id}: {message}')

    def descendants(self):
        for child in self.children:
            yield child
            yield from child.descendants()


@dataclass
class Tree:
    root: Path
    nodes: list[Node]
    index: dict
    records: dict
    aliases: dict
    surfaces: list[Node]
    free_counts: dict
    paths: list[str]
    read: object
    strict: bool
    uncovered_records: list[str] = field(default_factory=list)


def _relative(path):
    value = Path(path)
    if value.is_absolute() or '..' in value.parts or value.as_posix() != str(path):
        raise ContractError(f'invalid repository-relative path {path!r}')
    return value.as_posix()


def parse_surface(text, name):
    """Parse one Markdown surface without importing records or resolving refs."""
    document = markdown_reader.parse(text, name)
    headings = document.headings
    if not headings:
        raise ContractError(f'{name}:1: expected a surface heading')
    if text[:document.offset(headings[0].line)].strip():
        raise ContractError(f'{name}:1: content precedes the surface heading')
    nodes, stack, consumed = [], [], set()
    source_lines = text.splitlines()
    for i, heading in enumerate(headings):
        match = ANNOTATION.fullmatch(heading.text)
        if not match or match[3] not in KINDS:
            raise ContractError(f'{name}:{heading.line + 1}: expected a typed node heading')
        title, local, kind = match.groups()
        if not title.strip():
            raise ContractError(f'{name}:{heading.line + 1}: node title is empty')
        while stack and stack[-1].level >= heading.level:
            stack.pop()
        parent = stack[-1] if stack else None
        if parent:
            if heading.level != parent.level + 1 or kind not in CHILDREN[parent.kind]:
                raise ContractError(f'{name}:{heading.line + 1}: illegal {kind} beneath {parent.kind}')
        elif heading.level != 1 or kind != 'surface' or nodes:
            raise ContractError(f'{name}:{heading.line + 1}: expected exactly one level-one surface')
        ident = f'{parent.id}.{local}' if parent else local
        end = headings[i + 1].line if i + 1 < len(headings) else len(source_lines)
        blocks = [b for b in document.fences('contract') if heading.line < b.lines[0] < end]
        if len(blocks) > 1:
            raise ContractError(f'{name}:{heading.line + 1}: more than one facts block on {ident}')
        facts, fact_lines = {}, {}
        start = heading.line + 1
        if blocks:
            block = blocks[0]
            if '\n'.join(source_lines[start:block.lines[0]]).strip():
                raise ContractError(f'{name}:{block.lines[0] + 1}: facts must precede node prose')
            consumed.add(block.lines)
            for j, raw in enumerate(block.content.splitlines()):
                if not raw.strip():
                    continue
                key, separator, value = raw.partition(':')
                key = key.strip()
                line = block.lines[0] + j + 2
                allowed = FACTS_BY_KIND[kind] | (COMMON_FACTS if kind != 'owner' else set())
                dynamic = key.startswith(('bind.', 'match.', 'free.')) and kind != 'owner'
                if not separator or key in facts or (key not in allowed and not dynamic):
                    raise ContractError(f'{name}:{line}: duplicate, unknown or inapplicable fact {key!r}')
                value = value.strip()
                if not value:
                    raise ContractError(f'{name}:{line}: fact {key!r} has no value')
                try:
                    parsed = (value if key in EXPRESSION_KEYS or dynamic else json.loads(value))
                except json.JSONDecodeError as error:
                    raise ContractError(f'{name}:{line}: {key}: {error.msg}') from None
                facts[key], fact_lines[key] = parsed, line
            start = block.lines[1]
        prose = '\n'.join(source_lines[start:end]).strip()
        node = Node(ident, local, kind, title.strip(), heading.level, facts, prose,
                    str(name), heading.line + 1, fact_lines, parent)
        if parent:
            parent.children.append(node)
        nodes.append(node)
        stack.append(node)
    if any(b.lines not in consumed for b in document.fences('contract')):
        raise ContractError(f'{name}: unowned contract facts block')
    return nodes


def _native(text):
    if not isinstance(text, str) or not text:
        raise ValueError('type must be a nonempty string')
    aliases = {'string': 'String', 'boolean': 'Bool', 'integer': 'Int',
               'number': 'Number', 'object': 'JSON', 'null': 'Null',
               'JSON value': 'JSON', 'array': '[JSON]'}
    optional = text.endswith('?')
    raw = text[:-1] if optional else text
    if raw.startswith('[') and raw.endswith(']'):
        interior = raw[1:-1]
        if interior.startswith('String: '):
            raw = '[String: ' + _native(interior[8:]) + ']'
        else:
            raw = '[' + _native(interior) + ']'
    else:
        raw = aliases.get(raw, raw)
    return raw + ('?' if optional else '')


def _category(native, records):
    raw = native.removesuffix('?')
    if raw.startswith('@'):
        return raw[1:]
    if raw.startswith('[String: '):
        return 'map'
    if raw.startswith('['):
        return 'list'
    if raw in records:
        return 'union' if records[raw].get('variants') else 'record'
    if raw == 'Bool':
        return 'boolean'
    if raw in {'String', 'Data'}:
        return 'string'
    if raw in {'Index', 'Number', 'Double', 'Float'} or re.fullmatch(r'U?Int(?:8|16|32|64|128)?', raw):
        return 'number'
    if raw == 'Null':
        return 'null'
    if raw == 'JSON':
        return 'json'
    return 'unknown'


def _known_type(native, records):
    raw = native.removesuffix('?')
    if raw.startswith('[String: ') and raw.endswith(']'):
        return _known_type(raw[9:-1], records)
    if raw.startswith('[') and raw.endswith(']'):
        return _known_type(raw[1:-1], records)
    return _category(raw, records) != 'unknown'


def _compatible(left, right, records):
    a, b = _category(left, records), _category(right, records)
    if a == 'json' or b == 'json':
        return True
    if a == 'null' or b == 'null':
        return a == b or (right if a == 'null' else left).endswith('?')
    if a in {'number', 'string', 'boolean'}:
        return a == b
    return left.removesuffix('?') == right.removesuffix('?')


def _reference(tree, node, ident, key=None, allowed=None):
    if not isinstance(ident, str) or ident not in tree.index:
        node.fail(f'unresolved node reference {ident!r}', key)
    target = tree.index[ident]
    if target.kind == 'owner' or (allowed is not None and target.kind not in allowed):
        node.fail(f'inappropriate {target.kind} reference {ident!r}', key)
    node.references.add(ident)
    return target


def _ref_type(target):
    if target.kind in {'condition', 'checks'}:
        return 'Bool'
    if target.kind == 'acts':
        return '@action'
    if target.kind == 'field' and target.field_info:
        return target.field_info['swift_type']
    if target.kind == 'subject' and target.record:
        return target.record
    if target.kind == 'definition':
        defines = target.facts.get('defines', 'value')
        if defines == 'condition':
            return 'Bool'
        if defines in {'action', 'event', 'assessment', 'record'}:
            return '@' + defines
        if 'type' in target.facts:
            return _native(target.facts['type'])
        return '@' + defines
    return '@definition'


class Expressions:
    def __init__(self, tree, node, key):
        self.tree, self.node, self.key = tree, node, key

    def fail(self, text):
        self.node.fail(text, self.key)

    def category(self, native):
        return _category(native, self.tree.records)

    def boolean(self, native):
        if self.category(native) != 'boolean':
            self.fail(f'condition operand has type {native}, expected boolean')

    def parse(self, text, expected=None):
        if not isinstance(text, str):
            self.fail('expression must be a string')
        try:
            expression = ast.parse(text, mode='eval')
        except (SyntaxError, RecursionError) as error:
            self.fail(f'invalid expression: {error}')
        native = self.infer(expression.body)
        if expected == 'boolean':
            self.boolean(native)
        elif expected == 'effects':
            if native != '@effect' and native != '[@effect]':
                self.fail('effects require effect calls or a list of effect calls')
        return expression

    def infer(self, value):
        records, node = self.tree.records, self.node
        if isinstance(value, ast.Constant):
            if isinstance(value.value, bool): return 'Bool'
            if isinstance(value.value, int): return 'Int'
            if isinstance(value.value, float): return 'Number'
            if isinstance(value.value, str): return 'String'
            if value.value is None: return 'Null'
            self.fail('unsupported literal')
        if isinstance(value, ast.Name):
            if value.id in node.aliases:
                return node.aliases[value.id]
            if value.id in node.bindings:
                return node.bindings[value.id].index_type
            self.fail(f'unknown object or bound index {value.id!r}')
        if isinstance(value, ast.Attribute):
            owner = self.infer(value.value).removesuffix('?')
            if owner not in records or value.attr not in records[owner]['fields']:
                self.fail(f'unknown field {ast.unparse(value)}')
            info = records[owner]['fields'][value.attr]
            node.object_types[ast.unparse(value)] = _public_field(records[owner], info)
            return info['swift_type']
        if isinstance(value, ast.Subscript):
            owner = self.infer(value.value).removesuffix('?')
            if self.category(owner) not in {'list', 'map'}:
                self.fail('index applied to a noncollection')
            if not isinstance(value.slice, ast.Name) or value.slice.id not in node.bindings:
                self.fail('collection index is not bound')
            binding = node.bindings[value.slice.id]
            if binding.domain != ast.unparse(value.value):
                self.fail(f'index {value.slice.id!r} belongs to {binding.domain}, not {ast.unparse(value.value)}')
            return binding.member_type
        if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            if not value.elts:
                return '[JSON]'
            members = [self.infer(item) for item in value.elts]
            native = members[0] if all(item == members[0] for item in members) else 'JSON'
            return '[' + native + ']'
        if isinstance(value, ast.BoolOp) and isinstance(value.op, (ast.And, ast.Or)):
            for item in value.values:
                self.boolean(self.infer(item))
            return 'Bool'
        if isinstance(value, ast.UnaryOp):
            operand = self.infer(value.operand)
            if isinstance(value.op, ast.Not):
                self.boolean(operand)
                return 'Bool'
            if isinstance(value.op, (ast.USub, ast.UAdd)) and self.category(operand) == 'number':
                return operand
            self.fail('unsupported unary operator or operand')
        if isinstance(value, ast.BinOp) and isinstance(value.op, (ast.Add, ast.Sub, ast.Mult, ast.FloorDiv, ast.Mod)):
            if self.category(self.infer(value.left)) != 'number' or self.category(self.infer(value.right)) != 'number':
                self.fail('arithmetic requires numeric operands')
            return 'Number'
        if isinstance(value, ast.Compare):
            operands = [value.left, *value.comparators]
            for i, operator in enumerate(value.ops):
                if type(operator) not in COMPARE_OPERATORS:
                    self.fail('unsupported comparison operator')
                left, right = self.infer(operands[i]), self.infer(operands[i + 1])
                if isinstance(operator, (ast.In, ast.NotIn)):
                    if self.category(right) != 'list':
                        self.fail('membership requires a value collection')
                    right = right.removesuffix('?')[1:-1]
                if not _compatible(left, right, records):
                    self.fail(f'incompatible comparison types {left} and {right}')
            return 'Bool'
        if isinstance(value, ast.Call):
            if not isinstance(value.func, ast.Name) or value.func.id not in CALL_ARITY:
                self.fail('unsupported expression call')
            call = value.func.id
            if value.keywords or len(value.args) != CALL_ARITY[call]:
                self.fail(f'{call} requires {CALL_ARITY[call]} positional operands')
            if call == 'ref':
                if not isinstance(value.args[0], ast.Constant):
                    self.fail('ref requires a literal node identifier')
                return _ref_type(_reference(self.tree, node, value.args[0].value, self.key))
            if call == 'variant':
                native = self.infer(value.args[0]).removesuffix('?')
                variants = records.get(native, {}).get('variants', {})
                if not isinstance(value.args[1], ast.Constant) or value.args[1].value not in variants:
                    self.fail('unknown variant of the referenced record')
                return variants[value.args[1].value]
            operands = [self.infer(arg) for arg in value.args]
            if call in {'present', 'absent'}:
                if not isinstance(value.args[0], (ast.Name, ast.Attribute, ast.Subscript, ast.Call)):
                    self.fail(f'{call} requires an object or event reference')
                return 'Bool'
            if call == 'implies':
                for operand in operands: self.boolean(operand)
                return 'Bool'
            if call in {'count', 'length'}:
                if self.category(operands[0]) not in {'list', 'map', 'string'}:
                    self.fail(f'{call} requires text or a collection')
                return 'Int'
            if call == 'later':
                if self.category(operands[0]) != 'list' or not isinstance(value.args[1], ast.Name):
                    self.fail('later requires a collection and its bound index')
                index = node.bindings.get(value.args[1].id)
                if index is None or index.domain != ast.unparse(value.args[0]):
                    self.fail('later index belongs to a different collection')
                return operands[0]
            if call == 'set_value':
                target = value.args[0]
                if not isinstance(target, (ast.Name, ast.Attribute, ast.Subscript, ast.Call)):
                    self.fail('set_value requires a named target')
                if self.category(operands[0]) in {'action', 'event', 'component', 'boundary', 'entry', 'recipient', 'report'}:
                    self.fail('set_value requires a field or assessment target')
                if self.category(operands[0]) not in {'assessment', 'value'} and not _compatible(*operands, records):
                    self.fail('set_value operands have incompatible types')
            elif call == 'prevent':
                target = value.args[0]
                named_rule = (isinstance(target, ast.Call) and isinstance(target.func, ast.Name)
                              and target.func.id == 'ref'
                              and self.tree.index[target.args[0].value].kind in RULE_KINDS)
                if self.category(operands[0]) != 'action' and not named_rule:
                    self.fail('prevent requires an action reference')
                if self.category(operands[1]) not in {'record', 'union', 'list', 'map', 'event'}:
                    self.fail('prevent requires an explicit record, event or collection scope')
            elif call == 'retain_records':
                if self.category(operands[0]) not in {'record', 'union', 'list', 'map'}:
                    self.fail('retain_records requires a record or collection')
            elif call in {'retain_assessments', 'withhold'}:
                if not isinstance(value.args[0], (ast.Name, ast.Attribute, ast.Subscript, ast.Call)):
                    self.fail(f'{call} requires a named assessment or field')
                if self.category(operands[0]) in {'action', 'event'}:
                    self.fail(f'{call} requires an assessment, not an action/event')
            elif call == 'emit':
                if self.category(operands[0]) not in {'record', 'union', 'event', 'assessment', 'definition'}:
                    self.fail('emit requires a declared record, event or assessment')
            return '@effect'
        self.fail(f'unsupported expression syntax {type(value).__name__}')


def _public_field(record, info):
    facts = {'type': record_definitions.field_type(info),
             'presence': record_definitions.field_presence(record, info)}
    for key in ('optional', 'json_null', 'projection', 'omission', 'conditional_presence', 'shape_only'):
        if key in info:
            facts[key] = info[key]
    condition = record.get('conditional_null', {}).get(info['name'])
    if condition is not None:
        facts['conditional_null'] = condition
    return facts


class _ReadRoot:
    """The shared citation checker reads the selected tree through this adapter."""
    def __init__(self, read, path=''):
        self.read, self.path = read, path

    def __truediv__(self, path):
        return _ReadRoot(self.read, str(Path(self.path) / path))

    def is_file(self):
        try:
            self.read(self.path)
            return True
        except (OSError, KeyError, ValueError):
            return False

    def read_text(self, **unused):
        return self.read(self.path)


def _string(node, key, value):
    if not isinstance(value, str) or not value.strip():
        node.fail(f'{key} must be a nonempty string', key)


def _strings(node, key, value, empty=False):
    if not isinstance(value, list) or (not value and not empty) or any(not isinstance(x, str) or not x for x in value):
        node.fail(f'{key} must be a list of nonempty strings', key)
    if len(value) != len(set(value)):
        node.fail(f'{key} repeats a value', key)


def _inline_records(tree):
    pending = [n for n in tree.nodes if n.kind == 'subject' and 'record' in n.facts and n.facts['record'] not in tree.records]
    for node in pending:
        name = node.facts['record']
        _string(node, 'record', name)
        if name in tree.records:
            node.fail(f'inline record {name!r} is declared twice')
        fields = {}
        members = [c for c in node.children if c.kind == 'field']
        if not members:
            node.fail(f'unknown record {name!r}; an inline declaration requires typed field nodes', 'record')
        for member in members:
            if 'type' not in member.facts:
                member.fail('inline record fields require a type', 'type')
            key = member.facts.get('name', member.local)
            if key in fields:
                member.fail(f'duplicate inline public field {key!r}')
            native = _native(member.facts['type'])
            optional = member.facts.get('optional', native.endswith('?'))
            if not isinstance(optional, bool) or not isinstance(member.facts.get('json_null', False), bool):
                member.fail('optional and json_null must be booleans')
            if optional and not native.endswith('?'):
                native += '?'
            if not optional and native.endswith('?'):
                member.fail('optional false conflicts with an optional type')
            fields[key] = dict(name=key, swift_type=native, optional=optional,
                               json_null=member.facts.get('json_null', False))
            if 'projection' in member.facts:
                if member.facts['projection'] not in {'hex', 'base64'}:
                    member.fail('unknown byte projection', 'projection')
                fields[key]['projection'] = member.facts['projection']
        tree.records[name] = dict(name=name, fields=fields, input=False,
                                  authored=True, source=node.source,
                                  open=node.facts.get('open', False))
    for node in pending:
        for info in tree.records[node.facts['record']]['fields'].values():
            if not _known_type(info['swift_type'], tree.records):
                node.fail(f'inline field {info["name"]} names unknown type {info["swift_type"]}')


def _owner(tree, node):
    facts = node.facts
    if facts.get('scope', 'self') not in {'self', 'subtree'}:
        node.fail('owner scope must be self or subtree', 'scope')
    grade = facts.get('grade')
    if grade not in {'source_read', 'check_read', 'executed'}:
        node.fail('owner grade must be source_read, check_read or executed', 'grade')
    for key in ('pins', 'context', 'limits'):
        _string(node, key, facts.get(key))
    for key, required in (('source', True), ('check', grade != 'source_read')):
        value = facts.get(key)
        if value is None and not required:
            continue
        items = value if isinstance(value, list) else [value]
        if not items or any(not isinstance(x, dict) for x in items):
            node.fail(f'owner {key} requires a citation or citation list', key)
        for citation in items:
            try:
                generator_common.citation(citation, _ReadRoot(tree.read), check=key == 'check')
            except (KeyError, OSError, ValueError) as error:
                node.fail(str(error), key)
    if grade == 'executed':
        _string(node, 'run', facts.get('run'))
        if not facts.get('source_snapshot') and not facts.get('build'):
            node.fail('execution credit requires source_snapshot or build')
        for key in ('source_snapshot', 'build'):
            if key in facts:
                _string(node, key, facts[key])
    if 'release' in facts:
        if grade != 'executed':
            node.fail('release credit requires executed grade', 'release')
        _string(node, 'release', facts['release'])
        _string(node, 'case', facts.get('case'))
        if not re.fullmatch(r'[a-z0-9_]+/[a-z0-9_]+', facts['case']):
            node.fail('release case must name suite/case', 'case')


def _supported(node):
    if any(c.kind == 'owner' or (c.kind == 'gap' and c.facts.get('kind') == 'evidence') for c in node.children):
        return True
    parent = node.parent
    while parent:
        if any(c.kind == 'owner' and c.facts.get('scope') == 'subtree' for c in parent.children):
            return True
        if any(c.kind == 'gap' and c.facts.get('kind') == 'evidence' and c.facts.get('scope') == 'subtree' for c in parent.children):
            return True
        parent = parent.parent
    return False


def _record_children(record, records):
    targets = set()
    types = [*record.get('variants', {}).values(),
             *(info['swift_type'] for info in record['fields'].values())]
    for declared in types:
        native = declared.removesuffix('?')
        while native.startswith('[') and native.endswith(']'):
            native = native[9:-1] if native.startswith('[String: ') else native[1:-1]
            native = native.removesuffix('?')
        if native in records:
            targets.add(native)
    return targets


def _validate(tree):
    _inline_records(tree)
    catalog = json.loads(tree.read('tests/catalog.json'))['suites']
    counts, field_subjects = Counter(), defaultdict(list)
    for node in tree.nodes:
        node.context = dict(node.parent.context) if node.parent else {}
        node.aliases = dict(node.parent.aliases) if node.parent else dict(tree.aliases)
        node.bindings = dict(node.parent.bindings) if node.parent else {}
        facts = node.facts
        for key, value in facts.items():
            if key.startswith('free.'):
                kind = key[5:]
                if kind not in FREE_KINDS:
                    node.fail('unknown free-text relationship kind', key)
                counts[kind] += 1
                if key == 'free.when':
                    prior = node.context.get('free_when', [])
                    node.context['free_when'] = [*prior, value]
            if key in CONTEXT:
                if key in SET_CONTEXT:
                    _strings(node, key, value)
                    if key in node.context and not set(value) <= set(node.context[key]):
                        node.fail(f'{key} widens inherited applicability', key)
                elif key == 'who' and isinstance(value, list):
                    _strings(node, key, value)
                    for ident in value:
                        target = _reference(tree, node, ident, key, {'definition'})
                        if target.facts.get('defines') != 'component':
                            node.fail('who reference requires a component definition', key)
                else:
                    _string(node, key, value)
                # Acting components replace the inherited actor, as a literal
                # who does; entry/recipient/report retain their narrowing rule.
                if key == 'when' and key in node.context:
                    value = f'({node.context[key]}) and ({value})'
                node.context[key] = value
        if 'part' in facts and facts['part'] not in PARTS:
            node.fail('unknown document part', 'part')
        if node.kind == 'surface':
            if facts.get('coverage', 'selected') not in {'selected', 'public'}:
                node.fail('surface coverage must be selected or public', 'coverage')
            if type(facts.get('syntax')) is not int or facts['syntax'] != SYNTAX:
                node.fail('unsupported source syntax', 'syntax')
            for key in ('artifact', 'part'):
                _string(node, key, facts.get(key))
            for key in ('goldens', 'checks'):
                _strings(node, key, facts.get(key), empty=not tree.strict)
            for golden in facts['goldens']:
                try:
                    json.loads(tree.read(_relative(golden)))
                except (OSError, KeyError, ValueError) as error:
                    node.fail(f'invalid canonical shape input {golden}: {error}', 'goldens')
            if any(check not in catalog for check in facts['checks']):
                node.fail('unknown verification suite', 'checks')
            if tree.strict and not any(c.kind in {'subject', 'definition'} for c in node.children):
                node.fail('surface has no public subjects or definitions')
        if 'record' in facts:
            node.record = facts['record']
            if node.record not in tree.records:
                node.fail('unknown imported record', 'record')
            alias = facts.get('as')
            if not isinstance(alias, str) or not IDENTIFIER.fullmatch(alias):
                node.fail('record subject requires a simple alias', 'as')
            if alias in node.aliases and node.aliases[alias] != node.record:
                node.fail('record alias shadows a different inherited type', 'as')
            node.aliases[alias] = node.record
            field_subjects[node.record].append(node)
            if 'at' in facts:
                _strings(node, 'at', facts['at'])
        for key, value in facts.items():
            if key.startswith('bind.'):
                name = key[5:]
                if not IDENTIFIER.fullmatch(name) or name in node.aliases:
                    node.fail('invalid or colliding binding identifier', key)
                expressions = Expressions(tree, node, key)
                parsed = expressions.parse(value)
                native = expressions.infer(parsed.body).removesuffix('?')
                category = _category(native, tree.records)
                if category not in {'list', 'map'}:
                    node.fail('binding domain must be a collection', key)
                binding = Binding(ast.unparse(parsed.body), native[9:-1] if category == 'map' else native[1:-1],
                                  'String' if category == 'map' else 'Int')
                if name in node.bindings and node.bindings[name] != binding:
                    node.fail('binding shadows a different inherited domain', key)
                node.bindings[name] = binding
                node.expressions[key] = parsed
        if node.kind == 'field':
            parent = node.parent
            if not parent or not parent.record:
                node.fail('field belongs directly beneath a record subject')
            key = facts.get('name', node.local)
            info = tree.records[parent.record]['fields'].get(key)
            if info is None:
                node.fail(f'unknown public field {key!r}')
            node.field_info = info
            if not tree.records[parent.record].get('authored') and set(facts) & {'type', 'optional', 'json_null', 'projection'}:
                node.fail('imported type and presence are owned by the record definition')
            if tree.strict and not node.prose:
                node.fail('public field has no authored meaning')
            if any(k in facts for k in ('vocabulary', 'listed', 'values', 'unknown')):
                if facts.get('vocabulary') not in {'open', 'closed'} or facts.get('listed') not in {'exhaustive', 'illustrative'}:
                    node.fail('value set requires admitted openness and list completeness')
                if not isinstance(facts.get('values'), list) or not facts['values']:
                    node.fail('value set must contain displayed values', 'values')
                encoded = [json.dumps(x, sort_keys=True) for x in facts['values']]
                if len(set(encoded)) != len(encoded):
                    node.fail('value set repeats a value', 'values')
                if facts['vocabulary'] == 'open':
                    _string(node, 'unknown', facts.get('unknown'))
        if node.kind == 'definition':
            if facts.get('defines', 'value') not in DEFINITION_KINDS:
                node.fail('unknown definition kind', 'defines')
            if 'type' in facts and not _known_type(_native(facts['type']), tree.records):
                node.fail('unknown definition type', 'type')
        if node.kind == 'effect' and facts.get('on') not in {'failure', 'success', 'always'}:
            node.fail('effect requires an explicit on trigger', 'on')
        if 'failure' in facts and facts['failure'] not in {'first', 'accumulate'}:
            node.fail('failure mode must be first or accumulate', 'failure')
        if node.kind == 'gap':
            if facts.get('kind') not in {'behavior', 'evidence', 'meaning'}:
                node.fail('gap kind must be behavior, evidence or meaning', 'kind')
            if facts.get('scope', 'self') not in {'self', 'subtree'}:
                node.fail('gap scope must be self or subtree', 'scope')
            if not node.prose:
                node.fail('known gap requires a public statement')
        if node.kind == 'owner':
            _owner(tree, node)
        for path in facts.get('at', []):
            if not isinstance(path, str):
                node.fail('record placements must be object paths', 'at')
            expressions = Expressions(tree, node, 'at')
            parsed = expressions.parse(path)
            if not isinstance(parsed.body, (ast.Name, ast.Attribute, ast.Subscript, ast.Call)):
                node.fail('record placement must be a named object path', 'at')
            if expressions.infer(parsed.body).removesuffix('?') != node.record:
                node.fail('record placement has a different declared type', 'at')
    # Field refs can name a later surface, so resolve expressions after all joins.
    for node in tree.nodes:
        for key, value in node.facts.items():
            if key in EXPRESSION_KEYS or key.startswith('match.'):
                if key.startswith('match.') and key[6:] not in node.bindings:
                    node.fail('join names an unbound index', key)
                expected = 'effects' if key == 'effects' else ('boolean' if key in {'when', 'test', 'required_when', 'present_when'} or key.startswith('match.') else None)
                node.expressions[key] = Expressions(tree, node, key).parse(value, expected)
                if key.startswith('match.') and not any(isinstance(item, ast.Name) and item.id == key[6:]
                                                        for item in ast.walk(node.expressions[key])):
                    node.fail('join does not reference its bound index', key)
            if key in {'uses', 'after', 'precedes', 'requires'}:
                _strings(node, key, value)
                for ident in value:
                    target = _reference(tree, node, ident, key)
                    if key in {'after', 'precedes'} and target.kind not in ORDER_KINDS and not (target.kind == 'definition' and target.facts.get('defines') in {'event', 'action'}):
                        node.fail('order reference requires an action, check, condition, outcome or effect', key)
                    if key == 'requires' and _ref_type(target) != 'Bool':
                        node.fail('requirement reference must name a condition or check', key)
        if tree.strict:
            if node.kind in RULE_KINDS:
                missing = CONTEXT - {'when'} - node.context.keys()
                if missing:
                    node.fail('rule lacks particulars: ' + ', '.join(sorted(missing)))
                has_applicability = 'when' in node.context or any(k in node.context for k in SET_CONTEXT)
                has_obligation = ('effects' in node.facts or 'test' in node.facts or 'requires' in node.facts
                                  or any(k in node.facts for k in ('free.condition', 'free.dependency', 'free.effect'))
                                  or any(c.kind in {'condition', 'effect', 'outcome'} for c in node.children))
                if not has_applicability or not has_obligation:
                    node.fail('rule needs explicit applicability and an obligation')
            if node.kind in RULE_KINDS | {'example'} and not _supported(node):
                node.fail('rule/example has no graded support or explicit evidence gap')
            if node.kind == 'condition' and 'test' not in node.facts and 'free.condition' not in node.facts and not any(c.kind == 'condition' for c in node.children):
                node.fail('condition has no expression or explicit free-text condition')
            if node.kind == 'effect' and not ({'effects', 'free.effect'} & node.facts.keys()):
                node.fail('effect has no structured or explicit free-text consequence')
    # A public inventory covers every imported root, including an entire family
    # that an edit accidentally drops. Small constructed models select their own
    # subjects and still cover every referenced child record.
    required = set(field_subjects)
    if any(n.facts.get('coverage') == 'public' for n in tree.surfaces):
        required.update(name for name, record in tree.records.items() if record.get('coverage_required'))
    pending = list(required)
    while pending:
        name = pending.pop()
        for child in _record_children(tree.records[name], tree.records) - required:
            required.add(child)
            pending.append(child)
    tree.uncovered_records = sorted(required - field_subjects.keys())
    if tree.strict and tree.uncovered_records:
        raise ContractError('uncovered referenced records: ' + ', '.join(tree.uncovered_records))
    for record, subjects in field_subjects.items():
        if len(subjects) != 1:
            subjects[-1].fail('record meanings already belong to ' + subjects[0].id)
        expected = set(tree.records[record]['fields'])
        for subject in subjects:
            fields = [c.facts.get('name', c.local) for c in subject.children if c.kind == 'field']
            if len(fields) != len(set(fields)):
                subject.fail('duplicate public field meaning')
            if tree.strict and set(fields) != expected:
                subject.fail('record field coverage differs: missing ' + ', '.join(sorted(expected - set(fields))))
    # Imported object types carry their authored meaning wherever a field
    # exposes that object. The shared closure records this join for stamping.
    for node in tree.nodes:
        if node.kind != 'field':
            continue
        record = {'fields': {node.local: node.field_info}}
        for target in _record_children(record, tree.records):
            if target in field_subjects:
                node.references.add(field_subjects[target][0].id)
    graph = defaultdict(set)
    for node in tree.nodes:
        for before in node.facts.get('after', []): graph[before].add(node.id)
        for after in node.facts.get('precedes', []): graph[node.id].add(after)
    done = set()
    def visit(ident, active):
        if ident in active:
            tree.index[ident].fail('check-order cycle')
        if ident in done:
            return
        for child in graph.get(ident, set()): visit(child, active | {ident})
        done.add(ident)
    for ident in list(graph): visit(ident, set())
    tree.free_counts = {kind: counts[kind] for kind in sorted(FREE_KINDS)}


def load_tree(root, read=None, paths=None, strict=True):
    root = Path(root)
    selected_read = read or (lambda path: (root / path).read_text())
    if paths is None:
        paths = sorted(p.relative_to(root).as_posix() for p in (root / 'docs/contract').glob('*.surface.md'))
    paths = [_relative(str(path)) for path in paths]
    if not paths or len(set(paths)) != len(paths):
        raise ContractError('expected distinct surface source paths')
    nodes = []
    for path in paths:
        nodes.extend(parse_surface(selected_read(path), path))
    index = {}
    for node in nodes:
        if node.id in index:
            node.fail(f'duplicate node identifier; first at {index[node.id].source}:{index[node.id].line}')
        index[node.id] = node
    # A read overlay uses root's inventory unless it carries an explicit
    # inventory for another selected source tree. Released snapshots bypass
    # the current authoring reader altogether.
    swift_paths = getattr(read, 'swift_paths', None)
    if swift_paths is None:
        swift_paths = [path.relative_to(root).as_posix()
                       for path in sorted((root / 'runner/Sources/PWRunnerCore').glob('*.swift'))]
    records, aliases = record_definitions.load(root, read=selected_read, swift_paths=swift_paths)
    tree = Tree(root, nodes, index, records, aliases, [n for n in nodes if n.kind == 'surface'],
                {}, paths, selected_read, strict)
    _validate(tree)
    return tree


def _anchor(node):
    return 'contract-' + node.id.replace('.', '-')


def _link(node):
    return '[' + node.title + '](#' + _anchor(node) + ')'


def _cell(text):
    return ' '.join(str(text).split()).replace('|', '\\|')


def _literal(value):
    return '`' + json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '`'


def _expression_text(tree, expression):
    value = expression.body if isinstance(expression, ast.Expression) else expression
    if isinstance(value, ast.Constant):
        return _literal(value.value)
    if isinstance(value, (ast.Name, ast.Attribute, ast.Subscript)):
        return '`' + ast.unparse(value) + '`'
    if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
        return ', '.join(_expression_text(tree, x) for x in value.elts) or 'an empty set'
    if isinstance(value, ast.BoolOp):
        conjunction = ' and ' if isinstance(value.op, ast.And) else ' or '
        return '(' + conjunction.join(_expression_text(tree, x) for x in value.values) + ')'
    if isinstance(value, ast.UnaryOp):
        if isinstance(value.op, ast.Not):
            return 'not (' + _expression_text(tree, value.operand) + ')'
        return '`' + ast.unparse(value) + '`'
    if isinstance(value, ast.BinOp):
        return '`' + ast.unparse(value) + '`'
    if isinstance(value, ast.Compare):
        operators = {ast.Eq: '=', ast.NotEq: '≠', ast.Lt: '<', ast.LtE: '≤',
                     ast.Gt: '>', ast.GtE: '≥', ast.In: 'is one of', ast.NotIn: 'is outside'}
        operands = [value.left, *value.comparators]
        parts = [_expression_text(tree, operands[0])]
        for operator, operand in zip(value.ops, operands[1:]):
            parts += [operators[type(operator)], _expression_text(tree, operand)]
        return ' '.join(parts)
    if isinstance(value, ast.Call):
        call = value.func.id
        if call == 'ref':
            return _link(tree.index[value.args[0].value])
        args = [_expression_text(tree, x) for x in value.args]
        if call == 'present': return args[0] + ' is present'
        if call == 'absent': return args[0] + ' is absent'
        if call == 'implies': return 'if ' + args[0] + ', then ' + args[1]
        if call == 'later': return 'members after ' + args[1] + ' in ' + args[0]
        if call == 'set_value': return 'sets ' + args[0] + ' to ' + args[1]
        if call == 'prevent': return 'prevents ' + args[0] + ' for ' + args[1]
        if call == 'retain_records': return 'retains the records ' + args[0]
        if call == 'retain_assessments': return 'keeps the assessment ' + args[0]
        if call == 'withhold': return 'withholds ' + args[0]
        if call == 'emit': return 'reports ' + args[0] + ' as ' + args[1]
        if call in {'count', 'length'}: return call + ' of ' + args[0]
        if call == 'variant': return args[1] + ' alternative of ' + args[0]
    raise ContractError('cannot render an unchecked expression')


def _actor_text(tree, who):
    if isinstance(who, list):
        return ', '.join(_link(tree.index[ident]) for ident in who)
    return who.replace('_', ' ')


def _controller_check(node):
    who = node.context.get('who')
    if isinstance(who, list):
        return 'identity.definitions.controller' in who
    # Existing literal fixtures retain their exact-match indexing behavior.
    return who == 'controller'


def _context_text(tree, node):
    labels = lambda values: ', '.join(str(x).replace('_', ' ') for x in values)
    context = node.context
    parts = []
    if 'who' in context and 'where' in context:
        parts.append(_actor_text(tree, context['who']) + ' ' + node.kind + ' at ' + context['where'].replace('_', ' ') + '.')
    for key, title in (('entry', 'Entry'), ('recipient', 'Recipient'), ('report', 'Reports')):
        if key in context:
            parts.append(title + ': ' + labels(context[key]) + '.')
    return ' '.join(parts)


def _facts_text(tree, node, include_context=False):
    parts = []
    if include_context and node.kind in RULE_KINDS:
        context = _context_text(tree, node)
        if context: parts.append(context)
    for key, expression in node.expressions.items():
        if key.startswith('bind.'):
            parts.append('Binding `' + key[5:] + '`: entry in ' + _expression_text(tree, expression) + '.')
        elif key.startswith('match.'):
            parts.append('Association restriction for `' + key[6:] + '`: ' + _expression_text(tree, expression) + '.')
    if 'at' in node.facts:
        parts.append('Record `' + node.facts['as'] + '` locations: ' +
                     ', '.join('`' + path + '`' for path in node.facts['at']) + '.')
    if 'when' in node.context and include_context and node.kind in RULE_KINDS:
        parts.append('Applies when ' + _expression_text(tree, ast.parse(node.context['when'], mode='eval')) + '.')
    elif 'when' in node.expressions:
        parts.append('Applies when ' + _expression_text(tree, node.expressions['when']) + '.')
    if include_context and node.kind in RULE_KINDS:
        parts.extend(node.context.get('free_when', []))
    for key, label in (('test', 'Requires'), ('required_when', 'Required when'),
                       ('present_when', 'Present when'), ('object', 'Concerns')):
        if key in node.expressions:
            parts.append(label + ' ' + _expression_text(tree, node.expressions[key]) + '.')
    if 'effects' in node.expressions:
        trigger = node.facts.get('on')
        label = {'failure': 'On failure, ', 'success': 'On success, ', 'always': ''}.get(trigger, '')
        parts.append(label + _expression_text(tree, node.expressions['effects']) + '.')
    for key, label in (('after', 'Follows'), ('precedes', 'Precedes'), ('requires', 'Requires'), ('uses', 'Uses')):
        if key in node.facts:
            parts.append(label + ' ' + ', '.join(_link(tree.index[x]) for x in node.facts[key]) + '.')
    if 'failure' in node.facts:
        parts.append('The first failed condition selects the consequence.' if node.facts['failure'] == 'first'
                     else 'The check retains each failed condition it finds.')
    if 'value' in node.facts:
        parts.append('Value: ' + _literal(node.facts['value']) + '.')
    for key, value in node.facts.items():
        if key.startswith('free.'):
            if key == 'free.when' and include_context and node.kind in RULE_KINDS:
                continue
            if key == 'free.effect' and node.kind == 'effect' and 'effects' not in node.expressions:
                value = {'failure': 'On failure, ', 'success': 'On success, ', 'always': ''}[node.facts['on']] + value
            parts.append(value)
    return ' '.join(parts)


def _finding_consequence(tree, node):
    if node.kind == 'effect':
        # Effect prose belongs to this consequence, along with its trigger,
        # applicability and bindings. A check's general prose does not.
        return ' '.join(part for part in (_facts_text(tree, node), node.prose) if part)
    parts = []
    if 'effects' in node.expressions:
        parts.append(_expression_text(tree, node.expressions['effects']) + '.')
    if 'free.effect' in node.facts:
        parts.append(node.facts['free.effect'])
    return ' '.join(parts)


def _citation_links(value, label):
    items = value if isinstance(value, list) else [value]
    return ', '.join('[' + label + (f' {i + 1}' if len(items) > 1 else '') +
                     '](../' + item['path'] + ')' for i, item in enumerate(items) if isinstance(item, dict))


def _owner_text(node):
    facts = node.facts
    scope = ' for this subject and its descendants' if facts.get('scope') == 'subtree' else ''
    pieces = ['**Support' + scope + ' — ' + facts['grade'].replace('_', ' ') + '.**',
              facts['pins'], 'Context: ' + facts['context'], 'Evidence limit: ' + facts['limits']]
    pieces.append(_citation_links(facts['source'], 'Source'))
    if 'check' in facts:
        pieces.append(_citation_links(facts['check'], 'Check'))
    if facts['grade'] == 'executed':
        pieces.append('Run: `' + facts['run'] + '`.')
        for key in ('source_snapshot', 'build', 'release', 'case'):
            if key in facts: pieces.append(key.replace('_', ' ').capitalize() + ': `' + facts[key] + '`.')
    return ' '.join(pieces)


def _field_meaning(tree, node):
    parts = [node.prose, _facts_text(tree, node)]
    facts = node.facts
    if 'default' in facts:
        parts.append('Default: ' + _literal(facts['default']) + '.')
    if 'vocabulary' in facts:
        parts.append('Admitted vocabulary: ' + facts['vocabulary'] + '; displayed list: ' + facts['listed'] + ': ' +
                     ', '.join(_literal(v) for v in facts['values']) + '.')
        if 'unknown' in facts:
            parts.append('Unfamiliar values: ' + facts['unknown'] + '.')
    return ' '.join(p for p in parts if p)


def _field_type_text(tree, info):
    if info.get('projection'):
        return record_definitions.field_type(info)
    native = info['swift_type'].removesuffix('?')
    if native.startswith('[String: '):
        return 'object with string keys and ' + _field_type_text(tree, {'swift_type': native[9:-1]}) + ' values'
    if native.startswith('['):
        return 'array of ' + _field_type_text(tree, {'swift_type': native[1:-1]})
    subjects = [node for node in tree.nodes if node.kind == 'subject' and node.record == native]
    if subjects:
        return _link(subjects[0])
    return record_definitions.field_type(info)


PART_TITLES = {
    'identity': None, 'definitions': 'Definitions',
    'input': 'Running a specimen: accepted input', 'delivery': 'Delivery to the host',
    'report': "The host's report", 'assessment': "The controller's assessment and output",
    'installation': 'Managing runners', 'version': 'Reporting the version',
}


def _views(tree):
    applicability, findings, gaps = [], [], []
    for node in tree.nodes:
        if node.kind in RULE_KINDS:
            applicability.append((node, node.context))
        if node.kind == 'checks':
            expressions = [node, *node.descendants()]
            reads = set()
            for member in expressions:
                for key, expression in member.expressions.items():
                    if key not in {'when', 'test', 'required_when', 'present_when'} and not key.startswith(('bind.', 'match.')):
                        continue
                    for item in ast.walk(expression):
                        if isinstance(item, (ast.Attribute, ast.Subscript)):
                            reads.add(ast.unparse(item))
            # Keep the most specific path when a longer one includes the same parent.
            reads = {path for path in reads if not any(other.startswith(path + '.') or other.startswith(path + '[')
                                                       for other in reads if other != path)}
            consequences = ([node] if 'effects' in node.expressions or 'free.effect' in node.facts else [])
            consequences.extend(c for c in node.descendants() if c.kind == 'effect')
            findings.append((node, sorted(reads), consequences))
        if node.kind == 'gap':
            gaps.append(node)
    return applicability, findings, gaps


def render(tree):
    """Render the contract with a marker for the entry point's surface table."""
    output = ['# PolicyWitness contract', '']
    roots = defaultdict(list)
    for surface in tree.surfaces:
        roots[surface.facts['part']].append(surface)
        for node in surface.descendants():
            if 'part' in node.facts:
                roots[node.facts['part']].append(node)

    def heading(node, depth):
        output.extend(['<a id="' + _anchor(node) + '"></a>',
                       '#' * min(depth, 6) + ' ' + ('Known gap: ' if node.kind == 'gap' else '') + node.title, ''])

    def table(parent, children):
        if not children: return
        output.extend(['| Item | Requirement or consequence |', '| --- | --- |'])
        for child in children:
            text = ' '.join(p for p in (_facts_text(tree, child), child.prose) if p)
            output.append('| <a id="' + _anchor(child) + '"></a>' + _cell(child.title) + ' | ' + _cell(text) + ' |')
        output.append('')
        for child in children:
            nested = [c for c in child.children if c.kind in {'condition', 'effect', 'outcome'}]
            table(child, nested)
            for extra in child.children:
                if extra not in nested: visit(extra, min(parent.level + 3, 6))

    def visit(node, depth):
        if node.kind == 'owner':
            output.extend([_owner_text(node), ''])
            return
        heading(node, depth)
        facts = _facts_text(tree, node, include_context=True)
        if facts: output.extend([facts, ''])
        if node.prose: output.extend([node.prose, ''])
        fields = [c for c in node.children if c.kind == 'field']
        if fields:
            output.extend(['| Field | JSON type and presence | Meaning |', '| --- | --- | --- |'])
            for member in fields:
                info = _public_field(tree.records[node.record], member.field_info)
                name = member.facts.get('name', member.local)
                output.append('| <a id="' + _anchor(member) + '"></a>`' + name + '` | ' +
                              _cell(_field_type_text(tree, member.field_info) + '; ' + info['presence']) + ' | ' + _cell(_field_meaning(tree, member)) + ' |')
            output.append('')
        if node.record and tree.records[node.record].get('variants'):
            output.extend(['| Alternative | Record |', '| --- | --- |'])
            for label, target in tree.records[node.record]['variants'].items():
                candidates = [n for n in tree.nodes if n.record == target]
                rendered = _link(candidates[0]) if candidates else '`' + target + '`'
                output.append('| `' + label + '` | ' + rendered + ' |')
            output.append('')
        compact = [c for c in node.children if c.kind in {'condition', 'effect', 'outcome'}]
        table(node, compact)
        for member in fields:
            nested = [c for c in member.children if c.kind in {'condition', 'effect', 'outcome'}]
            if nested:
                output.extend(['**' + member.title + '.**', ''])
                table(member, nested)
            for extra in member.children:
                if extra not in nested: visit(extra, depth + 1)
        for child in node.children:
            if child.kind == 'field' or child in compact or 'part' in child.facts:
                continue
            visit(child, depth + 1)

    for part in PARTS:
        if not roots[part]: continue
        title = PART_TITLES[part]
        same_title = (title and len(roots[part]) == 1
                      and roots[part][0].title.casefold() == title.casefold())
        if title and not same_title: output.extend(['## ' + title, ''])
        for node in roots[part]: visit(node, 3 if title and not same_title else 2)
        if part == 'identity':
            output.extend(['<!-- CONTRACT SURFACE TABLE -->', ''])
    if not roots['identity']:
        output[2:2] = ['<!-- CONTRACT SURFACE TABLE -->', '']
    applicability, findings, gaps = _views(tree)
    if applicability:
        output.extend(['## Rule applicability', '', '| Rule | Component and boundary | Entry and recipient | Reports and conditions |', '| --- | --- | --- | --- |'])
        for node, context in applicability:
            scope = ', '.join(context.get('report', []))
            if 'when' in context: scope += '; ' + _expression_text(tree, ast.parse(context['when'], mode='eval'))
            if context.get('free_when'): scope += '; ' + ' '.join(context['free_when'])
            output.append('| ' + _link(node) + ' | ' + _cell(_actor_text(tree, context.get('who', '')) + '; ' + context.get('where', '')) +
                          ' | ' + _cell(', '.join(context.get('entry', [])) + '; ' + ', '.join(context.get('recipient', []))) + ' | ' + _cell(scope) + ' |')
        output.append('')
    if findings:
        output.extend(['## Controller findings', '', '| Check | Structured operands | Consequences and retained assessments |', '| --- | --- | --- |'])
        for node, reads, effects in findings:
            if not _controller_check(node): continue
            output.append('| ' + _link(node) + ' | ' + _cell(', '.join('`' + path + '`' for path in reads) if reads else 'See the linked rule.') +
                          ' | ' + _cell(' '.join(_finding_consequence(tree, effect) for effect in effects)) + ' |')
        output.append('')
    if gaps:
        output.extend(['## Known gaps', '', '| Item | Kind |', '| --- | --- |'])
        for node in gaps: output.append('| ' + _link(node) + ' | ' + node.facts['kind'] + ' |')
        output.append('')
    return '\n'.join(output).rstrip() + '\n'


def _ast_public(value):
    if isinstance(value, ast.AST):
        return {'node': type(value).__name__,
                **{key: _ast_public(member) for key, member in ast.iter_fields(value) if key != 'ctx'}}
    if isinstance(value, list):
        return [_ast_public(member) for member in value]
    return value


def _node_public(tree, node):
    facts = {key: (_ast_public(node.expressions[key]) if key in node.expressions else value)
             for key, value in node.facts.items() if key not in PUBLIC_EXCLUSIONS}
    context = dict(node.context)
    if 'when' in context:
        context['when'] = _ast_public(ast.parse(context['when'], mode='eval'))
    result = dict(id=node.id, kind=node.kind, title=node.title, facts=facts,
                  context=context, prose=node.prose)
    if node.field_info:
        result['field'] = _public_field(tree.records[node.parent.record], node.field_info)
    if node.record:
        record = tree.records[node.record]
        if record.get('variants'):
            result['variants'] = record['variants']
        if record.get('open'):
            result['additional_fields'] = record.get('additional_type', 'JSON')
    if node.object_types:
        result['referenced_types'] = node.object_types
    return result


def public_payload(tree, surface_id):
    """Canonical public facts and the public nodes explicitly referenced by them."""
    surface = tree.index.get(surface_id)
    if surface is None or surface.kind != 'surface':
        raise ContractError(f'unknown contract surface {surface_id!r}')
    local = {n.id for n in [surface, *surface.descendants()] if n.kind != 'owner'}
    selected, pending = set(local), list(local)
    while pending:
        node = tree.index[pending.pop()]
        for ident in node.references:
            target = tree.index[ident]
            candidates = [target, *target.descendants()]
            # The ancestor supplies effective definitions and context, without
            # importing unrelated sibling subjects into the dependent surface.
            parent = target.parent
            while parent:
                candidates.append(parent)
                parent = parent.parent
            for candidate in candidates:
                if candidate.kind != 'owner' and candidate.id not in selected:
                    selected.add(candidate.id)
                    pending.append(candidate.id)
    return {'format': 'policywitness-contract-public-1', 'surface': surface_id,
            'nodes': [_node_public(tree, tree.index[ident]) for ident in sorted(local)],
            'shared': [_node_public(tree, tree.index[ident]) for ident in sorted(selected - local)]}


def statistics(tree, body):
    """Counts separate rendered tables from authored prose and free-text facts."""
    lines = body.splitlines()
    table_lines = [line for line in lines if line.startswith('|')]
    authored = '\n'.join(n.prose for n in tree.nodes if n.kind not in {'field', 'owner'})
    fields = '\n'.join(n.prose for n in tree.nodes if n.kind == 'field')
    free_text = '\n'.join(value for n in tree.nodes for key, value in n.facts.items() if key.startswith('free.'))
    return {'lines': len(lines), 'words': len(body.split()),
            'table_lines': len(table_lines), 'table_words': len('\n'.join(table_lines).split()),
            'authored_body_lines': len([line for line in authored.splitlines() if line.strip()]),
            'authored_body_words': len(authored.split()), 'field_meaning_words': len(fields.split()),
            'free_text_words': len(free_text.split()), 'free_counts': tree.free_counts,
            'nodes': len(tree.nodes), 'fields': sum(n.kind == 'field' for n in tree.nodes),
            'surfaces': len(tree.surfaces), 'uncovered_records': tree.uncovered_records}
