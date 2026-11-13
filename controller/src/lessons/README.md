# Request lesson inputs

`create.json` and `capture_typo.json` are identity-free teaching inputs embedded
by [lesson.rs](../lesson.rs). The emitter inserts its binary's contract and the
caller's absolute target at the query and attempt operands marked `$EFFECT`.
The typo input deliberately carries an unknown capture field; neither supplies
a nonce. Publication does not perform request admission or execution.

The request-contract test corpus references these files while keeping expected
refusals separately authored. Its Python and Swift loaders supply their own
identity and target substitutions. The guide and developer lesson acquire
requests from the installed command. The public build identity includes both
files explicitly in [build_contract.py](../../../docs/build_contract.py).
