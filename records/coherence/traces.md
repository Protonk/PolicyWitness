# Trace findings and verification sequence

Codex, 2026-10-30. The associated plan fixes the initial sample. This file records
new attributable findings; earlier acceptance records remain historical and unchanged.

Initial state: isolated branch `review/pytest-coherence` at review baseline
`809ef178`; no execution observations or repairs yet. The accepted checkout is
`77eb9875` with its three pre-existing untracked review paths. All older worktrees,
pins and protected resources remain untouched.

## Localized finding: portable evidence account

Direct trace 1 found a stale consumer account: `docs/SIGNING.md` says only
portable schema 2 is supported, and `release_runs.battery_source` uses that same
obsolete description in three diagnostics. The completed candidate emits schema
3 with a producer contract; schema 2 remains historical transport evidence, with
positive producer identification at the release boundary. `tests/README.md`
already describes both correctly. The immediate sibling scan found no other
current guide making the schema-2-only claim. The preflight README's schema-2
*provenance record* describes a different object and remains correct.

Repair the guide and diagnostics, without changing admission or historical
allowlist policy. Expected discrimination: schema 2 and source-bound schema 3
positive controls still verify; unsupported format, missing family declaration,
missing terminal ownership and false historical downgrade still refuse. Existing
release controls and pytest portable controls cover those behaviors; generator
and source checks cover the edited guide. No production/oracle change is needed.

## 1. Execution becomes an accepted result

Directly inspected `tests/catalog.json`, `test_cli.catalog/select/main`,
`pytest_engine.Journal`, `pytest_family.Collector/account/display`,
`suite_run.account/execute`, `execution_contract`, `release_accept`,
`release_archive.battery_record` and `release_runs.verify_bundle/verify_release`.
F has one public whole-family route. Pytest collects stable `pw_id` variants once
in the same process later made eligible; discovery has no native fixture work.
Equipment/app checks and the actual inherited checkout descriptor precede fixture
execution. The adapter reconciles the collected identities; it does not choose
or order individual items. Other families retain their legacy invocations.

The phase journal retains setup/call/teardown, item starts/finishes and the session
terminal. A valid prefix survives truncation. Parent legacy `unrun` is accompanied
by explicit execution/accounting states: engine loss is `started/incomplete`,
missing equipment is `not_started/unavailable`. The ordinary display exposes both.
Legacy report counts explicitly exclude F; parent outcome counts include it.

Acceptance has an independently captured producer contract. Archive construction
also checks the current source contract. Portable verification derives required
family/selection/ownership roles from the external contract, not from optional
result hints. The release boundary binds historical producer recognition to the
ZIP's source stamp/provenance. Transport hashes alone do not establish semantic
completeness: deletion controls repair hashes and still must refuse. A standalone
schema-2 bundle inventory check is only historical transport verification; it is
not the release-level historical identity decision.

Fresh `coherence-01` exercises F together with ten legacy parents, as well as a
nested F/legacy-sentinel selection. All nine real variants pass; the 58-attempt
native sequence remains one observation. Normal discovery leaves the fixture
checkout unchanged. Missing declarations/references/ownership receipts and an
attempt to remove outer schema/contract fields cannot become successful legacy
evidence. All three public release controls pass. The localized wording repair
above is the only source change this trace requires.

**Emitted-report walk:** the `wrong-rejection` fixture names
`collection_from_final_reap`, a failed call phase and its artifact directory.
`expectation.json` records submitted `slot->exec_group_rc = 42;` and expected
`slot->exec_leader_exit_observed == leader`. `observation.json` and native stderr
instead show the group-rc/group-errno assertion, return -6. The body therefore
fails “outside its designated oracle”; a native failure alone is not credit.
Sources and command receipts remain beside the observation. The baseline-failure
display names the shared native ledger mismatch before the eight setup-blocked
variants; their bodies did not run. Both session-finalizer controls preserve nine
passing bodies while displaying shared input-integrity or cleanup failure and
last-item teardown attachment. Engine loss preserves a completed item, an active
item and unstarted queued items, but remains `started/incomplete`. These actual
paths and states are recorded in `walkthrough.json`; no reconstruction from raw
records is needed to find the scope of failure.

