# Plan: An Experimental Atlas of PolicyWitness

## Purpose and scope

Create `docs/ATLAS.md`, provisionally titled **An Experimental Atlas of
PolicyWitness**. Its reader learns about the instrument by asking questions of
experiments, inspecting their arrangements and observations, and considering
competing explanations. The primary reader is the project's investigator;
technically competent outsiders should also be able to use it without accepting
the project's account first. Contributor procedures belong in existing guides.

The atlas should make informed disagreement inexpensive and leave evidence useful
for questions the writer did not anticipate. Implement that through direct access
to specimens and raw observations, optional routes, visible uncertainty, and
explicit distinctions between observations and interpretations. Do not substitute
an introductory declaration of those values for those facilities.

This is a plan for a document and its inspectable supporting evidence. It does not
authorize repairing the application, changing tests to obtain a preferred result,
or implementing the pending worker-document project. It is not a coverage report,
verification certificate, testing tutorial, architecture tour, contributor
procedure, or narrative aimed at persuading an imagined evaluator. The document
should follow relationships among PW, the operating system, fixtures, observers,
and readers wherever the question requires; it need not treat a single process,
application, or author as the natural boundary of an experiment.

The eventual writer should retain room to discover a better question, revise an
interpretation, or expose an unresolved result. Keep both this plan and the atlas
concerned with the practice and the local evidence.

## Grounding and evidence status

This plan was prepared on 2026-10-17 against committed source
`6fd44fb15397678d29f0f96bfee2b1abbe4bbbb6`, inspected in an isolated archive of
that commit. Other working-tree changes were excluded. The preparation read source,
documentation, fixtures, and assertions, and successfully inspected the public
catalog with `tests/run.sh --all --list`. No build, live experiment, mutation
control, or test battery was executed. Statements below about what a case requires
describe its inspected assertions, not a newly observed outcome.

