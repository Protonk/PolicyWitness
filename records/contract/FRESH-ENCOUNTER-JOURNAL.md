# Interpretation journal: first reading of CONTRACT.md

This journal follows `docs/CONTRACT.md` in document order. Entries are appended before proceeding to the next portion; earlier entries retain the understanding and uncertainty present at their source passage. Line references identify the document as read. Later entries may answer earlier questions without revising them.

The examination reads the contract and the root, `docs/`, and `.tmp/` AGENTS guidance. Repository guidance governs the examination but is not used as evidence for beliefs about the contract. No implementation, tests, verification artifacts, or other agents' findings are consulted. The journal is the sole output file.

## 1. The public boundary is an exact identity boundary

Source: [lines 1–6](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:1).

**What do I now believe?** A saved specimen must assert a contract identity. Independently received envelopes, host replies, and client captures identify their producers. PolicyWitness does not negotiate a mutually acceptable version, silently accept another identity, translate historical material, or offer an admission bypass. I infer that otherwise understandable material can still be inadmissible because of identity.

**What supports that belief?** Lines 3–6 explicitly tie the public contract to the release, require the assertion and producer identification, and say admission is exact with none of those compatibility mechanisms. Rejection on identity despite understandable content is my inference from exact admission.

**What remains uncertain?** I do not yet know the identity's representation, the exact values accepted outside releases, or how an admission failure appears to a caller.

## 2. Release, development, and unbound identities

Source: [lines 8–15](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:8).

**What do I now believe?** A clean tree at exactly one annotated `vX.Y.Z` tag produces `release:vX.Y.Z`. Other packaged builds identify themselves as `development:<sha256>`, calculated from shipped source and build inputs, including their paths and on-disk contents. Ordinary documentation or test edits do not change that digest, while shipped-input edits do. A dirty release tree becomes a development build. Release admission checks scoped source bytes against tag blobs, so Git index flags cannot conceal relevant edits. The scope follows declared language/resource suffixes and explicit build helpers in both checkouts and source copies, and excludes incidental executables and OS files. Direct Cargo and SwiftPM builds are `unbound` and refuse both public requests and packaged peer checks. `--version`, envelope `build.contract`, and app/service `PWContract` expose the compiled identity; describe and commit values are provenance rather than compatibility keys.

**What supports that belief?** These are explicit claims in lines 8–15. Combined with lines 3–6, they lead me to expect exact matching against the compiled contract identity, rather than accepting a matching commit or describe string as a substitute.

**What remains uncertain?** The exact shipped-input inventory and hash serialization are not given here. I also do not yet know the refusal shape for an `unbound` producer. I do not need the inventory to understand the stated distinction between identity and provenance.

## 3. Reuse requires the specimen author's decision

Source: [lines 17–20](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:17).

**What do I now believe?** Moving a saved specimen to another release is a deliberate author operation: inspect changed surfaces, reconsider their definitions, and manually change the assertion. PolicyWitness never rewrites the user's specimen. External runners must be reinstalled from the current app when its contract changes. I infer that updating the app alone does not make a previously installed external runner suitable for the new contract.

**What supports that belief?** Lines 17–20 explicitly assign review, assertion changes, and reinstallation to the user. The external-runner inference combines that instruction with exact admission in lines 3–6.

**What remains uncertain?** I have not yet seen how to identify changed surfaces or how an old external runner is diagnosed.

## 4. Surface stamps describe changes, not compatibility

Source: [lines 22–50](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:22).

**What do I now believe?** `contract_surfaces.json` defines the tracked surface scope. The transport golden includes the complete binary record identity, including host-reply tags, native widths, and presentation rules. Transport and installation goldens also cover reservation limits and the overall client allowance, including counting, effects, and controls. A generator hashes canonical shape goldens and delimited normative regions across reachable annotated release tags. New or changed surfaces remain `unreleased` until release preparation; removal does not erase a surface's history row. Surface stamps help me find definitions to revisit, but I neither assert them nor use them to admit an artifact.

The displayed table places every listed surface at `v0.3.6`: actors, dossier, envelope, equipment, installation, lifecycle, policy, probes, profile, refusals, request, steps, and transport. I read these as their displayed last-change stamps, not as thirteen independently selectable protocol versions or proof of the running build's identity.

**What supports that belief?** Lines 24–32 explicitly define scope, hashing, stamp lifecycle, and the exclusion from admission. Lines 35–49 give the particular rows and stamps. My interpretation of the table follows from that exclusion and the build-identity rules in lines 8–15.

**What remains uncertain?** The referenced goldens' concrete shapes and the precise reservation allowances are not yet described. I do not need to open the manifest to understand the role of stamps.

## 5. Stamp checking can have explicitly limited historical coverage

Source: [lines 52–56](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:52).

**What do I now believe?** Without annotated release history, `--check` can validate current inputs and agreement between two tables, but must report that historical stamp derivation was not checked. Regeneration must refuse to erase existing release stamps in that situation. Release preflight requires history and full derivation, as does `--check --require-history`. I would not treat an ordinary successful check without history as establishing the stamps' historical derivation.

**What supports that belief?** Lines 52–56 explicitly distinguish the checks and refusal. The last conclusion is an inference from the reported limitation.

**What remains uncertain?** The second table and the command owning these flags are not identified in this passage. The distinction between current consistency and historical derivation is nevertheless clear.

## 6. Request identity gates precede selection and execution work

Source: [lines 58–63](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:58).

**What do I now believe?** A request root must contain a string `contract` exactly matching the running build. Missing, null, nonstring, and foreign values refuse before selectors, augments, helpers, or children. Unknown-field validation comes after that identity gate. Runner selection uses `runner`, aliases, and required entitlements to choose one installed or bundled runner. If a request has both a foreign assertion and an invalid runner selector, I expect the contract refusal and no client startup, rather than a selector error or an attempted run.

**What supports that belief?** Line 63 states the required type, equality, precedence, selection role, and concrete combined-error example. It makes the earlier exact-admission rule operational for requests.

**What remains uncertain?** The exact refusal field names for the four identity errors and the selector forms remain unspecified at this point.

## 7. Request objects are closed, but parameter names are data

Source: [lines 65–75](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:65).

