# Documentation tracing acceptance

Completed on 2026-11-15 (local time; run IDs use UTC). The accepted source is
`2627356390835d47910eeb22c75ac6765b043e88`. The final handoff commit adds only
this acceptance record, its transcribed evidence and the plan's completion
status. It changes no tested implementation, generator, fixture or permanent
documentation.

## Result and preservation

REQUEST and RESPONSE teach declaration/admission and returned evidence.
ARCHITECTURE carries the seven complete protocol subjects. The four tours link
their mechanisms to commitments, and CONTRACT supplies tracing, identity,
shared definitions, history and support. The editorial review and three bounded
source traces are separate from the newly executed verification below.

The final baseline comparison accounts for every local/shared public difference:

- `33806e55` removes 32 authored `part` facts, represented by 203 local/shared
  payload occurrences. Placement metadata now belongs to the presentation map.
- `fccf93ae` corrects only `actors.phase.order`'s `free.effect`, including its
  seven shared imports, to describe existing skip/reap/continue behavior and
  its cancellation gates.
- `81dc9158` replaces `wire.standalone`'s positional reference with a named
  canonical link to the validator protocol.

No runtime behavior or JSON shape changed. Shape goldens, free-text counts,
stamp-table bytes, interface artifacts, porcelain schema and the ABI layout
golden equal the starting baseline. The guide and its staged copy are identical
to the starting guide, SHA-256
`1e886e4ab5ccaf9aa73fe9c7d6e47e87bcf37d3d3c8caf2e093f38bced97d64d`.
`final-preservation.json` records the direct comparisons and preserved file
hashes; earlier per-change proofs retain the detailed payload differences.

The final history-backed command passed:

```sh
tests/lib/python.sh docs/generate_contract_stamps.py --check --require-history
```

## Signed build and source identity

One signed build ran from clean commit
`8b5de2b2882d7cb2536d1b42d9109f4b0dfc2855`:

```sh
make build IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'
```

It produced version 0.3.7, build 1482, with the full XPC and inspection settings,
using validated existing caches (`PW_FRESH_BUILD=0`). Documentation freshness,
worker-identity checks before compilation and signing, built-worker identity,
native source closure, thin arm64 output checks, evidence generation, signatures
and standalone guide staging all passed. Seven executables and two seals were
verified with the Developer ID chain, team, hardened runtime and secure
timestamps. `signed-build.log` is the captured build transcript.

Build identity:
`development:bdefcb44cb8b799494b555f6ba992e5bbfb58eba8ef980cb805adf15c103fb18`.
Worker identity:
`cc2502d5da48a2a36e0ef73de394536174e32c2b487a2a7b7981e17d83f21659`.

The two authored source-comment edits and three regenerated identity copies are
isolated in `23bbb912`. The only later tested-code change is the fixture API
repair in `26273563`; it selects neither identity's inputs. Both identities
remain equal to the signed build. The full app inventories after the selected
and default runs agree, and a final file-mode/hash comparison found the current
app identical to that inventory. The repair therefore required no rebuild.

## Executed verification

Every selection was inspected with `--list` before execution. All invocations
used the dispatcher and distinct output directories. Build/native work ran
outside the automation sandbox with the selected signing identity. Python was
the repository-pinned 3.14.9 interpreter. `verification.json` records canonical
case IDs, commands or pytest-family configuration, source commits, effective
configuration, run IDs, outcome counts and the app inventory.

| Local run directory under `tests/out/runs/` | Result and use |
| --- | --- |
| `documentation-trace-placement` | Initial `source_drift/build_contracts` failed on an invalid definition ID in a subject/rule commitment list. The map was corrected; retained as failed iteration evidence. |
| `documentation-trace-source-drift` | 10 of 11 cases passed. Canonical authored links were incorrectly checked as source-file anchors; the scoped checker and independent controls repaired this. Retained as failed iteration evidence. |
| `documentation-trace-link-check` | Corrected `source_drift/generator_contract` passed. |
| `documentation-trace-final-controls` | Run `20261116T003408Z_848241b9`: all 28 selected cases passed at clean `8b5de2b2`; zero skips, unrun cases, harness errors or sleep; valid unchanged app. |
| `documentation-trace-default` | Run `20261116T004927Z_ed1d41ef`: all 233 cases completed at clean `8b5de2b2`; 232 passed and one fixture case failed. Zero skips, unrun cases or sleep; valid unchanged app. The failure and its `suite_exit` harness error remain recorded. |
| `documentation-trace-fixture-recheck` | Run `20261116T011640Z_670555a8`: all six replacement cases passed at clean `26273563`; zero skips, unrun cases, harness errors or sleep. |

