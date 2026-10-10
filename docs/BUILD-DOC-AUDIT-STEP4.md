# Audit prompt: read the build document against the build

You are reading [BUILD.md](BUILD.md), the account of how this repository
builds and signs `PolicyWitness.app`, against the files it describes. You
are given the document and the build, nothing else: do not read
`docs/BUILD-DOC-PLAN.md`, `docs/BUILD-DOC-AUDIT-STEP1.md` or anything under
`records/`, and do not consult the plan's register. Your value is a reading
the authors did not shape. Like the document's plan, this file and your
report are working material: nothing links them and they are deleted later.

## What to read

1. `docs/BUILD.md` in full, including the generated figure and the six
   tables, which come from `docs/build.json` through `docs/generate_build.py`.
2. The build: `build.sh`, `meson.build`, `meson.options`, the `Makefile`
   (its `build` target and whatever calls it), `controller/build.rs`,
   `Info.plist` and `runner/Services/PWRunner/Info.plist`.
3. The helpers the script runs, when a claim depends on one:
   `tests/lib/native_sources.py`, `tests/lib/signer_check.py`,
   `tests/build-evidence.py`, and the generators under `docs/`.
4. The controls the document cites, when a row claims a control produces a
   refusal: `tests/suites/source_drift/contract.py`, `limits.py`,
   `build.py`, `build_rules.py`, `check_planner.py`, and
   `tests/suites/preflight/check_signed_artifacts.py`.

## How to read

Read in both directions. First, for each consequential claim in the prose
and each row in the tables, find the line of the build that implements it
and the assertion that covers it, and say whether the claim is what that
line does, more than it does, or less. A citation is a place to look, not
proof; read what the cited test asserts. Second, walk the build forward from
`make build` through every branch of `build.sh`, every operation, every
input from outside the tree, every write, every refusal and every warning,
and name what the document omits or misplaces.

Challenge the universal words. Wherever the document says "every", "before",
"only", "never" or "nothing", ask whether it holds in a partial build
(`BUILD_XPC=0`), in an inspection-off build (`PW_INSPECTION=0`), with a
reused build directory, with a reused Cargo target directory, in a copied
checkout, and when a tool rather than the script refuses. Where the document
says a refusal precedes an operation, ask what establishes that: the text's
order, a control that drives the build, or nothing.

Distinguish three things in your findings: a sentence that is wrong about
what the build does; a build behavior that is a defect against the promise
the document makes for it; and a guarantee the document claims that nothing
establishes. Say which, and for the second and third say what observation
would settle it. Do not propose wording for the document and do not change
any file other than your report.

## What you may do

Read anything the first section names. You may run `build.sh` in a disposable
copy of the checkout under `.tmp/` with `DIST_DIR` under `.tmp/`, never
against the repository's own `dist/` or `builddir/`; builds need
`PATH=/opt/homebrew/opt/rustup/bin:$PATH` for Cargo and an explicit
`IDENTITY` naming the Developer ID Application identity that
`security find-identity -v -p codesigning` lists. If a keychain prompt
appears, stop and report. You may run `tests/run.sh --suite source_drift`
into a fresh `PW_TEST_OUT_DIR=tests/out/runs/build-doc-audit4-<name>`, one
battery at a time. Never notarize, release or publish, and do not commit.

## Report

Write `docs/BUILD-DOC-AUDIT-STEP4-REPORT.md`, uncommitted, with:

1. **What you read and ran**, with paths and any command's log location.
2. **Claims that are wrong**, each with the sentence or row, the line of the
   build it misdescribes, and what the build actually does.
3. **Omissions and misplacements** from the forward walk, each with the
   script line and the section that should hold it.
4. **Guarantees nothing establishes**, each with the sentence, what the
   cited check actually asserts, and the observation that would establish or
   refute it.
5. **Build behaviors that look like defects** against the document's own
   promises, each with the promise quoted, the line, and the observation
   that would confirm it; say plainly when you could not observe it.
6. **What held up**: the universal claims you tried to break and could not,
   with what you tried.

One paragraph per finding. The reader is deciding what to fix and what to
rewrite, not reading a narrative.
