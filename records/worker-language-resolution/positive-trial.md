# Worker language: pre-RCA positive-reframing trial

Frozen against `672374c38b2b728719510300ced1090f1e0e35ef`. This round covers all 15 remaining decision units from `records/worker-language-triage/ledger.json`, before any RCA. No document/machinery repairs, history searches, runtime tests or RCAs were performed. This is not pass 6.

`positive-trial.json` preserves the complete machine-readable alternatives and exact source ranges. Original blocks below are verbatim; candidate text is a draft, never an applied edit. Read each candidate in its unchanged surrounding section. For headings/captions, the positive fact concerns documentation machinery; for runtime passages it concerns the worker or the explicitly named observer/fixture.

## Results

**8 positive wins; 3 elision wins; 0 original wins; 4 cannot decide before RCA.**

N004.cleanup and N239 require the release-action heading; N216.creation also needs its W41 status label corrected; N299 requires W50 removal. Thus several winners require repair of the premise, beyond a sentence substitution. All four D2 clauses still require the three bounded purpose investigations.

| Unit | Preferred trial | Reason |
| --- | --- | --- |
| N004.cleanup | positive | The concrete subject is the table and its worker/host cleanup actions |
| N005 | elision | The preceding clause already says precisely what the C harness checks |
| N017 | positive | The positive wording identifies the actor and observable behavior: the fixture adapters record uses and return EINVAL |
| N019 | positive | Both deletion and positive revision retain the observed fd collision |
| N025 | positive | The positive version gives the useful worker fact at its action: which native operation determines published attempt status |
| N051 | elision | The positive table version states the worker event order directly, but repeats the concrete create-then-kill paragraph and lengthens this reply-assembly row |
| N057 | positive | This is a positive fact about WORKER machinery rather than a worker runtime fact: it states the operations the generator performs |
| N122 | positive | The positive version names the actual endpoint observation and the specific L configuration |
| N164 | cannot decide | A positive source fact establishes the worker mapping call, while L records VM-region observations |
| N203 | cannot decide | The positive alternative states the worker event order and inherited constraints |
| N216.creation | positive | The positive version names the conditional filesystem acquisition and repairs the recorded trigger, W41 |
| N239 | positive | With the positive action heading, the entry describes what the worker requests |
| N266 | cannot decide | Both alternatives preserve the automatic frame lifetime and remove the separate byte-erasure topic |
| N270 | cannot decide | Both alternatives preserve the automatic frame lifetime and remove the separate byte-erasure topic |
| N299 | elision | The positive wording supplies accurate event facts but W50 still directs an observes edge from path diagnostics to the newly created object |

## N004.cleanup

<details>
<summary>Exact original context</summary>

`docs/WORKER.md:49–58` at `672374c`:

```text
In the table, H is the host, W the worker, E the host's extension session and I
the issuer. P means reporting apparatus, A supplied authority or restriction,
and O operation acquisitions. L is the recorded production launch observation;
IC and CLI are the contaminated-worker and ordinary exec-child controls in the
[inheritance suite](../tests/suites/runner_exec_inheritance/README.md).
Acquisition periods record call-site placement. Gating claims retain their
observed, source-only or unknown scope. Cleanup entries name calls; retained
native returns establish their observed outcomes where available. Process exit
reclaims that process's remaining references; created files and references held
by other processes have their own lifetimes.
```

`docs/WORKER.md:70–70` at `672374c`:

```text
| Id | Node | Kind | Inventory ID | Acquired by | When | Held across | Released | Authority | Sandbox-gated | Reaches exec children | Role | Sources | Checks | Limits |
```

</details>

**Positive trial**

```text
In the table, H is the host, W the worker, E the host's extension session and I
the issuer. P means reporting apparatus, A supplied authority or restriction,
and O operation acquisitions. L is the recorded production launch observation;
IC and CLI are the contaminated-worker and ordinary exec-child controls in the
[inheritance suite](../tests/suites/runner_exec_inheritance/README.md).
Acquisition periods record call-site placement. Gating claims retain their
observed, source-only or unknown scope. The release / teardown action column identifies the calls requested by the
host or worker and records their retained outcomes where available. Process exit
reclaims that process's remaining references; created files and references held
by other processes have their own lifetimes.

Table heading: Release / teardown action
```

**Elision trial**

```text
In the table, H is the host, W the worker, E the host's extension session and I
the issuer. P means reporting apparatus, A supplied authority or restriction,
and O operation acquisitions. L is the recorded production launch observation;
IC and CLI are the contaminated-worker and ordinary exec-child controls in the
[inheritance suite](../tests/suites/runner_exec_inheritance/README.md).
Acquisition periods record call-site placement. Gating claims retain their
observed, source-only or unknown scope. Process exit
reclaims that process's remaining references; created files and references held
by other processes have their own lifetimes.

Table heading: Released
```

**Verdict: positive.** The concrete subject is the table and its worker/host cleanup actions. The positive passage accurately names what the entries record; it is not a generic claim that all release succeeds. The shorter preferred implementation is to retain the positive heading and elide the explanatory sentence: the entries already supply the facts. Pure elision under Released retains the achieved-outcome ambiguity.

**What elision loses:** Pure elision loses the explicit interpretation of cleanup entries as requested calls. Changing the heading restores that interpretation without a separate caution. Process-exit and other-reference lifetimes remain in both passages.

**Support:** `docs/architecture.json: worker_capabilities.node_facts and all Released values`; `docs/WORKER.md:49–58,134`.

Implementation conditions:

- Rename the owning manifest key and heading together, retaining every value except separately adjudicated wording.
- Review all entries under the new heading, including the temporary-frame entries whose purpose remains pending Q03.


