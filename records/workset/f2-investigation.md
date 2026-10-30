# F2 lifecycle investigation

Authorized after the stopped checkpoint `17e02e6a`. This investigation preserves
F1 and all production behavior. Its stopping boundary is a concrete explanation,
its limits and a repair proposal for discussion, not an unapproved retry repair
or acceptance of the previously failed BYOXPC workload.

## Fixed comparison and questions

The selected current app is unchanged v0.3.3 build 1000 from `fd90eee`, identity
f477a8488d3f96715e987f7014dcd0aa76ba53b70575118e20ef238b600d4094.
The accepted Stage 1 source `2de5b1c7` is checked out at
`/private/tmp/pw-f2-stage1` and built with the normal signed pipeline and the same
Developer ID. Its build 999 uses identity
6f777628d0b0f233f6e26f99222e8f78cd0920bb94b842b5bf2d0c4b2e29a9a7.
The build transcript and source comparison are attached to the completed
baseline observation run. Signing/compiling succeeded; no main app was replaced.
Baseline and candidate live runs were serial. The baseline worktree and app are
retained for the repair discussion; no build or test is active there.

Questions fixed before new observations:

1. Do ordinary empty-plan requests reproduce 4097 in the accepted Stage 1 app,
   current app, or both, under the same bounded schedule?
2. Which observed host generations and lifecycle boundaries surround failures?
   Process sampling cannot establish absence of an unsampled short-lived worker.
3. Can retirement overtake a refused request's reply, and can a lost reply also
   accompany completed work? Keep these mechanisms distinct from attribution of
   the original two failures.

## Equipment and limits

An opt-in observation case sends 48 unique ordinary allow-default empty-plan
requests, twelve each with predeclared 0/10/30/60 ms inter-call gaps, with no
resubmission of failed requests. It retains every outcome, actual timing,
process generations and unified logs. Passing means the bounded observation
completed and was accounted for, not that all requests succeeded or that F2
is resolved. Empty plans avoid creating a new effect-cleanup ambiguity.

The controlled follow-up uses copied production host sources, the shipped raw
client and real workers in separately owned signed services. Instrumentation
records admission, orchestration return, encoded reply, reply invocation and
scheduled exit. Its gates do not hold the admission lock. Retirement is held
inside the existing 50 ms closure. Compare delivered refusal, retirement before
refusal delivery, and host termination after completed work before its reply.
Append-only effects, request identity and observed kernel process generations
provide independent observations. Instrumentation is a declared intervention,
not proof of unchanged production timing or attribution of historical failures.

Production source, the inspected app, public retry rules and existing pass/fail
expectations remain unchanged. Current acquisition permits another execution
attempt only after an admitted pre-worker refusal and observed generation
retirement. A generic XPC error supplies neither fact. Any proposal to change
that boundary must address duplicate effects, unknown execution, client loss,
resource ownership and the original overall deadline together.

## First comparison observations

Harness source is `edf2c561`; runtime builds remain separately identified above.
All three runs completed without sleep, skipped/unrun cases, harness errors or
app changes. Session cleanup verified removal in each run. Raw evidence is
local/gitignored and explicitly pinned; no failed historical credit is replaced.

| Run | Run ID | Actual observation |
| --- | --- | --- |
| f2-current-observe-01 | 20261030T000733Z_74846c01 | Current build: all 48 ordinary requests returned ok; 47 required admitted refusal/observed-retirement acquisition. 60.843 s. |
| f2-stage1-observe-01 | 20261030T000928Z_32f8abcc | Accepted Stage 1: all 48 returned ok; 47 required the same acquisition path. 60.792 s. |
| f2-stage1-original-01 | 20261030T001113Z_ef6793ae | Original extensions_byoxpc workload passed once on Stage 1, including directory effects, phases, maximum replies, issuer refusal and verified cleanup. 68.995 s. |

The reduction did not reproduce F2. Nor does one passing original baseline run
establish that the failure was introduced by Stage 2. The ordinary comparison
controls show successful execution of the existing refusal/retirement path
under this schedule. Actual retirement is observed, not inferred from the
nominal 50 ms delay. In the current run, median actual inter-call gaps were
0.091, 12.492, 33.775 and 61.806 ms; maximum process sweep was 7.550 ms.
Short-lived unsampled processes remain outside those observations.

Primary source comparison found byte-identical service, listener, service entry,
client, acquisition, runner-client and runner-manager sources at Stage 1 and
current. Embedded provenance reports identical toolchain and signing, with
expected source/membership/identity and worktree/build-directory differences.
The source-hash comparison and baseline build transcript are attached under
f2-stage1-observe-01/investigation. The underlying source commits remain the
recoverable authority; this small comparison is not a complete dependency proof.