**What do I now believe?** Swift `Codable` decoding remains the parser, with `CodingKeys` defining accepted fields for the root, policy, phases, ordinary action/probe steps, sandbox checks, filters, attempts, and `_test_overrides`. An unknown key is a `bad_request` carrying a bounded field path; it is not silently ignored. Thus `policy.capture_compiled_profiel` is an error. `policy.params` is different: callers choose its names, but values must be strings. Missing required fields and wrong types are rejected. Optional null usually means absence, but explicit null is rejected for actor `equipment`, `required_entitlements`, phase `after_termination`, and the actor equipment override map. Omission selects those fields' documented defaults.

**What supports that belief?** Lines 67–75 explicitly establish the parser, closed fields, dictionary exception, type requirements, and null exceptions. Together with line 63, I expect these structural errors to be considered after contract admission.

**What remains uncertain?** This passage does not enumerate all accepted fields, define the bounded-path format, or give the omission defaults for the null-rejecting fields. “Generally” does not establish absence-equivalence for every other optional field.

## 8. Controller selection and augmentation are preprocessing responsibilities

Source: [lines 77–85](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:77).

**What do I now believe?** The controller validates selector types and every required entitlement, even aliases whose values will be shadowed; unknown nested selector keys also fail. A non-null nested selector overrides its top-level alias, including an explicitly empty entitlement list. Selection fields are removed before XPC submission, while their resolved meaning remains in runner provenance. A direct XPC caller must not supply those runner-selection fields. Actor `required_entitlements` is a separate surviving field, checked per actor by the host.

A nonempty `policy.augments` list requires string `sbpl_source`. The controller splices the named fragments and removes the list; a direct XPC request with unresolved fragments is rejected. I infer that controller-accepted input and direct-XPC-accepted input are deliberately different at these preprocessing fields.

**What supports that belief?** Lines 77–85 explicitly describe validation, precedence, removal, provenance, the actor exception, and augment resolution. The distinction between the two input paths follows from the explicit direct-XPC refusals.

**What remains uncertain?** The selector vocabulary, entitlement comparison semantics, fragment catalog, and splice order are not provided here. I can understand the boundary without opening the linked runner-selection reference.

## 9. Semantic validation constrains plans before workers or validators exist

Source: [lines 87–98](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:87).

**What do I now believe?** Unknown attempt kind/action pairs and filter kinds are rejected before creating any worker or validator. Non-null `attempt.args` is legal only for `exec/spawn`; a `none` filter cannot have non-null `filter.value`. `capture_nonce` requires compiled-profile capture to be enabled, and enabled capture requires a valid nonce. A request must choose exactly one non-null plan form, `probe_plan` or `phases`. Explicit phases must be nonempty and have unique, nonempty phase IDs. Every ordinary action has both a query and an attempt; step IDs must be distinct across phases; exec targets must be absolute.

A known operation/filter combination excluded from prediction is not automatically excluded from attempting: I expect an explicit `prediction_unavailable` observation and normal execution of a supported attempt. Operation names supplied to `sandbox_check` remain OS queries, and the validator may return `unsupported_operation`. Query and attempt scopes are allowed to differ, so I cannot assume they describe identical operations or targets merely because they share a step.

**What supports that belief?** Lines 87–98 state all of these constraints and distinctions. The final caution is an inference from the explicit permission for different scopes.

**What remains uncertain?** Nonce validity, the closed vocabularies, and the combinations excluded from prediction are not enumerated. The text places unknown pairs and filters explicitly before worker/validator creation; it does not separately restate the timing of every other meaning check listed here.

## 10. Identity changes require renewed author acceptance, including fixes

Source: [lines 100–106](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:100).

**What do I now believe?** Every shipped-source change changes a development contract, while a clean annotated release binds the public surfaces together. Additions, removals, semantic changes, and implementation fixes all require the specimen author to review and assert the selected build's identity. Optional additions receive no compatibility exemption, and there is no independent request-version counter. Maintainers are responsible for keeping definitions, verified examples, and shape goldens current so the stamp table directs the author's review.

**What supports that belief?** Lines 100–106 say this explicitly, reinforcing the manual reuse procedure in lines 17–20 and the stamp/admission distinction in lines 29–32.

**What remains uncertain?** Nothing consequential for this passage. I do not interpret it as promising that every implementation fix changes the request grammar; it requires acceptance of the build identity regardless.

## 11. Runtime capacity is a separate gate and never silently shortens a plan

Source: [lines 108–114](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:108).

**What do I now believe?** A syntactically and semantically valid request can still exceed a runtime admission limit, such as worker step capacity. In the stated example, refusal identifies the field, actual count, and maximum before any attempts occur. PolicyWitness never truncates or reinterprets the plan to fit. The caller chooses between revising the specimen and using a higher-capacity build. Raising capacity can admit more requests; lowering it can exclude previously runnable ones. Maintainers must document and test these changes even if the grammar is unchanged.

**What supports that belief?** Lines 108–114 state the separation, example, consequences, and responsibilities. Alongside lines 100–106, I understand capacity as part of the behavior an author must reconsider, rather than only a parser detail.

**What remains uncertain?** Numerical limits and their complete scopes are delegated to `LIMITS.md`; I have not read them because the separation and refusal principle are intelligible here.

## 12. Accepted intent does not guarantee repeatable OS observations

Source: [lines 116–124](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:116).

**What do I now believe?** The maintained request contract consists of existing decoder/selector fields, guide meanings, and acceptance/refusal tests, without an additional schema language or parser generator. Its protections preserve requested intent; they do not guarantee identical sandbox observations across builds or macOS versions. The linked developer lesson is described as using the same specimens as decoding/validation tests and signed CLI/direct-XPC controls. I take that as the stated relationship of the materials, not as verification I have performed.

**What supports that belief?** Lines 116–122 explicitly describe the maintenance model, limit on guarantees, and lesson/test relationship. This qualifies any expectation of reproducibility I might otherwise derive from exact identity admission.

**What remains uncertain?** No further uncertainty is necessary to understand this qualification. I have not opened the lesson or any controls.

## 13. Policies are held inputs with controller-resolved augments

Source: [lines 126–130](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:126).

**What do I now believe?** A policy provides SBPL source and optional string parameters. The controller resolves named augments in memory before submission; unresolved augments are refused on direct XPC. Imports and hashes describe the held policy input and its closure. A missing augment causes refusal before worker creation and leaves the input file unchanged. I infer that augmentation does not require rewriting the specimen on disk.

**What supports that belief?** Line 129 explicitly supplies these claims and the missing-augment example. The in-memory behavior, together with the no-rewrite statement in line 19 and preprocessing in lines 83–85, supports the inference about disk mutation.

**What remains uncertain?** “Closure” suggests the relevant imported inputs, but the import-resolution rules and hash coverage are not defined in this passage. I do not yet know when or how that input is held.