Follow [Planning a change](../../CONTRIBUTING.md#planning-a-change),
[test working guidance](../../tests/AGENTS.md), and the
[runner rules](../../runner/AGENTS.md). This plan is self-contained; its execution
does not depend on the conversation or on a separate prompt file.

The documentation boundaries inspected were:

| Existing account | What it continues to own | What the atlas adds |
| --- | --- | --- |
| [Architecture](../../docs/ARCHITECTURE.md) | Processes, orchestration in time, channels, boundaries, and the document graph. | Routes beginning with an observable puzzle; implementation becomes an explanation to examine after the evidence. |
| [Build](../../docs/BUILD.md) and [signing](../../docs/SIGNING.md) | Toolchains, cache assumptions, signatures, provenance, release and artifact handling. | The particular equipment and provenance needed to assess a displayed experiment. |
| Worker document plan (`docs/WORKER-INST-DOC-PLAN.md` at the inspected commit) | A proposed assessment of resources and authority carried across application. `docs/WORKER.md` does not exist at the inspected commit. | Experimental encounters with publication, reporting resources, and changed external state; no capability inventory or adjudication register. |
| [Harness reference](../../tests/README.md), [fixture catalog](../../tests/fixtures/README.md), suite READMEs, and [coverage](../../tests/COVERAGE.md) | Commands, equipment, suite responsibilities, detailed assertions, and enumerated outcomes. | A small selection connected by questions, with routes into those references rather than copied catalogs. |
| [Wire contract](../../docs/CONTRACT.md), [failure evidence contract](../../tests/FAILURE-PROPAGATION-CONTRACT.md), [user guide](../../docs/PolicyWitness.md), and [limits](../../docs/LIMITS.md) | Accepted inputs, field meanings, claim ownership, capacities, and reading rules. | Worked inspection of the observations on which a particular interpretation rests. The atlas introduces no normative field vocabulary. |

## Proposed organization and navigation

Use one authored Markdown document, with stable question headings and a compact
entry table. A reader should be able to choose a question, reach the relevant raw
material, and understand the experimental arrangement without reading a preceding
chapter. A suggested starting path is useful, but should not be a prerequisite.

Start with the puzzle of an effect PW cannot report. Then present this map:

| Entry question | Initial experiment | Useful departure |
| --- | --- | --- |
| Can something happen without a completed result? | Death between a native return and slot publication. | Compare an in-flight operation with a completed observation followed by timeout. |
| What did the prediction actually ask about? | Swap query targets while holding attempts and policy fixed. | Inspect a permission failure whose cause PW cannot assign. |
| Does “before” mean the world stayed the same? | Hold collection open, observe effects, and change a target between observations. | Remove the barrier deliberately and see whether the observer notices. |
| What survives a failed observer? | Preserve partial validator output and independent attempt effects. | Distinguish a missing query, missing verdict, and missing attempt. |
| How can a denied worker still tell us anything? | Compare the public deny-default run with the direct worker harness. | Ask which prepared resources make reporting possible and what that preparation changes. |

These five routes are a bounded initial selection, not an ontology of PW. They
cover distinct ways an instrument can know less than an investigator, ask a
different question, observe a changing world, lose one channel, or depend on
prepared apparatus. The barrier mutation belongs beside the ordering route:
separating it into a general testing chapter would obscure the question it tests.

Each route needs a short field note with the following information. Use an order
that suits the question; do not require a repetitive form in the published prose.

- The phenomenon and the alternatives the arrangement can distinguish.
- The exact intervention, actors, resources, and conditions that can affect it.
- Separate access to PW's report, external observations, and the checker's rules.
- A bounded interpretation, an observation that would challenge it, and what
  remains unknown. A passing checker is evidence about its assertions.
- Links to the specimen or specimen builder, assertions, raw files, relevant
  implementation, and the owning contract. Give artifact-relative paths and
  JSON selectors or step IDs so a reader can find the cited observation.
- The exact public case selector, equipment, and a feasible neighboring question
  or variation. Mark unexecuted variations as proposals.

Include a compact evidence index at the end, keyed by question and canonical case
ID. It should reach raw material directly, without making a reader follow the
writer's conclusions. Link laterally among routes: missing publications to lost
validator output, differing query scope to changing state, and reporting survival
back to incomplete reporting. Avoid an exhaustive dependency graph or a prescribed
sequence of lessons.

## Initial routes and their evidence

All paths below are repository-relative unless a linked path says otherwise.
`<run>` means a fresh managed directory under `tests/out/runs/`.
The artifact paths describe outputs the tests produce; they are not claims those
outputs are already present in a clean checkout.

### 1. An effect outside the report

**Primary case:** `witness_contract/worker_killed_before_slot_publication`.
The [case wrapper](../../tests/suites/witness_contract/worker_killed_before_slot_publication.sh)
and [checker](../../tests/suites/witness_contract/check_killed_before_publication.py)
provide the specimen, capture, independent observation, and assertions.

The checker arranges a completed read, creation of a fresh file, and a final read.
The existing override selects the create slot for SIGKILL after its native return
but before publication. In
[pw_probe_runner.c](../../controller/tools/pw_probe_runner/pw_probe_runner.c),
`run_attempt` places that seam before the release store to `completed`.
[CWorkerOrchestrator.swift](../../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift),
through `buildAttemptResult`, withholds fields from incomplete slots.

The external witness is the checker's filesystem observation, taken before JSON
decoding: it requires an initially absent target to become a regular, empty file
with the expected mode. PW's separate account must retain a completed prefix, a started slot
without a result, and an unreached suffix. Its host observations include the
reaped signal and no host termination request; cause remains unknown. The
override echo records setup, not proof that the boundary was reached.

Inspect
`<run>/suites/witness_contract/worker_killed_before_slot_publication/artifacts/killed_before_publication/`:
`specimen.json`, `run.json`, `pw.stderr`, `capture.json`, `observations.json`,
`witnesses.json`, `diagnostics.json`, `oracle_findings.json`, `staging.json`, and
`cleanup.json`. The checker uses
[consumer.py](../../tests/lib/consumer.py),
[lifecycle_oracle.py](../../tests/lib/lifecycle_oracle.py), and
[lifecycle_adapter.py](../../tests/lib/lifecycle_adapter.py). These are additional
readers of the report, not additional witnesses of the file creation.

The interpretation would fail if the target already existed, the independent
effect were absent, the intended publication boundary were not evidenced, or PW
reported unpublished return fields as completed. The file observation and
controlled arrangement support the effect; they are not a general trace of every
worker syscall or a cause attribution available in ordinary PW output.

Use `witness_contract/worker_attempt_in_flight_at_deadline` as the first neighbor:
an operation blocked on a FIFO and one that returned but was never published can
both lack a completed result. The committed
[current-format capture](../../tests/fixtures/disposition/response23/a1_expected.json)
and [specimen](../../tests/fixtures/disposition/response23/a1_specimen.json)
support inspection of that neighbor now. A further departure is
`witness_contract/worker_post_apply_hang_seam`, where completed file effects
survive failed run completion. Removing the kill override from the primary
specimen is a proposed variation, not an experiment performed during planning.

**Equipment:** the catalog requires `app` and `clang`; the live case also depends
on macOS XPC and Python. Preserve staging until the fixture's exit-witness cleanup
rule permits removal. Do not replace that rule with “the CLI returned.”

### 2. The prediction's target

**Primary case:**
`witness_contract/prediction_target_is_independent_of_attempt_target`, implemented
by [check_prediction_targets.py](../../tests/suites/witness_contract/check_prediction_targets.py).
It uses the real validator without overrides. Two seeded files receive the same
attempts under the same policy in both runs. Only the query targets swap; seed
bytes are restored first, and step IDs remain fixed.

The checker reads the files before decoding either envelope. The allowed write
must leave changed, nonempty bytes; the denied target must retain its seed.
Separately, native predictions must follow the submitted query targets. The
comparison records retain the submitted-target relation without judging
prediction/enforcement agreement.

Inspect the case's `artifacts/matching/` and `artifacts/swapped/`: each has
`specimen.json`, `expectations.json`, `run.json`, `pw.stderr`, `capture.json`,
`file0.before`, `file0.after`, `file1.before`, `file1.after`, and
`diagnostics.json`. Expectations are test-authored literals. The shared
[blackbox checker](../../tests/lib/blackbox.py) validates shape and supplied
expectations; it does not choose those expectations from the policy or PW's
classification.

Trace query planning and joining in
[CWorkerOrchestrator.swift](../../runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
and native query handling in
[sb_api_validator.c](../../controller/tools/sb_api_validator/sb_api_validator.c).
Use the contract's
[claim/evidence review](../../tests/FAILURE-PROPAGATION-CONTRACT.md#claimevidence-review)
for the limits of pairing. A query accidentally redirected to the attempt target
would be challenged by this experiment even if the report echoed the requested
filter correctly. Failure to restore seeds would compromise the comparison.
Different submitted strings do not establish different runtime objects.

The [exec DAC suite](../../tests/suites/runner_exec_dac/README.md) is an optional
departure: direct execution controls can establish more about an EACCES result
than an ordinary PW report can. Do not expand its policy matrix into this route.
A symlink variation asking whether different spellings reach the same object is
an unexecuted question, not a promised result.

**Equipment:** `app` and `clang` in the catalog, live XPC and Python; log capture
is disabled in the case. No external runner installation is needed.

### 3. Ordering in a changing world

**Core cases:** `witness_contract/attempt_effects_wait_for_collection`,
`witness_contract/query_interval_is_not_a_snapshot`, and
`witness_contract/external_mutation_between_query_and_attempt`.
All use [check_ordering.py](../../tests/suites/witness_contract/check_ordering.py).

Read the [native bridge contract](../../tests/fixtures/validator/README.md) before
interpreting a gate receipt. The bridge makes native sandbox queries and
separates query acknowledgement, stdout emission, and collection closure.
It imports no PW parser, worker ABI, or classifier. Its executable override
changes the arrangement; it is controlled equipment, not the shipped validator.
[validator_bridge/protocol_controls](../../tests/suites/validator_bridge/README.md)
checks that equipment independently, including a separate native-call oracle.

The held-effects case observes unchanged file bytes and no helper connection
while collection remains open, then unlink and exec effects after closure.
Kernel peer identity, process ancestry, and exit observations relate the helper,
worker, and host. The helper equipment has its own
[exec_fixture/controls](../../tests/suites/exec_fixture/README.md). The other two
cases remove a target after an acknowledged native query, either before a second
query or before the attempt. The first allow receipt and the later ENOENT
observation remain separate facts. No particular verdict is required for a query
against the already missing target.

Inspect each case's `artifacts/`: `gate-events.json`, `effects.json` for held
effects or `external-state.json` for external mutation, and the `run/` capture's
`specimen.json`, `run.json`, `pw.stderr`, and `capture.json`. Retain bridge and
helper provenance alongside those files. Relate receipts to
`phases[].ordering` and `steps[].comparison.order`, then consult
[the ordering contract](../../tests/FAILURE-PROPAGATION-CONTRACT.md#ordering-evidence-states).
Production anchors are `wait_for_proceed` in the C worker, `runCWorker` in
[CWorker.swift](../../runner/Sources/PWRunnerCore/CWorker.swift), and the
phase callback, query planner, and ordering assembly in CWorkerOrchestrator.swift.

Early effects while collection is acknowledged open would challenge the barrier
interpretation. Effects only after closure would still not establish a frozen
external world or absence of all possible syscalls while held. The fixture's
knowledge that it removed the target must not become PW's attribution of the
ENOENT. Earlier actions within a phase and later phase collections are further
reasons not to read `query_first` as an immediate per-step snapshot; link to
`witness_contract/phases` for that departure.

**Detection control:** `witness_contract/order_barrier_mutations` belongs here.
[mutations.py](../../tests/suites/witness_contract/opt_in/mutations.py) builds an
unmodified baseline, a worker wait bypass, and an early host release. It calls
the same `held_effects` observer for signed candidate apps and requires specific
early unlink and exec evidence. Component controls separately check C quiescence
and the Swift collection hook. A build refusal, missing equipment, or arbitrary
assertion failure is not a substitute for the required early-effect observations.

Inspect `mutations.json`, baseline and mutant component logs, patched sources,
`hashes.json`, artifact/signature inspection, each candidate's `cli/effects.json`
and `cli/gate-events.json`, and `cli/run/` captures. The controlled mutants retain
the baseline generated identity deliberately to reach the semantic observer past
the identity guard. State that intervention; an ordinary build would refuse stale
identity. Mutation detection is bounded evidence of observer sensitivity to these
faults, not independence of the whole toolchain or proof that all ordering errors
are detectable.

**Equipment:** the ordinary cases require `app` and `clang`, live XPC, Python,
local sockets, and process observation. The opt-in also requires Swift, Meson,
and a matching Developer ID identity. Follow the
[opt-in entry](../../tests/OPT_IN_TESTS.md#order-barrier-mutation-controls);
only its disposable copies may be patched or signed. Preserve its cleanup and
source-app inventory checks. A different external change, such as replacing a
target instead of removing it, remains an unexecuted variation.

### 4. A failed observer and surviving observations

**Primary pair:**
`runner_validator_failure/validator_unavailable_reports_degraded` and
`runner_validator_failure/validator_decode_failure_reports_degraded`.
Use their canonical IDs even though the witness suite also exposes entrypoints.
The [suite reference](../../tests/suites/runner_validator_failure/README.md),
[checker](../../tests/suites/runner_validator_failure/check.py), and
[case wrapper](../../tests/suites/runner_validator_failure/case.sh) own the details.

The checked-in [validator fixture](../../tests/fixtures/validator/validator.py)
receives all queries, emits two replies in reverse step order, then reaches EOF
or emits malformed JSON. These are supplied verdicts, not native sandbox
predictions. The real worker still attempts an allowed write, a denied write,
and a denied access check. Independent file reads precede JSON decoding.
Unchanged bytes at the access target do not independently establish access
failure; that native result comes from the worker's published observation.

Inspect each case's artifact root: `specimen.json`, `run.json`, `pw.stderr`,
`capture.json`, copied `validator.py` and `validator.case.json`,
`validator.received.json`, `validator.emitted.ndjson`, `before_*.bin`,
`after_*.bin`, and `assertions.log`. The received transcript distinguishes an
unanswered query from a query omitted upstream. Reversed replies test association
by identity. The report must preserve accepted verdicts, all completed attempt
observations, and the explicit missing prediction despite failed run status.

Read receiver behavior in
[ValidatorClient.swift](../../runner/Sources/PWRunnerCore/ValidatorClient.swift)
and channel assembly in CWorkerOrchestrator.swift. Challenge the interpretation
with dropped accepted records, swapped step association, hidden missing verdicts,
or missing effects. Fixture setup failure is not validator-degradation evidence.
Agreement between a supplied verdict and an attempt cannot establish native
prediction behavior. `runner_validator_failure/transcript_controls` establishes
the fixture's output by direct execution outside PW. It shares `assert_transcript`
with the CLI checker; it is not an independently implemented transcript oracle.

Existing departures include `runner_validator_failure/validator_killed_mid_stream`
and `witness_contract/validator_spawn_failed_reports_degraded`; neither needs to
become another full field note. Delaying a valid reply past collection closure
is a question for further investigation, not a run performed for this plan.

**Equipment:** the primary cases require an app and live XPC; Python runs the
fixture and assertions. Transcript controls need no app. No new fake validator
or production override should be introduced for the atlas.

### 5. Reporting under denial

**Primary comparison:** `runner_use_c_worker/bare_deny_default` through the public
CLI, and `runner_c_worker_harness/bare_deny_default` through the direct ABI harness.
Use `runner_c_worker_harness/happy_default_allow` as a neighboring control and
`runner_c_worker_harness/max_slots_deny_default` to inspect publication across the
shared region. Assertion owners are the
[public case script](../../tests/suites/runner_use_c_worker/run.sh),
[harness case script](../../tests/suites/runner_c_worker_harness/run.sh), and
[harness.c](../../tests/suites/runner_c_worker_harness/harness.c).

The public case requires a coherent envelope with a deny prediction beside a
permission-shaped attempt failure. The direct harness observes worker application
and publication flags and reaps the child without needing its kill fallback.
It shares the worker ABI and reads worker-published attempt fields: it is not
an independent witness of every reported syscall or of a denial's cause. Its
process wait is a distinct observation. The full-region case fills no-op slots;
it tests publication across the region, not successful performance of every
probe kind under denial.

Inspect the CLI case's `specimen.json`, `run.json`, and `assert.log`, and each
direct case's `result.json`, `harness.stderr`, `assert.log`, and applicable
`build.log`. These older wrappers do not all use RunCapture; in particular, the
public case discards CLI stderr. Do not promise a nonexistent `capture.json` or
manufacture a stderr record for it. The dispatcher report and invocation record
provide the surrounding execution account.

After the observations, follow `runCWorker` in CWorker.swift and `map_region` in
the C worker to the mapping prepared before application. Link to the
[architecture's explanation](../../docs/ARCHITECTURE.md#why-these-processes-exist)
and, if implemented by then, the worker document. The question is which prepared
apparatus makes these observations possible, and how that apparatus conditions
the experiment. Do not turn the answer into a claim that a fresh worker is an
empty process or that reporting survives every policy on every OS revision.

Missing publication or a required kill where the control expects a clean exit
would challenge the observed survival. The harness's
`sigkill_fallback` case deliberately withholds the exit request; it is not evidence
of an SBPL rule denying exit. An experiment varying preparation of the reporting
mapping would require additional apparatus and lies beyond the initial writing
work; present it only as a question, not an authorized implementation change.

**Equipment:** the direct cases require `app`, `worker`, and `clang`; the public
case requires `app` and `clang`. Source and embedded worker identity must match.
Keep the independent process observation and shared publication channel distinct.

## Evidence available without execution

The published atlas must be useful in a clean checkout without a Mac, signing
identity, or build. Linking only to local `tests/out/` paths would not satisfy
that requirement. Source inspection is already possible; worked observations
need durable, inspectable capture files as well.

At the inspected commit, the retention index names runs whose output directories
are absent from the committed snapshot. Their retention entries do not prove the
files are available to an outside reader. The committed disposition capture used
above is a real current-format example, but its embedded build identifies
`fcc3558cfc25a34c6a36efbb74d4f1ef69f58a7a` with a dirty describe string. It is not
an observation of the planning commit. The
[response-12 comparison receipts](../../tests/fixtures/comparison/baseline_response12/README.md)
are historical evidence, not input accepted by current semantic readers. Preserve
their bytes and provenance rather than translating them into apparent new runs.

For the initial atlas, collect a compact evidence companion under
`docs/atlas-evidence/<capture-id>/`, linked from `docs/ATLAS.md`. Keep the navigation
and explanatory prose in the top-level document, which the existing documentation
scan includes. The companion is a selection of captured evidence, not a new test
fixture oracle or a generated catalog of passing cases.

The writer should first look for reusable evidence with established source and
equipment provenance, applying
[the reuse rules](../../tests/AGENTS.md#evaluate-and-reuse-evidence). If it is
unavailable or applicability is uncertain, run the selected cases on a matching
signed build. The five routes need their primary observations; the ordering route
also needs the baseline and detection control if it claims observed sensitivity
to barrier removal. Do not require rerunning every neighboring case merely because
the atlas links to it.

For each included capture:

- Preserve the exact specimen, raw report bytes, independent file/process/gate
  observations, supplied fixture transcript where applicable, assertion output,
  terminal case report, and the applicable dispatcher invocation/configuration.
  Keep paired controls together. Include failed or surprising observations when
  they affect the interpretation; do not silently select only favorable runs.
- Record canonical case IDs, source commit and any established source delta,
  app identity and hashes, relevant OS/architecture and tool/equipment facts,
  capture command, overrides, and origin paths. Separate facts embedded in an
  envelope from facts recorded by the test apparatus.
- Keep a small inventory mapping published files to their original artifact
  paths and SHA-256 hashes, with an explicit list of omissions. Choose its simple
  format during writing; no public schema, generator, or application reader is
  needed. The original managed run retains the complete execution record.
- Exclude copied app bundles, compiler caches, and temporary executable trees
  from the documentation companion. Preserve their identifying hashes and
  relevant build/signature receipts. Keep raw report bytes unchanged. If a
  capture cannot be published unchanged, use another publishable capture or
  explicitly mark a derived display and retain access to its source; never call
  an edited envelope raw evidence.
- Give every displayed excerpt a source file and selector. Small before/after
  files should remain inspectable as bytes; a rendered hex excerpt is a reading
  aid, not a replacement witness. A JSON excerpt must not suppress competing
  evidence elsewhere in that report.

Evidence acquisition is an outstanding dependency, not work completed by this
plan. Missing equipment may leave a route described from source during drafting,
but the writer must label that state and must not call the atlas's worked
observation set complete. A surprising run is material for investigation, not a
reason to change the test or silently narrow the question.

## Illustrations and repository integration

Use the question table for navigation. Initially use two small authored text
timelines inside Markdown fences: one distinguishing a native effect from result
publication, and one distinguishing the query/collection/release sequence from
external mutation. Label them as schematic arrangements, link their observations,
and distinguish native-call receipts, publication, and external observation.
Do not invent timestamps or imply simultaneous global snapshots. Text timelines
remain readable in plain Markdown and need no new diagram generator; a complete
process topology would duplicate the architecture tour. The writer may refine
their layout after inspecting actual captures, but must retain the distinctions.

The implementation should make these focused integration changes:

| Destination | Change |
| --- | --- |
| `docs/ATLAS.md` | The question map, field notes, lateral links, reproduction pointers, evidence index, and capture provenance. |
| `docs/atlas-evidence/` | The bounded, immutable selections of observations described above. No local-run or cleanup ownership is transferred here. |
| `README.md` | Add a documentation entry explaining that the atlas explores PW through experiments. |
| `tests/README.md` | Add an atlas link near the harness orientation, retaining the suite map as the command/coverage reference. |
| `docs/ARCHITECTURE.md` and `docs/architecture.json` | Add a brief reciprocal prose link and represent the atlas in the existing document graph. Its node describes authored experimental routes and evidence access; check citations establish link/citation mechanics, not the truth of its conclusions. Update the manifest and regenerate, including affected counts and generated files. |

The architecture graph's existing document and test references are sufficient;
no new graph type, multi-document generator routing, capability map, or runtime
contract is needed. In particular, do not implement the worker plan's generator
extension as a prerequisite. Reconcile links if that document lands first, without
copying its inventory or adopting its separate assessment workflow.

Use [source-drift conventions](../../tests/suites/source_drift/README.md#generator-contracts)
for links, symbols, generated ownership, and numeric spans. Keep normative limits
in their owners; exact values in a captured specimen remain that experiment's
inputs. `docs/*.md` is scanned, while nested evidence files are not automatically
validated as a new corpus. Verify the evidence inventory and links explicitly;
do not expand scan scope or add generic verification infrastructure by default.

## Execution sequence

1. **Re-anchor the investigation.** Start from the inspected commit or record the
   successor commit and review relevant differences. Recheck case selectors,
   specimen builders, assertions, contracts, and documentation destinations.
   Keep unrelated work separate. Check the worker-document status instead of
   assuming its plan has been implemented.
2. **Resolve the evidence dependency.** Identify reusable captures and their
   applicability, or establish a matching app and the equipment for new runs.
   Before composing field notes, keep a short working table of each claim,
   actual observation, source, checker inference, counterexample, and unresolved
   question. This is a writing aid, not another maintained project taxonomy.
3. **Capture the selected experiments.** Use the public dispatcher and fresh
   managed output. Run the witness happy-path sentinel first and investigate a
   failure before relying on later live captures. Run fixture controls before
   crediting fixture-dependent interpretations. Retain all outcomes and cleanup
   observations. Run the opt-in mutation separately so its additional equipment
   and deliberate source interventions are visible.
4. **Write from the observations.** Build the first route and its evidence links
   as the model, then write the others. Inspect raw material before summarizing
   checker verdicts. If the intended interpretation does not survive, revise it
   or leave the question open; do not write a draft chapter around an expected
   answer. Select a few lateral departures and label all proposed variations.
5. **Integrate and review.** Add navigation and the document-graph changes,
   regenerate owned outputs, validate links and artifact provenance, and review
   both rendered and plain-text reading. Complete the checks below and record
   what was actually inspected, executed, and left unresolved.

Run commands from the repository root. For example, inspect a selection before
execution, and replace `REPLACE` with a fresh run name:

```sh
tests/run.sh --case witness_contract/happy_path_baseline --list
PW_TEST_OUT_DIR=tests/out/runs/atlas-baseline-REPLACE \
  tests/run.sh --case witness_contract/happy_path_baseline

tests/run.sh --case witness_contract/worker_killed_before_slot_publication --list
PW_TEST_OUT_DIR=tests/out/runs/atlas-publication-REPLACE \
  tests/run.sh --case witness_contract/worker_killed_before_slot_publication

tests/run.sh --case witness_contract/order_barrier_mutations --list
PW_TEST_OUT_DIR=tests/out/runs/atlas-mutations-REPLACE \
  tests/run.sh --case witness_contract/order_barrier_mutations
```

Use repeated exact `--case` selectors for the remaining core cases. Relevant
equipment controls are `validator_bridge/protocol_controls`,
`exec_fixture/controls`, and `runner_validator_failure/transcript_controls`.
Do not select the whole witness suite merely for convenience: whole-suite
selection includes its opt-ins. The catalog's requirements are authoritative even
when an individual checker appears to need less equipment.

The build and guide describe the supported macOS and signing setup. Missing
equipment is an explicit outstanding dependency, not a skip that establishes an
observation. Follow the existing unsandboxed-retry guidance when the automation
harness refuses XPC, log, signing, or compiler access. No BYOXPC installation is
needed for the core routes. Keep log collection separate from execution claims.
Never unlink the checkout lock, bypass artifact checks, or reuse ambiguous output.
Store original runs under `tests/out/` and preserve them through the existing
retention mechanism; `.tmp/atlas/` is the requested location of this plan, not a
test-evidence destination.

## Verification and maintenance

Verification should establish that a reader can inspect the questions and their
evidence, not just that Markdown links exist.

**Semantic review.** For each route, identify what comes from a native call,
worker publication, host observation, fixture observation, literal expectation,
or interpretation. Follow at least one path from raw evidence to a conclusion
and one path that could contradict it. Check that independent witnesses are
independent of the particular claim being tested. Separate implementations can
still share an ABI, expected matrix, source assumptions, or the same OS behavior;
separate authorship is not evidence of independence.

Preserve these local cautions during writing:

- The shared comparison matrix exercises producer and reader interpretations;
  its reuse is not another independent live observation.
- A fixture supplying `allow` is not a native prediction. A permission errno,
  signal, missing output, or matching denial-log candidate does not by itself
  authorize a sandbox-cause claim.
- The full-region harness uses no-op slots. An exit request, EOF, and observed
  process exit are different facts. An empty log query cannot prove allowance.
- Some suite prose still describes preallocated exec pipes and a descriptor
  limit raise. The inspected worker acquires exec resources per attempt.
  The descriptor-ceiling control establishes bounded resource use; source
  inspection establishes placement after apply. Do not carry the stale prose
  or overstate that test's inference into the atlas. Record any necessary
  correction separately from the document's experimental claims.
- Historical fixture prose that calls an old producer “current” must be read
  with its embedded provenance and current version-admission rules.

**Mechanical and visual checks.** Verify exact case IDs with `--list`, all
repository links/anchors/symbols, every capture inventory/hash, and each excerpt's
selector against the retained file. Ensure a clean checkout has the material
advertised for inspection. Review the document in rendered Markdown and plain
text: tables must be usable, timelines legible, and each route independently
navigable. Test the skeptical reader's path from the question map directly to
raw files, without requiring acceptance of explanatory prose first.

For the proposed architecture-manifest integration, regenerate through its owner
and check idempotence:

```sh
python3 docs/generate_architecture.py
python3 docs/generate_architecture.py
python3 docs/generate_architecture.py --check
tests/run.sh --case source_drift/generator_contract \
  --case source_drift/architecture_documentation --list
PW_TEST_OUT_DIR=tests/out/runs/atlas-docs-REPLACE \
  tests/run.sh --case source_drift/generator_contract \
  --case source_drift/architecture_documentation
```

Confirm that the second generation changes nothing. These existing checks cover
the prose scan, generator contracts, and affected architecture outputs; they do
not establish the routes' runtime claims or the completeness of a capture
selection. Add other existing checks only when changed inputs or meanings require
them. Documentation edits alone do not call for a complete live battery or new
tests mirroring the prose. If investigation identifies an application or checker
defect, preserve the counterexample and report separate work rather than quietly
expanding this document implementation into a repair.

Maintenance follows the question's actual dependencies. Revisit a route when its
case, checker, fixture, publication protocol, field semantics, or supported
equipment changes. Preserve historical captures with their provenance; add a new
capture rather than editing old observations into a current format. A schema bump
may make current semantic readers reject a historical capture without making its
raw bytes worthless. Keep that reading boundary explicit. Do not promise automatic
refresh or let a generator choose the interpretation.

## Open decisions and completion criteria

The proposed placement, five starting questions, direct evidence access, and
separation of observations are the initial design. Heading wording, field-note
length, exact excerpt selection, simple inventory format, and timeline layout
belong to the writer. The following questions depend on evidence not yet acquired:

| Question | What resolves it | Consequence |
| --- | --- | --- |
| Are reusable complete captures available for the primary routes? | Inspect retained files, provenance, and dependency applicability; otherwise run the selected cases. | Determines acquisition work and the capture revisions, not the truth of the expected result. |
| Do current observations support the proposed readings? | Compare raw effects, gate/transcript receipts, report fields, and checker assertions. | Revise the reading, expose uncertainty, or replace a route if it no longer illuminates the intended question. Preserve the contrary evidence. |
| Can the mutation control demonstrate sensitivity with available equipment? | A passing unmodified baseline and the specific rejected mutant effects, with component and signing receipts. | Until available, describe its source arrangement only; do not claim the atlas demonstrates observed detection. |
| Does a compact evidence selection leave out something a dissenting reader needs? | Trace each interpretation and plausible challenge through the selected files and original run inventory. | Include the missing observations or provide durable access to the complete relevant records. |
| Has the worker document landed or changed shared explanation? | Compare its implementation and scope at the writing revision. | Adjust cross-links and avoid duplication without making its completion a prerequisite. |

The atlas is ready when a reader can enter through any starting question, inspect
the actual arrangement and observations without execution, identify what PW and
the test each know, locate what would challenge the writer's reading, and find a
feasible way to reproduce or vary the experiment. Each worked observation must
have recoverable provenance; unperformed variations and source-only conclusions
must be unmistakable. Navigation, evidence links, generator checks, and the
semantic review must pass, with unresolved experimental questions left visible.
The completion report should name the actual checks and captures used, remaining
limits, and any separate follow-up work. It should make no general certification
claim about PW.
