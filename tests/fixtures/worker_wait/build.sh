#!/usr/bin/env bash
# Builds the stamp worker and an uninstrumented twin from the unmodified
# production source with one flag list: meson.build's c_executable_flags and
# link arguments for pw-probe-runner, plus -Werror. The two commands differ
# only in their source file, so the twin can stand as the uninstrumented
# neighbor. Writes <output directory>/worker-build.json with the commands,
# toolchain, sha256 of every repository input and output, the seam call sites
# found in the production source, warm-up and --version observations.
#   build.sh <output directory>
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
FIXTURE_DIR="${ROOT_DIR}/tests/fixtures/worker_wait"
OUTPUT_DIR="${1:?usage: build.sh <output directory>}"
: "${PW_PYTHON:?build.sh needs the resolved PW_PYTHON that tests/run.sh and tests/lib/python.sh export}"
mkdir -p "${OUTPUT_DIR}"
OUTPUT_DIR="$(cd "${OUTPUT_DIR}" && pwd)"

FLAGS=(-Wall -Wextra -Werror -O2 -std=c11 -mmacosx-version-min=26.0 -arch arm64
       -I "${ROOT_DIR}/controller/tools/pw_probe_runner" -I "${FIXTURE_DIR}")
STAMPS=(/usr/bin/xcrun --sdk macosx clang "${FLAGS[@]}" "${FIXTURE_DIR}/stamp_worker.c"
        -lsandbox -o "${OUTPUT_DIR}/pw-probe-runner-stamps")
PLAIN=(/usr/bin/xcrun --sdk macosx clang "${FLAGS[@]}" "${ROOT_DIR}/controller/tools/pw_probe_runner/pw_probe_runner.c"
       -lsandbox -o "${OUTPUT_DIR}/pw-probe-runner-plain")
"${STAMPS[@]}"
"${PLAIN[@]}"

# Execute each output once with no arguments, stdin at EOF and only the
# standard descriptors open, so it exits at argument parsing (status 2), then
# with --version. The first exec of a new file can take hundreds of
# milliseconds; copies staged into an app are new files and stay cold until
# their own excluded execution. Elapsed time is diagnostic only. Any refusal
# still writes the receipt, then fails the build.
"${PW_PYTHON}" -B -S -P - "${ROOT_DIR}" "${OUTPUT_DIR}" "${#FLAGS[@]}" "${FLAGS[@]}" \
  "${#STAMPS[@]}" "${STAMPS[@]}" "${#PLAIN[@]}" "${PLAIN[@]}" <<'PY'
import hashlib, json, os, re, subprocess, sys, time
from pathlib import Path

argv = sys.argv[1:]
root, out = Path(argv[0]), Path(argv[1])
rest, lists = argv[2:], []
while rest:
    count = int(rest[0]); lists.append(rest[1:1 + count]); rest = rest[1 + count:]
flags, commands = lists[0], dict(stamps=lists[1], plain=lists[2])
production_dir = root / 'controller/tools/pw_probe_runner'
fixture_dir = root / 'tests/fixtures/worker_wait'
problems = []

# Call sites each seam must have in the production source; a different count
# changes what a stamp means, so the build refuses rather than records less.
SEAMS = {'PW_CONTINUOUS_READ': 2, 'PW_TIMEBASE_INFO': 1, 'PW_APPLIED_PUBLISHED': 1,
         'PW_PROCEED_ARRIVED': 1, 'PW_PROCEED_ORDINAL_LOADED': 1, 'PW_PROCEED_ACKNOWLEDGED': 1,
         'PW_ACTIVATION_LOADED': 1, 'PW_ACTIVATION_STORED': 1, 'PW_EXCHANGE_ANSWERED': 1,
         'PW_INBOUND_SCAN_PASS': 1, 'PW_INBOUND_SCAN_VISIT': 1, 'PW_INBOUND_SCAN_LOAD': 2,
         'PW_INBOUND_OBSERVE': 1, 'PW_INBOUND_ACKNOWLEDGED': 1, 'PW_ATTEMPT_PUBLISHED': 1,
         'PW_TERMINAL_PUBLISHED': 1}


def digest(path):
    hasher = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


def run(command, **kwargs):
    start = time.monotonic()
    try:
        result = subprocess.run([str(a) for a in command], capture_output=True, text=True, timeout=60, **kwargs)
        record = dict(argv=[str(a) for a in command], returncode=result.returncode,
                      stdout=result.stdout, stderr=result.stderr)
    except subprocess.TimeoutExpired:
        record = dict(argv=[str(a) for a in command], returncode='timeout', stdout=None, stderr=None)
    except OSError as error:
        record = dict(argv=[str(a) for a in command], returncode=f'launch error ({error.strerror})',
                      stdout=None, stderr=None)
    record['elapsed_ms'] = int((time.monotonic() - start) * 1000)
    return record


def relative(path):
    resolved = Path(path).resolve()
    return str(resolved.relative_to(root)) if resolved.is_relative_to(root) else str(resolved)


