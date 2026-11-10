# Contract migration inventory

Stage-one step four of [the staging plan](../../docs/CONTRACT-STAGING-PLAN.md).
Inspected at `8dfb11522447fc7cf3d9d1ef8c574f45f372140a` on 2026-11-10.
This is an implementation dependency inventory for the switch to the contract
tree. It records migration work and checks to retain, rather than claiming
that the proposed generator or document already implements them.

Evidence grades in this record are **source read** and **check read**. The
checks named below were opened, including their fixtures and assertions where
specified. None was executed for this inventory. Read-only searches, JSON
inspection, a Markdown-link inventory and Git comparisons were performed.
The previous ledger inventory was read and checked against those sources.

## Entry point and current history

`docs/generate_contract_stamps.py` currently owns these interfaces:

| Interface | Current consumers and migration requirement |
| --- | --- |
| CLI `--check`, `--release TAG`, `--require-history`, `--refresh-shapes` | `build.sh`, release instructions, uniform generator controls and fixture commands call these modes. Retaining the entry point avoids a build-script change. Preserve the read-only check, pending-release preparation and explicit shape-refresh distinctions. |
| `input_paths(root)` | Fixture discovery and both release-entry controls copy these paths. Include every tree file, parser/helper import, vendored Markdown-reader input, referenced definition/check source and historical-reader input needed in a relocated fixture. `copy_declared` creates a directory empty; declaring only `docs/contract/` will omit its files. |
| `render(root, release=None)` returning `(name, before, after)` triples | Release preflight and multiple fixture builders compare or write the returned documents. The replacement must return the complete contract and the guide's table, or every caller must change together. |
| `release_tags(root)` | Release preflight distinguishes unavailable history. It currently returns annotated `vMAJOR.MINOR.PATCH` tags on this repository's HEAD ancestry, in ancestor order; a nested directory in another repository is not its own history. |
| `stamps(root, release=None)` | Release preflight reads every entry's `stamp`; tests also inspect `removed`, surface keys and hashes. Retain removal rows in the returned account as well as the rendered table. |
| `check(root, require_history=False)` | Source-drift tests distinguish full verification (`True`) from the narrower source-copy check (`False`). Ordinary build retains the existing permissive check until its maintainer decision. |
| `check_shapes(root, refresh=False)` and `collected_shapes(root)` | Drift controls exercise stale-shape refusal and deliberate recollection. Preserve independently reviewed canonical shapes while reallocating their public ownership. |
| `OUTPUTS`, `BEGIN`, `END`, `MANIFEST` | Uniform ownership tests, fixture construction and surface mutation tests read these constants. Ownership must distinguish the whole generated contract from the guide's table region. A compatibility name must not preserve a second authoring hierarchy. |

The existing `manifest` validates the surface schema, relative input paths,
unique IDs and suite names against `tests/catalog.json`. `surface_hash` reads
the tag's own primary definition region, its supplementary regions in manifest
order, and its JSON goldens. It collapses whitespace in region text and hashes
the canonical JSON array of that text and the parsed goldens. Thus a current
surface includes examples and guide definitions inside those regions, while
the manifest's `artifact` and `checks` metadata do not enter that hash.

`git diff v0.3.6 -- docs/generate_contract_stamps.py
docs/contract_surfaces.json` was empty. Those files can therefore supply the
observed legacy reader and scope at this source snapshot. The legacy history
reader must continue to read each historical tag's own manifest and blobs;
using the new tree's shape assignment to reinterpret `v0.3.6` would change the
historical account. The current `stamps` skips a release only when that tag
has no manifest. The replacement needs to distinguish a release before this
format existed from a missing or unsupported released layout.

The present no-history behavior has two separate paths. `check` validates
current shapes and hash inputs, compares the two existing tables, reports that
derivation was not checked and succeeds unless `require_history` is set.
`render` refuses to overwrite existing versioned tables without history only
when `release is None`; supplying `--release` currently bypasses that guard.
The latter is the `R-29` defect to repair. It is also the bootstrap on which
the fixtures below currently rely.

## Surfaces, regions and shape collection

