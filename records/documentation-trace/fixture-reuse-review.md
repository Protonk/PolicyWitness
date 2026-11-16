# Fixture delta and evidence applicability

Prepared read-only while default run `20261116T004927Z_ed1d41ef` executes from
source commit `8b5de2b2882d7cb2536d1b42d9109f4b0dfc2855`. No test was run and no
checkout file was edited during this investigation.

The patch at `/private/tmp/documentation-trace-runtime-output-fixture.patch`
changes one identifier in
`tests/suites/preflight/opt_in/build_refusals.py`:
`runtime.OUTPUTS` becomes `runtime.STAMP_OUTPUTS` inside
`control_release_entrypoints_enforce_fresh_mode`. The expression snapshots
the inherited stamp carriers, public snapshot and free-text ratchet before
the fixture replaces authored surfaces. It retains the original assertion
that fixture setup must not erase those inherited history claims. It changes
no mutation, no controlled build script, no marker assertion and no output
preservation assertion.

The old/new file SHA-256 values and source-input membership observations are
in `fixture-delta.json`. This file is selected
by neither `build_contract.inputs` nor the worker identity generator. The
patch therefore requires no native rebuild for this delta alone. Confirm
unchanged actual build/worker identities and app inventory when crediting the
run; source membership alone is not proof of artifact identity.

## Cases to rerun after applying the patch

- `preflight/release_publish_controls` executes the changed function through
  `check_release_publish.py:check_release_entrypoints`, which imports the
  module by path. This is the default case that exposed the failure. The
  corrected function still imports genuine release ancestry, renders its
  minimal fixture, tags it, and exercises the real release preflight subprocess
  and Make entrypoints with its controlled stopping build.
- `preflight/build_provenance_controls` imports the changed module in
  `test_opt_in_mutation_anchors_match_current_sources`, applies `MUTATIONS`
  in memory and checks the script anchors. It does not call the changed
  function, but rerunning supplies current-file import evidence.
- `preflight/build_entry_controls` copies the build generator's declared
  inputs in `build_checkout`, then runs build freshness checks. That
  declaration includes this file through the citations in `docs/build.json`.
- `source_drift/build_documentation` reads this file through
  `generate_build.input_paths` / `load_manifest`. All ten build-rule input
  sets include it through manifest citations; definition checks inspect its
  Python AST. The change does not remove any cited symbol.
- `source_drift/generator_contract` includes the file in the build-generator
  fixtures and in prose-link/citation checking against BUILD. Its output
  ownership and freshness controls should describe the final fixture bytes.
- `source_drift/markdown_reader` parses all tracked Python files in
  `test_only_the_reader_imports_the_parser`, including this file.

Suggested dispatcher selection, listed before execution and assigned a fresh
output directory:

```sh
tests/run.sh --case preflight/release_publish_controls --case preflight/build_provenance_controls --case preflight/build_entry_controls --case source_drift/build_documentation --case source_drift/generator_contract --case source_drift/markdown_reader --list
```

The opt-in `preflight/build_refusal_controls` also invokes the same function
as its `release_entrypoints` sequence. Its other sequences, mutation anchors,
tool forwarding and real signing controls are unchanged. The default
`release_publish_controls` executes the changed sequence without running that
whole expensive opt-in family. `build_toolchain_switch_controls` and
`translated_build_refusal_controls` import other helpers from the file; their
imports and selected paths are unchanged, and they are not default cases.

## Reviewed reuse boundary

The battery finished with 232 passing cases and the one named fixture failure.
Its failed case and raw evidence remain intact. This review governs reuse after
the six replacement cases pass; it does not relabel the original run as passing.
Record the original run ID, source snapshot, signed app/build identity and
actual selected case outcomes; record the replacement run's distinct source
snapshot and outcomes. Credit the rerun above instead of rewriting the old
failure. Explicitly label any reused results as a reviewed exception for this
one-file, one-identifier delta.

The source search covered hidden paths and opt-in directories while excluding
build products, test output, Git internals and historical records. It found
only this live stale contract OUTPUTS caller. Remaining OUTPUTS and positional
indices belong to porcelain/interface generation. The two runtime.assemble
callers already expect a dictionary keyed by runtime.CONTRACT. The retained
baseline capture script describes the initial API and is not a current test.

Declared-input inspection found this file only in the build generator's
input set, not contract, worker identity, limits, architecture, footprint,
porcelain or interface generator inputs. No source-drift check.py rule input
included it. The planner's additional native fixture inputs exclude it too.
The direct-Python-start control inspects shell entrypoints and three wrapper
files, not this Python leaf. Native-policy controls import generate_build for
Meson parsing but use the raw manifest and Meson text; they do not load its
citations or this Python module.

Other application/runtime cases use unchanged harness paths and the same
signed app. This statement rests on the exact diff and inspected call/input
paths, not on app independence or file hashing as a universal dependency
proof. Revisit this review if any additional file changes, another failure
appears, the app inventory changes, or a case's source assumptions are unclear.

## Final disposition

The one-identifier repair was committed as `26273563`. All six named cases
passed in run `20261116T011640Z_670555a8` from that clean commit, with no skips,
unrun cases, harness errors or system sleep. The original run remains failed.
The accepted ledger uses these six replacement credits, 227 unaffected default
credits and four additional runner-case credits from the earlier selected run.
The latter 231 credits are explicitly reviewed reuse for this exact delta.
The final app file-mode/hash comparison matched the unchanged app inventory
after both native runs; build and worker identities also remained unchanged.
