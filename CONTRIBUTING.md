# Contributing to PolicyWitness

PolicyWitness is a research/teaching tool. Contributions are welcome, but “the product” here is not just code — it’s **inspectable behavior** plus the written contracts that explain what that behavior means. Meaning: documentation and tests are part of the product.

## Reach the most integrated test you can

The more integrated the test, the less surface for the test itself to be wrong. End-to-end through the CLI is the most integrated; a `_test_overrides`-driven suite is next; a unit test against an internal helper is the last resort.

## Read AGENTS.md, even if you're a human

Guidance in this repository is aimed at human and non-human agents. Don't assume that the contents of layered agent guidance are for others to worry about; we put useful direction in there.
