"""The Cargo configuration one invocation reads, parsed structurally, and the compiler selection and child environment it implies.

Cargo, invoked in a directory, reads `.cargo/config` or `.cargo/config.toml`
in that directory and in each ancestor, then `$CARGO_HOME/config(.toml)`
unless the walk already read it; where both names exist it uses `config`.
Deeper files take precedence over ancestors and Cargo home is lowest. A file's
top-level `include` loads other `.toml` files first, left to right with later
ones winning and recursively, and the including file's own values are merged
on top. Merging is Cargo's: tables merge key by key, arrays are joined with
higher-precedence items later, a higher-precedence scalar replaces a lower
one, and a value whose type differs between files is an error. Every leaf
keeps the file that defined it, because a config-relative path resolves from
the parent of the directory that holds its file, while a path from the
environment resolves from the invocation directory.

The compiler is RUSTC, else CARGO_BUILD_RUSTC, else build.rustc, else
`rustc`; each wrapper likewise (RUSTC_WRAPPER over CARGO_BUILD_RUSTC_WRAPPER
over build.rustc-wrapper, and the workspace wrapper), where an empty value at
any level disables the wrapper. A program value with a path separator is a
path; a bare name is searched on the PATH Cargo gives its children, which
`[env]` can replace. Cargo applies `[env]` to every process it starts,
including its own `rustc -vV` probe: an entry replaces a variable Cargo's own
environment already holds only when forced, and a relative entry becomes an
absolute path below its file's root. When `cargo` on PATH is a rustup proxy,
the proxy prepends `$CARGO_HOME/bin` to Cargo's PATH and sets
RUSTUP_TOOLCHAIN to the toolchain it resolved in the invocation directory;
that is the only launcher this module models, recognised because only a
rustup proxy accepts `cargo +<toolchain>`.

Nothing here guesses. A file that cannot be read or parsed, input beyond the
bounds (FILE_BYTES per file, TOTAL_BYTES in all, FILE_COUNT files, INCLUDE_DEPTH
levels), an include cycle, a missing required include, a value of an
unsupported type for a key this resolution uses, a program that cannot be
found, or a launcher answer that cannot be read is an Unresolved condition,
never a fallback to PATH. The resolution carries the redacted file graph, the
selected commands with their sources and the sources they override, the
`[env]` names with whether each applied, the effective values of the
variables that select the compiler or feed it, and the requested Rust flags by
precedence. It never carries raw configuration values beyond those, PATH or
any other environment value.
"""
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))

FILE_BYTES = 256 * 1024
TOTAL_BYTES = 1024 * 1024
FILE_COUNT = 64
INCLUDE_DEPTH = 8
# Variables whose effective child value selects the compiler or feeds it, resolved rather than named.
SELECTING = ('PATH', 'RUSTUP_TOOLCHAIN', 'RUSTUP_HOME')
FEEDING = ('SDKROOT', 'MACOSX_DEPLOYMENT_TARGET', 'DEVELOPER_DIR')
PROGRAMS = (
    ('rustc', 'rustc', ('RUSTC',), 'CARGO_BUILD_RUSTC'),
    ('wrapper', 'rustc-wrapper', ('RUSTC_WRAPPER',), 'CARGO_BUILD_RUSTC_WRAPPER'),
    ('workspace_wrapper', 'rustc-workspace-wrapper', ('RUSTC_WORKSPACE_WRAPPER',), 'CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER'),
)


class Unresolved(Exception):
    """A setting the resolution needs that cannot be established."""


class Leaf:
    """A scalar from one file, with the file that defined it (None for the environment)."""

    __slots__ = ('value', 'origin')

    def __init__(self, value, origin):
        self.value, self.origin = value, origin


def root_of(origin, cwd):
    """The directory a config-relative path resolves from: two levels above its file, or the invocation directory."""
    return Path(cwd) if origin is None else Path(origin).parent.parent


def redact(value, home):
    if isinstance(value, str) and home and home != '/':
        if value == home:
            return '<home>'
        return value.replace(home + '/', '<home>/')
    return value


