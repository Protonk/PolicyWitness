# Developer read input

`read.json` is the identity-free body embedded by [test_input.rs](../test_input.rs).
The publisher validates its fixed structure, inserts the compiled contract and
replaces the query and attempt targets positionally. Caller text, including
`$EFFECT`, is preserved verbatim. Publication neither inspects the target nor
runs the request. Fixtures and expected results belong to the test harness.
The body is an explicit input of [build_contract.py](../../../docs/build_contract.py).