## N005

<details>
<summary>Exact original context</summary>

`docs/WORKER.md:231–240` at `672374c`:

```text
The host's [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) creates
an evidence object, requests its immediate unlink, sizes and maps it, initializes
the request and touches its pages. The worker's
[`map_region`](../controller/tools/pw_probe_runner/pw_probe_runner.c) maps the
received descriptor before compilation. The mapping holds request data,
publication payloads and atomic control fields. The host's mapping remains
available during collection even when worker cleanup is unconfirmed. The
[C harness](../tests/suites/runner_c_worker_harness/README.md) checks publication
under its bare-deny and full-region cases; that assertion scope belongs beside
the source account of preparation.
```

</details>

**Positive trial**

```text
The host's [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) creates
an evidence object, requests its immediate unlink, sizes and maps it, initializes
the request and touches its pages. The worker's
[`map_region`](../controller/tools/pw_probe_runner/pw_probe_runner.c) maps the
received descriptor before compilation. The mapping holds request data,
publication payloads and atomic control fields. The host's mapping remains
available during collection even when worker cleanup is unconfirmed. The
[C harness](../tests/suites/runner_c_worker_harness/README.md) checks publication
under its bare-deny and full-region cases. These cases exercise the worker publication path described here.
```

**Elision trial**

```text
The host's [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) creates
an evidence object, requests its immediate unlink, sizes and maps it, initializes
the request and touches its pages. The worker's
[`map_region`](../controller/tools/pw_probe_runner/pw_probe_runner.c) maps the
received descriptor before compilation. The mapping holds request data,
publication payloads and atomic control fields. The host's mapping remains
available during collection even when worker cleanup is unconfirmed. The
[C harness](../tests/suites/runner_c_worker_harness/README.md) checks publication
under its bare-deny and full-region cases.
```

**Verdict: elision.** The preceding clause already says precisely what the C harness checks. A positive replacement repeats that statement and adds no worker fact. Elision leaves a coherent description with the exact case names and cited source account.

**What elision loses:** Only the editorial instruction that assertion scope belongs beside preparation; publication coverage and preparation facts remain.

**Support:** `docs/WORKER.md:231–240`; `tests/suites/runner_c_worker_harness/README.md: bare-deny and full-region publication cases`.

Implementation conditions:

- Coordinate with N057 so cited check definitions are described as definitions, rather than whole-row assertion coverage.


## N017

<details>
<summary>Exact original context</summary>

`docs/WORKER.md:319–327` at `672374c`:

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

</details>

**Positive trial**

```text
The [host setup controls](../tests/suites/runner_unit/README.md#host-setup-failures-and-descriptor-collisions)
exercise these boundaries in disposable source copies with an independent child
observer. Injected worker action-add failures allow a child to run with a wrong
endpoint; failed argument copies allow empty or truncated argv. Injected unlink
failures leave shared-memory names after owner teardown. The checked worker
pipe-flag and issuer action/attribute-flag failures prevent spawn and clean up
in the exercised cases. After a failed handle initialization, fixture adapters record the host's
subsequent invalid-handle uses and return EINVAL. Their receipts record the
continued host flow through those adapter calls.
```

**Elision trial**

```text
The [host setup controls](../tests/suites/runner_unit/README.md#host-setup-failures-and-descriptor-collisions)
exercise these boundaries in disposable source copies with an independent child
observer. Injected worker action-add failures allow a child to run with a wrong
endpoint; failed argument copies allow empty or truncated argv. Injected unlink
failures leave shared-memory names after owner teardown. The checked worker
pipe-flag and issuer action/attribute-flag failures prevent spawn and clean up
in the exercised cases.
```

**Verdict: positive.** The positive wording identifies the actor and observable behavior: the fixture adapters record uses and return EINVAL. That removes the misleading suggestion that the control exercised native libc on invalid handles. Pure deletion removes a distinct unchecked-initialization observation. Keeping the first invalid-handle sentence while deleting only its guard would be an incomplete elision and would retain the ambiguity.

**What elision loses:** The fact that failed handle initialization reaches later host calls, and the adapter containment which makes this observation meaningful.

**Support:** `tests/fixtures/host_setup/README.md:27–33 (nil handle; adapters record invalid use and return EINVAL)`; `docs/WORKER.md:311–327`.

Implementation conditions:

- Retain the existing fixture/control links and unchecked-production-setup paragraph.
- Do not convert fixture EINVAL into a claimed native libc return.


## N019

<details>
<summary>Exact original context</summary>

`docs/WORKER.md:329–336` at `672374c`:

```text
Descriptor order also matters without injected native failure. With stdin closed
in the low-descriptor control, evidence is allocated at fd 0. The policy action
overwrites it before the evidence action reads that number: the child receives
a policy pipe at fd 3. Its readiness source equals its destination and remains
close-on-exec in this observation, leaving fd 4 absent. The issuer's separate
high-duplicate control preserves its channel under the exercised low-descriptor
arrangement. These controlled launches do not establish that an ordinary XPC
host starts with the same descriptor arrangement.
```

</details>

**Positive trial**

```text
Descriptor order also matters without injected native failure. The low-descriptor fixture deliberately closes stdin and low unused
descriptors before exercising launch setup. In that configuration, evidence is
allocated at fd 0. The policy action
overwrites it before the evidence action reads that number: the child receives
a policy pipe at fd 3. Its readiness source equals its destination and remains
close-on-exec in this observation, leaving fd 4 absent. The issuer's separate
high-duplicate control preserves its channel under the exercised low-descriptor
arrangement.
```

**Elision trial**