## 14. A probe contains separate prediction and attempted-operation observations

Source: [lines 132–136](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:132).

**What do I now believe?** Each probe has a unique ID, a sandbox query, and an attempt. Supported attempt actions and filter kinds are closed sets. Predictions do not establish enforcement agreement. In particular, I must not interpret a prediction as proof of what the attempted operation will do. The file `open_write` action opens with truncation, so I expect an admitted attempt to have potentially destructive file effects; a same-shape request with a foreign build assertion must be stopped before that operation.

**What supports that belief?** Line 135 explicitly distinguishes predictions and attempts, states the vocabularies and truncation behavior, and supplies the foreign-identity example. Lines 93–98 already require paired actions and allow differing scopes; line 63 supplies the early identity gate.

**What remains uncertain?** The complete action/filter lists and observation shapes remain unknown. I am not assuming a successful open or actual truncation in every run; the stated operation can still fail.

## 15. Actor execution uses fresh processes and ordered phases

Source: [lines 138–142](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:138).

**What do I now believe?** A specimen can use the ordinary single-worker form or named actors and phases. Every sandboxed process is fresh, and an actor applies its policy once. Phases identify the active actor and preserve action order. Extension transfer and consumption are represented by explicit owned records. A phase referring to a nonexistent actor is rejected before children are created. I infer that returning to an existing actor in another phase does not mean applying its policy again.

**What supports that belief?** Line 141 explicitly states the execution forms, freshness, once-only application, phase ordering, ownership records, and missing-actor refusal. The returning-actor conclusion follows from once-only application combined with phases naming active actors.

**What remains uncertain?** I do not yet know how actor policy, equipment, phase transitions, and extension records are encoded or which actor lifetimes can overlap. “Preserve action order” alone does not establish every cross-process scheduling detail.

## 16. Envelopes have producer-local admission boundaries

Source: [lines 144–148](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:144).

**What do I now believe?** Every envelope contains `kind`, `generated_at_unix_ms`, `build`, `result`, and `data`. Its own producer is identified by `build.contract`, which readers admit before interpreting semantic fields. A nested helper envelope has an independent build context; a current outer envelope does not make a foreign helper's compilation claim acceptable. Unsupported received bytes remain available, but do not support inferred claims. I expect a foreign helper claiming compilation to be unable to produce a successful policy-check status.

**What supports that belief?** Line 147 explicitly provides the fields, admission order, independent nested context, byte preservation, and example. The outer-versus-inner conclusion also follows from independent arrival/producer identities in lines 3–6.

**What remains uncertain?** I do not yet know the allowed `kind`/`result` values, where unsupported bytes are exposed, or how the policy-check failure is encoded.

## 17. A dossier describes the admitted, held submission

Source: [lines 150–154](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:150).

**What do I now believe?** The dossier records the held request path, policy provenance, imports, selected runner, host context, and observed binary inventory. Unknown observations remain unknown. Submission serialization and the fallback compiler use the same held input; changing the source file after admission does not alter the held submission. I infer that a later on-disk edit must not make the fallback compile a different specimen from the one submitted.

**What supports that belief?** Line 153 explicitly describes dossier contents, unknowns, shared held input, and the source-edit example. It gives more concrete meaning to the held policy input in line 129.

**What remains uncertain?** The holding mechanism, inventory observation method, and representation of unknowns are not specified. I do not infer that the dossier inventories every environmental influence.

## 18. Replies need their own admission, and comparisons do not assign sandbox cause

Source: [lines 156–160](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:156).

**What do I now believe?** A host reply exposes `producer.contract`, `producer.describe`, and `producer.commit`, and exact admission precedes interpretation of its steps. A foreign host reply inside a current envelope yields one unsupported diagnostic and no recovered comparisons. Comparisons relate query and attempt observations, but permission-shaped failures alone cannot establish a sandbox cause. `query_first` is available only with a collection/release evidence chain; I cannot treat it as a label justified merely by a query and attempt appearing in that order in a report.

**What supports that belief?** Line 159 explicitly states producer fields, admission, the foreign-reply outcome, causal limitation, and evidence requirement. Lines 14–15 identify describe/commit as provenance rather than admission keys; lines 95–98 and 135 already distinguish the query from the attempt and disallow an enforcement-agreement conclusion. The report-order caution is my inference from requiring an evidence chain.

**What remains uncertain?** The concrete chain, fields used to establish it, and the meaning of `query_first` when the chain is incomplete are still unspecified at this point.

## 19. Lifecycle and effect claims require observations beyond successful requests

Source: [lines 162–166](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:162).

**What do I now believe?** Lifecycle conclusions depend on native progress, collection, and termination observations. Unknown or contradictory observations prevent dependent claims. Requesting exit does not prove reap, and a successful return does not by itself witness an effect. Even a successful termination request leaves an unreaped worker unconfirmed. I therefore need to distinguish requesting an operation, receiving a successful return, observing an effect, and confirming a process lifecycle event.

**What supports that belief?** Line 165 explicitly states each evidentiary restriction and the unreaped-worker example. The distinction among these events is my combined reading of those restrictions, consistent with the comparison limits in line 159.

**What remains uncertain?** The precise lifecycle fields and which native observations support each disposition have not yet been specified.

## 20. Actor identity, equipment identity, and ABI identity are separate relationships

Source: [lines 168–171](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:168).

**What do I now believe?** Actor evidence binds observations to a named process and equipment sealed by the service. Worker ABI identity remains independent of public build identity; I cannot substitute one for the other. Worker entitlements come from reading the selected binary. An equipment hash mismatch prevents use of the equipment being claimed, rather than merely adding a warning while allowing the same claim.

**What supports that belief?** Line 171 explicitly states the binding, independence, entitlement source, and hash-mismatch consequence. The non-substitution conclusion follows from independence together with the exact public-admission rules already encountered.

**What remains uncertain?** The sealing mechanism, hash coverage, ABI identity representation, and the broader failure result for a mismatch are not yet given.

## 21. Actor evidence stays with its owning actor or setup cell

Source: [lines 173–181](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:173).

**What do I now believe?** Actor execution produces neither a declaration reply nor a singular worker projection. Instead, `actors[]` owns each actor's launch, subprocess, application assessment, and equipment association. Setup evidence also has distinct ownership: `authority_setup.host` contains run/region/custody scopes, and `authority_setup.workers` contains cells retaining primary setup, independent cleanup, and native-capability observations. An acquired decision does not imply publication of another cell. A scheduling summary cannot stand in for an actor's own facts. I infer that readers must retain these separate evidence locations rather than collapsing the run into one worker's status.

