# Bounded pytest adoption: native exec evidence controls

Status: implementation authorized in an isolated candidate worktree. Authorization
includes dependency provisioning, integration, controls, ordinary correction of
defects introduced by this work, documentation/citation updates and the planned
verification. The accepted checkout is not an integration target for this leg.
Prepared by Codex, 2026-10-30. Planning branch `plan/pytest-exec-family` starts
at `5dbcf4d8255ca24a186e97488104772df9cb53d6`; accepted production/test source
remains `77eb987554eef10ffa3371ffb21b235097562a78`. The planning worktree is
`/private/tmp/pw-pytest-adoption-plan-20261030`.

The objective is better ordinary diagnosis and organization for **one family**,
with fewer repeated selection/setup/report declarations. Keeping operational
and evidence machinery outside pytest is intentional. Fewer total lines and
eventual replacement of the entire harness are not acceptance requirements.
Preserve accepted application bytes, native production behavior, independently
authored oracles and protected evidence. Changes to the candidate harness,
dependencies and their current guides are authorized within this family.
CHECK.md, merging into the accepted checkout and expansion to another family
remain outside scope.

Associated records: [source and consumer investigation](pytest-exec-adoption/source-notes.md)
[planning-state identities](pytest-exec-adoption/state.json), and
[implementation sequence and recovery index](pytest-exec-adoption/implementation.md). They distinguish
inspected facts, proposed contracts and outstanding implementation checks.

## 1. First family and fixed observations

Adopt only `runner_c_worker_harness/exec_control_states` (abbreviated **F**).
Keep its canonical catalog ID, default membership, standard context, inherited
requirements `app`, `worker`, `clang`, empty skip allowance and lack of catalog
dependencies. Its native code itself needs no app, but removing its existing
artifact admission is not part of this adoption. Other C-worker cases and live
exec lifecycle/inheritance suites retain their current paths.

This is a meaningful family: production worker code is compiled with deterministic
native-call equipment, checked against an independent ledger, and deliberately
mutated to test the assertions' ability to reject incorrect evidence. Its current
single shell result obscures which variant failed and which phase failed. Its
established controls and completed C replay make the benefits inspectable without
another feasibility demonstration.

Pytest will collect nine named items from one suite-local declaration:

| Stable item suffix | Required observation |
| --- | --- |
| `production` | Complete control executable succeeds; canonical native ledger equals all 58 golden attempts, including order, arguments, counts and digests. |
| `collection_from_final_reap` | Formed mutation is rejected by the unchanged collection/leader observation assertion. |
| `esrch_as_success` | Formed mutation is rejected by the unchanged group return/errno assertion. |
| `fallback_from_group` | Formed mutation is rejected by the unchanged independent fallback assertion. |
| `status_after_pending_wait` | Formed mutation is rejected by the unchanged wait result/errno assertion. |
| `revents_as_native_errno` | Formed mutation is rejected by the unchanged waitid/poll errno assertion. |
| `local_deadline_as_native_errno` | Formed mutation is rejected by the unchanged wait result/errno assertion. |
| `missing-pw_worker_timing.h` | Compiler refuses specifically at the missing timing-header include. |
| `missing-pw_worker_exec.h` | Compiler refuses specifically at the missing exec-header include. |

Full ID is `F::<suffix>`. Production source, native fixture, golden values,
mutation bodies and designated assertion text keep their accepted meanings.
The six mutation/expectation pairs become one case-local table, independently
authored rather than derived from producer constants. Missing-anchor failure is
failure to form a control, never successful detection of a production defect.

**Do not split the 58 ledger attempts into pytest items.** They include shared
state, repeated attempts, exclusions and sticky timing-fault relationships in
one native program. Each normal/mutant binary runs its complete existing native
sequence. The two missing-header variants compile only. Native “child” PIDs in
this fixture are substituted values, not evidence of real process creation or
kernel enforcement. Real compiler/linker/control processes are distinct resources.

Preserve baseline applicability without a second test scheduler. A session-scoped
pytest fixture supplies immutable source inputs and a lazily evaluated baseline
result. One domain helper builds/runs/canonicalizes the unmodified baseline once
and caches its receipt and validation findings, including failure. The `production`
item asserts that result in its **body**. A prerequisite fixture for every other
item requests the same result and raises a **setup error** if it is invalid,
before compiling that variant. Thus order does not affect applicability or repeat
baseline execution; no fixture calls another test function. Successful baseline
receipts link to every dependent item. An invalid baseline cannot yield credited
mutation passes. This preserves the current script's prerequisite relationship
while giving explicit diagnostics for blocked work.

## 2. Ownership boundary

| Owner | Responsibilities and proposed source location |
| --- | --- |
| Pytest | Collection and ordering of F's items, fixture caching/order/finalizers, variant execution, assertion and setup/call/teardown reports. `tests/suites/runner_c_worker_harness/test_exec_control_states.py`. |
| Domain helper | Source closure, immutable input inventory, mutation formation, native ledger normalization, literal expectations and artifact naming. Refactor existing `check_exec_evidence.py` into an importable helper; retain `canonical_ledger` there and remove its executable test loop. It imports no pytest. |
| Pytest integration | Collection manifest, eligibility wait, durable phase export and evidence links. Proposed `tests/lib/pytest_engine.py` and explicit `tests/pytest.ini`. No native resource acquisition at import/collection. |
| PW family adapter/supervisor | Admit the engine to the existing checkout claim, publish selected identities, authorize commands, supervise engine/process ownership, validate durable accounting and return one derived family result. Proposed `tests/lib/pytest_family.py`. No iteration that invokes individual pytest items. |
| PW command ownership | Gated command launch, direct stdout/stderr capture, deadlines, process-group and exit observations, recoverable ownership records. Proposed narrow `tests/lib/pytest_command_owner.py`; shared record/closure operations belong in a neutral module, not imported from a launcher. |
| Existing PW infrastructure | `checkout_lock.py`, `artifact.py`, `suite_run.py` equipment/dependency gates and sleep accounting, `retention.py`, release cleanup and acceptance consumers. These remain maintained infrastructure. |

