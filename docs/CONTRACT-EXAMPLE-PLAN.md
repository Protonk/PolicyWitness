# Contract example conformance plan

This plan adds the first executable entrance to the public contract: a signed PolicyWitness application emits one contract-bound specimen through its own CLI, that same application runs it, and an independent test checks selected public relationships in the resulting envelope. It follows the completed four-stage contract work, whose remaining release inputs are in [RELEASE-INPUTS.md](../records/contract/RELEASE-INPUTS.md), and targets the 0.3.8 candidate, without making the tag or publication an outcome.

The plan is written for an executor who knows the repository but not the planning conversation. Sections 2 and 3 record what was inspected and decided; sections 4 to 8 say what to build, in what order, and how to tell it is done; section 9 lists the public commitments the design creates, for the maintainer to confirm before controller work starts.

## 1. Intended result

```sh
PW=/Applications/PolicyWitness.app/Contents/MacOS/policy-witness
$PW example paired-probe > /tmp/paired-probe.json
$PW run /tmp/paired-probe.json > /tmp/result.json
```

- The first command prints a complete specimen. Its `contract` member is the emitting binary's own public identity, and its remaining members come from one authored example node in the contract tree.
- The second command admits and executes those exact bytes.
- A default-battery case obtains the specimen from the selected signed app, submits it to that app, retains every input and output, and checks request admission, producer identity, step association, the two observation channels and the ordering evidence, with single-change controls that must be refused.

This is a product capability with a test. It is not a contract browser, an examples catalog or a documentation interface.

## 2. Starting state

These observations were made on `main` at `e5d7488b` on 2026-11-12. Re-check any that the work depends on.

**The checkout is prepared for `v0.3.8` and has no `v0.3.8` tag.** The two stamp tables and [contract/public.json](contract/public.json) claim `v0.3.8`. `tests/lib/python.sh docs/generate_contract_stamps.py --check` therefore exits 1 with `release history unavailable; restore annotated release tags: v0.3.8`. Because [build.sh](../build.sh) runs that check before compiling, `make build` refuses in this state, and ordinary generation without `--release` refuses too (`require_available_history` in [contract/runtime.py](contract/runtime.py)). Generation with `--release v0.3.8` works. The earlier pre-tag work alternated between the two states: `d18d4925` returned the stamps to `unreleased` so the tree could be built and tested, and `6f65612b` prepared them again. This plan uses the same alternation (step 0 and section 8).

**Identity.** [build_contract.py](build_contract.py) derives `release:vX.Y.Z` only for a clean checkout at a single annotated release tag whose selected bytes equal the tag's blobs, and `development:<sha256>` otherwise. The digest covers `.rs`, `.c`, `.h`, `.swift`, `.sb`, `.plist` and `.ent` files under `controller/src`, `controller/tools` and four `runner/` directories, plus a fixed file list that includes `build.sh`. `build.sh` passes the value to Cargo as `PW_BUILD_CONTRACT`, stamps it into both property lists as `PWContract`, and recomputes it before signing. [json_contract.rs](../controller/src/json_contract.rs) embeds it as `BUILD_CONTRACT`; a plain Cargo build is `unbound`, and unit tests use `test:policy-witness`.

**Admission.** `validate_contract` in [request_patch.rs](../controller/src/request_patch.rs) requires `contract` to equal the binary's identity exactly and refuses when that identity is empty or `unbound`. The controller applies this before selector parsing, augmentation or any client invocation; the refusal is exit 1, `bad_request`, with `data.request_failure` carrying `code`, `path` and `expected_contract`. The host checks the contract again before other request fields.

**CLI.** [cli.rs](../controller/src/cli.rs) dispatches `run`, `runner` and `--version`. Every current output is an envelope. `run` reads a file path with `read_to_string`; there is no standard-input form.

**Contract tree.** Example nodes exist (`request.specimen.apply_only`, `probes.step.read_hosts` and fourteen others). They carry prose and support, and no kind-specific facts: `FACTS_BY_KIND['example']` in [contract/tree.py](contract/tree.py) is empty, though the common facts, including `uses`, are accepted. A node's facts enter the canonical public payload unless excluded, so they move the surface stamp. Strict loading requires every rule and example to have graded support or an explicit evidence gap. Every imported record has exactly one authored subject; `PWRunnerRunSpec` belongs to `request.specimen`. Generation refuses growth in `free.*` relationship counts ([contract/free_text.json](contract/free_text.json)).

**Generators.** [generate_contract_stamps.py](generate_contract_stamps.py) owns [CONTRACT.md](CONTRACT.md), the guide's stamp table, the public snapshot, the free-text baseline and the shape goldens. A generated Rust source already exists as precedent: `controller/src/porcelain_records.rs`, written by `generate_porcelain.py` and declared with `#[rustfmt::skip]` in [main.rs](../controller/src/main.rs). The [generator contracts](../tests/suites/source_drift/README.md#generator-contracts) (one owner per output, idempotence, check mode before signing) are enforced by `source_drift`.

