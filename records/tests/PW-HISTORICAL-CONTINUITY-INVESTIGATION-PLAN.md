# Historical continuity obligations in tests: investigation plan

## Question and intended result

Determine whether a specific test, assertion, fixture or supporting procedure
can be reduced or removed so that PolicyWitness stops maintaining a historical
continuity obligation. Deliver findings and supported reduction proposals in
`records/tests/PW-HISTORICAL-CONTINUITY-INVESTIGATION-REPORT.md`. This plan
authorizes an investigation and that report, not implementation changes.

The author establishes this intention for the investigation: **PolicyWitness
disclaims responsibility for historical interpretation. Using earlier PW
releases, interpreting their outputs, and determining how those observations
relate to later behavior are research problems for the user.** This is a stated
intention, not a finding that the implementation and repository already express
it. Identify any conflicting current document or executable obligation precisely;
do not silently resolve that conflict in favor of the premise.

The intention includes continuity between earlier and current releases that
share a wire-format version. Format admission and responsibility for historical
interpretation are separate questions: older bytes may satisfy every current
admission rule without establishing a promise to explain their original meaning
or their relationship to later observations. Conversely, the disclaimer does
not authorize rejecting otherwise admitted input because of its age or silently
changing a versioned meaning. Identify any current obligation to interpret such
input and treat a proposed narrowing as a conditional contract change.

Retained historical evidence is not itself a removal target. Observations and
comparisons can remain useful for establishing whether behavior changed without
requiring old interpretations, old releases or their readers to remain usable.
Investigate the additional maintenance responsibility actually imposed by current
checks. A small or zero-candidate result is valid.

## Evidence and operating boundary

