# Deny-capture fixtures

`observer.py` supplies independently timed events for window/receiver replay.
It does not model kernel emission or prove OS query selection.

The required archive control reads `query_predicate.logarchive` with the real
`/usr/bin/log show` engine and the production predicate and command builder.
The archive and its independent `query_predicate.json` manifest are required
equipment; absence fails the case. Generation is a maintenance operation on an
isolated disposable macOS host, never default-test setup. An ambient developer
log store, JSON export or saved syslog text is not a substitute.

The manifest has this schema:

```json
{
  "schema_version": 1,
  "message_marker": "PWQP:",
  "emitting_pid": 900,
  "window": {"start": "UTC start accepted by log show", "end": "UTC end"},
  "messages": ["complete declared message inventory, with duplicates"],
  "queries": [{
    "name": "query_name",
    "pid": 42,
    "process_name": "pw-probe-runner",
    "start": "UTC start",
    "end": "UTC end",
    "selected_messages": ["exact selected messages, including multiplicities"],
    "deny_events": [{"pid": 42, "process": "pw-probe-runner", "operation": "file-read-data", "path": "/target"}]
  }]
}
```

There must be at least two worker/PID queries, each with nonempty positives,
and an actual emitting PID different from the embedded worker identities.
Every corpus message begins with the unique marker, before its Sandbox text;
the syslog transport prefix is not part of the expected message. Expected
events omit the transport-dependent raw line; production events retain it.
Selected messages and events are compared as multisets before PID/candidate
filtering. Corpus declarations, not PW output, determine expectations.

Include ordinary and multiple-space/tab-separated Sandbox worker tokens, paths
with spaces, and negatives containing another worker name, a neighbouring or
longer PID, or the requested digits only in a path or unrelated deny text.
Before transferring the archive, inspect its unfiltered content, confirm every
declared record, and review all other retained material. Preserve all required
metadata, source emitter, exact generation recipe, source macOS version/build,
verified reader versions and SHA-256 hashes for every archive file here.

The registered case retains unfiltered and production-query argv, exit/wait and
cleanup facts, raw stdout/stderr and byte/deadline observations. It uses a fixed
10-second allowance, a 1-second cleanup grace, 1 MiB stdout and 128 KiB stderr.
Missing/unreadable archive data, blocked tool access, nonzero exit, timeout,
overflow and wrong/empty selection fail. Apply the documented sandboxed-harness
rerun procedure for tool refusal. Neither parser replay nor argv assertions
replace the required OS query. Regeneration must not respond automatically to a
failed assertion or revise the expected corpus to a captured subset.

Archive production and reader compatibility are separate observations. Record
the producer OS/build and every reader OS/build tested. A fixture generated on
26.2 must pass the same acceptance on a 14.8.3 reader before claiming that
compatibility. An unreadable archive fails the required case; it is not skipped.

## Generated fixture

`query_predicate.logarchive` and `query_predicate.json` were produced on
2026-09-29 by the recipe in `generation/generate.sh` with the corpus declared in
`make_manifest.py` (26 messages: 11 select for `pw-probe-runner(42)`, 3 for
`pw-probe-runner(7)`, 12 select for neither; `generation/corpus.lines` is the
emitted text with literal tabs). The manifest's selections and deny events are
derived by that script from the documented message contract, not from PW output.

- Producer: an isolated macOS 14.8.7 (23J520) guest,
  `VirtualMac2,1` under UTM 4.7.5 / Virtualization.framework on a macOS 26.6.2
  (25G83) host, fresh install with one throwaway `admin` account and no
  personal data. `generation/sw_vers.txt`, `generation/uname.txt`.
- Emitter: `emitter/pwqp_emit.c`, built on the host for macOS 14
  (SHA-256 `81311c16…3cbe`, Mach-O UUID `3C223CCA-74EE-3FA5-B62C-44587A1C50B3`);
  it logs each corpus line verbatim and public under
  `com.policywitness.fixture:query_predicate` at default level from PID 522
  (`generation/emitter.out`, `generation/record.json`). Producer `/usr/bin/log`
  SHA-256 `91ec8d27…daef` (`generation/inputs.sha256`).
- Window: `2026-09-29 06:12:03+0000` to `06:12:11+0000` (UTC, whole seconds,
  one second before and three after emission); `log collect --start` bounded
  the archive to that window (8005 records, 1295 in the window).
- Inspection before transfer: the unfiltered window query rendered exactly the
  declared corpus multiset (tabs, double spaces and quotes intact); the full
  dump holds only fresh-VM daemon chatter (opendirectoryd, syspolicyd, launchd,
  sshd for the generating SSH session, bluetoothd), the guest user name `admin`,
  the vmnet addresses 192.168.64.1/2, and the public-key fingerprint of the
  throwaway host key used for that session. No credentials, hostnames, or
  account data.
- Reduction: `log collect` wrote 232 files (127 MB), 113.7 MB of it one
  shared-cache format table under `dsc/`, above GitHub's per-file limit. The
  committed archive keeps only what the declared corpus needs: `Info.plist`,
  `Persist/` (the corpus records), `logdata.LiveData.tracev3`, `timesync/` and
  the emitter's own format-string entry `3C/`; `dsc/`, every other process's
  uuidtext entry, `Extra/` and `Special/` were removed after collection (6
  files, 1.6 MB). `generation/full-archive.SHA256SUMS` lists the unreduced set;
  the unreduced archive is retained outside git as
  `query_predicate-full-14.8.7-2026-09-29.logarchive.tar.gz`
  (SHA-256 `1788c0ed…2c1`). Other processes' records in the reduced archive are
  not renderable; the fixture never claimed them.
- Hashes: `query_predicate.logarchive.SHA256SUMS` (the committed 6 files),
  verified after transfer to and from the producer.
- Readers verified, on the reduced archive as committed: macOS 26.6.2 25G83
  (`/usr/bin/log` SHA-256 `2fa7b046…5974`): the registered case passes, and
  both required mutation controls fail (`FALSEPREDICATE`; `CONTAINS "Sandbox:"
  AND CONTAINS "<pid>"`, which admits 19 rows for worker 42 instead of 11).
  macOS 14.8.7 23J520 (the producer): the same three production argv
  (`unfiltered`, `worker_42`, `worker_7`) return the identical corpus multiset
  and selected rows with no reader diagnostics; the registered case itself has
  not run there (no toolchain in the guest). Acceptance on a 14.8.3 reader
  remains to be recorded.