```text
Descriptor order also matters without injected native failure. With stdin closed
in the low-descriptor control, evidence is allocated at fd 0. The policy action
overwrites it before the evidence action reads that number: the child receives
a policy pipe at fd 3. Its readiness source equals its destination and remains
close-on-exec in this observation, leaving fd 4 absent. The issuer's separate
high-duplicate control preserves its channel under the exercised low-descriptor
arrangement.
```

**Verdict: positive.** Both deletion and positive revision retain the observed fd collision. The positive version is preferable because it identifies the deliberate fixture intervention before the result, which supplies the configuration directly. An ordinary-host comparison then contributes no necessary fact.

**What elision loses:** The explicit warning against generalizing to an ordinary XPC launch. The chosen positive version supplies the setup that makes the observation meaningful.

**Support:** `tests/fixtures/host_setup/README.md:10–15`; `docs/WORKER.md:329–336`.

Implementation conditions:

- Retain the exact wrong fd 3 and absent fd 4 observations and the issuer high-duplicate control.


## N025

<details>
<summary>Exact original context</summary>

`docs/WORKER.md:351–363` at `672374c`:

```text
| Action | Call and retained observation |
| --- | --- |
| [`attempt_file_open_read`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens read-only, attempts a one-byte read and close, and discards those latter returns. Published success is the open result, with an available descriptor-path observation. |
| [`attempt_file_open_write`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens with `O_WRONLY \| O_TRUNC`, then attempts to write `x` and close. Published success is the open result; the write and close returns are discarded. |
| [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens with `O_WRONLY \| O_CREAT` and mode argument `0600`, subject to inherited umask. Existing targets are opened without truncation; missing targets can be created. Close is attempted and its return discarded. |
| [`attempt_file_read_fresh`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens a fresh close-on-exec descriptor and retains open, metadata, bounded read and single-close results, including partial native evidence when a later call fails. |

The [existing-file control](../tests/suites/witness_contract/README.md#create-on-an-existing-file)
checks preserved bytes and object identity in its case. The
[fresh-read contract](PolicyWitness.md#extension-and-fresh-read-output) defines
which native observations and bounded bytes reach the reply. The source
establishes where each call occurs and which returns are discarded; those are
separate from an independently observed filesystem effect.
```

</details>

**Positive trial**

```text
| Action | Call and retained observation |
| --- | --- |
| [`attempt_file_open_read`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens read-only. The open result determines the published attempt status. On successful open, records an available descriptor-path observation, attempts a one-byte read and close, and discards those latter returns. |
| [`attempt_file_open_write`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens with `O_WRONLY \| O_TRUNC`. The open result determines the published attempt status. On successful open, attempts to write `x` and close and discards their returns. |
| [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens with `O_WRONLY \| O_CREAT` and mode argument `0600`, subject to inherited umask. Existing targets are opened without truncation; missing targets can be created. Close is attempted and its return discarded. |
| [`attempt_file_read_fresh`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens a fresh close-on-exec descriptor and retains open, metadata, bounded read and single-close results, including partial native evidence when a later call fails. |

The [existing-file control](../tests/suites/witness_contract/README.md#create-on-an-existing-file)
checks preserved bytes and object identity in its case. The
[fresh-read contract](PolicyWitness.md#extension-and-fresh-read-output) defines
which native observations and bounded bytes reach the reply.
```

**Elision trial**

```text
| Action | Call and retained observation |
| --- | --- |
| [`attempt_file_open_read`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens read-only, attempts a one-byte read and close, and discards those latter returns. Published success is the open result, with an available descriptor-path observation. |
| [`attempt_file_open_write`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens with `O_WRONLY \| O_TRUNC`, then attempts to write `x` and close. Published success is the open result; the write and close returns are discarded. |
| [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens with `O_WRONLY \| O_CREAT` and mode argument `0600`, subject to inherited umask. Existing targets are opened without truncation; missing targets can be created. Close is attempted and its return discarded. |
| [`attempt_file_read_fresh`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens a fresh close-on-exec descriptor and retains open, metadata, bounded read and single-close results, including partial native evidence when a later call fails. |

The [existing-file control](../tests/suites/witness_contract/README.md#create-on-an-existing-file)
checks preserved bytes and object identity in its case. The
[fresh-read contract](PolicyWitness.md#extension-and-fresh-read-output) defines
which native observations and bounded bytes reach the reply.
```

**Verdict: positive.** The positive version gives the useful worker fact at its action: which native operation determines published attempt status. Pure deletion leaves Published success attached to action names that include read/write, inviting an overbroad effect interpretation. The independent existing-file control still has its own concrete observation.

**What elision loses:** The generic source-versus-filesystem-effect distinction. The positive version preserves its useful application through precise status and discarded-return facts.

**Support:** `controller/tools/pw_probe_runner/pw_probe_runner.c: attempt_file_open_read, attempt_file_open_write`; `docs/WORKER.md:353–363`; `docs/PolicyWitness.md: attempt status fields (PW status, not a raw syscall return)`.

Implementation conditions:

- Cross-check source order for descriptor-path recording/read/close before application.
- Keep attempt status distinct from a raw native return.
- Coordinate N216.creation and W41 status wording.


## N051

<details>
<summary>Exact original context</summary>

`docs/WORKER.md:466–476` at `672374c`:

