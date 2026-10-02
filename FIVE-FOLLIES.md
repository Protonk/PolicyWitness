# Five follies

Status (2026-10-01): the drift removal has landed. Of the five entries, none
shipped: `conditions.prediction_unavailable_pairs`, `comparison_conditions`,
`specimen.references` and `obligations.sandbox_attribution` were dropped from
the design, and `policy.imports.closure_sha256` ships as described in the
[guide's dossier section](docs/PolicyWitness.md#the-specimen-dossier). Of the
second-sweep findings, S1–S3, S5, S6 and S9 were implemented; S4, S7, S8 and
S10–S12 remain open ([DRIFT-REMOVAL-CANDIDATES.md](DRIFT-REMOVAL-CANDIDATES.md)
holds the adoptable ones). The text below is the review as written.

The drift-removal plan replaced one verdict with a set of records, and records
are easy to add. This document reports what happened when the whole of that new
surface was asked one question, after the question had already claimed a victim.

The victim was the proposed `target_mutation.steps`, the list of step IDs whose
attempts removed a query's submitted path. The plan had a producer emitting it,
an encoder checking it against the raw attempts, a consumer rederiving it from
the same attempts and comparing, and tests checking that defective lists were
rejected. No other use was specified. It was dropped from the plan at D6.42,
and the status was dropped later as well (S9 below): reading rule 6 of
[the failure contract](tests/FAILURE-PROPAGATION-CONTRACT.md#comparison-record)
states the interpretation and nothing ships.

Then the same question was put to every other object the plan added. The five
entries below are the first search's result, in the order they were examined —
including the last one, which came out clean. A list with nothing clean in it
would be a verdict, not a search, and would say more about the reviewer than
the plan.

**The question is not "is this derived."** D0 explicitly permits derived
descriptive fields, and most of what PolicyWitness reports is a derivation over
two channels. The operational question is: *what concrete task becomes harder
or impossible if this structure disappears?* Following producers and readers is
how to answer it. Operational decisions, independent test controls and useful
interpretation of stored evidence all count. Emitting a field and checking the
same derivation again does not, by itself, establish a task worth preserving.

The first four entries describe proposed fields, not implemented consumers.
Existing readers and the plan's promised readers must be distinguished. A task
that feeds `drift` or `comparison.conclusion` counts as a current use; whether
that task needs to feed the replacement is a separate review. This search marks
that dependency without assuming the answer or designing replacement code.

## 1. `conditions.prediction_unavailable_pairs`

The dossier's one backward glance. The controller reads the reply it just
received, collects every step carrying `query_plan:prediction_unavailable_pair`,
and reports the distinct `(operation, filter_kind)` pairs. The plan mentions it
four times, all definitional — the shape, the rule, and twice what it holds when
there is no usable reply.

The guide publishes the full exclusion set, and `source_drift` checks it against
`predictionUnavailableOpFilters` in `ProbeRunner.swift`, which holds three pairs
today. That is not the same set as the proposed field: this field reports the
subset encountered in one run. Its redundancy is with the per-step query
identities and limitations, not with the guide. Removing it makes a reader
collect and deduplicate those pairs; no further use is specified in the plan.

It is also the only dossier field computed from the runner's answer —
everything else is gathered before the runner is invoked. That single exception
is why D5 has to rule on what the dossier does with an unsupported reply.
Removing it makes the dossier purely pre-invocation, which is a boundary
statable in one sentence, while leaving the information in the steps.

## 2. `comparison_conditions`

A run-level object whose value space has exactly one member,
`{ "unestablishable": ["state_stability"] }`, with an encoder invariant that
rejects anything else.

It is not pure ceremony, and the distinction is worth drawing precisely: its
*presence* carries a bit — present beside `steps` on an ordinary reply, withheld
on both `runner_reporting_failed` levels — while its *value* carries none. So
the honest description is a one-bit field encoded as a nested object, plus a
checker for the constant. The bit is already recoverable from the reply's
reporting-failure state; it is not an independent observation. What remains is
the benefit of displaying a standing limitation in each stored reply. Whether
that task warrants the object and its duplicate checks is the open question.

## 3. `specimen.references`

Ten RFC 6901 pointers — the plan's example lists ten — from the envelope root to
the records the dossier does not own. The keys and values are fixed by envelope
5, "not computed from presence" — a pointer to a withheld or absent record is
still present. So the map is a constant, and the consumer "requires `references`
to carry exactly the fixed keys and values."

Zero bits, by construction. What it buys is orientation for a person opening a
stored envelope without the contract to hand, which is a real thing to want and
a reason to keep it. A wrong pointer would matter to someone following the
map, so constant content does not make its correctness unimportant. The
candidate is the repeated exact-set check: does consumer-side equality protect
a useful reading boundary beyond producer coverage, or only add another place
to edit when a path moves? Keeping the map and dropping that assertion is an
option, not a conclusion established by its zero information content.

## 4. `obligations.sandbox_attribution`

Its rule is a function of two things sitting beside it in the same object:
`observation`, and whether `limitations` contains
`exec_result_failed_after_spawn`. A reader holding the comparison record can
evaluate it with no knowledge the record does not already give them.

Its neighbour is the useful contrast. `runtime_target_identity` also looks like a
restatement, but its rule consults the mapped attempt filter, and that mapping
is producer knowledge — thin, but real, and the same kind of justification that
saved `target_mutation.status`. `sandbox_attribution` has no equivalent mapping
to supply. The proposed producer, encoder invariant and consumer all repeat its
rule.

There is a current reader beyond validation: `recover_evidence` in
[consumer.py](tests/lib/consumer.py) uses the existing
`sandbox_attribution_unestablished` limitation to construct `failure_groups`.
That reader was removed. No surviving operational use of the new status is
specified beyond field selection and checking; an explicit caution for a human
reader remains a possible justification. That benefit needs the same scrutiny
as the human uses that justify the reference map and closure hash.

## 5. `policy.imports.closure_sha256`

The one that survives, and the reason the criterion above is worth stating.

It hashes the applied source and successfully hashed import records. The source
bytes do not ship beside it: D2 explicitly omits them. A source hash cannot
substitute for those bytes when recomputing the closure hash. It is also the
only one of the five that exists today, as `policy_closure_sha256` in
`sbpl-check` output. The dossier reuses that algorithm for a separate
controller scan and preserves the helper's output on fallback paths; it does
not simply relocate one observation.

It survives because something does something with it. Two runs' closures compare
in one equality test, without diffing record lists — the cheapest possible answer
to "did these scans hash the same source and resolved import inputs?" The
[guide](docs/PolicyWitness.md#sbpl-check-sbpl-check) documents the sorted path/hash
records; the full framing, including the separator byte, is in
[`compute_closure_hash`](controller/src/bin/sbpl-check.rs). Recomputing still
requires the source bytes. Equality does not establish equal parameter values,
successful imports that were never observed, or completeness of a partial scan.
Its concrete use is comparison by a person or a diff; source searches found no
production reader making a decision on this hash. That distinction keeps the
retention argument honest without discarding the useful field.

## Also examined

Three more were looked at and left alone, for the record rather than for
balance. `binaries.*.manifest_*` duplicates data that ships inside the app, but
it is what explains a mismatch verdict and what keeps a stored envelope readable
without the app beside it. `library_identity.images[].on_disk` records disk-path
presence and, when possible, a file hash; shared-cache membership is a separate
observation. Disk presence does not establish that an override was loaded. D2
explicitly limits this record to host observations and makes no claim about
child mappings. The disk record remains useful when investigating such a
possibility. `policy.imports.records[]` is primary observation, not a join.

## Nearby findings

D3 says the controller's only production comparison reader is
`permission_failures_without_record`. In fact, `validate_disposition` in
[run_flow.rs](controller/src/run_flow.rs) also reads `comparison.limitations`
and checks the lifecycle entries against the disposition record. That reader
affects reported integrity findings. Consumer inventories must include
validation that feeds another output, not just selectors.

Two existing host-side helpers also warrant examination beyond new fields:
`runSandboxCheck` and `applySandboxPolicy`. Their call sites found in the source
tree are unit tests; production queries and sandbox application live in the
validator and C worker. Their dependency boundaries and test value are examined
in the second sweep below.

## Second sweep

This sweep covers existing runner helpers, step and subprocess projections,
comparison machinery, controller log evidence and the standalone policy helper.
It follows symbol and wire-key references through production code, Swift unit
tests, Python consumers, shell checkers, documentation and build wiring. These
are source findings, not removal experiments: no implementation was changed and
no build or live run was used to claim that a deletion is safe. Absence of a
reader means none was found in the active source tree; unknown external readers
are not ruled out. Stored evidence and release artifacts are not cleanup targets.

Each entry states the current task, the cost of losing the structure, and its
relationship to the drift plan. A validation reader is followed to its effect:
some checks merely compare duplicate representations, while others gate an
independent result. No present use is discounted because the plan might remove
its destination, and no proposed destination automatically earns its inputs.

### S1. The unused Swift attempt executor

**Implemented: removed with the host invariance rule.**
[`runAttempt`](runner/Sources/PWRunnerCore/ProbeRunner.swift) has no call site in
the source tree. Its private `runFileAttempt` and `runMachLookupAttempt` branches
implement file operations and Mach lookup, but production uses
[`pw_probe_runner.c`](controller/tools/pw_probe_runner/pw_probe_runner.c).
`observedPathForFd` in [PathUtils.swift](runner/Sources/PWRunnerCore/PathUtils.swift)
is called only by this unused file branch. No existing test calls `runAttempt`.
Removing this implementation would therefore take away no found execution or
independent test task.

Its surrounding file is not disposable. `validateSandboxChecks`,
`knownFilterKinds` and `predictionUnavailableOpFilters` have production callers.
Likewise, path canonicalization, parent resolution and firmlink resolution serve
the planner and later host observations. The separate `warmFirmlinkMap` function
has no caller; its comment prescribes warming before self-sandboxing, while the
current host never applies the specimen policy. Removing that unused entry
point would leave the actual lazy map and its readers intact.

There is already a misleading public consequence of keeping the unused branch.
`bootstrap_port_failed` is emitted only by Swift's `runMachLookupAttempt`, yet
the [guide](docs/PolicyWitness.md) and [coverage table](tests/COVERAGE.md)
attribute it to the C worker. The C worker writes an error string for
`task_get_special_port` failure; `buildAttemptResult` maps a nonzero Mach-lookup
slot to `lookup_failed`. The task here includes reconciling that documented
outcome with the actual producer, not just removing unused source.

### S2. A Swift query implementation tested only against itself

**Implemented: removed with the host invariance rule.**
[`runSandboxCheck`](runner/Sources/PWRunnerCore/ProbeRunner.swift) has four calls,
all in [PredictionUnavailableTests.swift](runner/Tests/PWRunnerCoreTests/PredictionUnavailableTests.swift).
All four exercise its exclusion branch. They verify a synthesized result from
this helper; they do not query the production worker through the validator or
exercise the helper's native-call branch. The same test file separately tests
the real `planValidatorQueries` planner, including exclusions and a different
operation on a known filter. Those tests have an independent production target.

The unused `currentProcessIsSandboxed` function is the other Swift caller of
the no-argument query shim. Together these functions account for all Swift calls
to [`PWSandboxCheckShim`](runner/Sources/PWSandboxCheckShim/PWSandboxCheckShim.c).
The shim has its own target in [Package.swift](runner/Package.swift) and is
compiled and linked by [build.sh](build.sh). Production prediction uses
`sb_api_validator`; removing this cluster would remove the task of testing an
unused query implementation and its build dependency. It would not replace or
remove the shared exclusion set or the planner controls. The helper, its shim
target and its build dependency are gone; the planner controls remain.

### S3. The Swift sandbox-application implementation and its tests

**Implemented: removed with the host invariance rule.**
[`applySandboxPolicy`](runner/Sources/PWRunnerCore/SandboxApply.swift) has six
calls, all in [SandboxApplyTests.swift](runner/Tests/PWRunnerCoreTests/SandboxApplyTests.swift).
The tests supply stubbed library functions and check this Swift helper's
messages, return values and resource cleanup. The test header, the
[runner-unit README](tests/suites/runner_unit/README.md), and the
[failure contract](tests/FAILURE-PROPAGATION-CONTRACT.md) already say it provides
no production C-worker failure-reporting coverage. No native experiment or
independent implementation comparison uses the helper. Removing it and its
exclusive `ApplyError` type would lose tests of that unused implementation.

The tests also serve as the C-function-pointer stubbing example in
[runner/AGENTS.md](runner/AGENTS.md). That contributor-documentation task would
need another example if the file disappeared; it is not a production reason to
keep a second application implementation.

Two nearby structures have current tasks and are outside this finding.
`computePolicyHash` is used by the service for source identity and structural
policy refusal. `SandboxLib.load` resolves symbols and can stop execution with
`libsandbox_unavailable`; the service discards its successful value but acts on
failure. The loader is therefore not dead merely because these function
pointers are otherwise invoked only by the unused apply helper. The loader
is gone and the host never loads libsandbox; S14 in the candidates document
records the distinction the check used to draw.

### S4. `attempt.lifecycle.boundary` and `.result`

**Duplicate evidence candidate, with a concrete reading cost; open.**
[`attemptLifecycle`](runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
copies `step_boundary_reached` and `step_result_published` from the corresponding
`runner_subprocess.disposition.steps[].questions` entry. These are entire claim
objects, including their basis or reason. Swift's `dispositionIntegrityProblems`,
Rust's `validate_disposition`, and Python's
[`check_record`](tests/lib/lifecycle_oracle.py) compare the copies with those
original claims. No separate operational use of the copied `boundary` or
`result` was found.

Those checks do have effects: a Swift mismatch can trigger reply degradation,
and a Rust mismatch makes `project_disposition` withhold its disposition and
cause. These are checks of duplicate evidence, but they are not inert. Removing
just the keys while keeping the checks would break real readers.

The useful task the copies serve is reading one attempt with its supporting
lifecycle claims at hand. Without them, a reader joins the step to the
disposition record. That convenience must justify the duplicated objects and
three implementations of their equality rule. The adjacent `summary` has a
different reader trail: the step builder uses it to append lifecycle limitations,
the Python adapter exposes it, and the FIFO deadline case reads it to distinguish
started and unreached attempts. This finding does not classify the whole
lifecycle object as unused.

### S5. Relation fields repeated as limitation strings

**Implemented: the record's `limitations` vocabulary carries no relation strings.**
[`comparisonEvidence`](runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
appends `operation:` plus `operation_relation` whenever that relation is not
`matched`, and `target:` plus `target_relation` whenever it is not
`same_submitted`. The resulting `operation:different`, `operation:unresolved`,
`target:different_submitted` and `target:unresolved` add no reason beyond the
neighboring relation fields.

Found readers assert their presence in classifier, checker and witness tests.
The current conclusion calculation reads the relation fields directly, not
these strings. Removing the strings would make a reader of the limitations list
also inspect those two fields. No production decision on the strings was found.
The distinct explanation strings, such as `compound_attempt`,
`broad_query_operation` and `submitted_target_unavailable`, are not covered by
this finding: they explain why a relation is unresolved. Nor does this finding
remove the relation calculation that currently feeds `conclusion` and `drift`.

### S6. `attempt.native_rc`, always null

**Implemented: `attempt.native_rc` is gone.** At the time of the sweep the
[step builder](runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift) explicitly
sets every attempt's `native_rc` to nil because ABI 7 carries PW attempt status,
not the syscall's native return. The API encodes that null when `result_source`
is present. Found tests require the null to prevent status from being presented
as a native result; no production branch reads the attempt field. A few
constructed Rust and Python log fixtures contain a nonnull attempt `native_rc`,
but they are not a producer of such evidence.

The concrete benefit is an explicit unknown in a uniform channel shape and a
reminder that `rc` is not a native syscall return. Removing it would require that
distinction to remain clear in the attempt contract. Its neighbor is different:
`sandbox_check.native_rc` carries actual validator returns and is consumed by
`eligibleOrderedPrediction` and `eligibleOrderedStep`. This candidate concerns
the attempt field alone; it does not imply that native-result provenance is
unneeded.

### S7. The observer's `deny_lines` list

**Strong duplicate candidate; open.** In both show and stream modes,
[`sandbox-log-observer`](controller/src/bin/sandbox-log-observer.rs) appends a
line to `deny_lines` exactly when it appends the parsed event to `deny_events`.
[`parse_sandbox_deny_line`](controller/src/log_show.rs) stores that same line in
the event's `raw_line`. The lists have the same order and membership, including
the bounded show path's event cutoff.

Source searches found construction, transport and a count assertion, but no
reader using `deny_lines` to make a decision or recover otherwise missing bytes.
Its human task is getting just the denial text without projecting
`deny_events[].raw_line`. Unlike the full `log_stdout`, it preserves no additional
non-denial context. The duplication is substantial enough that
[log_capture.rs](controller/src/log_capture.rs) explicitly names it in the
observer output-budget rationale. This is a candidate to remove a repeated list,
not a reason to discard raw lines from events or recompute the capture limits
without measurement.

### S8. Constant log disclaimers

**Presentation candidates; open.**
[`SandboxLogWindow`](controller/src/sandbox_log.rs) always emits four false
booleans: `event_timestamps_available`, `exact_run_membership`, `step_ordering`
and `pid_reuse_protection`. Rust and Python controls require those constants;
correlation does not branch on them. Their task is to put the same four limits
in every stored capture. This is the existing analogue of
`comparison_conditions`, and deserves the same human-reader test rather than
an automatic exemption for being shipped already.

The observer also emits `layer_attribution: { "seatbelt": "observer_only" }`
on its report paths. Its structure and literal have no reader found beyond
construction and test-fixture construction. The wording labels the observer's
role, but it does not report a varying attribution result. Removing either
representation would remove a local reminder; it would not change which log
records are selected. No proposed replacement representation is assumed here.

### S9. The whole-run target-removal calculation

**Current verdict use confirmed; replacement need deferred.**
[`reportsTargetRemoval` and `comparisonEvidence`](runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
scan the run attempts for a successful worker unlink of a query's submitted
path, subject to the query-exclusion guard. `ComparisonEvidence.conclusion`
uses `sameTargetUnordered` to prevent an allow/success pair from becoming
`agreement`, and `PWRunnerComparison.drift` projects that conclusion. The
consumer independently reconstructs the removal condition and enforces the
corresponding limitation and unavailable conclusion.

This machinery therefore has a concrete current task beyond checking itself:
it changed the verdict. The calculation was removed with the verdict; reading
rule 6 of the failure contract states the interpretation (S9 in the candidates
document). Whether identifying this confound warrants a producer-side run-wide
join was the later question
the present search leaves open. The current verdict use cannot establish the
answer for the replacement, and its impending removal cannot be used to call
the calculation dead today. The query guard's interpretation matters, but its
inputs are exposed in the reply; "producer knowledge" names a reading rule,
not an otherwise unavailable observation.

### S10. `partial_steps` and the lifecycle summary

**Weaker candidates than the copied claims in S4; open.**
`partial_steps` is `any(disposition.steps[].slot != completed)`, emitted by
[`buildWorkerSubprocess`](runner/Sources/PWRunnerCore/CWorkerOrchestrator.swift)
and checked by Swift, Rust and Python. It supplies no independent fact. But
live timeout, validator-failure, exec-lifecycle and isolation checkers use it to
ask whether all slots completed even when the run failed. The FIFO case uses
`summaries(view)` from [lifecycle_adapter.py](tests/lib/lifecycle_adapter.py) to
read the distinction between a started attempt and a later unreached one.

Without these summaries, those readers need an array scan or the lifecycle
claim interpretation table. They are convenience projections with concrete
scenario readers, not just equality controls. Neither is proof of effect, and
neither answers whether an operation was denied by the sandbox. Their value
does not depend on retaining a joint prediction/enforcement verdict. A later
cost review can still question their shape; this sweep does not establish that
they merely build and validate themselves.

### S11. `sbpl-check` parameter presence and count

**The simple duplication hypothesis is falsified.** On a scanned request,
`params_count` equals the length of `params_supplied`, which initially looks
like a disposable count. But [sbpl-check.rs](controller/src/bin/sbpl-check.rs)
uses `empty_param_diff` for unsupported formats, missing source and oversized
source: the name lists are empty while `params_count` still counts the submitted
map. A missing-source request with one parameter therefore reports count 1 and
an empty supplied-name list. `params_present` also distinguishes an empty map
from a missing or null map, all of which have count 0.

No downstream production selector for these two fields was found. Their
concrete task is retaining those submitted-request distinctions on stored helper
failures; deleting them loses information under the current shape. Whether that
distinction deserves reporting is separate from calling it a redundant list
length. The nearby `params_missing` has an even clearer use: it chooses
`missing_params`, exit 1 and the named diagnostic after compilation. The helper
surface was preserved; its output is unchanged.

### S12. Validator `records[].raw_line`

**Cleared by a concrete information-preservation task.**
[`decodeValidatorFrames`](runner/Sources/PWRunnerCore/ValidatorClient.swift)
keeps an accepted frame's text as well as projecting recognized fields into
`ValidatorVerdict`. Unknown JSON fields are not represented by those typed
properties. Removing `raw_line` would erase such fields and the received
spelling; the typed record cannot reconstruct them.

[DiagnosticTransportTests.swift](runner/Tests/PWRunnerCoreTests/DiagnosticTransportTests.swift)
and the [live diagnostic checker](tests/suites/witness_contract/check_diagnostic_transport.py)
actually parse the retained line to recover the fixture's extra diagnostic
content. These tests witness transport preservation of independently supplied
data, rather than validating a second derivation of the typed record. Retaining
the line has a task even without any drift or comparison verdict. Rejected
frame context is a different record and does not substitute for accepted bytes.

### S13. Log `candidate_step_ids`

**The closest-looking list has an operational reader.**
[`bounded_step_denies`](controller/src/sandbox_log.rs) emits both
`candidate_step_ids` and `matching_evidence`, whose records also contain the
step IDs. Nevertheless,
[`permission_failures_without_record`](controller/src/run_flow.rs) consumes the
ID list to construct the controller's list of permission-shaped failures lacking
a captured candidate. Python consumers also expose the associations, and log
controls check their relation to the evidence.

Removing the ID list would require that production reader to extract membership
from the matching records. This could be a later representation simplification,
but the list currently does more than build and validate itself. Its task is
log-coverage reporting, independently of `drift`. The matching records themselves
also retain which submitted operation and path forms admitted the association;
the submitted specimen is not embedded in the envelope, so they are not merely
decoration around the IDs.
