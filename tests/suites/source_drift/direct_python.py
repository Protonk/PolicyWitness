"""Keep every Python start under the resolver's form: entry points resolve and probe without arguments, every shell
start of the interpreter is ${PW_PYTHON} with -B -S (and -P for an inline or stdin start), no shell script under
tests/ names the shim or a bare python3, and the wrappers' shebang agrees. Behavior is established elsewhere; this
is the mechanical agreement over the tree.

Each check reads one file's lines and names its problems; `check(root)` dispatches the tree's entry points,
resolvers, discovered shell scripts and wrappers to them. The controls exercise each check on its own text, and
one full-tree scan establishes discovery-to-check dispatch.
"""
import os
import re
import shlex
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'docs'))
sys.path.insert(0, str(ROOT / 'tests/lib'))
import receipts  # noqa: E402
import fixture_inputs  # noqa: E402
import repository_tree  # noqa: E402
from repository_tree import inventory, required  # noqa: E402
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
# What check(root) reads: the entry points, the resolvers, the wrappers and every shell script under tests/.
INPUTS = (*(required(name) for name in ENTRIES + RESOLVING + WRAPPERS), inventory(repository_tree.TEST_SHELL_SCRIPTS))


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


def entry_problems(name, lines):
    """An entry point: no shim, well-formed starts, and the resolver calls when it starts helpers."""
    problems = shim_problems(name, lines) + start_problems(name, lines)
    if name in PROBING:
        problems += resolver_problems(name, lines, probe=True)
    return problems


def script_problems(name, lines):
    """A discovered shell script: no shim unless allowed, and well-formed starts."""
    problems = [] if name in SHIM_ALLOWED else shim_problems(name, lines)
    return problems + start_problems(name, lines)


def wrapper_problems(name, lines):
    return [] if lines[:1] == [SHEBANG] else [f'{name}: wrapper must start with {SHEBANG}']


def shell_scripts(root):
    """Every shell script under tests/ except retained output, through the test-shell scope's pruned walk."""
    tree = repository_tree.Tree(root)
    return [tree.path(relative) for relative in tree.inventory(repository_tree.TEST_SHELL_SCRIPTS)]


def check(root):
    """Every file the tree holds, dispatched to its check; an entry point found by discovery is checked once."""
    tree = repository_tree.Tree(root)
    problems = []
    for name in ENTRIES:
        problems += entry_problems(name, tree.read_text(name).splitlines())
    for name in RESOLVING:
        problems += resolver_problems(name, tree.read_text(name).splitlines(), probe=False)
    for name in tree.inventory(repository_tree.TEST_SHELL_SCRIPTS):
        if name not in ENTRIES:
            problems += script_problems(name, tree.read_text(name).splitlines())
    for name in WRAPPERS:
        problems += wrapper_problems(name, tree.read_text(name).splitlines())
    return problems


FORBIDDEN_STARTS = ('/usr/bin/python3 -B helper.py', 'env python3 helper.py',
                    'python3 helper.py', 'exec "/usr/bin/python3" helper.py',
                    'answer="$(python3 helper.py)"',
                    '/usr/bin/python3 -B helper.py \\\n  --check',
                    "python3 -c 'import sys\nprint(sys.version)'")
MALFORMED_STARTS = ('"${PW_PYTHON}" -B helper.py', '"${PW_PYTHON}" -B -S -P helper.py',
                    '"${PW_PYTHON}" -B -S -I helper.py', '"${PW_PYTHON}" -B -S - <<\'PY\'',
                    '"${PW_PYTHON}" -B -S -c "print(1)"',
                    'answer="$("${PW_PYTHON}" -B -P -c \'print(1)\')"',
                    'answer="$("${PW_PYTHON}" -B -S -c \'print(1)\')"',
                    'if ! answer="$("${PW_PYTHON}" -S -B "${ROOT_DIR}/helper.py" "$1" 2>/dev/null)"; then :; fi')