The current thirteen IDs are `request`, `policy`, `probes`, `actors`,
`envelope`, `dossier`, `steps`, `lifecycle`, `equipment`, `profile`,
`transport`, `refusals` and `installation`. Each has a primary `BEGIN/END
CONTRACT <id>` pair in `docs/CONTRACT.md` and a same-name JSON file under
`tests/fixtures/contract/surfaces/`. These names are written into
`collected_shapes`, not merely loaded from the manifest.

| Surface | Supplementary regions currently hashed | Additional golden beyond its surface JSON |
| --- | --- | --- |
| `request` | Guide `request_form`, `request_admission`, `installation` | `tests/fixtures/request_contract/examples.json` |
| `policy` | Guide `policy_input`, `policy_tools` | — |
| `probes` | Guide `probes`, `operations` | — |
| `actors` | Guide `actors_phases`, `actors_extensions` | — |
| `envelope` | Guide `envelope` | — |
| `dossier` | Guide `dossier` | — |
| `steps` | Guide `steps`, `operations` | `tests/fixtures/comparison/matrix.json` |
| `lifecycle` | Guide `lifecycle` | `tests/fixtures/disposition/current/constructed_deadline.json` |
| `equipment` | Guide `equipment`, `lifecycle` | — |
| `profile` | Guide `profile` | `tests/fixtures/contract/compiled_profile.json` |
| `transport` | Guide `transport`; contract `transport_encoding` | — |
| `refusals` | Guide `refusals`, `request_admission` | `tests/fixtures/request_contract/examples.json` |
| `installation` | Guide `installation` | — |

The coverage reconciliation must account for these regions before the tree
replaces them. In particular, three generated copies lie inside stamped guide
regions: extension coverage in `actors_extensions`, extension statuses in
`equipment`, and reading rules in `steps`. Their owners are respectively
`docs/EXTENSIONS.md` and the two shared regions in
`tests/FAILURE-PROPAGATION-CONTRACT.md`. Removing a guide region from stamping
does not supply a disposition for what it says.

`collected_shapes` has the following independent inputs and assignments to
replace with the confirmed surface ownership:

- `tests/fixtures/contract/response_shape.json`: `owner(path)` assigns fields
  by ordered path/substring tests. Producer fields go to `envelope`; step
  fields to `steps`; compiled-profile fields to `profile`; subprocess,
  disposition, termination and wait fields to `lifecycle`; equipment,
  resources, authority, bindings, transfers, extension events and remaining
  actor fields to `equipment`; failure fields to `refusals`. Remaining phase,
  schedule, sandbox/partial-step and clock fields go to `lifecycle`; the rest
  go to `envelope`. The order of these tests is consequential.
- Swift `CodingKeys` declarations in all
  `runner/Sources/PWRunnerCore/*.swift`: `key_owners` assigns run spec and test
  overrides to `request`, policy to `policy`, query/filter/attempt/step to
  `probes`, actor/phase/dependency/extension operations to `actors`, reservation
  request/control reply to `transport`, and equipment manifest records to
  `installation`. `ActorEquipment.swift` has a special declaration-index
  mapping for its nested `Worker` type.
- `controller/src/runner_select.rs`: `SELECTOR_FIELDS` and
  `RUNNER_SELECTOR_FIELDS` become the `request` surface's controller keys.
- Serializable struct bodies in `runner_manager.rs`, `runner_commands.rs`
  and `runner_select.rs` become `installation.serde_records`, including their
  types and serialization attributes. This collector is textual.
- `docs/porcelain.json`: `generate_porcelain.wire_identity` contributes the
  full decoder identity, including tags, widths and presentation, to
  `transport.wire_schema`.
- `docs/limits.json`: `client_rpc_wait`, `reservation_lease`,
  `reservation_rpc_wait`, `reservation_attempts` and
  `reservation_retry_delay` contribute value, unit, counting, effect and
  control to both `transport` and `installation`. Reservation closed keys
  also appear in both.
- `tests/fixtures/contract/envelope_shape.json`: `envelope_owner` assigns
  specimen fields to `dossier`, client capture to `transport`, request failure
  to `refusals` and other fields to `envelope`.