```text
A native call and publication are distinct boundaries.
[`pw_progress`](../controller/tools/pw_probe_runner/pw_worker_evidence.h)
records the latest atomic milestone, while
[`run_attempt`](../controller/tools/pw_probe_runner/pw_probe_runner.c)
releases the completed slot after writing its payload. The host reads completed
payload after observing publication. The
[create-then-kill control](../tests/suites/witness_contract/README.md#death-after-the-native-return-before-publication)
independently observes the created file while requiring the reply to withhold
the unpublished result. Partially written payload remains outside the evidence
the host is entitled to decode. Native call-boundary flags and result publication
have the meanings in the [worker evidence contract](../tests/FAILURE-PROPAGATION-CONTRACT.md#worker-evidence-contract).
```

`docs/WORKER.md:510–510` at `672374c`:

```text
| Move reply assembly into the worker or use missing publication as proof of no effect | Couples reporting to specimen-controlled communication or substitutes absence of evidence | The host reads released payload; [death before publication](../tests/suites/witness_contract/README.md#death-after-the-native-return-before-publication) preserves an independently observed effect with a withheld result. |
```

</details>

**Positive trial**

```text
| Move reply assembly into the worker | Couples reporting to specimen-controlled communication | Worker calls can complete before their result slots are published. The host reads released payload; [death before publication](../tests/suites/witness_contract/README.md#death-after-the-native-return-before-publication) preserves an independently observed effect with a withheld result. |
```

**Elision trial**

```text
| Move reply assembly into the worker | Couples reporting to specimen-controlled communication | The host reads released payload; [death before publication](../tests/suites/witness_contract/README.md#death-after-the-native-return-before-publication) preserves an independently observed effect with a withheld result. |
```

**Verdict: elision.** The positive table version states the worker event order directly, but repeats the concrete create-then-kill paragraph and lengthens this reply-assembly row. Elision removes the repeated issue from the proposed-change columns while retaining the reply-assembly example and its concrete evidence cell. For the earlier paragraph, the useful positive opening is: A native call can complete before the worker publishes the attempt slot.

**What elision loses:** A duplicate change-table warning, not the independent created-file observation or the publication boundary.

**Support:** `docs/WORKER.md:466–478,510`.

Implementation conditions:

- Keep the create-then-kill counterexample and its link intact.
- The earlier positive event-order opening is an optional concise improvement, not a new claim.


## N057

<details>
<summary>Exact original context</summary>

`docs/WORKER.md:63–66` at `672374c`:

```text
*Figure: worker capabilities. Generated from [architecture.json](architecture.json) by [generate_architecture.py](generate_architecture.py); dot source in [worker-capabilities.dot](worker-capabilities.dot). The ids in the figure are the ids in the tables below, and each row cites the source symbol that implements it and the test or rule the manifest names for it. Symbol presence and test definition are verified; whether a test asserts the row is not verified.*

<details>
<summary>Worker capabilities: 83 nodes and 55 edges, with symbol presence and test definition verified; whether a test asserts the row is not verified</summary>
```

`docs/WORKER.md:70–70` at `672374c`:

```text
| Id | Node | Kind | Inventory ID | Acquired by | When | Held across | Released | Authority | Sandbox-gated | Reaches exec children | Role | Sources | Checks | Limits |
```

</details>

**Positive trial**

```text
*Figure: worker capabilities. Generated from [architecture.json](architecture.json) by [generate_architecture.py](generate_architecture.py); dot source in [worker-capabilities.dot](worker-capabilities.dot). Figure IDs correspond to the table IDs. Each row lists source references and cited test or rule definitions. The generator checks source-symbol presence and resolves those definitions.*

<details>
<summary>Worker capabilities: 83 nodes and 55 edges; source symbols and cited definitions checked</summary>

Citation column: Cited check definitions
```

**Elision trial**

```text
*Figure: worker capabilities. Generated from [architecture.json](architecture.json) by [generate_architecture.py](generate_architecture.py); dot source in [worker-capabilities.dot](worker-capabilities.dot). The ids in the figure are the ids in the tables below, and each row cites the source symbol that implements it and the test or rule the manifest names for it.*

<details>
<summary>Worker capabilities: 83 nodes and 55 edges</summary>

Citation column: Checks
```

**Verdict: positive.** This is a positive fact about WORKER machinery rather than a worker runtime fact: it states the operations the generator performs. It avoids promising that a cited test proves a resource row. Pure deletion leaves the source/check pairing and loses the useful account of mechanical validation.

**What elision loses:** Mechanical citation-check behavior disappears with pure elision; row-level source/assertion/execution distinctions remain elsewhere but should not have to substitute for an accurate caption.

**Support:** `docs/generate_architecture.py:55–60,211–223,347–402`; `docs/generator_common.py: citation resolution helpers`.

Implementation conditions:

- Render the worker-specific caption, summary and check-column label without changing other documents.
- Keep the shared generator validation and source-review obligations.
- Preserve generated counts; no whole-row coverage claim.


## N122

<details>
<summary>Exact original context</summary>

`docs/WORKER.md:97–97` at `672374c`:

```text
| s14a | Worker inherited stdout/stderr | mixed | S14a | H spawn, without replacement file actions | Before compilation | Until exit | Exit; no explicit W close | Whatever underlying endpoints allow; L saw read/write /dev/null | L presence only; no universal stdio rule | No: exec-child capture pipes replace 1/2 | none | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift) | [`launch_inventory`](../tests/suites/runner_exec_inheritance/run.sh) |  |
```

`docs/WORKER.md:283–298` at `672374c`:

