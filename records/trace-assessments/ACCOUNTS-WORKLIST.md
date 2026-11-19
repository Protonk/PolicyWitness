# Accounts worklist

Status, 2026-11-19. This is the specification for the three technical-account
passes in `records/TRACE-MANAGEMENT-PLAN.md`. It was written on 2026-11-17 at
`837296af` in gitignored scratch. On 2026-11-19 it was copied here, and it is
unchanged below this paragraph. The "assessment files" it names are the files
in this directory. The plan's "Selected remedies" section carries everything
in its `RULINGS.md`. Its line numbers belong to `837296af`.
`DISPOSITIONS.md` governs where the two differ. `ACCOUNTS-ADDENDA.md` holds
the later entries and the status of the sections that no pass owns.

Basis: the twelve assessment files under
`.tmp/trace-integration/assessments/` and `RULINGS.md`, read at
`837296af` on 2026-11-17. This list holds everything those files require
that is not part of the product-code edits of rulings R1–R13: account
corrections, the generator refusals of R14, the generator-side schema
validation of R8, and test-side repairs that need no signed rebuild. The
product threads land their own code, checks and the accounts that state
their changed behavior; the table "Items the product threads carry" near
the end lists those so nothing falls between.

Line numbers are those the assessments cite at `837296af`. Re-read each
location before editing. The tree has moved since: `5ab8e530` and
`116cae5a` (the Markdown reader cohort) changed `docs/ARCHITECTURE.md`,
`docs/DEPENDENCIES.md`, `docs/architecture.json`,
`tests/CHANGE-VERIFICATION.md`, `tests/README.md`, `tests/catalog.json`
and files under `tests/suites/source_drift/`; and when this list was
finished another agent held uncommitted changes in about thirty test
files, among them several this list edits
(`tests/suites/failure_boundaries/check.py`,
`tests/suites/runner_outcome_bad_request/contract.py`,
`tests/suites/blackbox_e2e/disposition_controls.py`, and
`check_actor_compositions.py`, `check_dossier.py`, `check_ordering.py`,
`check_phases.py`, `check_pre_apply_failure.py` under
`tests/suites/witness_contract/`). Product threads that land first move
lines as well.

Constraints that apply to every entry: `docs/PolicyWitness.md`, its
distributed copies and its stamp table stay byte-unchanged; a shared
region (owned by `docs/LIMITS.md` through `docs/limits.json`,
`docs/QUESTIONS.md`, `docs/EXTENSIONS.md`, the shared statuses and
reading rules of `tests/FAILURE-PROPAGATION-CONTRACT.md`, and matrix
rows) may have a false statement corrected or removed in its owner and
gains no workflow, example or reorganized explanation; no permanent
document links to `records/`; surface edits change existing prose or
`free.*` text and add no new `free.*` fact (the free-text count refuses
an increase); generated copies are never edited.

## Reading an entry

Each entry gives the location, the claim ids it disposes of, the current
text or symbol, the change, the regenerating command when the file is a
generator input, and the check that verifies it. Each carries one mark:

- `independent`: can land without any product thread.
- `after R<n>`: its wording depends on that ruling's final behavior; the
  entry says what to confirm. Where the product thread for R<n> has
  already written the same sentence, the accounts thread verifies it and
  adds only what is missing.
- `comment in build input`: a source-comment edit inside a
  build-contract input. It does not land alone; the entry names the
  product thread whose rebuild carries it.

"Merged edit" in a location marks a sentence that two passes edit. Both
proposed texts are shown with a recommendation.

Entries are grouped by owner file, then ordered by location. The owner
groups are: contract surfaces; the presentation map and CONTRACT's
authored introduction; generator code; the failure evidence contract;
limits and shared-region owners; the architecture manifest; authored
technical documents; READMEs and test accounts; test-side repairs;
comments in build inputs; records.

## Contract surfaces

### `docs/contract/00-identity.surface.md`

- **`identity.public.forms` `:48-55`, `identity.public.inputs` `:63-79`, `identity.public.derive` prose `:94-97` — one merged edit** — DT-08.a (pass A and pass H), DT-88.a–c, DT-90.a, DT-90.d, DT-91.a, DT-92.c, DT-92.d, DT-93.g, DT-94.a–c. `after R3` for the refusal list (a directory that cannot be listed, an entry that cannot be inspected) — confirm the final refusal set and message nouns in `docs/source_identity.py`; the rest is true today, but the pass asks that statement and walker land together. [pass H]
  - Current `:63-65`: names six roots (omits `controller/interface`) and omits `docs/publication.py`; `:75`: "Discovery uses the same inventory in a checkout and a source copy. Missing declared inputs, symlinks under the selected roots and nonregular source objects refuse derivation."; `:50`: "sorted" without an order; `:96-97`: "The pre-sign comparison refuses a selected-source change during compilation."
  - Pass A change: add `controller/interface` to the directory list and `docs/publication.py` to the file list.
  - Pass H change (draft; the implementer may reword): "`development:<sha256>` identifies the selected source paths and bytes present in a source tree when it is derived; it does not identify a commit. … For each repository-relative path in ascending Unicode code-point order, which is also the byte order of the UTF-8 paths, the generator appends …" / "The development digest includes every regular file whose final suffix is exactly `.rs`, `.c`, `.h`, `.swift`, `.sb`, `.plist` or `.ent` anywhere under `controller/src`, `controller/tools`, `controller/interface`, `runner/Sources`, `runner/Clients`, `runner/Services` and `runner/augments`. It also includes `build.sh`, `meson.build`, `meson.options`, `runner/Package.swift`, `controller/Cargo.toml`, `controller/Cargo.lock`, `controller/build.rs`, `controller/src/test_inputs/read.json`, `Info.plist`, `PolicyWitness.entitlements`, `docs/build_contract.py`, `docs/source_identity.py`, `docs/publication.py`, `tests/build_equipment.py`, `tests/build-evidence.py`, `tests/lib/build_provenance.py`, `tests/lib/signer_check.py`, `tests/lib/cargo_config.py`, `tests/lib/checkout_lock.py` and `tests/lib/output_target.py`." / "Discovery reads the directory tree on disk and applies this rule alike in a checkout and a source copy. Git tracking and ignore rules do not enter it: an untracked, ignored or hidden file with a listed suffix under a listed root is included. The selection is declared by these roots, suffixes and files. It is not derived from what the compilers read, and it includes test-only code and files that no build step consumes. Derivation refuses a missing declared file or root; a root holding no selected file; a symlink, or an object that is neither a regular file nor a directory, anywhere under a selected root whatever its name; a directory that cannot be listed; an entry that cannot be inspected; and a selected file that cannot be read. The digest's equality concerns those paths and bytes. File modes, timestamps and extended attributes do not enter it, and path names are hashed as the file system returns them, without Unicode normalization. Build configuration, …" / "The pre-sign comparison refuses when the selected paths or bytes at that point differ from those hashed before compilation. A change made and reverted between the two derivations is not detected."
  - Recommended: pass H's text; it subsumes pass A's two additions and spells every path in full, which the statement-oracle test needs (no interpretation of "in that same directory"). Settle in the wording that a file named only `.rs` has no suffix and is not selected.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (rewrites `docs/CONTRACT.md` and `docs/contract/public.json`; every surface is already `unreleased`; prose only).
  - Check: the statement-oracle test in `tests/suites/source_drift/build_contracts.py`; pass A's set comparison (statement names against `DIRECTORIES`, `FILES`, `SUFFIXES`) returns empty both ways.

- **Support: new selection support owner under "Selected build inputs"; derivation support pins `:99-108` (pin at `:105`)** — DT-91.e, DT-93.a, DT-93.b, DT-93.i, DT-93.j, DT-94.e, DT-88.d. `after R3` — cite the literal-tree and statement-oracle tests under their final names once they exist. [pass H]
  - Current `:105`: "Selected-source mutations change the digest; clean annotated release selection checks actual bytes; Swift context disagreement and the extracted pre-sign guard refuse."
  - Change: add an owner (for example `#### Selection support {support: owner}`, grade `check_read`) citing `docs/build_contract.py` `DIRECTORIES`, `docs/source_identity.py` `source_paths` and the new tests, with pins limited to what they assert (statement/declaration equality; literal-tree inventory and framing; listed refusals; Git-state independence) and limits "No check compares the selection with compiler dependency records; the release-form and guard checks use copies of the generator's own inventory." Narrow the existing pin if "Selected-source mutations change the digest" is kept: after the oracle test it holds per root and per explicit file.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/generator_contract` (citation presence); review must reject a pin that credits behavior no cited check asserts.

### `docs/contract/10-request.surface.md`

- **Shared null rule, `:100`** — DT-18.c. `independent`; lands after the per-field presence rules. [pass A]
  - Current: "Treat optional null as absent where decodeIfPresent is used".
  - Change: name the fields by what their entries say (their stated presence rules), keeping the listed refusals; no reference to a Swift decoding call.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts`.

- **Exit-0 sentences, `:194` (`example`) and `:229-234` (`test-input`), and the two support owners' `limits`** — DT-28.c, DT-28.e. `independent` [pass C1]
  - Current: "Process exit 0 supplies the complete document"; "Process exit 0 establishes complete publication".
  - Change: add beside each: "Exit 0 reports that every write and the flush to the process's standard output succeeded. A command launched with standard output closed writes to a discarding descriptor and also exits 0."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: the `>&-` rows in `controller/integration/cli_contract.rs`. Re-executed now on the `2f4d76e4` app: every publisher exits 0 with stdout closed at launch.

- **Owner citations `:361` and `:467`** — DT-40.c1. `independent` [pass B]
  - Current: `run_flow.rs: validate_request_contract` and `run_flow.rs: strip_runner_selector` name the calling file.
  - Change: add `request_patch.rs: pub fn validate_request_contract` and `runner_select.rs: pub fn strip_runner_selector` beside the call sites.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (changed-item rows change; no stamp change).
  - Check: `source_drift/generator_contract` (citation presence).

- **Selector precedence rule, `:441` (`free.effect`)** — DT-27.a, DT-27.b. `independent` [pass C1]
  - Current: states two refusal conditions and names no code.
  - Change: "Refuse with `conflicting_selector`: standard mode with an external selector, or byoxpc mode without an ID or service (at the root path), and a `--runner-mode` value that differs from the file's nested `runner.mode` (at `runner.mode`)." Keep "nested": a legacy top-level `runner_mode` beside a different `--runner-mode` is not refused (`run_flow.rs:481-510`).
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (free-text relationship count unchanged).
  - Check: two existing interface cases plus the new third-condition case.

### `docs/contract/11-policy.surface.md`

- **Presence rules: `policy.spec.format`, `policy.helper_policy.format`, `policy.helper_policy.sbpl_source`** — DT-18.b, DT-18.d. `independent` [pass A]
  - Current: presence renders "as defined below"; the meaning states no required/optional/omission/null rule. `sbpl_source` is `Option<String>` in the import while its meaning says "Require a string source at helper admission".
  - Change: author each field's presence rule in its meaning after reading that field's decoder and admission (the import fact is decoder storage, not admission). For `sbpl_source`, establish whether omission, null and a wrong type are refused alike before writing.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: presence ratchet in `source_drift/build_contracts`; per-field admission stays source-derived unless exercised.

- **`policy.spec.format`, `:21-29`** — DT-37.f (and the DT-18.b presence rule for the same meaning). `independent` [pass B]
  - Current: vocabulary refusal stated without the 63-byte label bound.
  - Change: add the bound with `<!-- span limits.request_label.value_unit -->` and the same order clause. Optional, same batch (pass B, outside the review): the same span on `actors.sandbox.mode`, the actor policy `format` and the extension `operation`, `family` and `authority` labels, which share the `request_label` row (`CWorkerRequestPlanning.swift:235-252`).
  - Regenerate: `tests/lib/python.sh docs/generate_limits.py`, then `docs/generate_contract_stamps.py`.
  - Check: `failure_boundaries/admission`.

- **`capture_nonce` request field, `:54`** — DT-97.d, CL.c4. `independent` [pass I]
  - Current: "exactly 32 lowercase hexadecimal characters encoding the caller's nonce … Receipt publication and consistency checks belong to the compiled-profile surface."
  - Change: add "The host checks the nonce's form only and keeps no record of earlier nonces; uniqueness across requests is the caller's." (The refusal text's word "fresh" stays; changing it is a build-contract edit for a wording gain.)
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (no nonce store exists); reuse was never executed.

- **Augment rule code name, `:152`** — DT-26.a. `independent` [pass C1]
  - Current: "Invalid names produce `invalid_augment_name`".
  - Change: `invalid_value` (the code HEAD and `v0.3.7` produce, `controller/src/augments.rs:238-248`).
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `integration/cli.integration` (`invalid_augment_name_rejected_as_bad_request`) with the added path assertion.

- **Fallback capture sentence, `:392`** — DT-116.f (R11 names this statement). `independent` (true today; R11 deletes code that cannot run). [pass K]
  - Current: "The fallback capture reports this independent attempt alongside the transport result and any retained worker evidence."
  - Change: "The fallback capture reports this independent attempt beside the client transport capture; an envelope that carries a fallback capture carries no host reply and no execution diagnostics."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts`.

- **"Literal import inventory" subject, `:547`, limit L-D** — DT-81.t9, DT-81.t10. `after R12` (the R12 thread rewrites this sentence for the new field; L-D is added in the same subject). [pass G]
  - Change: add "The helper inventory carries no first-problem text and does not name which bound was reached; each cause is read from its own field."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts`.

- **Helper `records`, `:551`** — DT-83.b, DT-85.c, DT-85.d (limit L-C). `after R12` — confirm the record-error text for a file containing an unfollowed form. [pass G]
  - Current: "Each resolved file is opened once, checked as a regular file, and its held bytes are both hashed and scanned."
  - Change: say that scanning collects import forms and that an unfollowed form is reported by the flag and the record error; add that literal names are collected in every syntactic position, including forms the compiler does not evaluate.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts`; helper contrasts.

- **`policy_closure_sha256`, `:563`** — DT-87.a, DT-29.b, U1.4c (limit L-C). `independent` for the invalid-UTF-8 case; the "fully followed" clause is `after R12` (R12 gives a record error to a scanned file containing an unfollowed form). [pass G]
  - Current: "… Failed imports remain error records and contribute no path/hash line."
  - Change: a line is contributed by every record that carries both a resolved path and a hash, including a record whose `error` reports that its text could not be scanned or (after R12) fully followed; records without a hash (unresolved, unreadable, nonregular, depth-limited) contribute none. Add L-C: the closure digest identifies the source and every file the scan hashed; it does not encode `truncated`, `cycle`, record errors or the unfollowed flag, and it is not a digest of the compiler's inputs. Do not change `compute_closure_hash`.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: the invalid-UTF-8 helper contrast (closure equal to an independent recomputation that includes its line). Re-executed now: the framing with the line included matched.

- **"Separate reads and their identities", after `:577` — limit L-E (linked pair with the receipt-side sentence in `35-profile.surface.md`)** — U1.o1, U1.2c, U1.2e, U1.4f, U1.5q1a, U1.5q1c, U1.5q2, U2.o, U2.1e, U2.D1, U2.D2. `independent`; land with the receipt-side sentence so the pair reads as one statement. [pass G]
  - Current: "… A literal inventory describes the producer's walk; the worker compiled-profile receipt has its own observation boundary."
  - Change (pass G wording): "No field of a run envelope or a helper envelope associates an import record with the bytes the worker's compiler read. The dossier's applied-source digest, the reply's policy digest and the receipt's source digest are digests of one held source string; their equality says nothing about imported files." See the pass I entry for the receipt-side sentence and the recommended pairing.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (prose; adds no `free.*` fact).
  - Check: `source_drift`; existing source-join assertions (`check_dossier.py:161`, `:202`; `cli_contract.rs:1293`, `:1460-1464`; `check_actor_compositions.py:132`).

- **"Literal import evidence scope", `:585`** — DT-85.g (removal), DT-85.a–e, DT-85.h, IL.c, U1.4g, U1.7 (limit L-A). The removal is `independent`; the L-A sentence that mentions the unfollowed flag is `after R12` — confirm the field's final spelling and that the scan recognizes only `import`-headed forms. [pass G]
  - Current: "Native compilation examples establish their selected literal imports; collision precedence, macro-generated dependencies and files changing between independent reads retain their own evidence limits."
  - Change: remove the "Native compilation examples establish their selected literal imports" clause (the three native compilations in the tree assert only that compilation succeeds). In its place state L-A: the inventory is a scan of source text and of the files that scan read. It is not an observation of the compiler's file reads. A record states that the scan found that literal name and read those bytes during its walk, not that the compiler evaluated the form or read the file. An inventory with no record and no unfollowed form does not state that the compiler read no file: SBPL is evaluated, a policy can cause a file to be read through a computed argument, a rebound or applied `import`, `eval` or `load`, and the scan recognizes only forms headed by `import`. (Wording is the implementer's; the content is the disposition.)
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (policy stamp changes).
  - Check: the helper contrasts that assert present behavior for the unevaluated form (record without evaluation) and the aliased `import` (evaluation without record or flag) in `integration/cli.integration`.

- **Import subtree support owner, `:596-604`** — DT-86.a, DT-84.g, DT-86.i. `after R12` — cite the helper and dossier contrasts only once they exist under their final names. [pass G]
  - Current: `source_read`; cites `resolve_imports`, `read_regular_file`, `compute_closure_hash`, `ImportInventory` and no check.
  - Change: cite the new checks with their limit: constructed inputs, the helper's host-side compiler, evaluation shown by a diagnostic naming the file, on the tested OS build; state that the followed set is established for macOS 26.7.1 (25G241) only.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/generator_contract` (citation presence).

- **`tool_exit_code` `:628-630` and `stderr` `:672-674`** — DT-42.b, DT-117.g. `independent` [pass K]
  - Change: `tool_exit_code`: "Helper process exit code. It is 1 when the process status supplies no numeric exit code, as after termination by a signal, and 1 for an `unavailable` capture; `status` and the retained streams distinguish these." `stderr`: "Retained stderr text, including diagnostic output when the helper produced no envelope. For an `unavailable` capture it holds the controller's launch or delivery diagnostic, and the byte counts are null." Limit in the same place: a helper delivery failure is reported as `unavailable` and the helper's own output is not retained.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`policy_check.rs:34-41`, `:78`); retained controlled runs B4u, B4s (local).

- **Eligibility limit under `fallback.classify`, `:688-692`** — DT-116.c, DT-116.e. `independent` (the R10 thread edits the rule's `free.effect` at `:688` for the actor form; this limit is separate text). [pass K]
  - Change: add "Eligibility follows the client's terminal event only. It does not classify whether the specimen ran: an invoked `xpc_timeout` has no fallback capture, and an eligible `xpc_error` can follow a submission call that sent no request."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `runner_unit/client_session_controls` (`PWRunnerClientSessionTests/main.swift:158-167`).

- **`actor_check.actor_id`, `:715-717`** — DT-117.f. `independent` [pass K]
  - Change: add "A capture is associated with its actor by this label and by its position among the actors that carry a policy object; a null label is identified by position only."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`run_flow.rs:383-391`, `:633-636`); the corrected actor fallback tests.

### `docs/contract/12-probes.surface.md`

- **Presence rules: `probes.step.step_id`, `.sandbox_check`, `.attempt`; `probes.query.operation`; `probes.filter.kind`; `probes.attempt.kind`, `.action`, `.target`** — DT-18.b, DT-18.d. `independent` [pass A]
  - Change: author each field's presence rule (all non-optional in the import) after reading its decoder and admission.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: presence ratchet in `source_drift/build_contracts`.

- **`probes.step.step_id` meaning, `:23`** — DT-131.d, DT-50.t2 (R9 keeps request-name uniqueness canonical and has it stated); the same meaning takes the DT-18.b presence rule (pass A). `independent` [pass L]
  - Current: "… It is unique across all actions … Actor plans require it to be nonempty; ordinary plans currently accept a unique empty value."
  - Change: add "Uniqueness is under canonical Unicode equivalence: identifiers that differ only in normalisation are duplicates." Check the phase and actor identifier statements in `10-request.surface.md` and `13-actors.surface.md` for the same silence and add the sentence where it applies. (R5 leaves the request-side sentence about the empty value unchanged.)
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`ProbeRunner.swift:113-118`; `ActorPlan.swift:358-363`, `:397`); the review's `both_ids` live refusal is retained under `.tmp/contract-trio/acceptance/`.

- **`probes.query.excluded`, `:118`** — DT-37.d. `independent` [pass B]
  - Current: the definition renders its set as "Requires ((…) or (…))" with no statement of consequence.
  - Change: add "A query satisfying the condition below is excluded: it is admitted, receives no validator query and reports prediction_unavailable. The condition is not an admission requirement." Do not change the renderer label (`docs/contract/tree.py:1282`).
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (probes stamp changes).
  - Check: `runner_filter_sysctl_name/prediction_unavailable_attempt_observed` and the same case id in `runner_filter_local_name`, `runner_filter_iokit_registry_entry_class`, `runner_filter_iokit_user_client_class`.

- **`probes.filter.kind` `:163-171`, `probes.attempt.kind` `:197-205`, `probes.attempt.action` `:207-209`** — DT-37.f (and DT-18.b presence rules for the same three meanings: write each meaning once). `independent` [pass B]
  - Current: each states its vocabulary refusal without the byte limit whose capacity refusal precedes it.
  - Change: add the bound with `<!-- span limits.probe_plan_label.value_unit -->` and the clause "A value longer than … is a capacity refusal, decided before the vocabulary check."
  - Regenerate: `tests/lib/python.sh docs/generate_limits.py` (owns authored spans), then `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `failure_boundaries/admission` (`tests/suites/failure_boundaries/check.py:68-69`, `:157`, `:166-167`).

### `docs/contract/13-actors.surface.md`

- **Presence rules: `actors.actor.actor_id`, `.sandbox`; `actors.phase.phase_id`, `.actions`; `actors.after_termination.actor_id`** — DT-18.b, DT-18.d. `independent` [pass A]
  - Change: author each field's presence rule after reading its decoder and admission.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: presence ratchet in `source_drift/build_contracts`.

- **Owner citation `:140`** — DT-40.c1. `independent` [pass B]
  - Current: `ActorOrchestration.swift: actorApplicationAssessment`.
  - Change: cite `PWRunnerAuthoritySetup.swift: func actorApplicationAssessment`.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/generator_contract`.