Keep the two broad shape goldens separate from their surface projections.
`controller/src/run_flow.rs::envelope_shape` checks a constructed complete
controller envelope; `controller/src/bin/sbpl-check.rs` checks the helper
against the same envelope golden. `tests/suites/runner_unit/porcelain_replies.py`
replays constructed Swift reporting/codec receipts, checks required typed
fields and compares their combined reply shape with `response_shape.json`.
`tests/lib/consumer.py` loads both goldens as reader allowlists.
`tests/suites/source_drift/check.py::SHAPE_GOLDENS` and the fixture/architecture
accounts refer to those files. Reallocation of surface ownership should not
rewrite these underlying shapes merely to fit new headings. These checks
establish structure within their stated constructed or reader scope.

One additional opt-in dependency was absent from the earlier inventory:
`tests/suites/runner_outcome_bad_request/opt_in/same_shape_contract.py::main`
hashes `surfaces/request.json` into `product.json.request_shape_sha256` and
compares that receipt between two signed variants. It independently compares
the reply-shape hash and observed file effects. If the request projection moves
or splits, update the receipt's input and meaning together, then rerun
`runner_outcome_bad_request/same_shape_contract` when that control changes.

## Tests and fixtures that must move with the switch

All rows below have **check read** grade; no passing execution is claimed.

| Owner | Coupling found in the opened code | Required migration and retained assertion |
| --- | --- | --- |
| `tests/lib/fixture_inputs.py::GENERATORS`, `generator_module`, `generator_inputs`, `copy_declared` | Generator name/path discovery; `input_paths`; relocation; copied directory entries are empty. | Keep one discoverable generator and declare its complete input closure. Extend the independent known-input assertion for the tree, history reader and parser imports. |
| `tests/suites/source_drift/build_contracts.py::SurfaceStampTests` | `stamp_checkout` copies current stamped outputs into a new Git repository. `write_tables` stamps before the first tag. Tests name `request`, `profile`, `transport`, `installation`, `MANIFEST`, primary markers and a profile golden path. | Give these fixtures explicit initial history or a narrowly defined fixture authoring bootstrap; preserve no-history refusal for copied release tables. Replace manifest and marker mutations with tree mutations under the new names. Assert each mutation changed its target before judging the result. |
| Same class, `test_stamped_source_copy_and_no_tags_clone_validate_without_erasing_stamps` | Tests narrower check, strict refusal and `render(target)` refusal, but not `render(target, release=...)`. | Add explicit release-mode refusal with byte and mtime preservation; keep source-copy check behavior separate from regeneration. |
| Same class, pending-release/removal and shape tests | Checks pre-tag/post-tag reproduction, unaffected surfaces, retained removal, source key changes, shape refresh, missing suite, selector/reservation/wire changes. | Preserve those assertions across the legacy-to-tree boundary and future source syntax changes. Remap expected changed-surface sets after names are confirmed. |
| `tests/suites/source_drift/generators.py::region_ownership` | Assumes both `OUTPUTS` own only `(BEGIN, END)` regions. | Declare whole-file ownership for `docs/CONTRACT.md` and region ownership for the guide table. Preserve unrelated guide text and sentinels. |
| Same file, `test_regeneration_changes_nothing_outside_regions` | Changes the `request` marker in rendered CONTRACT, runs `--release v9.0.0` without Git, checks repeat bytes/mtime, then injects a write after the END marker through `sys.exit(main())`. | Mutate an authored tree node; establish fixture history; adapt the injected out-of-ownership write to a guide region or sentinel. The current before/after inequality can be satisfied by initial stamp changes even if the marker replacement became a no-op. Make mutation effectiveness an independent assertion. |
| Same file, `test_release_preflight_refuses_a_grown_baseline` | Copies `stamps.input_paths` and `build_contract.inputs`, then `stamps.render(root, tag)` before each fixture's first tag. | Seed history without permitting a real source copy to replace its released stamps. Keep equal/subset/superset/rewritten/predates/version-reset comparisons intact. |
| Same file, `test_fixture_declarations_cover_each_generators_inputs` | Its independently listed `contract_stamps` inputs name the old manifest and two outputs. | Replace the old manifest assertion with the actual authoring and historical input closure, including relocated imports; keep missing-helper refusals. |
| `tests/suites/preflight/check_build_entry.py::BuildEntryTests.checkout`, `stale_copy`, `test_build_refuses_stale_contract_stamps_copy_before_signing_or_creating_output` | Loads the module by filename, copies declared inputs, stamps `v9.0.0` without history, and changes the literal table header `Last changed` to `Stale`. | Bootstrap deliberate fixture history. Exercise stale whole-document output and stale guide-table output at the real early build gate; retain refusal before compilation/signing/output creation and update exact diagnostic assertions if necessary. |
| `tests/suites/preflight/check_release_publish.py::make_repo`, `git`, `check_preflight` | Synthesizes a one-surface legacy manifest, region-marked contract and empty guide table; its `git(... tag -a ...)` wrapper detects the old manifest, renders pending tables and amends the fixture commit. | Supply a minimal new-tree fixture plus explicit legacy fixture where history is under test. Replace the old `.exists()` discriminator. Keep real local Git/remote tag checks and publication controls; fixture amendments are not the real release retry procedure. |
| `tests/suites/preflight/opt_in/build_refusals.py::control_release_entrypoints_enforce_fresh_mode` | Copies the union of build/stamp inputs, calls `render(repo, 'v0.0.1')` before `git init`, then checks recursive make behavior with a controlled build. | Establish valid fixture history and adapt copied inputs while preserving fresh-mode forwarding/conflict refusal before a submission. This is opt-in. |
| Same file, `control_release_battery` | Calls `render(fresh.root, 'v0.0.0')` before initializing/tagging its disposable source; fresh-builds, then runs actual acceptance and the default battery with controlled Apple responses. | Preserve the complete integrated rehearsal. Its source fixture needs valid history and the revised generator inputs. This is opt-in and acceptance does not select it. |
| Same file, `_without_self_checks`, `SELF_CHECK_RE`, `SELF_CHECK_MARKERS` | Recognizes the exact list of `generate_<name>.py --check` lines and removes them only inside mutation fixtures, to reach the refusal being tested. | Retaining the entry point leaves this interface intact. If the invocation/name changes, update the exact list/recognizer and independently retain the real build's early check. |