**What supports that belief?** Lines 176–181 explicitly assign the observations and deny cross-cell or summary substitution. The reader consequence follows from those ownership rules.

**What remains uncertain?** I do not yet know the detailed shapes or state vocabulary of the authority-setup scopes/cells, or the full meaning of an “acquired decision.” The passage does establish that it is not evidence of another cell's publication.

## 22. Equipment references are positional and distinguish packaged selection from overrides

Source: [lines 183–191](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:183).

**What do I now believe?** `equipment_inventory` identifies the selected service's sealed inventory. Rows in `equipment_bindings` and `equipment_entitlements` are referenced by position: `binding_ref` and `entitlements_ref` are zero-based indexes into their respective arrays. A binding's identity consists of its `role` and `source`. If no row was produced for an actor's role, its `binding_ref` is null. Packaged roles and explicitly instrumented overrides are distinguished; override rows carry `unverified_fixture` implementation identity and cannot establish packaged selection. Entitlement evidence includes independently associated static and live XML read-backs.

**What supports that belief?** Lines 183–191 explicitly define the inventory, references, null condition, override identity, and read-backs. These make the actor/equipment binding in line 171 more concrete.

**What remains uncertain?** I have not seen the full row shapes or the procedure for independently associating static and live read-backs. A null binding reference tells me that no role row was produced; it does not itself explain why.

## 23. Entitlement requirements are per actor, and runtime inspection failure cancels activation

Source: [lines 191–196](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:191).

**What do I now believe?** Each actor's entitlement requirements are evaluated separately using boolean-true keys, including in the live read-back. I do not take mere key presence or a nonboolean truthy value as satisfying this criterion. Limits and reserve geometry are defined elsewhere. Runtime inspection failure cancels all scheduled activation while retaining already published setup/application facts. It is not classified as a before-launch `preparation_failure`, and any independently established earlier cancellation remains visible.

**What supports that belief?** Lines 191–196 explicitly state the boolean-true test, per-actor evaluation, reference for bounds, and failure handling. The rejection of key-presence/truthiness as sufficient is an inference from the specified boolean criterion. Lines 83 and 171 previously distinguished per-actor host checks and selected-binary entitlement evidence.

**What remains uncertain?** The precise runtime-inspection failure marker and the full extent of inspection are not given. I do not infer that earlier facts disappear or that every actor was necessarily unlaunched when the failure occurred.

## 24. Preparation failure is a narrowly admitted prelaunch result

Source: [lines 198–202](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:198).

**What do I now believe?** A `preparation_failure` may contain only `resolved_plan/inconsistent_assignment` or `equipment/equipment_binding_refused`. It has `runner_failed`, `rc: 1`, no launched actors, and empty observation arrays. Unique bounded declarative phase/action identities may remain, but they do not claim execution. This is the sole exception to the otherwise complete observation partition for those identities. I infer that runtime inspection failure cannot be relabeled preparation failure simply because it prevents later work.

**What supports that belief?** Lines 198–202 explicitly restrict the categories, outcome, launches, arrays, and declaration-only exception. The relabeling conclusion also uses lines 194–196, which explicitly distinguish runtime failure.

**What remains uncertain?** “Complete observation partition” is not yet defined in detail, nor are the bounds on retained identities. The allowed preparation-failure result is otherwise concrete.

## 25. Application assessment separates nonattempt from missing evidence

Source: [lines 204–210](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:204).

**What do I now believe?** `actors[].application` admits only closed state/basis combinations. Unapplied intent is represented by `not_requested/unapplied_declaration`. `not_attempted` requires host evidence of no launch or an eligible terminal worker branch before application. `observed` requires either an applied publication or a native apply-failure publication, so “observed” does not itself mean application succeeded. If application was requested but neither evidentiary source exists, its state is `unobserved`. Setup timeout, `done`, process death, and auxiliary reporting failure are each insufficient by themselves to establish nonattempt.

**What supports that belief?** Lines 204–210 explicitly give these mappings and exclusion rules. The distinction between observation and success follows from the inclusion of native apply failure in `observed`; the distinction between missing evidence and absence accords with lines 165 and 195–196.

**What remains uncertain?** The complete basis vocabulary and the eligible terminal branches are not enumerated. I cannot infer nonattempt from an arbitrary terminal condition.

## 26. Termination dependencies refer to a particular actor-owned reap

Source: [lines 212–220](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:212).

**What do I now believe?** A termination dependency retains the source actor's `owned_reap`, including native PID, return value, raw wait status, capture stage, ownership/departure flags, `capture_ordinal`, and optional `observed_ns`. A phase can retain `activation_observation: {capture_ordinal, observed_ns?}`. The ordinals belong to the source actor process; they are not a global process counter. `termination_gate.observation` has shape `{capture_ordinal}` and points to that source actor's owned reap. Even a failed gate's nonnull observation must match a positive source reap ordinal and have a present, later gate `capture_ordinal`. I therefore cannot compare unrelated actors' ordinal values as if they established a global execution order.

**What supports that belief?** Lines 212–220 explicitly identify the facts, shapes, ordinal scope, and requirement applying to every nonnull gate observation. The global-order limitation is an inference directly from their local scope.

**What remains uncertain?** I have not yet seen all gate result states or capture-stage values. Matching an ordinal alone has not yet been presented as sufficient to satisfy a gate.

## 27. Satisfied termination requires ordered, owned native observations within an allowance

Source: [lines 220–228](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:220).

**What do I now believe?** To satisfy a termination gate, the source's final activation must precede its owned reap, which must precede gate closure. Child PID and decoded wait status must be consistent, ownership must remain unbroken, and there must be no prior host departure request. Final-activation and owned-reap timestamps must both exist and be monotonically ordered. The wait also needs a usable clock, no native wait error, and elapsed time within a positive termination-gate allowance. Abnormal natural reap can satisfy termination; normal exit is not required by this passage. Final phase completion, `done`, requested exit, and cleanup-only reap cannot replace the required termination evidence.

**What supports that belief?** Lines 220–228 explicitly add these conditions to the matching-observation rule in lines 217–220. The conclusion about abnormal exit follows from the explicit acceptance of abnormal natural reap, rather than a general assumption about process semantics.

**What remains uncertain?** The numerical allowance and detailed ownership/departure flag meanings are not specified here. I understand the conditions without consulting `LIMITS.md`.

