"""Keep Python ancestry direct; leaf scripts are outside this check's scope."""
import re
import shlex
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
ENTRIES = ('build.sh', 'tests/lib/checkout_lock.sh', 'tests/run.sh')
WRAPPERS = ('tests/fixtures/build_refusals/tools.py', 'tests/fixtures/build_refusals/forward.py',
            'tests/fixtures/build_guards/tools.py')
SHEBANG = '#!/usr/bin/env -S ${PW_PYTHON} -B'


def check(root):
    problems = []
    for name in ENTRIES:
        # These entry scripts contain no Python heredocs. Shell quoting must
        # not hide an interpreter command; comments and longer arguments are ignored.
        for number, line in enumerate((root / name).read_text().splitlines(), 1):
            lexer = shlex.shlex(line + '\n', posix=True, punctuation_chars=';&|()')
            lexer.whitespace_split = True
            words = []
            try:
                words.extend(lexer)
            except ValueError:
                pass  # keep the command tokens before an unfinished multiline argument
            if any(word in ('/usr/bin/python3', 'python3') or
                   re.search(r'\$\(\s*(?:env\s+)?(?:/usr/bin/)?python3(?:\s|$)', word) for word in words):
                problems.append(f'{name}:{number}: Python ancestry must use the resolved PW_PYTHON')
    for name in WRAPPERS:
        if (root / name).read_text().splitlines()[0] != SHEBANG:
            problems.append(f'{name}: wrapper must start with {SHEBANG}')
    return problems


class DirectPythonTests(unittest.TestCase):
    def test_current_sources(self):
        self.assertEqual(check(ROOT), [])

    def test_independent_passing_and_rejected_sources(self):
        with tempfile.TemporaryDirectory(prefix='pw-python-drift-') as temporary:
            root = Path(temporary)
            for name in ENTRIES + WRAPPERS:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text((ROOT / name).read_text())
            self.assertEqual(check(root), [])
            for name in ENTRIES:
                path = root / name
                original = path.read_text()
                for command in ('/usr/bin/python3 -B helper.py', 'env python3 helper.py',
                                'python3 helper.py', 'exec "/usr/bin/python3" helper.py',
                                'answer="$(python3 helper.py)"',
                                '/usr/bin/python3 -B helper.py \\\n  --check',
                                "python3 -c 'import sys\nprint(sys.version)'"):
                    path.write_text(original + '\n' + command + '\n')
                    self.assertTrue(any(name in p for p in check(root)), (name, command))
                path.write_text(original + '\n# python3 and /usr/bin/python3 are forbidden ancestry\n')
                self.assertEqual(check(root), [])
                path.write_text(original)
            for name in WRAPPERS:
                path = root / name
                original = path.read_text()
                path.write_text(original.replace(SHEBANG, '#!/usr/bin/python3', 1))
                self.assertTrue(any(name in p for p in check(root)), name)
                path.write_text(original)
            self.assertEqual(check(root), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
