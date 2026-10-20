# Direct Python start acceptance

Implementation of [DIRECT-PYTHON-START-PLAN.md](../DIRECT-PYTHON-START-PLAN.md),
assessed on 2026-10-20. Changes remain uncommitted on
`9d654f96188e0afa62d31de9744f521288b82f67`.

The three shell entry points resolve the selected developer directory's
Python independently. The lock front end witnesses the five environment
variables without removing them; the command-line owner and session start
refuse missing or changed witnesses. Request transport and restoration are
removed. Nested front ends witness their own environment, and the tool
wrappers use the direct interpreter. The provenance record retains its
existing shape. Documentation, generated build accounts, worker identity,
fixture copies, mutation anchors, and the subsequent guard plan agree.

## Acceptance evidence

All paths under `tests/out/` below are gitignored evidence available only in
this local checkout. The acceptance directory contains console transcripts,
the final implementation patch, source hashes, artifact hashes, and the
post-test verification.

| Check | Result | Evidence |
|---|---|---|
| Fresh signed build, `PW_FRESH_BUILD=1` | Passed; full XPC and inspection build, eight thin arm64 executables | [Build transcript](../tests/out/runs/direct-python-default-20261020-08/acceptance/build.log) |
| Full default battery, including all eight source-drift cases and the 50 build-provenance controls | 198/198 passed; zero skips | [Run](../tests/out/runs/direct-python-default-20261020-08/run.json) |
| `preflight/build_refusal_controls` | Passed; 85 controls and 13 bypass demonstrations | [Run](../tests/out/runs/direct-python-refusals-20261020-07/run.json) |
| `preflight/signed_artifact_controls`, `preflight/build_guard_controls`, `preflight/build_toolchain_switch_controls` | 3/3 passed; zero skips | [Run](../tests/out/runs/direct-python-final-controls-20261020-09/run.json) |
| Cargo tests under the checkout lock | 345 passed, zero failed; three explicitly ignored tests | [Transcript](../tests/out/runs/direct-python-default-20261020-08/acceptance/cargo.log) |

The two ignored controller tests require Swift driver receipts; the ignored
observer test requires the committed log archive. Their corresponding
default `runner_unit` and `witness_contract/log_query_predicate_archive`
cases execute them with those inputs.

Accepted managed runs have no skipped or unrun cases, harness errors, or
reported system-sleep overlap. Their artifact-integrity reports record the
app as valid before execution and unchanged afterward.

Commands were run outside the restrictive automation sandbox, with
`SDKROOT`, `CPATH`, `LIBRARY_PATH`, `MANPATH`, and `PYTHONOPTIMIZE` unset:

```sh
env -u SDKROOT -u CPATH -u LIBRARY_PATH -u MANPATH -u PYTHONOPTIMIZE \
  make build PW_FRESH_BUILD=1 \
  IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'

env -u SDKROOT -u CPATH -u LIBRARY_PATH -u MANPATH -u PYTHONOPTIMIZE \
  tests/lib/checkout_lock.sh -- cargo test --manifest-path controller/Cargo.toml

env -u SDKROOT -u CPATH -u LIBRARY_PATH -u MANPATH -u PYTHONOPTIMIZE \
  PW_APP_DIR="$PWD/dist/PolicyWitness.app" \
  PW_TEST_OUT_DIR=tests/out/runs/direct-python-default-20261020-08 \
  tests/run.sh

env -u SDKROOT -u CPATH -u LIBRARY_PATH -u MANPATH -u PYTHONOPTIMIZE \
  PW_APP_DIR="$PWD/dist/PolicyWitness.app" \
  PW_TEST_OUT_DIR=tests/out/runs/direct-python-refusals-20261020-07 \
  tests/run.sh --case preflight/build_refusal_controls

env -u SDKROOT -u CPATH -u LIBRARY_PATH -u MANPATH -u PYTHONOPTIMIZE \
  PW_APP_DIR="$PWD/dist/PolicyWitness.app" \
  PW_TEST_OUT_DIR=tests/out/runs/direct-python-final-controls-20261020-09 \
  tests/run.sh --case preflight/signed_artifact_controls \
    --case preflight/build_guard_controls \
    --case preflight/build_toolchain_switch_controls
```

## Source and artifact identity

The [source snapshot](../tests/out/runs/direct-python-default-20261020-08/acceptance/source.json)
and [patch](../tests/out/runs/direct-python-default-20261020-08/acceptance/changes.patch)
were captured before the full default battery. The 864-entry source map has
SHA-256
`b76e6a5dac840e0077ad01270f0003bca38964eb2ffa455653a689fad2e3984b`.
Its digest covers the canonical JSON map of paths, contents, file modes,
and symlink targets. This acceptance note was added afterward.

The [post-test comparison](../tests/out/runs/direct-python-default-20261020-08/acceptance/verification.json)
found no source, signed artifact, or recorded provenance-input changes.
The fresh build preceded only test-control corrections; no production or
build input changed afterward. This applicability statement is a review
judgment, separate from the mechanical hash comparison.

One reviewed reuse exception applies to the refusal run: the independent
`source_drift/direct_python.py` checker was strengthened during that run to
cover shell continuations and multiline arguments. The refusal case does
not execute that checker; its build, wrapper, and refusal-control inputs
remained unchanged. The final default battery executes the strengthened
checker. The other three opt-in cases were rerun after all test edits.

The ZIP SHA-256 is
`ee56ba87e9102412016c3831eff7de268573e235123f0ba9d12043129a6891fb`;
the worker identity is
`415f9092643e8d4aed3cd963f963add208826d0905d3b0b6f87b0a5f8572e112`.
The [artifact hash list](../tests/out/runs/direct-python-default-20261020-08/acceptance/artifacts.json)
also identifies the sealed manifest and provenance record.

## Observations and corrected controls

The plan's historical statement that `/usr/bin/make` adds nothing did not
hold on this machine: it added `MANPATH`, while the selected developer
directory's own `make` did not. The
[environment observation](../tests/out/runs/direct-python-default-20261020-08/acceptance/make-environment.json)
records that comparison. The fresh build correctly records `MANPATH` as
set in `build.sh`'s starting environment, and `SDKROOT`, `CPATH`, and
`LIBRARY_PATH` as unset. The default battery starts directly through
`tests/run.sh` with all four unset.

Earlier failed and interrupted runs remain in `tests/out/runs/`. The
focused runs exposed and corrected fixture environment assumptions, resolver
ordering before `testlib.sh`, and the new source-drift case's shell wiring.
The first opt-in run (`direct-python-build-controls-20261020-06`) exposed an
incorrect negative-control premise: the system Python shim preserves an
explicit SDK request without necessarily inserting `CPATH`. The corrected
control observes a safe default shim environment, isolates the `CPATH`
witness mismatch, and passes in the complete refusal rerun. Those earlier
failures are not credited as passing evidence.

No accepted execution reproduced a developer-tools installation request.
The resolver's contained invalid-directory controls and invalid SDK control
also assert its absence. Environment preservation is checked against a
deliberate shim-start negative control, including raw bytes, empty and unset
values, trailing newlines, and a wrapper interpreter path containing spaces.