## 28. Clock failures do not erase stored activation, and cleanup cannot repair a failed gate

Source: [lines 230–238](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:230).

**What do I now believe?** Native facts may survive a clock failure without source timestamps, but cannot satisfy the dependency without those timestamps. There is an asymmetric later case: once dependent activation has been stored, failure to capture its post-store timestamp preserves both that activation and the already satisfied gate; it cannot be reported as absence of activation. If a dependent timestamp is present, it must not precede source reap. A reached failed gate withholds activation, collection, and release, even if cleanup subsequently observes reap. I infer that later cleanup evidence is not a retroactive authorization for the dependent phase.

**What supports that belief?** Lines 230–236 explicitly distinguish absent source timestamps, absent post-store dependent timestamps, and failed-gate behavior. The last inference combines that withholding rule with the exclusion of cleanup-only reap in line 228.

**What remains uncertain?** No consequential uncertainty for these distinctions. The exact result shape used to expose a clock failure has not been provided.

## 29. A compiled-profile receipt relies on admitted context and internal consistency

Source: [lines 240–244](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:240).

**What do I now believe?** A compiled-profile receipt has no independent schema marker and inherits producer context from its admitted host reply. Its status, nonce, worker binding, stage, byte count, and digest must be mutually consistent. A detached receipt supplies no producer context, and a wrong nonce invalidates the receipt even inside a current reply. I infer that host identity admission is necessary but insufficient for accepting the receipt's content.

**What supports that belief?** Line 243 explicitly states the contextual and consistency requirements and nonce example. Lines 90–91 already require capture enablement and a valid nonce at request admission; line 159 requires admission of the host reply before interpreting its contents.

**What remains uncertain?** The permissible statuses/stages, nonce format, digest algorithm, and complete consistency relationships are not enumerated here. I cannot treat an arbitrary detached receipt as independently attributable to a build.

## 30. Capture, embedded reply, and live peer each need admission

Source: [lines 246–250](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:246).

**What do I now believe?** Client capture and reservation messages carry string `contract` fields. Capture admission and embedded host-frame admission are independent. A binary shape fingerprint protects decoding but is not a substitute for the public compatibility identity. Failed reservation or submission does not authorize replay after an invocation whose occurrence or outcome is uncertain. A registry record matching the current contract is insufficient if the live peer is foreign: that peer receives no specimen submission.

**What supports that belief?** Line 249 explicitly states these boundaries, the fingerprint distinction, replay restriction, and live-peer example. It extends the independent-envelope and host-reply admission rules from lines 147 and 159.

**What remains uncertain?** The handshake sequence and representation of uncertain invocation are not yet described. The rule does not establish which, if any, pre-invocation failures permit another attempt; it specifically denies replay authority after uncertainty.

## 31. Refusal precedence preserves identity, delivery, and malformed-output distinctions

Source: [lines 252–255](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:252).

**What do I now believe?** Request refusals use `bad_request`, bounded paths, and distinct missing/type/unsupported codes. Contract failures include `expected_contract`. Foreign output is classified unsupported, while malformed output remains malformed. Delivery failure takes precedence over reply interpretation. A legacy specimen containing only `schema_version` fails for missing `contract`, before its obsolete field can produce an unknown-field error. I infer that receiving reply-like bytes does not override a failed delivery result.

**What supports that belief?** Line 255 explicitly states the distinctions and example. Its example confirms the request gate ordering in line 63. The inference about reply-like bytes follows from delivery precedence.

**What remains uncertain?** The exact missing/type codes and delivery-failure representation have not yet been supplied. I do not collapse all unusable output into foreign-contract failure.

## 32. Structured request failure is optional evidence of refusal, not a success flag

Source: [lines 256–264](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:256).

**What do I now believe?** Malformed JSON, contract assertions, selectors, augments, field structure/meaning, and capacity refusals all report `bad_request` and make the controller exit 1. Unreadable request files, unavailable runner installations, and transport failures remain tool/execution failures rather than being reclassified as bad requests. The controller exposes `data.request_failure`; for a runner-originated refusal it copies the runner's `request_failure` unchanged. This is optional additive response/envelope information. Its absence establishes only that no structured diagnostic was supplied, never successful execution.

**What supports that belief?** Lines 258–264 explicitly classify these failures, give the exit status and field, specify unchanged copying, and restrict the meaning of absence.

**What remains uncertain?** Exit statuses for the separate tool/execution failures are not given here. Optional diagnostic presence is clear and does not itself imply any compatibility exception to the identity rules in lines 100–106.

## 33. Diagnostic paths are bounded locations, and error prose is supplementary

Source: [lines 266–271](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:266).

**What do I now believe?** A request-failure record has `code` and `path`, with `expected_contract` added for contract-field refusals. Paths consist of object keys and decimal array positions; `[]` means the root. At most eight components, each at most 63 UTF-8 bytes, may be echoed. If the full location cannot be reported, `path` is null; I should not interpret a shortened path as the complete location. Refused parameter keys are also withheld. Consumers must use code/path without parsing the human-readable `error` text.

**What supports that belief?** Lines 266–271 explicitly define the fields, path form, bounds, withholding, and machine-readable interpretation. The no-shortened-location conclusion follows from the requirement to use null when the full location cannot be reported. This supplies the bounds left open in entry 7.

**What remains uncertain?** The passage does not specify every representation choice for parameter-key failures. It clearly rules out expecting the refused parameter name to be echoed.

## 34. Refusal codes preserve particular categories of invalid intent

Source: [lines 273–284](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:273).

**What do I now believe?** I expect the following distinctions to remain observable in a structured refusal:

- `invalid_json`: the request cannot be parsed as JSON.
- `unsupported_contract`: its marker names another contract.
- `unknown_field`, `missing_field`, `missing_value`, `type_mismatch`, and `invalid_value`: respectively an unknown input, absent input, required value supplied as null, wrong type, or invalid value.
- `unsupported_policy_format` and `missing_policy_source`: absent structural policy prerequisites.
- `unknown_filter_kind`, `missing_filter_value`, and `empty_operation`: the requested sandbox query cannot be formed.
- `unsupported_attempt`, `relative_exec_target`, and `duplicate_step_id`: the submitted plan cannot be executed with its intended meaning.
- `invalid_termination_dependency`: a phase names an unknown source actor, itself, or a source whose final visit is not earlier than the dependent phase. The diagnostic path identifies `phases`, its index, `after_termination`, and `actor_id`. I infer that dependency validation considers the source's final visit, not merely whether that actor appeared at some earlier point.
- `inapplicable_field` and `invalid_capture_nonce`: a field cannot take effect or meet prerequisites.
- `conflicting_selector`, `unresolved_augments`, and `augment_unavailable`: conflicting controller-owned instructions, unresolved instructions reaching XPC, or unavailable named fragments.
- `admission_refused`: capacity or native-string admission failed. A separate `admission_failure` retains the field, actual count, maximum, and applicable positions.

