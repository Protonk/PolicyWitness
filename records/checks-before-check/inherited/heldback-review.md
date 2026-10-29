# B1 held-back and delayed evaluation

Frozen design/open results: `db75edf`. Concrete predictions and unchanged
curator dataset: `152f984`. Evaluation: `replay/heldback.py`, through the
repository Python wrapper. It reads historical trees and writes only its
result directory. Six cases,15 revision states and33 recorded file hashes
were checked. `replay/heldback-results.json` retains actual facts and commands
from corrected equipment revision2; the original result is preserved as
`replay/heldback-results-initial.json`. `curator-review.md` records two initial
equipment gaps and their correction under unchanged B1. The repeated cases
are exposed equipment-development cases, not another independent trial.
No historical test/build was run; none was needed for these input/claim facts.

| Case | Evaluation | Assessment against frozen prediction |
| --- | --- | --- |
| H01 | Existing manifest names a Python definition present at a33b645 and6304fef, absent at e1db41a | Missing referent and both clean pointer negatives, for the stated reason. Exercises existing G4, not novel B1 semantics. |
| H02 | bfae9d4/fcc3558 registered hashes agree;085e23e worker/ABI differ while probe/report remain unchanged and wait name persists | Two conditional represented-input negatives and changed-input review request.972c54b also changes report; no explicit historical-only review supplied, so it remains review-required. |
| H03 | ce08ec1 paragraph hash changes; two code hashes identical | Old baseline stays unreviewed; edit requires review. No false semantic pass at baseline and no claim that B1 discovers wrong wording. |
| H04 | W50/W53 pointers exist; implementation bytes unchanged through143c8a4 removal/narrowing | Object attribution remains semantic exclusion. W53 is legitimate contrasting subject, not automatic proof from shared pointers. |
| H05 | Both test definitions exist. Old adjacent comment promises hash AND metadata while assertion accepts either; corrected tree narrows both to exact hash | Excluded assertion-adequacy class. The historical finder location was imprecise; package uses the verified checker comment. |
| H06 | Worker account adds privacy-consent limitation; no supplied completeness registration exists in either tree | Unregistered, not a clean negative. Partial prior exposure makes this delayed evaluation. No native consent behavior inferred. |

No B1 prediction failed; none was revised after execution. The initial H03
selector and H04 removal verification were incomplete, so only the corrected
equipment establishes those particular parts. The result supports
the stated limited contract, not an assertion that a complete implementation
would discover these relationships automatically or that the exclusions are
unimportant. Adoption reviews for H02 and A remain hypothetical. H03 exposes
why an unresolved record needs a visible support state independent of its
fingerprint state; B1 already has that distinction, so no B2 was introduced.

## Coverage reconciliation

| Claimed/excluded class | Positive / paired negative or boundary case |
| --- | --- |
| Disappeared referent (existing G4) | H01 e1db41a / a33b645 and6304fef |
| Missing identifying evidence | A51487f7 /69c7dfe conditional adopted receipt |
| Changed registered represented support (mode2 proxy) | A f468200, H02 085e23e / corresponding represented baselines |
| Changed registered claim input (mode3 proxy) | P11fddc4 /69c7dfe; H03 adds unresolved-support contrast |
| Same-name semantic change without registered changed input | Excluded: S9 wrong attribution, H04 coarse object relation; both retain existing symbols |
| Coarse/wrong source (mode4) | Excluded: S9 wrong/repaired citations, H04 W50/W53 |
| Check fails to assert claim (mode5) | Excluded: S2 substitute/corrected scopes; H05 stronger/narrowed assertion |
| Wrong source rendered faithfully | Excluded: S6 wrong/corrected manifest text |
| Omitted or unconnected prose | Excluded: S11 bound omitted/disclosed; B contradiction/correction; H06 delayed omitted/disclosed privacy limitation |

This meets the plan's coverage rule without calling excluded or unavailable
inputs clean negatives. Five selected case details were withheld from the
designer until freeze, subject to the contextual-exposure limits recorded in
heldback-predictions.md; H06 is delayed. The curator's selection was independent
of B1, but the executor performed the evaluation, so this is not an independent
implementation verification or a live behavioral study.
