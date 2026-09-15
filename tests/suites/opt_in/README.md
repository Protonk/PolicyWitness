# opt_in

Catalog group containing every non-default case: signing and BYOXPC tests, plus
exec inheritance mutation controls. See `tests/OPT_IN_TESTS.md` for requirements.

Inspect with `tests/run.sh --suite opt_in --list`; execute with
`tests/run.sh --suite opt_in`. `--all` also includes these cases. Missing required
resources fail with explicit unrun selections; skip policy belongs to each case.

The local `run.sh` forwards to the public command. Artifacts use each case's
canonical suite and ID, not an `opt_in` report alias.
