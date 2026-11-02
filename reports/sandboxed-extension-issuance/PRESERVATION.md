# Archival preservation verification

Preservation was verified offline on November 2, 2026, separately from the
[independent acceptance assessment](ACCEPTANCE.md). This verification checks the
disposition of accepted material; it does not reopen its conclusions.

The original inventory was captured from clean PW commit
`77a9b5880949475ade08eefea8870c3ec84445e3`. Its investigation material is identical
to the reviewed completed-investigation commit
`1de523c8744eafb50302145b0495a70c6f403f50`; the intervening commits concern unrelated
feedback records. The separate acceptance record was committed as
`719a39de334703b70e8793fe4566f47a24985435` before relocation.

The offline checks establish:

- All 503 relocated originals are present under the original-to-archive inventory:
  499 are byte-identical and four narratives have link-destination repairs, with
  one existing trailing space also removed from `PLAN.md`.
  All original evidence, raw NDJSON, trial/ownership records, source snapshots,
  constructed controls and mutation evidence retain their original SHA-256
  values. Apparatus, driver, reader and control sources are unchanged.
- All 24 planned r1 trial records are retained, one C0–C7 arrangement in each of
  three blocks. Their 2,112 assembled events equal the original NDJSON events.
  No record was substituted, regenerated, or added as a native trial.
- The report, acceptance assessment, final plan, traces, source review, protocol,
  reader account, schedules, checkpoints, and complete evidence tree are present.
- The complete browser packet is byte-identical to its original inventory. Its
  unchanged verifier passes all 32 packaged checksums and 25 upstream Git blob
  identities, including the retained notices and source licenses.
- Changes to original narrative files are limited to the Markdown destinations
  and one trailing space listed in [MIGRATION.md](MIGRATION.md). Normalizing those
  destinations and that space leaves identical original and relocated text.
- All 236 archive-relative navigation links and Markdown fragments resolve. Frozen
  source-snapshot links and checkout-local historical references are explicitly
  accounted for in [LINKS.json](LINKS.json) as 49 historical link occurrences,
  without editing frozen evidence.
- Pinned PW context content identities agree with the source commit's local Git
  objects. Public-hosting availability was not tested. Historical release and
  native-suite evidence remains outside the experiment and separately managed.
- The root plan and both former records directories are retired by relocation.
  No active inbound Markdown link continues to target them. Historical paths in
  archived text and raw evidence remain intentional provenance.
- The new `local/` product location is ignored and excluded from the portable
  inventory. No compiled product is included in either archival commit.
- No production source, registered fixture, suite checker, test catalog, or
  experimental source behavior changed. The repository changes are acceptance,
  relocation, archive documentation/verification, context snapshots and the
  local-product ignore rule.

The portable check is [VERIFY.py](VERIFY.py), run with Python's bytecode output
disabled. It reads the archive and runs only the source packet's original
offline integrity verifier. Additional disposition checks compared original Git
blobs with moved files, reviewed the link-only diffs and staged inventory, and
checked ignored products and retirement paths. These commands did not acquire
the native-test lock, execute native equipment, rebuild or sign binaries, run a
battery, or pursue deferred questions. **No native experiments were rerun.**

Hashes establish correspondence with the included provenance records, not an
external signature over the archive. Standalone users do not need optional
build products or the separately managed historical runs to inspect the accepted
24-trial result.
