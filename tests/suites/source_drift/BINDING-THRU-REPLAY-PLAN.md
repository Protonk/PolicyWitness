# Binding through replay

An investigation into how this repository binds documentation claims to code,
tests and receipts, ending in a design on paper and a package for whoever
later plans `docs/CHECK.md`. Facts below were established at `f468200`
(2026-10-22) unless another revision is named.

## Purpose and where this stops

The repository tries to keep a chain intact: root documentation, then named
`docs/` documents, then code comments and test messages, then source code and
receipts of app behavior. Much of the chain is enforced mechanically, but most
of that enforcement checks that a cited place exists, not that the place still
supports the claim. Recent defects in exactly that gap were found by outside
readers, not by the batteries or the drift checks.

The intended result is a package under `records/check-support/` that lets a
future planner write `docs/CHECK.md`: an account of the checking machinery as
current behavior, which that planner's team will make true. This plan has
three phases:

1. **Investigation**: inventory the source_drift machinery, then trace one
   claim (observation L) through it.
2. **Design**: a design on paper, tested by replaying historical defects
   against it.
3. **Outflow**: freeze the material and hand it to the CHECK.md planner.

This plan builds nothing. It does not change source_drift, the generators,
`docs/`, tests, the catalog, the build, `WORKER.md`, L's receipt or
`tests/RETAINED.json`. Defects found along the way are recorded as findings;
fixing them is separate work. Replay scripts may be written and committed
under `records/check-support/`, but nothing may wire them into `build.sh`, the
catalog or any battery.

## Background

### Three strengths of binding

