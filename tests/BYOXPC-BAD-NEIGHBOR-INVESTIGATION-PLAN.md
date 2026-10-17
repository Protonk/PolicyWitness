# Investigate BYOXPC coexistence and resource ownership

## Problem and intended result

PolicyWitness tests should remain useful on a machine where another checkout or
tool leaves runners behind, starts requests at inconvenient times, and acquires
system resources without coordinating with this checkout. An unexpected
`already_ran` followed by an agent's discretionary rerun is not a satisfactory
test workflow. Nor would replacing that workflow with a passing test that never
executes its intended specimen solve the problem.

The deliverable of this plan is an evidence-supported design for that test
system, with enough resolved questions to write its implementation plan. This
is an investigation, not an instruction to implement a predetermined isolation
mechanism. In particular, determine whether holding a private PolicyWitness
resource can confer or maintain ownership of a corresponding system resource,
and whether that relationship eliminates checks that would otherwise be needed.
Do not assume either that it works or that ordinary shared-name coordination is
the best available design.

Use source analysis, small OS experiments, and controlled interference against
disposable resources. Finish with a concrete recommended design and its limits;
a survey of APIs or a collection of intermittent failures is insufficient.
Production rollout and conversion of the complete BYOXPC battery belong to a
subsequent implementation plan. Bounded probes and prototypes needed to settle
the design are part of this investigation.

This plan was prepared from the working tree on 2026-10-17 through source,
contract and platform-documentation review. No build, BYOXPC execution or live
resource interference was performed while preparing it. The reported neighbor
explanation for `already_ran` remains a hypothesis, not an established diagnosis.

## Findings to start from

| Evidence | Established behavior and its consequence |
| --- | --- |
| [Catalog](catalog.json), `runner_byoxpc`; [suite](suites/runner_byoxpc/README.md) | BYOXPC cases are currently excluded from the default battery. Record the actual selection when investigating a reported failure rather than assuming it came from the default selection. |
| [Session helper](fixtures/byoxpc/session.py), `install` | Copies a complete runner into unique `/private/tmp` staging and assigns a service with 12 random bytes in its suffix. It inspects registry/reconciliation and checks initial service/plist absence. Ordinary tests do not deliberately share the bundled runner's name. Initial uniqueness does not establish continued ownership. |
| Session helper, `retire_host`; [suite wrapper](suites/runner_byoxpc/run.sh) | Setup performs a real `runner verify`, then waits for its host to retire. That wait currently treats a failed `launchctl print` or a listing without a matching PID as retirement. The wrapper reuses the installed service across selected specimen scripts without an equivalent handoff between those scripts. Unknown inspection and observed absence need separate treatment in the investigation's own oracle. |
| [Service](../runner/Sources/PWRunnerCore/PWRunnerService.swift), `PWRunnerAdmission` and `runSpecimen` | One host shares one terminal claim across connections. The claim precedes request decoding; the owner schedules exit after replying, with a 50 ms delay. `already_ran` establishes an occupied claim, not who occupied it. A preceding local request can produce the same symptom as another client. |
| [Single-use control](suites/runner_byoxpc/opt_in/single_use.py) | Already exercises two authorized clients against one held host, independent file effects, owner-only retirement and a subsequent fresh host. It deliberately expects `already_ran`; it is not a coexistence guarantee for ordinary specimen sequences. |
| [Registry manager](../controller/src/runner_manager.rs), registry paths, locks and `launchctl_target` | Registry writers coordinate through a stable lock associated with the selected registry. `PW_RUNNER_REGISTRY` and child-local `HOME` can separate registry/plist files. User-scope installation still targets `gui/<actual uid>`. File isolation and separate checkout locks do not isolate that launchd namespace. |
| [Installer](../controller/src/runner_commands.rs), `cmd_runner_install` | Checks selected-registry conflicts and plist existence, records pending installation, creates the plist exclusively, and bootstraps before inspecting the loaded service. The fixture's earlier live-service check does not reserve that service through installation. Whether a particular intervening conflict is harmless refusal or a more serious problem requires evidence. |
| Registry manager, `service_ownership` and `remove_record` | Cleanup persists pending ownership and distinguishes owned, unowned, ambiguous and unknown state. Live ownership uses the observed executable path; removal subsequently addresses the service by name. Investigate replacement between observation and action, including reuse of the same path. These code boundaries identify questions, not demonstrated live race failures. |
| [External client](../runner/Clients/PWRunnerClient/main.swift); service caller authorization | The client connects by Mach service name. Caller authorization checks signing identity, not the originating test session. Another checkout using an allowed signed client can satisfy that authorization. Registry selection and a reply's self-reported bundle identifier alone do not independently establish which service generation handled a request. |
| [Recovery controls](suites/runner_byoxpc/opt_in/registry_recovery.py), [setup controls](suites/shell_helpers/check_byoxpc_setup.py), [ownership contract](fixtures/byoxpc/README.md) | Existing coverage supplies durable recovery, registry contention, foreign/unknown state and partial-installation controls. Extend it where applicable; fake OS responses cannot establish launchd namespace or peer-identity guarantees. |

