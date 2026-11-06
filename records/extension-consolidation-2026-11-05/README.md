# Extension consolidation: contract review packet

**Status: final implementation and verification accepted by the user on 2026-11-06.**
The [final review account](final-review.md) and [implementation status](implementation-status.md)
record the current candidate. The [review decision](review-decision.md) records
authorization on 2026-11-06. Everything below this introduction preserves the
historical Stage 1–2 proposal and its then-current baseline; its prospective
wording and examples do not describe the final candidate. Associated plan:
[runner/EXTENSION-CONSOLIDATION-PLAN.md](../../runner/EXTENSION-CONSOLIDATION-PLAN.md).
Source baseline: `4cd1d6c7f14e3ebacfd2dda219dda85967f64680`, initially clean.

The proposed design replaces declarations with one actor extension mechanism.
Two signed variants of the same C worker preserve selectable issuer/subject
equipment. One admitted operation plan reaches execution; bounded automatic
setup observations retain primary failures, independent cleanup and each
actor's facts. A narrowly defined optional termination dependency orders a
later visit after an owned natural reap. Ordinary non-extension execution
remains available.

## Review decisions and recommendation

| Decision | Recommended contract | Grounding / remaining candidate obligation |
| --- | --- | --- |
| Actor equipment | `equipment: "selected" | "unentitled"`, omission selects `selected`; fixed distinct bundle-local workers compiled from one implementation. Equipment is independent of apply/unapplied. | Signed actual-worker prototype established the mixed arrangement for recorded equipment. Candidate must implement public selection, verified inventory/binding, installation and independent substitution refusal. |
| Entitlement requirements and provenance | Actor `required_entitlements` travels over XPC and applies to that actor's bound worker. Existing runner-level requirements remain selected-worker preflight. Separate requested selector, inspected artifact and owned live code observations. | Signature read-back, native effects and process identity support different claims. Live inspection after setup occurs before any scheduled activation; mismatch withholds activation while retaining setup/application facts. No new pre-policy worker rendezvous is proposed. |
| Automatic authority setup | One `authority_setup` account, scoped host run/region/custody and per-worker observations. Immutable independently published cells plus a separate terminal decision; 832 native bytes per worker and bounded reply storage. | Required-apparatus refusal terminates locally before policy processing. Missing symbols are per-operation capability observations. Failed/late setup never restores visit eligibility; valid facts survive. |
| Apparatus applicability | Preserve existing provisioning: an authority session assigns a required region to every actor, including actors with no authority actions. With no authority session, missing descriptor is not-required; symbol/core-limit observations remain applicable. | Avoids introducing selective region provisioning into this work. The required bit comes from the resolved assignment, not observed FD presence or participation alone. |
| Termination dependency | Include `phases[].after_termination: {"actor_id":"issuer"}`. Require the source's final visit earlier; owned natural reap satisfies termination even after abnormal exit, subject to existing failure/quiescence rules. | Gate precedes activation/query collection. Fixed 5,000 ms clipped to remaining execution allowance; timeout/ownership failure cancels later activation. Cleanup cannot retroactively satisfy it. New ordering and removed-gate controls remain required. |
| Versions | Request 6, response 26, envelope 11; runner protocol remains 3. Regenerate internal worker identity. | Removal changes request/reply meaning; per-actor dossier interpretation changes envelope rules. Reservation/capture protocol is unchanged. The manifest is not edited until acceptance. |
| Declaration removal | Refuse top-level `extensions`, including null; remove separate issuer/channel, singleton native implementation and declaration-only operands/overrides. | Ledger preserves shared fresh-file, validator ownership, byte-erasure and reply-size assertions. No adapter, legacy positive reader or negotiation path. Old installation recovery remains usable. |

Review may accept these recommendations together or identify a specific
revision. The plan's checkpoint requires that decision before broad production
implementation. No recommendation is treated as implicit approval merely
because an example or prototype exists.

## Packet map

- [Authority/equipment contract](authority-equipment.md): field defaults and
  bounds, bundle/signing ownership, host binding, direct XPC, requirements,
  provenance and refusal meanings.
- [Setup/lifecycle contract](setup-lifecycle.md): native inventories, exact
  proposed C/Swift cell layout, publication, primary/cleanup distinction,
  terminal pre-policy refusal, dependency and erasure ownership.
- [Resolved operation plan](resolved-plan.md): concrete typed representation,
  preparation owner, admission handoff, removed lookups/fallbacks, internal
  errors, versions and current-schema negative controls.
- [Disposition ledger](disposition-ledger.md): production/test/documentation
  remove/adapt/retain entries, named assertion owners, boundary-mode migration,
  watchlist and protected shared coverage.
- [Verification selection](verification-selection.md): exact catalog cases,
  equipment requirements, coordinated suites, candidate controls and final
  default battery. All listed selectors resolve against the baseline catalog;
  proposed BYOXPC case consolidation is explicitly distinguished.
- [Evidence account](evidence-account.md): current signed baseline,
  dispatcher results, prototype observations, failures and applicability.
- [Evidence archive index](evidence/index.json): original identities, hashes,
  copied source/observations and per-file inventories.
- [Recovery receipt](recovery.json): the prototype's retained App Sandbox
  container and the already-existing test container. Copies do not transfer
  active cleanup ownership.

## Complete proposed requests and representative replies

