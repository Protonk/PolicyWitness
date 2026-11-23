# Plan: what pytest family evidence costs to store and to read

Parts 1 and 2 are accepted for implementation. Read an archive in order and
store each distinct source blob once per family. Keep observing sources at
each item's start and checking the item against collection. This preserves
the evidence used on a shared machine. The changes can land independently
of the 0.3.8 guide review or the next release number.

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

Within one `verify_bundle` call, obtain the required family evidence in
archive order and serve repeated member requests from those bytes. The
number of backward reads must stay bounded as items and phases are added.
Keep reuse local to the opened archive. A same-named member read during
another verification says nothing about this copy.

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

Store each distinct blob once per family under `artifacts/inputs/`. Keep
the snapshot and digest references for every item, including repeated
observations of identical bytes.

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

## 3. Defer changing when sources are observed

Suppose collection sees file A, item 80 starts while a colleague's edit B is
on disk, and the file is back at A at session finish. Both endpoint digests
agree. Today's item snapshot can still expose B. With intact references and
valid blobs, `validate_inputs` refuses the mismatch with collection. This
establishes what was on disk at item start. Pytest may already have imported
the module. A missing blob exercises an earlier evidence check and cannot
stand in for this case. [Item capture](lib/pytest_engine.py) · [Family reader](lib/pytest_family.py)

Keep per-item capture. Reopen family-wide sampling only when someone can
name an actual decision about crediting or reusing an affected result and
explain how each layout would support it. If that decision needs a control,
use one constructed A/B/A case with valid hashes and check the specific
source-mismatch diagnostic. [Evidence reuse](AGENTS.md#evaluate-and-reuse-evidence)

## Verification and where this stops

Route each change through
[Observation and reporting readers](CHANGE-VERIFICATION.md#observation-and-reporting-readers).
Use the constructed bundle for the read count and the damaged-member
refusals. For storage, inspect one run each of the Markdown reader and
worker-wait pilot families. These checks establish the change without an
extra default battery or a loop over release builds.

Out of scope: the bundle format and schema versions, the unittest receipts,
repeated fixture content in other cases, and any implementation of part 3.
Reconsider part 2 if a reader turns out not to follow the recorded blob path,
since both layouts would then need explicit handling.