Ordinary fixture cleanup checks immutable inputs and asks to remove completed
scratch. Resources with obligations beyond the engine belong to PW **before
acquisition**. Fixtures request execution and await receipts; they do not launch
unowned `subprocess.run` commands or depend on post-yield code to reap them.
Compile and control commands retain the current 60-second and 20-second limits.
PW records timeout/interruption separately from the native result; a killed
control cannot count as its designated assertion rejection without that evidence.

For each command, publish intent (run/family/item, operation, command/cwd/env
identity, paths and nonce), start a gated command owner, register its PID/exit
observation, persist ownership, then release it to launch. The command owner
holds the verified checkout descriptor and supervises the command's separate
process group, retaining stdout/stderr directly in files even if pytest dies.
It waits/reaps and establishes group quiescence before declaring the obligation
closed. Do not infer closure from a requested signal or compiler-leader exit.
The owner stays outside the engine group and retains the claim while compiler
descendants remain, including descendants that close inherited descriptors.

This is a deliberately narrow resource kind: the invoked toolchain/control
process group and its files, not launchd installations or arbitrary escaping
descendants. The implementation must establish actual toolchain topology and
descriptor behavior. If that cannot support the stated ownership boundary,
stop at that finding and return a localized alternative; do not silently widen
the claim or build a general process service.

On engine death the live PW supervisor cancels/settles active commands and
preserves their partial bytes. On outer dispatcher/family-supervisor death the
command owner must remain identifiable, hold the claim, and settle or await
restricted recovery; it admits no new engine. Reuse the demonstrated authenticated
peer/nonce/descriptor and independent-exit principles, not its synthetic file
owner verbatim. If that owner also dies or its identity cannot be established,
retain an unresolved obligation and refuse successful finalization. Recovery
must not signal a historical PID merely because its number appears in a record.

Store durable ownership under a new, bounded `tests/out/pytest-owners/<run-id>/`
namespace, outside disposable `runs/`, with pointers to the owned run and
command artifacts. Registration precedes launch. Records protect their associated
output until disposition is established. Possible live commands or unbounded
ownership uncertainty also block checkout execution; proven quiescence with
remaining isolated file/evidence work protects only the affected output. The
operational classification and recovery path are specified below.
Place that admission check in shared checkout admission for the new namespace,
so both builds and tests respect an orphaned obligation even if its last lock
descriptor has disappeared. Keep its parser independent of pytest and of the
retention module to avoid circular ownership. Existing unrelated recovery
namespaces are not adopted by this check.
The same guard applies to release rotation/cleanup. Closed records are removable
with their unpinned run through supported pruning, after identity revalidation.
Pins continue to protect overlap. This fills the prototype's known retention
gap; merely setting `run.json.terminal=true` must not make a pending lease
disposable. Do not import, reinterpret or recover earlier protected resources.

### Recovery interface and dispositions (stage 2)

Add a mutually exclusive public mode, available without pytest or app admission:

```sh
tests/run.sh --recover-ownership RUN_ID          # read-only diagnosis/preview
tests/run.sh --recover-ownership RUN_ID --apply  # apply only evidence-justified recovery
```

Every registry refusal prints the record/run identity, blocking scope, evidence
still missing and the concrete preview command. The mode does not accept test
selectors, `--prune`, a force-clear option or an arbitrary PID. Preview writes
nothing. Apply revalidates the preview's inputs; it never treats a prior preview
as authorization to act on a changed identity. It leaves a durable recovery
receipt with before/after record digests, actions, observations and disposition.
Closure and deletion are separate: recovery does not prune evidence or remove
pins. Retries after interruption must be idempotent.

Recovery can inspect the registry before the ordinary unresolved-record guard.
Its narrow capability permits only diagnosis, revocation/settlement of the named
orphaned command and publication of recovery evidence. It cannot launch an engine
or native test. For a surviving owner it authenticates the live socket peer,
nonce and transferred held descriptor against the recorded checkout identity;
it refuses cancellation of a still-active valid test session. For records with
no live owner, mutation requires the ordinary OS lock acquired through a
recovery-only path, retaining the original record bytes before any new lock
owner metadata is written. Other unresolved entries are not waived: their live
holds still prevent acquisition, and their dispositions still govern admission.
A missing socket, available lock, old PID, changed nonce or elapsed time is not
proof of process exit. Signals require current authenticated ownership or an
independently established matching live process identity and scope; no signal
is sent solely from a saved PID/PGID. If that proof is unavailable, preserve the
record and identify the additional evidence or user decision needed.

Use monotonic per-command transitions with durable authorizations before their
effects: `reserved`, `owner_launch_authorized`, `owner_bound`,
`command_release_authorized`, `command_started`, `command_settled`,
`quiescent_retained`, `closed`. Each authorization is persisted before starting
or releasing the corresponding process; it records permission, not proof the
action occurred. The reservation identifies the authorizing controller and
checkout/session; bindings retain peer PID, kernel process-start identity and
boot identity where needed to distinguish reuse, plus the nonce/held descriptor.
An identity query that cannot establish the required relation leaves it unknown.
A gated owner cannot start the compiler until the command
release authorization is durable. Neither native success nor `command_settled`
alone proves the owner has relinquished its ability to launch further work.
Settlement records identify the exact command, wait/exit and group observations,
closed launch channel and remaining paths; recovery preserves the original
sequence and appends its conclusion instead of rewriting earlier states.

