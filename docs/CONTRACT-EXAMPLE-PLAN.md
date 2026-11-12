# Contract example plan

This plan gives PolicyWitness one specimen that it defines in its own controller source, prints through its own CLI and admits through `run`, with a test that follows that passage on the signed app. The contract renders the example from the same source. The work follows the completed four-stage contract effort, whose remaining release inputs are in [RELEASE-INPUTS.md](../records/contract/RELEASE-INPUTS.md), and targets the 0.3.8 candidate without making the tag or publication an outcome.

The plan is written for an executor who knows the repository but not the planning conversation. Section 2 holds the principles the maintainer settled; a design choice that conflicts with one of them is wrong even if the rest of the plan seems to allow it.

## 1. Intended result

```sh
PW=/Applications/PolicyWitness.app/Contents/MacOS/policy-witness
$PW example > /tmp/example.json
$PW run /tmp/example.json > /tmp/result.json
```

- One definition of the example exists, in controller source.
- `example` prints that definition with the binary's own identity, in the serialization the controller itself holds and delivers.
- `run` admits those bytes and delivers them unchanged.
- The contract's rendering of the example is extracted from that source.
- A default-battery case follows the passage on the signed app. It supplies no specimen of its own.

For this release the audience is the project: PolicyWitness is tested against its own expression at release. The command is a small entrance for that pipeline, not a published feature. It is the first step toward examples that keep statements of what PolicyWitness accepts out of the user guide.

## 2. Principles

The maintainer settled these on 2026-11-12.

**There is one way to hold PolicyWitness.** A specimen is submitted with `run`, and `run` is the only way to ask whether PolicyWitness accepts a shape. The answer comes from the same admission that precedes execution. This plan adds no admission query, validation mode, dry run or second submission path, and none is on its route. `example` takes no input and answers no question about a caller's document; it hands the caller an input for `run`. Every refusal the test demands is obtained through `run`.

**The app is the authority for the example.** The example is what the shipped code defines. Nothing outside that code holds a second copy that must be kept equal by hand: the contract extracts its rendering, and the test obtains the document from the built app.

**Fixtures author no specimen.** A fixture intervenes in three places and nowhere else:

- *before*, by changing the produced bytes in one place and demanding refusal at a stated boundary;
- *beside*, by observing the machine itself: the target file, the process exit status;
- *after*, by reading the envelope with the independently written consumer and requiring the controller's own assessment to be clean.

A fixture does not restate the app's interpretive rules. Those have three independent readers already (host, controller, test consumer), and this plan does not add a fourth.

**Promise almost nothing.** A shipped binary has no private commands, so the entrance is stated truthfully in the contract. Its single promise is that the emitting build admits what it prints. Content, layout and labels can change in any build.

## 3. Starting state

Observed on `main` on 2026-11-12. Re-check any that the work depends on.

**The checkout is prepared for `v0.3.8` and has no `v0.3.8` tag.** The stamp tables and [contract/public.json](contract/public.json) claim the release, so `generate_contract_stamps.py --check` exits 1 with `release history unavailable; restore annotated release tags: v0.3.8`, and [build.sh](../build.sh), which runs that check, refuses. Ordinary generation refuses too; generation with `--release v0.3.8` works. Earlier pre-tag work alternated between the two states: `d18d4925` returned the stamps to `unreleased`, and `6f65612b` prepared them again.

**Identity.** [build_contract.py](build_contract.py) derives `release:vX.Y.Z` for a clean checkout at one annotated release tag whose selected bytes equal the tag's blobs, and `development:<sha256>` otherwise. The digest covers every `.rs` file under `controller/src`. [json_contract.rs](../controller/src/json_contract.rs) embeds the value as `BUILD_CONTRACT`; a plain Cargo build is `unbound`.

**Admission and the held request.** `validate_contract` in [request_patch.rs](../controller/src/request_patch.rs) requires `contract` to equal the binary's identity and refuses an empty or `unbound` identity; a refusal is exit 1, `bad_request`, with `data.request_failure`. The controller owns that gate, selectors and augments. The request grammar belongs to the Swift host. [run_flow.rs](../controller/src/run_flow.rs) parses the file once, removes controller selection fields, and holds one `serde_json::to_string_pretty` serialization that it delivers to the client. A retained smoke run confirms the form: its `request_delivery.bytes_written` of 576 equals the length of the submitted specimen serialized with sorted keys and two-space indentation.

**The controller already originates one specimen.** `verify_request()` in [runner_commands.rs](../controller/src/runner_commands.rs) builds an apply-only request with the binary's identity and sends it on `runner verify`. The contract's `request.specimen.apply_only` example is a separate hand-typed document.

**CLI.** [cli.rs](../controller/src/cli.rs) dispatches `run`, `runner` and `--version`. Every current output is an envelope. `run` reads a file path; there is no standard-input form.

**Contract tree.** Example nodes carry prose and support and no kind-specific facts. A node's facts enter the canonical public payload, so they move the surface stamp. Strict loading requires each rule and example to have graded support or an explicit evidence gap. The tree already takes shapes from code: [record_definitions.py](contract/record_definitions.py) imports field declarations, and [runtime.py](contract/runtime.py) reads selector constants out of `runner_select.rs`. Generation refuses growth in `free.*` relationship counts.

