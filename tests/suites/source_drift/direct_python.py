"""Keep every Python start under the resolver's form: entry points resolve and probe without arguments, every shell
start of the interpreter is ${PW_PYTHON} with -B -S (and -P for an inline or stdin start), no shell script under
tests/ names the shim or a bare python3, and the wrappers' shebang agrees. Behavior is established elsewhere; this
is the mechanical agreement over the tree."""
import re
import shlex
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
ENTRIES = ('build.sh', 'tests/lib/checkout_lock.sh', 'tests/run.sh', 'tests/lib/python.sh', 'tests/accept-release.sh', 'Makefile')
# Entry points that start helpers: each calls the resolver's two functions, without arguments.
PROBING = ('build.sh', 'tests/lib/checkout_lock.sh', 'tests/run.sh', 'tests/lib/python.sh', 'tests/accept-release.sh')
# testlib.sh resolves for case.sh, direct suite scripts and release acceptance; it does not probe.
RESOLVING = ('tests/lib/testlib.sh', 'tests/lib/scripts.sh')
WRAPPERS = ('tests/fixtures/build_refusals/tools.py', 'tests/fixtures/build_refusals/forward.py',
            'tests/fixtures/build_guards/tools.py')
SHEBANG = '#!/usr/bin/env -S ${PW_PYTHON} -B -S'
INTERPRETER = '${PW_PYTHON}'
# Shell scripts under tests/ that may still start the shim: none. A deliberate shim start lives in a Python control.
SHIM_ALLOWED = ()


def words_of(line):
    """The command tokens of one shell line, with quotes removed; comments and unfinished arguments are ignored."""
    lexer = shlex.shlex(line + '\n', posix=True, punctuation_chars=';&|()')
    lexer.whitespace_split = True
    words = []
    try:
        words.extend(lexer)
    except ValueError:
        pass  # keep the command tokens before an unfinished multiline argument
    return words


def shim_problems(name, lines):
    out = []
    for number, line in enumerate(lines, 1):
        if any(word in ('/usr/bin/python3', 'python3') or
               re.search(r'\$\(\s*(?:env\s+)?(?:/usr/bin/)?python3(?:\s|$)', word) for word in words_of(line)):
            out.append(f'{name}:{number}: Python ancestry must use the resolved PW_PYTHON')
    return out


START = re.compile(r'(?<![^\s("])\$\{PW_PYTHON\}"?')
WORD = re.compile(r'"[^"]*"|\'[^\']*\'|[^\s)|;&]+')


def words_after(text):
    """The words that follow an interpreter start in raw shell text, quotes removed, up to the end of its command."""
    words = []
    for match in WORD.finditer(text):
        word = match.group()
        if word in ('&&', '||', '<<'):
            break
        words.append(word[1:-1] if word[:1] in '"\'' and word[-1:] == word[:1] and len(word) > 1 else word)
    return words


def start_problems(name, lines):
    """Every ${PW_PYTHON} start carries -B -S, then -P when what follows is - or -c; nothing else before the script.

    Starts are found in the raw text, so one inside a quoted command substitution, where the shell lexer sees a
    single assignment word, is checked like any other."""
    out = []
    for number, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith('#'):
            continue
        for match in START.finditer(line):
            words = words_after(line[match.end():])
            flags = words[0:2]
            rest = words[2:4]
            if flags != ['-B', '-S']:
                out.append(f'{name}:{number}: a ${{PW_PYTHON}} start carries -B -S first, found {flags}')
                continue
            inline = rest[:1] in (['-'], ['-c']) or rest[:2] == ['-P', '-'] or rest[:2] == ['-P', '-c']
            if rest[:1] == ['-P'] and rest[1:2] not in (['-'], ['-c']):
                out.append(f'{name}:{number}: -P belongs only to an inline or stdin start')
            elif rest[:1] in (['-'], ['-c']):
                out.append(f'{name}:{number}: an inline or stdin start carries -B -S -P')
            elif rest[:1] and rest[0].startswith('-') and rest[0] not in ('-P',):
                out.append(f'{name}:{number}: a ${{PW_PYTHON}} start takes no flag beyond -B -S and -P, found {rest[0]}')
    return out


def resolver_problems(name, lines, *, probe):
    """The entry point calls pw_python_start (and pw_python_probe when it starts helpers) with no argument."""
    out = []
    found = {'pw_python_start': 0, 'pw_python_probe': 0}
    for number, line in enumerate(lines, 1):
        words = words_of(line)
        for index, word in enumerate(words):
            if word in found:
                found[word] += 1
                following = words[index + 1:index + 2]
                if following not in ([], ['||'], ['&&']):
                    out.append(f'{name}:{number}: {word} takes no argument in an entry point, found {following[0]}')
    if found['pw_python_start'] != 1:
        out.append(f'{name}: expected one pw_python_start call, found {found["pw_python_start"]}')
    if probe and found['pw_python_probe'] != 1:
        out.append(f'{name}: expected one pw_python_probe call, found {found["pw_python_probe"]}')
    if not probe and found['pw_python_probe']:
        out.append(f'{name}: only entry points probe')
    return out


