# CONTRACT.md adjudication

A comparison of two reading journals of `docs/CONTRACT.md` with the contract
text and with the examination report. It judges the journal writer's
conclusions entry by entry, judges each recorded divergence between the two
readers, and sets the report's expectations about readers beside what the two
readers recorded. Sibling artifacts are named by path without links, under the
records link rule.

## Conventions

- `C:N` is a line of `docs/CONTRACT.md`. `G:N` is a line of
  `docs/PolicyWitness.md`, the guide. `J-nn`, `B-nn`, `L-nn`, `F-nn` and
  `D-nn` are the journal, baseline, report line-group, report finding and
  ledger divergence identifiers. `U-n` is the baseline reader's own label.
- "Close-out" is `records/contract/FRESH-ENCOUNTER-ADDENDA.md` for the
  journal and the closing section of
  `records/contract/ISOLATED-BASELINE-JOURNAL.md` for the baseline.
- Technical support is taken from the report as written. A † is carried over
  wherever the report marks its support as read by a delegated pass. No source
  code was opened and no test was run for this adjudication.
- Where an uncertainty is answered in a repository document, the location was
  found by searching documentation only (the guide, `LIMITS.md`,
  `REQUEST-GRAMMAR.md`, `EXTENSIONS.md`, `ARCHITECTURE.md`, the controller and
  runner READMEs, `tests/FAILURE-PROPAGATION-CONTRACT.md`). "Not found" means
  not found by that search, not that no document says it.
- Pairings come from the ledger's join table and are not re-derived.

**Classes.** *Supported interpretation*; *Mistaken reading*; *Invited
misunderstanding*; *Unsupported claim*; *Implementation discrepancy*;
*Unresolved*. A faithful restatement of lines whose report verdict is not
plain "Supported" is given a class from that verdict.

**Repository guidance.** The journal writer read the root guidance before the
contract. Its "Core ideas" list states five of the evidence principles the
contract also states. Where a journal inference matches one, the entry says
"also stated in repository guidance" and cites the baseline entry for the same
lines, since the baseline reader had no guidance.

**Result in brief.** No journal inference is classed as a mistaken reading.
Of 69 marked inferences, 67 are supported interpretations and two are invited
misunderstandings: `A-21` (b), which is also unresolved as to what the
contract sentence means, and `A-29` (a). One referral the reader relied on
does not land (`A-23`). Eighteen faithfully restated statements, in fifteen
entries, take a class from the report's verdict: nine implementation
discrepancies, five unsupported claims and four unresolved. One baseline
reading is classed mistaken, with a caveat (`A-D04`).

## Part 1: journal entries

### A-01 · J-01 · C:1-6

**Restatement.** Faithful. *Class:* supported interpretation for
`policy-witness run` and the XPC host (`L-01`). The restated denial of
"an admission bypass" repeats C:5-6; what lies outside it is `F-09`.

**Inferences.**

- (a) "I infer that otherwise understandable material can still be
  inadmissible because of identity." *Text:* for, C:5 "Admission is exact";
  later C:135 and C:159 give instances. *Report:* `L-01` supported; `L-08`;
  section 4.3 gives a live instance (identical sources, different contracts).
  *Class:* supported interpretation.

**Uncertainties.** None open; the close-out marks both answered (C:8-15,
C:255-284).

### A-02 · J-02 · C:8-15

**Restatement.** Faithful, with one change of word: "provenance rather than
compatibility keys" for "not admission keys" (C:15). Classes from `L-02`
("Partly supported") and `L-03`:

- "Other packaged builds identify themselves as `development:<sha256>`"
  (C:9): *implementation discrepancy* at one edge. A clean tree with two
  annotated release tags emits no identity (`F-11`).
- "Direct Cargo and SwiftPM builds are `unbound`" (C:12-13): *unresolved*.
  The report reads the Rust identity as taken from the build environment
  (`F-09`) and did not run it. Decided by the experiment in the report's
  section 9, second row.
- The remaining sentences: *supported interpretation* (`L-02`, `L-03`).

**Inferences.**

- (a) "they lead me to expect exact matching against the compiled contract
  identity, rather than accepting a matching commit or describe string as a
  substitute." *Text:* for, C:14-15 and C:439-440. *Report:* `L-03`
  supported; no Rust or Swift admission code compares describe or commit (†).
  *Class:* supported interpretation.

**Uncertainties.**

- Public identity input inventory and hash serialization (open): not found in
  documentation. The report's section 4.3 states the scope and framing from
  the generator. The contract names no place for it (`F-11`).
- Refusal shape for an `unbound` producer (open): not found in documentation.
  The report gives it under `L-08`: both sides refuse with
  `unsupported_contract` and `expected_contract: "unbound"` (†).

### A-03 · J-03 · C:17-20

**Restatement.** Faithful. *Class:* supported interpretation; the procedure's
dependence on the stamp table is `F-03` (`L-04`).

**Inferences.**

- (a) "I infer that updating the app alone does not make a previously
  installed external runner suitable for the new contract." *Text:* for,
  C:19-20; C:249 and C:296 later confirm. *Report:* `L-31`, `L-37` supported
  in code; live verification is opt-in (`F-04`). *Class:* supported
  interpretation.

**Uncertainties.**

- Exact diagnostic for an old external runner (open): another repository
  document the contract does not point to, in part. The guide's `transport`
  and `refusals` regions give the client-side vocabulary (G:1511-1516,
  G:2075-2081). The registry refusal text is given only by the report
  (`L-04`).

### A-04 · J-04 · C:22-50

**Restatement.** Faithful. *Class:* supported interpretation (`L-05`, `L-06`).

**Inferences.**

- (a) "I read these as their displayed last-change stamps, not as thirteen
  independently selectable protocol versions or proof of the running build's
  identity." *Text:* for, C:31-32 and C:14-15. *Report:* `L-05`, `L-06`
  supported; no product source mentions stamps. *Class:* supported
  interpretation.

**Uncertainties.**

- Concrete goldens (deferred): a document the contract names. The manifest at
  C:24 lists each golden's path (report section 4.2).
- Reservation and client allowances (deferred): a document the contract
  names, `LIMITS.md`, though not at these lines.

### A-05 · J-05 · C:52-56

**Restatement.** Faithful. *Class:* supported interpretation (`L-07`).

**Inferences.**

- (a) "I would not treat an ordinary successful check without history as
  establishing the stamps' historical derivation." *Text:* for, C:52-54.
  *Report:* `L-07` supported. *Class:* supported interpretation.

**Uncertainties.**

- "The two tables" (open): another repository document the contract does not
  point to. The second table is at G:2630-2646 (`L-07`, `F-12`).

### A-06 · J-06 · C:58-63

**Restatement.** Faithful. *Class:* supported interpretation (`L-08`).

**Inferences.**

- (a) "I expect the contract refusal and no client startup, rather than a
  selector error or an attempted run." *Text:* for, the example at C:63.
  *Report:* `L-08` supported. The exact combination is verified by a unit
  test with injected dependencies (†); an invalid selector given as a
  command-line flag is reported first (†), which the journal's expectation
  does not concern. *Class:* supported interpretation.

**Uncertainties.**

- Selector forms (deferred): a document the contract names (C:77).

### A-07 · J-07 · C:65-75

**Restatement.** Faithful. *Class:* supported interpretation. `L-09` is
"Partly supported" because the list of null-rejecting fields is incomplete
(`F-08`); the journal restates the list and, in (b), declines to treat it as
complete.

**Inferences.**

- (a) "Together with line 63, I expect these structural errors to be
  considered after contract admission." *Text:* for, C:63 "Unknown fields are
  refused after this gate". *Report:* `L-08`; the host gate precedes the
  unknown-key walk and field decoding. *Class:* supported interpretation.
- (b) "'Generally' does not establish absence-equivalence for every other
  optional field." *Text:* for, C:75. *Report:* `F-08` confirms a fifth class
  that rejects explicit null. *Class:* supported interpretation.

**Uncertainties.**

- Exhaustive accepted-field inventory (open): another repository document the
  contract does not point to. The guide's `request_form`, `request_admission`
  and actor regions (G:169-613) hold the field meanings; C:117 says "the
  guide" without a link (`F-01`, `F-12`).
- Omission defaults for the null-rejecting fields (open): G:295 for
  `equipment`; `REQUEST-GRAMMAR.md:166` for `required_entitlements`. The
  contract names `REQUEST-GRAMMAR.md` as a lesson, not as the place for
  defaults. The other two defaults were not found.
- Complete null-versus-absence rules (open): not found. `F-08` adds one
  exception from source.

### A-08 · J-08 · C:77-85

**Restatement.** Faithful. "A direct XPC caller must not supply those
runner-selection fields" turns C:83 into a duty on the caller with the same
content (`A-D04`). Classes from `L-10`:

- "their resolved meaning remains in runner provenance" (C:82-83):
  *implementation discrepancy* in part. Provenance records the selected
  target and read-backs, not the selector's entitlement demand, and is null
  when selection fails (†).
- The rest: *supported interpretation* (†).

**Inferences.**

- (a) "I infer that controller-accepted input and direct-XPC-accepted input
  are deliberately different at these preprocessing fields." *Text:* for,
  C:82-85. *Report:* `L-10` supported (†). *Class:* supported interpretation.

**Uncertainties.**

- Selector vocabulary (deferred): a document the contract names (C:77).
- Augment catalog and splice order (open): the catalog is in another
  repository document the contract does not point to,
  `runner/augments/README.md`. The splice order was not found.

### A-09 · J-09 · C:87-98

**Restatement.** Faithful. *Class:* supported interpretation (`L-11`).

**Inferences.**

- (a) "I expect an explicit `prediction_unavailable` observation and normal
  execution of a supported attempt." *Text:* for, C:95-96. *Report:* `L-11`
  supported; a default corpus row covers it (†). *Class:* supported
  interpretation.
- (b) "I cannot assume they describe identical operations or targets merely
  because they share a step." *Text:* for, C:98. *Report:* `L-11`; admission
  makes no comparison of scopes (†). *Class:* supported interpretation.
  See `A-D05`.
- (c) "it does not separately restate the timing of every other meaning check
  listed here." *Text:* for; C:87-88 places only unknown pairs and filter
  kinds before worker or validator creation. *Report:* `L-11` says all
  meaning checks run in admission, before any child (†). *Class:* supported
  interpretation. The reader's reservation is correct about the text and is
  answered by the report, not by the contract.

**Uncertainties.**

- Nonce validity (open): another repository document the contract does not
  point to. G:594 and G:639 give "32 lowercase hexadecimal characters".
- Attempt and filter vocabularies; prediction-excluded pairs (open): another
  repository document the contract does not point to, the guide's
  `operations` region (G:2111-2284; `L-17`).
- Whether every meaning check precedes worker and validator creation (open):
  not in the contract. The report answers it (`L-11`, †); G:2055 says
  `bad_request` is "rejected before any worker spawn".

### A-10 · J-10 · C:100-106

**Restatement.** Faithful. Classes from `L-12`:

- "Every shipped-source change changes a development contract" (C:100):
  *supported interpretation* for tracked scoped sources (`F-11`); the journal
  does not extend it to build variants (`F-10`).
- "verified examples" (C:104), repeated without comment: *unsupported claim*
  for the word "verified". `F-05` finds six of thirteen examples verified
  only on constructed data or by opt-in cases and one not verified as
  written.

**Inferences.**

- (a) "I do not interpret it as promising that every implementation fix
  changes the request grammar; it requires acceptance of the build identity
  regardless." *Text:* for, C:100-103. *Report:* `L-12`. *Class:* supported
  interpretation.

**Uncertainties.** None recorded.

### A-11 · J-11 · C:108-114