# ---- reading and merging ----------------------------------------------------------------------

class Reader:
    def __init__(self):
        self.total, self.files = 0, []

    def load(self, path):
        """A parsed file, bounded; Unresolved when it cannot be read, is too large or is not valid TOML."""
        import tomli
        path = Path(path)
        if len(self.files) >= FILE_COUNT:
            raise Unresolved(f'more than {FILE_COUNT} configuration files')
        try:
            info = path.stat()
        except OSError as exc:
            raise Unresolved(f'{path} cannot be read ({exc.__class__.__name__})')
        if not path.is_file():
            raise Unresolved(f'{path} is not a regular file')
        if info.st_size > FILE_BYTES:
            raise Unresolved(f'{path} is larger than {FILE_BYTES} bytes')
        try:
            with path.open('rb') as stream:
                data = stream.read(FILE_BYTES + 1)
        except OSError as exc:
            raise Unresolved(f'{path} cannot be read ({exc.__class__.__name__})')
        if len(data) > FILE_BYTES:
            raise Unresolved(f'{path} is larger than {FILE_BYTES} bytes')
        self.total += len(data)
        if self.total > TOTAL_BYTES:
            raise Unresolved(f'the configuration exceeds {TOTAL_BYTES} bytes in all')
        try:
            parsed = tomli.loads(data.decode('utf-8'))
        except (UnicodeDecodeError, tomli.TOMLDecodeError) as exc:
            raise Unresolved(f'{path} is not valid TOML ({str(exc)[:120]})')
        self.files.append(str(path))
        return parsed


def wrap(value, origin):
    if isinstance(value, dict):
        return {k: wrap(v, origin) for k, v in value.items()}
    if isinstance(value, list):
        return [wrap(v, origin) for v in value]
    return Leaf(value, origin)


def kind(value):
    return 'table' if isinstance(value, dict) else 'array' if isinstance(value, list) else type(value.value).__name__


def merge(lower, higher, where=''):
    """Cargo's merge of a higher-precedence tree onto a lower one."""
    if isinstance(lower, dict) and isinstance(higher, dict):
        out = dict(lower)
        for key, value in higher.items():
            out[key] = merge(out[key], value, f'{where}.{key}' if where else key) if key in out else value
        return out
    if isinstance(lower, list) and isinstance(higher, list):
        return lower + higher
    if isinstance(lower, (dict, list)) or isinstance(higher, (dict, list)) or type(lower.value) is not type(higher.value):
        raise Unresolved(f'configuration key `{where}` is a {kind(lower)} in one file and a {kind(higher)} in another')
    return higher


def include_entries(tree, path):
    include = tree.pop('include', None)
    if include is None:
        return []
    if not isinstance(include, list):
        raise Unresolved(f'{path}: `include` must be an array')
    entries = []
    for item in include:
        if isinstance(item, Leaf) and isinstance(item.value, str):
            entries.append((item.value, False))
        elif (isinstance(item, dict) and isinstance(item.get('path'), Leaf) and isinstance(item['path'].value, str)
              and set(item) <= {'path', 'optional'}
              and (('optional' not in item) or (isinstance(item['optional'], Leaf) and isinstance(item['optional'].value, bool)))):
            entries.append((item['path'].value, bool(item['optional'].value) if 'optional' in item else False))
        else:
            raise Unresolved(f'{path}: an `include` entry is neither a path nor a table with `path` and `optional`')
    return entries


