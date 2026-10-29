# Binding through replay

An investigation into how this repository binds documentation claims to code,
tests and receipts, ending in a design on paper and an internal transfer to the D2 investigation.
WORKSET-PLAN.md amends this plan: future CHECK writing, planning and handoff
deliverables are excluded; acceptance and disposition finish in this workset.
The fixed investigation source is `cf0136bbb6366d5f787c3547ec69d757772898c0`
(2026-10-29); the original starting facts below have been refreshed in the
[bounded inventory](../../../records/check-support/inventory.md) and
[L trace](../../../records/check-support/l-trace.md). The
[package account](../../../records/check-support/README.md) indexes owned artifacts,
including [cost evidence](../../../records/check-support/costs.md) and
[findings requiring disposition](../../../records/check-support/findings.md). Historical replay examples keep their named revisions; refreshing
the inventory does not move those examples to a new baseline.

## Purpose and where this stops

The repository tries to keep a chain intact: root documentation, then named
`docs/` documents, then code comments and test messages, then source code and
receipts of app behavior. Much of the chain is enforced mechanically, but most
of that enforcement checks that a cited place exists, not that the place still
supports the claim. Recent defects in exactly that gap were found by outside
readers, not by the batteries or the drift checks.

The intended result is a package under `records/check-support/` that lets a
D2 investigator distinguish the checking machinery's current behavior from
proposed changes and decide which bounded corrections are supported. This
plan has three phases:

1. **Investigation**: inventory the source_drift machinery, then trace one
   claim (observation L) through it.
2. **Design**: a design on paper, refined through open historical replays,
   then frozen before evaluating held-back cases.
3. **Outflow**: review the findings and hand them to the successor planner.

This plan builds nothing. It does not change source_drift, the generators,
`docs/`, tests, the catalog, the build, `WORKER.md`, L's receipt or
`tests/RETAINED.json`. Defects found along the way are recorded as findings;
fixing them is separate work. Replay scripts may be written and committed
under `records/check-support/`, but nothing may wire them into `build.sh`, the
catalog or any battery.

## Background

### What each binding establishes