- **`actors.phase.order` `free.effect`, `:225` — merged edit for the reap-precedence and allowance sentences** — DT-36.a (pass E), DT-10.a/.b/.d (pass A). `independent` [pass E]
  - Current: "After a failed active visit establish that actor's reap before any further activation; unresolved termination cancels the remaining schedule. Arrival or completion timeout cancels for exhausted execution allowance, and a wait error cancels for lost ownership."
  - Pass E text: "After a failed active visit establish that actor's reap before any further activation; unresolved termination cancels the remaining schedule, including after a wait error that leaves the actor unreaped. Once the reap is confirmed, an arrival or completion timeout cancels for exhausted execution allowance and a wait error cancels for lost ownership."
  - Pass A requirement (no exact text given): an arrival or completion wait ending with no remaining allowance, including one whose clock can no longer supply a remaining value, cancels under the execution-allowance label; the wording must cover the pre-visit site (`ActorScheduler.swift:320-324`), which selects the label with neither collection nor a reap.
  - Conflict: pass E's second sentence, read alone, places the allowance label after a confirmed reap; pass A's pre-visit site sets it with no reap. Recommended: use pass E's two sentences and add a third that carries pass A's point without contradicting the reap precedence, for example: "A wait, or a schedule entry about to begin, with no remaining execution allowance is classified as exhausted, including when the clock can no longer supply a remaining value." Confirm the final sentence against `ActorScheduler.swift:320-324`, `:425`, `:442-443`.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (free-text count unchanged).
  - Check: `runner_unit/pwrunner_core_unit_executable` with the DT-36.b label assertions (and the optional DT-10 clock control); `source_drift/build_contracts`.

- **Barrier support owners, `:232-239` and `:250`** — DT-13.a, DT-13.c. `independent` [pass A]
  - Current `:239`: "Integrated collection/release and mutation observations retain their own execution owners." Current `:250`: "retain their separate owners".
  - Change `:239`: "The source owner describes eligibility. No owner in this tree credits integrated collection/release or mutation execution; `witness_contract/order_barrier_mutations` is the control routed for changes to the wait, release store or eligibility rule." Matching change at `:250`. Add the source citation `controller/tools/pw_probe_runner/pw_probe_runner.c: wait_for_proceed` to the barrier's source-read owner (`:232-239`). Add the check citation `tests/suites/witness_contract/opt_in/mutations.sh: order_barrier_mutations` (form `test`, grade check-read) only if its author reads the control and states its context and limits (non-default, no run credited).
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (adds a changed-item row for `wait_for_proceed`).
  - Check: `source_drift/build_contracts` (citation existence); the behavior's own control is `witness_contract/order_barrier_mutations`.

- **Identifier rule support owner, `:418-426`** — DT-22.c. `after R5` — confirm the new live pair in `failure_boundaries` exists under its final case and symbol names before citing it. [pass C1]
  - Current: check-read support pins "ordinary meaning admission tests uniqueness without a nonempty condition" and cites `runReaderCorpusTests`, which constructs replies and submits no request.
  - Change: cite the live empty/non-empty pair (R5 control) and the actor `empty_step_id` refusal control; keep the corpus citation only for the reply-reader claim it supports.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/generator_contract` (citation presence); `failure_boundaries`, `runner_outcome_bad_request/accepted_input_contract`.

### `docs/contract/14-extensions.surface.md`

- **Presence rules: `extensions.action.step_id`; `extensions.operation.operation`** — DT-18.b, DT-18.d. `independent` [pass A]
  - Change: author each field's presence rule after reading its decoder and admission.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: presence ratchet in `source_drift/build_contracts`.

- **`extensions.custody.issue` `free.effect`, `:373`** — DT-64.a, DT-64.b. `independent` [pass D]
  - Current: "Erase the native allocation after copying."
  - Change: "Erase the returned token through its inspected length and free the allocation, after copying a bounded token or on refusing an empty or longer one; bytes of a longer return beyond the inspected length are freed without being erased." (Edits an existing free-text effect; free-text counts do not increase.)
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (`extensions` stamp changes in CONTRACT; rendered at `docs/ARCHITECTURE.md:356`).
  - Check: `witness_contract/extension_boundaries` with the added issuer-erase assertion; `source_drift/build_contracts`.

- **`extensions.custody.issue` paragraph, `:377`, last sentence** — DT-62.a, DT-122.b, DT-123.a–c, DT-65.b/.c. `independent` [pass E]
  - Current: "The native return and host custody acceptance are reported independently."
  - Change: "The host records custody acceptance separately from the worker's native return. The reply reports acceptance through the token status of a published non-null issue and through the transfer records that used the custody. While the issue result is unpublished the token is `unresolved` or `not_reached` and the reply reports no acceptance observation, whether or not the host accepted the published bytes. The issuing worker's own record of the host's answer is not a reply field." Add with the paragraph: "The host and controller checks relate a token's status to its issue event and a delivered transfer to its own fields; they do not compare the two."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (rendered at `docs/ARCHITECTURE.md:358`).
  - Check: `ActorReplyTests.swift` pinned case; consumer custody rule (`tests/lib/extension_evidence.py`).

- **`extensions.custody.erase`, prose under the rule at `:417-421`** — DT-124.b, X-1, X-3. `independent` [pass D]
  - Current: the rule's header carries `report: ["runner_reply"]`; no reply field reports either last-use clearing.
  - Change: add "The reply's `final_erase`, `shared_clear` and `terminal_owned_inbound_clear` cells record teardown and worker-exit clearing; last-use clearing has no reply field."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`ActorOrchestration.swift:462-474`); `source_drift/build_contracts`.

- **Custody subtree support owner `limits`, `:440-448`** — DT-124.j. `independent` [pass D]
  - Change: add "Host last-use custody clearing has no registered check; worker last-consume clearing is exercised by synthetic controls only."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts`.

- **Support pins, `:623`** — DT-122.e. `independent` [pass E]
  - Current: "The host custody record carries token acceptance".
  - Change: "A published issue native value projects to native_nonnull; token acceptance is carried by the token resource's status."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (owner metadata).
  - Check: `source_drift/build_contracts`.

- **Transfer record `status`, `:685`** — DT-30.b. `independent` [pass C1]
  - Current: ten "Host acknowledgement" names.
  - Change: list the seven host answers assigned at `AuthorityCustody.swift:513-606`; say `host_timeout` and `clock_fault` are the source worker's own wait results and appear in the transfer event's `status`; drop `none`.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading; `source_drift/build_contracts`.

- **Owner citation `:700`** — DT-40.c1. `independent` [pass B]
  - Current: `ActorOrchestration.swift: PWRunnerTransferRecord`.
  - Change: add `PWRunnerActors.swift: struct PWRunnerTransferRecord` beside it.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/generator_contract`.

- **`delivered_length`, `:882-884`** — DT-122.d. `independent` [pass E]
  - Change: add "The issuing worker wrote this length to its outbound slot and `token_length` to its evidence slot; their equality checks one writer's consistency."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading; retained E2 capture.

### `docs/contract/15-refusals.surface.md`

- **Controller refusal `code` values, `:138`** — DT-27.c. `independent` [pass C1]
  - Current: the list copies the host list and ends in `admission_refused`, which no controller source produces.
  - Change: the ten controller codes: `invalid_json`, `missing_value`, `type_mismatch`, `missing_field`, `unsupported_contract`, `unknown_field`, `invalid_value`, `conflicting_selector`, `augment_unavailable`, `missing_policy_source`; keep the field open and illustrative.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts`; `unit`, `integration`.

### `docs/contract/20-transport.surface.md`

- **Presence rules: `transport.reservation.contract`, `.attempt_id`, `.lease_ms`** — DT-18.b, DT-18.d. `independent` [pass A]
  - Change: author each field's presence rule after reading its decoder and admission.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: presence ratchet in `source_drift/build_contracts`.

- **Limits after `:574` and at `error.reason` `:449-451`** — DT-118.b, DT-118.d, DT-119.g. `independent` [pass K]
  - Change after `:574`: "Admission compares the capture and the host frame with the build contract and with their own retained-byte accounts. It does not compare either with the held request; their association rests on the one client invocation that read the held bytes." At `:451`: "The capture readers also accept `interrupted` and `invalidated`; the shipped client reports a failed connection as `xpc_error` or `proxy_type_mismatch` and emits neither."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`runner_client.rs:129-130`, `:356`, `:522-523`; `PWRunnerClientSession.swift:32`, `:35`).

### `docs/contract/21-wire.surface.md`

- **Fingerprint identity definition, `:102`** — DT-105.a–c, DT-105.g, DT-105.h, DT-106.a–c, DT-106.e. `independent`; lands in one pass with the R8 thread's refusal-list edit at `:82` if convenient. [pass J]
  - Current: "… Changes to a field's name, tag, type, optionality, null/projection rule or a newly added optional field change the fingerprint and require exact receiver agreement."
  - Change: append "The fingerprint identifies the schema declarations and is not a compatibility test. It also changes for a declaration that no producer writes: a public name, a null rule that a path-form or conditional-null rule or a required field makes ineffective, record order, a variant case name or declared type spelling, and a root key. A match shows that both builds carry the same declarations; structural admission, applied to each frame, checks the bytes."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (wire stamp changes; `surfaces/wire.json` unchanged).
  - Check: `source_drift/porcelain_codec` with the presentation mutations.

- **Projection definition, `:110`** — DT-109.c, DT-109.f, DT-112.a. `independent` [pass J]
  - Current: "Path-form fields equal to their input bytes are omitted and listed in `same_as_input`; unavailable forms remain null." and the hexadecimal sentence.
  - Change: after the path-form sentence add "The compaction applies to public JSON only; the frame, and the envelope's retained copy of it, carry each derived form." After the hexadecimal sentence add "The projection spells the bytes received; digest length is checked only by the equipment and control-observation readers." (If R8 were declined, the fallback sentence for DT-108 would go here; R8 is selected, so it does not.)
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading; `source_drift/build_contracts`.

- **Executed owners' `limits`, `:126` and `:140` (`source_snapshot` at `:134`, `:148`)** — DT-11.b. `independent` [pass A]
  - Current: `source_snapshot: reviewed-inputs sha256:<digest> (b6ce6d26 dirty…)` with no statement of the input set.
  - Change: add to `limits`: "The reviewed-inputs digest names an input set and framing this tree does not record; it cannot be recomputed here." If the author of `eac1482e` supplies the input list, record that instead.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts`.

- **`wire.validator.emit`, `:185`** — DT-37.a. `independent` [pass B]
  - Current: "Parse errors use `parse_error`; an unsupported filter uses `bad_filter`."
  - Change: "Grammar refusals use `parse_error`; this includes any filter_type other than NONE without filter_value, whether or not the type is recognized. A line that passes the grammar with an unrecognized filter_type uses `bad_filter`."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (wire stamp changes in CONTRACT).
  - Check: `validator_batch_mode/batch_ndjson_roundtrip` with the new unknown-type pair (see `tests/suites/validator_batch_mode/run.sh`). Re-executed now on the `2f4d76e4` validator: both outcomes as stated.

- **"Host line admission" prose, `:201`** — DT-48.t4. `after R5` — the R5 thread rewords this sentence ("Allow/deny require a string step_id, nonempty operation and filter_type plus integer rc and errno."); add the limit to the final sentence. [pass L]
  - Current: "Allow/deny require nonempty step_id, operation and filter_type plus integer rc and errno."
  - Change: add "Admission does not compare an `allow` or `deny` label with its `rc` and `errno`; that relation is the emitter's, and the host tests it only as a condition of `query_first`."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `runner_unit/pwrunner_core_unit_executable` (`ValidatorEvidenceTests.swift:154-163` asserts acceptance and preservation of allow/-1/13; `OrderingTests` reject `query_first` for it).

- **`wire.validator.support` limits, `:235`** — DT-37.e. `independent` [pass B]
  - Current: "Duplicate query-key behavior is source-read".
  - Change: replace the last sentence with "Duplicate query-key behavior has its own check-read support under Repeated native query keys."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (support metadata; no stamp change).
  - Check: `validator_batch_mode/batch_ndjson_roundtrip` (`duplicate_order{0,1}`).

- **Two `porcelain.rs: pub fn decode` citations** — DT-40.c3. `independent` [pass B]
  - Current: `pub fn decode` matches three definitions (`controller/src/porcelain.rs:32`, `:155`, `:174`).
  - Change: cite `pub fn decode<T: WireRead>(data: &[u8])`.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/generator_contract` (citation presence).

### `docs/contract/30-reply.surface.md`

- **`reply.record.policy_format`, `:69`** — DT-44.h. `independent` [pass B]
  - Current: names only decode refusal for `unknown`.
  - Change: "The ordinary policy format when available; a decode refusal uses `unknown`, as does a capacity refusal whose ordinary format is absent or exceeds its bound."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (reply stamp changes).
  - Check: `failure_boundaries/admission` (`check.py:157`).

- **`bad_policy` outcome row, `:199`** — DT-30.e. `independent` [pass C1]
  - Current: stated in the present tense as a reachable outcome.
  - Change: "Defensive: the host's policy-hash step could not identify the ordinary source after admission. Admission refuses a missing source or another format as `bad_request` first, so no admitted request reaches it."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`PWRunnerService.swift:376-394`; `ProbeRunner.swift:54-63`); `tests/COVERAGE.md:18` already calls it defensive.

- **`reply.record.outcomes`, `runner_timeout` row, `:201-202`** — DT-44.f. `after R13` — confirm that after the host maps `schedule_complete`, `ended_before_arrival` and `ended_before_completion` to `completion`, a cancelled actor schedule still yields `runner_failed` and no actor stop carries `sentinel_deadline`. [pass B]
  - Current: "Host sentinel or policy-transfer deadline expired" (silent on the actor case).
  - Change: add "Expiry of the actor schedule's execution allowance is reported as `runner_failed`."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`CWorkerDisposition.swift:276-277`, `:361-365`; `ActorOrchestration.swift:424-425`). No executed reply-level witness exists; the owner's support stays source-read for this clause.

- **Publish support owner, `:281-288` (pin at `:286`)** — DT-38.c. `independent` [pass B]
  - Current: "Independent minimal/empty paths are read in source."
  - Change: "Repeated writer failures reach the independent minimal writer, whose frame equals a separately constructed minimal report, and a failing minimal writer returns empty bytes." (asserted at `ReplyFailureTests.swift:247-312` and `:314-330`).
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `runner_unit/pwrunner_core_unit_executable`.

### `docs/contract/31-steps.surface.md`

- **`native_rc` meaning, `:59`** — DT-108.f. `independent` [pass J]
  - Current: "Native return carried by an associated allow, deny or error record. Synthetic results carry explicit null when result_source is present."
  - Change: append "No reader checks this relation: a result marked `synthetic` that carries a native return is admitted and projected as received."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (the producer has one assignment site, `CWorkerStepResults.swift:46-49`).

- **`missing_reason` meaning, `:63`** — DT-24.a. `independent` [pass C1]
  - Current: `validator_not_invoked` "when collection never ran".
  - Change: "`query_not_requested` for a planner exclusion; `validator_not_invoked` when no validator process supplied output for the phase, whether collection never ran or it ran and could not start one; `validator_no_verdict` when a validator ran and produced no uniquely associated record."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `witness_contract/validator_spawn_failed_reports_degraded` with the added `missing_reason` assertion.

- **`sandbox_check.pid` meaning, `:75`** — DT-24.b. `independent` [pass C1]
  - Current: the PID "targeted by this phase's validator collection".
  - Change: "Worker PID recorded for this step when worker output exists, including for a query the planner excluded. Whether a collection addressed that PID is stated by the phase's `collection_status` and `validator_subprocess`."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `witness_contract/phases` with the added excluded-step `pid` assertion.

- **`operation_relation` field meaning, `:275`** — DT-15.c. `independent` [pass A]
  - Current: "`unresolved` means the mapping cannot assign a single operation".
  - Change: "`unresolved` means the action has no single mapped operation, or the query is a wildcard spelling other than the matched `process-exec*`."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts`; behavior already asserted by `witness_contract/comparison_matrix` row S12.

- **`target_relation` meaning `:283` and rule prose `:754-755`** — DT-25.a, DT-25.c (R9 keeps target equality canonical and has it stated). `independent` [pass L]
  - Current `:283`: "`same_submitted` or `different_submitted` compares submitted strings when the query filter matches the action's mapped filter and both strings exist". `:754-755`: "Target equality compares submitted strings; runtime object identity requires its own observations".
  - Change `:283`: "…compares submitted strings under canonical Unicode equivalence when…". `:754`: "Target equality is canonical Unicode equivalence of the two submitted strings, so equal targets can differ in UTF-8 bytes;".
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `runner_unit/pwrunner_core_unit_executable` ("canonically equivalent targets with different UTF-8 bytes are same_submitted"); the two new controls in `blackbox_e2e/checker_controls`.

- **Assembly support owner, `:562-571`** — DT-38.a. `independent` [pass B]
  - Current pin: "Completed, incomplete, absent and unsupported slots map to distinct provenance and outcomes; action mapping preserves exec child observations."
  - Change: add checks `WorkerEvidenceTests.swift: runWorkerEvidenceTests` and `DispositionResolverTests.swift: runDispositionResolverTests`; pin "The attempt builder maps completed, non-completed and unsupported slots to their outcomes and preserves an exec child PID; step-assembly controls assert synthetic query provenance and the slot_incomplete and slot_absent attempt reasons."; add to limits "Incomplete and absent slots share one outcome and differ only in missing_reason. No cited control asserts attempt_not_supported provenance through the step builder."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (metadata; no stamp change).
  - Check: `runner_unit/pwrunner_core_unit_executable`; `source_drift/generator_contract` (citation presence).

- **Relations support owner, `:766-774`** — DT-38.b. `independent` [pass B]
  - Current pin: "The scenario matrix checks mapped operations, submitted relations, order and limitation values, including spawn and unlink distinctions."
  - Change: pin "… checks mapped operations, submitted relations and the producer's limitation values over constructed channel results, including spawn and unlink distinctions; the record's order equals the order supplied to the producer."; add to limits "Each row supplies its order, and the test adapter appends the lifecycle limitation."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `runner_unit/pwrunner_core_unit_executable`.

### `docs/contract/32-lifecycle.surface.md`

- **`exit_requested`, `:74-76`** — DT-129.a. `independent` [pass E]
  - Current: "Whether the host performed the release store asking the worker to exit. Worker receipt is a separate observation".
  - Change: add "The host also performs this store for a child it has already reaped; `grace_end: not_entered` and, for an actor, `owned_reap.departure_requested: false` then record that the ending preceded the request."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`ActorScheduler.swift:560-565`); retained E3 capture shows the combination.

- **`cleanup_trigger` field meaning, `:90-92` — merged edit** — DT-46.a, DT-46.b, DT-120.b, DT-120.d, DT-121.a (pass E) with DT-30.d (pass C1). `after R13` — confirm the final `triggerForStop` entries in `PWRunnerDisposition.swift:21-23` and that every other scheduler reason is still carried unchanged. [pass E]
  - Current: "Host fact recorded when it requests exit: deadline_expiry, completion, child_reaped, poll_wait_error, policy_transfer_error or policy_transfer_timeout."
  - Pass E text (R13 variant): "Why the host requested exit, derived at final collection from the stop reason it held when it stored the request: sentinel_deadline gives deadline_expiry; done and, in the actor form, schedule_complete, ended_before_arrival and ended_before_completion give completion; child_reaped gives child_reaped; wait_error gives poll_wait_error; policy_write_error and policy_transfer_deadline give policy_transfer_error and policy_transfer_timeout. Any other stop reason is carried unchanged. The value restates poll_stop_reason and is not a second observation."
  - Pass C1 requirement: if a fallback remains, add an open vocabulary block in the form `poll_stop_reason` uses (`:64-70`) and say an actor-form reply carries the scheduler's stop reason unmapped.
  - Gap between passes: each defers the vocabulary-block decision to the other. Recommended: pass E's text (its "carried unchanged" sentence is C1's statement) plus the open, illustrative block listing the six mapped values. Before `--refresh-shapes`, check whether the block changes the lifecycle shape golden (pass C1 found goldens carry no vocabulary values; pass B warns a declared vocabulary may change one) and review any change.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: the oracle derivation check (`tests/lib/lifecycle_oracle.py`); `witness_contract/actor_compositions` after the rebuild.

- **`collection_basis`, `:100`** — DT-30.c. `independent` [pass C1]
  - Current: lists `unavailable`.
  - Change: "`after_confirmed_reap` or `execution_may_continue`; absent when the host recorded no basis. Readers also accept `unavailable`, which no producer assigns."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`ActorSession.swift:629`).

- **`lifecycle.host_wait.stop`, `:290`** — DT-44.a1, DT-44.a2, DT-44.a3. `independent` [pass B]
  - Current: `clock_unavailable` "failed or backward time with bounded sleep fallback"; "setup_failed denotes an unavailable nonblocking prerequisite".
  - Change: "Owning operation's reason for ending this wait; each owning record defines its values and the set is open. clock_unavailable is the termination gate's stop when a time sample it required failed, moved backward or was absent. A wait that loses the clock elsewhere continues on bounded sleeps, keeps its own stop value and reports clock_fault. setup_failed denotes a prerequisite that could not be established before waiting: the nonblocking readiness reader, or actor authority-region and custody setup." Do not declare a vocabulary (it would change the shape golden).
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (lifecycle stamp changes).
  - Check: `runner_unit/pwrunner_core_unit_executable` (`ActorSchedulerTests.swift:204-259`); the non-gate half is source-read (`CWorker.swift:1040-1045`).

- **`lifecycle.worker_evidence.readiness`, `:443`** — DT-44.l1. `independent` [pass B]
  - Current: "readiness-write native result".
  - Change: "Worker publication of its readiness-write helper result, independent of the host's receipt of the byte."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`pw_probe_runner.c:394-402`).

- **`lifecycle.progress.index`, `:490`** — DT-44.c. `independent` [pass B]
  - Current: attributes the wait index to "actor waits".
  - Change: "… and activation and release waits identify their visit's first slot. Every phase of either request form has a release wait; activation waits occur only in the actor form."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`pw_probe_runner.c:1208`, `:1259`, `:1152`).

- **`lifecycle.policy_read` introduction, `:619`** — DT-44.l2. `independent` [pass B]
  - Current: "the worker publishes both counts".
  - Change: "At EOF the worker publishes the count it received before comparing it with the host-written expected count; the host reports both counts once it acquires that publication."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`pw_probe_runner.c:1468-1469`; `CWorker.swift:635-641`).

- **Resolution rule `free.condition`, `:659`** — DT-43.a. `independent` [pass E]
  - Current: "Resolve each question from the owning worker's acquired output, unique slot identities and submitted plan."
  - Change: "Resolve each question from the owning worker's acquired output and unique slot identities. The ordinary form joins them to the submitted plan; the actor form takes each actor's steps from that actor's collected slot list, in which every slot is a supported operation. A not_reached or unpublished conclusion requires terminal collection where specified below."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (lifecycle stamp changes).
  - Check: reading (`ActorOrchestration.swift:307`; `CWorkerDisposition.swift:148-149`); `source_drift/build_contracts`.

- **`not_reached` statement, `:666-667`** — DT-44.d. `independent` [pass B]
  - Current: "A final earlier progress position establishes `not_reached` only after confirmed reaping and with an incomplete slot; beside a completed slot it produces D5."
  - Change: "… only after confirmed reaping and without a completed slot, whether that slot is incomplete or absent; beside a completed slot it produces D5."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: new constructed control in `DispositionResolverTests.swift`; existing agreement of `CWorkerDisposition.swift:191`, `tests/lib/lifecycle_oracle.py:184-185`, `controller/src/porcelain_admission.rs:600-601`, `tests/FAILURE-PROPAGATION-CONTRACT.md:475`.

- **`claim_value` subject prose, `:810-816`** — DT-43.b. `independent` [pass E]
  - Current: the subject shows only the generated alternatives table labelled `Integer` and `Request`.
  - Change: add "JSON carries the chosen alternative's value directly: an integer for an exit code, signal or item index, or the termination-request object. The alternative labels are not JSON keys."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts`.