def load_file(reader, path, stack, graph):
    """One file with its includes beneath it, as a merged tree; graph receives the file and its includes."""
    path = Path(os.path.abspath(path))
    real = os.path.realpath(path)
    if real in stack:
        raise Unresolved(f'{path}: include cycle')
    if len(stack) > INCLUDE_DEPTH:
        raise Unresolved(f'{path}: includes nest deeper than {INCLUDE_DEPTH}')
    tree = wrap(reader.load(path), str(path))
    node = dict(path=str(path), includes=[])
    graph.append(node)
    merged = {}
    for target, optional in include_entries(tree, path):
        if not target.endswith('.toml'):
            raise Unresolved(f'{path}: include `{target}` does not end in .toml')
        included = path.parent / target
        if not included.exists():
            if optional:
                node['includes'].append(dict(path=str(included), optional=True, loaded=False))
                continue
            raise Unresolved(f'{path}: required include {included} is missing')
        node['includes'].append(dict(path=str(included), optional=optional, loaded=True))
        merged = merge(merged, load_file(reader, included, stack | {real}, graph))
    return merge(merged, tree)


def chosen(directory):
    """The configuration file Cargo reads in a directory: `config` when present, else `config.toml`, else None."""
    for name in ('config', 'config.toml'):
        candidate = Path(directory) / name
        if os.path.lexists(candidate):
            return candidate
    return None


def discover(cwd, env):
    """The configuration files of one invocation, highest precedence first, with Cargo home last."""
    found, seen = [], set()
    directory = Path(os.path.abspath(cwd))
    while True:
        path = chosen(directory / '.cargo')
        if path is not None:
            found.append(path)
            seen.add(os.path.realpath(path))
        if directory.parent == directory:
            break
        directory = directory.parent
    home = cargo_home(env)
    path = chosen(home)
    if path is not None and os.path.realpath(path) not in seen:
        found.append(path)
    return found


def cargo_home(env):
    return Path(env['CARGO_HOME']) if env.get('CARGO_HOME') else Path(env.get('HOME', '/')) / '.cargo'


def load(cwd, env):
    """The merged configuration and its graph of files, read the way Cargo reads them."""
    reader, graph, merged = Reader(), [], {}
    for path in reversed(discover(cwd, env)):
        merged = merge(merged, load_file(reader, path, frozenset(), graph))
    return merged, graph


def leaf(tree, *keys):
    node = tree
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


# ---- the launcher -------------------------------------------------------------------------------

def launcher(cwd, env, probe):
    """What starts Cargo: a rustup proxy, with the toolchain it resolves here, or Cargo itself.

    The proxy is recognised by what it does, through whatever `cargo` on PATH
    runs (a wrapper included): only a rustup proxy accepts a `+toolchain`
    argument. An unreadable probe cannot establish that Cargo is standalone;
    resolution refuses when no toolchain is available to distinguish them."""
    cargo = shutil.which('cargo', path=env.get('PATH'))
    if not cargo:
        raise Unresolved('cargo is not on PATH')
    rustup = shutil.which('rustup', path=env.get('PATH'))
    toolchain = env.get('RUSTUP_TOOLCHAIN')
    if not toolchain:
        if not rustup:
            raise Unresolved('the Cargo launcher cannot be resolved without rustup on PATH or an explicit RUSTUP_TOOLCHAIN')
        found = probe([rustup, 'show', 'active-toolchain'], cwd=cwd, env=env, limit=4096, stderr_limit=4096)
        words = found['text'].split() if found['status'] == 'ok' else []
        if not words:
            raise Unresolved('rustup did not establish the active toolchain (' + found.get('kind', 'malformed_output') + ')')
        toolchain = words[0]
    proxied = probe([cargo, f'+{toolchain}', '--version'], cwd=cwd, env=env, limit=4096, stderr_limit=4096)
    if proxied['status'] != 'ok':
        if proxied.get('kind') != 'nonzero_exit':
            raise Unresolved('the Cargo launcher probe failed (' + proxied.get('kind', 'unknown') + ')')
        return dict(kind='cargo', cargo=cargo)
    return dict(kind='rustup proxy', cargo=cargo, toolchain=toolchain)


# ---- resolution ----------------------------------------------------------------------------------

def program(value, origin, cwd, path_value, label):
    """A program Cargo would run, as an absolute path: config-relative or invocation-relative, or found on the child PATH."""
    if not isinstance(value, str) or not value:
        raise Unresolved(f'{label} is not a program path')
    if '/' in value:
        return os.path.normpath(os.path.join(root_of(origin, cwd), value))
    found = shutil.which(value, path=path_value)
    if not found:
        raise Unresolved(f'{label} names `{value}`, which is not on the PATH Cargo gives the compiler')
    return found


