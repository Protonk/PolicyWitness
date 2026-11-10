# Retained legacy contract reader

Implementation unit for the history guarantees in
[the staging plan](../../docs/CONTRACT-STAGING-PLAN.md).
`docs/contract/history_v0.py` reads the manifest-and-region layout carried by
`v0.3.6`. The current generator remains unchanged; integration belongs to the
single generator entry point.

## Interface and ownership

`surfaces(read)` returns the selected tree's manifest rows after the legacy
manifest validation. `surface_hash(read, row)` computes one returned row's
legacy public digest. Both receive the same callback, where `read(path)`
returns text for a repository-relative path from one selected tree and raises
if that input is unavailable. `MANIFEST` names
`docs/contract_surfaces.json`.

The module imports only standard-library modules. It performs no filesystem
reads itself, has no Git commands, writes no files and catches no missing-input
exception. The caller selects release trees, identifies their layout and owns
the history/removal-row account. It must call `surfaces` and hash every row
using a callback bound to that same tree. An unavailable or unfamiliar released
layout is a refusal in that caller, rather than a skipped release. Retain this
module when the current authoring syntax changes.

The two function bodies preserve the validation and digest operations from
`v0.3.6:docs/generate_contract_stamps.py::manifest` and `surface_hash`, with
only the read interface and manifest function name changed. The new module
does not collect shapes from current source: each row reads its released
goldens through the supplied callback.

## Calculation against the actual release

On 2026-11-10, a read-only Python calculation loaded the old generator's source
directly from Git, loaded the new module from its file, and compared both
implementations against `v0.3.6`. The old implementation received `(root,
tag)`; the new implementation received a callback implemented with
`git show v0.3.6:<path>`. Neither implementation wrote an output.

| Coordinate | Value |
| --- | --- |
| Source HEAD during implementation | `8dfb11522447fc7cf3d9d1ef8c574f45f372140a` |
| Annotated tag object | `6185f923c4d50724518a95b34c6da34d7d6f4cf2` |
| Released commit | `cbf5f298baff0d39a14a58019e779321d08791ad` |
| Released generator source SHA-256 | `6a5957da6637503a56ebdec6ef3212a52469cd837f786b52f811e386953a70e3` |
| Manifest comparison | All thirteen rows equal, including order and metadata |
| Input reads by the retained reader | Twenty-one distinct released paths |
| Digest comparison | All thirteen surfaces equal |

The resulting matching SHA-256 digests are:

| Surface | Digest |
| --- | --- |
| `request` | `fb3db81adbf292fde871c0be03d5ede782468ef9386247694e97c002c02c8e22` |
| `policy` | `29c2491439479b38f99fae027a1c28c9f696df0fa83383843e341cf14824479a` |
| `probes` | `21a25eed6a15c58c72823e439d5d098cc9dae298846605eb7402ec63859c9a60` |
| `actors` | `d5e19568a5de9b7290687b5b91693568be5d4456c817d60c69768dd7c64e56ee` |
| `envelope` | `f017d9ca9372d4aa69f4e373a09ebeee120e831d56512e3543a69e01374d9997` |
| `dossier` | `078ba6f57b909dc46c661cd1133c4d0f94bd625ea1e5a8e1ed22b242d8ac6225` |
| `steps` | `e3715a300a8dc78bc601702f16195111bdcd403cedfd318f602f85b979969df0` |
| `lifecycle` | `9dc59cf7077488c586ff682907a90263aee0830ebf9e8cb6fb7680f6f8119abb` |
| `equipment` | `0aee8e5780ad2dabca49e50d82fdd52228abeafccb6bd5788a6358d4e6e8940c` |
| `profile` | `d6a739beda0ed76f0a195c3cad435e3560547d8049e687a17baf1aedaa0a460d` |
| `transport` | `2531b56639363de223be1012400d21863cdce509e37bfdfcf011bbaa5637f734` |
| `refusals` | `36d565468613b164d79100ee78ac91c3346d16eb860b8624cde0b35f4ecf1ef0` |
| `installation` | `f2e3c7d84e98f4e54369ab80e1f099ecf58fa8fe20fe1d2cc311cce8d01f1c7a` |

