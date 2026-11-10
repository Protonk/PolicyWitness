# CONTRACT.md first-reader examination report

A read-only examination of [docs/CONTRACT.md](../../docs/CONTRACT.md), prepared
before the document is given to independent external readers. It records what
the document says, how its structure is generated and checked, and how far each
claim can be traced into implementation and evidence. It proposes no
replacement text and no remediation plan. Classifications of findings are
provisional.

## 1. Scope, boundaries and conventions

### 1.1 Object examined

| Item | Value |
| --- | --- |
| Commit | `298c180553616ae6086a2b9c723eddf6c650f77b` (`v0.3.6-12-g298c1805`), clean tree |
| `docs/CONTRACT.md` | 441 lines, about 4,000 words, blob `bfd2ededcfdeaf801b3f179e38886e9baa55fb7f` |
| `docs/PolicyWitness.md` (the guide) | 2,646 lines, blob `4dce8f691c99e9b1b9908d3846b4ccd4d464c940` |
| `docs/contract_surfaces.json` | blob `b5a07f358080c3df6f8227754dfc5010e7c6d8f4` |
| Date of examination | 2026-11-09 |

`docs/CONTRACT.md` is unchanged between `v0.3.6` and this commit. Of the 105
files in the public build-identity scope, one differs from `v0.3.6`:
`tests/lib/build_provenance.py`. No controller, runner or worker source differs.

### 1.2 Repository boundaries

- **Primary object:** every line of `docs/CONTRACT.md`.
- **Machinery read in full by the author:** `docs/contract_surfaces.json`,
  `docs/generate_contract_stamps.py`, `docs/build_contract.py`,
  `docs/source_identity.py`, `docs/generate_worker_identity.py`,
  `docs/generate_porcelain.py`, the stamp and identity tests in
  `tests/suites/source_drift/build_contracts.py`, the release preflight stamp
  check, and the surface shape goldens' structure.
- **Implementation traced:** `controller/src`, `runner/Sources`,
  `runner/Clients`, `runner/Services`, `controller/tools/pw_probe_runner`,
  `build.sh`, `meson.build`.
- **Verification traced:** `tests/catalog.json`, the suites and unit tests that
  the traces reached, and the fixtures the surface manifest names.
- **Existing runtime evidence consulted:** the v0.3.6 release acceptance
  battery under `dist/archive/v0.3.6/evidence/test-runs/`. This directory is
  gitignored and exists only in the local checkout.
- **Outside the boundary:** a complete review of the guide, `LIMITS.md`,
  `WORKER.md`, `ARCHITECTURE.md` and `tests/FAILURE-PROPAGATION-CONTRACT.md`.
  They were read only where `CONTRACT.md` defers to them or where the surface
  manifest makes their text part of a surface. Rule-level correctness of the
  semantic validators was not audited; their existence, reachability and
  effect on output were.

### 1.3 Line references

- `C:N` and `C:N-M` mean lines of `docs/CONTRACT.md` at the commit above.
- `G:N` means a line of `docs/PolicyWitness.md` at the same commit.
- Other citations are `repository/relative/path:line` at the same commit.
- The blob identifiers in 1.1 let a later reader confirm they hold the same
  bytes before relying on a line number.

### 1.4 Evidence classes

Each statement in this report belongs to one of these classes.

- **Observed.** Read in source or test text. An unmarked citation was read by
  the author. A citation marked **†** was read by one of five delegated
  read-only tracing passes and was not re-read by the author. Findings in
  section 7 carry the same marks.
- **Runtime.** Supported by the retained v0.3.6 acceptance battery
  (run `20261109T214743Z_63091daa`, 229 default cases, all passing, against an
  app reporting `release:v0.3.6`). The test sources at this commit differ from
  those the battery ran; the product sources do not.
- **Interpretation.** The author's reading of what a statement means or implies.
- **Hypothesis.** Would need a new experiment. None was performed.

"A test asserts X" in this report describes test source. It does not claim the
test passed unless the statement is marked Runtime.

### 1.5 Commands run

No build, test, generator write or other checkout mutation was performed
before this report was written. Four read-only checks were run with the pinned
interpreter and `-B -S`:

| Command | Result |
| --- | --- |
| `docs/generate_contract_stamps.py --check --require-history` | `ok: contract surface stamps current` |
| `docs/build_contract.py` | `development:bfba3708d7bc7cc02ae4de6c16b9ce59f14c6f0c0931490bf8dbb5163b3eb4d2` |
| `docs/generate_worker_identity.py --check` | `ok: worker identity 4be1acb4…27a1; all generated copies current` |
| `docs/generate_porcelain.py --check` | `checked 84 porcelain records` |

One delegated pass recomputed the porcelain fingerprint in memory from
`docs/porcelain.json`, outside the checkout, and reproduced the committed value.

## 2. Principal findings

Section 7 gives each finding in full. "Belongs to" is a provisional
classification: document, interpretation, implementation or evidence.

| ID | Finding | Belongs to | Consequence for a fresh reader |
| --- | --- | --- | --- |
| F-01 | Each surface's hashed definition includes about 2,090 lines of the guide. `CONTRACT.md` never links to the guide or says so. | Document | High |
| F-02 | The heading outline contradicts the region boundaries, and the region markers are invisible when rendered. | Document | High |
| F-03 | Stamps record declared change, not behavioral change. The reuse procedure relies on them. All 13 rows currently read `v0.3.6`. | Evidence, document | High |
| F-04 | The manifest's `checks` field is a label. Three surfaces name a suite that release acceptance does not run; two name a suite with no content for that surface. | Evidence | Medium |
| F-05 | "Verified examples": of 13 examples, default integrated controls verify 2 as written and 4 in part; 6 rest on constructed data or opt-in cases; 1 is not verified as written. | Evidence, document | Medium |
| F-06 | The compiled-profile sentence and its example describe a producer check as a reader refusal. | Document, possibly implementation | High |
| F-07 | "Requires" and "admits only" in the equipment region mean "flagged", not "refused". The checks are skipped for a degraded reply. | Interpretation, document | High |
| F-08 | The refusal code table omits about 29 emitted codes, one ordering sentence is not true of decode-time rules, and the null exceptions omit one class. | Document | Medium |
| F-09 | "No bypass" and "unbound" hold for the packaged run path. A shipped helper, direct builds and `_test_overrides` sit outside what the sentences suggest. | Interpretation, document | Medium |
| F-10 | The document does not say what equality of two contract strings fails to establish. The internal identity section does. | Document | Medium |
| F-11 | Four identity-derivation sentences have edge cases the wording does not cover. | Document | Low |
| F-12 | Residue of retired mechanisms, undefined terms and references that cannot be resolved inside the document. | Document | Medium |
| F-13 | Maintainer instructions sit inside hashed normative regions, and an internal identity sits inside a public contract. | Document | Low |
| F-14 | "Cannot disagree with each other about structure" is stronger than the code. | Document | Low |
| F-15 | Four equipment-region sentences have no corresponding check or no determinable meaning. | Document | Medium |
| F-16 | Three installation-region phrases are stronger or vaguer than the code. | Document, implementation (hypothesis) | Low |
| F-17 | Four statements in the internal identity section are unsupported, narrower than they read, or untested. | Document, evidence | Low |
| F-18 | Implemented behavior the document states that no executing test reaches. | Evidence | Medium |
| F-19 | Two hashed guide regions contradict `CONTRACT.md`. Found incidentally. | Document (guide) | Medium |
| F-20 | Statements that look questionable and are sound. No change warranted. | None | None |

The core claim of the document is well supported. A request is admitted only
when its `contract` string equals the compiled identity, in both the controller
and the XPC host, before selectors, augments or child processes. Client
captures, host replies and helper envelopes are admitted the same way before
their fields are read. Section 8 lists what is well supported.

## 3. Structure and authority of the document

### 3.1 Map by line range

"Hashed" means the text lies inside a `<!-- BEGIN CONTRACT id -->` region and
therefore contributes to a surface stamp.

| Lines | Heading as rendered | Role | Hashed into |
| --- | --- | --- | --- |
| C:1-6 | (title, introduction) | Normative summary of the whole design | Nothing |
| C:8-15 | (none) | Normative: how the build identity is derived and where it appears | Nothing |
| C:17-20 | (none) | Procedure for the specimen author and the runner operator | Nothing |
| C:22-32 | `## Surface stamps` | Explains machinery; denies that stamps are admission keys | Nothing |
| C:34-50 | (table) | Generated by `docs/generate_contract_stamps.py` | Nothing |
| C:52-56 | (none) | Explains machinery: behavior without tag history | Nothing |
| C:58-63 | `## Normative surfaces`, `### Saved specimen and runner selection` | Normative | `request` |
| C:65-124 | `## Accepted input contract` | Normative, mixed with maintenance instructions (C:103-105, C:113-114, C:116-118) and a pointer to a lesson (C:121-122) | `request` |
| C:126-166 | seven `###` headings | Normative summaries, one paragraph each, each ending in an example | `policy`, `probes`, `actors`, `envelope`, `dossier`, `steps`, `lifecycle` |
| C:168-238 | `### Actor evidence and equipment`, `## Actor evidence ownership` | Normative, dense reply-evidence constraints | `equipment` |
| C:240-250 | two `###` headings | Normative summaries | `profile`, `transport` |
| C:252-291 | `### Exit classification and structured refusals`, `### Structured request refusals` | Normative | `refusals` |
| C:293-298 | `### Runner installation and reservation` | Normative | `installation` |
| C:300-358 | `## Typed response transport` | Normative wire format, mixed with machinery explanation (C:304-311) | `transport` (as `transport_encoding`) |
| C:360-377 | `## Maintaining the contract` | Maintenance procedure; scope notes | Nothing |
| C:379-425 | `## Internal host/worker identity` | Describes an internal mechanism and its limits | Nothing |
| C:428-434 | `## Shape goldens` | Maintenance procedure | Nothing |
| C:436-441 | `## Build stamp` | Normative: envelope `build` fields | Nothing |

### 3.2 Where authority is deferred

`CONTRACT.md` contains eleven links.

| Line | Target | What it supplies |
| --- | --- | --- |
| C:24 | `contract_surfaces.json` | The surface list. Authoritative for scope. |
| C:77 | `controller/README.md#runner-selection-external-entitlements` | Selector fields. Further explanation; the anchor exists. |
| C:108, C:193, C:226, C:336 | `LIMITS.md` | Numeric limits. Authoritative for values. |
| C:121 | `REQUEST-GRAMMAR.md` | A developer lesson over the shared example corpus. Explanation. |
| C:304 | `porcelain.json` | The record schema. Authoritative for record structure. |
| C:330 | `controller/src/porcelain.rs` | The primitive reader. Source. |
| C:384 | `generate_worker_identity.py` | The identity generator. Source. |
| C:389 | `BUILD.md#one-build-in-time` | The order of build checks. Authoritative for sequence. |

There is no link to the guide, to the release procedure in `SIGNING.md`, to
`WORKER.md`, or to `tests/FAILURE-PROPAGATION-CONTRACT.md`. The guide is
referred to once, as "the guide" (C:117). Section 7, F-01 and F-12 follow from
this.

### 3.3 Are the roles apparent?

Partly. The stamp table is visibly generated in source (C:34, C:50). The
introduction and the `## Build stamp` section read as normative. The roles that
are not apparent:

- Which paragraphs are normative. The boundary is a pair of HTML comments.
  A rendered reader sees no boundary (F-02).
- That the normative text continues in another document (F-01).
- That C:379-425 describes something a specimen author never touches (F-13).
- That several sentences inside normative regions address maintainers (F-13).

## 4. Contract machinery

### 4.1 What is authored, derived, generated and observed

| Artifact | Kind | Produced by | Checked by |
| --- | --- | --- | --- |
| Region prose in `CONTRACT.md` and the guide | Authored | Hand | Marker well-formedness only (`generate_contract_stamps.py:174-186`) |
| `docs/contract_surfaces.json` | Authored | Hand | Field set, unique identifiers, nonempty goldens and checks, suite names exist in `tests/catalog.json` (`:41-60`) |
| `docs/porcelain.json` | Authored | Hand | `generate_porcelain.py:89-151` |
| Swift writers, Rust readers, Python tables | Generated | `generate_porcelain.py` | `--check` in every build (`build.sh:231`) |
| `tests/fixtures/contract/response_shape.json` | Observed, then reviewed | Swift unit executable writes binary replies; an independent Python reader decodes them and collects keys and JSON types (`tests/suites/runner_unit/porcelain_replies.py:109-121`) | Same case fails on any difference and writes a candidate |
| `tests/fixtures/contract/envelope_shape.json` | Observed from a hand-built field-complete envelope | Rust unit test (`controller/src/run_flow.rs:3463-3486`) | Same test |
| `tests/fixtures/contract/surfaces/*.json` (13 files) | Derived | `collected_shapes` (`generate_contract_stamps.py:63-153`) | `check_shapes` in every `--check` |
| `tests/fixtures/request_contract/examples.json` | Authored corpus of 158 requests with expected refusals | Hand | Swift decode tests and the signed CLI and direct-XPC control |
| Stamp table in `CONTRACT.md` and the guide | Generated | `generate_contract_stamps.py` | `--check`; release preflight |
| Public build identity | Derived at build time | `docs/build_contract.py` | Recomputed before signing (`build.sh:681-685`) |
| Worker identity (three copies) | Generated | `generate_worker_identity.py` | `--check` before compile and before signing; the built worker is asked (`build.sh:686-689`) |

### 4.2 Surface stamps

**Inputs to one surface hash** (`generate_contract_stamps.py:174-189`):

1. The text of the `CONTRACT.md` region whose identifier equals the surface
   identifier, with whitespace runs collapsed.
2. The text of every region the manifest lists under `definitions`, collapsed
   the same way.
3. Every file the manifest lists under `goldens`, parsed as JSON and
   re-serialized with sorted keys.

The manifest's `artifact` and `checks` fields are not hashed.

| Surface | Guide regions hashed (lines) | Goldens beyond `surfaces/<id>.json` |
| --- | --- | --- |
| `request` | `request_form` (G:169-205), `request_admission` (G:490-613), `installation` (G:2339-2622) | `request_contract/examples.json` |
| `policy` | `policy_input` (G:615-633), `policy_tools` (G:676-879) | none |
| `probes` | `probes` (G:881-908), `operations` (G:2111-2284) | none |
| `actors` | `actors_phases` (G:207-254), `actors_extensions` (G:256-488) | none |
| `envelope` | `envelope` (G:1204-1309) | none |
| `dossier` | `dossier` (G:1572-1651) | none |
| `steps` | `steps` (G:1737-2012), `operations` | `comparison/matrix.json` |
| `lifecycle` | `lifecycle` (G:1311-1489) | `disposition/current/constructed_deadline.json` |
| `equipment` | `equipment` (G:1653-1735), `lifecycle` | none |
| `profile` | `profile` (G:635-674) | `contract/compiled_profile.json` |
| `transport` | `transport` (G:1491-1570), `CONTRACT.md#transport_encoding` (C:300-358) | none |
| `refusals` | `refusals` (G:2014-2109), `request_admission` | `request_contract/examples.json` |
| `installation` | `installation` (G:2339-2622) | none |

**What each derived surface golden contains** (`collected_shapes`):

| Surface golden | Content |
| --- | --- |
| `request`, `policy`, `probes`, `actors` | Names of the Swift `CodingKeys` cases for the request types assigned to that surface. `request` adds the controller's two selector field lists. No value types, no vocabularies, no rules. |
| `envelope`, `dossier`, `steps`, `lifecycle`, `equipment`, `profile`, `refusals` | Keys and JSON types, taken from the two observed shape goldens and assigned to a surface by substring tests on the key path (`:66-79`, `:143-147`). Any path that matches no test goes to `envelope`. |
| `transport` | Reservation `CodingKeys`, five reservation and client limits with value, unit, counting, effect and control, client-capture shape, and the full wire identity of all 84 records. |
| `installation` | Equipment-manifest keys, the source text of every `Serialize` struct in three Rust files, the same five limits, and the reservation keys. |

**How a stamp is derived** (`:192-232`). The generator walks annotated
`vX.Y.Z` tags on the ancestry of `HEAD` in topological order, skipping tags
whose tree has no manifest. For each tag it computes each surface hash from
that tag's tree. A surface keeps its earlier stamp while its hash is unchanged
and takes the tag's name when the hash changes or the surface first appears.
The working tree is then compared with the last state; a difference yields
`unreleased`, or the name given to `--release`. A surface missing from a later
manifest keeps a row marked `(removed)`.

**Where it is checked.**

- Every build runs `--check` (`build.sh:227`). With history it must reproduce
  both tables. Without history it checks shape-golden freshness, region
  well-formedness and that the two tables are identical, then prints
  `stamp derivation not checked`.
- Release preflight requires history, an exact reproduction, and no
  `unreleased` row (`tests/lib/release_preflight.py:178-185`).
- `source_drift/build_contracts` exercises the generator in temporary
  repositories: pending release reproduces after tagging, removal rows, a
  region edit moves one stamp, a golden edit moves one stamp, text outside
  regions moves none, a new `CodingKeys` case makes the derived golden stale,
  reservation limits and wire tags move `transport` and `installation`, and a
  source copy or tagless clone cannot erase stamps
  (`tests/suites/source_drift/build_contracts.py:292-440`). Runtime: this case
  passed in the v0.3.6 acceptance battery.

**What the mechanism detects.**

- Any non-whitespace edit to a hashed region in either document.
- Any change to a golden's parsed JSON.
- A request key added, removed or renamed in Swift, because the derived golden
  becomes stale and the build refuses until it is recollected.
- A reply or envelope key added, removed or retyped, provided the shape
  fixtures produce it.
- Any change to the wire identity or to the five listed limits.

**What passes unnoticed.**

- A change of behavior with no change of key names, JSON types or hashed prose:
  a different admission rule, a renamed enumerated value, a changed comparison
  rule, a changed side effect of an attempt action.
- A change of a request field's type. The request goldens hold key names only.
- Edits to `CONTRACT.md` outside regions: the introduction, the identity
  derivation (C:8-15), the build stamp section, the internal identity section.
- Edits to the guide outside its 17 regions (about 550 lines).
- Attribution drift. A new reply key is assigned by substring. A key under
  `reply.actors` goes to `equipment`; a key matching nothing goes to
  `envelope`. The guide regions also do not align with surface names: the guide
  region `refusals` is the `normalized_outcome` catalog and client timeout
  table (G:2015-2107); the guide region `envelope` holds `runner_subprocess`
  lifecycle detail (G:1237-1285); the guide region `transport` holds validator
  receiver evidence (G:1494-1502).

**Independence.** The derived surface goldens agree with the sources by
construction; that agreement shows freshness and nothing else. Independent
evidence enters at two points. `response_shape.json` is collected by a Python
reader written separately from the Swift writer and the Rust reader, and live
harness readers use the two shape goldens as allowlists, so signed-product
output cannot carry a key the golden lacks
(`tests/lib/consumer.py:53-59`). The request example corpus is run through the
signed CLI and direct XPC. Neither reaches prose: nothing checks that a
region's sentences describe what the code does.

**Current state.** The manifest first exists at `v0.3.6`
(`git cat-file -e v0.3.5:docs/contract_surfaces.json` fails). All 13 rows
therefore read `v0.3.6`. The mechanism has not yet distinguished one surface
from another in real history.

### 4.3 Public build identity

**Derivation** (`docs/build_contract.py:73-90`). A SHA-256 over a domain prefix
and, for each scoped path in sorted order, the length-framed path and
length-framed file bytes. The scope is: files with suffix `.rs`, `.c`, `.h`,
`.swift`, `.sb`, `.plist` or `.ent` under six directories (`controller/src`,
`controller/tools`, `runner/Sources`, `runner/Clients`, `runner/Services`,
`runner/augments`), plus 18 named files. At this commit that is 105 files.
Nine are under `docs/` or `tests/`.

The result is `release:<tag>` when all of these hold: the directory is the top
level of its own Git repository; `git status --porcelain --untracked-files=all`
is empty; exactly one annotated tag matching `vN.N.N` points at `HEAD`; and the
on-disk bytes of every scoped path equal the tag's blobs, with equal path sets.
More than one such tag on a clean tree is an error and no identity is emitted.
Otherwise the result is `development:<digest>`.

**Plumbing** (†, with `build.sh:251-252` and `:681-685` and
`controller/src/json_contract.rs:10-22` read by the author).

1. `build.sh:251` computes the value once and exports `PW_BUILD_CONTRACT`.
2. Rust reads it with `option_env!`; absent or empty becomes `unbound`.
3. Meson runs `build_contract.py --swift-stdout` at configure time to generate
   `PWBuildContext.swift`; that mode refuses if its result differs from the
   exported value (`build_contract.py:110-112`).
4. `build.sh` stamps `PWContract` into the app and service `Info.plist` files
   from the same shell variable.
5. `build.sh:681-685` recomputes before signing and refuses on a difference.

No build step asks a built binary for its public contract. The default
`smoke` and `integration` cases compare the app plist with `--version`, the
envelope, the client capture and the host reply producer (†). Runtime: both
passed in the v0.3.6 acceptance battery.

