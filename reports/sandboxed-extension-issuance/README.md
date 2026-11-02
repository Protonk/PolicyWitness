# Sandboxed file-extension issuance

This archive preserves an accepted experiment about file sandbox-extension
issuance by an already sandboxed process and the usable access observed in a
separately sandboxed recipient. Its findings concern the specified apparatus,
policies, signing context and recorded macOS environment.

Start with the [investigation report](REPORT.md) and the separate
[independent acceptance assessment](ACCEPTANCE.md). The [agreed plan](PLAN.md)
records the original design and stopping conditions; it is a completed historical
plan, not an instruction to launch further work. [TRACES.md](TRACES.md) explains
the motivation from the [complete pinned browser source packet](browser-sandbox-sources/README.md).
Those sources do not turn the fixture observations into browser runtime findings.

## Contents and interpretation

- [REPORT.md](REPORT.md), [PLAN.md](PLAN.md), [TRACES.md](TRACES.md), and
  [ACCEPTANCE.md](ACCEPTANCE.md) keep the investigation and its acceptance distinct.
- [REVIEW.md](REVIEW.md), [NATIVE-PROTOCOL.md](NATIVE-PROTOCOL.md), and
  [READER.md](READER.md) describe the apparatus, publications and evidence reader.
- [pilot.c](pilot.c), [run.sh](run.sh), [driver.py](driver.py), [read.py](read.py),
  and [reader_controls.py](reader_controls.py) preserve the executed source bytes.
- [evidence/](evidence/) contains all original observations, equipment records and
  source snapshots, schedules, checkpoints, reader outputs, constructed controls,
  actual-record mutation, and closed accounting. It contains 24 planned trials
  on r1 and no diagnostic native reruns.
- [browser-sandbox-sources/](browser-sandbox-sources/) retains the complete packet,
  including 25 pinned upstream files, original manifests/checksums, verifier,
  selection account and license notices, without changing any packet bytes.
- [pw-context/](pw-context/README.md) supplies the pinned validator implementation
  used for Q2 and identifies further immutable PW references.

Apparatus sources, embedded command lines, absolute paths, and paths within raw
records retain their original checkout layout. The driver and shell entry point
are frozen experimental sources, not maintained archive launch commands. Their
repository-root assumptions have not been rewritten. The source snapshots also
retain their historical Markdown links. Use this README and the repaired
top-level narrative links for archive navigation. [LINKS.json](LINKS.json)
identifies historical link exceptions explicitly.

The earlier `constructed-01` inputs/results remain prebuild history. The final
`constructed-02` run includes source snapshots and is the constructed-control
evidence credited by acceptance. This distinction does not introduce another
native apparatus revision.

## Provenance and original locations

| Identity | Value |
| --- | --- |
| Original apparatus source commit | `6ea196363dd5007f3d98d72424e0ffd044524ddb` |
| Executed apparatus revision | `r1` |
| Signed executable SHA-256 | `67cef267c01dae2002a333ab2a5ddfbeff9f4574e8bc7bd52c3055404b0d017c` |
| Completed investigation commit reviewed | `1de523c8744eafb50302145b0495a70c6f403f50` |
| Independent acceptance record commit | `719a39de334703b70e8793fe4566f47a24985435` |
| Archival disposition commit | The Git commit first adding this README and `ARCHIVE.json`; separate from all identities above |

The independent decision was completed and accepted on November 2, 2026. Its
commit records that decision after the experiment. The archival commit preserves
and relocates the material; it is not an experimental execution or source revision.
In a PW checkout its full identity is available with:

```sh
git log --diff-filter=A --format=%H -- reports/sandboxed-extension-issuance/ARCHIVE.json
```

| Original location | Archive location |
| --- | --- |
| `BROWSER-TRACE-INVESTIGATIONS-PLAN.md` | [PLAN.md](PLAN.md) |
| `records/browser-trace-investigations/` | This directory, preserving filenames and evidence organization |
| `records/browser-sandbox-sources/` | [browser-sandbox-sources/](browser-sandbox-sources/) |

[ARCHIVE.json](ARCHIVE.json) records each original path, Git blob identity,
original SHA-256 and archived SHA-256. [MIGRATION.md](MIGRATION.md) records all
link repairs and removal of one pre-existing trailing space in `PLAN.md`.
Experimental conclusions and original evidence are unchanged. No native trials,
builds, signing operations, or deferred investigations were performed during
acceptance or preservation.

## Historical context

The following references remain separately managed, gitignored PW checkout-local
context. They were not part of the 24 trials, have not been copied into this
archive, and may be unavailable in another checkout or a standalone copy:

- [v0.3.4 release acceptance](../../tests/out/release-acceptance/run-3ab7e31af74345dfa87d1948c56ecb27/),
  associated with `0289d9ae8a78be59f9727e6fc2118b3c9b24bcc1`.
- [Native feasibility artifacts](../../tests/out/runs/workset-native-crossed-01/suites/sandbox_extensions_native/feasibility/artifacts/),
  source commit `8aa74027e78f0b7ab4c859c1ffa85f2b41a8a288`.
- [Release signing provenance](../../dist/archive/v0.3.4/evidence/provenance.json).

The pilot's own retained C0 trials establish its baseline. The accepted findings
do not depend on importing these historical runs into the experiment. References
to `tests/RETAINED.json`, the release tag, and old paths in the plan remain
historical references rather than portable runtime dependencies.

## Offline preservation verification

From any directory, with Python 3, run:

```sh
python3 -B reports/sandboxed-extension-issuance/VERIFY.py
```

Adjust the path to this archive if it has moved. This checks preservation hashes,
trial/NDJSON correspondence and the 24-position inventory, recorded link
dispositions, and the source packet's original offline integrity verifier. It
does not execute the native program, driver, reader controls, or a test battery,
and does not repeat acceptance. [PRESERVATION.md](PRESERVATION.md) records the
archival verification performed.

The optional `local/` directory contains gitignored build products when present
in this checkout. It is outside the portable inventory and is not needed for
verification or interpretation. Apple runtime libraries and the recorded macOS
environment are not distributed here. Further PW context uses immutable commit
links, which require access to the repository or its public hosting; preservation
verification does not fetch them.