The seven `SurfaceStampTests` methods are current-tree derivation; source-copy
behavior; pending release/removal; golden/malformed region; shape ownership;
reservation/selector keys; reservation limits/wire declarations. Their names
are also cited outside the test file. Retiring one requires updating those
citations and giving its retained assertion a new owner.

## Build, identity and architecture accounts

`build.sh` runs the stamp check after limits checking and before architecture,
footprint, porcelain, build-document and worker-identity checks, all before
compilation. Keeping `docs/generate_contract_stamps.py --check` preserves that
entry without editing `build.sh`. Its current banner can remain an operator
label if the accompanying build account accurately describes the enlarged
check.

`docs/build.json` owns step `check_contract_stamps`, refusal
`stale_contract_stamps` and invocation `inv_contract_check`. Update its reads,
diagnostic and citations to the new implementation; regenerate `docs/BUILD.md`,
`docs/build-steps.dot` and `docs/build-steps.svg`. The refusal currently cites
the literal `stale` in the generator and the named build-entry test.
`tests/suites/source_drift/build_rules.py` checks banner order, propagated
refusals and invocations; `tests/suites/source_drift/generators.py::build_checks`
also requires every named generator check before signing.

The identity scopes are explicit and were read:

- `docs/build_contract.py::DIRECTORIES`, `FILES`, `SUFFIXES` cover shipped
  source and named build inputs. `docs/contract/`, the surface manifest and
  stamp generator are outside this digest. `build.sh` is inside it. Whole-tree
  cleanliness still determines whether a build can identify as a release.
