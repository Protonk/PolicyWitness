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
Build output initially resides in `/private/tmp/pw-f2-stage1-build.log`; attach it
to the completed comparison run before removing the worktree. Signing/compiling
succeeded; no main app was replaced. Baseline and candidate live runs are serial.

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

## Controlled equipment candidate

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
replacement anchors. Compilation, signed installation and execution still need
the dispatcher. Command: `tests/run.sh --case runner_byoxpc/retirement_controls`
with a fresh F2 output directory and the unchanged current app.
