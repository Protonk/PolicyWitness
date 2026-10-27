"""Shared, mechanical citation checks for the documentation generators (G4–G6).

A definition is a place to look, never evidence that a test asserts a claim.
"""
import ast
from functools import lru_cache
import json
import re
from pathlib import Path
import sys

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import markdown_reader  # noqa: E402


@lru_cache(maxsize=128)
def python_definitions(text):
    return {node.name for node in ast.walk(ast.parse(text))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


RULE_ID = re.compile(r'[a-z][a-z0-9_]*')


@lru_cache(maxsize=128)
def rule_declarations(text):
    """The (rule ID, function name) rows of a module's RULES table, read statically.

    The table is one module-level `RULES = (...)` of `Rule("<id>", <function>, ...)` rows: a lowercase identifier
    ID and a bare name of a function the module defines, and `main()` must use `RULES`. A module without a table
    declares no rules. A malformed row, a duplicate ID, an undefined function, a second table or an unused table
    is refused. Nothing here imports or runs the module."""
    tree = ast.parse(text)
    tables = [node for node in tree.body if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == 'RULES' for target in node.targets)]
    if not tables:
        return ()
    if len(tables) > 1:
        raise ValueError('expected one module-level RULES table')
    value = tables[0].value
    if not isinstance(value, (ast.Tuple, ast.List)):
        raise ValueError('RULES must be a tuple or list of Rule(...) rows')
    defined = python_definitions(text)
    rows = []
    for element in value.elts:
        well_formed = (isinstance(element, ast.Call) and isinstance(element.func, ast.Name) and element.func.id == 'Rule'
                       and len(element.args) >= 2 and isinstance(element.args[0], ast.Constant)
                       and isinstance(element.args[0].value, str) and RULE_ID.fullmatch(element.args[0].value)
                       and isinstance(element.args[1], ast.Name))
        if not well_formed:
            raise ValueError('each RULES row is Rule("<id>", <function>, ...) with a lowercase identifier ID')
        rule_id, function = element.args[0].value, element.args[1].id
        if any(rule_id == existing for existing, _ in rows):
            raise ValueError(f'duplicate rule ID {rule_id!r}')
        if function not in defined:
            raise ValueError(f'rule {rule_id!r} names an undefined function {function!r}')
        rows.append((rule_id, function))
    main = next((node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main'), None)
    if main is None or not any(isinstance(node, ast.Name) and node.id == 'RULES' and isinstance(node.ctx, ast.Load)
                               for node in ast.walk(main)):
        raise ValueError('main() does not use the RULES table')
    return tuple(rows)


def catalog_case(root, path, symbol):
    if not path.startswith('tests/suites/'):
        return False
    suite = path.split('/')[2]
    data = json.loads((root / 'tests/catalog.json').read_text())
    return any(case['id'] == symbol for case in data['suites'].get(suite, {}).get('cases', []))


# The allowed files and the definition convention per check form. The README's
# form table is a checked copy of this table.
FORM_RULES = (
    ('test', '`tests/suites/**`, `runner/Tests/**`, or Rust sources with `#[test]`',
     'Python function; Rust function within three lines after `#[test]`; Swift function or run '
     "label ending in a colon; shell `test_selected` or `PW_TEST_ID`; or a case ID in the cited file's "
     'owning suite in `tests/catalog.json`.'),
    ('rule', '`tests/suites/source_drift/*.py`',
     "Python function registered in the module's `RULES` table, which `main()` runs; `build_rules.py` runs its "
     'banner row first and reports the others as blocked when it fails.'),
    ('control', '`tests/fixtures/**`, `tests/lib/**`, `build.sh`, or C sources under `tests/`',
     'Symbol presence; Python functions and C function-line definitions are required in those languages.'),
)


def allowed_file(form, path):
    relative = Path(path)
    if form == 'test':
        return path.startswith(('tests/suites/', 'runner/Tests/')) or relative.suffix == '.rs'
    if form == 'rule':
        return relative.parent.as_posix() == 'tests/suites/source_drift' and relative.suffix == '.py'
    if form == 'control':
        return (path.startswith(('tests/fixtures/', 'tests/lib/')) or path == 'build.sh'
                or (path.startswith('tests/') and relative.suffix == '.c'))
    raise ValueError(f'unknown check form {form!r}')


def form_table():
    rows = ['| Form | Allowed files | Definition convention |', '| --- | --- | --- |']
    return rows + [f'| `{form}` | {files} | {definition} |' for form, files, definition in FORM_RULES]


def citation(ref, root, *, check=False, forbidden=()):
    path, symbol = ref['path'], ref['symbol']
    if not isinstance(path, str) or not isinstance(symbol, str) or not symbol:
        raise ValueError('citation path and symbol must be nonempty strings')
    relative = Path(path)
    if relative.is_absolute() or '..' in relative.parts or not (root / relative).is_file():
        raise ValueError(f'missing/invalid reference {path}')
    if relative.as_posix() in forbidden:
        raise ValueError(f'self-citation: {path}')
    text = (root / relative).read_text(errors='replace')
    if not (markdown_symbol(text, symbol, path) if relative.suffix == '.md' else symbol in text):
        raise ValueError(f'missing symbol {symbol!r} in {path}')
    if not check:
        return
    form = ref.get('form')
    escaped = re.escape(symbol)
    defined = False
    allowed = allowed_file(form, path)
    if form == 'test':
        if allowed:
            if relative.suffix == '.py':
                defined = symbol in python_definitions(text)
            elif relative.suffix == '.rs':
                defined = bool(re.search(r'#\[test\][^\n]*\n(?:[^\n]*\n){0,2}\s*(?:pub\s+)?fn\s+' + escaped + r'\s*\(', text))
            elif relative.suffix == '.swift':
                defined = bool(re.search(r'\bfunc\s+' + escaped + r'\s*\(|"' + escaped + r':', text))
            elif relative.suffix == '.sh':
                defined = bool(re.search(r'\btest_selected\s+["\']?' + escaped + r'(?:["\']|\s|;|$)|\bPW_TEST_ID="' + escaped + '"', text))
            defined = defined or catalog_case(root, path, symbol)
    elif form == 'rule':
        if allowed:
            defined = symbol in {function for _, function in rule_declarations(text)}
    elif form == 'control':
        if allowed:
            if relative.suffix == '.py':
                defined = symbol in python_definitions(text)
            elif relative.suffix == '.c':
                defined = bool(re.search(r'^\s*(?:(?:static|inline|const|unsigned|signed|int|void|bool|size_t|char|long)\s+)*' + escaped + r'\s*\(', text, re.M))
            else:
                defined = True
    if not defined:
        raise ValueError(f'{form} citation is not defined in an allowed file: {path}: {symbol}')


def require_test(owner, checks):
    if not any(ref.get('form') in {'test', 'rule'} for ref in checks):
        raise ValueError(f'{owner}: at least one test or rule is required')


# Durations and sizes in reviewed manifests must come from limits, not literals.
DURATION_SIZE_RE = re.compile(
    r'\b(?:(?<!UTF-)\d[\d,]*(?:\.\d+)?[\s-]+(?:ms|milliseconds?|s|seconds?|bytes?|KiB|MiB)|'
    r'(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|'
    r'thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|'
    r'thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)[\s-]+seconds?)\b', re.I)
LIMIT_RE = re.compile(r'\{limit:([a-z][a-z0-9_]*)\}')


def strings(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, str):
        yield value


def markdown_symbol(text, symbol, name):
    """A Markdown citation names a region marker, a heading or a code span in a heading."""
    document = markdown_reader.parse(text, name)
    if symbol.startswith(('BEGIN ', 'END ')):
        marker = re.compile(rf'<!-- {re.escape(symbol)}(?: \([^)]*\))? -->')
        return any(marker.fullmatch(line.strip()) for block in document.blocks if block.kind == 'html'
                   for line in block.content.splitlines())
    return any(symbol == heading.text or symbol in heading.inline.code for heading in document.headings)


def format_value(value, unit=None):
    if unit is None:
        return f'{value:,}'
    if value == 1 and unit.endswith('s'):
        unit = unit[:-1]
    return f'{value:,} {unit}'


REGION_RE = re.compile(r'<!-- (BEGIN|END) ((?:GENERATED|COPIED) [^\n]*?) -->')
SPAN_RE = re.compile(r'<!-- span ([a-z][a-z0-9_]*\.[a-z0-9_.]+) -->(.*?)<!-- /span -->', re.S)


def region_ranges(text):
    """Generated/copy regions, including nested copies; shared source prose is authored."""
    stack, seen, ranges = [], set(), []
    for match in REGION_RE.finditer(text):
        direction, name = match[1], match[2]
        name = re.sub(r' \(docs/[^)]+\)$', '', name)
        if direction == 'BEGIN':
            if name in seen:
                raise ValueError(f'expected exactly one ordered block: duplicate region {name}')
            seen.add(name)
            stack.append((name, match.start()))
        else:
            if not stack or stack[-1][0] != name:
                raise ValueError(f'expected exactly one ordered block: unordered region {name}')
            _, start = stack.pop()
            ranges.append((start, match.end()))
    if stack:
        raise ValueError(f'expected exactly one ordered block: unclosed region {stack[-1][0]}')
    return ranges


def authored_spans(text, name='<text>'):
    ranges = region_ranges(text)
    def authored(offset):
        return not any(a <= offset < b for a, b in ranges)
    matches = [m for m in SPAN_RE.finditer(text) if authored(m.start())]
    # Reject malformed or nested spans instead of silently ignoring them.
    markers = [m for m in re.finditer(r'<!--\s*(?:span\b|/span\b)', text) if authored(m.start())]
    if len(markers) != 2 * len(matches) or any('<!--' in m[2] for m in matches):
        raise ValueError('malformed authored span')
    # A line that begins with a marker starts an HTML block, which GitHub renders
    # outside its paragraph without Markdown formatting.
    document = markdown_reader.parse(text, name)
    blocks = [(document.offset(b.lines[0]), document.offset(b.lines[1])) for b in document.blocks if b.kind == 'html']
    for marker in markers:
        if any(a <= marker.start() < b for a, b in blocks):
            raise ValueError(f'{name}:{document.line_of(marker.start()) + 1}: span marker in an HTML block, which '
                             'GitHub shows as raw HTML; keep span markers in paragraphs, list items or table cells')
    # A document may state one value in more than one sentence; each span renders.
    return matches


def span_problems(text, prefix, values, name='<text>'):
    problems = []
    for match in authored_spans(text, name):
        if match[1].split('.', 1)[0] != prefix:
            continue
        name = match[1].split('.', 1)[1]
        if name not in values:
            raise ValueError(f'unknown span {match[1]}')
        if match[2] != values[name]:
            problems.append(f'stale span {match[1]}')
    return problems


def render_spans(text, prefix, values, name='<text>'):
    span_problems(text, prefix, values, name)  # validate every authored span before any edit
    for match in reversed(authored_spans(text, name)):
        if match[1].split('.', 1)[0] == prefix:
            text = text[:match.start(2)] + values[match[1].split('.', 1)[1]] + text[match.end(2):]
    return text