| Durable evidence / crash window | Recovery permitted and still missing | Blocking scope |
| --- | --- | --- |
| `reserved`, before any owner-launch authorization | After confirming the authorizing controller is stopped or has irrevocably revoked this reservation, the write-before-launch invariant establishes no owner/command could have launched. Record `never_launched` and close/reconcile isolated preparation files. Mere absence of a PID field is insufficient. | Checkout until no future release is possible; then only affected output if file/evidence work remains. |
| Owner launch authorized, but no bound owner/PID receipt; or bound owner with no command-release authorization | The first case may contain a started gated owner. Authenticate and cancel it, or require positive lifecycle/revocation evidence; do not assume launch failed. In the second, the command-release invariant establishes no native command started only after the owner/controller can no longer release it. Observe the owner's exit before closing its hold. | Checkout while an owner or future launch remains possible; evidence/file hold afterwards. |
| Command release authorized but start receipt absent, or a command is active | The native command may have started. Use the authenticated live owner to settle it and independently observe exit/group quiescence, then revoke launch authority. With no such owner and no adequate lifecycle evidence, retain unresolved ownership. | Whole checkout; associated output protected. |
| Native command returned, then crash before `command_settled`/closure publication | A return code or output file does not settle descendants. The live owner may finish observations; otherwise require already durable matching wait/group/authority-revocation evidence. If that evidence is missing, do not reconstruct it from the current absence of a PID. | Whole checkout until quiescence and revocation are established. |
| Durable settled/quiescent evidence, crash before `closed` publication or during isolated file cleanup | Revalidate receipt identities and that no further command can launch. Reconcile the remaining owned paths and publish closure idempotently. Missing test phases stay missing; ownership recovery cannot convert an incomplete run to a pass. | Only that run, registry record and specifically owned staging paths; other builds/tests may proceed. Release acceptance/disposal of this run remains blocked until its required closure evidence is complete. |
| Malformed/truncated/conflicting record or unknown path/process scope | Preserve raw bytes. Recover only from independently matching intact receipts or a separately reviewed disposition; no “delete stale record” shortcut. | Whole checkout if live/future acquisition cannot be excluded. Narrow to output-only only with affirmative quiescence and bounded-path evidence. |
| Valid closed receipt | No remaining operational block; normal retention and pins decide disposal. | Ordinary retained-output protection only. |

“Whole checkout” means new build/test execution in that checkout, not read-only
inspection, help, list or recovery preview; another worktree has its own ownership.
An already authenticated owner may finish settling its registered command, but
cannot use the exception to admit another session. Output-only holds do not
silently become deletable because execution is again permitted. The guard is
computed from validated evidence, not trusted from an editable `blocking_scope`
label. Publish that classification and its supporting receipt references in both
recovery preview and ordinary refusal messages.

Disposal still needs the real checkout lock. If that lock is available and the
record's affected paths are known, unrelated output may be pruned through a
purpose-limited disposal admission; the pending run and its ownership/staging
paths remain protected. A cleanup capability cannot launch tests/builds. If the
record's path scope cannot be bounded, refuse managed-output deletion until
recovery narrows it. Shared admission must distinguish execution, disposal and
recovery explicitly rather than expose an environment-variable bypass.

Commit/review this state machine and exercise its crash-window/disposition
controls on isolated fixtures before enabling the registry in shared build,
prune and release admission. This is part of stage 2, not another general
feasibility trial. The registry stays limited to this family's new resource kind.

## 3. One public path and one item manifest

Keep `tests/run.sh` and `make test`. `--case F`, its owning suite, the default
battery and `--all` reach the same registered family route, once under the existing
union/deduplication rules. Add an explicit catalog engine kind for this one case;
retain the current engine as the default for other entries. Do not put nine IDs
in the catalog or keep nine shell branches. Other families continue through
the existing executor. F remains one top-level case, like the existing Rust/Swift
batch cases, but has a visible nine-item account.

Concretely, F's catalog entry gains `engine: pytest` and its single `module`
path. Its effective configuration excludes the inherited shell `command`;
`test_cli.catalog` validates the engine-specific module/launcher instead of
requiring a bash command for that entry. Other rows keep their present schema
and validation. The pytest engine kind contributes its `pytest` equipment
requirement to the effective `requires` displayed in the plan, alongside the
unchanged inherited three. The fixed PW launcher constructs the actual command
and records it; the catalog does not repeat item declarations or launcher flags.

The first adoption deliberately keeps **whole-family public selection**. It
does not add `-k`, raw node selectors or a new variant flag. Rerun a named failure
with `tests/run.sh --case runner_c_worker_harness/exec_control_states`; the
family is bounded. Item IDs support diagnostics
and evidence, not a second public execution interface. No direct pytest command
is an accepted run; executing fixtures require the authenticated PW session.

After ordinary argument/config/catalog validation, start the fixed family engine
in collection mode. Pytest discovers the module, attaches unique explicit stable
suffixes, and sends the immutable manifest: protocol version, family ID, stable
ID-to-nodeid mapping, fixture/prerequisite descriptions, source/config/package
identities and request identity. The supervisor checks family/request binding,
uniqueness and structural validity; it does not reconstruct expected variant
names or choose an order. Independent controls—not a second runtime registry—
assert that the accepted family still contains the intended nine observations.

For execution, keep that same engine waiting at the collection barrier: no
collect-twice admission. Once collection succeeds, the dispatcher acquires its
normal lock and durably publishes the ordinary plan with the family manifest
and its digest. Existing equipment/dependency/app checks decide whether the
family may run. At F's invocation slot, the PW adapter transfers verified
descriptors/session authorization and permits pytest execution. It does not
start items individually. Earlier ordinary-family failures do not suppress F
unless interruption or an actual prerequisite requires it. A queued engine's
wait is tied to the parent session/overall deadline, not the prototype's fixed
60-second socket timeout. Cancellation also closes/reaps collected but queued
engines without acquiring test equipment. Revalidate declared module/helper,
configuration and package identities against the collected manifest before
eligibility. A mismatch fails admission and requires a fresh invocation rather
than silently recollecting different code.