**Restatement.** One drift. Journal: "A syntactically and semantically valid
request can still exceed a runtime admission limit". Contract, C:109: "a
structurally valid plan can exceed the worker's step capacity". The journal's
version is broader. It is consistent with C:108 ("separate from this syntax
and meaning") and is not contradicted, but C:287-288 later puts capacity
checks before meaning checks, so a capacity-refused request has not been
checked for meaning. The close-out records this refinement. *Class:* supported
interpretation (`L-13`).

**Inferences.**

- (a) "I understand capacity as part of the behavior an author must
  reconsider, rather than only a parser detail." *Text:* for, C:111-112 with
  C:100-103. *Report:* `L-13` supported. Section 4.2 adds that only five
  reservation and client limits enter any stamp, so a capacity change need
  not move a row (`F-03`). *Class:* supported interpretation.

**Uncertainties.**

- Numerical limits (deferred): a document the contract names (C:108).

### A-12 · J-12 · C:116-124

**Restatement.** Faithful. *Class:* supported interpretation (`L-14`, `L-15`).

**Inferences.**

- (a) "I take that as the stated relationship of the materials, not as
  verification I have performed." *Text:* for, C:121-122. *Report:* `L-15`
  supported (†). *Class:* supported interpretation.

**Uncertainties.** None recorded. See `A-D06` and `A-D07`.

### A-13 · J-13 · C:126-130

**Restatement.** Faithful. *Class:* supported interpretation, on source
reading (`L-16`, "Supported in code"). No test asserts "leaves the input file
unchanged" for the missing-augment case (`F-05`, †).

**Inferences.**

- (a) "I infer that augmentation does not require rewriting the specimen on
  disk." *Text:* for, C:129 "in memory" and C:19. *Report:* `L-16`, `L-04`;
  the run path only reads the file. *Class:* supported interpretation.

**Uncertainties.**

- Import resolution and hash coverage (open): another repository document the
  contract does not point to, the guide's `dossier` region (G:1572-1651). The
  report adds that hashes cover `sbpl_source` strings only (`L-16`, †).
- When and how the input is held (open): not in the contract. The report
  answers it: read once into memory and serialized once (`L-20`, †).

### A-14 · J-14 · C:132-136

**Restatement.** Faithful. *Class:* supported interpretation (`L-17`).

**Inferences.**

- (a) "I must not interpret a prediction as proof of what the attempted
  operation will do." *Text:* for, C:135. *Report:* `L-17` supported; the
  step record has no agreement field (†). *Class:* supported interpretation.
  Also stated in repository guidance ("No dishonest attribution"); `B-10`
  records the same belief from the text alone.
- (b) "I expect an admitted attempt to have potentially destructive file
  effects; a same-shape request with a foreign build assertion must be
  stopped before that operation." *Text:* for, the example at C:135.
  *Report:* `L-17`; the truncation has a default signed test, the
  foreign-assertion half only an opt-in case (`F-05`, †). *Class:* supported
  interpretation.

**Uncertainties.**

- Complete action and filter lists (open): the guide's `operations` region,
  which the contract does not point to.
- Observation record shapes (deferred): a document the contract names,
  `porcelain.json`.

### A-15 · J-15 · C:138-142

**Restatement.** Faithful. *Class:* supported interpretation (`L-18`). "Every
sandboxed process is fresh" is also stated in repository guidance ("One-way
sandbox per process"); `B-11` records it from the text alone.

**Inferences.**

- (a) "I infer that returning to an existing actor in another phase does not
  mean applying its policy again." *Text:* for, C:141 "an actor applies its
  policy once" with "Phases name the active actor". *Report:* `L-18`
  supported (†). *Class:* supported interpretation.

**Uncertainties.**

- Request encodings for actors, equipment, transitions and extension
  operations (open): another repository document the contract does not point
  to, the guide's `actors_phases` and `actors_extensions` regions
  (G:207-488).
- Remaining response structures (deferred): `porcelain.json`.
- Actor-lifetime overlap and scheduling rules (open): not searched beyond the
  regions above; not decided here.

### A-16 · J-16 · C:144-148

**Restatement.** Faithful. Classes from `L-19` ("Supported, with one
precision"):

- "Unsupported received bytes remain available": *implementation discrepancy*
  in part. Exact for binary frames; a helper envelope that parses is kept
  re-serialized, and unparsed helper output as capped text (†).
- The rest: *supported interpretation*.

**Inferences.**

- (a) "I expect a foreign helper claiming compilation to be unable to produce
  a successful policy-check status." *Text:* for, the example at C:147.
  *Report:* `L-19` supported, on constructed data only (`F-05`, †). *Class:*
  supported interpretation.

**Uncertainties.**

- `kind` and `result` vocabularies (open): another repository document the
  contract does not point to, the guide's `refusals` region (G:2015-2107),
  which itself points to the controller README.
- Fields exposing retained bytes (deferred): `porcelain.json`; G:1541-1550
  describes them.
- Status produced by the foreign-helper example (open): another repository
  document the contract does not point to. G:756 and
  `tests/FAILURE-PROPAGATION-CONTRACT.md:1142` name `invalid_reply`.

### A-17 · J-17 · C:150-154

**Restatement.** Faithful. *Class:* supported interpretation on source reading
(`L-20`, "Supported in code"). For the built-in runner the "observed binary
inventory" is four nulls (†).

**Inferences.**

- (a) "I infer that a later on-disk edit must not make the fallback compile a
  different specimen from the one submitted." *Text:* for, C:153. *Report:*
  `L-20`; tested only with injected dependencies (`F-05`, `F-18`, †).
  *Class:* supported interpretation.

**Uncertainties.**

- Holding mechanism (open): as in `A-13`.
- Binary-inventory observation method (open): the guide's `dossier` region,
  which the contract does not point to.
- Representation of unknown observations (deferred): `porcelain.json`.

### A-18 · J-18 · C:156-160

**Restatement.** Faithful. *Class:* supported interpretation (`L-21`). The
example's literal shape, a foreign reply inside a current envelope, is one
only the harness reader meets (†). "Admission" at C:159 is producer identity
only (`F-07`); the journal does not say otherwise.

**Inferences.**

- (a) "I cannot treat it as a label justified merely by a query and attempt
  appearing in that order in a report." *Text:* for, C:159. *Report:* `L-21`
  supported; the label is gated in worker, host, controller and harness (†).
  *Class:* supported interpretation. Also stated in repository guidance
  ("Predictions precede attempts"); `B-14` restates the requirement without
  drawing this caution and leaves `U26` open.

The restated limit on sandbox-cause claims is also stated in repository
guidance ("No dishonest attribution"); `B-14` has it from the text alone.

**Uncertainties.**

- The complete collection and release chain (open): another repository
  document the contract does not point to. G:141 and G:1377 state it;
  `WORKER.md:425` points to its definition.
- Response fields (deferred): `porcelain.json`.
- Exact value when the chain is incomplete (deferred): G:1377 gives
  `unestablished`.

### A-19 · J-19 · C:162-166

**Restatement.** Faithful. *Class:* supported interpretation (`L-22`).

**Inferences.**

- (a) "I therefore need to distinguish requesting an operation, receiving a
  successful return, observing an effect, and confirming a process lifecycle
  event." *Text:* for, C:165. *Report:* `L-22` supported in producer and
  controller (†). *Class:* supported interpretation. Also stated in
  repository guidance ("Witness over interpretation"); `B-15` records the
  same distinctions from the text alone.

**Uncertainties.**

- Lifecycle field layout (deferred): `porcelain.json`.
- Mapping from native observations to dispositions (open): another repository
  document the contract does not point to, the guide's `envelope` region
  (G:1254-1285).

### A-20 · J-20 · C:168-171

**Restatement.** Faithful. *Class:* supported interpretation (`L-23`,
"Supported, with qualifications").

**Inferences.**

- (a) "I cannot substitute one for the other." *Text:* for, C:171; C:422-425
  later. *Report:* `L-23` and section 4.4: separate in computation and use,
  overlapping in inputs (†). *Class:* supported interpretation.
- (b) "rather than merely adding a warning while allowing the same claim."
  *Text:* for, the example at C:171. *Report:* `L-23`; a refused row refuses
  the whole run; verified at the binder and at install, not by a signed run
  (`F-05`, †). *Class:* supported interpretation.

**Uncertainties.**

- Sealing mechanism and hash coverage (open): another repository document the
  contract does not point to. G:374 and `EXTENSIONS.md:13` describe the
  service validating its seal and its sealed inventory.
- Full result of a hash mismatch (open): the report gives it (`L-23`, †):
  reason `worker_identity_mismatch`, reported as the
  `equipment/equipment_binding_refused` preparation failure. Not found in
  documentation.

### A-21 · J-21 · C:173-181

**Restatement.** Two drifts.

- Journal: "An acquired decision does not imply publication of another cell"
  and, in its uncertainty paragraph, "it is not evidence of another cell's
  publication". Contract, C:180-181: "An acquired decision does not publish
  another cell". The journal turns a statement about what a decision does
  into a statement about what a decision shows. See (b) and `A-D12`.
- Journal: "`authority_setup.workers` contains cells retaining primary setup,
  independent cleanup, and native-capability observations". Contract,
  C:178-180, attributes those observations to the host scopes and the worker
  cells together. Narrower.

*Class of the restated denials* ("neither a declaration reply nor a singular
worker projection"): supported interpretation (`L-24`, †); the terms are
undefined (`F-12`).

**Inferences.**

- (a) "I infer that readers must retain these separate evidence locations
  rather than collapsing the run into one worker's status." *Text:* for,
  C:176-181. *Report:* `L-24`, first three statements supported (†). *Class:*
  supported interpretation.
- (b) "The passage does establish that it is not evidence of another cell's
  publication." *Text:* not decidable. C:180-181 does not define "acquired
  decision" and its verb is "publish", not "show". *Report:* `L-24` not
  determined; `F-15`: the term is defined nowhere, and a temporal reading is
  contradicted (†). *Class:* invited misunderstanding as a reading, by an
  undefined term; *unresolved* as to what the sentence means. Decided by a
  definition of "acquired decision" from the maintainer.

**Uncertainties.**

- Scope and cell record shapes (deferred): `porcelain.json`.
- State vocabulary; meaning of "acquired decision" (open): not found
  (`F-12`, `F-15`, †).

### A-22 · J-22 · C:183-191

**Restatement.** Faithful. No marked inference. Classes from `L-25`:

- Override rows "cannot establish packaged selection" (C:188-190):
  *unsupported claim*. The row shape is enforced; no check corresponds to the
  sentence (`F-15`, †).
- The structural rules: *supported interpretation* (†).

**Uncertainties.**

- Row shapes (deferred): `porcelain.json`.
- How static and live read-backs are associated (open): not found in
  documentation.
- Why an actor has no binding row (open): not found.

### A-23 · J-23 · C:191-196

**Restatement.** Faithful. *Class:* supported interpretation (`L-25`, †).

**Inferences.**

- (a) "I do not take mere key presence or a nonboolean truthy value as
  satisfying this criterion." *Text:* for, C:192 "boolean true keys".
  *Report:* `L-25` supported (†). *Class:* supported interpretation.
- (b) "I do not infer that earlier facts disappear or that every actor was
  necessarily unlaunched when the failure occurred." *Text:* for, C:194-196.
  *Report:* `L-25`; covered at unit level, not on the signed product
  (`F-18`, †). *Class:* supported interpretation.

**Uncertainties.**

- Runtime-inspection failure marker (open): not found in documentation.
- Extent of runtime inspection (open): not found.
- "Reserve geometry" (taken as deferred to `LIMITS.md`): the referral does
  not land. The report says the phrase does not occur there (`L-25`, †). The
  reader's belief that `LIMITS.md` defines it is an *invited
  misunderstanding*, led by the referral at C:193.

### A-24 · J-24 · C:198-202

**Restatement.** Faithful. Classes from `L-26` ("Supported, read as 'a reply
violating this is flagged'"):

- "empty observation arrays" (C:200): *implementation discrepancy* in
  wording. Several arrays are required empty; `actors` is required nonempty
  and the binding tables are normally populated (`F-15`).
- The closed pair set and its side conditions: *supported interpretation*.
  The journal does not say what happens to a reply that violates them
  (`F-07`).

**Inferences.**

- (a) "I infer that runtime inspection failure cannot be relabeled
  preparation failure simply because it prevents later work." *Text:* for,
  C:195-196 with C:198. *Report:* `L-25`, `L-26` (†). *Class:* supported
  interpretation.

**Uncertainties.**

- "Complete observation partition" (open): another repository document the
  contract does not point to. `tests/FAILURE-PROPAGATION-CONTRACT.md:190`
  uses the term for the step and event arrays.
- Bounds on retained identities (deferred): a document the contract names
  (C:193).

### A-25 · J-25 · C:204-210

**Restatement.** Faithful. *Class:* supported interpretation (`L-27`, †).

**Inferences.**

- (a) "'observed' does not itself mean application succeeded." *Text:* for,
  C:207-208. *Report:* `L-27` supported (†). *Class:* supported
  interpretation.
- (b) "I cannot infer nonattempt from an arbitrary terminal condition."
  *Text:* for, C:206-210. *Report:* `L-27` (†). *Class:* supported
  interpretation.

**Uncertainties.**

- Complete basis vocabulary (open): not found in documentation. The report
  says ten of the eleven basis strings appear in no document (`L-27`, †).
- Eligible terminal worker branches (open): not found (`F-12`, †).

### A-26 · J-26 · C:212-220

**Restatement.** Faithful to the wording, and the wording is the issue.
Journal: "The ordinals belong to the source actor process; they are not a
global process counter." Contract, C:216-217: "These ordinals are local to
the source actor process". *Class:* implementation discrepancy in wording
(`F-15`, †). Each process has its own counter, so a dependent phase's
activation ordinal is not in the source's sequence. Whether the journal
writer includes that ordinal is listed under unclear items.

**Inferences.**

- (a) "I therefore cannot compare unrelated actors' ordinal values as if they
  established a global execution order." *Text:* for, C:216-217. *Report:*
  `L-28`; `F-15` (†). *Class:* supported interpretation. This is the correct
  consequence under either reading of the sentence.

**Uncertainties.**

- Gate result states and capture-stage values (open): not found in
  documentation. The report gives them from source (`L-28`, †).

### A-27 · J-27 · C:220-228

**Restatement.** Faithful. *Class:* supported interpretation (`L-28`, †).

**Inferences.**

- (a) "Abnormal natural reap can satisfy termination; normal exit is not
  required by this passage." *Text:* for, C:227. *Report:* `L-28`; a default
  signed case asserts a satisfied gate with a nonzero exit (†). *Class:*
  supported interpretation.

**Uncertainties.**

- Numerical allowance (deferred): a document the contract names (C:226). The
  report notes the row has a different name there (`F-12`, †).
- Ownership and departure flag meanings (open): in part in another repository
  document the contract does not point to,
  `tests/FAILURE-PROPAGATION-CONTRACT.md` (†).

### A-28 · J-28 · C:230-238

**Restatement.** Faithful. *Class:* supported interpretation (`L-29`, †).

**Inferences.**

- (a) "I infer that later cleanup evidence is not a retroactive authorization
  for the dependent phase." *Text:* for, C:234-236 with C:228. *Report:*
  `L-29` supported, with a default signed assertion (†). *Class:* supported
  interpretation.

**Uncertainties.**

- Clock-failure result shape (deferred): `porcelain.json`.

### A-29 · J-29 · C:240-244

**Restatement.** Faithful: "a wrong nonce invalidates the receipt even inside
a current reply" for "refuses the receipt". Classes from `L-30` ("Partly
supported"):

- The consistency sentence and the wrong-nonce example (C:243):
  *implementation discrepancy* as a statement about readers. The controller
  checks status, producer and stage only; the host checks the rest before
  publication and reports `unavailable` (`F-06`). The report's reading that a
  current reply with a different nonce would be admitted is from source and
  awaits the experiment in its section 9, first row.
- "A detached receipt supplies no producer context": *unsupported claim*. No
  reader takes a detached receipt (`L-30`, †).
- Inherited context and no schema marker: *supported interpretation*.

**Inferences.**

- (a) "I infer that host identity admission is necessary but insufficient for
  accepting the receipt's content." *Text:* for as written, C:243.
  *Report:* `F-06`: beyond host admission, a reader checks only status,
  producer and stage. *Class:* invited misunderstanding, if "accepting"
  means a check applied to a received reply. The feature: "refuses the
  receipt even inside a current reply", in a document about admission. The
  correcting text is in the guide (G:648-652), which the contract does not
  point to. The sense of "accepting" is listed under unclear items.

**Uncertainties.**

- Receipt status and stage vocabularies (open): the guide's `profile` region
  (G:635-674), which the contract does not point to.
- Nonce format (open): G:594, G:639.
- Receipt digest algorithm (open): a document the contract names; the field
  names in `porcelain.json` carry it (report section 5).
- Complete consistency relationships (open): G:648-652 states the host's
  requirement; `F-06` states what a reader checks.

### A-30 · J-30 · C:246-250

**Restatement.** Faithful. *Class:* supported interpretation on source
reading (`L-31`, "Supported in code"). The example's live control is opt-in
and uses an instrumented host (`F-05`, †).

**Inferences.**

- (a) "The rule does not establish which, if any, pre-invocation failures
  permit another attempt; it specifically denies replay authority after
  uncertainty." *Text:* for, C:249. *Report:* `L-31`: acquisition may retry
  before submission; nothing retries after it (†). *Class:* supported
  interpretation.

**Uncertainties.**

- Reservation and submission sequence (open): another repository document the
  contract does not point to, the guide's `transport` region (G:1523-1539).
- Capture structure for an uncertain invocation (deferred): `porcelain.json`;
  G:1515-1516 gives `invoked`, `not_invoked`, `unknown`.
- Which pre-invocation failures permit another attempt (open): a document the
  contract names, though not at these lines. `LIMITS.md:151-152` gives the
  acquisition attempt and retry-delay rows; G:2075-2082 describes them.

### A-31 · J-31 · C:252-255

**Restatement.** Faithful. *Class:* supported interpretation (`L-32`).

**Inferences.**

- (a) "I infer that receiving reply-like bytes does not override a failed
  delivery result." *Text:* for, C:255 "Delivery failure takes precedence
  over interpreting a reply". *Report:* `L-32` supported, on constructed
  captures (†). *Class:* supported interpretation.

**Uncertainties.**

- Delivery-failure representation and vocabulary (deferred and open): another
  repository document the contract does not point to. G:1552-1559 describes
  `runner_client.request_delivery` and the `tool_error` it produces.

### A-32 · J-32 · C:256-264

**Restatement.** Faithful. *Class:* supported interpretation (`L-33`).

**Inferences.**

- (a) "Optional diagnostic presence is clear and does not itself imply any
  compatibility exception to the identity rules in lines 100–106." *Text:*
  for, C:105-106. *Report:* `L-33` supported. *Class:* supported
  interpretation. See `A-D13`.

**Uncertainties.**

- Exit statuses for tool and execution failures (open): another repository
  document the contract does not point to. G:1557 gives exit 2 for
  `tool_error`; the report adds that transport and reply refusals exit 1
  (`L-33`, †).

### A-33 · J-33 · C:266-271

**Restatement.** Faithful. *Class:* supported interpretation (`L-34`).

**Inferences.**

- (a) "I should not interpret a shortened path as the complete location."
  *Text:* for, C:268-269. *Report:* `L-34` supported. *Class:* supported
  interpretation.

**Uncertainties.**

- Representation for refused parameter keys (open): a document the contract
  names. `LIMITS.md:98` says a refused key "is identified by field and byte
  count and is never echoed"; G:2061-2069 says the same at more length.

### A-34 · J-34 · C:273-284

**Restatement.** Faithful. *Class:* supported interpretation for the listed
codes (`L-35`, †). The journal neither says the table is the whole vocabulary
nor that it is partial (`F-08`).

**Inferences.**

- (a) "I infer that dependency validation considers the source's final visit,
  not merely whether that actor appeared at some earlier point." *Text:* for,
  C:281. *Report:* `L-35`; the one emitting site matches the row (†).
  *Class:* supported interpretation.
- (b) "lead me to expect absent, null, mistyped, and foreign contract
  assertions to remain distinguishable, with `expected_contract` supplied".
  *Text:* for, C:63, C:255, C:266-267, C:276-277. *Report:* `L-08`, four
  codes in controller and host. *Class:* supported interpretation.

**Uncertainties.**

- Native-string admission restrictions (deferred): a document the contract
  names, `LIMITS.md`; G:2060 adds that native C-string fields reject an
  embedded NUL.
- Complete mapping from malformed input to code (open): not found. `F-08`
  lists 29 emitted codes the table omits.

### A-35 · J-35 · C:286-291

**Restatement.** Faithful. Classes from `L-36`:

- "Capacity checks precede meaning checks" (C:287-288): *implementation
  discrepancy* for rules enforced during decoding, such as the plan-form rule
  (`F-08`). The close-out records the sentence as an answer.
- The rest: *supported interpretation*.

**Inferences.**

- (a) "'refused before children' does not mean no service process could have
  started." *Text:* for, C:286-287. *Report:* `L-36`, `F-20`. *Class:*
  supported interpretation.
- (b) "I should not expect an exhaustive defect report or infer success from
  an unfamiliar diagnostic." *Text:* for, C:288-289. *Report:* `L-36`.
  *Class:* supported interpretation.

**Uncertainties.**

- Ordering within the capacity and meaning stages (open): not found. `F-08`
  shows the two-stage picture is itself incomplete.

### A-36 · J-36 · C:293-296

**Restatement.** Faithful. *Class:* supported interpretation on source
reading (`L-37`, "Supported in code"); live verification is opt-in (`F-04`).

**Inferences.**

- (a) "I infer that identity rejection does not prevent legitimate cleanup of
  old records." *Text:* for, C:296. *Report:* `L-37` (†). *Class:* supported
  interpretation.
- (b) "I do not infer ownership merely from a matching identity or the
  ability to list a record." *Text:* for, C:297. *Report:* `L-37`. *Class:*
  supported interpretation.

**Uncertainties.**

- Ownership rules; what establishes observed absence (open): another
  repository document the contract does not point to, the guide's
  `installation` region (G:2339-2622). C:296 says "the existing ownership
  rules" without a reference (`F-12`).

### A-37 · J-37 · C:297-298

**Restatement.** Faithful, with one choice. Journal: "publication itself
establishes neither execution compatibility nor ownership". Contract, C:297:
"It never establishes execution compatibility or ownership". The journal
resolves "It" to publication, as `B-27` does; the report says the referent is
ambiguous and the statement holds on either reading (`F-16`, †). Classes from
`L-37`:

- "survive unrelated writes": *unresolved*. One command may drop unknown keys
  inside signature and entitlement records (`F-16`, †, an inference). Decided
  by the experiment in the report's section 9, fifth row.
- "lossless read-back before atomic replacement": *supported
  interpretation*, in a narrower sense than the words suggest (`F-16`).
- The rest: *supported interpretation*.

**Inferences.**

- (a) "I infer that retaining an unknown value and trusting it for execution
  are separate operations." *Text:* for, C:296-297. *Report:* `L-37` (†).
  *Class:* supported interpretation.
- (b) "Historical storage-shape acceptance does not lead me to expect
  historical public-contract admission or translation, which lines 3–6
  forbid." *Text:* for, C:5-6 and C:372-374. *Report:* `L-37`. *Class:*
  supported interpretation. See `A-D15`.

**Uncertainties.**

- Retired kind aliases (open): not found in documentation;
  `ARCHITECTURE.md:468` mentions them without listing them.
- Read-back failure result (open): not found in documentation; `F-16`
  describes the check.

### A-38 · J-38 · C:300-311

**Restatement.** One drift, toward caution. Journal: "I expect the three
structural definitions to agree because they derive from one schema."
Contract, C:307-308: "they cannot disagree with each other about structure".
Weaker than the contract. *Class:* supported interpretation (`L-38`).

**Inferences.**

- (a) The expectation quoted above. *Text:* for, C:307-308. *Report:*
  `L-38`, `F-14`: the three agree today; "cannot" is stronger than the code,
  because one Swift writer and two sets of tags are hand-written (†).
  *Class:* supported interpretation of the weaker form the journal holds.
- (b) "I do not read shared structure as a promise that the separate readers
  independently validate the schema or establish identical semantics by
  generation alone." *Text:* for, C:308-309. *Report:* `L-38`. *Class:*
  supported interpretation.

**Uncertainties.**

- Complete schema (deferred): `porcelain.json`.
- Implementation of semantic admission (open): not in any document the
  contract names. See `A-D16`.

### A-39 · J-39 · C:313-325

**Restatement.** Faithful. *Class:* supported interpretation (`L-39`).

**Inferences.**

- (a) "I infer that a structurally decodable text value need not be an
  admissible state or valid actor association." *Text:* for, C:319-322.
  *Report:* `L-39` supported in full (†). *Class:* supported interpretation.
- (b) "I do not generalize that statement to every numeric element without
  further text." *Text:* for; C:314 gives byte order for the payload length
  only. *Report:* not covered. `L-39` says "Supported in full" and does not
  note that the passage is silent on the byte order of integers, record
  identities, tags and counts, and on boolean encoding. *Class:* supported
  interpretation. Listed under report corrections.

**Uncertainties.**

- Boolean encoding; byte order of other numeric elements (deferred): a source
  file the contract names (C:330).
- Record identities, tags and cases (deferred): `porcelain.json`.

### A-40 · J-40 · C:326-334

**Restatement.** Faithful. No marked inference. *Class:* supported
interpretation on source reading (`L-39`; `L-40`, "Supported in code for both
readers").

**Uncertainties.**

- Numerical budgets (deferred): a document the contract names, `LIMITS.md`.
- Logical-storage charges (deferred): a source file the contract names.

### A-41 · J-41 · C:334-339

**Restatement.** Faithful. Classes from `L-40`:

- "arrives truncated and is refused as `runner_reply_truncated`":
  *unsupported claim* as to evidence. Implemented; no test produces the
  outcome (`F-18`). "Arrives truncated" is client retention after full
  receipt (†).
- The rest: *supported interpretation* (†).

**Inferences.**

- (a) "satisfying the writer's frame limit therefore does not guarantee
  client acceptance." *Text:* for, C:334-337. *Report:* `L-40` (†). *Class:*
  supported interpretation.
- (b) "I consequently cannot treat the retention cap as a bound on how much
  client output must first be collected, or infer a receiver timeout from
  this cap." *Text:* for, C:337-339. *Report:* `L-40` (†). *Class:*
  supported interpretation.
- (c) "'No receiver deadline of its own' does not tell me that the entire
  operation has no timeout elsewhere." *Text:* for, C:338-339. *Report:*
  `L-40`; the client has its own deadline (†). *Class:* supported
  interpretation.

**Uncertainties.**

- Sizes of the limits (deferred): `LIMITS.md`.
- Complete deadline picture (open): a document the contract names, though not
  for this. `LIMITS.md` holds the overall client allowance that C:27-28
  mentions; G:2075-2095 describes the timeout layers.

### A-42 · J-42 · C:341-345

**Restatement.** Faithful. *Class:* supported interpretation (`L-41`).

**Inferences.**

- (a) "I do not interpret the exclusion of comments or defaults from this
  fingerprint as an exclusion from the separate shipped-input build identity
  in lines 8–12." *Text:* for, C:9-10. *Report:* section 4.3; the public
  digest covers whole file contents. *Class:* supported interpretation.

**Uncertainties.** None recorded.

### A-43 · J-43 · C:347-358

**Restatement.** Faithful. *Class:* supported interpretation (`L-42`).

**Inferences.**

- (a) "I would therefore not decode all public byte-related fields using one
  common textual encoding." *Text:* for, C:347-351. *Report:* `L-42`
  supported (†). *Class:* supported interpretation.
- (b) "I infer that publishing contradictory facts is distinct from endorsing
  a conclusion based on them, and that a well-formed record alone does not
  justify such a conclusion." *Text:* for, C:351-355. *Report:* `L-42`,
  `F-07`. *Class:* supported interpretation. The journal ties this to C:165
  and not to the equipment region's "requires" sentences.

**Uncertainties.**

- Complete validator rules (open): not in any document the contract names.
- Projected field shapes (deferred): `porcelain.json`.

### A-44 · J-44 · C:360-370

**Restatement.** Faithful. No marked inference; no uncertainty. *Class:*
supported interpretation (`L-43`, "The commands match the generator").
"Verified examples" is repeated as at `A-10`.

### A-45 · J-45 · C:372-377

**Restatement.** Faithful. Classes from `L-43`:

- "Historical captures preserve their bytes but are rejected if their
  producer is unsupported" (C:373-374): *implementation discrepancy* in part.
  No test opens the capture files, and they would be classed malformed, not
  unsupported (†).
- The template and constructed-test sentences: *supported interpretation*
  (†).

**Inferences.**

- (a) "I infer that a reusable test template is not yet the
  identity-asserting submitted specimen required at the public boundary."
  *Text:* for, C:375-376 with C:63. *Report:* `L-43` (†). *Class:* supported
  interpretation. See `A-D18`.
- (b) "I do not infer a public identity bypass for test templates from their
  pre-submission form." *Text:* for, C:376. *Report:* `L-43` (†). *Class:*
  supported interpretation.

**Uncertainties.**

- Candidate inspection procedure (open): `REQUEST-GRAMMAR.md:34` says the
  identity is read from the app's plist. The contract names that document as
  a lesson, not for this.
- Other infrastructure marker definitions (open): not found, beyond
  `ARCHITECTURE.md:468` on the registry's own version.

### A-46 · J-46 · C:379-390

**Restatement.** Faithful. Classes from `L-44`:

- "Direct source-test builds regenerate in the same way" (C:389):
  *unresolved*. The sentence can mean that such builds regenerate
  automatically or that the same command applies. Under the first meaning it
  is contradicted (`F-17`). The journal does not say which it took; listed
  under unclear items. See `A-D19`.
- The rest: *supported interpretation* (†).

**Inferences.**

- (a) "I infer that an ordinary build check is not an automatic repair of
  stale generated identity copies." *Text:* for, C:386-387 "never writes
  them". *Report:* `L-44` supported. *Class:* supported interpretation.

**Uncertainties.** None open.

### A-47 · J-47 · C:392-404

**Restatement.** Faithful. *Class:* supported interpretation (`L-45`).

**Inferences.**

- (a) "I therefore expect source edits outside the ABI declarations
  themselves to be capable of invalidating the exact pair identity." *Text:*
  for, C:401-404. *Report:* `L-45` supported. *Class:* supported
  interpretation.
- (b) The passage "does not say their contents are part of this source
  digest" (of the SDK and developer directory). *Text:* for, C:399-401;
  C:417 confirms. *Report:* `L-45`. *Class:* supported interpretation.

**Uncertainties.**

- Length-framing byte encoding (deferred): a source file the contract names
  (C:384). See `A-D20`.

### A-48 · J-48 · C:406-414

**Restatement.** Faithful. Classes from `L-46` ("Supported, with three
narrowings"):

- "The host checks identity before decoding worker evidence and before
  releasing attempts" (C:411-412): *implementation discrepancy* in part. True
  of the worker-evidence record; other publications are read without the
  check (`F-17`, †).
- "The magic also causes ordinal-era workers to refuse the header" (C:410):
  *unsupported claim*. No test runs such a worker (`F-17`, †).
- The field path at C:413: *supported interpretation* for the ordinary form;
  the actor form's path is not named (`F-17`, †).
- The rest: *supported interpretation*.

**Inferences.**

- (a) "I therefore cannot cite that field alone as proof that the child
  reached or passed its bootstrap checks." *Text:* for, C:412-414. *Report:*
  `L-46`, `F-20`. *Class:* supported interpretation.
- (b) "I do not assume it necessarily shares code 4" (of a size failure).
  *Text:* for; C:409 assigns 4 to magic and identity mismatch only. *Report:*
  `F-17`: a region that is too small exits 3. *Class:* supported
  interpretation.

**Uncertainties.**

- Result of a mapped-region-size failure (open): not found in documentation;
  the report gives it (`F-17`).
- The `query_first` chain (open): as in `A-18`.

### A-49 · J-49 · C:416-420

**Restatement.** Faithful. *Class:* supported interpretation (`L-47`).

**Inferences.**

- (a) "I consequently cannot elevate a matching hash into proof that an
  observed failure was sandbox-caused, or that the executable was
  authentically produced from those sources." *Text:* for, C:416-420.
  *Report:* `L-47` supported. *Class:* supported interpretation. The first
  half is also stated in repository guidance ("No dishonest attribution");
  `B-38` records both halves from the text alone.

**Uncertainties.** None recorded.

### A-50 · J-50 · C:422-427

**Restatement.** Faithful. *Class:* supported interpretation (`L-47`).

**Inferences.**

- (a) "I infer that proving the pair's internal match neither replaces
  external public admission nor establishes admission of validator diagnostic
  material." *Text:* for, C:422-425. *Report:* `L-47`. *Class:* supported
  interpretation.

**Uncertainties.**

- Validator diagnostic marker and admission rules (open): another repository
  document the contract does not point to. The guide's `transport` region
  describes the validator records (G:1494-1502, G:1564-1568).

### A-51 · J-51 · C:428-434

**Restatement.** Faithful. *Class:* supported interpretation (`L-48`).

**Inferences.**

- (a) "I infer that accepting an updated shape golden cannot by itself make
  an incomplete or mistyped required field semantically admissible." *Text:*
  for, C:433. *Report:* `L-48`. *Class:* supported interpretation.

**Uncertainties.**

- Concrete goldens (deferred): as in `A-04`.
- Producer-control procedures (open): not in the contract. The report's
  section 4.1 names the two producing cases.

### A-52 · J-52 · C:436-441

**Restatement.** Faithful. Classes from `L-48`:

- "A release contract can be produced only by an annotated release tag on a
  clean tree" (C:440-441): *unresolved* for a direct Cargo build, as at
  `A-02`; *supported interpretation* for the build script.
- The rest: *supported interpretation*.

**Inferences.**

- (a) "I would not accept a matching version, build number, describe string,
  or commit as a substitute for a matching `build.contract`." *Text:* for,
  C:439-440. *Report:* `L-03`, `L-48` (†). *Class:* supported
  interpretation.

**Uncertainties.**

- Format and derivation of the four descriptive fields (open): another
  repository document the contract does not point to. G:1207-1211 gives
  `version` as the nearest release tag and `number` as the commit count.

## Part 2: divergences

Each entry says which reading the contract text supports, gives the report
reference, and classes the belief in question. The baseline reader has been
dismissed, so a class given to a baseline reading cannot be checked with that
reader.

### A-D01 · Title, C:113 · what PolicyWitness is

*Text:* supports the baseline's observation. The contract never says what the
product is; C:113 uses "PW" unexpanded. The baseline's working meaning, "the
system whose sandbox requests, execution and evidence the contract governs",
is consistent with every later passage. *Report:* not covered. *Class:*
supported interpretation (baseline). The journal writer had the answer from
repository guidance, so the journal shows nothing here. Listed under report
corrections.

### A-D02 · C:3-6 · what a saved specimen and a client capture are

*Text:* supports the baseline's end state. C:3-5 uses the terms undefined;
C:63, C:249, C:304 and C:375-377 later give the relationships the baseline
lists. *Report:* not covered as a finding; `L-01` concerns admission.
*Class:* supported interpretation (baseline). The structures are deferred to
documents the contract names.

### A-D03 · C:8-13 · the input inventory

*Text:* supports both. C:12 says "declared language/resource suffixes and
explicit build helpers" and lists neither. The journal's claim is narrow
("I do not need the inventory to understand the stated distinction between
identity and provenance") and holds. The baseline's claim, that the digest
cannot be reproduced or every edge case decided from the document, also
holds. *Report:* `L-02`, `F-11`; section 4.3 gives the inventory from the
generator. *Class:* supported interpretation (both). The readers weighed the
same gap by different tasks.

### A-D04 · C:82-85 · direct XPC and selection fields

*Text:* supports the journal. C:83: "Direct XPC requests reject runner
selection fields." The baseline's "direct XPC rejects unresolved selection or
augments" attaches "unresolved", which C:85 uses of fragments, to selection.
Selection fields are refused outright. *Report:* `L-10`; even a null
selection value is refused on direct XPC (†). *Class:* mistaken reading
(baseline), with a caveat: the correcting line is inside the lines the entry
covers, but the entry is a compressed summary and the wording may be
compression, not belief. The parallel sentences at C:83 and C:85 make the
merge easy.

### A-D05 · C:98 · comparisons when scopes differ

*Text:* supports the journal's caution and leaves the baseline's question
open. C:98 permits different scopes; C:159 says comparisons "relate query and
attempt observations"; no line says what a comparison claims across scopes.
*Report:* `L-11`, `L-21`; not covered as a finding. *Class:* supported
interpretation (journal). The baseline's `U17` is answered, if at all, in
another repository document the contract does not point to: the guide's
`steps` region (G:1737-2012).

### A-D06 · C:117-118 with C:304-306 · "no parser generator"

*Text:* supports the baseline's reconciliation. C:116-118 sits in the request
region and speaks of request maintenance; C:304-306 describes a generator for
response records; C:309 says request JSON keeps its own boundary. *Report:*
not covered. `F-13` cites both passages for another purpose and does not note
that they appear to conflict. *Class:* supported interpretation (baseline).
The journal is silent. Listed under report corrections.

### A-D07 · C:117 · "the guide"

*Text:* supports the baseline. C:117 has no antecedent and no link. *Report:*
`F-12`, `F-01`, section 3.2. *Class:* supported interpretation (baseline).
Answered in another repository document the contract does not point to:
`docs/PolicyWitness.md`. The journal writer had read `docs/` guidance, which
names that file as the guide; the journal's lack of a question cannot be
credited to the contract.

### A-D08 · C:135 · what enforcement agreement requires

*Text:* supports the baseline's end state: C:135 and C:159 say what does not
establish agreement and give no positive criterion. The journal draws the
same limit and asks nothing further. *Report:* `L-17`; no agreement field
exists in the step record (†). *Class:* supported interpretation (both). The
positive answer, that the product makes no agreement claim at all, is stated
in the root guidance and not in the contract.

### A-D09 · C:147 · whether "remain available" means unlimited retention

*Text:* supports the baseline's later answer. C:147 states availability
without a bound; C:328-339 supplies budgets, truncation and the retention
cap. *Report:* `L-19`, `L-40`; helper output is also capped (†). *Class:*
supported interpretation (baseline). The qualification is about 180 lines
after the claim it limits, which is the kind of separation `F-07` describes.
The journal did not raise the question.

### A-D10 · C:153 · what triggers fallback compilation

*Text:* supports the baseline's statement that the contract does not say.
*Report:* `L-20`: the fallback is `sbpl-check`, run only after a client
`xpc_error` (†). *Class:* supported interpretation (baseline). Answered in
another repository document the contract does not point to: G:681-683 and
`ARCHITECTURE.md:133`.

### A-D11 · C:176 · "declaration reply", "singular worker projection"

*Text:* supports the baseline. Neither term is defined. *Report:* `F-12`;
defined in none of the documents the contract could defer to (†). *Class:*
supported interpretation (baseline). The journal entry restates the terms
without question; the close-out's carried-terms table records that the writer
held only the negative statement.

### A-D12 · C:180-181 · "An acquired decision does not publish another cell"

*Text:* supports neither reading over the other. The baseline's "prevent one
acquired decision from publishing another cell" follows the grammar; the
journal's "is not evidence of another cell's publication" changes the verb.
Neither can be checked while the term is undefined. *Report:* `L-24` not
determined; `F-15`: a temporal reading is contradicted, and a reading in
which the decision is simply not a cell is consistent (†). *Class:*
unresolved (both). Decided by a definition from the maintainer.

### A-D13 · C:263-264 · optional diagnostics and compatibility

*Text:* supports the journal's immediate answer. C:105-106, already read,
says there is no "compatibility exception for optional additions". The
baseline reached the same answer at `B-31` from C:341-345, which speaks of
the wire fingerprint "at this layer" and is the weaker support. *Report:*
`L-33`, `L-41`. *Class:* supported interpretation (both). The question was
invited by the word "additive" at C:263 beside "no additive compatibility" at
C:344-345. Listed under report corrections.

### A-D14 · C:267-270 · how array positions are represented

*Text:* does not decide it. C:267 says "decimal array positions", which
suggests text and does not say so. *Report:* not covered; `L-34` does not
state the element type. *Class:* unresolved from these inputs. Decided by the
record's declaration in `porcelain.json`, which the contract names and to
which the baseline deferred.

### A-D15 · C:297 with C:5-6 · historical registry forms

*Text:* supports both readers' conclusion. C:5-6 denies historical
translation in the sentence about admission; C:297 says publication "never
establishes execution compatibility"; C:372-374 separates infrastructure
markers from the public contract. *Report:* `L-37`; `F-12` lists C:297 as
live behavior about old data and does not note the tension both readers
felt. *Class:* supported interpretation (both). Listed under report
corrections.

### A-D16 · C:307-309 · what establishes that the schema is correct

*Text:* supports the baseline's statement that nothing in the contract does.
C:308-309: "none of them checks the schema itself". *Report:* sections 4.1
and 4.2: the generator validates the schema's form; an independently written
reader collects the reply shape; live readers use the shape goldens as
allowlists; nothing compares prose with code. *Class:* supported
interpretation (baseline). Answered by the report, not by any document the
contract names.

### A-D17 · C:348-354 · "fresh-read content", "rejected validator context", "owned endings"

*Text:* supports the baseline. None is defined. *Report:* not covered; `F-12`
does not list these terms. *Class:* supported interpretation (baseline).
"Fresh-read content" is answered in another repository document the contract
does not point to (G:1104); "rejected validator context" in part (G:1500);
"owned endings" was not found as a phrase. Listed under report corrections.

### A-D18 · C:375-377 · template or specimen

*Text:* supports the journal's inference and largely answers the baseline's
question. C:375-376 says a template carries no identity and the harness
asserts one at submission; C:63 says anything submitted needs the assertion.
The boundary is the presence of the assertion at submission. *Report:*
`L-43`; the harness refuses a template that already carries a marker (†).
*Class:* supported interpretation (journal). For the baseline's `U55`, the
classification half is settled by contract lines the reader had passed
(C:63); the inspection procedure is not in the contract.

### A-D19 · C:389 · "Direct source-test builds regenerate the same way"

*Text:* ambiguous between "regenerate automatically" and "are regenerated
with the same command". The baseline's question, which operations regenerate
and which only check, is the right one. *Report:* `L-44`, `F-17`: nothing
regenerates automatically; an earlier revision read "can regenerate with the
same command" (†). *Class:* unresolved for the journal's restatement, which
does not say which meaning it took; supported interpretation for the
baseline's question. The baseline deferred it to `BUILD.md`; these inputs do
not show whether that document answers it.

### A-D20 · C:399-400 · "the shim"

*Text:* supports the baseline. The term is not identified. *Report:* `L-45`
uses the term without defining it; the definition is in the report's traces
(†), not in the report. *Class:* supported interpretation (baseline). Listed
under report corrections.

## Part 3: findings against the journals

"Formed" means the reader states the conclusion; "formed by restatement"
means the reader repeats the contract sentence the finding concerns without
qualifying it. "Avoided" means the reader states something that rules the
conclusion out. "Silent" means neither.

| Finding | Reader conclusion the report states | Journal | Baseline |
| --- | --- | --- | --- |
| F-01 | A reader given only `CONTRACT.md` "will take that paragraph as the complete normative definition" of a surface. | **Avoided.** `J-14`, `J-16`, `J-25` record the paragraphs as not enumerating; the close-out says a mention of "the guide" did not identify a document. | **Avoided.** `B-10`, `B-19`; carried term "Guide not uniquely identified". |
| F-02 | A reader navigating by outline "will conclude that only the first surface is under 'Normative surfaces', and cannot tell where a surface's normative text ends". | **Silent.** Read raw Markdown with markers visible (close-out, part 1). | **Silent.** Read raw Markdown (close-out, part 1). |
| F-03 | "an unchanged row means an unchanged surface". | **Silent** on the inference. Relies on the table: close-out, Journal §3, "Answered — identifying changed surfaces"; `J-10`. | **Silent** on the inference. Relies on the table: `B-02`, `B-08`. |
| F-04 | A reviewer who opens the manifest "will read `checks` as the verification owner of each surface". | **Silent.** Manifest unopened (`J-04`). | **Silent.** Manifest unopened (`B-02`). |
| F-05 | The examples are "verified" (C:104, C:365). | **Silent.** Repeats the word at `J-10` and `J-44`; forms expectations from examples at `J-06`, `J-14`, `J-16`, `J-29`. | **Silent.** `B-08` and `B-33` drop the word. |
| F-06 | A reader "will take it as a reader-side rule" (the nonce sentence). | **Formed.** `J-29`. | **Formed.** `B-22`: "a matching surrounding reply does not excuse a wrong nonce". |
| F-07 | A reader of the equipment region alone "will conclude that a reply with, say, a satisfied gate lacking a source timestamp cannot appear in output", and will assume a `runner_reporting_failed` reply passed the checks. | **Silent** at `J-24` to `J-28`. `J-43` states the general rule and ties it to C:165, not to those entries. | **Silent** at `B-18` to `B-21`. `B-32` states the general rule. |
| F-08 | The code table's "layout reads as complete"; capacity checks precede all meaning checks; the four null exceptions are the list. | Table: **silent** (`J-34`). Ordering: **formed** (`J-35`; close-out, Journal §9). Nulls: **avoided** (`J-07`). | Table: **silent** (`B-26`). Ordering: **formed** (`B-26`, `U18` answered). Nulls: **silent** (`B-05`). |
| F-09 | "no shipped tool reads a specimen without the gate, and … only the build script can produce a bound binary". | Helper: **silent**. Bound binary: **formed by restatement** (`J-02`, `J-52`). `_test_overrides`: read as instrumentation (close-out, part 3), silent on what it can replace. | Helper: **silent**. Bound binary: **formed by restatement** (`B-01`, `B-40`). |
| F-10 | "equal contracts mean equal binaries and … a matching peer is an authentic one". | **Silent.** `J-12` limits repeatability of observations; `J-49` limits the worker hash only. | **Silent.** `B-38` limits the worker hash only. |
| F-11 | "The reader cannot tell from the document which test files are 'ordinary'"; four further edge cases. | **Avoided.** Close-out, Journal §2: could not "classify every possible file as included". | **Avoided.** `U1` open: could not "decide every release-tree edge case". |
| F-12 | Denials of "mechanisms a fresh reader has never heard of"; undefined terms; references with no antecedent. | **Formed** for the references and terms: `J-05`, `J-21`; close-out, part 3. The denials were restated without difficulty (`J-10`, `J-44`, `J-46`). | **Formed:** `B-03`/`U8`, `B-16`/`U30`, `B-32`/`U54`; carried terms. |
| F-13 | Maintenance conventions and implementation detail are "presented in a public contract". | **Avoided.** `J-10`, `J-11`, `J-44` attribute the sentences to maintainers; `J-50` keeps the internal identity separate. | **Avoided.** `B-09`, `B-33`, `B-38`. |
| F-14 | The three implementations "cannot disagree with each other about structure". | **Formed**, in a weaker form: `J-38`, "I expect the three structural definitions to agree". | **Formed:** `B-28`, "Their shared derivation aligns structure". |
| F-15 | Four equipment sentences are taken as written: the acquired decision, packaged selection, empty observation arrays, ordinals local to the source. | **Formed by restatement:** `J-22`, `J-24`, `J-26`. `J-21` forms a reading of the first. | **Formed by restatement:** `B-17`, `B-18`, `B-20`. `B-16` forms a different reading of the first. |
| F-16 | "Survives unrelated writes", "lossless read-back" and "It never establishes" are taken as written. | **Formed by restatement:** `J-37`, with "It" resolved to publication. | **Formed by restatement:** `B-27`, same resolution. |
| F-17 | Direct source-test builds regenerate automatically; the host checks identity before decoding all worker evidence; ordinal-era workers refuse the header. | Regeneration: unclear (`J-46`). Host check and ordinal-era workers: **formed by restatement** (`J-48`). Size failure: **avoided** (`J-48`). | Regeneration: **avoided**, as a question (`B-35`, `U56`). Host check: **formed by restatement** (`B-37`). |
| F-18 | Stated behavior holds although no executing test reaches it. | **Avoided** as a general stance: `J-12`, `J-43`, `J-49` decline to treat statements as verified. Relies on `runner_reply_truncated` at `J-41`. | **Avoided:** `B-38`, `U59`: "supplies no results". Relies on it at `B-30`. |
| F-19 | A reader of the guide would believe a host from another build can execute the specimen before its reply is refused (G:1519-1521). | **Silent.** Guide unopened. | **Silent.** Guide unopened. |

Reliance on the statements the findings concern, beyond the cells above:
`J-03` and `B-01` rely on the reuse procedure (`F-03`); `J-29` and `B-22` on
the receipt sentence (`F-06`); `J-35` and `B-26` on the ordering sentence
(`F-08`); `J-23`, `J-24` and `B-17` on the referral of "reserve geometry" to
`LIMITS.md` (`L-25`).

## Part 4: four lists

### Silences

Conclusions that would affect what a reader does and that neither journal
states or rules out. The first seven are the Part 3 rows where both are
silent.

1. **Where a surface's normative text ends (`F-02`).** A reader of the
   rendered page looks under "Normative surfaces" for the transport rules,
   finds one surface there, and takes "Typed response transport" for
   background. Both readers read raw Markdown, so neither journal can show
   this.
2. **An unchanged stamp row means an unchanged surface (`F-03`).** An author
   moves a specimen to a later release, sees that `probes` has not moved,
   changes the assertion without rereading, and an attempt action's side
   effect has changed with no edit to prose or goldens.
3. **The manifest's `checks` names what verifies a surface (`F-04`).** A
   reviewer preparing a release opens the manifest, sees `runner_byoxpc`
   beside `transport`, and credits the default battery's pass to it.
4. **Each example is tested behavior (`F-05`).** A consumer's author cites
   the wrong-nonce example as tested behavior and omits their own nonce
   comparison.
5. **A published reply satisfies the equipment region's "requires"
   (`F-07`).** A consumer reads `termination_gate.outcome: "satisfied"` and
   acts on it without reading `disposition_integrity`; or treats the actor
   records in a `runner_reporting_failed` reply as checked.
6. **Equal contract strings mean equal builds, and a matching peer is
   authentic (`F-10`).** An operator compares two apps that both report
   `release:v0.3.6`, one built without the runner, and expects the same
   behavior; or treats a runner whose control reply matches as the shipped
   one.
7. **The guide and the contract agree (`F-19`).** A user who has only the
   shipped guide reads G:1519-1521 and plans for a specimen having run on an
   outdated external runner before the reply is refused.
8. **A shipped helper reads a specimen without the gate (`F-09`).** A user
   runs `sbpl-check` on a specimen asserting another release and takes the
   compile verdict as given under that specimen's contract.
9. **`_test_overrides` can replace the worker and validator in a signed build
   (`F-09`).** A service that accepts specimens from others admits one whose
   `contract` is current and whose overrides name another executable.
10. **The refusal table is the code vocabulary (`F-08`).** A consumer writes
    an exhaustive match over the 22 listed codes and meets
    `exclusive_plan_forms`. Both readers restate C:289 on unfamiliar codes;
    neither says whether the table is complete.
11. **The reuse procedure covers a specimen asserting a development identity
    (`L-04`).** An author whose specimen asserts `development:<sha256>` looks
    for "its asserted release" in the table and finds no row to compare.
12. **Exit 1 means `bad_request` (`L-33`).** A script branches on the
    controller's exit status and treats a transport refusal, which also exits
    1, as a malformed request. The journal leaves the other statuses open;
    neither reader rules the conclusion out.
13. **The host receives the file's bytes (`L-20`).** An author relies on a
    property of the file as written, such as a repeated key, that
    re-serialization does not preserve.
14. **An invalid command-line selector is handled like one in the request
    (`L-08`).** A caller passes a foreign specimen with an invalid
    `--runner-mode` and expects the contract refusal described at C:63.

### Unclear journal items

1. **`J-46`, "Direct source-test builds regenerate in the same way."** It is
   not clear whether the writer understood such builds to regenerate the
   identity copies automatically or understood that the same command is run
   by hand. `A-46` leaves the restatement unresolved.
2. **`J-29`, "host identity admission is necessary but insufficient for
   accepting the receipt's content."** It is not clear who does the
   accepting: a reader of a received reply, or the host before it publishes.
   `A-29` classes the inference as an invited misunderstanding on the first
   meaning; on the second it is a supported interpretation.
3. **`J-26`, "The ordinals belong to the source actor process."** It is not
   clear whether "the ordinals" includes the activation ordinal of a
   dependent phase. If it does, the belief is what `F-15` describes; if it
   means only the source's own ordinals, it is correct.

### Report corrections

Missing from the report:

1. **Byte order and boolean encoding in the frame description.** C:313-326
   gives byte order only for the payload length. `L-39` says "Supported in
   full" and does not note that an implementer cannot write a compatible
   reader from the passage. Both readers recorded it (`J-39`, `B-29`/`U49`).
2. **The apparent conflict between C:117-118 and C:304-306.** "No additional
   schema language or parser generator is used" is followed, 190 lines later,
   by a generator. The baseline reconciled it (`A-D06`); the report does not
   mention it.
3. **The tension between C:5-6 and C:297.** The opening denies "historical
   translation"; C:297 reads "historical flattened entries" and projects
   "retired kind aliases" as their current kind. Both readers noticed and
   resolved it (`A-D15`); `F-12` lists C:297 only as live behavior.
4. **"Additive" at C:263.** "Optional additive response/envelope information"
   sits beside "no additive compatibility" (C:344-345) and "no … compatibility
   exception for optional additions" (C:105-106). It cost the baseline reader
   a carried question (`A-D13`).
5. **Terms absent from `F-12`'s list.** Readers could not place: the product
   name and "PW" (`A-D01`); "fresh-read content", "rejected validator
   context", "owned endings" (`A-D17`); "shim" and "host mirror" (`A-D20`);
   "complete observation partition" (`J-24`, `B-18`/`U32`); "native-string
   admission" (`J-34`, `B-26`/`U44`); the trigger of the "fallback compiler"
   (`A-D10`); "independently inspected candidate" (`J-45`, `B-34`/`U55`);
   "producer controls" (`J-51`, `B-39`/`U60`); "packaged peer checks"
   (baseline carried terms).
6. **The element type of `path`.** `L-34` does not say whether components
   are text (`A-D14`).
7. **The dangling referral at C:193 as a reader effect.** `L-25` notes that
   "reserve geometry" does not occur in `LIMITS.md` (†) and no finding
   carries it. Three entries rely on the referral (`A-23`).

Expectations the journals do not bear out. The report's ratings are not
revised; these stand beside them.

8. **`F-01`.** The report expected a reader to take a one-paragraph region
   as the complete definition. Both readers recorded the paragraphs as
   incomplete. What they could not do is find the rest, which is the fact
   the finding rests on.
9. **`F-13`.** The report expected maintainer sentences to read as contract
   requirements. Both readers attributed them to maintainers.
10. **`F-12`, the denials.** Both readers restated most denials of retired
    mechanisms without recording difficulty. The undefined terms and missing
    antecedents did cost them, as the finding says.

Nothing in these inputs shows a statement of fact in the report to be wrong.

### Skipped

- The journal's preamble and the baseline's opening line: statements of
  method, not beliefs about the contract.
- Close-out part 1 (reading conditions), part 4 (going back) and part 5
  (changes of mind) of both readers. They were read and used as context.
  Part 5 of the journal's close-out was checked against Part 1 here: its
  seven refinements are consistent with `A-06`, `A-09`, `A-11`, `A-18`,
  `A-20`, `A-26`, `A-30` and `A-46`, and none withdraws a belief.
- Close-out part 3 (carried terms) of both readers: used to class items and
  to fill Part 3, not adjudicated row by row. Most rows restate a contract
  term with a working meaning and make no claim to judge.
- Uncertainty items the journal's close-out marks "Answered". They are not
  re-examined, with one exception noted at `A-35`: the close-out records
  "capacity before meaning checks" as an answer, and `F-08` qualifies it.
- Baseline entries as such. They are judged only where the ledger records a
  divergence and in Part 3, as the task defines.
- The journal's source links. They are absolute paths into this checkout and
  were not followed or checked.
- The splice order of augments, actor scheduling rules and two omission
  defaults: the documentation search did not settle them and no source was
  opened. They are marked "not found" in `A-07`, `A-08` and `A-15`.
