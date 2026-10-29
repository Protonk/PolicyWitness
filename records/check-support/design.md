# Proposed design B1

Paper design B1, based on the fixed cf0136b inventory. Nothing in this package
installs a checker, changes a generator or promises semantic validation.

## Decision

Prefer a small explicit applicability record for selected relationships over
a universal claim registry. Reuse existing source identities and file hashes.
A reverse index and class census are derived views of those registrations and
existing citations, not separate authored databases. Unregistered prose is
reported as outside the registered set; the census must never call it verified.
Do not infer subject equivalence from words or make Example B a new semantic
registry project. Preserve existing G4 and generator controls as their own
contracts, without crediting them as evidence applicability checks.

Each selected relationship supplies:

1. A stable claim ID, owner document/source site, exact text input selector
   (file or unambiguous structured manifest item), and binding class.
2. Evidence locator, actual assertion/observation, scope, preconditions and
   excluded inferences. A test definition alone is a pointer, not a witness.
3. Represented inputs: existing worker identity where relevant, exact source
   file hashes for observer/helpers, exact claim text/input hash, receipt
   identity and conditions (host/build/tool context for native observations).
4. A reviewer/date/source baseline and rationale for applicability. A review
   may grant reuse, require a new observation, narrow/remove a current claim,
   or leave it unresolved. The authoring reviewer owns semantic sufficiency;
   another reviewer is desirable but not fabricated as a mechanical property.
5. Whether the evidence is historical-only or requested as current support,
   and the checkpoint at which current support is required.

No complete-dependency assertion is implied. Source-level conditions and an
app fingerprint alone cannot attest the currently installed OS or tools.
Those conditions must be supplied/observed for a native acceptance checkpoint;
offline omission is `conditions-unavailable`, not a clean applicability pass.

## States and triggers

| Input/result | Diagnostic and required action |
| --- | --- |
| No selected registration | `unregistered`: census entry only; no evidence pass. A reviewer chooses whether to register, narrow, or leave outside. |
| Named referent absent | Existing pointer failure `referent-missing`; repair citation or restore referent. This is mode1, not new B1 semantics. |
| Registered observation without identifying receipt | `evidence-missing`; supply attributable evidence or retain only unsupported/historical prose. A named run absent from tree is not invented. |
| Required represented input unavailable | `input-unavailable`; cannot establish comparison. Raw full capture availability is separate from having a compact committed receipt. |
| Registered evidence/claim/conditions changed from reviewed baseline | `review-required` naming exact changed input(s), old/new fingerprints and affected IDs. No automatic assertion of factual falsity. |
| No represented changes, but no substantive review | `unreviewed`; re-stamping is insufficient. |
| Reviewed representation unchanged | `represented-inputs-current` for the specified scope, not a claim of complete dependencies or current native behavior. |
| Historical-only evidence | Preserve date/scope. A changed implementation does not invalidate past observations. Current-support request remains separate. |

Failure modes2/3 are addressed only as **change detection for registered,
represented input**, never detection that the new meaning is wrong. An exact
file hash is deliberately conservative. A structured item can reduce unrelated
prose churn where it already has a stable ID; do not add custom source parsers
or a new fingerprint scheme merely to avoid a review. Modes4/5 (coarse/wrong
referent and absent assertion), wrong manifest faithfully rendered, omitted
facts and unconnected contradictory prose are semantic review exclusions.
Existing citation presence still passes such cases; B1 must label that limit.

## Checkpoints and complete worked paths

Build retains generator currency and source membership gates. B1 does not make
ordinary builds run signed-app witnesses or block because a historical census
has a new worker identity. The default source-level checkpoint reports
registration/input/citation problems and review-required state. A deliberately
registered **current-support-required** relationship blocks that checkpoint
until a substantive applicability disposition is recorded; historical-only
rows report their date and cannot silently count as current support. Native
acceptance runs the relevant witness only when review identifies a consequential
change or conditions needing observation. This separation avoids turning every
fingerprint change into an unconditional forty-second launch run.

