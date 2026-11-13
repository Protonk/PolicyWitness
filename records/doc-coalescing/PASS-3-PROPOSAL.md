# App-owned request lesson: acquisition decision

Prepared at `71d4d2a6` for Pass 3 of
[DOC-COALESCING-PLAN](../../docs/DOC-COALESCING-PLAN.md). The maintainer accepted
the recommended separate `lesson` command. The following records the selected
interface and migration; implementation verification is pending.

## Recommended interface

Add these two forms to the current CLI:

```sh
policy-witness lesson create --target /absolute/path
policy-witness lesson capture_typo --target /absolute/path
```

Keep `example`'s no-argument read-hosts specimen and its same-build admission
promise. `lesson` publishes teaching inputs, including one deliberately refused
input. These two selectors supply the current exercise; they establish no
general catalog or design for the future `policywitness help` command.

The alternative is `policy-witness example --lesson create --target /absolute/path`
and its `capture_typo` form. It saves a top-level name but revises the current
promise that every argument to `example` is refused, and requires separate
publication/admission meanings for its two forms. The maintainer chooses the
acquisition interface before implementation.

For either interface:

- The emitter accepts exactly one supported selector and one target argument.
  The target must be a nonempty, absolute UTF-8 path without NUL. Preserve it
  verbatim in the query and attempt. Do not inspect the filesystem, normalize
  paths, create directories or certify target absence.
- Emit one pretty JSON object followed by one newline, carrying the binary's
  `BUILD_CONTRACT`. Use specimen ID `request-grammar` and step ID `create` for
  both inputs. `capture_typo` adds `capture_compiled_profiel: true`; neither
  input supplies a nonce. Materialize JSON values through serialization.
- Exit 0 means complete publication including a successful flush. It does not
  certify admission or effects; `run` performs admission independently. Usage,
  target, empty/`unbound` identity, rendering and write/flush failures exit 2;
  discard stdout on failure. Diagnostics use stderr when writable.
- Emission reads no external file and launches no process. Keep target-absence
  guards and independent effect observations in the user workflow. No content,
  formatting or label stability between builds is promised by these materials.

## Migration after the decision

1. Place two identity-free JSON templates under `controller/src/lessons/`, embedded
   by a small controller materializer. Add their paths to the public build-identity
   inputs: the current suffix inventory excludes JSON. Cover template changes in
   identity and fixture-input checks; do not rely on `include_str!` alone.
2. Replace only the corpus's `create` and `capture_typo` request bodies with
   source references. Python and Swift fixture loaders resolve those references;
   their identity/effect substitution remains independent. Keep expected code/path
   data, unrelated malformed inputs and the separately constructed typo control.
3. Make REQUEST-GRAMMAR and the standalone guide acquire both inputs from the
   installed app. Remove the guide's create heredoc, initial typo-construction
   recipe and the developer lesson's manual alignment instruction. The remaining
   developer corpus still uses its repository renderer.
4. Preserve saved filenames, work-directory preparation, failure-status checks,
   absence guards, independent file observations and the compiler helper input.
   Use macOS's `/usr/bin/plutil` for structured spelling repair, nonce insertion
   and BYOXPC selection/target changes so downstream recipes do not depend on
   printed layout or acquire Python, jq or checkout prerequisites.
   Keep the missing-nonce refusal and independently generated nonce exercise.
5. Update the guide fence executor's acquisition selectors and preserve its
   independent request/effect/refusal assertions. Account for the changed specimen
   ID in downstream consumers. Update the CLI reference and authored emission
   contract, regenerate owned outputs, and inspect public scope and dependencies.

## Verification and completion

Review edits before one signed build and one combined dispatcher selection:
`unit`, `integration`, `source_drift`, `runner_unit/pwrunner_core_unit_executable`,
`runner_outcome_bad_request/accepted_input_contract`,
`witness_contract/guide_workflows` and `witness_contract/example_round_trip`.
Use suite selectors for the first three and case selectors for the remainder;
inspect `--list` first. Guide execution requires its documented GUI, signing and
empty-registry equipment, and owns any installed runner through verified cleanup.

Unit and integration controls cover both exact materializations, escaping,
argument/target/identity refusals and incomplete output. Existing Swift and
CLI/direct-XPC controls retain independently authored admission expectations;
guide execution observes actual emitted inputs and external effects. Confirm the
old example still meets its promise. Reuse no native result merely because a
schema stayed unchanged. Review and prune disposable evidence after acceptance;
use no extra worktree. This preparation has run no tests or builds.

Two narrow Sol reviews mapped the existing consumers and compared acquisition
interfaces. Astra accepted the proposal with the standalone-tool clarification
above. Proposal links and referenced catalog cases were checked; these are
preparation checks, not execution evidence for the proposed command.