- `docs/generate_worker_identity.py::SOURCE_DIRS`, `SOURCE_FILES`, `TARGETS`
  cover worker/runner sources and named build inputs. The tree and stamp
  generator are outside; `build.sh`, `meson.build`, `meson.options` and
  `runner/Package.swift` are inside. A change there requires regeneration of
  the ABI header, `CWorker.swift` and `tests/lib/contract.py` identity regions.
- `docs/source_identity.py::source_paths` checks source path existence and
  rejects symlinks. Source/test citations added to contract inputs do not
  thereby become public or worker identity inputs.

`docs/architecture.json`'s `documents` graph has four directly affected nodes:
`contract_json`, `gen_contract`, `contract_md` and `guide`. The first three
currently describe a manifest, stamp-only generator and version/table output;
the guide describes its copied content and shipped status. Direct edges are
`D1`, `D2`, `D6`, `D34`, `D38` and `D44`. Change their input/output and ownership
accounts, then regenerate the architecture document and documents DOT/SVG.

The old pending-release test is additionally cited on `gen_identity`,
`json_contract_rs`, `contract_py`, `identity_sources`, `drift_contract`, and
edges `D16`–`D19`. Its name appears in checks on eleven graph rows, and as a
source citation on `drift_contract` and `D34`. These citations currently
establish that a test exists, not that the stamp test proves worker or
controller identity behavior. Review the assertion each row attributes when
moving or renaming tests. `generate_architecture` and its drift tests check
references and graph/table agreement, not that semantic attribution.

Update the operational accounts in `docs/SIGNING.md`,
`tests/suites/source_drift/README.md`, root `AGENTS.md` (the manifest sentence),
and `controller/AGENTS.md` (maintenance destination). The generated contract's
maintenance rules belong in its new directory guidance. Root README and
controller/runner/test routing labels can continue to name the contract while
their descriptions are made accurate.

## Guide staging, prose scans and links

`docs/generate_limits.py` owns five guide copy regions and the limits scalar
spans. Its `update_guide_rules`, `update_guide_extension_statuses` and
`update_guide_extension_coverage` copy the three stamped passages identified
above. It passes other guide text, including the stamp table, through.
Keep those copy owners intact during the switch; edit their sources and
regenerate when their text needs correction.

`build.sh` stages the checked guide with `generate_limits.py --stage-guide`
after signature checks and before ZIP creation. That command checks its own
sources and copies the exact guide bytes; it does not separately derive
contract stamps. The earlier stamp check and frozen release tree establish
that part of the sequence. `tests/suites/source_drift/limits.py::
test_staged_guide_is_exact_and_standalone` stages a fixture, compares bytes,
removes its repository and validates the staged copy. Its scope is copied
sections and internal links; `validate_guide` does not reject every external
companion-file link in ordinary guide prose.

`tests/lib/release_archive.py` requires the staged `PolicyWitness.md` beside
the final ZIP, copies it with the accepted app ZIP, verifies copied hashes and
lists it in `SHA256SUMS` and `release.json`. The contract is not an archived
asset under this arrangement. `release_accept.py` runs the ordinary battery
against the extracted app and records artifact integrity. Preserve the plan's
working shipping arrangement pending the maintainer's separate decision.

`tests/suites/source_drift/generators.py::scanned_documents` scans `docs/*.md`,
selected root/directory guidance and every Markdown region output registered
with the generators. It does not recursively scan new `docs/contract/*.md`
authoring files. `authored_prose` blanks regions recognized by
`docs/generator_common.py::region_ranges`, whose markers begin `GENERATED` or
`COPIED`. An entirely generated contract without an enclosing recognized
region is therefore treated as authored prose for literal-size/duration and
citation-pair baselines. Deliberately choose whole-output markers and check
the source tree through the contract generator; merely describing it as
generated does not change these scans.

The existing prose baseline has seven exact entries, three in the guide's
profile/installation passages. `baseline_problems` requires the current sites
to match that list. `release_preflight.inspect_baseline` additionally refuses
added or rewritten entries against the preceding release. A green drift check
after adding a baseline site does not establish release readiness. Convert
the site, and implement the contract's free-text count-by-kind ratchet
separately; it is a different comparison from these exact-entry counters.

