# Audit prompt: a build narrative and a challenge

Two tasks, both carried out in a disposable copy of this checkout and both
written up in one report. You come to the repository as a capable newcomer
would: read [AGENTS.md](../AGENTS.md), the [README](../README.md),
[BUILD.md](BUILD.md), [SIGNING.md](SIGNING.md) and whatever those lead you
to, in whatever order you would naturally take. Do not read
`docs/BUILD-DOC-PLAN.md`, anything under `.tmp/`, or anything under
`records/`. Like the plan, this prompt and your report are working material:
nothing links them and they are deleted later.

## Setup

Copy the working tree, not a clone of a commit, because the tree holds
uncommitted work the documents describe:

```sh
mkdir -p .tmp/audit-narrative
rsync -a --exclude 'builddir*' --exclude controller/target --exclude dist \
  --exclude .tmp --exclude tests/out . .tmp/audit-narrative/src/
```

Work only inside that copy. Builds need `PATH=/opt/homebrew/opt/rustup/bin:$PATH`
for Cargo and an explicit `IDENTITY` naming the Developer ID Application
identity that `security find-identity -v -p codesigning` lists; signing has
run unattended on this machine, and if a keychain prompt appears, stop and
report. Set `DIST_DIR` under the copy. Never run `build.sh` against the
repository's own `dist/` or `builddir/`; never notarize, release, publish or
commit. The sandboxed-harness note in SIGNING.md applies: Meson's Swift
discovery and the keychain can refuse inside a sandbox, and the remedy is the
same command outside it.

## Task 1: the narrative

The task is ordinary maintenance. Add a fourth top-level helper to the app: a
C executable named `pw-stamp` that prints the words `policy witness` and
exits 0. Build it with Meson, embed it under the app's `Contents/MacOS`,
sign it, inventory it, document it where the repository says such things are
documented, and bring these three back to green in the copy, in this order:

1. `make build IDENTITY='…'`
2. `python3 tests/lib/artifact.py <copy>/dist/PolicyWitness.app <copy>/inspection.json`
3. `tests/run.sh --suite source_drift` (from the copy; use a fresh
   `PW_TEST_OUT_DIR` under the copy's `tests/out/runs/`)

Stop there. Do not run the default battery, and do not make the helper do
anything more than print.

Keep a log as you work, from the first file you open to the last green
check, with an entry for every action: the command or the edit, what you
expected before you did it, and what happened. Write the expectation before
the action, not after. Include dead ends and the time each stretch took.

We are after surprises, however small, including pleasant ones. A surprise
is any gap between what you expected and what happened: a check that caught
an omission before you noticed it, a document that already answered the
question you were about to ask, a file you had to edit that nothing pointed
you to, a message that told you exactly what to do, a step that ran in an
order you did not expect, a tool that took longer or shorter than you
assumed. For each surprise record:

- an id and the log entry it belongs to;
- what you believed, in one sentence;
- what you observed, in one sentence;
- a valence from −2 to +2: −2 worse than expected in a way that cost you,
  −1 mildly worse, 0 surprising but neither better nor worse, +1 mildly
  better, +2 better than expected in a way that saved you.

Record no recommendations and no diagnosis of why the system behaves as it
does. The report is the gap and its sign, nothing more. Count the
non-surprises too: the places where you expected a check to catch you and it
did, and the places where you expected to be told what to do and were. Those
calibrate the surprises.

## Task 2: the challenge

Find one thing that is quite clever to do with this build machinery, and do
it. The machinery is `build.sh`, `meson.build` and the Makefile; the parsed
model of the script and its manifest in `docs/generate_build.py` and
`docs/build.json`, with the grounding rules and the baseline; the identity
generator; the evidence manifest; the signer check; the configured-source
check; the native comparison tools under `tests/lib/`; and the drift suite.

It qualifies if it is non-obvious (no document names it as a thing to do),
implementable with relatively few changes (think under a hundred lines, and
fewer is better), and either useful (something we might want to keep) or
fascinating (it shows something about the build that nobody wrote down). It
is not an exploit, not a bypass, and not merely a surprising outcome; it may
well be something we would want. Two examples of the scale, not assignments:
something that turns one real build's output into a statement about that
particular run; something that makes the manifest answer a question none of
the documents can.

Work as follows. List two or three candidates with a sentence each on why it
qualifies and what it would take. Pick one and attempt it in the copy. Report
what you changed (a diff stat and the essence of it), whether it worked, what
it enables, and what it cost in lines and in time. If it did not work, say
what the attempt taught.

## Report

Write `docs/BUILD-DOC-AUDIT-NARRATIVE-REPORT.md`, uncommitted, the only file
you write in the repository. Part 1 holds the log in order, then a table of
the surprises with their valences, then the count of non-surprises. Part 2
holds the candidates, the attempt and its result. Keep the log honest about
time and dead ends; a short log that leaves them out is worth less than a
long one that keeps them.
