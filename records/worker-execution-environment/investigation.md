# Execution environment investigation

Associated plan: [EXECUTION-ENVIRONMENT-PLAN.md](../../controller/src/EXECUTION-ENVIRONMENT-PLAN.md).
Reviewed source: `a458b2876da794dd159848ae1bc02e0c65d15c62`.
Date: 2026-10-18. Status: investigation complete; recommendation for review.

## Recommendation

Retain the current observation model and make the environmental limitation
explicit in the worker account. Do not add a general environment schema,
permission preflight, consent reset, or provisioned execution environment for
WA-10. The existing dossier already covers the immediately useful selection
facts. The missing facts are either particular process observations that need
a specific consumer, or OS decisions that cannot be recovered from those
selection facts.

Worker credentials are a credible, separately bounded future capability. They
would add information, and collecting them need not touch a target or request
consent. This report defers that capability because the reviewed uses do not
require a credential comparison today, not because credentials are unknowable
or useless. A user-versus-system runner experiment would be a concrete reason
to reopen it.

The immediate documentation correction should name privacy consent mediation
among ambient restrictions, preserve the existing warning that a stalled call
is not a sandbox verdict, and distinguish selected signing metadata from
observed process context. The starting-authority paragraph in `docs/WORKER.md`
is authored prose outside its generated graph blocks, so edit that paragraph
directly as part of the parent documentation workstream. Changes to generated
resource or graph facts would instead belong in `docs/architecture.json` and
require regeneration. This investigation edits neither.

## What was done

This is source and documentation review, not a new execution experiment. No
build, specimen run, process inspection, runner installation, consent query,
target preflight, TCC database read, settings change, or environment provisioning
was performed by this investigation. Test sources below establish what their
controls assert; citing them does not assert they were newly run. The
coordinator separately records any retained-run inspection and the reviewed
source hashes.

WA-10 originally identified a documentation omission. Its audit account,
`records/worker-pass6/initial-report.md`, explicitly did not observe
TCC behavior for this launch chain. Nothing in this review upgrades that
absence into a measured TCC condition.

The coordinator's [reviewed-evidence manifest](reviewed-evidence.json) identifies
five cases in the already retained run `20261018T215123Z_e8874e1f` and hashes
the artifacts inspected. The raw run files are gitignored, local to this
checkout and already pinned for retention. Prior CLI exec observations show
zero environment entries, descriptors 0/1/2 and stdin EOF. The contaminated
worker control records the supplied environment/descriptor reaching its
adapter and the exec children's narrower state. The live identity observer
records worker/host generations and independent queries, not credentials.
The exec-DAC control observes `EACCES` for a nonexecutable file and success
after restoring execute permission. These are prior bounded observations,
not fresh tests or evidence of a privacy permission census.

The manifest also hashes three older reports reviewed for context. In
`records/BYOXPC-ENTITLEMENT-BEHAVIOR.md`, an October 6 run on macOS 14.8.9
and an older app recorded a Desktop-target stall, including an allow-default
control, while relocating the target to `/private/tmp` completed. The
sampled stack located an `open` call; the report left privacy mediation a
hypothesis. `records/archive/BYOXPC-ENVIRONMENT-OBSERVABILITY.md` similarly
kept a location-sensitive exec failure separate from its environment
conclusions. Their raw receipts were not revalidated here. They motivate the
limitation without establishing current-OS replication or TCC causality.

## Existing facts and their owners