Commands used the main dispatcher and its fixed harness, with fresh output:
`tests/run.sh --case runner_byoxpc/retirement_observations` against the default
app and then `PW_APP_DIR=/private/tmp/pw-f2-stage1/dist/PolicyWitness.app`.
The baseline original workload used that same PW_APP_DIR and
`--case witness_contract/extensions_byoxpc`. No request was resubmitted by the
experiment, and no expected failure was changed into success.

## Controlled equipment

`review_public_extension` prepared the copied-source fixture; primary review
checked the insertion sites, process-generation observations, independent effect
assertions and cleanup ownership before integration. It adds no production API
or behavior. The case compiles the current explicit host membership with only
recorded instrumentation changes in service, entry and the post-spawn host
boundary. Its flags retain the production arm64/macOS 26 target and Onone/g
Swift settings. The existing generated identity is intentionally retained for
the unchanged real worker, so this is a disclosed instrumentation build rather
than normal source-identity or equivalence evidence.

The trace-only arrangement makes 24 public and 24 raw-client empty requests;
all outcomes remain data. Separate owned services exercise delivered refusal,
lost refusal and lost execution reply. The existing timer remains in place;
reply/exit gates are outside admission locks. Replies are encoded once and the
trace distinguishes encoding, invocation and return from client receipt.
Independent append effects and SDK process-generation observations accompany
the encoded-reply gates. The executed-reply-loss intervention is explicit
SIGKILL of the exact identified owned host, not a natural retirement claim.

Preparation checked Python/shell syntax, Swift parsing, C syntax and exact
replacement anchors. Compilation, signed installation and execution used the
dispatcher: `tests/run.sh --case runner_byoxpc/retirement_controls` with a fresh
F2 output directory and the unchanged current app.

The first controlled candidate `aa45aa48` failed compilation before installing
any service: Swift could not select the overloaded Int initializer supplied to
Optional.map in the trace's client-PID field. `f2-controls-01` preserves the
compiler diagnostic; no runtime control was credited. The fixture-only repair
uses an explicit conversion closure. Parsing alone had not resolved this type.

## Controlled observations

Corrected harness source `7d3b57a5` completed `f2-controls-02`, run
`20261030T001949Z_1c855119`, in 65.064 s. All four arrangements completed and
verified cleanup. There was no system sleep, skipped/unrun case, harness error
or inspected-app change. The raw evidence is local/gitignored and pinned in
tests/RETAINED.json. Its case artifacts are under
tests/out/runs/f2-controls-02/suites/runner_byoxpc/retirement_controls/artifacts.

| Arrangement | Client observation | Independent execution observation |
| --- | --- | --- |
| Trace only, no gates | Public: 23 ok, 1 xpc_error; raw: 8 ok, 14 already_ran, 2 xpc_error. All three transport errors report NSCocoaErrorDomain 4097. | The failed public request reached a used host and failed admission before the prior owner's exit. The two raw errors have no request-entry trace and remain unlocalized. |
| Delivered refusal | already_ran | Prior owner appended exactly one byte and its worker was reaped. Refused request did not enter orchestration or create its separate effect. |
| Lost refusal | xpc_error, 4097 | Same refusal/effect separation; releasing the owner's exit while the refusal reply was held lost the refusal. |
| Lost execution reply | xpc_error, 4097 | The request appended exactly one byte and its worker was reaped before the exact identified host was killed with its encoded reply held. |

The ungated public failure is `f2-observe-public-07`, client PID 37512, request
SHA-256 `9940764d3f5fddfd50bb78bfffae1b0819dc10a7333035e4c9a4d8895bb78c17`
(175 bytes), on host generation `37509@1793319609.745637`. The previous owner
was `f2-observe-public-06`. The host's ordered trace records:

| Sequence | Boundary |
| --- | --- |
| 4–7 | Owner claimed admission, entered orchestration, spawned worker 37510 and returned with that worker reaped. |
| 8–12 | Owner reply encoded, invoked and returned; host exit scheduled with the existing 50 ms delay. |
| 13 | New connection accepted for client 37512. |
| 14 | Owner's exit timer fired. |
| 15–16 | Request 07 entered the service and the real admission claim returned false. |
| 17 | Owner reached exit invocation. |

Request 07 has no reply-encoding or orchestration event. Its client capture
records complete local delivery, no acquisition receipt, and 4097. A later
kernel observation establishes this host generation's absence. Source ordering,
the positive refusal event and the exit establish a concrete lost-refusal
mechanism for this new instrumented execution. Missing events alone would not
establish nonexecution. The two raw-client errors remain unassigned.

