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
observation it could not make. Exit status zero with empty stdout still
refuses because the required value was not observed. Nonzero probe exits must
reach this diagnostic rather than exit through `set -e`; represent an empty
or unavailable value explicitly. One admission refusal,
`native_builder_required`, covers both
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

### Schema-2 release evidence

Keep the default release controls independent of ignored `dist/archive/`
material. In `check_release_publish.py::prepare_provenance_fixture`, put
these independent literal strings into the generated schema-2 record before
it is written into the synthetic ZIP and archived evidence:

```json
{
  "meson_machines.note": "Meson's host machine is the platform the native products are configured for; its build machine is where Meson reported compiling, a toolchain fact that is not constrained",
  "output_target.note": "the fixed target every shipped executable must satisfy, observed per output below; it describes the products, not the machine or processes that built them, and makes no claim about translation"
}
```

These keys identify the `note` fields of the two objects under
`configuration`; they are not new dotted keys in the record. Do not import
the strings from the production writer. Keep the fixtures' synthetic
v0.9.0/v0.9.1 stamps and generated Mach-O members. In
`preflight/release_publish_controls`, verify the complete generated archive
with `release_runs.verify_release` and assert that both the ZIP member and
archived provenance copy retain these exact note values. This establishes
schema-2 acceptance with the original note text, not verification of a
historical release. No extracted v0.3.2 files are added to Git, and no local
archive requirement is added to the default cases.

Separately, during implementation, run the updated
`release_runs.verify_release(Path('dist/archive/v0.3.2'))` once in the
checkout that holds the complete local archive. This read-only check needs
the original release.json, ZIP, guide, SHA256SUMS, archived provenance and
portable test evidence bundle; a copied provenance record alone cannot
satisfy it. Record the command, reader source snapshot, archive path,
status and diagnostics, plus hashes identifying those inputs and the
bundle's manifest, in the implementation evidence outside the default
release controls. Preserve the archive unchanged. If it is unavailable in a
worktree or fresh clone, leave this local observation outstanding until it
can run in the owning checkout; the generated-fixture result does not earn
that credit, and default tests still run without the archive.

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
  timeout, launch error or another value means missing `rosetta` equipment,
  without installing it.
  Only the new translated case requires `rosetta`. Remove the old control's
  optional-success return. A selected case without Rosetta is an equipment
  failure with an unrun case, not a skip or pass. Add dispatcher controls for
  the new requirement and for the general refusal case remaining runnable
  when Rosetta is unavailable; neither case depends on the other.
  In `tests/suites/dispatcher/check_selection.py`, run a disposable dispatcher
  fixture under one sandbox profile that denies execution of `/usr/bin/arch`.
  Select a harmless case requiring `rosetta` and an independent harmless
  sibling without that requirement. Use the real equipment probe: retain its
  execution-denial diagnostic (including a launch error if the subprocess API
  reports one rather than a shell status), require the Rosetta case to be
  unrun with missing `rosetta` equipment, and require the sibling's execution
  receipt and passing result. Also assert that the real catalog's
  `build_refusal_controls` has neither a `rosetta` requirement nor a dependency
  on the translated case.
  Do not run the real refusal suite inside this simulation: its own sandbox
  controls would require nesting. The denied launch is evidence of equipment
  failure handling, not evidence that Rosetta has been uninstalled.
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
  no lock was taken. Use the single combined profile described below for that
  subcase. Preserve the holder's evidence; never unlink its lock.

### Combined containment for the invalid-SDK control

Extend `shim_probe.profile_text()`, `prepare()` and `run()` with an optional
`extra_rules=()` argument, preserving existing behavior when it is empty.
For `control_unconfirmed_machine`'s invalid-SDK subcase, supply only the fixed
rule denying reads of `hw.optional.arm64`. The helper appends it to its usual
mach-lookup and write restrictions before writing `contained.sb`. This is an
internal test option for fixed restrictive rules, not a CLI or environment
interface for arbitrary policy. The control does not write or alter the
profile itself and does not wrap the returned prefix in another sandbox.
Call `prepare()` from the test parent before entering any control sandbox.

`prepare()` must validate the final combined profile before returning its
prefix. Keep its outside-DSCL success, inside-DSCL failure and permitted-command
success checks. For this extra-rule mode, also capture the two sysctl probes
outside and inside that same profile, with SDKROOT and DEVELOPER_DIR absent.
Require both outside probes to exit zero with values `1` and `0`. The inside
shell must run to completion, reporting the status, stdout and stderr of each
probe: require the arm64 query to exit zero with empty stdout, while the
translation query exits zero and prints `0`. This accepts the observed
blocked-read behavior as valid control setup; the build guard must then
refuse its missing arm64 value despite the query's zero exit status.
An apply/exec failure or incomplete probe cannot count as the expected empty
sysctl. Retain all raw checks in `containment.json`; return no prefix if any
gate fails. Only after this startup validation may the caller put the invalid
SDKROOT in the build child's environment and launch it under the returned
single `sandbox-exec` prefix. Keep the prepared profile unchanged through the
unchanged-script run, displaced-guard run and restored-script repeat.