**What supports that belief?** The table in lines 273–284 explicitly supplies these codes and meanings. The source-final-visit inference follows from line 281's specific criterion. Lines 63 and 255 combine with the table to lead me to expect absent, null, mistyped, and foreign contract assertions to remain distinguishable, with `expected_contract` supplied as described in lines 266–267.

**What remains uncertain?** Native-string admission's concrete restrictions are not defined here. The table gives grouped categories for several codes, not a complete mapping of every malformed specimen to one diagnostic.

## 35. Refusals report one problem and contain no execution observations

Source: [lines 286–291](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:286).

**What do I now believe?** These request refusals contain no steps or child-process observations. The XPC host may nevertheless have launched to decode the request; “refused before children” does not mean no service process could have started. Capacity checks precede meaning checks, and a diagnostic identifies one refusal rather than enumerating every defect. An unfamiliar code must remain an unclassified refusal instead of receiving a guessed cause.

**What supports that belief?** Lines 286–289 explicitly state the observation restriction, host-launch allowance, check order, singular reporting, and treatment of unknown codes. This refines the timing expectations from lines 87–110 without changing their prohibition on attempts for the described admission refusals.

**What remains uncertain?** The exact ordering within the capacity or meaning checks is not given. I should not expect an exhaustive defect report or infer success from an unfamiliar diagnostic.

## 36. Installation admission and execution admission are distinct checks

Source: [lines 293–296](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:293).

**What do I now believe?** Installation checks service `PWContract` before signing or changing launchd state and checks it again after signing. Execution requires both registry and live-peer identities to match. A record lacking a contract remains listable, reconcilable, and removable under existing ownership rules, although it cannot establish execution compatibility. In the explicit example, an owned legacy record cannot execute but can be removed after observed absence. I infer that identity rejection does not prevent legitimate cleanup of old records.

**What supports that belief?** Line 296 explicitly states each check and the legacy example. Lines 20 and 249 previously required external-runner reinstallation and no submission to a foreign live peer.

**What remains uncertain?** The ownership rules and what observation establishes absence are not defined here. I do not infer ownership merely from a matching identity or the ability to list a record.

## 37. Registry publication preserves opaque data without certifying it

Source: [lines 297–298](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:297).

**What do I now believe?** Unrecognized record, ownership, signature, entitlements, and registry metadata survive unrelated writes and pending cleanup as opaque data. A pending-cleanup entry contains nested `runner`, `cleanup_started_at_unix_ms`, and `observations`; historical flattened entries can also be read. Publication requires lossless read-back before atomic replacement, but publication itself establishes neither execution compatibility nor ownership. Known retired kind aliases are projected as their current kind. I infer that retaining an unknown value and trusting it for execution are separate operations.

**What supports that belief?** Line 297 explicitly states preservation, pending-entry shapes, historical reading, read-back/atomic replacement, the limits of publication, and alias projection. The retention-versus-trust distinction follows from those limits and exact execution admission in line 296.

**What remains uncertain?** The retired aliases and exact read-back failure result are not enumerated. Historical storage-shape acceptance does not lead me to expect historical public-contract admission or translation, which lines 3–6 forbid.

## 38. Production responses use generated typed structures and binary ingestion

Source: [lines 300–311](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:300).

**What do I now believe?** `porcelain.json` owns response and client-capture structure. `generate_porcelain.py` generates Swift writers/stored fields, Rust owned records/readers/JSON projection, and structural tables for a separately written Python reader. I expect the three structural definitions to agree because they derive from one schema. That shared derivation does not check whether the schema itself is correct. Request JSON, reservation JSON, and validator NDJSON retain separate boundaries. Production reply ingestion is binary; public JSON is a projection of typed records, while JSON reply fixtures serve as test inputs.

**What supports that belief?** Lines 304–311 explicitly describe ownership, generation, the asserted structural agreement and its limitation, separate boundaries, and production/test formats. This gives a concrete role to the binary fingerprint mentioned in line 249 without making it a public identity.

**What remains uncertain?** The complete schema and implementation of semantic admission are not included. I do not read shared structure as a promise that the separate readers independently validate the schema or establish identical semantics by generation alone.

## 39. Binary framing has canonical structure but leaves vocabulary to semantic admission

Source: [lines 313–325](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:313).

**What do I now believe?** A frame contains `PWP1`, the SHA-256 of the schema's wire identity, and one root value. Each value has a one-byte kind, four-byte little-endian payload length, and payload. The kinds are boolean, signed integer, unsigned integer, UTF-8 text, bytes, record, list, ordered string map, and declared variant. Integers take eight bytes on the wire, while readers enforce each field's native signedness and width. Digests are bytes. An equipment-row reference is an unsigned index into its named table.

Outcomes, states, reasons, and request-chosen step/phase/actor/token/delivery/handle names travel as text. Semantic admission, rather than the frame alone, checks their vocabularies and associations. A record begins with a two-byte identity and uses strictly increasing, nonzero two-byte field tags followed by values. Lists and maps begin with a four-byte count; map keys must be unique and sorted by UTF-8 bytes. A variant begins with a two-byte case tag. I infer that a structurally decodable text value need not be an admissible state or valid actor association.

**What supports that belief?** Lines 313–325 explicitly give these encodings and the division between framing and semantics. The inference follows from line 322, and the unsigned equipment references align with the zero-based arrays in lines 183–187.

**What remains uncertain?** Boolean encoding, allowed record/field/case identities, and handling of malformed structures have not yet been detailed. The passage specifies little-endian ordering for payload length; I do not generalize that statement to every numeric element without further text.

## 40. Missing optional values stay missing, and decoding has strict structural rejection

Source: [lines 326–334](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:326).

**What do I now believe?** A missing optional field remains absent rather than receiving a fabricated default. Readers reject unsupported fingerprints; unknown tags, records, or cases; missing required fields; incorrect kinds; invalid text; impossible lengths/counts; duplicates; and trailing data. The primitive reader enforces byte and nesting budgets and charges decoded collection slots, strings, and bytes to one logical-storage budget per frame. This does not establish a physical peak-memory bound. A client capture and its embedded host reply are separate frames with separate budgets, rather than sharing one combined decoding allowance.