- **Run question for the exit-request reason, `:869-871`** — DT-46.a. `independent` [pass E]
  - Current: "Recorded reason for requesting exit".
  - Change: "Reason for requesting exit, copied from the worker's cleanup_trigger; inapplicable when exit_requested is false."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts`.

- **`lifecycle.validator.read_error` `:1107` and `stdout_collection_stop` `:1111`** — DT-44.e. `independent` [pass B]
  - Current: `read_error` "Host diagnostic for stdout-read failure"; `stdout_collection_stop` "Host reason for stopping stdout collection".
  - Change: `read_error`: "Host diagnostic for the condition that ended collection early: a stdout read failure, the retention limit, a poll or clock failure, or expiry of the I/O deadline; separate from accepted record contents." Add to `stdout_collection_stop`: "eof beside a deadline diagnostic records that stdout had already ended when the I/O deadline expired with request bytes still unwritten."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`ValidatorClient.swift:284-291`); no fixture. See the pass C2 entries for DT-54 before finalizing the `read_error` wording, since the failure contract describes the same collection stops.

- **`decode_fault.kind` support owner `limits`, near `:1269-1273`** — DT-30.g. `independent` [pass C1]
  - Current: declared closed and exhaustive; no reader rejects another value.
  - Change: add "The host receiver assigns only these three kinds. Product recipients do not re-check the value; the independent consumer rejects any other."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: rejected control in `blackbox_e2e/checker_controls` (see `tests/lib/consumer.py`).

- **Surface support pins, `:1534`** — DT-43.c. `independent` [pass E]
  - Current: "explicit rule and evidence gaps preserve scope" (the surface declares no gap node).
  - Change: "Imported public field definitions joined to producer/decoder/assessment meanings."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (owner metadata; no public payload change).
  - Check: `source_drift/build_contracts`.

### `docs/contract/33-actor_evidence.surface.md`

- **`actor_evidence.actor.setup_status`, `:51-59`** — DT-44.b2. `independent` [pass B]
  - Current: lists `setup_timeout` with no meaning.
  - Change: append "setup_timeout labels an actor whose setup publication did not arrive within the shared setup allowance, and also an actor whose launch was not attempted because that allowance was already exhausted; the second has no launch or subprocess record and application basis worker_not_launched."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (actor_evidence stamp changes).
  - Check: new constructed control in `ActorSchedulerTests.swift` (two actors; the second has `setupStatus == .setupTimeout` and no pid).

- **Executed owner's `limits`, `:157` (`source_snapshot` at `:165`)** — DT-11.b. `independent` [pass A]
  - Change: the same reviewed-inputs limit sentence as in `21-wire.surface.md`.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts`.

- **`arrival_observed` `:429`, `completion_observed` `:433`** — DT-44.i. `independent` [pass B]
  - Current: one field text for both request forms.
  - Change: `arrival_observed`: "… The ordinary form reports the final acquisition of the phase's publication after cleanup; the actor form reports what the scheduler observed while that visit was active." `completion_observed`: "… at the same form-specific point; in the actor form a completion published after the visit's wait ended is not included."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`ActorSession.swift:632-637`, `ActorScheduler.swift:386`, `:462`).

- **`actor_evidence.schedule.cancelled`, `:544-546`, value list** — DT-44.b1 (merge with the DT-10.a/.d clause on the same meaning; one edit). `independent` [pass B]
  - Current: "Recorded schedule cancellation reason, such as preparation_refused, execution_allowance_exhausted, an equipment failure or termination_dependency followed by its outcome".
  - Change (pass B): "Recorded schedule cancellation reason: preparation_refused, execution_allowance_exhausted, equipment_execution_ followed by the inspection failure, termination_dependency: followed by the gate outcome, unresolved_termination or actor_quiescence_unresolved when a stopped actor was not reaped, or ownership_lost after a failed wait on the active actor; absent when no cancellation was recorded." Then append the pass A clause: execution_allowance_exhausted is the scheduler's classification; `execution_wait.elapsed_ms` and `execution_wait.clock_fault` show whether exhaustion was measured.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (string literals at `ActorScheduler.swift:474`, `:553`, `:177`, `:479`).

- **"A timeout followed by cleanup" support owner, `:828-838` (pin at `:835-837`)** — DT-38.d. `independent`. Edit only if the ordering assertions in `ActorSchedulerTests.swift` are not added. [pass B]
  - Current pin: "later source reap and unchanged timeout".
  - Change (fallback): pin "… and a final result that keeps timed_out beside the source's reaped quiescence" with the limit "The control reads one final result and does not order the reap after the gate's timeout."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `runner_unit/pwrunner_core_unit_executable`.

### `docs/contract/34-equipment.surface.md`

- **Presence rules: `equipment.manifest.schema_version`, `.contract`, `.worker_identity`, `.unsigned_worker_sha256`, `.workers`; `equipment.manifest_worker.role`, `.relative_path`, `.sha256`, `.cdhash`, `.identifier`, `.entitlements_xml`** — DT-18.b, DT-18.d. `independent` [pass A]
  - Change: author each field's presence rule after reading its decoder and admission.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: presence ratchet in `source_drift/build_contracts`.

- **Equipment diagnostic `operation`, `:400`** — DT-30.a. `independent` [pass C1]
  - Current: lists eleven names.
  - Change: state the seven assigned names (`signing_information`, `worker_signature`, `inventory_read`, `inventory_decode`, `worker_path`, `worker_hash`, `worker_entitlements`); say product readers also accept `service_seal`, `guest_code`, `dynamic_validity` and `associated_static_code`, which no producer assigns to this field; say an error in `equipment_inventory.error` after a failed service-seal inspection names the static inspection call (`worker_signature` or `signing_information`).
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (no shape golden carries vocabulary values).
  - Check: reading (`ActorEquipment.swift:221-254`, `:324-329`, `:334-357`, `:389-447`); `source_drift/build_contracts`.

- **`ownership` definition, `:870` (one edit for two rows)** — DT-128.a, DT-128.b, DT-128.e, X-2 (`performed`); DT-68.a, DT-127.e, DT-127.h, X-7, X-8 (time anchor). `independent` [pass D]
  - Current: "Named ownership states: object_name, descriptor and mapping use not_acquired, held, released or unresolved; shared_erasure/private_erasure use not_present, performed, withheld_not_quiescent or unobserved."
  - Change: append "Each value records the last operation published for that resource in its scope, not an inventory at reply time. Host region and custody values come from the host's own setup and teardown calls. A worker scope's values come from cells that worker published before it exited, so worker `mapping: held` records a successful setup mapping with no published unmap, including for a worker the same reply reports reaped." and "`performed` records that the scope's clearing operation ran over its assigned storage; it does not state that token bytes were present."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (`equipment` stamp changes; rendered at `docs/RESPONSE.md:2452`).
  - Check: `source_drift/build_contracts`; both independent readers already refuse `released` without a succeeded cleanup cell (`tests/lib/actor_evidence.py:100-113`, `controller/src/porcelain_actor.rs:312-358`).

- **Setup decision rule `free.effect` `:890-891`, prose `:894-899`, `retained_free` reason** — DT-60.a, DT-60.b. `independent` [pass E]
  - Current: "For an observed decision, validate its raw actor/required association before projecting the decision and its primary operation."
  - Change: "Retain independently valid operation cells even when the decision is absent. For an observed decision, compare its raw actor/required association with the session's and record `setup_association_mismatch` on a difference; the decision and its primary operation are still projected, under the session's own actor index and required flag." Add to the prose: "A scope carrying integrity errors supports no readiness: the scheduler treats that actor's setup as failed, and the controller reports a ready or not_required decision beside integrity errors as invalid." Update the `retained_free` reason ("checked during projection").
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (equipment stamp changes).
  - Check: constructed mismatch controls in `ActorAuthorityTests.swift:155-178`.

- **After the `decision` condition, `:912-917`** — DT-61.b, DT-133.a. `independent` [pass E]
  - Change: add "The worker publishes ready only after its core-limit, descriptor, size, mapping, close and header-binding cells succeeded. The host decoder checks the decision against `required` and does not re-check those cells." and "Before a required actor's setup counts as usable the scheduler also requires the worker's private header status word to report the mapped region. That word is not a reply field; a refusal on it is reported as setup_failed and its value appears only in the run's error text. The controller relates an actor's application to a terminal scope only and does not re-derive ready from its cells."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: consumer readiness relations (`tests/lib/actor_evidence.py`).

- **Cell `value` meaning, `:992`** — DT-128.a, DT-128.b. `independent` [pass D]
  - Current: "Operation-specific unsigned native observation when the cell marks a value present, such as object/page size."
  - Change: after "such as object/page size" add "or the bytes a clearing operation overwrote, which can be zero".
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts`.

- **Surface support pins, `:1052`** — DT-43.c (pass E, outside the review item 5). `independent` [pass E]
  - Change: the same replacement as `32-lifecycle.surface.md:1534`; this surface has no gap node either. (`33-actor_evidence.surface.md:880` has one gap node at `:840` and keeps its sentence.)
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts`.

### `docs/contract/35-profile.surface.md`

- **Status prose, `:35`** — DT-100.a, DT-100.b, DT-100.c, DT-100.d. `independent` [pass I]
  - Current: "`captured` states that the host's capture checks passed. `unavailable` states that a capture condition failed."
  - Change: add "The host evaluates application and worker completion before it reads any capture record. An `unavailable` receipt therefore does not report whether the worker copied the object, and a completed copy is withheld when application was not observed to succeed or the worker did not complete cleanly."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (profile stamp changes; add no `free.*` fact).
  - Check: `runner_unit/pwrunner_core_unit_executable` (`CompiledProfileCaptureTests.swift:86-87` rejects `captured` when `applied` is false); retained run re-shows the kill-after-application receipt.

- **Reason prose, `:47`** — DT-99.a, DT-99.b, DT-99.c, DT-99.d. `independent` [pass I]
  - Current: "The host names the first failing capture condition. The controller's label check accepts the carried reason string."
  - Change: add "`worker_capture_refused` covers every worker capture status other than captured: an unsupported type, reserved word or extent (including an empty object and one above the limit), an unreadable object, and malformed consumed input. The receipt does not say which. The host's extent and type condition repeats checks the worker makes before it records captured status."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: after the Swift coverage repair, the status-corruption row asserts `worker_capture_refused`.

- **`producer` `:55` and `capture_stage` `:59`** — DT-96.a, DT-96.b, DT-96.d. `independent` [pass I]
  - Current: "`worker` on a captured receipt identifies the component that captured the bytes."; "`before_apply` on a captured receipt identifies when the worker captured the bytes."
  - Change: producer: "`worker` on a captured receipt names the component whose program copies the bytes. The host writes this value on every captured receipt; no worker publication carries it." Stage: "`before_apply` on a captured receipt names the position of the copy in the worker's program, between compilation and application. The host writes this value on every captured receipt; it is not a recorded observation of that order."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`CWorker.swift:712-713`; `pw_probe_runner.c:1574-1641`).

- **`request_nonce`, `:63`** — DT-97.b, DT-97.c. `independent` [pass I]
  - Current: "… A comparison with a separately retained request nonce supplies a consumer's request association; the controller's carried-label check has no request-nonce operand."
  - Change: add "The nonce enters no compiled byte and no digest; the comparison associates the receipt with the reply that carries it."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading; the retained run shows three nonces with identical bytes.

- **`bytecode_b64`, `:85`** — DT-103.a–e, CL.b1–b3. `independent` [pass I]
  - Current: "The bytes copied from the compiler object passed to `sandbox_apply`, presented as base64."
  - Change: add "The worker reads that object through a fixed four-member view (type, reserved word, byte pointer, length) of a private structure. The receipt establishes that the bytes read this way matched their recorded length and digest. It does not establish the structure's layout on the running system, or which bytes application submitted."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `runner_abi_layout/c_swift_layout_agreement`, `witness_contract/max_targets_reply_survives`, `runner_outcome_bad_request/accepted_input_contract` (they reject a layout change that makes the type or reserved word nonzero, the length zero or the pointer unreadable; none can reject a readable but different extent).

- **"Captured input identity", `:112`, with a link to `policy.imports.holds` (`RESPONSE.md#contract-policy-imports-holds`) — linked pair with `11-policy.surface.md` after `:577`** — DT-98.a, DT-98.b, U1.s1.98, U1.s2.e, U1.s5.q3, U2.s2.a, NW2, DX1, DX2. `independent`; land with the inventory-side sentence. [pass I]
  - Pass I text: "The identity covers the source string and the parameter strings passed to the compiler. No receipt field identifies a file the compiler reads for an `import` form, so equal source and parameter identities do not imply equal bytecode."
  - Pass G (inventory side) text: "No field of a run envelope or a helper envelope associates an import record with the bytes the worker's compiler read. The dossier's applied-source digest, the reply's policy digest and the receipt's source digest are digests of one held source string; their equality says nothing about imported files."
  - Conflict: the placements agree (each owner states its own exclusion; the receipt side links to the inventory side). The wording differs in scope: pass G's re-executed contrasts show files reaching the compilation with no `import` form (`load`, `eval`, an aliased or applied `import`), so "for an `import` form" understates the exclusion. Recommended receipt-side sentence: "The identity covers the source string and the parameter strings passed to the compiler. No receipt field identifies a file the compiler reads, so equal source and parameter identities do not imply equal bytecode." Do not reintroduce "no reader compares"; do not write that compiled bytes carry no path information.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: structural (`pw_profile_capture.h:60-71`); optional live control (see `tests/suites/runner_outcome_bad_request/contract.py`).

- **Host support owner `limits`, `:281-290` (limits at `:289`)** — DT-101.b, DT-101.d, DT-101.g, DT-101.h, DT-101.j. `independent`; interim text until the Swift coverage repair lands, then replaced by the strengthened pin. [pass I]
  - Change (interim): "The corruption cases assert unavailability without a reason; reasons are asserted for the application guard with one input and for the extent guard. The first-failure order and the remaining withheld fields are source-read."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (owner-only; no public payload change).
  - Check: `source_drift/build_contracts`.

- **Labels rule prose, `:299-337` (prose at `:309`)** — DT-95.a, DT-95.g, DT-95.AT.b, DT-95.AT.e, DT-95.AT.f, DT-104.d, DT-134.a, DT-134.c, CL.c6. `independent`. The rule's `withhold` effect is edited for DT-32 by pass K at the same rule; write the rule once. [pass I]
  - Current: "After public producer admission and reply-capacity checks, the controller applies these conditions to every present receipt … The retained nonce, bytecode, digests, lengths and counts remain the host's assertions; their production checks belong to the host capture rule."
  - Change: add "The controller compares no receipt field with the request it delivered, with the reply's worker record or with the receipt's own bytes, and evaluates neither extent condition. A `finished` result beside a `captured` receipt reports the host's capture checks, not a controller comparison."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `unit/rust.unit` (the label test, once corrected to name the admitted disagreeing row).

- **Labels rule effect, `:334`** — DT-32.c, DT-119.d (with DT-104.b, pass I: one decision). `independent` [pass K]
  - Current: `withhold(envelope.data.runner_sandbox_diagnostics)` and no exit code.
  - Change: `set_value(envelope.result.exit_code, 1)` and `set_value(envelope.data.runner_sandbox_diagnostics, None)`, the effects `41-diagnostics.surface.md:355` already states and the producer emits (`run_flow.rs:66-71`, `:126`).
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (structured public content).
  - Check: `source_drift/build_contracts`; the key-presence assertion in the Rust label test (Controller B). Conflict note: pass I's interim pin for the "Constructed run labels" owner says the check reads the diagnostics value "without distinguishing an absent key"; once the key-presence assertion lands that pin is false. Write the pin in its final form if the Controller B correction has landed.

- **"Constructed run labels" owner, `:339-351` (pins/limits `:348-350`; `run`, `source_snapshot` `:344-345`)** — DT-95.d, DT-104.a, DT-104.b, DT-104.c. The limits are `independent`. The pin's "diagnostics value" wording and the `run`/`source_snapshot` refresh are `after R10` in the sense that the Controller B thread (R10, R11) carries the corrected Rust label test — confirm the test's final name, the diagnostics key's asserted form (present with JSON null, following the DT-32 disposition) and the `unit/rust.unit` run at the carrying commit. [pass I]
  - Current pin: credits "diagnostic presence"; executed credit names run `20261110T195016Z_0d197151` at `5e51300d`.
  - Change: pins → "The constructed check follows status and label admission through the public outcome, exit status, result and retained decoded report; it reads the diagnostics value as null without distinguishing an absent key." limits add → "Eight of the seventeen refused rows carry a non-string or absent status or label and are refused by the test's typed JSON reader as a client decode refusal before label admission. The admitted captured row's nonce, source and parameter fields do not correspond to the test request; admission here establishes nothing about request association." Refresh `run` and `source_snapshot` from the `unit/rust.unit` run at the commit carrying the corrected test, or grade the owner `check_read` until then.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `unit/rust.unit`; `source_drift/build_contracts`.

- **Source owner pin `:394` and limits `:396`** — DT-97.b, DT-98.b, DT-103.e, U1.s5.q3, U1.s7. `independent` [pass I]
  - Current pin: "Fields bind the observed worker, nonce and consumed input bytes." Limits: "Live capture behavior and platform private-layout compatibility require their native checks."
  - Change: pin → "The host compares the worker-recorded PID, nonce, source identity and parameter identity with its own values before emitting them; files read for imports are outside these identities." (recommended variant, matching the linked pair: "files the compiler reads are outside these identities"). Limits → "Constructed-layout controls (`tests/suites/runner_abi_layout/capture.c`) and live captures (`witness_contract/max_targets_reply_survives`, `runner_outcome_bad_request/accepted_input_contract`) show that the reading yields captured status and self-consistent, repeatable bytes on the tested system. None decodes the bytes, compares them with a reference compilation or observes what application submitted."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (owner-only).
  - Check: `source_drift/build_contracts`.

### `docs/contract/40-envelope.surface.md`

- **`result.error`, `:112-117`** — DT-32.b, DT-119.b. `independent` [pass K]
  - Current: "After execution admission, precedence is host error, client `stdout_capture_error`, client `stdout_parse_error`, then a generic unsuccessful-run message."
  - Change: "Human-readable diagnostic, null on successful controller/helper results. A refusal carries the refused boundary's diagnostic. After execution admission it is the host reply's `error` when present, otherwise a generic unsuccessful-run message; client `stdout_capture_error` and `stdout_parse_error` accompany only refused captures."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (envelope stamp changes; edit existing text, add no `free.*` fact).
  - Check: `source_drift/build_contracts`; the generic-message assertion is a `controller/src` test (handed to Controller B).

- **`data.runner_sandbox_diagnostics`, `:141-145`** — DT-31.a, DT-113.d. `independent` [pass K]
  - Current: "An admitted execution with no host report can still produce the controller's no-worker assessment".
  - Change: "Assessments after client/reply admission. Null for earlier refusals and tool errors. An admitted reply with no worker subprocess record has the no-worker assessment."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`porcelain_admission.rs:1579-1587`, `:1642`).

- **Classification rows `:242` (`runner_response_unavailable`) and `:243` (other admitted host label)** — DT-31.a, DT-113.a–d, Q1.c, DT-119.a. `independent` [pass K]
  - Current `:242`: "`runner_response_unavailable` | Completion has no host result to supply an outcome; exit 1."
  - Change `:242`: "`runner_response_unavailable` | Selected for an admitted completion that carries no host reply; exit 1. No client output reaches this row: capture admission yields a decoded host reply whenever it reports no failure." `:243` add: "A host label is copied without comparison with the controller's refusal spellings; a non-null `runner_result` with terminal `runner_reply` identifies a host-supplied label."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`. The row, the label and the `help result` card line stay (no interface inventory change).
  - Check: `help result` re-executed now on the `2f4d76e4` app prints the line; the parser-equivalence control is a `controller/src` test (handed to Controller B).

- **`admit` rule, `:251-252`** — DT-31.b, DT-114.e, DT-116.h. `independent` [pass K]
  - Current `:251`: "…then decoded host producer identity and host capacity/profile-label admission."
  - Change: `free.condition`: "Check request delivery error first, then client failure (capture admission, host frame admission including its schema fingerprint and producer contract, and transport terminal), then host capacity and profile-label admission of the decoded reply." Last sentence of `free.effect`: "An accepted capture with terminal xpc_error and no delivery error adds independent fallback compilation."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `unit/rust.unit` (`runner_client.rs:1391-1407`, `:1243-1282`).

### `docs/contract/41-diagnostics.surface.md`

- **Collection-bound support `pins` and `limits`, `:320-330` (`:327-329`)** — DT-32.a, DT-119.c. `independent` now with the interim limit; replaced `after R10` (Controller B adds the over-capacity run-level row). [pass K]
  - Current pin: "Collection bounds precede semantic joins and profile-context checking on run and verification admission; their refusal retains the decoded reply."
  - Change: say what the two cited controls call (the diagnostics function and `admission_problem` directly) and that the run-level refusal is source-read. Limit: "No control carries an over-capacity reply through `run` or `runner verify`; the run-level refusal and null diagnostics follow from the cited admission branch."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (owner-only).
  - Check: `source_drift/build_contracts`.

- **Controller ordering family row, `:678`** — DT-130.a, ACC-RES.order. `independent` (R9 changes the equality used inside the chain, not the direction stated here). [pass L]
  - Current: "comparison vocabulary and the complete `query_first` chain".
  - Change: "…comparison vocabulary and each claimed `query_first` against its complete chain. An `unestablished` order is not compared with eligibility."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: the `ordering-ordinary-withheld` reader-corpus row.

- **Finding family row for `reporting_failure`, `:683`** — DT-44.m. `independent` [pass B]
  - Current: the family applies to "A reply carrying reporting_failure".
  - Change: append "A reply whose outcome is runner_reporting_failed without that record receives the same finding kind and continues through the ordinary checks."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (diagnostics stamp changes).
  - Check: reading (`controller/src/porcelain_admission.rs:1469-1476`). Optional Rust control: see `controller/src/porcelain_admission.rs`.

- **Executed owners' `limits`, `:761`, `:1154`, `:1168` (`source_snapshot` at `:769`, `:1162`, `:1176`)** — DT-11.b. `independent` [pass A]
  - Change: the same reviewed-inputs limit sentence as in `21-wire.surface.md`.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts`.