The following links into current contract headings were found using the
repository Markdown reader over tracked Markdown files. “Checked” refers to
the current `scanned_documents` scope, not execution of the link check here.

| Caller | Current anchors | Scan |
| --- | --- | --- |
| `controller/AGENTS.md` | `maintaining-the-contract` | Checked; move to new maintenance guidance. |
| `controller/README.md` | `build-stamp` | Unchecked. |
| `docs/ARCHITECTURE.md` | `actor-evidence-ownership`, `controller-and-helper-envelopes`, `internal-hostworker-identity`, `shape-goldens` | Checked. |
| `docs/BUILD.md` | `internal-hostworker-identity` | Checked. |
| `docs/PolicyWitness.md` | `accepted-input-contract`, `structured-request-refusals` | Checked in repository; staged-guide validation does not resolve these companion links. |
| `docs/REQUEST-GRAMMAR.md` | `accepted-input-contract`, `actor-evidence-ownership` | Checked. |
| `docs/WORKER.md` | `actor-evidence-ownership` | Checked. |
| `runner/README.md` | `accepted-input-contract`, `actor-evidence-ownership` | Unchecked. |
| `tests/FAILURE-PROPAGATION-CONTRACT.md` | `actor-evidence-ownership` | Checked as a generator output. |
| `tests/suites/runner_abi_layout/README.md` | `internal-hostworker-identity` | Unchecked. |
| `records/FOOTPRINT-OUTFLOW.md` | `typed-response-transport` | Unchecked historical record; retain its historical meaning or qualify its target rather than silently treating it as a current definition. |
| `records/tests/PW-HISTORICAL-CONTINUITY-INVESTIGATION-REPORT.md` | `supported-versions`, `when-a-number-moves` | Unchecked historical record; same treatment. |

Document-level links also occur in root README/AGENTS, controller/runner/test
AGENTS, architecture, guide, failure-propagation contract and the staging plan
(checked); source-drift README, atlas plan and four contract/examination
records (unchecked). The four records are
`records/2026-11-09-release-stamped-contracts-review.md`,
`records/contract/CONTRACT-CONTACT-PLAN.md`,
`records/contract/CONTRACT-FIRST-READER-REPORT.md` and
`records/contract/FRESH-ENCOUNTER-ADDENDA.md`. `tests/fixtures/README.md` names
the contract as code text. `reports/sandboxed-extension-issuance/PLAN.md`
links to a commit-pinned remote contract, which remains historical. Preserve
or update active heading callers in the atomic switch, including the four
unchecked active links above. Generated graph links move through their input.

## Generator guarantees to make executable

These are recommendations for stage-one step three, grounded in the observed
consumers. They are not test results.

1. A released legacy tree is hashed from its own manifest and bytes. Include
   an actual `v0.3.6` snapshot control and an independently expected digest or
   row account; demonstrate that omitting that release fails. Preserve its
   thirteen surfaces and shape history even when the new tree removes names.
2. A removed surface retains its removal row through later releases. A
   carried surface changes at the migration release because the public
   representation changes. Test removal and unchanged new-layout releases
   separately, including pending-table equality after tagging.
3. Both ordinary regeneration and `--release` refuse when the released
   history they would overwrite is unavailable. Preserve all outputs and
   mtimes on refusal. Deliberate inaugural fixtures need a documented
   construction route that cannot erase copied released history.
4. An ordinary source-copy `--check` retains its separately stated narrower
   result; strict history checking refuses. A mismatched pair of tables,
   stale whole contract, malformed tree or stale shape must still refuse
   even without history. Do not let “no tags” bypass current-input checks.
5. Public-projection hashing changes for definitions, applicability,
   obligations, examples, shared public dependencies and canonical shapes.
   Owner citations, execution evidence and maintenance metadata alone do not
   move a stamp. Test both sides and indirect references, rather than hashing
   an entire authoring file as a substitute for the projection.
6. Every allocated public field has one authored meaning and a resolved
   record path; illegal nesting, duplicate IDs, missing references, unassigned
   fields and missing cited checks fail before writes. Examples have graded
   support or an explicit gap. Citation existence remains distinguishable
   from assertion coverage and execution credit.