Extend the helper's controls in `preflight/build_provenance_controls`
(`check_build_provenance.py`) for the combined profile: successful startup
with an arm64 read that exits zero and prints nothing alongside the
successful translation read, preservation of the existing containment gates,
and constructed observations with missing records, wrong values, nonzero
statuses or incomplete probes that stop both `prepare()` and `run()` before
dispatch. Rejecting
a constructed nonzero result here tests the setup gate, not the build guard's
handling of a real failed sysctl. Keep the existing plain-profile,
exec-restriction and nested-sandbox refusal tests. The build-refusal mutation
phase must then show the original guard's builder refusal and the displaced
guard's SDK refusal, under identical
combined containment, with raw diagnostics and installation-request detection
retained.
SDK checks in the Rosetta case use the ordinary shim-probe profile with
`arch` as the command inside it; they do not add a second sandbox either.

### Required observations

The case results must establish these observations:

| Control | Required result |
| --- | --- |
| Native success | Fresh full and partial builds pass on this Mac; a fresh signed candidate passes inspection and the default battery. |
| Translated build refused | In `preflight/translated_build_refusal_controls`, the unchanged script under `arch -x86_64 /bin/bash`, and `make build` under `arch -x86_64 /usr/bin/make`, refuse naming `sysctl.proc_translated=1` in both variants. With SDKROOT unset or valid, observe the script's refusal, empty wrapped-tool receipts, unchanged session/cache/distribution inventories and refusal ahead of the independently held lock. Make's earlier shim/SDK work is allowed. |
| Admission precedence | Exercise direct `--help`, an unknown argument, bad knobs, missing tracked inputs and an invalid SDKROOT alongside an unreadable sysctl, and alongside translation in the Rosetta case: the builder refusal wins. On an admitted native shell, retain the existing precedence. For make with an invalid command-line SDKROOT, require the parse-time SDK refusal and no entry into build.sh. The unreadable-sysctl plus invalid-SDK subcase uses the helper's validated combined profile; all SDK fault subcases use one contained shim-probe invocation. |
| Unconfirmed machine refused | In `preflight/build_refusal_controls`, the unchanged script under the sandbox profile refuses the zero-exit, empty-output `hw.optional.arm64` observation while `sysctl.proc_translated` exits zero and prints `0`, with the same receipt, inventory and lock-boundary checks in both variants. This exercises the empty-value path only. Refusal of an arm64 value of `0` or a nonzero sysctl exit (including an unknown OID) rests on guard-code review; neither a real failing build probe nor an Intel execution is established by this control. Record that limit. |
| Guard sensitivity | Removing the guard, moving it past Python/SDK setup or moving it past the lock front end fails `control_unconfirmed_machine` in `demonstrate_bypass`, without Rosetta. The restored script passes the same control. |
| Current versions | The archive reader and release verification refuse a schema 1 record and an archive without a provenance object. Complete generated schema-2 archives with the original note literals verify through `preflight/release_publish_controls`, without local release material. Verification of the complete local v0.3.2 archive is a separate recorded implementation check; the shell rule is not retroactively imposed on its recorded toolchain. |
| Worker wait | Identity regenerated; `runner_c_worker_harness`, the default battery and the opt-in `witness_contract/order_barrier_mutations` pass. |

Run `source_drift`, the generators' checks, `build_provenance_controls`,
`dispatcher/artifact_controls`, the dispatcher equipment controls and the
release controls offline; separately record the local v0.3.2 verification
described above. Then run the opt-in `build_refusal_controls` and,
separately on equipped hosts, `translated_build_refusal_controls`, then the
default battery against a fresh signed candidate. Record canonical case IDs,
equipment, source snapshots and run IDs. Keep scratchpad observations distinct
from credited test runs; this plan does not claim that these tests have run.

## Documentation and generation

Update [docs/build.json](docs/build.json) with the new admission refusal and
its controls and regenerate the build account; align the admission order,
make-entry scope and shortened Meson diagnostic. Update build.sh's header,
BUILD.md (including its `--help` statement), README.md, SIGNING.md, the
preflight, dispatcher and `source_drift` READMEs, the test equipment and
shim-probe references, the opt-in registry and the catalog together. State
the rule positively where the old text explained other builders; preserve
the provenance field meanings above and do not leave notes about what used
to be supported.

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