The 28-case command was:

```sh
IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)' \
PW_TEST_OUT_DIR=tests/out/runs/documentation-trace-final-controls \
tests/run.sh --suite source_drift --case preflight/build_entry_controls \
  --suite runner_abi_layout --suite runner_unit --suite unit
```

It includes all 11 source-drift cases, the new build-entry controls, all four
Rust cases, the runner units and opt-in mutations, and C/Swift layout checks.
Runner core passed 606 tests; all 201 C/Swift layout values agreed without a
golden refresh. Actor-handoff baselines passed and all eight mutations failed
their designated observations. The host-setup oracle sensitivity case retains
its explicit limitation: accepted controlled counterexamples are characterized,
not promoted to product-safety evidence.

The default command was:

```sh
IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)' \
PW_TEST_OUT_DIR=tests/out/runs/documentation-trace-default tests/run.sh
```

Its completed live checks include admission, sandbox application, worker
identity, independent effects, publication interruption, validator degradation,
ordered phases, actor/extension compositions and failure boundaries. Counts are
parent-case outcomes: the legacy-report count is 232 because one additional
case uses the pytest-family engine. The authoritative parent outcomes are
232 pass and one fail.

## Fixture repair and reviewed reuse

The default failure was `preflight/release_publish_controls`, which called the
removed `runtime.OUTPUTS` in its inherited-release-claims snapshot. Commit
`26273563` changes that one identifier to `runtime.STAMP_OUTPUTS`. This preserves
the original CONTRACT/guide carriers plus public/free snapshots and leaves the
history, mutation, controlled-build and no-output-write assertions intact.

The six-case replacement command was:

```sh
IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)' \
PW_TEST_OUT_DIR=tests/out/runs/documentation-trace-fixture-recheck \
tests/run.sh --case preflight/release_publish_controls \
  --case preflight/build_provenance_controls --case preflight/build_entry_controls \
  --case source_drift/build_documentation --case source_drift/generator_contract \
  --case source_drift/markdown_reader
```

This executes the corrected function and reruns the traced import, fixture-copy,
citation, build-rule and Python-AST readers of its file. The dependency review
and exact old/new hashes are recorded separately as `fixture-reuse-review.md`
and `fixture-delta.json`. Other results are credited as an explicit reviewed
exception for this exact one-file, one-identifier change. That applicability
judgment rests on inspected execution paths and inputs; file hashes alone do
not establish complete dependency coverage.

The accepted ledger contains 237 distinct passing cases: the 233 default cases
plus four additional runner mutation/characterization cases from the selected
run. Six credits come from the replacement run, 227 from the default run and
four from the selected run. The original default run remains failed; its one
failed credit is replaced, along with five affected passing credits. No other
case, input or app byte changed. No earlier-build runtime result is substituted
for a required observation on this signed build.

## Handoff and limits

The three tracing exercises and the whole-protocol rereading found no need for
another subject promotion. Useful residuals are long references and explicitly
partial source/interface associations. They are not universal change detectors
or guarantees of behavioral coverage. The guide outflow records the deferred
user explanations while preserving the freeze.

`witness_contract/guide_workflows` was not rerun: its guide and executable
workflow did not change. The wait, release store and query-eligibility
implementation did not change, so the opt-in order-barrier mutation control was
not selected. The publisher/example implementation also remained unchanged;
source traces retain their historical-versus-new evidence distinctions.

No required equipment or planned verification remains missing. This is local
development acceptance, not a release, notarization or publication. Raw test
evidence is gitignored and available in this checkout under the paths above;
it remains eligible for the repository's ordinary retention cleanup. The
committed ledger summarizes it without claiming retained release evidence.