Read [test guidance](AGENTS.md), [controller guidance](../controller/AGENTS.md),
[runner guidance](../runner/AGENTS.md), the
[external-runner contract](../docs/PolicyWitness.md#external-runners-byoxpc) and
[planning guidance](../CONTRIBUTING.md#planning-a-change) before execution.
Recheck the source boundaries above against the executor's snapshot, including
uncommitted changes. Preserve unrelated work.

## Operating model and evaluation criteria

Start with two independent processes or checkouts under the same UID and GUI
login. The neighbor need not honor PW locks, use the same registry, wait for
retirement, or clean up correctly. It may use the same signed client, discover
an advertised name, reuse a familiar name or path, run verification repeatedly,
and disappear at any lifecycle boundary. It is not assumed to compromise the
kernel or change an unrelated user's credentials.

Use adversarial scheduling to test this nonmalicious coexistence model: choose
the most inconvenient legal time for each action. Separately assess whether a
candidate mechanism needs stronger protection against a same-UID actor who
deliberately tries to bypass it. Do not silently depend on name secrecy, a
cooperative lock, or filesystem permissions between processes with the same UID.
Conversely, do not expand every experiment into arbitrary malicious rewriting
or unbounded host exhaustion. State exactly which powers invalidate a claimed
guarantee and whether that matters for ordinary bad-neighbor behavior.

Evaluate designs on four separate properties:

1. **Evidence integrity:** a credited specimen ran once in the intended fresh
   host/worker context with the intended entitlements. A refusal, stale reply,
   foreign execution, or unobserved request outcome cannot stand in for it.
2. **Progress:** finite interference must permit useful testing to continue by
   a defined mechanism where feasible. A design that reports every collision
   correctly but makes routine coexistence unusable is not enough. Identify
   conditions, such as indefinitely held shared resources, under which only a
   bounded diagnostic is achievable.
3. **Noninterference and recovery:** PW does not evict or delete a neighbor's
   resources to make itself pass. Interrupted ownership remains recoverable;
   resource reuse cannot turn stale cleanup authority into authority over a
   replacement.
4. **Test fidelity:** isolation must preserve the behavior BYOXPC exists to
   test: public installation/selection, external launchd/XPC execution, worker
   entitlement transfer and single-use process boundaries. Identify any
   coverage a proposed transport or namespace change would cease to establish.

Do not mask failures with repeated specimens or wider arbitrary sleeps. A
design may use bounded acquisition or reconnection if evidence establishes when
no specimen has been admitted; the investigation must establish that boundary.
Once admission or an effect is uncertain, do not replay the request as if it
had never happened. Keep deliberately expected interference outcomes separate
from ordinary specimen pass/fail accounting.

## 1. Map resources and distinguish failure mechanisms

Trace installation, verification, selection, connection, admission, reply,
retirement and removal through the public CLI and shared fixtures. Produce a
resource/lifetime table with, for each resource:

- Its actual namespace and identity: label, Mach endpoint name, domain, registry
  path/lock inode, plist, staged executable, process generation, request or
  specimen target. Do not collapse these into a single “runner name.”
- Who acquires it, the operation that grants ownership, what is held afterward,
  and which other processes can discover, acquire, replace or release it.
- The transition where ownership is durable, the observation that supports it,
  and what survives owner/controller/host death or deleted diagnostic output.
- What the present locks protect and what can happen outside each lock; where
  an observation can become stale before its dependent action.

Include default shared-registry contention and separate registries in separate
rows. Exercise shared-registry semantics with both actors pointing at one
fixture-owned registry, and trace how the ordinary default path reaches that
same locking mechanism; do not deliberately monopolize an unrelated live
registry. Trace additional shared dependencies rather than limiting the inventory
to launchd: staging and specimen paths, sockets/ports, signing resources,
launch throttling, and process/descriptor limits are candidates. Prioritize
resources the actual execution path shares; distinguish logical ownership
conflicts from general scheduling or equipment unavailability.

Establish a no-neighbor control for consecutive requests to one installed
service. Correlate verification, prior specimen completion, host claim, host
exit and next admission. Compare it with a controlled second authorized client
that consumes the claim. Preserve observations that distinguish these causes;
an `already_ran` string alone cannot do so. Existing failures need not recur by
chance: use gates or a narrow observation seam to demonstrate a reachable
sequence. If a sequence cannot be observed reliably, report that observability
gap before drawing a causal conclusion.

The separate
[executable-preparation and ordering plan](../EXECUTION-PREPARATION-AND-ORDERING-PLAN.md)
addresses first-start preparation. Its completion is not a prerequisite for
this investigation, but record executable preparation and final signing so
startup delay is not mistaken for interference. Do not modify or silently
re-sign the inspected source app to rescue an experiment.

**Checkpoint:** provide the resource map, supported explanations for occupied
claims, and the smallest unresolved OS questions. This determines which
interference schedules and candidate mechanisms need live experiments.

## 2. Test whether private ownership can bind system ownership

Do this early, before building a large collection of guards. The question is
not merely whether PW can hold a private file or port. It is whether holding
that object gives the required exclusive relationship to the system resource
through acquisition, use, process replacement and cleanup, despite a neighbor
that does not participate in PW's convention.

Use current supported macOS APIs and the installed SDK/manuals. Record OS/SDK
versions and retain the relevant documentation excerpts with the findings.
There are useful starting constraints, but none settles the proposed design:

- The installed `launchctl(1)` manual distinguishes services from endpoints and
  says GUI and user domains share Mach lookup names despite having separate
  service collections. Changing `gui/<uid>` to `user/<uid>` is therefore not
  already a proof of independent names. It also explicitly disclaims the
  stability of `launchctl print` output; assess how much the proposed design
  would rely on that diagnostic interface.
- Apple's [anonymous NSXPC listener](https://developer.apple.com/documentation/foundation/nsxpclistener/anonymous%28%29)
  and [listener endpoint](https://developer.apple.com/documentation/foundation/nsxpclistenerendpoint)
  APIs provide an endpoint that can be passed to another process. Investigate
  endpoint possession, initial delivery and peer authentication separately.
  An endpoint does not by itself explain how a launchd-created process receives
  it or whether the resulting test still exercises named external BYOXPC.
- The [Mach-service listener flag](https://developer.apple.com/documentation/xpc/xpc_connection_mach_service_listener)
  is for services advertised by the process's launchd plist. Do not assume an
  arbitrary private port can simply be substituted for launchd registration.
  The installed `launchd.plist(5)` also marks `HideUntilCheckIn` and
  `ResetAtClose` incompatible with XPC; their names are not sufficient reasons
  to propose them here.
- The existing [checkout lock](lib/checkout_lock.py) uses a held descriptor and
  authenticated handoff for its own ownership boundary. It is a useful local
  example to examine, not evidence that such a descriptor reserves an unrelated
  launchd name or survives launchd spawning in the needed way.

Compare a small set of mechanisms, starting with the least machinery that could
meet the criteria. Include unique names/private registry paths as a baseline,
a cooperative lock as a limited comparator, and at least one serious attempt
to establish the private-resource relationship. Depending on documented
feasibility, that attempt may involve a held kernel object, supported namespace
isolation, an endpoint/rendezvous capability, or a reservation owner that passes
authority to a child. Also consider whether authenticated admission or an
observed lifecycle handoff is required even if name ownership is solved.
Do not implement a broker or migrate transport merely to complete this list.

For each viable candidate, answer with a minimal probe or a documented
impossibility/compatibility argument:

1. What exact operation grants exclusivity, over which identity and namespace?
   Does it reserve the actual disputed resource or just a PW-side description
   of it? What can another same-UID process still do while it is held?
2. Can the binding be established without a check-then-acquire gap? Where is
   ownership transferred to a launchd-created process, and how is the recipient
   identified? Do not assume inherited descriptors or environment variables
   supply an authenticated transfer across that boundary.
3. Does it identify a service registration, a particular host generation, or a
   request? Which remains valid after host exit, service reload, PID reuse or
   reuse of a label/path? How does the client prove it reached the intended peer?
4. What happens when a name is learned, a stale handle/token is presented, the
   cooperative path is bypassed, or the holder dies? Can cleanup act on the
   owned generation without removing its replacement? If not, what residual
   observations or restrictions are necessary?
5. Which current checks become redundant by a demonstrated guarantee, and which
   remain necessary? What additional equipment, persistent state, privilege,
   compatibility constraint or loss of BYOXPC coverage does the mechanism add?

These questions remain open because source inspection cannot establish the
OS's exclusivity, transfer and revocation semantics for the proposed mechanism.
Run the smallest real-OS probe that would distinguish the alternatives. If the
private binding works, carry it into the integrated experiment in step 4 and
test the checks it would replace. If it protects only cooperative users or
changes the tested transport, narrow its claim and compare it with the baseline.
If no mechanism prevents a particular interference, evaluate detection,
bounded acquisition, recovery or an explicit equipment limit for that case.
Do not respond by adding unbounded retries.

**Checkpoint:** select the strongest feasible candidate and a baseline for
integration, with evidence for rejected alternatives. Keep another candidate
only when a specific unresolved observation could change that selection.

## 3. Build controlled neighbor experiments

Use three roles: the test session under investigation, a neighbor actor, and an
outer experiment owner. The first two must not accidentally share a lock that
prevents the interference being tested. The outer owner controls timing and
owns every disposable resource created by either actor. From the session's
perspective the neighbor's resources are foreign; the outer owner cleans them
only after observing that the session preserved them.

Reuse [BYOXPC staging and durable receipts](fixtures/byoxpc/README.md) and
[caller-auth fixture practices](fixtures/caller_auth/README.md). Keep separate
durable ownership ledgers for both actors outside any registry or output being
deliberately lost or corrupted. Arm cleanup before acquisition. The existing
session helper can refuse cleanup after ownership substitution, so design the
outer recovery path before running such a schedule. It must recover only
fixture-owned resources, not weaken the victim's ownership checks.

Use observed milestones and acknowledged gates to arrange interleavings. Gate
before/after actual production boundaries, not by fabricating success, refusal,
or ownership. Prefer existing public operations; add the narrowest test-only
seam when an internal window otherwise cannot be selected. A bounded watchdog
terminates failed experiments; its expiry is not evidence of the intended PW
outcome. Arbitrary sleep offsets or repeated runs until a race occurs cannot
establish that the requested schedule happened.

Start with the following matrix. Refine it from the resource map; mark an
unreachable combination with its reason and evidence rather than silently
omitting it. Run both the current behavior and the candidate where relevant.

| Boundary | Neighbor action and question |
| --- | --- |
| Before setup | Leave an unrelated stale runner; then preoccupy the experiment's chosen label, Mach name or plist. Distinguish a loaded job without a plist, a plist without a job, and a record in a different registry. Can unrelated ordinary specimens still run? |
| After absence checks, before acquisition | Acquire the label or endpoint before pending publication, plist creation or bootstrap. Where does the OS decide the winner, and what ownership/recovery state does the loser retain? Separate identical labels from identical Mach names; include different labels advertising the same Mach name and the relevant GUI/user lookup relationship. |
| After bootstrap, before verification | Connect with an otherwise authorized client, including a malformed request that can consume admission. Can successful installation still be confused with readiness for the intended request? |
| Between requests | Act after verification's reply, before host exit, after an observed exit but before the next request, and between shared-suite leaves. Distinguish local retirement lag, neighbor admission and a replacement registration. |
| During a specimen | Send another request, or stop/reload the fixture-owned registration at a selected boundary. Include loss of the reply after an independently witnessed effect. Can the harness retain honest outcomes without crediting foreign work or duplicating its own attempt? |
| Between ownership observation and removal | Replace the fixture-owned registration or plist before bootout/unlink. Include a new generation under the same name, and where feasible the same executable path. Can stale cleanup affect the replacement? Separate service and plist ownership throughout. |
| Shared dependencies | Hold a shared fixture registry's lock while using distinct service names; repeat with separate registries and independent checkout owners. Exercise any additional demonstrated chokepoint with bounded fixture-owned contention. Does isolation remove the dependency or merely move it? |
| Owner death and recovery | Interrupt at pending install, successful bootstrap before receipt, active request, pending cleanup and bootout before persistence. Repeat recovery without original run output and with a neighbor occupying a reused name. Can recovery distinguish outstanding ownership from replacement? |

Within the matrix include a neighbor that releases a resource and one that holds
it through the experiment's bound. After finite interference ends, observe the
promised progress or recovery directly. A finite set of hand-picked schedules
does not prove arbitrary concurrency: explain which resource invariants cover
other schedules and which claims remain empirical.

Do not manipulate unrelated installed services or launchd domains, disable a
user's jobs, alter login/keychain/privacy settings, or create unbounded host
load. Use distinct disposable registries, bundles and exact targets. Scope live
work initially to user-scope BYOXPC in the logged-in GUI session; document
system-scope implications and any additional experiment/authority it would
require. A raw neighbor helper may bypass PW installation conventions to create
a legal launchd configuration, but must remain within the outer owner's exact
resource ledger.

## 4. Establish the result independently and choose the design

For every decisive schedule retain actor commands/configuration, source and
binary identities, signed entitlement read-backs, namespace/domain identities,
gate acknowledgements, request IDs, native statuses and raw output. Correlate
host/worker process observations with unique specimen effects in fixture-owned
paths. Distinguish service generation, host PID and worker PID; when available,
record an independent process-start identity rather than relying on PID alone.
Never infer retirement from an inspection error or an unrecognized listing.
Record observation limitations explicitly.

Each checker needs a no-interference positive control and a control that would
expose a false pass. As applicable, supply a foreign reply with plausible
metadata, omit the requested effect, deliver an old generation's receipt,
attempt stale cleanup, or bypass the proposed ownership mechanism. Check that
the neighbor actually acquired or attempted the contested resource at the gated
point. A gate acknowledgement alone does not prove that its system operation
succeeded. Checker rejections and live OS behavior establish different facts;
retain both where the claim needs both.

Demonstrate the selected design through one complete public sequence:
installation, verification, two ordinary specimens with fresh processes,
interference at the decisive boundaries, and removal/recovery. Preserve
independent effect observations and intended worker entitlements. Include a
subsequent unaffected specimen after finite interference to demonstrate useful
continuation. This is a minimal integration prototype, not conversion of every
suite or a change to default test membership.

Use the real external launchd/XPC path for claims about BYOXPC. If a candidate
uses an anonymous endpoint, private namespace or other route that changes what
is exercised, name that difference and demonstrate how external-runner coverage
would be preserved. Reject a design whose apparent reliability comes from
bypassing the behavior being tested, unless the recommendation explicitly
retains separate coverage of that behavior with a workable coexistence design.

Compare the candidate with the baseline using the four evaluation criteria.
For each interference class, state whether the design prevents it, observes and
waits for it, safely refuses it, or requires recovery. Specify what can be
bounded and how the bound is chosen; ordinary scheduling variation must not
become an arbitrary ordering assertion. Account for the complexity of new
ownership state and recovery as well as any guards removed. Recommend the
least machinery supported by these observations, even if that is a combination
of isolation, admission binding and lifecycle handoff.

## Execution, artifacts and handoff

Use the dispatcher and fresh managed output as required by
[test guidance](AGENTS.md). Register retained experiment cases with their real
equipment requirements and opt-in membership in [catalog.json](catalog.json);
put helpers with [BYOXPC fixtures](fixtures/byoxpc/README.md) and assertions
with the [owning suite](suites/runner_byoxpc/README.md). Document new controls
beside them and update the applicable coverage/opt-in entries. Exploratory
prototypes must be clearly identified and reproducible before their evidence
supports the recommendation.

Inspect selections with `tests/run.sh --list`. Existing checks to reuse where
their boundary is affected include `shell_helpers/byoxpc_setup`,
`runner_byoxpc/registry_recovery`, `runner_byoxpc/single_use`,
`runner_byoxpc/entitlement_readback`, `runner_byoxpc/entitlement_transfer`, and
shared specimen cases such as `runner_byoxpc/BBX-001`. Include
`runner_byoxpc/runner_auth_external` only for its actual relaxed-auth claim;
it cannot establish protection between allowed signed callers. Changes to
admission/transport require the coordinated runner/controller checks in
[tests/AGENTS.md](AGENTS.md), plus affected consumers such as
`witness_contract/extensions_byoxpc` and
`witness_contract/dossier_witness_byoxpc` when applicable.
Use offline controls for parsing/state logic and live controls for OS claims.

Before touching external runners, inspect `runner list` and `runner reconcile`
and record exact ownership. Never clean by label prefix. Keep staging and
durable records on warnings, unknown absence or retained cleanup. Follow the
[retention and checkout-lock contract](README.md#retention-ownership-and-execution-locking):
never unlink the lock or protected evidence. Independent checkout experiments
need separate worktrees and output; nested neighbor actors within one case must
not secretly acquire a checkout lock that serializes away their actions.
Follow the documented same-command unsandboxed diagnostic procedure for
automation-harness restrictions, preserving the original failure. That
equipment diagnosis is distinct from an automatic specimen-retry policy.

Write `tests/BYOXPC-BAD-NEIGHBOR-INVESTIGATION.md` with:

- The resource/lifetime map, neighbor capability model and causal findings,
  separating code facts, documentation guarantees, live observations and
  remaining limitations.
- The private-resource feasibility result, including acquisition, transfer,
  revocation, generation identity and cleanup. Explain which tempting options
  failed and why; give precise evidence links and reproducible commands.
- The recommended architecture and its behavior at each lifecycle boundary,
  including readiness, admission, finite contention, uncertain execution and
  recovery. State the ownership invariant and the observations that enforce it.
- A coverage matrix showing each interference schedule, checker control,
  expected result, observed result and retained run. Record OS/SDK/source/app
  applicability, cleanup status and any incomplete equipment-dependent claim.
- A concrete implementation handoff: affected files/interfaces, dependencies,
  contract/documentation implications, acceptance controls, and the checks
  that can be removed only because a demonstrated invariant replaces them.

The investigation is complete when another contributor can implement that
design without first deciding how isolation, ownership and request handoff
work. Do not call it complete merely because a prototype passes repeatedly.
If a necessary premise is contradicted, revise the recommendation and test its
replacement within this investigation. If required equipment is unavailable,
identify the exact unresolved claim and resolving experiment; do not present
that conditional design as established. Leave broad production changes and
full-suite migration to the subsequent implementation plan.