`--list` uses collection only, displays the nine IDs and prerequisites in the
parent plan, and then terminates the collector without eligibility or owned
output. Collection may read declared source/package files but may not compile,
probe the app, create scratch/cache/bytecode, acquire a resource, or touch old
output. Disable plugin autoload and cache/bytecode writes; review the sole family
module's import path. Independent no-execution/file-snapshot controls cover this
boundary. This is a controlled trusted import, not a claim that pytest sandboxes
arbitrary Python imports.

Syntax/import/collection errors, duplicate IDs or empty collection reject the
plan with exit 2 before output replacement; stderr identifies the source and
collection phase. No partial item list becomes an executable selection. A missing
pytest installation is a declared equipment failure: during execution account
for F as unrun with `items: unavailable` and let independent families proceed,
as for other missing equipment; never invent a zero-item pass. `--list` cannot
claim complete discovery in that condition and exits 2 without output changes.
The parent family selection remains known even when its child discovery is not.

## 4. Dependency and invocation changes

Pin the already examined pytest **9.0.2**, pluggy **1.7.0**, iniconfig **2.3.1**,
packaging **26.3** and pygments **2.21.0** in a test-only hashed installation
manifest at proposed `tests/requirements-pytest.lock`. Continue using the
repository-resolved Homebrew Python 3.14 and its
recorded real path/version. The reference investigation used Python 3.14.9;
record the actual accepted interpreter when implementation begins.

Use an explicitly provisioned package target beneath `.tmp/pytest/`, keyed by
the lock digest and interpreter identity. A separate documented setup command,
proposed `tests/setup-pytest.sh`, uses the existing Python resolver to install
and verify that target. No default
test, collection, build or fixture downloads or repairs dependencies. The
engine alone adds that verified target to its import path, using the normal
`PW_PYTHON -B -S` entry form; no ambient site packages, `.pth` processing or
`PYTHONPATH`. PW helpers and command owners remain standard-library processes.
This keeps the existing interpreter identity comparison meaningful. Reject an
incompatible/missing target rather than falling back to ambient pytest.

Provision a fresh target under the checkout lock and publish it atomically;
never reinstall into a target used by a run. It is disposable cache under the
scratch guidance. Copy package/input hash manifests and setup receipt into run
evidence; keep no sole recovery record or decisive evidence in `.tmp/`.

Keep assertions enabled, serial execution, `--capture=fd`, `--import-mode=importlib`,
`-p no:cacheprovider`, explicit test/config paths and disabled plugin autoload.
Remove ambient pytest options before launch and validate the effective settings.
Native command environments/descriptor inheritance remain explicitly recorded;
pytest capture is supplementary to the directly retained native output. This
package-target startup differs from the demonstrated venv, so verify imports,
identity, FD capture and environment at the integration boundary once. Do not
claim it was covered by the old run.

This adds a dependency to an existing default member and makes complete `--list`
discovery require that package target. That is an intentional adoption cost for
review, not a reduction in production coverage or an automatic opt-out.

## 5. Reporting contract and reader experience

The family protocol is versioned independently of the product wire envelope.
Use the existing parent run ownership/retention format only where real consumers
need it; do not fabricate shell `test_begin`/`test_pass` events or a legacy
`report.json` for every pytest item.

Within `suites/runner_c_worker_harness/exec_control_states/`, retain:

```
selection.json                 # fixed manifest, mapping and identities
phases.jsonl                   # engine-only fsynced start/phase/session records
operations.jsonl               # PW command/ownership observations, separate writer
family.json                    # derived item and run-state account, version 1
summary.txt                    # readable projection, never an authority
artifacts/inputs/...           # immutable source closure and inventory
artifacts/baseline/...         # baseline build/run and canonical ledger
artifacts/<suffix>/...         # variant source hashes, commands, raw outputs
scratch/...                    # removed only after supervised commands settle
```

Phase records carry run/session, manifest digest, stable item ID, nodeid, sequence,
phase, outcome, diagnostic and relative evidence references. A shared fixture
failure names the fixture and affected IDs. Command receipts include intent,
actual invocation/environment/tool identities, returned status or missing status,
timeouts and independently obtained ownership/exit evidence. Byte inventories
are source identity, not a replacement for native observations.

Console summary and `summary.txt` show stable item, setup/call/teardown outcomes,
one short failure reason and exact relative artifact paths. They also show
separate **execution/accounting** and **ownership** states. Examples below are
proposed displays, not new experimental results:

| Reader sees | Evidence path and meaning |
| --- | --- |
| `F::esrch_as_success PASS — expected native assertion rejected formed mutation` | `artifacts/esrch_as_success/{source-sha256.json,build.stderr,run.stderr,command.json}` plus baseline receipt. A native nonzero exit is expected here; its exact designated assertion, successful compilation and formation checks are required. |
| `F::esrch_as_success FAIL call — mutation accepted` | Same paths show the submitted mutation and unexpected zero native status. Later applicable items still run. A wrong assertion names expected and observed rejection separately. |
| `F::fallback_from_group ERROR setup — baseline ledger mismatch; body not started` | `artifacts/baseline/{run.stdout,observed-call-policy.json,validation.json}` names the first differing attempt and links expected golden/source identities. Production item has its own body failure. No mutant command receipt is invented. |
| `F::production ERROR setup — input closure could not be prepared` | Input-preparation receipt names the missing/unreadable file; native invocation absent. Setup and missing body remain distinguishable. |
| `F::local_deadline_as_native_errno FAIL teardown — shared inputs changed` | Call remains passed; teardown diagnostic links immutable input before/after inventories. A session-finalizer report attached to the last item explicitly names its shared scope and affected items. Whole-family integrity fails without rewriting earlier assertion outcomes. |