| Fact | Provider and reader | What it establishes and what it leaves open |
| --- | --- | --- |
| Submitted policy, required entitlement keys, runner selector and test controls | [run flow](../../controller/src/run_flow.rs), [runner selection](../../controller/src/runner_select.rs), [request/reply types](../../runner/Sources/PWRunnerCore/PWRunnerAPI.swift) | Supplied inputs and admission decisions. Required keys are checked against the selected worker's read-back, not host entitlements. A supplied control does not establish that its boundary was reached. |
| macOS product/build version, kernel release and architecture | `HostFacts::collect` in [dossier.rs](../../controller/src/dossier.rs), backed by [host_facts.rs](../../controller/src/host_facts.rs) | Controller-side sysctl observations before runner invocation; failed reads become null. They identify OS context, not the worker's credentials, libraries or effective authority. |
| Selected service, worker, validator and issuer identity/entitlements | [runner_select.rs](../../controller/src/runner_select.rs), [runner_manager.rs](../../controller/src/runner_manager.rs), [dossier.rs](../../controller/src/dossier.rs) | Built-in metadata comes from the app manifest; external metadata comes from the installation registry. Selected nonbaseline files are hashed before invocation. Read-back age and selection-to-execution are real limits: none authenticates the running worker or constitutes an effective-permissions census. |
| App build provenance and optional evidence verification | `load_app_provenance` in [run_flow.rs](../../controller/src/run_flow.rs), [signing reference](../../docs/SIGNING.md#evidence-artifacts) | The dossier names the manifest and optional verification report. Build equipment/configuration explains the artifact's construction; it is not a worker runtime environment record. |
| External installation scope and ownership | `RunnerRecord`, `RunnerOwnership`, `build_launchd_plist` in [runner_manager.rs](../../controller/src/runner_manager.rs), installation in [runner_commands.rs](../../controller/src/runner_commands.rs) | Registry scope, launchd domain and installer owner UID are installation/cleanup facts. `RunnerProvenance` does not serialize scope. System selection is represented in recorded client argv by `--privileged`; neither that option nor the ownership UID measures worker credentials. |
| Worker existence, publication, timing, attempts, termination and collection | [CWorker.swift](../../runner/Sources/PWRunnerCore/CWorker.swift), [native worker](../../controller/tools/pw_probe_runner/pw_probe_runner.c), [reply types](../../runner/Sources/PWRunnerCore/PWRunnerAPI.swift) | Facts from the actual child and reporting channel, with explicit missing/partial states. No general worker UID/GID, supplementary-group, cwd, environment, session or privacy-state receipt is emitted. |
| Issuer PID and UID/EUID/GID/EGID | [issuer](../../controller/tools/pw_probe_runner/pw_extension_issuer.c), [ExtensionIssuer.swift](../../runner/Sources/PWRunnerCore/ExtensionIssuer.swift), [independent reader](../../tests/lib/extension_evidence.py) | The issuer samples its own credentials before the issue call; the host exposes them after valid publication. Missing publication withholds them. These are issuer facts only, not measurements of its worker sibling. |
| File identity and later path diagnostics | `attempt_file_read_fresh` in [native worker](../../controller/tools/pw_probe_runner/pw_probe_runner.c), `enrichPathDiagnostics` in [service](../../runner/Sources/PWRunnerCore/PWRunnerService.swift) | Fresh-read identity describes the descriptor opened by that worker. UID/GID in that identity identify the file owner/group. Later path resolution is explicitly host-observed after orchestration. Neither is a worker-credential or pre-attempt permission observation. |

The [independent consumer](../../tests/lib/consumer.py) validates dossier fields
and the publication/claim boundaries. The
[dossier witness](../../tests/suites/witness_contract/check_dossier.py) compares
OS strings with separate `sw_vers`/`uname` observations and binary hashes with
independently read files. These are useful independent checks of the stated
facts; they do not extend their meanings to privacy state.

## Launch chain and inherited context

The controller invokes the shipped client with held request bytes on stdin;
[runner_client.rs](../../controller/src/runner_client.rs) records the actual
client argv and transport capture. The
[client](../../runner/Clients/PWRunnerClient/main.swift) selects embedded XPC or
a Mach service, with a privileged connection option for system scope. The
[listener](../../runner/Sources/PWRunnerCore/PWRunnerListener.swift) uses the
corresponding launch mode. The host's signed-caller check in
[PWRunnerService.swift](../../runner/Sources/PWRunnerCore/PWRunnerService.swift)
checks caller signing identity; it does not determine who macOS regards as the
responsible code for privacy mediation.

The host spawns a worker with nil spawn attributes and nil envp, explicitly
arranging policy, evidence, readiness and optional token descriptors. It does
not perform a generic close-all-descriptors operation for the worker. By
contrast, an exec attempt explicitly supplies an empty environment and
`POSIX_SPAWN_CLOEXEC_DEFAULT` with selected standard descriptors and a new
process group. See [worker launch](../../runner/Sources/PWRunnerCore/CWorker.swift)
and [exec attempt](../../controller/tools/pw_probe_runner/pw_probe_runner.c).
These are different process boundaries and must not share an inferred
environment account.

The [worker account](../../docs/WORKER.md#starting-authority-and-ambient-context)
already distinguishes source-derived inheritance from its earlier bounded
launch inventory. It reports an examined native path constructing an empty
environment, and a prior ordinary-worker observation consistent with that;
this review does not rerun or broaden that observation. The
[inheritance suite](../../tests/suites/runner_exec_inheritance/README.md)
deliberately supplies an environment value and extra descriptor through a
direct-worker adapter, then checks that exec children exclude them. Shell
environment changes alone would not establish what reached a launchd-managed
host. The optional launch inventory is explicitly incomplete for ports,
signals, resource limits and extension-bearing workers.

Apple's archived [posix_spawn manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/posix_spawn.2.html)
describes default credential and process-state inheritance, with executable
mode and spawn-attribute exceptions. Such platform rules and source calls
describe the mechanism; they do not replace a per-run measurement of its
result. In particular, this investigation does not infer the worker's effective
UID from registry scope or the invoking shell.

## Concrete cases that distinguish the options

**Required worker entitlement.** A specimen conditions a write on a particular
entitlement. The existing selector can refuse a worker whose recorded key is
absent or false. The
[entitlement transfer control](../../tests/suites/runner_byoxpc/opt_in/entitlement_transfer.py)
uses separately installed true/false workers, independently reads resulting
file bytes and distinguishes selection refusal from an admitted denied
attempt. The relevant entitlement information already has a provider and
consumer. A second generic environment field would add no necessary fact.
This is a description of that control, not a claim of a new live BYOXPC result.

**Desktop read versus a temporary fixture.** Imagine the same read specimen
and selected binaries succeeding on an owned temporary file while a Desktop
target fails or stalls. Existing observations can establish each operation's
result and timing. They cannot establish whether the Desktop run encountered
consent mediation, which responsible identity was used, or which restriction
caused the result. Moving an ordinary SBPL fixture to an owned temporary
directory reduces exposure to the documented privacy-mediated location, but
changes the target and does not isolate causality. It is appropriate for a
fixture whose subject is the SBPL operation, not a substitute for a Desktop
experiment. The [BYOXPC suite](../../tests/suites/runner_byoxpc/README.md) already
uses owned temporary staging and targets and avoids privacy-database changes.

**User versus system runner, or unexpected file-owner mismatch.** Identical
policy and binary hashes do not establish identical worker credentials.
Worker-sampled UID/EUID/GID/EGID would make a difference visible and help a
reader decide whether runs are comparable. The distinction is especially
relevant when investigating file acquisition; the worker offers both
`access(R_OK)` and open/read operations. Apple's
[access manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/access.2.html)
specifies real UID and the real group access list for the former. It is not an
open/read preflight; a comparison about reading bytes should use `read_fresh`
and retain its actual read result. Current client connection flags
describe selected scope, and file identity describes the acquired object,
but neither fills this missing process fact.

This is the strongest small capability candidate. It still would not explain
all permission-shaped failures: four IDs omit supplementary groups, ACLs,
ancestor traversal, object changes and other policy layers. The reviewed
selection and comparison consumers do not currently promise credential
equivalence or require a credential gate. Therefore deferral preserves an
explicit unknown without removing evidence required by an existing claim.
If cross-scope comparability becomes a product requirement, credential
observation should be considered independently of any privacy-status feature.

The first focused investigation need not add a permanent reply field.
[launch_inventory.py](../../tests/suites/runner_exec_inheritance/launch_inventory.py)
already retains raw `ps` UID/GID and start-time output for the worker and host
held by existing sleep seams. The
[live identity observer](../../tests/suites/runner_live_worker_identity/observer.c)
already obtains `proc_bsdinfo` tied to PID, start time, ancestry and executable;
a test-owned extension could retain its real/effective ID fields. Neither
route currently provides supplementary-group coverage or a permanent
per-attempt credential record. A bounded next experiment could compare fresh
workers under already available user/system runners, using an owned,
mode-restricted temporary file, fixed allow-default policy and independently
recorded target metadata. New installations or privilege changes would need
their own explicit scope. The trigger for a product receipt is a demonstrated
need to retain these facts in ordinary runs without an observer hold window.

## Why a baseline permission probe is not metadata

Apple's [file-access protection guide](https://support.apple.com/guide/security/controlling-app-access-to-files-secddd1d86a6/web)
identifies consent protection for Desktop, Documents and other named locations.
Apple DTS's [file-system permissions account](https://developer.apple.com/forums/thread/678819)
describes multiple restriction mechanisms, location/version-dependent prompts
or refusals, persistent decisions and responsible-code attribution for helpers.
Those are platform
reasons to avoid treating signing metadata or a timeout as a TCC verdict;
they do not establish this application's current privacy state.

A proposed preflight that opens a target can itself request consent, affect
subsequent decisions, or acquire a resource before the specimen policy applies.
Checking from the controller or an extra helper measures that actor and launch
chain. Passing the opened descriptor to the worker changes the acquisition
under test. Repeating an allow-default control in a fresh worker preserves the
one-sandbox-per-process rule, but does not reset machine consent, filesystem
state or process-responsibility history. Its result is another attempt at
another time, not certification that the later attempt has only SBPL to contend
with. These are experimental-design inferences, not new observations here.

Do not add private TCC database inspection or guess a privacy-state boolean
from observed success. A specifically relevant framework authorization result
could someday be recorded with its actor, API, target/resource and observation
point. No such operation-specific need was demonstrated by the four current
ordinary attempt families in this review.

## Options and costs

| Option | Useful scope | Costs and decision |
| --- | --- | --- |
| General environment account | Group existing host and selection facts with new context | Grouping does not make those facts a common snapshot. Unknown fields quickly become an implied permission census. No new schema is justified by this investigation. |
| User-declared conditions | Preserve an operator's intended GUI session, consent setup or lab profile | Useful in an experiment's retained setup notes, explicitly declared and time-bound. Declarations cannot authorize causal claims or substitute for observations. No new accepted request field or automatic gate now. |
| Worker credential receipt | Identify actual worker UID/EUID/GID/EGID at a specified point | Low disturbance and no target open; real diagnostic value for credential-sensitive comparisons. Defer until that consumer is selected. It requires worker publication, absence semantics and independent controls, not just controller serialization. |
| Baseline access probe | Observe a particular operation for a particular actor | Can prompt, acquire authority or alter later state; no generic effective-access answer. Do not insert automatically. A future explicit experiment must retain its own operation, actor, ordering and effects. |
| Controlled fixture profile | Repeat selected SBPL tests on owned temporary objects, fixed binaries and explicit runner choice | Already substantially available in tests. Reproduces only those selected inputs and launch route; not ordinary Desktop/Documents behavior, another user's session, other BYOXPC scope or arbitrary third-party software. Keep it as a bounded testing convention. |
| VM snapshot or machine reset profile | Study a deliberately selected initial OS/user/privacy state | Provisioning and reset costs, platform dependence, and narrower applicability. Apple DTS recommends snapshot restoration for TCC testing, but that does not reproduce a user's existing desktop. No provisioning or reset proposed for WA-10. |
| Retain limitation | Report actual attempts, selected provenance and known observation boundaries | Leaves worker credentials and privacy state unknown. This is compatible with existing claims and is the recommended current decision. |

## Reopening criteria and boundaries

A future credential receipt should identify the worker, the sampling stage
(for example, after channel acceptance and before policy application), and
whether publication occurred. Early refusal/death must leave it unavailable;
the host must never fill it from its own credentials or the issuer's. It
would be a sample, not a claim of unchanging identity throughout a run.
Start with a consumer that compares runs or diagnoses a particular credential
condition; do not convert it into a permission classifier. Validate actual
sampling independently, wrong-actor rejection, publication loss and reader
behavior. The native layout/source identity, C/Swift transport, reply shape,
consumer fixtures and documentation would need coordinated review under the
[wire contract](../../docs/CONTRACT.md). Adding fields alone does not settle
whether a version bump is necessary; changed reading rules do.

A privacy experiment should first name the operation and launch route it is
trying to explain, the hypothesized external condition, and an independent
observation method. A controlled baseline needs fresh processes and an account
of persistent state and target acquisition. Any proposed consent response,
settings change, reset, account/VM provisioning or system-scope installation
should be presented separately as a concrete experiment for user decision.
None is necessary for the recommended documentation correction.

The current decision requires no worker refactor, supervisor dependency,
protocol change, or new execution mode. Claim-local observation records and
resource-ownership documentation can proceed without waiting for an
environment capability.

## Review and verification

The investigator, independent reviewer and coordinator agree on the current
recommendation. The review challenged it with actual worker credentials and
kept that missing capability explicit; it also checked actor attribution,
`access` versus actual reading, prior-evidence limits and authored versus
generated document ownership. No blocking finding remains in this report.

[reviewed-sources.json](reviewed-sources.json) identifies 43 unchanged reviewed
source/doc/test files at the stated commit. [external-sources.json](external-sources.json)
records primary reference locations and their limits. Local links, evidence
hashes and whitespace were checked. These checks validate the record's
references and identity, not a new runtime behavior or privacy-state claim.