```text

Host spawn actions select the policy, evidence and readiness endpoints, plus
the optional token endpoint. The worker launch uses nil spawn attributes and
leaves other descriptors to native close-on-exec inheritance. Its standard
output/error are inherited, and the evidence descriptor can also survive under
its original number if later file actions leave that number intact. The host
passes nil envp. The examined Apple
[spawn wrapper](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/libsyscall/wrappers/spawn/posix_spawn.c)
forwards that pointer and the examined
[exec path](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/kern/kern_exec.c)
constructs an empty environment. The recorded launch observation found matching
plain and environment-displaying process output, inherited null-device standard
output/error, and the expected protocol endpoints. The contaminated-worker
control separately establishes a configuration in which an extra descriptor
and environment value reach the worker.

```

</details>

**Positive trial**

```text

Host spawn actions select the policy, evidence and readiness endpoints, plus
the optional token endpoint. The worker launch uses nil spawn attributes and
leaves other descriptors to native close-on-exec inheritance. Its standard
output/error are inherited, and the evidence descriptor can also survive under
its original number if later file actions leave that number intact. The host
passes nil envp. The examined Apple
[spawn wrapper](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/libsyscall/wrappers/spawn/posix_spawn.c)
forwards that pointer and the examined
[exec path](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/kern/kern_exec.c)
constructs an empty environment. The recorded production launch case used an empty allow-default specimen.
Its observation found matching plain and environment-displaying process output,
inherited null-device standard output/error, and the expected protocol endpoints. The contaminated-worker
control separately establishes a configuration in which an extra descriptor
and environment value reach the worker.


S14a Sandbox-gated: L: inherited null-device stdout/stderr observed
```

**Elision trial**

```text

Host spawn actions select the policy, evidence and readiness endpoints, plus
the optional token endpoint. The worker launch uses nil spawn attributes and
leaves other descriptors to native close-on-exec inheritance. Its standard
output/error are inherited, and the evidence descriptor can also survive under
its original number if later file actions leave that number intact. The host
passes nil envp. The examined Apple
[spawn wrapper](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/libsyscall/wrappers/spawn/posix_spawn.c)
forwards that pointer and the examined
[exec path](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/kern/kern_exec.c)
constructs an empty environment. The recorded launch observation found matching
plain and environment-displaying process output, inherited null-device standard
output/error, and the expected protocol endpoints. The contaminated-worker
control separately establishes a configuration in which an extra descriptor
and environment value reach the worker.


S14a Sandbox-gated: L presence only
```

**Verdict: positive.** The positive version names the actual endpoint observation and the specific L configuration. The absence of a universal-stdio claim follows from describing one observation. Pure deletion leaves the terse presence-only cell readable, but throws away an opportunity to state which worker endpoints were observed.

**What elision loses:** The explicit anti-generalization wording. The selected positive formulation preserves the actual observation and source-level inheritance account.

**Support:** `tests/suites/runner_exec_inheritance/README.md: production launch inventory (two workers, empty allow-default plan)`; `docs/WORKER.md:97,284–298`.

Implementation conditions:

- Keep the separate contaminated-worker observation and independent source inheritance account.
- Do not imply that allow-default caused the null-device endpoints.


## N164

<details>
<summary>Exact original context</summary>

`docs/WORKER.md:110–110` at `672374c`:

```text
| s18 | Worker evidence base mapping | reporting | S18 | map_region: fstat, mmap(MAP_SHARED) | Before compilation | Later attempts/phases, until exit | No explicit W unmap; exit | Read requests, publish results, observe release/exit | L shared mappings observed; no mapping-identity attribution from size alone | No: exec replaces mappings and excludes fd 3 | P | [`map_region`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`launch_inventory`](../tests/suites/runner_exec_inheritance/run.sh) |  |
```

</details>

**Positive trial**

```text
Resource: Worker evidence base mapping
Acquired by: map_region: fstat, mmap(MAP_SHARED)
When: Before compilation
Held across: Later attempts/phases, until exit
Sandbox-gated: Source: map_region maps the received evidence descriptor before compilation; L records shared mapping regions
```

**Elision trial**

```text
Resource: Worker evidence base mapping
Acquired by: map_region: fstat, mmap(MAP_SHARED)
When: Before compilation
Held across: Later attempts/phases, until exit
Sandbox-gated: L shared mappings observed
```

**Verdict: cannot decide.** A positive source fact establishes the worker mapping call, while L records VM-region observations. Neither phrasing identifies a particular observed region as this resource. Both alternatives, placed in S18, may still lend that row specific runtime credit. Wording alone does not settle whether the original caution corrects an actual attribution in the retained observations.

**What elision loses:** The specific constraint on identifying a mapping by size. That could be useful if a retained mapping was credited by size; it could be redundant if no such attribution exists.

**Support:** `docs/WORKER.md:110,231–236,338–345`; `docs/architecture.json: worker_capabilities s18`.

Implementation conditions:

- Keep the source map_region account regardless of the runtime attribution result.
- Do not replace an unverified mapping identity with a new positive identification.

**Focused RCA question:** In the retained launch observations or interpretation notes, what exact mapping is attributed to S18, and on what identifiers? If none is attributed, what reader-visible fact currently supplies the size-based inference?


## N203

<details>
<summary>Exact original context</summary>

`docs/WORKER.md:121–121` at `672374c`:

```text
| s28 | Applied sandbox policy | authority | S28 | W: sandbox_apply(profile) | Between compilation and apply closing boundary | All later attempts/phases, until exit on success | One-way, no undo | Restricts starting authority; extension may augment access | Source placement; L final application/clean completion, not deny coverage | Inherited sandbox constraints; exact child policy effects not inventoried here | A | [`main`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`bare_deny_default`](../tests/suites/runner_c_worker_harness/run.sh) |  |
```

</details>

**Positive trial**

