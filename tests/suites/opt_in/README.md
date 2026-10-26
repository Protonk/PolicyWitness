# opt_in

Catalog group containing every non-default case, including signing, BYOXPC,
mutation controls and exploratory worker-resource observations. The
[harness selection account](../../README.md#how-to-run) describes membership
and dependencies. [Verification for changes and investigations](../../CHANGE-VERIFICATION.md)
explains applicable controls and their evidence; it is not a complete group inventory.

Inspect with `tests/run.sh --suite opt_in --list`; execute with
`tests/run.sh --suite opt_in`. `--all` also includes these cases. Missing required
resources fail with explicit unrun selections; skip policy belongs to each case.

Artifacts use each case's canonical suite and ID, not an `opt_in` report alias.
