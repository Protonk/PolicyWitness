# Contributing to PolicyWitness

PolicyWitness is a research/teaching tool. Contributions are welcome, but “the product” here is not just code — it’s **inspectable behavior** plus the written contracts that explain what that behavior means. Meaning: documentation and tests are part of the product.

## Write the most integrated test you can

The more integrated the test, the less surface for the test itself to be wrong. End-to-end through the CLI is the most integrated; a `_test_overrides`-driven suite is next; a unit test against an internal helper is the last resort.

## Read AGENTS.md, even if you're a human

Guidance in this repository is aimed at human and non-human agents. Don't assume that the contents of layered agent guidance are for others to worry about; we put useful direction in there.

`CLAUDE.md` at the repo root and under `runner/` are symlinks to the `AGENTS.md` beside them, so Claude Code loads the same guidance without a branded copy. Edit the `AGENTS.md` files; they are the source of truth.

## Releases

A release is one annotated tag on `main` plus a GitHub release made from it:

```sh
git tag -a vX.Y.Z -m "PolicyWitness X.Y.Z"
git push origin main vX.Y.Z
make notarize NOTARY_KEYCHAIN_PROFILE=<profile> IDENTITY='Developer ID Application: ...'   # see docs/SIGNING.md
gh release create vX.Y.Z PolicyWitness-X.Y.Z.zip SHA256SUMS --title "PolicyWitness X.Y.Z"
```

Nobody edits the version by hand. `build.sh` reads it from the nearest `v*` tag
and the commit count, and stamps the app, the XPC service and every envelope
(`policy-witness --version` prints it). Tag the commit you will ship, then build
from that clean checkout so the stamp carries no distance or `-dirty` suffix.
Copy the final accepted ZIP to the versioned asset name and write `SHA256SUMS`
with `shasum -a 256` before uploading. The contract numbers in
`docs/contract.json` move independently, under the rule in `docs/CONTRACT.md`;
a release never bumps them on its own.