**Readers and harness.** [consumer.py](../tests/lib/consumer.py) validates an envelope against the shape goldens and record rules without consulting specimen policy or production classifiers; its `eligible_order` re-derives whether a step's evidence supports `query_first`. [build_context.py](../tests/lib/build_context.py) reads the candidate identity from the app's `Info.plist`. [run_capture.py](../tests/lib/run_capture.py) serializes a specimen from a Python value, so it cannot submit bytes unchanged. Release acceptance runs the default battery with no selectors against the extracted ZIP ([SIGNING.md](SIGNING.md#release-procedure)); a default case therefore joins acceptance with no further wiring. The opt-in `preflight/build_refusal_controls` rehearsal builds a disposable tagged fixture that reports `release:v1.0.0` and runs the full default battery against its extracted ZIP.

## 3. Design

### 3.1 What the CLI exposes

```text
policy-witness example <name>
```

The MVP defines one name, `paired-probe`.

| Invocation | stdout | stderr | Exit |
| --- | --- | --- | --- |
| `example paired-probe` on a bound build | The specimen document and one trailing newline, nothing else | empty | 0 |
| `example` with no name, an unknown name, or extra arguments | empty | Usage naming the available example names | 2 |
| `example paired-probe` when the binary's identity is empty or `unbound` | empty | One line stating that this build has no public identity | 2 |

The command reads no file, resolves no app root, loads no manifest or registry and launches nothing. Its output is a function of the binary. `print_usage` gains the command; that listing and the usage error are the whole of its discoverability.

**The output is the specimen itself, not an envelope.** The specimen already carries the identity in `contract`, which is where the contract says a specimen carries it. `run` takes a file, so redirecting stdout yields a submittable file with no extraction tool. An envelope would need a JSON tool to unwrap, and would add an envelope kind to the shape goldens for no added binding.

**Refusing on an unbound build** keeps the command from printing a document that no build can admit. The emitter enforces this by construction: it renders the document, parses it with `parse_request`, applies `validate_request_contract`, and prints only on success. The binary never emits a specimen its own controller gate would refuse.

Rejected alternatives: `policy-witness contract ...` (invites the browser this plan excludes); a `--list` flag or an envelope describing examples (a catalog); emitting to a path argument (adds file-writing behavior and an overwrite decision to a read-only command).

### 3.2 Where the example originates

One authored node supplies the scenario. The node sits in the tree that defines the commitments it exercises, so there is no second specification to maintain.

**Authoring.** Add an example node beside `apply_only` in [10-request.surface.md](contract/10-request.surface.md), full identifier `request.specimen.paired_probe`, with two new example facts and the existing `uses` fact:

````markdown
### Paired read probe {paired_probe: example}

```contract
emit: "paired-probe"
specimen: {"policy":{"format":"sbpl","sbpl_source":"(version 1) (allow default)"},"probe_plan":[{"step_id":"read-hosts","sandbox_check":{"operation":"file-read-data","filter":{"kind":"path","value":"/etc/hosts"}},"attempt":{"kind":"file","action":"open_read","target":"/etc/hosts"}}]}
uses: ["identity.public.contract", "request.specimen.contract", "identity.producer.contract", "steps.step", "steps.query", "steps.attempt", "steps.comparison", "steps.assessment.order"]
```
````

- `specimen` is identity-free and label-free. Two members are derived, each from its own authority: the controller supplies `contract` from the binary, and the generator supplies `specimen_id` as the node's full identifier. An envelope produced from the emitted example therefore names the contract node that defines it in `runner_result.specimen_id`, with no new field.
- `uses` names the public definitions and rules that execution of the example is checked against. It is the existing relationship, so referenced nodes already flow into the surface's public payload. The list above is the intended selection. The executor settles it in step 4 under the coverage rule in section 3.4, and the maintainer reviews it at the evaluation point.
- The existing step fragment `probes.step.read_hosts` stays as it is.

The policy is `(allow default)` and the one probe is the read of `/etc/hosts` already used by the contract's teaching example. It writes nothing, needs no fixture, and makes no claim about a policy's effect. The deny variant is the README example and `smoke/specimen_file_read_deny`.

**Tree rules** (in `tree.py`, strict and preview alike unless noted):

- `emit` and `specimen` appear together or not at all. `emit` matches `[a-z][a-z0-9-]*` and is unique across the tree.
- `specimen` is a JSON object. It refuses the members `contract` and `specimen_id` (derived), `_test_overrides`, and the controller selection keys already collected from `runner_select.rs`. Its top-level members must be fields of the imported `PWRunnerRunSpec`. Deeper validity belongs to the host and is established by execution.
- The renderer prints the complete document for the reader (`contract` shown as `<reported-contract>`, then `specimen_id`, then the authored members in authored order) and the command that emits it. The fact replaces a prose JSON block; it does not sit beside one.

Add one rule under the same subject, `request.specimen.emit_example {emit_example: reports}`, stating the command's commitments as structured effects: who (`identity.definitions.controller`), entry (`cli_example`), recipient, report, and `set_value(specimen.contract, ref("identity.build.contract"))`. Author it without `free.*` facts; the free-text baseline refuses growth. If a free relationship proves unavoidable, stop and raise it rather than raising the baseline. No new subject or record is needed, so no shape golden changes.

**What the generator produces.** `generate_contract_stamps.py` gains one whole-file output, `controller/src/contract_examples.rs`. For each emitting example it holds exactly the emit name, the node identifier, and the document text before and after the `contract` value. It holds no title, prose or support. The consequences are deliberate:

- The file has the `.rs` suffix under `controller/src`, so it is a build-identity input with no change to `build_contract.py`. Editing the emitted example changes the `development:` digest and fails the release byte comparison.
- Editing any other contract prose leaves the file, and so the build identity, unchanged.
- The stale-copy check that `build.sh` already runs before compiling covers the file, and so does the existing refusal `stale generated contract: <copies>`. `build.sh` does not change. That matters twice: `build.sh` is an input to both the build identity and the worker identity, and an unchanged `build.sh` keeps the build account in [build.json](build.json) and the worker identity as they are.

Register the output wherever the generator's outputs are enumerated: `render` and both branches of `check` in `runtime.py`, `input_paths`, and `region_ownership` in [generators.py](../tests/suites/source_drift/generators.py).

**What the CLI embeds.** The controller declares `#[rustfmt::skip] mod contract_examples;` and renders `before + serde_json::to_string(BUILD_CONTRACT) + after`. Splicing a JSON-encoded string keeps authored member order and stays correct for any supplied identity spelling. Nothing is read at run time.

**What the build packages.** Nothing new. The material lives in `Contents/MacOS/policy-witness`, covered by that executable's signature and the app seal. Two alternatives were set aside. A resource under `Contents/Resources/` (as augments are packaged) adds a run-time read, a bundle inventory entry and an identity suffix, and lets the resource and the binary's identity come apart. `include_str!` of a file under `docs/` makes a path outside the identity directories a compiler input.

**Identities and stale artifacts.**

| Concern | Mechanism |
| --- | --- |
| Development build | `contract` is `development:<sha256>`; the digest includes the generated example source. |
| Release build | `contract` is `release:vX.Y.Z`; the release form requires the generated source to equal the tag's blob. |
| Authored example edited, not regenerated | `--check` refuses before compilation and in `source_drift`. |
| Generated source edited by hand | The same check refuses. |
| Identity input edited during a build | The existing pre-sign recomputation refuses. |
| Example changed between releases | The `request` surface payload changes, its stamp becomes `unreleased`, and release preflight refuses remaining `unreleased` rows. |
| Specimen saved from another build | Exact identity admission refuses it with `unsupported_contract` and names the expected identity. |

One property to know: the public snapshot sorts object keys, so reordering members inside `specimen` changes the emitted bytes and the build identity but not the surface payload.

### 3.3 What execution must demonstrate

The emitted document is called `S` below, and `E` is the run envelope for `S`. Commitments are named by contract node so the checker and the example's `uses` list can be compared.

**Contract relationships.** These hold for any run of `S` that the app completes, whatever the native results.

| Group | Relationship checked | Contract node |
| --- | --- | --- |
| Emission | `S.contract` equals `--version` `build.contract` and `data.contract`, and the independently read `PWContract`; it has the packaged `release:` or `development:` form; two emissions are byte-identical | `identity.public.contract`, `request.specimen.emit_example` |
| Emission | `S.specimen_id` is `request.specimen.paired_probe`; the remaining members equal the authored `specimen` fact | `request.specimen.paired_probe` |
| Admission | The submitted file's bytes are `S`; exit 0; `kind` is `run`; `result.ok` is true; `normalized_outcome` is `finished`; no `request_failure`; the dossier's `policy.augmentation.original_sha256` and the reply's `policy_sha256` equal the SHA-256 of `S`'s policy source | `request.specimen.contract`, `request.specimen.hold` |
| Producer identity | `E.build.contract`, `data.runner_client.transport.contract` and `runner_result.producer.contract` each equal `S.contract` | `identity.build.contract`, `identity.producer.contract` |
| Step association | `runner_result.specimen_id` equals `S.specimen_id`; `steps` has exactly the submitted step identifiers in order; the step's `phase_id` is `main` and that phase's `action_ids` name it; the query echoes the submitted operation and filter; the attempt echoes the submitted kind, action and target | `steps.step`, `steps.query`, `steps.attempt` |
| Two channels | The step has a `sandbox_check` and an `attempt`, each with its `result_source`, and a comparison record in the closed vocabulary; `operation_relation` is `matched` and `target_relation` is `same_submitted`, which follow from the submitted strings | `steps.comparison` |
| Ordering | `comparison.order` is `query_first` exactly when the reply's own evidence supports it (collection chain, setup, native answer, unique validator association), and `unestablished` otherwise; the shared consumer reports no shape or record errors | `steps.assessment.order` |

The ordering row is a biconditional over the envelope's evidence. It does not assert that this run established order.

**Native observations.** These depend on the machine. The case states its prerequisites and observes them itself: the built-in runner, an allow-default policy, and `/etc/hosts` resolving to a regular file the test user can open and read.

| Observation | Expectation under the prerequisites |
| --- | --- |
| Prediction | `result_source` is `validator`, `outcome` is `allow`, `native_rc` is 0 |
| Order | Given that prediction, the phase's ordering record shows the complete chain with `validator_disposition` `reaped`, and `order` is `query_first` |
| Attempt | `outcome` is `ok`, `rc` is 0; the comparison's `observation` is `succeeded` with basis `completed_worker_status` |
| Effect | The target's bytes and metadata, read by the test before and after, are unchanged |

Nothing in either group states that prediction and enforcement agree.

**Status and classification.** The case has two statuses, pass and fail. It declares no skip, and the dispatcher's equipment check does not cover these prerequisites, so no row below is an unrun case. The report's classification carries the distinction the status cannot.

| Situation | Contract relationships | Native expectations | Status | Classification |
| --- | --- | --- | --- | --- |
| Everything holds | Evaluated, passing | Evaluated, passing | pass | none |
| A contract relationship fails, at emission, admission or in the reply | Evaluated, failing | Evaluated when their prerequisites hold | fail | `contract_relationship` |
| The run yields no admitted reply (service unreachable, tool error) | Emission and controller-side relationships only; nothing is credited or faulted from the missing reply | Not evaluated | fail | `execution_unavailable` |
| A target prerequisite is not observed | Evaluated; they do not depend on it | Not evaluated | fail | `prerequisite_unestablished` |
| Prerequisites hold and a native expectation fails | Evaluated, passing | Evaluated, failing | fail | `native_observation` |

More than one classification can apply, and the report lists each.

**Release consequence.** Every failing row fails the default battery and therefore release acceptance; that attempt produces no archive. The classification says where the remedy lies, not whether the release may proceed:

- `contract_relationship` is a defect in the product, the contract or the checker. Fix it where it lives; a product or example fix is new shipped source and a new build.
- `execution_unavailable` locates missing execution evidence without assigning a cause. For an observed automation-sandbox refusal, follow the repository's sandboxed-harness guidance: rerun the same command once outside it with the artifact unchanged. A passing rerun supports that explanation and is the run that gets credited.
- `prerequisite_unestablished` is not a PolicyWitness result. The machine cannot run this example's native check, and acceptance belongs on one that can.
- `native_observation` is an observation about this machine or build. Retain the evidence without assigning a cause; the rules below determine whether acceptance needs a correction or a fresh qualifying run.

In no row is the case removed from the default battery, given a skip, or pointed at another target to obtain a pass. Changing the target changes the public example and the build identity, which is a design change for the maintainer.

**Earlier runs and variation.** A failed run remains failed. The following rules determine which earlier failures a fresh qualifying run can supersede and which remain objections to acceptance. They do not change the case's assertions or statuses, add automatic retries, or replace the complete passing default battery required by section 7. Review every failed assertion separately: an interruption does not excuse an independent identity, association or ordering defect.

| Earlier observation | Required disposition |
| --- | --- |
| One reply reports `query_first` and another `unestablished`, each supported by its own evidence | Evaluate the ordering biconditional in each reply. The difference needs no explanation for contract conformance. The latter run still fails the native ordering expectation; apply the remaining rows to that failure. |
| A target prerequisite was not observed, the dispatcher recorded system sleep overlapping the failure, or an automation-sandbox refusal was confirmed by the prescribed unchanged-artifact rerun | Record that exclusion and credit a fresh run that establishes the prerequisites and completes without it. Explaining why the target was unavailable, the machine slept or the harness imposed the restriction is unnecessary. Use the existing dispatcher sleep record and sandboxed-harness procedure. |
| The validator produced no answer, with a valid recorded spawn failure or timeout and honest `unestablished` ordering | A complete passing run can supersede this trial without explaining the underlying scheduling or OS cause. The earlier run supplies no successful native-observation credit. Its available evidence must satisfy the contract relationships; a generic error without evidence locating the failure does not establish this disposition. |
| The validator answered `deny`, or the worker failed `open_read`, while the stated prerequisites were observed | Resolve the challenge to the native expectation through a justified correction to its applicability, a checker correction or a product fix. Later successes alone do not settle it. |
| A producer identity, policy digest or step association is wrong, or `query_first` lacks supporting evidence | Resolve the product, checker or contract discrepancy before acceptance. These relationships must hold even when native execution fails. |

The example must demonstrate successful execution. This work does not require an explanation of every correctly reported inability to execute. A failure without a disposition supported by this table leaves evaluation pending, including a native discrepancy that the table does not cover. Do not infer an exclusion from a later pass or classify every `execution_unavailable` result as environmental.

For failures requiring a correction, the evidence needed to close the issue is bounded:

- **Checker defect:** replay the retained failing input through the corrected checker and show that the affected assertion's rejected control still works. Reproducing the original live event is unnecessary.
- **Product defect:** identify the faulty behavior and establish its correction with a focused control and the applicable verification. Explaining precisely why it occurred intermittently is unnecessary. Changes to section 4's not-touched components remain separate work.
- **Incorrect prerequisite or expectation:** identify the concrete condition that changes applicability and how the case observes it. Passing after a reboot alone does not establish that condition.

Record the failed assertion, the relevant retained observation and its disposition in the evaluation record, with any correction and replacement run. A new build identity or ten later passes is not itself a disposition; name the relevant change. Preserve original results under the repository's evidence-retention rules rather than rewriting a failed historical run as passing.

### 3.4 How conformity is independently established

One live case and one offline control case, both in `witness_contract`.

**`witness_contract/emitted_example_conformance`** (default; requires the app). A shell case in the style of the smoke case runs the selected app directly and retains raw stdout, stderr and exit status for every invocation: `--version`, two emissions, the run of the emitted bytes, and each refusal control. A Python checker then reads the retained files. The emitted bytes are submitted unchanged; the case does not route them through `RunCapture`.

The checker's oracles are separate from the generated material:

- Its relationship assertions are written by hand against the envelope and keyed by contract node identifier. It uses `consumer.validate` and `consumer.eligible_order` as shared readers and adds the relationships above itself.
- It pins the scenario's intent by hand: exactly one step, a read-only attempt action, no test overrides, no runner selection.
- It compares the emitted members with the authored `specimen` fact, read from the surface file. This is a comparison, never a substitution: a mismatch means the app does not contain the tree's example (a stale app fails here, as a stale worker identity already fails the smoke case).
- It makes its own observations of the target file and reads `PWContract` itself.

**`witness_contract/emitted_example_checker_controls`** (default; offline). Every assertion that can fail the live case has an identifier in the checker. All of the checker's inputs are retained files, so every assertion can be handed a constructed input that violates it. The rule is that each assertion has at least one rejected control with its own diagnostic, unless the suite account lists it as resting on other evidence and says why. The control case ends with a completeness assertion over the checker's own table of identifiers, so an assertion added without a control fails the case. Build the inputs from the existing constructed-envelope helpers in [blackbox.py](../tests/lib/blackbox.py) and the reply fixtures under `tests/fixtures/contract/`; the case generates no replacement fixtures.

| Group | Rejected controls required |
| --- | --- |
| Emission | The version identity differs; the plist identity differs; the identity is not in a packaged form; two emissions differ; `specimen_id` is not the node identifier; a member differs from the authored fact |
| Intent | A write action; test overrides; a runner selector; a second step |
| Admission | Submitted bytes differ from the emitted bytes; a nonzero exit; a `request_failure`; each policy digest differing |
| Producer identity | Each of the three identities differing, separately |
| Step association | The echoed `specimen_id` differs; an extra, missing or renamed step; the phase or its `action_ids` disagree; the query echo differs; the attempt echo differs |
| Two channels | A missing channel; a comparison value outside the vocabulary; each relation mismatched |
| Ordering | `query_first` without the supporting chain; `unestablished` despite a complete chain |
| Native | A prediction other than `allow`, an attempt that failed and a changed target, each with prerequisites held: the result must be `native_observation` with contract relationships still passing. An unobserved prerequisite: the result must be `prerequisite_unestablished` with native expectations not evaluated |
| Refusals | For each refusal control: an accepted run in its place; the wrong code; a missing or wrong expected identity; a client capture on a controller-side refusal |
| Classification | A combined-fault input reports every fault; an input with no admitted reply is `execution_unavailable` and credits or faults nothing from the reply |

Three things rest on other evidence, and the suite account says so:

- Shape and record validity come from `consumer.validate`, whose rejected controls belong to `blackbox_e2e/checker_controls`. This case adds one control showing that a consumer error fails the case.
- That the app is validly signed and unchanged comes from the dispatcher's inspection and inventory, controlled in the `dispatcher` suite.
- The usage matrix, the cross-build controls and the generation controls are direct assertions on real binaries and source copies. They are not a checker over retained documents, and each already pairs a passing case with refused ones.

**Coverage statement.** The `uses` list in section 3.2 is the intended selection, and it becomes final in step 4. The suite README then carries one row for each final entry: the relationship asserted, the assertion identifier, its rejected controls, and the limit of what the assertion establishes. A node enters `uses` only if it has such a row, and the row names the relationship, never the whole node. Limits known now: one specimen, one policy, one target and one platform; a reference to a subject such as `steps.attempt` covers the echo and channel relationships listed, not every field's meaning; the policy digests show that the dossier and the reply describe the submitted source, not that the request was read and serialized once.

**Refusal controls in the live case.** Each starts from the emitted bytes and makes exactly one change. The unmodified bytes pass in the same case, so each refusal is attributable to its change.

| Control | Change | Required result |
| --- | --- | --- |
| Other development build | One hexadecimal digit of a `development:` identity changed (or a well-formed `development:` identity substituted when the app is a release build) | Exit 1, `bad_request`, `request_failure` with code `unsupported_contract`, path `["contract"]` and `expected_contract` equal to the app's identity; no client capture and no runner reply |
| Other release | `contract` set to `release:v0.0.0` | The same |
| Unbound | `contract` set to `unbound` | The same |
| Absent identity | `contract` removed | Code `missing_field`, the same path and expected identity |
| Truncated document | Final byte of the object removed | Code `invalid_json`; no client capture |
| Unknown member | One unknown top-level member added, identity intact | Exit 1, `bad_request` from the host with code `unknown_field` and a path naming the member, the form the request corpus pins for a nested member; no step results |

The first five stop at the controller and need no XPC. The last shows that a correct identity does not carry an invalid document past the host.

**Cross-build controls** extend [cli_contract.rs](../controller/integration/cli_contract.rs), which already builds isolated non-test controllers with supplied and absent stamps: the unbound build's `example paired-probe` exits 2 with empty stdout; the build given another identity emits that identity, and the signed app refuses the resulting specimen with `unsupported_contract` and its own expected identity. The same file takes the usage matrix of section 3.1 against the signed app.

**Generation controls** go in the existing `source_drift` cases, over disposable source copies:

- An authored `specimen` edited without regeneration is refused by `--check`, which names the generated source and writes nothing; a hand edit of the generated source is refused the same way.
- After regeneration, the generated source differs, `build_contract.identity` differs and the `request` surface payload differs.
- An edit to unrelated contract prose leaves the generated source and the build identity unchanged.
- Invalid examples are refused with their source line: a specimen carrying `contract`, `specimen_id`, `_test_overrides` or a selection key; a non-object; an unknown top-level member; `emit` without `specimen` and the reverse; a duplicate or malformed name.
- A drift rule compares the checker's commitment identifiers with the example's `uses` list, so neither can drop a commitment alone.

**Unit tests** in the controller cover the renderer (identity spliced as JSON, including a spelling that needs escaping), the self-admission gate, the unbound and empty refusals, and dispatch.

### 3.5 Test boundary

| Stage | What is checked | Equipment | Home |
| --- | --- | --- | --- |
| Generation | Tree rules, stale and hand-edited copies, identity and stamp sensitivity, stability under unrelated edits, checker and `uses` agreement | Python | `source_drift` (existing cases) |
| Compilation | Rendering, self-admission, refusals, dispatch | Cargo | `unit/rust.unit`, `unit/rust.fmt` |
| Packaging | No new layout. Existing gates: generator check before compilation, identity recomputation before signing | Build toolchain and identity | `make build`; `preflight/build_refusal_controls` at candidate entry |
| Signed-app inspection | Usage matrix, emission, identity chain, agreement with the authored example, controller refusals, cross-build controls | Signed app; Cargo for the isolated builds; no XPC | `integration/cli.integration`; the live case |
| Checker | Passing and rejected constructed envelopes | Python | `witness_contract/emitted_example_checker_controls` |
| Actual execution | Admission, producer identity, association, channels, ordering, native observations, host refusal | Signed app and XPC | `witness_contract/emitted_example_conformance` |

Everything above the last row constructs a scenario or inspects an artifact. Only the last row observes native execution, and only its native-observation group depends on the machine.

Both new cases are default members: they are read-only, need no signing identity, GUI session or network, and add a handful of CLI invocations. Default membership is what places the live case in release acceptance. The dispatcher's app inspection and before-and-after inventory already establish that the tested app is validly signed and unchanged; no dispatcher, catalog schema or helper change is needed beyond registering the two cases.

## 4. Affected components

| Area | Files | Change |
| --- | --- | --- |
| Contract authoring | `docs/contract/10-request.surface.md` | Example node and emission rule, with support |
| Contract model | `docs/contract/tree.py`, `runtime.py`, `README.md`, `AGENTS.md`; `docs/generate_contract_stamps.py` | Example facts, their validation and rendering; the generated Rust output and its registration; authoring reference |
| Generated | `docs/CONTRACT.md`, `docs/contract/public.json`, `controller/src/contract_examples.rs` | Regenerated, never hand-edited |
| Controller | `controller/src/main.rs`, `cli.rs`, a small `example.rs`, `controller/README.md` | Module declaration, dispatch, renderer, unit tests, CLI block |
| Guide | `docs/PolicyWitness.md` | One row in the command table. No new workflow |
| Tests | `tests/catalog.json`; `tests/suites/witness_contract/` (two case scripts, one checker, README); `controller/integration/cli_contract.rs`; `tests/suites/source_drift/` (`contract_tree_controls.py`, `generators.py`, `build_contracts.py`, the drift rule); `tests/README.md`, `tests/COVERAGE.md` where applicable | Cases, controls, registry and suite accounts |
| Possibly | `docs/architecture.json` | Only if its account enumerates CLI entries; check and regenerate if so |

Not touched: `build.sh`, `meson.build`, `build_contract.py`, the bundle layout, the evidence manifest, the wire schema, the host, the worker, the validator and the dispatcher. A need to change any of these is a signal to stop and reconsider the design, not a routine extension.

## 5. Order of implementation

**Step 0. Return the stamps to `unreleased`.** Follow the `d18d4925` precedent so the tree can be generated, built and tested. Done when `generate_contract_stamps.py --check --require-history` passes and the three stamp artifacts are the only difference from `e5d7488b`.

**Step 1. Authoring model and generated source.** Extend the tree and runtime, author the example and rule (with an explicit evidence gap until the checks exist), regenerate, and add the generation controls. Done when `--tree-check` and `--check --require-history` pass and `tests/run.sh --suite source_drift` passes outside the automation sandbox.

**Confirm section 9 with the maintainer before step 2.** The commitments there shape the controller's public behavior.

**Step 2. Controller.** Add the module, renderer, dispatch, usage text, unit tests and README block. Done when `tests/run.sh --suite unit --suite source_drift` passes.

**Step 3. Signed build and CLI checks.** Build through the signed pipeline, then add the usage matrix and cross-build controls. Done when `tests/run.sh --suite integration` passes against that build.

**Step 4. Conformance.** Write the checker, its offline controls and the live case; register both; settle the final `uses` list and write the coverage statement in the suite account; add the `uses` drift rule. Done when both cases pass by `--case` against the step 3 build with a fresh `PW_TEST_OUT_DIR`, and the control case's completeness assertion covers every assertion identifier.

**Evaluation point.** Stop here and present the first complete result before anything else is built on it: the emitted specimen, the version envelope, the run envelope, the refusal inputs and outputs, the checker's report with its groups, and the coverage statement. Before presenting, run the live case ten times against the same build, each with a fresh output directory, and report every commitment's result and each failure's disposition under section 3.3. This is a bounded evaluation sample; do not restart it to obtain ten consecutive passes. Record subsequent corrective or replacement runs separately, including changes to their inputs, build or operating conditions. This is the point at which the capability can be judged on its own.

Passing tests are necessary here and not sufficient. Failures awaiting a disposition under section 3.3 leave evaluation pending and prevent step 5. The maintainer decides, on these criteria.

*Accept, and go on to step 5, when all of these hold:*

- The two commands in section 1 work from the usage text alone, and the emitted document reads as a specimen a user would write.
- Each row of the coverage statement is a fair test of its contract node: read side by side, the assertion would fail if the node's statement were false of this run. No `uses` entry lacks a row.
- No expected value in the checker comes from generated material. The authored fact is read only for the packaging comparison.
- Both identity sensitivities were observed: an example edit changes the build identity, and an unrelated contract edit does not.
- The final build has a complete passing live case, and every earlier failed assertion has a disposition supported by section 3.3. Different values supported by each reply's evidence do not themselves fail evaluation.
- A deliberately faulted input produces a diagnostic that names the commitment and the classification without a reader opening the checker.
- Nothing in section 4's not-touched list changed, the free-text baseline did not grow, and no harness machinery was added.

*Revise, keeping the design, when:*

- An assertion is true but weaker than its node's statement, or compares the envelope only with itself. Strengthen it, or remove the node from `uses`.
- The command name, usage text, exit statuses or emitted layout are awkward in use. A section 9 commitment can still be reversed here at the cost of the controller change and its tests.
- The report blurs contract relationships and native observations, or a failure is hard to attribute from the report.
- Evidence establishes a checker defect or a concrete condition requiring correction to a native expectation's applicability. Make and verify that correction under section 3.3; variation alone does not establish incomplete prerequisites.
- The example needed an evidence gap or a deviation from this plan that the maintainer has not seen.

*Stop, and reconsider the design, when:*

- A not-touched component had to change.
- The binding does not hold: unrelated contract edits move the build identity, or the example can change without moving it.
- The checker could not be made independent: a relationship could be asserted only by reading generated expectations or re-running a production classifier.
- Execution contradicts the contract node's text. That is a contract or product defect with its own change, not a test to adjust.
- The emission rule cannot be authored without free-text growth and the maintainer does not want the baseline raised.

**Recording the decision.** In the commit that completes step 4, the executor adds an "Evaluation record" section to this plan: the build identity and commit, the run identifiers with their availability (development evidence, disposable), the coverage statement's results, the ten-run comparison, each failed assertion with its relevant observation and disposition, any correction and replacement run, and every deviation from the plan. The maintainer's decision goes into that section in its own commit, in the maintainer's words: accept, revise with the changes listed, or stop with the reason. Step 5 does not begin before that commit exists.

**Step 5. Support and accounts.** Replace the evidence gap with owners that cite the emitter, the generator and the checks, with their limits stated; regenerate. Owner metadata is outside both the public payload and the generated source, so the build identity must be unchanged by this step. Confirm that it is; if it changed, the generated source carries more than it should.

**Step 6. Candidate verification** (section 8).

## 6. Anticipated failure modes

| Failure | Sign | Response |
| --- | --- | --- |
| The automation sandbox refuses XPC lookup, signing or native-builder queries | `xpc_error`, an empty keychain listing, refused `sysctl` reads | Follow the repository's sandboxed-harness guidance: rerun the same command once outside the sandbox, unchanged. Do not weaken the case |
| The app predates an example edit | The live case reports that emitted members differ from the authored fact | Rebuild. This is the intended stale-app refusal |
| The generated source carries prose or titles | Unrelated contract edits change the build identity; the stability control fails | Reduce the generated source to names, node identifiers and document text |
| The emission rule needs a `free.*` fact | Generation refuses free-text growth | Restructure the rule; otherwise stop and raise it |
| A `uses` reference pulls a large subtree into the `request` payload | A large `public.json` diff | Expected, since references are shared content; review that the references are the intended ones |
| The host refuses the authored example | The live case fails at admission with a `request_failure` | The example is invalid for this build. Fix the authored node; do not relax admission |
| `/etc/hosts` is unreadable or absent | The case fails as `prerequisite_unestablished` | Section 3.3's release consequence. Do not substitute a fixture file; changing the target changes the public example |
| The prediction is unavailable with a valid recorded spawn failure or timeout | The case fails as `native_observation` while contract relationships pass | Apply section 3.3's earlier-run rules: a complete passing run can supersede the trial without diagnosing the underlying OS cause |
| The prediction is `deny` or `open_read` fails with prerequisites established | The case fails as `native_observation` while contract relationships pass | Resolve the challenge to the native expectation under section 3.3; later successes alone do not settle it |
| A passing checker that checks nothing | The offline controls accept a faulted envelope | The controls must reject every single fault and report combined faults |
| The case passes against a release-form identity only by string luck | The identity-form assertions never see a `release:` value | Covered at candidate entry by the nested acceptance, whose fixture reports a release identity |
| The dispatcher's inventory differs after the case | Artifact-integrity failure | The command wrote into the app; it must not. Fix the command |

## 7. Acceptance criteria

1. In the `unreleased` stamp state, `generate_contract_stamps.py --check --require-history` passes, and a second generation writes nothing.
2. A signed development build of the final source prints, for `example paired-probe`, a specimen whose `contract` equals `--version`'s `build.contract` and the app's `PWContract`, and whose other members equal the authored example. `run` on those bytes exits 0 with `finished`.
3. `witness_contract/emitted_example_conformance` and `emitted_example_checker_controls` pass inside a complete default battery with no skips, unrun cases or harness errors, and with the app inventory unchanged. The live case's artifacts hold the emitted bytes, the version envelope, the run envelope, every refusal input and output, the target-file observations, and a report naming each commitment by contract node with its result, contract relationships apart from native observations.
4. Each refusal control in section 3.4 produces its stated code, path and expected identity, and the controller-side controls show no client capture.
5. The cross-build controls pass: the unbound build emits nothing and exits 2; the signed app refuses a specimen emitted under another identity.
6. The generation controls pass, including the two sensitivity directions: an example edit changes the build identity, and an unrelated contract edit does not.
7. `build.sh`, `build_contract.py`, the worker identity and the bundle inventory are unchanged from `e5d7488b`.
8. The controller README's CLI block, the guide's command table and the suite accounts describe the command and cases as built.

## 8. Entering the 0.3.8 candidate

Earlier pre-tag evidence does not carry over. This work changes the CLI, the build-identity inputs, the contract tree and its generator, so the rehearsals recorded for `8435e5d3` describe a different build. The following are required on the final source, in the `unreleased` state, before the work is treated as part of the candidate:

1. A signed development build, and a complete default battery against it (about half an hour on this machine as of 2026-11-11).
2. The complete `preflight/build_refusal_controls` rehearsal (about two and a quarter hours), because the generator and its build gate changed. Its nested extracted-ZIP acceptance runs the default battery, including the new live case, against a fixture that reports a `release:` identity. That run is this plan's evidence for the release form; record the identity the case saw.
3. A reviewed applicability statement for `witness_contract/order_barrier_mutations`: it is not required if the worker wait, release store and eligibility rule are untouched, which criterion 7 and an unchanged worker identity support. State this as a judgment, not as a mechanical fact.
4. Then prepare again: `generate_contract_stamps.py --release v0.3.8 --require-history`, changing only the two stamp tables and the snapshot history; confirm that the ordinary check gives exactly the expected missing-tag refusal; run the same prepared-commit checks as before (baselines against `v0.3.7`, footprint attribution).
5. Revise the prepared notes in [RELEASE-NOTES-v0.3.8.md](../records/contract/RELEASE-NOTES-v0.3.8.md): the `request` row gains an additive command, and the verification paragraph cites the new runs with their scopes.

The plan ends at that prepared, untagged state with the maintainer's review pending. Tagging, the tagged rehearsal, notarization and publication are separate decisions and are not steps here; the release inputs record the open decisions and checkpoint rules they will need. If the maintainer prefers to tag 0.3.8 without this work, steps 0 to 5 can equally sit on a branch of the `unreleased` state; nothing in the design depends on the release number.

## 9. Commitments to confirm

The design settles these; each creates public behavior, so each is stated for confirmation before step 2.

| Distinction | Why it matters | Commitment |
| --- | --- | --- |
| The command prints a bare specimen, not an envelope | It is the first controller output that is not an envelope, so "every output is an envelope" stops being true of the CLI | `example` output is a request document; envelopes remain the form of every report |
| An unbound build refuses instead of emitting | A direct Cargo build gets exit 2 from a command that otherwise cannot fail | The app emits only specimens its own controller gate admits |
| `specimen_id` is the contract node identifier | Renaming the node changes emitted bytes and the build identity; users who copy the example inherit a label that names the contract | Emitted examples are traceable to their defining node through an existing field |
| The example text is a build-identity input | Correcting the example invalidates specimens saved for the previous development build; other contract edits do not | Shipped example material is bound to the identity it is emitted under |
| Native expectations fail the case when their prerequisites hold | A machine where `sandbox_check` gives no answer for this read fails the default battery and release acceptance | The battery asserts the native result only under observed prerequisites, and reports it apart from contract relationships |

## 10. Where this stops, and the route onward

Out of scope: external runner examples, phased or actor specimens, expected-refusal examples, response fixtures, an examples listing, any documentation interface, and any classification of the contract as a whole.

The pieces are shaped so later material adds rows, not machinery:

- **Another executable specimen** (a phased probe, say) is another example node with `emit` and `specimen`, a regenerated source, and another entry in the checker's table keyed by its node identifiers.
- **Runner selection** needs values that exist only on the user's machine. That calls for a declared-prerequisite or parameter fact on the example and a decision about emitting templates that are not directly submittable; the live test would belong with the opt-in BYOXPC cases.
- **Refusals** need an expected-outcome fact, so an example can state that submission is refused and how. The refusal controls in this plan are the test-side shape of that.
- **Output interpretation** is not a request. It would be a different emitted artifact and deserves its own design.
- **Support grade.** After an archived release acceptance includes the live case, the example's owner can move from `check_read` to release credit naming that release and case.

Suitability for public expression and suitability for executable verification are separate questions for each candidate. This plan handles one item that satisfies both.
