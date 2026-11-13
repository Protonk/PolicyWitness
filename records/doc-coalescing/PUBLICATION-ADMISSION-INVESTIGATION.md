# Publication, preparation and admission boundary

A bounded investigation of three existing inputs: the specimen `example`
emits, the accepted `lesson create` input and the deliberately refused
`lesson capture_typo` input. It follows them through publication, controller
preparation and host admission, and stops before interpreting native execution.
It is not a four-pass cycle.

This record currently holds the initial map only. No experiment was run and no
public document was edited. Source was read at `c9a7978d`. The distribution
app reports `development:e2a3ddf1…`, the identity `docs/build_contract.py`
computes for this tree, so the experiments proposed below need no build.

## Passage

| Stage | Decision and owner | Same for all three inputs? |
| --- | --- | --- |
| Publication | Controller. [example.rs](../../controller/src/example.rs) and [lesson.rs](../../controller/src/lesson.rs) each check arguments, refuse an empty or `unbound` identity, parse the embedded document with `parse_request`, insert the identity, run `validate_contract`, serialize with `to_string_pretty`, append one newline, then `write_all` and flush. `lesson` also checks its target (nonempty, absolute, UTF-8, no NUL) and writes it at two fixed operand positions. | Same mechanism in two separate implementations. Neither consults the host grammar. |
| Controller preparation | Controller. `run` in [run_flow.rs](../../controller/src/run_flow.rs) reads the file once, parses, gates identity, validates selectors, resolves augments, strips selection fields and holds one pretty serialization for the client. | Yes. None of the three carries a selector or augment, and the controller does not check closed field sets, so the misspelled member is delivered. |
| Host admission | Host. [PWRunnerRequest.swift](../../runner/Sources/PWRunnerCore/PWRunnerRequest.swift) checks `contract`, then root and nested closed objects while decoding; `admitSpecimen` in [ProbeRunner.swift](../../runner/Sources/PWRunnerCore/ProbeRunner.swift) checks capacity, then meaning. | No. `capture_typo` stops in decoding at `policy`. `example` and `create` continue to capacity and meaning; `create` carries a caller-chosen target subject to the 511-byte operand capacities in [limits.json](../../docs/limits.json). |
| After admission | Host, worker, validator. | Not followed here. Admission starts children; it establishes no query answer and no file effect. |

## Map

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

## Established

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

## Narrow experiments

Both use the current distribution app by hand, with captures kept in scratch.
Neither adds a case, build or worktree.

- X1 (H1). Emit both lessons to fresh targets and submit the emitted files
  unchanged. Compare `request_delivery.bytes_written` with the emitted length
  less its newline; read `data.request_failure` and whether the runner reply
  carries the same record; observe each target independently. Four invocations.
- X2 (H2, H3). Repeat with 511-byte and 512-byte targets. Six invocations. The
  511-byte `create` is expected to be admitted whatever its attempt returns,
  which keeps admission apart from the effect.

Findings 2, 4, 6, 7 and 8 are settled by reading and need no experiment. H4
needs none unless a correction is selected.

## Recommended next step

Run X1 and X2, then return with dispositions sorted by kind:

- Editorial: CONTROLLER's origination and publication paragraphs; the lesson
  support owner's citations and limits.
- Public wording, for a maintainer decision: whether the example rule should
  separate what exit 0 establishes from the build-level admission promise and
  state that promise's conditions; whether usage text should state a host
  outcome for `capture_typo`.
- Mechanical: whether one default check should relate emitted lesson bytes to
  the materialized templates, and where.
- Retain: the two promise kinds, the independent corpus expectations and the
  separate `lesson` command.

Adjacent, not pursued: the root README's hand-written first specimen; whether
the example promise extends to an external runner selected at `run`.