ACCEPTED_STARTS = ('# python3 and /usr/bin/python3 are forbidden ancestry',
                   '"${PW_PYTHON}" -B -S helper.py', '"${PW_PYTHON}" -B -S -P -c "print(1)"',
                   'answer="$("${PW_PYTHON}" -B -S -P -c \'print(1)\')"',
                   'reply="$("${PW_PYTHON}" -B -S "${ROOT_DIR}/helper.py" x 2>&1)"')


class DirectPythonTests(receipts.TestCase):
    def test_current_sources(self):
        self.assertEqual(check(ROOT), [])

    def test_forbidden_and_malformed_starts_are_named_by_their_check(self):
        """Each forbidden ancestry form is named by the shim check, each malformed start by the start check,
        and the accepted forms by neither; the text is checked on its own, not through a tree scan."""
        for command in FORBIDDEN_STARTS:
            with self.subTest(command=command):
                lines = command.split('\n')
                self.assertTrue(shim_problems('x.sh', lines), command)
                self.assertTrue(all(p.startswith('x.sh:') and 'PW_PYTHON' in p for p in shim_problems('x.sh', lines)))
        for command in MALFORMED_STARTS:
            with self.subTest(command=command):
                lines = command.split('\n')
                self.assertEqual(shim_problems('x.sh', lines), [])
                self.assertTrue(start_problems('x.sh', lines), command)
        for command in ACCEPTED_STARTS:
            with self.subTest(command=command):
                lines = command.split('\n')
                self.assertEqual(shim_problems('x.sh', lines) + start_problems('x.sh', lines), [])

    def test_resolver_calls_are_named_by_their_check(self):
        """A probing entry point must call both resolver functions once without arguments; a resolver must not probe."""
        for name in PROBING:
            original = (ROOT / name).read_text()
            self.assertEqual(entry_problems(name, original.splitlines()), [], name)
            for mutation in (('pw_python_start || exit 2', 'pw_python_start /usr/bin/python3 || exit 2'),
                             ('pw_python_probe || exit 2', 'pw_python_probe /usr/bin/python3 || exit 2'),
                             ('pw_python_probe || exit 2', ': probe removed')):
                with self.subTest(name=name, mutation=mutation):
                    self.assertIn(mutation[0], original, name)
                    mutated = original.replace(mutation[0], mutation[1], 1).splitlines()
                    problems = resolver_problems(name, mutated, probe=True)
                    self.assertTrue(problems, (name, mutation))
                    self.assertTrue(all(p.startswith(name) for p in problems))
        for name in RESOLVING:
            lines = (ROOT / name).read_text().splitlines()
            self.assertEqual(resolver_problems(name, lines, probe=False), [], name)
            self.assertEqual(resolver_problems(name, lines + ['pw_python_probe || exit 2'], probe=False),
                             [f'{name}: only entry points probe'])

    def test_wrapper_shebangs_are_named_by_their_check(self):
        for name in WRAPPERS:
            lines = (ROOT / name).read_text().splitlines()
            self.assertEqual(wrapper_problems(name, lines), [], name)
            for shebang in ('#!/usr/bin/python3', '#!/usr/bin/env -S ${PW_PYTHON} -B'):
                with self.subTest(name=name, shebang=shebang):
                    self.assertEqual(wrapper_problems(name, [shebang] + lines[1:]), [f'{name}: wrapper must start with {SHEBANG}'])

    def checkout(self, temporary):
        root = Path(temporary)
        copied = fixture_inputs.copy_declared(ROOT, root, fixture_inputs.expand(ROOT, INPUTS))
        print(f'fixture: {copied.files} files, {copied.bytes} bytes, {copied.seconds:.3f} s')
        self.track_inputs(root)
        return root

    def test_full_tree_scan_dispatches_discovery_to_the_checks(self):
        """A copied checkout passes; faults in an entry point, a suite script, a wrapper and a newly discovered
        script are each named once in one scan, an entry point found by discovery is not reported twice, and
        the restored copy passes."""
        with tempfile.TemporaryDirectory(prefix='pw-python-drift-') as temporary:
            root = self.checkout(temporary)
            self.assertEqual(check(root), [])
            entry = root / 'tests/run.sh'
            suite = root / 'tests/suites/unit/run.sh'
            wrapper = root / WRAPPERS[0]
            discovered = root / 'tests/suites/new_suite/extra.sh'
            originals = {path: path.read_text() for path in (entry, suite, wrapper)}
            entry.write_text(originals[entry] + '\npython3 helper.py\n')
            suite.write_text(originals[suite] + '\n"${PW_PYTHON}" -B - <<\'PY\'\n')
            wrapper.write_text(originals[wrapper].replace(SHEBANG, '#!/usr/bin/python3', 1))
            discovered.parent.mkdir()
            discovered.write_text('#!/usr/bin/env bash\n/usr/bin/python3 - <<\'PY\'\n')
            problems = check(root)
            by_file = {}
            for problem in problems:
                by_file.setdefault(problem.split(':')[0], []).append(problem)
            self.assertEqual(sorted(by_file), ['tests/fixtures/build_refusals/tools.py', 'tests/run.sh', 'tests/suites/new_suite/extra.sh',
                                               'tests/suites/unit/run.sh'])
            self.assertEqual({name: len(found) for name, found in by_file.items()},
                             {'tests/fixtures/build_refusals/tools.py': 1, 'tests/run.sh': 1, 'tests/suites/new_suite/extra.sh': 1,
                              'tests/suites/unit/run.sh': 1})
            for path, text in originals.items():
                path.write_text(text)
            discovered.unlink()
            discovered.parent.rmdir()
            self.assertEqual(check(root), [])

    def test_inventory_is_a_pruned_walk_of_the_shell_scope(self):
        """Every shell script under tests/ is selected except retained output, in lexical order, and the
        walk never enters tests/out. Hidden and vendored paths, a nested `out`, file and broken symlinks and a
        directory named with the suffix stay candidates; a directory symlink is not followed; a near miss
        such as tests/output is included."""
        with tempfile.TemporaryDirectory(prefix='pw-shell-inventory-') as temporary:
            root = Path(temporary)
            for name in ('build.sh', 'tests/run.sh', 'tests/.hidden/keep.sh', 'tests/nested/out/keep.sh',
                         'tests/output/keep.sh', 'tests/lib/vendor/keep.sh', 'tests/suites/x/run.sh',
                         'tests/dir.sh/inner.sh', 'tests/out/drop.sh', 'tests/notes.md'):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text('')
            for index in range(200):
                case = root / f'tests/out/runs/run-{index:03d}/suites/case'
                case.mkdir(parents=True)
                (case / 'run.sh').write_text('')
            (root / 'tests/linked.sh').symlink_to('run.sh')
            (root / 'tests/linked-dir').symlink_to('suites', target_is_directory=True)
            (root / 'tests/broken.sh').symlink_to('missing.sh')
            entered = []
            original = os.scandir

            def counted(path='.'):
                entered.append(Path(os.fspath(path)).relative_to(root).as_posix())
                return original(path)
            os.scandir = counted
            try:
                selected = [p.relative_to(root).as_posix() for p in shell_scripts(root)]
            finally:
                os.scandir = original
            self.assertEqual(selected, ['tests/.hidden/keep.sh', 'tests/broken.sh', 'tests/dir.sh', 'tests/dir.sh/inner.sh',
                                        'tests/lib/vendor/keep.sh', 'tests/linked.sh', 'tests/nested/out/keep.sh',
                                        'tests/output/keep.sh', 'tests/run.sh', 'tests/suites/x/run.sh'])
            self.assertEqual(sorted(entered), ['tests', 'tests/.hidden', 'tests/dir.sh', 'tests/lib', 'tests/lib/vendor',
                                               'tests/nested', 'tests/nested/out', 'tests/output', 'tests/suites',
                                               'tests/suites/x'])
            self.assertEqual([d for d in entered if d == 'tests/out' or d.startswith('tests/out/')], [])


if __name__ == '__main__':
    sys.exit(receipts.timed_main(sys.modules[__name__], 'source_drift/direct_python_start', 'direct_python'))