**Readers and harness.** [consumer.py](../tests/lib/consumer.py) validates an envelope against the shape goldens and record rules, including `order` against its supporting chain, without consulting specimen policy or production classifiers. The controller reports its own assessment under `data.runner_sandbox_diagnostics` (`disposition_integrity`, `disposition_issues`). [run_capture.py](../tests/lib/run_capture.py) re-serializes a specimen, so it cannot submit bytes unchanged. Release acceptance runs the default battery with no selectors ([SIGNING.md](SIGNING.md#release-procedure)). The opt-in `preflight/build_refusal_controls` rehearsal runs that battery against a disposable fixture reporting `release:v1.0.0`.

## 4. Design

### 4.1 The example in controller source

A new module, `controller/src/example.rs`, holds the example as one raw string constant: a JSON object without a `contract` member.

```json
{"specimen_id":"example","policy":{"format":"sbpl","sbpl_source":"(version 1) (allow default)"},"probe_plan":[{"step_id":"read-hosts","sandbox_check":{"operation":"file-read-data","filter":{"kind":"path","value":"/etc/hosts"}},"attempt":{"kind":"file","action":"open_read","target":"/etc/hosts"}}]}
```

The scenario is one read-only paired probe under an allow-default policy. It writes nothing and needs no fixture, and it gives each of the three fixture interventions something to act on; an apply-only document would leave two of them empty.

The command builds its output from that constant with the functions `run` already uses:

1. `parse_request` reads the constant.
2. The binary's `BUILD_CONTRACT` is inserted as `contract`.
3. `validate_request_contract` gates the result.
4. `serde_json::to_string_pretty` serializes it, the call that produces `run`'s held request.

Two consequences follow, and the test checks both. The emitter cannot print a document its own controller gate refuses. And the printed document is a fixed point of `run`: it carries no selection field, so `run` parses it and holds the identical serialization. The bytes the user sees are the bytes the client is given.

The file is hand-written Rust under `controller/src`. It is a build-identity input with no change to `build_contract.py`, no generated source and no build step. `build.sh` does not change.

The module's constant is the example's only definition. `verify_request()` stays as it is; section 10 notes the later unification.

### 4.2 The command

```text
policy-witness example
```

It takes no argument. Naming and selecting examples wait until a second example exists and its design is settled.

| Invocation | stdout | stderr | Exit |
| --- | --- | --- | --- |
| `example` on a bound build | The document and one trailing newline, nothing else | empty | 0 |
| `example` with any argument | empty | Usage | 2 |
| `example` when the binary's identity is empty or `unbound` | empty | One line stating that this build has no public identity | 2 |
| `example` when the constant does not parse or the gate refuses on a bound build | empty | One line with the request-failure code | 2 |
| The write to stdout fails | Whatever the system accepted, possibly an incomplete document | One line, if stderr is writable | 2 |

The command reads no file, resolves no app root, loads no manifest or registry and launches nothing. The whole document is rendered in memory and gated before any byte is written, and the write is one call whose failure maps to exit 2 without a panic. Callers get one distinction: exit 0 with the complete document, or exit 2 with none they can use. The stderr line is for a person and is not a classification interface.

The fourth row cannot occur in a build from the signed pipeline: the contract generator's check, which `build.sh` runs before compiling, refuses a constant that is not an admissible-looking object (section 4.3), and JSON encoding of the identity round-trips exactly. The row is defined so that no failure can print a partial or inadmissible document. It has source and unit-test support and no built-app observation.

The output is the specimen itself, not an envelope. The document carries the identity in `contract`, where the contract says a specimen carries it, and redirecting stdout yields a file `run` accepts with no extraction step.

`print_usage` lists the command, and the controller README's CLI block follows `cli.rs` as the drift suite requires. The user guide does not mention it in this release.

### 4.3 The contract's account

**One rule.** Under `request.specimen`, add `emit_example {emit_example: reports}`: the controller, at entry `cli_example`, reports a specimen with `set_value(specimen.contract, ref("identity.build.contract"))`. Its prose states the single promise, that the emitting build's `run` admits the printed document, the two exit statuses, and that content and layout carry no promise between builds. Author it without `free.*` facts. If one proves unavoidable, stop and raise it; do not raise the baseline. No new subject or record is needed, so no shape golden changes.

**One example node, rendered from code.** Add `request.specimen.example {example: example}` with one new example fact, a citation in the shared `path` and `symbol` vocabulary:

````markdown
### Emitted example {example: example}

```contract
document: {"path": "controller/src/example.rs", "symbol": "EXAMPLE_DOCUMENT"}
```
````

The tree reader extracts the constant with a strict reader that refuses anything but exactly one definition of that symbol as a raw string. It then requires a JSON object that has no `contract` member, no `_test_overrides`, none of the controller selection keys already read from `runner_select.rs`, and only members that are fields of the imported `PWRunnerRunSpec`. Deeper validity belongs to the host and is established by execution.

The renderer prints the document with `contract` shown as `<reported-contract>`, and the command that emits it. The parsed document enters the node's public payload, so a change to the example moves the `request` surface stamp. The cited source file becomes a declared generator input, as `runner_select.rs` already is.

The existing `apply_only` and `read_hosts` examples stay as they are.

### 4.4 Identities and stale artifacts

| Concern | Mechanism |
| --- | --- |
| Development build | `contract` is `development:<sha256>`; the digest includes `example.rs`. |
| Release build | `contract` is `release:vX.Y.Z`; the release form requires `example.rs` to equal the tag's blob. |
| Example edited, contract not regenerated | `--check` refuses the stale [CONTRACT.md](CONTRACT.md) and snapshot before compilation and in `source_drift`. |
| Example malformed or carrying a forbidden member | The same check refuses, naming the source. |
| Source edited during a build | The existing pre-sign identity recomputation refuses. |
| Example changed between releases | The `request` stamp becomes `unreleased`; release preflight refuses remaining `unreleased` rows. |
| Specimen saved from another build | `run` refuses it with `unsupported_contract` and names the expected identity. |

No path runs from documentation into shipped code. Editing contract prose cannot change the build identity.

### 4.5 The round-trip case

**`witness_contract/example_round_trip`** (default; requires the app). A shell case in the style of the smoke case runs the selected app directly and retains raw stdout, stderr and exit status for every invocation: `--version`, two emissions, the `run` of the emitted bytes, and each perturbed `run`. A Python checker then reads the retained files. The emitted bytes are submitted unchanged; the case does not route them through `RunCapture`. The case contains no specimen document.

The emitted document is `S` and the run envelope for `S` is `E`. Every assertion has a stable identifier and belongs to one group.

**Consistency.** These hold whatever the native results. A non-`finished` admitted reply can satisfy them. When no admitted reply exists, only the passage and controller-side assertions are evaluated.

| Group | Demand | Intervention |
| --- | --- | --- |
| Passage | `S.contract` equals `--version`'s `build.contract` and `data.contract` and the `PWContract` the case reads from the app's property list; it has a packaged `release:` or `development:` form; two emissions are byte-identical | after |
| Passage | `S` re-serialized by the case, with sorted keys and two-space indentation, equals `S`'s bytes; `E`'s `request_delivery.bytes_written` equals the document's length without its final newline | after |
| Passage | `S` without `contract` equals the contract's rendered example, read from the snapshot | after |
| What the case will run | `S` is the ordinary form with a `probe_plan`; every attempt is a read-only file action; no `_test_overrides`; no selection or entitlement requirement. The case refuses to run a document outside these bounds | before |
| Admission | No `request_failure` and no `bad_request` outcome; the dossier's `policy.augmentation.original_sha256` and the reply's `policy_sha256` equal the SHA-256 of `S`'s policy source | after |
| Identity | `E.build.contract`, `data.runner_client.transport.contract` and `runner_result.producer.contract` each equal `S.contract` | after |
| Echo | `runner_result.specimen_id` equals `S.specimen_id`; the reply's step identifiers are `S`'s, in order; each query echoes its submitted operation and filter; each attempt echoes its submitted kind, action and target | after |
| Reported against observed | The CLI exit status the case captured equals `result.exit_code`; the target files' bytes and metadata, read by the case before and after, are unchanged | beside |
| Existing readers | `consumer.validate` reports no error; the controller's `disposition_integrity` is `valid` with no `disposition_issues` | after |

Every expected value in the passage, admission, identity and echo groups comes from `S` or from another output of the same app. The case knows the document's form and nothing of its content.

The comparison with the snapshot is a comparison, never a substitution: a mismatch means the app and the tree disagree, which a stale app produces. Ordering, comparison vocabulary and outcome mapping are not restated here. The consumer checks them, and its rejected controls belong to `blackbox_e2e/checker_controls`.

**Native expectations.** These depend on the machine. The case takes its targets from `S` and observes its prerequisites itself: each attempt target resolves to a regular file the test user can open and read. The expectations are pinned to the present example and change with it.

| Observation | Expectation under the prerequisites |
| --- | --- |
| Completion | `runner_result.normalized_outcome` is `finished` |
| Prediction | `result_source` is `validator`, `outcome` is `allow`, `native_rc` is 0 |
| Order | Given that prediction, `order` is `query_first` |
| Attempt | `outcome` is `ok`, `rc` is 0 |

Nothing in either group states that prediction and enforcement agree.

**Refusals.** Each starts from `S`, makes exactly one change and goes through `run`. The unmodified `S` passes in the same case, so each refusal is attributable to its change.

| Control | Change | Required result |
| --- | --- | --- |
| Other development build | One hexadecimal digit of a `development:` identity changed, or a well-formed `development:` identity substituted when the app is a release build | Exit 1, `bad_request`, `request_failure` with code `unsupported_contract`, path `["contract"]` and `expected_contract` equal to the app's identity; no client capture and no runner reply |
| Other release | `contract` set to `release:v0.0.0` | The same |
| Unbound | `contract` set to `unbound` | The same |
| Absent identity | `contract` removed | Code `missing_field`, the same path and expected identity |
| Truncated document | Final byte of the object removed | Code `invalid_json`; no client capture |
| Unknown member | One unknown top-level member added, identity intact | Exit 1, `bad_request` from the host with code `unknown_field` and a path naming the member; no step results |

The first five stop at the controller. The last shows that a correct identity does not carry an invalid document past the host. Together they show that `run` distinguishes the example from its neighbors, which the app's acceptance of its own example cannot show.

### 4.6 Status, classification and earlier runs

**Status and classification.** The case has two statuses, pass and fail. It declares no skip, and the dispatcher's equipment check does not cover these prerequisites, so no row below is an unrun case. The report's classification carries the distinction the status cannot.

| Situation | Consistency | Native expectations | Status | Classification |
| --- | --- | --- | --- | --- |
| Everything holds | Evaluated, passing | Evaluated, passing | pass | none |
| A consistency assertion fails, at emission, admission or in the reply | Evaluated, failing | Evaluated when their prerequisites hold | fail | `consistency` |
| The run yields no admitted reply (service unreachable, tool error) | Passage and controller-side assertions only; nothing is credited or faulted from the missing reply | Not evaluated | fail | `execution_unavailable` |
| A target prerequisite is not observed | Evaluated; they do not depend on it | Not evaluated | fail | `prerequisite_unestablished` |
| Prerequisites hold and a native expectation fails | Evaluated, passing | Evaluated, failing | fail | `native_observation` |

More than one classification can apply, and the report lists each.

**Release consequence.** Every failing row fails the default battery and therefore release acceptance; that attempt produces no archive. The classification says where the remedy lies, not whether the release may proceed:

- `consistency` is a defect in the product, the contract's account or the checker. Fix it where it lives; a product or example fix is new shipped source and a new build.
- `execution_unavailable` locates missing execution evidence without assigning a cause. For an observed automation-sandbox refusal, follow the repository's sandboxed-harness guidance: rerun the same command once outside it with the artifact unchanged. A passing rerun supports that explanation and is the run that gets credited.
- `prerequisite_unestablished` is not a PolicyWitness result. The machine cannot run this example's native check, and acceptance belongs on one that can.
- `native_observation` is an observation about this machine or build. Retain the evidence without assigning a cause; the rules below determine whether acceptance needs a correction or a fresh qualifying run.

In no row is the case removed from the default battery, given a skip, or handed another document to obtain a pass.

**Earlier runs and variation.** A failed run remains failed. The following rules determine which earlier failures a fresh qualifying run can supersede and which remain objections to acceptance. They do not change the case's assertions or statuses, add automatic retries, or replace the complete passing default battery required by section 8. Review every failed assertion separately: an interruption does not excuse an independent identity or echo defect.

| Earlier observation | Required disposition |
| --- | --- |
| One reply reports `query_first` and another `unestablished`, each accepted by the consumer | The difference needs no explanation for consistency. The latter run still fails the native order expectation; apply the remaining rows to that failure. |
| A target prerequisite was not observed, the dispatcher recorded system sleep overlapping the failure, or an automation-sandbox refusal was confirmed by the prescribed unchanged-artifact rerun | Record that exclusion and credit a fresh run that establishes the prerequisites and completes without it. Explaining why the target was unavailable, the machine slept or the harness imposed the restriction is unnecessary. Use the existing dispatcher sleep record and sandboxed-harness procedure. |
| The validator produced no answer, with a valid recorded spawn failure or timeout and honest `unestablished` ordering | A complete passing run can supersede this trial without explaining the underlying scheduling or OS cause. The earlier run supplies no successful native-observation credit. Its available evidence must satisfy the consistency assertions; a generic error without evidence locating the failure does not establish this disposition. |
| The validator answered `deny`, or the worker failed `open_read`, while the stated prerequisites were observed | Resolve the challenge to the native expectation through a justified correction to its applicability, a checker correction or a product fix. Later successes alone do not settle it. |
| An identity, policy digest, echo or reported-against-observed assertion is wrong, or an existing reader reports an error | Resolve the product, checker or contract discrepancy before acceptance. These must hold even when native execution fails. |

The example must demonstrate successful execution. This work does not require an explanation of every correctly reported inability to execute. A failure without a disposition supported by this table leaves evaluation pending, including a native discrepancy that the table does not cover. Do not infer an exclusion from a later pass or classify every `execution_unavailable` result as environmental.

For failures requiring a correction, the evidence needed to close the issue is bounded:

- **Checker defect:** replay the retained failing input through the corrected checker and show that the affected assertion's rejected control still works. Reproducing the original live event is unnecessary.
- **Product defect:** identify the faulty behavior and establish its correction with a focused control and the applicable verification. Explaining precisely why it occurred intermittently is unnecessary. Changes to section 5's not-touched components remain separate work.
- **Incorrect prerequisite or expectation:** identify the concrete condition that changes applicability and how the case observes it. Passing after a reboot alone does not establish that condition.

Record the failed assertion, the relevant retained observation and its disposition in the evaluation record, with any correction and replacement run. Continue that record through section 9's untagged candidate verification, including dispositions that need no product correction. A new build identity or ten later passes is not itself a disposition; name the relevant change. Preserve original results under the repository's evidence-retention rules rather than rewriting a failed historical run as passing.

### 4.7 Checker controls

**`witness_contract/example_round_trip_controls`** (default; offline). Every assertion that can fail the live case has a stable identifier in the checker. Each failure reports that identifier, its classification and a human-readable explanation. Controls match the identifier and classification; the explanation's wording can change. All of the checker's inputs are retained files, so every assertion can be handed a constructed input that violates it. Build the inputs from the existing constructed-envelope helpers in [blackbox.py](../tests/lib/blackbox.py) and the reply fixtures under `tests/fixtures/contract/`; the case generates no replacement fixtures. A constructed document stands in for `S` here because this case tests the checker, not the app.

The checker and control case establish coverage as follows:

- Start with an input that passes with no failure diagnostics. Each rejected control introduces one logical fault and names its target assertions and the exact expected set of `(assertion identifier, classification)` pairs, authored independently of the checker's output. If the fault necessarily triggers another assertion of this checker, include that consequence explicitly. Missing or unexpected diagnostics fail the control, with only the shared-consumer allowance below.
- A control earns coverage for its target assertions only after the actual diagnostic set matches the expected set under that allowance and includes their failures. Registering or executing a control earns no coverage. For example, changing the producer contract must produce the identity assertion's diagnostic with `consistency`; a generic consumer error alone cannot satisfy that control. Check producer identity before semantic reading; the consumer's version rejection still prevents assertions about the unsupported reply's semantics.
- Report all `consumer.validate` errors under one aggregate assertion, `consumer_validation`, classified as `consistency`, and retain every underlying message. Its dedicated propagation control requires that diagnostic exactly. Other rejected controls permit that one diagnostic in addition to their exact expected set; its presence there earns no coverage. Consumer errors still fail the live case and the passing baseline. The allowance applies only when matching negative-control diagnostics and does not suppress consumer output or permit another unexpected assertion.
- A combined-fault input must retain the diagnostics of its independent faults. Check unevaluated groups explicitly: a missing prerequisite requires `prerequisite_unestablished` and native expectations not evaluated; a missing admitted reply requires `execution_unavailable` and no credit or fault from the absent reply. A rejection alone does not establish these results.
- The completeness assertion compares the checker's full assertion table with the identifiers whose targeted controls actually matched, plus the documented exceptions resting on other evidence below. An assertion without verified coverage or a documented exception fails the case. The control results retain expected and actual diagnostic sets and the identifiers that earned coverage.

| Group | Rejected controls required |
| --- | --- |
| Passage | The version identity differs; the property-list identity differs; the identity is not in a packaged form; two emissions differ; the document is not in the held serialization; `bytes_written` differs from the document's length; a member differs from the contract's rendered example |
| What the case will run | A write action; an exec action; test overrides; a runner selector; a required entitlement; phases in place of the plan |
| Admission | A `request_failure` or `bad_request` outcome; each policy digest differing |
| Identity | Each of the three identities differing, separately |
| Echo | The echoed `specimen_id` differs; an extra, missing or renamed step; the query echo differs; the attempt echo differs |
| Reported against observed | The captured exit differs from `result.exit_code`; a changed target |
| Existing readers | The dedicated consumer propagation control; `disposition_integrity` not `valid`; a nonempty `disposition_issues` |
| Native | A coherent `validator_spawn_failed` reply with a missing prediction and honest `unestablished` ordering; a prediction other than `allow`; an attempt that failed. With prerequisites held, each must produce `native_observation` with consistency still passing. An unobserved prerequisite must produce `prerequisite_unestablished` with native expectations not evaluated |
| Refusals | For each refusal control: an accepted run in its place; the wrong code; a missing or wrong expected identity; a client capture on a controller-side refusal |
| Classification | A combined-fault input reports every fault; an input with no admitted reply is `execution_unavailable` and credits or faults nothing from the reply |

The coherent `validator_spawn_failed` control has matching reported and captured exits of 1 and a clean consumer reading. It fails the native completion and prediction expectations without failing consistency. A second control changes only its captured exit to 0 and must add the reported-against-observed diagnostic under `consistency` while retaining the native diagnostics. This establishes that a nonzero exit alone is not a consistency fault.

Two things rest on other evidence, and the suite account says so:

- Shape and record validity, including ordering, come from `consumer.validate`, whose rejected controls belong to `blackbox_e2e/checker_controls`. This case's propagation control requires `(consumer_validation, consistency)` and establishes that a consumer error fails the case; incidental consumer diagnostics in other controls do not cover it.
- That the app is validly signed and unchanged comes from the dispatcher's inspection and inventory, controlled in the `dispatcher` suite.

### 4.8 Other controls

**Cross-build controls** extend [cli_contract.rs](../controller/integration/cli_contract.rs), which already builds isolated non-test controllers with supplied and absent stamps. The unbound build's `example` exits 2 with empty stdout. The build given another identity emits that identity, and the signed app's `run` refuses the resulting document with `unsupported_contract` and its own expected identity. The same file takes the usage rows of section 4.2 against the signed app.

**Generation controls** go in the existing `source_drift` cases, over disposable source copies:

- The example constant edited without regeneration is refused by `--check`, which names the stale outputs and writes nothing.
- After regeneration, the rendered contract, the `request` surface payload and `build_contract.identity` all differ.
- The extraction refuses, naming the source: a missing symbol; two definitions; a constant that is not a raw string; a value that is not a JSON object; a `contract` member; `_test_overrides`; a selection key; an unknown top-level member.

**Unit tests** in the controller cover the renderer under several identity spellings, including one that needs escaping; the fixed-point property, by parsing the output and holding it as `run` does; the gate's typed refusals for an unbound identity and an unparsable constant; a failed write mapped to exit 2; and dispatch. The gate takes the document and the expected identity as parameters, so the tests match the returned reason and not a message.

### 4.9 Test boundary

| Stage | What is checked | Equipment | Home |
| --- | --- | --- | --- |
| Generation | Extraction and its refusals, stale rendering, stamp and identity sensitivity | Python | `source_drift` (existing cases) |
| Compilation | Rendering, fixed point, gate, failed write, dispatch | Cargo | `unit/rust.unit`, `unit/rust.fmt` |
| Packaging | No new layout or build step. Existing gates: generator check before compilation, identity recomputation before signing | Build toolchain and identity | `make build`; `preflight/build_refusal_controls` at candidate entry |
| Signed-app inspection | Usage rows, cross-build controls | Signed app; Cargo for the isolated builds; no XPC | `integration/cli.integration` |
| Checker | Matched rejected controls and completeness | Python | `witness_contract/example_round_trip_controls` |
| Actual execution | Passage, admission, identity, echo, existing readers, native expectations, refusals through `run` | Signed app and XPC | `witness_contract/example_round_trip` |

Only the last row observes native execution, and only its native group depends on the machine. Both new cases are default members: they are read-only, need no signing identity, GUI session or network, and add a handful of CLI invocations. Default membership places the live case in release acceptance with no further wiring.

## 5. Affected components

| Area | Files | Change |
| --- | --- | --- |
| Controller | `controller/src/example.rs` (new), `main.rs`, `cli.rs`, `controller/README.md` | The constant, the command, unit tests, usage and CLI block |
| Contract authoring | `docs/contract/10-request.surface.md` | The rule and the example node, with support |
| Contract model | `docs/contract/tree.py`, `README.md`, `AGENTS.md`; `docs/generate_contract_stamps.py` | The `document` fact, its extraction, validation and rendering; the cited source as a declared input; authoring reference |
| Generated | `docs/CONTRACT.md`, `docs/contract/public.json` | Regenerated, never hand-edited |
| Tests | `tests/catalog.json`; `tests/suites/witness_contract/` (two case scripts, one checker, README); `controller/integration/cli_contract.rs`; `tests/suites/source_drift/` (`contract_tree_controls.py`, `generators.py`, `build_contracts.py`); `tests/README.md`, `tests/COVERAGE.md` where applicable | Cases, controls, registry and suite accounts |
| Possibly | `docs/architecture.json` | Only if its account enumerates CLI entries; check and regenerate if so |

Not touched: `build.sh`, `meson.build`, `build_contract.py`, the bundle layout, the evidence manifest, the wire schema, the host, the worker, the validator, the dispatcher, `runner verify` and the user guide. A need to change any of these is a signal to stop and reconsider, not a routine extension.

## 6. Order of implementation

**Step 0. Return the stamps to `unreleased`.** Follow the `d18d4925` precedent so the tree can be generated, built and tested. Done when `generate_contract_stamps.py --check --require-history` passes and the three stamp artifacts are the only difference from the starting commit.

**Step 1. The example and its account, together.** Add the module and command with their unit tests, usage text and README block; extend the tree with the `document` fact; author the rule and the example node, with an explicit evidence gap until the checks exist; regenerate; add the generation controls. The command does not land without the contract's statement of it. Done when `--tree-check` and `--check --require-history` pass and `tests/run.sh --suite unit --suite source_drift` passes outside the automation sandbox.

**Step 2. Signed build and CLI checks.** Build through the signed pipeline, then add the usage rows and cross-build controls. Done when `tests/run.sh --suite integration` passes against that build.

**Step 3. The round trip.** Write the checker, its offline controls and the live case; register both; update the suite accounts. Done when both cases pass by `--case` against the step 2 build with a fresh `PW_TEST_OUT_DIR`, and the control case's completeness assertion accounts for every assertion identifier through matched expected diagnostics or documented other evidence under section 4.7.

**Evaluation point.** Stop here and present the first complete result before anything else is built on it: the emitted document, the version envelope, the run envelope, the refusal inputs and outputs, and the checker's report with its groups. Before presenting, run the live case ten times against the same build, each with a fresh output directory, and report every assertion's result and each failure's disposition under section 4.6. This is a bounded evaluation sample; do not restart it to obtain ten consecutive passes. Record subsequent corrective or replacement runs separately, including changes to their inputs, build or operating conditions.

Passing tests are necessary here and not sufficient. Failures awaiting a disposition under section 4.6 leave evaluation pending and prevent step 4. The maintainer decides, on these criteria.

*Accept, and go on to step 4, when all of these hold:*

- The two commands in section 1 work from the usage text alone.
- The passage is direct: the command's output comes from the one constant through the functions `run` uses, with no intermediate copy, generated source or build step, and the fixed-point assertions pass.
- The fixtures author no specimen. The live case contains no document, and what it knows about the document is limited to the bounds on what it will run and the native expectations pinned to the present example.
- The checker restates no interpretive rule that the consumer or the controller already owns.
- Nothing answers whether PolicyWitness accepts a shape except `run`.
- The final build has a complete passing live case, and every earlier failed assertion has a disposition supported by section 4.6. Different values supported by each reply's evidence do not themselves fail evaluation.
- A deliberately faulted input produces a diagnostic that names the assertion and the classification without a reader opening the checker.
- Nothing in section 5's not-touched list changed, the free-text baseline did not grow, and no harness machinery was added.

*Revise, keeping the design, when:*

- An assertion compares the envelope only with itself, or duplicates a consumer rule.
- The usage text, exit statuses or printed form are awkward in use.
- The report blurs consistency and native observations, or a failure is hard to attribute from the report.
- Evidence establishes a checker defect or a concrete condition requiring correction to a native expectation's applicability. Make and verify that correction under section 4.6; variation alone does not establish incomplete prerequisites.
- The work needed an evidence gap or a deviation from this plan that the maintainer has not seen.

*Stop, and reconsider the design, when:*

- A not-touched component had to change.
- The printed document is not a fixed point of `run`: the controller adds, removes or reorders something between the user's file and the client. That is a finding about `run` and comes before this plan.
- The case could pass only by carrying a specimen of its own or by re-running a production classifier.
- The work called for a second way to ask what `run` answers.
- The rule cannot be authored without free-text growth and the maintainer does not want the baseline raised.

**Recording the decision.** In the commit that completes step 3, the executor adds an "Evaluation record" section to this plan: the build identity and commit, the run identifiers with their availability (development evidence, disposable), the control case's verified coverage, the ten-run comparison, each failed assertion with its relevant observation and disposition, any correction and replacement run, and every deviation from the plan. The maintainer's decision goes into that section in its own commit, in the maintainer's words: accept, revise with the changes listed, or stop with the reason. Step 4 does not begin before that commit exists.

Continue the same record through section 9. For each later disposition, append the verification stage, case and failed assertion, failed and replacement run identifiers, applicable build identities, supporting observation and disposition. Commit the evidence update even when no product correction was needed. Later entries preserve the step 3 decision and make subsequent verification available for candidate review.

**Step 4. Support and accounts.** Replace the evidence gap with owners that cite the constant, the emitter and the checks, with their limits stated; regenerate. Owner metadata is outside the public payload and nothing here touches `controller/src`, so the build identity must be unchanged by this step. Confirm that it is.

**Step 5. Candidate verification** (section 9).

## 7. Anticipated failure modes

| Failure | Sign | Response |
| --- | --- | --- |
| The automation sandbox refuses XPC lookup, signing or native-builder queries | `xpc_error`, an empty keychain listing, refused `sysctl` reads | Follow the repository's sandboxed-harness guidance: rerun the same command once outside the sandbox, unchanged. Do not weaken the case |
| The app predates an example edit | The live case reports that the emitted document differs from the contract's rendering | Rebuild. This is the intended stale-app refusal |
| The strict extraction is defeated by ordinary Rust formatting | Generation refuses a valid constant | Keep the constant in the one form the reader accepts and say so beside it; do not widen the reader into a Rust parser |
| The rule needs a `free.*` fact | Generation refuses free-text growth | Restructure the rule; otherwise stop and raise it |
| The host refuses the example | The live case fails at admission with a `request_failure` | The example is invalid for this build. Fix the constant; do not relax admission |
| A target is unreadable or absent | The case fails as `prerequisite_unestablished` | Section 4.6's release consequence. Do not hand the case another document |
| The prediction is unavailable with a valid recorded spawn failure or timeout | The case fails as `native_observation` while consistency passes | Apply section 4.6's earlier-run rules: a complete passing run can supersede the trial without diagnosing the underlying OS cause |
| The prediction is `deny` or `open_read` fails with prerequisites established | The case fails as `native_observation` while consistency passes | Resolve the challenge to the native expectation under section 4.6; later successes alone do not settle it |
| A passing checker that checks nothing or rejects for the wrong reason | The offline controls accept a faulted input or its diagnostics differ from the expected set | Match each control's intended diagnostics and classification before crediting coverage; preserve independent combined faults and check unevaluated groups |
| The case passes against a release-form identity only by string luck | The identity-form assertions never see a `release:` value | Covered at candidate entry by the nested acceptance, whose fixture reports a release identity |
| The checker grows back into a second specification | New assertions about ordering, vocabulary or outcome mapping appear in it | They belong to the consumer. Add them there with its controls, or not at all |
| The dispatcher's inventory differs after the case | Artifact-integrity failure | The command wrote into the app; it must not. Fix the command |

## 8. Acceptance criteria

1. In the `unreleased` stamp state, `generate_contract_stamps.py --check --require-history` passes, and a second generation writes nothing.
2. A signed development build of the final source prints, for `example`, a document whose `contract` equals `--version`'s `build.contract` and the app's `PWContract`. `run` on those bytes is admitted, delivers a request of the same length, and exits 0 with `finished`.
3. `witness_contract/example_round_trip` and `example_round_trip_controls` pass inside a complete default battery with no skips, unrun cases or harness errors, and with the app inventory unchanged. The live case's artifacts hold the emitted bytes, the version envelope, the run envelope, every refusal input and output, the target-file observations, and a report giving each assertion's result and each failure's identifier and classification, consistency apart from native observations. The offline case retains expected and actual diagnostic sets and verified coverage under section 4.7.
4. Each refusal control in section 4.5 produces its stated code, path and expected identity through `run`, and the controller-side controls show no client capture.
5. The cross-build controls pass: the unbound build emits nothing and exits 2; the signed app refuses a document emitted under another identity.
6. The generation controls pass: an example edit is refused until regeneration and then moves the rendering, the stamp and the build identity.
7. The contract's rendered example equals the app's emitted document without its identity.
8. Every component in section 5's not-touched list, and the worker identity, are unchanged from the starting commit.
9. The repository contains one definition of the example. No test, fixture or document holds a copy that is not extracted from it.

## 9. Entering the 0.3.8 candidate

Earlier pre-tag evidence does not carry over. This work changes the CLI, the build-identity inputs, the contract tree and its generator, so the rehearsals recorded for `8435e5d3` describe a different build. The following are required on the final source, in the `unreleased` state, before the work is treated as part of the candidate:

1. A signed development build, and a complete default battery against it (about half an hour on this machine as of 2026-11-11).
2. The complete `preflight/build_refusal_controls` rehearsal (about two and a quarter hours), because the generator and its inputs changed. Its nested extracted-ZIP acceptance runs the default battery, including the new live case, against a fixture that reports a `release:` identity. That run is this plan's evidence for the release form; record the identity the case saw.
3. A reviewed applicability statement for `witness_contract/order_barrier_mutations`: it is not required if the worker wait, release store and eligibility rule are untouched, which criterion 8 and an unchanged worker identity support. State this as a judgment, not as a mechanical fact.
4. Confirm that the evaluation record includes the candidate battery and rehearsal results and all later dispositions, with their replacement runs. Commit any outstanding evidence update, including when no product correction was needed. Then prepare again: `generate_contract_stamps.py --release v0.3.8 --require-history`, changing only the two stamp tables and the snapshot history; confirm that the ordinary check gives exactly the expected missing-tag refusal; run the same prepared-commit checks as before (baselines against `v0.3.7`, footprint attribution).
5. Revise the prepared notes in [RELEASE-NOTES-v0.3.8.md](../records/contract/RELEASE-NOTES-v0.3.8.md): the `request` row gains an additive command, and the verification paragraph cites the new runs with their scopes.

The plan ends at that prepared, untagged state with the maintainer's review pending. Its disposition-recording procedure covers this untagged candidate work; it does not alter the [tagged-release checkpoint rules](../records/contract/RELEASE-INPUTS.md#checkpoint-rules-the-release-procedure-does-not-state), including restrictions on working-tree writes and the correcting-commit procedure. Tagging, the tagged rehearsal, notarization and publication are separate decisions and are not steps here. If the maintainer prefers to tag 0.3.8 without this work, steps 0 to 4 can equally sit on a branch of the `unreleased` state; nothing in the design depends on the release number.

## 10. Commitments

**Settled with the maintainer on 2026-11-12.**

| Commitment | What it means in practice |
| --- | --- |
| One way to hold PolicyWitness | No admission query or second submission path, here or later on this route. `example` answers nothing about a caller's document |
| The app is the authority for the example | One definition in controller source; the contract extracts it; tests obtain it from the built app |
| The entrance promises one thing | The emitting build admits what it prints. Content, layout and labels can change in any build. The earlier name and scenario promise, and the convention that `specimen_id` names a contract node, are withdrawn |
| Every failure to emit is exit 2 with no usable document | Usage errors, an unbound build, a failed gate and a failed write share one status; the reason is stderr text |

**To confirm before step 1.** Each creates behavior a caller can see.

| Distinction | Why it matters | Commitment |
| --- | --- | --- |
| The command prints a bare specimen, in the controller's held serialization, not an envelope | It is the first controller output that is not an envelope, and its key order is the serializer's, not an author's | `example` output is a request document; envelopes remain the form of every report |
| The command is listed in usage and stated in the contract, and absent from the user guide | A reader of the guide alone does not learn of it; a reader of `--help` does | The entrance is disclosed where the CLI is defined and is not presented as a workflow in this release |
| Native expectations fail the case when their prerequisites hold | A machine where `sandbox_check` gives no answer for this read fails the default battery and release acceptance, subject to section 4.6's dispositions | The battery asserts the native result only under observed prerequisites, and reports it apart from consistency |

## 11. Where this stops, and the route onward

Out of scope: more than one example, selection by name, external runner examples, expected-refusal examples, response fixtures, any documentation interface, and any query other than `run`.

Later steps on this route keep the same direction, from code to presentation:

- **The guide and README.** Their hand-substituted `BUILD_CONTRACT` examples can shrink to the two commands in section 1 once the entrance is presented to users. That is the point at which the promise in section 10 is reconsidered.
- **The verify request.** `verify_request()` and the contract's `apply_only` example are a second code definition and a hand-typed document for one more specimen the app originates. They can move into the same module and the same extraction.
- **A second example.** It needs a way to select among examples and, with that, a statement of what a selection denotes across releases. Neither is designed here.
- **Refusal examples.** A document the app prints so that `run` refuses it would let refusal guidance come from the app as well. Its expected outcome is obtained by running it, in keeping with section 2.
- **Support grade.** After an archived release acceptance includes the live case, the example's owner can move from `check_read` to release credit naming that release and case.
