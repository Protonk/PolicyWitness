# Build natively on Apple Silicon, with current versions only

The intended result is one rule and less machinery: building requires an
Apple Silicon Mac and a build that is not translated, and the repository
carries only the current version of each record and format it reads.
Comparing artifacts or runs of different PolicyWitness versions is the user's
research problem, not something the repository accommodates.

Follow [CONTRIBUTING.md](CONTRIBUTING.md#planning-a-change),
[BUILD.md](docs/BUILD.md) and [tests/AGENTS.md](tests/AGENTS.md) when
executing it. The output target, its gates, the runtime and every specimen
contract stay as they are.

## The builder rule

Put the guard in `build.sh` as the first executable block after
`set -euo pipefail`, before `ROOT_DIR` is computed. It runs before knob
validation, argument handling (including `--help`), the tracked-input check,
`source tests/lib/python_start.sh` and the checkout lock front end. The
guard uses shell builtins and the following two absolute-path probes only;
it refuses unless both succeed with these values:

- the machine is Apple Silicon: `/usr/sbin/sysctl -n hw.optional.arm64`
  prints `1`;
- the build is not translated: `/usr/sbin/sysctl -n sysctl.proc_translated`
  prints `0`.

The script's own shell launches both probes, even if the first fails, so the
refusal can name both observations. A Rosetta-translated process still reads
`hw.optional.arm64` as `1` but `sysctl.proc_translated` as `1`.
An absent, empty or other value refuses: the build never proceeds on an
observation it could not make. Probe failures must reach this diagnostic
rather than exit through `set -e`; represent an empty or unavailable value
explicitly. One admission refusal, `native_builder_required`, covers both
facts in both build variants, with status 2 and a message naming each value
read, for example `this build runs only natively on Apple Silicon (hw.optional.arm64=<value>,
sysctl.proc_translated=<value>)`.

What the rule establishes is limited to what it reads. `sysctl.proc_translated`
describes the process that asks; `sysctl` launched from a native shell runs
natively, and so do the universal tools the build starts, while a tool that
was installed with only an x86_64 slice would still run translated. The
record already carries the evidence for the two that matter, rustc's host
triple and Meson's build machine; the rule adds no further probes and no
record field. Do not add a check on Meson's reported build machine or rustc's
host triple.

Admission precedence is intentional:

| Entry | Result when the builder guard would refuse |
| --- | --- |
| Direct `build.sh`, including `--help`, an unknown argument, a bad knob, a missing tracked input or a bad `SDKROOT` | `native_builder_required` wins, with status 2; usage and the other checks are not reached. On an admitted builder their existing order remains: knobs, arguments, tracked inputs, Python/SDK setup, lock front end. |
| `make build`, with `SDKROOT` unset or accepted by make's SDK guard | A translated make starts `build.sh` translated, and the script refuses as above. Make exits 2 for the failed recipe. |
| `make build SDKROOT=…`, with a nonempty invalid value | The existing Makefile parse-time SDK refusal wins before `build.sh` starts. |

This is a `build.sh` boundary. Leave the Makefile's SDK guard in place:
`/usr/bin/make` is itself a developer-tool shim, and a nonempty `SDKROOT`
makes the Makefile run `sdk_guard.sh` and its `xcrun` probes before the
recipe. Those processes may be translated. The script's guard cannot
prevent them, or an installation request caused by an invalid inherited
`SDKROOT` before `/usr/bin/make` reads the Makefile. Use the existing contained
shim-probe helper for SDK fault controls. Do not describe the make entry as
refusing before all shims run.

For a refused invocation, replace the phrase "no tool run" with **no
invocation of cargo, meson, ninja, codesign or cp**, including version probes:
assert an empty receipt list, not just `no_calls`, which excludes version
probes. Separately, pin the guard's position in `source_drift` so that no
`build.sh`-initiated `xcode-select`, `xcrun`, Python or lock front end can run
before refusal. The five wrappers do not observe those absolute-path
commands. The two sysctl probes, launchers and make's earlier SDK work are
outside the empty-receipt claim. Preserve independent before/after
inventories of the session, caches and distribution; an unlocked file after
exit alone does not establish that no lock was taken.

## What the rule makes unnecessary

Remove, rather than keep alongside the rule:

- The explanations for other builders: in [BUILD.md](docs/BUILD.md), the
  output target bullet's account of translated Meson, unconstrained build
  machines and builders that cannot run the worker; the cross-file
  subsection under native compilation, with its Swift limitation; in
  [README.md](README.md), the sentence that the build does not check which
  machine runs it. Replace them with the rule in the build prerequisites:
  build on an Apple Silicon Mac, natively.
- `meson.build`'s comments about cross files and the unconstrained build
  machine, and the assertion diagnostic's parenthetical `the build machine,
  @2@ @3@, is not constrained`. Keep the host assertion's predicate, shorten
  the message to end at `host @0@ @1@` and remove the unused build-machine
  format arguments. Update the matching `meson_target` message in
  `docs/build.json`, regenerate BUILD.md's refusal table, and update
  `control_meson_target`, `MESON_TARGET_ASSERTION` and the expected diagnostic
  in `tests/suites/source_drift/build.py` together. Keep the explicit `-arch`
  and Swift `-target`: they are the output target's configuration rule and
  cost nothing on a native build.
- The arm64 cross build in `control_meson_target` and in the `source_drift`
  Meson control. The x86_64 cross file stays as the technique that produces
  the `meson_target` refusal; it is no longer a documented workflow.
- `control_translated_builder` as a passing control. It becomes the control
  for the separate Rosetta refusal case below; the general refusal suite
  uses the unreadable-sysctl control for the same refusal.
- The `#elif defined(__x86_64__)` branch and the generic fallback of
  `cpu_relax` in [pw_probe_runner.c](controller/tools/pw_probe_runner/pw_probe_runner.c),
  the only Intel-specific source: an arm64-only worker needs only `yield`.
  This is a worker-identity input inside the phase release wait, so
  regenerate the identity and rerun `witness_contract/order_barrier_mutations`
  although the compiled arm64 code does not change.

Keep Cargo's explicit `--target`, the controller package's target guard and
the recording of overridden target defaults: a configuration file can still
name another target on an Apple Silicon Mac, and a direct `cargo build
--target x86_64-apple-darwin` should still stop.

## Provenance meaning stays unchanged

Keep both sealed note strings in `tests/lib/build_provenance.py` byte for
byte, with their existing meanings:

- `configuration.meson_machines.note`: the reported build machine is still
  "a toolchain fact that is not constrained". Neither the Meson host
  assertion nor the provenance reader constrains that observation, and the
  new shell guard does not inspect it. An x86_64-only tool can still run
  translated after the shell passes admission.
- `configuration.output_target.note`: the product target still "makes no
  claim about translation". It describes output bytes; it does not attest
  that admission ran or that every tool ran natively.

Keep SIGNING.md's account of those fields and add this distinction between
the admission rule and the recorded observations. Do not reinterpret either
note as a native-build attestation, add an admission field, or require
native-valued build-machine or compiler-host observations when reading an
existing record. The schema and the current record's meaning remain at
version 2; this plan needs no provenance schema bump under the changed-meaning
rule in CONTRACT.md. The assertion diagnostic is not part of the sealed
record. These choices preserve v0.3.2 as a current-schema archive.

## Current versions only

Each reader accepts the current version and refuses the rest. Remove:

- In [build_provenance.py](tests/lib/build_provenance.py),
  `HISTORICAL_SCHEMA_VERSIONS`, the per-version record shapes and
  `read_zip_record`'s `historical` parameter; in
  [release_runs.py](tests/lib/release_runs.py), the historical read and the
  acceptance of an archive whose release record has no `provenance` object.
  Archive verification then refuses the local `dist/archive/` releases made
  before the current record: v0.2.7, v0.2.8 and v0.3.0 have no provenance
  object; v0.3.1 has schema 1. v0.3.2 has schema 2 and remains eligible for
  verification under the unchanged schema-2 rules. All stay on disk
  untouched; nothing in this plan deletes release material.
- In [release_cleanup.py](tests/lib/release_cleanup.py), recognition of
  legacy acceptance output (nested dispatcher ownership without a report).
  Output it no longer recognizes is kept with its reason, which is the safe
  direction for a cleanup tool.
- In [SIGNING.md](docs/SIGNING.md), the record's version paragraph, the
  statements about archives made before the record existed, older archives
  without portable bundles and legacy acceptance, and the hand-assembled
  `v2.3.0` and `v0.2.3` examples; the matching rule in
  [dist/AGENTS.md](dist/AGENTS.md) and row text in [dist/README.md](dist/README.md).
- The fixture generations no case reads:
  `tests/fixtures/blackbox_e2e/checker/response15`, `response16`,
  `response21`, `response22` and `tests/fixtures/disposition/response15`,
  `response16`, `response21`, `response22` (no tracked file outside them
  names them except a retention reason). Earlier captures remain in Git.
- The tests that exercise only the removed paths: the historical record
  cases in `build_provenance_controls` and the legacy-acceptance and
  missing-provenance cases in the release controls. Keep each refusal they
  also cover.

## Verification

Register the refusal and its equipment at separate boundaries:

- In `build_refusals.py`, add
  `('native_builder_required', ('full', 'partial'), control_unconfirmed_machine)`
  to `CONTROLS`, backed by the sandbox profile that denies reading
  `hw.optional.arm64`. Register the same variants and control in
  `docs/build.json`. This is the general suite's control for the new refusal;
  it needs no Rosetta.
- Remove `translated_builder` from `SEQUENCES`. Register
  `preflight/translated_build_refusal_controls` as a separate opt-in catalog
  case (`default: false`, `requires: ["rosetta"]`), include it in the opt-in
  group and dispatch it from `tests/suites/preflight/run.sh`. It runs
  `control_translated_builder` for both variants and both entry points, using
  a disposable admission fixture with receipt and inventory checks. It does
  not run the general suite or its successful signed-build setup, and needs
  no app, identity or compiler equipment merely to reach admission.
- Add `rosetta` to the allowed requirements in `tests/lib/test_cli.py` and
  implement its bounded equipment probe in `tests/lib/suite_run.py`:
  `/usr/bin/arch -x86_64 /bin/bash -c '/usr/sbin/sysctl -n sysctl.proc_translated'`
  must exit zero and print `1`. Record the probe's status and output; failure,
  timeout or another value means missing equipment, without installing it.
  Only the new translated case requires `rosetta`. Remove the old control's
  optional-success return. A selected case without Rosetta is an equipment
  failure with an unrun case, not a skip or pass. Add dispatcher controls for
  the new requirement and for the general refusal case remaining runnable
  when Rosetta is unavailable; neither case depends on the other.
- Key the guard-removal and guard-displacement entries in `MUTATIONS` by
  `native_builder_required`. `demonstrate_bypass` therefore finds
  `control_unconfirmed_machine` through its existing `CONTROLS` lookup;
  it does not need to search `SEQUENCES` or run the Rosetta case. Use valid
  knobs, arguments, tracked inputs and SDK selection in the lock-order
  subcase, and independently hold the disposable checkout's lock. The
  unchanged guard must report the unreadable sysctl before reaching the
  front end; a removed guard or one moved past that front end reaches the
  busy-lock refusal and fails the same diagnostic assertion. Retain the
  existing two mutation stages and restored-script repeat. Also move the
  guard just past `source tests/lib/python_start.sh`: the contained invalid
  SDK subcase must catch that displacement by the wrong refusal, even though
  no lock was taken. Preserve the holder's evidence; never unlink its lock.

The case results must establish these observations:

| Control | Required result |
| --- | --- |
| Native success | Fresh full and partial builds pass on this Mac; a fresh signed candidate passes inspection and the default battery. |
| Translated build refused | In `preflight/translated_build_refusal_controls`, the unchanged script under `arch -x86_64 /bin/bash`, and `make build` under `arch -x86_64 /usr/bin/make`, refuse naming `sysctl.proc_translated=1` in both variants. With SDKROOT unset or valid, observe the script's refusal, empty wrapped-tool receipts, unchanged session/cache/distribution inventories and refusal ahead of the independently held lock. Make's earlier shim/SDK work is allowed. |
| Admission precedence | Exercise direct `--help`, an unknown argument, bad knobs, missing tracked inputs and an invalid SDKROOT alongside an unreadable sysctl, and alongside translation in the Rosetta case: the builder refusal wins. On an admitted native shell, retain the existing precedence. For make with an invalid command-line SDKROOT, require the parse-time SDK refusal and no entry into build.sh. Run SDK fault subcases through the contained shim-probe equipment. |
| Unconfirmed machine refused | In `preflight/build_refusal_controls`, the unchanged script under the sandbox profile reports the empty `hw.optional.arm64` and native `sysctl.proc_translated=0`, with the same receipt, inventory and lock-boundary checks in both variants. There is no Intel Mac here: refusal of `0` and an absent sysctl is supported by predicate review, not an Intel execution; record that limit. |
| Guard sensitivity | Removing the guard, moving it past Python/SDK setup or moving it past the lock front end fails `control_unconfirmed_machine` in `demonstrate_bypass`, without Rosetta. The restored script passes the same control. |
| Current versions | The archive reader and release verification refuse a schema 1 record and an archive without a provenance object. Schema 2 still verifies end to end through the release controls, including a preserved v0.3.2 record with its original notes; the shell rule is not retroactively imposed on its recorded toolchain. |
| Worker wait | Identity regenerated; `runner_c_worker_harness`, the default battery and the opt-in `witness_contract/order_barrier_mutations` pass. |

Run `source_drift`, the generators' checks, `build_provenance_controls`,
`dispatcher/artifact_controls`, the dispatcher equipment controls and the
release controls offline, then the opt-in `build_refusal_controls` and,
separately on equipped hosts, `translated_build_refusal_controls`, then the
default battery against a fresh signed candidate. Record canonical case IDs,
equipment, source snapshots and run IDs. Keep scratchpad observations distinct
from credited test runs; this plan does not claim that these tests have run.

## Documentation and generation

Update [docs/build.json](docs/build.json) with the new admission refusal and
its controls and regenerate the build account; align the admission order,
make-entry scope and shortened Meson diagnostic. Update build.sh's header,
BUILD.md (including its `--help` statement), README.md, SIGNING.md, the
preflight and `source_drift` READMEs, the test equipment reference, the opt-in
registry and the catalog together. State the rule positively where the old
text explained other builders; preserve the provenance field meanings above
and do not leave notes about what used to be supported.

## Outside this plan

The same current-versions principle applies to runtime and contract
compatibility this plan does not touch, because removing it changes the
request, envelope or registry contracts and needs their own version handling
under [CONTRACT.md](docs/CONTRACT.md#when-a-number-moves):

- the runner registry's retired kind aliases (`machme`, `debuggable`) and its
  tolerance of older records without issuer read-back
  ([runner_manager.rs](controller/src/runner_manager.rs));
- the request selector's legacy top-level runner fields
  ([runner_select.rs](controller/src/runner_select.rs));
- the envelope's compatibility projections, such as the exec legacy leader
  status ([disposition.rs](controller/src/disposition.rs) and the consumers);
- the validator's legacy per-probe CLI mode
  ([sb_api_validator.c](controller/tools/sb_api_validator/sb_api_validator.c));
- the response-9 capture `tests/fixtures/disposition/a1_known_loss.json`,
  kept as a rejection fixture, and CONTRACT.md's statements about historical
  run formats.

A separate plan should decide those together.