- **Actor `stop_reason` field, `:803-807`** — DT-121.d. `independent` (R13 does not change `poll_stop_reason` or this projection; confirm after the host thread). [pass E]
  - Current: projects only the six ordinary values; silent on the scheduler's reasons.
  - Change: add "The scheduler's own reasons, such as schedule_complete or a visit end reason, are outside that set and project null; the actor's subprocess record keeps them in poll_stop_reason."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (diagnostics stamp changes).
  - Check: reading (`controller/src/porcelain_admission.rs:1403-1419`); retained E1b, E2, E5 captures.

- **Actor cause prose after the cause table, `:1014-1017`** — DT-121.b, DT-121.q, DT-121.e. `after R13` — confirm which stops still project `unknown` (timeouts, protocol violation, withheld release, failed setup) and that `schedule_complete` no longer does. [pass E]
  - Change: add "The actor scheduler never records sentinel_deadline, so no actor reply selects the deadline case." and the retained limit: "An actor stopped for an arrival, completion or setup timeout, a protocol violation, a withheld release or a failed setup keeps the scheduler's reason as its trigger. Its cause stays `unknown` even when the request result, exhausted grace and final status are all carried; read them in that actor's subprocess record." Keep the "Deadline expiry" row (`:972-977`).
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `witness_contract/actor_compositions` (R13 control). No executed actor-timeout observation exists; the limit is source-read.

- **Cause-rule support `limits`, `:1055` (support cited at `:1052`)** — DT-46.c. `independent` [pass E]
  - Current: cites `typed_host_cleanup_cause_requires_all_independent_observations` without scope.
  - Change: add "The test constructs each trigger and stop pair; it does not exercise the host's derivation of the trigger." Do not rename the Rust test.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts`.

### `docs/contract/42-dossier.surface.md`

- **`request_path`, `:104-106`** — DT-33.b. `independent` [pass C1]
  - Current: "null when preparation did not establish one".
  - Change: "Request-file path parsed from the command line; null when none was established, including when an option's value is refused, whether or not a path preceded it."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`run_flow.rs:443`, `:455` pass `None`). The frozen guide sentence ("when no path was given") stays contradicted.

- **`app_provenance`, `:120-122`** — DT-33.c. `independent` [pass C1]
  - Current: null "when its read or supported-schema parse failed".
  - Change: "…null when the run ended before the manifest was read, or when its read or supported-schema parse failed."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`run_flow.rs:524-531` returns before `:543-545`).

- **Dossier `status`, `:229`, limit L-B; `closure_sha256` `:233`, limit L-C; "Held input and file observation scope" `:83`** — DT-84.d, U1.5q3d, U2.1g. `after R12` — confirm the scanner's final grammar and the term used for unfollowed forms. [pass G]
  - Current `:229`: "`complete` exhausted the literal closure without a reported problem".
  - Change: "`complete`: every import form the scan recognized was followed and the walk ended with no unresolved name, read or decoding error, cycle or bound. It describes the scan, not the compiler's inputs." At `:233` the L-C closure sentence. (`:51` and `:263` are reworded to "import forms the scan did not follow" by the R12 thread.)
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: dossier contrasts in `witness_contract/dossier_witness`.

- **`imports.failure`, `cycle`, `exceeded`, `:239-249`** — DT-33.a. `after R12` — confirm the traversal order and the term for the root-source case once the scanner reports unfollowed forms (R12 replaces "nonliteral" reporting; see the pass G entries). [pass C1]
  - Current: "First collection problem" with no order stated.
  - Change: `failure`: "First collection problem in the scanner's traversal, scan setup failure or reason for a not-applicable scan; null when none was recorded. The traversal reports a nonliteral form in the submitted source first, then visits imports depth-first in byte order of their names; it is not source order." Add "in that traversal" to `cycle` and `exceeded`.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: order row in `tests/suites/witness_contract/check_dossier.py` (two absent names written in reverse order; `witness_contract/dossier_witness`).

- **Vocabulary note for `imports.failure` (pass C1's DT-33.a text)** — DT-33.a. `after R12` [pass G]
  - Conflict: pass C1's sentence says the traversal "reports a nonliteral form in the submitted source first"; pass G has R12 reword the dossier statements to "import forms the scan did not follow", and a flagged form may then have a literal argument. Recommended: write the DT-33.a sentence with R12's final term ("an unfollowed import form in the submitted source first") and confirm the order against `sbpl_imports.rs:313-320` after the scanner edit.

### `docs/contract/50-installation.surface.md`

- **Subtree support owner `limits`, `:14-21`** — DT-79.a. `independent` [pass F]
  - Current: "Managing runners and its descendants" graded check-read; none of the six cited checks exercises reconcile.
  - Change: add that its cited controls exercise neither reconcile, record location, service or plist inspection nor a registry load refusal. (The review's clause about `load_registry` on an absent path is mistaken: four of the six call it on a path not yet created.)
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts`.

- **Runner command result forms, after `:39`** — DT-35.a, DT-35.b, DT-35.c. `independent`; R2 adds a registry-inspection refusal that takes this stated form, and R6 adds the write-failure form at the same location in its own thread. [pass C1]
  - Current: `normalized_outcome` is stated only for `not_found` and verify; exit 2 is shared by an enveloped `not_found` and unenveloped refusals.
  - Change: add "A completed list, status, install, validate, remove or reconcile command reports `result.normalized_outcome: "ok"`, true `ok` and exit 0; for remove this includes a report whose `cleanup_retained` is true. A usage, argument, registry-load or operation refusal other than a lookup miss writes one reason to standard error, prints no envelope and exits 2."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: the new rows in `controller/integration/cli_contract.rs`.

- **Verify clause, `:97`** — DT-31.a, DT-113.c. `independent` [pass K]
  - Current: "an absent reply selects runner_response_unavailable and no PID."
  - Change: append "; capture admission supplies a decoded reply with every admitted capture, so no client output selects it".
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`runner_commands.rs:531-545`, `:614-623`).

- **`installation.commands.validate` free effect `:138`; `kind` `:302`; `unentitled_worker_sha256` `:332`; `worker_equipment_inventory` `:336`** — DT-44.j. `independent` [pass B]
  - Current: the "Refresh validation metadata" rule does not name three writes; `:332` "Unentitled-worker file hash retained at installation when available".
  - Change: the validate effect names the three writes (unentitled-worker hash, equipment inventory, `byoxpc` for a kindless record; a row whose host executable is missing is skipped before those writes). `unentitled_worker_sha256`: "Unentitled-worker file hash from the most recent installation or validation read, when available." `worker_equipment_inventory`: "Sealed equipment snapshot from installation, replaced by the verified current inventory at a successful validation, retained as JSON. …" `kind`: add "validation records byoxpc for a record with no kind".
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (installation stamp changes).
  - Check: source-read (`controller/src/runner_commands.rs:717-720`, `:733-735`, `:738`; `runner_manager.rs:1068-1076`). Not executed; a registry-only control (constructed registry and bundle directory, `runner validate`, read back the three fields) would witness it, and its support stays source-read until then.

- **New support owner under "Reconcile observations", under `:163`** — DT-79.c, DT-79.d, DT-72.d, DT-79.e. `independent`; cite the integration control once it exists. [pass F]
  - Change: an owner graded `check_read` citing `registry_recovery` (and the new integration control), stating what it asserts (row contents, a candidate, an inspection error, joint no-change) and does not: the assertions are opt-in; no-change comparisons cover reconcile together with other commands; no assertion reads `candidates` for an overlapping path.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/generator_contract` (citation presence).

- **Reconcile candidate paragraph, `:171-176`** — DT-71.a, DT-72.a, DT-72.b, DT-72.c, DT-73.a, DT-73.b, DT-80.b. `independent` [pass F]
  - Current: "Registered label/scope pairs are suppressed from candidates. Discovery establishes a candidate for inspection; cleanup authority requires the recorded identity and the independent ownership gates."
  - Change: add "Reconcile looks up a launchd service only for a record whose location resolved and for a candidate whose Label parsed. It does not enumerate launchd services, so a report with no row for a service is not an observation that the service is absent." "Suppression compares the parsed Label and the scanned directory's scope only. A plist at a recorded path whose Label cannot be read, or differs from the recorded service name, is reported in its record row and again as a candidate. `unregistered` means that no record in that scope has the candidate's parsed Label." "Another plist file that carries a registered Label in the same scope is reported in neither place, and on a location error the plist at the recorded path is not inspected." "Installation accepts any bundle identifier and executable name. An installed service with neither the label prefix nor the `PWRunner` executable name is not recognizable as a candidate without its record." Repeat the `unregistered` sentence at the `candidates` (`:871`) and candidate `recorded_state` (`:988`) fields.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (installation stamp changes; no `free.*` key added).
  - Check: reading (`runner_commands.rs:775-781`, `:837-860`); optional assertion in the integration control that a constructed foreign-label path appears in both places.

- **Plist ownership classification, `:207` — merged edit** — DT-76.a, DT-76.b (pass F) and DT-34.b (pass C1). `independent` [pass F]
  - Current: "Absent resources are classified ambiguous for ownership and retain their independently observed absent presence. Unknown presence produces unknown ownership."
  - Pass C1 text: "…Unknown presence produces unknown ownership, as does a present regular file whose content cannot be converted. A present path that is not a regular file is unowned."
  - Pass F text: "A present object that is not a regular file is unowned. A regular file whose content could not be converted is unknown."
  - Recommended: pass C1's; it extends the existing sentence. The two state the same branches (`runner_manager.rs:1380-1392`).
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: classifier unit control (rides the R2 rebuild; see the items handed to product threads).

- **Classifier owners `:209-216` and `:801-807`** — DT-79.b, DT-70.c. `independent` [pass F]
  - Current: both `source_read` with no `check`.
  - Change: add `check` citing `service_absence_requires_specific_observation_not_any_nonzero_exit` and `plist_and_service_evidence_independently_gate_cleanup_retirement` (`controller/src/runner_manager.rs`) with their constructed-input limits; carry the DT-70.c qualification (the present-without-program branch rests on an empty synthetic stdout; several `program` lines and native output of that shape are unobserved).
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/generator_contract`; `unit/rust.unit`.

- **Reconciliation introduction, `:847`** — DT-80.c, DT-80.d. `independent` [pass F]
  - Current: "The result reports successful reconciliation execution even when individual inspections remain unknown."
  - Change: add "The registry is read once, without the lock, before the per-row observations; a report is not a snapshot taken at one time." and "Reconcile waits without a time bound for each `launchctl print`, `id` and `plutil` child." Add no LIMITS row.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`runner_commands.rs:752`; `runner_manager.rs:1260-1263`, `:1156-1161`, `:785-799`); not exercised.

- **`records` field, `:863`** — DT-80.a. `independent` [pass F]
  - Current: says "retained cleanup entries".
  - Change: "One row for each recorded runner and for the nested runner of each retained cleanup entry, with current observations or a location error. A cleanup entry's `cleanup_started_at_unix_ms` and `observations` are not repeated; `runner list` returns them."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`runner_commands.rs:768-773`, `:455-460`).

- **Inspection errors field, `:879`** — DT-77.b, DT-77.d. `independent` [pass F]
  - Change: "…for every `.plist` entry in the scanned directories, whether or not it is a candidate. A property list that cannot be represented as JSON is one such failure and is recognized as a candidate only by filename prefix."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`runner_commands.rs:821-847`).

- **Record row `service` `:911`, `plist` `:919` and `error` `:973`** — DT-75.a, DT-75.c. `independent` [pass F]
  - Change: at `:911` and `:919`: "…otherwise only `{"presence":"unknown"}`: the resource was not inspected." At `:973`: "Location-check refusal text. It is the only field that distinguishes a recorded identity that disagrees with the current user, scope or paths from a location that could not be determined."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`runner_manager.rs:1322-1378`; `runner_commands.rs:784-787`). No output control exists for a location-error row; the dynamic-record owner already says so (`:1191`).

- **`service_ownership` `:946` and `plist_ownership` `:955` fields** — DT-70.a, DT-70.b. `independent` [pass F]
  - Current: list the four words only.
  - Change: add "`ambiguous` is assigned to an absent service and to a listed service without exactly one `program` line; read it with `service.presence`." and "Reconcile reports no retirement decision; `runner remove` decides retirement from its own observations." (the plist field takes the corresponding absent-plist wording).
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `unit/rust.unit` (`service_absence_requires_specific_observation_not_any_nonzero_exit`).

- **Candidate `ownership` field, `:1050`** — DT-76.a. `independent` [pass F]
  - Change: add "Assigned without reference to any record." (a symlink at a recorded path is `unowned` in its record row and `unknown` as a candidate; both are correct once this is said).
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: reading (`runner_commands.rs:863`).

- **Inspection-error `presence`, `:1074`** — DT-77.a. `independent` [pass F]
  - Change: "The constant `unknown`, marking a failed inspection. It is not the file's observed presence; a record row or candidate for the same path carries that."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `runner_byoxpc/registry_recovery` (`registry_recovery.py:340`) asserts the constant for a read failure.

### Several surface files: split symbol spellings

- **Owner `source:` lists naming `compare`, `gates`, `admission_problem`, `admit_reply`, `reply_contract`, `identity`** — DT-40.d1. `independent` [pass B]
  - Current: each symbol appears under two spellings in separate changed-item rows.
  - Change: use the definition-like spelling in every owner: `fn compare`, `fn gates`, `pub(crate) fn admission_problem`, `pub(crate) fn admit_reply`, `pub(crate) fn reply_contract`, `def identity`. Find with `grep -n '"symbol": *"\(compare\|gates\|admission_problem\|admit_reply\|reply_contract\|identity\)"' docs/contract/*.surface.md`.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/generator_contract`.

## Presentation map, CONTRACT introduction and contract README

### `docs/contract/README.md`

- **`checks` description, `:80-81`** — DT-14.a, DT-14.b. `independent` [pass A]
  - Current: "`checks` names catalog suites".
  - Change: add the validated limit: "A surface's `checks` list is validated only as catalog suite names; it is not compared with the checks its owners cite and selects no verification for a surface change."
  - Check: `source_drift/generator_contract`.

- **Link resolution paragraph, after `:96`** — DT-03.a, DT-03.b. `independent` [pass A]
  - Current: "Rendering resolves these links to the node's mapped document. The link checker verifies that the rendered destination actually contains the anchor."
  - Change: add after the first sentence: "Rebasing matches destination text within a paragraph that holds a link; show literal link syntax in a code span, not behind an escaped bracket. Write contract links with unencoded destinations."
  - Check: `source_drift/generator_contract`.

### `docs/contract/presentation.json`

- **CONTROLLER commitment lists: `commitments_preparation` `:362`, `commitments_selection` `:373`, `commitments_admission` `:389`** — DT-41.b1, DT-41.b2, DT-41.b3, DT-41.b4. `independent` [pass B]
  - Current: `commitments_selection` lists `equipment.binding` (`:376`); `commitments_admission` lists `steps.assessment.fresh` and omits `diagnostics.execution`, `diagnostics.issue`, `profile.receipt.labels`; four rules the preparation prose explains are in no list.
  - Change: in `commitments_selection` replace `equipment.binding` with `request.options`; in `commitments_admission` replace `steps.assessment.fresh` with `diagnostics.execution` and add `diagnostics.issue` and `profile.receipt.labels`; add `request.specimen.hold`, `request.options.failure_order`, `policy.augments.actors`, `refusals.controller.consequence` to `commitments_preparation`.
  - Conflict note: pass B's reason says `equipment.binding` "stays listed in BUILD"; pass A removes it from BUILD's `commitments_signing` (`:522`). With both edits the subject is listed only through `equipment.binding.bind` in WORKER's extensions list (`:480`). Recommended: apply both removals (each section's lead-in "Commitments explained here:" is then true) and accept that `equipment.binding` has no direct tour entry.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (no stamp change).
  - Check: `source_drift/build_contracts`.

- **BUILD commitment lists, `:509-534`** — DT-16.a, DT-16.c (and DT-41; see the B entry for the other tours). `independent` [pass A]
  - Current: `commitments_signing` lists `equipment.manifest` and `equipment.binding`; `commitments_evidence` lists `identity.build`, `equipment.inventory`, `equipment.manifest`; `commitments_identity` lists `identity.public.derive`.
  - Change: remove `equipment.binding` from `commitments_signing`; remove `equipment.inventory` and `equipment.manifest` from `commitments_evidence`; remove `identity.public.derive` from `commitments_identity` (it remains under `commitments_verification`).
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts` (regions regenerate).

### `docs/contract/trace-introduction.md`

