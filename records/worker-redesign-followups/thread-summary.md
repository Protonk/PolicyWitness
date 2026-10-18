# Worker redesign: thread summary

Date: 2026-10-18. Associated plan:
[WORKER-REDESIGN-PLAN.md](../../WORKER-REDESIGN-PLAN.md).
This report covers the daughter investigations, user decisions and accepted
follow-up work through the privacy-consent documentation correction. The
preceding repository commit is `3f2e76b`; this report and that correction are
documentation-only additions. The last runtime implementation is `a458b28`.

## Outcome and sequencing

Five scoped refactors are implemented, reviewed, committed and accepted against
signed builds. The execution-environment investigation concluded with a prose
clarification and retention of the current application model. No broader exec
supervisor, configuration schema or environment capability was selected.

We settled worker terminal lifetime first because it determines which process
and evidence survive while the host finishes collection. Descriptor, exec and
sysctl investigations then ran through sub-agents in parallel; native experiments,
builds and test executions were serialized in the shared checkout. Configuration
inventory and review followed, with environment review last. Each implementation
followed a concrete user decision and an executable plan, followed by coordinator
review, appropriate independent review and signed-app acceptance.

The associated plans below link the original investigations, source snapshots,
acceptance records and retained evidence. Those records preserve failures and
their repairs; this summary does not replace them. Raw managed test output is
gitignored and available only in this checkout, with credited runs pinned for
retention.

## Decisions and implemented changes

**Terminal lifetime and phase qualification — WA-04/WA-08.**
The [terminal-exit plan](../../controller/tools/pw_probe_runner/TERMINAL-EXIT-REFACTOR-PLAN.md)
was implemented in `f382cf6`. A worker erases accepted token storage before its
existing terminal publication and exits promptly afterward. Ordinary returns
and cancellation also erase accepted storage. The host performs final
acknowledgement reconciliation after confirmed reap, including abnormal exit.
Cancellation, host grace/termination/reap cleanup and synchronous validator
collection remain in place. Byte erasure is separate from native extension
release; worker exit supplies no descendant-supervision guarantee.

The adopted rule removes the need to reconstruct each query's target liveness.
On ordinary replies, an otherwise admissible query qualifies as a live-specimen
prediction only with successful policy application, the established phase
collection/release/worker-acknowledgement chain, uninterrupted ownership and the
existing eligibility checks. Without that basis, received native query records
remain available with unestablished order. Missing acknowledgement does not
prove a query encountered an exited target. Later abnormal termination does not
withdraw ordering already established. Degraded reporting-failure replies retain
their separate diagnostic-only boundary.

User review strengthened three controls: independently scan the fixed token
capacity with nonzero bytes beyond the terminating NUL; observe erasure at the
publication boundary so reversed operations fail; and recover an acknowledgement
missed between samples before fatal exit without `done`, preserving the abnormal
disposition. A later documentation correction (`503156f`) qualified worker token
cleanup as applying after channel acceptance: earlier mapping/header refusals
can leave erasure to the host. Existing eligibility and field meanings required
no version change.

**Exec observation and cleanup evidence — WA-03.**
The [exec-evidence plan](../../controller/tools/pw_probe_runner/EXEC-EVIDENCE-REFACTOR-PLAN.md)
was implemented in `924a6ed`. Optional `attempt.exec_observation` separates
collection observations frozen before cleanup, termination requests and their
native returns, and the owned leader's final wait/reap facts. Cleanup results
cannot become pre-cleanup completion observations. Signal success establishes
neither exit nor group absence. Missing metadata remains unknown, and publication
gates the new evidence. Producer, shared layout, Swift/Rust/Python readers and
controls were updated together. Existing cleanup behavior and aggregate status
meanings were preserved.

The investigation found that same-group descendants can remain after ordinary
leader-plus-EOF completion, and that worker loss poses a separate ownership
problem. An external group owner was feasible but would add authority and
child-visible state without containing escaped descendants. We chose evidence
separation and deferred stronger cleanup or supervision.

**Host evidence-descriptor lifetime — WA-01.**
The [descriptor plan](../../runner/Sources/PWRunnerCore/LAUNCH-DESCRIPTOR-REFACTOR-PLAN.md)
was implemented in `0262dfe`. After successful worker spawn and the existing
transfer-deadline construction, the host closes its evidence descriptor and
relinquishes close ownership. Its mapping remains available through collection
and teardown. Pre-spawn refusal cleanup is preserved, and deferred cleanup
cannot close another owner's reuse of the descriptor number. Independent
object, reuse and unmap observations test these distinctions. Broader descriptor
inheritance, low-number collisions and worker aliases remain outside this change.

**Bounded sysctl read — WA-11.**
The [sysctl disclosure plan](../../controller/tools/pw_probe_runner/SYSCTL-DISCLOSURE-REFACTOR-PLAN.md)
was implemented in `f699758`. `PW_SYSCTL_READ_BYTES` names the existing 4096-byte
capacity; the limits inventory and generated documentation disclose the bound
and discarded results. The operation remains one post-apply read with a non-null
destination, without sizing, retry or allocation. An independent call-boundary
oracle requires literal capacity 4096 and rejects a 4095 mutation. The
investigation did not justify interpreting the raw returned length as required
size or bytes copied; publishing additional length metadata remains optional.

