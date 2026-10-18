# Worker language inventory

Frozen source revision: `2d63c983224907b109b4349d216c03471a8b1f0c`.

This is a descriptive classification of WORKER.md and its direct machinery. It does not assess truth or recommend wording changes. The summary and scope are in `report.md`; original collection and review remain in `first-inventory.json` and `trigger-review.json`. `inventory.json` is the complete machine-readable reconciled record.

A1 states worker behavior, resources or constraints. B1 limits an inference; C2 has an identifiable trigger in WORKER.md and D2 has no identified local trigger. D2 origin status does not establish historical provenance.

Counts are inventory units, with primary classes exclusive. C2 and D2 partition B1. Repeated resource-specific qualifications can occupy separate units; copied manifest/generated occurrences are linked within units.

| Layer | A1 | B1 | C2 within B1 | D2 within B1 | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| WORKER authored | 33 | 24 | 18 | 6 | 57 |
| WORKER generated | 172 | 75 | 24 | 51 | 247 |
| Direct supporting machinery | 0 | 2 | 2 | 0 | 2 |
| Total | 205 | 101 | 44 | 57 | 306 |

## A1 — worker facts and constraints

### WORKER authored

#### N001

[docs/WORKER.md:10–13](../../docs/WORKER.md) · high confidence

```text
The boundary is policy application inside a running process. The executable,
libraries, memory and process context are already present. A fresh worker
applies one specimen once; its later phases share that process and can observe
effects of earlier actions. The unsandboxed host arranges queries, collects
```

**Proposition:** One fresh worker applies one specimen once, with later phases sharing process effects.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: one-way-process.  Independent review: agree; see trigger-review.json by ID.

#### N002

[docs/WORKER.md:43–44](../../docs/WORKER.md) · high confidence

```text
reporting mapping are separate. Validator predictions join host evidence
outside the worker; the host's release ordinal controls admission to attempts.
```

**Proposition:** Predictions remain outside the worker; the worker receives release control.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: evidence-ownership.  Independent review: agree; see trigger-review.json by ID.

#### N006

[docs/WORKER.md:241–247](../../docs/WORKER.md) · high confidence

```text

The worker retains its evidence descriptor as well as the mapping. Its policy
input and readiness descriptors also stay open until exit. Policy EOF ends
source delivery and the host closes its readiness reader after the wait, while
the worker's references remain. Results are published through mapped memory.
The ready pipe serves readiness, and the policy pipe supplies source bytes.
The production launch observation saw those endpoints before and after apply
```

**Proposition:** Worker policy, readiness and evidence references stay open until exit although source delivery and readiness use end.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: retained-resources.  Independent review: agree; see trigger-review.json by ID.

#### N007

[docs/WORKER.md:249–254](../../docs/WORKER.md) · high confidence

```text

Request, result and token storage have fixed capacities from the
[limits inventory](LIMITS.md). The policy buffer and consumed-parameter snapshot
are static worker storage. Temporary frames hold timing arithmetic, hash state,
argv pointers and diagnostics. Host-side Swift arrays and copied launch strings
remain host allocations; spawn copies argument contents into the new image.
```

**Proposition:** Worker request/result/token storage and input fields have fixed capacities.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: bounded-storage.  Independent review: agree; see trigger-review.json by ID.

#### N008

[docs/WORKER.md:260–261](../../docs/WORKER.md) · high confidence

```text
returned compile-error string on the corresponding paths. The compiled profile
has no explicit PW destruction call; ownership changes inside the private apply
```

**Proposition:** The compiled profile has no explicit PW destruction call.

**Context:**

```text
when requested → application. PW explicitly frees the parameter object and a
returned compile-error string on the corresponding paths. The compiled profile
has no explicit PW destruction call; ownership changes inside the private apply
routine remain unobserved.
```

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Secondary role:** B1 is separately inventoried: private apply ownership remains unobserved.

**Notes:** Family: retained-resources.  Independent review: agree; see trigger-review.json by ID.

#### N010

[docs/WORKER.md:273–275](../../docs/WORKER.md) · high confidence

```text
A worker starts with the authority and restrictions of its credentials, signed
image and inherited context. Built-in workers carry empty entitlements; external
runners supply a separately signed worker, whose read-back entitlements are
```

**Proposition:** Built-in workers have empty entitlements; external workers supply separately signed entitlements.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: starting-authority.  Independent review: agree; see trigger-review.json by ID.

#### N011

[docs/WORKER.md:284–289](../../docs/WORKER.md) · high confidence

```text
Host spawn actions select the policy, evidence and readiness endpoints, plus
the optional token endpoint. The worker launch uses nil spawn attributes and
leaves other descriptors to native close-on-exec inheritance. Its standard
output/error are inherited, and the evidence descriptor can also survive under
its original number if later file actions leave that number intact. The host
passes nil envp. The examined Apple
```

**Proposition:** Worker launch leaves nonselected descriptors to native inheritance and supplies nil envp.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: ambient-inheritance.  Independent review: agree; see trigger-review.json by ID.

#### N013

[docs/WORKER.md:299–303](../../docs/WORKER.md) · high confidence

```text
The worker inherits cwd, umask, limits and signal state. It ignores SIGPIPE
before compilation. Exec-child setup selects descriptor isolation and a new
process group, while leaving ignored-signal inheritance and the signal mask to
native spawn rules. Its empty environment and selected standard descriptors
have independent [inheritance controls](../tests/suites/runner_exec_inheritance/README.md).
```

**Proposition:** Worker changes SIGPIPE while child spawn leaves ignored dispositions and mask to native rules.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: ambient-inheritance.  Independent review: agree; see trigger-review.json by ID.

#### N015

[docs/WORKER.md:305–309](../../docs/WORKER.md) · high confidence

```text
covers environment and descriptors. For an extension request, preparation sets
both core limits to zero after resolving the private entry points; local failure
is recorded. Public admission in
[`extensionMeaningFailure`](../runner/Sources/PWRunnerCore/ProbeRunner.swift)
refuses an exec attempt combined with extension use.
```

**Proposition:** Extension preparation requests zero core limits and admission refuses extension/exec combinations.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: extension-admission.  Independent review: agree; see trigger-review.json by ID.

#### N016

[docs/WORKER.md:311–318](../../docs/WORKER.md) · high confidence

