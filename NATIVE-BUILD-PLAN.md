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

`build.sh` refuses, before the checkout lock front end and before any Python
runs, unless both hold:

- the machine is Apple Silicon: `/usr/sbin/sysctl -n hw.optional.arm64`
  prints `1`;
- the build is not translated: `/usr/sbin/sysctl -n sysctl.proc_translated`
  prints `0`.

Both are read by the script's own shell, as the admission row's other checks
are. A Rosetta-translated process still reads `hw.optional.arm64` as `1` but
`sysctl.proc_translated` as `1`; on an Intel Mac the first value is absent.
An absent, empty or other value refuses: the build never proceeds on an
observation it could not make. One refusal row covers both facts, with
status 2 and a message naming each value read, for example `this build runs
only natively on Apple Silicon (hw.optional.arm64=<value>,
sysctl.proc_translated=<value>)`.

What the rule establishes is limited to what it reads. `sysctl.proc_translated`
describes the process that asks; `sysctl` launched from a native shell runs
natively, and so do the universal tools the build starts, while a tool that
was installed with only an x86_64 slice would still run translated. The
record already carries the evidence for the two that matter, rustc's host
triple and Meson's build machine; the rule adds no further probes and no
record field. A `make` run under Rosetta starts `build.sh` translated and is
refused the same way.

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
  machine. Keep its host assertion and the explicit `-arch` and Swift
  `-target`: they are the output target's configuration rule and cost
  nothing on a native build.
- The arm64 cross build in `control_meson_target` and in the `source_drift`
  Meson control. The x86_64 cross file stays as the technique that produces
  the `meson_target` refusal; it is no longer a documented workflow.
- `control_translated_builder` as a passing control. It becomes the control
  for the new refusal (below).
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

## Current versions only

Each reader accepts the current version and refuses the rest. Remove:

- In [build_provenance.py](tests/lib/build_provenance.py),
  `HISTORICAL_SCHEMA_VERSIONS`, the per-version record shapes and
  `read_zip_record`'s `historical` parameter; in
  [release_runs.py](tests/lib/release_runs.py), the historical read and the
  acceptance of an archive whose release record has no `provenance` object.
  Archive verification then refuses the local `dist/archive/` releases made
  before the current record (v0.2.7 to v0.3.1). They stay on disk untouched;
  nothing in this plan deletes release material.
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

Extend the existing equipment and register what the new refusal needs:

| Control | Required result |
| --- | --- |
| Native success | Fresh full and partial builds pass on this Mac; a fresh signed candidate passes inspection and the default battery. |
| Translated build refused | The unchanged script under `arch -x86_64 /bin/bash`, and `make build` under `arch -x86_64`, refuse at admission naming `sysctl.proc_translated=1`, with no lock taken, no session, cache or distribution change and no tool run. Needs Rosetta: declare it as the case's equipment; its absence is an equipment failure, not a pass. |
| Unconfirmed machine refused | The script under a sandbox profile that denies reading `hw.optional.arm64` (the value reads empty) refuses the same way. There is no Intel Mac here: the value `0` and an absent sysctl are established only through this unreadable-value control and the code, and the record says so. |
| Guard sensitivity | The check removed lets the translated build proceed; the check moved after the lock front end lets the lock be taken first; either fails its control. |
| Current versions | The archive reader and release verification refuse a schema 1 record and an archive without a provenance object; the current record still verifies end to end through the release controls. |
| Worker wait | Identity regenerated; `runner_c_worker_harness`, the default battery and the opt-in `witness_contract/order_barrier_mutations` pass. |

Run `source_drift`, the generators' checks, `build_provenance_controls`,
`dispatcher/artifact_controls` and the release controls offline, then the
opt-in `build_refusal_controls`, then the default battery against a fresh
signed candidate. Record the equipment and the run IDs as the previous plan's
record does.

## Documentation and generation

Update [docs/build.json](docs/build.json) with the new admission refusal and
its controls and regenerate the build account; remove the rows' and steps'
wording about builders and cross files. Update BUILD.md, README.md,
SIGNING.md, the preflight and `source_drift` READMEs, the opt-in registry and
the catalog together. State the rule positively where the old text explained
other builders; do not leave notes about what used to be supported.

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