The JSON requests in [examples](examples/) are complete **draft schema-6**
requests, not requests accepted by the current app. The target
`/private/tmp/pw-extension-review/target.txt` denotes a file the specimen author
must prepare with known contents; it is not a retained test result. Public
examples must be regenerated into the guide only after contract acceptance.

| Example | Question and interpretation |
| --- | --- |
| [Basic issuer/subject](examples/basic.request.json) | Subject baseline fresh read; issuer issue/transfer; subject consume; a later phase collects queries before a fresh read; explicit release; another later fresh read. Successful consumption and known bytes establish the positive calibration. Post-release access is observed without a promised pattern. |
| [Termination dependency](examples/termination.request.json) | Same actors set up eagerly. The issuer's supply phase is its final visit. Subject consumption is gated on the host's owned natural reap; later fresh access retains its separate native evidence. This does not defer subject creation. |
| [BYOXPC mixed equipment](examples/byoxpc.request.json) | Same model with an unentitled issuer and selected entitled subject. `com.policywitness.review` is an illustrative owned installation name; the selected worker must actually carry the required allow-jit key. That key distinguishes signing, not the cause of file access. |
| [Sandboxed issuance/re-delegation](examples/redelegation.request.json) | The original issuer supplies B; sandboxed B consumes, reads, issues and transfers to C; C consumes and reads; releases and later reads are retained. A full-chain claim requires all links and known fresh contents, independently of a passing apparatus-only result. |
| [Ordinary specimen](examples/ordinary.request.json) | The non-extension single-worker form remains usable. |
| [Removed-field and dependency refusals](examples/negative-requests.json) | Current-schema requests target the removed field/operand or invalid dependency. Unsupported-version tests remain separate. |

The [representative successful reply projection](examples/basic.reply-projection.json)
shows the proposed landing paths and actor/resource associations. It is a
constructed schema-design example, not an execution receipt or full replacement
for the unchanged subprocess/ordering field specifications. Complete proposed
setup subobjects and their actor/phase assessments are supplied for
[host failure](setup-examples/host-failure.json),
[worker primary plus cleanup failure](setup-examples/worker-primary-cleanup.json),
[two workers failing at distinct stages](setup-examples/two-worker-failures.json),
[validation rejection](setup-examples/worker-validation.json),
[late observation after timeout](setup-examples/late-setup.json), and
[unresolved object-name cleanup](setup-examples/host-unlink-unresolved.json).
These examples deliberately do not satisfy the current response schema.

## Bounds and verification that implementation must finish

The setup contract fixes native storage and an encoded reserve of 524,288
bytes. The equipment contract bounds two packaged artifact read-backs and up to
eight live read-backs, independently of per-actor requirement decisions.
Explicit test overrides can add two inspected fixture artifacts, so the
whole-response proof covers twelve read-backs (ten without overrides).
Each serialized XML entitlement payload is at most 65,536 UTF-8 bytes before
JSON; oversize observation refuses eligibility and never silently truncates
requirements. Requirement keys are at most 64 per actor, 255 UTF-8 bytes each.

Use a conservative **8 MiB additional constructed-reply allowance** for the
new setup/equipment/dependency/preparation fields until the final field-complete
encoder proves a tighter exact maximum. Its independent overbound includes:
4,718,592 bytes for twelve fully escaped read-backs; 1,569,824 bytes for eight
required/missing-key list pairs; 524,288 for setup; 393,216 for twelve bounded
32,768-byte equipment metadata groups; 65,536 for sixteen 4,096-byte gates;
and 4,096 for the preparation summary (7,275,552 total). The metadata groups
must include all static/per-actor wrappers, paths, signature labels, inspection
statuses/diagnostics and table-reference overhead; the implementation's
constructor/checker must reject any larger proposed group rather than hide it.
This is a deliberately conservative **encoded-output** reserve, not a process
memory estimate or permission to cap/truncate observed facts at runtime.

`ReplyMaximumTests` must recompute the complete result after extracting ordinary
fresh-read allowance and removing declaration accounting. Update
`runner_reply_maximum` to that actual constructed maximum, and derive the
controller receiver bound by the existing three-times/4-MiB-rounding rule.
Do not assert the current manifest's numbers already prove this proposal.
Add independent limit-value and boundary controls in implementing languages,
and exercise real maximal replies separately from the constructed bound.

The full coordinated suites, adapted native dispatch/setup/erasure and reader
mutations, mixed-equipment BYOXPC controls, ordering mutations and final default
battery are Stage 4 obligations. The 13 successful baseline dispatcher cases
are not replacements for them. The deferred host-setup observer-receipt issue
remains independently owned and must receive explicit disposition if encountered.

## Review audit and stopping point

Four delegated investigations/reviews were used (three Astra, one Sol), within
the user's total cap and four-concurrent-agent environment limit. Root retained
all builds, live execution, integration and evidence ownership.
An independent packet review identified and resolved applicability,
prelaunch-versus-runtime failure shape, independently published cleanup role,
shared-memory name-reuse recovery, and shared static inspection versus per-actor
requirement-decision ambiguities. These are contract clarifications; none claims
the new product behavior already exists.

Stage 1 established a current signed baseline and a bounded successful
same-worker-variant authority arrangement. Stage 2 provides the concrete
contracts, examples, dispositions and selections for review. One supplemental
parent-restriction experiment failed and is retained with narrow partial credit;
one newly created test container remains under owned cleanup. These limits are
visible in the evidence account. The plan remains active at its review
checkpoint; Stage 3 has not begun.