- **Identity.** The text is rendered from one source of truth: generated
  regions, spans and copied guide sections (G1–G3 and G9 in the
  [generator contracts](README.md#generator-contracts)).
  The copies cannot disagree because only one copy exists.
- **Witness.** A test reads the documented claim as its expected value, so
  changing either side fails. The reference case is the limits value check:
  `compare` in `tests/suites/runner_abi_layout/limits.py` loads
  `docs/limits.json` and compares it with compiled values.
- **Pointer.** The citation names a place and a check confirms the place
  exists. `citation` in `docs/generator_common.py` accepts a non-Markdown
  citation when `symbol in text`, so a comment satisfies it; the `form` check
  adds that a definition of the right kind exists. `scope` strings and G10
  captions say honestly that this is not support.

Pointer binding is most of the system. A regex count of backticked symbol
links into `.swift`, `.rs`, `.c`, `.h`, `.py` and `.sh` files finds about
2,000 in five documents (WORKER 330, ARCHITECTURE 751, BUILD 558, LIMITS 354,
CONTRACT 8). In the other direction, 22 lines in five source files
(`build.sh`, `controller/src/disposition.rs`, `pw_probe_runner_abi.h`,
`CWorkerOrchestrator.swift`, `PWRunnerAPI.swift`) refer to those documents.
Someone editing code gets almost no signal about which sentences depend on it.

### Five ways a citation fails

1. The referent disappears. G4 catches this.
2. The referent changes meaning but keeps its name. Nothing catches this.
3. The prose changes while the referent does not. Caught only for spans.
4. The citation is coarser than the claim: a function cited for one line, or
   a token matched in a comment.
5. The cited check exists but does not assert the claim. Acknowledged in
   `scope` text; not checked.

No mechanism can decide whether a place supports a claim; that is a judgment
about meaning. A mechanism can always tell that one end of a citation has
changed since someone last judged it. The working goal is therefore: verify
identity, witness behavior, and make the age of each human judgment visible.

### Why observation L

`docs/WORKER.md` is a current-behavior account of the worker, and its section
"Launch observation L" reports what two production worker launches inherited:
descriptors 0–4, null-device stdout and stderr, cwd `/`, matching `ps` and
`ps -E` output, an inventory from `vmmap` and a refusal from `lsmp`.

- **Its evidence.** `docs/worker-launch-observation.json` is a receipt for run
  `20261018T223601Z_85d8418b`. It records the source revision `f85c7b0`, the
  worker source identity `4cb19db0…`, SHA-256 hashes of seven source files,
  selected raw captures and hashes of 59 original artifacts. The raw run is
  gitignored; `tests/RETAINED.json` pins it and
  `validator-selection-receipts-20261018`, whose `before.json` identifies the
  observed app. Nothing reads the receipt's hashes or identity.
- **Its weight.** In the `worker_capabilities` graph of
  `docs/architecture.json`, rendered into WORKER.md, 10 rows cite
  `launch_inventory` (s7, s13a, s13b, s13c, s14a, s15, s16e, s16f, s16g, s17).
  For seven of them (s13a, s14a, s15, s16e, s16f, s16g, s17) it is the only
  check. Its scope text says the inventory contents are "the separately
  identified observation L". The case is opt-in (`tests/catalog.json`,
  `default: false`), and it asserts only that captures, readiness and reaping
  succeed.
- **Its history.** An audit recorded in `51487f7` (finding WA-05 in
  `records/worker-pass6/initial-report.md`, removed in `d9346a3`) found that L
  had no provenance and had been recorded on a different worker build. It
  proposed three corrections: name the run, build and identity; state the
  sleep overrides; and make a worker-identity change trigger a
  `launch_inventory` rerun. The first two landed with the receipt in
  `69c7dfe`. The third, the only one that binds anything, did not. Three days
  later an outside reader found the same kind of drift again.

L is harder than most claims (it needs a signed app, an opt-in case and
process inspection), which is why it is the test case: a flow that handles L
handles the easy path too. The limits witness binding stays beside it as the
model of the easy path.

### The source_drift suite

The suite began in `c9f61c5` (2026-05-28) as one 186-line `check.py` and a
27-line `run.sh`, comparing native source lists across `meson.build`,
`build.sh` and `Package.swift`. Its name fitted that job. It now has eight
cases (`runner_source_manifests_agree`, `limits_documentation`,
`contract_versions`, `architecture_documentation`, `build_documentation`,
`generator_contract`, `markdown_reader`, `direct_python_start`) in 5,506 lines
across twelve files, including a 436-line README. `check.py` alone has 50
top-level functions; the original case now also runs the Known gap index,
harness guidance routes, the sandbox-API ban, registry checks and the
override-table lock. The suite became the place any checkable rule lands.
That, and the letter "L", are names given after the fact.

## Replay, by example

A replay asks: at a fixed historical revision, judging only from that
revision's tree and history, would a proposed design have flagged a claim, and
for the right reason? Its inputs are commits, which last; it needs no test
output, no network and no knowledge of later revisions.

The two cases below are examples, not the first task. They show what a replay
must state. Do not start by automating them. Read them during the inventory:
the inventory will turn up other defects, and each is a candidate replay for
the register.

### Example A: L against the worker it describes

| Revision | Tree at that revision | Expected verdict |
| --- | --- | --- |
| `51487f7` (2026-10-18) | `docs/WORKER.md:51` credits L ("L is the recorded production launch observation") and no receipt exists. `WORKER_IDENTITY` is `e1c88f81…`. | Flag: an observation is credited without provenance. |
| `69c7dfe` (2026-10-18) | The receipt is added. Its identity `4cb19db0…` equals `WORKER_IDENTITY`, and all seven recorded hashes match the tree. | No flag. This is the negative case. |
| `f468200` (2026-10-22) | The receipt is unchanged. `WORKER_IDENTITY` is `0da3a70a…`, and three recorded hashes differ (`pw_probe_runner.c`, `pw_probe_runner_abi.h`, `CWorker.swift`). | Flag: the receipt no longer identifies the tree, and nobody has reviewed applicability. The flag reports what changed. |

Every fact is readable from the tree. `docs/generate_worker_identity.py`
writes the identity into `tests/lib/contract.py`, `pw_probe_runner_abi.h` and
`CWorker.swift`, so at any revision:

```sh
git show <rev>:tests/lib/contract.py | grep WORKER_IDENTITY
git show <rev>:docs/worker-launch-observation.json   # absent before 69c7dfe
git show <rev>:<path> | shasum -a 256                 # against source_files
```

**What the positives mean.** Neither positive establishes that L's facts
became false. The audit reports that its rerun (run
`20261018T150641Z_12585892`) reproduced L's facts at its revision. At
`f468200` nobody has re-observed. A replay cannot tell whether a fact still
holds; it can only tell that the evidence no longer identifies the tree. The
expected verdicts are about visible, unreviewed age.

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
touching those files. The design must predict its flag count over this series
and justify it either way.

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
- each revision with its expected verdict and reason;
- how each fact is established from the tree (commands);
- open or held back;
- the prediction, written before evaluation;
- the result.

### Misleading passes to guard against

- **A design that always flags.** Every positive must have a paired negative.
- **A flag for the wrong reason.** The verdict must match the stated reason,
  not just flag versus no flag.
- **Knowledge from outside the tree.** WA-05's facts about run `b7815087` and
  build `6fd44fb` came from test output that existed then. A replay at
  `51487f7` may not use them.
- **Passing only the cases the design was shaped around.** Held-back cases are
  evaluated only after the design is frozen.
- **A rule that names the example's files or commits.** Naming L's receipt
  path as configuration is fine. A rule that works only for L is not a design.

## Working rules

- **Location.** Outputs live in `records/check-support/`, starting with a
  README that states its purpose, its single consumer (the CHECK.md planner)
  and its retirement condition: when `docs/CHECK.md` lands, the contents are
  absorbed or deleted.
- **Links.** Under `records/AGENTS.md`, only this plan may link into
  `records/check-support/`. CHECK.md will have to absorb the material, not
  link to it.
- **No dependence on `tests/out`.** Run evidence enters only as a committed,
  self-sufficient receipt. Replay inputs are commits.
- **Stamps.** Every inventory and trace artifact names the commit it describes.
  Others will keep changing the repository; stamps let a reader diff instead
  of trusting.
- **Commits.** Commit each phase's outputs before starting the next phase, so
  the next phase builds on a fixed record.
- **Replays.** Use only `git show` and `git log` up to the replay revision.

## Phase 1: Investigation

The two parts are staged, not run in parallel. The inventory is much larger
and may take several sessions, and each settled part of it can change what may
honestly be said about L's path. The L trace may be drafted early, but it stays
provisional until the inventory settles, and it is rewritten whenever an
inventory finding changes a statement in it.

### 1a. Inventory of the source_drift machinery

**Scope.** The source_drift suite and everything it runs or reads:
- the five generators and their shared modules (`docs/generate_*.py`,
  `docs/generator_common.py`, `docs/markdown_reader.py`);
- the baselines in `tests/fixtures/docs/`;
- the places the same rules run outside the suite: the generators' `--check`
  calls in `build.sh` (G3) and the baseline-growth refusal in release preflight.

Behavioral suites are in scope only as citation targets.

**What to record for each rule**, with the design question each column serves:

| Column | Design question it answers |
| --- | --- |
| Name and location (file and function), and the case or entry point that runs it | Which checkpoint owns which binding |
| Where it runs: build gate, default battery, release preflight or opt-in | Where a new binding could run at acceptable cost |
| Inputs read: documents, manifests, source, fixtures, baselines | Raw material for a reverse index |
| Binding class: identity, witness, pointer, or structure (presence and navigation) | The census; which claims can move to stronger binding |
| Failure modes caught, and failure modes not caught | Coverage the design must add or label |
| Controls and their cost | Whether the apparatus earns its keep |
| Name fit: does the name or location describe the job? | Split or rename questions for CHECK.md |
| Known misses, from git history or replay candidates | Entries for the replay register |

A cell may say "unknown" only together with what would settle it. Record
replay candidates in the register as soon as they appear.

**Done when** every rule in scope has a row, every unknown says what would
settle it, and the inventory is stamped with its commit.

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
- the two pins in `tests/RETAINED.json`.

The expectation to confirm or refute is that the chain is pointer-only where
it matters. The capability rows' `launch_inventory` citation is satisfied
because `test_selected launch_inventory` exists. The scope text is not
checked, the receipt's hashes are not compared, and the receipt's worker
identity is not compared with `WORKER_IDENTITY`.

**Done when** each claim site has its rule, what that rule establishes and its
class, consistent with the settled inventory, and the trace carries the same
stamp as the inventory.

## Phase 2: Design

### 2a. Design on paper

Write `records/check-support/design.md`. Consider these directions in this
order:

1. **A reverse index:** for a changed file or symbol, which claims cite it.
2. **Witness binding for behavioral claims:** tests declare a claim ID and a
   statement beside the assertion, and documents cite the ID.
3. **Checkpoint assignment:** identity binding at build time; source-level
   witnesses in the default battery; witnesses that need a signed app (L) at
   release acceptance; aging reports in drift checks, refused only at release
   preflight.
4. **A generated census** of claims by binding class.

Review stamps, meaning fingerprints of cited regions that mark a citation
unreviewed when they change, are considered only in a narrow form: keyed on
fingerprints the repository already computes, such as the worker identity,
the ABI layout golden or generated identities. Stamps on arbitrary text
regions tend to make re-stamping a reflex.

For L in particular, decide:
- which of L's facts become test expectations and which remain a dated census;
- what trigger marks the receipt unreviewed, using the churn series to choose
  its grain;
- where its witness runs.

Also state the design's own cost (new rules and their controls), held to the
same standard as the inventory's cost column.

### 2b. Replay the examples

Write each prediction into the register first, then evaluate Examples A and B
with read-only scripts in `records/check-support/replay/`. A script takes a
revision, reads only through `git show` and `git log`, and writes only to its
output directory. A wrong verdict or a wrong reason sends the work back to
2a, after which every replay runs again, not just the failing one. A replay
that shows the inventory misdescribed a rule reopens that inventory row.

### 2c. Broaden to N replays

N is set by coverage, not by count:
- at least one positive replay for each failure mode the design claims to
  catch;
- a negative paired with every positive;
- at least one replay for each class the design declares out of scope.

Before the design is frozen, mark some register entries as held back (at
least one in each class that has more than one candidate). Evaluate them only
after the freeze, and report their results separately. If the design passes
only the open cases, that is the most important thing the CHECK.md planner
can learn from this plan.

**Done when** the coverage rule is met, held-back results are reported, and
the churn series has the design's predicted and actual flag counts.

## Phase 3: Outflow

1. **Freeze.** No design changes from here on.
2. **Package.** The `records/check-support/` README indexes every artifact and
   marks each as either "current behavior at `<commit>`" (inventory, trace) or
   "proposed" (design). It lists the replay register with results, including
   held-back and out-of-scope cases, and the open questions with what would
   answer each.
3. **Readiness.** Apply CONTRIBUTING's test for a plan: the CHECK.md planner
   can write their plan from this package without reconstructing its
   rationale, and can recognize evidence that would require reconsideration.
   Ask it as a concrete question: could they proceed without this plan's
   conversation history and without re-deriving any fact here?
4. **Hand-off notes for the CHECK.md planner:**
   - CHECK.md absorbs this material and does not link to it.
   - CHECK.md's own claims fall under the machinery it describes: generator
     registration, the prose scan, G11 symbol links and the Known gap rule.
     If its claims about checks cannot be bound, that is itself a finding.
   - Today's closest thing to CHECK.md is the "Generator contracts" section of
     the source_drift README. Ownership moves, and that README shrinks to facts
     about the suite.
   - Whether to rename or split source_drift is answered by the inventory's
     name-fit column.
   - `records/check-support/` retires when CHECK.md lands.

## Open questions

| Question | What would answer it | What depends on the answer |
| --- | --- | --- |
| Is source_drift plus the generators the right boundary for "the checking machinery", or do structural checks in other suites belong too? | The inventory's inputs column, and any rule found outside the boundary that binds documentation | Design scope and CHECK.md's scope |
| What fingerprint grain should observation receipts use: the whole worker identity, the receipt's file hashes, or anchored regions? | The churn series in Example A, and the inventory of fingerprints the repository already computes | L's trigger; whether review stamps are used at all |
| Can disagreement between two pieces of prose (Example B) be detected without a registry of claim subjects? | A design attempt and its replay | Whether CHECK.md covers comments outside the prose scan |
| Should `launch_inventory`'s stable facts become assertions, and at which checkpoint? | The L trace and the checkpoint assignment in 2a | Whether the seven capability rows with only `launch_inventory` as their check gain a witness |

Re-observing L, changing its pins and editing WORKER.md are outside this plan.
Someone may do them independently; replays are fixed to commits and are not
affected.