7. Whole-document and guide-region ownership is explicit. Regeneration is
   deterministic, idempotent in bytes and mtimes, and leaves unrelated files
   and guide prose untouched. `--check` and invalid-input refusal write
   nothing. Every mutation proves that its intended input actually changed.
8. A relocated declared-input fixture imports only its own helpers and can
   parse the source tree. Removing a required parser/history helper fails
   clearly. New surface files and referenced owner sources are discovered.
9. A later source-syntax change still reads the archived `v0.3.7` layout and
   derives the same released public account. Record whether the chosen
   historical mechanism certifies recomputed content or stored digests.
10. The free-text baseline refuses growth by kind independently of the
    existing exact prose/build baselines. Generated output is recognized by
    the existing scan without concealing the tree's own authoring checks.
11. The real build refuses stale contract output and a stale guide stamp
    table before protected build work. The preflight then requires full
    history, exact tagged identity and no `unreleased` rows, using the same
    generator that produced the pending release.

## Release acceptance hazards and verification order

The relevant code was read in `Makefile`, `release_preflight.py`,
`release_archive.py`, the acceptance helper and the controls above. The release
procedure and staging plan remain the command authority.

- `release_preflight.inspect` imports the generator and calls `release_tags`,
  `render` and `stamps` directly. It does not call `check_shapes` through
  `check`. Preserve its full-history refusal and review whether the new
  `render` performs all structural validation required by its direct callers.
  The build still performs its own check.
- A pending release table intentionally differs from ancestry-derived current
  stamps until its new annotated tag exists. Finish the development build,
  default battery and opt-in refusal rehearsal before that stamp step.
- The no-history repair reaches default build-entry, source-drift and release
  publication fixtures, plus the opt-in refusal rehearsal. Passing only the
  default battery cannot establish that the latter fixtures migrated.
- Strict preflight compares exact baseline entries with the preceding tag,
  checks actual scoped source bytes against tagged blobs, checks the remote
  tag and refuses an existing archive or a non-increasing local version. It
  also requires footprint attribution to the newest local archive. Before
  `v0.3.8`, transcribe and attribute `v0.3.7` measurements.
- After tagging, repeat strict preflight, a fresh build and the default
  battery before spending a submission. `make release` fresh-builds again,
  then acceptance extracts the final ZIP and runs the default battery in its
  deeper output path. Archive verification binds that exact extracted app
  inventory, guide, provenance and complete test evidence.
- Keep the tree unchanged from tag through completed archive: preflight runs
  again after acceptance. A new untracked note or commit is enough to refuse.
  Failed attempts need their diagnosis recorded before retry; once the
  archive exists the version is spent.
- `v0.3.7` archival expires the last retained schema-1 archive under the
  four-release window. Remove `tests/lib/historical_release_storage.py` and
  its positive controls only when that archive and dependent quarantine have
  expired, as a separate change. Never bypass pending resource cleanup or
  interrupted retention ownership.
- The published history needs both new tags even if only `v0.3.8` becomes a
  public release: `make publish` pushes only the tag it publishes. Keep both
  releases unpublished throughout this work and draft each version's notes
  with presentation-only versus behavioral changes per surface.
- Missing identity/profile after an unsandboxed check and Apple's policy
  agreement are maintainer pauses. Sandbox keychain, Swift discovery,
  signature and XPC failures first require diagnosis and the same-command
  unsandboxed retry under repository guidance. Pending or identifier-less
  notarization follows the retained-response recovery procedure; resubmission
  is not a status check.

Expected verification owners after the switch are the full `source_drift`
suite, default `preflight/build_entry_controls` and
`preflight/release_publish_controls`, the changed golden owners, and opt-in
`preflight/build_refusal_controls`. Include
`runner_outcome_bad_request/same_shape_contract` if its receipt or source
selection changes. Each release boundary then requires the full rehearsals,
strict preflight and accepted final ZIP described above. None of those runs
has been credited by this inventory.
