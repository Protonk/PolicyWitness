"""Shared, mechanical citation checks for the documentation generators (G4–G6).

A definition is a place to look, never evidence that a test asserts a claim.
"""
import ast
from functools import lru_cache
import json
import re
from pathlib import Path


@lru_cache(maxsize=128)
def python_definitions(text):
    return {node.name for node in ast.walk(ast.parse(text))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def catalog_case(root, path, symbol):
    if not path.startswith('tests/suites/'):
        return False
    suite = path.split('/')[2]
    data = json.loads((root / 'tests/catalog.json').read_text())
    return any(case['id'] == symbol for case in data['suites'].get(suite, {}).get('cases', []))


def citation(ref, root, *, check=False, forbidden=()):
    path, symbol = ref['path'], ref['symbol']
    if not isinstance(path, str) or not isinstance(symbol, str) or not symbol:
        raise ValueError('citation path and symbol must be nonempty strings')
    relative = Path(path)
    if relative.is_absolute() or '..' in relative.parts or not (root / relative).is_file():
        raise ValueError(f'missing/invalid reference {path}')
    if path in forbidden:
        raise ValueError(f'self-citation: {path}')
    text = (root / relative).read_text(errors='replace')
    if symbol not in text:
        raise ValueError(f'missing symbol {symbol!r} in {path}')
    if not check:
        return
    form = ref.get('form')
    escaped = re.escape(symbol)
    defined = False
    if form == 'test':
        allowed = path.startswith(('tests/suites/', 'runner/Tests/')) or relative.suffix == '.rs'
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
        if relative.parent.as_posix() == 'tests/suites/source_drift' and relative.suffix == '.py':
            tree = ast.parse(text)
            main = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main'), None)
            defined = symbol in python_definitions(text) and main is not None and any(
                isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == symbol
                for n in ast.walk(main))
    elif form == 'control':
        allowed = path.startswith(('tests/fixtures/', 'tests/lib/')) or path == 'build.sh' or (
            path.startswith('tests/') and relative.suffix == '.c')
        if allowed:
            if relative.suffix == '.py':
                defined = symbol in python_definitions(text)
            elif relative.suffix == '.c':
                defined = bool(re.search(r'^\s*(?:(?:static|inline|const|unsigned|signed|int|void|bool|size_t|char|long)\s+)*' + escaped + r'\s*\(', text, re.M))
            else:
                defined = True
    else:
        raise ValueError(f'unknown check form {form!r}')
    if not defined:
        raise ValueError(f'{form} citation is not defined in an allowed file: {path}: {symbol}')


def require_test(owner, checks):
    if not any(ref.get('form') in {'test', 'rule'} for ref in checks):
        raise ValueError(f'{owner}: at least one test or rule is required')


# Durations and sizes in reviewed manifests must come from limits, not literals.
DURATION_SIZE_RE = re.compile(
    r'\b(?:\d[\d,]*(?:\.\d+)?[\s-]+(?:ms|milliseconds?|s|seconds?|bytes?|KiB|MiB)|'
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


def authored_spans(text):
    ranges = region_ranges(text)
    def authored(offset):
        return not any(a <= offset < b for a, b in ranges)
    matches = [m for m in SPAN_RE.finditer(text) if authored(m.start())]
    # Reject malformed or nested spans instead of silently ignoring them.
    markers = [m for m in re.finditer(r'<!--\s*(?:span\b|/span\b)', text) if authored(m.start())]
    if len(markers) != 2 * len(matches) or any('<!--' in m[2] for m in matches):
        raise ValueError('malformed authored span')
    names = [m[1] for m in matches]
    if len(names) != len(set(names)):
        raise ValueError('duplicate authored span')
    return matches


def span_problems(text, prefix, values):
    problems = []
    for match in authored_spans(text):
        if match[1].split('.', 1)[0] != prefix:
            continue
        name = match[1].split('.', 1)[1]
        if name not in values:
            raise ValueError(f'unknown span {match[1]}')
        if match[2] != values[name]:
            problems.append(f'stale span {match[1]}')
    return problems


def render_spans(text, prefix, values):
    span_problems(text, prefix, values)  # validate every authored span before any edit
    for match in reversed(authored_spans(text)):
        if match[1].split('.', 1)[0] == prefix:
            text = text[:match.start(2)] + values[match[1].split('.', 1)[1]] + text[match.end(2):]
    return text


def heading_anchors(prose):
    """ATX heading anchors, with punctuation stripping and duplicate suffixes."""
    anchors = set()
    prose = re.sub(r'<!--.*?-->', '', prose, flags=re.S)
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*\s*$', prose, re.M):
        base = re.sub(r'[^\w -]', '', heading.lower()).replace(' ', '-')
        anchor, suffix = base, 0
        while anchor in anchors:
            suffix += 1
            anchor = f'{base}-{suffix}'
        anchors.add(anchor)
    return anchors