def dependencies(role, sdk):
    """Files clang reads for this output, from its -MM listing with the same flags: repository
    inputs, and files inside the selected SDK (such as SDKSettings.json) kept as toolchain inputs."""
    source = commands[role][commands[role].index('-lsandbox') - 1]
    listing = run(['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', *flags, '-MM', source])
    if listing['returncode'] != 0:
        problems.append(f'{role}: dependency listing failed'); return listing, [], []
    text = listing['stdout'].replace('\\\n', ' ')
    listed = {Path(p).resolve() for p in text.split(':', 1)[1].split()}
    from_sdk = sorted(str(p) for p in listed if sdk and p.is_relative_to(sdk))
    paths = sorted(relative(p) for p in listed if not (sdk and p.is_relative_to(sdk)))
    outside = [p for p in paths if not (root / p).resolve().is_relative_to(production_dir)
               and not (root / p).resolve().is_relative_to(fixture_dir)]
    if outside: problems.append(f'{role}: inputs outside the worker and fixture directories and the SDK: {outside}')
    return listing, paths, from_sdk


def seam_sites(paths):
    sites = {name: [] for name in SEAMS}
    for path in paths:
        if not (root / path).resolve().is_relative_to(production_dir): continue
        for number, line in enumerate((root / path).read_text().splitlines(), 1):
            if line.lstrip().startswith('#'): continue
            for name in SEAMS:
                if re.search(r'\b' + name + r'\(', line): sites[name].append(f'{path}:{number}: {line.strip()}')
    for name, expected in SEAMS.items():
        if len(sites[name]) != expected:
            problems.append(f'seam {name}: expected {expected} production call site(s), found {len(sites[name])}')
    return sites


def declared_identity():
    abi = (production_dir / 'pw_probe_runner_abi.h').read_text()
    contract = (root / 'tests/lib/contract.py').read_text()
    header = re.search(r'#define PW_WORKER_ABI_IDENTITY_HEX "([0-9a-f]{64})"', abi)
    tests = re.search(r'^WORKER_IDENTITY = "([0-9a-f]{64})"$', contract, re.M)
    value = dict(abi_header=header and header.group(1), tests_lib_contract=tests and tests.group(1))
    if not header or not tests or header.group(1) != tests.group(1):
        problems.append(f'declared identities disagree or are missing: {value}')
    return value


def output_record(role, identity):
    path = out / f'pw-probe-runner-{role}'
    st = path.stat()
    warm = run([path], stdin=subprocess.DEVNULL)
    version = run([path, '--version'], stdin=subprocess.DEVNULL)
    if warm['returncode'] != 2: problems.append(f'{role}: warm execution rc={warm["returncode"]}, expected 2')
    reported = re.search(r'\babi_identity=([0-9a-f]{64})\b', version['stdout'] or '')
    if version['returncode'] != 0 or not reported:
        problems.append(f'{role}: --version reported no identity (rc={version["returncode"]})')
    elif reported.group(1) != identity['abi_header']:
        problems.append(f'{role}: --version reports {reported.group(1)}, source declares {identity["abi_header"]}')
    print(f'warm {path.name}: rc={warm["returncode"]} {warm["elapsed_ms"]} ms')
    return dict(path=str(path), command=commands[role], sha256=digest(path), size=st.st_size,
                st_dev=st.st_dev, st_ino=st.st_ino, mode=oct(st.st_mode & 0o7777),
                warm=warm, version=version, reported_identity=reported and reported.group(1))


identity = declared_identity()
toolchain = dict(clang=run(['/usr/bin/xcrun', '--sdk', 'macosx', '--find', 'clang']),
                 clang_version=run(['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '--version']),
                 sdk_path=run(['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-path']),
                 sdk_version=run(['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-version']),
                 sdkroot_environment=os.environ.get('SDKROOT'),
                 developer_dir_environment=os.environ.get('DEVELOPER_DIR'))
sdk = toolchain['sdk_path']['stdout'].strip() if toolchain['sdk_path']['returncode'] == 0 else ''
sdk = Path(sdk).resolve() if sdk else None
if not sdk: problems.append('the macosx SDK path is unavailable')
listings, inputs, sdk_inputs = {}, {}, {}
for role in ('stamps', 'plain'):
    listings[role], inputs[role], sdk_inputs[role] = dependencies(role, sdk)
if inputs['plain'] and any(p.startswith('tests/') for p in inputs['plain']):
    problems.append('plain: the uninstrumented twin read fixture sources')
sites = seam_sites(inputs['stamps'])
outputs = {role: output_record(role, identity) for role in ('stamps', 'plain')}
receipt = dict(
    version=1, kind='worker_wait_stamp_worker_build', root=str(root), ok=not problems, problems=problems,
    flags=flags, toolchain=toolchain, declared_identity=identity,
    inputs={role: {p: digest(root / p) for p in paths} for role, paths in inputs.items()},
    sdk_inputs={role: {p: digest(p) for p in paths} for role, paths in sdk_inputs.items()},
    recipe_inputs={relative(p): digest(p) for p in (fixture_dir / 'build.sh',)},
    dependency_listings=listings, seams=sites, outputs=outputs,
    provenance=dict(
        stamps=dict(provenance_kind='substitution', identity_is_fixture_source_digest=False,
                    note='The stamp worker reports the production ABI identity because that identity digests '
                         'production sources only; it does not describe the stamp wrapper. Actual bytes and '
                         'substitution provenance remain separate. It is not the production worker.'),
        plain=dict(provenance_kind='fixture_recipe', identity_is_fixture_source_digest=False,
                   note='Unmodified production source compiled by this recipe, not by Meson; its bytes are '
                        'not established to equal the distributed worker.')))
temporary = out / '.worker-build.json.tmp'
temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
os.replace(temporary, out / 'worker-build.json')
for problem in problems: print('build refused: ' + problem)
sys.exit(1 if problems else 0)
PY