The twenty-one inputs were the released manifest, catalog, contract, guide,
all thirteen `tests/fixtures/contract/surfaces/*.json` files, and four
additional goldens: `tests/fixtures/request_contract/examples.json`,
`tests/fixtures/comparison/matrix.json`,
`tests/fixtures/disposition/current/constructed_deadline.json` and
`tests/fixtures/contract/compiled_profile.json`.

This is executed calculation evidence for the released rows and digests.
It supplies neither an integrated generator check nor release acceptance
credit. No test suite, build, notarization or publication ran for this unit.

## Retained validation and canonicalization

The old layout's validation is kept in its original order. Its explicit
`ValueError` messages remain:

| Condition | Message |
| --- | --- |
| Manifest keys differ from `surfaces`, or its value is not a list | `invalid contract surfaces manifest` |
| A row has missing or extra keys, apart from optional `definitions` | `invalid surface fields` |
| ID fails `[a-z][a-z0-9_]*` or repeats | `duplicate or invalid surface id` |
| Goldens or checks are empty | `<id>: missing golden or verification` |
| A named check is absent from the selected tree's catalog suites | `<id>: unknown verification suite` |
| A definition/golden path is absolute or contains a `..` path component | `surface input must be repository-relative` |
| Primary marker pair is absent, duplicated or out of order | `<id>: expected one ordered definition region` |
| Supplementary marker pair is absent, duplicated or out of order | `<path>#<region>: expected one ordered definition region` |

The callback's read error propagates. JSON decoding and malformed-value errors
from the original operations also propagate; the module does not replace
them with a permissive fallback. No current-source catalog, current shape
collector or current authoring tree participates in these validations.

These details are deliberately retained:

- The manifest's `definitions` member is optional. A supplementary reference
  is split at `#` by the original operation; an invalid number of pieces fails
  when the hash is read. The validator does not add a new schema for old rows.
- Marker matching is literal string matching across the entire document.
  Text inside a fence is not treated specially. Whitespace within each selected
  region is collapsed by Python `split`/`join`, including whitespace inside
  examples. Supplementary regions are appended in their manifest order, with
  one separating space per region, including an empty region.
- The primary marker pair itself is excluded; all text within it, including
  any nested comments or citations, participates. Region text outside the
  selected boundaries does not participate.
- Goldens are parsed with the standard `json` decoder and retained in their
  manifest order. The digest input is `json.dumps([definition, values],
  sort_keys=True, separators=(',', ':'), ensure_ascii=True)` encoded as UTF-8.
  This sorts object keys, preserves array order and retains the standard
  decoder's duplicate-key and numeric handling. No extra Unicode
  normalization is applied.
- `artifact`, `checks`, and filenames are not independently added to the
  digest payload. The selected content and its order determine the digest;
  the ID and filenames select which content is read. Check names are still
  validated against the release's own catalog.
- Relative-path validation is lexical. The bound tree reader owns retrieval;
  the module does not reinterpret paths against its own directory.
- The legacy checks are not a complete JSON type schema. Invalid types can
  raise the same built-in exceptions as the original functions. Tightening
  current authoring validation belongs to the new layout reader.

## Integration checks to add

The following controls remain designs, with no execution credit here:

1. Pin the actual `v0.3.6` digests above in the generator's history controls;
   compare the complete set so dropping a surface cannot pass.
2. Supply the same released reader while changing the working tree's guide,
   catalog and goldens. The released rows/digests must remain identical.
3. Remove a required manifest, catalog, definition or golden from a controlled
   reader. The callback failure must reach the caller and prevent history
   rendering; the release must not disappear from the table.
4. Mutate each explicit refusal above and assert its named boundary. Include
   duplicated and reversed markers in primary and supplementary regions.
5. Change whitespace-only region text or JSON object-key order and preserve
   the digest; change a public value, array order or supplementary-region
   order and change the digest. Keep expected values independent of this
   implementation.
6. In the history orchestrator, remove a legacy surface in the new tree and
   retain its removal row across `v0.3.7` and `v0.3.8`; preserve this reader
   when introducing any later authoring syntax.

The source and check designs are grounded in the released generator,
`CONTRACT-GENERATOR-GUARANTEES.md` (`H01`–`H08`) and the verified migration
inventory. Only the actual-release calculation in the preceding section was
executed.