**What supports that belief?** Lines 326–334 explicitly give absence handling, rejection categories, accounting, the memory limitation, and independent frames. These fill in the malformed-frame behavior left open in entry 39.

**What remains uncertain?** Numerical budgets and accounting charges are not specified here. I have not opened the linked primitive-reader source: the stated behavior is sufficient to interpret the passage, and implementation examination is outside this reading.

## 41. Writer, client retention, and controller collection impose different boundaries

Source: [lines 334–339](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:334).

**What do I now believe?** The host writer limits a reply to the frame limit, but the client retains only a smaller reply allowance. A reply exceeding that client allowance arrives truncated and is refused as `runner_reply_truncated`; satisfying the writer's frame limit therefore does not guarantee client acceptance. The controller collects the client's complete output before applying its own retention cap. That read is not streamed and has no receiver deadline of its own. I consequently cannot treat the retention cap as a bound on how much client output must first be collected, or infer a receiver timeout from this cap.

**What supports that belief?** Lines 334–339 explicitly describe the relative limits, truncation result, collection order, nonstreaming read, and absence of a receiver-owned deadline. The implications follow from the smaller client allowance and post-collection cap.

**What remains uncertain?** The sizes of the limits and any other component's deadlines are not specified in this passage. “No receiver deadline of its own” does not tell me that the entire operation has no timeout elsewhere.

## 42. Wire identity is exact, including presentation, but grants no execution compatibility

Source: [lines 341–345](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:341).

**What do I now believe?** The wire fingerprint includes every record identity, field tag, field name, kind, and public presentation rule. Even an added optional field or changed null/byte spelling changes it. Source locations, defaults, and comments are excluded. There is neither negotiation nor additive compatibility at this layer. Public build-contract admission happens during reservation before execution; passing the structural fingerprint check supplies no independent permission to execute or accept another public contract.

**What supports that belief?** Lines 341–345 explicitly define coverage, exclusions, exactness, and admission timing. Lines 249 and 313 already distinguish the fingerprint from the public identity and place it in the frame.

**What remains uncertain?** Nothing consequential for these identity distinctions. I do not interpret the exclusion of comments or defaults from this fingerprint as an exclusion from the separate shipped-input build identity in lines 8–12.

## 43. Public JSON presents bytes and admitted claims with separate semantic checks

Source: [lines 347–358](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:347).

**What do I now believe?** The public envelope is projected from typed records; byte fields remain bytes until presentation. Retained host reply bytes, compiled-profile bytecode, and rejected validator context are presented as base64. Fresh-read content and every digest—including SHA-256, code directory hash, and worker identity—are presented as lowercase hexadecimal. I would therefore not decode all public byte-related fields using one common textual encoding.

Unsupported or malformed input cannot become a semantic claim. Structural admission establishes declared shape only. Separate named validators check native operations, lifecycle, phase order, actor setup/equipment, owned endings, and extension custody before claims are projected. Conflicting observations can remain publishable while dependent claims are withheld. I infer that publishing contradictory facts is distinct from endorsing a conclusion based on them, and that a well-formed record alone does not justify such a conclusion.

**What supports that belief?** Lines 347–355 explicitly state the encodings, timing of presentation, division of validation responsibilities, and treatment of conflicts. The implications follow from that division and reinforce the lifecycle rule in line 165.

**What remains uncertain?** The complete validator rules and projected field shapes are not enumerated here. The passage clarifies categories of validation without proving the implementation of any validator.

## 44. Contract maintenance regenerates owned structures and checks release-derived stamps

Source: [lines 360–370](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:360).

**What do I now believe?** Maintainers edit schema-owned record declarations in `docs/porcelain.json`, regenerate with `tests/lib/python.sh docs/generate_porcelain.py`, review shape changes, update goldens, and keep normative definitions and verified examples current. There is no public schema counter. `tests/lib/python.sh docs/generate_contract_stamps.py` generates the stamps; `--check` checks freshness without writing when annotated history exists and reports the verification limit otherwise. `--check --require-history` demands complete derivation. Release preparation uses `--release vX.Y.Z` before committing/tagging, and ordinary `--check` on the tagged tree must reproduce the prepared table.

**What supports that belief?** Lines 362–370 explicitly give the maintenance responsibilities, commands, history qualification, and ordering. They identify the stamp command previously left unspecified in entry 5 and agree with the history limitations in lines 52–56.

**What remains uncertain?** No consequential uncertainty for the described maintenance sequence. I am recording these as maintainer responsibilities, not executing the commands in this examination.

## 45. Other format markers and test contexts retain narrower roles

Source: [lines 372–377](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:372).

**What do I now believe?** Registry, provenance, other infrastructure format markers, the validator NDJSON marker, and worker ABI identity remain distinct mechanisms with their own purposes. Historical captures preserve their bytes but are rejected if their producer is unsupported. Authored request templates do not carry an identity; the harness supplies the identity of the independently inspected candidate at submission. Constructed response tests provide explicit producer context. I infer that a reusable test template is not yet the identity-asserting submitted specimen required at the public boundary.

**What supports that belief?** Lines 372–377 explicitly state the separate roles, historical handling, and test-context rules. The template inference reconciles those rules with the required root assertion in line 63. The preservation rule is consistent with retaining unsupported bytes in line 147 without recovering semantic claims.

**What remains uncertain?** The candidate inspection procedure and narrower infrastructure-marker definitions are not given here. I do not infer a public identity bypass for test templates from their pre-submission form.

## 46. The jointly built host and worker use generated exact source identity

Source: [lines 379–390](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:379).

**What do I now believe?** The XPC host and its bundle-local `pw-probe-runner` share an exact SHA-256 source identity generated by `generate_worker_identity.py`. There is no worker ABI ordinal or compatibility negotiation. The build checks C, Swift, and test copies before compilation and again before signing, without writing those copies. After an input edit, regeneration is performed with `tests/lib/python.sh docs/generate_worker_identity.py`; its `--check` mode verifies without writing. Direct source-test builds regenerate in the same way. The build account owns the detailed sequence of checks and signatures. I infer that an ordinary build check is not an automatic repair of stale generated identity copies.

**What supports that belief?** Lines 382–390 explicitly state the pair, algorithm, generator, check stages, nonwriting behavior, regeneration procedure, and ownership of the build sequence. The no-automatic-repair inference follows from “never writes them.” Lines 171 and 372–373 already distinguished worker identity from the public build contract.

