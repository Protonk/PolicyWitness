# Draft: one account of a run's result in the guide

A proposal for review. It changes nothing: `docs/PolicyWitness.md` is as it
was. It answers the maintainer's request of 2026-11-10 for a moderate
consolidation around the guide's output-envelope introduction, recorded as
register row `R-33` in `records/contract/CONTRACT-LEDGER.md`. Sibling
artifacts are named by path without links, under the records link rule.

**Use.** Stage four of `docs/CONTRACT-STAGING-PLAN.md` applies this draft
against the settled contract. The placement follows the maintainer's
direction recorded in `R-33`, and the maintainer reads the result with the
settled contract before the final checkpoint. "Open points" at the end says
who settles each.

The behavioral question in row `R-20` stays open. The draft text describes
what the product does now, so that the behavior can be judged. Sentences that
would change if `R-20` were decided the other way are marked **[R-20]**.

`G:N` below is a line of `docs/PolicyWitness.md` at commit `a7d9b320`.

## What is scattered now

One ordinary result is explained in five places, none of which states the
whole relationship.

| Lines | Under | Says |
| --- | --- | --- |
| G:1218-1229 | "Shape and producer contract" | What the reply projection holds and what the envelope's `result` and `data` carry. |
| G:1275-1287 | same section, after about forty lines on `runner_subprocess` | The controller's projection into `data.runner_sandbox_diagnostics`, ending "These fields do not change `normalized_outcome`." |
| G:1289-1294 | same section | Reporting failure: `runner_reporting_failed`, `evidence_retained`, omitted comparisons. |
| G:2024-2031 | "normalized_outcome catalog", about 730 lines later | What `finished` means, and that it gives `result.ok: true` and exit 0. |
| G:2040-2041, G:2094-2109 | same catalog | `runner_reporting_failed` again; exit 1 for timeouts; the controller's own outcomes, with a pointer to the controller README. |

The controller README states the relationship directly in two sentences:
status follows the admitted runner outcome and the reply is left as received;
the controller separately validates the carried evidence before projecting
its findings. The guide has no equivalent sentence.

## Proposed placement

Order of the guide after the change, from the "Output envelope" heading:

1. **Output envelope** introduction (G:1209-1213), unchanged.
2. **Reading a result**: new heading; the consolidated account below. It
   absorbs G:1218-1229, G:1275-1287, G:1289-1294 and the `finished` entry
   at G:2024-2031. Those passages are removed from where they are now, not
   repeated.
3. **normalized_outcome catalog** (G:2017-2109), moved up to follow the
   account directly. Its `finished` and `runner_reporting_failed` entries
   shrink to one line each that points at the account. The rest of the
   catalog, the client-failure paragraph and the timeout table are
   unchanged.
4. **Worker and host records**: new heading for the detail that stays:
   process identities (G:1234-1237), `runner_subprocess` (G:1239-1254), the
   host facts and the disposition record (G:1256-1273), optional objects and
   exec fields (G:1296-1309). Unchanged text.
5. **Top-level fields** (G:1314 onward), unchanged.

What does not move: descriptions of native observations, lifecycle records,
comparison records and individual attempt kinds stay in their sections. The
account refers to them.

### What the placement does to contract surfaces

The guide's text sits in hashed regions, so placement is also a statement
about surfaces. Three things follow while the guide's regions are part of
the surfaces' definitions. Stage one of the staging plan takes them out.
From then on moving this text moves no stamp, and none of the three needs a
decision.

- The catalog is the guide's `refusals` region. A region is found by its
  markers, wherever they are, so the region can move with its text. Moving
  it changes no hash; shortening two of its entries does.
- The account would sit in the guide's `envelope` region. Today that region
  also holds the `runner_subprocess` and disposition detail, which the
  report notes belongs to `lifecycle` by subject. For the catalog to follow
  the account directly, that detail has to leave the `envelope` region. The
  natural home is the `lifecycle` region, which begins immediately after.
  That moves text across a region boundary: the `envelope` surface's
  definition shrinks and the `lifecycle` surface's grows. The `equipment`
  surface also hashes the guide's `lifecycle` region.
- So `envelope`, `refusals`, `lifecycle` and `equipment` would all read
  `unreleased` after this change.

### Links that need attention

- `#output-envelope` is linked from `controller/README.md` and
  `runner/README.md`. The heading stays.
- `#shape-and-producer-contract` is linked once, at G:1487, as "the worker
  disposition record". That link would point at "Worker and host records".
- `#normalized_outcome-catalog` is linked at G:2309. The heading stays.
- None of these passages is inside a copied or generated region, and none
  carries a generated span.

## Proposed text

Everything from here to "What each statement rests on" is the text proposed
for the guide.

### Reading a result

`policy-witness run` prints one envelope. Three parts of it answer different
questions, and each is supplied by a different component.