Both body and teardown failures retain separate diagnostics and attachments.
Scratch deletion failure similarly appears as teardown/operational failure; it
is not a native assertion failure. If ordinary tests pass but a command cannot
be proven stopped, show `tests: passed; accounting: complete; ownership:
unresolved; run: unsuccessful`. If phase/session evidence is missing, accounting
is incomplete even if all visible calls passed. Missing exit evidence is never
rendered as a successful reap.

The PW reader joins the manifest to durable phases and operation receipts. It
preserves valid frames before a truncated tail, leaves absent phases incomplete,
and records malformed/duplicate/unselected records and nonterminal sessions as
errors. It never reruns a missing item or infers its outcome from artifact names.
SIGINT stops queued items; engine SIGKILL preserves completed items, partial
native bytes and started-versus-unstarted identities. A full-family pass requires
all nine valid item accounts, successful engine/session termination, no unexpected
skips/xfails, no integrity/accounting errors and all ownership obligations closed.
Framework continuation must not be overridden by an ambient max-failure option.

Parent `case_results` continues to contain F once, with a typed family-summary
reference and separate nested item counts. A complete set of failing phases is
`completed/fail`; missing item/session evidence is `unrun` with an accounting
error for compatibility with the existing completion counters. **`unrun` does
not mean never started.** Every new family parent result also carries required
`execution_state` (`not_started`, `started`, `unknown`) and `accounting_state`
(`complete`, `incomplete`, `unavailable`), a reason code and the decisive evidence
references. Collection alone is not family execution. A durable item-start or
actual PW command-start observation establishes `started`; a recorded refusal
before eligibility establishes `not_started`. Eligibility without surviving
start/non-start evidence yields `unknown`, not an inferred non-start.

The ordinary console, parent summary and release failure diagnostic must display
these states directly, for example:

```
F  INCOMPLETE — execution started; engine lost; 1/9 items complete; ownership pending
F  NOT STARTED — missing clang; item accounting unavailable; no execution eligibility
F  INCOMPLETE — execution start unknown after eligibility; phase evidence missing
```

Do not present all three as just `UNRUN`. Readers of a declared new family require
the accompanying states; a missing state is malformed accounting. Old records
retain their original counters without fabricated start evidence. F passes only
when the family predicate above holds. Parent overall `ok`
also retains all ordinary-family, artifact and sleep rules. Top-level case counts
and nested item counts are labelled separately; nine items do not silently become
nine catalog cases. `suite_run.finish` must consult authoritative case outcomes
as well as errors: its present success calculation based on legacy report counts
cannot simply ignore the new family.

For mixed runs, retain `reports` and `counts` for actual legacy reports and label
that scope explicitly (`counts_scope: legacy_reports`). Add `case_outcome_counts`
derived from `case_results` for the parent console/reader's overall case summary;
F contributes one outcome there. Its nine item outcomes live in `family.json`.
The parent schema's existing ownership/completion fields remain compatible, with
typed family references as additive fields. Compatibility is established from
independently checked producer/selection information as specified below; absent
family fields never establish a legacy run. No phase data is duplicated into
fake shell reports to make old report counts look comprehensive.

### Required evidence cannot be removed by selecting the legacy reader

Before executing the battery, the outer PW invocation records the expected
evidence contract from the actual harness source/configuration and requested
selection: producer identity and protocol capability, catalog/source snapshot
digests, selected top-level family IDs with their engine kinds, and required
accounting/ownership receipt roles. This is independent of pytest's results and
of the later `case_results` family reference. It lists family obligations, not
a second registry of the nine item identities. Pytest's collected manifest still
owns those items. A small standard-library contract reader should own this
validation for dispatch, release acceptance and archive consumers.

For live acceptance, construct and retain that expectation in the outer release
invocation **before** starting `tests/run.sh`, using its recorded argv and verified
harness/catalog inputs. Pass it explicitly to the battery reader; do not derive
it from the returned run's optional engine fields. For ordinary runs the PW
planner publishes its pre-execution contract alongside the owner/plan; inspection
checks it against the recorded producer source identity. Product-app provenance
alone does not identify which harness executed the tests.

For portable evidence, archive the outer invocation contract, the relevant
harness/catalog identity evidence and terminal ownership receipt with the run.
Bind them into the verified release/evidence inventory and its source/run
identity. The portable reader validates this against the independently established
harness provenance/expected contract for that release, not a profile guessed
from `family.json` or its absence. Required roles follow from that checked
producer/catalog contract even if an optional-looking reference is removed from
the run or archive manifest. The archive inventory establishes bytes and coverage;
recomputing its hashes after dropping a file does not discharge a required role.

Make the dependency explicit in the reader APIs: live acceptance/archive checks
receive an `expected_contract` from their outer invocation; portable verification
resolves the contract from a separately verified retained/release harness-source
identity and its matching snapshot. The source is the actual test harness,
recorded separately from the app build source. Use the repository's existing
source/retention/release provenance mechanisms; no new signing service is part
of this adoption. If that binding cannot be recovered, the reader can display
the record but cannot certify it by selecting a legacy fallback.

Legacy interpretation requires affirmative provenance identifying a producer
and selection whose contract did not require these roles—for example the
previously verified historical source/run or release identity and matching
source/catalog snapshot. Historical records remain readable without new fields
or rewriting. Unknown or stripped provenance is displayed as unverified and
cannot qualify a new acceptance as legacy. If provenance is unavailable, report
that missing prerequisite; do not infer age from timestamps, schema 1/2, or the
absence of engine metadata. Local source snapshots and archive receipts must
be bound to an independently checked source/release identity; internally
self-consistent hashes alone are not authenticity proof. This covers omitted
evidence/downgrade handling, not replacement of every external trust anchor.

