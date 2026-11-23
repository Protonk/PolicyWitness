# Reviewing the 0.3.8 trace handoff

The writer finished the trace and its three handoffs on November 23. The next product decision belongs to the guide reader and maintainer. After reading the guide, the maintainer will decide whether a separate reviewer should check the trace judgments against their evidence. [Guide review](../docs/guide/USER-GUIDE-PLAN.md)

## Start with the question under review

- Which decisions still belong to the caller, and when? Start with the [user duties](USER-RESPONSIBILITY-OUTFLOW.md). Compare a duty with the signed observation, the [requirements](../docs/REQUIREMENTS.md) and the passage that teaches it.
- Why does the implementation draw a particular boundary? The [maintainer judgments](MAINTAINER-JUDGMENT-OUTFLOW.md) give the finding identifiers, remedy commits, controls and remaining limits. Follow the identifiers into the original dispositions when the distinction matters.
- What changed, and which build ran which checks? The [release account](RELEASE-ACCOUNT-0.3.8.md) distinguishes the build 1634 trace verification, the build 1666 guide evidence and the acceptance still due on the eventual release ZIP.

## Read the original investigation

Commit `97a859d6bb4a54b93c4af400383bbd65d9961fec` contains the complete tracked investigation in its original layout. The writer counted 135 numbered findings, followed 1,036 assessment-local claim identifiers into dispositions across 34 rows, and checked the reverse path from 14 remedy commits and 32 technical-account settlement commits. Those are the writer's coverage checks. A reviewer can use the following paths at that commit to judge the evidence for any individual conclusion.

| At the checkpoint | What to look for |
| --- | --- |
| `records/DOCUMENTATION-TRACE-REVIEW.md` and `records/contract-trio/` | Original findings, appended reports and their validation provenance |
| `records/trace-assessments/DISPOSITIONS.md` and the lettered assessments beside it | Treatment of each local claim, referrals and reasons for retaining or narrowing it |
| `records/trace-assessments/ACCOUNTS-LEDGER.md` and `ACCOUNTS-ADDENDA.md` beside it | Technical-account settlements and questions left with another owner |
| `records/TRACE-MANAGEMENT-PLAN.md` | Step 4 run identifiers, scope and results, followed by the step 5 writer's check |
| `records/TRACE-CLOSEOUT-PLAN.md` | Original selections, review brief and retention preview |

For a single file, use `git show 97a859d6:records/trace-assessments/DISPOSITIONS.md`. To follow the original links into code, tests and documentation, export the tracked tree to a fresh directory.

```sh
review_dir=$(mktemp -d)
git archive 97a859d6 | tar -x -C "$review_dir"
```

The guide studies and their saved examples remain in the checkout for the reader. Full dispatcher output is gitignored and local. The November 23 prune preview listed 61 eligible development runs and removed none. Applying retention is a separate operator decision and requires a fresh preview. [Test output retention](../tests/AGENTS.md#preserve-and-clean-up-output)
