# Maintainer's close readings of CONTRACT.md

Readings the maintainer supplied during stage 4 of the plan in
`records/contract/CONTRACT-CONTACT-PLAN.md`, kept verbatim. The strain
register in `records/contract/CONTRACT-LEDGER.md` cites them by heading.
Sibling artifacts are named by path without links, under the records link
rule.

## C:243, the compiled-profile paragraph (2026-11-09)

Claims `K-243-1` to `K-243-9`. Register rows `R-01` to `R-05`.

I'd like to focus just on the paragraph in C:243.

The paragraph repeatedly uses the language of a precise contract while leaving the operative relationships unspecified. “Inherits,” “admitted,” “context,” “consistent,” “grants,” and “refuses” each suggest an established rule. Reading closely, we keep having to supply the actor, the comparison, the relevant boundary, or the consequence ourselves. The final example then supplies a concrete rule that the implementation does not perform.

“A compiled-profile receipt inherits its admitted host reply context” has a useful meaning: the receipt is interpreted under the public contract identified by its enclosing host reply. It carries no independent build identity. But “inherits” describes an interpretive relationship, not an operation that transfers information into the receipt. “Admitted” also needs care. The controller checks the reply’s producer contract before checking the receipt; receipt validation is itself part of deciding whether to admit the reply. The sentence cannot mean that the reply has already passed every check before its receipt is examined. Its defensible meaning is narrower: the enclosing reply’s identity must match before the receipt receives semantic interpretation.

“It has no independent schema marker” adds a useful qualification, provided “schema marker” means a separate version or compatibility identity. The receipt still has a structure defined by the shared wire schema. It simply has no independent contract or version field. This should be an uncomplicated fact, yet the guide still tells readers to require a “nested receipt version,” and the source comment still calls the receipt “Versioned.” The surrounding documentation does not consistently describe even this basic property.

“Status, nonce, worker binding, stage, byte count and digest must be consistent” is where the paragraph becomes substantially less informative than its tone suggests. Consistent with what? These items do not participate in one common consistency relation. A captured status requires the producer and stage labels `worker` and `before_apply`; an unavailable status excludes those labels. The captured nonce is compared with the requested nonce. The recorded PID is compared with the worker PID the host is collecting from. The byte count is checked against capacity and determines how many bytes the host reads. The bytecode digest is compared with the host’s calculation over those bytes. “Worker binding” gives a PID comparison the appearance of a broader, unspecified identity guarantee.

Those relationships also have different owners. The host checks nonce, PID, extent and digest while collecting the worker’s capture. The controller’s receipt-specific semantic validation checks status, producer and stage. The list conceals that division of responsibility. Some comparisons require information outside the receipt, so a reader could not perform them merely by inspecting its fields. The host additionally checks source and parameter identities, which the list does not clearly name. Even `captured` carries a substantial condition left unstated here: the host requires successful application and successful worker completion before publishing that status. The paragraph offers a checklist of nouns where it owes the reader actual rules.

The semicolon then joins this incomplete account of consistency to “a detached receipt grants no producer context.” This clause does not explain consistency. It changes the subject back to the relationship between the receipt and its enclosing reply, without saying that it has done so.

“Producer context” is particularly ill-chosen because the reply and the receipt both have something named `producer`, with different meanings. The reply’s producer record identifies its build through `contract`, `describe` and `commit`. The receipt’s producer string says `worker`; its stage says `before_apply`. A receipt extracted from its reply can still contain that producer label, a worker PID, a nonce and a stage. It has not lost all information about its production. What it lacks is the enclosing reply’s build identity. Calling both things “context” prevents the reader from knowing which information the sentence denies.

“Grants” adds another undefined operation. There is no special detached-receipt admission path implementing this denial. The defensible point is that extracting the receipt does not make it independently identify its producing build. That is a limitation on the information retained with an extracted object. The sentence presents it as though the receipt were an authority capable of granting something.

“Example: a wrong nonce refuses the receipt even inside a current reply” is the paragraph’s most emphatic sentence and its least accurate one. “Even” appears intended to establish that matching build identity does not excuse invalid contents. That distinction is valuable. But “current” must mean a matching producer contract, rather than recency or completed validation, and the example must actually demonstrate the second check. This one does not.

“Wrong nonce” also collapses two different failures. A malformed nonce in the request causes request refusal before capture. A nonce in the worker’s capture that differs from the requested nonce causes the host to construct an `unavailable` receipt with reason `capture_nonce_mismatch`. That receipt is published. Its bytecode and associated capture fields are withheld. The result is not accurately described as “refusing the receipt.”

The grammar makes the nonce the refusing agent, which might pass as shorthand if the responsible component and consequence were otherwise clear. Here those are exactly the facts omitted. Does the host reject worker data? Does the controller reject the enclosing reply? Does it discard only the receipt? Does the specimen fail? The sentence gives the reader no way to distinguish those outcomes.