| Part | Supplied by | What it is |
| --- | --- | --- |
| `data.runner_result` | The runner host | The host's report of the run: its `normalized_outcome`, each step's query, attempt and comparison, the phases, and the worker records. The controller publishes the report as it received it and changes none of its fields. |
| `data.runner_sandbox_diagnostics` | The controller | The controller's findings about the evidence in that report: what it concludes about how the worker ended, and whether the report's records agree with the facts they cite. |
| `result` and the exit status | The controller | One classification of the whole run: `result.normalized_outcome`, `result.ok`, `result.error`, and the status `policy-witness` exits with. |

Beside these, `data` carries the specimen dossier (`specimen`), the client
transport (`runner_client`), the fallback compilation (`policy_check`) and
`timeout_ms`. A report is readable on its own: it carries its `producer`
context and the policy identity (`specimen_id`, `policy_format`,
`policy_sha256`). The controller reads a report only after its
`producer.contract` matches the controller's own
(CONTRACT.md (link: `CONTRACT.md`)).

#### What success means

`result.ok` is true and the command exits 0 in exactly one case: the
controller admitted the host's report, and that report's
`normalized_outcome` is `finished`. For an admitted report the controller
does not form an outcome of its own. It copies the host's into
`result.normalized_outcome`. **[R-20]**

`finished` is the host's statement that the execution completed and was
collected. Worker completion and clean disposition are confirmed. Any
invoked validator also has confirmed clean disposition, valid received
records for every requested step ID, and no transport, decoding or
association failure. Uniquely associated per-step diagnostics retain their
per-step semantics.

`finished` says nothing about what the specimen's operations did. An
attempted operation can succeed or fail in a finished run, and a denied
`open` is an ordinary finished result. Read each step's `attempt` and
`comparison` for that (reading a comparison record (link: `#reading-a-comparison-record`)).
Success therefore means that the harness ran the specimen to completion. It
does not mean that any attempt succeeded, and it does not mean that the
controller found the reported evidence consistent, which is the next
subject. **[R-20]**