**What remains uncertain?** The covered input set and runtime handshake are not yet specified in this passage. I have no need to open the generator or build account to understand the regeneration responsibility.

## 47. Worker identity covers a conservative, mechanically discovered source scope

Source: [lines 392–404](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:392).

**What do I now believe?** The digest includes sorted repository-relative paths and file contents, each length-framed. Its scope is all `.c`, `.h`, and `.swift` files under `controller/tools/pw_probe_runner/` and `runner/Sources/`, plus the identity generator, its shared `source_identity.py` walker, `build.sh`, `meson.build`, `meson.options`, and `runner/Package.swift`. Generated identity-region bodies are excluded to avoid hashing their own generated values. New ordinary-file helpers beneath the covered directories are discovered automatically; a symlink there is refused.

The build reads Ninja's dependency log to check that compiler consumption for the worker and shim stays within those inputs, the selected SDK, and developer directory. This scope includes C wait/publication code, Swift release/collection code, orchestration, ABI declarations, and their host mirror. Even comments and unrelated changes inside the covered files change the identity; no maintainer judgment about semantic-version significance is needed. I therefore expect source edits outside the ABI declarations themselves to be capable of invalidating the exact pair identity.

**What supports that belief?** Lines 392–404 explicitly enumerate the hashing scope, exclusions, discovery/refusal, dependency-log boundary, and conservative consequences. The final expectation follows from the listed orchestration and publication code and the all-content hashing rule.

**What remains uncertain?** The exact length-framing byte encoding is not given. The passage includes SDK/developer inputs in the permitted compiler-consumption boundary, but does not say their contents are part of this source digest.

## 48. Bootstrap checks precede input, evidence, and attempt release, but the reported identity is host-selected

Source: [lines 406–414](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:406).

**What do I now believe?** The shared header places fixed bootstrap magic at byte 0 and 32 identity bytes at byte 64. The worker checks mapped-region size and those fields before reading policy input, publishing evidence, or using layout-dependent fields. Identity or magic mismatch exits with code 4 and publishes no ready/applied/done state. The magic also causes ordinal-era workers to refuse the header. The host checks identity before decoding worker evidence and before releasing attempts.

Nevertheless, these checks do not establish that a particular child validated the header. `runner_subprocess.worker_evidence.abi_identity` records the identity selected by the host and can exist without any worker publication. I therefore cannot cite that field alone as proof that the child reached or passed its bootstrap checks.

**What supports that belief?** Lines 406–414 explicitly specify offsets, check order, mismatch behavior, older-worker refusal, host checks, and the provenance limitation on the reported field. The final conclusion follows directly from the field existing without child publication.

**What remains uncertain?** The result of a mapped-region-size failure is not specified as precisely as identity/magic mismatch, and I do not assume it necessarily shares code 4. The full collection/release evidence chain required for `query_first` in line 159 has still not been enumerated by these identity checks alone.

## 49. Source equality is neither implementation proof nor authentication

Source: [lines 416–420](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:416).

**What do I now believe?** Equal host/worker identities establish agreement on the selected source bytes. They do not prove correct implementation, compiled layout agreement, identical compiler or SDK, binary authenticity, runtime behavior, or sandbox cause. Compiled C/Swift layout checks, signed artifact provenance, and lifecycle/order tests retain distinct responsibilities. The source hash is not a security authentication mechanism. I consequently cannot elevate a matching hash into proof that an observed failure was sandbox-caused, or that the executable was authentically produced from those sources.

**What supports that belief?** Lines 416–420 explicitly state the positive meaning, exclusions, separate checks, and authentication limitation. This qualifies the exact matching and broad source scope described in lines 382–414.

**What remains uncertain?** Nothing consequential for the hash's stated evidentiary limits. The implementations or results of the separate checks are outside this examination.

## 50. Internal memory identity does not subsume the external contracts

Source: [lines 422–427](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:422).

**What do I now believe?** This internal exact-match source identity applies to the jointly built host/worker pair. External runner XPC, JSON requests, public envelopes, and binary responses keep their own contract boundaries. Validator diagnostic JSON also has its own contract and is consumed independently of the memory interface. I infer that proving the pair's internal match neither replaces external public admission nor establishes admission of validator diagnostic material.

**What supports that belief?** Lines 422–425 explicitly limit the requirement and preserve the other boundaries. The inference follows from those boundaries together with the independent producer admission already specified in lines 147, 159, and 249.

**What remains uncertain?** The validator diagnostic contract's marker and exact validation rules are not defined here. Its independence is clear without opening another document.

## 51. Shape goldens record public JSON shape and do not replace semantic admission

Source: [lines 428–434](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:428).

**What do I now believe?** Shape goldens record public keys and their JSON types. Producer controls collect the current shape and write a candidate when it differs. Maintainers then review the difference, update the golden, and keep the normative definition and example current. Missing or mistyped required fields still fail semantic admission. There is no separate classifier that decides what version bump a shape change requires. I infer that accepting an updated shape golden cannot by itself make an incomplete or mistyped required field semantically admissible.

**What supports that belief?** Lines 430–434 explicitly describe the recorded shape, candidate/review workflow, ongoing admission requirement, and absence of a version-bump classifier. The final inference follows from the expressly retained semantic failure rule and the structure/semantics distinction in lines 352–355.

**What remains uncertain?** The concrete golden contents and producer-control procedures are not included. They are unnecessary to understand the respective responsibilities of shape recording and semantic admission.

## 52. The final build stamp distinguishes exact admission identity from descriptive metadata

Source: [lines 436–441](/Users/raccoon/Desktop/Security/PolicyWitness/docs/CONTRACT.md:436).

**What do I now believe?** Every envelope's build stamp contains `build.contract`, `build.describe`, `build.commit`, `build.version`, and `build.number`. Only `contract` is the exact admission identity; the other fields describe the build. A release contract can be produced only by an annotated release tag on a clean tree. I would not accept a matching version, build number, describe string, or commit as a substitute for a matching `build.contract`.

**What supports that belief?** Lines 438–441 explicitly name the five fields, assign their roles, and state the release prerequisite. The non-substitution conclusion follows from that role assignment. Lines 8–15 earlier gave the more specific clean-tree/exactly-one-tag rule, release/development spellings, and the compiled identity's other reporting locations; this final passage reinforces rather than replaces those details.

**What remains uncertain?** The formatting and derivation of the four descriptive fields are not specified here, but that does not make their non-admission role uncertain.
