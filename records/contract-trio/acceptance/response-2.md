# Response 2: acceptance pass, dispositions of validation-2

Both concerns from `validation-2.md` are confirmed and corrected in
`final.md`. Neither draft was changed (`draft-1.md` `f77e436a…715c`,
`draft-2.md` `c5a8fd1f…3294`).

- **W-1 (line-605 reading not applied uniformly): corrected.**
  - In the DT-50 trace's "Statements" bullet, two rules (31-steps "Unique
    association" and the 32-lifecycle cardinality conditions) are now listed
    as writing identity as an unqualified `==`. The ownership paragraph is
    named separately as one that fixes a shared procedure and states no
    equality relation.
  - DT-131's "Cost" now says the host applies the association procedure under
    canonical equality while the independent readers apply the same procedure
    under byte equality.
  - DT-135 still quotes lines 605–614 verbatim. It now also summarizes the
    remainder of the paragraph through line 622 (copied blocks fail;
    unexpected, duplicate and null-ID records remain diagnostic evidence; PID
    uniqueness is not an invariant) and notes that the remainder states no
    equality relation either.
  - `response-1.md` overstated this when it said the paragraph was "quoted in
    full". Only lines 605–614 are quoted. That file is left as written, and
    this entry records the correction.
- **W-2 (`transcript_controls` and "run the consumer"): corrected.**
  - The DT-53 trace and DT-132 now say the thirty default cases are
    attributed to the consumer without the oracle by checker file.
  - `runner_validator_failure/transcript_controls` is described as running
    `check.py fixture`, whose `check_fixture` (line 53) does not call the
    consumer. The file calls the consumer only in its CLI mode (lines
    107–114).
  - The 28 / 2 / 26 figures are unchanged. The text now says the catalog lists
    `app` among the requirements of each of the 28.
- **Validator's untraced branch (index outside `regions`): addressed by
  source.** `AuthorityCustody.init` builds one region for every actor index
  whenever the core limit succeeds (AuthorityCustody.swift lines 359–362). If
  the core limit fails, `setupFailure` refuses every launch. `final.md` adds
  this to the DT-61 trace, step 3.

## Disputes

None.
