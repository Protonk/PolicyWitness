# Bound the host wait for worker policy transfer

Preferred solution: give policy delivery its own monotonic deadline and use
nonblocking writes to the worker's policy pipe. When delivery cannot finish
within that budget, close the pipe and enter the host's child-cleanup path,
preserving partial transfer and process evidence. Keep readiness, validator
collection and sentinel polling as separate phases.

Status: resolved and validated 2026-10-06. Real stalled/draining pipes, deadline edge cases, failed cleanup, and actual driver replies through Rust/Python readers pass under response schema 15.
The final default battery passed 165/165 with no skips. The proposal and
diagnosis below preserve the investigation’s original grounding.

**Proposed change**

1. Make the host's policy write endpoint nonblocking before delivery. Start
   one absolute deadline immediately after successful spawn, before the first
   write. Refuse delivery if nonblocking setup fails; never fall back to a
   blocking write.
2. Account for partial writes and wait for writable readiness using only the
   remaining budget. Check the deadline across interrupted calls and partial
   progress; neither restarts it. Handle a closed pipe or zero-progress write
   explicitly. Preserve the existing protection against `SIGPIPE`.
3. On timeout or write failure, close the write endpoint, skip normal ready
   and sentinel polling, and enter the existing exit-request, grace and
   termination sequence. Keep worker publications and actual reap/kill
   observations, including `execution_may_continue` when appropriate.
4. Record deadline exhaustion as a host observation, distinct from an errno
   returned by `write`. Retain the number of bytes accepted by successful
   writes and the expected count; those counts do not establish what the
   child read. The current `policy_transfer_error.errno` contract requires a
   failed syscall, so a timeout needs an explicit representation and the
   corresponding contract, reader and golden updates. Do not manufacture a
   write errno to fit the existing shape.

Use an internal transfer-budget setting with a documented production default
and a short value available to driver tests. A new CLI flag is unnecessary.
This bounds policy delivery; the existing blocking final reap still prevents
a guarantee that the entire host lifecycle finishes by a fixed deadline.

**Problem and grounding**

In [CWorker.swift](../runner/Sources/PWRunnerCore/CWorker.swift), `runCWorker`
spawns the worker, then loops over blocking `Darwin.write` calls until the
policy is sent or a write fails. Only afterward does it start the
`readyByteTimeoutMs` polling loop, followed by sentinel polling. If the child
keeps its input open without draining it and the policy exceeds the pipe's
capacity, the host can remain in delivery without reaching either budget or
its cleanup sequence.

The [client](../runner/Clients/PWRunnerClient/main.swift) can time out and
return `xpc_timeout`, but that path sends no cancellation to the host. Existing
[worker evidence tests](../runner/Tests/PWRunnerCoreTests/WorkerEvidenceTests.swift)
cover closed input and `EPIPE`; an open, stalled reader exercises a different
failure. Transfer-field semantics are in the
[failure evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md).

**Reproduction and validation**

- Use a test-owned worker fixture that keeps stdin open without reading it.
  Send an admitted policy larger than the pipe's capacity, with short ready
  and sentinel budgets. Observe delivery remaining active beyond both
  nominal durations. Run this control under an independent watchdog that
  owns cleanup of the driver and child; neither PW timer covers the stall.
  The existing pre-ready hang override is unsuitable: it delays the real
  worker after policy consumption and compilation.
- After the change, require transfer timeout to initiate cleanup within its
  own budget, preserve write counts and independent process observations,
  and run no validator or attempts. Verify a draining reader still receives
  the complete policy, including through partial writes.
- Exercise repeated interruptions, slow progress, early pipe closure and
  cleanup failure. Progress must not extend the total delivery budget, and
  cleanup failure must not erase the transfer observation or imply a reap.