## 2. Resources become safe to release

Directly inspected `pytest_resources.reserve/Command/settled/disposition/recover`,
`pytest_command_owner.main`, checkout lock inheritance/group observation, retention
replacement/prune guards and release cleanup. Reservation registers an obligation
before launch authority; the owner gets the real descriptor. Launch/start records
are distinct from completion. The owner's direct `poll()` result does not settle
its process group. Output flushing, observed group absence and endpoint removal
(revoking launch authority) precede the matching settlement. `closed` additionally
requires isolated cleanup. A state label, available lock or historical PID cannot
supply this evidence.

Selected consequential window: the command returns while its child survives,
then the owner dies before group settlement. `pytest_windows` obtains independent
peer identities and registers kernel exit observers before the intervention.
Fresh `window-after-return` retains the inherited lock while the child is live,
refuses recovery and prevents the queued legacy sentinel from starting. The
external experiment then observes all actors' exits; this does not fabricate an
owner settlement, so that fixture checkout remains protected. This is intentionally
ambiguous experimental state, not an unresolved actual test command.

The positive neighbor uses a matching settled receipt but no closure publication.
It permits independent execution while protecting the particular output; public
recovery closes it, is idempotent, and only then can supported pruning dispose of
that unpinned fixture output. Active-session recovery refuses. Live-owner recovery
requires peer PID, token, nonce, actual descriptor inode and observed owner exit.
Offline recovery can revoke a reservation with no launch authorization, but cannot
resolve an authorized launch merely because no command PID was published. The
before-owner, before-release and before-start-publication siblings exercise these
same transitions. Build admission, per-invocation admission, pruning and release
cleanup consume the same registry disposition. No contract change is needed.

The fresh actual family has 16 closed command records. Eight deliberately
unresolved nested fixture records remain in the pinned run and recovery index.
The prior candidate's 176 closed actual records and 95 unresolved nested fixture
records remain under its original index. Earlier unknown-worker and prototype
resources were neither signalled nor released.

## 3. F2 observations become conclusions

Directly inspected `PWRunnerClientSession` acquisition/submission/terminal paths,
`PWRunnerTransport` capture fields, Rust `runner_client.validate_capture` and
`parse_runner_client_output`, the run-flow admission/fallback path, independent
`runner_client_capture.validate_client/host_reply`, and the authored controls.
Reservation retries remain effect-free and bounded by the original deadline.
The session marks invocation before calling the submission proxy. A subsequent
error, timeout, refusal or late callback does not reconnect or replay. Rust starts
with `submission=unknown` and projects invocation only after complete capture
admission. Exact retained host bytes, with a separate completeness check, are the
only source of a host reply. The independent reader rejects invented submission,
host result or host-byte diagnostics from missing/rejected capture. A separately
allowed fallback policy compilation reports its own compiler result; it does not
supply the missing worker observation.

Fresh production-session controls pass 10/10, including positive invocation before
proxy failure and no replay after terminal submission events. The independent
blackbox reader controls accept constructed known states and reject falsely
admitted/missing/truncated/contradictory observations. Native witness reliance is
explicit: `f2-controls-02`, source `7d3b57a5`, remains the historical instrumented
observation. Read its `lost_refusal` and `lost_execution_reply` control summaries,
final effects and the retired investigation at `67fff425`. Both produced 4097;
the former has only the prior owner's append, while the latter has the submitted
request's completed append before reply loss. Request/host trace association and
worker reap observations—not the error code or a bare missing file—justify those
different conclusions. Original F2 failures remain unattributed. No new native
XPC timing experiment or production repair is inferred from this pass.

## 4. Extracted definitions reach consumers