```text
Resource: Applied sandbox policy
Acquired by: W: sandbox_apply(profile)
When: Between compilation and apply closing boundary
Held across: All later attempts/phases, until exit on success
Reaches exec children: The worker applies the specimen before its exec attempts; exec children inherit sandbox constraints
```

**Elision trial**

```text
Resource: Applied sandbox policy
Acquired by: W: sandbox_apply(profile)
When: Between compilation and apply closing boundary
Held across: All later attempts/phases, until exit on success
Reaches exec children: Inherited sandbox constraints
```

**Verdict: cannot decide.** The positive alternative states the worker event order and inherited constraints. It is readable and more concrete than an undefined inventory limit, but it leaves the same unanswered distinction between inherited constraints and exact effective access. Wording cannot decide which child-policy inference motivated the added clause.

**What elision loses:** The unspecified statement about omitted exact child policy effects. Its value depends on whether it addresses a definite proposition or only a general wish for more coverage.

**Support:** `docs/WORKER.md:121,365 onward`; `docs/architecture.json: worker_capabilities s28`.

Implementation conditions:

- Keep inherited constraints and the worker apply-before-exec fact.
- Do not strengthen inherited constraints into identity of parent/child effective permissions.

**Focused RCA question:** Define exact child policy effects: is the concern parent/child effective-access equivalence, completeness of operations, or another proposition? Which present passage invites that proposition?


## N216.creation

<details>
<summary>Exact original context</summary>

`docs/WORKER.md:125–125` at `672374c`:

```text
| s31b | Newly created filesystem object, if absent | operation | S31b | attempt_file_create: same open | After apply within an attempt | Later attempts/phases and beyond worker exit | No automatic unlink; later action/external actor may remove | Persistent filesystem effect, mode subject to umask | Source-only; creation not implied for existing target | Child can resolve it by path, not inherited fd | O | [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`create_existing_file_preserves_contents`](../tests/suites/witness_contract/run.sh) |  |
```

`docs/WORKER.md:200–200` at `672374c`:

```text
| W41 | s31a | s18 | publishes | Publishes open/create status | [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`create_existing_file_preserves_contents`](../tests/suites/witness_contract/run.sh) |  |
```

`docs/WORKER.md:355–355` at `672374c`:

```text
| [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | Opens with `O_WRONLY \| O_CREAT` and mode argument `0600`, subject to inherited umask. Existing targets are opened without truncation; missing targets can be created. Close is attempted and its return discarded. |
```

</details>

**Positive trial**

```text
Resource: Newly created filesystem object, if absent
Acquired by: attempt_file_create: same open
When: After apply within an attempt
Held across: Later attempts/phases and beyond worker exit
Authority: Persistent filesystem effect, mode subject to umask
Sandbox-gated: Source-only; open(O_CREAT) can create an absent target
W41: Publishes file-create attempt status from open result
```

**Elision trial**

```text
Resource: Newly created filesystem object, if absent
Acquired by: attempt_file_create: same open
When: After apply within an attempt
Held across: Later attempts/phases and beyond worker exit
Authority: Persistent filesystem effect, mode subject to umask
Sandbox-gated: Source-only
W41: Publishes open/create status
```

**Verdict: positive.** The positive version names the conditional filesystem acquisition and repairs the recorded trigger, W41. Elision alone leaves open/create status sounding like new-object evidence. The authored create row already states existing-target behavior, so there is no need for another negation.

**What elision loses:** The direct warning that status does not establish new-object creation. Conditional acquisition plus a precise status edge supplies the same useful distinction.

**Support:** `controller/tools/pw_probe_runner/pw_probe_runner.c: attempt_file_create`; `docs/WORKER.md:125,200,355`; `docs/architecture.json: s31b and W41`.

Implementation conditions:

- Add W41 label repair to R05; the earlier package changed S31b but left its recorded trigger intact.
- Preserve the file-create action name, existing-target behavior and independent existing-file control.
- Keep Source-only as the retained evidence-scope fact.


## N239

<details>
<summary>Exact original context</summary>

`docs/WORKER.md:134–134` at `672374c`:

```text
| s36b | Child process group | reporting | S36b | Exec spawn attributes SETPGROUP, pgroup 0 | After apply within an attempt | As long as members remain, possibly beyond attempt/worker | Conditional group kill request, not an absence proof | Cleanup addressing for members that remain | Source-only; lifecycle cases inspected, not rerun | Yes to descendants unless they leave group | P | [`exec_resources_acquire`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`exec_pipes_per_attempt`](../tests/suites/runner_c_worker_harness/run.sh); [`contaminated_worker`](../tests/suites/runner_exec_inheritance/run.sh) |  |
```

</details>

**Positive trial**

```text
Resource: Child process group
Acquired by: Exec spawn attributes SETPGROUP, pgroup 0
Held across: As long as members remain, possibly beyond attempt/worker
Release / teardown action: Conditional process-group kill request
Authority: Cleanup addressing for members that remain
```

**Elision trial**

```text
Resource: Child process group
Acquired by: Exec spawn attributes SETPGROUP, pgroup 0
Held across: As long as members remain, possibly beyond attempt/worker
Released: Conditional group kill request
Authority: Cleanup addressing for members that remain
```

**Verdict: positive.** With the positive action heading, the entry describes what the worker requests. The row already says group members can outlive the attempt or worker. Pure deletion under Released retains the achieved-release ambiguity. This is a heading repair, not merely a softened absence disclaimer.

**What elision loses:** Only the explicit absence-proof warning. The conditional request, possible continuing group lifetime and cleanup-addressing role all remain.

**Support:** `docs/WORKER.md:134,391–408`; `docs/architecture.json: worker_capabilities s36b`.

Implementation conditions:

- Coordinate the heading with N004.cleanup.
- Preserve escaped-descendant and group-lifetime facts; no cleanup verification claim is added.


## N266

<details>
<summary>Exact original context</summary>

`docs/WORKER.md:144–144` at `672374c`:

```text
| n9a | Worker temporary pre-compile call frames | reporting | N9a | parse_args, map_region, read_all_from_fd, pw_timing_setup, prepare_extension | Before compilation | Call only | Return or process exit; no claim of byte erasure | None beyond existing pointers/rights | Source-only; native library internals unobserved | No: exec replaces stack | P | [`parse_args`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`map_region`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`read_all_from_fd`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`pw_timing_setup`](../controller/tools/pw_probe_runner/pw_probe_runner.c); [`prepare_extension`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`bare_deny_default`](../tests/suites/runner_c_worker_harness/run.sh) |  |
```

</details>

**Positive trial**

```text
Resource: Worker temporary pre-compile call frames
Acquired by: parse_args, map_region, read_all_from_fd, pw_timing_setup, prepare_extension
When: Before compilation
Held across: Call only
Release / teardown action: The automatic call frame's lifetime ends on return or process exit
Authority: None beyond existing pointers/rights
Sandbox-gated: Source-only; native library internals unobserved
```

**Elision trial**

```text
Resource: Worker temporary pre-compile call frames
Acquired by: parse_args, map_region, read_all_from_fd, pw_timing_setup, prepare_extension
When: Before compilation
Held across: Call only
Release / teardown action: Return or process exit
Authority: None beyond existing pointers/rights
Sandbox-gated: Source-only; native library internals unobserved
```

**Verdict: cannot decide.** Both alternatives preserve the automatic frame lifetime and remove the separate byte-erasure topic. The concise elided cell reads better than the expanded positive sentence. Neither says the bytes were wiped. That establishes a viable wording candidate, but not whether erasure serves a distinct confidentiality or cross-resource comparison purpose; the trial does not investigate that purpose.

**What elision loses:** The explicit distinction between ending a frame lifetime and erasing its bytes. If the inventory has a concrete reason to track wiping here, that distinction would disappear.

**Support:** `docs/WORKER.md:144`; `docs/architecture.json: worker_capabilities n9a`.

Implementation conditions:

- If Q03 finds no distinct necessary purpose, prefer the short cell Return or process exit under Release / teardown action.
- Keep frame ownership, acquisition timing and relevant native-internal scope.
- Do not add a wipe, confidentiality guarantee or unverifiable claim that bytes remain intact.

**Focused RCA question:** Which concrete data, observer or erasure requirement makes byte wiping material for this frame entry? Is the clause caused by the Released heading, by comparison with token erasure, or by a separate documented obligation?


## N270

<details>
<summary>Exact original context</summary>

`docs/WORKER.md:145–145` at `672374c`:

```text
| n9b | Capture hash/view/digest/sorting call frames | reporting | N9b | pw_capture_profile, pw_consumed_params_digest, pw_read_memory | Between compilation and apply | Call only | Return or process exit; no claim of byte erasure | Read own memory with existing task right | Source-only; qsort/CommonCrypto internals unobserved | No: exec replaces stack | P | [`pw_capture_profile`](../controller/tools/pw_probe_runner/pw_profile_capture.h) | [`bare_deny_default`](../tests/suites/runner_c_worker_harness/run.sh) |  |
```

</details>

**Positive trial**

```text
Resource: Capture hash/view/digest/sorting call frames
Acquired by: pw_capture_profile, pw_consumed_params_digest, pw_read_memory
When: Between compilation and apply
Held across: Call only
Release / teardown action: The automatic call frame's lifetime ends on return or process exit
Authority: Read own memory with existing task right
Sandbox-gated: Source-only; qsort/CommonCrypto internals unobserved
```

**Elision trial**

```text
Resource: Capture hash/view/digest/sorting call frames
Acquired by: pw_capture_profile, pw_consumed_params_digest, pw_read_memory
When: Between compilation and apply
Held across: Call only
Release / teardown action: Return or process exit
Authority: Read own memory with existing task right
Sandbox-gated: Source-only; qsort/CommonCrypto internals unobserved
```

**Verdict: cannot decide.** Both alternatives preserve the automatic frame lifetime and remove the separate byte-erasure topic. The concise elided cell reads better than the expanded positive sentence. Neither says the bytes were wiped. That establishes a viable wording candidate, but not whether erasure serves a distinct confidentiality or cross-resource comparison purpose; the trial does not investigate that purpose.

**What elision loses:** The explicit distinction between ending a frame lifetime and erasing its bytes. If the inventory has a concrete reason to track wiping here, that distinction would disappear.

**Support:** `docs/WORKER.md:145`; `docs/architecture.json: worker_capabilities n9b`.

Implementation conditions:

- If Q03 finds no distinct necessary purpose, prefer the short cell Return or process exit under Release / teardown action.
- Keep frame ownership, acquisition timing and relevant native-internal scope.
- Do not add a wipe, confidentiality guarantee or unverifiable claim that bytes remain intact.

**Focused RCA question:** Which concrete data, observer or erasure requirement makes byte wiping material for this frame entry? Is the clause caused by the Released heading, by comparison with token erasure, or by a separate documented obligation?


## N299

<details>
<summary>Exact original context</summary>

`docs/WORKER.md:125–125` at `672374c`:

```text
| s31b | Newly created filesystem object, if absent | operation | S31b | attempt_file_create: same open | After apply within an attempt | Later attempts/phases and beyond worker exit | No automatic unlink; later action/external actor may remove | Persistent filesystem effect, mode subject to umask | Source-only; creation not implied for existing target | Child can resolve it by path, not inherited fd | O | [`attempt_file_create`](../controller/tools/pw_probe_runner/pw_probe_runner.c) | [`create_existing_file_preserves_contents`](../tests/suites/witness_contract/run.sh) |  |
```

`docs/WORKER.md:151–151` at `672374c`:

```text
| x2 | Host disposition and comparison | external | X2 | comparisonEvidence | After collection/publication | Reply | Owning host/controller object lifetime | Join worker publications, query records and process observations | Outside specimen worker; source-only | No worker-to-child transfer | External evidence | [`comparisonEvidence`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | [`comparison_matrix`](../tests/suites/witness_contract/run.sh) |  |
```

`docs/WORKER.md:152–152` at `672374c`:

```text
| x3 | Host path diagnostics | external | X3 | enrichPathDiagnostics | After attempt collection | Reply | Owning host/controller object lifetime | Later path/metadata observations under host authority | Outside specimen worker; source-only | No worker-to-child transfer | External evidence | [`enrichPathDiagnostics`](../runner/Sources/PWRunnerCore/PWRunnerService.swift) | [`path_query_integrated`](../tests/suites/witness_contract/opt_in/path_query_integrated.sh) |  |
```

`docs/WORKER.md:209–212` at `672374c`:

```text
| W50 | x3 | s31b | observes | Later host path inspection may observe file effect | [`enrichPathDiagnostics`](../runner/Sources/PWRunnerCore/PWRunnerService.swift) | [`path_query_integrated`](../tests/suites/witness_contract/opt_in/path_query_integrated.sh) |  |
| W51 | s2 | x2 | joins | Host uses admitted publications | [`runCWorker`](../runner/Sources/PWRunnerCore/CWorker.swift); [`comparisonEvidence`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | [`bare_deny_default`](../tests/suites/runner_c_worker_harness/run.sh) |  |
| W52 | x1 | x2 | joins | Host joins prediction records to attempt evidence | [`planValidatorQueries`](../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) | [`comparison_matrix`](../tests/suites/witness_contract/run.sh) |  |
| W53 | x3 | x2 | joins | Host attaches later path observations | [`enrichPathDiagnostics`](../runner/Sources/PWRunnerCore/PWRunnerService.swift) | [`path_query_integrated`](../tests/suites/witness_contract/opt_in/path_query_integrated.sh) |  |
```

`docs/WORKER.md:220–220` at `672374c`:

```text
- `x3`: Path spelling alone is not object identity
```

</details>

**Positive trial**

```text
{
  "s31b": "Newly created filesystem object, if absent",
  "x3": "Host path diagnostics",
  "x2": "Host disposition and\ncomparison",
  "W50": {
    "from": "x3",
    "to": "s31b",
    "kind": "observes",
    "label": "Later host path inspection may observe file effect"
  },
  "W53": {
    "from": "x3",
    "to": "x2",
    "kind": "joins",
    "label": "Host attaches later path observations"
  },
  "x3_note": "The worker attempts file creation during its action; the host later attaches target-path metadata to the reply"
}
```

**Elision trial**

```text
{
  "s31b": "Newly created filesystem object, if absent",
  "x3": "Host path diagnostics",
  "x2": "Host disposition and\ncomparison",
  "W53": {
    "from": "x3",
    "to": "x2",
    "kind": "joins",
    "label": "Host attaches later target-path metadata"
  }
}
```

**Verdict: elision.** The positive wording supplies accurate event facts but W50 still directs an observes edge from path diagnostics to the newly created object. It therefore leaves the identity implication in place. The preferred elision removes that relationship and the note while retaining both resource nodes, X3 and its host-record relation W53. A note-only deletion is not a sufficient variant. This case requires graphic repair; wording alone does not solve it.

**What elision loses:** The graph no longer asserts that later host path inspection observes the particular worker-created object. This relationship is the issue being tested, not an unrelated resource fact. S31b and its actual worker acquisition/publication edges remain; X3 and metadata attachment remain.

**Support:** `docs/architecture.json: worker_capabilities s31b, x3, x2, W50, W53`; `runner/Sources/PWRunnerCore/PWRunnerService.swift: enrichPathDiagnostics`; `docs/WORKER.md:125,209–212,220,489–497`.

Implementation conditions:

- Keep every source/check citation attached to X3 and W53.
- Regenerate and visually inspect the graph to confirm the identity-directed edge is gone while the worker-created resource and host evidence account survive.
- Review the positive relationship actually implemented by enrichPathDiagnostics; do not infer object identity from the pathname.

## Recommended next round

Freeze this comparison, then run Q01 (S18 mapping attribution), Q02 (the exact child-policy proposition) and Q03 (the two frame-erasure clauses). Repeat only comparisons changed by their findings. The seven repair packages remain useful with these refinements:

- R01: use the positive `Release / teardown action` heading and remove its redundant explanatory sentence; settle Q03 before changing its frame cells.
- R02: use a positive mechanical-check caption and precise citation heading; elide N005’s editorial instruction.
- R03/R04: state fixture conditions and adapter actions directly.
- R05: identify the native result determining attempt status; repair W41 to `Publishes file-create attempt status from open result`.
- R06: elide the duplicated table warning; retain the concrete native-effect/publication counterexample.
- R07: remove W50 and the X3 note; retain S31b and the W53 host-metadata relation. A note-only rewrite fails.

For each undecided clause, identify a specific present inference or requirement, or record the bounded search that found none. No trial establishes a new native-memory, child-policy or mapping-identity guarantee. The original sweep and triage records remain unchanged.