Every other outcome gives `result.ok: false`. The command exits 1 for any
other host outcome, for a report the controller refused, and for a client
transport outcome. It exits 2 for `tool_error`, which means the controller
could not carry out the run. The [catalog](#normalized_outcome-catalog)
below lists the outcomes.

#### How the controller's findings qualify the report

After admitting a report the controller checks its records against one
another, and writes what it finds to `data.runner_sandbox_diagnostics`:

- `process_disposition`: how the worker ended, as far as the records
  support it: `no_worker`, `unconfirmed`, `clean_exit`, `nonzero_exit`,
  `signaled`, `conflicting`, `withheld` or `unrecognized`.
- `termination_cause`: host cleanup that the disposition record witnesses
  end to end (`host_sentinel_deadline`, `host_exit_grace_exhausted`,
  `host_cleanup_after_wait_error`, `host_cleanup_after_transfer_error`). It
  is null for a confirmed clean exit and `unknown` for every other
  termination, including a self-signal and an unresolved or conflicting
  status.
- `stop_reason`: why the host stopped polling. A deadline can coexist with a
  clean exit.
- `disposition_integrity` and `disposition_issues`: whether the report's
  records agreed with the raw facts they cite. `valid`, or `invalid` with
  one issue for each finding.

When a check finds a contradiction, `disposition_integrity` is `invalid`,
`process_disposition` is `withheld` and `termination_cause` is `unknown`.
Withheld means the controller declines to state the conclusion. Nothing is
removed: the host's report in `data.runner_result` is unchanged, including
the field the finding contradicts. A gate the host reported as `satisfied`
still reads `satisfied` there.

These findings do not enter `result` or the exit status. **[R-20]** One
envelope can therefore show all of these together:

- `data.runner_result.normalized_outcome: "finished"`: the host reports a
  completed, collected execution;
- `result.ok: true` and exit 0: the controller classifies the run by that
  outcome;
- `data.runner_sandbox_diagnostics.disposition_integrity: "invalid"`, with
  the disposition withheld: the controller found the report's evidence
  inconsistent with itself.

Read the combination as it stands: the run completed, and the evidence it
returned does not hold together. A consumer that needs consistent evidence
checks `disposition_integrity` as well as `result.ok`. **[R-20]**

The diagnostics object is present only for a report the controller
admitted. The worker and host records (link: `#worker-and-host-records`) describe
the raw fields and the disposition record these findings are drawn from.

#### What a reporting failure preserves

If the host cannot encode the result it assembled, it reports
`runner_reporting_failed` in its place, with `rc: 1`, an `error`, and a
`reporting_failure` object holding its diagnostic and a summary of the
original result. `result.ok` is false and the command exits 1.

What survives depends on `reporting_failure.evidence_retained`:

- **true**: queries, attempts and child observations survive. Every
  `comparison` is omitted. Retained ordering observations are diagnostic;
  this report certifies no per-step order.
- **false**: encoding the reduced report failed as well. The host sent a
  minimal report with no steps and no subprocess evidence.

The controller checks a reporting-failure report for the form of the
degradation: the outcome, the diagnostic, the absence of comparisons, and
the absence of evidence when none is said to be retained. It does not run
the consistency checks of the previous section on the observations such a
report retains. Treat them as the host's unexamined observations.

#### When no host report was admitted

- **The controller refused the report.** `unsupported_runner_response`
  means the report names another build's contract or was written under
  another record schema. `malformed_runner_response` means the bytes were
  not one complete typed record, or the decoded record failed admission.
  `data.runner_result` holds the decoded report when decoding succeeded and
  is null otherwise. There is no diagnostics object, and nothing is
  concluded from the report.
- **No report arrived.** The client outcomes in the catalog below
  (`xpc_error`, `xpc_timeout`, `xpc_acquisition_failed`,
  `xpc_submission_refused`) and a missing, malformed or unsupported client
  capture leave `data.runner_result` null. The client never manufactures a
  host report.
- **The run could not be carried out.** `tool_error`.

### normalized_outcome catalog

`data.runner_result.normalized_outcome` values the runner can produce (for
the standalone helper's `bad_request`, `policy_too_large`, `setup_error`,
`compile_error` and `ok` outcomes, see SBPL check (link: `#sbpl-check-sbpl-check`)):

- `finished` — the execution completed and was collected; see
  [What success means](#what-success-means).
- `runner_timeout` — *(entry unchanged)*
- `runner_failed` — *(entry unchanged)*
- `runner_reporting_failed` — the host could not encode its assembled
  result; see
  [What a reporting failure preserves](#what-a-reporting-failure-preserves).
- *(the remaining entries, the client-failure paragraph, the timeout table
  and the closing paragraphs are unchanged)*

## What each statement rests on

Grades are the plan's. "Source read" is by the coordinator on 2026-11-10
unless marked.

| Statement in the draft | Rests on | Grade |
| --- | --- | --- |
| `result.ok` and exit 0 follow the host's `finished` outcome alone | `controller/src/run_flow.rs`, `complete_execution` | Source read |
| Success, an invalid integrity finding and a withheld disposition can coexist; the report is published unchanged | A controller unit test in `run_flow.rs` that asserts exit 0 with `disposition_integrity: "invalid"`, `process_disposition: "withheld"`, `termination_cause: "unknown"`, and the report round-tripping equal | Test read; the case `unit/rust.unit` passed in run `tests/out/runs/contract-c243`, which is local and disposable |
| A contradiction sets `invalid`, `withheld` and `unknown` and appends issues | `controller/src/porcelain_admission.rs`, `execution_diagnostics` | Source read |
| Exit 1 for a refused report and for client outcomes; exit 2 for `tool_error` | `run_flow.rs`: the admission match and `tool_error_envelope` | Source read |
| A refused report keeps its decoded record; no diagnostics object | `run_flow.rs`: the comment and `execution_only` | Source read |
| The meaning of `finished`, the field vocabularies, the reporting-failure description | The guide's present text at G:1275-1294 and G:2024-2041, carried over | Not re-derived |
| The host's reduced and minimal reports | `runner/Sources/PWRunnerCore/PWRunnerService.swift`, `pwRunnerReportData`, read as far as the second encoding attempt | Source read, partial |
| The controller checks a reporting-failure report for form only | `execution_diagnostics`, the `reporting_failure` branch; the unit test above shows no `phase_collection` issue for a degraded reply; the report's finding `F-07` | Source read, partial; the full list of checks skipped was not enumerated |
| `unsupported_runner_response` and `malformed_runner_response` causes | `controller/README.md`, "Output contract" | Document read, not traced |
| A denied `open` is an ordinary finished result | The guide's present statement that attempts can fail in a finished run | Illustration; not tied to a named case |

## Open points

1. **R-20.** The maintainer's. The draft makes the present combination
   readable in one passage. It does not argue for keeping it. Until the
   maintainer rules, the marked sentences stand as written.
2. **The region moves.** Settled by stage one, which takes the guide's
   regions out of the surfaces' definitions. Before that, the question was
   whether `runner_subprocess` and disposition detail may leave the
   `envelope` surface for `lifecycle`, and whether four surfaces reading
   `unreleased` is acceptable for this change.
3. **Per-actor findings.** The executor's, in stage four. The draft does
   not yet describe the actor
   form. Read since: in the actor form the top-level `process_disposition`
   is `per_actor`, a value the guide's present list omits and this draft
   copied without; each actor has its own entry; the top-level integrity
   is `valid` only if every actor's is; and a reply-level finding sets the
   top level to `withheld` without changing the per-actor entries. The
   ledger's section "Withholding, as implemented" has the detail (`R-34`,
   `R-35`). The paragraph describes that scope as implemented, which is
   kept until the maintainer rules on `R-34`.
4. **The contract's own passages.** The executor's, in stage one. C:165
   and C:351-355 state the same
   relationship more briefly (`R-07`, `R-19`). They should be rewritten to
   agree with this account, and that is not drafted here.
5. **"Controller" and "host" as the guide's words.** The executor's, in
   stage four. The draft names the
   component that supplies each public assessment and uses no function
   names. Whether the guide's reader already has those two words, from its
   earlier sections, has not been checked.
