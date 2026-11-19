# Technical-account passes and reader probes

Daughter of [TRACE-MANAGEMENT-PLAN.md](TRACE-MANAGEMENT-PLAN.md), covering step 2
of its [remaining work](TRACE-MANAGEMENT-PLAN.md#remaining-checkpoint-and-later-work).
The step runs from the completed product checkpoint (`34639f3d`) to a prune
apply. The management plan keeps authority over dispositions, the guide freeze
and outflows. Nothing here runs until it is marked in [Approval](#approval).

## Result and limits

- Three writer passes apply
  [ACCOUNTS-WORKLIST.md](trace-assessments/ACCOUNTS-WORKLIST.md) and
  [ACCOUNTS-ADDENDA.md](trace-assessments/ACCOUNTS-ADDENDA.md) under
  [DISPOSITIONS.md](trace-assessments/DISPOSITIONS.md). Each entry ends
  applied, already done, not applicable or contradicted, with its reason.
- Four read-only reader probes give constrained views of the accounts that
  deep passes cannot give. A deep reader checks that a statement matches its
  producer. A reader who sees less shows what a statement leads someone to
  conclude, what a test actually establishes, and where restatements of one
  rule diverge.
- Probes produce leads, not findings, and add no completion obligation.
- **Out of scope:** the guide (frozen), product behavior, build inputs and
  management steps 3–5. An entry that needs a build-input edit is listed and
  lands in one commit just before step 4's build.

## Order

| # | Work | Who | Gate |
| --- | --- | --- | --- |
| 0 | Retention note for the 41 runs deleted on November 19; create the ledger; confirm AC power and a clean tree | Coordinator | none |
| 1 | Pass 1: contract surfaces, presentation map, contract README, generator code | Writer W1, then reviewer V1 | Approval |
| 2 | Pass 2: failure contract, limits and shared-region owners, architecture, technical documents, READMEs | Writer W2, then reviewer V2 | Approval |
| 3 | Answer keys for P1, P2 and P4, and the owner list for P3, committed before any probe starts | Coordinator | Approval |
| 4 | Probes P1–P4, with no writer active | Four workflows | Approval |
| 5 | Adjudicate every lead and record its destination | Coordinator | none |
| 6 | Pass 3: test-side repairs, with the P4 leads; then Pass 4 for any account corrections that adjudication accepted | Writer W3, then V3; W4 if needed | Approval |
| 7 | Commit the ledger and probe records, record progress, preview the prune; apply only if approved | Coordinator | Approval |

Reasons for this order:

- **Writers are serial.** Passes 1 and 2 regenerate shared outputs such as
  CONTRACT stamps and `public.json`, and the checkout allows one writer.
- **Probes P1–P3 follow Pass 2.** They test the corrected statements, not
  the ones the worklist already marks false.
- **P4 precedes Pass 3.** Pass 3 narrows credited claims, and the test-only
  readers inform what to narrow.
- **Answer keys are committed before probes run.** The key commit precedes
  the workflow, so grading cannot drift toward what readers said. This is
  the repository's rule that predictions precede attempts.
- **The prune apply comes last.** Pass 3 runs new reader rules over the live
  envelopes in `product-group-default`, and the probes read retained runs.

## Agent logistics

| Role | Model | Count | Sees | Produces | Runs through |
| --- | --- | --- | --- | --- | --- |
| Writer W1–W3 (W4 if needed) | Opus | one per pass, serial | full checkout; the brief below | commits, ledger rows, report | Agent tool |
| Reviewer V1–V3 | Opus | one per pass | the pass's diff and the source; not the writer's report or coordinator conclusions | findings, each tied to file and line | Agent tool |
| P1 envelope interpretation | Sonnet ×3, Opus ×1 control | 4 | about ten envelopes inline, and `docs/RESPONSE.md` as the only file it may read | per envelope: what happened, what is established, what cannot be concluded | workflow, 4 agents |
| P2 spec-only oracle | Sonnet ×3, Opus ×1 control | 4 | four to six contract subjects inline, each with constructed inputs | a predicted outcome per input, with the sentence it rests on | workflow, 4 agents |
| P3 restatement comparison | Sonnet | at most 8, one per rule and owner file | one owner file | every claim that file makes about the named rule | workflow, at most 8 agents |
| P4 test-only reading | Sonnet ×3, Opus ×1 control | 4 | about eight tests or checkers inline, without product code or the credit text | per test: what it establishes and what incorrect behavior it rejects | workflow, 4 agents |

Each workflow stays under this session's guideline of fewer than ten agents.
The Opus control sees exactly what its Sonnet peers see.

Probe material:

- **P1 envelopes** come from retained runs. Categories:
  - a permission-shaped failure;
  - `validator_unavailable`;
  - an ordinary fallback capture;
  - an actor request with `policy_check: null`;
  - truncated or non-UTF-8 exec output;
  - a `captured` receipt and an `unavailable` one;
  - an `unknown` cleanup trigger;
  - a `query_first` order;
  - a refused experimental control.

  Selected envelopes are copied into the probe records, so the prune apply
  cannot remove them.
- **P2 subjects** include the validator byte rule (R9), the reply guard rule
  (R8), unfollowed imports (R12), registry loading (R2) and exec stream fields
  (R1). Inputs come from existing independently authored rows, such as the
  reader corpus, `failure_boundaries` and `cli_contract.rs`, so the key needs
  no new execution.
- **P3 rules:**
  - fallback eligibility and the presence of `policy_check`;
  - the derivation of `cleanup_trigger`;
  - what a `captured` receipt implies.
- **P4 targets** are the Part 3 entries that narrow a credited claim, plus
  credited tests in the suites Part 3 touches.

## Constraints

- **Readers.** Material is given inline, plus at most the one named file. A
  reader is told not to open anything else and to list every file it opened.
  A reader that opened another file is excluded from comparison, because the
  constraint cannot be enforced by tools. No reader sees an answer key, the
  worklist, the review or another reader's output.
- **Keys.** The coordinator writes them from source and from existing checker
  expectations. They are committed before the workflow starts, and the key
  commit is recorded beside the results.
- **Adjudication.** A lead becomes a Pass 4 entry only if source shows that
  the statement is false, or that it omits a scope condition that changes a
  conclusion someone would act on. Otherwise its destination is the
  user-duty draft, a guide-rewrite note or none. Weighting:
  - one Sonnet disagreement alone counts as weak;
  - a misreading the Opus control shares points to the text or the constraint;
  - disagreement among readers under one constraint marks ambiguity.
- **Writers.** The brief below applies. Parts 1 and 2 must not add workflows,
  examples or explanation to shared regions. Optional worklist entries are
  taken only where `DISPOSITIONS.md` selects them.
- **Reviewers** compare each changed statement row by row with its producing
  code: omitted conditions, branch order, mappings, and absent versus null.
  A passing generator check is not evidence of meaning.
- **Power.** AC power with the lid open. A run that overlapped sleep is
  repeated in a new directory and is not a run of record.

## Writer brief

The root, `docs/`, `tests/`, `controller/` and `runner/` `AGENTS.md` files
govern, along with the management plan's "Guide freeze and public
commitments" and "Verification sequence".

1. Triage every entry first. Read the current text and the producing code.
   The proposed wording dates from `837296af`. Edits state current behavior
   after R1–R14, not the worklist's text. Contradictions are listed, not
   edited.
2. Keep one ledger row per entry: entry, claims, status, reason, commit.
   Write it to `.tmp/trace-integration/accounts/ledger-pass<N>.md`. The
   coordinator reviews it and commits it into `records/`.
3. Edit generator inputs only, regenerate in the worklist's order and review
   every generated diff. Run every generator's `--check`. Confirm that
   `docs/build_contract.py` still prints
   `development:0c8497126cab848b4faf781d891010a06f7510dea903d6bea546afb7d09b18b1`.
4. Commit by owner group on `main`, naming the DT identifiers in each body.
   Use the trailer the coordinator supplies. Never use `git add -A`, and
   never touch `records/`.
5. Run tests only through `tests/run.sh`, each with a fresh
   `PW_TEST_OUT_DIR=tests/out/runs/<name>`. A failure stays a failure: find
   the cause and use a new directory name.
6. Report:
   - the four counts and the contradictions;
   - statements that cannot be made true without a product change;
   - build-input entries;
   - runs of record, with sleep and failures.

| Pass | Verification on the final tree of the pass |
| --- | --- |
| 1 | `--suite source_drift`; `--case preflight/build_entry_controls` |
| 2 | `--suite source_drift`; `--suite unit --suite integration` (`unit/rust.unit` compiles `docs/limits.json`) |
| 3 | The suites owning each changed reader or control. Every new reader rule needs an accepted control and a rejected neighbour, and is run over the retained `product-group-default` envelopes. Also the opt-in `runner_unit/actor_handoff_mutations` and `--suite source_drift` |

## Records

- `records/trace-assessments/ACCOUNTS-LEDGER.md` holds the per-entry status
  and is committed after each pass.
- `records/trace-assessments/probes/` holds each probe's prompts, copied
  inputs, answer key, raw answers and adjudication table.
- The management plan gets a dated progress entry after each pass and after
  the probes.

## Closing prune

Once every result is committed, `make prune` previews the cleanup. The apply
deletes every development run, including `product-group-default`, the
pre-change runs and every run this step produces. The probe inputs survive
because they are copied into records. Approving the apply also amends the
management plan's statement that no further apply is intended in this stage.
Step 4's integrated verification then produces the evidence the outflows rest
on.

## Approval

Edit the boxes. A workflow also needs your go-ahead in conversation.

The maintainer approved items 0–6 in conversation on 2026-11-19 and asked
for work to stop on reaching item 7. The probe workflows' go-ahead was given
in the same message.

- [x] Phase 0, coordinator setup
- [x] Pass 1, W1 and V1
- [x] Pass 2, W2 and V2
- [x] Answer keys committed before probes
- [x] P1 envelope interpretation (3 Sonnet, 1 Opus)
- [x] P2 spec-only oracle (3 Sonnet, 1 Opus)
- [x] P3 restatement comparison (at most 8 Sonnet)
- [x] P4 test-only reading (3 Sonnet, 1 Opus)
- [ ] Optional, not proposed: a Haiku reader added to P1 and P4
- [x] Pass 3, W3 and V3; Pass 4, W4, if adjudication accepts entries
- [ ] Prune apply at close