L: register separate relationships for (a) actual readiness/completion/reap
assertions and (b) inventory census under the two selected empty-plan launches.
Retain descriptors0–4, null stdio, cwd/, ps equality, vmmap and lsmp outcomes
as dated census facts; do not promote them to required exact outputs. Current
coverage using the census requires the explicit applicability decision already
called for by WORKER. Store the existing worker identity plus seven receipt
source hashes and claim input, with host/observer conditions. Changed worker
identity produces `review-required` for registered current reuse. Reviewer
examines exact delta and conditions: unchanged operational paths may justify
reuse; changed launch/observer behavior or unresolved conditions requires a
new opt-in launch_inventory observation. The record names the diff and why it
supports the disposition, not just a replacement digest. Native output still
needs review of the inventory contents because this case does not assert them.

At f468200, unchanged L receipt plus changed identity/three file hashes yields
a review request. A hypothetical qualified review can retain the dated census
and decide whether reuse is warranted; replay cannot supply that decision from
absent raw app evidence. At69c7dfe the matching representation is a conditional
negative given a supplied adoption review, not independently proven support.

Limits: a changed limits.json value updates generated regions but leaves the
compiled C printer unchanged. Generation can be current while `compare`
fails exact selected-value equality. The comparison's mapping/subtractions
belong to its test, not the manifest. Review routes value edits to compiled
comparison and relevant independently expected boundary/path cases; the
native query cap uses fixed65,534/65,535 inputs. Passing equality cannot grant
behavioral support. A relationship to this actual assertion has file/manifest
inputs and test conditions; a changed test or claim triggers review even if
the function name persists. No new generic test framework is needed.

The index maps a changed represented file/identity/structured item to its
registered claim IDs and source citations. Symbol-only sources expose their
coarse scope rather than pretending a token is the asserted operation. A
generated census can count identity, value agreement, witness, pointer and
structure relationships separately, with unregistered/unreviewed/historical
states. It should report the registered population denominator, not "all claims".

## Adoption policy, controls and cost

Historical replay annotations are hypothetical registrations authored using
facts available at the named tree. They may name an existing claim, receipt,
file, test and review baseline, but may not silently import future audit
knowledge as a past review. A supplied review is an explicit assumption, not
historical evidence. Run each scenario with that assumption identified; absent
real registrations remain `unregistered` in an unadopted tree.

Any future implementation needs paired controls for missing receipt/input,
changed claim/evidence, unchanged reviewed representation, historical-only
state, absent registration, owner disposition and failure to drop a blocker by
only updating a hash. It needs no new native equipment to perform fingerprint
comparison. Keep compact receipts committed where they already have an owner;
raw retention remains the existing harness's responsibility. Do not duplicate
the catalog, manifest, retention index or source inventories.

Machine overhead is unmeasured: one bounded declared-input read/hash pass plus
index construction, not an output-tree scan. First-adoption review and ongoing
change review are the main costs. Existing instrumented timings are in costs.md.
The churn prediction is five review events for the five named worker-identity
changes, zero automatically ordered observations. Conservatively estimate one
diff/condition review per event, with build-target changes deserving particular
attention; exact human minutes are unmeasured. A blind whole-identity rerun rule
would impose five launch runs (roughly200s from the suite's about40s account,
plus build/process-inspection cost) without resolving what assertions support.

## Coverage and held-back policy

Open cases test missing receipt, unchanged represented inputs, changed worker
identity/file hashes, changed registered claim file, excluded unconnected prose,
wrong/coarse attribution, nonasserting check, wrong generated source and omitted
fact. Existing G4's missing referent class will also be tested through a reserved
historical case; it is not advertised as new B1 behavior.

Curator reserved six cases before seeing this design: one each for modes1–5 and
omission/unregistered prose, seal
`6c68e4618806d0d47000a10c0ea5be39ac564d1159c4497190153425a78c2cb4`.
Designer has seen no selected sites/revisions/expectations at this point. Prior
independent familiarity cannot be ruled out and will be disclosed on reveal.
Freeze B1, its annotation policy, open results and class-level predictions
before revealing them. Predictions: missing referent fails pointer lookup;
registered changed inputs/claim request review; unchanged reviewed inputs are
conditional negatives; modes4/5 and unregistered omission are excluded or
unreviewed, never clean semantic passes. Curator-specific predictions remain
sealed; commit their reveal before evaluating. If a case reveals a flaw, retain
the failure; changed design is B2 with exposed cases now development material.
