# Plan: what pytest family evidence costs to store and to read

This is an outline. Parts 1 and 2 are a direction already wanted: carry them
out, and decide the routine details yourself. Part 3 is a question to answer
in writing before anything is built for it.

## What was reported

Three related costs were reported for [pytest families](README.md#pytest-families)
whose items declare a command scope. Read them as reports of size and cause.
The magnitudes are rough and were estimated once; the direction below does not
depend on their exact values. Do not re-measure them before starting, and do
not run a battery to confirm them: each cause is visible in the source named
here, and each part states a small check of its own.

- **Stored bytes grow as items times collected sources.**
  [`pytest_runtest_logstart`](lib/pytest_engine.py) gives every item its own
  [`InputRecorder`](lib/receipts.py), whose [`Control`](lib/receipts.py)
  keeps a `blobs/` store beside that item's record, and first copies every
  collected source into it. A family with a few hundred items and about half
  a megabyte of collected sources stores on the order of a hundred megabytes
  in several thousand files, of which a few megabytes are distinct content.
- **Every reader reads everything, repeatedly.** After each phase
  [`pytest_runtest_makereport`](lib/pytest_engine.py) writes the full list
  from [`references`](lib/receipts.py) into the phase row.
  [`validate_inputs`](lib/pytest_family.py) reads and hashes every reference
  of every phase, and [`problems`](lib/execution_contract.py) reaches it twice
  for each family, through `validate_family` and through `_family_raw`. From a
  directory this is quick.
- **From a release archive it is not.** [`verify_bundle`](lib/release_runs.py)
  serves each of those reads as one member of `runs.tar.gz`. A gzip stream
  cannot move backward, so each read that lies before the previous one
  inflates the archive again from its start, and a family's validation makes
  several such reads per item. The estimate for one large family in a
  battery-sized archive is tens of minutes for one verification, where the
  rest of the archive takes seconds. `verify_bundle` runs from
  [`pack`](lib/release_runs.py), from [`verify_release`](lib/release_runs.py)
  at archive and publish, and through [`archives`](lib/retention.py) for
  every archive on every prune plan. It first matters at the next release
  whose battery includes such a family.

## 1. Read archived family evidence in one pass

Wanted: verifying a bundle costs about one pass over the archive, however
often validation asks for a member and in whatever order.

Within one `verify_bundle` call, serve reads from bytes obtained in archive
order: load the members under each required family's directory in one forward
pass before validation, or remember members by name and avoid reading
backward. The forward pass leaves no backward reads; choose between them.

Hold these fixed. The bundle format, its manifest and the archived producer
contract do not change, and existing archives verify as they do now.
[`verify_transport`](lib/release_runs.py) still hashes every member against
the inventory. Bytes come only from the archive being verified. A missing or
changed member is refused with the diagnostic it has today.

Check it with a constructed bundle; the dispatcher's pytest controls already
build and verify one ([pytest_outcomes.py](suites/dispatcher/pytest_outcomes.py),
[pytest_integration.py](suites/dispatcher/pytest_integration.py)). Count
backward reads of the underlying stream and require that the count does not
grow with items or phases. Assert a count, not a duration. Keep a rejected
neighbour: the same bundle with one family member altered, and with one
removed.

## 2. Keep one blob store per family

Wanted: each distinct content is stored once per family, under
`artifacts/inputs/`. Per-item snapshot records stay as they are.

Give the recorder its store location. Other users of `Control`, the unittest
receipts of the drift and preflight cases, keep one store per receipts file;
this part stops at the pytest recorder.

- A snapshot records each blob's path relative to `artifacts/inputs/`, and
  both `validate_inputs` and `references` follow the recorded path. By
  reading, the validators accept either layout. Archived evidence with
  per-item stores must keep verifying: establish both layouts with a
  constructed family instead of assuming it.
- [`blob`](lib/receipts.py) skips a name that already exists. With a shared
  store, a file left partly written by one item would be reused by later
  items. Write under a temporary name and rename.
- A missing or altered shared blob invalidates every item that references it.
  That is the correct reading. Add a control that removes one shared blob and
  requires each referencing item to be refused.
- Correct the accounts that say blobs are kept per item: the
  [Markdown reader](suites/source_drift/README.md#markdown-reader) and
  [worker-wait pilot controls](suites/witness_contract/README.md#worker-wait-pilot-controls)
  sections.

This part does not shorten reference lists or reduce reads; part 1 is needed
with or without it. Check it on one run of each family that declares command
scopes: every snapshot's blob paths resolve, no content is stored twice, and
validation accepts. Assert uniqueness, not a size.

## 3. Question: what does capturing sources for every item give us?

A possible third step would capture the collected sources once per family and
let items refer to that capture, which would remove most references and most
reads. Do not build it. Answer this first: if we did, what would we actually
lose?

1. What can a reader conclude from a capture at each item's start that one
   capture at session start, with the comparison
   [`pytest_sessionfinish`](lib/pytest_engine.py) already records and
   [`account`](lib/pytest_family.py) already reads, would not support?
   Consider a source that changes between items, one that changes and is
   restored within a session, and knowing which items preceded a change. The
   capture reads files from disk at item start; pytest imported the modules at
   collection. The recorder's own account says snapshots do not prove use.
2. Is that a capacity nothing exercises, or something tested now? Take each
   refusal in `validate_inputs` and the source-integrity branch of `account`
   and find the check that produces it, constructed or live. A first reading
   found one control that deletes a referenced input file and none that
   changes a collected source, substitutes a captured source blob or omits the
   source snapshot from a phase. Confirm or correct that.
3. Where a check exists, is it cogent? Establish whether it fails for the
   stated reason or for an earlier one: a deleted file is refused by
   [`validate_evidence`](lib/outcomes.py) before any source comparison runs.
   Establish whether it would still pass with the per-item relation removed.
4. Does any account or acceptance reader rely on per-item source identity,
   including the rules for [reusing evidence](AGENTS.md#evaluate-and-reuse-evidence)?

Answer with source reading and, where a branch needs showing, a small
constructed input. Report one of three results and what follows from it: the
capacity is untested, so either test it or drop it; it is tested by cogent
checks, so it stays and its cost is stated; or it is tested by checks that do
not establish it, so repair those before deciding.

## Verification and where this stops

Route each change through
[Observation and reporting readers](CHANGE-VERIFICATION.md#observation-and-reporting-readers).
The checks named in each part are constructed and small. Neither part needs a
default battery to show its effect: for part 1 it is a read count on a
constructed bundle, for part 2 a file layout in one family's output.

Out of scope: the bundle format and schema versions, the unittest receipts,
repeated fixture content in other cases, and any implementation of part 3.
Reconsider part 2 if a reader turns out not to follow the recorded blob path,
since both layouts would then need explicit handling.