def shell_scripts(root):
    return sorted(p for p in (root / 'tests').rglob('*.sh') if 'out' not in p.relative_to(root / 'tests').parts[:1])


def check(root):
    problems = []
    for name in ENTRIES:
        lines = (root / name).read_text().splitlines()
        problems += shim_problems(name, lines)
        problems += start_problems(name, lines)
        if name in PROBING:
            problems += resolver_problems(name, lines, probe=True)
    for name in RESOLVING:
        lines = (root / name).read_text().splitlines()
        problems += resolver_problems(name, lines, probe=False)
    for path in shell_scripts(root):
        name = path.relative_to(root).as_posix()
        lines = path.read_text().splitlines()
        if name not in SHIM_ALLOWED:
            problems += shim_problems(name, lines)
        problems += start_problems(name, lines)
    for name in WRAPPERS:
        if (root / name).read_text().splitlines()[0] != SHEBANG:
            problems.append(f'{name}: wrapper must start with {SHEBANG}')
    return problems


class DirectPythonTests(unittest.TestCase):
    def test_current_sources(self):
        self.assertEqual(check(ROOT), [])

    def checkout(self, temporary):
        root = Path(temporary)
        for path in [ROOT / name for name in ENTRIES + RESOLVING + WRAPPERS] + shell_scripts(ROOT):
            target = root / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(path.read_text())
        return root

    def test_independent_passing_and_rejected_sources(self):
        with tempfile.TemporaryDirectory(prefix='pw-python-drift-') as temporary:
            root = self.checkout(temporary)
            self.assertEqual(check(root), [])
            for name in ENTRIES:
                path = root / name
                original = path.read_text()
                for command in ('/usr/bin/python3 -B helper.py', 'env python3 helper.py',
                                'python3 helper.py', 'exec "/usr/bin/python3" helper.py',
                                'answer="$(python3 helper.py)"',
                                '/usr/bin/python3 -B helper.py \\\n  --check',
                                "python3 -c 'import sys\nprint(sys.version)'",
                                '"${PW_PYTHON}" -B helper.py', '"${PW_PYTHON}" -B -S -P helper.py',
                                '"${PW_PYTHON}" -B -S -I helper.py', '"${PW_PYTHON}" -B -S - <<\'PY\'',
                                '"${PW_PYTHON}" -B -S -c "print(1)"',
                                'answer="$("${PW_PYTHON}" -B -P -c \'print(1)\')"',
                                'answer="$("${PW_PYTHON}" -B -S -c \'print(1)\')"',
                                'if ! answer="$("${PW_PYTHON}" -S -B "${ROOT_DIR}/helper.py" "$1" 2>/dev/null)"; then :; fi'):
                    path.write_text(original + '\n' + command + '\n')
                    self.assertTrue(any(name in p for p in check(root)), (name, command))
                path.write_text(original + '\n# python3 and /usr/bin/python3 are forbidden ancestry\n')
                self.assertEqual(check(root), [])
                path.write_text(original + '\n"${PW_PYTHON}" -B -S helper.py\n"${PW_PYTHON}" -B -S -P -c "print(1)"\n'
                                'answer="$("${PW_PYTHON}" -B -S -P -c \'print(1)\')"\nreply="$("${PW_PYTHON}" -B -S "${ROOT_DIR}/helper.py" x 2>&1)"\n')
                self.assertEqual(check(root), [])
                path.write_text(original)
            for name in PROBING:
                path = root / name
                original = path.read_text()
                for mutation in (('pw_python_start || exit 2', 'pw_python_start /usr/bin/python3 || exit 2'),
                                 ('pw_python_probe || exit 2', 'pw_python_probe /usr/bin/python3 || exit 2'),
                                 ('pw_python_probe || exit 2', ': probe removed')):
                    self.assertIn(mutation[0], original, name)
                    path.write_text(original.replace(mutation[0], mutation[1], 1))
                    self.assertTrue(any(name in p for p in check(root)), (name, mutation))
                path.write_text(original)
            testlib = root / 'tests/lib/testlib.sh'
            original = testlib.read_text()
            testlib.write_text(original + '\npw_python_probe || exit 2\n')
            self.assertTrue(any('testlib.sh' in p for p in check(root)))
            testlib.write_text(original)
            suite = root / 'tests/suites/unit/run.sh'
            original = suite.read_text()
            for command in ('/usr/bin/python3 - <<\'PY\'', '"${PW_PYTHON}" -B - <<\'PY\'', 'python3 "${ROOT_DIR}/x.py"'):
                suite.write_text(original + '\n' + command + '\n')
                self.assertTrue(any('tests/suites/unit/run.sh' in p for p in check(root)), command)
            suite.write_text(original)
            for name in WRAPPERS:
                path = root / name
                original = path.read_text()
                for shebang in ('#!/usr/bin/python3', '#!/usr/bin/env -S ${PW_PYTHON} -B'):
                    path.write_text(original.replace(SHEBANG, shebang, 1))
                    self.assertTrue(any(name in p for p in check(root)), (name, shebang))
                path.write_text(original)
            self.assertEqual(check(root), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