Follow the [planning guidance](../../CONTRIBUTING.md#planning-a-change),
[record guidance](../AGENTS.md) and [test guidance](../../tests/AGENTS.md), with
the owning controller or runner guidance when following those sources.
Read the [test work survey](TEST-WORK-SURVEY-REPORT.md) and
[expectation authority report](TEST-EXPECTATION-AUTHORITY-REPORT.md). Treat them
as starting evidence, not a substitute for checking selected claims against
the revision being investigated. Both describe source revision
`31b81951c9c8c4124089aa4dd342b2b63c0a86de`.

This is a narrow, read-only investigation. Preserve preexisting work. Write only
the requested report in the checkout and keep investigative scratch outside it.
Do not change product code, tests, fixtures, catalogs, contracts, configuration
or historical records; do not delete, rewrite, migrate or regenerate retained
evidence. Use Git and file reads, static parsing and demonstrably non-executing
discovery. Do not run tests, build earlier releases, launch native experiments,
install services or prune artifacts. If a material conclusion requires execution,
state the smallest observation that would settle it and mark it unverified.

Do not reopen test-execution consolidation, design a taxonomy, decorate tests,
divide release and non-release work, or repair unrelated findings from the
preceding surveys. This is neither a general duplicate-test review nor a complete
compatibility audit or inventory of old material. Stale prose alone does not
establish an executable historical obligation.

## Investigation sequence

### 1. Establish the examined state and screen the existing accounting

Record the full examined commit, branch and working-tree condition before
interpreting sources. Distinguish committed contents from any relevant local
changes without altering either. Check intervening changes from the surveys'
source revision to the examined state, following renames and changed readers
where they affect a lead. If relevant files change during inspection, identify
which snapshot supports each conclusion rather than combining them silently.

Use the work survey's population accounting, including batch and nested-fixture
coverage, to locate plausible dependencies. Do not repeat its complete assertion
survey. Read the relevant current contracts, especially
[wire admission and stored evidence](../../docs/CONTRACT.md#supported-versions)
and the [evidence contract](../../tests/FAILURE-PROPAGATION-CONTRACT.md), before
calling a historical-looking input compatibility work.

### 2. Resolve the four starting leads

Investigate each lead without presuming that reduction is warranted. Follow
actual readers, assertions, callers and generation or refresh procedures, along
with nearby dependencies that could change the assessment. Consult history only
far enough to separate original purpose from continuing justification.

**Comparison matrix and earlier producer.** Start with work survey §2.15,
the [comparison fixture account](../../tests/fixtures/comparison/README.md) and
its [response-12 baseline](../../tests/fixtures/comparison/baseline_response12/README.md).
Trace consumers of the stored outputs, match receipts, specimens and matrix,
including current live and constructed-input readers and any regeneration path.
Establish whether the earlier producer is provenance, an actively checked
reference, a regeneration dependency or another kind of dependency. For any
expectation claimed to depend on it, determine whether agreement with that
producer is its sole authority or whether a current rule and supporting
controls justify it independently. Separate storing the receipts from requiring
them to remain interpretable or reproducible.

**Disposition known-loss capture.** Start with authority report §6 and the
[disposition fixture account](../../tests/fixtures/disposition/README.md).
Trace every current consumer of `a1_known_loss.json`, including the controls in
`tests/suites/blackbox_e2e/disposition_controls.py` and their admission readers.
Identify the first decisive check and whether any historical content is read
beyond that boundary. Assess whether the capture's particular content or
authenticity contributes to the current check, and what a smaller independently
constructed input would lose. Compare that work with current-format controls
for missing records and lost semantic information. Version rejection is not,
by itself, support for historical interpretation.

**Setup-oracle counterexample.** Start with authority report §2, work survey
§2.5 and the [suite's sensitivity account](../../tests/suites/runner_unit/README.md#host-setup-oracle-sensitivity-opt-in).
Trace `host_setup_oracle_sensitivity.py`, the copied
`host_setup_controls.py` recipe/checker, fixture instrumentation and their
callers. Determine what current work is supplied by requiring the copied
checker to accept the wrong variants, and whether that requirement carries an
earlier investigative result forward as an obligation. Assess the acceptance
expectation separately from independent observations, correct baseline checks,
negative controls and fixture cleanup. A source substitution becoming invalid
does not alone establish an obligation to preserve a past checker weakness.

**Former red-test wrappers.** Start with work survey §2.4, authority report §6
and the [unit suite account](../../tests/suites/unit/README.md#invariants).
Trace `tests/suites/unit/disposition_reds.sh` and `byoxpc_reds.sh`, their catalog
selection, exact Rust test names, expected-message classification and wrapper
controls. Establish whether the classifications still provide useful present
evidence or maintain distinctions justified only by a completed transition.
Evaluate wrapper machinery separately from the underlying regression
assertions. Verify any claimed remaining execution route and its assertions;
shared test names or apparent duplication are insufficient grounds for removal.

### 3. Conduct a brief wider screen

Perform a bounded repository-wide text screen of tracked active tests and
maintenance procedures, not only dependencies reachable from the four leads.
Include tests embedded in controller and runner sources, shared fixtures and
readers, generators, build/release scripts, workflow definitions and their owning
documentation. Exclude investigation records, archives, retained run outputs,
vendored sources and build outputs from the initial search population; follow
references into historical evidence only when an active dependency warrants it.

Use the survey's accounting to interpret hits, including historical-format
handling inside batches. Searches for `legacy`, `baseline`, `version`, `golden`
and `red` can locate material; names and age are not findings. Read hits far
enough to identify an active consumer or required procedure. Add a serious
candidate only when that evidence points to a concrete historical obligation;
do not reconstruct every matching test or procedure.

Record search locations, exclusions and terms, leads selected for deeper tracing,
and what remains unexamined. Depth remains limited to the four required leads,
additional direct candidates and their material dependencies. Completing this
screen does not establish repository-wide absence. Do not expand into a full
compatibility audit or keep searching to obtain a positive result.

### 4. Establish the obligation and test the interpretation

For each serious candidate, put the decisive chain in the report: input or
fixture, reader or procedure, decisive assertion, and contribution to the case
or procedure's result. Identify what must remain true, which component or
observation it concerns, and why that expectation is currently demanded.

Name the concrete maintenance burden. It might require an obsolete decoder,
translation of historical captures, continued authority for old answers,
reproduction of a past checker weakness, or operation of completed migration
machinery. Alternatively, the item may merely retain an observation and impose
none of those responsibilities. Identify actual consumers and requirements,
not a hypothetical inconvenience.

For each alleged burden, first consider a concrete change to the implementation
that still satisfies its present obligations. State exactly what would then fail or
need maintenance and why. Distinguish a historical obligation from a useful
regression alert, an invalid mutation anchor or a changed experimental
prerequisite. If the historical responsibility is itself a current contractual
obligation, say why removing it cannot pass that test unchanged.

The report may recommend a conditional contract change, rather than only naming
the conflict. Identify the exact rule or promised behavior to narrow, affected
callers and readers, and any versioning or admission implications. Explain how
the change serves the stated intention and what decision it requires. Separate
reductions consistent with current contracts from those contingent on changing
them. Leave unresolved intent unresolved; neither the premise nor a proposal
authorizes the contract change or its implementation.

Apply these distinctions at assertion or helper level where a case mixes work:

- Historical origin does not confer historical authority. An old regression
  can protect a current promise; a current-format fixture derived from an old
  observation need not support the original release. Conversely, an expectation
  can preserve a past limitation without executing an old binary.
- Refusal is not compatibility. Exact-version admission, ABI identity checks,
  unsupported-format rejection and withholding unsupported facts can protect
  current boundaries. Current producer/consumer agreement and phases within one
  run are not cross-release continuity either.
- Storing an observation, maintaining a route to observe a new execution and
  requiring that execution to reproduce the old result are different duties.
  Neither a capture's age nor a previously green result decides among them.

### 5. Assess the smallest supported reduction

For each proposal, identify the exact assertion, input, wrapper, reader,
regeneration step or whole case affected and the responsibility that would
actually disappear. Renaming, making a case opt-in or moving material to an
archive does not remove a responsibility while current checks still require
maintenance or execution.

Account for current-contract assertions, independent observers, negative
controls, artifact identity and provenance checks, cleanup, shared consumers,
and evidence-capture or comparison routes. Trace claimed remaining coverage to
concrete assertions and callers. State any lost observation, evidence or
experimental capability explicitly; do not call a reduction coverage-neutral
when such work disappears.

Preserving every unique current diagnostic or experimental capability is not a
precondition for proposing a reduction. A proposal may recommend surrendering
one as an explicit tradeoff: name the unique claim or experiment lost, explain
why the historical maintenance responsibility removed warrants that loss, and
state whether any substitute exists. Present acceptance of that loss as a
decision, not as an already-approved consequence of the disclaimer. Loss of a
current contractual guarantee also requires the conditional contract proposal
above. Unrelated current coverage is not a removal candidate merely because it
would be convenient to eliminate it.

For a smaller constructed fixture, specify the properties needed to exercise
the intended boundary and the independent basis for its expected answer.
Do not obtain that answer by regenerating expectations from today's producer.
Describe the fixture in the proposal without implementing or generating it.

A proposal may deliberately surrender a historical service. It need not replace
that service with an archive, historical replay service, fixture migration
framework or continuing compatibility matrix. Make collateral losses and any
decision or unverified observation visible rather than inventing replacement
maintenance as a condition of reduction.

## Report, verification and stopping rule

Produce one compact report containing:

1. The examined revision, working-tree condition, inspection method, search
   boundary and material areas left unexamined.
2. Source-grounded findings for the four starting leads and any additional
   serious candidate. Include leads that do not justify reduction, explaining
   their current purpose or the absence of an active historical obligation.
3. Supported reductions, each naming the exact obligation removed, smallest
   affected surface, present work preserved, evidence or capability lost, and
   unresolved decisions or verification. Distinguish proposals within current
   contracts from conditional contract changes and identify decisions to surrender
   unique current capabilities. If none is supported, say so within the examined
   boundary rather than claiming repository-wide absence.
4. Consequential uncertainties, including precise conflicts with the author's
   intention and the smallest additional observation needed for any conclusion
   that static inspection could not establish.

Cite paths, symbols, decisive assertions and relevant revisions. Use the two
survey reports as context without reproducing their inventory. Keep the evidence
needed to assess each conclusion in the report, not solely in scratch material
or a session-local ledger; label any local-only evidence as such.

Before completion, check that every proposal follows from an active requirement,
that claimed remaining coverage is traced, and that losses and uncertainty are
explicit. Verify references against the examined sources, links and anchors,
canonical case IDs, and Markdown using static document checks. Confirm that only
the requested report was changed and that no tests, builds or native experiments
ran. Document any limit of verification instead of implying execution evidence.

Stop once the leads and their material dependencies are resolved sufficiently to
support a bounded recommendation or explain why none is warranted. Success is
a defensible account of whether PW can stop maintaining a specific historical
continuity responsibility, and exactly what stopping it would change.