def child_environment(merged, base, cwd):
    """Cargo's environment for the processes it starts: the base with `[env]` applied; each entry and whether it applied."""
    table = merged.get('env', {})
    if not isinstance(table, dict):
        raise Unresolved('`env` is not a table')
    child, entries = dict(base), {}
    for name, entry in sorted(table.items()):
        if isinstance(entry, Leaf):
            value, force, relative, origin = entry.value, False, False, entry.origin
        elif isinstance(entry, dict) and isinstance(entry.get('value'), Leaf) and set(entry) <= {'value', 'force', 'relative'}:
            value, origin = entry['value'].value, entry['value'].origin
            flags = {}
            for flag in ('force', 'relative'):
                item = entry.get(flag)
                if item is not None and not (isinstance(item, Leaf) and isinstance(item.value, bool)):
                    raise Unresolved(f'`env.{name}.{flag}` is not a boolean')
                flags[flag] = bool(item.value) if item is not None else False
            force, relative = flags['force'], flags['relative']
        else:
            raise Unresolved(f'`env.{name}` is neither a string nor a table with `value`, `force` and `relative`')
        if not isinstance(value, str):
            raise Unresolved(f'`env.{name}` does not hold a string value')
        if relative:
            value = os.path.normpath(os.path.join(root_of(origin, cwd), value))
        applied = force or name not in base
        if applied:
            child[name] = value
        entries[name] = dict(applied=applied, force=force, relative=relative, file=origin)
    return child, entries


def selection(merged, env, cwd, path_value):
    """The compiler and each wrapper: the command, where the choice came from and the lower sources it overrides."""
    out = {}
    for role, key, plain, config_env in PROGRAMS:
        sources = []
        for name in plain:
            if name in env:
                sources.append((name, env[name], None))
        if config_env in env:
            sources.append((config_env, env[config_env], None))
        configured = leaf(merged, 'build', key)
        if configured is not None:
            if not isinstance(configured, Leaf) or not isinstance(configured.value, str):
                raise Unresolved(f'`build.{key}` is not a string program path')
            sources.append((f'build.{key}', configured.value, configured.origin))
        if not sources:
            out[role] = (dict(source='default', command='rustc', configured='rustc', overrides=[]) if role == 'rustc'
                         else dict(source='none', command=None, configured=None, overrides=[]))
            if role == 'rustc':
                out[role]['command'] = program('rustc', None, cwd, path_value, 'the default compiler')
            continue
        source, value, origin = sources[0]
        entry = dict(source=source, configured=value, file=origin, overrides=[s[0] for s in sources[1:]])
        if role != 'rustc' and value == '':
            entry.update(command=None, disabled=True)
        else:
            entry['command'] = program(value, origin, cwd, path_value, source)
        out[role] = entry
    return out