The terminal ownership receipt is mandatory for a new selected engine family,
even when its registered-command set is empty. It identifies the complete
registered operation set (bound to the durable registration/operations record),
settlement/closure evidence and any unresolved entries. The archived copy must
match those roles and identities; “no receipt/reference/pending flag” cannot
mean “no resources.” A verified legacy producer had no such receipt obligation;
that fact must come from its provenance, not the missing receipt. The portable
reader must not require a now-unavailable local ownership registry to validate
a properly closed archived run.

Consumer changes are explicit:

| Consumer | Required adaptation |
| --- | --- |
| `test_cli.py`, `suite_run.py`, `--list` | Engine route, collection manifest and one family result; bypass legacy event/report reconciliation for F only. Keep legacy namespace scanning and tampering detection for other cases. Distinguish legacy report counts from family outcomes. |
| `retention.py` replacement/pruning, release cleanup/rotation | Consult durable ownership, including ambiguous pending records; protect output/ownership together. Existing schema-1 parent completion validation remains useful, not sufficient for cleanup. |
| `release_accept.py:battery_problems`, `release_archive.py:battery_record` | Take the independently checked invocation/source contract, require every expected family account and its parent execution/accounting states, then validate item completeness and ownership. Reject stripped declarations/references as well as missing summaries. Preserve historical interpretation only with affirmative legacy provenance; keep default-selection and artifact requirements. |
| `release_runs.py` evidence snapshots | Parent still at `tests/run.json`; the existing whole-tree packer includes in-run family files. Include the outer invocation/source contract and terminal ownership receipt, verify their binding and required roles independently of optional references, and refuse missing closure even if mutable archive inventories are recomputed. A closed portable run needs no live local registry. No product envelope change. |
| Dispatcher/source-drift controls and documentation | Teach engine routes as catalog commands without exempting missing/duplicate paths. Update Python startup/dependency declarations, suite/output documentation and fixture-input inventories. |
| Architecture citations | Move `exec_control_states` citations from the retired shell block to the new owning test/helper in `docs/architecture.json`; regenerate `docs/ARCHITECTURE.md`/`docs/WORKER.md` through their owner. The native observation and its limits stay the same. |

## 6. Authorized implementation stages

Each stage has a fixed source commit before observation. Use separate candidate
and accepted-comparison worktrees and fresh output, never the frozen investigations.
No actor changes sources, expectations or shared equipment during another run.

Stage reviews are internal execution checkpoints, not requests for another
conversation or permission. Commit, inspect and verify the recovery state machine
and evidence contract before enabling their shared dependencies. Resolve routine
choices and correct candidate defects autonomously; retain consequential failed
observations before correction. Continue through setup, passing runs, checkpoints
and ordinary intermediate failures until the endpoint below.

The endpoint is completion of all implementation stages, the acceptance matrix,
the emitted-report walkthrough, evidence retention and the final disposition for
this family. Deliver a committed candidate, a supported acceptance or abandonment
recommendation, and a usable recovery index locating decisive runs and any owned
resources. Keep this plan and its records current. No merge or wider adoption is
authorized. Return early only for a production behavior/oracle change requiring
the user's participation, an ownership boundary that cannot satisfy this contract
within scope, or an external blocker that cannot be resolved; preserve localized
evidence and present a concrete decision in that case.

The candidate's ordinary family command remains concrete and public (use a new
run name each time; the app is inspected, never repaired by this command):

```sh
PW_APP_DIR=/Users/raccoon/Desktop/Security/PolicyWitness/dist/PolicyWitness.app \
PW_TEST_OUT_DIR=tests/out/runs/pytest-exec-normal-01 \
tests/run.sh --case runner_c_worker_harness/exec_control_states
```

1. **Dependency and domain preparation.** Provision the fixed test packages
   explicitly; record interpreter/packages/toolchain. Extract the current native
   recipe and canonical parser without changing the fixture/golden/production
   bytes. Pair mutation/expectation declarations. Add the pytest module with
   baseline prerequisite caching and per-variant inputs. In the isolated branch,
   only the old public route remains authoritative until the route switch; new
   equipment is not advertised as accepted execution. Review import-only behavior
   and phase/evidence mapping before any experimental execution.
2. **PW integration and ownership.** Add the collection barrier, durable reader,
   command ownership and retention guards; extend the existing dispatcher rather
   than copy its artifact/equipment/sleep logic. Preserve the datagram-reset and
   valid-prefix corrections as integration invariants. First seal the recovery
   transitions/disposition table, recovery-only invocation and independent source
   contract; exercise their refusal/recovery/downgrade controls in isolated
   fixtures before making the registry a shared admission dependency. Check
   package startup, explicit parent execution states, mixed-family accounting
   and the real compiler-group lifetime with the targeted controls below. This
   is the main new operational work and a stopping point if its boundary is not
   credible.
3. **Atomic route switch in the candidate branch.** Change F's catalog route,
   remove its shell `test_selected` block and the native checker's executable
   main loop, and complete reporting/consumer changes together. Keep its domain
   helper importable and the standalone fixture build tool as equipment, not an
   alternate test runner. Direct old checker execution should point to the public
   command and refuse. All credited candidate runs now use `tests/run.sh`; old
   behavior is obtained only from the clearly labelled comparison worktree.
4. **Diagnosis and obligation acceptance.** Run the matrix below through the
   public path. Perform the emitted-report walkthrough below, including shared
   baseline/finalizer scope and remaining observation applicability. Inspect
   actual reports and retained native observations, not just return codes.
   Compare the accepted branch's ordinary result and representative
   failures with candidate results. Record actual edited owners, removed wrapper/
   loop/declarations, added integration and what remains shared. Complete the
   targeted existing regression cases and reader controls, update current docs
   and generated citations, then seal source/run identities.