```text
Host launch setup has unchecked native returns: file-action initialization and
worker endpoint duplication, evidence unlink/descriptor flags, issuer handle
initialization and copied-argument allocation. The source specifies the actions
requested; a successful normal launch observes one completed path. These
unchecked paths are visible in
[`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift),
[`ExtensionSession`](../runner/Sources/PWRunnerCore/ExtensionIssuer.swift) and
[`withCStringArrayCopy`](../runner/Sources/PWRunnerCore/CWorker.swift).
```

**Proposition:** Worker launch preparation has unchecked native returns.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: unchecked-setup.  Independent review: agree; see trigger-review.json by ID.

#### N018

[docs/WORKER.md:329–334](../../docs/WORKER.md) · high confidence

```text
Descriptor order also matters without injected native failure. With stdin closed
in the low-descriptor control, evidence is allocated at fd 0. The policy action
overwrites it before the evidence action reads that number: the child receives
a policy pipe at fd 3. Its readiness source equals its destination and remains
close-on-exec in this observation, leaving fd 4 absent. The issuer's separate
high-duplicate control preserves its channel under the exercised low-descriptor
```

**Proposition:** The low-descriptor control loses the worker readiness endpoint and substitutes a policy pipe for evidence.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: launch-endpoints.  Independent review: agree; see trigger-review.json by ID.

#### N021

[docs/WORKER.md:353](../../docs/WORKER.md) · high confidence

```text
| [`attempt_file_open_read`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens read-only, attempts a one-byte read and close, and discards those latter returns. Published success is the open result, with an available descriptor-path observation. |
```

**Proposition:** open_read discards its read/close returns and publishes the open result.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: attempt-semantics.  Independent review: agree; see trigger-review.json by ID.

#### N022

[docs/WORKER.md:354](../../docs/WORKER.md) · high confidence

```text
| [`attempt_file_open_write`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens with `O_WRONLY \| O_TRUNC`, then attempts to write `x` and close. Published success is the open result; the write and close returns are discarded. |
```

**Proposition:** open_write discards write/close returns and publishes the truncating open result.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: attempt-semantics.  Independent review: agree; see trigger-review.json by ID.

#### N023

[docs/WORKER.md:355](../../docs/WORKER.md) · high confidence

```text
| [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens with `O_WRONLY \| O_CREAT` and mode argument `0600`, subject to inherited umask. Existing targets are opened without truncation; missing targets can be created. Close is attempted and its return discarded. |
```

**Proposition:** create opens existing targets without truncation and discards close status.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: attempt-semantics.  Independent review: agree; see trigger-review.json by ID.

#### N024

[docs/WORKER.md:356](../../docs/WORKER.md) · high confidence

```text
| [`attempt_file_read_fresh`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens a fresh close-on-exec descriptor and retains open, metadata, bounded read and single-close results, including partial native evidence when a later call fails. |
```

**Proposition:** Fresh read retains bounded read and single-close results, including partial evidence.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: attempt-semantics.  Independent review: agree; see trigger-review.json by ID.

#### N029

[docs/WORKER.md:391–395](../../docs/WORKER.md) · high confidence

```text
[`attempt_exec_spawn`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
retains leader ownership during observation and targets its process group for
exceptional cleanup. It records unconfirmed reaping when observation ends
without confirmation. Worker death can interrupt that cleanup; the host
supervises the worker. The [lifecycle controls](../tests/suites/runner_exec_lifecycle/README.md)
```

**Proposition:** Worker cleanup can be interrupted by worker death and records unconfirmed reap.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: cleanup-scope.  Independent review: agree; see trigger-review.json by ID.

#### N030

[docs/WORKER.md:398–400](../../docs/WORKER.md) · high confidence

```text
Known gap: an exec child's descendant that leaves the child's process group
can outlive the run unobserved. The worker targets the child's process group
when sending cleanup signals at the exec deadline and at cleanup.
```

**Proposition:** Descendants leaving the exec process group can outlive the run unobserved.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: cleanup-scope.  Independent review: agree; see trigger-review.json by ID.

#### N031

[docs/WORKER.md:402–406](../../docs/WORKER.md) · high confidence

```text
Mach lookup acquires a bootstrap send-right reference, then a service right on
successful lookup. [`attempt_mach_lookup`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
attempts to deallocate the service right and leaves the acquired bootstrap
reference until process exit, including after lookup failure and repeated
attempts. This lifetime is source-established; a live right-count measurement
```

**Proposition:** Mach lookup retains the bootstrap right until exit across failures and repeated attempts.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: retained-resources.  Independent review: agree; see trigger-review.json by ID.

#### N033

[docs/WORKER.md:407–409](../../docs/WORKER.md) · high confidence

```text
is absent. [`attempt_sysctl_read`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
uses an attempt-local stack buffer and publishes call status, discarding the
returned sysctl value. The inventory includes that buffer among local working
```

**Proposition:** Sysctl attempts publish status and discard the returned value.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: attempt-semantics.  Independent review: agree; see trigger-review.json by ID.

#### N034

[docs/WORKER.md:410–411](../../docs/WORKER.md) · high confidence

```text
storage. Unlink and access calls acquire no PW-owned target handle at their
call sites.
```

**Proposition:** Unlink/access acquire no PW-owned target handle at their call sites.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: attempt-semantics.  Independent review: agree; see trigger-review.json by ID.

#### N035

[docs/WORKER.md:418–419](../../docs/WORKER.md) · high confidence

```text
views, separate from worker evidence. Host delivery requires bounded accepted
issuance and confirmed clean issuer reaping.
```

**Proposition:** Worker token delivery requires bounded issuance and confirmed clean issuer reap.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: extension-delivery.  Independent review: agree; see trigger-review.json by ID.

#### N036

[docs/WORKER.md:423–432](../../docs/WORKER.md) · high confidence

```text
The worker's [`prepare_extension`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
resolves consume/release symbols before apply, changes the core limit on the
prepared path, maps and validates the optional channel, and attempts to close
its descriptor once. Early main refusals can precede that preparation. Accepted
token bytes remain a borrowed view of the shared mapping. Requested consume and
release calls occur in
[`attempt_extension`](../controller/tools/pw_probe_runner/pw_probe_runner.c),
inside an attempt after apply. The static handle carries state across actions
and phases; a native result other than the consume failure sentinel establishes
the handle used by a later requested release.
```

**Proposition:** Extension preparation precedes application, token bytes remain a borrowed view, and requested calls occur after apply.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: extension-boundaries.  Independent review: agree; see trigger-review.json by ID.

#### N037

[docs/WORKER.md:434–440](../../docs/WORKER.md) · high confidence

```text
Worker erasure occurs when preparation rejects a mapped channel, after the
consume decision on paths reaching that cleanup, and after normal completion of
the phase loop. Compile/apply/parameter failures, proceed refusal, cancellation
and interruption inside a native call can bypass the final loop erasure. The
accepted mapping remains until exit. The host separately erases its channel
before reply preparation and again at session destruction; its observation
belongs to the host. In issuer [`main`](../controller/tools/pw_probe_runner/pw_extension_issuer.c),
```

**Proposition:** Worker final erasure can be bypassed by earlier failures, cancellation or native-call interruption; accepted mapping remains until exit.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: extension-erasure.  Independent review: agree; see trigger-review.json by ID.

#### N041

[docs/WORKER.md:460–464](../../docs/WORKER.md) · high confidence

```text
The worker knows the admitted attempt kinds and targets, bounded arguments,
phase partitions, release ordinals, time allowances and extension handle state.
It compiles through libsandbox and applies the returned profile. Its attempts
record native operations and their outcomes. Prediction belongs to the separate
validator; disposition and comparison belong to the host.
```

**Proposition:** Worker performs admitted native attempts; prediction, disposition and comparison belong elsewhere.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: evidence-ownership.  Independent review: agree; see trigger-review.json by ID.

#### N045

[docs/WORKER.md:491–496](../../docs/WORKER.md) · high confidence

```text
The worker receives the release ordinal; the host retains the predictions and
assembles comparisons. Later path diagnostics come from the host, and log
candidates and dossiers from the controller. The
[evidence ownership table](ARCHITECTURE.md#evidence-channels-and-ownership)
and [comparison contract](PolicyWitness.md#reading-a-comparison-record) define
what those observations mean, including object-identity and causal limits.
```

**Proposition:** Worker receives release ordinals while host/controller own predictions, comparisons, later paths and log/dossier evidence.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Secondary role:** B1: the closing contract referral names object-identity and causal limits. N299 and N300 collect their concrete guards; this is not another independent inference claim.

**Notes:** Family: evidence-ownership.  Independent review: agree; see trigger-review.json by ID.

#### N046

[docs/WORKER.md:505](../../docs/WORKER.md) · high confidence

```text
| Open a file target before apply or retain a read descriptor across extension phases | Exercises previously acquired authority | Fresh-read source and [extension controls](../tests/suites/witness_contract/README.md#native-extension-boundaries) put each acquisition inside its requested action. |
```

**Proposition:** Preopening a target or retaining a descriptor across phases changes the authority exercised.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: experimental-boundaries.  Independent review: agree; see trigger-review.json by ID.

#### N047

[docs/WORKER.md:506](../../docs/WORKER.md) · high confidence

```text
| Prepare exec pipes and handles before apply | Moves setup outside the specimen's applied conditions | Per-attempt acquisition and [resource controls](../tests/suites/runner_c_worker_harness/README.md#exec-resources-are-per-attempt) retain that exposure. |
```

**Proposition:** Preparing exec resources before application changes the conditions of setup.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: experimental-boundaries.  Independent review: agree; see trigger-review.json by ID.

#### N048

[docs/WORKER.md:507](../../docs/WORKER.md) · high confidence

```text
| Consume a token during preparation or put its bytes in the evidence region | Moves the authority intervention earlier or gives reporting storage bearer authority | Preparation resolves symbols; the separate channel and requested lifecycle calls are covered by the [native boundary controls](../tests/suites/witness_contract/README.md#native-extension-boundaries). |
```

**Proposition:** Early token consumption or bearer bytes in evidence would change authority timing or storage.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: experimental-boundaries.  Independent review: agree; see trigger-review.json by ID.

#### N049

[docs/WORKER.md:508](../../docs/WORKER.md) · high confidence

```text
| Retry with a changed target, extra authority or a friendlier policy, or reuse a worker for another specimen | Substitutes different experimental conditions | The driver launches a fresh worker for the submitted specimen. Interrupted I/O and process-observation loops retry within their existing protocols. |
```

**Proposition:** Changed conditions or worker reuse would substitute a different experiment; protocol retries stay within existing conditions.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: experimental-boundaries.  Independent review: agree; see trigger-review.json by ID.

#### N050

[docs/WORKER.md:509](../../docs/WORKER.md) · high confidence

```text
| Insert `exec_baseline` automatically | Changes the tested policy, including its broad file-read allowance | [Augment composition](../runner/augments/README.md#exec_baseline-composition-limits) is explicit and recorded in resolved source. |
```

**Proposition:** Automatic exec_baseline insertion would change policy; current composition is explicit.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: experimental-boundaries.  Independent review: agree; see trigger-review.json by ID.

#### N055

[docs/WORKER.md:535](../../docs/WORKER.md) · high confidence

```text
- [Acquisitions inside attempts](#acquisitions-inside-attempts): descendants that leave the exec child's process group can outlive the run unobserved.
```

**Proposition:** Escaped exec descendants can outlive the run unobserved.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: cleanup-scope.  Independent review: agree; see trigger-review.json by ID.

#### N303

[docs/WORKER.md:486–487](../../docs/WORKER.md) · high confidence

```text
The host plans validator queries in no-report mode and closes collection before
releasing the worker.
```

**Proposition:** Validator queries use no-report mode outside the worker before release.

**Context:**

```text
The host plans validator queries in no-report mode and closes collection before
releasing the worker. The [ordering account](ARCHITECTURE.md#one-run-in-time)
```

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Notes:** Family: evidence-ownership.  Independent review: agree; see trigger-review.json by ID.

#### N304

[docs/WORKER.md:32–35](../../docs/WORKER.md) · medium confidence

```text
White nodes have multiple roles or form the ambient
execution substrate: the fresh worker, inherited state, token mappings that
also carry metadata, extension state acquired during a requested action, and
shared working storage.
```

**Proposition:** Map color does not divide every worker resource into a single exclusive authority/reporting role.

**Context:**

```text
Blue nodes are reporting apparatus, including exec reporting resources acquired
inside an attempt. Gold nodes represent deliberately supplied authority,
restriction or the API/compiler resources used to exercise them. Green nodes
are acquisitions by attempted operations. Purple nodes hold evidence assembled
outside the worker. White nodes have multiple roles or form the ambient
execution substrate: the fresh worker, inherited state, token mappings that
also carry metadata, extension state acquired during a requested action, and
shared working storage. Starting credentials and policy context remain outside
the supplied-authority cluster because part of that context is ambient.
```

**Classification:** The quoted text positively assigns multiple roles to particular worker resources. It is primarily a proposition about the resources and the representation chosen for them; the collector’s exclusivity inference is a plausible secondary role, not an explicit primary guard.

**Secondary role:** B1/C2 is a possible secondary representational role: separate colors in lines 28–31 can invite exclusive-role reading.

**Notes:** Family: map-scope. Primary function qualifies interpretation of a colored capability map; the named resource roles themselves are positive A1 context. Independent review: change; see trigger-review.json by ID.

### WORKER generated

#### N059

[docs/WORKER.md:72](../../docs/WORKER.md) · high confidence

```text
No explicit child reference; see S13b
```

**Proposition:** Evidence shared-memory object: No explicit child reference; see S13b

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:6489](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S1a, column 11. Owning manifest graph worker_capabilities, item s1a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N061

[docs/WORKER.md:73](../../docs/WORKER.md) · high confidence

```text
H: pw_cworker_shm_open_create; requests FD_CLOEXEC clear without checking return
```

**Proposition:** Host shmFD: H: pw_cworker_shm_open_create; requests FD_CLOEXEC clear without checking return

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:6517](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S1b, column 5. Owning manifest graph worker_capabilities, item s1b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N062

[docs/WORKER.md:73](../../docs/WORKER.md) · high confidence

```text
Worker receives it; exec child excludes it
```

**Proposition:** Host shmFD: Worker receives it; exec child excludes it

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:6523](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S1b, column 11. Owning manifest graph worker_capabilities, item s1b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N064

[docs/WORKER.md:74](../../docs/WORKER.md) · high confidence

```text
Through collection, even if worker cleanup unconfirmed
```

**Proposition:** Host evidence base mapping: Through collection, even if worker cleanup unconfirmed

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:6553](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S2, column 7. Owning manifest graph worker_capabilities, item s2; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N065

[docs/WORKER.md:74](../../docs/WORKER.md) · high confidence

```text
No: exec replaces address space
```

**Proposition:** Host evidence base mapping: No: exec replaces address space

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:6557](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S2, column 11. Owning manifest graph worker_capabilities, item s2; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N067

[docs/WORKER.md:75](../../docs/WORKER.md) · high confidence

```text
Readiness wait only
```

**Proposition:** Host ready-pipe read end: Readiness wait only

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:6582](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S3a, column 7. Owning manifest graph worker_capabilities, item s3a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N068

[docs/WORKER.md:75](../../docs/WORKER.md) · high confidence

```text
No: close-on-exec
```

**Proposition:** Host ready-pipe read end: No: close-on-exec

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:6586](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S3a, column 11. Owning manifest graph worker_capabilities, item s3a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N070

[docs/WORKER.md:76](../../docs/WORKER.md) · high confidence

```text
Worker fd 4; child excludes it
```

**Proposition:** Host ready-pipe write end: Worker fd 4; child excludes it

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:6615](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S3b, column 11. Owning manifest graph worker_capabilities, item s3b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N073

[docs/WORKER.md:78](../../docs/WORKER.md) · high confidence

```text
No: close-on-exec
```

**Proposition:** Host policy-pipe write end: No: close-on-exec

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:6673](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S4b, column 11. Owning manifest graph worker_capabilities, item s4b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N074

[docs/WORKER.md:79](../../docs/WORKER.md) · high confidence

```text
Host before apply; controlled failed endpoint action still spawns
```

**Proposition:** Host token-delivery duplicate tokenFD: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cell asserts actual placement and a failure path that still spawns. It does not state an evidential non-entailment; controlled is context for that actual worker-launch behavior.

**Associated occurrences:** [docs/architecture.json:6701](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S5; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s5; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N075

[docs/WORKER.md:79](../../docs/WORKER.md) · high confidence

```text
Worker fd 5; exec/extension combination refused
```

**Proposition:** Host token-delivery duplicate tokenFD: Worker fd 5; exec/extension combination refused

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:6702](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S5, column 11. Owning manifest graph worker_capabilities, item s5; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N076

[docs/WORKER.md:80](../../docs/WORKER.md) · high confidence

```text
Host before apply; controlled init/add failures reach later uses or spawn
```

**Proposition:** Worker-spawn file-action handle: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cell states actual failed-initialization/action behavior reaching later uses or worker spawn. Column placement does not convert the behavior proposition into a guard.

**Associated occurrences:** [docs/architecture.json:6735](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S6; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s6; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N077

[docs/WORKER.md:80](../../docs/WORKER.md) · high confidence

```text
Handle no; actions determine worker state
```

**Proposition:** Worker-spawn file-action handle: Handle no; actions determine worker state

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:6736](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S6, column 11. Owning manifest graph worker_capabilities, item s6; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N079

[docs/WORKER.md:81](../../docs/WORKER.md) · high confidence

```text
Until exit; unconfirmed cleanup may outlive driver
```

**Proposition:** Fresh worker process: Until exit; unconfirmed cleanup may outlive driver

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:6766](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S7, column 7. Owning manifest graph worker_capabilities, item s7; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N080

[docs/WORKER.md:81](../../docs/WORKER.md) · high confidence

```text
It parents exec children; not itself inherited
```

**Proposition:** Fresh worker process: It parents exec children; not itself inherited

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:6770](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S7, column 11. Owning manifest graph worker_capabilities, item s7; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N082

[docs/WORKER.md:82](../../docs/WORKER.md) · high confidence

```text
No admitted exec+extension plan
```

**Proposition:** Extension channel object: No admitted exec+extension plan

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:6799](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S8a, column 11. Owning manifest graph worker_capabilities, item s8a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N084

[docs/WORKER.md:83](../../docs/WORKER.md) · high confidence

```text
No: close-on-exec except explicit delivery dup
```

**Proposition:** Session descriptor: No: close-on-exec except explicit delivery dup

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:6833](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S8b, column 11. Owning manifest graph worker_capabilities, item s8b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N086

[docs/WORKER.md:84](../../docs/WORKER.md) · high confidence

```text
No: address space replaced
```

**Proposition:** Host token-channel mapping: No: address space replaced

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:6862](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S8c, column 11. Owning manifest graph worker_capabilities, item s8c; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N088

[docs/WORKER.md:85](../../docs/WORKER.md) · high confidence

```text
No: sibling, reaped before worker delivery
```

**Proposition:** Fresh issuer process: No: sibling, reaped before worker delivery

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:6891](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S9, column 11. Owning manifest graph worker_capabilities, item s9; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N090

[docs/WORKER.md:86](../../docs/WORKER.md) · medium confidence

```text
No: issuer creates no exec child
```

**Proposition:** Issuer zero soft/hard core limit: No: issuer creates no exec child

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Retain only under the explicit Reaches exec children column reading: this is a negative transfer boundary for worker exec children, explained by the issuer’s lack of children. As a free-standing proposition solely about issuer child creation it would be out of scope. The column supplies the worker relation; it is not a general supporting-apparatus exemption.

**Scope condition:** A1 only as the table’s worker-exec-child transfer boundary; otherwise exclude.

**Associated occurrences:** [docs/architecture.json:6920](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S10a, column 11. Owning manifest graph worker_capabilities, item s10a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N093

[docs/WORKER.md:87](../../docs/WORKER.md) · medium confidence

```text
No child
```

**Proposition:** Issuer channel mapping: No child

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Retain only under the explicit Reaches exec children column reading: this is a negative transfer boundary for worker exec children, explained by the issuer’s lack of children. As a free-standing proposition solely about issuer child creation it would be out of scope. The column supplies the worker relation; it is not a general supporting-apparatus exemption.

**Scope condition:** A1 only as the table’s worker-exec-child transfer boundary; otherwise exclude.

**Associated occurrences:** [docs/architecture.json:6949](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S10b, column 11. Owning manifest graph worker_capabilities, item s10b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N095

[docs/WORKER.md:88](../../docs/WORKER.md) · medium confidence

```text
No child
```

**Proposition:** Issuer channel fd 3: No child

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Retain only under the explicit Reaches exec children column reading: this is a negative transfer boundary for worker exec children, explained by the issuer’s lack of children. As a free-standing proposition solely about issuer child creation it would be out of scope. The column supplies the worker relation; it is not a general supporting-apparatus exemption.

**Scope condition:** A1 only as the table’s worker-exec-child transfer boundary; otherwise exclude.

**Associated occurrences:** [docs/architecture.json:6978](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S10c, column 11. Owning manifest graph worker_capabilities, item s10c; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N100

[docs/WORKER.md:89](../../docs/WORKER.md) · medium confidence

```text
No child
```

**Proposition:** Issuer libsandbox dynamic- library handle: No child

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Retain only under the explicit Reaches exec children column reading: this is a negative transfer boundary for worker exec children, explained by the issuer’s lack of children. As a free-standing proposition solely about issuer child creation it would be out of scope. The column supplies the worker relation; it is not a general supporting-apparatus exemption.

**Scope condition:** A1 only as the table’s worker-exec-child transfer boundary; otherwise exclude.

**Associated occurrences:** [docs/architecture.json:7007](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S11a, column 11. Owning manifest graph worker_capabilities, item s11a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N104

[docs/WORKER.md:90](../../docs/WORKER.md) · medium confidence

```text
No child
```

**Proposition:** Issuer issue/consume/release symbol addresses: No child

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Retain only under the explicit Reaches exec children column reading: this is a negative transfer boundary for worker exec children, explained by the issuer’s lack of children. As a free-standing proposition solely about issuer child creation it would be out of scope. The column supplies the worker relation; it is not a general supporting-apparatus exemption.

**Scope condition:** A1 only as the table’s worker-exec-child transfer boundary; otherwise exclude.

**Associated occurrences:** [docs/architecture.json:7036](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S11b, column 11. Owning manifest graph worker_capabilities, item s11b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N107

[docs/WORKER.md:91](../../docs/WORKER.md) · high confidence

```text
No: issuer storage not inherited
```

**Proposition:** Native returned token allocation: No: issuer storage not inherited

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:7065](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S12a, column 11. Owning manifest graph worker_capabilities, item s12a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N109

[docs/WORKER.md:92](../../docs/WORKER.md) · high confidence

```text
No admitted exec+extension plan
```

**Proposition:** Token bytes in shared channel: No admitted exec+extension plan

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7094](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S12b, column 11. Owning manifest graph worker_capabilities, item s12b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N111

[docs/WORKER.md:93](../../docs/WORKER.md) · high confidence

```text
No W close; exit
```

**Proposition:** Worker policy fd 0: No W close; exit

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7120](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S13a, column 8. Owning manifest graph worker_capabilities, item s13a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N112

[docs/WORKER.md:93](../../docs/WORKER.md) · high confidence

```text
No: child addopen replaces stdin
```

**Proposition:** Worker policy fd 0: No: child addopen replaces stdin

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7123](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S13a, column 11. Owning manifest graph worker_capabilities, item s13a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N114

[docs/WORKER.md:94](../../docs/WORKER.md) · high confidence

```text
No W close; exit
```

**Proposition:** Worker evidence fd 3: No W close; exit

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7149](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S13b, column 8. Owning manifest graph worker_capabilities, item s13b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N115

[docs/WORKER.md:94](../../docs/WORKER.md) · high confidence

```text
No: child CLOEXEC_DEFAULT
```

**Proposition:** Worker evidence fd 3: No: child CLOEXEC_DEFAULT

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7152](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S13b, column 11. Owning manifest graph worker_capabilities, item s13b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N117

[docs/WORKER.md:95](../../docs/WORKER.md) · high confidence

```text
H requests adddup2(readyPipe[1], 4); self-dup control leaves fd absent
```

**Proposition:** Worker ready fd 4: H requests adddup2(readyPipe[1], 4); self-dup control leaves fd absent

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7180](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S13c, column 5. Owning manifest graph worker_capabilities, item s13c; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N118

[docs/WORKER.md:95](../../docs/WORKER.md) · high confidence

```text
No W close; exit
```

**Proposition:** Worker ready fd 4: No W close; exit

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7183](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S13c, column 8. Owning manifest graph worker_capabilities, item s13c; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N119

[docs/WORKER.md:95](../../docs/WORKER.md) · high confidence

```text
No: child CLOEXEC_DEFAULT
```

**Proposition:** Worker ready fd 4: No: child CLOEXEC_DEFAULT

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7186](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S13c, column 11. Owning manifest graph worker_capabilities, item s13c; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N121

[docs/WORKER.md:96](../../docs/WORKER.md) · high confidence

```text
No admitted exec+extension plan; child flags would exclude it
```

**Proposition:** Worker token fd 5, if supplied: No admitted exec+extension plan; child flags would exclude it

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7220](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S13d, column 11. Owning manifest graph worker_capabilities, item s13d; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N123

[docs/WORKER.md:97](../../docs/WORKER.md) · high confidence

```text
H spawn, without replacement file actions
```

**Proposition:** Worker inherited stdout/stderr: H spawn, without replacement file actions

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7248](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S14a, column 5. Owning manifest graph worker_capabilities, item s14a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N124

[docs/WORKER.md:97](../../docs/WORKER.md) · high confidence

```text
Exit; no explicit W close
```

**Proposition:** Worker inherited stdout/stderr: Exit; no explicit W close

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7251](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S14a, column 8. Owning manifest graph worker_capabilities, item s14a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N125

[docs/WORKER.md:97](../../docs/WORKER.md) · high confidence

```text
No: exec-child capture pipes replace 1/2
```

**Proposition:** Worker inherited stdout/stderr: No: exec-child capture pipes replace 1/2

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7254](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S14a, column 11. Owning manifest graph worker_capabilities, item s14a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N126

[docs/WORKER.md:98](../../docs/WORKER.md) · medium confidence

```text
IC demonstrates inheritance; L saw no extra numeric fd
```

**Proposition:** Other inheritable ambient host descriptors: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This cell positively reports a demonstrated worker inheritance capability and an ordinary launch with no extra fd. The contrast may have B1 implications, but the two observations are actual worker-behavior propositions.

**Secondary role:** B1: the contrast between contaminated and ordinary observations can limit generalization, but the cell's primary propositions are the two actual inheritance observations.

**Associated occurrences:** [docs/architecture.json:7282](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S14b; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s14b; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N127

[docs/WORKER.md:98](../../docs/WORKER.md) · high confidence

```text
H spawn without CLOEXEC_DEFAULT
```

**Proposition:** Other inheritable ambient host descriptors: H spawn without CLOEXEC_DEFAULT

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7277](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S14b, column 5. Owning manifest graph worker_capabilities, item s14b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N128

[docs/WORKER.md:98](../../docs/WORKER.md) · high confidence

```text
No generic W sweep; exit
```

**Proposition:** Other inheritable ambient host descriptors: No generic W sweep; exit

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7280](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S14b, column 8. Owning manifest graph worker_capabilities, item s14b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N129

[docs/WORKER.md:98](../../docs/WORKER.md) · high confidence

```text
No: exec-child CLOEXEC_DEFAULT; IC/CLI observed isolation
```

**Proposition:** Other inheritable ambient host descriptors: No: exec-child CLOEXEC_DEFAULT; IC/CLI observed isolation

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7283](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S14b, column 11. Owning manifest graph worker_capabilities, item s14b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N131

[docs/WORKER.md:99](../../docs/WORKER.md) · high confidence

```text
H clears FD_CLOEXEC and duplicates to 3 without closing source
```

**Proposition:** Possible original-number alias of evidence shmFD: H clears FD_CLOEXEC and duplicates to 3 without closing source

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7306](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S14c, column 5. Owning manifest graph worker_capabilities, item s14c; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N132

[docs/WORKER.md:99](../../docs/WORKER.md) · high confidence

```text
No generic W sweep; exit
```

**Proposition:** Possible original-number alias of evidence shmFD: No generic W sweep; exit

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7309](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S14c, column 8. Owning manifest graph worker_capabilities, item s14c; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N133

[docs/WORKER.md:99](../../docs/WORKER.md) · high confidence

```text
Same evidence object as S13b, not a second object
```

**Proposition:** Possible original-number alias of evidence shmFD: Same evidence object as S13b, not a second object

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7310](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S14c, column 9. Owning manifest graph worker_capabilities, item s14c; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N134

[docs/WORKER.md:99](../../docs/WORKER.md) · high confidence

```text
No: exec-child CLOEXEC_DEFAULT
```

**Proposition:** Possible original-number alias of evidence shmFD: No: exec-child CLOEXEC_DEFAULT

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7312](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S14c, column 11. Owning manifest graph worker_capabilities, item s14c; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N135

[docs/WORKER.md:100](../../docs/WORKER.md) · medium confidence

```text
L plain/-E ps identical; Apple nil-env path corroborates
```

**Proposition:** Worker environment vector: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cell gives positive corroborating observations for the worker environment account. It does not itself state the generalized limit supplied by N136; retain that separate guard rather than duplicate it here.

**Associated occurrences:** [docs/architecture.json:7340](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S15; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s15; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N137

[docs/WORKER.md:100](../../docs/WORKER.md) · high confidence

```text
No: explicit {NULL} child env; IC/CLI
```

**Proposition:** Worker environment vector: No: explicit {NULL} child env; IC/CLI

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7341](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S15, column 11. Owning manifest graph worker_capabilities, item s15; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N139

[docs/WORKER.md:101](../../docs/WORKER.md) · high confidence

```text
Exit, not a PW reset
```

**Proposition:** Credentials and signed worker entitlements, ambient policy context: Exit, not a PW reset

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7367](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S16a, column 8. Owning manifest graph worker_capabilities, item s16a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N140

[docs/WORKER.md:101](../../docs/WORKER.md) · high confidence

```text
Starting access and restrictions; built-in manifest has empty entitlements
```

**Proposition:** Credentials and signed worker entitlements, ambient policy context: Starting access and restrictions; built-in manifest has empty entitlements

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7368](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S16a, column 9. Owning manifest graph worker_capabilities, item s16a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N142

[docs/WORKER.md:102](../../docs/WORKER.md) · high confidence

```text
Received at H spawn; no PW reset
```

**Proposition:** Working directory: Received at H spawn; no PW reset

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7397](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S16g, column 5. Owning manifest graph worker_capabilities, item s16g; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N143

[docs/WORKER.md:102](../../docs/WORKER.md) · high confidence

```text
Yes, no chdir action
```

**Proposition:** Working directory: Yes, no chdir action

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7403](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S16g, column 11. Owning manifest graph worker_capabilities, item s16g; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N145

[docs/WORKER.md:103](../../docs/WORKER.md) · high confidence

```text
Received at H spawn; no PW reset
```

**Proposition:** File-mode creation mask: Received at H spawn; no PW reset

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7426](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S16h, column 5. Owning manifest graph worker_capabilities, item s16h; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N146

[docs/WORKER.md:103](../../docs/WORKER.md) · high confidence

```text
Yes, no umask action
```

**Proposition:** File-mode creation mask: Yes, no umask action

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7432](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S16h, column 11. Owning manifest graph worker_capabilities, item s16h; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N148

[docs/WORKER.md:104](../../docs/WORKER.md) · high confidence

```text
Yes by spawn inheritance; public extension/exec exclusion applies
```

**Proposition:** Inherited resource limits: Yes by spawn inheritance; public extension/exec exclusion applies

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7461](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S16c, column 11. Owning manifest graph worker_capabilities, item s16c; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N150

[docs/WORKER.md:105](../../docs/WORKER.md) · high confidence

```text
W changes SIGPIPE only
```

**Proposition:** Inherited signal dispositions: W changes SIGPIPE only

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7487](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S16i, column 8. Owning manifest graph worker_capabilities, item s16i; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N151

[docs/WORKER.md:105](../../docs/WORKER.md) · high confidence

```text
Ignored dispositions persist, caught handlers reset by exec
```

**Proposition:** Inherited signal dispositions: Ignored dispositions persist, caught handlers reset by exec

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7490](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S16i, column 11. Owning manifest graph worker_capabilities, item s16i; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N153

[docs/WORKER.md:106](../../docs/WORKER.md) · high confidence

```text
No PW reset
```

**Proposition:** Inherited signal mask: No PW reset

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7516](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S16j, column 8. Owning manifest graph worker_capabilities, item s16j; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N154

[docs/WORKER.md:106](../../docs/WORKER.md) · high confidence

```text
Yes, no SETSIGMASK
```

**Proposition:** Inherited signal mask: Yes, no SETSIGMASK

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7519](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S16j, column 11. Owning manifest graph worker_capabilities, item s16j; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N156

[docs/WORKER.md:107](../../docs/WORKER.md) · high confidence

```text
No PW general release
```

**Proposition:** Initial Mach rights receive no PW general release.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7545](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S16e, column 8. Owning manifest graph worker_capabilities, item s16e; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N159

[docs/WORKER.md:108](../../docs/WORKER.md) · high confidence

```text
Native runtime; no PW census/teardown
```

**Proposition:** Executable/library mappings, runtime heaps and threads: Native runtime; no PW census/teardown

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7574](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S16f, column 8. Owning manifest graph worker_capabilities, item s16f; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N160

[docs/WORKER.md:108](../../docs/WORKER.md) · high confidence

```text
Not the same mappings/threads: exec loads a new image
```

**Proposition:** Executable/library mappings, runtime heaps and threads: Not the same mappings/threads: exec loads a new image

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7577](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S16f, column 11. Owning manifest graph worker_capabilities, item s16f; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N162

[docs/WORKER.md:109](../../docs/WORKER.md) · high confidence

```text
No reset
```

**Proposition:** Worker ignored SIGPIPE disposition: No reset

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7603](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S17, column 8. Owning manifest graph worker_capabilities, item s17; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N163

[docs/WORKER.md:109](../../docs/WORKER.md) · high confidence

```text
Yes: no SETSIGDEF
```

**Proposition:** Exec-child setup does not request SETSIGDEF.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7606](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S17, column 11. Owning manifest graph worker_capabilities, item s17; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N165

[docs/WORKER.md:110](../../docs/WORKER.md) · high confidence

```text
No explicit W unmap; exit
```

**Proposition:** Worker evidence base mapping: No explicit W unmap; exit

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7632](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S18, column 8. Owning manifest graph worker_capabilities, item s18; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N166

[docs/WORKER.md:110](../../docs/WORKER.md) · high confidence

```text
No: exec replaces mappings and excludes fd 3
```

**Proposition:** Worker evidence base mapping: No: exec replaces mappings and excludes fd 3

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7635](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S18, column 11. Owning manifest graph worker_capabilities, item s18; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N168

[docs/WORKER.md:111](../../docs/WORKER.md) · high confidence

```text
Static storage at exit; no dynamic handle acquired here
```

**Proposition:** Static extension function pointers: Static storage at exit; no dynamic handle acquired here

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7661](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S19, column 8. Owning manifest graph worker_capabilities, item s19; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N169

[docs/WORKER.md:111](../../docs/WORKER.md) · high confidence

```text
Callable native consume/release, no pre-apply consumption
```

**Proposition:** Static extension function pointers: Callable native consume/release, no pre-apply consumption

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7662](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S19, column 9. Owning manifest graph worker_capabilities, item s19; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N170

[docs/WORKER.md:111](../../docs/WORKER.md) · high confidence

```text
No admitted combination; pointer storage not inherited across exec
```

**Proposition:** Static extension function pointers: No admitted combination; pointer storage not inherited across exec

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7664](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S19, column 11. Owning manifest graph worker_capabilities, item s19; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N172

[docs/WORKER.md:112](../../docs/WORKER.md) · high confidence

```text
No reset; exit
```

**Proposition:** Worker zero soft/hard core limit: No reset; exit

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7690](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S20, column 8. Owning manifest graph worker_capabilities, item s20; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N173

[docs/WORKER.md:112](../../docs/WORKER.md) · high confidence

```text
No admitted exec with extension; hypothetical ABI child would inherit
```

**Proposition:** Worker zero soft/hard core limit: No admitted exec with extension; hypothetical ABI child would inherit

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7693](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S20, column 11. Owning manifest graph worker_capabilities, item s20; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N175

[docs/WORKER.md:113](../../docs/WORKER.md) · high confidence

```text
Rejected mapping: erase/munmap; accepted: no explicit unmap
```

**Proposition:** Worker extension-channel mapping: Rejected mapping: erase/munmap; accepted: no explicit unmap

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7719](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S21, column 8. Owning manifest graph worker_capabilities, item s21; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N176

[docs/WORKER.md:113](../../docs/WORKER.md) · high confidence

```text
No admitted combination; address space replaced on exec
```

**Proposition:** Worker extension-channel mapping: No admitted combination; address space replaced on exec

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7722](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S21, column 11. Owning manifest graph worker_capabilities, item s21; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N178

[docs/WORKER.md:114](../../docs/WORKER.md) · high confidence

```text
Consumable bearer token; validation does not consume it
```

**Proposition:** Accepted token view in S21 (alias of S12b, no copy): Consumable bearer token; validation does not consume it

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7749](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S22, column 9. Owning manifest graph worker_capabilities, item s22; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N179

[docs/WORKER.md:114](../../docs/WORKER.md) · high confidence

```text
No admitted combination
```

**Proposition:** Accepted token view in S21 (alias of S12b, no copy): No admitted combination

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7751](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S22, column 11. Owning manifest graph worker_capabilities, item s22; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N181

[docs/WORKER.md:115](../../docs/WORKER.md) · high confidence

```text
No wipe or explicit release
```

**Proposition:** Static policy_buf: No wipe or explicit release

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7777](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S23, column 8. Owning manifest graph worker_capabilities, item s23; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N182

[docs/WORKER.md:115](../../docs/WORKER.md) · high confidence

```text
Policy input, not a target-file descriptor
```

**Proposition:** Static policy_buf: Policy input, not a target-file descriptor

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7778](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S23, column 9. Owning manifest graph worker_capabilities, item s23; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N183

[docs/WORKER.md:115](../../docs/WORKER.md) · high confidence

```text
No: new exec image
```

**Proposition:** Static policy_buf: No: new exec image

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7780](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S23, column 11. Owning manifest graph worker_capabilities, item s23; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N185

[docs/WORKER.md:116](../../docs/WORKER.md) · high confidence

```text
No wipe; static storage teardown
```

**Proposition:** Static consumed_params snapshot: No wipe; static storage teardown

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7806](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S24, column 8. Owning manifest graph worker_capabilities, item s24; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N186

[docs/WORKER.md:116](../../docs/WORKER.md) · high confidence

```text
Exact compile/capture inputs; no additional access
```

**Proposition:** Static consumed_params snapshot: Exact compile/capture inputs; no additional access

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7807](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S24, column 9. Owning manifest graph worker_capabilities, item s24; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N187

[docs/WORKER.md:116](../../docs/WORKER.md) · high confidence

```text
No: new exec image
```

**Proposition:** Static consumed_params snapshot: No: new exec image

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7809](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S24, column 11. Owning manifest graph worker_capabilities, item s24; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N189

[docs/WORKER.md:117](../../docs/WORKER.md) · high confidence

```text
No: freed before possible child spawn
```

**Proposition:** params_obj and parameter entries: No: freed before possible child spawn

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7838](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S25, column 11. Owning manifest graph worker_capabilities, item s25; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N192

[docs/WORKER.md:118](../../docs/WORKER.md) · high confidence

```text
No explicit sandbox_free_profile; exit reclaims remaining process storage
```

**Proposition:** Returned compiled profile and its bytecode: No explicit sandbox_free_profile; exit reclaims remaining process storage

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7864](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S26a, column 8. Owning manifest graph worker_capabilities, item s26a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N193

[docs/WORKER.md:118](../../docs/WORKER.md) · high confidence

```text
Input to restriction application; not an applied policy by itself
```

**Proposition:** Returned compiled profile and its bytecode: Input to restriction application; not an applied policy by itself

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7865](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S26a, column 9. Owning manifest graph worker_capabilities, item s26a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N194

[docs/WORKER.md:118](../../docs/WORKER.md) · high confidence

```text
No: new exec image; applied restriction separate S28
```

**Proposition:** Returned compiled profile and its bytecode: No: new exec image; applied restriction separate S28

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7867](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S26a, column 11. Owning manifest graph worker_capabilities, item s26a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N196

[docs/WORKER.md:119](../../docs/WORKER.md) · high confidence

```text
Failure reporting only
```

**Proposition:** Compiler error string compile_err on failure: Failure reporting only

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7892](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S26b, column 7. Owning manifest graph worker_capabilities, item s26b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N197

[docs/WORKER.md:119](../../docs/WORKER.md) · high confidence

```text
No child on failed compile path
```

**Proposition:** Compiler error string compile_err on failure: No child on failed compile path

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7896](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S26b, column 11. Owning manifest graph worker_capabilities, item s26b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N199

[docs/WORKER.md:120](../../docs/WORKER.md) · high confidence

```text
No separate allocation/unmap; S18 teardown
```

**Proposition:** Compiled capture bytes/header inside S18: No separate allocation/unmap; S18 teardown

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7922](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S27, column 8. Owning manifest graph worker_capabilities, item s27; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N200

[docs/WORKER.md:120](../../docs/WORKER.md) · high confidence

```text
No: new image, evidence fd excluded
```

**Proposition:** Compiled capture bytes/header inside S18: No: new image, evidence fd excluded

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7925](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S27, column 11. Owning manifest graph worker_capabilities, item s27; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N202

[docs/WORKER.md:121](../../docs/WORKER.md) · high confidence

```text
One-way, no undo
```

**Proposition:** Applied sandbox policy: One-way, no undo

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7951](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S28, column 8. Owning manifest graph worker_capabilities, item s28; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N205

[docs/WORKER.md:122](../../docs/WORKER.md) · high confidence

```text
Attempt only on ordinary cleanup path
```

**Proposition:** open_read target fd: Attempt only on ordinary cleanup path

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7979](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S29, column 7. Owning manifest graph worker_capabilities, item s29; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N206

[docs/WORKER.md:122](../../docs/WORKER.md) · high confidence

```text
close after best-effort one-byte read; return ignored
```

**Proposition:** open_read target fd: close after best-effort one-byte read; return ignored

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7980](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S29, column 8. Owning manifest graph worker_capabilities, item s29; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N207

[docs/WORKER.md:122](../../docs/WORKER.md) · high confidence

```text
No: closed before later exec, which also excludes it
```

**Proposition:** open_read target fd: No: closed before later exec, which also excludes it

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7983](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S29, column 11. Owning manifest graph worker_capabilities, item s29; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N209

[docs/WORKER.md:123](../../docs/WORKER.md) · high confidence

```text
Attempt only on ordinary cleanup path
```

**Proposition:** open_write target fd: Attempt only on ordinary cleanup path

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8008](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S30, column 7. Owning manifest graph worker_capabilities, item s30; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N210

[docs/WORKER.md:123](../../docs/WORKER.md) · high confidence

```text
close after unchecked one-byte write
```

**Proposition:** open_write target fd: close after unchecked one-byte write

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8009](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S30, column 8. Owning manifest graph worker_capabilities, item s30; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N211

[docs/WORKER.md:123](../../docs/WORKER.md) · high confidence

```text
No: later exec excludes it
```

**Proposition:** open_write target fd: No: later exec excludes it

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8012](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S30, column 11. Owning manifest graph worker_capabilities, item s30; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N213

[docs/WORKER.md:124](../../docs/WORKER.md) · high confidence

```text
Attempt only on ordinary cleanup path
```

**Proposition:** create target fd: Attempt only on ordinary cleanup path

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8037](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S31a, column 7. Owning manifest graph worker_capabilities, item s31a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N214

[docs/WORKER.md:124](../../docs/WORKER.md) · high confidence

```text
close, return ignored
```

**Proposition:** create target fd: close, return ignored

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8038](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S31a, column 8. Owning manifest graph worker_capabilities, item s31a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N215

[docs/WORKER.md:124](../../docs/WORKER.md) · high confidence

```text
No: later exec excludes it
```

**Proposition:** create target fd: No: later exec excludes it

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8041](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S31a, column 11. Owning manifest graph worker_capabilities, item s31a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N217

[docs/WORKER.md:125](../../docs/WORKER.md) · high confidence

```text
No automatic unlink; later action/external actor may remove
```

**Proposition:** Newly created filesystem object, if absent: No automatic unlink; later action/external actor may remove

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8067](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S31b, column 8. Owning manifest graph worker_capabilities, item s31b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N218

[docs/WORKER.md:125](../../docs/WORKER.md) · high confidence

```text
Child can resolve it by path, not inherited fd
```

**Proposition:** Newly created filesystem object, if absent: Child can resolve it by path, not inherited fd

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8070](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S31b, column 11. Owning manifest graph worker_capabilities, item s31b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N220

[docs/WORKER.md:126](../../docs/WORKER.md) · high confidence

```text
Attempt only on successful close; close failure retained
```

**Proposition:** Fresh target fd and read observation: Attempt only on successful close; close failure retained

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8095](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S32, column 7. Owning manifest graph worker_capabilities, item s32; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N221

[docs/WORKER.md:126](../../docs/WORKER.md) · high confidence

```text
One close, result published; no retry
```

**Proposition:** Fresh target fd and read observation: One close, result published; no retry

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8096](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S32, column 8. Owning manifest graph worker_capabilities, item s32; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N222

[docs/WORKER.md:126](../../docs/WORKER.md) · high confidence

```text
No: close-on-exec and child exclusion
```

**Proposition:** Fresh target fd and read observation: No: close-on-exec and child exclusion

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8099](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S32, column 11. Owning manifest graph worker_capabilities, item s32; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N224

[docs/WORKER.md:127](../../docs/WORKER.md) · high confidence

```text
No matching mach_port_deallocate, even when lookup fails
```

**Proposition:** Bootstrap send-right reference: No matching mach_port_deallocate, even when lookup fails

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8125](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S33a, column 8. Owning manifest graph worker_capabilities, item s33a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N225

[docs/WORKER.md:127](../../docs/WORKER.md) · high confidence

```text
No explicit transfer; special bootstrap port inheritance is separate
```

**Proposition:** Bootstrap send-right reference: No explicit transfer; special bootstrap port inheritance is separate

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8128](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S33a, column 11. Owning manifest graph worker_capabilities, item s33a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N227

[docs/WORKER.md:128](../../docs/WORKER.md) · high confidence

```text
mach_port_deallocate(mach_task_self, svc), result ignored
```

**Proposition:** Lookup service send right: mach_port_deallocate(mach_task_self, svc), result ignored

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8154](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S33b, column 8. Owning manifest graph worker_capabilities, item s33b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N228

[docs/WORKER.md:128](../../docs/WORKER.md) · high confidence

```text
No explicit port-transfer action
```

**Proposition:** Lookup service send right: No explicit port-transfer action

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8157](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S33b, column 11. Owning manifest graph worker_capabilities, item s33b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N230

[docs/WORKER.md:129](../../docs/WORKER.md) · high confidence

```text
No: explicit addclose and CLOEXEC_DEFAULT
```

**Proposition:** Exec stdout/stderr read endpoints: No: explicit addclose and CLOEXEC_DEFAULT

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8186](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S34a, column 11. Owning manifest graph worker_capabilities, item s34a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N233

[docs/WORKER.md:131](../../docs/WORKER.md) · high confidence

```text
Handle no; action effects yes
```

**Proposition:** Exec file-action heap handle: Handle no; action effects yes

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8254](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S35a, column 11. Owning manifest graph worker_capabilities, item s35a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N235

[docs/WORKER.md:132](../../docs/WORKER.md) · high confidence

```text
Handle no; flags/group effects yes
```

**Proposition:** Exec attribute heap handle: Handle no; flags/group effects yes

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8288](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S35b, column 11. Owning manifest graph worker_capabilities, item s35b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N237

[docs/WORKER.md:133](../../docs/WORKER.md) · high confidence

```text
Attempt normally; unconfirmed reap may outlive it
```

**Proposition:** Exec child PID/process: Attempt normally; unconfirmed reap may outlive it

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8318](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S36a, column 7. Owning manifest graph worker_capabilities, item s36a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N242

[docs/WORKER.md:135](../../docs/WORKER.md) · high confidence

```text
Explicit release action once if submitted/eligible; no automatic exit-time release call; OS teardown
```

**Proposition:** Static extension handle and native extension state: Explicit release action once if submitted/eligible; no automatic exit-time release call; OS teardown

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8387](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S37, column 8. Owning manifest graph worker_capabilities, item s37; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N244

[docs/WORKER.md:135](../../docs/WORKER.md) · high confidence

```text
No admitted exec+extension plan
```

**Proposition:** Static extension handle and native extension state: No admitted exec+extension plan

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8390](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S37, column 11. Owning manifest graph worker_capabilities, item s37; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N246

[docs/WORKER.md:136](../../docs/WORKER.md) · high confidence

```text
No: issuer sibling, duplicate close-on-exec
```

**Proposition:** Issuer-channel high duplicate spawnFD: No: issuer sibling, duplicate close-on-exec

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:8419](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N1, column 11. Owning manifest graph worker_capabilities, item n1; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N247

[docs/WORKER.md:137](../../docs/WORKER.md) · high confidence

```text
No worker memory inheritance
```

**Proposition:** Issuer spawn file-action handle: No worker memory inheritance

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:8453](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N2, column 11. Owning manifest graph worker_capabilities, item n2; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N248

[docs/WORKER.md:138](../../docs/WORKER.md) · high confidence

```text
No worker memory inheritance
```

**Proposition:** Issuer spawn attribute handle: No worker memory inheritance

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:8487](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N3, column 11. Owning manifest graph worker_capabilities, item n3; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N250

[docs/WORKER.md:139](../../docs/WORKER.md) · medium confidence

```text
No: issuer creates no child
```

**Proposition:** Issuer stdio /dev/null descriptors 0/1/2: No: issuer creates no child

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Retain only under the explicit Reaches exec children column reading: this is a negative transfer boundary for worker exec children, explained by the issuer’s lack of children. As a free-standing proposition solely about issuer child creation it would be out of scope. The column supplies the worker relation; it is not a general supporting-apparatus exemption.

**Scope condition:** A1 only as the table’s worker-exec-child transfer boundary; otherwise exclude.

**Associated occurrences:** [docs/architecture.json:8521](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N4, column 11. Owning manifest graph worker_capabilities, item n4; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N251

[docs/WORKER.md:140](../../docs/WORKER.md) · high confidence

```text
Host before apply; controlled allocation failure spawns empty/truncated argv
```

**Proposition:** Host copied launch argument strings: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Empty/truncated worker argv after allocation failure is actual worker-launch behavior. Source placement is also actual; the header adds no B1 inference.

**Associated occurrences:** [docs/architecture.json:8549](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory N5; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item n5; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N253

[docs/WORKER.md:140](../../docs/WORKER.md) · high confidence

```text
Transfer launch arguments, not token bytes
```

**Proposition:** Host copied launch argument strings: Transfer launch arguments, not token bytes

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:8548](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N5, column 9. Owning manifest graph worker_capabilities, item n5; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N254

[docs/WORKER.md:140](../../docs/WORKER.md) · high confidence

```text
Arguments copied into new images, host pointers not inherited
```

**Proposition:** Host copied launch argument strings: Arguments copied into new images, host pointers not inherited

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:8550](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N5, column 11. Owning manifest graph worker_capabilities, item n5; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N256

[docs/WORKER.md:141](../../docs/WORKER.md) · high confidence

```text
Swift scope/ARC, not worker teardown
```

**Proposition:** Host policy byte array and request-population temporary arrays/data: Swift scope/ARC, not worker teardown

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:8581](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N6, column 8. Owning manifest graph worker_capabilities, item n6; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N257

[docs/WORKER.md:141](../../docs/WORKER.md) · high confidence

```text
No host memory inheritance
```

**Proposition:** Host policy byte array and request-population temporary arrays/data: No host memory inheritance

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:8584](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N6, column 11. Owning manifest graph worker_capabilities, item n6; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N258

[docs/WORKER.md:142](../../docs/WORKER.md) · medium confidence

```text
Source-only; no target fd held by PW call site
```

**Proposition:** Host target-resolution buffer/metadata and issuer record: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** No target fd held by the call site is an actual acquisition absence relevant to what target authority reaches the worker. Source-only is a secondary provenance qualifier needing a separate B1 unit if counted.

**Secondary role:** B1/D2: source-only suffix; external origin unknown and no specific local runtime-measurement trigger identified. Primary A1 is the absence of a held target fd.

**Associated occurrences:** [docs/architecture.json:8612](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory N7; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item n7; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N259

[docs/WORKER.md:142](../../docs/WORKER.md) · high confidence

```text
No
```

**Proposition:** Host target-resolution buffer/metadata and issuer record: No

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:8613](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N7, column 11. Owning manifest graph worker_capabilities, item n7; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N261

[docs/WORKER.md:143](../../docs/WORKER.md) · high confidence

```text
Process exit (main never returns after successful apply)
```

**Proposition:** Worker main-frame arguments, timing state and capture nonce: Process exit (main never returns after successful apply)

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8639](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N8, column 8. Owning manifest graph worker_capabilities, item n8; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N262

[docs/WORKER.md:143](../../docs/WORKER.md) · high confidence

```text
Operate release/timing protocol; no new access handle
```

**Proposition:** Worker main-frame arguments, timing state and capture nonce: Operate release/timing protocol; no new access handle

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8640](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N8, column 9. Owning manifest graph worker_capabilities, item n8; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N263

[docs/WORKER.md:143](../../docs/WORKER.md) · high confidence

```text
No: new exec image
```

**Proposition:** Worker main-frame arguments, timing state and capture nonce: No: new exec image

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8642](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N8, column 11. Owning manifest graph worker_capabilities, item n8; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N265

[docs/WORKER.md:144](../../docs/WORKER.md) · high confidence

```text
Call only
```

**Proposition:** Worker temporary pre-compile call frames: Call only

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8667](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N9a, column 7. Owning manifest graph worker_capabilities, item n9a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N267

[docs/WORKER.md:144](../../docs/WORKER.md) · high confidence

```text
No: exec replaces stack
```

**Proposition:** Worker temporary pre-compile call frames: No: exec replaces stack

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8671](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N9a, column 11. Owning manifest graph worker_capabilities, item n9a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N269

[docs/WORKER.md:145](../../docs/WORKER.md) · high confidence

```text
Call only
```

**Proposition:** Capture hash/view/digest/sorting call frames: Call only

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8712](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N9b, column 7. Owning manifest graph worker_capabilities, item n9b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N271

[docs/WORKER.md:145](../../docs/WORKER.md) · high confidence

```text
No: exec replaces stack
```

**Proposition:** Capture hash/view/digest/sorting call frames: No: exec replaces stack

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8716](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N9b, column 11. Owning manifest graph worker_capabilities, item n9b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N273

[docs/WORKER.md:146](../../docs/WORKER.md) · high confidence

```text
Call/attempt only; output copied into S18
```

**Proposition:** Attempt-local stack buffers, argv pointers, polls, wait status and metadata: Call/attempt only; output copied into S18

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8741](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N10, column 7. Owning manifest graph worker_capabilities, item n10; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N274

[docs/WORKER.md:146](../../docs/WORKER.md) · high confidence

```text
Use already inventoried target/child handles; no separate authority
```

**Proposition:** Attempt-local stack buffers, argv pointers, polls, wait status and metadata: Use already inventoried target/child handles; no separate authority

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8743](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N10, column 9. Owning manifest graph worker_capabilities, item n10; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N275

[docs/WORKER.md:146](../../docs/WORKER.md) · high confidence

```text
argv_local strings copied; stack not inherited
```

**Proposition:** Attempt-local stack buffers, argv pointers, polls, wait status and metadata: argv_local strings copied; stack not inherited

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8745](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N10, column 11. Owning manifest graph worker_capabilities, item n10; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N277

[docs/WORKER.md:147](../../docs/WORKER.md) · high confidence

```text
Return/exit; not dynamically allocated by PW
```

**Proposition:** Post-apply outside-attempt automatic diagnostics and seam timespec: Return/exit; not dynamically allocated by PW

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8775](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N11, column 8. Owning manifest graph worker_capabilities, item n11; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N278

[docs/WORKER.md:147](../../docs/WORKER.md) · high confidence

```text
No child spawned on these paths
```

**Proposition:** Post-apply outside-attempt automatic diagnostics and seam timespec: No child spawned on these paths

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8778](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N11, column 11. Owning manifest graph worker_capabilities, item n11; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N280

[docs/WORKER.md:148](../../docs/WORKER.md) · high confidence

```text
Read EOF without exposing policy pipe
```

**Proposition:** Exec child stdin /dev/null fd 0: Read EOF without exposing policy pipe

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8805](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N12, column 9. Owning manifest graph worker_capabilities, item n12; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N282

[docs/WORKER.md:149](../../docs/WORKER.md) · high confidence

```text
Library/exit; no PW-owned handle
```

**Proposition:** Libc diagnostic state reachable after apply: Library/exit; no PW-owned handle

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8838](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N13, column 8. Owning manifest graph worker_capabilities, item n13; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N284

[docs/WORKER.md:149](../../docs/WORKER.md) · high confidence

```text
Library memory not carried across exec
```

**Proposition:** Libc diagnostic state reachable after apply: Library memory not carried across exec

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8841](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N13, column 11. Owning manifest graph worker_capabilities, item n13; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N285

[docs/WORKER.md:150](../../docs/WORKER.md) · medium confidence

```text
Outside specimen worker; source-only
```

**Proposition:** Validator predictions: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Outside specimen worker is an actual provenance/interface boundary. Source-only is a distinct secondary B1/D2 epistemic qualifier; the combined cell should not be treated as entirely B1 merely because it is in Sandbox-gated.

**Secondary role:** B1/D2: source-only suffix, external origin unknown; no specific local runtime-measurement trigger identified.

**Associated occurrences:** [docs/architecture.json:8885](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory X1; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item x1; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N286

[docs/WORKER.md:150](../../docs/WORKER.md) · high confidence

```text
No worker-to-child transfer
```

**Proposition:** Validator predictions: No worker-to-child transfer

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8886](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory X1, column 11. Owning manifest graph worker_capabilities, item x1; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N287

[docs/WORKER.md:151](../../docs/WORKER.md) · medium confidence

```text
Outside specimen worker; source-only
```

**Proposition:** Host disposition and comparison: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Outside specimen worker is an actual provenance/interface boundary. Source-only is a distinct secondary B1/D2 epistemic qualifier; the combined cell should not be treated as entirely B1 merely because it is in Sandbox-gated.

**Secondary role:** B1/D2: source-only suffix, external origin unknown; no specific local runtime-measurement trigger identified.

**Associated occurrences:** [docs/architecture.json:8915](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory X2; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item x2; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N288

[docs/WORKER.md:151](../../docs/WORKER.md) · high confidence

```text
No worker-to-child transfer
```

**Proposition:** Host disposition and comparison: No worker-to-child transfer

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8916](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory X2, column 11. Owning manifest graph worker_capabilities, item x2; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N289

[docs/WORKER.md:152](../../docs/WORKER.md) · medium confidence

```text
Outside specimen worker; source-only
```

**Proposition:** Host path diagnostics: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Outside specimen worker is an actual provenance/interface boundary. Source-only is a distinct secondary B1/D2 epistemic qualifier; the combined cell should not be treated as entirely B1 merely because it is in Sandbox-gated.

**Secondary role:** B1/D2: source-only suffix, external origin unknown; no specific local runtime-measurement trigger identified.

**Associated occurrences:** [docs/architecture.json:8945](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory X3; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item x3; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N290

[docs/WORKER.md:152](../../docs/WORKER.md) · high confidence

```text
No worker-to-child transfer
```

**Proposition:** Host path diagnostics: No worker-to-child transfer

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8946](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory X3, column 11. Owning manifest graph worker_capabilities, item x3; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N291

[docs/WORKER.md:153](../../docs/WORKER.md) · medium confidence

```text
Outside specimen worker; source-only
```

**Proposition:** Controller denial-log candidates: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Outside specimen worker is an actual provenance/interface boundary. Source-only is a distinct secondary B1/D2 epistemic qualifier; the combined cell should not be treated as entirely B1 merely because it is in Sandbox-gated.

**Secondary role:** B1/D2: source-only suffix, external origin unknown; no specific local runtime-measurement trigger identified.

**Associated occurrences:** [docs/architecture.json:8975](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory X4; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item x4; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N292

[docs/WORKER.md:153](../../docs/WORKER.md) · high confidence

```text
No worker-to-child transfer
```

**Proposition:** Controller denial-log candidates: No worker-to-child transfer

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8976](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory X4, column 11. Owning manifest graph worker_capabilities, item x4; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N293

[docs/WORKER.md:154](../../docs/WORKER.md) · medium confidence

```text
Outside specimen worker; source-only
```

**Proposition:** Compiler receipt in dossier: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Outside specimen worker is an actual provenance/interface boundary. Source-only is a distinct secondary B1/D2 epistemic qualifier; the combined cell should not be treated as entirely B1 merely because it is in Sandbox-gated.

**Secondary role:** B1/D2: source-only suffix, external origin unknown; no specific local runtime-measurement trigger identified.

**Associated occurrences:** [docs/architecture.json:9005](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory X5; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item x5; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N294

[docs/WORKER.md:154](../../docs/WORKER.md) · high confidence

```text
No worker-to-child transfer
```

**Proposition:** Compiler receipt in dossier: No worker-to-child transfer

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:9006](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory X5, column 11. Owning manifest graph worker_capabilities, item x5; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N295

[docs/WORKER.md:199](../../docs/WORKER.md) · high confidence

```text
write return discarded
```

**Proposition:** The write result is not published.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:9848](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-ownership.  Owning manifest graph worker_capabilities, item W40; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N296

[docs/WORKER.md:202](../../docs/WORKER.md) · high confidence

```text
Publishes lookup status, not retained port authority
```

**Proposition:** Lookup publication carries status rather than retained port authority.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:9908](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-ownership.  Owning manifest graph worker_capabilities, item W43; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N297

[docs/WORKER.md:218](../../docs/WORKER.md) · high confidence

```text
No transfer into worker; release ordinal is separate
```

**Proposition:** Validator predictions are not transferred into the worker.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8902](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-ownership.  Owning manifest graph worker_capabilities, item x1; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N298

[docs/WORKER.md:219](../../docs/WORKER.md) · high confidence

```text
Host-owned interpretation under evidence contract
```

**Proposition:** Interpretation belongs to the host rather than the worker.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:8932](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-ownership.  Owning manifest graph worker_capabilities, item x2; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N302

[docs/WORKER.md:114](../../docs/WORKER.md) · high confidence

```text
Accepted token view in S21 (alias of S12b, no copy)
```

**Proposition:** The accepted token is a borrowed view, without another copy.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7741](../../docs/architecture.json).

**Notes:** Family: extension-channel.  Owning manifest graph worker_capabilities, item s22; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N310

[docs/WORKER.md:72](../../docs/WORKER.md) · high confidence

```text
Later phases; last mapping/reference may outlive worker
```

**Proposition:** The evidence object can outlive the worker through another mapping/reference.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:6485](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints.  Owning manifest graph worker_capabilities, item s1a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N311

[docs/WORKER.md:72](../../docs/WORKER.md) · high confidence

```text
H requests immediate shm_unlink; injected failure leaves name after teardown
```

**Proposition:** Failed unlink can leave the evidence-object name after owner teardown.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:6486](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints.  Owning manifest graph worker_capabilities, item s1a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N312

[docs/WORKER.md:82](../../docs/WORKER.md) · high confidence

```text
E requests shm_unlink; injected failure leaves name after teardown
```

**Proposition:** Failed unlink can leave the extension-channel name after teardown.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:6796](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints.  Owning manifest graph worker_capabilities, item s8a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N313

[docs/WORKER.md:85](../../docs/WORKER.md) · high confidence

```text
Until issuer exit; delivery requires confirmed clean reap
```

**Proposition:** Worker delivery is conditional on clean confirmed issuer reaping.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** This is retained for a concrete worker relation: delivered/inherited resources, the worker reporting/input protocol, absence of worker memory/authority transfer, worker-vs-host lifetime, or the shared object/channel actually used by the worker. It is not retained merely because it mentions the host/issuer or appears in the map.

**Associated occurrences:** [docs/architecture.json:6887](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints.  Owning manifest graph worker_capabilities, item s9; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N314

[docs/WORKER.md:92](../../docs/WORKER.md) · high confidence

```text
Through worker consume decision or host erase; failure branches differ
```

**Proposition:** Token-byte lifetime varies on failure branches.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7090](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints.  Owning manifest graph worker_capabilities, item s12b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N315

[docs/WORKER.md:94](../../docs/WORKER.md) · high confidence

```text
H requests adddup2(shmFD, 3); low-fd collision can substitute policy pipe
```

**Proposition:** A low-descriptor collision can substitute the policy pipe at the worker evidence endpoint.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7146](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints.  Owning manifest graph worker_capabilities, item s13b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N316

[docs/WORKER.md:96](../../docs/WORKER.md) · high confidence

```text
H requests adddup2(tokenFD, 5); failed action can still spawn
```

**Proposition:** Failed token-endpoint duplication can still be followed by worker spawn.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7214](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints.  Owning manifest graph worker_capabilities, item s13d; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N317

[docs/WORKER.md:96](../../docs/WORKER.md) · high confidence

```text
prepare_extension closes once; early main refusals leave to exit
```

**Proposition:** Worker token descriptor cleanup can be left to exit by early refusals.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7217](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints.  Owning manifest graph worker_capabilities, item s13d; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N318

[docs/WORKER.md:99](../../docs/WORKER.md) · high confidence

```text
Until exit if original number survives file actions
```

**Proposition:** Evidence-source alias survival depends on subsequent file actions.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7308](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints.  Owning manifest graph worker_capabilities, item s14c; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N319

[docs/WORKER.md:112](../../docs/WORKER.md) · high confidence

```text
Restricts core dumping; missing symbols/setup failure qualify it
```

**Proposition:** The extension core-limit change depends on successful prerequisite setup.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7691](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints.  Owning manifest graph worker_capabilities, item s20; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N320

[docs/WORKER.md:114](../../docs/WORKER.md) · high confidence

```text
Until consumption decision or normal loop completion; early exits differ
```

**Proposition:** Borrowed token-view lifetime has different early-exit paths.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:7747](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints.  Owning manifest graph worker_capabilities, item s22; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N321

[docs/WORKER.md:123](../../docs/WORKER.md) · high confidence

```text
Write/truncate opened object; actual write result unpublished
```

**Proposition:** The actual open_write write result is not published.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8010](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints.  Owning manifest graph worker_capabilities, item s30; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N322

[docs/WORKER.md:134](../../docs/WORKER.md) · high confidence

```text
As long as members remain, possibly beyond attempt/worker
```

**Proposition:** Child process-group members can remain beyond the attempt or worker.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8352](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints.  Owning manifest graph worker_capabilities, item s36b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N323

[docs/WORKER.md:134](../../docs/WORKER.md) · high confidence

```text
Yes to descendants unless they leave group
```

**Proposition:** Descendants inherit group membership only while they do not leave it.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The quoted proposition describes an actual worker resource, interface, lifecycle, implementation restriction or absence. Its negative wording is not by itself an interpretive guard.

**Associated occurrences:** [docs/architecture.json:8356](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints.  Owning manifest graph worker_capabilities, item s36b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### F001

[docs/WORKER.md:78](../../docs/WORKER.md) · high confidence

```text
Through bounded policy transfer
```

**Proposition:** The host policy-pipe write endpoint is held through a bounded policy-transfer interval.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The bounded policy-transfer interval bounds the worker’s source-input protocol, despite the endpoint being held by the host.

**Associated occurrences:** [docs/architecture.json:6669](../../docs/architecture.json).

**Notes:** Coverage follow-up addition for worker_capabilities.s4b.Held across; related first entries: none. Independent review: agree; see trigger-review.json by ID.

#### F003

[docs/WORKER.md:92](../../docs/WORKER.md) · medium confidence

```text
I: memcpy on bounded accepted token
```

**Proposition:** The issuer copies a bounded accepted token into the shared channel.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The bounded accepted bytes become the token channel view supplied to the worker (S12b/S22). This directly bounds a received worker resource, unlike the separate native issuer allocation’s cleanup.

**Associated occurrences:** [docs/architecture.json:7088](../../docs/architecture.json).

**Notes:** Coverage follow-up addition for worker_capabilities.s12b.Acquired by; related first entries: N035. Independent review: agree; see trigger-review.json by ID.

#### F004

[docs/WORKER.md:116](../../docs/WORKER.md) · high confidence

```text
W: memcpy from bounded shared parameters
```

**Proposition:** The worker copies bounded shared parameters into its consumed-parameter snapshot.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The worker’s own bounded parameter copy is an actual implementation/resource constraint.

**Associated occurrences:** [docs/architecture.json:7803](../../docs/architecture.json).

**Notes:** Coverage follow-up addition for worker_capabilities.s24.Acquired by; related first entries: N007. Independent review: agree; see trigger-review.json by ID.

#### F005

[docs/WORKER.md:133](../../docs/WORKER.md) · high confidence

```text
Wait observation, conditional group kill, bounded nonblocking reap
```

**Proposition:** Exec-child cleanup uses conditional group killing and bounded nonblocking reaping.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The worker’s conditional process-group cleanup and bounded reaping are actual lifecycle behavior, not a promise of complete descendant absence.

**Associated occurrences:** [docs/architecture.json:8319](../../docs/architecture.json).

**Notes:** Coverage follow-up addition for worker_capabilities.s36a.Released; related first entries: N029, N237. Independent review: agree; see trigger-review.json by ID.


## B1 / C2 — guards with local triggers

### WORKER authored

#### N004

[docs/WORKER.md:54–58](../../docs/WORKER.md) · medium confidence

```text
Acquisition periods record call-site placement. Gating claims retain their
observed, source-only or unknown scope. Cleanup entries name calls; retained
native returns establish their observed outcomes where available. Process exit
reclaims that process's remaining references; created files and references held
by other processes have their own lifetimes.
```

**Proposition:** Call-site placement and named cleanup calls do not by themselves establish gating or cleanup outcomes.

**Classification:** The Released column presents named cleanup calls as release facts, giving an exact local invitation to treat a requested call as an achieved cleanup outcome. This supports the cleanup part only. The gating-scope clause needs its own narrower analysis; the process-exit/reference lifetime sentences are A1.

**Trigger scope:** partial. C2 applies to the specifically named inference; the rationale identifies the remaining clauses.

**Secondary role:** A1: process exit reclaims that process's references while files and other processes' references have their own lifetimes. C2 covers cleanup-call versus outcome; the gating-scope clause has no separate trigger established here.

**Blocked inference:** A named cleanup call in the Released column establishes its successful outcome.

**Local trigger:** [docs/WORKER.md:70](../../docs/WORKER.md)

```text
| Held across | Released | Authority | Sandbox-gated |
```

The unqualified Released heading can make listed cleanup calls look like achieved release outcomes.

**Notes:** Family: scope-of-evidence.  Independent review: agree; see trigger-review.json by ID.

#### N005

[docs/WORKER.md:237–240](../../docs/WORKER.md) · medium confidence

```text
available during collection even when worker cleanup is unconfirmed. The
[C harness](../tests/suites/runner_c_worker_harness/README.md) checks publication
under its bare-deny and full-region cases; that assertion scope belongs beside
the source account of preparation.
```

**Proposition:** Bare-deny/full-region assertions have their own bounded coverage alongside source preparation.

**Classification:** The resource-specific table pairs mapping/preparation facts with bare_deny_default, supplying an organizational invitation to treat the named test as asserting every preparation fact. This is assertion coverage, not proof that a test was executed. The leading cleanup-lifetime fragment is A1 context.

**Secondary role:** A1: host mapping remains available when worker cleanup is unconfirmed. Primary B1/C2 concerns the breadth of assertions inferred from the attached test.

**Blocked inference:** The check attached to the mapping row verifies every described preparation step.

**Local trigger:** [docs/WORKER.md:74](../../docs/WORKER.md)

```text
[`bare_deny_default`](../tests/suites/runner_c_worker_harness/run.sh)
```

The named check is attached to the host evidence-mapping resource row whose acquisition/preparation facts precede it.

**Notes:** Family: scope-of-evidence.  Independent review: agree; see trigger-review.json by ID.

#### N012

[docs/WORKER.md:291–297](../../docs/WORKER.md) · medium confidence

```text
forwards that pointer and the examined
[exec path](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/kern/kern_exec.c)
constructs an empty environment. The recorded launch observation found matching
plain and environment-displaying process output, inherited null-device standard
output/error, and the expected protocol endpoints. The contaminated-worker
control separately establishes a configuration in which an extra descriptor
and environment value reach the worker.
```

**Proposition:** Recorded empty-environment and expected-endpoint observations are configuration-specific beside a contaminated control.

**Classification:** The normal launch observation, followed by the contaminated configuration, is the relevant local comparison. Freshness alone says nothing about a particular descriptor/environment arrangement. The actual configuration observations are A1 secondary propositions.

**Secondary role:** A1: the normal and contaminated launch configurations are actual reported observations; primary B1/C2 is their generalization limit.

**Blocked inference:** The normal launch configuration establishes the descriptor/environment arrangement of every worker launch.

**Local trigger:** [docs/WORKER.md:293–295](../../docs/WORKER.md)

```text
The recorded launch observation found matching
plain and environment-displaying process output, inherited null-device standard
output/error, and the expected protocol endpoints.
```

A specific observed launch configuration supplies the premise that can be improperly generalized to other worker launches.

**Notes:** Family: launch-census.  Independent review: agree; see trigger-review.json by ID.

#### N014

[docs/WORKER.md:304–305](../../docs/WORKER.md) · high confidence

```text
The observer used by those controls itself ignores SIGPIPE, so that observation
covers environment and descriptors. For an extension request, preparation sets
```

**Proposition:** The SIGPIPE-ignoring observer establishes environment/descriptors, not independent signal inheritance.

**Classification:** The adjoining affirmative signal-inheritance account and link to inheritance controls can invite reading the observer as independently establishing the worker-to-child signal state. The guard explains why its own ignored SIGPIPE defeats that reading.

**Blocked inference:** The cited observer independently establishes inherited SIGPIPE behavior or signal-mask state.

**Local trigger:** [docs/WORKER.md:299–303](../../docs/WORKER.md)

```text
The worker inherits cwd, umask, limits and signal state. It ignores SIGPIPE
before compilation. Exec-child setup selects descriptor isolation and a new
process group, while leaving ignored-signal inheritance and the signal mask to
native spawn rules. Its empty environment and selected standard descriptors
have independent [inheritance controls](../tests/suites/runner_exec_inheritance/README.md).
```

Signal rules immediately precede the control reference; this concrete adjacency, not the generic map caption, supplies the coverage inference.

**Notes:** Family: coverage-boundary.  Independent review: agree; see trigger-review.json by ID.

#### N017

[docs/WORKER.md:319–327](../../docs/WORKER.md) · high confidence

```text
The [host setup controls](../tests/suites/runner_unit/README.md#host-setup-failures-and-descriptor-collisions)
exercise these boundaries in disposable source copies with an independent child
observer. Injected worker action-add failures allow a child to run with a wrong
endpoint; failed argument copies allow empty or truncated argv. Injected unlink
failures leave shared-memory names after owner teardown. The checked worker
pipe-flag and issuer action/attribute-flag failures prevent spawn and clean up
in the exercised cases. Failed handle initialization reaches later uses of the
invalid handle; fixture adapters contain those uses, so the controls establish
continued host flow without claiming libc's behavior on that input.
```

**Proposition:** Contained invalid-handle controls establish continued host flow, not libc behavior on invalid handles.

**Classification:** The positive report that failed initialization reaches later invalid-handle uses is the exact premise that could be read as an observation of libc accepting or rejecting that input. The adapters qualification prevents that extension; the other failure-flow observations remain A1.

**Secondary role:** A1: the control reports concrete failure flows. Primary B1/C2 limits inference from fixture-contained invalid-handle uses to libc behavior.

**Blocked inference:** The control observed libc behavior on an invalid native handle.

**Local trigger:** [docs/WORKER.md:325–326](../../docs/WORKER.md)

```text
Failed handle initialization reaches later uses of the
invalid handle
```

This independent affirmative clause precedes the guard about fixture containment and names the exact invalid-input behavior.

**Notes:** Family: coverage-boundary.  Independent review: agree; see trigger-review.json by ID.

#### N019

[docs/WORKER.md:335–336](../../docs/WORKER.md) · high confidence

```text
arrangement. These controlled launches do not establish that an ordinary XPC
host starts with the same descriptor arrangement.
```

**Proposition:** Controlled low-descriptor launches do not establish the ordinary XPC launch arrangement.

**Classification:** The specific low-descriptor launch observations, not the word fresh, invite generalization to an ordinary launch.

**Blocked inference:** An ordinary XPC host starts with the low-descriptor arrangement observed in this control.

**Local trigger:** [docs/WORKER.md:329–334](../../docs/WORKER.md)

```text
With stdin closed
in the low-descriptor control, evidence is allocated at fd 0. The policy action
overwrites it before the evidence action reads that number: the child receives
a policy pipe at fd 3. Its readiness source equals its destination and remains
close-on-exec in this observation, leaving fd 4 absent.
```

This positive controlled descriptor arrangement is the exact state that must not be generalized to ordinary XPC hosts.

**Notes:** Family: launch-census.  Independent review: agree; see trigger-review.json by ID.

#### N025

[docs/WORKER.md:358–363](../../docs/WORKER.md) · medium confidence

```text
The [existing-file control](../tests/suites/witness_contract/README.md#create-on-an-existing-file)
checks preserved bytes and object identity in its case. The
[fresh-read contract](PolicyWitness.md#extension-and-fresh-read-output) defines
which native observations and bounded bytes reach the reply. The source
establishes where each call occurs and which returns are discarded; those are
separate from an independently observed filesystem effect.
```

**Proposition:** Source call placement and discarded returns are distinct from independently observed file effects.

**Classification:** The action table positively describes opened/written/created resources and labels a published success. That specific status/effect presentation can invite treating source call descriptions or status as independently witnessed filesystem effects. The caption alone was too broad.

**Trigger scope:** partial. C2 applies to the specifically named inference; the rationale identifies the remaining clauses.

**Secondary role:** A1: call placement and discarded returns describe implementation behavior. Primary B1/C2 limits status/source-to-filesystem-effect inference.

**Blocked inference:** The published open success or source placement establishes the independently observed write/filesystem effect.

**Local trigger:** [docs/WORKER.md:354](../../docs/WORKER.md)

```text
Published success is the open result; the write and close returns are discarded.
```

The positive success label names a particular result that could be overread as establishing the requested write effect; discarded returns delimit it.

**Notes:** Family: effect-evidence.  Independent review: agree; see trigger-review.json by ID.

#### N026

[docs/WORKER.md:368–378](../../docs/WORKER.md) · high confidence

```text
results and calls cleanup for initialized resources on failure. The examined Apple
[spawn implementation](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/libsyscall/wrappers/spawn/posix_spawn.c)
allocates both handles and can grow action storage. That is a published-source
account; allocation events in the installed libraries were unobserved. PW's
post-apply diagnostics also call libc formatting and error-string routines into
fixed destinations. The examined
[formatting implementation](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/stdio/FreeBSD/vfprintf.c)
and [error-string implementation](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/string/FreeBSD/strerror.c)
have path-dependent internal behavior, including a retained fallback error
buffer. Runtime allocator, locale and binding behavior remain unobserved at
these call sites.
```

**Proposition:** Published spawn/libc source does not establish installed-library allocation, locale or binding behavior.

**Classification:** The positive Apple-source allocation and fallback-buffer claims provide exact local triggers. Fixed PW buffers alone would not invite every claimed allocator/locale/binding inference. The allocation/source-versus-installed distinction is well supported; detailed locale/binding state still has weaker local prompting.

**Trigger scope:** partial. C2 applies to the specifically named inference; the rationale identifies the remaining clauses.

**Blocked inference:** The examined Apple source establishes which allocations occurred in the installed libraries.

**Local trigger:** [docs/WORKER.md:368–370](../../docs/WORKER.md)

```text
The examined Apple
[spawn implementation](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/libsyscall/wrappers/spawn/posix_spawn.c)
allocates both handles and can grow action storage.
```

The document makes a concrete positive allocation claim about examined source; readers can project it onto events in the installed library.

**Additional local trigger:** [docs/WORKER.md:374–377](../../docs/WORKER.md)

```text
[formatting implementation](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/stdio/FreeBSD/vfprintf.c)
and [error-string implementation](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/string/FreeBSD/strerror.c)
have path-dependent internal behavior, including a retained fallback error
buffer.
```

The positive source account of internal paths and a retained buffer can be mistaken for an observation of installed-library behavior.

**Notes:** Family: private-internals.  Independent review: agree; see trigger-review.json by ID.

#### N027

[docs/WORKER.md:380–383](../../docs/WORKER.md) · high confidence

```text
The [per-attempt resource controls](../tests/suites/runner_c_worker_harness/README.md#exec-resources-are-per-attempt)
exercise a descriptor ceiling and a bare-deny setup path. The ceiling checks
reuse across attempts; the denying case observes setup reaching spawn for its
profile and environment. Source establishes post-apply placement. The child
```

**Proposition:** Resource-ceiling and denying controls establish reuse/setup for their conditions; source establishes placement.

**Classification:** A named descriptor-ceiling and bare-deny path is an actual positive control account. It can be generalized to all profiles/environments or all setup properties; the guard scopes the result to the case and separates source placement.

**Blocked inference:** The controls establish setup/gating behavior in every profile and environment, or dynamically verify every call placement.

**Local trigger:** [docs/WORKER.md:380–382](../../docs/WORKER.md)

```text
The [per-attempt resource controls](../tests/suites/runner_c_worker_harness/README.md#exec-resources-are-per-attempt)
exercise a descriptor ceiling and a bare-deny setup path.
```

This is a specific exercised control, unlike a mere citation-presence claim.

**Notes:** Family: coverage-boundary.  Independent review: agree; see trigger-review.json by ID.

#### N039

[docs/WORKER.md:447–451](../../docs/WORKER.md) · high confidence

```text
The worker publishes the native release result and any subsequent requested
read observations. The [extension checks](../tests/suites/witness_contract/check_extensions.py)
accept either result for the after-release read and verify returned content
when successful. The [native evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#native-extension-evidence)
defines the limits of native results and local publication.
```

**Proposition:** After-release checks accept either fresh-read result rather than requiring revocation.

**Classification:** The before/during/after-release fresh-read sequence is a concrete local invitation to interpret the final read as a required revocation check; accepting either result blocks exactly that reading.

**Blocked inference:** The after-release read must fail or the extension test proves revocation.

**Local trigger:** [docs/WORKER.md:445–448](../../docs/WORKER.md)

```text
Fresh reads obtain a new descriptor at each requested action, so before-consume,
during-use and after-release reads each test fresh acquisition at that point.
The worker publishes the native release result and any subsequent requested
read observations.
```

The named before/during/after-release acquisition sequence and published native release result can invite a revocation/state-transition reading.

**Notes:** Family: extension-state.  Independent review: agree; see trigger-review.json by ID.

#### N040

[docs/WORKER.md:453–456](../../docs/WORKER.md) · medium confidence

```text
Known gap: private extension calls may allocate or retain internal state that PW
cannot inspect. Erasure observations cover PW-owned transient buffers; successful
native results and phase progress do not establish kernel extension state,
stable identity, effective permissions or access revocation.
```

**Proposition:** PW-buffer erasure and native success/progress do not establish private extension state, stable identity, permission or revocation.

**Classification:** The release/read sequence supports revocation and permission overreading; the static extension handle/native state wording supports handle-to-kernel-state overreading. Neither by itself supports every stable-identity or private-allocation claim. Preserve the mixed unit visibly: revocation/state parts have C2 triggers; stable identity/private allocation need separate trigger decisions rather than inheriting the bucket automatically.

**Trigger scope:** partial. C2 applies to the specifically named inference; the rationale identifies the remaining clauses.

**Secondary role:** B1/D2: stable-identity and private-allocation limits have no separately identified specific local trigger in this review. Primary C2 applies to the release/permission and handle-to-kernel-state inferences, with the additional trigger recorded.

**Blocked inference:** Native release success and subsequent phase/read progress prove revocation or a particular effective-permission transition.

**Local trigger:** [docs/WORKER.md:445–448](../../docs/WORKER.md)

```text
Fresh reads obtain a new descriptor at each requested action, so before-consume,
during-use and after-release reads each test fresh acquisition at that point.
The worker publishes the native release result and any subsequent requested
read observations.
```

The named before/during/after-release acquisition sequence and published native release result can invite a revocation/state-transition reading.

**Additional local trigger:** [docs/WORKER.md:430–432](../../docs/WORKER.md)

```text
The static handle carries state across actions
and phases; a native result other than the consume failure sentinel establishes
the handle used by a later requested release.
```

This affirmative state-carrying handle account can be mistaken for a full description of private kernel extension state.

**Notes:** Family: extension-state.  Independent review: agree; see trigger-review.json by ID.

#### N042

[docs/WORKER.md:472–476](../../docs/WORKER.md) · high confidence

```text
[create-then-kill control](../tests/suites/witness_contract/README.md#death-after-the-native-return-before-publication)
independently observes the created file while requiring the reply to withhold
the unpublished result. Partially written payload remains outside the evidence
the host is entitled to decode. Native call-boundary flags and result publication
have the meanings in the [worker evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#worker-evidence-contract).
```

**Proposition:** An unpublished slot payload cannot establish no native effect; the independent create-then-kill control has a withheld result.

**Classification:** Completed-slot publication and host decoding are concrete local premises for the absent-publication/absent-effect mistake. The created-file observation refutes that inference; payload eligibility itself is also A1 protocol behavior.

**Secondary role:** A1: publication controls payload eligibility. Primary B1/C2 limits absent-publication to absent-effect inference.

**Blocked inference:** No published result means no native operation or filesystem effect occurred.

**Local trigger:** [docs/WORKER.md:469–471](../../docs/WORKER.md)

```text
[`run_attempt`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
releases the completed slot after writing its payload. The host reads completed
payload after observing publication.
```

The actual report path exposes completed publications and can invite treating a missing report as an absent action/effect.

**Notes:** Family: publication-versus-effect.  Independent review: agree; see trigger-review.json by ID.

#### N043

[docs/WORKER.md:478–484](../../docs/WORKER.md) · high confidence

```text
The worker's release wait uses atomic fields, continuous-clock samples and local
arithmetic/text. Refusal can publish done and spin for exit; cancellation exits.
After the phase loop it erases a delivered token, runs any selected post-phase
seam, publishes done and waits for the host's exit request. These paths use
existing storage and automatic frames. Explicit PW dynamic acquisitions after
apply are concentrated in the attempted operations; the source-level inventory
ends at native/library call boundaries whose internals remain unobserved.
```

**Proposition:** The source-level post-apply inventory stops at native/library call boundaries.

**Classification:** Use the immediate affirmative claim about existing storage and the concentration of PW dynamic acquisitions, not the generic earlier static-buffer inventory. The exact possible overreading extends PW call-site acquisition behavior into native/library internals.

**Secondary role:** A1: the named paths use existing storage and automatic frames. Primary B1/C2 limits extension of the PW acquisition account into library internals.

**Blocked inference:** The named paths and native/library routines perform no additional internal dynamic acquisitions.

**Local trigger:** [docs/WORKER.md:481–483](../../docs/WORKER.md)

```text
These paths use
existing storage and automatic frames. Explicit PW dynamic acquisitions after
apply are concentrated in the attempted operations
```

The independent positive PW acquisition claim directly precedes the native-call-boundary guard.

**Notes:** Family: private-internals.  Independent review: agree; see trigger-review.json by ID.

#### N044

[docs/WORKER.md:489–490](../../docs/WORKER.md) · high confidence

```text
define eligibility for `query_first`. Earlier actions and external actors can
change conditions before a later attempt, even with an intact release hold.
```

**Proposition:** An intact query release hold does not freeze conditions through later attempts.

**Classification:** Closing collection before worker release establishes ordering, and directly invites an overstrong stable-snapshot reading across later attempts.

**Blocked inference:** Conditions observed by prior queries remain unchanged until every later attempt.

**Local trigger:** [docs/WORKER.md:486–487](../../docs/WORKER.md)

```text
The host plans validator queries in no-report mode and closes collection before
releasing the worker.
```

The affirmative query-before-release ordering can be overextended to stability of conditions until later actions.

**Notes:** Family: ordering-not-snapshot.  Independent review: agree; see trigger-review.json by ID.

#### N051

[docs/WORKER.md:510](../../docs/WORKER.md) · high confidence

```text
| Move reply assembly into the worker or use missing publication as proof of no effect | Couples reporting to specimen-controlled communication or substitutes absence of evidence | The host reads released payload; [death before publication](../tests/suites/witness_contract/README.md#death-after-the-native-return-before-publication) preserves an independently observed effect with a withheld result. |
```

**Proposition:** Missing publication is not proof of absent effect.

**Classification:** The completed-publication protocol supplies the exact local premise for treating an absent report as no effect. Moving assembly into the worker is a separate A1 design counterfactual already visible in the unit.

**Secondary role:** A1: moving reply assembly into the worker changes the reporting boundary. Primary B1/C2 is the separate missing-publication inference.

**Blocked inference:** Missing publication proves the operation had no effect.

**Local trigger:** [docs/WORKER.md:469–471](../../docs/WORKER.md)

```text
[`run_attempt`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
releases the completed slot after writing its payload. The host reads completed
payload after observing publication.
```

The actual report path exposes completed publications and can invite treating a missing report as an absent action/effect.

**Notes:** Family: publication-versus-effect.  Independent review: agree; see trigger-review.json by ID.

#### N052

[docs/WORKER.md:512–516](../../docs/WORKER.md) · high confidence

```text
Removing the collection hold would also let worker effects change what
supposedly prior queries observe. The
[ordering controls](../tests/suites/witness_contract/README.md#predictions-before-attempts)
observe both the hold and its limited snapshot meaning. The relevant design
choice is which authority and observation belong on each side of the boundary.
```

**Proposition:** The collection hold is necessary for query-before-attempt evidence but has limited snapshot meaning.

**Classification:** The positive query-before-release arrangement is an exact local trigger for a stable-snapshot overreading. The counterfactual about removing the hold is separately A1 implementation/experiment behavior.

**Secondary role:** A1: removing the collection hold changes which effects can precede queries. Primary B1/C2 limits the intact hold's snapshot meaning.

**Blocked inference:** A preserved hold creates an immutable snapshot of conditions for later operations.

**Local trigger:** [docs/WORKER.md:486–487](../../docs/WORKER.md)

```text
The host plans validator queries in no-report mode and closes collection before
releasing the worker.
```

The affirmative query-before-release ordering can be overextended to stability of conditions until later actions.

**Notes:** Family: ordering-not-snapshot.  Independent review: agree; see trigger-review.json by ID.

#### N053

[docs/WORKER.md:524–528](../../docs/WORKER.md) · high confidence

```text
independent control capable of refuting the proposed claim. Source citations
establish locations; a check's assertions establish its coverage; recorded
execution establishes the configuration actually observed. The inventory is
maintained as per-resource facts with citations, and this explanation is
authored. Call-site completeness is a source-review responsibility. Contributor
```

**Proposition:** Source citations, assertions and recorded execution establish different scopes; call-site completeness requires source review.

**Classification:** The resource-row source/check pairing is exactly the structure whose stronger semantic-coverage interpretation this passage limits. The source-review completeness sentence is broader and should retain its own scope.

**Trigger scope:** partial. C2 applies to the specifically named inference; the rationale identifies the remaining clauses.

**Secondary role:** B1/D2: call-site completeness has no separate specific local trigger established here. Primary C2 covers the source/check-pairing to assertion-coverage inference.

**Blocked inference:** Citation and definition presence establish that a check asserts the row or that the inventory is complete.

**Local trigger:** [docs/WORKER.md:63](../../docs/WORKER.md)

```text
each row cites the source symbol that implements it and the test or rule the manifest names for it.
```

This is a concrete source/check pairing for each resource row; it can be overread as verified assertion coverage.

**Notes:** Family: coverage-boundary.  Independent review: agree; see trigger-review.json by ID.

#### N056

[docs/WORKER.md:536](../../docs/WORKER.md) · medium confidence

```text
- [Supplied extension authority](#supplied-extension-authority): private native state and allocation extend beyond PW-owned buffer and publication observations.
```

**Proposition:** Private state/allocation extend beyond PW buffer/publication observations.

**Classification:** The relevant local material is the extension state-carrying handle and erasure account, not unrelated fixed-capacity policy/input storage. These invite overextending PW-visible state and erasure to private state. Private allocation extent is still a distinct weaker part.

**Trigger scope:** partial. C2 applies to the specifically named inference; the rationale identifies the remaining clauses.

**Secondary role:** B1/D2: private allocation extent lacks a separately identified local trigger. Primary C2 concerns extending PW-visible handle/buffer state into private extension state.

**Blocked inference:** PW handle/buffer publications completely describe private extension state.

**Local trigger:** [docs/WORKER.md:430–432](../../docs/WORKER.md)

```text
The static handle carries state across actions
and phases; a native result other than the consume failure sentinel establishes
the handle used by a later requested release.
```

The explicit state-carrying extension handle can be overread as a complete private-state account.

**Notes:** Family: private-internals.  Independent review: agree; see trigger-review.json by ID.

### WORKER generated

#### N057

[docs/WORKER.md:63](../../docs/WORKER.md) · high confidence

```text
Symbol presence and test definition are verified; whether a test asserts the row is not verified.
```

**Proposition:** Symbol/test-definition checks do not verify that a cited test asserts a resource row.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The concrete per-row source/check pairing can be overread as verified semantic assertion coverage; the guard expressly limits that stronger inference. No claim about historical origin follows.

**Blocked inference:** A cited/located test definition means the test asserts, covers or proves the resource row.

**Local trigger:** [docs/WORKER.md:63](../../docs/WORKER.md)

```text
each row cites the source symbol that implements it and the test or rule the manifest names for it.
```

This is a concrete source/check pairing for each resource row; it can be overread as verified assertion coverage.

**Associated occurrences:** [docs/WORKER.md:66](../../docs/WORKER.md); [docs/generate_architecture.py:363–364](../../docs/generate_architecture.py); [docs/generate_architecture.py:368](../../docs/generate_architecture.py).

**Notes:** Family: coverage-boundary.  Independent review: agree; see trigger-review.json by ID.

#### N110

[docs/WORKER.md:93](../../docs/WORKER.md) · high confidence

```text
L observed pre/post presence; gating unknown
```

**Proposition:** Worker policy fd 0: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The allow-default production observation is an exact local positive premise for this endpoint’s unknown gating limitation. Presence is not a broader usability/gating observation. The header alone was insufficient.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The endpoint’s presence before and after apply establishes its behavior or usability under other sandbox policies.

**Local trigger:** [docs/WORKER.md:247–248](../../docs/WORKER.md)

```text
The production launch observation saw those endpoints before and after apply
under its allow-default specimen.
```

Observed endpoint presence under this allow-default specimen can be overread as established usability or gating under other policies.

**Associated occurrences:** [docs/architecture.json:7122](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S13a; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s13a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N113

[docs/WORKER.md:94](../../docs/WORKER.md) · high confidence

```text
L observed pre/post presence; gating unknown
```

**Proposition:** Worker evidence fd 3: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The allow-default production observation is an exact local positive premise for this endpoint’s unknown gating limitation. Presence is not a broader usability/gating observation. The header alone was insufficient.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The endpoint’s presence before and after apply establishes its behavior or usability under other sandbox policies.

**Local trigger:** [docs/WORKER.md:247–248](../../docs/WORKER.md)

```text
The production launch observation saw those endpoints before and after apply
under its allow-default specimen.
```

Observed endpoint presence under this allow-default specimen can be overread as established usability or gating under other policies.

**Associated occurrences:** [docs/architecture.json:7151](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S13b; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s13b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N116

[docs/WORKER.md:95](../../docs/WORKER.md) · high confidence

```text
L observed pre/post presence; gating unknown
```

**Proposition:** Worker ready fd 4: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The allow-default production observation is an exact local positive premise for this endpoint’s unknown gating limitation. Presence is not a broader usability/gating observation. The header alone was insufficient.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The endpoint’s presence before and after apply establishes its behavior or usability under other sandbox policies.

**Local trigger:** [docs/WORKER.md:247–248](../../docs/WORKER.md)

```text
The production launch observation saw those endpoints before and after apply
under its allow-default specimen.
```

Observed endpoint presence under this allow-default specimen can be overread as established usability or gating under other policies.

**Associated occurrences:** [docs/architecture.json:7185](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S13c; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s13c; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N122

[docs/WORKER.md:97](../../docs/WORKER.md) · high confidence

```text
L presence only; no universal stdio rule
```

**Proposition:** Worker inherited stdout/stderr: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The null-device production launch observation is the precise configuration that might be mistaken for a universal stdio arrangement.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** All worker launches inherit null-device standard output/error.

**Local trigger:** [docs/WORKER.md:293–295](../../docs/WORKER.md)

```text
The recorded launch observation found matching
plain and environment-displaying process output, inherited null-device standard
output/error, and the expected protocol endpoints.
```

A specific observed launch configuration supplies the premise that can be improperly generalized to other worker launches.

**Associated occurrences:** [docs/architecture.json:7253](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S14a; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s14a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N136

[docs/WORKER.md:100](../../docs/WORKER.md) · medium confidence

```text
No entries observed; potential environment-dependent behavior is source-scoped
```

**Proposition:** Worker environment vector: No entries observed; potential environment-dependent behavior is source-scoped

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The positive source account that the examined exec path constructs an empty environment is a specific local invitation to generalize beyond the examined path/configuration; freshness was not relevant.

**Secondary role:** A1: accompanying positive resource context is subordinate to the explicit evidence-scope limitation.

**Blocked inference:** The source account completely establishes environment-dependent behavior of every worker launch.

**Local trigger:** [docs/WORKER.md:288–293](../../docs/WORKER.md)

```text
The host
passes nil envp. The examined Apple
[spawn wrapper](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/libsyscall/wrappers/spawn/posix_spawn.c)
forwards that pointer and the examined
[exec path](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/kern/kern_exec.c)
constructs an empty environment.
```

A concrete nil-env source behavior can be mistaken for a universal or completely observed environment guarantee.

**Associated occurrences:** [docs/architecture.json:7339](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S15, column 9. Owning manifest graph worker_capabilities, item s15; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N138

[docs/WORKER.md:101](../../docs/WORKER.md) · medium confidence

```text
Source + signed manifest; effective authority not fully measured
```

**Proposition:** Credentials and signed worker entitlements, ambient policy context: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The explicit read-back entitlement checks are a particular measured/checked part of starting authority that can be overread as a full effective-authority measurement. The local trigger covers that entitlement-to-authority extension, not every ambient-context uncertainty.

**Trigger scope:** partial. C2 applies to the specifically named inference; the rationale identifies the remaining clauses.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** Checked signed entitlements completely establish measured effective worker authority.

**Local trigger:** [docs/WORKER.md:273–277](../../docs/WORKER.md)

```text
A worker starts with the authority and restrictions of its credentials, signed
image and inherited context. Built-in workers carry empty entitlements; external
runners supply a separately signed worker, whose read-back entitlements are
checked against the specimen's required keys by
[`enforce_required_entitlements`](../controller/src/runner_select.rs).
```

Specific checked entitlement keys are placed within an account of starting authority.

**Associated occurrences:** [docs/architecture.json:7369](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S16a; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s16a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N158

[docs/WORKER.md:108](../../docs/WORKER.md) · medium confidence

```text
L vmmap inventory; per-allocation origin and gating unknown
```

**Proposition:** Executable/library mappings, runtime heaps and threads: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The independently affirmative vmmap inventory observation is a concrete premise for overreading per-allocation origin/gating. Only that positive clause is used as trigger; the unknown clause is the guard.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The VM inventory establishes each allocation’s origin and sandbox gating.

**Local trigger:** [docs/WORKER.md:108](../../docs/WORKER.md)

```text
L vmmap inventory
```

A named VM inventory observation may be mistaken for an account of each mapping’s origin and gating.

**Associated occurrences:** [docs/architecture.json:7576](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S16f; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s16f; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N201

[docs/WORKER.md:121](../../docs/WORKER.md) · high confidence

```text
Source placement; L final application/clean completion, not deny coverage
```

**Proposition:** Applied sandbox policy: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The positive final-application/clean-completion observation is an exact premise for overreading deny coverage. It is separate from the not-deny-coverage guard even though both occur in one cell.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** Observed final application and clean completion establish deny-path coverage.

**Local trigger:** [docs/WORKER.md:121](../../docs/WORKER.md)

```text
L final application/clean completion
```

Successful application and completion can be mistaken for exercised denial/enforcement coverage.

**Associated occurrences:** [docs/architecture.json:7953](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S28; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s28; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N216

[docs/WORKER.md:125](../../docs/WORKER.md) · high confidence

```text
Source-only; creation not implied for existing target
```

**Proposition:** Newly created filesystem object, if absent: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The action/resource name create and published open/create status are concrete wording that can invite existence-of-new-object inference. The source-only qualifier is a separate evidence-scope role.

**Secondary role:** B1/D2: source-only is an additional evidence-provenance qualifier. Primary C2 concerns create/open status versus creation of a new object.

**Blocked inference:** A successful create/open status means a new filesystem object was created.

**Local trigger:** [docs/WORKER.md:200](../../docs/WORKER.md)

```text
Publishes open/create status
```

Calling the status create can be read as proving a new object was created, including for an existing target.

**Associated occurrences:** [docs/architecture.json:8069](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S31b; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s31b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N229

[docs/WORKER.md:129](../../docs/WORKER.md) · medium confidence

```text
Source-only; IC/CLI successful captures, no deny run here
```

**Proposition:** Exec stdout/stderr read endpoints: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The positive successful-capture observation is the exact observed behavior that cannot be generalized to denial coverage. The header alone does not establish this relation.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** Successful IC/CLI captures establish capture behavior under a denying specimen.

**Local trigger:** [docs/WORKER.md:129](../../docs/WORKER.md)

```text
IC/CLI successful captures
```

Successful observed output captures may be overread as output capture being exercised under denial too.

**Associated occurrences:** [docs/architecture.json:8185](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S34a; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s34a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N232

[docs/WORKER.md:131](../../docs/WORKER.md) · high confidence

```text
Source-only Apple malloc/realloc path
```

**Proposition:** Exec file-action heap handle: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The explicit examined-Apple allocation claim supplies a more exact trigger than the gating header or static-storage account.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The examined source proves the installed library allocated this handle through that path in this run.

**Local trigger:** [docs/WORKER.md:368–370](../../docs/WORKER.md)

```text
The examined Apple
[spawn implementation](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/libsyscall/wrappers/spawn/posix_spawn.c)
allocates both handles and can grow action storage.
```

The document makes a concrete positive allocation claim about examined source; readers can project it onto events in the installed library.

**Associated occurrences:** [docs/architecture.json:8253](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S35a; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s35a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N234

[docs/WORKER.md:132](../../docs/WORKER.md) · high confidence

```text
Source-only Apple malloc
```

**Proposition:** Exec attribute heap handle: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The explicit examined-Apple allocation claim supplies a more exact trigger than the gating header or static-storage account.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The examined source proves the installed library allocated this handle through that path in this run.

**Local trigger:** [docs/WORKER.md:368–370](../../docs/WORKER.md)

```text
The examined Apple
[spawn implementation](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/libsyscall/wrappers/spawn/posix_spawn.c)
allocates both handles and can grow action storage.
```

The document makes a concrete positive allocation claim about examined source; readers can project it onto events in the installed library.

**Associated occurrences:** [docs/architecture.json:8287](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S35b; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s35b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N236

[docs/WORKER.md:133](../../docs/WORKER.md) · medium confidence

```text
IC/CLI observed spawn/exit; source-only failure lifetimes
```

**Proposition:** Exec child PID/process: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The success-path spawn/exit observation can be overextended to failure lifetimes; this is narrower and more concrete than the column heading.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** Observed successful spawn/exit establishes all failure-path process lifetimes.

**Local trigger:** [docs/WORKER.md:133](../../docs/WORKER.md)

```text
IC/CLI observed spawn/exit
```

The positive observed success path does not itself establish failure lifetimes.

**Associated occurrences:** [docs/architecture.json:8321](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S36a; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s36a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N239

[docs/WORKER.md:134](../../docs/WORKER.md) · high confidence

```text
Conditional group kill request, not an absence proof
```

**Proposition:** Child process group: Conditional group kill request, not an absence proof

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Exceptional group cleanup is an affirmative worker operation that can be mistaken for observed absence of every process. This is an exact local cleanup-to-absence inference.

**Secondary role:** A1: the same cell also gives the actual resource/lifetime account; the unknown or proof limitation is primary here.

**Blocked inference:** Requesting process-group cleanup proves no child/descendant remains.

**Local trigger:** [docs/WORKER.md:391–393](../../docs/WORKER.md)

```text
[`attempt_exec_spawn`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
retains leader ownership during observation and targets its process group for
exceptional cleanup.
```

Group targeting/cleanup language supplies the premise for an overstrong complete-removal inference.

**Associated occurrences:** [docs/architecture.json:8353](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S36b, column 8. Owning manifest graph worker_capabilities, item s36b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N241

[docs/WORKER.md:135](../../docs/WORKER.md) · high confidence

```text
Across attempts/phases; requested release is not proven revocation
```

**Proposition:** Static extension handle and native extension state: Across attempts/phases; requested release is not proven revocation

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The specific release/read sequence directly invites release-as-revocation interpretation.

**Secondary role:** A1: the same cell also gives the actual resource/lifetime account; the unknown or proof limitation is primary here.

**Blocked inference:** A requested or successful native release proves access revocation.

**Local trigger:** [docs/WORKER.md:445–448](../../docs/WORKER.md)

```text
Fresh reads obtain a new descriptor at each requested action, so before-consume,
during-use and after-release reads each test fresh acquisition at that point.
The worker publishes the native release result and any subsequent requested
read observations.
```

The named before/during/after-release acquisition sequence and published native release result can invite a revocation/state-transition reading.

**Associated occurrences:** [docs/architecture.json:8386](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S37, column 7. Owning manifest graph worker_capabilities, item s37; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N243

[docs/WORKER.md:135](../../docs/WORKER.md) · high confidence

```text
Native extension access represented by handle; exact kernel state unobserved
```

**Proposition:** Static extension handle and native extension state: Native extension access represented by handle; exact kernel state unobserved

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The resource label conjoins the static handle and native extension state, creating a specific local invitation to identify observed handle state with exact kernel state.

**Secondary role:** A1: the same cell also gives the actual resource/lifetime account; the unknown or proof limitation is primary here.

**Blocked inference:** The visible native handle exactly describes kernel extension state.

**Local trigger:** [docs/WORKER.md:135](../../docs/WORKER.md)

```text
Static extension handle and native extension state
```

The single named resource combines the observable handle with native state, which the guard carefully distinguishes.

**Associated occurrences:** [docs/architecture.json:8388](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S37, column 9. Owning manifest graph worker_capabilities, item s37; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N279

[docs/WORKER.md:148](../../docs/WORKER.md) · medium confidence

```text
IC/CLI observed EOF; no independent gating probe here
```

**Proposition:** Exec child stdin /dev/null fd 0: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The positive EOF observation is a concrete outcome that may be mistaken for an independent gating probe. The initial header was not a claim of such a probe.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The EOF observation independently establishes stdin sandbox gating.

**Local trigger:** [docs/WORKER.md:148](../../docs/WORKER.md)

```text
IC/CLI observed EOF
```

Observed EOF is an observed child-stdio result, not an independent policy-gating experiment.

**Associated occurrences:** [docs/architecture.json:8806](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory N12; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item n12; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N281

[docs/WORKER.md:149](../../docs/WORKER.md) · high confidence

```text
Source-only Apple paths; installed-library internals unobserved
```

**Proposition:** Libc diagnostic state reachable after apply: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Concrete positive claims about examined formatting/error-string implementation provide a source-to-installed-behavior trigger. Fixed destinations alone would not establish that exact inference.

**Trigger scope:** partial. C2 applies to the specifically named inference; the rationale identifies the remaining clauses.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The examined implementation establishes the installed library’s runtime allocation, locale and binding behavior.

**Local trigger:** [docs/WORKER.md:374–377](../../docs/WORKER.md)

```text
[formatting implementation](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/stdio/FreeBSD/vfprintf.c)
and [error-string implementation](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/string/FreeBSD/strerror.c)
have path-dependent internal behavior, including a retained fallback error
buffer.
```

The positive source account of internal paths and a retained buffer can be mistaken for an observation of installed-library behavior.

**Associated occurrences:** [docs/architecture.json:8840](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory N13; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item n13; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N283

[docs/WORKER.md:149](../../docs/WORKER.md) · high confidence

```text
Diagnostic formatting; hidden allocation/locale behavior bounded only by source studied
```

**Proposition:** Libc diagnostic state reachable after apply: Diagnostic formatting; hidden allocation/locale behavior bounded only by source studied

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Concrete positive claims about examined formatting/error-string implementation provide a source-to-installed-behavior trigger. Fixed destinations alone would not establish that exact inference.

**Trigger scope:** partial. C2 applies to the specifically named inference; the rationale identifies the remaining clauses.

**Secondary role:** A1: accompanying positive resource context is subordinate to the explicit evidence-scope limitation.

**Blocked inference:** The examined implementation establishes the installed library’s runtime allocation, locale and binding behavior.

**Local trigger:** [docs/WORKER.md:374–377](../../docs/WORKER.md)

```text
[formatting implementation](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/stdio/FreeBSD/vfprintf.c)
and [error-string implementation](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/string/FreeBSD/strerror.c)
have path-dependent internal behavior, including a retained fallback error
buffer.
```

The positive source account of internal paths and a retained buffer can be mistaken for an observation of installed-library behavior.

**Associated occurrences:** [docs/architecture.json:8839](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N13, column 9. Owning manifest graph worker_capabilities, item n13; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N299

[docs/WORKER.md:220](../../docs/WORKER.md) · medium confidence

```text
Path spelling alone is not object identity
```

**Proposition:** A path spelling does not establish object identity.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The drawn/table relationship maps later host path inspection to the newly created object. That is a more specific local invitation to object-identity overreading than generic path/metadata words.

**Blocked inference:** A later observation at the same path establishes that it is the worker-created object.

**Local trigger:** [docs/WORKER.md:209](../../docs/WORKER.md)

```text
| W50 | x3 | s31b | observes | Later host path inspection may observe file effect |
```

The observer-to-created-object relationship can invite identifying the later path object with the earlier created object.

**Associated occurrences:** [docs/architecture.json:8962](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-ownership.  Owning manifest graph worker_capabilities, item x3; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N300

[docs/WORKER.md:221](../../docs/WORKER.md) · medium confidence

```text
Candidate association, not worker-native cause
```

**Proposition:** Log candidate association does not establish worker-native causality.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** There is a missed local trigger: the graph identifies denial-log candidates and joins them with run comparison evidence. This specific association can invite causal attribution; it is more than a generic occurrence of evidence vocabulary. It does not prove historical origin.

**Blocked inference:** Associated denial-log candidates establish that the worker failure was caused by sandbox denial.

**Local trigger:** [docs/WORKER.md:214](../../docs/WORKER.md)

```text
Controller associates external log candidates with run evidence
```

The explicit association of the denial-log-candidate node with run evidence can be overread as worker-native causal evidence.

**Additional local trigger:** [docs/WORKER.md:153](../../docs/WORKER.md)

```text
Controller denial-log candidates
```

The associated external records are specifically denial-log candidates, which is what makes the causal inference locally invited.

**External origin (unknown):** No sufficiently specific independent inviting wording was identified in WORKER.md; external textual motivation is unknown. This is not a historical-origin claim.

**Associated occurrences:** [docs/architecture.json:8992](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-ownership.  Owning manifest graph worker_capabilities, item x4; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N301

[docs/WORKER.md:222](../../docs/WORKER.md) · medium confidence

```text
Receipt and applied-policy evidence are distinct
```

**Proposition:** Compiler receipt evidence does not itself establish applied policy.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The source-to-capture-to-application sequence gives an exact local relation that can be compressed into receipt-equals-applied-policy evidence. Merely saying the host validates a receipt was a weaker trigger.

**Blocked inference:** The compiler receipt itself establishes applied-policy evidence.

**Local trigger:** [docs/WORKER.md:255–260](../../docs/WORKER.md)

```text
The worker checks the received source length and bounded fields, then passes
the policy and parameter snapshot to libsandbox. Its compiled-object path is
[`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c) →
[`pw_capture_profile`](../controller/tools/pw_probe_runner/pw_profile_capture.h)
when requested → application.
```

The connected capture/application path can invite treating a capture receipt as proof of what was applied.

**Associated occurrences:** [docs/architecture.json:9022](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-ownership.  Owning manifest graph worker_capabilities, item x5; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N308

[docs/WORKER.md:109](../../docs/WORKER.md) · high confidence

```text
no dedicated live signal control
```

**Proposition:** No dedicated live signal control establishes the claimed exec-child signal inheritance.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The positive claim about changed exec-child behavior and the recorded EPIPE survival can be overread as a dedicated child-signal observation. The guard rejects that exact leap; the generic caption was not required.

**Blocked inference:** Worker EPIPE survival or the cited control independently establishes exec-child signal inheritance.

**Local trigger:** [docs/WORKER.md:109](../../docs/WORKER.md)

```text
Survive broken ready-pipe write; also changes exec-child behavior
```

A single resource row links observed worker survival with claimed child behavior, which can invite a child-inheritance coverage inference.

**Associated occurrences:** [docs/architecture.json:7606](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope.  Owning manifest graph worker_capabilities, item s17; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

### Direct supporting machinery

#### N305

[docs/generator_common.py:3](../../docs/generator_common.py) · high confidence

```text
A definition is a place to look, never evidence that a test asserts a claim.
```

**Proposition:** A located test definition is not evidence that the test asserts a worker capability claim.

**Context:**

```text
"""Shared, mechanical citation checks for the documentation generators (G4–G6).

A definition is a place to look, never evidence that a test asserts a claim.
"""
```

**Classification:** The concrete per-row source/check pairing can be overread as verified semantic assertion coverage; the guard expressly limits that stronger inference. No claim about historical origin follows.

**Blocked inference:** A cited/located test definition means the test asserts, covers or proves the resource row.

**Local trigger:** [docs/WORKER.md:63](../../docs/WORKER.md)

```text
each row cites the source symbol that implements it and the test or rule the manifest names for it.
```

This is a concrete source/check pairing for each resource row; it can be overread as verified assertion coverage.

**Notes:** Family: coverage-boundary. Shared checker is called by generate_architecture.py for the worker capability graph; included only in that direct role. Independent review: agree; see trigger-review.json by ID.

#### N306

[tests/suites/source_drift/README.md:155–158](../../tests/suites/source_drift/README.md) · high confidence

```text
- **G10. Captions state the verified guarantee.** A generated caption or
  summary says what the generator verified about citations, presence and
  definition, and nothing stronger; it never says a test exercises, covers or
  proves a row.
```

**Proposition:** Generated caption guarantees must not imply that a test exercises, covers or proves a worker inventory row.

**Classification:** The concrete per-row source/check pairing can be overread as verified semantic assertion coverage; the guard expressly limits that stronger inference. No claim about historical origin follows.

**Blocked inference:** A cited/located test definition means the test asserts, covers or proves the resource row.

**Local trigger:** [docs/WORKER.md:63](../../docs/WORKER.md)

```text
each row cites the source symbol that implements it and the test or rule the manifest names for it.
```

This is a concrete source/check pairing for each resource row; it can be overread as verified assertion coverage.

**Notes:** Family: coverage-boundary. G10 directly governs the WORKER caption/summary; general generator mechanics are otherwise contextual coverage. Independent review: agree; see trigger-review.json by ID.


## B1 / D2 — guards without identified local triggers

### WORKER authored

#### N003

[docs/WORKER.md:45–47](../../docs/WORKER.md) · medium confidence

```text
The edges select relationships among the inventoried resources. Some nodes,
including ambient state and temporary storage, stand without a drawn
observation path. Open the SVG at its native size to read the complete map.
```

**Proposition:** The capability map selects relationships and omits observation paths for some nodes.

**Classification:** An edge-type legend explains how to read drawn edges; it does not say every observation path is drawn. The proposed trigger changes a type legend into a completeness promise without specific wording making that promise.

**Blocked inference:** The figure draws every observation path for every resource.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Notes:** Family: map-scope.  Independent review: change; see trigger-review.json by ID.

#### N009

[docs/WORKER.md:261–262](../../docs/WORKER.md) · medium confidence

```text
ownership changes inside the private apply
routine remain unobserved.
```

**Proposition:** Private apply ownership changes remain unobserved.

**Context:**

```text
when requested → application. PW explicitly frees the parameter object and a
returned compile-error string on the corresponding paths. The compiled profile
```

**Classification:** No local statement describes the private apply routine transferring ownership or destroying the profile. A missing explicit PW destruction call is an actual absence, not a positive claim about what private apply does.

**Blocked inference:** The private apply routine takes ownership or preserves the allocation in a known way.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Notes:** Family: private-internals.  Independent review: agree; see trigger-review.json by ID.

#### N020

[docs/WORKER.md:338–344](../../docs/WORKER.md) · medium confidence

```text
Known gap: the starting-state observation is bounded to the exercised launch
configuration. It records descriptors, process identity, cwd, displayed
arguments/environment and VM regions. Task-port inspection was refused; live
signal masks, resource limits, a complete Mach-right census and private runtime
state remain unobserved. Native inheritance and loader behavior therefore form
part of the instrument's received substrate, without a complete isolation or
effective-authority census.
```

**Proposition:** Starting-state observations do not constitute a full signal/resource/Mach-right/runtime or effective-authority census.

**Classification:** Fresh worker denotes one process per specimen and is immediately paired with already-present libraries/process context. Neither freshness nor the listed endpoint/environment observations promise a full signal, Mach-right, private-runtime or effective-authority census. Some individual observation-generalization clauses have narrower C2 counterparts (N012/N122); do not let those establish C2 for the whole census claim.

**Secondary role:** A1: native inheritance and loader state are received worker substrate. Primary B1/D2 concerns the completeness of the observation and authority census.

**Blocked inference:** A fresh process or bounded launch observation establishes complete isolation and a full effective-authority/runtime census.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Notes:** Family: launch-census.  Independent review: change; see trigger-review.json by ID.

#### N028

[docs/WORKER.md:384–389](../../docs/WORKER.md) · medium confidence

```text
receives explicit null-device stdin, captured stdout/stderr, an empty environment
and a new process group. PW drains output and observes the leader under the
[execution budgets](LIMITS.md#execution-budgets). A nonzero child exit after
successful spawn still supplies spawn evidence; the
[exec action contract](PolicyWitness.md#attempt-kinds-the-runner-implements)
keeps spawn, child exit and cleanup meanings separate.
```

**Proposition:** A nonzero child exit does not negate successful-spawn evidence.

**Classification:** Null stdin, captured output and leader observation do not invite the exact inference that a nonzero child exit negates successful spawn. The proposed trigger discusses lifecycle setup, whereas the guard distinguishes the result of spawning from the result of the spawned program. A conventional process-success conflation is hypothetical external context.

**Blocked inference:** A nonzero child exit means the preceding spawn failed.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Notes:** Family: spawn-versus-child.  Independent review: change; see trigger-review.json by ID.

#### N032

[docs/WORKER.md:406–407](../../docs/WORKER.md) · medium confidence

```text
attempts. This lifetime is source-established; a live right-count measurement
is absent. [`attempt_sysctl_read`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
```

**Proposition:** The source-established Mach-right lifetime lacks a live right-count measurement.

**Classification:** The source says a bootstrap reference is retained, but does not claim a live right count. A generic cited test/definition is not a positive measurement claim. The exact inference that a native right-count measurement occurred lacks a local trigger.

**Blocked inference:** The described bootstrap-reference lifetime was independently established by a live right-count measurement.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Notes:** Family: coverage-boundary.  Independent review: change; see trigger-review.json by ID.

#### N054

[docs/WORKER.md:534](../../docs/WORKER.md) · medium confidence

```text
- [Starting authority and ambient context](#starting-authority-and-ambient-context): the launch observation is a bounded census of inherited and runtime state.
```

**Proposition:** Launch observations are a bounded census of inherited/runtime state.

**Classification:** The gap-index summary inherits N020’s census boundary, not a new trigger. Freshness does not assert complete instrumentation, isolation or effective-authority measurement.

**Blocked inference:** The launch observation completely inventories inherited/runtime state.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Notes:** Family: launch-census.  Independent review: change; see trigger-review.json by ID.

### WORKER generated

#### N058

[docs/WORKER.md:72](../../docs/WORKER.md) · medium confidence

```text
Source-only, host before apply
```

**Proposition:** Evidence shared-memory object: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:6488](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S1a; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s1a; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N060

[docs/WORKER.md:73](../../docs/WORKER.md) · medium confidence

```text
Source-only, host before apply
```

**Proposition:** Host shmFD: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:6522](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S1b; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s1b; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N063

[docs/WORKER.md:74](../../docs/WORKER.md) · medium confidence

```text
Source-only, host before apply
```

**Proposition:** Host evidence base mapping: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:6556](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S2; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s2; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N066

[docs/WORKER.md:75](../../docs/WORKER.md) · medium confidence

```text
Source-only, host before apply
```

**Proposition:** Host ready-pipe read end: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:6585](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S3a; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s3a; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N069

[docs/WORKER.md:76](../../docs/WORKER.md) · medium confidence

```text
Source-only, host before apply
```

**Proposition:** Host ready-pipe write end: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:6614](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S3b; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s3b; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N071

[docs/WORKER.md:77](../../docs/WORKER.md) · medium confidence

```text
Source-only, host before apply
```

**Proposition:** Host policy-pipe read end: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:6643](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S4a; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s4a; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N072

[docs/WORKER.md:78](../../docs/WORKER.md) · medium confidence

```text
Source-only, host before apply
```

**Proposition:** Host policy-pipe write end: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:6672](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S4b; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s4b; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N078

[docs/WORKER.md:81](../../docs/WORKER.md) · medium confidence

```text
Source-only spawn; L observed two lifetimes
```

**Proposition:** Fresh worker process: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:6769](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S7; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s7; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N081

[docs/WORKER.md:82](../../docs/WORKER.md) · medium confidence

```text
Source-only, outside worker sandbox
```

**Proposition:** Extension channel object: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:6798](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S8a; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s8a; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N108

[docs/WORKER.md:92](../../docs/WORKER.md) · medium confidence

```text
Source-only
```

**Proposition:** Token bytes in shared channel: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7093](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S12b; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s12b; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N120

[docs/WORKER.md:96](../../docs/WORKER.md) · medium confidence

```text
Source-only; close failure published on prepared path
```

**Proposition:** Worker token fd 5, if supplied: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7219](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S13d; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s13d; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N130

[docs/WORKER.md:99](../../docs/WORKER.md) · medium confidence

```text
Source-only possibility; L saw no extra alias
```

**Proposition:** Possible original-number alias of evidence shmFD: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7311](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S14c; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s14c; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N141

[docs/WORKER.md:102](../../docs/WORKER.md) · medium confidence

```text
L cwd /; gating unknown
```

**Proposition:** Working directory: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7402](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S16g; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s16g; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N144

[docs/WORKER.md:103](../../docs/WORKER.md) · medium confidence

```text
Source-only inheritance; live value unknown
```

**Proposition:** File-mode creation mask: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7431](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S16h; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s16h; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N147

[docs/WORKER.md:104](../../docs/WORKER.md) · medium confidence

```text
Unknown live values
```

**Proposition:** Inherited resource limits: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7460](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S16c; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s16c; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N149

[docs/WORKER.md:105](../../docs/WORKER.md) · medium confidence

```text
Source-only; no signal census
```

**Proposition:** Inherited signal dispositions: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7489](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S16i; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s16i; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N152

[docs/WORKER.md:106](../../docs/WORKER.md) · medium confidence

```text
Source-only; live mask unknown
```

**Proposition:** Inherited signal mask: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7518](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S16j; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s16j; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N155

[docs/WORKER.md:107](../../docs/WORKER.md) · medium confidence

```text
L lsmp refused; exact set unknown
```

**Proposition:** Task-self, bootstrap and other initial Mach rights: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7547](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S16e; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s16e; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N157

[docs/WORKER.md:107](../../docs/WORKER.md) · medium confidence

```text
Special-port inheritance/native exec rules; exact set unknown
```

**Proposition:** Task-self, bootstrap and other initial Mach rights: Special-port inheritance/native exec rules; exact set unknown

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Fixed request/result storage has no specific relation to the set of initial Mach rights or their inheritance. No other local complete-right-set assertion was identified.

**Secondary role:** A1: the same cell also gives the actual resource/lifetime account; the unknown or proof limitation is primary here.

**Blocked inference:** The exact inherited Mach-right set is known.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7548](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S16e, column 11. Owning manifest graph worker_capabilities, item s16e; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N161

[docs/WORKER.md:109](../../docs/WORKER.md) · medium confidence

```text
Source-only; L pre-ready final EPIPE survived
```

**Proposition:** Worker ignored SIGPIPE disposition: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7605](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S17; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s17; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N164

[docs/WORKER.md:110](../../docs/WORKER.md) · high confidence

```text
L shared mappings observed; no mapping-identity attribution from size alone
```

**Proposition:** Worker evidence base mapping: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The document reports shared mappings but gives no mapping-size observation or rule assigning identity by size. General shared-mapping discussion is only a shared topic for the exact size-to-identity inference.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** Equal or expected mapping sizes identify the worker evidence mapping.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7634](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S18; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s18; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N167

[docs/WORKER.md:111](../../docs/WORKER.md) · medium confidence

```text
Source-only; library internals unobserved
```

**Proposition:** Static extension function pointers: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7663](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S19; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s19; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N171

[docs/WORKER.md:112](../../docs/WORKER.md) · medium confidence

```text
Source-only, request-dependent
```

**Proposition:** Worker zero soft/hard core limit: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7692](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S20; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s20; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N174

[docs/WORKER.md:113](../../docs/WORKER.md) · medium confidence

```text
Source-only; rejection unmap failure recorded
```

**Proposition:** Worker extension-channel mapping: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7721](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S21; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s21; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N177

[docs/WORKER.md:114](../../docs/WORKER.md) · medium confidence

```text
Source-only
```

**Proposition:** Accepted token view in S21 (alias of S12b, no copy): the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7750](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S22; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s22; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N180

[docs/WORKER.md:115](../../docs/WORKER.md) · medium confidence

```text
Source-only; read receipt observed in L
```

**Proposition:** Static policy_buf: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7779](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S23; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s23; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N184

[docs/WORKER.md:116](../../docs/WORKER.md) · medium confidence

```text
Source-only
```

**Proposition:** Static consumed_params snapshot: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7808](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S24; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s24; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N188

[docs/WORKER.md:117](../../docs/WORKER.md) · medium confidence

```text
Source-only; private allocation internals unobserved
```

**Proposition:** params_obj and parameter entries: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7837](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S25; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s25; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N190

[docs/WORKER.md:118](../../docs/WORKER.md) · medium confidence

```text
Source-only, private object lifetime unknown
```

**Proposition:** Returned compiled profile and its bytecode: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7866](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S26a; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s26a; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N191

[docs/WORKER.md:118](../../docs/WORKER.md) · medium confidence

```text
Passed to capture/apply; allocation lifetime inside apply unknown
```

**Proposition:** Returned compiled profile and its bytecode: Passed to capture/apply; allocation lifetime inside apply unknown

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The compiled object is passed to apply, but no affirmative private ownership/lifetime change is specified. Source placement and missing explicit free do not identify that private transition.

**Secondary role:** A1: the same cell also gives the actual resource/lifetime account; the unknown or proof limitation is primary here.

**Blocked inference:** The allocation lifetime inside private apply is known.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7863](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S26a, column 7. Owning manifest graph worker_capabilities, item s26a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N195

[docs/WORKER.md:119](../../docs/WORKER.md) · medium confidence

```text
Source-only
```

**Proposition:** Compiler error string compile_err on failure: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7895](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S26b; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s26b; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N198

[docs/WORKER.md:120](../../docs/WORKER.md) · medium confidence

```text
Source-only, pre-apply
```

**Proposition:** Compiled capture bytes/header inside S18: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7924](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S27; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s27; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N203

[docs/WORKER.md:121](../../docs/WORKER.md) · medium confidence

```text
Inherited sandbox constraints; exact child policy effects not inventoried here
```

**Proposition:** Applied sandbox policy: Inherited sandbox constraints; exact child policy effects not inventoried here

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Executing under inherited sandbox constraints does not name exact child-policy effects or assert they have been inventoried. The proposed trigger is the same topic rather than an effect-census claim.

**Secondary role:** A1: accompanying positive resource context is subordinate to the explicit evidence-scope limitation.

**Blocked inference:** The exact sandbox effects on the exec child are inventoried here.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7954](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory S28, column 11. Owning manifest graph worker_capabilities, item s28; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N204

[docs/WORKER.md:122](../../docs/WORKER.md) · medium confidence

```text
Source-only; no file probe rerun in pass 1
```

**Proposition:** open_read target fd: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7982](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S29; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s29; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N208

[docs/WORKER.md:123](../../docs/WORKER.md) · medium confidence

```text
Source-only
```

**Proposition:** open_write target fd: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:8011](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S30; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s30; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N212

[docs/WORKER.md:124](../../docs/WORKER.md) · medium confidence

```text
Source-only; existing-file checker inspected, not rerun
```

**Proposition:** create target fd: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:8040](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S31a; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s31a; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N219

[docs/WORKER.md:126](../../docs/WORKER.md) · medium confidence

```text
Source-only; extension checker inspected, not rerun
```

**Proposition:** Fresh target fd and read observation: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:8098](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S32; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s32; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N223

[docs/WORKER.md:127](../../docs/WORKER.md) · medium confidence

```text
Source-only; native failure remains possible
```

**Proposition:** Bootstrap send-right reference: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:8127](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S33a; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s33a; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N226

[docs/WORKER.md:128](../../docs/WORKER.md) · medium confidence

```text
Source-only; no right-count control
```

**Proposition:** Lookup service send right: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:8156](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S33b; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s33b; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N231

[docs/WORKER.md:130](../../docs/WORKER.md) · medium confidence

```text
Source-only; IC/CLI observed streams
```

**Proposition:** Exec stdout/stderr write endpoints: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:8219](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S34b; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s34b; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N238

[docs/WORKER.md:134](../../docs/WORKER.md) · medium confidence

```text
Source-only; lifecycle cases inspected, not rerun
```

**Proposition:** Child process group: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:8355](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S36b; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s36b; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N240

[docs/WORKER.md:135](../../docs/WORKER.md) · medium confidence

```text
Source-only
```

**Proposition:** Static extension handle and native extension state: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:8389](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory S37; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item s37; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N260

[docs/WORKER.md:143](../../docs/WORKER.md) · medium confidence

```text
Source-only; stack mapping visible in L
```

**Proposition:** Worker main-frame arguments, timing state and capture nonce: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:8641](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory N8; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item n8; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N264

[docs/WORKER.md:144](../../docs/WORKER.md) · medium confidence

```text
Source-only; native library internals unobserved
```

**Proposition:** Worker temporary pre-compile call frames: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:8670](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory N9a; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item n9a; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N266

[docs/WORKER.md:144](../../docs/WORKER.md) · high confidence

```text
Return or process exit; no claim of byte erasure
```

**Proposition:** Worker temporary pre-compile call frames: Return or process exit; no claim of byte erasure

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The table says a frame returns or the process exits; it does not positively describe wiping those frame bytes. Released as a resource-lifetime heading is insufficient for the exact byte-erasure inference.

**Secondary role:** A1: the same cell also gives the actual resource/lifetime account; the unknown or proof limitation is primary here.

**Blocked inference:** Returning from the precompile frame proves its bytes were erased.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:8668](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N9a, column 8. Owning manifest graph worker_capabilities, item n9a; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N268

[docs/WORKER.md:145](../../docs/WORKER.md) · medium confidence

```text
Source-only; qsort/CommonCrypto internals unobserved
```

**Proposition:** Capture hash/view/digest/sorting call frames: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:8715](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory N9b; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item n9b; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N270

[docs/WORKER.md:145](../../docs/WORKER.md) · high confidence

```text
Return or process exit; no claim of byte erasure
```

**Proposition:** Capture hash/view/digest/sorting call frames: Return or process exit; no claim of byte erasure

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Capture/hash frame lifetime is described, but no positive wiping operation or byte-erasure guarantee is supplied for these automatic frames.

**Secondary role:** A1: the same cell also gives the actual resource/lifetime account; the unknown or proof limitation is primary here.

**Blocked inference:** Returning from the capture/hash frame proves its bytes were erased.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:8713](../../docs/architecture.json).

**Notes:** Family: inventory-resource-constraints. Inventory N9b, column 8. Owning manifest graph worker_capabilities, item n9b; manifest value is a duplicate occurrence, not another entry. Independent review: agree; see trigger-review.json by ID.

#### N272

[docs/WORKER.md:146](../../docs/WORKER.md) · medium confidence

```text
Source-only; compiler stack/page behavior unobserved
```

**Proposition:** Attempt-local stack buffers, argv pointers, polls, wait status and metadata: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:8744](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory N10; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item n10; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N276

[docs/WORKER.md:147](../../docs/WORKER.md) · medium confidence

```text
Source-only
```

**Proposition:** Post-apply outside-attempt automatic diagnostics and seam timespec: the gating/observation account has exactly the stated source, observed or unknown scope.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** The cited 'Sandbox-gated' header names the subject of this cell; it does not assert that this resource was empirically gated, that its test was run, or that private/live state was measured. A same-row check citation can invite an assertion-coverage reading (N057), but is not by itself the exact live-observation claim limited here. No independent affirmative local trigger for this cell's narrower source/observation limit was identified.

**Secondary role:** A1 only insofar as the same cell names actual call placement or an observed configuration; evidential scope is the primary limiting role.

**Blocked inference:** The source-scoped or specifically bounded account is a direct runtime observation or a more complete measurement than the text reports.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:8777](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope. Inventory N11; specific column qualifier, not an assertion that the resource is absent. Owning manifest graph worker_capabilities, item n11; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N307

[docs/WORKER.md:107](../../docs/WORKER.md) · medium confidence

```text
full live right census unavailable
```

**Proposition:** A full live initial-Mach-right census is unavailable.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Freshness says which specimen owns the process, not that all its Mach rights were inspected. The initial-rights row explicitly names other rights without enumerating them.

**Blocked inference:** The worker’s complete initial Mach-right census is known.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7545](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope.  Owning manifest graph worker_capabilities, item s16e; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.

#### N309

[docs/WORKER.md:108](../../docs/WORKER.md) · medium confidence

```text
Before compilation initially; later internal changes unknown
```

**Proposition:** Later runtime-image/internal changes have unknown acquisition timing.

**Context:** resource-specific generated cell; the complete row is retained in `inventory.json`.

**Classification:** Already-present executable/library mappings and a fresh process do not assert no later internal change or complete acquisition timing. The generic freshness trigger misses the exact timing inference.

**Blocked inference:** The acquisition timing of all later runtime/library internal changes is known.

**External origin (unknown):** Unknown. A general source-versus-observation or native-state misconception is only a hypothetical motivation; no historical origin is established.

**Associated occurrences:** [docs/architecture.json:7572](../../docs/architecture.json).

**Notes:** Family: inventory-evidence-scope.  Owning manifest graph worker_capabilities, item s16f; manifest value is a duplicate occurrence, not another entry. Independent review: change; see trigger-review.json by ID.


## Candidates excluded at scope review

These remain visible for coverage and traceability; they are outside the primary bucket counts.

### N038

[docs/WORKER.md:440–443](../../docs/WORKER.md)

```text
belongs to the host. In issuer [`main`](../controller/tools/pw_probe_runner/pw_extension_issuer.c),
bounded length inspection governs copying and erasure before free. An oversized
token is rejected and that inspected prefix is erased; the allocation extent
beyond the bound is unobserved.
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N083

[docs/WORKER.md:83](../../docs/WORKER.md)

```text
Source-only
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N085

[docs/WORKER.md:84](../../docs/WORKER.md)

```text
Source-only
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N087

[docs/WORKER.md:85](../../docs/WORKER.md)

```text
Source-only; no live issuer case rerun in pass 1
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N089

[docs/WORKER.md:86](../../docs/WORKER.md)

```text
Source-only
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N091

[docs/WORKER.md:87](../../docs/WORKER.md)

```text
Source-only
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N092

[docs/WORKER.md:87](../../docs/WORKER.md)

```text
Normal munmap; malformed header exits without explicit unmap
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N094

[docs/WORKER.md:88](../../docs/WORKER.md)

```text
Source-only
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N096

[docs/WORKER.md:89](../../docs/WORKER.md)

```text
Source-only
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N097

[docs/WORKER.md:89](../../docs/WORKER.md)

```text
Until exit; no explicit dlclose
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N098

[docs/WORKER.md:89](../../docs/WORKER.md)

```text
Loader/process teardown; internals unobserved
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N099

[docs/WORKER.md:89](../../docs/WORKER.md)

```text
Makes private issuance API callable, not an entitlement grant
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead. If scope were broadened, callable-symbol availability versus entitlement grant also deserves an A1/B1 clause review; the gold authority cluster could invite that inference. The present exclusion does not settle that broader classification.

### N101

[docs/WORKER.md:90](../../docs/WORKER.md)

```text
Source-only
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N102

[docs/WORKER.md:90](../../docs/WORKER.md)

```text
Automatic values end with I; no independent handle release
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N103

[docs/WORKER.md:90](../../docs/WORKER.md)

```text
API entry points; consume/release are checked, not invoked
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N105

[docs/WORKER.md:91](../../docs/WORKER.md)

```text
Source-only; private internals unobserved
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N106

[docs/WORKER.md:91](../../docs/WORKER.md)

```text
Copy/reject decision only
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N245

[docs/WORKER.md:136](../../docs/WORKER.md)

```text
Source-only
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N249

[docs/WORKER.md:139](../../docs/WORKER.md)

```text
Source-only, issuer outside specimen sandbox
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N252

[docs/WORKER.md:140](../../docs/WORKER.md)

```text
Spawn call only
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### N255

[docs/WORKER.md:141](../../docs/WORKER.md)

```text
Source-only; Swift allocation internals unobserved
```

This occurrence concerns the issuer/host’s own allocation, handle, cleanup, source/observation provenance or internal state. It does not itself assert what the worker receives, holds, does, can inherit or cannot access. Membership in the worker-capability map does not turn it into a worker proposition. Keep it as explicit excluded supporting-apparatus context; do not force it into B1 instead.

### F002

[docs/WORKER.md:91](../../docs/WORKER.md)

```text
I bounded erase then free; oversized tail caveat
```

The native issuer allocation is not worker storage. Its bounded erase/free behavior and oversized-tail caveat do not themselves assert a worker behavior, delivered-resource boundary or worker evidence limit. The related original N038 has the same scope issue.

### F006

[docs/WORKER.md:139](../../docs/WORKER.md)

```text
Read EOF/write discard
```

Issuer stdin/stdout/stderr EOF/discard behavior is solely issuer behavior; it describes neither worker stdio nor a worker transfer boundary. It is supporting-apparatus context, not A1 about the worker.
