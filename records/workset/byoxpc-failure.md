# F2: required BYOXPC verification remains incomplete

Examined source: `fd90eee66538cc02dc5d21b7a3fe8eca81a17403`; signed app
v0.3.3 build 1000; worker identity
`f477a8488d3f96715e987f7014dcd0aa76ba53b70575118e20ef238b600d4094`.
Primary investigation and independent read-only review by
`review_public_extension` agree on the observations below. The cause and repair
are unresolved. No expectation, automatic retry or production repair was made.

## Expected and observed

The required `witness_contract/extensions_byoxpc` case installs its own signed
service and repeats extension and ordinary-phase workloads through the public
CLI, then verifies authority, missing-issuer behavior and cleanup. Successful
subcases require execution evidence and independent effects. A transport error
cannot replace those observations.

| Run | Observation |
| --- | --- |
| `workset-r2-final-01`, `20261029T231443Z_9c34b030` | Of 207 selected cases, 205 passed. BYOXPC failed at `extensions/consume_only`; client PID 22345 received NSCocoaErrorDomain 4097, with no host/worker receipt. The other failure was a separately corrected contract citation. |
| `workset-r2-byoxpc-02`, `20261029T232845Z_044d37dc` | One unchanged diagnostic rerun failed at `directory/no_predicate-baseline`. The previous failing consume-only subcase passed. Client PID 23754 received 4097 under allow-default without an extension declaration. |

Both runs were outside the automation sandbox, on unchanged source and app
bytes, with no observed sleep, capture timeout or JSON error. Local request
writes completed; acquisition history is empty; no runner_subprocess is present.
The error PID is the client, not a witnessed host or worker PID. Fallback SBPL
compilation and unchanged external files establish neither execution nor exit.
The full first run lasted 803.162 seconds; the rerun lasted 25.969 seconds.
Both failed runs and their app inventories are pinned in tests/RETAINED.json;
raw output is local/gitignored under tests/out/runs, not recoverable from git.

Preceding successful calls exercised already_ran, observed retirement and fresh
acquisition. The failing calls began about 68/72 ms after the prior client
completed, near the unchanged 50 ms host retirement scheduling. This supports
a handoff hypothesis only. No generation/exit/crash evidence assigns a cause.
Service, client and controller acquisition implementations match Stage 1; exact
extraction and other passing controls do not rule out an execution problem.
No previous passing BYOXPC result is substituted for this changed candidate's
required verification. A baseline comparison or focused lifecycle investigation
could distinguish causes, but selecting a behavioral repair requires the user's
participation under WORKSET-PLAN's defect boundary.

## Ownership and cleanup

The first service was
`com.policywitness.test.byoxpc.s9bc86444c4142259b7c736b1`, bundle
`/private/tmp/pw-byoxpc-u_m1u4ur/PWRunner.xpc`. The rerun service was
`com.policywitness.test.byoxpc.sc9e8d53cfcbb42d7a0a64927`, bundle
`/private/tmp/pw-byoxpc-c3plrmtu/PWRunner.xpc`. Both were user-scope test installs
owned by their case's artifacts/session.json. Their supported finalizers
record removed=true, removal/registry/launchd checks, and source integrity.
Post-run default runner list and reconcile have no runners, pending cleanup,
records, candidates or inspection errors. No service is intentionally retained.

The rerun directory fixture is separate from service staging:
`/private/tmp/pw-extension-directory-uge3532e`. Its ownership.json and the
case's artifacts/directory/{ownership,cleanup}.json retain the exact ownership
and every attempt. Only no_predicate-baseline lacks a worker-exit witness.
The fixture correctly retained its targets and reports removed=false. Preserve
it and the pinned run until that execution's absence/exit can be established
through supported recovery; a label prefix, empty registry or unchanged target
contents does not by itself supply the missing worker observation.

## Disposition boundary

F2 blocks Swift Stage 2 acceptance, the combined refactor seal and workset
completion. F1 independently remains unresolved at the user's explicit request.
Do not weaken either guarantee, add retries to turn the workload green, claim
an environmental explanation, or silently accept missing BYOXPC evidence.
All independent citation corrections and their checks are completed separately.

The subsequent bounded investigation and user-authorized reservation repair
are accepted in f2-reservation-design.md. Combined verification now covers the
required BYOXPC workload and independent reply-loss/no-replay controls, resolving
F2's stage-acceptance blocker. This does not attribute either original failure or
supply the missing original worker-exit witness. That directory and its evidence
remain protected. F1 remains unresolved by the user's explicit decision.
