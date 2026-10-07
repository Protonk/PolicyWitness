"""Shared, mechanical citation checks for the documentation generators (G4–G6).

A definition is a place to look, never evidence that a test asserts a claim.
"""
import ast
import json
import re
from pathlib import Path


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
