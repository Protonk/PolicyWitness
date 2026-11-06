# Footprint reduction outflow

Recorded 2026-11-06. Source revision: `5a2715d24284014be868e6e239a9982079253826`.

Status: deferred investigation, not an execution plan, acceptance gate or release
commitment. The question is which current demands can be reduced while preserving
PW’s observations and claims. [FOOTPRINT](../docs/FOOTPRINT.md) establishes scoped
CPU demand, representation coexistence, backing identity and resource-specific
endings; [LIMITS](../docs/LIMITS.md) supplies the corresponding allowances. Row IDs
below refer to FOOTPRINT. Expected assertion reactions remain unverified until a
later experiment.

| Rows | Demand mechanism | Possible bounded change | Assertions and meaning |
| --- | --- | --- | --- |
| fr8 | Recursive envelope sorting clones complete subtrees while source and destination coexist. | Rebuild sorted maps from owned entries, preserving key order and rendered bytes. | Envelope shape/determinism, error behavior and byte-exact rendering are promises. The clone mechanism is an implementation fact; footprint source wording must change even if scalar boundary assertions still pass. |
| fr6–fr7 | Generic capture is cloned into a typed capture while raw output and decoded host bytes coexist. | Remove one redundant conversion copy while preserving the generic capture retained for diagnostics. | Capture admission, exact retained bytes/counts, invalid producer diagnostics and malformed transport evidence are promises. Current overlap is an implementation fact. Borrowed deserialization should not silently extend buffer lifetimes or weaken admission. |
| fw1–fw2 | Active and parked workers continuously poll protocol words. | Introduce a bounded paced wait, separately from serialization changes. | Collection-before-release, cancellation, continuous-clock expiry, activation, authority delivery and one-shot process lifetimes are promises. CPU ratios are observations. Worker CPU exceeding a sleeping control might still pass after pacing; that assertion is not a guaranteed detector of every blocking wait. |
| fw4–fw5 | Every worker initializes fixed evidence capacity even for a small request. | Investigate right-sized evidence only in a separate ABI change. | Published layout, bound checks, one backing with separate views, profile/slot coverage and failure evidence are promises. Capacity itself is current implementation structure, but changing it crosses ABI/build identity and reader boundaries. Not a small first perturbation. |
| fw6–fw7 | Per-actor authority regions and per-token private buffers are allocated before launch; erased bytes can remain allocated. | Investigate tighter admitted-plan capacities or earlier safe disposal separately. | Custody confinement, source/recipient identity, equality, last-use handling and unresolved-owner erasure rules are promises. Requested logical size, padded object size and physical residency must remain distinct. Do not dispose custody needed by later transfers or inbound bytes needed by repeated consumes. |

A small follow-on should change one mechanism at a time and compare matched
workloads against the same signed baseline. No expected gain, changed assertion
or claim of incidental structure is established by this candidate list alone.

Relevant assertion owners include the [controller boundary test](../controller/src/runner_client.rs)
(`response_footprint_success_boundaries`), [native response checker](../tests/suites/witness_contract/check_response_footprint.py),
[worker proceed and activation controls](../tests/suites/runner_c_worker_harness/run.sh),
[layout agreement](../tests/suites/runner_abi_layout/run.sh), and
[actor custody controls](../runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift).
Read their actual assertions before assigning a sensitivity claim. A failure
identifies a row and promise to inspect; a missing FOOTPRINT or LIMITS citation
does not establish incidental behavior.

Every reduction must preserve the [core ideas](../AGENTS.md#core-ideas): fresh
sandboxed processes, host/worker separation, observations supporting effects,
predictions before attempts, honest attribution and simple runner ownership.
Keep token erasure, native release, unmapping, process exit and reap distinct.