**Execution configuration and validator default — WA-07.**
The [configuration review](../../runner/Sources/PWRunnerCore/EXECUTION-CONFIGURATION-PLAN.md)
retained the existing request and shared production path. Supplied overrides,
selected configuration and observed interventions remain distinct: a control can
be default-valued, inert, sanitized or never reached. Existing evidence supports
qualified documentation observations without a new request mode or schema.

The user selected removal of the implicit app-level validator fallback. The
[validator-default plan](../../runner/Sources/PWRunnerCore/VALIDATOR-DEFAULT-REFACTOR-PLAN.md)
was implemented in `a458b28`, following decision commit `6380645`. Default
selection now resolves directly to the service bundle's
`Contents/MacOS/sb_api_validator`; admitted explicit overrides retain precedence.
Selection does not establish launch or authenticate executed bytes. Reached
launch failures retain native evidence; excluded queries and earlier worker
refusals do not invent validator failures. Supported bundles already contain
the local helper; manually arranged older layouts lose the implicit fallback.
Dynamic allowance records and native intervention observations were deferred.

**Execution environment — WA-10.**
The [environment investigation](../../controller/src/EXECUTION-ENVIRONMENT-PLAN.md),
recorded in `3f2e76b`, reviewed sources and existing evidence with independent
review. It performed no new execution experiment or privacy-setting change.
Selected binary/signing provenance, controller OS facts, issuer credentials and
file-owner IDs do not measure worker credentials or privacy-consent state.
Worker UID/EUID/GID/EGID observations could help a concrete cross-scope comparison,
but no current consumer justified permanent fields or a general environment
schema. Historical location-sensitive failures remain observations, without an
upgraded causal attribution.

The user accepted retention of the current model and refined the documentation
scope. The [worker account](../../docs/WORKER.md#starting-authority-and-ambient-context)
now states that PW does not determine whether privacy consent mediation affected
an attempt, that an error or timeout leaves this unresolved, and where existing
target-selection guidance lives. The generic permission-preflight design
argument stays in the investigation record.

## Verification and repairs

Each runtime implementation received a signed build and the full default battery,
with additional controls selected by its plan. Acceptance describes the tested
source and any replacement case credit explicitly:

| Implementation | Accepted verification |
| --- | --- |
| Terminal exit | All 192 default cases have passing credit. The initial run passed 189 and failed 3; the seven-case repair run passed, including 458 Swift tests and both required acknowledgement/ordering mutation controls. |
| Exec evidence | All 192 default cases have passing credit. The initial full run passed 191 and failed the opt-in selection check; the three-case repair/live-control run passed. The full Swift executable passed 461 tests; additional reader, producer and owning-suite controls passed. |
| Descriptor lifetime | Targeted 3/3 and full default 193/193 passed, including 461 Swift tests. |
| Sysctl disclosure | Targeted 3/3 and full default 194/194 passed, including 461 Swift tests. |
| Validator default | Full default 194/194 passed, including 465 Swift tests. After the console-receipt correction, all five affected cases passed again; final credit uses those five and the other 189 original passes. Six corrected console receipts parsed. |

Terminal acceptance repaired the documentation and selection test oracles
and four Swift clock controls that had required raw `allow` after worker refusal.
The corrected clock controls preserve the actual native answer without imposing
a target-liveness interpretation. Exec acceptance repaired missing aggregate
opt-in membership; an earlier shape-golden failure was resolved by reviewing the
intended optional response shape. Original failures remain retained.

The user's side investigation found one buffered `print` mixing with direct
stdout progress writes in the Swift tests. The immediate correction writes the
complete record through `FileHandle.standardOutput.write`. It changed no app
input or assertion; the unchanged signed app was retained and affected evidence
rerun. A broader receipt-artifact follow-up remains outstanding.

Request/response/envelope versions remain 5/23/7. The exec payload uses reserved
slot space; slot size and existing offsets remain unchanged. Latest runtime
acceptance is tied to `a458b28` and worker identity
`4cb19db043606894ace2e978434f8805edf4c79245f3588cc68a33b36deca9e8`.
These are development acceptance results, not notarized-release acceptance.
The final prose/report changes do not change the accepted app; their verification
is limited to documentation and generated-copy consistency. Architecture and
limits generator checks passed, as did local-link/anchor and whitespace checks
for all four changed Markdown files. No build or runtime test was repeated for
this documentation-only change.

## Remaining work and decisions

The parent's retained documentation workstream, WA-02/WA-05/WA-06/WA-09, is the
next substantial unfinished work: attach support to particular claims, represent
identifiable observations and their applicability, separate acquisition placement
from policy-specific observations, and improve the account of holders, shared
objects, multiple resource purposes and source ownership. No manifest or graph
redesign has been selected. Daughter acceptance does not automatically close
the separate [worker-documentation register](../../docs/WORKER-INST-DOC-PLAN.md).

The test-harness follow-up is also unfinished: standardize a shared console
writer, test alternating large JSON records and progress, and retain required
machine-readable receipts as separate validated artifacts before case success.
A single direct write is not a universal interleaving guarantee.

Optional capability decisions remain separate: stronger ordinary exec-group
cleanup or worker-loss supervision, raw sysctl length metadata, dynamic validator
allowance/intervention records, and measured worker credentials for a concrete
consumer. None is a prerequisite identified by these investigations for the
retained documentation work, and none was silently included in the accepted
refactors. The completed work has no unresolved implementation blocker.