- **Identity.** The text is rendered from one source of truth: generated
  regions, spans and copied guide sections (G1–G3 and G9 in the
  [generator contracts](README.md#generator-contracts)).
  Checked-in copies can disagree; currency checks detect that disagreement
  with the output rendered from the owning input.
- **Value agreement.** `compare` in
  `tests/suites/runner_abi_layout/limits.py` loads `docs/limits.json` and
  compares it with compiled values. This establishes equality of the selected
  values, not their behavioral consequences. Behavioral controls need their
  own assertions and independent expectations; changing the manifest must
  not silently change their oracle.
- **Behavioral witness.** A test asserts an observation under stated
  conditions. Its support for a claim depends on those assertions and
  conditions. A claim ID can locate that relationship; it does not prove it.
- **Pointer.** The citation names a place and a check confirms the place
  exists. `citation` in `docs/generator_common.py` accepts a non-Markdown
  citation when `symbol in text`, so a comment satisfies it; the `form` check
  adds requirements for the named check form. For `rule` citations, the
  function must be registered in the module's statically read `RULES` table.
  These checks do not establish the support described by `scope` strings.

Presence and navigation checks also establish structure without asserting a
claim. The inventory distinguishes these relationships instead of assigning
one strength to an entire document or test. For each claim-to-evidence
relationship, identify the claim, the asserted observation or comparison, its
conditions, the supporting source or receipt, and any judgment about applying
that evidence to the current implementation. A declared dependency, a recorded
input and semantic support are different facts.

### Five ways a citation fails

1. The referent disappears. G4 catches this.
2. The referent changes meaning but keeps its name. Existence checks still pass.
3. The prose changes while the referent does not. Currency checks cover owned
   spans, but do not judge independently written prose.
4. The citation is coarser than the claim: a function cited for one line, or
   a token matched in a comment.
5. The cited check exists but does not assert the claim. Acknowledged in
   `scope` text; not checked.

Human review remains responsible for whether the evidence supports the claim.
A mechanism can identify changes to represented, fingerprinted inputs since
that review; it cannot establish that the representation includes every
relevant dependency. The working goal is to verify identity and value
agreement, witness behavior, and expose changes that call an applicability
judgment into question.

### Why observation L

`docs/WORKER.md` is a current-behavior account of the worker, and its section
"Launch observation L" reports what two production worker launches inherited:
descriptors 0–4, null-device stdout and stderr, cwd `/`, matching `ps` and
`ps -E` output, an inventory from `vmmap` and a refusal from `lsmp`.

- **Its evidence.** `docs/worker-launch-observation.json` is a receipt for run
  `20261018T223601Z_85d8418b`. It records the source revision `f85c7b0`, the
  worker source identity `4cb19db0…`, SHA-256 hashes of seven source files,
  selected raw captures and hashes of 59 original artifacts. The raw run is
  gitignored. The receipt and WORKER.md still describe a pinned run, but
  `tests/RETAINED.json` no longer pins it or
  `validator-selection-receipts-20261018`, whose `before.json` identifies the
  observed app. At the current starting point, five of the seven source hashes
  differ: the C worker, its ABI header, `CWorker.swift`, `launch_inventory.py`
  and its suite's `run.sh`. The current worker identity is `1df328dc…`.
  No current check compares these identities or hashes for applicability.
- **Its weight.** In the `worker_capabilities` graph of
  `docs/architecture.json`, rendered into WORKER.md, 10 rows cite
  `launch_inventory` (s7, s13a, s13b, s13c, s14a, s15, s16e, s16f, s16g, s17).
  For seven of them (s13a, s14a, s15, s16e, s16f, s16g, s17) it is the only
  check. Most of these scopes refer inventory contents to the separately
  identified observation L. The case is opt-in (`tests/catalog.json`,
  `default: false`). It asserts capture success, readiness behavior, completion
  and confirmed reap, including readiness `EPIPE` in the pre-ready window;
  s17 explicitly cites that behavior. It does not assert L's exact descriptor
  inventory or the equality of its two `ps` captures. The trace must separate
  those observations from the behavior the case already asserts.
- **Its history.** An audit recorded in `51487f7` (finding WA-05 in
  `records/worker-pass6/initial-report.md`, removed in `d9346a3`) found that L
  had no provenance and had been recorded on a different worker build. It
  proposed three corrections: name the run, build and identity; state the
  sleep overrides; and make a worker-identity change trigger a
  `launch_inventory` rerun. The first two landed with the receipt in
  `69c7dfe`, establishing provenance and conditions. The automatic rerun
  trigger did not. A later outside review again found evidence whose
  applicability to the changed implementation had not been reviewed.

L is useful because it needs a signed app, an opt-in case and process
inspection. It also distinguishes a dated observation from reuse in a
current-behavior account: changing the source does not falsify the historical
observation. The limits comparison provides a simpler, mechanically checkable
relationship alongside it. Neither covers every class; Example B introduces
prose disagreement without a citation.

### The source_drift suite

The suite began in `c9f61c5` (2026-05-28) as one 186-line `check.py` and a
27-line `run.sh`, comparing native source lists across `meson.build`,
`build.sh` and `Package.swift`. Its name fitted that job. At the current
starting point it has eight cases, with 19 registered rules in `check.py` and
10 in `build_rules.py`, plus generator, reader and command controls outside
those tables. Build-entry, native-policy and native-source controls now run
as three default offline cases in `preflight`.

The rule tables, generator input declarations and per-control receipts give
the investigation concrete starting points. Their contracts are in the
[suite README](README.md), [fixture helper](../../lib/fixture_inputs.py) and
[receipt helper](../../lib/receipts.py). Declarations are a reviewed account
of inputs, and receipts observe registered inputs and explicit command
wrappers; neither is an audit of all reads or descendant processes.

## Replay, by example

A replay asks: at a fixed historical revision, judging only from that
revision's tree and history, would a proposed design have flagged a claim, and
for the right reason? Historical facts come from commits, not surviving local
test output. The design is new, and old trees may lack the registrations and
review metadata it would require. Each replay therefore separates:

- facts extracted from the tree and history available at the replay revision;
- proposed annotations supplied to model adoption of the design, with their
  provenance and the information needed to author them at that time;
- the design version and its prediction, committed before evaluation.

A replay with supplied annotations tests the proposed contract under those
assumptions. It does not demonstrate that the historical repository would
have discovered the relationship automatically. Later findings can select a
case and establish its evaluation target, but cannot silently supply a
connection or applicability review to the simulated checker.

Results distinguish a detected discrepancy, missing registration or evidence,
and a declared exclusion from scope. A clean negative means the required
inputs were present and the applicable check passed. Missing inputs do not
count as a clean negative. Report both the result and its reason; the tables
below describe the distinctions the design should explain.

The two cases below are examples, not the first task. They show what a replay
must state. Do not start by automating them. Read them during the inventory:
the inventory will turn up other defects, and each is a candidate replay for
the register.

### Example A: L against the worker it describes

| Revision | Tree at that revision | Expected verdict |
| --- | --- | --- |
| `51487f7` (2026-10-18) | `docs/WORKER.md:51` credits L ("L is the recorded production launch observation") and no receipt exists. `WORKER_IDENTITY` is `e1c88f81…`. | Flag: an observation is credited without provenance. |
| `69c7dfe` (2026-10-18) | The receipt is added. Its identity `4cb19db0…` equals `WORKER_IDENTITY`, and all seven recorded hashes match the tree. | No identity-change flag. This is the paired negative; matching identity alone does not prove support. |
| `f468200` (2026-10-22) | The receipt is unchanged. `WORKER_IDENTITY` is `0da3a70a…`, and three recorded hashes differ (`pw_probe_runner.c`, `pw_probe_runner_abi.h`, `CWorker.swift`). | Flag: the receipt no longer identifies the tree, with no recorded applicability review. The flag reports what changed. |

Every fact is readable from the tree. `docs/generate_worker_identity.py`
writes the identity into `tests/lib/contract.py`, `pw_probe_runner_abi.h` and
`CWorker.swift`, so at any revision:

```sh
git show <rev>:tests/lib/contract.py | rg WORKER_IDENTITY
git show <rev>:docs/worker-launch-observation.json   # absent before 69c7dfe
git show <rev>:<path> | shasum -a 256                 # against source_files
```

**What the positives mean.** Neither positive establishes that L's facts
became false. The audit reports that its rerun (run
`20261018T150641Z_12585892`) reproduced L's facts at its revision. At
`f468200` the tree records no replacement observation. A replay cannot tell
whether a fact still holds; it can tell that the evidence no longer identifies
the tree. The expected verdicts concern unreviewed reuse for a changed
implementation, not the truth of the dated observation. The replay must state
how the design recognizes that reuse and where its initial applicability
judgment comes from.

**The churn series.** This is a measurement, not a pass or fail. After
`69c7dfe` the worker identity changed five times:

| Commit | Date | What changed among the identity's inputs |
| --- | --- | --- |
| `e04ec96` | 2026-10-18 | `build.sh`, `meson.build` (thin arm64 outputs); identity regions |
| `2b0be8e` | 2026-10-19 | `PWRunnerAPI.swift`; identity regions |
| `16e2f83` | 2026-10-20 | `build.sh` (direct Python start); identity regions |
| `146e7d2` | 2026-10-20 | `build.sh`; identity regions |
| `cb8a110` | 2026-10-21 | `build.sh`, `meson.build`, `pw_probe_runner.c` (native-only build); identity regions |

Across the receipt's launch-path files (`CWorker.swift`,
`CWorkerOrchestrator.swift`, `pw_probe_runner.c`, `pw_probe_runner_abi.h`),
the only change outside the generated identity regions and comments is in
`cb8a110`. It removes six lines: the non-arm64 branches of a spin wait in
`pw_probe_runner.c`. The window behind WA-05 looks similar. Between L's
original build at `6fd44fb` (identity `33890392…`) and `51487f7`, the
identity changed once, and those files changed only in comments (`37be3d2`)
and identity regions.

So a trigger keyed to the whole worker identity fires five times for one
launch-path code change, and that change removes code the only supported
architecture never compiled. A trigger keyed to source lines would miss build
flag changes such as `e04ec96`, which can change the compiled worker without
touching those files. Predict both the flag count and the work needed to
resolve those flags: which changes require a review, a new observation or no
action, and what evidence permits each disposition. The series measures the
design's maintenance cost as well as its sensitivity.

### Example B: two statements about `/usr/bin/python3`

| Revision | Tree at that revision | Expected verdict |
| --- | --- | --- |
| `46fe43e` (2026-10-04) | The Makefile header says "/usr/bin/python3 -B is deliberate: the system interpreter, writing no bytecode." Nothing in the tree says otherwise. | No flag. The statement is false about macOS, but the repository cannot know that. |
| `b410ac3` (2026-10-16) | `docs/BUILD.md`, `tests/lib/checkout_lock.py` and `tests/lib/checkout_lock.sh` state that `/usr/bin/python3` is a shim. The Makefile is unchanged. | Flag: two statements about `/usr/bin/python3` disagree. |
| `d46ccd6` (2026-10-21) | Same disagreement, on the last revision before the correction. | Flag. |
| `99cf137` (2026-10-22) | The Makefile says "Python helpers run through tests/lib/python.sh, never the /usr/bin/python3 shim." | No flag. |

B differs from A in class. No build, receipt or code change is involved: two
pieces of prose disagree, and no citation connects them. The Makefile header is
outside the prose scan, and "interpreter" against "shim" is not a mechanical
contradiction unless something records that the two are exclusive. Its first
negative teaches a limit that holds for every design: replay can detect what
the repository itself states, not external truth. A design may either say how
it would connect these two sites or declare the class out of scope. Either is
a valid replay result if the prediction is written down before evaluation.

### Seeds, not yet worked

The audit report at `51487f7` holds other candidates. Read it with
`git show 51487f7:records/worker-pass6/initial-report.md`.

| Finding | Class | Expected kind of result |
| --- | --- | --- |
| WA-02: 46 of 137 capability rows cite no check that exercises the stated behavior | Failure mode 5 | Labeled unbound, not flagged |
| WA-09: two misattributed edge sources | Failure modes 2 or 4 | To be determined: the cited symbol existed but was the wrong one |
| WA-06: a generated column carried audit-process history and understated observations | Identity binding rendering wrong source data faithfully | Out of scope; bounds the design |
| WA-11: `sysctl_read` success bounded by an undisclosed 4,096-byte buffer | Omission: no citation exists to bind | Out of scope; bounds the design |

Working a seed means identifying the claim sites and revisions from the tree.
Other sources of candidates are earlier audit reports in git history, findings
by outside readers, and commits whose messages correct a stale statement.

### What a replay case records

The register at `records/check-support/replays.md` holds one entry per case:

- an ID;
- the claim sites;
- the class (failure mode, or out of scope);
- who found the defect and where that is recorded;
- each revision, design version, expected verdict and reason;
- how each fact is established from the tree (commands);
- any proposed annotations, their provenance and whether the result depends
  on them;
- open or held back, including who has seen the case and its expectation;
- the prediction and the commit that fixed it before evaluation;
- the result.

### Misleading passes to guard against

- **A design that always flags.** Every positive must have a paired negative.
- **A flag for the wrong reason.** The verdict must match the stated reason,
  not just flag versus no flag.
- **Knowledge from outside the tree.** WA-05 reports facts about run
  `b7815087` and build `6fd44fb` drawn from local output. At `51487f7` the
  committed report establishes what the audit said; it does not supply the
  missing raw output or app inventory for an independent comparison.
- **Passing only the cases the design was shaped around.** Delayed evaluation
  is useful, but is not independent if the designer already knows the case and
  its expected result. Record that exposure. Independent evaluation requires
  another person to withhold cases or expectations until after the freeze.
- **A rule that names the example's files or commits.** Naming L's receipt
  path as configuration is fine. A rule that works only for L is not a design.

## Working rules

- **Location.** Outputs live in `records/check-support/`, starting with a
  README that states its purpose, its single handoff consumer (the successor
  planner for checking changes and CHECK.md) and its retirement condition:
  acceptance, internal absorption and disposition within this workset. This plan and its package retire
  together; material still needed moves into the successor plan's own records.
- **Links.** Under `records/AGENTS.md`, only this plan may link into
  `records/check-support/`. Permanent documentation absorbs the useful account
  rather than linking to the package.
- **Evidence.** Commit the facts and compact summaries needed to assess the
  findings, including provenance for any measurements taken from receipts.
  Label raw `tests/out` evidence as local and gitignored; its later removal
  must not make the handoff unintelligible. Historical replay facts come from
  commits, with proposed annotations identified separately.
- **Stamps.** Every inventory and trace artifact names the commit it describes.
  Others will keep changing the repository; stamps let a reader diff instead
  of trusting.
- **Commits.** Commit each phase's outputs before starting the next phase, so
  the next phase builds on a fixed record.
- **Replays.** Extract historical facts through `git show` and `git log` up to
  the replay revision. Keep the evaluated tree separate from the proposed
  design and annotations supplied to the replay.

## Phase 1: Investigation

Settle the inventory before crediting the L trace. Both describe the same
chosen revision; refresh the starting facts if the investigation begins on a
later tree. The fixed historical examples remain unchanged.

### 1a. Inventory of the source_drift machinery

**Scope.** Start from a finite set of entry points:

- the 19 `check.py` and 10 `build_rules.py` rows, using their stable rule IDs,
  callables, declared inputs, helpers and execution contracts;
- the eight source_drift cases, the five generators and shared readers, their
  input/target/span declarations, and the baselines in `tests/fixtures/docs/`;
- `preflight/build_entry_controls`, `preflight/native_policy_controls` and
  `preflight/native_source_controls`, including their canonical commands;
- the places the same checks run outside these cases, including generator
  currency checks in `build.sh` and baseline-growth refusal in release
  preflight.

The tables are a starting inventory, not a claim of completeness. Add checks
outside them when they enforce a distinct contract in these entry points;
group controls under the rule they exercise. Follow shared readers far enough
to establish that contract and its inputs. Keep separate checkpoint entries
where the same mechanism runs with different inputs, equipment or refusal
policy. Behavioral suites otherwise enter as citation targets, with the limits
comparison and L traced in detail. Record a proposed scope extension when a
finding depends on another suite, rather than recursively inventorying every
dependency.

**What to record for each rule**, with the design question each column serves:

| Column | Design question it answers |
| --- | --- |
| Name and location (file and function), and the case or entry point that runs it | Which checkpoint owns which binding |
| Where it runs: build gate, default battery, release preflight or opt-in | Where a new binding could run at acceptable cost |
| Declared inputs, observed inputs where available, and gaps established by source review | Raw material and limits for a reverse index |
| Binding class: identity, value agreement, behavioral witness, pointer, or structure | What the check establishes about the related claims |
| Failure modes caught, and failure modes not caught | Coverage the design must add or label |
| Controls, equipment and cost, distinguishing measurements from estimates | Whether the apparatus earns its keep |
| Name fit: does the name or location describe the job? | Ownership and naming questions for D2 |
| Known misses, from git history or replay candidates | Entries for the replay register |

A cell may say "unknown" only together with what would settle it. Record
replay candidates in the register as soon as they appear.

Use the current receipt contract when accounting for cost: registered input
snapshots are observations of those inputs, and direct launches count explicit
command wrappers, not all helper invocations or descendant processes. Preserve
those boundaries in comparisons. Existing usable evidence can supply measured
costs; missing measurements need a settling action, not a full battery run by
default.

**Done when** the entry points reconcile with the inventory, including checks
outside the rule tables, and each row has its checkpoint, contract, evidence
and remaining questions. Stamp the inventory and commit any receipt-derived
summary needed by its reader.

### 1b. Trace of L through the machinery

For each place L is claimed or relied on, record which inventory rule touches
it, what that rule establishes, and the binding class:

- the "Launch observation L" section and the Starting authority prose in
  `docs/WORKER.md`;
- `docs/worker-launch-observation.json`;
- the 10 capability rows in `docs/architecture.json` that cite
  `launch_inventory`;
- `launch_inventory` in `tests/catalog.json` and `tests/CHANGE-VERIFICATION.md`, and
  the production launch inventory section of
  `tests/suites/runner_exec_inheritance/README.md`;
- the receipt's retention claims against the current `tests/RETAINED.json`.

Separate the dated census, assertions already made by `launch_inventory`,
and claims that reuse L as support for current behavior. Citation validation
does not check the meaning of the scope text. Trace the existing EPIPE,
completion and reap assertions as well as the unasserted inventory contents;
do not classify every relationship as pointer-only because citation validation
itself is mechanical. The receipt's hashes and worker identity currently have
no automated applicability comparison, and its former pins are absent.

**Done when** each relationship identifies its claim, evidence, conditions,
what the check establishes and any remaining applicability judgment, consistent
with the inventory and carrying the same stamp.

## Phase 2: Design

### 2a. Design on paper

Write `records/check-support/design.md`. Use the inventory and trace to assess
these directions:

1. **A reverse index:** for a changed file or symbol, which claims cite it.
2. **Explicit claim relationships:** identify assertions, observations and
   conditions beside the test or receipt, with claim IDs that documents can
   cite. Decide who reviews support and how that judgment is represented.
3. **Checkpoint assignment:** consider currency at build time, source-level
   checks in the default battery, and signed-app witnesses at acceptance.
   Decide where changed applicability is reported and where it blocks a
   checkpoint; the assignment is an output of the investigation.
4. **A generated census** of claims by binding class.

Prefer contracts with explicit inputs, results and review responsibilities.
For any proposed review stamp, start with fingerprints the repository already
computes, such as the worker identity or ABI layout golden. If these cannot
identify the relevant changes, explain what another representation adds and
what it costs. A fingerprint detects changed represented inputs; re-stamping
alone must not stand in for an applicability judgment.

The design needs to settle the consequential choices, not just list possible
mechanisms: what registers a relationship, what triggers review, how review or
new evidence restores applicability, what each checkpoint reports or refuses,
and how absent registrations, unavailable inputs and unsupported claims appear.
For L, decide which facts become expectations, which remain a dated census,
what change triggers review and where any new witness runs.

Show a complete worked path from changed input through affected claims and
diagnostic to review action and its recorded outcome. Use L and the simpler
limits comparison to expose differences in the contracts. Example B must
either have an explicit proposed connection or a stated exclusion. Account
for new rules, controls, equipment and required review work; distinguish
measured costs from estimates. The replay results should support these choices
or identify what evidence is still needed to choose.

### 2b. Develop through open replays

Write each prediction into the register first, then evaluate Examples A and B
with read-only scripts in `records/check-support/replay/`. Each evaluation
names its revision, design version and any supplied annotations; historical
facts are read through `git show` and `git log`. Scripts write only to their
output directory. A wrong verdict or reason calls for a revised design or a
justified correction to the expectation, retaining the earlier result. Rerun
the open cases against a changed design. If a replay shows that the inventory
misdescribed a rule, correct that row too.

### 2c. Broaden, freeze and evaluate

N is set by coverage, not by count:

- at least one positive replay for each failure mode the design claims to
  catch;
- a negative paired with every positive;
- at least one replay for each class the design declares out of scope.

Reserve held-back cases before refining the design against them, at least one
in each class with multiple candidates. Freeze and commit the design,
annotation policy, open results and predictions before evaluating those cases.
Record whether the designer knew the held-back expectations; if independent
selection is unavailable, describe this as delayed evaluation rather than
independent validation.

Report held-back results separately. A resulting design change creates a new
version, with those exposed cases now part of its development set. Rerun them
with the other open cases; a further claim of independent evaluation needs
fresh withheld cases or expectations. A failed frozen design is a useful
finding, not a reason to rewrite its earlier predictions.

**Done when** the coverage rule is met, held-back results are reported, and
the churn series records predicted and replayed flag counts plus the review
or observation work required to resolve them. Every result identifies the
design version and assumptions it evaluates.

## Phase 3: Outflow

1. **Package.** The `records/check-support/` README indexes every artifact and
   marks each as either "current behavior at `<commit>`" (inventory, trace) or
   "proposed at design version `<version>`". It includes the replay register,
   supplied annotations, open and held-back results, exclusions, cost summaries
   and unresolved questions with what would answer each.
2. **Acceptance review.** Apply the
   [planning guidance](../../../CONTRIBUTING.md#planning-a-change): can the
   successor planner understand the recommendation, its evidence and its limits
   without this conversation or missing local output? Distinguish settled
   decisions from alternatives that still need evidence. Acceptance concerns the quality
   of the investigation and handoff; it does not implement the proposed design.
3. **Internal transfer.** Record accepted findings, exclusions, name-fit and
   ownership complications for D2. Do not allocate a future CHECK document,
   design its narrative/registration, or prepare a future-writing handoff.
4. **Retirement.** After D2 accepts and absorbs the findings and the workset
   disposes them, transfer still-needed material into D2-owned records and
   retire this plan and package together. No future CHECK work is a condition.

## Open questions

| Question | What would answer it | What depends on the answer |
| --- | --- | --- |
| Does a claim need checks outside the named source_drift, preflight and build/release entry points? | A traced relationship whose support crosses that boundary | Any bounded scope extension for D2 |
| What fingerprint grain should observation receipts use? | The churn series, existing identities and file hashes, and the cost and coverage of any proposed alternative | L's review trigger and the work required to resolve it |
| Can disagreement between two pieces of prose (Example B) be detected without a registry of claim subjects? | A design attempt and its replay | Whether the proposed machinery covers comments outside the prose scan |
| Which unasserted facts in L should become expectations, and at which checkpoint? | The L trace's distinction between existing assertions, dated observations and present-tense reuse | Which capability claims gain additional witnesses and which retain an applicability judgment |

Re-observing L, changing its pins and editing WORKER.md are outside this plan.
Someone may do them independently; replays are fixed to commits and are not
affected.
