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