5. **Decision for this family only.** Present the evidence and any remaining
   obligations for acceptance. Successful family adoption authorizes no expansion.
   If diagnosis/organization does not improve or preservation is not credible,
   abandon the candidate route and retain its evidence. Acceptance does not depend
   on a global harness-replacement argument or an agent-time productivity claim.

The proposed source locations guide the authorized implementation. Update
`tests/README.md`, the owning suite/fixture
READMEs, `docs/DEPENDENCIES.md`, `tests/AGENTS.md` where engine-owned items require
clarification, applicable verification guidance, and the source-drift rules and
their independent rejection controls together. Keep “every case is registered”
for top-level families/cases; document pytest item ownership explicitly rather
than weakening registration checks generally. Inventory new dependency/command
sources in disposable control fixtures so their copied trees remain meaningful.

## 7. Proportionate acceptance evidence

Reuse the completed investigation for bounded architecture feasibility. Do not
rerun its entire 18-group demonstrator as an adoption prerequisite. The gaps
below concern the real family and its integration into public execution.

| Exercise | Inspectable acceptance observation |
| --- | --- |
| Ordinary F, old and candidate, same native inputs/toolchain | Candidate has nine named items, unchanged 58-attempt canonical ledger, six exact native refusals and two exact include refusals. No observation is weakened to “any nonzero exit.” |
| Absent mutation anchor in a disposable source copy; accepted mutation or wrong rejection in a controlled copy | Reports name each affected variant/phase and retain submitted source/output; formation failure is not credited as rejection. Baseline stays independently valid where the intervention allows it. Compare the old diagnostic without changing old sources during its run. |
| Invalid unmodified baseline/golden comparison using separate controlled inputs | Production body fails; dependents have setup errors and no variant-command starts. Neither skipped bodies nor unavailable prerequisites become passing controls. Never rewrite the accepted golden. |
| Setup acquisition followed by failure; body failure plus teardown failure | Real command ownership is published before launch; both diagnostics survive; later independent applicable work continues. Outside peer/exit observations establish resource disposition, not the candidate summary. |
| Import/syntax error, duplicate/empty IDs and publication refusal | No native command starts; collection fails explicitly; protected output/app bytes unchanged. Successful `--list` is read-only and agrees with the executing manifest. |
| Missing package/clang, invalid app and a mixed selection | F unrun with reason; independent eligible legacy case continues. Default/suite/case union still executes F once. App before/after inspection and interpreter/sleep records retain their meanings. Use existing fixture bundles for damaged-app controls. |
| Valid-prefix/truncated-tail, missing finish and contradictory phases | Earlier completed items retained, later/unreported items incomplete, overall unsuccessful. Outside expected observations do not import the candidate account function. Reuse the established accounting stimuli at the integrated reader boundary. |
| Interrupt/death with one completed item, active supervised command and queued work | Independent start receipts distinguish active from queued; partial logs survive; completed evidence survives; command owner holds the actual lock; ordinary SIGINT cancels queued legacy work too. Engine-only death follows existing independent-case continuation policy once ownership settles. |
| Death of outer/family supervisor while command/descendant survives | The new command owner or an unresolved durable record preserves ownership; a competing execution cannot acquire eligibility; authenticated recovery/observed exits permit closure. A dropped-hold/false-closure control must be rejected. This addresses the compiler integration gap, not arbitrary escaped processes. |
| Unresolved ownership and pruning/replacement/release readers | All refuse disposal/acceptance despite visible passing item reports; closed unpinned control output becomes eligible. Pin decisive failure before any destructive cleanup control; controls act only on disposable fixture runs. |

Extend those existing integration exercises with the following precise controls;
they do not start a separate feasibility workstream:

| Refinement | Required observation |
| --- | --- |
| Crash at each owner/command launch authorization boundary, including before launch and before PID/start publication | Independently record whether a gated owner/native command actually started. Recovery must not infer non-start from a missing PID receipt. With revoked authorization and affirmative no-launch evidence it closes the reservation without signalling; ambiguous authorization/start remains checkout-blocking. |
| Crash after direct command return but before settlement; and after durable quiescence but before closure | Return-only evidence cannot close possible descendants. Durable matching settlement plus revoked launch authority permits idempotent closure or output-only retention for isolated cleanup; an unrelated build/test can then proceed while pruning the held run still refuses. |
| Recovery entry while admission refuses; active owner, stale/reused identity and interrupted recovery | Preview remains usable/read-only; apply has no test-launch capability. Refuse an active session or identity mismatch without signals, preserve unknowns, and resume justified recovery without losing original evidence or clearing unrelated holds. |
| Strip family engine declaration, typed reference, or both while leaving apparent passing parent fields | Against the independently captured new-producer/selection contract, reject even when the summary file still exists. Also remove the family directory and all run-local hints: missing source/contract evidence cannot create a legacy pass. Keep a positively identified legacy neighbor readable under its own contract. |
| Strip terminal ownership receipt and its references from a new portable run | Recompute the mutable archive inventory, summary copies and checksums so a generic checksum failure cannot supply the result. The independently checked expected roles must still require closure; removing a receipt declaration, claiming an empty operation set, or making local registry lookup unavailable must not bypass it. A valid closed portable neighbor verifies without the original local registry. |
| Parent result for engine death, missing equipment and an indeterminate start window | The actual ordinary display and reader fields distinguish `started/incomplete`, `not_started/unavailable` and `unknown/incomplete`; none is shown merely as “never ran.” Removing the required state from a new family is rejected. |

Each deletion/downgrade control fixes its expected invocation/source contract
outside the mutated result/archive fixture before mutation. Check that anchor
remains unchanged. Also exercise removal or contradiction of the archived copy
of that contract: the external expected identity still requires the missing
roles, or verification fails for missing provenance; it never falls back to
legacy. These controls test semantic completeness after repairing transport
checksums, not adversarial replacement of all trusted source/release identities.

### Acceptance walkthrough using emitted reports

