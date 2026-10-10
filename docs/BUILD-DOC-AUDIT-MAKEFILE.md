# Audit prompt: the Makefile as the boundary object

Four parts, all carried out in a disposable copy of this checkout and written
up in one report. The Makefile is meant to be the thin layer a person or an
agent types at before reading anything: six verbs, a header that documents
them, and no build or release logic of its own. We want to know what contract
those verbs imply, whether they can be trusted under the conditions a
newcomer meets here, what the shortest Makefile that keeps that contract
looks like, and, with prudence set aside for one part, what a bolder
Makefile could be.

You come to the repository as a newcomer who runs before reading. Do not read
`docs/BUILD-DOC-PLAN.md`, anything under `records/`, or anything under
`.tmp/` except the tracked policy file `.tmp/AGENTS.md`, which the copy
needs, and your own report. Like the plan, this prompt and your report are
working material: nothing links them and they are deleted later.

## Setup

Copy the working tree, not a clone of a commit, because the tree holds
uncommitted work. The exclusions drop build products, scratch and test
output; three tracked files under the excluded directories are copied back
because the build and the drift suite need them:

```sh
mkdir -p .tmp/audit-makefile
rsync -a --exclude 'builddir*' --exclude controller/target --exclude dist \
  --exclude .tmp --exclude tests/out . .tmp/audit-makefile/src/
mkdir -p .tmp/audit-makefile/src/dist .tmp/audit-makefile/src/.tmp
cp -p dist/README.md dist/AGENTS.md .tmp/audit-makefile/src/dist/
cp -p .tmp/AGENTS.md .tmp/audit-makefile/src/.tmp/AGENTS.md
```

Work only inside that copy. Builds need `PATH=/opt/homebrew/opt/rustup/bin:$PATH`
for Cargo and an explicit `IDENTITY` naming the Developer ID Application
identity that `security find-identity -v -p codesigning` lists; signing has
run unattended on this machine, and if a keychain prompt appears, stop and
report. Set `DIST_DIR` under the copy whenever a verb builds. Never run
`build.sh` or `make` against the repository's own `dist/` or `builddir/`;
never notarize, release, publish or commit. The sandboxed-harness note in
SIGNING.md applies: Meson's Swift discovery, the keychain, signature
verification and live XPC can all refuse inside a sandbox, and the remedy is
the same command outside it. The copy has its own checkout lock; run one
battery at a time, and expect `make test` to be the longest thing you do.
When something blocks you, stop and say so rather than inferring permission.

## Part 1: the contract as read

Open the Makefile before any other file. For each verb, and for bare `make`
with no target, write the promise you infer from the file alone: what it
does, what it needs, what it refuses and how, what it writes and where, what
it leaves behind when it fails, and whether you would run it unattended,
inside a harness, or twice in a row. Write this down before you run anything
and before you open `build.sh`, `tests/run.sh` or any document.

Then read what the Makefile points at, then [AGENTS.md](../AGENTS.md), the
[README](../README.md), [BUILD.md](BUILD.md), [SIGNING.md](SIGNING.md) and
the [tests README](../tests/README.md), and record every place the
documents' account of a verb differs from the one you inferred, and every
place the header's own account differs from what its recipe does. As in the
narrative audit, a surprise is any gap between what you expected and what you
found, however small, and each one gets an id, one sentence of belief, one
sentence of observation, and a valence from −2 to +2. Record no diagnosis.

## Part 2: the conditions matrix

Implicit confidence means that whatever the conditions, a verb either keeps
its promise or refuses by naming the condition. Measure that. Exercise bare
`make`, `make build`, `make test` and `make clean` in the copy under the
conditions a newcomer here actually meets:

- inside the harness sandbox and outside it;
- `IDENTITY` set, absent, and set to a name the keychain lacks;
- Cargo on and off the `PATH`;
- `BUILD_XPC=1` and `BUILD_XPC=0`;
- a tree with a stale generated copy (edit a comment in `build.sh` and build
  again);
- a repeated invocation, and an invocation right after a refused one;
- `make test` and `make clean` with no built app, with a built app, and with
  run directories of each kind the pruner distinguishes that you can produce.

For each cell record which of three things happened: the promise held, the
verb refused and named the condition, or something else. The third outcome
is the only kind of finding this audit produces; the other two are the
measurement. Record the time each cell took and the exact message where
there was one. `notarize`, `release` and `publish` are read and reasoned
about but never run; their cells say "designed, not run".

## Part 3: the candidate

Write the Makefile you would want as the boundary object, in the copy. Which
verbs exist, which merge or go, what each refuses before doing partial work,
and how the file documents itself: the header, a verb that prints it, a
section in a document that is checked against it, or something else.
Constraints keep taste out of it: no new generator and no manifest; the
Makefile plus at most one document; fewer lines is better; every promise the
current verbs make must remain reachable somewhere, by make or by the script
it names; and the candidate must pass the matrix of Part 2 at least as well
as the current file. Rerun the cells your changes touch. Report a diff stat,
the essence of the change, the matrix result, and a required section on what
you would not change and why. Keeping the file as built is a valid answer to
this part.

## Part 4: bold, not radical

Set prudence aside for this part only. Parts 1 to 3 reward modifications of
the current design, and a careful auditor will not reach for a change with
large consequences and a small benefit. We want to see those changes anyway,
as design exploration, because the area is narrow enough that exploring it is
cheap and the verbs are the thing people touch first.

Start from what `make` should mean to someone who has never seen this
repository, not from your candidate, and propose three to five changes you
would not have proposed above. For each: the change in a sentence; what it
would make true for a person typing `make`; what it costs, meaning what
moves, what breaks and what has to be rewritten; and what would have to be
true of the project for the change to be worth it. Opinions are welcome and
should be labeled as opinions. A proposal may contradict your candidate.

Bold keeps the Makefile a thin layer and keeps every current promise
reachable somewhere. Radical would replace make, add a build system, or
change what the build does. Two examples of the scale, not assignments: if
`clean` is a pruner, could the pruning move to where it belongs and `clean`
become a cleaner again, even if not `rm -rf`? Could the pruner migrate and
leave no `clean` verb behind at all? Others in the same register: `test`
could take a suite and an output directory and the default battery could be
its own verb; bare `make` could print the header instead of building;
`notarize` could stop being a verb a person types; `build` could split so
that the refusals before any compile are a verb of their own. Do not
implement any of these. A page is enough.

## Report

Write `.tmp/audits/BUILD-DOC-AUDIT-MAKEFILE-REPORT.md` in the original
checkout, uncommitted, the only file you write outside the copy. It lives
under `.tmp/` so that the drift suite's prose scan, which covers every
document under `docs/`, never reads it. Part 1 holds the contract table, the
differences, and the surprises with their valences. Part 2 holds the matrix
with its times and messages. Part 3 holds the diff stat, the candidate's
essence, its matrix result, and what you would not change. Part 4 is
free-form. Keep a log of every action with the expectation written before it
and the outcome after, including dead ends and the time each stretch took; a
short report that leaves them out is worth less than a long one that keeps
them.