Trace IO and its lock perturb scheduling even without gates. The roughly
140 ms trace interval between exit scheduling and timer firing includes this
instrumentation; it does not measure the uninstrumented timer's latency. This
run does not attribute the two original failures or establish when the mechanism
was introduced. Matching source and error codes do not remove that limitation.
The executed-reply-loss control uses deliberate SIGKILL, not natural retirement.

Primary review and independent `review_public_extension` review agreed on the
request/host association, actual failed admission, effect distinction and limits.
The passing case means its investigative arrangements completed, not production
reliability acceptance. Required extensions_byoxpc verification remains unmet.

## Repair direction

The user accepted the proposed direction after the findings were reported:
separate effect-free host acquisition from specimen submission. This is a
design direction, not an implemented or verified protocol.

The current acquisition rule correctly requires an admitted already_ran reply,
no worker evidence and observed retirement of the identified host generation.
A client-generated xpc_error supplies none of those facts. The two loss controls
demonstrate that retrying 4097 can duplicate a completed effect. Waiting for host
exit after that error also cannot establish that the request did not execute.

The proposed protocol should enforce these boundaries:

1. Atomically reserve a fresh host, binding the grant to the authenticated
   connection and a single-use reservation identity. A reserved host cannot
   grant another client the same execution slot, including a legacy caller.
2. Send no specimen for execution until the client receives that grant. Keep
   acquisition and submission on the same connection. Transport loss during
   acquisition may permit bounded reconnection because no execution was sent.
3. Once the execution method is invoked, conservatively mark it submitted.
   Lost replies remain unknown execution and must never trigger automatic replay.
   A received grant is not an execution receipt or a guarantee of later delivery.
4. Bound acquisition by the original overall deadline and record its attempts.
   Handle lost grants, abandoned reservations and client disconnects with owned,
   bounded retirement; do not leave reserved hosts stranded or reuse a host
   after executing a specimen. Keep fresh workers and one specimen per host.
5. Design protocol capability/version admission and old/new client-service
   compatibility explicitly. Legacy fallback must retain today's conservative
   error behavior; it cannot silently convert transport failure into replay.

The concrete design must account for changes to the XPC protocol, host admission
state, helper/controller acquisition observations, versioned readers, fixtures
and public documentation. Reservation expiry racing submission needs one atomic
decision. The exact API and wire/version changes remain design work. Longer
delays would change timing without establishing delivery. Serializing entered
refusal handlers with exit would address only part of the boundary: messages
not yet dispatched can still be lost, and reply closure return is not receipt.

Acceptance should include lost grant/refusal replies before submission,
simultaneous reservations, abandonment, wrong-connection and reused/stale grants,
expiry/submission races, retirement during acquisition, overall timeout and
old/new compatibility. Preserve the completed-effect/lost-reply control and
establish exactly one effect with no replay after submission. Run the original
BYOXPC workload on a normal signed repaired build with its required integrated
checks; the instrumented observations cannot replace that acceptance.

## Verification and checkpoint

- `f2-controls-01`, `20261030T001924Z_3e1b5c4c`, source `aa45aa48`: preserved
  compile failure before installation, no runtime credit, unchanged app.
- `f2-controls-02`, `20261030T001949Z_1c855119`, source `7d3b57a5`: the four
  completed arrangements above, unchanged inspected build 1000.
- `f2-equipment-checks-01`, `20261030T002304Z_ad94e234`, source `7d3b57a5`:
  runner_source_manifests_agree and generator_contract both pass, no sleep,
  skips, unrun cases or harness errors. This checks the equipment's source,
  registry and documentation integration; it is not a production repair test.

All six F2 runs are pinned, including the compilation failure. Each new live
service has verified removal and the controlled arrangements' owned resources
were removed after process/effect evidence was copied. Final default registry
and reconcile observations are empty, with no pending cleanup or inspection
errors; copies are attached under f2-controls-02/investigation. Baseline source
and app remain at /private/tmp/pw-f2-stage1 for follow-up. The earlier retained
directory /private/tmp/pw-extension-directory-uge3532e remains untouched: these
new traces cannot establish its unwitnessed worker's exit.
Retention reconciliation verified all 24 local direct-run identities and
inventory paths. The supported prune preview found no eligible deletions and
no active checkout owner; existing release evidence and rotation were untouched.

The bounded investigation is complete. No production repair, F1 disposition,
Swift Stage 2 acceptance or plan retirement occurred. Next work is the concrete
reservation protocol and compatibility design for the agreed repair direction.