For each representative failed variant, start from the actual parent console
summary or portable report and follow its links through: stable item ID;
setup/call/teardown diagnosis; exact submitted mutation and source inventory;
expected rejection versus observed assertion/status; raw compiler/native output;
and its baseline/applicability and ownership receipts. A maintainer must be able
to make that trace without reconstructing the shell loop or reading the result
interpreter's implementation. Record the actual displayed excerpts, paths and
answers beside the pinned run. The example strings in this plan are not an
acceptance substitute. Any misleading emitted report is a consequential failed
acceptance result, retained before correcting the renderer/association.

For a shared baseline failure, the ordinary display should show one baseline
cause and its evidence, the production outcome, the list of dependent items
whose bodies did not run, and why no mutation rejection is credited. Preserve
the baseline's raw native observation even though it did not satisfy the golden;
do not describe the unattempted controls as independent native failures. Detailed
pytest phase records remain available behind the grouped explanation.

For a session finalizer failure, name the shared fixture, its affected item
scope and the fact that pytest attached the report to the last item's teardown.
Preserve each recorded body outcome. Distinguish **input-integrity uncertainty**
(show the changed inputs and qualify dependent observation applicability until
their retained per-variant input receipts establish otherwise) from **cleanup
failure after complete observations** (show the cleanup/ownership hold without
claiming the native assertions failed). Neither permits family success. Inspect
both emitted cases: a correct last-item traceback alone is insufficient if a
reader cannot tell which observations remain usable or why.

The acceptance record states whether every link resolved and whether a reader
could identify the phase, submitted control, expected/observed rejection, shared
failure scope, observation limitations and operational disposition. Compare
that experience with the retained current-harness failure where useful. This
is an exposed diagnostic evaluation, not a timed or blinded productivity test.

For the changed dispatcher, run `dispatcher/selection_controls`,
`accounting_controls`, `cancellation_controls`, `retention_controls` and `controls`;
run `artifact_controls` if its gate/inspection path changes rather than just a
new adapter calling it. Add narrowly scoped integration controls to those owners
or one registered dispatcher case, not a second ad hoc production harness.
Run `source_drift/runner_source_manifests_agree`, `architecture_documentation`,
`generator_contract` and `direct_python_start` (each with the `source_drift/`
prefix), plus `shell_helpers/python_startup` and
`shell_helpers/interpreter_boundary`. Extend/run `preflight/release_controls`
for acceptance, `preflight/release_publish_controls` for archive readers and
`preflight/release_rotation_controls` for portable evidence and the ownership
blocker. Extend the existing lock admission controls in
`dispatcher/retention_controls` and the build-side lock refusal controls in
`preflight/build_refusal_controls` for the new namespace guard; extend their
fixture inputs explicitly. The latter uses its declared signing/build equipment
and disposable fixture outputs, not a rebuild of the accepted app.
At implementation time record exact canonical selections, source/configuration
and applicable app/tool identities; this plan does not credit unexecuted tests.

A complete `runner_c_worker_harness` suite against the accepted unchanged app
checks neighboring selection paths. No native production behavior changes are
planned, so a fresh build, entire live battery, ordering mutation control or
release operation is not prescribed solely for adopting this family. Broaden
verification if implementation crosses those boundaries, using repository rules;
return production defects or changed promises with localized evidence to the
user before making that change. Protect the original tests/docs that establish
the promise while that decision is pending.

Acceptance answers five concrete questions:

1. Can a reader identify the item, failing phase and native evidence from the
   report without reconstructing the shell loop? Inspect the retained examples.
2. Is family logic found in one test module and one domain helper, with shared
   infrastructure clearly separate? Inspect the actual edit map.
3. Are the old wrapper/variant loop and parallel expectation maps retired, with
   one manifest and one public route? Check source and selection receipts.
4. Do complete native sequences, baseline applicability and the independent
   formation/rejection controls retain their meaning? Compare raw witnesses.
5. Can incomplete accounting or unresolved ownership still appear successful or
   disposable? The negative controls must refute that possibility at the family,
   parent, retention and release-reader boundaries.

## 8. Evidence, abandonment and review decisions

Pin decisive results, representative diagnostic comparisons and consequential
failures before pruning, with actual source commit/configuration and raw evidence.
Use fresh `PW_TEST_OUT_DIR=tests/out/runs/<name>` for every separate run. Review
disposable output periodically using repository pruning tools; impose no fixed
quota. Keep ownership records and staged resources until their closure is
established. Never prune prior engagement evidence or modify its pins. A failed
control and its correction retain separate source/run identities.

Before acceptance the candidate lives only in its implementation worktree;
abandonment leaves the accepted route unchanged. Preserve the candidate commit
and pins, settle or retain its owned resources, then use supported cleanup only
for eligible disposable output. Do not leave a fallback toggle selecting two
implementations of F. After a later accepted integration, reversal would be a
reviewed revert of the coherent route/consumer change; it must continue to read
or preserve new-format retained evidence and pending ownership. Deleting new
readers while their records remain unresolved is not a rollback plan.

The family choice and ownership split are supported by the user's review.
The refinements above belong to integration stage 2 and acceptance stage 4;
they preserve the **one-family** boundary. Proposed defaults are fixed:
retain app/worker admission and default membership; use whole-family public
selection; retain nine complete native variants; keep operational ownership
outside pytest. There is no unresolved family-selection choice requiring another
investigation or routine reauthorization. A compiler/resource boundary that cannot
meet the contract within scope, a production behavior/oracle change, or an external
blocker that cannot be resolved requires the user's participation with localized
evidence and a concrete decision, rather than unbounded extension.

Planning records and this plan are temporary acceptance material and are retired
together under CONTRIBUTING.md. No permanent index links to them. Original
counterfactual, demonstrations, maintenance comparison, pinned evidence, unknown
worker/resource directories and accepted application remain in place.
