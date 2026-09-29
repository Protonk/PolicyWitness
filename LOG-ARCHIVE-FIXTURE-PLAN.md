# Isolated archive fixture

Status: The available remote test Mac runs macOS 26.2. Use that host for
generation; no 14.8.3 VM is required up front. The development machine runs
14.8.3 and has no disposable environment. This is the external prerequisite for the query-selection claims in
[BEST-EFFORT-LOG-PLAN.md](BEST-EFFORT-LOG-PLAN.md), sections 2 and 4.

## Deliverable

Produce `tests/fixtures/deny_capture/query_predicate.logarchive`, a small,
self-contained archive readable by `/usr/bin/log show`, together with an
independent `query_predicate.json` expectation manifest and fixture README.
Include every required archive metadata file and per-file SHA-256 hashes.
Saved JSON/syslog text is not a substitute. Never collect or commit the ambient
development machine's log store.

## Generation on the isolated host

1. On the macOS 26.2 host, record the clean host's version/build, architecture and the exact
   generation commands. Use a temporary, isolated test environment containing
   no personal/account data. Privileged archive collection is a one-time
   maintenance action; it is not default-test setup.
2. Declare the message corpus and expectations before emission. Use fixed
   embedded worker names/PIDs, at least two queries, and unique public message
   markers. Include `Sandbox: worker(pid) deny(n) operation target` records for
   every supported message form, paths with spaces, and duplicate messages to
   test multiplicity. The actual emitting process must have a different PID
   from the embedded worker PID. User-space `os_log` messages are sufficient;
   the fixture tests query selection, not kernel emission or authenticity.
3. Include negative messages with another worker name, a neighbouring PID, a
   longer PID containing the requested digits, and those digits only in a path
   or unrelated deny text. Specify the exact selected message multiset and
   expected parsed deny events independently of PW's predicate and parser.
4. Emit the declared corpus with public text and collect a short bounded
   archive using the isolated host's supported `log collect` command. Record
   UTC query bounds independently of the message paths. Inspect the archive
   without the predicate under test: every corpus record and its multiplicity
   must be present. Inspect all other retained content before transferring it.
   If the capture is incomplete, retain the failed generation receipt and
   investigate; do not silently revise expectations to the captured subset.
5. Transfer the inspected archive, corpus/manifest, source emitter, recipe,
   source OS information and hashes back to this checkout. Do not strip files
   from the archive unless a fresh read proves it remains self-contained.

## Acceptance in this checkout

- Verify hashes and first run the reader acceptance on the producing 26.2 host.
  Transfer the same inspected bytes and run acceptance on the development
  machine's 14.8.3 reader. Record producer and reader versions separately.
  Archive compatibility is an acceptance question, not an assumption.
- If 14.8.3 cannot read the 26.2 archive, retain that failure and its exact
  diagnostics. A 26.2 pass establishes only that reader's behavior. The fallback
  is generation in a disposable 14.8.3 VM on the remote host (if practical),
  followed by acceptance on both readers. Do not mask incompatibility with a
  skip, replace the archive with saved text, or claim older-reader coverage.
  If no compatible fixture can be secured, this dependency stays open.
- Run the required `witness_contract/log_query_predicate_archive` case using
  the production command builder with only the archive and manifest query
  inputs substituted. It must first recover the complete unfiltered corpus,
  then compare selected messages/multiplicities before PW parsing, and finally
  compare production parser output with independent expected events.
- Require the nonempty positive selection and all negative exclusions. Prove
  that `FALSEPREDICATE` and the old bare-PID-digit alternative each fail, then
  restore production code. Preserve both query arguments, exits and bounded
  raw outputs for every run, including failures.
- Missing/unreadable data, blocked access, timeout, overflow, nonzero exit and
  wrong/empty selection fail this case. Use the repository's sandboxed-harness
  rerun procedure for a tool refusal; none of these outcomes is a live
  availability skip. No default test may emit new logs, collect an archive,
  download data or consult the current store to repair the fixture.

Until acceptance passes, predicate behavior through the real OS engine is
unvalidated. Parser controls, bounded subprocess fixtures and argv assertions
remain useful but cannot discharge this dependency. Permanent fixture docs and
tests must be usable after both plan files are removed.