**What the identity does not cover** (†, except where the author's own
enumeration of the scope is cited). Build variants (`PW_INSPECTION`,
`BUILD_XPC`), caller `RUSTFLAGS`, the Rust, Swift and C toolchains, the SDK,
`Makefile`, `docs/porcelain.json` and `docs/limits.json` (their generated
copies are covered), and unscoped test helpers that gate the build. Two tracked
files under the scoped directories fall outside the suffix list and neither is
shipped: `controller/tools/sb_api_validator/build.sh` and
`runner/augments/README.md` (author's enumeration).

**What it covers that is not shipped.** Eight Python files under `tests/`,
`runner/Package.swift`, and `controller/tools/sb_api_validator/debug.ent` (†).

**An instance at this commit.** `HEAD` is twelve commits after `v0.3.6` and
clean. Its identity is `development:bfba3708…`. The only scoped file that
differs from the tag is `tests/lib/build_provenance.py`. A build of this commit
and the v0.3.6 release are built from identical controller, runner and worker
sources and refuse each other's specimens.

### 4.4 Distinct identifiers and their responsibilities

| Identifier | Where it travels | Compared by | Purpose | Not for |
| --- | --- | --- | --- | --- |
| Public build contract | Request `contract`; envelope `build.contract`; reply `producer.contract`; client capture and reservation `contract`; plist `PWContract`; registry record `contract` | Exact string equality at every admission point | Admission | Authentication; proof of equal binaries |
| Surface stamp | The two tables | Nothing at run time. No product source mentions stamps. | Navigation for a specimen author | Admission |
| Porcelain fingerprint | Bytes 4-35 of every binary frame | Rust and Python readers, before any payload byte | Refusing to decode under another record schema | Compatibility permission. It never suffices without the contract. |
| Worker identity | Shared-memory header bytes 64-95; equipment inventory; `worker_evidence.abi_identity` | The C worker at startup; the host before decoding the worker evidence record | Agreement of jointly built host and worker sources | Public admission; authentication |
| `build.describe`, `build.commit`, `build.version`, `build.number` | Envelope, plist, reply producer | No Rust or Swift admission code. Release archiving compares the plist's describe and commit with the tag (`tests/lib/release_archive.py:184-187`). | Provenance | Request, reply or peer admission |
| Registry, provenance and validator format markers | Their own files and streams | Their own readers | Infrastructure formats | Public contract |

The two digests are computed separately and neither takes the other as input.
Their inputs overlap: every worker-identity input except the worker-identity
generator itself is also a public-identity input, and the public digest
includes the generated identity regions. A changed worker identity therefore
implies a changed development contract. The reverse does not hold (†).

## 5. Trace from each surface to implementation and verification

"Default" means the case is in the default battery and therefore in the
v0.3.6 acceptance run. "Opt-in" means it is not. The `runner_byoxpc` suite is
`default: false` as a whole (`tests/catalog.json`); none of its cases is in the
acceptance run.

| Surface | Produces or validates | Refuses or declines to conclude | Verification | In v0.3.6 acceptance |
| --- | --- | --- | --- | --- |
| `request` | Controller: `controller/src/run_flow.rs:598-602`, `request_patch.rs:75-100`. Host: `runner/Sources/PWRunnerCore/PWRunnerRequest.swift:108-145`, `ProbeRunner.swift` `admitSpecimen` (†). | Four contract codes with `expected_contract`; unknown keys by `CaseIterable` key walk (`PWRunnerCoding.swift:12-19` †); meaning and capacity refusals before any child. | Default: `runner_outcome_bad_request/accepted_input_contract` runs all 158 corpus rows through the signed CLI and direct XPC with a file-effect check (†). Unit: `request_patch.rs:226-242`, `RequestContractTests.swift` (†). Opt-in: `same_shape_contract`. | Yes, except `same_shape_contract` |
| `policy` | Controller resolves augments in memory (`run_flow.rs:625-634`, `augments.rs` †). Host refuses unresolved augments (`PWRunnerRequest.swift:347-349` †). | `augment_unavailable`, `unresolved_augments`. | Default: `integration/cli.integration`, `witness_contract/dossier_witness`, corpus rows `augment*` (†). | Yes |
| `probes` | Closed attempt table `CWorkerRequestPlanning.swift:107-134` (†); truncating open in `pw_probe_runner.c:455-458` (†). | No agreement field exists in the step record (†). | Default: `run_effects` file-action effects; `witness_contract` prediction and ordering cases (†). Opt-in: `same_shape_contract`. | Yes, except the foreign-build half of the example |
| `actors` | `ActorPlan.swift` normalization; one spawn per actor; single `sandbox_apply` site (†). | `unknown_actor` and related codes before `runActors` (†). | Default: corpus row `phase_unknown_actor` through CLI and XPC; `witness_contract/extensions`, `actor_compositions` (†). | Yes |
| `envelope` | `controller/src/json_contract.rs:66-99` (†); five frame keys, five build keys. | Helper envelope refused unless `build.contract` matches (`policy_check.rs:47-60`). | Unit on constructed data (`policy_check.rs` tests †); default `integration` checks `--version`. No signed control of the example. | Unit only |
| `dossier` | `controller/src/dossier.rs`; one in-memory serialization (`run_flow.rs:594`, `:696` †). | Unknown observations stay unknown (`dossier.rs` †). | Default: `witness_contract/dossier_witness` for contents. The held-input sentence and the example are unit tests with injected dependencies (`run_flow.rs:2666-2836` †). | Contents yes; held input unit only |
| `steps` | Reply `producer` (`PWRunnerAPI.swift:169-177`); comparison in `CWorkerComparison.swift` (†). | `decode_bound` refuses a foreign producer before the reply becomes a typed record (`porcelain.rs:174-222` †); `query_first` gated in worker, host, controller and harness (†). | Default: `failure_boundaries/admission`, `witness_contract/queries_precede_attempts`, `attempt_effects_wait_for_collection`, `runner_exec_dac` (†). Foreign reply: constructed, and opt-in `runner_byoxpc/reservation_controls`. | Ordering yes; foreign reply no |
| `lifecycle` | `CWorkerDisposition.swift:102-115`, `:170-213` (†). | `unresolved` projects to `unconfirmed`; any issue projects to `withheld` (`porcelain_admission.rs:1631-1636`). | `runner_unit` with a real host driver and fixture child; `unit` for the controller projection (†). Default `witness_contract/worker_termination` and related. | Yes (unit and live) |
| `equipment` | `ActorEquipment.swift`, `ActorScheduler.swift`, `ActorSession.swift` (†). | Reader checks in `controller/src/porcelain_actor.rs` (closed pairs at `:1076-1079`, application pairs at `:493-538` †, gate conjuncts at `:979-1024` †). A violation flags the reply; it does not refuse it. | Corpus of 77 constructed cases through Rust and Python readers; `runner_unit` real-process scheduler tests; default `witness_contract/extension_boundaries`, `extensions`, `actor_compositions`; default `preflight/byoxpc_verification_controls` (†). The manifest's named suite, `runner_byoxpc`, asserts none of the region's relationships (†). | Yes, through suites the manifest does not name |
| `profile` | Host `decodeProfileCapture` (`CWorker.swift:678-716`). | Reader checks status, producer and stage only (`porcelain_admission.rs:1289-1312`). | `unit`, `runner_unit`, `blackbox_e2e/checker_controls` (†). The manifest's named suite, `failure_boundaries`, contains no profile or nonce assertion. | Positive case only |
| `transport` | Client `PWRunnerClientSession.swift:205-252`; host `PWRunnerService.swift:289-322`; reader `controller/src/porcelain.rs`, `runner_client.rs:705-766` (†). | Contract compared on both sides of reservation before the specimen is sent; one submission; fingerprint first and never sufficient. | Unit: client session tests with fake connections, Rust capture tests, `source_drift/porcelain_codec` (†). Live: opt-in `runner_byoxpc/reservation_controls`. | Unit and codec yes; live reservation controls no |
| `refusals` | `PWRunnerRequestFailure` in host; `RequestFailure` in controller (`request_patch.rs:12-39`). | Path withheld as null beyond 8 components or 63 bytes. | Default: corpus through CLI and XPC; `failure_boundaries/admission`; unit `request_patch.rs:163-224`. | Yes |
| `installation` | `controller/src/runner_commands.rs:261`, `:364-373` (†); `runner_manager.rs:20-28`, `:596-629`. | Registry record must hold the current contract to execute; records without one stay listable and removable (†). | Unit in `runner_manager.rs`, `runner_select.rs`; `unit/rust.byoxpc_reds`. Live: `runner_byoxpc/registry_recovery`, `reservation_controls` (†). | Unit yes; live no |

## 6. Line-by-line examination

Every line of the document falls in one of the 48 groups below. Blank lines and
region markers are covered by the group that contains them. Verdicts:
**Supported**, **Partly supported**, **Unsupported**, **Not determined**.

### 6.1 Introduction and identity (C:1-20)

**L-01 · C:1-6 · Title and core claim.** Establishes that the release is the
unit of contract; that saved specimens assert `contract`; that envelopes, host
replies and client captures name their producer; that admission is exact; and
denies negotiation, implicit acceptance, historical translation and bypass.
*Evidence.* Exact string equality in the controller (`request_patch.rs:81-99`)
and host (`PWRunnerRequest.swift:110-123`); no translation code found (†).
Readers: `policy_check.rs:47-60`, `porcelain.rs:174-222`,
`runner_client.rs:705-766`, `run_flow.rs:96-104` (†).
*Verdict.* Supported for `policy-witness run` and the XPC host. "Bypass" is
qualified by F-09. "The public contract is the release" invites the inference
in F-10.

**L-02 · C:8-13 · Derivation of the identity.** Establishes the release and
development forms, that the digest covers contents and paths, that documentation
and test edits "ordinarily" do not change it, that a dirty release tree is a
development build, that scoped bytes are compared with the tag's blobs, and that
direct Cargo and SwiftPM builds are `unbound`.
*Evidence.* `docs/build_contract.py:35-90`; default tests
`build_contracts.py:180-197`, `:228-257`. Runtime: passed in acceptance.
*Verdict.* Partly supported. The derivation rules are exact and tested. Four
wordings have edge cases (F-11). "Direct Cargo … builds are `unbound`" depends
on the environment (F-09).

**L-03 · C:14-15 · Where the identity is reported.** `--version`, envelope
`build.contract` and plist `PWContract` report the compiled identity; describe
and commit are provenance, not admission keys.
*Evidence.* `controller/src/cli.rs:45`; `json_contract.rs:66-82` (†);
`build.sh` plist stamping (†). No Rust or Swift admission code compares describe
or commit (†). Runtime: default `smoke` and `integration` compare plist,
`--version`, envelope, capture and producer.
*Verdict.* Supported. `PWContract` is the build script's value, equal by
construction and by test; it is not read back from a binary. Release archiving
does compare describe and commit, which is outside request admission.

**L-04 · C:17-20 · Reuse procedure.** To reuse a specimen with another release,
inspect rows changed since its asserted release, revisit those definitions, and
change the assertion by hand. PolicyWitness never rewrites a specimen. Reinstall
external runners when the contract changes.
*Evidence.* The run path only reads the request file (`run_flow.rs:594`); the
signed control asserts unchanged bytes for every corpus row (†). The refusal
text says "upgrade and reinstall the runner" (`runner_manager.rs:25`).
*Verdict.* The denial is supported. The procedure depends on the stamp table
carrying the information the reader needs (F-03). It is undefined for a
specimen that asserts a `development:` identity.

### 6.2 Surface stamps (C:22-56)

**L-05 · C:22-32 · Stamp scope and derivation.** The manifest defines scope;
the transport golden holds the full binary record identity; transport and
installation goldens hold reservation limits; the generator hashes canonical
goldens and each delimited region across reachable annotated tags; changed
surfaces read `unreleased`; removed surfaces keep a row; stamps are never
asserted or used for admission.
*Evidence.* Section 4.2. No file under `controller/src`, `runner/` or
`controller/tools` mentions stamps or the manifest.
*Verdict.* Supported. "Each delimited normative region" does not tell the
reader that most of those regions are in another file (F-01).

**L-06 · C:34-50 · Generated table.** Thirteen rows, all `v0.3.6`.
*Evidence.* `--check --require-history` reproduces it at this commit.
*Verdict.* Supported as generated output. It carries no differentiating
information yet (F-03).

**L-07 · C:52-56 · Missing history.** `--check` validates current inputs and
"agreement between the two tables" and reports that derivation was not checked;
regeneration refuses to erase release stamps; release preflight requires
history; `--check --require-history` asks for the same.
*Evidence.* `generate_contract_stamps.py:236-238`, `:256-276`;
`release_preflight.py:178-185`; test `build_contracts.py:298-319`.
*Verdict.* Supported. "The two tables" has no antecedent in this document; the
second table is at G:2630-2646 (F-12).

### 6.3 Request surface (C:58-124)

**L-08 · C:58-63 · Contract gate.** The root requires a string `contract`
equal to the running build identity. Missing, null, nonstring and foreign
assertions refuse before selectors, augments, helpers or children. Unknown
fields are refused after the gate. Example: a foreign assertion plus an invalid
runner selector reports the contract refusal and starts no client.
*Evidence.* Controller order: parse, gate, `--runner-mode` injection, selector,
registry resolution, augments (`run_flow.rs:598-634`). Host order: gate, then
unknown-key walk, then fields (`PWRunnerRequest.swift:110-124`). Unbound builds
refuse (`request_patch.rs:83`, `PWRunnerRequest.swift:121`).
Example: unit test on the production `run()` with injected dependencies
(`run_flow.rs:2424-2453` †); default signed control with a missing contract and
a misspelled selector key asserts `data.runner_client is None` (†); the only
independent process observation is opt-in (†).
*Verdict.* Supported. Argument errors precede the gate: an invalid
`--runner-mode` flag reports `tool_error` before the file is read (†). The
controller checks unknown keys only inside `runner`; other unknown keys are
refused by the host after the client and host have started, which C:286-287
discloses.

**L-09 · C:65-75 · Accepted fields and nulls.** `CodingKeys` define the
accepted fields of the listed request objects; an unknown key is `bad_request`
with a bounded path; `policy.params` names are data; missing and mistyped
fields are rejected; optional nulls "generally" mean absence; four named fields
reject explicit null.
*Evidence.* Key walk called in every listed decoder and in the actor,
actor-sandbox, `after_termination` and extension decoders the list omits (†).
The four null exceptions at `PWRunnerActors.swift:62-63`,
`PWRunnerRequest.swift:197`, `:280-281` (†). Default corpus rows cover them.
*Verdict.* Partly supported. A fifth class rejects explicit null: an
inapplicable extension operand (`PWRunnerExtension.swift:20-24`,
`ActorPlan.swift:409-411`) (F-08). "Remain the parser" is history (F-12).
`_test_overrides` is listed as an ordinary object (F-09).

**L-10 · C:77-85 · Runner selection and augments.** Selector types and every
entitlement are validated including shadowed aliases; unknown nested selector
fields are errors; a non-null nested value wins over its alias, including an
empty list; selection fields are removed before XPC and their resolved meaning
is recorded in runner provenance; direct XPC rejects selection fields; actor
`required_entitlements` stays in the request and is checked per actor; nonempty
augments need a string `sbpl_source`; the controller splices and strips;
direct XPC with unresolved fragments is rejected.
*Evidence.* `runner_select.rs:148-231`, `augments.rs:182-280`,
`ActorEquipment.swift:368-375`, `PWRunnerRequest.swift:349` (all †). Unit and
default corpus tests (†).
*Verdict.* Supported except "resolved meaning is recorded in runner
provenance", which is partly supported: provenance records the selected target
and entitlement read-backs, not the selector's entitlement demand, and is null
when selection fails (†).

**L-11 · C:87-98 · Meaning checks.** Unknown attempt pairs and filter kinds
are refused before any worker or validator exists; `attempt.args` only for
`exec/spawn`; non-null `filter.value` refused for kind `none`; capture nonce
rules; exactly one plan form; nonempty unique phase identifiers; query and
attempt both required; step identifiers distinct across phases; exec targets
absolute; excluded pairs still yield `prediction_unavailable`; operation names
remain OS queries and can report `unsupported_operation`; scopes need not match.
*Evidence.* `ProbeRunner.swift:28-125`, `CWorkerRequestPlanning.swift:107-134`,
`:320-322`, `PWRunnerService.swift:365` before `:403` (all †). Default corpus
and `failure_boundaries` cover each rule on the signed product (†).
*Verdict.* Supported. Two notes. The plan-form rule is enforced at decode
time (`PWRunnerRequest.swift:132-142`), which matters for L-36. No signed test
asserting `unsupported_operation` was found in the suites searched (†).

**L-12 · C:100-106 · Re-assertion rule.** Every shipped-source change changes
a development contract; a clean annotated release binds all surfaces; any
change therefore requires the author to review and re-assert; keep definitions,
"verified examples" and goldens current so the table identifies what to review;
there is no request counter and no compatibility exception.
*Evidence.* Section 4.3.
*Verdict.* The first sentence is supported for tracked scoped sources and not
for build variants (F-10, F-11). The fourth sentence addresses maintainers
(F-13) and is the only link between behavior and stamps (F-03). "Verified
examples" is examined in F-05. The two denials are history (F-12).

**L-13 · C:108-114 · Limits.** Limits are separate from syntax; a capacity
refusal names field, actual count and maximum before any attempt; raising
capacity accepts more plans and lowering it can refuse runnable ones; PW never
truncates or reinterprets a plan; capacity changes must be documented and
tested.
*Evidence.* `CWorkerRequestPlanning.swift:13-44` (†); default
`failure_boundaries` asserts field, actual, maximum, unit, no subprocess, empty
steps and an untouched target file (†).
*Verdict.* Supported. The last sentence addresses maintainers (F-13).

**L-14 · C:116-119 · Maintenance and a disclaimer.** Maintenance consists of
decoder fields, their meaning "in the guide", and tests; no schema language is
used; the rules protect requested intent and do not promise identical sandbox
observations across builds or macOS versions.
*Verdict.* The disclaimer is a useful restriction and is consistent with the
design. "The guide" is unlinked (F-12). The first two sentences address
maintainers (F-13).

**L-15 · C:121-124 · Developer lesson.** `REQUEST-GRAMMAR.md` uses the same
specimens as the Swift tests and the signed CLI and direct-XPC controls.
*Evidence.* One corpus file read by `RequestContractTests.swift:35-84` and by
`runner_outcome_bad_request/contract.py:88-125` (†).
*Verdict.* Supported. The Swift tests admit against an injected test identity
and execute nothing; the signed controls use the compiled identity (†).

### 6.4 Short normative regions (C:126-166)

**L-16 · C:126-130 · Policy.** A policy supplies SBPL and optional string
parameters; augments are resolved in memory before submission; direct XPC
refuses unresolved augments; imports and hashes describe the held input and its
closure. Example: a missing augment refuses before worker creation and leaves
the input file unchanged.
*Evidence.* L-10 evidence; `dossier.rs:62-173` (†).
*Verdict.* Supported in code. Hashes cover `sbpl_source` strings, not
parameters; the closure is the controller's bounded scan (†). The example's
first half has default signed controls; no test asserts the second half for
this case (F-05). A selection failure is returned before an augment refusal, so
a missing augment with an unselectable runner reports `tool_error` (†).

**L-17 · C:132-136 · Probes.** Unique step identifier, query and attempt;
closed vocabularies; predictions are observations distinct from attempts and do
not establish enforcement agreement. Example: `open_write` truncates; a
same-shape foreign assertion prevents the operation.
*Verdict.* Supported. The truncation has a default signed effect test. The
foreign-assertion half is verified only by the opt-in two-build case (F-05).
The vocabularies themselves are in the guide's `operations` region, not here.

**L-18 · C:138-142 · Actors.** Single-worker form or named actors and phases;
every sandboxed process is fresh; an actor applies its policy once; phases name
the active actor and preserve action order; extension transfer and consumption
use "explicit owned records". Example: a phase naming a nonexistent actor is
refused before children.
*Evidence.* Section 5 row `actors` (†).
*Verdict.* Supported. The example has a default signed control on both paths.
"Fresh" is a producer property; no reader requires distinct process
identifiers across actors (†). The single-worker form also has phases, so
"named actors and phases" does not distinguish the forms (†). "Owned records"
is undefined (F-12). The refusal code, `unknown_actor`, is not in the table at
C:273-284 (F-08).

**L-19 · C:144-148 · Envelope.** Five keys; `build.contract` identifies the
producer; readers admit before semantic fields; nested helper envelopes have
their own build context; unsupported received bytes remain available without
inferred claims. Example: a foreign helper envelope claiming compilation cannot
supply a successful policy-check status.
*Evidence.* `json_contract.rs`, `policy_check.rs:47-60`, capture and reply
readers as in L-01.
*Verdict.* Supported, with one precision. "Bytes remain available" is exact
for binary frames. A helper envelope that parses is kept as a re-serialized
JSON value, and unparsed helper output as lossy text with a cap (†). The
example is verified on constructed data only (F-05).

**L-20 · C:150-154 · Dossier.** Records the held request path, policy
provenance, imports, selected runner, host context and observed binary
inventory; unknown stays unknown; the submitted serialization and the fallback
compiler use the same held input. Example: changing the source file after
admission does not change the held submission.
*Verdict.* Supported in code. "Held" means read once into memory and
serialized once; the host receives a re-serialization, not the file's bytes
(†). For the built-in runner the binary inventory is four nulls and nothing is
hashed unless verification is requested (†). The held-input sentence and the
example are tested only with injected dependencies (F-05). The "fallback
compiler" is `sbpl-check`, which the document does not name.

**L-21 · C:156-160 · Steps.** A host reply carries `producer.contract`,
`describe`, `commit`; admission is exact before interpreting steps; comparisons
relate query and attempt; permission-shaped failures do not prove a sandbox
cause; `query_first` requires the collection and release chain. Example: a
foreign host reply inside a current envelope yields one unsupported diagnostic
without recovered comparisons.
*Verdict.* Supported. "Admission" here is producer identity; semantic
admission does not gate publication (F-07). The example's literal shape, a
foreign reply inside a current envelope, is a state only the harness reader
meets; the controller yields `unsupported_runner_response` with a null
`runner_result` and the raw bytes retained (†). Live verification is opt-in.

**L-22 · C:162-166 · Lifecycle.** Claims depend on native progress, collection
and termination observations; unknown or contradictory observations withhold
dependent claims; an exit request is not proof of reap; a successful return is
not an effect witness. Example: an unreaped worker stays unconfirmed after a
successful termination request.
*Verdict.* Supported in producer and controller. The example is verified by a
unit test using the real host driver with a fixture child and an injected wait
fault, and by constructed controller tests (†).

### 6.5 Equipment region (C:168-238)

**L-23 · C:168-171 · Opening.** Actor evidence binds observations to the named
process and "service-sealed" equipment; the worker identity is independent of
the public identity; worker entitlements are read from the selected binary.
Example: an equipment hash mismatch prevents use of the claimed equipment.
*Verdict.* Supported, with qualifications. "Independent" holds for
computation and use, not inputs (section 4.4). The reader cannot verify the
seal; it checks an OSStatus and digest lengths (†). The example is verified at
the binder on a constructed bundle and at `runner install` on a signed bundle;
no signed `run` against a mismatched worker was found (†). The public reason is
`worker_identity_mismatch`, and any refused row refuses the whole run (†).

**L-24 · C:173-181 · Ownership.** No "declaration reply" or "singular worker
projection"; `actors[]` owns launch, subprocess, application and equipment
association; `authority_setup.host` scopes and `authority_setup.workers` cells
retain setup, cleanup and capability observations; "an acquired decision does
not publish another cell"; "a scheduling summary does not replace any actor's
facts".
*Verdict.* The first three statements are supported in producer and reader
(†). The last two are not determined: neither phrase is defined anywhere in the
repository's documentation, and one natural reading of the first is
contradicted by the worker, which publishes cleanup cells after its decision
(F-15). The two opening denials are history (F-12).

**L-25 · C:183-196 · Equipment tables.** Inventory; rows named by position;
zero-based references; null `binding_ref` when no row exists for the role;
override rows carry `unverified_fixture` and "cannot establish packaged
selection"; static and live read-backs; requirements evaluated per actor with
boolean-true keys; bounds belong to LIMITS; runtime inspection failure cancels
scheduled activation and retains published facts and is not a
`preparation_failure`.
*Verdict.* Supported in producer and reader for the structural rules (†).
"Cannot establish packaged selection" has no corresponding check (F-15).
Runtime inspection failure is covered at unit level with real processes and by
constructed cases; no suite asserts it against the signed product (†). "Reserve
geometry" does not occur in `LIMITS.md` (†).

**L-26 · C:198-202 · `preparation_failure`.** Admits only two stage and code
pairs, with `runner_failed`, `rc: 1`, no launched actors, empty observation
arrays; declarative phase and action identities may remain; this is the sole
exception to the complete observation partition.
*Evidence.* `porcelain_actor.rs:1066-1116`; matching Swift and Python readers
(†).
*Verdict.* Supported, read as "a reply violating this is flagged" (F-07).
"Observation arrays are empty" is imprecise: `actors`, `phases`,
`authority_setup.workers` and normally the binding and entitlement tables are
populated (F-15). No Rust unit test reaches this function; the signed product
exercises the equipment pair (†). The `resolved_plan` pair appears unreachable
from a public request (†, inferred).

**L-27 · C:204-210 · Application.** Closed state and basis pairs;
`not_requested/unapplied_declaration`; what `not_attempted`, `observed` and
`unobserved` require; what cannot establish nonattempt.
*Evidence.* Eleven pairs in the reader, then a precedence check shared with
the producer (`porcelain_actor.rs:493-577` †).
*Verdict.* Supported. The document names four states and one basis; ten basis
strings appear in none of the documents it could defer to (†). Signed-product
assertions exist for three of the eleven pairs (†).

**L-28 · C:212-228 · Termination dependencies.** `owned_reap` contents;
`activation_observation`; ordinals local to the source actor process;
`termination_gate.observation`; requirements for every nonnull observation and
additional requirements for a satisfied gate; what cannot substitute for a
natural reap.
*Evidence.* Every conjunct of "a satisfied gate additionally requires" maps to
a reader condition and a producer condition (†; table in the delegated trace,
reader lines `porcelain_actor.rs:868-1024`). Real-process scheduler tests with
an independent `waitpid` witness, constructed negatives, and default signed
assertions for satisfied, abnormal-exit and timed-out cases (†).
*Verdict.* Supported. This is the best-supported dense passage in the
document. Notes: the reader enforces about nine further conditions the passage
does not state, including a closed set of eight gate outcomes of which only
`satisfied` is named (†). A dependent phase's activation ordinal lives in the
dependent's sequence, which "local to the source actor process" does not say
(F-15). "Capture stage" and "ownership/departure flags" are not field names
(F-12).

**L-29 · C:230-238 · Clock failure and failed gates.** Absent source
timestamps cannot satisfy a dependency; a stored dependent activation is kept
when its timestamp is missing; a present dependent timestamp must not precede
the source reap; reached failed gates withhold activation, collection and
release.
*Verdict.* Supported in reader and producer, with constructed negatives and a
default signed assertion for the failed-gate case (†).

### 6.6 Profile, transport, refusals, installation (C:240-298)

**L-30 · C:240-244 · Compiled-profile receipt.** Inherits the admitted reply's
context; has no independent schema marker; status, nonce, worker binding,
stage, byte count and digest must be consistent; a detached receipt grants no
producer context. Example: a wrong nonce refuses the receipt even inside a
current reply.
*Evidence.* Reader `porcelain_admission.rs:1289-1312`; host
`CWorker.swift:678-716`; unit test `porcelain_admission.rs:2710-2744`.
*Verdict.* Partly supported; the example is unsupported as written (F-06).
"Detached receipt" is not determined: no reader takes one (†).

**L-31 · C:246-250 · Transport.** Client capture and reservation messages
carry a string `contract`; capture and embedded host frame are independently
admitted; the fingerprint guards decoding and is not a compatibility identity;
reservation and submission failures never authorize replay after an uncertain
invocation. Example: a foreign live peer behind a matching registry entry
receives no specimen submission.
*Evidence.* Host `PWRunnerService.swift:293-299`; client
`PWRunnerClientSession.swift:205-252`; one `submit` call site after
`phase = .submitted`; retry only while acquiring (†).
*Verdict.* Supported in code. The example's live control is opt-in and uses an
instrumented host that returns a substituted control reply, so it shows that
the shipped client declines to submit; it does not contact a genuinely foreign
signed host, and it does not assert the absence of a host-side receive event
(†). The peer's identity is self-reported (F-10).

**L-32 · C:252-255 · Refusals opening.** Request refusals use `bad_request`,
bounded paths and distinct codes; contract failures include
`expected_contract`; foreign output is unsupported and malformed output stays
malformed; delivery failure takes precedence. Example: an old
`schema_version`-only specimen reports missing `contract`, not an unknown
field.
*Verdict.* Supported. The example has a unit test and a default signed control
on both paths (†). The example itself is phrased as history (F-12). The
unsupported-versus-malformed and precedence statements are tested on
constructed captures (†).

**L-33 · C:256-264 · What reports `bad_request`.** Lists the causes; the
controller exits 1; unreadable files, unavailable runners and transport
failures are tool or execution failures; `data.request_failure` is an unchanged
copy of the runner's record when the runner refused; absence means no
structured diagnostic.
*Verdict.* Supported. Exit 1 is not unique to `bad_request`; transport and
reply refusals also exit 1 and `tool_error` exits 2 (†). The copy is unchanged
because the controller applies no vocabulary or bounds check to it (†).

**L-34 · C:266-271 · The record.** `code`, `path`, and `expected_contract` for
contract-field refusals; path grammar; null when the location cannot be
reported in full; eight components of 63 UTF-8 bytes; refused parameter keys
withheld; prose `error` is supplementary.
*Evidence.* `request_patch.rs:27-38`, unit tests `:163-224`.
*Verdict.* Supported.

**L-35 · C:273-284 · Code table.** Ten rows naming 22 codes.
*Verdict.* Every listed code exists as a literal in controller or runner
source (author's search) and has a reachable emit site (†). The table is not
the vocabulary (F-08). "The request marker" in the `unsupported_contract` row is a
retired term (F-12).

**L-36 · C:286-291 · Ordering statements.** Refusals contain no steps or child
observations; the XPC host may have launched to decode; capacity checks precede
meaning checks; one refusal is reported, not an exhaustive list; retain
unfamiliar codes as unclassified.
*Verdict.* Supported, except that "capacity checks precede meaning checks" is
not true of rules enforced at decode time (F-08). The disclosure that the host
may have launched is a correct and necessary qualification of L-08.

**L-37 · C:293-298 · Installation.** Install admits service `PWContract`
before signing or launchd changes and rechecks after signing; registry and
live-peer identities must both match; records without a contract remain
listable, reconcilable and removable; unknown metadata survives unrelated
writes and pending cleanup; pending-cleanup entry shape; historical flattened
entries are read; publication requires a lossless read-back before atomic
replacement; "it never establishes execution compatibility or ownership";
retired kind aliases project as their current kind. Example: an owned legacy
record cannot execute but can be removed after observed absence.
*Evidence.* `runner_commands.rs:261`, `:364-373` (†);
`runner_manager.rs:20-28`, `:596-629`.
*Verdict.* Supported in code, with three imprecise phrases (F-16). All live
verification is in the opt-in `runner_byoxpc` suite (F-04). The admitted value
at install is the plist string, not the service binary's compiled identity,
which is first met at reservation (†).

### 6.7 Typed response transport (C:300-358)

**L-38 · C:300-311 · Schema ownership.** `porcelain.json` owns record
structure; the generator emits Swift writers and fields, Rust records, readers
and projection, and tables for a separately written Python reader; all three
derive from one schema "so they cannot disagree with each other about
structure"; none checks the schema; request, reservation and validator formats
keep their own boundaries; production reply ingestion is binary.
*Verdict.* Supported, except that "cannot disagree" is stronger than the code
(F-14). "None of them checks the schema itself" is a correct and valuable
limit statement.

**L-39 · C:313-326 · Frame format.** Magic, fingerprint, one root value; kind
and length header; nine kinds; eight-byte integers with native width and
signedness enforced; digests as bytes; equipment references as unsigned
indexes; enumerated values and request-chosen names as text checked by semantic
admission; record identity and strictly increasing nonzero tags; counts; sorted
unique map keys; variant case tag; optional fields absent.
*Evidence.* Each width and rule matches the Swift writer, the Rust reader and
the Python reader (†; three-column table in the delegated trace).
*Verdict.* Supported in full.

**L-40 · C:328-339 · Rejections, budgets, truncation.** The listed reader
rejections; byte, nesting and logical-storage budgets, which are not physical
memory bounds; capture and reply are separate frames under separate budgets;
the host writer bounds a reply by the frame limit; the client retains at most
its smaller allowance and a larger reply is refused as
`runner_reply_truncated`; the controller collects all client output before its
retention cap; reading is not streamed and has no receiver deadline.
*Verdict.* Supported in code for both readers. Rust test coverage of the
rejection list is incomplete and the truncation outcome has no test (F-18).
"Arrives truncated" describes client retention after full receipt (†). The
disclaimers about memory bounds and the missing receiver deadline are correct
limit statements.

**L-41 · C:341-345 · Fingerprint.** Covers every record identity, field tag,
field name, kind and presentation rule; any edit to those changes it; source
locations, defaults and comments are outside it; no negotiation and no additive
compatibility; the build contract is checked during reservation before
execution; the fingerprint supplies no compatibility permission.
*Evidence.* `generate_porcelain.py:275-298`, `:303`.
*Verdict.* Supported. The list of covered attributes is accurate and
incomplete: optionality, record names, variant cases, roots and the schema
version are also covered (author's reading; a delegated in-memory recomputation
confirmed each sensitivity and insensitivity).

**L-42 · C:347-358 · Presentation and validators.** Byte fields become base64
or lowercase hexadecimal only at presentation, as listed; unsupported or
malformed input cannot become a semantic claim; structural admission
establishes shape; named validators check native operations, lifecycle, phase
order, actor setup and equipment, owned endings and extension custody "before
projecting claims"; conflicting observations remain publishable with dependent
claims withheld.
*Verdict.* Supported. The base64 list omits one public field, the rejected
client capture's `data_base64`, which is a controller field outside the schema
(†). The last sentence is the document's only statement of how validator
failures reach the reader, and it sits here rather than beside the "requires"
sentences it governs (F-07).

### 6.8 Maintenance and internal identity (C:360-441)

**L-43 · C:360-377 · Maintaining the contract.** How to edit the schema,
review shapes, update goldens and regenerate stamps; no schema counter; other
format markers and the worker identity keep separate purposes; historical
captures keep their bytes and are rejected if their producer is unsupported;
authored templates carry no identity and the harness asserts the inspected
candidate; constructed response tests supply an explicit producer context.
*Verdict.* The commands match the generator. `--refresh-shapes`, the only way
to recollect a stale surface golden, is not mentioned. The historical-capture
sentence is partly supported: the capture files exist and no test opens them;
they lack any `contract` and would be classed malformed, not unsupported (†).
The template and constructed-test sentences are supported (†).

**L-44 · C:379-390 · Worker identity generation.** An exact SHA-256 source
identity; no ordinal or negotiation; the build checks the three copies before
compilation and before signing and never writes them; "direct source-test
builds regenerate the same way"; the build account owns the sequence.
*Verdict.* Supported except the quoted sentence (F-17).

**L-45 · C:392-404 · Digest scope.** The listed directories, suffixes and
files; region bodies excluded; symlinks refused; the Ninja dependency log check
for the worker and the shim.
*Evidence.* `generate_worker_identity.py:26-56`; `source_identity.py`;
`tests/lib/native_sources.py:160-215` (†).
*Verdict.* Supported. The prose matches the generator exactly.

**L-46 · C:406-414 · Header and checks.** Magic at byte 0, identity at byte
64; the worker checks size and these fields before reading policy, publishing
or using layout-dependent fields; mismatch exits 4 with no publication; the
magic makes ordinal-era workers refuse; the host checks the identity before
decoding worker evidence and before releasing attempts; these checks do not
assert that a child validated the header; `abi_identity` records the
host-selected identity.
*Evidence.* `pw_probe_runner.c:1301-1319`; `CWorker.swift:584-591`;
`ActorSession.swift:137-141`. Default harness case runs the real bundled worker
against a flipped identity byte and a wrong magic (†).
*Verdict.* Supported, with three narrowings (F-17). The sentence that the
checks "do not assert that a child validated the header" is a correct limit
statement: the host compares bytes it wrote itself.

**L-47 · C:416-425 · Limits of equality; confinement.** Equality establishes
agreement on source bytes and nothing about implementation correctness, layout,
compiler, authenticity, behavior or sandbox cause; the hash is not
authentication; the exact-match requirement is confined to the host and worker
pair.
*Verdict.* Supported and exemplary. The public identity has no equivalent
passage (F-10).

**L-48 · C:428-441 · Shape goldens; build stamp.** Goldens record keys and
JSON types; producer controls write a candidate on difference; missing or
mistyped required fields still fail semantic admission; no version-bump
classifier. Every envelope carries five `build` fields; `contract` is the
admission identity; only an annotated tag on a clean tree yields a release
contract.
*Verdict.* Supported. The first paragraph states the goldens' limit plainly.
The last sentence is true of `build_contract.py` and `build.sh`; a direct Cargo
build takes the value from its environment (F-09).

## 7. Findings

Each finding states what was observed, what is interpretation, and where the
apparent problem provisionally belongs. None authorizes a change.

### F-01 · The normative text is larger than the document

*Observed.* The surface manifest gives every surface a `definitions` list
(`docs/contract_surfaces.json`). `surface_hash` concatenates the `CONTRACT.md`
region with those regions (`generate_contract_stamps.py:174-186`). Seventeen
of the eighteen distinct listed regions are in the guide and total about 2,090
of its 2,646 lines (table in section 4.2). `CONTRACT.md` contains no link to the guide
(section 3.2) and mentions it once, as "the guide" (C:117). The guide ships
beside the release; `CONTRACT.md` does not (the v0.3.6 archive carries
`PolicyWitness.md` beside the ZIP, the ZIP holds no Markdown, and
`CONTRACT.md` is in neither).

Ten identifiers are used for a region in both files: `probes`, `envelope`,
`lifecycle`, `transport`, `dossier`, `equipment`, `steps`, `refusals`,
`installation`, `profile`.

*Interpretation.* Nine of the thirteen `CONTRACT.md` surface regions are one
paragraph long. A reader given only `CONTRACT.md` will take that paragraph as the
complete normative definition of, for example, the `steps` surface. The
generator treats 276 further lines of the guide as part of that definition.
C:29-30 says the generator hashes "each delimited normative region" and does
not say where the regions are. The reverse also holds: of the equipment
region's distinctive terms, `termination_gate`, `preparation_failure`,
`unapplied_declaration`, `binding_ref` and `unverified_fixture` occur nowhere
in the guide, so for that surface `CONTRACT.md` is the only definition and the
guide regions listed for it define other fields.

*Belongs to.* Document. The cross-reference supplies missing authority; it is
not merely further explanation.

### F-02 · The outline contradicts the regions

*Observed.* Headings at C:65, C:173 and C:301 are level two and sit inside
level-three surface sections. The rendered outline is:

- `## Normative surfaces` contains only "Saved specimen and runner selection".
- `## Accepted input contract` contains "SBPL, params, augments and imports"
  through "Actor evidence and equipment".
- `## Actor evidence ownership` contains "Compiled-profile receipt" through
  "Runner installation and reservation".
- `## Typed response transport` stands alone.

The heading at C:256 follows a paragraph with no blank line. The
`transport_encoding` region (C:300-358) follows the `installation` region under
the heading "Runner installation and reservation" until its own heading; it is
hashed into `transport` and has no row in the stamp table. Region boundaries
are HTML comments. Inbound links from other documents target the inner
headings (`#accepted-input-contract`, `#actor-evidence-ownership`,
`#structured-request-refusals`).

*Interpretation.* A reader navigating by outline will conclude that only the
first surface is under "Normative surfaces", and cannot tell where a surface's
normative text ends. A reader looking for "Typed response transport" in the
stamp table will not find it.

*Belongs to.* Document.

### F-03 · Stamps record declared change, not behavioral change

*Observed.* Section 4.2 lists what a stamp's hash covers and what passes
unnoticed. The request-side goldens hold key names only. The reply-side goldens
hold keys and JSON types. Nothing compares a region's sentences with code. The
only connection between a behavior change and a stamp is the instruction at
C:103-105 to keep definitions, examples and goldens current. All 13 rows read
`v0.3.6`, the first tag that carries the manifest.

*Interpretation.* C:31-32 says stamps are navigation aids and are never used
for admission, and C:100-103 says every release requires re-assertion. Both are
accurate. The reuse procedure at C:17-18 nevertheless tells the author to
"inspect the surface rows changed since its asserted release", from which a
reader can reasonably infer that an unchanged row means an unchanged surface.
That inference holds only as far as maintainers edit prose or goldens whenever
behavior changes. The mechanism's tests show that it tracks its inputs
faithfully; they cannot show that its inputs track behavior. The procedure is
also undefined for a specimen asserting a `development:` identity, and the
table says that something changed, not what.

Attribution is a second, smaller limit. Reply keys are assigned to surfaces by
substring with `envelope` as the fallback, and several guide regions hold text
that belongs to a different surface by name (section 4.2). A stamp can
therefore move on the wrong row.

*Belongs to.* Evidence (what the mechanism can establish) and document (what
the reuse procedure implies).

### F-04 · The manifest's `checks` field is a label

*Observed.* The generator requires only that each named suite exists in the
catalog (`generate_contract_stamps.py:55-56`). Nothing else reads the field.

| Surface | Named suite | What was found |
| --- | --- | --- |
| `equipment`, `transport`, `installation` | `runner_byoxpc` | Suite is `default: false`. Zero of its cases are among the 229 in the v0.3.6 acceptance battery. For `equipment`, no file in the suite references the region's fields (†). |
| `profile` | `failure_boundaries` | `check.py`, `README.md` and `run.sh` contain neither "profile" nor "nonce". |
| `probes` | `witness_contract` | Covers prediction and ordering. Not unique identifiers, closed vocabularies or the example (†). |
| `steps` | `failure_boundaries` | Covers `query_first`. Not producer admission or the example (†). |
| `policy` | `integration` | Covers augment application and refusal. Not the direct-XPC refusal (†). |
| `dossier` | `witness_contract` | Covers contents. Not the held-input sentence or the example (†). |
| `envelope`, `lifecycle`, `actors`, `request`, `refusals` | `unit`, `runner_unit`, `runner_unit`, `failure_boundaries`, `runner_outcome_bad_request` | The named suite exercises the surface (†). |

*Interpretation.* `CONTRACT.md` does not describe the field; C:24 says the
manifest "defines the scope". A reviewer who opens the manifest will read
`checks` as the verification owner of each surface. For three surfaces the
retained release evidence contains no run of that owner. Those surfaces are
exercised by other default suites (section 5), so the gap is in what the
manifest says, not necessarily in coverage.

*Belongs to.* Evidence.

### F-05 · "Verified examples"

*Observed.* C:104 and C:365 call the examples "verified". Each of the 13
regions carries one sentence beginning "Example:". No mechanism ties an example
sentence to a test. Status by example:

| Line | Example | Status |
| --- | --- | --- |
| C:141 | Nonexistent actor refused before children | Default signed control, CLI and direct XPC (†) |
| C:255 | Old `schema_version`-only specimen reports missing `contract` | Default signed control on both paths; unit test `request_patch.rs:232` |
| C:63 | Foreign assertion plus invalid selector | Exact combination: unit test with injected dependencies. Default signed control uses a missing contract and a misspelled selector key and reads the controller's own `runner_client: null`. Independent process observation is opt-in (†). |
| C:129 | Missing augment refuses before worker creation and leaves the file unchanged | First half: default signed controls. Second half: no assertion for this case (†). |
| C:135 | `open_write` truncates; a foreign assertion prevents it | First half: default signed effect test. Second half: opt-in two-build case only (†). |
| C:171 | Equipment hash mismatch prevents use | Constructed bundle at the binder; signed bundle at `runner install` (default). No signed `run` (†). |
| C:147 | Foreign helper envelope cannot supply a successful status | Constructed data only (†) |
| C:153 | Changing the file after admission does not change the submission | Unit test with injected dependencies only (†) |
| C:165 | Unreaped worker stays unconfirmed | Unit test with the real host driver and a fixture child; constructed controller test (†) |
| C:159 | Foreign host reply yields one unsupported diagnostic | Constructed harness-reader document; live control opt-in (†) |
| C:249 | Foreign live peer receives no submission | Unit tests with fake connections; live control opt-in, with an instrumented host (†) |
| C:296 | Legacy record cannot execute but can be removed | Unit tests; live control in the opt-in suite (†) |
| C:243 | Wrong nonce refuses the receipt inside a current reply | Not verified as written (F-06) |

*Belongs to.* Evidence for the gaps; document for the word "verified".

### F-06 · The compiled-profile sentence describes a producer check as a reader refusal

*Observed.* C:243: "Status, nonce, worker binding, stage, byte count and digest
must be consistent … Example: a wrong nonce refuses the receipt even inside a
current reply."

- The controller's reader checks that `status` is `captured` or `unavailable`,
  that a captured receipt has `producer: worker` and
  `capture_stage: before_apply`, and that an unavailable one has neither
  (`porcelain_admission.rs:1299-1309`). It checks nothing else.
- A unit test builds a `captured` receipt with nonce, length, digest and
  bytecode all absent and asserts the reader admits it
  (`porcelain_admission.rs:2713-2742`).
- The host checks worker process identifier, nonce, extent, digest and consumed
  inputs against worker shared memory before publication
  (`CWorker.swift:691-709`). A mismatch yields `status: "unavailable"` with a
  reason such as `capture_nonce_mismatch`. It is not a refusal and it happens
  before any reply exists.
- The guide states the host-side rule accurately (G:649-652).

*Interpretation.* The sentence sits in a document about admission and uses
"refuses … inside a current reply", so a reader will take it as a reader-side
rule. By source inspection, a current reply carrying a `captured` receipt with
a different nonce would be admitted by the controller. Confirming that needs an
experiment, which was not run.

*Belongs to.* Document primarily. If a reader-side consistency check was
intended, implementation.

### F-07 · "Requires" and "admits only" mean "flagged"

*Observed.* The equipment region uses "admits only" (C:198), "requires"
(C:205-207, C:219-226) and "cannot" throughout. In the controller:

- A reply is refused only for a delivery failure, a foreign producer, or
  `admission_problem`, which covers table capacities and the compiled-profile
  context (`run_flow.rs:332-359` †, `porcelain_admission.rs:1289-1312`).
- Every equipment-region rule runs later, in `execution_diagnostics`. A
  violation sets `process_disposition: "withheld"`, `disposition_integrity:
  "invalid"` and appends issues (`porcelain_admission.rs:1631-1636`).
  `data.runner_result` is published unchanged, including the violating field.
  `result.ok` and the exit code follow only `normalized_outcome == "finished"`
  (`run_flow.rs:748-760`). A unit test asserts exit 0 with
  `disposition_integrity: invalid` (†).
- When `reporting_failure` is present, the phase, native, association and
  actor validators are not run at all (`porcelain_admission.rs:1426-1449`).
  The host reaches that state when its own self-check fails, and re-encodes the
  same actor records (†).

*Interpretation.* C:351-355 says "conflicting observations remain publishable
with dependent claims withheld". That sentence is correct and governs every
"requires" in C:168-238, but it is 115 lines later, in a different region,
under the transport heading. A reader of the equipment region alone will
conclude that a reply with, say, a satisfied gate lacking a source timestamp
cannot appear in output. It can; it is marked invalid in a sibling field. A
reader will also assume a `runner_reporting_failed` reply passed these checks.
It did not.

*Belongs to.* Interpretation and document. The qualification is separated from
the claims it constrains.

### F-08 · Refusal vocabulary, ordering and nulls

*Observed.*

- The table at C:273-284 names 22 codes. Twenty-nine further codes are string
  literals in runner source and appear nowhere in `CONTRACT.md` or the guide;
  five appear in `REQUEST-GRAMMAR.md` (author's search). They include codes for
  rules the request region itself states: `exclusive_plan_forms` for C:91-92,
  and `empty_phases`, `empty_phase_id`, `duplicate_phase_id` for C:92-93. The
  actors example at C:141 produces `unknown_actor`, which is not in the table.
- C:287-288 says "capacity checks precede meaning checks". The plan-form rule,
  which C:91-92 lists among the meaning checks, is enforced during decoding,
  before capacity (`PWRunnerRequest.swift:132-142`). So are
  `actors_require_phases` and the override-map checks (†).
- C:75 lists four fields that reject explicit null. An inapplicable extension
  operand is a fifth: present-but-null is refused as `inapplicable_field` where
  absence is accepted (`PWRunnerExtension.swift:20-24`,
  `ActorPlan.swift:409-411`).

*Interpretation.* C:289 tells consumers to retain unfamiliar codes, which
makes the omission safe for a careful consumer. Nothing says the table is
partial, and its layout reads as complete.

*Belongs to.* Document.

### F-09 · "No bypass" and "unbound"

*Observed.*

- `sbpl-check` is shipped and documented as directly runnable (G:677-685). It
  deserializes only `policy` from a request file, has no contract check and
  does not reject unknown fields (`controller/src/bin/sbpl-check.rs:47-58`,
  `:433-439`). It compiles and reports; it applies nothing and starts no child.
  The guide's account of it (G:690-695) is accurate and does not mention
  `contract`.
- The Rust controller's compiled identity is whatever nonempty
  `PW_BUILD_CONTRACT` its build environment held
  (`controller/src/json_contract.rs:10-20`; `controller/build.rs` only declares
  the variable). `build.sh` always overwrites it. A direct `cargo build` with
  the variable set does not. The integration suite runs
  `env -u PW_BUILD_CONTRACT cargo test` (†). A SwiftPM build with
  `-DPW_UNIT_TEST_CONTEXT` is `test:policy-witness`
  (`PWRunnerAPI.swift:155-167`); a direct Meson build is bound (†).
- `_test_overrides` is accepted in signed release builds with no build-flag
  gate, and can substitute the worker and validator executables and alter
  timeouts and fault seams (†). The contract gate still applies to such a
  request. C:70 lists the object among ordinary request objects.

*Interpretation.* C:5-6 denies "bypass" and C:12-13 says direct builds "are
`unbound`". Both are true of what the document is about: the packaged run path.
A reader can reasonably take them further: that no shipped tool reads a
specimen without the gate, and that only the build script can produce a bound
binary. Whether a direct build with the variable set reports the supplied
string is a source inference and was not run.

*Belongs to.* Interpretation, and document for the unqualified wording.

### F-10 · What equality of contract strings establishes

*Observed.* C:416-420 says, of the worker identity, that equality "does not
prove correct implementation, compiled layout agreement, identical compiler or
SDK, binary authenticity, runtime behavior, or sandbox cause" and that "the
hash is not a security authentication mechanism". No comparable passage exists
for the public contract. For the public contract:

- `release:vX.Y.Z` is a tag name. It carries no digest.
- The identity does not cover `PW_INSPECTION`, `BUILD_XPC`, caller `RUSTFLAGS`,
  toolchains or the SDK (†). Two apps with one contract can differ in
  optimization and in whether they contain a runner at all.
- Every peer check compares a string the peer reports about itself: the
  reservation control reply, the registry record, the plist value.
- Conversely, identical sources can be mutually inadmissible. A build of this
  commit and the v0.3.6 release differ in no controller, runner or worker
  source and carry different contracts (section 4.3).

*Interpretation.* "The public contract is the release" (C:3) and "every
shipped-source change changes a development contract" (C:100) invite the
conclusion that equal contracts mean equal binaries and that a matching peer is
an authentic one. The document does not claim either. It also does not deny
either, although it is careful to deny both for the internal identity.

*Belongs to.* Document.

### F-11 · Identity-derivation wording

*Observed.*

| Line | Wording | Edge |
| --- | --- | --- |
| C:9 | "Other packaged builds emit `development:<sha256>`" | A clean tree with two annotated release tags at `HEAD` emits nothing; the script exits with an error (`build_contract.py:88-89`). |
| C:11 | "Ordinary documentation and test edits do not change that digest" | Nine files under `docs/` and `tests/` are in scope. The one in-scope change since `v0.3.6` is a test-library file. The reader cannot tell from the document which test files are "ordinary". |
| C:12 | "Git index flags cannot hide edited inputs" | True for scoped paths. Outside the scope, cleanliness is `git status`, which honors index flags (†). |
| C:12 | "Incidental executables and OS files are excluded" | By suffix. An incidental file with a scoped suffix under a scoped directory is hashed (†, hypothesis for specific file names). |
| C:100 | "Every shipped-source change changes a development contract" | True for tracked scoped sources. The scope also contains files that do not ship (†). |

*Belongs to.* Document. Each sentence is true in the ordinary case.

### F-12 · Residue, undefined terms and unresolved references

*Observed.* The repository's documentation rule is to describe current
behavior and leave history to `git log`. These passages describe the current
design by denying or recalling a previous one:

| Line | Text |
| --- | --- |
| C:67 | "The existing Swift `Codable` types remain the parser" |
| C:105-106 | "There is no separate request counter" |
| C:116 | "the existing decoder/selector fields" |
| C:176 | "no declaration reply or singular worker projection" |
| C:243 | "It has no independent schema marker" |
| C:255 | "an old `schema_version`-only specimen" |
| C:276 | "The request marker names another contract" |
| C:296 | "under the existing ownership rules" |
| C:297 | "the reader also accepts historical flattened entries"; "Known retired kind aliases" |
| C:365 | "No public schema counter is maintained" |
| C:372-373 | "retain their separate purposes" |
| C:384-385 | "There is no worker ABI ordinal" |
| C:410 | "ordinal-era workers" |
| C:433-434 | "There is no separate version-bump classifier" |

Some of these state live behavior that happens to concern old data (C:255,
C:297, C:410) and are needed. The others deny mechanisms a fresh reader has
never heard of.

Terms used in C:168-238 that are defined in none of the documents
`CONTRACT.md` could defer to (†): "declaration reply", "singular worker
projection", "acquired decision", "scheduling summary", "native-capability
observations", "eligible terminal worker branch", "owned records", "reserve
geometry". "Capture stage" and "ownership/departure flags" (C:213) paraphrase
the fields `stage`, `ownership_unbroken` and `departure_requested`; a different
record has a field actually named `capture_stage`. "Termination-gate allowance"
(C:225) is named `actor_termination_wait` in `LIMITS.md` (†).

References with no antecedent in the document: "the two tables" (C:52-53);
"the guide" (C:117); "Release preflight" and "release preparation" (C:55,
C:31); "It" at C:297, which follows "Publication" and in source belongs to
opaque metadata (†).

*Interpretation.* The denials are a large share of what the task calls
"statements that deny a guarantee". They should be separated from the denials
that carry weight for a reader: no negotiation (C:5), stamps are not admission
keys (C:32), predictions do not establish agreement (C:135), an exit request is
not proof of reap (C:165), the fingerprint is not a compatibility identity
(C:249, C:345), budgets are not memory bounds (C:332-333), and the limits at
C:412-420.

*Belongs to.* Document. Several items could be removed or simplified without
losing a behavioral distinction.

### F-13 · Maintainer instructions inside normative regions

*Observed.* Inside the hashed `request` region: "Keep the affected normative
definition, verified examples and shape goldens current" (C:103-105);
"Capacity changes must be documented and tested" (C:113-114); "Maintenance
consists of …" (C:116-118); the pointer to a developer lesson (C:121-122).
Inside `transport_encoding`: the account of the generator (C:304-309). Outside
any region, C:379-425 describes the host and worker shared-memory identity,
which no specimen author or envelope consumer can observe except through one
field.

*Interpretation.* These are maintenance conventions and implementation
detail presented in a public contract. Editing a maintenance sentence at
C:103-105 moves the `request` stamp. C:422-425 does say the internal identity
is confined to the host and worker pair, which is the necessary qualification;
it comes at the end of the section.

*Belongs to.* Document.

### F-14 · "Cannot disagree with each other about structure"

*Observed.* C:307-309. The generator emits Swift record writers, Rust readers
and Python tables from one schema. Exceptions:

- The Swift writer for the schema's one variant is hand-written with literal
  case tags 1 and 2 (`PWPorcelain.swift:115-126`). The generator's Swift output
  contains nothing for variants. Rust and Python take those tags from the
  schema. They agree today; no check pins the Swift literals (†).
- The producer-context tags are hard-coded in the Rust and Python
  `decode_bound` functions (†).
- The three primitive codecs are separate hand-written implementations. The
  fingerprint does not cover them (†).

*Belongs to.* Document. "None of them checks the schema itself", in the same
sentence, is accurate.

### F-15 · Equipment-region sentences without a check or a determinable meaning

*Observed.*

- C:180-181, "An acquired decision does not publish another cell". The term is
  undefined. Under a temporal reading it is contradicted: the worker publishes
  its decision and then publishes cleanup cells (†). No test names the
  property.
- C:188-190, override rows "cannot establish packaged selection". The row
  shape is enforced. No check prevents an actor bound to an override row from
  being matched, eligible and run (†).
- C:200, "Observation arrays are empty". Steps, extension events, transfers,
  resource tables and host region and custody arrays are required empty, and
  `actors` is required nonempty (`porcelain_actor.rs:1081-1108`). `phases`,
  `authority_setup.workers` and the binding and entitlement tables are
  normally populated; the refused binding row is the evidence (†).
- C:216-217, "These ordinals are local to the source actor process". Each
  process has its own counter. A dependent phase's activation ordinal is in the
  dependent's sequence, so the three ordinals the gate rule compares are the
  source's, and other phases' ordinals are not comparable with them (†).

*Hypothesis (†, not run).* A source actor that exits while parked between
visits is reaped at the first wait after its next activation. That would give
an activation ordinal below the reap ordinal and a satisfied gate, although
the process ended before the recorded final activation. An experiment would
need an independent record of the exit time.

*Belongs to.* Document, except the hypothesis, which would belong to
implementation or interpretation if confirmed.

### F-16 · Installation-region phrases

*Observed.*

- "Survives unrelated writes" (C:297). Unknown keys are kept through
  `serde(flatten)` maps. `runner validate` rebuilds signature and entitlement
  records with empty maps (`runner_manager.rs:1046-1069`); whether that drops
  unknown keys from a validated record is an inference with no test either way
  (†).
- "Lossless read-back before atomic replacement" (C:297). The check
  serializes, parses those bytes, serializes again and compares
  (`runner_manager.rs:602-607`). It does not read the written file or compare
  with the previous registry. It detects an opaque key that collides with a
  known one.
- "It never establishes execution compatibility or ownership" (C:297). The
  referent is ambiguous (F-12).

*Belongs to.* Document; implementation for the first item if the inference
holds.

### F-17 · Internal identity section

*Observed.*

- C:389, "Direct source-test builds regenerate the same way". Nothing
  regenerates automatically: `runner/Package.swift` and
  `tests/suites/runner_unit/run.sh` do not mention the generator. An earlier
  revision read "can regenerate with the same command" (†).
- C:411-412, "The host checks the identity before decoding worker evidence".
  True of the `worker_evidence` record and the authority-setup decode. Slot,
  applied, done and phase publications are read without the identity gate, and
  in the actor form the release path checks at setup only (†).
- C:413, `runner_subprocess.worker_evidence.abi_identity`. The actor form's
  path is `actors[].subprocess.worker_evidence.abi_identity` (†).
- C:410, "The bootstrap magic also makes ordinal-era workers refuse the
  header". No test runs an ordinal-era worker. The existing control shows the
  converse: the current worker refuses a header with the wrong magic (†).
- A mapped region that is too small exits 3, not 4
  (`pw_probe_runner.c:1301-1302`). The document claims 4 only for a magic or
  identity mismatch, so this is consistent; no test of the size refusal was
  found (†).

*Belongs to.* Document for the first three; evidence for the last two.

### F-18 · Stated behavior that no executing test reaches

*Observed (†, with the `runner_reply_truncated` search repeated by the author).*

- `runner_reply_truncated` (C:337). The string occurs in one source line, in
  `CONTRACT.md` and in `tests/COVERAGE.md`. No test produces it.
- The refusal of the post-signing recheck at install (C:296).
- Unbound builds refusing peer checks (C:13). Every site has the comparison;
  Rust unit tests run with a fixed test identity, so no test executes those
  branches with an unbound expectation. One default integration test covers an
  unbound binary refusing a request.
- Rust reader: unknown variant case, impossible collection count, unordered
  map key, a frame over the byte limit, nesting past the limit (C:328-331).
  The Python reader's tests cover the first three and the nesting limit.
- The host writer's refusal at the frame limit (C:335).
- Reading a flattened pending-cleanup entry through the shipped CLI (C:297).
- Runtime inspection failure on the signed product (C:194-196).
- Eight of the eleven application pairs on the signed product (C:204-210).
- The single fallback compile using the held input, on the signed product
  (C:153).

*Belongs to.* Evidence. Each item is implemented; source inspection supports
the document's statement.

### F-19 · Hashed guide text that contradicts the document

Found while reading guide regions for other purposes. The guide was not
compared with `CONTRACT.md` systematically.

*Observed.*

- G:1519-1521, inside the `transport` region: "A host from another build, such
  as an external runner installed before an app update, can produce the second
  case after it has executed the specimen." C:249 says a foreign live peer
  "receives no specimen submission" and C:345 says the contract "is checked
  during reservation before execution". The code agrees with `CONTRACT.md`:
  the registry gate precedes client launch and both sides of reservation
  compare contracts before the specimen is sent.
- G:655-656, inside the `profile` region: "Readers require the nested receipt
  version". C:243 says the receipt "has no independent schema marker". The
  record has no version field (†).
- G:196-197, inside `request_form`: the accepted input contract "rejects
  unsupported request versions". The request has a `contract`, not a version.

*Belongs to.* Document (the guide). Relevant here because these sentences are
part of the hashed definitions of the `transport`, `profile` and `request`
surfaces.

### F-20 · Examined and sound; no change warranted

- **The host compares identity bytes it wrote itself** (C:411-414). This looks
  circular. The document says so: the checks "do not assert that a child
  validated the header" and `abi_identity` "records the host-selected
  identity". The claim is correctly limited.
- **Exactness is restated on five surfaces** (C:3-6, C:63, C:147, C:159,
  C:249). Each restatement governs a different admission point with its own
  code path. The repetition is needed.
- **Fingerprint and contract are both required** (C:249, C:341-345). The
  distinction is enforced: fingerprint first, never sufficient
  (`porcelain.rs:156-161`, `:218-220` †).
- **"The XPC host itself may have launched to decode a request"** (C:286-287).
  This weakens "refuse before … children" at C:63 and is the correct
  qualification for unknown-field refusals.
- **`expected_contract` in a refusal** (C:255, C:266). The refusal tells the
  caller the identity to assert. That is the design: the assertion is an
  acknowledgement by the author, not a secret.
- **Reservation retries** (C:249). Acquisition retries up to 256 times. No
  retry can resubmit: the reservation request carries no specimen and
  submission happens once (†).

## 8. Statements that are correct and well supported

Supported by source the author read and by default tests that passed in the
v0.3.6 acceptance battery, unless noted.

- The request contract gate, its position before selectors, augments and
  children, its four codes and `expected_contract`, in both controller and
  host, including unbound builds (C:63).
- Unknown-key refusal for every listed request object, and for the actor and
  extension objects the list omits (C:67-72, †).
- The four listed null exceptions (C:75, †).
- Selector validation, precedence and removal; direct-XPC refusal of selectors
  and unresolved augments (C:77-85, †).
- Each meaning rule and its position before child creation (C:87-94, †).
- Capacity refusal content (C:108-112, †).
- Path bounds and their units (C:266-270).
- The request file is never written (C:19).
- Exact admission of client capture, host reply and helper envelope before
  interpretation, with frame bytes retained (C:147, C:159, C:249; †, unit
  level for the foreign cases).
- `open_write` truncation (C:135, †).
- The `query_first` chain, enforced in worker, host, controller and harness
  (C:159, †).
- No reap means unresolved, projected as unconfirmed (C:165, †).
- The whole termination-gate passage (C:212-236, †).
- The closed `preparation_failure` and application pair sets (C:198-210).
- Contract comparison on both sides of reservation before submission, and a
  single submission (C:249, C:345).
- `PWContract` admission before signing, registry or launchd changes (C:296,
  †; live evidence is opt-in).
- Every stated frame width, ordering rule and reader rejection, in two readers
  (C:313-330, †).
- Fingerprint inputs and exclusions (C:341-344).
- The byte and hexadecimal presentation mapping for schema fields (C:347-351,
  †).
- The stamp generator's behavior as described, including missing history
  (C:24-32, C:52-56, C:362-370).
- Release derivation: annotated tag, clean tree, byte comparison with the tag
  (C:8-12).
- Worker-identity digest scope, the checks before compilation and before
  signing, the Ninja dependency check (C:382-404, †).
- Magic at byte 0, identity at byte 64, worker check order, exit 4 with no
  publication, tested against the real bundled worker (C:406-410, †).
- The limits at C:412-420.
- The five `build` fields and `--version` (C:14, C:438-440).

## 9. Experiments identified and not performed

| Claim | What would establish it |
| --- | --- |
| A current reply with a `captured` receipt and a different nonce is admitted (F-06) | Feed a constructed reply to the controller's reply path and read `result` and `runner_sandbox_diagnostics`. |
| A direct Cargo build with `PW_BUILD_CONTRACT` set reports that string (F-09) | Build into a scratch target directory outside the managed one and run `--version`. |
| A genuinely foreign signed host receives no submission (L-31) | Install a service from another build under a current-contract registry record and trace host-side receive events. |
| The single fallback compile uses the held input on the signed product (L-20) | Force a client `xpc_error`, replace the request file mid-run, compare the helper's policy hash with the applied hash. |
| `runner validate` drops unknown signature and entitlement keys (F-16) | Add unknown keys to a registry record, run validate, compare. |
| A parked source's exit can satisfy a gate after a later activation (F-15) | Two-visit source that exits between visits, with an independent exit timestamp. |
| A 92 to 128 MiB reply is reachable from a live host (L-40) | Not designed. |
| CLI and direct XPC treat duplicated JSON keys alike (†) | Submit a request with a duplicated key on both paths. |
| An ordinal-era worker refuses the current header (F-17) | Run a worker built before the identity change against a current header. |

## 10. Limits of this examination

- Five delegated passes did most of the source tracing. Their citations are
  marked †. The author re-read the code behind section 4, behind every
  unmarked citation in section 7, and behind the gate, reservation, receipt
  and reader claims; † citations rest on the delegated reading.
- "A test asserts" describes test source. Only cases named as passing in the
  v0.3.6 acceptance battery are runtime evidence, and that battery ran the test
  sources of its own commit.
- No opt-in case has a retained run in this checkout. Earlier development runs
  of `runner_byoxpc/reservation_controls`, `registry_recovery` and
  `runner_outcome_bad_request/same_shape_contract` are described in
  `records/2026-11-09-release-stamped-contracts-review.md` and their output has
  since been pruned.
- The guide's regions were read in part. F-19 is not a complete comparison.
- The semantic validators were examined for existence, reachability and effect
  on output. Whether each rule is correct was examined only for the equipment
  region.
- The single-worker form's process freshness was not traced in full (†).