- **Paragraph at `:20-25` (one combined edit)** — DT-40.a1, DT-40.a2, DT-40.b, DT-40.e2 (pass B) with DT-14.e and DT-20.b (pass A). `independent` [pass B]
  - Current: "The commitment index covers every routing unit. Source and interface associations are partial: an absent association is an unknown, and a source citation is evidence with the stated scope, not a declaration of every behavior that source can affect."
  - Change: replace the first sentence with "The commitment index has one row for each routed subject. A surface's own heading carries its introduction and surface-wide support, and the changed-item index names that heading where support is declared for the whole surface." Add after it: "Limit identifiers have no rows; a statement that embeds a limit shows its identifier, so a search of the statement documents for that identifier finds it." Then "Source, check and interface associations are partial: …" (pass A's one-word change) and the Known gaps scope sentence (pass A). The four changes do not conflict.
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/generator_contract`, `source_drift/build_contracts`.

## Generator code (R14 refusals, R8 schema validation, generated text)

### `docs/contract/presentation.py`

- **`:147-148` changed-item index record label** — DT-05.a, DT-05.b. `independent` [pass A]
  - Current: every `node.record` row is labelled "imported record declaration".
  - Change: label the row "authored record declaration" when `tree.records[node.record].get('authored')` is true (twelve records).
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (changes `docs/CONTRACT.md` only).
  - Check: new assertion in `ContractPresentationTests` (`tests/suites/source_drift/contract_tree_controls.py`, `source_drift/build_contracts`): `ControllerSelectionOptions` carries the authored label and `PWRunnerRunSpec` the imported one; rejects a renderer that labels every record row imported.

- **`render` destination validation, near `:167-172`** — DT-01.a (R14). `independent` [pass A]
  - Current: validation compares marker names and counts per mapped document (`:167-172`), checks each pair's own order (`:119-125`) and replaces sequentially (`:176-194`).
  - Change: before assembly, require that the declared regions of each document are disjoint (each BEGIN is followed by its own END before any other BEGIN); refuse otherwise, naming the document and both regions.
  - Regenerate: none (generator code; committed regions are sequential, so output is unchanged).
  - Check: nested-marker mutation in `tests/suites/source_drift/generators.py::test_contract_map_refusals_validate_every_destination_before_writing` (`source_drift/generator_contract`): generation and `--check` both refuse, checkout snapshot unchanged. Must reject a generation that returns or writes a destination lacking any declared region.

- **`render` destination validation, same loop** — DT-02.a (R14). `independent` [pass A]
  - Current: only documents the map names are inspected (`:76-79`, `:163-172`, `:209-217`); the comment at `:161-162` states the intent ("An obsolete marker must not keep an old statement alive outside the declared region inventory").
  - Change: refuse, before any write, a `GENERATED CONTRACT <region>` marker in a Markdown document directly under `docs/` that the map does not name. Today such markers occur only in the seven destinations, so no present refusal results.
  - Regenerate: none.
  - Check: moved-destination pair in the same `generators.py` test: (i) key renamed, file copied, old file kept: refused, snapshot unchanged; (ii) same with the old file's regions removed: accepted.

### `docs/contract/tree.py`

- **`SUPPORT_GRADES['executed']`, `:84`** — DT-11.a, DT-11.d, DT-11.e, DT-12.a, DT-12.c. `independent` [pass A]
  - Current: "The named run exercised the stated assertions with its identified source or build."
  - Change: "**executed:** The named run exercised the stated assertions with its identified source or build. A development run is disposable test output and may no longer be held; source and check links name the current files, which can differ from that source."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (rendered only at `docs/CONTRACT.md:1696`; not in `public.json`; no test pins it).
  - Check: `generate_contract_stamps.py --check`; `source_drift/build_contracts`.

- **`NOTATION`, `:1412-1423`** — DT-18.a. `independent`, but land with the per-field presence rules (DT-18.b), because the definition is true only once every such entry states its rule. [pass A]
  - Current: the notation does not define "as defined below".
  - Change: add that, for an input record, "as defined below" means the entry's meaning states whether the key is required, optional or may be null. Do not rename the phrase (it occurs 2,372 times in `docs/contract/public.json` and is pinned by `build_contracts.py:622-623` and `contract_tree_controls.py:244`).
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py` (CONTRACT only; no snapshot change).
  - Check: `source_drift/build_contracts`.

- **Controller findings introduction, `:1604-1605`** — DT-21.d. `independent` [pass A]
  - Current: the sentence says each row names the record members a check reads; five of nine rows say "See the linked rule."
  - Change: "A row names the record members its check's structured conditions read and links each structured consequence with what it reaches; where the rule states these in prose, the row refers to the linked rule."
  - Regenerate: `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `source_drift/build_contracts` (`contract_tree_controls.py:416-429` pins the row text, not the introduction).

### `docs/generate_contract_stamps.py`

- **`input_paths`, `:78-83`** — DT-02.a (R14). `independent` [pass A]
  - Current: declared inputs name the mapped destinations only.
  - Change: declare the `docs/*.md` documents that the new unmapped-marker scan reads, because fixtures copy declared inputs and receipts track them.
  - Regenerate: none.
  - Check: `source_drift/generator_contract` fixture runs (the moved-destination pair above runs in a fixture tree and fails if the scanned documents are not copied).

### `docs/generate_porcelain.py`

- **`validate()`, after `:111` and inside the variant loop `:128-136`** — DT-110.a–d, DT-107.e, DT-106.d (R8, generator-side schema validation). `independent` (no build-contract input; no generated output or fingerprint changes; `build.sh:230` already runs `generate_porcelain.py --check`, which calls `validate()`). [pass J]
  - Current: `validate()` accepts a `conditional_null` whose guard or dependent is a path form, a guard that is itself a dependent, a variant with two cases of one JSON type, and unknown keys on a variant case (which enter the fingerprint).
  - Change: refuse (1) a record whose `conditional_null` names, as dependent or guard, a field listed in `path_forms`; (2) a guard that is also a dependent; (3) a variant whose cases do not have pairwise different JSON types; (4) a variant case with a key other than `name` and `type`. A working sketch is in the assessment's work directory (`probe_rules.py`): the current schema is accepted and each constructed combination is refused.
  - Regenerate: none; run `tests/lib/python.sh docs/generate_porcelain.py --check` (expect "checked 84 porcelain records"). Confirm before and after that `tests/lib/python.sh docs/build_contract.py` prints the same identity.
  - Check: five refusal controls in `tests/suites/source_drift/porcelain_codec.py` (`source_drift/porcelain_codec`); `preflight/build_entry_controls`.

## Failure evidence contract (authored prose)

### `tests/FAILURE-PROPAGATION-CONTRACT.md`

- **Status-word definition and retention paragraph, `:20-41`; rows `:57-58`, `:67`; precedence `:73-76`; `:641-642`** — DT-45.a, DT-45.b (withdraws a stated commitment). `independent` [pass C2]
  - Current `:27-30`: "Parameter allocation, parameter setting, the defensive parameter NUL check, and compilation can all write -1. `apply_errno` is populated only for an actual failed application". `:35-37`: "For a published status-word failure (no failure record), retain R and any nonzero `apply_errno` in the runner's `error` diagnostic as published status values". `:73-76` names "published status-word worker failure".
  - Change: R is the header's `apply_rc` word, written only with the return of the application call and read by the host only beside A; preparation and compilation failures publish a failure record and leave R unwritten; in the ordinary form a terminal publication without A and without a failure record is reported as completed without an observed application, and neither R nor `apply_errno` is read (the actor form's setup account keeps its own section, `:194-240`; do not word the ordinary-form statement so that it covers the actor form's authority-setup refusal or an unapplied actor's ordinary completion). Merge row `:57` into `:58`; reword `:67` to "terminal publication without application followed by …"; replace "published status-word worker failure" in `:73-76` with "terminal publication without an observed application"; adjust `:641-642` so it no longer refers to an imprecise published status.
  - Regenerate: none owns these lines; run `tests/lib/python.sh docs/generate_limits.py --check` (FPC is a span document).
  - Check: `runner_unit/pwrunner_core_unit_executable` (`HostOutcomeClassifierTests.swift:234-250`, `CWorkerLifecycleTests.swift:414-434`); `runner_c_worker_harness/compile_failure`; `witness_contract/worker_progress_and_failure`; `source_drift`.

- **Reply-construction paragraph, `:108-114`** — DT-58.a. `independent` [pass C2]
  - Current: calls the minimal `runner_reporting_failed` reply "This final path".
  - Change: after the minimal-reply sentence add that if the minimal writer also fails, the host returns zero bytes; the recipient cannot decode them and no reporting-failure object, identity or original summary is delivered. Keep "never substitutes `{}`". Name the minimal reply as the last structured form. Keep the closing sentence that these paths are tested with constructed results and an internal encoder fault. State the host side only; the recipient's label for zero bytes is source-read.
  - Regenerate: none; `docs/generate_limits.py --check`.
  - Check: `runner_unit/pwrunner_core_unit_executable` (`ReplyFailureTests.swift:314-330`).

- **Custody observations sentence, after `:260-261`** — DT-62.a, DT-122.b. `independent` [pass E]
  - Current: "Custody acceptance, delivery acceptance and native consumption remain three observations."
  - Change: add "Custody acceptance has no field of its own: it is carried by `issued` against `issued_uncustodied` on a published non-null issue and by the transfer records."
  - Regenerate: none; `docs/generate_limits.py --check`.
  - Check: `source_drift`.

- **Shared block, `:280` (copied into the frozen guide)** — outside the review (pass E item 1); optional. `independent` [pass E]
  - Current: the host "rejected, timed out on or never saw the publication".
  - Change: remove "timed out on" (`serviceOutbound` has no timeout branch, `AuthorityCustody.swift:456-502`; only the worker's wait can time out, and a host that accepts afterwards yields `issued`). A false statement corrected in the owner; the guide's copy stays frozen.
  - Regenerate: `tests/lib/python.sh docs/generate_limits.py` (shared regions), then `--check`.
  - Check: `source_drift/limits_documentation`.

- **Host observations paragraph and `cleanup_trigger` row, `:361-367`** — DT-46.a, DT-46.b, DT-120.b, DT-120.d. `after R13` for the table listed in the row; the derivation wording itself is independent. [pass E]
  - Current: "They are facts, recorded where the host acts, not conclusions reconstructed from a final status." Row: "Host string recorded at the exit-request store: `deadline_expiry`, `completion`, `child_reaped`, `poll_wait_error` `policy_transfer_error` or `policy_transfer_timeout`. It names why exit was requested; today it corresponds one-to-one with `poll_stop_reason`, and both are retained."
  - Change: "Three host values join … `grace_end` and `collection_basis` are recorded where the host acts. `cleanup_trigger` is derived from the stop reason the host held when it stored the exit request. None is reconstructed from a final status." Row: "Host string derived at final collection from `poll_stop_reason` through a fixed table (…); a reason outside the table is carried unchanged. It names why exit was requested and is not an observation independent of `poll_stop_reason`; both are retained."
  - Regenerate: none; `tests/lib/python.sh docs/generate_limits.py --check`.
  - Check: oracle derivation check; `source_drift`.

- **Witness table rows, `:468-469`; stop-reason row `:132`** — DT-46.a, DT-121.a. `after R13` for the reason lists (coordinate with the `cleanup_trigger` field's vocabulary). [pass E]
  - Current `:469`: "direct host observation of why exit was requested".
  - Change `:469`: witness "the stop reason the host held when it requested exit, through the fixed table". `:132` and `:468`: the stop-reason rows name the actor scheduler's reasons (open list).
  - Regenerate: none; `docs/generate_limits.py --check`.
  - Check: `source_drift`.

- **Cause-label table, `:508-522`** — DT-46.a, DT-120.f, DT-121.q. `after R13` for the retained-`unknown` limit's list of stops. [pass E]
  - Current: column "Witnessed trigger"; "`termination_cause` projects host cleanup that the account witnesses end to end. A label requires all of: `cleanup_trigger` supported with the trigger in the table …".
  - Change: column "Trigger"; add "The trigger selects the label and restates the stop reason. The independent observations are the request result, the exhausted grace and the owned final status." After the table add the retained limit (same sentence as `41-diagnostics.surface.md:1014-1017`).
  - Regenerate: none; `docs/generate_limits.py --check`.
  - Check: `source_drift`; `unit/rust.unit` cause test asserts `unknown` for an unlisted trigger.

- **Diagnostics `stop_reason` row, `:541`** — DT-121.d (pass E, outside the review item 2). `independent` [pass E]
  - Current: "the `stop_reason` answer when supported; otherwise null".
  - Change: "when supported and one of the six ordinary values" (line 570 of the same file already says so).
  - Check: `source_drift`.

- **"Reader validation responsibilities", `:594-603`** — DT-52.a. `independent` [pass C2]
  - Current: describes the consumer as combining "shape-golden checks with required-field and semantic checks" without saying which reader checks nullable-key presence; `:637` and `:866-867` require key presence for a null step `errno`.
  - Change: add that key presence for a nullable step field is produced by the schema projection, which writes `null` for an absent value in both the Rust serializer and the Python structural reader; on public envelopes `tests/lib/blackbox.py` `validate_step` rejects a missing key; `consumer.validate` checks the type of a present value and accepts an absent one. Limit sentence: "`consumer.validate` does not establish that a nullable step key is present; it accepts an absent `errno` as it accepts `null`."
  - Regenerate: none; `docs/generate_limits.py --check`.
  - Check: `blackbox_menagerie/validation_controls` (`checker_controls.py:167-177`), `runner_specimen_isolation/overlapping_runs_keep_evidence_separate`. See pass L for the other sentences added to this section (lifecycle claims, order direction); write the section once.

- **"Reader validation responsibilities", `:594-597` — one edit of the section with the DT-52 addition (pass C2)** — DT-53.a, DT-132.b, DT-53.g. `independent` [pass L]
  - Current: "`tests/lib/consumer.py` combines shape-golden checks with required-field and semantic checks. `tests/lib/lifecycle_oracle.py` independently checks lifecycle claims and their supporting observations; it is not a complete response-shape validator."
  - Change: after the first sentence add "The consumer does not check lifecycle claims: a record whose claim is absent or contradicts its raw field passes it. The lifecycle oracle and the controller's lifecycle checks reject such a record, and the envelope result is unchanged." Then the nullable-key sentences from pass C2. The byte-equality sentence for association after `:614` ("Step identifiers and query metadata are compared as UTF-8 bytes in this recomputation.") belongs to the R9 thread.
  - Regenerate: none; `docs/generate_limits.py --check`.
  - Check: reader-corpus lifecycle rows; `source_drift`.

- **Coverage rows `:675`, `:676`** — DT-47.a. `independent` [pass C2]
  - Current: `:675` "records `sentinel_deadline`, reaped exit 0, and no termination request through actual subprocess encoding"; `:676` "asserts applied/not-done/no-host-kill/SIGKILL, `child_reaped` and encoded process facts".
  - Change: credit the real worker, the driver's final snapshot, the assembled record and the classifier, say that encoding completes, and name `witness_contract/worker_attempt_in_flight_at_deadline` and `witness_contract/worker_termination` for the encoded facts.
  - Regenerate: none; `docs/generate_limits.py --check`.
  - Check: the two named witness cases (`check_attempt_in_flight.py:236-246`, `check_worker_termination.py:66-71`). Optional (not required for any stated claim): write `data` under `PW_TEST_ARTIFACTS` in `CWorkerTests.swift:417-418`, `:461-462` and decode it in `tests/suites/runner_unit/porcelain_replies.py`.

- **Coverage row `:678` (`runner_c_worker_harness/compile_failure`)** — DT-45.a (pass C2, outside the review). `independent` [pass C2]
  - Current: says the case shows "A=false, D=true, R=-1".
  - Change: the case shows the published compile failure record with A false and D true; the worker does not write R on a compile failure and the case asserts nothing about it (`tests/suites/runner_c_worker_harness/run.sh:454-481`).
  - Check: `runner_c_worker_harness/compile_failure`; `source_drift`.

- **Coverage row for `pre_apply_failure`, `:683`** — DT-53.g. `independent`; lands with the oracle group in the checker. [pass L]
  - Current: "Independent attribution, lifecycle and consumer-validation groups".
  - Change: "Independent attribution, raw lifecycle-observation, lifecycle-claim and consumer-validation groups…".
  - Check: `witness_contract/pre_apply_failure_reports_no_policy_verdict`.

- **Coverage row `:684` (`reported_failure_hang`)** — DT-45.d, and DT-47.a for its "actual subprocess assembler and binary writer preserve reports and missing status" clause. `independent` [pass C2]
  - Current: "published status-word failure then cleanup".
  - Change: "terminal publication with a written status word and no failure record, then cleanup: the word is not read". Reword the binary-writer clause as in `:675-676` (`CWorkerLifecycleTests.swift:58-60`, `:192-193` encode, discard and assert on the typed record).
  - Check: `runner_unit/pwrunner_core_unit_executable`; `source_drift`.

- **Coverage sentence, `:687`** — DT-113.e. `independent` [pass K]
  - Current: "Constructed replies cross production assembly".
  - Change: "Constructed replies cross production completion and rendering".
  - Check: `source_drift/generator_contract`.

- **Diagnostic `rc` sentence, `:1111-1113`** — DT-49.a. `independent` [pass C2]
  - Current: "A received diagnostic without a native return retains `result_source="validator"`, `native_rc=null` and `rc=-1`".
  - Change: take the RESPONSE meaning (`docs/contract/31-steps.surface.md:67`): `rc` is the record's carried return, or -1 when the record carries none; `native_rc` is null for an outcome outside allow, deny and error.
  - Regenerate: none; `docs/generate_limits.py --check`.
  - Check: new carried-return control in `failure_boundaries/validator_frames`.

- **`stdout_collection_stop` list and `read_error` clause, `:1128-1133`** — DT-54.a. `independent` [pass C2]
  - Current: lists `eof`, `deadline`, `read_error` or `poll_error`; says `read_error` "independently retains a read/poll/deadline failure".
  - Change: list `eof`, `clock_error`, `deadline`, `poll_error`, `byte_limit` and `read_error`; the preceding clause says `read_error` keeps the read, poll, deadline, clock or byte-limit diagnostic. Do not say `clock_error`, `poll_error` or `read_error` are exercised. (Acceptable alternative form: replace the restated list with a reference to the RESPONSE field.) Use the same five conditions as the `lifecycle.validator.read_error` correction (DT-44 lead e).
  - Regenerate: none; `docs/generate_limits.py --check`.
  - Check: `witness_contract/phases` (`check_phases.py:134-138`), `runner_unit/pwrunner_core_unit_executable` (`ValidatorEvidenceTests.swift:90-96`) for `byte_limit`.

- **`operation_relation` row, `:1224`** — DT-15.b. `independent` [pass A]
  - Current: `different` "when it is another operation"; `unresolved` omits wildcard queries.
  - Change: `unresolved` cell reads "for compound `file`/`create` or `file`/`create_fresh`, an unsupported attempt, or a query operation containing `*` other than the exact `process-exec*` match". The row is authored, outside the shared regions (`:270-303`, `:1399-1456`) and the generated matrix (`:1483-1531`); do not touch those.
  - Regenerate: none.
  - Check: existing `witness_contract/comparison_matrix` (row S12) and `runner_unit/pwrunner_core_unit_executable` already assert the rule; `source_drift` for the document.

- **Working table, `:1225`, last sentence** — DT-25.a. `independent` [pass L]
  - Current: "Different strings establish different submitted targets".
  - Change: "Submitted strings that are not canonically equivalent establish different submitted targets, not distinct runtime objects." (Reading rule 4 at `:1419-1422` and `docs/QUESTIONS.md:41` are already correct and are shared regions; do not touch them.)
  - Regenerate: none; `tests/lib/python.sh docs/generate_limits.py --check`.
  - Check: `source_drift`.

- **Label sentence, `:1231-1232`** — DT-48.t4. `independent` [pass L]
  - Current: "These labels classify native returns."
  - Change: "These labels are the validator's classification of its native returns; the host admits them by type and tests their agreement with `rc` and `errno` only as a condition of `query_first`."
  - Check: `source_drift`.

- **Consumer bullet, `:1378-1379`** — DT-130.a. `independent` [pass L]
  - Current: "validates `observation`, the two relations and `order` against the raw channel fields and `ordering`".
  - Change: "…validates `observation` and the two relations against the raw channel fields, and `order` against them and `ordering` in both directions: a claimed `query_first` needs an eligible record and the complete chain, and an eligible record with the complete chain must say `query_first`." Note (pass L, outside the review): the consumer's chain also requires `arrival_observed` (`consumer.py:253`), one condition more than the stated chain; word "the complete chain" so it does not claim identity with the rule's chain, or name the extra condition.
  - Check: `source_drift`; `blackbox_e2e/checker_controls`.

## Limits manifest and shared-region owners

### `docs/EXTENSIONS.md`

- **Self-transfer sentence, `:79-81` (shared region; guide copy at `docs/PolicyWitness.md:489` frozen) — merged edit** — DT-59.a (pass E) and DT-39.a (pass B). `independent` [pass E]
  - Current: "The recipient accepts a delivery while parked between its visits; it consumes only in a later visit of its own, after that phase's queries were collected and the host released it."
  - Pass E text: "A recipient other than the sender accepts a delivery while parked between its visits and consumes it in a later visit of its own. A self-transfer is accepted inside the sender's own wait and can be consumed later in that same visit. Either way consumption follows that phase's query collection and the host's release."
  - Pass B text: "A recipient other than the sender accepts a delivery while parked between its visits and consumes only in a later visit of its own, after that phase's queries were collected and the host released it. An actor that transfers to itself consumes in a later action, which may be in the same visit."
  - Recommended: pass E's. It keeps the collection-and-release condition on the self-transfer case as well, and names the acceptance point the same document already states at `:45` and `:76-77`. (Pass B cites the sentence at `:81-83`; it is at `:79-81`.)
  - Regenerate: `tests/lib/python.sh docs/generate_limits.py`; `--check` verifies the owner and the frozen guide bytes.
  - Check: `source_drift/limits_documentation`; the new same-visit composition in `witness_contract/actor_compositions`.

- **`actor_unavailable` row, `:126` (shared region; guide copy frozen)** — DT-44.g. `independent` [pass B]
  - Current: names `actor_unavailable` as how the visits read.
  - Change: "… its visits are not activated: their phases carry no `activation_observation`, `arrival_observed: false` and `collection_status: not_reached`; other actors' evidence stands. The run is `runner_failed`."
  - Regenerate: `tests/lib/python.sh docs/generate_limits.py`.
  - Check: `source_drift/limits_documentation`; reading (`ActorOrchestration.swift:349-366`).

### `docs/limits.json`

- **Row `runner_remove_teardown_wait`, `:1435-1463` (`effect` at `:1441`, rendered `docs/LIMITS.md:145`; guide copy frozen) — merged edit** — DT-69.a (pass F) and DT-34.c (pass C1). `independent` [pass F]
  - Current `effect`: "a later `runner remove` or `runner reconcile` continues recovery."
  - Pass F change: remove "or `runner reconcile`" from `effect`; add the check citation `removal_preserves_recovery_across_faults_and_repeated_cleanup` (`controller/src/runner_manager.rs`, kind `path`, form `test`); add one clause to `behavior` saying a repeated removal retires a retained record once absence is observed.
  - Pass C1 change: "…a later `runner remove` continues recovery; `runner reconcile` reports the retained record."
  - Recommended: pass F's. It removes the false clause from the shared region without adding a statement there; the citation and `behavior` clause land in the coverage table (`docs/LIMITS.md:310-430`), outside the shared region.
  - Regenerate: `tests/lib/python.sh docs/generate_limits.py` (development mode leaves the guide's bytes unchanged), then `--check`.
  - Check: `source_drift/limits_documentation`; `unit` (`documented_removal_limits` compiles `docs/limits.json` in); the cited unit test (`runner_manager.rs:2754-2770`) and `registry_recovery.py:458-465` assert that a later remove continues recovery.

- **Actor fallback row `:1646`; oversize-input row `:1881`; shared-region sentence rendered at `docs/LIMITS.md:77-78` (guide copy frozen)** — DT-117.h, DT-117.i. `independent` [pass K]
  - Change `:1646`: "Actor fallback does not depend on host admission and can accumulate more policies than the admitted actor count." LIMITS shared sentence (correct it in its owner input): "These independent compile diagnostics do not depend on host admission; they do not establish application." `:1881`: "Oversized input is tested through the shipped helper with a request file; the controller's fallback delivery of an oversized source and the exact boundary are source-inspected."
  - Regenerate: `tests/lib/python.sh docs/generate_limits.py`, then `--check`.
  - Check: `source_drift/limits_documentation`.

- **`extension_token_payload.effect`, `:2850` (rendered `docs/LIMITS.md:176`; guide copy frozen)** — outside the review (ruling "Corrections outside the review"; pass D). `independent` [pass D]
  - Current: "Larger native results report `token_oversized`".
  - Change: state what a longer native result reads as: issue `status: returned` with `native_nonnull: true` and `token_length: 0`, token `issued_uncustodied`, transfer `custody_unavailable`; an empty return reads identically. Remove `token_oversized` (no producer contains the string; removed at `bc3abe2f`). Correct the false statement only; add no workflow or example.
  - Regenerate: `tests/lib/python.sh docs/generate_limits.py`, then `--check`.
  - Check: `source_drift/limits_documentation`; retained `extension_boundaries/artifacts/issue-2` shows the stated reading.

## Architecture manifest

### `docs/architecture.json`

- **`sbpl_check` Lifetime `:551`; T12 label and checks `:977-1004`; B9 label `:1987`; `helper_envelope` Form `:1401`** — DT-117.h, DT-115.3, DT-115.4, DT-117.i. The wording corrections are `independent`; adding the corrected actor fallback test to T12 is `after R10` (Controller B corrects it). [pass K]
  - Change: `:551` replace "potentially before host admission" with "host admission may not have occurred". T12: drop the association credit from `fallback_compilation_is_requested_only_for_an_admitted_xpc_error` and `refused_reply_versions_request_no_fallback_compilation` (their claim is the invocation rule); add `actor_fallback_preserves_resolved_inputs_order_and_transport_evidence` once corrected. B9 label → "nested unchanged; admitted by kind and frame version; per-helper retention is not a cumulative envelope or memory bound", narrowed to the ordinary capture until the consumer question is decided. `helper_envelope` Form → "…independently compiled diagnostic for the delivered policy input, not application evidence".
  - Regenerate: `tests/lib/python.sh docs/generate_architecture.py`.
  - Check: `source_drift/architecture_documentation`.

- **Porcelain generator row, `:3849`** — DT-107.a. `independent` [pass J]
  - Current: "Swift writers".
  - Change: "Swift record writers".
  - Regenerate: `tests/lib/python.sh docs/generate_architecture.py`.
  - Check: `source_drift/architecture_documentation`. Note: this location's file changed after the assessments were written (`5ab8e530`); re-read it.

- **Node `reconcile` `facts.Behavior` `:6787-6812` (text at `:6791`); edges X24 `:7459-7478` and X25 `:7480-7499`** — DT-78.a, DT-78.b, DT-78.c, DT-78.d. `independent`; the integration-control citation follows once that control exists. [pass F]
  - Current: node "reports launchd services and plists that look owned, changing nothing"; X24 "inspect_service lists candidate services"; X25 "inspect_plist lists candidate plists"; all three cite `runner_install`.
  - Change: node "reports each recorded runner and cleanup entry with its observed service and plist, and recognizable unrecorded plists, changing nothing"; X24 "launchctl print for each recorded service and each candidate label, without changes"; X25 "reads each recorded plist and each plist in the two launchd directories, without changes" (add `cmd_runner_reconcile` to X25's sources for the listing). Replace the `runner_install` citation on all three with `tests/suites/runner_byoxpc/opt_in/registry_recovery.sh` / `registry_recovery` (form `test`) and add the new integration control.
  - Regenerate: `tests/lib/python.sh docs/generate_architecture.py` (rewrites `docs/architecture-byoxpc.dot`, its SVG and the `docs/ARCHITECTURE.md` regions; Graphviz `dot` at `/opt/homebrew/bin/dot`), then `tests/lib/python.sh docs/generate_contract_stamps.py`.
  - Check: `docs/generate_architecture.py --check`; `source_drift`. Note: this location's file changed after the assessments were written (`5ab8e530`); re-read it.

- **Inventory row a3, `:9845` (rendered `docs/WORKER.md:647`)** — DT-64.c (optional; the row is not false). `independent` [pass D]
  - Current: "Erase inspected length and free before outbound publication; oversized tail unobserved."
  - Change (optional): "… bytes beyond the inspected length not erased".
  - Regenerate: `tests/lib/python.sh docs/generate_architecture.py`, then `--check`.
  - Check: `source_drift`. Note: this location's file changed after the assessments were written (`5ab8e530`); re-read it.

## Authored technical documents

### `docs/ARCHITECTURE.md`

- **"Host admission" sentence, `:164-165`** — DT-117.h. `independent` (the whole-request sentence at `:160-163` is R10's). [pass K]
  - Current: fallback "can run before host admission".
  - Change: "Fallback does not depend on host admission, so the admitted actor-count bound does not bound the number of helper invocations."
  - Check: `source_drift/architecture_documentation`.

- **`runActors` link, `:258`** — DT-39.g. `independent` [pass B]
  - Current: links the calling file (`CWorkerOrchestrator.swift`).
  - Change: link target `../runner/Sources/PWRunnerCore/ActorOrchestration.swift`.
  - Check: `source_drift/generator_contract` link rules.

- **"One run in time" sequence block, `:302`** — DT-09.a. `independent` [pass A]
  - Current: `optional logs;` between `complete execution;` and `print envelope`.
  - Change: delete the line. The block is authored, outside every generated region (regions end at `:245`, resume at `:342`). After removal the tail reads decode / admit / complete / print, which is `controller/src/run_flow.rs:692-712` in order.
  - Regenerate: none.
  - Check: `tests/lib/python.sh docs/generate_architecture.py --check`; `source_drift`.

- **Authored prose `:462-468`** — DT-116.f, DT-116.g (and DT-39.c: same sentence as `controller/README.md:232-235`). `independent` [pass K]
  - Current: names `execution_envelope` as the assembler; "yields a synthetic `xpc_timeout` reply".
  - Change: the pass K assembly sentence (see `controller/README.md`); "The client's timeout ends the controller's wait; the admitted capture records terminal `xpc_timeout` and `runner_result` is null."
  - Check: `source_drift`; `docs/generate_architecture.py --check`. Note: this location's file changed after the assessments were written (`5ab8e530`); re-read it.

### `docs/BUILD.md`

- **"Order." paragraph, `:989-994`** — DT-16.a. `independent` [pass A]
  - Current: no section prose mentions the service-local equipment inventory; it appears only in the generated step row at `:170`.
  - Change: one sentence stating that each service's `worker-equipment.json` is written from the signed workers after that service's nested signatures and before its seal (`build.sh:732-736`), written without a literal count and in the citation form the prose rules accept. This keeps `equipment.manifest` under the signing list true.
  - Regenerate: none (authored prose); `docs/generate_build.py --check` afterwards.
  - Check: `source_drift/generator_contract` prose and link rules.

### `docs/RESPONSE.md`

- **Authored opening prose, `:88-90` (outside the generated regions)** — DT-31.a, DT-113.d. `independent` [pass K]
  - Current: "An admitted completion without a host reply can instead have a no-worker assessment."
  - Change: "Null `runner_sandbox_diagnostics` accompanies earlier refusals and tool errors. An admitted reply with no worker subprocess record has a no-worker assessment. A withheld assessment has its own supporting findings."
  - Regenerate: none (authored); `docs/generate_contract_stamps.py --check` afterwards.
  - Check: `source_drift/generator_contract`.

### `docs/WORKER.md`

- **Readiness reader sentence, `:142-144`** — DT-39.d. `independent` [pass B]
  - Current: "the host closes its readiness reader after the wait".
  - Change: "The host closes its readiness reader after the wait unless the ready byte arrived; after a received byte it keeps the reader through polling and exit grace until session teardown."
  - Regenerate: none; `docs/generate_architecture.py --check`.
  - Check: agrees with the generated row s3a at `docs/WORKER.md:583`.

- **"Starting authority and ambient context" section, `:176-275`** — DT-41.a. `independent` [pass B]
  - Current: the list at `:276-283` names `actors.sandbox`; the section does not discuss apply or unapplied.
  - Change: add "An actor declared `unapplied` runs its visits under exactly this starting authority and inherited context; an `apply` actor adds its declared policy to the same starting point." Keep the list entry.
  - Regenerate: none.
  - Check: `source_drift` prose rules.

## READMEs and test accounts

### `controller/README.md`

- **Foreign-producer paragraph, `:185-190`** — DT-31.b, DT-114.a, DT-114.b, DT-114.e. `independent` [pass K]
  - Current: "A host frame naming another schema fingerprint, or a decoded reply carrying another producer contract, produces `unsupported_runner_response`. … `data.runner_result` holds the decoded record's projection when decoding succeeded and is null otherwise."
  - Change: "A host frame naming another schema fingerprint or another producer contract produces `unsupported_runner_response`; the frame is not decoded and `data.runner_result` is null. Host bytes that are not one complete typed record produce `malformed_runner_response` with a null `runner_result`. A decoded reply that fails capacity or compiled-profile label admission produces `malformed_runner_response` with the decoded record in `data.runner_result`. Each exits 1 and withholds runner-derived diagnostics." Add the limit: "A second comparison of the decoded reply's producer contract follows decoding; it cannot refuse a frame the decoder accepted."
  - Check: `source_drift`; `unit/rust.unit` (`producer_gate_precedes_malformed_descendants_and_keeps_raw_bytes`).

- **Envelope assembly sentence, `:232-235` — merged edit** — DT-116.f (pass K) and DT-39.c (pass B). `independent` [pass K]
  - Current: names `execution_envelope` (a `#[cfg(test)]` helper) as the assembler of fallback with diagnostics.
  - Pass K text: "`execution_parts` joins the dossier, transport and acquisition history with the execution diagnostics. Independent fallback compilation is attached only to a refused `xpc_error` capture, which carries no diagnostics."
  - Pass B text: name `run` (which fills `ExecutionData` with the dossier, transport, acquisition history and fallback compilation) and `execution_parts` (which joins it with the diagnostics for `envelope`).
  - Conflict: pass B's wording keeps fallback compilation inside the record that is joined with the diagnostics, the pairing pass K shows cannot occur. Recommended: pass K's text, which also replaces the test-helper name. Apply the same sentence at `docs/ARCHITECTURE.md:462-465`.
  - Check: `source_drift`.

- **Install signing sentence, `:287-288`** — DT-34.d. `independent` [pass C1]
  - Current: describes entitlements only on the worker.
  - Change: "Install signs the selected worker with the entitlements, the validator and the unentitled worker without them, refreshes the equipment inventory, then signs the enclosing bundle and its host executable with the entitlements".
  - Check: `source_drift`; reading (`runner_manager.rs:978-982`).

- **Runner command result forms, `:304-307`** — DT-35.a, DT-35.b, DT-35.c. `independent` [pass C1]
  - Change: the same two sentences as `50-installation.surface.md` (success label including a retained-cleanup remove; unenveloped stderr refusal with exit 2).
  - Check: `source_drift`.

### `runner/README.md`

- **Region creation sentence, `:127-128`** — DT-39.b. `independent` [pass B]
  - Current: "every actor's region and authority region exist before the first launch".
  - Change: "every actor's authority region and the host custody session exist before the first launch, and each actor's evidence region is created when that actor is launched".
  - Check: `source_drift`.

### `tests/CHANGE-VERIFICATION.md`

- **"Find verification for a change": new route row** — R12 routing (pass G A.6 item 10). `after R12` [pass G]
  - Change: a row for "import scanner grammar, resolver flags or helper inventory projection" naming `unit`, `integration`, `witness_contract/dossier_witness`, `blackbox_e2e/checker_controls` and `source_drift`.
  - Check: `source_drift`. Note: this location's file changed after the assessments were written (`5ab8e530`); re-read it.

### `tests/COVERAGE.md`

- **Reader-corpus sentence, `:201`** — DT-135.b. `independent` [pass L]
  - Change: "…its reply is replayed through Rust assembly and the Python consumer and lifecycle oracle, whose phase-collection and ownership checks are one shared implementation."
  - Check: `source_drift`.

### `tests/fixtures/README.md`

- **Contract fixtures account, `:23-24`** — DT-111.a, DT-111.b, DT-111.d. `independent` [pass J]
  - Current: "Shape checks separately own explicit null versus omitted fields."
  - Change: say that shape checks record key names and JSON types and do not distinguish an omitted key from an explicit null or one byte spelling from another, and that the normal fixture is the authored exact projection of `normal.pwp`. Add "The omit or null rule of an optional field is compared with an authored expectation only where `normal_reply.json` leaves that field absent or a dedicated assertion names it. Elsewhere both readers and RESPONSE's presence phrase take the rule from `docs/porcelain.json`."
  - Check: `source_drift`.

- **Compiled-profile fixture account, `:25-27`** — DT-95.d. `independent` [pass I]
  - Change: add that the valid captured row's other fields are arbitrary.
  - Check: `source_drift`.

### `tests/suites/blackbox_e2e/README.md`

- **Receipt corpus account, `:71-74`** — outside the review (ruling "Corrections outside the review"; pass I). `independent` [pass I]
  - Current: "checks the nested receipt version" (a field and rows that do not exist); "Swift and Rust controls read the same … cases" (wrong readers).
  - Change: the corpus checks the status vocabulary and the worker/before-apply labels in the Rust reply-admission tests (`run_flow.rs:1929`, `:2967`) and the Python consumer controls (`checker_controls.py:296-300`, `:758-775`); Swift constructs its own.
  - Check: `source_drift`.

### `tests/suites/runner_unit/README.md`

- **Path-diagnostics account, `:95-98`** — outside the review (pass J). `independent`; optional. [pass J]
  - Current: says `PathDiagnosticsTests` pins "rejection of conflicting/missing representations" and that `path_diagnostics.json` supplies cases "to Rust and Python reader checks".
  - Change: the Swift group has three cases, none a rejection; the fixture is read only by `tests/suites/blackbox_e2e/checker_controls.py:978`.
  - Check: `source_drift`.

- **Compiled-profile capture account, `:285-293`** — DT-101. `independent`; extend only after the Swift coverage repair lands. [pass I]
  - Change: say reasons, order and withheld fields are asserted (accurate now without that sentence).
  - Check: `source_drift`.

### `tests/suites/source_drift/README.md`

- **`checks` description, `:406-409`** — DT-14.a, DT-14.b, DT-14.f. `independent` [pass A]
  - Current: "The surface manifest's `checks` entries name catalog suites that own verification; they are validated as suite names, not G5 assertion citations. Their presence does not establish a defined assertion or coverage of the surface's behavior."
  - Change: replace "that own verification" with the validated fact: "A surface's `checks` list is validated only as catalog suite names; it is not compared with the checks its owners cite and selects no verification for a surface change."
  - Check: `source_drift/generator_contract` prose and link rules.

- **`build_contracts` paragraph near `:659`; `tests/suites/preflight/README.md` (`build_entry_controls`); `tests/catalog.json` description of `preflight/build_entry_controls`; `tests/CHANGE-VERIFICATION.md#build-entry-controls` and a route row for identity selection, walker or framing changes** — DT-89.a, DT-91.e (test accounts for the R3 controls). `after R3` — these describe controls the identity thread writes; confirm the final control names and messages. [pass H]
  - Change: describe the literal-tree walker controls, the pinned digest, the statement-oracle test and the unlistable-directory build-entry control (purpose and "When to run": identity derivation refusals).
  - Check: `source_drift`. Note: this location's file changed after the assessments were written (`5ab8e530`); re-read it.

- **Porcelain paragraphs: `:321`, `:786-790`, `:799-803`** — DT-107.a–d, DT-106.f, DT-110 (accounts for the new controls). `:321` and `:799-803` are `independent`; the refusal sentence at `:786-790` is `after R8` — confirm the reader refusal's final diagnostic. [pass J]
  - Current `:321`: "Swift writers".
  - Change `:321`: "Swift record writers", and add "The variant writer in `PWPorcelain.swift` is hand-written. Check mode does not compare its case tags or payload types with the schema; `runner_unit` replays Swift-written frames through the generated readers, and that replay is the first check to read a Swift-written variant value." `:799-803`: name the four new schema refusals and the presentation mutations. `:786-790`: add the conditional-field-without-guard refusal (after R8).
  - Check: `source_drift`. Note: this location's file changed after the assessments were written (`5ab8e530`); re-read it.

- **New-control descriptions** — DT-01, DT-02, DT-04, DT-05, DT-07, DT-18.b. `independent` [pass A]
  - Change: describe each new control and rule beside the ones it joins (nested-marker and moved-destination refusals under G1, on-disk anchor count, positional scope control, record-label assertion, RESPONSE fence rule, presence ratchet as a keyword heuristic), as `tests/AGENTS.md` requires for a changed suite.
  - Check: `source_drift` documentation rules.

### `tests/suites/unit/README.md`

- **Receipt label corpus account, `:33-39`** — DT-104.a, DT-95.d. `independent` [pass I]
  - Current: credits label refusal for all refused rows.
  - Change: the corpus has two admitted and seventeen refused rows; nine refusals are status/label refusals by `admission_problem`, eight are refusals by the test's typed reader with a null `runner_result`; the admitted captured row is unrelated to the request.
  - Check: `source_drift`.

### `tests/suites/witness_contract/README.md`

- **Capture receipt sentence, `:40-41`** — DT-95.g. `independent` [pass I]
  - Current: "The capture receipt binds nonce, worker PID, source hash …".
  - Change: the case compares those receipt fields with its own request and reply.
  - Check: `source_drift`.

- **Redelegation contrasts sentence, `:793-797`** — DT-67.a. `independent` [pass D]
  - Current: "The contrasts omit `B`'s consume, remove `B`'s issuance allowance, omit `C`'s consume and omit `C`'s extension predicate; each must still publish its remaining links and must not be credited, and their observations are retained beside the principal run for comparison."
  - Change: "The contrasts omit `B`'s consume, remove `B`'s issuance allowance, omit `C`'s consume and omit `C`'s extension predicate; each must still publish its remaining links. The two omitted-consume contrasts must lack the omitted action's event, so their chain is incomplete and is not credited. The two weakened-policy contrasts publish all six links; whether their chain is credited is computed and recorded in `report.json` beside the principal run and is not asserted."
  - Check: `source_drift` (suite account).

## Test-side repairs (no signed rebuild)

### `controller/integration/cli_contract.rs`

- **Closed-stream publication tests, `:408-423`** — DT-28.c, DT-28.e. `independent` [pass C1]
  - Current: the cited controls close stderr at launch, not stdout.
  - Change: add `>&-` (stdout closed at launch) rows for `example` and `test-input read`, expecting exit 0; note in the test that the runtime holds a discarding descriptor (write failure is tested with a reader-less pipe).
  - Check: `integration/cli.integration`.

- **`sbpl_check_argument_and_request_failures_exit_2_without_an_envelope` `:811-853`; comment `:1296-1297`** — DT-42.a, Q3.c, DT-116.e. `independent` [pass K]
  - Change: add an actor-form row (a held request with `actors` and no top-level `policy`: exit 2, empty stdout, nonempty stderr). Comment at `:1296-1297`: "the xpc_error disambiguation path" → "reserved for an admitted client `xpc_error`".
  - Check: `integration/cli.integration`. Re-executed now on the `2f4d76e4` helper: exit 2, 0 stdout bytes, "missing field `policy`".

- **`invalid_augment_name_rejected_as_bad_request`, `:1395-1430`** — DT-26.a, DT-26.b. `independent` (`controller/integration/` is not a build-contract input) [pass C1]
  - Current: asserts code `invalid_value` for `["../etc/passwd"]`, not the path.
  - Change: also assert `request_failure.path == ["policy","augments","0"]`.
  - Check: `integration/cli.integration`.

- **`sbpl_check_records_import_provenance_for_system_sb`, `:1513-1516`** — DT-86.b. `independent` (`controller/integration` is not a build-contract input) [pass G]
  - Current: asserts `policy_sha256 != policy_closure_sha256` "when imports were resolved"; the two hashes always differ (all 53 envelopes re-executed now, including the no-import case).
  - Change: each record hash equals an independent hash of its `resolved_path`; the closure equals an independent recomputation (source, byte 0x1F, sorted `path sha` lines) made without calling `compute_closure_hash`; the transitive `dyld-support.sb` record is present.
  - Check: `integration/cli.integration`. The unit test with the same property (`controller/src/sbpl_imports.rs:447-453`) is removed or renamed in the R12 rebuild.

- **New reconcile no-change control (beside `help_needs_no_app_home_registry_or_valid_tail`, `:1922-1932`)** — DT-69.b, DT-79.d, DT-79.e, DT-74.d. `independent` (`controller/integration` is not a build-contract input); it asserts current behavior and is expected to pass on the current app. [pass F]
  - Change: with `HOME` and `PW_RUNNER_REGISTRY` pointed into scratch: (1) reconcile on an absent registry path leaves the path, its `.lock` sibling and its parent directory absent; (2) reconcile on a constructed registry holding one installed record and one `pending_cleanup` record (plist path under the fixture `LaunchAgents`, label never bootstrapped) exits 0, reports both `recorded_state` values, and leaves the registry bytes and the directory listing identical with no lock created. Do not assert presence values. Canonicalize the scratch path before writing it into the fixture record and `HOME` (`env::temp_dir()` is under the `/var` symlink and `record_location` refuses a symlinked ancestor). Add a line to `tests/suites/integration/README.md` under Invariants.
  - Check: `integration/cli.integration`. Must reject a reconcile that creates a lock or directory, rewrites the registry, or retires a record whose resources are absent.

- **New runner-command result-form rows** — DT-35.a, DT-35.b, DT-35.c. `independent` [pass C1]
  - Change: `policy-witness runner` with no subcommand: usage on stderr, no envelope, exit 2; `runner list` under a scratch `PW_RUNNER_REGISTRY`: `normalized_outcome: "ok"`, exit 0.
  - Check: `integration/cli.integration`. Optional: `runner_byoxpc/registry_recovery` asserts the `ok` label on its retained-cleanup remove (opt-in, GUI session).

### `controller/integration/interface_cases.json`

- **New `conflicting_selector` third-condition case (beside `:1111`, `:1131`)** — DT-27.a, DT-27.b. `independent` [pass C1]
  - Current: two cases assert the code at the root path; the CLI/file disagreement has only a unit test on its message (`run_flow.rs:2392-2395`).
  - Change: a file with `runner.mode: "byoxpc"` run with `--runner-mode standard`: `bad_request`, `request_failure.code: "conflicting_selector"`, path `["runner","mode"]`.
  - Regenerate: `tests/lib/python.sh docs/generate_interface.py` (joins).
  - Check: `integration`, `unit`, `source_drift` ("Interface definitions and help cards" in `tests/CHANGE-VERIFICATION.md`).

### `runner/Tests/PWRunnerCoreTests/ActorAuthorityTests.swift`

- **Constructed setup-buffer test, `:155-178`** — DT-60.a, DT-60.b. `independent` [pass E]
  - Current: supplies matching words; asserts cell retention and `invalid_setup_cell`.
  - Change: add a published `ready` decision with raw actor ≠ argument, then raw required ≠ argument; require `integrity_errors` to contain `setup_association_mismatch` in both.
  - Check: `runner_unit/pwrunner_core_unit_executable`; rerun opt-in `runner_unit/actor_handoff_mutations`. Must reject a decoder that returns a mismatched block's decision with no integrity error.

- **Comment above the custody assertion, `:467-468`** — DT-63.a, DT-124.g. `independent` (`runner/Tests` is not a build-contract input) [pass D]
  - Current: the comment says custody was erased "at the token's last declared transfer"; the assertion reads `outcome.custody[].erased` after `scheduler.run` returned.
  - Change: "Custody reads erased after the run; teardown sets this flag whether or not the last declared transfer ran." Keep the assertion as a final-state check. Leave `:307` unchanged.
  - Check: `runner_unit/pwrunner_core_unit_executable` on the signed app. The file is also an input of the opt-in `runner_unit/actor_handoff_mutations`; rerun it before crediting it ("Actor authority ownership and operation controls" in `tests/CHANGE-VERIFICATION.md`).

### `runner/Tests/PWRunnerCoreTests/ActorReplyTests.swift`

- **Interrupted-issue case, `:113-134`** — DT-62.d, DT-129.d. `independent` [pass E]
  - Current: asserts the interrupted issue's `unresolved` token and event, not host acceptance.
  - Change: add `expectEqual(outcome.custody.first { $0.tokenIndex == 0 }?.status, "accepted")` and `expectNil(reply.resources!.tokens[0].token_length)`.
  - Check: `runner_unit/pwrunner_core_unit_executable`.

### `runner/Tests/PWRunnerCoreTests/ActorSchedulerTests.swift`

- **Timeout-then-cleanup test, `:261-277`** — DT-38.d. `independent` [pass B]
  - Current: reads one final result; asserts `timed_out` twice and `quiescence == "reaped"`; no ordinal or time comparison.
  - Change: assert that the gate carries no reap reference and that the source's owned-reap capture ordinal is greater than the gate's capture ordinal.
  - Check: `runner_unit/pwrunner_core_unit_executable`. Must reject a scheduler that reaps the source inside the gate after its timeout.

- **Optional clock-fault control beside `:334-362`** — DT-10.c. `independent` (`runner/Tests` is not a build-contract input) [pass A]
  - Current: `:303-313` and `:334-362` assert the label under a zero or a measured-exhausted allowance; no test injects a failing clock.
  - Change: constructed control in which `calls.clock` returns nil after the collection hook; expect `cancelled == "execution_allowance_exhausted"`, `executionWait.stop == "deadline"`, `executionWait.clock_fault == true`, `executionWait.elapsed_ms == nil`. Needed only if the schedule-support owner (`13-actors.surface.md:241-250`) is to credit the new clause as check-read; without it the clause stays source-read and the owner says so.
  - Check: `runner_unit/pwrunner_core_unit_executable` (against the signed app, with `runner_c_worker_harness`, per `runner/AGENTS.md`).

- **"Lost ownership" test `:365-407` and a new neighbor case** — DT-36.b. `independent` [pass E]
  - Current: injects ECHILD; asserts `quiescence == "unresolved"` (`:394`) and `cancelled != nil` (`:397`) without naming a label.
  - Change: (1) add `expectEqual(result.cancelled, "unresolved_termination")` to the ECHILD case; (2) add a case whose injected wait fails once with a non-ECHILD, non-EINTR errno for the active child and then delegates: expect `quiescence == "reaped"`, `cancelled == "ownership_lost"`, the later visit not activated, the failed call retained in `output.waitErrors`, `pollStopReason == "wait_error"`.
  - Check: `runner_unit/pwrunner_core_unit_executable`. The file is compiled by the opt-in `runner_unit/actor_handoff_mutations`; rerun it.

- **New never-launched `setup_timeout` control** — DT-44.b2. `independent` [pass B]
  - Change: two actors and a setup allowance the first consumes; the second has `setupStatus == .setupTimeout` and no pid.
  - Check: `runner_unit/pwrunner_core_unit_executable`.

### `runner/Tests/PWRunnerCoreTests/CompiledProfileCaptureTests.swift`

- **Corruption loop `:67-76`, extent loop `:77-83`, application cases `:84-91`, digest `:92-97`** — DT-97.e, DT-99.f, DT-101.b, DT-101.d, DT-101.g, DT-101.h, DT-102.b. `independent` (`runner/Tests` is not a build-contract input) [pass I]
  - Current: eleven single-bit corruptions assert `unavailable`, nil bytes, nil digest; six of nine reasons are named in no test; no two-fault case.
  - Change: assert the reason for each of the eleven corruptions; assert that every `unavailable` result has only `status`, `reason`, `worker_pid`; add `rc: -1` → `successful_application_unconfirmed`, `done: false`, signal 9 and `exit: 1` → `worker_not_complete`; add adjacent two-fault cases for the order (application+completion, completion+capture completion, capture completion+status, status+PID, PID+nonce, nonce+type, type+byte digest, byte digest+input); add the same known-answer parameter digest as `capture.c`. Optional, in `WorkerEvidenceTests.swift`: run the `.apply-failure` companion with capture requested and assert `unavailable` / `successful_application_unconfirmed` beside failure operation 8, `done` and exit 0.
  - Check: `runner_unit/pwrunner_core_unit_executable`. Must reject a decoder that swaps two guards or two reason strings, or leaves a capture field on an `unavailable` receipt.

### `runner/Tests/PWRunnerCoreTests/DispositionResolverTests.swift`

- **New absent-slot control beside `:286-296`** — DT-44.d. `independent` [pass B]
  - Change: duplicate slot identities, terminal basis, progress before the step; expect boundary `not_reached` and result `unresolved: slot_unavailable`.
  - Check: `runner_unit/pwrunner_core_unit_executable`. Must reject a resolver that answers `not_reached` beside a completed slot or under a non-terminal basis.

### `runner/Tests/PWRunnerCoreTests/ReaderCorpusTests.swift`

- **Reader corpus rows and per-reader expectations (`:65`, `:245-263`, `:350`)** — DT-53.b–f, DT-53.t1–t7, DT-132.a, DT-130.b–d. `independent` (`runner/Tests` is not a build-contract input; `controller/src/run_flow.rs` copies row keys through at `:1384` and needs no edit). The association rows for R9 are that thread's checks. [pass L]
  - Current: one Boolean, `expected_semantic`, is compared with the host verdict, Rust `admit_reply` and the consumer alike, so the corpus holds no ordinary-form claim fault.
  - Change: per-row `expected_host` (the `:350` comparison uses it when present) and `expected_projection`; rows `lifecycle-ordinary-final-status-absent` and `lifecycle-ordinary-final-status-17` built from `orderedOrdinary(applyRC: 0)`, with `ordering-ordinary` as the accepted baseline carrying `expected_lifecycle_findings: []`; row `ordering-ordinary-withheld` (`order` set to `unestablished` on an eligible record with the complete chain: host accepts, Rust admits with `valid`, consumer rejects with `s: eligible record with complete chain requires query_first`). Update `tests/suites/runner_unit/README.md` where it describes the corpus rows.
  - Check: `runner_unit/pwrunner_core_unit_executable`. Must reject an oracle or controller that accepts an absent or wrong `final_status`, a consumer verdict credited as a claim check, and a result that changes with the finding.

### `tests/fixtures/contract/normal_reply.json`

- **`request_failure` `:276-282` and `error` at `:387`** — DT-111.b, DT-111.e. `independent` [pass J]
  - Current: authors `"error": null` where the projection omits the key (`ValidatorVerdict.error` has `json_null: false`); lacks `request_failure.expected_contract`, which the projection carries.
  - Change: remove `"error": null` at `:387`; add `"expected_contract": "test:request"` to `request_failure`.
  - Check: `runner_unit/pwrunner_core_unit_executable` with the exact comparison.

### `tests/fixtures/validator/validator.py`

- **New diagnostic tail that keeps `rc`/`errno`, beside `:46-49`** — DT-49.a, DT-49.b. `independent` of the product threads; sequence with the seam migration of `validator_executable_path` (S-A/S-C), since `failure_boundaries/check.py` is a caller of that seam. [pass C2]
  - Current: the diagnostic fixture drops `rc` (`verdict.pop('rc')`).
  - Change: a tail with `outcome = "future_937"`, `rc = 17`, `errno = 5`.
  - Check: see `tests/suites/failure_boundaries/check.py`.

### `tests/lib/actor_evidence.py`

- **Readiness relations in `_setup`, `:149-159`, plus an actor cross-check** — DT-61.c, DT-133.c. `independent` [pass E]
  - Current: checks terminal applicability only; four constructed bodies with `ready` kept pass.
  - Change: (a) `ready` requires `required is True`, no `primary_operation`, and cells 3, 4, 5, 7, 8, 9, 10 present as succeeded/accepted/succeeded/accepted/succeeded/succeeded/accepted; (b) `not_required` requires `required is False`; (c) a `ready` worker scope requires that actor's host region scope to be `ready`; (d) an actor whose `setup_status` is `applied` or `unapplied_declared` and whose scope is `required` must have an observed `ready` scope without integrity errors.
  - Check: Python-only rows in `tests/suites/blackbox_e2e/extension_controls.py`: the four DT-61.c edits rejected; the unchanged body, a `terminal_required_failure` scope with a partial prefix, and a `not_observed` scope with cells accepted. Do not add these rows to `tests/fixtures/contract/actor_evidence.json` (the Rust test `typed_setup_equipment_application_and_gate_corpus` reads it). Before landing, run the rule over the Swift-built frames of `tests/suites/runner_unit/reader_corpus.py`. Then `blackbox_e2e/checker_controls`, the `witness_contract` extension cases and `unit/rust.unit` (shared fixtures unchanged).

- **Bound-row identifier requirement, `:302-309`** — DT-108.g. `independent` [pass J]
  - Current: the Python actor reader accepts a bound binding with no signing identifier; Rust (`porcelain_actor.rs:1869-1876`) and Swift (`PWRunnerEquipment.swift:229-231`) require a nonempty identifier.
  - Change: require a nonempty bounded `identifier` on a bound row. Add one shared row (bound binding without identifier, expected invalid) to `tests/fixtures/contract/actor_evidence.json`. This row is shared because the Rust test at `porcelain_actor.rs:2188` already rejects the shape; the readiness and custody rows of pass E stay Python-only because Rust accepts those.
  - Check: `blackbox_e2e/checker_controls`; `unit/rust.unit`.

### `tests/lib/blackbox.py`

- **`envelope_skeleton` for `policy_check_controls` (`:54-112`; `tests/suites/blackbox_e2e/checker_controls.py:39-43`)** — DT-115.4. `independent` [pass K]
  - Current: wraps helper captures in an envelope whose `runner_result` is a host reply labelled `xpc_error` with terminal `runner_reply`.
  - Change: a fallback-shaped skeleton: null `runner_result`, capture terminal `xpc_error` with its error record, result `xpc_error`.
  - Check: `blackbox_e2e/checker_controls`.

### `tests/lib/consumer.py`

- **Optional nullable-key presence check, `:483-486`** — DT-52.a (optional strengthening, T52-2). `independent` [pass C2]
  - Current: `attempt.get('errno') is not None` tests the type of a present value only.
  - Change: require the `errno` key on attempt and query records, with a passing null control and a rejected deletion in `tests/suites/blackbox_e2e/checker_controls.py` beside `:498-500`. Cost: `tests/fixtures/contract/exec_observation.json` omits the key in 51 attempt objects, read through `validate_exec_observation` only; every caller of `consumer.validate` over hand-authored steps must carry the key.
  - Check: `blackbox_e2e/checker_controls`.

- **`decode_fault.kind` membership** — DT-30.g. `independent` [pass C1]
  - Change: reject a `decode_fault.kind` outside the three assigned kinds (`ValidatorClient.swift:495-504`).
  - Check: accepted and rejected controls in `tests/suites/blackbox_e2e/checker_controls.py` (`blackbox_e2e/checker_controls`).

### `tests/lib/extension_evidence.py`

- **Custody relation after `:306`** — DT-65.b, DT-65.c. `independent` [pass E]
  - Current: accepts either issuance status for a completed non-null event without joining custody to transfers.
  - Change: for every transfer row with `custody_status == "held"`, the token named by `token_ref` must have status `issued` or `unresolved`.
  - Check: Python-only rows in `tests/suites/blackbox_e2e/extension_controls.py` on `tests/fixtures/contract/actor_authority_reply.json`: `issued_uncustodied` rejected with the new diagnostic; unchanged body accepted; `issued` beside a transfer and delivery rewritten to `custody_unavailable`/`unavailable` accepted. `extension_controls.py` must call `validate_actor_extensions` for these rows (its corpus loop calls only `validate_actor_evidence` today).

### `tests/lib/lifecycle_contract.py`

- **Comment at `:105-106`** — DT-120.d. `independent` [pass E]
  - Current: carries the exit-request-store wording.
  - Change: the host derives the trigger from this stop reason at final collection.
  - Check: `source_drift`.

- **Prohibited-inference line, `:241`** — DT-44.d (pass B, outside the review). `independent` [pass B]
  - Current: "not_reached from missing progress, an unfamiliar opcode, an absent slot or a live snapshot".
  - Change: "an absent slot alone", so the line and the positive row at `:234-236` are both true once the surface says "without a completed slot".
  - Check: `source_drift`; lifecycle oracle unit controls.

### `tests/lib/lifecycle_oracle.py`

- **Module docstring** — DT-135.a, DT-135.b, DT-135.d. `independent` [pass L]
  - Change: add "D6 phase-collection and extension findings come from `phase_evidence` and `extension_evidence`, which the consumer also calls; they are not a second judgment."
  - Check: `source_drift`; `blackbox_e2e/checker_controls`.

- **Derivation check near `:135-146`** — DT-120.e, DT-46.a. `independent`; land it first with the current table and run it against the current app (it passes: pass-through is `table.get(stop, stop)`), then the R13 table change follows in the host thread together with `tests/lib/lifecycle_contract.py:107-109`, `:752`. [pass E]
  - Current: each claim is compared with its own raw field; nothing checks the trigger against the stop reason.
  - Change: require `cleanup_trigger == TRIGGER_FOR_STOP.get(poll_stop_reason, poll_stop_reason)`. Controls in `tests/suites/blackbox_e2e/disposition_controls.py`: a mismatched pair (for example `completion` beside `sentinel_deadline`) rejected; an unknown pair accepted.
  - Check: `blackbox_e2e/checker_controls`; `witness_contract/worker_attempt_in_flight_at_deadline`, `witness_contract/worker_killed_before_slot_publication`.

### `tests/suites/blackbox_e2e/checker_controls.py`

- **Two target-relation controls** — DT-25.a, DT-25.c. `independent` [pass L]
  - Change: an NFC/NFD target pair reported `different_submitted` must be rejected with `comparison.target_relation disagrees with the submitted targets (same_submitted)`; a non-equivalent pair reported `same_submitted` must be rejected.
  - Check: `blackbox_e2e/checker_controls`.

### `tests/suites/blackbox_e2e/extension_controls.py`

- **Comment at `:129-130`** — DT-135.b. `independent` [pass L]
  - Change: "…Each reader entry point must reject the transplant for the stated reason; the lifecycle oracle surfaces the shared phase-evidence finding."
  - Check: `blackbox_e2e/checker_controls` (comment-only).

### `tests/suites/failure_boundaries/check.py`

- **Carried-return branch beside `:346-352`** — DT-49.a, DT-49.b. `independent`; follows the validator-substitution route current when it lands. [pass C2]
  - Current: requires -1 for a fixture whose diagnostic omits `rc`.
  - Change: for the carried-return tail expect `native_rc is None`, `rc == 17`, `errno == 5`, `outcome == 'error'`, `result_source == 'validator'`, `finished`, order `unestablished`, with the raw record under `phases[0].validator_subprocess.records` keeping `future_937`.
  - Check: `failure_boundaries/validator_frames` on a signed app. Must reject a host that forces `rc` to -1 for a carried return, or fills `native_rc` from a record whose outcome is not allow, deny or error.

### `tests/suites/runner_abi_layout/capture.c`

- **Header comment `:1-2`; known-answer digest** — DT-103.d, DT-102.b. `independent` (not a build-contract input) [pass I]
  - Current comment: "live authored controls separately qualify that layout".
  - Change: name what they observe (captured status and self-consistent bytes on the tested system). Assert the known answer for parameters `a=é`, `z=2`: `5aa8848d0fbdc2f9c5bb4c59cbf358459609fe0a42982d825a40ba787a36fcb6` (computed from the framing at `35-profile.surface.md:112`; recompute before pinning).
  - Check: `runner_abi_layout/c_swift_layout_agreement`.

### `tests/suites/runner_byoxpc/opt_in/reservation_controls.py`

- **`lost_execution`, `:471-484`** — LIM.d (optional). `independent` [pass K]
  - Change: assert the ordinary fallback capture: `policy_check.status == "ok"`, helper `policy_sha256` equal to the SHA-256 of the specimen's source, null diagnostics.
  - Check: `runner_byoxpc/reservation_controls` (opt-in; GUI session, identity). Optional neighbor: a zero-length result control in `runner/Tests/PWRunnerClientSessionTests/main.swift` (DT-119.f).

### `tests/suites/runner_outcome_bad_request/contract.py`

- **`capture_worker_death` `:498-512` and new capture rows** — DT-100.e, DT-102.a, DT-102.c, CL.c1 (and optional DT-98 control). `independent` of the product threads; `capture_worker_death` is the seam caller map's "live self-signal case", so its exact-key-set assertion joins that invocation's migration (seam S-A/S-C). [pass I]
  - Current: does not assert absence of the other eight withheld fields; every live capture assertion uses no parameters.
  - Change: for `capture_worker_death` assert the exact key set (`reason`, `status`, `worker_pid`); add an ordinary compile-failure specimen with capture requested asserting `successful_application_unconfirmed`, the exact key set, `sandboxed_after_apply` false and the worker's published compile failure; add one captured specimen with two parameters (one non-ASCII) asserting `parameter_count` and an independently framed `params_sha256`. Optional: one source importing a scratch file by absolute path, two runs with the file rewritten between them, asserting equal identity fields, different byte digests and a changed dossier closure.
  - Check: `runner_outcome_bad_request/accepted_input_contract` on the current signed app.

- **New actor-form `empty_step_id` refusal row** — DT-22.d. `independent` [pass C1]
  - Current: the code has one producer (`ActorPlan.swift:396`), is listed at `15-refusals.surface.md:82` and occurs in no test.
  - Change: an actor-form request with one empty action ID; expect `bad_request`, `request_failure.code: "empty_step_id"`, the action path, and no actor launch. Update `tests/COVERAGE.md` and the suite README.
  - Check: `runner_outcome_bad_request/accepted_input_contract`.

### `tests/suites/runner_unit/porcelain_replies.py`

- **`require_subset` `:24-37`, comment `:29`, call `:291`** — DT-111.b, DT-111.e. `independent` [pass J]
  - Current: an authored `null` is satisfied by an absent key; projected keys the fixture lacks are ignored; the comment says "shape checks own null-versus-omission".
  - Change: compare exactly: an authored `null` requires a present `null`; a projected key the fixture lacks is a failure. Correct the comment.
  - Check: `runner_unit/pwrunner_core_unit_executable`. Must reject an omit/null flip on any optional field that `normal.pwp` leaves absent, an extra or missing projected key, and a changed byte spelling on a field the fixture carries.

### `tests/suites/runner_unit/reader_corpus.py`

- **Per-reader expectations, `:118-119` and beside `:94-96`** — DT-53, DT-132, DT-130. `independent` [pass L]
  - Change: use `case.get('expected_consumer', expected)`; add the `expected_projection` assertion against the Rust-assembled diagnostics.
  - Check: `runner_unit/pwrunner_core_unit_executable`.

### `tests/suites/source_drift/build_contracts.py`

- **New statement-as-oracle test** — DT-91.e, DT-93.a, DT-93.b, DT-88.d, DT-92.e, DT-08.b. `independent` as a test (not a build-contract input); it fails at HEAD naming `controller/interface` and `docs/publication.py` until the statement is corrected, so land it with the statement edit and keep the failing run as the pre-change observation. [pass H]
  - Current: no check compares the statement's list with the code; every fixture that uses `build_contract.inputs` copies whatever the code selects (`:214-215`).
  - Change: read the backticked names from the `inputs` definition of `docs/contract/00-identity.surface.md`. (i) Require the sets of roots, files and suffixes to equal `build_contract.DIRECTORIES`, `FILES` and `SUFFIXES`, naming each difference. (ii) Build a literal tree from the statement's names only, run the unmodified `docs/build_contract.py --root <tree>` and require stdout to equal an in-test recomputation of the stated framing. (iii) On that tree: one mutation per root and per explicit file changes the value; an eligible addition, a rename and a removal change it; a mode and mtime change and files with unlisted suffixes do not; after `git init` an ignored eligible file still changes it; a second temporary root gives the same value.
  - Check: `source_drift/build_contracts`.

- **Byte-sensitivity loop, `:246-250`** — DT-93.c. `independent` [pass H]
  - Current: names `runner/augments/mach-register.sb`, which never existed, and silently substitutes the first `*.sb` through a `glob` fallback.
  - Change: use `runner/augments/exec_baseline.sb`, assert that each named path exists, and delete the fallback.
  - Check: `source_drift/build_contracts`. Must reject a loop whose subject silently changes when the named file is absent.

### `tests/suites/source_drift/check.py`

- **`RULES`: new rule for the RESPONSE opening fence** — DT-07.a, DT-07.b. `independent` [pass A]
  - Current: nothing ties the fenced JSON at `docs/RESPONSE.md:125-137` ("the second action's two operands in EXAMPLE_DOCUMENT", `:121-123`) to `controller/src/example_document.rs:6`.
  - Change: a drift rule comparing the fence under "Read the published example" with the second action of phase `initial-reads` in `EXAMPLE_DOCUMENT`, minus `step_id`; declared inputs `docs/RESPONSE.md` and `controller/src/example_document.rs` (read only; no edit to the build input).
  - Check: `source_drift/runner_source_manifests_agree`; a passing and a rejected planner control in `tests/suites/source_drift/check_planner.py`. Note: this location's file changed after the assessments were written (`5ab8e530`); re-read it.

### `tests/suites/source_drift/contract_tree_controls.py`

- **Statement-coverage control, `:1335-1339`** — DT-02.b. `independent` [pass A]
  - Current: sums node anchors over `rendered.values()` only.
  - Change: also count each node anchor across every `docs/*.md` on disk; a node anchor occurs once across the documents readers can open.
  - Check: `source_drift/build_contracts`. Also catches a stale copy whose markers were stripped, which the generator refusal cannot.

- **Scope-preservation control, `:1350-1392`** — DT-04.a. `independent` [pass A]
  - Current: required phrases are looked for anywhere in a destination; one pair of case anchors is order-checked.
  - Change: each required phrase must lie between its own rule anchor and the next `<a id="contract-` anchor. Add the rejecting control: the sentence "A grant was admitted and a fresh continuous-clock sample is before the original deadline." moved from `contract-transport-delivery-invoke` to a final unrelated heading.
  - Check: `source_drift/build_contracts`.

- **New presence-word ratchet in `ContractTreeTests`** — DT-18.b. `independent`; lands after the per-field presence rules. [pass A]
  - Change: count input-record fields whose presence renders "as defined below" and whose meaning has none of required / optional / omit / omission / null / absent / absence / default; expected zero. Describe it in the suite README as a keyword heuristic.
  - Check: `source_drift/build_contracts`.

### `tests/suites/source_drift/generators.py`

- **`test_contract_map_refusals_validate_every_destination_before_writing`, `:1067-1099`** — DT-01.a, DT-02.a (R14 controls). `independent` [pass A]
  - Current: four map mutations (duplicate, unknown, omitted, missing region); no document-side mutation.
  - Change: add the nested-marker document mutation and the moved-destination pair (refused with the old file's regions kept; accepted with them removed), each asserting an unchanged snapshot for `--check` and for generation.
  - Check: `source_drift/generator_contract`. Run the new mutations against the generator before the refusals land and keep that run as the pre-change observation (both mutations are accepted today).

### `tests/suites/source_drift/porcelain_codec.py`

- **`test_literal_invalid_ids_variants_and_cycles_do_not_write`, mutation list `:361-393`** — DT-110.b–d, DT-107.e, DT-106.d (R8 controls). `independent` [pass J]
  - Change: add five rows, each requiring refusal with its diagnostic and unchanged fixture bytes: guard is a path form; dependent is a path form; chained guard; variant with two integer cases; variant case with an extra key.
  - Check: `source_drift/porcelain_codec`. Run them against the generator before the validation rules land and keep that run as the pre-change observation (all five are accepted today).

- **Fingerprint mutation loop, `:491-539`** — DT-106.f, DT-105.a–c. `independent` [pass J]
  - Current: a comment control and five structural mutations; none mutates a public name, null rule, projection, path-form or conditional rule, variant or root.
  - Change: add a public-name rename, a null-rule flip on an optional field, a projection change, a reversed `path_forms` list, a removed `conditional_null`, a variant case rename and a root-key rename; the existing assertions apply unchanged (every output changes; the old fingerprint is refused; a one-sided restore is stale).
  - Check: `source_drift/porcelain_codec`. Must reject a `wire_identity` that stops covering a presentation rule the statement lists.

### `tests/suites/validator_batch_mode/run.sh`

- **`direct-batch` step: unknown-type pair** — DT-37.a. `independent` [pass B]
  - Current: asserts `bad_filter` for an unknown type with a value (`e1`) and `parse_error` for `PATH` without a value (`e2`); no unknown type without a value.
  - Change: add a line with an unknown `filter_type` and no `filter_value` (expect `parse_error` naming `filter_value`) beside the existing unknown type with a value (`bad_filter`). Update `tests/suites/validator_batch_mode/README.md` and the case description in `tests/catalog.json` if they enumerate the controls.
  - Check: `validator_batch_mode/batch_ndjson_roundtrip`. Must reject a validator that resolves the filter name before checking value presence.

### `tests/suites/witness_contract/check_actor_compositions.py`

- **New same-visit self-transfer composition** — DT-59.b, DT-59.c. `independent`; if `witness_contract/actor_compositions` joins a pytest cohort, add after that cohort's migration equivalence is established. [pass E]
  - Current: both registered placements (`:33-50` and the unit test) put the self-consume in a later visit; the review's execution is not available.
  - Change: one unapplied actor, one phase: issue; transfer to self; consume; `read_fresh`; release. Assert `finished`, the transfer row `delivered` with `source_actor_id == recipient_actor_id`, the consume event `returned` with the same `phase_id` as the transfer, and `[]` from consumer and oracle.
  - Check: `witness_contract/actor_compositions` on the current app.

### `tests/suites/witness_contract/check_dossier.py`

- **New import-failure order row** — DT-33.a. `after R12` (same confirmation as the dossier statement). [pass C1]
  - Change: a source importing two absent names written in reverse byte order; assert `imports.failure` names the one first in the stated traversal and that each record carries its own `error`.
  - Check: `witness_contract/dossier_witness`.

### `tests/suites/witness_contract/check_extension_boundaries.py`

- **Issuer-erase assertion, near `:220-223` (or in the `:279-283` and `:326-332` branches)** — DT-64.c. `independent` [pass D]
  - Current: `issuer_token_erased` is asserted only when the observer holds a native token, so not for issuer modes 2, 3 and 16.
  - Change: assert `observed['issuer_token_erased']` for the fixture-supplied oversized (mode 2) and maximum (mode 16) returns. Retained default-battery output at `2f4d76e4` already shows the word true for `issue-2` and `issue-16`.
  - Check: `witness_contract/extension_boundaries`. Must reject removal of the refusal-branch clear (`pw_probe_runner.c:862`): the word stays 0 for `issue-2`.

### `tests/suites/witness_contract/check_extension_redelegation.py`

- **Comment at `:266-267`** — DT-67.a. `independent` (comment-only change to a default case's checker) [pass D]
  - Change: align the comment with the README: omitted-consume contrasts are asserted incomplete; weakened-policy credit is computed and recorded, not asserted.
  - Check: rerun `witness_contract/extension_redelegation` before crediting the case against the edited file, or record the comment-only delta as a reviewed exception under `tests/AGENTS.md`.

### `tests/suites/witness_contract/check_ordering.py`

- **`spawn_failed` check, `:272-284`** — DT-24.a. `independent` [pass C1]
  - Current: does not assert the step's `missing_reason`.
  - Change: assert `missing_reason == "validator_not_invoked"` beside `collected` and `not_spawned`.
  - Check: `witness_contract/validator_spawn_failed_reports_degraded`.

### `tests/suites/witness_contract/check_phases.py`

- **Excluded-step `pid` assertion** — DT-24.b. `independent` [pass C1]
  - Change: for the excluded query in the `not_needed` phase assert `query_not_requested`, `pid` equal to the worker PID and no validator subprocess.
  - Check: `witness_contract/phases`.

### `tests/suites/witness_contract/check_pre_apply_failure.py`

- **New `lifecycle_claims` group after `:253`** — DT-53.g, DT-53.t10, ACC-CLS.7. `independent`; run the revised checker against the current app first (replay over its seven retained checkpoint envelopes predicts no finding). [pass L]
  - Current: calls `consumer.validate` (`:83`, `:292`, `:339`) and asserts raw host observations; a withheld projection would pass, while the case carries lifecycle credit (`tests/COVERAGE.md:236`, FPC `:683`, suite README `:1157-1159`).
  - Change: import `lifecycle_oracle`; add a group `{name}.lifecycle_claims` calling `lifecycle_oracle.check_record` for both runs; update `tests/suites/witness_contract/README.md:1157-1161`.
  - Check: `witness_contract/pre_apply_failure_reports_no_policy_verdict`. Its `worker_pre_ready_hang_ms` control is one of the eight moving to `test-input run`; follow the route current when it lands.

## Comments in build inputs

Each of these rides with a product thread's rebuild. Where no ruling edits
the file itself, the entry says so; the comment then shares that thread's
rebuild and worker-identity regeneration and forces none of its own.

### `controller/tools/pw_probe_runner/pw_probe_runner.c`

- **Status-word comment, `:21-22`** — DT-45.a (pass C2, outside the review). `comment in build input` — pass C2 places it in the R1 rebuild; no ruling's worklist otherwise edits this file, so confirm the exec-stream thread (R1) takes it (the file is a worker-identity input and R1 regenerates that identity). [pass C2]
  - Change: the same correction as the header comment.
  - Check: worker-identity regeneration and the R1 rebuild.

### `controller/tools/pw_probe_runner/pw_probe_runner_abi.h`

- **Status-word comment, `:207-219`** — DT-45.a (pass C2, outside the review). `comment in build input` — rides with the exec-stream thread (R1), which already edits this header. [pass C2]
  - Current: describes status-word writes on preparation and compilation failures.
  - Change: correct the comment's account: the word is written only with the return of the application call.
  - Check: worker-identity regeneration and the R1 rebuild.

### `runner/Sources/PWRunnerCore/CWorker.swift`

- **Comment at `:559-562`** — DT-120.d. `comment in build input` — rides with the exec-stream thread (R1), which edits `CWorker.swift` directly, or with the host thread (R13), whose worker-identity regeneration rewrites this file's generated lines. [pass E]
  - Current: carries the exit-request-store wording.
  - Change: the trigger is derived from the stop reason at final collection. The order-barrier control patches this file at exact anchors; the comment is not an anchor, but review the control if an anchor moves.

### `runner/Sources/PWRunnerCore/CWorkerDisposition.swift`

- **Comment at `:80-81`** — DT-43.a. `comment in build input` — rides with the host thread (R4, R5, R9, R13). No ruling edits this file itself; the comment shares that thread's rebuild and worker-identity regeneration. [pass E]
  - Current: "production passes the plan".
  - Change: the ordinary form passes the plan; the actor form resolves from each actor's collected slots.

### `runner/Sources/PWRunnerCore/PWRunnerLifecycleEvidence.swift`

- **Doc comment above `PWHostWait`, `:128-137`** — DT-44.a1. `comment in build input` — rides with the host thread (R4, R5, R9, R13). No ruling edits this file itself; the comment shares that thread's rebuild and worker-identity regeneration. [pass B]
  - Current: carries the `clock_unavailable` "bounded sleep fallback" sentence.
  - Change: the same correction as `lifecycle.host_wait.stop`.
  - Check: reading; rebuild with the host thread.

### `runner/Sources/PWRunnerCore/PWRunnerPathEvidence.swift`

- **Comment at `:17-20`** — DT-109.c. `comment in build input` — rides with the host thread (R4, R5, R9, R13). No ruling edits this file itself; the comment shares that thread's rebuild and worker-identity regeneration. [pass J]
  - Current: labels the compacted form the "Wire form".
  - Change: "Public JSON form" (the wire carries every form).

### `runner/Sources/PWRunnerCore/PWRunnerPredictionEvidence.swift`

- **Comment at `:157`** — DT-50.c, DT-131.d. `comment in build input` — rides with the host thread (R9 edits this file). [pass L]
  - Current: "shared with every reader that recomputes it".
  - Change: "shared by host association and reporting validation; the controller and the test readers implement the rule separately".

## Records

### `records/TRACE-MANAGEMENT-PLAN.md`

- **"Evidence availability and reuse limits" table** — CL.5 (and CL.1, CL.3). `independent` [pass B]
  - Change: add one row for the CONTRACT-tracing scratch directory (`/private/tmp/claude-501/…/1b7c19fb-c395-4c94-9f87-0906550f66e3/scratchpad/`): absent; every "reproduced" item in DT-22–44 that depended on it is an account of an earlier observation, not replayable evidence.
  - Check: none (record).

- **"Import and receipt association" bounded assessment and the dispositions** — U1.o1, U1.6, U1.2a, U2.N1, U2.1f, U2.4c. `independent` [pass G]
  - Change: record that the source join holds by construction and is compared by tests (`check_dossier.py:161`, `:202`; `cli_contract.rs:1293`, `:1460-1464`; `runner_use_c_worker/run.sh:706`; `check_actor_compositions.py:132`), correcting the review's "no reader compares"; record the two unexecuted inferences (a same-source recompilation cannot reveal a scanner miss; system-directory imports cannot change within a boot). The review stays unchanged.
  - Check: none (record).

- **Reader population in the disposition** — ACC-LIM.b, DT-53.t8, DT-53.t9, DT-132.c. `independent` [pass L]
  - Change: record that about forty-nine default live cases reach the consumer with no oracle (the review's count of twenty-eight is a lower bound from a static map that did not follow `blackbox.validate_run_shape`, `tests/lib/unavailable_prediction.py`, `footprint_workloads.HeldWorkload` or inline shell Python), that `witness_contract/extension_combinations` also runs the oracle, and that `.tmp/contract-trio/acceptance/reader-case-map.jsonl` is not reused as a complete list.
  - Check: none (record).

## Items the product threads carry

Not part of this worklist. Listed from the assessments' own worklists so
the accounts thread can confirm each landed with its ruling and does not
write it twice. An item marked † is a test or cleanup inside a
build-contract input that an assessment asks for without a ruling of its
own; it needs the named thread's rebuild.

| Ruling (thread) | Accounts and checks the thread lands with its code |
| --- | --- |
| R1 (exec stream) | `31-steps.surface.md:238-244`; `32-lifecycle.surface.md:1407-1426` (new stream fields); `docs/limits.json` `exec_stream` `behavior` and `checks` (DT-55.g); `tests/FAILURE-PROPAGATION-CONTRACT.md:1101-1102`; `docs/porcelain.json` and generated readers; `tests/fixtures/contract/exec_observation.json`, `response_shape.json`, shape goldens (`--refresh-shapes`); `ReplyMaximumTests`, `porcelain_replies.py` accounting, `check_max_target_reply.py` margins; six `runner_use_c_worker` contrasts; `tests/COVERAGE.md`; the two status-word comments listed under "Comments in build inputs". |
| R2 (controller A) | `50-installation.surface.md:34-39` and a new support owner under "Read and select records"; `controller/README.md:311-319`; unit controls on `load_registry` and on selection; the integration control for list, reconcile, status and `run`; integration and unit README invariants. † The classifier unit control of pass F (`plist_ownership` and `service_ownership` branches, `controller/src/runner_manager.rs` tests) and its citation from the owners at `50-installation.surface.md:209-216`, `:801-807`. |
| R3 (identity tool) | `docs/source_identity.py`; literal-tree walker controls and the pinned digest in `source_drift/build_contracts`; two build-entry controls; `docs/build.json` refusal row (then `docs/generate_build.py`); worker-identity regeneration. The statement edit is listed above under `00-identity.surface.md`, marked `after R3`. |
| R4 (host) | `30-reply.surface.md:188-191` and its support owner `:209-219`; the `finished` necessary condition in `tests/lib/consumer.py` with controls in `blackbox_e2e/checker_controls`; new case in `runner_validator_failure`; `ActorReplyTests` rows for spawn and pipe failures; `tests/COVERAGE.md` validator rows. |
| R5 (host) | `21-wire.surface.md:201`; `tests/FAILURE-PROPAGATION-CONTRACT.md:996-998`; `tests/lib/lifecycle_adapter.py:132`; live pair and fixture rows in `failure_boundaries`; oracle control in `blackbox_e2e/checker_controls`; `ValidatorEvidenceTests` row. |
| R6 (controller A) | `00-identity.surface.md:797`; `40-envelope.surface.md:96-100`; `50-installation.surface.md:39` (write-failure form); the helper exit statement in `11-policy.surface.md`; `controller/README.md:84-90`; reader-less-stdout rows in `controller/integration/cli_contract.rs`. |
| R7 (controller A) | `50-installation.surface.md:85`; an integration row for the install refusal (or the assertion in `runner_byoxpc/registry_recovery`). |
| R8 (wire) | `21-wire.surface.md:82` refusal list; generated Rust reader and `tests/lib/porcelain.py`; the changed codec control and the literal-frame Rust test; `tests/suites/source_drift/README.md:786-790`. The generator-side validation is in this worklist. |
| R9 (host) | `31-steps.surface.md` "Unique association" and `32-lifecycle.surface.md:1164-1166` (byte-equality sentence); the failure contract after `:614`; `OrderingTests` assertions; reader-corpus association rows. Open for that thread: whether worker-slot identity joins follow the same byte rule (pass L, outside the review, item 5). |
| R10, R11 (controller B) | `11-policy.surface.md:688` (`free.effect`), `:702`, `:703`; `40-envelope.surface.md:152-155`; `42-dossier.surface.md:36`, `:92`, `:93`; `controller/README.md:5-8`, `:173-175`; `docs/CONTROLLER.md:118-119`, `:313-316`; `docs/ARCHITECTURE.md:160-163`; `docs/architecture.json` T12 label. † The selected `run_flow.rs` test corrections (pass K section 6.1 items 1–5, the decision 3 rows, the over-capacity row, the generic-message assertion, the production foreign-contract text, the parser-equivalence control in `runner_client.rs`); † the receipts label-test correction (pass I step 7), after which the `35-profile.surface.md` "Constructed run labels" owner is refreshed; † optional: a Rust control for the reporting-outcome-without-record branch (`porcelain_admission.rs:1469-1476`, DT-44.m); `tests/suites/unit/README.md:25-39` if a described test changes. |
| R12 (controller C) | `11-policy.surface.md` new field, `:547`, `:551`, `:378`; `42-dossier.surface.md:51`, `:263`, `:309`; `tests/fixtures/contract/envelope_shape.json`; `surfaces/policy.json` (`--refresh-shapes`); `tests/suites/blackbox_e2e/checker_controls.py:50-51`; helper contrasts in `controller/integration/cli_contract.rs`; dossier contrasts in `check_dossier.py`; lexer, resolver and helper unit tests; removal of the unit test at `sbpl_imports.rs:447-453`; `tests/suites/witness_contract/README.md` dossier section. |
| R13 (host) | `PWRunnerDisposition.swift:21-23`; the mirror table and self-check in `tests/lib/lifecycle_contract.py:107-109`, `:752`; the actor hang control in `check_actor_compositions.py:346-360`. † Optional: removal of the unread `custodyNames` table (`ActorOrchestration.swift:295`, DT-123.a), with R4, which edits that file. |

## Outside-the-review notes that no ruling or disposition settles

For the coordinator; none is an entry above.

- `runner validate` counts a recorded executable under an inaccessible
  ancestor as missing and saves that (`runner_commands.rs:705-709`,
  `:738`); the surface says "did not exist" (pass F). Same idiom as
  DT-74; R2 does not cover it.
- The read act's entry list (`50-installation.surface.md:31`) omits
  `runner install`, `runner validate` and external selection in `run`,
  which use the same loader (pass F).
- `docs/ARCHITECTURE.md:441-442` and `docs/LIMITS.md:303` route receipt
  provenance and prerequisites to the frozen guide; the complete
  statement is in RESPONSE (pass I). Repointing is an arrangement change
  no recommendation requires.
- `docs/build.json` has no refusal row for any derivation refusal of
  `docs/build_contract.py`; R3 adds one for the new refusal only
  (pass H).
- Other traversals discard listing errors as the identity walker does
  today: `tests/lib/native_sources.py:223,225`,
  `tests/lib/fixture_inputs.py:136`, `tests/lib/receipts.py:90`
  (pass H; not assessed).
- The consumer's order chain also requires `arrival_observed`
  (`consumer.py:253`), one condition more than the stated chain
  (pass L).
- Reply `sandbox_check.operation` can carry the validator's spelling;
  R9 returns it to the submitted bytes (pass L).
- Whether `tests/lib/consumer.py` should admit `actor_policy_checks`
  captures is undecided (pass K); B9's credit is narrowed until then.
- `formNames` in `PWRunnerPathEvidence.swift:22, 56` has no reader
  (pass J).

## Regeneration order for the batch

Land generator code and its controls before the account edits that
regenerate through them. Then, from the repository root:

```sh
tests/lib/python.sh docs/generate_porcelain.py --check     # after the validate() rules; expect 84 records, no output change
tests/lib/python.sh docs/generate_limits.py                # limits.json, EXTENSIONS, shared regions, authored spans (the DT-37.f spans)
tests/lib/python.sh docs/generate_architecture.py          # architecture.json
tests/lib/python.sh docs/generate_interface.py             # joins, after the new interface case
tests/lib/python.sh docs/generate_contract_stamps.py       # surfaces, presentation.json, trace-introduction.md, tree.py, presentation.py
```

Development mode reports publication withheld and leaves the guide
untouched. No entry in this worklist changes a record shape, so no
`--refresh-shapes` is expected; the one place to watch is the
`cleanup_trigger` vocabulary block. If the generator names
`--refresh-shapes`, review the golden difference before refreshing. If a
prose or free-text guard refuses an authorized sentence, revise that
rule with positive and negative controls; do not disable it.

Then check every owner:

```sh
tests/lib/python.sh docs/generate_limits.py --check
tests/lib/python.sh docs/generate_architecture.py --check
tests/lib/python.sh docs/generate_build.py --check
tests/lib/python.sh docs/generate_interface.py --check
tests/lib/python.sh docs/generate_contract_stamps.py --check
tests/lib/python.sh docs/generate_contract_stamps.py --check --require-history
tests/lib/python.sh docs/build_contract.py                 # identity unchanged by this batch
```

Expected generated differences: CONTRACT's stamp table for the edited
surfaces (identity, request, policy, probes, actors, extensions,
refusals, transport, wire, reply, steps, lifecycle, actor_evidence,
equipment, profile, envelope, diagnostics, dossier, installation);
REQUEST, RESPONSE and ARCHITECTURE regions; `docs/contract/public.json`;
`docs/LIMITS.md`; `docs/BUILD.md` commitment lists. The guide's copies,
limit spans and stamp table stay at their `3d3f8e65` bytes.

Entries marked `after R<n>` regenerate with, or after, that thread; they
do not block the independent entries.

## Verification selection for the batch

Record this selection and its rationale before executing. No entry
changes a build-contract input, so the batch runs on the signed app
current when it lands; a fresh `PW_TEST_OUT_DIR=tests/out/runs/<name>`
and the checkout lock apply.

| Boundary changed | Selection | Why |
| --- | --- | --- |
| Generators, surfaces, limits, architecture, authored documents | `tests/run.sh --suite source_drift` (notably `generator_contract`, `build_contracts`, `limits_documentation`, `architecture_documentation`, `porcelain_codec`, `runner_source_manifests_agree`); `--case preflight/build_entry_controls` | Owning generation and `source_drift` for documentation; the build binds `generate_porcelain.py --check`. |
| `docs/limits.json`, controller integration rows, interface case | `--suite unit --suite integration` | `unit/rust.unit` compiles `docs/limits.json` in; new `cli_contract.rs` rows and the interface case run in `integration/cli.integration`. |
| Swift test files under `runner/Tests`, `porcelain_replies.py`, `reader_corpus.py`, `normal_reply.json` | `--suite runner_unit`; `--case runner_abi_layout/c_swift_layout_agreement`; opt-in `runner_unit/actor_handoff_mutations` | Scheduler, authority, reply, capture, resolver and corpus rows; the exact normal-fixture comparison; the C known-answer digest. `ActorAuthorityTests.swift` and `ActorSchedulerTests.swift` are inputs of the opt-in mutation case. |
| Python readers (`consumer.py`, `actor_evidence.py`, `extension_evidence.py`, `lifecycle_oracle.py`, `blackbox.py`) and their controls | `--case blackbox_e2e/checker_controls`; then the default `witness_contract` cases that run these readers on live envelopes, including `extensions`, `extension_boundaries`, `extension_combinations`, `extension_redelegation`, `actor_compositions`, `worker_attempt_in_flight_at_deadline`, `worker_killed_before_slot_publication` | New reader rules must reject their constructed controls and accept current live output. Run each new rule over the retained envelopes before landing, as the assessments did. |
| Individual checkers | `--case witness_contract/phases`, `--case witness_contract/validator_spawn_failed_reports_degraded`, `--case witness_contract/pre_apply_failure_reports_no_policy_verdict`, `--case witness_contract/dossier_witness`, `--case validator_batch_mode/batch_ndjson_roundtrip`, `--case failure_boundaries/validator_frames`, `--case failure_boundaries/admission`, `--case runner_outcome_bad_request/accepted_input_contract` | Each carries an added assertion or control from this worklist. Controls that use validator substitution or a selected worker control follow the `test-input run` route once the seam migration lands. |
| Opt-in assertions, if taken | `runner_byoxpc/registry_recovery`, `runner_byoxpc/reservation_controls` in a logged-in GUI session; verify owned resources absent afterwards | Only when the optional assertions are added. |

Revised checks run first against existing behavior where the plan
requires it: the R14 generator mutations, the R8 schema refusal rows,
the statement-oracle test and the presence ratchet are expected to fail
before their change lands; the reconcile no-change control, the
same-visit composition, the oracle derivation check and the
`pre_apply_failure` oracle group are expected to pass. The reader
changes reach every live case, so the grouped default battery of the
final integrated verification is their broad check; no additional
battery is needed for this batch.