def requested_flags(merged, env, host):
    """The source Cargo takes its extra rustc flags from, by its precedence; tokens only where the source is established."""
    present = []
    if 'CARGO_ENCODED_RUSTFLAGS' in env:
        value = env['CARGO_ENCODED_RUSTFLAGS']
        present.append(dict(source='CARGO_ENCODED_RUSTFLAGS', tokens=[] if value == '' else value.split('\x1f'), resolved=True))
    if 'RUSTFLAGS' in env:
        present.append(dict(source='RUSTFLAGS', tokens=env['RUSTFLAGS'].split(), resolved=True))
    target = merged.get('target', {})
    rules = {}
    if isinstance(target, dict):
        for name, table in target.items():
            if isinstance(table, dict) and 'rustflags' in table:
                rules[name] = table['rustflags']
    env_rule = f'CARGO_TARGET_{host.upper().replace("-", "_")}_RUSTFLAGS' if host else None
    applicable = {k: v for k, v in rules.items() if k == host or k.startswith('cfg(')}
    if applicable or (env_rule and env_rule in env):
        resolved = not any(k.startswith('cfg(') for k in applicable)
        tokens = []
        for value in applicable.values():
            tokens += flag_list(value)
        if env_rule and env_rule in env:
            resolved = False  # how Cargo joins an environment rule with file rules is not modelled
        present.append(dict(source='target rules', tokens=tokens if resolved else None, resolved=resolved,
                            rules=sorted(applicable) + ([env_rule] if env_rule and env_rule in env else [])))
    build = leaf(merged, 'build', 'rustflags')
    if build is not None or 'CARGO_BUILD_RUSTFLAGS' in env:
        resolved = build is None or 'CARGO_BUILD_RUSTFLAGS' not in env
        tokens = env['CARGO_BUILD_RUSTFLAGS'].split() if build is None else flag_list(build)
        present.append(dict(source='build.rustflags', tokens=tokens if resolved else None, resolved=resolved))
    if not present:
        return dict(source='none', tokens=[], resolved=True, overrides=[])
    return dict(present[0], overrides=[p['source'] for p in present[1:]])


def flag_list(value):
    if isinstance(value, Leaf) and isinstance(value.value, str):
        return value.value.split()
    if isinstance(value, list) and all(isinstance(v, Leaf) and isinstance(v.value, str) for v in value):
        return [v.value for v in value]
    raise Unresolved('a rustflags value is neither a string nor an array of strings')


def resolve(cwd, env, *, probe):
    """The resolution for a Cargo invocation in cwd with environment env (the caller's, as Cargo receives it).

    probe runs the launcher queries with the caller's bounds. The merged tree is
    returned for the flag attribution, which needs the host the compiler reports."""
    merged, graph = load(cwd, env)
    start = launcher(cwd, env, probe)
    base = dict(env)
    if start['kind'] == 'rustup proxy':
        base['PATH'] = f"{cargo_home(env) / 'bin'}{os.pathsep}{env.get('PATH', '')}"
        base['RUSTUP_TOOLCHAIN'] = start['toolchain']
    child, entries = child_environment(merged, base, cwd)
    programs = selection(merged, env, cwd, child.get('PATH'))
    return dict(graph=graph, launcher=start, env_entries=entries, programs=programs, child=child, merged=merged)


def conflicts(resolution, env):
    """Effective settings Cargo would give the compiler that differ from the ones the build selected."""
    out = []
    for name in FEEDING:
        if resolution['child'].get(name) != env.get(name):
            out.append((name, resolution['child'].get(name), env.get(name)))
    return out


def summary(resolution, home):
    """The publishable account: redacted paths, sources and names, the feeding values, never PATH or other environment values."""
    def file_entry(node):
        return dict(path=redact(node['path'], home),
                    includes=[dict(path=redact(i['path'], home), optional=i['optional'], loaded=i['loaded']) for i in node['includes']])
    programs = {}
    for role, entry in resolution['programs'].items():
        programs[role] = dict(source=entry['source'], command=redact(entry.get('command'), home), overrides=entry['overrides'],
                              file=redact(entry.get('file'), home), disabled=bool(entry.get('disabled')))
    child = resolution['child']
    return dict(files=[file_entry(n) for n in resolution['graph']],
                launcher=dict(kind=resolution['launcher']['kind'], toolchain=resolution['launcher'].get('toolchain')),
                programs=programs,
                env_entries={name: dict(applied=e['applied'], force=e['force'], relative=e['relative'], file=redact(e['file'], home))
                             for name, e in resolution['env_entries'].items()},
                child_environment=dict({name: redact(child.get(name), home) for name in FEEDING},
                                       RUSTUP_TOOLCHAIN=child.get('RUSTUP_TOOLCHAIN'),
                                       path_replaced_by_env=bool(resolution['env_entries'].get('PATH', {}).get('applied')),
                                       rustup_home_replaced_by_env=bool(resolution['env_entries'].get('RUSTUP_HOME', {}).get('applied'))))