Directly inspected the Stage-2 design recovered at
`67fff425:records/workset/swift-refactor.md`, `PWRunnerAttemptEvidence.swift`,
`CWorker` publication gating, `CWorkerStepResults` construction, `PWRunnerReply`
codecs/integrity, Meson's explicit shared contract membership and the independent
`native_sources.SHARED_CONTRACT_SOURCES` list. `PWRunnerAttemptEvidence` compiles
in both client and host; host processing remains outside the client membership.
The driver publishes optional exec facts only from completed C slots; the step
builder carries the value and any decode problem into ordinary reply integrity.
Absence remains unavailable, not invented `not_requested` cleanup. Present invalid
facts fail typed decode or degrade production reporting and remove comparison.
The pre-existing encode/decode asymmetry is preserved rather than “normalized.”

Immediate consumers inspected include Rust `disposition.exec_observation_problem`,
independent Python `consumer.validate_exec_observation`, the authored contract
fixture and Swift `ExecObservationTests`. Cleanup request return values do not
prove group absence; reap concerns the owned leader, separate from the pre-cleanup
collection snapshot. The mutation equipment targets the extracted decoder file
and the still-owning CWorker publication gate, with source snapshots for each.
Fresh baseline passes 3/3; publication bypass and invented absent metadata each
fail their designated unchanged assertions. Shared membership, source mutations,
architecture citations and generator controls also pass. The generated architecture
points to the current orchestrator/step-result owners; runner documentation names
the extracted wire-family owner. No stale source route or reader adaptation was
found in this trace. No native source, ABI, oracle or identity changed here.

## 5. F1 guard and independent omissions

Directly inspected `check.RUNNER_NATIVE`, `host_tokens`,
`host_invariance_problems/check_host_invariance`, `check_planner`'s independent
required-symbol examples, per-symbol omissions and file mutations, and the
source-drift README's scope. Discovery covers host Swift/C/header material under
`runner/Sources`; the production C worker/validator/issuer remain outside that
scope. Literal symbol bindings, direct uses and simple named constants are checked;
computed names and complete language analysis remain explicitly excluded.

Fresh source controls accept 14 benign snippets, reject 102 prohibited examples,
and detect each of the 11 omissions independently before complete restoration.
Swift-host/C-shim extension mutations exercise discovery as well as classification.
The original F1 red observation and correction remain distinct historical records;
this passing run does not rewrite the original missing rejections. No additional
repair or promise expansion is needed.

## Documentary decisions, verification and stopping point

Recovered D2 acceptance at `67fff425:records/checks-before-check/acceptance.md`
tracks C1–C5, the later D35 citation correction, bounded F1 repair and retirement.
B1's new registry machinery was declined; source checks remain mechanical evidence
with semantic applicability review. The counterfactual, demonstration and maintenance
decision keep feasibility, maintenance value and replacement worth separate. The
later family adoption follows the user's diagnostic/organization goals; it is not
proof of general savings or a retroactive migration recommendation. No historical
assessment required rewriting.

`coherence-01` at clean runtime/guide source `6b35e27a` passes 11/11 parents,
including nine F variants, with no skip, unrun parent, harness error or app change.
The 10 legacy reports and 11 parent passes deliberately differ. All expected
negative observations are inside the pinned control run. No new consequential
failed observation occurred. The review-index writer initially used `normal`
instead of the actual `integrated-normal` fixture directory; correcting that
bookkeeping path changed no source under test, observation or expectation.

Existing broader evidence remains bounded: inherited acceptance is 229 composed
credits, not one green run; the C replay preserves its historical exposed inputs;
the adoption's 202-case battery and 16 build mutations precede its final narrow
corrections. Their source limits and subsequent targeted verification remain in
the frozen assessment/index. This pass does not relabel them as fresh runs.

The four required traces and one justified extra trace are complete. Expansion
stopped at the release-schema wording mechanism and its consumers. No consequential
choice requires the user. Recommend handing the candidate to the separate reviewer
with the prior one-family acceptance recommendation intact. This is a bounded
coherence sample, not a whole-tree audit, production reliability proof or authority
to merge, expand pytest adoption or settle the original F2 attribution.
