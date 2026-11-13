# Publication, preparation and admission boundary

A bounded investigation of three existing inputs: the specimen `example`
emits, the accepted `lesson create` input and the deliberately refused
`lesson capture_typo` input. It follows them through publication, controller
preparation and host admission, and stops before interpreting native execution.
It is not a four-pass cycle.

The passage, map, findings and hypotheses below were written from source at
`c9a7978d`, before any experiment or edit. The sections from
[Baseline observations](#baseline-observations) onward record what was then
observed, the bounded repairs and what remains open.

## Passage

| Stage | Decision and owner | Same for all three inputs? |
| --- | --- | --- |
| Publication | Controller. [example.rs](../../controller/src/example.rs) and [lesson.rs](../../controller/src/lesson.rs) each check arguments, refuse an empty or `unbound` identity, parse the embedded document with `parse_request`, insert the identity, run `validate_contract`, serialize with `to_string_pretty`, append one newline, then `write_all` and flush. `lesson` also checks its target (nonempty, absolute, UTF-8, no NUL) and writes it at two fixed operand positions. | Same mechanism in two separate implementations. Neither consults the host grammar. |
| Controller preparation | Controller. `run` in [run_flow.rs](../../controller/src/run_flow.rs) reads the file once, parses, gates identity, validates selectors, resolves augments, strips selection fields and holds one pretty serialization for the client. | Yes. None of the three carries a selector or augment, and the controller does not check closed field sets, so the misspelled member is delivered. |
| Host admission | Host. [PWRunnerRequest.swift](../../runner/Sources/PWRunnerCore/PWRunnerRequest.swift) checks `contract`, then root and nested closed objects while decoding; `admitSpecimen` in [ProbeRunner.swift](../../runner/Sources/PWRunnerCore/ProbeRunner.swift) checks capacity, then meaning. | No. `capture_typo` stops in decoding at `policy`. `example` and `create` continue to capacity and meaning; `create` carries a caller-chosen target subject to the 511-byte operand capacities in [limits.json](../../docs/limits.json). |
| After admission | Host, worker, validator. | Not followed here. Admission starts children; it establishes no query answer and no file effect. |

## Map as found

| | `example` | `lesson create` | `lesson capture_typo` |
| --- | --- | --- | --- |
| Promise and its owner | [emit_example](../../docs/contract/10-request.surface.md): exit 0 supplies the complete document "and the same build's `run` admits it"; every failure is exit 2 and stdout is discarded; no stability between builds. | [emit_lesson](../../docs/contract/10-request.surface.md): exit 0 is complete publication and "establishes neither admission nor an effect"; `run` independently admits or refuses; target preserved verbatim; no stability between builds. | The same rule, which adds that the input "deliberately includes an unknown policy field". The refusal's meaning for that member is owned separately by the [misspelling example](../../docs/contract/15-refusals.surface.md), which does not mention the lesson. |
| Conditions the promise leaves unstated | Which checks exit 0 itself performed; that admission is observed only when `run` reaches the host. | None promised. Acceptance additionally depends on the caller's target fitting host capacity. | None promised. |
| Who decides admission, and with what information | Host grammar. The emitting controller holds the constant and the identity only. | Host grammar and capacity, using the caller's target. The emitter deliberately does not inspect the target beyond its own usage rule. | Host decoder. The refusal precedes capacity, so it does not depend on the target. |
| Other presentations | CLI usage ("that the same build's run admits"), [controller reference](../../controller/README.md), [CONTROLLER](../../docs/CONTROLLER.md) origination and publication paragraphs, guide command-table row, extracted [contract example](../../docs/contract/10-request.surface.md) and the probes surface's step. | CLI usage, controller reference, [lessons README](../../controller/src/lessons/README.md), guide quick start, [REQUEST-GRAMMAR](../../docs/REQUEST-GRAMMAR.md). Absent from CONTROLLER and from the guide's command table. | The same, plus CLI usage "capture_typo is deliberately refused by run", the guide's and REQUEST-GRAMMAR's exact code and path, and the corpus row. |
| Checks on publication | `example.rs` unit tests; `cli_contract.rs` integration tests against the selected app and isolated Cargo builds. | `lesson.rs` unit tests; `cli_contract.rs` `lesson_publishes_both_inputs_from_the_installed_binary`, `lesson_cli_refusals_and_write_failures_exit_2_safely` and the isolated-build identity loop. | Same as `create`. |
| Checks on preparation | `run_flow.rs` `emitted_example_reaches_the_client_as_the_emitted_document`: exact callback string under the test identity. | None for the emitted document. | None for the emitted document. |
| Checks on host admission | Default `witness_contract/example_round_trip`: the selected app's emitted bytes submitted unchanged, admission and six one-change refusals observed. | Default `runner_outcome_bad_request/accepted_input_contract` and Swift `RequestContractTests`: a request materialized from the repository template by the Python or Swift loader, not the app's emitted bytes. Emitted bytes reach `run` only in opt-in `witness_contract/guide_workflows`. | Same as `create`, with the independently authored refusal in [examples.json](../../tests/fixtures/request_contract/examples.json). |
| Unproved | Exact bytes at the pipe and host receipt (stated in the owner's limits); a gate refusal on a bound build. | Default-battery admission of the emitted document; the fixed-point property; behavior at the target capacity boundary. | Default-battery refusal of the emitted document; refusal code when the target also exceeds capacity. |

## Established by reading

1. **The starting observations hold.** The contract gives `example` a
   same-build admission promise and `lesson` a publication promise. Both
   emitters run only parsing and the identity gate. CONTROLLER describes
   `example` and `runner verify` as controller-originated requests and does
   not mention `lesson`.

2. **The example rule joins two claims with different owners.** "Exit 0
   supplies the complete document" is decided by the controller at emission.
   "The same build's `run` admits it" is decided by the host at a later `run`;
   nothing at emission checks it. It holds because the constant and the host
   grammar are inputs of one build identity and the default live case observes
   the passage. The rule's support limits say this; the rule sentence, the CLI
   usage and CONTROLLER's "Exit 0 promises that the emitted specimen is
   admitted" read as though exit 0 reports an admission decision. The emitter's
   own vocabulary reinforces that reading: its gate-failure reason is "the
   example is not admissible", and the rule lists "an example the contract
   gate refuses", a branch a bound signed-pipeline build cannot reach.

3. **`lesson create` cannot inherit that promise unconditionally.** Its
   admission depends on an operand the emitter passes through uninspected. The
   emitter's target rule (absolute, UTF-8, no NUL) is a usage rule of its own:
   stricter than host file-attempt admission in requiring an absolute path and
   looser in length.

4. **Expected outcomes for the lesson inputs are stated by components that do
   not decide them.** The CLI usage states that `run` refuses `capture_typo`,
   without condition. The publication rule states a content fact beside a
   no-stability clause. The independently authored expectation is the corpus
   row; the normative refusal meaning is the contract's misspelling example.
   The guide and REQUEST-GRAMMAR restate the code and path in prose.

5. **Mechanical support differs by input.** The example's emitted bytes pass
   through `run` on the signed app in the default battery. The lesson inputs'
   emitted bytes do not: default host-admission evidence uses loader-materialized
   templates. The emitted and materialized requests are related by composition
   (unit and integration field assertions on the emission; identity digest over
   the template files), not by an observed passage.

6. **Target substitution has two rules.** The Python and Swift loaders replace
   every `$EFFECT` marker. The Rust emitter writes two fixed JSON positions and
   never reads the marker; the lessons README describes it as marker-driven.
   The two agree for the present templates and the unit test pins both
   positions.

7. **CONTROLLER's publication paragraph is no longer exact.** It contrasts
   general envelopes with "the example command's explicit fallible write/flush
   protocol". `lesson` implements the same protocol in separate code.

8. **The lesson support owner omits existing checks.** It cites three unit
   controls and says exit mapping and stderr handling have source-read
   support. The two `cli_contract.rs` lesson tests, added in the same commit,
   observe exit status, empty stdout on refusal, an unwritable stdout and a
   closed stderr on the selected app. The example owner cites its equivalents.

## Hypotheses

Their outcomes are under [Baseline observations](#baseline-observations).

- H1. Each emitted lesson document is a fixed point of `run`'s preparation,
  and the host treats it as it treats the loader-materialized request.
  Expected by construction; unobserved in the default battery.
- H2. `lesson create` with a 512-byte target exits 0 and `run` refuses it with
  `admission_refused` before any child. Source-read.
- H3. `lesson capture_typo` with that target is still refused with
  `unknown_field` at `policy.capture_compiled_profiel`. Source-read; the
  existing decode-before-capacity control uses a different oversized field.
- H4. A lesson template that parses but lacks `probe_plan[0]` would reach a
  `serde_json` index panic rather than the rule's exit 2. Source-read. The
  shipped templates cannot reach it and the unit suite would fail first; the
  example constant has a pre-compile generator check and the templates do not.

## Derivable facts and authored expectations

Facts about an input that could be presented from its owner:

- The lesson documents themselves. The contract renders the example from
  source and shows neither lesson input.
- Which member differs between the two templates, and where. That name is
  written out in the contract's misspelling example, the guide (prose and a
  `plutil` command), REQUEST-GRAMMAR (table and JSON), the corpus row and four
  test sources.
- The selector list and operand positions, held separately in `cli.rs`,
  `lesson.rs`, the README CLI block, the rule prose and both loaders.
- The shared emitter exit protocol, restated per command in the contract,
  controller reference, usage text, guide and REQUEST-GRAMMAR.

Expectations that must stay independently authored:

- That `run` admits the example, with the live case's pinned native results.
- That `create` is accepted and a new file exists afterward.
- That `capture_typo` is refused with its code and path, with no child and no
  file.
- Host capacities, owned by LIMITS.
- Each promise's wording, owned by the contract.

The misspelled member's name is both: its identity is a fact of the input, and
its appearance in `request_failure.path` is an expected outcome.

## Baseline observations

One execution of each passage on one machine, by hand, against
`dist/PolicyWitness.app`. `--version`, the app property list and
`docs/build_contract.py` on this tree all report
`development:e2a3ddf1c5f3848d9bcd370287fb9ad2be81ec78b11e8060d93ca9dd9e6fbac0`;
the app describes itself as `v0.3.7-74-g5adff9ae`. Each emitted file was
written to disk as printed and passed to `run` unchanged. Each target was
observed with `lstat` before emission and after `run`. Raw captures are in
`.tmp/publication-admission/captures/`, which is gitignored, disposable and
present only in the local checkout; the table is the retained account.

| Passage | Target, UTF-8 bytes / characters | `lesson` exit, emitted bytes | `run` exit and outcome | Refusal record | `bytes_written` | Target before → after |
| --- | --- | --- | --- | --- | --- | --- |
| X1 `create` | 42 / 42 | 0, 623 | 0, `finished`; one step, attempt `ok` | none | 622 | absent → regular file, size 0 |
| X1 `capture_typo` | 42 / 42 | 0, 661 | 1, `bad_request` | `unknown_field` at `policy.capture_compiled_profiel` | 660 | absent → absent |
| X2 `capture_typo` | 511 / 510 | 0, 1599 | 1, `bad_request` | `unknown_field`, same path | 1598 | absent → absent |
| X2 `create` | 511 / 510 | 0, 1561 | 0, `finished`; attempt `ok` | none | 1560 | absent → regular file, size 0 |
| X2 `capture_typo` | 512 / 511 | 0, 1601 | 1, `bad_request` | `unknown_field`, same path | 1600 | absent → absent |
| X2 `create` | 512 / 511 | 0, 1563 | 1, `bad_request` | `admission_refused` at `probe_plan.0.attempt.target`; `admission_failure` field `target`, actual 512, maximum 511, unit `utf8_bytes`, origin `runner_host` | 1562 | absent → absent |

The two boundary targets share one existing directory, differ by one leaf
byte, keep every component at or below 200 bytes and contain one two-byte
character. In every refused passage the runner reply carried the same
`request_failure` as the envelope, no worker or validator record and no steps.
In all six, emission wrote nothing to stderr, the submitted file was unchanged
after `run`, and the emitted JSON value equalled the repository template with
its `$EFFECT` markers replaced and the identity added.

What these establish, for this build and machine:

- H1, in part. `run` admitted the emitted `create` document and a new empty
  file appeared; the host refused the emitted `capture_typo` document. The
  host's decisions matched the corpus rows written for the loader-built forms.
- H2. Publication succeeded for a target the host then refused on capacity,
  before any child. The 512-byte target has 511 characters, so the count is
  of UTF-8 bytes.
- H3. The misspelled member is refused first at either length.

What remains inferred or unobserved:

- Exact delivered bytes. `bytes_written` equalled the emitted length less its
  newline in all six passages. That is a count of bytes the client's pipe
  accepted. It does not show which bytes were written or that the host
  received them.
- The fixed point. That `run`'s preparation reproduces an emitted lesson is
  supported by source inspection and that length agreement only. The example
  has a constructed exact-string test under a test identity; the lessons have
  none.
- Host receipt. The host's replies name the misspelled member and the 512-byte
  count, which is consistent with receipt of documents having those
  properties and is not a byte comparison.
- The query operand's own capacity. The attempt target is checked first, so
  the 511-byte bound on `sandbox_check.filter.value` was not separately
  reached.
- Release builds, other machines, repeated runs and a failing stderr write.
- H4, which was not pursued.

No observation contradicted a public promise.

## Repairs

No controller source, template or generator input of the build identity
changed; the tree still computes the identity above, so the staged app was
reused.

| Gap | Change | Kind |
| --- | --- | --- |
| CONTROLLER omitted `lesson` and joined publication with the example guarantee | [CONTROLLER](../../docs/CONTROLLER.md) now describes both emitters under one publication account, then states the example's same-build admission as a build guarantee spanning controller constant and host grammar, which emission does not observe, and states that `lesson` carries none. The guarantee's strength is unchanged. | Editorial |
| CONTROLLER named the write/flush protocol as the example's alone | The publication paragraph names both commands and both injected-writer tests. | Editorial |
| CONTROLLER did not say which lesson checks exist | The preparation paragraph states that no constructed exact-string test covers a lesson and what the live control reads. | Editorial |
| Guide command table listed `example` and not `lesson` | One authored row in the [guide](../../docs/PolicyWitness.md); the staged copy was refreshed with `generate_limits.py --stage-guide`. | Editorial |
| Lesson support owner omitted existing checks | The owner in [10-request.surface.md](../../docs/contract/10-request.surface.md) cites the three unit controls, the two selected-app CLI tests, the isolated-build identity test and the live control; its pins and limits say what each establishes. Regenerated with `generate_contract_stamps.py`: `CONTRACT.md` changed, `public.json` did not. | Support presentation |
| Default battery never submitted emitted lesson bytes | `emitted_lessons` in [contract.py](../../tests/suites/runner_outcome_bad_request/contract.py), inside the existing default `accepted_input_contract` case. | Mechanical |

The lesson tests were read before citing them. The selected-app tests observe
exit status, stdout, an empty stderr on success, identity, labels, verbatim
targets and the one-member difference. Their stderr control closes the stream
at launch. Unlike the example's, no lesson control gives stderr a reader-less
pipe, so the lesson's indifference to a failing stderr write stays
source-read, and the owner says so.

`emitted_lessons` runs the selected app's `lesson` for each corpus row that
names an app-owned source, retains its stdout, stderr and exit status, writes
the emitted bytes as the request file and submits it through the case's
existing `cli` helper. Expected admission, refusal code and path, child
absence and the file observation come from the corpus row and that helper;
nothing is derived from the emitted document except the request itself. It
requires a row for every lesson source, so a removed row fails instead of
passing by omission. The loader-built rows remain. They exercise the direct
host entry, and the Swift unit tests read the same rows without an app; the
emitted path covers neither.

Maintenance added:

- The lesson selector is taken from the template's file stem. A selector
  renamed apart from its file fails the control.
- The support owner cites seven checks by symbol, and CONTROLLER names one
  more test and links the control. Renaming any of them requires the
  citation.
- The guide's command table carries a `lesson` row beside the usage text.
- The default case makes four more app invocations.

## Verification

One dispatcher run covered the changed documents, generated contract and
changed control: the `source_drift` suite with
`runner_outcome_bad_request/accepted_input_contract`, run
`20261113T230216Z_ae39b836`. All 11 cases passed, the app was unchanged
across the run and no case overlapped system sleep. The tree was `8d4d202a`
with the repairs above uncommitted, against the staged app of the same
identity. In the live case's artifacts, each `lesson-emitted-*` request file
is byte-identical to the retained `lesson` stdout; `create` was admitted with
its file observed, and `capture_typo` was refused with `unknown_field`, no
worker and no steps.

The plan paragraph changed after that run, so
`source_drift/generator_contract` ran once more alone, run
`20261113T231002Z_20f65548`, and passed. Both were development runs. Their
output was inspected and then removed with `make prune APPLY=1`, together
with the earlier plan-link check.

Not rerun, as reviewed judgments and not mechanical facts:

- `unit` and `integration`. No Rust source changed. The newly cited lesson
  tests were read, not executed here; the owner credits no execution.
- `witness_contract/example_round_trip` and Swift `runner_unit`. Neither the
  example, the corpus nor a loader changed.
- Opt-in `witness_contract/guide_workflows`. The guide gained one table row,
  outside every fence that case selects.

No rejected control has been run for `emitted_lessons`. The step reuses the
case's existing assertions, and the mutation proposed below would be its
first rejected control.

## Remaining public wording

Two sentences still read as though exit 0 reports an admission decision.
Neither was changed: the first is stamped public content, and the second is
controller source, an identity input whose edit requires a new build.

1. The example rule in the request surface. Current: "Process exit 0 supplies
   the complete document, and the same build's `run` admits it." and, at the
   end, "The command reads no file, starts no runner and reports nothing about
   a caller's document; `run` remains the only admission." Proposed: "Process
   exit 0 supplies the complete document. The build guarantees that its own
   `run` admits that document; emission performs no admission, and `run`
   remains the only admission." with the final sentence ending at "a caller's
   document." Every surface stamp is already `unreleased`, so this changes
   `CONTRACT.md` and the public snapshot and moves no released stamp.
2. The CLI usage notes in `cli.rs`. Proposed for `example`: "…carrying this
   build's contract; the build guarantees its own run admits it; exit 0
   supplies the complete document, and on exit 2 discard stdout". Proposed
   for `lesson`: "…capture_typo carries a deliberately unknown policy field;
   exit 0 means complete publication and reports nothing about admission, and
   on exit 2 discard stdout". This is best carried with the next controller
   source change, not built for alone.

Retained without change: the two promise kinds, the lesson rule, the
independent corpus expectations, the separate `lesson` command and both
substitution implementations.

## Proposed mutation experiment

Not run.

**Mutation.** A disposable stand-in for the selected app's `policy-witness`
forwards every invocation to the real binary, except that
`lesson capture_typo` returns the real `lesson create` output for the same
target. Publication still exits 0 with a complete, correctly identified
document; the document no longer carries the misspelled member. No source,
template, corpus row or app byte changes, and nothing is rebuilt.

**Reader conclusion at risk.** "A passing `accepted_input_contract` shows
that what `lesson capture_typo` publishes is refused by `run`." Before the
repair above the case could not support that: it built the request from the
repository template and never read the app's output.

**Detection expected.** `emitted_lessons` should fail on the `capture_typo`
row, where `run` exits 0 and the target file exists against an expected
`unknown_field` refusal. The loader-built `capture_typo` rows should still
pass, since they do not depend on the emitter.

**Reading the result.** A missed detection would show that the new step does
not bind the published document to the row's expectation, a checker defect.
It would show nothing about the product: the real emitter and host are
unchanged. Detection would show that this one divergence is caught. It would
not show that emitter and template agree in general, that any byte-level
property holds, or that publication implies admission of `create`.

**Cost.** The stand-in needs links to the real client, service and property
list beside it, and one by-hand run of `contract.py` outside the dispatcher
with its output in scratch.
