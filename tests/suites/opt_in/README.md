# opt_in

Catalog group containing every non-default case, including signing, BYOXPC,
mutation controls and exploratory worker-resource observations. See `tests/OPT_IN_TESTS.md` for requirements.

Inspect with `tests/run.sh --suite opt_in --list`; execute with
`tests/run.sh --suite opt_in`. `--all` also includes these cases. Missing required
resources fail with explicit unrun selections; skip policy belongs to each case.

Artifacts use each case's canonical suite and ID, not an `opt_in` report alias.
